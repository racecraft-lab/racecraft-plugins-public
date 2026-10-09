#!/usr/bin/env python3
"""Small source-contract checks for the standalone artifact gallery."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GALLERY = REPO_ROOT / "speckit-pro" / "artifact-gallery"
TEMPLATES = GALLERY / "templates"
ORACLE = Path(__file__).with_name("fixtures") / "artifact-gallery" / "catalog.json"
LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from test_result import run_counted  # noqa: E402


POLICY = (
    "default-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'; "
    "frame-src 'none'; connect-src 'none'; worker-src 'none'; script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src data: https://fonts.gstatic.com; img-src data:"
)
HEAD_MARKERS = ("<!-- GALLERY-HEAD:START -->", "<!-- GALLERY-HEAD:END -->")
BRAND_MARKERS = ("/* BRAND-KIT:START */", "/* BRAND-KIT:END */")
PLANNED = {"uat-walkthrough", "architecture-viewer"}
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def region(value: str, markers: tuple[str, str]) -> str:
    start, end = markers
    if value.count(start) != 1 or value.count(end) != 1:
        raise AssertionError(f"expected one {start} region")
    begin = value.index(start)
    finish = value.index(end, begin) + len(end)
    return value[begin:finish]


def catalog() -> list[tuple[object, ...]]:
    return [tuple(row) for row in json.loads(read(ORACLE))]


def catalog_errors(entries: list[dict[str, object]], template_ids: set[str]) -> list[str]:
    expected = catalog()
    pairs = [(entry["id"], entry["status"]) for entry in entries]
    shipped = {identifier for identifier, status, *_rest in expected if status == "shipped"}
    return [
        message
        for message, actual, wanted in (
            ("manifest rows", pairs, [row[:2] for row in expected]),
            ("template ids", template_ids, shipped),
            ("planned row", {entry["id"] for entry in entries if entry["status"] == "planned"}, PLANNED),
        )
        if actual != wanted
    ]


def document_errors(value: str, entry: dict[str, object]) -> list[str]:
    errors: list[str] = []
    canonical_head = region(read(GALLERY / "theme-toggle.html"), HEAD_MARKERS)
    canonical_brand = region(read(GALLERY / "brand-kit.css"), BRAND_MARKERS)
    if value.count(canonical_brand) != 1 or value.count(canonical_head) != 1:
        errors.append("canonical blocks")
    head = re.search(r"<head\b[^>]*>(.*?)</head>", value, re.IGNORECASE | re.DOTALL)
    prefix = head.group(1).split(canonical_head, 1)[0] if head and canonical_head in head.group(1) else ""
    if not re.fullmatch(
        r"\s*<meta\b[^>]*\bcharset\s*=\s*(['\"])?utf-8\1?[^>]*>\s*", prefix, re.IGNORECASE
    ):
        errors.append("CSP head position")
    if not re.search(
        rf"{re.escape(HEAD_MARKERS[0])}\s*<meta http-equiv=\"Content-Security-Policy\" content=\"{re.escape(POLICY)}\">",
        canonical_head,
    ):
        errors.append("CSP policy")
    source = entry["source"]
    if source["origin"] == "upstream" and not all(
        token in value
        for token in ("Upstream repository: anthropics/html-effectiveness", source["file"], "License: MIT")
    ):
        errors.append("attribution")
    return errors


def narrative_contract_errors(value: str) -> list[str]:
    policy = " ".join(value.split())
    required = (
        "Work one page at a time, in the listed order.",
        "Invoke the loaded runner's `fill-artifact-page` helper in `dry_run` mode",
        "Invoke `fill-artifact-page` again in `apply` mode with the same inputs plus `narrative`",
        "Send plain text. The runner escapes every character and wraps the text in the page's markup",
    )
    return [clause for clause in required if clause not in policy]


BANNED_MARKUP = (
    ("banned element", re.compile(r"<(?:base|iframe|object|embed)\b", re.IGNORECASE)),
    ("event attribute", re.compile(r"<[a-z][^>]*\son[a-z]+\s*=", re.IGNORECASE)),
    ("srcdoc or ping attribute", re.compile(r"<[a-z][^>]*\s(?:srcdoc|ping)\s*=", re.IGNORECASE)),
    ("scheme-relative URL", re.compile(
        r"""(?:\b(?:src|href|action|formaction|poster|srcset)\s*=\s*["']?|url\(\s*["']?)//""", re.IGNORECASE
    )),
    ("form submission target", re.compile(r"<form\b[^>]*\baction\s*=|\bformaction\s*=", re.IGNORECASE)),
    ("non-image data URI", re.compile(r"data:(?!image/|font/)[a-z-]+/", re.IGNORECASE)),
    ("button without type", re.compile(r"<button\b(?![^>]*\btype\s*=)[^>]*>", re.IGNORECASE)),
)
PLANNED_RULE = "A `planned` entry has no template yet, so it is never selected and never reported as a gap."
SLOT_RE = re.compile(r"^\s*Slot:\s*([a-z0-9-]+)\s*\|", re.MULTILINE)
FILL_RE = re.compile(r"<!-- FILL:([a-z0-9-]+):(START|END) -->")


def slot_errors(value: str) -> list[str]:
    """The slot inventory names each FILL pair once, and each pair is ordered and unnested."""
    slots = SLOT_RE.findall(value)
    markers = FILL_RE.findall(value)
    opened: str | None = None
    pairs: list[str] = []
    for name, edge in markers:
        if edge == "START" and opened is None:
            opened = name
        elif edge == "END" and opened == name:
            pairs.append(name)
            opened = None
        else:
            return ["slot markers"]
    if opened is not None:
        return ["slot markers"]
    return [] if slots and len(set(slots)) == len(slots) and sorted(slots) == sorted(pairs) else ["slot inventory"]


def contract_errors(value: str) -> list[str]:
    """Security bans, button types, and the slot inventory from SPA-CONTRACT.md."""
    return [name for name, pattern in BANNED_MARKUP if pattern.search(value)] + slot_errors(value)


class ArtifactGalleryTests(unittest.TestCase):
    def test_author_roles_write_plain_narrative_through_the_runner(self) -> None:
        for path in ("agents/artifact-author.md", "codex-agents/artifact-author.toml"):
            with self.subTest(path=path):
                self.assertEqual([], narrative_contract_errors(read(REPO_ROOT / "speckit-pro" / path)))

    def test_narrative_contract_guard_rejects_a_dropped_clause(self) -> None:
        for path in ("agents/artifact-author.md", "codex-agents/artifact-author.toml"):
            value = read(REPO_ROOT / "speckit-pro" / path)
            for old, new in (("in the listed order", "in any order"), ("`dry_run` mode", "`apply` mode"),
                             ("Send plain text.", "Send HTML.")):
                with self.subTest(path=path, mutation=old):
                    self.assertIn(old, value)
                    self.assertTrue(narrative_contract_errors(value.replace(old, new, 1)))

    def test_frozen_catalog_maps_every_manifest_row_and_file(self) -> None:
        expected = catalog()
        entries = json.loads(read(GALLERY / "manifest.json"))["templates"]
        shipped = [row for row in expected if row[1] == "shipped"]
        planned = [row for row in expected if row[1] == "planned"]
        self.assertEqual(22, len(expected))
        self.assertEqual(20, len(shipped))
        self.assertEqual(2, len(planned))
        self.assertEqual(PLANNED, {row[0] for row in planned})
        self.assertEqual(len({row[0] for row in expected}), 22)
        self.assertEqual([], catalog_errors(entries, {path.stem for path in TEMPLATES.glob("*.html")}))

    def test_shipped_documents_preserve_the_compact_standalone_contract(self) -> None:
        entries = {entry["id"]: entry for entry in json.loads(read(GALLERY / "manifest.json"))["templates"]}
        self.assertIn("MIT License", read(GALLERY / "UPSTREAM-NOTICE.md"))
        for identifier, status, *_rest in catalog():
            if status == "shipped":
                with self.subTest(identifier=identifier):
                    self.assertEqual([], document_errors(read(TEMPLATES / f"{identifier}.html"), entries[identifier]))

    def test_compact_guards_reject_catalog_and_document_drift(self) -> None:
        entries = json.loads(read(GALLERY / "manifest.json"))["templates"]
        entry = entries[0]
        document = read(TEMPLATES / "implementation-plan.html")
        remaining = [item for item in entries if item["id"] != "implementation-plan"]
        remaining_files = {path.stem for path in TEMPLATES.glob("*.html")} - {"implementation-plan"}
        self.assertIn("manifest rows", catalog_errors(remaining, remaining_files))
        self.assertIn("template ids", catalog_errors(remaining, remaining_files))
        self.assertIn("canonical blocks", document_errors(document.replace("worker-src 'none'; ", "", 1), entry))


class TemplateMarkupContractTests(unittest.TestCase):
    """Shipped template markup keeps the SPA-CONTRACT.md security and slot rules."""

    def test_shipped_templates_keep_the_markup_contract(self) -> None:
        for path in sorted(TEMPLATES.glob("*.html")):
            with self.subTest(template=path.name):
                self.assertEqual([], contract_errors(read(path)))

    def test_markup_guard_rejects_each_banned_construct(self) -> None:
        document = read(TEMPLATES / "implementation-plan.html")
        body = "<body"
        self.assertIn(body, document)
        for injected, expected in (
            ("<iframe></iframe>", "banned element"),
            ("<base href=\"x\">", "banned element"),
            ("<object></object>", "banned element"),
            ("<embed>", "banned element"),
            ("<div onclick=\"x()\"></div>", "event attribute"),
            ("<iframe srcdoc=\"x\">", "srcdoc or ping attribute"),
            ("<a ping=\"https://example.test\" href=\"#x\">x</a>", "srcdoc or ping attribute"),
            ("<img src=\"//example.test/x.png\" alt=\"\">", "scheme-relative URL"),
            ("<form action=\"https://example.test\"></form>", "form submission target"),
            ("<img src=\"data:text/html,x\" alt=\"\">", "non-image data URI"),
            ("<button>Go</button>", "button without type"),
        ):
            with self.subTest(injected=injected):
                self.assertIn(expected, contract_errors(document.replace(body, injected + body, 1)))

    def test_slot_guard_rejects_inventory_and_marker_drift(self) -> None:
        document = read(TEMPLATES / "implementation-plan.html")
        name = SLOT_RE.findall(document)[0]
        start, end = f"<!-- FILL:{name}:START -->", f"<!-- FILL:{name}:END -->"
        for label, mutated, expected in (
            ("undeclared slot", document.replace(f"Slot: {name} |", "Slot: renamed-slot |", 1), "slot inventory"),
            ("missing end marker", document.replace(end, "", 1), "slot markers"),
            ("reversed pair", document.replace(start, "@@", 1).replace(end, start, 1).replace("@@", end, 1), "slot markers"),
        ):
            with self.subTest(case=label):
                self.assertIn(expected, contract_errors(mutated))


class GalleryGuidanceTests(unittest.TestCase):
    """The author prompts, contract, and UAT template describe what ships."""

    def test_author_prompts_and_contract_skip_planned_entries(self) -> None:
        for path in ("agents/artifact-author.md", "codex-agents/artifact-author.toml",
                     "skills/speckit-autopilot/references/phase-execution.md", "artifact-gallery/SPA-CONTRACT.md"):
            text = " ".join(read(REPO_ROOT / "speckit-pro" / path).split())
            with self.subTest(path=path):
                self.assertTrue(PLANNED_RULE in text, f"{path} does not state the planned-entry rule")

    def test_both_author_hosts_leave_markup_and_escaping_to_the_runner(self) -> None:
        # The runner escapes narrative text (test-artifact-page-fill.py); no author writes markup.
        for path in ("agents/artifact-author.md", "codex-agents/artifact-author.toml"):
            text = " ".join(read(REPO_ROOT / "speckit-pro" / path).split())
            with self.subTest(path=path):
                self.assertIn("markup or Markdown you send shows on the page as literal characters", text)
                self.assertNotIn("Write only between a `START` marker and its matching `END`", text)

    def test_contract_names_the_suite_that_enforces_each_rule(self) -> None:
        text = " ".join(read(GALLERY / "SPA-CONTRACT.md").split())
        self.assertNotIn("repository tests validate the contracts below", text)
        for clause in ("tests/speckit-pro/unit/test-artifact-gallery.py", "pnpm --dir docs-site validate:gallery"):
            with self.subTest(clause=clause):
                self.assertTrue(clause in text, f"SPA-CONTRACT.md does not name {clause}")

    def test_uat_template_comment_counts_its_own_sections(self) -> None:
        template = read(REPO_ROOT / "speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md")
        comment, body = template.split("-->", 1)
        words = {"five": 5, "six": 6, "seven": 7, "eight": 8}
        claimed = re.search(r"\b(five|six|seven|eight) section headers\b", comment)
        self.assertIsNotNone(claimed)
        self.assertEqual(words[claimed.group(1)], len(re.findall(r"^## ", body, re.MULTILINE)))
        self.assertEqual(1, len(re.findall(r"^# ", body, re.MULTILINE)))
        self.assertNotIn("## UAT Runbook", comment)

if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]), label="test-artifact-gallery"))

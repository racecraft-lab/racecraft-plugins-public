#!/usr/bin/env python3
"""Offline contracts for upstream skill notices and derivative attribution."""

from __future__ import annotations

import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "upstream-skill-attribution"
NOTICE_PATH = Path(
    "speckit-pro/skills/speckit-coach/references/upstream/"
    "mattpocock-skills/UPSTREAM-NOTICE.md"
)
README_PATH = Path("speckit-pro/README.md")
ACK_TARGET = NOTICE_PATH.relative_to("speckit-pro").as_posix()
LICENSE_PATH = FIXTURE_ROOT / "mattpocock-LICENSE.txt"
PIN = "c55ee46073ed923f86ce59a5eb3b6d895095d1b7"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


def _notice_fence_structure(content: bytes) -> bytes:
    """Mask literal fence contents while retaining delimiters and byte offsets."""
    visible = []
    fence = b""
    for line in content.splitlines(keepends=True):
        if not fence:
            visible.append(line)
            opening = re.match(rb" {0,3}(`{3,}|~{3,})", line)
            if opening:
                fence = opening[1]
        else:
            closing = (
                rb" {0,3}" + re.escape(fence[:1])
                + b"{" + str(len(fence)).encode("ascii")
                + rb",}[ \t]*(?:\r?\n)?"
            )
            if re.fullmatch(closing, line):
                visible.append(line)
                fence = b""
            else:
                visible.append(re.sub(rb"[^\r\n]", b" ", line))
    return b"".join(visible)


def validate_matt_notice(repo_root: Path, license_bytes: bytes) -> list[str]:
    """Check holder identity and the enclosed license without normalizing bytes."""
    path = repo_root / NOTICE_PATH
    if not path.is_file():
        return [f"{NOTICE_PATH}: missing required notice file"]
    content = path.read_bytes()
    structure = _notice_fence_structure(content)
    headings = list(re.finditer(rb"(?m)^## License(?:\n|$)", structure))
    if len(headings) != 1:
        return [f"{NOTICE_PATH}: expected exactly one License section"]
    start = headings[0].end()
    next_heading = re.search(rb"(?m)^#{1,2} ", structure[start:])
    end = start + next_heading.start() if next_heading else len(content)
    section = content[start:end]
    visible_section = structure[start:end]
    openings = list(re.finditer(rb"(?m)^```text\n", visible_section))
    if len(openings) != 1:
        return [f"{NOTICE_PATH}: License section requires exactly one fenced text block"]
    opening = openings[0]
    closing = re.search(rb"(?m)^```(?:\n|$)", visible_section[opening.end():])
    mismatch = f"{NOTICE_PATH}: license bytes differ from {LICENSE_PATH.name}"
    if closing is None:
        return [f"{mismatch}: missing closing fence or final newline"]
    block_end = opening.end() + closing.start()
    if not license_bytes or section[opening.end():block_end] != license_bytes:
        return [mismatch]
    prose = structure[:start + opening.start()] + structure[start + opening.end() + closing.end():]
    identities = (
        ("upstream repository", rb"https://github\.com/mattpocock/skills(?=[\s)`]|$)"),
        ("provenance fork", rb"https://github\.com/racecraft-lab/skills(?=[\s)`]|$)"),
        ("baseline tag", rb"speckit-pro-baseline(?=[\s)`]|$)"),
        ("pinned commit", PIN.encode() + rb"(?=[\s)`]|$)"),
        ("MIT license", rb"\bMIT\b"),
        ("modified derivatives", rb"\blanded\b[^\n]*\bmodified derivatives\b"),
        ("ledger.json link", rb"\[[^\]]+\]\(ledger\.json\)"),
    )
    return [
        f"{NOTICE_PATH}: missing or incorrect {field}"
        for field, pattern in identities
        if re.search(pattern, prose) is None
    ]


def validate_matt_acknowledgment(repo_root: Path) -> list[str]:
    """Require a Matt acknowledgment with a direct, resolved local notice link."""
    path = repo_root / README_PATH
    if not path.is_file():
        return [f"{README_PATH}: missing required README file"]
    content = path.read_bytes()
    if b"Matt Pocock" not in content:
        return [f"{README_PATH}: missing Matt Pocock acknowledgment"]
    link = rb"\[[^\]]+\]\(" + re.escape(ACK_TARGET.encode()) + rb"\)"
    if re.search(link, content) is None:
        return [f"{README_PATH}: missing direct notice link to {NOTICE_PATH}"]
    if not any(
        b"Matt Pocock" in paragraph and re.search(link, paragraph)
        for paragraph in content.split(b"\n\n")
    ):
        return [f"{README_PATH}: notice link is outside the Matt acknowledgment"]
    target = (path.parent / ACK_TARGET).resolve()
    if target != (repo_root / NOTICE_PATH).resolve() or not target.is_file():
        return [f"{README_PATH}: notice link target {NOTICE_PATH} is missing"]
    return []


class MattNoticeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.license_bytes = LICENSE_PATH.read_bytes()
        self.notice_bytes = (
            b"# Matt Pocock upstream skills\n\n"
            b"- Upstream repository: https://github.com/mattpocock/skills\n"
            b"- Provenance fork: https://github.com/racecraft-lab/skills\n"
            b"- Baseline tag: speckit-pro-baseline\n"
            b"- Pinned commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7\n"
            b"- License: MIT\n\n"
            b"Files identified as landed in the sibling ledger are modified derivatives.\n"
            b"See the [skill ledger](ledger.json) for their disposition and ownership.\n\n"
            b"## License\n\n"
            b"```text\n" + self.license_bytes + b"```\n"
        )
        self.readme_bytes = (
            "# SpecKit Pro\n\n## Acknowledgments\n\n"
            "We acknowledge Matt Pocock's upstream skills. "
            f"See the [MIT notice]({ACK_TARGET}).\n"
        ).encode("utf-8")
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.notice = self.root / NOTICE_PATH
        self.notice.parent.mkdir(parents=True)
        self.notice.write_bytes(self.notice_bytes)
        self.readme = self.root / README_PATH
        self.readme.write_bytes(self.readme_bytes)

    def test_frozen_license_is_independent_nonempty_evidence(self) -> None:
        digest = hashlib.sha256(self.license_bytes).hexdigest()
        self.assertEqual(
            digest, "0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5"
        )
        self.assertTrue(self.license_bytes.endswith(b"\n"))
        self.assertIn(b"Copyright (c) 2026 Matt Pocock\n", self.license_bytes)

    def test_authored_matt_notice_satisfies_contract(self) -> None:
        notice = REPO_ROOT / NOTICE_PATH
        self.assertTrue(notice.is_file(), f"{NOTICE_PATH}: missing required notice file")
        errors = validate_matt_notice(REPO_ROOT, self.license_bytes)
        self.assertEqual(errors, [], "\n".join(errors))

    def test_authored_readme_acknowledgment_resolves_to_notice(self) -> None:
        readme = (REPO_ROOT / README_PATH).read_text(encoding="utf-8")
        self.assertIn("Matt Pocock", readme, f"{README_PATH}: missing Matt acknowledgment")
        self.assertIn(f"]({ACK_TARGET})", readme, f"{README_PATH}: missing direct notice link")
        errors = validate_matt_acknowledgment(REPO_ROOT)
        self.assertEqual(errors, [], "\n".join(errors))

    def test_valid_temporary_notice_passes_before_sibling_ledger_exists(self) -> None:
        errors = validate_matt_notice(self.root, self.license_bytes)
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertFalse(self.notice.with_name("ledger.json").exists())

    def test_missing_notice_names_required_filename_and_input_defect(self) -> None:
        self.notice.unlink()
        errors = validate_matt_notice(self.root, self.license_bytes)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(NOTICE_PATH.as_posix(), errors[0])
        self.assertIn("missing", errors[0].lower())

    def test_isolated_license_defects_name_notice_and_targeted_contract(self) -> None:
        block = b"```text\n" + self.license_bytes + b"```\n"
        cases = (
            ("missing section", self.notice_bytes.replace(b"## License", b"## Terms"), "License section"),
            ("duplicate section", self.notice_bytes + b"\n## License\n", "License section"),
            ("missing block", self.notice_bytes.replace(block, b""), "text block"),
            ("wrong fence", self.notice_bytes.replace(b"```text\n", b"```markdown\n"), "text block"),
            ("duplicate block", self.notice_bytes + b"\n" + block, "text block"),
            ("holder byte", self.notice_bytes.replace(b"2026 Matt Pocock", b"2026 Other Holder"), "license bytes"),
            ("content byte", self.notice_bytes.replace(b"free of charge", b"free of charges"), "license bytes"),
            ("missing final newline", self.notice_bytes.replace(b"SOFTWARE.\n```", b"SOFTWARE.```"), "license bytes"),
            ("changed final newline", self.notice_bytes.replace(b"SOFTWARE.\n```", b"SOFTWARE.\r\n```"), "license bytes"),
            ("extra blank line", self.notice_bytes.replace(b"SOFTWARE.\n```", b"SOFTWARE.\n\n```"), "license bytes"),
            ("newline conversion", self.notice_bytes.replace(self.license_bytes, self.license_bytes.replace(b"\n", b"\r\n")), "license bytes"),
            ("block outside section", self.notice_bytes.replace(b"## License\n\n" + block, block + b"\n## License\n"), "text block"),
            ("block hidden in another section", self.notice_bytes.replace(b"## License\n\n", b"## License\n\n## Other\n\n"), "text block"),
        )
        for name, content, field in cases:
            with self.subTest(defect=name):
                self.notice.write_bytes(content)
                errors = validate_matt_notice(self.root, self.license_bytes)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(NOTICE_PATH.as_posix(), errors[0])
                self.assertIn(field, errors[0])
                if field == "license bytes":
                    self.assertIn(LICENSE_PATH.name, errors[0])

    def test_license_section_inside_enclosing_fence_is_not_a_section(self) -> None:
        prefix, section = self.notice_bytes.split(b"## License\n", 1)
        section = b"## License\n" + section
        cases = (
            ("four backticks", b"````markdown\n", b"````\n"),
            ("tildes", b"~~~markdown\n", b"~~~\n"),
            ("one-space indentation", b" ````markdown\n", b" ````\n"),
            ("three-space indentation", b"   ~~~markdown\n", b"   ~~~\n"),
            ("unclosed backticks", b"````markdown\n", b""),
            ("unclosed tildes", b"~~~markdown\n", b""),
            ("wrong closing character", b"````markdown\n", b"~~~~\n"),
            ("shorter closing fence", b"````markdown\n", b"```\n"),
        )
        for name, opening, closing in cases:
            with self.subTest(enclosing_fence=name):
                self.notice.write_bytes(prefix + opening + section + closing)
                errors = validate_matt_notice(self.root, self.license_bytes)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(NOTICE_PATH.as_posix(), errors[0])
                self.assertIn("License section", errors[0])

    def test_unrelated_closed_fences_do_not_hide_the_real_license_section(self) -> None:
        examples = (
            b"```example\nA small unrelated code sample.\n```\n\n",
            b"~~~example\nA small unrelated code sample.\n~~~\n\n",
            b"   ````example\nA small unrelated code sample.\n   ````\n\n",
        )
        for example in examples:
            with self.subTest(fence=example.split(b"\n", 1)[0]):
                self.notice.write_bytes(example + self.notice_bytes)
                errors = validate_matt_notice(self.root, self.license_bytes)
                self.assertEqual(errors, [], "\n".join(errors))

    def test_isolated_identity_and_link_defects_name_the_failed_field(self) -> None:
        cases = (
            ("upstream", b"https://github.com/mattpocock/skills", b"https://github.com/mattpocock/skillz", "upstream repository"),
            ("fork", b"https://github.com/racecraft-lab/skills", b"https://github.com/racecraft-lab/skillz", "provenance fork"),
            ("tag", b"speckit-pro-baseline", b"other-baseline", "baseline tag"),
            ("pin", PIN.encode(), b"0" * 40, "pinned commit"),
            ("MIT", b"- License: MIT", b"- License: BSD", "MIT license"),
            ("landed explanation", b"identified as landed", b"identified as planned", "modified derivatives"),
            ("modified explanation", b"modified derivatives", b"unmodified copies", "modified derivatives"),
            ("ledger link", b"](ledger.json)", b"](other.json)", "ledger.json link"),
            ("plain ledger", b"[skill ledger](ledger.json)", b"ledger.json", "ledger.json link"),
        )
        for name, original, replacement, field in cases:
            with self.subTest(defect=name):
                content = self.notice_bytes.replace(original, replacement)
                self.notice.write_bytes(content)
                errors = validate_matt_notice(self.root, self.license_bytes)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(NOTICE_PATH.as_posix(), errors[0])
                self.assertIn(field, errors[0])

    def test_valid_temporary_acknowledgment_names_holder_and_resolves(self) -> None:
        errors = validate_matt_acknowledgment(self.root)
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertTrue((self.readme.parent / ACK_TARGET).is_file())

    def test_missing_readme_names_the_required_input(self) -> None:
        self.readme.unlink()
        errors = validate_matt_acknowledgment(self.root)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(README_PATH.as_posix(), errors[0])
        self.assertIn("missing", errors[0].lower())

    def test_isolated_acknowledgment_defects_name_the_readme(self) -> None:
        cases = (
            ("holder", self.readme_bytes.replace(b"Matt Pocock", b"Other Holder"), "Matt Pocock"),
            ("link", self.readme_bytes.replace(f"]({ACK_TARGET})".encode(), b"](missing.md)"), "notice link"),
            ("remote link", self.readme_bytes.replace(ACK_TARGET.encode(), b"https://example.com/notice"), "notice link"),
            ("plain path", self.readme_bytes.replace(f"[MIT notice]({ACK_TARGET})".encode(), ACK_TARGET.encode()), "notice link"),
            ("unrelated holder", self.readme_bytes.replace(b"We acknowledge Matt Pocock's upstream skills. ", b"") + b"\nMatt Pocock\n", "acknowledgment"),
        )
        for name, content, field in cases:
            with self.subTest(defect=name):
                self.readme.write_bytes(content)
                errors = validate_matt_acknowledgment(self.root)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(README_PATH.as_posix(), errors[0])
                self.assertIn(field, errors[0])

    def test_dangling_acknowledgment_names_the_missing_notice(self) -> None:
        self.notice.unlink()
        errors = validate_matt_acknowledgment(self.root)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(README_PATH.as_posix(), errors[0])
        self.assertIn(NOTICE_PATH.as_posix(), errors[0])
        self.assertIn("missing", errors[0].lower())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MattNoticeTests)
    raise SystemExit(run_counted(suite, label="test-upstream-skill-attribution"))

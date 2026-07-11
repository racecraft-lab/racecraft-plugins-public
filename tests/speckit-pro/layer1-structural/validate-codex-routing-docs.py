#!/usr/bin/env python3
"""Validate repository-grounded facts in the Codex routing PRD and roadmap.

This validator intentionally checks only deterministic repository facts and
cross-document ownership. Future files may be named before they exist, but the
corresponding Key Files bullet must carry an explicit ``[proposed]`` marker.
"""

from __future__ import annotations

import glob
import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


PRD = REPO_ROOT / "docs" / "prd-codex-chatgpt-agent-routing.md"
ROADMAP = REPO_ROOT / "docs" / "ai" / "specs" / "codex-chatgpt-agent-routing-technical-roadmap.md"
MOC = REPO_ROOT / "docs" / "ai" / "specs" / "codex-chatgpt-agent-routing-roadmap-MOC.md"
FIXTURE_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency" / "fixtures-codex"
FIXTURE_README = FIXTURE_ROOT / "README.md"
AGENT_ROOT = REPO_ROOT / "speckit-pro" / "codex-agents"

EXPECTED_FIXTURES = {
    "codebase-analyst",
    "domain-researcher",
    "spec-context-analyst",
}
EXPECTED_AGENTS = {
    "analyze-executor.toml",
    "autopilot-fast-helper.toml",
    "checklist-executor.toml",
    "clarify-executor.toml",
    "codebase-analyst.toml",
    "domain-researcher.toml",
    "implement-executor.toml",
    "phase-executor.toml",
    "spec-context-analyst.toml",
    "uat-runbook-author.toml",
}
EXPECTED_SUPPORT_PLAN_KEYS = {
    "business_grandfathered_codex_seat",
    "business_standard",
    "edu_flexible",
    "edu_included_seat",
    "enterprise_flexible",
    "enterprise_included_seat",
    "enterprise_legacy_message",
    "free",
    "go",
    "plus",
    "pro_20x",
    "pro_5x",
}
LIVE_CORPUS_PATHS = {
    "tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py",
    "tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py",
    "tests/speckit-pro/layer6-efficiency/fixtures-codex/",
    "tests/speckit-pro/unit/test-efficiency-codex-runner.py",
    "tests/speckit-pro/unit/test-efficiency-runner-portability.py",
}
EXPECTED_G56R_002_ACS = {
    "AC-2.2",
    "AC-2.3",
    "AC-2.4",
    "AC-2.5",
    "AC-2.15",
    "AC-2.16",
}
EXPECTED_G56R_003_ACS = {
    "AC-2.1",
    "AC-2.19",
    "AC-2.20",
    "AC-2.21",
    *(f"AC-2.{number}" for number in range(6, 15)),
}
EXPECTED_DEPENDENCIES = {
    "G56R-001": set(),
    "G56R-002": {"G56R-001"},
    "G56R-003": {"G56R-002"},
    "G56R-004": {"G56R-003"},
    "G56R-005": {"G56R-004"},
    "G56R-006": {"G56R-005"},
    "G56R-007": {"G56R-006"},
    "G56R-008": {"G56R-006"},
    "G56R-009": {"G56R-006"},
    "G56R-010": {"G56R-006"},
    "G56R-011": {"G56R-007", "G56R-008", "G56R-009", "G56R-010"},
}
REPO_PATH_PREFIXES = ("dist/", "docs/", "scripts/", "speckit-pro/", "tests/")
OBSOLETE_LAYER6_PATHS = {
    "run-efficiency-benchmarks.sh",
    "quality-scorer.sh",
    "test-efficiency-codex-runner.sh",
}


@dataclass(frozen=True)
class KeyFileEntry:
    line_number: int
    path: str
    proposed: bool


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def roadmap_section(text: str, spec_id: str) -> str:
    match = re.search(
        rf"^### {re.escape(spec_id)}:.*?(?=^### G56R-\d{{3}}:|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(0) if match else ""


def key_file_entries(text: str) -> list[KeyFileEntry]:
    entries: list[KeyFileEntry] = []
    in_key_files = False
    saw_entry = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line == "**Key Files:**":
            in_key_files = True
            saw_entry = False
            continue
        if not in_key_files:
            continue
        if line.startswith("---") or line.startswith("### "):
            in_key_files = False
            continue
        if saw_entry and not line.strip():
            in_key_files = False
            continue
        if not line.startswith("- "):
            continue
        saw_entry = True
        match = re.search(r"`([^`]+)`", line)
        if match:
            entries.append(
                KeyFileEntry(
                    line_number=line_number,
                    path=match.group(1),
                    proposed="[proposed]" in line.casefold(),
                )
            )
    return entries


def missing_current_key_files(entries: list[KeyFileEntry]) -> list[str]:
    failures: list[str] = []
    for entry in entries:
        if entry.proposed:
            continue
        raw = entry.path.rstrip("/")
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts:
            failures.append(f"line {entry.line_number}: Key Files path must be repository-relative: {entry.path}")
            continue
        if any(character in raw for character in "*?["):
            exists = bool(glob.glob(str(REPO_ROOT / raw)))
        else:
            exists = (REPO_ROOT / raw).exists()
        if not exists:
            failures.append(
                f"line {entry.line_number}: current Key Files path does not exist; "
                f"fix it or mark it [proposed]: {entry.path}"
            )
    return failures


def section_key_paths(section: str) -> set[str]:
    return {entry.path for entry in key_file_entries(section)}


def roadmap_titles(text: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"^### (G56R-\d{3}):\s+(.+)$", text, flags=re.MULTILINE)
    }


def crosswalk(text: str) -> dict[str, tuple[str, str, str]]:
    rows: dict[str, tuple[str, str, str]] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not re.fullmatch(r"G56R-\d{3}", cells[2]):
            continue
        rows[cells[2]] = (cells[0], cells[1], cells[3])
    return rows


def normalized_title(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.casefold())
    return " ".join(word for word in words if word != "and")


def mandatory_plan_keys(text: str) -> set[str]:
    match = re.search(
        r"`mandatory_plan_keys`\s*=\s*\[(.*?)\]",
        text,
        flags=re.DOTALL,
    )
    return set(re.findall(r"`([a-z0-9_]+)`", match.group(1))) if match else set()


def expand_acceptance_criteria(value: str, defined: set[str] | None = None) -> set[str]:
    expanded: set[str] = set()
    for start_section, start_number, end_section, end_number in re.findall(
        r"AC-(\d+)\.(\d+)\s+through\s+AC-(\d+)\.(\d+)", value
    ):
        if start_section != end_section:
            continue
        expanded.update(
            f"AC-{start_section}.{number}"
            for number in range(int(start_number), int(end_number) + 1)
        )
    without_ranges = re.sub(
        r"AC-\d+\.\d+\s+through\s+AC-\d+\.\d+",
        "",
        value,
    )
    expanded.update(re.findall(r"AC-\d+\.\d+", without_ranges))
    if defined:
        for section in re.findall(r"AC-(\d+)\.\*", value):
            expanded.update(ac for ac in defined if ac.startswith(f"AC-{section}."))
    return expanded


def expand_spec_ids(value: str) -> set[str]:
    expanded = set(re.findall(r"G56R-\d{3}", value))
    for start, end in re.findall(r"G56R-(\d{3})\s+through\s+G56R-(\d{3})", value):
        expanded.update(f"G56R-{number:03d}" for number in range(int(start), int(end) + 1))
    return expanded


def roadmap_dependencies(text: str) -> dict[str, set[str]]:
    dependencies: dict[str, set[str]] = {}
    for spec_id in EXPECTED_DEPENDENCIES:
        section = roadmap_section(text, spec_id)
        match = re.search(r"\*\*Depends On:\*\*\s*(.*?)\s*\|", section, flags=re.DOTALL)
        dependencies[spec_id] = expand_spec_ids(match.group(1)) if match else set()
    return dependencies


def current_repo_paths(path: Path) -> list[KeyFileEntry]:
    entries: list[KeyFileEntry] = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        proposed = "[proposed]" in line.casefold()
        for code in re.findall(r"`([^`]+)`", line):
            value = code.strip()
            if value.startswith("python3 "):
                value = value.split()[1]
            else:
                value = value.split()[0]
            if value.startswith(REPO_PATH_PREFIXES):
                entries.append(KeyFileEntry(line_number, value, proposed))
    return entries


def missing_current_doc_paths(path: Path) -> list[str]:
    failures: list[str] = []
    for entry in current_repo_paths(path):
        if entry.proposed:
            continue
        raw = re.sub(r"<[^>]+>", "*", entry.path.rstrip("/"))
        exists = bool(glob.glob(str(REPO_ROOT / raw))) if any(char in raw for char in "*?[") else (REPO_ROOT / raw).exists()
        if not exists:
            failures.append(f"{path.relative_to(REPO_ROOT)}:{entry.line_number}: {entry.path}")
    return failures


def broken_relative_links(path: Path) -> list[str]:
    failures: list[str] = []
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        for destination in re.findall(r"\[[^\]]+\]\(([^)]+)\)", line):
            if re.match(r"^(?:https?://|mailto:|#)", destination):
                continue
            relative = destination.split("#", 1)[0]
            if relative and not (path.parent / relative).resolve().exists():
                failures.append(f"{path.relative_to(REPO_ROOT)}:{line_number}: {destination}")
    return failures


class ValidateCodexRoutingDocs(unittest.TestCase):
    def test_current_facts_and_ownership(self) -> None:
        with self.subTest(msg="Codex routing PRD and technical roadmap exist"):
            self.assertTrue(PRD.is_file() and ROADMAP.is_file(), f"missing {PRD} or {ROADMAP}")

        prd_text = read_text(PRD)
        roadmap_text = read_text(ROADMAP)
        fixture_readme_text = read_text(FIXTURE_README)
        entries = key_file_entries(roadmap_text)

        with self.subTest(msg="current roadmap Key Files paths exist or are explicitly proposed"):
            self.assertEqual(missing_current_key_files(entries), [])

        with self.subTest(msg="current Layer 6 Key Files paths do not use obsolete shell entrypoints"):
            obsolete = sorted(
                entry.path
                for entry in entries
                if not entry.proposed
                and entry.path.endswith(".sh")
                and (
                    entry.path.startswith("tests/speckit-pro/layer6-efficiency/")
                    or entry.path.startswith("tests/speckit-pro/unit/test-efficiency-")
                )
            )
            self.assertEqual(obsolete, [])

        with self.subTest(msg="routing docs have no broken current paths or obsolete Layer 6 names"):
            docs = (PRD, ROADMAP, MOC, FIXTURE_README)
            broken = [failure for path in docs for failure in missing_current_doc_paths(path)]
            combined = "\n".join(read_text(path) for path in docs)
            stale = sorted(name for name in OBSOLETE_LAYER6_PATHS if name in combined)
            self.assertEqual(broken, [])
            self.assertEqual(stale, [])

        with self.subTest(msg="routing docs have no broken relative Markdown links"):
            docs = (PRD, ROADMAP, MOC, FIXTURE_README)
            broken = [failure for path in docs for failure in broken_relative_links(path)]
            self.assertEqual(broken, [])

        with self.subTest(msg="Layer 6 has exactly the three current Codex fixture directories"):
            actual = {path.name for path in FIXTURE_ROOT.iterdir() if path.is_dir()} if FIXTURE_ROOT.is_dir() else set()
            self.assertEqual(actual, EXPECTED_FIXTURES)

        with self.subTest(msg="Codex source inventory has exactly ten agent TOMLs"):
            actual = {path.name for path in AGENT_ROOT.glob("*.toml")} if AGENT_ROOT.is_dir() else set()
            self.assertEqual(actual, EXPECTED_AGENTS)

        with self.subTest(msg="routing docs state the current three-fixture ten-agent inventory"):
            self.assertIn("three existing fixtures", prd_text)
            self.assertIn("ten Codex custom agents", prd_text)
            self.assertIn("three-current/seven-missing fixture inventory", roadmap_text)
            self.assertIn("ten `speckit-pro/codex-agents/*.toml` files", roadmap_text)
            self.assertIn("All three current Codex fixtures", fixture_readme_text)

        with self.subTest(msg="PRD and roadmap freeze the same mandatory plan-support rows"):
            self.assertEqual(mandatory_plan_keys(prd_text), EXPECTED_SUPPORT_PLAN_KEYS)
            self.assertEqual(mandatory_plan_keys(roadmap_text), EXPECTED_SUPPORT_PLAN_KEYS)

        section_002 = roadmap_section(roadmap_text, "G56R-002")
        section_003 = roadmap_section(roadmap_text, "G56R-003")
        paths_002 = section_key_paths(section_002)
        paths_003 = section_key_paths(section_003)

        with self.subTest(msg="G56R-002 owns telemetry and trace-schema files, not live corpus files"):
            telemetry_paths = {
                path for path in paths_002 if any(term in path.casefold() for term in ("telemetry", "trace", "schema"))
            }
            self.assertTrue(
                section_002 and telemetry_paths and paths_002.isdisjoint(LIVE_CORPUS_PATHS),
                f"G56R-002 paths={sorted(paths_002)} telemetry_paths={sorted(telemetry_paths)}",
            )

        with self.subTest(msg="G56R-003 owns the active Python corpus runner scorer fixtures and tests"):
            self.assertTrue(
                section_003 and LIVE_CORPUS_PATHS.issubset(paths_003),
                f"missing from G56R-003: {sorted(LIVE_CORPUS_PATHS - paths_003)}",
            )

        with self.subTest(msg="live corpus and scoring paths are owned only by G56R-003"):
            self.assertEqual(paths_002 & LIVE_CORPUS_PATHS, set())

        rows = crosswalk(prd_text)
        titles = roadmap_titles(roadmap_text)
        expected_specs = {f"G56R-{number:03d}" for number in range(1, 12)}

        with self.subTest(msg="PRD crosswalk and roadmap define all eleven G56R specs"):
            self.assertEqual(set(rows), expected_specs)
            self.assertEqual(set(titles), expected_specs)

        with self.subTest(msg="PRD crosswalk feature ownership matches roadmap section titles"):
            mismatches = {
                spec_id: (rows[spec_id][0], titles[spec_id])
                for spec_id in expected_specs & rows.keys() & titles.keys()
                if normalized_title(rows[spec_id][0]) != normalized_title(titles[spec_id])
            }
            self.assertEqual(mismatches, {})

        with self.subTest(msg="every PRD acceptance criterion has exactly one SPEC owner"):
            defined = set(re.findall(r"\*\*(AC-\d+\.\d+)", prd_text))
            ownership: dict[str, list[str]] = {ac: [] for ac in defined}
            for spec_id, (_, expression, _) in rows.items():
                for ac in expand_acceptance_criteria(expression, defined):
                    ownership.setdefault(ac, []).append(spec_id)
            invalid = {ac: owners for ac, owners in ownership.items() if len(owners) != 1}
            self.assertEqual(invalid, {})

        with self.subTest(msg="PRD crosswalk dependencies match roadmap section dependencies"):
            crosswalk_dependencies = {
                spec_id: expand_spec_ids(row[2]) for spec_id, row in rows.items()
            }
            self.assertEqual(crosswalk_dependencies, EXPECTED_DEPENDENCIES)
            self.assertEqual(roadmap_dependencies(roadmap_text), EXPECTED_DEPENDENCIES)

        with self.subTest(msg="G56R-002 and G56R-003 acceptance-criteria ownership is exact and disjoint"):
            actual_002 = expand_acceptance_criteria(rows.get("G56R-002", ("", ""))[1])
            actual_003 = expand_acceptance_criteria(rows.get("G56R-003", ("", ""))[1])
            self.assertEqual(actual_002, EXPECTED_G56R_002_ACS)
            self.assertEqual(actual_003, EXPECTED_G56R_003_ACS)
            self.assertTrue(actual_002.isdisjoint(actual_003))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexRoutingDocs)
    return run_counted(suite, label="validate-codex-routing-docs")


if __name__ == "__main__":
    raise SystemExit(main())

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
EXPECTED_SOURCE_AGENTS = {
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
EXPECTED_CORE_AGENTS = EXPECTED_SOURCE_AGENTS - {"autopilot-fast-helper.toml"}
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
    "gov_managed",
    "healthcare_managed",
    "clinicians_managed",
    "plus",
    "pro_20x",
    "pro_5x",
    "regulated_workspace_managed",
    "teachers_managed",
}
EXPECTED_NAMED_SUPPORT_CATEGORIES = {
    "chatgpt_fedramp",
    "chatgpt_for_clinicians",
    "chatgpt_for_healthcare",
    "chatgpt_for_teachers",
    "chatgpt_gov",
    "enterprise_regulated_workspace",
}
EXPECTED_CATEGORY_ROW_MAPPINGS = {
    "chatgpt_for_clinicians": "clinicians_managed",
    "chatgpt_for_healthcare": "healthcare_managed",
    "chatgpt_for_teachers": "teachers_managed",
    "chatgpt_gov": "gov_managed",
    "enterprise_regulated_workspace": "regulated_workspace_managed",
}
REQUIRED_CANONICAL_FIELDS = {
    "canonical_baseline_deliverable",
    "canonical_candidate_set_hash",
    "canonical_lock_timestamp",
    "canonical_row_key",
    "canonical_selection_rationale",
    "canonical_selection_rule_version",
    "canonical_subscription_environment_id",
}
REQUIRED_ROW_COMPARATOR_FIELDS = {
    "baseline_comparator_type",
    "baseline_exact_treatment_evidence_hashes",
    "baseline_policy_id",
    "baseline_support_state",
    "comparator_claim_boundary",
    "row_reference_policy_id",
    "target_population_weight",
}
REQUIRED_POPULATION_SNAPSHOT_FIELDS = {
    "target_population_snapshot_id",
    "snapshot_source",
    "query_or_derivation_version",
    "measurement_start",
    "measurement_end",
    "population_definition",
    "inclusion_and_exclusion_rules",
    "unknown_plan_handling",
    "coverage_numerator",
    "coverage_denominator",
    "minimum_coverage_threshold",
    "weight_normalization_rule",
    "fallback_canonical_row_rule",
    "snapshot_hash",
}
REQUIRED_ROW_REFERENCE_SELECTION_FIELDS = {
    "row_reference_selection_rule_id",
    "eligible_reference_policy_set",
    "required_quality_and_contract_floors",
    "relationship_to_production_policy",
    "compatibility_projection_rules",
    "selection_metric",
    "selection_precedence",
    "tie_break_rule",
    "selection_evidence_hash",
    "reference_qualification_evidence_id",
}
COMPONENT_SPEC_IDS = ("G56R-007", "G56R-008", "G56R-009")
FORBIDDEN_HELPER_STATE_PATTERNS = (
    r"installed[-_ ]disabled",
    r"copy\s+the\s+helper\s+toml\s+disabled",
    r"optional\s+toml\s+disabled",
)
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


def declared_code_list(text: str, label: str) -> set[str]:
    match = re.search(
        rf"`{re.escape(label)}`\s*=\s*\[(.*?)\]",
        text,
        flags=re.DOTALL,
    )
    return set(re.findall(r"`([a-z0-9_]+)`", match.group(1))) if match else set()


def declared_code_mappings(text: str, label: str) -> dict[str, str]:
    match = re.search(
        rf"`{re.escape(label)}`\s*=\s*\[(.*?)\]",
        text,
        flags=re.DOTALL,
    )
    if not match:
        return {}
    return {
        source: destination
        for source, destination in re.findall(
            r"`([a-z0-9_]+)\s*->\s*([a-z0-9_]+)`",
            match.group(1),
        )
    }


def acceptance_criterion_section(text: str, ac_id: str) -> str:
    match = re.search(
        rf"^- \*\*{re.escape(ac_id)}(?:\s+[^*]+)?\*\*:.*?(?=^- \*\*AC-\d+\.\d+|^### |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(0) if match else ""


def inline_code_fields(text: str) -> set[str]:
    return set(re.findall(r"`([a-z][a-z0-9_]+)`", text))


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
            self.assertEqual(actual, EXPECTED_SOURCE_AGENTS)

        with self.subTest(msg="routing docs state the current three-fixture ten-agent inventory"):
            self.assertIn("three existing fixtures", prd_text)
            self.assertIn("ten Codex custom agents", prd_text)
            self.assertIn("three-current/seven-missing fixture inventory", roadmap_text)
            self.assertIn("ten `speckit-pro/codex-agents/*.toml` files", roadmap_text)
            self.assertIn("All three current Codex fixtures", fixture_readme_text)

        with self.subTest(msg="PRD and roadmap freeze the same mandatory plan-support rows"):
            self.assertEqual(declared_code_list(prd_text, "mandatory_plan_keys"), EXPECTED_SUPPORT_PLAN_KEYS)
            self.assertEqual(declared_code_list(roadmap_text, "mandatory_plan_keys"), EXPECTED_SUPPORT_PLAN_KEYS)

        with self.subTest(msg="every named managed-workspace category is mapped or explicitly excluded"):
            for text in (prd_text, roadmap_text):
                self.assertEqual(
                    declared_code_list(text, "named_category_keys"),
                    EXPECTED_NAMED_SUPPORT_CATEGORIES,
                )
                self.assertEqual(
                    declared_code_mappings(text, "named_category_row_mappings"),
                    EXPECTED_CATEGORY_ROW_MAPPINGS,
                )
            manifest_sections = (
                acceptance_criterion_section(prd_text, "AC-1.6"),
                roadmap_section(roadmap_text, "G56R-001"),
            )
            self.assertTrue(all("chatgpt_fedramp" in section and "named exclusion" in section for section in manifest_sections))

        with self.subTest(msg="support manifest requires exactly one pre-outcome canonical row"):
            manifest_sections = (
                acceptance_criterion_section(prd_text, "AC-1.6"),
                roadmap_section(roadmap_text, "G56R-001"),
            )
            self.assertTrue(all("exactly one canonical row" in section.casefold() for section in manifest_sections))
            self.assertTrue(all("before screening" in section.casefold() for section in manifest_sections))

        with self.subTest(msg="canonical row freezes environment rationale candidate set and treatment delivery"):
            manifest_sections = (
                acceptance_criterion_section(prd_text, "AC-1.6"),
                roadmap_section(roadmap_text, "G56R-001"),
            )
            for section in manifest_sections:
                self.assertTrue(REQUIRED_CANONICAL_FIELDS.issubset(inline_code_fields(section)))
                self.assertIn("production", section.casefold())
                self.assertIn("candidate", section.casefold())
                self.assertIn("deliver", section.casefold())

        with self.subTest(msg="canonical weights have a complete frozen population snapshot and one fallback"):
            manifest_sections = (
                acceptance_criterion_section(prd_text, "AC-1.6"),
                roadmap_section(roadmap_text, "G56R-001"),
            )
            for section in manifest_sections:
                fields = inline_code_fields(section)
                self.assertTrue(REQUIRED_POPULATION_SNAPSHOT_FIELDS.issubset(fields))
                self.assertIn("exactly one `target_population_snapshot` object", section.casefold())
                self.assertIn("shared `target_population_snapshot_id`", section.casefold())
                self.assertIn("exactly one predeclared `fallback_canonical_row_rule`", section.casefold())
                self.assertIsNotNone(re.search(r"use\s+`plus`", section, flags=re.IGNORECASE))
                self.assertIn("90 complete utc days", section.casefold())
                self.assertIn("0.95", section)
                self.assertIsNotNone(
                    re.search(r"alternate\s+fallbacks\s+are\s+prohibited", section, flags=re.IGNORECASE)
                )
                self.assertIn("invalidates", section.casefold())

        with self.subTest(msg="every support row declares baseline or row-reference comparator behavior"):
            manifest_sections = (
                acceptance_criterion_section(prd_text, "AC-1.6"),
                roadmap_section(roadmap_text, "G56R-001"),
            )
            for section in manifest_sections:
                self.assertTrue(REQUIRED_ROW_COMPARATOR_FIELDS.issubset(inline_code_fields(section)))
                self.assertIn("every row", section.casefold())
            comparator_ac = acceptance_criterion_section(prd_text, "AC-2.13")
            self.assertIn("row-reference", comparator_ac.casefold())
            self.assertIsNotNone(
                re.search(
                    r"cannot claim\s+improvement over production",
                    comparator_ac,
                    flags=re.IGNORECASE,
                )
            )

        with self.subTest(msg="row-reference selection is deterministic and production-derived"):
            reference_sections = (
                acceptance_criterion_section(prd_text, "AC-2.13"),
                roadmap_section(roadmap_text, "G56R-001"),
            )
            for section in reference_sections:
                fields = inline_code_fields(section)
                self.assertTrue(REQUIRED_ROW_REFERENCE_SELECTION_FIELDS.issubset(fields))
                self.assertIsNotNone(
                    re.search(
                        r"exact-treatment-deliverable\s+(?:compatibility\s+)?projections?\s+of\s+(?:the\s+)?immutable\s+production\s+core",
                        section,
                        flags=re.IGNORECASE,
                    )
                )
                self.assertIn("changed-agent count", section.casefold())
                self.assertIn("changed-field count", section.casefold())
                self.assertIsNotNone(
                    re.search(r"candidate\s+outcomes?.{0,80}cannot\s+(?:affect|influence)", section, flags=re.IGNORECASE | re.DOTALL)
                )
                self.assertIsNotNone(
                    re.search(r"absolute.{0,40}floors?", section, flags=re.IGNORECASE | re.DOTALL)
                )
                self.assertIsNotNone(
                    re.search(r"(?:changing|change).{0,120}invalidates", section, flags=re.IGNORECASE | re.DOTALL)
                )
                self.assertIn("reference_qualification_evidence_id", section)
                self.assertIn("reference-qualification corpus", section.casefold())
                self.assertIn("disjoint", section.casefold())

        with self.subTest(msg="optional helper uses only installed_enabled or not_installed states"):
            combined = "\n".join((prd_text, roadmap_text, read_text(MOC)))
            forbidden = [pattern for pattern in FORBIDDEN_HELPER_STATE_PATTERNS if re.search(pattern, combined, flags=re.IGNORECASE)]
            self.assertEqual(forbidden, [])
            self.assertIn("`installed_enabled`", combined)
            self.assertIn("`not_installed`", combined)

        with self.subTest(msg="Spark attempts are hard core-policy failures not invalidated observations"):
            core_sections = (
                acceptance_criterion_section(prd_text, "AC-2.18"),
                acceptance_criterion_section(prd_text, "AC-8.9"),
                roadmap_section(roadmap_text, "G56R-010"),
                roadmap_section(roadmap_text, "G56R-011"),
            )
            for section in core_sections:
                self.assertIn("`not_installed`", section)
                self.assertIsNotNone(
                    re.search(
                        r"every\s+primary\s+and\s+secondary\s+arm",
                        section,
                        flags=re.IGNORECASE,
                    )
                )
            failure_contract = "\n".join(
                (
                    acceptance_criterion_section(prd_text, "AC-2.18"),
                    acceptance_criterion_section(prd_text, "AC-8.9"),
                    roadmap_section(roadmap_text, "G56R-010"),
                    roadmap_section(roadmap_text, "G56R-011"),
                )
            )
            self.assertIn("candidate-caused", failure_contract.casefold())
            self.assertIn("`A_i = 0`", failure_contract)
            self.assertIn("hard contract failure", failure_contract.casefold())
            self.assertIn("cannot be rerun", failure_contract.casefold())
            stale = re.search(
                r"(?:spark|any) invocation invalidates",
                "\n".join((prd_text, roadmap_text)),
                flags=re.IGNORECASE,
            )
            self.assertIsNone(stale)

        with self.subTest(msg="optional helper identity hashes a row-aware installation-state mapping"):
            identity_sections = (
                acceptance_criterion_section(prd_text, "AC-3.1"),
                roadmap_section(roadmap_text, "G56R-006"),
                roadmap_section(roadmap_text, "G56R-010"),
            )
            for section in identity_sections:
                self.assertIn("optional_helper_policy_id", section)
                self.assertIn("helper_installation_state_id", section)
                self.assertIsNotNone(
                    re.search(r"plan_key\s*->\s*helper_installation_state_id", section)
                )
                self.assertIn("`installed_enabled`", section)
                self.assertIn("`not_installed`", section)

        with self.subTest(msg="documents distinguish ten source agents from nine required destination agents"):
            self.assertEqual(len(EXPECTED_SOURCE_AGENTS), 10)
            self.assertEqual(len(EXPECTED_CORE_AGENTS), 9)
            self.assertIn("Source and generated payload inventory contain all ten agent TOMLs", prd_text)
            self.assertIn("plugin-managed destination set", prd_text)
            self.assertIn("exactly nine required core TOMLs", prd_text)
            self.assertIn("plugin-managed destination set", roadmap_text)
            self.assertIn("conditional helper", roadmap_text)

        with self.subTest(msg="destination counts only plugin-managed agents and removes stale Spark"):
            destination_sections = (
                acceptance_criterion_section(prd_text, "AC-3.4"),
                roadmap_section(roadmap_text, "G56R-006"),
                roadmap_section(roadmap_text, "G56R-011"),
            )
            for section in destination_sections:
                folded = section.casefold()
                self.assertIn("plugin-managed destination set", folded)
                self.assertIn("nine", folded)
                self.assertIn("user-owned", folded)
                self.assertIn("byte-for-byte", folded)
                self.assertIn("stale", folded)
                self.assertIn("spark", folded)
            combined = "\n".join((prd_text, roadmap_text))
            self.assertIsNone(
                re.search(
                    r"\b(?:a|every) destination (?:contains|has) exactly\s+(?:the\s+)?nine\b",
                    combined,
                    flags=re.IGNORECASE,
                )
            )

        with self.subTest(msg="component stages qualify or lock while only integrated release proof promotes"):
            component_text = "\n".join(
                [
                    acceptance_criterion_section(prd_text, "AC-4.2"),
                    acceptance_criterion_section(prd_text, "AC-5.3"),
                    acceptance_criterion_section(prd_text, "AC-6.4"),
                    *(roadmap_section(roadmap_text, spec_id) for spec_id in COMPONENT_SPEC_IDS),
                    read_text(MOC),
                ]
            )
            self.assertIsNone(re.search(r"\bpromot\w*", component_text, flags=re.IGNORECASE))
            prd_without_gate = prd_text.replace(acceptance_criterion_section(prd_text, "AC-8.9"), "")
            roadmap_without_release = roadmap_text.replace(roadmap_section(roadmap_text, "G56R-011"), "")
            self.assertIsNone(re.search(r"\bpromot\w*", prd_without_gate, flags=re.IGNORECASE))
            self.assertIsNone(re.search(r"\bpromot\w*", roadmap_without_release, flags=re.IGNORECASE))
            self.assertIsNotNone(
                re.search(
                    r"sole\s+promotion\s+decision",
                    acceptance_criterion_section(prd_text, "AC-8.9"),
                )
            )

        with self.subTest(msg="G56R-004 freezes controls and G56R-011 compares the final core"):
            control_contract = roadmap_section(roadmap_text, "G56R-004")
            release_contract = "\n".join(
                (
                    acceptance_criterion_section(prd_text, "AC-8.9"),
                    roadmap_section(roadmap_text, "G56R-011"),
                )
            )
            folded_control = control_contract.casefold()
            self.assertIn("content-address", folded_control)
            self.assertIn("freeze every control parameter", folded_control)
            self.assertIn("dominance metrics and margins", folded_control)
            self.assertIn("quality eligibility", folded_control)
            self.assertIn("does not compare", folded_control)
            folded_release = release_contract.casefold()
            self.assertIn("final `universal_core_policy_id`", folded_release)
            self.assertIn("secondary arms", folded_release)
            self.assertIn("untouched", folded_release)
            self.assertIn("multiplicity", folded_release)
            self.assertIn("cannot change after g56r-004", folded_release)

        with self.subTest(msg="whole-core objective claims improvement not global assembled-policy optimality"):
            problem = prd_text.split("## 2. Goals & Non-goals", 1)[0]
            release_section = roadmap_section(roadmap_text, "G56R-011")
            self.assertIn("improves canonical resource", problem)
            self.assertIn("not materially dominated", problem)
            self.assertIn("globally lowest-resource passing policy", prd_text)
            self.assertIsNotNone(
                re.search(r"does not\s+establish global optimality", release_section)
            )

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

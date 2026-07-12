#!/usr/bin/env python3
"""Layer-4 regression tests for Claude/Codex eval runner skill selection.

Port of ``test-eval-runner-skill-selection.sh`` (XPLAT-010 PR9 T084). The
predecessor executes 13 assertions; the count-parity baseline is pinned at
``tests/speckit-pro/parity/bash-to-python/test-eval-runner-skill-selection-baseline.txt``
(TOTAL: 13).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FUNCTIONAL_SCRIPT = TESTS_ROOT / "layer3-functional" / "run-functional-evals.py"
TRIGGER_SCRIPT = TESTS_ROOT / "layer2-trigger" / "run-trigger-evals.py"
CODEX_FUNCTIONAL_SCRIPT = TESTS_ROOT / "layer3-functional" / "run-functional-evals-codex.py"
CODEX_TRIGGER_SCRIPT = TESTS_ROOT / "layer2-trigger" / "run-trigger-evals-codex.py"
BASELINE = TESTS_ROOT / "parity" / "bash-to-python" / "test-eval-runner-skill-selection-baseline.txt"
CODEX_SKILLS = ("speckit-scaffold-spec", "speckit-status", "speckit-resolve-pr", "install")
LAYER3_CONTRACT_ROOTS = (
    TESTS_ROOT / "layer3-functional" / "evals",
    TESTS_ROOT / "layer3-functional" / "codex-evals",
)
LAYER8_ROOT = TESTS_ROOT / "layer8-parity"

RETIRED_REPOSITORY_HELPERS = frozenset(
    {
        "aggregate-crl.sh",
        "atomicity-route.sh",
        "check-prerequisites.sh",
        "confidence-gate.sh",
        "count-markers.sh",
        "create-new-feature.sh",
        "detect-commands.sh",
        "detect-presets.sh",
        "detect-stack-manager.sh",
        "estimate-reviewable-loc.sh",
        "estimate-spec-size.sh",
        "final-reviewability-backstop.sh",
        "generate-pr-body.sh",
        "generate-spec-index.sh",
        "generate-uat-skeleton.sh",
        "install-curated-set.sh",
        "migrate-structure.sh",
        "multi-pr-emission.sh",
        "o5-topology.sh",
        "parse-consensus-categories.sh",
        "plan-layers.sh",
        "project-fixup.sh",
        "relocate-process-artifacts.sh",
        "resolve-confidence-mode.sh",
        "restack.sh",
        "reviewability-gate.sh",
        "validate-agent-install.sh",
        "validate-gate.sh",
        "validate-pr-packet.sh",
        "validate-pr-workflow-contract.sh",
        "validate-uat-runbook.sh",
    }
)
RETIRED_HELPER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])(" + "|".join(re.escape(name) for name in sorted(RETIRED_REPOSITORY_HELPERS)) + r")(?![A-Za-z0-9_-])"
)

# These evals intentionally describe legacy PROCESS relocation. Retired paths
# are allowed only as negative assertions in expected contract fields.
LAYER3_NEGATIVE_CONTEXTS = {
    ("tests/speckit-pro/layer3-functional/evals/speckit-scaffold-spec-evals.json", 1): {"relocate-process-artifacts.sh"},
    ("tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json", 8): {"relocate-process-artifacts.sh"},
    ("tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json", 23): {"relocate-process-artifacts.sh"},
    ("tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json", 29): {"relocate-process-artifacts.sh"},
}

# Layer 8 Markdown is scanned only in contract files. Each retained retired
# path must live in one explicitly classified section.
LAYER8_MARKDOWN_CONTEXTS = {
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/README.md",
        "Test scenario",
        "relocate-process-artifacts.sh",
    ): "negative",
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/workflow.md",
        "Legacy Input Scenario",
        "migrate-structure.sh",
    ): "legacy_input",
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/workflow.md",
        "Legacy Input Scenario",
        "relocate-process-artifacts.sh",
    ): "legacy_input",
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/workflow.md",
        "No Auto-Run Guard",
        "relocate-process-artifacts.sh",
    ): "negative",
}

NEGATIVE_MARKERS = ("must not", "does not", "never", "reject", "forbidden", "not invoke")
LEGACY_SECTION_MARKERS = ("fixture input", "historical provenance", "neither may be recommended or invoked")

CURRENT_INVENTORY = [
    "Functional runner uses Claude skill for speckit-coach",
    "Trigger runner uses Claude skill for speckit-coach",
    "Trigger runner uses Claude skill for speckit-coach",
    "Codex functional runner uses codex skill for speckit-coach",
    "Codex trigger runner uses codex skill for speckit-coach",
    "Codex functional runner uses codex skill for speckit-scaffold-spec",
    "Codex trigger runner uses codex skill for speckit-scaffold-spec",
    "Codex functional runner uses codex skill for speckit-status",
    "Codex trigger runner uses codex skill for speckit-status",
    "Codex functional runner uses codex skill for speckit-resolve-pr",
    "Codex trigger runner uses codex skill for speckit-resolve-pr",
    "Codex functional runner uses codex skill for install",
    "Codex trigger runner uses codex skill for install",
]

LIB_DIR = TESTS_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def baseline_inventory(path: Path) -> list[str]:
    if not path.is_file():
        return []
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


def merged_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def json_strings(value: object, path: tuple[object, ...] = ()) -> list[tuple[tuple[object, ...], str]]:
    strings: list[tuple[tuple[object, ...], str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            strings.extend(json_strings(child, (*path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            strings.extend(json_strings(child, (*path, index)))
    elif isinstance(value, str):
        strings.append((path, value))
    return strings


def json_path_display(path: tuple[object, ...]) -> str:
    result = ""
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += ("." if result else "") + str(part)
    return result


def is_vendored_speckit_reference(value: str, match: re.Match[str]) -> bool:
    start = value.rfind(".specify/", 0, match.start())
    if start < 0:
        return False
    between = value[start : match.start()]
    return re.search(r"[\s`\"'()<>{}\[\],]", between) is None


def layer3_reference_allowed(relative: str, eval_id: object, field_path: tuple[object, ...], value: str, helper: str) -> bool:
    allowed = LAYER3_NEGATIVE_CONTEXTS.get((relative, eval_id), set())
    if helper not in allowed or not field_path or field_path[0] not in {"expected_output", "expectations"}:
        return False
    lowered = value.casefold()
    return "retired" in lowered and any(marker in lowered for marker in NEGATIVE_MARKERS)


def layer8_contract_files() -> tuple[list[Path], list[Path]]:
    markdown = [LAYER8_ROOT / "README.md"]
    structured: list[Path] = []
    for fixture_dir in sorted(path for path in LAYER8_ROOT.iterdir() if path.is_dir() and path.name[:1].isdigit()):
        markdown.extend(fixture_dir / name for name in ("README.md", "workflow.md"))
        structured.extend(fixture_dir / name for name in ("expected-equivalence.json", "tolerance.json"))
    return [path for path in markdown if path.is_file()], [path for path in structured if path.is_file()]


def markdown_section_map(text: str) -> tuple[list[str], dict[str, str]]:
    current = "<preamble>"
    line_sections: list[str] = []
    section_lines: dict[str, list[str]] = {current: []}
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            section_lines.setdefault(current, [])
        line_sections.append(current)
        section_lines[current].append(line)
    return line_sections, {section: "\n".join(lines).casefold() for section, lines in section_lines.items()}


def layer8_markdown_reference_allowed(relative: str, section: str, line: str, section_text: str, helper: str) -> bool:
    classification = LAYER8_MARKDOWN_CONTEXTS.get((relative, section, helper))
    lowered = line.casefold()
    if classification == "negative":
        return "retired" in lowered and any(marker in lowered for marker in NEGATIVE_MARKERS)
    if classification == "legacy_input":
        return all(marker in section_text for marker in LEGACY_SECTION_MARKERS)
    return False


def retired_contract_violations() -> list[str]:
    violations: list[str] = []

    for root in LAYER3_CONTRACT_ROOTS:
        for path in sorted(root.glob("*.json")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            data = json.loads(path.read_text(encoding="utf-8"))
            for eval_case in data.get("evals", []):
                eval_id = eval_case.get("id")
                for field_path, value in json_strings(eval_case):
                    for match in RETIRED_HELPER_PATTERN.finditer(value):
                        helper = match.group(1)
                        if is_vendored_speckit_reference(value, match):
                            continue
                        if layer3_reference_allowed(relative, eval_id, field_path, value, helper):
                            continue
                        violations.append(f"{relative}:eval[{eval_id}].{json_path_display(field_path)} prescribes {helper}")

    markdown_paths, structured_paths = layer8_contract_files()
    for path in structured_paths:
        relative = path.relative_to(REPO_ROOT).as_posix()
        data = json.loads(path.read_text(encoding="utf-8"))
        for field_path, value in json_strings(data):
            for match in RETIRED_HELPER_PATTERN.finditer(value):
                if is_vendored_speckit_reference(value, match):
                    continue
                violations.append(f"{relative}:{json_path_display(field_path)} prescribes {match.group(1)}")

    for path in markdown_paths:
        relative = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        line_sections, section_texts = markdown_section_map(text)
        for line_number, line in enumerate(text.splitlines(), start=1):
            section = line_sections[line_number - 1]
            for match in RETIRED_HELPER_PATTERN.finditer(line):
                helper = match.group(1)
                if is_vendored_speckit_reference(line, match):
                    continue
                if layer8_markdown_reference_allowed(relative, section, line, section_texts[section], helper):
                    continue
                violations.append(f"{relative}:{line_number} [{section}] prescribes {helper}")

    return violations


def run_script(script: Path, *args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def write_fake_skill_creator(root: Path) -> Path:
    skill_creator = root / "skill-creator"
    scripts = skill_creator / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "__init__.py").write_text("", encoding="utf-8")
    (scripts / "run_eval.py").write_text(
        textwrap.dedent(
            """\
            import sys

            print("fake run_eval invoked")
            print("args:", " ".join(sys.argv[1:]))
            """
        ),
        encoding="utf-8",
    )
    return skill_creator


class EvalRunnerSkillSelectionTests(unittest.TestCase):
    def test_eval_runner_skill_selection_contract(self) -> None:
        self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
        self.assertEqual(retired_contract_violations(), [])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_skill_creator = write_fake_skill_creator(root)
            fake_home = root / "home"
            fake_home.mkdir()

            name = CURRENT_INVENTORY[0]
            result = run_script(FUNCTIONAL_SCRIPT, "speckit-coach")
            with self.subTest(msg=name):
                output = merged_output(result)
                self.assertTrue(
                    result.returncode == 0
                    and f"Skill path: {PLUGIN_ROOT / 'skills' / 'speckit-coach'}" in output,
                    output,
                )

            name = CURRENT_INVENTORY[1]
            result = run_script(
                TRIGGER_SCRIPT,
                "speckit-coach",
                env_overrides={"SKILL_CREATOR_ROOT": str(fake_skill_creator), "HOME": str(fake_home)},
            )
            with self.subTest(msg=name):
                self.assertEqual(result.returncode, 0, merged_output(result))

            name = CURRENT_INVENTORY[2]
            with self.subTest(msg=name):
                self.assertIn(f"Skill path: {PLUGIN_ROOT / 'skills' / 'speckit-coach'}", merged_output(result))

            name = CURRENT_INVENTORY[3]
            result = run_script(CODEX_FUNCTIONAL_SCRIPT, "speckit-coach")
            with self.subTest(msg=name):
                output = merged_output(result)
                self.assertTrue(
                    result.returncode == 0
                    and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / 'speckit-coach'}" in output,
                    output,
                )

            name = CURRENT_INVENTORY[4]
            result = run_script(CODEX_TRIGGER_SCRIPT, "speckit-coach")
            with self.subTest(msg=name):
                output = merged_output(result)
                self.assertTrue(
                    result.returncode == 0
                    and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / 'speckit-coach'}" in output,
                    output,
                )

            inventory_index = 5
            for skill in CODEX_SKILLS:
                name = CURRENT_INVENTORY[inventory_index]
                result = run_script(CODEX_FUNCTIONAL_SCRIPT, skill)
                with self.subTest(msg=name):
                    output = merged_output(result)
                    self.assertTrue(
                        result.returncode == 0
                        and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / skill}" in output,
                        output,
                    )
                inventory_index += 1

                name = CURRENT_INVENTORY[inventory_index]
                result = run_script(CODEX_TRIGGER_SCRIPT, skill)
                with self.subTest(msg=name):
                    output = merged_output(result)
                    self.assertTrue(
                        result.returncode == 0
                        and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / skill}" in output,
                        output,
                    )
                inventory_index += 1


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvalRunnerSkillSelectionTests)
    return run_counted(suite, label="test-eval-runner-skill-selection")


if __name__ == "__main__":
    raise SystemExit(main())

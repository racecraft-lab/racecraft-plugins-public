#!/usr/bin/env python3
"""Project SpecKit skills call only script options their scripts accept."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO_ROOT / "speckit-pro"), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner.helpers.read_only import check_prerequisites, setup_contract_mismatches  # noqa: E402
from test_result import run_counted  # noqa: E402

SCRIPT = """#!/usr/bin/env bash
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks|--include-tasks)
            ;;
{extra}        *)
            echo "ERROR: Unknown option '$1'." >&2
            exit 1
            ;;
    esac
    shift
done
"""
TEMPLATE_CASE = "        --template)\n            shift\n            ;;\n"
CALL = "1. Run `.specify/scripts/bash/check-prerequisites.sh --json --template checklist-template` from repo root.\n"


class SetupContract(unittest.TestCase):
    def repo(self, *, script_extra: str = "", skill: str = CALL, script: bool = True) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        skill_path = root / ".claude/skills/speckit-checklist/SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(skill, encoding="utf-8")
        if script:
            script_path = root / ".specify/scripts/bash/check-prerequisites.sh"
            script_path.parent.mkdir(parents=True)
            script_path.write_text(SCRIPT.format(extra=script_extra), encoding="utf-8")
        return root

    def test_an_option_the_script_rejects_is_a_mismatch(self) -> None:
        self.assertEqual(
            [".claude/skills/speckit-checklist/SKILL.md: check-prerequisites.sh --template"],
            setup_contract_mismatches(self.repo()),
        )

    def test_an_accepted_option_passes_including_alternation_labels(self) -> None:
        skill = CALL + "Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` once.\n"
        self.assertEqual([], setup_contract_mismatches(self.repo(script_extra=TEMPLATE_CASE, skill=skill)))

    def test_a_missing_script_is_a_mismatch(self) -> None:
        self.assertEqual(
            [".claude/skills/speckit-checklist/SKILL.md: check-prerequisites.sh is missing"],
            setup_contract_mismatches(self.repo(script=False)),
        )

    def test_prerequisite_check_fails_closed_on_a_mismatch(self) -> None:
        result = check_prerequisites({"workflow_file": ""}, self.repo())
        report = json.loads(result["stdout"])
        [setup] = [item for item in report["checks"] if item["check"] == "setup_contract"]
        self.assertFalse(setup["pass"])
        self.assertFalse(report["all_pass"])
        self.assertIn("check-prerequisites.sh --template", setup["detail"])

    def test_this_repository_skills_match_their_scripts(self) -> None:
        self.assertEqual([], setup_contract_mismatches(REPO_ROOT))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SetupContract)
    raise SystemExit(run_counted(suite, label="test-speckit-setup-contract"))

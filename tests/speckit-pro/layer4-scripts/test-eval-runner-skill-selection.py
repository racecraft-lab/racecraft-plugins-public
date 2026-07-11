#!/usr/bin/env python3
"""Layer-4 regression tests for Claude/Codex eval runner skill selection.

Port of ``test-eval-runner-skill-selection.sh`` (XPLAT-010 PR9 T084). The
predecessor executes 13 assertions; the count-parity baseline is pinned at
``tests/speckit-pro/parity/xplat-010/test-eval-runner-skill-selection-baseline.txt``
(TOTAL: 13).
"""

from __future__ import annotations

import os
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
BASELINE = TESTS_ROOT / "parity" / "xplat-010" / "test-eval-runner-skill-selection-baseline.txt"
CODEX_SKILLS = ("speckit-scaffold-spec", "speckit-status", "speckit-resolve-pr", "install")

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

#!/usr/bin/env python3
"""Layer-4 contract tests for project Claude hook ports."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GUARD = REPO_ROOT / ".claude" / "hooks" / "guard-version-triplet.py"
STRUCTURAL = REPO_ROOT / ".claude" / "hooks" / "validate-structural.py"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def run_hook(script: Path, payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        shell=False,
        check=False,
    )


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_payload(path: str) -> str:
    return json.dumps({"tool_name": "Edit", "tool_input": {"file_path": path}})


def make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


class ClaudeHookTests(unittest.TestCase):
    def test_hook_ports_contract(self) -> None:
        with self.subTest(msg="guard-version-triplet.py exists"):
            self.assertTrue(GUARD.is_file(), f"file not found: {GUARD}")

        with self.subTest(msg="validate-structural.py exists"):
            self.assertTrue(STRUCTURAL.is_file(), f"file not found: {STRUCTURAL}")

        with self.subTest(msg="guard-version-triplet.py is executable"):
            self.assertTrue(os.access(GUARD, os.X_OK), f"file not executable: {GUARD}")

        with self.subTest(msg="validate-structural.py is executable"):
            self.assertTrue(os.access(STRUCTURAL, os.X_OK), f"file not executable: {STRUCTURAL}")

        target = f"{REPO_ROOT}/.claude-plugin/marketplace.json"
        result = run_hook(GUARD, make_payload(target))
        with self.subTest(msg="guard blocks marketplace edit with exit 2"):
            self.assertEqual(result.returncode, 2, result.stderr)

        with self.subTest(msg="guard warning names version-load-bearing file"):
            self.assertIn("version-load-bearing", result.stderr)

        result = run_hook(GUARD, make_payload(f"{REPO_ROOT}/README.md"))
        with self.subTest(msg="guard allows unrelated file"):
            self.assertEqual(result.returncode, 0, result.stderr)

        with self.subTest(msg="guard unrelated file is quiet"):
            self.assertEqual(result.stderr, "")

        result = run_hook(GUARD, "{not-json")
        with self.subTest(msg="guard malformed JSON fails open"):
            self.assertEqual(result.returncode, 0, result.stderr)

        result = run_hook(STRUCTURAL, "{not-json")
        with self.subTest(msg="structural malformed JSON fails open"):
            self.assertEqual(result.returncode, 0, result.stderr)

        result = run_hook(STRUCTURAL, make_payload(f"{REPO_ROOT}/README.md"))
        with self.subTest(msg="structural ignores unrelated file"):
            self.assertEqual(result.returncode, 0, result.stderr)

        structural = import_module(STRUCTURAL, "validate_structural_hook")
        with tempfile.TemporaryDirectory() as tmp:
            fake_repo = Path(tmp)
            (fake_repo / "speckit-pro").mkdir()
            runner = fake_repo / "tests" / "speckit-pro" / "run-layer-scripts.py"
            runner.parent.mkdir(parents=True)
            make_executable(
                runner,
                "#!/usr/bin/env python3\nimport sys\nprint('fake layer one pass')\nsys.exit(0)\n",
            )
            exit_code, message = structural.handle_payload(
                make_payload(f"{fake_repo}/speckit-pro/skills/example/SKILL.md"),
                repo_root=fake_repo,
            )
            with self.subTest(msg="structural runs Python layer-1 dispatch for matching file"):
                self.assertEqual(exit_code, 0, message)

        with tempfile.TemporaryDirectory() as tmp:
            fake_repo = Path(tmp)
            (fake_repo / "speckit-pro").mkdir()
            runner = fake_repo / "tests" / "speckit-pro" / "run-layer-scripts.py"
            runner.parent.mkdir(parents=True)
            make_executable(
                runner,
                "#!/usr/bin/env python3\nimport sys\nprint('fake layer one fail')\nsys.exit(1)\n",
            )
            exit_code, message = structural.handle_payload(
                make_payload(f"{fake_repo}/speckit-pro/skills/example/SKILL.md"),
                repo_root=fake_repo,
            )
            with self.subTest(msg="structural failure exits 2"):
                self.assertEqual(exit_code, 2, message)

            with self.subTest(msg="structural failure message includes Layer 1"):
                self.assertIn("Layer 1 structural test failed", message)

        with self.subTest(msg="structural validates command markdown trigger"):
            self.assertTrue(structural.should_validate(f"{REPO_ROOT}/speckit-pro/commands/autopilot.md"))

        with self.subTest(msg="structural ignores non-trigger markdown"):
            self.assertFalse(structural.should_validate(f"{REPO_ROOT}/docs/readme.md"))

        for script in (GUARD, STRUCTURAL):
            source = script.read_text(encoding="utf-8")
            tree = ast.parse(source)
            with self.subTest(msg=f"{script.name} does not call os.system"):
                self.assertNotIn("os.system", source)
            with self.subTest(msg=f"{script.name} does not use shell=True"):
                shell_true = any(
                    isinstance(node, ast.keyword)
                    and node.arg == "shell"
                    and isinstance(node.value, ast.Constant)
                    and node.value.value is True
                    for node in ast.walk(tree)
                )
                self.assertFalse(shell_true, f"{script} uses shell=True")
            with self.subTest(msg=f"{script.name} does not invoke jq"):
                self.assertNotIn("jq", source)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ClaudeHookTests)


def main() -> int:
    return run_counted(build_suite(), label="test-claude-hooks")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Claude fixture scaffolds are real lib files that run standalone once staged."""
from __future__ import annotations

import ast
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TEST_ROOT = Path(__file__).resolve().parents[1]
LIB = TEST_ROOT / "lib"
sys.path.insert(0, str(LIB))

import native_eval_adapters as adapters  # noqa: E402
import native_eval_git_scaffold as git_scaffold  # noqa: E402
from test_result import run_counted  # noqa: E402

STAGED_MODULES = (
    "native_eval_fixture_setup.py", "native_eval_strict_json.py", "native_eval_upstream.py",
    "native_eval_toolchain.py", "native_eval_git_scaffold.py", "native_eval_upstream_scaffold.py",
)


class AdapterSourceTests(unittest.TestCase):
    def test_adapters_embed_no_python_program_as_a_string(self) -> None:
        tree = ast.parse(Path(adapters.__file__).read_text(encoding="utf-8"))
        embedded = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and "import native_eval" in node.value:
                embedded.append(node.lineno)
        self.assertEqual(embedded, [])


class StagedScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_staged_modules_import_without_the_rest_of_lib(self) -> None:
        staged = self.temp / "staged"
        staged.mkdir()
        for name in STAGED_MODULES:
            shutil.copyfile(LIB / name, staged / name)
        elsewhere = self.temp / "elsewhere"
        elsewhere.mkdir()
        program = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import native_eval_git_scaffold, native_eval_upstream_scaffold"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", program, str(staged)], cwd=elsewhere,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode(errors="replace"))

    def test_receipt_path_defaults_beside_the_script_and_requires_one_absolute_argument(self) -> None:
        root = self.temp
        self.assertEqual(git_scaffold.receipt_path(root, []), root / "fixture-receipt.json")
        external = root / "controller" / "receipt.json"
        self.assertEqual(git_scaffold.receipt_path(root, [str(external)]), external)
        for arguments in (["relative.json"], [str(external), "extra"]):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                git_scaffold.receipt_path(root, arguments)

    def test_exclude_file_carries_controller_entries_and_worktree_marker(self) -> None:
        for include_worktrees, suffix in ((False, b""), (True, b"/.worktrees/\n")):
            with self.subTest(include_worktrees=include_worktrees):
                workspace = self.temp / f"workspace-{include_worktrees}"
                (workspace / ".git").mkdir(parents=True)
                git_scaffold.write_exclude(workspace, b"/.agents/\n", include_worktrees)
                self.assertEqual(
                    (workspace / ".git" / "info" / "exclude").read_bytes(), b"/.agents/\n" + suffix,
                )

    def test_exclude_file_refuses_a_symlinked_control_directory(self) -> None:
        workspace = self.temp / "workspace-link"
        workspace.mkdir()
        (self.temp / "elsewhere").mkdir()
        (workspace / ".git").symlink_to(self.temp / "elsewhere")
        with self.assertRaisesRegex(ValueError, "control directory is unsafe"):
            git_scaffold.write_exclude(workspace, b"", False)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-native-eval-scaffolds"))

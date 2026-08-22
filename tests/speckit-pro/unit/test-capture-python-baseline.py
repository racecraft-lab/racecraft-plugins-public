#!/usr/bin/env python3
"""Focused contracts for Python-port count-parity baseline capture."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "tests" / "speckit-pro" / "lib" / "capture_python_baseline.py"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def write_script(root: Path, name: str, source: str) -> Path:
    path = root / name
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


def run_tool(
    target: Path,
    *,
    out: Path | None = None,
    script_args: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(TOOL), str(target)]
    if out is not None:
        command.extend(("--out", str(out)))
    command.extend(script_args)
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class CapturePythonBaselineTests(unittest.TestCase):
    def _assert_capture(
        self,
        script_name: str,
        source: str,
        expected_inventory: str,
        *,
        expected_returncode: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = write_script(root, script_name, source)
            output = root / "baseline.txt"
            completed = run_tool(target, out=output)

            self.assertEqual(completed.returncode, expected_returncode, completed.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), expected_inventory)
            return completed

    def test_build_suite_captures_subtest_names_in_runtime_order(self) -> None:
        self._assert_capture(
            "counted_port.py",
            """
            import unittest

            class CountedPortTests(unittest.TestCase):
                def test_inventory(self):
                    for name in ("first check", "second check", "first check"):
                        with self.subTest(msg=name):
                            self.assertTrue(True)

            def build_suite():
                return unittest.defaultTestLoader.loadTestsFromTestCase(CountedPortTests)
            """,
            "001 first check\n002 second check\n003 first check\nTOTAL: 3\n",
        )

    def test_default_loader_captures_module_without_build_suite(self) -> None:
        self._assert_capture(
            "default_loader_port.py",
            """
            import unittest

            class DefaultLoaderPortTests(unittest.TestCase):
                def test_inventory(self):
                    with self.subTest(msg="discovered check"):
                        self.assertEqual(2 + 2, 4)
            """,
            "001 discovered check\nTOTAL: 1\n",
        )

    def test_reporter_capture_writes_inventory_and_propagates_target_exit(self) -> None:
        completed = self._assert_capture(
            "reporter_port.py",
            """
            import os
            import sys

            def main():
                if os.environ.get("VERBOSE") == "true":
                    print("  reporter first ... PASS")
                    print("  reporter second ... FAIL")
                return 7

            if __name__ == "__main__":
                raise SystemExit(main())
            """,
            "001 reporter first\n002 reporter second\nTOTAL: 2\n",
            expected_returncode=7,
        )
        self.assertIn("target_exit_code=7", completed.stdout)

    def test_zero_count_cli_capture_is_valid(self) -> None:
        self._assert_capture(
            "zero_count_port.py",
            """
            def main():
                print("No counted checks for this invocation mode")
                return 0

            if __name__ == "__main__":
                raise SystemExit(main())
            """,
            "TOTAL: 0\n",
        )

    def test_missing_and_non_python_targets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            missing_output = root / "missing-baseline.txt"
            missing = run_tool(root / "missing.py", out=missing_output)
            non_python_target = write_script(root, "not-python.txt", "not python\n")
            non_python_output = root / "non-python-baseline.txt"
            non_python = run_tool(non_python_target, out=non_python_output)

            self.assertEqual(missing.returncode, 1)
            self.assertIn("target not found:", missing.stderr)
            self.assertFalse(missing_output.exists())
            self.assertEqual(non_python.returncode, 1)
            self.assertIn("target must be a .py file:", non_python.stderr)
            self.assertFalse(non_python_output.exists())

    def test_unnamed_subtests_and_plain_counted_methods_fail_loud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            unnamed = write_script(
                root,
                "unnamed_port.py",
                """
                import unittest

                class UnnamedPortTests(unittest.TestCase):
                    def test_inventory(self):
                        with self.subTest(msg="   "):
                            self.assertTrue(True)
                """,
            )
            plain = write_script(
                root,
                "plain_port.py",
                """
                import unittest

                class PlainPortTests(unittest.TestCase):
                    def test_plain_method(self):
                        self.assertTrue(True)
                """,
            )

            unnamed_result = run_tool(unnamed, out=root / "unnamed-baseline.txt")
            plain_result = run_tool(plain, out=root / "plain-baseline.txt")

            self.assertEqual(unnamed_result.returncode, 1)
            self.assertIn("empty subtest name", unnamed_result.stderr)
            self.assertEqual(plain_result.returncode, 1)
            self.assertIn("counted non-subtest method", plain_result.stderr)

    def test_reporter_subprocess_preserves_argv_without_shell_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            argv_log = root / "argv.json"
            injected = root / "shell-expanded"
            dangerous_arg = f"$(touch {injected})"
            target = write_script(
                root,
                "argv_port.py",
                """
                import json
                import os
                import sys
                from pathlib import Path

                def main():
                    Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]), encoding="utf-8")
                    if os.environ.get("VERBOSE") == "true":
                        print("argv preserved ... PASS")
                    return 0

                if __name__ == "__main__":
                    raise SystemExit(main())
                """,
            )
            output = root / "baseline.txt"

            completed = run_tool(
                target,
                out=output,
                script_args=(str(argv_log), "value with spaces", dangerous_arg, "--literal-flag"),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                json.loads(argv_log.read_text(encoding="utf-8")),
                ["value with spaces", dangerous_arg, "--literal-flag"],
            )
            self.assertFalse(injected.exists())
            self.assertEqual(output.read_text(encoding="utf-8"), "001 argv preserved\nTOTAL: 1\n")

    def test_cli_creates_the_explicit_output_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = write_script(
                root,
                "output_port.py",
                """
                import unittest

                class OutputPortTests(unittest.TestCase):
                    def test_output(self):
                        with self.subTest(msg="output check"):
                            self.assertTrue(True)
                """,
            )
            output = root / "nested" / "evidence" / "custom-baseline.txt"

            completed = run_tool(target, out=output)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "001 output check\nTOTAL: 1\n")
            self.assertIn(str(output), completed.stdout)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(CapturePythonBaselineTests)


def main() -> int:
    return run_counted(build_suite(), label="test-capture-python-baseline")


if __name__ == "__main__":
    raise SystemExit(main())

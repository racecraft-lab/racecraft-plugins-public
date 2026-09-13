#!/usr/bin/env python3
"""Layer-4 contract tests for refresh-local-plugin.py."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "refresh-local-plugin.py"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
STUB_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "refresh-local-plugin"
STUB_NAMES = ("success-claude", "success-codex", "failure-claude", "failure-codex", "reject-execution")
for path in (PLUGIN_ROOT, LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from test_result import run_counted  # noqa: E402


def run_helper(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    child_env = os.environ.copy()
    child_env["PATH"] = ""
    for name in ("CALL_LOG", "STUB_REPO_ROOT", "MKT_NAME", "MKT_MODE", "UNINSTALL_MSG", "UNINSTALL_RC", "REMOVE_MSG", "REMOVE_RC"):
        child_env.pop(name, None)
    child_env["STUB_REPO_ROOT"] = str(REPO_ROOT)
    if env:
        child_env.update(env)
    allowed = {STUB_FIXTURE_DIR / name for name in STUB_NAMES}
    for tool in ("claude", "codex"):
        selected = shutil.which(tool, path=child_env["PATH"])
        if selected is not None:
            executable = Path(selected).resolve()
            owned = executable in allowed
            if os.name == "nt" and executable.is_file():
                owned = executable.read_bytes() in {fixture.read_bytes() for fixture in allowed}
            if not owned:
                raise AssertionError(f"unowned provider selected for {tool}")
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=child_env,
        shell=False,
        check=False,
    )


def merged(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def make_executable(path: Path, fixture_name: str) -> None:
    if fixture_name not in STUB_NAMES:
        raise ValueError("unknown provider fixture")
    source = STUB_FIXTURE_DIR / fixture_name
    if os.name == "nt":
        shutil.copyfile(source, path)
        path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    else:
        path.symlink_to(source)


class RefreshLocalPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.work = Path(self._tmp.name)
        self.call_log = self.work / "calls.log"
        self.call_log.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @unittest.skipIf(os.name == "nt", "POSIX noexec fixture contract")
    def test_provider_stubs_execute_from_tracked_inputs(self) -> None:
        for mode in ("success", "failure"):
            stub_bin = self.make_stubs(mode)
            for tool in ("claude", "codex"):
                stub = stub_bin / tool
                self.assertTrue(stub.is_symlink())
                self.assertEqual(stub.resolve(), STUB_FIXTURE_DIR / f"{mode}-{tool}")
                self.assertFalse(stub.resolve().is_relative_to(self.work.resolve()))
                self.assertTrue(os.access(stub, os.X_OK))

    def test_provider_lookup_cannot_fall_back_to_real_tools(self) -> None:
        with patch.object(shutil, "which", return_value="/unowned/provider"), patch.object(subprocess, "run") as launch:
            with self.assertRaisesRegex(AssertionError, "unowned provider"):
                run_helper("--no-build", "--no-validate", "--codex", env={"PATH": "/owned-test-bin"})
            launch.assert_not_called()
        with patch.dict(os.environ, {"PATH": "/unowned-bin"}), patch.object(shutil, "which", return_value=None), patch.object(subprocess, "run") as launch:
            run_helper("--help")
            self.assertEqual(launch.call_args.kwargs["env"]["PATH"], "")

    def test_refresh_local_plugin_contract(self) -> None:
        with self.subTest(msg="refresh helper exists"):
            self.assertTrue(SCRIPT.is_file(), f"file not found: {SCRIPT}")

        with self.subTest(msg="refresh helper is executable"):
            self.assertTrue(os.access(SCRIPT, os.X_OK), f"file not executable: {SCRIPT}")

        with self.subTest(msg="help mentions Codex refresh"):
            result = run_helper("--help")
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertIn("--codex", merged(result))

        with self.subTest(msg="dry-run default rebuilds, validates, and prints Claude dev command"):
            result = run_helper("--dry-run")
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertIn("build-plugin-payloads.py", merged(result))
            self.assertIn("claude plugin validate", merged(result))
            self.assertIn("claude --plugin-dir", merged(result))

        with self.subTest(msg="dry-run default refreshes both installed plugin caches"):
            self.assertIn("plugin uninstall", merged(result))
            self.assertIn("codex plugin remove", merged(result))

        with self.subTest(msg="dry-run opt-outs skip installed plugin cache refresh"):
            result = run_helper("--dry-run", "--no-codex", "--no-claude-install")
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertNotIn("plugin uninstall", merged(result))
            self.assertNotIn("codex plugin remove", merged(result))

        with self.subTest(msg="dry-run does not require generated payloads to exist"):
            result = run_helper("--dry-run", env={"SPECKIT_PLUGIN_NAME": "plugin-without-payloads"})
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertNotIn("payload not found", merged(result))

        fail_bin = self.work / "fail-bin"
        fail_bin.mkdir()
        make_executable(fail_bin / "claude", "reject-execution")
        make_executable(fail_bin / "codex", "reject-execution")
        with self.subTest(msg="dry-run all prints refresh commands without requiring real CLI state"):
            result = run_helper("--dry-run", "--all", env={"PATH": f"{fail_bin}{os.pathsep}{os.environ['PATH']}"})
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertIn("claude plugin marketplace list # verify", merged(result))
            self.assertIn("codex plugin marketplace list # verify", merged(result))
            self.assertIn("claude plugin install", merged(result))
            self.assertIn("codex plugin add", merged(result))

        stub_bin = self.make_stubs("success")
        env = {"PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}", "CALL_LOG": str(self.call_log)}

        with self.subTest(msg="Codex refresh removes and adds installed plugin"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--codex", env=env)
            self.assertEqual(result.returncode, 0, merged(result))
            calls = self.call_log.read_text(encoding="utf-8")
            self.assertIn("codex plugin marketplace list", calls)
            self.assertIn("codex plugin remove speckit-pro@racecraft-plugins-public", calls)
            self.assertIn("codex plugin add speckit-pro@racecraft-plugins-public", calls)
            self.assertIn("Start a new Codex thread", merged(result))

        with self.subTest(msg="Claude install refresh honors requested scope"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--claude-install", "--scope", "local", env=env)
            self.assertEqual(result.returncode, 0, merged(result))
            calls = self.call_log.read_text(encoding="utf-8")
            self.assertIn("claude plugin marketplace list", calls)
            self.assertIn("claude plugin uninstall speckit-pro@racecraft-plugins-public --scope local -y", calls)
            self.assertIn("claude plugin install speckit-pro@racecraft-plugins-public --scope local", calls)
            self.assertIn("/reload-plugins", merged(result))

        with self.subTest(msg="Claude launch uses generated Claude payload"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--launch-claude", env=env)
            self.assertEqual(result.returncode, 0, merged(result))
            calls = self.call_log.read_text(encoding="utf-8")
            self.assertIn(f"claude --plugin-dir {REPO_ROOT}/dist/claude/speckit-pro", calls)

        failure_bin = self.make_stubs("failure")
        failure_env = {
            "PATH": f"{failure_bin}{os.pathsep}{os.environ['PATH']}",
            "CALL_LOG": str(self.call_log),
            "STUB_REPO_ROOT": str(REPO_ROOT),
        }

        with self.subTest(msg="benign 'not found' uninstall still proceeds to install"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper(
                "--no-build",
                "--no-validate",
                "--no-codex",
                "--claude-install",
                env=failure_env
                | {"UNINSTALL_RC": "1", "UNINSTALL_MSG": 'Plugin "speckit-pro@racecraft-plugins-public" not found in installed plugins'},
            )
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertIn("/reload-plugins", merged(result))
            self.assertIn("claude plugin install speckit-pro@racecraft-plugins-public", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="non-benign uninstall failure aborts with its output"):
            result = run_helper(
                "--no-build",
                "--no-validate",
                "--no-codex",
                "--claude-install",
                env=failure_env | {"UNINSTALL_RC": "1", "UNINSTALL_MSG": "Error: permission denied writing plugin cache"},
            )
            self.assertEqual(result.returncode, 1, merged(result))
            self.assertIn("permission denied writing plugin cache", merged(result))
            self.assertIn("failed to uninstall", merged(result))

        with self.subTest(msg="marketplace present as a non-local source aborts clearly"):
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "github"})
            self.assertEqual(result.returncode, 1, merged(result))
            self.assertIn("not a local Directory source", merged(result))

        with self.subTest(msg="marketplace pointing at another checkout aborts"):
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "elsewhere"})
            self.assertEqual(result.returncode, 1, merged(result))
            self.assertIn("points at '/some/other/checkout'", merged(result))

        with self.subTest(msg="absent marketplace is added"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "absent"})
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertIn("claude plugin marketplace add", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="marketplace inspection failure aborts"):
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "listfail"})
            self.assertEqual(result.returncode, 1, merged(result))
            self.assertIn("failed to inspect", merged(result))

        with self.subTest(msg="non-benign Codex remove failure aborts"):
            result = run_helper(
                "--no-build",
                "--no-validate",
                "--codex",
                "--no-claude-install",
                env=failure_env | {"REMOVE_RC": "1", "REMOVE_MSG": "Error: disk failure"},
            )
            self.assertEqual(result.returncode, 1, merged(result))
            self.assertIn("failed to remove", merged(result))

        with self.subTest(msg="marketplace name with regex metacharacters matches its row literally"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper(
                "--no-build",
                "--no-validate",
                "--no-codex",
                "--claude-install",
                env=failure_env | {"SPECKIT_MARKETPLACE": "my+plug-mkt", "MKT_NAME": "my+plug-mkt"},
            )
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertNotIn("Adding Claude marketplace", merged(result))
            self.assertIn("speckit-pro@my+plug-mkt", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="missing claude skips validation instead of aborting a Codex-only run"):
            codex_only = self.work / "codex-only"
            codex_only.mkdir()
            make_executable(codex_only / "codex", "failure-codex")
            result = run_helper(
                "--no-build",
                "--codex",
                "--no-claude-install",
                env={"PATH": f"{codex_only}{os.pathsep}/usr/bin:/bin", "CALL_LOG": str(self.call_log), "STUB_REPO_ROOT": str(REPO_ROOT)},
            )
            self.assertEqual(result.returncode, 0, merged(result))
            self.assertIn("skipping Claude payload validation", merged(result))
            self.assertIn("codex plugin add speckit-pro@racecraft-plugins-public", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="invalid scope exits with usage error"):
            result = run_helper("--scope", "managed")
            self.assertEqual(result.returncode, 2, merged(result))
            self.assertIn("--scope must be one of", merged(result))

        with self.subTest(msg="unknown option exits with usage error"):
            result = run_helper("--wat")
            self.assertEqual(result.returncode, 2, merged(result))
            self.assertIn("unknown option", merged(result))

    def make_stubs(self, mode: str) -> Path:
        stub_bin = self.work / f"{mode}-bin"
        stub_bin.mkdir()
        for tool in ("claude", "codex"):
            make_executable(stub_bin / tool, f"{mode}-{tool}")
        return stub_bin


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(RefreshLocalPluginTests)


def main() -> int:
    return run_counted(build_suite(), label="test-refresh-local-plugin")


if __name__ == "__main__":
    raise SystemExit(main())

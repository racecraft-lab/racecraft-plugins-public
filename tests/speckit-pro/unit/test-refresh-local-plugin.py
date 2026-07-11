#!/usr/bin/env python3
"""Layer-4 contract tests for refresh-local-plugin.py."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "refresh-local-plugin.py"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for path in (PLUGIN_ROOT, LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from test_result import run_counted  # noqa: E402


def run_helper(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
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


def make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


class RefreshLocalPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.work = Path(self._tmp.name)
        self.call_log = self.work / "calls.log"
        self.call_log.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_refresh_local_plugin_contract(self) -> None:
        with self.subTest(msg="refresh helper exists"):
            self.assertTrue(SCRIPT.is_file(), f"file not found: {SCRIPT}")

        with self.subTest(msg="refresh helper is executable"):
            self.assertTrue(os.access(SCRIPT, os.X_OK), f"file not executable: {SCRIPT}")

        with self.subTest(msg="help mentions Codex refresh"):
            result = run_helper("--help")
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="help mentions Codex refresh"):
            self.assertIn("--codex", merged(result))

        with self.subTest(msg="dry-run default rebuilds, validates, and prints Claude dev command"):
            result = run_helper("--dry-run")
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="dry-run default rebuilds, validates, and prints Claude dev command"):
            self.assertIn("build-plugin-payloads.py", merged(result))

        with self.subTest(msg="dry-run default rebuilds, validates, and prints Claude dev command"):
            self.assertIn("claude plugin validate", merged(result))

        with self.subTest(msg="dry-run default rebuilds, validates, and prints Claude dev command"):
            self.assertIn("claude --plugin-dir", merged(result))

        with self.subTest(msg="dry-run default refreshes both installed plugin caches"):
            self.assertIn("plugin uninstall", merged(result))

        with self.subTest(msg="dry-run default refreshes both installed plugin caches"):
            self.assertIn("codex plugin remove", merged(result))

        with self.subTest(msg="dry-run opt-outs skip installed plugin cache refresh"):
            result = run_helper("--dry-run", "--no-codex", "--no-claude-install")
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="dry-run opt-outs skip installed plugin cache refresh"):
            self.assertNotIn("plugin uninstall", merged(result))

        with self.subTest(msg="dry-run opt-outs skip installed plugin cache refresh"):
            self.assertNotIn("codex plugin remove", merged(result))

        with self.subTest(msg="dry-run does not require generated payloads to exist"):
            result = run_helper("--dry-run", env={"SPECKIT_PLUGIN_NAME": "plugin-without-payloads"})
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="dry-run does not require generated payloads to exist"):
            self.assertNotIn("payload not found", merged(result))

        fail_bin = self.work / "fail-bin"
        fail_bin.mkdir()
        make_executable(fail_bin / "claude", "#!/usr/bin/env python3\nraise SystemExit(99)\n")
        make_executable(fail_bin / "codex", "#!/usr/bin/env python3\nraise SystemExit(99)\n")
        with self.subTest(msg="dry-run all prints refresh commands without requiring real CLI state"):
            result = run_helper("--dry-run", "--all", env={"PATH": f"{fail_bin}{os.pathsep}{os.environ['PATH']}"})
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="dry-run all prints refresh commands without requiring real CLI state"):
            self.assertIn("claude plugin marketplace list # verify", merged(result))

        with self.subTest(msg="dry-run all prints refresh commands without requiring real CLI state"):
            self.assertIn("codex plugin marketplace list # verify", merged(result))

        with self.subTest(msg="dry-run all prints refresh commands without requiring real CLI state"):
            self.assertIn("claude plugin install", merged(result))

        with self.subTest(msg="dry-run all prints refresh commands without requiring real CLI state"):
            self.assertIn("codex plugin add", merged(result))

        stub_bin = self.make_success_stubs()
        env = {"PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}", "CALL_LOG": str(self.call_log)}

        with self.subTest(msg="Codex refresh removes and adds installed plugin"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--codex", env=env)
            self.assertEqual(result.returncode, 0, merged(result))

        calls = self.call_log.read_text(encoding="utf-8")
        with self.subTest(msg="Codex refresh removes and adds installed plugin"):
            self.assertIn("codex plugin marketplace list", calls)

        with self.subTest(msg="Codex refresh removes and adds installed plugin"):
            self.assertIn("codex plugin remove speckit-pro@racecraft-plugins-public", calls)

        with self.subTest(msg="Codex refresh removes and adds installed plugin"):
            self.assertIn("codex plugin add speckit-pro@racecraft-plugins-public", calls)

        with self.subTest(msg="Codex refresh removes and adds installed plugin"):
            self.assertIn("Start a new Codex thread", merged(result))

        with self.subTest(msg="Claude install refresh honors requested scope"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--claude-install", "--scope", "local", env=env)
            self.assertEqual(result.returncode, 0, merged(result))

        calls = self.call_log.read_text(encoding="utf-8")
        with self.subTest(msg="Claude install refresh honors requested scope"):
            self.assertIn("claude plugin marketplace list", calls)

        with self.subTest(msg="Claude install refresh honors requested scope"):
            self.assertIn("claude plugin uninstall speckit-pro@racecraft-plugins-public --scope local -y", calls)

        with self.subTest(msg="Claude install refresh honors requested scope"):
            self.assertIn("claude plugin install speckit-pro@racecraft-plugins-public --scope local", calls)

        with self.subTest(msg="Claude install refresh honors requested scope"):
            self.assertIn("/reload-plugins", merged(result))

        with self.subTest(msg="Claude launch uses generated Claude payload"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--launch-claude", env=env)
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="Claude launch uses generated Claude payload"):
            calls = self.call_log.read_text(encoding="utf-8")
            self.assertIn(f"claude --plugin-dir {REPO_ROOT}/dist/claude/speckit-pro", calls)

        failure_bin = self.make_failure_stubs()
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

        with self.subTest(msg="benign 'not found' uninstall still proceeds to install"):
            self.assertIn("/reload-plugins", merged(result))

        with self.subTest(msg="benign 'not found' uninstall still proceeds to install"):
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

        with self.subTest(msg="non-benign uninstall failure aborts with its output"):
            self.assertIn("permission denied writing plugin cache", merged(result))

        with self.subTest(msg="non-benign uninstall failure aborts with its output"):
            self.assertIn("failed to uninstall", merged(result))

        with self.subTest(msg="marketplace present as a non-local source aborts clearly"):
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "github"})
            self.assertEqual(result.returncode, 1, merged(result))

        with self.subTest(msg="marketplace present as a non-local source aborts clearly"):
            self.assertIn("not a local Directory source", merged(result))

        with self.subTest(msg="marketplace pointing at another checkout aborts"):
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "elsewhere"})
            self.assertEqual(result.returncode, 1, merged(result))

        with self.subTest(msg="marketplace pointing at another checkout aborts"):
            self.assertIn("points at '/some/other/checkout'", merged(result))

        with self.subTest(msg="absent marketplace is added"):
            self.call_log.write_text("", encoding="utf-8")
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "absent"})
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="absent marketplace is added"):
            self.assertIn("claude plugin marketplace add", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="marketplace inspection failure aborts"):
            result = run_helper("--no-build", "--no-validate", "--no-codex", "--claude-install", env=failure_env | {"MKT_MODE": "listfail"})
            self.assertEqual(result.returncode, 1, merged(result))

        with self.subTest(msg="marketplace inspection failure aborts"):
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

        with self.subTest(msg="non-benign Codex remove failure aborts"):
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

        with self.subTest(msg="marketplace name with regex metacharacters matches its row literally"):
            self.assertNotIn("Adding Claude marketplace", merged(result))

        with self.subTest(msg="marketplace name with regex metacharacters matches its row literally"):
            self.assertIn("speckit-pro@my+plug-mkt", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="missing claude skips validation instead of aborting a Codex-only run"):
            codex_only = self.work / "codex-only"
            codex_only.mkdir()
            shutil.copy(failure_bin / "codex", codex_only / "codex")
            result = run_helper(
                "--no-build",
                "--codex",
                "--no-claude-install",
                env={"PATH": f"{codex_only}{os.pathsep}/usr/bin:/bin", "CALL_LOG": str(self.call_log), "STUB_REPO_ROOT": str(REPO_ROOT)},
            )
            self.assertEqual(result.returncode, 0, merged(result))

        with self.subTest(msg="missing claude skips validation instead of aborting a Codex-only run"):
            self.assertIn("skipping Claude payload validation", merged(result))

        with self.subTest(msg="missing claude skips validation instead of aborting a Codex-only run"):
            self.assertIn("codex plugin add speckit-pro@racecraft-plugins-public", self.call_log.read_text(encoding="utf-8"))

        with self.subTest(msg="invalid scope exits with usage error"):
            result = run_helper("--scope", "managed")
            self.assertEqual(result.returncode, 2, merged(result))

        with self.subTest(msg="invalid scope exits with usage error"):
            self.assertIn("--scope must be one of", merged(result))

        with self.subTest(msg="unknown option exits with usage error"):
            result = run_helper("--wat")
            self.assertEqual(result.returncode, 2, merged(result))

        with self.subTest(msg="unknown option exits with usage error"):
            self.assertIn("unknown option", merged(result))

    def make_success_stubs(self) -> Path:
        stub_bin = self.work / "bin"
        stub_bin.mkdir()
        make_executable(
            stub_bin / "claude",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import os
                import sys

                with open(os.environ["CALL_LOG"], "a", encoding="utf-8") as call_log:
                    call_log.write("claude " + " ".join(sys.argv[1:]) + "\\n")
                if sys.argv[1:4] == ["plugin", "marketplace", "list"]:
                    sys.stdout.write(
                        "Configured marketplaces:\\n\\n"
                        "  > racecraft-plugins-public\\n"
                        "    Source: Directory ({REPO_ROOT})\\n"
                    )
                raise SystemExit(0)
                """
            ),
        )
        make_executable(
            stub_bin / "codex",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import os
                import sys

                with open(os.environ["CALL_LOG"], "a", encoding="utf-8") as call_log:
                    call_log.write("codex " + " ".join(sys.argv[1:]) + "\\n")
                if sys.argv[1:4] == ["plugin", "marketplace", "list"]:
                    sys.stdout.write(
                        "MARKETPLACE               ROOT\\n"
                        "racecraft-plugins-public  {REPO_ROOT}\\n"
                    )
                raise SystemExit(0)
                """
            ),
        )
        return stub_bin

    def make_failure_stubs(self) -> Path:
        stub_bin = self.work / "fail-stub"
        stub_bin.mkdir()
        make_executable(
            stub_bin / "claude",
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import os
                import sys

                with open(os.environ["CALL_LOG"], "a", encoding="utf-8") as call_log:
                    call_log.write("claude " + " ".join(sys.argv[1:]) + "\\n")

                if sys.argv[1:4] == ["plugin", "marketplace", "list"]:
                    name = os.environ.get("MKT_NAME") or "racecraft-plugins-public"
                    mode = os.environ.get("MKT_MODE") or "local"
                    if mode == "local":
                        sys.stdout.write(
                            f"Configured marketplaces:\\n\\n  > {name}\\n"
                            f"    Source: Directory ({os.environ['STUB_REPO_ROOT']})\\n"
                        )
                    elif mode == "github":
                        sys.stdout.write(
                            f"Configured marketplaces:\\n\\n  > {name}\\n"
                            f"    Source: GitHub (racecraft-lab/{name})\\n"
                        )
                    elif mode == "elsewhere":
                        sys.stdout.write(
                            f"Configured marketplaces:\\n\\n  > {name}\\n"
                            "    Source: Directory (/some/other/checkout)\\n"
                        )
                    elif mode == "absent":
                        sys.stdout.write(
                            "Configured marketplaces:\\n\\n  > other-marketplace\\n"
                            "    Source: GitHub (a/b)\\n"
                        )
                    elif mode == "listfail":
                        sys.stderr.write("boom\\n")
                        raise SystemExit(7)
                    raise SystemExit(0)

                if sys.argv[1:3] == ["plugin", "uninstall"]:
                    message = os.environ.get("UNINSTALL_MSG") or ""
                    if message:
                        sys.stderr.write(message + "\\n")
                    raise SystemExit(int(os.environ.get("UNINSTALL_RC") or "0"))
                raise SystemExit(0)
                """
            ),
        )
        make_executable(
            stub_bin / "codex",
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import os
                import sys

                with open(os.environ["CALL_LOG"], "a", encoding="utf-8") as call_log:
                    call_log.write("codex " + " ".join(sys.argv[1:]) + "\\n")

                if sys.argv[1:4] == ["plugin", "marketplace", "list"]:
                    sys.stdout.write(
                        "MARKETPLACE               ROOT\\n"
                        f"racecraft-plugins-public  {os.environ['STUB_REPO_ROOT']}\\n"
                    )
                    raise SystemExit(0)

                if sys.argv[1:3] == ["plugin", "remove"]:
                    message = os.environ.get("REMOVE_MSG") or ""
                    if message:
                        sys.stderr.write(message + "\\n")
                    raise SystemExit(int(os.environ.get("REMOVE_RC") or "0"))
                raise SystemExit(0)
                """
            ),
        )
        return stub_bin


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(RefreshLocalPluginTests)


def main() -> int:
    return run_counted(build_suite(), label="test-refresh-local-plugin")


if __name__ == "__main__":
    raise SystemExit(main())

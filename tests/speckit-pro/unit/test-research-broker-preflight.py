#!/usr/bin/env python3
"""Every state of the value-free research-broker preflight.

The preflight decides how the research broker screens fetched content. These
tests pin one case per preflight state (plan A.3), plus the rules that keep the
check value-free: it never opens a Jev key file and never prints a variable's
value. Every case runs against a temporary HOME and a fake `evaluate` binary, so
no test touches the real machine's key files or calls a provider.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for entry in (PLUGIN_ROOT, REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from speckit_pro_runner import research_preflight as preflight  # noqa: E402
from test_result import run_counted  # noqa: E402

# A value that must never be echoed. Built at run time so no key-shaped literal
# sits in the tree.
SECRET_VALUE = "fixture" + "-secret-" + "value-0000"


class FakeRunner:
    """Records argv and returns canned results for `version` and `call --check`."""

    def __init__(self, *, version: str | None = "0.9.0", check_exit: int | None = 0, version_exit: int = 0) -> None:
        self.version = version
        self.check_exit = check_exit
        self.version_exit = version_exit
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(self, argv: list[str], env: dict[str, str], stdin: bytes | None, timeout: float) -> preflight.ProcessResult:
        self.calls.append((list(argv), dict(env)))
        if argv[1:] == ["version"]:
            out = (self.version or "").encode("utf-8") + b"\n"
            return preflight.ProcessResult(self.version_exit, out)
        if argv[1:] == ["call", "--check", "--plugin-defaults"]:
            return preflight.ProcessResult(self.check_exit, b"")
        raise AssertionError(f"unexpected argv {argv!r}")


class PreflightStateTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="research-preflight-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.binary = self.home / ".local" / "libexec" / "racecraft-jev" / "evaluate"

    def env(self, **extra: str) -> dict[str, str]:
        return {"HOME": str(self.home), "PATH": os.defpath, **extra}

    def install_binary(self) -> None:
        self.binary.parent.mkdir(parents=True, exist_ok=True)
        self.binary.write_text("placeholder\n", encoding="utf-8")
        self.binary.chmod(0o755)

    def write_key(self, directory: str, name: str, mode: int = 0o600, content: str = SECRET_VALUE) -> Path:
        path = self.home / ".config" / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        path.chmod(mode)
        return path

    def run_preflight(self, env: dict[str, str], runner: FakeRunner | None = None) -> dict:
        return preflight.research_broker_preflight(env=env, runner=runner or FakeRunner())

    # --- Jev screening states -------------------------------------------------

    def test_ready_with_key_file_is_ok_and_jev_mode(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        self.write_key("speckit-pro", "tavily.key")
        record = self.run_preflight(self.env())
        self.assertEqual(record["jev"]["state"], "ready")
        self.assertEqual(record["jev"]["credential_source"], "key_file")
        self.assertEqual(record["screening_mode"], "jev")
        self.assertTrue(record["jev"]["usable"])
        self.assertEqual(record["severity"], "ok")
        self.assertEqual(record["warnings"], [])
        self.assertEqual(record["errors"], [])

    def test_no_credential_source_is_warning_and_sanitizer_only(self) -> None:
        self.install_binary()
        self.write_key("speckit-pro", "tavily.key")
        record = self.run_preflight(self.env(), FakeRunner(check_exit=3))
        self.assertEqual(record["jev"]["state"], "no_credential")
        self.assertEqual(record["screening_mode"], "sanitizer-only")
        self.assertEqual(record["severity"], "warning")
        self.assertIn("jev_no_credential", [item["code"] for item in record["warnings"]])

    def test_binary_missing_without_credential_is_warning_naming_install(self) -> None:
        self.write_key("speckit-pro", "tavily.key")
        runner = FakeRunner()
        record = self.run_preflight(self.env(), runner)
        self.assertEqual(record["jev"]["state"], "binary_missing")
        self.assertEqual(record["jev"]["binary"], "missing")
        self.assertEqual(record["screening_mode"], "sanitizer-only")
        self.assertEqual(record["severity"], "warning")
        warning = next(item for item in record["warnings"] if item["code"] == "jev_binary_missing")
        self.assertIn("install", warning["message"].lower())
        self.assertEqual(runner.calls, [])

    def test_unusable_key_file_is_error_and_every_chunk_drops(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key", mode=0o644)
        self.write_key("speckit-pro", "tavily.key")
        record = self.run_preflight(self.env(), FakeRunner(check_exit=4))
        self.assertEqual(record["jev"]["state"], "credential_unusable")
        self.assertEqual(record["screening_mode"], "jev")
        self.assertFalse(record["jev"]["usable"])
        self.assertEqual(record["severity"], "error")
        self.assertIn("jev_credential_unusable", [item["code"] for item in record["errors"]])

    def test_explicit_key_file_path_that_is_absent_is_configured(self) -> None:
        missing = self.home / "elsewhere" / "typesafe.key"
        record = self.run_preflight(self.env(JEV_API_KEY_FILE=str(missing)))
        self.assertEqual(record["jev"]["state"], "binary_missing_with_credential")
        self.assertEqual(record["severity"], "error")

    def test_binary_missing_with_credential_is_error(self) -> None:
        self.write_key("racecraft-jev", "openrouter.key")
        record = self.run_preflight(self.env())
        self.assertEqual(record["jev"]["state"], "binary_missing_with_credential")
        self.assertEqual(record["screening_mode"], "jev")
        self.assertFalse(record["jev"]["usable"])
        self.assertEqual(record["severity"], "error")

    def test_binary_older_than_minimum_with_credential_is_error(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        runner = FakeRunner(version="0.8.0")
        record = self.run_preflight(self.env(), runner)
        self.assertEqual(record["jev"]["state"], "binary_outdated")
        self.assertEqual(record["jev"]["binary_version"], "0.8.0")
        self.assertEqual(record["severity"], "error")
        # 0.8.0 has no `call` subcommand, so the check must not run.
        self.assertEqual([argv[1:] for argv, _ in runner.calls], [["version"]])

    def test_binary_older_than_minimum_without_credential_is_warning(self) -> None:
        self.install_binary()
        record = self.run_preflight(self.env(), FakeRunner(version="v0.8.0"))
        self.assertEqual(record["jev"]["state"], "binary_outdated")
        self.assertEqual(record["screening_mode"], "sanitizer-only")
        self.assertIn("jev_binary_outdated", [item["code"] for item in record["warnings"]])

    def test_unparseable_version_fails_closed(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        record = self.run_preflight(self.env(), FakeRunner(version="garbage", version_exit=0))
        self.assertEqual(record["jev"]["state"], "binary_unusable")
        self.assertEqual(record["severity"], "error")

    def test_unknown_check_exit_code_fails_closed(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        for code in (1, 2, 5, 6, 99, None):
            with self.subTest(code=code):
                record = self.run_preflight(self.env(), FakeRunner(check_exit=code))
                self.assertEqual(record["jev"]["state"], "check_failed")
                self.assertEqual(record["screening_mode"], "jev")
                self.assertFalse(record["jev"]["usable"])
                self.assertEqual(record["severity"], "error")

    def test_environment_only_credential_is_ready_but_warns(self) -> None:
        self.install_binary()
        self.write_key("speckit-pro", "tavily.key")
        record = self.run_preflight(self.env(TYPESAFE_API_KEY=SECRET_VALUE))
        self.assertEqual(record["jev"]["state"], "ready")
        self.assertEqual(record["jev"]["credential_source"], "environment")
        self.assertEqual(record["screening_mode"], "jev")
        self.assertEqual(record["severity"], "warning")
        self.assertIn("jev_environment_only_credential", [item["code"] for item in record["warnings"]])

    def test_empty_variables_count_as_unset(self) -> None:
        self.install_binary()
        record = self.run_preflight(
            self.env(TYPESAFE_API_KEY="", JEV_API_KEY_FILE="", EVALUATE_BIN=""), FakeRunner(check_exit=3)
        )
        self.assertEqual(record["jev"]["state"], "no_credential")
        self.assertEqual(record["jev"]["credential_source"], "none")

    def test_evaluate_bin_overrides_the_default_location(self) -> None:
        other = self.home / "custom" / "evaluate"
        other.parent.mkdir(parents=True)
        other.write_text("placeholder\n", encoding="utf-8")
        other.chmod(0o755)
        runner = FakeRunner(check_exit=3)
        record = self.run_preflight(self.env(EVALUATE_BIN=str(other)), runner)
        self.assertEqual(record["jev"]["binary"], "present")
        self.assertEqual(runner.calls[0][0][0], str(other))

    # --- Search and docs key sources -----------------------------------------

    def test_missing_tavily_key_is_warning_search_unavailable(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        record = self.run_preflight(self.env())
        self.assertEqual(record["search"]["state"], "missing")
        self.assertIn("search_unavailable", [item["code"] for item in record["warnings"]])
        self.assertEqual(record["severity"], "warning")

    def test_tavily_key_file_with_group_bits_is_error(self) -> None:
        self.write_key("speckit-pro", "tavily.key", mode=0o640)
        record = self.run_preflight(self.env())
        self.assertEqual(record["search"]["state"], "unusable")
        self.assertEqual(record["search"]["reason"], "key_file_permissions")
        self.assertEqual(record["severity"], "error")

    def test_empty_and_oversized_key_files_are_unusable(self) -> None:
        for content, reason in (("", "key_file_empty"), ("x" * 9000, "key_file_too_large")):
            with self.subTest(reason=reason):
                self.write_key("speckit-pro", "tavily.key", content=content)
                record = self.run_preflight(self.env())
                self.assertEqual(record["search"]["reason"], reason)

    def test_tavily_environment_key_is_configured_with_warning(self) -> None:
        record = self.run_preflight(self.env(TAVILY_API_KEY=SECRET_VALUE))
        self.assertEqual(record["search"]["state"], "configured")
        self.assertEqual(record["search"]["source"], "environment")
        self.assertIn("search_environment_only_credential", [item["code"] for item in record["warnings"]])

    def test_context7_is_optional_and_keyless_is_not_a_warning(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        self.write_key("speckit-pro", "tavily.key")
        record = self.run_preflight(self.env())
        self.assertEqual(record["docs"]["state"], "keyless")
        self.assertEqual(record["severity"], "ok")

    def test_context7_key_file_is_configured(self) -> None:
        self.write_key("speckit-pro", "context7.key")
        record = self.run_preflight(self.env())
        self.assertEqual(record["docs"]["state"], "configured")
        self.assertEqual(record["docs"]["source"], "key_file")

    # --- Value-free and bounded ----------------------------------------------

    def test_never_opens_a_key_file_or_prints_a_value(self) -> None:
        self.install_binary()
        self.write_key("racecraft-jev", "typesafe.key")
        self.write_key("speckit-pro", "tavily.key")
        real_open = open

        def guarded_open(file, *args, **kwargs):  # type: ignore[no-untyped-def]
            if str(file).endswith(".key"):
                raise AssertionError(f"preflight opened a key file: {file}")
            return real_open(file, *args, **kwargs)

        with mock.patch("builtins.open", guarded_open), mock.patch.object(Path, "read_text", side_effect=AssertionError("read_text")), mock.patch.object(Path, "read_bytes", side_effect=AssertionError("read_bytes")):
            record = self.run_preflight(self.env(OPENROUTER_API_KEY=SECRET_VALUE, TAVILY_API_KEY=SECRET_VALUE))
        self.assertNotIn(SECRET_VALUE, json.dumps(record))

    def test_child_environment_is_an_allowlist(self) -> None:
        self.install_binary()
        runner = FakeRunner()
        self.run_preflight(
            self.env(
                TYPESAFE_API_KEY=SECRET_VALUE,
                TAVILY_API_KEY=SECRET_VALUE,
                JEV_PROVIDER="attacker",
                UNRELATED_SECRET=SECRET_VALUE,
            ),
            runner,
        )
        _, child_env = runner.calls[-1]
        self.assertNotIn("TAVILY_API_KEY", child_env)
        self.assertNotIn("UNRELATED_SECRET", child_env)
        self.assertEqual(child_env["JEV_PROVIDER"], "typesafe")
        self.assertEqual(child_env["JEV_FALLBACK_PROVIDER"], "openrouter")
        self.assertIn("TYPESAFE_API_KEY", child_env)
        self.assertNotIn("OPENROUTER_API_KEY", child_env)
        self.assertLessEqual(set(child_env), preflight.CHILD_ENVIRONMENT_NAMES)

    def test_evaluate_bin_must_name_an_evaluate_file(self) -> None:
        other = self.home / "custom" / "jev-binary"
        other.parent.mkdir(parents=True)
        other.write_text("placeholder\n", encoding="utf-8")
        other.chmod(0o755)
        record = self.run_preflight(self.env(EVALUATE_BIN=str(other)))
        self.assertEqual(record["jev"]["binary"], "missing")

    def test_display_paths_hide_the_home_directory(self) -> None:
        record = self.run_preflight(self.env())
        self.assertNotIn(str(self.home), json.dumps(record))


@unittest.skipUnless(os.name == "posix", "fake evaluate binary relies on a shebang")
class PreflightProcessTests(unittest.TestCase):
    """The real subprocess path against a fake `evaluate` program."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="research-preflight-proc-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()

    def fake_binary(self, *, version: str, check_exit: int) -> Path:
        path = self.home / "bin" / "evaluate"
        path.parent.mkdir(parents=True)
        path.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "args = sys.argv[1:]\n"
            f"if args == ['version']:\n    print({version!r}); raise SystemExit(0)\n"
            "if args == ['call', '--check', '--plugin-defaults']:\n"
            "    sys.stderr.write('raw child stderr must never surface\\n')\n"
            f"    raise SystemExit({check_exit})\n"
            "raise SystemExit(64)\n",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def run_helper(self, env: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], dict]:
        request = {
            "schema_version": "1.0",
            "request_id": "test-research-broker-preflight",
            "helper_id": "research-broker-preflight",
            "operation": "research-broker-preflight",
            "mode": "read_only",
            "inputs": {},
        }
        completed = subprocess.run(
            [sys.executable, "-m", "speckit_pro_runner"],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env={"PYTHONPATH": str(PLUGIN_ROOT), "PATH": os.defpath, **env},
            check=False,
            timeout=60,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        return completed, json.loads(lines[-1])

    def test_runner_reports_ready_through_the_real_process_path(self) -> None:
        binary = self.fake_binary(version="0.9.0", check_exit=0)
        key = self.home / ".config" / "racecraft-jev" / "typesafe.key"
        key.parent.mkdir(parents=True)
        key.write_text(SECRET_VALUE, encoding="utf-8")
        key.chmod(0o600)
        completed, response = self.run_helper({"HOME": str(self.home), "EVALUATE_BIN": str(binary)})
        self.assertEqual(response["status"], "ok", completed.stderr)
        self.assertEqual(response["data"]["jev"]["state"], "ready")
        self.assertFalse(response["data"]["writes_state"])
        self.assertNotIn("raw child stderr", completed.stdout + completed.stderr)
        self.assertNotIn(SECRET_VALUE, completed.stdout + completed.stderr)

    def test_runner_reports_expected_failure_for_an_unusable_credential(self) -> None:
        binary = self.fake_binary(version="0.9.1", check_exit=4)
        completed, response = self.run_helper(
            {"HOME": str(self.home), "EVALUATE_BIN": str(binary), "TYPESAFE_API_KEY": SECRET_VALUE}
        )
        self.assertEqual(response["status"], "expected_failure")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(response["data"]["jev"]["state"], "credential_unusable")
        self.assertIn("jev_credential_unusable", [diag["code"] for diag in response["diagnostics"]])
        self.assertNotIn(SECRET_VALUE, completed.stdout + completed.stderr)

    def test_runner_rejects_unknown_inputs(self) -> None:
        request = {
            "schema_version": "1.0",
            "helper_id": "research-broker-preflight",
            "operation": "research-broker-preflight",
            "mode": "read_only",
            "inputs": {"evaluate_bin": "/somewhere"},
        }
        completed = subprocess.run(
            [sys.executable, "-m", "speckit_pro_runner"],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env={"PYTHONPATH": str(PLUGIN_ROOT), "PATH": os.defpath, "HOME": str(self.home)},
            check=False,
            timeout=60,
        )
        response = json.loads(completed.stdout.splitlines()[-1])
        self.assertEqual(response["status"], "input_error")


if __name__ == "__main__":
    suite = unittest.TestSuite(
        [
            unittest.defaultTestLoader.loadTestsFromTestCase(PreflightStateTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(PreflightProcessTests),
        ]
    )
    raise SystemExit(run_counted(suite, label="test-research-broker-preflight"))

#!/usr/bin/env python3
"""Focused tests for receipt-bound installed native evaluation tools."""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

import native_eval_toolchain as toolchain  # noqa: E402
from native_eval_toolchain import (  # noqa: E402
    NativeToolchainError,
    prepare_claude_plugin_toolchain,
    prepare_native_toolchain,
    verify_native_toolchain,
)
from test_result import run_counted  # noqa: E402


class NativeEvalToolchainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._cleanup)
        self.root = Path(self.temp.name).resolve()
        os.chmod(self.root, 0o700)
        self.workspace = self._workspace("workspace")
        self.capture = self.root / "captured.json"

        python_parent = self.root / "installed-python"
        self.python_root = python_parent / "cpython-3.13.13"
        (self.python_root / "bin").mkdir(parents=True)
        self.python_executable = self.python_root / "bin" / "python3.13"
        self.python_executable.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import os
                from pathlib import Path
                import runpy
                import sys

                if sys.argv[1:] == ["--version"]:
                    print("Python 3.13.13")
                elif len(sys.argv) >= 3 and sys.argv[1] == "-I":
                    sys.argv = sys.argv[2:]
                    runpy.run_path(sys.argv[0], run_name="__main__")
                elif len(sys.argv) == 3 and Path(sys.argv[1]).name == "specify" and sys.argv[2] == "--version":
                    print("specify 1.0.1")
                else:
                    Path({str(self.capture)!r}).write_text(json.dumps({{
                        "argv": sys.argv,
                        "environment": dict(os.environ),
                    }}, sort_keys=True), encoding="utf-8")
                """
            ),
            encoding="utf-8",
        )
        os.chmod(self.python_executable, 0o755)
        self.python_alias = python_parent / "cpython-3.13"
        self.python_alias.symlink_to(self.python_root.name, target_is_directory=True)

        self.specify_root = self.root / "installed-tools" / "specify-cli"
        (self.specify_root / "bin").mkdir(parents=True)
        (self.specify_root / "lib" / "python3.13" / "site-packages").mkdir(parents=True)
        package = self.specify_root / "lib" / "python3.13" / "site-packages" / "specify_cli"
        package.mkdir()
        (package / "__init__.py").write_text("fixture = True\n", encoding="utf-8")
        distribution = package.parent / "specify_cli-1.0.1.dist-info"
        distribution.mkdir()
        (distribution / "METADATA").write_text(
            "Metadata-Version: 2.5\nName: specify-cli\nVersion: 1.0.1\n",
            encoding="utf-8",
        )
        (distribution / "direct_url.json").write_text(json.dumps({
            "url": "https://github.com/github/spec-kit.git",
            "vcs_info": {
                "vcs": "git",
                "commit_id": "9118ed15a0ba65053469a94c560ea5d233f75884",
                "requested_revision": "v1.0.1",
            },
        }, separators=(",", ":")), encoding="utf-8")
        self.specify_python = self.specify_root / "bin" / "python"
        self.specify_python.symlink_to(self.python_alias / "bin" / "python3.13")
        self.specify_entry = self.specify_root / "bin" / "specify"
        self.specify_entry.write_text(
            f"#!{self.specify_python}\nraise SystemExit('controller must use resolved Python')\n",
            encoding="utf-8",
        )
        os.chmod(self.specify_entry, 0o755)
        self.specify_candidate = self.root / "bin" / "specify"
        self.specify_candidate.parent.mkdir()
        self.specify_candidate.symlink_to(self.specify_entry)

        self.uv_root = self.root / "cellar" / "uv" / "0.12.5"
        (self.uv_root / "bin").mkdir(parents=True)
        self.uv_executable = self.uv_root / "bin" / "uv"
        self.uv_executable.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import sys
                if sys.argv[1:] == ["--version"]:
                    print("uv 0.12.5 (fixture)")
                else:
                    raise SystemExit(2)
                """
            ),
            encoding="utf-8",
        )
        os.chmod(self.uv_executable, 0o755)
        self.uv_candidate = self.root / "homebrew-bin" / "uv"
        self.uv_candidate.parent.mkdir()
        self.uv_candidate.symlink_to(self.uv_executable)

    def _cleanup(self) -> None:
        for path in self.root.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                os.chmod(path, 0o700)
        self.temp.cleanup()

    def _workspace(self, name: str) -> Path:
        workspace = self.root / name
        (workspace / ".codex").mkdir(parents=True)
        os.chmod(workspace, 0o700)
        os.chmod(workspace / ".codex", 0o700)
        return workspace

    def _plugin(self, name: str) -> Path:
        plugin = self.root / name
        plugin.mkdir()
        os.chmod(plugin, 0o700)
        return plugin

    def prepare(
        self,
        workspace: Path | None = None,
        *,
        required_tools: tuple[str, ...] = ("specify", "uv"),
    ):
        return prepare_native_toolchain(
            workspace or self.workspace,
            required_tools=required_tools,
            specify_executable=self.specify_candidate,
            uv_executable=self.uv_candidate,
        )

    def test_prepares_exact_opt_in_launchers_roots_and_receipts(self) -> None:
        prepared = self.prepare()

        self.assertEqual(set(prepared.launchers), {"specify", "uv"})
        self.assertEqual(
            prepared.path_entries,
            (
                self.workspace / ".codex" / "native-eval-tool-bin",
                self.uv_root / "bin",
            ),
        )
        self.assertEqual(
            prepared.readonly_roots,
            tuple(sorted((self.python_root, self.specify_root, self.uv_root), key=str)),
        )
        self.assertEqual(
            prepared.environment,
            {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "PYTHONSAFEPATH": "1",
            },
        )
        identity = prepared.runtime_identity
        self.assertEqual(identity["schema_version"], "native-eval-toolchain/v1")
        self.assertEqual(identity["required_tools"], ["specify", "uv"])
        self.assertEqual(identity["tools"]["specify"]["version"], "specify 1.0.1")
        self.assertEqual(identity["tools"]["specify"]["python_version"], "Python 3.13.13")
        self.assertEqual(identity["tools"]["specify"]["distribution"]["version"], "1.0.1")
        self.assertEqual(
            identity["tools"]["specify"]["distribution"]["direct_url"]["vcs_info"]["commit_id"],
            "9118ed15a0ba65053469a94c560ea5d233f75884",
        )
        self.assertEqual(identity["tools"]["uv"]["version"], "uv 0.12.5 (fixture)")
        self.assertEqual(identity["launchers"]["specify"]["path"], ".codex/native-eval-tool-bin/specify")
        self.assertNotIn(str(self.workspace), json.dumps(identity["launchers"], sort_keys=True))
        self.assertEqual(stat.S_IMODE(prepared.launchers["specify"].stat().st_mode), 0o555)
        self.assertNotIn(b"/bin/bash", prepared.launchers["specify"].read_bytes())
        verify_native_toolchain(prepared)

    def test_generated_python_launcher_forwards_arguments_and_closes_environment(self) -> None:
        prepared = self.prepare(required_tools=("specify",))
        environment = {
            "PATH": "/controlled/bin:/usr/bin:/bin",
            "LANG": "en_US.UTF-8",
            "SECRET_TOKEN": "must-not-cross",
            "HTTP_PROXY": "must-not-cross",
            "UV_INDEX_URL": "https://secret.example",
        }
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(prepared.launchers["specify"]),
                "argument with spaces",
                "--flag=x",
            ],
            cwd=self.workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        captured = json.loads(self.capture.read_text(encoding="utf-8"))
        self.assertEqual(
            captured["argv"][1:],
            [str(self.specify_entry), "argument with spaces", "--flag=x"],
        )
        passed = captured["environment"]
        self.assertEqual(passed["HOME"], str(self.workspace))
        self.assertEqual(
            passed["PYTHONPATH"],
            str(self.specify_root / "lib" / "python3.13" / "site-packages"),
        )
        self.assertEqual(passed["PATH"], environment["PATH"])
        self.assertEqual(passed["LANG"], environment["LANG"])
        for key in ("SECRET_TOKEN", "HTTP_PROXY", "PYTHONHOME", "UV_INDEX_URL"):
            self.assertNotIn(key, passed)

    def test_identity_is_stable_across_equivalent_workspace_relocation(self) -> None:
        first = self.prepare(self.workspace, required_tools=("specify",))
        second_workspace = self._workspace("other-workspace")
        second = self.prepare(second_workspace, required_tools=("specify",))

        self.assertEqual(first.runtime_identity, second.runtime_identity)
        self.assertNotEqual(first.launchers["specify"], second.launchers["specify"])
        self.assertEqual(
            first.launchers["specify"].read_bytes(),
            second.launchers["specify"].read_bytes(),
        )

    def test_tools_are_never_enabled_implicitly(self) -> None:
        with self.assertRaisesRegex(NativeToolchainError, "at least one"):
            self.prepare(required_tools=())
        with self.assertRaisesRegex(NativeToolchainError, "unsupported"):
            self.prepare(required_tools=("git",))
        with self.assertRaisesRegex(NativeToolchainError, "collection"):
            prepare_native_toolchain(self.workspace, required_tools="uv")

        uv_only = self.prepare(required_tools=("uv",))
        self.assertIsNone(uv_only.launcher_dir)
        self.assertEqual(uv_only.launchers, {"uv": self.uv_executable})
        self.assertFalse((self.workspace / ".codex" / "native-eval-tool-bin").exists())
        self.assertNotIn("specify", uv_only.runtime_identity["tools"])

    def test_preparation_rejects_unsafe_or_ambiguous_installations(self) -> None:
        cases: list[tuple[Path, int, str]] = [
            (self.specify_entry, 0o775, "group/world writable"),
            (self.python_executable, 0o777, "group/world writable"),
            (self.specify_root, 0o777, "group/world writable"),
        ]
        for index, (path, unsafe_mode, message) in enumerate(cases):
            with self.subTest(path=path):
                original_mode = stat.S_IMODE(path.stat().st_mode)
                os.chmod(path, unsafe_mode)
                try:
                    with self.assertRaisesRegex(NativeToolchainError, message):
                        self.prepare(
                            self._workspace(f"unsafe-{index}"),
                            required_tools=("specify",),
                        )
                finally:
                    os.chmod(path, original_mode)

        original = self.specify_entry.read_bytes()
        self.specify_entry.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        os.chmod(self.specify_entry, 0o755)
        try:
            with self.assertRaisesRegex(NativeToolchainError, "one absolute Python"):
                self.prepare(self._workspace("bad-shebang"), required_tools=("specify",))
        finally:
            self.specify_entry.write_bytes(original)
            os.chmod(self.specify_entry, 0o755)

    def test_preexisting_controller_output_is_never_overwritten(self) -> None:
        destination = self.workspace / ".codex" / "native-eval-tool-bin"
        destination.mkdir()
        marker = destination / "preserve"
        marker.write_text("owned elsewhere", encoding="utf-8")

        with self.assertRaisesRegex(NativeToolchainError, "must not pre-exist"):
            self.prepare(required_tools=("specify",))
        self.assertEqual(marker.read_text(encoding="utf-8"), "owned elsewhere")

    def test_claude_preexisting_outputs_and_runtime_are_never_removed(self) -> None:
        for name in ("specify", "python3"):
            with self.subTest(name=name):
                plugin = self._plugin(f"preexisting-{name}")
                bin_root = plugin / "bin"
                bin_root.mkdir()
                output = bin_root / name
                if name == "python3":
                    output.symlink_to("owned-target")
                    expected = os.readlink(output)
                else:
                    output.write_bytes(b"owned bytes\n")
                    os.chmod(output, 0o744)
                    expected = output.read_bytes()
                before = output.lstat()
                with self.assertRaisesRegex(NativeToolchainError, "must not pre-exist"):
                    prepare_claude_plugin_toolchain(
                        plugin,
                        required_tools=("specify",),
                        specify_executable=self.specify_candidate,
                    )
                self.assertTrue(output.exists() or output.is_symlink())
                self.assertEqual(
                    os.readlink(output) if output.is_symlink() else output.read_bytes(),
                    expected,
                )
                self.assertEqual(stat.S_IMODE(output.lstat().st_mode), stat.S_IMODE(before.st_mode))

        plugin = self._plugin("preexisting-runtime")
        runtime = plugin / ".native-toolchain"
        runtime.mkdir()
        marker = runtime / "owned"
        marker.write_text("preserve", encoding="utf-8")
        with self.assertRaisesRegex(NativeToolchainError, "must not pre-exist"):
            prepare_claude_plugin_toolchain(
                plugin,
                required_tools=("specify",),
                specify_executable=self.specify_candidate,
            )
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")

    def test_claude_failed_second_output_removes_only_first_new_output(self) -> None:
        plugin = self._plugin("partial-output")
        original_open = Path.open

        def fail_launcher_open(path: Path, *args, **kwargs):
            if path == plugin / "bin" / "specify":
                raise OSError("forced launcher creation failure")
            return original_open(path, *args, **kwargs)

        with mock.patch.object(Path, "open", new=fail_launcher_open):
            with self.assertRaisesRegex(OSError, "forced launcher"):
                prepare_claude_plugin_toolchain(
                    plugin,
                    required_tools=("specify",),
                    specify_executable=self.specify_candidate,
                )
        self.assertFalse((plugin / "bin").exists())
        self.assertFalse((plugin / ".native-toolchain").exists())

    def test_failed_postwrite_verification_removes_only_new_controller_output(self) -> None:
        destination = self.workspace / ".codex" / "native-eval-tool-bin"
        with mock.patch.object(
            toolchain,
            "verify_native_toolchain",
            side_effect=NativeToolchainError("forced verifier failure"),
        ):
            with self.assertRaisesRegex(NativeToolchainError, "forced verifier failure"):
                self.prepare(required_tools=("specify",))
        self.assertFalse(destination.exists())
        self.assertTrue((self.workspace / ".codex").is_dir())

    def test_verifier_rejects_launcher_installation_link_and_identity_mutation(self) -> None:
        prepared = self.prepare(required_tools=("specify",))
        launcher = prepared.launchers["specify"]
        os.chmod(launcher.parent, 0o700)
        os.chmod(launcher, 0o755)
        launcher.write_text("#!/usr/bin/false\n", encoding="utf-8")
        with self.assertRaisesRegex(NativeToolchainError, "launcher"):
            verify_native_toolchain(prepared)

        other_workspace = self._workspace("mutated-install")
        prepared_install = self.prepare(other_workspace, required_tools=("uv",))
        executed = self.root / "mutated-uv-executed"
        self.uv_executable.write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\n"
            f"Path({str(executed)!r}).write_text('unsafe', encoding='utf-8')\n",
            encoding="utf-8",
        )
        os.chmod(self.uv_executable, 0o755)
        with self.assertRaises(NativeToolchainError):
            verify_native_toolchain(prepared_install)
        self.assertFalse(executed.exists(), "mutated executable ran before receipt rejection")

        identity = dict(prepared_install.runtime_identity)
        identity["required_tools"] = ["specify"]
        tampered = replace(prepared_install, runtime_identity=identity)
        with self.assertRaisesRegex(NativeToolchainError, "digest"):
            verify_native_toolchain(tampered)

    def test_verifier_rejects_changed_environment_contract(self) -> None:
        prepared = self.prepare(required_tools=("uv",))
        for environment in (
            {**prepared.environment, "PYTHONPATH": "/untrusted"},
            {**prepared.environment, "PYTHONDONTWRITEBYTECODE": "0"},
            {},
        ):
            with self.subTest(environment=environment):
                with self.assertRaisesRegex(NativeToolchainError, "environment changed"):
                    verify_native_toolchain(replace(prepared, environment=environment))

    def test_symlink_chain_is_bound_and_noncanonical_source_is_rejected(self) -> None:
        prepared = self.prepare(required_tools=("specify",))
        links = prepared.runtime_identity["tools"]["specify"]["interpreter"]["links"]
        self.assertEqual(
            [record["path"] for record in links],
            [str(self.specify_python), str(self.python_alias)],
        )

        os.chmod(prepared.launchers["specify"].parent, 0o700)
        self.specify_candidate.unlink()
        self.specify_candidate.symlink_to(self.uv_executable)
        with self.assertRaises(NativeToolchainError):
            verify_native_toolchain(prepared)

    def test_probe_environment_does_not_inherit_process_secrets(self) -> None:
        original = os.environ.get("SECRET_NATIVE_TOOLCHAIN_TEST")
        os.environ["SECRET_NATIVE_TOOLCHAIN_TEST"] = "do-not-copy"
        calls: list[dict[str, str]] = []
        original_run = toolchain.subprocess.run

        def observed_run(*args, **kwargs):
            calls.append(dict(kwargs["env"]))
            return original_run(*args, **kwargs)

        try:
            with mock.patch.object(toolchain.subprocess, "run", side_effect=observed_run):
                self.prepare(required_tools=("uv",))
        finally:
            if original is None:
                os.environ.pop("SECRET_NATIVE_TOOLCHAIN_TEST", None)
            else:
                os.environ["SECRET_NATIVE_TOOLCHAIN_TEST"] = original
        self.assertGreaterEqual(len(calls), 2)
        self.assertTrue(all("SECRET_NATIVE_TOOLCHAIN_TEST" not in environment for environment in calls))
        self.assertTrue(all(environment["HOME"] == str(self.workspace) for environment in calls))

    def test_claude_plugin_runtime_is_relocatable_and_contains_no_external_links(self) -> None:
        plugin = self._plugin("plugin")
        prepared = prepare_claude_plugin_toolchain(
            plugin,
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )

        self.assertEqual(prepared.path_entries, (plugin / "bin",))
        self.assertEqual(
            prepared.readonly_roots,
            (plugin / ".native-toolchain", plugin / "bin"),
        )
        self.assertEqual(prepared.launchers["specify"], plugin / "bin" / "specify")
        identity = prepared.runtime_identity
        self.assertEqual(identity["schema_version"], "native-eval-toolchain/claude-plugin-v1")
        self.assertEqual(identity["transport"], "claude-plugin-bin")
        self.assertEqual(identity["staged"]["python"]["path"], ".native-toolchain/python")
        self.assertEqual(identity["staged"]["specify"]["path"], ".native-toolchain/specify")
        self.assertNotIn(str(plugin), json.dumps(identity["staged"], sort_keys=True))
        self.assertNotIn(str(self.python_root), prepared.launchers["specify"].read_text())
        self.assertNotIn(str(self.specify_root), prepared.launchers["specify"].read_text())

        for path in (plugin / ".native-toolchain").rglob("*"):
            if path.is_symlink():
                target = (path.parent / os.readlink(path)).resolve(strict=True)
                target.relative_to(plugin / ".native-toolchain")
        verify_native_toolchain(prepared)

        moved = self._plugin("moved-plugin")
        moved_prepared = prepare_claude_plugin_toolchain(
            moved,
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )
        self.assertEqual(prepared.runtime_identity, moved_prepared.runtime_identity)
        self.assertEqual(
            prepared.launchers["specify"].read_bytes(),
            moved_prepared.launchers["specify"].read_bytes(),
        )

    def test_claude_plugin_launcher_forwards_arguments_and_closes_environment(self) -> None:
        plugin = self._plugin("plugin-launch")
        prepared = prepare_claude_plugin_toolchain(
            plugin,
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )
        environment = {
            "PATH": f"{prepared.path_entries[0]}:/usr/bin:/bin",
            "LANG": "en_US.UTF-8",
            "SECRET_TOKEN": "must-not-cross",
            "HTTP_PROXY": "must-not-cross",
            "UV_INDEX_URL": "https://secret.example",
        }
        result = subprocess.run(
            [str(prepared.launchers["specify"]), "argument with spaces", "--flag=x"],
            cwd=plugin,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        captured = json.loads(self.capture.read_text(encoding="utf-8"))
        self.assertEqual(
            captured["argv"][1:],
            [
                str(plugin / ".native-toolchain" / "specify" / "bin" / "specify"),
                "argument with spaces",
                "--flag=x",
            ],
        )
        passed = captured["environment"]
        self.assertEqual(passed["HOME"], str(plugin))
        self.assertEqual(
            passed["PYTHONPATH"],
            str(
                plugin
                / ".native-toolchain"
                / "specify"
                / "lib"
                / "python3.13"
                / "site-packages"
            ),
        )
        self.assertEqual(passed["PATH"], environment["PATH"])
        self.assertEqual(passed["LANG"], environment["LANG"])
        for key in ("SECRET_TOKEN", "HTTP_PROXY", "PYTHONHOME", "UV_INDEX_URL"):
            self.assertNotIn(key, passed)

    def test_claude_plugin_runtime_rejects_tamper_missing_files_and_external_links(self) -> None:
        escaped = self.specify_root / "escaped"
        escaped.symlink_to("/etc/passwd")
        try:
            with self.assertRaisesRegex(NativeToolchainError, "outside admitted roots"):
                prepare_claude_plugin_toolchain(
                    self._plugin("escaped-plugin"),
                    required_tools=("specify",),
                    specify_executable=self.specify_candidate,
                )
        finally:
            escaped.unlink()

        plugin = self._plugin("tamper-plugin")
        prepared = prepare_claude_plugin_toolchain(
            plugin,
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )
        launcher = prepared.launchers["specify"]
        os.chmod(launcher, 0o755)
        launcher.write_text("#!/usr/bin/false\n", encoding="utf-8")
        with self.assertRaisesRegex(NativeToolchainError, "launcher"):
            verify_native_toolchain(prepared)

        plugin_missing = self._plugin("missing-plugin")
        missing = prepare_claude_plugin_toolchain(
            plugin_missing,
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )
        dependency = (
            plugin_missing
            / ".native-toolchain"
            / "specify"
            / "lib"
            / "python3.13"
            / "site-packages"
            / "specify_cli"
            / "__init__.py"
        )
        cursor = dependency.parent
        runtime_root = plugin_missing / ".native-toolchain"
        while cursor != runtime_root:
            os.chmod(cursor, 0o700)
            cursor = cursor.parent
        dependency.unlink()
        with self.assertRaisesRegex(NativeToolchainError, "staged|changed"):
            verify_native_toolchain(missing)

        environment_prepared = prepare_claude_plugin_toolchain(
            self._plugin("environment-plugin"),
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )
        with self.assertRaisesRegex(NativeToolchainError, "environment changed"):
            verify_native_toolchain(
                replace(environment_prepared, environment={"PYTHONHOME": "/unsafe"})
            )

    def test_claude_plugin_runtime_executes_after_source_roots_are_unavailable(self) -> None:
        plugin = self._plugin("source-independent-plugin")
        prepared = prepare_claude_plugin_toolchain(
            plugin,
            required_tools=("specify",),
            specify_executable=self.specify_candidate,
        )
        hidden_python = self.python_root.with_name("python-unavailable")
        hidden_specify = self.specify_root.with_name("specify-unavailable")
        self.python_root.rename(hidden_python)
        self.specify_root.rename(hidden_specify)
        try:
            result = subprocess.run(
                [str(prepared.launchers["specify"]), "--version"],
                cwd=plugin,
                env={"PATH": f"{prepared.path_entries[0]}:/usr/bin:/bin"},
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        finally:
            hidden_specify.rename(self.specify_root)
            hidden_python.rename(self.python_root)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "specify 1.0.1"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalToolchainTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-toolchain"))

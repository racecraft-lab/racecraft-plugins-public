#!/usr/bin/env python3
"""Layer 4 tests for typesafe-jev release builds, installation and launcher updates.

The archives and checksums the script writes are read by two consumers that
ship in the plugin: install_evaluate.py and `evaluate update`. These tests
check the script's output against the installer's own parser, and check that
the version stamped into the binary is the bare version those consumers
compare, never the tag.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import signal
import socketserver
import threading
import time
import subprocess
import sys
import tarfile
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_SCRIPTS = REPO_ROOT / "typesafe-jev/plugin/scripts"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


from script_loader import load_script  # noqa: E402


def load_module(module_name: str, path: Path) -> ModuleType:
    return load_script(module_name, path)


BUILD = load_module("build_typesafe_jev_release", REPO_ROOT / "scripts" / "build-typesafe-jev-release.py")
INSTALLER = load_module(
    "install_evaluate", REPO_ROOT / "typesafe-jev" / "plugin" / "scripts" / "install_evaluate.py"
)
LAUNCHER = load_module("evaluate_launch", REPO_ROOT / "typesafe-jev/plugin/scripts/evaluate_launch.py")
GO_CHECK = load_module("check_go_module", REPO_ROOT / "scripts" / "check-go-module.py")
REAL_FETCH = INSTALLER.fetch


@contextlib.contextmanager
def malformed_release_host(response: bytes):
    """Serve malformed HTTP locally, including errors raised while reading."""
    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.recv(65536)
            self.request.sendall(response)

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        worker.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}/download"
        finally:
            server.shutdown()
            worker.join(timeout=2)


MALFORMED_HTTP = {
    "IncompleteRead": b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\nzz\r\n",
    "BadStatusLine": b"garbage\r\n\r\n",
    "LineTooLong": b"HTTP/1.1 200 OK\r\nX: " + b"a" * 70000 + b"\r\n\r\n",
}


def completed(argv: list[str], returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout, "")


class TypesafeJevReleaseBuildTests(unittest.TestCase):
    def test_only_typesafe_jev_tags_name_a_release(self) -> None:
        self.assertEqual("0.9.0", BUILD.version_from_tag("typesafe-jev-v0.9.0"))
        self.assertEqual("1.0.0-rc.1", BUILD.version_from_tag("typesafe-jev-v1.0.0-rc.1"))
        for tag in ("v0.9.0", "0.9.0", "speckit-pro-v2.33.0", "typesafe-jev-0.9.0", "typesafe-jev-v0.9", ""):
            with self.subTest(tag=tag), self.assertRaises(BUILD.ReleaseBuildError):
                BUILD.version_from_tag(tag)

    def test_release_targets_match_the_pull_request_cross_compile(self) -> None:
        self.assertEqual(GO_CHECK.RELEASE_TARGETS, BUILD.RELEASE_TARGETS)

    def test_archives_are_reproducible_and_hold_the_binary_and_licence(self) -> None:
        first = BUILD.archive_bytes(b"binary", b"licence")
        self.assertEqual(first, BUILD.archive_bytes(b"binary", b"licence"))
        with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as tar:
            members = {member.name: member for member in tar.getmembers()}
        self.assertEqual({"evaluate", "LICENSE"}, set(members))
        self.assertTrue(members["evaluate"].isreg())
        self.assertEqual(0o755, members["evaluate"].mode)
        self.assertEqual(b"binary", INSTALLER.extract_binary(first, "evaluate"))

    def test_checksums_parse_with_the_installer(self) -> None:
        archives = {
            BUILD.asset_name("linux", "amd64"): BUILD.archive_bytes(b"linux", b"licence"),
            BUILD.asset_name("darwin", "arm64"): BUILD.archive_bytes(b"darwin", b"licence"),
        }
        sums = BUILD.sums_text(archives).encode("utf-8")
        for name, data in archives.items():
            with self.subTest(asset=name):
                self.assertEqual(hashlib.sha256(data).hexdigest(), INSTALLER.expected_checksum(sums, name))

    def test_build_stamps_the_bare_version_and_writes_every_asset(self) -> None:
        calls: list[list[str]] = []

        def fake_run(argv, **kwargs):  # type: ignore[no-untyped-def]
            calls.append(list(argv))
            Path(argv[argv.index("-o") + 1]).write_bytes(f"{kwargs['env']['GOOS']}/{kwargs['env']['GOARCH']}".encode())
            self.assertEqual("0", kwargs["env"]["CGO_ENABLED"])
            self.assertFalse(kwargs["shell"])
            return completed(argv)

        with tempfile.TemporaryDirectory() as out, unittest.mock.patch.object(BUILD.subprocess, "run", side_effect=fake_run):
            with contextlib.redirect_stdout(io.StringIO()):
                BUILD.build("0.9.0", Path(out))
            written = sorted(path.name for path in Path(out).iterdir())
            sums = (Path(out) / BUILD.SUMS_NAME).read_bytes()
            linux = (Path(out) / BUILD.asset_name("linux", "amd64")).read_bytes()

        self.assertEqual(len(BUILD.RELEASE_TARGETS), len(calls))
        for argv in calls:
            self.assertEqual("go", argv[0])
            self.assertIn("-s -w -X main.version=0.9.0", argv)
            self.assertFalse(any("typesafe-jev-v" in arg for arg in argv))
        self.assertEqual(
            sorted([BUILD.asset_name(goos, goarch) for goos, goarch in BUILD.RELEASE_TARGETS] + [BUILD.SUMS_NAME]),
            written,
        )
        self.assertEqual(hashlib.sha256(linux).hexdigest(), INSTALLER.expected_checksum(sums, BUILD.asset_name("linux", "amd64")))
        self.assertEqual(b"linux/amd64", INSTALLER.extract_binary(linux, "evaluate"))

    def test_asset_check_rejects_a_mismatch_and_a_missing_archive(self) -> None:
        archives = {
            BUILD.asset_name(goos, goarch): BUILD.archive_bytes(goos.encode(), b"licence")
            for goos, goarch in BUILD.RELEASE_TARGETS
        }
        with tempfile.TemporaryDirectory() as scratch:
            directory = Path(scratch)
            for name, data in archives.items():
                (directory / name).write_bytes(data)
            (directory / BUILD.SUMS_NAME).write_text(BUILD.sums_text(archives), encoding="utf-8")
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, BUILD.PROVENANCE_NAME):
                BUILD.check_assets(directory)
            (directory / BUILD.PROVENANCE_NAME).write_text("{}", encoding="utf-8")
            self.assertEqual(set(archives), set(BUILD.check_assets(directory)))

            (directory / BUILD.asset_name("linux", "arm64")).write_bytes(b"tampered")
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, "does not match"):
                BUILD.check_assets(directory)

            (directory / BUILD.asset_name("linux", "arm64")).unlink()
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, "has no"):
                BUILD.check_assets(directory)

    def test_resolve_passes_release_please_outputs_through(self) -> None:
        with unittest.mock.patch.object(BUILD.subprocess, "run") as run:
            self.assertEqual(
                ("typesafe-jev-v0.9.0", "## raw body\n"),
                BUILD.resolve("", "typesafe-jev-v0.9.0", "## raw body\n"),
            )
            with self.assertRaises(BUILD.ReleaseBuildError):
                BUILD.resolve("", "speckit-pro-v2.35.0", "body")
        run.assert_not_called()

    def test_recovery_rejects_a_malformed_tag_before_calling_gh(self) -> None:
        for tag in ("typesafe-jev-v0.9.0-rc.1", "speckit-pro-v2.35.0", "typesafe-jev-v0.9", "v0.9.0", "typesafe-jev-v0.9.0\n"):
            with self.subTest(tag=tag), unittest.mock.patch.object(BUILD.subprocess, "run") as run:
                with self.assertRaisesRegex(BUILD.ReleaseBuildError, "not typesafe-jev-vX.Y.Z"):
                    BUILD.resolve(tag, "", "")
                run.assert_not_called()

    def test_recovery_reads_the_draft_body_from_the_api(self) -> None:
        view = '{"isDraft": true, "tagName": "typesafe-jev-v0.9.0", "body": "## [0.9.0](compare)\\n"}'
        with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"], stdout=view)) as run:
            self.assertEqual(
                ("typesafe-jev-v0.9.0", "## [0.9.0](compare)\n"),
                BUILD.resolve("typesafe-jev-v0.9.0", "", ""),
            )
        self.assertEqual(
            ["gh", "release", "view", "typesafe-jev-v0.9.0", "--json", "isDraft,tagName,body"],
            run.call_args.args[0],
        )

    def test_recovery_refuses_a_published_missing_or_mismatched_release(self) -> None:
        cases = (
            ('{"isDraft": false, "tagName": "typesafe-jev-v0.9.0", "body": "b"}', 0, "not a draft"),
            ('{"isDraft": true, "tagName": "typesafe-jev-v0.8.0", "body": "b"}', 0, "did not return"),
            ('{"isDraft": true, "tagName": "typesafe-jev-v0.9.0", "body": ""}', 0, "has no body"),
            ("not json", 0, "invalid JSON"),
            ("", 1, "gh release view failed"),
        )
        for stdout, returncode, message in cases:
            result = completed(["gh"], returncode=returncode, stdout=stdout)
            with self.subTest(message=message), unittest.mock.patch.object(BUILD.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(BUILD.ReleaseBuildError, message):
                    BUILD.resolve("typesafe-jev-v0.9.0", "", "")

    def test_published_release_notes_can_be_recovered_without_rebuilding_assets(self) -> None:
        body = "## [0.10.0](compare)\n"
        view = json.dumps({"isDraft": False, "tagName": "typesafe-jev-v0.10.0", "body": body})
        with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"], stdout=view)) as run:
            self.assertEqual(
                ("typesafe-jev-v0.10.0", body),
                BUILD.resolve("typesafe-jev-v0.10.0", "", "", notes_only=True),
            )
        self.assertEqual("view", run.call_args.args[0][2])
        self.assertEqual(1, run.call_count)

    def test_notes_recovery_requires_a_published_uncomposed_release(self) -> None:
        for is_draft, body in ((True, "raw"), (False, "## Highlights\n\ncomposed"), (False, "")):
            with self.subTest(is_draft=is_draft, body=body):
                view = json.dumps({"isDraft": is_draft, "tagName": "typesafe-jev-v0.10.0", "body": body})
                with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"], stdout=view)):
                    with self.assertRaises(BUILD.ReleaseBuildError):
                        BUILD.resolve("typesafe-jev-v0.10.0", "", "", notes_only=True)

    def test_github_output_keeps_a_multiline_body_intact(self) -> None:
        body = "## [0.9.0](compare)\n\n### Features\n\n* one\nname=value\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "output"
            BUILD.write_github_output(path, {"tag_name": "typesafe-jev-v0.9.0", "body": body})
            lines = path.read_text(encoding="utf-8").split("\n")
        parsed: dict[str, str] = {}
        index = 0
        while index < len(lines) and lines[index]:
            name, delimiter = lines[index].split("<<", 1)
            end = lines.index(delimiter, index + 1)
            parsed[name] = "\n".join(lines[index + 1:end])
            index = end + 1
        self.assertEqual({"tag_name": "typesafe-jev-v0.9.0", "body": body}, parsed)

    def test_publish_never_marks_the_release_latest(self) -> None:
        with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"])) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                BUILD.publish("typesafe-jev-v0.9.0")
        argv = run.call_args.args[0]
        self.assertEqual(["gh", "release", "edit", "typesafe-jev-v0.9.0", "--draft=false", "--latest=false"], argv)

    def test_upload_attaches_the_provenance_bundle_and_requires_it(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            out_dir = Path(scratch) / "out"
            out_dir.mkdir()
            archives = {BUILD.asset_name(goos, goarch): goarch.encode() for goos, goarch in BUILD.RELEASE_TARGETS}
            for name, data in archives.items():
                (out_dir / name).write_bytes(data)
            sums = BUILD.sums_text(archives)
            (out_dir / BUILD.SUMS_NAME).write_text(sums, encoding="utf-8")
            bundle = Path(scratch) / "attestation.json"
            bundle.write_text('{"bundle": 1}', encoding="utf-8")

            with unittest.mock.patch.object(BUILD.subprocess, "run") as run:
                with self.assertRaisesRegex(BUILD.ReleaseBuildError, "PROVENANCE_BUNDLE"):
                    BUILD.upload("typesafe-jev-v0.9.0", out_dir, "")
                run.assert_not_called()

            with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"])) as run:
                with contextlib.redirect_stdout(io.StringIO()):
                    BUILD.upload("typesafe-jev-v0.9.0", out_dir, str(bundle))
            argv = run.call_args.args[0]
            self.assertEqual(["gh", "release", "upload", "typesafe-jev-v0.9.0"], argv[:4])
            self.assertEqual("--clobber", argv[-1])
            uploaded = [Path(arg).name for arg in argv[4:-1]]
            self.assertEqual(
                [BUILD.asset_name(goos, goarch) for goos, goarch in BUILD.RELEASE_TARGETS] + [BUILD.SUMS_NAME, BUILD.PROVENANCE_NAME],
                uploaded,
            )
            self.assertEqual('{"bundle": 1}', (out_dir / BUILD.PROVENANCE_NAME).read_text(encoding="utf-8"))
            # The checksums cover only the archives, never the bundle.
            self.assertEqual(sums, (out_dir / BUILD.SUMS_NAME).read_text(encoding="utf-8"))
            self.assertEqual(sorted(archives), sorted(BUILD.parse_sums(sums)))

    def test_provenance_verifies_every_archive_against_the_repository(self) -> None:
        names = [BUILD.asset_name(goos, goarch) for goos, goarch in BUILD.RELEASE_TARGETS]
        directory = Path("downloaded")
        with unittest.mock.patch.object(BUILD.subprocess, "run") as run:
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, "GITHUB_REPOSITORY"):
                BUILD.verify_provenance(directory, names, "")
            run.assert_not_called()

        with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"])) as run:
            BUILD.verify_provenance(directory, names, "racecraft-lab/racecraft-plugins-public")
        self.assertEqual(
            [
                ["gh", "attestation", "verify", str(directory / name), "--bundle", str(directory / BUILD.PROVENANCE_NAME), "--repo", "racecraft-lab/racecraft-plugins-public"]
                for name in names
            ],
            [call.args[0] for call in run.call_args_list],
        )

        with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"], returncode=1)):
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, "gh attestation verify"):
                BUILD.verify_provenance(directory, names, "racecraft-lab/racecraft-plugins-public")

    def test_binary_checks_require_the_version_and_the_unconfigured_exit(self) -> None:
        BUILD.require_version(completed(["evaluate"], stdout="0.9.0\n"), "0.9.0")
        with self.assertRaises(BUILD.ReleaseBuildError):
            BUILD.require_version(completed(["evaluate"], stdout="dev\n"), "0.9.0")
        BUILD.require_unconfigured(completed(["evaluate"], returncode=3))
        for code in (0, 1, 4):
            with self.subTest(code=code), self.assertRaises(BUILD.ReleaseBuildError):
                BUILD.require_unconfigured(completed(["evaluate"], returncode=code))

    def test_binary_runners_name_their_fixed_paths(self) -> None:
        # The runners spell each path out so the Bash-confinement guard can
        # resolve the executable. The spelling must stay the constant's.
        source = (REPO_ROOT / "scripts" / "build-typesafe-jev-release.py").read_text(encoding="utf-8")
        self.assertIn(f'argv = ["{BUILD.VERIFY_BINARY}"]', source)
        self.assertIn(f'argv = ["{BUILD.SMOKE_BINARY}"]', source)


class _LauncherFixture(unittest.TestCase):
    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.home = Path(scratch.name)
        self.destination = self.home / ".local/libexec/racecraft-jev/evaluate"
        self.version = INSTALLER.plugin_version()
        self.payload = self.binary_script(self.version)
        archive = BUILD.archive_bytes(self.payload, b"licence")
        asset = BUILD.asset_name(*INSTALLER.target())
        sums = BUILD.sums_text({asset: archive}).encode()
        self.fetch = self.enterContext(unittest.mock.patch.object(INSTALLER, "fetch", side_effect=[sums, archive]))
        self.enterContext(unittest.mock.patch.dict(os.environ, {"HOME": str(self.home), "PATH": os.defpath}, clear=True))

    def binary_script(self, version: str) -> bytes:
        return (
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            f"version = {version!r}\n"
            "if sys.argv[1:] == ['--version']:\n"
            "    print(version)\n"
            "else:\n"
            "    assert sys.argv[1:] == ['mcp', '--plugin-defaults']\n"
            "    for line in sys.stdin:\n"
            "        request = json.loads(line)\n"
            "        print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': "
            "{'binary': version, 'plugin': os.environ['EVALUATE_PLUGIN_VERSION']}}), flush=True)\n"
        ).encode()

    def put_binary(self, payload: bytes) -> None:
        INSTALLER.install(payload, self.destination, force=True)

    def launch(self, *, expect_exec: bool = True) -> tuple[str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        requests = io.TextIOWrapper(io.BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"initialize"}\n'))
        with (
            contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr),
            unittest.mock.patch.object(sys, "stdin", requests),
            unittest.mock.patch.object(os, "execv", side_effect=SystemExit(0)) as execute,
        ):
            if expect_exec:
                with self.assertRaises(SystemExit) as result:
                    LAUNCHER.main()
                self.assertEqual(0, result.exception.code)
                execute.assert_called_once_with(str(self.destination), [str(self.destination), "mcp", "--plugin-defaults"])
                self.assertEqual(self.version, os.environ["EVALUATE_PLUGIN_VERSION"])
                self.assertEqual("", stdout.getvalue())
            else:
                self.assertEqual(0, LAUNCHER.main())
                execute.assert_not_called()
                self.assertEqual(1, len(stdout.getvalue().splitlines()))
                self.assertIn("instructions", json.loads(stdout.getvalue())["result"])
        self.assertEqual([], list(self.destination.parent.glob(".evaluate-install-*")))
        return stdout.getvalue(), stderr.getvalue()


class TypesafeJevLauncherVersionTests(_LauncherFixture):
    def test_stale_missing_newer_and_unreadable_binaries_install_the_plugin_release(self) -> None:
        for initial in (None, "0.1.0", "99.0.0", "dev", "broken"):
            with self.subTest(initial=initial):
                if self.destination.exists():
                    self.destination.unlink()
                if initial is not None:
                    self.put_binary(b"not an executable" if initial == "broken" else self.binary_script(initial))
                self.fetch.reset_mock(side_effect=True)
                archive = BUILD.archive_bytes(self.payload, b"licence")
                asset = BUILD.asset_name(*INSTALLER.target())
                self.fetch.side_effect = [BUILD.sums_text({asset: archive}).encode(), archive]
                stdout, stderr = self.launch()
                self.assertEqual(self.payload, self.destination.read_bytes())
                self.assertEqual("", stdout + stderr)
                self.assertEqual([
                    unittest.mock.call(f"{INSTALLER.RELEASES}/{INSTALLER.TAG_PREFIX}{self.version}/{INSTALLER.SUMS_NAME}", INSTALLER.MAX_SUMS_BYTES),
                    unittest.mock.call(f"{INSTALLER.RELEASES}/{INSTALLER.TAG_PREFIX}{self.version}/{asset}", INSTALLER.MAX_ARCHIVE_BYTES),
                ], self.fetch.call_args_list)

    def test_matching_binary_does_not_download(self) -> None:
        self.put_binary(self.payload)
        self.launch()
        self.fetch.assert_not_called()

    def test_version_probe_failure_and_timeout_trigger_install(self) -> None:
        self.put_binary(self.payload)
        for failure in (OSError("cannot execute"), subprocess.TimeoutExpired(["evaluate", "--version"], 3),
                        subprocess.CompletedProcess([], 1, b"wrong", b"")):
            with self.subTest(failure=failure), unittest.mock.patch.object(subprocess, "run") as probe:
                if isinstance(failure, Exception):
                    probe.side_effect = failure
                else:
                    probe.return_value = failure
                self.fetch.reset_mock()
                archive = BUILD.archive_bytes(self.payload, b"licence")
                self.fetch.side_effect = [BUILD.sums_text({BUILD.asset_name(*INSTALLER.target()): archive}).encode(), archive]
                self.launch()
                self.assertEqual(2, self.fetch.call_count)
                self.assertLessEqual(probe.call_args.kwargs["timeout"], 3)
                self.assertIs(probe.call_args.kwargs["stdin"], subprocess.DEVNULL)
                self.assertEqual(["./evaluate", "--version"], probe.call_args.args[0])
                self.assertEqual(str(self.destination.parent), probe.call_args.kwargs["cwd"])
                self.assertIs(probe.call_args.kwargs["shell"], False)


class TypesafeJevLauncherSettingsTests(_LauncherFixture):
    def test_operator_binary_and_disabled_or_invalid_settings_do_not_download(self) -> None:
        self.put_binary(self.binary_script("0.1.0"))
        for setting in ({"EVALUATE_BIN": str(self.destination)}, {"EVALUATE_BIN": ""},
                        {"EVALUATE_AUTO_INSTALL": "false"}, {"EVALUATE_AUTO_INSTALL": "0"},
                        {"EVALUATE_AUTO_INSTALL": "invalid\nsetting"}, {"EVALUATE_AUTO_INSTALL": ""}):
            with self.subTest(setting=setting), unittest.mock.patch.dict(os.environ, setting):
                _, stderr = self.launch()
                invalid = "EVALUATE_AUTO_INSTALL" in setting and setting["EVALUATE_AUTO_INSTALL"] not in ("false", "0")
                self.assertEqual(int(invalid), len(stderr.splitlines()))
                if invalid:
                    self.assertIn(repr(setting["EVALUATE_AUTO_INSTALL"]), stderr)
                self.fetch.assert_not_called()

    def test_explicit_enabled_settings_install(self) -> None:
        for setting in ("true", "1"):
            with self.subTest(setting=setting), unittest.mock.patch.dict(os.environ, {"EVALUATE_AUTO_INSTALL": setting}):
                if self.destination.exists():
                    self.destination.unlink()
                archive = BUILD.archive_bytes(self.payload, b"licence")
                asset = BUILD.asset_name(*INSTALLER.target())
                self.fetch.side_effect = [BUILD.sums_text({asset: archive}).encode(), archive]
                self.launch()
                self.assertEqual(self.payload, self.destination.read_bytes())


class TypesafeJevLauncherResilienceTests(_LauncherFixture):
    def test_unexpected_download_or_disk_errors_fall_back_with_one_typed_diagnostic(self) -> None:
        for existing in (True, False):
            for owner, operation in ((INSTALLER, "release_binary"), (INSTALLER, "install")):
                with self.subTest(existing=existing, operation=operation):
                    if self.destination.exists():
                        self.destination.unlink()
                    old = self.binary_script("0.1.0")
                    if existing:
                        self.put_binary(old)
                    archive = BUILD.archive_bytes(self.payload, b"licence")
                    self.fetch.side_effect = [BUILD.sums_text({BUILD.asset_name(*INSTALLER.target()): archive}).encode(), archive]
                    with unittest.mock.patch.object(owner, operation, side_effect=RuntimeError("unexpected\nfixture failure")):
                        _, stderr = self.launch(expect_exec=existing)
                    self.assertEqual(1, len(stderr.splitlines()))
                    self.assertIn("RuntimeError: unexpected fixture failure", stderr)
                    self.assertEqual(old if existing else None,
                                     self.destination.read_bytes() if self.destination.exists() else None)

    def test_blocked_download_returns_by_deadline_and_cannot_install_afterwards(self) -> None:
        from concurrent.futures import ThreadPoolExecutor
        for existing in (True, False):
            with self.subTest(existing=existing):
                if self.destination.exists():
                    self.destination.unlink()
                old = self.binary_script("0.1.0")
                if existing:
                    self.put_binary(old)
                entered, release = threading.Event(), threading.Event()
                workers = []
                archive = BUILD.archive_bytes(self.payload, b"licence")
                sums = BUILD.sums_text({BUILD.asset_name(*INSTALLER.target()): archive}).encode()

                def blocked_fetch(url, _limit):
                    workers.append(threading.current_thread())
                    entered.set()
                    self.assertTrue(release.wait(timeout=3))
                    return sums if url.endswith(INSTALLER.SUMS_NAME) else archive

                self.fetch.side_effect = blocked_fetch
                with (unittest.mock.patch.object(LAUNCHER, "INSTALL_TIMEOUT_SECONDS", 0.05),
                      ThreadPoolExecutor(max_workers=1) as pool):
                    started = time.monotonic()
                    pending = pool.submit(self.launch, expect_exec=existing)
                    try:
                        stdout, stderr = pending.result(timeout=0.7)
                        self.assertLess(time.monotonic() - started, 0.7)
                        self.assertTrue(entered.is_set())
                        self.assertIn("timed out", stderr)
                        self.assertEqual(1, len(stderr.splitlines()))
                        if not existing:
                            self.assertIn("timed out", json.loads(stdout)["result"]["instructions"])
                        self.assertTrue(workers[0].daemon)
                    finally:
                        release.set()
                        for worker in set(workers):
                            worker.join(timeout=2)
                    self.assertEqual(old if existing else None,
                                     self.destination.read_bytes() if self.destination.exists() else None)
                    self.assertEqual([], list(self.destination.parent.glob(".evaluate-install-*")))


class TypesafeJevLauncherFailureTests(_LauncherFixture):
    def assert_install_failure(self, existing: bool, failure: str) -> None:
        if self.destination.exists():
            self.destination.unlink()
        old = self.binary_script("0.1.0")
        if existing:
            self.put_binary(old)
        self.fetch.side_effect = INSTALLER.InstallError("cannot download fixture") if failure == "download" else [b"0" * 64 + b"  " + BUILD.asset_name(*INSTALLER.target()).encode(), b"bad archive"]
        stdout, stderr = self.launch(expect_exec=existing)
        self.assertEqual(1, len(stderr.splitlines()))
        self.assertIn("cannot download" if failure == "download" else "checksum mismatch", stderr)
        if existing:
            self.assertEqual(old, self.destination.read_bytes())
        else:
            self.assertFalse(self.destination.exists())
            self.assertIn("auto-install", json.loads(stdout)["result"]["instructions"])


    def test_download_failure_or_bad_checksum_preserves_old_binary_or_serves_standin(self) -> None:
        for existing, failure in ((True, "download"), (False, "download"), (True, "checksum"), (False, "checksum")):
            with self.subTest(existing=existing, failure=failure):
                self.assert_install_failure(existing, failure)

    def test_whole_install_deadline_interrupts_download_and_cleans_up_timer(self) -> None:
        for existing in (True, False):
            with self.subTest(existing=existing):
                if self.destination.exists():
                    self.destination.unlink()
                if existing:
                    self.put_binary(self.binary_script("0.1.0"))
                self.fetch.side_effect = lambda *args: time.sleep(1)
                before = signal.getsignal(signal.SIGALRM)
                started = time.monotonic()
                with unittest.mock.patch.object(LAUNCHER, "INSTALL_TIMEOUT_SECONDS", 0.05):
                    stdout, stderr = self.launch(expect_exec=existing)
                self.assertLess(time.monotonic() - started, 0.8)
                self.assertIn("timed out", stderr)
                self.assertEqual(1, len(stderr.splitlines()))
                self.assertEqual(before, signal.getsignal(signal.SIGALRM))
                self.assertEqual(0, signal.getitimer(signal.ITIMER_REAL)[0])
                if not existing:
                    self.assertIn("timed out", json.loads(stdout)["result"]["instructions"])


class TypesafeJevLauncherAtomicFailureTests(_LauncherFixture):
    def test_only_the_caller_writes_after_download_and_verification_complete(self) -> None:
        caller = threading.current_thread()
        writes = []
        install = INSTALLER.install

        def record_write(*args, **kwargs):
            self.assertEqual(2, self.fetch.call_count)
            writes.append(threading.current_thread())
            return install(*args, **kwargs)

        with unittest.mock.patch.object(INSTALLER, "install", side_effect=record_write):
            self.launch()
        self.assertEqual([caller], writes)
        self.assertEqual(self.payload, self.destination.read_bytes())

    def test_failed_atomic_replace_keeps_old_binary_and_removes_stage(self) -> None:
        old = self.binary_script("0.1.0")
        self.put_binary(old)
        with unittest.mock.patch.object(os, "replace", side_effect=OSError("fixture rename failed")):
            _, stderr = self.launch()
        self.assertIn("fixture rename failed", stderr)
        self.assertEqual(1, len(stderr.splitlines()))
        self.assertEqual(old, self.destination.read_bytes())

    def test_timeout_during_staging_removes_partial_stage(self) -> None:
        self.put_binary(self.binary_script("0.1.0"))
        old = self.destination.read_bytes()
        with (unittest.mock.patch.object(LAUNCHER, "INSTALL_TIMEOUT_SECONDS", 0.05),
              unittest.mock.patch.object(os, "chmod", side_effect=lambda *args: time.sleep(1))):
            _, stderr = self.launch()
        self.assertIn("timed out", stderr)
        self.assertEqual(old, self.destination.read_bytes())


class TypesafeJevLauncherHttpFailureTests(_LauncherFixture):
    def test_real_fetch_http_errors_exec_old_binary_or_serve_standin_with_only_mcp_stdout(self) -> None:
        for error_type, response in MALFORMED_HTTP.items():
            for existing in (True, False):
                with self.subTest(error_type=error_type, existing=existing), malformed_release_host(response) as base:
                    if self.destination.exists():
                        self.destination.unlink()
                    old = self.binary_script("0.1.0")
                    if existing:
                        self.put_binary(old)
                    script = (
                        f"import sys; sys.path.insert(0, {str(PLUGIN_SCRIPTS)!r}); "
                        "import evaluate_launch, install_evaluate; "
                        f"install_evaluate.RELEASES = {base!r}; "
                        "raise SystemExit(evaluate_launch.main())"
                    )
                    result = subprocess.run([sys.executable, "-I", "-c", script],
                                            input='{"jsonrpc":"2.0","id":7,"method":"initialize"}\n',
                                            text=True, capture_output=True, timeout=5, check=False)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(1, len(result.stderr.splitlines()), result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    frames = [json.loads(line) for line in result.stdout.splitlines()]
                    self.assertEqual(1, len(frames))
                    self.assertEqual("2.0", frames[0]["jsonrpc"])
                    self.assertEqual(7, frames[0]["id"])
                    if existing:
                        self.assertEqual({"binary": "0.1.0", "plugin": self.version}, frames[0]["result"])
                        self.assertEqual(old, self.destination.read_bytes())
                    else:
                        self.assertIn("auto-install failed", frames[0]["result"]["instructions"])
                        self.assertFalse(self.destination.exists())
                    self.assertEqual([], list(self.destination.parent.glob(".evaluate-install-*")))


class TypesafeJevLauncherProtocolTests(_LauncherFixture):
    def test_installed_binary_exec_writes_only_mcp_frames(self) -> None:
        archive = BUILD.archive_bytes(self.payload, b"licence")
        asset = BUILD.asset_name(*INSTALLER.target())
        script = (
            "import sys; from unittest.mock import patch; "
            f"sys.path.insert(0, {str(REPO_ROOT / 'typesafe-jev/plugin/scripts')!r}); "
            "import evaluate_launch, install_evaluate; "
            f"fetch = patch.object(install_evaluate, 'fetch', side_effect={[BUILD.sums_text({asset: archive}).encode(), archive]!r}); "
            "fetch.start(); raise SystemExit(evaluate_launch.main())"
        )
        result = subprocess.run([sys.executable, "-c", script], input='{"jsonrpc":"2.0","id":7,"method":"initialize"}\n',
                                text=True, capture_output=True, timeout=5, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertEqual([{"jsonrpc": "2.0", "id": 7, "result": {"binary": self.version, "plugin": self.version}}],
                         [json.loads(line) for line in result.stdout.splitlines()])


class TypesafeJevInstallerHttpFailureTests(unittest.TestCase):
    def test_real_fetch_http_errors_become_install_errors_and_clean_cli_failures(self) -> None:
        for error_type, response in MALFORMED_HTTP.items():
            with self.subTest(error_type=error_type), malformed_release_host(response) as base:
                with self.subTest(entry="fetch"):
                    with self.assertRaises(INSTALLER.InstallError) as failure:
                        REAL_FETCH(base, INSTALLER.MAX_SUMS_BYTES)
                    self.assertEqual(error_type, type(failure.exception.__cause__).__name__)
                with self.subTest(entry="cli"), tempfile.TemporaryDirectory() as scratch:
                    destination = Path(scratch) / "evaluate"
                    result = subprocess.run(
                        [sys.executable, "-I", str(PLUGIN_SCRIPTS / "install_evaluate.py"),
                         "--base-url", base, "--version", "0.9.0", "--dest", str(destination)],
                        env={"PATH": os.defpath, "HOME": scratch}, text=True, capture_output=True, timeout=5, check=False,
                    )
                    self.assertEqual(1, result.returncode)
                    self.assertIn("install_evaluate: cannot download", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(destination.exists())
                    self.assertEqual([], list(destination.parent.glob(".evaluate-install-*")))

    def test_manual_installer_does_not_hide_unexpected_errors(self) -> None:
        with (tempfile.TemporaryDirectory() as scratch,
              unittest.mock.patch.object(INSTALLER, "release_binary", side_effect=RuntimeError("fixture bug")),
              contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, "fixture bug")):
            INSTALLER.main(["--version", "0.9.0", "--dest", str(Path(scratch) / "evaluate")])


class TypesafeJevInstallerTests(unittest.TestCase):
    def test_concurrent_installs_use_unique_stages_and_preserve_a_complete_winner(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            destination = Path(scratch) / "evaluate"
            barrier = threading.Barrier(2)
            replace = os.replace
            stages = []

            def racing_replace(source, target):
                stages.append(source)
                barrier.wait(timeout=5)
                replace(source, target)

            with unittest.mock.patch.object(os, "replace", side_effect=racing_replace):
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [pool.submit(INSTALLER.install, payload, destination, True) for payload in (b"first" * 1000, b"second" * 1000)]
                    for future in futures:
                        future.result(timeout=5)
            self.assertEqual(2, len(set(stages)))
            self.assertTrue(all(Path(stage).parent == destination.parent for stage in stages))
            self.assertIn(destination.read_bytes(), (b"first" * 1000, b"second" * 1000))
            self.assertEqual([], list(destination.parent.glob(".evaluate-install-*")))

    def test_installer_hint_names_key_files_and_keyless_ollama_app(self) -> None:
        archive = BUILD.archive_bytes(b"binary", b"licence")
        asset = BUILD.asset_name("linux", "amd64")
        sums = BUILD.sums_text({asset: archive}).encode("utf-8")
        output = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as scratch,
            unittest.mock.patch.object(INSTALLER, "target", return_value=("linux", "amd64")),
            unittest.mock.patch.object(INSTALLER, "fetch", side_effect=[sums, archive]),
            contextlib.redirect_stdout(output),
        ):
            destination = Path(scratch) / "evaluate"
            self.assertEqual(0, INSTALLER.main(["--version", "0.9.0", "--dest", str(destination)]))
            self.assertEqual(b"binary", destination.read_bytes())
        hint = output.getvalue().splitlines()[-1]
        self.assertEqual(
            "Next: put any keys your chain needs in ~/.config/racecraft-jev/ "
            "(typesafe.key, openrouter.key, or ollama.key; chmod 600). "
            "The signed-in Ollama app (ollama-local) needs no key file. "
            "Then reconnect the jev MCP server.",
            hint,
        )
        self.assertNotIn("ollama-local.key", output.getvalue())
        self.assertIn("The signed-in Ollama app (ollama-local) needs no key file.", hint)


def build_suite() -> unittest.TestSuite:
    return unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (TypesafeJevReleaseBuildTests, TypesafeJevInstallerTests, TypesafeJevLauncherVersionTests,
                     TypesafeJevLauncherSettingsTests, TypesafeJevLauncherFailureTests, TypesafeJevLauncherProtocolTests,
                     TypesafeJevLauncherAtomicFailureTests, TypesafeJevLauncherResilienceTests,
                     TypesafeJevLauncherHttpFailureTests, TypesafeJevInstallerHttpFailureTests)
    )


def main() -> int:
    return run_counted(build_suite(), label="test-typesafe-jev-release-build")


if __name__ == "__main__":
    raise SystemExit(main())

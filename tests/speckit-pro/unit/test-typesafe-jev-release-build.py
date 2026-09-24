#!/usr/bin/env python3
"""Layer 4 tests for the typesafe-jev release build script.

The archives and checksums the script writes are read by two consumers that
ship in the plugin: install_evaluate.py and `evaluate update`. These tests
check the script's output against the installer's own parser, and check that
the version stamped into the binary is the bare version those consumers
compare, never the tag.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import subprocess
import sys
import tarfile
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def load_module(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


BUILD = load_module("build_typesafe_jev_release", REPO_ROOT / "scripts" / "build-typesafe-jev-release.py")
INSTALLER = load_module(
    "install_evaluate", REPO_ROOT / "typesafe-jev" / "plugin" / "scripts" / "install_evaluate.py"
)
GO_CHECK = load_module("check_go_module", REPO_ROOT / "scripts" / "check-go-module.py")


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
            self.assertEqual(set(archives), set(BUILD.check_assets(directory)))

            (directory / BUILD.asset_name("linux", "arm64")).write_bytes(b"tampered")
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, "does not match"):
                BUILD.check_assets(directory)

            (directory / BUILD.asset_name("linux", "arm64")).unlink()
            with self.assertRaisesRegex(BUILD.ReleaseBuildError, "has no"):
                BUILD.check_assets(directory)

    def test_publish_never_marks_the_release_latest(self) -> None:
        with unittest.mock.patch.object(BUILD.subprocess, "run", return_value=completed(["gh"])) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                BUILD.publish("typesafe-jev-v0.9.0")
        argv = run.call_args.args[0]
        self.assertEqual(["gh", "release", "edit", "typesafe-jev-v0.9.0", "--draft=false", "--latest=false"], argv)

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


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(TypesafeJevReleaseBuildTests)


def main() -> int:
    return run_counted(build_suite(), label="test-typesafe-jev-release-build")


if __name__ == "__main__":
    raise SystemExit(main())

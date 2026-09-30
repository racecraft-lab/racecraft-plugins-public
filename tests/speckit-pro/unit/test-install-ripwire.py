#!/usr/bin/env python3
"""Focused Layer 4 tests for the pinned ripwire installer and advisory report.

No test touches the network: every download goes through a fake opener, and
every ripwire or git call goes through a mocked subprocess.
"""

from __future__ import annotations

import hashlib
import io
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402
from script_loader import load_script as load_module_from_path  # noqa: E402

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ripwire-advisory.yml"
PR_CHECKS = REPO_ROOT / ".github" / "workflows" / "pr-checks.yml"


def load_script(module_name: str, script_name: str) -> ModuleType:
    return load_module_from_path(module_name, REPO_ROOT / "scripts" / script_name)


RIPWIRE = load_script("install_ripwire_under_test", "install-ripwire.py")


def make_archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            member.mode = 0o755
            archive.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


def fake_release(arch: str = "x64") -> bytes:
    prefix = f"ripwire-{RIPWIRE.RIPWIRE_VERSION}-linux-{arch}"
    return make_archive(
        {
            f"{prefix}/LICENSE": b"license\n",
            f"{prefix}/ripwire": b"fake-ripwire-binary\n",
            f"{prefix}/README.md": b"readme\n",
        }
    )


class PinTests(unittest.TestCase):
    def test_pins_one_exact_version_with_a_digest_per_linux_architecture(self) -> None:
        self.assertEqual("0.6.5", RIPWIRE.RIPWIRE_VERSION)
        self.assertEqual(
            {
                "x64": "5c5794612f5f06632ada7c27a0f5c8f400748a70f707b64ec4d238c4fba2f7ea",
                "arm64": "25e5f37e2985830bbff189879797988b862e36521413a6e3654630a0e1f0b108",
            },
            RIPWIRE.RIPWIRE_SHA256,
        )

    def test_architecture_maps_linux_machines_and_fails_closed_elsewhere(self) -> None:
        self.assertEqual("x64", RIPWIRE.linux_architecture("Linux", "x86_64"))
        self.assertEqual("arm64", RIPWIRE.linux_architecture("Linux", "aarch64"))
        for system, machine in (("Darwin", "arm64"), ("Linux", "riscv64"), ("Windows", "AMD64")):
            with self.subTest(system=system, machine=machine):
                with self.assertRaisesRegex(RIPWIRE.RipwireError, "no pinned ripwire release"):
                    RIPWIRE.linux_architecture(system, machine)


class InstallTests(unittest.TestCase):
    def test_correct_pin_installs_the_verified_binary(self) -> None:
        archive_bytes = fake_release("arm64")
        observed: dict[str, object] = {}

        def opener(request: object, *, timeout: int) -> io.BytesIO:
            observed["url"] = request.full_url  # type: ignore[attr-defined]
            observed["timeout"] = timeout
            return io.BytesIO(archive_bytes)

        with tempfile.TemporaryDirectory() as temporary_directory:
            install_directory = Path(temporary_directory)
            installed = RIPWIRE.install_ripwire(
                install_directory,
                "arm64",
                sha256_by_arch={"arm64": hashlib.sha256(archive_bytes).hexdigest()},
                opener=opener,
            )
            self.assertEqual(install_directory / "ripwire", installed)
            self.assertEqual(b"fake-ripwire-binary\n", installed.read_bytes())
            self.assertEqual(0o755, stat.S_IMODE(installed.stat().st_mode))
            self.assertEqual(["ripwire"], sorted(p.name for p in install_directory.iterdir()))

        self.assertEqual(
            "https://github.com/redhat-et/ripwire/releases/download/"
            "v0.6.5/ripwire-0.6.5-linux-arm64.tar.gz",
            observed["url"],
        )
        self.assertEqual(RIPWIRE.DOWNLOAD_TIMEOUT_SECONDS, observed["timeout"])

    def test_checksum_mismatch_fails_before_extraction(self) -> None:
        archive_bytes = fake_release("x64")
        with tempfile.TemporaryDirectory() as temporary_directory:
            install_directory = Path(temporary_directory)
            with self.assertRaisesRegex(RIPWIRE.RipwireError, "checksum mismatch"):
                RIPWIRE.install_ripwire(
                    install_directory,
                    "x64",
                    opener=lambda *_args, **_kwargs: io.BytesIO(archive_bytes),
                )
            self.assertFalse((install_directory / "ripwire").exists())

    def test_architecture_without_a_pin_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            opener = mock.Mock()
            with self.assertRaisesRegex(RIPWIRE.RipwireError, "no pinned ripwire release"):
                RIPWIRE.install_ripwire(Path(temporary_directory), "riscv64", opener=opener)
            opener.assert_not_called()

    def test_archive_without_the_versioned_binary_is_rejected(self) -> None:
        archive_bytes = make_archive({"ripwire": b"top-level-binary\n"})
        with tempfile.TemporaryDirectory() as temporary_directory:
            install_directory = Path(temporary_directory)
            with self.assertRaisesRegex(RIPWIRE.RipwireError, "exactly one"):
                RIPWIRE.install_ripwire(
                    install_directory,
                    "x64",
                    sha256_by_arch={"x64": hashlib.sha256(archive_bytes).hexdigest()},
                    opener=lambda *_args, **_kwargs: io.BytesIO(archive_bytes),
                )
            self.assertFalse((install_directory / "ripwire").exists())


ARCH_OUTPUT = (
    "ripwire arch: 2 violation(s) total — 1 suppressed (baseline) — 1 new\n"
    '<!-- legend with <tags> and "quotes" --><arch schema="ripwire.arch/v1" '
    'violations="2" baselined="1" new_violations="1"><v from="a.py" to="b.py"/></arch>\n'
)
QUALITY_OUTPUT = (
    '<quality-delta schema="ripwire.quality-delta/v1" regressions="0" minor="0" '
    'preexisting-worse="0" new-symbol="0" gating="0"></quality-delta>\n'
)
DRIFT_OUTPUT = '<doc-drift schema="ripwire.doc-drift/v1" docs="9" clean="9" checked="40" drift="0"></doc-drift>\n'


def completed(argv: list[str], returncode: int, stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout, "")


class ReportTests(unittest.TestCase):
    def fake_binary(self, root: Path) -> Path:
        binary = root / "ripwire"
        binary.write_bytes(b"fake\n")
        binary.chmod(0o755)
        return binary

    def fake_run(self, arch_code: int = 2) -> mock.Mock:
        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            self.assertIs(kwargs.get("shell"), False)
            self.assertIs(kwargs.get("check"), False)
            if argv[:2] == ["git", "merge-base"]:
                return completed(argv, 0, "abc123\n")
            flag = argv[2]
            if flag.startswith("--arch="):
                return completed(argv, arch_code, ARCH_OUTPUT)
            if flag.startswith("--quality-delta="):
                return completed(argv, 0, QUALITY_OUTPUT)
            return completed(argv, 0, DRIFT_OUTPUT)

        return mock.Mock(side_effect=run)

    def test_findings_are_reported_but_never_fail_the_step(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            runner = self.fake_run(arch_code=2)
            stdout = io.StringIO()
            with mock.patch.object(RIPWIRE.subprocess, "run", runner):
                code, summary = RIPWIRE.build_report(self.fake_binary(root), "base-sha", stdout=stdout)

        self.assertEqual(0, code)
        argvs = [call.args[0] for call in runner.call_args_list]
        self.assertEqual(["git", "merge-base", "base-sha", "HEAD"], argvs[0])
        self.assertEqual(
            [
                ["--arch=.ripwire_arch_rules"],
                ["--quality-delta=abc123..HEAD"],
                ["--doc-drift"],
            ],
            [argv[2:] for argv in argvs[1:]],
        )
        self.assertTrue(all(argv[1] == "." for argv in argvs[1:]))
        self.assertIn("advisory", summary.lower())
        self.assertRegex(summary, r"\| Layering \|.*\| 2 \|.*new_violations=1.*\| findings \|")
        self.assertRegex(summary, r"\| Quality delta \|.*\| 0 \|.*regressions=0.*\| clean \|")
        self.assertRegex(summary, r"\| Doc drift \|.*\| 0 \|.*drift=0.*\| clean \|")
        self.assertIn("&lt;arch schema=", summary)
        self.assertNotIn("<arch schema=", summary)
        self.assertIn("::warning", stdout.getvalue())

    def test_quality_regressions_and_doc_drift_count_as_findings(self) -> None:
        self.assertEqual(
            "findings",
            RIPWIRE.check_status("quality-delta", 0, {"regressions": "3", "gating": "0"}),
        )
        self.assertEqual("findings", RIPWIRE.check_status("doc-drift", 0, {"drift": "2"}))
        self.assertEqual("clean", RIPWIRE.check_status("arch", 0, {"new_violations": "0"}))
        self.assertEqual("error", RIPWIRE.check_status("doc-drift", 1, {}))
        self.assertEqual("error", RIPWIRE.check_status("arch", 0, {}))

    def test_missing_binary_reports_an_error_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with mock.patch.object(RIPWIRE.subprocess, "run") as runner:
                code, summary = RIPWIRE.build_report(
                    Path(temporary_directory) / "ripwire", "base-sha", stdout=io.StringIO()
                )
            runner.assert_not_called()
        self.assertEqual(0, code)
        self.assertIn("not installed", summary)

    def test_merge_base_failure_skips_only_the_quality_delta(self) -> None:
        def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            if argv[:2] == ["git", "merge-base"]:
                return completed(argv, 1, "")
            return completed(argv, 0, DRIFT_OUTPUT if argv[2] == "--doc-drift" else ARCH_OUTPUT)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with mock.patch.object(RIPWIRE.subprocess, "run", mock.Mock(side_effect=run)) as runner:
                code, summary = RIPWIRE.build_report(self.fake_binary(root), "base-sha", stdout=io.StringIO())
        self.assertEqual(0, code)
        flags = [call.args[0][2] for call in runner.call_args_list[1:]]
        self.assertEqual(["--arch=.ripwire_arch_rules", "--doc-drift"], flags)
        self.assertRegex(summary, r"\| Quality delta \|.*merge-base.*\| error \|")

    def test_long_output_is_truncated(self) -> None:
        text = RIPWIRE.output_excerpt("x" * (RIPWIRE.MAX_OUTPUT_CHARS + 50))
        self.assertIn("truncated", text)
        self.assertLess(len(text), RIPWIRE.MAX_OUTPUT_CHARS + 200)


def job_block(content: str, job_id: str) -> str:
    match = re.search(rf"(?ms)^  {re.escape(job_id)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", content)
    return match.group("body") if match else ""


class AdvisoryWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), f"file not found: {WORKFLOW}")
        self.content = WORKFLOW.read_text(encoding="utf-8")
        self.job = job_block(self.content, "ripwire-advisory")

    def test_runs_on_pull_request_with_read_only_token_and_no_secrets(self) -> None:
        self.assertRegex(self.content, r"(?m)^on:\n  pull_request:\n")
        self.assertNotRegex(self.content, r"(?m)^\s*pull_request_target:")
        self.assertRegex(self.content, r"(?m)^permissions: \{\}$")
        self.assertRegex(self.job, r"(?m)^    permissions:\n      contents: read\n(?!      )")
        self.assertNotRegex(self.content, r"\bsecrets\.[A-Za-z_]")
        self.assertNotIn("github.token", self.content)

    def test_checkout_has_history_for_the_merge_base_and_no_credentials(self) -> None:
        self.assertRegex(self.job, r"uses: actions/checkout@[0-9a-f]{40} # v")
        self.assertIn("fetch-depth: 0", self.job)
        self.assertIn("persist-credentials: false", self.job)
        self.assertIn("BASE_SHA: ${{ github.event.pull_request.base.sha }}", self.job)

    def test_install_and_report_are_advisory_python_dispatches(self) -> None:
        self.assertIn("run: python3 scripts/install-ripwire.py install\n", self.job)
        self.assertIn("run: python3 scripts/install-ripwire.py report\n", self.job)
        self.assertEqual(2, self.job.count("continue-on-error: true"))
        self.assertIn("timeout-minutes:", self.job)

    def test_job_stays_out_of_the_required_sentinel(self) -> None:
        pr_checks = PR_CHECKS.read_text(encoding="utf-8")
        self.assertNotIn("ripwire", pr_checks)
        self.assertNotIn("ripwire", (REPO_ROOT / "scripts" / "check-pr-workflow-results.py").read_text(encoding="utf-8"))


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in (PinTests, InstallTests, ReportTests, AdvisoryWorkflowTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-install-ripwire")


if __name__ == "__main__":
    raise SystemExit(main())

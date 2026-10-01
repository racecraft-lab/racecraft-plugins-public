#!/usr/bin/env python3
"""Focused Layer 4 tests for the pinned ripwire installer and advisory report.

No test touches the network: every download goes through a fake opener, and
every ripwire or git call goes through a mocked subprocess.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
import urllib.request
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


class RecordingOpener:
    """Fake urlopen that serves fixed bytes and records each request."""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.urls: list[str] = []
        self.timeouts: list[int] = []

    def __call__(self, request: urllib.request.Request, *, timeout: int) -> io.BytesIO:
        self.urls.append(request.full_url)
        self.timeouts.append(timeout)
        return io.BytesIO(self.payload)


class InstallTests(unittest.TestCase):
    def install(self, payload: bytes, arch: str, pins: dict[str, str] | None = None) -> tuple[Path, RecordingOpener]:
        """Install from a fake release into a fresh directory; pins default to the real ones."""
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        opener = RecordingOpener(payload)
        kwargs = {} if pins is None else {"sha256_by_arch": pins}
        try:
            RIPWIRE.install_ripwire(root, arch, opener=opener, **kwargs)
        finally:
            self.left_behind = sorted(p.name for p in root.iterdir())
        return root / "ripwire", opener

    def test_correct_pin_installs_the_verified_binary(self) -> None:
        payload = fake_release("arm64")
        installed, opener = self.install(payload, "arm64", {"arm64": hashlib.sha256(payload).hexdigest()})
        self.assertEqual(b"fake-ripwire-binary\n", installed.read_bytes())
        self.assertEqual(0o755, stat.S_IMODE(installed.stat().st_mode))
        self.assertEqual(["ripwire"], self.left_behind)
        self.assertEqual(
            ["https://github.com/redhat-et/ripwire/releases/download/v0.6.5/ripwire-0.6.5-linux-arm64.tar.gz"],
            opener.urls,
        )
        self.assertEqual([RIPWIRE.DOWNLOAD_TIMEOUT_SECONDS], opener.timeouts)

    def test_mismatch_unpinned_architecture_or_bad_layout_installs_nothing(self) -> None:
        top_level = make_archive({"ripwire": b"top-level-binary\n"})
        cases = (
            ("checksum mismatch", fake_release("x64"), "x64", None),
            ("no pinned ripwire release", b"unused", "riscv64", None),
            ("exactly one", top_level, "x64", {"x64": hashlib.sha256(top_level).hexdigest()}),
        )
        for pattern, payload, arch, pins in cases:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(RIPWIRE.RipwireError, pattern):
                    self.install(payload, arch, pins)
                self.assertEqual([], self.left_behind)


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
OUTPUT_BY_FLAG = {"--arch": ARCH_OUTPUT, "--quality-delta": QUALITY_OUTPUT, "--doc-drift": DRIFT_OUTPUT}


class FakeSubprocess:
    """Stand in for subprocess.run: git merge-base plus the three ripwire checks."""

    def __init__(self, merge_base_code: int = 0, arch_code: int = 2) -> None:
        self.merge_base_code = merge_base_code
        self.arch_code = arch_code

    def __call__(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if kwargs.get("shell") is not False or kwargs.get("check") is not False:
            raise AssertionError(f"unsafe subprocess call: {kwargs}")
        if argv[:2] == ["git", "merge-base"]:
            return subprocess.CompletedProcess(argv, self.merge_base_code, "abc123\n", "")
        flag = argv[2].split("=", 1)[0]
        code = self.arch_code if flag == "--arch" else 0
        return subprocess.CompletedProcess(argv, code, OUTPUT_BY_FLAG[flag], "")


def fake_subprocess(merge_base_code: int = 0, arch_code: int = 2) -> mock.Mock:
    return mock.Mock(side_effect=FakeSubprocess(merge_base_code, arch_code))


class ReportTests(unittest.TestCase):
    def report(self, runner: mock.Mock, *, installed: bool = True) -> tuple[int, str, str]:
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        binary = root / "ripwire"
        if installed:
            binary.write_bytes(b"fake\n")
            binary.chmod(0o755)
        stdout = io.StringIO()
        with mock.patch.object(RIPWIRE.subprocess, "run", runner):
            code, summary = RIPWIRE.build_report(binary, "base-sha", stdout=stdout)
        return code, summary, stdout.getvalue()

    def test_findings_are_reported_but_never_fail_the_step(self) -> None:
        runner = fake_subprocess(arch_code=2)
        code, summary, annotations = self.report(runner)
        self.assertEqual(0, code)
        argvs = [call.args[0] for call in runner.call_args_list]
        self.assertEqual(["git", "merge-base", "base-sha", "HEAD"], argvs[0])
        self.assertEqual(
            [[".", "--arch=.ripwire_arch_rules"], [".", "--quality-delta=abc123..HEAD"], [".", "--doc-drift"]],
            [argv[1:] for argv in argvs[1:]],
        )
        self.assertEqual(["ripwire"] * 3, [argv[0] for argv in argvs[1:]])
        ripwire_path = runner.call_args_list[1].kwargs["env"]["PATH"].split(os.pathsep, 1)[0]
        self.assertTrue(Path(ripwire_path, "ripwire").is_file())
        self.assertIn("advisory", summary.lower())
        self.assertRegex(summary, r"\| Layering \|.*\| 2 \|.*new_violations=1.*\| findings \|")
        self.assertRegex(summary, r"\| Quality delta \|.*\| 0 \|.*regressions=0.*\| clean \|")
        self.assertRegex(summary, r"\| Doc drift \|.*\| 0 \|.*drift=0.*\| clean \|")
        self.assertIn("&lt;arch schema=", summary)
        self.assertNotIn("<arch schema=", summary)
        self.assertIn("::warning", annotations)

    def test_missing_binary_reports_an_error_without_failing(self) -> None:
        runner = fake_subprocess()
        code, summary, _annotations = self.report(runner, installed=False)
        runner.assert_not_called()
        self.assertEqual(0, code)
        self.assertIn("not installed", summary)

    def test_merge_base_failure_skips_only_the_quality_delta(self) -> None:
        runner = fake_subprocess(merge_base_code=1)
        code, summary, _annotations = self.report(runner)
        self.assertEqual(0, code)
        flags = [call.args[0][2] for call in runner.call_args_list[1:]]
        self.assertEqual(["--arch=.ripwire_arch_rules", "--doc-drift"], flags)
        self.assertRegex(summary, r"\| Quality delta \|.*merge-base.*\| error \|")


class StatusTests(unittest.TestCase):
    def test_quality_regressions_and_doc_drift_count_as_findings(self) -> None:
        self.assertEqual(
            "findings",
            RIPWIRE.check_status("quality-delta", 0, {"regressions": "3", "gating": "0"}),
        )
        self.assertEqual("findings", RIPWIRE.check_status("doc-drift", 0, {"drift": "2"}))
        self.assertEqual("clean", RIPWIRE.check_status("arch", 0, {"new_violations": "0"}))
        self.assertEqual("error", RIPWIRE.check_status("doc-drift", 1, {}))
        self.assertEqual("error", RIPWIRE.check_status("arch", 0, {}))

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
    for test_case in (PinTests, InstallTests, ReportTests, StatusTests, AdvisoryWorkflowTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-install-ripwire")


if __name__ == "__main__":
    raise SystemExit(main())

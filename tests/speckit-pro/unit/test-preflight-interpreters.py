#!/usr/bin/env python3
"""Behavioral tests for the hosted Windows interpreter probes."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
DISPATCHER = REPO_ROOT / "tests" / "speckit-pro" / "run-container-preflight.py"
sys.path.insert(0, str(LIB_DIR))
import preflight_interpreters as interpreters  # noqa: E402
from test_result import run_counted  # noqa: E402


def probe_output(version: tuple[int, int, int], process: str, native: str,
                 executable: str = "C:/Python/python.exe") -> str:
    return json.dumps(
        {
            "major": version[0], "minor": version[1], "micro": version[2],
            "executable": executable, "machine": "ARM64",
            "processor_architecture": process, "processor_architew6432": native,
        },
        separators=(",", ":"),
    )


def result(stdout: str = "", returncode: int = 0, stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def fake_probe_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
    """Answer each launcher command with the interpreter a hosted ARM64 runner might report."""
    outputs = {
        "py -V:3": ((3, 13, 14), "AMD64", "ARM64"),
        "py -3": ((3, 10, 14), "ARM64", "ARM64"),
        "python": ((3, 13, 14), "ARM64", "ARM64"),
    }
    key = " ".join(command[:-2]) if command[0] == "py" else command[0]
    version, process, native = outputs.get(key, ((3, 12, 11), "ARM64", "ARM64"))
    return result(probe_output(version, process, native, f"C:/Python/{command[0]}.exe"))


class ProbeCase(unittest.TestCase):
    def probe(self, run: object, candidate: str = "python",
              expected: str = "arm64") -> tuple[dict[str, object], Path]:
        """Probe one candidate with a launcher on PATH; ``run`` is a result, exception or callable."""
        evidence = Path(self.enterContext(tempfile.TemporaryDirectory())) / "evidence"
        outcome = {"side_effect": run} if callable(run) or isinstance(run, Exception) else {"return_value": run}
        with (
            unittest.mock.patch.object(interpreters.shutil, "which", return_value="C:/Windows/launcher.exe"),
            unittest.mock.patch.object(interpreters.subprocess, "run", **outcome) as run_mock,
        ):
            record = interpreters.probe_interpreter(candidate, expected, evidence, cwd=REPO_ROOT)
        self.run_mock = run_mock
        return record, evidence

    def evidence_file(self, evidence: Path, name: str) -> str:
        return (evidence / name).read_text(encoding="utf-8")


class ProbeRecordTests(ProbeCase):
    def test_candidates_are_ordered_and_each_has_an_evidence_slug(self) -> None:
        self.assertEqual(interpreters.INTERPRETER_CANDIDATES, ("py -V:3", "py -3", "python", "python3"))
        self.assertEqual(len(set(interpreters.INTERPRETER_SLUGS.values())), 4)

    def test_a_missing_launcher_is_recorded_without_running_anything(self) -> None:
        evidence = Path(self.enterContext(tempfile.TemporaryDirectory()))
        with unittest.mock.patch.object(interpreters.shutil, "which", return_value=None), \
                unittest.mock.patch.object(interpreters.subprocess, "run") as run_mock:
            record = interpreters.probe_interpreter("py -3", "x64", evidence, cwd=REPO_ROOT)
        run_mock.assert_not_called()
        self.assertEqual((record["status"], record["exit_code"], record["supported"]), ("missing", 127, False))
        self.assertEqual(self.evidence_file(evidence, "probe-py-3.exit-code.txt"), "127\n")
        self.assertIn("py was not found on PATH", self.evidence_file(evidence, "probe-py-3.stderr.txt"))

    def test_probe_failures_are_classified_and_never_supported(self) -> None:
        cases = (
            ("probe_failed", result("", returncode=2, stderr="boom")),
            ("invalid_probe", result("not json")),
            ("invalid_probe", result("[1, 2]")),
        )
        for status, completed in cases:
            with self.subTest(status=status, stdout=completed.stdout):
                record, _ = self.probe(completed)
                self.assertEqual((record["status"], record["supported"]), (status, False))

    def test_timeouts_and_launch_errors_become_probe_errors(self) -> None:
        for error in (subprocess.TimeoutExpired("python", 120), OSError("denied")):
            with self.subTest(error=type(error).__name__):
                record, evidence = self.probe(error)
                self.assertEqual((record["status"], record["exit_code"], record["error_type"]),
                                 ("probe_error", 124, type(error).__name__))
                self.assertEqual(self.evidence_file(evidence, "probe-python.exit-code.txt"), "124\n")


class ProbeSupportTests(ProbeCase):
    def test_support_needs_python_311_a_native_process_and_the_expected_architecture(self) -> None:
        cases = {
            "supported": ((3, 11, 0), "ARM64", "ARM64", "arm64", True),
            "newer major": ((4, 0, 0), "ARM64", "ARM64", "arm64", True),
            "too old": ((3, 10, 14), "ARM64", "ARM64", "arm64", False),
            "emulated": ((3, 13, 14), "AMD64", "ARM64", "arm64", False),
            "wrong architecture": ((3, 13, 14), "ARM64", "ARM64", "x64", False),
        }
        for name, (version, process, native, expected, supported) in cases.items():
            with self.subTest(case=name):
                record, _ = self.probe(result(probe_output(version, process, native)), expected=expected)
                self.assertEqual((record["supported"], record["version"]), (supported, ".".join(map(str, version))))
                self.assertEqual(record["status"], "supported" if supported else "rejected")

    def test_an_interpreter_with_no_executable_is_unsupported(self) -> None:
        stdout = json.dumps({"major": 3, "minor": 13, "micro": 14, "executable": "", "machine": "ARM64"})
        self.assertFalse(self.probe(result(stdout))[0]["supported"])

    def test_probes_run_as_argv_without_a_shell_in_the_given_directory(self) -> None:
        self.probe(result(""), candidate="py -V:3", expected="x64")
        call = self.run_mock.call_args
        self.assertEqual(call.args[0][:3], ["py", "-V:3", "-c"])
        self.assertEqual((call.kwargs["shell"], call.kwargs["cwd"], call.kwargs["timeout"]),
                         (False, REPO_ROOT, interpreters.PROBE_TIMEOUT_SECONDS))


class ProbeSelectionTests(unittest.TestCase):
    def probe_all(self, active_python: str) -> tuple[object, list[dict[str, object]], Path, list[list[str]]]:
        evidence = Path(self.enterContext(tempfile.TemporaryDirectory())) / "evidence"
        with (
            unittest.mock.patch.object(interpreters.shutil, "which", side_effect=lambda name: f"C:/Windows/{name}.exe"),
            unittest.mock.patch.object(interpreters.subprocess, "run", side_effect=fake_probe_run) as run_mock,
            unittest.mock.patch.object(interpreters.sys, "executable", active_python),
        ):
            selected, records = interpreters.probe_interpreters("arm64", evidence, cwd=REPO_ROOT)
        return selected, records, evidence, [call.args[0] for call in run_mock.call_args_list]

    def test_probes_are_ordered_and_select_the_active_native_python(self) -> None:
        selected, records, evidence, commands = self.probe_all("C:/Python/python.exe")
        aggregate = json.loads((evidence / "interpreter-probes.json").read_text(encoding="utf-8"))
        assert isinstance(selected, dict)
        self.assertEqual((selected["candidate"], selected["interpreter"]), ("python", "C:/Python/python.exe"))
        self.assertEqual([r["candidate"] for r in records], list(interpreters.INTERPRETER_CANDIDATES))
        self.assertEqual([c[:2] for c in commands], [["py", "-V:3"], ["py", "-3"], ["python", "-c"], ["python3", "-c"]])
        self.assertEqual([r["supported"] for r in records], [False, False, True, True])
        self.assertEqual([r["selected"] for r in records], [False, False, True, False])
        self.assertTrue(records[0]["architecture_emulated"])
        self.assertEqual(aggregate, records)

    def test_no_selection_when_no_supported_candidate_is_the_running_python(self) -> None:
        selected, records, _, _ = self.probe_all("C:/Elsewhere/python.exe")
        self.assertIsNone(selected)
        self.assertFalse(any(record["selected"] for record in records))


class DispatcherSplitTests(unittest.TestCase):
    def test_the_dispatcher_holds_no_interpreter_probing(self) -> None:
        source = DISPATCHER.read_text(encoding="utf-8")
        needles = ("INTERPRETER_PROBE_CODE", "def _probe_interpreter", "PROCESSOR_ARCHITECTURE", "resolve_architectures")
        self.assertEqual([needle for needle in needles if needle in source], [])
        self.assertIn("probe_interpreters", source)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-preflight-interpreters"))

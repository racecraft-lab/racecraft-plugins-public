#!/usr/bin/env python3
"""Shared per-assertion counting ``TestResult`` for the test suite.

``CountingTestResult`` reports each executed ``subTest`` as one unit and each
plain test method as one unit. This keeps the suite summary aligned with the
behavior that actually ran instead of counting only container methods.

This module is imported by ports (as a shared utility) — it never self-runs a
suite. Its own unit tests live in ``tests/speckit-pro/lib/test_lib.py``.
"""

from __future__ import annotations

import os
import re
import unittest
import unittest.case
from pathlib import Path
from typing import TextIO

# Repo root, from this file's own location: tests/speckit-pro/lib/ -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPECS_GUARD_INSTALLED = False
_COUNTED_SUMMARY_RE = re.compile(
    r"^(?P<label>[^:]+):\s*(?P<passed>\d+)/(?P<total>\d+) passed\s*$"
)


def classify_counted_child(
    exit_code: int,
    stdout: str,
    expected_label: str,
) -> tuple[str, int, int, str]:
    """Classify exactly one summary owned by the directly executed child."""
    owned = []
    for line in stdout.splitlines():
        match = _COUNTED_SUMMARY_RE.fullmatch(line)
        if match is not None and match.group("label") == expected_label:
            owned.append((line, int(match.group("passed")), int(match.group("total"))))
    if not owned:
        disposition = "missing-summary" if exit_code == 0 else "crash"
        return disposition, 0, 1, f"no valid {expected_label} summary"
    if len(owned) != 1:
        return "duplicate-summary", 0, 1, f"multiple {expected_label} summaries"
    line, passed, total = owned[0]
    if total == 0:
        return "invalid-summary", 0, 1, "zero checks discovered"
    if passed > total:
        return "invalid-summary", 0, 1, "passed count exceeds total"
    failed = total - passed
    if exit_code != 0 and failed == 0:
        return "failed-exit", passed, 1, f"all checks passed but child exited {exit_code}"
    detail = line if failed == 0 else "not all checks passed"
    return "counted", passed, failed, detail


def child_check_status(exit_code: int, stdout: str, expected_label: str) -> tuple[bool, str]:
    """Return whether a directly executed counted child passed."""
    disposition, _passed, failed, detail = classify_counted_child(
        exit_code,
        stdout,
        expected_label,
    )
    return disposition == "counted" and failed == 0, detail


def install_specs_read_guard(repo_root: Path | None = None) -> None:
    """Fail any test that reads a live ``specs/<feature>/`` path from disk.

    Archive cleanup deletes a feature's ``specs/`` folder once its pull request
    merges, so a test that opens one is a time bomb: green today, red at archive
    time, months later, in a cleanup branch that has nothing to do with it. That
    is not hypothetical: archived feature folders disappear while tests remain,
    so a test that reads one eventually fails for reasons unrelated to behavior.

    **Why an audit hook rather than a source scan.** The distinction that matters
    is data versus access, and no static pass draws it reliably. A ``specs/...``
    string is perfectly legitimate as *data* — the same test asserts dozens of
    them, because ``specs/<feature>/`` is the shape a real run produces and the
    fixtures are right to pin it. What is not legitimate is *opening* one. Only
    the interpreter knows which happened, and ``sys.addaudithook`` is where it
    says so. A grep would flood on the strings and still miss the real read,
    which reached the filesystem through a variable rather than a literal.

    **``os.stat`` is deliberately not watched.** ``Path.resolve()``,
    ``exists()``, and ``is_dir()`` on a specs-shaped path survive archive on
    their own terms: the folder simply stops existing and the probe answers
    False. Watching them would fail exactly the path arithmetic that is safe.
    Content reads and directory listings are what break, and those are what this
    catches.

    **Opt out where sweeping the live tree is the job.** These suites do:
    ``validate-moc-orphan``, ``validate-moc-stale-index``,
    ``validate-agent-instructions``, ``test-privacy-scan`` and
    ``test-artifact-gallery``. Each walks whatever
    specs happen to exist rather than depending on one by name, which makes it
    archive-safe by construction: an absent feature folder contributes nothing.
    They pass ``allow_live_specs=True`` to ``run_counted``.

    That is the whole test for whether opting out is right, and it is narrower
    than "this suite touches ``specs/``". Sweeping what is there is safe;
    depending on a named spec is the time bomb, and no amount of opting out
    makes it safe — that case wants its documents frozen under the suite's own
    ``fixtures/`` tree instead. Several were found by this guard
    failing on its first run rather than predicted, so expect to discover rather
    than enumerate.

    **Subprocess boundary.** Tests must not hand named live ``specs/`` paths to
    subprocesses. A subprocess test that needs a spec-shaped tree must instead
    create a test-owned temporary repository and use frozen fixture documents.
    The hook remains deliberately process-local; tests enforce the boundary by
    construction rather than adding subprocess interception.
    """
    global _SPECS_GUARD_INSTALLED
    if _SPECS_GUARD_INSTALLED:
        return
    import sys

    root = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    prefix = str(root / "specs") + os.sep
    watched = ("open", "os.scandir", "os.listdir", "glob.glob")

    def _hook(event: str, hook_args: tuple) -> None:
        if event not in watched or not hook_args:
            return
        candidate = hook_args[0]
        if not isinstance(candidate, (str, bytes, os.PathLike)):
            return
        try:
            path = os.fsdecode(os.fspath(candidate))
        except (TypeError, ValueError):
            return
        if not os.path.abspath(path).startswith(prefix):
            return
        raise AssertionError(
            f"a test read a live specs/ path: {path}\n"
            "Archive cleanup deletes specs/<feature>/ once the feature merges, so "
            "this read would go red at archive time rather than now. Freeze the "
            "documents the test needs under its own fixtures/ tree and read them "
            "from there. Asserting a specs/... path as a string is fine; opening "
            "one is not. A validator whose job is scanning the live tree passes "
            "allow_live_specs=True to run_counted."
        )

    sys.addaudithook(_hook)
    _SPECS_GUARD_INSTALLED = True

class CountingTestResult(unittest.TextTestResult):
    """A ``TextTestResult`` that counts per-assertion units, not just methods.

    ``units_total`` / ``units_passed`` are the numbers a port reports as
    ``{total}`` / ``{passed}``. A method that emits ``subTest``s contributes one
    unit per executed subTest (and is not itself counted); a method with no
    ``subTest``s contributes exactly one unit. If a method fails outside a
    subTest after emitting subTests, that method-level failure contributes one
    additional failed unit.
    """

    def __init__(self, stream: TextIO | None = None, descriptions: bool = False, verbosity: int = 0) -> None:
        # TextTestResult requires a real stream for its writeln() calls; callers
        # that pass stream=None get a throwaway sink so counting works headless.
        if stream is None:
            import io

            stream = _StreamWrapper(io.StringIO())
        elif not hasattr(stream, "writeln"):
            stream = _StreamWrapper(stream)
        super().__init__(stream, descriptions, verbosity)
        self.units_total = 0
        self.units_passed = 0
        self._current_has_subtests = False
        self._current_method_failed = False

    def startTest(self, test: unittest.case.TestCase) -> None:
        super().startTest(test)
        self._current_has_subtests = False
        self._current_method_failed = False

    def addSubTest(
        self,
        test: unittest.case.TestCase,
        subtest: unittest.case._SubTest,
        outcome: object,
    ) -> None:
        super().addSubTest(test, subtest, outcome)
        self._current_has_subtests = True
        self.units_total += 1
        # stdlib passes outcome=None on success, or the (type, value, tb) tuple
        # on failure/error.
        if outcome is None:
            self.units_passed += 1

    def addFailure(self, test: unittest.case.TestCase, err: object) -> None:
        super().addFailure(test, err)
        self._current_method_failed = True

    def addError(self, test: unittest.case.TestCase, err: object) -> None:
        super().addError(test, err)
        self._current_method_failed = True

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        self._current_method_failed = True

    def stopTest(self, test: unittest.case.TestCase) -> None:
        super().stopTest(test)
        if self._current_has_subtests and self._current_method_failed:
            # Successful subTests do not account for a later method-level
            # failure, so represent that independent failure as one unit.
            self.units_total += 1
        elif not self._current_has_subtests:
            # A non-loop, non-grouped method is exactly one counted unit.
            self.units_total += 1
            if not self._current_method_failed:
                self.units_passed += 1


class _StreamWrapper:
    """Minimal ``runner``-stream shim exposing the ``writeln`` TextTestResult needs."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream

    def write(self, text: str) -> None:
        self._stream.write(text)

    def writeln(self, text: str = "") -> None:
        self._stream.write(text)
        self._stream.write("\n")

    def flush(self) -> None:
        flush = getattr(self._stream, "flush", None)
        if callable(flush):
            flush()


def run_counted(
    suite: unittest.TestSuite,
    *,
    label: str,
    stream: TextIO | None = None,
    verbosity: int = 0,
    allow_live_specs: bool = False,
) -> int:
    """Run ``suite`` with per-assertion counting; print the house summary.

    Prints ``<label>: {passed}/{total} passed`` to ``stream`` (default stdout)
    and returns ``0`` only when at least one counted unit ran and every unit
    passed, ``1`` otherwise.

    Installs the live-``specs/`` read guard first, because every test in this
    repository funnels through here and one install covers all of them. Pass
    ``allow_live_specs=True`` only when walking the live tree is the suite's
    actual job; see ``install_specs_read_guard``.
    """
    import sys

    if not allow_live_specs:
        install_specs_read_guard()
    out = sys.stdout if stream is None else stream
    result = CountingTestResult(stream=None, descriptions=False, verbosity=verbosity)
    suite.run(result)
    out.write(f"{label}: {result.units_passed}/{result.units_total} passed\n")
    ok = result.units_total > 0 and (result.units_passed == result.units_total) and not result.failures and not result.errors
    return 0 if ok else 1


__all__ = (
    "CountingTestResult",
    "child_check_status",
    "install_specs_read_guard",
    "run_counted",
)

#!/usr/bin/env python3
"""Shared per-assertion counting ``TestResult`` for XPLAT-010 count-parity ports.

Every ported ``.sh`` structural/unit test lands as a stdlib ``unittest`` module
whose ``__main__`` prints the house-convention ``<label>: {passed}/{total}
passed`` line the suite orchestrator (``run-all.py`` / ``run-layer-scripts.py``)
and the shipped suite gate parse. The bash predecessor counted **every executed
assertion** (``_pass``/``_fail``), including loop-generated repetitions. Bare
``unittest`` ``result.testsRun`` counts test *methods* and never increments for
``subTest`` units, so it silently under-counts any looped or grouped assertions
(count-parity contract §3, FR-010, research §D6).

``CountingTestResult`` fixes this: ``{total}`` equals ``(test methods NOT in a
subTest loop/group) + (subTest units actually executed)`` and each former
assertion execution maps to exactly one counted unit. Ports reconcile each bash
check name 1:1 via ``subTest(msg=<name>)``; the executed names are captured in
``subtest_names`` for the dual-run inventory diff.

This module is imported by ports (as a shared utility) — it never self-runs a
suite. Its own unit tests live in ``tests/speckit-pro/lib/test_lib.py``.
"""

from __future__ import annotations

import unittest
import unittest.case
from typing import TextIO

_SUBTEST_MSG_SENTINEL = getattr(unittest.case, "_subtest_msg_sentinel", None)


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
        self.subtest_names: list[str] = []
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
        self.subtest_names.append(_subtest_label(subtest))

    def addFailure(self, test: unittest.case.TestCase, err: object) -> None:
        super().addFailure(test, err)
        self._current_method_failed = True

    def addError(self, test: unittest.case.TestCase, err: object) -> None:
        super().addError(test, err)
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


def _subtest_label(subtest: unittest.case._SubTest) -> str:
    """Recover the 1:1 bash-check name a port pinned via ``subTest(msg=...)``."""
    message = getattr(subtest, "_message", None)
    if _SUBTEST_MSG_SENTINEL is not None and message is _SUBTEST_MSG_SENTINEL:
        message = None
    if message:
        return str(message)
    params = getattr(subtest, "params", None)
    if params:
        return ", ".join(f"{key}={value}" for key, value in params.items())
    return "<subtest>"


def run_counted(
    suite: unittest.TestSuite,
    *,
    label: str,
    stream: TextIO | None = None,
    verbosity: int = 0,
) -> int:
    """Run ``suite`` with per-assertion counting; print the house summary.

    Prints ``<label>: {passed}/{total} passed`` to ``stream`` (default stdout)
    and returns ``0`` when every counted unit passed, ``1`` otherwise.
    """
    import sys

    out = sys.stdout if stream is None else stream
    result = CountingTestResult(stream=None, descriptions=False, verbosity=verbosity)
    suite.run(result)
    out.write(f"{label}: {result.units_passed}/{result.units_total} passed\n")
    ok = (result.units_passed == result.units_total) and not result.failures and not result.errors
    return 0 if ok else 1


__all__ = ("CountingTestResult", "run_counted")

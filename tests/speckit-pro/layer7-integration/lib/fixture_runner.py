#!/usr/bin/env python3
"""Shared mechanics for the Layer-7 Python fixture runners."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

LAYER7_ROOT = Path(__file__).resolve().parent.parent
SCRUBBER = LAYER7_ROOT / "scrub-transcript.py"
REDUCER = LAYER7_ROOT / "reduce-transcript-fixture.py"


class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.total = 0
        self.failures: list[str] = []
        self.names: list[str] = []
        self.verbose = os.environ.get("VERBOSE", "").lower() == "true"

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.total += 1
        self.names.append(name)
        if condition:
            self.passed += 1
            if self.verbose:
                print(f"  {name} ... PASS")
            return True
        self.failures.append(f"{name}: {detail}" if detail else name)
        if self.verbose:
            print(f"  {name} ... FAIL")
        elif detail:
            print(f"FAIL: {name}: {detail}", file=sys.stderr)
        else:
            print(f"FAIL: {name}", file=sys.stderr)
        return False

    def finish(self, label: str) -> int:
        print(f"{label}: {self.passed}/{self.total} passed")
        return 0 if self.passed == self.total else 1


def parse_runner_args(argv: list[str]) -> tuple[str, str | None, bool]:
    mode = "replay"
    selected: str | None = None
    help_requested = False
    for value in argv:
        if value == "--replay":
            mode = "replay"
        elif value == "--live":
            mode = "live"
        elif value in {"-h", "--help"}:
            help_requested = True
        else:
            selected = value
    return mode, selected, help_requested


def collect_fixtures(root: Path, selected: str | None) -> list[Path]:
    if selected is not None:
        fixture = root / selected
        if not fixture.is_dir():
            raise ValueError(f"fixture not found: {selected}")
        return [fixture]
    return sorted(path for path in root.iterdir() if path.is_dir())


def load_expected(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def capture_live(fixture: Path, budget_usd: str, *, announce_saved: bool = False) -> bool:
    claude = shutil.which("claude")
    if claude is None:
        print("  SKIP (claude CLI not found)")
        return False

    prompt_file = fixture / "prompt.txt"
    transcript_file = fixture / "transcript.jsonl"
    parser_fixture = fixture / "parser-fixture.jsonl"
    print(f"  Capturing live transcript (budget: ${budget_usd})...")
    with prompt_file.open("r", encoding="utf-8") as prompt, transcript_file.open("w", encoding="utf-8") as transcript:
        completed = subprocess.run(
            [
                claude,
                "-p",
                "--output-format",
                "stream-json",
                "--include-partial-messages",
                "--verbose",
                "--max-budget-usd",
                budget_usd,
                "--no-session-persistence",
            ],
            stdin=prompt,
            stdout=transcript,
            stderr=subprocess.DEVNULL,
            text=True,
            shell=False,
            check=False,
        )
    if completed.returncode != 0:
        print("  WARN: claude -p exited non-zero - partial transcript may have been captured")

    scrub_succeeded = transcript_file.stat().st_size == 0
    try:
        if transcript_file.stat().st_size > 0:
            scrubbed = subprocess.run(
                [sys.executable, str(SCRUBBER), str(transcript_file)],
                text=True,
                capture_output=True,
                shell=False,
                check=False,
            )
            if scrubbed.returncode != 0:
                raise RuntimeError(scrubbed.stderr.strip() or "transcript scrub failed")
            scrub_succeeded = True
    finally:
        if not scrub_succeeded:
            try:
                transcript_file.unlink()
            except FileNotFoundError:
                pass
    if announce_saved:
        print(f"  Saved scrubbed transient transcript to {transcript_file}")

    if os.environ.get("L7_UPDATE_PARSER_FIXTURE", "false").lower() == "true" and transcript_file.stat().st_size > 0:
        with parser_fixture.open("w", encoding="utf-8") as destination:
            reduced = subprocess.run(
                [sys.executable, str(REDUCER), str(transcript_file), str(fixture / "expected.json")],
                stdout=destination,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                check=False,
            )
        if reduced.returncode != 0:
            raise RuntimeError(reduced.stderr.strip() or "transcript reduction failed")
        print(f"  Updated reduced parser fixture at {parser_fixture}")
    return True


def transcript_for(fixture: Path, mode: str) -> Path:
    return fixture / ("transcript.jsonl" if mode == "live" else "parser-fixture.jsonl")


def assert_dispatch_fixture(
    fixture: Path,
    mode: str,
    reporter: Reporter,
    *,
    check_terms: bool,
) -> None:
    from . import transcript_helpers as helpers

    expected_path = fixture / "expected.json"
    transcript = transcript_for(fixture, mode)
    if not expected_path.is_file():
        reporter.check(f"{fixture.name}: expected.json present", False, f"missing {expected_path}")
        return
    if not transcript.is_file():
        if mode == "replay":
            print(f"  SKIP {fixture.name}: no parser-fixture.jsonl committed (run --live with L7_UPDATE_PARSER_FIXTURE=true to refresh)")
        else:
            reporter.check(f"{fixture.name}: transient transcript.jsonl produced by --live", False, "no transcript captured")
        return

    expected = load_expected(expected_path)
    fixture_id = fixture.name
    for target in string_list(expected.get("must_dispatch_to")):
        reporter.check(
            f"{fixture_id}: dispatched to {target}",
            helpers.assert_dispatched_to(transcript, target),
            f"expected dispatch to {target}, none found",
        )

    allowed = string_list(expected.get("must_dispatch_to_at_least_one_of"))
    if "must_dispatch_to_at_least_one_of" in expected:
        reporter.check(
            f"{fixture_id}: dispatched to at least one of allowed set",
            any(helpers.assert_dispatched_to(transcript, target) for target in allowed),
            "expected dispatch to at least one allowed target",
        )

    for target in string_list(expected.get("must_not_dispatch_to")):
        reporter.check(
            f"{fixture_id}: never dispatched to {target}",
            helpers.assert_not_dispatched_to(transcript, target),
            f"{target} was dispatched but should not have been",
        )

    if expected.get("must_not_have_forbidden_spawns") is True:
        reporter.check(
            f"{fixture_id}: no subagent spawned an Agent()",
            helpers.assert_no_forbidden_spawns(transcript),
            "found subagent that spawned another Agent",
        )

    for pattern in string_list(expected.get("must_not_invoke_skill")):
        reporter.check(
            f"{fixture_id}: skill never invoked: {pattern} (any scope)",
            helpers.assert_skill_not_invoked(transcript, pattern),
            f"skill matching {pattern!r} was invoked",
        )

    if check_terms:
        for term in string_list(expected.get("must_include_terms")):
            reporter.check(
                f"{fixture_id}: transcript includes term: {term}",
                helpers.assert_transcript_contains_term(transcript, term),
                f"expected transcript to include {term!r}",
            )

        for term in string_list(expected.get("must_not_include_terms")):
            reporter.check(
                f"{fixture_id}: transcript excludes term: {term}",
                helpers.assert_transcript_not_contains_term(transcript, term),
                f"transcript included forbidden term {term!r}",
            )

    total = len(helpers.extract_orchestrator_dispatches(transcript))
    if "min_dispatch_count" in expected:
        minimum = int(expected["min_dispatch_count"])
        reporter.check(
            f"{fixture_id}: dispatch count >= {minimum} (got {total})",
            total >= minimum,
            f"expected >= {minimum}, got {total}",
        )
    if "max_dispatch_count" in expected:
        maximum = int(expected["max_dispatch_count"])
        reporter.check(
            f"{fixture_id}: dispatch count <= {maximum} (got {total})",
            total <= maximum,
            f"expected <= {maximum}, got {total}",
        )

    order = helpers.extract_dispatch_order(transcript)
    constraints = expected.get("dispatch_order_constraints", [])
    if isinstance(constraints, list):
        for constraint in constraints:
            if not isinstance(constraint, dict):
                continue
            before = str(constraint.get("before", ""))
            after = str(constraint.get("after", ""))
            condition = before in order and after in order and order.index(before) < order.index(after)
            reporter.check(f"{fixture_id}: {before} precedes {after}", condition, "order constraint violated")


def print_fixture_heading(fixture: Path) -> None:
    print(f"\nFixture: {fixture.name}")


def report_runtime_error(label: str, exc: Exception) -> int:
    print(f"{label}: {exc}", file=sys.stderr)
    return 2 if isinstance(exc, ValueError) else 1

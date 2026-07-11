#!/usr/bin/env python3
"""Run Layer-7 Class-3 end-to-end fixtures in replay or live mode."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from lib import transcript_helpers as helpers
from lib.fixture_runner import (
    Reporter,
    capture_live,
    collect_fixtures,
    load_expected,
    parse_runner_args,
    print_fixture_heading,
    report_runtime_error,
    string_list,
    transcript_for,
)


SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES = SCRIPT_DIR / "e2e-fixtures"
LABEL = "run-e2e-fixtures"


def assert_fixture(fixture: Path, mode: str, reporter: Reporter) -> None:
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


def main(argv: list[str]) -> int:
    mode, selected, help_requested = parse_runner_args(argv)
    if help_requested:
        print("usage: run-e2e-fixtures.py [--replay|--live] [fixture-id]")
        return 0
    reporter = Reporter()
    try:
        fixtures = collect_fixtures(FIXTURES, selected)
        print(f"\nLayer 7 Class 3: End-to-End Fixtures (mode: {mode})")
        if mode == "live" and not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            print("NOTE: --live requires claude -p with auth configured.")
        budget = os.environ.get("E2E_FIXTURE_BUDGET_USD", "10.00")
        for fixture in fixtures:
            print_fixture_heading(fixture)
            if mode == "live":
                capture_live(fixture, budget, announce_saved=True)
            assert_fixture(fixture, mode, reporter)
        return reporter.finish(LABEL)
    except (OSError, ValueError, RuntimeError) as exc:
        return report_runtime_error(LABEL, exc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

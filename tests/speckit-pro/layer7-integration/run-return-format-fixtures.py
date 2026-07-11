#!/usr/bin/env python3
"""Run Layer-7 Class-2 cross-agent response-format fixtures."""

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
FIXTURES = SCRIPT_DIR / "return-format-fixtures"
LABEL = "run-return-format-fixtures"


def response_assertions(expected: dict[str, object], fixture_id: str) -> list[dict[str, object]]:
    assertions = expected.get("response_assertions", [])
    if not isinstance(assertions, list):
        raise ValueError(f"{fixture_id}: response_assertions must be an array")

    validated: list[dict[str, object]] = []
    for index, assertion in enumerate(assertions):
        if not isinstance(assertion, dict):
            raise ValueError(f"{fixture_id}: response_assertions[{index}] must be an object")
        subagent_type = assertion.get("subagent_type")
        if not isinstance(subagent_type, str) or not subagent_type:
            raise ValueError(f"{fixture_id}: response_assertions[{index}].subagent_type must be a non-empty string")
        for field in ("must_contain_any", "must_contain_section_keywords"):
            if field not in assertion:
                continue
            value = assertion[field]
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"{fixture_id}: response_assertions[{index}].{field} must be an array of strings")
        validated.append(assertion)
    return validated


def assert_fixture(fixture: Path, mode: str, reporter: Reporter) -> None:
    expected_path = fixture / "expected.json"
    transcript = transcript_for(fixture, mode)
    if not expected_path.is_file():
        reporter.check(f"{fixture.name}: expected.json", False, "missing")
        return
    if not transcript.is_file():
        if mode == "replay":
            print(f"  SKIP {fixture.name}: no parser-fixture.jsonl committed")
        else:
            reporter.check(f"{fixture.name}: transient transcript captured", False, "no transcript")
        return

    expected = load_expected(expected_path)
    fixture_id = fixture.name
    for target in string_list(expected.get("must_dispatch_to")):
        reporter.check(
            f"{fixture_id}: dispatched to {target}",
            helpers.assert_dispatched_to(transcript, target),
            f"expected dispatch to {target}",
        )

    if expected.get("must_not_have_forbidden_spawns") is True:
        reporter.check(
            f"{fixture_id}: no subagent spawned an Agent()",
            helpers.assert_no_forbidden_spawns(transcript),
            "found subagent spawning Agent",
        )

    for pattern in string_list(expected.get("must_not_invoke_skill")):
        reporter.check(
            f"{fixture_id}: skill never invoked: {pattern} (any scope)",
            helpers.assert_skill_not_invoked(transcript, pattern),
            f"skill matching {pattern!r} was invoked",
        )

    for assertion in response_assertions(expected, fixture_id):
        subagent_type = assertion["subagent_type"]
        content = helpers.get_response_content(transcript, subagent_type)
        if "must_contain_any" in assertion:
            needles = string_list(assertion.get("must_contain_any"))
            reporter.check(
                f"{fixture_id}: {subagent_type} response contains any of allowed substrings",
                any(needle in content for needle in needles),
                f"none of the expected substrings found in {subagent_type} response",
            )
        for keyword in string_list(assertion.get("must_contain_section_keywords")):
            reporter.check(
                f"{fixture_id}: {subagent_type} response contains section keyword '{keyword}'",
                keyword.casefold() in content.casefold(),
                f"missing keyword {keyword!r} in {subagent_type} response",
            )


def main(argv: list[str]) -> int:
    mode, selected, help_requested = parse_runner_args(argv)
    if help_requested:
        print("usage: run-return-format-fixtures.py [--replay|--live] [fixture-id]")
        return 0
    reporter = Reporter()
    try:
        fixtures = collect_fixtures(FIXTURES, selected)
        print(f"\nLayer 7 Class 2: Return-Format Fixtures (mode: {mode})")
        budget = os.environ.get("RETURN_FORMAT_FIXTURE_BUDGET_USD", "1.00")
        for fixture in fixtures:
            print_fixture_heading(fixture)
            if mode == "live":
                capture_live(fixture, budget)
            assert_fixture(fixture, mode, reporter)
        return reporter.finish(LABEL)
    except (OSError, ValueError, RuntimeError) as exc:
        return report_runtime_error(LABEL, exc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

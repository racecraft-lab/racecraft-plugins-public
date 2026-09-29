#!/usr/bin/env python3
"""Run Layer-6 Class-2 cross-agent response-format fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from lib import transcript_helpers as helpers
from lib.fixture_runner import (
    Reporter,
    capture_or_fail,
    check_dispatch_shape,
    check_transcript_terms,
    collect_fixtures,
    load_fixture,
    parse_runner_args,
    print_fixture_heading,
    report_runtime_error,
    string_list,
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
        for field in ("must_contain_any", "must_not_contain_any", "must_contain_section_keywords"):
            if field not in assertion:
                continue
            value = assertion[field]
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"{fixture_id}: response_assertions[{index}].{field} must be an array of strings")
        validated.append(assertion)
    return validated


def check_response_assertion(
    reporter: Reporter,
    fixture_id: str,
    transcript: Path,
    assertion: dict[str, object],
    mode: str,
) -> None:
    subagent_type = str(assertion["subagent_type"])
    content = helpers.get_response_content(transcript, subagent_type)
    if not content.strip():
        if mode == "replay":
            print(f"  SKIP {fixture_id}: {subagent_type} response format is checked by --live (no captured response retained)")
        else:
            reporter.check(f"{fixture_id}: {subagent_type} response captured", False, "empty response")
        return
    if "must_contain_any" in assertion:
        needles = string_list(assertion.get("must_contain_any"))
        reporter.check(
            f"{fixture_id}: {subagent_type} response contains any of allowed substrings",
            any(needle in content for needle in needles),
            f"none of the expected substrings found in {subagent_type} response",
        )
    for needle in string_list(assertion.get("must_not_contain_any")):
        reporter.check(
            f"{fixture_id}: {subagent_type} response excludes {needle!r}",
            needle not in content,
            f"forbidden substring {needle!r} found in {subagent_type} response",
        )
    for keyword in string_list(assertion.get("must_contain_section_keywords")):
        reporter.check(
            f"{fixture_id}: {subagent_type} response contains section keyword '{keyword}'",
            keyword.casefold() in content.casefold(),
            f"missing keyword {keyword!r} in {subagent_type} response",
        )


def assert_fixture(fixture: Path, mode: str, reporter: Reporter) -> None:
    loaded = load_fixture(fixture, mode, reporter)
    if loaded is None:
        return
    transcript, expected = loaded
    check_dispatch_shape(reporter, fixture.name, transcript, expected)
    check_transcript_terms(reporter, fixture.name, transcript, expected, forbidden=False)
    for assertion in response_assertions(expected, fixture.name):
        check_response_assertion(reporter, fixture.name, transcript, assertion, mode)


def main(argv: list[str]) -> int:
    mode, selected, help_requested = parse_runner_args(argv)
    if help_requested:
        print("usage: run-return-format-fixtures.py [--replay|--live] [fixture-id]")
        return 0
    reporter = Reporter()
    try:
        fixtures = collect_fixtures(FIXTURES, selected)
        print(f"\nLayer 6 Class 2: Return-Format Fixtures (mode: {mode})")
        budget = os.environ.get("RETURN_FORMAT_FIXTURE_BUDGET_USD", "1.00")
        for fixture in fixtures:
            print_fixture_heading(fixture)
            if mode == "live" and not capture_or_fail(fixture, budget, reporter):
                continue
            assert_fixture(fixture, mode, reporter)
        return reporter.finish(LABEL)
    except (OSError, ValueError, RuntimeError) as exc:
        return report_runtime_error(LABEL, exc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

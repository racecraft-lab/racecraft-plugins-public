#!/usr/bin/env python3
"""Run Layer-6 Class-4 grounding fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

from lib import grounding_helpers as grounding
from lib import transcript_helpers as helpers
from lib.fixture_runner import (
    Reporter,
    check_transcript_terms,
    collect_fixtures,
    load_fixture,
    parse_runner_args,
    print_fixture_heading,
    report_runtime_error,
    string_list,
)


SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES = SCRIPT_DIR / "grounding-fixtures"
LABEL = "run-grounding-fixtures"


def assert_fixture(fixture: Path, reporter: Reporter) -> None:
    fixture_id = fixture.name
    loaded = load_fixture(fixture, "replay", reporter)
    if loaded is None:
        return
    transcript, expected = loaded

    if "expect_grounding_verdict" in expected:
        wanted = str(expected["expect_grounding_verdict"])
        actual = grounding.grounding_verdict(transcript)
        reporter.check(
            f"{fixture_id}: grounding verdict is '{wanted}' (got '{actual}')",
            actual == wanted,
            f"expected {wanted!r}, got {actual!r}",
        )

    if "expect_citation_count" in expected:
        wanted_count = int(expected["expect_citation_count"])
        actual_count = len(grounding.extract_capability_citations(transcript))
        reporter.check(
            f"{fixture_id}: distinct cited-capability count == {wanted_count} (got {actual_count})",
            actual_count == wanted_count,
            f"expected {wanted_count}, got {actual_count}",
        )

    for tool in string_list(expected.get("must_invoke_tools")):
        reporter.check(
            f"{fixture_id}: tool actually invoked: {tool}",
            helpers.tool_invoked(transcript, tool),
            f"expected a real tool_use for {tool!r}",
        )

    for tool in string_list(expected.get("must_not_invoke_tools")):
        reporter.check(
            f"{fixture_id}: tool never invoked: {tool}",
            not helpers.tool_invoked(transcript, tool),
            f"{tool!r} was invoked but should not have been",
        )

    check_transcript_terms(reporter, fixture_id, transcript, expected)


def main(argv: list[str]) -> int:
    mode, selected, help_requested = parse_runner_args(argv)
    if help_requested:
        print("usage: run-grounding-fixtures.py [--replay] [fixture-id]")
        return 0
    reporter = Reporter()
    try:
        if mode != "replay":
            raise ValueError("grounding fixtures are replay-only; --live is not supported")
        print("\nLayer 6 Class 4: Grounding Fixtures (replay)")
        for fixture in collect_fixtures(FIXTURES, selected):
            print_fixture_heading(fixture)
            assert_fixture(fixture, reporter)
        return reporter.finish(LABEL)
    except (OSError, ValueError, RuntimeError) as exc:
        return report_runtime_error(LABEL, exc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

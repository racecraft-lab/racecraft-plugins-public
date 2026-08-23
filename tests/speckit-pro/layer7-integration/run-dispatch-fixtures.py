#!/usr/bin/env python3
"""Run Layer-7 Class-1 dispatch fixtures in replay or live mode."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from lib.fixture_runner import (
    Reporter,
    assert_dispatch_fixture,
    capture_live,
    collect_fixtures,
    parse_runner_args,
    print_fixture_heading,
    report_runtime_error,
)


SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES = SCRIPT_DIR / "dispatch-fixtures"
LABEL = "run-dispatch-fixtures"


def assert_fixture(fixture: Path, mode: str, reporter: Reporter) -> None:
    assert_dispatch_fixture(fixture, mode, reporter, check_terms=True)


def main(argv: list[str]) -> int:
    mode, selected, help_requested = parse_runner_args(argv)
    if help_requested:
        print("usage: run-dispatch-fixtures.py [--replay|--live] [fixture-id]")
        return 0
    reporter = Reporter()
    try:
        fixtures = collect_fixtures(FIXTURES, selected)
        print(f"\nLayer 7 Class 1: Dispatch Fixtures (mode: {mode})")
        if mode == "live" and not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            print("NOTE: --live requires claude -p with auth configured.")
        budget = os.environ.get("DISPATCH_FIXTURE_BUDGET_USD", "1.00")
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

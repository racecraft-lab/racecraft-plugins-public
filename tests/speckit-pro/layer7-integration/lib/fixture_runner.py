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


def print_fixture_heading(fixture: Path) -> None:
    print(f"\nFixture: {fixture.name}")


def report_runtime_error(label: str, exc: Exception) -> int:
    print(f"{label}: {exc}", file=sys.stderr)
    return 2 if isinstance(exc, ValueError) else 1

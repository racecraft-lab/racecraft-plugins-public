"""Failing-check fingerprints the runner derives from verification output it executed.

A closed set of output formats (unittest, pytest, bun, jest) is parsed into a
sorted set of failing test identifiers, passing identifiers where the format
names them, and the number of checks the run reported. The command's argv is
bound by digest, so a narrowed command never compares with the original. Anything else, including output that matches two formats, a
nonzero exit that names no failure, or a command that did not finish, records
no failing set. No set means no evidence of progress, so the ledger falls back
to its fixed correction allowances.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .agent_materialization import canonical_bytes

# The most identifiers one fingerprint keeps. A larger failing set is unparsed;
# a larger passing set is dropped, which only withholds disjoint-move progress.
MAX_IDENTIFIERS = 2000
MAX_IDENTIFIER_LENGTH = 240
FORMATS: dict[str, dict[str, re.Pattern[str] | None]] = {
    "unittest": {"marker": re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.M),
                 "failing": re.compile(r"^(?:FAIL|ERROR): (\S+ \([\w.]+\))", re.M),
                 "passing": re.compile(r"^(\S+ \([\w.]+\)) \.\.\. ok$", re.M)},
    "pytest": {"marker": re.compile(r"^=+ .*\b\d+ (?:passed|failed|errors?)\b.* in [\d.]+s\b.*=+$", re.M),
               "failing": re.compile(r"^(?:FAILED|ERROR) (\S+)", re.M),
               "passing": re.compile(r"^(\S+::\S+) PASSED\b", re.M)},
    "bun": {"marker": re.compile(r"^Ran (\d+) tests? across \d+ files?\.", re.M),
            "failing": re.compile(r"^\(fail\) (.+?)(?: \[[\d.]+m?s\])?$", re.M),
            "passing": re.compile(r"^\(pass\) (.+?)(?: \[[\d.]+m?s\])?$", re.M)},
    "jest": {"marker": re.compile(r"^Tests: +.*\b(\d+) total$", re.M),
             "failing": re.compile(r"^ +● (.+?)$", re.M),
             "passing": None},
}


def _identifier(text: str) -> str:
    """One normalized identifier; an overlong one is replaced by its digest so it cannot collide."""
    text = " ".join(text.split())
    if len(text) <= MAX_IDENTIFIER_LENGTH:
        return text
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identifiers(pattern: re.Pattern[str] | None, text: str) -> list[str] | None:
    if pattern is None:
        return None
    found = sorted({_identifier(match) for match in pattern.findall(text)})
    return found if len(found) <= MAX_IDENTIFIERS else None


PYTEST_COUNTS = re.compile(r"(\d+) (?:passed|failed|errors?|skipped|xfailed|xpassed)\b")


def _checks_run(name: str, text: str) -> int | None:
    """The number of checks the run reports: its own summary count, summed across summaries."""
    pattern = FORMATS[name]["marker"]
    if pattern is None:
        return None
    if name == "pytest":
        return sum(int(count) for line in pattern.findall(text) for count in PYTEST_COUNTS.findall(line))
    return sum(int(count) for count in pattern.findall(text))


def fingerprint(command_id: str, argv: list[str], exit_code: int | None, completed: bool, stdout: bytes,
                stderr: bytes) -> dict[str, Any]:
    """The failing-check set one verification run shows, or `failing: None` when the output is unparsed."""
    output = stdout + b"\n" + stderr
    text = output.decode("utf-8", errors="replace").replace("\r\n", "\n")
    record: dict[str, Any] = {"command_id": command_id,
                              "command_sha256": hashlib.sha256(canonical_bytes(argv)).hexdigest(),
                              "format": "unparsed", "failing": None, "passing": None, "checks_run": None,
                              "output_sha256": hashlib.sha256(output).hexdigest()}
    formats = [name for name, patterns in FORMATS.items() if patterns["marker"] and patterns["marker"].search(text)]
    if not completed or type(exit_code) is not int:
        return record
    if exit_code == 0:
        if len(formats) != 1:
            return {**record, "format": "passed", "failing": []}
        return {**record, "format": formats[0], "failing": [], "checks_run": _checks_run(formats[0], text),
                "passing": _identifiers(FORMATS[formats[0]]["passing"], text) or None}
    if len(formats) != 1:
        return record
    patterns = FORMATS[formats[0]]
    failing = _identifiers(patterns["failing"], text)
    if not failing:
        return record
    return {**record, "format": formats[0], "failing": failing, "checks_run": _checks_run(formats[0], text),
            "passing": _identifiers(patterns["passing"], text) or None}

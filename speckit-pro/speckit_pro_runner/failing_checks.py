"""Failing-check fingerprints the runner derives from verification output it executed.

A closed set of output formats (unittest, pytest, bun, jest, go test, cargo test,
vitest, mocha, JUnit XML) is parsed into a
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
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable
from typing import Any

from .canonical_json import canonical_bytes

# The most identifiers one fingerprint keeps. A larger failing set is unparsed;
# a larger passing set is dropped, which only withholds disjoint-move progress.
MAX_IDENTIFIERS = 2000
MAX_IDENTIFIER_LENGTH = 240
_JUNIT_START = re.compile(r"^\s*<(?:\?xml\b[^>]*\?>\s*<)?testsuites?[\s>]", re.M)


def _junit_cases(text: str) -> list[ElementTree.Element] | None:
    """Every `testcase` of the JUnit XML document in the output, or None when it is not one well-formed document.

    A document type or entity declaration is refused, so no entity can expand.
    """
    start = _JUNIT_START.search(text)
    if start is None or "<!DOCTYPE" in text or "<!ENTITY" in text:
        return None
    body = text[start.start():]
    close = max(body.rfind("</testsuites>"), body.rfind("</testsuite>"))
    if close < 0:
        return None
    try:
        return list(ElementTree.fromstring(body[:body.index(">", close) + 1]).iter("testcase"))
    except ElementTree.ParseError:
        return None


def _junit_id(case: ElementTree.Element) -> str:
    classname, name = case.get("classname", ""), case.get("name", "")
    return f"{classname}.{name}" if classname and name else classname or name


def _junit_checks(text: str) -> int | None:
    cases = _junit_cases(text)
    return None if cases is None else len(cases)


def _junit_failing(text: str) -> list[str] | None:
    cases = _junit_cases(text)
    return None if cases is None else _bounded({_identifier(_junit_id(case)) for case in cases
                                                if case.find("failure") is not None or case.find("error") is not None})


def _junit_passing(text: str) -> list[str] | None:
    cases = _junit_cases(text)
    return None if cases is None else _bounded({_identifier(_junit_id(case)) for case in cases
                                                if not {child.tag for child in case} & {"failure", "error", "skipped"}})


MOCHA_TITLE = re.compile(r"^ {2}\d+\) (.+)$")
MOCHA_TITLE_PART = re.compile(r"^ {5,}(\S.*)$")


def _mocha_failing(text: str) -> list[str] | None:
    """The full title of each entry in mocha's failure list, which follows its `N failing` line."""
    lines = text.split("\n")
    start = next((index for index, line in enumerate(lines) if re.fullmatch(r" +\d+ failing", line)), None)
    if start is None:
        return None
    found: set[str] = set()
    parts: list[str] | None = None
    for line in lines[start + 1:]:
        if parts is None:
            head = MOCHA_TITLE.match(line)
            parts = [head.group(1)] if head else None
        elif (part := MOCHA_TITLE_PART.match(line)) is not None:
            parts.append(part.group(1))
        else:
            parts = None
            continue
        if parts is not None and parts[-1].endswith(":"):
            parts[-1] = parts[-1][:-1]
            found.add(_identifier(" ".join(parts)))
            parts = None
    return _bounded(found)


Extractor = re.Pattern[str] | Callable[[str], list[str] | None] | None
FORMATS: dict[str, dict[str, Any]] = {
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
    # `go test`: the package line marks the run, and every `=== RUN` line (printed only with `-v`) is one check.
    # A plain run does not say how many checks ran, so its count is unknown, never the failure count.
    "go": {"marker": re.compile(r"^(?:ok|FAIL)\s+\S+\s+(?:[\d.]+s|\(cached\))(?:\s.*)?$", re.M),
           "count": re.compile(r"^=== RUN ", re.M),
           "failing": re.compile(r"^ *--- FAIL: (\S+)", re.M),
           "passing": re.compile(r"^ *--- PASS: (\S+)", re.M)},
    "cargo": {"marker": re.compile(r"^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;", re.M),
              "failing": re.compile(r"^test (.+?) \.\.\. FAILED$", re.M),
              "passing": re.compile(r"^test (.+?) \.\.\. ok$", re.M)},
    "vitest": {"marker": re.compile(r"^ +Tests +(?:\d+ \w+ \| )*\d+ \w+ \((\d+)\)$", re.M),
               "failing": re.compile(r"^ FAIL  (.+?)$", re.M),
               "passing": None},
    "mocha": {"marker": re.compile(r"^ +(\d+) passing(?: \(\d+m?s\))?$", re.M),
              "count": re.compile(r"^ +(\d+) (?:passing|failing|pending)\b", re.M),
              "failing": _mocha_failing,
              "passing": None},
    "junit": {"marker": _JUNIT_START,
              "failing": _junit_failing,
              "passing": _junit_passing},
}


def _identifier(text: str) -> str:
    """One normalized identifier; an overlong one is replaced by its digest so it cannot collide."""
    text = " ".join(text.split())
    if len(text) <= MAX_IDENTIFIER_LENGTH:
        return text
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bounded(found: set[str]) -> list[str] | None:
    return sorted(found) if len(found) <= MAX_IDENTIFIERS else None


def _identifiers(extractor: Extractor, text: str) -> list[str] | None:
    if extractor is None:
        return None
    if callable(extractor):
        return extractor(text)
    return _bounded({_identifier(match) for match in extractor.findall(text)})


PYTEST_COUNTS = re.compile(r"(\d+) (?:passed|failed|errors?|skipped|xfailed|xpassed)\b")


def _checks_run(name: str, text: str) -> int | None:
    """The number of checks the run reports: its own summary count, summed across summaries."""
    patterns = FORMATS[name]
    if name == "pytest":
        return sum(int(count) for line in patterns["marker"].findall(text) for count in PYTEST_COUNTS.findall(line))
    if name == "junit":
        return _junit_checks(text)
    if name == "go":
        return len(patterns["count"].findall(text)) or None
    if name == "cargo":
        return sum(int(count) for counts in patterns["marker"].findall(text) for count in counts)
    if name == "mocha":
        return sum(int(count) for count in patterns["count"].findall(text))
    return sum(int(count) for count in patterns["marker"].findall(text))


def fingerprint(command_id: str, argv: list[str], exit_code: int | None, completed: bool, stdout: bytes,
                stderr: bytes) -> dict[str, Any]:
    """The failing-check set one verification run shows.

    A failing or incomplete run whose output is not exactly one known format records `failing: None`.
    A zero exit in no single known format records `format: "passed"` with an empty set and no
    `checks_run`: nothing failed, and the unknown count can never admit a convergence correction.
    """
    output = stdout + b"\n" + stderr
    text = output.decode("utf-8", errors="replace").replace("\r\n", "\n")
    record: dict[str, Any] = {"command_id": command_id,
                              "command_sha256": hashlib.sha256(canonical_bytes(argv)).hexdigest(),
                              "format": "unparsed", "failing": None, "passing": None, "checks_run": None,
                              "output_sha256": hashlib.sha256(output).hexdigest()}
    formats = [name for name, patterns in FORMATS.items() if patterns["marker"].search(text)]
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

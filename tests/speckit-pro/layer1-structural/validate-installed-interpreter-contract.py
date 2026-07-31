#!/usr/bin/env python3
"""Validate that shipped plugin prose never hardcodes a Python interpreter name.

The Installed Runtime Contract requires every installed Claude and Codex surface
to resolve Python 3.11+ and invoke it as ``resolved_python``. Prose is the only
place that contract is expressed to an agent, so prose is the only place it can
be broken: a skill that literally says ``python3 …`` tells the agent to run a
command that does not exist on a stock Windows install, and both platforms read
a nonzero exit as blocking.

Two things are checked. The class check scans every shipped markdown file for a
bare interpreter used as a command. The call-site check pins the phase-coverage
guard invocation in all four autopilot surfaces, because that one is load-bearing
— the Claude and Codex variants must name the same script with the same scoping
flag or the two distributions silently enforce different rules.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
# Generated release history quotes old commit subjects verbatim ("resolve python
# interpreter on windows"), which is prose about the fix, not an instruction.
EXCLUDED_NAMES = frozenset({"CHANGELOG.md"})

# A bare interpreter used as a command: not preceded by an identifier character,
# a dot, a slash or a hyphen — so `resolved_python`, `/usr/bin/python3` and
# `some-python` are left alone — and followed by whitespace plus an argument.
HARDCODED_INTERPRETER = re.compile(r"(?<![\w./-])(?:python[0-9.]*|py)\s+(?=[-\w\"'/$])")

RESOLVED_TOKEN = "resolved_python"
COVERAGE_SCRIPT = "validate-autopilot-phase-coverage.py"
COVERAGE_RULE_FLAG = "--rule status-evidence"
# Every surface that tells an agent to run the phase-coverage guard.
COVERAGE_CALL_SITES = (
    Path("speckit-pro/skills/speckit-autopilot/SKILL.md"),
    Path("speckit-pro/codex-skills/speckit-autopilot/SKILL.md"),
    Path("speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md"),
)

POSITIVE_CASES = (
    'python3 "runner helper validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE"',
    "python3 -m json.tool docs/ai/specs/.process/autopilot-state.json",
    "python3 tests/speckit-pro/run-all.py",
    "- `python -m venv .venv`",
    "Run python3.11 scripts/build.py to regenerate",
    "py -3 scripts/build.py",
)
NEGATIVE_CASES = (
    "resolved_python -m speckit_pro_runner < request.json",
    'resolved_python "<plugin-root>/skills/speckit-autopilot/scripts/validate.py" --rule x',
    '`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on',
    "Keep repository-owned tooling on Python 3.11+ standard library.",
    "resolve Python 3.11 or newer, invoke",
    "#!/usr/bin/env python3",
    "the interpreter at /usr/bin/python3 is not guaranteed",
    "`resolved_python` is the Python 3.11+ interpreter resolved by the installed",
)


def shipped_markdown() -> list[Path]:
    """Every shipped plugin markdown file, in deterministic order."""
    return sorted(
        path
        for path in PLUGIN_ROOT.rglob("*.md")
        if path.name not in EXCLUDED_NAMES
    )


def hardcoded_interpreter_errors() -> list[str]:
    """Plain-English `file:line` strings for every hardcoded interpreter command."""
    errors: list[str] = []
    for path in shipped_markdown():
        display = path.relative_to(REPO_ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{display}: unreadable ({exc})")
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for match in HARDCODED_INTERPRETER.finditer(line):
                errors.append(
                    f"{display}:{number}: {match.group(0).strip()!r} hardcodes an"
                    f" interpreter; the Installed Runtime Contract requires"
                    f" {RESOLVED_TOKEN!r}"
                )
    return errors


def coverage_invocation_errors() -> list[str]:
    """Every autopilot surface must invoke the guard the same resolvable way."""
    errors: list[str] = []
    for relative in COVERAGE_CALL_SITES:
        path = REPO_ROOT / relative
        display = relative.as_posix()
        if not path.is_file():
            errors.append(f"{display}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        invocations = [
            (number, line)
            for number, line in enumerate(text.splitlines(), start=1)
            if COVERAGE_SCRIPT in line and ("--workflow" in line or "--state" in line)
        ]
        if not invocations:
            errors.append(f"{display}: no {COVERAGE_SCRIPT} invocation found")
            continue
        for number, line in invocations:
            if RESOLVED_TOKEN not in line:
                errors.append(
                    f"{display}:{number}: guard invocation does not name {RESOLVED_TOKEN!r}"
                )
            if COVERAGE_RULE_FLAG not in line:
                errors.append(
                    f"{display}:{number}: guard invocation omits {COVERAGE_RULE_FLAG!r},"
                    f" so this surface gates on checks the other surface does not"
                )
    return errors


class ValidateInstalledInterpreterContract(unittest.TestCase):
    def test_installed_interpreter_contract(self) -> None:
        files = shipped_markdown()
        with self.subTest(msg="shipped plugin markdown is discoverable"):
            self.assertTrue(files, f"no *.md files under {PLUGIN_ROOT}")

        with self.subTest(msg="no shipped prose hardcodes a Python interpreter name"):
            errors = hardcoded_interpreter_errors()
            self.assertEqual([], errors, "\n".join(errors))

        with self.subTest(msg="every phase-coverage guard invocation is resolvable and identically scoped"):
            errors = coverage_invocation_errors()
            self.assertEqual([], errors, "\n".join(errors))

        with self.subTest(msg="matcher catches every hardcoded-interpreter form"):
            missed = [case for case in POSITIVE_CASES if not HARDCODED_INTERPRETER.search(case)]
            self.assertEqual([], missed, "\n".join(missed))

        with self.subTest(msg="matcher accepts resolved_python, shebangs, and Python-version prose"):
            matched = [case for case in NEGATIVE_CASES if HARDCODED_INTERPRETER.search(case)]
            self.assertEqual([], matched, "\n".join(matched))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateInstalledInterpreterContract)


def main() -> int:
    return run_counted(build_suite(), label="validate-installed-interpreter-contract")


if __name__ == "__main__":
    raise SystemExit(main())

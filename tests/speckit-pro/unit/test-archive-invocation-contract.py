#!/usr/bin/env python3
"""Every archive invocation the skills prescribe must parse as one feature.

The stock archive extension (stn1slv/spec-kit-archive) archives exactly one
feature per run. Its input contract requires the first token to be the feature
directory, recognizes only four scope modifiers in the leading flag position,
and rejects a second feature reference, a range, or a glob. The rules below
restate that contract; a prescribed invocation that breaks one of them blocks a
consumer repository before Phase 0.

The vendored fork in `.specify/extensions/archive` also accepts the positional
single-feature form, which the last test pins, so one prescribed form works for
both installations.
"""

from pathlib import Path
import re
import sys
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "tests/speckit-pro/lib")]
from test_result import run_counted  # noqa: E402

SKILL_ROOTS = {
    "claude": REPO / "speckit-pro/skills",
    "codex": REPO / "speckit-pro/codex-skills",
}
AUTOPILOT_DIRS = {
    "claude": REPO / "speckit-pro/skills/speckit-autopilot",
    "codex": REPO / "speckit-pro/codex-skills/speckit-autopilot",
}
VENDORED_COMMAND = REPO / ".specify/extensions/archive/commands/archive.md"

# An invocation is the command name followed by arguments on the same line, up
# to the end of an inline code span. A bare mention such as `/speckit-archive-run`
# followed by a backtick carries no arguments and is not an invocation.
INVOCATION = re.compile(
    r"(?:/speckit-archive-run|/speckit\.archive\.run|\$speckit-archive-run|archive command:)[ \t]+([^`\n]+)"
)
SCOPE_MODIFIERS = frozenset({"--spec-only", "--plan-only", "--changelog-only", "--agent-only"})
PATH_SHAPED = re.compile(r"(?:^|/)specs/[^/\s]+")
BARE_FEATURE = re.compile(r"^\d{3,}(?:-|$)")


def stock_parse_errors(arguments: str) -> list[str]:
    """Apply the stock single-feature input rules; return every rule broken."""
    tokens = arguments.split()
    if not tokens or tokens[0].startswith("--"):
        return ["no feature directory in the first position"]
    errors: list[str] = []
    if not PATH_SHAPED.search(tokens[0]):
        errors.append(f"first token {tokens[0]!r} is not a specs/<feature> path")
    feature_tokens = [token for token in tokens if PATH_SHAPED.search(token) or BARE_FEATURE.match(token)]
    if len(feature_tokens) != 1:
        errors.append(f"expected exactly one feature reference, found {feature_tokens}")
    if any(glob in tokens[0] for glob in "*?"):
        errors.append("glob in the feature reference")
    for token in tokens[1:]:
        if not token.startswith("--"):
            break
        if token not in SCOPE_MODIFIERS:
            errors.append(f"unrecognized flag {token!r}")
    return errors


def prescribed_invocations(root: Path) -> list[tuple[str, int, str]]:
    found: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in INVOCATION.finditer(line):
                found.append((path.relative_to(REPO).as_posix(), number, match.group(1).strip()))
    return found


class ArchiveInvocationContractTests(unittest.TestCase):
    def test_parser_rejects_the_sweep_form_and_accepts_the_single_feature_form(self) -> None:
        self.assertTrue(stock_parse_errors("--sweep --current-target specs/007-current --dry-run"))
        self.assertTrue(stock_parse_errors("specs/007-a --dry-run"))
        self.assertTrue(stock_parse_errors("specs/007-a specs/008-b"))
        self.assertEqual([], stock_parse_errors("specs/007-invoice-settings"))
        self.assertEqual([], stock_parse_errors("specs/<merged-spec-dir> --changelog-only"))

    def test_each_host_prescribes_an_autopilot_archive_invocation(self) -> None:
        for host, directory in AUTOPILOT_DIRS.items():
            with self.subTest(host=host):
                self.assertTrue(prescribed_invocations(directory), f"no archive invocation under {directory}")

    def test_every_prescribed_invocation_parses_as_one_feature(self) -> None:
        for host, root in SKILL_ROOTS.items():
            for path, number, arguments in prescribed_invocations(root):
                with self.subTest(host=host, location=f"{path}:{number}", arguments=arguments):
                    self.assertEqual([], stock_parse_errors(arguments))

    def test_vendored_extension_accepts_the_positional_single_feature_form(self) -> None:
        text = VENDORED_COMMAND.read_text(encoding="utf-8")
        self.assertIn("speckit.archive.run specs/###-feature-name", text)
        self.assertIn("First non-option token: feature spec directory path", text)


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.defaultTestLoader.loadTestsFromTestCase(ArchiveInvocationContractTests),
            label="test-archive-invocation-contract",
        )
    )

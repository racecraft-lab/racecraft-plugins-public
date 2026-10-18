#!/usr/bin/env python3
"""Every Codex subagent spawn passes `fork_turns="none"`.

Codex defaults an omitted `fork_turns` to `"all"`, which copies the caller's whole
history into the child (openai/codex `multi_agents_v2/spawn.rs`, rust-v0.160.0).
A fresh child already gets a self-contained task message, so the copy is pure
input cost, repeated for every child (#1317).
"""

from __future__ import annotations

import ast
import io
import json
import re
import tempfile
import sys
import tomllib
import tokenize
import unittest
from pathlib import Path
from unittest.mock import patch

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path[:0] = [str(TEST_DIR.parent / "lib")]

from host_skill_views import host_skill_root  # noqa: E402
from test_result import run_counted  # noqa: E402

FORK = 'fork_turns="none"'
# Discover all concrete calls, independent of argument order or line wrapping.
DISPATCH = re.compile(r"\bspawn_agent\s*\(")
PROSE_INVENTORY = TEST_DIR / "fixtures/codex-spawn-reviewed-prose.json"


def call_tokens(text: str) -> tuple[int, list[tokenize.TokenInfo]]:
    """Read one balanced call; never borrow tokens from a subsequent comment/call."""
    tokens = []
    depth = 0
    lines = text.splitlines(keepends=True)
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type in (tokenize.NL, tokenize.NEWLINE):
                continue
            if token.type not in {
                tokenize.NAME, tokenize.NUMBER, tokenize.STRING, tokenize.OP,
                tokenize.COMMENT, tokenize.ENDMARKER,
            }:
                raise AssertionError(f"unsupported call token: {token.type}")
            tokens.append(token)
            if token.type == tokenize.OP:
                depth += int(token.string in "([{") - int(token.string in ")]}")
                if depth == 0 and token.string == ")":
                    row, column = token.end
                    return sum(map(len, lines[:row - 1])) + column, tokens
    except (tokenize.TokenError, IndentationError) as error:
        raise AssertionError(f"unreadable spawn_agent call: {error}") from error
    raise AssertionError("unterminated spawn_agent call")


def dispatch_sites(text: str) -> list[tuple[int, int, list[tokenize.TokenInfo]]]:
    return [(match.start(), match.start() + length, tokens)
            for match in DISPATCH.finditer(text)
            for length, tokens in [call_tokens(text[match.start():])]]


def call_arguments(tokens: list[tokenize.TokenInfo]) -> list[list[str]]:
    """Split only at commas in the outer call, retaining nested values as tokens."""
    arguments: list[list[str]] = [[]]
    depth = 0
    for token in tokens[2:-1]:
        if token.type == tokenize.COMMENT:
            continue
        if token.type == tokenize.OP:
            if token.string == "," and depth == 0:
                arguments.append([])
                continue
            depth += int(token.string in "([{") - int(token.string in ")]}")
        arguments[-1].append(token.string)
    return [argument for argument in arguments if argument]


def passes_fork_none(tokens: list[tokenize.TokenInfo]) -> bool:
    arguments = call_arguments(tokens)
    forks = [argument for argument in arguments if argument[0] == "fork_turns"]
    if len(forks) != 1 or any(argument[0] == "**" for argument in arguments):
        return False
    fork = forks[0]
    if len(fork) != 3 or fork[1] != "=":
        return False
    try:
        return ast.literal_eval(fork[2]) == "none"
    except (ValueError, SyntaxError):
        return False


def prose_blocks(text: str) -> list[str]:
    """Unknown prose fails closed rather than guessing its intent from a verb/window.

    Reviewed blocks are literal, human-readable evidence, not auto-updated snapshots.
    Include fork-only blocks so a contradictory instruction cannot hide elsewhere.
    Concrete calls are checked structurally and cannot supply a prose marker.
    """
    argument_text = []
    # Keep character offsets stable even for nested/overlapping call spans.
    # Whitespace on both sides prevents the mask from swallowing a word boundary.
    masked = list(text)
    for start, end, tokens in reversed(dispatch_sites(text)):
        for token in tokens:
            if token.type == tokenize.STRING:
                try:
                    argument_text.append(str(ast.literal_eval(token.string)))
                except (ValueError, SyntaxError) as error:
                    raise AssertionError("unsupported argument string") from error
            elif token.type == tokenize.COMMENT:
                argument_text.append(token.string)
        masked[start:end] = " CALL ".ljust(end - start)
    blocks = re.split(r"\n\s*\n", "".join(masked)) + argument_text
    return [" ".join(block.split()) for block in blocks
            if re.search(r"\b(?:spawn_agent|fork_turns)\b", block)]


def skill_paths(root: Path) -> list[Path]:
    """Scan every shipped text surface, including renamed/linked references."""
    paths = sorted(root.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise AssertionError(f"unreviewed skill symlink: {path.relative_to(root)}")
    return [path for path in paths if path.is_file()]


def assert_reviewed_prose(test: unittest.TestCase, key: str, text: str) -> None:
    inventory = json.loads(PROSE_INVENTORY.read_text(encoding="utf-8"))
    test.assertIn(key, inventory, f"unreviewed dispatch surface: {key}")
    for block in prose_blocks(text):
        test.assertIn(block, inventory[key], f"review dispatch prose explicitly: {key}: {block}")


class CodexSpawnForkTests(unittest.TestCase):
    def test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none(self) -> None:
        root = host_skill_root("codex")
        sites = 0
        for path in skill_paths(root):
            for start, _, tokens in dispatch_sites(path.read_text(encoding="utf-8", errors="replace")):
                sites += 1
                with self.subTest(file=str(path.relative_to(root)), offset=start):
                    self.assertTrue(passes_fork_none(tokens), f"missing literal {FORK} in call")
        self.assertGreater(sites, 0, "no dispatch examples found: the scan matched nothing")

    def test_every_codex_agent_that_dispatches_states_the_rule(self) -> None:
        checked = []
        for path in sorted((REPO_ROOT / "speckit-pro/codex-agents").glob("*.toml")):
            text = tomllib.loads(path.read_text(encoding="utf-8"))["developer_instructions"]
            if "spawn_agent" in text or "fork_turns" in text:
                checked.append(path.stem)
                with self.subTest(agent=path.stem):
                    self.assertIn(FORK, text)
                    assert_reviewed_prose(self, "agents/" + path.name, text)
                    for _, _, tokens in dispatch_sites(text):
                        self.assertTrue(passes_fork_none(tokens))
        self.assertGreaterEqual(len(checked), 4, checked)

    def test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none(self) -> None:
        root = host_skill_root("codex")
        for path in skill_paths(root):
            text = path.read_text(encoding="utf-8", errors="replace")
            if prose_blocks(text):
                with self.subTest(file=str(path.relative_to(root))):
                    assert_reviewed_prose(self, "skills/" + path.relative_to(root).as_posix(), text)

    def test_the_autopilot_names_the_default_that_costs_tokens(self) -> None:
        text = " ".join((host_skill_root("codex") / "speckit-autopilot/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn(f"Every `spawn_agent` call passes `{FORK}`", text)


class CodexSpawnGateFaultTests(unittest.TestCase):
    """Inject contributor-controlled text through the same gates as shipped files."""

    def assert_skill_rejected(
        self, snippet: str, method: str, relative: str = "speckit-autopilot/SKILL.md",
    ) -> None:
        source = host_skill_root("codex") / "speckit-autopilot/SKILL.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / relative
            target.parent.mkdir(parents=True)
            target.write_text(source.read_text(encoding="utf-8") + "\n\n" + snippet, encoding="utf-8")
            result = unittest.TestResult()
            with patch(__name__ + ".host_skill_root", return_value=root):
                CodexSpawnForkTests(method).run(result)
            self.assertFalse(result.wasSuccessful(), "gate accepted: " + snippet)
            self.assertFalse(result.errors, result.errors)

    def test_task_name_first_call_is_rejected(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(task_name="job", agent_type="phase-executor", message="work")',
            "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none")

    def test_space_after_opening_parenthesis_is_rejected(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent( agent_type="phase-executor", message="work")',
            "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none")

    def test_multiline_call_opening_is_rejected(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(\n    agent_type="phase-executor", message="work")',
            "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none")

    def test_adjacent_comment_cannot_supply_the_argument(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(agent_type="phase-executor", message="work")\n# fork_turns="none"',
            "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none")

    def test_unrecognized_prose_dispatch_verb_is_rejected(self) -> None:
        self.assert_skill_rejected(
            'Spawn a child using `spawn_agent` with `agent_type="phase-executor"`.',
            "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_unrelated_prose_cannot_supply_the_argument(self) -> None:
        self.assert_skill_rejected(
            'An unrelated example uses `fork_turns="none"`.\n'
            'Dispatch with `spawn_agent` using `agent_type="phase-executor"`.',
            "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_markers_in_other_arguments_or_calls_are_rejected(self) -> None:
        for snippet in (
            'spawn_agent(task_name="job", message=\'fork_turns="none"\')',
            'spawn_agent(agent_type="phase-executor", options={"fork_turns": "none"})',
            'spawn_agent(agent_type="phase-executor") # fork_turns="none"',
            'spawn_agent(agent_type="phase-executor")\n'
            'spawn_agent(agent_type="phase-executor", fork_turns="none")',
            'spawn_agent(agent_type="phase-executor", # fork_turns="none"\n message="work")',
        ):
            with self.subTest(snippet=snippet):
                self.assert_skill_rejected(
                    snippet, "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none")

    def test_nested_calls_cannot_erase_following_prose(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(fork_turns="none", message=spawn_agent(fork_turns="none"))'
            'fork_turns="all" for children.',
            "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_call_mask_cannot_hide_an_adjacent_identifier(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(fork_turns="none")fork_turns="all" for children.',
            "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_formatted_string_token_kinds_fail_closed(self) -> None:
        # Model a tokenizer that splits a formatted/template string into new kinds.
        token_kind = max(tokenize.tok_name) + 1
        tokens = [
            tokenize.TokenInfo(tokenize.NAME, "spawn_agent", (1, 0), (1, 11), ""),
            tokenize.TokenInfo(tokenize.OP, "(", (1, 11), (1, 12), ""),
            tokenize.TokenInfo(token_kind, 'fork_turns="all"', (1, 12), (1, 28), ""),
            tokenize.TokenInfo(tokenize.OP, ")", (1, 28), (1, 29), ""),
        ]
        with patch.object(tokenize, "generate_tokens", return_value=iter(tokens)):
            with self.assertRaisesRegex(AssertionError, "unsupported.*token"):
                prose_blocks('spawn_agent(fork_turns="all")')

    def test_formatted_argument_strings_fail_closed(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(fork_turns="none", message=f\'Use fork_turns="all" for children.\')',
            "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_prompt_cannot_hide_conflicting_child_instructions(self) -> None:
        self.assert_skill_rejected(
            'spawn_agent(task_name="job", fork_turns="none", '
            'message=\'For the next child, use fork_turns="all".\')',
            "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_conflicting_or_dynamic_call_arguments_are_rejected(self) -> None:
        for arguments in (
            'fork_turns="all"', 'fork_turns=None', 'fork_turns=mode',
            'fork_turns="none", fork_turns="all"', 'fork_turns="none", **options',
        ):
            with self.subTest(arguments=arguments):
                self.assert_skill_rejected(
                    f'spawn_agent(task_name="job", {arguments})',
                    "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none")

    def test_valid_call_formatting_is_accepted(self) -> None:
        for snippet in (
            'spawn_agent(task_name="job", fork_turns="none", agent_type="phase-executor")',
            "spawn_agent (\n task_name='job',\n fork_turns = 'none',\n message='done)',\n)",
            'collaboration.spawn_agent(agent_type="phase-executor", message={"steps": [1, 2]}, fork_turns="none")',
            'spawn_agent("phase-executor", fork_turns="none", prompt="""work (now)""")',
        ):
            with self.subTest(snippet=snippet):
                sites = dispatch_sites(snippet)
                self.assertEqual(len(sites), 1)
                self.assertTrue(passes_fork_none(sites[0][2]))

    def test_new_or_recontextualized_prose_is_rejected(self) -> None:
        for snippet in (
            'Launch a child through `spawn_agent`.',
            'Every `spawn_agent` call passes `fork_turns="none"`. Except this one: use "all".',
            'Dispatch with `spawn_agent`.\n\nAn unrelated example uses `fork_turns="none"`.',
            'Use `fork_turns="all"` for the next child.',
        ):
            with self.subTest(snippet=snippet):
                self.assert_skill_rejected(
                    snippet, "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none")

    def test_renamed_or_new_reference_is_scanned(self) -> None:
        for relative in ("speckit-autopilot/references/new.txt", "other/new.markdown", "other/new.data"):
            self.assert_skill_rejected(
                'spawn_agent(task_name="job", agent_type="phase-executor")',
                "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none", relative)

    def test_linked_skill_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "target").write_text('spawn_agent(task_name="job")', encoding="utf-8")
            (root / "linked.md").symlink_to(root / "target")
            with self.assertRaisesRegex(AssertionError, "skill symlink"):
                skill_paths(root)

    def test_shipped_codex_payload_passes_the_same_gates(self) -> None:
        payload = REPO_ROOT / "dist/codex"
        result = unittest.TestResult()
        with patch(__name__ + ".REPO_ROOT", payload), patch(
            __name__ + ".host_skill_root", return_value=payload / "speckit-pro/skills",
        ):
            for method in (
                "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none",
                "test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none",
                "test_every_codex_agent_that_dispatches_states_the_rule",
            ):
                CodexSpawnForkTests(method).run(result)
        self.assertTrue(result.wasSuccessful(), (result.failures, result.errors))

    def test_conflicting_agent_instruction_is_rejected(self) -> None:
        agents = REPO_ROOT / "speckit-pro/codex-agents"
        sources = {path.name: tomllib.loads(path.read_text(encoding="utf-8"))["developer_instructions"]
                   for path in agents.glob("*.toml")}
        dispatchers = [name for name, text in sources.items() if "spawn_agent" in text]
        self.assertGreaterEqual(len(dispatchers), 4)
        for name in dispatchers:
            for conflict in (
                'For the next child, use `fork_turns="all"` with `spawn_agent`.',
                'For the next child, use `fork_turns="all"`.',
                'spawn_agent(task_name="child", fork_turns="all")',
            ):
                with self.subTest(agent=name, conflict=conflict):
                    self.assert_agent_rejected(sources, name, conflict)

    def assert_agent_rejected(self, sources: dict[str, str], name: str, conflict: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            agents = root / "speckit-pro/codex-agents"
            agents.mkdir(parents=True)
            for filename, original in sources.items():
                text = original + ("\n\n" + conflict if filename == name else "")
                (agents / filename).write_text("developer_instructions = " + json.dumps(text, ensure_ascii=False), encoding="utf-8")
            result = unittest.TestResult()
            with patch(__name__ + ".REPO_ROOT", root):
                CodexSpawnForkTests("test_every_codex_agent_that_dispatches_states_the_rule").run(result)
            self.assertFalse(result.wasSuccessful(), "gate accepted conflicting agent instructions")
            self.assertFalse(result.errors, result.errors)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-codex-spawn-fork-turns"))

#!/usr/bin/env python3
"""Every Codex subagent spawn passes `fork_turns="none"`.

Codex defaults an omitted `fork_turns` to `"all"`, which copies the caller's whole
history into the child (openai/codex `multi_agents_v2/spawn.rs`, rust-v0.160.0).
A fresh child already gets a self-contained task message, so the copy is pure
input cost, repeated for every child (#1317).

Both rules derive from the files themselves, with no reviewed-content fixture:
every `spawn_agent(` call passes the literal argument, and every file that names
`spawn_agent` states the argument. Natural-language intent is left to review.
"""

from __future__ import annotations

import ast
import io
import re
import shutil
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
# The rule as a file states it, in call form or in key-value form.
RULE = re.compile(r'fork_turns(?:="none"|: "none")')
MENTION = re.compile(r"\bspawn_agent\b")
# Discover all concrete calls, independent of argument order or line wrapping.
DISPATCH = re.compile(r"\bspawn_agent\s*\(")
# A directory holding this notice is a vendored upstream tree (Quint references).
VENDOR_NOTICE = "UPSTREAM-NOTICE.md"
LOCKFILE = re.compile(r"(?:-lock\.json|-lock\.yaml|\.lock)$")
SKILL_GATES = (
    "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none",
    "test_every_codex_skill_file_that_dispatches_states_the_rule",
)


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


def call_arguments(tokens: list[tokenize.TokenInfo]) -> list[list[tokenize.TokenInfo]]:
    """Split only at commas in the outer call, retaining nested values as tokens."""
    arguments: list[list[tokenize.TokenInfo]] = [[]]
    depth = 0
    for token in tokens[2:-1]:
        if token.type == tokenize.COMMENT:
            continue
        if token.type == tokenize.OP:
            if token.string == "," and depth == 0:
                arguments.append([])
                continue
            depth += int(token.string in "([{") - int(token.string in ")]}")
        arguments[-1].append(token)
    return [argument for argument in arguments if argument]


def passes_fork_none(tokens: list[tokenize.TokenInfo]) -> bool:
    arguments = [[token.string for token in argument] for argument in call_arguments(tokens)]
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


def read_surface(path: Path) -> str:
    """Decode strictly: an unreadable file fails the gate instead of being skipped."""
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise AssertionError(f"unreadable dispatch surface: {path.name}: {error}") from error


def is_dispatch_surface(root: Path, path: Path) -> bool:
    """Skip only the kinds that cannot dispatch; any other file kind stays in scope."""
    relative = path.relative_to(root)
    if "scripts" in relative.parts[:-1] and path.suffix == ".py":
        return False
    if path.name.endswith(".schema.json") or LOCKFILE.search(path.name):
        return False
    return not any((root.joinpath(*relative.parts[:depth]) / VENDOR_NOTICE).is_file()
                   for depth in range(1, len(relative.parts)))


def skill_paths(root: Path) -> list[Path]:
    """Every file a Codex agent can read as instructions, including renamed references."""
    paths = sorted(root.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise AssertionError(f"unreviewed skill symlink: {path.relative_to(root)}")
    return [path for path in paths if path.is_file() and is_dispatch_surface(root, path)]


class CodexSpawnForkTests(unittest.TestCase):
    def test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none(self) -> None:
        root = host_skill_root("codex")
        sites = 0
        for path in skill_paths(root):
            for start, _, tokens in dispatch_sites(read_surface(path)):
                sites += 1
                with self.subTest(file=str(path.relative_to(root)), offset=start):
                    self.assertTrue(passes_fork_none(tokens), f"missing literal {FORK} in call")
        self.assertGreater(sites, 0, "no dispatch examples found: the scan matched nothing")

    def test_every_codex_skill_file_that_dispatches_states_the_rule(self) -> None:
        root = host_skill_root("codex")
        checked = []
        for path in skill_paths(root):
            relative = path.relative_to(root).as_posix()
            if MENTION.search(text := read_surface(path)):
                checked.append(relative)
                with self.subTest(file=relative):
                    self.assertRegex(text, RULE, f"names spawn_agent without stating {FORK}")
        self.assertIn("speckit-autopilot/SKILL.md", checked, "the scan matched no dispatcher")

    def test_every_codex_agent_that_dispatches_states_the_rule(self) -> None:
        checked = []
        for path in skill_paths(REPO_ROOT / "speckit-pro/codex-agents"):
            source = read_surface(path)
            try:
                text = tomllib.loads(source)["developer_instructions"]
            except (tomllib.TOMLDecodeError, KeyError) as error:
                raise AssertionError(f"unreadable agent file: {path.name}: {error}") from error
            if MENTION.search(source):
                checked.append(path.stem)
                with self.subTest(agent=path.stem):
                    self.assertIn(FORK, text)
                    for _, _, tokens in dispatch_sites(source):
                        self.assertTrue(passes_fork_none(tokens))
        self.assertGreaterEqual(len(checked), 4, checked)

    def test_the_autopilot_names_the_default_that_costs_tokens(self) -> None:
        text = " ".join((host_skill_root("codex") / "speckit-autopilot/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn(f"Every `spawn_agent` call passes `{FORK}`", text)


def agent_instruction_sources() -> dict[str, str]:
    """Load complete agent files so fault fixtures preserve untouched bytes."""
    agents = REPO_ROOT / "speckit-pro/codex-agents"
    return {path.name: path.read_bytes().decode("utf-8") for path in sorted(agents.glob("*.toml"))}


class CodexSpawnGateFaultTests(unittest.TestCase):
    """Inject contributor-controlled text through the same gates as shipped files."""

    def run_skill_gates(self, edits: dict[str, tuple[str, str | bytes]]) -> unittest.TestResult:
        """Run every skill gate on a copy of the rendered tree with `edits` applied.

        Each edit replaces one exact `old` string, or appends when `old` is empty.
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            shutil.copytree(host_skill_root("codex"), root)
            for relative, (old, new) in edits.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(new, bytes):
                    target.write_bytes(new)
                    continue
                text = target.read_text(encoding="utf-8") if target.exists() else ""
                if old:
                    self.assertEqual(text.count(old), 1, relative)
                target.write_text(text.replace(old, new, 1) if old else text + new, encoding="utf-8")
            result = unittest.TestResult()
            with patch(__name__ + ".host_skill_root", return_value=root):
                for method in SKILL_GATES:
                    CodexSpawnForkTests(method).run(result)
            return result

    def assert_skill_gates_reject(self, edits: dict[str, tuple[str, str | bytes]]) -> None:
        result = self.run_skill_gates(edits)
        self.assertFalse(result.wasSuccessful(), f"gate accepted: {edits}")
        self.assertFalse(result.errors, result.errors)

    def assert_skill_gates_accept(self, edits: dict[str, tuple[str, str | bytes]]) -> None:
        result = self.run_skill_gates(edits)
        self.assertTrue(result.wasSuccessful(), (result.failures, result.errors))

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

    def test_wording_only_skill_edits_are_accepted(self) -> None:
        for relative, edit in (
            ("speckit-coach/SKILL.md", ("", "\nAsk one question at a time.\n")),
            ("speckit-autopilot/SKILL.md", (
                "and keep orchestration in the parent.\n",
                "and keep the orchestration in the parent session.\n")),
        ):
            with self.subTest(file=relative):
                self.assert_skill_gates_accept({relative: edit})

    def test_real_call_without_the_argument_is_rejected(self) -> None:
        self.assert_skill_gates_reject({"speckit-autopilot/references/phase-driver.md": (
            "", '\n```text\nspawn_agent(agent_type="clarify-executor", message="work")\n```\n')})

    def test_dispatch_line_without_the_rule_is_rejected(self) -> None:
        # The phase driver reads only its own reference at dispatch (#1369).
        self.assert_skill_gates_reject({"speckit-autopilot/references/phase-driver.md": (
            'Dispatch with `spawn_agent` and `fork_turns="none"`,', "Dispatch with `spawn_agent`,")})

    def test_new_file_that_names_spawn_agent_must_state_the_rule(self) -> None:
        for relative in ("new/SKILL.md", "speckit-autopilot/references/new.md", "other/new.data"):
            with self.subTest(file=relative):
                self.assert_skill_gates_reject({relative: ("", "Dispatch with `spawn_agent`.\n")})
                self.assert_skill_gates_accept(
                    {relative: ("", 'Dispatch with `spawn_agent` and `fork_turns="none"`.\n')})

    def test_only_nondispatching_file_kinds_are_skipped(self) -> None:
        call = 'spawn_agent(agent_type="phase-executor", message="work")\n'
        for relative in (
            "speckit-coach/references/quint/quint-lang/new.md",
            "speckit-coach/examples/formal/tooling/quint/package-lock.json",
            "speckit-autopilot/contracts/new.schema.json",
            "speckit-autopilot/scripts/new.py",
        ):
            with self.subTest(skipped=relative):
                self.assert_skill_gates_accept({relative: ("", call)})
        for relative in ("speckit-coach/examples/new.py", "speckit-autopilot/contracts/new.json",
                         "speckit-autopilot/agents/openai.yaml", "speckit-autopilot/scripts/new.md",
                         "other/new.data"):
            with self.subTest(scanned=relative):
                self.assert_skill_gates_reject({relative: ("", call)})

    def test_unreadable_surface_or_call_fails_closed(self) -> None:
        for relative, new in (
            ("speckit-autopilot/references/new.md", b"\xff\xfe plain notes\n"),
            ("speckit-autopilot/references/new.md", '\nspawn_agent(fork_turns="none", message="work"\n'),
        ):
            with self.subTest(content=new[:24]):
                self.assert_skill_gates_reject({relative: ("", new)})

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
                dispatch_sites('spawn_agent(fork_turns="all")')

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

    def test_renamed_or_new_reference_is_scanned(self) -> None:
        for relative in ("speckit-autopilot/references/new.txt", "other/new.markdown", "other/new.data"):
            self.assert_skill_rejected(
                'spawn_agent(task_name="job", agent_type="phase-executor")',
                "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none", relative)

    def test_linked_skill_reference_is_rejected(self) -> None:
        for filename in ("linked.md", "linked.toml"):
            with self.subTest(link=filename), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "target").write_text('spawn_agent(task_name="job")', encoding="utf-8")
                (root / filename).symlink_to(root / "target")
                with self.assertRaisesRegex(AssertionError, "skill symlink"):
                    skill_paths(root)

    def test_shipped_codex_payload_passes_the_same_gates(self) -> None:
        payload = REPO_ROOT / "dist/codex"
        result = unittest.TestResult()
        with patch(__name__ + ".REPO_ROOT", payload), patch(
            __name__ + ".host_skill_root", return_value=payload / "speckit-pro/skills",
        ):
            for method in (*SKILL_GATES, "test_every_codex_agent_that_dispatches_states_the_rule"):
                CodexSpawnForkTests(method).run(result)
        self.assertTrue(result.wasSuccessful(), (result.failures, result.errors))

    def test_conflicting_agent_call_is_rejected(self) -> None:
        sources = agent_instruction_sources()
        dispatchers = [name for name, text in sources.items() if MENTION.search(text)]
        self.assertGreaterEqual(len(dispatchers), 4)
        for name in dispatchers:
            with self.subTest(agent=name):
                self.assert_agent_rejected(sources, name, 'spawn_agent(task_name="child", fork_turns="all")')

    def test_agent_that_names_spawn_agent_must_state_the_rule(self) -> None:
        sources = agent_instruction_sources()
        others = [name for name, text in sources.items() if not MENTION.search(text)]
        self.assertTrue(others)
        for name in (*others, "new.toml"):
            with self.subTest(agent=name):
                self.assert_agent_rejected(
                    {**sources, name: sources.get(name, "")}, name, "Use `spawn_agent` for research.")

    def assert_agent_rejected(self, sources: dict[str, str], name: str, conflict: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            agents = root / "speckit-pro/codex-agents"
            agents.mkdir(parents=True)
            for filename, original in sources.items():
                if original:
                    (agents / filename).write_bytes(original.encode("utf-8"))
            method = "test_every_codex_agent_that_dispatches_states_the_rule"
            control = unittest.TestResult()
            with patch(__name__ + ".REPO_ROOT", root):
                CodexSpawnForkTests(method).run(control)
            self.assertTrue(control.wasSuccessful(), (control.failures, control.errors))
            original = sources[name] or 'developer_instructions = """\n"""\n'
            marker = 'developer_instructions = """\n'
            self.assertEqual(original.count(marker), 1)
            text = original.replace(marker, marker + conflict + "\n\n", 1)
            self.assertIn(conflict, tomllib.loads(text)["developer_instructions"])
            (agents / name).write_bytes(text.encode("utf-8"))
            result = unittest.TestResult()
            with patch(__name__ + ".REPO_ROOT", root):
                CodexSpawnForkTests(method).run(result)
            self.assertFalse(result.wasSuccessful(), "gate accepted conflicting agent instructions")
            self.assertFalse(result.errors, result.errors)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-codex-spawn-fork-turns"))

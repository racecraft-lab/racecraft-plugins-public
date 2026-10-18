#!/usr/bin/env python3
"""Every Codex subagent spawn passes `fork_turns="none"`.

Codex defaults an omitted `fork_turns` to `"all"`, which copies the caller's whole
history into the child (openai/codex `multi_agents_v2/spawn.rs`, rust-v0.160.0).
A fresh child already gets a self-contained task message, so the copy is pure
input cost, repeated for every child (#1317).

Calls must pass the literal argument. Complete instruction surfaces must also
match a reviewed inventory: keyword matching cannot prove that arbitrary prose
does not contradict the rule. Regenerate explicitly after reviewing source edits
with scripts/refresh-codex-instruction-inventory.py; validation never writes it.
"""

from __future__ import annotations

import ast
import io
import json
import re
import runpy
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
sys.path[:0] = [str(TEST_DIR.parent / "lib"), str(REPO_ROOT / "scripts")]

from codex_instruction_review import (  # noqa: E402
    REVIEW_INVENTORY, instruction_inventory, instruction_paths, read_surface,
)
from host_skill_views import host_skill_root  # noqa: E402
from test_result import run_counted  # noqa: E402

FORK = 'fork_turns="none"'
# The rule as a file states it: the call form or the key-value form, either quote.
RULE = re.compile(r"fork_turns\s*[=:]\s*(?:\"none\"|'none')")
MENTION = re.compile(r"\bspawn_agent\b")
# Discover all concrete calls, independent of argument order or line wrapping.
DISPATCH = re.compile(r"\bspawn_agent\s*\(")
# Vendored upstream trees, owned by test-quint-reference-attribution.py.
VENDORED_ROOTS = ("speckit-coach/references/quint/quint-lang", "speckit-coach/references/quint/quint-modeling")
LOCKFILE = re.compile(r"(?:-lock\.json|-lock\.yaml|\.lock)$")
SKILL_GATES = (
    "test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none",
    "test_every_codex_skill_file_that_dispatches_states_the_rule",
    "test_codex_skill_instruction_inventory_matches",
)
AGENT_GATES = (
    "test_every_codex_agent_that_dispatches_states_the_rule",
    "test_codex_agent_instruction_inventory_matches",
)
CONFLICT = "For any child you launch, inherit the complete parent conversation."


def call_tokens(text: str) -> list[tokenize.TokenInfo]:
    """Read one balanced call; never borrow tokens from a subsequent comment/call."""
    tokens = []
    depth = 0
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
                    return tokens
    except (tokenize.TokenError, IndentationError) as error:
        raise AssertionError(f"unreadable spawn_agent call: {error}") from error
    raise AssertionError("unterminated spawn_agent call")


def dispatch_sites(text: str) -> list[tuple[int, list[tokenize.TokenInfo]]]:
    return [(match.start(), call_tokens(text[match.start():])) for match in DISPATCH.finditer(text)]


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
    # A `*` or `**` expansion is a dynamic argument list the gate cannot inspect.
    if len(forks) != 1 or any(argument[0] in ("*", "**") for argument in arguments):
        return False
    fork = forks[0]
    if len(fork) != 3 or fork[1] != "=":
        return False
    try:
        return ast.literal_eval(fork[2]) == "none"
    except (ValueError, SyntaxError):
        return False



def is_dispatch_surface(root: Path, path: Path) -> bool:
    """Skip only the kinds that cannot dispatch; any other file kind stays in scope."""
    relative = path.relative_to(root)
    if "scripts" in relative.parts[:-1] and path.suffix == ".py":
        return False
    if path.name.endswith(".schema.json") or LOCKFILE.search(path.name):
        return False
    return not any(relative.is_relative_to(vendored) for vendored in VENDORED_ROOTS)


def skill_paths(root: Path) -> list[Path]:
    """Filter the shared instruction walk for concrete call examples."""
    return [path for path in instruction_paths(root) if is_dispatch_surface(root, path)]



def assert_instruction_inventory(case: unittest.TestCase, kind: str, root: Path) -> None:
    """Require an explicit review update for every changed, added or removed file."""
    try:
        expected = json.loads(read_surface(REVIEW_INVENTORY))[kind]
    except (ValueError, KeyError, TypeError) as error:
        raise AssertionError("unreadable instruction review inventory") from error
    case.assertEqual(instruction_inventory(root), expected, "review instruction changes, then run python3 scripts/refresh-codex-instruction-inventory.py")


class CodexSpawnForkTests(unittest.TestCase):
    def test_codex_skill_instruction_inventory_matches(self) -> None:
        assert_instruction_inventory(self, "skills", host_skill_root("codex"))

    def test_codex_agent_instruction_inventory_matches(self) -> None:
        assert_instruction_inventory(self, "agents", REPO_ROOT / "speckit-pro/codex-agents")

    def test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none(self) -> None:
        root = host_skill_root("codex")
        sites = 0
        for path in skill_paths(root):
            for start, tokens in dispatch_sites(read_surface(path)):
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
                    self.assertRegex(text, RULE)
                    for _, tokens in dispatch_sites(source):
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

    def test_keyword_free_skill_paragraph_requires_review(self) -> None:
        self.assert_skill_gates_reject({"speckit-autopilot/SKILL.md": (
            "", "\n\n" + CONFLICT + "\n")})

    def test_keyword_free_call_fields_require_review(self) -> None:
        for field in ("message", "prompt", "context", "options", "task_name", "agent_type"):
            with self.subTest(field=field):
                arguments = {"task_name": "job", "agent_type": "phase-executor", "message": "work",
                             "fork_turns": "none", field: CONFLICT}
                call = "spawn_agent(" + ", ".join(f"{key}={json.dumps(value)}" for key, value in arguments.items()) + ")"
                self.assert_skill_gates_reject({"speckit-autopilot/SKILL.md": (
                    "", "\n" + call + "\n")})

    def test_keyword_free_call_comment_requires_review(self) -> None:
        self.assert_skill_gates_reject({"speckit-autopilot/SKILL.md": (
            "", f'\nspawn_agent(task_name="job", fork_turns="none",\n# {CONFLICT}\nmessage="work")\n')})

    def test_explicit_conflicting_prose_requires_review(self) -> None:
        self.assert_skill_gates_reject({"speckit-autopilot/SKILL.md": (
            "", '\nFor the next child, use `fork_turns="all"`.\n')})

    def test_new_or_renamed_keyword_free_skill_requires_review(self) -> None:
        edits = {relative: ("", CONFLICT + "\n") for relative in
                 ("new/SKILL.md", "renamed/SKILL.md", "other/new.data")}
        for relative, edit in edits.items():
            with self.subTest(path=relative):
                self.assert_skill_gates_reject({relative: edit})

    def test_borrowed_marker_requires_review(self) -> None:
        for marker in ('<!-- fork_turns="none" -->', 'An unrelated example uses `fork_turns="none"`.'):
            with self.subTest(marker=marker):
                self.assert_skill_gates_reject({"new/SKILL.md": (
                    "", f'Dispatch with spawn_agent.\n\n{marker}\n')})

    def test_keyword_free_agent_instructions_require_review(self) -> None:
        sources = agent_instruction_sources()
        for name in (*sources, "new.toml", "renamed.toml"):
            with self.subTest(agent=name):
                self.assert_agent_rejected({**sources, name: sources.get(name, "")}, name, CONFLICT)

    def test_keyword_free_agent_description_requires_review(self) -> None:
        sources = agent_instruction_sources()
        for name, source in sources.items():
            for field in sorted(tomllib.loads(source).keys() - {"developer_instructions"}):
                with self.subTest(agent=name, field=field):
                    self.assert_agent_rejected(sources, name, CONFLICT, field=field)

    def test_script_and_schema_instruction_text_requires_review(self) -> None:
        for relative, text in (
            ("speckit-autopilot/scripts/new.py", f'print("{CONFLICT}")\n'),
            ("speckit-autopilot/contracts/new.schema.json", f'{{"description": "{CONFLICT}"}}\n'),
        ):
            with self.subTest(file=relative):
                self.assert_skill_gates_reject({relative: ("", text)})

    def test_shipped_keyword_free_skill_instruction_requires_review(self) -> None:
        with patch(__name__ + ".host_skill_root", return_value=REPO_ROOT / "dist/codex/speckit-pro/skills"):
            self.assert_skill_gates_reject({"speckit-autopilot/SKILL.md": ("", "\n\n" + CONFLICT + "\n")})

    def test_shipped_keyword_free_agent_instruction_requires_review(self) -> None:
        agents = REPO_ROOT / "dist/codex/speckit-pro/codex-agents"
        sources = {path.name: read_surface(path) for path in sorted(agents.glob("*.toml"))}
        self.assertTrue(sources)
        self.assert_agent_rejected(sources, "phase-executor.toml", CONFLICT)

    def test_composed_argument_instruction_text_requires_review(self) -> None:
        for message in (
            '"For any child you launch, " "inherit the complete parent conversation."',
            '"For any child you launch, " + "inherit the complete parent conversation."',
            '{"instructions": ["' + CONFLICT + '"]}',
            'f"' + CONFLICT + '"',
        ):
            with self.subTest(message=message):
                self.assert_skill_gates_reject({"speckit-autopilot/SKILL.md": (
                    "", '\nspawn_agent(task_name="job", agent_type="phase-executor", fork_turns="none", '
                    f'message={message})\n')})

    def test_instruction_inventory_detects_renames_and_removals(self) -> None:
        for kind, source, relative in (
            ("skills", host_skill_root("codex"), "speckit-coach/SKILL.md"),
            ("agents", REPO_ROOT / "speckit-pro/codex-agents", "phase-executor.toml"),
        ):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / kind
                shutil.copytree(source, root)
                assert_instruction_inventory(self, kind, root)
                target = root / relative
                target.rename(target.with_suffix(".data"))
                for change in ("renamed", "removed"):
                    with self.subTest(kind=kind, change=change), self.assertRaises(AssertionError):
                        assert_instruction_inventory(self, kind, root)
                    target.with_suffix(".data").unlink(missing_ok=True)

    def test_inventory_refresh_reproduces_reviewed_fixture(self) -> None:
        module = runpy.run_path(str(REPO_ROOT / "scripts/refresh-codex-instruction-inventory.py"))
        refresh = module["main"]
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "inventory.json"
            target.write_text("stale proof data", encoding="utf-8")
            with patch.dict(refresh.__globals__, {"REVIEW_INVENTORY": target}), patch.object(
                sys, "argv", ["refresh-codex-instruction-inventory.py"],
            ):
                self.assertEqual(refresh(), 0)
            self.assertEqual(target.read_bytes(), REVIEW_INVENTORY.read_bytes())

    def test_inventory_rejects_links_and_missing_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "note.md").write_text("Use a fresh child.", encoding="utf-8")
            for target in (root / "note.md", root / "missing", root):
                with self.subTest(target=target.name):
                    (root / "linked").symlink_to(target)
                    with self.assertRaisesRegex(AssertionError, "instruction symlink"):
                        instruction_inventory(root)
                    (root / "linked").unlink()
            with self.assertRaisesRegex(AssertionError, "instruction root"):
                instruction_inventory(root / "missing")

    def test_unreadable_review_inventory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            inventory = Path(temporary) / "inventory.json"
            for content in (None, b"\xff", b"{", b"{}", b"[]", b'null'):
                with self.subTest(content=content), patch(__name__ + ".REVIEW_INVENTORY", inventory):
                    if content is not None:
                        inventory.write_bytes(content)
                    with self.assertRaises(AssertionError):
                        assert_instruction_inventory(self, "skills", host_skill_root("codex"))

    def test_structural_fault_tests_depend_on_their_own_gates(self) -> None:
        for gate, replacement, fault in (
            ("RULE", re.compile(".*"), "test_dispatch_line_without_the_rule_is_rejected"),
            ("passes_fork_none", lambda _: True, "test_real_call_without_the_argument_is_rejected"),
        ):
            with self.subTest(gate=gate), patch(__name__ + "." + gate, replacement):
                result = unittest.TestResult()
                CodexSpawnGateFaultTests(fault).run(result)
                self.assertFalse(result.wasSuccessful(), "inventory masked disabled structural gate: " + gate)
                self.assertFalse(result.errors, result.errors)

    def run_skill_gates(self, edits: dict[str, tuple[str, str | bytes]]) -> unittest.TestResult:
        """Run every skill gate on a copy of the rendered tree with `edits` applied.

        Each edit replaces one exact `old` string, or appends when `old` is empty.
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            shutil.copytree(host_skill_root("codex"), root)
            control = unittest.TestResult()
            with patch(__name__ + ".host_skill_root", return_value=root):
                for method in SKILL_GATES:
                    CodexSpawnForkTests(method).run(control)
            self.assertTrue(control.wasSuccessful(), (control.failures, control.errors))
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

    def test_wording_only_skill_edits_require_review(self) -> None:
        for relative, edit in (
            ("speckit-coach/SKILL.md", ("", "\nAsk one question at a time.\n")),
            ("speckit-autopilot/SKILL.md", (
                "and keep orchestration in the parent.\n",
                "and keep the orchestration in the parent session.\n")),
        ):
            with self.subTest(file=relative):
                self.assert_skill_gates_reject({relative: edit})

    def test_real_call_without_the_argument_is_rejected(self) -> None:
        with patch(__name__ + ".assert_instruction_inventory"):
            self.assert_skill_gates_reject({"speckit-autopilot/references/phase-driver.md": (
                "", '\n```text\nspawn_agent(agent_type="clarify-executor", message="work")\n```\n')})

    def test_dispatch_line_without_the_rule_is_rejected(self) -> None:
        # The phase driver reads only its own reference at dispatch (#1369).
        with patch(__name__ + ".assert_instruction_inventory"):
            self.assert_skill_gates_reject({"speckit-autopilot/references/phase-driver.md": (
                'Dispatch with `spawn_agent` and `fork_turns="none"`,', "Dispatch with `spawn_agent`,")})

    def test_new_file_that_names_spawn_agent_must_state_the_rule(self) -> None:
        for relative in ("new/SKILL.md", "speckit-autopilot/references/new.md", "other/new.data"):
            with self.subTest(file=relative), patch(__name__ + ".assert_instruction_inventory"):
                self.assert_skill_gates_reject({relative: ("", "Dispatch with `spawn_agent`.\n")})
                control = self.run_skill_gates({relative: ("", 'Dispatch with `spawn_agent` and `fork_turns="none"`.\n')})
                self.assertTrue(control.wasSuccessful(), (control.failures, control.errors))

    def test_call_scan_exclusions_still_require_content_review(self) -> None:
        call = 'spawn_agent(agent_type="phase-executor", message="work")\n'
        for relative in (
            "speckit-coach/references/quint/quint-lang/new.md",
            "speckit-coach/examples/formal/tooling/quint/package-lock.json",
            "speckit-autopilot/contracts/new.schema.json",
            "speckit-autopilot/scripts/new.py",
        ):
            with self.subTest(skipped=relative):
                self.assert_skill_gates_reject({relative: ("", call)})
                with patch(__name__ + ".assert_instruction_inventory"):
                    control = self.run_skill_gates({relative: ("", call)})
                    self.assertTrue(control.wasSuccessful(), (control.failures, control.errors))
        for relative in ("speckit-coach/examples/new.py", "speckit-autopilot/contracts/new.json",
                         "speckit-autopilot/agents/openai.yaml", "speckit-autopilot/scripts/new.md",
                         "other/new.data"):
            with self.subTest(scanned=relative), patch(__name__ + ".assert_instruction_inventory"):
                self.assert_skill_gates_reject({relative: ("", call)})
        # A notice file cannot exempt a directory; only the pinned upstream roots are skipped.
        with self.subTest(scanned="speckit-resolve-pr with a notice"), patch(__name__ + ".assert_instruction_inventory"):
            self.assert_skill_gates_reject({
                "speckit-resolve-pr/UPSTREAM-NOTICE.md": ("", "Vendored.\n"),
                "speckit-resolve-pr/new.md": ("", call)})

    def test_unreadable_surface_or_call_fails_closed(self) -> None:
        for relative, new in (
            ("speckit-autopilot/references/new.md", b"\xff\xfe plain notes\n"),
            ("speckit-autopilot/references/new.md", '\nspawn_agent(fork_turns="none", message="work"\n'),
        ):
            with self.subTest(content=new[:24]), patch(__name__ + ".assert_instruction_inventory"):
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
            '*options, fork_turns="none"',
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
                self.assertTrue(passes_fork_none(sites[0][1]))

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
                with self.assertRaisesRegex(AssertionError, "instruction symlink"):
                    skill_paths(root)

    def test_shipped_codex_payload_passes_the_same_gates(self) -> None:
        payload = REPO_ROOT / "dist/codex"
        result = unittest.TestResult()
        with patch(__name__ + ".REPO_ROOT", payload), patch(
            __name__ + ".host_skill_root", return_value=payload / "speckit-pro/skills",
        ):
            for method in (*SKILL_GATES, *AGENT_GATES):
                CodexSpawnForkTests(method).run(result)
        self.assertTrue(result.wasSuccessful(), (result.failures, result.errors))

    def test_conflicting_agent_call_is_rejected(self) -> None:
        sources = agent_instruction_sources()
        dispatchers = [name for name, text in sources.items() if MENTION.search(text)]
        self.assertGreaterEqual(len(dispatchers), 4)
        for name in dispatchers:
            with self.subTest(agent=name), patch(__name__ + ".assert_instruction_inventory"):
                self.assert_agent_rejected(sources, name, 'spawn_agent(task_name="child", fork_turns="all")')

    def test_agent_that_names_spawn_agent_must_state_the_rule(self) -> None:
        sources = agent_instruction_sources()
        others = [name for name, text in sources.items() if not MENTION.search(text)]
        self.assertTrue(others)
        for name in (*others, "new.toml"):
            with self.subTest(agent=name), patch(__name__ + ".assert_instruction_inventory"):
                self.assert_agent_rejected(
                    {**sources, name: sources.get(name, "")}, name, "Use `spawn_agent` for research.")

    def assert_agent_rejected(
        self, sources: dict[str, str], name: str, conflict: str, field: str = "developer_instructions",
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            agents = root / "speckit-pro/codex-agents"
            agents.mkdir(parents=True)
            for filename, original in sources.items():
                if original:
                    (agents / filename).write_bytes(original.encode("utf-8"))
            control = unittest.TestResult()
            with patch(__name__ + ".REPO_ROOT", root):
                for method in AGENT_GATES:
                    CodexSpawnForkTests(method).run(control)
            self.assertTrue(control.wasSuccessful(), (control.failures, control.errors))
            original = sources[name] or 'developer_instructions = """\n"""\n'
            if field == "developer_instructions":
                marker = 'developer_instructions = """\n'
                self.assertEqual(original.count(marker), 1)
                text = original.replace(marker, marker + conflict + "\n\n", 1)
            else:
                text, replacements = re.subn(
                    rf'(?m)^{re.escape(field)} = .*$', lambda _: f'{field} = "{conflict}"', original)
                self.assertEqual(replacements, 1)
            self.assertIn(conflict, tomllib.loads(text)[field])
            (agents / name).write_bytes(text.encode("utf-8"))
            result = unittest.TestResult()
            with patch(__name__ + ".REPO_ROOT", root):
                for method in AGENT_GATES:
                    CodexSpawnForkTests(method).run(result)
            self.assertFalse(result.wasSuccessful(), "gate accepted conflicting agent instructions")
            self.assertFalse(result.errors, result.errors)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-codex-spawn-fork-turns"))

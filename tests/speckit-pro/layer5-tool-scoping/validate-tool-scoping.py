#!/usr/bin/env python3
"""Layer-5 agent tool scoping validation (port of validate-tool-scoping.sh).

XPLAT-010 count-parity port (T046, US2). Python 3.11+ standard library only.
Every former ``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
names are reproduced via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-tool-scoping-baseline.txt``
(TOTAL: 186).
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

AGENTS_DIR = PLUGIN_ROOT / "agents"
CODEX_AGENTS_DIR = PLUGIN_ROOT / "codex-agents"

ORCHESTRATION_TOOLS = ("Agent", "TeamCreate", "SendMessage")
MUTATION_DENIALS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
OPEN_EXECUTORS = ("phase-executor", "analyze-executor", "checklist-executor", "implement-executor")
READ_ONLY_ROLES = (
    "codebase-analyst",
    "spec-context-analyst",
    "domain-researcher",
    "clarify-executor",
    "consensus-synthesizer",
)
TERMINAL_WORKERS = ("implement-executor", "uat-runbook-author")
SKILL_DRIVEN_EXECUTORS = ("phase-executor", "analyze-executor", "checklist-executor")
CODEX_READ_ONLY_ROLES = ("codebase-analyst", "spec-context-analyst", "domain-researcher", "clarify-executor")
CODEX_WRITE_ROLES = (
    "checklist-executor",
    "analyze-executor",
    "implement-executor",
    "phase-executor",
    "uat-runbook-author",
)
TEST_METHOD_ORDER = (
    "test_operator_tool_surface_no_tools_allowlist_pinning",
    "test_open_executors_orchestration_capabilities_never_denied",
    "test_read_only_roles_deny_builtin_mutation_primitives",
    "test_gate_validator",
    "test_terminal_workers_deny_skill_keep_mutation_surface",
    "test_skill_driven_executors_keep_skill_and_mutation_surface",
    "test_session_shape_metadata",
    "test_codex_agent_sandbox_mode_scoping",
    "test_named_tool_regression_guard",
)

NAMED_TOOL_PATTERN = re.compile(r"mcp__[A-Za-z0-9-]+__[A-Za-z0-9_-]+")
PROSE_TOKEN_ALLOWLIST: set[str] = set()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _frontmatter(path: Path) -> str:
    lines = _read(path).splitlines()
    out: list[str] = []
    fences = 0
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 1:
                continue
            if fences == 2:
                break
        elif fences == 1:
            out.append(line)
    return "\n".join(out)


def _md_body(path: Path) -> str:
    lines = _read(path).splitlines()
    out: list[str] = []
    fences = 0
    for line in lines:
        if line == "---":
            fences += 1
            continue
        if fences >= 2:
            out.append(line)
    return "\n".join(out)


def _yaml_field(path: Path, field: str) -> str:
    for line in _frontmatter(path).splitlines():
        if line.startswith(f"{field}:"):
            return re.sub(rf"^{re.escape(field)}:[ \t]*", "", line)
    return ""


def _toml_field(path: Path, field: str) -> str:
    pattern = re.compile(rf'^[ \t]*{re.escape(field)}[ \t]*=[ \t]*"([^"]*)"[ \t]*$')
    for line in _read(path).splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1)
    return ""


def _toml_prose(path: Path) -> str:
    out: list[str] = []
    in_block = False
    for line in _read(path).splitlines():
        if line == 'developer_instructions = """':
            in_block = True
            continue
        if in_block and line.strip() == '"""':
            in_block = False
            continue
        if in_block:
            out.append(line)
    return "\n".join(out)


def _disallowed_tools(path: Path) -> list[str]:
    for line in _frontmatter(path).splitlines():
        if line.startswith("disallowedTools:"):
            raw = re.sub(r"^disallowedTools:[ \t]*", "", line)
            return [item.strip() for item in raw.split(",") if item.strip()]
    return []


def _claude_agent_files() -> list[Path]:
    return sorted(AGENTS_DIR.glob("*.md"))


def _codex_agent_files() -> list[Path]:
    return sorted(CODEX_AGENTS_DIR.glob("*.toml")) if CODEX_AGENTS_DIR.is_dir() else []


def _positive_integer(value: str) -> bool:
    return value.strip().isdigit() and int(value.strip()) > 0


def _first_named_tool_violation(text: str) -> str:
    for token in sorted(set(NAMED_TOOL_PATTERN.findall(text))):
        if token not in PROSE_TOKEN_ALLOWLIST:
            return token
    return ""


class ValidateToolScoping(unittest.TestCase):
    def assert_denied(self, denials: list[str], tool: str, agent: str) -> None:
        self.assertIn(tool, denials, f"{agent} must deny '{tool}' in disallowedTools but does not")

    def assert_not_denied(self, denials: list[str], tool: str, agent: str) -> None:
        self.assertNotIn(tool, denials, f"{agent} denies '{tool}' but its role requires it")

    def test_operator_tool_surface_no_tools_allowlist_pinning(self) -> None:
        for agent_file in _claude_agent_files():
            agent_name = agent_file.stem
            frontmatter = _frontmatter(agent_file)

            with self.subTest(msg=f"{agent_name} has NO tools: allowlist (inherits the operator's full surface)"):
                self.assertIsNone(
                    re.search(r"^tools:", frontmatter, re.MULTILINE),
                    f"{agent_name} pins a tools: allowlist - availability is operator-owned; use disallowedTools for role denials only",
                )

            with self.subTest(msg=f"{agent_name} frontmatter has no vendor-qualified mcp__ token"):
                self.assertIsNone(
                    NAMED_TOOL_PATTERN.search(frontmatter),
                    f"{agent_name} frontmatter names a vendor-qualified MCP tool - the plugin neither grants nor blocks named vendor tools",
                )

    def test_open_executors_orchestration_capabilities_never_denied(self) -> None:
        for agent in OPEN_EXECUTORS:
            denials = _disallowed_tools(AGENTS_DIR / f"{agent}.md")
            for tool in ORCHESTRATION_TOOLS:
                with self.subTest(msg=f"{agent} does NOT deny {tool} (operator orchestration stays available)"):
                    self.assert_not_denied(denials, tool, agent)

    def test_read_only_roles_deny_builtin_mutation_primitives(self) -> None:
        for agent in READ_ONLY_ROLES:
            denials = _disallowed_tools(AGENTS_DIR / f"{agent}.md")

            for tool in MUTATION_DENIALS:
                with self.subTest(msg=f"{agent} denies {tool} (read-only role)"):
                    self.assert_denied(denials, tool, agent)

            with self.subTest(msg=f"{agent} denies Skill (consensus workers do not re-enter phases)"):
                self.assert_denied(denials, "Skill", agent)

            for tool in ORCHESTRATION_TOOLS:
                with self.subTest(msg=f"{agent} denies {tool} (hyper-focused worker does not fan out)"):
                    self.assert_denied(denials, tool, agent)

    def test_gate_validator(self) -> None:
        agent = "gate-validator"
        agent_file = AGENTS_DIR / f"{agent}.md"
        denials = _disallowed_tools(agent_file)

        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit", "Skill"):
            with self.subTest(msg=f"gate-validator denies {tool} (validates, never fixes)"):
                self.assert_denied(denials, tool, agent)

        for tool in ORCHESTRATION_TOOLS:
            with self.subTest(msg=f"gate-validator denies {tool} (hyper-focused validator does not fan out)"):
                self.assert_denied(denials, tool, agent)

        with self.subTest(msg="gate-validator does NOT deny Bash (runs gate scripts)"):
            self.assert_not_denied(denials, "Bash", agent)

        with self.subTest(msg="gate-validator model is sonnet (max-thinking policy: haiku does not support max)"):
            self.assertEqual("sonnet", _yaml_field(agent_file, "model"))

        with self.subTest(msg="gate-validator effort is max (max-thinking policy)"):
            self.assertEqual("max", _yaml_field(agent_file, "effort"))

        with self.subTest(msg="gate-validator maxTurns exists and is positive"):
            self.assertTrue(_positive_integer(_yaml_field(agent_file, "maxTurns")), "maxTurns must be positive")

    def test_terminal_workers_deny_skill_keep_mutation_surface(self) -> None:
        for agent in TERMINAL_WORKERS:
            denials = _disallowed_tools(AGENTS_DIR / f"{agent}.md")

            with self.subTest(msg=f"{agent} denies Skill (terminal worker, no phase re-entry)"):
                self.assert_denied(denials, "Skill", agent)

            for tool in ("Write", "Edit", "Bash"):
                with self.subTest(msg=f"{agent} does NOT deny {tool} (mutating role requires it)"):
                    self.assert_not_denied(denials, tool, agent)

        denials = _disallowed_tools(AGENTS_DIR / "uat-runbook-author.md")
        for tool in ORCHESTRATION_TOOLS:
            with self.subTest(msg=f"uat-runbook-author denies {tool} (hyper-focused worker does not fan out)"):
                self.assert_denied(denials, tool, "uat-runbook-author")

        with self.subTest(msg="uat-runbook-author model is sonnet (read-and-synthesize task)"):
            self.assertEqual("sonnet", _yaml_field(AGENTS_DIR / "uat-runbook-author.md", "model"))

    def test_skill_driven_executors_keep_skill_and_mutation_surface(self) -> None:
        for agent in SKILL_DRIVEN_EXECUTORS:
            denials = _disallowed_tools(AGENTS_DIR / f"{agent}.md")
            for tool in ("Skill", "Write", "Edit", "Bash"):
                with self.subTest(msg=f"{agent} does NOT deny {tool} (skill-driven executor requires it)"):
                    self.assert_not_denied(denials, tool, agent)

    def test_session_shape_metadata(self) -> None:
        for agent_file in _claude_agent_files():
            agent_name = agent_file.stem

            with self.subTest(msg=f"{agent_name} maxTurns exists and is positive"):
                self.assertTrue(_positive_integer(_yaml_field(agent_file, "maxTurns")), "maxTurns must be positive")

            with self.subTest(msg=f"{agent_name} effort field exists"):
                self.assertNotEqual("", _yaml_field(agent_file, "effort"), "effort must not be empty")

        with self.subTest(msg="phase-executor effort is max (max-thinking policy)"):
            self.assertEqual("max", _yaml_field(AGENTS_DIR / "phase-executor.md", "effort"))

        with self.subTest(msg="consensus-synthesizer model is sonnet"):
            self.assertEqual("sonnet", _yaml_field(AGENTS_DIR / "consensus-synthesizer.md", "model"))

        with self.subTest(msg="consensus-synthesizer effort is max (max-thinking policy)"):
            self.assertEqual("max", _yaml_field(AGENTS_DIR / "consensus-synthesizer.md", "effort"))

    def test_codex_agent_sandbox_mode_scoping(self) -> None:
        if not CODEX_AGENTS_DIR.is_dir():
            return

        for agent in CODEX_READ_ONLY_ROLES:
            agent_file = CODEX_AGENTS_DIR / f"{agent}.toml"
            if not agent_file.is_file():
                continue

            with self.subTest(msg=f"codex {agent}: sandbox_mode is read-only"):
                self.assertEqual("read-only", _toml_field(agent_file, "sandbox_mode"), f"{agent} must be read-only")

            with self.subTest(msg=f"codex {agent}: model is gpt-5.5"):
                self.assertEqual("gpt-5.5", _toml_field(agent_file, "model"), f"{agent} must use gpt-5.5")

            effort = _toml_field(agent_file, "model_reasoning_effort")
            if agent in {"codebase-analyst", "spec-context-analyst"}:
                with self.subTest(msg=f"codex {agent}: reasoning is L6-validated (low or xhigh)"):
                    self.assertIn(
                        effort,
                        {"low", "xhigh"},
                        f"{agent} reasoning must be low (L6-validated 100%) or xhigh (policy default), got '{effort}'",
                    )
            else:
                with self.subTest(msg=f"codex {agent}: reasoning is xhigh (max-thinking policy, no L6 carve-out)"):
                    self.assertEqual("xhigh", effort, f"{agent} must use xhigh reasoning per plugin policy")

        agent = "clarify-executor"
        agent_file = CODEX_AGENTS_DIR / f"{agent}.toml"
        if agent_file.is_file():
            with self.subTest(msg=f"codex {agent}: sandbox_mode is read-only"):
                self.assertEqual("read-only", _toml_field(agent_file, "sandbox_mode"), f"{agent} must be read-only")

        agent_file = CODEX_AGENTS_DIR / "autopilot-fast-helper.toml"
        if agent_file.is_file():
            with self.subTest(msg="codex autopilot-fast-helper: sandbox_mode is read-only (advisory text-only leaf)"):
                self.assertEqual(
                    "read-only",
                    _toml_field(agent_file, "sandbox_mode"),
                    "autopilot-fast-helper must be read-only",
                )

        for agent in CODEX_WRITE_ROLES:
            agent_file = CODEX_AGENTS_DIR / f"{agent}.toml"
            if not agent_file.is_file():
                continue

            with self.subTest(msg=f"codex {agent}: sandbox_mode is workspace-write"):
                self.assertEqual("workspace-write", _toml_field(agent_file, "sandbox_mode"), f"{agent} must be workspace-write")

            with self.subTest(msg=f"codex {agent}: model is gpt-5.5"):
                self.assertEqual("gpt-5.5", _toml_field(agent_file, "model"), f"{agent} must use gpt-5.5")

            with self.subTest(msg=f"codex {agent}: reasoning is xhigh (max-thinking policy)"):
                self.assertEqual(
                    "xhigh",
                    _toml_field(agent_file, "model_reasoning_effort"),
                    f"{agent} must use xhigh reasoning per plugin policy",
                )

    def test_named_tool_regression_guard(self) -> None:
        named_guard_files = [*_claude_agent_files(), *_codex_agent_files()]

        with self.subTest(msg="named-tool guard: active-agent set is non-empty (fail-closed)"):
            self.assertGreater(
                len(named_guard_files),
                0,
                "no active agents matched speckit-pro/agents/*.md or codex-agents/*.toml - guard would pass vacuously",
            )

        for agent_file in named_guard_files:
            if agent_file.suffix == ".md":
                prose = _md_body(agent_file)
            else:
                prose = _toml_prose(agent_file)
            violation = _first_named_tool_violation(prose)

            with self.subTest(msg=f"{agent_file.name} guidance prose has no hardcoded named vendor tool"):
                self.assertEqual(
                    "",
                    violation,
                    f"{agent_file.name} prose names vendor-qualified optional tool '{violation}' - use capability discovery, not a hardcoded tool (TACD-004 FR-001)",
                )


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for method_name in TEST_METHOD_ORDER:
        suite.addTest(ValidateToolScoping(method_name))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="validate-tool-scoping")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Opt-in live probe: does a Codex custom agent file enforce its own limits?

This script is not part of any suite. It bills the operator's Codex account,
so run it only by hand, with a throwaway project directory outside the
repository:

    python3 tests/speckit-pro/fixtures/codex-enforcement-probe/run-probe.py \
        --project <empty-dir> [--case readonly] [--model <model>]

Each case writes one probe custom agent under `<project>/.codex/agents/`,
then runs `codex exec` as a parent that spawns it. The parent's sandbox comes
from the operator's own config; the script passes no sandbox or approval flag,
because Codex reapplies a parent's live runtime overrides to a child. It trusts the project through a `-c projects...trust_level` override.
Codex 0.156.0 persists the `-c projects."<project>".trust_level` override as a
`[projects."<project>"]` entry in the operator's `~/.codex/config.toml`;
remove that entry after the run. The parent's JSON events
and stderr land in `<project>/logs/<case>.*`; the child rollouts stay in the
operator's Codex session store, found by each case's nonce.

Cases:
- baseline: no limits. Positive control that the file loads, the child can
  write, and both research-broker tools are reachable.
- readonly: `sandbox_mode = "read-only"`; the child tries one shell write.
- mcp-top: `[mcp_servers.research-broker] enabled_tools = ["docs_query"]`.
- mcp-plugin: `[plugins."<plugin>".mcp_servers.research-broker]
  enabled_tools = ["docs_query"]`.
- mcp-top-full: a complete stdio `[mcp_servers.research-broker]` definition
  (command, args, cwd) plus the same `enabled_tools`, pointed at the installed
  plugin root given by `--plugin-root`. It asks whether an agent-local server
  definition can replace the plugin's server for that agent.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


PLUGIN_ID = "speckit-pro@racecraft-plugins-public"
BROKER = "research-broker"
ALLOWED_TOOL = "docs_query"
DENIED_TOOL = "research_search"

TOOL_TASK = (
    f"(b) List the exact names of every tool you can call whose name contains "
    f"'research' or 'docs_query'. (c) Call the {BROKER} tool {DENIED_TOOL} with "
    f"query set to a single space character and report the exact result or "
    f"error text. If no such tool exists for you, say TOOL-ABSENT and do not "
    f"substitute any other tool."
)
WRITE_TASK = (
    "(a) Run exactly this shell command once: printf ok > {name}. Report the "
    "exact exit status and error text. You must attempt the command even if "
    "you expect it to fail: the point is to observe the runtime's answer. Do "
    "not request escalated permissions and do not retry another way."
)

CASES: dict[str, dict[str, str]] = {
    "baseline": {
        "agent": "probe_baseline",
        "extra": "",
        "task": WRITE_TASK.format(name="baseline-write.txt") + " " + TOOL_TASK,
    },
    "readonly": {
        "agent": "probe_readonly",
        "extra": 'sandbox_mode = "read-only"\n',
        "task": WRITE_TASK.format(name="readonly-write.txt"),
    },
    "mcp-top": {
        "agent": "probe_mcp_top",
        "extra": f'\n[mcp_servers.{BROKER}]\nenabled_tools = ["{ALLOWED_TOOL}"]\n',
        "task": TOOL_TASK,
    },
    "mcp-top-full": {
        "agent": "probe_mcp_top_full",
        "extra": (
            f'\n[mcp_servers.{BROKER}]\ncommand = "python3"\n'
            f'args = ["-m", "speckit_pro_runner.research_broker"]\n'
            'cwd = {plugin_root}\n'
            f'enabled_tools = ["{ALLOWED_TOOL}"]\n'
        ),
        "task": TOOL_TASK,
    },
    "mcp-plugin": {
        "agent": "probe_mcp_plugin",
        "extra": (
            f'\n[plugins."{PLUGIN_ID}".mcp_servers.{BROKER}]\n'
            f'enabled_tools = ["{ALLOWED_TOOL}"]\n'
        ),
        "task": TOOL_TASK,
    },
}


def nonce(case: str) -> str:
    return f"PROBE-NONCE-{case.upper()}-{int(time.time())}"


def agent_toml(case: str, token: str, model: str, plugin_root: Path | None) -> str:
    spec = CASES[case]
    instructions = (
        f"Begin your final reply with the line {token}. Then do this task and "
        f"report each step: {spec['task']}"
    )
    # Top-level keys first; any table the case adds goes last.
    lines = [
        f"name = {json.dumps(spec['agent'])}",
        'description = "Probe agent that runs one short task and reports raw results."',
        f"model = {json.dumps(model)}",
        # Differs from the parent's "low": a positive control that this file's
        # config layer reached the child.
        'model_reasoning_effort = "medium"',
        f"developer_instructions = {json.dumps(instructions)}",
    ]
    extra = spec["extra"]
    if "{plugin_root}" in extra:
        if plugin_root is None:
            raise SystemExit(f"case {case} needs --plugin-root")
        extra = extra.replace("{plugin_root}", json.dumps(str(plugin_root)))
    if extra and not extra.startswith("\n"):
        lines.append(extra.rstrip("\n"))
        extra = ""
    return "\n".join(lines) + "\n" + extra


def run_case(project: Path, case: str, model: str, plugin_root: Path | None) -> int:
    token = nonce(case)
    agents = project / ".codex" / "agents"
    shutil.rmtree(agents, ignore_errors=True)
    agents.mkdir(parents=True)
    (agents / f"{CASES[case]['agent']}.toml").write_text(
        agent_toml(case, token, model, plugin_root), encoding="utf-8"
    )
    logs = project / "logs"
    logs.mkdir(exist_ok=True)
    prompt = (
        f"Spawn exactly one subagent using the custom agent type "
        f"{CASES[case]['agent']}, with the message 'Follow your developer "
        f"instructions.' Do not fork your context into it: set fork_turns to "
        f"\"none\". Wait for it to finish, then print its final reply "
        f"verbatim. Do nothing else yourself."
    )
    trust = f'projects."{project}".trust_level="trusted"'
    argv = [
        "codex", "exec", "--json", "--skip-git-repo-check",
        "-m", model, "-c", 'model_reasoning_effort="low"', "-c", trust, prompt,
    ]
    completed = subprocess.run(
        argv, cwd=project, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False, timeout=900
    )
    (logs / f"{case}.jsonl").write_text(completed.stdout, encoding="utf-8")
    (logs / f"{case}.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    (logs / f"{case}.nonce.txt").write_text(token + "\n", encoding="utf-8")
    print(f"{case}: exit={completed.returncode} nonce={token}")
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--case", choices=sorted(CASES), action="append")
    parser.add_argument("--plugin-root", type=Path, help="installed speckit-pro plugin root")
    parser.add_argument("--model", default=os.environ.get("PROBE_MODEL", "gpt-6-luna"))
    args = parser.parse_args(argv)
    if shutil.which("codex") is None:
        print("codex CLI not found on PATH", file=sys.stderr)
        return 2
    project = args.project.resolve()
    repo_root = Path(__file__).resolve().parents[4]
    if project == repo_root or repo_root in project.parents:
        print("--project must be outside the repository", file=sys.stderr)
        return 2
    project.mkdir(parents=True, exist_ok=True)
    failures = 0
    for case in args.case or list(CASES):
        failures += run_case(project, case, args.model, args.plugin_root) != 0
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

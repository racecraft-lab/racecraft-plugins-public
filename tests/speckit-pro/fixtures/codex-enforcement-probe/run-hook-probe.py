#!/usr/bin/env python3
"""Opt-in live probe: can a Codex PreToolUse hook enforce one agent's limits?

This script is not part of any suite. It bills the operator's Codex account,
so run it only by hand, with a throwaway project directory outside the
repository:

    python3 tests/speckit-pro/fixtures/codex-enforcement-probe/run-hook-probe.py \
        --project <empty-dir> [--case hook-project] [--model <model>]

Each case makes the parent run one shell write itself, then spawn one probe
custom agent that tries a shell write and the research broker's
`research_search`. A hook script logs every payload it receives to
`<project>/logs/hooks.jsonl` and denies the two calls when its policy says so.

Cases:
- hook-project: a project `.codex/hooks.json` hook that denies only when it
  can tell the caller is the probe agent, from the hook payload or, failing
  that, from the `session_meta` record of the payload's `transcript_path`.
- hook-project-patch: the same project hook, but the probe agent writes with
  its file-edit tool (`apply_patch`) instead of the shell.
- hook-agent: the hook is declared inline in the probe agent file, not in the
  project, and denies unconditionally. It asks whether an agent-file hook
  layer applies to that agent only.

The run passes `--dangerously-bypass-hook-trust`, so no hook trust is
recorded, and trusts the project through a `-c` override.
Codex 0.156.0 persists the `-c projects."<project>".trust_level` override as a
`[projects."<project>"]` entry in the operator's `~/.codex/config.toml`;
remove that entry after the run.
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


CHILD = "probe_hook_child"
CASES = ("hook-project", "hook-project-patch", "hook-agent")
HOOK_SCRIPT = r'''
import json, sys
from pathlib import Path

layer, policy = sys.argv[1], sys.argv[2]
payload = json.load(sys.stdin)
role = next((payload[k] for k in ("agent_role", "agent_type") if payload.get(k)), None)
source = "payload" if role else None
transcript = payload.get("transcript_path")
if role is None and transcript:
    try:
        with open(transcript, encoding="utf-8") as handle:
            meta = json.loads(handle.readline()).get("payload", {})
        role, source = meta.get("agent_role"), "transcript"
    except (OSError, ValueError):
        source = "transcript-unreadable"
tool = payload.get("tool_name") or ""
args = payload.get("tool_input")
text = json.dumps(args) if args is not None else ""
limited = (
    (tool in ("Bash", "exec_command") and ">" in text)
    or tool in ("apply_patch", "Write", "Edit")
    or tool.endswith("research_search")
)
deny = limited and (policy == "deny-all" or policy == "deny-role:" + str(role))
record = {
    "layer": layer, "event": payload.get("hook_event_name"), "keys": sorted(payload),
    "tool_name": tool or None, "agent_type": payload.get("agent_type"),
    "agent_id_present": "agent_id" in payload, "role": role, "role_source": source,
    "input_excerpt": text[:160], "denied": deny,
}
log = Path(__file__).resolve().parent.parent / "logs" / "hooks.jsonl"
with log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record) + "\n")
if deny:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": "probe policy denies this call for " + str(role)}}))
'''

PATCH_TASK = (
    "(a) Create a new file child-patch.txt containing the word ok, using your "
    "file-editing tool (apply_patch), not the shell. Report the exact result or "
    "error text; you must attempt it. Do not request escalated permissions and "
    "do not retry another way."
)
CHILD_TASK = (
    "(a) Run exactly this shell command once: printf ok > child-write.txt. "
    "Report the exact exit status and error text; you must attempt it. "
    "(b) Call the research-broker tool research_search with query set to a "
    "single space character and report the exact result or error text. Do not "
    "request escalated permissions and do not retry another way."
)


def hook_command(project: Path, layer: str, policy: str) -> str:
    return f"python3 {json.dumps(str(project / '.codex' / 'probe_hook.py'))} {layer} {policy}"


def setup(project: Path, case: str, token: str, model: str) -> None:
    codex = project / ".codex"
    shutil.rmtree(codex, ignore_errors=True)
    (codex / "agents").mkdir(parents=True)
    (project / "logs").mkdir(exist_ok=True)
    (codex / "probe_hook.py").write_text(HOOK_SCRIPT.lstrip(), encoding="utf-8")
    task = PATCH_TASK if case == "hook-project-patch" else CHILD_TASK
    instructions = f"Begin your final reply with the line {token}. Then do this task: {task}"
    agent = [
        f"name = {json.dumps(CHILD)}",
        'description = "Probe agent that runs one short task and reports raw results."',
        f"model = {json.dumps(model)}",
        'model_reasoning_effort = "medium"',
        f"developer_instructions = {json.dumps(instructions)}",
    ]
    if case == "hook-agent":
        agent += [
            "",
            "[[hooks.PreToolUse]]",
            'matcher = "*"',
            "",
            "[[hooks.PreToolUse.hooks]]",
            'type = "command"',
            f"command = {json.dumps(hook_command(project, 'agent', 'deny-all'))}",
        ]
    else:
        group = [{"hooks": [{"type": "command",
                             "command": hook_command(project, "project", f"deny-role:{CHILD}")}]}]
        (codex / "hooks.json").write_text(
            json.dumps({"hooks": {"PreToolUse": group, "SubagentStart": group}}, indent=2),
            encoding="utf-8",
        )
    (codex / "agents" / f"{CHILD}.toml").write_text("\n".join(agent) + "\n", encoding="utf-8")


def run_case(project: Path, case: str, model: str) -> int:
    token = f"PROBE-NONCE-{case.upper()}-{int(time.time())}"
    setup(project, case, token, model)
    prompt = (
        "First run exactly this shell command yourself once: printf ok > "
        "parent-write.txt, and note its exit status. Then spawn exactly one "
        f"subagent using the custom agent type {CHILD}, with the message 'Follow "
        "your developer instructions.' and fork_turns set to \"none\". Wait for "
        "it, then print the parent write's exit status and the subagent's final "
        "reply verbatim."
    )
    argv = [
        "codex", "exec", "--json", "--skip-git-repo-check", "--dangerously-bypass-hook-trust",
        "-m", model, "-c", 'model_reasoning_effort="low"',
        "-c", f'projects."{project}".trust_level="trusted"', prompt,
    ]
    completed = subprocess.run(
        argv, cwd=project, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        check=False, timeout=900,
    )
    logs = project / "logs"
    (logs / f"{case}.jsonl").write_text(completed.stdout, encoding="utf-8")
    (logs / f"{case}.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    (logs / f"{case}.nonce.txt").write_text(token + "\n", encoding="utf-8")
    print(f"{case}: exit={completed.returncode} nonce={token}")
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--case", choices=CASES, action="append")
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
        failures += run_case(project, case, args.model) != 0
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run Layer 2 trigger evals against a Codex skill via the codex CLI.

Mirrors skill-creator's run_eval.py for Claude. Stages the skill into a
disposable repository with a marker injected into the body, runs each query
through `codex` non-interactively, validates the JSONL lifecycle and exact
marker, then scores trigger/no-trigger correctness against the eval fixture.

Subprocess invocations use `subprocess.run` with a list argument (no shell
involvement), so query strings are passed directly as argv entries and
cannot be interpreted as shell metacharacters.

Usage:
  run_codex_evals.py <skill> [--runs N] [--limit N] [--reasoning EFFORT]
                              [--model MODEL] [--threshold 0.5]

Examples:
  # Smoke test: 3 queries, 1 run each, low reasoning
  run_codex_evals.py grill-me --limit 3 --runs 1 --reasoning low

  # Full eval (slow, costs LLM tokens)
  run_codex_evals.py speckit-coach --runs 3
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


# Tests live at <repo>/tests/speckit-pro/; the plugin is the sibling <repo>/speckit-pro/.
TESTS_ROOT = pathlib.Path(__file__).resolve().parents[1]      # <repo>/tests/speckit-pro
PLUGIN_ROOT = TESTS_ROOT.parents[1] / "speckit-pro"           # <repo>/speckit-pro
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MODEL = "gpt-5.6-sol"
MARKER_PATTERN = re.compile(r"CODEX_SKILL_FIRED:[A-Za-z0-9_-]+")


def find_eval_file(skill: str) -> pathlib.Path:
    codex_specific = TESTS_ROOT / "layer2-trigger/codex-evals" / f"{skill}-trigger.json"
    shared = TESTS_ROOT / "layer2-trigger/evals" / f"{skill}-trigger.json"
    if codex_specific.exists():
        return codex_specific
    if shared.exists():
        return shared
    sys.exit(f"ERROR: no eval file for skill '{skill}' (tried {codex_specific}, {shared})")


def find_skill_source(skill: str) -> pathlib.Path:
    p = PLUGIN_ROOT / "codex-skills" / skill / "SKILL.md"
    if not p.exists():
        sys.exit(f"ERROR: codex skill not found at {p}")
    return p


def stage_skill_with_marker(src: pathlib.Path, dst_dir: pathlib.Path, new_name: str, marker: str) -> None:
    """Copy SKILL.md to dst_dir, rename it to new_name, prepend a marker requirement to the body."""
    text = src.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"ERROR: no YAML frontmatter found in {src}")
    fm_body, skill_body = m.group(1), m.group(2)

    fm_lines = [
        f"name: {new_name}" if ln.startswith("name:") else ln
        for ln in fm_body.split("\n")
    ]
    fm = "\n".join(fm_lines)

    marker_block = (
        "## IMPORTANT EVAL MARKER\n\n"
        "When this skill is invoked, your VERY FIRST action MUST be to print\n"
        "this exact line and nothing else before it:\n\n"
        f"    {marker}\n\n"
        "After printing the marker, proceed normally with the skill below.\n\n"
        "---\n\n"
    )

    dst_dir.mkdir(parents=True, exist_ok=True)
    (dst_dir / "SKILL.md").write_text(f"---\n{fm}\n---\n\n{marker_block}{skill_body}")


def stage_repository_skill(
    src: pathlib.Path,
    workspace: pathlib.Path,
    new_name: str,
    marker: str,
) -> pathlib.Path:
    """Stage one uniquely named skill at Codex's documented repository scope."""
    destination = workspace / ".agents" / "skills" / new_name
    stage_skill_with_marker(src, destination, new_name, marker)
    return destination


def inspect_codex_jsonl(output: str, marker: str) -> dict[str, object]:
    """Validate one Codex JSONL run and identify only the exact staged marker."""
    events: list[dict[str, object]] = []
    try:
        for line in output.splitlines():
            if line.strip():
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError("event is not an object")
                events.append(event)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"valid": False, "selected": False, "selected_marker": None, "reason": f"invalid JSONL: {exc}"}

    event_types = [event.get("type") for event in events]
    if event_types.count("thread.started") != 1 or event_types.count("turn.completed") != 1:
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": "missing or ambiguous thread/turn lifecycle",
        }
    if any(event_type in {"error", "turn.failed"} for event_type in event_types):
        return {"valid": False, "selected": False, "selected_marker": None, "reason": "Codex reported a failed run"}
    thread_event = next(event for event in events if event.get("type") == "thread.started")
    thread_id = thread_event.get("thread_id") or thread_event.get("threadId")
    if not isinstance(thread_id, str) or not thread_id:
        return {"valid": False, "selected": False, "selected_marker": None, "reason": "thread start omitted its id"}

    agent_messages = [
        item.get("text")
        for event in events
        if isinstance((item := event.get("item")), dict)
        and item.get("type") == "agent_message"
        and isinstance(item.get("text"), str)
    ]
    markers = MARKER_PATTERN.findall("\n".join(agent_messages))
    competing = sorted(set(markers) - {marker})
    if competing:
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": f"competing staged marker(s): {', '.join(competing)}",
        }
    marker_count = markers.count(marker)
    selected = marker_count == 1
    if marker_count > 1:
        return {"valid": False, "selected": False, "selected_marker": None, "reason": "ambiguous repeated staged marker"}
    if selected:
        first_lines = [line.strip() for message in agent_messages for line in message.splitlines() if line.strip()]
        if not first_lines or first_lines[0] != marker:
            return {"valid": False, "selected": False, "selected_marker": None, "reason": "staged marker was not first"}
    return {
        "valid": True,
        "selected": selected,
        "selected_marker": marker if selected else None,
        "thread_id": thread_id,
        "reason": "exact staged marker" if selected else "no staged marker",
    }


def case_passes(
    should_trigger: bool,
    triggers: int,
    runs: int,
    threshold: float,
    invalid_runs: int,
) -> bool:
    """Score a case only when every provider run completed truthfully."""
    if runs <= 0 or invalid_runs != 0:
        return False
    return ((triggers / runs) >= threshold) == should_trigger


def run_codex_query(
    workspace: pathlib.Path,
    query: str,
    reasoning: str,
    model: str,
    timeout: int,
) -> tuple[int, str, str]:
    cmd = [
        "codex", "exec",
        "--cd", str(workspace),
        "--sandbox", "read-only",
        "--ephemeral",
        "--ignore-user-config",
        "--json",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning}"',
    ]
    cmd.append(query)
    env = os.environ.copy()
    try:
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=env,
            shell=False,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", f"TIMEOUT after {timeout}s: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", help="Codex skill name (looked up under codex-skills/)")
    ap.add_argument("--runs", type=int, default=3, help="Trials per query (default 3)")
    ap.add_argument("--limit", type=int, help="Only run the first N queries from the eval set")
    ap.add_argument(
        "--reasoning",
        default=DEFAULT_REASONING_EFFORT,
        help=f"codex model_reasoning_effort (default: {DEFAULT_REASONING_EFFORT})",
    )
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Codex model id (default: {DEFAULT_MODEL})")
    ap.add_argument("--threshold", type=float, default=0.5, help="Trigger-rate threshold for pass (default 0.5)")
    ap.add_argument("--timeout", type=int, default=180, help="Per-query timeout seconds (default 180)")
    ap.add_argument("--out", help="Write detailed JSON results to this file")
    args = ap.parse_args()

    if shutil.which("codex") is None:
        sys.exit("ERROR: codex CLI not on PATH")

    eval_file = find_eval_file(args.skill)
    skill_src = find_skill_source(args.skill)
    eval_data = json.loads(eval_file.read_text())
    if args.limit:
        eval_data = eval_data[: args.limit]

    test_uuid = uuid.uuid4().hex[:8]
    test_skill_name = f"{args.skill}-eval-{test_uuid}"
    marker = f"CODEX_SKILL_FIRED:{test_skill_name}"

    workspace = pathlib.Path(tempfile.mkdtemp(prefix=f"codex-eval-{args.skill}-"))
    try:
        initialized = subprocess.run(
            ["git", "init", "--quiet"],
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=False,
        )
        if initialized.returncode != 0:
            sys.exit(f"ERROR: could not initialize disposable eval repository: {initialized.stderr.strip()}")
        skill_dir = stage_repository_skill(skill_src, workspace, test_skill_name, marker)

        print(f"Codex Layer 2 trigger eval: {args.skill}", file=sys.stderr)
        print(f"  Eval file:  {eval_file}", file=sys.stderr)
        print(f"  Skill src:  {skill_src}", file=sys.stderr)
        print(f"  Test skill: {test_skill_name}", file=sys.stderr)
        print(f"  Workspace:  {workspace}", file=sys.stderr)
        print("  Login:      existing Codex session (credential files are not copied)", file=sys.stderr)
        print(f"  Queries:    {len(eval_data)} (x{args.runs} runs)", file=sys.stderr)
        print(f"  Reasoning:  {args.reasoning}", file=sys.stderr)
        print(f"  Model:      {args.model}", file=sys.stderr)
        print("", file=sys.stderr)

        results = []
        passed = failed = 0
        for idx, entry in enumerate(eval_data, start=1):
            query = entry["query"]
            should_trigger = bool(entry["should_trigger"])
            triggers = 0
            invalid_runs = 0
            run_evidence = []
            for run in range(args.runs):
                rc, output, error_output = run_codex_query(
                    workspace,
                    query,
                    args.reasoning,
                    args.model,
                    args.timeout,
                )
                evidence = inspect_codex_jsonl(output, marker)
                run_valid = rc == 0 and bool(evidence["valid"])
                if not run_valid:
                    invalid_runs += 1
                    evidence = {
                        **evidence,
                        "reason": f"exit={rc}; {evidence['reason']}; stderr={error_output.strip()[:200]}",
                    }
                if run_valid and evidence["selected"]:
                    triggers += 1
                run_evidence.append(evidence)
            trigger_rate = triggers / args.runs
            is_pass = case_passes(
                should_trigger,
                triggers,
                args.runs,
                args.threshold,
                invalid_runs,
            )
            if is_pass:
                passed += 1
            else:
                failed += 1
            mark = "PASS" if is_pass else "FAIL"
            expect = "TRIG" if should_trigger else "NOOP"
            print(
                f"  [{idx:2d}/{len(eval_data)}] expect={expect} trig={triggers}/{args.runs} "
                f"invalid={invalid_runs} {mark}  {query[:70]}",
                file=sys.stderr,
            )
            results.append({
                "query": query,
                "should_trigger": should_trigger,
                "triggers": triggers,
                "runs": args.runs,
                "trigger_rate": round(trigger_rate, 3),
                "invalid_runs": invalid_runs,
                "selection_evidence": run_evidence,
                "pass": is_pass,
            })

        summary = {
            "skill": args.skill,
            "total": len(eval_data),
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / len(eval_data), 3) if eval_data else 0.0,
            "runs_per_query": args.runs,
            "reasoning": args.reasoning,
            "model": args.model,
        }

        report = {"summary": summary, "results": results}
        print("", file=sys.stderr)
        print("===========================", file=sys.stderr)
        print(f"Codex Trigger Eval: {args.skill}", file=sys.stderr)
        print(f"  PASSED: {passed}/{len(eval_data)} ({summary['pass_rate']*100:.0f}%)", file=sys.stderr)
        print(f"  FAILED: {failed}/{len(eval_data)}", file=sys.stderr)
        print("===========================", file=sys.stderr)

        if args.out:
            pathlib.Path(args.out).write_text(json.dumps(report, indent=2))
            print(f"Wrote detailed results to: {args.out}", file=sys.stderr)

        print(json.dumps(report, indent=2))
        return 0 if failed == 0 else 1
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

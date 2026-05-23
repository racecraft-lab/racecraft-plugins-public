#!/usr/bin/env python3
"""Run Layer 2 trigger evals against a Codex skill via the codex CLI.

Mirrors skill-creator's run_eval.py for Claude. Stages the skill into an
isolated workspace with a marker injected into the body, runs each query
through `codex` non-interactively, scans stdout for the marker, scores
trigger/no-trigger correctness against the eval fixture.

Subprocess invocations use `subprocess.run` with a list argument (no shell
involvement), so query strings are passed directly as argv entries and
cannot be interpreted as shell metacharacters.

Usage:
  run_codex_evals.py <skill> [--runs N] [--limit N] [--reasoning EFFORT]
                              [--model MODEL] [--threshold 0.5]

Examples:
  # Smoke test: 3 queries, 1 run each, minimal reasoning
  run_codex_evals.py grill-me --limit 3 --runs 1 --reasoning minimal

  # Full eval (slow, costs LLM tokens)
  run_codex_evals.py speckit-coach --runs 3
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def find_eval_file(skill: str) -> pathlib.Path:
    codex_specific = REPO_ROOT / "tests/layer2-trigger/codex-evals" / f"{skill}-trigger.json"
    shared = REPO_ROOT / "tests/layer2-trigger/evals" / f"{skill}-trigger.json"
    if codex_specific.exists():
        return codex_specific
    if shared.exists():
        return shared
    sys.exit(f"ERROR: no eval file for skill '{skill}' (tried {codex_specific}, {shared})")


def find_skill_source(skill: str) -> pathlib.Path:
    p = REPO_ROOT / "codex-skills" / skill / "SKILL.md"
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


def run_codex_query(workspace: pathlib.Path, query: str, reasoning: str, model: str | None, timeout: int) -> tuple[int, str]:
    cmd = [
        "codex", "exec",
        "--cd", str(workspace),
        "--skip-git-repo-check",
        "--sandbox", "read-only",
        "--ephemeral",
        "-c", f'model_reasoning_effort="{reasoning}"',
    ]
    if model:
        cmd += ["-c", f'model="{model}"']
    cmd.append(query)
    try:
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as e:
        return -1, f"TIMEOUT after {timeout}s: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", help="Codex skill name (looked up under codex-skills/)")
    ap.add_argument("--runs", type=int, default=3, help="Trials per query (default 3)")
    ap.add_argument("--limit", type=int, help="Only run the first N queries from the eval set")
    ap.add_argument("--reasoning", default="minimal", help="codex model_reasoning_effort (default: minimal)")
    ap.add_argument("--model", help="Override codex model id")
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
    skill_dir = workspace / ".codex/skills" / test_skill_name
    try:
        stage_skill_with_marker(skill_src, skill_dir, test_skill_name, marker)

        print(f"Codex Layer 2 trigger eval: {args.skill}", file=sys.stderr)
        print(f"  Eval file:  {eval_file}", file=sys.stderr)
        print(f"  Skill src:  {skill_src}", file=sys.stderr)
        print(f"  Test skill: {test_skill_name}", file=sys.stderr)
        print(f"  Workspace:  {workspace}", file=sys.stderr)
        print(f"  Queries:    {len(eval_data)} (x{args.runs} runs)", file=sys.stderr)
        print(f"  Reasoning:  {args.reasoning}", file=sys.stderr)
        if args.model:
            print(f"  Model:      {args.model}", file=sys.stderr)
        print("", file=sys.stderr)

        results = []
        passed = failed = 0
        for idx, entry in enumerate(eval_data, start=1):
            query = entry["query"]
            should_trigger = bool(entry["should_trigger"])
            triggers = 0
            for run in range(args.runs):
                rc, output = run_codex_query(workspace, query, args.reasoning, args.model, args.timeout)
                if marker in output:
                    triggers += 1
            trigger_rate = triggers / args.runs
            is_pass = (trigger_rate >= args.threshold) == should_trigger
            if is_pass:
                passed += 1
            else:
                failed += 1
            mark = "PASS" if is_pass else "FAIL"
            expect = "TRIG" if should_trigger else "NOOP"
            print(f"  [{idx:2d}/{len(eval_data)}] expect={expect} trig={triggers}/{args.runs} {mark}  {query[:70]}", file=sys.stderr)
            results.append({
                "query": query,
                "should_trigger": should_trigger,
                "triggers": triggers,
                "runs": args.runs,
                "trigger_rate": round(trigger_rate, 3),
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

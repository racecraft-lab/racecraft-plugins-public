#!/usr/bin/env python3
"""Generate audit/ledger.json and audit/lanes.json from origin/main.

Deterministic: the file list comes from `git ls-tree` at origin/main, lanes come
from the ordered rule table below, in-flight tags come from open PR branches.
Usage: python3 audit/scope.py [--ref origin/main] [--no-inflight]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
MAX_LANE = 100

# --- scope -----------------------------------------------------------------
INCLUDE = [
    r"^speckit-pro/",
    r"^tests/speckit-pro/",
    r"^scripts/",
    r"^docs-site/",
    r"^specs/",
    r"^docs/ai/specs/[^/]+$",  # active roadmaps, design concepts, workflows (not .process/)
    r"^docs/ai/research/",
    r"^docs/[^/]+\.md$",  # PRDs, roadmaps, traceability
    r"^(AGENTS|CLAUDE|GEMINI|REVIEW|README)\.md$",
]
EXCLUDE = [
    r"^dist/",
    r"(^|/)(pnpm-lock\.yaml|package-lock\.json|yarn\.lock|go\.sum|uv\.lock)$",
    r"^docs-site/src/content/docs/reference/",  # generated reference pages
    r"^speckit-pro/skills/speckit-coach/references/quint/",  # vendored upstream
    r"/\.process/",  # generated workflow exhaust
    r"(^|/)\.gitkeep$",
    r"\.(png|ico|woff2?|ttf|otf|jpe?g|gif|webp)$",  # binary assets
]

# --- lanes: ordered (id, name, feature, [path regexes]); first match wins ----
R = "speckit-pro/speckit_pro_runner/"
T = "tests/speckit-pro/"
LANES = [
    ("coach-and-formal", "Coach skill and formal methods", "speckit-coach skill, guides, templates and Codex overlay; selective formal methods runner package, catalog, checkers, tests.",
     [rf"^{R}formal/", rf"^{R}contracts/formal", r"formal", r"quint", r"tlc|apalache|itf|traces?\b"]),
    ("artifact-gallery", "Artifact gallery and author/preview agents", "HTML artifact gallery templates, artifact review, author and preview brokers, gallery docs.",
     [r"^speckit-pro/artifact-gallery/", rf"^{R}artifact_review|^{R}author_broker|^{R}preview_launcher", r"artifact", r"author-broker", r"gallery", r"preview-verdict", r"agents/uat-runbook|uat-runbook"]),
    ("brokers-and-verification", "Brokers, sweep and verification", "Sweep and research brokers, MCP protocol, hooks; Docker and git verification records, quality gates, task execution and results.",
     [rf"^{R}(sweep_|research_|mcp_protocol)", r"sweep|feedback-sweep", r"mcp-protocol", r"research-broker|research_broker|research-preflight", r"^speckit-pro/(hooks|codex-hooks|\.mcp)", r"claude-hooks|workflow-guard|workflow_guard", r"agents/sweep|contracts/sweep"]),
    ("brokers-and-verification", "", "",
     [rf"^{R}(verification_|quality_gates|task_execution|task_results|execution_control|failing_checks)", rf"^{R}contracts/(docker|verification|quality|task|execution)", r"verification-docker|verification-git|quality-gates|crap|mutation-score|task-execution|batched-task|execution-control|docker", r"scripts/(crap|mutation)"]),
    ("pr-emission-and-stack", "PR emission, stack manager and finalization", "Draft PR emission, PR packet, split ratification, stack manager, run finalization, archive sweep, egress authorization, reviewability.",
     [rf"^{R}helpers/(pr_|stack_|run_final|archive_|egress_|promotion)", r"pr-packet|pr-split|ratify|stack-manager|stack_manager|finalize|finalization|archive|egress|reviewability|draft-pr|estimate-spec-size|implementation-notes|phase7|atomicity|corrective|autonomy-boundary|07-|03-reviewability|04-stack"]),
    ("release-tooling", "Release tooling and marketplace", "Release notes, release-PR lifecycle, payload build, marketplace sync, refresh scripts, CI contracts, plugin metadata.",
     [r"^scripts/", r"release|marketplace|payload|pr-checks|refresh-local|check-toolchain|hosted-windows|container-preflight|typesafe-jev|plugin-metadata|validate-ci|installed-release|install-verification|^speckit-pro/(CHANGELOG|\.claude-plugin|\.codex-plugin)|sync-|dispatch-release"]),
    ("native-eval-harness", "Native eval harness", "Native eval runner library: adapters, capture, grading, judge, pool, store, runtime, toolchain.",
     [rf"^{T}lib/native_eval", r"native-eval|native_eval|run-native-evals|native-(functional|integration|parity|trigger|response|scaffold|workflow|worktree)|native-runner|evals/audit|evals/README|evals/catalog|eval-runner|search-observation|runtime-agent|unit-layout"]),
    ("trigger-evals", "Trigger evals (layer 2)", "Skill trigger evals, campaigns, carry-forward, comparison, controlled descriptions.",
     [rf"^{T}layer2-trigger/", rf"^{T}lib/trigger_", r"trigger", r"signal-restoration|skill-selection"]),
    ("functional-evals", "Functional evals (layer 3)", "Functional and headless evals, executor-mode scoring, functional fixtures.",
     [rf"^{T}layer3-functional/", r"executor-mode|executor_mode", rf"^{T}evals/fixtures/functional/", r"functional|headless"]),
    ("integration-layer6", "Integration fixtures (layer 6)", "Dispatch, performance, e2e, grounding and return-format fixtures and their runners.",
     [rf"^{T}layer6-", r"integration|dispatch|grounding|return-format|integration-return|transcript|performance-fixtures|scrub"]),
    ("lifecycle-skills", "", "", [rf"^{T}evals/fixtures/(scaffold-contracts|status-contracts|grounding/status)"]),
    ("parity-layer7", "Claude and Codex parity (layer 7)", "Cross-host parity fixtures, extractors, judge, parity evals.",
     [rf"^{T}layer7-", r"parity", rf"^{T}evals/fixtures/(parity|scenario-contracts|scaffold-contracts|status-contracts)"]),
    ("structural-layers", "Structural layers 1 and 5, suite harness", "Layer 1 structural validators and fixtures, layer 5 tool scoping, suite manifest, run-all, privacy scan, test library helpers.",
     [rf"^{T}layer(1|5)-", rf"^{T}(run-|test-run|suite-manifest|check-|AGENTS|CLAUDE|GEMINI)", rf"^{T}lib/", r"privacy|json-schema|semantic-contract|bash-confinement|structural|moc-lint|generate-spec-index|spec-index|unit/README|unit/fixtures/README"]),
    ("autopilot-and-agents", "Autopilot skill and executor agents", "speckit-autopilot skill, references, contracts, Codex overlay; Claude and Codex executor agents, consensus analysts, agent inventory.",
     [r"^speckit-pro/(skills|codex-skills)/speckit-autopilot/", r"autopilot", r"post-implementation-reference", r"skills/speckit-autopilot"]),
    ("autopilot-and-agents", "", "",
     [r"^speckit-pro/(agents|codex-agents)/", rf"^{R}agent_", r"agent-inventory|agent-materialization|agent-memory|agent-terminal|consensus|analyst|synthesizer"]),
    ("coach-and-formal", "", "",
     [r"^speckit-pro/(skills|codex-skills)/speckit-coach/", r"coach", r"roadmap-moc|slicing|constitution"]),
    ("lifecycle-skills", "Lifecycle skills", "scaffold-spec, prd, grill-me, status, ubiquitous-language, install, upgrade, resolve-pr, archive-cleanup skills with overlays, contracts and tests.",
     [r"^speckit-pro/(skills|codex-skills)/(speckit-scaffold-spec|speckit-prd|grill-me|speckit-status|ubiquitous-language)/", r"scaffold|prd|grill|status|ubiquitous|read-only-helper-feature"]),
    ("lifecycle-skills", "", "",
     [r"^speckit-pro/(skills|codex-skills)/(speckit-install|install|speckit-upgrade|speckit-resolve-pr|speckit-archive-cleanup)/", r"install|upgrade|resolve-pr|speckit-setup"]),
    ("runner-core", "Runner core, gates and helpers", "Runner entrypoint, envelope, runtime, gates registry, helper registry and read-only/mutation helpers, contracts.",
     [rf"^{R}", r"architecture-graph|speckit-pro-runner|speckit-pro-gates|read-only|mutation-helpers|runner-gates|runner_gates|plan-layers|research|gate-", r"^speckit-pro/scripts/"]),
    ("docs", "Docs site, root docs and planning", "Authored docs-site pages, root agent docs, READMEs, active specs, PRDs, roadmaps, design concepts.",
     [r"^docs-site/"]),
    ("docs", "", "",
     [r"^(AGENTS|CLAUDE|GEMINI|REVIEW|README)\.md$", r"^speckit-pro/(README|AGENTS|CLAUDE|GEMINI)", r"^specs/", r"^docs/"]),
]
FALLBACK = "misc-unassigned"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def in_scope(path: str) -> bool:
    return any(re.search(p, path) for p in INCLUDE) and not any(re.search(p, path) for p in EXCLUDE)


def assign(path: str) -> str:
    for lane_id, _n, _f, pats in LANES:
        if any(re.search(p, path) for p in pats):
            return lane_id
    return FALLBACK


def in_flight(ref: str) -> dict[str, list[int]]:
    tags: dict[str, list[int]] = {}
    try:
        prs = json.loads(subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--limit", "100", "--json", "number,headRefName"],
            check=True, capture_output=True, text=True).stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot list open PRs: {exc}")
    for pr in sorted(prs, key=lambda p: p["number"]):
        branch = pr["headRefName"]
        try:
            names = git("diff", "--name-only", f"{ref}...origin/{branch}").splitlines()
        except subprocess.CalledProcessError:
            sys.exit(f"cannot diff origin/{branch} (PR {pr['number']}); run git fetch origin")
        for n in names:
            tags.setdefault(n, []).append(pr["number"])
    return tags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--no-inflight", action="store_true")
    args = ap.parse_args()

    files = sorted(p for p in git("ls-tree", "-r", "--name-only", args.ref).splitlines() if in_scope(p))
    by_lane: dict[str, list[str]] = {}
    for f in files:
        by_lane.setdefault(assign(f), []).append(f)

    # split oversize lanes into numbered parts, in sorted-path order
    meta = {}
    for lid, name, feat, _ in LANES:
        if name:
            meta.setdefault(lid, (name, feat))
    meta[FALLBACK] = ("Unassigned", "Files no lane rule matched; must be empty.")
    lanes, owner = [], {}
    order = list(dict.fromkeys(l[0] for l in LANES)) + [FALLBACK]
    for lid in order:
        fl = by_lane.get(lid, [])
        if not fl:
            continue
        parts = -(-len(fl) // MAX_LANE) if len(fl) > MAX_LANE else 1
        size = -(-len(fl) // parts)
        for i in range(parts):
            chunk = fl[i * size:(i + 1) * size]
            sid = lid if parts == 1 else f"{lid}-{i + 1}"
            name = meta[lid][0] + ("" if parts == 1 else f" ({i + 1}/{parts})")
            lanes.append({"id": sid, "name": name, "feature": meta[lid][1], "files": chunk, "file_count": len(chunk)})
            for f in chunk:
                owner[f] = sid
    tags = {} if args.no_inflight else in_flight(args.ref)
    rows = [{"path": f, "lane": owner[f], "in_flight": tags.get(f, []), "verdict": None, "findings": [], "checks_run": []} for f in files]

    AUDIT.joinpath("lanes.json").write_text(json.dumps(lanes, indent=2) + "\n")
    AUDIT.joinpath("ledger.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"{len(rows)} files, {len(lanes)} lanes, {sum(1 for r in rows if r['in_flight'])} in flight")
    return 0


if __name__ == "__main__":
    sys.exit(main())

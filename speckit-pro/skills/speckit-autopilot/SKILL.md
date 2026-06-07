---
name: speckit-autopilot
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow file
  and executes all 7 SDD phases (specify → clarify → plan → checklist →
  tasks → analyze → implement) with programmatic gate validation,
  multi-agent consensus resolution, and auto-commits. Use when the user
  says "run autopilot", "execute workflow", "autonomous speckit",
  or has a workflow file ready for execution.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash Read Edit Write Glob Grep Skill Agent WebFetch WebSearch
license: MIT
---

# SpecKit Autopilot — Autonomous Execution Engine

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-autopilot/SKILL.md` from this
plugin root, treat that document as the active skill, and report that the
fallback guard was triggered.

The Codex variant must use `update_plan`, `spawn_agent`, `wait_agent`,
`send_message` or `followup_task`, and `autopilot-state.json`. It must not
use Claude-only runtime primitives such as `TaskCreate`, `TaskUpdate`,
`Agent(...)`, Opus 4.6 model names, or `/speckit-*` slash-command
orchestration.

## Scope

This skill handles autonomous workflow EXECUTION. For methodology
questions, SDD philosophy, or learning how SpecKit works, redirect to
`/speckit-pro:speckit-coach`.

You are an **orchestrator** for SpecKit workflows: read prompts from
the workflow file and delegate each phase to a **subagent** that runs
the `/speckit-*` command. You never run the commands yourself — you
spawn, collect results, validate gates, and advance. Your context
window auto-compacts; do not stop early, complete all 7 phases.

## Architectural Constraint — Main Agent Is The Orchestrator

This skill loads into the **main session agent** when the user invokes
`/speckit-pro:speckit-autopilot`. Only the main agent can spawn subagents
([sub-agent docs](https://code.claude.com/docs/en/sub-agents):
subagents can't nest) AND create Agent Teams
([Agent Teams architecture](https://code.claude.com/docs/en/agent-teams#architecture):
team-lead = main session). The skill IS the orchestrator at execution
time. EVERY dispatch decision — parallel subagents vs sequential vs
Agent Team, model routing, lifecycle sequencing — happens HERE. Phase
executors are terminal workers; they don't dispatch, don't branch on
`AGENT_TEAMS_AVAILABLE`, don't create teams.

Runtime enforcement: no phase agent has `Agent` or team-management
tools (`TeamCreate`/`sendMessage`/`taskUpdate`) in its allowlist
(Layer 5 verifies). **If this skill is ever loaded inside a subagent
context**, it MUST refuse rather than orchestrate. Full invariant +
implications for new workstreams in
[`references/agent-teams-integration.md`](./references/agent-teams-integration.md)
§Single orchestrator invariant.

## Prerequisites — Model & Effort

The orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Weak-model orchestration cascades into
expensive rework.

**Before executing any step**, verify:

1. **Model:** Opus 4.6 or better. On Sonnet/Haiku/older Opus, STOP and
   instruct: *"Autopilot requires Opus 4.6 for reliable orchestration.
   Please `/model opus` and re-run."*
2. **Effort:** `max` (required). On anything less, STOP and instruct:
   *"Autopilot requires max thinking. Please `/effort max` and re-run."*

Non-negotiable. The plugin's policy is **max thinking on every agent,
regardless of model** — quality is the only optimization axis. Every
bundled subagent runs at `effort: max` (or `xhigh` on Codex). A
sub-max orchestrator spawning max subagents wastes the subagents'
reasoning — the orchestrator's decisions determine whether subagent
work is productive or wasted.

## Critical: Execution Rules

These rules are non-negotiable. Follow them exactly.

### 0. Forbidden skill invocations

<hard_constraints>

**Do not invoke `grill-me` from any autopilot phase or agent — ever.**

`grill-me` is human-in-the-loop only — it uses `AskUserQuestion` to
interview a real user one question at a time. Inside autopilot there
is no user available; calling it would block indefinitely or produce
low-value automated output that defeats its purpose.

Autopilot's Clarify phase uses `/speckit-clarify` with the multi-agent
consensus protocol — the **only** sanctioned clarification mechanism
inside autopilot. If a phase encounters ambiguity consensus can't
resolve, fail the gate and surface to the user. **Never escalate to
grill-me.**

Applies to this skill (the orchestrator), every phase-executor agent,
every consensus analyst, the synthesizer, the gate-validator, and any
other agent spawned during autopilot execution. `grill-me` is for
**pre-workflow** human alignment via `/speckit-pro:speckit-scaffold-spec` or
`/speckit-pro:grill-me` only; it must not appear in any phase agent's
tool call history.

</hard_constraints>

### 1. Subagent per phase

For each phase, spawn a **foreground subagent** via the Agent
tool. The subagent runs the `/speckit-*` command and returns a
summary. You (the parent) receive the result as a tool call
response, which keeps your agent loop alive.

**Why:** Claude Code's agent loop terminates when a response has no
tool calls. A direct `Skill()` call loads the command into YOUR
context; the command's "report completion" instruction makes you
output plain text and the loop dies. With subagents, the command
runs in isolated context — the result returns as a tool response and
your loop continues.

### 2. Use phase-specific executor agents

Each phase type has its own specialized executor agent. All noise
stays in the subagent's context; the parent receives only a summary.

| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `phase-executor` | Heavy reasoning (Specify, Plan); mechanical for Tasks. Single skill invocation, single summary. |
| Clarify | `clarify-executor` | Read-only question set; parent answers and edits |
| Checklist | `checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `analyze-executor` | Must run analysis AND remediate ALL findings with research |
| Implement | per-task routing | Task-level dispatch: routes each task to best-fit agent with TDD protocol |

Full `Agent(...)` prompt template + per-phase prefixes live in
[`references/phase-execution.md`](./references/phase-execution.md)
§Subagent Delegation.

### 3. Task list first

Before executing any phase, create a granular task list using
TaskCreate. The task list drives the loop — after each subagent
returns, check it to know what's next. See Step 1.1 for the
full naming pattern and rules.

### 4. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow file.
Spawn a **separate subagent for each prompt** and run the two-layer
resolution (Rule 6) after each one BEFORE spawning the next — later
sessions/domains may depend on earlier resolved items. Do not batch
all sessions and check for markers only at the end.

Per-phase flow templates (per-session for Clarify, per-domain for
Checklist) live in
[`references/phase-execution.md`](./references/phase-execution.md)
§Phase-by-Phase Execution.

### 5. Clarify — executor returns questions to parent

The `clarify-executor` is read-only. It does not invoke
`/speckit-clarify`, does not wait on a user, and does not edit
artifacts. It inspects the workflow prompt, feature spec, and repo
evidence, then returns a `Clarify Question Set` containing up to 5
prioritized questions, recommended answers, evidence, and suggested
artifact updates.

The parent orchestrator answers the returned questions in the main
session, applies the spec/workflow/state edits, then checks for
remaining `[NEEDS CLARIFICATION]` markers and resolves unresolved
items via consensus if needed (see Rule 6).

### 6. Two-layer resolution with category-routed consensus

After EACH executor subagent returns for a consensus phase
(Clarify, Checklist, Analyze), run a two-layer resolution
process BEFORE spawning the next subagent.

**Layer 1 — Executor prepares evidence:** Clarify is different
from Checklist and Analyze. The `clarify-executor` returns questions
and recommendations to the parent; the parent answers and applies
accepted edits. `checklist-executor` and `analyze-executor` still
resolve most items directly and apply fixes to artifacts. Any item
that needs further resolution is flagged in an "Unresolved for
consensus" summary section, **each prefixed with one or more category
tags** (`[codebase]`, `[spec]`, `[domain]`, `[security]`,
`[ambiguous]`).

**Layer 2 — Category-routed consensus** (Tier A): for ALL unresolved
items in the phase, **batch-dispatch the union of routed analysts in
ONE assistant message** (`run_in_background: true`), wait for all,
then batch-dispatch ALL synthesizers in ONE message, then apply each
synthesizer's Artifact Edit **serially** (orchestrator's own `Edit`
calls — avoids write contention on spec.md/plan.md/tasks.md).
Escape-hatch to Round 2 (remaining analysts, full fan-out + 2-of-3
majority) on `[ESCAPE_TO_ROUND_2]` or low confidence, also batched.
`[security]` always uses all 3 in Round 1. Full routing table, Round-2
algorithm, batched-dispatch pseudocode, and the "no silently-shipped
low-confidence answers" escape-hatch rationale live in
[`references/consensus-protocol.md`](./references/consensus-protocol.md)
§Category-Routed Dispatch + §Batched Dispatch.

**Consensus rules summary:** N=1 high-confidence → use answer;
N=2 both-agree → use answer; N=3 2-of-3 or 3-of-3 agree → use
majority/unanimous; escape-hatch keyword OR low confidence → Round 2;
all-disagree at Round 2 → `[HUMAN REVIEW NEEDED]` + STOP;
`[security]` → always Round 2 with all 3, never single-routed.
Full rules + Logging schema + Re-evaluation trigger live in
[`references/consensus-protocol.md`](./references/consensus-protocol.md).

**Why two layers:** Executor handles ~80% directly; category-routed
consensus spends model effort only on the perspective(s) the executor
identified as relevant. Run after each prompt — later sessions may
depend on earlier resolved items.

## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]
```

## Step -1 + Step 0: Pre-flight (Archive Sweep + Prerequisites)

Run the pre-flight sequence before any phase work. STOP on failure.

1. **Resolve `SKILL_SCRIPTS`** from the skill header's base directory
   (append `/scripts`). All script invocations below use it as prefix.
   `CLAUDE_PLUGIN_ROOT` is unavailable in Bash; use the literal path.
2. **Archive Sweep** — `/speckit-archive-run --sweep --current-target
   <current-spec-dir>` on feature/spec branches; add `--dry-run` on
   `main`, release, or any protected integration branch. Skip if the
   archive extension is absent. Excludes the current target spec.
3. **Run prereq scripts** and parse the JSON output of each:
   ```text
   Bash("bash '<SKILL_SCRIPTS>/check-prerequisites.sh' <workflow_file>")
   Bash("bash '<SKILL_SCRIPTS>/detect-commands.sh'")
   Bash("bash '<SKILL_SCRIPTS>/detect-presets.sh'")
   ```
   Record `on_feature_branch`, `PROJECT_COMMANDS`, `PRESET_CONVENTIONS`,
   and MCP availability into the workflow file. Pass `PROJECT_COMMANDS`
   and `PRESET_CONVENTIONS` to every subagent prompt.
4. **Constitution validation** — for each principle in
   `.specify/memory/constitution.md`, run the appropriate
   PROJECT_COMMANDS check (typecheck/test/build/lint); update the
   workflow's Prerequisites table. STOP on any failure.
5. **Implementation agent detection** — Glob `.claude/agents/*.md`,
   match descriptions against implementation keywords; set
   `PROJECT_IMPLEMENTATION_AGENT` (fallback: `phase-executor`). Also
   check CLAUDE.md for an explicit agent reference.
6. **Load settings + Agent Teams probe** — read `.claude/speckit-pro.local.md`
   (`consensus-mode`, `gate-failure`, `auto-commit`, `security-keywords`);
   record `AGENT_TEAMS_AVAILABLE` from env+version probe (see prerequisites.md §Step 0.6).
6b. **Resolve pre-Implement confidence gate mode** — run
   `<SKILL_SCRIPTS>/resolve-confidence-mode.sh -- <argv>` to resolve
   the mode for G6.5 (precedence: `--strict` / `--advisory` flag
   in argv > `confidence_gate_mode` in local config > default
   `advisory`). If the script exits 2 (both flags passed), STOP
   the autopilot before Phase 0 with the conflict message — fail
   fast on usage errors. Record the resolved value as
   `CONFIDENCE_GATE_MODE` for use at G6.5. **Do not re-run the
   script at G6.5; G6.5 reads `CONFIDENCE_GATE_MODE` directly.**
   See [Gate Validation §G6.5](./references/gate-validation.md#g65--pre-implement-confidence-gate-between-analyze-and-implement).

**Plugin agent caveat:** `permissionMode`, `hooks`, and `mcpServers`
frontmatter are silently ignored on plugin agents. Run the parent
session in `acceptEdits` or `bypassPermissions` for smooth execution.
See `references/plugin-limitations.md`.

**Full per-step details, JSON schemas, MCP fallback behavior, and
failure-escalation rules:** see [`references/prerequisites.md`](./references/prerequisites.md).

## Step 1: Parse Workflow State

Read the workflow file and parse the "Workflow Overview" status
table. Find the first phase with status `⏳ Pending` or
`🔄 In Progress`.

If `--from-phase` is specified, start from that phase regardless of
the status table.

If all phases are `✅ Complete`, report "All phases complete" and
stop.

### 1.1 Create Progress Task List

After parsing the workflow state, create a **granular** task list. For
multi-prompt phases (Clarify, Checklist), create one task per
prompt/session. **Every Clarify session, every Checklist domain, and
the Analyze phase MUST have a paired Consensus task** immediately
after (skipped only if the executor reports zero unresolved items).

The full **13-entry Post-Implementation task list** and the task
naming pattern live in
[`references/task-list-canonical.md`](./references/task-list-canonical.md).
Every entry there MUST appear in the visible progress panel before
Phase 1 starts — when an extension is absent, the task still appears
marked `skipped: <ext-name> not installed`.

**Verify completeness before starting Phase 1**: count the prescribed
entries (every Phase, every Consensus, every `Post:`) and ADD any
missing before advancing.

## Step 2: Main Execution Loop

For each pending phase, spawn a subagent, collect the result, validate
the gate, advance. Every step is a tool call.

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    1. TaskUpdate: phase task → in_progress
    2. Run before_<phase> hooks from .specify/extensions.yml
    3. For each workflow prompt in this phase:
         Agent(subagent_type: <phase executor>, prompt: ...)
    4. Run consensus (Clarify/Checklist/Analyze only) — see Rule 6
    5. Run after_<phase> hooks
    6. Validate gate via gate-validator agent → parse PASS/FAIL
       On FAIL: auto-fix max 2 attempts; then honor gate-failure setting
    7. Update workflow file; auto-commit if configured
         phases 1-6: git add specs/ && git commit
         phase 7:    git add -A && git commit
    7b. After Plan (G3 pass, plan.md exists), run the plan-phase
        reviewability budget: estimate-reviewable-loc.sh <plan.md>,
        guarded against errexit. Branch on JSON `status`
        (pass / over_budget / not_estimated) or the exit code.
        ADVISORY — never blocks, prompts mid-autonomous-run, or
        crashes the run (hard block / re-slicing is PRSG-010).
    8. After Tasks (G5 pass), run reviewability-gate.sh tasks;
       unexcepted `block` → STOP and split the spec
    9. Advance
```

**Full per-phase prompts, dispatch templates, gate validation
details, hook events, and the dispatcher-agent table:**
see [`references/phase-execution.md`](./references/phase-execution.md).

After all 7 phases pass G7, execute the post-implementation task list.
The 13 tasks, detailed prompts, and extension routing live in
[`references/post-implementation.md`](./references/post-implementation.md);
the canonical name list is in
[`references/task-list-canonical.md`](./references/task-list-canonical.md).

**⚠️ Use `Agent()` subagents for ALL post-implementation tasks — NEVER
`Skill()` directly.** Rule 1 applies: a `Skill()` call loads the
command into YOUR context and the command's completion text can kill
the agent loop, preventing subsequent tasks from running.

**Extension availability**: Step 0.12 records which extensions are
installed in `.registry`. If an extension is missing, log a warning
and mark its task `skipped: <ext> not installed` — do NOT fail the
autopilot. Recommend `specify extension add <name>` in the warning.

**Dynamic task updates:** If consensus reveals new questions or
remediation adds loops, create additional tasks via TaskCreate.

### Phase Dispatch

Every subagent prompt includes the workflow-file prompt plus, when
present, `PRESET_CONVENTIONS` (from Step 0.12) and `PROJECT_COMMANDS`
(from Step 0.11). The full `Agent(...)` template lives in
[`references/phase-execution.md`](./references/phase-execution.md)
§Subagent Delegation.

**Agent selection:**

| Phase | subagent_type | Prefix |
| ----- | ------------- | ------ |
| Specify | `phase-executor` | Branch-aware when `ON_FEATURE_BRANCH` (skip `create-new-feature.sh`) |
| Clarify | `clarify-executor` | Read-only — returns a Clarify Question Set; parent answers + applies edits |
| Plan | `phase-executor` | None |
| Checklist | `checklist-executor` | One subagent per domain |
| Tasks | `phase-executor` | None |
| Analyze | `analyze-executor` | None |
| Implement | per-task routing | TDD protocol + COMPLETED_TASKS — see Implement — Task-Level Dispatch below |

Per-phase prefix templates (branch-aware Specify prefix, Clarify
question-set contract, multi-prompt fan-out for Clarify sessions and
Checklist domains) live in
[`references/phase-execution.md`](./references/phase-execution.md)
§Phase-by-Phase Execution.

#### Resolution — After Each Prompt (Main Session)

After EACH executor subagent returns for a consensus phase (Clarify,
Checklist, Analyze), apply the two-layer category-routed protocol —
Layer 1 marker scan, Layer 2 routed-analyst dispatch with Round 2
escape-hatch, post-resolution per-phase verification, and mandatory
Consensus Resolution Log rows. Full protocol, per-phase verification
prompts, and canonical log columns live in
[`references/consensus-protocol.md`](./references/consensus-protocol.md)
§Phase-Specific Consensus Flows + §Logging.

#### Implement — Task-Level Dispatch (honors `[P]` markers)

Phase 7 dispatches each task to the best-fit agent and **honors `[P]`
parallel-safe markers from `/speckit-tasks`** for batched parallel
execution. Within a phase group, partition tasks into runs:
**consecutive `[P]` tasks form a parallel run; non-`[P]` tasks are
singletons.** Dispatch each parallel run in ONE assistant message via
background subagents. Sequential runs spawn one foreground agent, await,
advance. After every parallel run, run TYPECHECK + UNIT_TEST as a
safety net; on regression, fall back to serial re-run for that group.

**Agent routing:**

| Task Type | Agent | TDD? |
|-----------|-------|------|
| Tests (contract/unit/integration) | `implement-executor` | Yes |
| Domain implementation | PROJECT_IMPLEMENTATION_AGENT | Yes |
| Research / API investigation | `domain-researcher` | No |
| Verification (build, lint) | orchestrator-direct | No |

Every implementation agent receives the TDD protocol from
`references/tdd-protocol.md`. Agent selection is about domain
expertise — all follow identical RED-GREEN-REFACTOR discipline.

**Full algorithm** (parse tasks, partition into runs, route, batched
dispatch for `[P]` runs, accumulate context, verify): see
[`references/phase-execution.md`](./references/phase-execution.md)
§Phase 7 Step 3.

This is **Use site 3** of the [Agent Teams integration map](./references/agent-teams-integration.md)
— when `AGENT_TEAMS_AVAILABLE=true`, parallel runs spawn as a team
(cross-task mailbox coordination); otherwise batched background
subagents in one message (same wall-clock, no team coordination).

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes, follow the
detailed procedures in `references/post-implementation.md`:

1. **3.0 Parallel group** — auto-routed by `AGENT_TEAMS_AVAILABLE` (teams vs parallel-subagents)
2. **3.1 Integration Suite** — verify spec-specific tests
   exist, run FULL suite to catch regressions, fix failures
3. **Self-Review** — mandatory 4-question audit between Integration
   Suite and the PR body; findings are recorded in the workflow log and
   reproduced in the PR body. Reporting step — never gates the PR.
4. **UAT Runbook Generation** — mandatory between Self-Review and the
   PR body: run `generate-uat-skeleton.sh` to write
   `<feature-dir>/.process/uat-runbook.md`, then spawn the
   `uat-runbook-author` subagent to rewrite the skeleton into plain,
   executable steps, then commit it. Both the script and the author step
   are fail-open (never block the PR) but NOT optional — they run.
5. **3.2 PR Creation** — final verification, reviewability diff gate,
   then build the PR body by running `generate-pr-body.sh` →
   `.git/speckit-pr-body.md`, fill its **What changed / Why it matters /
   Anything reviewers should know** sections in plain English (no internal
   jargon; governance stays in the collapsed details block), and open the
   PR with `--body-file .git/speckit-pr-body.md`. **Never write the body
   from scratch or pass an inline `--body`** — the script is what embeds
   the review packet and the `## UAT Runbook` section (which carries the
   Self-Review findings).
   Before `gh pr create`, confirm the body file carries the
   `speckit-pro-review-packet-source` marker and a `## UAT Runbook`
   heading; if either is missing, regenerate with the script once. Push,
   create PR, update workflow file.
6. **3.3 Review Remediation** — schedule `/loop` to monitor
   and resolve Copilot/human review comments every 5 minutes

After scheduling the loop, the autopilot is DONE. Report
the final summary with PR URL.

## Workflow File Update Protocol

After EVERY phase, update the workflow file so it remains the
durable source of truth across context compactions and resumes:
status table `⏳` → `✅` with summary notes; per-phase Results
tables; Constitution Validation table after Specify (initial) and
Implement (final); Consensus Resolution Log row per resolution
(when consensus was used).

Full per-phase update table and Consensus Resolution Log column
schema live in
[`references/workflow-file-protocol.md`](./references/workflow-file-protocol.md).

## Error Recovery

- **Resume:** `/speckit-pro:speckit-autopilot workflow.md --from-phase
  <next-pending-phase>` — the workflow file persists all state.
- **Gate fails after 2 auto-fix attempts:** honor `gate-failure`
  setting (default `stop`); on STOP, show gate script output.
- **Consensus all-disagree** (Round 2): flag `[HUMAN REVIEW NEEDED]`,
  STOP, and present all 3 perspectives to the user.
- **MCP tool unavailable:** skip dependent research; use Read/Grep
  fallback; log a warning.
- **Context window pressure:** keep subagent summaries concise; the
  workflow file is the durable record (re-read after compaction).

Full details, additional failure modes, and recovery playbooks live
in [`references/error-recovery.md`](./references/error-recovery.md).

## References

- [Prerequisites](./references/prerequisites.md) — Archive Sweep + Step 0.x environment, settings, constitution, agent detection, command/preset discovery
- [Phase Execution](./references/phase-execution.md) — Per-phase prompt construction, dispatch templates, branch-aware/Clarify/Multi-prompt prefixes
- [Consensus Protocol](./references/consensus-protocol.md) — Category-routed dispatch, Round 1/2, per-phase flows, Logging schema
- [Gate Validation](./references/gate-validation.md) — Programmatic gate checks (G0–G7), auto-fix loops, escalation
- [Post-Implementation](./references/post-implementation.md) — 13-task post-impl sequence (incl. self-review, UAT runbook), integration suite, PR creation, review loop
- [Task List Canonical](./references/task-list-canonical.md) — Task naming pattern + canonical post-implementation entries
- [Workflow File Protocol](./references/workflow-file-protocol.md) — Per-phase update table + Consensus Resolution Log column schema
- [Error Recovery](./references/error-recovery.md) — Resume, common issues, context-window management
- [TDD Protocol](./references/tdd-protocol.md) — Red-green-refactor rules injected into implementation agent prompts
- [Plugin Limitations](./references/plugin-limitations.md) — permissionMode/hooks/mcpServers caveats, MCP fallback behavior
- [Agent Teams Integration](./references/agent-teams-integration.md) — Use-site map (current + planned), capability detection, lifecycle policy
- [Token Discipline](./references/token-discipline.md) — Opt-in compressed vocabulary for inter-agent transcripts (off by default; never applied to PR bodies, logs, or artifacts)

## Scripts

Deterministic bash scripts for prerequisite checks and validation.
These ship with the **plugin** at `<SKILL_SCRIPTS>/` (resolved in
Step 0.0 from the skill header's base directory path).
Always invoke via the full resolved path — never from `.specify/scripts/bash/`.

- `check-prerequisites.sh <workflow_file>` — Verify CLI,
  project init, constitution, commands, branch detection (JSON)
- `validate-gate.sh <G1-G7> <feature_dir>` — Validate
  any gate with marker counts and details (JSON)
- `confidence-gate.sh <workflow-file> [--threshold N.NN] [--mode advisory|strict]` —
  Read the synthesizer's `📊 Confidence: X.XX` pre-Implement emit and decide
  whether Phase 7 may begin. Exit: 0 PASS, 1 NO_DATA (soft-skip), 2 FAIL.
  See [Gate Validation §G6.5](./references/gate-validation.md#g65--pre-implement-confidence-gate-between-analyze-and-implement).
- `resolve-confidence-mode.sh [--config <path>] [--] <argv>` —
  Resolve the pre-Implement confidence gate mode (advisory|strict) for
  the current invocation. Precedence: `--strict`/`--advisory` flag in argv >
  `confidence_gate_mode` in `.claude/speckit-pro.local.md` > default
  `advisory`. Exit: 0 resolved, 2 flag conflict, 1 usage error. Used by
  the orchestrator in Step 0.6b to set `CONFIDENCE_GATE_MODE` before G6.5.
- `reviewability-gate.sh <setup|tasks|diff> <path-or-range>` —
  Enforce setup, tasks, and pre-PR reviewability budgets (JSON)
- `estimate-reviewable-loc.sh <plan.md>` — Plan-phase reviewability
  budget: project production-LOC from `plan.md`'s declared file
  structure and emit a three-value `status` (`pass` / `over_budget` /
  `not_estimated`) in JSON. Advisory — the three statuses return exit 0
  (verdict in `status`); only a usage/IO error exits non-zero. Wired
  into the Plan phase advisory-and-never-crash (see
  [Phase Execution §Phase 3: Plan](./references/phase-execution.md#phase-3-plan)).
- `generate-pr-body.sh <repo-root> <feature-dir> <output-file> [diff-range]` —
  Generate a PR review packet from the host repository PR template when present,
  or from the bundled fallback template
- `generate-uat-skeleton.sh <spec-path> <output-path> [--workflow-file <path>]` —
  Render a deterministic UAT runbook skeleton from `spec.md` (Env Setup formatted
  from the `UAT_PROJECT_COMMANDS` env var). Exit 0/2/1; silent stdout. Run after
  Self-Review and before PR-body generation (fail-open). See
  [Post-Implementation §UAT Runbook Generation](./references/post-implementation.md#uat-runbook-generation)
- `detect-commands.sh` — Auto-detect build/test/lint
  commands for Node.js, Rust, Go, Python, Makefile (JSON)
- `detect-presets.sh` — Find installed presets,
  extensions, hooks, template resolution (JSON)
- `count-markers.sh <type> <feature_dir>` — Deterministic
  marker counting (gaps, findings, clarifications, all) for agent
  validation. Used by analyze-executor and checklist-executor (JSON)

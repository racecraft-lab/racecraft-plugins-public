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
allowed-tools: Read Edit Write Glob Grep Skill Agent WebFetch WebSearch ToolSearch
license: MIT
---

# SpecKit Autopilot — Autonomous Execution Engine

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Scope

This skill handles autonomous workflow EXECUTION. For methodology
questions, SDD philosophy, or learning how SpecKit works, redirect to
`/speckit-pro:speckit-coach`.

You are an **orchestrator** for SpecKit workflows: read prompts from
the workflow file and delegate each phase to a **subagent** that runs
the `/speckit-*` command. You never run the commands yourself — you
spawn, collect results, validate gates, and advance. Your context
window auto-compacts; do not stop early — complete every phase in the
**resolved stage's** range (`AUTOPILOT_STAGE`, set at Step 0.6c). A
`--stage plan` run that stops after the confidence gate has finished its
work; a `full` run completes all 7 phases.

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

Runtime enforcement is two-tier (Layer 5 verifies both): the
hyper-focused single-purpose workers (the consensus analysts,
clarify-executor, gate-validator, uat-runbook-author) explicitly deny
`Agent`/`TeamCreate`/`SendMessage` via `disallowedTools` so they stay
on their one job; the open workhorse executors (phase-, analyze-,
checklist-, implement-executor) keep the operator's full surface —
including orchestration tools — and the invariant there is carried by
this skill owning all PHASE dispatch plus each executor's
terminal-worker prompt, never by a capability block. **If this skill is ever loaded inside a subagent
context**, it MUST refuse rather than orchestrate. Full invariant +
implications for new workstreams in
[`references/agent-teams-integration.md`](./references/agent-teams-integration.md)
§Single orchestrator invariant.

The no-allowlist rule is about **agent definitions**: Claude agents must omit
`tools:` so they inherit the operator's installed surface. This skill's
frontmatter may still declare Claude `allowed-tools` to authorize the
orchestrator's core primitives; that declaration is not an MCP/vendor
availability list and does not replace runtime capability discovery.

## Prerequisites — Model

The orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Weak-model orchestration cascades into
expensive rework.

**Before executing any step**, verify:

1. **Model:** Opus 4.6 or better. On Sonnet/Haiku/older Opus, STOP and
   instruct: *"Autopilot requires Opus 4.6 for reliable orchestration.
   Please `/model opus` and re-run."*

**Reasoning effort is inherited, never checked.** Run at whatever the
operator has set for the session and do not stop, warn, or ask them to
change it. Higher effort produces better orchestration, so the bundled
subagents still ship pinned at `effort: max` (or `xhigh` on Codex) —
that pin only ever raises a worker's effort and never refuses to run.
The operator owns the session setting; the plugin does not veto it.

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

### 0.5 Static Tier-2 relocation suggestions only

<hard_constraints>

Autopilot may surface Tier-2 PROCESS relocation guidance for thawed legacy
specs, but it must never execute relocation mutation from any autopilot phase,
subagent, or post-implementation step.

</hard_constraints>

At startup and when evaluating the active workflow target, inspect candidate
state directly. Suggest relocation only for a thawed in-scope legacy spec that
has root PROCESS allow-list artifacts or matching docs-side scaffold artifacts.

For an eligible candidate, print the concrete `specs/<spec-dir>` value and say
that relocation remains manual operator work outside autopilot. Describe any
write as a follow-up after review and a clean worktree.
Suppress the suggestion and report the reason for:

- `frozen/in-flight` specs named by `.specify/feature.json`
- invalid active-feature state
- already-current specs with `SPEC-MOC.md` `structureVersion: 1`
- already-normalized specs whose PROCESS artifacts are under `.process/`
- candidates with no relocatable PROCESS artifacts
- out-of-scope `non_speckit_namespace` and `date_named_legacy_namespace`
  candidates

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

**Third-party skills:** the same hazard applies when capability discovery
selects an *installed* skill you invoke via `Skill()` — its completion text
can end your loop. Capture the skill's result as evidence and continue with a
follow-up tool call; never treat a third-party skill's completion text as your
own terminal output.

### 2. Use phase-specific executor agents

Each phase type has its own specialized executor agent. All noise
stays in the subagent's context; the parent receives only a summary.

| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `speckit-pro:phase-executor` | Heavy reasoning (Specify, Plan); mechanical for Tasks. Single skill invocation, single summary. |
| Clarify | `speckit-pro:clarify-executor` | Read-only question set; parent answers and edits |
| Checklist | `speckit-pro:checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `speckit-pro:analyze-executor` | Must run analysis AND remediate ALL findings with research |
| Implement | per-task routing | Task-level dispatch: routes each task to best-fit agent with TDD protocol |

Full `Agent(...)` prompt template + per-phase prefixes live in
[`references/phase-execution.md`](./references/phase-execution.md)
§Subagent Delegation.

**Agent-type namespacing (required):** the prefix requirement applies to every
speckit-pro **bundled agent id** used as a `subagent_type` value — the
executors above and the analysts in the routing tables below dispatch with
their `speckit-pro:` prefix (`speckit-pro:phase-executor`,
`speckit-pro:clarify-executor`, …). The runtime resolves plugin agents by their
namespaced id, so a bare `subagent_type: "phase-executor"` fails immediately
with `Agent type 'phase-executor' not found`. Identifiers that take **no**
prefix: `general-purpose` (a built-in agent), and entries in the tables that are
not bundled agent ids — the `PROJECT_IMPLEMENTATION_AGENT` variable (resolved to
a host-project agent, with `speckit-pro:phase-executor` as its fallback value)
and `orchestrator-direct` (the orchestrator acting directly, not a subagent).

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
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID] [--stage plan|implement|full] [--strict | --advisory]
```

`--stage` selects which range of phases this invocation runs; omit it and
Step 0.6c resolves the stage from the workflow file's own status table.
Argument order is presentation only — every argument is read by name.

## Step -1 + Step 0: Pre-flight (Archive Sweep + Prerequisites)

Run the pre-flight sequence before any phase work. STOP on failure.

1. **Use runner helper operation IDs**. Invoke read-only helper behavior through
   `resolved_python -m speckit_pro_runner` with one JSON request on stdin; do not rely on
   plugin-local script files.
2. **Archive Sweep** — `/speckit-archive-run --sweep --current-target
   <current-spec-dir>` on feature/spec branches; add `--dry-run` on
   `main`, release, or any protected integration branch. Skip if the
   archive extension is absent. Excludes the current target spec.
3. **Run prereq helper operations** and parse the JSON output of each:
   ```text
   helper_id=check-prerequisites operation=check-prerequisites mode=read_only
   helper_id=detect-commands operation=detect-commands mode=read_only
   helper_id=detect-presets operation=detect-presets mode=read_only
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
   `PROJECT_IMPLEMENTATION_AGENT` (fallback: `speckit-pro:phase-executor`). Also
   check CLAUDE.md for an explicit agent reference.
6. **Load settings + Agent Teams probe** — read `.claude/speckit-pro.local.md`
   (`consensus-mode`, `gate-failure`, `auto-commit`, `security-keywords`);
   record `AGENT_TEAMS_AVAILABLE` from env+version probe (see prerequisites.md §Step 0.6).
6b. **Resolve pre-Implement confidence gate mode** — run runner helper
   `resolve-confidence-mode` with the invocation argv to resolve
   the mode for G6.5 (precedence: `--strict` / `--advisory` flag
   in argv > `confidence_gate_mode` in local config > default
   `advisory`). If the script exits 2 (both flags passed), STOP
   the autopilot before Phase 0 with the conflict message — fail
   fast on usage errors. Record the resolved value as
   `CONFIDENCE_GATE_MODE` for use at G6.5. **Do not re-run the
   resolver at G6.5; G6.5 reads `CONFIDENCE_GATE_MODE` directly.**
   See [Gate Validation §G6.5](./references/gate-validation.md#g65--pre-implement-confidence-gate-between-analyze-and-implement).
6c. **Resolve the stage** — run runner helper `resolve-autopilot-stage`
   with the invocation argv and the workflow file path. It returns one
   JSON envelope; record `stage` as `AUTOPILOT_STAGE` and keep `source`,
   `basis`, `recorded_stage`, `planning_complete`, and
   `confidence_gate_status` for the phase loop. An explicit `--stage`
   always wins; with none given the stage is resolved from the workflow
   file's `## Workflow Overview` table. If the operation exits 2
   (unrecognised stage, `--stage` repeated with different values,
   `--from-phase` outside an explicitly named stage's range, `--stage`
   with no value, or an unreadable/unparseable workflow file), STOP the
   autopilot before Phase 0 with that one-line message — the same
   fail-fast shape 0.6b uses. **Print the resolved stage and its basis
   before any phase work begins** — before Phase 0, before the Step 1
   coverage guard, and before the first subagent dispatch. Emit one line,
   `Stage: <stage> (<source>) — <basis>`, using the envelope's `basis`
   verbatim. For an auto-detected stage that basis names the first
   non-terminal planning phase and its status, which is the row the operator
   has to act on; `plan` after a strict-mode gate stop reads
   `the first non-terminal planning phase is Confidence Gate, which is
   ⚠️ Blocked` rather than an unexplained stage token.
   If Step 0.6d reclaimed the slot, append
   `reclaimed the state slot from <prior workflow file> (prior status:
   <prior_run_note>)` to the same report. A `prior_run_note` of
   `in_progress` is the only available signal that a second run may still be
   live — the state file records no pid, heartbeat, or lease — so it is
   **reported, never blocking**. The stage bounds which phases this
   run may start: see
   [Phase Execution §Stage-Bounded Phase Selection](./references/phase-execution.md#stage-bounded-phase-selection).
6d. **Reclaim the state slot if it names another workflow** — `autopilot-state.json`
   holds exactly one run. When this invocation targets a workflow file the state
   file does not currently name, **re-initialise the slot from the target
   workflow file before continuing**: rewrite `workflow_file`, `spec_id`,
   `feature_dir`, `branch`, `status`, `stage`, and `plan`. Reclaiming is normal
   operation — one slot, many specs — and is **not** an error.
   - **This runs before the Step 1 coverage guard, not after.** The guard's
     workflow-identity check fails a run whose state names a different
     specification, so ordering re-initialisation after the guard would turn
     every legitimate reclaim into a guard halt — the run stops at Step 1.1
     before the slot is rewritten. Reclaiming first rewrites `workflow_file`
     from the target, and the guard then compares two references that agree.
   - The trigger is **unscoped by stage**. Any stage can be the one that finds a
     foreign slot, and the ordering holds for all of them.
   - Record the reclaimed run's `status` **verbatim** in `prior_run_note` before
     overwriting it, so `in_progress` stays distinguishable from `completed` or
     `completed_archived`. Surface it in the Step 0.6c report.
   - **It MUST NOT block.** The state file carries no liveness evidence — no pid,
     no heartbeat, no lease — so `in_progress` cannot distinguish a live run from
     one abandoned to a crash or a closed terminal. Blocking on it would strand
     every run that followed an interrupted one. Report it and proceed.
6e. **Preserve the prerequisite test-count baseline; do not recompute it** — if
   the workflow file already records a G0 test-count baseline, **keep it.** The
   post-implementation gate verifies the count *increased* against that baseline
   (see [Gate Validation §G7](./references/gate-validation.md#g7--after-implement)),
   and a baseline recaptured after planning already contains whatever the run
   added, which makes the comparison vacuous — it would compare the tree against
   itself and pass unconditionally. A `--stage implement` run in a fresh session
   is exactly when this is tempting and exactly when it is wrong.
   - If a newly observed count differs from the recorded baseline, record it as a
     **non-blocking drift diagnostic** naming both numbers. Do **not** replace the
     baseline with it. Drift means the tree moved underneath the spec, which the
     operator should see; it is not grounds to stop.
   - **Resume protocol (both distributions).** A run that resumes in a fresh
     session, or in a different working copy, reconstructs its context from the
     **workflow file**, which is durable and survives archiving of `specs/<id>/`:
     the `## Workflow Overview` status table, the `Stage` row, the recorded
     `Confidence Gate` verdict, and the G0 baseline. `autopilot-state.json` is a
     mirror of the active run and may be absent, stale, or naming another spec —
     each is recoverable, and none is an error. A **missing** state file is
     rebuilt from the workflow file; a state file naming **another** workflow is
     reclaimed per Step 0.6d. The one carve-out is the pull-request marker plan,
     which keeps its own stricter stop-rather-than-infer rule and is **not**
     relaxed to satisfy this resume path.
7. **Capability enumeration, grounding & feed-down** — you are the only
   component that discovers openly. Before relying on any capability, enumerate
   what this session actually exposes: surface deferred MCP tools with
   `ToolSearch`, and treat the available-skills list as the installed-skill
   registry. Select best-fit per
   [`references/capability-discovery.md`](./references/capability-discovery.md) —
   do not assume a fixed set; the user may have installed anything. Your phase
   and consensus subagents inherit the operator's full installed surface and
   follow the same directive — read-only roles select only read/research
   capabilities (their mutation built-ins are denied). Still pass the
   discovered evidence and capability context a subagent needs directly in its
   prompt: shared context beats re-discovery. Ground your OWN output
   (gate decisions, consensus synthesis, generated PR bodies) per
   [`references/grounding.md`](./references/grounding.md): every external fact
   you assert must cite a real tool/skill/file result, and you abstain when
   nothing grounds it.

**Plugin agent caveat:** `permissionMode`, `hooks`, and `mcpServers`
frontmatter are silently ignored on plugin agents. Run the parent
session in `acceptEdits` or `bypassPermissions` for smooth execution.
See `references/plugin-limitations.md`.

**Full per-step details, JSON schemas, capability fallback behavior, and
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

The full **12-entry Post-Implementation task list** and the task
naming pattern live in
[`references/task-list-canonical.md`](./references/task-list-canonical.md).
Every entry there MUST appear in the visible progress panel before
Phase 1 starts — when an extension is absent, the task still appears
marked `skipped: <ext-name> not installed`.

**Verify completeness before starting Phase 1**: count the prescribed
entries (every Phase, every Consensus, every `Post:`) and ADD any
missing before advancing.

**Then run the deterministic coverage guard and STOP on a nonzero exit.**
This is the same guard the Codex variant runs, so both distributions share
one enforcement path instead of two prose descriptions of one:

```text
Command("<resolved_python> '<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py' --workflow <workflow-file-path> --state <workflow-directory>/autopilot-state.json --rule status-evidence")
```

`--rule status-evidence` scopes the **exit code** to the bookkeeping rule.
The full report is still printed, so the structural coverage lists remain
visible and worth fixing — but they do not block, because most of the existing
workflow corpus predates them and a blocking guard would make those specs
unresumable. Drop `--rule` to gate on every check once a spec is migrated.

`<resolved_python>` is the Python 3.11+ interpreter resolved by the
Installed Runtime Contract; `<plugin-root>` is the directory that owns
`skills/speckit-autopilot/`. Exit 0 is required to advance; exit 1 reports
the failing checks as JSON on stdout; exit 2 is an input error. The guard
also fails when a Workflow Overview status row contradicts a gate verdict
recorded elsewhere in the same file, which is what keeps the status table
honest across compactions and manual phase runs.

**Expected-commit flags — contract stated, not yet wired here.** When
`pr-marker-plan.v2` declares a changed-file manifest, the guard accepts
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`.
Both OIDs must be fetched from live PR metadata immediately before every
validation and never sourced from the workflow, state, or manifest itself, and
missing, stale, or mismatched external PR authority is blocking. **The Claude
flow does not fetch those values yet**, so the PR-head byte comparison the flags
feed is unreachable on this platform and runs only on Codex today. This is a
statement of the contract, not of current behavior. **ART-016** wires the fetch
and removes this caveat.

## Step 2: Main Execution Loop

For each pending phase, spawn a subagent, collect the result, validate
the gate, advance. Every step is a tool call.

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]

for phase in PHASES starting from first_pending:
    0. Re-run the Step 1.1 coverage guard against the workflow file and
       autopilot-state.json. Exit 0 is required; on nonzero, repair the plan
       and the workflow status table, then repeat before executing this phase.
    1. TaskUpdate: phase task → in_progress
    2. Run before_<phase> hooks from .specify/extensions.yml
    3. For each workflow prompt in this phase:
         Agent(subagent_type: <phase executor>, prompt: ...)
    4. Run consensus (Clarify/Checklist/Analyze only) — see Rule 6
    5. Run after_<phase> hooks
    6. Validate gate via gate-validator agent → parse PASS/FAIL
       On FAIL: auto-fix max 2 attempts; then honor gate-failure setting
    7. Update workflow file; auto-commit if configured
         phases 1-6: git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit
         phase 7:    git add -A && git commit
    7b. After Plan (G3 pass, plan.md exists), run the plan-phase
        reviewability budget with runner helper `estimate-reviewable-loc`,
        guarded against errexit. Branch on JSON `status`
        (pass / over_budget / not_estimated) or the exit code.
        ADVISORY — never blocks, prompts mid-autonomous-run, or
        crashes the run (hard block / re-slicing is PRSG-010).
    8. After Tasks (G5 pass), apply the tasks-phase reviewability
       boundary. Runner helper `reviewability-gate` supports setup mode
       only on the installed runner — tasks mode is deferred, so do not
       invoke it as an active helper. Record the deferred-mode
       diagnostics (helper ID, requested mode, deferral reason) in the
       workflow file, then continue on the fallback evidence chain: the
       setup-mode gate result recorded at scaffold, the plan-phase
       `estimate-reviewable-loc` verdict from step 7b, and any
       operator-ratified split decision in the workflow file.
       In that committed evidence, `pass`, `warn`, honored exception,
       and valid current size-only `block` are marker-planning inputs.
       A valid current size-only block continues into marker planning
       and marker emission; it is not a manual re-slicing stop.
       Preserve correctness stops for malformed/stale marker state,
       failed verification, invalid packet, unsafe output, unusable
       gate evidence, invalid JSON, missing status/mode, stale
       fingerprints, and non-size safety findings.
    8c. After Tasks (G5 pass), run runner helper `atomicity-route`
        for `<feature-dir>`
        and record the emitted JSON decision into the workflow
        file's "## Atomicity Route" section. READ-ONLY + ADVISORY —
        the script writes nothing and never blocks; the SKILL is
        what records it.
    8d. After recording the atomicity route, run the layer planner only
        when route is exactly `split-PR`, and always before Analyze or
        Implement can continue:
        - non-split routes: record `layer_plan.status=skipped` in
          `autopilot-state.json` and the workflow "## Layer Plan" section,
          then continue with route context.
        - split route: run helper operation `plan-layers-feature-dir` for
          `<feature-dir>` and capture stdout, stderr, and exit code.
        - exit 0: parse stdout as the full versioned layer-plan envelope,
          persist it under `layer_plan` in `autopilot-state.json`, write a
          concise workflow "## Layer Plan" summary, carry warnings into the
          implementation context, then continue.
        - exit 1: STOP before implementation and print exactly:
          `STOP: Layer planner returned invalid_plan (exit 1) for <feature-dir>; implementation has not started. Fix tasks.md using the planner diagnostics below, then rerun autopilot from the Layer Plan step.`
          Then show planner diagnostics from stdout/stderr.
        - exit 2: STOP before implementation with a distinct
          `input_error` message and include planner diagnostics.
        This wires NO PR emission or branch creation (PRSG-009 owns that).
    8e. Persist marker planning state when reviewability evidence requires it:
        top-level `pr_marker_plan` in `autopilot-state.json`, mirrored
        workflow evidence, and repo-relative evidence paths. Do not treat
        `tasks.md` as authoritative marker state.
    9. Advance
```

**Full per-phase prompts, dispatch templates, gate validation
details, hook events, and the dispatcher-agent table:**
see [`references/phase-execution.md`](./references/phase-execution.md).

After all 7 phases pass G7, execute the post-implementation task list.
The 12 tasks, detailed prompts, and extension routing live in
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
| Specify | `speckit-pro:phase-executor` | Branch-aware when `ON_FEATURE_BRANCH` (skip new feature branch creation) |
| Clarify | `speckit-pro:clarify-executor` | Read-only — returns a Clarify Question Set; parent answers + applies edits |
| Plan | `speckit-pro:phase-executor` | None |
| Checklist | `speckit-pro:checklist-executor` | One subagent per domain |
| Tasks | `speckit-pro:phase-executor` | None |
| Analyze | `speckit-pro:analyze-executor` | None |
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
| Tests (contract/unit/integration) | `speckit-pro:implement-executor` | Yes |
| Domain implementation | PROJECT_IMPLEMENTATION_AGENT | Yes |
| Research / API investigation | `speckit-pro:domain-researcher` | No |
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
   PR body. The runner helper `generate-uat-skeleton` is registered as
   deferred, so do not invoke it as an active helper. Reuse a committed
   source-derived runbook when present; otherwise record the UAT skeleton as
   skipped with deferred-helper evidence, then spawn the
   `uat-runbook-author` subagent only when a skeleton exists. This is
   fail-open and must be logged.
5. **3.2 PR Creation** — final verification, then apply the final
   reviewability boundary. The runner helper `final-reviewability-backstop` is
   registered as deferred, so do not invoke it as an active helper; use current
   committed reviewability evidence or stop before PR side effects if no
   current evidence exists. Only
   `pass`, `warn`, honored typed-exception outcomes, or final `marker_split`
   with a valid current `pr_marker_plan` may continue. When a current
   `pr_marker_plan` is present, successful PR preparation uses marker-based PR
   emission even if the final full-diff gate is only `pass` or `warn`. A
   full-diff size block with current marker evidence also proceeds to
   marker-based PR emission; it is not a manual re-slicing stop. An unexcepted
   correctness block writes
   `final_reviewability_gate` state plus a `reslicing_required` packet and
   stops only the unsafe PR side effects. It is not a final answer or operator
   handoff: read `autopilot_continuation`, `operator_steps`, and
   `resume.resume_from`, then continue internally through PRSG-007/008/009
   until a valid slice PR stack is emitted or a typed exception is committed.
   Never report completion while `autopilot_continuation.required=true`; a gate
   error writes state and stops without a packet. After a proceed result,
   emit or refresh the feature-local packet at
   `specs/<feature>/.process/pr-packets/<packet-id>.json` with
   `pr-packet-output`. Run it in `dry_run` first, then `apply` only after the
   packet path, body path, base/head target, title, changed-file scope,
   verification evidence, UAT text, non-goals, and known gaps are current.
   `pr-packet-output` writes the packet JSON and packet-owned body file, and
   declares the validation-result path; `generate-pr-body` remains body-only and is not a
   packet substitute. Run `validate-pr-packet-read-only` against the emitted
   packet and consume only the current response `data.stdout_json` in memory
   and durable state. Continue only when it reports `status=passed`,
   `pr_blocked=false`, and the response reports `writes_state=false`. Commit or
   otherwise checkpoint the packet/body artifacts so the worktree is clean, then
   run `validate-pr-packet-write`; apply mode reruns read-only validation before
   persisting the packet's `validation_result_path`. Open
   the PR with packet fields through
   `gh pr create --base --head --title --body-file`; never derive the title
   from the branch, write the body from scratch, pass inline `--body`, reuse
   prior validation evidence, or repair invalid packets after creation. Before
   any single-PR create attempt, run runner helper
   `validate-pr-workflow-contract` with the packet title and changed-file
   list; a nonzero result blocks the aggregate PR path. If the changed files
   include multi-PR candidate commands or final marker-split evidence for more
   than one PR, the single-PR path is forbidden. `multi-pr-emission` may capture
   a `golden_only` command plan, but it does not emit packets or execute PRs.
   Continue only when every required feature-local packet has been emitted or
   refreshed through `pr-packet-output`, passes the same read-only validation,
   and has current persisted validation evidence. Push, create PR, update
   workflow file.
   Required evidence prompts: gate status/mode/exit/evidence path,
   fingerprint status, ordered marker IDs, checkpoints, warnings, final
   marker_split or marker-plan-ready handoff, packet validation, and PR
   mappings.
6. **3.3 Review Remediation** — schedule `/loop` to monitor
   and resolve Copilot/human review comments every 5 minutes

After scheduling the loop, the autopilot is DONE. Report
the final summary with PR URL.

## Workflow File Update Protocol

**The workflow file is the per-spec durable store.** It survives archive, so
its Workflow Overview status table is the record of what a spec did.
`autopilot-state.json` is the current-in-flight pointer for one run — it holds a
single spec's live plan and is overwritten by the next run, so it is never
per-spec history. When the two disagree **about Workflow Overview status
content**, the workflow file wins and the state file is repaired to match. A
status row that contradicts a gate verdict recorded elsewhere in the same file
fails the Step 1.1 coverage guard.

That precedence is scoped to the status table and does not generalize. The
state file stays authoritative for two things the coverage guard enforces
directly:

- **Which workflow file is active.** When the state names a `workflow_file` and
  a repository root resolves, that value is the authority. A mismatch fails with
  a message that opens with the exact sentence "supplied workflow does not match
  autopilot state workflow_file authority" and appends both compared paths. The
  comparison is skipped when the state names no `workflow_file`, because a state
  naming none asserts no authority, and skipped again when no repository root
  resolves. A malformed state value fails, and so does a supplied workflow that
  resolves outside the repository. Branch order and the reason behind each
  verdict live in
  [`references/workflow-file-protocol.md`](./references/workflow-file-protocol.md).
- **PR Marker Plan Evidence status**, which must equal
  `pr_marker_plan.status` exactly. Repairing the workflow file to match the
  state is the correct move here.

**The `Stage` entry is workflow-file-wins.** The `Stage` row in the workflow
file's `### Basic Information` table is the authoritative durable store of the
resolved stage; `autopilot-state.json.stage` mirrors it for the active run only
and is never authoritative. On disagreement the workflow file wins and the
mirror is repaired from it. That is the **opposite** direction from the two
exceptions above, which is why this rule is recorded as its own clause and MUST
NOT be added to that list. Absence on either side is legal — it means no run
yet, and resolves through Step 0.6c auto-detection. A two-sided disagreement is
reported by the Step 1.1 coverage guard as `stage_mirror_errors`, which is
registered in the `status-evidence` rule and so fails the guard rather than
merely printing.

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
- **Research/context capability unavailable:** use the next acceptable
  evidence path, record any confidence impact, and escalate only when no
  acceptable evidence path remains or a true gate fails.
- **Context window pressure:** keep subagent summaries concise; the
  workflow file is the durable record (re-read after compaction).

Full details, additional failure modes, and recovery playbooks live
in [`references/error-recovery.md`](./references/error-recovery.md).

## References

- [Prerequisites](./references/prerequisites.md) — Archive Sweep + Step 0.x environment, settings, constitution, agent detection, command/preset discovery
- [Phase Execution](./references/phase-execution.md) — Per-phase prompt construction, dispatch templates, branch-aware/Clarify/Multi-prompt prefixes
- [Consensus Protocol](./references/consensus-protocol.md) — Category-routed dispatch, Round 1/2, per-phase flows, Logging schema
- [Gate Validation](./references/gate-validation.md) — Programmatic gate checks (G0–G7), auto-fix loops, escalation
- [Post-Implementation](./references/post-implementation.md) — 12-task post-impl sequence (incl. self-review, UAT runbook), integration suite, PR creation, review loop
- [Task List Canonical](./references/task-list-canonical.md) — Task naming pattern + canonical post-implementation entries
- [Workflow File Protocol](./references/workflow-file-protocol.md) — Per-phase update table + `workflow_file` state authority (branch order, verdicts) + Consensus Resolution Log column schema
- [Error Recovery](./references/error-recovery.md) — Resume, common issues, context-window management
- [TDD Protocol](./references/tdd-protocol.md) — Red-green-refactor rules injected into implementation agent prompts
- [Plugin Limitations](./references/plugin-limitations.md) — permissionMode/hooks/mcpServers caveats and capability fallback behavior
- [Agent Teams Integration](./references/agent-teams-integration.md) — Use-site map (current + planned), capability detection, lifecycle policy
- [Token Discipline](./references/token-discipline.md) — Opt-in compressed vocabulary for inter-agent transcripts (off by default; never applied to PR bodies, logs, or artifacts)

## Runner Operations

Deterministic prerequisite checks, validation, reviewability, routing, payload,
and PR-preparation behavior is owned by `speckit_pro_runner`. Invoke
`resolved_python -m speckit_pro_runner` with one JSON request on stdin and use the
registered helper or gate operation IDs below.

- `check-prerequisites` — Verify CLI, project init, constitution, commands,
  branch detection, and workflow file readiness (JSON).
- `validate-gate` — Validate G1-G7 with marker counts and details (JSON).
- `confidence-gate` — Read the synthesizer's `📊 Confidence: X.XX`
  pre-Implement emit and decide whether Phase 7 may begin.
- `resolve-confidence-mode` — Resolve the pre-Implement confidence mode from
  invocation flags, local config, or the advisory default.
- `resolve-autopilot-stage` — Resolve which stage this invocation runs from
  `--stage` or, with none given, from the workflow file's own status table.
  Returns the stage, its source and basis, the recorded `Stage` row, and the
  confidence-gate verdict; exits 2 on a pre-flight rejection.
- `reviewability-gate` — Enforce the setup-mode reviewability budget. Tasks
  and pre-PR modes are deferred for installed workflows; record the deferral
  and use committed fallback evidence per the guidance above instead of
  invoking them.
- `atomicity-route` — Classify whether a feature should remain one PR or split.
- `plan-layers-feature-dir` — Emit a versioned layer-plan envelope for split
  routes before implementation.
- `estimate-reviewable-loc` — Project production reviewable LOC from declared
  file operations.
- `generate-pr-body` — `golden_only` body writer accepting exactly
  `output_path`, `title`, and `sections`; it writes one Markdown body and does
  not emit packet JSON, metadata, markers, validation evidence, or PR commands.
- `pr-packet-output` — `golden_only` packet emitter accepting structured
  packet fields; it writes the feature-local packet JSON, packet-owned body
  file, and declared validation-result path used before PR creation.
- `validate-pr-packet-read-only` — Validate an existing feature-local packet and
  return the result in `data.stdout_json` with `writes_state=false`; it does not
  persist validation state.
- `validate-pr-packet-write` — Rerun read-only packet validation in apply mode,
  then persist that current passing result to the packet's
  `validation_result_path`; do not use caller-supplied or stale validation
  results.
- `validate-pr-workflow-contract` — Validate PR title and changed-file scope.
- `detect-commands`, `detect-presets`, and `count-markers` — Provide
  deterministic command, preset, and marker evidence through runner-owned
  operation IDs.
- `generate-uat-skeleton` and `final-reviewability-backstop` — Registered but
  deferred for installed workflows; follow the deferred guidance above instead
  of invoking them.
- `relocate-process-artifacts` and `restack` — Registered but deferred with no
  active invocation contract. Do not invoke them or infer capability from
  generic runner plumbing.

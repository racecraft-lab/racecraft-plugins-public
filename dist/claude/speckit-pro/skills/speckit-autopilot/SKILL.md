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
window auto-compacts, which is not a stopping point: complete every
phase in the **resolved stage's** range (`AUTOPILOT_STAGE`, set at Step
0.6c). A `--stage plan` run finishes its work after the confidence gate.
A `full` run completes all 7 phases.

## Architectural Constraint — Main Agent Is The Orchestrator

This skill loads into the **main session agent** when the user invokes
`/speckit-pro:speckit-autopilot`. Current Claude Code can nest subagents, but
this workflow deliberately keeps one orchestration owner: the main session.
EVERY workflow dispatch decision — parallel subagents vs sequential vs Agent
Team, model routing, and lifecycle sequencing — happens HERE. Phase executors
are terminal workers; they don't dispatch workflow phases, branch on
`AGENT_TEAMS_AVAILABLE`, or create teams.

Runtime enforcement is two-tier (Layer 5 verifies both): the
hyper-focused single-purpose workers (the consensus analysts,
clarify-executor, uat-runbook-author) explicitly deny
`Agent`/`SendMessage` via `disallowedTools` so they stay
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

Skill `allowed-tools` pre-approves the listed core primitives; it is not
capability discovery. Runner calls still follow the session's permissions, so
an unattended run must prepare them before launch. See the plugin agent caveat
in Step 0 and
[`references/plugin-limitations.md`](./references/plugin-limitations.md).

## Prerequisites — Model

The orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Weak-model orchestration cascades into
expensive rework.

**Before executing any step**, verify:

1. **Model:** run on the operator's strongest available tier. If the
   session reports a small-tier model, stop and ask the operator to
   switch models and re-run.

**Reasoning effort is inherited, never checked.** Run at whatever the
operator has set for the session and do not stop, warn, or ask them to
change it. The bundled subagents carry their own pins: judgment roles
ship at `effort: max` (`xhigh` on Codex), and bounded rule-applying
roles that only apply rules to inputs already in their prompt ship at
the documented default. A pin sets that worker's effort regardless of
the session and never refuses to run.
The operator owns the session setting; the plugin does not veto it.

## Execution Rules

### 0. Forbidden skill invocations

<hard_constraints>

**Do not invoke `grill-me` from any autopilot phase or agent — ever.**

`grill-me` is human-in-the-loop only — it uses `AskUserQuestion` to
interview a real user one question at a time. Inside autopilot there
is no user available; calling it would block indefinitely or produce
low-value automated output that defeats its purpose.

Autopilot's Clarify phase uses `/speckit-clarify` with the multi-agent
consensus protocol. If a phase encounters ambiguity consensus can't
resolve, fail the gate and surface to the user. `grill-me` belongs to
pre-workflow human alignment via `/speckit-pro:speckit-scaffold-spec` or
`/speckit-pro:grill-me` only.

</hard_constraints>

### 1. Subagent per phase

For each phase, spawn a **foreground subagent** via the Agent
tool. The subagent runs the `/speckit-*` command and returns a
summary. You (the parent) receive the result as a tool call
response, which keeps your agent loop alive.

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

After EACH Clarify, Checklist, or Analyze executor returns, complete consensus
before the next prompt. The parent applies accepted Clarify edits; all three
executors surface remaining items with category tags. For every such item,
call `parse-consensus-categories`, dispatch exactly the routed analysts in
host-bounded batches, consume their actual results, synthesize, apply artifact
edits serially, and append the Consensus Resolution Log. Follow the mandatory
Round 2, stop, re-evaluation, and Phase 6 confidence-emit contracts in
[`references/consensus-protocol.md`](./references/consensus-protocol.md)
§Category-Routed Dispatch, §Batched Dispatch, §Phase-Specific Consensus Flows,
and §Logging.

## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID] [--stage plan|implement|full] [--strict | --advisory]
```

`--stage` selects which range of phases this invocation runs; omit it and
Step 0.6c resolves the stage from the workflow file's own status table.
Argument order is presentation only — every argument is read by name.

Before Step -1, use the read-only `resolve-workflow-binding` runner helper to
verify that Claude Code's live checkout already owns the workflow. Continue
only for `binding_status=resolved` with `relation=same`. If scaffold was run
from a parent checkout, follow the printed `/cd <absolute-worktree-root>` and
then retry the relative autopilot command. Never run Archive Sweep or mutate
the workflow's worktree from the parent checkout.

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
6. **Load settings + Claude subagent runtime record** — read
   `.claude/speckit-pro.local.md` (`consensus-mode`, `gate-failure`,
   `auto-commit`, `security-keywords`), observe the bounded Claude CLI/runtime
   inputs, and call runner helper `resolve-claude-subagent-runtime`. Persist its
   record and take `AGENT_TEAMS_AVAILABLE`, `SUBAGENT_WAVE_SIZE`, and resume
   behavior from it (see prerequisites.md §Step 0.6).
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
   - **Corroborate the recorded draft pull request — one read-only observation
     per run, taken only when the workflow file's `Draft PR` row is present.**
     Read the row first. When it is absent, take no observation at all and send
     no `pr_observation`. When it is present, take exactly one observation,
     scoped to the feature's head branch:

     ```text
     gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName
     ```

     `--state all` is load-bearing: returning pull requests in every state is
     what makes a closed one distinguishable from an absent one.
     That observation is Step 0.6c's own — one at this step per run, not a
     cap on every corroboration read a run may take. The create-or-refresh
     terminal step and the Phase 7 feedback sweep's description refresh each
     take their own later live read.
   - **The trigger is the row's presence, not the stage.** Any invocation
     carrying a `Draft PR` row takes this observation — including one whose
     stage came from an explicit `--stage` argument, and one that resolves a
     stage other than `plan`. A run with no emission terminal step still reports
     the status and still records a discrepancy durably.
   - **Pass the result to `resolve-autopilot-stage` as `inputs.pr_observation`,
     and let the helper classify it.** Set `ok` to the JSON literal `true` —
     never `1`, never `"true"` — only when the query exited zero *and* its output
     parsed, and carry the parsed array in `pull_requests`. Otherwise send
     `ok: false` with a short `reason`. **You take the observation; the helper
     never does.** It never runs the tool and never touches the network, which
     is what keeps classification deterministic and offline-testable. Anything
     short of `ok: true` with a parseable array yields `skipped`, because a tool
     that was absent, unauthenticated, rate-limited, or unparseable is not
     evidence that a recorded pull request is gone.
   - **Print one line beside the `Stage:` line this step already prints, on
     every run**, naming `corroboration.status` from the envelope. The object is
     always present, so all six statuses print — `match`, `no_record`,
     `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch` — and a run that
     could not check stays distinguishable from one that checked and agreed:

     ```text
     Stage: plan (argv) — explicit --stage plan
     Draft PR: match — #438 recorded, #438 observed
     ```

     ```text
     Draft PR: skipped — gh not authenticated
     Draft PR: pr_closed — #438 recorded, closed (merged: false)
     ```
   - **Record that same line durably in this step's workflow-file record for the
     three discrepancy statuses only** — `pr_closed`, `pr_missing`, and
     `identity_mismatch`. Write it in the **same edit turn as the `Stage` row**
     so it lands in the same commit, the write cadence `Stage` already follows.
     `match`, `no_record`, and `skipped` write nothing durable, and the scaffold
     workflow template ships no placeholder line.
   - **Corroboration reports; it never decides.** It never changes the resolved
     stage, never blocks stage resolution, and never stops the run. It is
     computed after the stage is decided and only ever appended to the envelope.
     Every consequence of a discrepancy belongs to the terminal step, in
     [Phase Execution](./references/phase-execution.md).
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

Read the workflow file and apply
[`references/phase-execution.md`](./references/phase-execution.md)
§Stage-Bounded Phase Selection. Filter Workflow Overview rows to
`AUTOPILOT_STAGE`, start at the first non-terminal row (`Complete` and
`Skipped` variants are terminal), and accept `--from-phase` only within that
stage. If no candidate row remains, execute the stage's terminal instruction
and STOP; do not scan into a later stage.

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

`--rule status-evidence` gates the **exit code** on the four workflow/state
status-evidence checks (`workflow_status_evidence_errors`,
`state_status_errors`, `stage_mirror_errors`, `workflow_authority_errors`) and
the three current-run state-plan invariants (`in_progress_errors`,
`duplicate_state_steps`, `state_order_errors`). The full report is still
printed; structural coverage checks and every advisory key are visible but
never block. Drop `--rule` to gate on every check.

`<resolved_python>` is the Python 3.11+ interpreter resolved by the
Installed Runtime Contract; `<plugin-root>` is the directory that owns
`skills/speckit-autopilot/`. Exit 0 is required to advance; exit 1 reports
the failing checks as JSON on stdout; exit 2 is an input error. The guard
also fails when a Workflow Overview status row contradicts a gate verdict
recorded elsewhere in the same file, which is what keeps the status table
honest across compactions and manual phase runs.

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
    6. Validate the gate (G1-G7): run runner helper
       `helper_id=validate-gate operation=validate-gate mode=read_only`
       with `gate=G<N>` and `feature_dir=<feature-dir>`, then branch on
       the JSON `pass` field
       On FAIL: auto-fix max 2 attempts; then honor gate-failure setting
    7. Update workflow file; auto-commit if configured
         phases 1-6: git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit
         phase 7:    git add -A && git commit
    7b. After Plan (G3 pass, plan.md exists), run the plan-phase
        reviewability budget with runner helper `estimate-reviewable-loc`,
        guarded against errexit. Branch on JSON `status`
        (pass / over_budget / not_estimated) or the exit code.
        ADVISORY — never blocks, prompts mid-autonomous-run, or
        crashes the run.
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
        This wires NO PR emission or branch creation; the multi-PR emission
        phase owns those effects.
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

Before each corresponding dispatch, read the mandatory
[`references/phase-execution.md`](./references/phase-execution.md) sections
§Subagent Delegation, §Phase-by-Phase Execution, and §Phase 7 Step 3. They own
the exact workflow-prompt envelope, preset/project-command feed-down,
branch-aware prefixes, Clarify and Checklist sequencing, namespaced agent
routing, `[P]` waves, TDD injection, and regression fallback. Rule 6 and the
consensus reference own resolution between prompts. Do not reconstruct those
contracts from this entrypoint.

## Step 3: Post-Implementation

After Phase 7 passes G7, read and execute
[`references/post-implementation.md`](./references/post-implementation.md)
in canonical order. It owns the parallel group, integration suite, mandatory
self-review and UAT runbook, current reviewability evidence and continuation,
packet dry-run/apply and validation, single- versus split-PR emission, review
remediation, retrospective, and final summary. Do not start PR side effects
without the reference's current evidence and packet contracts, and never report
completion while its continuation or canonical Post work remains incomplete.

## Workflow File Update Protocol

After every phase, apply
[`references/workflow-file-protocol.md`](./references/workflow-file-protocol.md)
to update the durable workflow status/results, constitution evidence, and any
Consensus Resolution Log rows. Workflow Overview and `Stage` are
workflow-file-wins and repair their one-run state mirrors. Only active
`workflow_file` and `pr_marker_plan.status` are state-authoritative and repair
the workflow in the opposite direction. The coverage guard enforces these
directions; do not infer a broader precedence rule.

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

Active runner operations are named at their use sites and in the targeted
references above; the runner registry is their deterministic authority. Treat
deferred operations as unavailable unless a use site explicitly authorizes
them.

---
name: speckit-autopilot
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow
  file and runs all 7 SDD phases (specify → clarify → plan →
  checklist → tasks → analyze → implement) with programmatic gate
  validation, multi-agent consensus resolution, and auto-commits.
  Use when the user says "run autopilot", "execute workflow",
  "autonomous speckit", "autonomous execution", "kick off autopilot",
  "start the autonomous pipeline", "drive it through all the SDD
  phases", "run the whole thing autonomously", "full end-to-end
  speckit run", or hands over a populated SPEC-NNN-workflow.md file
  for end-to-end execution. Requires SpecKit CLI installed,
  constitution created, and a populated workflow file. Not for SDD
  methodology questions ($speckit-coach), pre-spec scoping
  ($grill-me), new-spec setup ($speckit-scaffold-spec), status
  checks ($speckit-status), or PR comment resolution
  ($speckit-resolve-pr).
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
questions, SDD philosophy, or learning how SpecKit works, redirect
the user to `$speckit-coach` — the coaching skill is the right
resource for methodology guidance.

You are an **orchestrator** for SpecKit workflows. You read
prompts from the workflow file and delegate each phase to a
**subagent** that runs the appropriate SpecKit command. You never
run the commands yourself — you spawn, collect results, validate
gates, and advance through every phase in the resolved
`AUTOPILOT_STAGE`. A `--stage plan` run stops at its stage boundary;
`full` covers all seven phases.

## Architectural Constraint — Main Agent Is The Orchestrator

This skill loads into the **main Codex session agent**, which owns all phase
and lifecycle dispatch. Phase workers are terminal workers and must not
orchestrate later phases. **If this skill is loaded inside a subagent context,
refuse and surface the violation.** Discover the current host's actual
collaboration capabilities below; do not infer architecture from a universal
nesting limit.

## Codex Runtime Contract

This Codex variant is a concrete tool contract, not advisory prose.
Bind the workflow to actual Codex primitives:

- `update_plan` is REQUIRED before Phase 1 and after every phase transition.
  If the call fails or is skipped, STOP.
- Discover the callable collaboration actions before dispatch and select the
  semantic equivalents that the current Codex surface actually exposes.
  `spawn_agent` plus `wait_agent` and delivery of the agent's result are the
  REQUIRED common contract. Hosted Responses Multi-agent provides
  `spawn_agent`, `send_message`, `followup_task`, `wait_agent`,
  `interrupt_agent`, and `list_agents`; it does not expose `close_agent`.
  Other Codex surfaces can expose equivalents such as `send_input`,
  `resume_agent`, or `close_agent`. On hosted Responses, `send_message` queues
  context and `followup_task` assigns work and starts the next turn. On a
  surface with `send_input`, use it to deliver follow-up work to an open agent;
  if that agent was explicitly closed, call `resume_agent` first and then
  `send_input`. Inspection, interruption, and explicit closure are optional
  actions used only when present. Hard-stop only if spawning or receiving the
  required result is unavailable — absence of `close_agent` is NOT a
  prerequisite failure. See the official [Responses Multi-agent action
  contract](https://developers.openai.com/api/docs/guides/responses-multi-agent#how-multi-agent-works)
  and [Codex subagent orchestration
  guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents#orchestration-and-thread-controls),
  plus the local [configuration
  reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml).
- The REQUIRED lifecycle on every surface is `spawn_agent` → bounded
  `wait_agent` loop → consume the dispatched agent's actual final result. A
  hosted `wait_agent` call can wake for an ordinary message, unrelated mailbox
  update, timeout, or steering event, so associate updates with the dispatched
  sender/task and keep waiting until its `FINAL_ANSWER` or equivalent summary
  is consumed. A terminal status is corroboration or recovery evidence only;
  it never replaces the required result. If an agent is terminal without a
  delivered result, drain the mailbox and then re-spawn or fail that item.
- When `close_agent` is exposed, call it promptly after consuming the result.
  Cleanup policy is best-effort: if the surface reports the agent already gone,
  log it and continue without retry-looping. When `close_agent` is absent,
  consume the result and leave the inspectable thread to the host; optionally
  reuse it with the available follow-up action.
- On resume, never assume an older agent still exists. If `list_agents` is
  available, match returned current-tree entries to the workflow target and
  current incomplete plan item's canonical task name/prompt; manage or reuse
  only agents confirmed present and owned by this autopilot run. Without
  inspection, treat prior-session agent references as stale and spawn fresh.
  Apply explicit closure only to run-owned agents confirmed present, including
  a reconciled agent that was spawned before the interruption.
- Derive `subagent_slots` from the current session without mixing surface
  conventions: use explicit `max_concurrent_subagents` when provided; when the
  host advertises total active agents including `/root`, subtract one; when a
  local surface advertises an open-thread cap, follow that surface's stated
  semantics. If no count is exposed, set `subagent_slots = 1` as the safe
  fallback. For wider fan-out, dispatch in waves of at most `subagent_slots`,
  consume each required result, perform optional closure when exposed, then
  start the next queued item. Never hard-code one surface's default as
  another surface's cap.
- A `wait_agent` timeout is one bounded mailbox poll, not proof that an agent is
  stuck. Continue bounded waits and inspect status/progress when possible. Use
  `interrupt_agent` only after a separate execution deadline or confirmed
  no-progress condition, and only to cancel a still-running turn; it preserves
  context and is not closure. Any interrupted required item must be re-spawned
  and return a real result before its plan item can complete.
- Before reporting the run complete, use `list_agents` when exposed; otherwise
  audit the tracked dispatch IDs and consumed results. Every required dispatch
  must have a consumed result. Close remaining current-run threads best-effort
  only when `close_agent` is exposed. Hosted completed threads are host-managed
  and do not block completion.
- `autopilot-fast-helper` is OPTIONAL. Only the main autopilot may invoke it,
  and only for tiny text-only compression, triage, or query-drafting work.
  Never route edits, gate decisions, or consensus votes through it.
- Use the current surface's exposed read, search, command, and edit equivalents
  for workflow parsing, validation, and artifact mutation.
- Persist orchestration state to `autopilot-state.json` in the same directory
  as the workflow file. Resume reads that file first, then reconciles with the
  workflow file.
- This skill owns `./agents/openai.yaml` as Codex skill metadata for UI
  appearance and invocation policy. Optional research/context capabilities are
  discovered at runtime, so the sidecar MUST NOT declare Tavily, Context7, or
  any other optional capability as a required tool dependency. Do not treat
  that sidecar as a custom-agent manifest.
- SpecKit Pro also ships bundled custom-agent templates under
  `../../codex-agents/`. Those bundled TOML files are package assets, not
  runtime registrations.
- Custom executor and consensus agents must be installed as real Codex
  subagents under `.codex/agents/` (project scope) or `~/.codex/agents/`
  (user scope). The bundled `install` skill copies the plugin templates into
  those official Codex runtime paths.

Do not translate this skill into Claude-only primitives such as legacy
task-list tools or legacy Claude agent/shell placeholders. Do not read the
bundled TOML templates and inline them as ad hoc prompts. Validate that the
required custom subagents are installed, then spawn them by agent name. If any
required SpecKit Pro subagent is missing, STOP and instruct the user to run
`$install` from the SpecKit Pro plugin, then restart Codex.

## Prerequisites — Model

The autopilot orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Running on a weak model produces poor orchestration
decisions that cascade into expensive rework.

**Before executing any step**, verify:

1. **Model check:** You MUST be running on the highest-capability Codex model
   tier available. Prefer `gpt-5.6-sol` when it is available
   in the Codex model picker. `gpt-5.5` or `gpt-5.4` is an acceptable fallback
   during rollout or when the environment uses API-key authentication. If the
   session is explicitly on a mini, fast, Luna, or otherwise reduced-capability
   tier, STOP and instruct the user to relaunch the autopilot on a stronger
   model. `$install` owns bundled-agent installation and fallback configuration.

**Reasoning effort is inherited, never checked.** Run at whatever
`model_reasoning_effort` the session already has and do not stop, warn,
or ask the operator to relaunch. Bundled subagents keep their declared effort;
the optional `autopilot-fast-helper` is pinned to low effort on gpt-5.6-luna
for latency-sensitive prep. Those pins only constrain worker effort and never
refuse to run. The operator owns the session setting; the plugin does not veto
it.

The model check above is non-negotiable.

## Critical: Execution Rules

These rules are non-negotiable. Follow them exactly.

### 0. Forbidden skill invocations

**Never invoke `$grill-me` from any phase, subagent, or consensus step.**
Grill-me is a strictly human-in-the-loop, pre-workflow scoping interview. Its
runtime guard probes for `request_user_input` then a TTY before asking any
question; if invoked from autopilot's autonomous loop it will refuse and write
nothing — but the autopilot must not even attempt the call.

If a phase encounters ambiguity that feels like it needs grill-me, the correct
response is one of:

- Run the `$speckit-clarify` skill (Phase 2) with the multi-agent consensus
  protocol — that is autopilot's only clarification mechanism.
- Fail the gate, surface the ambiguity, and stop. Pre-workflow interviews
  belong in `$speckit-scaffold-spec`, not autopilot.

This rule applies to: the orchestrator, every phase subagent
(`phase-executor`, `clarify-executor`, `checklist-executor`,
`analyze-executor`, `implement-executor`), every consensus analyst
(`codebase-analyst`, `spec-context-analyst`, `domain-researcher`), and
`consensus-synthesizer`.

### 1. Canonical plan and stage-bounded execution

The canonical execution order is:

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]
```

Before phase work starts, the parent session MUST create a durable progress
plan that accounts for every phase in that list plus prerequisites and
post-implementation verification. Execution starts and stops within the stage
resolved at Step 0.6c; phases outside that stage stay visible but are not
started.

`--from-phase` changes the starting index only within the resolved stage. It
does not remove plan entries from `update_plan` or `autopilot-state.json`.

### 2. Subagent per phase

For each phase, spawn a **foreground subagent** with `spawn_agent`,
wait for it with `wait_agent`, and keep orchestration in the parent.
The subagent runs the SpecKit command and returns a summary.

**Why:** If you invoke a skill directly in your own context, the command's
completion behavior causes your loop to output plain text and terminate.
With subagents, the command runs in an isolated context and its completion
is harmless — the result returns to you and your loop continues.

**Third-party skills:** when capability discovery selects an installed skill you
$-invoke, its completion text can likewise end the loop. Capture the skill's
result as durable state/evidence and continue; never treat a third-party skill's
completion text as your own terminal output.

### 3. Use phase-specific executor agents

Each phase type has its own specialized executor agent:

| Phase | Agent | Why specialized |
| ----- | ----- | --------------- |
| Specify, Plan, Tasks | `phase-executor` | Heavy reasoning (Specify, Plan); mechanical for Tasks. Single skill invocation, single summary. |
| Clarify | `clarify-executor` | Read-only question set; parent answers and edits |
| Checklist | `checklist-executor` | Must run checklist AND remediate gaps with research |
| Analyze | `analyze-executor` | Must run analysis AND remediate ALL findings with research |
| Implement | `implement-executor` | Task-level dispatch with strict TDD. **Honor `[P]` markers within derived `subagent_slots`** — dispatch consecutive `[P]`-tagged tasks of the same agent type in cap-bounded waves. As each actual result arrives through the bounded `wait_agent` loop, record it, call `close_agent` only when exposed, and start the next `[P]` task. Do NOT spawn every `[P]` task in ONE turn when the run is wider than the cap. Non-`[P]` tasks dispatch one at a time. After each wave, run TYPECHECK + UNIT_TEST in the lead; on regression, fall back to serial re-run. |
| Read-only consensus | analyst agents | Read-heavy code/spec/domain analysis |

Concrete Codex mapping:

- `./agents/openai.yaml` is skill metadata only. It does not register custom
  agents for Codex.
- Resolve the installed agent from `.codex/agents/<agent>.toml` first, then
  `~/.codex/agents/<agent>.toml`
- If the installed agent is missing, STOP and tell the user to run `$install`,
  then restart Codex
- Build the phase prompt in the parent session
- Call `spawn_agent` using the installed custom agent by its `name`
  plus the workflow prompt
- Call `wait_agent` for completion
- Persist the returned summary into the workflow file and `autopilot-state.json`

Spawn each agent with phase-specific prefix where needed, followed by:

```text
Workflow prompt:
---
<paste the exact prompt from the workflow file>
---
```

Each agent runs the command (and any post-execution work like gap
remediation) in isolation and returns a structured summary.

### 4. Multi-prompt phases

Clarify and Checklist have multiple prompts in the workflow file.
Spawn a **separate subagent for each prompt**, consume its result, and complete
Rule 6 resolution before starting the next prompt. Follow the per-phase flow in
[`references/phase-execution-codex.md`](./references/phase-execution-codex.md).

### 5. Clarify — executor returns questions to parent

The `clarify-executor` is read-only. It does not invoke
`$speckit-clarify`, does not wait on a user, and does not edit
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
call `parse-consensus-categories`, dispatch exactly the returned analysts in
host-bounded waves, consume their actual results, synthesize, apply artifact
edits serially, and append the Consensus Resolution Log. Follow the mandatory
Round 2, stop, re-evaluation, and Phase 6 confidence-emit contracts in
[`consensus-protocol.md`](../../skills/speckit-autopilot/references/consensus-protocol.md)
§Category-Routed Dispatch, §Batched Dispatch, §Phase-Specific Consensus Flows,
and §Logging.

### 7. Optional Luna helper is advisory only

The main autopilot may optionally spawn `autopilot-fast-helper`
for one of these narrow tasks:

- compress a long executor result into a compact brief
- triage an unresolved item into `codebase`, `spec-context`,
  `domain-research`, or `mixed`
- draft short search queries for a stronger agent to execute

Guardrails:

- Only the parent orchestrator may call this helper
- Executor or consensus subagents must never spawn it
- Use it only for text-only prep work before a real decision
- Never use it to edit artifacts, vote in consensus, or decide gates
- If the helper spawn fails because `gpt-5.6-luna` is unavailable,
  log the failure briefly and continue without it

This helper is a latency optimization, not a dependency.

You run in the **main session** and keep all phase and lifecycle dispatch there.

## Input

You receive a workflow file path and optional arguments:

```text
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID] [--strict | --advisory] [--stage plan|implement|full]
```

`--stage` selects which range of phases this invocation runs, and Step 0.6c
resolves it when omitted. Argument order is presentation only — every
argument is read by name. Stage-bounded execution is specified in
[phase-execution-codex.md](./references/phase-execution-codex.md#stage-bounded-execution).

Before Step -1, use the `resolve-workflow-binding` runner helper exactly as
specified in `prerequisites-codex.md`. That reference owns the executable-root
invariant and fail-closed recovery.

`--strict` and `--advisory` override the pre-Implement confidence
gate (G6.5) mode for this invocation. They beat
`confidence_gate_mode` in `.claude/speckit-pro.local.md` (or
`.codex/speckit-pro.local.md`). Passing both is a usage error;
STOP before Phase 0 with the conflict message from
the runner helper operation `resolve-confidence-mode`. See [Gate Validation §G6.5](../../skills/speckit-autopilot/references/gate-validation.md#g65--pre-implement-confidence-gate-between-analyze-and-implement)
and the precedence rule documented there.

## Step -1 + Step 0: Pre-flight (Archive Sweep + Prerequisites)

See [prerequisites-codex.md](./references/prerequisites-codex.md) for the full pre-flight sequence:

- **Step -1: Archive Sweep Startup** — execute the installed archive
  extension's project-local command contract directly in Codex, use the
  Codex-native worktree binding for path prerequisites, and fail closed on a
  broken installed extension
- **Step 0.0: Use Runner Operations** — invoke `speckit_pro_runner` helper IDs with one JSON request on stdin
- **Step 0.1–0.7: Environment Checks** — `check-prerequisites` JSON parsing, branch detection
- **Step 0.6: Load Settings** — `consensus-mode`, `gate-failure`, `auto-commit`, `security-keywords`
- **Step 0.6b: Resolve Pre-Implement Confidence Gate Mode** — run helper
  operation `resolve-confidence-mode` to resolve
  `CONFIDENCE_GATE_MODE` for G6.5. Precedence: `--strict`/`--advisory`
  flag > `confidence_gate_mode` in `.claude/speckit-pro.local.md`
  (or `.codex/speckit-pro.local.md` — the script checks both
  default paths, with `.claude/` winning when both exist) > default
  `advisory`. If the script exits 2 (both flags passed), STOP
  before Phase 0 with the conflict message. **Do not re-run the
  script at G6.5; the gate reads `CONFIDENCE_GATE_MODE` directly.**
- **Step 0.6c: Resolve The Stage** — run helper operation
  `resolve-autopilot-stage` with the invocation argv and the workflow
  file path. Record `stage` as `AUTOPILOT_STAGE` and keep `source`,
  `basis`, `recorded_stage`, `planning_complete`, and
  `confidence_gate_status` for the phase loop. An explicit `--stage`
  always wins; with none given the stage is resolved from the workflow
  file's `## Workflow Overview` table. If the operation exits 2, STOP
  before Phase 0 with that one-line message — the same fail-fast shape
  0.6b uses. **Print the resolved stage and its basis before any phase
  work begins.**
  - **Corroborate the `Draft PR` row.** Read the row first; when absent, send no
    `pr_observation`. When present, take exactly **one** read-only observation,
    scoped to the head branch. `--state all` separates a closed pull request from
    an absent one. The trigger is the row's presence, not the stage.

    ```text
    gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName
    ```

  - **Send it as `inputs.pr_observation`; the helper classifies.** Set `ok` to
    the JSON literal `true` — never `1`, never `"true"` — only when the query
    exited zero *and* parsed, carrying the array in `pull_requests`; otherwise
    `ok: false` with a `reason`. **You observe; the helper never runs the tool or
    touches the network.** Anything less yields `skipped`: an unreachable query
    is not evidence a pull request is gone.
  - **Print `corroboration.status` beside the `Stage:` line every run**; all six
    print:

    ```text
    Draft PR: pr_closed — #438 recorded, closed (merged: false)
    ```

  - **Record that line durably only for `pr_closed`, `pr_missing`, and
    `identity_mismatch`**, in the **same edit turn as the `Stage` row** so one
    commit carries both.
  - **It reports; it never decides** — never changes the stage, blocks
    resolution, or stops the run. Consequences belong to the terminal step, in
    [phase-execution-codex.md](./references/phase-execution-codex.md).
- **Step 0.8: Capability Coverage Check** — informational research/context advisory (agents have fallbacks)
- **Step 0.8b: Capability Enumeration, Grounding & Feed-down** — you are the only component that discovers openly. Enumerate the tools and installed skills this session actually exposes and select best-fit per the capability-discovery directive (speckit-pro/skills/speckit-autopilot/references/capability-discovery.md); assume no fixed set — the user may have installed anything. Most subagents inherit that surface and follow the directive; read-only roles select read/research only, and the two untrusted-input consumers pin closed allowlists. Still pass the discovered evidence a subagent needs directly in each prompt: shared context beats re-discovery. Ground your OWN output (gate decisions, consensus synthesis, PR bodies) per the grounding contract (speckit-pro/skills/speckit-autopilot/references/grounding.md): cite a real tool/skill/file result for every external fact, and abstain when none grounds it.
- **Step 0.9: Constitution Validation** — principle checks against current codebase
- **Step 0.10: Codex Agent Availability Check** — Run the promoted
  `install-codex-agents` helper in `dry_run` mode against the selected project or
  user destination and its installed model choice. If any required file is
  missing or stale, STOP and instruct the user to run `$install`, approve the
  expected local write, and restart Codex. Do not apply the repair inside
  autopilot: the current process cannot reload changed custom agents safely.
- **Step 0.10b: Implementation Agent Detection** — discover `PROJECT_IMPLEMENTATION_AGENT` from `.codex/agents/`
- **Step 0.11: Project Command Discovery** — runner helper `detect-commands` → `PROJECT_COMMANDS`
- **Step 0.12: Preset and Extension Detection** — runner helper `detect-presets` → `PRESET_CONVENTIONS`

If any check fails, STOP with the error message from the script's JSON output.
Pass `WORKFLOW_ROOT`, `PROJECT_COMMANDS`, and `PRESET_CONVENTIONS` to every
subagent prompt.

## Step 1: Parse Workflow State

Read the workflow file and apply
[`phase-execution-codex.md`](./references/phase-execution-codex.md)
§Stage-Bounded Execution. Filter Workflow Overview rows to
`AUTOPILOT_STAGE`, start at the first non-terminal row (`Complete` and
`Skipped` variants are terminal), and accept `--from-phase` only within that
stage. If no candidate remains, run the stage's terminal step and STOP; for
`implement` and `full`, rebuild and finish incomplete canonical Post work
before reporting completion.

### 1.1 Create Durable Progress Plan

After parsing the workflow state, create a **granular** progress plan
and immediately materialize it in TWO places:

1. `update_plan` with the full checklist
2. `<workflow directory>/autopilot-state.json` with the same items

Do both before Phase 1 or STOP. The initial plan must include every
canonical phase family even when its detailed items will be discovered
later. For multi-prompt phases (Clarify, Checklist), create one item
per prompt/session when known; otherwise create the phase discovery
placeholder.

**Item naming + combined post-impl list (14 mandatory rows including
`Post: Doctor Extension Check` ... `Post: Retrospective` as the FINAL
STEP) + reference `autopilot-state.json` schema:** see
[task-list-canonical-codex.md](./references/task-list-canonical-codex.md).
Mark missing extensions as `skipped: <ext-name> not installed`; never
silently drop the item.

**CRITICAL — phase family coverage is mandatory:**

Before any subagent is spawned, verify that the plan includes at least
one item whose name starts with each of these exact prefixes:
`Archive Sweep:`, `Phase 0:`, `Phase 1:`, `Phase 2:`, `Phase 3:`,
`Phase 4:`, `Phase 5:`, `Phase 6:`, `Phase 6.5:`, `Phase 7:`,
`Post:`.

If any prefix is missing from `update_plan` or `autopilot-state.json`,
STOP, repair both stores, print the corrected checklist summary, and
repeat this coverage audit. A complete workflow plan is required even
when `--from-phase` starts execution in the middle of the workflow.

After writing or repairing `autopilot-state.json`, run the deterministic
coverage guard and STOP on nonzero exit:

```text
resolved_python "<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE" --state "$WORKFLOW_DIR/autopilot-state.json" --rule status-evidence
```

`resolved_python` is the Python 3.11+ interpreter resolved by the installed
runtime contract, not a hardcoded interpreter name; `<plugin-root>` is the
directory that owns `skills/speckit-autopilot/`. `--rule status-evidence`
gates the exit code on the four workflow/state status-evidence checks
(`workflow_status_evidence_errors`, `state_status_errors`,
`stage_mirror_errors`, `workflow_authority_errors`) and the three current-run
state-plan invariants (`in_progress_errors`, `duplicate_state_steps`,
`state_order_errors`), the same scoping the Claude variant uses. The full
report still prints; structural coverage checks and every advisory key are
visible but never block. Drop `--rule` to gate on every check.

When `pr-marker-plan.v2` declares a changed-file manifest, append
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`.
Fetch both OIDs from live PR metadata immediately before every validation;
never source either authority from the workflow, state, or manifest itself.
Missing, stale, or mismatched external PR authority is blocking.

**CRITICAL — Consensus items are MANDATORY:**

Every Clarify session, every Checklist domain, and the Analyze
phase MUST have a corresponding Consensus item immediately after
it. The consensus item runs the two-layer resolution process
(Rule 6) — skipped only if the executor reports zero unresolved
items. **Never omit consensus items.**

### 1.2 Validate Plan State Before Phase 1

Before Phase 1 starts, validate all of the following or STOP:

- `update_plan` succeeded and the active plan matches the workflow-derived checklist
- `autopilot-state.json` exists and contains the same ordered step list
- Exactly one plan item is `in_progress`
- Every canonical phase family prefix from Phase 0 through Phase 7 plus
  Phase 6.5 and Post appears in both `update_plan` and
  `autopilot-state.json`, with the Archive Sweep item recorded before Phase 0
- `validate-autopilot-phase-coverage.py` exits 0 for the workflow/state pair
- Every Clarify session, Checklist domain, and Analyze phase has its
  mandatory Consensus item
- The checklist summary was printed so progress is visible to the user

## Step 2: Main Execution Loop

For each pending phase the parent orchestrator does six things in
order: pre-phase hooks → spawn executor → consensus resolution →
post-phase hooks → gate validation → auto-commit + advance. Full
11-step pseudocode (including the `PHASES = [...]` canonical order
and `--from-phase` semantics) lives in
[phase-execution-codex.md §Main Execution Loop](./references/phase-execution-codex.md#main-execution-loop).

**Plan-phase reviewability budget (advisory):** After the Plan phase
(G3 pass, `plan.md` exists), the parent runs
runner helper `estimate-reviewable-loc` via `exec_command`, capturing
the exit code so a non-zero exit can never abort the run. Branch on the
JSON `status` (`pass` / `over_budget` / `not_estimated`) or the exit
code, recording the outcome to the workflow file and
`autopilot-state.json`. This is preventive sizing and **advisory only**
— no outcome blocks, prompts mid-autonomous-run, or crashes the run
(hard blocking and re-slicing are a separate step). Full status branch in
[phase-execution-codex.md §Phase 3: Plan — Reviewability Budget](./references/phase-execution-codex.md#phase-3-plan--reviewability-budget-advisory).

After G5, reconcile the Phase 7 placeholder against `tasks.md` in both state
stores, then apply the tasks-phase reviewability fallback without invoking the
deferred tasks mode of `reviewability-gate`. Persist any required marker-plan
state, record the read-only `atomicity-route`, and run
`plan-layers-feature-dir` if and only if the route is `split-PR`. Persist the
route and the full versioned layer-plan envelope to the workflow and
`autopilot-state.json`; for a non-split route record the layer plan as skipped.
Exit 1 is `invalid_plan`: STOP before implementation and print
`STOP: Layer planner returned invalid_plan (exit 1) for <feature-dir>; implementation has not started. Fix tasks.md using the planner diagnostics below, then rerun autopilot from the Layer Plan step.`
before the diagnostics. Exit 2 is `input_error`: STOP separately and show its
diagnostics. Analyze or Implement must not begin before this sequence completes.
Before performing it, read
[`phase-execution-codex.md`](./references/phase-execution-codex.md)
§Phase 7: Implement for the authoritative placeholder, reviewability, marker
state, and no-side-effect boundaries.

The marker planning step must preserve correctness stops for malformed or stale state,
failed verification, invalid packets, unsafe output, unusable gate evidence,
and non-size safety findings.

**Dynamic updates:** If consensus reveals new questions or
remediation adds loops, add additional items to your checklist.

### Phase Dispatch

Before each corresponding dispatch, read the mandatory
[`phase-execution-codex.md`](./references/phase-execution-codex.md) sections
§Agent Mapping, §Main Execution Loop, and §Phase 7: Implement. Pass the exact
workflow prompt plus `WORKFLOW_ROOT`, `PRESET_CONVENTIONS`, and
`PROJECT_COMMANDS` already resolved above. When already on the feature branch,
tell Specify to use that branch and existing spec directory rather than create
another. The reference owns agent routing, per-prompt result handling, `[P]`
waves, TDD injection, and regression fallback; do not reconstruct those
algorithms from this entrypoint.

## Step 3: Post-Implementation

After Phase 7 passes G7, read and execute
[`post-implementation-codex.md`](./references/post-implementation-codex.md)
in canonical order. It owns the parallel group, full integration suite,
mandatory self-review and UAT runbook, current reviewability evidence and
continuation, packet dry-run/apply and current read-only/persisted validation,
packet-owned base/head/title/body, single- versus split-PR emission, review
remediation, retrospective, and final summary. Do not start PR side effects
with invalid or stale evidence, and never report completion while continuation
or canonical Post work remains incomplete.

### 3.4 Pre-final completion audit

Before sending any final user-facing response, re-read
`autopilot-state.json` and the workflow file, reconcile them with
`update_plan`, and audit the canonical Post list. You MUST NOT send a
final response if any `Post:` item is `pending`, `in_progress`, or missing.
If the audit finds incomplete Post work, set the first
incomplete item to `in_progress` in both state stores and continue the
autopilot loop instead of summarizing. `Post: Retrospective` is the final
Post item; it must be completed or explicitly skipped before the
autopilot can report completion.

Only after every Post item is completed or explicitly skipped, and the
PR URL is known, the autopilot is DONE. Report the final summary with
PR URL.

## Workflow File Update Protocol + Error Recovery

- **Per-phase workflow-file section updates** (Specify Results table,
  Clarify Results, Plan Results, Checklist Results + Addressing Gaps,
  Tasks Results, Analysis Results, Implementation Progress + Post-Impl
  Checklist + Success Criteria) — see
  [workflow-file-protocol-codex.md](./references/workflow-file-protocol-codex.md).
  Also: Constitution Validation table after Specify (initial) + Implement
  (final), and Consensus Resolution Log entries when consensus was used.
- **Resume protocol** (`autopilot-state.json` reconciliation, missing-state
  reconstruction, `--from-phase` semantics), **common issues** (subagent
  retry, gate failure, consensus all-disagree, MCP unavailable), and
  **context window management** — see
  [error-recovery-codex.md](./references/error-recovery-codex.md).

## References

**Codex-specific (lifted from this SKILL.md body):**
- [Prerequisites for Codex](./references/prerequisites-codex.md) — Step -1
  Archive Sweep + Step 0.0-0.12 (scripts path, env checks, settings,
  MCP, constitution, Codex agent availability, implementation agent
  detection, command discovery, preset detection)
- [Canonical Task List for Codex](./references/task-list-canonical-codex.md) —
  Step 1.1 checklist naming pattern, 14 mandatory Post rows, item-naming
  rules, reference `autopilot-state.json` schema
- [Phase Execution for Codex](./references/phase-execution-codex.md) —
  PHASES order, agent mapping, main execution loop (11-step per-phase
  pseudocode), Phase 7 implement detail, PR body generation, coverage audit
- [Post-Implementation for Codex](./references/post-implementation-codex.md) —
  Items 10-19 table plus supporting-row mapping, parallel group dispatch (Doctor/Code Review/Verify-chain),
  extension availability rules
- [Workflow File Update Protocol for Codex](./references/workflow-file-protocol-codex.md) —
  Per-phase section updates + Constitution + Consensus Log +
  `workflow_file` state authority
- [Error Recovery for Codex](./references/error-recovery-codex.md) — Resume
  protocol, common issues, context window management

**Shared CC references (still applicable to Codex):**
- [Consensus Protocol](../../skills/speckit-autopilot/references/consensus-protocol.md) —
  Multi-agent resolution rules and flows
- [Gate Validation](../../skills/speckit-autopilot/references/gate-validation.md) —
  Programmatic gate checks and remediation loops
- [TDD Protocol](../../skills/speckit-autopilot/references/tdd-protocol.md) —
  Red-green-refactor rules injected into implementation agent prompts
- [Plugin Limitations](../../skills/speckit-autopilot/references/plugin-limitations.md) —
  permissionMode, hooks, mcpServers restrictions for plugin agents;
  research/context capability coverage and fallback behavior
- [Token Discipline](../../skills/speckit-autopilot/references/token-discipline.md) —
  Opt-in compressed vocabulary for inter-agent transcripts
  (off by default; never applied to PR bodies, logs, or artifacts)

Active runner operations are named at their use sites and in the targeted
references above; the runner registry is their deterministic authority.
Registry-deferred or out-of-scope operations are unavailable and MUST NOT be
invoked, promoted, or inferred from use-site prose.

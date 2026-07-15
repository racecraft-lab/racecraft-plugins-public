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
path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]
```

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

If all seven SDD phases are `✅ Complete`, inspect every canonical `Post:` row
in the workflow and `autopilot-state.json`. Rebuild the durable Post plan and
continue from the first missing, pending, or in-progress item. Report "All
phases complete" and stop only after every required Post item is complete,
every optional skip is authorized by its named procedure, and an exact
head/base lookup verifies the recorded open PR.

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
   error writes state and stops without a packet. After a single-route proceed
   result, invoke the `golden_only` `pr-packet-output` helper in `apply` mode
   with grounded feature, title, UAT, verification, scope, gap, and source-marker
   inputs. It derives the current branch, immutable base/source HEAD SHAs,
   source-diff fingerprint, changed-file scope, body path, packet path,
   versioned protected fingerprint, and validation-result path, then atomically
   writes the body before the authorizing single-packet JSON at
   `specs/<feature>/.process/pr-packets/<packet-id>.json`. Callers must not pass
   raw output paths, content, operations, or split metadata. The helper supports
   single packets only; split packet output and `validate-pr-packet-write` remain
   deferred. It accepts `base_ref` only as `<base_branch>` or
   `origin/<base_branch>` and rejects object IDs. Both `dry_run` and `apply`
   require a clean committed worktree because scope is derived from
   `base...HEAD`. On resume, if either body or packet already exists, never
   authorize reuse or overwrite.
   Inspect and remove both artifacts; if either is tracked, commit its deletion,
   restore a clean committed worktree, and regenerate. Apply mode fails closed
   with `secure_atomic_writes_unavailable` when descriptor-relative no-follow
   writes and atomic no-clobber installation are unavailable. Do not substitute
   path-based writes; resume at the same clean source revision in a supported
   POSIX environment. `generate-pr-body`
   remains a separate one-Markdown-body helper and
   does not create packet JSON or metadata. Refine only declared editable
   prose, then stage only the generated body and packet and commit them as the
   single direct child of the recorded source revision. Run
   `validate-pr-packet-read-only` against those committed, clean artifacts and consume
   only the current response `data.stdout_json` in memory and durable state.
   Continue only when it reports `status=passed`, `pr_blocked=false`, and the
   response reports `writes_state=false`; no validation file is written. Re-run the full final
   verification suite, final reviewability boundary, packet validation, and
   PR workflow validation against the committed artifacts. Push that packet
   commit only after every repeated check passes, then open the PR with packet fields through
   `gh pr create --base --head --title --body-file`; never derive the title
   from the branch, write the body from scratch, pass inline `--body`, reuse
   prior validation evidence, or repair invalid packets after creation. Before
   any single-PR create attempt, run runner helper
   `validate-pr-workflow-contract` with the packet title and changed-file
   list; a nonzero result blocks the aggregate PR path. If the changed files
   include multi-PR candidate commands or final marker-split evidence for more
   than one PR, the single-PR path is forbidden. `multi-pr-emission` may capture
   a `golden_only` command plan, but it does not emit packets or execute PRs.
   Continue on a split route only when every required feature-local slice packet
   already exists and passes the same read-only validation; otherwise stop
   blocked with validator evidence because split packet output remains deferred.
   Commit the generated packet artifacts, reverify and revalidate them, push,
   create the PR, then update the workflow file. Packet generation, push, and
   PR creation are non-skippable. Require `gh` availability/authentication,
   exact head/base existing-PR reconciliation before and after create, and a
   verified PR number and URL in durable workflow/state evidence. A failure
   leaves PR Creation incomplete; it never authorizes a skip or completion.
   Required evidence prompts: gate status/mode/exit/evidence path,
   fingerprint status, ordered marker IDs, checkpoints, warnings, final
   marker_split or marker-plan-ready handoff, packet validation, and PR
   mappings.
6. **3.3 Review Remediation** — schedule `/loop` to monitor
   and resolve Copilot/human review comments every 5 minutes

After scheduling the loop, re-read the workflow and state. The autopilot is
DONE only when every required Post item is complete, each optional skip is
authorized by its named fail-open procedure, and a live exact-head/base lookup
verifies the recorded PR number and URL. Report the final summary with PR URL.

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
- [Workflow File Protocol](./references/workflow-file-protocol.md) — Per-phase update table + Consensus Resolution Log column schema
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
- `pr-packet-output` — `golden_only` single-packet producer. It accepts only
  structured feature/title/UAT/evidence/scope inputs, derives its feature-local
  body and packet paths plus current git scope, and writes the body before the
  packet. It does not accept raw output paths, content, operations, or split
  metadata.
- `validate-pr-packet-read-only` — Validate an existing feature-local packet and
  return the result in `data.stdout_json` with `writes_state=false`; it does not
  persist validation state.
- `validate-pr-workflow-contract` — Validate PR title and changed-file scope.
- `detect-commands`, `detect-presets`, and `count-markers` — Provide
  deterministic command, preset, and marker evidence through runner-owned
  operation IDs.
- `generate-uat-skeleton` and `final-reviewability-backstop` — Registered but
  deferred for installed workflows; follow the deferred guidance above instead
  of invoking them.
- `validate-pr-packet-write`, `relocate-process-artifacts`, and `restack` —
  Registered but deferred with no active invocation contract. Split packet
  output is also deferred; do not infer those capabilities from generic runner
  plumbing.

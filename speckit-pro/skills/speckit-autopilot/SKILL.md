---
name: speckit-autopilot
description: >
  Autonomous SpecKit workflow executor. Reads a populated workflow file
  and executes all 7 SDD phases (specify → clarify → plan → checklist →
  tasks → analyze → implement) with programmatic gate validation,
  multi-agent consensus resolution, and auto-commits. Use when the user
  says "run autopilot", "execute workflow", "autonomous speckit",
  or has a workflow file ready for execution.
user-invokable: false
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
`Agent(...)`, Opus 4.6 model names, or `/speckit.*` slash-command
orchestration.

## Scope

This skill handles autonomous workflow EXECUTION. For methodology
questions, SDD philosophy, or learning how SpecKit works, redirect
the user to `/speckit-pro:coach` — the coaching skill is the right
resource for methodology guidance.

Your context window will be automatically compacted as it
approaches its limit, allowing you to continue working
indefinitely. Do not stop tasks early. Always be as persistent
and autonomous as possible and complete all 7 phases fully.

You are an **orchestrator** for SpecKit workflows. You read
prompts from the workflow file and delegate each phase to a
**subagent** that runs the `/speckit.*` command. You never run
the commands yourself — you spawn, collect results, validate
gates, and advance.

## Architectural Constraint — Main Agent Is The Orchestrator

This skill loads into the **main session agent** when the user invokes
`/speckit-pro:autopilot`. Only the main agent can spawn subagents — per
[Anthropic's sub-agent docs](https://code.claude.com/docs/en/sub-agents),
**subagents cannot spawn other subagents.** The Orchestrator-Direct pattern
this skill uses works because *the skill IS the main agent at execution
time*; "spawn a subagent for each phase" is a flat fan-out, never nested.

**If this skill is ever loaded inside a subagent context** (for example a
phase-executor mistakenly calls `Skill('speckit-autopilot')`), it MUST
refuse and surface the violation rather than attempt to orchestrate. None
of the bundled phase agents (`phase-executor`, `clarify-executor`,
`checklist-executor`, `analyze-executor`, `implement-executor`,
`codebase-analyst`, `spec-context-analyst`, `domain-researcher`,
`consensus-synthesizer`, `gate-validator`) include `Agent` in their tools
list, so they cannot spawn subagents — this constraint is enforced by the
Anthropic runtime, not just by convention.

## Prerequisites — Model & Effort

The autopilot orchestrator makes gate decisions, synthesizes consensus, and
manages a 7-phase workflow. Running on a weak model produces poor orchestration
decisions that cascade into expensive rework.

**Before executing any step**, verify:

1. **Model check:** You MUST be running on **Opus 4.6** or better. If your
   current model is Sonnet, Haiku, or an older Opus version, STOP immediately
   and instruct the user:

   > "Autopilot requires Opus 4.6 for reliable orchestration. Please switch
   > your model with `/model opus` and re-run the autopilot command."

2. **Effort check:** Verify your effort level is set to `high` or `max`.
   If running at `low` or `medium`, instruct the user:

   > "Autopilot performs best at high effort. Please set `/effort max` and
   > re-run the autopilot command."

These checks are non-negotiable. A haiku or sonnet orchestrator spawning
opus subagents is an expensive anti-pattern — the orchestrator makes the
decisions that determine whether subagent work is wasted or productive.

## Critical: Execution Rules

These rules are non-negotiable. Follow them exactly.

### 0. Forbidden skill invocations

<hard_constraints>

**Do not invoke `grill-me` from any autopilot phase or agent — ever.**

The `grill-me` skill is human-in-the-loop only. It uses `AskUserQuestion`
to interview a real user one question at a time. Inside autopilot, there
is no user available to answer; calling grill-me would either block
indefinitely or produce low-value automated output that defeats the
skill's entire purpose.

Autopilot's Clarify phase uses `/speckit-clarify` with the multi-agent
consensus protocol — that is the **only** sanctioned clarification
mechanism inside autopilot. If a phase encounters ambiguity that
consensus can't resolve, fail the gate and surface to the user.
**Never escalate to grill-me.**

This constraint applies to:

- This skill (the orchestrator)
- All phase-executor agents (`phase-executor`, `clarify-executor`,
  `checklist-executor`, `analyze-executor`, `implement-executor`)
- The consensus analysts (`codebase-analyst`, `spec-context-analyst`,
  `domain-researcher`)
- `consensus-synthesizer` and `gate-validator`
- Any other agent spawned during autopilot execution

Grill-me is for **pre-workflow** human alignment via `/speckit-pro:scaffold-spec`
or `/speckit-pro:grill-me`. It is not part of the autopilot loop and
must not appear in any phase agent's tool call history.

</hard_constraints>

### 1. Subagent per phase

For each phase, spawn a **foreground subagent** via the Agent
tool. The subagent runs the `/speckit.*` command and returns a
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

**Layer 2 — Category-routed consensus** (Tier A, see
`references/consensus-protocol.md`): For EACH unresolved item,
parse the category prefix and dispatch to only the relevant
analyst(s). Two rounds:

```text
ROUND 1 — Category-routed
  Parse the [<categories>] prefix on the unresolved item.
  Spawn N analysts (1 ≤ N ≤ 3) per the routing table:
    [codebase]            → codebase-analyst only
    [spec]                → spec-context-analyst only
    [domain]              → domain-researcher only
    [security]            → ALL 3 (defense-in-depth)
    [ambiguous] or empty  → ALL 3 (safe default)
    [a, b]                → union of named analysts
  Run them in parallel with run_in_background: true.
  Wait for all N to complete.

  Spawn consensus-synthesizer with the routed categories,
  Round=1, and the N analyst responses (mark non-routed
  analysts as "NOT SPAWNED").

  IF synthesizer output: Flags = None AND Confidence = high:
    APPLY artifact edit, log result, done.
  ELSE (Flags includes [ESCAPE_TO_ROUND_2]):
    fall through to Round 2.

ROUND 2 — Full fan-out (legacy 3-analyst path)
  Spawn the (3 - N) analysts that did not run in Round 1,
  in parallel with run_in_background: true.
  Wait for them to complete.
  Re-invoke consensus-synthesizer with Round=2 and all 3
  analyst responses.
  Apply 2-of-3 majority rule per consensus-protocol.md.
  APPLY edit OR flag [HUMAN REVIEW NEEDED] and STOP.
```

The escape-hatch keeps routing cheap when right and safe when
wrong: a `[codebase]`-tagged item where `codebase-analyst`
returns "no precedent in this repo" triggers Round 2 the same
turn — no silently-shipped low-confidence answers.

**Logging requirement:** Every resolution writes a row to the
Consensus Resolution Log in the workflow file with `Round`,
`Routed Categories`, `Outcome`, and `Analysts Used` columns.
The 10% Round-2 escape-rate re-evaluation trigger is computed
from this log (see consensus-protocol.md §"Re-evaluation trigger").

**Consensus rules summary (see consensus-protocol.md for full):**
- N=1 high-confidence → use answer
- N=2 both-agree → use answer
- N=3 2/3 or 3/3 agree → use majority/unanimous
- Any escape-hatch keyword OR low confidence → fall through to Round 2
- All disagree (Round 2) → flag `[HUMAN REVIEW NEEDED]`, STOP
- Security keyword → always Round 2 with all 3, never single-routed

**Why two layers:** Executor handles ~80% directly. Category-routed
consensus spends model effort on the perspective(s) the executor
identified as relevant.

**Why after each prompt:** Later sessions may depend on earlier
resolved questions/gaps.

**Stop conditions:** Gate failure after 2 auto-fix attempts,
failed consensus (all disagree at Round 2), security keyword
flagged for human, or missing prerequisite.

You run in the **main session** (not as a sub-agent) so you can
spawn sub-agents directly. Sub-agents cannot nest — this is the
Orchestrator-Direct pattern.

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
2. **Archive Sweep** — `/speckit.archive.run --sweep --current-target
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
6. **Load settings** from `.claude/speckit-pro.local.md` if present
   (`consensus-mode`, `gate-failure`, `auto-commit`, `security-keywords`).

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

The full **11-entry Post-Implementation task list** and the task
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
    8. After Tasks (G5 pass), run reviewability-gate.sh tasks;
       unexcepted `block` → STOP and split the spec
    9. Advance
```

**Full per-phase prompts, dispatch templates, gate validation
details, hook events, and the dispatcher-agent table:**
see [`references/phase-execution.md`](./references/phase-execution.md).

After all 7 phases pass G7, execute the post-implementation task list.
The 11 tasks, detailed prompts, and extension routing live in
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

For each phase: read the prompt, spawn a subagent, validate.

#### Subagent Prompt Construction

Use the phase-specific executor agent:

```text
Agent(
  subagent_type: "<agent for this phase>",
  description: "SPEC-XXX <phase>",
  prompt: """
    <phase-specific prefix if needed>

    [IF presets detected in Step 0.12]
    PRESET_CONVENTIONS:
      Preset: <name> (priority <N>)
      Overrides: <templates this preset replaces>
      Enforces: <conventions from preset templates>
    [/IF]

    [IF PROJECT_COMMANDS discovered in Step 0.11]
    PROJECT_COMMANDS:
      BUILD: <cmd>  TYPECHECK: <cmd>  LINT: <cmd>
      UNIT_TEST: <cmd>  INTEGRATION_TEST: <cmd>
    [/IF]

    Workflow prompt:
    ---
    <paste the exact prompt from the workflow file>
    ---
  """
)
```

**Agent selection:**

| Phase | subagent_type | Prefix |
| ----- | ------------- | ------ |
| Specify | `phase-executor` | Branch-aware (if ON_FEATURE_BRANCH) |
| Clarify | `clarify-executor` | Parent answers question set |
| Plan | `phase-executor` | None |
| Checklist | `checklist-executor` | None |
| Tasks | `phase-executor` | None |
| Analyze | `analyze-executor` | None |
| Implement | per-task routing | TDD protocol + COMPLETED_TASKS context (see "Implement — Task-Level Dispatch") |

#### Specify — Branch-Aware Prefix

When `ON_FEATURE_BRANCH` is true (Step 0.7), add this prefix
to the subagent prompt before the workflow prompt:

```text
IMPORTANT: Already on feature branch `<CURRENT_BRANCH>`.
Do NOT run `create-new-feature.sh` or create a new branch.
The branch and `specs/<CURRENT_BRANCH>/` directory already
exist. Skip directly to spec content generation.
```

All other phases use `check-prerequisites.sh` →
`get_current_branch()` which detects the worktree branch
automatically. No prefix needed.

#### Clarify — Parent Answering Prefix

The `clarify-executor` is a read-only question-preparation agent.
It returns a `Clarify Question Set` to the parent instead of invoking
the interactive `/speckit-clarify` command or editing artifacts. The
parent orchestrator answers each returned question in the main session,
applies the accepted clarifications to the spec/workflow/state files,
then runs marker checks and consensus routing for unresolved items.
No additional prefix is needed in the prompt — just pass the session
prompt from the workflow file.

#### Multi-Prompt Phases

Clarify and Checklist have multiple prompts. Spawn a
**separate subagent for each prompt**:

- **Clarify:** One subagent per session (e.g., "Session 1:
  Search Behavior", "Session 2: Database Operations")
- **Checklist:** One subagent per domain (e.g.,
  api-workaround, type-safety, requirements)

#### Resolution — After Each Prompt (Main Session)

After EACH executor subagent returns for a consensus phase (Clarify,
Checklist, Analyze), run the two-layer category-routed protocol from
[`references/consensus-protocol.md`](./references/consensus-protocol.md).

**Layer 1** — parse the executor summary for remaining markers
(`[NEEDS CLARIFICATION]`, `[Gap]`), items in the "Unresolved for
consensus" section, and any security-keyword items. If none, advance
to the next prompt/gate.

**Layer 2** — for each unresolved item, parse the `[<categories>]`
prefix and dispatch the routed analysts in Round 1 (parallel via
`run_in_background: true`), then the synthesizer. Escape-hatch to
Round 2 (remaining analysts) on `[ESCAPE_TO_ROUND_2]`. Apply the
synthesizer's Artifact Edit and continue.

**Per-phase verification** (post-resolution): Clarify re-greps for
`[NEEDS CLARIFICATION]`; Checklist re-runs the domain checklist;
Analyze re-runs `/speckit-analyze`. Full per-phase prompts and
verification steps live in
[`references/consensus-protocol.md`](./references/consensus-protocol.md)
§Phase-Specific Consensus Flows.

**Logging requirement:** Every resolution writes a row to the
Consensus Resolution Log in the workflow file. The `Round` and
`Routed Categories` columns are mandatory — the 10% Round-2
escape-rate re-evaluation trigger is computed from them. See
[`references/consensus-protocol.md`](./references/consensus-protocol.md)
§Logging for the canonical column set.

#### Implement — Task-Level Dispatch

Phase 7 dispatches each task to the best-fit agent instead of
one monolithic executor. Subagents can't nest — task-level
routing solves this with flat orchestrator-worker.

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

**Full algorithm** (parse tasks, route, dispatch, accumulate
context, verify): see `references/phase-execution.md` —
"Phase 7: Implement (Task-Level Dispatch)".

## Step 3: Post-Implementation

After all 7 phases complete and G7 passes, follow the
detailed procedures in `references/post-implementation.md`:

1. **3.1 Integration Suite** — verify spec-specific tests
   exist, run FULL suite to catch regressions, fix failures
2. **3.2 PR Creation** — final verification, reviewability diff gate,
   host-template-aware PR body generation, push, create PR with
   `--body-file`, update workflow file
3. **3.3 Review Remediation** — schedule `/loop` to monitor
   and resolve Copilot/human review comments every 5 minutes

After scheduling the loop, the autopilot is DONE. Report
the final summary with PR URL.

## Workflow File Update Protocol

After EVERY phase, update these sections in the workflow file:

| Phase | Sections to Update |
| --- | --- |
| **All** | Status table: `⏳` → `✅` with summary notes |
| **Specify** | Specify Results table, Files Generated checkboxes |
| **Clarify** | Clarify Results table (session focus, questions, outcomes) |
| **Plan** | Plan Results table (artifact status) |
| **Checklist** | Checklist Results table, Addressing Gaps section |
| **Tasks** | Tasks Results table (total, phases, parallel, coverage) |
| **Analyze** | Analysis Results table (ID, severity, issue, resolution) |
| **Implement** | Implementation Progress, Post-Implementation Checklist, Success Criteria |

Also update the Constitution Validation table after Specify (initial)
and Implement (final).

If consensus was used, add entries to the Consensus Resolution Log.

## Error Recovery

### Resuming After Interruption

The workflow file persists all state. To resume:

```text
/speckit-pro:autopilot workflow.md --from-phase <next-pending-phase>
```

The autopilot reads prior artifacts from disk and continues from
the specified phase.

### Common Issues

- **Subagent returns empty/incomplete summary:** Re-spawn with
  the same prompt. If it fails again, run the command directly
  via Bash and parse the output.
- **Gate fails after 2 auto-fix attempts:** If `gate-failure`
  setting is `stop`, STOP and report. Show the gate script
  output so the user can diagnose.
- **Consensus agents all disagree:** Flag `[HUMAN REVIEW NEEDED]`
  and STOP. Present all 3 perspectives to the user.
- **MCP tool unavailable:** Skip research that depends on it.
  Use Read/Grep fallback for codebase analysis. Log warning.

### Context Window Management

For large specs, the context window may fill across 7 phases.
Mitigations:

- Keep sub-agent results concise (summaries, not full artifacts)
- The workflow file is the persistent record — read it rather than
  relying on conversation memory
- Auto-compaction preserves CLAUDE.md and system instructions
- If compacted, re-read the workflow file to restore state

## References

- [Phase Execution](./references/phase-execution.md) — Per-phase
  prompt construction and execution details
- [Consensus Protocol](./references/consensus-protocol.md) —
  Multi-agent resolution rules and flows
- [Gate Validation](./references/gate-validation.md) — Programmatic
  gate checks and remediation loops
- [Post-Implementation](./references/post-implementation.md) —
  Integration suite, PR creation, review remediation loop
- [TDD Protocol](./references/tdd-protocol.md) — Red-green-refactor
  rules injected into implementation agent prompts
- [Plugin Limitations](./references/plugin-limitations.md) —
  permissionMode, hooks, mcpServers restrictions for plugin agents;
  MCP server prerequisites and fallback behavior

## Scripts

Deterministic bash scripts for prerequisite checks and validation.
These ship with the **plugin** at `<SKILL_SCRIPTS>/` (resolved in
Step 0.0 from the skill header's base directory path).
Always invoke via the full resolved path — never from `.specify/scripts/bash/`.

- `check-prerequisites.sh <workflow_file>` — Verify CLI,
  project init, constitution, commands, branch detection (JSON)
- `validate-gate.sh <G1-G7> <feature_dir>` — Validate
  any gate with marker counts and details (JSON)
- `reviewability-gate.sh <setup|tasks|diff> <path-or-range>` —
  Enforce setup, tasks, and pre-PR reviewability budgets (JSON)
- `generate-pr-body.sh <repo-root> <feature-dir> <output-file> [diff-range]` —
  Generate a PR review packet from the host repository PR template when present,
  or from the bundled fallback template
- `detect-commands.sh` — Auto-detect build/test/lint
  commands for Node.js, Rust, Go, Python, Makefile (JSON)
- `detect-presets.sh` — Find installed presets,
  extensions, hooks, template resolution (JSON)
- `count-markers.sh <type> <feature_dir>` — Deterministic
  marker counting (gaps, findings, clarifications, all) for agent
  validation. Used by analyze-executor and checklist-executor (JSON)

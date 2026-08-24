# Phase Execution Reference

**RULES (from SKILL.md — repeated here for clarity):**

1. **SUBAGENT PER PHASE** — Spawn a foreground subagent for
   each phase via the Agent tool. The subagent runs the
   `/speckit-*` command and returns a summary. The parent
   receives the result as a tool response, keeping the agent
   loop alive.
2. **MULTI-PROMPT** — Clarify and Checklist have multiple
   prompts. Spawn a separate subagent for each prompt.
3. **TWO-LAYER RESOLUTION (BATCHED)** — After executor subagents
   return, the main session parses "Unresolved for consensus"
   items and BATCHES dispatch: all routed analysts for all items
   spawned in ONE assistant message (per-item category routing),
   then all synthesizers in ONE message, then serial Artifact
   Edit application. See consensus-protocol.md §Batched Dispatch.
4. **TASK LIST DRIVES EXECUTION** — Check the task list
   after each subagent returns to know what's next.

---

How each SDD phase is executed by the autopilot. Each phase
is delegated to a **foreground subagent** that runs the real
`/speckit-*` command via the `Skill` tool. The subagent
operates in its own context — the command's noise (template
reads, file exploration, completion reports) stays there and
never touches the parent. The parent receives only a summary.

**Future direction (Phase 7 `[P]` tasks):** Phase 7 is **Use site 3**
in the [Agent Teams use-site map](./agent-teams-integration.md). Tasks
marked `[P]` by `/speckit-tasks` are parallel-safe; the planned WS-D2
implementation dispatches `[P]` runs as either an Agent Team (cross-task
coordination via mailbox) when `AGENT_TEAMS_AVAILABLE`, or as batched
background subagents otherwise. See `agent-teams-integration.md` §Use
site 3 for the forward design.

## Contents

- [SpecKit Infrastructure](#speckit-infrastructure) — commands, scripts, templates, constitution
- [Subagent Delegation](#subagent-delegation) — prompt template for phase executors
- [Branch/Worktree Detection](#branchworktree-detection) — context detection before dispatch
- [Stage-Bounded Phase Selection](#stage-bounded-phase-selection) — which phases the resolved stage may start
- [Phase-by-Phase Execution](#phase-by-phase-execution) — per-phase prompts, agents, gates, file updates (Phases 1–7)
- [Full Integration / E2E Suite Verification](#full-integration--e2e-suite-verification) — post-Implement test gate
- [Extension Hook Events](#extension-hook-events) — `.specify/extensions.yml` `before_*` / `after_*` hooks
- [PR Creation Protocol](#pr-creation-protocol) — generate body, push, open PR
- [Copilot Review Remediation Loop](#copilot-review-remediation-loop) — `/loop` scheduling for review comments
- [Workflow File Update Protocol](#workflow-file-update-protocol) — what to write after each phase

## SpecKit Infrastructure

The autopilot relies on the project's installed SpecKit
commands and scripts:

| Component | Location | Purpose |
| ----------- | ---------------------------------------- | --------------------------------------------------------- |
| **Core phase skills** | `.claude/skills/speckit-*/SKILL.md` | Skills that orchestrate each SDD phase (specify/plan/tasks/clarify/checklist/analyze/implement) — SpecKit v0.8.13+ |
| **Extension commands** | `.claude/commands/speckit.*.md` | Slash commands provided by SpecKit extensions (verify, retrospective, …) |
| **Scripts** | `.specify/scripts/<type>/` | Shell scripts for branch creation, path resolution, prerequisite checking |
| **Templates** | `.specify/templates/` | Spec, plan, tasks, checklist, and agent file templates |
| **Constitution** | `.specify/memory/constitution.md` | Project principles for gate validation |

### Key Scripts

| Script | Used By | What It Does |
| -------- | --------- | ----------- |
| `common` | All scripts | Branch detection (`get_current_branch`), feature path resolution (`get_feature_paths`, `find_feature_dir_by_prefix`) |
| `create-new-feature` | `/speckit-specify` | Creates git branch, `specs/` dir, copies spec template. Supports `--json`, `--short-name`, `--number` |
| `setup-plan` | `/speckit-plan` | Copies plan template to feature dir. Outputs `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH` |
| `check-prerequisites` | `/speckit-clarify`, `.checklist`, `.tasks`, `.analyze`, `.implement` | Validates feature dir + required files exist. Supports `--json`, `--require-tasks`, `--include-tasks`, `--paths-only` |

## Subagent Delegation

Each phase is executed by spawning a foreground subagent via
the Agent tool. The subagent:

1. Loads the `/speckit-*` command via `Skill()`
2. Runs the command in its own context
3. Returns a concise summary to the parent

The parent receives the summary as a tool result, which keeps
the parent's agent loop alive. The parent then validates the
gate and spawns the next subagent.

### Subagent Prompt Template

Use the `speckit-pro:phase-executor` agent type for every phase. This
agent is pre-configured with rules to run the command and
return only a structured summary.

```text
Agent(
  subagent_type: "speckit-pro:phase-executor",
  description: "SPEC-XXX <phase>",
  prompt: """
    Run the /speckit-<phase> command.
    Use: Skill("speckit-<phase>", args: "<workflow prompt>")

    <branch prefix if ON_FEATURE_BRANCH>

    Workflow prompt:
    ---
    <exact prompt from workflow file>
    ---
  """
)
```

The `speckit-pro:phase-executor` handles summary formatting and the
"no recommendations" constraint automatically.

## Branch/Worktree Detection

Before executing any phase, detect the current branch context:

```text
# Detect current branch
CURRENT_BRANCH=<command output>

# Check if in a worktree
GIT_DIR=<command output>
GIT_COMMON=<command output>
IS_WORKTREE=<command output>
```

Record two facts:

- **`ON_FEATURE_BRANCH`**: `true` if `CURRENT_BRANCH` matches
  `^[0-9]{3}-`
- **`IS_WORKTREE`**: `true` if `GIT_DIR != GIT_COMMON`

When `ON_FEATURE_BRANCH` is true, the Specify subagent gets
a "skip branch creation" prefix in its prompt. Do NOT use
`export SPECIFY_FEATURE` — env vars do not persist across
tool invocations.

## Stage-Bounded Phase Selection

`AUTOPILOT_STAGE` is resolved once at Step 0.6c. It bounds which phases this
invocation may run:

| Stage | Phase range | Terminal step |
| --- | --- | --- |
| `plan` | Specify, Clarify, Plan, Checklist, Tasks, Analyze | G6.5 confidence gate, then the stage-boundary commit |
| `implement` | Implement, then the post-implementation steps | `Post: Retrospective` |
| `full` | All seven phases end to end | `Post: Retrospective` |

**A resolved stage MUST NOT start a phase outside its own range.** Apply the
range *before* the SKILL.md Step 1 scan picks a row, not after:

```text
candidate_rows = Workflow Overview rows whose phase is in AUTOPILOT_STAGE's range
start = first candidate row whose status is NOT terminal
        (terminal = Complete / ✅ Complete / Skipped / ✅ Skipped / ⏭ Skipped)
if no such row  → the stage's work is already done; run its terminal step, then STOP
```

Select on **"not terminal"**, not on "pending or in progress". This is the
difference that matters. The unbounded scan takes the first row reading
`⏳ Pending` or `🔄 In Progress`, and a `⚠ Blocked` row matches **neither**
arm. After a strict-mode G6.5 stop the six planning rows are terminal and the
`Confidence Gate` row is **blocked**, so the unbounded scan skips straight past
it and lands on the implementation row — starting the very phase the gate just
refused, while the resolved stage still reads `plan`. Both halves look correct
in isolation; only the pair is wrong.

Two consequences follow directly:

- **A non-terminal `Confidence Gate` row makes the planning stage re-enter at
  the confidence gate**, because that row is inside the plan stage's range and
  is the first non-terminal row in it.
- **Crossing that boundary requires an explicit `--stage implement`.** A bare
  invocation re-resolves `plan` (the row is in the planning-complete predicate),
  and the crossing is reported rather than silent.

`--from-phase` still moves the starting point *within* the resolved stage's
range; a value outside an explicitly named stage's range is rejected at Step
0.6c before any phase work begins.

### Implementation Stage: Read The Recorded Verdict, Do Not Re-Run The Gate

G6.5 is the **plan** stage's terminal step, so it is outside the implementation
stage's range. An `implement` invocation **MUST NOT re-run the pre-implement
confidence gate.** Re-running it would score a planning result the operator
already accepted, against artifacts that have not changed since the plan stage
committed — and under `--strict` it could refuse a boundary that was already
resolved.

Instead, read the **recorded verdict**: the `confidence_gate_status` field of
the Step 0.6c `resolve-autopilot-stage` envelope, which echoes the
`Confidence Gate` status row verbatim. Do not read it from the
`## Phase 6.5: Confidence Gate` prose record — that record's field name varies
across workflow files (`Verdict`, `Decision`, `Result`), and a bare composite
score is not a verdict at all: the same score proceeds under advisory mode and
stops under strict, so identical prose accompanies both outcomes. `null` means
no row is recorded, which is legal and is not a verdict.

**The confidence-mode flags stay accepted.** `--strict` and `--advisory` are
advertised unconditionally by both distributions' synopses, so an
implementation-stage invocation **MUST NOT reject them** — rejecting would be
a subtractive change to a shipped surface. It must instead make the flag's
inertness explicit, so an accepted flag never silently does nothing. When
`--strict` or `--advisory` is present on an `implement` invocation, emit:

```text
Stage `implement`: the pre-implement confidence gate (G6.5) belongs to the plan
stage and is not run here, so `<flag>` selects no mode for this invocation. The
recorded verdict is read from the `Confidence Gate` row instead: `<verdict>`.
```

Substitute `<flag>` with the flag as given and `<verdict>` with
`confidence_gate_status` verbatim, or the words `none recorded` when it is
`null`.

**When the recorded verdict is non-terminal, the same diagnostic names it and
says the boundary is being crossed.** A non-terminal verdict — `⚠️ Blocked`, or
any status outside the terminal set — is the state a strict-mode stop leaves
behind. Append:

```text
That verdict is non-terminal: the gate refused this boundary, and `--stage
implement` is proceeding past it.
```

Emit that sentence on **every** implementation-stage run past a non-terminal
verdict, flag or no flag. Naming the implementation stage explicitly remains
sufficient to proceed — the operator is not blocked, and no confirmation is
required. Crossing *silently* is the only thing forbidden.

## Phase-by-Phase Execution

Each phase follows the same pattern: read prompt → spawn
subagent → receive summary → validate gate → advance.

### Progress Task List

Before executing phases, create a **granular** task list
(visible in the CLI, survives context compaction):

- One task per single-prompt phase (Specify, Plan, Tasks,
  Analyze, Implement)
- One task **per prompt** for multi-prompt phases (each
  Clarify session, each Checklist domain)
- One task for consensus/remediation after multi-prompt
  phases (only runs if needed)
- Parse the workflow file to get session/domain names

Update tasks as each subagent returns.

### Phase 0: Prerequisites (Constitution Validation)

**No subagent.** This runs directly in the main session —
it does NOT invoke a `/speckit-*` command.

1. Read `.specify/memory/constitution.md` — extract all
   numbered principles
2. Run automated checks using PROJECT_COMMANDS from Step
   0.10 (BUILD, TYPECHECK, LINT, UNIT_TEST, INTEGRATION_TEST)
3. Verify structural patterns documented in CLAUDE.md
   (e.g., source code organization, module boundaries)
4. Record baselines in the workflow file's Prerequisites
   table
5. Set the "Constitution Check" summary line

**Gate:** G0 — all automated checks must pass. If any
fail, STOP.

**Doctor Health Check (ALWAYS — plugin skill):**
After G0 passes, run `/speckit.speckit-utils.doctor` for a full
project diagnostic (structure, agents, features, scripts,
extensions, git). Log the report in the workflow file.

```text
TaskUpdate: "Phase 0: Doctor Health Check" → in_progress
Agent(
  subagent_type: "general-purpose",
  description: "SPEC-XXX doctor health check",
  prompt: "Run /speckit.speckit-utils.doctor for this project.
    Return the diagnostic report summary."
)
TaskUpdate: → completed
```

⚠️ Use Agent() subagent, NOT Skill() directly — Skill() loads
the command into your context and can kill the agent loop.

### Static Tier-2 Relocation Suggestion

During pre-flight, the parent may inspect the active workflow target and nearby
legacy spec candidates for Tier-2 PROCESS relocation. This is static
inspection/reporting only. The `relocate-process-artifacts` runner operation is
deferred, has no authoritative request, and is unavailable.

Report relocation candidates only for thawed in-scope legacy specs with
relocatable PROCESS artifacts. For each eligible spec, print:

```text
Tier-2 relocation candidate: specs/<spec-dir>.
Deferred: relocate-process-artifacts is unavailable; no runner command may be executed.
```

Do not advertise or invoke either runner mode and do not invent a replacement
helper. The parent must suppress the candidate report for
`frozen/in-flight`, invalid active-feature, already-current, already-normalized,
no-candidate, `non_speckit_namespace`, and `date_named_legacy_namespace`
cases. Record any surfaced suggestion or suppression note in the workflow log
before Phase 1 continues.

### Phase 1: Specify

Read the workflow file's `### Specify Prompt` section.
Spawn a subagent:

```text
Agent(description: "SPEC-XXX specify", prompt: "...")
```

**Branch-aware:** If `ON_FEATURE_BRANCH` is true, add
prefix: "Already on feature branch `<branch>`. Do NOT run
`create-new-feature`. Skip to spec content generation."

**Gate:** G1 — check subagent summary for
`[NEEDS CLARIFICATION]` markers (routing decision)

**Commit:**
`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit -m "feat(SPEC-XXX): complete specify phase"`

### Phase 2: Clarify (Conditional)

Only runs if G1 detected `[NEEDS CLARIFICATION]` markers.

Spawn a **separate subagent for each clarify session**.
The clarify-executor is read-only. It returns a `Clarify Question Set`
with prioritized questions, recommended answers, evidence, and
suggested artifact updates. The parent orchestrator answers returned
questions and applies accepted edits in the main session.

```text
For each clarify session in the workflow file:
  1. TaskUpdate: session task → in_progress
  2. Agent(subagent_type: "speckit-pro:clarify-executor",
          prompt: """
            Prepare a Clarify Question Set for: <session prompt>
          """)
  3. Parent answers returned questions and edits spec/workflow/state
  4. Parse executor's "Unresolved for consensus" section
  5. If unresolved items exist:
     a. TaskUpdate: "<session> Consensus" → in_progress
     b. BATCHED dispatch (see consensus-protocol.md §Batched Dispatch):
        Stage 1: spawn ALL routed analysts for ALL items in ONE
                 assistant message via run_in_background: true.
                 Per-item routing parses the [<categories>] prefix.
        Stage 2: await all → spawn ALL synthesizers in ONE message.
        Stage 3: apply each synthesizer's Artifact Edit SERIALLY
                 to spec.md (preserves write contention safety).
        Round 2 escape-hatch: also batched across all queued items.
     c. TaskUpdate: "<session> Consensus" → completed
  6. TaskUpdate: session task → completed
  7. Proceed to next session
```

**Layer 1 (executor):** The clarify-executor researches possible
questions using web search, library docs, codebase exploration, and
local file analysis (MCP tools preferred when available). It does not
edit artifacts. It returns questions and recommendations to the parent.

**Layer 2 (consensus):** For items the executor flagged
(low confidence, conflicting sources, security keywords),
the main session spawns 3 consensus agents to get distinct
perspectives and applies consensus rules.

**Why after each session:** Session 2 may depend on
Session 1's resolved questions. Both layers complete
before the next session runs.

**Gate:** G2 — verify 0 markers remain

**Commit:**
`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit -m "feat(SPEC-XXX): complete clarify phase"`

### Phase 3: Plan

Read the workflow file's `### Plan Prompt` section.
Spawn a subagent.

**Plan-phase reviewability budget (advisory — never blocks, never crashes):**
After `plan.md` exists, run the standalone plan-phase estimator to project
each slice's production-LOC footprint from `plan.md`'s declared file structure.
This is preventive sizing — it catches an oversized slice at plan time, before
any code is written. It is **advisory only**: no outcome blocks, prompts
mid-autonomous-run, or aborts the run (hard blocking / re-slicing is PRSG-010,
explicitly out of scope here).

Invoke runner helper `estimate-reviewable-loc` from the parent session and
capture the structured response instead of letting a failed helper response
abort the run:

```text
resolved_python -m speckit_pro_runner < request.json

request.json:
{
  "schema_version": "1.0",
  "request_id": "plan-reviewability-budget",
  "helper_id": "estimate-reviewable-loc",
  "operation": "estimate-reviewable-loc",
  "mode": "read_only",
  "inputs": {"plan_file": "specs/<feature>/plan.md"}
}
```

`resolved_python` is the Python 3.11+ interpreter resolved by the installed
runtime contract, not a hardcoded interpreter name.

The three budget statuses (`pass`, `over_budget`, `not_estimated`) all return
runner status `ok` with the verdict in the helper stdout JSON `status` field;
`input_error` is the error path for usage errors or an absent/unreadable
`plan.md`. Branch on the helper stdout JSON `status` when the runner response is
`ok`, and on diagnostics otherwise:

- **`pass`** → log "within budget" and record it in the workflow/plan record
  (silent — no prompt, no block).
- **`over_budget`, autonomous run** → record an over-budget note in the
  workflow/plan record and **CONTINUE** (advisory, non-blocking — FR-004,
  SC-002). MUST NOT block the run or trigger re-slicing.
- **`over_budget`, interactive use** → surface the over-budget result to the
  human as a decision (FR-005).
- **`not_estimated`** (`projected: null` — `plan.md` has no parseable declared
  production-file structure) → record "not estimated (no declared production
  files)" and continue. Never treat this as a within-budget pass.
- **diagnostic response** → record "estimator could not run" with the diagnostic code and
  continue the autonomous run.

This mirrors the established gate-handling pattern below: read the structured
runner response and branch on it rather than aborting.
Advisory-and-never-crash is the invariant for every outcome — under-budget,
over-budget, unmeasured, or errored — none may block, prompt mid-autonomous-run,
or crash the run. If the helper is unavailable on an older plugin build, record
the diagnostic note and continue, same as any other error path.

**Gate:** G3 — verify plan.md, research.md, data-model.md
exist

**Commit:**
`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit -m "feat(SPEC-XXX): complete plan phase"`

### Phase 4: Checklist

Spawn a **separate subagent for each checklist domain**,
with two-layer resolution **after each domain**:

```text
For each checklist domain in the workflow file:
  1. TaskUpdate: domain task → in_progress
  2. Agent(subagent_type: "speckit-pro:checklist-executor",
          prompt: "Run /speckit-checklist with: <domain prompt>")
     The checklist-executor runs the checklist, researches
     gaps, applies fixes, and re-runs to verify (Layer 1)
  3. Parse executor's "Unresolved for consensus" section
  4. If unresolved gaps exist:
     a. TaskUpdate: "<domain> Consensus" → in_progress
     b. BATCHED dispatch (see consensus-protocol.md §Batched Dispatch):
        Stage 1: spawn ALL routed analysts for ALL gaps in ONE
                 assistant message via run_in_background: true.
        Stage 2: await all → spawn ALL synthesizers in ONE message.
        Stage 3: apply each synthesizer's Artifact Edit SERIALLY
                 to spec.md or plan.md.
        Round 2 escape-hatch: also batched across all queued gaps.
     c. Re-run domain checklist to verify gaps closed
     d. TaskUpdate: "<domain> Consensus" → completed
  5. TaskUpdate: domain task → completed
  6. Proceed to next domain
```

**Layer 1 (executor):** The checklist-executor handles
gap research and remediation internally using web search,
codebase exploration, and library docs (MCP tools preferred
when available).

**Layer 2 (consensus):** For gaps the executor couldn't
resolve (remained after 2 loops, low confidence, security
keywords), the main session spawns 3 consensus agents.

**Why after each domain:** Domain 2 may depend on Domain
1's gap fixes. Both layers complete before the next
domain runs.

**Gate:** G4 — verify 0 `[Gap]` markers

**Commit:**
`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit -m "feat(SPEC-XXX): complete checklist phase"`

### Phase 5: Tasks

Read the workflow file's `### Tasks Prompt` section.
Spawn a subagent.

**Gate:** G5 — cross-reference every FR in spec.md with
tasks.md

**Verify Tasks (ALWAYS — plugin skill):**
After G5 passes, run `/speckit.verify-tasks` to detect
phantom completions — tasks marked `[X]` that have no real
implementation. This catches tasks that were incorrectly
marked complete during previous iterations.

```text
TaskUpdate: "Phase 5: Verify Tasks" → in_progress
Agent(
  subagent_type: "general-purpose",
  description: "SPEC-XXX verify tasks",
  prompt: "Run /speckit.verify-tasks for SPEC-XXX.
    Check for phantom completions — tasks marked [X]
    that have no real implementation. Return findings."
)
TaskUpdate: → completed
```

⚠️ Use Agent() subagent, NOT Skill() directly.

**Post-G5 reviewability capture (guarded):**
After G5 and Verify Tasks pass, run the task reviewability gate without letting
the script's compatibility exit code abort the run:

```text
code=0
out=<command output> || code=$?
```

Parse stdout as JSON and record stdout, stderr, exit code, gate
status/mode/exit/evidence path, and a repo-relative evidence path in the
workflow file. If the result is `pass`, `warn`, or an honored typed exception,
continue normally. If the result is a valid current size-only `status=block`
for `mode=tasks`, continue into marker planning and later marker emission; it is
not a manual re-slicing stop and MUST NOT ask the operator to rewrite task
boundaries solely for size.

Correctness stops remain blocking: malformed/stale marker state, failed
verification, invalid packet, unsafe output, unusable gate evidence, invalid
JSON, unreadable artifacts, missing reviewability status/mode, stale
fingerprints, or any non-size safety finding. These stops fire before Analyze or
Implement.

**Optional: Tasks to GitHub Issues:**
If the project uses GitHub Issues for tracking and the GitHub
MCP server is available, export tasks to issues:

```text
TaskUpdate: "Phase 5: Tasks to Issues" → in_progress
Agent(
  subagent_type: "general-purpose",
  description: "SPEC-XXX tasks to issues",
  prompt: "Run /speckit-taskstoissues for SPEC-XXX."
)
TaskUpdate: → completed
```

Skip if GitHub MCP is not configured or the project uses a
different tracker (Jira, Azure DevOps, etc. — those have
their own extensions).

**Atomicity Route (post-G5 — read-only, advisory, records the route):**
After G5 passes, run the read-only atomicity classifier over the
feature directory to decide whether the change can be split into
multiple small PRs safely. Splittability is judged by structural
seams (independent additive capabilities), not lines of code. The
classifier emits ONE machine-readable decision to stdout and writes
no file of its own; **the SKILL records that decision** into the
workflow file's `## Atomicity Route` section. It is advisory-only —
no outcome blocks the run.

```text
# Single positional arg = the feature dir holding tasks.md/plan.md/spec.md.
# Emits {route, releasable, signals[], hints[], warnings[]} (or {"error":…}).
out=<command output>
```

Then record the four surfaced fields (`route`, `releasable`,
`signals`, `warnings`) into the workflow file's `## Atomicity Route`
section via the orchestrator's own `Edit`. Route values:
`split-PR` (proven additive multi-seam), `one-navigable-PR` (default /
abstain, guarded cutover, or modify-heavy), `single-atomic-PR`
(hard-atomic or release-held cutover), `branch-by-abstraction`
(all affected consumers are in-tree and coexistence/migration/contract
evidence is complete), or `out-of-scope` (empty/missing `tasks.md`).
`releasable: false` carries a canonical "CI-green ≠ releasable"
warning for a destructive-migration or concurrency-sensitive change.

**FLAG — this wires NO PR emission and NO branch creation.** The
classifier only records a route for downstream specs to read; actually
emitting multiple PRs or creating branches is **out of scope here** and
belongs to PRSG-008 (layer-planner) and PRSG-009 (multi-PR emission).
The route is recorded ONLY in the workflow file — never in the spec map.
The classifier makes no call to, and no edit of, the reviewability gate;
combining this route with reviewability sizing to decide whether to
*actually* split is a later concern, not this step's.

**PR Marker Plan (post-route, pre-Analyze/pre-Implement):**
When the captured reviewability result is marker-planning input, create or
refresh top-level `pr_marker_plan` state before Analyze or Implement can
continue. The marker plan derives from the current task structure, captured
reviewability finding, plan-declared file/test scope, and recorded hazard route.
Persist it in `autopilot-state.json` and mirror the same schema version, source
fingerprint, ordered marker IDs, review order, checkpoints, warnings, final
marker_split placeholder, packet validation placeholder, and PR mappings
placeholder in the workflow file. `tasks.md` remains the task source, not
authoritative marker state.

On resume, validate the source fingerprint before reusing checkpoints or
emission evidence. A changed fingerprint, malformed/stale marker state, missing
marker membership, changed order, or changed fold target clears affected
checkpoint/emission evidence or stops when the boundary requires current marker
state.

**Commit:**
`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit -m "feat(SPEC-XXX): complete tasks phase"`

### Phase 6: Analyze

Read the workflow file's `### Analyze Prompt` section.
Spawn the analyze-executor subagent.

The analyze-executor runs the analysis, researches ALL
findings at every severity, applies fixes, and re-runs to
verify (Layer 1). Items it can't resolve are flagged in its
"Unresolved for consensus" summary section.

```text
1. TaskUpdate: "Analyze" → in_progress
2. Agent(subagent_type: "speckit-pro:analyze-executor",
        prompt: "Run /speckit-analyze with: <prompt>")
   The executor handles research + remediation (Layer 1)
3. Parse executor's "Unresolved for consensus" section
4. If unresolved findings exist:
   a. TaskUpdate: "Analyze - Consensus" → in_progress
   b. BATCHED dispatch (see consensus-protocol.md §Batched Dispatch):
      Stage 1: spawn ALL routed analysts for ALL findings in ONE
               assistant message via run_in_background: true.
      Stage 2: await all → spawn ALL synthesizers in ONE message.
      Stage 3: apply each synthesizer's Artifact Edit SERIALLY to
               tasks.md, spec.md, or plan.md.
      Round 2 escape-hatch: also batched across all queued findings.
   c. Re-run analyze to verify findings resolved
   d. TaskUpdate: "Analyze - Consensus" → completed
5. TaskUpdate: "Analyze" → completed
```

If 0 unresolved items from executor, skip consensus and
advance immediately.

**Gate:** G6 — verify 0 CRITICAL findings

**Commit:**
`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit -m "feat(SPEC-XXX): complete analyze phase"`

### Phase 6.5: Pre-Implement Confidence Gate

After Phase 6 commits and before Phase 7 begins, run the optional
Pre-Implement Confidence Gate (G6.5). The synthesizer's final
emit on the workflow file (see
[consensus-protocol.md §Pre-Implement Confidence Emit](./consensus-protocol.md#pre-implement-confidence-emit-end-of-phase-6-analyze))
provides the data; the gate script reads it and decides whether
to proceed, surface a remediation hint, or stop.

```
1. Read mode from `CONFIDENCE_GATE_MODE` (set at Step 0.6b — see
   [Prerequisites](./prerequisites.md) and the SKILL.md orchestration
   summary). Do not re-run `resolve-confidence-mode` here —
   the resolver runs once at autopilot start so `--strict --advisory`
   conflicts fail fast before any phase work happens, instead of
   surfacing 6 phases in.

2. Resolve threshold from .claude/speckit-pro.local.md
   (`confidence_threshold: 0.90`). Default: 0.90. (Per-invocation
   threshold override is out of scope for this gate; only the mode
   flag is invocation-overridable.)

3. On entry, print the /goal tip (Claude Code interactive only):
   "Tip: run `/goal achieve confidence ≥<threshold> on the
   pre-Implement gate` in a separate Claude Code message to get the
   live ◎ /goal active indicator. In Codex `codex exec`, /goal is
   not first-class — the 3-iteration cap is the safety bound."

4. Run the gate:
     runner helper confidence-gate \
       <workflow-file> --threshold <T> --mode <M>

5. Parse exit code + JSON:
   - exit 0 (PASS): TaskUpdate G6.5 → completed; advance to Phase 7.
   - exit 1 (NO_DATA): log a warning, surface to operator that the
     synthesizer skipped its confidence emit (treat as a plugin
     regression report). TaskUpdate G6.5 → completed with a
     `no_data: true` note. Advance to Phase 7.
   - exit 2 (FAIL):
       a. Read JSON `criteria` object; find the lowest-scoring
          criterion (lowest numeric value among the 5 keys).
       b. If iteration_count < 3:
            - Dispatch a focused consensus round on that criterion's
              underlying artifact (e.g., "task_understanding" lowest
              → re-evaluate spec.md ambiguity via clarify-executor
              re-pass; "risk_assessment" lowest → re-run analyze on
              remaining open findings; "completeness" lowest →
              re-verify artifact presence).
            - After remediation completes, dispatch the
              consensus-synthesizer agent (single fan-out) to
              re-emit the pre-Implement Confidence block to the
              workflow file.
            - Re-run confidence-gate.
            - Increment iteration_count.
       c. If iteration_count == 3 OR exit 0 reached: stop iterating.
       d. After max iterations:
            - mode=advisory: log the final score + breakdown,
              surface the iteration history to the operator,
              advance to Phase 7.
            - mode=strict: STOP. Surface the breakdown + history.
              Operator may resume with `--stage implement` if they
              accept the lower confidence; that run reads this
              recorded verdict rather than re-running the gate, and
              reports that it is crossing a refused boundary. The
              older `--from-phase implement` form keeps working.
```

The iteration cap of 3 is the only safety bound when `/goal` is
not available (Codex `codex exec` headless mode). In Claude Code
interactive mode, an operator-set `/goal` provides an additional
turn-based check layered on top.

**Why this gate is opt-in for blocking:** the autopilot already
runs Clarify (G2) and Analyze (G6) gates before this point, so
most pre-Implement shakiness is already filtered. Advisory mode
surfaces the score and a remediation hint without blocking;
operators who want a fail-closed posture opt into strict via
`.claude/speckit-pro.local.md` or pass `--strict` on a single
invocation. Per-invocation flag wins over local config.

**TaskCreate**: at autopilot start, after the G6 task, create a
G6.5 task: `Confidence gate (pre-Implement)`. Mark it
`in_progress` on entry to this phase and `completed` on exit
regardless of advisory pass-with-warning vs strict pass.

#### Plan stage: G6.5 is the terminal step

G6.5 runs *after Phase 6 commits and before Phase 7 begins*, so on a
`--stage plan` run it is the last work the stage does. The run takes the
stage-boundary commit below and then **STOPs** — it does not advance to Phase 7,
in any mode. In advisory mode the gate passes or warns and the stage still ends
here; in strict mode the STOP **is** the gate resolving, and the boundary commit
is still taken so the failing verdict reaches version history.

On a strict-mode stop, write the `Confidence Gate` row to a **non-terminal**
blocked status — never to a terminal one. The row must advance off its pending
state (so the boundary commit is non-empty) while leaving the planning-complete
predicate unsatisfied (so a later bare invocation re-resolves `plan` rather than
crossing the boundary the gate refused). Record the failing verdict in a form
the gate-record matcher does **not** read as a pass: a non-terminal row sitting
beside a record that scans as a passing G6.5 is exactly the
status-versus-evidence contradiction that the Step 1.1 coverage guard and the
tree-wide CI gate both fail on.

#### Stage-boundary commit (plan stage only)

After the gate resolves — pass, warn, or strict stop — take **one distinct
commit**. It is not a renamed analyze-phase commit: that commit was already
taken before the gate ran, so renaming it would leave the verdict uncommitted.

```text
git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json \
  && git commit -m "chore(SPEC-XXX): close the plan stage boundary"
```

Three properties, each load-bearing:

- **The message names the stage boundary, not a phase**, so the boundary is
  identifiable in version history.
- **The staged path set is the same enumeration as the per-phase bookkeeping
  commits** — the specification directory, the workflow file, and the state
  file. Never the workflow *directory*, which also holds untracked run
  byproducts that a directory-wide add would sweep in.
- **The commit is non-empty regardless of whether the `Stage` row changed**,
  because the `Confidence Gate` row always advances off its pending state — so
  the conditional second `Stage` write needs no empty-commit escape hatch.

`chore:` because a planning-stage boundary ships no runtime change and must not
trigger a release-please version bump, the same reasoning the spec-MOC
regeneration commit below uses for its `docs:` subject.

#### Draft-PR emission: the terminal-step sequence (plan stage only)

Once the final gate resolves **pass or warn**, the plan stage's terminal step
does not end at the boundary commit above. It runs this sequence, in this order:

```text
1. Generate the artifacts into specs/<feature>/artifacts/.
2. Take the stage-boundary commit above.
3. Push the branch.
4. Create or refresh the draft pull request.
5. Write the `Draft PR` record to the workflow file.
6. Take a separate bookkeeping commit carrying that record, and push it.
```

**Generation runs first** because the pages land under
`specs/<feature>/artifacts/`, which the boundary commit's existing `specs/` path
already stages. The order is what lets that commit carry the artifacts with its
staged path set unchanged.

**Step 2 is the boundary commit above, not a second one.** Its message
(`chore(SPEC-XXX): close the plan stage boundary`), its staged path set, and its
non-emptiness are exactly as that subsection states them. The `Draft PR` record
is never folded into it — the record does not exist yet at step 2, and writing it
there would put a pull-request identity in the commit that closes the boundary
rather than in the commit that records the hand-off.

**The push at step 3 is load-bearing.** No earlier plan-stage step pushes the
branch, so without it creation has no remote head to open against and fails on
every run. Detect the remote name rather than assuming it, the same way the PR
Creation Protocol below does.

**The bookkeeping commit at step 6 stages the workflow file** — the only file
this step writes. Never the workflow *directory*, which also holds untracked run
byproducts that a directory-wide add would sweep in. Its message follows the
repository's conventional-commit shape, and `chore:` for the same reason the
boundary commit uses it: recording an identity ships no runtime change.

```text
git add <workflow-file-path> \
  && git commit -m "chore(SPEC-XXX): record the draft pull request"
```

**Each step is a precondition for the next, and no step is retried
automatically.** The operator re-run is the recovery path, and the two-way
existence test below is what makes that re-run safe. A failed step stops the
sequence where it failed and reports through the stop-report shape for that step.

**A re-run reaching a step whose content is already committed has nothing left to
stage there.** Such a commit is a no-op, not a failed step: the sequence
continues past the nothing-to-commit condition rather than reading it as a
failure, and it needs no empty-commit escape hatch. This does not weaken the
boundary commit's non-emptiness above, which describes what a first pass
produces — that pass's `Confidence Gate` row advances off its pending state, and
a re-run of an already-resolved stage does not repeat that advance. Treating the
resulting empty stage as a failure would strand the operator re-run that is the
only recovery path.

#### Artifact generation: the `artifact-author` dispatch

Step 1 is one dispatch of the `speckit-pro:artifact-author` subagent. The
orchestrator hands it the feature's planning record and the shipped gallery, and
it returns one outcome per page it wrote or could not write:

```text
Agent(
  subagent_type: "speckit-pro:artifact-author",
  description: "SPEC-XXX draft artifact generation",
  prompt: """
    Author this feature's draft-stage gallery pages and write them into
    specs/<feature>/artifacts/.

    Inputs, all read-only:
    - Specification: specs/<feature>/spec.md
    - Plan: specs/<feature>/plan.md
    - Tasks: specs/<feature>/tasks.md
    - Design concept: docs/ai/specs/.process/<SPEC-ID>-design-concept.md
    - Gallery manifest: speckit-pro/artifact-gallery/manifest.json
    - Templates: speckit-pro/artifact-gallery/templates/<entry-id>.html

    Select, fill, and report per your agent instructions. Return one outcome
    per selected page.
  """
)
```

**Selection lives inside the agent and is driven by the manifest.** The
orchestrator names no page list of its own. The agent reads
`speckit-pro/artifact-gallery/manifest.json`, keeps the entries whose `stage` is
`draft-pr`, and applies each surviving entry's `trigger`: `{"always": true}`
selects on every run, and `{"any_of": [...]}` selects only when the feature
carries at least one signal the entry names.

As the manifest stands, that routing selects the implementation-plan and
spec-explainer pages on every run, the code-approaches page only on the
`competing_approaches` signal, and the module-map page only on the
`brownfield_change` signal. **The manifest is read at run time and wins over
that sentence.** It is the routing's source of truth and it grows, so a page
list memorized from this paragraph goes stale, and a draft-stage entry shipped
later must route from the manifest alone with no edit here.

**The gallery is input, never output.** `speckit-pro/artifact-gallery/` holds
the shipped manifest and the shipped templates, and writing anything into that
directory is a defect. Finished pages are written to
`specs/<feature>/artifacts/`, one per selected entry, keeping the manifest
entry's `id` as the filename stem.

**Each outcome is `generated` or `gap`**, one per selected page, and a gap names
what is missing and why. **A page with any unfilled slot is a gap for that page,
not a partial success** — a half-filled page is never reported as generated.
Feed the outcome list to the three sinks under fail-open below. That subsection
owns where each outcome is written and which runs reach it; this step owes it
nothing but the outcomes themselves.

**A dispatch that cannot report is a whole-set gap, not a failed step.** An
agent that errors, returns nothing, or returns something that cannot be read as
an outcome list leaves the run with zero generated pages and one whole-set gap
naming that reason. The precondition rule above binds the steps that stop the
sequence; generation is not one of them, because fail-open below turns every
shortfall this step can produce into an outcome. The sequence continues to
step 2 either way.

**A truncated report is not a clean one.** An agent that exhausts its budget
while composing its summary returns a fragment, and a fragment that does not
carry one outcome per selected page is exactly the "cannot be read as an outcome
list" case above — it takes the whole-set gap rather than being read as far as it
got. A partial summary is missing information, never evidence of success, and a
gap count read off one is not a measurement.

**Reconcile current-run ownership before trusting any artifact file.** Read the
manifest's `draft-pr` entry IDs after the dispatch. A complete outcome list owns
only the IDs it reports as `generated`; an error, timeout, truncated result, or
unreadable list owns none. Delete every draft-stage final `.html` whose ID lacks
a complete current-run `generated` outcome, and delete every sibling
`.artifact-author-*.tmp` file. This cleanup removes stale results from prior
runs as well as interrupted writes. After deletion, re-read the artifact
directory and require that every remaining draft-stage final ID is owned by the
complete current-run `generated` set and that no `.artifact-author-*.tmp` file
remains. A successfully removed page is ordinary fail-open gap handling. A
failed deletion or an ownership postcondition that cannot be established is an
artifact-integrity failure: STOP before staging, the boundary commit, push, or
pull-request creation or refresh, because fail-open cannot safely preserve an
unowned file.

#### The written pages are verified on disk, not taken on report

**Every outcome above is a claim about a file; this step checks the file.** The
agent reports what it believes it wrote, and a dispatch that dies partway through
can leave a page on disk its own report never mentioned. Run this check after the
dispatch returns and **before the boundary commit**, so nothing that fails it can
reach a commit.

For each page written to `specs/<feature>/artifacts/`, two positive tests:

| Test | The page fails when |
| --- | --- |
| it is not its own template | the file is byte-identical to `speckit-pro/artifact-gallery/templates/<entry-id>.html` |
| it is not still sample content | the body carries a sample-banner element: `class="sample-notice"`, `class="notice"`, or `class="note"` |

**The banner test covers only the templates that carry a banner.** Seven of the
shipped templates mark theirs, under three different class names, and the rest
carry none at all. On those, byte-identity is the only guard, and one byte of
drift defeats it. Neither test is a substitute for reading the page when the
outcome is in doubt.

**A page that fails either test is a gap for that page — whatever the agent
reported — and the file is deleted.** Deleting is the point. The shipped
templates are complete worked examples built on an invented feature, so an
unfilled page is neither empty nor obviously broken: it is a plausible-looking
document about something else. Left on disk it is committed, pushed, and linked
from the pull-request body as though it were real.

After every verification-driven deletion, re-read that path and require it to
be absent. If an invalid or sample page cannot be removed, STOP before staging,
the boundary commit, push, or pull-request creation or refresh. Demoting the
outcome remains fail-open only when the invalid file is verifiably gone; a
surviving invalid file is the same artifact-integrity failure as a surviving
unowned file.

**This is why an emptiness check cannot stand in for these two.** "Is every
marked region populated?" answers yes on a page that was never touched, because
the shipped region content is populated prose. Both tests above are positive —
they ask what the page *is*, not whether something is missing from it.

**The check converts outcomes; it never blocks.** A page turned into a gap here
reports through the same three sinks as any other gap, and a run whose every page
fails still opens the pull request carrying a whole-set gap. Fail-open is
unchanged. What changes is that a page no reader could tell from a template is no
longer counted as generated.

#### Strict-mode block: the return happens before generation

On a strict-mode block the run never enters the sequence above. The blocked-stop
contract from the two subsections above is preserved exactly: the boundary
commit is still taken, the `Confidence Gate` row is written to a **non-terminal**
blocked status, and the stage STOPs. That commit belongs to the blocked-stop
contract in its own right; it is the rest of the sequence — generation, push,
create-or-refresh, the record, the bookkeeping commit — that does not run.

**The return is placed before generation, not around it.** A blocked stage
therefore generates no artifact pages at all, pushes nothing, opens no pull
request, and writes no `Draft PR` row. Emission is not something the blocked path
fails open through; it is something the blocked path never reaches. The re-run
that resolves pass or warn is the run that emits.

#### Create or refresh: the two-way existence test

Exactly one draft pull request exists per feature branch. Before creating one,
test for an existing one **two ways**:

| Test | Source |
| --- | --- |
| the recorded identity | the workflow file's `Draft PR` row |
| the live identity | one read-only query for an **open** pull request on the head branch |

**Either positive proves one exists.** Neither test alone is sufficient, because
the record is written only after creation succeeds: a run interrupted between the
two leaves a pull request with no record, which the record test alone would read
as "none exists" and answer by opening a second one.

Take the live test as one read-only query that returns structured output, and
read the fields with a structured parser:

```text
gh pr list --head <branch> --state open --json number,url,title
```

**When either positive fires, the run refreshes rather than creates.** Refresh
the pull request's description; refresh its title as well when the title changed;
write or repair the workflow file's `Draft PR` row; and report that existing URL
as the emission outcome. Never open a second pull request for the branch.

```text
gh pr edit <number> --body-file <packet.body_file> [--title <packet.generated_title.value>]
```

**Create only when neither positive fires**, and create in draft state:

```text
gh pr create --draft --base <packet.target.base_branch> --head <packet.target.head_branch> \
  --title <packet.generated_title.value> --body-file <packet.body_file>
```

A recorded pull request that is closed or merged is a discrepancy, not grounds to
open a second one.

**A live query that cannot answer is not proof that nothing exists.** When the
query tool is absent, unauthenticated, rate-limited, or returns output that
cannot be parsed, and no `Draft PR` row is recorded either, the run has no basis
for creation. It refuses to create and reports through the could-not-be-opened
shape below, rather than risking a duplicate pull request on a branch it could
not observe.

**Self-validate the title before creation.** The title is final-shape at
creation and is not re-derived at the later ready flip:

`<type>(<lowercase-scope>): <plain English description>`

`type` is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, and the
scope is **lowercase**. Validate the exact string through the release-readiness
gate's `validate-pr-title` operation before creating. The packet schema alone
would also accept an uppercase ticket-style scope; the release-readiness shape
would not, so the lowercase form is the binding one. Draft-mode title validation
checks the conventional shape only — it does not ask the description to reference
verification or evidence a draft has not produced.

**On a title that fails its self-validation, do not create the pull request.**
Report through the could-not-be-opened shape below rather than opening one whose
title a human would have to repair.

#### The draft description: exactly two blocks

The description carries exactly two blocks and nothing else:

```text
## Artifacts

| Artifact | Purpose | Open |
| --- | --- | --- |
| Implementation Plan | Lay out the phases of the planned change | `open specs/<feature>/artifacts/implementation-plan.html` |
| Spec Explainer | Explain what the feature does and why | `open specs/<feature>/artifacts/spec-explainer.html` |

## Resume

Stage: plan — stopped at the plan-stage boundary for review.
Resume with: `/speckit-pro:speckit-autopilot <workflow-file> --stage implement`
```

- **The artifacts index** is a table of three columns: the artifact, its purpose
  in one line, and a copy-paste command that opens it locally.
- **The resume/status block** names the stage the run stopped at and the exact
  command that resumes it.

**Forbidden in a draft description**: a release-note fence, any verification
section, any scope or UAT section, and any placeholder final-writeup content. The
pull request sits in draft state, so the repository's PR checks do not run
against it — no release-note fence is needed or wanted, and a placeholder section
would read as evidence that does not exist.

**The orchestrator composes both blocks itself.** Emit the packet with
`runner helper pr-packet-output` in `draft` mode and pass the finished Markdown
as `inputs.body`; the producer uses that string verbatim. The `build_packet_body`
fallback stays single/split-shaped and is never reached in draft mode.

#### Fail-open: three sinks, and the runs that reach them

Artifact generation fails open. A generation failure of any size — one page,
several, or the whole set — still opens the pull request. Emission is the review
hand-off, and no generation shortfall may withhold it.

The shortfall is recorded in three sinks, so the same fact is legible wherever a
reader looks:

| Sink | What it carries |
| --- | --- |
| the artifacts index in the description | a gap-marked row in place of the artifact row |
| the plan-stage stop report | a note naming the shortfall |
| the workflow file's `Draft PR` row | the gap note that follows the link in the same cell |

**Every gap-marked row names what is missing and why** — the individual page when
a page failed, or the whole set as a single row when selection itself could not
run. A page whose marked fill regions are not all populated is a gap for that
page rather than a partial success.

**A run that produced zero artifacts still opens the pull request.** Its index
table is present under its heading and carries only gap rows. The table is never
omitted, and never left as a heading with no rows under it.

**The sink-reachability rule.** Each sink binds only the runs that reach it. A
run that stops at create-or-refresh because the recorded and live identities
disagree, or stops before creation because a step of the sequence failed, writes
no pull-request description and no `Draft PR` row — its shortfall reaches the
stop report alone. A run whose bookkeeping commit failed after creation has
written the description but not the record. In each case the unwritten sinks are
a consequence of the run not getting there, and are **not** a fail-open
violation. The stop report is the one sink every such run reaches, so it carries
the shortfall on all of them.

#### The plan-stage stop report

The stop report is what an operator reads to decide what to do next, so every
failure shape names the step that failed, the state it left behind, and the
resume path — one line of substance each, in the style Step 0.6c already uses, so
the report alone is enough to hand off.

- **Emission ran.** Carry the pull request URL, the artifact index, and the
  resume instructions.
- **The gate blocked.** Name the blocked gate in place of a URL, and say that no
  pull request was opened.
- **The pull request could not be opened.** Say so and name the step that
  refused — title self-validation, an existence query that could not answer, or
  creation itself. Note that the artifacts and the boundary commit are already
  committed on the branch, so no planning work is lost, and name the resume path.
- **The branch push failed.** Name the failed push, state that no pull request
  was opened and no `Draft PR` row was written, and name the resume path. The
  artifacts and the boundary commit sit on the local branch and nothing reached
  the remote.
- **The bookkeeping commit or its push failed after create-or-refresh.** Carry
  the pull request URL, say the `Draft PR` record did not reach the remote, and
  name the resume path. The pull request is neither closed nor recreated and the
  record is not discarded: the re-run finds the open pull request through the
  two-way existence test and repairs the record instead of opening a second one.
- **The recorded and live identities disagree.** Name which disagreement it is —
  the recorded pull request is closed or merged, it could not be found at all, or
  a different pull request is open on the branch. State that nothing was created,
  refreshed, or recorded and that the row was left exactly as found, and name the
  manual resume path for that case: reopen it yourself and re-run, or correct or
  clear the row and re-run. Carry both identities when they differ. The artifacts
  and the boundary commit are already committed and pushed, so no planning work
  is lost.

That is six shapes, and the set is closed. Every one of them names the step that
failed, the state it left behind, and the resume path, so an operator can act on
the report without reading the run's logs.

#### The `Draft PR` row

The pull request's identity is recorded as one scalar row keyed `Draft PR` in the
workflow file's `### Basic Information` table. Its placement, grammar, and legal
states are in
[workflow-file-protocol.md §The Draft PR Entry](./workflow-file-protocol.md#the-draft-pr-entry).
What the emission sequence owes it:

- **Written only after creation or refresh succeeds.** Before that there is
  nothing to record. An absent row is information — it means no pull request has
  been opened for this feature — and is never reported as an error.
- **Carried by the bookkeeping commit**, never folded into the stage-boundary
  commit.
- **Repaired, not skipped.** When a pull request exists but the row is missing or
  wrong, write or repair it. That is what a run interrupted between creation and
  the record leaves behind for the next run to fix.
- **Rewritten whole from the current run's outcome, every time.** A refresh whose
  shortfall differs from the recorded one replaces the note; a refresh that
  generated every selected page leaves the cell carrying the link alone. A note
  describing an earlier run's shortfall never survives a later refresh that no
  longer fell short.
- **Left exactly as found** when the run stops at create-or-refresh because the
  recorded and live identities disagree. A run that creates nothing and refreshes
  nothing records nothing.

**The workflow file is the only place this identity is stored — there is no
state-file mirror.** That is why this row behaves differently from the `Stage`
row that shares its table. `Stage` has a mirror, and therefore a write cadence
and a same-edit-turn rule to keep the two in step. Writing the `Draft PR` row
neither counts against nor re-triggers that cadence, and needs no state-file
write at all: the two rows are matched by key, so neither writer disturbs the
other's value, and this identity has no mirror to keep in step. A second sink
would introduce exactly the status-versus-evidence drift the Step 1.1 coverage
guard and the tree-wide CI gate already fail on.

#### What each corroboration status means at the terminal step

Step 0.6c classifies the recorded `Draft PR` row against one live observation and
reports one of six statuses. Three of them are ordinary and three are
discrepancies. This is what each one means here, at create-or-refresh:

| Status | Terminal-step behaviour |
| --- | --- |
| `match` | refresh the recorded pull request's description, and its title if the title changed; report that URL |
| `no_record` | fall through to the live by-branch existence test above, then create or refresh |
| `skipped` | **never create.** The present row is already a positive under the two-way existence test, so a run that merely could not reach the tool has not learned that no pull request exists. Refresh the recorded pull request when the tool can be reached; when it cannot, report through the could-not-be-opened path |
| `pr_closed` | do not reopen it, do not open a second one, and leave the row exactly as found. The stop report names the number, the URL, that **the operator** may reopen it with `gh pr reopen <number>`, and that a re-run then proceeds normally |
| `pr_missing` | do not create, do not rewrite the row. The stop report names the recorded identity and says to correct or clear the row, then re-run |
| `identity_mismatch` | do not create. The stop report names **both** identities — the one recorded and the one observed — and the manual resume path |

**`gh pr reopen` is the operator's own step and never automation's.** It appears
in this reference only as prose inside a resume path. Nothing in this sequence
runs it, and nothing infers permission to run it from the fact that the stop
report mentions it.

**No second pull request is opened in any discrepancy class.** That is the single
invariant the three discrepancy rows share, and it is why each of them stops
rather than falling through to creation.

**All three discrepancies end the attempt at create-or-refresh** — after
generation, after the stage-boundary commit, and after the push. Never earlier.
Ending earlier would strand the durable discrepancy line: that line is written at
stage resolution, and it reaches version history only inside a commit this stage
goes on to take. A run that stopped before its own boundary commit would discard
the very record of why it stopped.

**This is fail-open.** A discrepancy does not invoke the strict-mode blocked-stop
contract, does not mark the gate blocked, and does not change the resolved stage.
The stage did everything it could and reports what it found.

**The two reads are separate, and the later one is the current evidence.** The
observation Step 0.6c takes at resolution and the existence query the terminal
step takes before creating are two different reads, with the whole stage running
between them. Do not treat the resolution-time observation as current at the
terminal step: a pull request can be opened, closed, or replaced while the stage
runs, and the emission-time query is the one that governs.

#### When reviewability later splits the work

A draft pull request opened here is **not** a throwaway. When the final
reviewability boundary later determines the work must land as more than one pull
request, this draft becomes the **first slice** of that stack. It is never
closed, superseded, or recreated to make room for the split.

The reason is the review thread. By the time a split is decided, the draft may
already carry review comments, and closing it to open replacements would discard
that conversation and ask reviewers to repeat themselves. The packet identity is
stable across the transition, and that stability is what preserves the thread.

Nothing in this sequence closes, supersedes, or recreates the draft pull request.
Refresh is the only mutation it ever performs on an existing one.

### Phase 7: Implement (Task-Level Dispatch)

Phase 7 uses **task-level dispatch**: the orchestrator parses
tasks.md and dispatches each task (or parallel group) to the
best-fit agent. This replaces the monolithic implement-executor
pattern.

When top-level `pr_marker_plan` is available and current, Phase 7 executes,
checkpoints, and records evidence in marker order. Each marker's tasks run in
the marker's `review_order`; within one marker, keep the existing task-order and
`[P]` parallel rules. After a marker completes, record a checkpoint with the
marker ID, ordered task IDs, test/verification evidence path, fingerprint
status, checkpoint commit SHA (`implementation_checkpoint.head_sha` or
`implementation_checkpoint.commit_sha`), warnings, and any blocked/fixed tasks.
The marker checkpoint SHA is the source commit for later live marker PR
branches. Do not infer a new marker order from changed files or reviewability
warnings.

**Why task-level:** Subagents cannot spawn other subagents
(Claude Code platform constraint). The flat orchestrator-worker
pattern — recommended by Anthropic's BrowseComp architecture
and Research system — routes each task to a specialized agent
from the orchestrator level.

#### Phase 7 Setup: The Pull-Request Feedback Sweep

Run the sweep **first**, ahead of the byproduct directory below and ahead of
the implementation-notes record. Reviewer feedback left on the draft pull
request this stage already opened is read, classified, recorded, and answered
before the first task is dispatched, so a comment that arrived while the stage
was running is acted on rather than overtaken by the work it asks about.

The sweep runs only when the workflow file carries a Draft PR row whose
corroboration status is `match`. It **adds no row to the Workflow Overview
table**, and it changes neither the phase-coverage guard's governed phase-id
list, the stage-to-phase map, nor the workflow template. It is a setup step
inside a phase that already exists, never a phase of its own.

#### Phase 7 Setup: The Run Report Every Path Builds

**Every path ends in the run report, and every run builds exactly one.**
Stopping or proceeding, the sweep finishes by building the report described
here. The sections below name only what their own condition contributes to it
and never restate its shape. A run where several stopping conditions hold
builds **one** report naming every one of them, never one report per
condition.

**Three parts, in this order.** The **condition**: what stopped the run, or
that it proceeded. **What already landed** before that: the commits pushed,
the log rows written, and the replies posted so far. The **resume path**, one
line of substance.

**What already landed is written as empty, never left out**, on a stop that
happens before any write. An absent part reads as an oversight, while "no
commit, no row, no reply" reads as a fact an operator can act on.

**The per-comment dispositions sit inside that one report.** Report each
observed comment, candidate and exclusion alike, and name a reason on every
exclusion: the trust filter reports `not swept: untrusted author`, and every
self-reply exclusion is named the same way. The proceed path is exactly where
a run that swept nothing but untrusted comments lands, and a silent proceed
there would leave an operator no way to tell it from a run that saw nothing. A
run that observed no comment at all reports that, as a one-line report rather
than an absent one.

**Every redaction event goes in, on every path, stopping or proceeding**: per
affected comment the comment id, the leg, the rule, and the count, and nothing
else about the match.

**The report names the sweep's byproduct directory as removed, on every
path.**

**The report goes to the operator's sink**, the one the plan-stage stop report
reaches, and never to the pull request.

**The conditions that end a run in this sequence** are an invalid
authenticated account, a corroboration status that is neither `match` nor
`no_record` or one outside the six, a failed observation, an unreadable
Feedback Sweep Log row, a malformed classifier or analyst record, a resolved
edit target outside the three artifacts, a failed push, a consensus outcome
requiring human review, one or more amendments requiring re-review, and one or
more redaction events reported once every write landed. The last two are the
only ones that are not failures.

**One condition needs more than the shared shape.** The human-review stop's
resume path names **both** operator actions, resolve the substance and re-run
**or** resolve the thread, because it is the only stop whose resume path a
re-run alone does not satisfy.

#### Phase 7 Setup: The Corroboration Gate

**The six corroboration statuses are exhaustive, and each maps to exactly one
outcome.** Step 0.6c classifies the recorded `Draft PR` row and reports one of
them, and the sweep reads that report rather than taking an observation of its
own. No status falls to a default, and no two share a behaviour by accident.

| Status | What the sweep does | Resume path |
| --- | --- | --- |
| `match` | sweep | none, the run proceeds |
| `no_record` | proceed without sweeping | none, the run proceeds |
| `skipped` | stop | fix the tool, then re-run |
| `pr_closed` | stop | reopen the pull request, or clear the `Draft PR` row if the checkpoint is genuinely abandoned, then re-run |
| `pr_missing` | stop | clear the row, then re-run |
| `identity_mismatch` | stop | correct the row to name the right pull request, then re-run |

**Each stopping status names its own resume path**, because the four have
different fixes and one shared path would send an operator to the wrong repair.
**Clearing the row belongs to `pr_missing` alone**: it is the one status where
the row's absence would match reality.

**The sweep never writes the `Draft PR` row on any path**, these four stops
included. A run that repaired the record it had just failed to corroborate
would destroy the evidence of the discrepancy, and the next reader would find a
healthy row where a stop had been.

**A value outside the six is a malformed record and stops.** Do not map it onto
one of the six, and do not read it as absence. Exactly one status proceeds, so
a default that proceeded would make a corrupted record the cheapest way past
the checkpoint.

**`skipped` and `no_record` are different readings and never interchangeable.**
`no_record` means the gate **does not apply**: no draft pull request was ever
opened, so there is no checkpoint to carry unread feedback, and the run
proceeds. `skipped` means the gate **applies and could not be evaluated**: a row
is recorded and the observation behind it failed, so the run stops. Treating
"could not observe" as "observed nothing" would make the checkpoint silently
optional exactly when the tool is unreliable, which is when unread feedback is
most likely to be sitting on the pull request.

**A tool that was absent, unauthenticated, rate-limited, or that returned output
which could not be parsed is not evidence that a recorded pull request is
gone.** Those four are the causes of a `skipped`, and not one of them observed
anything about the pull request.

**The `skipped` report must read differently from the three discrepancy stops,
and must name which of the four causes occurred**: the tool was absent, the tool
was unauthenticated, the tool was rate-limited, or the tool returned output that
could not be parsed. Those three stops observed something and this one observed
nothing, so a report that read the same would tell an operator the record is
wrong when the record may be perfectly correct. **Behaviour does not branch on
the cause; only the report does.** All four take the same stop and the same
resume path.

**Clearing the `Draft PR` row is not a resume path here.** That belongs to
`pr_missing`, and reusing it for a `skipped` would erase a probably-true record
to manufacture a `no_record` reading on the next run.

**Every one of these paths reports.** A gate stop's condition is the status
and, for `skipped`, its cause. Nothing landed, because the gate is evaluated
ahead of the first read and therefore ahead of every write. The resume path is
the one the table above gives.

**Read the authenticated account from the live session, at call time.** The
sweep excludes the replies it posted itself, and the author half of that rule
compares against the account this run authenticated as, which is the parse's
`self_login` input. Read that account from the live authenticated session at
the moment of the call. Never take it from configuration, from a project
setting, or from a value remembered earlier in the run. This is the same
freshness the author-association field below requires, and it needs saying
because nothing else says how the orchestrator learns its own login, so nothing
today guarantees the value arrives correct.

**Two reads, and only two**, both `gh api` reads. Read **every review thread
whose resolved flag is false** and **every pull-request conversation comment**.
Do not read review summary bodies. **Paginate both to exhaustion**: follow the
cursor until the surface reports no further page, rather than taking a first
page and stopping. Request the **`authorAssociation`** field explicitly on both
reads. No shipped query asks for it, so the author-association filter has no
input unless this read supplies it. **No comment text reaches a shell argument
in either direction**: a read passes its query by file or by structured
argument, and a write passes its body by file path.

**Pipe the observation straight into the runner.** The reads' output reaches
`sweep-pr-feedback` on stdin, `gh ... | resolved_python -m speckit_pro_runner`,
with the request envelope wrapped around the read rather than around a file.
**No unredacted body is written to disk at any point**, which is a stronger
control than ignoring such a file would be. Where a byproduct file is
unavoidable it goes under `specs/<feature>/.process/feedback-sweep/` and
nowhere else, the directory the next section describes, which is where the
reply bodies already live.

**The two reads are one observation, taken all or nothing.** It succeeds only
when both surfaces have been read to exhaustion. Three failures fall under the
rule: one surface readable and the other not, a page failing partway through
pagination, and output that cannot be parsed. **A failed observation is
discarded rather than swept.** The partial data does not reach classification.
The run writes zero log rows, posts zero replies, takes zero commits, and
stops. Nothing needs unwinding, because every read precedes every write.

**The mid-read failure report is not the gate stop, and must not read like
it.** It draws on the same four causes the gate's `skipped` draws on: the tool
was absent, the tool was unauthenticated, the tool was rate-limited, or the tool
returned output that could not be parsed. So the report **also names that
reading had begun** and **which surface failed**, because an operator who cannot
tell a gate failure from a mid-read failure cannot tell whether the pull request
was ever reachable. Nothing landed, for the same reason nothing landed at the
gate: every read precedes every write. The resume path is the same as the
gate's `skipped`, fix the tool and re-run, and needs no repair step first,
because the observation is retaken fresh on every invocation.

**Dispatch one classifier per candidate, and read no body.** The parse returns
`candidates` and `excluded`. A candidate record carries the comment id, the
surface, the author, the association, the truncation flag, and the export
metadata, and it carries **no body**. Iterate `candidates` and nothing else;
no path enumerates the observation directly. For each candidate whose export
kind is not `empty`, dispatch **exactly one `sweep-classifier`**, handed the
sanitized delimited block the piped call already returned for that candidate,
the closed class vocabulary, the three-file target set, and nothing else. A
candidate whose export kind is `empty` is never dispatched: that form carries
no objections and takes `no action` from the parse alone.

**The orchestrator reads no comment body on any path.** It is a conduit for a
block. It hands each block to the classifier unchanged, and for an amended
item hands that same block to the analysts. It keeps a shell and could run the
read for itself, so the control is that a body is never handed to it, which is
construction rather than enforcement, and saying so is more honest than
implying a guarantee that does not hold.

What comes back is the structured record `contracts/sweep-classifier-output.md`
fixes: the echoed comment id, the class, the target, and a bounded reason.
Consume those and nothing else. The reason is reviewer-derived text a model
rewrote, so pass it through the redaction surface's `log_row` leg **before** it
reaches a cell, a reply, or the run report, and carry the string that leg
returns rather than the orchestrator's own copy of what the classifier said. A
record carrying a class outside the set, a target outside the three artifacts,
or a missing field is **malformed**: stop the run naming that comment id. Do
not coerce it onto a class, and do not re-prompt.
A classifier that cannot answer in its own vocabulary is a defect, not a fifth
outcome.

**The dispatch lives here, not in the routing table.** It emits no category
tag, it produces no `Unresolved for consensus` item, and it never consults
`consensus-protocol.md`'s Category-Routed Dispatch table or the three
phase-specific flows under it. That is what leaves Clarify, Checklist, and
Analyze exactly as they were.

**The vocabulary the dispatch hands over.** The closed class set is `amended`,
`answered`, `deferred`, and `no action`, and the classifier returns exactly
one of the four. The **comment** is the unit, so a recognized export carrying
several distinct objections still yields one class, one log row, and one
reply. Recognition never forces a class; the empty-export form above is the
one exception. The rules for choosing among the four, including the tie-break
for a comment whose objections pull different ways and the naming of every
non-dominant objection, are stated once in the classifier's own definition.
This reference carries the dispatch, the payload, and the record's shape, and
points at that definition for the rules, so the two cannot drift.

**A target outside the three artifacts takes `deferred` at classification.**
That is rule 1, and it is the disposition half of a pair. A comment whose
requested change lies outside `spec.md`, `plan.md`, and `tasks.md` in the
feature directory is declined, so its class is `deferred` and its bounded
reason **names the refused target**, which is what carries that name into the
disposition cell and into the reply. The refused path travels in the reason
and never in the record's `target` field, which the malformed-record rule
above confines to the three artifacts. Word the disposition and the reply as
**recorded and not acted on**, and let neither **imply future action**: the
class name reads like a queue, and the request is declined rather than
scheduled. The rule for choosing among the four classes stays in the
classifier's own definition; what this sequence fixes is what a `deferred`
reached this way has to carry.

**Rule 1 is disposition and rule 2, at the write point below, is the
enforcement boundary.** They are not the same rule and neither substitutes for
the other. Rule 1 alone would be prose a mis-routed item walks past. Rule 2
alone would turn an ordinary out-of-scope request into a stopped run, when
declining it in a reply is the whole of the correct response.

**The recognized-export payload.** For a recognized comment the payload is two
parts standing side by side: the helper's export record, carrying the template
id, the kind, and the anchors, and the block, which is the body with every
line the parse named in `matched_lines` replaced in place by
`[registered export lead removed]`. The export record stands **beside** the
block, never inside it. The remainder is delimited and labelled as
reviewer-supplied data, never concatenated into the prompt as instruction. A
registry entry that only tags the comment while the raw body still reaches the
agent does not satisfy this: the imperative addressed to a coding agent would
still be sitting in the prompt, with a label attached that nothing acts on.

**The removal is the redaction surface's work, not this reference's.** Hand
the surface the parse's `matched_lines` for that comment and forward the block
it returns **unchanged**. Delimiting is the strongest layer available inside a
prompt and removal is defence in depth. Both are model-layer controls, and
nothing deterministic stands behind them on the forward path, so neither is a
reason to relax the author-association filter. If cost ever forces one of the
two out, removal goes and delimiting stays.

**The work set shrinks or holds, and never grows.** A run's **work set** is
the comments that pass the trust filter, are absent from the Feedback Sweep
Log, and are not excluded as the sweep's own replies. Every run either shrinks
that set or leaves it unchanged. **No run may grow it.** That is what makes
the loop terminate, and any future rule that writes to either comment surface
has to be tested against it, because a rule that adds an unexcluded comment
breaks convergence however reasonable it looks on its own.

One path does not shrink the set. A comment whose consensus round returns a
human-review outcome takes no class and writes no row, so it is in the set
again on the next run and stops that run too. The set does not grow, so this
is not divergence, but re-running without operator action reproduces the same
stop. That path is bounded by a human rather than by a counter, and **no
attempt counter is introduced**: a per-comment counter would need the
state-file mirror the log rules forbid.

#### Phase 7 Setup: Consensus for an Amended Comment

**Only `amended` routes into consensus.** `answered`, `deferred`, and `no
action` never invoke it. Those three are complete at classification, and a
consensus round on any of them would spend four dispatches confirming a
disposition already reached.

**The sweep runs its own consensus.** Per amended item, dispatch **three
`sweep-analyst`s**, the perspective (codebase, spec-context, domain) given
**in the prompt rather than by role**, then **one more `sweep-analyst`** in a
synthesis prompt. Four calls per item, all to the same definition. **Await
all three before the synthesis call**, which reasons over the three answers
together, and **apply the one structured edit it returns** by the amendment
path below.

**Synthesis is not `consensus-synthesizer`.** That agent declares no `tools:`
allowlist, so it inherits a shell, web fetch, web search, and every installed
MCP server. Routing sanitized reviewer text into it would reopen, one hop
downstream, the exposure the classifier dispatch above exists to close.
`sweep-analyst` carries a closed read-only allowlist instead, which is also
why **the domain perspective runs without web access**: it reasons from the
repository and the handed block, never from the network.

**What stays untouched is the routing table, not the file that holds it.** The
sweep emits no category-tagged `Unresolved for consensus` item, so the routing
table and the three phase-specific flows under it are never reached and
Clarify, Checklist, and Analyze keep the shared analysts and those flows
unchanged. This slice does edit `consensus-protocol.md`, to add the `Sweep`
row type and the note that its rows count toward the escape-rate metric, and
those two are the only edits this feature makes to that file, so say routing
table untouched and never say that file untouched.

**When consensus does not answer, the item goes to human review.** Three ways
lead there: all three analysts disagreeing after Round 2, a Round-1 escape
whose Round 2 still cannot resolve, and an analyst that fails its single
retry. All three land on one behavior, and only the report names which
occurred.

**No edit, no class, no sweep row.** No artifact is edited and the comment is
given no class, because `amended` would assert an edit nobody resolved and the
other three would assert a disposition nobody reached. Writing no Feedback
Sweep Log row is the load-bearing part: the skip key is that log's comment-id
column and nothing else, so the absent row is what makes the comment a
candidate again once a human has resolved it. A row here would record the
sweep's own failure as the comment's disposition and make it permanent.

**It surfaces as one Consensus Resolution Log row instead**, `Type` `Sweep`,
its item cell naming the comment id, and that row **counts** toward the
Round-2 escape-rate metric. That log feeds no skip key, so a row there costs
no idempotency.

**It stops the run whether or not anything was amended.** A run whose only
unresolved item took no class would otherwise read as nothing to act on and
walk into task work. When other items amended in the same run, the re-review
stop and this one are the same stop and one report, not two.

**Other items in the batch still complete.** Items that resolved are edited,
committed, recorded, and replied to normally, and the run stops after that.

#### Phase 7 Setup: Amending, Committing, and Pushing

**One commit per amendment, never one run-wide commit.** A log row names its
commit, an `amended` reply names the amending commit, and the re-review stop
reports a commit range. None of the three survives collapsing every amendment
into a single blob.

**Each amendment commit stages exactly the one artifact path it amended, never
a directory**, so no stray file rides along on an amendment.

**The subject is fixed in shape and carries no body:**

```text
docs(<feature-id>): amend <artifact> for <comment-id>
```

The scope is the feature's roadmap id in lowercase, `<artifact>` is one of the
three artifacts, and `<comment-id>` is the observation's id for the comment
being amended. Every slot is an id or an enum, so no byte from a comment or
from a resolution reaches `git log`, and the subject is **not a redaction
leg**. The shape also satisfies the release-readiness title regex.

**The hazard to watch: this is a Phase 7 setup step, and Phase 7 is the one
phase whose existing commit path uses `git add -A`.** An amendment commit that
inherited that pattern would stage the whole worktree and defeat the
edit-surface allowlist at the last step. Name the one path.

**What the synthesis returns is a record, not a patch.** An analyst answers
with `{file, anchor, replacement}` and nothing else: never a diff, never a
patch, and never prose the orchestrator retypes into the artifact. `file` is
one of the three allowed names, and `replacement` sits inside the contract's
cap. An edit whose `file` falls outside those three names, or whose shape is
not that record, **stops the run naming the comment id**, the same way a
malformed classifier record does.

**The order of the three steps is fixed: allowlist check, redaction, write.**
Check the resolved target first, pass `replacement` through the redaction
surface's `amendment` leg second, write what the surface returned third, then
stage that one path, commit, and push. The order is not a preference.
Redacting after the write leaves reviewer bytes in a commit, and checking the
target after the write is not a check.

**The write point checks the resolved target before any amendment write.** It
is a named surface of the one registered helper operation, never a second
registered operation.

**A refusal is a verdict, not a diagnostic.** `allowed: false` is a successful
read of that surface rather than an error from it: the surface answers, and
the stop belongs to the orchestrator. The answer carries a `reason` that is
either null or one of `outside_set`, `symlink_target`, and `symlink_parent`.

**A refused target stops the run.** Its condition names the **refused target
path** and the **comment id it came from**, and its resume path is to fix the
classification and re-run.

**Reaching this check means classification already failed**, so it is a defect
report and not a routine path. That is why it stops rather than downgrading
the item quietly: an out-of-scope request is meant to be declined at
classification, and one that reached the write instead is worth an operator's
attention.

**The amendment leg runs between the check and the write.** Once consensus has
resolved the edit and the target check has passed, the text the edit
**introduces**, meaning the replacement or the inserted lines, goes through
the redaction surface's `amendment` leg. Never the file around it, and never a
diff read back off disk. The orchestrator then writes back **exactly what the
leg returned**, stages the one artifact path, commits, and pushes. No staged
path list is read back afterwards: single-path staging and the `git add -A`
hazard named above stay the controls on what an amendment commit stages.

**Cut each line for transport at the first character boundary at or past byte
8193.** The surface answers a line longer than 8192 bytes with the whole-line
placeholder whatever lies past that boundary, so sending the tail buys
nothing. Cutting there is outcome-equivalent, keeps every string the call
carries under the runner's 32 KiB limit, and **never splits a line**, because
the cut falls on a character boundary and one line in stays one line out.

**The push is part of the amendment step, not a step after it.** An amendment
is not finished until its commit is on the remote.

**A commit that succeeded whose push failed stops the run immediately, before
that amendment's bookkeeping commit**, naming the unpushed commit's sha and
the comment id. Ordering does the work: the bookkeeping commit already comes
after the amendment's own commit, so stopping between them writes no log row,
and because replies wait on bookkeeping commits landing, it posts no reply.

**The local commit stands and is not unwound.** The edit is correct work that
consensus resolved, and discarding it would throw away a completed round to
tidy a state that already recovers on its own. With no row written, the skip
key does not see the comment, so it is a candidate again on the next run.

**A bookkeeping commit whose push fails stops the run the same way**, and
differs in one consequence. Its row is already in the local workflow file, and
the sweep reads that file locally, so the skip key **does** see the comment.
The reply is what would otherwise be lost, and reply reconciliation against
the pull request is what recovers it.

**No automatic retry on either push.** Retrying inside the run would multiply
the window that the per-amendment cadence exists to bound.

**Log writes ride a separate bookkeeping commit and are never folded into an
amendment commit.** The ordering is forced rather than stylistic: a row that
names its commit cannot exist until that commit's sha does.

**The bookkeeping commit stages the workflow file path alone, never the
directory, and takes a `chore:` subject.**

**The trigger is rows, not handled comments.** A run takes a bookkeeping
commit when it wrote at least one row to **either** log, and takes none when
it wrote none. Three consequences follow:

- A run with zero amendments but at least one handled comment takes exactly
  one, carrying every `answered`, `deferred`, and `no action` row.
- A run that handles no comment but must write Consensus Resolution Log rows
  also takes exactly one, carrying every such row.
- A run that wrote no row to either log takes none. An empty commit there
  would record nothing.

**One bookkeeping commit per amendment, not per run**, which bounds the window
in which an amendment is pushed but unrecorded to a single item.

#### Phase 7 Setup: The Redaction Surface's Outbound Call Points

**The surface has four legs and the set is closed at four**: `amendment`,
`log_row`, and `reply` outbound, and `analyst_payload` inbound. Anything
outside the four returns `invalid_input`. A fifth leg is code this feature
does not budget for.

**The `log_row` leg runs over every cell the sweep fills with prose** rather
than with an id, an enum, a sha, or a count: the Feedback Sweep Log
`Disposition` cell, the disposition text of the Consensus Resolution Log rows
the sweep writes, and those rows' item cell, which names the comment id and
then summarizes the item in prose the way every shipped row does. **One call
per cell**, so an amended item makes three calls on this leg, a human-review
item two, and any other class one. The classifier's bounded reason, which is
what becomes the disposition, is capped at 512 bytes and carries neither a
pipe nor a newline, because the readers of these tables split cells on the
bare pipe.

**The `log_row` call comes before the pipe and newline escaping, never
after.** The placeholder the surface writes contains neither character, so
escaping never splits a placeholder and `CRL #` stays in its column.

**Capture each `log_row` response at the call, before escaping.** Captured
after escaping, the identity assertion downstream compares the wrong pair and
passes on a run report the orchestrator built from its own pre-call copy. The
order is: call the leg, capture what it returned, then escape the captured
string on its way into the cell.

**The `reply` leg runs over the filled reply body, marker included**, before
that body is written to the file the reply write passes by path. The marker
stands alone on line 1, no rule's trigger appears on that line, and neither
line-granularity rule reaches a line ahead of its own: the bound replaces only
the line it measured, and the key-header span runs forward from its own header
line. The self-reply anchor therefore survives, and an over-bound disposition
costs line 2 onward and never the marker.

**Never the matched line**, an excerpt of it, a redacted or truncated copy, or
any encoded form, whether in the report, a log row, a reply, or the surface's
own response. The report carries an event exactly as the builder above names
it, and nothing more. The disposition it carries per comment is the `log_row`
response for that comment's `Disposition` cell, before escaping, never the
orchestrator's copy from before the call.

**Redaction never refuses a write and never discards a row.** A run with no
amendment batches every row it wrote into one bookkeeping commit, so a refused
commit would discard them all, and the next run would regenerate the same
disposition and refuse again: a livelock on ordinary reviewer input.

**A run with any event stops once every write has landed**, after the last
push and the last reply, with resume path re-run. The next run finds the rows
and the replies already in place, fires no event, and proceeds.

#### Phase 7 Setup: The Reply Templates

**Exactly one reply per handled comment**, posted after a run's bookkeeping
commits have all landed. **Every reply names its class.** Only an `amended`
reply names an artifact, a section, and a commit: requiring those three of all
four classes would leave three of the four templates unsatisfiable, because
`answered`, `deferred`, and `no action` amend nothing.

**One fixed template per class, in plain public-readable English**, fixed in
shape so a reviewer reading two replies on one pull request can tell the
classes apart at a glance.

**Every template opens with an HTML comment whose prefix is the same fixed
string in every reply**, `<!-- speckit-pro:feedback-sweep`, followed by the
answered comment's id and the closing `-->`. It renders as nothing, and it is
what the self-reply exclusion anchors on. A marker rather than a visible
sentence, because a visible sentence is exactly what a reviewer quotes back
when they disagree.

**The marker is the whole of line 1, alone, and the disposition starts on line
2.** Nothing else shares that line, which is what keeps the per-line redaction
rules off it, as the reply leg above already relies on.

**One more fixed-shape line is the last line of every template**, present only
when the parse reported the comment `truncated` or its analyst-payload report
carries `spans_withheld` above zero:

```text
Body truncated at 8192 bytes; N spans withheld.
```

`N` is that count, and nothing else appears in the line. This is the channel
that tells a reviewer their fence or their tail was never read. The pull
request is where a reviewer learns what happened to their comment, and the
disposition cell lives in a file they need not open.

#### Phase 7 Setup: Where a Reply Is Written, and When

**Two write paths, one per surface.** A reply to a review-thread comment posts
**into its thread**. The pull-request conversation has no threading, so a
reply there is a **new top-level comment that names the comment it answers**.

**Every reply body is passed by file path, never inline**, on both paths.

**Replies post once, at the end of the run, after every bookkeeping commit
this run takes has landed.** No reply is posted before that point. Two orders
are defensible and only one may be written down, so this is the one: a reply
asserts that the record behind it is durable. The rule also makes the composed
interrupt case exact rather than ambiguous. A run interrupted after two rows
were written, with one amendment commit local and unpushed, has posted
**zero** replies.

**Which stops post replies is named rather than inferred.** The re-review
stop, the human-review stop, and the post-publication redaction stop all occur
**after** the reply point, so a run that reaches any of them has already
posted every reply it owes. **Every other stop aborts before the reply point
and posts none**: an invalid authenticated account, a corroboration failure, a
failed observation, an unreadable log row, a refused edit target, and a failed
push. Never write a blanket rule that a stopping run first posts what it owes,
which would contradict all six.

**The sweep never resolves a review thread.** Not on any class, not on any
path, and not after a reply. Resolution is the reviewer's, and a swept thread
stays open until they close it.

#### Phase 7 Setup: Reply Reconciliation

**Replies are reconciled against the pull request, not assumed from the log.**
A comment is owed a reply when three things hold together: it is **present in
this run's observation**, it has a log row, and it carries no sweep reply
answering it.

**The observation qualifier is load-bearing.** Keying on log rows alone would
post a second reply into a thread someone had deliberately resolved, which
turns a recovery rule into a duplicate-reply generator.

**The marker carries the answered comment's id** after its unchanged fixed
prefix, inside the same HTML comment, so a thread carrying more than one
comment still says which one a reply answered. Matching the prefix alone would
find a reply and lose the question.

**A failed reply is reported and does not by itself stop the run.** It appears
in the run report naming the comment id and the surface. The asymmetry with a
failed observation is deliberate: an observation that failed means the work
never happened, while a reply that failed means the work landed and only the
notification did not.

#### Phase 7 Setup: Stop or Proceed

**One or more `amended`: stop for re-review before any task work.** Its
what-landed part names the comments swept, the amendments made, and the commit
range, and the report **states that the draft artifact pages regenerate once
slice 2 lands**.

**No `amended` but at least one comment handled: write the records, post the
replies, and proceed directly into task execution**, without stopping. Nothing
was amended, so there is nothing to re-review.

**No comment handled at all: no rows, no replies, no bookkeeping commit,
proceed.** This case is stated apart from the one above so that the one above
cannot be read as requiring an empty commit on a pull request that carried no
comments.

**Any redaction event, on any leg: stop once every commit is pushed and every
reply is posted.** The resume path is re-run. Where nothing was amended, this
stop replaces the proceed at that same point. Where the re-review stop or the
human-review stop also holds, it is the same stop and one report.

The regeneration sentence is an interface slice 2 replaces. Until it does, it
is the only thing telling a reviewer why the pages they are looking at are
older than the amendments beside them.

#### Phase 7 Setup: The Sweep's Byproduct Directory Ignores Itself

The pull-request feedback sweep writes the files it needs for its own transport
under `specs/<feature>/.process/feedback-sweep/`. **The first write into that
directory, before any byproduct, is a `.gitignore` inside it whose whole content
is a single `*` line.** Create the directory and write that ignore file in one
step. A byproduct that lands first has already been exposed, so the order is
part of the rule rather than a preference.

**Every file the sweep writes for its own transport goes there and nowhere
else**: the helper request the runner reads on stdin, each reply body file the
reply write passes by path, the captured commands, and any scratch the run
needs. **The request cannot be redacted instead.** The parse filters over the
comment bodies, so that file has to carry them, and keeping the directory
ignored is what stops Phase 7's `git add -A` from staging a request holding
every observed body.

Git honors that file in whatever repository the worktree belongs to, and `*`
matches the ignore file itself as well as every byproduct beside it, so Phase
7's `git add -A` can stage neither. The control is by construction rather than
by care: it holds in a consumer repository whose root ignore file this project
never wrote and cannot amend.

This repository's own root `.gitignore` carries
`specs/*/.process/feedback-sweep/`, so the directory is ignored here even before
the sweep has written into it. That entry is committed, so a fresh clone carries
it. It covers this repository only, which is the whole reason the self-ignore
write exists.

**The sweep removes the directory before it proceeds into task work or stops,
on every path.** Removal is neither conditional on the run having succeeded
nor deferred to a later phase. The spec-index generator scans the worktree
rather than the index, so a live byproduct left behind would contaminate a
regeneration even though nothing staged it. **The run report names the
directory as removed.**

#### Phase 7 Setup: Open the Implementation-Notes Record

Run this before Step 1, so the record exists before the first task is
dispatched. It is not deferred to the first append: a phase interrupted before
any task completes, and a spec carrying no implementation tasks at all, must
both still leave a header-only record behind.

The record is one file per spec, at
`specs/<feature>/.process/implementation-notes.md`, alongside the rest of the
feature's autopilot exhaust — the same `specs/<feature>/` this phase reads
tasks.md from in Step 1. Its first line is the header, and the header is
written exactly once:

```text
# Implementation Notes: <SPEC_ID>
```

- **Create if absent**: when the record is not there, create its `.process/`
  directory too if that directory is also absent, then create the file with the
  header as its only content. An absent directory is a thing to create, never a
  failure to report.
- **Never truncate**: when the record is already there, leave every existing
  byte as found and append after the existing content. Do not write a second
  header. This is the resumed-phase case, and the entries already in the file
  are the whole point of the record.
- **Check the record's own path**, in the working copy this run executes in,
  never a state file, an index, or anything carried over from the session that
  wrote the record. A resume in a fresh session then behaves exactly like a
  resume in the session that started the run.
- **Fail-open**: if creation fails, record a gap in
  `docs/ai/specs/.process/<SPEC_ID>-workflow.md` naming this setup step and the
  operation that failed, do not retry, and carry on into Step 1. The task and
  phase outcomes are exactly what they would have been had the write succeeded.

#### Step 1: Parse tasks.md

```text
1. Read tasks.md from specs/<feature>/
2. Parse phase groups (## Phase 1: Setup, ## Phase 2: ..., etc.)
3. Within each phase group:
   - Identify [P] (parallel) vs sequential tasks
   - Classify: test-only, implementation, verification
4. Build ordered task list respecting phase dependencies
```

#### Step 2: Load TDD Protocol

```text
Read references/tdd-protocol.md → store as TDD_PROTOCOL
```

This protocol is injected into every implementation agent's
prompt, ensuring identical RED→GREEN→REFACTOR discipline
regardless of which agent executes the task.

#### Step 3: Task-Level Execution Loop (with `[P]` parallel partitioning)

This is **Use site 3** in the [Agent Teams use-site map](./agent-teams-integration.md).
Partition each phase group's tasks into RUNS (parallel for consecutive
`[P]`-tagged tasks; singleton for non-`[P]`). Dispatch each parallel
run in ONE assistant message via background subagents (or as an Agent
Team when `AGENT_TEAMS_AVAILABLE=true`). Sequential runs dispatch one
foreground agent at a time. Safety net: after every parallel run, run
TYPECHECK + UNIT_TEST; on regression, fall back to serial re-run.

```text
Initialize COMPLETED_TASKS = {}

For each phase group in tasks.md:
  TaskUpdate: "<Phase 7: group name>" → in_progress

  # Step 3a: Partition tasks into RUNS
  RUNS = []
  current_parallel_run = []
  For each task in the group (in order):
    if task has [P] marker AND routes to the same agent type as the
       previous [P] task in current_parallel_run:
      current_parallel_run.append(task)
    else:
      if current_parallel_run is non-empty:
        RUNS.append(("parallel", current_parallel_run))
        current_parallel_run = []
      RUNS.append(("singleton", task))
  if current_parallel_run is non-empty:
    RUNS.append(("parallel", current_parallel_run))

  # Step 3b: Execute each RUN
  For each (kind, tasks_in_run) in RUNS:
    if kind == "parallel" and len(tasks_in_run) >= 2:
      if AGENT_TEAMS_AVAILABLE:
        # Path A: spawn an Agent Team for this parallel run
        Create an agent team with len(tasks_in_run) teammates
        (max 5 per Anthropic's 3-5 sweet spot — partition into
        multiple teams if the run is larger). Use Sonnet teammates.
        Each teammate claims one [P] task and runs it with the
        Agent prompt template below, plus one Teams-only line:
        each teammate MUST send its complete
        `## Task Result: <TASK_ID>` block to the lead when its
        task completes. The team's shared mailbox
        lets teammates coordinate ("I'm changing the auth
        interface, heads up").
        Append each teammate's entry as that report message
        arrives, without waiting for the rest of the run, and
        never on a bare idle or liveness notification.
        Only then wait for all teammates to complete.
        Clean up the team before the next run.
      else:
        # Path B: spawn all [P] tasks in ONE message, background
        For each task in tasks_in_run:
          Agent(
            subagent_type: <routed agent>,
            run_in_background: true,
            isolation: "worktree",
            description: "SPEC-XXX <task-id> [P] <brief>",
            prompt: <task prompt — see Step 3c>
          )
        # All N tasks dispatched in ONE assistant message
        Wait for ALL to complete.
        Each background subagent's completion arrives on its own
        turn; append that task's entry then, without waiting for
        the rest of the run.

      # Safety net for either path: verify no regression
      # (every arrived attempt's entry is already appended by now)
      Run Command("<TYPECHECK> && <UNIT_TEST>") in the orchestrator.
      If FAIL:
        Log regression to workflow file.
        Re-run the tasks SERIALLY (one foreground agent each):
        for task in tasks_in_run:
          Agent(subagent_type: <routed agent>, ..., prompt: ...)
          On that result, append a further entry under the same
          task ID; the earlier entry stays exactly as written.
        After serial re-run, run TYPECHECK + UNIT_TEST again.
        If still failing, surface to user.

    else:
      # Singleton run or single-task "parallel" run
      ROUTE to agent for tasks_in_run[0]:
        a. PROJECT_IMPLEMENTATION_AGENT — task description matches
           keywords from the detected agent (Step 0.9)
        b. implement-executor — if test-only task (keywords:
           "test", "contract test", "unit test", "integration")
        c. domain-researcher — if research task (keywords:
           "research", "investigate", "explore API")
        d. orchestrator-direct — if verification-only (keywords:
           "verify", "run", "check", "build", "lint")
        e. implement-executor — default fallback

      All five branches append an entry; c and d emit no
      task-result block, so their entries record None.

      Foreground dispatch: Agent(..., prompt: ...)
      Wait for result.
      Append this task's entry on the turn that result arrives,
      before the next dispatch.

  # Step 3c: Agent prompt template (used for parallel + singleton)
  Agent(
    subagent_type: "<routed agent>",
    isolation: "worktree" if part of a [P] parallel run else omitted,
    run_in_background: true if part of a [P] parallel run else omitted,
    description: "SPEC-XXX <task-id> <brief>",
    prompt: """
      <tdd_protocol>
      <TDD_PROTOCOL contents>
      </tdd_protocol>

      PROJECT_COMMANDS:
        BUILD: <cmd>  TYPECHECK: <cmd>  LINT: <cmd>
        UNIT_TEST: <cmd>  INTEGRATION_TEST: <cmd>
        SINGLE_FILE_TEST: <cmd>
        SINGLE_FILE_INTEGRATION: <cmd>

      <if PRESET_CONVENTIONS>
      PRESET_CONVENTIONS: ...
      </if>

      COMPLETED_TASKS:
        <structured list of prior task results>

      Your task:
      ---
      <exact task description from tasks.md>
      ---
    """
  )

  # Step 3d: ACCUMULATE context
  COMPLETED_TASKS[T00X] = {
    files: [paths created/modified],
    tests: N,
    status: "GREEN" | "RED" | "error"
  }

  Phase-group verification (orchestrator-direct):
    Command(BUILD) && Command(TYPECHECK) && Command(LINT) &&
    Command(UNIT_TEST)
    If any fail → dispatch fix agent, re-run.

  TaskUpdate: "<Phase 7: group name>" → completed
```

#### Append Contract: One Entry Per Dispatched Attempt

Every attempt Step 3 dispatched gets one entry in the record the Phase 7 setup
step opened, appended after everything already in the file:

```text
### <TASK_ID>

**Deviations/Edge cases/Surprises:** <reported text, or None>
```

`<TASK_ID>` is the task's ID exactly as `tasks.md` writes it, and one blank line
separates the entry from the content before it.

**One entry per task, even when several tasks share one dispatch.** Batching
related tasks into a single worker is a sensible dispatch choice and does not
change the record: each task named in the task list gets its own entry under its
own ID. Never write a compound heading such as `### T007+T008+T009`, because a
reader cannot recover three task IDs from one heading. Split the worker's
reported text across those entries, or repeat the shared text under each.

**Per-arrival cadence, one rule for every dispatch shape.** Append on the turn
that attempt's own result reaches the orchestrator, before dispatching further
work. A member of a parallel run does not wait for the rest of its run: the
platform delivers each worker's completion individually, so the entry is written
when that worker reports, not when the run reaches the TYPECHECK and UNIT_TEST
safety net. Never batched to phase end, and never deferred to a run boundary.
Where several results do reach the orchestrator on the same turn, each still
gets its own entry on that turn, in the order they are presented.

**Never append on a bare idle or liveness signal.** A worker that stops without
delivering a task summary has produced no result, which is a cue to request the
summary rather than to write an entry. Appending on it writes an empty entry,
and double-counts the attempt once the worker is woken and finishes.

**Additive only.** No entry already written is rewritten, reordered, or removed,
and the record is never read back to update a counter or to find a previous
entry. The serial re-run after a parallel regression appends a further entry
under the same task ID and leaves the earlier one exactly as written; two
entries sharing a task ID are correct history, not a defect. Document order is
append order, so position is the record's only ordering signal, and where two
entries share a task ID the earlier-positioned one is the earlier attempt.

**Fail-open.** A failure to append is recorded as a gap in
`docs/ai/specs/.process/<SPEC_ID>-workflow.md`, never in the
implementation-notes record that just failed, and the gap names the attempt and
the operation that failed so a reader can tell which write was lost. The write
is not retried: one attempt, then the gap. The fallback is exactly one level
deep, so when the workflow file is itself the unwritable path, surface that
second failure in the run's own output and carry on, with no third destination
and no recursion. The blast radius is one entry: every other attempt in the same
run is still appended as its own result arrives, and the next dispatch still
happens. A reporting-content problem is not a write failure. A missing or
unreadable field produces a `None` entry, not a gap.

#### Step 4: Final Verification

After all phase groups complete:

```text
Run FULL_VERIFY:
  Command(BUILD) && Command(TYPECHECK) && Command(LINT) &&
  Command(UNIT_TEST) && Command(INTEGRATION_TEST)
```

#### Agent Routing Table

| Task Type | Agent | TDD Protocol? |
|-----------|-------|---------------|
| Contract/unit/integration tests | `speckit-pro:implement-executor` | Yes |
| Implementation needing project patterns | PROJECT_IMPLEMENTATION_AGENT | Yes |
| Research / API investigation | `speckit-pro:domain-researcher` | No |
| Verification (build, lint, typecheck) | orchestrator-direct (command tool) | No |

Every agent receiving implementation work gets the TDD protocol
injected. Agent selection is about DOMAIN EXPERTISE — the
implement-executor is a TDD specialist, the project agent brings
domain knowledge. Both follow identical discipline.

**Three append call sites in the routing, not one.** The routing branch decides
what an entry carries, which is a different axis from the dispatch shape that
decides when it is written:

| Route | Task-result block? | Entry value |
|-------|--------------------|-------------|
| `implement-executor`, project agent | Yes | Reported text, or `None` |
| `domain-researcher` research | No | `None` |
| orchestrator-direct verification | No | `None` |

Appending only on the executor branch leaves research and verification attempts
silently missing from the record.

**The literal `None`** is the single value for every nothing-to-report case: the
executor reported `None`, the executor omitted the field, the field cannot be
read out of the summary it returned, or the route emits no task-result block at
all. No distinct marker and no route field, because a second value would make
the record unreadable as a count of what was reported the moment a run contains
one research task.

**Gate:** G7 — full verification suite
(build + typecheck + lint + unit tests + integration tests)

**Commit:**
`git add -A && git commit -m "feat(SPEC-XXX): implement phase"`

**After G7 passes:** Run Integration/E2E Test Verification,
then execute PR Creation Protocol (see below).

### Phase-Gate: Spec-MOC Navigation Regeneration

At **every phase boundary** — for all seven phases — regenerate the
spec map navigation zones and fold any change into that phase's
existing checkpoint commit. This runs as an **idempotent** step
**immediately before** each phase's **Commit:** step (above), so the
rebuilt maps are swept into the same `git add … && git commit`. A
boundary that changes nothing contributes nothing.

**Why before the commit:** the existing per-phase `git add <enumerated
trio> && git commit` (phases 1–6) / `git add -A && git commit` (phase 7)
is what folds the rebuilt maps into the one checkpoint commit. The
regenerated maps live under `specs/`, which the enumeration covers.
Running the
rebuild *after* the commit would force a second commit on every
map-affecting boundary — that is the failure this ordering avoids.

**Step (run at each boundary, before the Commit step):**

```text
# Write mode (NO --check): regenerate over the autopilot's target repo.
# Pass "$PWD" explicitly — do NOT rely on the generator's default
# REPO_ROOT. In a cached-plugin run the default resolves to the plugin
# cache's parent, not the user's project. Use the explicit target repository
# path for installed-cache runs.
runner helper generate-spec-index-write with repo root "$PWD" and mode apply
```

**Act on the result:**

- **Exit 2 (error)** → a map is malformed/unbalanced or a PRS manifest
  is unreadable. **Surface the actionable stderr line and STOP.** Do
  NOT commit a broken regen and do NOT advance the phase.
- **Exit 0 (clean)** → the generator wrote any stale maps and returned
  success. **The commit decision is diff-driven, not exit-code-driven**
  (write mode returns `0` whether or not it changed a file; the stale
  `exit 1` is `--check`-only and never reached here). Inspect the
  working tree:
  - `git diff` (plus `git status` for newly-injected zones) is
    **empty** → nothing was regenerated. This is the idempotent no-op:
    contribute nothing, proceed to the phase's normal Commit step.
  - `git diff` is **non-empty** and the rebuild rides **alongside**
    other staged phase work → it is folded into that phase's existing
    checkpoint commit (`feat(SPEC-XXX): complete <phase> phase` /
    `feat(SPEC-XXX): implement phase`). No separate commit is made.
  - `git diff` is **non-empty** and the regenerated maps are the
    **only** staged change → make a standalone commit with this fixed,
    public-readable subject:

    ```text
    docs(speckit-pro): regenerate spec-MOC navigation zones
    ```

This subject is a fixed constant (it is NOT computed per run): `docs:`
because regenerating generated documentation zones is a docs-scope
change and does not trigger a release-please version bump. The
regeneration is a pure function of committed files, so re-running it on
an unchanged tree yields a zero-byte diff and no commit — exactly one
rebuild contribution to the checkpoint commit on a map-affecting
boundary, and none on a no-op boundary.

## Full Integration / E2E Suite Verification

Integration tests are created DURING the Implement phase by
implementation agents (mandatory, not optional). This
post-implementation step runs the FULL suite to catch
regressions from other specs.

1. Verify spec-specific tests exist:
   `Glob("tests/integration/*<spec-name>*")`
2. If missing → spawn implement-executor to create them
   (the Implement phase failed to meet this requirement)
3. Run the FULL integration suite (all specs, not just new):
   `Command("<INTEGRATION_TEST command>")`
4. Fix any failures (max 2 attempts)
5. Record results in workflow file

## Extension Hook Events

If extension hook events are configured (detected in Step
0.11 via `.specify/extensions/.registry` or Glob fallback),
the autopilot must handle prompts that fire at each phase.
Hooks are configured in `.specify/extensions.yml`.

**Extension detection priority (Step 0.11):**
1. `.specify/extensions/.registry` (JSON) — MOST authoritative.
   Check each extension's `enabled` field.
2. Glob `.specify/extensions/*/extension.yml` — fallback if
   no registry exists.
3. NEVER rely on the `installed` field in `.specify/extensions.yml`
   — it may be stale or empty even when extensions are active.

### All 8 Hook Events in the Autopilot Flow

| Hook Event | When It Fires | Autopilot Behavior |
|------------|--------------|-------------------|
| `before_specify` | Before Phase 1 starts | **Accept** — pre-flight checks are non-destructive |
| `after_specify` | After Phase 1 completes | **Accept** — may sync to external tools |
| `before_plan` | Before Phase 3 starts | **Accept** — validates prerequisites |
| `after_plan` | After Phase 3 completes | **Accept** — may generate additional artifacts |
| `before_tasks` | Before Phase 5 starts | **Accept** — verifies plan completeness |
| `after_tasks` | After Phase 5 completes | **Accept** — e.g., verify-tasks checks for phantom completions |
| `before_implement` | Before Phase 7 starts | **Accept** — checklist pre-checks |
| `after_implement` | After Phase 7 completes | **Accept** — e.g., verify, review, retrospective |

**Where hooks fire in the execution loop:**

```text
for each phase:
  1. Check .specify/extensions.yml for before_<phase> hooks
  2. If hooks exist → run accepted hooks, skip duplicates
  3. Spawn subagent for the phase
  4. Receive result
  5. Check .specify/extensions.yml for after_<phase> hooks
  6. If hooks exist → run accepted hooks, skip duplicates
  7. Validate gate
  8. Advance
```

### Hook Handling Rules

1. **Accept non-destructive hooks** — read-only verification,
   reports, and analysis hooks are safe to run automatically
2. **Skip hooks that duplicate autopilot verification** — if
   the autopilot already runs the same check (e.g., cleanup
   vs the autopilot's own lint/test verification), skip to
   avoid redundancy
3. **Document decisions in workflow file** — log which hooks
   were accepted, skipped, and why
4. **Check ALL 8 events** — don't assume only after_tasks
   and after_implement have hooks. Extensions may register
   hooks for any event. Read `.specify/extensions.yml` to
   know which events have hooks configured.

**Hook `optional` field behavior:**
- `optional: true` — In interactive mode, the CLI prompts the user
  before running. The autopilot runs NON-INTERACTIVELY, so it
  must decide automatically: **auto-accept** hooks that match the
  acceptance rules above (non-destructive, no duplication).
  The autopilot does NOT literally respond to a prompt — it
  invokes the hook's command directly via `Skill()`.
- `optional: false` — The hook auto-executes without prompting.
  The autopilot should always run these.
- `enabled: false` — The hook is disabled. Skip it entirely.

### Preset-Aware Phase Execution

If presets are installed (detected in Step 0.11), the autopilot
should understand what the presets enforce:

1. **Read preset templates** at startup (Step 0.11) to learn
   what conventions the project uses (TDD mandates, architecture
   patterns, test requirements, etc.)
2. **Pass conventions to subagents** — include PRESET_CONVENTIONS
   in the implement-executor and other subagent prompts so they
   follow the project's patterns without hardcoding
3. **Expect different artifact structure** — if a preset overrides
   `tasks-template.md`, the generated tasks will have different
   sections than core defaults. The autopilot's task parsing
   should handle any structure.
4. **Debug with `specify preset resolve`** — if artifacts have
   unexpected structure, run `specify preset resolve <template>`
   to see which file the `/speckit-*` command actually used

## PR Creation Protocol

After G7 passes:

```text
Step 1: Run final verification suite (build, typecheck, lint, test)
Step 2: Detect remote name: git remote -v
Step 3: Push branch: git push -u <remote> <branch>
Step 4: Apply final reviewability boundary:
  Use current committed reviewability evidence; if none is current, stop before PR side effects because final-reviewability-backstop is deferred.
Step 5: Emit or refresh the current packet at specs/<feature>/.process/pr-packets/<packet-id>.json.
  Run pr-packet-output in dry_run, then apply with current title, target, changed-file, verification, UAT, non-goal, and known-gap evidence.
Step 6: Validate that packet with validate-pr-packet-read-only and consume data.stdout_json in memory/state.
  Require data.stdout_json.status=passed, data.stdout_json.pr_blocked=false, and response data.writes_state=false.
  If any required packet is absent or invalid, stop before PR creation with the validator diagnostics.
  Checkpoint packet/body artifacts so validate-pr-packet-write runs from a clean worktree; apply mode reruns read-only validation before persisting validation_result_path.
Step 7: Validate title/scope with validate-pr-workflow-contract using the packet title.
Step 8: Create the PR only from packet fields:
  gh pr create --base <packet.target.base_branch> --head <packet.target.head_branch> \
    --title <packet.generated_title.value> --body-file <packet.body_file>
Step 9: Update workflow file with PR URL
Step 10: Final commit: "feat(SPEC-XXX): open PR for review"
```

`generate-pr-body` is a body-only `golden_only` operation. Its complete input
contract is `output_path`, `title`, and `sections`, and it writes one Markdown
body. It does not create or update packet JSON, packet metadata, template
markers, validation evidence, or PR commands. Its output alone never authorizes
PR creation.

The current committed backstop evidence is fail-closed at the PR boundary.
Recorded exit 0 means the final diff gate passed, warned, honored a valid typed
exception, or produced final
`marker_split` with a current `pr_marker_plan`; PR preparation may continue.
When a current `pr_marker_plan` exists, PR preparation continues through
marker emission even if the final full-diff result is only `pass` or `warn`.
A full-diff size block with current marker evidence also proceeds to marker
emission and is not a manual re-slicing stop. Recorded exit 1 means
`reslicing_required` only for unexcepted
correctness or missing-marker cases: do not run `generate-pr-body`, do not
invoke any `gh pr create` variant, and do not run `multi-pr-emission` yet.
This blocks only PR side effects. It is not a final response condition: read
`autopilot_continuation`, `operator_steps`, and `resume.resume_from`; continue
inside the same autopilot run through PRSG-007, regenerate PRSG-008, or hand off
to PRSG-009 until a valid slice PR stack is emitted or a typed exception is
committed. Never report completion while
`autopilot_continuation.required=true`. Recorded exit 2 is a gate error: state is
written, no packet is valid, and the run stops for operator repair.

For marker-aware PR preparation, record gate status/mode/exit/evidence path,
fingerprint status, ordered marker IDs, checkpoints, warnings, final
marker_split or marker-plan-ready handoff, packet validation, and PR mappings
before PR side effects.

## Copilot Review Remediation Loop

After PR creation, use `/loop` to schedule recurring review
comment monitoring. The loop prompt must be **self-contained**
— each cron fire runs in a fresh context with no memory.

**Before invoking `/loop`:**
1. Extract PR number from `gh pr create` output
2. Extract repo owner/name from `git remote -v`
3. Hardcode both values in the loop prompt

**Prompt structure for `/loop`:**

```text
Skill("loop", args: "5m
  Check PR #<PR_NUMBER> in <REPO> for unresolved review
  comments and resolve them.

  Step 1 — Fetch reviews and comments:
  Command('gh api repos/<REPO>/pulls/<PR_NUMBER>/reviews ...')
  Command('gh api repos/<REPO>/pulls/<PR_NUMBER>/comments ...')

  Step 2 — If 0 unresolved, report and stop.

  Step 3 — For each unresolved comment:
  a. Code fix → edit, verify suite, commit, push, reply, resolve
  b. Style → lint:fix, commit, push, reply, resolve
  c. Question/FP → reply via gh api, then resolve

  Step 4 — Report summary.
")
```

**Critical:** All values (PR number, repo, branch) must be
hardcoded strings in the prompt. Variables and references to
conversation context will not resolve — the cron fires in a
clean session.

The loop auto-expires after 3 days (Claude Code limit).

## Workflow File Update Protocol

After each phase completes, update the workflow file with:

1. **Status table**: Change phase status from
   `⏳ Pending` to `✅ Complete` with summary notes
2. **Phase-specific results table**: Fill in metrics
   and outcomes
3. **Files Generated checkboxes**: Check off produced
   artifacts
4. **Consensus Resolution Log** (if applicable): Record
   consensus decisions

The workflow file serves as both checklist and execution
log — the complete auditable record of the autonomous
execution.

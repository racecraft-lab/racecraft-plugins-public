# Phase Execution for Codex

Codex autopilot orchestration runs in the parent session. Phase work runs in
installed custom subagents through `spawn_agent` and `wait_agent`.

## Contents

- [Canonical Order](#canonical-order) — `PHASES = [...]` + `--from-phase` semantics
- [Stage-Bounded Execution](#stage-bounded-execution) — which phases the resolved stage may start, its terminal step, and the resume protocol
- [Agent Mapping](#agent-mapping) — per-phase executor + prompt prefix table
- [Main Execution Loop](#main-execution-loop) — full 11-step per-phase pseudocode
- [Phase 3: Plan — Reviewability Budget](#phase-3-plan--reviewability-budget-advisory) — advisory plan-phase production-LOC estimate
- [Phase 7: Implement](#phase-7-implement) — task decomposition + placeholder replacement + reviewability gate
- [PR Body Generation](#pr-body-generation) — script invocation order pre-PR
- [Coverage Audit](#coverage-audit) — all-phase prefix audit run before/during/on-resume

## Canonical Order

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]
```

`--from-phase` changes the first phase to execute, not the required plan
coverage. `update_plan` and `autopilot-state.json` must still contain Phase 0,
all seven SDD phases, and Post before any subagent is spawned.

## Stage-Bounded Execution

`AUTOPILOT_STAGE` is resolved once at Step 0.6c. It bounds which phases this
invocation may run:

| Stage | Phase range | Terminal step |
| --- | --- | --- |
| `plan` | Specify, Clarify, Plan, Checklist, Tasks, Analyze | G6.5 confidence gate, then the stage-boundary commit |
| `implement` | Implement, then the post-implementation steps | `Post: Retrospective` |
| `full` | All seven phases end to end | `Post: Retrospective` |

The stage bounds which phases may **start**. It never truncates the canonical
plan: `update_plan` and `autopilot-state.json` still contain Phase 0, all seven
SDD phases, and Post before any subagent is spawned, and entries outside the
range are marked per
[task-list-canonical-codex.md](./task-list-canonical-codex.md#out-of-stage-entries).

**A resolved stage MUST NOT start a phase outside its own range.** Apply the
range *before* the first-pending scan picks a row, not after:

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

### Plan Stage: G6.5 Is The Terminal Step

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
regeneration commit uses for its `docs:` subject.

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
implementation-stage invocation **MUST NOT reject them** — rejecting would be a
subtractive change to a shipped surface. It must instead make the flag's
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

### Resume Protocol

Resuming is the same protocol on both distributions, because both read the same
durable store through the same Step 0.6c operation.

**The `Stage` entry is workflow-file-wins.** The `Stage` row in the workflow
file's `### Basic Information` table is the authoritative durable store of the
resolved stage; `autopilot-state.json.stage` mirrors it for the active run only
and is never authoritative. On disagreement the workflow file wins and the
mirror is repaired from it. Absence on either side is legal — it means no run
yet, and resolves through Step 0.6c auto-detection. A two-sided disagreement is
reported by the Step 1.1 coverage guard as `stage_mirror_errors`, which is
registered in the `status-evidence` rule and so fails the guard rather than
merely printing.

Three resume forms, in order of preference:

- **Bare re-invocation** — pass the workflow file and nothing else. Step 0.6c
  re-resolves the stage from the workflow file's own status table and prints the
  basis. After a plan-stage boundary this re-resolves `plan` whenever the
  `Confidence Gate` row is non-terminal, so a refused boundary is never crossed
  by accident.
- **`--stage implement`** — the explicit crossing. Required after a strict-mode
  stop, and it reports the recorded verdict it is proceeding past rather than
  re-running the gate.
- **`--from-phase <phase>`** — moves the starting point within the resolved
  stage's range. The older `--from-phase implement` form keeps working and is
  not rejected against an auto-detected stage.

## Agent Mapping

| Phase | Agent | Prompt prefix |
| ----- | ----- | ------------- |
| Specify | `phase-executor` | `Run $speckit-specify with:` |
| Clarify | `clarify-executor` | `Prepare a Clarify Question Set for:` |
| Plan | `phase-executor` | `Run $speckit-plan with:` |
| Checklist | `checklist-executor` | `Run $speckit-checklist with:` |
| Tasks | `phase-executor` | `Run $speckit-tasks with:` |
| Analyze | `analyze-executor` | `Run $speckit-analyze with:` |
| Implement | `implement-executor` or project implementation agent | Task-specific TDD prompt |

Consensus uses `codebase-analyst`, `spec-context-analyst`, and
`domain-researcher`. `autopilot-fast-helper` is optional and never votes.

## Main Execution Loop

For each pending phase, spawn a subagent, collect the result, validate the
gate, and advance.

```text
for phase in PHASES starting from first_pending:
    0. Re-run the all-phase coverage audit against update_plan and
       autopilot-state.json. If Archive Sweep or any canonical phase family
       is missing, STOP and repair the plan before executing this phase.
    1. update_plan: mark the current phase item as "in_progress"
       and mirror the same status change into autopilot-state.json
    2. Check .specify/extensions.yml for before_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    3. Read the workflow file's prompt(s) for this phase
    4. For EACH prompt in the phase:
       a. Resolve <executor>:
          use the matching installed SpecKit custom agent
       b. spawn_agent the resolved <executor>:
          "Run $speckit-<phase> with: <prompt>"
       c. Loop bounded wait_agent calls until this executor's actual summary is
          delivered; a status update or timeout alone is not the result. Record
          the summary, then close_agent only when that action is exposed. On
          hosted Responses, the host retains the inspectable completed thread.
       d. update_plan: mark this prompt's item as "completed"
       e. Write the same transition to autopilot-state.json
    5. Run consensus in main session if needed:
       Parse executor's "Unresolved for consensus" section.
       For each item → spawn the category-routed analysts (codebase-analyst,
       spec-context-analyst, domain-researcher) per Rule 7 via
       spawn_agent → bounded wait_agent loop → consume each analyst result,
       calling close_agent only when exposed and never exceeding the derived
       subagent_slots limit (dispatch in waves when items × analysts exceeds
       the cap) → apply consensus rules → edit
       artifacts → mark the corresponding Consensus item complete in both stores
    6. Check .specify/extensions.yml for after_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    7. Validate gate directly in the main session:
       Run 'runner helper validate-gate' for gate G<N>
       against <feature_dir> from the orchestrator using the
       resolved scripts path for this skill.
       Parse the script output for PASS/FAIL status.
    8. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
    9. Update workflow file with results and print the current checklist summary
   10. If auto-commit == "per-phase":
       For phases 1–6: run: git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json && git commit
       (the workflow file and state file live outside specs/, so a phase that
       does not stage them by path leaves its bookkeeping uncommitted)
       For phase 7 (implement): run: git add -A && git commit
       (implementation changes include src/, tests/, etc.)
   11. Advance to next phase (next iteration of loop) and write the new
       in_progress item to both update_plan and autopilot-state.json.
       Never mark the run complete while a later phase family still has
       pending items.
```

After all 7 phases complete, proceed to the post-implementation parallel
group (see [post-implementation-codex.md](./post-implementation-codex.md)).

## Static Tier-2 Relocation Suggestion

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

## Phase 3: Plan — Reviewability Budget (advisory)

After the Plan phase executor returns and `plan.md` exists (G3 pass), run the
standalone plan-phase estimator to project each slice's production-LOC footprint
from `plan.md`'s declared file structure. This is preventive sizing — it catches
an oversized slice at plan time, before any code is written. It is **advisory
only**: no outcome blocks, prompts mid-autonomous-run, or aborts the run (hard
blocking / re-slicing is PRSG-010, explicitly out of scope here).

Invoke runner helper `estimate-reviewable-loc` from the parent session with
`exec_command` and **capture the response status** rather than letting a
non-zero tool result propagate and abort the run:

```text
plan = "specs/<feature>/plan.md"
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

- **`pass`** → record "within budget" in the workflow/plan record and
  `autopilot-state.json` (silent — no prompt, no block).
- **`over_budget`, autonomous run** → record an over-budget note in the
  workflow/plan record and **CONTINUE** (advisory, non-blocking — FR-004,
  SC-002). Never block the run or trigger re-slicing.
- **`over_budget`, interactive use** → surface the over-budget result to the
  human as a decision (FR-005).
- **`not_estimated`** (`projected: null` — `plan.md` has no parseable declared
  production-file structure) → record "not estimated (no declared production
  files)" and continue. Never treat this as a within-budget pass.
- **diagnostic response** → record "estimator could not run" with the diagnostic code and
  continue the autonomous run.

This mirrors the Codex gate-handling pattern: read the structured runner
response and branch on it rather than aborting.
Advisory-and-never-crash is the invariant for every outcome — under-budget,
over-budget, unmeasured, or errored — none may block, prompt
mid-autonomous-run, or crash the run. If the helper is unavailable on an older
plugin build, record the diagnostic note and continue, same as any other error
path.

## Phase-Gate: Spec-MOC Navigation Regeneration

At **every phase boundary** — for all seven phases — regenerate the spec map
navigation zones and fold any change into that phase's existing checkpoint
commit. This runs as an **idempotent** step **immediately before step 10's
commit** in the Main Execution Loop above (the scoped `git add` for
phases 1–6, `git add -A && git commit` for phase 7), so the rebuilt maps are
swept into that same commit. A boundary that changes nothing contributes
nothing — no extra `update_plan` item and no `autopilot-state.json` transition
are recorded for this step.

**Why before step 10:** step 10's `git add … && git commit` is what folds the
rebuilt maps into the one checkpoint commit. Running the rebuild *after* the
commit would force a second commit on every map-affecting boundary — the
failure this ordering avoids.

**Step (run at each boundary, before step 10):**

```text
# Write mode (NO --check): regenerate over the autopilot's target repo.
# Pass "$PWD" explicitly — do NOT rely on the generator's default REPO_ROOT.
# In a cached-plugin run the default resolves to the plugin cache's parent, not
# the user's project, so the explicit arg is required.
runner helper generate-spec-index-write with repo root "$PWD" and mode apply
```

**Act on the result:**

- **Exit 2 (error)** → a map is malformed/unbalanced or a PRS manifest is
  unreadable. **Surface the actionable stderr line and STOP.** Do NOT commit a
  broken regen and do NOT advance the phase.
- **Exit 0 (clean)** → the generator wrote any stale maps and returned success.
  **The commit decision is diff-driven, not exit-code-driven** (write mode
  returns `0` whether or not it changed a file; the stale `exit 1` is
  `--check`-only and is never reached here). Inspect the working tree:
  - `git diff` (plus `git status` for newly-injected zones) is **empty** →
    nothing was regenerated. This is the idempotent no-op: contribute nothing,
    proceed to step 10's normal commit.
  - `git diff` is **non-empty** and the rebuild rides **alongside** other
    staged phase work → it is folded into that phase's existing checkpoint
    commit (`feat(SPEC-XXX): complete <phase> phase` / `feat(SPEC-XXX):
    implement phase`). No separate commit is made.
  - `git diff` is **non-empty** and the regenerated maps are the **only**
    staged change → make a standalone commit with this fixed, public-readable
    subject:

    ```text
    docs(speckit-pro): regenerate spec-MOC navigation zones
    ```

This subject is a fixed constant (it is NOT computed per run): `docs:` because
regenerating generated documentation zones is a docs-scope change and does not
trigger a release-please version bump. The regeneration is a pure function of
committed files, so re-running it on an unchanged tree yields a zero-byte diff
and no commit — exactly one rebuild contribution to the checkpoint commit on a
map-affecting boundary, and none on a no-op boundary.

## Phase 6.5: Pre-Implement Confidence Gate

After Phase 6 (Analyze) commits and before Phase 7 begins, run the optional
Pre-Implement Confidence Gate (G6.5). The synthesizer's final emit on the
workflow file (see [consensus-protocol.md §Pre-Implement Confidence Emit](consensus-protocol.md#pre-implement-confidence-emit-end-of-phase-6-analyze))
provides the data; the gate script reads it and decides whether to proceed,
surface a remediation hint, or stop.

```text
1. Read mode from `CONFIDENCE_GATE_MODE` (set at Step 0.6b in
   the autopilot SKILL.md by `resolve-confidence-mode`). The
   resolver runs once at autopilot start so `--strict --advisory`
   conflicts and unknown values fail fast before any phase work
   begins, instead of surfacing 6 phases in.

2. Resolve threshold (`confidence_threshold: 0.90`). Default: 0.90.

3. On entry, print the /goal tip:
   - Codex interactive mode: "Tip: run `/goal achieve confidence ≥<T> on
     the pre-Implement gate` to get the goal-mode iteration."
     (Requires `features.goals = true` in `~/.codex/config.toml`.)
   - Codex `codex exec` headless: "/goal is not first-class in headless
     mode per openai/codex#21764 — the 3-iteration cap is your safety
     bound."

4. Run the gate:
     'runner helper confidence-gate' \
       <workflow-file> --threshold <T> --mode <M>

5. Parse exit code + JSON:
   - exit 0 (PASS): update_plan G6.5 → completed. Advance to Phase 7.
   - exit 1 (NO_DATA): log a warning, treat as plugin regression to
     report. update_plan G6.5 → completed with `no_data: true`.
     Advance to Phase 7.
   - exit 2 (FAIL):
       a. Read JSON `criteria` object; find the lowest-scoring criterion.
       b. If iteration_count < 3:
            - spawn_agent on the appropriate analyst for the lowest
              criterion (e.g., "task_understanding" lowest →
              clarify-executor re-pass on spec.md; "risk_assessment"
              → analyze-executor re-pass on open findings;
              "completeness" → verify artifact presence).
            - spawn_agent consensus-synthesizer to re-emit the
              pre-Implement Confidence block to the workflow file.
            - Re-run confidence-gate.
            - Increment iteration_count.
       c. After max iterations OR exit 0:
            - mode=advisory: log + advance to Phase 7.
            - mode=strict: STOP. Operator may resume with
              --from-phase implement if they accept the lower score.
```

The iteration cap of 3 is the only safety bound in Codex `codex exec`
headless mode. In Codex interactive TUI with `features.goals = true`,
an operator-set `/goal` provides an additional turn-based check
layered on top of the cap.

**Why this gate is opt-in for blocking:** Clarify (G2) and Analyze
(G6) already filter most pre-Implement shakiness. Advisory mode
surfaces the score and a remediation hint without blocking; strict
opt-in via local config for operators who want a fail-closed posture.

**update_plan**: at autopilot start, after the G6 task, create a
G6.5 task `Confidence gate (pre-Implement)`. Transition through
`in_progress` → `completed` regardless of advisory vs strict outcome
(strict only differs in whether Phase 7 runs).

## Phase 7: Implement

Before `tasks.md` exists, the plan contains:

```text
Phase 7: Implement - Pending task decomposition
```

After Tasks completes, replace that placeholder with concrete task-group items
from `tasks.md`. Each implement item must include the task IDs, dependencies,
TDD protocol, `PROJECT_COMMANDS`, and `COMPLETED_TASKS` context accumulated from
earlier work.

After G5 passes, the placeholder is invalid. Before Analyze or Implement can
run, audit `update_plan` and `autopilot-state.json`, then apply the
tasks-phase reviewability boundary. Runner helper `reviewability-gate`
supports setup mode only on the installed runner — tasks mode is deferred, so
do not invoke it as an active helper. Record the deferred-mode diagnostics
(helper ID, requested mode, deferral reason) in the workflow file, then
evaluate the fallback evidence chain: the setup-mode gate result recorded at
scaffold, the plan-phase `estimate-reviewable-loc` verdict, and any
operator-ratified split decision in the workflow file. If that committed
evidence shows `pass`, `warn`, or an honored typed exception, continue. If it
shows a valid current size-only `status=block`, continue into marker
planning and later marker emission; it is not a manual re-slicing stop.
Correctness stops remain blocking: malformed/stale marker state, failed
verification, invalid packet, unsafe output, unusable gate evidence, invalid
JSON, unreadable artifacts, missing reviewability status/mode, stale
fingerprints, or any non-size safety finding.

- no `Phase 7: Implement - Pending task decomposition` item remains
- one or more concrete `Phase 7:` items exist
- each concrete item names one or more task IDs parsed from `tasks.md`

If any check fails, repair both state stores and print the corrected checklist
summary before continuing.

When reviewability evidence is marker-planning input, persist top-level
`pr_marker_plan` in `autopilot-state.json` and mirror the same schema version,
source fingerprint, fingerprint status, ordered marker IDs, review order,
checkpoints, warnings, final marker_split placeholder, packet validation
placeholder, and PR mappings placeholder in the workflow evidence. `tasks.md`
stays the task source; it is not authoritative marker state. Use repo-relative
evidence paths.

On resume, validate the marker-plan fingerprint against the current spec,
plan-declared file/test scope, tasks, reviewability evidence, and hazard route.
Missing, malformed, stale, or fingerprint-mismatched marker plans are
correctness stops at marker-required boundaries.

**Open the implementation-notes record before the first task is dispatched.**
This is parent-session work, not delegated work, and it runs ahead of the first
`spawn_agent` call rather than lazily on the first append: a phase interrupted
before any task completes, and a spec carrying no implementation tasks at all,
must both still leave a header-only record behind. The record is one file per
spec at `<FEATURE_DIR>/.process/implementation-notes.md`, beside the rest of the
feature's autopilot exhaust. Its first line is the header, written exactly once:

```text
# Implementation Notes: <SPEC_ID>
```

- **Create if absent**: create the `.process/` directory too when that directory
  is also absent, then create the file with the header as its only content. An
  absent directory is a thing to create, never a failure to report.
- **Never truncate**: when the record is already there, leave every existing
  byte as found and append after the existing content. Do not write a second
  header. This is the resumed-phase case, and the entries already in the file
  are the whole point of the record.
- **Check the record's own path** in the working copy this run executes in,
  never a state file, an index, or anything carried over from the session that
  wrote the record, so a resume in a fresh session behaves exactly like a resume
  in the session that started the run.
- **Fail-open**: when creation fails, record a gap in
  `docs/ai/specs/.process/<SPEC_ID>-workflow.md` naming this setup step and the
  operation that failed, do not retry, and carry on into dispatch. Task and
  phase outcomes are exactly what they would have been had the write succeeded.

Use `implement-executor` for test and implementation tasks unless Step 0.11
found a more specific project implementation agent. The parent session dispatches
all workers directly; subagents do not spawn nested agents.

Every attempt the parent session dispatched gets one entry in that record,
appended after everything already in the file:

```text
### <TASK_ID>

**Deviations/Edge cases/Surprises:** <reported text, or None>
```

`<TASK_ID>` is the task's ID exactly as the task list writes it, and one blank
line separates the entry from the content before it.

**One entry per task, even when several tasks share one dispatch.** Batching
related tasks into a single worker is a sensible dispatch choice and does not
change the record: each task named in the task list gets its own entry under its
own ID. Never write a compound heading such as `### T007+T008+T009`, because a
reader cannot recover three task IDs from one heading. Split the worker's
reported text across those entries, or repeat the shared text under each.

**Per-arrival cadence, one rule for every dispatch shape.** Append on the turn
that attempt's own result reaches the parent session, before dispatching further
work. The bounded `wait_agent` loop already delivers each worker's summary
individually, so a member of a cap-bounded `[P]` wave does not wait for the rest
of its wave: its entry is written when that summary is consumed, not when the
wave reaches its TYPECHECK and UNIT_TEST safety net. Never batched to phase end,
and never deferred to a wave boundary. Where several summaries are consumed on
the same turn, each still gets its own entry on that turn, in the order they are
presented.

**Never append on a bare idle or liveness signal.** A status update, a
`wait_agent` timeout, or a worker that stops without delivering its task summary
is not a result: it is a cue to keep polling, or to ask for the summary, and not
a cue to write an entry. Appending on one writes an empty entry, then
double-counts the attempt once that worker's real summary arrives.

**Additive only.** No entry already written is rewritten, reordered, or removed,
and the record is never read back to update a counter or to find a previous
entry. The serial re-run after a regression appends a further entry under the
same task ID and leaves the earlier one exactly as written; two entries sharing
a task ID are correct history, not a defect. Document order is append order, so
position is the record's only ordering signal, and where two entries share a
task ID the earlier-positioned one is the earlier attempt.

**Fail-open on an append too.** A failed append is recorded as a gap in the
run's workflow file, never in the implementation-notes record that just failed,
and the gap names the attempt and the operation that failed so a reader can tell
which write was lost. The write is not retried: one attempt, then the gap. The
fallback is exactly one level deep, so when the workflow file is itself the
unwritable path, surface that second failure in the run's own output and carry
on, with no third destination and no recursion. The blast radius is one entry:
every other attempt in the same wave is still appended as its own result
arrives, and the next dispatch still happens. A reporting-content problem is not
a write failure, so a missing or unreadable field produces a `None` entry rather
than a gap.

**Three append call sites in the routing, not one.** The routing branch decides
what an entry carries, which is a different axis from the dispatch shape that
decides when it is written:

| Route | Task-result block? | Entry value |
| ----- | ------------------ | ----------- |
| `implement-executor` or project implementation agent | Yes | Reported text, or `None` |
| Research routed to `domain-researcher` | No | `None` |
| Verification run orchestrator-direct | No | `None` |

Appending only on the executor branch leaves research and verification attempts
silently missing from the record.

**The literal `None`** is the single value for every nothing-to-report case: the
executor reported `None`, the executor omitted the field, the field cannot be
read out of the summary it returned, or the route emits no task-result block at
all. No distinct marker and no route field, because a second value would make
the record unreadable as a count of what was reported the moment a wave contains
one research task.

When a current `pr_marker_plan` is available, execute, checkpoint, and record
Phase 7 evidence in marker order. Run each marker's tasks according to
`markers[].review_order`; keep normal task dependency and `[P]` parallel rules
inside a marker. After each marker completes, record marker ID, ordered task IDs,
verification evidence path, fingerprint status, checkpoint commit SHA
(`implementation_checkpoint.head_sha` or `implementation_checkpoint.commit_sha`),
warnings, and any blocked/fixed tasks. The marker checkpoint SHA is the source
commit for later live marker PR branches. Do not infer a new marker order from
changed files or reviewability warnings.

## PR Packet and Body Boundary

Before creating or updating a PR after G7, the parent session applies this
fail-closed sequence:

```text
final-reviewability boundary: use current committed reviewability evidence; if none is current, stop before PR side effects
emit or refresh specs/<feature>/.process/pr-packets/<packet-id>.json with pr-packet-output dry_run then apply
run validate-pr-packet-read-only for that packet and consume response data.stdout_json in memory/state
require data.stdout_json.status=passed, data.stdout_json.pr_blocked=false, and response data.writes_state=false
checkpoint packet/body artifacts so validate-pr-packet-write runs from a clean worktree
run validate-pr-packet-write; apply mode reruns read-only validation before persisting validation_result_path
run validate-pr-workflow-contract with the packet title
create only with packet-owned --base, --head, --title, and --body-file values
```

Continue only after current committed reviewability evidence shows `pass`,
`warn`, honored typed exception, or final `marker_split` with a current
`pr_marker_plan`. When a current `pr_marker_plan` exists, PR preparation
continues through marker emission even if the final full-diff result is only
`pass` or `warn`. A full-diff size block with current marker evidence also
proceeds to marker emission and is not a manual re-slicing stop. In the current
committed evidence, exit 1 is `reslicing_required` only for unexcepted
correctness or missing-marker cases:
do not generate a PR body, invoke any `gh pr create` variant, or run
`multi-pr-emission` yet. This blocks only PR side effects. It is not a final
response condition: read `autopilot_continuation`, the packet's
`operator_steps`, and `resume.resume_from`; continue inside the same autopilot
run through the named PRSG-007/008/009 phase until a valid slice PR stack is
emitted or a typed exception is committed. Never report completion while
`autopilot_continuation.required=true`. Recorded exit 2 is a gate error: state is
written, no packet is valid, and the run stops for operator repair.

For marker-aware PR preparation, record gate status/mode/exit/evidence path,
fingerprint status, ordered marker IDs, checkpoints, warnings, final
marker_split or marker-plan-ready handoff, packet validation, and PR mappings
before PR side effects.

Use `pr-packet-output` to emit or refresh the feature-local packet and
packet-owned body before `gh pr create`. If the packet or body is missing,
stale, malformed, or invalid, rerun packet output with current title, target,
changed-file, verification, UAT, non-goal, and known-gap evidence. The
read-only validator returns its result in `data.stdout_json` and does not
persist state. If any required packet is absent or invalid, stop before PR
creation with the validator diagnostics. Checkpoint packet/body artifacts so
`validate-pr-packet-write` runs from a clean worktree; apply mode reruns
read-only validation before persisting `validation_result_path`.

`generate-pr-body` is a body-only `golden_only` operation. Its complete input
contract is `output_path`, `title`, and `sections`, and it writes one Markdown
body. It does not create or update packet JSON, packet metadata, template
markers, validation evidence, or PR commands. Its output alone never authorizes
PR creation.

## Coverage Audit

Run the all-phase coverage audit before Phase 1, after every phase transition,
and on resume. If any of these prefixes is absent from either durable state
store, repair the plan before continuing:

```text
Phase 0:
Phase 1:
Phase 2:
Phase 3:
Phase 4:
Phase 5:
Phase 6:
Phase 6.5:
Phase 7:
Post:
```

Then run the deterministic guard against the workflow/state pair:

```text
resolved_python "<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py" --workflow "$WORKFLOW_FILE" --state "$WORKFLOW_DIR/autopilot-state.json" --rule status-evidence
```

`resolved_python` is the Python 3.11+ interpreter resolved by the installed
runtime contract, not a hardcoded interpreter name; `<plugin-root>` is the
directory that owns `skills/speckit-autopilot/`. `--rule status-evidence`
scopes the exit code to the bookkeeping rule, matching the Claude variant.

For `pr-marker-plan.v2` state with a changed-file manifest, append
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`
using OIDs fetched from live PR metadata immediately before the run. Do not
reuse values declared by the workflow, state, or manifest as external PR
authority.

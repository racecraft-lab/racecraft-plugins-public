# Gate Validation Reference

Programmatic gate checks performed after each SDD phase. Before every repair,
use [Bounded Execution and Verification](./execution-efficiency.md): one corrective
cycle per stable failure family and two across the spec, including nested work.
No gate has an independent retry allowance. An exhausted repair budget defers
that gate's repair to the end-of-run request; a failed requirement or security
gate never becomes a pass.

## Contents

- [Gate Definitions](#gate-definitions) — G0 (prerequisites) through G7 (post-implement), with Check + Auto-Fix + Failure Escalation per gate
- [Gate Summary Table](#gate-summary-table) — at-a-glance phase → gate → script mapping
- [Additional Verification (Extension Commands)](#additional-verification-extension-commands) — `/speckit.verify`, `/speckit.verify-tasks`
- [Failure Escalation Protocol](#failure-escalation-protocol) — defer an exhausted repair and ask once at the end

## Gate Definitions

### G0 — Prerequisites (Before Specify)

**Check:** Constitution principles validated against the current codebase.

```
1. Architecture patterns verified (e.g., patterns documented in CLAUDE.md)
2. Workflow file's Prerequisites table filled with the quality-gate baselines
3. Constitution Check summary line set to "✅ Verified"
4. Reviewability setup gate passes:
   `runner helper reviewability-gate setup <workflow-or-roadmap>`
   must be `pass`, `warn`, or a recorded `exception`; `block` stops before
   Specify and requires spec decomposition.
   When the target is the technical roadmap (scaffold), pass `spec_id`. The
   gate then reads only that `### <SPEC-ID>:` section: its budget numbers,
   its `Primary surface:` values, and a line-anchored
   `Reviewability-Exception: refactor|infra|upgrade` pragma, which turns a
   size `block` into `exception`. A missing section is a gate error; a
   missing budget number is a `block` that no pragma excuses.
```

The typecheck, test, build, and lint baseline belongs to implement entry
(phase-execution.md, Phase 7 Setup: Project Baseline).

**Auto-Fix:** Spawn a repair agent for the failing check within the gate's allowance.

**Failure Escalation:** If a check still fails, run the repair loop within its allowance, then defer per the Failure Escalation Protocol. Record which checks failed with their output.

### G1 — After Specify

**Check:** Determine if clarification is needed.

```
Search spec.md for "[NEEDS CLARIFICATION]" and "[NEEDS CLARIFICATION: ...]" markers.
- Record the marker count; Clarify runs next either way (one session, at most 5 questions)
```

G1 records the count. It does not route: every SPEC runs Clarify. Markers are expected and normal.

### G2 — After Clarify

**Check:** All ambiguities resolved, no unresolved review flags.

```
1. grep -c "NEEDS CLARIFICATION" spec.md → must be 0
2. grep -c "ROUND_3_TIEBREAK" spec.md → must be 0
3. Clarifications section exists in spec.md with documented decisions
```

**Auto-Fix:** Re-run clarify focused on remaining markers. Spawn consensus agents for each unresolved question.

**Failure Escalation:** If markers remain when the shared reservation ends, run the repair loop within its allowance, then defer per the Failure Escalation Protocol; its last tier for a remaining consensus item is the Round 3 tiebreak (see consensus-protocol.md §Round 3 Tiebreak). An item that changes product scope the spec and roadmap do not settle is applied provisionally with its most conservative option and listed in the end-of-run request; the run continues. Record the remaining ambiguities with all 3 agent perspectives.

### G3 — After Plan

**Check:** Required artifacts exist and constitution gates pass.

```
1. Verify plan.md exists and is non-empty
2. Verify research.md exists (may be brief for simple specs)
3. Verify data-model.md exists (if spec has data entities)
4. Search plan.md for "FAIL" in constitutional gate sections
5. Verify no unresolved `[NEEDS CLARIFICATION]`, `TODO`, `TKTK`, or `???`
   markers in plan.md
6. When formal selection is enabled, require its current model-check receipt
   after the separate post-Plan author checkpoint; pass workflow_file to the
   validate-gate request. Type checking, stale evidence, and partial induction
   are insufficient. Follow formal-methods.md for bounded repair and resume.
```

**Auto-Fix:** Re-run Plan with the gate failure as additional context, then
re-run G3. If a required artifact is missing or a specific constitutional gate
failed, include the missing artifact or principle text and ask the planner to
address it. Use the parent's shared corrective reservation.

#### Plan ambiguity provenance repair

When G3 fails on unresolved requirement wording, the parent orchestrator owns
this repair. Do not ask consensus agents to vote on provenance and do not treat
the planner's interpretation as the original requirement.

Before the first repair attempt:

1. Read the exact disputed wording and trace it to the earliest available
   authoritative source: the original human answer in the current conversation
   or its durable Clarify Results record; an operator-authored brief, PRD, or
   roadmap statement; or cited code/documentation evidence for a necessary
   implication.
2. Assign exactly one provenance class:
   - `explicit-human` — direct human wording, or a durable record that
     preserves that answer without strengthening it;
   - `necessary-implication` — a constraint required by cited source facts,
     with the implication chain recorded;
   - `assistant-inference` — wording introduced or strengthened by an agent
     beyond the source evidence; or
   - `unresolved-provenance` — the original source is unavailable, conflicting,
     or too ambiguous to classify safely.
3. Treat generated spec/plan text, repetition by later agents, and consensus
   agreement only as downstream interpretations. None can upgrade a constraint
   to `explicit-human` or justify calling it user-ratified.
4. Under Plan Results, create or append this conditional durable record:

```text
#### Plan Ambiguity Repair Log

| Attempt | Disputed wording | Source evidence | Provenance class | Repair action | G3 result | Remaining escalation reason |
| --- | --- | --- | --- | --- | --- | --- |
```

For each attempt, dispatch the same Plan phase executor with literal trusted
context blocks containing the complete original Plan prompt and the direct
source evidence used for provenance. Add a `Plan Repair Context` containing the
complete immediately preceding actual G3 runner response envelope without
summary or field omission (including its exact G3 JSON), disputed wording,
provenance class, prior repair result, and attempt number. The repair rules are:

Render that context through `render-plan-repair-context` and dispatch its
unchanged successful response envelope. The executor must copy the rendered
`PLAN_REPAIR_CONTEXT_SHA256=<digest>` receipt into its final return exactly.
This receipt preserves an authenticated context binding when a native client
retains the child prompt only in encrypted form.

The parent orchestrator, not the Plan executor, invokes the authoritative G3
runner once before the first repair and again after every completed executor
return. The executor receives the parent's complete immediately preceding G3
envelope and must not run G3 itself. Each repair therefore has the strict order
`parent G3 -> executor dispatch and return -> parent G3 rerun`.

- `assistant-inference`: remove or narrow only the unsupported strengthening;
  retain the source-supported requirement and any marker whose actual choice
  remains unresolved.
- `explicit-human` or `necessary-implication`: preserve the constraint and seek
  an implementable architecture. Do not weaken it merely to make G3 pass.
- `unresolved-provenance`: do not guess, do not call the wording user-ratified,
  and record why a repair cannot safely proceed before escalation.

Never substitute a proxy for a disputed event unless the recorded evidence
establishes that the proxy satisfies the requirement. In particular,
acknowledgement time is not interchangeable with actual UI-delivery timing.
Never delete or disguise an unresolved marker merely to make G3 pass.

`explicit-human` establishes the requested outcome, not the existence or
suitability of a proposed mechanism. A proposed callback, hook, event, or other
architecture path remains **unverified architecture** until current code or
authoritative documentation proves that the path exists and satisfies the
requirement. If that support is absent, preserve the clarification marker and
failed G3 verdict, record the evidence gap, and follow the normal bounded repair
then escalation sequence. Do not turn the proposal into established
architecture evidence, clear the marker, or report G3 passed merely because the
desired behavior came from a human.

The executor message itself must contain the exact trusted-context bytes and
the complete parsed G3 response object. A path, instruction to read, excerpt,
summary, or reconstructed subset is not equivalent. Verify those complete
values are literal substrings of the message before dispatch; repair the
message first if any value is absent.

After every completed Plan repair, run `validate-gate` for G3 again and append
the returned result to the log. Stop when G3 passes, its shared corrective
reservation ends, or when `unresolved-provenance` makes a safe repair
impossible. A skipped repair records the applicable reason rather than
fabricating an attempt.

**Failure Escalation:** If any G3 condition still fails after its reserved cycle,
or provenance cannot be established well enough to repair safely, run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
Record the exact gate output, disputed wording, source evidence, provenance
class, repairs made, and the remaining choice that requires human input. The
deferred item leaves the failed G3 verdict and unresolved marker recorded and
must not rewrite their provenance.

### G4 — After Checklist

**Check:** All gap markers resolved across all checklist files.

```
1. Find all checklist files: specs/<feature>/checklists/*.md
2. Count [Gap] markers across ALL files: grep -c "\[Gap\]" checklists/*.md,
   plus spec.md and plan.md (runner `validate-gate` G4 counts all three)
3. Total must be 0
```

G4 counts only `[Gap]` markers, by design. Unticked checklist items are
reviewer-owned, so they do not fail G4. They are deferred to PR review, and
Phase 7 setup records that decision as the Implement Checklist Gate (see
phase-execution.md).

**Auto-Fix:** This is the **Checklist Gap Remediation Loop**.
Runs after each domain subagent returns (not batched — see
SKILL.md Rule 6).

```text
For EACH [Gap] marker found after a domain subagent:

Step 1: Resolve concrete evidence gaps; reuse current sources. Select relevant
sources below, not a mandatory code/web/history checklist:
  a. Codebase context — use capability-first discovery per
     `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
     ([capability-discovery.md](./capability-discovery.md)) to select
     the best installed codebase context capability and ask
     "How should we close this gap?" with the gap text,
     spec.md excerpt, and plan.md excerpt as context.
     Explore the codebase for established patterns and
     propose an evidence-grounded fix.
  b. Web or domain research / library documentation — use
     capability-first discovery per
     `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
     ([capability-discovery.md](./capability-discovery.md)) to select
     the best installed evidence source for API docs, standards,
     or best practices relevant to the gap (e.g., API behavior,
     framework patterns, error handling standards)
  c. Read constitution + prior specs — check if project
     principles or precedent decisions address the gap

Step 2: Determine the fix:
  - Which artifact to edit (spec.md, plan.md, or both)
  - What exact text to add or modify
  - Where in the artifact the edit goes (section name)

Step 3: Apply the fix to the relevant artifact(s)

Step 4: Re-run the domain checklist to verify the gap
  is closed
  - If new gaps appear → reserve by stable invariant in the same ledger;
    no per-domain reset or independent nested allowance
  - If 0 gaps → domain complete, proceed to next domain

Step 5: If gaps remain when the shared reservation ends → run the repair loop within its allowance, then defer per the Failure Escalation Protocol,
  recording the gap description, research findings,
  and attempted fixes
```

**Why research + consensus:** Gaps often require understanding
both what the codebase already does (codebase exploration) AND what
the API/standard requires (via the research broker's web search). Using multiple research
sources produces higher-quality fixes than guessing.

**Critical:** Run gap remediation sequentially (one gap at a
time) to prevent conflicting spec edits.

### G5 — After Tasks

For a Tasks prompt that requests execution metadata, validate the sidecar with
`validate-task-execution` and `task_execution_required=true` after production.
Also validate existing sidecars in legacy runs. Reconcile definitions added by
review/Converge before partitioning; checkbox-only completion is not definition
drift. See [the producer contract](./execution-efficiency.md).

For enabled formal selection, require the current `planning` checkpoint and
pass `workflow_file` to `validate-gate`. Tasks must include the selected model's
implementation obligations and any requested trace work; follow [the shared contract](formal-methods.md).

**Check:** Every functional requirement has at least one task. When tasks.md
has a requirement coverage table (a Markdown table with a `Task`, `Tasks`, or
`Task IDs` column), `validate-gate` G5 also fails every row that opens with a
requirement ID but whose task cell names no task ID, such as a blank cell or
`()`. The failure lists those rows in `empty_coverage_rows`; fill each from the
task list.

```
1. Extract all FR-XXX markers from spec.md
2. For each FR-XXX, verify it appears in tasks.md
3. Verify task dependency ordering makes sense (no forward references)
4. Verify [P] markers are only on genuinely parallel-safe tasks
5. Apply the tasks-phase reviewability boundary. Runner helper
   `reviewability-gate` supports setup mode only on the installed runner —
   tasks mode is deferred, so do not invoke it as an active helper. Record
   the deferred-mode diagnostics (helper ID, requested mode, deferral
   reason), then gather the fallback evidence chain: the setup-mode gate
   result recorded at scaffold, the plan-phase `estimate-reviewable-loc`
   verdict, and any ratified split decision (autopilot or operator) in the workflow file.
6. Apply the post-G5 reviewability proceed/stop matrix below to that
   committed evidence. A valid current size-only `status=block` continues
   into marker planning and later marker emission; it is not a manual
   re-slicing stop.
```

**Gate-task loop check:** `validate-gate` G5 also fails when an open task
gates later source work and its text requires post-implementation evidence. A
task gates source work when it sits in a setup or foundation phase, or when a
task outside the polish or emission phase depends on it, directly or through
the sidecar's `depends_on`. The evidence phrases are a closed list: "first
implementation checkpoint" (with or without "actual"), "actual diff", "actual
per-PR diff", and "actual LOC". Such a task can never
complete, because only its dependents produce that evidence. The failing
payload lists each one under `gate_task_loops`. Fix it by splitting the task: a
candidate check now, and the reconciliation attached to the emission step. A
clause that hands the evidence to a later step passes: it says "later",
"defer", "attached to", "handled by", "emission step", or "emission task".
Wording that only times a step or a stop, such as "stop before PR emission",
names no evidence and passes. An unreadable sidecar fails the gate closed.

**Auto-Fix:** For each unmapped FR:
- Generate a task that covers the requirement
- Place it in the appropriate user story phase
- Ensure it has the correct FR reference marker

**Failure Escalation:** If coverage gaps persist after the reserved cycle, run the repair loop within its allowance, then defer per the Failure Escalation Protocol. Record the unmapped FRs with the relevant spec sections.

#### Post-G5 Reviewability Capture Matrix

Autopilot owns the interpretation of tasks-phase reviewability evidence. With
tasks mode deferred on the installed runner, this matrix applies to the
committed fallback evidence chain (and to any committed tasks-mode gate
output from a prior run). Preserve the existing script contract for
lower-level callers, but do not collapse every nonzero task gate exit into a
manual stop.

**Proceed inputs:**

- `pass`, `warn`, or honored typed `exception` with valid JSON and current
  evidence.
- A valid current size-only `status=block` where `mode=tasks`, the JSON is
  parseable, the evidence is tied to the current feature, and no correctness or
  safety issue is present. This proceeds to marker planning, not operator
  re-slicing. Persist the sizing result so marker emission can use it later.

**Correctness stops:**

- malformed/stale marker state
- failed verification
- invalid packet
- unsafe output
- unusable gate evidence
- invalid JSON or unreadable task/plan artifacts
- missing reviewability status or mode
- stale fingerprints, including drift in the spec, plan-declared file/test
  scope, tasks, reviewability evidence, or hazard decision
- any non-size correctness or safety block

For every proceed decision, record evidence prompts in the workflow file:
gate status/mode/exit/evidence path, reason the block is size-only, fingerprint
status, ordered marker IDs when available, checkpoints, warnings, final
marker_split, packet validation, and PR mappings. All paths in examples and
workflow evidence must be repo-relative, not absolute runtime paths.

### G6 — After Analyze

After remediation, reconcile selected formal models and renew `planning`
evidence before proceeding. Pass `workflow_file` to `validate-gate`; current
evidence and the state mirror are required at the planning boundary.

**Check:** All requirement-linked defects and safety findings resolved at every
severity. Keep optional style/naming suggestions distinct from blocking defects.
The runner's G6 counts open CRITICAL/HIGH rows (empty Resolution) in the
workflow's Analysis Results table, plus bracketed markers in the planning files,
and fails closed when the workflow or that table is missing.

```
1. Run /speckit-analyze and capture output
2. Count findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
3. All required defects must be resolved; record optional suggestions separately
```

**Auto-Fix:** This is the **Analyze Remediation Loop**. Uses
the same research + consensus workflow as Checklist Gap
Remediation.

```text
Step 1: Run /speckit-analyze (via phase-executor subagent)
Step 2: Parse ALL findings by severity

Step 3: For EACH finding (CRITICAL, HIGH, MEDIUM, LOW):

  a. Resolve concrete evidence gaps; reuse current sources. Select relevant
     sources below, not a mandatory code/web/history pass:
     - Codebase context — use capability-first discovery per
       `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
       ([capability-discovery.md](./capability-discovery.md)) to select
       the best installed codebase context capability and ask
       "How should we fix this finding?" with the finding
       text, spec.md/plan.md/tasks.md excerpts as context.
       Explore the codebase for established patterns and
       propose an evidence-grounded fix.
     - Web or domain research / library documentation — use
       capability-first discovery per
       `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
       ([capability-discovery.md](./capability-discovery.md)) to select
       the best installed evidence source for API docs, standards,
       or best practices relevant to the finding
     - Read constitution + prior specs — check if project
       principles or precedent decisions inform the fix

  b. Determine the fix:
     - Which artifact to edit (tasks.md, spec.md, plan.md)
     - What exact change to make (add task, amend task,
       edit requirement, fix coverage gap, remove stale
       marker, etc.)
     - Cite the research source supporting the fix

  c. Apply the fix to the relevant artifact(s)

Step 4: Re-run analyze to verify all findings resolved
  - If new required findings appear → reserve by stable invariant in the same ledger
  - If 0 findings → G6 PASS

Step 5: If required findings remain when the reservation ends → run the repair loop within its allowance, then defer per the Failure Escalation Protocol,
  recording all remaining findings, research results,
  and attempted fixes
```

Severity alone cannot dismiss a behavioral defect. Required MEDIUM/LOW defects
remain blocking; optional style changes do not justify expanding the spec.

### G6.5 — Pre-Implement Confidence Gate (between Analyze and Implement)

**Check:** The synthesizer's final pre-Implement confidence
emit (see
[consensus-protocol.md §Pre-Implement Confidence Emit](./consensus-protocol.md#pre-implement-confidence-emit-end-of-phase-6-analyze))
clears a composite threshold of 0.90 (or the operator-configured
threshold). Read by
`runner helper confidence-gate`.

**The helper computes the composite; the synthesizer does not.**
It averages the five criterion scores, rounds to two decimals,
then deducts 0.30 for each open `CRITICAL` and 0.10 for each
open `HIGH` row in the workflow file's most recent Analysis
Results table, floored at 0.00. A row is open only while its
`Resolution` cell is empty, so the count falls as remediation
records fixes. The JSON reports `composite_source` (`computed`, or
`stated` when the five criterion lines are missing and only the
`📊` line is available), `criteria_mean` before deductions, and
`deductions` with its `critical`, `high`, and `amount`. A stated
number that disagrees with `criteria_mean` loses, and the
disagreement is named in `reason`.

**Default mode:** advisory.

**Mode precedence (highest wins):**

1. **Per-invocation flag:** `--strict` or `--advisory` passed to
<!-- host:claude: retain the existing Claude guidance -->
   `/speckit-pro:speckit-autopilot` (or `$speckit-autopilot` in Codex)
<!-- /host -->
<!-- host:codex: installed plugin skills use namespaced dollar mentions -->
   `/speckit-pro:speckit-autopilot` (or `$speckit-pro:speckit-autopilot` in Codex)
<!-- /host -->
   overrides everything below. Passing both flags is a usage
   error — the autopilot stops with a clear message before Phase
   0 runs. Resolved by
   `runner helper resolve-confidence-mode`
   (see [Script reference in SKILL.md](../SKILL.md)).
2. **Local config:** `confidence_gate_mode: strict` (or
   `advisory`) in `.claude/speckit-pro.local.md`.
3. **Default:** `advisory`.

```
1. Run confidence-gate against the workflow file
2. Read the runner envelope `status`, `data.exit_code`, and
   `data.stdout_json.recommended_action`. Valid PASS, advisory FAIL,
   and NO_DATA verdicts have runner status `ok`; strict FAIL has
   `expected_failure`. The raw domain exit code remains in
   `data.exit_code`. `input_error` means a malformed mode or threshold,
   while a missing or unreadable workflow is a file prerequisite failure.
   Do not treat advisory FAIL or NO_DATA as invalid input.
   Then route the domain verdict:
   - exit 0 (PASS, composite ≥ threshold) → proceed to G7 / Phase 7
   - exit 1 (NO_DATA, no synthesizer emit found) → soft-skip:
        log a warning and proceed. NO_DATA usually indicates a
        synthesizer-prompt regression worth reporting to the
        plugin author.
   - exit 2 (FAIL, composite < threshold):
        - advisory mode (default): log the breakdown, surface
          the lowest-scoring criterion, proceed to Phase 7
        - strict mode: STOP and surface to the operator

3. Corrective loop (both modes, shared execution-control reservation):
   - If exit 2 AND the same failure-family/spec budget permits repair:
     - If deductions_applied is true, remediate the
       unresolved CRITICAL and HIGH rows in the workflow
       file's Analysis Results table first, and record each
       fix in that row's Resolution cell. Filling the cell is
       what clears the deduction, so a fix left unrecorded
       fails the gate again on the next iteration. The
       criterion breakdown will not point at those rows: the
       synthesizer does not deduct for findings, so they
       show up in deductions, not in a low criterion.
     - Otherwise identify the lowest-scoring criterion from
       the JSON output and dispatch a focused consensus round
       on that criterion's artifacts (e.g., "Task
       understanding" low → re-evaluate spec.md ambiguity;
       "Approach clarity" low → re-evaluate plan.md TBDs)
     - Re-invoke the synthesizer's pre-Implement confidence
       emit (consensus-synthesizer agent, single fan-out)
     - Re-run confidence-gate
   - After 3 iterations OR exit 0: stop iterating
```

**Why advisory by default:** the autopilot already runs Clarify
(G2) and Analyze (G6) gates before this point, so most shakiness
is already filtered. Advisory mode surfaces the score and a
remediation hint without blocking — operators who want a
fail-closed posture opt into strict mode via local config.

### G7 — After Implement

After implementation tests, execute selected `final` formal checks and pass
`workflow_file` to `validate-gate`. Only current success or an explicit scoped
operator waiver can complete this prerequisite; generic skip-and-log cannot.

**Check:** Full verification suite passes, TDD was followed,
and no placeholder tests exist.

```
1. Run BUILD command → must pass
2. Run TYPECHECK command → must pass (skip if N/A)
3. Run LINT command → must pass
4. Run UNIT_TEST command → must pass
5. Run INTEGRATION_TEST command separately → must pass.
   Many projects exclude integration tests from the default
   test command — you MUST run both.
(use PROJECT_COMMANDS discovered in Step 0.11)
6. Verify the requirement-to-test mapping names real integration coverage:
   inspect existing or new test files and assertions, not spec-ID filenames
7. Verify requirement-linked behavioral coverage; preserve the baseline count recorded at implement entry as diagnostic,
   not a test-count growth requirement
8. Verify NO placeholder tests in new files:
   Search for placeholder test markers
        path: "specs/<number>-<name>/") → must be 0
   Search for placeholder test markers
        path: "tests/integration/*<spec-name>*") → must be 0
9. ALL must pass for G7 to pass
```

**Placeholder Test Check:** `it.todo()`, `it.skip()`,
`xit()`, `test.todo()`, and empty test bodies are NOT real
tests. They don't fail during RED and don't verify behavior
during GREEN. If ANY are found in spec-related files, G7
FAILS. The implement-executor must replace them with real
assertions.

**TDD Verification:** Each changed behavior has real RED→GREEN→refactor
evidence, with a separate result for every task and shared `tdd_unit` references
for related test/implementation checkboxes. G7 validates the aggregate commands
and effects, not a worker's GREEN label. Existing behavior may cite verified
existing coverage without fabricated RED; new behavior without meaningful
RED evidence fails. Test-only work never claims an independent GREEN cycle.

**Note:** G7 runs AFTER all Phase 7 task groups complete. Focused tests and one
independent review validate each capability group. Execute required full-suite
and artifact checks once on the final snapshot; G7 and Post consume that same
result only through `validate-execution-record` with genuine native producer
observation. Missing provenance, changed inputs, or `reusable=false` requires
rerunning affected checks; a worker summary or hash alone is insufficient.
For Docker v2, revalidate current inputs and runtime dependencies through that
same validator at G7. Post may supply the same independently retained observation,
but must validate again; a prior G7 decision is not a fresh Post decision.

**Integration Test Requirement:** Required integration coverage
MUST exist with real assertions, whether existing or new. If missing or all
placeholders, spawn implement-executor to create/fix them
before G7 can pass.

**Auto-Fix:**
- Build failures: Check for syntax errors, missing imports
- Type errors: Fix type mismatches, add missing types
- Lint errors: Run LINT_FIX command
- Test failures: Fix failing tests or implementation bugs
- Missing integration tests: Spawn implement-executor

**After G7 passes:** Validate/reuse the integration proof for Step 3.1, then apply the
final reviewability boundary before PR body generation, any `gh pr create`
variant, or `multi-pr-emission`. The runner helper
`final-reviewability-backstop` is registered as deferred for installed
workflows; do not invoke it as an active helper. Use current committed
reviewability evidence, or hold PR side effects and regenerate the committed reviewability evidence if no current evidence
exists; run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
Only `pass`, `warn`, or an honored typed-exception outcome may continue. An
unexcepted block or gate error holds PR preparation and records the
`final_reviewability_gate` state plus re-slicing packet when applicable.

**Failure Escalation:** If verification suite fails after its shared corrective cycle, run the repair loop within its allowance, then defer per the Failure Escalation Protocol. Record the specific failures.

## Gate Summary Table

| Gate | After | Check | Auto-Fix Strategy | Repair allowance |
|------|-------|-------|-------------------|--------------|
| G1 | Specify | NEEDS CLARIFICATION markers (recorded; Clarify always runs) | N/A | N/A |
| G2 | Clarify | 0 markers remain | Re-run clarify | Gate's own 2 rounds for planning documents; else Shared |
| G3 | Plan | Artifacts exist, gates pass | Re-run plan | Gate's own 2 rounds for planning documents; else Shared |
| G4 | Checklist | 0 [Gap] markers | Research + consensus remediation | Gate's own 2 rounds for planning documents; else Shared |
| G5 | Tasks | FR coverage, valid required execution metadata, and no gate task waiting on its own dependents | Generate missing tasks; split looping gate tasks | Gate's own 2 rounds for planning documents; else Shared |
| G6 | Analyze | 0 required defects (all severities) | Research + consensus remediation | Gate's own 2 rounds for planning documents; else Shared |
| G6.5 | (between Analyze and Implement) | Pre-Implement confidence ≥ 0.90 (advisory default; strict opt-in via `.claude/speckit-pro.local.md`) | Re-route consensus on lowest-scoring criterion, re-emit confidence | Shared |
| G7 | Implement | Build+type+lint+test pass, integration tests exist, 0 placeholders, TDD evidence | Fix errors, replace placeholders, create real tests | Gate's own 2 rounds for planning documents; else Shared |

A gate's own allowance admits only a remediation whose every path is a planning
document of the bound feature: `spec.md`, `plan.md`, `research.md`, `tasks.md`,
`data-model.md`, `quickstart.md`, `.process/task-execution.json`, or a
`checklists/<name>.md`. Reserve it with `gate_remediation` as
[execution-efficiency.md](execution-efficiency.md) describes. It never touches
the shared budget and needs no operator question. A remediation that touches
code, tests, formal models, `contracts/`, or any other path uses the shared
budget. The helper judges paths only, so a threshold or scope change written
inside a planning document is the orchestrator's call: reserve it on the shared
budget without `gate_remediation`.

## Additional Verification (Extension Commands)

If the `verify` extension is enabled in `.registry` (detected
in Step 0.12), run the `speckit-verify-run` skill as additional
validation alongside the standard G7 checks. This validates the
implementation against spec artifacts.

If the `verify-tasks` extension is enabled in `.registry`,
run the `speckit-verify-tasks-run` skill once, as the
`Post: Verify Tasks Phantom Check` item, to detect phantom
completions — tasks marked `[X]` that have no real
implementation behind them.

These are extension-installed skills under `.claude/skills/`,
installed by `specify extension add`. They are additive checks,
not replacements for gates. If the extension is not installed,
skip the check and log a recommendation to install it.

## Failure Escalation Protocol

A gate whose own allowance is exhausted returns `disposition=defer` with
`gate_remediation_allowance_exhausted`: it does not stop here. Record its open
findings for the end-of-run request and continue. The protocol below applies
to the shared budget.

When the shared corrective reservation is exhausted, the ledger returns
`disposition=defer` and records the blocked unit in its `deferred` list:

1. **Defer the repair.** Record the deferred gate with its failure. Never
   pass the gate, and never start work that depends on it.
2. **Continue independent work.** Keep executing every task, increment, gate,
   and Post check that does not depend on the deferred gate. It is never a
   mid-run question.
3. **Ask once, at the end.** Put the gate into the one end-of-run consolidated
   request with its context:
   - Which gate failed
   - What the specific failure is
   - What auto-fix attempts were made
   - Research findings from codebase exploration and web search (for G4/G6)

   The operator can approve one correction (`authorize-corrective-exception`)
   or a re-plan (`begin-replan-epoch`), provide a fix and resume, skip the
   gate ("Proceed anyway", logged as a deliberate override), or stop the
   autopilot.
4. **Resume** from the failed phase after the operator answers.

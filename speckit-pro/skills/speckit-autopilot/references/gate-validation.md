# Gate Validation Reference

Programmatic gate checks performed after each SDD phase. Before every repair,
use [Bounded Execution and Verification](./execution-efficiency.md): one corrective
cycle per stable failure family and two across the spec, including nested work.
No gate has an independent retry allowance. Time/budget exhaustion checkpoints
remaining work; a failed requirement or security gate never becomes a pass.

## Contents

- [Gate Definitions](#gate-definitions) — G0 (prerequisites) through G7 (post-implement), with Check + Auto-Fix + Failure Escalation per gate
- [Gate Summary Table](#gate-summary-table) — at-a-glance phase → gate → script mapping
- [Additional Verification (Extension Commands)](#additional-verification-extension-commands) — `/speckit.verify`, `/speckit.verify-tasks`
- [Failure Escalation Protocol](#failure-escalation-protocol) — when to STOP vs. retry vs. skip-and-log

## Gate Definitions

### G0 — Prerequisites (Before Specify)

**Check:** Constitution principles validated against the current codebase.

```
1. TYPECHECK command → must pass (0 errors)
2. UNIT_TEST + INTEGRATION_TEST commands → must pass (record count as baseline)
3. BUILD command → must pass
4. LINT command → must pass
(use PROJECT_COMMANDS discovered in Step 0.11)
5. Architecture patterns verified (e.g., patterns documented in CLAUDE.md)
6. Workflow file's Prerequisites table filled with baselines
7. Constitution Check summary line set to "✅ Verified"
8. Reviewability setup gate passes:
   `runner helper reviewability-gate setup <workflow-or-roadmap>`
   must be `pass`, `warn`, or a recorded `exception`; `block` stops before
   Specify and requires spec decomposition.
```

**Auto-Fix:** Not applicable — if the codebase doesn't pass typecheck/test/build, the user must fix it before starting a new spec workflow. These are foundational health checks.

**Failure Escalation:** Immediate STOP. Report which checks failed with output. The user must resolve codebase issues before autopilot can proceed.

### G1 — After Specify

**Check:** Determine if clarification is needed.

```
Search spec.md for "[NEEDS CLARIFICATION]" markers.
- If markers found → Proceed to Clarify phase
- If no markers → Skip Clarify, proceed to Plan
```

This is a routing decision, not a pass/fail gate. The presence of markers is expected and normal.

### G2 — After Clarify

**Check:** All ambiguities resolved, no human review flags.

```
1. grep -c "NEEDS CLARIFICATION" spec.md → must be 0
2. grep -c "HUMAN REVIEW NEEDED" spec.md → must be 0
3. Clarifications section exists in spec.md with documented decisions
```

**Auto-Fix:** Re-run clarify focused on remaining markers. Spawn consensus agents for each unresolved question.

**Failure Escalation:** If markers remain when the shared reservation ends, STOP. Present remaining ambiguities to human with all 3 agent perspectives.

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

For each attempt, dispatch the same Plan phase executor with the original Plan
prompt plus a `Plan Repair Context` containing the exact G3 JSON, disputed
wording, source evidence, provenance class, prior repair result, and attempt
number. The repair rules are:

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

After every completed Plan repair, run `validate-gate` for G3 again and append
the returned result to the log. Stop when G3 passes, its shared corrective
reservation ends, or when `unresolved-provenance` makes a safe repair
impossible. A skipped repair records the applicable reason rather than
fabricating an attempt.

**Failure Escalation:** If any G3 condition still fails after its reserved cycle,
or provenance cannot be established well enough to repair safely, apply the
configured `gate-failure` behavior. The default `stop` path presents the exact
gate output, disputed wording, source evidence, provenance class, repairs made,
and the remaining choice that requires human input. `skip-and-log` is a
deliberate override only: it leaves the failed G3 verdict and unresolved marker
recorded and must not rewrite their provenance.

### G4 — After Checklist

**Check:** All gap markers resolved across all checklist files.

```
1. Find all checklist files: specs/<feature>/checklists/*.md
2. Count [Gap] markers across ALL files: grep -c "\[Gap\]" checklists/*.md
3. Total must be 0
```

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

Step 5: If gaps remain when the shared reservation ends → STOP, present
  to human with the gap description, research findings,
  and attempted fixes
```

**Why research + consensus:** Gaps often require understanding
both what the codebase already does (codebase exploration) AND what
the API/standard requires (via web search). Using multiple research
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

**Check:** Every functional requirement has at least one task.

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
   verdict, and any operator-ratified split decision in the workflow file.
6. Apply the post-G5 reviewability proceed/stop matrix below to that
   committed evidence. A valid current size-only `status=block` continues
   into marker planning and later marker emission; it is not a manual
   re-slicing stop.
```

**Auto-Fix:** For each unmapped FR:
- Generate a task that covers the requirement
- Place it in the appropriate user story phase
- Ensure it has the correct FR reference marker

**Failure Escalation:** If coverage gaps persist after the reserved cycle, STOP. Present the unmapped FRs with the relevant spec sections.

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

Step 5: If required findings remain when the reservation ends → STOP, present
  to human with all remaining findings, research results,
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
   `/speckit-pro:speckit-autopilot` (or `$speckit-autopilot` in Codex)
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
2. Read exit code + JSON output:
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
       synthesizer no longer deducts for findings, so they
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
7. Verify requirement-linked behavioral coverage; preserve G0 count as diagnostic,
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
reviewability evidence or stop before PR side effects if no current evidence
exists.
Only `pass`, `warn`, or an honored typed-exception outcome may continue. An
unexcepted block or gate error stops PR preparation and records the
`final_reviewability_gate` state plus re-slicing packet when applicable.

**Failure Escalation:** If verification suite fails after its shared corrective cycle, STOP. Present the specific failures to human.

## Gate Summary Table

| Gate | After | Check | Auto-Fix Strategy | Repair allowance |
|------|-------|-------|-------------------|--------------|
| G1 | Specify | NEEDS CLARIFICATION markers | N/A (routing) | N/A |
| G2 | Clarify | 0 markers remain | Re-run clarify | Shared |
| G3 | Plan | Artifacts exist, gates pass | Re-run plan | Shared |
| G4 | Checklist | 0 [Gap] markers | Research + consensus remediation | Shared |
| G5 | Tasks | FR coverage and valid required execution metadata | Generate missing tasks | Shared |
| G6 | Analyze | 0 required defects (all severities) | Research + consensus remediation | Shared |
| G6.5 | (between Analyze and Implement) | Pre-Implement confidence ≥ 0.90 (advisory default; strict opt-in via `.claude/speckit-pro.local.md`) | Re-route consensus on lowest-scoring criterion, re-emit confidence | Shared |
| G7 | Implement | Build+type+lint+test pass, integration tests exist, 0 placeholders, TDD evidence | Fix errors, replace placeholders, create real tests | Shared |

## Additional Verification (Extension Commands)

If the `verify` extension is enabled in `.registry` (detected
in Step 0.12), run the `speckit-verify-run` skill as additional
validation alongside the standard G7 checks. This validates the
implementation against spec artifacts.

If the `verify-tasks` extension is enabled in `.registry`,
run the `speckit-verify-tasks-run` skill to complement G5 by detecting
phantom completions — tasks marked `[X]` that have no real
implementation behind them.

These are extension-installed skills under `.claude/skills/`,
installed by `specify extension add`. They are additive checks,
not replacements for gates. If the extension is not installed,
skip the check and log a recommendation to install it.

## Failure Escalation Protocol

When the shared corrective reservation or time budget is exhausted:

1. **STOP** execution — do not proceed to the next phase
2. **Present context** to human:
   - Which gate failed
   - What the specific failure is
   - What auto-fix attempts were made
   - Research findings from codebase exploration and web search (for G4/G6)
3. **Wait for guidance** — the human can:
   - Provide a fix and resume: "Fix X, then continue"
   - Skip the gate: "Proceed anyway" (logged as a deliberate override)
   - Abort: "Stop the autopilot"
4. **Resume** from the failed phase after human intervention

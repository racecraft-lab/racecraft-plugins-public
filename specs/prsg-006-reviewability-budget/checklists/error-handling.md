# Error-Handling & Failure-Mode Checklist: Plan-phase reviewability budget + gate rework (PRSG-006)

**Purpose**: Validate that the error-handling, fail-closed, and graceful-degradation
*requirements* are complete, clear, consistent, and measurable — before implementation.
This is a "unit test for the requirements," not a test of the scripts themselves.

**Created**: 2026-06-06

**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [contracts/](../contracts/)

**Depth**: Formal release gate (fail-closed security-adjacent behavior + autonomous-run safety)

**Audience**: Spec author + reviewer (pre-implementation requirements quality)

## Fail-Closed Exception Matching (FR-011 / FR-012)

- [ ] CHK001 - Is the canonical exception matcher specified as an exact, copy-pastable regex with anchoring, case-sensitivity, and trailing-content rejection all stated? [Clarity, Spec §FR-011]
- [ ] CHK002 - Is the closed class set `{refactor, infra, upgrade}` defined as exhaustive, with a requirement that any class outside it is NOT honored? [Completeness, Spec §FR-012]
- [ ] CHK003 - Are requirements defined for each fail-closed bypass case (class outside set; partial/extended `refactoring`/`ref`/`refactor,infra`; case variant `Refactor`/`REVIEWABILITY-EXCEPTION:`; trailing content `refactor # ok`; no space after colon)? [Coverage, Spec §Edge Cases]
- [ ] CHK004 - Is it required that a pragma on a context (unchanged) or removed (`-`) diff line MUST NOT flip the result? [Completeness, Spec §FR-012]
- [ ] CHK005 - Is it required that a pragma appearing only in the PR description or a commit message MUST NOT be honored (mutable, non-version-bound sources excluded)? [Completeness, Spec §FR-012]
- [ ] CHK006 - Is the requirement that the unified-diff `+++ b/<file>` header line cannot itself satisfy the matcher stated, with the added-line isolation sequence specified? [Clarity, Spec §FR-012]
- [ ] CHK007 - Is the positive case (a valid pragma on an added `+` line of a committed `.md` file in range flips `block`) stated as an explicit requirement, not only implied by the negatives? [Completeness, Spec §FR-011]
- [ ] CHK008 - Is the "introduced by the PR being gated" semantic (branch-introduced added line honored vs. base-branch context line not honored over `merge-base..HEAD`) stated unambiguously? [Clarity, Spec §FR-012]
- [ ] CHK009 - Is the single-shared-matcher requirement (one function reused across `setup`/`tasks`/`diff`, POSIX ERE via `grep -E`, never bash `[[ =~ ]]`) stated to prevent per-mode regex drift? [Consistency, Spec §FR-011 §FR-012]
- [ ] CHK010 - Is the legacy three-phrase keyword removal required across ALL three modes, with an explicit statement that no mode may silently retain the legacy matcher or lose its exception path? [Consistency, Spec §FR-013]
- [ ] CHK011 - Is the both-present case (a document carrying a legacy phrase AND a valid typed pragma) resolved unambiguously (typed pragma honored, legacy ignored either way)? [Consistency, Spec §Edge Cases]
- [ ] CHK012 - Is the case-sensitivity fail-direction stated as deliberate (a mis-cased class denies a legitimate exception rather than granting an unearned pass)? [Clarity, Spec §FR-011]
- [ ] CHK013 - Is the fenced-code-block / inline-code pragma residual recorded as a known limitation (line-scoped matcher WOULD flip) rather than left as an undocumented hole, and is its deferral target (PRSG-010) named? [Edge Case, Spec §Assumptions §Edge Cases]
- [ ] CHK014 - Is the template's literal placeholder `Reviewability-Exception: <class>` required to remain a non-enum example so setup-mode parsing of the template never honors the documentation example as a live exception? [Edge Case, Contract reviewability-gate.output.md]

## Estimator Exit-Code Contract (FR-003 / FR-004 / FR-007)

- [ ] CHK015 - Are the estimator's exit codes defined for every status — `pass`, `over_budget`, and `not_estimated` all return exit 0 (non-blocking)? [Completeness, Contract estimate-reviewable-loc.output.md]
- [ ] CHK016 - Is it stated as a requirement that the budget verdict NEVER drives the exit code (the verdict lives in JSON `status`, exit 0 carries all three statuses)? [Clarity, Contract estimate-reviewable-loc.output.md]
- [ ] CHK017 - Is the absence of an exit `1` from the estimator stated as a deliberate contract difference from the gate (the estimator does not block), not an omission? [Clarity, Contract estimate-reviewable-loc.output.md]
- [ ] CHK018 - Is exit `2` defined for the estimator's usage errors (missing/extra args) AND unreadable/absent input file, as a path distinct from `not_estimated`? [Completeness, Contract estimate-reviewable-loc.output.md]
- [ ] CHK019 - Does a spec-level requirement (not only the contract) state what the estimator returns for a malformed/unreadable/absent `plan.md` versus an absent declared-files block — i.e., are the file-level IO-error case (non-zero exit) and the content-level missing-block case (`not_estimated`, exit 0) BOTH covered in the spec body, told as one consistent story? [Resolved — Spec §FR-003 now distinguishes the content-level missing-block case (`not_estimated`, exit 0) from the file-level error case (absent/unreadable file or usage error → non-zero exit), deferring the literal "2" to contracts/estimate-reviewable-loc.output.md]
- [ ] CHK020 - **Is there a requirement that an estimator non-zero exit (usage/IO error, exit 2) does NOT crash the autonomous plan phase under `set -euo pipefail` — i.e., is the plan-phase invocation required to handle a non-zero estimator exit non-fatally so the run never crashes?** [Resolved — Plan §Plan-phase wiring now requires the wiring to read the exit code and guard the invocation against `errexit` (capture the exit code, record an "estimator could not run" note, continue), mirroring the established gate-handling pattern in phase-execution.md; Spec §Edge Cases adds a peer case making advisory-and-never-crash the invariant for every estimator outcome]
- [ ] CHK021 - Is the gate's existing exit-code contract (0 within-budget, 1 block, 2 usage/unreadable) required to remain UNCHANGED, with that invariant stated rather than assumed? [Consistency, Contract reviewability-gate.output.md, Spec §FR-007]

## Over-Budget Handling at Plan Phase (FR-004 / FR-005)

- [ ] CHK022 - Is the autonomous-run over-budget behavior specified as record-and-proceed with an explicit "MUST NOT block the run or trigger re-slicing"? [Completeness, Spec §FR-004]
- [ ] CHK023 - Is "never blocks or prompts mid-run" stated for the autonomous over-budget path, and does it also cover "never crashes" (advisory non-blocking includes not aborting on a non-zero exit)? [Clarity, Spec §Edge Cases §FR-004]
- [ ] CHK024 - Is the interactive over-budget behavior (surface a decision to the human) specified distinctly from the autonomous path, so the two modes are not conflated? [Consistency, Spec §FR-005]
- [ ] CHK025 - Is the boundary between PRSG-006 (advisory record-and-proceed) and PRSG-010 (blocking / re-slicing) stated so an over-budget result is unambiguously non-blocking in this spec? [Consistency, Spec §Out of Scope]
- [ ] CHK026 - Is the destination of the over-budget record specified (which artifact: `plan.md` and/or the workflow record) clearly enough to be verifiable? [Clarity, Spec §FR-004]

## Graceful Degradation: Malformed / Empty / Unreadable plan.md (FR-002 / FR-003)

- [ ] CHK027 - Is the `not_estimated` state defined as distinct from a within-budget `pass`, with the vacuous-pass failure mode it prevents stated as the rationale? [Completeness, Spec §FR-003 §Edge Cases]
- [ ] CHK028 - Is `not_estimated` required to set `projected: null` (never a number that could read as within-budget)? [Clarity, Contract estimate-reviewable-loc.output.md, Spec §FR-003]
- [ ] CHK029 - Is the trigger condition for `not_estimated` specified precisely (no `## Declared File Operations` block, OR zero lines matching the entry grammar) so "absent" is binary, not fuzzy? [Clarity, Spec §Edge Cases, Plan §Decision 1]
- [ ] CHK030 - Is determinism required to hold for the degraded path too (the same unparseable/empty input always yields the same `not_estimated` record)? [Consistency, Spec §Edge Cases §FR-002]
- [ ] CHK031 - Is the determinism fixture required to assert a KNOWN expected value (parsed count AND projected LOC) against a representative non-empty block — not merely two-run equality — so the fixture cannot pass while measuring nothing? [Measurability, Spec §FR-002]
- [ ] CHK032 - Is the empty-input edge case (a block present but every line failing the grammar) covered by the same `not_estimated` rule as a wholly absent block, with no third undefined outcome? [Edge Case, Spec §Edge Cases]
- [ ] CHK033 - Is the under-counting known limitation (`is_production_file` does not match this repo's `.sh` plugin paths, so plugin-script slices project `production: 0`) recorded as a requirement-to-document-in-code rather than an unrecorded surprise? [Assumption, Spec §Assumptions, Contract estimate-reviewable-loc.output.md]

## Boundary: Surface-Count Downgrade (FR-010)

- [ ] CHK034 - Is it required that a primary-surface count greater than one produces a warning and NOT a block, with the blocker behavior explicitly removed? [Completeness, Spec §FR-010]
- [ ] CHK035 - Is there a requirement that NO error/block path still treats surface count > 1 as a blocker (the surface-count blocker is removed from every code path, not merely from the happy path)? [Consistency, Spec §FR-010, Contract reviewability-gate.output.md]
- [ ] CHK036 - Is the JSON output required to continue reporting `primary_surface_count` and the `primary_surfaces` list for downstream consumers after the downgrade? [Completeness, Spec §FR-010]
- [ ] CHK037 - Is the measurable outcome stated that a multi-surface slice produces 0 blocks attributable to surface count while still producing a surface-count warning? [Measurability, Spec §SC-004]

## Cross-Cutting Consistency & Determinism

- [ ] CHK038 - Is the production-only LOC recount required to apply consistently in BOTH the gate's `diff` mode and the plan-phase estimator (so the two never disagree on what counts)? [Consistency, Spec §FR-008]
- [ ] CHK039 - Is the greenfield predicate's file-set rule stated identically for the estimator (all declared entries `NEW`) and the gate (all non-excluded changed paths add-status `A`), including the `--no-renames` pin so ambient `diff.renames` config cannot vary the boolean? [Consistency, Spec §FR-006 §FR-009]
- [ ] CHK040 - Is the keep-in-sync requirement for the shared per-file production-LOC constant stated (copied-comment convention guarding drift between estimator and gate)? [Consistency, Spec §FR-007]
- [ ] CHK041 - Is the legacy-keyword removal documented as a backward-incompatible break (new-specs-only, no deprecation window) and handed to PRSG-011, so the break is auditable rather than silent? [Traceability, Spec §FR-013]

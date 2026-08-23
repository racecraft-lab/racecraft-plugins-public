# Implementation Notes: G56R-005

### T001

**Deviations/Edge cases/Surprises:** Implementation agents could not complete writes while bound from the inherited checkout, so the orchestrator applied the three schemas directly in the explicitly authorized feature worktree. TDD is not applicable to this contract-only seed task; JSON parsing and `git diff --check` passed.

### T002

**Deviations/Edge cases/Surprises:** The reviewed source-roster identity is derived from 10 required-core TOMLs plus the sole optional helper, `autopilot-fast-helper.toml`; 32 required scenario labels are covered by 22 independently addressable seed cases. TDD is not applicable to this fixture-only seed task; roster bytes, classifications, identity, and coverage equality were validated directly.

### T003

**Deviations/Edge cases/Surprises:** RED was observed exactly as intended: two contract/corpus tests pass while the roster identity and drift tests fail because `codex_route_fallback.py` does not exist yet.

### T004

**Deviations/Edge cases/Surprises:** Registered the focused test once in Layer 4 after preserving the first RED result; manifest JSON, unique registration, target existence, and `git diff --check` passed.

### T005

**Deviations/Edge cases/Surprises:** RED expanded from the missing resolver to six deterministic route cases covering preferred absence, fixed six-reason order, availability/treatment failures, exhaustion, loop-on-arrival, and strict override short-circuiting.

### T006

**Deviations/Edge cases/Surprises:** GREEN added a Codex-local pure resolver and roster binding without importing the frozen Claude resolver or extracting shared logic. The first GREEN run exposed an invalid test assertion that confused the `qualified_route` data field with a terminal value; the assertion was narrowed to the singular `terminal_outcome` field and the focused suite passed.

### T007

**Deviations/Edge cases/Surprises:** Three canonical replays are byte-identical and exclude the repository path. The first Layer 4 safety-net run reported 84 failures caused by the inherited task sandbox denying test fixture writes in the externally bound worktree; a representative failing test passed when rerun with exact-worktree write permission. Full escalated verification remains scheduled for T022/T023.

### T008

**Deviations/Edge cases/Surprises:** Added approved and unapproved service rows plus RED assertions proving service attribution must remain outside plugin diagnostics and scoring must be reported separately.

### T009

**Deviations/Edge cases/Surprises:** Attribution normalization now fails closed when the target is undeclared or the non-route treatment digest changes. The intermediate focused run left only the expected unapproved-scoring RED failure.

### T010

**Deviations/Edge cases/Surprises:** Scoring eligibility now requires both a qualified plugin route and no unapproved service attribution; route qualification remains a separate fact.

### T011

**Deviations/Edge cases/Surprises:** Added one canonical digest over all eight named non-route treatment fields. Model/effort-only changes preserve the digest; instruction changes and mismatched candidate digests fail closed.

### T012

**Deviations/Edge cases/Surprises:** Optional-helper unavailability records a separate zero-attempt counter and permits required-core success only for an explicitly qualified no-helper continuation. Unqualified continuation stops before required-route success.

### T013

**Deviations/Edge cases/Surprises:** RED covered real-home, traversal, symlink, immutable seed, prewrite atomicity, partial-write rollback, cleanup failure, previous-known-good preservation, and rollback failure. All writes use harness-created temporary roots only.

### T014

**Deviations/Edge cases/Surprises:** Fake-home identity is canonical JSON over sorted relative paths, content SHA-256, numeric mode text, and role classification; marker paths, absolute roots, mtimes, inodes, and timestamps are excluded.

### T015

**Deviations/Edge cases/Surprises:** The staged adapter snapshots exact pre-state bytes and modes, validates the sole agents boundary before staging, rolls back every touched managed file on late failure, and reports cleanup independently. Simulated rollback failure intentionally preserves evidence of residual writes and deterministic remediation.

### T016

**Deviations/Edge cases/Surprises:** The sole optional-helper classification is bound to the checked-in filename, name, `gpt-5.3-codex-spark` model, and read-only sandbox. Roster membership, classifications, source bytes, and canonical identity continue to fail closed on drift.

### T017

**Deviations/Edge cases/Surprises:** RED covered retry, deterministic elapsed units, fan-out, context, cancellation, escalation, HITL, recursion, inherited fields, generic substitution, and unqualified-adjacent routes. Corpus budget evidence remains counter-based and contains no wall-clock input.

### T018

**Deviations/Edge cases/Surprises:** One sequential harness enforces strict override first, then bounded counters and cancellation before route success. Fan-out above one, recursion, and HITL are rejected without dispatch; cancellation after mutation invokes only the bounded fake-home recovery path.

### T019

**Deviations/Edge cases/Surprises:** Canonical harness output excludes the temporary root, real home, mtimes, inodes, timestamps, and temporary-root metadata while retaining deterministic relative action paths.

### T020

**Deviations/Edge cases/Surprises:** The fixture corpus now maps every FR-001 through FR-022 and SC-001 through SC-009 to a named contract, case, or focused test. Scope-preservation assertions forbid Claude resolver imports and live-availability wording.

### T021

**Deviations/Edge cases/Surprises:** Focused verification passed 33/33 tests after the Post review contract remediation.

### T022

**Deviations/Edge cases/Surprises:** Layer 4 passed 5998/5998 with exact-worktree fixture-write permission. The earlier sandbox-denied result is superseded by this clean run.

### T023

**Deviations/Edge cases/Surprises:** The full deterministic suite passed 7659/7659: Layer 1 1469/1469, Layer 4 5998/5998, and Layer 5 192/192.

### T024

**Deviations/Edge cases/Surprises:** Spec-index regeneration changed only the feature SPEC-MOC and recheck passed. Docs references generated 7 pages and `reference:check` passed. After checkpointing the expected generated docs page, isolated release-artifact regeneration passed and proved payload, version, marketplace, and release evidence remained current.

### T025 — PR Packet Evidence

- **What changed:** Added three closed schemas, one reviewed roster-bound corpus, one Codex-local pure resolver/fake-home adapter/sequential harness, one focused unit module, and Layer 4 registration.
- **Why:** Freeze deterministic G56R-005 evidence before any G56R-006 production routing or installer wiring.
- **Non-goals:** No production routing, real-home install, live model/service qualification, payload/version/release change, checkpoint/resume change, shared resolver extraction, or Claude/G56R-004 behavior edit.
- **Review order:** Schemas → corpus/roster → `codex_route_fallback.py` → focused tests → suite manifest → generated docs/spec index.
- **Traceability:** Corpus `traceability` covers all 22 FRs and 9 SCs; focused verification passed 33/33 after review remediation.
- **Verification:** Layer 4 5998/5998; full deterministic suite 7659/7659; docs reference and spec-index checks pass. Live model/service smoke was not run by design.
- **Rollback:** Remove the new simulation files and focused-test registration, then regenerate the docs reference and spec index.

### Post Review Remediation

**Finding:** Independent review found that the route-policy schema constrained
`declaration_source` to `local` while the resolver intentionally rejects four
non-local declaration sources.

**RED:** Added `test_route_policy_declares_every_supported_declaration_source`;
the focused suite failed with `KeyError: 'enum'` (32 pass, 1 error).

**GREEN:** Replaced the single-value contract with the closed five-value enum
`local`, `inherited_model`, `inherited_effort`, `generic_substitution`, and
`unqualified_adjacent`. Focused verification passed 33/33 and the final full
suite passed 7659/7659.

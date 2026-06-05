# Error-Handling Checklist: Artifact relocation — tiering, .process/, collapse

**Purpose**: Validate the quality, completeness, and consistency of the requirements that govern failure, degradation, and re-run behavior during artifact relocation — specifically the consumer ensure-step's idempotency (re-run = no-op; line appended only if absent), the create-vs-append branching when the consuming repo has no `.gitattributes`, the gate arm's safe degradation when no `.process/` paths exist (no false exclusions), and the hard invariant that an existing consumer `.gitattributes` is never corrupted.
**Created**: 2026-06-05
**Feature**: [spec.md](../spec.md)

**Note**: These items are "unit tests for the requirements" — they test whether the spec/plan are written correctly for the error/degradation/idempotency paths, NOT whether the implementation works. This domain deliberately covers the *false-exclusion / no-op-degradation / idempotency / non-corruption* angle; the *false-inclusion / scoping-correctness* angle is owned by `data-integrity.md` (cross-referenced where the two meet).

## Consumer Ensure-Step Idempotency (Re-Run = No-Op)

- [ ] CHK001 - Is the idempotency contract for the consumer `.gitattributes` ensure-step stated as a hard requirement — re-running the scaffold MUST leave exactly one copy of the `.process/` rule (no duplicate, no second append)? [Completeness, Spec §FR-009/SC-004]
- [ ] CHK002 - Is the *detection condition* that makes the append a no-op specified — i.e., HOW the ensure-step decides the rule is "already present" (the line is already in the file) so the second run appends nothing? [Clarity, Spec §FR-009]
- [ ] CHK003 - Does the spec address whitespace/trailing-newline variance in the presence check, so a rule that already exists with a differing trailing newline or surrounding blank line is still recognized as present (not re-appended as a near-duplicate)? [Edge Case, Spec §FR-009/SC-004]
- [ ] CHK004 - Is SC-004's idempotency claim ("re-running the scaffold leaves exactly one copy of the rule") expressed as an objectively-verifiable outcome (exactly-one-occurrence count), rather than a directional "does not duplicate" statement? [Measurability, Spec §SC-004]

## Create vs Append Branching (Consumer Has No `.gitattributes`)

- [x] CHK005 - Does the spec define the behavior when the consuming repo has NO `.gitattributes` file at all — i.e., the ensure-step MUST create the file (with the `.process/` rule) rather than fail or skip? [Completeness, Spec §FR-009, Edge Cases] — RESOLVED: FR-009 clause (a) now requires the ensure-step to create the repository-root `.gitattributes` containing the rule when the file is absent.
- [ ] CHK006 - Does the spec define the behavior when the consuming repo already HAS a `.gitattributes` — i.e., the ensure-step appends the rule (subject to the idempotency check) rather than overwriting the file? [Clarity, Spec §FR-009]
- [ ] CHK007 - Are the create-branch and append-branch each specified to converge on the same end state (the consumer `.gitattributes` contains exactly one `.process/` collapse rule), so neither branch is left as an undefined or divergent outcome? [Consistency, Spec §FR-009/SC-004]

## Gate Degrades Safely — No False Exclusions

- [x] CHK008 - Does the spec state the inverse of the exclusion as an invariant — a changed path that has NO `/.process/` segment MUST NOT be excluded from the reviewable-LOC accounting (no false exclusion)? [Completeness, Spec §FR-010/FR-011] — RESOLVED: FR-010 now states the inverse invariant explicitly — a path with no `/.process/` segment MUST NOT be excluded.
- [ ] CHK009 - Does the spec define the gate's behavior when a change contains ZERO `.process/` paths — the new exclusion arm degrades to a no-op and the reviewable-LOC count is unchanged from its pre-feature value? [Edge Case, Spec §FR-010]
- [ ] CHK010 - Is the no-false-exclusion property traceable to the same `/.process/`-segment-only matching rule that protects CONTRACT files (cross-ref `data-integrity.md` CHK002/CHK008), so "degrades safely" is anchored to a stated rule rather than assumed? [Consistency, Spec §FR-010/FR-011]

## Never Corrupt an Existing Consumer `.gitattributes`

- [x] CHK011 - Is the non-corruption guarantee stated as a hard invariant — the ensure-step MUST preserve every pre-existing line of the consumer `.gitattributes` and only append, never truncate, rewrite, or reorder existing content? [Completeness, Spec §FR-009] — RESOLVED: FR-009 clause (c) now states the edit MUST be append-only, preserving every pre-existing line byte-for-byte and never truncating, rewriting, or reordering.
- [x] CHK012 - Does the spec address the partial-write / interrupted-run failure mode for the consumer `.gitattributes` edit, so an interrupted ensure-step cannot leave the file truncated or half-written (the write is safe)? [Completeness, Spec §FR-009, Exception Flow] — RESOLVED (requirement stated; mechanism flagged for consensus): a new Edge Cases bullet ("The consumer `.gitattributes` write is interrupted partway") requires that an interrupted run MUST NOT leave a partial/truncated/corrupted file and that a re-run completes idempotently. The CONCRETE safe-write technique is deferred to plan/tasks and flagged in the Unresolved-for-consensus section, because the existing precedent (`ensure-reviewability-preset.sh`) writes via a full Python `write_text` rewrite, which is NOT interruption-safe and would need temp-file+rename to satisfy this invariant.
- [ ] CHK013 - Are the requirements consistent that the consumer `.gitattributes` edit is purely additive and reversible (the append is the only mutation; revert removes only the added rule), aligning with the no-deletion / no-mutation posture of the feature? [Consistency, Spec §FR-009/FR-013]

## Notes

- Items carrying a gap marker indicate a missing or under-specified requirement that may need a spec/plan edit before implementation.
- The four locked scope decisions (linguist-generated only; new-specs-only; gate hardcodes the `.process/` glob; extension-authored exhaust out of scope) are treated as decided — items here test that the failure/degradation/idempotency behavior under those decisions is clearly captured, NOT that scope should expand.
- This checklist's angle is false-exclusion / no-op-degradation / idempotency / non-corruption. The complementary false-inclusion / scoping-correctness angle is owned by `data-integrity.md`.

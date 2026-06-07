# Data-Integrity Checklist: Vertical-slice sizing heuristics in PRD/grill-me (PRSG-005)

**Purpose**: Validate that the requirements governing the deterministic estimator's
data integrity — its input→output contract, the single-source-of-truth ceiling, the
`ok|warn` status enum, the at-ceiling boundary, the `suggested_slices` rounding, the
spike triple, robustness on bad input, and the advisory-only invariant — are complete,
unambiguous, consistent, and measurable before implementation.
**Created**: 2026-06-06
**Feature**: [spec.md](../spec.md)

**Note**: These items test the QUALITY of the requirements (are they well-written?), not
the behavior of the estimator (does the code work?). Implementation and tests are out of
scope for this pass.

## Determinism & Reproducibility

- [ ] CHK001 - Is the determinism requirement (identical inputs → byte-identical output)
  stated unambiguously, including the explicit exclusion of clocks, randomness, and
  environment dependence? [Clarity, Spec §FR-007]
- [ ] CHK002 - Is "byte-identical" defined consistently across spec, plan, data-model, and
  contract (not loosely paraphrased as "same" in one place and "byte-identical" in another)?
  [Consistency, Spec §FR-007 / Contract §Behavior rules 1]
- [ ] CHK003 - Is the determinism guarantee paired with a measurable acceptance criterion
  (repeated runs on identical inputs compared byte-for-byte)? [Measurability, Spec §SC-003]

## Single Source-of-Truth Ceiling

- [ ] CHK004 - Is the requirement that the ~400-LOC ceiling is a single source-of-truth
  constant stated, and is the set of all artifacts that must refer to the same value
  (estimator, both skills, shared reference doc) enumerated? [Completeness, Spec §FR-008]
- [ ] CHK005 - Is the anti-drift expectation explicit — i.e. that no second hardcoded copy
  of the ceiling may exist that could diverge — rather than merely implied? [Clarity, Spec §FR-008 / Plan §Estimator contract]
- [ ] CHK006 - Is the relationship between the in-script ceiling constant and the prose value
  in `slicing-heuristics.md` specified as a keep-in-sync obligation (which is authoritative,
  how they stay aligned)? [Consistency, Data-model §Documented LOC ceiling]
- [ ] CHK007 - Is it stated that the ceiling is shared with PRSG-006 by documentation only
  (no consumed artifact), so the constant has exactly one runtime owner? [Clarity, Spec §Assumptions / Key Entities]

## Status Enum Integrity (`ok|warn`)

- [ ] CHK008 - Is the `status` field constrained to EXACTLY the two values `ok` and `warn`,
  with an explicit prohibition on ever introducing a third value? [Clarity, Spec §FR-006 / §FR-017]
- [ ] CHK009 - Is the no-third-value constraint stated consistently in every artifact that
  describes the output (spec, data-model, contract) rather than only in one? [Consistency, Spec §FR-017 / Data-model §Size estimate / Contract §Output]
- [ ] CHK010 - Is there a measurable check that `status` is never any value other than `ok`
  or `warn` across all input classes (normal, boundary, spike, malformed)? [Measurability, Contract §Verification]

## At-Ceiling Boundary

- [ ] CHK011 - Is the at-ceiling rule pinned unambiguously — `status = ok` when
  `estimated_loc == ceiling`, `warn` only when `estimated_loc` is STRICTLY greater than the
  ceiling? [Clarity, Spec §Edge Cases / §FR-006]
- [ ] CHK012 - Is the boundary rule stated identically in spec Edge Cases, data-model, plan,
  and contract (no off-by-one disagreement between "at or over" vs "strictly over")?
  [Consistency, Data-model §State/boundary rules / Contract §Behavior rules 2]
- [ ] CHK013 - Is the boundary covered by a measurable acceptance criterion at exactly the
  ceiling AND just over it? [Measurability, Spec §SC-003 / Contract §Verification]

## `suggested_slices` Rounding

- [ ] CHK014 - Is the `suggested_slices` formula specified exactly (`ceil(estimated_loc /
  ceiling)`, minimum 1) rather than described vaguely? [Clarity, Plan §Estimator contract / Contract §Behavior rules 4]
- [ ] CHK015 - Is the integer-rounding behavior pinned AT the boundary (e.g. exactly at the
  ceiling → 1) and AROUND it (just over → 2), so the ceil semantics are unambiguous?
  [Coverage, Edge Case, Contract §Verification]
- [ ] CHK016 - Is the minimum value of `suggested_slices` (≥ 1, including the zero/empty
  input case) stated so it can never be 0? [Completeness, Data-model §Size estimate]

## Spike Case (FR-017)

- [ ] CHK017 - Is the spike behavior pinned as an exact output triple
  (`estimated_loc: 0`, `suggested_slices: 1`, `status: ok`) with the LOC-threshold comparison
  skipped? [Clarity, Spec §FR-017 / Contract §Behavior rules 3]
- [ ] CHK018 - Is the semantic meaning of `status: ok` for a spike explicitly defined as
  "LOC sizing is not applicable" (not "trivially small"), so the value is not misread?
  [Ambiguity, Spec §FR-017 / §Edge Cases]
- [ ] CHK019 - Is it explicit that the spike path introduces no new status value and does not
  trip a misleading `warn`, preserving the enum and advisory-only invariants? [Consistency, Spec §FR-017]

## Robustness on Bad Input (FR-016)

- [ ] CHK020 - Are the malformed/missing/zero/negative input classes each enumerated with a
  defined normalization rule (missing → 0, negative → clamped non-negative, malformed →
  predictable value)? [Completeness, Data-model §Validation/robustness rules]
- [x] CHK021 - Is the resulting `status` for bad-input cases actually pinned to a specific
  value (`ok` vs `warn`)? RESOLVED: spec §FR-016 + Edge Cases, plan §Robustness, data-model
  §Validation rules, and contract §Behavior rule 5 now pin all bad/missing/negative/malformed
  signals to normalize to `0`, yielding `estimated_loc: 0` with `status: ok` by the same
  at-ceiling boundary rule — no third value, no gate logic. [Resolved, Spec §FR-016 / Contract §Behavior rules 5]
- [ ] CHK022 - Is "non-crashing" specified in a way that cannot be confused with a blocking
  error exit — i.e. the estimator returns a normal result rather than raising a hard error?
  [Clarity, Data-model §Validation/robustness rules / Contract §Behavior rules 5]

## Output ↔ Consumer Consistency (no Budget drift)

- [ ] CHK023 - Is the requirement that the `Budget: ~N LOC` line `speckit-prd` writes reflects
  the estimator's `estimated_loc` (no drift between the written number and the returned value)
  stated explicitly? [Clarity, Spec §FR-002]
- [ ] CHK024 - Is the rule that both skills invoke the SAME single copy of the estimator
  (so both consume identical output for identical signals) specified? [Consistency, Spec §FR-009 / Plan §Codex-parity plan]
- [ ] CHK025 - Is the output JSON shape (`{estimated_loc, suggested_slices, status}`) and its
  field types defined once and referenced consistently by every consumer surface? [Consistency, Data-model §Size estimate / Contract §Output]

## Advisory-Only Invariant (no gate/exit-code/threshold)

- [ ] CHK026 - Is it explicit that a `warn` status is informational only and that no path —
  including robustness/error paths — emits gate, threshold, blocking, or non-zero/exit-code
  logic? [Clarity, Spec §FR-011 / Contract §Output]
- [ ] CHK027 - Is the advisory-only invariant stated consistently for both the normal `warn`
  case AND the estimator-unavailable / bad-input degradation cases (both degrade to advisory
  text, never a hard stop)? [Consistency, Spec §FR-011 / §Edge Cases]
- [ ] CHK028 - Is there a measurable success criterion that no PRSG-005 path blocks, gates, or
  rejects in any scenario? [Measurability, Spec §SC-004]

## Notes

- Check items off as completed: `[x]`
- Items carrying a Gap marker indicate a requirement that is missing or only loosely
  specified and needs a spec/plan/contract edit before implementation.
- Traceability: at least 80% of items cite a spec section or a quality marker
  (Gap / Ambiguity / Consistency / Clarity / Measurability).

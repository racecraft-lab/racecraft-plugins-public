# Error-Handling Checklist: Vertical-slice sizing heuristics in PRD/grill-me (PRSG-005)

**Purpose**: Validate that the requirements governing PRSG-005's error/degradation behavior —
the estimator's non-crashing response to malformed/missing/zero/negative inputs, the SPIDR
"Spike" near-zero-LOC case, the grill-me slice-sizing branch when the estimate is borderline
or the estimator is unavailable, and the cross-surface "never convert a `warn` or an
unavailable estimate into a hard stop" invariant — are complete, unambiguous, consistent, and
measurable before implementation.
**Created**: 2026-06-06
**Feature**: [spec.md](../spec.md)

**Note**: These items test the QUALITY of the requirements (are they well-written?), not the
behavior of the estimator or the skills (does the code work?). Implementation and tests are out
of scope for this pass. This is the error-handling sibling to `data-integrity.md`; where an
item overlaps an already-locked data-integrity requirement it is resolved by citation rather
than re-edited.

## Estimator Non-Crash on Bad Input (FR-016)

- [ ] CHK001 - Is the requirement that the estimator is NON-CRASHING on malformed, missing,
  zero, and negative size signals stated explicitly (rather than only implied by "predictable
  behavior")? [Clarity, Spec §FR-016 / Edge Cases]
- [ ] CHK002 - Is "non-crashing" specified in a way that cannot be confused with a blocking
  error exit — i.e. the estimator returns a normal JSON result rather than raising a hard error
  or emitting a non-zero "block" exit? [Clarity, Data-model §Validation/robustness / Contract §Behavior rules 5]
- [ ] CHK003 - Is the bad-input normalization rule (each malformed/missing/zero/negative signal
  → `0`) stated consistently across spec, plan, data-model, and contract (not paraphrased
  divergently)? [Consistency, Spec §FR-016 / Contract §Behavior rules 5]
- [ ] CHK004 - Is the resulting `status` for the all-bad/all-absent input case pinned to a
  specific value (`estimated_loc: 0` → `status: ok`, by the at-ceiling rule), with no third
  value and no misleading `warn`? [Completeness, Spec §FR-016 / Data-model §Validation rules]
- [ ] CHK005 - Is the mixed-input case (some valid signals, some bad) addressed — valid signals
  retained and sized normally while bad ones normalize to `0` — rather than only the all-bad
  case? [Coverage, Edge Case, Contract §Behavior rules 5]
- [ ] CHK006 - Is the `ok ≠ "input validated as good"` semantic clarified for the bad-input
  case (it means "no over-ceiling estimate to flag"), so a `0`/`ok` result is not misread as
  endorsement of malformed input? [Ambiguity, Data-model §Validation rules / Contract §Behavior rules 5]

## SPIDR Spike Near-Zero-LOC Case (FR-017)

- [ ] CHK007 - Is the spike (research-only) slice behavior pinned as an exact output triple
  (`estimated_loc: 0`, `suggested_slices: 1`, `status: ok`) with the LOC-threshold comparison
  skipped? [Clarity, Spec §FR-017 / Contract §Behavior rules 3]
- [ ] CHK008 - Is the meaning of `status: ok` for a spike explicitly defined as "LOC sizing is
  not applicable to a research slice" (the INVEST "Estimable" escape hatch), NOT "trivially
  small", so a near-zero-LOC spike is not misread as a fine/safe estimate? [Ambiguity, Spec §FR-017 / Edge Cases]
- [ ] CHK009 - Is it explicit that the spike path never trips a misleading `warn` and
  introduces no new status value, preserving the enum and advisory-only invariants?
  [Consistency, Spec §FR-017]

## grill-me Slice-Sizing Branch — Borderline & Unavailable Degradation (US2)

- [ ] CHK010 - Is the grill-me behavior when the estimate is at/under the ceiling specified as
  "surface the size estimate as an advisory note and do not force a split"? [Completeness, Spec §US2 Acceptance 4 / §FR-011]
- [ ] CHK011 - Is the grill-me degradation path when the estimate is borderline OR the
  estimator is unavailable pinned as "degrade to an advisory note and continue — never block
  the interview"? [Clarity, Spec §US2 Acceptance 5 / Edge Cases]
- [x] CHK012 - Is the term "borderline" in the grill-me branch defined or bounded, or is it
  left to interpretation? RESOLVED (by citation, no edit): under the advisory-only invariant
  (FR-011) nothing keys off a precise "borderline" threshold — both the borderline and
  unavailable paths collapse to the same behavior (advisory note + continue, no forced split),
  so no hard number is required. A quantified threshold would only matter for a gate, which
  PRSG-005 explicitly does not have (Q3; PRSG-006 owns gating). [Resolved, Spec §FR-011 / §US2 Acceptance 5]
- [ ] CHK013 - Is it explicit that the grill-me split branch, on the unavailable/borderline
  path, records or surfaces an advisory note WITHOUT asking a forced split question or halting
  the design-tree walk? [Coverage, Exception Flow, Spec §US2 Acceptance 5 / Design Concept Q5]

## speckit-prd Degradation Path (US1)

- [ ] CHK014 - Is the speckit-prd behavior when an entry is over the ceiling specified as
  "surface the size signal as advisory text and continue — nothing blocked or rejected"?
  [Completeness, Spec §US1 Acceptance 3]
- [x] CHK015 - Does the spec pin a speckit-prd-specific behavior for when the estimator is
  UNAVAILABLE (parallel to grill-me's US2 Acceptance 5), or is the unavailable path only stated
  generically in shared Edge Cases with no US1 acceptance-scenario coverage? RESOLVED: added
  US1 Acceptance Scenario 5 (spec §US1) mirroring US2 Acceptance 5 — when the estimator is
  unavailable (missing script/`jq`/non-zero exit/empty output) `speckit-prd` degrades to
  advisory text, leaves the Budget line unpopulated, and continues; never a hard stop, exit
  code never read as a gate. [Resolved, Spec §US1 Acceptance 5]

## Cross-Surface "Never a Hard Stop" Invariant (FR-011)

- [ ] CHK016 - Is it explicit that a `warn` status is informational only and that no PRSG-005
  path — speckit-prd, grill-me, or the script — converts a `warn` into a block/gate/reject/hard
  stop? [Clarity, Spec §FR-011 / §SC-004]
- [ ] CHK017 - Is the advisory-only invariant stated consistently for BOTH the normal `warn`
  case AND the estimator-unavailable / bad-input degradation cases (each degrades to advisory
  text, never a hard stop)? [Consistency, Spec §FR-011 / Edge Cases]
- [ ] CHK018 - Is the script's own exit behavior pinned as exit `0` on a successful estimate
  including `warn` (so `warn` is never expressed as a non-zero/blocking exit)? [Clarity, Contract §Output]
- [x] CHK019 - Does any requirement state the CALLER-side obligation — that neither skill may
  treat the estimator's exit code (or an absent/empty result when the script cannot run) as a
  gate or hard stop? The script-side "exits 0 / never raises a block exit" guarantee does not
  cover the case where the script does NOT run (missing script, missing `jq`, non-zero/127
  exit), and no requirement currently pinned what the caller must do with that. RESOLVED: the
  "Estimator unavailable mid-interview" Edge Case (spec §Edge Cases) now defines "unavailable"
  (missing script/`jq`/non-zero exit/empty output) and pins the caller-side obligation — each
  skill treats it as an absent estimate, surfaces an advisory note, and continues; a non-zero
  exit MUST NOT be read by either caller as a gate. The contract (§Output) carries the matching
  caller-side rule alongside the script-side `exits 0` guarantee. [Resolved, Spec §Edge Cases / Contract §Output]
- [ ] CHK020 - Is there a measurable success criterion that NO PRSG-005 path blocks, gates, or
  rejects in any scenario (every `warn` or unavailable estimate → advisory text + continued
  interview)? [Measurability, Spec §SC-004]

## Notes

- Check items off as completed: `[x]`
- Items carrying a `[Gap]` marker indicate a requirement that is missing or only loosely
  specified and needs a spec/plan/contract edit before implementation.
- Traceability: at least 80% of items cite a spec section or a quality marker
  (Gap / Ambiguity / Consistency / Clarity / Measurability / Coverage).

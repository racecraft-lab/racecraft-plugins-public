# Data-Integrity Checklist: Artifact relocation — tiering, .process/, collapse

**Purpose**: Validate the quality, completeness, and consistency of the requirements that protect data integrity during artifact relocation — specifically the `.process/`-only scoping of the collapse glob and gate arm, the no-deletion preservation guarantee, the textual lint proof, the determinism test with negative control, and the dual-tree anchor not colliding with same-tree CONTRACT files (notably `*-technical-roadmap.md`).
**Created**: 2026-06-05
**Feature**: [spec.md](../spec.md)

**Note**: These items are "unit tests for the requirements" — they test whether the spec/plan are written correctly, NOT whether the implementation works.

## Scope Boundary — `.process/`-Only Matching (Collapse Glob + Gate Arm)

- [x] CHK001 - Is the set of CONTRACT files that MUST NEVER match the collapse glob or gate exclusion enumerated explicitly (spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/**, checklists/**, SPEC-MOC.md, *-technical-roadmap.md), rather than only described generically as "spec, plan, tasks, and their supporting design artifacts"? [Completeness, Spec §Key Entities/FR-012] — RESOLVED: the CONTRACT artifact Key Entity now enumerates the full set explicitly.
- [ ] CHK002 - Is the matching rule for both the `.gitattributes` glob and the gate arm specified to key on the `/.process/` path segment ONLY, so it cannot match a CONTRACT path that merely lives in the same tree? [Clarity, Spec §FR-007/FR-010/FR-011]
- [ ] CHK003 - Are the requirements for the collapse glob (FR-007/FR-012) and the gate exclusion (FR-010/FR-011) consistent with each other in stating the SAME `.process/` anchor, so a reviewer is never shown something the gate counts (or vice versa)? [Consistency, Spec §FR-011, Edge Cases]
- [ ] CHK004 - Is the intentional duplication between the repo-root collapse rule and the gate's self-contained `.process/` exclusion documented as deliberate (not a defect), with the drift guard named? [Clarity, Spec §FR-011]

## Dual-Tree Anchor vs Same-Tree CONTRACT Collision

- [x] CHK005 - Does the spec explicitly state that `docs/ai/specs/*-technical-roadmap.md` is a CONTRACT artifact that the dual-tree anchor (`docs/ai/specs/.process/` + `specs/<NNN>/.process/`) MUST NOT collapse, given the roadmap sits in the SAME `docs/ai/specs/` tree as the relocated scaffold exhaust? [Completeness, Spec §Key Entities] — RESOLVED: the CONTRACT artifact Key Entity now names `*-technical-roadmap.md` and flags it as same-tree-but-protected.
- [x] CHK006 - Is it specified WHY the same-tree roadmap is safe from collapse (it lacks the `/.process/` segment), so the protection is traceable to the matching rule rather than assumed? [Clarity, Spec §Key Entities] — RESOLVED: the Key Entity now states the protection follows from the `/.process/`-segment-only matching rule, which a roadmap path lacks.
- [ ] CHK007 - Are the two `.process/` trees (`docs/ai/specs/.process/` for scaffold-time exhaust, `specs/<NNN>/.process/` for per-feature exhaust) each unambiguously specified so neither is omitted from collapse coverage nor broadened to a parent CONTRACT directory? [Completeness, Spec §Key Entities]
- [ ] CHK008 - Does the spec address the boundary case of a CONTRACT file whose name or path resembles exhaust (e.g., a roadmap or design artifact under `docs/ai/specs/`) but is NOT under a `.process/` directory, confirming it stays review-visible? [Edge Case, Coverage]

## Textual Lint Proof (L1)

- [ ] CHK009 - Is the lint's acceptance condition specified textually and objectively — every `linguist-generated` line MUST contain the `/.process/` segment — so "scoped to `.process/`" is measurable rather than subjective? [Measurability, Spec §FR-012/SC-005]
- [ ] CHK010 - Is it specified that the textual containment of `/.process/` is what guarantees a CONTRACT path cannot be matched (i.e., the lint proves the scoping property, not merely that the file exists)? [Clarity, Spec §FR-012]
- [ ] CHK011 - Does SC-005 require BOTH a positive case (lint passes when all rules are scoped to `.process/`) AND a negative case (lint fails when a rule is broadened beyond `.process/`), so the guard is proven in both directions? [Completeness, Spec §SC-005]

## Determinism Test with Negative Control (L4)

- [ ] CHK012 - Does SC-003 specify a deterministic test that adds KNOWN line counts to both a `.process/` file and a CONTRACT artifact, asserting `.process/` lines are excluded from reviewable-LOC AND the CONTRACT file's additions are still counted (the negative control)? [Completeness, Spec §SC-003]
- [ ] CHK013 - Is the test's scope pinned to diff-mode reviewable-LOC accounting (markdown is not a production file), so the assertion is unambiguous about what is measured? [Clarity, Spec §SC-003, Assumptions]
- [ ] CHK014 - Is the expected outcome of the determinism test expressed as an exact, objectively-checkable value (e.g., reviewable_loc equals the CONTRACT lines only), rather than a directional "fewer lines" claim? [Measurability, Spec §SC-003]

## No-Deletion Preservation Guarantee

- [ ] CHK015 - Is the no-deletion guarantee stated as a hard invariant — every relocated artifact remains present and readable at its new `.process/` location — covering all three authored exhaust files (design-concept doc, workflow file, UAT runbook)? [Completeness, Spec §FR-004/SC-002]
- [ ] CHK016 - Is "100% still exist and are readable (zero data loss)" specified as objectively verifiable after a run, rather than asserted as an assumption? [Measurability, Spec §SC-002]
- [ ] CHK017 - Are the requirements consistent that collapse is generated-only (no `-diff`), so relocated artifacts stay diffable and loadable on demand and are never rendered non-diffable? [Consistency, Spec §FR-008]

## Reference Integrity After Relocation

- [ ] CHK018 - Is it required that relocating the UAT runbook repoints (not removes) the PR-body reference so the "## UAT Runbook" section still renders, preventing a broken reference (dangling pointer to a moved file)? [Completeness, Spec §FR-005, Edge Cases]
- [ ] CHK019 - Are the requirements clear that the `.process/` directory is created when absent (FR-014), so the first exhaust artifact of a new spec lands at the correct location rather than failing or falling back to the old path (which would split data across two locations)? [Clarity, Spec §FR-014, Edge Cases]
- [ ] CHK020 - Is the consuming-project ensure-step required to write the collapse rule idempotently (re-running MUST NOT duplicate the rule), so the consumer `.gitattributes` does not accumulate conflicting/duplicate entries? [Consistency, Spec §FR-009/SC-004]

## Scope Boundaries (Out-of-Scope Integrity)

- [ ] CHK021 - Is the new-specs-only boundary stated as a non-mutation guarantee — the feature MUST NOT migrate, move, or mutate any existing `specs/<NNN>/` directory — so legacy data is untouched? [Completeness, Spec §FR-013, Out of Scope]
- [ ] CHK022 - Is extension-authored exhaust (retrospective, verify-tasks report) documented as explicitly OUT of scope with its post-merge cleanup attributed to the `archive` extension, so its non-relocation is a decision rather than an unhandled data-integrity gap? [Assumption, Spec §Out of Scope]

## Notes

- Items carrying a gap marker indicate a missing or under-specified requirement that may need a spec/plan edit before implementation.
- The four locked scope decisions (linguist-generated only; new-specs-only; gate hardcodes the `.process/` glob; extension-authored exhaust out of scope) are treated as decided — items here test that those decisions are clearly captured, NOT that scope should expand.

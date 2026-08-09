# State Management Checklist: Autopilot Staging

**Purpose**: Unit tests for the requirements themselves — do `spec.md` and
`plan.md` specify stage state completely, unambiguously, and consistently enough
that an implementer cannot silently reproduce the two store failures this
repository has already shipped?

**Created**: 2026-08-04

**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [data-model.md](../data-model.md)

**Depth**: Standard · **Audience**: Reviewer (PR) · **Domain**: state-management

Focus areas, verbatim from the Phase 4 domain prompt: survival across session /
worktree / archive sweep; workflow file as per-spec store vs. `autopilot-state.json`
as in-flight pointer; every state write reaching git; resume reconstruction
including `CONFIDENCE_GATE_MODE` and the G0 baseline; and two specs in flight at
once.

## Requirement Completeness — Durable Store and Survival

- [x] CHK001 Is the authoritative durable store named explicitly, with its path and its field location, rather than described in prose? [Completeness, Spec §FR-008, data-model.md §Workflow file]
- [x] CHK002 Are the requirements explicit that the durable store survives deletion of `specs/<id>/` by the archive sweep? [Coverage, Spec §Edge Cases "Archived specification"]
- [x] CHK003 Is the derived mirror's path specified, and is its single-slot, overwritten-per-run nature stated as a property rather than assumed? [Completeness, Spec §Key Entities, data-model.md §Session state file]
- [x] CHK004 Are the two fields written to the mirror today but absent from the shipped state contract (`stage`, `prior_run_note`) both required to be added to that contract? [Completeness, Spec §FR-012a, plan.md §5 State contract]
- [x] CHK005 Is the meaning of an absent `Stage` entry defined as a first-class legal state rather than left to implementer inference? [Completeness, Spec §FR-008a]
- [x] CHK006 Do the requirements state how many times per run the durable entry is written, and at which two points? [Completeness, Spec §FR-008b]
- [x] CHK007 Are the requirements complete on what a `--stage implement` run must reconstruct, enumerating each item rather than saying "the context it needs"? [Completeness, Spec §FR-010, §SC-003]
- [x] CHK008 Is the G0 test-count baseline that G7 compares against required to be preserved rather than recomputed, and is its durable location identified? [Completeness, Spec §FR-010a]
- [x] CHK009 Is the session-scoped confidence-gate mode addressed for a resumed stage — either as reconstructed state or as state explicitly re-derived by opening preparation? [Coverage, Spec §Assumptions "Requesting the implementation stage re-runs opening preparation"]

## Requirement Clarity — Vocabulary, Authority, Cadence

- [x] CHK010 Is the stage vocabulary stated once as literal tokens with casing fixed, rather than restated per platform where the two could drift? [Clarity, Spec §FR-001, contracts/stage-invocation.md §Stage vocabulary]
- [x] CHK011 Is the authority direction stated unambiguously in one place — which store wins, and which store is repaired? [Clarity, Spec §FR-008, data-model.md §Authority order]
- [x] CHK012 Do the requirements make clear that the durable entry records the last *resolved* stage and not stage *completion*, so an implementer cannot invent a fourth "done" token? [Clarity, Spec §FR-008a]
- [x] CHK013 Is "all planning phases complete" — the auto-detection predicate — defined as an enumerated set of workflow rows, or is the row set left to inference? [Resolved, Spec §FR-006a]
- [x] CHK014 Is the staged path set for bookkeeping commits enumerated rather than expressed as a directory, and is the reason recorded? [Clarity, Spec §FR-009a]
- [x] CHK015 Does the staged-path-set requirement scope itself to the phases it governs, so it cannot be read as also constraining the implementation phase's commit? [Resolved, Spec §FR-009a]
- [x] CHK016 Is the content an implementation-stage run reads as "the recorded confidence-gate verdict" specified as a named, parseable location, rather than as free-text gate prose? [Resolved, Spec §FR-010a]

## Requirement Consistency — Two Stores, Two Checks

- [x] CHK017 Are the in-run check and the at-rest check stated as two different checks with two different scopes, so neither is implemented as a duplicate of the other? [Consistency, Spec §FR-014, data-model.md §Validation rules]
- [x] CHK018 Do the requirements state why the new durable field must not join the existing exception list in the store-precedence document, given that list runs the opposite direction? [Consistency, Spec §FR-008]
- [x] CHK019 Is the requirement that the in-run check register its own problem key stated with the consequence of omitting it, rather than as a bare instruction? [Consistency, Spec §FR-014a]
- [x] CHK020 Do the plan's cited enforcement surfaces match what those files actually sweep, so the at-rest check is not scoped narrower than the success criterion it serves? [Resolved, plan.md §Summary, §6 Verification]
- [x] CHK021 Are the durable write and the mirror write required to land in the same commit, and is the failure they prevent named? [Consistency, Spec §FR-008b]
- [x] CHK022 Do the spec's Edge Cases and its Functional Requirements agree on the trigger condition for reclaiming a foreign state slot? [Resolved, Spec §FR-012a]

## Scenario Coverage — Resume Across Session, Worktree, Archive

- [x] CHK023 Are requirements defined for a resume that happens in a different working copy, not only in a later session of the same one? [Coverage, Spec §User Story 2 scenario 3, §FR-010]
- [x] CHK024 Is the carve-out for pull-request marker evidence stated with its own governing rule, so the "reconstruct from the workflow file alone" requirement does not silently relax a stricter shipped rule? [Coverage, Spec §FR-010, §SC-003]
- [x] CHK025 Are requirements defined for a workflow file that predates this feature and carries no stage entry, including how it resolves? [Coverage, Spec §FR-008a, §Edge Cases "Workflow file predating this feature"]
- [x] CHK026 Are requirements defined for the case where the durable entry and the mirror disagree, naming which is corrected? [Coverage, Spec §Edge Cases "Mirror disagrees with the authoritative record"]
- [x] CHK027 Are requirements defined for the case where the durable entry contradicts the workflow file's own phase evidence? [Coverage, Spec §Edge Cases "Recorded stage disagrees with phase evidence", §SC-006]
- [x] CHK028 Is the ordering constraint between slot reclamation and the coverage guard stated as a requirement with its rationale, not left as plan-level sequencing advice? [Coverage, Spec §FR-012a, plan.md §Sequencing constraints]

## Edge Case Coverage — Concurrency and Slot Reclaim

- [x] CHK029 Do the requirements address a state slot that names a different specification, and is reclaiming it defined as normal operation rather than an error? [Edge Case, Spec §FR-012a]
- [x] CHK030 Is the field used to note the reclaimed predecessor required to be part of the documented contract, with the ad-hoc name explicitly denied precedent status? [Edge Case, Spec §FR-012a]
- [x] CHK031 Do the requirements distinguish reclaiming a slot whose recorded run status is finished from one whose recorded status is still in progress? [Resolved, Spec §FR-012b]
- [x] CHK032 Is the enumerated set of fields rewritten on reclaim complete, and does it include the resolved stage itself? [Edge Case, Spec §FR-012a]
- [x] CHK033 Are the requirements explicit that the previous specification's durable record is unaffected by reclaiming the slot — the property that makes reclaiming safe? [Edge Case, Spec §FR-012a, §Key Entities]

## Acceptance Criteria Quality — Measurability

- [x] CHK034 Can "reconstructs the context it needs from the workflow file alone" be objectively verified, or does it need an enumerated list to be testable? [Measurability, Spec §SC-003, §FR-010]
- [x] CHK035 Is the tree-wide consistency criterion measurable against a defined file set, and does that set match what the reused validator actually covers? [Measurability, Spec §SC-006]
- [x] CHK036 Are the durable-state assertions assigned to a named verification surface, so no state rule relies on an agent choosing to run something? [Traceability, Spec §FR-014, §FR-015]

## Dependencies and Assumptions

- [x] CHK037 Is the assumption that the mirror is derived rather than a second source of truth stated, along with the earlier drift it exists to prevent? [Assumption, Spec §Assumptions]
- [x] CHK038 Is the dependency on the shipped state-vs-workflow contract identified as discharged, with the two outputs this feature depends on named? [Dependency, Spec §Dependencies]
- [x] CHK039 Is the assumption that opening preparation is unconditional and cheap stated, since resume correctness rests on it re-deriving session-scoped values? [Assumption, Spec §Assumptions]

## Notes

**All 39 items evaluated; 39 pass. 0 gaps outstanding, 0 items unresolved for
consensus.**

- Six items were raised against insufficient requirement *text*, not against a
  wrong design. Each carries a `Resolved` tag naming the requirement that closes
  it: CHK013 and CHK016 (FR-006a, FR-009, FR-010a), CHK015 (FR-009a), CHK020
  (plan.md sweep scope), CHK022 (FR-012a), CHK031 (FR-012b).
- The remaining 33 were evaluated and found already satisfied by existing
  requirement text. They are checked because they were *evaluated and passed* —
  an unchecked box would read as "not verified" and understate the coverage.
- **Verification provenance.** The orchestrator independently re-verified 8 of
  those 33 against `spec.md` and `data-model.md`, sampled across all six
  categories — CHK004, CHK009, CHK019, CHK024, CHK028, CHK033, CHK035, CHK039 —
  and confirmed the cited requirement text exists in every case (8/8). The other
  25 rest on the executor's evaluation, not on an independent re-read.

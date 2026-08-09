# Error Handling Checklist: Autopilot Staging

**Purpose**: Unit tests for the requirements themselves — do `spec.md` and
`plan.md` specify stage-resolution failure behaviour precisely enough that no
implementation of them can resolve the wrong stage *silently*? Resolving the
wrong stage re-runs finished work or skips unfinished work with no error, so
every item below asks whether a failure path has a **defined, visible** answer.

**Created**: 2026-08-04

**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [contracts/stage-invocation.md](../contracts/stage-invocation.md)

**Depth**: Standard · **Audience**: Reviewer (PR) · **Domain**: error-handling

Focus areas, verbatim from the Phase 4 domain prompt: conflicting flags failing
fast at pre-flight rather than clamping silently; a self-disagreeing status table
producing a visible outcome; the Stop-hook path being fail-open and never
stranding an operator in a continuation loop; missing or unreadable stage state
degrading to a defined answer rather than a crash; and above all whether any
failure mode can silently resolve `plan` on finished work.

Domain 1 (`state-management.md`) resolved CHK013, CHK015, CHK016, CHK020, CHK022
and CHK031. Those are not re-raised here.

## Requirement Completeness — Pre-Flight Rejection

- [x] CHK001 Is every rejection condition for the stage argument enumerated, rather than left as a general "invalid input" clause? [Completeness, Spec §FR-007, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK002 Is the rejection required to happen *before any phase work*, with the no-partial-output consequence stated rather than implied? [Completeness, Spec §FR-007, §SC-005]
- [x] CHK003 Is a repeated `--stage` with differing values specified as its own rejection case, distinct from an unrecognized value? [Completeness, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK004 Is `--stage` present with no value specified as a rejection case rather than degrading to a default? [Completeness, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK005 Do the requirements state which exit code signals a pre-flight rejection, and is the orchestrator's obligation on that code specified rather than left to inference? [Completeness, contracts/stage-invocation.md §Exit codes, Spec §FR-007]
- [x] CHK006 Is the `--from-phase` range conflict scoped to say *which* stage it is tested against — the explicitly named one or the auto-detected one? [Resolved, Spec §FR-007]
- [x] CHK007 Are the requirements explicit that a rejected run performs no state write, so a rejection cannot leave a half-written `Stage` entry? [Coverage, Spec §FR-007, §FR-008b]

## Requirement Clarity — Defined Answers for Missing and Unreadable State

- [x] CHK008 Is an absent `Stage` entry defined as a legal, non-error state with a named resolution path, rather than as an implicit default? [Clarity, Spec §FR-008a]
- [x] CHK009 Do the requirements distinguish a *readable file with no `Stage` row* from a *file that cannot be read at all*, rather than treating both as "missing state"? [Resolved, Spec §FR-007, contracts/stage-invocation.md §Exit codes]
- [x] CHK010 Is the behaviour for an unparseable phase status table defined, given that auto-detection has no input without it? [Resolved, Spec §Edge Cases "Unreadable workflow file or unparseable status table"]
- [x] CHK011 Does the contract avoid stating two different outcomes for the same input condition in its exit-code section? [Resolved, contracts/stage-invocation.md §Exit codes]
- [x] CHK012 Is the meaning of each response field defined for its null case, so a consumer cannot read "absent" as "false"? [Clarity, contracts/stage-invocation.md §Response — exit 0]
- [x] CHK013 Is the diagnostic text for each rejection specified concretely enough to be asserted on, rather than described as "a message naming the problem"? [Clarity, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK014 Is a stage value differing only by casing or spelling covered by the rejection rule, given the vocabulary is declared as literal lowercase tokens? [Clarity, Spec §FR-001]

## Requirement Consistency — The Silent-Wrong-Stage Failure Mode

- [x] CHK015 Is the auto-detection predicate an enumerated row set, so it cannot silently widen or narrow as the status table gains rows? [Consistency, Spec §FR-006a]
- [x] CHK016 Do the requirements state why the advisory-phase exclusion must NOT be reused in the predicate, rather than merely saying which rows to read? [Consistency, Spec §FR-006a]
- [x] CHK017 Is the *phase loop's own starting-row selection* constrained to the resolved stage's range, or does the spec constrain only stage resolution and leave the loop's entry point governed by a separate, unmodified scan? [Resolved, Spec §FR-009]
- [x] CHK018 Do FR-006a and FR-009 interlock without a gap — does a refused gate close the boundary to *both* auto-detection and the loop's own row scan? [Resolved, Spec §FR-006a, §FR-009]
- [x] CHK019 Is the status value a refused gate writes required to be non-terminal, and is it drawn from the closed vocabulary the shipped validators already accept? [Consistency, Spec §FR-009]
- [x] CHK020 Is the *form* of the recorded failing verdict constrained, so a stopped gate cannot be recorded in a way the shipped pass-matcher reads as a pass? [Resolved, Spec §FR-009]
- [x] CHK021 Would a non-terminal gate row beside its recorded verdict satisfy the status-versus-evidence rule, rather than converting every strict-mode stop into a tree-wide gate failure? [Resolved, Spec §FR-009, §FR-014]
- [x] CHK022 Do the requirements state that an explicitly named stage overrides auto-detection *including* when the two disagree, so precedence is not left to inference? [Consistency, Spec §FR-006, contracts/stage-invocation.md §Precedence]
- [x] CHK023 Is `--from-phase` stated as *not* a competing source of the stage, so it cannot silently widen a resolved range? [Consistency, contracts/stage-invocation.md §Precedence, Spec §Edge Cases]

## Scenario Coverage — Gate Refusal, Resume, and Operator Escape

- [x] CHK024 Are requirements defined for the state a strict-mode gate stop leaves behind, rather than only for the passing path? [Coverage, Spec §FR-009]
- [x] CHK025 Is the outcome specified when an implementation stage is named explicitly against a recorded verdict that is a refusal — proceed, stop, or proceed-with-report? [Resolved, Spec §FR-010a]
- [x] CHK026 Is the operator's documented escape from a refused gate still reachable under the new conflict rule, so the boundary is crossable rather than a dead end? [Resolved, Spec §FR-007, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK027 Are the requirements consistent about *which argument* the gate's stop guidance directs an operator to, given that guidance is being edited by this change? [Resolved, contracts/stage-invocation.md §Response — exit 2, plan.md §3]
- [x] CHK028 Are requirements defined for an implementation stage requested before planning finished, naming the outstanding phases rather than failing generically? [Coverage, Spec §Edge Cases "Implementation stage requested before planning finished"]
- [x] CHK029 Are requirements defined for a stage whose phases are all already complete, so a re-invocation reports rather than re-runs? [Coverage, Spec §Edge Cases "A stage whose phases are all already complete"]
- [x] CHK030 Is a recorded stage that contradicts the file's own phase evidence required to surface as a failure rather than be silently resolved? [Coverage, Spec §Edge Cases, §SC-006]
- [x] CHK031 Is the mirror-versus-authority disagreement given a defined winner and a defined repair direction, rather than a generic "reconcile"? [Coverage, Spec §FR-008, §Edge Cases]

## Edge Case Coverage — Degradation Boundaries

- [x] CHK032 Is reclaiming a foreign state slot defined as normal operation rather than an error condition, so it degrades to a defined answer? [Edge Case, Spec §FR-012a]
- [x] CHK033 Is the requirement explicit that reclaiming an `in_progress` slot reports but does not block, with the reason it cannot block stated? [Edge Case, Spec §FR-012b]
- [x] CHK034 Is the resolver's behaviour defined when the runner package is not importable from the in-run guard, so a copied-out validator degrades rather than emitting a false violation? [Edge Case, plan.md §2]
- [x] CHK035 Are the requirements explicit that a workflow file predating this feature resolves normally rather than erroring, given nearly the whole corpus is in that state? [Edge Case, Spec §FR-008a, §Edge Cases]

## Non-Functional — Enforcement Surfaces and Fail-Open Posture

- [x] CHK036 Is the enforcement surface set closed and named, so no stage rule depends on an agent choosing to run something? [Traceability, Spec §FR-014, §SC-006]
- [x] CHK037 Is the consequence of an unregistered problem key stated — that the check computes, prints, and is inert as a gate — rather than the registration being a bare instruction? [Consistency, Spec §FR-014a]
- [x] CHK038 Is a harness stop-hook enforcement path either specified with its fail-open and re-entry obligations, or explicitly excluded, so a reader can tell whether the design-concept obligation was inherited, deferred, or dropped? [Resolved, Spec §Out of Scope]
- [x] CHK039 Do the requirements establish that nothing in this slice runs at session end, so no continuation-loop or operator-stranding risk is introduced? [Resolved, Spec §Out of Scope, §FR-014]

## Acceptance Criteria Quality — Measurability of Error Behaviour

- [x] CHK040 Is "every invalid or conflicting stage argument is rejected" measurable against an enumerated case set rather than an open-ended one? [Measurability, Spec §SC-005, contracts/stage-invocation.md §Response — exit 2]
- [x] CHK041 Is the cross-distribution identical-resolution criterion measurable by execution rather than by prose comparison, given nothing compares the two skill bodies? [Measurability, Spec §SC-007, §FR-015a]
- [x] CHK042 Is the "gate outcomes are unchanged" criterion stated in a way a reviewer can falsify, rather than as a general assurance? [Measurability, Spec §SC-008]
- [x] CHK043 Are the rejection cases assigned to a named verification surface, so error behaviour is covered by a test rather than by prose alone? [Traceability, Spec §FR-015, plan.md §6]

## Dependencies & Assumptions

- [x] CHK044 Is the assumption that opening preparation is unconditional and cheap stated, since fail-fast rejection depends on it running every invocation? [Assumption, Spec §Assumptions]
- [x] CHK045 Is the known-inert workflow-identity check documented as a *dependency hazard* — something this spec must not reproduce — rather than assumed fixed? [Dependency, Spec §FR-014a, research.md "Known defect"]
- [x] CHK046 Is the assumption that both orchestrators can execute the shared resolver validated, given fail-fast rejection is unreachable on a platform that cannot run it? [Assumption, Spec §Assumptions]

## Notes

**All 46 items evaluated; 46 marked complete. 38 passed as-written, 8 were
remediated. 0 outstanding.**

Eight items were raised against insufficient or self-contradicting requirement
*text*, not against a wrong design. Each carries a `Resolved` tag naming the
requirement that closes it:

| Item(s) | Defect | Closed by |
|---|---|---|
| CHK017, CHK018 | The phase loop's starting-row scan was left governed by shipped table-wide logic that matches neither arm of a blocked row, so a refused gate resolved `plan` while the loop started the implementation phase | FR-009 (stage-bounded scan; blocked gate row is the planning stage's re-entry point) |
| CHK020, CHK021 | The failing verdict's record *form* was unconstrained and could scan as a pass beside a non-terminal row | FR-009 (record-form constraint) |
| CHK025 | No stated outcome for an explicitly named implementation stage against a refused recorded verdict | FR-010a (crossing is permitted but must be reported) |
| CHK006, CHK026, CHK027 | The `--from-phase` range conflict was unscoped, so the documented escape from a refused gate was either rejected (stranding the operator) or silently widening | FR-007 (conflict tested only against an explicitly named stage) + stop-guidance rewording |
| CHK009, CHK010, CHK011 | The invocation contract stated two incompatible outcomes for an unreadable workflow file, and an unparseable status table had no defined answer | FR-007 + contract exit-code split |
| CHK038, CHK039 | A harness stop-hook path was neither specified nor excluded | Out of Scope entry |

The remaining 38 were evaluated and found already satisfied by existing
requirement text. They are checked because they were *evaluated and passed* — an
unchecked box would read as "not verified" and understate the coverage.

**Flagship-failure probe result.** Three distinct routes to a silent wrong stage
were found and closed: (1) a refused gate leaving the loop's row scan to select
the implementation phase while the resolved stage read `plan` — the sharpest
form, because both halves individually looked correct; (2) an unreadable or
unparseable workflow file degrading to a default that reads every planning row as
incomplete and re-plans finished work; (3) an explicitly named implementation
stage crossing a refused boundary with no diagnostic. Routes (1) and (3) are the
`implement`-on-unfinished-work direction; route (2) is the `plan`-on-finished-work
direction the domain prompt singled out.

**Scope impact.** +7 reviewable LOC (446 → 453), no new file, no new surface, no
new requirement — every fix tightens FR-007, FR-009, or FR-010a, or removes an
ambiguity. Recorded at plan.md §Reviewability governance. Budget posture
unchanged: warn on LOC and file count, block on neither.

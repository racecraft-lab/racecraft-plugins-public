# Traceability Checklist: CAR-001 Candidate Route Baseline and Role Contracts

**Purpose**: Validate that the CAR-001 requirements artifacts (spec.md, plan.md,
data-model.md, contracts/) traceably and completely cover the PRD acceptance
criteria (AC-1.1…AC-1.7) and the binding design-concept decisions (Q1–Q9).
Unit-tests the *requirements writing* for traceability quality — not the
not-yet-authored deliverables.
**Created**: 2026-07-14
**Feature**: [spec.md](../spec.md)

## AC-to-Requirement Traceability (Completeness)

- [ ] CHK001 - Is every AC-1.1 clause (twelve-agent inventory plus the route-policy surface inventory) mapped to a named requirement? [Completeness, Spec §FR-002, §FR-003]
- [ ] CHK002 - Is AC-1.2's platform-fact citation list (model IDs, aliases, subagent configuration fields, effort levels, model-resolution precedence, plugin-agent field support, fast mode, authentication modes, non-interactive telemetry) fully mapped to a requirement? [Completeness, Spec §FR-004]
- [ ] CHK003 - Is AC-1.3's exclusion rule (excluded only for recorded incompatibility, contract failure, or predeclared dominance) traced to a requirement? [Completeness, Spec §FR-016]
- [x] CHK004 - Is AC-1.3's "prompt/context candidates when justified" clause given an explicit disposition — either a requirement to record them or a recorded deferral? [Resolved: Spec §FR-027 — deferral to CAR-003 prompt/context stage recorded]
- [ ] CHK005 - Is AC-1.4's four-way statement-class separation (fact / inference / proposed policy / assumption) traced to a requirement? [Completeness, Spec §FR-006]
- [x] CHK006 - Is AC-1.7's condition that lifts the `non_release_evidence` label (CAR-003 replay through the shared materializer with exact treatment, tool surface, mutation contract, dispatch context, and telemetry proof) specified or explicitly deferred in the labeling requirement? [Resolved: Spec §FR-020 — AC-1.7 replay conditions now named inline]
- [ ] CHK007 - Are all seven acceptance criteria (AC-1.1…AC-1.7) each referenced by at least one acceptance scenario, leaving no AC unmapped? [Traceability, Spec §User Scenarios]

## Design-Concept Decision Traceability (Q1–Q9)

- [ ] CHK008 - Is each binding design decision Q1–Q9 traceable to a requirement, or explicitly revised with a note? [Traceability, Spec §FR-001…§FR-023]
- [ ] CHK009 - Is Q3's comparator-identity revision (design-time 2.19.0 to research-time 2.19.1) recorded as an explicit, justified note rather than a silent change? [Consistency, Spec §Assumptions]
- [ ] CHK010 - Is Q4's instruction-identity contract (sha256 over the frontmatter-stripped body, full-file sha256 alongside) traced to both a requirement and a success criterion? [Traceability, Spec §FR-011, §SC-007]
- [ ] CHK011 - Is Q7's helper-derivation decision (contract-equivalent translation plus platform-field mapping table, "proposed SpecKit Pro policy" labels for Claude-only fields) traced to requirements? [Completeness, Spec §FR-017, §FR-018]

## Twelve-Agent and Surface Inventory Coverage

- [ ] CHK012 - Are all twelve named agents enumerated explicitly (by name, not by count alone) in a requirement? [Completeness, Spec §FR-002]
- [ ] CHK013 - Is the helper's production-route absence specified as an explicit *recorded absence* rather than a silent omission? [Clarity, Spec §FR-010]
- [ ] CHK014 - Is the twelve-agent set consistent across the spec, the data-model cardinality rule, and the contract's `propertyNames` enum? [Consistency, Spec §FR-002 / data-model §1 / contract]
- [ ] CHK015 - Does the AC-1.1 surface-inventory requirement name all six surface classes (source, skills, validation, evaluation, generated-payload, installed-cache)? [Completeness, Spec §FR-003]
- [ ] CHK016 - Are the read-only inventory source locations for the surface inventory identified so the inventory's scope is unambiguous? [Clarity, Plan §Project Structure]

## Go/No-Go Handoff Content Completeness (AC-1.5)

- [ ] CHK017 - Does a requirement enumerate all six handoff contents (provisional manifest, role-contract catalog, fixture backlog, telemetry requirements, capability questions, go/no-go decision)? [Completeness, Spec §FR-022]
- [ ] CHK018 - Is the "provisional candidate-route manifest" handoff item traceable to the manifest requirements? [Traceability, Spec §FR-001, §FR-014]
- [ ] CHK019 - Is the "role-contract catalog" handoff item traceable to a role-contract requirement? [Traceability, Spec §FR-014 / data-model §3.1]
- [ ] CHK020 - Is the "fixture backlog" handoff item traceable to a requirements-level fixture-backlog requirement? [Traceability, Spec §FR-019]
- [x] CHK021 - Is the "telemetry requirements" handoff item backed by a source requirement that defines its content and acceptance criteria, rather than only being named in the handoff list? [Resolved: Spec §FR-026, cross-referenced from §FR-022]
- [ ] CHK022 - Is the "unresolved capability questions" handoff item traced to a stable-ID (`CAP-Qn`) capability-question requirement? [Traceability, Spec §FR-021]
- [ ] CHK023 - Are the handoff's independence from CAR-002 results and its no-candidate-executable-before-probing constraint both specified? [Completeness, Spec §FR-022]

## Manifest Field and Identity Traceability

- [ ] CHK024 - Are all AC-1.6 per-agent manifest fields enumerated in a requirement and mirrored in the data-model field set? [Completeness, Spec §FR-014 / data-model §3]
- [ ] CHK025 - Is each candidate tuple required to carry both the shipped alias and the expected resolved model ID? [Clarity, Spec §FR-012, §FR-014]
- [ ] CHK026 - Is the project-level-eligibility versus environment-time-availability distinction specified as a manifest-structural requirement? [Completeness, Spec §FR-015 / data-model §4]
- [ ] CHK027 - Is `agent_contract_id` defined as created-by-CAR-001 and stable across pure route changes, consistent with the PRD identity lifecycle? [Consistency, Spec §FR-014 / PRD §2.3]
- [ ] CHK028 - Is the manifest's "versioned" property (`schema_version`) traceable from an entity or requirement through to the contract? [Traceability, Spec §Key Entities / data-model §1]

## Evidence, Consistency, and Ambiguities

- [ ] CHK029 - Is "official Anthropic documentation" defined as the sole admissible source for platform facts, so evidence provenance is unambiguous? [Clarity, Spec §FR-006]
- [ ] CHK030 - Is the `fable` rule (enters executor-class sets; excluded only by recorded probe or contract evidence, never by product-announcement status) consistent between the requirements and the edge cases? [Consistency, Spec §FR-013 / Edge Cases]
- [ ] CHK031 - Is "executor-class" defined with a criterion so the set of `fable`-eligible agents is unambiguous? [Clarity, Spec §Assumptions]
- [ ] CHK032 - Do the data-model and contract agree that `platform_field_mapping` is required only on the helper entry and absent on the eleven current agents? [Consistency, data-model §5 / contract]
- [ ] CHK033 - Are success criteria SC-001…SC-008 each traceable to the requirements they measure? [Traceability, Spec §Success Criteria]

## Verification Pass (post-remediation)

- [x] CHK034 - Re-check: does a source requirement now define the "telemetry requirements" content (the non-interactive telemetry fields, labeled by necessity) that the handoff enumerates? [Resolved: Spec §FR-026]
- [x] CHK035 - Re-check: is AC-1.3's "prompt/context candidates when justified" clause now given a recorded disposition (explicit deferral to CAR-003)? [Resolved: Spec §FR-027]
- [x] CHK036 - Re-check: does the labeling requirement now name AC-1.7's replay conditions (shared materializer, exact treatment, tool surface, mutation contract, dispatch context, telemetry proof) that lift the `non_release_evidence` label? [Resolved: Spec §FR-020]
- [x] CHK037 - Re-scan: is every AC-1.1…AC-1.7 clause now mapped to at least one requirement with no dangling clause remaining? [Traceability, Spec §FR-002…§FR-027]
- [x] CHK038 - Re-scan: are all nine design decisions Q1–Q9 honored or revised-with-note, including Q3's 2.19.0→2.19.1 revision? [Traceability, Spec §Assumptions, §FR-001…§FR-023]
- [x] CHK039 - Re-scan: is each of the six go/no-go handoff contents traced to a defining requirement (manifest→§FR-001/§FR-014, role-contract catalog→§FR-014, fixture backlog→§FR-019, telemetry requirements→§FR-026, capability questions→§FR-021, go/no-go→§FR-022)? [Completeness, Spec §FR-022]
- [x] CHK040 - Re-scan: do the added requirements (§FR-026, §FR-027) and the §FR-020 extension introduce no conflict with the binding design decisions or existing requirements? [Consistency, Spec §FR-020, §FR-026, §FR-027]
- [x] CHK041 - Re-scan: do the twelve-agent inventory (§FR-002) and the six-surface inventory (§FR-003) remain complete and consistent with the data-model and contract after remediation? [Consistency, Spec §FR-002, §FR-003]

## Notes

- Check items off as completed: `[x]`
- A standalone `Gap` marker (bracketed) flags a requirements-writing gap surfaced for remediation; it is removed once the source requirement is added.
- This checklist validates requirement *traceability quality*; it does not verify the (not-yet-authored) research record or manifest deliverables.

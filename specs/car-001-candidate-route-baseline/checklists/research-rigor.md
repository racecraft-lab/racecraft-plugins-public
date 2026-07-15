# Research-Rigor Checklist: CAR-001 Candidate Route Baseline and Role Contracts

**Purpose**: Unit-test the *requirements writing* for research rigor — that
spec.md, plan.md, and data-model.md properly REQUIRE the disciplines that make
the eventual research record and JSON manifest trustworthy: primary-source
citation quality (URL + access date + verbatim quote, no paraphrase, conflicts
rejected or unresolved), visible fact / inference / proposed-policy / assumption
separation, undocumented-behavior → `CAP-Qn` handling, and helper-parity
mapping completeness. It does NOT validate the not-yet-authored research record
or manifest deliverables — those are Implement-phase content this checklist's
requirements govern.
**Created**: 2026-07-14
**Feature**: [spec.md](../spec.md)

## Primary-Source Citation Quality (fact rows)

- [ ] CHK001 - Is every recorded platform fact required to carry an official source URL, an access date, and a short verbatim quote? [Completeness, Spec §FR-004, §SC-002]
- [ ] CHK002 - Is "official Anthropic documentation" required as the sole admissible source for platform facts, so evidence provenance is unambiguous? [Clarity, Spec §FR-006]
- [ ] CHK003 - Is paraphrase-presented-as-fact foreclosed — a verbatim quote (not a summary) required, with a measurable "zero facts rest on paraphrase or uncited assertion" criterion? [Clarity, Spec §FR-004, §SC-002]
- [ ] CHK004 - Is the verbatim quote's length bounded enough to be reproducible (a stated short / one-to-two-sentence bound) rather than left fully open to interpretation? [Clarity, Spec §FR-004, research §D5]
- [x] CHK005 - When official sources conflict, does a requirement define the VISIBLE mechanism for "explicitly unresolved" — a recorded home consistent with the four-class scheme? [Resolved: Spec §FR-005 — an unresolved conflict MUST be recorded as a `CAP-Qn` with both claims quoted verbatim and neither labeled a platform fact, consistent with FR-006/SC-003]

## Statement-Class Separation (fact / inference / proposed policy / assumption)

- [ ] CHK006 - Are the four statement classes (platform fact, reasonable inference, proposed SpecKit Pro policy, unverified assumption) required to be visibly separated? [Completeness, Spec §FR-006]
- [ ] CHK007 - Is the separation measurable — can a reviewer classify each statement into exactly one class without ambiguity? [Measurability, Spec §SC-003]
- [ ] CHK008 - Is the manifest's machine statement-class tag (`evidence_class` enum: fact / inference / proposed_policy / assumption) required to stay consistent with the record's four-class labeling, so one datum cannot carry two different classes across the two artifacts? [Consistency, data-model §4.1, §5, Constitution VI]
- [ ] CHK009 - Is "no head-to-head benchmark result or native fallback feature claimed where none is documented" required, keeping undocumented claims out of the fact class? [Completeness, Spec §FR-007]

## Undocumented-Behavior → Capability-Question Discipline

- [ ] CHK010 - Is the undocumented behavior when agent frontmatter names an UNAVAILABLE model (hard error vs. silent substitution) required to be a mandatory `CAP-Qn` probe question, never an assumed behavior? [Completeness, Spec §FR-008, §Edge Cases]
- [ ] CHK011 - Is `fable` resolution / availability required to be a capability question — with `fable` kept in executor-class candidate sets and excluded only by recorded probe or contract evidence, never by product-announcement status? [Completeness, Spec §FR-013, §Edge Cases]
- [x] CHK012 - Is the undocumented EXECUTION-TIME manifestation of alias re-pointing (silent re-pointing versus hard error) required to be a mandatory `CAP-Qn` probe question — distinct from, and additional to, alias re-pointing's use as an invalidation trigger — rather than assumed? [Resolved: Spec §FR-008 + §Edge Cases — alias re-pointing manifestation is now a mandatory capability question, distinct from and additional to the FR-014 invalidation trigger]
- [ ] CHK013 - Is an unbound alias-to-resolved-model-ID mapping required to be recorded as a capability question rather than an assumed fact? [Completeness, Spec §Edge Cases, data-model §4.2]
- [ ] CHK014 - Is there a general no-silent-gaps guarantee — every mandatory fact left unverified becomes a stable-ID `CAP-Qn` or a no-go item in the handoff? [Completeness, Spec §SC-005, §FR-023]
- [ ] CHK015 - Are capability questions required to carry stable IDs (`CAP-Q1…CAP-Qn`) in a dedicated section? [Traceability, Spec §FR-021]

## Helper Parity Mapping Completeness (autopilot-fast-helper)

- [ ] CHK016 - Is the `autopilot-fast-helper` contract required to be a contract-equivalent translation of the Codex toml (role prose, bounded jobs, hard rules, output formats), accompanied by an explicit platform-field mapping table? [Completeness, Spec §FR-017]
- [x] CHK017 - Does a requirement mandate that the platform-field mapping table is COMPLETE over the source — every field present in `autopilot-fast-helper.toml` (e.g. `model`, `sandbox_mode`, the `developer_instructions` contract content) either mapped to a Claude equivalent or explicitly marked no-equivalent with a proposed-policy label — so no Codex field is silently dropped? [Resolved: Spec §FR-017 + data-model §5 — the mapping table MUST be source-complete over `autopilot-fast-helper.toml`; no source field is silently dropped]
- [ ] CHK018 - Are Claude-only helper fields with no Codex equivalent (e.g. `maxTurns`) required to carry a proposed value labeled "proposed SpecKit Pro policy," deferred to CAR-010? [Completeness, Spec §FR-018, data-model §5]
- [ ] CHK019 - Is each mapping row required to carry an `evidence_class` label, so a speculative mapping (e.g. `codex-spark` → `haiku` + low effort) is visibly marked a hypothesis rather than a fact? [Clarity, data-model §5, contract `platform_field_mapping_row`]
- [ ] CHK020 - Is `platform_field_mapping` required only on the helper entry and absent on the eleven current agents, so the parity table is scoped correctly? [Consistency, data-model §5, contract]

## Research Method & Cross-Artifact Rigor

- [ ] CHK021 - Does the plan specify the fact-sourcing method (fetch the current official page live; capture source URL, access date, and short verbatim quote per platform-fact class)? [Completeness, Plan §Technical Context, research §method]
- [ ] CHK022 - Is the single-source-of-truth rule (manifest = machine data, record = evidence; cross-referenced by `agent_name` + `agent_contract_id`, never duplicated) specified so facts cannot drift between the two artifacts? [Consistency, Constitution VI, data-model intro, §7 rule 9]
- [ ] CHK023 - Are all `CAP-Qn`, `agent_contract_id`, and `fixture_backlog_ref` cross-references required to resolve to a record section (referential integrity)? [Completeness, data-model §7 rule 9]

## Verification Pass (post-remediation)

- [x] CHK024 - Re-check: does a source requirement now give an "explicitly unresolved" documentation conflict a visible, classifiable home (recorded as a `CAP-Qn`, both claims quoted verbatim, neither labeled a fact) instead of an undefined fifth state? [Resolved: Spec §FR-005]
- [x] CHK025 - Re-check: is the undocumented execution-time manifestation of alias re-pointing now a mandatory `CAP-Qn`, kept distinct from its FR-014 invalidation-trigger (detection) role? [Resolved: Spec §FR-008, §Edge Cases]
- [x] CHK026 - Re-check: does a requirement now mandate a source-complete helper mapping — every Codex toml field mapped or explicitly marked no-equivalent with a proposed-policy label? [Resolved: Spec §FR-017, data-model §5]
- [x] CHK027 - Re-scan: do the §FR-005 / §FR-008 / §FR-017 clauses, the Edge Cases note, and the data-model §5 edit introduce no conflict with the binding design decisions (Q1–Q9) or existing requirements? [Consistency, Spec §FR-005, §FR-008, §FR-017 / data-model §5] — no conflict: Q5 verbatim-quote citations, Q6 alias-only candidates, and Q7 contract-equivalent helper mapping are each preserved and strengthened; the additions reuse the existing `CAP-Qn` (FR-021) and proposed-policy (FR-018) machinery rather than adding new scope.

## Notes

- Check items off as completed: `[x]`
- A standalone `Gap` marker (bracketed) flags a research-rigor requirements-writing gap surfaced for remediation; it is removed once the source requirement, data-model rule, or contract constraint is added.
- This checklist validates requirement *research-rigor quality*; it does not verify the (not-yet-authored) research record or manifest deliverables.

# Data-Integrity Checklist: CAR-001 Candidate Route Baseline and Role Contracts

**Purpose**: Unit-test the *requirements writing* for the manifest schema and the
identity/comparator contracts — that the data-integrity rules governing
`docs/ai/research/claude-agent-route-candidate-manifest.json` (as specified in
spec.md, data-model.md, and `contracts/agent-route-candidate-manifest.schema.json`)
are complete, unambiguous, and internally consistent. It does NOT validate the
not-yet-authored manifest instance.
**Created**: 2026-07-14
**Feature**: [spec.md](../spec.md)

## Manifest Validity & Versioning (AC-1.6 field set)

- [x] CHK001 - Is the manifest's JSON-validity-and-schema-conformance obligation stated as a requirement or success criterion (the produced manifest MUST parse as JSON and validate against `contracts/agent-route-candidate-manifest.schema.json`), rather than living only as a plan-level verification step? [Resolved: Spec §SC-008 added — manifest MUST be well-formed JSON and validate against the contract with zero violations]
- [ ] CHK002 - Is `schema_version` defined with a bump policy (who bumps it and when the shape changes) so the "versioned" property is traceable entity → data-model → contract? [Consistency, Spec §Key Entities, data-model §1]
- [ ] CHK003 - Are all AC-1.6 per-agent fields enumerated in a requirement AND mirrored one-to-one in the data-model field set and the contract's `required` array? [Completeness, Spec §FR-014, data-model §3]
- [ ] CHK004 - Is the twelve-agent cardinality (exactly twelve keys) specified consistently across the spec, the data-model cardinality rule, and the contract's `minProperties`/`maxProperties` + `propertyNames` enum? [Consistency, Spec §FR-002, data-model §1]

## Instruction & File Hash Integrity

- [ ] CHK005 - Does a requirement define instruction identity as the sha256 over the frontmatter-stripped body with the full-file sha256 recorded alongside? [Completeness, Spec §FR-011, data-model §3.2]
- [x] CHK006 - Do the requirements bind the hash-input bytes to the pinned comparator's release-tag content (`speckit-pro-v2.19.1` @ its commit SHA) rather than the possibly-dirty working tree, so recorded hashes provably represent the immutable comparator? [Resolved: Spec §FR-011 + data-model §3.2 — all hashes computed over the agent bytes at the pinned tag, not the working tree; §7 rule 4 updated]
- [x] CHK007 - Is the frontmatter-stripping boundary defined precisely enough (which bytes are removed) that the instruction sha256 is reproducible by CAR-003 without re-deriving a normalization policy? [Resolved: data-model §3.2 — frontmatter = leading YAML block between the first pair of `---` fences; body hashed verbatim, no normalization (consistent with Design Q4)]
- [ ] CHK008 - Is the SC-007 invariant (a pure frontmatter route change leaves the instruction sha256 unchanged) traceable to both the hash definition and a success criterion? [Traceability, Spec §FR-011, §SC-007]
- [ ] CHK009 - Is the hash algorithm and runtime (lowercase-hex sha256 via Python 3.11+ stdlib, 64-hex) specified so recorded hashes are format-consistent across all twelve entries? [Clarity, Spec §FR-025, data-model §3.2, contract `$defs.sha256`]
- [ ] CHK010 - Is the helper's hash provenance (`codex-toml-translation`: instruction hash over the translated body, `full_file_sha256` over the source toml) specified distinctly from the eleven `claude-agent-md` entries? [Completeness, data-model §3.2]

## Comparator Pin & Eligibility/Availability Split

- [ ] CHK011 - Is the comparator pin (release tag + 40-hex commit SHA + pin rationale) specified as a required, structurally-typed object rather than prose? [Completeness, Spec §FR-009, data-model §2]
- [ ] CHK012 - Is the 2.19.0 → 2.19.1 comparator reconciliation recorded as an explicit, justified note (byte-identical agent files) rather than a silent change? [Consistency, Spec §Assumptions, data-model §2]
- [ ] CHK013 - Is the project-level-eligibility vs environment-time-availability split specified as a manifest-structural requirement (nested objects on every tuple), not prose-only? [Completeness, Spec §FR-015, data-model §4]
- [ ] CHK014 - Is `environment_time_availability.status` constrained to `probe_required` so no tuple can assert availability at CAR-001 time? [Consistency, data-model §4.2, contract]
- [x] CHK015 - When `expected_resolved_model_id` is null, does the CONTRACT (not only the data-model prose) enforce that a `binding_question_ref` to a `CAP-Qn` is present? [Resolved: contract `candidate_route_tuple.allOf` conditional added and validated (null id -> binding_question_ref required); data-model §4.2 + §7 rule 6 updated]
- [ ] CHK016 - Is the exclusion rule (excluded only for recorded incompatibility / contract failure / predeclared dominance, never product-announcement status) traced to a requirement and reflected in the schema keeping `fable` structurally admissible? [Consistency, Spec §FR-016, §FR-013, data-model §4]

## Invalidation Triggers (per-candidate, actionable, non-boilerplate)

- [ ] CHK017 - Is `invalidation_triggers` a required, non-empty per-agent field in the requirement, the data-model, and the contract (`minItems` >= 1)? [Completeness, Spec §FR-014, data-model §3]
- [x] CHK018 - Do the requirements make invalidation triggers actionable and candidate-specific — covering each candidate alias's re-pointing and the agent's comparator-hash drift — rather than admitting a single boilerplate line? [Resolved: Spec §FR-014 clause + data-model §3 field description + §7 rule 10 — per-alias re-pointing and comparator-drift triggers required; boilerplate rejected]
- [ ] CHK019 - Is "alias re-pointing" specified as a recorded invalidation trigger (tied to the edge case about documentation pages changing after the access date) rather than handled by re-research? [Consistency, Spec §Edge Cases, data-model §3]
- [ ] CHK020 - Is agent-file drift from the pinned comparator specified as a detectable invalidation condition via the recorded content hashes? [Traceability, Spec §Edge Cases, §FR-010, data-model §2]

## Cross-Artifact Consistency & Referential Integrity

- [ ] CHK021 - Do the data-model and the contract agree that `platform_field_mapping` is required only on the `autopilot-fast-helper` entry and absent on the eleven current agents? [Consistency, data-model §5, contract `allOf`]
- [ ] CHK022 - Is the single-source-of-truth rule (manifest = machine data, record = evidence; cross-referenced by `agent_name` + `agent_contract_id`, never duplicated) specified so facts cannot drift between the two artifacts? [Consistency, Constitution VI, data-model intro, §7 rule 9]
- [ ] CHK023 - Are all `CAP-Qn`, `agent_contract_id`, and `fixture_backlog_ref` cross-references required to resolve to a record section (referential integrity)? [Completeness, data-model §7 rule 9]
- [ ] CHK024 - Is `agent_contract_id` defined as created-by-CAR-001 and stable across pure route changes, so identity integrity survives frontmatter edits? [Clarity, Spec §FR-014, data-model §3]

## Verification Pass (post-remediation)

- [x] CHK025 - Re-check: is manifest schema-conformance now an explicit acceptance property (SC-008) so a malformed or non-conformant manifest fails a stated success criterion, not just a plan step? [Resolved: Spec §SC-008]
- [x] CHK026 - Re-check: do the requirements now foreclose the working-tree hash-source ambiguity by binding every recorded hash to the pinned-tag bytes? [Resolved: Spec §FR-011, data-model §3.2, §7 rule 4]
- [x] CHK027 - Re-check: is the instruction sha256 now reproducible from a byte-exact frontmatter boundary without a normalization policy (no conflict with Design Q4)? [Resolved: data-model §3.2]
- [x] CHK028 - Re-check: does the contract now structurally reject a null `expected_resolved_model_id` tuple that omits `binding_question_ref` (verified with positive and negative instances)? [Resolved: contract `candidate_route_tuple.allOf`]
- [x] CHK029 - Re-check: do the requirements now reject boilerplate invalidation triggers by mandating per-candidate-alias re-pointing plus comparator-drift coverage? [Resolved: Spec §FR-014, data-model §3, §7 rule 10]
- [x] CHK030 - Re-scan: do the added SC-008, the FR-011 and FR-014 clauses, the data-model §3.2 / §3 / §7 edits, and the contract conditional introduce no conflict with the binding design decisions (Q1–Q9) or existing requirements? [Consistency, Spec §FR-011, §FR-014, §SC-008 / data-model §3.2, §7 / contract] — no conflict: hashes stay alias-based and stdlib-computed (FR-012, FR-025), the strip rule preserves Q4's no-normalization stance, and the manifest remains valid JSON.

## Notes

- Check items off as completed: `[x]`
- A standalone `Gap` marker (bracketed) flags a data-integrity requirements-writing gap surfaced for remediation; it is removed once the source requirement, data-model rule, or contract constraint is added.
- This checklist validates requirement *data-integrity quality*; it does not verify the (not-yet-authored) manifest or research-record deliverables.

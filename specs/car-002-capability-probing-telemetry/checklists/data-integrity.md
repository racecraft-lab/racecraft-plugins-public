# Data Integrity Checklist: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

**Purpose**: Unit-test the *requirements* (spec.md, plan.md, data-model.md, contracts/) for data-integrity quality — schema validity/versioning, per-`$def` AC-2.2/2.3/2.4 field completeness, structural nulls-preserved semantics, snapshot identity, sanitized-payload + SHA-256 reproducibility, and CAR-001 cross-reference resolvability. Tests whether the requirements are complete, unambiguous, consistent, and measurable — not whether code works.
**Created**: 2026-07-16
**Feature**: [spec.md](../spec.md)

## Schema Validity & Versioning

- [x] CHK001 Are the JSON Schema's structural conventions (draft 2020-12, `$id`, `additionalProperties: false`, camelCase `$defs`, shared `sha256`/`nullableString` primitives) required so validity is checkable rather than assumed? [Completeness, Spec §FR-015]
- [x] CHK002 Is an instance-level `schema_version` const required on every one of the four record types (not just on the file) so each record self-identifies its contract version? [Completeness, Spec §FR-015; data-model "every record carries schema_version const 1.0.0"]
- [x] CHK003 Is the contract's own version line (`1.0.0`, independent of the CAR-001 manifest's `2.0.0`) stated so "consistent with CAR-001" cannot be misread as sharing the manifest's number? [Clarity, Spec §Assumptions "Contract versioning"]
- [x] CHK004 Is the single-schema-file requirement (four `$defs`, standard-library-validated, readable and checkable by Codex-side parity without executing Python) explicit? [Completeness, Spec §FR-015/§FR-016/§FR-017/§SC-007]

## AC Field-Set Completeness per `$def`

- [x] CHK005 Does the `runtime_capability_snapshot` requirement enumerate the full AC-2.2 field set — probed/resolved model IDs, alias→ID bindings, supported efforts, client version, timestamp, and raw evidence? [Completeness, Spec §FR-006/§FR-011/§FR-012; data-model Record 1]
- [x] CHK006 Is the snapshot's retrieval/probe method (bounded exact-invocation probe vs. API models endpoint under API-key auth, per AC-2.2) required to be recorded as a distinguishable snapshot element, rather than only inferable from `authentication_mode` + `models_endpoint_evidence`? [Completeness, AC-2.2 — remediated: Key Entities snapshot bullet now requires an explicit retrieval/probe method element]
- [x] CHK007 Does the `route_resolution` requirement bind the full AC-2.3 identity set — `candidate_route_id`, `agent_contract_id`, `runtime_capability_snapshot_id`, `route_resolution_id`, requested + resolved/effective model, configured effort, instruction hash, mutation contract, client version, fast-mode state, and env-override proof? [Completeness, Spec §FR-021; data-model Record 3]
- [x] CHK008 Are AC-2.3's "fallback index and reason" fields either bound in the `route_resolution`/replay contract or explicitly documented as deferred (distinct from the deferred "fallback ordering"), so the omission is intentional and traceable rather than an unreconciled gap? [Completeness, AC-2.3 — remediated: FR-021 binds nullable fallback-index/fallback-reason (consumer-populated, always null under unset-proof probes); data-model Record 3 updated]
- [x] CHK009 Is AC-2.3's "platform-initiated route change recorded separately from route resolution and makes the run non-scorable for the requested route" captured as a requirement (record class + observed-vs-resolved rule)? [Coverage, Spec §FR-025; data-model misdelivery rule]
- [x] CHK010 Does the exact-treatment replay requirement capture the complete treatment identity (full `route_resolution` binding + observed record class + outcome) sufficient to reproduce one invocation without re-probing? [Completeness, Spec §FR-022; data-model Record 4]
- [x] CHK011 Does the `telemetry_profile` requirement mandate the full AC-2.4 field set — effective model + raw token vector `stable_native`, client-side cost estimates `derived`, effective reasoning effort `derived_from_controlled_configuration` (never a returned value), conditional/unavailable fields null? [Completeness, Spec §FR-019]
- [x] CHK012 Is AC-2.3's "raw token categories including cache writes by TTL class and cache reads" explicitly enumerated (per-TTL ephemeral 5m/1h pair + cache-read fields) in the mandated classifications? [Completeness, Spec §FR-019; data-model "Mandated classifications"]
- [x] CHK013 For a replay record, is the linkage from `outcome.telemetry_ref` to the telemetry-profile token vector required to resolve (so AC-2.3's "raw token categories ... nulls preserved" is reachable), rather than left as a free nullable string with no resolution rule? [Completeness, AC-2.3 — remediated: FR-022 resolution rule (dangling telemetry reference fails validation); data-model outcome rule added]

## Nulls-Preserved Semantics (Structural, not Prose-Only)

- [x] CHK014 Is nulls-preserved enforced structurally — a `nullableString`/nullable primitive plus every nullable field held `required` under `additionalProperties:false` — so "unavailable" is distinguishable from "absent," not asserted in prose only? [Completeness, Spec §FR-020; data-model `nullableString`]
- [x] CHK015 Does the `null` record class carry a fixture requirement asserting every nullable field is present-but-null (not dropped), with required non-nullable fields still present? [Coverage, Spec §FR-025 "null"; data-model record-class rules]
- [x] CHK016 Is the exactly-one-classification-label + nulls-preserved requirement on the telemetry profile made verifiable on every run (SC-006 enforced by the deterministic test against the `telemetry_profile` `$def`)? [Measurability, Spec §FR-024/§SC-006]

## Snapshot Identity & Canonicalization

- [x] CHK017 Is the "one canonical committed snapshot" path required, with a re-probe replacing the file in place and git history preserving priors? [Completeness, Spec §FR-011]
- [x] CHK018 Are the snapshot's internal identity elements — `captured_at_utc` timestamp, `pinned_client_version`, `authentication_mode`, and canary text + hash — all required fields? [Completeness, data-model Record 1; Spec §FR-014/§FR-018/§FR-005]
- [x] CHK019 Is the `runtime_capability_snapshot_id` format (`CAR-002-RCS-<YYYY-MM-DD>-V<n>`) required and pattern-constrained rather than free-text? [Clarity, Spec §Assumptions "ID conventions"; schema `runtimeCapabilitySnapshot` pattern]
- [x] CHK020 Is there a requirement that the date embedded in `runtime_capability_snapshot_id` be consistent with `captured_at_utc`, and that a re-probe bump `V<n>` monotonically, so the identity cannot silently disagree with the recorded timestamp? [Consistency, Spec §FR-011 — remediated: ID-date must equal capture-timestamp UTC date + monotonic V<n>, both checked by validation]

## Tuple Evidence Sharing & No-Duplication

- [x] CHK021 Is "one shared evidence set per unique (model, effort) tuple" required, with every candidate route citing its tuple's evidence via a derived reference? [Completeness, Spec §FR-003/§FR-004]
- [x] CHK022 Is the no-duplication rule explicit — the `candidate_route_id`→`tuple_id` map MUST NOT be persisted, and the join is derived every run? [Consistency, Spec §FR-004/§SC-005; data-model "Relationships and derived join"]
- [x] CHK023 Is the 37-route→tuple join required to be recomputed deterministically on every CI run, failing closed if any route resolves to zero or to more than one tuple? [Measurability, Spec §FR-024/§SC-005]
- [x] CHK024 Is the `tuple_id` derivation formula (pure function of the CAR-001 manifest's `model_selector`/`effort_selector`; null effort → `none`) specified unambiguously so the manifest-side and snapshot-side keys compute identically? [Clarity, data-model "Identity conventions" R1; Spec §FR-004]

## Sanitized Payload & SHA-256 Integrity

- [x] CHK025 Is the SHA-256 required to be computed over the exact sanitized UTF-8 bytes of the stored payload (hash over the *sanitized* bytes, not the raw or a parsed/reserialized object)? [Clarity, Spec §FR-013; data-model `rawEvidence`]
- [x] CHK026 Is the raw payload required to be committed verbatim as a string (not parsed-and-reserialized) so the hash reproduces from the committed bytes? [Clarity, Spec §FR-013]
- [x] CHK027 Is the ordering constraint explicit — sanitization MUST occur before hashing/writing, and no unsanitized home/user/session path may be committed? [Completeness, Spec §FR-012/§FR-013]
- [x] CHK028 Is there a requirement that deterministic validation RECOMPUTE `raw_output_sha256` over the committed `raw_output` (and `canary_sha256` over the canary text) and fail on mismatch, so "reproducible" is enforced rather than only asserted — given the `sha256` `$def` checks only the 64-hex pattern? [Measurability, Spec §FR-024 — remediated: validator recomputes raw_output_sha256 + canary hash over committed bytes, fails on mismatch]
- [x] CHK029 Is there a requirement that validation verify committed `raw_output` payloads contain no unsanitized home/user/session paths, rather than trusting the writer sanitized at write time (FR-013 governs write-time only; FR-024's test list omits a sanitization check)? [Measurability, Spec §FR-024 — remediated: continuous sanitization re-scan of committed payloads]
- [x] CHK030 Is the `rawEvidence.sanitization` marker required as a const, and is the full-payload-vs-CAR-001-bounded-extract decision documented so the stored-bytes contract is unambiguous? [Clarity, data-model `rawEvidence`; Spec §Key Entities "Raw probe evidence"]

## ID Formats & CAR-001 Cross-Reference Resolvability

- [x] CHK031 Are `candidate_route_id` (`CAR-001-CR-<NN>-<NN>`) and `agent_contract_id` (`car.<name>.v1`) required to be format-validated (pattern-constrained) rather than accepted as free-text `minLength:1` strings, per "resolvable, not free-text"? The schema currently constrains neither. [Clarity, Spec §FR-021 — remediated: cross-reference IDs pattern-constrained, never free-text; schema draft aligns at WP1 implementation]
- [x] CHK032 Is there a referential-integrity requirement that a `route_resolution` record's `candidate_route_id` / `agent_contract_id` resolve to an existing entry in the committed CAR-001 manifest (not merely be well-formed)? [Measurability, Spec §FR-024 — remediated: referential-integrity check against the committed CAR-001 manifest]
- [x] CHK033 Is `runtime_capability_snapshot_id` validated consistently across records — the `runtimeCapabilitySnapshot` `$def` pattern-enforces it, but `routeResolution` and `telemetryProfile` accept it as free-text `minLength:1`? [Consistency, Spec §FR-015 — remediated: identical ID pattern constraints across all $defs; schema draft aligns at WP1 implementation]
- [x] CHK034 Is the reuse-verbatim rule for CAR-001 cross-reference strings stated so IDs are never re-derived or reformatted (drift risk)? [Consistency, Spec §FR-021; data-model "Cross-reference IDs ... reused verbatim"]
- [x] CHK035 Is the `route_resolution_id` contract (pattern-only; minted by CAR-003+ consumers; fixtures use deterministic literals) specified so CAR-002 fixes identity rules without over-constraining downstream? [Clarity, Spec §Key Entities "route_resolution record"; data-model "Identity conventions"]

## Dependencies, Assumptions & Cross-Record Integrity

- [x] CHK036 Is the CAR-001 manifest dependency (frozen 12 contracts / 37 routes; consumption gate satisfied at a pinned base) documented as the authoritative join source? [Assumption, Spec §Assumptions "Consumption gate satisfied"]
- [x] CHK037 Are the four record-class fixtures (success/null/unavailable/misdelivery) each required to be complete exact-treatment replay records carrying a full `route_resolution` binding, so cross-record integrity is testable? [Completeness, Spec §FR-025; data-model record-class rules]
- [x] CHK038 Is the `unavailable` fixture required to cross-reference its corresponding snapshot observation via `runtime_capability_snapshot_id`, establishing the fixture→snapshot integrity link? [Coverage, Spec §FR-025 "unavailable"; data-model record-class rules]

## Notes

- This checklist tests requirement *quality* (completeness, clarity, consistency, measurability, coverage) — it does not verify implementation behavior.
- Traceability: every item cites a spec section (`§FR`/`§SC`/`§Assumptions`/`§Key Entities`), a data-model/schema location, or an acceptance criterion (AC-2.2/2.3/2.4) / focus marker.
- A gap marker flags a requirement that appears missing, unresolved, or internally inconsistent and is a candidate for remediation by the orchestrator. All other items reference an existing requirement judged adequate.
- Generation run (phase-executor) + orchestrator remediation 2026-07-16: 29 items verified by the generator; the 9 gap-marked items were remediated by the orchestrator (spec.md FR-011/FR-015/FR-021/FR-022/FR-024 + Key Entities snapshot bullet; data-model.md Record 3 + outcome rule). The contracts/ schema draft aligns with the new pattern/fallback requirements at WP1 implementation (Analyze cross-checks).

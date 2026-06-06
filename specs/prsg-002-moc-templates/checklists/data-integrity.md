# Data Integrity Checklist: MOC templates + scaffold-time skeleton + version-gated lints

**Purpose**: Validate the QUALITY of the data-integrity requirements — namespace-aware ID normalization, exact-segment matching, cross-namespace collision avoidance, the three load-bearing frontmatter fields, and the `spec_id` ↔ directory join. These are "unit tests for the requirements," not for the implementation.
**Created**: 2026-06-06
**Feature**: [spec.md](../spec.md)
**Focus**: Namespace normalization (`SPEC-`/`PRSG-`/no-prefix→`spec`), exact-segment number-suffix matching, cross-namespace collisions, frontmatter join-key integrity.

## Namespace-aware ID normalization — grammar completeness

- [x] CHK001 - Is the normalization grammar (lowercase → split on `-` → all-alpha first segment = namespace else `spec`) fully specified as a deterministic procedure? [Completeness, Spec §FR-017]
- [x] CHK002 - Is the no-alpha-prefix → legacy `spec` namespace rule stated unambiguously for directory names that begin with a digit? [Clarity, Spec §FR-017]
- [x] CHK003 - Is the number-suffix comparison explicitly required to be opaque whole-segment (byte-equality), with sub-parsing of trailing letters from digits explicitly forbidden? [Clarity, Spec §FR-017]
- [x] CHK004 - Are requirements defined for the grammar's behavior when an all-alpha first segment has no following segment (e.g., a value that is only a namespace token, or has a trailing dash and an empty next segment)? [Resolved, Spec §FR-017 totality clause + Edge Cases "Degenerate normalization inputs"]
- [x] CHK005 - Are requirements defined for the degenerate inputs an empty string, a value that is only `-`, or a value with leading/trailing dashes, so the `(namespace, number-suffix)` derivation is total (never undefined)? [Resolved, Spec §FR-017 totality clause + Edge Cases]

## Exact-segment matching & cross-namespace collisions

- [x] CHK006 - Is the match rule (BOTH namespace AND number-suffix must agree) stated as a single conjunctive condition? [Clarity, Spec §FR-018]
- [x] CHK007 - Is the cross-namespace non-collision requirement (`PRSG-002` MUST NOT match `SPEC-002`; `PRSG-002` MUST NOT match `002-...`) specified with canonical examples? [Completeness, Spec §FR-018]
- [x] CHK008 - Is the near-miss suffix non-match requirement (`013a` MUST NOT match `013a1`) specified and traceable to a measurable outcome? [Consistency, Spec §FR-018, §SC-004]
- [x] CHK009 - Are the canonical worked examples for normalization internally consistent across spec, data-model, and the ID-normalization contract (no example normalizes two different ways in two documents)? [Consistency, Spec §FR-018]
- [x] CHK010 - Are requirements defined for how the lint treats two scanned directories that normalize to the SAME `(namespace, number-suffix)` pair (duplicate-ID collision across directories), or is this intentionally out of scope for the per-spec join? [Resolved — Spec Assumptions "Global ID uniqueness is NOT a v1 goal" states the per-spec join scope and the out-of-scope exclusion]

## Frontmatter join-key integrity (the three load-bearing fields)

- [x] CHK011 - Are exactly three fields (`up`, `structureVersion`, `spec_id`) designated load-bearing/enforced in v1, with `status`/`rank`/`related` explicitly carried-but-unenforced? [Completeness, Spec §FR-003]
- [x] CHK012 - Is the division of labor for `up` integrity unambiguous — presence/non-empty/well-formed owned by the orphan lint, target resolution owned by the stale-index lint, with no overlap and no gap? [Consistency, Spec §FR-009, §FR-011]
- [x] CHK013 - Is the `spec_id` ↔ directory join required to normalize BOTH the `spec_id` value AND the containing directory name with the same grammar before comparing (symmetry of normalization)? [Resolved, Spec §FR-019 symmetric-normalization clause]
- [x] CHK014 - Are requirements defined for whether a MISSING or EMPTY `spec_id` in a version-gated `SPEC-MOC.md` is itself a violation, distinct from a present-but-mismatched `spec_id`? [Resolved, Spec §FR-019 absent/empty clause + Edge Cases "Version-gated marker missing/empty spec_id"]
- [x] CHK015 - Is the `spec_id` mismatch outcome (violation in a version-gated spec) stated as a hard-fail consistent with the other lints' exit semantics? [Consistency, Spec §FR-014, §FR-019]

## Version-gate value integrity

- [x] CHK016 - Is the version-gate condition (`structureVersion >= 1`) and the exempt-on-absence rule specified so legacy specs are grandfathered? [Completeness, Spec §FR-013, §SC-002]
- [x] CHK017 - Is `structureVersion` required to be an integer, and are requirements defined for how a MALFORMED or non-integer value (e.g., a quoted string, a decimal, or non-numeric text) is treated by the `>= 1` gate — exempt, violation, or error? [Resolved, Spec §FR-013 malformed-value clause + Edge Cases "Marker present but structureVersion malformed"]
- [x] CHK018 - Is the hardcoded version literal `1` required to stay in sync between the lint scripts and the scaffold-stamped marker, such that a future drift cannot silently mis-gate specs? [Consistency, Spec §FR-016]

## Acceptance criteria & measurability

- [x] CHK019 - Can the headline ID-join integrity be objectively verified via the stated collision/near-miss pairs (`PRSG-002`/`SPEC-002`, `013a`/`013a1`) rather than a subjective "joins correctly"? [Measurability, Spec §SC-004]
- [x] CHK020 - Are the dogfooded real-tree examples (`006a-uat-skeleton`→`(spec,006a)`, `prsg-002-moc-templates`→`(prsg,002)`, `002-...`→`(spec,002)`) consistent with the actual directories present under `specs/`, so the green-on-adoption claim is verifiable? [Traceability, Spec §FR-018, §SC-002]

## Notes

- Check items off as resolved: `[x]`.
- A "Resolved" tag marks an item that surfaced a missing/underspecified data-integrity requirement and was closed by editing spec.md (and the matching contract/data-model artifacts), not by changing implementation. The bracketed reference names the FR/section that now carries the rule.
- Five items surfaced underspecified data-integrity rules and were remediated: CHK004/CHK005 (grammar totality on degenerate inputs → FR-017), CHK010 (cross-directory duplicate-ID is an explicit v1 non-goal → Assumptions), CHK013 (symmetric normalization → FR-019), CHK014 (absent/empty `spec_id` is a violation → FR-019), CHK017 (malformed `structureVersion` treated as not-gated → FR-013).
- Locked/settled decisions (namespace-prefixed contract dirs; `spec_id` carries the roadmap identity; the three load-bearing fields; the opaque whole-segment grammar with `PRSG-002`≠`SPEC-002` and `013a`≠`013a1`) are deliberately NOT re-litigated here — those items are phrased as consistency/clarity checks that the requirements ENCODE the settled decision, and they pass.

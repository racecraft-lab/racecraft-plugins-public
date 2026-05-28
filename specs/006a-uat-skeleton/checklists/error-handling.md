# Error Handling Checklist: Deterministic UAT Runbook Skeleton + PR Body Integration

**Purpose**: Unit-test the *requirements writing* for every failure path. Fail-open is the autopilot's guarantee — the skeleton script must never block PR creation. This checklist asks whether each failure mode (missing spec, malformed env, absent headings, duplicate IDs, unresolved clarification markers, missing Self-Review, missing Rollback) is specified completely, clearly, and consistently, and whether the autopilot-level fail-open outcome is pinned.
**Created**: 2026-05-28
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [contracts/generate-uat-skeleton-cli.md](../contracts/generate-uat-skeleton-cli.md)
**Domain**: error-handling · **Audience**: PR reviewer · **Depth**: formal release gate

**Note**: These are "unit tests for the English." Each item is a yes/no quality assertion about the spec/plan/contract — not an implementation task. A checked box means the requirement text already answers the question; an unchecked gap-marked item means it does not, and the item is escalated for consensus.

## Fatal-Path Requirements (the only error exits)

- [x] CHK001 - Is the missing/unreadable-spec failure specified as exit 1 with **no partial runbook written** (the output file is not created on this path)? [Completeness, Spec §FR-006, Contract §Exit codes]
- [x] CHK002 - Is the usage-error failure (wrong/missing argv, unknown flag, extra positional) specified as exit 2, distinct from the spec-readability failure? [Clarity, Spec §FR-006, Contract §Exit codes]
- [x] CHK003 - Is exit-code precedence between the two fatal paths specified (usage validation → 2 evaluated before spec readability → 1)? [Consistency, Contract §Exit codes]
- [x] CHK004 - Is it explicit that these are the ONLY non-zero exits — i.e., every other degraded input is non-fatal and still exits 0? [Completeness, Contract §Exit codes]

## Non-Fatal Degradation Paths (must NOT crash)

- [x] CHK005 - Is the unset `UAT_PROJECT_COMMANDS` path specified as emitting unknown-value placeholders rather than failing? [Completeness, Spec §FR-008, Spec §Edge Cases]
- [x] CHK006 - Is the **malformed** `UAT_PROJECT_COMMANDS` (non-`jq`-parseable) path specified as a fail-soft fall back to placeholders rather than a crash? [Completeness, Spec §FR-008, Contract §Environment variables]
- [x] CHK007 - Is the absent `### Edge Cases` heading path specified as retaining the Negative-Path Tests header and emitting the exact stub line `No edge cases identified in spec.md` (not omitting the section)? [Clarity, Spec §FR-010, Spec §Edge Cases]
- [x] CHK008 - Is the missing-Self-Review path (flag absent, file unreadable, or heading missing) specified as a graceful stub line with exit 0? [Coverage, Spec §FR-009, Contract §Flags]
- [x] CHK009 - Is the missing-`## Rollback` path specified as a synthesized fallback stanza rather than an empty or omitted section? [Completeness, Spec §FR-012, Spec §Edge Cases]
- [x] CHK010 - Are all eight degraded-input edge cases enumerated in one place and each mapped to its governing FR? [Completeness, Spec §Edge Cases]

## Duplicate-ID Handling (FR-004)

- [x] CHK011 - Is the duplicate FR/SC ID behavior specified as keeping the first-seen entry only (deterministic dedupe) plus a stderr warning naming the duplicated ID? [Completeness, Spec §FR-004, Contract §stderr warning triggers]
- [x] CHK012 - Is it specified that the duplicate-ID warning is non-fatal (script continues, exit 0)? [Clarity, Contract §stderr warning triggers]
- [x] CHK013 - Is the stderr warning style for duplicates specified as plain/unprefixed (no machine-readable tag), with an example message? [Measurability, Spec §FR-004, Contract §Output streams]

## Clarification-Marker Propagation (FR-005)

- [x] CHK014 - Is the clarification-marker behavior specified as propagating each marker into the runbook with an annotation rather than silently dropping it? [Completeness, Spec §FR-005, Spec §Edge Cases]
- [x] CHK015 - Are both marker forms (bare and colon-question) specified as in-scope for detection? [Coverage, Spec §FR-005, Plan §Decision 3]
- [x] CHK016 - Is the **scope** of propagation unambiguous — i.e., does the spec consistently state whether markers are propagated only when carried by a parsed US/FR/SC/Edge bullet, or anywhere in `spec.md`? [Consistency, Spec §FR-005, Plan §Decision 3]
- [x] CHK017 - Is it specified that clarification markers route to the runbook annotation, NOT to stderr (distinct from the duplicate-ID warning channel)? [Clarity, Contract §stderr warning triggers]

## Autopilot Fail-Open Guarantee (the load-bearing outcome)

- [x] CHK018 - Is the autopilot-level fail-open behavior specified — a nonzero exit from the skeleton generator MUST NOT abort the run or block PR creation? [Completeness, Plan §FR-013 Wiring]
- [x] CHK019 - Is it specified what lands in the PR body when the skeleton generator fails — the `## UAT Runbook` heading still appears, followed by a stub note, via the absent-file path? [Coverage, Plan §FR-013 Wiring]
- [x] CHK020 - Is the fail-open mechanism specified as compositional (FR-006 writes no partial file → the PR-body absent-file path fires) rather than a new ad-hoc error branch? [Consistency, Spec §FR-006, Plan §FR-013 Wiring]
- [x] CHK021 - Is the failure-vs-absence ambiguity resolved — the generic stub cannot distinguish "generator failed" from "never run," and the failure detail lives in the autopilot log? [Clarity, Plan §FR-013 Wiring]
- [x] CHK022 - Is the standalone-run degradation (no env, no workflow file) specified as graceful, so non-autopilot invocations never error on optional inputs? [Coverage, Contract §Invocation, Spec §Assumptions]

## Recovery & Idempotency Under Failure

- [x] CHK023 - Is re-run behavior after a prior failed/partial run specified (deterministic overwrite means a subsequent successful run fully replaces any stale output)? [Coverage, Spec §FR-007]
- [x] CHK024 - Is it specified that a failed run leaves no partial artifact that a later run would have to merge or clean up (exit-1 path writes nothing)? [Consistency, Spec §FR-006, Spec §FR-007]

## Acceptance-Criteria Quality for Failure Paths

- [x] CHK025 - Does the Layer 4 test plan cover the fatal path (missing-spec error case) with an explicit exit-code assertion? [Measurability, Spec §FR-015, Plan §Traceability]
- [x] CHK026 - Does the Layer 4 test plan cover the non-fatal degradation paths (zero-stories, duplicate-FR, clarification-marker) as distinct fixtures? [Coverage, Spec §FR-015]
- [x] CHK027 - Are stderr-warning assertions (duplicate-ID case) and silent-stdout assertions specified as objectively checkable in the test plan? [Measurability, Plan §Traceability]

## Notes

- CHK016 surfaced a real consistency gap: the spec's Edge Cases entry stated markers are propagated "when `spec.md` still carries clarification markers" (reading as *anywhere in the file*), while FR-005 and Plan Decision 3 scope propagation to a *parsed US/FR/SC/Edge bullet*. Resolved in-place by tightening the Edge Cases entry to the parsed-bullet scope, matching FR-005/Decision 3.
- CHK018–CHK021 (autopilot fail-open) were under-specified at the spec/plan level — each script's own exit behavior was documented, but the composed autopilot-level guarantee (nonzero skeleton exit must not block PR creation; the heading survives via the absent-file path) was not pinned. Resolved in-place by adding the "Autopilot-level fail-open (the composed guarantee)" paragraph to the plan's FR-013 Wiring section, derived by composing FR-006 (no partial file) with the existing absent-file PR-body path.
- All other failure paths were already specified across spec.md, plan.md, and the CLI contract. Zero unresolved gap-marked items remain in this domain.

# Data-Integrity Requirements Quality Checklist: PRSG-006

**Purpose**: Unit-test the SPEC + PLAN for data-integrity quality — are the
determinism, counting, in-sync, greenfield-agreement, back-compat, and
fail-closed behaviors of the plan-phase estimator (`estimate-reviewable-loc.sh`)
and the reworked gate (`reviewability-gate.sh`) specified precisely enough to
implement and test without silent corruption, double-counting, or drift?

**Created**: 2026-06-06 (re-run after remediation)
**Feature**: `specs/prsg-006-reviewability-budget`
**Scope**: Requirements quality (is it written correctly?), NOT implementation behavior.

## Determinism (byte-identical output, known-value assertion)

- [ ] CHK001 - Is the determinism contract (same `plan.md` input ⇒ byte-identical stdout) stated as a hard requirement with a fixture obligation, not just a goal? [Clarity, Spec §FR-002, §SC-001]
- [ ] CHK002 - Does the spec/plan require the determinism fixture to assert a **known expected value** (parsed planned-file count AND projected production-LOC) rather than only two-run equality, so an empty/garbage declaration cannot pass a vacuous stability check? [Completeness, Spec §FR-002; contracts/estimate-reviewable-loc.output.md §Determinism]
- [ ] CHK003 - Are the determinism hazards to avoid (no timestamps, no `$RANDOM`, no unsorted-set iteration that can reorder output) enumerated so "deterministic" is measurable rather than aspirational? [Measurability, contracts/estimate-reviewable-loc.output.md §Determinism]

## Production-LOC metric & double-counting

- [ ] CHK004 - Is the production-LOC metric defined as counting production files only (`is_production_file` AND NOT `is_excluded_generated`), with docs/tests/config explicitly excluded, and is this stated to apply consistently in BOTH the gate's `diff` mode and the estimator? [Clarity, Spec §FR-008; Key Entities]
- [ ] CHK005 - Is the `projected` production-LOC formula for the estimator unambiguously defined as (count of declared production files) × per-file constant, including which entries count as "production"? [Clarity, contracts/estimate-reviewable-loc.output.md §Field semantics]
- [ ] CHK006 - Is a **de-duplication rule specified** so a repo-relative path listed twice contributes once — for the gate (`sort -u` of its file lists) AND for the estimator's `## Declared File Operations` block (de-dupe by repo-relative path), preventing a duplicated entry from double-counting projected LOC and breaking determinism-of-meaning? [Resolved, Spec §FR-008 "No double-counting"; contracts/estimate-reviewable-loc.output.md §Declared-files parse grammar "De-duplication"]
- [ ] CHK007 - Is the all-docs/tests/config slice (zero production files) explicitly defined as within-budget on the size metric, so a non-production slice is not mis-scored? [Coverage, Edge Case, Spec §Edge Cases]

## Shared production-LOC-per-file constant (in-sync / drift)

- [ ] CHK008 - Is the **unit difference** between the gate's `×40` (per-task, a `tasks.md` line count) and the estimator's per-file constant recorded, so an implementer does not assume the two values must be numerically equal? [Clarity, Spec §FR-007; plan.md §The per-file LOC constant]
- [ ] CHK009 - Is the keep-in-sync mechanism for the shared magnitude named concretely (the repository's copied-comment "keep in sync" convention) rather than left as an unspecified "stay aligned"? [Clarity, Spec §FR-007; plan.md §Architecture]
- [ ] CHK010 - Does the spec/plan specify a mechanism that **catches** drift — an L1 structural assertion that the keep-in-sync comment marker is present in BOTH scripts — and does it state explicitly that this is comment-presence (NOT numeric value-equality, since the per-task vs per-file units differ and the value is tunable), so the chosen integrity guarantee is unambiguous rather than implied? [Resolved, Spec §FR-007 "Drift-catch mechanism"; plan.md §Test strategy L1 "Keep-in-sync drift guard"]

## Greenfield detection (plan-mode vs diff-mode agreement)

- [ ] CHK011 - Is the greenfield predicate stated identically for both detectors — plan-mode (every non-excluded declared entry is `NEW`, none `MODIFIED`) and diff-mode (every non-excluded changed path is git add-status `A`) — so the two modes cannot disagree on the same file-set? [Consistency, Spec §FR-006, §FR-009; contracts/estimate-reviewable-loc.output.md `greenfield` field]
- [ ] CHK012 - Is the treatment of a modified **excluded/generated** file (e.g. a lockfile) specified — that it does NOT disqualify greenfield — and is this consistent between the plan-mode and diff-mode rules so the exclusion set matches FR-008's production-only counting? [Consistency, Spec §FR-009]
- [ ] CHK013 - Is the diff-mode add-status call required to pin rename/copy detection off (e.g. `--no-renames`) so an ambient `diff.renames` git config cannot vary the greenfield boolean? [Clarity, Spec §FR-009]

## Back-compat break (legacy exception keywords)

- [ ] CHK014 - Is it specified that the legacy three-phrase keyword (`split exception` / `transition exception` / `ratified exception`) is no longer honored at **all three** gate modes (`setup`, `tasks`, `diff`), with no mode silently retaining the old matcher? [Completeness, Spec §FR-013]
- [ ] CHK015 - Is the backward-incompatible break (new-specs-only, no deprecation window) documented in the spec for PRSG-011 to pick up for retro-migration, so the data-model change is traceable rather than silent? [Traceability, Spec §FR-013, §Deferred]

## Typed-exception fail-closed integrity

- [ ] CHK016 - Is the single shared matcher specified exactly (line-anchored, case-sensitive, closed enum `{refactor, infra, upgrade}`, no trailing content, POSIX ERE) and required to be implemented once and reused across all three modes to prevent regex-engine drift? [Clarity, Consistency, Spec §FR-011, §FR-012]
- [ ] CHK017 - Is fail-closed behavior pinned for every non-conforming input (class outside the set, mis-cased class, trailing content, missing pragma, free-form prose) — each leaving `status = block` — so no input class is left ambiguous? [Completeness, Edge Case, Spec §FR-012, §Edge Cases]
- [ ] CHK018 - Is the diff-mode pragma read specified to use **added (`+`) lines of committed Markdown only**, with the unified-diff `+++ b/<file>` header isolated out so it cannot self-satisfy the matcher, and with PR-body/commit-message sources excluded as mutable? [Clarity, Edge Case, Spec §FR-012; contracts/reviewability-gate.output.md §Typed exception]

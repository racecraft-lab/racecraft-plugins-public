# G56R-004 PR Review Traceability

## What Changed

G56R-004 adds a repository-only Codex policy-control harness with exactly three
controls: unpinned, adaptive, and justified-high-effort. It adds Codex-local
schemas and deterministic fixtures, Python 3.11 standard-library validators and
replay/smoke helpers, and coverage in three existing unit-test owners.

The implementation is confined to the 12 declared paths in `plan.md`:

- 2 Codex-local schemas
- 4 deterministic fixtures
- 3 helper modules
- 3 existing unit-test owners

## Why

The feature freezes Codex-local control and comparison contracts before
G56R-011 observes final static-core outcomes. It preserves CAR-004 category
1-6 semantics, derives authority-bound members in both directions, rejects
drift and silent omissions, and keeps the sole sanctioned platform divergence:
Codex `justified_high_effort` represents the CAR-004
`orchestration_changing` control.

## Non-Goals

- No production routing, installer, manifest, scheduler, default, or release
  integration behavior changes.
- No edits to frozen G56R-003, CAR-003, or CAR-004 contracts, fixtures, traces,
  partitions, or evidence.
- No final G56R-011 dominance conclusion.
- No G56R-012 reconciliation work.
- No live model execution or off-repository context transfer.

## Review Order

1. Review the two schemas and four fixtures for the frozen data shape.
2. Review `codex_policy_controls.py`, `codex_control_comparison.py`, and
   `codex_control_smoke.py` for validation and replay behavior.
3. Review the three unit-test owners for requirement and success-criterion
   evidence.
4. Review this packet, `tasks.md`, and the final verification results.

`tests/speckit-pro/suite-manifest.json` is intentionally unchanged because the
three existing unit owners remain registered.

## Scope Budget

The plan declares 12 file operations: 9 new repository-only test-tree files and
3 modified unit owners. The reviewability estimator passed with 0 production
files and a one-slice decision. No install-facing plugin runtime file is in
scope.

## Traceability

| Requirements | Success criteria | Changed implementation paths | Verification owner |
|---|---|---|---|
| FR-001-FR-005 | SC-001-SC-003 | `policy-control-registry.schema.json`, `policy-control-registry.json`, `codex_policy_controls.py` | `test-policy-control-contracts.py` |
| FR-006-FR-007, FR-040-FR-041 | SC-004, SC-018 | Both schemas; registry, comparison, and partition fixtures; `codex_policy_controls.py` | `test-twin-handoff-completeness.py` plus the policy and comparison owners |
| FR-008-FR-009 | — | `policy-control-registry.json`, `codex_policy_controls.py` | `test-policy-control-contracts.py` |
| FR-010-FR-017 | SC-005-SC-007 | `policy-control-registry.json`, `replay-cases.json`, `codex_policy_controls.py` | `test-policy-control-contracts.py` |
| FR-018-FR-023 | SC-008-SC-009 | `policy-control-registry.json`, `replay-cases.json`, `codex_policy_controls.py` | `test-policy-control-contracts.py` |
| FR-024-FR-030 | SC-010-SC-011 | `control-comparison.schema.json`, `control-comparison.json`, `codex_control_comparison.py` | `test-control-comparison-dominance.py` |
| FR-031-FR-034 | SC-012-SC-013 | `partition-registry-entries.json`, `replay-cases.json`, `codex_policy_controls.py` | `test-policy-control-contracts.py` |
| FR-035-FR-039 | SC-014-SC-017 | `replay-cases.json`, `codex_control_smoke.py` | `test-policy-control-contracts.py` |
| FR-042 | SC-019 | All 12 declared implementation paths and this packet | All three unit owners plus final docs/full-suite verification |

The canonical task-level mapping is retained in the `tasks.md` Coverage Matrix.

## Verification Evidence

- Policy owner: 689/689 assertions passed at the T033 boundary.
- Comparison owner: 170/170 assertions passed at the T033 boundary.
- Twin handoff owner: 41/41 assertions passed at the T033 boundary.
- Deterministic replay fixture: 18/18 cases passed.
- Privacy scan: 10/10 assertions passed after the raw-capture exclusion fix.
- Final narrow verification passed at the same counts above.
- Docs reference generation produced 7 pages and the subsequent reference check
  reported the pages current.
- The authoritative default repository suite passed 5142/5142: Layer 1
  1428/1428, Layer 4 3528/3528, and Layer 5 186/186.

## Known Gaps

- Live ChatGPT-sign-in smoke execution is operator-only and remains unrun.
  Deterministic replay and unrun/refusal smoke-plan validation are implemented;
  no live smoke outcome is claimed.
- SC-014-SC-016 therefore have deterministic contract evidence but no
  operator-authorized live observation.
- Final reconciliation found zero unrepresentable members, so no FR-041
  follow-up reconciliation item is currently required.

## Rollback And Non-Applicability

Rollback is removal of the 9 additive Codex-local test-tree files and
reversion of the additions in the 3 existing unit owners. No runtime migration,
data migration, production rollback, installer rollback, or release rollback
applies.

No production routing, installer, manifest, scheduler, default, or release
integration behavior changed.

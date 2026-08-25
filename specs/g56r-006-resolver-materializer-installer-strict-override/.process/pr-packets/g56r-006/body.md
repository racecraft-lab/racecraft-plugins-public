# feat(g56r-006): Add capability-aware agent installation

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds trusted capability-aware Codex agent resolution, canonical materialization, strict overrides, and rollback-safe installation.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added closed trusted route-policy activation with a single capability snapshot for the required 12-agent roster and one optional helper.
- Extended canonical materialization to bind source bytes, selected model and effort, unchanged non-route contracts, and destination proofs.
- Added strict override, ownership-safe helper removal, anchored no-clobber mutation, exhaustive rollback, and structured cleanup evidence across POSIX and Windows.
- Added deterministic fake-home and mocked Win32 adversarial coverage.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This provides the safe reusable resolver/materializer/installer framework required before G56R-007 through G56R-010 can qualify and enable production routing policies.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review the manifest, response, and fixture contracts.
2. Review canonical route materialization and proof fields.
3. Review installer resolution, strict override, ownership, apply, rollback, and cleanup evidence.
4. Review the focused mutation/materialization tests, then the generated payload and trust mirrors.

## How To UAT

Run the deterministic fake-home installer and materializer suites. Live installed-home UAT is intentionally deferred to G56R-011.

## UAT Runbook

1. Run `python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` and expect 196/196.
2. Run `python3 tests/speckit-pro/unit/test-agent-materialization.py` and expect 11/11.
3. Run `python3 tests/speckit-pro/unit/test-canonical-agent-materializer.py` and expect 17/17.
4. Confirm no real user-home files were mutated.

## Verification

- Independent attack review at `c2e9d6c89`: 0 Important, 0 nits.
- Focused installer: 196/196.
- Route materializer: 11/11.
- Canonical materializer: 17/17.
- Full deterministic suite: 14352/14352 (L1 1511, L4 12622, L5 219).
- Release artifacts and docs references current; diff whitespace clean.

## Scope

- One atomic resolver/materializer/installer vertical slice.
- 12,542 authored added lines versus 385 planned, accepted by a typed atomic-safety reviewability exception.
- Generated payloads, installed-cache mirrors, docs/planning artifacts, and implementation notes are excluded from authored scope.
- No live model calls or real-user-home acceptance writes.

## Known Gaps

- Native Windows filesystem execution was not run in this macOS worktree; deterministic mocked Win32 contract tests cover that boundary.
- Production route qualification/default activation and final downstream roster composition remain in G56R-007 through G56R-011.

## Release Note

```release-note
Adds capability-aware Codex agent installation with trusted route policy validation, strict overrides, and rollback-safe file handling.
```

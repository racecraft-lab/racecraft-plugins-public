# State Management Checklist: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Purpose**: Validate fake-home state identity, write boundaries, and replay state transitions.
**Created**: 2026-08-22
**Feature**: [spec.md](../spec.md)

## Fake-Home Boundary

- [x] CHK001 Checked-in fake-home fixtures are immutable seeds.
- [x] CHK002 Mutation replay requires a harness-created temporary `fake_home_root`.
- [x] CHK003 The only writable destination is `<fake_home_root>/.codex/agents`.
- [x] CHK004 Real homes, traversal, symlink traversal, and out-of-bound destinations are rejected.

## State Identity

- [x] CHK005 Pre-state, final-state, and previous-known-good IDs use canonical manifests.
- [x] CHK006 Canonical manifests include sorted fake-home-relative paths, SHA-256 content digests, modes, and role classification.
- [x] CHK007 Absolute temporary roots, mtimes, inodes, timestamps, and host-specific paths are excluded.

## Transition Semantics

- [x] CHK008 Failure before managed-file touch skips rollback and proves identical pre/final state IDs.
- [x] CHK009 Failure after managed-file touch triggers rollback and bounded cleanup.
- [x] CHK010 Successful rollback restores exact pre-state and reports `writes_state=false`.
- [x] CHK011 Previous-known-good state remains recoverable when replacement cannot complete.

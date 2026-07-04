# Error-Handling Checklist: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Purpose**: Validate that XPLAT-006 defines deterministic failure behavior for mutation, install, doctor, PR-emission, and hardening paths.
**Created**: 2026-07-03
**Feature**: [spec.md](../spec.md)

## Existing Behavior Preservation

- [x] ERR001 Functional requirements preserve current stdout JSON schemas, stderr diagnostics, human-readable remediation text, and documented exit-code semantics.
- [x] ERR002 Bash-reference comparison is required before Python behavior can become authoritative for Bash-backed mutation helpers.
- [x] ERR003 Promotion records must identify normalized fields and distinguish golden-only, Bash-compared, Python-authoritative, deferred, and out-of-scope helpers.

## Mutation Failure Cases

- [x] ERR004 Dry-run/apply divergence is represented explicitly in mutation helper request/result contracts.
- [x] ERR005 No-op, dirty-worktree, invalid-input, malformed-JSON, missing-prerequisite, path-boundary, symlink, write-failure, and partial-failure cases are required fixture coverage.
- [x] ERR006 Multi-operation helpers must preflight before the first write and report partial failure with rollback/manual-remediation notes instead of promising global rollback.
- [x] ERR007 Live repository, user-local, plugin-cache, and GitHub command-plan apply returns deterministic deferred-live-mutation diagnostics in XPLAT-006.

## Doctor And Install Failures

- [x] ERR008 Doctor/preflight classifications cover complete, safe repair, unsafe manual remediation, blocked, stale release, downgrade refusal, malformed inventory, and source-truth checksum mismatch.
- [x] ERR009 Repair behavior is a separate apply-mode operation and cannot run from the read-only doctor path.
- [x] ERR010 Fake-home fixtures must cover missing agents, stale cache, missing runner files, checksum mismatch, missing generated payload files, malformed inventory, real-home refusal, and blocked repair.

## Hardening Failure Cases

- [x] ERR011 Phase-coverage validation fails deterministically for missing Phase 6.5, missing canonical Post items, collapsed or semantically mislabeled later phases, duplicate state steps, malformed state JSON, and multiple in-progress items.
- [x] ERR012 The current workflow/state pair has passing validator evidence before Checklist proceeds.

## Notes

- Gaps: None.
- Consensus: Skipped because all error-handling checks are satisfied by current spec, plan, contracts, workflow, and focused hardening evidence.

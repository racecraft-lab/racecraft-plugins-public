# UAT Runbook: xplat-006-mutation-install-pr-emission-helper-port

| Field | Value |
|-------|-------|
| Spec | xplat-006-mutation-install-pr-emission-helper-port |
| Branch | xplat-006-mutation-install-pr-emission-helper-port |
| PR | Pending until PR is opened |
| Generated from | 2026-07-03T19:55:50Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| TYPECHECK | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| LINT | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| LINT_FIX | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| UNIT_TEST | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| INTEGRATION_TEST | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| SINGLE_FILE_INTEGRATION | <unknown — autopilot did not pass PROJECT_COMMANDS> |

## Per-Story Acceptance Tests

### User Story 1 - Run Mutation Helpers Safely (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

### User Story 2 - Verify Install Completeness And Safe Repair (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

### User Story 3 - Review Deterministic Parity Evidence (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| User Story 1 - Run Mutation Helpers Safely (Priority: P1) | see the Per-Story Acceptance Tests block above |
| User Story 2 - Verify Install Completeness And Safe Repair (Priority: P1) | see the Per-Story Acceptance Tests block above |
| User Story 3 - Review Deterministic Parity Evidence (Priority: P2) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- A request names an unknown helper id, mismatched operation, unsupported mode, or a mixed-mode helper whose read-only behavior was already accepted in XPLAT-005.
- A dry-run request would plan no operations because the target output is already current.
- An apply request targets a repository with a dirty worktree, missing Git metadata, missing fake CLI, malformed fixture JSON, or stale expected manifest.
- A helper input path contains Windows-style separators, spaces, relative components, symlinks, or attempts to escape the repo, plugin, fake-home, or fake-cache boundary.
- Atomic write setup fails because the target directory is missing, unwritable, cross-device, or already contains an incompatible file type.
- A generated output is partially written, a backup cannot be created, or a rollback cannot be completed automatically.
- Fake `gh`, fake `git`, or fake `specify` returns a conflict, network-like error, malformed JSON, or an unexpected success shape.
- The install doctor finds complete source bundles but incomplete generated payload files or mismatched runner manifest/checksum metadata.
- The install inventory is malformed, source truth has a checksum mismatch, installed metadata is newer than selected inventory, or source/dist/marketplace versions disagree.
- A repair request targets the real home, real plugin cache, or repository state without explicit approval, or attempts to repair outside fake/plugin-owned boundaries.
- A live PR-emission, restack, migration, or relocation request supplies only a boolean approval flag or CLI switch instead of auditable approval evidence tied to prior dry-run output.
- An autopilot workflow or `autopilot-state.json` plan omits Phase 6.5, collapses later phase families, or drops canonical Post items while a run is still incomplete.
- A live mutation path is requested without prior dry-run evidence and explicit operator approval.
- A proposed implementation touches active invocation paths, hook configuration, generated-payload selection/cutover, public docs, release gates, or native installed-cache claims outside the explicit autopilot phase-coverage hardening scope.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

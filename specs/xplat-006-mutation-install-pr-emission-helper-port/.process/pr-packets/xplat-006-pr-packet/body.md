<!-- speckit-pro-review-packet-source: specs/xplat-006-mutation-install-pr-emission-helper-port/.process/pr-packets/xplat-006-pr-packet/packet.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
This PR implements: Add mutation, install, and PR-emission helper port.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification and changed-file scope.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Updated the Python runner implementation for the requested feature behavior.
- Added or updated focused Layer 4 coverage and fixtures for the changed behavior.
- Added or updated the source spec, task, UAT, and review packet evidence for reviewer traceability.
- Updated roadmap, workflow, or repository guidance that tracks the feature state.
<!-- speckit-pro-editable:what_changed:end -->

Source: generated PR packet changed-file evidence.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Reviewers can evaluate the actual implementation, its verification evidence, and its scope limits without reverse-engineering the packet metadata.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Start with the implementation files changed for this feature.
2. Review the focused tests and fixtures that prove the expected behavior and rejected-input paths.
3. Check the scope notes and UAT runbook to confirm deferred work is not being claimed here.

## How To UAT

Use the UAT runbook below for reviewer-facing acceptance checks. Treat installed-plugin, native-platform, and public-support claims as out of scope unless the runbook explicitly includes them.

## UAT Runbook

# UAT Runbook: xplat-006-mutation-install-pr-emission-helper-port

| Field | Value |
|-------|-------|
| Spec | xplat-006-mutation-install-pr-emission-helper-port |
| Branch | codex/xplat-006-mutation-install-pr-emission-helper-port |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/281 |
| Generated from | 2026-07-03T19:55:50Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Check | Command or disposition |
|-------|------------------------|
| BUILD | No compiled build step for this plugin repository |
| TYPECHECK | `python3 -m py_compile speckit-pro/speckit_pro_runner/helpers/mutation.py speckit-pro/speckit_pro_runner/helpers/install.py speckit-pro/speckit_pro_runner/helpers/pr_emission.py speckit-pro/speckit_pro_runner/helpers/promotion.py` |
| LINT | `git diff --check` |
| LINT_FIX | Not applicable; no formatter-managed files changed |
| UNIT_TEST | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` |
| INTEGRATION_TEST | `bash tests/speckit-pro/run-all.sh` |
| SINGLE_FILE_INTEGRATION | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` |

## Per-Story Acceptance Tests

### User Story 1 - Run Mutation Helpers Safely (Priority: P1)

- [x] Run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` and confirm dry-run leaves target files untouched, apply writes atomically, dirty-worktree apply fails closed, symlink/external paths are rejected, write failures return `write_failure`, and partial failures report applied operations plus manual remediation.
- [x] Confirm `bash tests/speckit-pro/run-all.sh` includes `test-speckit-pro-mutation-helpers (11/11)` so the hardening remains in the default deterministic suite.

### User Story 2 - Verify Install Completeness And Safe Repair (Priority: P1)

- [x] Run the same mutation-helper test and confirm `doctor-preflight` reports `safe_repair` for missing fake-home inventory files, `doctor-repair` applies only with `fake_home=true`, a second preflight reports `complete`, malformed inventory returns `malformed_inventory`, and non-fake-home repair returns `real_home_refused`.
- [x] Confirm `speckit-pro/speckit_pro_runner/install_inventory.json` is present and runner manifest/checksum metadata is current via `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py`.

### User Story 3 - Review Deterministic Parity Evidence (Priority: P2)

- [x] Run `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` and confirm XPLAT-005 read-only registry compatibility remains intact with no mutation modes exposed there.
- [x] Run `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD` and confirm the typed infra reviewability exception is honored for this one-workflow XPLAT-006 PR.
- [x] Review `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json` and confirm no Bash-backed helper is marked Python-authoritative in this PR.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| User Story 1 - Run Mutation Helpers Safely (Priority: P1) | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` covers dry-run, apply, dirty worktree, path rejection, write failure, and partial failure |
| User Story 2 - Verify Install Completeness And Safe Repair (Priority: P1) | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` covers doctor safe repair, complete status, malformed inventory, and real-home refusal |
| User Story 3 - Review Deterministic Parity Evidence (Priority: P2) | `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` and `bash tests/speckit-pro/run-all.sh` cover compatibility and aggregate proof |


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

**Self-Review:** The implementation keeps active Claude/Codex invocation cutover, generated-payload selection, release-gate migration, native matrix UAT, and public platform claims out of XPLAT-006. Remaining Bash parity and active cutover are explicitly deferred to XPLAT-007/XPLAT-008.

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations
## Verification

- Run the focused and repository-level verification commands listed in the UAT runbook.
- Confirm generated packet validation passes before using this body for PR creation.

Source: generated PR packet.

## Scope

- Source feature: specs/xplat-006-mutation-install-pr-emission-helper-port.
- Changed files recorded in packet metadata: 60.
- Scope: this PR implements Add mutation, install, and PR-emission helper port.
- Traceability: source feature, rendered body, validation, and changed-file scope are recorded in the packet metadata.
- Non-goals: split PR emission, unrelated install/update behavior, and claims not covered by the UAT runbook.

## Known Gaps

No known gaps are recorded by the generated packet. Review the UAT runbook and source spec for feature-specific deferred work.

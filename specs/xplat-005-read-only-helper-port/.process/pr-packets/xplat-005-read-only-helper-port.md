<!-- speckit-pro-review-packet-source: specs/xplat-005-read-only-helper-port/.process/pr-packets/xplat-005-read-only-helper-port.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
This PR implements: Add read-only helper port.
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

# UAT Runbook: xplat-005-read-only-helper-port

| Field | Value |
|-------|-------|
| Spec | xplat-005-read-only-helper-port |
| Branch | xplat-005-read-only-helper-port |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/276 |
| Generated from | 2026-07-02T16:19:35Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

1. Confirm you are on branch `codex/xplat-005-read-only-helper-port`.
2. Confirm Python 3.11+ is available with `python3 --version`.
3. Use the repository source checkout only. Do not install or refresh the plugin cache for this UAT.
4. Use `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh` for the focused helper check.
5. Use `bash tests/speckit-pro/run-all.sh` for the deterministic repository gate.

## Per-Story Acceptance Tests

### User Story 1 - Run Read-Only Helpers Through The Runner (Priority: P1)

- [ ] Run `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/smoke-runtime-info-request.json` and confirm the response has `status:"ok"` and `source_vs_installed_context:"source_checkout"`.
- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh` and confirm `32/32 passed`.
- [ ] Inspect `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json` and confirm every in-scope helper has a `python_authoritative` promotion record, deterministic remediation, path-boundary policy, rollback note, and authoritative command.

### User Story 2 - Add Helper Ports Through A Small Registry Pattern (Priority: P2)

- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh --helper helper-registry-dispatch` and confirm the registry lists only read-only helper operations and no mutation modes.
- [ ] Inspect `speckit-pro/speckit_pro_runner/helpers/registry.py` and confirm each helper has an explicit helper id, operation, comparison mode, promotion status, and out-of-scope mutation modes where applicable.
- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` and confirm the runner metadata covers `helpers/__init__.py`, `helpers/registry.py`, and `helpers/read_only.py`.

### User Story 3 - Review Release-Gate Promotion And Scope Boundaries (Priority: P3)

- [ ] Run `bash tests/speckit-pro/run-all.sh --layer 4` and confirm `2135/2135 passed`.
- [ ] Run `bash tests/speckit-pro/run-all.sh` and confirm `3778/3778 passed`.
- [ ] Review `git diff --name-only origin/main...HEAD` and confirm there are no active cutover edits outside the bounded PR-review packet rendering remediation files allowed by the spec.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| User Story 1 - Run Read-Only Helpers Through The Runner (Priority: P1) | Runtime-info smoke plus focused helper suite return passing runner envelopes and helper parity evidence. |
| User Story 2 - Add Helper Ports Through A Small Registry Pattern (Priority: P2) | Registry dispatch test lists only read-only helpers, and runner metadata covers helper modules. |
| User Story 3 - Review Release-Gate Promotion And Scope Boundaries (Priority: P3) | Layer 4/default suites pass and changed-file review confirms no active cutover or public-claim surfaces changed. |


## Negative-Path Tests


- A helper currently reads optional files that may not exist in older or partially scaffolded feature directories.
- A helper currently emits duplicate or repeated markers, warnings, or advisory findings that must remain stable for downstream gates.
- A helper currently accepts paths with spaces, symlinks, relative components, or Windows-style separators.
- A fixture includes JSON object field ordering that must be compared semantically, while stream text and exit codes remain exact unless an explicit normalization rule applies.
- A helper's current Bash reference depends on source-checkout state; installed-cache and user-local state are not used as parity inputs in XPLAT-005.
- Late `validate-pr-packet` coverage must remain read-only validation only; PR body generation, PR emission, split PR state, and restack behavior are excluded.

## Self-Review Findings

**Self-Review:** The implementation stays runner-owned and source-checkout-only. It adds Python-native read-only helper dispatch, focused parity fixtures, metadata coverage, and UAT evidence without switching active Claude/Codex invocation paths or making public platform-support claims.

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

- Source feature: specs/xplat-005-read-only-helper-port.
- Changed files recorded in packet metadata: 49.
- Scope: this PR implements Add read-only helper port.
- Traceability: source feature, rendered body, validation, and changed-file scope are recorded in the packet metadata.
- Non-goals: split PR emission, unrelated install/update behavior, and claims not covered by the UAT runbook.

## Known Gaps

No known gaps are recorded by the generated packet. Review the UAT runbook and source spec for feature-specific deferred work.

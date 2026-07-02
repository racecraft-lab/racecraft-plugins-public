# UAT Runbook: xplat-005-read-only-helper-port

| Field | Value |
|-------|-------|
| Spec | xplat-005-read-only-helper-port |
| Branch | xplat-005-read-only-helper-port |
| PR | Pending until PR is opened |
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
- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh` and confirm `7/7 passed`.
- [ ] Inspect `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json` and confirm every in-scope helper has a `python_authoritative` promotion record, deterministic remediation, path-boundary policy, rollback note, and authoritative command.

### User Story 2 - Add Helper Ports Through A Small Registry Pattern (Priority: P2)

- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh --helper helper-registry-dispatch` and confirm the registry lists only read-only helper operations and no mutation modes.
- [ ] Inspect `speckit-pro/speckit_pro_runner/helpers/registry.py` and confirm each helper has an explicit helper id, operation, comparison mode, promotion status, and out-of-scope mutation modes where applicable.
- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` and confirm the runner metadata covers `helpers/__init__.py`, `helpers/registry.py`, and `helpers/read_only.py`.

### User Story 3 - Review Release-Gate Promotion And Scope Boundaries (Priority: P3)

- [ ] Run `bash tests/speckit-pro/run-all.sh --layer 4` and confirm `2108/2108 passed`.
- [ ] Run `bash tests/speckit-pro/run-all.sh` and confirm `3751/3751 passed`.
- [ ] Review `git diff --name-only origin/main...HEAD` and confirm there are no edits under active skill, hook, generated payload, install, marketplace, docs-site, PR-emission, split-state, restack, relocation, install repair, or autoheal surfaces.



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

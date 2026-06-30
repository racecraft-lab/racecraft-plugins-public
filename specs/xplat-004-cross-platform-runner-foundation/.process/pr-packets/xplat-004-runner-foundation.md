<!-- speckit-pro-review-packet-source: specs/xplat-004-cross-platform-runner-foundation/.process/pr-packets/xplat-004-runner-foundation.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Add a Python standard-library runner foundation for XPLAT-004.
<!-- speckit-pro-editable:summary:end -->

Source: XPLAT-004 specification defines the runner foundation behavior.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added the source-checkout `speckit_pro_runner` package with JSON request/response handling, preflight checks, typed path validation, subprocess fixture execution, and runner metadata verification.
- Added contract fixtures, Layer 4 runner coverage, generated tests reference refresh, and process evidence for the XPLAT-004 branch.
<!-- speckit-pro-editable:what_changed:end -->

Source: runner contracts and tests define the review boundary.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This establishes the no-new-runtime-dependency runner seam for future helper ports without cutting over installed-plugin behavior or making public support claims early.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Inspect `speckit-pro/speckit_pro_runner/` for the Python stdlib runner envelope, runtime reporting, preflight checks, and metadata verification.
2. Inspect `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` plus `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json` for contract coverage.
3. Confirm the branch does not change `dist/**`, active skills/hooks, installed-plugin launch behavior, or public support claims.

## How To UAT

Use the UAT Runbook below for reviewer-facing acceptance checks. Native installed-cache execution remains deferred to XPLAT-007.

## UAT Runbook

# UAT Runbook: xplat-004-cross-platform-runner-foundation

| Field | Value |
|-------|-------|
| Spec | xplat-004-cross-platform-runner-foundation |
| Branch | xplat-004-cross-platform-runner-foundation |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/274 |
| Generated from | 2026-06-30T04:01:02Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

- Confirm the branch is `codex/xplat-004-cross-platform-runner-foundation`.
- Run `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`.
- Run `bash tests/speckit-pro/run-all.sh --layer 1`.
- Run `bash tests/speckit-pro/run-all.sh --layer 4`.
- Run `bash tests/speckit-pro/run-all.sh`.
- Optional manual smoke: run `<python> -m speckit_pro_runner` with `PYTHONPATH=speckit-pro` and a `runtime-info` request from `quickstart.md`.

## Per-Story Acceptance Tests

### User Story 1 - Structured runner preflight (Priority: P1)

- [ ] Send a `runtime-info` request through `<python> -m speckit_pro_runner` and confirm stdout contains exactly one JSON response with runner identity, Python version, platform, architecture, `source_checkout`, typed metadata paths, and `metadata.verification_status: "not_checked"`.
- [ ] Send a `preflight` request using test-controlled valid prerequisites and metadata status, and confirm `status: "ok"`, exit code `0`, and prerequisite records for Python and `specify`.
- [ ] Send preflight requests with test overrides for too-old Python, missing `specify`, and missing plugin root, and confirm fail-closed `missing_prerequisite` responses with structured diagnostics on stdout and line-delimited JSON stderr.

### User Story 2 - Contract fixture runway for helper ports (Priority: P2)

- [ ] Run `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` and confirm the contract fixture suite passes.
- [ ] Inspect `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json` and confirm it covers valid envelope, invalid JSON, invalid envelope, unsupported schema, missing field, typed path, subprocess nonzero, subprocess timeout, and stderr-only failure cases.
- [ ] Confirm subprocess fixture records use argv arrays, `shell: false`, explicit timeouts at or below 5 seconds, 16 KiB stream limits, byte counts, duration, and truncation flags.

### User Story 3 - Inspectable runner identity and source metadata (Priority: P3)

- [ ] Validate `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` with `python3 -m json.tool`.
- [ ] Confirm `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` and the manifest cover every runner-owned `*.py` file and exclude the manifest/checksum files themselves.
- [ ] Confirm `git diff --name-only origin/main...HEAD` has no `dist/**`, active skill/hook/generated payload/install cutover, or public documentation support-claim changes.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| User Story 1 - Structured runner preflight (Priority: P1) | Runtime-info, valid preflight, and fail-closed prerequisite checks |
| User Story 2 - Contract fixture runway for helper ports (Priority: P2) | Contract fixture suite and subprocess/typed-path fixture inspection |
| User Story 3 - Inspectable runner identity and source metadata (Priority: P3) | Manifest/checksum validation and no-cutover diff review |


## Negative-Path Tests


- The runtime prerequisite is missing, too old, or resolves to an unsupported executable.
- The SpecKit `specify` prerequisite is missing or not discoverable from the runner environment.
- The plugin root cannot be found from the invocation context.
- The JSON request is malformed, missing required fields, or names an unsupported runner action.
- Paths contain spaces, Windows-style separators, relative traversal segments, or non-existent targets.
- A subprocess fixture exits non-zero, writes to standard error, emits large but bounded output, or exceeds its configured timeout.
- Runner metadata is absent, stale, incomplete, or does not cover all runner-owned source files.

## Self-Review Findings

Recorded before final push:
- Focused runner tests passed.
- Default deterministic SpecKit Pro suite passed.
- Generated docs reference and docs quality checks passed.
- Scope boundaries preserve no installed-plugin cutover and no public support claim.
- Native Windows/Linux installed-cache execution remains runbook-only for XPLAT-007.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations
## Verification

- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` passed, 9/9.
- `bash tests/speckit-pro/run-all.sh` passed, 3713/3713.
- `node docs-site/scripts/generate-reference-pages.mjs --check` passed.
- `node docs-site/scripts/validate-docs-quality.mjs` passed.
- `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh specs/xplat-004-cross-platform-runner-foundation/.process/pr-packets/xplat-004-runner-foundation.json` passed.

Source: generated PR packet.

## Scope

- Source feature: `specs/xplat-004-cross-platform-runner-foundation`.
- Scope: source-checkout Python stdlib runner package, runner manifest/checksum metadata, contract fixtures, runner tests, generated tests reference refresh, and process evidence.
- Traceability: source feature, runner body, validation, and changed-file scope are recorded in the packet metadata.
- Non-goals: generated payload propagation, active skill/hook/install cutover, native installed-cache UAT, and public platform-support claims.

## Known Gaps

Native Windows/Linux installed-cache UAT, generated payload propagation, and public support claims remain deferred to XPLAT-007. No active skill invokes the runner yet.

# UAT Runbook: xplat-004-cross-platform-runner-foundation

| Field | Value |
|-------|-------|
| Spec | xplat-004-cross-platform-runner-foundation |
| Branch | xplat-004-cross-platform-runner-foundation |
| PR | Pending until PR is opened |
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

Before PR creation, record:
- Tests executed.
- Scope boundaries preserved.
- Known gaps.
- Whether native Windows/Linux execution happened or remains runbook-only for XPLAT-007.
- Review order for the two planned slices.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

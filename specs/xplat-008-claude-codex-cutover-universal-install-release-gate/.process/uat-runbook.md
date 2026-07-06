# UAT Runbook: xplat-008-claude-codex-cutover-universal-install-release-gate

| Field | Value |
|-------|-------|
| Spec | xplat-008-claude-codex-cutover-universal-install-release-gate |
| Branch | codex/xplat-008-claude-codex-cutover-universal-install-release-gate |
| PR | Pending until PR is opened |
| Generated from | 2026-07-05T22:04:02Z |



## Env Setup

Use a clean checkout of this branch from the repository root. This repository
has no compiled build step; validation is done through the shell test harness,
the Python runner gates, and docs-site validation.

Run these checks before reviewer walk-through:

1. `bash tests/speckit-pro/run-all.sh --layer 1`
2. `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
3. `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/requests/active-runtime-guard.json`
4. `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/requests/payload-completeness.json`
5. `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/requests/release-readiness.json`
6. `npx --yes pnpm@10.25.0 --dir docs-site validate`

Native platform support remains blocked until separate operators fill the six
Claude/Codex Windows, macOS, and Linux rows in `.process/uat-matrix.md`.

## Per-Story Acceptance Tests

### User Story 1 - Install and run first use without shell prerequisites (Priority: P1)

1. Open `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/active-runtime-inventory.md` and confirm active installed surfaces are identified separately from archive, fixture, and CI-only text.
2. Run the active runtime guard command from Env Setup.
3. Confirm the JSON response reports `status: "ok"`, `gate_status: "pass"`, and `blocking_count: 0`.
4. Inspect `speckit-pro/hooks/hooks.json` and `speckit-pro/codex-hooks.json`; each hook should check `speckit_pro_runner` availability and should not contain `jq`, `command -v specify`, or a required Bash/WSL/Git Bash path.
5. Confirm this story is not release-ready by itself: real native first-use journeys still need platform evidence in `.process/uat-matrix.md`.

- [ ] Reviewer confirmed the installed-runtime source surfaces are guarded and do not claim native first-use proof before platform evidence exists.

### User Story 2 - Verify generated release payload completeness (Priority: P2)

1. Run the payload completeness command from Env Setup.
2. Confirm the JSON response reports `gate_status: "pass"` for both generated payload families.
3. Inspect `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`; both should include runner files, manifests, hooks, skills, agents, README, changelog, license, and checksum metadata.
4. Confirm the payload was rebuilt through the runner apply-mode request rather than by hand-editing generated files.

- [ ] Reviewer confirmed the committed generated payloads match the source-derived inventory.

### User Story 3 - Update and repair installed plugins safely (Priority: P3)

1. Run `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/requests/install-health-repair.json`.
2. Confirm the JSON response shows trusted missing or stale artifacts are refreshed only when source identity and expected digests are known.
3. Inspect the install-health fixture cases and confirm unsafe drift, extra unknown files, out-of-cache paths, and broad reinstall actions are rejected with manual remediation.
4. Confirm real update and repair proof remains pending for each native platform row in `.process/uat-matrix.md`.

- [ ] Reviewer confirmed repair behavior is bounded and native update/repair proof is not overstated.

### User Story 4 - Review public evidence and trust claims (Priority: P4)

1. Open `README.md`, `speckit-pro/README.md`, and the docs-site install, first-run, troubleshooting, security, update, and release workflow pages touched by this branch.
2. Confirm public guidance names Python 3.11+ as the installed runtime prerequisite without requiring Bash, Git Bash, WSL, PowerShell-specific command language, or `jq`.
3. Confirm trust wording is limited to implemented runner, inventory, checksum, payload, update, and repair controls. It must not claim signing, SBOM, SLSA, formal audit, vulnerability-free status, or marketplace-enforced verification.
4. Run the release-readiness command from Env Setup and confirm the fixture-backed positive case passes.
5. Open `.process/release-readiness.md` and confirm the release decision remains blocked until real native operator evidence replaces the pending UAT rows.

- [ ] Reviewer confirmed public claims are implemented-only and the release blocker is visible.



## FR Coverage Matrix

| Behavior | Acceptance check |
|-------|-----------------|
| Active installed surfaces use the Python runner and avoid legacy shell-only prerequisites | User Story 1, steps 1-4 |
| The PR does not claim native first-use support before platform evidence exists | User Story 1, step 5; User Story 4, step 5 |
| Generated Claude and Codex payloads match the source inventory | User Story 2, steps 1-4 |
| Release payloads include runner, hook, agent, manifest, checksum, and version metadata | User Story 2, step 3 |
| Install repair is limited to trusted missing or stale artifacts | User Story 3, steps 1-3 |
| Unsafe install drift leads to manual remediation, not broad reinstall | User Story 3, step 3 |
| Public docs describe only implemented support and trust controls | User Story 4, steps 1-3 |
| The release packet maps changed files, verification, non-goals, and blockers | User Story 4, steps 4-5 |


## Negative-Path Tests


1. Add a required `jq` or Bash-only command to an active installed skill or hook, then run the active runtime guard. Expected result: the guard reports a blocking finding.
2. Put the same shell wording in archive/provenance or test fixture text, then run the active runtime guard. Expected result: the guard keeps that text in a non-blocking exception class.
3. Delete a runner file from `dist/codex/speckit-pro/`, then run the payload completeness request. Expected result: the request reports the missing generated payload path.
4. Leave a row in `.process/uat-matrix.md` as `PENDING` or mark a row as smoke-only, then run the release-readiness check against real matrix evidence. Expected result: release readiness blocks native support publication.
5. Add a public doc claim for signing, SBOM, SLSA, formal audit, vulnerability-free status, or marketplace-enforced verification, then run the public-claim release-readiness cases. Expected result: the claim is rejected unless a separate implementation and evidence exists.
6. Add an install repair action that wipes or broadly reinstalls the plugin cache, then run the install-health repair cases. Expected result: the repair action is rejected and manual remediation is required.

## Self-Review Findings

**Self-Review:** The deterministic gates, generated payloads, public docs, and
repair controls are reviewable. Native Windows/macOS/Linux Claude and Codex UAT
evidence remains pending and must not be treated as release-ready support.

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

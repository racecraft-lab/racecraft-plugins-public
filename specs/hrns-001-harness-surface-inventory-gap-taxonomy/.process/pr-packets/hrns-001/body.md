# fix(speckit-pro): Enable PR packet emission

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds the HRNS-001 harness surface inventory and gap taxonomy, and fixes the SpecKit Pro packet-emission bug that blocked autopilot PR creation.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Adds the canonical HRNS-001 taxonomy, spec artifacts, workflow state, and verification report.
- Promotes pr-packet-output and validate-pr-packet-write so autopilot can create the required machine-readable packet before opening a PR.
- Hardens packet validation persistence with packet/body source fingerprints so stale validations cannot be written after source drift.
- Hardens mutation writes against symlink/path races, preserves file modes, rolls back created directories, and reports live mutations accurately.
- Tightens protected PR-body hashing and marker validation so pre-H1 content, trailing content, and crossed editable markers are covered.
- Updates Claude Code and Codex autopilot guidance, eval expectations, packaged dist payloads, and installed-cache proof fixtures.
- Adds runner and release-artifact tests proving packet emission, read-only validation, persisted validation, rollback behavior, and mode-drift detection.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This removes a release-blocking failure mode where verified autopilot work could not be published because the workflow required a PR packet that the installed plugin could not create.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review the HRNS taxonomy artifact and spec evidence first.
- Review mutation.py, read_only.py, pr_emission.py, and refresh-release-artifacts.py for the durable failure-mode fixes.
- Review the Claude Code and Codex autopilot guidance updates for lockstep behavior.
- Review generated dist and installed-cache proof changes as package-refresh output.
- Review the new regression tests before treating the PR-packet flow as fixed.

## How To UAT

No manual product UAT is required. Re-run the packet-emission, read-only packet validation, mutation-helper, release reconciliation, and artifact refresh checks listed in Verification.

## UAT Runbook

No manual product UAT is required. Re-run the packet-emission, read-only packet validation, mutation-helper, release reconciliation, and artifact refresh checks listed in Verification.

## Verification

- python3 -m unittest -v tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py passed 34/34.
- python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py --helper validate-pr-packet-read-only passed 49/49.
- python3 -m unittest -v tests/speckit-pro/unit/test-release-pr-reconciliation.py passed 40/40.
- python3 -m unittest -v tests/speckit-pro/unit/test-eval-runner-skill-selection.py tests/speckit-pro/unit/test-privacy-scan.py passed 6/6.
- python3 -m unittest -v tests/speckit-pro/unit/test-post-implementation-reference.py tests/speckit-pro/unit/test-parity-runner.py tests/speckit-pro/unit/test-parity-extractors.py tests/speckit-pro/unit/test-parity-judge.py passed 5/5.
- SPECKIT_SKIP_TOOLCHAIN_CHECK=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json passed Layers 1/4/5/7/8.
- python3 tests/speckit-pro/run-all.py passed 2774/2774.
- git diff --check passed.
- HRNS-001 verify-tasks report recorded 35/35 verified tasks before packet emission.

## Scope

- HRNS-001 specification, workflow state, and taxonomy documentation.
- SpecKit Pro PR packet emission and validation-write runner helpers.
- Mutation-helper and read-only validation hardening for safe packet persistence.
- Claude Code and Codex autopilot guidance, evals, dist payloads, and installed-cache proofs.
- Release artifact reconciliation behavior for mode-only installed-cache drift.
- Regression tests and fixtures proving the failure mode is fixed durably.

## Known Gaps

- final-reviewability-backstop remains deferred; this PR uses current committed reviewability evidence.
- multi-pr-emission remains command-plan only and does not execute live GitHub PR mutations.

## Release note

```release-note
SpecKit Pro autopilot can now emit reviewer PR packets and persist current validation evidence for Claude Code and Codex workflows, preventing completed work from being blocked by missing packet metadata.
```

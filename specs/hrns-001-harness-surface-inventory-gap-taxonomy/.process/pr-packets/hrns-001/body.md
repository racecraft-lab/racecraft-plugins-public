# feat(HRNS-001): Add harness gap taxonomy

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds the HRNS-001 harness surface inventory and gap taxonomy, and fixes the SpecKit Pro packet-emission bug that blocked autopilot PR creation.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Adds the canonical HRNS-001 taxonomy, spec artifacts, workflow state, and verification report.
- Promotes pr-packet-output and validate-pr-packet-write so autopilot can create the required machine-readable packet before opening a PR.
- Updates Claude Code and Codex autopilot guidance, eval expectations, packaged dist payloads, and installed-cache proof fixtures.
- Adds runner tests proving packet emission, read-only validation, and persisted validation work together.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This removes a release-blocking failure mode where verified autopilot work could not be published because the workflow required a PR packet that the installed plugin could not create.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review the HRNS taxonomy artifact and spec evidence first.
- Review the pr_emission.py and registry.py runner changes next.
- Review the Claude Code and Codex autopilot guidance updates for lockstep behavior.
- Review generated dist and installed-cache proof changes as package-refresh output.

## How To UAT

No manual product UAT is required. Re-run the packet-emission unit test, Layer 1 structural validation, and packet validators listed in Verification.

## Verification

- python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py passed 31/31.
- python3 tests/speckit-pro/run-all.py --layer 1 passed 1428/1428.
- python3 -m json.tool passed for edited Claude/Codex eval and packet request fixtures.
- git diff --check passed.
- HRNS-001 verify-tasks report recorded 35/35 verified tasks before packet emission.

## Scope

- HRNS-001 specification, workflow state, and taxonomy documentation.
- SpecKit Pro PR packet emission and validation-write runner helpers.
- Claude Code and Codex autopilot guidance, evals, dist payloads, and installed-cache proofs.
- Mutation-helper tests and fixtures proving packet emission and validation persistence.

## Known Gaps

- final-reviewability-backstop remains deferred; this PR uses current committed reviewability evidence.
- multi-pr-emission remains command-plan only and does not execute live GitHub PR mutations.

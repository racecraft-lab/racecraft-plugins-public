# fix(speckit-pro): Enable PR packet emission

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

- python3 -m unittest -v tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py passed 33/33.
- python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py --helper validate-pr-packet-read-only passed 48/48.
- python3 -m unittest -v tests/speckit-pro/unit/test-eval-runner-skill-selection.py passed 5/5.
- python3 -m unittest -v tests/speckit-pro/unit/test-privacy-scan.py passed 1/1.
- python3 -m unittest -v tests/speckit-pro/unit/test-post-implementation-reference.py passed 1/1.
- python3 -m unittest -v tests/speckit-pro/unit/test-parity-runner.py tests/speckit-pro/unit/test-parity-extractors.py tests/speckit-pro/unit/test-parity-judge.py passed 4/4.
- TITLE='fix(speckit-pro): Enable PR packet emission' BASE_REF='main' PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/release-readiness-live-github.json passed.
- HRNS-001 verify-tasks report recorded 35/35 verified tasks before packet emission.

## Scope

- HRNS-001 specification, workflow state, and taxonomy documentation.
- SpecKit Pro PR packet emission and validation-write runner helpers.
- Claude Code and Codex autopilot guidance, evals, dist payloads, and installed-cache proofs.
- Mutation-helper tests and fixtures proving packet emission and validation persistence.

## Known Gaps

- final-reviewability-backstop remains deferred; this PR uses current committed reviewability evidence.
- multi-pr-emission remains command-plan only and does not execute live GitHub PR mutations.

## Release note

```release-note
SpecKit Pro autopilot can now emit reviewer PR packets and persist current validation evidence for Claude Code and Codex workflows, preventing completed work from being blocked by missing packet metadata.
```

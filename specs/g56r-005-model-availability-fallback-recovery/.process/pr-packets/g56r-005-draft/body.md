# feat(g56r-005): Add model availability fallback and recovery simulation

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds deterministic Codex-local evidence for model availability fallback, service reroute attribution, bounded recovery, and fake-home safety without changing production routing.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added three closed JSON schemas and a reviewed source-roster-bound scenario corpus.
- Added a pure Codex-local resolver, attribution/scoring split, fake-home adapter, recovery record, and bounded sequential harness.
- Added 33 focused tests, Layer 4 registration, traceability evidence, and regenerated repository references.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
G56R-006 can build production routing against a deterministic, fail-closed evidence contract instead of inferring behavior from live model or service availability.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review route-policy and report schemas first.
- Review corpus roster, scenarios, and FR/SC traceability.
- Review codex_route_fallback.py, then the focused tests and suite registration.
- Confirm generated docs/spec-index changes and explicit production-scope exclusions.

## How To UAT

No manual or live UAT is required for this deterministic test-only feature. Re-run the focused test and full repository suite; live reroute smoke is intentionally unrun.

## UAT Runbook

No manual or live UAT is required for this deterministic test-only feature. Re-run the focused test and full repository suite; live reroute smoke is intentionally unrun.

## Verification

- Focused G56R-005 fallback-recovery suite passed 33/33.
- Full deterministic suite passed 7659/7659: L1 1469, L4 5998, L5 192.
- Docs reference, spec-index, release-artifact consistency, workflow coverage, and git diff checks pass.
- Independent review finding was remediated with a focused RED then GREEN contract test.

## Scope

- Deterministic contracts, fixtures, simulation runtime, focused tests, and generated planning/reference evidence.
- Zero production routing or installer files changed.

## Known Gaps

- The Codex task/worktree binding bug is tracked as TODO-CODEX-WORKTREE-BINDING and is outside G56R-005 feature behavior.
- generate-uat-skeleton is deferred and no committed skeleton exists, so UAT runbook generation was skipped fail-open.
- Live model/service reroute smoke was intentionally not run because this spec makes no live availability claim.

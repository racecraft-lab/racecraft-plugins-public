# feat(g56r-003): add evaluation runner scoring

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds a deterministic qualification framework for evaluating agent routes without turning calibration data into production routing decisions.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Publishes an additive, source-bound capability freeze and one canonical agent materializer.
- Adds exact-treatment trace joins, a governed twelve-role corpus, blinded ballots, adjudication, and replayable score bundles.
- Adds calibration-only statistical decisions with frozen budgets, paired non-inferiority, raw Pareto comparison, and fail-closed boundaries.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Later routing cohorts can reuse one auditable evaluation contract while preserving historical evidence and preventing post-hoc qualification decisions.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review capability publication, materialization, and treatment trace joins first.
- Then review corpus authority, hard gates, blinded scoring, and adjudication.
- Finish with frozen experiment policy, statistical sequencing, replay, and calibration-only boundaries.

## How To UAT

No manual UAT runbook was generated because the installed helper is deferred. Run `python3 tests/speckit-pro/run-all.py` and confirm 3251/3251, then run the release-artifact and documentation-reference drift checks.

## UAT Runbook

No manual UAT runbook was generated because the installed helper is deferred. Run `python3 tests/speckit-pro/run-all.py` and confirm 3251/3251, then run the release-artifact and documentation-reference drift checks.

## Verification

- `python3 tests/speckit-pro/run-all.py` — 3251/3251 passed.
- `python3 tests/speckit-pro/unit/test-codex-capability-contract.py` — 99/99 passed.
- `python3 scripts/refresh-release-artifacts.py --check` — current.
- `pnpm --dir docs-site reference:check` — current.
- Final independent code review — zero findings.

## Scope

- Slice 1: capability publication, canonical materialization, and exact-treatment traces.
- Slice 2: governed corpus, hard gates, blinded scoring, adjudication, and score replay.
- Slice 3: experiment contracts, calibration controls, statistical decisions, and analysis replay.

## Known Gaps

- Manual UAT runbook generation is deferred; deterministic verification is complete.
- The optional Claude command directory is absent in this Codex worktree; doctor classified it as a non-blocking configuration warning.

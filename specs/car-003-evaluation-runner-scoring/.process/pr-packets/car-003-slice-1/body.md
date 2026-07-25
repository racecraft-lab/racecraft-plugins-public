# feat(car-003): Add the evaluation platform that turns capability evidence into qualification evidence

## Summary

<!-- speckit-pro-editable:summary:start -->
Generated SpecKit Pro review packet.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- See changed-file scope evidence in the packet.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This prepares the completed SpecKit work for review.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review the changed files and verification evidence in order.

## How To UAT

No manual UAT runbook was provided; use verification evidence for this PR.

## UAT Runbook

No manual UAT runbook was provided; use verification evidence for this PR.

## Verification

- 4143 of 4143 passed on the committed tree, zero failures, zero live model calls. Baseline before this branch was 3251.
- Second run is a genuine no-op. All five copies of the shipped materializer share one hash across source, both payloads, and both installed-cache proofs.
- Reference pages are current. This gate is not covered by the test suite and fails only in clean continuous integration.
- Six fail-open paths found by executing the code and all fixed, each with a test reproducing the permissive behavior first.
- Twenty-four completed tasks opened and verified against real artifacts. No phantom completions found.

## Scope

- .specify/autopilot-state.json
- dist/claude/speckit-pro/speckit_pro_runner/materializer.py
- dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- dist/codex/speckit-pro/speckit_pro_runner/materializer.py
- dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- docs-site/src/content/docs/reference/tests.md
- docs/ai/research/claude-car-003-mandatory-observation-manifest.json
- docs/ai/specs/.process/CAR-003-design-concept.md
- docs/ai/specs/.process/CAR-003-slice-1-pr-packet.md
- docs/ai/specs/.process/CAR-003-slice-2-pr-packet.md
- docs/ai/specs/.process/CAR-003-slice-3-pr-packet.md
- docs/ai/specs/.process/CAR-003-workflow.md
- docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json
- docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- docs/ai/specs/.process/XPLAT-009-release-readiness-result.json
- docs/ai/specs/claude-agent-routing-roadmap-MOC.md
- docs/ai/specs/claude-agent-routing-technical-roadmap.md
- docs/prd-claude-agent-routing.md
- speckit-pro/speckit_pro_runner/materializer.py
- speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- specs/car-003-evaluation-runner-scoring/SPEC-MOC.md
- specs/car-003-evaluation-runner-scoring/checklists/data-integrity.md
- specs/car-003-evaluation-runner-scoring/checklists/error-handling.md
- specs/car-003-evaluation-runner-scoring/checklists/llm-integration.md
- specs/car-003-evaluation-runner-scoring/checklists/performance.md
- specs/car-003-evaluation-runner-scoring/checklists/requirements.md
- specs/car-003-evaluation-runner-scoring/contracts/analysis-decision.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/analysis-plan.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/car-003-additive-records.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/experiment-assignment.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/experiment-policy.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/role-corpus.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/score-bundle.schema.json
- specs/car-003-evaluation-runner-scoring/contracts/successor-capability-freeze.schema.json
- specs/car-003-evaluation-runner-scoring/data-model.md
- specs/car-003-evaluation-runner-scoring/plan.md
- specs/car-003-evaluation-runner-scoring/quickstart.md
- specs/car-003-evaluation-runner-scoring/research.md
- specs/car-003-evaluation-runner-scoring/spec.md
- specs/car-003-evaluation-runner-scoring/tasks.md
- tests/speckit-pro/layer6-efficiency/.gitignore
- tests/speckit-pro/layer6-efficiency/fixtures/car-003-alias-repoint-replay.json
- tests/speckit-pro/layer6-efficiency/fixtures/car-003-calibration-replay.json
- tests/speckit-pro/layer6-efficiency/fixtures/car-003-role-corpus.json
- tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py
- tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py
- tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py
- tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py
- tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py
- tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py
- tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py
- tests/speckit-pro/suite-manifest.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/materializer.py
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/materializer.py
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- tests/speckit-pro/unit/test-analysis-decision-ladder.py
- tests/speckit-pro/unit/test-canonical-agent-materializer.py
- tests/speckit-pro/unit/test-exact-treatment-runner.py
- tests/speckit-pro/unit/test-experiment-policy-partitions.py
- tests/speckit-pro/unit/test-role-corpus-governance.py
- tests/speckit-pro/unit/test-score-bundle-adjudication.py
- tests/speckit-pro/unit/test-speckit-pro-runner.py
- tests/speckit-pro/unit/test-successor-capability-freeze.py

## Known Gaps

- Two operator-only live tasks and the analysis-plan freeze that depends on them remain outstanding by design; freezing invented calibration estimates would bind later cohorts to uncalibrated values.
- Two requirements disagree on how a missing hard-gate failure is coded; both readings are kept visible and a fix must land on both platforms together.
- The sibling platform's experiment policy still cannot validate a calibration run, and the direction-of-preference wording needs mirroring there.
- A rare unreproducible failure was observed twice in one test layer under heavy parallel load; the affected files are untouched by this branch.

## Release note

```release-note
Adds the evaluation platform that turns capability evidence into qualification
evidence for Claude Code agent route selection. Publishes a successor
capability freeze that detects when the platform silently re-points a model
alias, ships a single canonical materializer that proves the exact agent policy
a run received by hashing the bytes written to disk, governs a twelve-role
fixture corpus scored by two blinded ballots with a third adjudicator, and
freezes a replayable decision ladder that qualifies a route only after absolute
floors, paired non-inferiority, and Pareto dominance all pass. A tie, mixed
dominance, incomplete evidence, or statistical uncertainty returns no
qualification rather than a forced ranking. Subscription authentication is the
supported path and no supported path requires an API key. The legacy
prompt-emulation smoke runner is demoted to non-release evidence rather than
deleted.
```

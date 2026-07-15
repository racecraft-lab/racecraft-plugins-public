<!-- speckit-pro-review-packet-source: specs/g56r-001-candidate-route-baseline/.process/pr-packets/g56r-001-single.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Completes the G56R-001 candidate-route baseline and repairs SpecKit Pro autopilot so both Claude Code and Codex must create and verify one source-bound pull request before completion.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Completed the twelve-agent G56R-001 evidence baseline, manifest, checker, focused tests, task audit, and terminal handoff.
- Added schema 1.1 source-bound PR packets, secure atomic output handling, and fail-closed PR completion contracts shared by Claude Code and Codex.
- Regenerated cross-client payload proofs, recorded adversarial official-documentation and community-practice validation, and made all default-suite CI checkouts full-history for frozen revision validation.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Autopilot can no longer report success after deferring the PR boundary, and stale or tampered packets cannot authorize a GitHub side effect.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review the G56R specification, tasks, research narrative, manifest, checker, and focused negative cases as one mutually validating evidence packet.
2. Review the shared runner packet generation and validation path together with both Claude Code and Codex autopilot completion contracts.
3. Confirm the typed infrastructure reviewability exception waives only file-count splitting and does not waive correctness, tests, packet freshness, or live PR verification.

## How To UAT

Run the focused G56R checker tests, runner mutation and read-only tests, integration suite, and default deterministic suite documented in the verification section.

## UAT Runbook

No interactive product path is required; execute the repository commands in the feature quickstart and confirm the source-bound packet validator accepts this committed revision.

## Verification

- Final uninterrupted default deterministic suite passed Layer 1, Layer 4, and Layer 5. Source: tests/speckit-pro/run-all.py. Result: 2814/2814 passed.
- Replay integration fixtures passed after the cross-client recovery changes. Source: tests/speckit-pro/run-all.py. Result: 257/257 passed.
- G56R artifact contract and adversarial negative cases passed. Source: tests/speckit-pro/unit/test-g56r-001-artifacts.py. Result: 56/56 passed.
- Source-bound packet output and secure atomic mutation regressions passed. Source: tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py. Result: 33/33 passed.
- Packet freshness and read-only validation regressions passed. Source: tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py. Result: 48/48 passed.
Source: the G56R-001 specification defines the frozen route-baseline acceptance contract.
Source: the G56R-001 tasks define the completed T001 through T026 execution contract.
Source: the retrospective records adversarial findings, official documentation alignment, and community best-practice disposition.
Source: the workflow records every autopilot phase and the mandatory verified-PR recovery boundary.

## Scope

- Reviewable LOC: 1304
- Production files: 14
- Total files: 127
- Budget result: exception
- Changed files:
  - `.github/workflows/container-preflight.yml`
  - `.github/workflows/pr-checks.yml`
  - `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md`
  - `dist/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
  - `dist/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  - `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
  - `dist/claude/speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
  - `dist/claude/speckit-pro/speckit_pro_runner/helpers/mutation.py`
  - `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
  - `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
  - `dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py`
  - `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
  - `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution-codex.md`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
  - `dist/codex/speckit-pro/speckit_pro_runner/helpers/mutation.py`
  - `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
  - `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
  - `dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py`
  - `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
  - `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
  - `docs-site/src/content/docs/reference/tests.md`
  - `docs/ai/research/codex-agent-route-candidate-manifest.json`
  - `docs/ai/research/codex-agent-route-candidates.md`
  - `docs/ai/specs/.process/G56R-001-design-concept.md`
  - `docs/ai/specs/.process/G56R-001-workflow.md`
  - `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
  - `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
  - `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
  - `docs/ai/specs/.process/autopilot-state.json`
  - `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md`
  - `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
  - `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
  - `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
  - `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`
  - `speckit-pro/skills/speckit-autopilot/SKILL.md`
  - `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
  - `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  - `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
  - `speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
  - `speckit-pro/speckit_pro_runner/helpers/mutation.py`
  - `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
  - `speckit-pro/speckit_pro_runner/helpers/read_only.py`
  - `speckit-pro/speckit_pro_runner/helpers/registry.py`
  - `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
  - `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
  - `specs/g56r-001-candidate-route-baseline/.process/pr-packets/g56r-001-single.json`
  - `specs/g56r-001-candidate-route-baseline/.process/pr-packets/g56r-001-single.md`
  - `specs/g56r-001-candidate-route-baseline/SPEC-MOC.md`
  - `specs/g56r-001-candidate-route-baseline/check-artifacts.py`
  - `specs/g56r-001-candidate-route-baseline/checklists/integration.md`
  - `specs/g56r-001-candidate-route-baseline/checklists/llm-integration.md`
  - `specs/g56r-001-candidate-route-baseline/checklists/reliability.md`
  - `specs/g56r-001-candidate-route-baseline/checklists/requirements.md`
  - `specs/g56r-001-candidate-route-baseline/checklists/security.md`
  - `specs/g56r-001-candidate-route-baseline/contracts/agent-route-candidate-manifest.md`
  - `specs/g56r-001-candidate-route-baseline/contracts/combined-pr-reviewability-exception.md`
  - `specs/g56r-001-candidate-route-baseline/data-model.md`
  - `specs/g56r-001-candidate-route-baseline/plan.md`
  - `specs/g56r-001-candidate-route-baseline/quickstart.md`
  - `specs/g56r-001-candidate-route-baseline/research.md`
  - `specs/g56r-001-candidate-route-baseline/retrospective.md`
  - `specs/g56r-001-candidate-route-baseline/spec.md`
  - `specs/g56r-001-candidate-route-baseline/tasks.md`
  - `specs/g56r-001-candidate-route-baseline/verify-tasks-report.md`
  - `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
  - `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
  - `tests/speckit-pro/layer8-parity/01-post-impl-parity/README.md`
  - `tests/speckit-pro/layer8-parity/01-post-impl-parity/expected-equivalence.json`
  - `tests/speckit-pro/layer8-parity/01-post-impl-parity/tolerance.json`
  - `tests/speckit-pro/layer8-parity/01-post-impl-parity/workflow.md`
  - `tests/speckit-pro/layer8-parity/README.md`
  - `tests/speckit-pro/suite-manifest.json`
  - `tests/speckit-pro/unit/fixtures/mutation-helpers/fixture-manifest.json`
  - `tests/speckit-pro/unit/fixtures/mutation-helpers/promotion-records.json`
  - `tests/speckit-pro/unit/fixtures/mutation-helpers/requests/pr-packet-output.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/SKILL.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/mutation.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/registry.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/SKILL.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution-codex.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/mutation.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/registry.py`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
  - `tests/speckit-pro/unit/fixtures/pr-packet/invalid-missing-evidence.json`
  - `tests/speckit-pro/unit/fixtures/pr-packet/invalid-protected-edit.json`
  - `tests/speckit-pro/unit/fixtures/pr-packet/invalid-title-token.json`
  - `tests/speckit-pro/unit/fixtures/pr-packet/valid-single.json`
  - `tests/speckit-pro/unit/fixtures/pr-packet/valid-split.json`
  - `tests/speckit-pro/unit/test-eval-runner-skill-selection.py`
  - `tests/speckit-pro/unit/test-g56r-001-artifacts.py`
  - `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`
  - `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`
  - `tests/speckit-pro/unit/test-speckit-pro-runner.py`
- Non-goals:
  - Routing qualification and fallback ordering remain owned by downstream G56R specs.
  - This change does not expand public native-platform support claims.
  - The research baseline does not mutate production routes or claim an empirically preferred candidate.

## Known Gaps

- G56R-002 owns runtime capability snapshots and telemetry qualification.
- G56R-003 owns empirical route scoring, uncertainty, and out-of-distribution evaluation.

```release-note
SpecKit Pro autopilot now emits source-bound PR packets and cannot report completion until a single pull request is verified for both Claude Code and Codex.
```

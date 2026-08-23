# fix(art-017): Arm state bookkeeping checks

## Summary

<!-- speckit-pro-editable:summary:start -->
ART-017 makes the three already-reported current-run state bookkeeping invariants stop the scoped autopilot gate while legacy structural coverage debt remains advisory. Both Claude Code and Codex sources and generated payloads are covered.
```release-note
SpecKit autopilot now stops when current-run state bookkeeping contains multiple active steps, duplicate steps, or reordered checkpoints.
```
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Armed exactly in_progress_errors, duplicate_state_steps, and state_order_errors under status-evidence and aligned their intent records.
- Added isolated negative controls, clean/report-shape coverage, deterministic tracked-pair census, and fail-closed corpus error cases.
- Aligned Claude Code and Codex guidance, then regenerated both client payloads, installed-cache proofs, and reference outputs.
- Executed and recorded manual UAT for all 9 acceptance scenarios.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
The autopilot can no longer report contradictory current-run bookkeeping and still continue with exit zero. Maintainers also get one consistent rule, intent, test, manual UAT, and two-client distribution story.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review the validator three-key rule and intent delta first.
- Review the three isolated failure tests, clean control, legacy advisory control, and tracked-pair census.
- Follow the committed UAT runbook and its observed 9/9 results.
- Confirm Claude Code and Codex authored guidance agree, then treat dist and installed-cache changes as generated evidence.

## How To UAT

Follow specs/art-017-state-bookkeeping-checks/.process/uat-runbook.md. The executed run passed 9/9 scenarios: each isolated state invariant exited 1 under --rule status-evidence; clean and legacy-debt controls exited 0; tracked-pair, reviewer-traceability, and Claude/Codex parity checks passed.

## UAT Runbook

Follow specs/art-017-state-bookkeeping-checks/.process/uat-runbook.md. The executed run passed 9/9 scenarios: each isolated state invariant exited 1 under --rule status-evidence; clean and legacy-debt controls exited 0; tracked-pair, reviewer-traceability, and Claude/Codex parity checks passed.

## Verification

- Final repository suite passed 7896/7896 with toolchain preflight green (L1 1469, L4 6235, L5 192).
- Focused bookkeeping-guard suite passed 272/272.
- Codex skill structural validation passed 163/163.
- Release-artifact consistency check passed on the committed final source tree.
- Docs reference generation completed and reference:check reported current.
- Manual UAT passed all 9 acceptance scenarios; both initial UAT-oracle findings were remediated and no product finding remains.

## Scope

- dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md
- dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md
- dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- docs/ai/specs/.process/ART-017-design-concept.md
- docs/ai/specs/.process/ART-017-workflow.md
- docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json
- docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- docs/ai/specs/.process/XPLAT-009-release-readiness-result.json
- docs/ai/specs/.process/autopilot-state.json
- docs/ai/specs/html-artifacts-roadmap-MOC.md
- docs/ai/specs/html-artifacts-technical-roadmap.md
- speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- speckit-pro/skills/speckit-autopilot/SKILL.md
- speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- specs/art-017-state-bookkeeping-checks/.process/implementation-notes.md
- specs/art-017-state-bookkeeping-checks/.process/uat-runbook.md
- specs/art-017-state-bookkeeping-checks/SPEC-MOC.md
- specs/art-017-state-bookkeeping-checks/artifacts/code-approaches.html
- specs/art-017-state-bookkeeping-checks/artifacts/implementation-plan.html
- specs/art-017-state-bookkeeping-checks/artifacts/module-map.html
- specs/art-017-state-bookkeeping-checks/artifacts/spec-explainer.html
- specs/art-017-state-bookkeeping-checks/checklists/error-handling.md
- specs/art-017-state-bookkeeping-checks/checklists/reliability.md
- specs/art-017-state-bookkeeping-checks/checklists/requirements.md
- specs/art-017-state-bookkeeping-checks/checklists/state-management.md
- specs/art-017-state-bookkeeping-checks/contracts/status-evidence-guard.md
- specs/art-017-state-bookkeeping-checks/data-model.md
- specs/art-017-state-bookkeeping-checks/plan.md
- specs/art-017-state-bookkeeping-checks/quickstart.md
- specs/art-017-state-bookkeeping-checks/research.md
- specs/art-017-state-bookkeeping-checks/spec.md
- specs/art-017-state-bookkeeping-checks/tasks.md
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/SKILL.md
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/SKILL.md
- tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py

## Known Gaps

- No known implementation or manual UAT gap remains.
- The authored nonblank diff is 570 gross lines, dominated by exhaustive regression coverage; this is a disclosed size-only reviewability warning.
- The separate Codex same-task scaffold-to-autopilot handoff bug remains outside ART-017 and is tracked in the workflow against branch fix-codex-same-task-autopilot.

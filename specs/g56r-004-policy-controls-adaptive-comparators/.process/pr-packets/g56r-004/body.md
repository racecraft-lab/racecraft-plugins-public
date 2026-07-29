# feat(g56r-004): add policy controls and adaptive comparators

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds a deterministic test harness for comparing inherited, adaptive, and deliberately high-effort routing without changing production routing.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Defines fixed schemas and fixtures for inherited, adaptive, and deliberately high-effort routing.
- Adds deterministic replay, bounded sign-in smoke records, and direction-aware comparison rules.
- Rejects contract drift, missing evidence, reserved-test use, and raw prompt or response captures.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Future routing evaluations can compare the same governed evidence consistently while preserving the previously frozen evaluation contracts.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Start with the two schemas and four fixtures.
- Review the three Codex helper modules and their authority boundaries.
- Review the three registered unit owners and the PR traceability packet.

## How To UAT

No live model smoke was authorized. Review the deterministic replay, authorization-withheld, refusal, bound, and privacy evidence in the focused test owners.

## UAT Runbook

No live model smoke was authorized. Review the deterministic replay, authorization-withheld, refusal, bound, and privacy evidence in the focused test owners.

## Verification

- Authoritative SpecKit Pro suite passed 5194/5194.
- Focused policy, comparison, and twin owners passed 730/730, 172/172, and 50/50.
- Privacy scan passed 10/10 and generated docs references are current.
- Fourteen independent review passes closed 24 Important findings; final review returned NO FINDINGS.

## Scope

- docs-site/src/content/docs/reference/tests.md
- docs/ai/specs/.process/G56R-004-design-concept.md
- docs/ai/specs/.process/G56R-004-workflow.md
- docs/ai/specs/.process/autopilot-state.json
- docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md
- docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md
- specs/g56r-004-policy-controls-adaptive-comparators/.process/pr-review-traceability.md
- specs/g56r-004-policy-controls-adaptive-comparators/SPEC-MOC.md
- specs/g56r-004-policy-controls-adaptive-comparators/checklists/data-integrity.md
- specs/g56r-004-policy-controls-adaptive-comparators/checklists/error-handling.md
- specs/g56r-004-policy-controls-adaptive-comparators/checklists/llm-integration.md
- specs/g56r-004-policy-controls-adaptive-comparators/checklists/performance.md
- specs/g56r-004-policy-controls-adaptive-comparators/contracts/control-comparison.md
- specs/g56r-004-policy-controls-adaptive-comparators/contracts/policy-control-registry.md
- specs/g56r-004-policy-controls-adaptive-comparators/contracts/smoke-replay.md
- specs/g56r-004-policy-controls-adaptive-comparators/data-model.md
- specs/g56r-004-policy-controls-adaptive-comparators/plan.md
- specs/g56r-004-policy-controls-adaptive-comparators/quickstart.md
- specs/g56r-004-policy-controls-adaptive-comparators/research.md
- specs/g56r-004-policy-controls-adaptive-comparators/spec.md
- specs/g56r-004-policy-controls-adaptive-comparators/tasks.md
- specs/g56r-004-policy-controls-adaptive-comparators/verify-tasks-report.md
- tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json
- tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json
- tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json
- tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/partition-registry-entries.json
- tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json
- tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json
- tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py
- tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py
- tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py
- tests/speckit-pro/unit/test-control-comparison-dominance.py
- tests/speckit-pro/unit/test-policy-control-contracts.py
- tests/speckit-pro/unit/test-twin-handoff-completeness.py

## Known Gaps

- Operator-authorized ChatGPT sign-in smokes remain unrun.
- The live-smoke success criteria therefore have deterministic contract evidence but no live observation.

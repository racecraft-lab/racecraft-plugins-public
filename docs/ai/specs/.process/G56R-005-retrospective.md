---
feature: G56R-005
name: Model Availability, Fallback, and Recovery Simulation
branch: g56r-005-model-availability-fallback-recovery
date: 2026-08-22
completion_rate: 100
spec_adherence: 100
counts:
  tasks_total: 25
  tasks_completed: 25
  functional_requirements: 22
  nonfunctional_requirements: 0
  success_criteria: 9
  scored_requirements: 31
  implemented: 31
  partial: 0
  modified: 0
  unspecified: 0
critical_findings: 0
significant_findings: 4
minor_findings: 2
positive_findings: 3
---

# Retrospective: G56R-005

## Executive Summary

G56R-005 completed its implementation contract with 25/25 tasks marked complete and 100% spec adherence across 22 functional requirements and 9 success criteria. The delivered surface is repository-local deterministic simulation evidence only: no production route policy, installer, payload, version, live service, checkpoint, resume, or frozen Claude/G56R-004 behavior was changed.

Two minor process findings remain. First, the Codex task/worktree binding bug required explicit execution-root binding and is already tracked as `TODO-CODEX-WORKTREE-BINDING`. Second, implementation exceeded the planned reviewable line estimate in the primary runtime file, but stayed within the declared one-slice feature boundary with zero production files changed.

Manual UAT found one significant artifact-generation defect: the four HTML
review pages corrected stale static titles by inserting repository-derived text
into a script body. The templates, Claude and Codex author instructions,
generated pages, and regression floor were fixed; the browser and behavioral
UAT suites now pass with zero open findings.

Code review found three additional important contract defects. The local review
expanded the declaration-source vocabulary. The live PR review then bound
`recovery_record` to its dedicated closed schema and made the shared policy
fixture helper supply every required top-level section. All three were
remediated with focused RED/GREEN tests; the final focused suite passes 35/35.

## Proposed Spec Changes

None.

No `spec.md` edits are proposed. The review findings were contract implementation defects, not requirement gaps, and were remediated with RED/GREEN test updates.

## Requirement Coverage Matrix

| ID | Status | Evidence |
|----|--------|----------|
| FR-001 | Implemented | Route-policy schema and corpus accept preferred/fallback routes, local capability evidence, probes, overrides, reroute evidence, helper state, and fake-home inputs. |
| FR-002 | Implemented | `codex_route_fallback.py` separates pure route resolution from fake-home mutation. |
| FR-003 | Implemented | Focused tests prove fixed diagnostic ordering and exactly one terminal outcome. |
| FR-004 | Implemented | Corpus and focused tests cover distinct preferred absence, unsupported effort, discovery unavailable, availability probe, and treatment probe reasons. |
| FR-005 | Implemented | Resolver qualifies only declared model, effort, capability, availability, and treatment evidence that satisfies policy. |
| FR-006 | Implemented | Treatment digest comparison permits only model/effort deltas and rejects non-route mutation. |
| FR-007 | Implemented | Strict override rejection short-circuits before fallback evaluation or writes. |
| FR-008 | Implemented | Service reroute attribution remains separate from plugin-authored diagnostic reasons. |
| FR-009 | Implemented | Score eligibility is split from route qualification and rejects unapproved service reroutes. |
| FR-010 | Implemented | Loop-on-arrival, inherited/generic/unqualified fail-closed cases, and `no_safe_route` exhaustion are covered. |
| FR-011 | Implemented | Optional helper is separately classified, with no-helper continuation allowed only under explicit independent qualification. |
| FR-012 | Implemented | Bounded retry exhaustion is recorded before unbounded retry behavior can occur. |
| FR-013 | Implemented | Time, fan-out, context, cancellation, and escalation budgets are enforced by the harness. |
| FR-014 | Implemented | One non-recursive sequential harness rejects HITL and recursive dispatch paths. |
| FR-015 | Implemented | Staged fake-home adapter confines writes to `<fake_home_root>/.codex/agents` and rejects escape paths. |
| FR-016 | Implemented | Required-core membership derives from the authoritative roster minus the optional helper and fails closed on roster drift. |
| FR-017 | Implemented | Canonical pre-state and previous-known-good manifests drive rollback and write-state evidence. |
| FR-018 | Implemented | Recovery records are canonical and exclude temporary roots, mtimes, inodes, timestamps, and host-specific paths. |
| FR-019 | Implemented | Focused tests forbid importing Claude fallback logic or extracting a shared resolver core. |
| FR-020 | Implemented | PR evidence and checks show no live qualification claims, production wiring, payload, version, release, checkpoint, or resume changes. |
| FR-021 | Implemented | Corpus covers all required scenario rows with independently replayable cases. |
| FR-022 | Implemented | Corpus traceability and PR packet map requirements and success criteria to fixtures, replay output, and fake-home assertions. |
| SC-001 | Implemented | Required scenario coverage rows are represented in the corpus and focused tests. |
| SC-002 | Implemented | Three consecutive canonical replays are byte-identical and exclude host metadata. |
| SC-003 | Implemented | Resolution attempts produce ordered diagnostics, exactly one terminal outcome, and `no_safe_route` for exhaustion. |
| SC-004 | Implemented | Strict override rejection stops before fallback evaluation. |
| SC-005 | Implemented | Service reroute evidence reports attribution separately and marks approved/unapproved status. |
| SC-006 | Implemented | Fake-home failure cases prove atomic no-write, rollback, previous-known-good preservation, rollback failure evidence, and no-helper counter separation. |
| SC-007 | Implemented | Retry, time, fan-out, context, cancellation, and escalation budgets terminate at declared bounds with no recursion or HITL. |
| SC-008 | Implemented | PR packet and corpus traceability cover every FR and SC. |
| SC-009 | Implemented | Final evidence records zero production routing changes, zero live model claims, zero generated payload changes, and zero frozen Claude/G56R-004 edits. |

## Success Criteria Assessment

All 9 measurable outcomes passed. Focused verification passed 35/35 after all review remediation. The static-title contract passed 90/90. Layer 4 passed 6002/6002 with exact-worktree fixture-write permission. The full deterministic suite passed 7663/7663: Layer 1 1469/1469, Layer 4 6002/6002, and Layer 5 192/192.

## Architecture Drift

| Area | Planned | Actual | Drift |
|------|---------|--------|-------|
| Runtime surface | Python 3.11+ stdlib repository-local simulation | Python 3.11+ stdlib under `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` | None |
| Resolver shape | One Codex-local resolver, no Claude import, no shared core | One Codex-local resolver; focused test guards against Claude import and shared core extraction | None |
| State mutation | Fake-home staged adapter only | Fake-home writes confined to harness-created temporary roots under `.codex/agents` | None |
| Production scope | No production resolver, installer, payload, version, release, checkpoint, or resume wiring | No production route or installer files changed; release-artifact check passed | None |
| Reviewability | 385 projected reviewable LOC, 0 production files, 10 total files | Final authored review surface is 584 LOC across 20 implementation/remediation files; 0 production files | Minor |

## Significant Deviations

- REMEDIATED: Manual UAT found stale static document titles plus a dynamic
  `document.title` workaround that violated the gallery's generated-content
  safety contract. Four templates now expose required static title slots, both
  author surfaces forbid the workaround, shipped artifacts were regenerated,
  and browser retesting passed.
- REMEDIATED: The route-resolution report accepted any recovery-record object;
  it now accepts only `null` or the dedicated closed recovery-record schema.
- REMEDIATED: The shared policy fixture helper omitted required helper,
  fake-home, and budget sections; neutral schema-shaped defaults now keep every
  route-resolution fixture aligned with the closed policy contract.

## Minor Findings

- MINOR: Codex task/worktree binding did not adopt the feature worktree inside the same task. The implementation required explicit exact-worktree execution and exact-worktree write permission for tests that create fixtures. This is tracked as `TODO-CODEX-WORKTREE-BINDING` and is outside G56R-005 feature behavior.
- MINOR: Reviewable size exceeded the setup estimate in the primary runtime file. The final implementation still stayed in one coherent simulation slice, did not touch production files, and remained reviewable through the PR packet review order.

## Innovations and Best Practices

- POSITIVE: The post-review schema defect was remediated with a focused RED test (`declaration_source` enum missing) followed by a closed five-value schema contract and GREEN focused/full verification.
- POSITIVE: Recovered HTML review artifacts are present for this spec: `implementation-plan.html`, `spec-explainer.html`, `code-approaches.html`, and `module-map.html`.
- POSITIVE: Manual browser and behavioral UAT produced a committed runbook and
  caught the dynamic-title defect before merge.

Neither positive deviation requires a constitution change. The schema remediation is a normal contract hardening, and the review artifacts restore intended process evidence.

## Constitution Compliance

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Feature behavior stayed repository-only; the separately requested artifact-generation repair changed only gallery templates and Claude/Codex artifact-author instructions, with shipped payloads regenerated. |
| II. Cross-Platform Runtime & Script Safety | PASS | New runtime is Python stdlib, structured JSON, deterministic UTF-8; no new Bash or `jq` dependency. |
| III. Semantic Versioning | PASS | No plugin version or manifest version changed. |
| IV. Test Coverage Before Merge | PASS | Focused tests are registered in `suite-manifest.json`; full deterministic suite passed 7663/7663. |
| V. Conventional Commits | PASS | Branch commits and PR title use conventional lowercase scope form. |
| VI. KISS, Simplicity & YAGNI | PASS | One local resolver, one fake-home adapter boundary, and one sequential harness; no speculative production wiring. |

Constitution violations: None.

## Unspecified Implementations

None for feature behavior.

Process-only additions include recovered HTML review artifacts and autopilot/PR packet evidence. These support the SDD workflow and do not expand G56R-005 runtime behavior.

## Task Execution Analysis

- Total tasks: 25
- Completed tasks: 25
- Completion rate: 100%
- Foundation: T001-T004 complete
- User Story 1: T005-T007 complete
- User Story 2: T008-T011 complete
- User Story 3: T012-T016 complete
- User Story 4: T017-T019 complete
- Polish and verification: T020-T025 complete

The only notable execution deviation was orchestrator-directed implementation in the exact feature worktree after phase agents could not write from the inherited task checkout. This did not change feature scope, but it should be fixed in the autopilot worktree-binding layer.

## Root Cause Analysis

| Finding | Discovery Point | Cause | Prevention |
|---------|-----------------|-------|------------|
| Worktree binding bug | Implement/Post verification | Codex task root, sandbox write scope, phase-agent cwd, and workflow authority did not bind to the same registered feature worktree | Implement `TODO-CODEX-WORKTREE-BINDING` before relying on same-task worktree adoption for future specs |
| `declaration_source` schema mismatch | Independent post-implementation review | Valid schema constrained only `local` while fail-closed tests intentionally used inherited/generic/unqualified sources | Keep contract canaries for every fail-closed vocabulary value, including values intended only for invalid-policy rejection paths |
| Unsafe dynamic document title | Manual browser UAT | Draft templates had no fillable static title slot, so generated pages retained example metadata and used a script workaround | Require and regression-test a static `document-title` fill region; forbid repository-derived title text in script bodies |
| Open recovery-record object | Live PR review | The report schema used a generic object/null union instead of the dedicated closed recovery contract | Bind nested contract properties to their authoritative schema and test the exact reference shape |
| Incomplete shared policy fixture | Live PR review | Resolver tests used a convenience helper that omitted three required policy sections | Give shared fixture helpers neutral schema-shaped defaults and assert them directly |

## Lessons Learned and Recommendations

1. Keep invalid-policy canaries in the schema layer when the runtime intentionally rejects named closed-vocabulary values.
2. Treat exact-worktree binding as part of the execution contract, not just an operator convenience.
3. Continue separating local deterministic evidence from live service claims until G56R-006 owns production wiring.
4. Keep generated review artifacts checked during setup/plan recovery so reviewers can inspect the spec visually before implementation.
5. Treat document metadata as generated content: expose a safe fill region
   instead of repairing it after load with JavaScript.
6. Keep shared test builders schema-shaped even when the runtime path under test
   reads only a subset of the contract.

## File Traceability Appendix

| File | Role |
|------|------|
| `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-policy.schema.json` | Fixture policy contract, including closed declaration-source vocabulary. |
| `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-resolution-report.schema.json` | Route resolution report contract. |
| `tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/recovery-record.schema.json` | Recovery record contract. |
| `tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json` | Scenario corpus, roster identity, and FR/SC traceability. |
| `tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` | Codex-local pure resolver, scoring attribution, fake-home adapter, and bounded harness. |
| `tests/speckit-pro/unit/test-codex-route-fallback-recovery.py` | Focused RED/GREEN and regression coverage for all feature behavior. |
| `tests/speckit-pro/suite-manifest.json` | Layer 4 registration for focused tests. |
| `specs/g56r-005-model-availability-fallback-recovery/.process/pr-packets/g56r-005-draft/body.md` | PR packet summary, review order, verification, scope, UAT, and known gaps. |
| `specs/g56r-005-model-availability-fallback-recovery/artifacts/*.html` | Generated HTML review artifacts for plan, explainer, approach, and module-map review. |
| `docs/ai/specs/.process/G56R-005-manual-uat.md` | Manual browser and deterministic behavioral UAT evidence, finding, remediation, and retest result. |

## Self-Assessment Checklist

- PASS: Evidence completeness - every major deviation includes concrete evidence.
- PASS: Coverage integrity - all FR-001 through FR-022 and SC-001 through SC-009 are represented.
- PASS: Metrics sanity - completion rate is 25/25 = 100%; spec adherence is `(31 + 0.5*0) / 31 = 100%`.
- PASS: Severity consistency - no critical/significant impact remains; process issues are minor and feature behavior is complete.
- PASS: Constitution review - violations are explicitly listed as None.
- PASS: Human Gate readiness - no spec changes are proposed, so no spec-modifying action is requested.
- PASS: Actionability - recommendations are tied to the worktree binding bug and schema canary lesson.

Retrospective saved | Adherence: 100% | Critical findings: 0

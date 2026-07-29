---
feature: "G56R-004 Policy Controls and Adaptive Comparators"
branch: "g56r-004-policy-controls-adaptive-comparators"
date: "2026-07-29"
completion_rate: 100
spec_adherence: 97.5
counts:
  total_tasks: 38
  completed_tasks: 38
  total_requirements: 61
  implemented: 58
  modified: 0
  partial: 3
  not_implemented: 0
  unspecified: 0
  critical_findings: 0
  significant_findings: 0
  minor_findings: 1
  positive_findings: 4
verification:
  final_suite: "5194/5194"
  layer_1: "1428/1428"
  layer_4: "3580/3580"
  layer_5: "186/186"
  review_passes: 14
  important_findings_remediated: 24
  final_review: "NO FINDINGS"
  draft_pr: 403
live_smoke: "operator_only_unrun"
---

# Retrospective: G56R-004 Policy Controls and Adaptive Comparators

## Executive Summary

G56R-004 completed the planned repository-only Codex policy-control harness with
38 of 38 tasks complete, 42 of 42 functional requirements covered, and the final
repository suite passing 5194/5194. Fourteen independent review passes produced
24 Important findings; all were remediated, and the final review returned
`NO FINDINGS`.

Spec adherence is **97.5%**. The only partial coverage is the explicitly
operator-only live ChatGPT sign-in observation for SC-014 through SC-016. No
live or off-box smoke was run, and no live outcome is claimed. Deterministic
replay, unrun/refusal handling, bounded smoke planning, smoke sealing, privacy
checks, and PR traceability are implemented and verified.

Completion metric:

```text
completion_rate = 38 completed tasks / 38 total tasks = 100%
```

Spec adherence metric:

```text
total_requirements = 42 FR + 0 NFR + 19 SC = 61
spec_adherence = (58 implemented + 0 modified + (3 partial * 0.5)) / (61 - 0 unspecified) * 100
spec_adherence = 97.5%
```

## Proposed Spec Changes

None.

No `spec.md` edit is recommended. The operator-only live smoke status is already
specified: unauthorized, refused, incomplete, or unrun live smoke evidence must
remain reported as `unrun` and must not be fabricated or inferred.

Because no spec change is proposed, the retrospective human gate for spec
modification is not triggered.

## Requirement Coverage Matrix

| Requirement IDs | Status | Evidence |
|---|---|---|
| FR-001, FR-002, FR-003, FR-004, FR-005 | Implemented | Policy-control registry schema and fixture enforce exactly three controls, Codex-local IDs, content-address preimages, frozen bindings, and no frozen-artifact edits. Verified by `test-policy-control-contracts.py` and final suite. |
| FR-006, FR-007, FR-040, FR-041 | Implemented | Twin completeness is staged by registry, comparison, partition, and final composition. Final reconciliation reports zero missing, extra, invented, drifted, duplicated, omitted, or unrepresentable members. Verified by `test-twin-handoff-completeness.py`. |
| FR-008, FR-009 | Implemented | Unpinned control binds one inherited parent arm, parent context identity, absent local overrides, and produced-evidence read-back. |
| FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017 | Implemented | Adaptive ladder membership/order, closed signal mapping, precedence, no-wrap escalation/de-escalation, retry/cancellation bounds, budget responses, service reroute, and drift invalidation are covered by replay fixtures and policy-control tests. |
| FR-018, FR-019, FR-020, FR-021, FR-022, FR-023 | Implemented | Justified-high-effort route binding, eligibility rationale, no fallback, exact treatment, and parent-plus-children aggregation are implemented in the registry fixture, replay fixture, and policy helper. |
| FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030 | Implemented | Comparison eligibility, gate-first ordering, eight direction-aware dimensions, margins, confidence, multiplicity, zero denominator, no-verdict behavior, and claim-class mapping are implemented in the comparison schema, fixture, helper, and tests. |
| FR-031, FR-032, FR-033, FR-034 | Implemented | Reserved G56R-011 and G56R-004 smoke partitions are content-addressed and protected from replay/smoke consumption; deterministic replay is byte-stable and non-scored. |
| FR-035, FR-036, FR-037, FR-038, FR-039 | Implemented | Smoke plan/seal behavior, sign-in authorization refusal, mirrored bounds, exact-treatment read-back rules, cache isolation, and raw-capture exclusion are implemented. Live execution remains operator-only and unrun by instruction. |
| FR-042 | Implemented | PR traceability, review order, known gaps, verification evidence, scope/non-goals, rollback notes, and no production-routing change are recorded in the PR review packet and draft PR #403 body. |
| SC-001, SC-002, SC-003 | Implemented | Registry shape, content-address, and frozen-binding checks pass. |
| SC-004 | Implemented | Bidirectional mirror check reports zero drift outside the sanctioned platform divergence. |
| SC-005, SC-006, SC-007 | Implemented | Adaptive ladder, signal mapping, replay movement, no-wrap behavior, non-scorable handling, and bound responses pass. |
| SC-008, SC-009 | Implemented | Justified-high-effort binding and parent-plus-children aggregation pass. |
| SC-010, SC-011 | Implemented | Comparison contract and verdict-to-claim mapping pass. |
| SC-012, SC-013 | Implemented | Reserved partitions and deterministic replay pass. |
| SC-014, SC-015, SC-016 | Partial | Deterministic smoke planning, refusal, bounds, exact-treatment, and cache-isolation validation pass. Operator-authorized live ChatGPT sign-in smoke was not run, so no live observation is claimed. |
| SC-017, SC-018, SC-019 | Implemented | Raw-capture exclusion, zero unrepresentable members, and PR packet traceability pass. |

Coverage inventory checked: FR-001 through FR-042, SC-001 through SC-019, no
NFR IDs.

## Success Criteria Assessment

| ID | Result | Assessment |
|---|---|---|
| SC-001 | Implemented | Exactly three controls and negative cases are machine-checked. |
| SC-002 | Implemented | Control, registry, and comparison content addresses are recomputed over the declared preimages. |
| SC-003 | Implemented | Frozen G56R-003/CAR-003 binding drift fails closed without editing frozen artifacts. |
| SC-004 | Implemented | CAR-004 mirror derivation is checked bidirectionally with only the sanctioned control-kind divergence. |
| SC-005 | Implemented | Adaptive ladder membership and ordering derive from admitted frozen tuples. |
| SC-006 | Implemented | Adaptive observable values map to exactly one response under declared precedence. |
| SC-007 | Implemented | Replay covers escalation, no-wrap behavior, de-escalation boundary, non-scorable exclusion, and bound responses. |
| SC-008 | Implemented | Justified-high-effort binds exactly one qualified route and rejects fallback or predicate failure. |
| SC-009 | Implemented | Parent-plus-children aggregation covers all required dimensions and raw/cache members. |
| SC-010 | Implemented | Comparison declares dimensions, directions, margins, confidence, multiplicity, zero denominator, no weights, and no-verdict mapping. |
| SC-011 | Implemented | Every reachable comparison outcome maps to exactly one permitted release claim class. |
| SC-012 | Implemented | Reserved G56R-011 and G56R-004 smoke partitions are disjoint and protected. |
| SC-013 | Implemented | Every control fixture replays byte-identically and produces zero outcome-bearing scored rows. |
| SC-014 | Partial | Smoke bounds and refusal/seal checks pass, but no authorized live ChatGPT sign-in smoke was run. |
| SC-015 | Partial | Exact-treatment read-back rules are implemented and negative-tested, but no live produced evidence exists. |
| SC-016 | Partial | Cache-isolation rules and invalidation cases are implemented, but no live cache roots were observed. |
| SC-017 | Implemented | Repository privacy scan and raw-capture exclusion tests pass. |
| SC-018 | Implemented | Final reconciliation found zero unmirrorable CAR-004 members. |
| SC-019 | Implemented | PR packet maps major FR/SC coverage to changed files and records verification, gaps, and no production-routing change. |

## Architecture Drift

| Planned decision | Delivered outcome | Drift |
|---|---|---|
| Add two Codex-local schemas and preserve the CAR-004 mirror shape. | Added `policy-control-registry.schema.json` and `control-comparison.schema.json`. | None. |
| Add deterministic Codex control fixtures under a durable fixture directory. | Added four fixtures under `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/`. | None. |
| Add the smallest Codex-local validator/comparison/smoke helpers. | Added `codex_policy_controls.py`, `codex_control_comparison.py`, and `codex_control_smoke.py`. | None. |
| Use frozen G56R-003/CAR-003/CAR-004 artifacts read-only. | Final safety evidence reports zero frozen-artifact changes. | None. |
| Keep existing suite ownership authoritative. | `tests/speckit-pro/suite-manifest.json` stayed unchanged because the three existing owners remained registered. | None. |
| Keep production routing, installer, manifest, scheduler, defaults, and release integration out of scope. | No production/runtime integration file was changed. | None. |
| Keep live smoke operator-only. | No live smoke was run; deterministic unrun/refusal evidence is implemented. | Expected evidence limitation, not scope drift. |
| Generate PR packet and docs reference evidence when required. | PR packet/body/validation and generated docs reference output were produced and validated. | None. |

## Significant Deviations

No CRITICAL or SIGNIFICANT implementation drift was found.

| Severity | Finding | Impact | Disposition |
|---|---|---|---|
| MINOR | SC-014 through SC-016 have no live ChatGPT sign-in observation. | Full live smoke observation is unavailable. Deterministic planning, refusal, seal, bound, exact-treatment, and cache-isolation evidence exists. | Accepted as an explicit operator-only non-run. No spec change and no live/off-box smoke. |

## Innovations and Best Practices

| Classification | Observation | Reuse potential |
|---|---|---|
| POSITIVE | The mirror proof is dependency-ordered: registry-owned, comparison-owned, partition-owned, then final composed bidirectional proof. | Reuse for future specs where one handoff surface is not available at the first RED test. |
| POSITIVE | Live smoke was modeled as governed `unrun`/refusal/seal evidence instead of being silently waived or fabricated. | Reuse for operator-only evidence paths in repository-only specs. |
| POSITIVE | Review remediation converted 24 Important findings into strict test evidence and finished with `NO FINDINGS`. | Reuse the review loop as a correctness and privacy hardening pattern. |
| POSITIVE | The PR review packet gives reviewers a single traceability map from FR/SC groups to changed files and verification owners. | Reuse for one-PR specs with many contract-level requirements. |

## Root Cause Analysis

| Item | Discovery point | Cause | Prevention recommendation |
|---|---|---|---|
| SC-014-SC-016 live observation unrun | Planning, implementation, and Post evidence | Live ChatGPT sign-in smoke requires explicit operator authorization, and no authorization was supplied. | Keep the unrun status explicit in every evidence surface and do not convert deterministic smoke validation into a live claim. |
| Analyze A-002 dependency ordering | Analyze plus early implementation | The first task wording tried to prove comparison-owned and partition-owned mirror members before those fixtures existed. | Stage mirror proofs by artifact availability and keep a final composed proof after all fixtures exist. |
| Review remediation volume | Post code review | Contract/privacy details around exact evidence, raw capture, and mirror completeness benefited from independent review pressure. | Preserve strict RED/GREEN remediation and final independent `NO FINDINGS` review before PR handoff. |

## Constitution Compliance

| Principle | Result | Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | Changes are repository-only under `tests/speckit-pro/`, feature docs, generated docs reference, and process artifacts. No install-facing plugin structure changed. |
| II. Cross-Platform Runtime & Script Safety | PASS | New helpers are Python 3.11 standard-library code using structured JSON and path-safe repository validation. No active Bash or `jq` dependency was added. |
| III. Semantic Versioning | PASS | No plugin manifest, marketplace version, or release version was changed. |
| IV. Test Coverage Before Merge | PASS | The three existing Layer 4 owners pass after remediation; final default suite passes 5194/5194. |
| V. Conventional Commits | PASS | The PR title `feat(g56r-004): add policy controls and adaptive comparators` passed packet validation and release-readiness title validation. |
| VI. KISS, Simplicity & YAGNI | PASS | The implementation stayed at the planned 12 implementation paths, one vertical slice, three helper modules, and no speculative runtime integration. |

Constitution violations: None.

## Unspecified Implementations

None that affect product or plugin runtime behavior.

Supporting artifacts outside the 12 implementation paths were process or
generated evidence: the feature workflow, design concept, PR packet/body,
PR traceability report, verify-tasks report, generated docs reference page, and
roadmap/MOC updates. These support reviewability and publication rather than
adding unplanned runtime behavior.

## Task Execution Analysis

| Area | Result |
|---|---|
| Task completion | 38/38 complete. |
| Verify-tasks | 38/38 verified, 0 partial, 0 weak, 0 not found, 0 skipped. |
| RED/GREEN pairs | 15 pairs completed. |
| Final narrow owners | `test-policy-control-contracts.py` 730/730, `test-control-comparison-dominance.py` 172/172, `test-twin-handoff-completeness.py` 50/50. |
| Final replay evidence | 18/18 deterministic replay cases passed. |
| Privacy evidence | 10/10 privacy assertions passed. |
| Final suite | `python3 -u tests/speckit-pro/run-all.py` passed 5194/5194: Layer 1 1428/1428, Layer 4 3580/3580, Layer 5 186/186. |
| Reviews | 14 independent passes; 24 Important findings remediated; final pass `NO FINDINGS`. |
| Draft PR | PR #403 created as a draft with validated title and body. |

The earlier verify-tasks report captured a pre-remediation suite count of
5142/5142. The final Post evidence supersedes that with 5194/5194 after review
remediation and generated reference updates.

## Skipped Prerequisites and Explicit Non-Runs

| Item | Status | Effect |
|---|---|---|
| Live ChatGPT sign-in smoke | Skipped by instruction, operator-only, unrun | SC-014 through SC-016 remain partial for live observation. No live/off-box smoke was run. |
| UAT skeleton/runbook generation | Skipped earlier in Post workflow | No committed feature-local UAT runbook exists; this is not a retrospective blocker. |
| `.specify/feature.json` metadata refresh | Initial prerequisite helper lacked active feature metadata; rerun used `SPECIFY_FEATURE_DIRECTORY` for G56R-004. Sandbox denied the helper's metadata write, but `FEATURE_DIR` and docs resolved successfully. | Retrospective used the resolved feature directory and did not edit workflow or autopilot state. |

## Lessons Learned and Recommendations

1. Keep evidence order aligned with artifact availability. The final mirror proof
   should compose registry, comparison, and partition evidence after those
   artifacts exist.
2. Treat operator-only live evidence as a first-class state. `unrun` and refused
   smoke records are safer than either blocking deterministic validation or
   inventing a live result.
3. Keep raw capture and produced-evidence boundaries under dedicated tests. They
   found and closed correctness/privacy gaps that broad suite counts alone would
   not explain.
4. Keep PR traceability grouped by requirement family and verification owner. It
   made a large contract surface reviewable as one navigable PR.

## File Traceability Appendix

| File | Role | Requirement evidence |
|---|---|---|
| `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json` | Codex policy-control schema | FR-001 through FR-007, FR-040, SC-001 through SC-004 |
| `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json` | Codex comparison schema | FR-024 through FR-030, FR-040, SC-010, SC-011 |
| `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json` | Control registry fixture | FR-001 through FR-023, FR-040, SC-001 through SC-009 |
| `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json` | Comparison fixture | FR-024 through FR-030, SC-010, SC-011 |
| `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/partition-registry-entries.json` | Reserved partition fixture | FR-031 through FR-033, SC-012 |
| `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json` | Deterministic replay and smoke-plan cases | FR-012 through FR-039, SC-006 through SC-017 |
| `tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py` | Policy-control validation, replay, aggregation, and twin derivation | FR-001 through FR-023, FR-031 through FR-041, SC-001 through SC-009, SC-012 through SC-018 |
| `tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py` | Comparison and claim-class behavior | FR-024 through FR-030, SC-010, SC-011 |
| `tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py` | Non-live smoke planning, refusal, sealing, bounds, privacy, and cache-isolation validation | FR-031 through FR-039, SC-014 through SC-017 |
| `tests/speckit-pro/unit/test-policy-control-contracts.py` | Main policy-control, replay, partition, smoke, and privacy owner | FR-001 through FR-039, SC-001 through SC-017 |
| `tests/speckit-pro/unit/test-control-comparison-dominance.py` | Comparison dominance and claim owner | FR-024 through FR-030, SC-010, SC-011 |
| `tests/speckit-pro/unit/test-twin-handoff-completeness.py` | Twin completeness owner | FR-006, FR-007, FR-040, FR-041, SC-004, SC-018 |
| `specs/g56r-004-policy-controls-adaptive-comparators/.process/pr-review-traceability.md` | PR traceability and evidence packet source | FR-042, SC-019 |
| `specs/g56r-004-policy-controls-adaptive-comparators/.process/pr-packets/g56r-004/body.md` | Draft PR body source | FR-042, SC-019 |
| `specs/g56r-004-policy-controls-adaptive-comparators/verify-tasks-report.md` | Phantom-completion verification | All 38 tasks |
| `docs-site/src/content/docs/reference/tests.md` | Generated docs reference output | T036, FR-042, SC-019 |

## Self-Assessment Checklist

| Check | Result | Evidence |
|---|---|---|
| Evidence completeness | PASS | Every major deviation and non-run names concrete files, tasks, or behavior. |
| Coverage integrity | PASS | FR-001 through FR-042 and SC-001 through SC-019 are accounted for. |
| Metrics sanity | PASS | `completion_rate` and `spec_adherence` formulas are shown and reconcile to frontmatter. |
| Severity consistency | PASS | The only non-complete item is classified as MINOR evidence limitation, not CRITICAL/SIGNIFICANT drift. |
| Constitution review | PASS | All six principles are checked and no violations are listed. |
| Human Gate readiness | PASS | No spec changes are proposed, so no spec-modifying action is requested. |
| Actionability | PASS | Recommendations are specific and tied to evidence ordering, operator-only smoke handling, privacy testing, and PR traceability. |

Blocking-rule checks passed. The retrospective is finalized report-only and does
not require spec, workflow, implementation, PR packet/body, or autopilot-state
edits.

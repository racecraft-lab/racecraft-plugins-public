---
feature: G56R-001
title: Candidate Route Baseline and Role Contracts
branch: g56r-001-candidate-route-baseline
date: 2026-07-14
completion_rate: 100
spec_adherence: 100
requirements:
  total: 37
  implemented: 35
  modified: 2
  partial: 0
  not_implemented: 0
  unspecified: 0
findings:
  critical: 0
  significant: 1
  minor: 1
  positive: 3
  unresolved: 0
terminal_handoff: go
---

# G56R-001 Retrospective

## Executive Summary

G56R-001 completed all 26 tasks and all 37 explicitly numbered requirements
(27 FR, 0 NFR, and 10 SC). The final artifacts reproduce a `go` handoff with
exactly 12 agents, 10 present routes, 2 explicit route absences, 3 current
fixtures, and 9 missing fixtures. The focused checker passes, the independent
task audit records 26 VERIFIED items, and the final default suite passes
2803/2803.

Spec adherence is 100%. Two numbered requirements, FR-026 and SC-010, were
modified during review to include the exact repository guard allowance and
then fully implemented. One significant validation gap and one minor scope
declaration gap were found after the first implementation commit; both were
resolved in `7eab3c69` before closeout. There are no residual deviations,
constitution violations, or unowned findings.

The reviewability gate remains WARN with `pass: true`: the six-path
implementation is 13,432 added lines, but it preserves 0 production LOC and 0
production files and is atomic because the narrative, manifest, checker, and
tests mutually validate one another.

## Metrics

- Task completion: `26 / 26 = 100%`.
- Requirement population: `27 FR + 0 NFR + 10 SC = 37`.
- Requirement disposition: 35 implemented, 2 modified-and-implemented, 0
  partial, 0 not implemented, and 0 unspecified.
- Spec adherence:
  `((35 implemented + 2 modified + (0 partial * 0.5)) / (37 - 0 unspecified)) * 100 = 100%`.
- Terminal implementation interval: `2026-07-14T12:45:56-05:00` through
  `2026-07-14T14:55:31-05:00`, within the predeclared deadline of
  `2026-07-14T20:45:56-05:00`.
- Final verification: checker PASS, focused artifacts 48/48, runner guard
  11/11, integration 257/257, Layer 1 1427/1427, Layer 4 1190/1190, Layer 5
  186/186, and default total 2803/2803.

## Proposed Spec Changes

None. The final `spec.md` already incorporates the post-review human-narrative
binding and exact repository-guard boundary, so no further FR, NFR, or SC edit
is warranted. The retrospective default-NO human gate therefore remains
closed: this report does not modify `spec.md` and does not invoke a spec
handoff.

## Requirement Coverage Matrix

Legend: **Implemented** means the final implementation matches the requirement;
**Modified** means the requirement was refined during review and the final
implementation matches the refined text.

| Requirement | Status | Implementation and verification evidence |
|---|---|---|
| FR-001 | Implemented | The dated Markdown narrative and versioned JSON manifest exist; T020-T022; checker PASS. |
| FR-002 | Implemented | The manifest and normalized projection contain the exact 12-agent set; T004/T020; focused 48/48. |
| FR-003 | Implemented | Ten agents have bound present routes and the two parity roles have cited absences; T014/T015/T020. |
| FR-004 | Implemented | The narrative and per-agent records contain stable, reciprocal route-policy inventory entries with mismatch ownership; T011. |
| FR-005 | Implemented | Tracked, cached, and installed observations are distinct and tracked source remains authoritative; T012. |
| FR-006 | Implemented | All 12 semantic contracts encode every hard boundary plus permitted, prohibited, and stop/escalation behavior; T014/T015. |
| FR-007 | Implemented | Both parity roles contain field-level Claude-source mappings and explicit absent Codex routes; T015. |
| FR-008 | Implemented | Readable contract IDs and repeatable instruction/contract hashes are checked; T005/T006/T016. |
| FR-009 | Implemented | The manifest root is agent-centric and each record keeps contract, route, candidate, provenance, and invalidation data together; T020/T021. |
| FR-010 | Implemented | Every candidate is bound to its enclosing contract and includes the required tuple, capabilities, evidence, qualification, and invalidation fields; T005/T006/T017/T021. |
| FR-011 | Implemented | The catalog contains 21 evidence-supported project candidates, including immutable baselines and unchanged controls; T017. |
| FR-012 | Implemented | Exclusion and hard-incompatibility evidence is required and local unavailability cannot exclude a candidate; T017 plus focused negative tests. |
| FR-013 | Implemented | Project eligibility is separate from installation availability, which remains `unresolved_g56r_002`; T017/T021. |
| FR-014 | Implemented | Treatments retain unchanged controls and require evidence-backed bounded hypotheses; T017. |
| FR-015 | Implemented | Preference and fallback signals remain unqualified hypotheses with no final order; T017. |
| FR-016 | Implemented | Official evidence covers identifiers, custom agents, reasoning, discovery, telemetry, reroutes, and non-interactive output; T010. |
| FR-017 | Implemented | Platform and project provenance includes locator, date/revision, surface, scope, applicability, conflict, role, and invalidation fields; T009/T010. |
| FR-018 | Implemented | Facts, inferences, policy, assumptions, conflicts, and environment observations remain visibly classified; T009/T013. |
| FR-019 | Implemented | Conflicts follow frozen authority and have blocking or owned nonblocking dispositions; T013. |
| FR-020 | Implemented | CLI, desktop app, app server, and non-interactive records are independent and require surface-and-feature-matched official evidence; T009/T010 plus review hardening. |
| FR-021 | Implemented | Publication rejects absolute/home paths, identities, hostnames, credentials, secrets, and unrelated configuration; T009/T012 plus sanitization negative tests. |
| FR-022 | Implemented | All 12 fixture contracts exist with the exact 3-current/9-missing split and `non_release_evidence` labeling; T018. |
| FR-023 | Implemented | Telemetry, owned unknowns, immutable admission binding, content hash, and G56R-002 snapshot ownership are published; T019/T021/T025. |
| FR-024 | Implemented | Eleven objective completion checks pass and reproduce `go` without changing eligibility or qualification state; T007/T008/T023/T025/T026. |
| FR-025 | Implemented | Start, stop, and deadline are RFC 3339 ordered timestamps, and the terminal packet was emitted before deadline; T001/T025. |
| FR-026 | Modified | Final scope adds the exact two-file runner-guard allowance to the Python checker, focused Layer 4 test, and suite declaration; T002-T008/T023/T024; focused 48/48, guard 11/11, default 2803/2803. |
| FR-027 | Implemented | The six implementation paths contain no runtime probe, score, qualification, route mutation, source-defect repair, or production change; T009/T017/T023. |

### Non-Functional Requirements

The specification defines no `NFR-XXX` IDs. Its cross-cutting qualities are
expressed as FR-026/FR-027, architecture constraints, the one-day boundary,
and constitution gates; all are covered above and below. No NFR is missing
from the adherence denominator.

## Success Criteria Assessment

| Success criterion | Status | Evidence |
|---|---|---|
| SC-001 | Implemented | One dated narrative and one versioned manifest exist; the handoff is `go`. |
| SC-002 | Implemented | Checker PASS reports 12 agents, 10 present, and 2 absent. |
| SC-003 | Implemented | All 12 contracts have unique IDs and repeatable canonical hashes; focused tests pass. |
| SC-004 | Implemented | All 21 candidates contain required fields and none is excluded for local unavailability. |
| SC-005 | Implemented | Official and project provenance is complete, current to the research date/revision, and conflict-labeled. |
| SC-006 | Implemented | Four surfaces and three source-observation classes remain distinct; sanitization tests pass. |
| SC-007 | Implemented | Fixture inventory and contracts reproduce the exact 3/9 split and non-release label. |
| SC-008 | Implemented | Structured checker and 48 focused tests prove parsing, identity, hashing, canonicalization, and cross-artifact agreement. |
| SC-009 | Implemented | Two identical checker runs and the admission binding reproduce the same `go` and downstream owners. |
| SC-010 | Modified | Final scope is exactly 3 delivery plus 3 validation paths, including the exact guard allowance; production impact remains zero and reviewability is WARN/pass. |

## Architecture Drift

| Planned boundary | Actual result | Drift disposition |
|---|---|---|
| Markdown narrative plus separate agent-centric JSON manifest | Delivered at the two fixed `docs/ai/research/` paths | None |
| One feature-local, offline, read-only Python 3.11+ standard-library checker | Delivered under the feature directory; live checker PASS | None |
| Exact 12/10/2 agents/routes and 3/9 fixtures | Checker and manifest reproduce those sets | None |
| Official-only platform evidence, repository project evidence, and independent client surfaces | Final provenance and surface checks enforce the frozen authority model | None |
| No probing, scoring, qualification, final ordering, defect repair, or production mutation | Six changed implementation paths are research/validation only; 0 production LOC/files | None |
| Three delivery plus three validation paths | Final implementation has exactly those six paths | None against the final plan; initial five-path declaration was corrected during review |
| One 8-hour workday | Terminal packet emitted after about 2 hours 10 minutes | None |
| One navigable review slice | 13,432 added implementation lines triggered WARN/pass, but splitting would separate mutually validating artifacts | MINOR reviewability pressure, accepted without exception |

## Significant Deviations and Root Causes

| ID | Severity | State | Deviation and evidence | Root cause and prevention |
|---|---|---|---|---|
| D-01 | SIGNIFICANT | Resolved | Independent review found that the first checker could accept dangling candidate evidence, cross-surface evidence, narrower sanitization, and stale prose outside the normalized projection. Commit `7eab3c69` added referential integrity, surface/feature matching, expanded sanitization, and a deterministic human-prose hash with negative tests. | The initial RED matrix emphasized schema shape and projection equality but did not enumerate adversarial reference and prose-drift cases. Add those cases to the first checker-test inventory, before artifact population. |
| D-02 | MINOR | Resolved | The first declared implementation boundary omitted the existing post-commit public-claim guard. Commit `7eab3c69` added four exact allowlist lines in `test-speckit-pro-runner.py` and reconciled FR-026, SC-010, plan, tasks, quickstart, data model, and contract docs from two to three validation paths. | Planning validated the new checker and suite membership before testing the committed research paths against the existing guard. Run the exact post-commit guard before freezing declared file operations. |

No requirement was dropped, relaxed, left partial, or implemented outside the
final accepted boundaries. Both deviations were corrected and reverified
before the terminal evidence commit `60dfff18`.

## Innovations and Best Practices

| ID | Severity | Improvement | Reuse and constitution disposition |
|---|---|---|---|
| P-01 | POSITIVE | The human narrative has a non-circular deterministic hash that excludes the normalized projection and substitutes its own marker, so prose drift cannot hide behind machine projection agreement. | Reuse for future dual human/machine research packets. Keep it feature-local unless a second concrete use appears; not yet a constitution candidate. |
| P-02 | POSITIVE | Candidate rationale, eligibility, and incompatibility evidence must resolve inside that candidate's provenance, while surface claims require official evidence matching both surface and feature. | Reuse as an evidence-integrity checklist pattern in G56R-002/G56R-003. Prefer checklist guidance over a generic validation framework. |
| P-03 | POSITIVE | The existing public-claim guard was broadened by exactly two file paths, not by a directory prefix, and received a direct 11/11 proof. | Reuse exact allowlisting for future research-only artifacts. This already follows KISS/YAGNI and does not require a constitution amendment. |

## Constitution Compliance

| Article | Result | Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | No shipped plugin file changed; repository tests remain under `tests/speckit-pro/`; Layer 1 passes 1427/1427. |
| II. Cross-Platform Runtime & Script Safety | PASS | The checker uses Python 3.11+ standard-library structured JSON, deterministic UTF-8, and platform-safe paths; no Bash, `jq`, package, or shell subprocess was added; Layer 4 passes 1190/1190. |
| III. Semantic Versioning | PASS / N/A | No plugin manifest, marketplace version, or release metadata changed. Manifest version 1 is a research-data contract, not a plugin version. |
| IV. Test Coverage Before Merge | PASS | The checker has 48 focused Layer 4 tests, declared suite membership, an 11/11 exact guard test, and a 2803/2803 default-suite result. |
| V. Conventional Commits | PASS | All branch commits use `type(scope): description`; no PR was created, so the eventual PR-title gate remains outside this report-only closeout. |
| VI. KISS, Simplicity & YAGNI | PASS | One fixed-path checker and explicit agent-centric data were used; no package, reusable validator framework, route abstraction, or speculative runtime feature was added. |

Constitution violations: **None**. Complexity exceptions: **None**.

## Unspecified Implementations

None in the delivery. The final human-prose hash and exact runner-guard
allowance were incorporated into the normative specification and planning
artifacts before closeout, so they are classified as modified requirements,
not unspecified features. `verify-tasks-report.md` and this retrospective are
post-implementation workflow evidence rather than product scope.

## Task Execution Analysis

| Phase | Tasks | Result | Notes |
|---|---:|---|---|
| Start clock and checker TDD | T001-T008 | 8/8 complete | Three RED/GREEN increments established the executable artifact contract before conclusions. |
| Collect and reconcile evidence | T009-T013 | 5/5 complete | Authority, inventory, source classes, conflicts, and surface isolation were frozen. |
| Contracts, candidates, fixtures, unknowns | T014-T019 | 6/6 complete | Twelve contracts, 21 candidates, 12 fixture contracts, telemetry, and owned unknowns were recorded. |
| Agent-centric manifest | T020-T022 | 3/3 complete | Narrative and JSON normalized projection agree. |
| Validate and hand off | T023-T026 | 4/4 complete | Checker, focused, guard, integration, and default suites pass; handoff is `go`. |

- Added tasks: 0.
- Dropped tasks: 0.
- Modified tasks: T024 and T026 were reconciled to include the exact guard test
  and final six-path boundary; their intended validation and terminal-gate
  purpose did not change.
- Independent phantom audit: 26 VERIFIED, 0 PARTIAL, 0 WEAK, 0 NOT_FOUND, and
  0 SKIPPED.
- Blockers: no terminal blocker. Analyze found four pre-implementation issues
  (one CRITICAL and three HIGH) and resolved them before implementation;
  independent review later found D-01/D-02 and resolved both before closeout.
- Post boundaries: UAT and PR creation were explicitly skipped because no
  source-derived UAT runbook or validated PR packet exists. These are workflow
  boundaries, not missing G56R-001 implementation tasks or requirements.

## Lessons Learned and Recommendations

1. **HIGH — Exercise committed-path guards early.** Run the exact runner guard
   after the first research-path commit or in a temporary index-equivalent
   state, before freezing the declared file-operation count.
2. **HIGH — Start evidence validators with adversarial references.** Include
   dangling evidence IDs, wrong-surface evidence, prose-only contradiction,
   broad absolute paths, local identities, and credential-shaped values in the
   initial RED suite.
3. **MEDIUM — Budget artifact volume separately from production LOC.** A
   0-production-LOC spike can still create a 13,432-line review surface. Future
   spikes should record both production LOC and expected research/fixture data
   volume while preserving the one-navigable-PR atomicity test.
4. **MEDIUM — Preserve local evidence ownership.** G56R-002 and G56R-003 should
   reuse candidate-local provenance resolution and surface/feature matching so
   qualification cannot inherit evidence from another candidate or client.
5. **LOW — Keep narrow exceptions exact.** Continue preferring file-level
   guard allowances and focused direct tests over directory prefixes or a
   reusable exception framework.

No recommendation requires changing this completed spec. If a future request
seeks to amend `spec.md`, it must pass a new explicit human confirmation gate.

## File Traceability Appendix

### Implementation boundary

| Path | Role | Primary traceability |
|---|---|---|
| `docs/ai/research/codex-agent-route-candidates.md` | Human evidence record, contracts, candidate catalog, fixtures, unknowns, handoff | FR-001-FR-025, FR-027; SC-001-SC-009 |
| `docs/ai/research/codex-agent-route-candidate-manifest.json` | Versioned agent-centric machine projection and admission binding | FR-001-FR-025; SC-001-SC-009 |
| `specs/g56r-001-candidate-route-baseline/check-artifacts.py` | Fixed-path offline completeness and agreement checker | FR-002-FR-026; SC-002-SC-009 |
| `tests/speckit-pro/unit/test-g56r-001-artifacts.py` | 48 focused positive and negative artifact-contract tests | FR-002-FR-027; SC-002-SC-010 |
| `tests/speckit-pro/suite-manifest.json` | Single Layer 4 membership declaration | FR-026; SC-010 |
| `tests/speckit-pro/unit/test-speckit-pro-runner.py` | Exact two-research-file public-claim guard allowance | FR-026; SC-010 |

### Planning, contract, and workflow evidence

- Feature contract and design: `SPEC-MOC.md`, `spec.md`, `plan.md`,
  `research.md`, `data-model.md`, `quickstart.md`,
  `contracts/agent-route-candidate-manifest.md`, and `tasks.md`.
- Domain audits: `checklists/requirements.md`, `checklists/integration.md`,
  `checklists/llm-integration.md`, `checklists/reliability.md`, and
  `checklists/security.md`.
- Process and roadmap traceability:
  `docs/ai/specs/.process/G56R-001-design-concept.md`,
  `docs/ai/specs/.process/G56R-001-workflow.md`,
  `docs/ai/specs/.process/autopilot-state.json`,
  `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md`, and
  `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`.
- Independent post-implementation evidence:
  `specs/g56r-001-candidate-route-baseline/verify-tasks-report.md`.
- Implementation history: `15399458` published the baseline; `7eab3c69`
  resolved independent-review findings; `003d0ea1` refreshed verification
  evidence; `60dfff18` recorded the stable final suite totals.

## Required Self-Assessment

| Check | Result | Basis |
|---|---|---|
| Evidence completeness | PASS | D-01 and D-02 cite commits, paths, behaviors, and verification; positive findings cite their implementations. |
| Coverage integrity | PASS | Every FR-001-FR-027 and SC-001-SC-010 appears exactly once; the absence of NFR IDs is explicit. |
| Metrics sanity | PASS | Completion is 26/26; adherence uses 35 implemented + 2 modified over 37 non-unspecified requirements. |
| Severity consistency | PASS | No residual or constitutional issue is labeled below its impact; the significant and minor deviations are explicitly resolved. |
| Constitution review | PASS | All six articles are assessed and violations are explicitly stated as None. |
| Human Gate readiness | PASS | Proposed Spec Changes explicitly states None; default-NO is recorded and no spec mutation or handoff occurred. |
| Actionability | PASS | Five prioritized recommendations map directly to D-01, D-02, reviewability evidence, and reusable positive practices. |

**Overall self-assessment: PASS.** All blocking checklist items pass.

---
feature: G56R-006
branch: g56r-006-resolver-materializer-installer-strict-override
date: 2026-08-25
completion_rate: 100
spec_adherence: 100
requirements_total: 38
requirements_implemented: 38
requirements_partial: 0
requirements_modified: 0
requirements_unspecified: 0
tasks_total: 53
tasks_completed: 53
critical_findings: 0
significant_findings: 1
minor_findings: 1
positive_findings: 5
---

# Retrospective: Capability-aware Resolver, Materializer, Installer, and Strict Override

## Executive Summary

G56R-006 was completed with 53/53 tasks marked complete and acceptance evidence covering 29 functional requirements, 9 success criteria, 4 user stories, and 13 acceptance scenarios. The implementation adhered to the spec: route-aware mode remains gated by an explicit trusted manifest, static no-manifest mode remains compatible, and all G56R-006 acceptance evidence is deterministic fake-home evidence with no live model calls or real-user-home mutation.

The main deviation was process/reviewability, not product behavior: the implementation exceeded the planned 385 reviewable LOC because rollback-safe installer behavior required a larger atomic adversarial test and remediation set. That deviation has an explicit typed exception in release readiness evidence and was independently reviewed at exact head with 0 Important findings and 0 nits.

Spec Adherence = ((38 implemented + 0 modified + (0 partial * 0.5)) / (38 total - 0 unspecified)) * 100 = 100%.

## Proposed Spec Changes

None. No `spec.md` edits are recommended from this retrospective, so the human gate for spec modification is not triggered.

Future downstream specs should preserve the existing G56R-006 scope boundaries:

| Area | Recommendation | Rationale |
|------|----------------|-----------|
| G56R-007 through G56R-011 | Keep roster reconciliation downstream. | FR-029 intentionally names reconciliation inputs without assigning cohorts. |
| Route qualification | Keep production route qualification outside G56R-006. | G56R-006 proves framework compatibility only. |
| Reviewability planning | Add an explicit atomic rollback/security evidence multiplier for installer work. | The 385 LOC estimate missed cross-platform rollback and concurrent-edit proof complexity. |

## Requirement Coverage Matrix

| Requirement | Status | Evidence |
|-------------|--------|----------|
| FR-001 | Implemented | `helpers/install.py` validates explicit trusted manifest path, schema, identities, source-roster digest, 12 required policies, helper state, candidates, and probes; T006-T008/T014-T015. |
| FR-002 | Implemented | Static no-manifest mode preserves the 13-file copy/verify path and omits `routing`; materializer review remediation preserved legacy static bytes; T005/T014-T015/T018. |
| FR-003 | Implemented | Strict 13-TOML source inventory validation is implemented and tested; T005/T007-T008. |
| FR-004 | Implemented | Required roster constants cover the 12 specified agents and route-aware records preserve canonical order; T006-T008/T031-T032. |
| FR-005 | Implemented | `autopilot-fast-helper` is the sole optional helper in planning; T006-T008/T024-T025. |
| FR-006 | Implemented | Optionality affects destination planning only; source inventory still requires the helper TOML; T007-T008/T024-T025. |
| FR-007 | Implemented | One runtime snapshot is captured and bound across required/helper records, with probe child evidence; T009-T010/T014-T015/T033-T034. |
| FR-008 | Implemented | Runtime capability observation enters through an injectable runner-owned adapter; T009-T010/T033-T034. |
| FR-009 | Implemented | Native-discovery fallback probes are manifest-admitted child evidence and do not widen candidates; T033-T034. |
| FR-010 | Implemented | Preferred/fallback resolution evaluates all required agents in canonical order and continues diagnostics after misses; T014-T015/T031-T032. |
| FR-011 | Implemented | Resolution requires model, explicit effort, capability, availability, and exact materialization; T012-T015. |
| FR-012 | Implemented | Route-aware mode never infers model or effort; explicit-route materialization still requires non-empty effort; T012-T013/T019-T020. |
| FR-013 | Implemented | Materialization proof binds original source bytes to rendered destination bytes; T012-T013. |
| FR-014 | Implemented | Non-route fields are verified unchanged; T012-T013. |
| FR-015 | Implemented | Route-aware responses contain the closed top-level `routing` object and all required sub-evidence; T014-T038. |
| FR-016 | Implemented | Low-level mutation records remain mechanical, with routing evidence in `routing`; T014-T015/T035-T036. |
| FR-017 | Implemented | Complete required batch resolution/materialization/verification precedes planned writes and apply mutations; T016-T017/T035-T036. |
| FR-018 | Implemented | Required misses report zero planned/applied writes/removals, `writes_state=false`, and no restart; T019-T020/T031-T032. |
| FR-019 | Implemented | Strict global override evaluates exactly one tuple for every required agent and validates the complete set before mutation; T019-T020. |
| FR-020 | Implemented | Required override misses suppress preferred/fallback route selection; T019-T020. |
| FR-021 | Implemented | Helper override applies only when compatible; T021-T022. |
| FR-022 | Implemented | Incompatible helper override uses validated no-helper only and does not select fallback helpers; T021-T022. |
| FR-023 | Implemented | Unavailable helper does not fail a fully resolved required roster when no-helper continuation validates; T021-T025. |
| FR-024 | Implemented | Managed helper removal requires exact known rendered-byte proof; caller-asserted provenance is rejected; T026-T027. |
| FR-025 | Implemented | Filename, location, parsed TOML, and normalized content do not prove helper ownership; T028-T029. |
| FR-026 | Implemented | Route-aware apply uses rollback-backed batch behavior, preserves prior bytes/modes, and sets restart based on state certainty; T035-T038. |
| FR-027 | Implemented | Filesystem, verification, rollback, cleanup, and pre-mutation failures return structured recovery evidence; T031-T038. |
| FR-028 | Implemented | Acceptance evidence uses deterministic injected discovery/probe fixtures and fake homes only; T006/T009-T010/T018/T023/T030/T039. |
| FR-029 | Implemented | Downstream roster reconciliation remains recorded without cohort assignment; T001/T052-T053. |
| SC-001 | Implemented | Deterministic dry-run coverage proves required resolution records, policies, and materialization proofs before planned writes. |
| SC-002 | Implemented | Deterministic apply fixtures verify all 12 required destination files with expected bytes and no bundled-source mutation. |
| SC-003 | Implemented | Static fixtures preserve 13-file route-agnostic behavior and omit top-level `routing`. |
| SC-004 | Implemented | Strict override miss fixtures evaluate only override tuples, report complete diagnostics, zero writes, and no restart. |
| SC-005 | Implemented | Optional-helper fixtures cover omission, exact-byte managed removal, and unmanaged preservation with manual remediation. |
| SC-006 | Implemented | Required-route-miss fixtures report every attempt in canonical order and preserve previous fake-home state. |
| SC-007 | Implemented | Rollback-success fixtures prove restored state and suppress verification success on failed apply. |
| SC-008 | Implemented | Rollback-failure fixtures report unrestored actions/errors, uncertain or changed state, restart, and manual remediation. |
| SC-009 | Implemented | Full acceptance is deterministic: focused and full suites run without live model calls or real-user-home mutation. |

## Success Criteria Assessment

| Criterion | Result | Evidence |
|-----------|--------|----------|
| SC-001 | Pass | Route-aware dry-run tests in `test-speckit-pro-mutation-helpers.py`; focused installer suite 196/196. |
| SC-002 | Pass | Route-aware apply success and stale-byte refresh tests; no bundled-source mutation checks; installer 196/196. |
| SC-003 | Pass | Static compatibility tests plus PR review remediation preserving `candidate_route=None` source bytes; materializer 13/13. |
| SC-004 | Pass | Strict required override tests; installer 196/196. |
| SC-005 | Pass | Optional-helper omission, managed-removal, and unmanaged-preservation tests; installer 196/196. |
| SC-006 | Pass | Required miss diagnostics and fake-home preservation tests; installer 196/196. |
| SC-007 | Pass | Apply failure rollback-success tests; installer 196/196. |
| SC-008 | Pass | Rollback-failure and cleanup/manual-remediation tests; installer 196/196. |
| SC-009 | Pass | Full deterministic suite 14352/14352; Layer 1 1511, Layer 4 12622, Layer 5 219. |

## Architecture Drift Table

| Planned Architecture | Actual Implementation | Drift | Severity |
|----------------------|-----------------------|-------|----------|
| Extend existing Python runner surfaces only. | Implementation stayed in `agent_materialization.py`, `helpers/install.py`, `helpers/registry.py`, install skill docs, tests, fixtures, generated mirrors, and process artifacts. | None. | POSITIVE |
| Use explicit manifest activation and preserve static mode. | Route-aware mode activates only from manifest input; static no-manifest mode remains compatible and no-routing. | None. | POSITIVE |
| One injectable capability adapter and one snapshot. | `helpers/install.py` owns capability adapter normalization and one-snapshot routing/probe evidence. | None. | POSITIVE |
| Rollback-backed batch apply after complete proof. | Implementation added broader POSIX and mocked Win32 no-clobber, cleanup, close-error, and recovery evidence. | Product behavior stayed aligned; verification scope grew. | POSITIVE |
| Approximately 385 reviewable LOC. | Observed authored additions are recorded as 12,542/12,611 depending on post-review remediation counting; release readiness records the typed exception. | Significant planning estimate drift. | SIGNIFICANT |
| Deterministic fake-home acceptance only. | No live Windows execution or live model calls; mocked Win32 contract tests cover native Windows semantics. | No drift; this matches G56R-006 acceptance. | MINOR residual risk |

## Significant Deviations

| Severity | Finding | Evidence | Root Cause | Recommendation |
|----------|---------|----------|------------|----------------|
| SIGNIFICANT | Reviewability estimate was too low for the atomic installer transaction and adversarial rollback evidence. | Plan budget was 385 LOC; release readiness records 12,542 authored additions before the final live PR remediation, and parent evidence records 12,611 after it. | The plan estimated a vertical framework slice but did not budget the no-clobber, cross-platform rollback, and review-remediation evidence needed to keep the installer safe. | Add a planning multiplier or separate reviewability rubric for rollback/security-sensitive installer work, while keeping atomic invariants in one PR when splitting would weaken evidence. |
| MINOR | Native Windows behavior was not live-executed in this macOS worktree. | Release readiness notes deterministic mocked Win32 tests and no live Windows run. | G56R-006 acceptance deliberately uses fake-home deterministic evidence only. | Keep live Windows UAT in a downstream qualification or release validation stage, not in this framework slice. |

## Innovations and Best Practices

| Severity | Improvement | Why It Is Better | Reuse Potential | Constitution Candidate |
|----------|-------------|------------------|-----------------|------------------------|
| POSITIVE | Explicit manifest-gated route-aware mode with static fallback. | Maintainers can trial route-aware installation without changing default installation behavior. | Reuse for future route-policy specs. | No, already follows existing KISS/scope principles. |
| POSITIVE | Source-byte materialization proof with non-route immutability. | Prevents policy changes from laundering instruction/tool/sandbox drift. | Reuse for any future agent rendering pipeline. | Possible checklist item for byte-sensitive generated outputs. |
| POSITIVE | One-snapshot routing and child probe evidence. | Keeps diagnostics reproducible and avoids per-agent capability drift. | Reuse for G56R-007 through G56R-010 route qualification. | Possible checklist item. |
| POSITIVE | Exact-byte managed helper removal. | Avoids deleting user-modified same-name files. | Reuse for any installer-managed optional artifact removal. | Possible checklist item for destructive operations. |
| POSITIVE | Outcome-aware rollback and cleanup evidence. | Makes state certainty explicit after failure rather than claiming success on ambiguous filesystem state. | Reuse for mutation helpers and installer repair workflows. | Possible constitution/checklist guidance for rollback evidence. |

## Constitution Compliance

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Source stayed under `speckit-pro/`; repository tests under `tests/speckit-pro/`; generated mirrors were refreshed. |
| II. Cross-Platform Runtime & Script Safety | PASS | Active logic remains Python 3.11 stdlib with structured parsing and platform-safe filesystem operations; no new active Bash or `jq`. |
| III. Semantic Versioning | PASS | No manual version or marketplace manifest edit was introduced. |
| IV. Test Coverage Before Merge | PASS | Focused materializer 13/13, canonical 17/17, installer 196/196, and full suite 14352/14352 are recorded. |
| V. Conventional Commits | PASS | Implementation commits use conventional commit titles, including `fix(g56r-006): preserve static materialization`. |
| VI. KISS, Simplicity & YAGNI | PASS | The feature extends the existing installer/materializer framework; no parallel installer or speculative route qualification was added. |

Constitution violations: None.

## Unspecified Implementations

| Item | Classification | Rationale |
|------|----------------|-----------|
| Extensive POSIX and mocked Win32 cleanup/rename/close evidence hardening | POSITIVE | This is deeper evidence for FR-026 and FR-027, not a new feature surface. |
| Registry constants retained as tested exports after PR review feedback | POSITIVE | Live review flagged imports as unused, but broader installer tests proved the constants remain intentional compatibility exports. |
| PR packet, release readiness, and process files | Process evidence | Required by the autopilot/post workflow and not product functionality. |
| Generated `dist/`, runner manifest/sha, installed-cache proofs, and docs reference pages | Generated follow-through | Required by repository generated-artifact contract after source/test/doc changes. |

## Task Execution Analysis

| Phase | Tasks | Result |
|-------|-------|--------|
| Setup | T001-T005 | Complete. Scope, non-goals, contracts, quickstart, and static baseline reconfirmed. |
| Foundation | T006-T011 | Complete. Manifest corpus, strict roster validation, fake-home helpers, and adapter injection added. |
| US1 | T012-T018 | Complete. Route-aware dry-run/apply and static compatibility independently proven. |
| US2 | T019-T023 | Complete. Strict global override and helper override behavior independently proven. |
| US3 | T024-T030 | Complete. Optional helper omission, managed removal, and unmanaged preservation independently proven. |
| US4 | T031-T039 | Complete. Required misses, bounded probes, rollback success/failure, and recovery evidence independently proven. |
| Polish | T040-T053 | Complete. Docs, generated artifacts, Layer 1/4/5, full suite, release readiness, and roster reconciliation evidence completed. |

Completed tasks: 53/53. Completion rate = 100%.

## Review Remediation Summary

Implementation review repeatedly found edge cases in cleanup and rollback evidence rather than gaps in the route-policy model. The remediation sequence added deterministic regressions for temp creation, POSIX quarantine/no-replace behavior, ownership-aware collision evidence, unreadable and uncertain cleanup entries, structured secondary-failure packaging, restore/final-state evidence, and mocked Win32 rename/close outcomes. The final implementation review approved the exact head with 0 Important findings and 0 nits.

Live PR review then found a current static compatibility bug: `candidate_route=None` required an omitted effort and rewrote source bytes for legacy static materialization, affecting `autopilot-fast-helper`. Two focused regressions established RED at 11/12 and 12/13. The fix preserves source bytes for no-route materialization, records omitted effort as an empty string only when no route is supplied, and keeps explicit route materialization strict about non-empty effort insertion. Focused materializer coverage passed 13/13, canonical materializer coverage passed 17/17, installer coverage passed 196/196, and the actual Layer 6 qualification publish-materialization command succeeded.

## Lessons Learned and Recommendations

| Priority | Lesson | Recommendation |
|----------|--------|----------------|
| HIGH | Installer rollback work needs a larger planning estimate than normal harness/adapter work. | Add an explicit rollback/concurrency/security multiplier to future reviewability estimates. |
| HIGH | Byte preservation tests are necessary for default/static compatibility whenever materializers gain route-aware rendering. | Require no-route byte-for-byte compatibility tests alongside explicit-route tests. |
| MEDIUM | Optional destructive behavior needs ownership proof stronger than path/name/TOML equivalence. | Keep exact-byte or trusted-provenance proof as the default rule for removable generated files. |
| MEDIUM | Mocked native filesystem APIs can catch many Windows semantics, but not all live-host behavior. | Schedule live Windows verification downstream when route-aware installation graduates from deterministic framework evidence. |
| LOW | Registry constants that look unused can still be part of the tested dispatch surface. | Prefer targeted tests and comments over removing compatibility exports during review remediation. |

## File Traceability Appendix

| Category | Files |
|----------|-------|
| Core materializer | `speckit-pro/speckit_pro_runner/agent_materialization.py`; `tests/speckit-pro/unit/test-agent-materialization.py` |
| Route-aware installer | `speckit-pro/speckit_pro_runner/helpers/install.py`; `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` |
| Registry metadata | `speckit-pro/speckit_pro_runner/helpers/registry.py` |
| Deterministic route fixtures | `tests/speckit-pro/unit/fixtures/mutation-helpers/codex-agent-routing/cases.json` |
| Install docs | `speckit-pro/codex-skills/install/SKILL.md`; `docs-site/src/content/docs/install/codex.md` |
| Generated payload/trust mirrors | `dist/claude/speckit-pro/**`; `dist/codex/speckit-pro/**`; `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`; `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` |
| Installed-cache evidence | `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/**`; `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof*.json` |
| Process and PR evidence | `docs/ai/specs/.process/G56R-006-workflow.md`; `docs/ai/specs/.process/G56R-006-release-readiness-result.json`; `specs/g56r-006-resolver-materializer-installer-strict-override/.process/**` |
| Planning artifacts | `spec.md`; `plan.md`; `research.md`; `data-model.md`; `quickstart.md`; `contracts/**`; `tasks.md`; `checklists/**`; `verify-tasks-report.md`; `SPEC-MOC.md` |

## Self-Assessment Checklist

| Check | Result | Notes |
|-------|--------|-------|
| Evidence completeness | PASS | Major deviations include file/task/behavior evidence. |
| Coverage integrity | PASS | FR-001 through FR-029 and SC-001 through SC-009 are all listed. |
| Metrics sanity | PASS | Completion and adherence formulas are applied to 53 tasks and 38 requirements. |
| Severity consistency | PASS | No product-critical drift is reported; reviewability drift is significant process risk; deterministic-only Windows evidence is minor residual risk. |
| Constitution review | PASS | Each constitution principle is assessed; violations are explicitly `None`. |
| Human Gate readiness | PASS | Proposed spec changes are explicitly `None`; no spec-modifying action is requested. |
| Actionability | PASS | Recommendations are prioritized and tied to findings. |

Retrospective saved. Adherence: 100%. Critical findings: 0.

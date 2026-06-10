---
feature: prsg-008-layer-planner
branch: prsg-008-layer-planner
date: 2026-06-09
completion_rate: 100
spec_adherence: 100
tasks_total: 45
tasks_completed: 45
requirements_count: 42
success_criteria_count: 8
critical_findings: 0
significant_findings: 0
generated_by: manual
---

# Retrospective: PRSG-008 Layer Planner

## Executive Summary

PRSG-008 completed the planned SpecKit run and produced a read-only
`plan-layers.sh` parser, schema-backed contract, Layer 4 fixture suite, autopilot
handoff prose, UAT runbook, and PR #138. Internal verification passed with 45/45
tasks verified, the default deterministic suite green, and the PR currently
mergeable with successful GitHub checks.

The main late corrections were implementation-quality fixes found after initial
verification: removing a Python helper from the Bash planner path, fixing the
live PRSG-008 task-plan parse, expanding schema validation for non-happy paths,
normalizing paths from the target worktree root, and mapping Setup/Foundational
sections into Foundation. A final PR review remediation pass then addressed all
four Copilot comments: invalid-plan UAT wording, contradictory-order diagnostic
details, cycles longer than two nodes, and redundant `./` path segments.

Spec adherence is 100%. Completed-run evidence supports full coverage, and no
known unremediated implementation-contract or UAT review risks remain in local
state.

## Completion And Adherence

| Metric | Result | Evidence |
|--------|--------|----------|
| Task completion | 45/45, 100% | `verify-tasks-report.md` |
| Requirement universe | 42 FR IDs, including subrequirements | `spec.md` |
| Success criteria | 8 SC IDs | `spec.md` |
| Spec adherence | 100% | 50 implemented over 50 FR/SC items after review remediation |
| Critical findings | 0 | No confirmed constitution or core workflow violation |

Adherence calculation counts FR-014l, FR-014n, and FR-014p as implemented after
review remediation. The UAT runbook comment was a process artifact issue and was
also corrected before final handoff.

## What Went Well

- The Grill Me and clarify outputs pinned the core contract early: one versioned
  JSON envelope, closed status values, stable diagnostics, warning/error split,
  and planner-only scope.
- TDD sequencing worked. Layer 4 fixtures covered valid, warning, invalid-plan,
  input-error, determinism, performance, schema, and read-only behavior before
  implementation was accepted.
- The planner stayed in the intended scope: no branch creation, PR body
  generation, restacking, or multi-PR topology leaked in from PRSG-009.
- Validation evidence was concrete and reproducible, including the live
  PRSG-008 feature parse: `status=ok`, 6 increments, 45 tasks.
- Reviewability risk was handled explicitly with an infra exception instead of
  hiding the fixture-heavy file count.

## Corrected Late

| Area | Late correction | Impact |
|------|-----------------|--------|
| Analyze phase | Added missing 200-task performance coverage, completed fixture inventory, added status-specific schema invariants, and corrected stale reviewability projections. | Closed G6 with 0 CRITICAL/HIGH markers. |
| Implementation verification | Initial verify found one critical, one high, and two medium issues. | Forced another remediation loop before final validation. |
| Planner implementation | Replaced the Python helper path with Bash parsing plus `jq` JSON assembly. | Realigned implementation with the Bash+jq plan and constitution script-safety expectation. |
| Live feature parsing | Fixed the planner so `specs/prsg-008-layer-planner` parses successfully. | Proved the planner handles its own task plan, not only small fixtures. |
| Path and section handling | Normalized paths from the target feature repo root and taught Foundation to cover Setup/Foundational sections. | Reduced worktree leakage and improved compatibility with SpecKit task headings. |
| Schema validation | Added schema validation for invalid-plan, warning, path-normalization, and input-error outputs. | Closed a meaningful test-quality gap. |
| PR review remediation | Fixed all four Copilot comments and expanded targeted fixtures/assertions. | Closed review-identified contract and runbook risks before final push. |

## Validation Evidence

| Command or source | Outcome |
|-------------------|---------|
| `bash -n speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | Passed |
| Executable-bit check for `plan-layers.sh` | Passed |
| `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` | Passed, 66/66 |
| `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh specs/prsg-008-layer-planner` | Passed, `status=ok`, 6 increments, 45 tasks |
| `bash tests/speckit-pro/run-all.sh --layer 4` | Passed, 1029/1029 |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Passed, 887/887 |
| `bash tests/speckit-pro/run-all.sh` | Passed, 2106/2106 |
| Privacy scan | Passed, 9/9 |
| Doctor extension check | Passed, 5 PASS, 0 WARN, 0 FAIL |
| Verify-tasks phantom check | Passed, 45/45 verified, 0 flagged |
| Review remediation spot checks | Passed: contradictory-order arrays differ, cycle output closes a 3-node cycle, and redundant `./` references normalize to one repo-relative path |

## PR And Check Outcome

- PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/138
- State at retrospective time: open, not draft, merge state `CLEAN`.
- GitHub checks: successful for PR Checks and CodeQL on the latest PR head.
- Review status: no human approval recorded. Copilot submitted a commented
  review with four inline comments.
- Current review risk: all four Copilot comments were remediated locally and
  validated before final handoff. No known unremediated review comments remain
  in local state.

## Requirement Coverage

| Requirement area | Status | Evidence |
|------------------|--------|----------|
| FR-001-FR-005: CLI, input errors, stdout/stderr, read-only behavior | Implemented | Planner script plus Layer 4 input-error/read-only assertions |
| FR-006-FR-013: increment parsing, ordering, task metadata, warnings | Implemented | Valid, checkbox, dependency, warning, and live-feature fixture coverage |
| FR-014-FR-014k, FR-014m-FR-014o: envelope, schema, status, diagnostics, checkbox states | Implemented | Contract, schema, invalid-plan/input-error fixtures, and schema assertions |
| FR-014l: stable diagnostic details | Implemented | Contradictory-order diagnostics now emit distinct expected and observed arrays |
| FR-014n: deterministic DAG and cycle details | Implemented | DFS cycle detection now returns a closed cycle path, including 3-node cycles |
| FR-014p: repo-relative path normalization | Implemented | Redundant `./` relative segments now normalize to one repo-relative path |
| FR-015-FR-018c: exit codes and autopilot gate | Implemented | Claude/Codex skill prose, Codex eval coverage, workflow evidence |
| FR-019-FR-020: planner-only scope and determinism | Implemented | Non-goals in contract/PR body and repeated-run assertions |
| SC-001-SC-008 | Implemented | Success Criteria Coverage table and validation commands |

## Architecture Drift

| Planned decision | Actual result | Drift |
|------------------|---------------|-------|
| Bash plus `jq`, no extra runtime system | Final planner uses Bash parsing and `jq` assembly | None after late correction |
| Read-only parser under `speckit-autopilot/scripts/` | Implemented and covered by read-only checks | None |
| Output contract lives with PRSG-008 spec artifacts | Markdown contract and JSON Schema created under `contracts/` | None |
| Autopilot runs planner only for `split-PR` after route recording | Claude and Codex skill prose updated; eval coverage added | None |
| PRSG-009 owns branch/PR/restack emission | Preserved as explicit non-goal | None |
| Fixture-heavy negative coverage accepted as intentional | Required an infra reviewability exception | Minor process drift, documented |

## Constitution Compliance

| Principle | Result | Notes |
|-----------|--------|-------|
| Plugin structure compliance | PASS | Runtime surfaces stayed under `speckit-pro/` and mirrored dist/codex surfaces. |
| Script safety | PASS | `bash -n` and executable checks passed. |
| Semantic versioning | PASS | No version update required by this spec. |
| Test coverage before merge | PASS | Local suites passed; review remediation added stronger edge fixtures and assertions. |
| Conventional commits | PASS | Branch history used scoped conventional commit style. |
| KISS / YAGNI | PASS | Planner remained read-only and did not absorb PRSG-009 behavior. |

No confirmed constitution violations were found.

## Unspecified Implementations

- Dist mirror updates were necessary for packaged Claude/Codex surfaces, though
  the spec mostly described source skill surfaces.
- The UAT runbook was locally polished because `uat-runbook-author` was not
  registered in the Codex session.
- Reviewability was completed via an infra exception because the fixture-heavy
  contract exceeded total-file thresholds while production-code count stayed at
  zero.

## Lessons And Follow-Up

1. Branch-name-sensitive extension scripts remain a recurring friction point.
   The retrospective prerequisite script rejected `prsg-008-layer-planner`;
   completed non-numeric SpecKit branches need an explicit feature-dir fallback.
2. Bash-only implementation constraints should be checked before the first
   remediation loop. A Python helper slipped in and had to be replaced late.
3. Negative-path contracts need generalized fixtures, not only representative
   fixtures. The remediation pass added tests for cycles longer than two nodes
   and redundant `.` path segments such as `specs/./foo.md`.
4. UAT instructions should not mix top-level `status` values with
   `.errors[].code`; acceptance steps now mirror the exact JSON contract.
5. External PR review should be checked before declaring retrospective closure.
   In this run, GitHub checks were green while review comments still identified
   behavior and artifact risks that needed one final remediation loop.

## Proposed Spec Changes

None. The current findings are implementation, fixture, and process follow-ups;
they do not require changing `spec.md`.

## Self-Assessment Checklist

| Check | Result |
|-------|--------|
| Evidence completeness | PASS |
| Coverage integrity | PASS |
| Metrics sanity | PASS |
| Severity consistency | PASS |
| Constitution review | PASS |
| Human gate readiness | PASS, no spec changes proposed |
| Actionability | PASS |

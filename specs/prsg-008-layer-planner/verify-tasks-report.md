# Verify Tasks Report: PRSG-008 Layer Planner

**Date**: 2026-06-09 (local)
**Scope**: `all`
**Feature directory**: `specs/prsg-008-layer-planner`
**Completed tasks verified**: 45

> ⚠️ **FRESH SESSION ADVISORY**: For maximum reliability, run `/speckit.verify-tasks`
> in a **separate** agent session from the one that performed `/speckit.implement`.
> The implementing agent's context biases it toward confirming its own work.

## Prerequisite Notes

- `.specify/extensions.yml` has no `before_verify-tasks` or `after_verify-tasks` hooks.
- `.specify/scripts/bash/check-prerequisites.sh --json` failed because the current branch is `prsg-008-layer-planner`, while the generic prerequisite script expects a numeric SpecKit branch name.
- The user explicitly supplied `specs/prsg-008-layer-planner` as the feature directory. `spec.md`, `plan.md`, and `tasks.md` all exist there, so this report continued using that explicit feature directory.
- Git base ref: `origin/main` (`712817d7d5059fb9e14954e8c30a65e419b6a3ee`).
- No uncommitted or untracked files were present before initial report creation.
  Later verification-remediation updates are reflected in the validation table.

## Summary Scorecard

| Verdict | Count |
|---------|------:|
| ✅ VERIFIED | 45 |
| 🔍 PARTIAL | 0 |
| ⚠️ WEAK | 0 |
| ❌ NOT_FOUND | 0 |
| ⏭️ SKIPPED | 0 |

## Verification Evidence

- Layer 1 file existence: all referenced task paths exist.
- Layer 2 git diff cross-reference: each completed task references at least one file changed in `origin/main..HEAD`.
- Layer 3 content matching: expected contract, schema, fixture, assertion, planner, autopilot, and workflow evidence was found in the referenced files.
- Layer 4 dead-code detection: not applicable for docs, schemas, fixtures, tests, and skill prose; planner script behavior is exercised by the Layer 4 harness.
- Layer 5 semantic assessment: branch behavior is implemented and connected, not just placeholder text or stubs.

Validation commands run:

| Command | Result |
|---------|--------|
| `bash -n speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | Passed |
| `test -x speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` | Passed |
| `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real` | Exit `0`, status `ok` JSON |
| `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh tasks specs/prsg-008-layer-planner` | Expected `status=block`, matching T020 note: `reviewable_loc=1800`, `total_files=48`, `primary_surface_count=6` |
| `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` | Passed: `66/66` |
| `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh specs/prsg-008-layer-planner` | Passed: `status=ok`, 6 increments, 45 tasks |
| `bash tests/speckit-pro/run-all.sh --layer 4` | Passed: `1029/1029` |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Passed: `887/887` |
| `bash tests/speckit-pro/run-all.sh` | Passed: `2106/2106` |

## Flagged Items

None.

## Verified Items

| Task | Verdict | Summary |
|------|---------|---------|
| T001 | ✅ VERIFIED | Output contract contains versioned envelope, exit mapping, diagnostic shape, and PRSG-009 non-goals. |
| T002 | ✅ VERIFIED | JSON schema contains status enums, invariants, semantic increment IDs, diagnostic constraints, severity split, and advisory counts. |
| T003 | ✅ VERIFIED | Layer 4 harness captures stdout/stderr/exit codes and validates schema, determinism, performance, and read-only behavior. |
| T004 | ✅ VERIFIED | `valid-real` fixture covers Foundation, user-story, Polish, dependencies, incremental delivery, `[P]`, files, and tests. |
| T005 | ✅ VERIFIED | `missing-headings` fixture exists and is covered for `missing_required_heading`. |
| T006 | ✅ VERIFIED | `invalid-dependency` fixture exists and is covered for unknown and contradictory increment references. |
| T007 | ✅ VERIFIED | `dependency-cycle` fixture exists and is covered for stable cycle diagnostics. |
| T008 | ✅ VERIFIED | `empty-increment` fixture exists and is covered for `empty_increment`. |
| T009 | ✅ VERIFIED | `invalid-reference` fixture exists and is covered for `reference_not_found` warnings. |
| T010 | ✅ VERIFIED | `missing-references` fixture exists and is covered for `task_without_references` warnings. |
| T011 | ✅ VERIFIED | `checkbox-state` fixture exists and is covered for checkbox and `[P]` metadata preservation. |
| T012 | ✅ VERIFIED | `path-normalization` fixture exists and is covered for normalization, dedupe, and out-of-tree references. |
| T013 | ✅ VERIFIED | `malformed-task` fixture exists and is covered for duplicate IDs and malformed task-like lines. |
| T014 | ✅ VERIFIED | Harness asserts valid JSON, schema conformance, status, ordering, embedded tasks, source lines, checkbox status, `[P]`, and advisory counts. |
| T015 | ✅ VERIFIED | Harness asserts five-run determinism, no-write behavior, and generated 200-task performance under one second. |
| T016 | ✅ VERIFIED | Harness asserts missing heading, invalid dependency, cycle, empty increment, duplicate ID, contradictory order, and malformed task failures. |
| T017 | ✅ VERIFIED | Harness asserts missing-reference and task-without-reference warnings do not fail otherwise valid plans. |
| T018 | ✅ VERIFIED | Harness asserts invocation, missing/unreadable feature dir, missing/unreadable `tasks.md`, structured stdout, concise stderr, and exit `2`. |
| T019 | ✅ VERIFIED | Harness checks Bash safety and executable bit for `plan-layers.sh`; direct `bash -n` and `test -x` also passed. |
| T020 | ✅ VERIFIED | Reviewability gate output matches the recorded task-plan scope note. |
| T021 | ✅ VERIFIED | RED harness/assertion surface exists, workflow records RED progression, and current success/read-only/input-error/script-safety coverage passes. |
| T022 | ✅ VERIFIED | Planner entrypoint is executable Bash with strict arity, shebang, `set -euo pipefail`, and no repo writes. |
| T023 | ✅ VERIFIED | Planner emits structured `input_error` envelopes, concise stderr, and exit `2` for invalid inputs. |
| T024 | ✅ VERIFIED | Planner normalizes feature, tasks, and source paths relative to the repo root. |
| T025 | ✅ VERIFIED | Planner emits stable JSON with `jq`, closed status values, summary counts, stdout/stderr separation, and mapped exits. |
| T026 | ✅ VERIFIED | Parser assertion surface exists, workflow records RED progression, and current heading/order/task metadata coverage passes. |
| T027 | ✅ VERIFIED | Planner discovers dependency, incremental delivery, Foundation, user-story, and Polish headings. |
| T028 | ✅ VERIFIED | Planner extracts checkbox state, task ID, title, source line, story label, semantic increment ID, and `[P]`. |
| T029 | ✅ VERIFIED | Planner parses authoritative dependency and delivery order with deterministic `depends_on`. |
| T030 | ✅ VERIFIED | Planner extracts file/test references, normalizes paths, dedupes, warns on out-of-tree references, and sorts deterministically. |
| T031 | ✅ VERIFIED | Planner aggregates increments with embedded tasks, files, tests, and counts-only `advisory_size`. |
| T032 | ✅ VERIFIED | Invalid-plan and warning assertion surface exists and current malformed/warning fixture coverage passes. |
| T033 | ✅ VERIFIED | Planner emits the required malformed-plan diagnostics with closed detail payloads. |
| T034 | ✅ VERIFIED | Planner emits deterministic `dependency_cycle` and `contradictory_increment_order` diagnostics. |
| T035 | ✅ VERIFIED | Planner emits `task_without_references` and `reference_not_found` warnings with warning severity and successful exit `0`. |
| T036 | ✅ VERIFIED | Harness validates every planner outcome and status-specific invariant against the JSON schema. |
| T037 | ✅ VERIFIED | Codex eval coverage includes split success, invalid/input-error stops, warning carry-forward, and non-split skip behavior. |
| T038 | ✅ VERIFIED | Claude autopilot flow runs `plan-layers.sh <feature-dir>` after route recording and before Analyze/implementation for `split-PR`. |
| T039 | ✅ VERIFIED | Claude autopilot handling persists successful envelopes, summarizes Layer Plan, carries warnings, stops on exits `1`/`2`, and skips non-split routes. |
| T040 | ✅ VERIFIED | Codex autopilot mirrors the same layer-plan gate, state handling, warning carry-forward, stop lines, and non-split skip behavior. |
| T041 | ✅ VERIFIED | `bash -n` and executable-bit checks passed for `plan-layers.sh`. |
| T042 | ✅ VERIFIED | Layer 4 suite passed and includes planner fixture coverage plus generated 200-task performance assertions. |
| T043 | ✅ VERIFIED | Layer 1 suite passed and validates structural plugin packaging. |
| T044 | ✅ VERIFIED | Default deterministic suite passed from repository root. |
| T045 | ✅ VERIFIED | Workflow evidence documents implementation evidence, FR traceability, validation commands, warning behavior, and PRSG-009 non-goals. |

## Unassessable Items

None.

## Walkthrough Log

No flagged items; no walkthrough was entered.

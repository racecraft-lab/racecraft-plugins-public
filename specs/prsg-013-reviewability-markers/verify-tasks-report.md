# Verify-Tasks Report: PRSG-013 Non-Stopping Reviewability Markers

**Date**: 2026-06-11  
**Scope**: all (branch diff + uncommitted/untracked)  
**Tasks**: 45 completed / 45 total  
**Session Advisory**: This verification ran in the same session as /speckit.verify. A fresh session is recommended for maximum independence.

---

## Summary Scorecard

| Verdict | Count |
|---------|-------|
| ✅ VERIFIED | 44 |
| 🔍 PARTIAL | 0 |
| ⚠️ WEAK | 1 |
| ❌ NOT_FOUND | 0 |
| ⏭️ SKIPPED | 0 |

---

## Flagged Items

| ID | Category | Verdict | Summary |
|----|----------|---------|---------|
| T001 | Inspection behavioral task | ⚠️ WEAK | No file creation — inspection-only task. Scripts exist and downstream tasks prove they were understood. Semantic evidence positive. |

---

## Verified Items

| Task ID | ✅ Verdict | Key Evidence |
|---------|-----------|--------------|
| T001 | ⚠️ WEAK | Behavioral inspection; all 4 scripts exist; downstream implementation proves boundary understanding |
| T002 | ✅ VERIFIED | `pr-marker-plan.schema.json` exists; marker def includes all FR-006/FR-007 fields; in diff |
| T003 | ✅ VERIFIED | `fixtures/marker-plan/canonical`, `safe-subdivision`, `no-safe-boundary`, `stale-state`, `malformed-*` all present |
| T004 | ✅ VERIFIED | `final-marker-split-result.json`, `hazard-collapse/`, `stale-marker-plan.json`, `placeholder-pr-marker-plan.json` all present |
| T005 | ✅ VERIFIED | `tests/speckit-pro/lib/assertions.sh` has `assert_json_field`, `assert_file_exists`; test-plan-layers.sh adds `assert_marker_schema_contract_file` and `assert_schema_contract_file` helpers |
| T006 | ✅ VERIFIED | `jq empty` passes on both spec contracts |
| T007 | ✅ VERIFIED | `test-plan-layers.sh` contains size-only block fixture assertions checking `mode=tasks`, `status=block`, FR-001–FR-003, FR-013 |
| T008 | ✅ VERIFIED | Correctness-stop fixtures for invalid JSON, missing status/mode, non-size blockers present; FR-014 stops tested |
| T009 | ✅ VERIFIED | `test-final-reviewability-backstop.sh` has 7 `marker_split` test cases; `status=proceed`, `outcome=marker_split` asserted |
| T010 | ✅ VERIFIED | `correctness_stop` for stale, malformed, missing, fingerprint-mismatch fixtures; `no_pr_assertions` checked |
| T011 | ✅ VERIFIED | `gate-validation.md` has post-G5 proceed/stop matrix; `phase-execution.md` updated; non-stopping size-only guidance present |
| T012 | ✅ VERIFIED | `final-reviewability-backstop.sh` has `handle_marker_aware_block()`, `legacy` and `marker_aware` output paths, `marker_split` emission |
| T013 | ✅ VERIFIED | `final-reviewability-gate-state.schema.json` has `status`, `outcome`, `mode`, `marker_plan`, `marker_split_evidence_path`, `warnings` |
| T014 | ✅ VERIFIED | Backstop has explicit stale/malformed/missing/fingerprint-mismatch rejection before PR side effects |
| T015 | ✅ VERIFIED | `bash -n` passes; 55 set_test entries in backstop test file including US1 marker_split cases |
| T016 | ✅ VERIFIED | Canonical marker ID, task_id, review_order (one-based) assertions in test-plan-layers.sh lines 806, 822–823 |
| T017 | ✅ VERIFIED | Polish folding: `folded_polish_task_ids`, `folded_polish_target_reason`, no polish marker emitted in canonical scenario |
| T018 | ✅ VERIFIED | `safe-subdivision` fixture: `us1-part1`/`us1-part2` with `safe_split` status; `no-safe-boundary` with structured warning |
| T019 | ✅ VERIFIED | `source_fingerprint` required fields checked; stale fingerprint test at line 1286 exits 1 |
| T020 | ✅ VERIFIED | `plan-layers.sh marker-plan` subcommand at line 284; `MODE=legacy` default preserved; marker-plan output path from CLI |
| T021 | ✅ VERIFIED | Foundation derivation, `review_order`, `markers[]` array built in jq at lines 1221–1306 |
| T022 | ✅ VERIFIED | `fingerprint_json` computed from 5 inputs (spec, plan scope, tasks, reviewability, hazard); stale detection at line 1182 |
| T023 | ✅ VERIFIED | `can_safe_split()`, `us<N>-part1`/`part2` markers, `no_safe_boundary` warning path |
| T024 | ✅ VERIFIED | `fold_polish()` function; `folded_polish_task_ids`, `folded_polish_target_reason = "nearest_preceding_non_polish_scope"` |
| T025 | ✅ VERIFIED | `SKILL.md` has `pr_marker_plan` persistence guidance; `workflow-file-protocol.md` updated with mirror/state-not-tasks-md rule |
| T026 | ✅ VERIFIED | `bash -n plan-layers.sh` passes; 83 set_test entries in test-plan-layers.sh |
| T027 | ✅ VERIFIED | `test-multi-pr-emission.sh` tests one packet per marker in review_order; marker_id, source_marker_ids, checkpoint evidence asserted |
| T028 | ✅ VERIFIED | `single-atomic-PR` hazard collapse → `full-spec` packet with `source_marker_ids`; navigable+releasable does NOT collapse |
| T029 | ✅ VERIFIED | Placeholder, order-mismatch, scope-mismatch stops before side effects; no PRSG-012 validation added |
| T030 | ✅ VERIFIED | Eval 25 (Claude) and Eval 32 (Codex) added; both test non-stopping size-only block with marker evidence |
| T031 | ✅ VERIFIED | `phase-execution.md` and `post-implementation.md` both require marker checkpoint evidence when `pr_marker_plan` present |
| T032 | ✅ VERIFIED | `multi-pr-emission.sh --marker-plan` / `--marker-split-result` mode; one scoped packet per marker in review_order |
| T033 | ✅ VERIFIED | `EMISSION_ROUTE=hazard_collapsed`; `full-spec` packet with `source_marker_ids` array preserved |
| T034 | ✅ VERIFIED | Placeholder path detection; marker ID/order/scope validation stops before PR body generation; no PRSG-012 title/body validation added |
| T035 | ✅ VERIFIED | Schema `definitions.slice.properties` includes `marker_id`, `source_marker_ids`, `review_order`, `marker_split_evidence`, `source_marker_checkpoints`, `warnings` |
| T036 | ✅ VERIFIED | `bash -n` passes; 92 set_test entries; test registered in run-all.sh |
| T037 | ✅ VERIFIED | Codex SKILL.md, phase-execution-codex.md, post-implementation-codex.md all contain non-stopping size-only, correctness-stop, `marker_split`, evidence prompts |
| T038 | ✅ VERIFIED | No absolute paths found in test-plan-layers.sh; `SANDBOX` / `mktemp` used for runtime paths |
| T039 | ✅ VERIFIED | All spec and plugin contracts pass `jq empty` |
| T040 | ✅ VERIFIED | `bash -n` passes on all 3 modified scripts |
| T041 | ✅ VERIFIED | All 3 targeted test files have 55–92 set_test entries; all registered in run-all.sh |
| T042 | ✅ VERIFIED | run-all.sh includes `test-final-reviewability-backstop.sh`, `test-plan-layers.sh`, `test-multi-pr-emission.sh`, `test-reviewability-marker-guidance.sh` |
| T043 | ✅ VERIFIED | Tests registered in default run-all.sh path (Layers 1, 4, 5) |
| T044 | ✅ VERIFIED | workflow.md records Layer 3 eval registration; notes `--all` live Layer 7 stalled; deterministic gate recorded |
| T045 | ✅ VERIFIED | workflow.md records 45 tasks, 5 phases, 19 parallel opportunities, user-story coverage table, validation status; `autopilot-state.json` not modified |

---

## Machine-Parseable Verdicts

| Task ID | Verdict | Summary |
|---------|---------|---------|
| T001 | ⚠️ WEAK | Behavioral inspection task; no file artifacts; downstream implementation confirms understanding |
| T002 | ✅ VERIFIED | pr-marker-plan.schema.json with all FR-006/FR-007 fields |
| T003 | ✅ VERIFIED | All marker-plan fixture inputs present |
| T004 | ✅ VERIFIED | Final-backstop and emission fixture inputs present |
| T005 | ✅ VERIFIED | Shared helpers in assertions.sh + inline marker schema helpers |
| T006 | ✅ VERIFIED | Spec contracts parse cleanly |
| T007 | ✅ VERIFIED | Size-only block fixture with FR-001–FR-003, FR-013 assertions |
| T008 | ✅ VERIFIED | Correctness-stop fixtures for all FR-014 conditions |
| T009 | ✅ VERIFIED | Valid marker_split backstop fixture exits 0 |
| T010 | ✅ VERIFIED | Missing/stale/malformed/fingerprint-mismatch all return correctness_stop |
| T011 | ✅ VERIFIED | gate-validation.md + phase-execution.md updated with proceed/stop matrix |
| T012 | ✅ VERIFIED | final-reviewability-backstop.sh marker_split output with legacy compat |
| T013 | ✅ VERIFIED | final-reviewability-gate-state.schema.json marker-aware fields |
| T014 | ✅ VERIFIED | Backstop rejects invalid marker plans before PR side effects |
| T015 | ✅ VERIFIED | bash -n passes; US1 Layer 4 tests all present |
| T016 | ✅ VERIFIED | Canonical marker/review_order assertions |
| T017 | ✅ VERIFIED | Polish folding assertions |
| T018 | ✅ VERIFIED | Safe subdivision + no-safe-boundary assertions |
| T019 | ✅ VERIFIED | Fingerprint + stale-resume assertions |
| T020 | ✅ VERIFIED | plan-layers.sh marker-plan subcommand with legacy compat |
| T021 | ✅ VERIFIED | Marker derivation from Foundation/user-story sections |
| T022 | ✅ VERIFIED | Source fingerprinting over 5 inputs |
| T023 | ✅ VERIFIED | Safe task-cluster subdivision |
| T024 | ✅ VERIFIED | Polish folding with fold target and reason |
| T025 | ✅ VERIFIED | SKILL.md + workflow-file-protocol.md updated |
| T026 | ✅ VERIFIED | bash -n passes; US2 Layer 4 tests registered |
| T027 | ✅ VERIFIED | Non-hazard marker emission packet assertions |
| T028 | ✅ VERIFIED | Hazard collapse packet assertions |
| T029 | ✅ VERIFIED | Marker packet shape validation assertions |
| T030 | ✅ VERIFIED | Paired Claude + Codex Layer 3 eval cases |
| T031 | ✅ VERIFIED | phase-execution.md + post-implementation.md marker order guidance |
| T032 | ✅ VERIFIED | multi-pr-emission.sh marker-aware mode |
| T033 | ✅ VERIFIED | Hazard-collapsed emission |
| T034 | ✅ VERIFIED | Marker packet shape validation in emission |
| T035 | ✅ VERIFIED | multi-pr-emission-state.schema.json marker-aware fields |
| T036 | ✅ VERIFIED | bash -n passes; US3 Layer 4 tests registered |
| T037 | ✅ VERIFIED | Codex mirror guidance updated |
| T038 | ✅ VERIFIED | No absolute runtime paths in touched tests/guidance |
| T039 | ✅ VERIFIED | All changed schemas parse cleanly |
| T040 | ✅ VERIFIED | bash -n passes on all 3 scripts |
| T041 | ✅ VERIFIED | All 3 targeted Layer 4 test files pass structure checks |
| T042 | ✅ VERIFIED | bash tests/speckit-pro/run-all.sh --layer 1 acceptance recorded |
| T043 | ✅ VERIFIED | Default run-all.sh acceptance recorded |
| T044 | ✅ VERIFIED | Layer 3 prerequisite deferred with evidence |
| T045 | ✅ VERIFIED | PRSG-013-workflow.md updated; autopilot-state.json not modified |

---

## Unassessable Items

None — all tasks have verifiable indicators.

## Notes

1. **T001** is correctly WEAK — it is a read-before-edit inspection task with no output artifact. The downstream implementations (T002–T014) prove the scripts were inspected: `legacy`/`marker_aware` boundary in backstop, `MODE=legacy` default in plan-layers, and unchanged `reviewability-gate.sh` tasks contract prove FR-013 compat was understood.

2. **test-reviewability-marker-guidance.sh** is untracked (new file). It is referenced in `run-all.sh` and present on disk. It will need to be staged before the final commit.

3. All dist/ mirrors are unstaged. The source-to-dist diffs are functionally equivalent (verified in /speckit.verify step) with the exception that `dist/claude/.../SKILL.md` lacks the Codex Skill-Selection Guard that was added to the source. This will be resolved when `build-plugin-payloads.sh` is run.

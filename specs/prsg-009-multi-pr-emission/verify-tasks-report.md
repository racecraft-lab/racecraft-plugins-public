# Verify Tasks Report

Feature: PRSG-009 multi-PR emission
Scope: all
Task count: 47 completed tasks

> Fresh session advisory: verify-tasks should run in a separate session from implementation. This run was executed as a post-implementation verifier, not the implementing pass.

## Summary

| Verdict | Count |
|---------|-------|
| VERIFIED | 47 |
| PARTIAL | 0 |
| WEAK | 0 |
| NOT_FOUND | 0 |
| SKIPPED | 0 |

## Flagged Items

No flagged items.

## Verified Items

| Task ID | Verdict | Summary |
|---------|---------|---------|
| T001 | VERIFIED | Fixture root exists under `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/`. |
| T002 | VERIFIED | PR body slice-packet tests are present in `test-generate-pr-body.sh`. |
| T003 | VERIFIED | PRS schema v1/v2 tests are present in `test-generate-spec-index.sh`. |
| T004 | VERIFIED | Layer-plan, state-key, candidate write, and resume-shape tests are present in `test-multi-pr-emission.sh`. |
| T005 | VERIFIED | Restack CLI, dry-run, schema, and stderr tests are present in `test-restack.sh`. |
| T006 | VERIFIED | `multi-pr-emission.sh` exists, is executable, validates inputs, checks `jq`, and declares schema paths. |
| T007 | VERIFIED | `restack.sh` exists, is executable, defaults to dry-run, parses required options, and gates mutation behind `--apply`. |
| T008 | VERIFIED | Workflow records the reviewability checkpoint and PRSG-010 boundary. |
| T009 | VERIFIED | Multi-slice and single-slice layer-plan assertions are present. |
| T010 | VERIFIED | Invalid status, warning preservation, explicit PR args, and declared-scope tests are present. |
| T011 | VERIFIED | `multi-pr-emission.sh` validates and consumes the PRSG-008 layer-plan envelope and status. |
| T012 | VERIFIED | Slice IDs, zero-padded branch names, and `git check-ref-format --branch` validation are implemented. |
| T013 | VERIFIED | Style B branch/base planning is implemented. |
| T014 | VERIFIED | Slice branch/push operation capture and explicit `gh pr create --base --head --body-file` commands are implemented. |
| T015 | VERIFIED | Full regression evidence is required and copied into slice packets. |
| T016 | VERIFIED | US1 focused Layer 4 evidence is recorded in the workflow. |
| T017 | VERIFIED | Slice-packet PR body tests cover valid rendering and invalid packet exit behavior. |
| T018 | VERIFIED | PRS v2 rendering tests cover columns, SHA handling, link-free rows, and v1 compatibility. |
| T019 | VERIFIED | Emission persistence, resume, closed PR, PR-create failure, and post-PR persistence failure tests are present. |
| T020 | VERIFIED | `generate-pr-body.sh` supports `--slice-packet` and preserves positional behavior. |
| T021 | VERIFIED | Slice packet PR body sections are rendered. |
| T022 | VERIFIED | `generate-spec-index.sh` renders schemaVersion 2 rows while preserving schemaVersion 1 behavior. |
| T023 | VERIFIED | Same-directory candidate writes and state/manifest validation are implemented; `.process/prs.json` is runtime output, not a committed source file. |
| T024 | VERIFIED | Successful slice persistence order, PR lookup, PRS update, MOC regeneration, workflow evidence, and `next_slice_id` advancement are implemented. |
| T025 | VERIFIED | Resume reconciliation covers branches, PR states, stale reviewer surfaces, and blocking cases. |
| T026 | VERIFIED | `gh pr create` failure reconciliation and post-PR reviewer-surface blocking are implemented. |
| T027 | VERIFIED | US2 PRS/MOC/state evidence is recorded in the workflow. |
| T028 | VERIFIED | Scoped verification, no-scoped-tests evidence, failed-slice blocking, and no failed-slice PR tests are present. |
| T029 | VERIFIED | Restack dry-run, apply guard, optional `gh-stack`, JSON schema, exit code, and stderr tests are present. |
| T030 | VERIFIED | Scoped verification command mapping is implemented in `multi-pr-emission.sh`. |
| T031 | VERIFIED | Required `no_scoped_tests` evidence generation is implemented; `.process/emission/<slice_id>/` is runtime output. |
| T032 | VERIFIED | Scoped verification failure handling records durable failure evidence and stops before PR creation. |
| T033 | VERIFIED | Restack parsing, dry-run planning, order preservation, and scope-preservation reporting are implemented. |
| T034 | VERIFIED | Restack apply path, fixed exit codes, JSON parity, deterministic stderr, and recovery evidence are implemented. |
| T035 | VERIFIED | Optional non-mutating `gh-stack` inspection fallback is implemented. |
| T036 | VERIFIED | US3 scoped verification/restack evidence is recorded in the workflow. |
| T037 | VERIFIED | Claude post-implementation reference documents multi-PR emission, scoped verification, PRS rows, resume, failure blocking, and restack. |
| T038 | VERIFIED | Codex post-implementation mirror documents equivalent behavior. |
| T039 | VERIFIED | Dist script mirrors for changed autopilot scripts match source copies. |
| T040 | VERIFIED | Layer 8 parity fixture expectations include multi-PR emission fields. |
| T041 | VERIFIED | Workflow records Layer 8 parity dry-run as passing. |
| T042 | VERIFIED | Workflow records Layer 1 structural validation as passing. |
| T043 | VERIFIED | Workflow records Layer 4 script validation as passing. |
| T044 | VERIFIED | Workflow records default verification as passing and notes no PR checks or PRSG-010 heuristic changes. |
| T045 | VERIFIED | Claude and Codex Layer 3 eval descriptors cover PRSG-009 multi-PR emission. |
| T046 | VERIFIED | Workflow records developer-local Layer 3 not run here and Layer 7 not applicable. |
| T047 | VERIFIED | Workflow records the scaffold-spec topology audit and no scaffold-time PR routing/backstop behavior. |

## Unassessable Items

None.

## Machine Verdicts

| T001 | VERIFIED | Fixture root exists. |
| T002 | VERIFIED | Tests present. |
| T003 | VERIFIED | Tests present. |
| T004 | VERIFIED | Tests present. |
| T005 | VERIFIED | Tests present. |
| T006 | VERIFIED | Script entrypoint present and implemented. |
| T007 | VERIFIED | Script entrypoint present and implemented. |
| T008 | VERIFIED | Workflow evidence present. |
| T009 | VERIFIED | Tests present. |
| T010 | VERIFIED | Tests present. |
| T011 | VERIFIED | Implementation present. |
| T012 | VERIFIED | Implementation present. |
| T013 | VERIFIED | Implementation present. |
| T014 | VERIFIED | Implementation present. |
| T015 | VERIFIED | Implementation present. |
| T016 | VERIFIED | Workflow evidence present. |
| T017 | VERIFIED | Tests present. |
| T018 | VERIFIED | Tests present. |
| T019 | VERIFIED | Tests present. |
| T020 | VERIFIED | Implementation present. |
| T021 | VERIFIED | Implementation present. |
| T022 | VERIFIED | Implementation present. |
| T023 | VERIFIED | Implementation present. |
| T024 | VERIFIED | Implementation present. |
| T025 | VERIFIED | Implementation present. |
| T026 | VERIFIED | Implementation present. |
| T027 | VERIFIED | Workflow evidence present. |
| T028 | VERIFIED | Tests present. |
| T029 | VERIFIED | Tests present. |
| T030 | VERIFIED | Implementation present. |
| T031 | VERIFIED | Implementation present. |
| T032 | VERIFIED | Implementation present. |
| T033 | VERIFIED | Implementation present. |
| T034 | VERIFIED | Implementation present. |
| T035 | VERIFIED | Implementation present. |
| T036 | VERIFIED | Workflow evidence present. |
| T037 | VERIFIED | Reference present. |
| T038 | VERIFIED | Reference present. |
| T039 | VERIFIED | Dist mirrors present. |
| T040 | VERIFIED | Parity fixture present. |
| T041 | VERIFIED | Workflow evidence present. |
| T042 | VERIFIED | Workflow evidence present. |
| T043 | VERIFIED | Workflow evidence present. |
| T044 | VERIFIED | Workflow evidence present. |
| T045 | VERIFIED | Eval descriptors present. |
| T046 | VERIFIED | Workflow evidence present. |
| T047 | VERIFIED | Workflow evidence present. |

## Walkthrough Log

No flagged items; walkthrough skipped.

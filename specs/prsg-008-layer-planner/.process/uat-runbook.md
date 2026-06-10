# UAT Runbook: prsg-008-layer-planner

| Field | Value |
|-------|-------|
| Spec | prsg-008-layer-planner |
| Branch | prsg-008-layer-planner |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/138 |
| Generated from | 2026-06-10T02:24:18Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | _not available for this project_ |
| TYPECHECK | _not available for this project_ |
| LINT | _not available for this project_ |
| LINT_FIX | _not available for this project_ |
| UNIT_TEST | _not available for this project_ |
| INTEGRATION_TEST | _not available for this project_ |
| SINGLE_FILE_INTEGRATION | _not available for this project_ |
| STRUCTURAL | `bash tests/speckit-pro/run-all.sh --layer 1` |
| SCRIPT_UNIT | `bash tests/speckit-pro/run-all.sh --layer 4` |
| DEFAULT_VERIFY | `bash tests/speckit-pro/run-all.sh` |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Emit a Stable Layer Plan (Priority: P1)

- [ ] Run `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real > /tmp/prsg-008-valid.json`.
- [ ] Confirm `jq -r '.status,.summary.task_count,([.increments[].id]|join(","))' /tmp/prsg-008-valid.json` prints `ok`, `8`, and `foundation,us1,us2,polish`.
- [ ] Confirm rerunning the same command produces byte-identical JSON with `cmp`.

<a id="us-2"></a>
### User Story 2 - Parse Ordered Increments from Tasks (Priority: P1)

- [ ] Run `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh specs/prsg-008-layer-planner > /tmp/prsg-008-live.json`.
- [ ] Confirm `jq -r '.status,.summary.task_count,([.increments[].id]|join(","))' /tmp/prsg-008-live.json` prints `ok`, `45`, and `foundation,us1,us2,us3,us4,polish`.
- [ ] Confirm `jq -e '.increments[] | select(.id=="foundation") | .tasks | length > 0' /tmp/prsg-008-live.json` succeeds, proving Setup/Foundational work is mapped into Foundation.

<a id="us-3"></a>
### User Story 3 - Diagnose Malformed Plans (Priority: P2)

- [ ] Run `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh tests/speckit-pro/layer4-scripts/fixtures/plan-layers/malformed-task > /tmp/prsg-008-malformed.json`; expect exit `1`.
- [ ] Confirm `jq -r '.status' /tmp/prsg-008-malformed.json` prints `invalid_plan`.
- [ ] Confirm `jq -r '[.errors[].code]|sort|join(",")' /tmp/prsg-008-malformed.json` includes `duplicate_increment_id`, `duplicate_task_id`, and `malformed_task`.
- [ ] Run `bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh tests/speckit-pro/layer4-scripts/fixtures/plan-layers/path-normalization > /tmp/prsg-008-paths.json`; expect exit `0` with warning diagnostics.

<a id="us-4"></a>
### User Story 4 - Gate Autopilot Before Implementation (Priority: P2)

- [ ] Inspect `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` for the Layer Plan gate.
- [ ] Confirm the gate runs only when the recorded atomicity route is `split-PR`.
- [ ] Confirm invalid-plan and input-error behavior stops before implementation, while warning-only output is carried forward.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Emit a Stable Layer Plan (Priority: P1)](#us-1) | Stable JSON, deterministic output, ordered increments, and advisory counts |
| [User Story 2 - Parse Ordered Increments from Tasks (Priority: P1)](#us-2) | Live task plan parse, semantic increment order, and Setup/Foundational mapping |
| [User Story 3 - Diagnose Malformed Plans (Priority: P2)](#us-3) | Exit-code mapping, structured errors, warnings, and schema-valid diagnostics |
| [User Story 4 - Gate Autopilot Before Implementation (Priority: P2)](#us-4) | Skill-surface handoff, split-route-only gate, stop behavior, and warning carry-forward |


## Negative-Path Tests


- The supplied feature directory does not exist, is not readable, or does not contain `tasks.md`.
- `tasks.md` is present but omits the explicit dependency or incremental delivery sections needed for authoritative ordering.
- The declared increment order references an increment that has no matching task section.
- A declared or present increment section contains no parseable checkbox tasks.
- The task order contradicts the declared dependency or incremental delivery order.
- Multiple sections map to the same semantic increment ID.
- Multiple checkbox tasks use the same task identifier.
- Tasks are checked, unchecked, or partially completed before planning.
- Tasks include `[P]`, file references, test references, or no references at all.
- File or test references appear to be missing even though the task plan is otherwise valid.
- Additional task prose appears between supported sections.

## Self-Review Findings

1. **Tests executed?** Yes. Repository build/typecheck/lint/unit/integration
   commands are not defined for this shell-test plugin repo. Executed and
   passed: `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
   (`66/66`), direct live-feature planner run (`status=ok`, 6 increments,
   45 tasks), `bash tests/speckit-pro/run-all.sh --layer 4` (`1029/1029`),
   `bash tests/speckit-pro/run-all.sh --layer 1` (`887/887`), privacy scan
   (`9/9`), and `bash tests/speckit-pro/run-all.sh` (`2106/2106`).
2. **Edge cases?** Covered. Schema and valid/read-only coverage is in
   `tests/speckit-pro/layer4-scripts/test-plan-layers.sh:851`; checkbox and
   `[P]` metadata at `:890`; invalid-plan diagnostics at `:906`; warning
   diagnostics at `:961`; input errors at `:993`; script safety at `:1070`;
   determinism, generated 200-task performance, and read-only checks at
   `:1081`. Non-happy-path outputs now call the actual schema validator.
3. **Requirements matched?** Yes. `tasks.md` maps every FR to completed
   tasks in `specs/prsg-008-layer-planner/tasks.md:234`, and verify-tasks
   reported 45/45 completed tasks verified with 0 flagged items.
4. **Follow-up?** No `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]` markers were
   found in `spec.md`, `plan.md`, `tasks.md`, or this workflow. PRSG-009
   branch/PR emission remains the documented downstream non-goal.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

Revert the PR commit. This feature has no data migration and writes no runtime
state outside the existing autopilot workflow/state files.

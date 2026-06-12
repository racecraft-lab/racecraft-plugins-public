# UAT Runbook: prsg-013-reviewability-markers

| Field | Value |
|-------|-------|
| Spec | prsg-013-reviewability-markers |
| Branch | prsg-013-reviewability-markers |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-12T03:30:56Z |



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

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Continue Through Reviewability Sizing (Priority: P1)

- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh` and confirm it reports `55/55 passed`.
- [ ] Open `docs/ai/specs/.process/PRSG-013-final-reviewability-state.json` and confirm `status` is `proceed`, `outcome` is `marker_split`, and `full_diff.reviewability_status` is `warn`.
- [ ] Confirm the same JSON has `no_pr_assertions.gh_pr_create_invoked=false` and `no_pr_assertions.multi_pr_emission_invoked=false`, proving the backstop did not create PR side effects.

<a id="us-2"></a>
### User Story 2 - Emit Scoped PRs From Durable Markers (Priority: P2)

- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` and confirm it reports `85/85 passed`.
- [ ] Open `docs/ai/specs/.process/PRSG-013-pr-marker-plan.json` and confirm marker IDs are exactly `foundation`, `us1`, `us2`, and `us3` in review order.
- [ ] Confirm `us3.folded_polish_task_ids` contains T037 through T045, and no separate `polish` marker exists.

<a id="us-3"></a>
### User Story 3 - Verify Marker Planning And Emission Behavior (Priority: P3)

- [ ] Run `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` and confirm it reports `116/116 passed`.
- [ ] Open `docs/ai/specs/.process/PRSG-013-marker-emission-dry-run.json` and confirm `emission.mode=marker`, `emission.route=marker_split`, and `emission.slice_count=4`.
- [ ] Confirm `pr_create_commands` uses the stacked marker order: `foundation` based on `main`, `us1` based on `01-foundation`, `us2` based on `02-us1`, and `us3` based on `03-us2`.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Continue Through Reviewability Sizing (Priority: P1)](#us-1) | final backstop marker-aware proceed plus no PR side effects |
| [User Story 2 - Emit Scoped PRs From Durable Markers (Priority: P2)](#us-2) | durable marker plan with Foundation, user-story, fingerprint, and Polish-fold evidence |
| [User Story 3 - Verify Marker Planning And Emission Behavior (Priority: P3)](#us-3) | marker-aware emission dry-run with four scoped PR packets |


## Negative-Path Tests


- A reviewability sizing result is missing, malformed, or cannot be tied to the current feature.
- A post-task reviewability check exits nonzero while still emitting valid `status=block` JSON.
- Tasks contain user-story sections but one story exceeds the reviewability budget.
- A large story has no safe internal task-cluster boundary for subdivision, so the original story marker must continue with a structured warning.
- Tasks include Foundation but no meaningful Polish section, or Polish contains only cleanup items.
- Hard-atomic or release-sensitive hazards conflict with the default split-by-marker plan.
- Existing autopilot state contains marker data from an earlier run of the same feature and must be validated against current task, reviewability, and hazard-decision fingerprints.
- Final backstop evidence is size-blocked but the marker plan is missing, stale, malformed, or fingerprint-mismatched.

## Self-Review Findings

**Tests executed:** Deterministic validation ran in this session: targeted Layer 4, Layer 3 registration, Layer 1, and default suite. Final default result: `2574/2574 passed`.

**Edge cases:** Covered by malformed/stale/fingerprint-mismatched marker plans, non-size final blocks, no-safe-boundary marker planning, hazard collapse, placeholder packet rejection, marker order mismatch, and changed-file scope mismatch fixtures.

**Requirements matched:** `specs/prsg-013-reviewability-markers/tasks.md` is 45/45 complete, and the workflow evidence maps the implementation to `foundation`, `us1`, `us2`, and `us3` markers.

**Follow-up:** `bash tests/speckit-pro/run-all.sh --all` reached live Layer 7 and stalled without output; the deterministic default suite is the completion gate for this PR.

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

Revert the PR commit(s). This change is Bash/Markdown/JSON only and does not introduce data migrations.

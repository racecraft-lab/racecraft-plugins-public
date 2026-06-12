# What changed

# Why it matters

# Anything reviewers should know


## Summary

<!-- speckit-pro-editable:summary:start -->
Adds reviewer-ready split PR packet evidence for `us2`.
<!-- speckit-pro-editable:summary:end -->

Source: slice packet defines split PR identity and source boundary evidence.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Prepared `prsg-012-reviewer-ready-pr-packet-contract/03-us2` for review against `prsg-012-reviewer-ready-pr-packet-contract/02-us1`.
- Rendered scoped verification, declared files, traceability, and known-gap evidence before PR creation.
<!-- speckit-pro-editable:what_changed:end -->

Source: slice packet declared files and scoped verification define the reviewer body.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Reviewers can inspect the exact split scope and validation evidence before the PR is opened.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review the declared files and scoped verification evidence for this slice.
2. Confirm the base/head ordering matches the recorded stack order.
3. Check known gaps and rollback notes before approving.

## How To UAT

Run the scoped verification commands listed below, then confirm the full regression evidence remains current.

## Verification

- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single.md` (SCRIPT_UNIT, exit 0) — specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/us2/layer4.log
- `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` (SCRIPT_UNIT, exit 0) — specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/us2/layer4.log
- `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh` (SCRIPT_UNIT, exit 0) — specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/us2/layer4.log
- Full regression evidence: `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/full-regression.log`

Source: quickstart and scoped verification records define the validation evidence.

## Scope

- Declared files:
  - `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
  - `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
  - `speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`
- Traceability:
  - Traceability: FR-010 maps files speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh, speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh, speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md to evidence specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/full-regression.log
- Non-goals: this packet does not broaden the declared slice scope or replace full regression evidence.

## Known Gaps

No known gaps for this split packet.

## Slice summary

- Slice: `us2`
- PR row status: `pending`
- Head branch: `prsg-012-reviewer-ready-pr-packet-contract/03-us2`
- Base branch: `prsg-012-reviewer-ready-pr-packet-contract/02-us1`

## Review order

3 of 5

## Slice Scope

- `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`
- `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`
- `speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md`

## Slice Verification

- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single.md` (SCRIPT_UNIT, exit 0) — specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/us2/layer4.log
- `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` (SCRIPT_UNIT, exit 0) — specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/us2/layer4.log
- `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh` (SCRIPT_UNIT, exit 0) — specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/us2/layer4.log

## Traceability

- FR-010: files speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh, speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh, speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md; evidence specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/full-regression.log

## Restack or rollback

Style B incremental stack: first slice targets the integration base and later slices target the previous slice branch.

## Known gaps

- None recorded.

## Full regression evidence

- `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/full-regression.log`

<details>
<summary>Reviewer checklist &amp; scope details</summary>

**Size:** 0 reviewable lines across 96 files (0 production). Budget: block.
**Primary surfaces:** API, docs/process, other, scheduler/runtime, schema/migration, seed/config.

**Review in this order:**
1. The spec and plan under `specs/prsg-012-reviewer-ready-pr-packet-contract`.
2. The highest-risk production files.
3. Verification evidence and any known gaps.

**Verification:**
- [ ] Build / Typecheck / Lint / Tests pass (or N/A for this repo)
- [ ] Visual review completed or N/A

**Rollback:** `git revert <SHA>` unless noted otherwise.
</details>

## UAT Runbook

# UAT Runbook: prsg-012-reviewer-ready-pr-packet-contract

| Field | Value |
|-------|-------|
| Spec | prsg-012-reviewer-ready-pr-packet-contract |
| Branch | prsg-012-reviewer-ready-pr-packet-contract |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-12T19:36:21Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | _not available for this project_ |
| TYPECHECK | _not available for this project_ |
| LINT | _not available for this project_ |
| LINT_FIX | _not available for this project_ |
| UNIT_TEST | `bash tests/speckit-pro/run-all.sh --layer 4` |
| INTEGRATION_TEST | `bash tests/speckit-pro/run-all.sh` |
| SINGLE_FILE_INTEGRATION | `bash tests/speckit-pro/run-all.sh --layer 1` |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Specific conventional PR titles (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Structured reviewer body (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Pre-create validation block (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-4"></a>
### User Story 4 - Safe prose refinement (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Specific conventional PR titles (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Structured reviewer body (Priority: P1)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Pre-create validation block (Priority: P1)](#us-3) | see the Per-Story Acceptance Tests block above |
| [User Story 4 - Safe prose refinement (Priority: P2)](#us-4) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- A single-PR packet and a split-PR packet require different titles, UAT details, and verification evidence for the same feature.
- A host PR template includes legacy headings, template comments, placeholder variables, or example text in the final rendered body.
- Manual UAT is not applicable for a packet, but the reviewer still needs explicit How To UAT and `## UAT Runbook` content explaining that no manual UAT path is required.
- Known Gaps has no open gaps; the body must still say so explicitly rather than omit the section.
- A source marker appears only inside a code fence, HTML comment, generated fixture, or non-rendered area.
- One split packet fails validation while other split packets pass.
- The packet file path is missing, unreadable, points to a directory, contains invalid JSON, or fails the packet schema before a `packet_id` can be trusted.
- A split-PR run has already opened one or more earlier slice PRs when a later packet fails validation.

## Self-Review Findings

1. **Tests executed?** Applicable verification ran in this resumed session. `bash tests/speckit-pro/run-all.sh --layer 1` passed 978/978, `bash tests/speckit-pro/run-all.sh --layer 4` passed 1622/1622, and `bash tests/speckit-pro/run-all.sh` passed 2790/2790. The project command detector reports BUILD, TYPECHECK, LINT, UNIT_TEST, and INTEGRATION_TEST as `N/A` for this shell-only plugin repository, so no separate build/typecheck/lint commands were inferred as passing.
2. **Edge cases?** Acceptance coverage is present for single and split packet title generation, stale/title-token rejection, canonical body order, UAT compatibility, missing evidence, banned labels, input-error packet paths, stale validation, split partial-failure resume, safe prose edits, protected evidence edits, and host-template coexistence. Evidence includes `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh:385`, `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh:390`, `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh:530`, `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh:346`, `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh:1141`, and `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh:1445`.
3. **Requirements matched?** FR-001 through FR-004A map to checked title and PR-create tasks T010-T017; FR-005 through FR-015F map to checked validator, workflow-event, stale-result, and split-resume tasks T018-T034; FR-016 through FR-018 map to checked safe-edit and protected-fingerprint tasks T035-T041; FR-019 maps to checked mirrored guidance/parity tasks T042-T053. Verification tasks T054-T056 are checked and passed.
4. **Follow-up?** No `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]` markers were found in `spec.md`, `plan.md`, or `tasks.md`, and branch commit subjects do not contain those markers. No self-review follow-up item is required.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

<!-- speckit-pro-review-packet-source
template: speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md
feature_dir: specs/prsg-012-reviewer-ready-pr-packet-contract
diff_range: 3118e81162104bfd081d01755c00c205a8eab061...HEAD
reviewability: {"mode":"diff","status":"block","pass":false,"reviewable_loc":0,"production_files":0,"total_files":96,"primary_surface_count":6,"primary_surfaces":["API","docs/process","other","scheduler/runtime","schema/migration","seed/config"],"greenfield":false,"thresholds":{"warn":{"reviewable_loc":400,"production_files":6,"total_files":15,"primary_surfaces":1},"block":{"reviewable_loc":800,"production_files":8,"total_files":25,"primary_surfaces":1}},"exception_honored":false,"exception_class":null,"exceptions":{"accepted":[],"rejected":[]},"warnings":["total files 96 exceeds warn threshold 15","primary surfaces 6 exceeds warn threshold 1"],"blockers":["total files 96 exceeds block threshold 25"]}
-->

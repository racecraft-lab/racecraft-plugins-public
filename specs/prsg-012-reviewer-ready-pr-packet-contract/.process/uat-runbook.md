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

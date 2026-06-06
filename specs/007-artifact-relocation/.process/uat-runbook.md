# UAT Runbook: 007-artifact-relocation

| Field | Value |
|-------|-------|
| Spec | 007-artifact-relocation |
| Branch | 007-artifact-relocation |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-05T23:26:39Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| TYPECHECK | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| LINT | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| LINT_FIX | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| UNIT_TEST | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| INTEGRATION_TEST | <unknown — autopilot did not pass PROJECT_COMMANDS> |
| SINGLE_FILE_INTEGRATION | <unknown — autopilot did not pass PROJECT_COMMANDS> |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Tier and redirect speckit-pro-authored exhaust (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Collapse, align the gate, and lint the collapse rule (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Tier and redirect speckit-pro-authored exhaust (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Collapse, align the gate, and lint the collapse rule (Priority: P2)](#us-2) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- **A `.process/` directory does not yet exist when exhaust is first written.** The redirect must create the `.process/` directory as needed so the first design-concept doc, workflow file, or UAT runbook of a new spec lands in the right place rather than failing or falling back to the old location.
- **The collapse rule is present in the plugin repo but absent from a consuming project.** Because the platform reads each repository's own collapse configuration, a plugin-only rule would collapse only the plugin's own PRs. The consuming-project ensure-step closes this gap; if it is skipped, the consuming project's new-spec exhaust stays visible (a degraded but non-broken state).
- **The consumer `.gitattributes` write is interrupted partway.** The ensure-step's edit to the consumer `.gitattributes` MUST be safe under interruption: an interrupted run MUST NOT leave the file truncated, half-written, or otherwise corrupted (upholding FR-009 clause (c)). A subsequent re-run MUST be able to complete the edit idempotently and arrive at the same single-rule end state. Corruption also includes silently concatenating the new rule onto a pre-existing final line that lacks a trailing newline, so the write MUST normalize the trailing newline before appending. (The concrete safe-write mechanism was resolved during Checklist consensus — write to a same-directory temp file then atomic rename, with a fixed-string whole-line presence guard — and is pinned in plan.md; the requirement here remains the no-partial-file, no-concatenation outcome.)
- **The collapse rule and the gate's exclusion list disagree.** The two are intentionally maintained in two places (the repository-root collapse configuration and the gate's own exclusion logic). The lint exists specifically to catch drift between them so a reviewer is never shown something the gate counts, or vice versa.
- **A PR-body section references a relocated file.** Relocating the UAT runbook must not break the PR body's rendering of its UAT section; the reference is repointed to the new `.process/` location so the section still renders.
- **An existing (legacy) spec directory is present.** This feature is new-specs-only and must not touch or migrate any existing `specs/<NNN>/` directory; legacy relocation is owned by a separate, later spec.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

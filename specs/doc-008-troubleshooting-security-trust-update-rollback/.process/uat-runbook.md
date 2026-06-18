# UAT Runbook: doc-008-troubleshooting-security-trust-update-rollback

| Field | Value |
|-------|-------|
| Spec | doc-008-troubleshooting-security-trust-update-rollback |
| Branch | doc-008-troubleshooting-security-trust-update-rollback |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-18T04:15:25Z |



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
### User Story 1 - Diagnose A Failure Symptom (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Evaluate Security And Trust Boundaries (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Recover From Stale Or Incorrect Installs (Priority: P3)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Diagnose A Failure Symptom (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Evaluate Security And Trust Boundaries (Priority: P2)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Recover From Stale Or Incorrect Installs (Priority: P3)](#us-3) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- A symptom maps to different Claude Code and Codex diagnostics; the page must keep one shared concept row when practical and use platform-specific diagnostic text inside the row.
- A failure class cannot be represented cleanly as a shared row; the page may use a short platform-specific subsection, but it must not duplicate common source, payload, cache, or trust explanations.
- A user has edited an installed plugin cache or copied payload manually; the recovery guidance must treat that as drift and route to reinstall, refresh, or regenerate from source rather than preserving the manual edit.
- A marketplace listing is current but generated payload or custom-agent registration is stale; the guidance must separate marketplace source, generated payload, installed cache, and copied custom-agent files.
- A managed policy blocks plugin install, marketplace source, hooks, MCP, network, or permissions; the docs must identify managed policy as a possible cause and avoid telling the user to bypass organization controls.
- A platform vendor changes command names, settings locations, sandbox behavior, or plugin behavior; implementation must verify current official docs before shipping platform-behavior claims.
- A Racecraft-specific statement is not covered by DOC-007 generated reference pages; implementation must cite the checked-in source file directly or omit the claim.
- Browser-rendered docs must not run a local doctor command, local filesystem probe, permission grant or request, plugin/workflow action, or automatic repair.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

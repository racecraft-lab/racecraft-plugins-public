# UAT Runbook: doc-006-safe-interactive-selector-and-validation-aids

| Field | Value |
|-------|-------|
| Spec | doc-006-safe-interactive-selector-and-validation-aids |
| Branch | doc-006-safe-interactive-selector-and-validation-aids |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-17T03:47:40Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | `pnpm --dir docs-site validate` |
| TYPECHECK | Covered by docs-site validation |
| LINT | N/A |
| LINT_FIX | N/A |
| UNIT_TEST | `node docs-site/scripts/validate-doc006-safe-aids.mjs` |
| INTEGRATION_TEST | `pnpm --dir docs-site validate:links` |
| SINGLE_FILE_INTEGRATION | `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/doc-006-safe-interactive-selector-and-validation-aids` |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Choose the correct install path (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Inspect repository metadata consistency (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Review safe first-run checkpoints (Priority: P3)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Choose the correct install path (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Inspect repository metadata consistency (Priority: P2)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Review safe first-run checkpoints (Priority: P3)](#us-3) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- A platform path has no additional install scope choices; the selector still presents a complete path without implying unsupported scopes.
- A stale enhanced selector state, unavailable selector metadata, or unsupported platform/scope combination is encountered; the page explains the unsupported or ambiguous state in text, keeps supported static path guidance available, and routes users to safe install or troubleshooting handoffs without claiming a local diagnostic was run.
- Repository metadata is temporarily unavailable during content generation; the page falls back to explicit unavailable-state content rather than stale generated output.
- Source and generated payload versions differ; the checker reports mismatch and routes users to lightweight troubleshooting handoffs without attempting repair.
- A user opens the page without browser scripting; all selector paths, checker comparison values, diagram nodes, and checklist items remain accessible as static content.
- A user tries to infer that the browser can run commands; the page labels commands as copyable guidance only and never presents them as executable browser actions.
- Existing DOC-008 troubleshooting ownership is not ready; mismatch handoffs remain lightweight and avoid replacing the future full troubleshooting matrix.

## Self-Review Findings

No unresolved self-review findings were recorded. Post-implementation verification found no critical, significant, or minor findings.

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

Revert the implementation PR or the DOC-006 implementation commits. No data migration or user configuration rollback is required.

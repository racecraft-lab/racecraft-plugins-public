# UAT Runbook: doc-001-static-docs-framework-and-ia-spike

| Field | Value |
|-------|-------|
| Spec | doc-001-static-docs-framework-and-ia-spike |
| Branch | doc-001-static-docs-framework-and-ia-spike |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-12T21:47:50Z |



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
### User Story 1 - Review the framework recommendation (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Handoff IA and commands to DOC-002 (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Confirm research-only scope (Priority: P3)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Review the framework recommendation (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Handoff IA and commands to DOC-002 (Priority: P2)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Confirm research-only scope (Priority: P3)](#us-3) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- If live framework or platform source documentation is temporarily unavailable, the report must record the gap, avoid relying on stale unsupported claims, and use the best available official or primary source evidence.
- If every candidate has a hard blocker for GitHub Pages hosting from this repository, the report must record the blocker and recommend the least risky fallback instead of forcing a preferred framework.
- If a candidate supports an evaluation criterion only through third-party plugins or paid services, the report must distinguish that support from built-in or first-party support.
- If source evidence conflicts across framework or platform docs, the report must prefer the most current official source and note the conflict.
- If an IA route lacks enough source evidence or a measurable success criterion, the route must be revised or omitted from the top-level skeleton.

## Self-Review Findings

- The report satisfies the spike: Astro/Starlight is the default recommendation, Docusaurus/MDX is retained only as a deferred fallback, alternatives have concrete rationale, DOC-002 gets command handoff, and the IA skeleton covers the required routes.
- DOC-001 stayed research-only: forbidden-surface scans found 0 package, lockfile, site config, CI, generated payload, README migration, or plugin behavior changes.
- Verification passed for this docs/process change: Layer 1 and default deterministic suites passed before merge, post-merge verification passed `2915/2915`, G7 passed, and final reviewability proceeded with marker evidence.
- Remaining follow-up is explicit: DOC-002 owns scaffolding/config refresh and DOC-010 owns search, accessibility, responsive, deep-link, and docs validation hardening.

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

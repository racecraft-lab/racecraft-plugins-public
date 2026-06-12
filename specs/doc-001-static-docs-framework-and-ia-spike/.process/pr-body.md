# What changed
This PR adds the planning and research foundation for a future Racecraft documentation website. It recommends Docusaurus with MDX as the default docs stack, records why the other options were not selected, and gives the next implementation PR a route-level site map plus command handoff.

# Why it matters
The repo needs a public docs site, but creating package files and hosting config before choosing the stack would make review harder. This keeps the decision research-only so the next PR can create the site shell with a clear framework, hosting path, and content structure.

# Anything reviewers should know
- This does not create a docs-site package, site config, workflow, README migration, or plugin behavior change.
- The final size check is a size-only block on total file count, so marker evidence is included for review ordering.
- The next implementation PR should refresh Docusaurus and GitHub Pages docs again before scaffolding.

<!-- The "Reviewer checklist & scope details" block and the "UAT Runbook" section
     are appended automatically by generate-pr-body.sh. Do not add them by hand. -->

<details>
<summary>Reviewer checklist &amp; scope details</summary>

**Size:** 0 reviewable lines across 30 files (0 production). Budget: block.
**Primary surfaces:** docs/process, scheduler/runtime, seed/config.

**Review in this order:**
1. The spec and plan under `specs/doc-001-static-docs-framework-and-ia-spike`.
2. The highest-risk production files.
3. Verification evidence and any known gaps.

**Verification:**
- [ ] Build / Typecheck / Lint / Tests pass (or N/A for this repo)
- [ ] Visual review completed or N/A

**Rollback:** `git revert <SHA>` unless noted otherwise.
</details>

## UAT Runbook

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

- The report satisfies the spike: Docusaurus/MDX is the default recommendation, alternatives have concrete rationale, DOC-002 gets command handoff, and the IA skeleton covers the required routes.
- DOC-001 stayed research-only: forbidden-surface scans found 0 package, lockfile, site config, CI, generated payload, README migration, or plugin behavior changes.
- Verification passed for this docs/process change: Layer 1 passed `978/978`, the default deterministic suite passed `2587/2587`, G7 passed, and final reviewability proceeded with marker evidence.
- Remaining follow-up is explicit: DOC-002 owns scaffolding/config refresh and DOC-010 owns search, accessibility, responsive, deep-link, and docs validation hardening.

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

<!-- speckit-pro-review-packet-source
template: /Users/fredrickgabelmann/.codex/worktrees/4440/racecraft-plugins-public/.worktrees/001-static-docs-framework-and-ia-spike/speckit-pro/skills/speckit-autopilot/templates/pr-description-template.md
feature_dir: specs/doc-001-static-docs-framework-and-ia-spike
diff_range: origin/main...HEAD
reviewability: {"mode":"diff","status":"block","pass":false,"reviewable_loc":0,"production_files":0,"total_files":30,"primary_surface_count":3,"primary_surfaces":["docs/process","scheduler/runtime","seed/config"],"greenfield":false,"thresholds":{"warn":{"reviewable_loc":400,"production_files":6,"total_files":15,"primary_surfaces":1},"block":{"reviewable_loc":800,"production_files":8,"total_files":25,"primary_surfaces":1}},"exception_honored":false,"exception_class":null,"exceptions":{"accepted":[],"rejected":[]},"warnings":["total files 30 exceeds warn threshold 15","primary surfaces 3 exceeds warn threshold 1"],"blockers":["total files 30 exceeds block threshold 25"]}
-->

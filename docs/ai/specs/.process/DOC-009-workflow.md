# SpecKit Workflow: DOC-009 - Maintainer and contributor release workflow

**Template Version**: 1.0.0
**Created**: 2026-06-18
**Purpose**: Reusable workflow guide for executing DOC-009 with SpecKit.

---

## How to Use This Template

1. Use this file as the phase-by-phase prompt source for DOC-009.
2. Run each SpecKit phase from branch `doc-009-maintainer-contributor-release-workflow`.
3. Keep the Design Concept open while running every phase:

   ```text
   docs/ai/specs/.process/DOC-009-design-concept.md
   ```

4. After each phase, stop for human review before continuing.
5. Do not run implementation from `main`.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec DOC-009`. The full Q&A log, Goals, Non-goals, Open
Questions, and acceptance-criteria mapping live at:

```text
docs/ai/specs/.process/DOC-009-design-concept.md
```

Re-read it before each phase. The Design Concept is the source of truth for
scope decisions captured during setup.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created `specs/doc-009-maintainer-contributor-release-workflow/spec.md`; G1 passed with zero clarification markers |
| Clarify | `/speckit-clarify` | Complete | Resolved page structure, source-fact boundaries, validation lanes, and DOC-010 handoff |
| Plan | `/speckit-plan` | Complete | Created `plan.md`, `research.md`, and `quickstart.md`; G3 passed with projected production LOC 0 |
| Checklist | `/speckit-checklist` | Complete | Four domain checklists completed; G4 passed with zero gap markers |
| Tasks | `/speckit-tasks` | Complete | Generated 23 story-sliced tasks; G5 passed |
| Analyze | `/speckit-analyze` | Complete | G6 passed with zero findings |
| Implement | `/speckit-implement` | Complete | Implemented docs-only route update; G7 validation passed |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories and AC-9.1 through AC-9.6 are represented with no unresolved clarification markers |
| G2 | After Clarify | Page shape, command blocks, docs-only behavior, and DOC-010 handoff are decided |
| G3 | After Plan | Plan stays documentation-only unless source evidence proves a narrow supporting change is required |
| G4 | After Checklist | All gaps are resolved or explicitly scoped out |
| G5 | After Tasks | Tasks are ordered by independently reviewable user story slices |
| G6 | After Analyze | No critical consistency issues remain |
| G7 | After Implementation | Docs-site validation and repository shell checks pass or any skipped check is justified |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with `.specify/memory/constitution.md`
and repository guidance in `AGENTS.md` and `CLAUDE.md`.

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Surface assumptions before editing | State whether DOC-009 is docs-only and which files are expected to change | Chat/update before edits |
| Simplest change that solves it | Deepen the existing `/contribute-and-release` route before adding new pages | Plan review |
| Surgical edits | Avoid changing CI, release scripts, manifests, or generated payloads unless required by source truth | `git diff --stat` and human review |
| Verifiable success criteria | Tie every docs claim to a command or checked-in source file | Source links plus validation commands |
| Public-readable PRs | Use Conventional Commit titles and plain-English PR bodies | PR title/body review |

**Constitution Check:** Verified during autopilot preflight and Specify; DOC-009 remains docs-only and source-backed.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| Spec ID | DOC-009 |
| Name | Maintainer and contributor release workflow |
| Branch | `doc-009-maintainer-contributor-release-workflow` |
| Dependencies | DOC-007 completed in PR #208 |
| Enables | DOC-010 |
| Priority | P1 |
| Roadmap | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| Target route | `docs-site/src/content/docs/contribute-and-release.md` |
| Design concept | `docs/ai/specs/.process/DOC-009-design-concept.md` |

### Success Criteria Summary

- AC-9.1: List required checks for docs-only, plugin source, dist payload,
  marketplace, and release automation changes.
- AC-9.2: Explain `bash scripts/build-plugin-payloads.sh`,
  `bash scripts/sync-marketplace-versions.sh`, and
  `bash tests/speckit-pro/run-all.sh`.
- AC-9.3: State which changes should or should not manually edit version fields.
- AC-9.4: Cover source/dist parity, Claude/Codex marketplace parity, manifest
  version consistency, and generated payload validation.
- AC-9.5: Include Conventional Commit and public-readable PR title/body
  expectations.
- AC-9.6: Explain docs-only CI behavior and add a future docs-site CI requirement
  handoff to DOC-010.

---

## Phase 1: Specify

**When to run:** At the start of the DOC-009 specification. Focus on what the
docs page must teach and why, not the final implementation mechanics.

### Specify Prompt

```bash
/speckit-specify

## Feature: Maintainer and contributor release workflow

### Problem Statement
Maintainers and contributors need one source-backed page that explains how to
move from source edits to release-ready PRs without confusing authoring source,
generated payloads, marketplace registries, version fields, docs-site files,
CI behavior, release-please, and PR conventions.

### Users
- Maintainers preparing release-ready docs or plugin changes.
- Contributors preparing a PR that maintainers can review without reconstructing
  the repo's release process.

### User Stories
- As a contributor, I can identify whether my change is docs-only, plugin source,
  generated payload, marketplace, or release automation work and see the checks
  required for that path.
- As a maintainer, I can complete a release-readiness checklist that covers
  source/dist parity, Claude/Codex marketplace parity, manifest version
  consistency, generated payload validation, full deterministic tests, and
  docs-site validation when relevant.
- As a reviewer, I can verify that a PR title/body follows Conventional Commit
  and public-readable guidance and includes the right validation evidence.
- As a docs maintainer, I can see current docs-only CI behavior and the future
  DOC-010 handoff for docs-site CI hardening.

### Required Behavior
- Deepen `docs-site/src/content/docs/contribute-and-release.md`, which already
  exists as the DOC-002 shell for `/contribute-and-release`.
- Use the Design Concept at
  `docs/ai/specs/.process/DOC-009-design-concept.md` for scope decisions.
- Use source facts from `AGENTS.md`, `CLAUDE.md`, `.github/workflows/pr-checks.yml`,
  `.github/workflows/release.yml`, `scripts/build-plugin-payloads.sh`,
  `scripts/sync-marketplace-versions.sh`, `tests/speckit-pro/run-all.sh`, and
  `docs-site/package.json`.
- Explain full-playbook flow inline, but link to deeper repository guidance
  instead of duplicating all internals.
- Treat `bash tests/speckit-pro/run-all.sh` as the release-readiness test
  expectation. Add `pnpm --dir docs-site validate` when docs-site files change.
- Explain release automation as observable maintainer behavior, not as hidden
  implementation internals.

### Constraints
- DOC-009 is documentation work. Do not change CI, release automation behavior,
  scripts, manifests, generated payloads, or version fields unless a source
  citation is broken and the narrow fix is approved.
- Keep generated reference pages generated. If they drift, use their existing
  generator contract rather than hand-editing generated output.
- Current docs-site CI hardening belongs to DOC-010; DOC-009 must state the
  handoff, not implement it.

### Out of Scope
- Changing release automation.
- Duplicating all `CLAUDE.md` internals.
- Adding DOC-010 search, accessibility, deep-link, responsive, or docs-CI
  hardening.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 15 requirements covering AC-9.1 through AC-9.6 |
| User Stories | 4 stories: contributor path, maintainer readiness, reviewer verification, docs-CI handoff |
| Acceptance Criteria | Six PRD criteria plus 8 acceptance scenarios |
| G1 Gate | Passed: `spec.md` exists with 0 `[NEEDS CLARIFICATION]` markers |

### Files Generated

- `specs/doc-009-maintainer-contributor-release-workflow/spec.md` - created

### SpecKit Traceability Markers

Use `[US1]`, `[US2]`, `[US3]`, `[US4]`, `[FR-001]` style markers in `spec.md`.
Map each requirement back to AC-9.1 through AC-9.6 and cite the Design Concept.

---

## Phase 2: Clarify

**When to run:** After Specify, before Plan. Focus only on areas that could
produce different docs or validation tasks.

### Clarify Prompts

#### Session 1: Page Structure

```bash
/speckit-clarify

Focus on DOC-009 page structure for `docs-site/src/content/docs/contribute-and-release.md`.
Resolve whether command examples should be grouped by change type or consolidated
into one release-readiness block. Use the Design Concept open questions.
```

#### Session 2: Source-Fact Boundaries

```bash
/speckit-clarify

Focus on source-fact accuracy. Decide which statements must cite `AGENTS.md`,
`CLAUDE.md`, `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`,
`scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`,
`tests/speckit-pro/run-all.sh`, and `docs-site/package.json`.
```

#### Session 3: Validation and DOC-010 Handoff

```bash
/speckit-clarify

Focus on validation boundaries. Decide when DOC-009 requires
`pnpm --dir docs-site validate`, when `bash tests/speckit-pro/run-all.sh` is the
release-readiness check, and exactly how to state the future DOC-010 docs-site CI
handoff without promising current CI behavior that does not exist.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Page structure | 4 questions | Consolidated release-readiness command block, sparse generated-reference links, docs-site-only validation trigger, and classification-first page order |
| 2 | Source facts | 5 questions | Primary-source citation rules, docs-only PR Checks wording, caveated release-dispatch wording, dual-manifest version hierarchy, and docs-site validation source boundaries |
| 3 | Validation and DOC-010 | 5 questions | Docs-site validation trigger, reference-check preflight, release-readiness suite expectation, mixed-change validation lanes, and DOC-010 CI hardening handoff |

---

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Release-please PR workflow-event wording | [codebase, domain, security] | 1 | 3/3 | Use observable release workflow dispatch wording and caveat any `GITHUB_TOKEN` explanation | codebase-analyst, domain-researcher, spec-context-analyst |
| 2 | Clarify | Version-field source hierarchy | [codebase, spec] | 1 | both-agree | Release-please owns both source platform manifest versions; dist is generated; marketplace versions sync from platform manifests | codebase-analyst, spec-context-analyst |

## Phase 3: Plan

**When to run:** After spec is finalized. Generates the implementation blueprint.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs site: Astro 6.4.6, Starlight 0.40.0, JavaScript ESM on Node.
- Package manager: pnpm 10.25.0 inside `docs-site/`.
- Content: checked-in Markdown and MDX under `docs-site/src/content/docs/`.
- Generated reference pages: `docs-site/scripts/generate-reference-pages.mjs`.
- Repository validation: Bash tests under `tests/speckit-pro/`.
- Release automation: GitHub Actions, release-please, root Bash scripts.
- Database/storage: none.

## Constraints
- Target the existing route `docs-site/src/content/docs/contribute-and-release.md`.
- Keep DOC-009 docs-only unless source evidence proves a narrow supporting fix
  is necessary and approved.
- Do not manually edit generated payloads or marketplace versions as part of the
  DOC-009 implementation.
- Preserve the generated reference-page contract; use `pnpm --dir docs-site reference:check`
  and `pnpm --dir docs-site reference:generate` only as the existing docs-site
  workflow requires.
- Reflect the Grill Me decisions from
  `docs/ai/specs/.process/DOC-009-design-concept.md`: balanced audience, full
  playbook, docs and plugins, guide plus links, full suite always, observable
  automation handoff, single route, separate docs-only path, DOC-010 CI handoff.

## Architecture Notes
- Treat `/contribute-and-release` as a how-to/reference hybrid.
- Use the generated reference pages for deep file inventories:
  `/reference/source-vs-dist/`, `/reference/scripts/`, `/reference/tests/`,
  and `/reference/manifests/`.
- The page should be scannable: role split, change-type matrix, contributor
  flow, maintainer flow, version guidance, release automation, checklist, and
  DOC-010 handoff.
- Validation should include `pnpm --dir docs-site validate` and
  `bash tests/speckit-pro/run-all.sh` before release readiness.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Docs-only implementation plan with reviewability budget, declared file operations, and source-backed constraints |
| `research.md` | Complete | Captures source-fact decisions for CI, release automation, version ownership, generated references, and validation |
| `data-model.md` | Not needed | No data entities, storage, API behavior, or runtime contracts in DOC-009 |
| `contracts/` | Not needed | Documentation-only route update; no API or schema contract changes |
| `quickstart.md` | Complete | Captures implementation steps, validation commands, AC review checks, and rollback |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Run focused checks before task generation.

### Recommended Domains

| Signal | Recommended Domain |
|---|---|
| Existing docs route plus generated reference links | documentation-ia |
| Release scripts, CI workflows, version fields, generated payloads | release-process-accuracy |
| Docs-only and plugin-changing PR check behavior | ci-validation |
| Maintainer/contributor task flow and checklist usability | reviewer-usability |

### Checklist Prompts

#### 1. documentation-ia Checklist

```bash
/speckit-checklist documentation-ia

Focus on DOC-009:
- The existing `/contribute-and-release` route is deepened instead of replaced.
- The page stays a how-to/reference hybrid for maintainers and contributors.
- The page links to generated references rather than duplicating generated
  inventories.
- The DOC-010 handoff is visible but not over-specified.
```

#### 2. release-process-accuracy Checklist

```bash
/speckit-checklist release-process-accuracy

Focus on DOC-009:
- Every claim about payload rebuilds, marketplace sync, version fields,
  release-please, PR checks, and docs-only behavior is traceable to checked-in
  files.
- `build-plugin-payloads.sh`, `sync-marketplace-versions.sh`, and
  `tests/speckit-pro/run-all.sh` are explained accurately.
- The docs state when generated payloads and marketplace files should not be
  hand-edited.
```

#### 3. ci-validation Checklist

```bash
/speckit-checklist ci-validation

Focus on DOC-009:
- The page correctly distinguishes docs-only PR behavior from plugin-changing
  PR behavior in `.github/workflows/pr-checks.yml`.
- The page treats `bash tests/speckit-pro/run-all.sh` as the release-readiness
  expectation.
- The page adds `pnpm --dir docs-site validate` for docs-site changes and hands
  future docs-site CI enforcement to DOC-010.
```

#### 4. reviewer-usability Checklist

```bash
/speckit-checklist reviewer-usability

Focus on DOC-009:
- A contributor can prepare a PR body with relevant validation evidence.
- A maintainer can complete the release-readiness checklist without reading all
  of `CLAUDE.md`.
- PR title/body guidance is public-readable and Conventional Commit compatible.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| documentation-ia | 11 | 0 | AC-9.1, AC-9.6 |
| release-process-accuracy | 10 | 0 | AC-9.2, AC-9.3, AC-9.4 |
| ci-validation | 9 | 0 | AC-9.1, AC-9.6 |
| reviewer-usability | 9 | 0 | AC-9.5 |

Consensus escalation was not required for any checklist domain.

---

## Phase 5: Tasks

**When to run:** After checklists complete and all gaps are resolved.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Use small, reviewable tasks grouped by user story.
- Reference `spec.md`, `plan.md`, and
  `docs/ai/specs/.process/DOC-009-design-concept.md`.
- Bound tasks with the Design Concept non-goals: no CI/release behavior changes,
  no generated payload edits, no marketplace version changes, no DOC-010
  implementation.
- Use Q&A context for ordering: single route first, source-fact map second,
  contributor and maintainer flows third, checklist and validation last.
- Mark independent docs-source reading or section edits with [P] only when they
  do not touch the same page section.

## Suggested Implementation Phases
1. Source-fact audit: verify current route shell, reference pages, release
   scripts, CI workflows, release workflow, tests, and docs-site scripts.
2. Page structure: replace the DOC-002 shell with the DOC-009 full playbook
   outline in `docs-site/src/content/docs/contribute-and-release.md`.
3. Contributor flow: add change-type decision matrix, source/dist guidance,
   Conventional Commit guidance, and public-readable PR body expectations.
4. Maintainer flow: add payload rebuild, marketplace sync, release-please,
   version fields, CI behavior, and release-readiness checklist.
5. Validation and polish: run docs-site validation and repository shell tests,
   then update tasks and PR packet evidence.

## Validation Commands
- `pnpm --dir docs-site reference:check`
- `pnpm --dir docs-site validate`
- `bash tests/speckit-pro/run-all.sh`
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 23 |
| Phases | 6: setup/source audit, US1, US2, US3, US4, polish/validation |
| Parallel Opportunities | T001-T003 read-only source audit, T018 reference check after page edits; US3 and US4 drafts can proceed in parallel after shared terminology |
| User Stories Covered | US1, US2, US3, US4 |

---

## Atomicity Route

After the Tasks phase / gate G5, run the read-only atomicity classifier and
record its decision here.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true` or `false` |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Warnings | None | Release-safety warnings |

Run:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-009-maintainer-contributor-release-workflow
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on DOC-009:
1. Cross-check `spec.md`, `plan.md`, `tasks.md`, and
   `docs/ai/specs/.process/DOC-009-design-concept.md`.
2. Verify each AC-9.1 through AC-9.6 requirement has tasks and validation.
3. Flag any drift from the Grill Me decisions:
   - balanced maintainer/contributor audience
   - full playbook
   - docs and plugin scope
   - guide plus links
   - full deterministic suite expectation
   - observable automation handoff
   - single route
   - separate docs-only path
   - DOC-010 CI handoff
4. Flag any task that changes CI, release automation, manifests, generated
   payloads, scripts, or version fields without explicit justification.
5. Verify task file paths match the actual repo structure and generated
   reference-page contract.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| CRITICAL | Blocks implementation or violates scope | Must fix before G6 |
| HIGH | Significant gap in release-process accuracy | Should fix before implementation |
| MEDIUM | Useful improvement or wording ambiguity | Review and decide |
| LOW | Minor consistency issue | Note or fix opportunistically |

### Analyze Results

| Check | Result | Evidence |
|-------|--------|----------|
| Artifact coverage | Pass | `spec.md`, `plan.md`, `tasks.md`, Design Concept, and checklists are present and non-empty |
| AC-9.1 through AC-9.6 task coverage | Pass | `tasks.md` Coverage Matrix maps FR-001 through FR-015, including all DOC-009 acceptance criteria |
| Grill Me decision drift | Pass | Tasks preserve balanced audience, full playbook, docs/plugins scope, guide plus links, full suite expectation, observable automation handoff, single route, separate docs-only path, and DOC-010 handoff |
| Scope boundary | Pass | No task changes CI, release automation, scripts, manifests, generated payloads, marketplace registries, or version fields |
| File-path accuracy | Pass | Tasks target the existing route, workflow/state artifacts, generated reference contract, and checked-in primary source files |

No CRITICAL, HIGH, MEDIUM, or LOW findings remained after the Analyze pass.
Consensus escalation was not required for Analyze.

### Pre-Implement Confidence

📊 Confidence: 0.96

- Task understanding: 0.95
- Approach clarity: 0.95
- Requirements alignment: 0.95
- Risk assessment: 1.00
- Completeness: 0.95

Confidence gate result: passed in advisory mode with threshold 0.90; recommended action `proceed`.

---

## Phase 7: Implement

**When to run:** After tasks are generated and analyzed.

### Implement Prompt

```bash
/speckit-implement

## Approach
Implement DOC-009 as documentation work on
`doc-009-maintainer-contributor-release-workflow`.

Before editing:
1. Confirm branch with `git rev-parse --abbrev-ref HEAD`.
2. Re-read `docs/ai/specs/.process/DOC-009-design-concept.md`.
3. Re-read source files for any command/workflow claim being documented.

Implementation notes:
- Target `docs-site/src/content/docs/contribute-and-release.md`.
- Prefer links to generated references for inventories:
  `/reference/source-vs-dist/`, `/reference/scripts/`, `/reference/tests/`,
  `/reference/manifests/`.
- Do not hand-edit generated payloads, marketplaces, release workflows, or
  generated reference pages unless a task explicitly authorizes a narrow fix.
- Keep PR guidance public-readable and Conventional Commit compatible.
- Include current docs-only CI behavior and DOC-010 future CI handoff.

Verification:
- `pnpm --dir docs-site reference:check`
- `pnpm --dir docs-site validate`
- `bash tests/speckit-pro/run-all.sh`
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Source-fact audit | T001-T004 | Yes | Rechecked existing route shell, generated reference contract, release/validation source files, and docs-only reviewability boundary. |
| Page structure | T005-T008 | Yes | Replaced the DOC-002 shell with DOC-009 purpose, source-of-truth map, change-type matrix, and source-vs-generated guidance. |
| Contributor flow | T014-T015 | Yes | Added smallest-source-surface guidance, Conventional Commit title expectations, public-readable PR body guidance, and reviewer evidence expectations. |
| Maintainer flow | T009-T013 | Yes | Added release-readiness command block, payload rebuild and marketplace sync guidance, version-field ownership, release automation flow, and final checklist. |
| Validation and polish | T016-T023 | Yes | Added current PR Checks behavior and DOC-010 handoff, then completed validation, traceability review, tasks, and PR packet evidence. |

### Implementation Evidence

| Check | Result | Evidence |
|-------|--------|----------|
| Reviewability boundary | Pass | Only `docs-site/src/content/docs/contribute-and-release.md` changes implementation content; no CI, release automation, script, manifest, payload, marketplace, or version-field edits. |
| `git diff --check` | Pass | No whitespace errors. |
| `pnpm --dir docs-site reference:check` | Pass | `Reference pages are current.` |
| `pnpm --dir docs-site validate` | Pass | Ran `reference:check`, `astro check`, `astro build`, and internal link validation with 0 errors. |
| `bash tests/speckit-pro/run-all.sh` | Pass | `speckit-pro test suite: 3041/3041 passed` across Layers 1, 4, and 5. |

### Acceptance Criteria Traceability

| Criterion | Implemented Evidence |
|-----------|----------------------|
| AC-9.1 | Change Type Matrix lists docs-only, docs-site, plugin source, generated payload/dist, marketplace registry, and release automation lanes with required evidence. |
| AC-9.2 | Maintainer Release Readiness explains `build-plugin-payloads.sh`, `sync-marketplace-versions.sh`, `run-all.sh`, `reference:check`, and `docs-site validate`. |
| AC-9.3 | Version Fields defines release-please-owned source manifests, generated dist manifests, marketplace sync ownership, and rare manual override cases. |
| AC-9.4 | Final Checklist covers source/dist parity, Claude/Codex marketplace parity, manifest version consistency, generated payload validation, full suite, and docs-site validation. |
| AC-9.5 | Contributor Path documents Conventional Commit titles, public-readable PR bodies, validation evidence, non-goals, known gaps, and rollback notes. |
| AC-9.6 | Current PR Checks Behavior explains docs-only plugin-matrix skip behavior, sentinel/title checks, local docs-site validation, and DOC-010 CI hardening handoff. |

### PR Packet Evidence

- **Summary:** Deepened `/contribute-and-release` from a DOC-002 placeholder shell into the DOC-009 maintainer/contributor release workflow.
- **Affected paths:** `docs-site/src/content/docs/contribute-and-release.md`, `specs/doc-009-maintainer-contributor-release-workflow/tasks.md`, and this workflow evidence file.
- **Validation:** `git diff --check`; `pnpm --dir docs-site reference:check`; `pnpm --dir docs-site validate`; `bash tests/speckit-pro/run-all.sh`.
- **Scope notes:** Docs-only implementation. No CI, release automation, scripts, manifests, generated payloads, marketplace registries, or version fields changed.
- **Recommended PR title:** `docs(DOC-009): document maintainer contributor release workflow`

---

## Post-Implementation Checklist

- All tasks are marked complete in `tasks.md`.
- `docs-site/src/content/docs/contribute-and-release.md` no longer reads like a
  placeholder shell.
- AC-9.1 through AC-9.6 are traceable in the implemented docs.
- `pnpm --dir docs-site reference:check` passes.
- `pnpm --dir docs-site validate` passes.
- `bash tests/speckit-pro/run-all.sh` passes.
- The PR title uses Conventional Commit format and plain English.
- The PR body lists affected paths and validation commands.

### Post-Implementation Evidence

| Item | Result | Evidence |
|------|--------|----------|
| Doctor Extension Check | Complete | Fallback parent-session health check passed: templates present, Claude commands registered, scripts executable, constitution present, and feature artifacts present. |
| Verify Implementation | Complete | Verified 23/23 tasks complete, 15/15 functional requirements covered, and no constitution or scope-boundary findings. |
| Verify Tasks Phantom Check | Complete | `specs/doc-009-maintainer-contributor-release-workflow/verify-tasks-report.md` records 23 VERIFIED tasks and no flagged items. |
| Code Review | Skipped | Review extension is not installed in `.specify/extensions/.registry` and no review command surface exists under `.claude/commands`. |
| Integration Suite | Complete | `bash tests/speckit-pro/run-all.sh` passed with `3041/3041`. |
| Cleanup | Skipped | Cleanup extension is not installed in `.specify/extensions/.registry`; no cleanup command surface exists. |
| Final Reviewability Backstop | Complete | Returned `warn` with no blockers: total files 20 exceeded warn threshold 15 and primary surfaces 3 exceeded warn threshold 1; production LOC remained 0. |
| PR Packet/Body Generation | Complete | Generated packet/body, edited only allowed prose fields, and `validate-pr-packet.sh` passed. The generated protected body sections were generic packet text, so the actual PR body was prepared separately with DOC-009-specific review content. |
| PR Workflow Contract | Complete | `validate-pr-workflow-contract.sh` passed for `docs(DOC-009): document maintainer contributor release workflow`. |
| PR Creation | Complete | Draft PR opened: https://github.com/racecraft-lab/racecraft-plugins-public/pull/219 |
| Review Remediation | Complete | No review feedback existed at PR creation time. |
| Retrospective | Complete | `specs/doc-009-maintainer-contributor-release-workflow/retrospective.md` records 100% completion, 100% spec adherence, and zero critical findings. |

Note: post-extension subagent dispatch was attempted after G7, but the agent
threads were shut down before returning usable summaries. The post checks above
were completed in the parent session as a fallback and are recorded explicitly.

---

## Project Structure Reference

```text
racecraft-plugins-public/
  AGENTS.md
  CLAUDE.md
  .github/workflows/pr-checks.yml
  .github/workflows/release.yml
  docs/ai/specs/interactive-documentation-technical-roadmap.md
  docs/ai/specs/.process/DOC-009-design-concept.md
  docs/ai/specs/.process/DOC-009-workflow.md
  docs-site/package.json
  docs-site/src/content/docs/contribute-and-release.md
  docs-site/src/content/docs/reference/
  scripts/build-plugin-payloads.sh
  scripts/sync-marketplace-versions.sh
  specs/doc-009-maintainer-contributor-release-workflow/
  tests/speckit-pro/run-all.sh
```

---

Template based on SpecKit best practices and populated for DOC-009.

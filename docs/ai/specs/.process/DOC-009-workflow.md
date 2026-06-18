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
| Clarify | `/speckit-clarify` | In Progress | Resolving docs-page structure and validation boundaries |
| Plan | `/speckit-plan` | Pending | Produce implementation plan and reviewability budget |
| Checklist | `/speckit-checklist` | Pending | Run documentation, release-process, and validation checks |
| Tasks | `/speckit-tasks` | Pending | Produce ordered, reviewable implementation tasks |
| Analyze | `/speckit-analyze` | Pending | Check consistency across spec, plan, tasks, and design concept |
| Implement | `/speckit-implement` | Pending | Implement docs changes with focused verification |

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
| 1 | Page structure | Record count after session | Record command-block and section decisions |
| 2 | Source facts | Record count after session | Record citation rules and generated-reference boundaries |
| 3 | Validation and DOC-010 | Record count after session | Record validation matrix and handoff wording |

---

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
| `plan.md` | Pending | Must include docs-site and release-process constraints |
| `research.md` | Pending if needed | Use only if source facts require decisions |
| `data-model.md` | Pending if needed | Usually unnecessary for docs-only work |
| `contracts/` | Pending if needed | Usually unnecessary for docs-only work |
| `quickstart.md` | Pending | Should capture validation and review steps |

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
| documentation-ia | Fill after run | Fill after run | AC-9.1, AC-9.6 |
| release-process-accuracy | Fill after run | Fill after run | AC-9.2, AC-9.3, AC-9.4 |
| ci-validation | Fill after run | Fill after run | AC-9.1, AC-9.6 |
| reviewer-usability | Fill after run | Fill after run | AC-9.5 |

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
| Total Tasks | Fill after run |
| Phases | Fill after run |
| Parallel Opportunities | Fill after run |
| User Stories Covered | Fill after run |

---

## Atomicity Route

After the Tasks phase / gate G5, run the read-only atomicity classifier and
record its decision here.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | Pending | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | Pending | `true` or `false` |
| Signals | Pending | Decisive detector findings |
| Warnings | Pending | Release-safety warnings |

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
| Source-fact audit | Pending | No | |
| Page structure | Pending | No | |
| Contributor flow | Pending | No | |
| Maintainer flow | Pending | No | |
| Validation and polish | Pending | No | |

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

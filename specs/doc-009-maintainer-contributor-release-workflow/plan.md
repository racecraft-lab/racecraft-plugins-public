# Implementation Plan: Maintainer and Contributor Release Workflow

**Branch**: `doc-009-maintainer-contributor-release-workflow` | **Date**: 2026-06-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/doc-009-maintainer-contributor-release-workflow/spec.md`

## Summary

Deepen the existing `/contribute-and-release` docs route into a source-backed workflow page for maintainers, contributors, reviewers, and docs maintainers. The implementation is documentation-only: replace the DOC-002 shell content with a scannable how-to/reference hybrid that maps change types to source surfaces, generated/synchronized surfaces, validation evidence, version ownership, release automation behavior, PR expectations, and the DOC-010 docs-site CI handoff.

## Technical Context

**Language/Version**: Markdown content rendered by Astro 6.4.6 and Starlight 0.40.0; docs-site JavaScript ESM on Node for generated references.

**Primary Dependencies**: `docs-site/package.json` declares Astro, Starlight, `@astrojs/check`, and `starlight-links-validator`; no new dependency is planned.

**Storage**: Checked-in repository files only; no database, browser storage, or runtime service state.

**Testing**: `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site validate`, and `bash tests/speckit-pro/run-all.sh`.

**Target Platform**: Static docs-site route at `docs-site/src/content/docs/contribute-and-release.md`.

**Project Type**: Documentation site content in a plugin marketplace repository.

**Performance Goals**: Static-page content only; avoid adding runtime logic or build-time work beyond existing docs-site validation.

**Constraints**: Documentation-only unless a source citation is broken and a narrow fix is explicitly approved. Do not change CI workflows, release automation, scripts, manifests, generated payloads, marketplace registries, version fields, or generated reference pages for DOC-009.

**Scale/Scope**: One existing docs route plus spec workflow artifacts. The published page should cover five change types and map AC-9.1 through AC-9.6 to visible sections or checklist items.

**Reviewability Budget**: Primary surface docs/process; projected reviewable LOC 380; production files 0; total files about 6; budget result within budget.

## Declared File Operations

- MODIFIED docs-site/src/content/docs/contribute-and-release.md
- MODIFIED specs/doc-009-maintainer-contributor-release-workflow/plan.md
- NEW specs/doc-009-maintainer-contributor-release-workflow/research.md
- NEW specs/doc-009-maintainer-contributor-release-workflow/quickstart.md
- NEW specs/doc-009-maintainer-contributor-release-workflow/tasks.md
- MODIFIED docs/ai/specs/.process/DOC-009-workflow.md
- MODIFIED docs/ai/specs/.process/autopilot-state.json
- MODIFIED AGENTS.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| Surface assumptions before editing | Pass | DOC-009 is documented as docs-only in the workflow, design concept, spec, and this plan. |
| Simplest change that solves it | Pass | Deepen the existing `/contribute-and-release` route rather than adding a new route or changing release behavior. |
| Surgical edits | Pass | Planned source edits are limited to the target docs route and SpecKit workflow artifacts. |
| Verifiable success criteria | Pass | The plan requires docs reference check, docs-site validation, and the deterministic repository shell suite. |
| Public-readable PRs | Pass | The page will include Conventional Commit title guidance and public-readable PR body expectations. |
| Reviewability budget | Pass | Production files remain 0 and total files stay below the reviewability warning thresholds. |

## Project Structure

### Documentation (this feature)

```text
specs/doc-009-maintainer-contributor-release-workflow/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
└── tasks.md
```

### Source Code (repository root)

```text
docs-site/
├── package.json
├── scripts/
│   └── generate-reference-pages.mjs
└── src/content/docs/
    ├── contribute-and-release.md
    └── reference/
        ├── manifests.md
        ├── scripts.md
        ├── source-vs-dist.md
        └── tests.md

.github/workflows/
├── pr-checks.yml
└── release.yml

scripts/
├── build-plugin-payloads.sh
└── sync-marketplace-versions.sh

tests/speckit-pro/
└── run-all.sh
```

**Structure Decision**: Use the existing docs-site route as the only public content surface. Generated reference pages remain generated and are used as reader-facing links, while primary behavior claims cite checked-in source files.

## Complexity Tracking

No constitutional or reviewability violations are planned.

## Phase 0: Research

Research output is captured in [research.md](research.md). Decisions are source-backed by the existing docs shell, docs-site package scripts, generated reference generator, PR Checks workflow, Release workflow, release helper scripts, release-please config, plugin manifests, marketplace registries, test runner, and repository guidance.

Key decisions:

- Use one consolidated release-readiness command block in the page and let the change-type matrix label which evidence applies.
- Require `pnpm --dir docs-site validate` for `docs-site/**` changes, with `reference:check` named as both part of validation and a focused generated-reference drift preflight.
- Treat `bash tests/speckit-pro/run-all.sh` as the maintainer release-readiness expectation without claiming current CI runs it for every PR.
- Explain release automation as observable maintainer behavior from `.github/workflows/release.yml`, `release-please-config.json`, and `.release-please-manifest.json`.
- State that release-please owns source plugin manifest versions, generated payload manifests are rebuilt, and marketplace versions sync from source platform manifests.

## Phase 1: Design and Contracts

No data model is required because DOC-009 introduces no data entities, API behavior, storage, or runtime contracts. No contract files are required because this is a documentation-only route update.

[quickstart.md](quickstart.md) captures the reviewer-facing implementation and validation path:

1. Audit source facts against primary files.
2. Replace the existing route shell with the DOC-009 full playbook.
3. Verify generated reference drift with `pnpm --dir docs-site reference:check`.
4. Verify docs-site rendering and type checks with `pnpm --dir docs-site validate`.
5. Verify repository release-readiness expectations with `bash tests/speckit-pro/run-all.sh`.

## Phase 2: Task Planning Approach

Tasks should be grouped by user story and ordered for review:

1. Source-fact audit and citation map.
2. Route outline and source-of-truth map.
3. Change-type matrix and contributor path.
4. Maintainer release-readiness, version guidance, and release automation path.
5. Reviewer PR metadata guidance, final checklist, DOC-010 handoff, and validation.

Parallel task markers should only be used for independent source-reading or artifact updates that do not edit the same section of `docs-site/src/content/docs/contribute-and-release.md`.

## Reviewability and PR Packet Plan

**Primary review surface**: docs/process.

**Secondary surfaces**: docs-site content.

**Projected production files**: 0.

**Projected total files**: about 6.

**Split decision**: No split. The deliverable is one existing public docs route with supporting SpecKit artifacts and no behavior changes.

**PR review packet source**:

- What changed: DOC-009 replaces the DOC-002 `/contribute-and-release` shell with a source-backed release workflow.
- Why: maintainers and contributors need one page that separates source edits, generated payloads, marketplace sync, version ownership, validation evidence, and release automation.
- Non-goals: CI changes, release behavior changes, generated payload edits, marketplace version edits, and DOC-010 docs-site CI hardening.
- Review order: route content first, source citations second, SpecKit artifacts third.
- Traceability: map AC-9.1 through AC-9.6 to route sections and validation evidence.
- Verification: include docs-site reference check, docs-site validate, full shell suite, and any skipped-check rationale.
- Known gaps: DOC-010 owns future docs-site CI/search/accessibility/deep-link/responsive hardening.
- Rollback: revert the docs route and SpecKit artifact commits; no feature flags apply.

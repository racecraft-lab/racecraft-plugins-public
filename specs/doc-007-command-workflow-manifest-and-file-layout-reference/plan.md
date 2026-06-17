# Implementation Plan: Command, workflow, manifest, and file-layout reference

**Branch**: `doc-007-command-workflow-manifest-and-file-layout-reference` | **Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

DOC-007 adds deterministic, checked-in Markdown reference subpages for SpecKit Pro repository surfaces while preserving the existing `/reference/` landing page. The implementation uses one local Node generator under `docs-site/scripts/` to read allowlisted checked-in source paths, render seven stable Markdown pages, and provide a read-only `--check` mode that fails on stale output without changing plugin behavior, manifests, payloads, install flow, hooks, marketplace behavior, release automation, or GitHub Actions.

## Technical Context

**Language/Version**: JavaScript ESM on the docs-site Node runtime; Astro 6.4.6 and Starlight 0.40.0 for docs rendering.

**Primary Dependencies**: Node built-ins (`node:fs`, `node:path`, `node:url`), existing docs-site pnpm scripts, Astro/Starlight, and `starlight-links-validator`; no new runtime dependency planned.

**Storage**: Checked-in Markdown files under `docs-site/src/content/docs/reference/`; no database or browser storage.

**Testing**: `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, plus `bash tests/speckit-pro/run-all.sh --layer 1` only if implementation touches plugin/spec surfaces beyond docs-site reference generation.

**Target Platform**: Static docs site built from `docs-site/` with public routes under `/racecraft-plugins-public/reference/<slug>/`.

**Project Type**: Documentation generator plus static docs content.

**Performance Goals**: Deterministic local generation over a bounded checked-in source inventory; output order and bytes remain stable for unchanged inputs.

**Constraints**: Local-file-only generator; source reads restricted to allowlisted checked-in paths; check mode is read-only and exits `0` current, `1` stale output, `2` source/parsing/internal error; no `.github/workflows/*` edits; no reusable docs platform beyond DOC-007; generated content separates source facts from inferred notes.

**Scale/Scope**: Exactly seven generated first-class subpages: `skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, and `source-vs-dist`.

**Reviewability Budget**: Primary surface: docs/process. Secondary surfaces: docs-site generated reference pages and local docs validation. Plan estimator result: 80 projected LOC, 2 docs-site production-classified entries, 11 declared file entries, below warn/block thresholds. Plugin/runtime production-file scope remains 0. Generated reference pages are declared generated output and excluded from reviewable LOC estimates.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
List one entry per file on its own line, each starting with a `- ` list marker:
`- NEW <repo-relative-path>` for a new file or `- MODIFIED <repo-relative-path>`
for an existing one. The leading `- ` marker is required - a line without it is
ignored. Omit this block entirely and the estimator degrades gracefully to
`not_estimated`.

- NEW docs-site/scripts/generate-reference-pages.mjs
- MODIFIED docs-site/package.json
- MODIFIED docs-site/astro.config.mjs
- MODIFIED docs-site/src/content/docs/reference.md
- NEW docs-site/src/content/docs/reference/skills.md
- NEW docs-site/src/content/docs/reference/agents.md
- NEW docs-site/src/content/docs/reference/manifests.md
- NEW docs-site/src/content/docs/reference/hooks.md
- NEW docs-site/src/content/docs/reference/scripts.md
- NEW docs-site/src/content/docs/reference/tests.md
- NEW docs-site/src/content/docs/reference/source-vs-dist.md

Generated output declaration:

- `docs-site/src/content/docs/reference/*.md` subpages are generated Markdown output owned by `docs-site/scripts/generate-reference-pages.mjs`.
- Plugin source, generated payloads, manifests, hooks, marketplace files, release automation, and tests are source evidence only for DOC-007 unless a later phase explicitly identifies a validation-only docs-site need.
- Production-file scope is 2 docs-site production-classified entries by the estimator and 0 plugin/runtime production files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | DOC-007 application |
|-----------|--------|---------------------|
| I. Plugin Structure Compliance | PASS | Reads plugin structures as evidence only; does not edit `speckit-pro/`, `dist/`, manifests, hooks, marketplace entries, install flow, or release automation. |
| II. Script Safety | PASS | Adds a Node ESM docs-site script, not a shell script. The script must keep explicit file reads, deterministic ordering, clear exit codes, and no network/browser execution. |
| III. Semantic Versioning | PASS | No plugin version or release metadata edits are planned. |
| IV. Test Coverage Before Merge | PASS | Freshness check is part of docs validation. Link validation and stale-output behavior are required before implementation is complete. Plugin Layer 1 is conditional if plugin/spec surfaces are touched. |
| V. Conventional Commits | PASS | PR title and commit must use a docs-oriented Conventional Commit such as `docs(reference): generate plugin surface reference pages`. |
| VI. KISS, Simplicity & YAGNI | PASS WITH TRACKED TRADEOFF | One small generator is justified because generated full pages and check mode are explicit DOC-007 requirements. No reusable docs platform, CI hardening, search, or troubleshooting depth is included. |

Additional reviewability gates:

- Primary review surface: docs/process, with docs-site generated reference output as a secondary surface.
- Budget: 80 projected LOC, 2 docs-site production-classified entries, and 11 total declared entries including 7 generated outputs; all are below warn thresholds.
- Split decision: remains one spec because the slice is documentation/reference generation only and does not change plugin runtime behavior.
- PR review packet source: use `spec.md`, this plan, `quickstart.md`, generator check output, docs validation output, link validation output, and final `git diff --name-only` scope review.

Post-design re-check: PASS. Phase 1 artifacts define bounded data entities, CLI/check contracts, and validation scenarios without introducing broader platform scope.

## Project Structure

### Documentation (this feature)

```text
specs/doc-007-command-workflow-manifest-and-file-layout-reference/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── reference-generator.md
│   └── reference-inventory.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
docs-site/
├── package.json
├── astro.config.mjs
├── scripts/
│   └── generate-reference-pages.mjs
└── src/content/docs/
    ├── reference.md
    └── reference/
        ├── skills.md
        ├── agents.md
        ├── manifests.md
        ├── hooks.md
        ├── scripts.md
        ├── tests.md
        └── source-vs-dist.md

speckit-pro/                         # read-only source evidence
dist/claude/speckit-pro/             # read-only generated payload evidence
dist/codex/speckit-pro/              # read-only generated payload evidence
tests/speckit-pro/                   # read-only test evidence
```

**Structure Decision**: Use a docs-site-local generator and committed generated Markdown pages. This keeps the implementation small, reviewable in normal Markdown diffs, compatible with Starlight content routing, and independent of plugin runtime surfaces.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Generated full page content instead of hand-authored reference prose | Grill Me selected generated full pages, and the finalized spec requires deterministic generate/check behavior plus stale-output detection. | Hand-authored pages would be simpler but would not provide a reliable freshness check for generated rows and source citations. |

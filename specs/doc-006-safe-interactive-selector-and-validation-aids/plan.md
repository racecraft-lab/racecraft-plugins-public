# Implementation Plan: Safe Interactive Selector and Validation Aids

**Branch**: `doc-006-safe-interactive-selector-and-validation-aids` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md`

## Summary

Enhance the existing `choose-your-path` docs route with static-first selector, repository manifest checker, accessible generated-payload diagram, and first-run checklist aids. The implementation will read checked-in manifest JSON at docs build time, combine those manifest-backed values with a small docs metadata helper for curated command guidance, and render complete semantic fallback content without browser-side local command execution.

## Technical Context

**Language/Version**: Astro 6.4.6, Starlight 0.40.0, TypeScript/MDX-compatible docs content, Node.js through the docs-site pnpm toolchain

**Primary Dependencies**: Existing `docs-site` Astro/Starlight stack, native HTML controls, build-time JSON imports or Node `fs` reads for checked-in manifest files

**Storage**: Checked-in repository JSON and plugin manifests only; no generated metadata output and no user-local files

**Testing**: Focused metadata/rendering fixture or test, `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`

**Target Platform**: Static Starlight documentation site under the existing `/racecraft-plugins-public/` base path

**Project Type**: Static documentation web app

**Performance Goals**: Complete selector, checker, diagram, and checklist facts render in static HTML; any progressive enhancement remains small and non-blocking

**Constraints**: Use the existing `choose-your-path` route as the primary surface; follow `docs/ai/specs/.process/DOC-006-design-concept.md`; do not add a reusable generator, committed generated data file, pasted JSON checker, rich app widget, local browser command execution, or auto-config editing

**Scale/Scope**: One docs route, one small Astro component, one source-derived docs metadata helper, six manifest inputs, and one focused validation fixture/test

**Reviewability Budget**: Primary surface is `docs-site` docs/process content for the existing choose-your-path route. Projected reviewable LOC is 450-700 excluding fixtures/generated artifacts. Projected production files are 3-5 and projected total files are 5-8. Budget result: PASS with advisory warning because projected reviewable LOC is above the 400 LOC warning band but below the 800 LOC block threshold, with one primary surface and no split exception required.

### Preserved Q&A Decisions

- Q1 chose "Enhance Choose Your Path".
- Q3 chose "Build-time read only" for source-derived metadata.
- Q4 chose "Static-first enhancement".
- Q5 chose "Lightweight handoff only" for troubleshooting.
- Q6 chose "Repo consistency only" for the checker.
- Q7 chose "Accessible static diagram".
- Q8 chose "Docs plus focused fixture".

## Declared File Operations

- MODIFIED docs-site/src/content/docs/choose-your-path.md
- NEW docs-site/src/content/docs/choose-your-path.mdx
- NEW docs-site/src/components/SafeInstallAids.astro
- NEW docs-site/src/data/safe-install-aids.ts
- NEW docs-site/scripts/validate-doc006-safe-aids.mjs

Route file operation note: implementation should preserve the public `choose-your-path` route while converting the current Markdown source to MDX if needed for the Astro component import. Git may record this as a rename or delete/add pair; the declaration lists both the current and target route paths so review can verify the route remains stable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial gate status**: PASS with advisory reviewability warning.

- **I. Plugin Structure Compliance**: PASS. This is a docs-site-only change and does not alter plugin manifests, command definitions, skill folders, agents, hooks, or plugin packaging structure.
- **II. Script Safety**: PASS by plan. The only planned script is a focused docs-site validation fixture. If implemented as Bash it must use `#!/usr/bin/env bash` and `set -euo pipefail`; the preferred plan is a Node `.mjs` fixture to stay aligned with the Astro toolchain.
- **III. Semantic Versioning**: PASS. No plugin version or release metadata changes are planned.
- **IV. Test Coverage Before Merge**: PASS by plan. Standard docs validation and link validation remain required, plus the DOC-006 focused metadata/rendering fixture.
- **V. Conventional Commits**: PASS by process. Final PR title and commit must use the repo's Conventional Commit format.
- **VI. KISS, Simplicity & YAGNI**: PASS. The plan uses one route, one small component, one helper, native controls, static fallback content, and no reusable generator or rich app widget.

**Re-check after Phase 1 design**: PASS with the same advisory warning. The data model and contract keep the implementation to one vertical docs slice. No ratified split exception is required because the projected total files and production files stay below block thresholds and the feature has one primary review surface.

## Project Structure

### Documentation (this feature)

```text
specs/doc-006-safe-interactive-selector-and-validation-aids/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- contracts/
|   +-- doc006-safe-aids.schema.json
+-- tasks.md                  # Phase 2 output, not created by /speckit-plan
```

### Source Code (repository root)

```text
docs-site/
+-- src/
|   +-- components/
|   |   +-- SafeInstallAids.astro
|   +-- content/docs/
|   |   +-- choose-your-path.mdx
|   +-- data/
|       +-- safe-install-aids.ts
+-- scripts/
    +-- validate-doc006-safe-aids.mjs

.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
speckit-pro/.claude-plugin/plugin.json
speckit-pro/.codex-plugin/plugin.json
dist/claude/speckit-pro/.claude-plugin/plugin.json
dist/codex/speckit-pro/.codex-plugin/plugin.json
```

**Structure Decision**: Use the existing docs-site route as the only user-facing surface. Keep source-derived manifest reads in a small `docs-site/src/data/` helper, render selector/checker/diagram/checklist markup in one Astro component, and keep focused validation in one docs-site script or fixture. The six manifest paths are read-only data inputs, not implementation targets.

## Phase 0: Research Decisions

See [research.md](research.md). No open research items remain for planning. Decisions are bounded by the design concept and clarified spec: build-time read-only data, route-preserving static-first UI, repository-only checker, accessible static diagram, lightweight troubleshooting handoffs, and focused fixture validation.

## Phase 1: Design Artifacts

- [data-model.md](data-model.md) defines selector paths, command guidance, manifest consistency comparisons, checker states, diagram nodes, first-run checkpoints, and handoff links.
- [contracts/doc006-safe-aids.schema.json](contracts/doc006-safe-aids.schema.json) defines the normalized metadata shape expected by the focused fixture/test.
- [quickstart.md](quickstart.md) records focused and standard validation commands.

## Implementation Boundaries

- Allowed: route-preserving MDX conversion, one small Astro component, one small data helper, focused fixture/test, static fallback tables/lists, native controls, copyable visible commands.
- Required manifest inputs: `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/claude/speckit-pro/.claude-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`.
- Disallowed: install Markdown parsing as data source, persistent generated metadata output, pasted JSON checker, browser-side shell command execution, local user file inspection, local plugin workflow invocation, auto-config editing, full troubleshooting matrix, update/rollback/cache diagnosis expansion.
- Unsupported, unavailable, or ambiguous selector states are handled as static rendering states only: derive supported platform/scope pairs from checked-in selector path metadata, identify unsupported or ambiguous combinations in text, keep complete supported static guidance reachable, and route to safe install or DOC-008-owned troubleshooting handoffs without local diagnostics or repair claims.
- Direct source-data bug rule: If implementation discovers an actual mismatch in one of the six checked-in manifest files, stop and record it as a source-data bug before modifying source manifests.

## Validation Plan

- Focused metadata/rendering fixture or test verifies selector required fields, unsupported or ambiguous selector-state handling, platform command-surface boundaries, checker pass/mismatch/unavailable states, no pasted-JSON or local-diagnostic UI, handoff links, first-run checkpoint coverage, and manifest-backed field drift.
- Build validation: `pnpm --dir docs-site validate`.
- Link validation: `pnpm --dir docs-site validate:links`.
- Full verify: `pnpm --dir docs-site validate && pnpm --dir docs-site validate:links`.

## Complexity Tracking

No constitution violations require a complexity exception. The advisory LOC warning is accepted because the feature remains one route-centered docs slice below block thresholds and avoids generator or rich-widget scope.

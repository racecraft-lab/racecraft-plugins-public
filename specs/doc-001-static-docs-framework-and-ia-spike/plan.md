# Implementation Plan: Static docs framework and IA spike

**Branch**: `doc-001-static-docs-framework-and-ia-spike` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/doc-001-static-docs-framework-and-ia-spike/spec.md`

## Summary

DOC-001 is a research-only spike that selects the static documentation stack and route-level IA foundation for DOC-002. The selected recommendation is **Astro with Starlight**, hosted through GitHub Pages from this repository, with package/build/test commands recorded as report-only guidance and no docs-site scaffolding created in this phase.

## Technical Context

**Language/Version**: Markdown/MDX research artifacts. Docusaurus official docs were refreshed at version 3.10.1 on 2026-06-12; the 2026-06-13 update observed npm metadata for `@astrojs/starlight` 0.40.0, `starlight-versions` 0.9.0, and `starlight-links-validator` 0.24.1. DOC-001 records evidence only and does not pin package versions or add Node project files; DOC-002 must refresh current docs before installation.

**Primary Dependencies**: None added by DOC-001. Report-only DOC-002 recommendation: Astro/Starlight, MDX/components, GitHub Actions Pages deployment, built-in Pagefind search, optional `starlight-links-validator`, and deferred/optional `starlight-versions`.

**Storage**: N/A. Static docs content only.

**Testing**: Research validation by source evidence review and final diff scope check. Report-only DOC-002 command roles: scaffold/setup, dependency install, development preview, production build, local static preview, deployment, and minimum validation. DOC-002 owns actual package scripts after scaffolding; the minimum docs-site validation role is the production build.

**Target Platform**: GitHub Pages from this repository.

**Project Type**: Documentation research spike for a future static docs site.

**Performance Goals**: N/A for DOC-001. Future site should remain static, searchable, deep-linkable, and usable with static fallbacks.

**Constraints**: Research-only. Do not create site scaffold, package files, lockfiles, CI workflows, marketplace files, generated payloads, README migrations, plugin behavior changes, or prototype components.

**Scale/Scope**: One decision record, one route-level IA skeleton covering the 11 required PRD route labels, plus SpecKit plan artifacts.

**Reviewability Budget**: Primary surface: docs/process; projected reviewable LOC: 200-450 excluding unchanged templates; production files: 1 research report and 0 production code files; total files: 3-5 including SpecKit artifacts; budget result: within budget.

## Declared File Operations

- NEW docs/ai/research/interactive-documentation-framework-spike.md
- NEW specs/doc-001-static-docs-framework-and-ia-spike/research.md
- NEW specs/doc-001-static-docs-framework-and-ia-spike/data-model.md
- NEW specs/doc-001-static-docs-framework-and-ia-spike/quickstart.md
- MODIFIED specs/doc-001-static-docs-framework-and-ia-spike/plan.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate Result | Notes |
|---|---|---|
| I. Plugin Structure Compliance | Pass | DOC-001 does not alter plugin manifests, commands, agents, skills, hooks, or tests. |
| II. Script Safety | Pass | No shell scripts are created or modified. |
| III. Semantic Versioning | Pass | No plugin version fields are modified. |
| IV. Test Coverage Before Merge | Pass | No implementation code or script behavior changes require new tests; verification is documentation-scope and diff-scope review. |
| V. Conventional Commits | Pass | No commit is created by this phase. Future PR title must remain Conventional Commit compliant. |
| VI. KISS, Simplicity & YAGNI | Pass | One research artifact records the decision; no speculative scaffold or tooling is introduced. |

**Review surface**: docs/process only.

**Budget check**: Within reviewability budget. DOC-001 remains a research spike and does not cross production-file or primary-surface thresholds.

**Split decision**: No split required. DOC-002 owns docs-site shell creation after this recommendation is accepted.

**PR review packet source**: The PR description should summarize the research recommendation, non-goals, scope budget, route-level IA handoff, verification evidence, known community-plugin/versioning/link-validation tradeoffs, Astro portfolio alignment, and rollback as deleting the DOC-001 research/planning artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/doc-001-static-docs-framework-and-ia-spike/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── spec.md

docs/ai/research/
└── interactive-documentation-framework-spike.md
```

### Source Code (repository root)

```text
docs/
├── prd-interactive-documentation.md
├── roadmap-interactive-documentation.md
└── ai/
    ├── research/
    │   └── interactive-documentation-framework-spike.md
    └── specs/
        ├── interactive-documentation-technical-roadmap.md
        └── .process/
            └── DOC-001-design-concept.md

specs/doc-001-static-docs-framework-and-ia-spike/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
└── quickstart.md
```

**Structure Decision**: DOC-001 writes one public research decision record under `docs/ai/research/` and normal SpecKit planning artifacts under the feature spec directory. Contracts are not generated because the spike exposes no API, CLI, service, schema, or runtime interface.

## Phase 0: Research Plan

Research resolved the open framework, package-manager, and GitHub Pages hosting questions with live official-source refresh on 2026-06-12 and an Astro/Starlight decision update on 2026-06-13.

**Candidate set**:
- Docusaurus/MDX
- VitePress
- Astro/Starlight
- Repo-native fallback

**Required comparison dimensions**:
- Static hosting
- GitHub Pages support
- MDX or equivalent reusable-component interactivity
- Search
- Versioning
- Accessibility and static fallback
- Link checking
- Docs-as-code workflow
- Maintenance load
- Package/build/test commands
- Support class for each capability

**Research output**: [research.md](research.md) plus the full decision record at [docs/ai/research/interactive-documentation-framework-spike.md](../../docs/ai/research/interactive-documentation-framework-spike.md).

## Phase 1: Design Plan

**Data model**: [data-model.md](data-model.md) defines Framework Candidate, Evaluation Criterion, IA Route, Source Evidence, Command Recommendation, and Spike Report.

**Contracts**: Not applicable. No external interface is exposed by DOC-001, and no `contracts/` directory is created.

**Quickstart**: [quickstart.md](quickstart.md) documents reviewer validation for the research report, IA skeleton, no-implementation boundary, and DOC-002 handoff.

**Agent context update**: Skipped. `CLAUDE.md` in this worktree does not contain `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` markers, so no marker-bounded plan reference can be updated without inventing a new contract.

## Post-Design Constitution Check

| Principle | Gate Result | Notes |
|---|---|---|
| I. Plugin Structure Compliance | Pass | Generated artifacts are documentation/planning files only. |
| II. Script Safety | Pass | No scripts changed. |
| III. Semantic Versioning | Pass | No manifest or marketplace versions changed. |
| IV. Test Coverage Before Merge | Pass | No runtime behavior changed; verification is documentation and scope review. |
| V. Conventional Commits | Pass | No commit created. |
| VI. KISS, Simplicity & YAGNI | Pass | Astro/Starlight is recommended for DOC-002, but no framework files are introduced in DOC-001. |

**Gate status**: Pass. No unjustified constitutional violations.

## Complexity Tracking

No constitutional violations require justification.

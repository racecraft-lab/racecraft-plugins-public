# Implementation Plan: Claude Code Marketplace Installation Path

**Branch**: `doc-003-claude-code-marketplace-installation-path` | **Date**: 2026-06-14 | **Spec**: `specs/doc-003-claude-code-marketplace-installation-path/spec.md`

**Input**: Feature specification from `specs/doc-003-claude-code-marketplace-installation-path/spec.md`

## Summary

Deliver the canonical Claude Code install route for SpecKit Pro at `docs-site/src/content/docs/install/claude-code.md`. The implementation is documentation-only: write the ordered marketplace add, plugin install, reload, verification, lifecycle, and trust guidance; align install-relevant README/AGENTS terminology around namespaced plugin skills; and cite official Claude Code docs for platform behavior plus repository source/generated payload paths for SpecKit Pro specifics.

## Technical Context

**Language/Version**: Markdown content for Astro 6.4.6 and Starlight 0.40.0 docs site, plus repository Markdown docs

**Primary Dependencies**: Astro 6.4.6, Starlight 0.40.0, pnpm 10.25.0, official Claude Code plugin docs, Racecraft marketplace/source/generated payload files

**Storage**: N/A

**Testing**: `pnpm --dir docs-site validate`; add `bash tests/speckit-pro/run-all.sh --layer 1` only if plugin manifests, hooks, agents, skills, or generated payloads change

**Target Platform**: Static docs site under `docs-site/src/content/docs/` and repository Markdown readers

**Project Type**: Documentation site and repository documentation

**Performance Goals**: First-time Claude Code install path completable from the page in under 10 minutes; evaluator can identify trust surfaces in under 5 minutes

**Constraints**: Docs-only; do not change plugin runtime behavior, regenerate `dist/**`, bump versions, or alter release automation; Claude route cross-links Codex but does not explain Codex install steps; platform behavior claims cite official Claude Code docs; plugin-specific claims cite repository source or generated payload paths; consolidate install-relevant wording on skills terminology

**Scale/Scope**: One canonical Claude install page plus tightly scoped install-relevant README/AGENTS terminology patches, projected 250-600 documentation lines across 3-6 total files

**Reviewability Budget**: Primary surface docs/process; secondary surfaces install-relevant README/AGENTS wording only; projected reviewable LOC 250-600; production files 0; projected total files 3-6; budget result within budget; split decision one spec

## Declared File Operations

- MODIFIED docs-site/src/content/docs/install/claude-code.md
- MODIFIED README.md
- MODIFIED AGENTS.md
- MODIFIED speckit-pro/README.md
- MODIFIED specs/doc-003-claude-code-marketplace-installation-path/plan.md
- NEW specs/doc-003-claude-code-marketplace-installation-path/research.md
- NEW specs/doc-003-claude-code-marketplace-installation-path/data-model.md
- NEW specs/doc-003-claude-code-marketplace-installation-path/quickstart.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Plugin Structure Compliance | PASS | Planned implementation does not change plugin layout, manifests, hooks, agents, skills, or generated payloads. |
| II. Script Safety | PASS | No shell scripts are planned. |
| III. Semantic Versioning | PASS | No plugin version or release automation changes are planned. |
| IV. Test Coverage Before Merge | PASS | Docs-site validation is the required verification. Layer 1 is only required if implementation escapes docs/process scope into plugin manifests, hooks, agents, skills, or generated payloads. |
| V. Conventional Commits | PASS | PR title can use a docs-scoped Conventional Commit such as `docs: add Claude Code marketplace install guide`. |
| VI. KISS, Simplicity & YAGNI | PASS | One vertical docs slice covers the Claude install route, lifecycle guidance, and trust inventory without absorbing the DOC-008 troubleshooting matrix or DOC-004 Codex install path. |

Additional reviewability gate:

- Primary review surface: docs/process.
- Secondary surfaces: install-relevant README/AGENTS terminology only.
- Budget thresholds: below 800 reviewable LOC, 8 production files, 25 total files, and one primary surface.
- Split decision: one spec remains appropriate. Deferred work: DOC-004 owns Codex install instructions; DOC-008 owns deep troubleshooting and rollback matrix content.
- PR review packet source: final PR description must include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback/feature-flag notes.

## Project Structure

### Documentation (this feature)

```text
specs/doc-003-claude-code-marketplace-installation-path/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
└── quickstart.md
```

`contracts/` is intentionally omitted. DOC-003 does not introduce a public API, CLI grammar, endpoint, parser contract, or machine-readable schema. Its user-facing contract is the documentation route itself, validated through source-backed command coverage and docs-site validation.

### Source Code (repository root)

```text
docs-site/
└── src/content/docs/install/claude-code.md

README.md
AGENTS.md
speckit-pro/README.md

.claude-plugin/marketplace.json
speckit-pro/.claude-plugin/plugin.json
speckit-pro/skills/
speckit-pro/agents/
speckit-pro/hooks/hooks.json
dist/claude/speckit-pro/
```

**Structure Decision**: Modify only the canonical docs route and install-relevant terminology surfaces. Treat marketplace manifests, source skill/agent/hook directories, and generated Claude payload paths as read-only evidence unless implementation finds a direct documentation accuracy blocker that still fits docs/process scope.

## Phase 0 Research

Research is recorded in `research.md`. All technical context items are resolved.

## Phase 1 Design

Design entities are recorded in `data-model.md`.

Contracts are intentionally omitted because this feature exposes no external software interface.

Validation scenarios are recorded in `quickstart.md`.

## Post-Design Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Plugin Structure Compliance | PASS | Design keeps plugin source and generated payload files as citation targets, not mutation targets. |
| II. Script Safety | PASS | No script changes or new scripts are planned. |
| III. Semantic Versioning | PASS | Version files remain out of scope. |
| IV. Test Coverage Before Merge | PASS | `pnpm --dir docs-site validate` covers the docs route. Layer 1 remains conditional on any unplanned plugin source/payload change. |
| V. Conventional Commits | PASS | Docs-only PR can use a valid public-readable docs title. |
| VI. KISS, Simplicity & YAGNI | PASS | Scope remains one route and limited terminology alignment; troubleshooting matrix and runtime behavior remain deferred/out of scope. |

## Complexity Tracking

No constitution violations.

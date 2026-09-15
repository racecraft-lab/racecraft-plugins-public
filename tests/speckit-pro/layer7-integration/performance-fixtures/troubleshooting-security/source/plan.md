# Implementation Plan: Troubleshooting, Security, Trust, Update, And Rollback

**Branch**: `doc-008-troubleshooting-security-trust-update-rollback` | **Date**: 2026-06-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md`

## Summary

DOC-008 expands the existing Troubleshooting and Security & Trust route shells into source-backed user documentation and adds a top-level Update & Rollback page. The implementation stays docs-only: Markdown content under the docs site, a minimal Starlight sidebar addition, install-page links into the new recovery route, and a hand-authored `reference.md` handoff into the correct DOC-008 destinations. Platform behavior claims must cite current official Claude Code or OpenAI Codex documentation; Racecraft-specific claims must cite checked-in files or generated DOC-007 reference pages.

## Technical Context

**Language/Version**: Docs-site JavaScript ESM on Node, with Markdown/MDX content under `docs-site/src/content/docs/`

**Primary Dependencies**: Astro 6.4.6, Starlight 0.40.0, existing `starlight-links-validator`

**Storage**: Checked-in Markdown/MDX files only; no database, browser storage, or runtime state

**Testing**: `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`

**Target Platform**: Static Starlight documentation site served from `/racecraft-plugins-public/`

**Project Type**: Documentation site content update

**Performance Goals**: No runtime code path or build architecture change; pages must remain static Markdown/MDX and validate in the existing docs-site build

**Constraints**: Docs-only; no live diagnostic command; no browser execution; no browser-granted permissions; no browser-run plugin/workflow actions; no CI workflow changes; no plugin behavior, manifest, hook, generated-payload, marketplace, release automation, or SpecKit CLI changes; official platform claims require current vendor documentation citations; Racecraft claims require checked-in source or generated DOC-007 reference citations

**Scale/Scope**: Three user-facing support/evaluator routes plus sidebar, install-page linking, and hand-authored reference-shell handoff linking
**Reviewability Budget**: Primary surface docs/process; projected 380 lines of Markdown content excluding phase artifacts; no runtime app logic files; estimator-projected 40 LOC because `docs-site/astro.config.mjs` is a production-classified config file; about 7 docs-site files; within budget

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
List one entry per file on its own line, each starting with a `- ` list marker:
`- NEW <repo-relative-path>` for a new file or `- MODIFIED <repo-relative-path>`
for an existing one. The leading `- ` marker is required - a line without it is
ignored.

- MODIFIED docs-site/src/content/docs/troubleshooting.md
- MODIFIED docs-site/src/content/docs/security-and-trust.md
- NEW docs-site/src/content/docs/update-and-rollback.md
- MODIFIED docs-site/src/content/docs/install/claude-code.md
- MODIFIED docs-site/src/content/docs/install/codex.md
- MODIFIED docs-site/src/content/docs/reference.md
- MODIFIED docs-site/astro.config.mjs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Plugin Structure Compliance | PASS | DOC-008 may cite plugin structure, manifests, hooks, skills, agents, and generated references, but the planned file operations do not edit plugin payloads, manifests, hooks, agents, skills, marketplace registries, or generated payloads. |
| II. Script Safety | PASS | No shell scripts are planned. Existing docs-site scripts are invoked only for validation. |
| III. Semantic Versioning | PASS | No plugin manifest or version file changes are planned. |
| IV. Test Coverage Before Merge | PASS | The plan requires docs-site reference, build/type, and link validation. Layer 1 is conditional only if later implementation touches plugin/spec surfaces, manifests, scripts, hooks, or generated payload paths. |
| V. Conventional Commits | PASS | PR title remains compatible with `docs(speckit-pro): ...` or another valid Conventional Commit title. |
| VI. KISS, Simplicity & YAGNI | PASS | The design uses existing Starlight pages, Markdown tables/headings, generated DOC-007 references, and existing validation commands. No diagnostic engine, browser command runner, CI hardening, or new dependency is planned. |

**Post-design re-check**: PASS. Phase 0 and Phase 1 artifacts keep the same docs-only file operations, no new runtime dependencies, and no constitution exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/doc-008-troubleshooting-security-trust-update-rollback/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── spec.md
```

Contracts are intentionally omitted because DOC-008 does not expose a new API, CLI command, schema, or generated data artifact.

### Source Code (repository root)

```text
docs-site/
├── astro.config.mjs
└── src/content/docs/
    ├── troubleshooting.md
    ├── security-and-trust.md
    ├── update-and-rollback.md
    ├── reference.md
    └── install/
        ├── claude-code.md
        └── codex.md
```

**Structure Decision**: Use the existing docs-site content tree and Starlight sidebar. Add `update-and-rollback` under the existing How-to navigation next to `troubleshooting`; keep security/trust in Explanation.

## Phase 0 Research

Research is recorded in [research.md](./research.md). It resolves these planning decisions:

- Three-page IA: troubleshooting, security/trust, and update/rollback stay separate.
- Source policy: official vendor behavior, repository facts, and recommended practice are distinct evidence groups.
- Troubleshooting model: symptom matrix rows separate read-only inspection from mutating recovery.
- Recovery model: each recovery case carries checkpoint, manual action, side effect, reload/restart expectation, and source citation.
- Validation model: docs-site validation bundle is required; plugin Layer 1 is conditional.

## Phase 1 Design

Design is recorded in [data-model.md](./data-model.md) and [quickstart.md](./quickstart.md).

### Page Architecture

| Page | Planned shape | Citation policy |
|------|---------------|-----------------|
| `troubleshooting.md` | Symptom matrix as a semantic Markdown table or equivalent sectioned list with explicit field headers, readable row labels, stable support anchors, platform label, likely cause, read-only inspect command/file, recommended fix, follow-up link, and citation | Platform command behavior cites official docs; Racecraft source/payload/cache claims cite DOC-007 references or checked-in source |
| `security-and-trust.md` | Fact-bound trust model grouped by official vendor behavior, repository facts, and recommended practice | Every platform behavior claim cites current official vendor docs; repository claims cite DOC-007 generated pages or checked-in source files |
| `update-and-rollback.md` | Recovery cases for update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version sync as semantic Markdown tables or equivalent sectioned lists with explicit headers, readable case labels, stable anchors where useful, checkpoint, manual action, side effect, reload/restart expectation, and source citation | Each case includes checkpoint, manual action, side effect, reload/restart need, and source citation |
| `reference.md` | Hand-authored reference shell handoff that sends readers from source/dist, manifests, skills, agents, hooks, scripts, and tests orientation to the correct DOC-008 troubleshooting, security/trust, or update/rollback destination | Links point to DOC-008 pages without hand-editing generated `reference/*.md` subpages |

### Documentation Boundaries

- Inspection cells contain only read-only commands, platform detail views, manual paths, or links.
- Dense troubleshooting and recovery matrices remain understandable as copied/static Markdown and do not rely on visual layout, color, JavaScript, or interactive-only controls.
- Required follow-up links use descriptive destination-identifying link text.
- Stable headings, slugs, anchors, or first-column labels support direct support links without creating site-wide deep-link conventions owned by DOC-010.
- Browser docs may show commands, files, and workflow names as guidance, but they do not grant permissions or run plugin/workflow actions.
- Mutating commands appear only in recommended fix or recovery guidance, with side effects stated before the command.
- Direct cache edits, direct cache deletion, and cache directory removal are never default fixes.
- Codex plugin install, bundled skill loading, custom-agent registration, and restart remain separate recovery concepts.
- Claude Code marketplace update/remove, plugin install/uninstall, `/reload-plugins`, plugin detail inspection, managed policy, installed state, and cache behavior remain separate recovery concepts.
- Generated DOC-007 reference pages are not hand-edited.
- Reference-to-DOC-008 handoffs live in the hand-authored `reference.md` shell unless a later spec explicitly changes the reference generator.

## Validation Plan

Required implementation verification:

```bash
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate
pnpm --dir docs-site validate:links
pnpm --dir docs-site validate && pnpm --dir docs-site validate:links
```

Conditional verification:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

Run Layer 1 only if implementation unexpectedly touches plugin/spec surfaces, manifests, scripts, hooks, or generated payload paths.

## Review Packet Source

The DOC-008 PR packet should map:

- What changed: expanded troubleshooting/security pages, added update/rollback page, linked install pages and the hand-authored reference shell, and sidebar route.
- Why: DOC-008 support, evaluator, and stale-install recovery guidance.
- Non-goals: no security audit, certification, threat model, live diagnostic command, browser execution, CI change, plugin behavior change, generated payload change, or release automation change.
- Review order: `update-and-rollback.md`, `troubleshooting.md`, `security-and-trust.md`, install links, sidebar.
- Scope budget: docs/process primary surface, no runtime app logic files, seven docs-site files planned, and estimator-projected 40 LOC from one production-classified config file.
- Traceability: FR-001 through FR-019 to changed docs and validation commands.
- Verification: docs-site reference, build/type, link validation; conditional Layer 1 only if surfaces expand.
- Known gaps: platform docs may drift after implementation; validate official citations again before final PR.
- Rollback/flags: revert the docs-site content/sidebar diff; no feature flags.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

# Implementation Plan: Command, workflow, manifest, and file-layout reference

**Branch**: `doc-007-command-workflow-manifest-and-file-layout-reference` | **Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

DOC-007 adds deterministic, checked-in Markdown reference subpages for SpecKit Pro repository surfaces while preserving the existing `/reference/` landing page. The implementation uses one local Node generator under `docs-site/scripts/` to read allowlisted checked-in source paths, render seven stable Markdown pages, update existing docs pages with context-specific deep links to those generated subpages, and provide a read-only `--check` mode that fails on stale output without changing plugin behavior, manifests, payloads, install flow, hooks, marketplace behavior, release automation, or GitHub Actions.

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

**Reviewability Budget**: Primary surface: docs/process. Secondary surfaces: docs-site generated reference pages, link-only existing docs updates, and local docs validation. Plan estimator result: approximately 92 projected LOC, 8 docs-site production-classified entries, and 17 declared file entries, below warn/block thresholds. Plugin/runtime production-file scope remains 0. Generated reference pages are declared generated output and excluded from reviewable LOC estimates.

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
- MODIFIED docs-site/src/content/docs/install/claude-code.md
- MODIFIED docs-site/src/content/docs/install/codex.md
- MODIFIED docs-site/src/content/docs/first-run.md
- MODIFIED docs-site/src/content/docs/troubleshooting.md
- MODIFIED docs-site/src/content/docs/security-and-trust.md
- MODIFIED docs-site/src/content/docs/contribute-and-release.md
- NEW docs-site/src/content/docs/reference/skills.md
- NEW docs-site/src/content/docs/reference/agents.md
- NEW docs-site/src/content/docs/reference/manifests.md
- NEW docs-site/src/content/docs/reference/hooks.md
- NEW docs-site/src/content/docs/reference/scripts.md
- NEW docs-site/src/content/docs/reference/tests.md
- NEW docs-site/src/content/docs/reference/source-vs-dist.md

Generated output declaration:

- `docs-site/src/content/docs/reference/*.md` subpages are generated Markdown output owned by `docs-site/scripts/generate-reference-pages.mjs`.
- Existing install, first-run, troubleshooting, security, and contributor docs updates are link-only UX routing changes to point readers at generated reference subpages; they must not add DOC-008 troubleshooting/security depth or DOC-009 contributor/release procedure depth.
- Plugin source, generated payloads, manifests, hooks, marketplace files, release automation, and tests are source evidence only for DOC-007 unless a later phase explicitly identifies a validation-only docs-site need.
- Production-file scope is 8 docs-site production-classified entries by the estimator and 0 plugin/runtime production files.

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

- Primary review surface: docs/process, with docs-site generated reference output and link-only existing docs updates as secondary surfaces.
- Budget: approximately 92 projected LOC, 8 docs-site production-classified entries, and 17 total declared entries including 7 generated outputs and 6 link-only existing docs updates; all are below warn thresholds.
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
    ├── install/
    │   ├── claude-code.md
    │   └── codex.md
    ├── first-run.md
    ├── troubleshooting.md
    ├── security-and-trust.md
    ├── contribute-and-release.md
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

**Source Allowlist And Evidence Boundary**: The generator validates inputs with normalized repo-relative paths. It must not reject the repository merely because the absolute checkout path is nested under a parent `.worktrees/` directory.

| Source group | Allowed repo-relative inputs | Evidence use |
|--------------|------------------------------|--------------|
| Marketplace and plugin manifests | `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json`, `.specify/integrations/claude.manifest.json`, `.specify/integrations/speckit.manifest.json` | Source evidence for marketplace, plugin, and integration manifest rows. |
| Plugin source package | `speckit-pro/` | Authoring-source evidence for skills, Claude agents, Codex agents, hooks, scripts, README/changelog context, and source-vs-dist relationships. |
| Checked-in generated payloads | `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/` | Generated-payload inventory evidence only; do not treat these files as authoring source-of-truth for plugin behavior or semantics. |
| Root scripts | `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh` | Source evidence for release/build script inventory only; DOC-007 must not change release automation behavior. |
| Tests | `tests/speckit-pro/` | Source evidence for test and validation inventory rows only. |
| Docs-site handoff | `docs-site/package.json`, `docs-site/astro.config.mjs`, `docs-site/src/content/docs/reference.md`, `docs-site/src/content/docs/install/claude-code.md`, `docs-site/src/content/docs/install/codex.md`, `docs-site/src/content/docs/first-run.md`, `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, `docs-site/src/content/docs/contribute-and-release.md` | Source evidence for package-script handoff, sidebar/reference navigation, and existing-doc deep-link updates. |

Explicit exclusions: repo-relative `.git/`, repo-relative `.worktrees/`, `node_modules/`, generated `docs-site/src/content/docs/reference/skills.md`, `agents.md`, `manifests.md`, `hooks.md`, `scripts.md`, `tests.md`, and `source-vs-dist.md` as source evidence, any path outside the repository root, user home/cache installs, network sources, and user-pasted JSON.

**Generator Error Handling Contract**: Stale generated output is a freshness result, not a source/parsing/internal failure. The generator classifies failures before reporting them:

| Class | Applies in | Exit | Diagnostic route | Required diagnostic fields | Disposition |
|-------|------------|------|------------------|----------------------------|-------------|
| Current output | Check mode | `0` | stdout | Current-output summary | No recovery needed. |
| Stale generated output | Check mode only | `1` | stdout | Stale generated page paths and `pnpm --dir docs-site reference:generate` | Does not imply source corruption; run generate, review generated Markdown diff, rerun check. |
| Absent optional surface | Generate and check | `0` unless another failure occurs | Generated content | Surface is labeled absent or omitted without source facts | Non-error; do not invent rows or cite generated output as evidence. |
| Missing or unreadable required source | Generate and check | `2` | stderr | `source` category, repo-relative source path, concise cause | Fix the checked-in source path, allowlist, or file permissions; rerun generate/check. |
| Allowlist or normalized path violation | Generate and check | `2` | stderr | `source` category, normalized repo-relative path or attempted path, concise cause | Fix the source inventory or path construction. A checkout under a parent `.worktrees/` directory remains valid. |
| Malformed JSON manifest/config | Generate and check | `2` | stderr | `parse` category, repo-relative source path, concise parse cause | Fix the checked-in JSON before generated rows are trusted. |
| Malformed or missing Markdown/frontmatter metadata | Generate and check | `2` | stderr | `parse` category, repo-relative source path, missing field or parser cause | Fix the checked-in Markdown/frontmatter metadata before generated rows are trusted. |
| Generated output write failure | Generate mode only | `2` | stderr | `output-write` category, generated output path, concise write cause | Fix the local filesystem/output path and rerun generate; check mode never writes. |
| Internal render or comparison failure | Generate and check | `2` | stderr | `internal` category, generator phase, source/output path when available, concise cause | Fix the generator or failing phase; do not route to DOC-008 troubleshooting or DOC-010 CI unless the failure reveals out-of-scope docs hardening work. |

Generate mode must collect, parse, validate, and render all source-backed reference data in memory before writing the seven generated Markdown outputs. Source, parsing, or internal failures stop before output writes so unsupported source facts or inferred notes are not published. Output-write failures can only occur after source data has been validated and must be reported as `output-write` without weakening check-mode immutability.

Check mode renders expected Markdown in memory and compares it to committed output. In both exit `1` and exit `2` paths, check mode must not create, rewrite, delete, format, or update generated reference files, docs-site package/config files, sidebar configuration, or existing docs links. `pnpm --dir docs-site validate` must propagate `reference:check` exit codes instead of masking stale-output or source/parsing/internal failures.

**Generated Page Source-Input Matrix**:

| Generated page | Source inputs that may support rows | Required source-data boundary |
|----------------|--------------------------------------|-------------------------------|
| `reference/skills` | `speckit-pro/skills/`, `speckit-pro/codex-skills/`, `dist/claude/speckit-pro/skills/`, `dist/codex/speckit-pro/skills/`, `README.md`, `speckit-pro/README.md`, and existing install/first-run docs where they state invocation/prerequisite/output behavior | Present Claude Code and Codex command or skill forms in parallel where concepts map; include source-backed invocation, purpose, prerequisites, and expected output artifact; cite `dist/` only as payload inventory evidence. |
| `reference/agents` | `speckit-pro/agents/`, `speckit-pro/codex-agents/`, `dist/claude/speckit-pro/agents/`, `dist/codex/speckit-pro/codex-agents/` | Preserve runtime-specific agent file formats and do not collapse Markdown and TOML differences. |
| `reference/manifests` | Marketplace/plugin/integration manifests from the allowlist plus generated dist plugin manifests | Distinguish marketplace registries, source plugin manifests, integration manifests, and generated distribution manifests; list required and optional plugin manifest fields separately for Claude Code and Codex without changing manifest semantics. |
| `reference/hooks` | `speckit-pro/hooks/hooks.json`, `speckit-pro/codex-hooks.json`, `dist/claude/speckit-pro/hooks/hooks.json`, `dist/codex/speckit-pro/codex-hooks.json` | Describe hook/config inventory without changing hook semantics. |
| `reference/scripts` | `speckit-pro/scripts/`, `speckit-pro/skills/speckit-autopilot/scripts/`, root `scripts/`, and relevant test validators | Classify build/release scripts separately from autopilot helper scripts and validation scripts. |
| `reference/tests` | `tests/speckit-pro/` | Classify tests as validation evidence and avoid treating fixtures or replay data as plugin behavior source. |
| `reference/source-vs-dist` | All allowed source groups above | Show editability and responsibility for source, generated payload, test-only, release infrastructure, and documentation infrastructure paths. |

**Generated Record Content Requirements**:

- Command and skill records include the visible fields `Claude Code invocation`, `Codex invocation`, `Purpose`, `Prerequisites`, and `Expected output artifact` when the values are applicable and supported by checked-in source evidence. Runtime-specific absence is labeled explicitly instead of inferred from silence.
- Manifest records include runtime-specific `Required fields` and `Optional fields` groupings for Claude Code and Codex plugin manifests. If a field classification is derived from repository conventions rather than a manifest file literal, it appears as an inferred note with `Based on:` source paths.
- Every generated page includes the visible generated notice before record content, and check mode treats a missing or changed notice as stale generated output rather than silently accepting the page.

**Source-vs-Dist Responsibility Mapping**:

| Surface group | Authoring source evidence | Generated payload evidence | Classification rule |
|---------------|---------------------------|----------------------------|---------------------|
| Skills | `speckit-pro/skills/*/SKILL.md`, `speckit-pro/codex-skills/*/SKILL.md` | `dist/claude/speckit-pro/skills/*/SKILL.md`, `dist/codex/speckit-pro/skills/*/SKILL.md` | Source files are editable; dist files are generated payload inventory. |
| Agents | `speckit-pro/agents/*.md`, `speckit-pro/codex-agents/*.toml` | `dist/claude/speckit-pro/agents/*.md`, `dist/codex/speckit-pro/codex-agents/*.toml` | Markdown and TOML runtime formats are parallel but distinct. |
| Manifests | `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json`, `.specify/integrations/*.manifest.json` | `dist/claude/speckit-pro/.claude-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json` | Marketplace, plugin, integration, and dist manifests must remain separate categories; required and optional field lists are reference metadata only and do not alter manifest semantics. |
| Hooks | `speckit-pro/hooks/hooks.json`, `speckit-pro/codex-hooks.json` | `dist/claude/speckit-pro/hooks/hooks.json`, `dist/codex/speckit-pro/codex-hooks.json` | Hooks are documented as configuration surfaces only; semantics are unchanged. |
| Scripts | `speckit-pro/scripts/`, `speckit-pro/skills/speckit-autopilot/scripts/`, root `scripts/` | `dist/*/speckit-pro/scripts/` and `dist/*/speckit-pro/skills/speckit-autopilot/scripts/` where present | Script records identify role and path; release/build behavior remains out of scope. |
| Tests | `tests/speckit-pro/` | None | Test files are validation-only evidence and are not generated payload. |
| Docs reference output | `docs-site/scripts/generate-reference-pages.mjs`, docs-site config/content allowlist | `docs-site/src/content/docs/reference/*.md` generated pages | Generated reference pages are outputs, not source evidence. |

**Docs-Site Script And Navigation Handoff**:

| File | Required change |
|------|-----------------|
| `docs-site/package.json` | Add `"reference:generate": "node scripts/generate-reference-pages.mjs"`, add `"reference:check": "node scripts/generate-reference-pages.mjs --check"`, and change `"validate"` from the current check/build sequence to `"pnpm reference:check && pnpm check && pnpm build"`. |
| `docs-site/astro.config.mjs` | Keep the existing `Reference` group, with sidebar items ordered as `reference`, `reference/skills`, `reference/agents`, `reference/manifests`, `reference/hooks`, `reference/scripts`, `reference/tests`, `reference/source-vs-dist`, then `glossary`. |

**Structure Decision**: Use a docs-site-local generator and committed generated Markdown pages. This keeps the implementation small, reviewable in normal Markdown diffs, compatible with Starlight content routing, and independent of plugin runtime surfaces.

**Generated Markdown Accessibility Constraints**: Generated output must be readable as committed Markdown and rendered static HTML. Required source facts, source citations, inferred notes, and platform mappings must not rely on JavaScript-only filtering, disclosure, expansion, or client-rendered data. Output must use stable page, section, and per-record headings; ordered field labels; labeled compact tables or lists when used; and citation links whose visible text includes repo-relative source paths with distinguishing context for repeated or multiple citations. DOC-010 owns automated accessibility tooling, responsive/browser validation, search, and CI hardening.

**Deep-Link Update Scope**: Existing install, first-run, troubleshooting, security, and contributor pages receive only task-relevant links and short lead-in text to generated reference subpages. The target mapping follows the spec's IA clarification and uses exact source files:

| Existing docs file | Required generated reference targets |
|--------------------|--------------------------------------|
| `docs-site/src/content/docs/install/claude-code.md` | `reference/manifests`, `reference/skills`, `reference/agents`, `reference/hooks`, `reference/source-vs-dist` where those links clarify install-time surfaces. |
| `docs-site/src/content/docs/install/codex.md` | `reference/manifests`, `reference/skills`, `reference/agents`, `reference/hooks`, `reference/source-vs-dist` where those links clarify install-time surfaces. |
| `docs-site/src/content/docs/first-run.md` | `reference/skills`, `reference/scripts`, `reference/tests`. |
| `docs-site/src/content/docs/troubleshooting.md` | `reference/source-vs-dist`, `reference/manifests`, `reference/hooks`. |
| `docs-site/src/content/docs/security-and-trust.md` | `reference/hooks`, `reference/agents`, `reference/manifests`, `reference/source-vs-dist`. |
| `docs-site/src/content/docs/contribute-and-release.md` | `reference/source-vs-dist`, `reference/scripts`, `reference/tests`, `reference/manifests`. |

Generic-only `/reference/` links are insufficient in these files when a generated subpage is more precise for the surrounding task. Existing-doc edits remain link-only plus brief lead-in text; DOC-008 troubleshooting/security depth and DOC-009 contributor/release procedure depth stay out of scope.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Generated full page content instead of hand-authored reference prose | Grill Me selected generated full pages, and the finalized spec requires deterministic generate/check behavior plus stale-output detection. | Hand-authored pages would be simpler but would not provide a reliable freshness check for generated rows and source citations. |

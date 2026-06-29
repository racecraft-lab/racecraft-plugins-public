# Repository Guidelines

## Project Structure & Module Organization

This repository is a Claude Code and Codex plugin marketplace. The Claude Code
registry lives in `.claude-plugin/marketplace.json`. Each plugin gets its own
top-level directory; today that is `speckit-pro/`.

Inside `speckit-pro/`:

- `commands/` contains Claude Code slash-command docs with required YAML
  frontmatter. Install-facing usage should still prefer current plugin skill
  wording, for example `/speckit-pro:<skill>`.
- `skills/` contains skill folders such as `speckit-autopilot/` and `speckit-coach/`, each with a `SKILL.md` entry point plus optional `references/` and `scripts/`.
- `agents/` contains sub-agent definitions.
- `hooks/` contains plugin hook configuration.
- `tests/` contains the 5-layer shell test suite.

## Build, Test, and Development Commands

There is no compiled build step. Work is validated through shell scripts and repository structure checks.

- `bash tests/speckit-pro/run-all.sh` runs the default deterministic layers: 1, 4, and 5.
- `bash tests/speckit-pro/run-all.sh --layer 1` runs structural validation only.
- `bash tests/speckit-pro/run-all.sh --layer 4` runs script unit tests.
- `bash tests/speckit-pro/run-all.sh --all` includes AI-eval layers when prerequisites are installed.

For marketplace updates, commit and push changes, then refresh the marketplace in Claude Code with `/plugin marketplace update racecraft-plugins-public`.

## Coding Style & Naming Conventions

Use Bash and Markdown consistently with the existing codebase: 2-space indentation in Markdown lists/tables where needed, and shell scripts starting with `#!/usr/bin/env bash` plus `set -euo pipefail`.

Name plugins and skill directories in kebab-case, for example `speckit-autopilot`. Keep command filenames aligned with command names, for example `commands/autopilot.md`. Command docs must start and end frontmatter with `---` and include `description:` and `allowed-tools:`.

## Testing Guidelines

Tests are shell-based. Structural tests verify manifests, command frontmatter, hooks, skills, and agents. Script tests cover helper scripts such as `skills/.../scripts/validate-gate.sh`.

Add or update tests when changing command schemas, hook config, skill layout, or script behavior. Prefer the smallest relevant layer during development, then rerun `bash tests/speckit-pro/run-all.sh` before opening a PR.

## Commit & Pull Request Guidelines

Follow the repo’s existing Conventional Commit pattern: `feat(skills): ...`, `fix(agents): ...`, `chore(evals): ...`. Keep scopes specific to the area changed.

PRs should include a brief summary, affected plugin paths, test commands run, and sample output or screenshots when user-facing command behavior changes.

## Recent SpecKit Archive Notes

- PRSG-007 and PRSG-011 are archived in `.specify/memory/` as completed on 2026-06-09.
- PRSG-008 is archived in `.specify/memory/` as completed on 2026-06-10.
- PRSG-009 is archived in `.specify/memory/` as completed on 2026-06-11.
- PRSG-010 is archived in `.specify/memory/` as completed on 2026-06-11.
- PRSG-005 and PRSG-013 are archived in `.specify/memory/` as completed on 2026-06-12.
- SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-006a, PRSG-002, PRSG-003, PRSG-004, PRSG-006, and PRSG-012 are archived in `.specify/memory/` as completed or historically merged on 2026-06-13.
- DOC-001 is archived in `.specify/memory/` as completed on 2026-06-13 after PR #163 merged.
- DOC-002 is archived in `.specify/memory/` as completed on 2026-06-14 after PRs #173-#177 merged.
- PRSG-014 is archived in `.specify/memory/` as completed on 2026-06-14 after PR #181 merged.
- DOC-003 and DOC-004 are archived in `.specify/memory/` as completed on 2026-06-15 after PR #187 and PR #186 merged.
- DOC-005 is archived in `.specify/memory/` as completed on 2026-06-16 after PRs #198-#201 merged.
- DOC-006 is archived in `.specify/memory/` as completed on 2026-06-17 after PR #203 merged.
- DOC-007 is archived in `.specify/memory/` as completed on 2026-06-17 after PR #208 merged.
- DOC-008 and DOC-009 are archived in `.specify/memory/` as completed on 2026-06-18 after PR #220 and PR #219 merged.
- TACD-001 is archived in `.specify/memory/` as completed on 2026-06-18 after PRs #211-#214 and #216 merged.
- TACD-002 is archived in `.specify/memory/` as completed on 2026-06-18 after PRs #221-#226 merged.
- TACD-003 is archived in `.specify/memory/` as completed on 2026-06-19 after PR #230 merged.
- DOC-010 is archived in `.specify/memory/` as completed on 2026-06-19 after PRs #232-#236 merged.
- TACD-004 is archived in `.specify/memory/` as completed on 2026-06-22 after PR #240 merged.
- DOC-011 is archived in `.specify/memory/` as completed on 2026-06-23 after PR #243 merged.
- DOC-013 is archived in `.specify/memory/` as completed on 2026-06-24 after PR #246 merged; `specs/doc-013-brand-identity-marketplace-landing/` was removed from active `specs/**` cleanup and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-24-doc-013-post-merge-hygiene.md`.
- XPLAT-003 is archived in `.specify/memory/` as completed on 2026-06-29 after PR #267 merged; `specs/xplat-003-supply-chain-security-and-consumer-trust-model/` was removed from active `specs/**` cleanup and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`.
- XPLAT-001, XPLAT-002, and DOC-014 are archived in `.specify/memory/` as completed on 2026-06-29 after PR #263, PR #266, and PR #264 merged; `specs/xplat-001-runtime-inventory-constraints/`, `specs/xplat-002-runtime-implementation-options-contract-decision/`, and `specs/doc-014-seo-and-ai-discoverability/` were removed from active `specs/**` cleanup and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.
- `specs/prsg-007-atomicity-router` and `specs/prsg-011-retro-migration` were removed from active `specs/**` cleanup after PR #136 decoupled Layer 4 dogfood/schema tests from the live PRSG-007 spec directory.
- `specs/prsg-008-layer-planner` was removed from active `specs/**` cleanup after the planner schema fixture was vendored under `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/`.
- `specs/prsg-009-multi-pr-emission` was removed from active `specs/**` cleanup after PR #145 merged and the PRSG-009 contract schemas were preserved under `speckit-pro/skills/speckit-autopilot/contracts/`.
- `specs/prsg-010-harden-the-hatch` was removed from active `specs/**` cleanup after PRs #149-#155 merged and the PRSG-010 contract schemas were preserved under `speckit-pro/skills/speckit-autopilot/contracts/`.
- `specs/prsg-005-slice-sizing-heuristics` and `specs/prsg-013-reviewability-markers` were removed from active `specs/**` cleanup after PR #120 and PR #157 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.
- `specs/001-repository-foundation`, `specs/002-pr-checks-workflow`, `specs/003-release-automation`, `specs/004-integration-verification`, `specs/006a-uat-skeleton`, `specs/prsg-002-moc-templates`, `specs/prsg-003-spec-index`, `specs/prsg-004-roadmap-moc-home-note`, `specs/prsg-006-reviewability-budget`, and `specs/prsg-012-reviewer-ready-pr-packet-contract` were removed from active `specs/**` cleanup after merge provenance, recovery commands, and fixture decoupling were recorded in `.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.
- `specs/doc-001-static-docs-framework-and-ia-spike` was removed from active `specs/**` cleanup after PR #163 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md`.
- `specs/doc-002-unified-landing-page-and-ia-shell` was removed from active `specs/**` cleanup after PRs #173-#177 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`.
- `specs/prsg-014-optional-gh-stack-stack-manager-integration` was removed from active `specs/**` cleanup after PR #181 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`.
- `specs/doc-003-claude-code-marketplace-installation-path` and `specs/doc-004-codex-marketplace-installation-path` were removed from active `specs/**` cleanup after PR #187 and PR #186 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md`.
- Residual DOC-005 PR-packet evidence under `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer` was removed from active `specs/**` cleanup after PRs #198-#201 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md`.
- `specs/doc-006-safe-interactive-selector-and-validation-aids` was removed from active `specs/**` cleanup after PR #203 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md`.
- `specs/doc-007-command-workflow-manifest-and-file-layout-reference` was removed from active `specs/**` cleanup after PR #208 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md`.
- `specs/doc-008-troubleshooting-security-trust-update-rollback` and `specs/doc-009-maintainer-contributor-release-workflow` were removed from active `specs/**` cleanup after PR #220 and PR #219 merged, the canonical docs-site support/release workflow pages landed, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.
- `specs/tacd-001-platform-mechanics-spike` was removed from active `specs/**` cleanup after PRs #211-#214 and #216 merged, the canonical spike report landed at `docs/ai/research/tool-agnostic-capability-discovery-spike.md`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md`.
- `specs/tacd-002-capability-discovery-directive-and-agent-updates` was removed from active `specs/**` cleanup after PRs #221-#226 merged, the shared capability directive and marker-emission hardening landed in source/generator/test paths, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`.
- `specs/tacd-003-prerequisite-and-documentation-messaging` was removed from active `specs/**` cleanup after PR #230 merged, the generic `capability_coverage` advisory, active guidance, generated payloads, focused tests, and PR packet evidence landed, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`.
- `specs/doc-010-search-accessibility-deep-links-docs-validation` was removed from active `specs/**` cleanup after PRs #232-#236 merged, the docs-site validation path, support anchors, accessibility/fallback updates, PR Checks docs gate, compact smoke coverage, and PR packet evidence landed, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md`.
- `specs/tacd-004-verification-coverage` was removed from active `specs/**` cleanup after PR #240 merged, the `strip_codex_guard` payload-build fix, rebuilt payloads, the named-tool and pointer/resolution/body-completeness guards, and rewritten vendor-neutral evals landed in source/generator/test paths, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md`.
- `specs/doc-011-github-pages-build-and-deploy-pipeline` was removed from active `specs/**` cleanup after PR #243 merged, the Deploy Docs GitHub Pages workflow, staging noindex/robots guard, CI/CD verification runbook, workflow lint gate, release runtime alignment, shared index generator hardening, synced payloads, and focused tests landed, and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md`.
- `.specify/feature.json` is transient local state. Do not commit a stale completed-spec pointer back to `main`.

## Active Technologies
- Docs-site JavaScript ESM on Node; Astro 6.4.6 and Starlight 0.40.0 for docs rendering; Node built-ins (`node:fs`, `node:path`, `node:url`) plus existing docs-site pnpm scripts and `starlight-links-validator`; no new runtime dependency planned. (doc-007-command-workflow-manifest-and-file-layout-reference)
- Checked-in Markdown files under `docs-site/src/content/docs/reference/`; no database or browser storage. (doc-007-command-workflow-manifest-and-file-layout-reference)
- Markdown content rendered by Astro 6.4.6 and Starlight 0.40.0; docs-site JavaScript ESM on Node for generated references; `docs-site/package.json` declares Astro, Starlight, `@astrojs/check`, and `starlight-links-validator`; no new dependency planned. (doc-009-maintainer-contributor-release-workflow)
- Checked-in repository files only; no database, browser storage, or runtime service state. (doc-009-maintainer-contributor-release-workflow)
- Docs-site validation uses Node ESM scripts, Astro/Starlight build and link validation, focused safe-aids/docs-quality checks, and Playwright smoke through `pnpm --dir docs-site validate`; smoke evidence is a short-retention CI artifact, not a committed durable payload. (doc-010-search-accessibility-deep-links-docs-validation)
- GitHub Actions deploys the docs-site through standard GitHub Pages Actions after `pnpm --dir docs-site validate`; repository Pages source remains a manual Settings -> Pages prerequisite until configured by an operator. (doc-011-github-pages-build-and-deploy-pipeline)
- Docs-site brand styling via a single `brand.css` mapping the Racecraft palette onto Starlight `--sl-color-*` tokens (light + dark), five self-hosted woff2 `@font-face`s (Space Grotesk/Geist/Fira Code) with `font-display: swap` and two `crossorigin` preloads, and a Starlight-native `template: splash` landing route; no new runtime dependency (fonts/favicons/logos ported verbatim). (doc-013-brand-identity-marketplace-landing)
- XPLAT runtime planning now targets a Python 3.11+ standard-library runner aligned with official Spec Kit / `specify` prerequisites; Go, Rust, Zig, native binaries, Bash, Git Bash, WSL, PowerShell helper scripts, `jq`, Node, `pip install`, venv restore, and package restore are rejected as required installed-plugin runtime substrates. (xplat-003-supply-chain-security-and-consumer-trust-model)
- Docs-site discoverability uses Astro/Starlight static output with `starlight-llms-txt`, `astro-og-canvas`/CanvasKit, `@astrojs/sitemap`, route-data JSON-LD injection, per-page Markdown routes, dynamic `robots.txt`, git-backed freshness, and focused Playwright SEO specs; staging noindex remains until DOC-012 launch. (doc-014-seo-and-ai-discoverability)

## Recent Changes
- doc-007-command-workflow-manifest-and-file-layout-reference: Planned a docs-site reference generator that emits committed Markdown pages using Node built-ins and existing Astro/Starlight validation; no new runtime dependency planned.
- doc-009-maintainer-contributor-release-workflow: Planned a docs-only release workflow page for maintainers and contributors using existing docs-site validation, release helper scripts, PR Checks, and release-please source evidence.
- doc-010-search-accessibility-deep-links-docs-validation: Shipped support anchors, accessible docs aids and fallbacks, one local docs validation path, the conditional `validate-docs` PR Checks gate, and compact Playwright smoke evidence across PRs #232-#236.
- doc-011-github-pages-build-and-deploy-pipeline: Shipped the Deploy Docs workflow, staging noindex/robots guard, CI/CD runbook, workflow lint gate, release runtime alignment, and shared index generator hardening; the first post-merge deploy failed until Pages is manually enabled for GitHub Actions.
- doc-013-brand-identity-marketplace-landing: Shipped the Racecraft docs-site brand identity (palette → Starlight tokens for light/dark, self-hosted woff2 typefaces, wordmark/favicon set) and a Starlight-native splash marketplace landing page with one primary CTA, WCAG AA contrast, and reduced-motion support, merged via PR #246.
- xplat-003-supply-chain-security-and-consumer-trust-model: Shipped the Python-only first-release supply-chain and consumer-trust model, including runner integrity metadata, install-completeness evidence, latest tagged release verification, autoheal/doctor expectations, native UAT boundaries, and public-claim limits, merged via PR #267.
- xplat-001-runtime-inventory-constraints: Shipped the cross-platform runtime inventory report and non-scoring runtime/supply-chain rubrics, merged via PR #263.
- xplat-002-runtime-implementation-options-contract-decision: Shipped the amended Python standard-library runner decision, rejected compiled binaries for XPLAT, and recorded the `speckit-pro-runner` contract, merged via PR #266.
- doc-014-seo-and-ai-discoverability: Shipped crawler access, agent-readable docs, metadata/schema/social-card/freshness surfaces, SEO validation, and the AI-discoverability metric, merged via PR #264.

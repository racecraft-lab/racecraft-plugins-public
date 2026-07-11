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
- `speckit_pro_runner/` contains the Python 3.11+ installed runtime and gates.

Repository-only validation lives under `tests/speckit-pro/`, outside the shipped
plugin. `tests/speckit-pro/suite-manifest.json` is the source of truth for layer
membership, dispatch, execution mode, and default selection.

## Build, Test, and Development Commands

There is no compiled build step. Work is validated through Python 3.11+
standard-library tooling and repository structure checks. Run commands from the
repository root.

- `python3 tests/speckit-pro/run-all.py` runs the toolchain preflight and default deterministic Layers 1, 4, and 5.
- `python3 tests/speckit-pro/run-all.py --layer 1` runs structural validation only.
- `python3 tests/speckit-pro/run-all.py --layer 4` runs the `Unit Tests` layer under `tests/speckit-pro/unit/`.
- `python3 tests/speckit-pro/run-all.py --integration` runs Layer 7 replay fixtures; add `--live` only for an intentional live integration run.
- `python3 tests/speckit-pro/check-toolchain.py --mode tests` prints the direct test-toolchain report; `docs` and `all` modes cover docs tooling.

`--all` implies live mode: it executes Layers 1, 4, 5, and live Layer 7,
prints manual command plans for live-only Layers 2, 3, and 6, and does not select
gate-only Layer 8. Do not describe it as the full deterministic suite.

For marketplace updates, commit and push changes, then refresh the marketplace in Claude Code with `/plugin marketplace update racecraft-plugins-public`.

## Coding Style & Naming Conventions

Use Python and Markdown consistently with the existing codebase: Python 3.11+
standard library, `#!/usr/bin/env python3` for executable Python files, argument
arrays and `shell=False` for subprocesses, and 2-space indentation in Markdown
lists/tables where needed. Repository-local Bash is confined to bounded workflow
dispatch glue and the fixed vendored `.specify/**` allowlist; do not introduce a
new Bash or `jq` runtime dependency.

Name plugins and skill directories in kebab-case, for example `speckit-autopilot`. Keep command filenames aligned with command names, for example `commands/autopilot.md`. Command docs must start and end frontmatter with `---` and include `description:` and `allowed-tools:`.

## Testing Guidelines

The suite is manifest-driven and Python-authoritative. Layer 1 verifies
manifests, command frontmatter, hooks, skills, agents, payloads, and workflow
contracts. The `Unit Tests` layer uses `tests/speckit-pro/unit/` for repository
helpers and runner behavior; Layer 5 verifies agent tool scoping.

Add or update tests when changing command schemas, hook config, skill layout, or
helper behavior. Prefer the smallest relevant layer during development, then
rerun `python3 tests/speckit-pro/run-all.py` before opening a PR.

## Commit & Pull Request Guidelines

Follow the repo’s existing Conventional Commit pattern: `feat(skills): ...`, `fix(agents): ...`, `chore(evals): ...`. Keep scopes specific to the area changed.

PRs should include a brief summary, affected plugin paths, test commands run, and sample output or screenshots when user-facing command behavior changes.

Use the repository PR template. `feat` and `fix` PRs require exactly one
non-empty fenced `release-note` block unless `release-note/skip` applies. The
Release workflow refreshes generated release artifacts on the release PR branch;
do not hand-edit generated payloads, installed-cache proofs, or generated
reference pages.

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
- XPLAT-004 is archived in `.specify/memory/` as completed on 2026-07-01 after PR #274 merged; `specs/xplat-004-cross-platform-runner-foundation/` was removed from active `specs/**` cleanup, the Layer 4 runner runbook fixture was preserved under `tests/speckit-pro/unit/fixtures/speckit-pro-runner/`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`.
- XPLAT-005 is archived in `.specify/memory/` as completed on 2026-07-03 after PR #276 merged; `specs/xplat-005-read-only-helper-port/` was removed from active `specs/**` cleanup, the Layer 4 read-only helper fixture inputs were preserved under `tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature/`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`.
- XPLAT-006 is archived in `.specify/memory/` as completed on 2026-07-04 after PR #281 merged; `specs/xplat-006-mutation-install-pr-emission-helper-port/` was removed from active `specs/**` cleanup, the Layer 4 mutation-helper contract fixtures were preserved under `tests/speckit-pro/unit/fixtures/mutation-helpers/contracts/`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md`.
- XPLAT-007 is archived in `.specify/memory/` as completed on 2026-07-05 after PRs #284-#287 merged; `specs/xplat-007-python-tooling-and-release-gate-migration/` was removed from active `specs/**` cleanup, the Layer 4 gate contract fixtures were preserved under `tests/speckit-pro/unit/fixtures/runner-gates/contracts/`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`.
- XPLAT-008 is archived in `.specify/memory/` as completed on 2026-07-07 after PRs #289-#292 merged; `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/` was removed from active `specs/**` cleanup, the Layer 4 release contract fixtures were preserved under `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/`, release-readiness and UAT evidence was preserved under `docs/ai/specs/.process/`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md`.
- XPLAT-009 is archived in `.specify/memory/` as completed on 2026-07-08 after PR #297 merged (shipped in speckit-pro 2.18.0, with Windows interpreter follow-up fix PR #299); `specs/xplat-009-plugin-source-and-payload-bash-eradication/` was removed from active `specs/**` cleanup, the Layer 4 zero-Bash contract schemas were preserved under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/`, guard and release evidence remains preserved under `docs/ai/specs/.process/XPLAT-009-*`, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md`.
- XPLAT-010 is archived in `.specify/memory/` as completed on 2026-07-11 after PRs #311-#328 merged; `specs/xplat-010-repository-bash-confinement/` was removed from active `specs/**` cleanup after live schema, planner, parity-contract, and UAT inputs were preserved under purpose-based test/process paths, all eleven `docs/ai/specs/.process/XPLAT-010-*` evidence files remain preserved, and recovery commands were recorded in `.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`.
- `specs/prsg-007-atomicity-router` and `specs/prsg-011-retro-migration` were removed from active `specs/**` cleanup after PR #136 decoupled Layer 4 dogfood/schema tests from the live PRSG-007 spec directory.
- `specs/prsg-008-layer-planner` was removed from active `specs/**` cleanup after the planner schema fixture was vendored under `tests/speckit-pro/unit/fixtures/plan-layers/contracts/`.
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
- SpecKit Pro now includes a source-checkout Python 3.11+ standard-library runner package at `speckit-pro/speckit_pro_runner/`, invoked with `<python> -m speckit_pro_runner`, with JSON envelope validation, runtime-info/preflight operations, typed path/subprocess fixture primitives, manifest/checksum metadata, and Layer 4 runner tests; active Claude/Codex cutover remains XPLAT-007. (xplat-004-cross-platform-runner-foundation)
- SpecKit Pro read-only/advisory helper behavior is now ported into `speckit-pro/speckit_pro_runner/helpers/` with an explicit registry, Python-authoritative helper records, source-checkout Bash-reference comparisons, request fixtures under `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/`, and Layer 4 parity coverage; mutation/install/PR-emission helpers and active Claude/Codex cutover remain XPLAT-006/XPLAT-007. (xplat-005-read-only-helper-port)
- SpecKit Pro mutation, install/doctor, PR-body, and deferred PR-emission/restack helper behavior now has Python runner-side mutation primitives, install inventory and fake-home proof, PR-emission fixtures, deferred live-mutation diagnostics, phase-coverage hardening, and Layer 4 mutation-helper gates; active repo-local Bash gate migration remains XPLAT-007 and Claude/Codex installed cutover remains XPLAT-008. (xplat-006-mutation-install-pr-emission-helper-port)
- SpecKit Pro active repo-local suite, payload, install-verification, release-readiness, and active-path guard gates now run through Python 3.11+ standard-library runner operations with promotion records, CI dispatch updates, maintainer command updates, XPLAT-007 gate fixtures, and Layer 4 gate coverage; active Claude/Codex installed cutover, release payload publication, native UAT, update/autoheal, and public release readiness remain XPLAT-008. (xplat-007-python-tooling-and-release-gate-migration)
- SpecKit Pro installed Claude/Codex runtime surfaces, generated payloads, public docs claim wording, release-readiness gates, UAT matrix contract, and bounded install-health repair now run through Python 3.11+ standard-library runner operations with XPLAT-008 release fixtures and generated payloads refreshed; public native Windows/macOS/Linux release claims remain blocked until the preserved six-row UAT matrix passes. (xplat-008-claude-codex-cutover-universal-install-release-gate)
- SpecKit Pro plugin source and generated Claude/Codex payloads contain zero live `.sh` files and zero unallowlisted active Bash/`jq` instructions, enforced by a Python-backed zero-Bash guard over source, rebuilt payloads, and a bounded installed-cache proof with a reviewable historical allowlist; repository-wide confinement was completed by XPLAT-010. (xplat-009-plugin-source-and-payload-bash-eradication)
- Repository-only validation is manifest-driven Python 3.11+ standard-library tooling under `tests/speckit-pro/`; tracked Bash is confined to bounded GitHub workflow dispatch glue and the fixed release-excluded vendored `.specify/**` allowlist; stable Linux amd64/arm64 sentinels, advisory Windows smoke, repository confinement, spec-size estimation, and deterministic consumer release-note validation/composition are active. Public native-platform claims remain blocked by the XPLAT-008 operator UAT matrix. (xplat-010-repository-bash-confinement)

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
- xplat-004-cross-platform-runner-foundation: Shipped the source-checkout Python runner foundation, runtime-info/preflight contract surface, manifest/checksum metadata, contract fixtures, and Layer 4 runner tests, merged via PR #274.
- xplat-005-read-only-helper-port: Shipped the read-only/advisory helper registry and ports, Python-authoritative helper records, Bash-reference parity fixtures, runner metadata refresh, and Layer 4 helper gates, merged via PR #276.
- xplat-006-mutation-install-pr-emission-helper-port: Shipped Python runner mutation primitives, install/doctor fake-home proof, generated PR-body output, deferred command-plan diagnostics for live mutation, autopilot phase-coverage hardening, contract fixtures, and Layer 4 mutation-helper gates, merged via PR #281.
- xplat-007-python-tooling-and-release-gate-migration: Shipped Python-authoritative repo-local suite, payload, install-verification, release-readiness, and active-path guard gates across PRs #284-#287, including CI dispatch updates, promotion records, test payload evidence, no-shell guard coverage, and Layer 4 gate tests; XPLAT-008 is now ready for installed Claude/Codex cutover and public release readiness.
- xplat-008-claude-codex-cutover-universal-install-release-gate: Shipped active Claude/Codex installed-runtime cutover, generated Claude/Codex payload rebuilds, public docs and README claim alignment, release-readiness/UAT/update/repair gates, partial Codex/macOS installed-cache evidence, and safe repair controls across PRs #289-#292; public native-platform claims remain blocked by pending operator UAT rows preserved under `docs/ai/specs/.process/`.
- xplat-009-plugin-source-and-payload-bash-eradication: Shipped plugin-source Bash removal, active-instruction cleanup, generated Claude/Codex payload rebuilds, the zero-Bash guard with installed-cache proof and historical allowlist, and seeded regression coverage via PR #297 (speckit-pro 2.18.0), with Windows interpreter/home resolution fixed in PR #299; repository-wide Bash confinement was completed by XPLAT-010.
- xplat-010-repository-bash-confinement: Shipped manifest-driven Python repository validation, purpose-based parity fixtures, repository Bash confinement, Linux container and advisory Windows preflight, restored spec-size estimation, and deterministic release-note validation/Highlights across PRs #311-#328; T108/T117 hosted evidence is complete, while native platform claims remain held by XPLAT-008 UAT.

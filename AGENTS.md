# Repository Guidelines

## Project Structure & Module Organization

This repository is a Claude Code plugin marketplace. The registry lives in `.claude-plugin/marketplace.json`. Each plugin gets its own top-level directory; today that is `speckit-pro/`.

Inside `speckit-pro/`:

- `commands/` contains slash-command docs with required YAML frontmatter.
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
- `specs/prsg-007-atomicity-router` and `specs/prsg-011-retro-migration` were removed from active `specs/**` cleanup after PR #136 decoupled Layer 4 dogfood/schema tests from the live PRSG-007 spec directory.
- `specs/prsg-008-layer-planner` was removed from active `specs/**` cleanup after the planner schema fixture was vendored under `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/`.
- `specs/prsg-009-multi-pr-emission` was removed from active `specs/**` cleanup after PR #145 merged and the PRSG-009 contract schemas were preserved under `speckit-pro/skills/speckit-autopilot/contracts/`.
- `specs/prsg-010-harden-the-hatch` was removed from active `specs/**` cleanup after PRs #149-#155 merged and the PRSG-010 contract schemas were preserved under `speckit-pro/skills/speckit-autopilot/contracts/`.
- `specs/prsg-005-slice-sizing-heuristics` and `specs/prsg-013-reviewability-markers` were removed from active `specs/**` cleanup after PR #120 and PR #157 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.
- `specs/001-repository-foundation`, `specs/002-pr-checks-workflow`, `specs/003-release-automation`, `specs/004-integration-verification`, `specs/006a-uat-skeleton`, `specs/prsg-002-moc-templates`, `specs/prsg-003-spec-index`, `specs/prsg-004-roadmap-moc-home-note`, `specs/prsg-006-reviewability-budget`, and `specs/prsg-012-reviewer-ready-pr-packet-contract` were removed from active `specs/**` cleanup after merge provenance, recovery commands, and fixture decoupling were recorded in `.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.
- `specs/doc-001-static-docs-framework-and-ia-spike` was removed from active `specs/**` cleanup after PR #163 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md`.
- `specs/doc-002-unified-landing-page-and-ia-shell` was removed from active `specs/**` cleanup after PRs #173-#177 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`.
- `specs/prsg-014-optional-gh-stack-stack-manager-integration` was removed from active `specs/**` cleanup after PR #181 merged and recovery commands were recorded in `.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`.
- `.specify/feature.json` is transient local state. Do not commit a stale completed-spec pointer back to `main`.

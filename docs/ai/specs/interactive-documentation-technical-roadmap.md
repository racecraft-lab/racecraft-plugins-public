# Racecraft Interactive Documentation Implementation Roadmap

> SpecKit-compatible roadmap copy for [../../roadmap-interactive-documentation.md](../../roadmap-interactive-documentation.md). The prompt-requested roadmap is canonical for product review; this file exists so SpecKit tools that search `docs/ai/specs/*roadmap*.md` can discover the DOC-SPEC catalog.
> **Source PRD:** [../../prd-interactive-documentation.md](../../prd-interactive-documentation.md)
> **Roadmap-MOC home note:** [interactive-documentation-roadmap-MOC.md](interactive-documentation-roadmap-MOC.md)
> Status: Ready for SPEC decomposition. Created 2026-06-12.

## Roadmap Overview

The feature is decomposed into 10 specifications across 6 dependency tiers:

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | DOC-SPEC-001 | Static docs framework and IA spike | Sequential |
| 2 | DOC-SPEC-002 | Unified landing and IA shell | Sequential |
| 3 | DOC-SPEC-003, DOC-SPEC-004 | Claude and Codex install paths | Parallel |
| 4 | DOC-SPEC-005, DOC-SPEC-006 | First-run tutorial and safe interactive aids | Parallel |
| 5 | DOC-SPEC-007, DOC-SPEC-008, DOC-SPEC-009 | Reference, troubleshooting/trust, maintainer workflow | Parallel |
| 6 | DOC-SPEC-010 | Search, accessibility, deep links, docs validation | Sequential hardening |

**Execution Order:** DOC-SPEC-001 -> DOC-SPEC-002 -> DOC-SPEC-003/DOC-SPEC-004 -> DOC-SPEC-005/DOC-SPEC-006 -> DOC-SPEC-007/DOC-SPEC-008/DOC-SPEC-009 -> DOC-SPEC-010

## Reviewability Contract

Every spec is a thin documentation-product slice. The `Projected reviewable LOC` values below come from `speckit-pro`'s shared advisory estimator and are forward guesses, not gates.

## Dependency Graph

```text
DOC-SPEC-001
  |
  v
DOC-SPEC-002
  |-----------|
  v           v
DOC-SPEC-003 DOC-SPEC-004
  | \       / |
  |  v     v  |
  | DOC-SPEC-005
  |      |
  v      v
DOC-SPEC-006
  |
  v
DOC-SPEC-007 -> DOC-SPEC-008
        \       /
         v     v
       DOC-SPEC-009
          |
          v
       DOC-SPEC-010
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| DOC-SPEC-001 | Static docs framework and IA spike | Pending | DOC-SPEC-001-workflow.md | Specify |
| DOC-SPEC-002 | Unified landing page and IA shell | Pending | DOC-SPEC-002-workflow.md | Blocked by DOC-SPEC-001 |
| DOC-SPEC-003 | Claude Code marketplace installation path | Pending | DOC-SPEC-003-workflow.md | Blocked by DOC-SPEC-002 |
| DOC-SPEC-004 | Codex marketplace installation path | Pending | DOC-SPEC-004-workflow.md | Blocked by DOC-SPEC-002 |
| DOC-SPEC-005 | First successful workflow tutorial | Pending | DOC-SPEC-005-workflow.md | Blocked by DOC-SPEC-003, DOC-SPEC-004 |
| DOC-SPEC-006 | Safe interactive selector and validation aids | Pending | DOC-SPEC-006-workflow.md | Blocked by DOC-SPEC-002, DOC-SPEC-003, DOC-SPEC-004 |
| DOC-SPEC-007 | Command, workflow, manifest, and file-layout reference | Pending | DOC-SPEC-007-workflow.md | Blocked by DOC-SPEC-003, DOC-SPEC-004 |
| DOC-SPEC-008 | Troubleshooting, security, trust, update, rollback | Pending | DOC-SPEC-008-workflow.md | Blocked by DOC-SPEC-007 |
| DOC-SPEC-009 | Maintainer and contributor release workflow | Pending | DOC-SPEC-009-workflow.md | Blocked by DOC-SPEC-007 |
| DOC-SPEC-010 | Search, accessibility, deep links, docs validation | Pending | DOC-SPEC-010-workflow.md | Blocked by DOC-SPEC-001, DOC-SPEC-002, DOC-SPEC-006 |

## Specification Sections

### DOC-SPEC-001: Static docs framework and IA spike

**Priority:** P1 | **Depends On:** None | **Enables:** DOC-SPEC-002

**Goal:** Select the static docs-site stack and IA foundation with evidence.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 |
Production files: 0 |
Total files: 1-2 |
Budget result: spike, LOC not applicable

**Scope:**
- Compare Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback.
- Record package manager, build, validation, hosting, search, versioning, accessibility, and maintenance tradeoffs.
- Draft Diataxis IA skeleton and recommend the site stack.

**Out of Scope:**
- Implementing the site.
- Migrating README content.

**Key Files:**
- `docs/prd-interactive-documentation.md` - Source requirements.
- `docs/roadmap-interactive-documentation.md` - Prompt-requested roadmap.
- `docs/ai/research/interactive-documentation-framework-spike.md` - Likely spike output.

### DOC-SPEC-002: Unified landing page and IA shell

**Priority:** P1 | **Depends On:** DOC-SPEC-001 | **Enables:** DOC-SPEC-003, DOC-SPEC-004, DOC-SPEC-006, DOC-SPEC-010

**Goal:** Create the static docs shell, landing page, nav, and task-first IA.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 325 |
Production files: 0 |
Total files: about 5 |
Budget result: within budget

**Scope:**
- Create chosen static-site foundation and top-level docs routes.
- Build landing page that explains Racecraft Public Plugins, `speckit-pro`, supported platforms, and next paths.
- Add glossary seed and source-vs-generated-payload explanation.

**Out of Scope:**
- Full platform install content.
- Interactive widgets beyond basic navigation.

**Key Files:**
- Future site config and docs content paths from DOC-SPEC-001.
- `README.md` and `speckit-pro/README.md` as source evidence.

### DOC-SPEC-003: Claude Code marketplace installation path

**Priority:** P1 | **Depends On:** DOC-SPEC-002 | **Enables:** DOC-SPEC-005, DOC-SPEC-007, DOC-SPEC-008

**Goal:** Ship Claude-specific install/update/remove and invocation docs.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 285 |
Production files: 0 |
Total files: about 4 |
Budget result: within budget

**Scope:**
- Document `/plugin marketplace add racecraft-lab/racecraft-plugins-public`.
- Document `/plugin install speckit-pro@racecraft-plugins-public`.
- Explain `/speckit-pro:*` namespacing, skills, agents, hooks, MCP/settings, managed marketplaces, and legacy/current command-folder wording.

**Out of Scope:**
- Codex install path.
- Full troubleshooting matrix.

**Key Files:**
- `.claude-plugin/marketplace.json`
- `speckit-pro/.claude-plugin/plugin.json`
- `dist/claude/speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/agents/`
- `speckit-pro/hooks/hooks.json`

### DOC-SPEC-004: Codex marketplace installation path

**Priority:** P1 | **Depends On:** DOC-SPEC-002 | **Enables:** DOC-SPEC-005, DOC-SPEC-007, DOC-SPEC-008

**Goal:** Ship Codex-specific install/update/remove and custom-agent registration docs.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 340 |
Production files: 0 |
Total files: about 5 |
Budget result: within budget

**Scope:**
- Document repo/personal/CLI marketplace paths and generated Codex payload use.
- Explain `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, plugin cache behavior, `$install`, `@SpecKit Pro -> install`, `.codex/agents`, `~/.codex/agents`, restart, sandbox, approvals, and network access.
- Validate personal marketplace path examples against official Codex docs.

**Out of Scope:**
- Claude install path.
- Changing Codex manifests or install behavior.

**Key Files:**
- `.agents/plugins/marketplace.json`
- `speckit-pro/.codex-plugin/plugin.json`
- `dist/codex/speckit-pro/.codex-plugin/plugin.json`
- `speckit-pro/codex-skills/install/SKILL.md`
- `speckit-pro/codex-agents/`
- `speckit-pro/codex-hooks.json`

### DOC-SPEC-005: First successful workflow tutorial and lifecycle explainer

**Priority:** P1 | **Depends On:** DOC-SPEC-003, DOC-SPEC-004 | **Enables:** DOC-SPEC-006, DOC-SPEC-008

**Goal:** Guide a user through one successful `speckit-pro` workflow.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 340 |
Production files: 0 |
Total files: about 5 |
Budget result: within budget

**Scope:**
- Explain idea -> PRD -> roadmap -> scaffold -> autopilot lifecycle.
- Include platform-specific first-run commands and prerequisite checks.
- Provide a static fallback lifecycle diagram.
- Validate Codex vs Claude Spec Kit init guidance.

**Out of Scope:**
- Full reference table for every skill.
- Browser-executed plugin runs.

**Key Files:**
- `speckit-pro/README.md`
- `speckit-pro/skills/speckit-prd/SKILL.md`
- `speckit-pro/skills/grill-me/SKILL.md`
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`
- `speckit-pro/skills/speckit-autopilot/SKILL.md`
- Codex skill mirrors.

### DOC-SPEC-006: Safe interactive selector and validation aids

**Priority:** P1 | **Depends On:** DOC-SPEC-002, DOC-SPEC-003, DOC-SPEC-004 | **Enables:** DOC-SPEC-010

**Goal:** Add safe interactive docs aids without executing local plugin workflows.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 380 |
Production files: 0 |
Total files: about 6 |
Budget result: within budget

**Scope:**
- Platform/path selector and install-scope selector.
- Copyable command blocks with platform labels.
- Manifest/version checker using checked-in JSON values.
- Generated payload diagram and first-run checklist.
- Static fallbacks and keyboard-accessible controls.

**Out of Scope:**
- Live local doctor command.
- Auto-editing user config.

**Key Files:**
- Site component paths from DOC-SPEC-001.
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- Source/dist plugin manifests.

### DOC-SPEC-007: Command, workflow, manifest, and file-layout reference

**Priority:** P2 | **Depends On:** DOC-SPEC-003, DOC-SPEC-004 | **Enables:** DOC-SPEC-008, DOC-SPEC-009

**Goal:** Provide stable reference pages for all plugin and repo surfaces.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 380 |
Production files: 0 |
Total files: about 6 |
Budget result: within budget

**Scope:**
- Command/skill matrix for Claude and Codex.
- Manifest and marketplace reference.
- File-layout reference for source-only, dist-only, test-only, and generated files.
- Reference pages for agents/subagents, hooks, MCP/config, scripts, tests, and CI.

**Out of Scope:**
- Step-by-step tutorials.
- Live generated reference tables unless separately justified.

**Key Files:**
- `speckit-pro/skills/**/SKILL.md`
- `speckit-pro/codex-skills/**/SKILL.md`
- `speckit-pro/agents/`
- `speckit-pro/codex-agents/`
- `scripts/`
- `tests/speckit-pro/`

### DOC-SPEC-008: Troubleshooting, security, trust, update, rollback

**Priority:** P1 | **Depends On:** DOC-SPEC-003, DOC-SPEC-004, DOC-SPEC-007 | **Enables:** DOC-SPEC-010

**Goal:** Help users diagnose failures and evaluate plugin trust boundaries.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 380 |
Production files: 0 |
Total files: about 6 |
Budget result: within budget

**Scope:**
- Symptom-driven troubleshooting for install, path, cache, permission, version, CLI, and custom-agent issues.
- Security/trust model for source, generated payloads, installed cache, hooks, MCP, agents/custom agents, sandbox, approvals, and managed policy.
- Update/remove/rollback guidance.

**Out of Scope:**
- Security audit of plugin code.
- New local diagnostics command.

**Key Files:**
- `README.md`
- `speckit-pro/README.md`
- `speckit-pro/codex-hooks.json`
- `speckit-pro/hooks/hooks.json`
- Marketplace and plugin manifests.

### DOC-SPEC-009: Maintainer and contributor release workflow

**Priority:** P1 | **Depends On:** DOC-SPEC-007 | **Enables:** DOC-SPEC-010

**Goal:** Give contributors a release-ready checklist for docs/plugin changes.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 380 |
Production files: 0 |
Total files: about 6 |
Budget result: within budget

**Scope:**
- Source edit, payload rebuild, marketplace sync, tests, CI, release-please, conventional commits, and PR body expectations.
- Explain docs-only PR behavior and future docs-site CI.
- Surface `build-plugin-payloads.sh`, `sync-marketplace-versions.sh`, and `tests/speckit-pro/run-all.sh`.

**Out of Scope:**
- Changing CI/release behavior.
- Duplicating all CLAUDE.md internals.

**Key Files:**
- `AGENTS.md`
- `CLAUDE.md`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/release.yml`
- `scripts/build-plugin-payloads.sh`
- `scripts/sync-marketplace-versions.sh`

### DOC-SPEC-010: Search, accessibility, deep links, docs validation

**Priority:** P2 | **Depends On:** DOC-SPEC-001, DOC-SPEC-002, DOC-SPEC-006 | **Enables:** Feature complete

**Goal:** Harden the docs site so it is findable, accessible, linkable, responsive, and validated in CI.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 395 |
Production files: 0 |
Total files: about 6 |
Budget result: within budget

**Scope:**
- Search/glossary/deep-link conventions.
- Accessibility and responsive checks for interactive components.
- Docs CI for site build, markdown lint, link checks, manifest/payload consistency, safe command-snippet validation, and visual/regression checks when feasible.

**Out of Scope:**
- Full analytics instrumentation.
- Live install tests in CI.

**Key Files:**
- Site config and docs validation config from DOC-SPEC-001.
- `.github/workflows/pr-checks.yml` if docs CI is added.
- Existing validation scripts where reusable.

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Current docs | Markdown files in repo root, `docs/`, `docs/ai/specs/`, and `speckit-pro/README.md`. |
| Current site tooling | No `package.json`, lockfile, or known static site config found in this checkout. |
| Existing validation | Shell-based repo tests under `tests/speckit-pro/`, plus marketplace/payload scripts. |
| Product-code constraint | This roadmap changes documentation planning and future docs-site files only; no plugin behavior changes. |

## References

- Source PRD: [../../prd-interactive-documentation.md](../../prd-interactive-documentation.md)
- Prompt roadmap: [../../roadmap-interactive-documentation.md](../../roadmap-interactive-documentation.md)
- Traceability matrix: [../../traceability-interactive-documentation.md](../../traceability-interactive-documentation.md)
- Roadmap-MOC home note: [interactive-documentation-roadmap-MOC.md](interactive-documentation-roadmap-MOC.md)


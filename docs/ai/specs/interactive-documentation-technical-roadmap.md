# Racecraft Interactive Documentation Implementation Roadmap

> **Authoritative SPEC catalog** for the Interactive Documentation initiative — the single source of truth for the DOC-001 through DOC-021 spec list, dependency tiers, dependency graph, and launch sequencing (SpecKit tools discover the catalog here). The [product-review companion](../../roadmap-interactive-documentation.md) carries the higher-level framing (autopilot-ready property, validation strategy, cut list) and points back here for the catalog.
> **Source PRD:** [../../prd-interactive-documentation.md](../../prd-interactive-documentation.md)
> **Roadmap-MOC home note:** [interactive-documentation-roadmap-MOC.md](interactive-documentation-roadmap-MOC.md)
> Status: DOC-001 through DOC-011 are complete and archived. **Phase 7 production-readiness specs DOC-012 - DOC-018 and Phase 8 content/IA-excellence specs DOC-019 - DOC-021 are PENDING** — added 2026-06-19 from a production-deployment audit, a live per-route preview review of all pages, and a cited deep-research report on best-in-class Astro/Starlight docs. The site builds, is CI-validated, and has a deploy-ready GitHub Pages staging workflow with a noindex guard; repository Pages still requires the documented manual Settings -> Pages setup before the first successful publication. Created 2026-06-12; refreshed 2026-06-23.

## Roadmap Overview

The feature is decomposed into 21 specifications across 8 dependency tiers (Tiers 1-6 = content + IA, shipped; Tier 7 = production readiness, Tier 8 = content/IA excellence — both pending):

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | DOC-001 | Static docs framework and IA spike | Sequential |
| 2 | DOC-002 | Unified landing and IA shell | Sequential |
| 3 | DOC-003, DOC-004 | Claude and Codex install paths | Parallel |
| 4 | DOC-005, DOC-006 | First-run tutorial and safe interactive aids | Parallel |
| 5 | DOC-007, DOC-008, DOC-009 | Reference, troubleshooting/trust, maintainer workflow | Parallel |
| 6 | DOC-010 | Search, accessibility, deep links, docs validation | Sequential hardening |
| 7 | DOC-011 - DOC-018 | Production readiness: deploy, custom domain, branding/landing, SEO, editorial, accessibility, performance, launch hygiene | DOC-011 shipped; remaining specs are mostly parallel after deploy + domain constraints |
| 8 | DOC-019 - DOC-021 | Content/IA excellence: voice & ELI5 tone, per-page value & right-sizing, task-based IA & wayfinding | Mostly parallel |

**Execution Order:** DOC-001 -> DOC-002 -> DOC-003/DOC-004 -> DOC-005/DOC-006 -> DOC-007/DOC-008/DOC-009 -> DOC-010 -> **[Phase 7]** DOC-011 (deploy + noindex) -> (DOC-013, DOC-014, DOC-015) -> (DOC-016, DOC-017) -> DOC-018 -> **[Phase 8]** DOC-019 -> DOC-020 ; DOC-021 -> **[Launch gate — DEAD LAST]** DOC-012 (flip to root, attach plugins.racecraft.co, remove noindex)

**Public-exposure policy:** GitHub Pages is publicly reachable the moment DOC-011 deploys, so DOC-011 ships the site with a search-engine `noindex` + `robots` disallow and keeps it on the obscure `racecraft-lab.github.io/racecraft-plugins-public/` staging URL throughout build-out — reachable for team preview, but not indexed or discoverable. **DOC-012 is intentionally DEAD LAST**: attaching the custom domain and removing `noindex` is the single go-live action that makes the site overtly public, gated behind every content, branding, SEO, and accessibility spec.

## Reviewability Contract

Every spec is a thin documentation-product slice. The `Projected reviewable LOC` values below come from `speckit-pro`'s shared advisory estimator and are forward guesses, not gates.

## Dependency Graph

```text
DOC-001
  |
  v
DOC-002
  |-----------|
  v           v
DOC-003 DOC-004
  | \       / |
  |  v     v  |
  | DOC-005
  |      |
  v      v
DOC-006
  |
  v
DOC-007 -> DOC-008
        \       /
         v     v
       DOC-009
          |
          v
       DOC-010
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| DOC-001 | Static docs framework and IA spike | Completed/archived | DOC-001-workflow.md | Archived after PR #163 |
| DOC-002 | Unified landing page and IA shell | Completed/archived | `.process/DOC-002-workflow.md` | Archived after PRs #173-#177 |
| DOC-003 | Claude Code marketplace installation path | Completed/archived | `.process/DOC-003-workflow.md` | Archived after PR #187 |
| DOC-004 | Codex marketplace installation path | Completed/archived | `.process/DOC-004-workflow.md` | Archived after PR #186 |
| DOC-005 | First successful workflow tutorial | Completed/archived | DOC-005-workflow.md | Archived after PRs #198-#201 |
| DOC-006 | Safe interactive selector and validation aids | Completed/archived | `.process/DOC-006-workflow.md` | Archived after PR #203 |
| DOC-007 | Command, workflow, manifest, and file-layout reference | Completed/archived | `.process/DOC-007-workflow.md` | Archived after PR #208 |
| DOC-008 | Troubleshooting, security, trust, update, rollback | Completed/archived | `.process/DOC-008-workflow.md` | Archived after PR #220 |
| DOC-009 | Maintainer and contributor release workflow | Completed/archived | `.process/DOC-009-workflow.md` | Archived after PR #219 |
| DOC-010 | Search, accessibility, deep links, docs validation | Completed/archived | `.process/DOC-010-workflow.md` | Archived after PRs #232-#236 |
| DOC-011 | GitHub Pages build-and-deploy pipeline | Completed/archived | `.process/DOC-011-workflow.md` | Archived after PR #243 |
| DOC-012 | Custom domain + base-path migration to plugins.racecraft.co | ⏳ Pending | — | **LAST — public launch gate**; runs after all other DOC specs (P1) |
| DOC-013 | Brand identity and marketplace landing page | ⏳ Pending | — | Not started — production readiness (P1) |
| DOC-014 | SEO and AI discoverability | ⏳ Pending | — | Not started — staging deploy foundation exists from DOC-011; URLs finalize at DOC-012 launch (P1) |
| DOC-015 | Editorial and content-QA pass | ⏳ Pending | — | Not started — production readiness (P1) |
| DOC-016 | WCAG 2.1 AA accessibility hardening | ⏳ Pending | — | Not started — depends on DOC-013 (P2) |
| DOC-017 | Performance budget and Lighthouse CI | ⏳ Pending | — | Not started — depends on DOC-013/014 plus the shipped DOC-011 deploy foundation (P2) |
| DOC-018 | Launch hygiene: analytics, 404, legal, contributor onboarding | ⏳ Pending | — | Not started — uses the shipped DOC-011 deploy foundation and activates at DOC-012 launch (P3) |
| DOC-019 | Content voice and ELI5 tone system | ⏳ Pending | — | Not started — depends on DOC-015 (P1) |
| DOC-020 | Per-page value alignment and right-sizing | ⏳ Pending | — | Not started — depends on DOC-019 (P2) |
| DOC-021 | Task-based information architecture and wayfinding | ⏳ Pending | — | Not started — depends on DOC-013 (P2) |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

## Specification Sections

### DOC-001: Static docs framework and IA spike

**Priority:** P1 | **Depends On:** None | **Enables:** DOC-002

**Status:** Completed and archived after PR #163. Canonical decision record: `docs/ai/research/interactive-documentation-framework-spike.md`.

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
- `docs/ai/research/interactive-documentation-framework-spike.md` - Completed framework recommendation and IA decision record.
- `.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md` - Archive provenance and raw artifact recovery commands.

### DOC-002: Unified landing page and IA shell

**Priority:** P1 | **Depends On:** DOC-001 completed | **Enables:** DOC-003, DOC-004, DOC-006, DOC-010

**Status:** Completed and archived after PRs #173-#177. Canonical site shell lives in `docs-site/`; archive provenance is recorded in `.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`.

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
- `docs-site/` shell, route content, sidebar config, Pages-ready Astro config, and link-validation scripts created by DOC-002.
- `README.md` and `speckit-pro/README.md` as source evidence.

### DOC-003: Claude Code marketplace installation path

**Priority:** P1 | **Depends On:** DOC-002 | **Enables:** DOC-005, DOC-007, DOC-008

**Status:** Completed and archived after PR #187. Canonical Claude install guidance lives in `docs-site/src/content/docs/install/claude-code.md`; archive provenance is recorded in `.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md`.

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

### DOC-004: Codex marketplace installation path

**Priority:** P1 | **Depends On:** DOC-002 | **Enables:** DOC-005, DOC-007, DOC-008

**Status:** Completed and archived after PR #186. Canonical Codex install guidance lives in `docs-site/src/content/docs/install/codex.md`; archive provenance is recorded in `.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md`.

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

### DOC-005: First successful workflow tutorial and lifecycle explainer

**Priority:** P1 | **Depends On:** DOC-003, DOC-004 | **Enables:** DOC-006, DOC-008

**Status:** Completed and archived after PRs #198-#201. Canonical first-run and
lifecycle routes live in `docs-site/src/content/docs/first-run.md` and
`docs-site/src/content/docs/spec-kit-lifecycle.mdx`; archive provenance is
recorded in `.specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md`.

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

### DOC-006: Safe interactive selector and validation aids

**Priority:** P1 | **Depends On:** DOC-002, DOC-003, DOC-004 | **Enables:** DOC-010

**Status:** Completed and archived after PR #203. Canonical safe install aids live in `docs-site/src/content/docs/choose-your-path.mdx`, `docs-site/src/components/SafeInstallAids.astro`, `docs-site/src/data/safe-install-aids.ts`, and `docs-site/scripts/validate-doc006-safe-aids.mjs`; archive provenance is recorded in `.specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md`.

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
- DOC-002 site component paths after the Astro/Starlight shell exists.
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- Source/dist plugin manifests.

### DOC-007: Command, workflow, manifest, and file-layout reference

**Priority:** P2 | **Depends On:** DOC-003, DOC-004 | **Enables:** DOC-008, DOC-009

**Status:** Completed and archived after PR #208. Canonical generated reference pages live in `docs-site/src/content/docs/reference/`, with generation logic in `docs-site/scripts/generate-reference-pages.mjs`; archive provenance is recorded in `.specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md`.

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

### DOC-008: Troubleshooting, security, trust, update, rollback

**Priority:** P1 | **Depends On:** DOC-003, DOC-004, DOC-007 | **Enables:** DOC-010

**Status:** Completed and archived after PR #220. Canonical docs live in
`docs-site/src/content/docs/troubleshooting.md`,
`docs-site/src/content/docs/security-and-trust.md`,
`docs-site/src/content/docs/update-and-rollback.md`, and linked install/reference
routes; archive provenance is recorded in
`.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.

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

### DOC-009: Maintainer and contributor release workflow

**Priority:** P1 | **Depends On:** DOC-007 | **Enables:** DOC-010

**Status:** Completed and archived after PR #219. Canonical docs live in
`docs-site/src/content/docs/contribute-and-release.md`; archive provenance is
recorded in
`.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.

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

### DOC-010: Search, accessibility, deep links, docs validation

**Priority:** P2 | **Depends On:** DOC-001, DOC-002, DOC-006 | **Enables:** Feature complete

**Status:** Completed and archived after PRs #232-#236. Canonical docs-site
validation, support anchor, accessibility/fallback, PR Checks docs-gate, and
compact smoke evidence lives in `docs-site/` and `.github/workflows/pr-checks.yml`;
archive provenance is recorded in
`.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md`.

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
- DOC-002 site config and DOC-010 docs validation config after the Astro/Starlight shell exists.
- `.github/workflows/pr-checks.yml` if docs CI is added.
- Existing validation scripts where reusable.

## Phase 7 — Production Readiness (DOC-011 - DOC-018)

> Added 2026-06-19 from a production-deployment audit (PRD + technical roadmap cross-check plus a live per-page visual review of the running site). DOC-001 - DOC-010 delivered a *content + IA* product; these specs deliver a *deployed, branded, discoverable, accessible* product. Per the Reviewability Contract these are documentation/infra slices — low production-LOC, docs/config/CI heavy.

### DOC-011: GitHub Pages build-and-deploy pipeline

**Priority:** P1 | **Depends On:** DOC-010 (site builds + validates) | **Enables:** staged (noindex) preview of every later spec; DOC-012 go-live

**Status:** Completed and archived after PR #243. Canonical implementation now lives in `.github/workflows/deploy-docs.yml`, the staging noindex/robots guard under `docs-site/`, and the CI/CD verification runbook at `docs/ai/specs/cicd-release-pipeline-verification.md`. The first post-merge Deploy Docs run failed because repository Pages was not yet enabled/configured for GitHub Actions; that is the documented manual operator prerequisite before expecting publication. The guard is removed only by DOC-012 at go-live.

**Goal:** Continuously build and deploy `docs-site/` to GitHub Pages so the documentation is reachable at a live URL.

**Reviewability Budget:** Primary surface: harness/CI |
Projected reviewable LOC: about 60 |
Final production reviewable LOC: 36 |
Final production files: 2 |
Final total files: 54 |
Budget result: archived as one review-remediation slice after PR #243

**Scope:**
- Add `.github/workflows/deploy-docs.yml` using `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages`, with `permissions: pages: write, id-token: write` and a `github-pages` environment.
- Trigger on push to `main` (path-filtered to `docs-site/**` and generated-reference sources) plus `workflow_dispatch`; build under Node >=22.12 with pnpm; gate deploy on `pnpm --dir docs-site validate`.
- Enable Pages with source = GitHub Actions (or `enablement: true`) and document the one-time repo setting.
- Ship a build-out `noindex` guard: a `robots.txt` disallow plus `<meta name="robots" content="noindex, nofollow">` (via Starlight `head`) so the staging site is not indexed or discoverable; DOC-012 removes it at launch.
- Add a deploy runbook note to `docs/ai/specs/cicd-release-pipeline-verification.md` and a CLAUDE.md CI/CD note.

**Out of Scope:**
- Custom domain and DNS (DOC-012).
- Branding, SEO, analytics (DOC-013/014/018).

**Key Files:**
- `.github/workflows/deploy-docs.yml` (new)
- `docs-site/package.json` build/validate scripts
- `docs/ai/specs/cicd-release-pipeline-verification.md`

### DOC-012: Custom domain and base-path migration to plugins.racecraft.co

**Priority:** P1 (LAST — public launch gate) | **Depends On:** DOC-011 and all content/branding/SEO/a11y specs (DOC-013 - DOC-021) launch-ready | **Enables:** public go-live

**Status:** Pending. `astro.config.mjs` is pinned to `site: 'https://racecraft-lab.github.io'` and `base: '/racecraft-plugins-public'`. The base prefix is hardcoded across ~20 content files, in `generate-reference-pages.mjs` (the `Public path` line), and in `validate-docs-quality.mjs` fixtures (`SUPPORT_ANCHOR_INVENTORY`, `REQUIRED_SUPPORT_LINKS`). Target: serve at the root of `plugins.racecraft.co`; DNS will be a CNAME at Epik (decision: not Route53). **This spec is deliberately DEAD LAST** — it is the single go-live flip (attach the domain + remove the DOC-011 `noindex` guard), so it runs only after every other DOC spec is launch-ready, ensuring the site is not overtly public until then.

**Goal:** Serve the docs at the root of `plugins.racecraft.co` with correct links, DNS, and validation.

**Reviewability Budget:** Primary surface: docs/config |
Projected reviewable LOC: about 0 (config + link rewrites) |
Production files: 0 |
Total files: about 24 |
Budget result: within budget (docs/config heavy, low production LOC)

**Scope:**
- Set `site: 'https://plugins.racecraft.co'` and remove/blank `base` in `astro.config.mjs`.
- Migrate every hardcoded `/racecraft-plugins-public/...` link in content, the reference generator, and the quality-validator fixtures — prefer a single base-aware helper over scattered literals.
- Add `docs-site/public/CNAME` = `plugins.racecraft.co`; document the Epik CNAME record (`plugins` -> `racecraft-lab.github.io`) and enabling Enforce HTTPS.
- Remove the DOC-011 `noindex`/`robots`-disallow guard and switch `robots.txt` to allow indexing — this is the go-live moment that makes the site publicly discoverable.
- Re-run `pnpm --dir docs-site validate` to prove zero broken internal links after migration.

**Out of Scope:**
- Route53 / DNS migration of the apex (decision: stay on Epik).
- Redirects from the old `/racecraft-plugins-public` path (note as a follow-up if needed).

**Key Files:**
- `docs-site/astro.config.mjs`
- `docs-site/public/CNAME` (new)
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/scripts/validate-docs-quality.mjs`
- `docs-site/src/content/docs/**` (link rewrites)

### DOC-013: Brand identity and marketplace landing page

**Priority:** P1 | **Depends On:** DOC-002 | **Enables:** DOC-016 (contrast), public launch

**Status:** Pending. The site is stock Starlight — `astro.config.mjs` has no `customCss`, `logo`, `favicon`, `head`, or fonts, and there is no `docs-site/public/`. Visual review confirmed default blue/lavender accent, system font, no logo, and no hero in both light and dark mode; the landing route renders as a generic "Start" doc page, not a marketplace landing. A full brand kit already exists in the sibling `landing-page/website`.

**Goal:** Apply Racecraft visual identity and turn the landing route into a real marketplace landing page.

**Reviewability Budget:** Primary surface: docs/UI |
Projected reviewable LOC: about 80 (CSS) |
Production files: 1-2 (brand CSS) |
Total files: 6-8 plus binary font/favicon assets |
Budget result: within budget

**Scope:**
- Create `docs-site/public/`; port the favicon set and `site.webmanifest` from `landing-page/website/public/`.
- Add `docs-site/src/styles/brand.css` mapping brand colors (red `#dc143c`, blue `#3c89c6`, orange `#e74900`) to Starlight `--sl-color-*` tokens for light and dark; wire via `customCss`.
- Self-host Space Grotesk / Geist / Fira Code woff2 (port from sibling); set Starlight font tokens with `<link rel=preload>`.
- Set `logo` + `favicon` in the Starlight config; add a branded hero / value-prop block to the landing route so it reads as a marketplace entry point, not a doc.

**Out of Scope:**
- Per-component restyle beyond tokens (a11y component fixes are DOC-016).
- Performance budget (DOC-017).

**Key Files:**
- `docs-site/astro.config.mjs`
- `docs-site/src/styles/brand.css` (new)
- `docs-site/public/` favicon/font assets (new)
- `docs-site/src/content/docs/index.mdx`
- Brand source: `landing-page/website/public/` and `astro.config.mjs`

### DOC-014: SEO and AI discoverability

**Priority:** P1 | **Depends On:** DOC-011 (canonical/sitemap URLs derive from astro `site` and finalize automatically when DOC-012 flips the domain at launch) | **Enables:** public launch

**Status:** Pending. 0 of 19 content pages carry `description:` frontmatter (no meta descriptions); there is no Open Graph / social-card setup, no `robots.txt`, no `llms.txt`, and no canonical-URL handling for the final domain. The sibling site already ships `astro-llms-txt`, a sitemap, and `robots.txt`.

**Goal:** Make the docs indexable, shareable, and AI-discoverable with correct metadata for the production domain.

**Reviewability Budget:** Primary surface: docs/config + content |
Projected reviewable LOC: about 40 |
Production files: 0 |
Total files: about 22 (frontmatter + config) |
Budget result: within budget

**Scope:**
- Add `description:` frontmatter to all content pages; add a `validate-docs-quality.mjs` rule requiring it.
- Add Open Graph / social-card metadata and canonical URLs for `plugins.racecraft.co` (Starlight `head` or a card component).
- Verify/emit a correct sitemap for the final domain and add `robots.txt` pointing at it.
- Add `llms.txt` (port the three-tier `astro-llms-txt` pattern from the sibling site).

**Out of Scope:**
- Analytics (DOC-018).
- Prose rewrites (DOC-015).

**Key Files:**
- `docs-site/astro.config.mjs`
- `docs-site/src/content/docs/**` (frontmatter)
- `docs-site/scripts/validate-docs-quality.mjs`
- `docs-site/public/robots.txt` (new)

### DOC-015: Editorial and content-QA pass

**Priority:** P1 | **Depends On:** None | **Enables:** public launch

**Status:** Pending. Visual review confirmed internal-authoring leakage in rendered pages: "Route Scope" / "Shell owner DOC: DOC-002" / "Full-content owner DOC" on the landing and `choose-your-path`, "Deferred Boundary" on `choose-your-path`, and generator mechanics ("Generated by ...", "Public path:", "Page Sources", title-cased "Speckit Prd") on the reference pages. Also: gate numbering shows G1-G7 while the autopilot source uses G0-G7; "Spec Kit" vs "SpecKit" drift; and `first-run.md` uses `specify version` vs the verified `specify --version`. `validate-docs-quality.mjs` checks structure, not prose.

**Goal:** Make the public docs read cleanly and accurately by removing internal scaffolding and fixing factual drift.

**Reviewability Budget:** Primary surface: docs/content |
Projected reviewable LOC: about 30 (editorial linter) |
Production files: 0 |
Total files: 8-10 |
Budget result: within budget

**Scope:**
- Strip internal scaffolding from rendered pages ("Route Scope" / "Route Shell", "owner DOC", "Deferred Boundary"); move any needed provenance to frontmatter/comments.
- Reframe the generated reference pages for a public reader (drop or collapse generator mechanics, internal source paths, and base-path lines; fix title-casing such as "SpecKit PRD" / "SpecKit Resolve PR").
- Reconcile gate numbering to G0-G7 in `spec-kit-lifecycle.mdx`; normalize "Spec Kit" vs "SpecKit" to one deliberate convention; fix `specify version` -> `specify --version`.
- Add an editorial linter to `validate-docs-quality.mjs` (deny-list of internal tokens like `DOC-0\d\d`, "owner DOC", "Deferred Boundary") so leaks cannot recur.

**Out of Scope:**
- IA restructuring or new pages.
- Reconciling the same `specify version` drift in plugin source (flag separately).

**Key Files:**
- `docs-site/src/content/docs/index.mdx`, `choose-your-path.mdx`, `spec-kit-lifecycle.mdx`, `first-run.md`
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/scripts/validate-docs-quality.mjs`

### DOC-016: WCAG 2.1 AA accessibility hardening

**Priority:** P2 | **Depends On:** DOC-013 (brand contrast), DOC-010 (smoke harness) | **Enables:** PRD AC-10.2

**Status:** Pending. Today's a11y is smoke-tested only — no axe-core, no contrast verification. `SafeInstallAids.astro` reimplements radiogroup keyboard navigation with a custom `keydown` handler over loose `<input type=radio>` (no `role="radiogroup"`) and toggles `panel.hidden` with no `aria-controls` / `aria-expanded`. PRD AC-10.2 requires keyboard, focus, label, contrast, and static-fallback conformance; only static-fallback + basic keyboard are verified.

**Goal:** Replace smoke-only a11y with verified WCAG 2.1 AA conformance and fix the custom-widget semantics.

**Reviewability Budget:** Primary surface: docs/UI + tests |
Projected reviewable LOC: about 70 |
Production files: 1 (component fix) |
Total files: 4-5 |
Budget result: within budget

**Scope:**
- Add `@axe-core/playwright` checks across the route list in `docs-smoke.spec.mjs`; wire into `validate:smoke`.
- Fix `SafeInstallAids.astro`: proper `role="radiogroup"` / `<fieldset>` semantics, reconcile or remove the custom `keydown` handler, and add `aria-controls` / `aria-expanded` (or a non-`hidden` pattern) for panel toggles.
- Verify brand-token contrast (post-DOC-013) meets AA; fix muted-gray secondary text flagged on the lifecycle and selector components.
- Add an accessibility-statement page.

**Out of Scope:**
- Manual screen-reader certification (advisory).

**Key Files:**
- `docs-site/src/components/SafeInstallAids.astro`, `LifecycleFlow.astro`
- `docs-site/tests/docs-smoke.spec.mjs`
- `docs-site/package.json`

### DOC-017: Performance budget and Lighthouse CI

**Priority:** P2 | **Depends On:** DOC-011, DOC-013, DOC-014 | **Enables:** PRD AC-10.7

**Status:** Pending. No Lighthouse config or perf budget exists in `docs-site` (the sibling site has `lighthouserc.json`). Branding will add fonts/assets, so a budget is needed to prevent regression. PRD AC-10.7 ("visual regression or screenshot checks required once the site exists") is also unmet — the current smoke test checks element presence, not visual baselines.

**Goal:** Guard load performance and core-web-vitals with a CI budget once branding/fonts land.

**Reviewability Budget:** Primary surface: harness/CI |
Projected reviewable LOC: about 30 |
Production files: 0 |
Total files: 2-3 |
Budget result: within budget

**Scope:**
- Add `lighthouserc.json` + a Lighthouse CI step (port the sibling config) asserting perf/SEO/a11y/best-practices thresholds against the built preview.
- Confirm font-loading strategy (preload + `font-display`) and optimize any images.
- Add visual-regression / screenshot baselines to satisfy PRD AC-10.7.

**Out of Scope:**
- RUM / real-user analytics (DOC-018).

**Key Files:**
- `docs-site/lighthouserc.json` (new)
- `.github/workflows/deploy-docs.yml` or a docs-CI job
- `docs-site/tests/`

### DOC-018: Launch hygiene — analytics, 404, legal, docs contributor onboarding

**Priority:** P3 | **Depends On:** DOC-011 (analytics is configured here but activates at DOC-012 go-live) | **Enables:** Feature complete

**Status:** Pending. The PRD deferred analytics "until the site foundation and hosting path exist" — that precondition is now met but the work is unstarted. There is no branded 404 page, no repo `LICENSE` / privacy notice, and `contribute-and-release.md` has no docs-site contributor section (how to run/preview/add a page).

**Goal:** Close the remaining production-hygiene items now that hosting and domain exist.

**Reviewability Budget:** Primary surface: docs/content + config |
Projected reviewable LOC: about 20 |
Production files: 0 |
Total files: 5-6 |
Budget result: within budget

**Scope:**
- Add a privacy-respecting analytics option (documented choice; PRD gated this on hosting, now satisfied).
- Add a branded `src/pages/404.astro` (or Starlight 404 override).
- Add a repo `LICENSE` and a short privacy notice page.
- Extend `contribute-and-release.md` with a docs-site contributor section (`pnpm --dir docs-site dev`, adding a page, passing `validate`).

**Out of Scope:**
- Docs versioning (defer until a breaking plugin-docs change forces it).

**Key Files:**
- `docs-site/src/pages/404.astro` (new)
- `docs-site/src/content/docs/contribute-and-release.md`
- `LICENSE` (new), privacy notice page

## Phase 8 — Content & IA Excellence (DOC-019 - DOC-021)

> Added 2026-06-19 from (a) a live per-route preview audit of all 19 navigable pages and (b) a cited deep-research report on the best Astro/Starlight and developer-tool doc sites.
>
> **Exemplars to study** (verified real Astro/Starlight or best-in-class doc sites): Cloudflare Docs, Netlify Docs, freeCodeCamp, Biome, Knip, sharp, Font Awesome, OpenAI Agents SDK (all Starlight); Stripe (task-oriented landing + business-function IA); Google developer documentation style guide (non-condescending tone rules); Fern + Nielsen Norman Group (task-based IA, progressive disclosure).
>
> **Verified principles a stock Starlight site lacks:** organize IA around user goals/tasks, not raw Diátaxis labels or internal structure; lead the landing above the fold with use-case quick-start cards (Stripe); progressive disclosure via accordions (sequential), tabs (parallel paths, e.g. Claude vs Codex), and collapsible sidebar groups (Fern, NN/g); a "knowledgeable friend" voice — conversational, friendly, respectful, not pedantic or pushy — with a lint rule banning "simply / easy / just / quickly / it's that simple" (Google). Accessibility targets are falsifiable WCAG 2.2 AA thresholds: 4.5:1 / 3:1 contrast (SC 1.4.3), 200% text resize (SC 1.4.4), full keyboard operability (SC 2.1.1). Note: 320px / 400% reflow is the separate, stricter SC 1.4.10 — do not assert it as an AA baseline. Search (Pagefind) and code copy-to-clipboard (Expressive Code) already ship by default and need no new spec.

### DOC-019: Content voice and ELI5 tone system

**Priority:** P1 | **Depends On:** DOC-015 (editorial cleanup) | **Enables:** public launch

**Status:** Pending. A live per-route preview audit found 11 of 19 pages open with the templated, self-referential formula "Use this route when ..." / "Use this page to ...", leading with internal "route" jargon instead of the reader's goal; several pages repeat defensive disclaimers ("does not run local diagnostics, grant permissions, invoke plugin workflows ..."). This is neither ELI5 nor warm. Google's developer style guide prescribes a "knowledgeable friend" voice (conversational, friendly, respectful; not pedantic or pushy) and a concrete lint rule against "simply / easy / quickly / it's that simple."

**Goal:** Establish and enforce one friendly-but-not-condescending voice so every page opens with the reader's outcome in plain language.

**Reviewability Budget:** Primary surface: docs/content |
Projected reviewable LOC: about 40 (tone linter) |
Production files: 0 |
Total files: about 15 |
Budget result: within budget

**Scope:**
- Write a short voice guide (the "knowledgeable friend" model) into the contributor docs.
- Replace the "Use this route/page when ..." opener on every page with a value-first sentence (what you will accomplish + why it matters), dropping internal "route" jargon.
- Consolidate the repeated safety disclaimers into one calm, reusable note rather than per-page legalese.
- Add a tone linter to `validate-docs-quality.mjs`: deny-list condescending words ("simply", "just", "easy", "easily", "quickly", "it's that simple") and the "Use this route when" opener pattern.

**Out of Scope:**
- Right-sizing reference data tables (DOC-020).
- IA / navigation restructuring (DOC-021).

**Key Files:**
- All hand-authored pages under `docs-site/src/content/docs/`
- `docs-site/scripts/validate-docs-quality.mjs`
- `docs-site/src/content/docs/contribute-and-release.md` (voice guide)

**Research grounding:** Google developer documentation style guide — tone (`developers.google.com/style/tone`) and word-list (`developers.google.com/style/word-list`).

### DOC-020: Per-page value alignment and right-sizing

**Priority:** P2 | **Depends On:** DOC-019 | **Enables:** public launch

**Status:** Pending. The per-route audit found uneven value delivery: generated reference pages are walls of data (`reference/tests` 5,844 words; `reference/skills` 2,058; `reference/agents` 1,455) with no "what is this / why you would care" framing or progressive disclosure, while others are thin (home 204 words; `reference/hooks` 304). No page consistently states what the reader will get, the prerequisites, and the next step.

**Goal:** Make every page deliver its promised value at the right depth, scannably.

**Reviewability Budget:** Primary surface: docs/content |
Projected reviewable LOC: about 0 |
Production files: 0 |
Total files: about 12 |
Budget result: within budget

**Scope:**
- Add a consistent page scaffold: a one-line "what you'll get," prerequisites, and an explicit "next step" link on each route.
- Apply progressive disclosure to the heavy generated reference pages (collapsible/accordion sections, tabs for Claude vs Codex) so each opens with orientation, not a data wall; reconsider whether the 5,844-word Tests reference is reader-facing at all.
- Strengthen thin pages (home, hooks) so each states its value; align every page against the PRD IA table's stated purpose + success criterion.
- Add a per-route "promised-value" check to `validate-docs-quality.mjs` (each page has an intro sentence and a next-step link).

**Out of Scope:**
- New pages or IA regrouping (DOC-021).
- Tone wording (DOC-019).

**Key Files:**
- `docs-site/src/content/docs/**`
- `docs-site/scripts/generate-reference-pages.mjs` (progressive disclosure for generated pages)
- `docs-site/scripts/validate-docs-quality.mjs`

**Research grounding:** Fern + Nielsen Norman Group — progressive disclosure (accordions = sequential, tabs = parallel paths, collapsible sidebars = hierarchical).

### DOC-021: Task-based information architecture and wayfinding

**Priority:** P2 | **Depends On:** DOC-013 (landing), DOC-002 | **Enables:** public launch

**Status:** Pending. The sidebar is grouped by raw Diátaxis mode labels (Tutorials / How-to / Reference / Explanation). Best-in-class docs (Stripe; Fern; Nielsen Norman Group) organize IA around user goals/tasks — not internal structure or Diátaxis labels — and add "where do I start" wayfinding plus progressive disclosure. The landing is a thin doc with no task-based quick-start (Stripe leads above the fold with use-case cards).

**Goal:** Restructure navigation and the landing around user goals with clear wayfinding.

**Reviewability Budget:** Primary surface: docs/UI + config |
Projected reviewable LOC: about 30 |
Production files: 0-1 |
Total files: 3-5 |
Budget result: within budget

**Scope:**
- Regroup the sidebar by user goal with plain labels (for example: Get started / Install / First success / Look it up / Trust & security / Contribute) instead of Diátaxis jargon.
- Add "where do I start" wayfinding (Stripe-style use-case quick-start cards) to the landing — coordinate with DOC-013's hero.
- Apply progressive disclosure: collapsible sidebar groups and tabs for the parallel Claude vs Codex paths, so a beginner is not shown the whole tree at once.
- Verify keyboard operability of the new navigation controls (WCAG SC 2.1.1) — coordinate with DOC-016.

**Out of Scope:**
- Per-page prose/tone (DOC-019/020).
- Brand tokens/fonts (DOC-013).

**Key Files:**
- `docs-site/astro.config.mjs` (sidebar config)
- `docs-site/src/content/docs/index.mdx` (landing wayfinding)
- Optional Hero / SiteTitle component override under `docs-site/src/components/`

**Research grounding:** Stripe (`docs.stripe.com` — task-oriented landing + business-function IA); Fern + Nielsen Norman Group (task-based IA, progressive disclosure).

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Current docs | Markdown/MDX content under `docs-site/src/content/docs/`, plus source planning docs under `docs/` and `docs/ai/specs/`. |
| Current site tooling | `docs-site/package.json` with pnpm 10.25.0, Astro 6.4.6, Starlight 0.40.0, `starlight-links-validator`, and scripts for reference generation, Astro check, build, and validation. |
| Existing validation | Shell-based repo tests under `tests/speckit-pro/`, docs-site `reference:check` / `validate`, generated reference checks, and DOC-006 safe-aids validation. |
| Product-code constraint | This roadmap changes documentation planning and future docs-site files only; no plugin behavior changes. |

## References

- Source PRD: [../../prd-interactive-documentation.md](../../prd-interactive-documentation.md)
- Prompt roadmap: [../../roadmap-interactive-documentation.md](../../roadmap-interactive-documentation.md)
- Traceability matrix: [../../traceability-interactive-documentation.md](../../traceability-interactive-documentation.md)
- Roadmap-MOC home note: [interactive-documentation-roadmap-MOC.md](interactive-documentation-roadmap-MOC.md)

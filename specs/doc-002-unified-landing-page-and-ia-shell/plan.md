# Implementation Plan: Unified landing page and IA shell

**Branch**: `doc-002-unified-landing-page-and-ia-shell` | **Date**: 2026-06-13 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/doc-002-unified-landing-page-and-ia-shell/spec.md`

## Summary

Create a new `docs-site/` Astro/Starlight documentation app that turns the DOC-001 framework and IA decision record into a usable public shell. DOC-002 delivers a thin landing page, Diataxis navigation, all 11 top-level route shells, source-vs-generated-payload explanation, GitHub Pages-ready configuration assumptions, and docs-site-scoped build plus internal-link validation without adding a publish workflow or touching plugin behavior.

## Technical Context

**Language/Version**: TypeScript, Markdown, and MDX in an Astro docs app; package versions planned from the current refresh are `astro@6.4.6`, `@astrojs/starlight@0.40.0`, and `@astrojs/check@0.9.9`.

**Primary Dependencies**: Astro, Starlight, `@astrojs/check`, and `starlight-links-validator` for Markdown/MDX internal-link validation during production build.

**Storage**: Static repository files only: `docs-site/` package/config files and Starlight Markdown/MDX content under `docs-site/src/content/docs/`. No database, generated payload, runtime service, or persisted user data.

**Testing**: Docs-site-scoped `pnpm` scripts after `docs-site/` exists: `pnpm check` (`astro check`), `pnpm build` (`astro build`), `pnpm validate` (`pnpm check && pnpm build`), `pnpm validate:links` (`pnpm build` with `starlight-links-validator` enabled), and `pnpm preview` (`astro preview`). Root plugin test commands remain out of DOC-002 implementation scope unless plugin/spec scaffolding surfaces are changed.

**Target Platform**: Static documentation site for GitHub Pages project hosting from `racecraft-lab/racecraft-plugins-public`.

**Project Type**: Static documentation web app.

**Performance Goals**: Static prerendered Starlight route shells with default Pagefind search behavior. DOC-002 does not add analytics, custom client-side widgets, screenshot checks, or search hardening.

**Accessibility Constraints**: Keep critical choices and explanations in semantic static Markdown/MDX content. Use native links and Starlight navigation defaults for the landing choices, route links, source evidence links, and page-local links. Preserve visible focus, descriptive link text, heading order, non-color-only meaning, and readable order for any DOC-002 custom styling; leave automated accessibility tooling and responsive screenshot policy to DOC-010.

**Constraints**: Use DOC-001 as the stack and IA contract; keep README files as source evidence only; do not change plugin behavior, marketplace manifests, generated payloads, hooks, agents, release automation, or GitHub Pages publish workflows.

**Scale/Scope**: One docs app, one landing page, 10 additional top-level route shell pages, four Diataxis sidebar groups, and build-integrated internal-link validation.

**Reviewability Budget**: Primary implementation surface is `docs-site/`; secondary review surface is DOC-002 process artifacts under `specs/doc-002-unified-landing-page-and-ia-shell/` and `docs/ai/specs/.process/DOC-002-workflow.md`. The setup forward estimate remains approximately 395 to 405 reviewable LOC excluding lock/vendor output. Declared operations include 16 expected docs-site config/content/control files, which keeps the constitution file-count warning accepted but below the 25-file block threshold. The plan-phase estimator is ready to parse the declared operations and reports `status: pass`, `projected: 80`, `new: 16`, `total_entries: 16` under the greenfield threshold.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this block to project the slice's production-LOC footprint before `tasks.md` exists.

- NEW docs-site/package.json
- NEW docs-site/pnpm-lock.yaml
- NEW docs-site/astro.config.mjs
- NEW docs-site/tsconfig.json
- NEW docs-site/src/content.config.ts
- NEW docs-site/src/content/docs/index.mdx
- NEW docs-site/src/content/docs/install/claude-code.md
- NEW docs-site/src/content/docs/install/codex.md
- NEW docs-site/src/content/docs/first-run.md
- NEW docs-site/src/content/docs/choose-your-path.md
- NEW docs-site/src/content/docs/reference.md
- NEW docs-site/src/content/docs/troubleshooting.md
- NEW docs-site/src/content/docs/security-and-trust.md
- NEW docs-site/src/content/docs/contribute-and-release.md
- NEW docs-site/src/content/docs/spec-kit-lifecycle.md
- NEW docs-site/src/content/docs/glossary.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Reason |
|-----------|--------|--------|
| I. Plugin Structure Compliance | PASS | DOC-002 plans only `docs-site/` docs app files and SpecKit planning artifacts. It does not alter plugin manifests, commands, skills, agents, hooks, generated payloads, or marketplace registry files. |
| II. Script Safety | PASS | No new Bash scripts are planned. Validation is through package scripts invoking Astro/Starlight commands. |
| III. Semantic Versioning | PASS | No plugin version or release-please changes are planned. |
| IV. Test Coverage Before Merge | PASS | The feature defines docs-site validation with `pnpm validate`; root plugin test layers are not required unless implementation touches plugin/spec scaffold surfaces beyond DOC-002 artifacts. |
| V. Conventional Commits | PASS | Parent orchestrator owns commits and must use a conventional PR title; this phase does not commit. |
| VI. KISS, Simplicity & YAGNI | PASS | The plan uses Starlight defaults, a single docs app, route shell pages, build-integrated link validation, and no speculative widgets, deploy workflow, or custom validation framework. |

**Budget gate**: WARN accepted for the constitution/setup budget because the expected docs-site file count is 16 and the setup forward LOC estimate is near the advisory ceiling. The standalone plan-phase estimator parses all 16 declared operations and currently returns `status: pass`. This does not cross the block threshold, and the spec already records the accepted one-workflow, two-slice intent.

**Exact split decision**: Keep one DOC-002 spec and one DOC-002 workflow identity. If autopilot emits split PRs, use two review slices: Slice 1 creates the Astro/Starlight shell, landing page, sidebar, and 11 route shells; Slice 2 adds internal-link validation, final Pages-ready config hardening, and build/link verification. If routing emits one navigable PR, preserve this review order in the PR packet instead of creating a second spec.

**PR review packet source**: The PR body must draw from `spec.md`, this `plan.md`, `research.md`, `data-model.md`, `contracts/route-shell-manifest.json`, and `quickstart.md`. It must include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback/feature-flag notes.

**Post-design re-check**: PASS. Phase 0 and Phase 1 artifacts keep the same stack, route contract, non-goals, validation boundary, and two-slice intent. No unresolved clarification markers remain.

## Project Structure

### Documentation (this feature)

```text
specs/doc-002-unified-landing-page-and-ia-shell/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── route-shell-manifest.json
└── tasks.md
```

### Source Code (repository root)

```text
docs-site/
├── package.json
├── pnpm-lock.yaml
├── astro.config.mjs
├── tsconfig.json
└── src/
    ├── content.config.ts
    └── content/
        └── docs/
            ├── index.mdx
            ├── choose-your-path.md
            ├── contribute-and-release.md
            ├── first-run.md
            ├── glossary.md
            ├── reference.md
            ├── security-and-trust.md
            ├── spec-kit-lifecycle.md
            ├── troubleshooting.md
            └── install/
                ├── claude-code.md
                └── codex.md
```

**Structure Decision**: Use Starlight's docs collection under `docs-site/src/content/docs/` with one page per top-level route shell. Keep sidebar groups in `astro.config.mjs` using `starlight({ sidebar: [...] })` with slug strings. Keep shell metadata aligned with `contracts/route-shell-manifest.json`.

## Phase 0 Decisions

| Decision | Selected |
|----------|----------|
| Documentation stack | Astro with Starlight remains accepted; no hard blocker found in the provided current refresh. |
| Package manager | `pnpm` scoped to `docs-site/`. |
| Package versions | `astro@6.4.6`, `@astrojs/starlight@0.40.0`, `@astrojs/check@0.9.9`; `starlight-links-validator` selected as the validator package, with the lockfile capturing the resolved version during implementation. |
| GitHub Pages assumptions | Configure `site: "https://racecraft-lab.github.io"`, `base: "/racecraft-plugins-public"`, and `trailingSlash: "always"` unless implementation build evidence requires a narrower Astro-compatible adjustment. Do not add `.github/workflows/**`. |
| Search | Leave Starlight/Pagefind default enabled; DOC-010 owns hardening. |
| Link validation | Add `starlight-links-validator` to Starlight config and expose `pnpm validate` plus `pnpm validate:links`; link validation is expected to run during `astro build`, so `validate:links` reuses the production build path instead of adding a separate crawler. |
| Accessibility shell contract | Keep DOC-002 core navigation and route orientation static, semantic, keyboard reachable, and compatible with Starlight defaults; DOC-006 may enhance only when equivalent static fallback remains. |

## Phase 1 Design

1. Define route shell metadata in `data-model.md` and `contracts/route-shell-manifest.json`.
2. Implement Starlight sidebar groups: Tutorials, How-to, Reference, Explanation.
3. Create all 11 route shell pages from the DOC-001 IA skeleton.
4. Put source-vs-generated-payload explanation on `/` and `/reference`.
5. Keep the landing page bounded to a first-screen purpose/value statement,
   Claude Code and Codex next actions, and a short source-vs-payload summary;
   exclude full install procedures, command matrices, and generic marketing
   content.
6. Give deferred route shells a compact orientation block: audience, useful-now
   shell content, deferred owner DOC, source evidence, and one static next step
   or related route link.
7. Keep README-derived claims as cited source evidence only.
8. Keep validation local to `docs-site/` package scripts and do not add a GitHub Pages publish workflow.
9. Use Starlight's page structure and Markdown headings so each page has one
   clear title, ordered `h2`/`h3` sections, and descriptive native links for
   platform choices, source evidence, route links, and next steps.
10. Avoid custom widgets or styling that suppresses native focus indicators,
   uses color alone for callout/status meaning, changes reading order, or
   replaces static route-shell content with JavaScript-only behavior.

## Selected Command Roles

| Role | Command | `docs-site/package.json` script body |
|------|---------|--------------------------------------|
| Install dependencies | `cd docs-site && pnpm install` | N/A: package-manager install step |
| Development server | `cd docs-site && pnpm dev` | `astro dev` |
| Type/content diagnostics | `cd docs-site && pnpm check` | `astro check` |
| Production build | `cd docs-site && pnpm build` | `astro build` |
| Full DOC-002 validation | `cd docs-site && pnpm validate` | `pnpm check && pnpm build` |
| Internal-link validation | `cd docs-site && pnpm validate:links` | `pnpm build` |
| Static preview | `cd docs-site && pnpm preview` | `astro preview` |

`pnpm validate` should compose the package scripts as `pnpm check && pnpm build` so diagnostics and the production build share the same docs-site scope. `pnpm validate:links` intentionally reuses `pnpm build` because `starlight-links-validator` is build-integrated; do not add a separate external-link crawler for DOC-002.

## Reliability Failure Modes

- `pnpm install` may require package-registry network access and may create or
  refresh `docs-site/pnpm-lock.yaml`. Treat that as setup, not the repeatable
  DOC-002 minimum completion gate after dependencies are installed.
- `pnpm check` blocks DOC-002 completion on Astro diagnostics, type errors, or
  content typing/schema errors reported by `astro check`.
- `pnpm build` blocks DOC-002 completion when Astro/Starlight cannot generate the
  static site because of config errors, content/frontmatter/schema errors, route
  generation failures, invalid sidebar slugs, or GitHub Pages `site`, `base`, or
  `trailingSlash` mismatches.
- `pnpm validate:links` blocks DOC-002 completion only for internal Markdown/MDX
  route link issues reported during the production build path, including invalid
  internal routes, invalid hashes, missing or forbidden trailing slashes, and
  same-site/base-path mismatches.
- External official-doc URL reachability, external-link crawling, GitHub Pages
  deployment, browser screenshot checks, analytics checks, and broader docs CI
  policy are not part of DOC-002's minimum completion gate; DOC-010 owns those
  hardening decisions.
- A build or link-validation failure caused by ordinary Astro/Starlight config,
  package-script naming, route, or Pages path errors must be fixed inside
  DOC-002. Reopen the DOC-001 framework fallback only if Astro/Starlight cannot
  satisfy GitHub Pages hosting, MDX/component authoring, accessible static
  fallback, dependency policy, or maintainability without violating a hard
  blocker.

## Error Handling Next Actions

| Failure | Next action | Fallback boundary |
|---------|-------------|-------------------|
| Missing `pnpm` before setup | Stop setup, enable or install `pnpm` in the local development environment, then rerun `cd docs-site && pnpm install`. Do not substitute root `npm`/`yarn` commands or create a root workspace to bypass the docs-site package-manager decision. | Setup prerequisite only; not a framework blocker. |
| Dependency install or lockfile setup failure | Fix the docs-site package manifest, package versions, registry access, or lockfile refresh in `docs-site/`, then rerun `pnpm install`. | Setup issue unless package policy or maintainership constraints make the selected dependency set unacceptable. |
| `pnpm check` diagnostics | Fix Astro diagnostics, TypeScript/content typing, or schema issues in docs-site source/config, then rerun `pnpm check` before `pnpm build`. | Fixable DOC-002 error. |
| `pnpm build` failure | Inspect the Astro/Starlight build output and repair `astro.config.mjs`, package scripts, content/frontmatter/schema, route files, sidebar slugs, or Pages `site`/`base`/`trailingSlash` settings as applicable, then rerun `pnpm build` and `pnpm validate`. | Reopen fallback only if Astro/Starlight cannot satisfy GitHub Pages hosting, MDX/component authoring, accessible static fallback, dependency policy, or maintainability after local fixes are attempted or ruled out. |
| `pnpm validate:links` failure | Fix the broken Markdown/MDX route link, anchor, trailing slash, same-site URL, or base-path assumption in docs-site content/config, then rerun `pnpm validate:links`. Do not add an external-link crawler for DOC-002. | Fixable DOC-002 error; external-link policy remains DOC-010. |
| GitHub Pages base/path mismatch | Align `site`, `base`, `trailingSlash`, Starlight route slugs, and internal links with the project-page values `https://racecraft-lab.github.io`, `/racecraft-plugins-public`, and `always`, then rerun `pnpm build` plus `pnpm validate:links`. Do not add `.github/workflows/**`. | Fixable DOC-002 config error unless GitHub Pages hosting itself becomes impossible for the stack. |
| True Astro/Starlight hard blocker | Stop the scaffold path, record the blocker evidence in plan/research/workflow, and apply the DOC-001 fallback order: Docusaurus/MDX, then VitePress, then repo-native Markdown. | Requires evidence that GitHub Pages hosting, MDX/component authoring, accessible static fallback, dependency policy, or maintainability cannot be satisfied by Astro/Starlight in this repository. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Warning-level reviewability size | The accepted IA requires all 11 route shells plus package/config/control files in one DOC-002 workflow. | Splitting into two separate specs would churn roadmap identity and route ownership. A landing-only shell would fail DOC-002 route contract requirements. |

# Implementation Plan: Unified landing page and IA shell

**Branch**: `doc-002-unified-landing-page-and-ia-shell` | **Date**: 2026-06-13 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/doc-002-unified-landing-page-and-ia-shell/spec.md`

## Summary

Create a new `docs-site/` Astro/Starlight documentation app that turns the DOC-001 framework and IA decision record into a usable public shell. DOC-002 delivers a thin landing page, Diataxis navigation, all 11 top-level route shells, source-vs-generated-payload explanation, GitHub Pages-ready configuration assumptions, and docs-site-scoped build plus internal-link validation without adding a publish workflow or touching plugin behavior.

## Technical Context

**Language/Version**: TypeScript, Markdown, and MDX in an Astro docs app; package versions planned from the current refresh are `astro@6.4.6`, `@astrojs/starlight@0.40.0`, and `@astrojs/check@0.9.9`.

**Primary Dependencies**: Astro, Starlight, `@astrojs/check`, and `starlight-links-validator` for Markdown/MDX internal-link validation during production build.

**Storage**: Static repository files only: `docs-site/` package/config files and Starlight Markdown/MDX content under `docs-site/src/content/docs/`. No database, generated payload, runtime service, or persisted user data.

**Testing**: Docs-site-scoped `pnpm` scripts after `docs-site/` exists: `pnpm check`, `pnpm build`, `pnpm validate`, `pnpm validate:links`, and `pnpm preview`. Root plugin test commands remain out of DOC-002 implementation scope unless plugin/spec scaffolding surfaces are changed.

**Target Platform**: Static documentation site for GitHub Pages project hosting from `racecraft-lab/racecraft-plugins-public`.

**Project Type**: Static documentation web app.

**Performance Goals**: Static prerendered Starlight route shells with default Pagefind search behavior. DOC-002 does not add analytics, custom client-side widgets, screenshot checks, or search hardening.

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
| Link validation | Add `starlight-links-validator` to Starlight config and expose `pnpm validate` plus `pnpm validate:links`; link validation is expected to run during `astro build`. |

## Phase 1 Design

1. Define route shell metadata in `data-model.md` and `contracts/route-shell-manifest.json`.
2. Implement Starlight sidebar groups: Tutorials, How-to, Reference, Explanation.
3. Create all 11 route shell pages from the DOC-001 IA skeleton.
4. Put source-vs-generated-payload explanation on `/` and `/reference`.
5. Keep README-derived claims as cited source evidence only.
6. Keep validation local to `docs-site/` package scripts and do not add a GitHub Pages publish workflow.

## Selected Command Roles

| Role | Command |
|------|---------|
| Install dependencies | `cd docs-site && pnpm install` |
| Development server | `cd docs-site && pnpm dev` |
| Type/content diagnostics | `cd docs-site && pnpm check` |
| Production build | `cd docs-site && pnpm build` |
| Full DOC-002 validation | `cd docs-site && pnpm validate` |
| Internal-link validation | `cd docs-site && pnpm validate:links` |
| Static preview | `cd docs-site && pnpm preview` |

`pnpm validate` should run `astro check && astro build`. `pnpm validate:links` should run the production build path with `starlight-links-validator` enabled, because the validator is build-integrated.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Warning-level reviewability size | The accepted IA requires all 11 route shells plus package/config/control files in one DOC-002 workflow. | Splitting into two separate specs would churn roadmap identity and route ownership. A landing-only shell would fail DOC-002 route contract requirements. |

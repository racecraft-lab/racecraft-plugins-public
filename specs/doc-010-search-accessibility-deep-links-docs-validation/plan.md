# Implementation Plan: Search, Accessibility, Deep Links, Docs Validation

**Branch**: `doc-010-search-accessibility-deep-links-docs-validation` | **Date**: 2026-06-19 | **Spec**: `specs/doc-010-search-accessibility-deep-links-docs-validation/spec.md`

**Input**: Feature specification from `specs/doc-010-search-accessibility-deep-links-docs-validation/spec.md`

**Note**: This plan applies the `speckit-pro-reviewability` preset and uses `docs/ai/specs/.process/DOC-010-design-concept.md` as the source of truth for scoped planning decisions.

## Summary

DOC-010 hardens the existing Astro/Starlight docs site for support-oriented search, stable deep links, accessible interactive aids, and deterministic docs validation. The implementation keeps the six existing logical routes, extends the current docs-site validation path, adds minimal Playwright smoke coverage with `/racecraft-plugins-public` owned by Playwright baseURL configuration, and adds a job-level `validate-docs` PR Checks gate without changing plugin matrix semantics or forcing plugin matrix jobs for docs-site-only PRs.

## Technical Context

**Language/Version**: JavaScript ESM on Node.js for docs-site scripts; Astro 6.4.6 and Starlight 0.40.0 in `docs-site/`; pnpm 10.25.0 scoped with `pnpm --dir docs-site ...`

**Primary Dependencies**: Existing `astro`, `@astrojs/starlight`, `@astrojs/check`, `starlight-links-validator`; add minimal Playwright dev dependency only for `validate:smoke`

**Storage**: Checked-in Markdown, Astro components, package scripts, generated reference files, and CI artifacts only; no database or browser storage

**Testing**: `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site check`, `pnpm --dir docs-site build`, focused docs quality validation, `pnpm --dir docs-site validate:smoke`, and combined `pnpm --dir docs-site validate`. Security/safety evidence is verified by source review and validation output review: validators emit repo-relative paths, avoid local absolute paths and sensitive values, treat unsafe commands as manual-only/copyable guidance, avoid user-local inputs, and keep Playwright evidence limited to the configured local docs preview route and viewport set.

**Target Platform**: GitHub Pages hosted Astro/Starlight docs site under `/racecraft-plugins-public/`; GitHub Actions PR Checks on `ubuntu-latest`

**Project Type**: Documentation site, validation scripts, and CI workflow hardening

**Performance Goals**: Keep validation deterministic and smoke-level; avoid broad visual snapshots; keep CI docs validation limited to docs-site/reference-source/doc-contract changes

**Constraints**: No new top-level route, no search replacement, no analytics, no live plugin install commands in CI, no browser-side local command execution, no local-user-file inspection, no destructive validation, no workflow-level `paths` filters

**Security/Safety Planning Boundaries**: DOC-010 validation uses checked-in repository sources, generated docs output, and a local docs-site preview only. It does not inspect user home directories, local JSON/config/cache, browser profiles, environment secrets, or user-supplied payloads. Command snippets, manifests, payload references, and generated-reference facts are checked through source-backed static validation and copyable-guidance review, not execution. Playwright smoke stays on the configured docs-site baseURL and must not perform live installs, destructive actions, analytics, production telemetry, external marketplace navigation, or browser-side local command execution. Validation output and smoke artifacts use repo-relative paths and sanitized evidence. The `validate-docs` gate must not add new permissions, credentials, secrets, marketplace access, or plugin matrix fan-out for docs-site-only PRs.

**Scale/Scope**: Six logical routes (`/`, `/choose-your-path/`, `/spec-kit-lifecycle/`, `/glossary/`, `/reference/skills/`, `/contribute-and-release/`), two viewports, one compact smoke artifact, and deterministic validation for full internal links/anchors

**Reviewability Budget**: Primary surface docs/process; secondary surfaces UI and harness/adapter; projected reviewable LOC 275-395; projected production files 5; projected total files 10; budget result within budget; split decision is one spec with route coverage reduction before any split

## Declared File Operations

- MODIFIED docs-site/package.json
- MODIFIED docs-site/pnpm-lock.yaml
- NEW docs-site/playwright.config.mjs
- NEW docs-site/tests/docs-smoke.spec.mjs
- NEW docs-site/scripts/validate-docs-quality.mjs
- MODIFIED docs-site/scripts/validate-doc006-safe-aids.mjs
- MODIFIED docs-site/src/content/docs/glossary.md
- MODIFIED docs-site/src/content/docs/choose-your-path.mdx
- MODIFIED docs-site/src/components/LifecycleFlow.astro
- MODIFIED .github/workflows/pr-checks.yml

## Reviewability Estimate

- **Estimated reviewable LOC**: 275-395, anchored by the DOC-010 design concept estimator result of 277 and the implementation-file budget above.
- **Estimated production files**: 5 (`docs-site` scripts/config/test/component/content surfaces, excluding lockfile churn and CI-only workflow semantics).
- **Estimated total files**: 10 planned implementation files.
- **Budget status**: Within budget. If implementation pressure rises, reduce Playwright route assertions before splitting the spec.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | DOC-010 does not alter plugin manifests, command schemas, skills, agents, or hooks. |
| II. Script Safety | PASS | New or modified scripts stay in JavaScript ESM or package scripts; no unsafe shell script changes are planned. |
| III. Semantic Versioning | PASS | No manual plugin version change is planned. |
| IV. Test Coverage Before Merge | PASS | Docs validation is covered by `pnpm --dir docs-site validate`; plugin test matrix semantics remain unchanged. |
| V. Conventional Commits | PASS | PR title remains a merge-time concern enforced by existing `validate-pr-title`. |
| VI. KISS, Simplicity & YAGNI | PASS | Reuses Starlight search, existing validators, existing routes, and a minimal smoke test instead of adding broad frameworks or new docs routes. |

**Reviewability gate**: PASS. Primary surface is docs/process with bounded UI and harness/adapter secondary surfaces. The file and LOC estimates stay below warning thresholds.

**PR review packet source**: PR description must include what changed, why, non-goals, review order, scope budget, traceability, verification, known gaps, rollback/fallback notes, browser smoke evidence, and manual accessibility/responsive review evidence. It must also include automation-safety evidence: commands run, confirmation that copyable snippets were not executed, confirmation that local user files/JSON/cache and environment secrets were not inspected, confirmation that no live plugin or marketplace install/destructive/browser-side command behavior occurred, and a sanitized summary of the compact `docs-site-smoke-evidence` artifact.

## Project Structure

### Documentation (this feature)

```text
specs/doc-010-search-accessibility-deep-links-docs-validation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── browser-smoke-contract.md
│   ├── docs-validation-contract.md
│   └── pr-checks-docs-gate-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
docs-site/
├── astro.config.mjs
├── package.json
├── pnpm-lock.yaml
├── playwright.config.mjs
├── scripts/
│   ├── generate-reference-pages.mjs
│   ├── validate-doc006-safe-aids.mjs
│   └── validate-docs-quality.mjs
├── src/
│   ├── components/
│   │   ├── LifecycleFlow.astro
│   │   └── SafeInstallAids.astro
│   └── content/docs/
│       ├── choose-your-path.mdx
│       ├── contribute-and-release.md
│       ├── glossary.md
│       ├── index.mdx
│       ├── spec-kit-lifecycle.mdx
│       └── reference/
│           └── skills.md
└── tests/
    └── docs-smoke.spec.mjs

.github/workflows/
└── pr-checks.yml
```

**Structure Decision**: Keep the feature inside the existing docs-site package and existing PR Checks workflow. Generated reference pages remain under `docs-site/src/content/docs/reference/` and deterministic reference validation remains owned by `docs-site/scripts/generate-reference-pages.mjs`.

## Phase 0 Research Summary

Research resolved the planning choices without open clarifications:

- Keep Starlight/Pagefind search and improve findability through headings, glossary terms, and cross-links.
- Extend current validators with one focused docs quality validator instead of creating a broad new framework.
- Add minimal Playwright smoke coverage for six logical routes, two viewports, representative deep links, and selected interactive aid checks.
- Add a job-level `validate-docs` gate with changed-file detection for rendered docs-site, generated-reference source, and docs-validation contract surfaces.
- Keep docs-site-only PRs on the docs validation path without making `detect.outputs.plugins` non-empty or running unrelated plugin matrix jobs unless the same PR also touches plugin or generated-reference source inputs.
- Treat accessibility automation as guardrails and record manual/browser evidence in the existing PR packet sections.
- Preserve native controls and semantic HTML in the interactive aids where possible: `SafeInstallAids.astro` keeps radio inputs, copy buttons, semantic tables/code blocks, and polite status text for selector or copy-result changes; `LifecycleFlow.astro` stays readable as ordered semantic content before adding any custom interaction.
- Manual/browser evidence must explicitly cover visible unclipped focus, status announcement text, screen-reader-oriented label/state inspection, contrast and reflow across desktop and mobile-sized layouts, and static fallback/non-JavaScript readability. This evidence is a review record, not an accessibility certification claim.

See `research.md` for decisions, rationale, and alternatives.

## Phase 1 Design Summary

Design artifacts define the docs entities, validation contracts, browser smoke behavior, and local validation guide:

- `data-model.md`: Documentation Page, Deep Link Anchor, Interactive Aid, Static Fallback, Validation Path, Generated Reference Source Input, Browser Smoke Evidence, External Platform Claim.
- `contracts/docs-validation-contract.md`: local script contract for `validate`, `validate:quality`, and `validate:smoke`.
- `contracts/browser-smoke-contract.md`: route, viewport, baseURL, and artifact expectations.
- `contracts/pr-checks-docs-gate-contract.md`: CI changed-file detection and `validate-docs` behavior.
- `quickstart.md`: local verification path and manual evidence checklist.
- Support anchor scope is defined by page family and support purpose: install, recovery/troubleshooting, generated reference, glossary, and release workflow pages must expose stable support anchors or documented exceptions. Deterministic docs validation owns full link and anchor coverage.
- Browser smoke route rationale maps the six logical routes to critical journeys: entry/search, install selection, lifecycle guidance, glossary terminology, generated skills reference, and contributor/release workflow. Playwright remains representative and does not become an exhaustive crawl or visual snapshot suite.
- Accessibility review detail: focused validators and Playwright smoke may catch missing labels, status regions, unsafe controls, broken fallback content, and representative reflow failures; manual PR packet evidence remains required for contrast judgment, focus quality, screen-reader-oriented state inspection, and any known gaps.

## Post-Design Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | No plugin layout changes are introduced by the design artifacts. |
| II. Script Safety | PASS | Planned automation is Node ESM and Playwright config; no new bash script is required. |
| III. Semantic Versioning | PASS | No plugin version mutation is planned. |
| IV. Test Coverage Before Merge | PASS | The plan defines local and CI docs validation paths plus representative smoke coverage. |
| V. Conventional Commits | PASS | Existing PR title validation remains the enforcement point. |
| VI. KISS, Simplicity & YAGNI | PASS | The design keeps one focused validator, one smoke spec, existing routes, and existing search. |

**Gate result**: PASS with no complexity exceptions.

## Complexity Tracking

No constitution violations or split exceptions are required.

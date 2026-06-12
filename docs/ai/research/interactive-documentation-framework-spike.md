# DOC-001: Interactive Documentation Framework Spike

**Date**: 2026-06-12  
**Retrieval date for live framework/platform sources**: 2026-06-12  
**Status**: Recommended for DOC-002 handoff  
**Scope**: Research-only decision record. No site scaffold, package files, lockfiles, CI workflows, marketplace files, generated payloads, README migrations, prototype components, or plugin behavior changes.

## Decision

Recommend **Docusaurus with MDX** as the default static documentation stack for DOC-002.

DOC-002 should implement the docs shell with Docusaurus, MDX pages/components, GitHub Pages deployment from this repository, and `pnpm` as the recommended package manager unless a new hard blocker appears before implementation.

## Why This Wins

Docusaurus is the best fit because it combines first-party MDX/React authoring, documented GitHub Pages deployment, first-party docs versioning, and production-build broken-link handling. Those cover the hard blockers and the highest-risk future maintenance needs better than the alternatives.

The main tradeoff is search. Docusaurus has first-class Algolia DocSearch support, while local/offline search is community-supported. DOC-002 should either use the official search path or explicitly add a local-search plugin with the support-class tradeoff recorded.

## DOC-002 Failure Handling and Fallback Rules

DOC-002 should refresh official Docusaurus and GitHub Pages docs before scaffolding. If Docusaurus still satisfies the hard blockers and the failure is limited to repository configuration, `baseUrl`, `trailingSlash`, `.nojekyll`, package-script naming, or GitHub Actions wiring, DOC-002 should keep Docusaurus and fix the configuration instead of reopening stack selection.

If Docusaurus cannot satisfy GitHub Pages hosting from this repository without violating a hard blocker, DOC-002 should stop the scaffold path, record the blocker, and use this fallback order:

1. **Astro/Starlight** if GitHub Pages deployment, MDX/static fallback, and maintainability remain acceptable, with extra versioning/link-check tooling recorded as a tradeoff.
2. **VitePress** if Vue-in-Markdown is acceptable and built-in local search becomes more important than Docusaurus versioning/link-check behavior, with custom versioning/link-check work recorded as a tradeoff.
3. **Repo-native Markdown fallback** only if framework candidates are blocked by GitHub Pages feasibility, dependency policy, or maintainership constraints.

Search-provider availability, package-manager preference, and local-search preference are not hard blockers by themselves. They become blockers only if they create an unacceptable dependency, cost, policy, or maintainership risk for this repository.

## Live Source Evidence

| Source | Retrieval date | Evidence note |
|---|---:|---|
| [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | 2026-06-12 | GitHub Pages hosts static HTML/CSS/JS from a repository and can run a build process before publishing. |
| [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) | 2026-06-12 | GitHub Pages can publish with custom GitHub Actions workflows. |
| [Docusaurus installation](https://docusaurus.io/docs/installation) | 2026-06-12 | Docusaurus documents `create-docusaurus`, `pnpm create docusaurus`, `pnpm run start`, `pnpm run build`, and `pnpm install` command paths. |
| [Docusaurus deployment](https://docusaurus.io/docs/deployment) | 2026-06-12 | Docusaurus emits static files to `build`, documents GitHub Pages deployment, and includes same-repo Actions examples. |
| [Docusaurus MDX and React](https://docusaurus.io/docs/markdown-features/react) | 2026-06-12 | Docusaurus has built-in MDX support for JSX and React components in Markdown. |
| [Docusaurus search](https://docusaurus.io/docs/search) | 2026-06-12 | Docusaurus provides first-class Algolia DocSearch support; local search options are community-supported. |
| [Docusaurus versioning](https://docusaurus.io/docs/versioning) | 2026-06-12 | Docusaurus supports versioned docs through `versions.json`, `versioned_docs/`, and versioned sidebars. |
| [Docusaurus config](https://docusaurus.io/docs/api/docusaurus-config) | 2026-06-12 | Production builds can throw on broken links, and Markdown link/image hooks are configurable. |
| [VitePress deploy](https://vitepress.dev/guide/deploy) | 2026-06-12 | VitePress documents GitHub Pages deployment, `docs:build`, `docs:preview`, and base path requirements. |
| [VitePress Vue in Markdown](https://vitepress.dev/guide/using-vue) | 2026-06-12 | Markdown files can use Vue features and imported Vue components. |
| [VitePress local search](https://vitepress.dev/reference/default-theme-search) | 2026-06-12 | VitePress supports built-in in-browser fuzzy full-text search with Minisearch. |
| [Astro GitHub Pages](https://docs.astro.build/en/guides/deploy/github/) | 2026-06-12 | Astro can deploy static prerendered sites to GitHub Pages with the official Astro GitHub Action. |
| [Starlight components](https://starlight.astro.build/components/using-components/) | 2026-06-12 | Starlight supports MDX components, built-in components, and UI framework components in MDX. |
| [Starlight site search](https://starlight.astro.build/guides/site-search/) | 2026-06-12 | Starlight includes built-in full-text search powered by Pagefind. |
| [Starlight sidebar](https://starlight.astro.build/guides/sidebar/) | 2026-06-12 | Starlight supports autogenerated and frontmatter-customized sidebar navigation. |
| [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) | 2026-06-12 | WCAG provides technology-neutral, testable accessibility success criteria, including keyboard, focus, labels, contrast, and responsive/reflow concerns. |
| [W3C WAI evaluating accessibility](https://www.w3.org/WAI/test-evaluate/) | 2026-06-12 | WAI recommends evaluating accessibility early and throughout development; tools help, but knowledgeable human evaluation is still required. |
| [WAI-ARIA APG keyboard interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) | 2026-06-12 | Interactive widgets need predictable keyboard operation and focus behavior. |

## Local Source Inputs

| Source | Use in this spike |
|---|---|
| `docs/prd-interactive-documentation.md` | Required routes, product outcomes, install/reference/troubleshooting/security/contribution coverage, and no-local-command-execution guardrails. |
| `docs/roadmap-interactive-documentation.md` | DOC-002 through DOC-010 ownership, sequencing, and acceptance handoff. |
| `docs/ai/specs/.process/DOC-001-design-concept.md` | Grill Me decisions for one default stack recommendation, IA skeleton scope, live-source refresh, and research-only output boundary. |
| `specs/doc-001-static-docs-framework-and-ia-spike/spec.md` | Formal DOC-001 requirements, acceptance scenarios, forbidden surfaces, and success criteria. |

## Support Class Legend and Evidence Bounds

Use these support-class labels when reading the matrix:

- **Built-in**: ships in the framework or default docs theme.
- **Official**: documented by the framework/platform maintainers, but may require configuration or a first-party integration.
- **Official third-party hosted**: officially supported by the framework, but provided by an external hosted service.
- **Community**: supported through community-maintained packages or patterns, not first-party docs.
- **External/manual**: possible through separate tools or hand-maintained repo practice.
- **Unsupported/blocked**: no acceptable path for DOC-001 requirements without changing the candidate's scope.
- **Unknown/weak**: the 2026-06-12 official-source refresh did not identify first-party support comparable to another candidate.

Negative findings are intentionally bounded. "No refreshed first-party versioning path found" and "link checking likely needs extra tooling" mean the official source set refreshed on 2026-06-12 did not show a first-party docs versioning or production-build broken-link gate comparable to Docusaurus. They are not claims that the broader ecosystem cannot solve those needs. DOC-002 must refresh official docs again before installing packages or configuring the site.

Version-sensitive observations are evidence freshness markers, not package pins. The Docusaurus docs opened at version 3.10.1 on 2026-06-12, while VitePress docs showed 2.0.0-alpha.17 with a link to 1.6.4. DOC-002 should install the current recommended version after a fresh source check.

Accessibility is split into two concerns. The hard blocker is whether the stack can support accessible static or keyboard-usable fallback content. Accessibility testing is a DOC-010 validation obligation after the site and interactive aids exist; DOC-001 records the handoff but does not add test tooling, CI, package files, or a site scaffold.

## Candidate Matrix

| Criterion | Weight | Docusaurus/MDX | VitePress | Astro/Starlight | Repo-native fallback |
|---|---|---|---|---|---|
| Static hosting | Hard blocker | Built-in/official: static files emitted to `build` | Built-in/official: static output in `.vitepress/dist` | Official Astro deployment path for static prerendered output | External/manual: GitHub can render Markdown, but no docs-site shell exists without Pages/Jekyll or custom output |
| GitHub Pages from this repo | Hard blocker | Official: Docusaurus GitHub Pages and Actions path | Official: VitePress GitHub Pages Actions path | Official: Astro GitHub Pages action path | External/manual: Pages can host static files, but fallback lacks a chosen site build |
| Reusable interactivity | Hard blocker | Built-in: MDX/React | Built-in: Vue in Markdown equivalent | Built-in/official: MDX, Astro components, and UI framework components | Unsupported/blocked: Markdown-only without extra tooling |
| Accessible static/keyboard fallback | Hard blocker | Built-in static output plus project discipline; generally works without JavaScript | Built-in static output plus project discipline | Built-in static output plus project discipline and Starlight docs defaults | Partial built-in Markdown accessibility, but missing required interactive aids |
| Accessibility testing and validation handoff | Required DOC-010 hardening | External/manual: compatible with static output; DOC-010 must choose automated checks plus human review | External/manual: compatible with static output; DOC-010 must choose automated checks plus human review | External/manual: compatible with static output; DOC-010 must choose automated checks plus human review | External/manual: Markdown can be audited, but there is no site-level validation surface until later tooling exists |
| DOC-001 no-implementation boundary | Hard blocker | Process-only: recommendation without scaffold | Process-only: recommendation without scaffold | Process-only: recommendation without scaffold | Process-only: no scaffold |
| Search | High | Official third-party hosted: Algolia DocSearch; Community: local search | Built-in: local Minisearch index | Built-in: Pagefind; Official plugin: Algolia DocSearch | External/manual: repository or browser search only unless extra tooling is added |
| Link checking | High | Built-in/official: production build can fail on broken links | Unknown/weak: refreshed official docs did not identify comparable first-party link-check gate; external checker likely | Unknown/weak: refreshed Astro/Starlight docs did not identify comparable first-party link-check gate; external checker likely | External/manual: separate checker needed |
| Versioning | Medium | Built-in/official: docs versioning CLI and versioned docs | Unknown/weak: refreshed official docs did not identify a first-party docs versioning path | Unknown/weak: refreshed Astro/Starlight docs did not identify first-party docs versioning comparable to Docusaurus | External/manual: copies, branches, or convention |
| Docs-as-code workflow | Medium | Built-in/official: Markdown/MDX, sidebars, GitHub Actions | Built-in/official: Markdown/Vue, GitHub Actions | Built-in/official: content collections/Starlight, GitHub Actions | Built-in repo practice for simple Markdown, weak for site UX |
| Maintenance load | Tie-breaker | Qualitative: medium; React/MDX stack, but docs-focused and mature | Qualitative: low-medium; lightweight but Vue-specific and versioning workarounds | Qualitative: medium; Astro/Starlight plus possible custom versioning/link checks | Qualitative: low initially, high once required features are rebuilt manually |
| Package/build/test commands | Required | Official: Docusaurus documents scaffold, install, start, build, and serve command roles; DOC-002 must define actual scripts | Official: `docs:build`/`docs:preview` scripts documented | Official: Astro action path and configurable build command | External/manual: validation can stay Markdown-only, but no framework command baseline exists |

## Accessibility and Interaction Guardrails

Reusable interactivity is not an accessibility claim by itself. DOC-002, DOC-006, and DOC-010 must keep every selector, copyable command block, metadata checker, decision tree, glossary popover, and lifecycle visualizer usable without relying on inaccessible dynamic behavior.

Minimum guardrails for later implementation:

- Provide a static Markdown table, static diagram, or equivalent non-JavaScript path for critical instructions and decisions.
- Preserve keyboard operation, visible focus, labels or accessible names, understandable status/error text, and contrast/reflow expectations.
- Avoid browser-side local command execution, config mutation, or hidden permission grants.
- Treat any component that cannot satisfy keyboard and static fallback requirements as out of scope until it is replaced with static content or redesigned.
- Leave accessibility tool selection, responsive/browser verification, and docs CI enforcement to DOC-010.

## Candidate Decisions

### Docusaurus/MDX: Accept

**Acceptance reason**: Docusaurus is the only candidate that refreshed sources showed covering MDX interactivity, GitHub Pages deployment, first-party versioned docs, and production-build broken-link enforcement in one docs-specific framework.

**Tradeoff**: Search needs a deliberate DOC-002 choice. Official Algolia DocSearch is first-class, but local search is community-supported. This is acceptable because search is high-weight but not a hard blocker, and Docusaurus wins on versioning and link checking.

### VitePress: Reject for Default

**Rejection reason**: VitePress is strong for lightweight docs, Vue component interactivity, GitHub Pages, and built-in local search. It is weaker for this repo because the official docs source set refreshed on 2026-06-12 did not identify a first-party docs-versioning workflow or first-party production-build link-checking gate comparable to Docusaurus, and the repository has no existing Vue tooling precedent.

**Evidence bound**: This is a bounded negative finding, not an ecosystem-wide unsupported claim. If DOC-002 finds newer official VitePress documentation for versioning or link checking, it should update the comparison before implementation.

**Best future use**: Reconsider only if DOC-002 prioritizes local search and minimal framework weight above versioning and Docusaurus link-check behavior.

### Astro/Starlight: Defer

**Deferral reason**: Starlight is strong for built-in Pagefind search, MDX components, autogenerated sidebars, and Astro GitHub Pages deployment. It is deferred because the Astro/Starlight official source set refreshed on 2026-06-12 did not identify first-party docs versioning or a first-party production-build link-checking gate comparable to Docusaurus, so those needs likely require extra tooling.

**Evidence bound**: This is a bounded negative finding. If DOC-002 finds newer official Astro/Starlight documentation for versioning or link checking, it should update the comparison before implementation.

**Best future use**: Reconsider if Docusaurus search is unacceptable and the team accepts custom versioning/link-check work.

### Repo-Native Fallback: Reject for Default, Retain as Emergency Fallback

**Fallback assessment**: Repo-native Markdown is evaluated as a serious low-dependency fallback. It preserves current docs-as-code reviewability, avoids a Node/site toolchain, avoids new package or lockfile maintenance, and can still support a static IA through ordinary Markdown pages and repository navigation.

**Rejection reason**: It is not the default because it fails reusable rich interactivity, site search, first-party docs versioning, and build-time docs validation without rebuilding those capabilities manually.

**Fallback condition**: Use only if Docusaurus, Astro/Starlight, and VitePress are later blocked by GitHub Pages feasibility, dependency policy, or maintainership constraints.

## Recommended Package and Commands for DOC-002

These are command roles, not DOC-001-created scripts. DOC-001 does not create or run them as implementation. DOC-002 must either define matching package scripts after scaffolding or update the handoff to the actual scripts created by the scaffold.

| Command role | Report-only recommendation |
|---|---|
| Package manager | `pnpm` |
| Future scaffold/setup | Use the current Docusaurus scaffold path, such as `pnpm create docusaurus`, in the DOC-002-owned docs-site path. DOC-002 chooses the final directory and commits the generated `package.json` and `pnpm-lock.yaml`. |
| Future dependency install | `pnpm install` after DOC-002 creates the site package files. |
| Future development preview | `pnpm run start` or the equivalent Docusaurus start script DOC-002 defines. |
| Future production build | `pnpm run build` as the minimum site build and broken-link validation gate. |
| Future local static preview | `pnpm run serve` or the equivalent Docusaurus serve script DOC-002 defines after a production build. |
| Future minimum validation/test | The site production build is the minimum docs-site validation command; existing repository structural checks run only when plugin/spec surfaces are touched. |
| Future GitHub Pages deployment | GitHub Actions Pages workflow from this repository; configure Docusaurus `url`, `baseUrl`, `trailingSlash`, and `.nojekyll` handling in DOC-002/DOC-010 as appropriate |

## IA Skeleton for DOC-002

| Route path | Route label | Primary Diataxis mode | Secondary modes | Audience | Purpose | Source evidence | Success criterion | Shell owner DOC | Full content owner DOC |
|---|---|---|---|---|---|---|---|---|---|
| `/` | Start | Tutorial | Explanation | First-time user | Explain Racecraft Public Plugins, `speckit-pro`, platform choice, and first next step. | `docs/prd-interactive-documentation.md` DOC-FR-002; `docs/roadmap-interactive-documentation.md` DOC-002 | User chooses Claude Code or Codex path within one screen. | DOC-002 | DOC-002 |
| `/install/claude-code` | Install: Claude Code | Tutorial | How-to | Claude Code user | Add marketplace, install/update/remove `speckit-pro`, verify namespaced plugin skills. | `docs/prd-interactive-documentation.md` DOC-FR-003; Claude Code plugin docs from PRD source map | User reaches a working `/speckit-pro:*` command path. | DOC-002 | DOC-003 |
| `/install/codex` | Install: Codex | Tutorial | How-to | Codex user | Add/select marketplace, install plugin, run install skill, restart, and verify custom agents. | `docs/prd-interactive-documentation.md` DOC-FR-004; OpenAI Codex plugin docs from PRD source map | User reaches a working `$speckit-*` flow with custom agents loaded when needed. | DOC-002 | DOC-004 |
| `/first-run` | First Run | Tutorial | Explanation | New plugin user | Guide one safe first `speckit-pro` workflow with checkpoints and lifecycle context. | `docs/prd-interactive-documentation.md` DOC-FR-005; `docs/roadmap-interactive-documentation.md` DOC-005 | User produces or identifies the expected first artifact and validation checkpoint. | DOC-002 | DOC-005 |
| `/choose-your-path` | Choose Your Path | How-to | Tutorial | New and returning users | Provide platform/scope selector, copyable commands, and checklist handoff without browser-side local execution. | `docs/prd-interactive-documentation.md` DOC-FR-006; W3C accessibility principles in PRD source map | User gets commands relevant only to selected platform/scope, with static fallback. | DOC-002 | DOC-006, DOC-010 |
| `/reference` | Reference | Reference | How-to | Users, agents, maintainers | Index command/skill matrix, manifests, marketplace files, hooks, agents, payloads, tests, and file layout. | `docs/prd-interactive-documentation.md` DOC-FR-007; `docs/roadmap-interactive-documentation.md` DOC-007 | Each supported surface has a stable deep link and source citation. | DOC-002 | DOC-007 |
| `/troubleshooting` | Troubleshooting | How-to | Reference | Users and support | Diagnose install, path, cache, permission, version, and prerequisite failures. | `docs/prd-interactive-documentation.md` DOC-FR-008; `docs/roadmap-interactive-documentation.md` DOC-008 | User can identify likely cause and next file/command to inspect. | DOC-002 | DOC-008 |
| `/security-and-trust` | Security & Trust | Explanation | Reference | Security/platform evaluator | Explain marketplace trust, generated payloads, hooks/MCP/agents, sandbox/approval behavior, updates, and rollback. | `docs/prd-interactive-documentation.md` DOC-FR-008; official Claude/Codex security docs in PRD source map | Evaluator can approve, reject, or ask a concrete follow-up. | DOC-002 | DOC-008 |
| `/contribute-and-release` | Contribute & Release | How-to | Reference | Maintainer/contributor | Explain source edits, payload rebuilds, marketplace sync, tests, release-please, and PR expectations. | `docs/prd-interactive-documentation.md` DOC-FR-009; `docs/roadmap-interactive-documentation.md` DOC-009 | Maintainer can complete a release-readiness checklist. | DOC-002 | DOC-009 |
| `/spec-kit-lifecycle` | Spec Kit Lifecycle | Explanation | Tutorial | User/evaluator | Explain PRD, roadmap, scaffold, autopilot phases, artifacts, and gates with static fallback diagram. | `docs/prd-interactive-documentation.md` DOC-FR-005; GitHub Spec Kit source in PRD source map | User can explain what each phase produces and validates. | DOC-002 | DOC-005, DOC-010 |
| `/glossary` | Glossary | Reference | Explanation | All users | Define marketplace, payload, source tree, skill, agent, hook, cache, constitution, and lifecycle terms. | `docs/prd-interactive-documentation.md` DOC-FR-002/DOC-FR-010; Diataxis source in PRD source map | Support answers can link to exact definitions. | DOC-002 | DOC-010 |

### DOC-010 Route Hardening Coverage

DOC-010 does not add a twelfth top-level route in this IA skeleton. It hardens existing routes after DOC-002 and DOC-006 create the site and interactive aids:

| Route scope | DOC-010 ownership |
|---|---|
| All top-level routes | Search, stable deep links, responsive layout checks, accessibility checks, and docs validation policy. |
| `/choose-your-path` | Keyboard/focus/label/contrast/static-fallback requirements for selectors, command blocks, and install workflow layouts. |
| `/spec-kit-lifecycle` | Static fallback diagram and accessible visualizer behavior if DOC-005/DOC-006 add an interactive lifecycle view. |
| `/glossary` | Glossary/deep-link conventions, findability, and definition pages suitable for support links. |

## DOC-002 Consumption

DOC-002 should consume this report as the stack and IA decision record:

- Create the Docusaurus/MDX docs-site shell.
- Add the package files, lockfile, site config, route shell, nav/sidebar, and basic build command in DOC-002.
- Use the IA skeleton as the top-level route contract.
- Preserve content ownership: DOC-002 owns route shell and skeletal landing/navigation; DOC-003 through DOC-010 own full route content as listed.
- Preserve DOC-010 hardening ownership for search, accessibility, responsive UX, deep links, and docs validation across the affected routes.
- Keep Docusaurus if a GitHub Pages failure is configuration-only and can be fixed through DOC-002/DOC-010 site config, Actions wiring, or package-script normalization.
- Do not re-run framework selection unless new evidence creates a hard blocker for Docusaurus on GitHub Pages, MDX interactivity, accessibility fallback, dependency policy, or maintainability.
- If a true Docusaurus hard blocker appears, follow the fallback order in this report: Astro/Starlight, VitePress, then repo-native Markdown fallback.

## Scope Boundary Evidence

DOC-001 implementation is complete only if it remains research-only and avoids site/package/plugin behavior changes. The PR branch also contains the source PRD/roadmap scaffold that enabled DOC-001; the DOC-001 implementation output is the research report plus SpecKit artifacts.

Forbidden DOC-001 changes include:

- `package.json`, lockfiles, site config, generated site directories, or prototype components
- `.github/workflows/**`
- `.claude-plugin/**`, `.agents/plugins/**`, `dist/**`, or marketplace/generated payload files
- `README.md`, `speckit-pro/README.md`, plugin behavior files, hooks, skills, agents, or scripts

Verification on 2026-06-12:

| Check | Result |
|---|---|
| Branch diff scope | `git diff --name-only origin/main...HEAD` listed 23 files: PRD/roadmap scaffold, this research report, and DOC-001 SpecKit artifacts. |
| Post-scaffold DOC-001 scope | `git diff --name-only origin/doc-001-static-docs-framework-and-ia-spike...HEAD` listed 17 files: this research report plus DOC-001 process/spec/checklist/task artifacts. |
| Forbidden surface scan | Both diff scopes returned 0 matches for package files, lockfiles, site configs, generated site directories, CI workflows, README migrations, marketplace/generated payload files, and plugin behavior files. |
| IA route coverage | 11 required route labels are present in the IA skeleton with route path, Diataxis mode, audience, purpose, source evidence, success criterion, shell owner, and full content owner. |
| Structural validation | `bash tests/speckit-pro/run-all.sh --layer 1` passed `978/978`. |
| Default deterministic suite | `bash tests/speckit-pro/run-all.sh` passed `2587/2587`. |

## Traceability

| Requirement / criterion | Evidence |
|---|---|
| FR-001, FR-002, FR-003, FR-004, FR-005 | `Live Source Evidence`, `Support Class Legend and Evidence Bounds`, `Candidate Matrix`, and `Candidate Decisions` compare Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback with retrieval dates and support classes. |
| FR-006, SC-004 | `Recommended Package and Commands for DOC-002` names `pnpm` and report-only setup, install, preview, build, validation, static preview, and deployment command roles. |
| FR-007, FR-008, SC-003 | `IA Skeleton for DOC-002` records all 11 route labels and every required route field with no placeholder values. |
| FR-009 | This file is the required spike report: `docs/ai/research/interactive-documentation-framework-spike.md`. |
| FR-010, FR-011, SC-005 | `Scope Boundary Evidence` records the final diff checks and confirms 0 forbidden implementation surfaces changed. |
| SC-001, SC-002, SC-006 | The matrix covers 4 candidates across more than 10 dimensions; `Decision` and `Candidate Decisions` make the default/rejected options reviewable; source evidence uses the 2026-06-12 retrieval date. |

## PR Review Packet Source Notes

Use these notes when updating the PR body:

- **What changed**: Added the interactive documentation PRD/roadmap scaffold, DOC-001 SpecKit artifacts, and this research decision record.
- **Why**: DOC-002 needs an approved static docs framework and route-level IA before creating package files, site config, shell routes, or CI.
- **Non-goals**: No docs-site scaffold, package files, lockfiles, site config, CI workflow, README migration, interactive widgets, marketplace/generated payloads, or plugin behavior changes.
- **Review order**: Start with `docs/ai/research/interactive-documentation-framework-spike.md`, then review `specs/doc-001-static-docs-framework-and-ia-spike/spec.md`, `plan.md`, `tasks.md`, and the checklist files.
- **Scope budget**: Research/process-only branch; task-gate size warning is recorded in `specs/doc-001-static-docs-framework-and-ia-spike/.process/reviewability/tasks-gate.json` and final reviewability must remain a backstop.
- **Verification evidence**: Layer 1 passed `978/978`; default deterministic suite passed `2587/2587`; diff-scope scan found 0 forbidden implementation surfaces.
- **Known gaps**: DOC-002 owns concrete Docusaurus scaffold/config decisions and DOC-010 owns deterministic docs validation, accessibility, responsive checks, search hardening, and deep-link policy.
- **Rollback**: Revert the DOC-001 commits to remove the research/spec artifacts; no runtime or package state is introduced by this spike.

## Known Gaps and Follow-Ups

- DOC-002 must make the concrete Docusaurus directory/config decision.
- DOC-002 must refresh the Docusaurus/GitHub Pages path and apply the fallback rules if a true hard blocker appears.
- DOC-002 or DOC-010 must decide official Algolia DocSearch versus community local search.
- DOC-010 should add deterministic docs validation, link checking policy, accessibility checks, and responsive/browser verification once the site exists.
- DOC-003 and DOC-004 should refresh platform install docs again before writing full install content because Claude Code and Codex plugin behavior may change.

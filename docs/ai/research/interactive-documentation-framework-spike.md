# DOC-001: Interactive Documentation Framework Spike

**Date**: 2026-06-12  
**Initial retrieval date for live framework/platform sources**: 2026-06-12
**Decision update date**: 2026-06-13
**Status**: Recommended for DOC-002 handoff, updated after Astro/Starlight plugin refresh and portfolio-context review
**Scope**: Research-only decision record. No site scaffold, package files, lockfiles, CI workflows, marketplace files, generated payloads, README migrations, prototype components, or plugin behavior changes.

## Decision

Recommend **Astro with Starlight** as the default static documentation stack for DOC-002.

DOC-002 should implement the docs shell with Astro, Starlight, MDX pages/components, GitHub Pages deployment from this repository, and `pnpm` as the recommended package manager unless a new hard blocker appears before implementation.

## Why This Wins

Astro/Starlight is the best fit because it satisfies the hard blockers while aligning the documentation stack with the upcoming Racecraft Systems website and Focusengine product website, both of which are expected to use Astro. That portfolio alignment should reduce long-term design-system, component, deployment, and contributor-context drift across Racecraft web properties.

Starlight also provides strong docs-specific defaults: built-in Pagefind search, MDX/component authoring, sidebar/navigation conventions, Astro GitHub Pages deployment, and a community plugin path for docs versioning and internal link validation. Docusaurus still has the strongest first-party docs-governance story, but full docs versioning is not a DOC-002 launch requirement and should not outweigh Astro portfolio alignment unless near-term users need docs pinned to older plugin versions.

The main tradeoff is support class. Starlight's versioning and link-validation paths are community-supported, not first-party. DOC-002 should record whether it includes `starlight-links-validator` immediately, defers `starlight-versions`, and treats docs versioning as a future requirement triggered by meaningful behavior divergence across released plugin versions.

## DOC-002 Failure Handling and Fallback Rules

DOC-002 should refresh official Astro, Starlight, Starlight plugin, and GitHub Pages docs before scaffolding. If Astro/Starlight still satisfies the hard blockers and the failure is limited to repository configuration, `base`, `trailingSlash`, package-script naming, or GitHub Actions wiring, DOC-002 should keep Astro/Starlight and fix the configuration instead of reopening stack selection.

If Astro/Starlight cannot satisfy GitHub Pages hosting, MDX/component authoring, static/keyboard fallback, or maintainability requirements from this repository without violating a hard blocker, DOC-002 should stop the scaffold path, record the blocker, and use this fallback order:

1. **Docusaurus/MDX** if first-party docs versioning, first-party production-build broken-link behavior, or mature docs-governance support becomes more important than Astro portfolio alignment.
2. **VitePress** if Vue-in-Markdown is acceptable and built-in local search/minimal framework weight becomes more important than Astro alignment, with custom versioning/link-check work recorded as a tradeoff.
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
| [Astro: Why Astro?](https://docs.astro.build/en/concepts/why-astro/) | 2026-06-13 | Astro is a content-driven web framework for fast, SEO-friendly sites with UI-framework flexibility and content collections. |
| [Starlight homepage](https://starlight.astro.build/) | 2026-06-13 | Starlight is powered by Astro and includes docs navigation, search, i18n, SEO, typography, code highlighting, dark mode, and component support. |
| [Starlight getting started](https://starlight.astro.build/getting-started/) | 2026-06-13 | Starlight is a full-featured documentation theme built on Astro and can be scaffolded with `pnpm create astro --template starlight`. |
| [Starlight components](https://starlight.astro.build/components/using-components/) | 2026-06-12 | Starlight supports MDX components, built-in components, and UI framework components in MDX. |
| [Starlight site search](https://starlight.astro.build/guides/site-search/) | 2026-06-12 | Starlight includes built-in full-text search powered by Pagefind. |
| [Starlight sidebar](https://starlight.astro.build/guides/sidebar/) | 2026-06-12 | Starlight supports autogenerated and frontmatter-customized sidebar navigation. |
| [Starlight plugins and integrations](https://starlight.astro.build/resources/plugins/) | 2026-06-13 | Starlight documents official and community plugins; the community list includes `starlight-versions` and `starlight-links-validator`. |
| [starlight-versions](https://starlight-versions.vercel.app/) | 2026-06-13 | Community Starlight plugin for versioning documentation pages. |
| [starlight-links-validator](https://starlight-links-validator.vercel.app/) | 2026-06-13 | Community Starlight plugin for validating internal Markdown/MDX links during production builds. |
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

## Portfolio Context Added 2026-06-13

The upcoming Racecraft Systems website and Focusengine product website are expected to use Astro. DOC-001 treats that as a strategic maintainability factor, not as a hard blocker by itself. The effect is that Astro/Starlight gains weight for shared implementation knowledge, shared component/design-system options, shared deployment patterns, and lower long-term context switching across Racecraft web properties.

## Support Class Legend and Evidence Bounds

Use these support-class labels when reading the matrix:

- **Built-in**: ships in the framework or default docs theme.
- **Official**: documented by the framework/platform maintainers, but may require configuration or a first-party integration.
- **Official third-party hosted**: officially supported by the framework, but provided by an external hosted service.
- **Community**: supported through community-maintained packages or patterns, not first-party docs.
- **Community listed by official docs**: community-supported, but discoverable from an official framework plugin catalog.
- **External/manual**: possible through separate tools or hand-maintained repo practice.
- **Unsupported/blocked**: no acceptable path for DOC-001 requirements without changing the candidate's scope.
- **Unknown/weak**: the 2026-06-12 official-source refresh did not identify first-party support comparable to another candidate.

Negative findings are intentionally bounded. "No refreshed first-party versioning path found" and "link checking likely needs extra tooling" mean the official first-party source set refreshed on 2026-06-12 did not show a first-party docs versioning or production-build broken-link gate comparable to Docusaurus. The 2026-06-13 community-plugin refresh found `starlight-versions` and `starlight-links-validator`, which provide credible community paths for those needs but do not change their support class to first-party. DOC-002 must refresh official docs and selected plugin docs again before installing packages or configuring the site.

Version-sensitive observations are evidence freshness markers, not package pins. The Docusaurus docs opened at version 3.10.1 on 2026-06-12, while VitePress docs showed 2.0.0-alpha.17 with a link to 1.6.4. npm metadata observed on 2026-06-13 listed `@astrojs/starlight` 0.40.0, `starlight-versions` 0.9.0, and `starlight-links-validator` 0.24.1. DOC-002 should install the current recommended versions after a fresh source check.

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
| Link checking | High | Built-in/official: production build can fail on broken links | Unknown/weak: refreshed official docs did not identify comparable first-party link-check gate; external checker likely | Community: `starlight-links-validator` validates internal Markdown/MDX links during production builds; not first-party | External/manual: separate checker needed |
| Versioning | Medium/future | Built-in/official: docs versioning CLI and versioned docs | Unknown/weak: refreshed official docs did not identify a first-party docs versioning path | Community: `starlight-versions` versions documentation pages; not first-party and marked early/opinionated | External/manual: copies, branches, or convention |
| Docs-as-code workflow | Medium | Built-in/official: Markdown/MDX, sidebars, GitHub Actions | Built-in/official: Markdown/Vue, GitHub Actions | Built-in/official: content collections/Starlight, GitHub Actions | Built-in repo practice for simple Markdown, weak for site UX |
| Maintenance load | Tie-breaker | Qualitative: medium-high for portfolio fit; docs-focused and mature, but adds a React/Docusaurus web stack beside Astro portfolio sites | Qualitative: low-medium; lightweight but Vue-specific and no portfolio precedent | Qualitative: medium-low; Astro/Starlight plus optional community plugins, offset by shared Astro portfolio direction | Qualitative: low initially, high once required features are rebuilt manually |
| Package/build/test commands | Required | Official: Docusaurus documents scaffold, install, start, build, and serve command roles; DOC-002 must define actual scripts | Official: `docs:build`/`docs:preview` scripts documented | Official: Starlight starter plus Astro dev/build/deploy command path; DOC-002 must define actual scripts | External/manual: validation can stay Markdown-only, but no framework command baseline exists |

## Accessibility and Interaction Guardrails

Reusable interactivity is not an accessibility claim by itself. DOC-002, DOC-006, and DOC-010 must keep every selector, copyable command block, metadata checker, decision tree, glossary popover, and lifecycle visualizer usable without relying on inaccessible dynamic behavior.

Minimum guardrails for later implementation:

- Provide a static Markdown table, static diagram, or equivalent non-JavaScript path for critical instructions and decisions.
- Preserve keyboard operation, visible focus, labels or accessible names, understandable status/error text, and contrast/reflow expectations.
- Avoid browser-side local command execution, config mutation, or hidden permission grants.
- Treat any component that cannot satisfy keyboard and static fallback requirements as out of scope until it is replaced with static content or redesigned.
- Leave accessibility tool selection, responsive/browser verification, and docs CI enforcement to DOC-010.

## Candidate Decisions

### Astro/Starlight: Accept

**Acceptance reason**: Astro/Starlight satisfies the hard blockers, provides built-in Pagefind search, supports MDX/components, deploys to GitHub Pages through Astro, and aligns with the upcoming Racecraft Systems and Focusengine Astro websites. That alignment should reduce long-term toolchain and design-system fragmentation across Racecraft's public web surfaces.

**Tradeoff**: Versioning and link validation are community-supported rather than first-party. This is acceptable because full docs versioning is not a launch requirement, Starlight has credible community plugins for both needs, and DOC-010 can harden validation policy once the site exists.

### Docusaurus/MDX: Defer

**Deferral reason**: Docusaurus remains the strongest docs-governance option because first-party versioning and production-build broken-link behavior are built into the framework path. It is no longer the default because those strengths are not launch hard blockers, Docusaurus local search is community-supported, and it would introduce a separate React/Docusaurus web stack beside Racecraft's planned Astro portfolio.

**Best future use**: Choose Docusaurus if DOC-002 or a later docs release determines that first-party docs versioning, first-party link enforcement, or mature docs-governance conventions are more important than Astro portfolio alignment.

### VitePress: Reject for Default

**Rejection reason**: VitePress is strong for lightweight docs, Vue component interactivity, GitHub Pages, and built-in local search. It is weaker for this repo because the official docs source set refreshed on 2026-06-12 did not identify a first-party docs-versioning workflow or first-party production-build link-checking gate comparable to Docusaurus, and the repository has no existing Vue tooling precedent.

**Evidence bound**: This is a bounded negative finding, not an ecosystem-wide unsupported claim. If DOC-002 finds newer official VitePress documentation for versioning or link checking, it should update the comparison before implementation.

**Best future use**: Reconsider only if DOC-002 prioritizes minimal framework weight or Vue-specific authoring above Astro portfolio alignment.

### Repo-Native Fallback: Reject for Default, Retain as Emergency Fallback

**Fallback assessment**: Repo-native Markdown is evaluated as a serious low-dependency fallback. It preserves current docs-as-code reviewability, avoids a Node/site toolchain, avoids new package or lockfile maintenance, and can still support a static IA through ordinary Markdown pages and repository navigation.

**Rejection reason**: It is not the default because it fails reusable rich interactivity, site search, first-party docs versioning, and build-time docs validation without rebuilding those capabilities manually.

**Fallback condition**: Use only if Astro/Starlight, Docusaurus, and VitePress are later blocked by GitHub Pages feasibility, dependency policy, or maintainership constraints.

## Recommended Package and Commands for DOC-002

These are command roles, not DOC-001-created scripts. DOC-001 does not create or run them as implementation. DOC-002 must either define matching package scripts after scaffolding or update the handoff to the actual scripts created by the scaffold.

| Command role | Report-only recommendation |
|---|---|
| Package manager | `pnpm` |
| Future scaffold/setup | Use the current Astro/Starlight scaffold path, such as `pnpm create astro --template starlight`, in the DOC-002-owned docs-site path. DOC-002 chooses the final directory and commits the generated `package.json` and `pnpm-lock.yaml`. |
| Future dependency install | `pnpm install` after DOC-002 creates the site package files. |
| Future development preview | `pnpm dev` or the equivalent Astro dev script DOC-002 defines. |
| Future production build | `pnpm build` as the minimum site build; add `starlight-links-validator` in DOC-002 or DOC-010 if internal-link validation is required before deployment. |
| Future local static preview | `pnpm preview` or the equivalent Astro preview script DOC-002 defines after a production build. |
| Future minimum validation/test | The Astro production build is the minimum docs-site validation command; internal-link validation should be enabled through `starlight-links-validator` when DOC-002 or DOC-010 formalizes the docs validation gate. Existing repository structural checks run only when plugin/spec surfaces are touched. |
| Future GitHub Pages deployment | GitHub Actions Pages workflow from this repository using Astro's GitHub Pages guidance; configure Astro `site`, `base`, `trailingSlash`, and output path handling in DOC-002/DOC-010 as appropriate |

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

- Create the Astro/Starlight docs-site shell.
- Add the package files, lockfile, site config, route shell, nav/sidebar, and basic build command in DOC-002.
- Use the IA skeleton as the top-level route contract.
- Preserve content ownership: DOC-002 owns route shell and skeletal landing/navigation; DOC-003 through DOC-010 own full route content as listed.
- Preserve DOC-010 hardening ownership for search, accessibility, responsive UX, deep links, and docs validation across the affected routes.
- Keep Astro/Starlight if a GitHub Pages failure is configuration-only and can be fixed through DOC-002/DOC-010 site config, Actions wiring, or package-script normalization.
- Do not re-run framework selection unless new evidence creates a hard blocker for Astro/Starlight on GitHub Pages, MDX/component interactivity, accessibility fallback, dependency policy, or maintainability.
- If a true Astro/Starlight hard blocker appears, follow the fallback order in this report: Docusaurus/MDX, VitePress, then repo-native Markdown fallback.

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
| Branch diff scope | Initial branch diff was limited to PRD/roadmap scaffold, this research report, DOC-001 SpecKit artifacts, and final process evidence; current branch diff scope is recorded in the 2026-06-13 update below. |
| Post-scaffold DOC-001 scope | `git diff --name-only origin/doc-001-static-docs-framework-and-ia-spike...HEAD` listed 24 files: this research report plus DOC-001 process/spec/checklist/task artifacts and final process evidence. |
| Forbidden surface scan | Both diff scopes returned 0 matches for package files, lockfiles, site configs, generated site directories, CI workflows, README migrations, marketplace/generated payload files, and plugin behavior files. |
| IA route coverage | 11 required route labels are present in the IA skeleton with route path, Diataxis mode, audience, purpose, source evidence, success criterion, shell owner, and full content owner. |
| Structural validation | `bash tests/speckit-pro/run-all.sh --layer 1` passed `978/978`. |
| Default deterministic suite | `bash tests/speckit-pro/run-all.sh` passed `2587/2587`. |

Decision update verification on 2026-06-13:

| Check | Result |
|---|---|
| Stale recommendation scan | Decision-update scan found no obsolete default-stack wording in the research report; the later consistency pass updates related workflow, PRD, roadmap, traceability, UAT, and process evidence to match Astro/Starlight. |
| Current branch diff scope | `git diff --name-only origin/main...HEAD` lists 32 files after PR packet and validation artifacts were added. |
| Whitespace check | `git diff --check` passed. |
| Structural validation | `bash tests/speckit-pro/run-all.sh --layer 1` passed `978/978`. |
| Post-merge MOC stale-index validation | `bash tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh` passed `11/11`. |
| Post-merge PR packet validation | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh specs/doc-001-static-docs-framework-and-ia-spike/.process/pr-packets/pr-163.json` passed. |
| Post-merge default deterministic suite | `bash tests/speckit-pro/run-all.sh` passed `2915/2915`. |

## Traceability

| Requirement / criterion | Evidence |
|---|---|
| FR-001, FR-002, FR-003, FR-004, FR-005 | `Live Source Evidence`, `Support Class Legend and Evidence Bounds`, `Candidate Matrix`, and `Candidate Decisions` compare Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback with retrieval dates and support classes. |
| FR-006, SC-004 | `Recommended Package and Commands for DOC-002` names `pnpm` and report-only setup, install, preview, build, validation, static preview, and deployment command roles. |
| FR-007, FR-008, SC-003 | `IA Skeleton for DOC-002` records all 11 route labels and every required route field with no placeholder values. |
| FR-009 | This file is the required spike report: `docs/ai/research/interactive-documentation-framework-spike.md`. |
| FR-010, FR-011, SC-005 | `Scope Boundary Evidence` records the final diff checks and confirms 0 forbidden implementation surfaces changed. |
| SC-001, SC-002, SC-006 | The matrix covers 4 candidates across more than 10 dimensions; `Decision` and `Candidate Decisions` make the default/rejected options reviewable; source evidence uses the 2026-06-12 initial retrieval date and 2026-06-13 update date where applicable. |

## PR Review Packet Source Notes

Use these notes when updating the PR body:

- **What changed**: Added the interactive documentation PRD/roadmap scaffold, DOC-001 SpecKit artifacts, and this research decision record.
- **Why**: DOC-002 needs an approved static docs framework and route-level IA before creating package files, site config, shell routes, or CI.
- **Non-goals**: No docs-site scaffold, package files, lockfiles, site config, CI workflow, README migration, interactive widgets, marketplace/generated payloads, or plugin behavior changes.
- **Review order**: Start with `docs/ai/research/interactive-documentation-framework-spike.md`, then review `specs/doc-001-static-docs-framework-and-ia-spike/spec.md`, `plan.md`, `tasks.md`, and the checklist files.
- **Scope budget**: Research/process-only branch; task-gate size warning is recorded in `specs/doc-001-static-docs-framework-and-ia-spike/.process/reviewability/tasks-gate.json`, and the final size-only block proceeds through marker evidence.
- **Verification evidence**: 2026-06-12 Layer 1 passed `978/978`; default deterministic suite passed `2587/2587`; diff-scope scan found 0 forbidden implementation surfaces. 2026-06-13 decision update Layer 1 passed `978/978`; `git diff --check` passed. Post-merge validation passed MOC stale-index `11/11`, PR packet validation, and the default deterministic suite `2915/2915`.
- **Known gaps**: DOC-002 owns concrete Astro/Starlight scaffold/config decisions and DOC-010 owns deterministic docs validation, accessibility, responsive checks, search hardening, versioning policy, and deep-link policy.
- **Rollback**: Revert the DOC-001 commits to remove the research/spec artifacts; no runtime or package state is introduced by this spike.

## Known Gaps and Follow-Ups

- DOC-002 must make the concrete Astro/Starlight directory/config decision.
- DOC-002 must refresh the Astro/Starlight/GitHub Pages path and apply the fallback rules if a true hard blocker appears.
- DOC-002 or DOC-010 must decide whether to add `starlight-links-validator` immediately or defer link-validation enforcement to DOC-010.
- DOC-010 should add deterministic docs validation, link checking policy, accessibility checks, responsive/browser verification, and a versioning trigger policy once the site exists.
- DOC-003 and DOC-004 should refresh platform install docs again before writing full install content because Claude Code and Codex plugin behavior may change.

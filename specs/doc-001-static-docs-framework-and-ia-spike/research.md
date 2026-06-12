# Phase 0 Research: Static docs framework and IA spike

**Date**: 2026-06-12  
**Retrieval date for live framework/platform sources**: 2026-06-12  
**Full decision record**: [docs/ai/research/interactive-documentation-framework-spike.md](../../docs/ai/research/interactive-documentation-framework-spike.md)

## Decision

Recommend **Docusaurus with MDX** as the default DOC-002 stack, deployed to GitHub Pages from this repository.

Use **pnpm** as the report-only package-manager recommendation for DOC-002 because Docusaurus supports pnpm commands in its official workflow and this repository has no existing Node lockfile to preserve. DOC-001 does not create `package.json`, lockfiles, site config, CI, generated payloads, marketplace files, README migrations, or plugin behavior changes.

If Docusaurus GitHub Pages deployment fails in DOC-002, configuration-only failures should keep Docusaurus in scope. A true hard blocker should route to Astro/Starlight, then VitePress, then repo-native Markdown fallback.

## Rationale

Docusaurus/MDX is the strongest fit for the hard blockers and weighted tradeoffs:

- GitHub Pages support is documented for Docusaurus, including same-repository GitHub Actions deployment and `baseUrl`/trailing-slash considerations.
- MDX/React support is first-party and directly matches the requirement for reusable interactive components.
- Versioning is first-party and maps well to plugin documentation over time.
- Broken-link behavior is built into the production build, which supports the high-weight link-checking criterion.
- Search is the main tradeoff: Docusaurus has first-class Algolia DocSearch support, while local search is community-supported. DOC-002 should decide whether official hosted search is acceptable or whether to add a local-search plugin with the tradeoff recorded.

## Alternatives Considered

| Candidate | Decision | Reason |
|---|---|---|
| Docusaurus/MDX | Accept | Best combined support for MDX interactivity, GitHub Pages, versioning, docs IA, and build-time broken-link enforcement. |
| VitePress | Reject for default | Strong local search and lightweight Vue-in-Markdown authoring, but no refreshed first-party versioning path was found and the repo has no Vue precedent. |
| Astro/Starlight | Defer | Strong built-in Pagefind search, MDX components, and GitHub Pages deployment through Astro, but first-party versioning/link-checking evidence is weaker than Docusaurus for this repo's needs. |
| Repo-native fallback | Reject for default; retain as emergency fallback | Lowest dependency and strongest short-term reviewability, but it does not satisfy rich component interactivity, site search, route-level IA, versioning, or build validation without adding separate tooling. |

## Resolved Questions

| Unknown | Resolution |
|---|---|
| Final static-site framework | Docusaurus/MDX. |
| Package manager | pnpm, report-only for DOC-002. |
| GitHub Pages feasibility | Feasible through Docusaurus static output and GitHub Actions/Pages configuration. |
| Docusaurus failure handling | Keep Docusaurus for configuration-only GitHub Pages failures; route true hard blockers to Astro/Starlight, VitePress, then repo-native Markdown fallback. |
| Whether a prototype is needed | No. DOC-001 remains research-only. |
| DOC-002 handoff | DOC-002 should create the Docusaurus shell, routes, nav/sidebar, package files, lockfile, and basic build validation using this report. |

## Evidence Summary

Official Docusaurus docs refreshed on 2026-06-12 show static build output, GitHub Pages deployment, MDX/React support, first-class Algolia search support, versioned docs, and build-time broken-link handling. Official VitePress docs show GitHub Pages deployment, Vue component use in Markdown, and built-in local search. Official Astro/Starlight docs show GitHub Pages deployment via Astro, MDX component support, and built-in Pagefind search. Official GitHub Pages docs confirm Pages hosts static HTML/CSS/JS from a repository and can publish via a build process.

Support classes are recorded in the full decision record as built-in, official, official third-party hosted, community, external/manual, unsupported/blocked, or unknown/weak. Negative findings for VitePress and Astro/Starlight versioning/link-checking are bounded to the official source set refreshed on 2026-06-12; they mean no first-party path comparable to Docusaurus was found during the refresh, not that the broader ecosystem cannot solve those needs.

Docusaurus docs opened at version 3.10.1 on 2026-06-12. That version observation is evidence freshness, not a DOC-002 package pin.

No hard blocker was found for Docusaurus. Search remains the main documented tradeoff and is not a stack blocker by itself unless it creates unacceptable dependency, cost, policy, or maintainership risk.

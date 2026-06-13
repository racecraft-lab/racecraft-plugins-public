# Phase 0 Research: Static docs framework and IA spike

**Date**: 2026-06-12  
**Initial retrieval date for live framework/platform sources**: 2026-06-12
**Decision update date**: 2026-06-13
**Full decision record**: [docs/ai/research/interactive-documentation-framework-spike.md](../../docs/ai/research/interactive-documentation-framework-spike.md)

## Decision

Recommend **Astro with Starlight** as the default DOC-002 stack, deployed to GitHub Pages from this repository.

Use **pnpm** as the report-only package-manager recommendation for DOC-002 because Starlight's official quick start supports `pnpm create astro --template starlight` and this repository has no existing Node lockfile to preserve. DOC-001 does not create `package.json`, lockfiles, site config, CI, generated payloads, marketplace files, README migrations, or plugin behavior changes.

If Astro/Starlight GitHub Pages deployment fails in DOC-002, configuration-only failures should keep Astro/Starlight in scope. A true hard blocker should route to Docusaurus/MDX, then VitePress, then repo-native Markdown fallback.

## Rationale

Astro/Starlight is the strongest fit for the hard blockers and weighted tradeoffs after the 2026-06-13 update:

- GitHub Pages support is documented for Astro, including static prerendered deployment through GitHub Actions.
- Starlight is built on Astro and provides docs navigation, search, i18n, SEO, typography, code highlighting, dark mode, and component support.
- MDX/component support matches the requirement for reusable interactive docs content.
- Built-in Pagefind search avoids making search dependent on a hosted third-party service for launch.
- The upcoming Racecraft Systems website and Focusengine product website are expected to use Astro, making Astro/Starlight the lower-friction portfolio stack.
- Versioning and link checking have credible community plugin paths through `starlight-versions` and `starlight-links-validator`, but those remain community support classes rather than first-party.
- Full docs versioning is treated as a future requirement, not a DOC-002 launch blocker, unless older plugin versions need maintained docs immediately.

## Alternatives Considered

| Candidate | Decision | Reason |
|---|---|---|
| Astro/Starlight | Accept | Best combined fit for GitHub Pages, MDX/component interactivity, built-in local search, docs IA, and Astro portfolio alignment; versioning/link validation have community plugin paths. |
| Docusaurus/MDX | Defer | Strongest first-party docs governance, versioning, and production-build broken-link behavior, but weaker portfolio fit and local search is community-supported. |
| VitePress | Reject for default | Strong local search and lightweight Vue-in-Markdown authoring, but no refreshed first-party versioning path was found and the repo has no Vue precedent. |
| Repo-native fallback | Reject for default; retain as emergency fallback | Lowest dependency and strongest short-term reviewability, but it does not satisfy rich component interactivity, site search, route-level IA, versioning, or build validation without adding separate tooling. |

## Resolved Questions

| Unknown | Resolution |
|---|---|
| Final static-site framework | Astro/Starlight. |
| Package manager | pnpm, report-only for DOC-002. |
| GitHub Pages feasibility | Feasible through Astro static prerendered output and GitHub Actions/Pages configuration. |
| Astro/Starlight failure handling | Keep Astro/Starlight for configuration-only GitHub Pages failures; route true hard blockers to Docusaurus/MDX, VitePress, then repo-native Markdown fallback. |
| Whether a prototype is needed | No. DOC-001 remains research-only. |
| DOC-002 handoff | DOC-002 should create the Astro/Starlight shell, routes, nav/sidebar, package files, lockfile, and basic build validation using this report. |

## Evidence Summary

Official Docusaurus docs refreshed on 2026-06-12 show static build output, GitHub Pages deployment, MDX/React support, first-class Algolia search support, versioned docs, and build-time broken-link handling. Official VitePress docs show GitHub Pages deployment, Vue component use in Markdown, and built-in local search. Official Astro/Starlight docs show GitHub Pages deployment via Astro, MDX component support, built-in Pagefind search, and Starlight's docs-specific theme/toolkit role. Official GitHub Pages docs confirm Pages hosts static HTML/CSS/JS from a repository and can publish via a build process.

Support classes are recorded in the full decision record as built-in, official, official third-party hosted, community, external/manual, unsupported/blocked, or unknown/weak. Negative findings for VitePress and Astro/Starlight first-party versioning/link-checking are bounded to the official source set refreshed on 2026-06-12. The 2026-06-13 update found Starlight community plugin paths for docs versioning and internal link validation, so Astro/Starlight no longer carries an ecosystem-capability gap there; the tradeoff is support class and maturity.

Docusaurus docs opened at version 3.10.1 on 2026-06-12. npm metadata observed on 2026-06-13 listed `@astrojs/starlight` 0.40.0, `starlight-versions` 0.9.0, and `starlight-links-validator` 0.24.1. These version observations are evidence freshness markers, not DOC-002 package pins.

No hard blocker was found for Astro/Starlight. Community plugin support for versioning and link validation remains the main documented tradeoff and is not a stack blocker by itself unless it creates unacceptable dependency, policy, or maintainership risk.

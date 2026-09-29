Priority: minor

## Summary

Public docs pages still carry internal planning scaffolding: DOC-005 example ids, 'Route Shell' blocks and spec-id link labels. The first-run tutorial ends with a docs-site maintainer step that contradicts the repository rule, and the lifecycle explainer stops at Implement. The site config also hard-codes the base path in several files and keeps three copies of one route-key mapping.

## Evidence

- **docs-005** (minor): The public first-run tutorial ends with 'For DOC-005-style docs work' and tells users to cd docs-site then run pnpm validate, contradicting the repo rule (docs-site/AGENTS.md, REVIEW.md) to run pnpm --dir docs-site from the root. The step is docs-site maintainer work, not a first-run check for a user's own project. It also uses DOC-005 example ids throughout and checks the Spec Kit version with 'specify version' while the install skill and troubleshooting page use 'specify --version'.
  - `docs-site/src/content/docs/first-run.md:132-138`, `docs-site/src/content/docs/first-run.md:30`, `speckit-pro/skills/speckit-install/SKILL.md:39`, `docs-site/AGENTS.md:5`
- **docs-006** (minor): The lifecycle explainer is written for the DOC-005 docs feature ('Changed docs files, static component', 'docs validation output', 'Docs changes'). It also stops at Implement: the confidence gate (G6.5) appears only as a next action and the pull-request phase is absent, while G7 is described more loosely than the runner's build/type/lint/test and TDD-evidence check. The same phase table is hand-copied in LifecycleFlow.astro and the MDX tables, with small wording differences (G5 'route/marker planning' versus 'route planning').
  - `docs-site/src/content/docs/spec-kit-lifecycle.mdx:28`, `docs-site/src/content/docs/spec-kit-lifecycle.mdx:57`, `docs-site/src/components/LifecycleFlow.astro:96-100`, `speckit-pro/skills/speckit-autopilot/references/gate-validation.md:599-600`
- **docs-011** (minor): Public pages still carry planning scaffolding ('Route Shell', 'Shell owner DOC', 'Full-content owner DOC', 'reference shell') for features that shipped and were archived (DOC-007, DOC-008, DOC-010). The root README links these pages as 'DOC-007 reference shell' and 'DOC-003-owned path'. Users see internal spec ids and descriptions of completed pages as shells.
  - `docs-site/src/content/docs/reference.md:8-14`, `docs-site/src/content/docs/choose-your-path.mdx:13-18`, `docs-site/src/content/docs/glossary.md:10-17`, `README.md:65`, `README.md:140-144`
- **docs-007** (minor): The route-id to key mapping exists as three copies (ogCardKey twice, slugToMdParam once, identical logic). The og:image URL in routeData.ts must match the card key generated in og/[...slug].ts, and comments in both files say they must stay identical, so the contract has no single source.
  - `docs-site/src/pages/og/[...slug].ts:33`, `docs-site/src/routeData.ts:63`, `docs-site/src/pages/[...slug].md.ts:41`
- **docs-009** (minor): astro.config.mjs says the DOC-012 launch flip is a one-place change (update SITE/BASE), but the same file hard-codes the /racecraft-plugins-public/ base in six head link hrefs, and brand.css and site.webmanifest repeat it. The comment overstates the single source.
  - `docs-site/astro.config.mjs:30-33`, `docs-site/astro.config.mjs:182-229`, `docs-site/src/styles/brand.css:29-33`, `docs-site/public/site.webmanifest:5-9`
- **docs-010** (minor): The OG card comment says the indigo accent edge (99,102,241) matches the docs site's brand palette. brand.css defines a blue accent and brand red #dc143c and has no indigo.
  - `docs-site/src/pages/og/[...slug].ts:60-66`, `docs-site/src/styles/brand.css:1-10`

## Proposed fix

- docs-005: Replace step 5 with a validation checkpoint that applies to the user's repository, use the same version command everywhere, and use neutral example ids.
- docs-006: Generalize the Implement and G7 wording, add G6.5 and the PR phase, and feed both the component and the tables from one data source.
- docs-011: Remove the Route Shell blocks and spec-id link labels from user-facing pages, keeping ownership in the roadmap.
- docs-007: Extract one helper into src/lib and import it from the three modules.
- docs-009: Derive the head hrefs from BASE and correct the comment, or list the remaining hard-coded files as part of the DOC-012 checklist.
- docs-010: Use the brand accent tokens in the card options or fix the comment.

## Acceptance

- [ ] User-facing pages carry no internal spec ids or shell blocks, and first-run uses one version command.
- [ ] The lifecycle explainer covers G6.5 and the PR phase from one data source shared by LifecycleFlow.astro and the MDX tables.
- [ ] Route-key mapping lives in one helper; head hrefs derive from BASE; the OG card comment matches brand.css.
- [ ] pnpm --dir docs-site validate passes.

## Related

- None.

Found by the 2026-09 coherence audit.

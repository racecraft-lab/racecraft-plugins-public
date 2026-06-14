# Research: DOC-002 Unified landing page and IA shell

## Sources Used

- `docs/ai/research/interactive-documentation-framework-spike.md`
- `docs/ai/specs/.process/DOC-002-design-concept.md`
- Current official-doc/package refresh supplied for DOC-002 Plan

## Decisions

### Decision: Keep Astro with Starlight

**Rationale**: DOC-001 selected Astro/Starlight for static hosting, MDX/component authoring, Starlight documentation defaults, Pagefind search, and GitHub Pages feasibility. The current refresh did not identify a hard blocker. Astro/Starlight also remains aligned with the portfolio-context rationale recorded in DOC-001.

**Alternatives considered**: Docusaurus remains the fallback if first-party docs governance outweighs Astro alignment. VitePress remains a fallback if Vue/minimal framework weight becomes more important. Repo-native Markdown remains the emergency fallback only if framework candidates are blocked by hosting, dependency, or maintainership constraints.

### Decision: Use docs-site-scoped pnpm and current package pins

**Rationale**: DOC-002 should isolate the docs app from root plugin validation. Use `pnpm` inside `docs-site/` and plan the observed current packages: `astro@6.4.6`, `@astrojs/starlight@0.40.0`, and `@astrojs/check@0.9.9`.

**Alternatives considered**: A root workspace would expand the repository-level Node surface too early. Deferring package decisions would leave DOC-002 less executable. Root npm/yarn commands would drift from the DOC-001 handoff.

### Decision: Select `starlight-links-validator` for internal-link validation

**Rationale**: Q6 selected link validation now, and Q7 limited validation to production build plus links. `starlight-links-validator` is the Starlight-community path recorded by DOC-001 for validating internal Markdown/MDX links during production builds. The implementation should expose a clear docs-site script such as `pnpm validate:links`; the lockfile will capture the resolved validator version.

**Alternatives considered**: Build-only validation was rejected by the user in Q6. Broader docs CI, screenshots, accessibility tooling, and search hardening are deferred to DOC-010. A generic external link checker would add a separate validation surface before the Starlight-native route shell exists.

### Decision: Use build-integrated validation commands

**Rationale**: Astro CLI docs identify `astro dev`, `astro build`, `astro preview`, and `astro check` as the relevant command roles. Astro TypeScript guidance recommends `astro check && astro build` when builds should fail on type/content diagnostics. DOC-002 should define `pnpm validate` as `astro check && astro build`; link validation runs during the `astro build` path through the Starlight validator integration.

**Alternatives considered**: Separate root commands are unavailable before `docs-site/` exists and would mix docs validation with plugin validation. A preview-only check would not prove production output or link correctness.

### Decision: Configure Pages-ready site/base assumptions without a workflow

**Rationale**: Astro GitHub Pages docs recommend the official Astro GitHub Action for deployment, but DOC-002 must not add a publish workflow. DOC-002 should still make config assumptions explicit: GitHub Pages project hosting for `racecraft-lab/racecraft-plugins-public`, `site: "https://racecraft-lab.github.io"`, `base: "/racecraft-plugins-public"`, and `trailingSlash: "always"`. Internal links must be authored through Starlight/Astro routes so the base path is respected.

**Alternatives considered**: Adding `.github/workflows/**` is explicitly out of scope and belongs to DOC-010. Deferring Pages config would risk discovering base/path issues after route content lands.

### Decision: Use Starlight sidebar groups with slug strings

**Rationale**: Starlight sidebar docs support `starlight({ sidebar: [...] })`, groups with `{ label, items }`, and internal doc links with slug strings or `{ slug }`. DOC-002 should group the 11 routes by Diataxis: Tutorials, How-to, Reference, and Explanation.

**Alternatives considered**: A flat list would satisfy raw reachability but weaken the task-oriented IA. Platform-first grouping would bury reference, trust, lifecycle, and contributor paths.

### Decision: Leave Pagefind search at Starlight default

**Rationale**: Starlight config docs state Pagefind search is enabled by default. DOC-002 can rely on that default because DOC-010 owns search policy hardening.

**Alternatives considered**: Disabling search would remove a useful Starlight default. Custom search configuration would expand DOC-002 beyond the shell, routes, and basic validation boundary.

### Decision: Preserve one DOC-002 workflow with two implementation slices

**Rationale**: The design concept accepted a two-slice review intent but kept one DOC-002 roadmap identity. Tasks should preserve Shell/routes first, then Validation/config hardening. If autopilot emits one PR, the PR body must preserve that review order.

**Alternatives considered**: Two separate specs would churn the roadmap and route ownership model. A single unsliced review order would make the warning-level size harder to review.

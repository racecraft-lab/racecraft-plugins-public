# Data Model: DOC-002 Unified landing page and IA shell

DOC-002 is a static documentation shell. The data model describes repository content contracts, not runtime database entities.

## Entity: Documentation Site

| Field | Value |
|-------|-------|
| `root` | `docs-site/` |
| `framework` | Astro with Starlight |
| `packageManager` | `pnpm` scoped to `docs-site/` |
| `deploymentTarget` | GitHub Pages project page for `racecraft-lab/racecraft-plugins-public` |
| `pagesSite` | `https://racecraft-lab.github.io` |
| `pagesBase` | `/racecraft-plugins-public` |
| `trailingSlash` | `always` |
| `publishWorkflowOwner` | DOC-010 |
| `searchPolicy` | Starlight/Pagefind default for DOC-002 |
| `accessibilityPolicy` | Static semantic shell and fallback contract for DOC-002; automated accessibility hardening owned by DOC-010 |
| `minimumCompletionGate` | Local post-install docs-site validation: `pnpm check`, `pnpm build`, `pnpm validate`, and `pnpm validate:links` |

**Validation rules**

- Must not create or modify `.github/workflows/**`.
- Must not modify plugin behavior, generated payloads, marketplace manifests, hooks, agents, or release automation.
- Must expose docs-site-scoped install, build, preview, and validation command roles.
- Must configure Pages-ready `site`, `base`, and `trailingSlash` values without
  adding a publish workflow.
- Must keep the repeatable completion gate local after dependencies are
  installed; dependency installation may require package-registry access, but
  build, check, validation, and link validation must not require deployment,
  external-link crawling, browser screenshots, analytics checks, or remote URL
  availability.
- Must keep critical platform choices, source-vs-payload explanations, route
  orientation, source evidence, and next steps available as semantic static
  content without JavaScript-only behavior.

## Entity: Top-Level Route Shell

| Field | Description |
|-------|-------------|
| `path` | Public route path without GitHub Pages base. |
| `slug` | Starlight sidebar/content slug. |
| `label` | Navigation label shown to users. |
| `diataxisGroup` | One of Tutorials, How-to, Reference, Explanation. |
| `secondaryModes` | Additional Diataxis modes when useful. |
| `audience` | Primary user type for the shell. |
| `purpose` | What the route helps users do. |
| `shellOwnerDoc` | DOC that owns the skeletal shell. |
| `fullContentOwnerDoc` | DOC that owns full content when distinct. |
| `successCriterion` | User-visible proof that the route works. |
| `sourceEvidence` | Local evidence file or research source for the route. |

**Validation rules**

- Every route shell must display purpose, shell owner DOC, full content owner DOC when distinct, success criterion, and source evidence.
- Deferred route shells must include a compact user-facing orientation block
  with audience, useful-now shell content, deferred owner DOC, source evidence,
  and one static next step or related route link.
- The landing page and Reference shell must explain `speckit-pro/` authoring source versus generated payloads under `dist/claude/**` and `dist/codex/**`.
- Deferred content must name the follow-up DOC owner instead of expanding DOC-002 into later work.
- Route shells must use visible page content, headings, and descriptive native
  links for route purpose, owner DOCs, success criterion, source evidence, and
  next steps rather than relying only on frontmatter or visual labels.
- Route shells that DOC-006 may enhance later must preserve an equivalent
  static Markdown/MDX path for selectors, diagrams, glossary aids, and command
  handoffs.

## Entity: Navigation Group

| Field | Description |
|-------|-------------|
| `label` | Diataxis group name: Tutorials, How-to, Reference, or Explanation. |
| `items` | Ordered route shell slugs. |

**Validation rules**

- The Starlight sidebar must expose all four groups.
- Every top-level route shell must appear exactly once in the sidebar.
- Sidebar and page-local navigation must use native links in source order so
  keyboard focus order and screen-reader reading order match the route
  hierarchy.

## Entity: Accessibility Shell Contract

| Field | Description |
|-------|-------------|
| `staticFallback` | Critical route and platform guidance available without JavaScript-only behavior. |
| `keyboardPath` | Native links and controls reachable in meaningful source order. |
| `focusVisibility` | DOC-002 styling must not suppress visible focus indicators. |
| `semanticStructure` | Page title plus ordered headings and landmark-compatible Starlight structure. |
| `linkPurpose` | Link text identifies destination or action for platform choices, evidence, and related routes. |
| `visualMeaning` | Callouts, route status, and source-vs-payload distinctions do not rely on color alone. |
| `responsiveOrder` | Narrow viewport reading order preserves the same content sequence as desktop. |

**Validation rules**

- If DOC-002 adds custom styles, they must preserve Starlight/native focus
  visibility, contrast-compatible callouts, non-color-only meaning, target
  affordance, and readable source order.
- DOC-002 must not introduce custom widgets for core navigation or platform
  choice; later DOC-006 enhancements must keep the static fallback contract.
- DOC-010 owns automated accessibility checks, responsive screenshots, and CI
  policy after the site and interactive aids exist.

## Entity: Source Evidence Link

| Field | Description |
|-------|-------------|
| `path` | Repository-relative evidence path or official source URL named in the research record. |
| `use` | The route or claim supported by the evidence. |
| `boundary` | Whether DOC-002 may summarize, cite, or only point to the source. |

**Validation rules**

- README files are source evidence only. DOC-002 must not convert, redirect, or rewrite them.
- Official docs refresh items supplied to Plan are acceptable evidence for package, Pages, CLI, sidebar, and Pagefind decisions.

## Entity: Validation Command Role

| Field | Command | Script body |
|-------|---------|-------------|
| `install` | `cd docs-site && pnpm install` | N/A |
| `dev` | `cd docs-site && pnpm dev` | `astro dev` |
| `check` | `cd docs-site && pnpm check` | `astro check` |
| `build` | `cd docs-site && pnpm build` | `astro build` |
| `validate` | `cd docs-site && pnpm validate` | `pnpm check && pnpm build` |
| `validateLinks` | `cd docs-site && pnpm validate:links` | `pnpm build` |
| `preview` | `cd docs-site && pnpm preview` | `astro preview` |

**Validation rules**

- `validate` should run `pnpm check && pnpm build`.
- Internal-link validation must run through the production build path with `starlight-links-validator` enabled.
- Validation must not require browser-side local command execution.
- Build failures block DOC-002 when Astro/Starlight config, content/schema,
  route generation, sidebar slugs, or Pages path/base settings prevent static
  output.
- Link-validation failures block DOC-002 only for internal Markdown/MDX route
  links, anchors, trailing slashes, and same-site/base-path mismatches.
- External URL reachability, deployment checks, browser screenshots, analytics,
  and broader docs CI policy are deferred to DOC-010.

## Entity: Error Handling Disposition

| Field | Description |
|-------|-------------|
| `failureClass` | Missing package manager, setup/install failure, check diagnostics, build failure, link-validation failure, Pages mismatch, or framework hard blocker. |
| `blockingScope` | Whether the failure blocks setup, DOC-002 completion, or later DOC-010 hardening. |
| `nextAction` | The concrete maintainer action before rerunning the relevant docs-site command. |
| `fallbackEligible` | Whether the failure can trigger the DOC-001 fallback order. |

**Validation rules**

- Missing `pnpm` blocks setup until `pnpm` is enabled or installed locally; it
  must not change DOC-002 to root `npm`/`yarn` commands or a root workspace.
- `pnpm check`, `pnpm build`, and `pnpm validate:links` failures must point to
  local docs-site fixes first: package scripts, Astro/Starlight config,
  content/frontmatter/schema, route files, sidebar slugs, internal route links,
  anchors, trailing slashes, same-site URLs, or Pages config values.
- Pages base/path mismatches must be fixed by aligning `site`, `base`,
  `trailingSlash`, route slugs, and internal links with GitHub Pages project
  hosting values; they must not add `.github/workflows/**` in DOC-002.
- Framework fallback is eligible only when Astro/Starlight cannot satisfy
  GitHub Pages hosting, MDX/component authoring, accessible static fallback,
  dependency policy, or maintainability after local fixes are attempted or
  ruled out.
- The fallback order is Docusaurus/MDX, then VitePress, then repo-native
  Markdown.

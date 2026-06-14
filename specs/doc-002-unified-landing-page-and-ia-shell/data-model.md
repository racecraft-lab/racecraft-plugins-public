# Data Model: DOC-002 Unified landing page and IA shell

DOC-002 is a static documentation shell. The data model describes repository content contracts, not runtime database entities.

## Entity: Documentation Site

| Field | Value |
|-------|-------|
| `root` | `docs-site/` |
| `framework` | Astro with Starlight |
| `packageManager` | `pnpm` scoped to `docs-site/` |
| `deploymentTarget` | GitHub Pages project page for `racecraft-lab/racecraft-plugins-public` |
| `publishWorkflowOwner` | DOC-010 |
| `searchPolicy` | Starlight/Pagefind default for DOC-002 |

**Validation rules**

- Must not create or modify `.github/workflows/**`.
- Must not modify plugin behavior, generated payloads, marketplace manifests, hooks, agents, or release automation.
- Must expose docs-site-scoped install, build, preview, and validation command roles.

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
- The landing page and Reference shell must explain `speckit-pro/` authoring source versus generated payloads under `dist/claude/**` and `dist/codex/**`.
- Deferred content must name the follow-up DOC owner instead of expanding DOC-002 into later work.

## Entity: Navigation Group

| Field | Description |
|-------|-------------|
| `label` | Diataxis group name: Tutorials, How-to, Reference, or Explanation. |
| `items` | Ordered route shell slugs. |

**Validation rules**

- The Starlight sidebar must expose all four groups.
- Every top-level route shell must appear exactly once in the sidebar.

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

| Field | Command |
|-------|---------|
| `install` | `cd docs-site && pnpm install` |
| `dev` | `cd docs-site && pnpm dev` |
| `check` | `cd docs-site && pnpm check` |
| `build` | `cd docs-site && pnpm build` |
| `validate` | `cd docs-site && pnpm validate` |
| `validateLinks` | `cd docs-site && pnpm validate:links` |
| `preview` | `cd docs-site && pnpm preview` |

**Validation rules**

- `validate` should run `astro check && astro build`.
- Internal-link validation must run through the production build path with `starlight-links-validator` enabled.
- Validation must not require browser-side local command execution.

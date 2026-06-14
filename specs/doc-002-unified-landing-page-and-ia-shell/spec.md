# Feature Specification: Unified landing page and IA shell

**Feature Branch**: `doc-002-unified-landing-page-and-ia-shell`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "/speckit-specify DOC-002 unified landing page and IA shell"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the marketplace and choose a path (Priority: P1)

As a first-time visitor, I can understand Racecraft Public Plugins, the current
`speckit-pro` plugin, supported platforms, why source and generated payloads
differ, and which platform path to choose from the first screen.

**Why this priority**: This is the minimum public docs value. Without a useful
first screen, the shell does not help new users decide whether to continue.

**Independent Test**: A reviewer can open the landing page and confirm that it
states the marketplace purpose, names `speckit-pro`, identifies Claude Code and
Codex as supported paths, explains source versus generated install payloads, and
offers clear next actions without requiring later DOC-owned content.

**Acceptance Scenarios**:

1. **Given** a first-time visitor opens the docs site, **When** they view the
   first screen, **Then** they see the marketplace purpose, current plugin,
   supported platforms, primary value, source-vs-payload distinction, and
   Claude Code/Codex next actions.
2. **Given** a visitor wants to install or evaluate the plugin, **When** they
   choose a platform path from the landing page, **Then** they can navigate to
   the corresponding Claude Code or Codex route shell.

---

### User Story 2 - Navigate the 11-route IA shell (Priority: P2)

As a user with a specific task, I can navigate to one of the 11 top-level IA
routes and see that route's purpose, owner DOC, success criterion, and source
evidence.

**Why this priority**: Stable route contracts let later DOC specs fill content
without changing the information architecture or breaking links.

**Independent Test**: A reviewer can inspect the Starlight navigation and every
top-level route shell to confirm the route exists, is grouped by Diataxis mode,
and displays purpose, ownership, success criterion, and source evidence.

**Acceptance Scenarios**:

1. **Given** the docs shell is built, **When** a user scans navigation, **Then**
   they see Tutorials, How-to, Reference, and Explanation groups.
2. **Given** a user opens any top-level route, **When** they read the route
   shell, **Then** the page identifies its purpose, shell owner DOC, full content
   owner DOC when distinct, success criterion, and source evidence.
3. **Given** a later DOC spec adds full content to an existing route, **When**
   it uses the DOC-002 route contract, **Then** no top-level route rename or
   regrouping is required.

---

### User Story 3 - Validate the docs shell before handoff (Priority: P3)

As a maintainer, I can install, build, preview, and validate internal links for
the Astro/Starlight docs site before publishing or handing the shell to later
DOC specs.

**Why this priority**: The shell must be executable and verifiable before later
content work depends on it.

**Independent Test**: A maintainer can use docs-site-scoped `pnpm` command roles
to install dependencies, run a production build, preview the built site, and run
internal-link validation without adding a GitHub Pages publish workflow.

**Acceptance Scenarios**:

1. **Given** `docs-site/` exists, **When** a maintainer follows the local command
   roles, **Then** dependency install, production build, preview, and
   internal-link validation are available from the docs-site scope.
2. **Given** DOC-002 has Pages-ready configuration, **When** a reviewer inspects
   the site configuration and repository changes, **Then** Pages assumptions are
   explicit and no GitHub Pages publish workflow has been added.

### Edge Cases

- If a Starlight route shell intentionally defers full content to a later DOC,
  the shell must still provide enough purpose, ownership, source evidence, and
  success criterion for users and maintainers.
- If generated install payload paths under `dist/claude/**` or `dist/codex/**`
  differ from authoring source under `speckit-pro/`, the landing page and
  Reference shell must explain the distinction without changing payload files.
- If README files contain source evidence used by a shell page, DOC-002 must cite
  them as evidence only and must not convert, redirect, or rewrite README
  content.
- If GitHub Pages deployment needs a later workflow, DOC-002 must stop at
  explicit Pages-ready configuration assumptions and leave workflow creation to
  DOC-010.
- If package versions or validator package choices change after DOC-001, DOC-002
  must resolve them in Plan/implementation without reopening the Astro/Starlight
  framework choice unless a hard blocker appears.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create `docs-site/` as the Astro/Starlight site
  app for the public documentation shell.
- **FR-002**: The system MUST keep docs-site package management scoped to
  `docs-site/` using `pnpm` command roles for dependency install, production
  build, static preview, and internal-link validation.
- **FR-003**: The system MUST implement a thin actionable landing page that is
  more useful than a placeholder and does not become a full marketing page.
- **FR-004**: The landing page MUST state the Racecraft Public Plugins
  marketplace purpose, the current `speckit-pro` plugin, primary value, supported
  Claude Code and Codex paths, and next actions.
- **FR-005**: The landing page MUST explain the difference between authoring
  source under `speckit-pro/` and generated install payloads under
  `dist/claude/**` and `dist/codex/**`.
- **FR-006**: The system MUST create skeletal top-level route pages for Start,
  Install: Claude Code, Install: Codex, First Run, Choose Your Path, Reference,
  Troubleshooting, Security & Trust, Contribute & Release, Spec Kit Lifecycle,
  and Glossary.
- **FR-007**: Each route shell MUST show its route purpose, shell owner DOC,
  full content owner DOC when distinct, success criterion, and source evidence.
- **FR-008**: Navigation MUST organize the top-level route shells by Diataxis
  groups: Tutorials, How-to, Reference, and Explanation.
- **FR-009**: Claude Code and Codex paths MUST be selectable from the landing
  page's first interaction without requiring interactive widgets or browser-side
  local command execution.
- **FR-010**: The Reference shell MUST include a source-vs-generated-payload
  explanation suitable for later deep links from install, contributor, and trust
  content.
- **FR-011**: The system MUST include internal-link validation for Markdown/MDX
  route links as part of DOC-002 validation scope.
- **FR-012**: The system MUST include production build verification for the
  Astro/Starlight docs site.
- **FR-013**: Astro/Starlight configuration MUST make GitHub Pages assumptions
  explicit, including site/base/path behavior needed for later deployment.
- **FR-014**: The system MUST NOT add a GitHub Pages publish workflow in DOC-002.
- **FR-015**: DOC-002 MUST consume the DOC-001 Astro/Starlight decision record
  at `docs/ai/research/interactive-documentation-framework-spike.md` and MUST
  NOT reopen framework selection unless a true hard blocker appears.
- **FR-016**: DOC-002 MUST NOT change plugin behavior, marketplace manifests,
  generated payloads, hooks, agents, release automation, or README source files.
- **FR-017**: DOC-002 MUST preserve one workflow identity with two-slice intent:
  shell/routes first, then validation/config hardening.
- **FR-018**: The landing page first screen MUST include a concise purpose and
  value statement, supported-platform choice targets for Claude Code and Codex,
  a short source-vs-generated-payload summary, and one static next action per
  platform; it MUST NOT include full install procedures, long command matrices,
  testimonials, pricing or generic marketing claims, analytics prompts, or full
  content owned by DOC-003 through DOC-010.
- **FR-019**: Each route shell that defers full content to a later DOC MUST
  include user-facing orientation content beyond metadata: who the page is for,
  what is useful now, what is intentionally deferred and which DOC owns it,
  source evidence links, and at least one static next step or related route
  link; it MUST NOT include full platform install, troubleshooting, security,
  contributor, lifecycle, glossary, search, accessibility, or deployment depth
  owned by later DOC specs.
- **FR-020**: DOC-002 route content MUST keep critical platform choices,
  source-vs-generated-payload explanations, route shell metadata, source
  evidence, and next-step links available as semantic static content using
  native document links and headings; it MUST NOT hide this content behind
  JavaScript-only widgets, visual-only controls, or frontmatter-only metadata.
- **FR-021**: DOC-002 MUST define the static fallback contract for later
  DOC-006 interactive aids: any future enhanced selector, command aid, diagram,
  or glossary aid must preserve equivalent static Markdown/MDX content,
  keyboard-reachable controls, visible focus, descriptive labels or link text,
  non-color-only communication, and a meaningful reading order.
- **FR-022**: DOC-002's minimum completion gate MUST be deterministic and
  docs-site-local after dependencies are installed: `pnpm check`, `pnpm build`,
  `pnpm validate`, and `pnpm validate:links` from `docs-site/`. The gate MUST
  NOT require GitHub Pages deployment, browser screenshots, external-link
  crawls, remote official-doc URL checks, analytics checks, or network access
  beyond initial dependency installation or lockfile refresh.
- **FR-023**: DOC-002 MUST document the next action for each setup and
  validation failure class: missing `pnpm`, dependency install or lockfile
  setup failure, `pnpm check` diagnostics, `pnpm build` failure, `pnpm
  validate:links` failure, and GitHub Pages `site`/`base`/`trailingSlash`
  mismatch. Ordinary package-script, content, route, sidebar, and Pages config
  failures MUST be fixed inside DOC-002 and MUST NOT reopen framework selection;
  framework fallback may be used only when Astro/Starlight cannot satisfy a
  hard blocker after those fixes are attempted or ruled out.

### Reviewability Notes *(if applicable)*

- DOC-002 is docs-site and docs-process work. It must not modify plugin runtime
  behavior, marketplace manifests, generated install payloads, hooks, agents, or
  release automation.
- README files are source evidence only. Any README-derived claims should be
  linked or summarized in route shells without converting README content.
- Deferred route depth must name the owning follow-up DOC rather than expanding
  DOC-002 into full install, troubleshooting, security, contributor, lifecycle,
  glossary, search, accessibility, or deployment content.
- Landing and route shells should use compact orientation copy and static
  links/sections. They must be useful enough to choose a next path, but they
  must stop before detailed platform commands, full matrices, or broad marketing
  content that belongs to later DOC specs.
- Accessibility scope is the static shell contract only: semantic headings,
  native links, visible focus preservation, descriptive link text, static
  fallback, non-color-only communication, and readable order. Automated
  accessibility tooling, responsive screenshot policy, and broad hardening stay
  with DOC-010.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: docs-site shell, Astro/Starlight config, route
  content shells
- **Projected reviewable LOC**: 395 to 405 excluding generated lock/vendor
  artifacts
- **Projected production files**: 0 plugin production files; docs-site
  source/config files only
- **Projected total files**: 6 expected source/control files before package
  manager generated artifacts
- **Budget result**: warning accepted
- **Split decision**: Keep one DOC-002 spec and workflow identity, but preserve
  two implementation slices: shell/routes first, then validation/config
  hardening.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback or
  feature-flag notes.
- Traceability MUST map landing, route shell, navigation, source-vs-payload,
  build/link validation, Pages-ready config, and non-goal requirements to
  changed files and verification evidence.
- Deferred work MUST name the follow-up DOC or issue, especially DOC-003,
  DOC-004, DOC-005, DOC-006, DOC-007, DOC-008, DOC-009, and DOC-010.

### Key Entities *(include if feature involves data)*

- **Documentation Site**: The Astro/Starlight app rooted at `docs-site/`, with
  package commands, Starlight configuration, landing page, and route pages.
- **Top-Level Route Shell**: A skeletal docs page with route label, path,
  Diataxis group, purpose, shell owner DOC, full content owner DOC, success
  criterion, and source evidence.
- **Navigation Group**: A Diataxis section in the Starlight sidebar: Tutorials,
  How-to, Reference, or Explanation.
- **Source Evidence Link**: A repository or research document reference used to
  justify a route shell's purpose and later content ownership.
- **Validation Command Role**: A docs-site-scoped command role for installing,
  building, previewing, or validating internal links.
- **Accessibility Shell Contract**: The static accessibility boundary that keeps
  platform choices, route shell orientation, source evidence, and future
  interactive-aid fallbacks perceivable, keyboard reachable, and useful without
  JavaScript-only behavior.
- **Reliability Completion Gate**: The repeatable local validation boundary for
  DOC-002 after `docs-site/` dependencies and lockfile are present.
- **Error Handling Disposition**: The documented outcome for a setup,
  validation, link, Pages, or framework-blocker failure, including whether the
  next action is local remediation, setup prerequisite repair, DOC-010 deferral,
  or framework fallback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The landing page states the marketplace purpose, current plugin,
  primary value, supported platforms, source-vs-payload distinction, and next
  actions within the first screen.
- **SC-002**: The Starlight navigation exposes Tutorials, How-to, Reference, and
  Explanation sections.
- **SC-003**: Claude Code and Codex paths are both reachable from the landing
  page's first interaction.
- **SC-004**: The landing page and Reference shell both distinguish
  `speckit-pro/` authoring source from generated install payloads under
  `dist/claude/**` and `dist/codex/**`.
- **SC-005**: All 11 top-level route shells exist and each displays purpose,
  owner DOC, success criterion, and source evidence.
- **SC-006**: A maintainer can run the documented docs-site production build and
  internal-link validation without relying on root plugin test commands.
- **SC-007**: Repository changes contain no GitHub Pages publish workflow and no
  plugin behavior, marketplace manifest, generated payload, hook, agent, release
  automation, or README content changes.
- **SC-008**: A reviewer can audit the first screen against the required landing
  content units and exclusions in FR-018 without interpreting "thin actionable"
  subjectively.
- **SC-009**: A reviewer can open any deferred route shell and identify its
  audience, useful-now shell content, deferred owner DOC, source evidence, and
  next step without encountering full later-DOC content.
- **SC-010**: A reviewer can inspect the landing page and any route shell and
  identify semantic headings, descriptive native links, visible focus-compatible
  controls or links, non-color-only status/callout meaning, and static fallback
  content for any future DOC-006 enhancement point.
- **SC-011**: After `docs-site/` dependencies are installed and `pnpm-lock.yaml`
  exists, a maintainer can rerun `pnpm check`, `pnpm build`, `pnpm validate`,
  and `pnpm validate:links` from `docs-site/` without deployment, browser
  screenshots, external-link crawling, remote URL availability checks, or
  additional package-network access.
- **SC-012**: A reviewer can inspect the quickstart, plan, and route-shell
  contract and identify the prescribed next action for missing `pnpm`, build
  failure, internal-link validation failure, Pages base/path mismatch, and true
  Astro/Starlight hard blocker without inferring from implementation logs.

## Assumptions

- DOC-001's Astro/Starlight recommendation remains valid unless Plan discovers
  a hard blocker for GitHub Pages hosting, MDX/component authoring, accessible
  static fallback, dependency policy, or maintainability.
- `docs-site/` is the only site app path for DOC-002.
- The install command role can be represented as docs-site-scoped `pnpm install`
  while build, preview, and link validation are represented by package scripts
  chosen during Plan.
- If `pnpm` is unavailable, setup is blocked until the maintainer enables or
  installs `pnpm`; DOC-002 should not switch to root `npm`/`yarn` commands or a
  repository-wide workspace to work around that prerequisite.
- `pnpm install` may require package-registry network access when dependencies or
  the lockfile are first created or refreshed; that install step is setup, not
  the repeatable DOC-002 minimum completion gate after dependencies are present.
- DOC-010 owns publish workflow creation, broader docs CI hardening, search
  hardening, accessibility checks, responsive screenshots, and validation policy
  beyond DOC-002's build plus internal-link checks and static accessibility
  shell contract.
- Later DOC specs own full platform install content, first-run walkthroughs,
  troubleshooting matrices, security/trust depth, contributor/release workflow,
  lifecycle explanations, glossary depth, and interactive aids.

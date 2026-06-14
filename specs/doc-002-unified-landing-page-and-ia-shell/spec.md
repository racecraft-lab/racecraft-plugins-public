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

### Reviewability Notes *(if applicable)*

- DOC-002 is docs-site and docs-process work. It must not modify plugin runtime
  behavior, marketplace manifests, generated install payloads, hooks, agents, or
  release automation.
- README files are source evidence only. Any README-derived claims should be
  linked or summarized in route shells without converting README content.
- Deferred route depth must name the owning follow-up DOC rather than expanding
  DOC-002 into full install, troubleshooting, security, contributor, lifecycle,
  glossary, search, accessibility, or deployment content.

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

## Assumptions

- DOC-001's Astro/Starlight recommendation remains valid unless Plan discovers
  a hard blocker for GitHub Pages hosting, MDX/component authoring, accessible
  static fallback, dependency policy, or maintainability.
- `docs-site/` is the only site app path for DOC-002.
- The install command role can be represented as docs-site-scoped `pnpm install`
  while build, preview, and link validation are represented by package scripts
  chosen during Plan.
- DOC-010 owns publish workflow creation, broader docs CI hardening, search
  hardening, accessibility checks, responsive screenshots, and validation policy
  beyond DOC-002's build plus internal-link checks.
- Later DOC specs own full platform install content, first-run walkthroughs,
  troubleshooting matrices, security/trust depth, contributor/release workflow,
  lifecycle explanations, glossary depth, and interactive aids.

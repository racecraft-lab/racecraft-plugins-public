# Feature Specification: Claude Code Marketplace Installation Path

**Feature Branch**: `doc-003-claude-code-marketplace-installation-path`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Claude Code users need a complete, source-backed path for adding the Racecraft marketplace, installing SpecKit Pro, reloading plugins, verifying the namespaced skill surface, updating, uninstalling, removing the marketplace when appropriate, and understanding the trust implications before running plugin skills."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install SpecKit Pro from the Racecraft marketplace (Priority: P1)

As a Claude Code user, I can add the Racecraft marketplace, install SpecKit Pro, and reload plugins using exact commands from the Claude install page.

**Why this priority**: Installation is the primary user value for this route; without a complete first-run path, the page remains a shell.

**Independent Test**: A reviewer can open the Claude install page and confirm that a new user has an ordered add, install, and reload path with expected evidence for each step.

**Acceptance Scenarios**:

1. **Given** a Claude Code user has not installed the Racecraft marketplace, **When** they read the install route, **Then** they see the exact commands needed to add the marketplace and install SpecKit Pro.
2. **Given** the marketplace or plugin list may be stale after install actions, **When** the user follows the route, **Then** the page tells them when and why to reload plugins before verification.
3. **Given** an evaluator wants to inspect before installing, **When** they review the install path, **Then** each trust-relevant install step is backed by the official Claude Code docs or the Racecraft repository source.

---

### User Story 2 - Verify the installed namespaced skill surface (Priority: P1)

As a Claude Code user, I can verify the install through `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach` without confusing current skill usage with deprecated command-folder wording.

**Why this priority**: Users need immediate proof that the plugin is available and that they are invoking the current namespaced skills correctly.

**Independent Test**: A reviewer can compare the verification section against the installed plugin surface and confirm that it names the expected commands, namespaces, and positive signals.

**Acceptance Scenarios**:

1. **Given** SpecKit Pro is installed, **When** the user follows the verification section, **Then** they can confirm plugin presence with `/plugin`.
2. **Given** SpecKit Pro is installed, **When** the user invokes `/speckit-pro:speckit-status` and `/speckit-pro:speckit-coach`, **Then** the page explains what successful availability looks like.
3. **Given** a user expects older command-folder behavior, **When** they read the verification guidance, **Then** the docs direct them to current namespaced skill usage instead.

---

### User Story 3 - Manage plugin lifecycle without guessing commands (Priority: P2)

As a Claude Code user, I can update, uninstall, remove the marketplace when appropriate, and reinstall the plugin from one lifecycle section.

**Why this priority**: Lifecycle commands prevent one-time install docs from becoming a support burden after plugin updates or failed local experiments.

**Independent Test**: A reviewer can validate that the lifecycle section covers update, uninstall, marketplace removal, and reinstall with clear decision points.

**Acceptance Scenarios**:

1. **Given** an installed SpecKit Pro plugin may be outdated, **When** the user reads lifecycle guidance, **Then** they see the update path and expected post-update verification.
2. **Given** a user wants to stop using SpecKit Pro but may keep other Racecraft plugins later, **When** they read uninstall guidance, **Then** the page distinguishes plugin uninstall from marketplace removal.
3. **Given** a user needs a clean reinstall, **When** they read lifecycle guidance, **Then** they see the safe reinstall sequence without needing a separate troubleshooting matrix.

---

### User Story 4 - Inspect trust surfaces before running plugin skills (Priority: P2)

As an evaluator, I can see which marketplace metadata, plugin manifest, skills, agents, hooks, MCP/settings surfaces, and generated payload files affect trust before installing or running SpecKit Pro skills.

**Why this priority**: Marketplace installation carries trust implications; evaluators need a concise source-backed inventory before enabling plugin behavior.

**Independent Test**: A reviewer can use the page to identify the relevant trust surfaces and trace them back to repository-controlled source or generated payload files.

**Acceptance Scenarios**:

1. **Given** an evaluator wants to inspect plugin behavior before install, **When** they read the trust section, **Then** they can identify the marketplace metadata, plugin manifest, skills, agents, hooks, and MCP/settings surfaces that matter for review.
2. **Given** generated Claude install payloads exist separately from authoring source, **When** the evaluator reads the trust section, **Then** the docs clearly label which paths are source and which paths are generated payloads.
3. **Given** official Claude Code platform behavior may change, **When** platform behavior is described, **Then** the page cites or links to official Claude Code documentation rather than treating repository assumptions as platform authority.

---

### User Story 5 - Maintain source and generated payload clarity (Priority: P3)

As a maintainer, I can update install-relevant wording across the docs without leaving command-vs-skill confusion or implying runtime changes.

**Why this priority**: The install page must stay aligned with repository terminology and generated payloads while preserving a documentation-only scope.

**Independent Test**: A reviewer can inspect the canonical page and install-relevant README/AGENTS wording and find no contradictions about current skill-based usage.

**Acceptance Scenarios**:

1. **Given** install-relevant README or AGENTS wording references outdated command-folder usage, **When** this feature is complete, **Then** that wording is updated or clarified without unrelated maintainer rewrites.
2. **Given** a maintainer needs to trace install docs to repository sources, **When** they read the page, **Then** source paths and generated payload paths are both visible and not conflated.

### Edge Cases

- The user already added the Racecraft marketplace before reading the new page and only needs install, reload, or verification guidance.
- The user added the wrong marketplace source, has a stale Racecraft marketplace listing, or sees the marketplace but not the `speckit-pro` plugin.
- The plugin appears installed but namespaced skills are not visible until the user reloads or refreshes the plugin surface.
- A verification, update, uninstall, marketplace removal, or reinstall step fails or produces an inconclusive result.
- A user is on the Codex install path or sees Codex-specific plugin, custom-agent, cache, sandbox, or approval failures while reading the Claude route.
- An evaluator wants to inspect trust surfaces before installing anything locally.
- A user wants to uninstall SpecKit Pro while keeping the Racecraft marketplace available for future plugins.
- Official Claude Code lifecycle commands or marketplace behavior differ from older local assumptions.
- Generated payload filenames or paths differ from authoring source paths and must be labeled clearly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The canonical Claude Code install route MUST live at `docs-site/src/content/docs/install/claude-code.md`.
- **FR-002**: The Claude Code install route MUST provide an ordered path for adding the Racecraft marketplace, installing SpecKit Pro, reloading plugins, and verifying the result.
- **FR-003**: The install path MUST include exact user-facing commands for each install and lifecycle action it asks users to perform.
- **FR-004**: The verification guidance MUST include `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach` as the primary installed-surface checks.
- **FR-005**: The page MUST explain expected successful verification signals in plain language so users can tell whether the install worked.
- **FR-006**: The lifecycle guidance MUST cover update, uninstall, marketplace removal when appropriate, and reinstall without requiring users to infer command order.
- **FR-007**: The lifecycle guidance MUST distinguish uninstalling SpecKit Pro from removing the Racecraft marketplace.
- **FR-008**: The trust guidance MUST identify install-relevant marketplace metadata, plugin manifest metadata, skills, agents, hooks, MCP/settings surfaces, and generated Claude payload files that evaluators should inspect before running plugin skills. The Claude route MUST use progressive disclosure for this trust content: keep the add, install, reload, and `/plugin` visibility check in one uninterrupted first-time path; place a concise pre-skill trust note with a jump link before the `/speckit-pro:speckit-status` and `/speckit-pro:speckit-coach` checks; and place the deeper source-backed trust inventory after the primary install and verification flow.
- **FR-009**: The docs MUST distinguish authoring source paths from generated Claude install payload paths wherever both are mentioned.
- **FR-010**: Platform behavior claims MUST be backed by official Claude Code documentation, while plugin-specific path and surface claims MUST be backed by repository manifests or generated payloads.
- **FR-011**: Install-relevant README and AGENTS wording MUST be updated broadly enough to remove command-vs-skill confusion, while avoiding unrelated repository-maintainer rewrites.
- **FR-012**: The Claude route MUST include only a cross-link to the Codex install route at `/install/codex/` and MUST NOT add Codex install instructions.
- **FR-013**: The feature MUST NOT change plugin runtime behavior, regenerate generated payloads, bump versions, or alter release automation.
- **FR-014**: The documentation update MUST be validatable with `pnpm --dir docs-site validate`.
- **FR-015**: The Claude route MUST use accessibility-friendly Markdown structure: descriptive hierarchical headings for deep links and screen-reader navigation, ordered or unordered lists for step sequences, fenced code blocks for commands, and literal command names in inline code when referenced in prose.
- **FR-016**: User-facing install, verification, and lifecycle commands MUST appear as standalone copyable command examples, not as commands hidden inside dense tables.
- **FR-017**: Link text on the Claude route MUST identify the destination or source path without relying on ambiguous surrounding prose such as "here", "this page", or "read more".
- **FR-018**: The Claude route MUST NOT use side-by-side or overloaded comparison tables that mix Claude and Codex command forms; Codex remains a single descriptive cross-link to `/install/codex/`.
- **FR-019**: The Claude route MUST NOT claim that Claude Code plugins, hooks, generated payloads, marketplace installation, or marketplace-managed installs provide sandboxing, isolation, harmlessness, or blocking guarantees unless the claim is directly supported by official Claude Code documentation cited on the page.
- **FR-020**: Hook behavior guidance MUST stay limited to documented Claude Code hook surfaces and the repository hook files being cited; it MUST NOT infer undocumented execution timing, safety, isolation, or blocking behavior from repository-specific assumptions.
- **FR-021**: Managed marketplace guidance MUST stay bounded to official Claude Code settings behavior, source inspection, add/update/remove implications, and user/project/local/managed scope distinctions; full rollback, incident response, policy design, and troubleshooting matrices are deferred to DOC-008.
- **FR-022**: The Claude route MUST include concise basic recovery guidance for wrong marketplace source, stale marketplace listing, missing `speckit-pro` plugin, failed `/plugin` visibility, missing namespaced skills after reload, failed update, failed uninstall, failed marketplace removal, and failed reinstall. The recovery guidance MUST use official Claude Code lifecycle surfaces only, such as marketplace list/update/remove, plugin install/uninstall, `/reload-plugins`, `/plugin` installed/error views, and exact SpecKit Pro names from repository-controlled sources.
- **FR-023**: Each DOC-003 recovery path MUST define a stopping point: after the documented basic check or one clean retry does not restore the expected Claude install surface, or when the issue appears to involve managed policy, permissions, network access, cache clearing, rollback, incident response, or undocumented platform behavior, the page MUST route to the troubleshooting route owned by DOC-008 rather than expanding DOC-003 into a troubleshooting matrix.
- **FR-024**: Codex-specific install, verification, custom-agent, cache, sandbox, approval, or plugin-runtime failures MUST be routed to the Codex install route at `/install/codex/` or DOC-008 troubleshooting, and the Claude route MUST NOT include Codex recovery commands beyond that routing note.

### Reviewability Notes *(if applicable)*

- This is a docs/process feature. Runtime plugin behavior, generated payload regeneration, release automation, and production application code are outside the review surface.
- Typed reviewability exceptions are not expected for this work.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: Install-relevant README/AGENTS wording only
- **Projected reviewable LOC**: 250-600 documentation lines
- **Projected production files**: 0
- **Projected total files**: 3-6
- **Budget result**: within budget
- **Split decision**: One spec is appropriate because the work is one Claude Code install route plus tightly scoped supporting wording; full troubleshooting, rollback procedures, runtime changes, and side-by-side Claude/Codex comparisons are deferred or out of scope.

### Declared File Operations

- MUST modify `docs-site/src/content/docs/install/claude-code.md`.
- MAY modify install-relevant README or AGENTS wording needed to remove command-vs-skill confusion.
- MAY update feature workflow metadata or PR packet documentation required by the SpecKit process.
- MUST NOT modify production runtime files.
- MUST NOT regenerate generated Claude payloads.
- MUST NOT change plugin versions, marketplace release automation, or generated release artifacts.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Claude Install Route**: The canonical documentation page that guides Claude Code users through SpecKit Pro marketplace installation and lifecycle management.
- **Lifecycle Command Set**: The set of user-facing install, reload, verify, update, uninstall, marketplace removal, and reinstall commands documented for Claude Code users.
- **Trust Surface Inventory**: The source-backed list of marketplace metadata, plugin manifest metadata, skills, agents, hooks, MCP/settings surfaces, and generated payload files that evaluators inspect before running plugin skills.
- **Source and Generated Path Map**: The documentation distinction between repository authoring source and generated Claude install payloads.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time Claude Code user can complete the add, install, reload, and verification path from the canonical page in under 10 minutes without maintainer assistance.
- **SC-002**: 100% of install, verification, and lifecycle commands shown on the Claude route have clear backing from official Claude Code docs or repository-controlled plugin sources.
- **SC-003**: An evaluator can identify the documented marketplace metadata, plugin manifest metadata, skills, agents, hooks, MCP/settings surfaces, and generated payload files that affect trust in under 5 minutes from the canonical page.
- **SC-004**: Review of the canonical page and install-relevant README/AGENTS wording finds zero unresolved command-vs-skill terminology contradictions.
- **SC-005**: The docs-site validation command `pnpm --dir docs-site validate` completes successfully for this change.
- **SC-006**: The final implementation changes 0 production runtime files and does not regenerate payloads, bump versions, or alter release automation.
- **SC-007**: A reviewer can inspect the Claude route and find descriptive headings, list-based step structure, standalone copyable command blocks, meaningful link text, and no mixed Claude/Codex command comparison table.
- **SC-008**: A reviewer can find concise recovery guidance for wrong marketplace, missing plugin, failed verification, update, uninstall, marketplace removal, and reinstall cases, with each case either ending in a source-backed basic action or routing to DOC-008 troubleshooting.

## Assumptions

- Claude Code is the primary install surface for this feature; Codex coverage is limited to a cross-link to `/install/codex/`.
- Official Claude Code documentation remains the authority for marketplace and plugin lifecycle platform behavior.
- Repository manifests, authoring files, and existing generated payloads are sufficient authority for SpecKit Pro path and trust-surface claims.
- The implementation will keep troubleshooting concise and defer a full troubleshooting matrix or rollback guide to future work if needed.
- Users and evaluators can access the public Racecraft marketplace repository and the docs site.
- Screen-reader or keyboard users may navigate by headings, lists, links, and code blocks rather than reading the page linearly; ambiguous link text, dense command tables, or mixed Claude/Codex command comparisons would make the install path harder to follow.
- Official documentation links, repository source paths, and generated payload paths must remain distinguishable when read as standalone link text or inline code.
- Security and trust wording must distinguish "inspectable source-backed surfaces" from platform guarantees; the DOC-003 page must avoid unsupported claims about sandboxing, hook isolation, or managed marketplace safety.
- Basic recovery belongs in DOC-003 only when it keeps a Claude install, update, remove, or reinstall user from getting stuck on the primary path; detailed symptom diagnosis, cache cleanup, rollback, incident response, and cross-platform troubleshooting remain DOC-008 scope.

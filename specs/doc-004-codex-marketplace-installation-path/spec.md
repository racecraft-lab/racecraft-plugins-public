# Feature Specification: Codex marketplace installation path

**Feature Branch**: `doc-004-codex-marketplace-installation-path`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Codex users need a precise, source-backed install path for Racecraft Public Plugins and `speckit-pro`."

## Source Review Baseline

- Official Codex plugin docs refreshed on 2026-06-14:
  - `https://developers.openai.com/codex/plugins`
  - `https://developers.openai.com/codex/plugins/build`
  - `https://developers.openai.com/codex/skills`
  - `https://developers.openai.com/codex/subagents`
  - `https://developers.openai.com/codex/permissions`
  - `https://developers.openai.com/codex/agent-approvals-security`
- Local Codex CLI help refreshed on 2026-06-14 for `codex plugin marketplace add --help`.
- Documentation authored from this spec MUST treat official Codex docs as the source of truth for marketplace, plugin, skills, custom-agent, sandbox, approval, and network wording. Local CLI help may be used only to confirm command syntax when official docs do not yet spell out a subcommand.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose the correct install path (Priority: P1)

As a Codex user, I can choose between repo-scoped marketplace, personal marketplace, and local plugin installation paths without confusing authoring source, generated payload, and installed cache.

**Why this priority**: Users must understand which directory Codex reads before they can safely install or repair `speckit-pro`.

**Independent Test**: Review the three install entry points and confirm a new Codex user can identify the correct path for repo-scoped, personal, and local setups without reading unrelated docs.

**Acceptance Scenarios**:

1. **Given** a user wants repo-scoped installation, **When** they read the Codex install guidance, **Then** they see `.agents/plugins/marketplace.json` described as the repo marketplace source and distinct from plugin manifests and installed cache paths.
2. **Given** a user wants personal or local installation, **When** they read the Codex install guidance, **Then** they see that the local plugin root is the generated Codex payload at `dist/codex/speckit-pro/`, not the mixed authoring source tree at `speckit-pro/`.
3. **Given** a user sees `~/.codex/plugins/cache/...`, **When** they compare it to marketplace and source paths, **Then** they understand it is Codex's installed copy and should not be edited as the source of truth.

---

### User Story 2 - Install and verify custom agents (Priority: P1)

As a Codex user, I can install `speckit-pro`, run the Codex install skill, restart Codex, and verify the expected custom-agent TOML files are registered.

**Why this priority**: `speckit-pro` skills are available through the plugin, but custom agents require an additional Codex registration step.

**Independent Test**: Follow only the Codex install page and confirm the plugin is installed, `$install` or `@SpecKit Pro -> install` is run, the expected TOML files are copied, and Codex is restarted.

**Acceptance Scenarios**:

1. **Given** `speckit-pro` is installed as a Codex plugin, **When** the user invokes the install workflow, **Then** the docs explain `@SpecKit Pro -> install` and `$install` as the Codex-only custom-agent registration step.
2. **Given** a user asks why custom agents are not available immediately, **When** they read the docs, **Then** they see that plugin-bundled skills are available from the installed plugin while custom agents must be copied into `.codex/agents/` or `~/.codex/agents/`.
3. **Given** a user verifies the result, **When** they inspect the target custom-agent directory, **Then** the docs list the current bundled TOML files from `speckit-pro/codex-agents/`, including `uat-runbook-author.toml` if it remains present in source.

---

### User Story 3 - Keep install guidance consistent (Priority: P2)

As a maintainer, I can keep the root README, plugin README, and docs-site Codex page consistent after official-source validation.

**Why this priority**: Contradictory entry points create install failures and support churn.

**Independent Test**: Compare `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` and confirm they agree on Codex marketplace surfaces, generated payload target, install skill, restart, and verification language.

**Acceptance Scenarios**:

1. **Given** a maintainer updates Codex install guidance, **When** they compare all three entry points, **Then** the command wording, paths, and safety caveats do not contradict each other.
2. **Given** deeper troubleshooting or security topics exceed this feature, **When** a maintainer reviews the docs, **Then** the content preserves cross-links to DOC-007 and DOC-008 ownership without expanding into those topics.

---

### User Story 4 - Evaluate install safety (Priority: P2)

As a security-minded user, I can see the bounded sandbox, approvals, network, cache, and trust implications needed before first install.

**Why this priority**: Installing a plugin changes what Codex can load, and users need enough safety context before approving marketplace, cache, and agent-registration steps.

**Independent Test**: Review the Codex install page and confirm it explains sandbox and approval boundaries without implying full troubleshooting or security-reference coverage.

**Acceptance Scenarios**:

1. **Given** a user runs Codex with workspace-write permissions, **When** they read install guidance, **Then** they understand Codex can edit workspace files while approvals still gate outside-workspace writes or network access according to the user's configured policy.
2. **Given** a plugin install or custom-agent registration requires local writes or network access, **When** a prompt appears, **Then** the docs explain what the user is approving and how to reject or rerun with narrower permissions.

---

### Edge Cases

- Official Codex docs do not document a CLI subcommand that local Codex help exposes.
- A user points a personal marketplace or local plugin source at `speckit-pro/` instead of `dist/codex/speckit-pro/`.
- A user edits the installed cache and loses changes after reinstall or update.
- A user installs the plugin but skips `$install`, so skills work but custom agents are unavailable.
- A user copies only some TOML files and misses `uat-runbook-author.toml` while it remains in source.
- A user does not restart Codex after changing plugin or custom-agent state.
- A user runs with network disabled and tries to install from a Git-backed marketplace.
- Existing Claude Code install guidance appears near Codex guidance and creates cross-agent confusion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Documentation MUST update `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` so the three Codex entry points agree on install paths, cache behavior, custom-agent registration, restart, and verification.
- **FR-002**: Documentation MUST distinguish `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, and `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` as separate surfaces with separate roles.
- **FR-003**: Documentation MUST describe repo-scoped marketplace installation separately from personal marketplace and local plugin layout installation.
- **FR-004**: Documentation MUST state that personal or local plugin installs should target `dist/codex/speckit-pro/` rather than the mixed authoring source tree at `speckit-pro/`.
- **FR-005**: Documentation MUST explain that Codex loads an installed local plugin from its cache copy, not directly from the marketplace source directory.
- **FR-006**: Documentation MUST include `codex plugin marketplace add` guidance only after refreshing official Codex docs and local Codex CLI help for current marketplace source semantics.
- **FR-007**: Documentation MUST describe supported marketplace source forms only when source-backed: local marketplace path, `owner/repo[@ref]`, HTTPS Git URL, SSH Git URL, `--ref`, and repeatable `--sparse` paths.
- **FR-008**: Documentation MUST show the Codex plugin browser path through `codex` then `/plugins` as a supported install flow for marketplace entries.
- **FR-009**: Documentation MUST explain `@SpecKit Pro -> install` and `$install` as the Codex-only custom-agent registration step after plugin installation.
- **FR-010**: Documentation MUST explain why bundled skills are available from the plugin while custom agents require TOML files copied into `.codex/agents/` or `~/.codex/agents/`.
- **FR-011**: Documentation MUST list every current TOML custom-agent file bundled under `speckit-pro/codex-agents/`; the expected source list at specification time is `analyze-executor.toml`, `autopilot-fast-helper.toml`, `checklist-executor.toml`, `clarify-executor.toml`, `codebase-analyst.toml`, `domain-researcher.toml`, `implement-executor.toml`, `phase-executor.toml`, `spec-context-analyst.toml`, and `uat-runbook-author.toml`.
- **FR-012**: Documentation MUST tell users to restart Codex after plugin enablement changes, custom-agent installation, or manual `~/.codex/config.toml` edits that affect plugin or skill state.
- **FR-013**: Documentation MUST include bounded install-safety guidance covering sandbox mode, approval prompts, network access, installed cache trust, and external app or MCP authentication implications.
- **FR-014**: Documentation MUST preserve cross-links to DOC-007 and DOC-008 for future reference-depth and troubleshooting/security-depth work.
- **FR-015**: Documentation MUST keep Claude Code installation instructions out of DOC-004 content except for an explicit cross-link to the DOC-003-owned path.
- **FR-016**: Implementation MUST remain documentation-only unless the plan records and justifies a narrow source correction for a docs contradiction.
- **FR-017**: PR readiness MUST include `cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, and `bash tests/speckit-pro/run-all.sh`.

### Declared File Operations

- **Modify**: `README.md`
- **Modify**: `speckit-pro/README.md`
- **Modify**: `docs-site/src/content/docs/install/codex.md`
- **Modify**: `specs/doc-004-codex-marketplace-installation-path/spec.md`
- **Create or modify**: `specs/doc-004-codex-marketplace-installation-path/checklists/requirements.md`
- **Do not modify**: `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, `speckit-pro/codex-agents/*.toml`, install scripts, generated payload behavior, release automation, or runtime code.

### Reviewability Notes *(if applicable)*

- This is a docs/process feature. No typed reviewability exception is expected.
- Any proposed non-docs change must be called out in the plan as a narrow source correction, with a reason the docs cannot be made accurate without it.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 250-500 documentation LOC excluding generated lock or vendor artifacts
- **Projected production files**: 3 documentation entry points
- **Projected total files**: 4-6 including SpecKit artifacts and any docs-site metadata touched only if required
- **Budget result**: within budget
- **Split decision**: This remains one spec because the scope is a bounded Codex installation path alignment. Full troubleshooting, update/rollback, and trust/security reference depth remain deferred to DOC-007 and DOC-008.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name DOC-007 or DOC-008 where deeper reference, troubleshooting, update/rollback, or security topics are intentionally out of scope.

### Key Entities *(include if feature involves data)*

- **Marketplace Source**: A catalog location Codex can read to discover installable plugin entries, including repo, legacy-compatible, and personal marketplace files.
- **Codex Plugin Payload**: The installable plugin root containing `.codex-plugin/plugin.json` plus bundled skills, hooks, assets, and optional app or MCP configuration.
- **Installed Plugin Cache**: The copy Codex installs under `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` and loads at runtime.
- **Custom Agent Registration**: The Codex-only step that copies bundled TOML files into project-scoped or user-scoped Codex agent locations.
- **Documentation Entry Point**: A user-facing page or README section that must agree with the other entry points on paths, commands, and safety guidance.
- **Install Safety Posture**: The combination of sandbox mode, approval policy, network access, local cache trust, and external authentication expectations presented before install.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three documentation entry points describe the same Codex install sequence and contain zero contradictory path or command statements.
- **SC-002**: A first-time Codex user can choose repo-scoped, personal, or local installation from the docs in under 5 minutes without consulting source files outside the install guidance.
- **SC-003**: A user can verify custom-agent registration from the docs by checking the expected TOML filenames with no missing current source files.
- **SC-004**: Security-minded readers encounter sandbox, approval, network, cache, and trust guidance before any step that could install or register plugin components.
- **SC-005**: PR readiness validation completes with docs-site validation, docs-site link validation, and the default `speckit-pro` shell test suite passing.

## Assumptions

- The target feature directory already exists at `specs/doc-004-codex-marketplace-installation-path/`; this specification does not create a new branch or feature directory.
- Official Codex docs refreshed on 2026-06-14 are sufficient for the specify phase, and implementation will refresh them again if command wording changes before docs edits land.
- `codex plugin marketplace add --help` is acceptable as a local Codex CLI source for subcommand syntax when official docs confirm marketplace concepts but do not spell out the subcommand.
- The current `speckit-pro/codex-agents/` TOML list remains source of truth at implementation time; docs must reflect any file added or removed before the docs edit.
- DOC-004 covers bounded install guidance only. DOC-007 and DOC-008 own deeper reference, troubleshooting, update/rollback, and security/trust coverage.

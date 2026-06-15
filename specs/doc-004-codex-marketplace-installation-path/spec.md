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
- Documentation authored from this spec MUST treat official Codex docs as the source of truth for marketplace, plugin, skills, custom-agent, lifecycle hook, sandbox, approval, and network wording. Local CLI help may be used only to confirm command syntax when official docs do not yet spell out a subcommand.

## Clarifications

### Session 1 - Official Codex path semantics

- Q: Which exact `codex plugin marketplace add` source forms should DOC-004 document?
  A: Document local marketplace root directories, GitHub shorthand `owner/repo` and `owner/repo@ref`, HTTP or HTTPS Git URLs, SSH Git URLs, `--ref`, repeatable `--sparse PATH` for Git marketplace sources only, and `--json` output for automation. Do not document unsupported source forms.
- Q: How should repo-scoped marketplace behavior be described for this repo?
  A: `$REPO_ROOT/.agents/plugins/marketplace.json` is the repo marketplace source. Its `source.path` for `speckit-pro` resolves to `./dist/codex/speckit-pro` from the marketplace root and must remain distinct from plugin manifests, authoring source, and installed plugin cache paths.
- Q: For personal/local installs, should docs say to point directly at `dist/codex/speckit-pro/` or copy/sync that generated payload into a personal plugin location?
  A: The installable unit is the generated Codex payload, not the authoring source tree. Repo-scoped examples may point marketplace `source.path` directly at `./dist/codex/speckit-pro`. Personal/local examples may copy or sync that generated payload into the official personal plugin layout, then point the personal marketplace `source.path` at the copied payload. In all cases, docs must not point Codex at `speckit-pro/`, and copied payloads must be refreshed before users expect source changes to appear.
- Q: What installed-cache terminology should DOC-004 use?
  A: Use `installed plugin cache` and the official path pattern `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`. For local plugins, `$VERSION` is `local`. DOC-004 user-facing docs should not teach stale internal install-skill terms such as `marketplace tmp root` or `active plugin install` unless explicitly explaining a bounded version-specific mismatch.
- Q: How should docs distinguish bundled skills from custom agents?
  A: Use official terms: plugin bundle or payload, bundled skills, and custom agents as TOML files under `.codex/agents/` or `~/.codex/agents/`. Skill metadata sidecars such as `agents/openai.yaml` are not custom-agent registration.

### Session 2 - Custom-agent registration and verification

- Q: Should DOC-004 list expected custom-agent files from `speckit-pro/codex-agents/` or from the installer's copied set?
  A: For user-facing verification, list the files the Codex install skill actually verifies and copies. The raw `speckit-pro/codex-agents/` directory is source/package evidence, not the expected installed output when it differs from the installer. At specification time, the installer-copied set is `autopilot-fast-helper.toml`, `phase-executor.toml`, `clarify-executor.toml`, `checklist-executor.toml`, `analyze-executor.toml`, `implement-executor.toml`, `codebase-analyst.toml`, `spec-context-analyst.toml`, and `domain-researcher.toml`. `uat-runbook-author.toml` is present in the source directory but must not be listed as an expected installed file unless the plan records and approves a narrow source correction that changes the installer copied set.
- Q: Which destination-path wording should the docs use for `$install`?
  A: The install skill defaults to user-scope `~/.codex/agents/`. Project-scoped `.codex/agents/` is an explicit destination override, not the default, and should be presented when users intentionally want repo-local agent registration.
- Q: How should docs explain plugin-shipped skills versus copied TOML custom agents?
  A: Use a three-surface model: bundled skills loaded from the installed plugin payload, optional `agents/openai.yaml` skill metadata sidecars for skill UI/invocation/tool policy, and TOML custom agents that must be copied into `.codex/agents/` or `~/.codex/agents/` by the install skill. Plugin installation does not automatically register custom agents.
- Q: What verification is safe to document without changing installer behavior?
  A: Document observational verification only: review the installer report, destination directory, copied filenames, model line, restart instruction, and preservation of unrelated user agents. Do not add a new doctor/list command, do not tell users to edit the installed cache or TOML files manually, and do not imply installer behavior changes.
- Q: How should docs describe permission and approval implications for `$install` writing outside the workspace?
  A: Treat this as bounded install-safety guidance, not a full security reference. DOC-004 docs MUST state that `$install` copies bundled SpecKit Pro TOML custom-agent files into the selected Codex agent directory, such as `.codex/agents/` or `~/.codex/agents/`. If that destination is outside the current workspace, Codex may require approval according to the user's sandbox and approval policy. The docs MUST tell users to approve only the expected local write of the named SpecKit Pro TOML files to the selected destination, or reject the prompt and rerun with a project-scoped destination or narrower permissions. Git-backed marketplace setup or plugin installation may require network access or network approval, but the `$install` custom-agent registration step itself is local filesystem work from the installed plugin bundle. Deeper permission policy, rollback, managed-policy, and trust-analysis details remain deferred to DOC-008.

### Session 3 - Scope, consistency, and validation

- Q: What consistency rule should bind `README.md`, `speckit-pro/README.md`, and the docs-site Codex page?
  A: All three entry points must share the critical Codex install invariants: marketplace surfaces, generated payload target, installed plugin cache behavior, `$install`, restart, verification, and bounded safety. The docs-site Codex page remains the detailed install path; READMEs may stay concise if they do not contradict the docs-site.
- Q: How should DOC-004 bound trust, sandbox, approval, network, cache, and permission guidance versus DOC-008?
  A: DOC-004 MUST include a short install-safety block only. That block MUST explain that Codex sandbox mode and approval policy may gate outside-workspace writes, network access, and other sensitive actions; that Git-backed marketplace setup or plugin installation may require network access or approval; that `$install` is local filesystem work that copies the named SpecKit Pro TOML custom-agent files from the installed plugin bundle into the selected `.codex/agents/` or `~/.codex/agents/` destination; that SpecKit Pro's generated Codex payload may also include lifecycle hook configuration such as `codex-hooks.json` referenced by the plugin manifest; that users should approve only the expected local write to the selected destination, or reject and rerun with a project-scoped destination or narrower permissions; and that the installed plugin cache is a runtime copy, not the source of truth. DOC-004 MUST link or defer to DOC-008 for full marketplace trust analysis, managed-policy guidance, hook/MCP/agent security depth, stale-cache diagnosis, permission troubleshooting, update/remove/rollback procedures, and the broader security/trust model. DOC-004 MUST NOT imply that plugin install, bundled hooks, or `$install` bypass Codex sandbox/approval controls or grant silent autonomous access.
- Q: What plugin behavior changes are forbidden in DOC-004?
  A: DOC-004 implementation is documentation/spec artifacts only. It must not change manifests, generated payloads, installer behavior, TOML templates, hooks, marketplace behavior, release automation, or runtime behavior. If a real docs contradiction requires a behavior or source correction, the plan must record it as a narrow exception and stop for explicit approval before implementation.
- Q: What exact validation command set should define PR readiness?
  A: Use the existing full verification set: `cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, and `bash tests/speckit-pro/run-all.sh`. Treat `pnpm validate:links` as the current DOC-002 link-validation hook even if it presently aliases a production build. DOC-004 must not change docs-site validation scripts.
- Q: What should manual command-snippet review prove?
  A: The implementation evidence must include a source-backed snippet checklist mapping every Codex command and path snippet to official OpenAI docs, local Codex CLI help, or checked-in source. The checklist must cover `codex` plus `/plugins`, `codex plugin marketplace add`, marketplace source forms, `dist/codex/speckit-pro/`, installed plugin cache path, `$install` and `@SpecKit Pro -> install`, agent destination paths, restart guidance, and expected TOML filenames.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose the correct install path (Priority: P1)

As a Codex user, I can choose between repo-scoped marketplace, personal marketplace, and local plugin installation paths without confusing authoring source, generated payload, and installed plugin cache.

**Why this priority**: Users must understand which directory Codex reads before they can safely install or repair `speckit-pro`.

**Independent Test**: Review the three install entry points and confirm a new Codex user can identify the correct path for repo-scoped, personal, and local setups without reading unrelated docs.

**Acceptance Scenarios**:

1. **Given** a user wants repo-scoped installation, **When** they read the Codex install guidance, **Then** they see `.agents/plugins/marketplace.json` described as the repo marketplace source and distinct from plugin manifests and installed plugin cache paths.
2. **Given** a user wants personal or local installation, **When** they read the Codex install guidance, **Then** they see that `dist/codex/speckit-pro/` is the generated Codex plugin payload to copy or sync into the marketplace plugin directory, such as `~/.codex/plugins/speckit-pro/` for a personal marketplace, and that they must not install from the mixed authoring source tree at `speckit-pro/`.
3. **Given** a user sees `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`, **When** they compare it to marketplace and source paths, **Then** they understand it is Codex's installed plugin cache copy, should not be edited as the source of truth, and should be refreshed by updating the marketplace source or generated payload and reinstalling or refreshing the plugin.

---

### User Story 2 - Install and verify custom agents (Priority: P1)

As a Codex user, I can install `speckit-pro`, run the Codex install skill, restart Codex, and verify the expected custom-agent TOML files are registered.

**Why this priority**: `speckit-pro` skills are available through the plugin, but custom agents require an additional Codex registration step.

**Independent Test**: Follow only the Codex install page and confirm the plugin is installed, `$install` or `@SpecKit Pro -> install` is run, the expected TOML files are copied, and Codex is restarted.

**Acceptance Scenarios**:

1. **Given** `speckit-pro` is installed as a Codex plugin, **When** the user invokes the install workflow, **Then** the docs explain `@SpecKit Pro -> install` and `$install` as the Codex-only custom-agent registration step.
2. **Given** a user asks why custom agents are not available immediately, **When** they read the docs, **Then** they see that plugin-bundled skills are available from the installed plugin while custom agents must be copied into `.codex/agents/` or `~/.codex/agents/`.
3. **Given** a user verifies the result, **When** they inspect the target custom-agent directory, **Then** the docs list the TOML files the current install skill copies and reports, and do not list source-only TOML files as expected installed output.

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
- A user points a personal marketplace or local plugin source at `speckit-pro/` instead of a copy or sync of `dist/codex/speckit-pro/`.
- A user edits the installed plugin cache and loses changes after reinstall or update.
- A user updates or refreshes the plugin but still sees old skill copy, old plugin metadata, unchanged custom-agent behavior, or a copied personal payload that has not been refreshed.
- A user installs the plugin but skips `$install`, so skills work but custom agents are unavailable.
- A plugin update changes bundled custom-agent TOML files, but the user restarts without rerunning `$install`, so old registered agents remain in the selected Codex agent directory.
- A user compares raw `speckit-pro/codex-agents/` source contents with installer output and sees source/package drift.
- A user does not restart Codex after changing plugin or custom-agent state.
- A user runs with network disabled and tries to install from a Git-backed marketplace.
- Existing Claude Code install guidance appears near Codex guidance and creates cross-agent confusion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Documentation MUST update `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` so the three Codex entry points agree on install paths, installed plugin cache behavior, custom-agent registration, restart, verification, and bounded install-safety guidance. The docs-site Codex page MAY contain the full detail while the README surfaces stay concise.
- **FR-002**: Documentation MUST distinguish `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, and `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` as separate surfaces with separate roles.
- **FR-003**: Documentation MUST describe repo-scoped marketplace installation separately from personal marketplace and local plugin layout installation.
- **FR-004**: Documentation MUST state that personal or local plugin installs use the generated Codex payload, not the mixed authoring source tree: repo-scoped examples MAY point `source.path` directly at `./dist/codex/speckit-pro`, while personal marketplace examples MAY copy or sync `dist/codex/speckit-pro/` into the official personal plugin layout and MUST point the personal marketplace `source.path` at that copied payload. Documentation MUST NOT direct users to install from `speckit-pro/`.
- **FR-005**: Documentation MUST explain that Codex loads an installed plugin from the installed plugin cache at `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`, not directly from the marketplace source directory or generated payload directory. Documentation MUST tell users to update the marketplace source or generated payload, then reinstall or refresh, rather than editing the installed plugin cache.
- **FR-006**: Documentation MUST include `codex plugin marketplace add` guidance only after refreshing official Codex docs and local Codex CLI help for current marketplace source semantics.
- **FR-007**: Documentation MUST describe supported marketplace source forms only when source-backed: local marketplace root directories, GitHub shorthand `owner/repo` and `owner/repo@ref`, HTTP or HTTPS Git URLs, SSH Git URLs, `--ref`, repeatable `--sparse PATH` for Git marketplace sources only, and `--json` output for automation.
- **FR-008**: Documentation MUST show the Codex plugin browser path through `codex` then `/plugins` as a supported install flow for marketplace entries.
- **FR-009**: Documentation MUST explain `@SpecKit Pro -> install` and `$install` as the Codex-only custom-agent registration step after plugin installation.
- **FR-010**: Documentation MUST explain why bundled skills are available from the plugin while custom agents require TOML files copied into `.codex/agents/` or `~/.codex/agents/`; it MUST distinguish skill metadata sidecars such as `agents/openai.yaml` from registered custom-agent TOML files.
- **FR-011**: Documentation MUST list the Codex custom-agent TOML files that the current install skill verifies and copies into `.codex/agents/` or `~/.codex/agents/`, rather than every TOML present in `speckit-pro/codex-agents/` when those sets differ. The expected copied and verified set at specification time is `autopilot-fast-helper.toml`, `phase-executor.toml`, `clarify-executor.toml`, `checklist-executor.toml`, `analyze-executor.toml`, `implement-executor.toml`, `codebase-analyst.toml`, `spec-context-analyst.toml`, and `domain-researcher.toml`. Documentation MUST NOT list `uat-runbook-author.toml` as an expected installed file unless the plan records and approves a narrow source correction that updates the installer copied set before implementation.
- **FR-012**: Documentation MUST tell users to restart Codex after plugin enablement changes, custom-agent installation, rerunning `$install` after bundled custom-agent TOML updates, or manual `~/.codex/config.toml` edits that affect plugin or skill state. Documentation MUST tell users to rerun `$install` after a plugin update when the installer report, expected TOML list, model lines, or bundled custom-agent behavior has changed before expecting updated custom agents.
- **FR-013**: Documentation MUST include a short install-safety block covering sandbox mode, approval prompts, network access, installed plugin cache/source distinction, selected custom-agent destination permissions, bundled lifecycle hook configuration as a plugin payload component, and external app or MCP authentication implications only as they affect first install. The block MUST warn that default `~/.codex/agents/` is outside most project workspaces and may require approval, while project-scoped `.codex/agents/` is an explicit destination override. The block MUST identify `codex-hooks.json` as bundled plugin payload configuration when present, state that hook behavior remains governed by Codex sandbox, approval, and configured policy controls, and avoid implying silent hook execution or approval bypass. Documentation MUST link or defer to DOC-008 for full trust/security analysis, managed policy, hook/MCP/agent risk detail, permission troubleshooting, stale-cache diagnosis, and update/remove/rollback procedures.
- **FR-014**: Documentation MUST preserve cross-links to DOC-007 and DOC-008 for future reference-depth and troubleshooting/security-depth work.
- **FR-015**: Documentation MUST keep Claude Code installation instructions out of DOC-004 content except for an explicit cross-link to the DOC-003-owned path.
- **FR-016**: Implementation MUST remain documentation-only unless the plan records and justifies a narrow source correction for a docs contradiction.
- **FR-017**: PR readiness MUST include `cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, `bash tests/speckit-pro/run-all.sh`, and a manual source-backed command-snippet review covering every Codex command/path snippet introduced or changed by DOC-004.
- **FR-018**: Documentation MUST keep the Codex install path accessible for keyboard and screen-reader users: headings, lists, tables, and command groups MUST use semantic structure and clear labels; link text MUST describe its destination or purpose without relying on surrounding prose alone; command snippets MUST be grouped or labeled by platform, install scope, and source-of-truth context; safety warnings MUST be visible in text and not conveyed by color, icon, or callout styling alone; and any dense install path matrix MUST include clear headers plus a mobile-readable or screen-reader-friendly alternative such as a compact list/card sequence when the table would otherwise require difficult horizontal scanning.
- **FR-019**: Documentation MUST include a bounded stale-after-update checkpoint that tells users to inspect the marketplace source or copied personal payload, generated payload directory, installed plugin cache, selected custom-agent destination, and Codex restart state when the plugin appears stale after an update. The checkpoint MUST mention observable symptoms such as old skill text, old plugin metadata, unchanged custom-agent behavior, stale copied personal payloads, or generated-payload/source mismatch; it MUST provide clear next links to DOC-008 for deeper troubleshooting, update/remove, rollback, and stale-cache forensics and DOC-007 for reference details. DOC-004 MUST keep this checkpoint shallow and MUST NOT duplicate DOC-008's full troubleshooting matrix.

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
- **Install Safety Posture**: The combination of sandbox mode, approval policy, network access, local cache trust, bundled lifecycle hook awareness, and external authentication expectations presented before install.
- **Stale Update Checkpoint**: A short DOC-004 guidance block that helps users identify whether stale behavior is likely caused by an old marketplace source, stale copied generated payload, installed plugin cache state, old custom-agent TOML files, or missing restart, then hands deeper diagnosis to DOC-008 or DOC-007.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three documentation entry points describe the same Codex install sequence and contain zero contradictory path, command, cache, custom-agent, restart, verification, or bounded install-safety statements.
- **SC-002**: A first-time Codex user can choose repo-scoped, personal, or local installation from the docs in under 5 minutes without consulting source files outside the install guidance.
- **SC-003**: A user can verify custom-agent registration from the docs by checking every installer-copied TOML filename, with no required expected-installed file missing from the docs.
- **SC-004**: Security-minded readers encounter sandbox, approval, network, cache, and trust guidance before any step that could install or register plugin components.
- **SC-005**: PR readiness validation completes with docs-site validation, docs-site link validation, the default `speckit-pro` shell test suite passing, and the manual command-snippet review recorded as implementation or PR evidence.
- **SC-006**: Manual accessibility review confirms the Codex install page uses descriptive links, labeled command groups, text-visible warnings, semantic heading/list/table structure, and a mobile-readable or screen-reader-friendly alternative for any dense install path matrix.
- **SC-007**: A user who sees stale plugin behavior after an update can identify the likely surface to refresh or re-register from DOC-004 and can follow a clear DOC-008 or DOC-007 link for deeper diagnosis without DOC-004 becoming a troubleshooting matrix.

## Assumptions

- The target feature directory already exists at `specs/doc-004-codex-marketplace-installation-path/`; this specification does not create a new branch or feature directory.
- Official Codex docs refreshed on 2026-06-14 are sufficient for the specify and first clarify phase, and implementation will refresh them again if command wording changes before docs edits land.
- `codex plugin marketplace add --help` is acceptable as a local Codex CLI source for subcommand syntax when official docs confirm marketplace concepts but do not spell out a subcommand detail.
- Older local install skill wording such as `marketplace tmp root` and `active plugin install` is implementation-detail terminology; DOC-004 user-facing docs should use `installed plugin cache` unless explicitly explaining a bounded version-specific mismatch.
- The installer's actual copied and reported TOML set remains the source of truth for post-install verification. The raw `speckit-pro/codex-agents/` directory may reveal packaging drift, but DOC-004 user docs must describe shipped install behavior unless the plan records and implements a narrow source correction.
- Rerunning `$install` is the supported DOC-004-level recovery when a plugin update changes bundled custom-agent TOML templates; users still need to restart Codex after that copy step before expecting updated agents.
- DOC-004 covers bounded install guidance only. DOC-007 and DOC-008 own deeper reference, troubleshooting, update/rollback, and security/trust coverage.
- DOC-004 must not modify plugin manifests, generated payloads, installer behavior, TOML templates, hooks, marketplace behavior, release automation, or runtime behavior unless a plan-approved narrow source correction is explicitly recorded before implementation.

# Feature Specification: Troubleshooting, Security, Trust, Update, and Rollback

**Feature Branch**: `doc-008-troubleshooting-security-trust-update-rollback`

**Created**: 2026-06-18

**Status**: Draft

**Input**: User description: "DOC-008 should turn the existing troubleshooting and security/trust route shells into full user-facing documentation and add a top-level update/rollback route. It must stay docs-only and source-backed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Diagnose A Failure Symptom (Priority: P1)

As a user, I can match a failed install, stale behavior, missing custom agent, permission prompt, path confusion, version drift, or Spec Kit CLI prerequisite issue to a likely cause, inspect the right command or file, and apply a safe recommended fix.

**Why this priority**: Troubleshooting is the first support surface users need when an install or update does not behave as expected.

**Independent Test**: Open the troubleshooting page and verify that each in-scope failure class has a symptom-driven row with a likely cause, diagnostic command or file, recommended fix, platform label, and follow-up link.

**Acceptance Scenarios**:

1. **Given** a user has an install or runtime symptom, **When** they scan the troubleshooting matrix, **Then** they can find a row with symptom, likely cause, diagnostic command or file, recommended fix, platform label, and follow-up link.
2. **Given** a failure concept applies to Claude Code and Codex, **When** the troubleshooting page presents it, **Then** the row uses a shared `Both` platform label and includes platform-specific commands or file paths only where the diagnosis or fix differs.
3. **Given** the documentation runs in a browser, **When** a troubleshooting row includes a diagnostic action, **Then** the page presents copyable commands or file paths only and does not execute local commands, request permissions, or modify user configuration.

---

### User Story 2 - Evaluate Security And Trust Boundaries (Priority: P2)

As a security or platform evaluator, I can understand what SpecKit Pro can package or invoke on Claude Code and Codex, and distinguish official platform behavior from repository facts and recommended practice.

**Why this priority**: Evaluators need a fact-bound trust model before approving marketplace plugins, hooks, MCP/app integrations, agents, sandbox behavior, approval prompts, managed settings, or update paths.

**Independent Test**: Review the security and trust page and confirm every platform-behavior claim cites current official vendor documentation while every Racecraft-specific claim cites checked-in files or generated DOC-007 reference pages.

**Acceptance Scenarios**:

1. **Given** an evaluator needs to separate evidence types, **When** they read the trust model, **Then** claims are grouped as official vendor behavior, checked-in repository facts, or recommended practice.
2. **Given** an evaluator asks what the plugin can package or invoke, **When** they read the trust model, **Then** it covers source vs generated payload, installed cache/runtime state, manifests, skills, agents/custom agents, hooks, MCP/app integrations, sandboxing, approvals, and managed policy.
3. **Given** an evaluator expects certification or a formal control audit, **When** they read the page, **Then** it clearly states DOC-008 is user documentation, not a security audit, certification, threat model, or control attestation.

---

### User Story 3 - Recover From Stale Or Incorrect Installs (Priority: P3)

As a returning user, I can update, refresh, remove, reinstall, or rollback a stale or incorrect install without hand-editing generated payloads or installed caches.

**Why this priority**: Returning users need safe recovery guidance after marketplace updates, cache drift, copied payload drift, version mismatch, or custom-agent registration changes.

**Independent Test**: Open the update and rollback page and verify it defines each recovery case and routes users to platform-specific refresh, reinstall, remove, rollback, stale-payload, stale-cache, and version-sync procedures without adding a diagnostics command.

**Acceptance Scenarios**:

1. **Given** a user sees stale plugin behavior after an update, **When** they open the update and rollback page, **Then** they can distinguish update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version-sync cases.
2. **Given** a user needs to recover a stale install, **When** they follow the page, **Then** the page directs them to refresh marketplace source or generated payload through documented platform flows, reload or restart the agent surface as needed, and avoid direct edits to installed caches.
3. **Given** a user needs to return to a previous working release, **When** they follow rollback guidance, **Then** the page describes a platform-specific safe rollback path using a known marketplace source, generated payload, version, or commit reference without changing plugin behavior or generated payload semantics.

### Edge Cases

- A symptom maps to different Claude Code and Codex diagnostics; the page must keep one shared concept row when practical and use platform-specific diagnostic text inside the row.
- A failure class cannot be represented cleanly as a shared row; the page may use a short platform-specific subsection, but it must not duplicate common source, payload, cache, or trust explanations.
- A user has edited an installed plugin cache or copied payload manually; the recovery guidance must treat that as drift and route to reinstall, refresh, or regenerate from source rather than preserving the manual edit.
- A marketplace listing is current but generated payload or custom-agent registration is stale; the guidance must separate marketplace source, generated payload, installed cache, and copied custom-agent files.
- A managed policy blocks plugin install, marketplace source, hooks, MCP, network, or permissions; the docs must identify managed policy as a possible cause and avoid telling the user to bypass organization controls.
- A platform vendor changes command names, settings locations, sandbox behavior, or plugin behavior; implementation must verify current official docs before shipping platform-behavior claims.
- A Racecraft-specific statement is not covered by DOC-007 generated reference pages; implementation must cite the checked-in source file directly or omit the claim.
- Browser-rendered docs must not run a local doctor command, local filesystem probe, permission grant or request, plugin/workflow action, or automatic repair.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: DOC-008 MUST produce three user-facing docs pages: `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, and `docs-site/src/content/docs/update-and-rollback.md`.
- **FR-002**: The update and rollback page MUST be a top-level docs route with the slug `update-and-rollback.md` and the reader-facing label `Update & Rollback`, placed with the existing how-to/support navigation conventions.
- **FR-003**: The troubleshooting page MUST replace the DOC-002 shell with a symptom-driven matrix whose rows include symptom, likely cause, diagnostic command or file, recommended fix, platform label, and follow-up link. The matrix MUST be a semantic Markdown table or equivalent sectioned list with explicit headers for every required field; every row MUST have a readable first-column label, stable heading, slug, or anchor that preserves meaning when read outside table position.
- **FR-004**: Troubleshooting coverage MUST include at least one explicit matrix row for each required category: install failure, marketplace source, generated payload, installed cache/runtime state, permissions/approvals, missing or outdated Spec Kit CLI, missing or outdated GitHub CLI, missing or outdated jq, and Codex custom agents. Coverage MUST also preserve existing DOC-008 failure concepts for path confusion, version drift, and source-vs-generated-payload mismatch where those are not fully covered by the required category rows.
- **FR-005**: Troubleshooting rows MUST use `Claude Code`, `Codex`, or `Both` platform labels, using shared rows where concepts overlap and platform-specific text only where command, file, reload, restart, or policy behavior differs.
- **FR-006**: Browser docs MUST NOT execute local commands, grant or request local permissions, run or invoke plugin workflows, inspect the local filesystem, or modify user configuration. Troubleshooting matrix inspect command/file cells MUST contain only read-only inspection guidance: state-reporting commands, platform detail views, file paths to inspect manually, or source/reference links. The inspect column MUST NOT contain login, install, remove, reload, restart, approve, edit, set, unset, delete, rebuild, config-write, cache-edit, or token/secret-printing commands. Mutating recovery steps MUST appear only in recommended fix or linked recovery guidance, framed as manual operator actions with side effects stated before any command.
- **FR-007**: The security and trust page MUST separate official vendor behavior, checked-in repository facts, and recommended practice in distinct sections or clearly labeled claim groups.
- **FR-008**: Platform-behavior claims MUST cite current official vendor docs verified during implementation. The minimum citation inventory MUST include Claude Code discover/install plugins, create plugins, plugin marketplaces, plugins reference, settings, environment variables including `CLAUDE_CONFIG_DIR`, permissions, sandbox/security, hooks, subagents, and managed MCP; plus OpenAI Codex plugins, build plugins, agent skills, subagents/custom agents, hooks, MCP/app integrations, config basics, config reference, environment variables including `CODEX_HOME`, CLI reference for documented `codex plugin ...` commands, sandboxing, permissions, approvals/security, managed configuration, and AGENTS.md. DOC-008 MUST cite the narrowest official page for each platform claim and MUST NOT use vendor docs as evidence for Racecraft source, generated payload, or local observed cache layout unless the vendor doc explicitly documents that behavior.
- **FR-009**: Racecraft-specific behavior MUST cite checked-in repository files or generated DOC-007 reference pages for manifests, skills, agents, hooks, scripts, tests, and source-vs-dist evidence.
- **FR-010**: The security and trust page MUST cover source tree, generated payloads, installed cache/runtime state, marketplace manifests, skills, agents/custom agents, hooks, MCP/app integrations, sandboxing, approvals, managed settings or policy, update flow, and rollback boundaries.
- **FR-011**: The update and rollback page MUST define and distinguish update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version-sync cases for Claude Code, Codex, or both. Each recovery case MUST identify the read-only checkpoint, manual operator action, expected side effect, reload or restart need, and source citation. Recovery cases MUST be represented as semantic Markdown table rows or equivalent sectioned list items with explicit headers for every required field, plus a case label, stable heading, slug, or anchor that remains understandable without relying on table position.
- **FR-012**: Recovery guidance MUST tell users to inspect marketplace/source state first, then generated or copied payload state, then platform-managed refresh, reinstall, remove, reload, or restart steps, then Codex custom-agent reinstall when applicable, before any last-resort cache guidance. Payload rebuild and version-sync scripts may be cited as maintainer/source-infrastructure evidence or handoff points, but not as end-user recovery commands owned by DOC-008.
- **FR-013**: DOC-008 MUST NOT present direct installed-cache edits, direct cache deletion, or cache directory removal as the default stale-install or stale-cache fix. If direct cache mutation is mentioned, it MUST be framed as a last-resort manual operator action after marketplace source, generated payload, reinstall/refresh, reload/restart, version sync, managed policy, and custom-agent registration checks have been considered, and it MUST state side effects before any command or path.
- **FR-014**: Cache paths, installed locations, and cache-mutating commands may be classified as official vendor behavior only when current official vendor docs explicitly document that exact path, command, or behavior. Otherwise, cache wording MUST be classified as repository fact, local runtime or CLI evidence, or recommended practice.
- **FR-015**: Codex recovery guidance MUST preserve the separation between plugin installation, bundled skill loading, marketplace upgrade/add/remove/list, custom-agent registration through `@SpecKit Pro -> install` or `$install`, and Codex restart. Codex guidance MUST cite `CODEX_HOME`, plugin or marketplace CLI commands, `codex plugin remove`, and JSON `installedPath` fields only where current official OpenAI docs document them, and MUST NOT describe a stable hardcoded Codex plugin cache path as vendor behavior unless current official docs explicitly document it.
- **FR-016**: Claude Code recovery guidance MUST preserve the separation between marketplace update/remove, plugin install/uninstall, `/reload-plugins`, plugin detail inspection, managed policy, installed runtime state, and version or cache-key behavior. Even when Claude Code docs document cache paths or cache-clearing recovery, DOC-008 MUST keep those actions out of inspection columns and frame them as scoped recovery steps rather than default fixes.
- **FR-017**: The three pages MUST cross-link to the platform install guides, DOC-007 generated reference subpages, first-run/lifecycle docs where relevant, and each other for follow-up from symptom to trust or recovery detail. DOC-008 MUST NOT require hand-edited backlinks inside generated `docs-site/src/content/docs/reference/*.md`; any reference-to-DOC-008 handoff must live in hand-authored `reference.md` or be implemented through an explicit reference-generator change. Troubleshooting, security/trust, and update/rollback pages MUST use stable headings or anchors for support-linkable sections and descriptive link text that identifies the destination without surrounding prose; generic required follow-up labels such as `here`, `learn more`, `read more`, or repeated ambiguous `details` MUST NOT be used.
- **FR-018**: DOC-008 MUST NOT change plugin behavior, generated payload semantics, manifests, hooks, release automation, CI behavior, SpecKit CLI behavior, browser-side diagnostics, or local repair commands.
- **FR-019**: DOC-008 validation MUST use the docs-site verification bundle: `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, `pnpm --dir docs-site reference:check`, and the configured full verification command.

### Source Evidence Confirmed For Implementation

- Claude Code official docs: [Discover and install prebuilt plugins](https://code.claude.com/docs/en/discover-plugins), [Create plugins](https://code.claude.com/docs/en/plugins), [Plugins reference](https://code.claude.com/docs/en/plugins-reference), [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Settings](https://code.claude.com/docs/en/settings), [Environment variables](https://code.claude.com/docs/en/env-vars), [Permissions](https://code.claude.com/docs/en/permissions), [Sandbox environments](https://code.claude.com/docs/en/sandbox-environments), [Security](https://code.claude.com/docs/en/security), [Hooks](https://code.claude.com/docs/en/hooks), [Subagents](https://code.claude.com/docs/en/sub-agents), and [Managed MCP](https://code.claude.com/docs/en/managed-mcp).
- OpenAI Codex official docs: [Plugins](https://developers.openai.com/codex/plugins), [Build plugins](https://developers.openai.com/codex/plugins/build), [Agent Skills](https://developers.openai.com/codex/skills), [Subagents](https://developers.openai.com/codex/subagents), [Hooks](https://developers.openai.com/codex/hooks), [MCP](https://developers.openai.com/codex/mcp), [Config basics](https://developers.openai.com/codex/config-basic), [Config reference](https://developers.openai.com/codex/config-reference), [Environment variables](https://developers.openai.com/codex/environment-variables), [CLI reference](https://developers.openai.com/codex/cli/reference), [Sandbox](https://developers.openai.com/codex/concepts/sandboxing), [Permissions](https://developers.openai.com/codex/permissions), [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security), [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration), and [AGENTS.md](https://developers.openai.com/codex/guides/agents-md).
- Racecraft source-backed docs: `docs-site/src/content/docs/reference/{manifests,skills,agents,hooks,scripts,tests,source-vs-dist}.md`, `docs-site/src/content/docs/install/claude-code.md`, and `docs-site/src/content/docs/install/codex.md`.

### Reviewability Notes *(if applicable)*

- DOC-008 is docs-only. Reviewability exceptions must not be used to justify runtime behavior changes, generated payload changes, hook changes, manifest changes, release automation changes, or CI changes.
- Generated payloads and installed caches may be cited as evidence, but implementation must edit source-owned docs and source-owned plugin files only when a later spec owns that behavior.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 380 lines of Markdown content, excluding phase artifacts
- **Projected production files**: 0 runtime production files
- **Projected total files**: About 7 docs/process files, including three user-facing pages plus navigation, install-page links, and the hand-authored reference shell handoff
- **Budget result**: within budget
- **Split decision**: Keep as one DOC-008 slice because troubleshooting, trust, and update/rollback share the same source/payload/cache/platform evidence model and the design concept estimated one reviewable slice.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Troubleshooting Row**: A symptom-driven matrix row with symptom, likely cause, read-only inspect command or file, recommended fix, platform label, follow-up link, and a readable row label or anchor that remains meaningful outside visual table position.
- **Read-only Inspection**: A state-reporting command, platform detail view, manual file path inspection, or source/reference link that helps a user diagnose state without mutating local files, credentials, permissions, installed caches, plugin state, custom-agent registration, or managed policy.
- **Manual Recovery Action**: A user-run recovery step that can mutate local plugin state, marketplace state, copied payloads, custom-agent registration, process state, or runtime cache state, and therefore must be separated from read-only inspection with expected side effects stated first.
- **Rollback Anchor**: A known marketplace source, Git ref, generated payload path, manifest version, CLI JSON field, or source-vs-dist reference that identifies the state a rollback or version-sync procedure should return to.
- **Platform Label**: The row-level label `Claude Code`, `Codex`, or `Both` used to show where a symptom or procedure applies.
- **Trust Claim**: A statement about platform behavior, repository fact, or recommended practice that must be grouped by evidence type and backed by a source. Implementation should prefer a table shape with platform, claim, evidence type, citation, and boundary note when presenting dense trust claims.
- **Official Vendor Behavior**: Behavior claimed from current Claude Code or OpenAI Codex documentation, such as plugin loading, marketplace behavior, settings, sandboxing, approvals, hooks, subagents, skills, or managed policy.
- **Repository Fact**: Behavior or file layout proven by checked-in Racecraft source, generated DOC-007 reference pages, generated payload inventories, or docs-site content.
- **Recommended Practice**: User guidance derived from official behavior and repository facts, such as not editing installed caches or generated payloads directly. Recommended-practice claims MUST be phrased as derived guidance, not as platform guarantees, security attestations, certifications, or audit findings.
- **Recovery Case**: One of update, refresh, reinstall, remove, rollback, stale payload, stale cache, or version sync, presented with a readable case label or anchor and explicit field labels for checkpoint, manual action, side effect, reload or restart need, and source evidence.
- **Installed Runtime State**: Claude Code or Codex local runtime plugin/cache/custom-agent state that users may inspect but should not treat as editable source of truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The docs site contains three user-facing routes for troubleshooting, security/trust, and update/rollback, and all internal links among them resolve.
- **SC-002**: The troubleshooting matrix includes at least one row for each required category in FR-004, and 100% of rows include symptom, likely cause, diagnostic command or file, recommended fix, platform label, and follow-up link.
- **SC-003**: 100% of platform-behavior claims on the security/trust and update/rollback pages cite official Claude Code or OpenAI Codex documentation.
- **SC-004**: 100% of Racecraft-specific source, payload, manifest, skill, agent, hook, cache, or file-layout claims cite checked-in source files or DOC-007 generated reference pages.
- **SC-005**: The security and trust page clearly separates official vendor behavior, checked-in repository facts, and recommended practice, and states that DOC-008 is not a security audit, certification, formal threat model, or control attestation.
- **SC-006**: The update and rollback page defines all eight recovery cases from FR-011 and gives at least one safe Claude Code or Codex recovery path for each applicable case, with checkpoint, manual action, side effect, reload-or-restart expectation, and source evidence.
- **SC-007**: The final DOC-008 diff changes docs/process surfaces only and contains no plugin behavior, generated payload semantics, manifest, hook, release automation, or CI changes.
- **SC-008**: `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, `pnpm --dir docs-site reference:check`, and `pnpm --dir docs-site validate && pnpm --dir docs-site validate:links` pass.
- **SC-009**: 100% of troubleshooting rows and update/rollback recovery cases remain understandable as static Markdown by using semantic headers or equivalent section labels, readable row/case labels, stable support-link headings or anchors where applicable, and descriptive link text for all required follow-up links.

## Assumptions

- The route slug and sidebar label are resolved as `update-and-rollback.md` and `Update & Rollback` under the existing top-level how-to/support docs navigation.
- Shared troubleshooting rows with `Claude Code`, `Codex`, or `Both` labels are sufficient for most failure classes; short platform-specific subsections are allowed only when a shared row would be unclear.
- Official vendor docs listed in this spec were verified on 2026-06-18 and must be rechecked during implementation before publishing detailed platform-behavior wording.
- Existing DOC-007 generated reference pages are the preferred Racecraft-specific citation source where they cover the claim; otherwise implementation should cite the checked-in source file directly.
- Browser documentation can show commands and files for users to run or inspect, but all local execution, permission approval, and configuration modification remain user-controlled outside the docs site.

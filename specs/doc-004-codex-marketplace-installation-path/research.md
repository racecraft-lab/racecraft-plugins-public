# Research: Codex marketplace installation path

**Date**: 2026-06-14

## Decision 1: Keep DOC-004 as one focused Codex install page plus README alignment

**Decision**: Expand `docs-site/src/content/docs/install/codex.md` into the
full Codex install guide and update `README.md` and `speckit-pro/README.md`
only enough to preserve the same critical install invariants.

**Rationale**: DOC-002 already created the route shell, and Grill Me Q1 selected
one focused page. Grill Me Q6 selected "Update all docs now", so the READMEs
must not remain contradictory.

**Alternatives considered**:

- Multiple Codex pages: deferred to DOC-007 and DOC-008 to avoid expanding this
  slice into reference or troubleshooting depth.
- Docs-site only: rejected because README and plugin README entry points would
  continue to show partial or conflicting Codex install guidance.

## Decision 2: Use official marketplace and cache terminology

**Decision**: Use official Codex terms and path patterns for marketplace files,
marketplace source forms, and installed plugin cache behavior.

**Rationale**: OpenAI's Build plugins docs describe repo marketplaces at
`$REPO_ROOT/.agents/plugins/marketplace.json`, personal marketplaces at
`~/.agents/plugins/marketplace.json`, `source.path` resolution relative to the
marketplace root, CLI marketplace source forms, and installed plugin cache path
`~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`. The local
CLI help confirms `codex plugin marketplace add` accepts local path,
`owner/repo[@ref]`, HTTPS Git URL, SSH Git URL, `--ref`, repeatable `--sparse`,
and `--json`.

**Alternatives considered**:

- Use older install-skill terms such as "marketplace tmp root" or "active plugin
  install": rejected for user-facing first-install copy because the spec
  requires official installed plugin cache terminology.
- Omit CLI source forms: rejected because FR-007 requires source-backed CLI
  guidance, including HTTP or HTTPS Git URLs and `--json`.

## Decision 3: Treat `dist/codex/speckit-pro/` as the installable Codex payload

**Decision**: Tell users that `dist/codex/speckit-pro/` is the generated Codex
payload and `speckit-pro/` is the mixed authoring source tree.

**Rationale**: The repo-scoped marketplace at `.agents/plugins/marketplace.json`
uses `source.path: ./dist/codex/speckit-pro`. The source plugin manifest points
skills at `./codex-skills/`, while the generated payload manifest points skills
at `./skills/`. That confirms personal/local installs should copy or sync the
generated payload, not the authoring source tree.

**Alternatives considered**:

- Point personal installs at `speckit-pro/`: rejected by FR-004 and by local
  source evidence because the authoring tree mixes platform-specific source
  layout that differs from the install payload.
- Regenerate or change payload behavior: rejected as out of scope for DOC-004.

## Decision 4: List the installer-copied nine TOML custom-agent files

**Decision**: User-facing verification must list:

- `autopilot-fast-helper.toml`
- `phase-executor.toml`
- `clarify-executor.toml`
- `checklist-executor.toml`
- `analyze-executor.toml`
- `implement-executor.toml`
- `codebase-analyst.toml`
- `spec-context-analyst.toml`
- `domain-researcher.toml`

Do not list `uat-runbook-author.toml` as expected installed output in DOC-004.

**Rationale**: `speckit-pro/codex-agents/uat-runbook-author.toml` exists in the
source directory, but the install skill and installer script verify/copy only
the nine files above. The user explicitly clarified not to change installer
behavior in this plan.

**Alternatives considered**:

- List every source TOML file: rejected because it would make the docs disagree
  with actual installer verification.
- Change installer behavior to copy `uat-runbook-author.toml`: rejected because
  the plan must not change installer behavior without a narrow source
  correction approval.

## Decision 5: Separate bundled skills, skill metadata sidecars, and custom agents

**Decision**: Explain three Codex surfaces:

1. Bundled skills load from the installed plugin payload.
2. Skill metadata sidecars such as `agents/openai.yaml` describe skill UI,
   invocation, or policy metadata.
3. TOML custom agents must be copied into `.codex/agents/` or
   `~/.codex/agents/` by `@SpecKit Pro -> install` or `$install`.

**Rationale**: OpenAI's Skills docs describe skills as `SKILL.md` packages with
optional supporting folders, while OpenAI's Subagents docs describe custom
agents as TOML files. The local install skill exists because plugin
installation does not automatically register those TOML custom agents.

**Alternatives considered**:

- Collapse skills and custom agents into one "agents" concept: rejected because
  it obscures why `$install` is necessary.
- Deeply document every skill sidecar: deferred to DOC-007.

## Decision 6: Keep trust guidance to first-install safety

**Decision**: Include a short safety block covering sandbox mode, approval
policy, network access, outside-workspace writes, installed cache/source
distinction, bundled lifecycle hook configuration, and external app/MCP
authentication implications only as first install expectations.

**Rationale**: OpenAI approvals/security docs describe sandbox mode and approval
policy as separate controls and note local defaults around workspace-limited
writes and network approvals. OpenAI plugin docs describe bundled hooks as part
of the plugin package, and local manifests point to `codex-hooks.json`. DOC-004
must help users approve only the expected local write of named TOML files or
reject and rerun with a project-scoped destination, while naming bundled hook
configuration without expanding into hook policy or lifecycle security. DOC-008
owns the full trust/security lifecycle.

**Alternatives considered**:

- Full trust model or hook policy guide in DOC-004: rejected as DOC-008 scope.
- Defer trust guidance entirely: rejected because first-time install includes
  plugin installation, network decisions, and possible writes to
  `~/.codex/agents/`.

## Decision 7: Preserve existing validation scripts

**Decision**: Use existing validation commands without changing package scripts:
`cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, and
`bash tests/speckit-pro/run-all.sh`.

**Rationale**: `docs-site/package.json` defines `validate` as `pnpm check &&
pnpm build` and `validate:links` as `pnpm build`. The spec requires using the
current DOC-002 link-validation hook even though it presently aliases a build.

**Alternatives considered**:

- Add or replace link-check tooling in DOC-004: rejected because DOC-010 owns
  docs validation hardening.
- Skip the full repo suite for docs-only work: rejected because Grill Me Q7
  selected the stricter full repo suite.

## Decision 8: Keep stale-update recovery as a bounded checkpoint

**Decision**: Add a short stale-after-update checkpoint to DOC-004 instead of a
full troubleshooting matrix. The checkpoint tells users to inspect the
marketplace source or copied personal payload, generated payload, installed
plugin cache, selected custom-agent destination, and restart state. It also
tells users to rerun `@SpecKit Pro -> install` or `$install` after plugin
updates that change bundled custom-agent TOML files, then restart Codex.

**Rationale**: OpenAI's local plugin guidance says to update the plugin
directory targeted by the marketplace entry and restart Codex after plugin
changes. OpenAI's skills guidance says Codex detects skill changes
automatically, but users should restart Codex if an update does not appear. The
SpecKit Pro install skill/script already treats `install` as an install,
refresh, repair, and verify path for Codex custom-agent TOML files and always
finishes by telling users to restart Codex.

**Alternatives considered**:

- Full symptom decision tree in DOC-004: rejected because DOC-008 owns
  troubleshooting, stale-cache forensics, update/remove, rollback, and the full
  trust model.
- No stale guidance in DOC-004: rejected because the Codex install path must
  give users a shallow checkpoint when update or custom-agent state appears
  stale before handing off to DOC-007 or DOC-008.

## Source Index

- OpenAI Codex plugins: https://developers.openai.com/codex/plugins
- OpenAI Codex build plugins: https://developers.openai.com/codex/plugins/build
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Codex subagents: https://developers.openai.com/codex/subagents
- OpenAI Codex permissions: https://developers.openai.com/codex/permissions
- OpenAI Codex approvals/security: https://developers.openai.com/codex/agent-approvals-security
- Local CLI: `codex plugin marketplace add --help`
- Local files: `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, `speckit-pro/codex-skills/install/SKILL.md`, `speckit-pro/codex-skills/install/scripts/install-codex-agents.sh`, `speckit-pro/codex-agents/*.toml`, `speckit-pro/codex-hooks.json`

## Implementation Refresh: T001-T003 Source Evidence

Codex manual fetched during implementation with the OpenAI docs helper reported
the local manual was current. The implementation pass re-read the current manual
sections for Build plugins, Plugins, Agent Skills, Subagents, Permissions,
Agent approvals and security, Sandbox, and Hooks.

Official evidence remained consistent with the plan:

- Build plugins confirms repo marketplaces at
  `$REPO_ROOT/.agents/plugins/marketplace.json`, personal marketplaces at
  `~/.agents/plugins/marketplace.json`, `source.path` resolution relative to
  the marketplace root, local and Git-backed marketplace sources, plugin
  directory browsing, and restart-after-change guidance.
- Plugins confirms the CLI plugin browser path is `codex` then `/plugins`,
  plugin installation happens through marketplace entries, bundled skills are
  available after plugin install, and existing approval settings plus external
  app or MCP authentication policies still apply.
- Agent Skills confirms `$skill` explicit invocation, automatic skill-change
  detection with restart as the fallback when updates do not appear, and
  `agents/openai.yaml` as optional skill metadata rather than TOML custom-agent
  registration.
- Subagents confirms custom agents are standalone TOML files under
  `~/.codex/agents/` or `.codex/agents/`, inherit parent sandbox and approval
  controls, and may declare fields such as `name`, `description`,
  `developer_instructions`, `model`, `model_reasoning_effort`, and
  `sandbox_mode`.
- Permissions, approvals, sandbox, and hooks confirm DOC-004 should keep safety
  language bounded to first-install expectations: workspace-limited writes,
  outside-workspace approvals, network approvals, plugin-bundled lifecycle hook
  configuration, and the fact that hooks do not bypass Codex trust, sandbox, or
  approval controls.

Local CLI evidence from `codex plugin marketplace add --help` confirmed local
path, `owner/repo[@ref]`, HTTPS Git URL, SSH Git URL, `--ref`, repeatable
Git-only `--sparse`, and `--json`. The command emitted a non-blocking sandbox
warning about PATH aliases, but returned the required help text.

Local repository evidence remained consistent with the plan:

- `.agents/plugins/marketplace.json` exposes `racecraft-plugins-public` with
  `speckit-pro` version `2.14.0` and `source.path` set to
  `./dist/codex/speckit-pro`.
- source/dist manifest versions: 2.14.0 in both
  `speckit-pro/.codex-plugin/plugin.json` and
  `dist/codex/speckit-pro/.codex-plugin/plugin.json`; the source manifest uses
  `skills: ./codex-skills/`, while the generated payload manifest uses
  `skills: ./skills/`.
- The generated payload and source manifest both reference `codex-hooks.json`;
  source and generated hook payloads match and define a `UserPromptSubmit`
  command hook that checks SpecKit CLI availability for SpecKit prompts.
- The installer-copied TOML files remain nine:
  `autopilot-fast-helper.toml`, `phase-executor.toml`,
  `clarify-executor.toml`, `checklist-executor.toml`,
  `analyze-executor.toml`, `implement-executor.toml`,
  `codebase-analyst.toml`, `spec-context-analyst.toml`, and
  `domain-researcher.toml`.
- `uat-runbook-author.toml` is still present in source and generated
  `codex-agents/` directories, but the install skill and installer script do
  not copy it. DOC-004 user-facing verification should continue to list only
  the installer-copied set unless a later plan records an approved installer
  correction.

Reconciliation result: refreshed official and local evidence does not require a
non-docs source correction for T001-T004. `spec.md`, `plan.md`,
`data-model.md`, and the content contract remain aligned with the refreshed
evidence. README alignment, detailed install matrices, exact command-snippet
review evidence, and full validation remain owned by later DOC-004 tasks.

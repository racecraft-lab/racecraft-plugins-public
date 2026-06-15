---
title: "Install: Codex"
---

Use this route when you are installing SpecKit Pro in Codex and need to choose
the right marketplace, plugin payload, custom-agent destination, and
verification path.

## Install Decision

Start by choosing the install context before running commands:

- **Repo-scoped marketplace:** use this when you opened this repository in Codex
  and want Codex to read `.agents/plugins/marketplace.json`.
- **Personal or local marketplace:** use this when you want your own Codex
  setup to point at a copied generated payload.
- **CLI marketplace add:** use this when you want Codex to track a local or
  Git-backed marketplace source from the command line.

Claude Code installation is a separate path. Use the
[Claude Code install guide](/racecraft-plugins-public/install/claude-code/)
for Claude Code commands.

## Source, Payload, And Cache

Keep these surfaces separate:

- `speckit-pro/` is the mixed authoring source tree. Do not install Codex from
  this path.
- `dist/codex/speckit-pro/` is the generated Codex plugin payload.
- `.agents/plugins/marketplace.json` is this repository's Codex marketplace
  catalog.
- `speckit-pro/.codex-plugin/plugin.json` is source manifest evidence.
- `dist/codex/speckit-pro/.codex-plugin/plugin.json` is generated payload
  manifest evidence.
- `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` is Codex's
  installed plugin cache. Treat it as runtime state, not as the editable source
  of truth.

The detailed source and file-layout reference belongs in
[DOC-007 reference](/racecraft-plugins-public/reference/).

## Install Paths

Use this outline to pick the next task:

| Context | Marketplace source | Payload to install | Use when |
|---|---|---|---|
| Repo-scoped | `.agents/plugins/marketplace.json` | `./dist/codex/speckit-pro` | You are working inside this repository in Codex. |
| Personal or local | `~/.agents/plugins/marketplace.json` | A copied or synced `dist/codex/speckit-pro/` payload | You want the plugin available outside this repo. |
| CLI marketplace add | `codex plugin marketplace add <source>` | The plugin path named by that marketplace | You want Codex to manage a local or Git-backed marketplace source. |

Compact checklist:

1. Confirm whether the marketplace source is repo-scoped, personal/local, or
   CLI-managed.
2. Confirm the plugin entry points at the generated Codex payload, not
   `speckit-pro/`.
3. Install SpecKit Pro from Codex's plugin browser.
4. Run the Codex custom-agent registration step.
5. Restart Codex and verify the expected skill and custom-agent behavior.

Codex plugin browser command group, repo-scoped or configured marketplace:

```text
codex
/plugins
```

## Register Custom Agents

Plugin installation loads SpecKit Pro's bundled skills, but it does not
automatically register the bundled Codex custom agents. After installing the
plugin, run the Codex-only install skill:

```text
@SpecKit Pro -> install
```

or:

```text
$install
```

The install skill copies the installer-copied SpecKit Pro TOML custom-agent
files into the selected Codex agent directory. The default destination is
`~/.codex/agents/`; `.codex/agents/` is the project-scoped destination when you
explicitly choose a repo-local registration.

## Verify The Install

After the custom-agent registration step:

1. Review the install skill report for the source directory, destination
   directory, effective model, copied filenames, and restart instruction.
2. Confirm unrelated user custom agents were preserved.
3. Restart Codex.
4. Start a new Codex thread and verify a simple `$speckit-*` workflow can load
   the plugin skill surface.

The full expected TOML inventory and command-snippet review belong to the later
DOC-004 user-story tasks and the
[DOC-007 reference](/racecraft-plugins-public/reference/).

## Stale Update Checkpoint

If SpecKit Pro still looks stale after an update, keep the first check shallow:

- Symptoms can include old skill text, old plugin metadata, unchanged
  custom-agent behavior, a stale copied personal payload, or mismatch between
  source and generated payload.
- Inspect the marketplace source or copied personal payload, the generated
  payload directory, the installed plugin cache, the selected custom-agent
  destination, and whether Codex was restarted.
- Rerun `@SpecKit Pro -> install` or `$install` after an update that changes
  bundled custom-agent TOML files, then restart Codex.

Do not edit the installed plugin cache. Use
[DOC-008 troubleshooting](/racecraft-plugins-public/troubleshooting/) for
deeper stale-cache diagnosis, update or remove procedures, rollback, and
permission repair. Use [DOC-007 reference](/racecraft-plugins-public/reference/)
for command, manifest, payload, skill, agent, and file-layout detail.

## Install Safety

Safety warning: Codex sandbox mode and approval policy still apply during plugin
installation and custom-agent registration.

- Git-backed marketplace setup or plugin installation may require network
  access or network approval.
- `~/.codex/agents/` is outside most project workspaces, so writing there may
  require approval. Approve only the expected local write of the named SpecKit
  Pro TOML custom-agent files, or reject the prompt and rerun with
  `.codex/agents/` or narrower permissions.
- SpecKit Pro's generated Codex payload may include lifecycle hook
  configuration such as `codex-hooks.json`. Hook behavior remains governed by
  Codex sandbox, approval, hook trust, and configured policy controls.
- External app and MCP authentication, if a future plugin payload uses them,
  remains subject to the connected service and Codex approval flow.

The full security, trust, hook policy, managed policy, update, rollback, and
stale-cache lifecycle belongs in
[DOC-008 security and trust](/racecraft-plugins-public/security-and-trust/) and
[DOC-008 troubleshooting](/racecraft-plugins-public/troubleshooting/).

## Source Evidence And Boundaries

This page is grounded in:

- [OpenAI Codex plugins](https://developers.openai.com/codex/plugins)
- [OpenAI Codex build plugins](https://developers.openai.com/codex/plugins/build)
- [OpenAI Codex skills](https://developers.openai.com/codex/skills)
- [OpenAI Codex subagents](https://developers.openai.com/codex/subagents)
- [OpenAI Codex permissions](https://developers.openai.com/codex/permissions)
- [OpenAI Codex approvals and security](https://developers.openai.com/codex/agent-approvals-security)
- Local CLI help for `codex plugin marketplace add --help`
- Local repository evidence in `.agents/plugins/marketplace.json`,
  `speckit-pro/.codex-plugin/plugin.json`,
  `dist/codex/speckit-pro/.codex-plugin/plugin.json`,
  `speckit-pro/codex-skills/install/SKILL.md`,
  `speckit-pro/codex-skills/install/scripts/install-codex-agents.sh`,
  `speckit-pro/codex-agents/*.toml`, and `speckit-pro/codex-hooks.json`

DOC-004 stays bounded to Codex first-install guidance. DOC-007 owns deeper
reference content, and DOC-008 owns troubleshooting, update, remove, rollback,
managed-policy, stale-cache forensics, and full trust or security lifecycle
depth.

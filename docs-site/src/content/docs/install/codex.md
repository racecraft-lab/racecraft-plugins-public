---
title: "Install: Codex"
description: "Install SpecKit Pro in Codex — choose the right marketplace, plugin payload, custom-agent destination, and verification step for your install context."
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

Claude Code installation is the separate DOC-003-owned path. Use the
[Claude Code install guide](/racecraft-plugins-public/install/claude-code/)
for Claude Code commands.

## Source, Payload, And Cache

Keep these surfaces separate:

- `speckit-pro/` is the mixed authoring source tree. Do not install Codex from
  this path. Do not point a personal or local Codex marketplace at `speckit-pro/`.
- `dist/codex/speckit-pro/` is the generated Codex plugin payload.
- `.agents/plugins/marketplace.json` is this repository's Codex marketplace
  catalog.
- `speckit-pro/.codex-plugin/plugin.json` is source manifest evidence.
- `dist/codex/speckit-pro/.codex-plugin/plugin.json` is generated payload
  manifest evidence.
- `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` is Codex's
  installed plugin cache. Treat it as runtime state, not as the editable source
  of truth. For local plugins, `$VERSION` is `local`.

When source changes, update the marketplace source or copied personal payload, then reinstall or refresh the plugin. Do not edit the installed plugin cache to
try to patch a stale install.

For generated reference detail, use the focused DOC-007 pages:
[manifests](/racecraft-plugins-public/reference/manifests/),
[skills](/racecraft-plugins-public/reference/skills/),
[agents](/racecraft-plugins-public/reference/agents/),
[hooks](/racecraft-plugins-public/reference/hooks/), and
[source vs dist](/racecraft-plugins-public/reference/source-vs-dist/).

## Install Path Matrix

Use this accessible matrix to pick the next task. The headers identify the
install context, marketplace source, payload source of truth, and when to use
each flow.

| Context | Marketplace source | Payload to install | Use when |
|---|---|---|---|
| Repo-scoped marketplace entry | `.agents/plugins/marketplace.json` | `./dist/codex/speckit-pro` from this repository | You opened this repo in Codex and want to install from the checked-in marketplace. |
| Personal or local generated-payload layout | `~/.agents/plugins/marketplace.json` | A copied or synced `dist/codex/speckit-pro/` payload, for example `~/.codex/plugins/speckit-pro/` | You want SpecKit Pro available outside this repository. |
| CLI marketplace source examples | `codex plugin marketplace add <source>` | The plugin path named by the local or Git-backed marketplace source | You want Codex to track a marketplace source through the CLI. |

## Compact Install Path List

- **Repo-scoped:** use `.agents/plugins/marketplace.json`. Its `speckit-pro`
  entry points at `./dist/codex/speckit-pro`, so the source of truth is the
  generated Codex payload in this repository.
- **Personal or local:** copy or sync `dist/codex/speckit-pro/` into a personal
  plugin location such as `~/.codex/plugins/speckit-pro/`, then point
  `~/.agents/plugins/marketplace.json` at that copied payload. Do not point a
  personal or local Codex marketplace at `speckit-pro/`.
- **CLI marketplace add:** use `codex plugin marketplace add <source>` for a
  local marketplace root, GitHub shorthand, or a Git URL source. Install the
  plugin entry from Codex after the marketplace source is added.

## Install From A Marketplace Entry

Codex plugin browser command group, repo-scoped or configured marketplace:

```text
codex
/plugins
```

Choose the Racecraft Public Plugins marketplace entry, then install
SpecKit Pro.

Repo-scoped Codex marketplace context:

- Open this repository in Codex.
- Use the checked-in `.agents/plugins/marketplace.json` marketplace.
- Confirm the `speckit-pro` entry uses `source.path`:

```text
./dist/codex/speckit-pro
```

Personal or local Codex marketplace context:

- Copy or sync the generated payload at `dist/codex/speckit-pro/` into a
  personal plugin location such as `~/.codex/plugins/speckit-pro/`.
- Point `~/.agents/plugins/marketplace.json` at the copied payload.
- Refresh the copied payload before expecting repo source changes to appear in
  your personal install.

CLI marketplace add command group, Codex CLI source context:

```text
codex plugin marketplace add ./local-marketplace-root
codex plugin marketplace add owner/repo
codex plugin marketplace add owner/repo@ref
codex plugin marketplace add owner/repo --ref main
codex plugin marketplace add https://github.com/example/plugins.git --sparse .agents/plugins
codex plugin marketplace add git@github.com:example/plugins.git
codex plugin marketplace add <source> --json
```

Supported source forms are local marketplace root directories, GitHub shorthand
such as `owner/repo` and `owner/repo@ref`, HTTP or HTTPS Git URLs, SSH Git URLs,
`--ref`, and `--json`. Repeat `--sparse PATH` only for Git marketplace sources
when you need more than one sparse checkout path.

## Register Custom Agents

Plugin installation loads SpecKit Pro's bundled skills, but it does not
automatically register the bundled Codex custom agents.

Keep these three Codex surfaces separate:

- Bundled skills load from the installed plugin payload.
- OpenAI agent metadata sidecars such as `agents/openai.yaml` describe skill
  UI, invocation, and policy metadata. They are not custom-agent registration.
- TOML custom-agent registration happens only when the install skill copies the
  bundled TOML files into `~/.codex/agents/` or `.codex/agents/`. Those TOML
  custom-agent files are copied into the selected destination; they are not
  loaded directly from the plugin bundle.

After installing the plugin, run the Codex-only custom-agent registration step:

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

Use this checklist:

1. Invoke `@SpecKit Pro -> install` from the SpecKit Pro plugin card, or invoke
   the same skill directly with `$install`.
2. Keep the default user destination, `~/.codex/agents/`, unless you want
   repo-local custom agents.
3. For an explicit project destination override, choose `.codex/agents/` in the
   repository you want to carry the custom-agent registration.
4. Approve only the expected local write of the named SpecKit Pro TOML files to
   the selected destination.
5. Restart Codex after the installer reports success.

Expected installed TOML files:

- `autopilot-fast-helper.toml`
- `phase-executor.toml`
- `clarify-executor.toml`
- `checklist-executor.toml`
- `analyze-executor.toml`
- `implement-executor.toml`
- `codebase-analyst.toml`
- `spec-context-analyst.toml`
- `domain-researcher.toml`
- `uat-runbook-author.toml`

## Verify The Install

After the custom-agent registration step, use observational verification only.
Do not edit the installed plugin cache, and do not manually edit the copied TOML
files as part of DOC-004 verification.

1. Review the install skill report for the source directory, destination
   directory, effective model, copied filenames, and restart instruction.
2. Confirm the selected destination contains the expected TOML filenames
   above.
3. Confirm the copied TOML model lines match the model reported by the installer
   when you used a supported fallback model.
4. Confirm unrelated user custom agents were preserved.
5. Restart Codex after plugin enablement changes, custom-agent install or
   refresh, or `~/.codex/config.toml` or `.codex/config.toml` edits that affect
   plugin or skill state.
6. Start a new Codex thread and verify a simple `$speckit-*` workflow can load
   the plugin skill surface.

Rerun `@SpecKit Pro -> install` or `$install` after a plugin update when the
installer report, expected TOML list, model lines, or bundled custom-agent
behavior has changed, then restart Codex before expecting updated custom agents.

The full command-snippet review belongs to the later DOC-004 validation tasks.
Use the generated [skills](/racecraft-plugins-public/reference/skills/) and
[manifests](/racecraft-plugins-public/reference/manifests/) reference pages
when you need source-cited command or manifest detail.

## Stale Update Checkpoint

If SpecKit Pro still looks stale after an update, keep the first check shallow:

- Symptoms can include old skill text, old plugin metadata, unchanged custom-agent behavior, a stale copied personal payload, or source/payload mismatch.
- Inspect the marketplace source or copied personal payload, the generated
  payload directory, the installed plugin cache, the selected custom-agent
  destination, and whether Codex was restarted.
- If the marketplace source or copied payload is stale, update the marketplace source or copied personal payload, then reinstall or refresh the plugin.
- Rerun `@SpecKit Pro -> install` or `$install` after an update that changes
  bundled custom-agent TOML files, then restart Codex.

Do not edit the installed plugin cache. Use
[Troubleshooting](/racecraft-plugins-public/troubleshooting/) to match stale
plugin text, stale copied payloads, missing custom agents, path, cache, version,
permission, or prerequisite symptoms to a likely cause. Use
[Update & Rollback](/racecraft-plugins-public/update-and-rollback/) for
marketplace refresh, reinstall, remove, rollback, stale-payload, stale-cache,
custom-agent refresh, and version-sync procedures. Use the generated
[skills](/racecraft-plugins-public/reference/skills/),
[agents](/racecraft-plugins-public/reference/agents/),
[manifests](/racecraft-plugins-public/reference/manifests/), and
[source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) pages for
command, manifest, payload, skill, agent, and file-layout detail.

## Install Safety

Safety warning: Codex sandbox mode and approval policy still apply during plugin
installation and custom-agent registration.

- Git-backed marketplace setup or plugin installation may require network
  access or network approval; network use remains governed by your Codex
  settings and any approval prompts.
- The installed plugin cache is runtime state, not the source of truth. Its
  path is `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`;
  update the marketplace source or generated payload instead of editing the
  installed cache.
- The default user-scoped destination is `~/.codex/agents/`, an
  outside-workspace write for most projects that may require approval before
  Codex writes there.
  Approve only the expected local write of the named SpecKit Pro TOML
  custom-agent files to the selected destination.
- For a narrower project-scoped `.codex/agents/` destination override, reject
  the prompt and rerun in the repository that should carry the custom-agent
  registration.
- SpecKit Pro's generated Codex payload may include `codex-hooks.json` as
  bundled plugin payload configuration for lifecycle hooks. This is not a
  separate permission grant. Hook behavior remains governed by Codex sandbox
  mode, approval prompts, and configured policy controls.
- External app or MCP authentication, if a future plugin payload uses it, is
  not automatic. It remains subject to the connected service and Codex approval
  flow.

DOC-008 owns hook trust analysis, managed policy, external authentication,
permission troubleshooting, update, remove, rollback, and stale-cache forensics.
The full security, trust, hook policy, and install lifecycle belong in
[DOC-008 security and trust](/racecraft-plugins-public/security-and-trust/) and
[Troubleshooting](/racecraft-plugins-public/troubleshooting/). Returning users
who need procedural recovery should use
[Update & Rollback](/racecraft-plugins-public/update-and-rollback/).

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

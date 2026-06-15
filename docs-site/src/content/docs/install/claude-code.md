---
title: "Install: Claude Code"
---

Use this route when you are installing SpecKit Pro in Claude Code and need to
choose the right marketplace, plugin payload, reload path, and verification
path.

## Install Decision

Start by choosing the install context before running commands:

- **Marketplace install:** use this when you want Claude Code to install
  SpecKit Pro from the Racecraft marketplace.
- **Repository source inspection:** use this when you need to inspect the
  authoring source and generated Claude payload before installing.
- **Managed or policy-controlled install:** use this when your Claude Code
  environment is governed by organization policy, managed settings, or approved
  marketplace sources.

Codex installation is the separate DOC-004-owned path. Use the
[Codex install guide](/racecraft-plugins-public/install/codex/) for Codex
commands.

## Source, Payload, And Cache

Keep these surfaces separate:

- `speckit-pro/` is the mixed authoring source tree. Do not treat it as the
  generated Claude install payload.
- `dist/claude/speckit-pro/` is the generated Claude Code plugin payload.
- `.claude-plugin/marketplace.json` is this repository's Claude Code
  marketplace catalog.
- `speckit-pro/.claude-plugin/plugin.json` is source manifest evidence.
- `dist/claude/speckit-pro/.claude-plugin/plugin.json` is generated payload
  manifest evidence.
- Claude Code's installed plugin state is runtime state, not as the editable
  source of truth.

When source changes, update the marketplace source or generated payload, then
refresh the marketplace or reinstall the plugin. Do not edit installed runtime
state to try to patch a stale install.

The detailed source and file-layout reference belongs in
[DOC-007 reference](/racecraft-plugins-public/reference/).

## Install Path Matrix

Use this accessible matrix to pick the next task. The headers identify the
install context, marketplace source, payload source of truth, and when to use
each flow.

| Context | Marketplace source | Payload to install | Use when |
|---|---|---|---|
| Racecraft marketplace entry | `.claude-plugin/marketplace.json` | `./dist/claude/speckit-pro` from this repository | You want Claude Code to install SpecKit Pro from the Racecraft marketplace. |
| Repository source inspection | `racecraft-lab/racecraft-plugins-public` | The generated Claude payload under `dist/claude/speckit-pro/` | You need to compare source files, generated payload files, and installed plugin behavior. |
| Managed marketplace source | Organization-managed Claude Code settings | The marketplace and plugin payload approved by policy | Your Claude Code environment restricts marketplace sources, hooks, MCP, or plugin settings. |

## Compact Install Path List

- **Marketplace install:** add the Racecraft marketplace, install
  `speckit-pro@racecraft-plugins-public`, then reload plugins.
- **Repository source inspection:** inspect `speckit-pro/`,
  `.claude-plugin/marketplace.json`, and `dist/claude/speckit-pro/` before
  comparing installed behavior.
- **Managed install:** confirm the approved marketplace source and policy
  settings before attempting install, reload, hook, or MCP troubleshooting.

## Install From A Marketplace Entry

Claude Code plugin marketplace command group, Racecraft marketplace source:

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-plugins-public
/reload-plugins
/plugin
```

Expected signal: Claude Code adds the Racecraft marketplace, installs
`speckit-pro`, reloads plugin components, and shows the plugin in the installed
plugin view.

Repo-scoped Claude Code marketplace context:

- Open this repository in Claude Code.
- Use the checked-in `.claude-plugin/marketplace.json` marketplace.
- Confirm the `speckit-pro` entry uses `source.path`:

```text
./dist/claude/speckit-pro
```

Expected signal: `speckit-pro` appears in the installed plugin view, and the
plugin details show the skills, agents, hooks, plugin MCP servers, or plugin
LSP servers Claude Code loaded from the payload when present.

Managed or policy-controlled Claude Code marketplace context:

- Confirm the Racecraft marketplace source is approved by managed settings.
- Confirm plugin install, reload, hooks, MCP, and LSP behavior are allowed by
  local or organization policy.
- Refresh the approved marketplace source before expecting source changes to
  appear in the installed plugin.

Lifecycle command group, Claude Code marketplace context:

```text
/plugin marketplace update racecraft-plugins-public
/reload-plugins
/plugin
/plugin uninstall speckit-pro@racecraft-plugins-public
/reload-plugins
/plugin marketplace remove racecraft-plugins-public
/plugin marketplace list
```

Use marketplace update when Claude Code cannot find the expected
`speckit-pro` entry. Use uninstall when you want to remove the plugin while
keeping the Racecraft marketplace available. Use marketplace remove only when
you want Claude Code to remove the marketplace itself and plugins installed from
it.

## Register Custom Agents

Claude Code does not use the Codex custom-agent copy step. Plugin skills,
agents, hooks, plugin MCP servers, and plugin LSP servers are loaded from the
installed Claude Code plugin payload after plugin install and reload.

Keep these three Claude Code surfaces separate:

- Plugin skills use the namespaced slash-command form
  `/speckit-pro:<skill-name>`.
- Plugin agents are part of the Claude Code plugin payload and are surfaced by
  Claude Code after install and reload when available.
- Hook, MCP, LSP, and settings behavior remains governed by Claude Code plugin
  and settings policy.

After installing the plugin, run the Claude Code reload step:

```text
/reload-plugins
```

or:

```text
/plugin
```

The reload and plugin manager views confirm Claude Code loaded plugin-provided
skills, agents, hooks, plugin MCP servers, and plugin LSP servers from the
installed payload. Claude Code does not copy SpecKit Pro TOML custom-agent files
into `~/.codex/agents/` or `.codex/agents/`.

Use this checklist:

1. Install `speckit-pro@racecraft-plugins-public` from the Racecraft
   marketplace.
2. Run `/reload-plugins` after install, uninstall, update, or marketplace
   source changes.
3. Open `/plugin` and inspect the installed plugin detail view.
4. Verify the namespaced skill surface with `/speckit-pro:speckit-status`.
5. Confirm managed settings or local policy before troubleshooting hooks, MCP,
   LSP, or plugin permission behavior.

Expected namespaced plugin skill surfaces:

- `/speckit-pro:grill-me`
- `/speckit-pro:speckit-autopilot`
- `/speckit-pro:speckit-coach`
- `/speckit-pro:speckit-install`
- `/speckit-pro:speckit-prd`
- `/speckit-pro:speckit-resolve-pr`
- `/speckit-pro:speckit-scaffold-spec`
- `/speckit-pro:speckit-status`
- `/speckit-pro:speckit-upgrade`

## Verify The Install

After plugin install and reload, use observational verification only. Do not
edit installed runtime state as part of DOC-003 verification.

1. Review the `/plugin` installed plugin detail view for loaded components.
2. Confirm `speckit-pro` is installed from `racecraft-plugins-public`.
3. Confirm the installed plugin points back to the generated Claude payload
   referenced by the marketplace.
4. Confirm `/speckit-pro:speckit-status` responds from the namespaced skill
   surface.
5. Confirm `/speckit-pro:speckit-coach walk me through SDD` responds with
   Spec-Driven Development coaching or asks for needed context.
6. Reload plugins after plugin enablement changes, marketplace updates, or
   settings edits that affect plugin state.

Rerun `/plugin marketplace update racecraft-plugins-public`, reinstall or
refresh `speckit-pro`, and reload plugins after a plugin update when marketplace
metadata, generated payload files, hook configuration, agents, skills, MCP, or
LSP behavior has changed.

The full command-snippet review belongs to the later DOC-003 validation tasks
and the [DOC-007 reference](/racecraft-plugins-public/reference/).

## Stale Update Checkpoint

If SpecKit Pro still looks stale after an update, keep the first check shallow:

- Symptoms can include old skill text, missing namespaced skills, old plugin
  metadata, unchanged hook behavior, a stale marketplace listing, or
  source/payload mismatch.
- Inspect the marketplace source, generated Claude payload directory, installed
  plugin detail view, reload status, and managed settings.
- If the marketplace listing or generated payload is stale, update the
  marketplace source or generated payload, then refresh, reinstall, or reload
  the plugin.
- Rerun `/reload-plugins` after install, update, uninstall, remove, managed
  settings, hook, MCP, or LSP changes.

Do not edit installed runtime state. Use
[DOC-008 troubleshooting](/racecraft-plugins-public/troubleshooting/) for
deeper stale-cache diagnosis, update or remove procedures, rollback, and
permission repair. Use [DOC-007 reference](/racecraft-plugins-public/reference/)
for command, manifest, payload, skill, agent, hook, and file-layout detail.

## Install Safety

Safety warning: Claude Code plugin permissions, managed settings, hooks, MCP,
and LSP policy still apply during plugin installation and reload.

- Git-backed marketplace setup or plugin installation may require network
  access or network approval; network use remains governed by your Claude Code
  settings and any approval prompts.
- Installed plugin runtime state is not the source of truth. Update the
  marketplace source or generated payload instead of editing runtime state.
- Claude Code plugin skills use the namespaced `/speckit-pro:<skill-name>`
  form; install docs should not direct users to older unnamespaced command
  paths.
- Managed marketplace configuration can restrict which plugin sources are
  available. Confirm approved marketplace sources before treating missing plugin
  listings as cache or payload defects.
- SpecKit Pro's generated Claude payload may include hooks as bundled plugin
  payload configuration. This is not a separate permission grant. Hook behavior
  remains governed by Claude Code settings, managed policy, and configured
  controls.
- External app or MCP authentication, if a future plugin payload uses it, is
  not automatic. It remains subject to the connected service and Claude Code
  approval flow.

DOC-008 owns hook trust analysis, managed policy, external authentication,
permission troubleshooting, update, remove, rollback, and stale-cache forensics.
The full security, trust, hook policy, and install lifecycle belong in
[DOC-008 security and trust](/racecraft-plugins-public/security-and-trust/) and
[DOC-008 troubleshooting](/racecraft-plugins-public/troubleshooting/).

## Source Evidence And Boundaries

This page is grounded in:

- [Claude Code plugin marketplace docs](https://code.claude.com/docs/en/discover-plugins)
- [Claude Code plugin authoring docs](https://code.claude.com/docs/en/plugins)
- [Claude Code settings docs](https://code.claude.com/docs/en/settings)
- Claude Code plugin manager observation through `/plugin`
- Local repository evidence in `.claude-plugin/marketplace.json`
- Local repository evidence in `speckit-pro/.claude-plugin/plugin.json`
- Local repository evidence in
  `dist/claude/speckit-pro/.claude-plugin/plugin.json`
- Local repository evidence in `speckit-pro/skills/`,
  `speckit-pro/agents/`, and `speckit-pro/hooks/hooks.json`

DOC-003 stays bounded to Claude Code first-install guidance. DOC-007 owns
deeper reference content, and DOC-008 owns troubleshooting, update, remove,
rollback, managed-policy, stale-cache forensics, and full trust or security
lifecycle depth.

---
title: "Install: Claude Code"
---

Use this route to add the Racecraft marketplace to Claude Code, install
SpecKit Pro, reload plugin surfaces, verify the namespaced skills, and manage
the plugin lifecycle.

This page is for Claude Code. Codex users should use the
[Install: Codex route](/racecraft-plugins-public/install/codex/).

## Source Authority

- Claude Code marketplace, install, reload, lifecycle, and trust behavior:
  [Claude Code plugin marketplace docs](https://code.claude.com/docs/en/discover-plugins)
- Claude Code plugin layout and skill behavior:
  [Claude Code plugin authoring docs](https://code.claude.com/docs/en/plugins)
- Claude Code settings, managed marketplaces, scopes, hooks, and MCP policy:
  [Claude Code settings docs](https://code.claude.com/docs/en/settings)
- Racecraft marketplace catalog:
  `.claude-plugin/marketplace.json`
- SpecKit Pro Claude plugin manifest:
  `speckit-pro/.claude-plugin/plugin.json`
- Generated Claude install payload:
  `dist/claude/speckit-pro/`

## First-Time Install

### Add The Racecraft Marketplace

Run this from Claude Code:

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
```

Expected signal: Claude Code adds the marketplace named
`racecraft-plugins-public` so its plugins can appear in `/plugin`.

### Install SpecKit Pro

Install the plugin from the Racecraft marketplace:

```text
/plugin install speckit-pro@racecraft-plugins-public
```

Expected signal: Claude Code installs `speckit-pro` from the Racecraft
marketplace. The repository marketplace entry points Claude Code at
`dist/claude/speckit-pro/`, the generated Claude payload.

### Reload Plugins

Reload after installing so Claude Code picks up the plugin skills, agents,
hooks, and plugin configuration without a full restart:

```text
/reload-plugins
```

Expected signal: Claude Code reports refreshed plugin components. The official
Claude Code docs describe reload output as including counts for plugins, skills,
agents, hooks, plugin MCP servers, and plugin LSP servers when present.

### Confirm Plugin Visibility

Open the plugin manager:

```text
/plugin
```

Expected signal: `speckit-pro` appears in the installed plugin view, and the
plugin details show the components Claude Code will load from the plugin.

Before running SpecKit Pro skills, review the
[trust surface inventory](#trust-surface-inventory) if you need to inspect what
the plugin adds.

### Verify Namespaced Skills

Check project status through the installed Claude Code skill namespace:

```text
/speckit-pro:speckit-status
```

Expected signal: SpecKit Pro responds with project status, archive-sweep state,
or the next recommended SpecKit action.

Run a lightweight coaching check:

```text
/speckit-pro:speckit-coach walk me through SDD
```

Expected signal: SpecKit Pro explains the Spec-Driven Development workflow or
asks for the next context needed to coach the current repository.

Claude Code plugin skills are namespaced by plugin name, so the Claude Code
form is `/speckit-pro:<skill-name>`. Install-facing docs should prefer skill
language over older command-folder wording.

## Lifecycle Management

### Refresh Marketplace Listings

Use this when the Racecraft marketplace may be stale or when Claude Code cannot
find the expected `speckit-pro` listing:

```text
/plugin marketplace update racecraft-plugins-public
```

Then reload plugins:

```text
/reload-plugins
```

Verify again:

```text
/plugin
```

Expected signal: the Racecraft marketplace listing refreshes, and the installed
view or discover view reflects the current `speckit-pro` entry.

### Uninstall SpecKit Pro

Use this when you want to remove SpecKit Pro but keep the Racecraft marketplace
available for future Racecraft plugins:

```text
/plugin uninstall speckit-pro@racecraft-plugins-public
```

Then reload plugins:

```text
/reload-plugins
```

Expected signal: `speckit-pro` no longer appears as an installed plugin, while
`racecraft-plugins-public` remains an added marketplace.

### Remove The Racecraft Marketplace

Use this only when you want to remove the marketplace itself. Claude Code's
marketplace docs state that removing a marketplace also uninstalls plugins
installed from it.

```text
/plugin marketplace remove racecraft-plugins-public
```

Then confirm the marketplace list:

```text
/plugin marketplace list
```

Expected signal: `racecraft-plugins-public` no longer appears in the marketplace
list, and any plugin installed from that marketplace is removed.

### Clean Reinstall

Use this sequence after uninstalling or removing the marketplace:

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
```

```text
/plugin marketplace update racecraft-plugins-public
```

```text
/plugin install speckit-pro@racecraft-plugins-public
```

```text
/reload-plugins
```

```text
/speckit-pro:speckit-status
```

Expected signal: Claude Code can see the Racecraft marketplace, install
`speckit-pro`, reload plugin components, and run the namespaced status skill.

## Basic Recovery

### Wrong Marketplace Source

List configured marketplaces:

```text
/plugin marketplace list
```

If the Racecraft marketplace source is wrong, remove that marketplace entry and
add the GitHub source again:

```text
/plugin marketplace remove racecraft-plugins-public
```

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
```

Stop after one clean retry. If managed policy, permissions, network access, or
undocumented platform behavior appears to be involved, route the issue to the
DOC-008 troubleshooting work instead of expanding this install route.

### Stale Listing Or Missing Plugin

Refresh the Racecraft marketplace:

```text
/plugin marketplace update racecraft-plugins-public
```

Then retry the install:

```text
/plugin install speckit-pro@racecraft-plugins-public
```

Stop if `speckit-pro` is still missing after the refresh and retry. That belongs
in the DOC-008 troubleshooting path.

### Failed Plugin Visibility

Reload and reopen the plugin manager:

```text
/reload-plugins
```

```text
/plugin
```

Use the plugin manager installed and error views to check whether `speckit-pro`
loaded or reported an error. Stop if visibility remains inconclusive after one
reload.

### Missing Namespaced Skills

Reload plugins, then verify both the plugin manager and the status skill:

```text
/reload-plugins
```

```text
/plugin
```

```text
/speckit-pro:speckit-status
```

Stop if the plugin is installed but the namespaced skills still do not appear.
Deep cache, dependency, rollback, or platform-state debugging belongs to
DOC-008.

### Failed Update, Uninstall, Remove, Or Reinstall

For failed marketplace refreshes, uninstall attempts, marketplace removals, or
clean reinstalls, run the relevant lifecycle command once more only after
checking `/plugin` for the current installed or error state.

Do not keep layering retries into this route. Stop when the issue appears tied
to managed policy, permissions, network access, cache clearing, rollback,
incident response, or undocumented platform behavior.

## Trust Surface Inventory

### Marketplace Metadata

Inspect `.claude-plugin/marketplace.json` for the marketplace name,
`racecraft-plugins-public`, and its `speckit-pro` plugin entry. The marketplace
entry names the generated Claude payload source as `./dist/claude/speckit-pro`.

### Plugin Manifest

Inspect `speckit-pro/.claude-plugin/plugin.json` for the SpecKit Pro plugin
name, version, description, author, license, homepage, and repository metadata.
The source manifest is the authoring-side Claude plugin manifest.

### Skills

Inspect `speckit-pro/skills/` for the source skill folders that define the
Claude Code plugin skill surface. After installation and reload, Claude Code
uses the namespaced form `/speckit-pro:<skill-name>` for those plugin skills.

### Agents

Inspect `speckit-pro/agents/` for source agent definitions that the plugin can
make available to Claude Code. The plugin manager details view is the user-facing
place to confirm what the installed plugin contributes.

### Hooks

Inspect `speckit-pro/hooks/hooks.json` for repository-defined hook
configuration. Keep hook claims limited to the official Claude Code hook and
settings documentation plus the checked-in hook file. This page does not claim
that hooks provide sandboxing, isolation, harmlessness, or blocking guarantees.

### Settings And MCP

Inspect official Claude Code settings documentation for user, project, local,
and managed scopes. Managed marketplace behavior, hook restrictions, MCP
controls, and organization policy are Claude Code platform settings, not
Racecraft-specific guarantees.

### Source And Generated Payload Paths

- Authoring source: `speckit-pro/`
- Claude plugin source manifest: `speckit-pro/.claude-plugin/plugin.json`
- Claude skills source: `speckit-pro/skills/`
- Claude agents source: `speckit-pro/agents/`
- Claude hooks source: `speckit-pro/hooks/hooks.json`
- Generated Claude install payload: `dist/claude/speckit-pro/`

Do not treat `dist/claude/speckit-pro/` as the authoring source. It is the
generated install payload referenced by the marketplace.

## Boundaries

- This route does not regenerate payloads, change plugin manifests, bump
  versions, or alter runtime behavior.
- This route does not provide a full troubleshooting matrix, rollback playbook,
  incident response guide, or managed policy design.
- This route does not include install, verification, custom-agent, cache,
  sandbox, approval, or runtime recovery commands for other runtimes.

## Next Step

After the two verification skills respond, continue with the
[source and payload reference](/racecraft-plugins-public/reference/) if you need
to inspect more repository surfaces before running heavier SpecKit Pro workflows.

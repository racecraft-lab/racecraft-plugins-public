---
title: "Update & Rollback"
---

Use this route when a SpecKit Pro install is stale, incorrect, removed, or
needs to return to a known working version. The page documents operator
recovery choices; it does not run commands, grant permissions, mutate local
files, or repair installed plugin state from the browser.

Read the checkpoint first, then decide whether the manual action is appropriate
for your environment. Mutating actions name their side effect before the command
or platform step.

## Recovery Cases

| Case | Platform | Read-only Checkpoint | Manual Operator Action | Expected Side Effect | Reload Or Restart | Source Evidence |
|---|---|---|---|---|---|---|
| Update | Both | Inspect the marketplace source, generated payload path, manifest version, and platform plugin detail view or Codex CLI JSON output. | Side effect: marketplace metadata and installed plugin state may change. Refresh the approved marketplace source and update the installed plugin through the platform. | Platform sees newer marketplace or plugin metadata. | Claude Code: run `/reload-plugins` after plugin changes. Codex: restart after plugin enablement or custom-agent changes. | [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Codex CLI reference](https://developers.openai.com/codex/cli/reference), [manifests](/racecraft-plugins-public/reference/manifests/) |
| Refresh | Both | Compare authoring source, generated payload, marketplace source, and installed runtime state. | Side effect: copied payload or platform plugin state may change. Refresh the generated or copied payload through the owning project flow, then refresh the platform install. | Stale payload files are replaced by source-owned output. | Reload or restart only after the platform plugin state changes. | [source vs dist](/racecraft-plugins-public/reference/source-vs-dist/), [scripts](/racecraft-plugins-public/reference/scripts/) |
| Reinstall | Both | Confirm the plugin is present but still points at stale or incorrect metadata after update/refresh checks. | Side effect: installed plugin state is replaced. Remove or uninstall through the platform, then install again from the approved marketplace source. | Platform recreates installed plugin state from the selected source. | Claude Code: `/reload-plugins`. Codex: restart after reinstall and rerun custom-agent registration if TOML agents changed. | [Claude plugins reference](https://code.claude.com/docs/en/plugins-reference), [Codex plugins](https://developers.openai.com/codex/plugins) |
| Remove | Both | Confirm whether you want to remove the plugin only, the marketplace source, or both. | Side effect: plugin availability or marketplace visibility may be removed. Use the platform remove or uninstall flow for the intended scope. | Plugin commands and skills may disappear until reinstalled. | Reload Claude Code or restart Codex before judging the result. | [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Codex CLI reference](https://developers.openai.com/codex/cli/reference) |
| Rollback | Both | Identify a known marketplace source, Git ref, generated payload path, manifest version, or documented CLI JSON field for the prior working state. | Side effect: installed plugin state may move back to an older source or payload. Point the marketplace or copied payload at the rollback anchor, then reinstall or refresh through the platform. | Platform uses the rollback anchor instead of the newer source. | Reload or restart after platform state changes. | [manifests](/racecraft-plugins-public/reference/manifests/), [source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) |
| Stale payload | Both | Inspect generated payload references for Claude Code and Codex, and compare them with authoring source. | Side effect: generated or copied payload files may change. Regenerate or copy payloads through source-owned maintainer flow, then refresh the platform install. | Payload files align with checked-in source. | Reload or restart after platform install state changes. | [source vs dist](/racecraft-plugins-public/reference/source-vs-dist/), [scripts](/racecraft-plugins-public/reference/scripts/) |
| Stale cache | Both | Confirm marketplace source, generated payload, installed plugin detail, Codex CLI JSON output, reload/restart state, and custom-agent registration before considering cache-specific action. | Side effect: cache-specific actions can remove local runtime state. Do not make direct cache edits, cache deletion, or cache directory removal the default fix; treat them as last-resort manual reset actions only when platform docs or local policy support them. | Runtime state may be rebuilt or unavailable until the plugin is refreshed. | Reload or restart after platform state is rebuilt. | [security and trust](/racecraft-plugins-public/security-and-trust/), [Codex CLI reference](https://developers.openai.com/codex/cli/reference), [Claude plugins reference](https://code.claude.com/docs/en/plugins-reference) |
| Version sync | Both | Compare marketplace manifest, source manifest, generated payload manifest, plugin detail version, and documented CLI JSON fields when available. | Side effect: source-owned metadata or generated payload state may change through maintainer flow. Align the marketplace source or generated payload to the intended manifest version; do not hand-edit installed runtime state. | Version signals match the selected source or payload. | Reload or restart only after platform state changes. | [manifests](/racecraft-plugins-public/reference/manifests/), [source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) |

## Case Notes

### Update

Use update when the approved marketplace source should move forward to newer
metadata or a newer plugin payload.

### Refresh

Use refresh when the source is correct but a generated or copied payload needs
to be made current through the owning project flow.

### Reinstall

Use reinstall when platform state remains stale after source and payload checks.

### Remove

Use remove when the intended recovery is to make the plugin or marketplace
source unavailable before choosing a clean source.

### Rollback

Use rollback when a known source, generated payload, manifest version, or Git
reference is the desired recovery anchor.

### Stale Payload

Use stale payload guidance when generated Claude or Codex payload files lag
behind authoring source or a copied personal payload.

### Stale Cache

Use stale cache guidance only after marketplace, payload, installed-state,
reload/restart, and Codex custom-agent registration checks. Do not make cache
edits or cache deletion the first fix.

### Version Sync

Use version sync when source manifests, generated manifests, marketplace
metadata, and platform-visible versions do not agree.

## Codex Recovery Notes

Keep these Codex surfaces separate:

- Plugin installation loads the bundled plugin skills.
- Marketplace commands manage marketplace sources and plugin entries.
- `@SpecKit Pro -> install` or `$install` copies bundled SpecKit Pro TOML custom
  agent files to the selected Codex agent directory.
- Restarting Codex is needed before changed plugin, config, or custom-agent
  state can be judged reliably.

Use documented CLI JSON output, such as `codex plugin list --json` and
marketplace JSON output, when inspecting installed plugin state. Treat concrete
paths from repository docs, installer reports, or local runtime output as local
runtime evidence unless current OpenAI docs document that exact path.

After a plugin update that changes bundled custom-agent TOML files, run
`@SpecKit Pro -> install` or `$install` as a manual action, approve only the
expected TOML-file write, then restart Codex.

## Claude Code Recovery Notes

Keep these Claude Code surfaces separate:

- Marketplace update and marketplace remove affect available marketplace source.
- Plugin install and uninstall affect the installed plugin entry.
- `/reload-plugins` reloads plugin-provided components after install, update,
  uninstall, or settings changes.
- `/plugin` is the detail view for installed plugin inspection.
- Managed settings may restrict marketplace, hook, MCP, LSP, or permission
  behavior.

If Claude Code docs mention cache-specific recovery, keep that action outside
troubleshooting inspection cells and treat it as a scoped recovery step, not the
default fix.

## Rollback Anchors

A rollback anchor should be source-backed:

- Approved marketplace source
- Git ref or commit reference
- Generated payload path
- Manifest version
- Documented CLI JSON field
- [Source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) or
  [manifests](/racecraft-plugins-public/reference/manifests/) reference evidence

Do not use a manually edited installed cache as a rollback anchor.

## Where To Go Next

- Use [Troubleshooting](/racecraft-plugins-public/troubleshooting/) to match a
  symptom before choosing a recovery action.
- Use [Security & Trust](/racecraft-plugins-public/security-and-trust/) to check
  permission, sandbox, hook, MCP, managed-policy, or cache-boundary claims.
- Use [Install: Claude Code](/racecraft-plugins-public/install/claude-code/) or
  [Install: Codex](/racecraft-plugins-public/install/codex/) for first-install
  platform flows.

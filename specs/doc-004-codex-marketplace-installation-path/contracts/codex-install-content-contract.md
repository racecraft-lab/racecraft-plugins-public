# Contract: Codex install content and command snippets

This contract defines the minimum content and snippet evidence required for
DOC-004 implementation. It is a documentation contract, not a runtime API.

## Required Route Sections

`docs-site/src/content/docs/install/codex.md` must include these sections in a
task-first order:

1. Purpose and audience for the Codex install path.
2. Source vs generated payload vs installed plugin cache distinction.
3. Install path matrix:
   - Repo-scoped marketplace.
   - Personal/local marketplace.
   - CLI marketplace add.
   - Clear table headers/caption when rendered as a table, plus a compact
     list/card alternative if the matrix is too dense for mobile or
     screen-reader navigation.
4. Plugin installation through Codex plugin browser (`codex` then `/plugins`).
5. Custom-agent registration checklist.
6. Expected installer-copied TOML file list.
7. Restart and verification guidance.
8. Bounded stale-after-update checkpoint:
   - What to inspect when the plugin appears stale after update: marketplace
     source, copied personal payload, generated payload, installed plugin cache,
     selected custom-agent destination, and restart state.
   - When to rerun `@SpecKit Pro -> install` or `$install` after bundled
     custom-agent TOML updates, then restart Codex.
   - Observable symptoms such as old skill text, old plugin metadata, unchanged
     custom-agent behavior, stale copied personal payload, or source/payload
     mismatch.
   - Links to DOC-008 for deeper troubleshooting, update/remove, rollback, and
     stale-cache forensics and DOC-007 for reference details.
9. Bounded install-safety block covering sandbox, approvals, network, cache
   source of truth, selected custom-agent destination permissions, bundled
   lifecycle hook configuration, and external app or MCP authentication
   implications only as first-install expectations.
10. Source evidence and deferred DOC-007/DOC-008 boundaries.

## Required README Alignment

`README.md` and `speckit-pro/README.md` must remain concise but include or link
to the same critical invariants:

- Codex repo marketplace: `.agents/plugins/marketplace.json`.
- Installable Codex payload: `dist/codex/speckit-pro/`.
- Do not install Codex from `speckit-pro/`.
- Installed plugin cache is runtime state, not source of truth.
- Run `@SpecKit Pro -> install` or `$install` after plugin install.
- Rerun `@SpecKit Pro -> install` or `$install` after plugin updates that change
  bundled custom-agent TOML files, then restart Codex.
- Restart Codex after plugin enablement, custom-agent install or refresh, or
  relevant config edits.
- Verification uses the nine installer-copied TOML custom-agent files.
- Stale-after-update guidance stays shallow: check marketplace source or copied
  personal payload, generated payload, installed cache, selected custom-agent
  destination, and restart state, then link to DOC-008 or DOC-007 for depth.
- DOC-004 covers first-install safety, including bounded lifecycle hook payload
  awareness; DOC-008 owns deeper trust, update, rollback, hook policy, and
  troubleshooting.

## Accessibility Structure Requirements

The detailed docs-site Codex page must:

- Use semantic heading order for install decisions, custom-agent registration,
  verification, safety, and source evidence.
- Prefer ordered or unordered lists for procedures, TOML inventories, and
  command groups instead of dense prose.
- Use descriptive link text that names the destination or purpose.
- Label command snippets by Codex platform, install scope, and source-of-truth
  context.
- Render safety warnings as visible text; styling, icons, or colors may support
  the warning but must not be the only signal.

## Command And Path Snippet Review Table

Implementation must keep a manual review checklist for every changed or new
Codex command/path snippet. Minimum expected checklist:

| Snippet | Required source evidence | Notes |
|---------|--------------------------|-------|
| `codex` | OpenAI Codex plugin browser docs or local CLI context | Used before `/plugins`. |
| `/plugins` | OpenAI Codex plugin docs | Plugin browser path. |
| `codex plugin marketplace add ./local-marketplace-root` | OpenAI Build plugins docs and local CLI help | Local marketplace source. |
| `codex plugin marketplace add owner/repo` | OpenAI Build plugins docs and local CLI help | GitHub shorthand. |
| `codex plugin marketplace add owner/repo@ref` | OpenAI Build plugins docs and local CLI help | GitHub shorthand with inline ref. |
| `codex plugin marketplace add owner/repo --ref main` | OpenAI Build plugins docs and local CLI help | Pinned Git ref. |
| `codex plugin marketplace add https://github.com/example/plugins.git --sparse .agents/plugins` | OpenAI Build plugins docs and local CLI help | HTTP or HTTPS Git URL plus Git-only sparse path; repeat `--sparse PATH` when more than one sparse path is needed. |
| `codex plugin marketplace add git@github.com:example/plugins.git` | OpenAI Build plugins docs and local CLI help | SSH Git URL source. |
| `codex plugin marketplace add <source> --json` | Local CLI help | Automation output. |
| `.agents/plugins/marketplace.json` | OpenAI Build plugins docs and repo marketplace file | Repo-scoped marketplace. |
| `~/.agents/plugins/marketplace.json` | OpenAI Build plugins docs | Personal marketplace. |
| `dist/codex/speckit-pro/` | Repo marketplace and generated payload manifest | Racecraft installable Codex payload. |
| `~/.codex/plugins/speckit-pro/` | OpenAI Build plugins docs and DOC-004 spec | Example copied personal payload location, not installed cache. |
| `speckit-pro/` | Source tree evidence | Must be labeled authoring source, not install target. |
| `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` | OpenAI Build plugins docs | Installed plugin cache. |
| `@SpecKit Pro -> install` | Local install skill and plugin manifest default prompt | UI invocation. |
| `$install` | Local install skill | Explicit Codex skill invocation. |
| `.codex/agents/` | OpenAI Subagents docs and local install skill | Project-scoped destination override. |
| `~/.codex/agents/` | OpenAI Subagents docs and local install skill | Default destination. |

Every command block that contains these snippets must include nearby text naming
the platform (`Codex`), install scope (`repo-scoped`, `personal/local`, or
`CLI marketplace add`), and whether the snippet is source, generated payload,
installed cache, or custom-agent destination context.

## Custom-Agent Verification List

The docs must list exactly these files as expected installed output:

- `autopilot-fast-helper.toml`
- `phase-executor.toml`
- `clarify-executor.toml`
- `checklist-executor.toml`
- `analyze-executor.toml`
- `implement-executor.toml`
- `codebase-analyst.toml`
- `spec-context-analyst.toml`
- `domain-researcher.toml`

`uat-runbook-author.toml` may be mentioned only as source/package drift if the
copy explicitly says it is not part of DOC-004's expected installed output.

## Forbidden Content

- Do not add Claude Code install steps except as a cross-link to the Claude path.
- Do not document unsupported marketplace source forms.
- Do not tell users to edit the installed plugin cache.
- Do not promise sandbox, approval, network, lifecycle hook, app, MCP, or
  external-service access beyond what Codex policy and user approval allow.
- Do not turn the stale-after-update checkpoint into a symptom decision tree,
  recovery matrix, cache forensics guide, or rollback procedure.
- Do not expand into DOC-007 reference-library depth or DOC-008 troubleshooting,
  update/remove/rollback, managed policy, stale-cache forensics, or full trust
  model.

## Acceptance Checks

- A first-time Codex user can choose repo-scoped, personal/local, or CLI setup
  without reading source files.
- The generated payload warning appears before any personal/local install
  instructions.
- The install skill and restart sequence appears after plugin install.
- The stale-after-update checkpoint names observable symptoms, surfaces to
  inspect, rerun/restart triggers, and DOC-007/DOC-008 next links without
  duplicating deeper troubleshooting.
- Security-minded readers see bounded safety guidance before approving writes
  or network-backed setup.
- Bundled lifecycle hooks are identified as plugin payload configuration, while
  hook trust analysis, policy tuning, and lifecycle security are deferred to
  DOC-008.
- Safety warnings are readable as text and do not rely on callout color or icon
  alone.
- Dense install path comparisons have a mobile-readable or screen-reader-friendly
  alternative.
- All three entry points agree on the same install invariants.

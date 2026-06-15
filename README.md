# Racecraft Plugins Public

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
![Platforms: Claude Code and Codex](https://img.shields.io/badge/platforms-Claude%20Code%20%2B%20Codex-blue)
![Marketplace: public](https://img.shields.io/badge/marketplace-public-lightgrey)

Racecraft Plugins Public is the open-source plugin marketplace from
[Racecraft Lab](https://github.com/racecraft-lab). It currently publishes
[SpecKit Pro](./speckit-pro/README.md) for both Claude Code and Codex.

The short version: install this marketplace if you want Racecraft-maintained
agent workflows you can inspect, version, and update through your coding-agent
plugin system.

> **Trust check:** Plugins can change how an agent reads files, writes files,
> launches tools, or delegates work. Review the plugin README and source before
> installing or updating.

## Should I Install This?

| You are... | Install if... | Skip for now if... |
|---|---|---|
| Evaluating Racecraft plugins | You want to inspect and install public Racecraft plugins from one place. | You only need a one-off prompt or local personal workflow. |
| Using Spec-Driven Development | You want a guided Spec Kit workflow with scoping, planning, gates, and implementation support. | Your change is tiny enough for a direct manual edit. |
| Maintaining plugins | You want examples of dual Claude Code and Codex plugin packaging. | You do not need marketplace distribution or generated payloads. |

## Available Plugins

| Plugin | What it does | Best first step |
|---|---|---|
| [SpecKit Pro](./speckit-pro/README.md) | Adds Racecraft workflows around GitHub Spec Kit: coaching, scoping interviews, spec scaffolding, autopilot execution, status, and PR review resolution. | Read the [SpecKit Pro decision guide](./speckit-pro/README.md#should-i-install-speckit-pro). |

## Install The Marketplace

This repository exposes the same marketplace through two runtime surfaces:

| Runtime | Marketplace metadata | Install payload |
|---|---|---|
| Claude Code | [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) | [`dist/claude/speckit-pro`](./dist/claude/speckit-pro/) |
| Codex | [`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json) | [`dist/codex/speckit-pro`](./dist/codex/speckit-pro/) |

### Claude Code

Add the marketplace, then install the plugin:

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-plugins-public
/reload-plugins
```

Verify the installed plugin from Claude Code's `/plugin` UI, then use
namespaced plugin skills such as `/speckit-pro:speckit-status` and
`/speckit-pro:speckit-coach`.

### Codex

Claude Code commands are the separate DOC-003-owned path; use the
[Claude Code install guide](./docs-site/src/content/docs/install/claude-code.md)
for that runtime. For Codex, open this repository in Codex, then open the plugin
directory:

```text
codex
/plugins
```

Codex reads the repo-scoped marketplace from
[`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json). That
marketplace points SpecKit Pro at the generated Codex payload,
[`dist/codex/speckit-pro/`](./dist/codex/speckit-pro/). Do not install Codex
from the mixed authoring tree at [`speckit-pro/`](./speckit-pro/).

After installing SpecKit Pro, run the plugin's Codex install skill so its
bundled custom-agent TOML files are copied into Codex's agent registry:

```text
@SpecKit Pro -> install
```

or:

```text
$install
```

The default destination is `~/.codex/agents/`; choose `.codex/agents/` only when
you intentionally want project-scoped custom agents. Verify these nine
installer-copied TOML files only:

- `autopilot-fast-helper.toml`
- `phase-executor.toml`
- `clarify-executor.toml`
- `checklist-executor.toml`
- `analyze-executor.toml`
- `implement-executor.toml`
- `codebase-analyst.toml`
- `spec-context-analyst.toml`
- `domain-researcher.toml`

Then restart Codex. Also restart Codex after plugin enablement changes,
custom-agent refreshes, or relevant Codex config edits.

Codex loads installed plugins from the installed plugin cache at
`~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`. Treat that as
runtime state, not the source of truth. If SpecKit Pro looks stale after an
update, check the marketplace source or copied personal payload, the generated
payload, the installed plugin cache, the selected custom-agent destination, and
whether Codex was restarted. Rerun `@SpecKit Pro -> install` or `$install` after
a plugin update that changes bundled custom-agent TOML files, then restart
Codex again. Do not edit the installed plugin cache.

Install safety stays bounded here: Codex sandbox, approval, and network policy
still apply. Git-backed marketplace setup can require network access or network
approval. Writing to `~/.codex/agents/` is outside most project workspaces, so
approve only the expected local write of the named SpecKit Pro TOML files, or
rerun with `.codex/agents/` or narrower permissions. The generated Codex payload
can include lifecycle hook configuration such as `codex-hooks.json`; hook
behavior remains governed by Codex sandbox, approval, hook trust, and configured
policy controls.

For personal Codex installs, follow the official local-plugin layout: copy or
sync the generated Codex payload, then point
`~/.agents/plugins/marketplace.json` at that copied payload, not the mixed
authoring tree:

```text
dist/codex/speckit-pro/
```

For deeper Codex file-layout details, use the
[DOC-007 reference shell](./docs-site/src/content/docs/reference.md). For
trust, hook policy, update, rollback, permission repair, and stale-cache
forensics, use the
[DOC-008 security and trust](./docs-site/src/content/docs/security-and-trust.md)
and [DOC-008 troubleshooting](./docs-site/src/content/docs/troubleshooting.md)
shells.

## How This Repo Is Organized

| Path | Purpose | Edit directly? |
|---|---|---|
| [`speckit-pro/`](./speckit-pro/) | Source of truth for SpecKit Pro across Claude Code and Codex. | Yes |
| [`dist/claude/speckit-pro/`](./dist/claude/speckit-pro/) | Generated Claude Code install payload. | No, regenerate |
| [`dist/codex/speckit-pro/`](./dist/codex/speckit-pro/) | Generated Codex install payload. | No, regenerate |
| [`tests/speckit-pro/`](./tests/speckit-pro/) | Shell test suite for structure, scripts, tool scoping, and generated payloads. | Yes |
| [`scripts/build-plugin-payloads.sh`](./scripts/build-plugin-payloads.sh) | Rebuilds platform-specific payloads from source. | Yes |

## Contributor Path

Use this lane when changing documentation, skills, agents, hooks, scripts, or
marketplace packaging.

1. Edit source files under `speckit-pro/` or this root README.
2. Rebuild generated install payloads:

   ```bash
   bash scripts/build-plugin-payloads.sh
   ```

3. Run the default validation suite:

   ```bash
   bash tests/speckit-pro/run-all.sh
   ```

4. For structural-only changes, this narrower check is useful while iterating:

   ```bash
   bash tests/speckit-pro/run-all.sh --layer 1
   ```

5. Open a PR with a Conventional Commit title, for example:

   ```text
   docs(speckit-pro): clarify plugin install paths
   ```

### What Not To Edit Directly

- Do not hand-edit `dist/**` payload files except to inspect a generated result.
  Regenerate them from source.
- Do not install `speckit-pro/` directly as a Codex personal plugin. Use
  `dist/codex/speckit-pro/`.
- Do not change marketplace versions manually as part of normal docs work.
  Release automation owns version synchronization.

## Official Platform Docs

The README install and packaging guidance is grounded in these official docs:

| Platform | Docs |
|---|---|
| Claude Code | [Create plugins](https://code.claude.com/docs/en/plugins), [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Plugins reference](https://code.claude.com/docs/en/plugins-reference) |
| Codex | [Plugins](https://developers.openai.com/codex/plugins), [Build plugins](https://developers.openai.com/codex/plugins/build), [Skills](https://developers.openai.com/codex/skills), [Subagents](https://developers.openai.com/codex/subagents) |
| Spec Kit | [Docs](https://github.github.io/spec-kit/), [Installation](https://github.github.io/spec-kit/installation.html), [Quick start](https://github.github.io/spec-kit/quickstart.html), [GitHub repo](https://github.com/github/spec-kit) |

Repo-specific behavior is grounded in the checked-in manifests, payload builder,
tests, and plugin source.

## License

This repository is licensed under the [MIT License](./LICENSE). See each plugin
README for plugin-specific details.

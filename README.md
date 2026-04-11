# Racecraft Plugins for Claude Code and Codex

A curated directory of open-source plugins from [Racecraft Lab](https://github.com/racecraft-lab) for both Claude Code and Codex.

> **⚠️ Important:** Make sure you trust a plugin before installing, updating, or using it. Racecraft Lab maintains these plugins but cannot guarantee they will work in all environments or that they won't change. See each plugin's README for more information.

## Structure

- **`/speckit-pro`** - Autonomous Spec-Driven Development powered by GitHub SpecKit

## Installation

This repository ships both plugin surfaces:

- Claude Code marketplace metadata in [`.claude-plugin/marketplace.json`](/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.claude-plugin/marketplace.json)
- Codex marketplace metadata in [`.agents/plugins/marketplace.json`](/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.agents/plugins/marketplace.json)

### Claude Code

Add the marketplace:

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
```

Install the plugin:

```text
/plugin install speckit-pro@racecraft-plugins-public
```

You can also browse it in `/plugin > Discover`.

### Codex

For repo-scoped Codex installs, open this repository in Codex and use the built-in plugin directory:

```text
codex
/plugins
```

Codex reads the repo marketplace from [`.agents/plugins/marketplace.json`](/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.agents/plugins/marketplace.json).

For personal installs, follow the official Codex plugin docs: copy the plugin to `~/.codex/plugins/<plugin-name>`, point `~/.agents/plugins/marketplace.json` at that directory with a `./`-prefixed relative path, then restart Codex. Official references:

- [Codex plugins](https://developers.openai.com/codex/plugins)
- [Install a local plugin manually](https://developers.openai.com/codex/plugins/build#install-a-local-plugin-manually)
- [Marketplace metadata](https://developers.openai.com/codex/plugins/build#marketplace-metadata)

## Contributing

We welcome contributions from the community. See each plugin's README for details on its structure and requirements.

To submit a new plugin or improve an existing one:

1. Fork this repository
2. Create your plugin following the [standard structure](#plugin-structure)
3. Add your plugin to `.claude-plugin/marketplace.json` for Claude Code and `.agents/plugins/marketplace.json` for Codex
4. Submit a pull request

Pull request titles must follow [Conventional Commits](https://www.conventionalcommits.org/) format (e.g., `feat(plugin-name): add new feature`). This drives automated versioning via [release-please](https://github.com/googleapis/release-please).

## Plugin Structure

Each plugin follows a cross-platform structure:

```
plugin-name/
├── .codex-plugin/
│   └── plugin.json      # Codex plugin metadata (required for Codex)
├── .claude-plugin/
│   └── plugin.json      # Claude Code plugin metadata (required for Claude Code)
├── commands/            # Slash commands (optional)
├── codex-skills/        # Codex skill entrypoints (optional)
├── agents/              # Agent definitions (optional)
├── skills/              # Skill definitions (optional)
├── hooks/               # Event hooks (optional)
├── tests/               # Plugin test suite (optional)
└── README.md            # Documentation
```

## License

This repository is licensed under the [MIT License](./LICENSE). See each plugin's README for additional details.

## Documentation

For more information on developing plugins for each platform:

- [Claude Code plugin docs](https://code.claude.com/docs/en/plugins)
- [Codex plugin docs](https://developers.openai.com/codex/plugins/build)

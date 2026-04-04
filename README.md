# Racecraft Plugins for Claude Code

A curated directory of open-source plugins for Claude Code from [Racecraft Lab](https://github.com/racecraft-lab).

> **⚠️ Important:** Make sure you trust a plugin before installing, updating, or using it. Racecraft Lab maintains these plugins but cannot guarantee they will work in all environments or that they won't change. See each plugin's README for more information.

## Structure

- **`/speckit-pro`** - Autonomous Spec-Driven Development powered by GitHub SpecKit

## Installation

Plugins can be installed directly from this marketplace via Claude Code's plugin system.

To add the marketplace, run `/plugin marketplace add racecraft-lab/racecraft-plugins-public`

To install, run `/plugin install speckit-pro@racecraft-public-plugins`

or browse for the plugin in `/plugin > Discover`

## Contributing

We welcome contributions from the community. See each plugin's README for details on its structure and requirements.

To submit a new plugin or improve an existing one:

1. Fork this repository
2. Create your plugin following the [standard structure](#plugin-structure)
3. Add your plugin to `.claude-plugin/marketplace.json`
4. Submit a pull request

Pull request titles must follow [Conventional Commits](https://www.conventionalcommits.org/) format (e.g., `feat(plugin-name): add new feature`). This drives automated versioning via [release-please](https://github.com/googleapis/release-please).

## Plugin Structure

Each plugin follows a standard structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (required)
├── commands/            # Slash commands (optional)
├── agents/              # Agent definitions (optional)
├── skills/              # Skill definitions (optional)
├── hooks/               # Event hooks (optional)
├── tests/               # Plugin test suite (optional)
└── README.md            # Documentation
```

## License

This repository is licensed under the [MIT License](./LICENSE). See each plugin's README for additional details.

## Documentation

For more information on developing Claude Code plugins, see the [official documentation](https://code.claude.com/docs/en/plugins).

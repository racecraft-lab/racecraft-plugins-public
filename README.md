# Racecraft Public Plugins

Public Claude Code plugins for spec-driven development and AI-assisted workflows.

## Installation

### Add as Marketplace

```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
```

### Install Individual Plugins

```bash
/plugin install speckit-pro@racecraft-public-plugins
```

## Available Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| `speckit-pro` | 1.0.0 | Autonomous Spec-Driven Development powered by GitHub SpecKit |

## Available Commands

| Command | Description |
|---------|-------------|
| `/speckit-pro:setup <SPEC-ID>` | Prepare a spec for autopilot execution |
| `/speckit-pro:autopilot <workflow.md>` | Autonomous 7-phase SDD workflow execution |
| `/speckit-pro:coach` | SDD methodology coaching and guidance |
| `/speckit-pro:status [SPEC-ID]` | Project roadmap and phase progress |
| `/speckit-pro:resolve-pr <PR>` | Address GitHub PR review comments |

## Updating

After making changes:

```bash
git add . && git commit -m "Description" && git push
```

Then in Claude Code:

```
/plugin marketplace update racecraft-public-plugins
```

## Adding New Plugins

1. Create a new directory: `mkdir new-plugin-name`
2. Add the plugin structure:
   ```
   new-plugin-name/
   ├── .claude-plugin/
   │   └── plugin.json
   ├── commands/
   ├── skills/
   ├── agents/
   └── README.md
   ```
3. Update `.claude-plugin/marketplace.json` to include the new plugin
4. Commit and push

## Structure

```
racecraft-plugins-public/
├── .claude-plugin/
│   └── marketplace.json      ← Marketplace registry
├── speckit-pro/               ← speckit-pro plugin (v1.0.0)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/
│   ├── commands/
│   ├── hooks/
│   ├── skills/
│   │   ├── speckit-autopilot/
│   │   └── speckit-coach/
│   ├── tests/
│   └── README.md
└── [future-plugins]/
```

# Racecraft Local Plugins

Private Claude Code plugins for Racecraft productivity and planning workflows.

## Installation

### Add as Local Marketplace

From GitHub:

```bash
/plugin marketplace add fgabelmannjr/claude-plugins
```

### Install Individual Plugins

```bash
/plugin install racecraft@racecraft-local-plugins
```

## Available Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| `racecraft` | 1.1.0 | Weekly planning, status checks, and workflow automation |

## Available Commands

| Command | Description |
|---------|-------------|
| `/racecraft:check` | Quick 5-minute status check |
| `/racecraft:plan` | Full weekly planning session |

## Available Subagents

| Agent | Purpose |
|-------|---------|
| `asana-collector` | Gathers Asana task data |
| `calendar-collector` | Gathers calendar events |
| `vault-collector` | Gathers Obsidian vault context |

## Updating

After making changes:

```bash
git add . && git commit -m "Description" && git push
```

Then in Claude Code:

```
/plugin marketplace update racecraft-local-plugins
```

## Adding New Plugins

1. Create a new directory: `mkdir new-plugin-name`
2. Add the plugin structure:
   ```
   new-plugin-name/
   ├── .claude-plugin/
   │   └── plugin.json
   ├── skills/
   ├── agents/
   └── README.md
   ```
3. Update `.claude-plugin/marketplace.json` to include the new plugin
4. Commit and push

## Structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json      ← Marketplace registry
├── racecraft/                 ← Racecraft plugin (v1.1.0)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/
│   │   ├── asana-collector.md
│   │   ├── calendar-collector.md
│   │   └── vault-collector.md
│   ├── skills/
│   │   ├── check/
│   │   │   └── SKILL.md
│   │   └── plan/
│   │       ├── SKILL.md
│   │       └── templates/
│   │           └── weekly-plan.md
│   └── README.md
└── [future-plugins]/
```

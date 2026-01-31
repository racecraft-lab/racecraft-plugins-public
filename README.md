# Racecraft Local Plugins

Private Claude Code plugins for Racecraft productivity and planning workflows.

## Installation

### Add as Local Marketplace

```bash
/plugin marketplace add /Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/claude-plugins
```

Or from GitHub (after pushing):

```bash
/plugin marketplace add fredrickgabelmann/claude-plugins
```

### Install Individual Plugins

```bash
/plugin install racecraft-weekly-planning@racecraft-local-plugins
```

## Available Plugins

| Plugin | Description |
|--------|-------------|
| `racecraft-weekly-planning` | Weekly planning across E84, Inbanx, Racecraft, Personal, and Family calendars |

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
├── racecraft-weekly-planning/ ← Plugin 1
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/
│   ├── skills/
│   └── README.md
└── [future-plugins]/          ← Add more here
```

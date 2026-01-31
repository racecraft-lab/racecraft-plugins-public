# Racecraft Local Plugins

Private Claude Code plugins for Racecraft productivity, planning, and competitor intelligence workflows.

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
| `racecraft` | 2.0.0 | Weekly planning, reviews, competitor intelligence, and workflow automation with subagent architecture |

## Available Commands

| Command | Duration | Description |
|---------|----------|-------------|
| `/racecraft:check` | 5 min | Quick status check |
| `/racecraft:weekly-plan` | 90-120 min | Full weekly planning session |
| `/racecraft:weekly-review` | 90 min | Full weekly review with competitor intel |
| `/racecraft:weekly-technical` | 30 min | Technical review only (no intel) |
| `/racecraft:intel` | 45 min | Standalone competitor intelligence scan |
| `/racecraft:monthly-review` | 45 min | End-of-month strategy review |
| `/racecraft:quarterly-review` | 60 min | End-of-quarter strategic review |

## Available Subagents

| Agent | Purpose |
|-------|---------|
| `asana-collector` | Gathers Asana task data |
| `calendar-collector` | Gathers calendar events |
| `vault-collector` | Gathers Obsidian vault context |
| `feedly-scanner` | Chrome automation for Feedly competitor intel |

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
   ├── commands/
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
├── racecraft/                 ← Racecraft plugin (v2.0.0)
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/
│   │   ├── asana-collector.md
│   │   ├── calendar-collector.md
│   │   ├── vault-collector.md
│   │   └── feedly-scanner.md
│   ├── commands/
│   │   ├── check.md
│   │   ├── weekly-plan.md
│   │   ├── weekly-review.md
│   │   ├── weekly-technical.md
│   │   ├── intel.md
│   │   ├── monthly-review.md
│   │   └── quarterly-review.md
│   ├── skills/
│   │   ├── check/
│   │   │   └── SKILL.md
│   │   ├── weekly-plan/
│   │   │   ├── SKILL.md
│   │   │   └── templates/
│   │   ├── weekly-review/
│   │   │   ├── SKILL.md
│   │   │   └── templates/
│   │   ├── weekly-technical/
│   │   │   └── SKILL.md
│   │   ├── intel/
│   │   │   └── SKILL.md
│   │   ├── monthly-review/
│   │   │   ├── SKILL.md
│   │   │   └── templates/
│   │   └── quarterly-review/
│   │       ├── SKILL.md
│   │       └── templates/
│   └── README.md
└── [future-plugins]/
```

## Version History

- **2.0.0** (2026-01-31): Weekly review + competitor intelligence + quarterly
  - Renamed commands for consistency (weekly-plan, weekly-review, etc.)
  - Added weekly-review, weekly-technical, intel, monthly-review commands
  - Added quarterly-review for end-of-quarter strategic planning
  - Added feedly-scanner agent with Chrome automation
  - Ideaverse Pro aligned templates
  - Subagent architecture for parallel data gathering

- **1.2.0**: Enhanced subagents
- **1.0.0**: Initial release

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A **Claude Code plugin marketplace** containing public plugins for spec-driven development. Plugins are installed via:
```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-public-plugins
```

After making changes, publish with:
```bash
git add . && git commit -m "Description" && git push
# Then in Claude Code:
/plugin marketplace update racecraft-public-plugins
```

## Plugin Architecture

Each plugin lives in its own top-level directory with this structure:
```
plugin-name/
├── .claude-plugin/plugin.json   ← Manifest (name, version, description, author)
├── agents/                      ← Subagent definitions (.md files)
├── commands/                    ← Slash commands (.md files with YAML frontmatter)
├── hooks/hooks.json             ← Event hooks (SessionStart, etc.)
├── skills/                      ← Skills with SKILL.md + optional references/ and scripts/
└── tests/                       ← 5-layer test suite
```

The marketplace registry is at `.claude-plugin/marketplace.json`. Adding a new plugin requires updating this file.

### Command File Format
Commands must have YAML frontmatter (`---`) with `description:` and `allowed-tools:` fields, followed by body content. No frontmatter = test failure.

### Skill Structure
Skills live under `skills/<skill-name>/` with a `SKILL.md` entry point. Supporting reference docs go in `references/` and shell scripts in `scripts/`.

## Running Tests

All tests are shell scripts. Run from the `speckit-pro/` directory:

```bash
# Default: Layers 1, 4, 5 (fast, deterministic)
bash tests/run-all.sh

# With live SpecKit project tests
bash tests/run-all.sh --live

# Single layer
bash tests/run-all.sh --layer 1   # Structural validation
bash tests/run-all.sh --layer 4   # Script unit tests
bash tests/run-all.sh --layer 5   # Agent tool scoping

# Layers 2 & 3 (AI evals — require skill-creator plugin and claude -p)
bash tests/layer2-trigger/run-trigger-evals.sh speckit-coach
bash tests/layer2-trigger/run-trigger-evals.sh speckit-autopilot
```

### Test Layers
| Layer | What it tests | Cost |
|-------|---------------|------|
| 1 – Structural | File existence, JSON validity, frontmatter format | Fast |
| 2 – Trigger | Skill trigger accuracy via eval harness | Slow (AI) |
| 3 – Functional | End-to-end skill behavior evals | Slow (AI) |
| 4 – Script unit | Shell script logic (validate-gate, detect-commands, etc.) | Fast |
| 5 – Tool scoping | Agent tool list restrictions | Fast |

Layer 2/3 evals require `skill-creator` plugin at `$SKILL_CREATOR_ROOT` (default: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator`).

## speckit-pro Plugin

The only current plugin. It implements Spec-Driven Development (SDD) powered by [GitHub SpecKit](https://github.com/github/spec-kit).

**Key dependency:** The `specify` CLI must be installed for the plugin to function:
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

The SessionStart hook warns if `specify` is not found.

**Commands:** `setup`, `autopilot`, `coach`, `status`, `resolve-pr`

**Skills:**
- `speckit-autopilot` — Autonomous 7-phase SDD workflow executor with multi-agent consensus. References in `references/` cover gate validation, consensus protocol, phase execution, TDD protocol, and post-implementation steps.
- `speckit-coach` — SDD methodology coaching. References cover command guide, constitution guide, presets/extensions, checklist domains, best practices, and getting-started templates.

## Active Technologies
- Bash (macOS/Linux) + jq (JSON processing), release-please (Google, version automation) (001-repository-foundation)
- YAML (GitHub Actions workflow syntax) + Bash (inline sync step) + `googleapis/release-please-action@v4`, `actions/checkout@v4`, `jq` (pre-installed on `ubuntu-latest`) (003-release-automation)
- N/A (git-managed config files only) (003-release-automation)

## Recent Changes
- 001-repository-foundation: Added Bash (macOS/Linux) + jq (JSON processing), release-please (Google, version automation)

# Copilot Instructions

## What This Repository Is

A **Claude Code plugin marketplace**. Plugins are installed by end-users via:
```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-public-plugins
```

There is no compiled build step. The repository is pure Bash + Markdown.

---

## Testing

All tests are shell scripts. Run from the **`speckit-pro/` directory**:

```bash
# Default: Layers 1, 4, 5 (fast, deterministic — run these during development)
bash tests/run-all.sh

# Single layer (fastest during development)
bash tests/run-all.sh --layer 1   # Structural: file existence, JSON, frontmatter
bash tests/run-all.sh --layer 4   # Script unit tests (validate-gate, detect-commands, etc.)
bash tests/run-all.sh --layer 5   # Agent tool scoping

# Run a single layer-4 test directly
bash tests/layer4-scripts/test-validate-gate.sh

# Layers 2 & 3 require skill-creator plugin + claude -p (slow, AI-based — run manually)
bash tests/layer2-trigger/run-trigger-evals.sh speckit-coach
bash tests/layer2-trigger/run-trigger-evals.sh speckit-autopilot
```

During development, prefer the smallest relevant layer (e.g., layer 4 when editing a script, layer 1 when adding a command file).

---

## Plugin Architecture

Each plugin lives in a top-level directory with this structure:

```
plugin-name/
├── .claude-plugin/plugin.json       ← Manifest (name, version, description, author)
├── commands/                        ← Slash commands (.md with YAML frontmatter)
├── agents/                          ← Sub-agent definitions (.md with YAML frontmatter)
├── hooks/hooks.json                 ← Event hooks (e.g., SessionStart)
├── skills/
│   └── skill-name/
│       ├── SKILL.md                 ← Entry point (required)
│       ├── references/              ← Supporting reference docs
│       ├── scripts/                 ← Helper shell scripts
│       └── templates/               ← Workflow/plan templates
└── tests/                           ← 5-layer test suite
```

The marketplace registry lives at `.claude-plugin/marketplace.json` (root-level). **Adding a new plugin requires updating this file.**

---

## Key Conventions

### Command Files

Every file in `commands/` **must** have YAML frontmatter with both `description:` and `allowed-tools:` fields — missing frontmatter causes a Layer 1 test failure:

```markdown
---
description: One-line description of what this command does
allowed-tools:
  - Read
  - Bash
---

Command body content here.
```

### Agent Files

Every file in `agents/` must have YAML frontmatter with `name:`, `description:`, `model:`, `tools:`, and `permissionMode:`.

### SKILL.md Files

Every skill's `SKILL.md` must have frontmatter including `name:`, `description:`, and `user-invokable:`.

### Shell Scripts

All scripts use:
```bash
#!/usr/bin/env bash
set -euo pipefail
```

Scripts that are referenced by agents or hooks must be **executable** (`chmod +x`). Layer 1 validates this.

### Naming

- Plugin/skill directories: `kebab-case`
- Shell script variables: `snake_case`
- Conventional Commits for git messages: `feat(skills):`, `fix(agents):`, `chore(evals):`

---

## speckit-pro Plugin Architecture

The only current plugin. It implements Spec-Driven Development (SDD) using the `specify` CLI.

**External dependency** — the `specify` CLI must be installed:
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

The `SessionStart` hook warns automatically if `specify` is missing.

### Two-Skill Design

**`speckit-autopilot`** (`skills/speckit-autopilot/SKILL.md`, 737 lines): The orchestration engine. Runs the full 7-phase SDD workflow (specify → clarify → plan → checklist → tasks → analyze → implement) with programmatic gate validation between phases. Spawns sub-agents directly (foreground) — sub-agents cannot nest further.

**`speckit-coach`** (`skills/speckit-coach/SKILL.md`, 299 lines): Methodology coaching. Routes user questions to the right reference guide. Also handles master plan decomposition for multi-spec projects. Works without `specify` installed.

### Consensus Pattern

When autopilot encounters genuinely ambiguous items, the main session spawns 3 consensus agents **in parallel**, each with a distinct perspective:
- `codebase-analyst` — what existing code patterns suggest
- `spec-context-analyst` — what the project's decisions/principles say
- `domain-researcher` — what industry standards recommend

The main session synthesizes the 3 responses. This is a deliberate **orchestrator-direct** pattern: the main skill stays in the session, sub-agents run in foreground, preventing agent loop termination.

### MCP Tool Usage in Agents

Some agents have optional MCP tools with built-in fallbacks:
- `codebase-analyst`: RepoPrompt MCP preferred, Grep/Read as fallback
- `domain-researcher`: Tavily + Context7 MCP preferred, WebSearch/WebFetch as fallback

Agents function without MCP tools — they degrade gracefully.

### Publishing Changes

After committing and pushing:
```bash
git add . && git commit -m "feat(skills): ..." && git push
# Then in Claude Code:
/plugin marketplace update racecraft-public-plugins
```

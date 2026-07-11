# Copilot Instructions

## What This Repository Is

A **Claude Code and Codex plugin marketplace**. Claude Code plugins are installed
by end-users via:
```bash
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-public-plugins
```

There is no compiled build step. Repository tooling is Python 3.11+
standard-library code; plugin content is primarily Markdown, JSON, and YAML, and
the docs site uses Node and pnpm.

---

## Testing

Run repository tests from the **repository root**. The layer roster and dispatch
mode come from `tests/speckit-pro/suite-manifest.json`; do not maintain a second
suite list in prose.

```text
# Default: toolchain preflight plus Layers 1, 4, and 5
python3 tests/speckit-pro/run-all.py

# Single layer (fastest during development)
python3 tests/speckit-pro/run-all.py --layer 1   # Structural validation
python3 tests/speckit-pro/run-all.py --layer 4   # Unit Tests (tests/speckit-pro/unit)
python3 tests/speckit-pro/run-all.py --layer 5   # Agent tool scoping

# Layer 7 integration fixtures: replay by default, live only when requested
python3 tests/speckit-pro/run-all.py --integration
python3 tests/speckit-pro/run-all.py --integration --live

# Direct toolchain report; use --mode docs or --mode all when relevant
python3 tests/speckit-pro/check-toolchain.py --mode tests
```

`--all` is not a synonym for a larger deterministic gate. It implies live mode,
executes Layers 1, 4, 5, and live Layer 7, prints manual command plans for
live-only Layers 2, 3, and 6, and does not select gate-only Layer 8. During
development, prefer the smallest relevant layer, then run the default suite
before opening a PR.

---

## Plugin Architecture

Each plugin lives in a top-level directory with this structure:

```
plugin-name/
├── .claude-plugin/plugin.json       ← Manifest (name, version, description, author)
├── .codex-plugin/plugin.json        ← Codex manifest
├── commands/                        ← Slash commands (.md with YAML frontmatter)
├── agents/                          ← Sub-agent definitions (.md with YAML frontmatter)
├── hooks/hooks.json                 ← Event hooks (e.g., SessionStart)
├── speckit_pro_runner/              ← Python 3.11+ installed runtime and gates
├── skills/
│   └── skill-name/
│       ├── SKILL.md                 ← Entry point (required)
│       ├── references/              ← Supporting reference docs
│       ├── scripts/                 ← Python helper scripts
│       └── templates/               ← Workflow/plan templates
└── codex-skills/                    ← Codex skill mirrors
```

Repository-only validation lives under `tests/speckit-pro/`, outside the shipped
plugin. The Claude marketplace registry lives at
`.claude-plugin/marketplace.json`; adding a new plugin also requires the matching
Codex marketplace entry under `.agents/plugins/marketplace.json`.

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

### Python Scripts

Repo-owned executable helpers use Python 3.11+ and the standard library:

```python
#!/usr/bin/env python3
```

Use argument arrays with `subprocess` and `shell=False`. Do not add a required
Bash or `jq` dependency to repository tests, release tools, hooks, or shipped
plugin runtime. Workflow YAML may retain bounded shell dispatch glue, and the
tracked `.specify/**` shell files are a fixed vendored allowlist.

### Naming

- Plugin/skill directories: `kebab-case`
- Python modules and identifiers: `snake_case`
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

Open a PR with a Conventional Commit title and public-readable body. A `feat` or
`fix` PR must contain exactly one non-empty fenced `release-note` block unless
the `release-note/skip` label applies. Do not hand-edit generated payloads,
installed-cache proofs, or generated reference pages; run their Python
generator or let the Release workflow synchronize them onto the release PR.

After the release PR is merged and published, Claude Code consumers refresh with
`/plugin marketplace update racecraft-plugins-public`.

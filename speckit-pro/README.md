# speckit-pro

Autonomous Spec-Driven Development plugin for Claude Code and Codex, powered by [GitHub SpecKit](https://github.com/github/spec-kit).

## Overview

speckit-pro turns feature descriptions into production code through a structured workflow: Archive Sweep, then specify, clarify, plan, checklist, tasks, analyze, implement. Instead of writing code directly from a prompt, it builds a complete specification first — catching gaps, validating requirements, and planning implementation before any code is written.

The plugin runs autonomously. You provide a feature description, and it handles the rest — spawning specialized agents for research, running multi-agent consensus to resolve ambiguities, validating gates between phases, and implementing with strict TDD. The result is a PR with tests, implementation, and a full paper trail of design decisions.

Archive-aware runs start by checking for the `archive` extension. When installed
or vendored, autopilot runs Archive Sweep for previously merged specs before the
requested spec's Phase 0, excludes the current target spec, and keeps cleanup
dry-run-only on dirty or unsafe branches.

This plugin ships different entrypoint surfaces for the two platforms:

- **Claude Code** — 2 bundled skills plus 5 `/speckit-pro:*` commands
- **Codex** — 6 bundled skills plus skill-local `agents/openai.yaml` metadata sidecars

## Codex Entry Points

Codex does not load the Anthropic `commands/` files from this repository. In Codex, use the skill-backed entrypoints below:

| Capability | Claude Code | Codex |
| ---------- | ----------- | ----- |
| Coaching | `/speckit-pro:coach` | `/speckit-coach` or `$speckit-coach` |
| Setup | `/speckit-pro:setup` | `/speckit-setup` or `$speckit-setup` |
| Codex agent install / repair | — | `@SpecKit Pro` → `install` or `$install` |
| Autopilot | `/speckit-pro:autopilot` | `/speckit-autopilot` or `$speckit-autopilot` |
| Status | `/speckit-pro:status` | `/speckit-status` or `$speckit-status` |
| Review remediation | `/speckit-pro:resolve-pr` | `/speckit-resolve-pr` or `$speckit-resolve-pr` |

You can also type `@SpecKit Pro` in Codex and then choose the bundled skill you want.

To browse or install plugins in Codex CLI, use `/plugins`, not `/plugin`.

The Codex skills own their local
[`agents/openai.yaml`](./codex-skills/speckit-autopilot/agents/openai.yaml)
metadata sidecars, which is the official Codex skills packaging model. Those
sidecars are metadata only. The official
[Codex subagents](https://developers.openai.com/codex/subagents) docs still
register real custom agents from `.codex/agents/` or `~/.codex/agents/`, so
SpecKit Pro keeps a separate Codex-only `install` skill that copies the bundled
`codex-agents/*.toml` templates into those runtime paths. The built-in
`worker`, `explorer`, and `default` roles remain a degraded fallback, but the
preferred SpecKit Pro path is to run the install skill after plugin install and
restart Codex. See [Installation](#installation) for the exact sequence.

## Claude Code Commands

### `/speckit-pro:coach`

Get SDD methodology coaching and guidance on any aspect of the workflow.

**Usage:**
```
/speckit-pro:coach walk me through SDD
/speckit-pro:coach help me create a technical roadmap
/speckit-pro:coach which checklist domains for a REST API
/speckit-pro:coach the simplicity gate is failing
/speckit-pro:coach how does the consensus protocol work
```

**What it does:**
1. Loads the speckit-coach skill with routing tables and reference material
2. Matches your question to the right topic area
3. Provides guidance grounded in SDD methodology and the SpecKit CLI

**Covers:** Getting started, per-command coaching, constitution design, checklist domain selection, technical roadmap creation, gate failure troubleshooting, autopilot usage, and consensus protocol.

### `/speckit-pro:setup <SPEC-ID>`

Prepare a spec for autopilot execution — creates the worktree, branch, and populated workflow file.

**Usage:**
```
/speckit-pro:setup SPEC-009
```

**What it does:**
1. Finds the technical roadmap in your project
2. Extracts scope, dependencies, and priority for the requested spec
3. Creates a git worktree and pushes the branch to origin
4. Copies the workflow template and populates all phase prompts
5. Commits and pushes — ready for autopilot

**Output:**
```
## Setup Complete

Spec:      SPEC-009 Search & Database
Branch:    009-search-database
Worktree:  .worktrees/009-search-database/
Workflow:  .worktrees/009-search-database/docs/ai/specs/SPEC-009-workflow.md
Remote:    Pushed to origin/009-search-database

Ready to run:
/speckit-pro:autopilot docs/ai/specs/SPEC-009-workflow.md
```

### `/speckit-pro:autopilot <workflow.md>`

Execute the SpecKit workflow autonomously — all 7 phases from spec to PR.

**Usage:**
```
/speckit-pro:autopilot docs/ai/specs/SPEC-009-workflow.md
```

**What it does:**
1. Runs Archive Sweep for previously merged specs and excludes the current target spec
2. Validates prerequisites (SpecKit CLI, constitution, workflow file, MCP servers)
3. Executes all 7 SDD phases sequentially, each delegated to a specialized agent
4. Validates gates programmatically between phases (max 2 auto-fix attempts)
5. Runs multi-agent consensus for ambiguous questions, gaps, and findings
6. Implements with strict TDD red-green-refactor
7. Creates a PR via `gh` CLI when complete

**Example workflow:**
```
# Set up the spec (creates worktree + workflow file)
/speckit-pro:setup SPEC-009

# Review the workflow file — verify prompts have enough context
# Then run the autopilot
/speckit-pro:autopilot docs/ai/specs/SPEC-009-workflow.md

# Claude will:
# - Run Archive Sweep for previously merged specs before Phase 0
# - Run specify → clarify → plan → checklist → tasks → analyze → implement
# - Validate gates between each phase
# - Spawn consensus agents for unresolved items
# - Implement each task with TDD
# - Create a PR when complete
```

### `/speckit-pro:status [SPEC-ID]`

Full project roadmap, phase detail, and next-spec recommendation.

**Usage:**
```
/speckit-pro:status              # Show full roadmap + active specs
/speckit-pro:status all          # Same as above
/speckit-pro:status SPEC-009     # Show specific spec detail
```

**What it does:**
1. Finds all workflow files and the technical roadmap
2. Parses phase completion from workflow files
3. Reads archive extension state when `.specify/extensions/archive` or registry data exists
4. Builds a unified dashboard with completed, in-progress, and pending specs
5. Shows Archive Sweep installation, cleanup safety, and excluded current-spec state when available
6. Recommends the next spec to implement based on priority and dependencies

**Output format:**
```
# SpecKit Project Status

## Summary
- Total specs: 14
- Complete: 3
- In progress: 1
- Remaining: 10

## Recommended Next
SPEC-009: Search & Database (10 tools, P1, Tier 2)
/speckit-pro:setup SPEC-009
```

### `/speckit-pro:resolve-pr <PR>`

Address all GitHub review comments, fix the code, and resolve threads.

**Usage:**
```
/speckit-pro:resolve-pr 42
```

**What it does:**
1. Fetches all review comments on the PR via `gh api`
2. For each unresolved thread, reads the code and applies the fix
3. Commits all fixes in one pass
4. Resolves the review threads
5. Pushes to the PR branch

## Architecture

### Orchestrator-Direct Pattern

The autopilot skill runs in the main session so it can spawn subagents directly — no nesting needed.

- **Codex runtime contract**: orchestration is bound to `spawn_agent` / `wait_agent`, progress is required in `update_plan`, and the same ordered plan is mirrored into `autopilot-state.json` next to the workflow file for resume safety.
- **Claude Code runtime contract**: orchestration stays on the existing Agent/task primitives for Claude sessions.
- **Archive Sweep startup**: before Phase 0, autopilot checks archive extension state, records eligible prior merged specs, excludes the current target, and stays dry-run-only unless cleanup is explicitly safe.
- **Skill-local Codex metadata**: each Codex skill owns `agents/openai.yaml` for display metadata, invocation policy, and tool dependencies.
- **Bundled Codex custom-agent templates**: SpecKit Pro ships `codex-agents/*.toml` in the plugin bundle, but Codex still needs them copied into `.codex/agents/` or `~/.codex/agents/` before they are real spawnable agents.
- **Codex install skill**: use `install` to copy or refresh those bundled templates without touching any Claude-only files.
- **Preferred Codex runtime**: the autopilot uses the installed `phase-executor`, `clarify-executor`, `checklist-executor`, `analyze-executor`, `implement-executor`, `codebase-analyst`, `spec-context-analyst`, and `domain-researcher` agents by name.
- **Fallback roles**: the built-in `worker`, `explorer`, and `default` roles remain available as a degraded fallback when a matching custom agent is unavailable.
- **Simple phases** (specify, plan, tasks): prefer a registered `phase-executor`, otherwise delegate to `worker`
- **Consensus executors** (clarify, checklist, analyze): prefer registered `clarify-executor`, `checklist-executor`, or `analyze-executor` agents, otherwise delegate to `worker`
- **Consensus analysts**: prefer registered `codebase-analyst`, `spec-context-analyst`, and `domain-researcher` agents, otherwise use `explorer` for read-heavy work
- **Optional fast helper**: `autopilot-fast-helper` (`gpt-5.3-codex-spark`, low reasoning, read-only) for near-instant text-only compression, triage, or query drafting. Advisory only; only the top-level autopilot may call it when available.
- **Implementation**: prefer a registered `implement-executor`, otherwise use `worker` with strict TDD, one agent per task

### Consensus Agents

Three perspective agents provide multi-viewpoint resolution for ambiguous questions, specification gaps, and analysis findings:

| Agent | Perspective | Primary Tools |
| ----- | ---------- | ------------- |
| **codebase-analyst** | What does the existing code show? | RepoPrompt or Grep/Glob/Read |
| **spec-context-analyst** | What do project decisions say? | Read (constitution, technical roadmap, prior specs) |
| **domain-researcher** | What do best practices recommend? | Tavily/Context7 or WebSearch/WebFetch |

### Consensus Rules (Moderate Mode — Default)

- **2/3 agree** → Use majority answer
- **3/3 agree** → High confidence, apply automatically
- **All disagree** → Flag for human review
- **Security keywords** (auth, token, secret, PII) → Always flag for human

### Gate Validation

Gates are validated programmatically after each phase using `validate-gate.sh`:

| Gate | Phase | Passes When |
|------|-------|-------------|
| G1 | Specify | spec.md exists, 0 `[NEEDS CLARIFICATION]` markers |
| G2 | Clarify | 0 `[NEEDS CLARIFICATION]` markers in spec.md |
| G3 | Plan | plan.md exists, 0 unresolved markers |
| G4 | Checklist | 0 `[Gap]` markers in spec.md and plan.md |
| G5 | Tasks | tasks.md exists with task entries |
| G6 | Analyze | 0 CRITICAL/HIGH findings remain |
| G7 | Implement | All tasks marked complete |

## Configuration

Create `.claude/speckit-pro.local.md` for per-project settings:

```yaml
---
consensus-mode: moderate    # conservative | moderate | aggressive
gate-failure: stop          # stop | skip-and-log
auto-commit: per-phase      # per-phase | batch | none
---
```

| Setting | Options | Default | Description |
|---------|---------|---------|-------------|
| `consensus-mode` | conservative, moderate, aggressive | moderate | How many agents must agree to auto-apply |
| `gate-failure` | stop, skip-and-log | stop | What happens when a gate fails after 2 auto-fix attempts |
| `auto-commit` | per-phase, batch, none | per-phase | When to commit artifacts during the workflow |

## Best Practices

### When to use speckit-pro

- Features that need clear requirements before implementation
- Multi-spec projects with dependency ordering
- Autonomous overnight implementation runs
- Projects where design decisions need a paper trail
- Teams standardizing their specification workflow

### When not to use speckit-pro

- Quick bug fixes or one-line changes
- Exploratory prototyping where requirements are unknown
- Changes that don't warrant a full specification cycle
- Projects without a constitution (create one first with `/speckit.constitution`)

### Tips

- **Write a constitution first**: The constitution defines your project principles — every spec is validated against it
- **Review workflow prompts before autopilot**: More context in the prompts = better output
- **Start with the coaching entrypoint**: Use `/speckit-pro:coach` in Claude Code or `/speckit-coach` in Codex before running the autopilot
- **Use technical roadmaps for multi-spec projects**: Decompose large features into sequential specs with dependency graphs
- **Trust the gates**: If a gate fails, the spec has a real gap — fix it rather than skipping
- **Run in `acceptEdits` mode**: Plugin agents inherit the parent session's permission mode (see Troubleshooting)

## Prerequisites

- **Claude Code or Codex** — this plugin ships separate entrypoint surfaces for both runtimes
- **SpecKit CLI** — install with: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- **SpecKit initialized** — run: `specify init --ai claude`
- **Constitution created** — run: `/speckit.constitution`
- **GitHub CLI (`gh`)** — required for PR creation and review resolution
- **jq** — required by validation scripts

### Optional MCP Servers

These enhance research quality but are not required — all agents include built-in fallbacks:

| MCP Server | Enhances | Fallback |
|------------|----------|----------|
| Tavily | Web research for consensus agents | WebSearch + WebFetch |
| Context7 | Library documentation lookup | WebSearch for "[library] docs" |
| RepoPrompt | Codebase exploration and analysis | Grep + Glob + Read |

## Troubleshooting

### Autopilot stops after first phase

**Issue:** The agent loop terminates after running one phase.

**Solution:** The autopilot must delegate each phase to a subagent instead of invoking the phase skill in the parent session. In Codex that means `spawn_agent` / `wait_agent`; in Claude Code that means the Agent tool. If it runs a Skill directly, the command's completion report kills the agent loop. This is handled automatically — if you see this, re-run the autopilot.

### Progress plan disappears mid-run

**Issue:** The autopilot loses track of which phase or consensus step is active.

**Solution:** In Codex, the autopilot must recreate the full checklist with `update_plan` before Phase 1, keep exactly one item `in_progress`, and mirror the same ordered plan into `autopilot-state.json` beside the workflow file after every transition. If either store is missing, stop and rebuild both before continuing.

### Permission prompts on every edit

**Issue:** Agents prompt for permission on every file edit, making the autopilot impractical.

**Solution:** Plugin agents cannot set their own `permissionMode` (silently ignored by Claude Code for security). They inherit the parent session's mode. Run Claude Code in `acceptEdits` or `bypassPermissions` mode:
```
claude --permission-mode acceptEdits
```

### MCP tools not available to agents

**Issue:** Agents reference MCP tools (Tavily, Context7, RepoPrompt) but they fail.

**Solution:** Plugin agents cannot declare their own MCP connections. They depend on the parent session having those servers configured. Check with `/mcp`. All agents include fallback tool chains, so functionality is preserved without MCP — just with reduced research quality.

### Gate fails after 2 auto-fix attempts

**Issue:** A gate keeps failing and the autopilot stops.

**Solution:** This means there's a genuine gap in the specification that automated fixes couldn't resolve. Read the gate failure output — it tells you exactly which markers remain and where. Fix the underlying issue in the spec/plan artifact, then re-run the phase.

### SpecKit CLI not found

**Issue:** The prerequisite check reports "SpecKit CLI not found."

**Solution:** Install it:
```
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

### Consensus agents disagree on everything

**Issue:** All 3 consensus agents return different answers, flagging everything for human review.

**Solution:** This usually means the question is genuinely ambiguous. The agents are working correctly — they have different perspectives by design. Review the flagged items and make a decision. Consider adding the decision to your constitution so future specs don't hit the same ambiguity.

### Workflow file has unfilled placeholders

**Issue:** The autopilot fails because workflow prompts still contain `<!-- ... -->` placeholders.

**Solution:** Run the setup entrypoint for your platform to auto-populate the workflow file from your technical roadmap: `/speckit-pro:setup <SPEC-ID>` in Claude Code or `/speckit-setup <SPEC-ID>` in Codex. If you're creating the workflow manually, fill in all phase prompts before running the autopilot.

## Installation

### Claude Code

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-plugins-public
```

### Codex

For repo-scoped installs, open the repository in Codex and use:

```text
codex
/plugins
```

Codex reads the repo marketplace from [`.agents/plugins/marketplace.json`](../.agents/plugins/marketplace.json).

After the plugin is installed in Codex, run `@SpecKit Pro` → `install` or
`$install` to copy the bundled `codex-agents/*.toml` templates into
`.codex/agents/` or `~/.codex/agents/`, then restart Codex again so the custom
agents are registered.

For user-scope installs, use the official Codex local-plugin layout:

1. Copy the `speckit-pro/` plugin directory to `~/.codex/plugins/speckit-pro`
2. Point `~/.agents/plugins/marketplace.json` at `./.codex/plugins/speckit-pro`
3. Restart Codex so the plugin appears in the plugin directory
4. Run `@SpecKit Pro` → `install` or `$install`
5. Restart Codex again so the installed custom agents are loaded

After updating the plugin, update the plugin directory that the Codex
marketplace points to, rerun the install skill if the bundled
`codex-agents/*.toml` templates changed, and restart Codex so the installed
cache and custom-agent registry refresh.

Official references:

- [Codex plugins](https://developers.openai.com/codex/plugins)
- [Install a local plugin manually](https://developers.openai.com/codex/plugins/build#install-a-local-plugin-manually)
- [Marketplace metadata](https://developers.openai.com/codex/plugins/build#marketplace-metadata)
- [Codex skills](https://developers.openai.com/codex/skills)
- [Codex subagents](https://developers.openai.com/codex/subagents)

### Claude Code Marketplace Shortcut

```
/plugin install speckit-pro@racecraft-plugins-public
```

Or add the marketplace first:

```
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-plugins-public
```

## Author

Fredrick Gabelmann — [Racecraft Lab](https://github.com/racecraft-lab)

## License

[MIT](../LICENSE)

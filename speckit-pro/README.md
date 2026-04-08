# speckit-pro

Autonomous Spec-Driven Development plugin for Claude Code and Codex, powered by [GitHub SpecKit](https://github.com/github/spec-kit).

## Overview

speckit-pro turns feature descriptions into production code through a structured 7-phase workflow: specify, clarify, plan, checklist, tasks, analyze, implement. Instead of writing code directly from a prompt, it builds a complete specification first — catching gaps, validating requirements, and planning implementation before any code is written.

The plugin runs autonomously. You provide a feature description, and it handles the rest — spawning specialized agents for research, running multi-agent consensus to resolve ambiguities, validating gates between phases, and implementing with strict TDD. The result is a PR with tests, implementation, and a full paper trail of design decisions.

This plugin ships different entrypoint surfaces for the two platforms:

- **Claude Code** — 2 bundled skills plus 5 `/speckit-pro:*` commands
- **Codex** — 5 bundled skills that surface as slash commands and explicit skill invocations

## Codex Entry Points

Codex does not load the Anthropic `commands/` files from this repository. In Codex, use the skill-backed entrypoints below:

| Capability | Claude Code | Codex |
| ---------- | ----------- | ----- |
| Coaching | `/speckit-pro:coach` | `/speckit-coach` or `$speckit-coach` |
| Setup | `/speckit-pro:setup` | `/speckit-setup` or `$speckit-setup` |
| Autopilot | `/speckit-pro:autopilot` | `/speckit-autopilot` or `$speckit-autopilot` |
| Status | `/speckit-pro:status` | `/speckit-status` or `$speckit-status` |
| Review remediation | `/speckit-pro:resolve-pr` | `/speckit-resolve-pr` or `$speckit-resolve-pr` |

You can also type `@SpecKit Pro` in Codex and then choose the bundled skill you want.

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
1. Validates prerequisites (SpecKit CLI, constitution, workflow file, MCP servers)
2. Executes all 7 phases sequentially, each delegated to a specialized agent
3. Validates gates programmatically between phases (max 2 auto-fix attempts)
4. Runs multi-agent consensus for ambiguous questions, gaps, and findings
5. Implements with strict TDD red-green-refactor
6. Creates a PR via `gh` CLI when complete

**Example workflow:**
```
# Set up the spec (creates worktree + workflow file)
/speckit-pro:setup SPEC-009

# Review the workflow file — verify prompts have enough context
# Then run the autopilot
/speckit-pro:autopilot docs/ai/specs/SPEC-009-workflow.md

# Claude will:
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
3. Builds a unified dashboard with completed, in-progress, and pending specs
4. Recommends the next spec to implement based on priority and dependencies

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

- **Simple phases** (specify, plan, tasks): Delegate to `phase-executor` (Sonnet)
- **Consensus phases** (clarify, checklist, analyze): Specialized executor agent (Opus) + 3 consensus agents in parallel (Sonnet)
- **Implementation**: `implement-executor` (Opus) with strict TDD, one agent per task

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

- **Claude Code CLI** — the plugin runs inside Claude Code
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

**Solution:** The autopilot must delegate each phase to a subagent via the Agent tool. If it runs a Skill directly, the command's completion report kills the agent loop. This is handled automatically — if you see this, re-run the autopilot.

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

```
/plugin install speckit-pro@racecraft-public-plugins
```

Or from the marketplace:

```
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install speckit-pro@racecraft-public-plugins
```

## Author

Fredrick Gabelmann — [Racecraft Lab](https://github.com/racecraft-lab)

## Version

1.1.0

## License

[MIT](../LICENSE)

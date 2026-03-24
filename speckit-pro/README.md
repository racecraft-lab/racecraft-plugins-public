# speckit-pro

Autonomous Spec-Driven Development plugin for Claude Code,
powered by GitHub SpecKit.

## Overview

Two skills packaged as a single plugin:

- **speckit-coach** — SDD methodology coaching, per-command
  guidance, multi-spec master plan creation, workflow tracking,
  and plugin usage guidance
- **speckit-autopilot** — Autonomous workflow executor that reads
  a populated workflow file and runs all 7 SDD phases with
  programmatic gate validation, multi-agent consensus resolution,
  and auto-commits

## Quick Start

1. Install the plugin: `/plugin install speckit-pro@racecraft-public-plugins`
2. Install SpecKit CLI:
   `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
3. Initialize SpecKit: `specify init --ai claude`
4. Create constitution: `/speckit.constitution`
5. Create master plan: `/speckit-pro:coach` →
   "help me create a master plan"
6. Populate workflow file from template:
   `skills/speckit-coach/templates/workflow-template.md`
7. Run autopilot: `claude --dangerously-skip-permissions`
   then `/speckit-pro:autopilot path/to/workflow.md`

## Commands

| Command | Description |
| ------- | ----------- |
| `/speckit-pro:setup <SPEC-ID>` | Set up a spec for autopilot — creates worktree, branch, and populated workflow file |
| `/speckit-pro:autopilot <workflow.md>` | Execute SpecKit workflow autonomously |
| `/speckit-pro:coach <question>` | Get SDD coaching and guidance |
| `/speckit-pro:status [SPEC-ID]` | Full project roadmap, phase detail, and next-spec recommendation |
| `/speckit-pro:resolve-pr <PR>` | Address all GitHub review comments, fix code, and resolve threads via gh CLI |

## Architecture

### Orchestrator-Direct Pattern

The autopilot skill runs in the main session so it can spawn
sub-agents directly — no nesting needed.

- **Simple phases** (specify, plan, tasks): Delegate to a
  single foreground sub-agent
- **Consensus phases** (clarify, checklist, analyze): Main
  session orchestrates, spawns 3 consensus agents in parallel
- **Implementation**: Parallel sub-agents with worktree
  isolation for `[P]` tasks

### Consensus Agents

Three perspective agents provide multi-viewpoint resolution:

| Agent | Perspective | Primary Tools |
| ----- | ---------- | ------------- |
| **codebase-analyst** | Existing code patterns | RepoPrompt |
| **spec-context-analyst** | Constitution, master plan, prior specs | Read, Glob, Grep |
| **domain-researcher** | Best practices, official docs | Tavily, Context7 |

### Consensus Rules (Moderate Mode — Default)

- **2/3 agree** → Use majority answer
- **3/3 agree** → High confidence
- **All disagree** → Flag for human review
- **Security keywords** → Always flag for human

## Configuration

Create `.claude/speckit-pro.local.md` for per-project settings:

```yaml
---
consensus-mode: moderate    # conservative | moderate | aggressive
gate-failure: stop          # stop | skip-and-log
auto-commit: per-phase      # per-phase | batch | none
---
```

## Skills

### speckit-coach

Coaching skill for SDD methodology. Covers getting started,
per-command coaching, troubleshooting, constitution design,
checklist domain selection, multi-spec master plans, workflow
tracking, and autopilot usage.

### speckit-autopilot

Autonomous execution engine. Reads a populated workflow file
and executes all 7 phases:

1. **Specify** → sub-agent runs /speckit.specify
2. **Clarify** → consensus agents resolve each question
3. **Plan** → sub-agent with tech stack injection from CLAUDE.md
4. **Checklist** → all domains + consensus gap remediation
5. **Tasks** → sub-agent with project constraints
6. **Analyze** → finding remediation via consensus
7. **Implement** → parallel sub-agents with worktree isolation

Gates are validated programmatically after each phase. Auto-fix
is attempted (max 2 tries) before escalating to human. After
implementation, a PR is auto-created via `gh` CLI.

## Prerequisites

- Claude Code CLI
- SpecKit CLI:
  `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- SpecKit initialized: `specify init --ai claude`
- Constitution created: `/speckit.constitution`
- Master plan + populated workflow file (for autopilot)

## License

MIT

---
description: Execute a SpecKit workflow autonomously. Reads a populated workflow file and runs all 7 SDD phases with programmatic gate validation, multi-agent consensus resolution, and auto-commits. Requires SpecKit CLI installed, constitution created, and a populated workflow file.
allowed-tools:
  - Agent
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Skill
  - mcp__RepoPrompt__context_builder
  - mcp__RepoPrompt__file_search
  - mcp__RepoPrompt__get_code_structure
  - mcp__RepoPrompt__read_file
  - mcp__tavily-mcp__tavily-search
  - mcp__tavily-mcp__tavily-extract
  - mcp__context7__resolve-library-id
  - mcp__context7__get-library-docs
argument-hint: "path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]"
---

# SpecKit Autopilot

Execute a SpecKit workflow autonomously from a populated workflow file.

## Invocation

The user provides a path to a workflow file and optionally a starting phase:

```text
/speckit-pro:autopilot docs/ai/specs/SPEC-013-workflow.md
/speckit-pro:autopilot docs/ai/specs/SPEC-013-workflow.md --from-phase plan
```

## What to Do

1. **Load the speckit-autopilot skill** using the Skill tool:
   `Skill("speckit-autopilot")`
2. **Pass the workflow file path** and any arguments to the skill
3. The skill contains the full orchestration logic — follow it exactly

The autopilot skill invokes the real `/speckit.*` commands
(in `.claude/commands/`) via the Skill tool for each phase. These
commands use the `.specify/scripts/bash/` infrastructure for branch
creation, prerequisite validation, and path resolution. The autopilot
enriches each command's arguments with context from the workflow file,
master plan, and codebase analysis.

### SpecKit Commands Used

| Phase | Command Invoked | Key Script |
| ----- | -------------- | ---------- |
| Specify | `Skill("speckit.specify", ...)` | `create-new-feature.sh` |
| Clarify | `Skill("speckit.clarify", ...)` | `check-prerequisites.sh` |
| Plan | `Skill("speckit.plan", ...)` | `setup-plan.sh`, `update-agent-context.sh` |
| Checklist | `Skill("speckit.checklist", ...)` | `check-prerequisites.sh` |
| Tasks | `Skill("speckit.tasks", ...)` | `check-prerequisites.sh` |
| Analyze | `Skill("speckit.analyze", ...)` | `check-prerequisites.sh` |
| Implement | `Skill("speckit.implement", ...)` | `check-prerequisites.sh` |

## Prerequisites Check

Before invoking the skill, verify:

- The workflow file exists at the provided path
- SpecKit CLI is installed: `specify check`
- `.specify/` directory exists (with `scripts/bash/` and `templates/`)
- `.specify/memory/constitution.md` exists
- `.claude/commands/speckit.*.md` commands are installed

If any prerequisite fails, tell the user what's missing and how to fix it.

## Arguments

| Argument | Description |
| -------- | ----------- |
| `path` (required) | Path to the populated workflow file |
| `--from-phase` | Start from a specific phase (skip completed phases) |
| `--spec` | Override spec ID detection |

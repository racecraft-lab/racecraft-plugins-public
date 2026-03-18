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

```
/speckit-pro:autopilot docs/ai/specs/SPEC-013-workflow.md
/speckit-pro:autopilot docs/ai/specs/SPEC-013-workflow.md --from-phase plan
```

## What to Do

1. **Load the speckit-autopilot skill** using the Skill tool: `Skill("speckit-autopilot")`
2. **Pass the workflow file path** and any arguments to the skill
3. The skill contains the full orchestration logic — follow it exactly

## Prerequisites Check

Before invoking the skill, verify:
- The workflow file exists at the provided path
- SpecKit CLI is installed: `specify check`
- `.specify/` directory exists
- `.specify/memory/constitution.md` exists

If any prerequisite fails, tell the user what's missing and how to fix it.

## Arguments

| Argument | Description |
|----------|-------------|
| `path` (required) | Path to the populated workflow file |
| `--from-phase` | Start from a specific phase (skip completed phases) |
| `--spec` | Override spec ID detection |

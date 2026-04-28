---
description: Execute a SpecKit workflow autonomously. Reads a populated workflow file and runs all 7 SDD phases with programmatic gate validation, multi-agent consensus resolution, and auto-commits. Requires SpecKit CLI installed, constitution created, and a populated workflow file.
allowed-tools: "*"
argument-hint: "path/to/workflow-file.md [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement] [--spec SPEC-ID]"
---

# SpecKit Autopilot

Execute a SpecKit workflow autonomously from a populated workflow file. The
autopilot starts with Archive Sweep for previously merged specs before running
the requested spec phases.

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

The autopilot skill reads each phase's prompt from the workflow
file and passes it directly to the corresponding `/speckit.*`
command via the Skill tool. It does not enrich, supplement, or
modify the prompts — it passes them as-is, the same way a human
would copy-paste the prompt into Claude Code. The commands use
the `.specify/scripts/bash/` infrastructure for branch creation,
prerequisite validation, and path resolution.

Before Phase 0, the skill checks whether the archive extension is installed
or vendored. If present, it runs the Archive Sweep contract for previously
merged specs, excludes the current target spec, and keeps cleanup dry-run-only
when the branch or worktree is unsafe.

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
- Archive extension is installed or vendored when the project expects
  completed spec cleanup; otherwise Archive Sweep runs as disabled/dry-run
  evidence and reports next steps.

If any prerequisite fails, tell the user what's missing and how to fix it.

## Arguments

| Argument | Description |
| -------- | ----------- |
| `path` (required) | Path to the populated workflow file |
| `--from-phase` | Start from a specific phase (skip completed phases) |
| `--spec` | Override spec ID detection |

# /autopilot

Execute a SpecKit workflow autonomously from a populated workflow file.

## Arguments

- `path` (required): Path to the populated workflow file
- `--from-phase` (optional): Start from a specific phase (specify|clarify|plan|checklist|tasks|analyze|implement)
- `--spec` (optional): Override spec ID detection

## Workflow

1. **Verify Prerequisites**:
   - Workflow file exists at the provided path
   - SpecKit CLI installed: `specify check`
   - `.specify/` directory exists with `scripts/bash/` and `templates/`
   - `.specify/memory/constitution.md` exists

2. **Load the speckit-autopilot skill** — invoke `$speckit-autopilot` with the workflow file
   path and any arguments. The skill contains the full orchestration logic.

The autopilot skill reads each phase's prompt from the workflow file and delegates
to subagents that run the corresponding SpecKit commands. It does not modify the
prompts — it passes them as-is.

## SpecKit Commands Used

| Phase | Command | Key Script |
|-------|---------|------------|
| Specify | `$speckit-specify` | `create-new-feature.sh` |
| Clarify | `$speckit-clarify` | `check-prerequisites.sh` |
| Plan | `$speckit-plan` | `setup-plan.sh`, `update-agent-context.sh` |
| Checklist | `$speckit-checklist` | `check-prerequisites.sh` |
| Tasks | `$speckit-tasks` | `check-prerequisites.sh` |
| Analyze | `$speckit-analyze` | `check-prerequisites.sh` |
| Implement | `$speckit-implement` | `check-prerequisites.sh` |

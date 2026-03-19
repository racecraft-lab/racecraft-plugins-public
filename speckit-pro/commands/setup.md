---
description: Set up a new spec for autopilot execution. Reads the master plan, creates a git worktree, pushes the branch to origin, and generates a populated workflow file. Point it at a SPEC-ID from your master plan and it does the rest.
allowed-tools: "*"
argument-hint: "SPEC-ID (e.g., SPEC-009)"
---

# SpecKit Setup

Prepare a spec from the master plan for autonomous execution.
Creates the worktree, branch, and workflow file — ready for
`/speckit-pro:autopilot`.

## Invocation

```text
/speckit-pro:setup SPEC-009
/speckit-pro:setup SPEC-008
```

## What to Do

### 1. Find the Master Plan

```text
Glob("**/*master*plan*" or "**/*master-plan*")
Also check: docs/ai/*master*.md, docs/ai/specs/*plan*.md
```

If no master plan found, STOP: "No master plan found. Create
one with `/speckit-pro:coach help me create a master plan`."

### 2. Find the Spec in the Master Plan

Read the master plan and find the section for the requested
SPEC-ID (e.g., `### SPEC-009: Search & Database`).

Extract:

- **Spec name** (e.g., "Search & Database")
- **Short name** for the branch (e.g., "search-database")
- **Spec number** (e.g., 009)
- **Tool count** and tool names
- **Priority** (P1/P2/P3)
- **Dependencies** (what it depends on, what depends on it)
- **Scope description** (the full scope text from the
  master plan — this drives the workflow prompts)
- **Status** (must be ⏳ Pending — if already In Progress
  or Complete, warn the user)

If the SPEC-ID is not found, STOP: "SPEC-ID not found in
master plan. Available specs: <list pending specs>."

### 3. Create Git Worktree

```text
1. Detect remote name:
   Bash("git remote -v")

2. Create the branch and worktree:
   Bash("git worktree add .worktrees/<number>-<short-name> -b <number>-<short-name>")

3. Push the branch to origin:
   Bash("git push -u <remote> <number>-<short-name>")
```

If the worktree already exists, ask the user whether to use
the existing one or recreate it.

If the branch already exists (locally or remotely), check it
out in the worktree instead of creating a new one.

### 4. Copy Workflow Template

Find the workflow template in the plugin:

```text
Glob("**/workflow-template.md")
```

Copy it to the spec's workflow location:

```text
Bash("cp <template-path> <worktree>/docs/ai/specs/SPEC-<ID>-workflow.md")
```

Create the `docs/ai/specs/` directory in the worktree if it
doesn't exist.

### 5. Populate the Workflow File

Read the copied workflow file and replace ALL placeholders
with spec-specific values from the master plan:

| Placeholder | Replace With |
| ----------- | ------------ |
| `SPEC_ID` | e.g., `SPEC-009` |
| `SPEC_NAME` | e.g., `Search & Database` |
| `BRANCH_NAME` | e.g., `009-search-database` |
| `TOOL_COUNT` | e.g., `10` |
| `TOOL_NAMES` | e.g., `search_tasks, search_projects, ...` |

**Populate the phase prompts** using the master plan's scope
description. Each phase prompt should include:

- **Specify Prompt:** The full scope description from the
  master plan, plus any constraints, dependencies, and
  prior art referenced in the master plan section

- **Clarify Prompts:** Generate clarify session focuses
  based on the tool types (e.g., "Session 1: Search API
  Behavior", "Session 2: Database Operations")

- **Plan Prompt:** Reference the tech stack from CLAUDE.md,
  the constitution, and the scope description

- **Checklist Prompts:** Recommend checklist domains based
  on the spec's scope (use the signal extraction from
  `checklist-domains-guide.md` if available)

- **Tasks Prompt:** Reference the spec and plan artifacts

- **Analyze Prompt:** Standard cross-artifact analysis

- **Implement Prompt:** Reference tasks.md and plan.md

### 6. Verify and Report

After populating the workflow file:

1. Read it back and verify no placeholders remain
2. Verify the worktree is on the correct branch
3. Verify the branch is pushed to remote

Report:

```text
## Setup Complete

**Spec:** SPEC-009 Search & Database
**Branch:** 009-search-database
**Worktree:** .worktrees/009-search-database/
**Workflow:** docs/ai/specs/SPEC-009-workflow.md
**Remote:** Pushed to <remote>/009-search-database

**Ready to run:**
/speckit-pro:autopilot docs/ai/specs/SPEC-009-workflow.md

**Review the workflow file first** — verify the phase prompts
have enough context for autonomous execution. The more detail
in the prompts, the better the autopilot's output.
```

### 7. Update Master Plan Status

Update the master plan's Progress Tracking table to mark
the spec as `🔄 In Progress`:

```text
| SPEC-009 | Search & Database | 10 | 🔄 In Progress | ... | Specify |
```

Commit: `"chore(SPEC-XXX): set up worktree and workflow for autopilot"`

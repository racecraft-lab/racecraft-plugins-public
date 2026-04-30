---
description: Set up a new spec for autopilot execution. Reads the technical roadmap, creates a git worktree, pushes the branch to origin, runs a Grill Me interview to align on design decisions, and generates a populated workflow file plus a Design Concept doc. Point it at a SPEC-ID from your technical roadmap and it does the rest. Interactive — requires a human user to answer the grill-me questions.
allowed-tools: "*"
argument-hint: "SPEC-ID (e.g., SPEC-009)"
---

# SpecKit Setup

Prepare a spec from the technical roadmap for autonomous execution.
Creates the worktree, branch, and workflow file — ready for
`/speckit-pro:autopilot`.

## Invocation

```text
/speckit-pro:setup SPEC-009
/speckit-pro:setup SPEC-008
```

## What to Do

### 1. Find the Technical Roadmap

```text
Glob("**/*technical*roadmap*" or "**/*technical-roadmap*")
Also check: docs/ai/*roadmap*.md, docs/ai/specs/*roadmap*.md
```

If no technical roadmap found, STOP: "No technical roadmap found. Create
one with `/speckit-pro:coach help me create a technical roadmap`."

### 2. Find the Spec in the Technical Roadmap

Read the technical roadmap and find the section for the requested
SPEC-ID (e.g., `### SPEC-009: Search & Database`).

Extract:

- **Spec name** (e.g., "Search & Database")
- **Short name** for the branch (e.g., "search-database")
- **Spec number** (e.g., 009)
- **Tool count** and tool names
- **Priority** (P1/P2/P3)
- **Dependencies** (what it depends on, what depends on it)
- **Scope description** (the full scope text from the
  technical roadmap — this drives the workflow prompts)
- **Status** (must be ⏳ Pending — if already In Progress
  or Complete, warn the user)

If the SPEC-ID is not found, STOP: "SPEC-ID not found in
technical roadmap. Available specs: <list pending specs>."

### 3. Create Git Worktree

<hard_constraints>

**NEVER commit or push to main.** All work happens in the
worktree. The worktree branch is what gets pushed to remote.

</hard_constraints>

```text
1. Detect remote name:
   Bash("git remote -v")

2. Create the branch and worktree:
   Bash("git worktree add .worktrees/<number>-<short-name> -b <number>-<short-name>")

3. Switch your working directory to the worktree:
   ALL subsequent commands run FROM the worktree path:
   .worktrees/<number>-<short-name>/

4. Push the WORKTREE BRANCH (not main) to remote:
   Bash("cd .worktrees/<number>-<short-name> && git push -u <remote> <number>-<short-name>")

5. Verify you're on the correct branch:
   Bash("cd .worktrees/<number>-<short-name> && git rev-parse --abbrev-ref HEAD")
   Must show: <number>-<short-name> (NOT main)
```

If the worktree already exists, ask the user whether to use
the existing one or recreate it.

If the branch already exists (locally or remotely), check it
out in the worktree instead of creating a new one.

### 4. Run Grill Me Interview (IN the Worktree)

<hard_constraints>

**This step is mandatory.** Every `/setup` invocation runs grill-me before
the workflow file is written. There is no `--no-grill` flag and no skip
path — the interview is what makes the workflow prompts good enough for
autonomous execution.

**Grill-me is human-in-the-loop only.** It uses `AskUserQuestion` to
interview the user. If you are running this command in a non-interactive
context (CI, background agent, automation), abort the entire `/setup`
invocation — do not attempt to skip grilling.

</hard_constraints>

```text
1. Create docs directory in the WORKTREE for the design concept:
   Bash("mkdir -p .worktrees/<number>-<short-name>/docs/ai/specs/")

2. Invoke the grill-me skill with the spec scope as input:
   Skill("grill-me", args: {
     mode: "setup",
     spec_id: "SPEC-<ID>",
     spec_name: "<spec name from roadmap>",
     scope: <full scope description from technical roadmap>,
     output_path: ".worktrees/<number>-<short-name>/docs/ai/specs/SPEC-<ID>-design-concept.md"
   })

3. The skill walks the design tree using AskUserQuestion (one question
   at a time, with the AI's recommendation marked as the first option).
   It returns when the user reaches a natural stop, hits the soft cap
   at 30 questions and chooses to wrap up, or selects "End interview".

4. Verify the design concept doc exists:
   Read(".worktrees/<number>-<short-name>/docs/ai/specs/SPEC-<ID>-design-concept.md")
   Must contain Goals, Non-goals, Design Tree (Q&A log), and Open Questions.
```

The Q&A log and Goals/Non-goals from this doc drive the next step's
workflow prompts. Pass the doc path forward.

### 5. Copy Workflow Template (IN the Worktree)

All file operations happen in the worktree directory.

```text
1. Read the workflow template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/workflow-template.md")

2. Write the template to the WORKTREE:
   Write(".worktrees/<number>-<short-name>/docs/ai/specs/SPEC-<ID>-workflow.md",
         content: <template content from step 1>)
```

### 6. Populate the Workflow File

Read the copied workflow file (in the worktree) and replace
ALL placeholders with spec-specific values from the master
plan:

| Placeholder | Replace With |
| ----------- | ------------ |
| `SPEC_ID` | e.g., `SPEC-009` |
| `SPEC_NAME` | e.g., `Search & Database` |
| `BRANCH_NAME` | e.g., `009-search-database` |
| `TOOL_COUNT` | e.g., `10` |
| `TOOL_NAMES` | e.g., `search_tasks, search_projects, ...` |

**Populate the phase prompts** using BOTH the technical roadmap's scope
description AND the design concept doc from Step 4. The roadmap scope
is the seed; the design concept is the enrichment layer that fills in
the decisions the roadmap left ambiguous.

- **Specify Prompt:** Combine the roadmap scope description with the
  Goals, Non-goals, and major design decisions from
  `SPEC-<ID>-design-concept.md`. Quote specific Q&A entries when a
  prompt needs to capture *why* a particular decision was made.

- **Clarify Prompts:** Use the design concept's Open Questions section
  to seed the autopilot's clarify session focuses. Anything still open
  after the grill-me interview is exactly what `/speckit.clarify` should
  be told to dig into. Generate session focuses based on the tool types
  and any unresolved branches (e.g., "Session 1: Search API Behavior",
  "Session 2: Database Operations").

- **Plan Prompt:** Combine the tech stack from CLAUDE.md, the
  constitution, the roadmap scope description, AND the
  architecture / data-model / constraint decisions extracted from
  the design concept doc's Q&A log. Quote the user's chosen answer
  for any decision that drives a planning choice. Also reference
  the design concept doc path so the autopilot can re-read it
  during planning if it needs context the prompt didn't capture.

- **Checklist Prompts:** Recommend checklist domains based on the
  spec's scope and the design tree branches the grill-me session
  walked (use the signal extraction from `checklist-domains-guide.md`).

- **Tasks Prompt:** Reference the spec, plan, AND design concept
  doc. Use the design concept's Non-goals to bound task generation —
  flag any task that would cross those boundaries. Use the Q&A
  log's "why" context to inform task ordering and TDD test
  specifications.

- **Analyze Prompt:** Cross-artifact consistency check across
  spec.md, plan.md, tasks.md, AND the design concept doc. Flag any
  drift between the design concept's Goals / Non-goals / decisions
  and what the downstream artifacts say. The design concept is the
  source of truth for scoping decisions captured during grill-me;
  if a downstream artifact contradicts it, the downstream artifact
  is wrong unless there is an explicit revision note.

- **Implement Prompt:** Reference tasks.md, plan.md, AND the
  design concept doc. When implementing, consult the Q&A log for
  the "why" behind decisions — this informs test specifications,
  edge-case handling, and refactor choices. Decisions captured in
  the design concept that aren't reflected in tasks.md should be
  surfaced as gaps before coding, not silently dropped.

### 7. Commit and Verify (IN the Worktree)

All commits happen on the worktree branch — NEVER on main.

```text
1. Stage and commit BOTH the design concept doc AND the workflow file:
   Bash("cd .worktrees/<number>-<short-name> && \
     git add docs/ai/specs/SPEC-<ID>-design-concept.md \
             docs/ai/specs/SPEC-<ID>-workflow.md && \
     git commit -m 'chore(SPEC-XXX): add design concept and workflow for autopilot'")

2. Push the WORKTREE BRANCH:
   Bash("cd .worktrees/<number>-<short-name> && \
     git push")

3. Verify:
   - Read the design concept doc — must contain Goals, Non-goals,
     Q&A log, and Open Questions sections.
   - Read the workflow file back — no placeholders remain, and the
     Specify/Clarify Prompts contain content traceable to the
     design concept's Q&A log.
   - Bash("cd .worktrees/... && git rev-parse --abbrev-ref HEAD")
     → must show the spec branch, NOT main
   - Bash("cd .worktrees/... && git log --oneline -1")
     → must show the design-concept-and-workflow commit
```

Report:

```text
## Setup Complete

**Spec:** SPEC-009 Search & Database
**Branch:** 009-search-database
**Worktree:** .worktrees/009-search-database/
**Design Concept:** .worktrees/009-search-database/docs/ai/specs/SPEC-009-design-concept.md
**Workflow:** .worktrees/009-search-database/docs/ai/specs/SPEC-009-workflow.md
**Remote:** Pushed to <remote>/009-search-database

**Ready to run:**
/speckit-pro:autopilot docs/ai/specs/SPEC-009-workflow.md

**Review both files first** — the design concept doc captures the
decisions you made during grill-me; the workflow file is what the
autopilot will execute. Verify the phase prompts have enough context
for autonomous execution.
```

### 8. Update Technical Roadmap Status (IN the Worktree)

Update the technical roadmap's Progress Tracking table IN THE
WORKTREE (not on main) to mark the spec as `🔄 In Progress`:

```text
1. Edit the technical roadmap found in Step 1, using the WORKTREE path:
   Edit(".worktrees/<number>-<short-name>/<roadmap-path-from-step-1>")

2. Commit IN THE WORKTREE:
   Bash("cd .worktrees/<number>-<short-name> && \
     git add docs/ai/ && \
     git commit -m 'chore(SPEC-XXX): mark as In Progress' && \
     git push")
```

**NEVER push to main.** The technical roadmap update will reach
main when the spec's PR is merged.

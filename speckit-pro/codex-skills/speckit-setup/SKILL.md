---
name: speckit-setup
description: >
  Prepare a SPEC-ID from the technical roadmap for autonomous
  execution in Codex. Creates or reuses the spec branch and
  worktree, copies the workflow template, fills the phase prompts,
  commits the workflow artifacts, and updates roadmap status.
---

# SpecKit Setup

## Scope

Use this skill when the user wants a SPEC-ID prepared for
`$speckit-autopilot`. This skill is responsible for the mutation-heavy
bootstrap step: identify the roadmap entry, create or reuse the correct
worktree branch, generate the workflow file, and leave the repository in a
state where the autopilot can start immediately.

If the user is still figuring out how to decompose a feature, write a
technical roadmap, or understand the SDD process, redirect them to
`$speckit-coach`. Do not invent roadmap data or phase prompts from vague
requirements when the roadmap entry does not exist.

## Input

Accept:

- a required `SPEC-ID` such as `SPEC-009`
- an optional technical roadmap path if the user already knows it
- an optional worktree root override if the repository uses a nonstandard
  location

If the request does not include a SPEC-ID, stop and ask for it. Everything
else should be derived from the repository.

## Hard Constraints

- Never commit or push `main`.
- Detect the actual git remote name before pushing.
- Create or reuse a dedicated worktree branch for the spec.
- After the worktree exists, perform all file edits inside the worktree, not in
  the main checkout.
- Use the shared workflow template at
  `../../skills/speckit-coach/templates/workflow-template.md`.
- Do not leave placeholder tokens such as `SPEC_ID`, `SPEC_NAME`, or empty
  phase prompts in the generated workflow.
- Do not run the autopilot at the end. Setup stops once the workflow is ready,
  committed, and pushed.

## Procedure

### 1. Locate the technical roadmap

Search for the roadmap before asking the user where it lives. Check likely
paths such as `docs/ai/`, `docs/ai/specs/`, and any file matching
`*technical-roadmap*` or `*roadmap*`. If no roadmap exists, stop with a short
message telling the user to create one with `$speckit-coach`.

### 2. Parse the requested roadmap entry

Read the section for the requested `SPEC-ID` and extract the data needed to
seed the workflow:

- spec name
- spec number
- short branch slug
- priority
- dependency information
- current status
- scope description and any constraints
- any tool count or tool names already recorded in the roadmap

If the spec is missing, stop and report the available pending specs. If the
spec is already complete, warn the user and stop. If the roadmap says the spec
is already in progress, prefer reusing the existing worktree branch rather than
creating a second setup.

### 3. Prepare the branch and worktree

Before any git mutation, inspect the actual remotes with `git remote -v`.
Never assume `origin`. Then:

1. Check whether the intended branch already exists locally or remotely.
2. If a worktree for that branch already exists, reuse it unless the user has
   explicitly asked to recreate it.
3. If the branch exists but no worktree does, add a worktree for the existing
   branch.
4. If the branch does not exist, create it while adding the worktree.

Use a deterministic branch naming scheme based on the spec number and short
slug, for example `009-search-database`. Verify the active branch inside the
worktree before continuing.

### 4. Copy the workflow template into the worktree

Create the destination directory inside the worktree, typically
`docs/ai/specs/`, then load the shared workflow template from the plugin. Do
not author a new template from scratch. The generated file should live at a
path like `docs/ai/specs/SPEC-009-workflow.md` inside the worktree.

### 5. Populate the workflow file

Replace all placeholders using the roadmap data. At minimum populate:

- `SPEC_ID`
- `SPEC_NAME`
- `BRANCH_NAME`
- tool count and tool names if the roadmap provides them

Then seed each phase prompt with concrete, spec-specific context rather than a
generic placeholder. Use the roadmap scope and dependencies to fill:

- Specify prompt
- Clarify session focus areas
- Plan prompt
- Checklist domain suggestions
- Tasks prompt
- Analyze prompt
- Implement prompt

The prompts should be strong enough that `$speckit-autopilot` can execute
without the user hand-editing obvious missing context. If some detail is not in
the roadmap but can be inferred from the repo, use that repo context. If a
critical detail cannot be derived, stop and report the gap rather than filling
it with fiction.

### 6. Commit and push from the worktree

Stage the workflow file in the worktree branch, create a focused setup commit,
and push that branch to the detected remote. Then verify:

- the workflow file exists in the worktree
- placeholders are gone
- `git rev-parse --abbrev-ref HEAD` shows the spec branch
- `git log --oneline -1` shows the setup commit

### 7. Update roadmap status in the worktree

Update the technical roadmap copy inside the worktree to mark the spec as in
progress. Commit and push that roadmap status change on the same spec branch.
Do not touch the main checkout. The roadmap change reaches the default branch
only when the spec branch is merged.

## Output

Finish with a concise setup report that includes:

- the spec name and ID
- branch name
- worktree path
- workflow path
- remote branch that was pushed
- the exact next step: run `$speckit-autopilot` or `/speckit-autopilot` with
  the generated workflow file

## Failure Handling

Stop instead of improvising when any of the following are true:

- no technical roadmap exists
- the SPEC-ID is not in the roadmap
- the branch or worktree state is ambiguous and cannot be safely reused
- git push fails
- the workflow still contains unresolved placeholders after population

If setup partially succeeds before a failure, report exactly what was created
and what remains unfinished so the user can resume without duplicating work.

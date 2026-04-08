---
name: speckit-status
description: >
  Show the current SpecKit roadmap and workflow status in Codex.
  Aggregates workflow files and technical roadmaps, highlights
  active specs, identifies blocked work, and recommends the next
  unblocked spec to start.
---

# SpecKit Status

## Scope

Use this skill when the user wants to know what is in progress, what is
blocked, what has already shipped, or which spec should be started next. This
is the read-only project dashboard for SpecKit workflows. It should summarize
both the high-level roadmap and the phase-level progress inside workflow files.

If the user wants help understanding SDD methodology, checklist domains, or how
to fix a failing gate, redirect to `$speckit-coach`. If the user wants to
execute a populated workflow, redirect to `$speckit-autopilot`. This skill is
for status, synthesis, and next-step recommendation.

## Input

Accept either:

- no argument, meaning “show the overall roadmap”
- `all`, which is the same as the overall roadmap view
- a specific `SPEC-ID` such as `SPEC-013`

When no argument is provided, prefer the full dashboard. When a `SPEC-ID` is
provided, show the targeted detail view for that spec first.

## What to Read

Search the repository and any attached git worktrees for both of the following
before answering:

- technical roadmap files, typically matching `*technical-roadmap*` or
  `*roadmap*`
- workflow files, typically matching `*-workflow.md`

Do not assume the user keeps everything under one directory. Search the current
checkout first, then inspect `git worktree list --porcelain` so workflows in
attached worktrees are included even when setup used a nonstandard worktree
root. Narrow to the files that actually describe the SpecKit project. If a file
looks unrelated, ignore it rather than polluting the dashboard.

## Overall Dashboard Procedure

### 1. Parse the roadmap first

The technical roadmap is the source of truth for the full set of specs,
including pending work that does not yet have a workflow file. From the roadmap
extract, when available:

- spec IDs
- spec names
- priority
- dependency relationships or tiers
- tool counts
- status markers such as complete, in progress, pending, or blocked
- next phase or blocker notes

If multiple roadmap files exist, pick the most relevant current roadmap and say
which file you used. Do not merge unrelated roadmaps unless the repo clearly
uses a multi-roadmap setup.

### 2. Parse workflow files for phase detail

Workflow files add the fine-grained execution state the roadmap usually lacks.
Collect them from the main checkout and any attached worktree paths. For each
workflow file:

- identify the `SPEC-ID`
- read the workflow overview table
- record which phases are complete, in progress, pending, or failed
- detect the current phase
- capture the branch name if the workflow records it

Use workflow data to enrich the roadmap view, not to replace it. A spec may be
pending in the roadmap and have no workflow file yet. That should still appear
in the output.

### 3. Build a unified picture

Combine roadmap and workflow information into a single report. The dashboard
should clearly separate:

- complete specs
- active specs with phase detail
- ready-to-start specs with no blockers
- blocked specs with the specific dependency or missing prerequisite

When there are active workflows, show a phase table so the user can see whether
the spec is stuck in clarify, checklist, analyze, or implementation.

### 4. Recommend the next spec

Pick the next recommendation using concrete rules, not vibes:

1. Exclude complete specs.
2. If a spec is already in progress, recommend finishing it first.
3. Among pending specs, exclude anything blocked by incomplete dependencies.
4. Sort the remaining specs by priority, then by roadmap order.
5. Recommend the top candidate and optionally list one or two alternatives.

Explain why the recommendation is unblocked and why it outranks the
alternatives. If all remaining specs are blocked, say so plainly.

## Specific Spec Procedure

When the user requests a single `SPEC-ID`, show:

- the spec name and status
- the roadmap scope summary
- dependencies and what this spec unlocks
- workflow phase status if a workflow file exists
- current blockers or missing artifacts
- the next concrete command

If no workflow file exists for the requested spec, say that directly and
recommend `$speckit-setup <SPEC-ID>` rather than pretending there is execution
state.

## Output Format

Prefer a concise dashboard with:

- a summary section with totals
- grouped tables or lists for complete, active, ready, and blocked specs
- a `Recommended Next` section

For a spec-specific view, prefer a shorter report with the current phase, key
artifacts, blockers, and next action.

The answer should be actionable. If the best next step is to create a workflow,
say so. If the best next step is to resume autopilot from an active workflow,
say so. If the roadmap is missing, point the user to `$speckit-coach` for
roadmap creation guidance.

## Edge Cases

Handle these explicitly:

- No roadmap and no workflow files: report that no SpecKit tracking artifacts
  were found.
- Roadmap exists but no workflow files: show the roadmap view and recommend
  `$speckit-setup` for pending specs.
- Workflow files exist without a roadmap: report phase detail from workflows,
  but note that backlog visibility is incomplete.
- Multiple workflow files for the same spec: prefer the one that matches the
  active branch or the most recent in-progress state.

## Boundaries

This skill does not mutate the repo. Do not create branches, edit workflow
files, or mark roadmap rows complete from inside the status skill. If the user
wants to act on the recommendation, direct them to the corresponding entrypoint:

- `$speckit-setup` to prepare a spec
- `$speckit-autopilot` to execute a workflow
- `$speckit-resolve-pr` to address review feedback
- `$speckit-coach` for process guidance

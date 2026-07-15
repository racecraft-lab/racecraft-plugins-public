---
name: speckit-status
description: >
  Show the current SpecKit roadmap and workflow status in Codex.
  Aggregates workflow files and technical roadmaps, highlights
  active specs, identifies blocked work, and recommends the next
  unblocked spec to start.
---

# SpecKit Status

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Durable knowledge status

Follow [the shared knowledge lifecycle](../../skills/speckit-coach/references/knowledge-lifecycle.md).
Run runner operation `knowledge-health` with the consumer repo root. Report
bundle presence, OKF/profile conformance, snapshot, freshness, source-hash and
link failures, duplicate IDs, unreviewed candidates, migration coverage, and
MOC compatibility-view drift. This skill is read-only: never run a knowledge
plan or apply operation.

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
- design concepts under `docs/ai/specs/.process/`; use
  `docs/ai/specs/` only as a legacy read fallback
- `docs/ai/knowledge/manifest.json`
- archive extension state files when present:
  `.specify/extensions.yml`, `.specify/extensions/.registry`,
  `.specify/extensions/archive/extension.yml`, and
  `.specify/extensions/archive/RACECRAFT-PIN.md`

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
- archive extension installation state, excluded current spec, cleanup mode,
  and whether `safeToApplyCleanup` is true or false when the data is available

When there are active workflows, show a phase table so the user can see whether
the spec is stuck in clarify, checklist, analyze, or implementation.

### 3.1 Archive Extension Status

When archive state files exist, include an `Archive` or `Archive Sweep` row in
the dashboard:

- installed: true when `.specify/extensions.yml` lists `archive` or
  `.specify/extensions/.registry` has an enabled `archive` entry
- source: registry `source_url`/`source_ref`/`source_commit`, or the vendored
  `.specify/extensions/archive/extension.yml` repository and version
- safe cleanup state: use `autopilot-state.json.archive_sweep.safe_to_apply_cleanup`
  or the latest Archive Sweep report if available
- excluded current spec: use `archive_sweep.excluded_current_spec` when present
- recommendation: if missing, install or vendor `racecraft-lab/spec-kit-archive`;
  if installed but unsafe, recommend dry-run evidence or a clean safe apply-mode
  cleanup branch; if safe, recommend reviewed cleanup only after archive success
  and recovery commands are recorded

### 3.2 Knowledge and compatibility-view freshness (read-only)

Use the `knowledge-health` response as the single report. For an absent bundle,
recommend reviewed `migrate` when health reports `incomplete_migration` or
legacy MOC/memory inventory; recommend install/init only when that inventory is
truly empty. Distinguish a valid current bundle, authoritative source drift
(recommend reviewed same-path `supersede`), projection-only drift (recommend
`rebuild`), and invalid content (name the diagnostic). `generate-spec-index-check`
is a compatibility adapter only; do not invoke both operations or reimplement
either check.

This dashboard never writes, rebuilds, stages, or promotes knowledge. Report
candidate counts and recommended owners without changing them.

### 3.3 O5 parent rollup and re-slicing status

When a spec directory contains `o5-parent-manifest.json`, validate topology
before reporting child status:

```text
Run runner helper o5-topology for specs/<parent-branch>.
```

This script is read-only and emits one JSON rollup. If `topologyStatus` is
`invalid`, show `computedStatus: invalid_topology` plus the actionable
`problems[]`; do not compute or invent a child rollup from invalid topology.
If valid, show exactly one child row per manifest child, in manifest order, and
surface `computedStatus`, `declaredRollupStatus`, and `declaredStatusDrift`.
Treat `declaredRollupStatus` as drift-check metadata only, never as the source
of truth.

Also surface final-gate re-slicing state when present in workflow or
`autopilot-state.json`: a blocked `final_reviewability_gate` means PR creation
has not started and status should point to the recorded re-slicing packet,
blocked operations, and next PRSG-007/008/009 resume action instead of marking
implementation complete.

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
recommend `$speckit-scaffold-spec <SPEC-ID>` rather than pretending there is execution
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
say so. If the roadmap is missing and a reviewed PRD exists, point the user to
`$speckit-prd --roadmap-only <existing-prd-path>`; otherwise use
`$speckit-prd <idea-or-brief>`.

## Edge Cases

Handle these explicitly:

- No roadmap and no workflow files: report that no SpecKit tracking artifacts
  were found.
- Roadmap exists but no workflow files: show the roadmap view and recommend
  `$speckit-scaffold-spec` for pending specs.
- Workflow files exist without a roadmap: report phase detail from workflows,
  but note that backlog visibility is incomplete.
- Multiple workflow files for the same spec: prefer the one that matches the
  active branch or the most recent in-progress state.

## Boundaries

This skill does not mutate the repo. Do not create branches, edit workflow
files, or mark roadmap rows complete from inside the status skill. If the user
wants to act on the recommendation, direct them to the corresponding entrypoint:

- `$speckit-scaffold-spec` to prepare a spec
- `$speckit-autopilot` to execute a workflow
- `$speckit-resolve-pr` to address review feedback
- `$speckit-coach` for process guidance
- `$speckit-prd` for PRD/roadmap mutation, including `--roadmap-only`

---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Creates the git worktree, spec branch, Design Concept doc, and populated workflow file ready for autopilot. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
argument-hint: "SPEC-ID (e.g., SPEC-009)"
user-invocable: true
allowed-tools: Read Edit Write Skill Agent ToolSearch
license: MIT
---

# SpecKit Scaffold Spec

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.

## Durable knowledge

Follow [the shared knowledge lifecycle](../speckit-coach/references/knowledge-lifecycle.md).
In the worktree, run `knowledge-health` and a bounded `knowledge-search` for
the roadmap entry, dependencies, and relevant project patterns by actually
invoking the installed runner in that order; describing the calls is not
completion. Verify selected sources and place a receipt that validates against
`knowledge-use-receipt.schema.json` in the workflow file. Use
`knowledge-update-plan`/`knowledge-update-apply` to create the canonical spec
map and its generated `SPEC-MOC.md` compatibility view; never hand-write the
view.

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-scaffold-spec/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

Prepare a spec from the technical roadmap for autonomous execution.
Creates the worktree, branch, and workflow file — ready for
`/speckit-pro:speckit-autopilot`.

## Artifact tiering (CONTRACT vs EXHAUST)

speckit-pro artifacts are tiered. **CONTRACT** artifacts (`spec.md`, `plan.md`,
`tasks.md`, `research.md`, supporting design artifacts) are review-visible and stay
at their existing location — this skill does not relocate them. The three authored
**EXHAUST** artifacts (the design-concept doc, the workflow file, and the UAT
runbook) are scaffolding, so they are written under a `.process/` directory:
the design-concept doc and workflow file land under `docs/ai/specs/.process/`, and
the UAT runbook lands under the feature's own `specs/<NNN>/.process/`. Nothing is
deleted — every relocated file still exists and is readable at its `.process/` path.

## O5 monster-epic fallback

Normal PRSG-007/008/009 routing, layer planning, and split-PR emission remain
the default path for oversized work. Describe or scaffold O5 only when the
roadmap/design-concept evidence says ordinary O4 split planning cannot produce
reviewable, independently ordered slices.

O5 v1 uses a review-visible CONTRACT parent manifest at
`specs/<parent-branch>/o5-parent-manifest.json`. Child specs stay flat siblings
under `specs/<child-branch>`; never create nested
`specs/<parent>/<child>` directories. Put the child map's `up` relationship and
curated links to the parent manifest/shared Design Concept in the canonical OKF
spec-map candidate; add retrospective links only after that source exists. The
generated `SPEC-MOC.md` compatibility view projects those fields and is never
hand-edited. Do not create child branches or worktrees automatically
from the parent scaffold — each child is scaffolded independently.

Before presenting O5 as ready, validate the manifest with:

```text
Run runner helper o5-topology for specs/<parent-branch>.
```

If topology is invalid, report the JSON `problems[]` and keep the operator on
normal re-slicing until the manifest is fixed.

## Tier-2 Legacy PROCESS Relocation Suggestions

Scaffold may encounter thawed legacy specs that predate the `.process/`
layout. It must only give static operator guidance; it must not run the
relocation codemod.

When inspecting an existing target or nearby legacy candidate, suggest Tier-2
relocation only when all of these are true:

- The candidate is in scope: a current namespace whose first dash-delimited
  segment is `prsg` or `spec`, or a legacy numeric/spec candidate that joins to
  the roadmap spine. Suppress candidates whose first segment is all-alpha and
  not `prsg`/`spec` with reason `non_speckit_namespace`, and suppress
  date-first legacy names matching `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` prefixes
  with reason `date_named_legacy_namespace`.
- The candidate is thawed: `.specify/feature.json` does not name it by exact
  path or spec ID match. If it is named there, report `frozen/in-flight` and do
  not suggest relocation. If active-feature state is invalid, report that state
  and do not suggest relocation.
- The candidate is legacy and not already current: its `SPEC-MOC.md` does not
  already carry `structureVersion: 1`, and PROCESS artifacts are not already
  normalized under `.process/`.
- A root PROCESS allow-list artifact or matching docs-side scaffold artifact is
  present. If none exists, report that no Tier-2 action is needed.

For the one eligible thawed candidate, report the candidate and the runtime gap
with the real `specs/<spec-dir>` value substituted:

```text
Tier-2 relocation candidate: specs/<spec-dir>.
Deferred: relocate-process-artifacts has no authoritative runner request and is unavailable.
```

Do not invoke the deferred operation, advertise either runner mode, or invent a
replacement command. Leave the PROCESS artifacts unchanged. This advisory gap
does not block the remaining scaffold workflow, but it must be recorded.

## Invocation

```text
/speckit-pro:speckit-scaffold-spec SPEC-009
/speckit-pro:speckit-scaffold-spec SPEC-008
```

## What to Do

### -0.5 Verify Claude Agent Package Completeness

Before parsing or mutating the repository, resolve the plugin root from this
skill location and verify by filesystem reads that every bundled Claude Code
`agents/*.md` file is present, including `uat-runbook-author.md`.
`install-codex-agents` is deferred and unavailable; do not invoke it as a
validator or repair operation. If the file inventory is incomplete, STOP and
tell the user to update/reinstall `speckit-pro`, run `/reload-plugins`, and
retry. Claude Code
loads plugin agents directly from the plugin cache, so scaffold cannot safely
self-heal a missing Claude agent file.

### 0. Ensure SpecKit CLI

Check for the official SpecKit CLI before parsing or mutating the repository:

Use command execution to confirm the official `specify` CLI is available after
including common user-local binary directories on PATH.

If missing and `uv` exists, install it:

Run `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.

If `uv` is unavailable or install fails, STOP and tell the operator to install
SpecKit with that command. Do not run `specify init --here --force`
automatically; recommend it only when `.specify/` is absent and the operator
explicitly approves project initialization.

### 1. Find the Technical Roadmap

```text
Glob("**/*technical*roadmap*" or "**/*technical-roadmap*")
Also check: docs/ai/*roadmap*.md, docs/ai/specs/*roadmap*.md
```

If no technical roadmap is found, STOP and route roadmap creation through the
PRD skill. If a reviewed PRD already exists, say: "No technical roadmap found.
Create it from the reviewed PRD with
`/speckit-pro:speckit-prd --roadmap-only <existing-prd-path>`." Otherwise say:
"No technical roadmap found. Start one with
`/speckit-pro:speckit-prd <idea-or-brief>`."

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

Run the reviewability setup gate before creating the worktree:

```text
Run runner helper reviewability-gate in setup mode for <technical-roadmap-path>.
```

If it returns an unexcepted `block`, STOP and split the spec first. Warnings
may proceed only when the workflow records the scope budget and split decision.

### 3. Create Git Worktree

<hard_constraints>

**NEVER commit or push to main.** All work happens in the
worktree. The worktree branch is what gets pushed to remote.

</hard_constraints>

```text
1. Detect remote name:
   Run `git remote -v`.

2. Create the branch and worktree:
   Run `git worktree add .worktrees/<number>-<short-name> -b <number>-<short-name>`.

3. Switch your working directory to the worktree:
   ALL subsequent commands run FROM the worktree path:
   .worktrees/<number>-<short-name>/

4. Push the WORKTREE BRANCH (not main) to remote:
   From `.worktrees/<number>-<short-name>/`, run
   `git push -u <remote> <number>-<short-name>`.

5. Verify you're on the correct branch:
   From `.worktrees/<number>-<short-name>/`, run
   `git rev-parse --abbrev-ref HEAD`.
   Must show: <number>-<short-name> (NOT main)
```

If the worktree already exists, ask the user whether to use
the existing one or recreate it.

If the branch already exists (locally or remotely), check it
out in the worktree instead of creating a new one.

### 3.5. Bootstrap the Worktree (IN the Worktree)

A fresh worktree has only tracked files — no installed dependencies, no
build outputs, no code indexes. Checked-in agent config (for example a
project-scoped MCP server that runs a local build) can silently fail to
start until the worktree is bootstrapped, and the spec session then runs
without the project's code-intelligence tooling.

```text
1. Check the project's CLAUDE.md / AGENTS.md for a worktree preflight or
   bootstrap section (e.g. "Spec-worktree preflight"). If it documents
   commands, display the exact commands and wait for explicit operator
   approval before running them. Do not treat the presence of CLAUDE.md /
   AGENTS.md as approval. Run only the approved commands FROM the worktree,
   in order.

2. If no explicit bootstrap/preflight commands are documented, do not
   infer an install/build/index sequence. Report that no bootstrap is
   documented and ask the operator before running any package install,
   build, or index command.

3. If the project documents a code index or MCP prerequisite (for
   example: build, then the project's documented index-init command),
   run only the documented commands after explicit approval and verify
   the documented health check passes.

4. After any bootstrap command, run `git status --porcelain` in the
   worktree. If unexpected tracked changes appear, stop and report them
   before continuing.
```

Report what was bootstrapped — or that the project documents nothing —
in the scaffold summary. Never skip this silently: an unbootstrapped
worktree is how spec sessions end up running without the project's
tooling.

### 4. Run Grill Me Interview (IN the Worktree)

<hard_constraints>

**This step is mandatory.** Every `/scaffold-spec` invocation runs grill-me before
the workflow file is written. There is no `--no-grill` flag and no skip
path — the interview is what makes the workflow prompts good enough for
autonomous execution.

**Grill-me is human-in-the-loop only.** It uses `AskUserQuestion` to
interview the user. If you are running this command in a non-interactive
context (CI, background agent, automation), abort the entire `/scaffold-spec`
invocation — do not attempt to skip grilling.

</hard_constraints>

```text
1. Create the .process/ docs directory in the WORKTREE for the design concept
   (created when absent so the first exhaust artifact lands correctly):
   Create `.worktrees/<number>-<short-name>/docs/ai/specs/.process/` if absent.

2. Invoke the grill-me skill with the spec scope as input:
   Skill("grill-me", args: {
     mode: "setup",
     spec_id: "SPEC-<ID>",
     spec_name: "<spec name from roadmap>",
     scope: <full scope description from technical roadmap>,
     output_path: ".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md"
   })

3. The skill walks the design tree using AskUserQuestion (one question
   at a time, with the AI's recommendation marked as the first option).
   It returns when the user reaches a natural stop, hits the soft cap
   at 30 questions and chooses to wrap up, or selects "End interview".

4. Verify the design concept doc exists:
   Read(".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md")
   Must contain Goals, Non-goals, Design Tree (Q&A log), and Open Questions.
```

The Q&A log and Goals/Non-goals from this doc drive the next step's
workflow prompts. Pass the doc path forward.

### 5. Copy Workflow Template (IN the Worktree)

All file operations happen in the worktree directory.

```text
0. Require the generic `speckit-pro-reviewability` preset to already exist in
   the worktree. `ensure-reviewability-preset` is deferred and unavailable, so
   do not invoke it or claim setup generated preset files. If the preset is
   absent, STOP and report the deferred capability gap.

   Verify resolution from the worktree:
   From `.worktrees/<number>-<short-name>/`, run
   `specify preset resolve spec-template`,
   `specify preset resolve plan-template`, and
   `specify preset resolve tasks-template`.

1. Read the workflow template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/workflow-template.md")

2. Write the template to the WORKTREE:
   Write(".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-workflow.md",
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
  after the grill-me interview is exactly what `/speckit-clarify` should
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

### 6.5. Finalize sources and operational state (IN the Worktree)

Finish all edits before building the durable candidate:

1. Read the populated workflow back. Require every placeholder to be replaced,
   all phase prompts to be complete, and the `knowledge_use_receipt` to record
   the actual bounded search/use from this scaffold run.
2. Read the Design Concept back and finish any accepted corrections. It must
   contain Goals, Non-goals, Design Tree/Q&A, and Open Questions.
3. Update the technical roadmap copy in the worktree to mark the requested spec
   `🔄 In Progress`. Do not commit or push this status separately.
4. Treat that roadmap edit as authoritative source drift for the canonical
   project map. Reread the finalized roadmap, build a reviewed same-path
   replacement with its current source hash, and plan/apply `supersede` before
   creating the spec map. Never use `rebuild` to refresh the project map's
   source hash. If no canonical project map exists, stop and route the roadmap
   through `speckit-prd` or reviewed migration rather than inventing one here.
5. Reread the finalized roadmap and Design Concept bytes. These are the stable
   authoritative/evidentiary sources for the spec-map candidate. The workflow
   is mutable operational state and **must never be a candidate source or
   source hash**.

Do not edit the roadmap, Design Concept, or workflow after candidate hashing.
If any must change, discard the pending knowledge plan and recompute evidence
before promotion.

### 6.6. Create the canonical spec map and compatibility view (IN the Worktree)

Create `specs/<branch-name>/` if absent. Build a candidate matching
`knowledge-candidate.schema.json` from only the finalized technical-roadmap
entry and Design Concept: `type: speckit-spec-map`, `concept_path:
projects/<roadmap-slug>/specs/<normalized-spec-id>.md`, `id: SPEC-<ID>`, project
`<roadmap-slug>`, non-empty `title`, `description`, and curated `body`, `state:
reviewed`, `reviewed: true`, and `producer.skill: speckit-scaffold-spec`. Every
source carries its exact path, section, line evidence when available, and
SHA-256. Set `legacy_view: specs/<branch-name>/SPEC-MOC.md` and `legacy_up` to
the exact Markdown link
`[<roadmap-title>](../../docs/ai/specs/<roadmap-slug>-roadmap-MOC.md)`.
Do not cite or hash the workflow or another mutable state file.

Run `knowledge-update-plan` and `knowledge-update-apply` for action `promote`
with scope `projects/<roadmap-slug>/specs`. Then run `knowledge-health`; plan and
apply action `rebuild` with the same scope only for generated index, manifest,
log, or compatibility-view drift while canonical sources are current. Every
apply carries the worktree `repo_root`, the complete
returned `plan`, `plan_hash`, and `expected_snapshot`. Review the proposed
operations before each apply, then inspect the durable concept and generated
compatibility view. The durable concept carries stable identity and curated
links; status, PRS, backlinks, indexes, and compatibility views are generated.
Never hand-edit the compatibility view or its sentinel zones.

### 7. Commit and Verify (IN the Worktree)

All commits happen on the worktree branch — NEVER on main.

```text
1. Run final `knowledge-health` in the worktree with scope
   `projects/<roadmap-slug>/specs`. Require the promoted spec map, generated
   indexes, source hashes, and SPEC-MOC compatibility view to be current. Stop
   before commit if health is not clean.

2. Stage and commit the technical roadmap, design concept doc, workflow file, canonical spec-map
   concept, generated indexes, and SPEC-MOC compatibility view (the view is a
   review-visible projection — if it is
   written but left untracked it never reaches the PR). From the worktree, add
   `<roadmap-path-from-step-1>`,
   `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`,
   `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, and
   `docs/ai/knowledge/index.md`, `log.md`, `manifest.json`,
   `docs/ai/knowledge/projects/<roadmap-slug>/`, and
   `specs/<branch-name>/SPEC-MOC.md`, then commit with
   `chore(SPEC-XXX): add design concept and workflow for autopilot`.

3. Push the WORKTREE BRANCH:
   From `.worktrees/<number>-<short-name>/`, run `git push`.

4. Verify:
   - Read the design concept doc — must contain Goals, Non-goals,
     Q&A log, and Open Questions sections.
   - Read the workflow file back — no placeholders remain, and the
     Specify/Clarify Prompts contain content traceable to the
     design concept's Q&A log.
   - From the worktree, run `git rev-parse --abbrev-ref HEAD`
     → must show the spec branch, NOT main
   - From the worktree, run `git log --oneline -1`
     → must show the design-concept-and-workflow commit
```

Report:

```text
## Scaffold Complete

**Spec:** SPEC-009 Search & Database
**Branch:** 009-search-database
**Worktree:** .worktrees/009-search-database/
**Design Concept:** .worktrees/009-search-database/docs/ai/specs/.process/SPEC-009-design-concept.md
**Workflow:** .worktrees/009-search-database/docs/ai/specs/.process/SPEC-009-workflow.md
**Remote:** Pushed to <remote>/009-search-database
**Bootstrap:** <commands run, documented health check, or "no documented bootstrap">

**Ready to run:**
/speckit-pro:speckit-autopilot docs/ai/specs/.process/SPEC-009-workflow.md

**Review both files first** — the design concept doc captures the
decisions you made during grill-me; the workflow file is what the
autopilot will execute. Verify the phase prompts have enough context
for autonomous execution.
```

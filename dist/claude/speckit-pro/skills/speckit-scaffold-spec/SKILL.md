---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Creates the git worktree, spec branch, Design Concept doc, and populated workflow file ready for autopilot. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
argument-hint: "SPEC-ID (e.g., SPEC-009)"
user-invocable: true
allowed-tools: Bash Read Edit Write Skill Agent
license: MIT
---

# SpecKit Scaffold Spec

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
`specs/<parent>/<child>` directories. Child `SPEC-MOC.md` frontmatter keeps
`up:` pointed at the roadmap. Add only curated body links to the parent
manifest and shared design concept; add retrospective links only after the
retrospective exists. Do not create child branches or worktrees automatically
from the parent scaffold — each child is scaffolded independently.

Before presenting O5 as ready, validate the manifest with:

```text
Bash("${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/scripts/o5-topology.sh specs/<parent-branch>")
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

For the one eligible thawed candidate, print these exact commands with the real
`specs/<spec-dir>` value substituted:

```text
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/<spec-dir> --repo-root .
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/<spec-dir> --repo-root .
```

Frame `--apply` as a follow-up only after the operator reviews clean dry-run
output and has a clean worktree. Never invoke
`relocate-process-artifacts.sh --dry-run` or
`relocate-process-artifacts.sh --apply` from scaffold.

## Invocation

```text
/speckit-pro:speckit-scaffold-spec SPEC-009
/speckit-pro:speckit-scaffold-spec SPEC-008
```

## What to Do

### 0. Ensure SpecKit CLI

Check for the official SpecKit CLI before parsing or mutating the repository:

```text
Bash("PATH=\"${HOME:+$HOME/.local/bin:}/opt/homebrew/bin:/usr/local/bin:${PATH:-}\"; command -v specify")
```

If missing and `uv` exists, install it:

```text
Bash("uv tool install specify-cli --from git+https://github.com/github/spec-kit.git")
```

If `uv` is unavailable or install fails, STOP and tell the operator to install
SpecKit with that command. Do not run `specify init --here --force`
automatically; recommend it only when `.specify/` is absent and the operator
explicitly approves project initialization.

### 1. Find the Technical Roadmap

```text
Glob("**/*technical*roadmap*" or "**/*technical-roadmap*")
Also check: docs/ai/*roadmap*.md, docs/ai/specs/*roadmap*.md
```

If no technical roadmap found, STOP: "No technical roadmap found. Create
one with `/speckit-pro:speckit-coach help me create a technical roadmap`."

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
Bash("${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/scripts/reviewability-gate.sh setup <technical-roadmap-path>")
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
   Bash("mkdir -p .worktrees/<number>-<short-name>/docs/ai/specs/.process/")

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
0. Install or refresh the generic speckit-pro reviewability preset:
   Bash("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/ensure-reviewability-preset.sh .worktrees/<number>-<short-name> ${CLAUDE_PLUGIN_ROOT} speckit-pro-reviewability")

   If status is installed, commit .specify/presets/speckit-pro-reviewability
   and .specify/presets/.registry with the setup artifacts.

   Verify resolution from the worktree:
   Bash("cd .worktrees/<number>-<short-name> && specify preset resolve spec-template")
   Bash("cd .worktrees/<number>-<short-name> && specify preset resolve plan-template")
   Bash("cd .worktrees/<number>-<short-name> && specify preset resolve tasks-template")

1. Read the workflow template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/workflow-template.md")

2. Write the template to the WORKTREE:
   Write(".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-workflow.md",
         content: <template content from step 1>)
```

### 5.5. Write the SPEC-MOC Marker (IN the Worktree)

Write a minimal `SPEC-MOC.md` navigation marker into the spec's CONTRACT
directory on EVERY new spec, regardless of how many slices it will ultimately
have (single-slice specs get the marker too — it is the version-gate carrier).

This marker is a CONTRACT artifact: it is written to `specs/<branch-name>/` —
NOT redirected to `.process/`, and NOT written to `docs/ai/specs/`. The
directory is named from the branch (NOT auto-numbered), so its `spec_id`
namespace-matches the directory.

```text
1. Create the spec's contract directory in the WORKTREE (scaffold owns this
   early creation; mkdir -p is a no-op if it already exists):
   Bash("mkdir -p .worktrees/<number>-<short-name>/specs/<branch-name>/")

2. Read the spec-MOC template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/spec-moc-template.md")

3. Token-substitute the template (same {{TOKEN}} mechanism as the workflow
   template) and write it to the contract directory:
   Write(".worktrees/<number>-<short-name>/specs/<branch-name>/SPEC-MOC.md",
         content: <template with the tokens below substituted>)

   | Token | Replace With |
   | ----- | ------------ |
   | `{{ROADMAP_TITLE}}` | a short link text for the roadmap (e.g., the spec series name + " roadmap") |
   | `{{ROADMAP_FILENAME}}` | the existing `*-technical-roadmap.md` filename WITHOUT the `.md` extension (from Step 1) |
   | `{{SPEC_ID}}` | the roadmap identity, e.g., `PRSG-002` (must namespace-match `<branch-name>`) |
```

The written marker MUST carry:

- a non-empty, quoted relative `up:` markdown link pointing at the existing
  `*-technical-roadmap.md` — from `specs/<branch-name>/` this resolves as
  `../../docs/ai/specs/<roadmap-filename>.md` (the `../../docs/ai/specs/`
  prefix is hardcoded in the template; only the filename is tokenized), NEVER
  a `[[wikilink]]`;
- `structureVersion: 1` (carried verbatim from the template, with its "keep in
  sync with the lint scripts' hardcoded literal" comment); and
- a `spec_id` that namespace-matches the contract directory name.

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

### 7. Commit and Verify (IN the Worktree)

All commits happen on the worktree branch — NEVER on main.

```text
1. Stage and commit the design concept doc, the workflow file, AND the
   SPEC-MOC marker (the marker is a review-visible CONTRACT artifact — if it is
   written but left untracked it never reaches the PR):
   Bash("cd .worktrees/<number>-<short-name> && \
     git add docs/ai/specs/.process/SPEC-<ID>-design-concept.md \
             docs/ai/specs/.process/SPEC-<ID>-workflow.md \
             specs/<branch-name>/SPEC-MOC.md && \
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
## Scaffold Complete

**Spec:** SPEC-009 Search & Database
**Branch:** 009-search-database
**Worktree:** .worktrees/009-search-database/
**Design Concept:** .worktrees/009-search-database/docs/ai/specs/.process/SPEC-009-design-concept.md
**Workflow:** .worktrees/009-search-database/docs/ai/specs/.process/SPEC-009-workflow.md
**Remote:** Pushed to <remote>/009-search-database

**Ready to run:**
/speckit-pro:speckit-autopilot docs/ai/specs/.process/SPEC-009-workflow.md

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

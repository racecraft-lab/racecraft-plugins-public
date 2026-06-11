---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Creates the git worktree, spec branch, Design Concept doc, and populated workflow file ready for autopilot. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
---

# SpecKit Scaffold Spec

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
skills/speckit-autopilot/scripts/o5-topology.sh specs/<parent-branch>
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
`relocate-process-artifacts.sh --apply` from `$speckit-scaffold-spec`.

> **Codex implicit-trigger note (eval harness vs production):** Layer 2 trigger evals score this skill at 69% (11/16) on the Codex selector — but POS is a perfect 8/8 (every "scaffold SPEC-009" / "create a new spec branch" / "prep SPEC-022 for autopilot" query fires correctly). All 5 NEG misses are false-positives in single-skill staging where the harness loads only this skill, so the Codex selector has no alternative to route adjacent SDD queries to ("roadmap status" / "what's the progress on SPEC-009" → should go to `$speckit-status`, "run the fully populated workflow" → `$speckit-autopilot`, "resolve PR review comments" → `$speckit-resolve-pr`). In production all six speckit-pro skills are loaded together and Codex routes those queries to their proper destinations. The eval results under-report real-world accuracy; positive-trigger reliability is the operationally-relevant number. (This skill was renamed from `speckit-setup` in v1.12; the rename did not regress trigger behavior — same POS pass rate as before.)

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
- Use the shared workflow template shipped with this plugin. Locate it at
  `skills/speckit-coach/templates/workflow-template.md` relative to the
  speckit-pro plugin root directory.
- Do not leave placeholder tokens such as `SPEC_ID`, `SPEC_NAME`, or empty
  phase prompts in the generated workflow.
- Do not run the autopilot at the end. Setup stops once the workflow is ready,
  committed, and pushed.
- Always run the `$grill-me` interview before writing the workflow file. The
  Design Concept doc is a required setup output, not optional. Setup must not
  attempt to fabricate design-concept content if grill-me aborts.

## Procedure

### 0. Ensure SpecKit CLI

Before parsing or mutating the repository, verify the official SpecKit CLI is
available:

```text
command -v specify
```

If it is missing and `uv` is available, install it:

```text
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

If `uv` is unavailable or installation fails, stop and report the exact install
command for the operator to run. Do not continue with setup without the
`specify` command.

Do not run `specify init --here --force` automatically. Project initialization
and forced refreshes can overwrite managed files; setup may recommend the
command when `.specify/` is missing, but it must not run it without explicit
operator approval.

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

Before creating the worktree, run the reviewability setup gate against the
roadmap or extracted spec entry:

```text
skills/speckit-autopilot/scripts/reviewability-gate.sh setup <technical-roadmap-path>
```

If the gate returns `block` without a ratified split exception, stop setup and
tell the user which threshold requires decomposition. Warnings may proceed only
when the generated workflow records the budget result and split decision.

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

Place worktrees under `.worktrees/` at the repository root by default. The
full worktree path should follow the pattern `.worktrees/<number>-<short-slug>`,
for example `.worktrees/009-search-database`. Use a different root only if the
user provides an explicit override.

### 4. Run the Grill Me interview (in the worktree)

Before writing the workflow file, run an iterative scoping interview so the
Specify and Clarify prompts can be enriched from human-validated answers. Use
the spec scope description from the technical roadmap (and any constraints,
dependencies, or stated tools) as the input.

Invoke `$grill-me` from inside the worktree with a setup-mode marker so it
knows to:

- Write its Design Concept doc to
  `docs/ai/specs/.process/SPEC-<ID>-design-concept.md` inside the worktree
- Surface the key answers (Goals, Non-goals, major design decisions) back to
  this skill so step 6 can fold them into the workflow prompts

Codex grill-me uses a picker-first HITL guard: it must call
`request_user_input` for each Grill Me question. In Codex Default mode this
requires the `default_mode_request_user_input` feature to be enabled before the
thread starts or resumes. Do not ask the Grill Me question as a normal assistant
message, progress update, or final response. If `request_user_input` is absent
or unavailable, stop setup and tell the user to run
`codex features enable default_mode_request_user_input`, restart Codex or open a
new thread, then rerun `$speckit-scaffold-spec <SPEC-ID>`. A nonzero shell
`tty -s` result is not enough to stop a live Codex conversation, but a missing
native picker is a config prerequisite failure. Do not try to drive grill-me from
`codex exec` or any non-interactive runner — it will refuse and write nothing.

If grill-me aborts (no interactive runtime), stop setup and report the
condition. Do not synthesize design-concept content yourself.

### 5. Copy the workflow template into the worktree

Before copying the workflow template, install or refresh the generic
speckit-pro reviewability preset inside the worktree:

```text
skills/speckit-coach/scripts/ensure-reviewability-preset.sh <worktree-path> <plugin-root> speckit-pro-reviewability
```

This script generates `.specify/presets/speckit-pro-reviewability/` from the
host project's current core templates and then adds reviewability budget and PR
review packet requirements. Commit the resulting preset files on the spec
branch when the script reports `status: installed`.

After installation, verify template resolution from the worktree:

```text
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Each command should resolve to `.specify/presets/speckit-pro-reviewability/`
or to a project-specific higher-priority override that intentionally includes
the reviewability sections.

Create the destination directory inside the worktree, typically
`docs/ai/specs/.process/` (created when absent so the first exhaust artifact
lands correctly), then load the shared workflow template from the plugin. Do
not author a new template from scratch. The generated file should live at a
path like `docs/ai/specs/.process/SPEC-009-workflow.md` inside the worktree.

### 5.5. Write the SPEC-MOC marker (in the worktree)

Write a minimal `SPEC-MOC.md` navigation marker into the spec's CONTRACT
directory on EVERY new spec, regardless of how many slices it will ultimately
have (single-slice specs get the marker too — it is the version-gate carrier).

This marker is a CONTRACT artifact: write it to `specs/<branch-name>/SPEC-MOC.md`
— NOT redirected to `.process/`, and NOT written to `docs/ai/specs/`. Create the
contract directory if it is absent (`mkdir -p specs/<branch-name>/`); scaffold
owns this early creation. Name the directory from the branch (NOT auto-numbered)
so the `spec_id` namespace-matches the directory.

Load the shared spec-MOC template from the plugin at
`skills/speckit-coach/templates/spec-moc-template.md` (the template is a single
shared, runtime-agnostic copy — do NOT duplicate it under `codex-skills/`).
Token-substitute it with the same `{{TOKEN}}` mechanism used for the workflow
template:

- `{{ROADMAP_TITLE}}` — a short link text for the roadmap (e.g., the spec series
  name + " roadmap")
- `{{ROADMAP_FILENAME}}` — the existing `*-technical-roadmap.md` filename without
  the `.md` extension
- `{{SPEC_ID}}` — the roadmap identity, e.g., `PRSG-002` (must namespace-match
  `<branch-name>`)

The written marker MUST carry a non-empty, quoted relative `up:` markdown link
pointing at the existing `*-technical-roadmap.md` — from `specs/<branch-name>/`
this resolves as `../../docs/ai/specs/<roadmap-filename>.md` (the
`../../docs/ai/specs/` prefix is hardcoded in the template; only the filename is
tokenized), NEVER a `[[wikilink]]` — plus `structureVersion: 1` (carried verbatim
from the template, with its "keep in sync with the lint scripts' hardcoded
literal" comment) and a `spec_id` that namespace-matches the contract directory.

### 6. Populate the workflow file

Replace all placeholders using the roadmap data. At minimum populate:

- `SPEC_ID`
- `SPEC_NAME`
- `BRANCH_NAME`
- tool count and tool names if the roadmap provides them

Then seed each phase prompt with concrete, spec-specific context rather than a
generic placeholder. Use **both** the roadmap scope/dependencies and the
Design Concept doc produced in step 4 (`SPEC-<ID>-design-concept.md`) to fill:

- Specify prompt — fold in Goals, Non-goals, and the user-validated design
  decisions from the Q&A log
- Clarify session focus areas — pull from the Open Questions section of the
  design concept
- Plan prompt — combine CLAUDE.md tech stack, constitution, roadmap scope,
  AND architecture/data-model/constraint decisions extracted from the design
  concept Q&A log. Quote the chosen answer for any decision driving a
  planning choice. Reference the design concept doc path as well.
- Checklist domain suggestions — based on roadmap scope plus the design tree
  branches the grill-me interview walked
- Tasks prompt — reference spec.md, plan.md, AND the design concept doc.
  Use Non-goals to bound task generation; use Q&A "why" context to inform
  task ordering and TDD test specifications.
- Analyze prompt — cross-artifact consistency check across spec.md, plan.md,
  tasks.md, AND the design concept doc. Flag drift between Goals / Non-goals /
  decisions and downstream artifacts. The design concept is the source of
  truth for scoping decisions captured during grill-me.
- Implement prompt — reference tasks.md, plan.md, AND the design concept
  doc. Consult the Q&A log for the "why" behind decisions; this informs
  test specifications, edge-case handling, and refactor choices.

The prompts should be strong enough that `$speckit-autopilot` can execute
without the user hand-editing obvious missing context. The design concept is
the primary enrichment layer; the roadmap scope is the seed. If a critical
detail cannot be derived from either, stop and report the gap rather than
filling it with fiction.

### 7. Commit and push from the worktree

Stage the generated/updated preset files when present, plus the design concept
doc, the workflow file, AND the SPEC-MOC marker in the worktree branch (the
marker is a review-visible CONTRACT artifact — if it is written but left
untracked it never reaches the PR). Create a focused setup commit and push that
branch to the detected remote:

```
git add .specify/presets/speckit-pro-reviewability \
        .specify/presets/.registry \
        docs/ai/specs/.process/SPEC-<ID>-design-concept.md \
        docs/ai/specs/.process/SPEC-<ID>-workflow.md \
        specs/<branch-name>/SPEC-MOC.md
git commit -m 'chore(SPEC-XXX): add design concept and workflow for autopilot'
```

If the preset was already present and unchanged, the add command may include
only the design concept, the workflow, and the marker:

```
git add docs/ai/specs/.process/SPEC-<ID>-design-concept.md \
        docs/ai/specs/.process/SPEC-<ID>-workflow.md \
        specs/<branch-name>/SPEC-MOC.md
git commit -m 'chore(SPEC-XXX): add design concept and workflow for autopilot'
```

Then verify:

- both files exist in the worktree
- placeholders are gone from the workflow file
- `git rev-parse --abbrev-ref HEAD` shows the spec branch
- `git log --oneline -1` shows the setup commit

### 8. Update roadmap status in the worktree

Update the technical roadmap copy inside the worktree to mark the spec as in
progress. Commit and push that roadmap status change on the same spec branch.
Do not touch the main checkout. The roadmap change reaches the default branch
only when the spec branch is merged.

## Output

Finish with a concise scaffold report that includes:

- the spec name and ID
- branch name
- worktree path
- design concept path
- workflow path
- remote branch that was pushed
- the exact next step: run `$speckit-autopilot` with the generated
  workflow file (Codex skills are invoked via `$skill-name`, not via
  any `/<plugin>:<skill>` slash command — see openai/codex#7480)

## Failure Handling

Stop instead of improvising when any of the following are true:

- no technical roadmap exists
- the SPEC-ID is not in the roadmap
- the branch or worktree state is ambiguous and cannot be safely reused
- git push fails
- the workflow still contains unresolved placeholders after population
- `$grill-me` aborts because no interactive runtime is available (e.g.,
  invoked from `codex exec` or a CI runner). Scaffolding is HITL-gated by design.

If scaffolding partially succeeds before a failure, report exactly what was created
and what remains unfinished so the user can resume without duplicating work.

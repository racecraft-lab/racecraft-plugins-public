---
title: "First Run"
description: "Walk through your first SpecKit Pro run on Claude Code or Codex and recognize success by the artifact trail it produces, not a merged pull request."
---

Use this route after installing SpecKit Pro for Claude Code or Codex. The first
successful run is not a merged pull request. Success is a visible artifact
trail: PRD, roadmap entry, scaffolded workflow and spec folder, autopilot phase
artifacts, and a validation checkpoint.

## Start From The Right Install Path

Complete the install route for your agent before starting this tutorial:

- [Install SpecKit Pro for Claude Code](/racecraft-plugins-public/install/claude-code/) when your commands use `/speckit-pro:<skill>`.
- [Install SpecKit Pro for Codex](/racecraft-plugins-public/install/codex/) when your commands use `$speckit-*` skills.
- [Choose your platform path](/racecraft-plugins-public/choose-your-path/) when you are not sure which surface applies.

Do not mix command surfaces. Claude Code plugin skills use
`/speckit-pro:<skill>`. Codex skills use `$speckit-*`.

## Check Prerequisites

Run or inspect these checks from the repository where you want the workflow
artifacts to live.

| Check | Command or action | Expected signal | Bounded fallback |
|---|---|---|---|
| Spec Kit CLI exists | `command -v specify` | A path to the `specify` executable | Return to the platform install page and confirm Spec Kit setup before continuing. |
| Spec Kit CLI version | `specify version` | A version report from the installed CLI | Compare the local output with the install route and pause before documenting new command behavior. |
| Constitution exists | `test -f .specify/memory/constitution.md` | Exit status 0 | Inspect the repo's Spec Kit project setup and use the platform install route for setup context. |
| Roadmap has the SPEC-ID | Review `docs/ai/specs/*.md` or run the project status skill | A roadmap row for the target SPEC-ID | Return to PRD or roadmap creation before scaffolding a SPEC. |
| GitHub CLI exists | `command -v gh` | A path to `gh` | Continue only with local artifacts, or install GitHub CLI before PR creation. |
| GitHub CLI version | `gh --version` | A version report from `gh` | Treat PR creation as out of scope until the CLI is available. |
| `jq` exists | `command -v jq` | A path to `jq` | Pause validation scripts that parse JSON until `jq` is available. |
| `jq` version | `jq --version` | A version string | Record the missing version in validation notes before continuing. |
| Current branch | `git rev-parse --abbrev-ref HEAD` | A feature branch or worktree branch | Inspect branch state before scaffolding or running autopilot. |
| Clean starting point | `git status --short` | No unrelated changes | Record unrelated work before starting so the tutorial artifacts remain reviewable. |

For a new Codex Spec Kit project, current local CLI evidence supports this
skills-mode initialization form:

```bash
specify init --here --integration codex --integration-options="--skills" --script sh
```

Use the [Codex install guide](/racecraft-plugins-public/install/codex/) for the
full Codex setup path. Claude Code setup is separate and belongs in the
[Claude Code install guide](/racecraft-plugins-public/install/claude-code/).

## Know The Skill Roles

| Role | Claude Code | Codex | Use it when |
|---|---|---|---|
| Scoping interview | `/speckit-pro:grill-me` | `$grill-me` | You need one decision at a time before a spec is written. |
| PRD and roadmap | `/speckit-pro:speckit-prd` | `$speckit-prd` | You have a broad idea and need a PRD plus SPEC catalog. |
| SPEC scaffold | `/speckit-pro:speckit-scaffold-spec DOC-005` | `$speckit-scaffold-spec DOC-005` | A SPEC exists in the roadmap and needs a worktree plus workflow file. |
| Autopilot | `/speckit-pro:speckit-autopilot docs/ai/specs/.process/DOC-005-workflow.md` | `$speckit-autopilot docs/ai/specs/.process/DOC-005-workflow.md` | The workflow file is ready to run through the SpecKit phases. |
| Status check | `/speckit-pro:speckit-status` | `$speckit-status` | You need the current roadmap, active spec, archive sweep, or next step. |

## Walk The First Artifact Trail

### 1. Capture The Idea

Start with the smallest idea that still needs structure: a user problem, a
support issue, a feature request, or a transcript.

| Claude Code | Codex |
|---|---|
| `/speckit-pro:grill-me docs/raw-idea.md` | `$grill-me docs/raw-idea.md` |

**Checkpoint:** You have a short decision log or enough answers to create a
PRD.

**Next action:** Move from scoping to PRD and roadmap creation.

### 2. Create The PRD And Roadmap Entry

Turn the idea into a PRD and a SPEC catalog entry. The roadmap entry becomes
the source of truth for the SPEC-ID used by scaffold and autopilot.

| Claude Code | Codex |
|---|---|
| `/speckit-pro:speckit-prd "first successful workflow tutorial"` | `$speckit-prd "first successful workflow tutorial"` |

**Checkpoint:** The artifact trail includes a PRD, a technical roadmap, and a
SPEC-ID such as `DOC-005`.

**Next action:** Confirm the SPEC-ID is ready, then scaffold that SPEC.

### 3. Scaffold One SPEC

Scaffold prepares the feature branch or worktree, design concept, workflow
file, spec folder, and `SPEC-MOC.md` for one roadmap item.

| Claude Code | Codex |
|---|---|
| `/speckit-pro:speckit-scaffold-spec DOC-005` | `$speckit-scaffold-spec DOC-005` |

**Checkpoint:** Look for these artifacts:

- `docs/ai/specs/.process/DOC-005-design-concept.md`
- `docs/ai/specs/.process/DOC-005-workflow.md`
- `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/SPEC-MOC.md`
- `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/spec.md`

**Next action:** Start autopilot with the generated workflow file.

### 4. Run Autopilot Through The Phases

Autopilot executes the workflow in gated phases. It should produce phase
artifacts before implementation starts.

| Claude Code | Codex |
|---|---|
| `/speckit-pro:speckit-autopilot docs/ai/specs/.process/DOC-005-workflow.md` | `$speckit-autopilot docs/ai/specs/.process/DOC-005-workflow.md` |

**Checkpoint:** The artifact trail grows as each gate completes:

- `spec.md` after specify and clarify
- `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` after plan
- `checklists/*.md` after checklist
- `tasks.md` after tasks
- `docs/ai/specs/.process/autopilot-state.json` as the run state
- PR packet evidence under `specs/<feature>/.process/pr-packets/`

**Next action:** Use the
[Spec Kit lifecycle](/racecraft-plugins-public/spec-kit-lifecycle/) page to
understand any phase or gate before continuing.

### 5. Validate The First Success

For DOC-005-style docs work, validation is the docs-site check plus manual
review evidence.

```bash
cd docs-site
pnpm validate
pnpm validate:links
```

**Checkpoint:** The validation output and manual review notes are recorded in
the feature's PR packet. The first run is successful when the artifacts and
validation evidence are visible, even before a PR is merged.

**Next action:** Prepare the review packet or use the status skill to inspect
what remains.

## Bounded Pause Points

These are short first-run checks, not full troubleshooting procedures.

| State | Inspect | Next action |
|---|---|---|
| Missing roadmap entry | PRD output, `docs/ai/specs/*.md`, and `$speckit-status` or `/speckit-pro:speckit-status` | Return to PRD or roadmap creation so the SPEC-ID exists before scaffold. |
| Missing scaffold output | Scaffold chat output, design concept path, workflow path, and `SPEC-MOC.md` | Re-open the scaffold evidence and confirm the roadmap target before continuing. |
| Partial autopilot output | `autopilot-state.json`, phase artifacts, checklists, tasks, and PR packet evidence | Continue from the phase named in the state file after recording what already exists. |
| Failed validation checkpoint | The validation command output and changed docs files | Record the failing check in the PR packet and use the troubleshooting route for deeper diagnosis. |

For deeper command reference, use the generated
[skills](/racecraft-plugins-public/reference/skills/) page. For validation
surface detail, use [scripts](/racecraft-plugins-public/reference/scripts/) and
[tests](/racecraft-plugins-public/reference/tests/). For deeper diagnosis, use
[troubleshooting orientation](/racecraft-plugins-public/troubleshooting/).
For platform trust questions, use
[security and trust orientation](/racecraft-plugins-public/security-and-trust/).

## Source Evidence And Boundaries

This page is grounded in:

- [docs/prd-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/prd-interactive-documentation.md)
- [docs/roadmap-interactive-documentation.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs/roadmap-interactive-documentation.md)
- [speckit-pro/README.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/README.md)

This route owns the first successful workflow tutorial. It links to later
reference, selector, troubleshooting, and trust work instead of duplicating
those deeper pages.

---
name: speckit-install
description: "Installs the official SpecKit CLI and initializes one or both coding-agent integrations (Claude Code, Codex CLI). Detects existing installs and hands off to /speckit-pro:speckit-upgrade rather than overwriting. Optionally installs the curated set of community extensions and presets. Use when the user says \"install speckit\", \"set up speckit\", \"initialize speckit\", \"add speckit to this repo\", \"install spec-kit\", \"bootstrap speckit\", \"first-time speckit setup\", \"install the specify cli\", \"set up specify\", or wants to install for claude only, codex only, or both side-by-side. Not for upgrading an existing install (use /speckit-pro:speckit-upgrade) or running workflows (use /speckit-pro:speckit-autopilot)."
argument-hint: "(optional) integration keys, e.g. 'claude', 'codex', or 'claude codex'"
user-invocable: true
allowed-tools: Read Edit Write
license: MIT
---

# SpecKit Install

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-install/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

Install the SpecKit CLI (if missing) and initialize this repository
to use it with Claude Code, Codex CLI, or both. Safe to run on any
repo — detects existing installs and hands off to
`/speckit-pro:speckit-upgrade` rather than overwriting them.

## Invocation

```text
/speckit-pro:speckit-install                    # interactive — asks which integrations
/speckit-pro:speckit-install claude             # claude only
/speckit-pro:speckit-install codex              # codex only
/speckit-pro:speckit-install claude codex       # both (dual-integration)
```

## What to Do

### 1. Ensure the SpecKit CLI is on PATH

Use command execution to check whether `specify --version` succeeds after
including common user-local binary directories on PATH.

- If the output begins with `specify`, the CLI is installed. Capture the
  version and move on.
- If the CLI is missing:
  - Check whether `uv` is available.
  - If `uv` is present, install with `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
  - If `uv` is missing, STOP and instruct the operator to install `uv`
    from the official Astral documentation, then re-run
    `/speckit-pro:speckit-install`.

### 2. Detect existing-install state

Inspect whether `.specify/` exists and record the state as `PRESENT` or
`ABSENT`.

If `.specify/` is **PRESENT**:
- Run `specify integration list` to see which integrations are already
  installed.
- Tell the operator: "This repo already has SpecKit installed
  (integrations: `<list>`). Use `/speckit-pro:speckit-upgrade` to upgrade
  safely, or add a new integration alongside the existing ones with
  `specify integration install <key>`."
- Ask whether to (a) hand off to `/speckit-pro:speckit-upgrade`, (b) add a
  new integration alongside the existing ones, or (c) abort.
- If (a): STOP and invoke `/speckit-pro:speckit-upgrade`.
- If (b): skip Step 3's `specify init`, go straight to Step 4 with
  the operator's chosen integrations.
- If (c): STOP.

If `.specify/` is **ABSENT**: continue to Step 3.

### 3. Ask which integrations to install

If the operator passed integration keys as arguments (e.g.,
`/speckit-pro:speckit-install claude codex`), use those. Otherwise ask:

> Which coding-agent integrations should this project support?
> - `claude` — Claude Code (installs skills at `.claude/skills/speckit-*/`)
> - `codex` — Codex CLI (installs skills at `.codex/skills/speckit-*/`)
> - `both`  — dual-integration (Claude AND Codex side-by-side)

Both Claude and Codex are declared "Multi-install Safe" by the
SpecKit CLI, so dual-integration is officially supported. The
plugin's own skills (`$speckit-coach`, `$speckit-autopilot`, etc.)
work in both runtimes.

### 4. Initialize the repository

For a **fresh install** (Step 2 said ABSENT):

- Run `specify init --here --integration <first-key>` to scaffold
  `.specify/` (templates, scripts, constitution placeholder) AND
  install the first integration.
- For each additional integration the operator chose, run
  `specify integration install <key>`.

For **adding to an existing install** (Step 2 said PRESENT, operator
chose option (b)):

- For each new integration the operator chose, run
  `specify integration install <key>`.

Pass `--script sh` explicitly on macOS/Linux to avoid prompting.

### 5. Offer to install the curated set of extensions and presets

speckit-pro recommends a small set of community extensions and presets
that power the autopilot's post-implementation parallel group and the
native AskUserQuestion picker on `/speckit-clarify` and `/speckit-checklist`.
See [presets-extensions-guide.md → The curated set](../speckit-coach/references/presets-extensions-guide.md)
for the full list and rationale.

Compare `.specify/extensions/` and `.specify/presets/` against the entries
in `${CLAUDE_PLUGIN_ROOT}/scripts/curated-set.json`.

- If every entry is present: report "Curated extensions and presets already
  installed — nothing to install." Continue to Step 6.

- Otherwise, list the missing entries and ask which to install. Recommended
  default is **all**. For each accepted entry, give the operator the
  `specify extension add <id>` or preset command from the curated set and
  run it only after they confirm. Skipped entries can be installed later
  with `/speckit-pro:speckit-upgrade`.

### 6. Verify and report

Run `specify check` and `specify integration list`.
Report to the operator:

- Installed SpecKit CLI version.
- Each integration that was installed and its artifact path.
- The constitution placeholder at `.specify/memory/constitution.md` —
  next step is `/speckit-pro:speckit-coach create my project constitution`
  or `/speckit-constitution` (or `$speckit-coach` / `$speckit-constitution`
  in Codex).
- A reminder to **restart the coding-agent process** (Claude Code or
  Codex CLI) so the newly installed skills/commands are picked up.

## Hard Constraints

- Never run `specify init --here --force` from this command. `--force`
  overwrites existing customizations. The upgrade command is the
  only place that handles `--force` (with backup/restore).
- Never proceed to Step 4 without explicit operator confirmation of
  the integration choice when there's ambiguity.
- Never mutate `.specify/memory/constitution.md` — that's the
  operator's content. If they don't have one yet, leave the SpecKit
  placeholder in place and tell them how to fill it.
- If `specify init` fails (e.g., network error fetching templates),
  STOP and report the exact error. Do not partially-install or
  retry silently.

## Failure Handling

Stop and report — do not improvise — when:

- `uv` is missing and the operator cannot install it.
- `specify init` returns a non-zero exit code.
- `specify integration install <key>` fails (the operator may have a
  conflicting integration; surface the CLI's error message and let
  them decide).
- The repo has detached HEAD or uncommitted changes that would
  conflict with the new files. Recommend committing or stashing
  first.

## Why This Skill

The SpecKit CLI's `specify init` and `specify integration install`
commands are the canonical install path. This skill wraps them so
the user gets:

- A consistent up-front check for `uv` and the CLI.
- A clean state-detection step that hands off to `/speckit-pro:speckit-upgrade`
  for already-installed repos (no accidental overwrites).
- An explicit prompt for dual-integration setup, which the CLI
  supports natively (both `claude` and `codex` are marked
  "Multi-install Safe").
- An interactive offer to install recommended community extensions and presets
  with native Spec Kit commands after operator confirmation.
- A consistent post-install summary so the operator knows what to
  do next.

For upgrading an existing install (including the v0.8.13 migration
from slash commands to skills, or moving from single- to
dual-integration), use `/speckit-pro:speckit-upgrade` instead.

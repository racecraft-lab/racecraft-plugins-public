---
description: Install the SpecKit CLI and initialize this repository for one or both coding-agent integrations (Claude Code, Codex CLI). If SpecKit is already installed in this repo, hands off to /speckit-pro:upgrade. Asks which integrations you want before mutating anything.
allowed-tools: Bash Read Edit Write
argument-hint: "(optional) integration keys, e.g. 'claude', 'codex', or 'claude codex'"
---

# SpecKit Install

Install the SpecKit CLI (if missing) and initialize this repository
to use it with Claude Code, Codex CLI, or both. Safe to run on any
repo — detects existing installs and hands off to
`/speckit-pro:upgrade` rather than overwriting them.

## Invocation

```text
/speckit-pro:install                    # interactive — asks which integrations
/speckit-pro:install claude             # claude only
/speckit-pro:install codex              # codex only
/speckit-pro:install claude codex       # both (dual-integration)
```

## What to Do

### 1. Ensure the SpecKit CLI is on PATH

```text
Bash("command -v specify >/dev/null 2>&1 && specify --version || echo MISSING")
```

- If the output begins with `specify`, the CLI is installed. Capture the
  version and move on.
- If the output is `MISSING`:
  - Check for `uv`: `Bash("command -v uv")`.
  - If `uv` is present, install: `Bash("uv tool install specify-cli --from git+https://github.com/github/spec-kit.git")`.
  - If `uv` is missing, STOP and instruct the operator: "Install `uv`
    first — https://docs.astral.sh/uv/#installation. Then re-run
    `/speckit-pro:install`."

### 2. Detect existing-install state

```text
Bash("test -d .specify && echo PRESENT || echo ABSENT")
```

If `.specify/` is **PRESENT**:
- Run `Bash("specify integration list 2>&1 | head -40")` to see which
  integrations are already installed.
- Tell the operator: "This repo already has SpecKit installed
  (integrations: `<list>`). Use `/speckit-pro:upgrade` to upgrade
  safely, or add a new integration alongside the existing ones with
  `specify integration install <key>`."
- Ask whether to (a) hand off to `/speckit-pro:upgrade`, (b) add a
  new integration alongside the existing ones, or (c) abort.
- If (a): STOP and invoke `/speckit-pro:upgrade`.
- If (b): skip Step 3's `specify init`, go straight to Step 4 with
  the operator's chosen integrations.
- If (c): STOP.

If `.specify/` is **ABSENT**: continue to Step 3.

### 3. Ask which integrations to install

If the operator passed integration keys as arguments (e.g.,
`/speckit-pro:install claude codex`), use those. Otherwise ask:

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

### 5. Verify and report

Run `Bash("specify check 2>&1")` and `Bash("specify integration list 2>&1")`.
Report to the operator:

- Installed SpecKit CLI version.
- Each integration that was installed and its artifact path.
- The constitution placeholder at `.specify/memory/constitution.md` —
  next step is `/speckit-pro:coach create my project constitution`
  or `/speckit.constitution` (or `$speckit-coach` / `$speckit-constitution`
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
- A clean state-detection step that hands off to `/speckit-pro:upgrade`
  for already-installed repos (no accidental overwrites).
- An explicit prompt for dual-integration setup, which the CLI
  supports natively (both `claude` and `codex` are marked
  "Multi-install Safe").
- A consistent post-install summary so the operator knows what to
  do next.

For upgrading an existing install (including the v0.8.13 migration
from slash commands to skills, or moving from single- to
dual-integration), use `/speckit-pro:upgrade` instead.

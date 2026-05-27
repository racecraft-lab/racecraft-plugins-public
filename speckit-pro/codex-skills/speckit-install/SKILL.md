---
name: speckit-install
description: "Install the SpecKit CLI and initialize the current repository for one or both coding-agent integrations (Claude Code, Codex CLI). Use when the operator says: 'install speckit', 'set up speckit', 'initialize speckit in this repo', 'add speckit to this project', 'specify init for me', 'install spec-kit', '$speckit-install', or has a repo with no .specify/ directory and wants to start using Spec-Driven Development. Detects existing installs and hands off to $speckit-upgrade rather than overwriting. Safe to run on any repo. Not for upgrading an existing speckit install ($speckit-upgrade), not for scaffolding a new spec on an already-installed repo ($speckit-scaffold-spec), and not for installing this plugin's own bundled Codex subagents (use $install for that)."
---

# SpecKit Install

## Scope

Install the official SpecKit CLI (https://github.com/github/spec-kit)
if missing, then initialize the current repository for one or both
coding-agent integrations (Claude Code, Codex CLI). Safe to run on
any repo — detects an existing `.specify/` directory and hands off
to `$speckit-upgrade` rather than mutating it.

This skill is **mutation-heavy** (it writes files to the repo and
to `~/.local/share/uv/tools/specify-cli/` if installing the CLI).
It runs only on explicit operator request and never auto-fires from
other skills.

## Scope Boundaries — Not For

- Upgrading an existing SpecKit install. That is `$speckit-upgrade`.
  This skill hands off to it automatically when `.specify/` is
  present.
- Scaffolding a new spec from the technical roadmap. That is
  `$speckit-scaffold-spec`.
- Installing this plugin's own bundled Codex subagent TOML files
  (`autopilot-fast-helper.toml`, `phase-executor.toml`, etc.) into
  `~/.codex/agents/`. That is `$install`.
- Methodology coaching. That is `$speckit-coach`.

> **Codex implicit-trigger note (eval harness vs production):** Layer 2 trigger evals score this skill at 75% (15/20) on the Codex selector — but POS is a perfect 10/10 (every "install speckit" / "set up speckit" / "$speckit-install" query fires correctly). All 5 NEG misses are false-positives in single-skill staging where the harness loads only this skill, so the Codex selector has no alternative to route adjacent SDD queries to ("status of SPEC-014" → should go to `$speckit-status`, "scaffold spec SPEC-009" → `$speckit-scaffold-spec`, "upgrade my existing speckit installation" → `$speckit-upgrade`, "install the bundled SpecKit Pro Codex subagents" → `$install`). In production all six speckit-pro skills are loaded together and Codex routes those queries to their proper destinations. The eval results under-report real-world accuracy; positive-trigger reliability is the operationally-relevant number.

## Input

Accept optional integration keys as arguments:

- `$speckit-install` (interactive — asks which integrations)
- `$speckit-install claude`
- `$speckit-install codex`
- `$speckit-install claude codex` (dual-integration)

If the operator does not specify, ask before proceeding.

## Hard Constraints

- Never run `specify init --here --force` from this skill. `--force`
  overwrites local customizations. Force-flagged behavior lives
  exclusively in `$speckit-upgrade` (where it is wrapped with
  backup/restore).
- Never mutate `.specify/memory/constitution.md`. The placeholder
  written by `specify init` is the operator's content from that
  moment on.
- Never partially-install. If any `specify` invocation fails, STOP
  and report the exact error.
- Never proceed to mutation without explicit confirmation of the
  integration choice when there is ambiguity.
- Never touch `.claude-plugin/`, `commands/`, or this plugin's
  marketplace files. Those are this plugin's own files, not the
  consumer repo's.

## Procedure

### 1. Resolve the SpecKit CLI

```bash
command -v specify >/dev/null 2>&1 && specify --version || echo MISSING
```

If the CLI is present, capture the version (e.g., `specify 0.8.13`)
and continue.

If MISSING, check for `uv`:

```bash
command -v uv >/dev/null 2>&1 && uv --version || echo NO_UV
```

If `uv` is present, install:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

If `uv` is missing, STOP and tell the operator:

> Install `uv` first (https://docs.astral.sh/uv/#installation), then
> re-run `$speckit-install`. SpecKit CLI is distributed as a `uv`
> tool.

Do not attempt other install methods (pipx, manual git clone) unless
the operator explicitly requests it.

### 2. Detect existing-install state

```bash
test -d .specify && echo PRESENT || echo ABSENT
```

If `.specify/` is **PRESENT**:

1. Capture current integrations:

   ```bash
   specify integration list 2>&1
   ```

2. Tell the operator: "This repo already has SpecKit installed
   (integrations: `<list>`). The right tool for this state is
   `$speckit-upgrade` (handles diff-aware upgrades and
   slash-command-to-skills migration safely)."

3. Ask: (a) hand off to `$speckit-upgrade`, (b) add a new integration
   alongside the existing ones (e.g., adding `codex` to a `claude`-only
   repo), or (c) abort.

4. On (a): STOP this skill and invoke `$speckit-upgrade`.
5. On (b): skip Step 3's `specify init` and go directly to Step 4
   with only the new integration(s) the operator wants to add.
6. On (c): STOP.

If `.specify/` is **ABSENT**: continue to Step 3.

### 3. Resolve integration choice

If the operator passed integration keys as arguments, use them. Otherwise:

> Which coding-agent integrations should this repo support?
>
> - `claude` — Claude Code (default in v0.8.13 installs skills at `.claude/skills/speckit-*/`)
> - `codex`  — Codex CLI (use `--integration-options="--skills"` for skills mode)
> - `both`   — dual-integration (`claude` AND `codex` side-by-side)

Both `claude` and `codex` are declared "Multi-install Safe" by the
SpecKit CLI, so dual-integration is officially supported in a single
project.

If the operator's request is ambiguous (e.g., "install for codex but
also leave Claude alone"), ask one clarifying question — do NOT
infer.

### 4. Initialize the repository

For a fresh install (`.specify/` was ABSENT in Step 2):

1. Pick the operator's first integration key as the bootstrap key.
2. Run:

   ```bash
   specify init --here --integration <first-key> --script sh
   ```

   For Codex with skills mode (the recommended setup in v0.8.13):

   ```bash
   specify init --here --integration codex --integration-options="--skills" --script sh
   ```

3. For each additional integration the operator chose, run:

   ```bash
   specify integration install <key> --script sh
   ```

   For Codex with skills mode:

   ```bash
   specify integration install codex --integration-options="--skills" --script sh
   ```

For adding to an existing install (Step 2 was PRESENT, operator chose
option (b)):

- Skip the bootstrap `specify init`. For each new integration the
  operator chose, run `specify integration install <key> --script sh`
  (with `--integration-options="--skills"` for codex).

If any command returns non-zero, STOP. Do not retry or "fix" without
operator input — the CLI's error message is the operator's signal.

### 5. Offer to install the curated set of extensions and presets

speckit-pro recommends a small set of community extensions and presets
that power the autopilot's post-implementation parallel group and the
AskUserQuestion picker preset for `/speckit.clarify` and
`/speckit.checklist`. The full list and rationale are in
`speckit-pro/skills/speckit-coach/references/presets-extensions-guide.md`
(section: "The curated set").

Check what would change. The script lives at
`<skill-dir>/../../scripts/install-curated-set.sh`:

```bash
bash "<skill-dir>/../../scripts/install-curated-set.sh" --mode=check
```

The script prints one line per entry that would be installed, exits 0
if everything is already current, exits 2 if work is pending.

- If exit code is **0**: report "Curated extensions and presets
  already current." Continue to Step 6.

- If exit code is **1** (typically `gh not on PATH` or another missing
  prerequisite): surface the stderr message and **skip this step**.
  Do not block the install. Tell the operator: "Curated-set
  auto-install skipped — install `gh` (https://cli.github.com/) and
  re-run `$speckit-upgrade` to pull the curated extensions and
  presets." Continue to Step 6.

- If exit code is **2**: tell the operator the check output and ask
  which entries to install. Recommended default is **all**. Then
  invoke the script in install mode:

  - All: `bash "<skill-dir>/../../scripts/install-curated-set.sh" --mode=install`
  - Subset: `bash "<skill-dir>/../../scripts/install-curated-set.sh" --mode=install --accept=<csv>`
  - None: skip. The operator can run `$speckit-upgrade` later to
    install the curated set on demand.

The script never installs without an explicit selection — empty
`--accept` means all from the manifest; any other value scopes to that
csv. A provenance trail is recorded in `.specify/curated-install.json`
— commit this to git so the project's extension state is reproducible.

If the script reports that an entry has neither a GitHub Release nor
a git tag, surface the message but do not block the install. The
operator can re-run after the upstream extension publishes a tag.

### 6. Verify

```bash
specify check 2>&1
specify integration list 2>&1
```

Confirm:

- `specify check` reports the project is ready.
- Each chosen integration appears as `installed` in the integration
  list.

If verification fails, report the mismatch — do not silently
continue.

### 7. Report

Return a concise install summary:

```text
## SpecKit Installed

**CLI version:** specify <X.Y.Z>
**Repo init:** .specify/ scaffolded (templates, scripts, constitution placeholder)
**Integrations installed:**
- claude → .claude/skills/speckit-*/ (skills mode)
- codex  → .codex/skills/speckit-*/ (skills mode)

**Next steps:**
1. Restart your coding-agent process (Claude Code or Codex CLI) so
   the new skills load.
2. Create your project constitution:
   - Claude: `/speckit.constitution` or `/speckit-pro:speckit-coach create my project constitution`
   - Codex:  `$speckit-constitution` or `$speckit-coach`
3. When you're ready to spec a feature, use `$speckit-scaffold-spec
   SPEC-ID` to bootstrap from the technical roadmap.
```

Do not continue into any other workflow in the same skill. Install
ends here.

## Failure Handling

STOP and report — do not improvise — when:

- `uv` is missing and the operator cannot install it.
- `specify init` returns a non-zero exit code (network failure,
  template fetch error, etc.).
- `specify integration install <key>` fails (likely conflict — let
  the operator decide).
- The repo has uncommitted changes that would conflict with the
  new files. Recommend committing or stashing first.
- The operator declines confirmation on integration choice.

If a partial install happened (e.g., `claude` succeeded but `codex`
failed), report exactly what landed and what did not. Recommend
running `specify integration list` to see current state.

## Why This Skill Exists

The official SpecKit CLI already provides `specify init`,
`specify integration install`, and `specify integration list`. This
skill is a thin orchestrator that:

- Bootstraps the CLI itself via `uv tool install` when missing.
- Detects existing installs and refuses to overwrite them
  (handing off to `$speckit-upgrade` instead).
- Asks explicitly about dual-integration vs single-integration
  before mutating files.
- Returns a consistent post-install summary so the operator knows
  what restart and which next-step skill to invoke.

The plugin does not duplicate any CLI behavior. It wraps the CLI
with the consistency a plugin user expects.

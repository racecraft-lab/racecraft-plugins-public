---
name: speckit-install
description: "Installs the official SpecKit CLI and initializes one or both coding-agent integrations (Claude Code, Codex CLI). Detects existing installs and hands off to /speckit-pro:speckit-upgrade rather than overwriting. Optionally installs the curated set of community extensions and presets. Use when the user says \"install speckit\", \"set up speckit\", \"initialize speckit\", \"add speckit to this repo\", \"install spec-kit\", \"bootstrap speckit\", \"first-time speckit setup\", \"install the specify cli\", \"set up specify\", or wants to install for claude only, codex only, or both side-by-side. Not for upgrading an existing install (use /speckit-pro:speckit-upgrade) or running workflows (use /speckit-pro:speckit-autopilot)."
argument-hint: "(optional) integration keys, e.g. 'claude', 'codex', or 'claude codex'"
user-invocable: true
allowed-tools: Read Edit Write
license: MIT
---

# SpecKit Install

Install the official SpecKit CLI (https://github.com/github/spec-kit)
if missing, then initialize this repository to use it with Claude
Code, Codex CLI, or both. Safe to run on any repo — detects an
existing `.specify/` directory and hands off to
`/speckit-pro:speckit-upgrade` rather than overwriting it.

This skill is **mutation-heavy** (it writes files to the repo and
to `~/.local/share/uv/tools/specify-cli/` if installing the CLI).
It runs only on explicit operator request and never auto-fires from
other skills.

## Scope Boundaries — Not For

- Upgrading an existing SpecKit install. That is
  `/speckit-pro:speckit-upgrade`. This skill hands off to it when
  `.specify/` is present.
- Scaffolding a new spec from the technical roadmap. That is
  `/speckit-pro:speckit-scaffold-spec`.
- Methodology coaching. That is `/speckit-pro:speckit-coach`.

## Invocation

```text
/speckit-pro:speckit-install                    # interactive — asks which integrations
/speckit-pro:speckit-install claude             # claude only
/speckit-pro:speckit-install codex              # codex only
/speckit-pro:speckit-install claude codex       # both (dual-integration)
```

If the operator does not specify, ask before proceeding.

## What to Do

### 1. Ensure the SpecKit CLI is available

The runner owns the pinned Spec Kit version. Invoke
`[resolved_python, "-m", "speckit_pro_runner"]` with this request on
stdin, parse `data.stdout.text` as JSON, and read its `spec_kit` object
(`status`, `installed_version`, `pinned_version`, `install_argv`, `cli_argv`):

```json
{"schema_version":"1.0","request_id":"install-spec-kit-pin","helper_id":"check-prerequisites","operation":"check-prerequisites","mode":"read_only","inputs":{"workflow_file":""}}
```

Use `spec_kit.cli_argv` as the executable prefix for every Spec Kit command
below, including health checks, extensions, presets and upgrade handoffs.
Append the listed arguments and launch the resulting array with `shell=False`.
The runner supplies the verified absolute path; preserve it even if PATH,
the current directory or a discovery link changes. If `cli_argv` is empty, STOP
before any Spec Kit command; offer the pinned install, then verify again.
Re-run `check-prerequisites` after any CLI install or replacement and pass the
new `spec_kit` object to subsequent steps and handoffs. A declined version
repair permits continuation only with a nonempty `cli_argv`.

- If it is found, record `installed_version`. When `status` is `match`,
  move on. When it is `older`, `newer` or `unreadable`, tell the
  operator the installed version and the pinned one, and ask before
  running `install_argv` (it replaces the CLI).
- If the CLI is missing (`status` is `missing`):
  - Look up `uv` the same way.
  - If `uv` is present, install the pinned CLI by invoking
    `install_argv` with argv-only execution.
  - If `uv` is missing, STOP and tell the operator to install `uv`
    from the official Astral documentation, then re-run
    `/speckit-pro:speckit-install`. SpecKit CLI is distributed as a
    `uv` tool.

Do not attempt other install methods (pipx, manual git clone) unless
the operator explicitly requests it.

### 2. Detect existing-install state

Use a filesystem directory check for `.specify/` and record the state
as `PRESENT` or `ABSENT`.

If `.specify/` is **PRESENT**:

1. Invoke `spec_kit.cli_argv + ["integration", "list"]` with argv-only execution and
   capture stdout and stderr to see which integrations are installed.
2. Tell the operator: "This repo already has SpecKit installed
   (integrations: `<list>`). The right tool for this state is
   `/speckit-pro:speckit-upgrade` (handles diff-aware upgrades and
   slash-command-to-skills migration safely)."
3. Ask whether to (a) hand off to `/speckit-pro:speckit-upgrade`, (b)
   add a new integration alongside the existing ones (e.g., adding
   `codex` to a `claude`-only repo), or (c) abort.
4. On (a): STOP this skill and invoke `/speckit-pro:speckit-upgrade`.
5. On (b): go directly to Step 4 with only the new integration(s) the
   operator wants to add, and skip its bootstrap `spec_kit.cli_argv + ["init"]`.
6. On (c): STOP.

If `.specify/` is **ABSENT**: continue to Step 3.

### 3. Ask which integrations to install

If the operator passed integration keys as arguments, use those.
Otherwise ask:

> Which coding-agent integrations should this project support?
>
> - `claude` — Claude Code (installs skills at `.claude/skills/speckit-*/`)
> - `codex`  — Codex CLI (installs skills at `.agents/skills/speckit-*/`; skills mode is the default)
> - `both`   — dual-integration (`claude` AND `codex` side-by-side)

Both `claude` and `codex` are declared "Multi-install Safe" by the
SpecKit CLI, so dual-integration is officially supported in a single
project. The plugin's own skills work in both runtimes.

If the operator's request is ambiguous (e.g., "install for codex but
also leave Claude alone"), ask one clarifying question — do NOT
infer.

### 4. Initialize the repository

Every `specify` call passes `--script sh`, the script flavor the
runner's setup-contract check reads, and which avoids the CLI's script
prompt.

For a **fresh install** (Step 2 said ABSENT):

1. Pick the operator's first integration key as the bootstrap key.
2. Run `spec_kit.cli_argv + ["init", "--here", "--integration", "<first-key>", "--script", "sh"]` to
   scaffold `.specify/` (templates, scripts, constitution placeholder)
   AND install the first integration. For Codex, skills mode is the
   default and writes `.agents/skills/speckit-*/`, so no extra option
   is needed.
3. For each additional integration the operator chose, run
   `spec_kit.cli_argv + ["integration", "install", "<key>", "--script", "sh"]`.

For **adding to an existing install** (Step 2 said PRESENT, operator
chose option (b)):

- Skip the bootstrap `spec_kit.cli_argv + ["init"]`. For each new integration the
  operator chose, run `spec_kit.cli_argv + ["integration", "install", "<key>", "--script", "sh"]`.

If any command returns non-zero, STOP. Do not retry or "fix" without
operator input — the CLI's error message is the operator's signal.

When `claude` was installed, use the resolved Python 3.11+ interpreter to run
`<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode apply --repo-root "<repository-root>"`
with argv-only execution before any memory-enabled plugin agent runs. Include
the resulting `.gitignore` change in the setup commit before clean-worktree-gated
helpers. If the command reports tracked memory or an ineffective nested
override, stop and report its paths; never remove memory automatically.

For every install, also use the resolved Python 3.11+ interpreter to run
`<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode apply --target worktrees --repo-root "<repository-root>"`
with argv-only execution. It ignores `.worktrees/`, where scaffold places each
spec worktree, so the first scaffold does not stop on an unignored target.
Include the `.gitignore` change in the same setup commit. A nonzero exit means a
nested ignore rule overrides it: stop and report the output.

### 5. Offer to install the curated set of extensions and presets

speckit-pro recommends a small set of community extensions and presets
that power the autopilot's post-implementation parallel group and the
AskUserQuestion picker preset for `/speckit-clarify` and
`/speckit-checklist`.
See [presets-extensions-guide.md → The curated set](../speckit-coach/references/presets-extensions-guide.md)
for the full list and rationale.

First install the reviewability preset, which scaffold requires. Send this
request and read `reviewability_preset` in the result:

```json
{"schema_version":"1.0","request_id":"install-reviewability-preset","helper_id":"detect-presets","operation":"detect-presets","mode":"read_only","inputs":{"repo_root":"."}}
```

When `status` is `missing`, run `spec_kit.cli_argv + add_args` without asking:
it is part of the install, not a recommendation, then send the
`check-prerequisites` request again and report a failing `template_resolution`
check. When `status` is `unavailable`, report it and continue.

Compare `.specify/extensions/` and `.specify/presets/` against the entries in
`${CLAUDE_PLUGIN_ROOT}/scripts/curated-set.json`.

- If every entry is present: report "Curated extensions and presets
  already installed — nothing to install." Continue to Step 6.

- Otherwise, list the missing entries and ask which to install.
  Recommended default is **all**. For each accepted entry, give the
  operator the `spec_kit.cli_argv + ["<kind>", "add", "<id>", "--from", "<archive_url>"]`
  command from the curated set (`<kind>` is `extension` or `preset`). Spec Kit
  refuses a bare `add <id>` for these entries. Run a preset command yourself after
  the operator confirms. Do not run an extension command: it stops at Spec Kit's
  trust prompt, so the operator runs it in their own terminal. The pin
  pins the bytes but does not vet them: before the operator confirms, ask them to
  review the archive's commands, scripts, and hooks.
  [The curated set](../speckit-coach/references/presets-extensions-guide.md)
  says how to vet the archive and verify the result. Skipped entries can be
  installed later with `/speckit-pro:speckit-upgrade`.

### 6. Verify

Invoke `spec_kit.cli_argv + ["check"]` and `spec_kit.cli_argv + ["integration", "list"]` with argv-only
execution, and capture stdout and stderr. Confirm:

- `spec_kit.cli_argv + ["check"]` reports the project is ready.
- Each chosen integration appears as `installed` in the integration
  list.
- For Codex, `.agents/skills/speckit-*/SKILL.md` exists. That is the
  primary Codex skills path. A legacy `.codex/skills/` directory may
  also exist from an older setup; Codex still reads it, so report it
  and leave it in place.

If verification fails, report the mismatch — do not silently
continue.

#### Research screening check

speckit-pro requires the typesafe-jev plugin, and Claude Code installs it
with speckit-pro. Run runner helper `research-broker-preflight` in
`read_only` mode with empty `inputs`.

Report `data.screening_mode` and each `data.warnings[].message` and
`data.errors[].message`. The helper never reads a key value.

- A key is optional. With no Jev key or binary, research runs in
  `sanitizer-only` mode, which is a warning, not a failure.
- With no Tavily key, `research_search` returns `search_unavailable` and
  `docs_query` still works through keyless Context7. Point the user to a free
  Tavily key in `~/.config/speckit-pro/tavily.key` (mode 0600).
- `expected_failure` means a credential or binary is configured but broken.
  Report the fix it names. Do not roll back the SpecKit install for it.
- A key held only in an environment variable is a warning: the broker runs
  as an MCP server, which may not see it. Prefer the key files.


### 7. Report

Return a concise install summary:

```text
## SpecKit Installed

**CLI version:** specify <X.Y.Z>
**Repo init:** .specify/ scaffolded (templates, scripts, constitution placeholder)
**Integrations installed:**
- claude → .claude/skills/speckit-*/ (skills mode)
- codex  → .agents/skills/speckit-*/ (skills mode)

**Next steps:**
1. Restart your coding-agent process (Claude Code or Codex CLI) so
   the new skills load.
2. Create your project constitution:
   - Claude: `/speckit-constitution` or `/speckit-pro:speckit-coach create my project constitution`
   - Codex:  `$speckit-constitution` or `$speckit-coach`
3. When you're ready to spec a feature, scaffold it from the technical
   roadmap with `/speckit-pro:speckit-scaffold-spec SPEC-ID` (Claude)
   or `$speckit-scaffold-spec SPEC-ID` (Codex).
```

Do not continue into any other workflow in the same skill. Install
ends here.

## Hard Constraints

- Never run `spec_kit.cli_argv + ["init", "--here", "--force"]` from this skill. `--force`
  overwrites local customizations. Force-flagged behavior lives
  exclusively in the upgrade skill, where it is wrapped with
  backup/restore.
- Never proceed to mutation without explicit operator confirmation of
  the integration choice when there is ambiguity.
- Never mutate `.specify/memory/constitution.md` — that's the
  operator's content. If they don't have one yet, leave the SpecKit
  placeholder in place and tell them how to fill it.
- Never partially-install. If any `specify` invocation fails (e.g.,
  network error fetching templates), STOP and report the exact error.
  Do not retry silently.
- Never touch `.claude-plugin/`, `commands/`, or this plugin's
  marketplace files. Those are this plugin's own files, not the
  consumer repo's.

## Failure Handling

Stop and report — do not improvise — when:

- `uv` is missing and the operator cannot install it.
- `spec_kit.cli_argv + ["init"]` returns a non-zero exit code (network failure,
  template fetch error, etc.).
- `spec_kit.cli_argv + ["integration", "install", "<key>"]` fails (the operator may have a
  conflicting integration; surface the CLI's error message and let
  them decide).
- The repo has detached HEAD or uncommitted changes that would
  conflict with the new files. Recommend committing or stashing
  first.
- The operator declines confirmation on the integration choice.

If a partial install happened (e.g., `claude` succeeded but `codex`
failed), report exactly what landed and what did not. Recommend
running `spec_kit.cli_argv + ["integration", "list"]` to see current state.

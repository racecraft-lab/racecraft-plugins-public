---
name: speckit-install
<!-- host:claude: Claude reads a trigger-phrase description and Claude-only frontmatter keys -->
description: "Installs the official SpecKit CLI and initializes one or both coding-agent integrations (Claude Code, Codex CLI). Detects existing installs and hands off to /speckit-pro:speckit-upgrade rather than overwriting. Optionally installs the curated set of community extensions and presets. Use when the user says \"install speckit\", \"set up speckit\", \"initialize speckit\", \"add speckit to this repo\", \"install spec-kit\", \"bootstrap speckit\", \"first-time speckit setup\", \"install the specify cli\", \"set up specify\", or wants to install for claude only, codex only, or both side-by-side. Not for upgrading an existing install (use /speckit-pro:speckit-upgrade) or running workflows (use /speckit-pro:speckit-autopilot)."
argument-hint: "(optional) integration keys, e.g. 'claude', 'codex', or 'claude codex'"
user-invocable: true
allowed-tools: Read Edit Write
license: MIT
<!-- /host -->
<!-- host:codex: Codex keeps its own selection description -->
description: "Install the SpecKit CLI and initialize the current repository for one or both coding-agent integrations (Claude Code, Codex CLI). Use when the operator says: 'install speckit', 'set up speckit', 'initialize speckit in this repo', 'add speckit to this project', 'specify init for me', 'install spec-kit', '$speckit-install', or has a repo with no .specify/ directory and wants to start using Spec-Driven Development. Detects existing installs and hands off to $speckit-upgrade rather than overwriting. Safe to run on any repo. Not for upgrading an existing speckit install ($speckit-upgrade), not for scaffolding a new spec on an already-installed repo ($speckit-scaffold-spec), and not for installing this plugin's own bundled Codex subagents (use $install for that)."
<!-- /host -->
---

# SpecKit Install

Install the official SpecKit CLI (https://github.com/github/spec-kit)
if missing, then initialize this repository to use it with Claude
Code, Codex CLI, or both. Safe to run on any repo — detects an
existing `.specify/` directory and hands off to
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-upgrade` rather than overwriting it.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-upgrade` rather than overwriting it.
<!-- /host -->

This skill is **mutation-heavy** (it writes files to the repo and
to `~/.local/share/uv/tools/specify-cli/` if installing the CLI).
It runs only on explicit operator request and never auto-fires from
other skills.

## Scope Boundaries — Not For

<!-- host:claude: Claude names skills with a slash -->
- Upgrading an existing SpecKit install. That is
  `/speckit-pro:speckit-upgrade`. This skill hands off to it when
  `.specify/` is present.
- Scaffolding a new spec from the technical roadmap. That is
  `/speckit-pro:speckit-scaffold-spec`.
- Methodology coaching. That is `/speckit-pro:speckit-coach`.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign and ships an agent install skill -->
- Upgrading an existing SpecKit install. That is `$speckit-upgrade`.
  This skill hands off to it when `.specify/` is present.
- Scaffolding a new spec from the technical roadmap. That is
  `$speckit-scaffold-spec`.
- Installing this plugin's own bundled Codex subagent TOML files
  (`autopilot-fast-helper.toml`, `phase-executor.toml`, etc.) into
  `~/.codex/agents/`. That is `$install`.
- Methodology coaching. That is `$speckit-coach`.
<!-- /host -->

## Invocation

```text
<!-- host:claude: Claude names skills with a slash -->
/speckit-pro:speckit-install                    # interactive — asks which integrations
/speckit-pro:speckit-install claude             # claude only
/speckit-pro:speckit-install codex              # codex only
/speckit-pro:speckit-install claude codex       # both (dual-integration)
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
$speckit-install                    # interactive — asks which integrations
$speckit-install claude             # claude only
$speckit-install codex              # codex only
$speckit-install claude codex       # both (dual-integration)
<!-- /host -->
```

If the operator does not specify, ask before proceeding.

## What to Do

### 1. Ensure the SpecKit CLI is available

Look up `specify` with argv-only execution, never through shell
parsing: first on `PATH`, then at `~/.local/bin/specify`, where
`uv tool install` puts it. This is where the runner's own
prerequisite check looks.

- If it is found, capture the version (for example, `specify 0.8.13`)
  and move on.
- If the CLI is missing:
  - Look up `uv` the same way.
  - If `uv` is present, install the official SpecKit CLI by invoking
    the equivalent of `uv tool install specify-cli --from
    git+https://github.com/github/spec-kit.git` with argv-only
    execution.
  - If `uv` is missing, STOP and tell the operator to install `uv`
    from the official Astral documentation, then re-run
<!-- host:claude: Claude names skills with a slash -->
    `/speckit-pro:speckit-install`. SpecKit CLI is distributed as a
    `uv` tool.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
    `$speckit-install`. SpecKit CLI is distributed as a `uv` tool.
<!-- /host -->

Do not attempt other install methods (pipx, manual git clone) unless
the operator explicitly requests it.

### 2. Detect existing-install state

Use a filesystem directory check for `.specify/` and record the state
as `PRESENT` or `ABSENT`.

If `.specify/` is **PRESENT**:

1. Invoke `specify integration list` with argv-only execution and
   capture stdout and stderr to see which integrations are installed.
2. Tell the operator: "This repo already has SpecKit installed
   (integrations: `<list>`). The right tool for this state is
<!-- host:claude: Claude names skills with a slash -->
   `/speckit-pro:speckit-upgrade` (handles diff-aware upgrades and
   slash-command-to-skills migration safely)."
3. Ask whether to (a) hand off to `/speckit-pro:speckit-upgrade`, (b)
   add a new integration alongside the existing ones (e.g., adding
   `codex` to a `claude`-only repo), or (c) abort.
4. On (a): STOP this skill and invoke `/speckit-pro:speckit-upgrade`.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
   `$speckit-upgrade` (handles diff-aware upgrades and
   slash-command-to-skills migration safely)."
3. Ask whether to (a) hand off to `$speckit-upgrade`, (b) add a new
   integration alongside the existing ones (e.g., adding `codex` to a
   `claude`-only repo), or (c) abort.
4. On (a): STOP this skill and invoke `$speckit-upgrade`.
<!-- /host -->
5. On (b): go directly to Step 4 with only the new integration(s) the
   operator wants to add, and skip its bootstrap `specify init`.
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
2. Run `specify init --here --integration <first-key> --script sh` to
   scaffold `.specify/` (templates, scripts, constitution placeholder)
   AND install the first integration. For Codex, skills mode is the
   default and writes `.agents/skills/speckit-*/`, so no extra option
   is needed.
3. For each additional integration the operator chose, run
   `specify integration install <key> --script sh`.

For **adding to an existing install** (Step 2 said PRESENT, operator
chose option (b)):

- Skip the bootstrap `specify init`. For each new integration the
  operator chose, run `specify integration install <key> --script sh`.

If any command returns non-zero, STOP. Do not retry or "fix" without
operator input — the CLI's error message is the operator's signal.

When `claude` was installed, use the resolved Python 3.11+ interpreter to run
<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
`<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode apply --repo-root "<repository-root>"`
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable and names the root in prose -->
`<resolved_python> <plugin-root>/scripts/agent-memory-ignore.py --mode apply --repo-root <repository-root>`
<!-- /host -->
with argv-only execution before any memory-enabled plugin agent runs. Include
the resulting `.gitignore` change in the setup commit before clean-worktree-gated
helpers. If the command reports tracked memory or an ineffective nested
override, stop and report its paths; never remove memory automatically.

### 5. Offer to install the curated set of extensions and presets

speckit-pro recommends a small set of community extensions and presets
that power the autopilot's post-implementation parallel group and the
<!-- host:claude: Claude names SpecKit skills with a slash -->
AskUserQuestion picker preset for `/speckit-clarify` and
`/speckit-checklist`.
<!-- /host -->
<!-- host:codex: Codex names SpecKit skills with a dollar sign -->
AskUserQuestion picker preset for `$speckit-clarify` and
`$speckit-checklist`.
<!-- /host -->
See [presets-extensions-guide.md → The curated set](../speckit-coach/references/presets-extensions-guide.md)
for the full list and rationale.

Compare `.specify/extensions/` and `.specify/presets/` against the entries in
<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
`${CLAUDE_PLUGIN_ROOT}/scripts/curated-set.json`.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable and names the root in prose -->
`<plugin-root>/scripts/curated-set.json`.
<!-- /host -->

- If every entry is present: report "Curated extensions and presets
  already installed — nothing to install." Continue to Step 6.

- Otherwise, list the missing entries and ask which to install.
  Recommended default is **all**. For each accepted entry, give the
  operator the `specify extension add <id>` or preset command from the
  curated set and run it only after they confirm. Skipped entries can be
<!-- host:claude: Claude names skills with a slash -->
  installed later with `/speckit-pro:speckit-upgrade`.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
  installed later with `$speckit-upgrade`.
<!-- /host -->

### 6. Verify

Invoke `specify check` and `specify integration list` with argv-only
execution, and capture stdout and stderr. Confirm:

- `specify check` reports the project is ready.
- Each chosen integration appears as `installed` in the integration
  list.
- For Codex, `.agents/skills/speckit-*/SKILL.md` exists. That is the
  primary Codex skills path. A legacy `.codex/skills/` directory may
  also exist from an older setup; Codex still reads it, so report it
  and leave it in place.

If verification fails, report the mismatch — do not silently
continue.

#### Research screening check

<!-- host:claude: Claude installs typesafe-jev as a speckit-pro plugin dependency -->
speckit-pro requires the typesafe-jev plugin, and Claude Code installs it
with speckit-pro. Run runner helper `research-broker-preflight` in
`read_only` mode with empty `inputs`.
<!-- /host -->
<!-- host:codex: Codex has no plugin dependency mechanism -->
speckit-pro requires the typesafe-jev plugin, and Codex has no plugin
dependency mechanism. Run `codex plugin list` with argv-only execution. If
`typesafe-jev` is absent, print `codex plugin add
typesafe-jev@racecraft-plugins-public`, tell the user to restart Codex, and
stop this step. Otherwise run runner helper `research-broker-preflight` in
`read_only` mode with empty `inputs`.
<!-- /host -->

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

<!-- host:codex: only Codex has an automatic approval reviewer -->
#### Autopilot review policy check

Codex's automatic approval reviewer needs a standing policy so that a ratified
autopilot plan's ordinary actions run without a per-run question: feature-branch
pushes, the plan's pull requests and review replies, public documentation
research, and offline audits on a worker on this machine. Read the
`auto_review.extra_policy` string from the user-level `~/.codex/config.toml`,
if one exists; read that file, never write it. Run runner helper
`render-egress-authorization` in `read_only` mode with `scope=standing`, the
repository's GitHub `owner/name`, its default branch, and that string as
`installed_extra_policy`.

- When `data.installed` is true, report the standing policy as installed.
- Otherwise print `data.extra_policy_fragment` unchanged as the install text,
  and tell the operator to review it and install it once. It needs Codex 0.158
  or later. TOML allows one `[auto_review]` table, so merge it into an existing
  `extra_policy` string. It is an `extra_policy` fragment, never
  `auto_review.policy`, which replaces the default reviewer policy.
- Tell the operator that a reviewer session persists for its thread, even
  after an app restart: a new or changed policy reaches only threads started
  after the change, so start the autopilot in a new thread after installing it.
- This skill never writes the fragment into `~/.codex`, the repository's
  `.codex/`, or `AGENTS.md`: the reviewer trusts `AGENTS.md`, and a branch
  could rewrite it.
- A missing policy is a warning, not a failure. The autopilot asks for it once,
  at run start, before Phase 1, and the run starts on the operator's reply.
<!-- /host -->

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

- Never run `specify init --here --force` from this skill. `--force`
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
- `specify init` returns a non-zero exit code (network failure,
  template fetch error, etc.).
- `specify integration install <key>` fails (the operator may have a
  conflicting integration; surface the CLI's error message and let
  them decide).
- The repo has detached HEAD or uncommitted changes that would
  conflict with the new files. Recommend committing or stashing
  first.
- The operator declines confirmation on the integration choice.

If a partial install happened (e.g., `claude` succeeded but `codex`
failed), report exactly what landed and what did not. Recommend
running `specify integration list` to see current state.

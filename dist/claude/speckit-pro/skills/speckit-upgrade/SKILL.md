---
name: speckit-upgrade
description: "Upgrades or migrates an existing SpecKit installation safely with backup-and-restore for locally-modified files. Preserves the project constitution and template overrides. Supports upgrading one or both integrations (Claude Code, Codex CLI) and offering missing curated community extensions and presets. Use when the user asks to execute an upgrade or migration, including \"upgrade speckit\", \"update speckit\", \"refresh speckit\", \"new speckit version\", \"latest speckit\", \"upgrade specify cli\", \"safe speckit upgrade\", \"speckit migration to skills\", or \"preserve my constitution during upgrade\". Not for pre-upgrade project, template, or preset repair (use /speckit-pro:speckit-coach). Hands off to /speckit-pro:speckit-install if .specify/ is missing."
argument-hint: "(optional) integration keys to upgrade, e.g. 'claude', 'codex', or omit for all"
user-invocable: true
allowed-tools: Read Edit Write
license: MIT
---

# SpecKit Upgrade

Upgrade an existing SpecKit install in the current repository safely.
Preserves `.specify/memory/constitution.md` and any other
locally-modified files via backup-then-force-then-restore. Supports
upgrading one or both integrations (`claude`, `codex`).

If `.specify/` is missing, hands off to `/speckit-pro:speckit-install`
— upgrade only operates on existing installs.

This skill is **mutation-heavy** (it modifies files in `.specify/`,
`.claude/`, `.codex/`, `.agents/skills/`, and writes backups to `/tmp/`). It
runs only on explicit operator request and never auto-fires from other
skills.

## Scope Boundaries — Not For

- Initial install (no `.specify/` directory yet). That is
  `/speckit-pro:speckit-install`. This skill hands off to it.
- Scaffolding a new spec from the technical roadmap. That is
  `/speckit-pro:speckit-scaffold-spec`.
- Upgrading the SpecKit CLI binary itself (`specify` package). The
  operator runs that with `uv tool install --force`; this skill
  detects when it's out of date and recommends the command, but
  does not run it.

## Repository Structure Migration Guidance

For existing projects, after integration upgrade and verification, report that
repository structure migration is not available through the current runner.
The `migrate-structure` operation has `promotion_status=deferred` and no
authoritative request. Neither `dry_run` nor `apply` is an operator contract;
do not invoke the operation or claim that it will report or mutate repository
state.

Record the deferred capability gap and leave repository structure unchanged.
Tier-2 PROCESS relocation is separate, but `relocate-process-artifacts` is also
deferred and unavailable. Do not recommend or auto-run either operation.

## Invocation

```text
/speckit-pro:speckit-upgrade                    # upgrade all installed integrations
/speckit-pro:speckit-upgrade claude             # upgrade claude only
/speckit-pro:speckit-upgrade codex              # upgrade codex only
/speckit-pro:speckit-upgrade claude codex       # both, explicit
```

## What to Do

### 1. Detect state and hand off if needed

Use a filesystem directory check for `.specify/` and record the state
as PRESENT or ABSENT.

If `.specify/` is **ABSENT**: STOP and invoke `/speckit-pro:speckit-install`
— upgrade only operates on existing installs.

If **PRESENT**: continue.

### 2. Capture current versions and integrations

Run the `check-prerequisites` helper with `workflow_file` empty and read its
`spec_kit` object. Use `spec_kit.cli_argv` as the executable prefix for every
Spec Kit command below, including health checks, integration upgrades,
extensions and presets. Append the listed arguments and launch the resulting
array with `shell=False`. The runner supplies the verified absolute path;
preserve it even if PATH, the current directory or a discovery link changes.
If `cli_argv` is empty, STOP before any Spec Kit command; offer the pinned
install, then verify again. Re-run `check-prerequisites` after any CLI install
or replacement and use the new `spec_kit` object for subsequent steps.
A declined version repair permits continuation only with a nonempty `cli_argv`.

Use argv-only execution to capture `spec_kit.cli_argv + ["version"]`, run
`spec_kit.cli_argv + ["self", "check"]`, and run `spec_kit.cli_argv + ["integration", "list"]`. Preserve
stdout, stderr, and exit status for each command in the report.

Surface to the operator:

- Current CLI version (e.g. `0.6.1`).
- Whether `spec_kit.cli_argv + ["self", "check"]` reports a newer release available.
- Each installed integration with its current status.

Send the `check-prerequisites` request shown in step 5a now and read the
`spec_kit` object of its result. If `spec_kit.status` is not `match`, recommend that
the operator run `install_argv` from it and then
re-invoke this skill. This skill does not run it. Ask the operator to either upgrade
the CLI first or confirm they want to proceed with the current CLI
version, and wait for the answer before continuing.

### 3. Resolve which integrations to upgrade

If the operator passed integration keys, use those. Otherwise ask:

> Which integrations should I upgrade?
> - `<each-installed-key>` (currently installed)
> - `all` to upgrade everything that's installed
>
> If you want to ADD a new integration (e.g., add `codex` to a
> `claude`-only repo), use `/speckit-pro:speckit-install <new-key>` instead.

### 4. Snapshot the repo state for safety

Create a timestamped backup directory outside the repo, copy
`.specify/`, and copy any present `.claude/`, `.codex/`,
`.agents/skills/`, and `.github/` directories into that backup using
filesystem APIs or argv-only file operations. Codex skills live in
`.agents/skills/` (primary) or `.codex/skills/` (legacy); back up
whichever exists, or both. Report the backup path and copied entries.

Tell the operator: "Repo state snapshotted to `<backup-path>/`. If
anything goes wrong, restore `.specify/` and any listed integration
directories from that backup."

### 5. Per-integration upgrade

For each integration the operator chose:

#### 5a. Try the safe (no --force) upgrade first

Invoke `spec_kit.cli_argv + ["integration", "upgrade", "<key>", "--script", "sh"]` with argv-only
execution.

The CLI is diff-aware: it compares manifest hashes and blocks if
the operator has locally-modified files. If the upgrade succeeds
without blocking, capture its output and read it before moving to
the next integration.

A successful upgrade can still leave shared infrastructure behind.
It refreshes the integration's skills but not the shared
`.specify/scripts/` and `.specify/templates/` files, and it says so
with one or both of these warnings:

- `shared infrastructure path(s) already exist and were not updated`
- `Preserved N customized shared infrastructure file(s)`

Never report such an upgrade as complete. The new skills may call
script options the old scripts reject. List every path the warnings
name and treat them as the modified files in 5b: offer
`force-and-restore`, `keep-mine`, or `manual-merge`. After this step,
invoke `[resolved_python, "-m", "speckit_pro_runner"]` with this
request on stdin:

```json
{"schema_version":"1.0","request_id":"upgrade-setup-contract","helper_id":"check-prerequisites","operation":"check-prerequisites","mode":"read_only","inputs":{"workflow_file":""}}
```

Parse `data.stdout.text` as JSON. Its `setup_contract` check must pass
(the missing workflow file fails a separate check; ignore that one
here). A failing `setup_contract` names each skill that still calls an
option its script rejects. Its `template_resolution` check must pass
too: SpecKit parses preset manifests with PyYAML from the first
`python3` on `PATH`, and a `uv tool` or `pipx` install keeps PyYAML in
its own environment.
If the check fails, show its message; installing packages or editing
shell startup files is the operator's call.

#### 5b. If blocked: parse the block message, back up, force, restore

When the CLI blocks, its output names the modified files. Surface
that list to the operator and ask:

> The upgrade is blocked because these files are locally modified:
> - `<file1>`
> - `<file2>`
>
> Options:
> 1. `force-and-restore` — back up each modified file (already
>    snapshotted to `$BACKUP`), run `--force` to take the new
>    template, then offer to restore your modifications on top.
>    Recommended when the CLI updates are bigger than your local
>    edits.
> 2. `keep-mine` — skip the upgrade for this integration. Your
>    modifications stay intact; you'll miss the upstream template
>    updates.
> 3. `manual-merge` — abort this skill, examine the diff yourself,
>    and re-run after deciding which edits to keep.

If `force-and-restore`, invoke
`spec_kit.cli_argv + ["integration", "upgrade", "<key>", "--force", "--script", "sh"]` with
argv-only execution.

Then for each previously-modified file, compare the backup copy with
the freshly-templated file using a diff tool, show the operator the
result, and ask whether to restore (file-by-file or all-at-once):

- `constitution.md` — almost always restore the backup verbatim. This
  is the operator's project content.
- Templates, scripts, and gate validators — case-by-case. The CLI's
  new versions usually carry fixes/features the operator wants.

### 6. Deduplicate legacy commands when both forms are present

When the upgraded project has the `claude` integration, use the resolved Python 3.11+ interpreter to run
`<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode apply --repo-root "<repository-root>"`
with argv-only execution. Preserve and commit any `.gitignore` change before
clean-worktree-gated helpers. Report tracked memory or overriding nested ignore
rules separately; an ignore rule does not untrack files, and this command never
deletes memory.

For every upgraded project, also use the resolved Python 3.11+ interpreter to run
`<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode apply --target worktrees --repo-root "<repository-root>"`
with argv-only execution. It ignores `.worktrees/`, where scaffold places each
spec worktree. Commit any `.gitignore` change before clean-worktree-gated
helpers. A nonzero exit means a nested ignore rule overrides it: stop and
report the output.

After upgrading, the new skills directories may now exist alongside
the legacy slash-command files (if the prior install was in legacy
mode). Use filesystem glob checks to detect legacy command/prompt
entries and current skills entries for Claude and Codex:

- Claude: legacy `.claude/commands/speckit.*.md`; skills
  `.claude/skills/speckit-*/`.
- Codex: legacy `.codex/prompts/speckit.*.md`; skills
  `.agents/skills/speckit-*/` (primary) or `.codex/skills/speckit-*/`
  (legacy). Either skills path counts as the skills form.

If BOTH legacy and skills paths exist for an integration:

> Both legacy slash-commands and skills are installed for `<integration>`.
> The legacy slash-commands still work but create duplicate triggers. Options:
>
> 1. `dedupe` — delete the legacy `<path>/speckit.*.md` files that
>    SpecKit manages. Recommended unless downstream tooling references
>    the slash-command names.
> 2. `keep-both` — leave the duplicates in place.

On `dedupe`, delete only files matching `speckit.<single-word>.md`
(e.g. `speckit.constitution.md`, `speckit.specify.md`,
`speckit.plan.md`). Files like `speckit.speckit-utils.doctor.md`
and any non-`speckit.` files MUST be preserved — those are
extension commands or unrelated. Show the exact deletion list
before deleting anything so the operator can confirm.

### 7. Verify

Invoke `spec_kit.cli_argv + ["check"]` and `spec_kit.cli_argv + ["integration", "list"]` with argv-only
execution. Preserve stdout, stderr, and exit status.

Confirm each upgraded integration shows `installed` and reports the
new manifest. Report any verification mismatch — do not silently
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


### 8. Offer missing curated extensions and presets

speckit-pro maintains a manual recommendation catalog of community extensions
and presets. See
[presets-extensions-guide.md → The curated set](../speckit-coach/references/presets-extensions-guide.md)
for the full list.

Compare `.specify/extensions/` and `.specify/presets/` against the entries in
`${CLAUDE_PLUGIN_ROOT}/scripts/curated-set.json`.

- If every entry is present: report "Curated extensions and presets already
  installed." Continue to Step 9.

- Otherwise, list the missing entries and ask which to install. Recommended
  default is **all**. For each accepted entry, give the operator the
  `spec_kit.cli_argv + ["<kind>", "add", "<id>", "--from", "<archive_url>"]`
  command from the curated set (`<kind>` is `extension` or `preset`). Spec Kit
  refuses a bare `add <id>` for these entries. Run a preset command yourself after
  the operator confirms. Do not run an extension command: it stops at Spec Kit's
  trust prompt, so the operator runs it in their own terminal.
  [The curated set](../speckit-coach/references/presets-extensions-guide.md)
  says how to verify the result. Skipped entries leave the
  autopilot's post-implementation parallel group running with reduced
  coverage; it does not fail.

### 9. Report

Return a concise upgrade summary:

```text
## SpecKit Upgrade Complete

**CLI version:** specify <X.Y.Z>
**Backup:** /tmp/specify-upgrade-backup-<STAMP>/ (preserved)
**Integrations upgraded:**
- claude → manifest <oldhash> → <newhash> (N modified files restored)
- codex  → manifest <oldhash> → <newhash> (clean upgrade, no blocks)
**Slash-commands deduped:** Yes (claude) / No-changes (codex)

**Customizations preserved:**
- .specify/memory/constitution.md (restored from backup)
- .specify/templates/spec-template.md (kept upgrade version; your edits saved at $BACKUP)
- SpecKit prerequisite helper restored from backup

**Next steps:**
1. Restart your coding-agent process (Claude Code or Codex CLI) so the
   upgraded skills load.
2. Skim the summary above — if you preferred the old version of
   any file, restore from $BACKUP/.
3. Run `spec_kit.cli_argv + ["check"]` independently to confirm health.
```

Do not continue into any other workflow in the same skill. Upgrade
ends here.

## Hard Constraints

- Always snapshot to `/tmp/specify-upgrade-backup-<STAMP>/` BEFORE
  the first `spec_kit.cli_argv + ["integration", "upgrade"]` call.
- Never use `--force` on the first attempt. Try the safe path
  first; only escalate to `--force` after the operator has chosen
  `force-and-restore` and the backup exists.
- Never delete files from `.claude/commands/` or `.codex/prompts/`
  without explicit operator confirmation in Step 6.
- Never delete non-SpecKit-managed files. SpecKit-managed legacy
  command files are the `speckit.<single-word>.md` files; extension
  commands such as `speckit.speckit-utils.doctor.md` and custom
  commands without the `speckit.` prefix must be preserved.
- Never modify `.specify/memory/constitution.md` mid-flight without
  explicit operator instruction. Either restore the operator's backup
  verbatim or leave the freshly-templated version in place if the
  operator says so.
- Never touch this plugin's own files (`.claude-plugin/`,
  `codex-skills/`, the plugin's `commands/`).
- If `spec_kit.cli_argv + ["integration", "upgrade"]` fails for reasons other than
  the diff-aware block (e.g., network failure, missing source
  bundle), STOP and report the exact error. Do not retry silently.
  The operator can re-run after fixing the underlying issue.

## Failure Handling

STOP and report — do not improvise — when:

- The CLI itself is missing (uncommon for upgrade, but possible; hand
  off to `/speckit-pro:speckit-install`).
- A `spec_kit.cli_argv + ["integration", "upgrade"]` call fails for non-diff reasons.
- The backup directory could not be created (filesystem full,
  permission denied, etc.).
- The operator declines all three options in Step 5b for a blocked
  upgrade. Their choice stands; do not retry.
- A restore step fails mid-flight. Report which files succeeded,
  which did not, and where the backup is.

The backup at `/tmp/specify-upgrade-backup-<STAMP>/` is the
operator's safety net. Tell them about it explicitly in the final
report so they know it exists and where to find it.

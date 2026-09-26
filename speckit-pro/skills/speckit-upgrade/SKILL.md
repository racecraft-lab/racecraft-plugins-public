---
name: speckit-upgrade
description: "Upgrades or migrates an existing SpecKit installation safely with backup-and-restore for locally-modified files. Preserves the project constitution and template overrides. Supports upgrading one or both integrations (Claude Code, Codex CLI) and offering missing curated community extensions and presets. Use when the user asks to execute an upgrade or migration, including \"upgrade speckit\", \"update speckit\", \"refresh speckit\", \"new speckit version\", \"latest speckit\", \"upgrade specify cli\", \"safe speckit upgrade\", \"speckit migration to skills\", or \"preserve my constitution during upgrade\". Not for pre-upgrade project, template, or preset repair (use /speckit-pro:speckit-coach). Hands off to /speckit-pro:speckit-install if .specify/ is missing."
argument-hint: "(optional) integration keys to upgrade, e.g. 'claude', 'codex', or omit for all"
user-invocable: true
allowed-tools: Read Edit Write
license: MIT
---

# SpecKit Upgrade

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-upgrade/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

Upgrade an existing SpecKit install safely. Preserves
`.specify/memory/constitution.md` and any other locally-modified
files via backup-then-force-then-restore. Supports upgrading one or both
integrations.

If `.specify/` is missing, hands off to `/speckit-pro:speckit-install`.

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

Use argv-only execution to capture the `specify` version, run
`specify self check`, and run `specify integration list`. Preserve
stdout, stderr, and exit status for each command in the report.

Surface to the operator:
- Current CLI version (e.g. `specify 0.6.1`).
- Whether `specify self check` reports a newer release available.
- Each installed integration with its current status.

If the CLI itself is outdated, recommend running:

Invoke `uv tool install specify-cli --force --from
git+https://github.com/github/spec-kit.git` with argv-only execution.

Wait for the operator to confirm they've upgraded the CLI (or want
to proceed with the current version) before continuing.

### 3. Resolve which integrations to upgrade

If the operator passed integration keys, use those. Otherwise: ask.

> Which integrations should I upgrade?
> - `<key1>` (currently installed)
> - `<key2>` (currently installed)
> - `all` to upgrade everything that's installed
> - Or specify a different integration key not currently installed
>   (treat that as an add-integration request, not an upgrade)

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

Invoke `specify integration upgrade <key> --script sh` with argv-only
execution.

The CLI is diff-aware: it compares manifest hashes and blocks if
the operator has locally-modified files. If the upgrade succeeds
without blocking, capture its output and move to the next
integration.

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
`specify integration upgrade <key> --force --script sh` with
argv-only execution.

Then for each previously-modified file, surface the differences
between the freshly-templated version and the backup, and ask
whether to restore (one-by-one or all-at-once):

Use a diff tool to compare the backup copy with the current file and
show the operator the result.

Constitution.md is the most-common case — almost always restore the
backup verbatim. Templates, scripts, and gate validators are case-
by-case (the CLI's new versions usually have fixes/features the
operator wants).

### 6. Deduplicate legacy commands when both forms are present

When the upgraded project has the `claude` integration, use the resolved Python 3.11+ interpreter to run `<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode apply --repo-root "<repository-root>"`. Preserve and commit any `.gitignore` change before clean-worktree-gated helpers. Report tracked memory or overriding nested ignore rules separately; an ignore rule does not untrack files, and this command never deletes memory.

After upgrading, the new `.claude/skills/speckit-*/` and
`.agents/skills/speckit-*/` directories may now exist alongside the
old `.claude/commands/speckit.*.md` and `.codex/prompts/speckit.*.md`
files (if the prior install was in legacy mode). A repo may also
carry Codex skills in the legacy `.codex/skills/speckit-*/` location.

Use filesystem glob checks to detect legacy `.claude/commands/`
entries and current `.claude/skills/` entries.

If BOTH exist:

> Both legacy slash-commands and skills are installed for Claude. The legacy
> commands still work but create duplicate triggers. Options:
> 1. `dedupe` — delete the legacy `.claude/commands/speckit.*.md`
>    files. Recommended unless you have downstream tooling that
>    references the slash-command names.
> 2. `keep-both` — leave the duplicates in place.

If the operator chooses `dedupe`, delete only the SpecKit-managed
ones (`speckit.constitution.md`, `speckit.specify.md`, etc.) — not
the extension commands (`speckit.speckit-utils.doctor.md`, etc.) and
not any commands without the `speckit.` prefix.

Do the symmetric check for Codex:

Use filesystem glob checks to detect legacy `.codex/prompts/`
entries and current Codex skills entries. Check both skills paths:
`.agents/skills/speckit-*/` (primary) and `.codex/skills/speckit-*/`
(legacy). Either one counts as the skills form.

### 7. Verify

Invoke `specify check` and `specify integration list` with argv-only
execution. Preserve stdout, stderr, and exit status.

Confirm each upgraded integration shows `installed` and is on the
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

### 8. Offer missing curated extensions and presets

speckit-pro maintains a manual recommendation catalog of community extensions
and presets. See
[presets-extensions-guide.md → The curated set](../speckit-coach/references/presets-extensions-guide.md)
for the full list.

Compare `.specify/extensions/` and `.specify/presets/` against the entries
in `${CLAUDE_PLUGIN_ROOT}/scripts/curated-set.json`.

- If every entry is present: report "Curated extensions and presets already
  installed." Continue to Step 9.

- Otherwise, list the missing entries and ask which to install. Recommended
  default is **all**. For each accepted entry, give the operator the
  `specify extension add <id>` or `specify preset add <id>` command and run it
  only after they confirm. Skipped entries leave the
  autopilot's post-implementation parallel group running with reduced
  coverage; it does not fail.

### 9. Report

Return a concise upgrade summary:

```text
## SpecKit Upgrade Complete

**CLI version:** specify <X.Y.Z>
**Backup:** /tmp/specify-upgrade-backup-<STAMP>/
**Integrations upgraded:**
- claude → from manifest <oldhash> to <newhash> (N modified files restored)
- codex  → from manifest <oldhash> to <newhash> (no modified files)
**Slash-commands deduped:** Yes (claude) / No-changes (codex)

**Customizations preserved:**
- .specify/memory/constitution.md (restored from backup)
- .specify/templates/spec-template.md (kept upgrade version; your edits saved at $BACKUP)
- SpecKit prerequisite helper restored from backup

**Next steps:**
1. Restart your coding-agent process so the upgraded skills load.
2. Skim the upgrade summary above — if you preferred the old
   version of any file, restore from $BACKUP.
```

## Hard Constraints

- Always snapshot to `/tmp/specify-upgrade-backup-<STAMP>/` BEFORE
  the first `specify integration upgrade` call.
- Never use `--force` on the first attempt. Try the safe path
  first; only escalate to `--force` after the operator has chosen
  `force-and-restore` and the backup exists.
- Never delete files from `.claude/commands/` or `.codex/prompts/`
  without explicit operator confirmation in Step 6.
- Never delete non-SpecKit-managed files (extension commands,
  custom commands without the `speckit.` prefix).
- Never modify `.specify/memory/constitution.md` mid-flight. Either
  restore the operator's backup verbatim or leave the freshly-
  templated version in place if the operator says so.
- If `specify integration upgrade` fails for reasons other than
  the diff-aware block (e.g., network failure, missing source
  bundle), STOP and report the exact error. The operator can re-run
  after fixing the underlying issue.

## Failure Handling

STOP and report — do not improvise — when:

- The CLI itself is missing (hand off to `/speckit-pro:speckit-install`).
- A `specify integration upgrade` call fails for non-diff reasons.
- The backup directory could not be created (filesystem full, etc.).
- The operator declines all three options in Step 5b for a blocked
  upgrade. Their choice stands.
- A restore step fails mid-flight. Report which files succeeded,
  which did not, and where the backup is.

The backup at `/tmp/specify-upgrade-backup-<STAMP>/` is the
operator's safety net. Tell them about it explicitly in the final
report so they know it exists and where to find it.

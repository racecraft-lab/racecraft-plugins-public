---
name: speckit-upgrade
description: "Upgrades an existing SpecKit installation safely with backup-and-restore for locally-modified files. Preserves the project constitution and template overrides. Supports upgrading one or both integrations (Claude Code, Codex CLI) and offering missing curated community extensions and presets. Use when the user says \"upgrade speckit\", \"update speckit\", \"refresh speckit\", \"new speckit version\", \"latest speckit\", \"upgrade specify cli\", \"safe speckit upgrade\", \"preserve my constitution during upgrade\", or asks how to upgrade without losing template edits. Hands off to /speckit-pro:speckit-install if .specify/ is missing."
argument-hint: "(optional) integration keys to upgrade, e.g. 'claude', 'codex', or omit for all"
user-invocable: true
allowed-tools: Read Edit Write
license: MIT
---

# SpecKit Upgrade

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
`.specify/`, and copy any present `.claude/`, `.codex/`, and
`.github/` directories into that backup using filesystem APIs or
argv-only file operations. Report the backup path and copied entries.

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

After upgrading, the new `.claude/skills/speckit-*/` and
`.codex/skills/speckit-*/` directories may now exist alongside the
old `.claude/commands/speckit.*.md` and `.codex/prompts/speckit.*.md`
files (if the prior install was in legacy mode).

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
entries and current `.codex/skills/` entries.

### 7. Verify

Invoke `specify check` and `specify integration list` with argv-only
execution. Preserve stdout, stderr, and exit status.

Confirm each upgraded integration shows `installed` and is on the
new manifest. Report any verification mismatch — do not silently
continue.

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

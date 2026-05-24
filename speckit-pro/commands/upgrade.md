---
description: Upgrade an existing SpecKit installation in this repo safely — preserves customizations (constitution.md, template overrides) via backup-and-restore, handles the v0.8.13 slash-command → skills migration, and supports upgrading one or both integrations (Claude Code, Codex CLI). Hands off to /speckit-pro:install if .specify/ is missing.
allowed-tools: Bash Read Edit Write
argument-hint: "(optional) integration keys to upgrade, e.g. 'claude', 'codex', or omit for all"
---

# SpecKit Upgrade

Upgrade an existing SpecKit install safely. Preserves
`.specify/memory/constitution.md` and any other locally-modified
files via backup-then-force-then-restore. Handles the v0.8.13
slash-command → skills migration. Supports upgrading one or both
integrations.

If `.specify/` is missing, hands off to `/speckit-pro:install`.

## Invocation

```text
/speckit-pro:upgrade                    # upgrade all installed integrations
/speckit-pro:upgrade claude             # upgrade claude only
/speckit-pro:upgrade codex              # upgrade codex only
/speckit-pro:upgrade claude codex       # both, explicit
```

## What to Do

### 1. Detect state and hand off if needed

```text
Bash("test -d .specify && echo PRESENT || echo ABSENT")
```

If `.specify/` is **ABSENT**: STOP and invoke `/speckit-pro:install`
— upgrade only operates on existing installs.

If **PRESENT**: continue.

### 2. Capture current versions and integrations

```text
Bash("command -v specify >/dev/null 2>&1 && specify --version || echo MISSING")
Bash("specify self check 2>&1 || true")
Bash("specify integration list 2>&1")
```

Surface to the operator:
- Current CLI version (e.g. `specify 0.6.1`).
- Whether `specify self check` reports a newer release available.
- Each installed integration with its current status.

If the CLI itself is outdated, recommend running:

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

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

Create a timestamped backup directory outside the repo:

```text
Bash("STAMP=$(date +%Y%m%d-%H%M%S); BACKUP=/tmp/specify-upgrade-backup-$STAMP; mkdir -p $BACKUP; cp -R .specify $BACKUP/.specify; ls $BACKUP")
```

Also snapshot the agent integration directories that the upgrade
may touch:

```text
Bash("BACKUP=/tmp/specify-upgrade-backup-$STAMP; for d in .claude .codex .github; do [ -e $d ] && cp -R $d $BACKUP/$(basename $d) || true; done; ls $BACKUP")
```

Tell the operator: "Repo state snapshotted to `$BACKUP/`. If
anything goes wrong, restore with `cp -R $BACKUP/.specify .`."

### 5. Per-integration upgrade

For each integration the operator chose:

#### 5a. Try the safe (no --force) upgrade first

```bash
specify integration upgrade <key> --script sh
```

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

If `force-and-restore`:

```bash
specify integration upgrade <key> --force --script sh
```

Then for each previously-modified file, surface the differences
between the freshly-templated version and the backup, and ask
whether to restore (one-by-one or all-at-once):

```text
Bash("diff $BACKUP/<file> <file>")
```

Constitution.md is the most-common case — almost always restore the
backup verbatim. Templates, scripts, and gate validators are case-
by-case (the CLI's new versions usually have fixes/features the
operator wants).

### 6. Handle the slash-command → skills migration (v0.8.13)

After upgrading, the new `.claude/skills/speckit-*/` and
`.codex/skills/speckit-*/` directories may now exist alongside the
old `.claude/commands/speckit.*.md` and `.codex/prompts/speckit.*.md`
files (if the prior install was in legacy mode).

```text
Bash("ls .claude/commands/speckit.*.md 2>/dev/null | head")
Bash("ls .claude/skills/speckit-*/SKILL.md 2>/dev/null | head")
```

If BOTH exist:

> Both legacy slash-commands and skills are installed for Claude. The
> v0.8.13 default is skills-mode. The legacy commands still work but
> create duplicate triggers. Options:
> 1. `dedupe` — delete the legacy `.claude/commands/speckit.*.md`
>    files. Recommended unless you have downstream tooling that
>    references the slash-command names.
> 2. `keep-both` — leave the duplicates in place.

If the operator chooses `dedupe`, delete only the SpecKit-managed
ones (`speckit.constitution.md`, `speckit.specify.md`, etc.) — not
the extension commands (`speckit.speckit-utils.doctor.md`, etc.) and
not any commands without the `speckit.` prefix.

Do the symmetric check for Codex:

```text
Bash("ls .codex/prompts/speckit.*.md 2>/dev/null | head")
Bash("ls .codex/skills/speckit-*/SKILL.md 2>/dev/null | head")
```

### 7. Verify

```text
Bash("specify check 2>&1")
Bash("specify integration list 2>&1")
```

Confirm each upgraded integration shows `installed` and is on the
new manifest. Report any verification mismatch — do not silently
continue.

### 8. Report

Return a concise upgrade summary:

```text
## SpecKit Upgrade Complete

**CLI version:** specify <X.Y.Z>
**Backup:** /tmp/specify-upgrade-backup-<STAMP>/ (preserved for 24h+)
**Integrations upgraded:**
- claude → from manifest <oldhash> to <newhash> (N modified files restored)
- codex  → from manifest <oldhash> to <newhash> (no modified files)
**Slash-commands deduped:** Yes (claude) / No-changes (codex)

**Customizations preserved:**
- .specify/memory/constitution.md (restored from backup)
- .specify/templates/spec-template.md (kept upgrade version; your edits saved at $BACKUP)
- .specify/scripts/bash/check-prerequisites.sh (restored from backup)

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

- The CLI itself is missing (hand off to `/speckit-pro:install`).
- A `specify integration upgrade` call fails for non-diff reasons.
- The backup directory could not be created (filesystem full, etc.).
- The operator declines all three options in Step 5b for a blocked
  upgrade. Their choice stands.
- A restore step fails mid-flight. Report which files succeeded,
  which did not, and where the backup is.

The backup at `/tmp/specify-upgrade-backup-<STAMP>/` is the
operator's safety net. Tell them about it explicitly in the final
report so they know it exists and where to find it.

## Why This Skill

The SpecKit CLI's `specify integration upgrade` is the canonical
upgrade path and is diff-aware (blocks on modified files), but its
`--force` flag overwrites those files without any backup. This skill
wraps the CLI to provide:

- Automatic timestamped snapshots before any mutation.
- A structured "what's modified, what do you want to do" prompt
  when the diff-aware path blocks.
- File-by-file restore decisions after `--force`.
- Awareness of the v0.8.13 slash-command → skills migration, with
  explicit dedupe of legacy SpecKit commands (and a hard guarantee
  to never touch extension commands or non-SpecKit slash commands).
- Symmetric handling for Claude and Codex when both integrations
  are installed (the consumer doesn't have to remember which
  invocation goes where).

For an initial install, use `/speckit-pro:install`. The two skills
hand off to each other based on `.specify/` presence.

---
name: speckit-upgrade
description: "Upgrade an existing SpecKit installation safely. Use when the operator says: 'upgrade speckit', 'update speckit', 'specify integration upgrade', 'migrate from slash commands to skills', 'safely upgrade spec-kit', 'bump speckit version', '$speckit-upgrade', or has an existing .specify/ directory and wants to move to the current spec-kit release. Preserves customizations (constitution.md, template overrides) via backup-and-restore. Handles the v0.8.13 slash-command → skills migration. Supports upgrading one or both integrations (Claude Code, Codex CLI). Hands off to $speckit-install when .specify/ is missing. Not for installing speckit for the first time (use $speckit-install), not for scaffolding a new spec ($speckit-scaffold-spec), and not for installing this plugin's bundled Codex subagents ($install)."
---

# SpecKit Upgrade

## Scope

Upgrade an existing SpecKit installation in the current repository
safely. Preserves `.specify/memory/constitution.md` and any other
locally-modified files via backup-then-force-then-restore. Handles
the v0.8.13 slash-command → skills migration. Supports upgrading
one or both integrations (`claude`, `codex`).

If `.specify/` is missing, hands off to `$speckit-install` —
upgrade only operates on existing installs.

This skill is **mutation-heavy** (it modifies files in `.specify/`,
`.claude/`, `.codex/`, and writes backups to `/tmp/`). It runs only
on explicit operator request and never auto-fires from other
skills.

## Scope Boundaries — Not For

- Initial install (no `.specify/` directory yet). That is
  `$speckit-install`. This skill hands off to it automatically.
- Scaffolding a new spec from the technical roadmap. That is
  `$speckit-scaffold-spec`.
- Installing this plugin's own bundled Codex subagent TOML files
  into `~/.codex/agents/`. That is `$install`.
- Upgrading the SpecKit CLI binary itself (`specify` package). The
  operator runs that with `uv tool install --force` — this skill
  detects when it's out of date and recommends the command, but
  does not run it for them.

## Input

Accept optional integration keys as arguments:

- `$speckit-upgrade` (upgrade all installed integrations interactively)
- `$speckit-upgrade claude`
- `$speckit-upgrade codex`
- `$speckit-upgrade claude codex`

## Hard Constraints

- Always snapshot the repo state to
  `/tmp/specify-upgrade-backup-<STAMP>/` BEFORE the first
  `specify integration upgrade` invocation.
- Never use `--force` on the first attempt. Try the safe path
  first; only escalate to `--force` after explicit operator
  confirmation AND after the backup exists.
- Never delete files from `.claude/commands/` or `.codex/prompts/`
  without explicit operator confirmation in the dedupe step.
- Never delete non-SpecKit-managed files. SpecKit-managed
  slash-command files are exactly those matching `speckit.*.md`
  (the dot-prefixed legacy form). Extension commands like
  `speckit.speckit-utils.doctor.md` are NOT SpecKit-managed and
  must be preserved.
- Never modify `.specify/memory/constitution.md` mid-flight without
  explicit operator instruction. Restore the operator's backup
  verbatim, or leave the freshly-templated placeholder in place if
  they explicitly said so.
- Never touch this plugin's own files (`.claude-plugin/`,
  `codex-skills/`, plugin's `commands/`).
- If any `specify` invocation fails for non-diff reasons (network,
  missing source bundle), STOP and report — do not retry silently.

## Procedure

### 1. Detect state; hand off if needed

```bash
test -d .specify && echo PRESENT || echo ABSENT
```

If ABSENT: STOP this skill and invoke `$speckit-install` (upgrade
operates only on existing installs).

If PRESENT: continue.

### 2. Capture current CLI version and installed integrations

```bash
command -v specify >/dev/null 2>&1 && specify --version || echo MISSING
specify self check 2>&1 || true
specify integration list 2>&1
```

Surface to the operator:

- Current CLI version (e.g. `specify 0.6.1`).
- Whether `specify self check` reports a newer release.
- Each installed integration with its current status.

If the CLI itself is outdated, recommend:

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

Ask the operator to either upgrade the CLI first (then re-invoke
this skill) or confirm they want to proceed with the current CLI
version.

### 3. Resolve which integrations to upgrade

If the operator passed keys, use them. Otherwise ask:

> Which integrations should I upgrade?
> - `<each-installed-key>` (currently installed)
> - `all` for everything that's installed
>
> If you want to ADD a new integration (e.g., add `codex` to a
> `claude`-only repo), use `$speckit-install <new-key>` instead.

### 4. Snapshot the repo state

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP=/tmp/specify-upgrade-backup-$STAMP
mkdir -p "$BACKUP"
cp -R .specify "$BACKUP/.specify"
for d in .claude .codex .github; do
  [ -e "$d" ] && cp -R "$d" "$BACKUP/$(basename $d)" || true
done
ls "$BACKUP"
```

Tell the operator: "Repo state snapshotted to `$BACKUP/`. Manual
rollback: `cp -R $BACKUP/.specify .` (and any other directories
listed)."

### 5. Per-integration upgrade

For each integration the operator chose:

#### 5a. Safe (no --force) attempt

```bash
specify integration upgrade <key> --script sh
```

The CLI is diff-aware. If it succeeds, capture output and move to
the next integration.

#### 5b. If blocked: structured triage

The CLI block message names each modified file. Surface them and
ask:

> The upgrade is blocked because these files are locally modified:
> - `<file1>`
> - `<file2>`
>
> Options:
>
> 1. `force-and-restore` — back up each modified file (already in
>    `$BACKUP`), run `--force` to take the new template, then offer
>    to restore your modifications on top. Recommended when the
>    upstream updates are bigger than your local edits.
>
> 2. `keep-mine` — skip this integration's upgrade. Modifications
>    stay; you miss the upstream template updates.
>
> 3. `manual-merge` — abort this skill, examine the diff yourself,
>    re-run after deciding.

On `force-and-restore`:

```bash
specify integration upgrade <key> --force --script sh
```

Then for each previously-modified file:

```bash
diff "$BACKUP/<file>" "<file>"
```

Ask whether to restore (file-by-file or all-at-once):

- `constitution.md` — almost always restore the backup. This is the
  operator's project content.
- Templates / scripts / gate validators — case-by-case. The CLI's
  new versions usually carry fixes/features the operator wants.

### 6. Slash-command → skills migration (v0.8.13)

After upgrading, the new skills directories may now exist alongside
the legacy slash-command files. Detect:

```bash
ls .claude/commands/speckit.*.md 2>/dev/null | head
ls .claude/skills/speckit-*/SKILL.md 2>/dev/null | head
ls .codex/prompts/speckit.*.md 2>/dev/null | head
ls .codex/skills/speckit-*/SKILL.md 2>/dev/null | head
```

If BOTH legacy and skills paths exist for an integration:

> Both legacy slash-commands and skills are installed for `<integration>`.
> The v0.8.13 default is skills-mode. The legacy slash-commands still
> work but create duplicate triggers. Options:
>
> 1. `dedupe` — delete the legacy `<path>/speckit.*.md` files.
>    Recommended unless downstream tooling references the
>    slash-command names.
> 2. `keep-both` — leave the duplicates in place.

On `dedupe`, delete only files matching `speckit.<single-word>.md`
(e.g. `speckit.constitution.md`, `speckit.specify.md`,
`speckit.plan.md`). Files like `speckit.speckit-utils.doctor.md`
and any non-`speckit.` files MUST be preserved — those are
extension commands or unrelated. Show the exact deletion list
before running `rm` so the operator can confirm.

### 7. Verify

```bash
specify check 2>&1
specify integration list 2>&1
```

Confirm each upgraded integration shows `installed` and reports the
new manifest. Report any verification mismatch — do not silently
continue.

### 8. Report

Return a structured summary:

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
- .specify/scripts/bash/check-prerequisites.sh (restored from backup)

**Next steps:**
1. Restart Codex (and Claude Code if it's running) so the new
   skills load.
2. Skim the summary above — if you preferred the old version of
   any file, restore from $BACKUP/.
3. Run `specify check` independently to confirm health.
```

Do not continue into any other workflow in the same skill. Upgrade
ends here.

## Failure Handling

STOP and report — do not improvise — when:

- The CLI itself is missing (uncommon for upgrade, but possible;
  recommend installing it via `$speckit-install`).
- A `specify integration upgrade` call fails for non-diff reasons.
- The backup directory could not be created (filesystem full,
  permission denied, etc.).
- The operator declines all three options in Step 5b for a blocked
  upgrade. Their choice stands; do not retry.
- A restore step fails mid-flight. Report which files succeeded,
  which did not, and the backup path.

The backup at `/tmp/specify-upgrade-backup-<STAMP>/` is the
operator's safety net. Surface it explicitly in the final report.

## Why This Skill Exists

The SpecKit CLI's `specify integration upgrade` is diff-aware and
blocks on locally-modified files, but its `--force` flag overwrites
them without any backup. This skill wraps the CLI to provide:

- Automatic timestamped snapshots before any mutation.
- A structured "what's modified, what do you want to do" prompt
  when the diff-aware path blocks.
- File-by-file restore decisions after `--force`.
- Explicit handling of the v0.8.13 slash-command → skills migration
  (with hard guarantees about preserving extension commands and
  non-SpecKit files).
- Symmetric Claude/Codex handling when both integrations are
  installed (operator doesn't have to remember the per-integration
  invocations).

For an initial install, use `$speckit-install`. The two skills
hand off to each other based on `.specify/` presence.

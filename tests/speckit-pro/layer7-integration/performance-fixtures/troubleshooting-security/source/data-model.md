# Data Model: Troubleshooting, Security, Trust, Update, And Rollback

DOC-008 models documentation content, not runtime data. These entities define the fields implementation must satisfy in Markdown tables and sections.

## Troubleshooting Row

**Purpose**: A symptom-driven row on `troubleshooting.md`.

**Fields**:

- `anchor`: stable heading or slug for direct support links
- `symptom`: user-observed failure or confusing behavior
- `platform`: one of `Claude Code`, `Codex`, or `Both`
- `likely_cause`: source-backed cause or bounded hypothesis
- `inspect_command_or_file`: read-only state-reporting command, platform detail view, manual file path, or source/reference link
- `recommended_fix`: manual recovery guidance, with side effects stated before mutating commands
- `follow_up_link`: install, reference, trust, or update/rollback route
- `source_citation`: official vendor doc, generated DOC-007 reference page, or checked-in source file

**Validation rules**:

- All rows must include every field.
- `inspect_command_or_file` must not contain login, install, remove, reload, restart, approve, edit, set, unset, delete, rebuild, config-write, cache-edit, or token/secret-printing commands.
- Required coverage includes install failure, marketplace source, generated payload, installed cache/runtime state, permissions/approvals, Spec Kit CLI, GitHub CLI, jq, Codex custom agents, path confusion, version drift, and source-vs-generated-payload mismatch.

## Trust Claim

**Purpose**: A statement on `security-and-trust.md` about platform behavior, repository facts, or recommended practice.

**Fields**:

- `claim`: concise statement
- `platform`: `Claude Code`, `Codex`, `Both`, or `Racecraft`
- `evidence_type`: `official vendor behavior`, `repository fact`, or `recommended practice`
- `citation`: narrow official doc, generated reference page, or checked-in file
- `boundary_note`: what the claim does not prove

**Validation rules**:

- Official vendor behavior claims cite current Claude Code or OpenAI Codex docs.
- Repository facts cite checked-in Racecraft source or generated DOC-007 reference pages.
- Recommended practice must be phrased as derived guidance, not as a platform guarantee, security audit, certification, formal threat model, or control attestation.

## Recovery Case

**Purpose**: A procedural case on `update-and-rollback.md`.

**Fields**:

- `case`: one of `update`, `refresh`, `reinstall`, `remove`, `rollback`, `stale payload`, `stale cache`, or `version sync`
- `platform`: `Claude Code`, `Codex`, or `Both`
- `checkpoint`: read-only command, detail view, file path, or reference link to inspect before action
- `manual_action`: operator-run recovery action
- `side_effect`: expected mutation or state change
- `reload_or_restart`: whether Claude Code reload or Codex restart is required
- `source_citation`: official or repository citation
- `last_resort_boundary`: cache mutation caveat when applicable

**Validation rules**:

- Every case must distinguish checkpoint from manual action.
- Direct cache mutation must never be the default fix.
- Codex custom-agent reinstall must remain separate from plugin refresh and restart.
- Payload rebuild and version-sync scripts may be cited as maintainer/source-infrastructure evidence or handoff points, not as DOC-008 end-user recovery commands.

## Read-Only Inspection

**Purpose**: A safe diagnostic action shown in a troubleshooting inspect cell or recovery checkpoint.

**Allowed forms**:

- State-reporting command
- Platform detail view
- Manual file path inspection
- Generated reference link
- Checked-in source link

**Forbidden forms**:

- Login, install, uninstall, remove, reload, restart, approve, edit, set, unset, delete, rebuild, cache-edit, config-write, or token/secret-printing command

## Manual Recovery Action

**Purpose**: A user-run action that may mutate local plugin state, marketplace state, copied payloads, process state, custom-agent registration, or runtime cache state.

**Fields**:

- `action`
- `side_effect_before_command`
- `operator_scope`
- `rollback_or_reversal_hint`

**Validation rules**:

- Must appear outside inspect/checkpoint cells.
- Must name expected side effects before command examples.
- Must preserve organization-managed policy boundaries and avoid bypass guidance.

## Rollback Anchor

**Purpose**: A known state used to return to a previous working install.

**Allowed anchors**:

- Marketplace source
- Git ref or commit reference
- Generated payload path
- Manifest version
- CLI JSON field when officially documented
- Generated source-vs-dist reference

**Validation rules**:

- Anchors must cite source evidence.
- Installed cache paths count as official vendor behavior only when current vendor docs explicitly document the exact path or behavior.

## Evidence Source

**Purpose**: A citation target for user-facing claims.

**Fields**:

- `label`
- `url_or_repo_path`
- `evidence_type`
- `covers`
- `last_verified`

**Validation rules**:

- Official vendor docs use external URLs and `last_verified: 2026-06-18`.
- Racecraft facts use generated DOC-007 reference pages or checked-in source paths.
- Generated reference subpages must not be hand-edited for DOC-008 backlinks.

# Contract: Migration Report JSON

Every PRSG-011 migration command emits exactly one compact JSON object to stdout.
Stderr is reserved for shell-level usage or fatal diagnostics.

## Common Object

```json
{
  "schema_version": 1,
  "script": "migrate-structure",
  "mode": "dry-run",
  "repo_root": "/absolute/repo",
  "spec_dir": null,
  "active_feature": {
    "state": "absent",
    "path": null,
    "reason": "feature_json_missing"
  },
  "dirty_tree": {
    "is_dirty": false,
    "entries": [],
    "apply_blocked": false
  },
  "backup": {
    "path": "/tmp/speckit-migration-backup-20260608T000000Z",
    "created": false
  },
  "status": "pending",
  "items": [],
  "recovery": {
    "available": false,
    "hint": null
  }
}
```

## Field Semantics

| Field | Type | Semantics |
|-------|------|-----------|
| `schema_version` | integer | Report schema version. PRSG-011 starts at `1`. |
| `script` | string | `migrate-structure` or `relocate-process-artifacts`. |
| `mode` | string | `dry-run` or `apply`. |
| `repo_root` | string | Absolute repository root after argument/default resolution. |
| `spec_dir` | string or null | Repo-relative spec path for Tier-2; null for repo migration. |
| `active_feature` | object | Parsed `.specify/feature.json` state. |
| `dirty_tree` | object | Dirty-tree status from `git status --porcelain=v1 --untracked-files=all`. |
| `backup` | object | Planned or created backup location; `created` is true only after the backup exists on disk. |
| `status` | string | Overall command result. |
| `items` | array | Deterministically ordered itemized decisions. Each item includes an `action`, a repo-relative path or target identifier when applicable, and a stable `reason` when the action needs operator interpretation. |
| `recovery` | object | Restore instructions when a backup exists; post-backup failures must name `backup.path` in the hint. |

## Enumerations

### `active_feature.state`

- `absent`
- `valid`
- `invalid`

### `status`

- `pending`
- `applied`
- `noop`
- `blocked_dirty_tree`
- `blocked_active_feature_invalid`
- `blocked_collision`
- `blocked_missing_moc`
- `blocked_usage`
- `failed_backup`
- `failed_marker_write`
- `failed_move`
- `failed_stamp`
- `failed_generator`

### `items[].reason`

For `skipped_out_of_scope`, `reason` MUST be one of:

- `non_speckit_namespace`: the first dash-delimited segment is all-alpha and is
  not `prsg` or `spec`.
- `date_named_legacy_namespace`: the basename or archive ID starts with `YYYY`,
  `YYYY-MM`, or `YYYY-MM-DD` followed by end-of-string or `-`.

### `items[].action`

- `pending`
- `applied`
- `noop_current`
- `skipped_frozen_in_flight`
- `skipped_out_of_scope`
- `protected_contract`
- `move`
- `normalize`
- `stamp`
- `generated_update`
- `backup`
- `collision`
- `recovery`
- `failed_backup`
- `failed_marker_write`
- `failed_move`
- `failed_stamp`
- `failed_generator`

## Determinism Rules

- Object keys are emitted in the stable order shown by this contract.
- `items` are sorted by tier, then action, then repo-relative path or target
  identifier, then reason.
- `dirty_tree.entries` preserve `git status --porcelain=v1` order after command
  output normalization.
- Dry-run never creates the backup directory.
- Tests may set deterministic backup root and timestamp environment overrides.
- Reports never include elapsed time, random values, process IDs, or hostnames.

## Dirty-Tree Rules

Dry-run reports dirty-tree state but never blocks on it. Apply mode reports
`blocked_dirty_tree` and exits before backup or mutation when any dirty entry is
present.

## Active-Feature Rules

Missing `.specify/feature.json` is `absent` and does not block. Valid
`feature_directory` freezes the matching spec and is reported as
`skipped_frozen_in_flight`. Invalid active-feature state is reported by dry-run
and blocks apply before backup or mutation.

## Failure and Recovery Rules

- Pre-mutation blocked statuses (`blocked_dirty_tree`,
  `blocked_active_feature_invalid`, `blocked_collision`, `blocked_missing_moc`,
  `blocked_usage`) never create a backup and report `recovery.available` as
  false.
- Backup creation failure reports `failed_backup`, keeps `backup.created` false,
  and reports `recovery.available` as false.
- Any failure after backup creation reports the stage-specific status
  (`failed_marker_write`, `failed_move`, `failed_stamp`, or
  `failed_generator`), keeps `backup.created` true, and reports
  `recovery.available` as true with a restore hint that names `backup.path`.
- After a post-backup failure, the command stops and does not continue later
  moves, stamps, marker writes, or generated-zone updates.

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
| `backup` | object | Planned or created backup location. |
| `status` | string | Overall command result. |
| `items` | array | Deterministically ordered itemized decisions. |
| `recovery` | object | Restore instructions when a backup exists or would exist. |

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

## Determinism Rules

- Object keys are emitted in the stable order shown by this contract.
- `items` are sorted by tier, then action, then repo-relative path.
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

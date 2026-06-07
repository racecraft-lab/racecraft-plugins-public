# Contract: PRS manifest (repo-local committed source) — D3 / FR-010 / FR-011

The pull-requests zone renders **only** from this repo-local committed source.
The generator never contacts the network or `gh` to populate it (FR-010). PRSG-003
ships the *renderer* + this input contract + the fixture; the *writer* that
populates this file when a slice merges is PRSG-009 (out of scope here).

## Location

```text
specs/<branch>/.process/prs.json
```

Per-spec, under that spec's own `.process/` subtree. Because it lives in the
spec's tree, when present it is itself one BACKLINKS reachability entry (intended;
it resolves fine).

## Shape

```json
{
  "schemaVersion": 1,
  "records": [
    { "slice": "PRSG-003", "pr": 117, "merged_sha": "abc1234" }
  ]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schemaVersion` | integer | yes | `1` for this contract; carried so PRSG-009 can evolve the writer without breaking this renderer |
| `records` | array | yes | may be empty (`[]`) |
| `records[].slice` | string | yes | a spec/slice identifier; normalized via `moc_normalize` for ordering |
| `records[].pr` | integer | yes | PR number |
| `records[].merged_sha` | string | yes | short or full merged commit SHA |

Parsed with `jq` (constitution VI: `jq` over `sed`/`awk` for JSON).

## Rendering

- Each record renders as **plain text**, not a `[]()` link, e.g.
  `PRSG-003 · PR#117 · abc1234`. Plain text keeps the PRS zone link-free so it
  never introduces a link the stale-index lint must resolve.
- Order: by normalized `slice` ascending (`moc_normalize`), then `pr` ascending.
- The rendered rows go between the `GENERATED:PRS:START` / `GENERATED:PRS:END`
  sentinels (whole-zone replace).

## Empty / absent / malformed behavior

| Condition | Behavior |
|-----------|----------|
| File absent | empty-but-valid (link-free) PRS zone — NOT an error (FR-011) |
| `records: []` | empty-but-valid (link-free) PRS zone — NOT an error (FR-011) |
| Malformed JSON / unreadable | fail safe: actionable message + exit 2; no partial write (FR-016) — distinct from the absent/empty case |
| Unknown `schemaVersion` | conservative: render the records it understands; on an unparseable structure, fail safe per FR-016 |

## Determinism

The manifest is a committed file, so identical content always renders the
identical PRS zone (FR-003). Fixtures supply both a populated manifest and an
absent/empty manifest to exercise both the rendered-rows path and the
empty-but-valid path (L4 + L1).

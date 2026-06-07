# Contract: `estimate-reviewable-loc.sh` output

The NEW plan-phase estimator (US1). Deterministic bash+jq. Reads a `plan.md` and projects
production-LOC from its `## Declared File Operations` block. Emits one JSON object to stdout.

## Invocation

```bash
estimate-reviewable-loc.sh <path-to-plan.md>
```

## Exit codes (budget verdict NEVER drives exit)

| Code | Meaning |
|------|---------|
| 0 | Ran successfully — for ALL three statuses (`pass`, `over_budget`, `not_estimated`). The budget verdict is in the JSON `status`, never in the exit code. Over-budget is advisory (FR-004): the estimator returns 0 so the autonomous plan phase continues. |
| 2 | Usage error (missing/extra args) or unreadable/absent input file. |

(There is no exit `1` — the estimator does not block. This is the deliberate difference from
`reviewability-gate.sh`, which exits `1` on `block`. FR-004/FR-007.)

## Status (three-value — FR-003)

| `status` | When | `projected` |
|----------|------|-------------|
| `pass` | A parseable block exists AND projected production-LOC ≤ budget | the integer projection |
| `over_budget` | A parseable block exists AND projected production-LOC > budget | the integer projection |
| `not_estimated` | No `## Declared File Operations` block, or zero lines match the entry grammar | `null` (NEVER recorded as within-budget — avoids the vacuous-pass failure mode) |

## JSON shape

```json
{
  "tool": "estimate-reviewable-loc",
  "status": "pass",
  "projected": 320,
  "declared_files": {
    "production": 8,
    "new": 8,
    "modified": 0,
    "total_entries": 8
  },
  "greenfield": true,
  "thresholds": {
    "warn": 600,
    "block": 1200,
    "greenfield_multiplier": 1.5,
    "base_warn": 400,
    "base_block": 800
  }
}
```

### Field semantics

| Field | Type | Notes |
|-------|------|-------|
| `tool` | string | constant `"estimate-reviewable-loc"` (distinguishes from the gate's `mode`) |
| `status` | string | `pass` \| `over_budget` \| `not_estimated` (FR-003) |
| `projected` | integer \| null | projected production-LOC = (count of declared **production** files, by `is_production_file` & not `is_excluded_generated`) × `PROD_LOC_PER_FILE`. `null` iff `not_estimated`. |
| `declared_files.production` | integer | declared entries that pass `is_production_file` & not `is_excluded_generated` |
| `declared_files.new` | integer | declared entries with `STATUS = NEW` |
| `declared_files.modified` | integer | declared entries with `STATUS = MODIFIED` |
| `declared_files.total_entries` | integer | all grammar-matching entries |
| `greenfield` | boolean | true iff every non-excluded declared entry is `NEW` and none is `MODIFIED` (FR-006 — same file-set rule as the gate's diff-mode `A`-status detector, FR-009). `false` when `not_estimated`. |
| `thresholds.warn` / `.block` | integer | the **applied** thresholds (greenfield-scaled when `greenfield` is true) |
| `thresholds.greenfield_multiplier` | number | `1.5` |
| `thresholds.base_warn` / `.base_block` | integer | the un-scaled `400` / `800` |

### `not_estimated` example

```json
{
  "tool": "estimate-reviewable-loc",
  "status": "not_estimated",
  "projected": null,
  "declared_files": { "production": 0, "new": 0, "modified": 0, "total_entries": 0 },
  "greenfield": false,
  "thresholds": { "warn": 400, "block": 800, "greenfield_multiplier": 1.5, "base_warn": 400, "base_block": 800 }
}
```

## Determinism (FR-002 / SC-001)

Identical `plan.md` input ⇒ byte-identical stdout. No timestamps, no `$RANDOM`, no
unsorted-set iteration that can reorder. The L4 determinism fixture asserts the parsed
planned-file count AND `projected` equal a **known expected value** against a representative
non-empty block (not merely two-run equality), then asserts run-2 is byte-identical to run-1.

## Declared-files parse grammar (plan.md `## Declared File Operations`)

Only lines matching this POSIX ERE are counted; all other lines (prose, blank, comments) are
ignored:

```text
^[[:space:]]*[-*][[:space:]]+(NEW|MODIFIED)[[:space:]]+([^[:space:]]+)[[:space:]]*$
```

Group 1 = `STATUS` (`NEW`|`MODIFIED`); group 2 = repo-relative path (full path required so
`is_production_file`'s prefix arm can classify — see plan.md Decision 1).

**De-duplication (no double-counting):** entries are de-duplicated by repo-relative path
before counting — a path that appears more than once in the block contributes **once** to
`declared_files.*` and to `projected`. This is the estimator's counterpart to the gate's
per-mode path-uniqueness: the gate's `setup`/`tasks` modes de-duplicate explicitly via
`sort -u` (`reviewability-gate.sh:191`), and its `diff` mode is inherently per-path-unique
because `git diff --name-only`/`--numstat` (`reviewability-gate.sh:221-222`) never list the
same path twice. The estimator parses free-form `plan.md` lines, where a path genuinely can
repeat, so it must de-duplicate explicitly to match that guarantee. This keeps the projection
stable under a duplicated declaration and preserves the byte-identical-output contract
(determinism of meaning, not just of formatting). If the same path appears once as `NEW`
and once as `MODIFIED`, the de-duplicated entry is treated as `MODIFIED` (so the slice is
correctly NOT greenfield — fail-safe toward "an existing file is touched", consistent with
FR-006's "any modified existing file disqualifies greenfield").

## Known limitation (recorded in code per spec Assumptions; do NOT "fix" here)

`is_production_file` matches `src/ app/ lib/ scripts/` prefixes + JS/TS/SQL extensions. It does
NOT match this repo's plugin production code (`.sh` under `speckit-pro/skills/`), so plugin-script
slices (including PRSG-006's own) under-count to `production: 0`. Broadening the predicate is
PRSG-001 scope, out of scope here. The estimator MUST carry this as a code comment.

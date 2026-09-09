# Fixtures: spec-index generator

Committed fixture spec trees consumed by
`tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py` and
`tests/speckit-pro/unit/test-generate-spec-index.py`. These are **test inputs
only** — no production code lives here.

The generated zones use this exact byte framing: one blank line before
`GENERATED:INDEX:START`, one blank line between each zone, an empty zone is its
`START`/`END` lines on consecutive lines with no body between them, and the file
ends with `GENERATED:BACKLINKS:END` + a single trailing newline.

## Fixture cases

| Dir | Case | Behavior under test |
|-----|------|------------------------|
| `current-empty/` | Version-marked MOC, all three zones present-but-empty, NO sibling artifacts, no `prs.json`. A regen reproduces all-empty zones → zero diff → `--check` exit 0. | Current-path no-op |
| `stale-fill/` | Version-marked MOC with empty zones BUT sibling stub artifacts + a populated `.process/prs.json`. A regen fills BACKLINKS + PRS → non-empty diff → `--check` exit 1. Also the ordering fixture (≥2 precedence buckets + `.process`). | Present-zone rebuild, stale path, and ordering |
| `inject-missing-all/` | Version-marked MOC with NO zone markers at all and sibling stub artifacts. Inject-if-missing adds the three empty zones at the canonical anchor, then fills them. | Inject-if-missing |
| `skip-one-missing/` | Version-marked MOC with ONLY the PRS marker pair removed (INDEX + BACKLINKS present); sibling artifacts present. The missing PRS zone is skipped; INDEX + BACKLINKS are still rebuilt. | Skip one missing zone |
| `prs-malformed/` | Version-marked MOC + a `.process/prs.json` containing invalid JSON. Fail-safe: exit 2, distinct from missing data. | Malformed PR data |
| `roadmap-moc/` | A roadmap-MOC home note at `docs/ai/specs/<slug>-roadmap-MOC.md` carrying ONLY the INDEX sentinel pair (gated), plus `specs/` dirs: two normal gated specs, one empty-`status` gated spec, one absent-`spec_id` gated spec, one legacy non-gated dir. Each home INDEX is populated from the repository scan with one row per gated spec that home owns (non-empty `spec_id`, normalized-ID ascending, relative `[]()` links); the empty-`status` spec still emits a row with a blank status; the absent-`spec_id` spec, legacy dir, and specs owned by another home are skipped; every per-spec SPEC-MOC INDEX stays empty/byte-identical. | Home-note index behavior |

`SPEC-MOC.md` is the map note itself and is therefore NOT one of its own
BACKLINKS rows.
This is what lets `current-empty/` (only a `SPEC-MOC.md`, no artifacts) regenerate
to an all-empty, zero-diff map.

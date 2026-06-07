# Fixtures: spec-index generator (PRSG-003)

Committed fixture spec trees consumed by the Layer 1 determinism fixture
(`../validate-spec-index-determinism.sh`) and the Layer 4 unit test
(`../../layer4-scripts/test-generate-spec-index.sh`). These are **test inputs
only** — no production code lives here.

The generated zones reproduce the byte framing from
`specs/prsg-003-spec-index/contracts/sentinel-grammar.md` exactly: one blank line
before `GENERATED:INDEX:START`, one blank line between each zone, an empty zone is
its `START`/`END` lines on consecutive lines with no body between them, and the
file ends with `GENERATED:BACKLINKS:END` + a single trailing newline.

## Fixture cases (T003)

| Dir | Case | FR/behavior under test |
|-----|------|------------------------|
| `current-empty/` | Version-marked MOC, all three zones present-but-empty, NO sibling artifacts, no `prs.json`. A regen reproduces all-empty zones → zero diff → `--check` exit 0. | FR-008, current path (T006 a) |
| `stale-fill/` | Version-marked MOC with empty zones BUT sibling stub artifacts + a populated `.process/prs.json`. A regen fills BACKLINKS + PRS → non-empty diff → `--check` exit 1. Also the ordering fixture (≥2 precedence buckets + `.process`). | FR-005/FR-006/FR-009→present-zones-rebuilt, stale path, ordering (T006 a/i) |
| `inject-missing-all/` | Version-marked MOC with NO zone markers at all and sibling stub artifacts. Inject-if-missing adds the three empty zones at the canonical anchor, then fills them. The injected block must be byte-identical to a template-born block. | FR-008/FR-017 inject-if-missing (T006 h) |
| `skip-one-missing/` | Version-marked MOC with ONLY the PRS marker pair removed (INDEX + BACKLINKS present); sibling artifacts present. The missing PRS zone is skipped; INDEX + BACKLINKS are still rebuilt. | FR-009 skip-one (T006 d) |
| `unbalanced-marker/` | Version-marked MOC with a duplicated/unbalanced BACKLINKS marker pair. Fail-safe: exit 2, no partial write. | FR-022 fail-safe (T006 e) |
| `prs-populated/` | Version-marked MOC + a populated `.process/prs.json` with two records (out of `slice`/`pr` order, to exercise the sort). | D3 PRS render + ordering (T006 g) |
| `prs-empty/` | Version-marked MOC + a `.process/prs.json` whose `records` is `[]`. Empty-but-valid link-free PRS zone, NOT an error. | FR-011 (T006 g) |
| `prs-absent/` | Version-marked MOC, NO `.process/prs.json` at all. Empty-but-valid link-free PRS zone, NOT an error. | FR-011 (T006 g) |
| `prs-malformed/` | Version-marked MOC + a `.process/prs.json` containing invalid JSON. Fail-safe: exit 2, distinct from absent/empty. | FR-016 (T006 g) |
| `legacy-skip/` | A NON-version-marked legacy spec (no `structureVersion`). Skipped and left unmodified by any run (stays byte-identical). | FR-007 skip (consumed by the L1 determinism run) |

`SPEC-MOC.md` is the map note itself and is therefore NOT one of its own
BACKLINKS rows (FR-006 / SC-002: "every **non-map** document … is reachable").
This is what lets `current-empty/` (only a `SPEC-MOC.md`, no artifacts) regenerate
to an all-empty, zero-diff map.

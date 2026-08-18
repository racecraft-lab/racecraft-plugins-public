# Implementation Notes: ART-007

### T001

**Deviations/Edge cases/Surprises:** None. `python3 tests/speckit-pro/run-all.py`
finished green at 7399/7399 (L1 1447, L4 5766, L5 186), which matches the G0
baseline recorded at Phase 0 exactly. No drift diagnostic is owed. The recorded
baseline is preserved rather than recaptured, per the autopilot's Step 0.6e rule:
a baseline recaptured after planning would already contain whatever this run
adds, making the G7 comparison vacuous.

### T002

**Deviations/Edge cases/Surprises:** Already satisfied, so nothing was run.
`docs-site/node_modules` is present and populated (`.pnpm` store plus the six
direct dependencies and three dev dependencies `docs-site/package.json`
declares). Node resolves to v24.11.1, above the ≥22.12 floor the docs-site
toolchain needs. The worktree was bootstrapped during the plan stage and the
install survives into this stage.

### T003

**Deviations/Edge cases/Surprises:** Already satisfied, so nothing was run.
`git config --get merge.generated.name` returns
`keep ours; regenerate after merge` and `merge.generated.driver` returns
`exit 0`. The driver is per-clone configuration that cannot be committed, so
verifying it rather than assuming it is the point of the task.

### T004

**Deviations/Edge cases/Surprises:** None. The verdict below is restated from
plan.md, not recomputed — recomputing it is the failure mode the task exists to
prevent, because a fresh hand count of 11 production files would trip a naive
block reading the plan already ratified against.

**Ratified reviewability verdict, carried forward unchanged:**

| Signal | Value |
|---|---|
| `estimate-reviewable-loc` | 0 projected, against 400/800 thresholds — 0 by its own production-file definition on a Markdown/JSON/stdlib-Python surface |
| `estimate-spec-size` at the spec's 10 projected production files | `{"estimated_loc": 335, "suggested_slices": 1, "status": "ok"}` |
| `estimate-spec-size` at the plan's 11 | `{"estimated_loc": 355, "suggested_slices": 1, "status": "ok"}` |
| Hand count | 16 total files (11 under `speckit-pro/`, 5 under `tests/speckit-pro/`) |
| Against the file lines | one above the 15-file warn line, well under the 25-file block line |
| Primary surfaces | one (harness/adapter), so the multi-surface rule holds |
| **Split decision** | **no split** |

The two design corrections recorded in the workflow file as DC-1 and DC-2 add no
file and change no surface, so this verdict stands unamended.

### T005

**Deviations/Edge cases/Surprises:** The capture was widened past what the task
originally asked for. A pass/fail capture cannot see an SC-008 regression in
which a fixture still fails but for a newly different reason, and the `else` arm
this feature introduces is exactly the kind of edit that can cause one. So the
baseline records each fixture's **failure rule strings**. Captured outside the
repository, in terminal output only; no file was added.

| Fixture | Status | Mode | Failure rules |
|---|---|---|---|
| `valid-single.json` | passed | single | — |
| `valid-split.json` | passed | split | — |
| `invalid-malformed-json.json` | failed | null | `input.error` |
| `invalid-missing-evidence.json` | failed | single | `body.protected_fingerprint`, `body.title`, `evidence.scope.changed_files`, `evidence.verification`, `packet.schema.const`, `packet.schema.min_items`, `packet.schema.min_length`, `packet.schema.required` |
| `invalid-no-feature-dir.json` | failed | single | `evidence.scope.changed_files`, `evidence.verification`, `input.path.validation_result_path`, `packet.schema.required` |
| `invalid-protected-edit.json` | failed | single | `body.protected_fingerprint`, `body.title` |
| `invalid-schema-with-feature-dir.json` | failed | single | `evidence.scope.changed_files`, `evidence.verification`, `input.path.validation_result_path`, `packet.schema.required` |
| `invalid-title-token.json` | failed | single | `body.protected_fingerprint`, `body.title` |
| `split-partial-failure-state.json` | failed | null | `evidence.scope.changed_files`, `evidence.verification`, `input.path.validation_result_path`, `packet.schema.additional_properties`, `packet.schema.required` |

Two observations that constrain the T010 validator guard. Four fixtures already
emit `evidence.verification` and `evidence.scope.changed_files`, so the guard
must be `mode != "draft"` rather than `mode == "single"` — two of those four
carry a null `mode`, and a `mode == "single"` guard would silently drop their
failures. And `mode` is absent on `invalid-malformed-json.json` and
`split-partial-failure-state.json`, so the guard must tolerate `None` without
raising.

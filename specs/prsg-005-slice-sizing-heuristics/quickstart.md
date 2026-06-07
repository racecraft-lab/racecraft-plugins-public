# Quickstart: PRSG-005 — Vertical-slice sizing heuristics

How to run and verify the feature once implemented. All commands below run from the
**repository root** of your checkout (the directory that contains `speckit-pro/`, `specs/`,
and `tests/`).

## Run the estimator directly

```bash
# (Exact arg syntax finalized in Tasks; conceptually:)
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --user-stories 2 --files 8 --frs 12 --new-vs-modify new
# → {"estimated_loc":...,"suggested_slices":...,"status":"ok|warn"}

# Spike (research-only) slice:
bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh --spike
# → {"estimated_loc":0,"suggested_slices":1,"status":"ok"}
```

## Verify the estimator (Layer 4)

```bash
bash tests/speckit-pro/run-all.sh --layer 4   # runs test-estimate-spec-size.sh among others
```

Asserts: byte-identical output for identical inputs; `ok` at exactly the ceiling and `warn`
strictly over; spike → `ok`/1/0; zero/negative/missing/malformed → predictable, non-crashing.

## Verify structural + Codex parity (Layer 1) and full fast suite

```bash
bash tests/speckit-pro/run-all.sh --layer 1   # structural + validate-codex-skills.sh
bash tests/speckit-pro/run-all.sh             # Layers 1 + 4 + 5 (the CI gate for this feature)
```

## Exercise the skill behavior (developer-local, not CI)

- **Layer 2 (trigger routing)**: confirm new sizing/slicing phrases route to the right skill
  AND existing phrases for both skills still route unchanged (no over/under-trigger
  regression).
- **Layer 3 (functional)**: run a `speckit-prd` interview on a would-be-fat fixture idea and
  confirm the emitted catalog is multiple thin vertical slices, each with a populated
  `Projected reviewable LOC` from the estimator + a one-line INVEST/vertical-slice rationale; run a
  `grill-me` interview on a fat/horizontal single spec and confirm the slice-sizing branch
  triggers, asks the split question, and records the chosen split in the Design Concept doc.
- **Layer 8 (Codex parity)**: confirm both `codex-skills/` mirrors behave equivalently
  (free-text Q&A loop standing in for `AskUserQuestion`).

## Invariants to confirm

- **Advisory-only (FR-011)**: no path blocks, gates, or rejects; every `warn` or unavailable
  estimate yields advisory text and a continued interview.
- **Single source of truth**: SPIDR/INVEST/vertical-slicing guidance exists in exactly one
  doc (`slicing-heuristics.md`); both skills carry only a short inline summary + a link; both
  Codex mirrors carry the equivalent.
- **Forward-estimate caveat (FR-015)**: the shared doc states the estimate is an approximate
  forward guess, NOT the authoritative reviewable-LOC count (PRSG-006 owns that).

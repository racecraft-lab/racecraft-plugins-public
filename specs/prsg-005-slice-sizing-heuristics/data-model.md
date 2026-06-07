# Data Model: PRSG-005 — Vertical-slice sizing heuristics

This feature has no persistent storage. The "data model" is the estimator's
input/output contract plus the two shared constants/assets. Entities below are derived
directly from spec.md (Key Entities + FR-006/007/008/016/017).

## Entity: Size signals (estimator input)

The structured, pre-implementation size indicators a skill collects for a spec and passes
to `estimate-spec-size.sh`. The skill supplies these as args/JSON; the estimator never
reads roadmap markdown itself.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `user_stories` | integer ≥ 0 | yes | Number of user stories in the spec/catalog entry. |
| `files_or_surfaces` | integer ≥ 0 | yes | Number of files/surfaces the spec touches. |
| `functional_requirements` | integer ≥ 0 | yes | Number of functional requirements. |
| `new_vs_modify` | enum `new` \| `modify` | no (default `new`) | Whether the spec is net-new or modifies existing code; defaults to `new` when absent (matches contract §Inputs). |
| `spike` | boolean | no (default false) | Marks the slice as a SPIDR "Spike" (research-only). FR-017. |

**Validation / robustness rules (FR-016):**

- Missing or empty numeric signals are treated as `0` (a sensible, non-misleading default),
  never a crash.
- Negative numeric signals are clamped/normalized to `0` rather than producing a misleading
  negative estimate.
- Malformed (non-numeric) input does not crash the estimator; it normalizes to `0` rather
  than degrading to an arbitrary value.
- **Pinned bad-input status**: each non-conforming signal normalizes to `0`, and `status`
  then follows the same at-ceiling boundary rule used for normal inputs on the resulting
  `estimated_loc` — not a separate code path. When every signal is bad/absent the estimate
  is `0` (at/under the ceiling) → `status` is **`ok`**; a mixed input keeps its valid signals
  and is sized normally. Here `ok` means "there is no over-ceiling estimate to flag", not
  "the input was validated as good" (the same `ok ≠ endorsement` framing the spike rule
  uses). A bad input therefore never trips a misleading `warn` and introduces no third
  status value.
- The estimator never raises a hard error or non-zero "block" exit that a caller could read
  as a gate — robustness behavior keeps the advisory-only invariant (FR-011) intact.

## Entity: Size estimate (estimator output)

The JSON object the estimator emits to stdout.

| Field | Type | Notes |
|-------|------|-------|
| `estimated_loc` | integer ≥ 0 | The forward LOC guess. `0` for a spike. |
| `suggested_slices` | integer ≥ 1 | Recommended number of thin vertical slices. `1` for a spike. |
| `status` | enum **`ok` \| `warn`** | Exactly two values — no third value ever (FR-017). |

**State / boundary rules:**

- **At-ceiling boundary**: when `estimated_loc == ceiling`, `status = ok`. `status = warn`
  only when `estimated_loc` is **strictly greater than** the ceiling. (Edge Cases; Clarify S1.)
- **Spike**: when `spike = true`, the estimator **skips** the LOC-threshold comparison and
  returns `status: ok`, `suggested_slices: 1`, `estimated_loc: 0`. `ok` here means "LOC
  sizing is not applicable to a research slice" (INVEST "Estimable" escape hatch), not
  "trivially small". (FR-017.)
- **suggested_slices** for a non-spike slice = `ceil(estimated_loc / ceiling)` (documented
  formula; minimum `1`). The L4 fixtures pin the integer rounding at and around the ceiling.
- **Determinism (FR-007)**: identical inputs always yield byte-identical output — no clocks,
  randomness, or environment dependence.

## Entity: Documented LOC ceiling (constant)

The single source-of-truth constant (~400 reviewable LOC). FR-008.

- Lives as **one hardcoded constant** in `estimate-spec-size.sh`, carrying a comment
  "keep in sync with the documented ceiling in slicing-heuristics.md".
- Referenced (by value, in prose) by `slicing-heuristics.md` and summarized in both skills.
- Shared with PRSG-006 **by documentation only** — PRSG-005 emits no artifact PRSG-006 reads.

## Entity: Shared slicing-heuristics reference (document)

The one canonical document holding SPIDR + INVEST + vertical-slicing guidance. FR-010, FR-015.

- Path: `speckit-pro/skills/speckit-coach/references/slicing-heuristics.md`.
- Holds the canonical guidance prose; both skills carry only a short inline summary + a link.
- MUST state the FR-015 caveat: the estimate is an approximate **forward** guess made before
  implementation, NOT the authoritative reviewable-LOC count (that is PRSG-006's
  `estimate-reviewable-loc.sh`).
- MUST document the FR-017 spike-as-timebox-slice-type note and the at-ceiling boundary rule
  so the two skills stay consistent.

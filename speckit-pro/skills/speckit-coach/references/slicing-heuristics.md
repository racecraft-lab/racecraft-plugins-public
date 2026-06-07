# Vertical-Slice Sizing Heuristics

The single source of truth for how `speckit-pro` decomposes work into thin,
PR-sized vertical slices. Both `speckit-prd` (catalog-level decomposition) and
`grill-me` (per-spec validation and split) carry only a short inline summary and
link here — there is no duplicated guidance prose anywhere else.

This guidance is **advisory**. Nothing here blocks, gates, or rejects a spec.
The companion estimator (`estimate-spec-size.sh`) and these heuristics exist to
make the right-sizing visible at authoring time, not to enforce a hard limit.

## Contents

- [The ~400 reviewable-LOC ceiling](#the-400-reviewable-loc-ceiling)
- [SPIDR — how to split a story](#spidr--how-to-split-a-story)
- [INVEST — what a good slice looks like](#invest--what-a-good-slice-looks-like)
- [Vertical slicing — cut end-to-end, not by layer](#vertical-slicing--cut-end-to-end-not-by-layer)
- [The estimate is a forward guess, not the authoritative count](#the-estimate-is-a-forward-guess-not-the-authoritative-count)
- [Spikes are sized by timebox, not LOC](#spikes-are-sized-by-timebox-not-loc)
- [The at-ceiling boundary rule](#the-at-ceiling-boundary-rule)
- [How the estimator turns signals into a guess](#how-the-estimator-turns-signals-into-a-guess)

## The ~400 reviewable-LOC ceiling

A single spec (and the PR that implements it) should stay at or under
**~400 reviewable lines of code**. Above that, a reviewer's defect-detection
rate drops sharply and the change becomes hard to reason about as one unit.

This ceiling is the **single source-of-truth constant**. It lives as one
hardcoded value in `estimate-spec-size.sh` (carrying a "keep in sync with the
documented ceiling in slicing-heuristics.md" comment) and is referenced by value
here and summarized in both skills. If the ceiling ever changes, it changes in
the script and this doc together — there is no second copy.

## SPIDR — how to split a story

SPIDR is a story-splitting mnemonic. When a slice is too big, split it along one
of these five seams (each produces thinner slices that still deliver value):

- **S — Spike**: a research-only slice that buys down uncertainty before the real
  work. Sized by timebox, not LOC (see
  [Spikes are sized by timebox, not LOC](#spikes-are-sized-by-timebox-not-loc)).
- **P — Path**: split by the distinct paths through the workflow (happy path
  first; alternate, error, and edge paths as later slices).
- **I — Interface**: split by interface or surface (one entry point, one command,
  one screen, one endpoint at a time).
- **D — Data**: split by data variation (one record type, format, or boundary at
  a time; defer the rest).
- **R — Rules**: split by business rule (implement the core rule first; add the
  secondary rules and exceptions as later slices).

## INVEST — what a good slice looks like

INVEST is the quality bar each slice should clear:

- **I — Independent**: the slice can be built and reviewed without waiting on a
  sibling slice.
- **N — Negotiable**: it captures intent, not a frozen implementation contract.
- **V — Valuable**: it delivers observable end-to-end value on its own, however
  small.
- **E — Estimable**: its size can be reasoned about up front. When it cannot be
  estimated, that is the signal to cut a **Spike** first — the "Estimable" escape
  hatch (see [Spikes](#spikes-are-sized-by-timebox-not-loc)).
- **S — Small**: it fits at or under the ~400 reviewable-LOC ceiling.
- **T — Testable**: there is a clear way to verify it is done and correct.

## Vertical slicing — cut end-to-end, not by layer

A **vertical** slice cuts end-to-end through every layer it touches (data →
logic → interface) and delivers a thin, working capability. A **horizontal**
slice cuts by layer ("all the data models", then "all the services", then "all
the UI") and delivers nothing usable until the last layer lands.

Always prefer vertical slices. A horizontally-sliced spec is a re-slicing
signal: recommend cutting it into vertical slices, each delivering one thin
end-to-end capability, rather than one fat layer at a time.

## The estimate is a forward guess, not the authoritative count

The number `estimate-spec-size.sh` returns is an **approximate forward guess**
made *before* any code exists, from structured size signals (user-story count,
files/surfaces touched, functional-requirement count, new-vs-modify). It is a
right-sizing aid for authoring time.

It is **NOT** the authoritative reviewable-LOC count. The authoritative
measurement of actual reviewable LOC — and the plan-phase budget gate that acts
on it — is owned by **PRSG-006** (`estimate-reviewable-loc.sh`). Do not over-trust
the forward guess or treat it as the final word; it exists to shape decomposition
early, not to score a finished change.

## Spikes are sized by timebox, not LOC

A SPIDR **Spike** is a research-only slice: its job is to answer a question, not
to ship a feature. A spike is therefore a distinct slice *type* that is exempt
from the LOC threshold — it is sized by its timebox (e.g. "one day to prototype
the parser") rather than by lines of code.

When a slice is marked as a spike, the estimator skips the LOC comparison
entirely and returns `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}`.
Here `status: ok` means **"LOC sizing is not applicable to a research slice"**
(the INVEST "Estimable" escape hatch) — it does **not** mean the slice is
trivially small. A spike never trips a misleading `warn`, and no third status
value is ever introduced.

## The at-ceiling boundary rule

Both skills must treat the boundary identically:

- When the estimate is **exactly at** the ceiling (`estimated_loc == ~400`), the
  status is **`ok`**.
- The status is **`warn`** only when the estimate is **strictly over** the
  ceiling (`estimated_loc > ~400`).

`status` is always exactly one of **`ok`** or **`warn`** — never a third value.
A `warn` is informational: surface it as advisory text and continue the
interview. It is never an exit code, a gate, or a hard stop.

## How the estimator turns signals into a guess

The estimate is intentionally a **simple, deterministic, documented** heuristic —
a weighted sum of the structured size signals, with a modest discount when the
work modifies existing code rather than adding net-new code. It makes no attempt
at cleverness; the point is a stable forward guess that the fixtures can pin
byte-for-byte.

The documented weights (kept in sync with the constants in
`estimate-spec-size.sh`) are:

| Signal | Weight (LOC per unit) |
|--------|-----------------------|
| user stories | 25 |
| files / surfaces touched | 40 |
| functional requirements | 15 |

- **new vs modify**: the summed estimate is used as-is for net-new work
  (`new`, the default); for `modify` it is halved (integer division) to reflect
  that modifying existing code is typically a smaller reviewable surface than
  building it from scratch.
- **suggested_slices** (non-spike) = `ceil(estimated_loc / ~400)`, with a minimum
  of `1`.
- **Robustness**: each numeric signal that is missing, zero, negative, or
  non-numeric is normalized to `0` before the sum (not a separate code path); the
  status then follows the at-ceiling rule on the resulting estimate. When every
  signal is bad or absent, the estimate is `0` (at/under the ceiling) → `ok`.

Because there are no clocks, randomness, or result-affecting environment reads,
identical inputs always produce byte-identical output.

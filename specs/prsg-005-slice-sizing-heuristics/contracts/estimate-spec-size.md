# Contract: `estimate-spec-size.sh`

The single shared, runtime-agnostic deterministic estimator. This contract is what the
Layer-4 fixtures pin and what both Claude Code skills and both Codex mirrors rely on.

## Location & invocation

- **Path (single copy)**: `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh`
- **Invoked by all four skill surfaces via**:
  `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh`
- Runtime: `bash` + `jq` only. Begins with `#!/usr/bin/env bash` and `set -euo pipefail`;
  all variables quoted; `chmod +x`; passes `bash -n`. (Constitution II.)

## Inputs

Structured size signals, supplied by the calling skill (the skill gathers them from the
catalog entry it is drafting, or the single spec it is scoping). The exact argument syntax
(flags vs a single JSON blob on stdin) is finalized in Tasks; whichever is chosen, the
accepted signal set is:

| Signal | Meaning | Default if absent |
|--------|---------|-------------------|
| user stories | count of user stories | `0` |
| files/surfaces | count of files/surfaces touched | `0` |
| functional requirements | count of FRs | `0` |
| new-vs-modify | `new` or `modify` | `new` |
| spike | research-only slice flag | `false` |

## Output

Compact JSON on stdout, produced via `jq`:

```json
{"estimated_loc": <int>=0>, "suggested_slices": <int>=1>, "status": "ok|warn"}
```

- `status` is **exactly** `ok` or `warn`. No third value is ever emitted (FR-017).
- The script exits `0` on a successful estimate (including `warn`). `warn` is **informational
  only** and MUST NOT be expressed as a non-zero/blocking exit — advisory-only (FR-011).
- **Caller-side obligation** (FR-011): a calling skill MUST NOT use this script's exit code for
  control flow or treat it as a gate. If the script is unavailable (missing script, missing
  `jq`, a non-zero exit, or empty/unparseable output), the caller MUST treat the result as an
  absent estimate, surface an advisory note, and continue — never a hard stop. The script-side
  `exits 0` guarantee above covers only the case where the script runs; this caller-side rule
  covers the case where it cannot run.

## Behavior rules

1. **Deterministic** (FR-007): identical inputs → byte-identical stdout. No clocks, no
   randomness, no environment reads that affect the result.
2. **At-ceiling boundary** (Edge Cases; Clarify S1): `estimated_loc == ceiling` → `status: ok`.
   `status: warn` only when `estimated_loc > ceiling` (strictly over).
3. **Spike** (FR-017): `spike=true` → skip the LOC-threshold comparison; return
   `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}`.
4. **suggested_slices** (non-spike): `ceil(estimated_loc / ceiling)`, minimum `1`.
5. **Robustness** (FR-016): each non-conforming numeric signal is normalized to `0` before the
   estimate — missing → `0`; negative → `0`; zero → `0`; malformed/non-numeric → `0`. `status`
   then follows the same at-ceiling boundary rule as rule 2 on the resulting `estimated_loc`
   — it is **not** a separate code path. When every signal is bad/absent the estimate is `0`
   (at/under the ceiling) → `status: ok`; a mixed input keeps its valid signals and is sized
   normally. Here `ok` means "there is no over-ceiling estimate to flag", **not** "the input
   was validated as good" (mirrors the spike `ok` rationale in rule 3). Never crash, never
   block, never emit a third status value.
6. **Ceiling constant** (FR-008): a single hardcoded `~400` constant with a "keep in sync with
   the documented ceiling in slicing-heuristics.md" comment.

## Verification (Layer 4)

`tests/layer4-scripts/test-estimate-spec-size.sh` + committed fixtures assert:

- Byte-identical output for repeated identical inputs (determinism).
- `status` correct at `estimated_loc == ceiling` (→ `ok`) and just over (→ `warn`).
- Spike input → `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}`.
- Zero / negative / missing / malformed signals → predictable non-crashing output.
- `status` is never any value other than `ok` or `warn`.

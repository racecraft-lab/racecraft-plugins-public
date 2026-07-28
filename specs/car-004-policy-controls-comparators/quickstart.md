# Quickstart: validating CAR-004

How to prove the feature works end to end. Everything in sections 1 through 4 is
deterministic and runs in CI. Section 5 is the developer-local live smoke, run by
hand, three times, once per control.

Details of what each rule means live in [data-model.md](./data-model.md) and
[contracts/](./contracts/); this file is the run guide.

## Prerequisites

- Python 3.11 or newer on `PATH`. No package installation, no virtualenv, no
  `jq`.
- The `car-004-policy-controls-comparators` worktree, on its own branch. Never
  `main`.
- For section 5 only: an authenticated Claude subscription session. **No API key
  is used, and no supported path may require one.**
- For section 6 only: Node 22.12 or newer for the docs-site reference
  regeneration.

## 1. Baseline before touching anything

```bash
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
```

Both must be green before the first change. A red baseline is an environment
problem, not a CAR-004 finding.

## 2. Structural validation

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

Confirms the repository structure still validates with the two new contract
documents and the new `fixtures-controls/` directory in place.

## 3. Contract and control validation

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

Expected outcomes, each traceable to a success criterion:

| Check | Expected | Criterion |
|---|---|---|
| Registry enumerates exactly three controls; a seeded fourth is refused | refusal raised | SC-001 |
| Altering any hash-relevant field changes the control's content address, once per control | three digests change | SC-002 |
| Each recorded digest recomputes and matches | equal | SC-012 |
| The adaptive signal domain maps totally and single-valuedly | zero unmapped, zero ambiguous | SC-003 |
| `escalation_ladder` carries every admitted tuple exactly once; a seeded duplicate, omission, bad within-model position, and un-rationalized cross-model step are each refused | four refusals | SC-014 |
| All three controls replay deterministically | two runs, identical digest | SC-005 |
| Multi-child orchestration replay: additive dimensions equal the parent-plus-children sum; terminal state is worst-wins; acceptance floors to 0; no null aggregate acceptance | pass | SC-006, SC-015 |
| Reserved-partition guard fails on a seeded violation and passes on the delivered evidence | one refusal, one pass | SC-007 |
| Margin map total over eight dimensions; four eligible at 0.10; zero-comparator yields `margin_not_computable` | pass | SC-016 |
| Every verdict state resolves to exactly one claim class | three lookups, three classes | SC-008 |
| Raw-token smoke bounds sum to exactly 1,000,000; no reference resolves outside `#/$defs/` | pass | SC-017 |
| Twin-handoff categories 1 through 6 re-derive with zero differences in either direction | pass | SC-011 |
| Delivered evidence carries zero outcome-bearing scored rows and consumes zero selection or confirmation objectives | pass | SC-010 |

## 4. Additive-only verification, no execution required

```bash
git diff --name-status origin/main...HEAD -- tests/speckit-pro/layer6-efficiency/contracts-claude/
```

Expect exactly two `A` (added) lines and **zero** `M` lines. Any modification
under `contracts-claude/` or `contracts-codex-specification/` is a FR-005
violation and blocks the change. This is SC-004, and it is verifiable from the
change set alone.

```bash
git diff --name-status origin/main...HEAD -- tests/speckit-pro/layer6-efficiency/lib/
```

Expect two `A` lines and zero `M` lines against the frozen `claude_*.py` modules.

## 5. Bounded live smoke — developer-local, three runs, never CI

One run per control, on the supported subscription authentication path. Run them
**in sequence, each under its own ephemeral cache root**, so no control's smoke
warms another arm's cache (FR-032).

```bash
# 1. Print the bounded plan and read it before running anything
python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \
    --control unpinned --plan

# 2. Execute the printed plan by hand, then seal the produced record
python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \
    --control unpinned --seal <record.json>
```

Repeat for `--control adaptive` and `--control orchestration-changing`.

Each run must stay inside all four declared bounds — at most 5 non-reserved
objectives, 1 repetition, a 1,000,000 raw-token ceiling, and a 30-minute wall
clock — and each must demonstrate its own behavior:

| Control | Must demonstrate |
|---|---|
| `unpinned` | a real inherit resolution against the pinned parent session |
| `adaptive` | a real dispatch-time escalation to the next-higher ladder entry |
| `orchestration-changing` | a real parallel dispatch with child aggregation |

The plan step derives its objectives from the registered CAR-004 smoke partition
and refuses to print any objective the frozen consumption path does not admit, so
a reserved objective never reaches you in the first place.
The seal step refuses a record whose `authentication_mode` is `api_key`, whose
`scored` is not `false`, whose objectives touch the reserved partition, or whose
consumed budget exceeds any frozen bound. A run that reaches a bound stops there
and stays valid non-scored evidence.

**Nothing from this section is committed.** Per-run output is written under
`tests/speckit-pro/layer6-efficiency/results/`, which the existing layer6
`.gitignore` already excludes. Verify with:

```bash
git status --porcelain tests/speckit-pro/layer6-efficiency/results/
```

Expect no output. [FR-033, SC-009]

## 6. Before opening the PR

```bash
pnpm --dir docs-site install          # once per worktree
pnpm --dir docs-site reference:generate
python3 tests/speckit-pro/run-all.py
```

New `.py` files under `tests/speckit-pro/` stale the generated
`docs-site/src/content/docs/reference/tests.md`, and CI's validate-docs job runs
`reference:check` against it. Regenerate and commit that file with the change.

Then confirm, from the artifacts rather than from memory:

- `docs/ai/specs/.process/CAR-004-twin-handoff.md` is committed in this PR, states
  its publication date and the reference by which the G56R-004 owner was
  notified, and lists an explicitly empty reconciliation candidate list.
  [FR-037, FR-037a, SC-013]
- No twin acknowledgment, response, or landing is a merge precondition.
  [FR-037, SC-013]
- The PR title passes the release-readiness gate:
  `<type>(<lowercase-scope>): <plain English description>`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| A totality check fails against a frozen enum after an upstream change | The frozen enums are read live from `score-bundle.schema.json` on purpose. The break is upstream, not in CAR-004; the failure message names the frozen source. |
| A digest mismatch on the unpinned control | The pinned parent-session binding is wrong. The environment contract has no `contracts-claude/` mirror, so confirm the identity the CAR-003 harness actually reads before re-freezing. |
| A digest changes after "only reordering the ladder" | Correct behavior. Array order is inside the preimage; reordering is a new control version, never an edit. [FR-011b] |
| The smoke script refuses to seal | Read the refusal. It is one of: API-key authentication, a scored row, a reserved-partition reference, or a budget breach. All four are fail-closed by design. |

# CAR-003 Slice 3 — PR Review Packet

**Feature**: `specs/car-003-evaluation-runner-scoring/`
**Slice**: 3 of 3 — US4, experiment policy, statistics, and replay
**Proposed PR title**: `feat(speckit-pro): add experiment policy, partitions, and the decision ladder`

> Title validated against the release-readiness gate pattern
> `^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+` — **PASS**.

The nine sections below are the set `spec.md` "PR Review Packet Requirements"
makes mandatory.

---

## 1. What changed

Slice 3 closes the platform: it decides what a scored result *means*, and it does
so under rules frozen before any outcome is visible.

- **`claude_experiment_policy.py`** — the partition registry and the immutable
  experiment bundle. An objective ID appearing in two registered partitions fails
  closed with `failure_plane=partition`. A calibration partition declaring
  `qualification_eligible=true` is schema-rejected. A calibration pair binds the
  calibration protocol; a qualification-eligible pair binds the frozen analysis
  plan; binding both is rejected. An experiment-policy budget unequal to the
  analysis-plan budget on a qualification-eligible partition fails closed. Every
  assigned pair binds a workload stratum before execution from a closed
  pre-execution membership basis with `derived_from_realized_outcomes=false`.
- **`claude_analysis_decision.py`** — the ordered decision ladder. Semantic and
  reliability floors run first, then paired cluster-adjusted non-inferiority, then
  the resource comparison; a stage that is not reached records `not_evaluated`
  rather than being omitted. A tie, mixed dominance, incomplete evidence, or
  statistical uncertainty produces `no_qualification` or `inconclusive` — no
  weighted ranking is ever forced, and no scalar score or price coefficient
  appears anywhere in the bundle. Candidate failures, timeouts, cancellations,
  budget exhaustion, and abandoned work stay in the estimand at acceptance zero.
  Reruns are complete-pair only, capped, and classified from arm-blind evidence
  before either outcome is read. The `qualified` terminal state is unreachable
  from a calibration partition.
- **Guardrails and stopping rules** (same module) — fully declared p95 guardrails
  each carrying unit, denominator, comparator, margin, confidence method,
  missing-data rule, direction, and multiplicity family; per-stratum
  `minimum_unique_tasks` floors that return **inconclusive** below the floor
  rather than passing; three multiplicity families with cluster-adjusted variance
  as a precondition and the guardrail family declared distinct from those three;
  and racing and futility declarations recording every planned interim look with
  its information fraction, boundary, bindingness, complete-pair stop scope, and
  stopped-not-completed reporting.
- **`fixtures/car-003-calibration-replay.json`** — frozen experiment, score,
  analysis, and decision bundles for deterministic replay, bounded in count and
  size so suite cost does not scale per campaign.

## 2. Why

The failure mode this slice exists to prevent is deciding the rules after seeing
the results. Every mechanism here is a pre-commitment: strata bound before
execution, interim looks declared in advance, multiplicity families fixed,
guardrails fully specified down to the missing-data rule.

The ladder is strictly ordered — and records `not_evaluated` for unreached stages
rather than omitting them — because an omitted stage is indistinguishable from a
passed one when someone reads the bundle six months later.

There is deliberately **no scalar score and no price coefficient**. A single
number invites a weighted ranking, and a weighted ranking would let a strong
result on one dimension buy a regression on another. Pareto comparison with an
explicit `inconclusive` terminal state is the honest alternative: when the
evidence does not separate two candidates, the system says so instead of
manufacturing a winner.

## 3. Non-goals

- No live model calls in the default suite. The calibration pilot is T078,
  operator-only, and is **not** in this PR.
- **No frozen numeric analysis plan.** See known gaps — this is the single most
  important non-goal in this packet.
- No final route policy. Slice 3 freezes the decision *platform*; it does not
  decide any route.
- No cohort outcomes. CAR-007 through CAR-010 own those.
- No policy controls or adaptive comparators — CAR-004.
- No changes to shipped plugin source. Zero production files.

## 4. Review order

**Review this PR third and last.** It consumes slice 2's score bundles, which
consume slice 1's treatment records.

Suggested reading order within the PR:

1. `contracts/experiment-policy.schema.json` and
   `contracts/experiment-assignment.schema.json` — the pre-execution binding
   rules.
2. `claude_experiment_policy.py`, then `test-experiment-policy-partitions.py`.
3. `contracts/analysis-plan.schema.json` and
   `contracts/analysis-decision.schema.json`. Note that `analysis-decision` is a
   **parity mirror** of the Codex twin and must stay logically identical; changes
   here are joint cross-platform changes.
4. `claude_analysis_decision.py`, then `test-analysis-decision-ladder.py`. This is
   the largest single file in the feature — read the ladder ordering and the
   inconclusive paths first.
5. `fixtures/car-003-calibration-replay.json` last, as data.

## 5. Scope budget

Counting rule for logic LOC: non-blank lines excluding comments and docstrings.

| Metric | Ratified in `plan.md` | Measured on the branch | Delta |
|---|---|---|---|
| Shipped production files | 0 | **0** | on budget |
| Authored implementation files | 7 | **6** | -1 (analysis plan not frozen) |
| Changed paths | 7 | **8** | +1 |
| Logic LOC | 590 | **1,463** | **2.48x over** |

Measured logic LOC composition: `claude_analysis_decision.py` 914,
`claude_experiment_policy.py` 549.

This is the largest overrun of the three slices. The statistical surface — three
multiplicity families, per-stratum floors, racing and futility boundaries,
complete-pair rerun classification, and the full `not_evaluated` bookkeeping — is
substantially more code than the plan's estimate anticipated. At 8 changed paths
and zero production files the slice remains far under the 25-file threshold, so
the overrun does not change the slice boundary.

### Whole-feature reviewability, measured

Recorded here because Polish owns the cross-cutting figures.

| Metric | Ratified | Measured | Delta |
|---|---|---|---|
| Shipped production files | 1 | **1** | on budget |
| Authored implementation files | 23 | **22** (18 new, 4 modified) | -1 |
| Regenerated artifacts | 12 | **30** | **+18** |
| Total changed paths | ~35 | **78** | **well past the 25-file threshold** |
| Logic LOC | 1,858 | **3,490** | **1.88x over** |

**The estimator undershoots this repository's Python harness consistently** —
1.44x on slice 2, 1.71x on slice 1, 2.48x on slice 3, 1.88x across the feature.
The mechanical tasks-mode estimator's two heuristics (`tasks x 40` reviewable LOC,
and production-file classification by path prefix) do not fit a repository whose
Python lives under `speckit-pro/` and `tests/speckit-pro/` and whose task list is
deliberately fine-grained for TDD, so task count tracks test granularity rather
than review surface.

**No re-slicing is proposed.** FR-025 and the roadmap require Work Package A to
stay intact, and `plan.md` explicitly directs that a larger-than-projected
regenerated set be recorded rather than used as grounds to subdivide. Whether to
grant a threshold exception is an operator ruling, not an implementation decision.

## 6. Traceability

| Requirements | Changed files | Verification evidence |
|---|---|---|
| FR-013 (partition registry, no cross-partition objective reuse) | `claude_experiment_policy.py`, `contracts/experiment-policy.schema.json` | `test-experiment-policy-partitions.py`; quickstart 5 |
| FR-017, FR-018 (Pareto comparison, exact eight-member dimension set) | `claude_analysis_decision.py`, `contracts/analysis-plan.schema.json` | `test-analysis-decision-ladder.py`; quickstart 2, 5 |
| FR-019 (no scalar score, no price coefficient, no forced ranking) | `claude_analysis_decision.py`, `contracts/analysis-decision.schema.json` | `test-analysis-decision-ladder.py`; quickstart 5 |
| FR-020 (estimand retention at acceptance zero) | `claude_analysis_decision.py` | `test-analysis-decision-ladder.py`; quickstart 5 |
| FR-021 (complete-pair capped reruns, arm-blind classification) | `claude_analysis_decision.py` | `test-analysis-decision-ladder.py`; quickstart 5 |
| FR-022 (operator-only live boundary) | `claude_experiment_policy.py` | `test-experiment-policy-partitions.py`; zero live calls in suite |
| FR-023 (post-calibration pre-cohort analysis plan) | *not landed* — see known gaps | blocked on T078 |
| FR-024 (`qualified` unreachable from calibration) | `claude_analysis_decision.py` | `test-analysis-decision-ladder.py`; quickstart 5 |
| FR-037 (calibration protocol versus frozen plan binding) | `claude_experiment_policy.py` | `test-experiment-policy-partitions.py`; quickstart 5 |
| FR-038 (budget equality on qualification-eligible partitions) | `claude_experiment_policy.py` | `test-experiment-policy-partitions.py`; quickstart 5 |
| FR-049 (reasoning-token report, Pareto exclusion) | `claude_analysis_decision.py` | `test-analysis-decision-ladder.py` |
| FR-050, FR-053, FR-054, FR-055 (p95 guardrails, per-stratum floors, multiplicity families, racing and futility) | `claude_analysis_decision.py` | `test-analysis-decision-ladder.py` |
| FR-052 (cache-state isolation in the resource comparison) | `claude_experiment_policy.py`, `claude_analysis_decision.py` | `test-experiment-policy-partitions.py` |
| FR-056 (inconclusive terminal state) | `claude_analysis_decision.py` | `test-analysis-decision-ladder.py` |
| FR-057 (suite budget, bounded fixtures, quantified replay bound) | `fixtures/car-003-calibration-replay.json` | measured in section 7 |
| FR-058 (workload strata bound pre-execution) | `claude_experiment_policy.py` | `test-experiment-policy-partitions.py` |

Success criteria covered here: SC-007, SC-008, SC-009, SC-010, SC-011, SC-019,
SC-022, SC-023, SC-025. **SC-012 is not yet satisfied** — see known gaps.

## 7. Verification evidence

- **Full default suite**: `python3 tests/speckit-pro/run-all.py` →
  **4100/4100 passed** (L1 1428, L4 2486, L5 186), wall clock **4m40s** against a
  declared 6-minute budget — within budget with roughly 22% headroom.
- **Deterministic replay, quantified**: ten consecutive runs of
  `test-analysis-decision-ladder.py` on a clean checkout measured
  0.23–0.27 seconds wall clock; **p95 = 0.27s** against the declared 10-second
  bound, a margin of roughly 37x.
- **Replay fixtures are bounded**: exactly **3** CAR-003 fixture files totalling
  **84 KB** (`car-003-alias-repoint-replay.json` 12.8 KB,
  `car-003-calibration-replay.json` 48.7 KB, `car-003-role-corpus.json`
  17.1 KB). The count is fixed by contract, not per campaign, so suite cost does
  not grow as campaigns accumulate.
- **Zero live calls** in the default suite, confirmed by the suite's own live-call
  accounting.
- **Privacy**: targeted CAR-003 scan of 42 artifact files returns zero hits;
  tree-wide `test-privacy-scan.py` 10/10.

## 8. Known gaps

1. **T078 — the calibration pilot has not been run. Operator-only, by design.**
   It runs only disposable `qualification_eligible=false` calibration objectives
   under an explicit, local, pinned, budgeted invocation with all eight ceilings
   set. It is the only source of the variance estimates the analysis plan needs.
2. **T079 — the numeric analysis plan is NOT frozen, and must not be.**
   `docs/ai/research/claude-car-003-analysis-plan.json` does not exist. It is
   blocked on T078 and deliberately left undone: freezing invented variance
   estimates would violate the calibration-evidence-only rule and would bind the
   CAR-007 through CAR-010 cohort specs to an uncalibrated digest. **SC-012 is
   therefore open.** The correct sequence is pilot first, then freeze, then any
   cohort outcome — and the plan must be frozen before the first outcome-bearing
   cohort exists. Until it is, no qualification-eligible campaign can run, which
   is the intended fail-closed state.
3. **The FR-014 versus FR-034 failure-plane contradiction is still outstanding**
   and is recorded in full in the slice 2 packet. It needs an operator ruling and
   a matching change on both platforms; the implementation keeps both
   requirements visible rather than silently choosing.
4. **Slice 3 logic LOC is 2.48x the ratified estimate** — see section 5. Recorded,
   not resolved.

## 9. Rollback and feature-flag notes

- **No feature flag.** All artifacts are additive and versioned.
- **Rollback is a plain revert** and touches no shipped plugin surface — zero
  production files, so no payload refresh and no installed-cache proof change.
- **Revert this slice first** if the whole feature is being withdrawn. Nothing
  depends on slice 3 at merge time; CAR-007 through CAR-010 do not exist yet.
- **Reverting is safe precisely because nothing is frozen yet.** No analysis plan
  is published and no cohort has drawn from it, so a revert cannot orphan a
  frozen numeric commitment or invalidate an outcome that already referenced one.
  This property disappears the moment T079 lands — after that, a revert would
  need to account for any cohort bound to the frozen plan digest.
- **The parity mirror is the one cross-platform caveat.**
  `contracts/analysis-decision.schema.json` must stay logically identical to the
  Codex twin's; a unilateral revert on this side would break that parity and
  should be coordinated with the corresponding G56R-003 change.

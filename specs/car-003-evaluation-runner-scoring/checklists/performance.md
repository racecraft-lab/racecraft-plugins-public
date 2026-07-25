# Performance Checklist: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Purpose**: Unit tests for the *English* of CAR-003's performance requirements — campaign budgets, the p95 guardrail registry, workload strata, cache-state isolation, racing/futility stopping, and the cost of the deterministic replay suite. Every item asks whether the requirement is written completely, unambiguously, consistently, and measurably. None of them asks whether an implementation works.

**Created**: 2026-07-24

**Feature**: `specs/car-003-evaluation-runner-scoring/spec.md`

**Depth**: Formal release gate. **Audience**: Reviewer (PR). **Timing**: Post-plan, pre-tasks.

**Primary risk lens**: any budget or guardrail threshold that could be *set or relaxed after outcomes are observed*. A threshold chosen once outcomes are visible silently redefines the estimand, exactly as FR-038 already argues for the campaign budget.

**Status**: 49 items assessed, 30 `[Gap]` findings raised and remediated in this pass. 2 residual items (CHK050, CHK051) remain open because they require a joint cross-platform change and cannot be made unilaterally.

## Campaign Budget Requirements

- [x] CHK001 - Are all eight campaign-budget ceilings (attempts, wall-clock, raw input tokens, cache-write by TTL class, cache-read, output tokens, candidate count, confirmation entries) enumerated in the requirements rather than left to the schema? [Completeness, Spec §FR-022]
- [x] CHK002 - Is it unambiguous which of the two budgets is decision-bearing when the analysis-plan budget and the experiment-policy budget disagree? [Clarity, Spec §FR-038]
- [x] CHK003 - Is the point in time at which budget equality is checked specified, rather than only the equality itself? [Clarity, Spec §FR-038]
- [x] CHK004 - Is the TTL-class key space closed and identical across the ceiling and its measurement, so a ceiling cannot be keyed differently from what it bounds? [Consistency, Spec §FR-022]
- [x] CHK005 - Are requirements defined for what happens when a *campaign-level* ceiling is exhausted between the two arms of a pair, leaving a structurally incomplete pair? [Resolved → Spec §FR-056]
- [x] CHK006 - Is the requirement clear that a campaign-ceiling stop is an administrative truncation and therefore must not be recorded as the candidate-caused budget exhaustion FR-020 assigns acceptance zero? [Resolved → Spec §FR-056]
- [x] CHK007 - Are requirements defined governing a post-freeze amendment to any budget ceiling — whether relaxation is permitted at all, and what it invalidates? [Resolved → Spec §FR-056]
- [x] CHK008 - Is budget-freeze timing tied to observable evidence rather than asserted, so "frozen before outcomes" is falsifiable? [Measurability, Spec §FR-023, SC-012]

## Guardrail Registry — Definitional Completeness

- [x] CHK009 - Are the p95 resource and p95 duration guardrails defined with an explicit **unit** for each guarded quantity? [Completeness, Spec §FR-049, FR-053]
- [x] CHK010 - Is the **denominator** of each p95 specified — the population the percentile is taken over (attempts, pairs, tasks, per arm, per stratum, pooled)? [Resolved → Spec §FR-053, `guardrail_method.denominator`]
- [x] CHK011 - Is the **comparator** specified — whether a guardrail is an absolute ceiling or a relative bound against the paired comparator arm? [Resolved → Spec §FR-053, `guardrail_method.comparator`]
- [x] CHK012 - Is a **margin** defined for each guardrail, distinct from the non-inferiority margins of the semantic and reliability endpoints? [Resolved → Spec §FR-053, `guardrail_method.margin`]
- [x] CHK013 - Is the **confidence method** specified — whether the guardrail compares a point estimate or an upper confidence bound of the percentile? [Resolved → Spec §FR-053, FR-054, `guardrail_method.confidence_method`]
- [x] CHK014 - Is a **missing-data rule** defined for attempts that produce no duration or token observation because they failed, timed out, or were cancelled? [Resolved → Spec §FR-053, `guardrail_method.missing_data_rule`]
- [x] CHK015 - Is the guardrail's **multiplicity position** declared, given that FR-050 enumerates exactly three families and guardrails are named in none of them? [Resolved → Spec §FR-053, `guardrail_method.multiplicity_family`]
- [x] CHK016 - Is a **minimum unique-task count** stated *per stratum*, rather than only once for the whole manifest, so a guardrail cannot be evaluated on a stratum too small to support it? [Resolved → Spec §FR-054, `stratum_minimum_unique_tasks`]
- [x] CHK017 - Are guardrail **directions** declared (which way is worse) for every guarded quantity, so "breach" is objectively decidable? [Resolved → Spec §FR-053, `guardrail_method.direction`]
- [x] CHK018 - Is the consequence of a guardrail breach specified — whether it blocks qualification, returns inconclusive, or is diagnostic only? [Resolved → Spec §FR-053, `guardrail_method.breach_result`]

## Guardrail Estimability

- [x] CHK019 - Do the requirements acknowledge that a 95th percentile estimated from a small sample is unstable, and state the sample condition under which a guardrail comparison is admissible at all? [Resolved → Spec §FR-054]
- [x] CHK020 - Is the behaviour specified when a stratum's observed sample is below the estimability floor — inconclusive, guardrail skipped, or stratum excluded? [Resolved → Spec §FR-054, returns inconclusive]
- [x] CHK021 - Can each guardrail threshold be objectively re-derived at replay from the frozen plan plus the bound traces, with no operator judgement? [Measurability, Spec §SC-011, SC-023]

## Workload Strata and Long-Horizon Membership

- [x] CHK022 - Is the rule by which a task is assigned to a workload stratum written down, or is stratum membership left entirely to the implementation? [Resolved → Spec §FR-052, `strata[].membership_rule`]
- [x] CHK023 - Is it explicitly required that long-horizon membership derives from **task and protocol characteristics known before either arm runs**? [Resolved → Spec §FR-052, closed `permitted_basis`]
- [x] CHK024 - Is it explicitly prohibited to derive stratum membership from **realized** duration, turns, tokens, retries, or compactions? [Resolved → Spec §FR-052, `derived_from_realized_outcomes` pinned false]
- [x] CHK025 - Is the long-horizon stratum required to be **powered** — carrying its own sample size rather than inheriting the pooled one? [Resolved → Spec §FR-052, `stratum_sample_size`]
- [x] CHK026 - Is stratum membership required to be bound in the pre-execution assignment record, so "membership was fixed before the run" is provable rather than asserted? [Resolved → Spec §FR-052, `stratum_assignment` in the assignment contract, SC-022]
- [x] CHK027 - Is the handling of a task matching no registered stratum specified? [Coverage, Spec §FR-038, `unknown_stratum_policy` = inconclusive]

## Reliability Guardrails — Late Failure, Retry, Compaction

- [x] CHK028 - Are retry and compaction **guardrails** defined, distinct from their role as Pareto dimensions, given that pairwise dominance imposes no absolute bound? [Resolved → Spec §FR-053, `reliability_guardrails`]
- [x] CHK029 - Is "late failure" defined as a term, and is a late-failure guardrail specified alongside the resource and duration guardrails? [Resolved → Spec §FR-053, `late_failure_definition`]
- [x] CHK030 - Are the reliability guardrails consistent with the existing closed failure taxonomy rather than introducing a parallel vocabulary? [Consistency, Spec §FR-034 — reuses existing planes, coins no failure code]

## Cache-State Isolation

- [x] CHK031 - Are requirements defined that cache state is isolated between arms so one arm cannot warm another's? [Completeness, Spec §FR-049, US2 AS-5]
- [x] CHK032 - Is **observed** isolation evidence required per arm, and does any contract provide a representable place to record it? [Resolved → `observed_cache_isolation` in the CAR-003 additive records, SC-024]
- [x] CHK033 - Is the consequence specified for a pair whose arms cannot be shown to have used distinct cache roots? [Resolved → Spec §FR-049; `observed_shared` and `unobserved` contribute zero resource comparisons]
- [x] CHK034 - Do the requirements state why isolation is load-bearing rather than hygienic — that `cached_input_tokens` is decision-bearing, so a cache artifact enters the dominance result directly? [Clarity, Spec §FR-018, FR-049]
- [x] CHK035 - Are order and carryover effects addressed, given that billed cache writes make a crossover ordering directly distortive? [Coverage, Spec §FR-049, `order_leakage_prohibited`]

## Racing, Futility, and Interim Stopping

- [x] CHK036 - Is the content of the racing declaration specified, or is "racing rules" named without saying what a racing rule must contain? [Resolved → Spec §FR-055, `racing_policy`]
- [x] CHK037 - Is the content of the futility declaration specified, including whether a futility boundary is binding or non-binding? [Resolved → Spec §FR-055, `futility_policy.boundary_binding`]
- [x] CHK038 - Do the requirements address the error inflation that repeated interim looks introduce, and is that stated to be distinct from the three multiplicity families of FR-050? [Resolved → Spec §FR-055, declared a fourth error-control concern]
- [x] CHK039 - Is it required that the number and timing of interim looks be prespecified with the plan, so a look cannot be added after outcomes are visible? [Resolved → Spec §FR-055, `look_schedule_frozen`, SC-025]
- [x] CHK040 - Do the requirements record that stopping early biases the effect estimate, so a raced or futility-stopped comparison is not reported as though it were a completed one? [Resolved → Spec §FR-055, `early_stop_biases_estimate`]
- [x] CHK041 - Are racing and futility rules consistent with FR-021's rule that classification must precede reading either arm's outcome? [Consistency, Spec §FR-021, `stop_scope` = complete_pair]

## Deterministic Replay Suite Cost

- [x] CHK042 - Is the requirement that the default suite makes zero live model calls stated unambiguously and traceable to a measurable criterion? [Measurability, Spec §FR-022, SC-019]
- [x] CHK043 - Is any **runtime** bound stated for the default deterministic suite, so "fast enough to run in default CI" is a requirement rather than an aspiration? [Resolved → Spec §FR-057, SC-019; budget declared in the plan's Technical Context]
- [x] CHK044 - Do the plan's stated performance goals conflict with the spec's dependence on the suite remaining runnable in default CI? [Resolved → Plan §Technical Context rewritten; the prior "Performance Goals: None" contradicted SC-011 and SC-019 and also dropped a bound the twin declares]
- [x] CHK045 - Are the replay fixtures required to be bounded in size or count, so the suite's cost cannot grow without limit as cohorts accumulate? [Resolved → Spec §FR-057]

## Outcome-Dependence and Post-Hoc Relaxation

- [x] CHK046 - Is every performance threshold in this feature traceable to an artifact that freezes before outcomes are observed, with no threshold left to run time? [Traceability, Spec §FR-038, FR-052, FR-054, FR-055, FR-056]
- [x] CHK047 - Are the requirements explicit that an exclusion applied on performance grounds is an eligibility gate evaluated before any outcome is read, never a post-hoc filter? [Consistency, Spec §FR-051]
- [x] CHK048 - Is the count of comparisons excluded on performance-eligibility grounds required to be reported alongside qualification claims? [Coverage, Spec §FR-051, FR-054]
- [x] CHK049 - Are the assumptions that numeric performance values are deliberately deferred to the frozen plan documented and validated, rather than read as missing requirements? [Assumption, Spec §Assumptions]

## Open — Requires Joint Cross-Platform Change

- [ ] CHK050 - Is the **direction of preference** declared for each of the eight Pareto dimensions, given that `acceptance` is better when higher, the token and duration dimensions are better when lower, and `terminal_state` is categorical rather than ordered? Without a declared ordering, "no worse on every dimension" is not objectively decidable. [Gap, Measurability, Spec §FR-018] — **Not remediated unilaterally**: `pareto_policy` is the frozen parity surface FR-018 and FR-049 require to stay identical across platforms, so a direction map must be added to both in the same change.
- [ ] CHK051 - Does the closed `invalidation_reason` set carry a member for an analysis-plan or budget change, so a post-freeze threshold amendment can be recorded as an additive invalidation rather than only detected through binding identity? [Gap, Completeness, Spec §FR-041] — **Not remediated unilaterally**: `invalidation_reason` lives in the parity-mirror score-bundle contract under `additionalProperties: false`, so a unilateral member would validate on one platform and fail on the other. FR-056 currently enforces non-pooling through `{id, digest}` binding identity instead, which works but leaves the invalidation unnamed.

## Remediation Record

Requirements added this pass: **FR-052** (stratum membership derived pre-execution, powered long-horizon stratum), **FR-053** (guardrail definitional completeness and the guardrail multiplicity family), **FR-054** (per-stratum estimability floor), **FR-055** (racing and futility declaration content, interim-look error control), **FR-056** (campaign-ceiling truncation vs candidate budget exhaustion; no post-freeze relaxation), **FR-057** (default-suite and replay cost bounds). Success criteria added: **SC-022** through **SC-025**; **SC-019** extended with the runtime bound.

Contracts changed (CAR-owned only): `contracts/analysis-plan.schema.json` (`guardrail_method`, per-stratum `membership_rule` / `stratum_minimum_unique_tasks` / `stratum_sample_size`, `reliability_guardrails`, structured `racing_policy` and `futility_policy`); `contracts/experiment-assignment.schema.json` (`stratum_assignment`); `contracts/car-003-additive-records.schema.json` (`observed_cache_isolation`). The parity-mirror contracts `score-bundle.schema.json` and `analysis-decision.schema.json` were **not** modified, and `pareto_policy.dimensions` remains exactly the eight of FR-018.

## Notes

- Check items off as completed: `[x]`
- `[Gap]` marks a requirement that is missing or undecidable as written, not an implementation defect.
- Numeric *values* (thresholds, margins, sample sizes) are deliberately analysis-plan data, not spec literals. These items test whether the requirements say what the plan must **contain**, not what the numbers must be.

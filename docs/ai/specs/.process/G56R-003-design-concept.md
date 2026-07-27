---
topic: "Evaluation Runner, Fixtures, Scoring, and Statistical Analysis"
slug: "g56r-003-evaluation-runner-scoring"
date: "2026-07-24"
mode: "setup"
spec_id: "G56R-003"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
question_count: 15
stop_reason: "natural"
---

# Design Concept: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

> **Source:** `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-24
> **Questions asked:** 15
> **Stop reason:** natural

## Goals

- Preserve the archived G56R-002 zero-eligible freeze while adding an
  authoritative, non-empty successor capability freeze from the pinned live
  Codex catalog before any qualification-capable execution (Q1, Q11).
- Keep the existing bare `codex exec` benchmark as explicitly non-release smoke
  evidence and add a separate canonical exact-treatment runner (Q2).
- Implement one shipped Python 3.11 standard-library materializer that the
  Layer 6 harness consumes now and G56R-006 reuses directly (Q5).
- Keep the G56R-002 trace contract and historical evidence immutable. Publish
  versioned G56R-003 experiment/score/decision bundles keyed by new G56R-003
  `execution_trace_id` records that conform to that contract (Q3).
- Govern one twelve-role corpus: eleven required core role contracts plus
  `autopilot-fast-helper`. Execute only admitted routes and keep the helper
  outside the required-core primary statistic (Q6).
- Hard-gate deterministic role, safety, grounding, mutation, tool, output, and
  acceptance contracts before two-ballot blinded semantic adjudication (Q4,
  Q12).
- Apply quality and reliability floors plus paired non-inferiority before a
  Pareto comparison of raw resource vectors; preserve ties as inconclusive
  rather than inventing post-hoc weights (Q7).
- Keep live campaigns explicit, local, budgeted, and pinned. CI runs
  deterministic replay, contract, scorer, and statistical tests only (Q8).
- Permit only capped complete-pair reruns for preclassified independent
  transient harness failures; candidate-caused failures remain outcomes (Q9).
- Make G56R-003 qualification-capable without emitting final per-agent route
  policies: G56R-007 through G56R-010 own outcome-bearing cohort campaigns
  (Q10).
- Prove the end-to-end platform with a live calibration-only partition whose
  results can never support a route-qualification claim, then freeze one
  versioned analysis plan before cohort outcomes exist (Q14, Q15).
- Deliver one G56R-003 spec as three ordered review slices: capability,
  materialization, and trace; corpus and blinded scoring; experiment policy,
  statistics, and the calibration-only pilot (Q13).

## Non-goals

- Mutating or reinterpreting the archived G56R-002 freeze or treatment records
  (Q1, Q3).
- Final preferred/fallback route policies, installed defaults, resolver or
  installer behavior, aggregate identities, or release confirmation (Q10).
- Consuming screening, selection, cohort-lock, or untouched integrated-
  confirmation objectives during the G56R-003 calibration pilot (Q14).
- Treating the current lexical heading/word-overlap scorer as qualification
  evidence (Q2, Q4).
- Replacing or deleting the legacy smoke runner (Q2).
- Running nondeterministic or chargeable live model campaigns in default CI
  (Q8).
- Retrying one candidate arm independently or discarding candidate-caused
  failures from the estimand (Q9).
- Treating Ultra or any topology-changing mode as an ordinary per-agent effort;
  those remain policy-level controls for G56R-004.
- Committing raw live model, app-server, CLI, picker, prompt, or response bytes.
  Raw captures inherit the operator-only content-addressed retention contract
  from G56R-002.
- Adding active Bash or `jq` dependencies, external evaluation frameworks,
  cross-vendor abstractions, or a second materializer implementation.

## Design Tree (Q&A log)

### Q1. How should the G56R-003 scaffold handle the now-confirmed candidate-admission gap?

**Branch:** Dependency integrity and candidate admission

**Recommended answer:** Add successor freeze (Recommended)
> Preserve G56R-002 as immutable historical evidence, use the pinned runtime's
> documented catalog inspection path, and require a non-empty successor freeze
> before qualification-capable execution. The live Codex 0.145.0 catalog proved
> that the account has executable model/effort pairs, so the empty G56R-002
> freeze reflects an evidence-collection gap rather than an empty account.

**Alternatives offered:**
- Harness only: Build runner, corpus, scoring, and analysis but leave every route blocked until another spec admits candidates.
- Pause scaffold: Stop and revise the roadmap and dependency state before authoring G56R-003 artifacts.

**User's answer:** Add successor freeze (Recommended)

**Notes:** The user first asked whether candidates should have existed and what
was actually available. A live `codex debug models` check found seven visible
models with explicit supported reasoning efforts.

---

### Q2. What should G56R-003 do with the existing tool-less smoke benchmark?

**Branch:** Runner boundary and legacy compatibility

**Recommended answer:** Add canonical runner (Recommended)
> The current benchmark intentionally omits the exact tools, skills, MCP
> servers, and parent delivery needed for qualification. Keeping it as smoke
> evidence preserves a useful low-cost signal without confusing it with the
> separately named exact-treatment path.

**Alternatives offered:**
- Replace smoke runner: Convert the existing benchmark in place into the qualification runner.
- Retire smoke runner: Remove the old benchmark and make the new qualification runner the only supported path.

**User's answer:** Add canonical runner (Recommended)

---

### Q3. How should qualification scores and decisions relate to the immutable G56R-002 treatment contract and new G56R-003 traces?

**Branch:** Evidence schema and historical integrity

**Recommended answer:** Add score bundle (Recommended)
> The G56R-002 schema deliberately owns treatment proof and requires
> `acceptance: null`. G56R-003 creates new immutable `execution_trace_id`
> records under that schema, and its versioned score bundle references those
> records without changing archived evidence or combining delivery proof with
> outcome judgment.

**Alternatives offered:**
- Extend trace schema: Version the treatment schema so later trace records carry qualification scores directly.
- Annotate records: Add result fields to copied treatment records with provenance controls.

**User's answer:** Add score bundle (Recommended)

---

### Q4. What scoring authority should the scaffold freeze for outcome-bearing evaluation?

**Branch:** Quality measurement and scorer governance

**Recommended answer:** Hybrid blinded scoring (Recommended)
> Deterministic role, safety, grounding, mutation, tool, output, and acceptance
> checks should remain hard gates. A frozen semantic rubric then measures
> quality under candidate-blind adjudication and explicit disagreement
> handling, avoiding the current lexical scorer's heading and word-overlap
> limitation.

**Alternatives offered:**
- Deterministic only: Qualify only on executable checks and omit nuanced role-quality measurement.
- Single semantic judge: Use one frozen blinded judge, reducing cost while increasing judge-bias risk.

**User's answer:** Hybrid blinded scoring (Recommended)

---

### Q5. Where should the canonical agent materializer live?

**Branch:** Source ownership and shared production seam

**Recommended answer:** Shipped runner module (Recommended)
> The evaluation and installation paths must consume the same component, not
> copied implementations. A pure Python standard-library module in
> `speckit_pro_runner` provides one source of truth, while Layer 6 keeps only
> thin adapters and G56R-006 reuses the shipped module directly.

**Alternatives offered:**
- Harness library first: Implement under Layer 6 and relocate it during G56R-006.
- Contract only now: Define fixtures and equivalence tests now but defer the materializer implementation to G56R-006.

**User's answer:** Shipped runner module (Recommended)

---

### Q6. Which governed corpus should G56R-003 define?

**Branch:** Corpus scope and role parity

**Recommended answer:** Twelve contracts (Recommended)
> Corpus completeness should be independent of current route executability.
> Authoring one twelve-role corpus now—eleven required core roles plus
> `autopilot-fast-helper`—lets later cohort specs consume one governed corpus,
> while only admitted executable routes run and the helper stays outside the
> required-core statistic.

**Alternatives offered:**
- Executable roles only: Limit this spec to agents with current Codex TOMLs and add missing-role fixtures later.
- Helper in core: Include the optional helper in the required-core primary statistic and defer the two required roles without Codex TOMLs.

**User's answer:** Twelve contracts (Recommended)

---

### Q7. How should G56R-003 distinguish qualified preferred and fallback candidates after hard quality gates pass?

**Branch:** Qualification and resource selection

**Recommended answer:** Quality-first Pareto (Recommended)
> Absolute semantic and reliability floors plus task-paired
> non-inferiority protect quality first. Comparing the complete raw resource
> vector only among passing routes preserves interpretability and permits an
> honest inconclusive result when no route dominates.

**Alternatives offered:**
- Frozen weighted score: Predeclare one scalar combining quality, tokens, duration, retries, and compactions.
- Quality only: Qualify on quality and reliability while deferring resource ordering.

**User's answer:** Quality-first Pareto (Recommended)

---

### Q8. Where should outcome-bearing live evaluation campaigns run?

**Branch:** Execution environment and CI boundary

**Recommended answer:** Explicit local campaigns (Recommended)
> Live model runs are networked, chargeable, and nondeterministic. An explicit
> budgeted developer command can preserve pinned environment evidence, while CI
> remains stable by replaying governed traces and testing contracts, scoring,
> and statistical decisions deterministically.

**Alternatives offered:**
- Small CI campaign: Run a capped live screening subset in CI and reserve larger campaigns for developers.
- No CI coverage: Keep both live campaigns and replay verification outside CI.

**User's answer:** Explicit local campaigns (Recommended)

---

### Q9. When a campaign attempt fails, what rerun policy should the experiment contract allow?

**Branch:** Retry, attrition, and estimand integrity

**Recommended answer:** Capped paired rerun (Recommended)
> Candidate-caused failures, timeouts, cancellations, and budget exhaustion are
> outcomes. Only an independently preclassified transient harness failure may
> trigger a frozen, capped rerun of the complete pair, preventing differential
> attrition and arm-specific discretion.

**Alternatives offered:**
- Per-arm retries: Retry only the failed route up to a shared limit.
- Never rerun: Treat every failure as final, including independent infrastructure failures.

**User's answer:** Capped paired rerun (Recommended)

---

### Q10. Which specs should own the outcome-bearing per-agent qualification campaigns?

**Branch:** Roadmap stage ownership

**Recommended answer:** Cohort specs own them (Recommended)
> G56R-003 should build and validate the reusable qualification platform,
> corpus, and frozen analysis contract. G56R-007 through G56R-010 already own
> the per-agent A1/A2/A3, Stage B, and Stage C campaigns and final route
> policies; running them fully in G56R-003 would duplicate cost and consume
> evidence partitions prematurely.

**Alternatives offered:**
- G56R-003 owns them: Run complete qualification here and make later cohort specs package existing evidence.
- Split the stages: Run A1/A2 here and leave A3/B/C to the cohort specs.

**User's answer:** Cohort specs own them (Recommended)

---

### Q11. How should later cohort campaigns consume the G56R-003 successor capability freeze?

**Branch:** Capability freshness and invalidation

**Recommended answer:** Versioned refresh on triggers (Recommended)
> G56R-003 should ship the authoritative collector and initial immutable
> snapshot. A client, account, catalog, or official-source-ledger change then
> creates a new immutable snapshot before a campaign, balancing auditability
> with current availability.

**Alternatives offered:**
- One series-wide freeze: Reuse the initial G56R-003 snapshot for every later cohort.
- Refresh every campaign: Collect a new snapshot for every campaign regardless of observed changes.

**User's answer:** Versioned refresh on triggers (Recommended)

---

### Q12. What semantic adjudication protocol should the scorer contract require?

**Branch:** Blinding, calibration, and disagreement handling

**Recommended answer:** Two blinded ballots (Recommended)
> Two independent candidate-blind rubric ballots reduce single-judge bias. A
> third frozen blinded adjudicator resolves disagreement, and retaining all
> ballots keeps the result replayable and auditable.

**Alternatives offered:**
- Single fixed judge: Use one frozen calibrated evaluator for every result.
- Human panel only: Require human semantic review for every outcome.

**User's answer:** Two blinded ballots (Recommended)

---

### Q13. How should G56R-003 be divided for review and implementation?

**Branch:** Reviewability and vertical slicing

**Recommended answer:** Three ordered slices (Recommended)
> The shared estimator returned `estimated_loc: 1120`,
> `suggested_slices: 3`, and `status: warn` from four capabilities, at least 21
> files, and twelve requirement groups. Three ordered capabilities keep each
> review narrower while preserving roadmap Package A as slice 1 and dividing
> Package B across slices 2 and 3.

**Alternatives offered:**
- Two roadmap packages: Runner and trace first, followed by one larger fixture, scoring, statistics, and pilot slice.
- One combined slice: Implement the entire spec in one PR despite the estimator warning.

**User's answer:** Three ordered slices (Recommended)

**Notes:** The estimate is an advisory pre-implementation guess and likely
overstates fixture-heavy work. The plan-phase reviewability gate remains
authoritative.

---

### Q14. What evidence boundary should the G56R-003 live pilot use?

**Branch:** Pilot validity and evidence partitioning

**Recommended answer:** Calibration-only partition (Recommended)
> Dedicated disposable calibration objectives can prove exact treatment,
> scoring, and statistical plumbing without consuming screening, selection,
> cohort-lock, or untouched integrated-confirmation data. Every pilot record
> must state that it is ineligible for qualification.

**Alternatives offered:**
- Screening partition: Let the pilot produce reusable A1 screening evidence.
- Replay only: Run no live pilot and validate the platform entirely with synthetic or replayed records.

**User's answer:** Calibration-only partition (Recommended)

---

### Q15. When should numeric qualification margins, sample sizes, and multiplicity rules become immutable?

**Branch:** Analysis-plan governance

**Recommended answer:** Freeze after calibration (Recommended)
> Calibration-only and historical non-release evidence may estimate variance
> and feasibility without observing cohort outcomes. One versioned analysis
> plan must then freeze margins, sample sizes, power, multiplicity, racing,
> attrition, and terminal rules before any outcome-bearing cohort run.

**Alternatives offered:**
- Freeze per cohort: Let each cohort choose thresholds before its own outcomes.
- Set them now: Hardcode conservative values without calibration estimates.

**User's answer:** Freeze after calibration (Recommended)

## Grounded Context

- The canonical G56R-002 evidence report records zero eligible tuples and 23
  explicit exclusions:
  `docs/ai/research/codex-g56r-002-capability-evidence.md`.
- The pinned local runtime is Codex CLI `0.145.0`. Its documented
  `codex debug models` catalog reported seven visible models:
  `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, `gpt-5.4`,
  `gpt-5.4-mini`, and `gpt-5.3-codex-spark`, each with explicit supported
  reasoning efforts. This is account- and runtime-bound evidence, not a
  universal platform claim.
- Current official Codex documentation identifies `codex debug models` as the
  local raw-catalog inspection command and the interactive model picker as the
  account-visible selection surface.
- The existing smoke runner is
  `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`; its
  fixture README explicitly says the subprocess lacks the full tool/MCP
  treatment required for qualification.
- The current lexical smoke scorer is
  `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py`.
- G56R-002 treatment records are governed by
  `tests/speckit-pro/layer6-efficiency/contracts/treatment-record.schema.json`
  and `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_model.py`.
  Their G56R-002-owned acceptance field remains null.
- Raw captures inherit the operator-only, content-addressed, fail-closed
  retention contract described in
  `docs/ai/research/codex-g56r-002-capability-evidence.md`.
- The roadmap's reference to
  `tests/speckit-pro/layer6-efficiency/run_codex_role_eval.py` is stale; that
  file is absent. Planning must bind the legacy smoke boundary to the live
  `run-efficiency-benchmarks.py` path.
- The constitution requires Python 3.11+ standard-library implementation,
  deterministic replay, test-first delivery, and no active Bash or `jq`
  dependency.

Capability path: official Codex manual and documented `codex debug models`
command -> pinned Codex CLI 0.145.0 live catalog -> G56R-001 candidate ledger,
G56R-002 immutable evidence contracts, and the G56R-003 roadmap. Confidence is
high for the pinned runtime's visible model/effort catalog and repository
contracts; no claim is made about other accounts or later catalog revisions.

## Open Questions

- **What:** What exact numeric semantic floors, practical margins, sample sizes,
  alpha, power, multiplicity adjustment, racing rule, and attrition cap should
  the first outcome-bearing analysis plan use?
  **Why deferred:** Q15 deliberately reserves these values until the
  calibration-only pilot and historical non-release evidence are available.
  **Suggested next step:** Calculate and independently review the values during
  G56R-003 slice 3, then freeze the versioned plan before G56R-007 begins.
- **What:** Which calibrated adjudicator identities and rubric calibration set
  should supply the two primary ballots and disagreement ballot?
  **Why deferred:** Q12 freezes the protocol, but evaluator identities and
  calibration evidence depend on the implementation-time capability snapshot.
  **Suggested next step:** Bind identities, versions, calibration results, and
  invalidation triggers in the scorer registry before the calibration pilot.

## Recommended Next Step

Complete the G56R-003 scaffold from this design concept, then start
`$speckit-autopilot` in the dedicated G56R-003 worktree with the generated
workflow. The Specify and Plan phases must reconcile the roadmap's stale runner
path and the clarified boundary that G56R-007 through G56R-010 own final
outcome-bearing route campaigns.

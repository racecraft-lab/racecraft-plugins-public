---
topic: "CAR-003 evaluation runner, fixtures, scoring, and statistical analysis"
slug: "car-003-evaluation-runner-scoring"
date: "2026-07-24"
mode: "setup"
spec_id: "CAR-003"
source_input:
  type: "topic"
  ref: "CAR-003 scope section, docs/ai/specs/claude-agent-routing-technical-roadmap.md"
question_count: 14
stop_reason: "natural"
---

# Design Concept: CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

> **Source:** CAR-003 scope from `docs/ai/specs/claude-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-24
> **Questions asked:** 14
> **Stop reason:** natural (every queued branch walked; no new critical branches surfaced)

## Goals

- Preserve the archived CAR-002 capability snapshot and trace contract as
  immutable historical evidence, while adding an authoritative successor
  capability freeze before any qualification-capable execution (Q1).
- Close CAP-Q6 by defining the alias-re-pointing detection rule, plus versioned
  refresh triggers — client change, catalog change, alias re-point, and
  source-ledger change — that invalidate affected evidence (Q1).
- Carry a dated amendment to AC-2.19 making subscription authentication the
  supported scored path and API-key an optional environment, preserving the two
  substantive guarantees unchanged: auth mode recorded per run, and no
  plan-based claim (Q2).
- Probe the full ordered supported-effort set from `low` through `max` for every
  role-eligible model, so the A2 descend-and-boundary-retest search has a
  defined ladder (Q3).
- Implement one canonical Python 3.11 standard-library materializer inside the
  shipped `speckit_pro_runner` module, consumed now by a thin Layer 6 adapter
  and reused directly by the CAR-006 frontmatter drift gate and session
  preflight (Q4).
- Demote the existing dual-platform prompt-emulation benchmark to explicitly
  labeled smoke evidence by editing the shared runner in place, coordinating the
  merge with the in-flight G56R-003 branch (Q5).
- Emit new `execution_trace_id` records conforming unchanged to the frozen
  CAR-002 `exactTreatmentReplay` contract, and publish a separate versioned
  experiment/score/decision bundle that references them by ID (Q6).
- Hard-gate deterministic role, safety, grounding, mutation, tool, output, and
  acceptance contracts, then measure quality with a frozen semantic rubric under
  two candidate-blind ballots plus a third adjudicator on disagreement, with all
  ballots retained (Q7, Q8).
- Select among passing candidates by **raw-vector Pareto dominance** after
  absolute quality and reliability floors and task-paired cluster-adjusted
  non-inferiority, returning no qualification on a tie, mixed dominance, or
  uncertainty and never forcing a weighted ranking (Q9 as superseded by the
  2026-07-24 parity decision; see Parity Alignment).
- Keep live campaigns explicit, local, budgeted, and pinned; CI runs
  deterministic replay, contract, scorer, and statistical tests only, with zero
  live calls (Q10).
- Make CAR-003 qualification-capable without emitting final per-agent route
  policies: CAR-007 through CAR-010 own the outcome-bearing cohort campaigns
  (Q11).
- Prove the end-to-end platform with a live calibration-only partition whose
  records are explicitly ineligible for qualification, then freeze one versioned
  analysis plan before any cohort outcomes exist (Q12, Q13).
- Deliver CAR-003 as three ordered review slices: WP-A intact; corpus and
  blinded scoring; experiment policy, statistics, and the calibration-only pilot
  (Q14).

## Non-goals

- Mutating or reinterpreting the archived CAR-002 capability snapshot, telemetry
  profile, or trace contract schema (Q1, Q6).
- Final preferred and fallback route policies, shipped defaults, aggregate
  release identities, resolver or preflight behavior, and release confirmation —
  Q11.
- Running outcome-bearing per-agent A1/A2/A3, Stage B, or Stage C campaigns;
  CAR-003 implements the stages, the cohort specs execute them (Q11).
- Consuming screening, selection, cohort-lock, or untouched
  integrated-confirmation objectives during the CAR-003 pilot (Q12).
- Treating the current lexical heading and word-overlap scorer as qualification
  evidence (Q7).
- Requiring an API key for any supported path. The plugin supports API keys but
  must never require one — the user's constraint, verbatim: *"we don't have an
  API key and shouldn't need one. The plugin does support api keys but we should
  not require one."* (Q2).
- Running nondeterministic or chargeable live model campaigns in default CI
  (Q10).
- Retrying one candidate arm independently, or discarding candidate-caused
  failures from the estimand — settled by AC-2.7 and AC-2.14, not re-litigated.
- Treating fast mode or any orchestration-topology-changing mode as an ordinary
  per-agent effort; those remain policy-level controls owned by CAR-004.
- Committing raw live model, CLI, prompt, or response bytes. Raw captures
  inherit the sanitization contract CAR-002 established.
- Adding active repository Bash or `jq` dependencies, external evaluation
  frameworks, or a second materializer implementation.

## Design Tree (Q&A log)

### Q1. How should CAR-003 handle capability-snapshot staleness, given Opus 5 shipped today and CAR-002 binds `opus` to `claude-opus-4-8` as of 2026-07-17?

**Branch:** Dependency integrity and candidate admission

**Recommended answer:** Successor + refresh triggers (Recommended)
> CAR-003 ships the authoritative collector, captures one immutable successor
> snapshot, and closes CAP-Q6 by defining the alias-re-pointing detection rule
> plus versioned refresh triggers that invalidate affected evidence. The
> committed snapshot records `runtime_capability_snapshot_id`
> `CAR-002-RCS-2026-07-17-V3` with `opus` bound to `claude-opus-4-8`, and lists
> CAP-Q6 alias re-pointing with `disposition: open`. AC-2.21 makes alias
> re-pointing a requalification trigger. The two models also differ
> behaviorally — Opus 4.8 requires an explicit adaptive-thinking setting while
> Opus 5 thinks by default and rejects disabled thinking above `high` effort —
> so a silent re-point changes treatment, not merely identity.

**Alternatives offered:**
- One-time re-probe, no trigger rules: Refresh once and treat the snapshot as fixed for the series; leaves CAP-Q6 open and cannot distinguish plugin fallback from platform re-pointing.
- Contract only, cohorts collect their own: Define the schema and invalidation rules but collect nothing; leaves the calibration pilot with no admitted candidate set.

**User's answer:** Successor + refresh triggers (Recommended)

**Notes:** The user surfaced the decisive fact directly: *"today Anthropic
launched Opus 5!"* An earlier framing of this question centered on
authentication rather than staleness and was withdrawn as mis-scoped; the auth
axis was split out into Q2.

---

### Q2. How should CAR-003 reconcile AC-2.19's requirement that scored campaigns run under a dedicated API-key-authenticated environment?

**Branch:** Environment contract and evidence authority

**Recommended answer:** Amend AC-2.19 explicitly (Recommended)
> CAR-003 carries a dated amendment making subscription authentication the
> supported scored path and API-key an optional environment, while preserving
> the two substantive guarantees unchanged: auth mode recorded per run, and no
> plan-based claim. AC-2.5 independently pins the cost coefficients to the
> published API price sheet as diagnostic-derived rather than plan accounting,
> so the raw token vector and its weighting stay legitimate under either auth
> mode. CAR-001 established the precedent for this shape with its
> evidence-parity amendment.

**Alternatives offered:**
- Spec supports both, no PRD amendment: Less process overhead, but Analyze cross-checks spec against PRD acceptance criteria and would surface an unamended AC-2.19 as a contradiction finding every phase.
- Keep AC-2.19 literal, scored path blocked: Faithful to the PRD as written, but makes the calibration pilot unrunnable and pushes the conflict onto CAR-007 unchanged.

**User's answer:** Amend AC-2.19 explicitly (Recommended)

**Notes:** User constraint stated verbatim: *"we don't have an API key and
shouldn't need one. The plugin does support api keys but we should not require
one."*

The reasoning above cited AC-2.5's price-sheet-pinned coefficients as what keeps
the resource evidence diagnostic-derived. AC-2.5 was subsequently amended to the
Pareto rule (see Q9 and Parity Alignment), which strengthens rather than weakens
this decision: with no price coefficients anywhere in the selection rule, there
is no plan-accounting surface for the auth mode to contaminate. The decision to
amend AC-2.19 is unchanged.

---

### Q3. What effort ladder should the successor snapshot establish?

**Branch:** Capability coverage and search origin

**Recommended answer:** Full ordered set, low to max (Recommended)
> Probe every supported ordinary effort per role-eligible model. AC-2.11
> requires an ordered supported-effort set from `low` through `max`, and A2's
> descend-and-boundary-retest step is undefined without knowing the next lower
> rung. The committed CAR-002 snapshot covers only `max` for
> opus/sonnet/fable/haiku plus `low` for haiku/sonnet — so `high`, the AC-2.1
> documented-default search origin, was never probed at all, and neither were
> `medium` or `xhigh`. `xhigh` is documented as the best setting for coding and
> agentic work and is Claude Code's own default, so omitting it would hide a
> likely-winning route for exactly these roles.

**Alternatives offered:**
- Search origin plus extremes only: Cheaper up front, but A2 would then mutate the capability record mid-campaign, colliding with the snapshot being immutable evidence.
- Minimal patch, add `high` only: Smallest probe cost, but leaves the effort search unable to reach the rung most likely to win.

**User's answer:** Full ordered set, low to max (Recommended)

---

### Q4. Where should the canonical agent materializer live?

**Branch:** Source ownership and shared production seam

**Recommended answer:** Shipped runner module (Recommended)
> Place it in `speckit_pro_runner` with Layer 6 keeping only a thin adapter, so
> CAR-006's frontmatter drift gate and session preflight consume the same
> component rather than a copy. This repository settled the rule after the test
> relocation work: a library used by shipped code lives in the plugin, not under
> `tests/`, and CAR-006's gate and resolver are shipped surfaces. This also
> matches G56R-003's Q5 decision, keeping the two platforms structurally
> parallel — and it supersedes the CAR-003 roadmap Key Files entry that proposed
> `tests/speckit-pro/layer6-efficiency/lib/agent_materializer.py`.

**Alternatives offered:**
- Layer 6 first, relocate during CAR-006: Honors the roadmap Key Files as written, but relocating a payload-affecting module means running the artifact and hash regeneration ritual twice and re-proving equivalence after the move.
- Contract and fixtures only, defer implementation: Shrinks CAR-003, but WP-A's core deliverable is proving real dispatch and materialized rendering semantically equivalent, which needs a working materializer.

**User's answer:** Shipped runner module (Recommended)

**Notes:** This decision moves production code into the shipped payload, so the
reviewability profile changes from the roadmap's recorded `Production files: 0`.
Accounted for in Q14.

---

### Q5. How should CAR-003 avoid colliding with the in-flight G56R-003 branch over the shared smoke runner?

**Branch:** Cross-platform coordination and shared infrastructure

**Recommended answer:** Add alongside, don't edit the shared file (Recommended)
> `run-efficiency-benchmarks.py` is a single 495-line dual-platform script that
> dispatches both `claude -p` and `codex exec` off a `--codex` flag, with
> separate `fixtures/` and `fixtures-codex/` directories. Both CAR-003 and
> G56R-003 name it as the file to demote to smoke, and G56R-003 is already
> scaffolded and past its Specify phase. The recommendation was to mark the
> legacy path as smoke through results metadata and docs rather than editing the
> shared script, since the roadmap's requirement is that historical results
> carry `non_release_evidence` — a property of the records.

**Alternatives offered:**
- Edit the shared runner, coordinate the merge: Most literal reading of "demote the current prompt-emulation path," but puts two parallel worktrees into the same 495-line file.
- Split into per-platform runners first: Cleanest end state, but unrequested scope that guarantees the collision rather than avoiding it.

**User's answer:** Edit the shared runner, coordinate the merge

**Notes:** Chosen against the recommendation. The consequence carried forward:
CAR-003 will modify the shared dual-platform runner, so the spec and plan must
treat merge coordination with the G56R-003 branch as an explicit deliverable.
This repository's shared-infrastructure conflicts are resolved by merge rather
than rebase.

---

### Q6. How should qualification scores relate to the frozen CAR-002 trace schema?

**Branch:** Evidence schema and historical integrity

**Recommended answer:** Separate versioned score bundle (Recommended)
> Emit new `execution_trace_id` records conforming unchanged to CAR-002's
> `exactTreatmentReplay` contract, and publish a separate versioned
> experiment/score/decision bundle that references them by ID. The frozen schema
> already draws this line: `exactTreatmentReplay` carries `scorable` — whether a
> run is admissible — but its `outcome` is only `{status, telemetry_ref, notes}`
> with no score, acceptance, or resource vector. Keeping delivery proof and
> outcome judgment in different artifacts preserves that boundary and leaves
> archived CAR-002 evidence untouched.

**Alternatives offered:**
- Version the trace schema to carry scores: One artifact and simpler joins, but mutates a schema CAR-002 deliberately froze and merges treatment proof with outcome judgment.
- Annotate copied trace records: Avoids editing the frozen schema, but creates two records describing the same run and therefore two candidate sources of truth.

**User's answer:** Separate versioned score bundle (Recommended)

---

### Q7. What scoring authority should CAR-003 freeze for outcome-bearing evaluation?

**Branch:** Quality measurement and scorer governance

**Recommended answer:** Hybrid — deterministic gates plus blinded semantic (Recommended)
> Keep deterministic role, safety, grounding, mutation, tool, output, and
> acceptance checks as hard gates, then measure quality with a frozen semantic
> rubric scored blind to candidate identity. AC-2.20 forbids any score threshold
> predetermining the cause and requires adjudication into five named classes;
> the current `lib/quality-scorer.py` is lexical heading and word-overlap
> matching, which cannot distinguish a genuinely worse answer from a
> differently-worded correct one, so it cannot carry that judgment alone.

**Alternatives offered:**
- Deterministic checks only: Cheapest and fully replayable with no judge dependency, but cannot detect quality regressions that pass every mechanical gate.
- Single frozen semantic judge: Simpler pipeline and lower per-run cost, but concentrates judge bias and loses the cheap hard-fail path for contract and safety violations.

**User's answer:** Hybrid — deterministic gates plus blinded semantic (Recommended)

---

### Q8. What adjudication protocol should the scorer contract require when output is low or surprising?

**Branch:** Blinding, calibration, and disagreement handling

**Recommended answer:** Two blinded ballots plus tiebreak (Recommended)
> Two independent candidate-blind rubric ballots, with a third frozen blinded
> adjudicator resolving disagreement, and every ballot retained so the decision
> replays. Disagreement between two judges is itself the signal that a result
> belongs in one of AC-2.20's non-quality buckets rather than being scored.
> Matches G56R-003's Q12 decision, keeping the two platforms' evidence
> comparable.

**Alternatives offered:**
- Single frozen blinded judge: Roughly half the adjudication cost and simpler to keep deterministic, but produces no disagreement signal, so misclassification becomes invisible rather than flagged.
- Automated pass with human review on contested: Highest fidelity on hard cases, but AC-2.15 constrains human steering to a frozen scripted policy and manual review does not scale across a twelve-role corpus.

**User's answer:** Two blinded ballots plus tiebreak (Recommended)

---

### Q9. How should CAR-003 implement the AC-2.5 price-sheet pinning for the selection scalar?

**Branch:** Resource evidence and selection rule

**Recommended answer:** Content-address one dated revision, freeze it (Recommended)
> Capture the published price sheet once at lock time, hash it, record the
> revision date, and use those coefficients for the whole campaign regardless of
> later list-price movement. This is concretely load-bearing right now: Sonnet 5
> is on introductory pricing that reverts on 2026-08-31, so an unfrozen scalar
> would silently reweight mid-campaign and make early and late runs
> incomparable.

**Alternatives offered:**
- Re-fetch current prices per campaign: More faithful to present-day spend, but two campaigns either side of a price change lose their common yardstick.
- Hardcode coefficients in the analysis plan: Fully deterministic with no fetch path, but drops the provenance binding to a published dated revision that keeps the figure diagnostic-derived.

**User's answer:** Content-address one dated revision, freeze it (Recommended)

**Notes:** At interview time this was framed as a deliberate platform divergence:
G56R-003 chose a quality-first Pareto comparison over raw resource vectors, while
the CAR PRD (AC-2.5) and roadmap both mandated a single predeclared
price-weighted scalar.

**SUPERSEDED 2026-07-24.** The maintainer subsequently directed that CAR-003 and
G56R-003 be logically the same with no logical divergence, and chose the Pareto
rule. CAR-003 therefore selects by **raw-vector Pareto dominance**, and the
price-sheet pinning mechanism described above is not implemented. Published price
data may be cited as diagnostic context only, never as a selection coefficient.
This required amending PRD AC-2.5 and the roadmap qualification rule, both
carried on this branch with dated amendment notes. This entry is retained
unrewritten because the Q&A log records what was asked and answered at scoping
time.

---

### Q10. Where should outcome-bearing live evaluation campaigns run, and what does CI cover?

**Branch:** Execution environment and CI boundary

**Recommended answer:** Local budgeted campaigns; CI replays only (Recommended)
> Live runs happen behind an explicit operator command with a frozen budget and
> pinned environment; CI runs deterministic replay plus contract, scorer, and
> statistical tests with zero live calls. The constitution already makes live
> probing operator-only and never CI, and CAR-002 shipped its full 3193-test
> suite with zero live calls — this keeps that property intact.

**Alternatives offered:**
- Capped live screening subset in CI: Continuous real-dispatch signal and early drift detection, but puts nondeterminism and per-run cost into the default gate and breaks the operator-only rule.
- No CI coverage for either: Smallest CI surface, but loses the deterministic regression net over scorer contracts and statistical decisions, which are pure code and cheap to test.

**User's answer:** Local budgeted campaigns; CI replays only (Recommended)

---

### Q11. Should CAR-003 run the A1/A2/A3/B/C stages as outcome-bearing campaigns, or just build and validate the platform?

**Branch:** Roadmap stage ownership

**Recommended answer:** Cohort specs run them (Recommended)
> CAR-003 builds and validates the reusable qualification platform, corpus,
> stage implementations, and frozen analysis contract; CAR-007 through CAR-010
> execute the per-agent campaigns and emit final route policies. The roadmap
> already puts final route policies out of CAR-003's scope and assigns four
> disjoint cohorts to those specs, and AC-2.12 spends the confirmation set
> exactly once — running campaigns here would consume partitions before cohort
> locks exist.

**Alternatives offered:**
- CAR-003 runs complete qualification: Fewer handoffs and one place to debug, but moves campaign cost and every evidence partition into a spec whose declared scope excludes final route policies.
- Split the ladder, A1/A2 here: Early screening signal, but splits one statistical ladder across specs while AC-2.12 requires its partitions stay disjoint and accounted for.

**User's answer:** Cohort specs run them (Recommended)

---

### Q12. What evidence boundary should CAR-003's own live validation run use?

**Branch:** Pilot validity and evidence partitioning

**Recommended answer:** Calibration-only partition (Recommended)
> Use dedicated disposable objectives to prove exact dispatch, scoring, and
> statistical plumbing end-to-end, with every pilot record explicitly marked
> ineligible for qualification. This validates WP-A's real `speckit-pro:<name>`
> dispatch claim without touching the screening, selection, cohort-lock, or
> untouched confirmation sets that AC-2.12 keeps disjoint.

**Alternatives offered:**
- Pilot doubles as A1 screening: Efficient if the platform is already correct, but a pilot exists to find platform defects, and any fix afterwards invalidates the screening evidence while the partition stays spent.
- Replay only, no live pilot: Zero cost and keeps every partition pristine, but never demonstrates that real installed-plugin dispatch and transcript-proven spawn work.

**User's answer:** Calibration-only partition (Recommended)

---

### Q13. When should the numeric qualification margins, sample sizes, power, multiplicity, and attrition rules become immutable?

**Branch:** Analysis-plan governance

**Recommended answer:** Freeze after calibration, before any cohort run (Recommended)
> Let the calibration-only pilot and historical non-release evidence estimate
> variance and feasibility, then lock one versioned analysis plan covering
> margins, sample sizes, power, multiplicity, racing, attrition, and terminal
> rules before CAR-007 starts. Calibration records are already ineligible for
> qualification, so using them for variance estimation cannot contaminate
> outcomes — and AC-2.12 makes changing a locked decision afterwards invalidate
> the affected evidence.

**Alternatives offered:**
- Freeze per cohort: More tailored to observed variance, but the multiplicity strategy spans all four cohorts and choosing it four times independently makes the family-wise error rate incoherent.
- Set conservative values now: Maximally predeclared, but guessing at variance yields campaigns that are either underpowered and inconclusive or wastefully oversized.

**User's answer:** Freeze after calibration, before any cohort run (Recommended)

---

### Q14. How should CAR-003 be divided for review?

**Branch:** Reviewability and vertical slicing

**Recommended answer:** Three ordered slices (Recommended)
> Slice 1 is WP-A intact: successor snapshot and collector, refresh triggers,
> shipped materializer, exact-treatment runner, and trace records. Slice 2 is
> corpus plus scoring: twelve-role fixtures, scorer contracts, two-ballot
> adjudication, and the gitignore allow rule. Slice 3 is experiment policy,
> selection rule, statistics, and the calibration-only pilot. The shared
> estimator returned `estimated_loc: 502`, `suggested_slices: 2`, `status: warn`
> on the roadmap's recorded signals; re-run with post-interview signals
> (approximately 26 files, 19 requirements) it returns `estimated_loc: 675`,
> still `suggested_slices: 2`. The binding constraint is not the LOC estimate
> but the reviewability gate's hard block at 25 total files, which a single PR
> would cross. Three slices preserve WP-A whole as the roadmap requires, divide
> WP-B along its corpus-versus-statistics seam, keep each PR under the block
> thresholds, and match G56R-003's three-slice decision.

**Alternatives offered:**
- Two slices matching the two work packages: The most literal reading of the preserve-both-packages mandate and what the estimator suggests, but WP-B alone carries the corpus, scorers, adjudication, statistics, and pilot, so slice two would likely still block.
- One slice, accept the warn: Cleanest single review narrative, but roughly 26 files crosses the hard 25-file block and would fail the PR-time reviewability check.

**User's answer:** Three ordered slices (Recommended)

**Notes:** The estimate is an advisory pre-implementation guess. The plan-phase
reviewability gate remains authoritative, and the Q4 decision to ship the
materializer in `speckit_pro_runner` means CAR-003 now has a non-zero production
file count where the roadmap recorded `Production files: 0`.

## Grounded Context

- The committed capability snapshot is
  `docs/ai/research/claude-runtime-capability-snapshot.json`, id
  `CAR-002-RCS-2026-07-17-V3`, captured `2026-07-17T10:47:42Z` under
  `authentication_mode: subscription` with `pinned_client_version`
  `2.1.212 (Claude Code)`. It records six tuples — `opus/sonnet/fable/haiku`
  at `max`, plus `haiku` and `sonnet` at `low` — and four alias bindings:
  `opus` to `claude-opus-4-8`, `sonnet` to `claude-sonnet-5`, `fable` to
  `claude-fable-5`, `haiku` to `claude-haiku-4-5-20251001`.
- That snapshot lists two open items: CAP-Q6 alias re-pointing with
  `disposition: open`, and `models_endpoint` with `disposition: gap`
  (`models_endpoint_evidence` is null).
- The locally installed Claude Code client is `2.1.219`, ahead of the pinned
  `2.1.212`.
- Anthropic launched Claude Opus 5 on 2026-07-24, one week after the snapshot
  bound `opus` to `claude-opus-4-8`.
- The frozen trace contract is
  `docs/ai/research/claude-trace-contract.schema.json`, a `oneOf` over
  `runtimeCapabilitySnapshot`, `telemetryProfile`, `routeResolution`, and
  `exactTreatmentReplay`. `exactTreatmentReplay` carries `execution_trace_id`,
  `record_class`, `observed_model_id`, `scorable`, and an `outcome` of
  `{status, telemetry_ref, notes}` only. `routeResolution` already carries
  `fast_mode_state` and `parent_session_configuration`.
- The existing smoke runner is
  `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`, a single
  495-line dual-platform script serving both `claude -p` and `codex exec`.
- The current lexical scorer is
  `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py`.
- Claude-side role fixtures currently cover two roles (`consensus-synthesizer`,
  `gate-validator`); the roadmap requires expansion to twelve.
- `tests/speckit-pro/layer6-efficiency/.gitignore` is currently a blanket
  `results/` ignore with no allow rule for consolidated baselines.
- The reviewability gate thresholds are warn at 400 reviewable LOC / 6
  production files / 15 total files, and block at 800 reviewable LOC / 8
  production files / 25 total files.
- The setup-mode reviewability gate returned `status: warn`, `pass: true`, zero
  blockers, with one warning: primary surfaces 5 exceeds the warn threshold of 1.
- G56R-003, the Codex mirror, is scaffolded and past its Specify phase on branch
  `g56r-003-evaluation-runner-scoring`.

Capability path: official Anthropic model and effort documentation, plus the
pinned local client version, plus CAR-001's candidate ledger, CAR-002's immutable
evidence contracts, and the CAR-003 roadmap section. Confidence is high for the
committed repository artifacts and the documented model catalog; no claim is made
about how the `opus` alias resolves today, which the CAR-003 collector must
establish by operator probe.

## Parity Alignment with G56R-003

Post-interview directive from the maintainer: CAR-003 and G56R-003 must be
**logically the same, with no logical divergence** — differing only in values
where a platform documents a different surface. G56R-003 is further along
(through Plan, with committed contract schemas), so its `spec.md` is the
reference shape. Eight items were aligned to it after the interview closed:

| Aligned item | G56R reference |
|---|---|
| Four user stories — successor freeze, exact treatment, corpus scoring, analysis plan — mapped onto the same three slices | US1–US4 |
| Four Clarify sessions, adding a dedicated materialization/delivery/trace-join session | Clarifications S1–S4 |
| Checklist domains changed to data-integrity, error-handling, llm-integration, performance | committed `checklists/` |
| Explicit score-eligibility predicate gating every scored outcome | FR-030 |
| Separate closed failure taxonomies per plane, including unclassifiable attrition as an evidence-boundary failure | FR-029, FR-034 |
| Equivalence proven by content-hash identity, not parsed-field or semantic comparison | FR-006, FR-008 |
| Deny-by-default sanitization allowlist that fails closed and blocks publication | FR-027, FR-036 |
| Contract-only roles retained but never run until a route is admitted | FR-011, FR-012 |
| Success criteria mirrored one-for-one | SC-001–SC-016 |
| **Selection rule: raw-vector Pareto dominance after absolute floors and paired non-inferiority; no forced weighted ranking** | FR-018, FR-019 |

**Selection rule — the one item that required amending Claude-side source
documents.** CAR PRD AC-2.5 and the roadmap qualification rule both mandated a
predeclared price-weighted scalar with coefficients pinned from a dated published
price sheet. G56R-003 FR-019 forbids a forced weighted ranking and ends in Pareto
dominance. The Codex PRD is permissive here — line 355 allows "one predeclared
environment-independent score **or** Pareto rule" — so G56R-003's Pareto choice
was a free interview decision, while CAR's scalar was mandatory. Converging on
Pareto therefore required amending the Claude side. On 2026-07-24 the maintainer
directed exactly that. Both documents now carry dated amendment notes preserving
the superseded wording and its rationale:

- `docs/prd-claude-agent-routing.md` — AC-2.5
- `docs/ai/specs/claude-agent-routing-technical-roadmap.md` — qualification rule

The raw-vector reporting obligation is unchanged; only the rule that ranks
passing candidates changed.

**Platform-surface differences retained (values, not logic).** The raw token
vector categories differ — CAR carries cache-write by TTL class and cache-read
where Codex carries cached-input tokens — and CAR carries the AC-2.19 auth
amendment because only the Claude PRD constrains the scored-run authentication
environment. Both platforms record the auth mode of every run and produce no
plan-based claim. The parity contract explicitly contemplates this: platform
differences remain values, not schemas.

**Note on the parity contract's scope.** `agent-routing-parity-contract.md`
states it applies to `CAR-001` and `G56R-001` and is the active foundation for
the `-002` pair. It does not formally extend to `-003`. Parity here is therefore
a maintainer decision recorded in this document, not a contract obligation.

## Open Questions

- **What:** Has the `opus` alias actually re-pointed from `claude-opus-4-8` to
  `claude-opus-5` since the CAR-002 snapshot was captured?
  **Why deferred:** Confirming it requires an operator live probe, which is
  exactly the collector CAR-003 slice 1 builds; scaffolding deliberately does not
  burn a probe.
  **Suggested next step:** Run the successor-snapshot collector as the first
  operator action in slice 1 and record the result, whichever way it resolves.
- **What:** What exact numeric semantic floors, practical margins, sample sizes,
  alpha, power, multiplicity adjustment, racing rule, and attrition cap should
  the first outcome-bearing analysis plan use?
  **Why deferred:** Q13 deliberately reserves these until the calibration-only
  pilot and historical non-release evidence are available.
  **Suggested next step:** Calculate and independently review during slice 3,
  then freeze the versioned plan before CAR-007 begins.
- **What:** Which calibrated adjudicator identities and rubric calibration set
  should supply the two primary ballots and the disagreement ballot?
  **Why deferred:** Q8 freezes the protocol, but evaluator identities depend on
  the implementation-time capability snapshot, which Q1 makes a moving target
  until the successor freeze lands.
  **Suggested next step:** Bind identities, versions, calibration results, and
  invalidation triggers in the scorer registry before the calibration pilot.
- **What:** How will the shared-runner edit in slice 1 be sequenced against the
  in-flight G56R-003 branch?
  **Why deferred:** Q5 chose to edit the shared file and coordinate rather than
  avoid the collision; the sequencing depends on which branch merges first.
  **Suggested next step:** Sync from `main` before implementing slice 1, and
  resolve any overlap with `g56r-003-evaluation-runner-scoring` by merge rather
  than rebase.

## Recommended Next Step

The CAR-003 scaffold completes from this design concept. Start
`/speckit-pro:speckit-autopilot` in the dedicated CAR-003 worktree with the
generated workflow file. The Specify and Plan phases must reconcile three things
this interview surfaced: the roadmap Key Files entry placing the materializer
under `tests/` (superseded by Q4), the roadmap's recorded `Production files: 0`
reviewability budget (no longer accurate after Q4), and the AC-2.19 amendment
recorded in Q2.

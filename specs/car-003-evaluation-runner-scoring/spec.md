# Feature Specification: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Feature Branch**: `car-003-evaluation-runner-scoring`

**Created**: 2026-07-24

**Status**: Draft

**Input**: User description: "CAR-003 builds an additive successor capability freeze, an exact-treatment evaluation runner backed by one canonical shipped materializer, a governed twelve-role corpus with blinded scoring, and a frozen calibration analysis platform for later Claude Code agent routing cohorts."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish Successor Capability Freeze (Priority: P1)

As a capability steward, I can collect the pinned Claude Code runtime catalog and publish a versioned non-empty successor freeze containing only source-admitted, runtime-supported model and effort tuples, while preserving CAR-002 as immutable historical evidence.

**Why this priority**: Later evaluation and routing decisions require a trustworthy executable candidate set before any treatment, scoring, or analysis can be valid. The archived snapshot binds `opus` to a model identity that the published catalog has since moved past, so no qualification-capable execution is trustworthy until the freeze is refreshed.

**Independent Test**: Can be fully tested by collecting the pinned runtime catalog, comparing it with the current official-source candidate ledger, and verifying that the new freeze is additive, non-empty, source-bound, and traceable without altering CAR-002 artifacts.

**Acceptance Scenarios**:

1. **Given** the archived CAR-002 six-tuple snapshot and the current pinned runtime catalog, **When** the steward generates the CAR-003 capability freeze, **Then** CAR-002 remains unchanged and a new versioned freeze contains only tuples admitted by both the official-source ledger and runtime support.
2. **Given** a model or effort appears in runtime discovery but not in the official-source candidate ledger, **When** the freeze is assembled, **Then** that tuple is excluded and the exclusion reason is recorded from the closed capability-exclusion taxonomy.
3. **Given** fast mode or another orchestration-topology-changing mode appears in current capability evidence, **When** ordinary per-agent effort tuples are qualified, **Then** that mode is classified as a CAR-004 policy control and not admitted as an ordinary candidate effort.
4. **Given** the pinned runtime is probed for a role-eligible model, **When** the supported-effort set is recorded, **Then** the full ordered set `low` through `max` is covered, including `high` as the documented search origin that CAR-002 never observed.
5. **Given** an observed model identity differs from the resolved qualified identity for a requested alias, **When** the collector evaluates the result, **Then** the difference is recorded as an alias re-pointing event attributed to platform behavior, CAP-Q6 moves from open to closed, and the event is never reported as a SpecKit Pro fallback.

---

### User Story 2 - Prove Exact Treatment Before Scoring (Priority: P1)

As an evaluation author, I can materialize and run the actual named-agent policy, prove the exact treatment each candidate received, and emit immutable replayable traces before any outcome is scored.

**Why this priority**: Semantic outcomes are not meaningful unless reviewers can prove that each candidate ran the intended named-agent route under the requested controls. The current path emulates agents with bare prompts, which is smoke-only degradation evidence that cannot support release.

**Independent Test**: Can be fully tested by materializing an admitted executable route, running a disposable calibration objective, and verifying that all mandatory treatment evidence exists before any score bundle is accepted.

**Acceptance Scenarios**:

1. **Given** an admitted executable route and a governed calibration objective, **When** the runner executes the route, **Then** it records named agent, requested route, instruction hash, permitted tools and mutation contract, skills, MCP startup and schema evidence, parent controls, client, context, and all mandatory CAR-002 treatment fields before scoring begins.
2. **Given** a route cannot prove installed-plugin policy or content-hash-identical canonical materialization, **When** the runner prepares the treatment record, **Then** the run is blocked from outcome scoring and classified as an infrastructure or treatment failure.
3. **Given** an existing CAR-002 trace contract, **When** CAR-003 creates execution evidence, **Then** each new `execution_trace_id` is immutable and later experiment, score, and decision bundles reference it without mutating archived evidence or extending the frozen outcome shape.
4. **Given** a real installed-plugin session is dispatched, **When** the treatment record is assembled, **Then** the `speckit-pro:<name>` spawn is proven from the transcript and the per-model usage breakdown establishes the effective model rather than inferring it from configuration.
5. **Given** two arms of a comparison pair are executed, **When** the campaign is set up, **Then** cache state is isolated between arms so that one arm cannot warm another's cache.

---

### User Story 3 - Score Governed Twelve-Role Corpus (Priority: P2)

As a scorer, I can evaluate one governed twelve-role corpus through deterministic hard gates and blinded semantic ballots, with explicit fixture, scorer, treatment, candidate, and infrastructure failure classes.

**Why this priority**: Cohort specs need a stable fixture and scoring contract that separates route quality from harness failures and avoids outcome leakage.

**Independent Test**: Can be fully tested by running the governed corpus against admitted executable routes and verifying that deterministic gates, blind ballots, adjudication, failure classes, and provenance are complete for every accepted score bundle.

**Acceptance Scenarios**:

1. **Given** the eleven required core roles and `autopilot-fast-helper`, **When** the fixture corpus is prepared, **Then** all twelve role contracts are present, the helper is identified separately from the required core, and only admitted executable routes are run.
2. **Given** a role has a governed fixture contract but no shipped agent definition yet, **When** the corpus is executed, **Then** the contract is retained and the role is never run until an executable route is admitted.
3. **Given** a candidate run reaches semantic evaluation, **When** scoring starts, **Then** deterministic hard gates have already passed and two independent candidate-blind rubric ballots are collected with complete provenance.
4. **Given** two blinded ballots disagree according to the frozen rubric, **When** adjudication is required, **Then** a frozen third adjudicator resolves the outcome and its provenance is attached to the score bundle.
5. **Given** a fixture, scorer, treatment, candidate, or infrastructure failure occurs, **When** the run is classified, **Then** the failure class is explicit, drawn from the closed taxonomy for its own plane, and downstream analysis uses the class according to the frozen estimand.

---

### User Story 4 - Freeze Calibration Analysis Plan (Priority: P3)

As an experiment owner, I can run a calibration-only pilot, freeze the numeric analysis plan, and replay paired decision behavior without creating final route policies or consuming final cohort evidence.

**Why this priority**: Later CAR-007 through CAR-010 cohorts need a precommitted decision platform that cannot adapt to their observed outcomes.

**Independent Test**: Can be fully tested by running only disposable calibration objectives, freezing the analysis plan, and replaying decisions from versioned bundles while proving no final cohort or integrated-confirmation partition was consumed.

**Acceptance Scenarios**:

1. **Given** calibration and historical non-release evidence, **When** the analysis plan is frozen, **Then** numeric floors, non-inferiority rules, Pareto inputs, rerun limits, and inconclusive handling are versioned before cohort outcomes are observed.
2. **Given** paired candidate outcomes, **When** the decision platform evaluates qualification, **Then** it applies absolute semantic and reliability floors, task-paired cluster-adjusted non-inferiority, and only then compares the raw vector through Pareto dominance.
3. **Given** evidence is incomplete, inconclusive, or outside the allowed calibration partition, **When** qualification is requested, **Then** the result is no qualification, no weighted ranking is forced, and no final preferred or fallback route policy is created.
4. **Given** a live campaign is requested, **When** campaign setup is validated, **Then** it is explicit, local, pinned, and budgeted, while the default suite remains limited to deterministic replay with zero live calls.
5. **Given** a comparison pair has already been bound, **When** a capability freeze, fixture, scorer, or policy refresh occurs, **Then** the refresh creates an additive invalidation and never rebinds the existing pair.

### Edge Cases

- The pinned runtime catalog is available but the official-source ledger contains no matching tuple.
- The official-source ledger admits a candidate that the pinned runtime does not support.
- The pinned runtime exposes visible defaults, aliases, aggregate identities, fast mode, or other topology-changing modes that must not become ordinary per-agent candidates.
- Catalog collection succeeds but omits required provenance such as client version, account or environment boundary, collection method, raw digest, timestamps, defaults, supported efforts, or invalidation criteria.
- The source/runtime intersection is empty or contains only alias, aggregate, or topology-control entries.
- No documented catalog enumeration surface is available, so the collector must derive supported tuples from observed probe results rather than an authoritative listing.
- A committed snapshot or replay fixture contains a non-allowlisted account, authentication, credential, raw-response, private-host, absolute-path, remote, billing, or plan field.
- A role has a governed fixture contract but no shipped agent definition yet.
- Installed-plugin policy and canonical materialization differ in any byte of the shipped frontmatter-plus-body content hash.
- MCP startup succeeds but schema evidence is incomplete or non-replayable.
- Parent controls, permitted tools, mutation contract, skills, or context evidence are missing after a run reaches terminal state.
- A trace reports profile-supported effective model and effort observations but lacks configured-route proof or authoritative route-change monitoring.
- An alias silently re-points mid-campaign, changing thinking defaults and therefore the treatment rather than merely the recorded identity.
- A candidate fails, times out, is cancelled, exhausts budget, or is abandoned.
- A transient harness failure is identified after only one arm of a pair completed.
- A scorer ballot is missing, non-blind, stale relative to the frozen rubric, or lacks provenance.
- A fixture, rubric, scorer, adjudicator, or ballot is stale, invalid, identity-revealing, or no longer matches its bound version and digest.
- A committed scorer artifact contains raw prompts, responses, transcripts, personal scorer mappings, or other operator-private evidence.
- Attrition occurs that cannot be classified into any known plane.
- Calibration evidence overlaps with screening, selection, cohort-lock, or untouched integrated-confirmation objectives.
- Replay produces a different decision from the same versioned experiment, score, and analysis bundles.
- A run executes under API-key authentication when only subscription authentication was expected, or the auth mode is not recorded at all.
- Several disqualifying conditions fire on one attempt — for example the delivered agent is not the requested one, the observed identity diverges from the freeze, and the override proof is incomplete. Every fired code is recorded and the terminal disposition is the highest-precedence bucket, never whichever condition happened to be evaluated first.

## Clarifications

### Session 1 — Successor freeze and invalidation (2026-07-24)

- **Q: What may the effort canonicalization map admit?** → The map is keyed to
  official-source display strings and targets only the closed ordered ladder
  `low` < `medium` < `high` < `xhigh` < `max`. Omitted, `inherit`, runtime-only,
  API-only, alias, aggregate, and topology-changing values can never become
  ordinary candidate efforts; any unmapped source value records
  `canonical_effort_unknown`. (FR-003)
- **Q: What does each of the four refresh triggers invalidate, and what
  survives?** → All four invalidate freeze admission and every unexecuted
  binding derived from it, and additively invalidate affected experiment, score,
  and decision bundles. Immutable execution traces, treatment records, and
  already-bound pairs survive unchanged and are marked invalidated rather than
  rebound. Alias re-point additionally marks in-flight attempts for that alias
  non-scorable; a source-ledger change alone cannot admit a tuple the runtime
  never supported. (FR-041)
- **Q: What does an empty or invalid intersection publish, and may CAR-002's
  tuples be reused?** → Diagnostic collection evidence only; no authoritative
  successor freeze; qualification-capable execution blocked; and the six
  archived CAR-002 tuples are never promoted to an active candidate set.
  Immutable does not imply reusable — silently falling back to the archived
  binding is a live treatment-integrity failure mode, because that snapshot
  binds `opus` to a predecessor that differs from the current model on thinking
  defaults. (FR-044, new)
- **Q: Which runtime surface is the sole authority for freeze admission?** → The
  operator-run `claude -p` print-mode canary probe on the pinned client, with
  effort admitted only by configuration acceptance on that same surface.
  Subagent-frontmatter dispatch, the model picker, the catalog endpoint, visible
  defaults, and bundled client strings are diagnostic-only: they may corroborate
  or invalidate, never admit. Two independent grounds converge — the existing
  CAR-002 capability library already encodes the catalog endpoint as
  "corroborating (never alias-establishing)", and that endpoint yields evidence
  only under API-key authentication, so admitting on it would make freeze
  admission depend on an auth mode FR-042 forbids requiring. Disagreement
  between the admitting probe and a diagnostic observation must trigger recorded
  investigation or exclusion, never a logged-and-ignored footnote. (FR-002,
  FR-004)
- **Q: What separates an alias re-pointing event from a resolver fallback?** →
  The classification was already settled upstream: resolver fallback is a
  resolution-time substitution of the requested route; a platform route change
  is a delivery-time divergence from a route SpecKit Pro did not change. Only
  the detection mechanics were open, and they need five observables rather than
  four — the fifth is the pinned client version, because a client change is a
  distinct refresh trigger and would otherwise be misattributed as a platform
  re-point. The freeze-bound identity must be read from CAR-003's own successor
  freeze, not the identically named run-time field and not the archived CAR-002
  snapshot. Attribution is bounded rather than proven: documented
  serving-infrastructure changes can alter behavior without changing the model
  identity, so the enumerated cause set cannot certify its own completeness.
  The attribution label lives in a new additive record because the frozen
  `record_class` enumeration is closed. The detector is validated by synthetic
  replay below the live trigger path, which resolves the standing catch-22 that
  inducing a real re-point requires setting the very override the proof
  requires to be unset. (FR-039, FR-045, FR-046)

### Session 2 — Materialization, delivery, and trace joins (2026-07-24)

- **Q: What is the exact content-hash preimage?** → SHA-256 over the destination
  file's exact UTF-8 bytes read back from disk after write, with zero
  normalization and never from the in-memory render buffer. This is precisely
  what parsed-field equivalence cannot see: key order, whitespace, comments,
  unknown keys, line endings, encoding. (FR-008)
- **Q: Which telemetry observations are mandatory?** → The inherited profile
  never enumerated them — it constrains only list cardinality — which left this
  requirement undecidable as written. CAR-003 publishes its own versioned closed
  mandatory-observation manifest as an additive artifact. (FR-009)
- **Q: How is the trace digest computed and verified?** → SHA-256 over the
  existing canonical JSON serialization, recomputed and compared at bundle
  acceptance and at replay; mismatch or dangling reference blocks the decision
  bundle rather than repairing by rewrite. (FR-032)
- **Q: Does `scorable` bind the score-eligibility predicate, and what is
  `treatment_disposition`?** → `scorable` is derived solely from the record class
  and speaks only to platform-initiated route change, so it is necessary but
  never sufficient. `treatment_disposition` is **not** a new field: the shared
  treatment-record contract already closes it to `proven`, `unknown`,
  `non_scorable_rerouted`, `hard_fail`, and that contract is byte-identical
  across the Claude and Codex worktrees. Reusing it preserves parity; inventing
  a parallel vocabulary would have created a third unbridged taxonomy. (FR-030)
- **Q: How are co-occurring disqualifiers classified?** → Every fired condition
  is derived independently and recorded together in the `disposition_reasons`
  array; the terminal disposition is the highest-precedence bucket
  (`hard_fail` > `non_scorable_rerouted` > `unknown` > `proven`). There is no
  condition-level tie-break, and non-terminal causes are never discarded. This
  documents already-shipped shared behavior rather than inventing new behavior,
  so it introduces no cross-platform divergence. (FR-031)

### Session 3 — Corpus and blinded scoring (2026-07-24)

- **Q: Which checks are deterministic hard gates?** → The closed set `role`,
  `safety`, `grounding`, `mutation`, `tool`, `output`, `acceptance`, each
  recording pass/fail and an evidence digest; no ballot is collected until every
  required gate passes. (FR-014)
- **Q: How is a contract-only role retained without being run?** → Twelve role
  entries, each carrying independent `required_core` and `executable` booleans
  and binding every contract field even when not executable. Route bindings are
  absent for non-executable roles, which emit no score bundle and are never
  counted as attrition. (FR-012)
- **Q: What is the digest preimage for fixture and scorer artifacts?** → The
  same canonical JSON serialization used for trace digests, excluding the
  artifact's own digest field, recomputed at bundle acceptance and replay. The
  twin's schemas pin the digest *format* but never its preimage, which would
  have left deterministic replay unclosed. (FR-033)
- **Q: How should platform alias re-pointing be coded?** → Reuse the existing
  shared `service_reroute_requested_route_non_scorable` code in
  `disposition_reasons`; do **not** coin a Claude-only member. The enumerations
  are closed under `additionalProperties: false` and the treatment-record
  contract is byte-identical across worktrees, so a unilateral addition would
  validate on one platform and fail on the other. The two platforms' wordings
  name one causal event; splitting them would fragment a category downstream
  analysis treats as mutually exclusive. (FR-034)
- **Q: How is candidate-blindness enforced, and what about the residual?** →
  A mechanical pre-ballot leak check strips explicit identifiers and fails
  closed with the existing `ballot_non_blind` code. Beyond that, scorers and
  adjudicators are excluded from any candidate's own model family, because
  judges recognize their own family's output well above chance and that
  recognition correlates with preferring it — a systematic validity threat, not
  a residual. Because stylistic tells survive identifier stripping, each ballot
  records whether provenance was inferred and from what signal, and blinding is
  reported as bounded rather than claimed complete. (FR-035, FR-047, FR-048)

### Session 4 — Partitions, statistics, and campaign controls (2026-07-24)

- **Q: What unit must be disjoint across partitions?** → The **objective**. A
  versioned Partition Registry Entry binds the partition id, type, eligibility,
  an objective-set digest, frozen timestamp, and owning spec; an objective
  appearing in two partitions fails closed. (FR-013)
- **Q: Can a calibration pair bind the analysis plan?** → No — and this was a
  circular dependency, not a wording gap. Every pair was required to bind the
  frozen analysis plan before execution, but that plan freezes only *after*
  calibration, so calibration pairs were required to bind an artifact that
  cannot yet exist. Calibration pairs now bind a versioned calibration protocol
  carrying no margins, sample sizes, or terminal thresholds, and the frozen plan
  references it. (FR-037)
- **Q: What does the rerun cap count?** → Reruns, not attempts, per comparison
  pair; transient classification is made from arm-blind evidence **before**
  either arm's outcome is read, since classifying afterward is
  outcome-conditioned filtering; superseded pairs are retained immutably and
  excluded only as complete pairs. (FR-021)
- **Q: Two budgets exist — which is decision-bearing?** → The analysis-plan
  budget. The experiment-policy budget must equal it for qualification-eligible
  partitions and may be tighter only for calibration, because budget exhaustion
  enters the estimand at acceptance zero and an outcome-dependent budget would
  redefine it. (FR-038)
- **Q: Should reasoning tokens be a Pareto dimension?** → Recorded and reported,
  but **not** decision-bearing while the twin's frozen policy omits it. The
  field is disjoint from output tokens and is billed, so the exclusion is a
  stated limitation rather than a claim the cost is absent; adding it must be a
  joint cross-platform change. (FR-049)
- **Q: What multiplicity adjustment applies?** → Three separate families, not
  one global correction. The conjunctive floors and non-inferiority stage need
  no adjustment; the Pareto stage's disjunctive "better on at least one" half
  does and must say how; many ladders across candidates and roles form their own
  family. Cluster-adjusted variance is a precondition, not a correction — naive
  standard errors on paired clustered data break the test statistic itself, and
  no multiplicity control repairs that. The specific corrections freeze after
  calibration, as they do on the twin. (FR-050)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve all CAR-002 artifacts, identifiers, and snapshot evidence as immutable historical records and publish any CAR-003 capability evidence as additive successor artifacts.
- **FR-002**: The system MUST collect the pinned runtime catalog through an operator-run `claude -p --model <alias-or-id>` print-mode canary probe of the pinned Claude Code client as the **sole admitting runtime authority**, MUST admit effort support only by configuration acceptance on that same surface, and MUST record the command contract, client version and distribution, sanitized account and environment boundary, raw and parsed catalog digests, observed models, alias bindings, defaults, supported efforts, timestamps, and invalidation criteria.
- **FR-003**: The system MUST canonicalize source-admitted ordinary effort values only through an explicit evidence-backed normalization map and admit only model and effort tuples present in both the current official-source candidate ledger and the pinned-runtime-supported tuple set. Omitted, `inherit`, runtime-only, API-only, alias, aggregate, and topology-changing values MUST NOT become ordinary candidate efforts, and any source value without an evidence-backed mapping to the ordered ladder `low`, `medium`, `high`, `xhigh`, `max` MUST record `canonical_effort_unknown`.
- **FR-004**: The system MUST prevent subagent-frontmatter, model-picker, models-endpoint, visible-default, bundled-client, or any other diagnostic runtime observation from adding a model or effort absent from the official-source ledger or the refreshed pinned runtime catalog. Diagnostic observations MAY corroborate or invalidate an admitted tuple but MUST NEVER admit one. Because the catalog endpoint yields evidence only under API-key authentication, treating it as admitting would make freeze admission depend on an authentication mode FR-042 forbids requiring. Any disagreement between the admitting probe and a diagnostic observation MUST trigger recorded investigation or exclusion of the affected tuple and MUST NOT be logged and ignored.
- **FR-005**: The system MUST classify fast mode and any orchestration-topology-changing mode as a CAR-004 policy-level control rather than an ordinary per-agent effort candidate.
- **FR-006**: The system MUST maintain one shipped materialization contract in `speckit_pro_runner` that owns the exact rendered destination bytes and instruction/configuration digests consumed by both Layer 6 evidence and CAR-006 resolver behavior, with no parsed-only or divergent evaluation materializer.
- **FR-007**: The system MUST keep the existing dual-platform efficiency runner and the lexical quality scorer as non-release smoke surfaces and MUST NOT promote their historical results as route qualification evidence.
- **FR-008**: The system MUST execute installed-plugin agent policy or prove content-hash identity over the shipped frontmatter-plus-body against canonical materializer-owned destination bytes before accepting a requested-route treatment record; parsed-field equivalence or source-template equality MUST NOT satisfy this proof. The proof MUST be SHA-256 over the destination file's exact UTF-8 bytes read back from the destination path after write, with no normalization, re-serialization, newline translation, trailing-newline insertion, or key reordering, and MUST NOT be computed from an in-memory render buffer. The destination path MUST be verified separately rather than folded into the digest preimage.
- **FR-009**: The system MUST prove named agent, requested route, instruction hash, permitted tools, mutation contract, skills, MCP startup and schema evidence, parent controls, client, context, configured-route identity, authoritative route-change monitoring, and every mandatory CAR-002 treatment-profile observation before any outcome is scored; missing, unavailable, or undocumented mandatory evidence cannot support the claim. The mandatory observation set MUST be published as a versioned additive CAR-003 manifest naming each required field, because the frozen CAR-002 telemetry profile constrains only list cardinality and never enumerates the fields, leaving this requirement undecidable without one. Each mandatory field MUST carry a non-null observed value and a classification other than `unavailable`; an `unavailable` or null mandatory field MUST record failure code `missing mandatory telemetry`. Explicit nulls remain permitted only on fields the frozen schema declares nullable that are absent from the mandatory manifest.
- **FR-010**: The system MUST create a new immutable CAR-003 `execution_trace_id` record for every assigned attempt under the CAR-002 trace contract and append versioned experiment, score, and decision bundles through foreign-key-style IDs and digests without embedding or mutating archived or new treatment traces, and without extending the frozen `exactTreatmentReplay.outcome` shape.
- **FR-011**: The system MUST govern one twelve-role fixture corpus consisting of the eleven required-core roles that currently have shipped agent definitions plus the separate `autopilot-fast-helper` contract, which has no shipped agent definition until CAR-011 authors it.
- **FR-012**: The system MUST run only roles with admitted executable routes, MUST retain contracts for roles without a shipped agent definition without running them, and MUST analyze `autopilot-fast-helper` separately from required-core primary statistics. Each of the twelve role entries MUST carry independent `required_core` and `executable` booleans and MUST bind source digest, fixture digest, objective, permitted tools, mutation contract, expected artifacts, acceptance-oracle digest, and independent-review binding even when `executable=false`. Candidate route bindings MUST be absent for non-executable roles. A non-executable role MUST produce no score bundle and MUST NOT be counted as attrition. The role-corpus contract is authored by this spec mirroring the Codex twin's committed spec-scoped schema, which is a parity reference rather than a repo-level shared file.
- **FR-013**: Every fixture, experiment, score, and decision bundle MUST reference a registry-bound `partition_id` and closed partition type of `calibration`, `screening`, `selection`, `cohort_lock`, or `integrated_confirmation`; CAR-003 MUST consume only `qualification_eligible=false` calibration objectives and MUST fail closed on cross-partition reuse. Partition membership MUST be registered in a versioned Partition Registry Entry binding `partition_id`, `partition_type`, `qualification_eligible`, an objective-set digest, a frozen timestamp, and the owning spec. Disjointness is enforced at the **objective** level: an objective identifier appearing in more than one registered partition's objective set MUST fail closed with `failure_plane=partition`. `partition_type` and `qualification_eligible` MUST be immutable after freeze, and calibration MUST always carry `qualification_eligible=false`.
- **FR-014**: The system MUST run deterministic hard gates before semantic evaluation and fail closed when required gate evidence is missing or failing. Deterministic hard gates MUST use the closed set `role`, `safety`, `grounding`, `mutation`, `tool`, `output`, `acceptance`, each recording gate name, pass/fail, and an evidence digest. CAR-003 authors its own score-bundle contract mirroring the Codex twin's committed spec-scoped schema; that schema is a parity reference, not a repo-level shared file, and the two MUST stay logically identical. Semantic ballots MUST NOT be collected until every required gate has passed.
- **FR-015**: The system MUST require two independent candidate-blind rubric ballots for semantic scoring and a frozen third adjudicator when the required ballots disagree.
- **FR-016**: The system MUST preserve complete fixture, scorer, treatment, candidate, adjudicator, and infrastructure provenance for every score decision.
- **FR-017**: The system MUST apply absolute semantic and reliability floors before evaluating task-paired non-inferiority.
- **FR-018**: The system MUST evaluate prespecified task-paired, cluster-adjusted non-inferiority only after absolute semantic and reliability floors pass and MUST compare exactly eight decision-bearing dimensions — `input_tokens`, `cached_input_tokens`, `output_tokens`, duration, retries, compactions, acceptance, and terminal state — through Pareto dominance only after non-inferiority passes. This dimension set MUST be identical to the Codex twin's frozen Pareto policy: a candidate that is dominant on one platform's dimension set but mixed on the other's would yield different qualification outcomes from equivalent evidence, which is precisely the logical divergence the parity commitment forbids. Cache-write-by-TTL-class and cache-read breakdowns MUST be recorded in an additive diagnostic CAR-003 record and MUST NOT be Pareto dimensions, because the shared `rawTokenVector` is closed under `additionalProperties: false`, is byte-identical across worktrees, and carries no such fields.
- **FR-049**: `reasoning_output_tokens` MUST be recorded and reported for every attempt but MUST NOT be a decision-bearing Pareto dimension while the Codex twin's frozen Pareto policy omits it. This exclusion is a **known, stated limitation, not a claim that the cost is absent**: the field is disjoint from `output_tokens` in the shared contract — the shipped token accounting sums the two as separate additive terms — and published pricing bills reasoning tokens at the output-token rate, so a route whose cost concentrates in reasoning can appear less expensive than it is. Every qualification claim MUST report the reasoning-token totals alongside the dominance result so the omission is visible to a reviewer. Adding this dimension MUST be a joint cross-platform decision applied to both platforms in the same change, never unilaterally, and MUST account for the fact that each added dimension weakens dominance as a discriminator and raises the inconclusive rate. The comparison MUST bind a frozen workload-strata manifest, p95 raw-resource and p95-duration guardrails for applicable strata, and a cache-state isolation policy before either arm runs.
- **FR-019**: The system MUST return no qualification for a failed gate, tie, mixed dominance, incomplete evidence, or statistical uncertainty and MUST NOT force a weighted ranking. Published price data MAY be reported as diagnostic context only and MUST NOT be used as a selection coefficient or scalar weight.
- **FR-020**: The assigned-attempt estimand MUST retain candidate-caused failures, timeouts, cancellations, budget exhaustion, and abandoned work in their pairs with acceptance zero and MUST NOT use complete-case filtering.
- **FR-021**: The system MUST permit reruns only for independently preclassified transient harness failures, only as capped complete-pair reruns, never as one-arm reruns, and MUST return inconclusive after the cap when complete evidence is unavailable. The rerun cap MUST be prespecified per comparison pair and MUST count reruns rather than attempts. Transient-harness classification MUST be made from arm-blind evidence **before either arm's outcome is read**, because classifying after outcomes are visible is outcome-conditioned filtering. Superseded pairs MUST be retained immutably and marked superseded; exclusion MUST be complete-pair and arm-symmetric, and primary statistics MUST use exactly one terminal complete pair per assignment. Unknown or unclassifiable attrition MUST NOT be treated as candidate-caused, transient, or complete-case evidence; it MUST be recorded as an evidence-boundary failure that blocks completeness and returns inconclusive or no qualification unless resolved before terminal analysis.
- **FR-022**: The system MUST make live campaigns explicit, local, pinned, and budgeted while limiting the default suite to deterministic replay, contract tests, and statistical tests with zero live calls. Each live campaign budget MUST include separate ceilings for attempts, wall-clock duration, raw input tokens, cache-write tokens by TTL class, cache-read tokens, output tokens, candidate count, and confirmation-entry count.
- **FR-023**: The system MUST use calibration and historical non-release evidence only to freeze the numeric analysis plan before CAR-007 through CAR-010 observe outcomes.
- **FR-024**: The system MUST NOT create final preferred route policies, fallback route policies, installed defaults, aggregate identities, release claims, or outcome-bearing cohort campaign decisions.
- **FR-025**: The system MUST organize implementation review into three ordered slices, keeping roadmap Work Package A intact as the first slice, and MUST rerun the authoritative reviewability gate during planning.
- **FR-026**: The system MUST refresh generated runner metadata, payloads, hashes, and installed-cache proof fixtures whenever shipped runner source changes.
- **FR-027**: The system MUST commit only allowlisted sanitized capability-boundary evidence and MUST keep raw captures, account identifiers, authentication material, credentials, headers, cookies, private hostnames, absolute paths, repository remotes, prompts, responses, transcripts, and billing or plan identifiers in the operator-only content-addressed retention store; any non-allowlisted field MUST block publication rather than being silently stripped.
- **FR-028**: The system MUST NOT publish an authoritative successor freeze when the source/runtime intersection is empty, the source ledger or catalog is malformed or stale, required provenance is missing, collection authority is untrusted, sanitization or retention fails, identity or digest checks fail, or any CAR-002 artifact would be mutated.
- **FR-029**: Tuple exclusions MUST use a closed taxonomy comprising `source_not_admitted`, `effort_not_source_admitted`, `effort_source_not_admitted`, `canonical_effort_unknown`, `surface_evidence_incomplete`, `surface_disagreement`, `alias_repoint_unresolved`, `availability_not_proven`, and `topology_control_not_candidate_effort`; snapshot-publication authority failures MUST be recorded separately, and treatment, telemetry, fixture, scorer, and adjudication failures MUST use their later evidence bundles.
- **FR-030**: A requested route MUST be score-eligible only when the pre-score record has `treatment_disposition=proven`, installed-policy or content-hash-identical materialization proof, matching configured-route proof, complete mandatory observations, complete authoritative route-change monitoring, and no platform route change, misdelivery, treatment failure, or infrastructure failure; profile-only effective-treatment evidence MUST remain diagnostic and replay-only. `treatment_disposition` MUST use the closed taxonomy already defined by the shared treatment-record contract — `proven`, `unknown`, `non_scorable_rerouted`, `hard_fail` — rather than introducing a parallel vocabulary; that contract is byte-identical across the Claude and Codex worktrees, so reusing it preserves cross-platform parity. The frozen `exactTreatmentReplay.scorable` flag MUST be treated as necessary but not sufficient: it is derived solely from the record class and speaks only to platform-initiated route change, so `scorable=false` MUST force score-ineligibility while `scorable=true` MUST NOT by itself admit an outcome.
- **FR-031**: Platform-re-pointed attempts MUST remain immutable but non-scorable for the requested route, and different-agent, ambiguous, unapproved, or unidentifiable delivery MUST hard-fail treatment without scoring the observed destination. When several disqualifying conditions co-occur, the system MUST derive every condition independently and record all fired condition codes together in the `disposition_reasons` evidence array, and MUST NOT discard non-terminal causes. The single terminal `treatment_disposition` MUST be selected by the existing shared disposition-bucket precedence `hard_fail` > `non_scorable_rerouted` > `unknown` > `proven`. There MUST NOT be a condition-level tie-break that suppresses one co-firing code in favour of another; co-occurring causes are unioned, not ordered against each other. This precedence is specified here rather than left to implementation because independent Claude-side and Codex-side implementations must classify identical evidence identically.
- **FR-032**: Score bundles MUST reference `execution_trace_id`, trace digest, candidate route, agent contract, runtime capability snapshot, route resolution, experiment policy, treatment contract digest, and telemetry profile bindings; decision bundles MUST reference versioned score-bundle and analysis-plan IDs and digests. The trace digest MUST be SHA-256 over the canonical JSON serialization of the complete trace record using the existing CAR-002 canonicalization (sorted keys, minimal separators, UTF-8, no NaN). Bundle acceptance and replay MUST recompute and compare it; a mismatched or dangling reference MUST produce an additive invalidation with closed reason `trace_reference_integrity_failure` and MUST block the decision bundle rather than rewriting either artifact.
- **FR-033**: Every fixture MUST bind a versioned role/source digest, objective, evidence partition, permitted tools and mutation contract, expected artifacts, acceptance oracle, fixture digest, and independent validity review before any candidate may score against it. Every fixture, oracle, corpus, rubric, scorer, and adjudicator digest MUST be SHA-256 over the canonical JSON serialization (sorted keys, minimal separators, UTF-8, no NaN) of the artifact record excluding its own digest field, emitted as `sha256:<64 hex>`, and MUST be recomputed and compared at bundle acceptance and at replay. A mismatch MUST fail the fixture before candidate scoring. The shared contracts pin the digest format but not its preimage, which would otherwise leave deterministic replay unclosed.
- **FR-034**: The closed score-disposition, failure-plane, and invalidation-reason sets MUST be adopted verbatim from the Codex twin's committed contract — `score_disposition` = `accepted`, `gate_failed`, `non_scorable`, `invalidated`; `failure_plane` = `none`, `treatment`, `fixture`, `scorer`, `ballot`, `adjudication`, `candidate`, `infrastructure`, `evidence_boundary`, `partition`, `schema`; `invalidation_reason` = `none`, `fixture_changed`, `scorer_changed`, `rubric_changed`, `adjudicator_changed`, `treatment_changed`, `capability_changed`, `partition_changed`, `schema_changed`. Platform alias re-pointing MUST reuse the existing shared `service_reroute_requested_route_non_scorable` code recorded in the `disposition_reasons` array and MUST NOT coin a Claude-only member: the enclosing enumerations are closed under `additionalProperties: false`, and the treatment-record contract is verified byte-identical across both worktrees, so a unilateral addition would validate on one platform and fail on the other. The Claude-side wording "platform route change" and the Codex-side wording "service reroute" name one causal event; splitting them into two codes would fragment a category that downstream analysis treats as mutually exclusive and would force a crosswalk before pooled results could be compared. The capability-plane code `alias_repoint_unresolved` MUST stay at the capability-freeze plane and MUST NOT be repurposed here. Score bundles MUST use these closed score disposition, failure plane, failure code, and invalidation reason fields; fixture, scorer, rubric, adjudicator, treatment, capability, partition, or schema version changes MUST create additive invalidations without mutating prior bundles. The closed score failure-code taxonomy MUST include `none` only for `failure_plane=none` and MUST distinguish, at minimum, treatment misdelivery, platform route change, missing mandatory telemetry, invalid or stale fixture, invalid or stale scorer, missing or non-blind ballot, unresolved adjudication disagreement, invalid or stale adjudicator, candidate terminal outcome, infrastructure failure, evidence-boundary violation, partition violation, schema violation, and unclassifiable attrition.
- **FR-035**: Semantic scoring MUST require two distinct scorer identities and execution records, candidate-blind artifacts, a frozen rubric version/digest, current scorer calibration, and a frozen third adjudicator for every decision-affecting ballot disagreement. Each ballot MUST bind exactly one blinded-artifact digest as its sole scored input. Before ballot collection the blinded artifact MUST pass a mechanical leak check against freeze-bound model identities, aliases, effort values, agent frontmatter, and route identifiers; failure MUST record the existing `ballot_non_blind` code and block scoring.
- **FR-047**: A scorer or adjudicator MUST NOT be drawn from the same model family as any candidate it scores. Published evaluation research documents that model judges recognize their own family's output at rates well above chance and that this recognition correlates with preferring it, and separately that stylistic bias is the dominant judge-side bias — so same-family pairing is a systematic validity threat rather than a residual to be documented. Family exclusion MUST be static and declared in the frozen experiment policy so it carries no replay cost. Presentation order MUST be randomized under a seed recorded for replay, and the rubric MUST score only checkable properties. Artifact paraphrase or style normalization before scoring MUST NOT be used: it requires an additional non-frozen model call that breaks bit-exact replay and changes what is being scored.
- **FR-048**: Blinding enforcement MUST be recorded as bounded rather than claimed as complete. Identifier stripping cannot remove stylistic tells, so each ballot MUST additionally record whether the scorer inferred candidate provenance and from what signal, mirroring established blinded-review practice of measuring the residual instead of assuming blinding succeeded. A recorded inference MUST NOT silently invalidate the ballot, but the residual MUST be reported alongside any qualification claim and MUST NOT be described as full blinding.
- **FR-036**: Committed scorer evidence MUST be limited to sanitized schemas, manifests, deterministic fixtures, opaque scorer identities, rubric/scorer/adjudicator digests, anonymized ballots, score bundles, and evidence references; raw scoring prompts, responses, transcripts, personal identity mappings, and private runtime evidence MUST remain operator-only.
- **FR-037**: Before execution, each pair MUST immutably bind the comparison set, partition, candidate and comparator routes, role, fixture, task, instruction/configuration hashes, capability snapshot/freeze, route resolution, materialization, assigned order, pre-execution timestamp, experiment policy, and — for qualification-eligible partitions — the frozen analysis plan. Calibration-partition pairs MUST instead bind a versioned calibration protocol carrying no margins, sample sizes, or terminal thresholds, and the frozen analysis plan MUST reference that protocol as its calibration binding. This resolves an otherwise circular dependency: the analysis plan freezes only after calibration, so a calibration pair cannot bind a plan that does not yet exist. Later refreshes MUST create additive invalidations instead of rebinding, and each rerun MUST create new paired assignments linked to the original comparison set rather than superseding it.
- **FR-038**: One schema-governed, versioned analysis plan MUST freeze workload strata, p95 guardrails, margins, sample sizes, sample-size assumptions, power, alpha, multiplicity, racing and futility rules, attrition caps, campaign budgets, cache policy, and terminal rules after calibration and before any CAR-007 through CAR-010 cohort outcome is observed. The analysis-plan budget is authoritative. The experiment-policy budget MUST equal the frozen analysis-plan budget for qualification-eligible partitions and MAY be tighter only for calibration; any inequality MUST fail closed with `failure_plane=partition`. This matters because budget exhaustion enters the estimand at acceptance zero, so a per-campaign budget adjusted after results are visible would silently redefine the estimand.
- **FR-050**: The frozen multiplicity declaration MUST address three distinct families rather than a single global correction, because the decision ladder is not uniformly conjunctive. (a) The absolute floors and the non-inferiority stage are conjunctive: all must pass, so they control error at alpha without adjustment and without alpha relaxation, paying the cost in power. (b) The Pareto stage decomposes into two halves with opposite behavior — "no worse on every dimension" is conjunctive and becomes more conservative as dimensions grow, while "better on at least one dimension" is disjunctive and inflates the spurious-win rate with each added dimension unless controlled. The declaration MUST state how the disjunctive half is controlled; leaving the whole stage unadjusted under-protects. (c) Running many ladders across candidates, roles, and strata forms a separate family whose declaration MUST be stated independently of the within-ladder rule. The declaration MUST also record that cluster-adjusted variance estimation is a **precondition** rather than a multiplicity control: paired, clustered observations analyzed with naive standard errors inflate error through a mis-estimated test statistic, which no familywise or false-discovery correction can repair. The specific corrections freeze with the rest of the analysis plan after calibration; this requirement fixes what the declaration must cover, not which correction is chosen, and the Codex twin leaves the same value open for the same reason.
- **FR-039**: The system MUST close CAP-Q6 by detecting alias re-pointing from a mismatch between the observed model identity and the resolved qualified identity for a requested alias, MUST record every such event as platform behavior, and MUST NOT report it as a SpecKit Pro fallback. Detection MUST read five observables: the requested alias; the resolved identity bound by **CAR-003's own successor freeze** (explicitly disambiguated from the identically named run-time route-resolution field, and never read from the archived CAR-002 snapshot as authoritative); the run-observed identity from the per-model usage breakdown; the complete environment-override proof; and the pinned client version at both freeze time and run time. A mismatch MUST be attributed to the platform only when the requested route is unchanged, every local override is proven unset, and the client version is unchanged; a plugin-initiated route substitution MUST be classified as resolver fallback; and any mismatch with incomplete override proof, a changed client version, or an otherwise unattributable cause MUST record `alias_repoint_unresolved` and block admission.
- **FR-045**: The platform-attribution label MUST be carried in a new additive CAR-003 record, because the frozen CAR-002 `record_class` enumeration is closed and MUST NOT be extended. The attribution claim MUST be bounded to observed-identity divergence: a behavioral difference without an identity change is a separate diagnostic condition and MUST NOT be recorded as an alias re-point, since documented serving-infrastructure changes can alter observable behavior while the model identity and weights are unchanged. The elimination argument behind attribution MUST therefore be recorded as bounded by its enumerated cause set rather than as proof of platform causation.
- **FR-046**: The alias-re-pointing detector MUST be validated by a synthetic replay fixture that supplies a divergent observed identity below the live trigger path while environment overrides remain genuinely unset, so validation never requires setting the override that would violate the override-unset proof. If that replay path cannot be built, the detector MUST be recorded as unvalidated-in-band rather than reported as tested coverage.
- **FR-040**: The system MUST probe and record the full ordered supported-effort set from `low` through `max` for every role-eligible model, including `high` as the documented search origin, so that the within-model effort boundary search has a defined ladder.
- **FR-041**: The system MUST define versioned refresh triggers covering client change, catalog change, alias re-point, and source-ledger change, and MUST record for each trigger which evidence it invalidates and which evidence survives. All four triggers MUST invalidate freeze admission and every unexecuted binding derived from it, and MUST additively invalidate affected experiment, score, and decision bundles. Immutable execution traces, treatment records, and already-bound pairs MUST survive unchanged and MUST be marked invalidated rather than rebound. An alias re-point MUST additionally mark in-flight attempts for that alias non-scorable for the requested route, and a source-ledger change alone MUST NOT admit a tuple the pinned runtime never supported.
- **FR-042**: The system MUST treat subscription authentication as the supported scored path, MUST NOT require API-key authentication on any supported path, MUST record the authentication mode of every run, and MUST NOT produce any plan-based or billing-based claim. This relaxation MUST be recorded as a dated amendment to AC-2.19 so later cross-artifact analysis does not read it as specification-versus-PRD drift.
- **FR-043**: The system MUST treat the shared dual-platform smoke runner as jointly owned with the in-flight G56R-003 branch, MUST sync from the default branch before editing it, and MUST resolve any overlap by merge rather than rebase.
- **FR-044**: When the source/runtime intersection is empty or invalid, the system MUST record diagnostic collection evidence only, MUST NOT publish an authoritative CAR-003 successor freeze, MUST block qualification-capable execution, and MUST NOT reuse, rewrite, or promote the archived CAR-002 snapshot tuples as an active candidate set.

### Reviewability Notes *(if applicable)*

- Typed reviewability exceptions are not expected for this feature.
- Generated runner metadata, payloads, proof fixtures, `.process` files, PR bodies, and code fences are not valid provenance for reviewability exceptions.
- The accepted design concept fixes a single shipped materializer owned by the runner surface; planning must not introduce a second materializer or divergent evaluation/install path. This supersedes the roadmap Key Files entry that proposed the materializer under the test tree.
- Because the materializer now ships in plugin source, the roadmap's recorded `Production files: 0` budget for CAR-003 no longer holds and must be re-derived during planning.
- The accepted design concept keeps CAR-003 as a calibration and decision-platform spec only; final route-policy decisions remain reserved for later specs.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: seed/config, docs/process
- **Projected reviewable LOC**: 1,800-2,400 across three ordered review slices
- **Projected production files**: 6-10 (non-zero; supersedes the roadmap's recorded `Production files: 0`)
- **Projected total files**: 18-26
- **Budget result**: split required for implementation review
- **Split decision**: Keep one specification because freeze, treatment, scoring, and analysis contracts must be coherent, but implement and review as three ordered slices: capability freeze and materialized treatment trace (roadmap Work Package A, kept intact); governed corpus with hard gates and blinded scoring; calibration analysis plan with replayable decision bundles and generated metadata refresh.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Capability Snapshot**: A sanitized pinned-runtime collection record with client identity, opaque account or environment boundary, command contract, raw and parsed digests, observed models, alias bindings, defaults, supported efforts, timestamps, raw evidence reference, and invalidation criteria.
- **Capability Freeze**: A versioned non-empty admitted tuple set derived from the intersection of official-source candidates and pinned-runtime-supported tuples; invalid snapshot authority blocks publication rather than producing an empty authoritative freeze.
- **Candidate Tuple**: A canonical model and ordinary-effort pairing with a tuple-local admission decision and, when excluded, one or more closed capability exclusion reasons.
- **Alias Binding**: The mapping from a requested alias to a resolved qualified model identity, with the observed identity recorded per run so that re-pointing is detectable as platform behavior.
- **Treatment Record**: Immutable pre-score evidence proving canonical materialization, configured-route identity and controls, named-agent delivery, mandatory telemetry-profile observations, route-change monitoring and disposition, authentication mode, and every CAR-002 treatment field.
- **Execution Trace**: A replayable CAR-003 trace identified by `execution_trace_id` and trace digest under the existing CAR-002 trace contract; it exists for every assigned attempt regardless of score eligibility.
- **Role Fixture Contract**: A versioned role/source-bound objective, partition, tool and mutation contract, expected-artifact, acceptance-oracle, digest, and independent-validity contract, including roles without shipped agent definitions.
- **Fixture Corpus**: The full twelve-role corpus containing the eleven required core roles and `autopilot-fast-helper`.
- **Experiment Bundle**: Versioned assignment record that immutably binds partition, comparison set, candidate/comparator routes, role, fixture, task, configuration, capability, route-resolution, policy, and analysis-plan identities before execution.
- **Ballot**: Candidate-blind scorer judgment tied to one opaque scorer identity and execution record, frozen rubric and calibration versions, timestamp, and provenance.
- **Score Bundle**: Versioned hard-gate, two-ballot, adjudication, closed failure/invalidation, and provenance output that references but never embeds or mutates its immutable execution traces.
- **Analysis Plan**: Schema-governed, post-calibration, pre-cohort frozen numeric rules for floors, workload strata, p95 raw-resource and p95-duration guardrails, clustered paired non-inferiority, Pareto comparison, margins, sample size and assumptions, power, alpha, multiplicity, racing/futility, reruns, attrition, campaign budgets, cache-state isolation, terminal policy, estimand inclusion, and inconclusive outcomes.
- **Decision Bundle**: Replayable qualification result that references the frozen analysis plan and score-bundle versions/digests and records the terminal decision and reasons, including an explicit inconclusive terminal state, and carries no per-category weights, price coefficients, or scalar score field.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of CAR-002 artifact paths and IDs remain unchanged after CAR-003 artifacts are generated.
- **SC-002**: The successor freeze contains at least one admitted tuple, and every admitted tuple carries both official-source and pinned-runtime support evidence.
- **SC-003**: 100% of excluded candidate tuples include a machine-checkable exclusion reason from the closed taxonomy.
- **SC-004**: 100% of accepted score bundles reference a pre-score immutable treatment record with content-hash-identical materialization or installed-policy proof, configured-route proof, complete mandatory observations, authoritative route-change monitoring, `treatment_disposition=proven`, and no disqualifying re-point or treatment failure.
- **SC-005**: The fixture corpus contains exactly twelve valid role contracts: the eleven required core roles plus `autopilot-fast-helper`, reported separately from required-core statistics.
- **SC-006**: 100% of semantic score outcomes include two distinct independently executed candidate-blind ballots bound to one frozen rubric, and 100% of decision-affecting disagreements include a frozen third adjudicator record.
- **SC-007**: 100% of decision bundles apply semantic and reliability floors before paired cluster-adjusted non-inferiority, and non-inferiority before the resource comparison.
- **SC-008**: 100% of inconclusive or incomplete evidence paths produce no qualification.
- **SC-009**: 100% of candidate-caused failures, timeouts, cancellations, budget exhaustion events, and abandoned work are included in the estimand with acceptance zero.
- **SC-010**: 100% of approved transient harness reruns are complete-pair reruns under a documented cap, with zero one-arm reruns or complete-case substitutions.
- **SC-011**: Deterministic replay reconstructs the same terminal decisions from frozen experiment, score, analysis, and decision bundles on a clean checkout.
- **SC-012**: The numeric analysis plan is frozen before any CAR-007 through CAR-010 outcome-bearing cohort evidence is observed.
- **SC-013**: The planning reviewability gate records three ordered review slices and maps each slice to requirements, files, and verification evidence.
- **SC-014**: Every shipped runner source change has synchronized generated payloads, hashes, and installed-cache proofs before the phase is complete.
- **SC-015**: 100% of committed capability snapshots and replay fixtures pass deny-by-default sensitive-field inspection and contain only allowlisted sanitized boundary evidence.
- **SC-016**: 100% of empty, malformed, stale, untrusted, unsanitized, identity-mismatched, or digest-mismatched successor collections block authoritative freeze publication.
- **SC-017**: CAP-Q6 is closed: alias re-pointing is detected from observed-versus-resolved model ID, recorded as platform behavior, and never reported as SpecKit Pro fallback.
- **SC-018**: The full ordered effort set `low` through `max` is probed per role-eligible model, including `high` as the documented search origin.
- **SC-019**: Full default suite green with zero live calls; payload boundary clean.

## Assumptions

- The current official-source candidate ledger exists outside this specification and is the only source allowed to admit candidate model identities.
- The pinned runtime catalog is collected by operator probe from the pinned Claude Code client. CAR-002 recorded no documented catalog enumeration surface, so supported tuples are derived from observed probe results rather than an authoritative listing, and any other observation remains diagnostic only.
- Runtime discovery can remove or constrain candidates but cannot add new model identities beyond the official-source ledger.
- The eleven required core roles currently have shipped agent definitions; `autopilot-fast-helper` remains a contract-only role until CAR-011 authors it, so the twelve-role corpus is complete as contracts while only admitted executable routes are run.
- Disposable calibration objectives are available and separable from screening, selection, cohort-lock, and untouched integrated-confirmation objectives.
- Later specs own the excluded policy areas: CAR-004 policy controls and adaptive comparators, CAR-005 availability and fallback simulation, CAR-006 resolver and preflight behavior, and CAR-011 the `autopilot-fast-helper` addition.
- Live campaigns are operator-triggered, local, pinned, and budgeted; the default suite never runs live model campaigns.
- Historical smoke evidence can inform calibration-plan design but cannot substitute for CAR-003 treatment, scoring, or decision evidence.
- The exact numeric floors, margins, sample sizes, alpha, power, multiplicity adjustment, racing rule, and attrition caps are deliberately deferred to the frozen analysis plan produced after the calibration pilot; they are analysis-plan data, not specification literals.
- Calibrated scorer and adjudicator identities are bound in the scorer registry before the calibration pilot, once the successor capability freeze has settled which evaluators are available.
- Reviewers will evaluate implementation through the ordered slice structure declared in the reviewability budget.

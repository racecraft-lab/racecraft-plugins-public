# Feature Specification: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Feature Branch**: `g56r-003-evaluation-runner-scoring`

**Created**: 2026-07-24

**Status**: Draft

**Input**: User description: "G56R-003 builds an additive successor executable tuple freeze, exact-treatment evaluation runner, governed corpus, blinded scorer, and statistical analysis platform for later GPT-5.6 routing cohorts."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish Successor Capability Freeze (Priority: P1)

As a capability steward, I can collect the pinned Codex catalog and publish a versioned non-empty successor freeze containing only source-admitted, runtime-supported model and effort tuples, while preserving G56R-002 as immutable historical evidence.

**Why this priority**: Later evaluation and routing decisions require a trustworthy executable candidate set before any treatment, scoring, or analysis can be valid.

**Independent Test**: Can be fully tested by collecting the pinned runtime catalog, comparing it with the current official-source candidate ledger, and verifying that the new freeze is additive, non-empty, source-bound, and traceable without altering G56R-002 artifacts.

**Acceptance Scenarios**:

1. **Given** the archived G56R-002 zero set and the current pinned runtime catalog, **When** the steward generates the G56R-003 capability freeze, **Then** G56R-002 remains unchanged and a new versioned freeze contains only tuples admitted by both the official-source ledger and runtime support.
2. **Given** a model or effort appears in runtime discovery but not in the official-source candidate ledger, **When** the freeze is assembled, **Then** that tuple is excluded and the exclusion reason is recorded.
3. **Given** Ultra or another topology-changing mode appears in current capability evidence, **When** ordinary per-agent effort tuples are qualified, **Then** that mode is classified as a G56R-004 policy control and not admitted as an ordinary candidate effort.

---

### User Story 2 - Prove Exact Treatment Before Scoring (Priority: P1)

As an evaluation author, I can materialize and run the actual named-agent policy, prove the exact treatment each candidate received, and emit immutable replayable traces before any outcome is scored.

**Why this priority**: Semantic outcomes are not meaningful unless reviewers can prove that each candidate ran the intended named-agent route under the requested controls.

**Independent Test**: Can be fully tested by materializing an admitted executable route, running a disposable calibration objective, and verifying that all mandatory treatment evidence exists before any score bundle is accepted.

**Acceptance Scenarios**:

1. **Given** an admitted executable route and a governed calibration objective, **When** the runner executes the route, **Then** it records named agent, requested route, instruction hash, sandbox, permissions, skills, tools, MCP startup and schema evidence, parent controls, client, context, and all mandatory G56R-002 treatment fields before scoring begins.
2. **Given** a route cannot prove installed custom-agent policy or byte-identical canonical materialization, **When** the runner prepares the treatment record, **Then** the run is blocked from outcome scoring and classified as an infrastructure or treatment failure.
3. **Given** an existing G56R-002 trace contract, **When** G56R-003 creates execution evidence, **Then** each new `execution_trace_id` is immutable and later experiment, score, and decision bundles append to it without mutating archived evidence.

---

### User Story 3 - Score Governed Twelve-Role Corpus (Priority: P2)

As a scorer, I can evaluate one governed twelve-role corpus through deterministic hard gates and blinded semantic ballots, with explicit fixture, scorer, treatment, candidate, and infrastructure failure classes.

**Why this priority**: Cohort specs need a stable fixture and scoring contract that separates route quality from harness failures and avoids outcome leakage.

**Independent Test**: Can be fully tested by running the governed corpus against admitted executable routes and verifying that deterministic gates, blind ballots, adjudication, failure classes, and provenance are complete for every accepted score bundle.

**Acceptance Scenarios**:

1. **Given** the eleven required core roles and `autopilot-fast-helper`, **When** the fixture corpus is prepared, **Then** all twelve role contracts are present, the helper is identified separately from the required core, and only admitted executable routes are run.
2. **Given** a candidate run reaches semantic evaluation, **When** scoring starts, **Then** deterministic hard gates have already passed and two independent candidate-blind rubric ballots are collected with complete provenance.
3. **Given** two blinded ballots disagree according to the frozen rubric, **When** adjudication is required, **Then** a frozen third adjudicator resolves the outcome and its provenance is attached to the score bundle.
4. **Given** a fixture, scorer, treatment, candidate, or infrastructure failure occurs, **When** the run is classified, **Then** the failure class is explicit and downstream analysis uses the class according to the frozen estimand.

---

### User Story 4 - Freeze Calibration Analysis Plan (Priority: P3)

As an experiment owner, I can run a calibration-only pilot, freeze the numeric analysis plan, and replay paired decision behavior without creating final route policies or consuming final cohort evidence.

**Why this priority**: Later G56R-007 through G56R-010 cohorts need a precommitted decision platform that cannot adapt to their observed outcomes.

**Independent Test**: Can be fully tested by running only disposable calibration objectives, freezing the analysis plan, and replaying decisions from versioned bundles while proving no final cohort or integrated-confirmation partition was consumed.

**Acceptance Scenarios**:

1. **Given** calibration and historical non-release evidence, **When** the analysis plan is frozen, **Then** numeric floors, non-inferiority rules, Pareto inputs, rerun limits, and inconclusive handling are versioned before cohort outcomes are observed.
2. **Given** paired candidate outcomes, **When** the decision platform evaluates qualification, **Then** it applies absolute semantic and reliability floors, task-paired non-inferiority, and only then compares Pareto metrics.
3. **Given** evidence is incomplete, inconclusive, or outside the allowed calibration partition, **When** qualification is requested, **Then** the result is no qualification and no final preferred or fallback route policy is created.
4. **Given** a live campaign is requested, **When** campaign setup is validated, **Then** it is explicit, local, pinned, and budgeted, while default CI remains limited to deterministic replay and contract or statistical tests.

### Edge Cases

- The pinned runtime catalog is available but the official-source ledger contains no matching tuple.
- The official-source ledger admits a candidate that the pinned runtime does not support.
- The pinned runtime catalog contains visible defaults, aliases, aggregate identities, Ultra, or other topology-changing modes that must not become ordinary per-agent candidates.
- Catalog collection succeeds but omits required provenance such as client version, account or environment boundary, collection method, raw digest, timestamps, defaults, supported efforts, or invalidation criteria.
- The source/runtime intersection is empty or contains only hidden, alias, aggregate, or topology-control entries.
- A committed snapshot or replay fixture contains a non-allowlisted account, authentication, credential, raw-response, private-host, absolute-path, remote, billing, or plan field.
- A role has a governed fixture contract but no executable Codex TOML route yet.
- Installed custom-agent policy and canonical materialization differ in any byte or instruction hash relevant to treatment.
- MCP startup succeeds but schema evidence is incomplete or non-replayable.
- Parent controls, sandbox, permissions, tools, skills, or context evidence are missing after a run reaches terminal state.
- A trace reports profile-supported effective model and effort observations but lacks configured-route proof or authoritative reroute monitoring.
- A candidate fails, times out, is cancelled, exhausts budget, or is abandoned.
- A transient harness failure is identified after only one arm of a pair completed.
- A scorer ballot is missing, non-blind, stale relative to the frozen rubric, or lacks provenance.
- A fixture, rubric, scorer, adjudicator, or ballot is stale, invalid, identity-revealing, or no longer matches its bound version and digest.
- A committed scorer artifact contains raw prompts, responses, transcripts, personal scorer mappings, or other operator-private evidence.
- Calibration evidence overlaps with screening, selection, cohort-lock, or untouched integrated-confirmation objectives.
- Replay produces a different decision from the same versioned experiment, score, and analysis bundles.

## Clarifications

### Session 1 - Successor Freeze and Invalidation

- **Runtime authority**: Refreshed `codex debug models` output from the pinned
  Codex client is the sole runtime-catalog authority for freeze admission.
  App-server, hidden, picker, bundled, cache, and source-inventory observations
  are diagnostic or invalidation evidence only and cannot admit tuples.
- **Committed boundary evidence**: Git may contain only sanitized client
  identity, opaque account/environment boundary IDs, collection metadata,
  digests or content-addressed references, tuple decisions, and invalidation
  criteria. Raw captures and any identity-, authentication-, credential-, or
  private-environment-bearing fields remain in the operator-only G56R-002
  retention store. Publication fails closed when sanitization cannot prove the
  allowlist.
- **Effort normalization**: Source-admitted ordinary effort values are
  canonicalized only through an explicit evidence-backed map, such as
  `Extra High` to `xhigh`, before intersection with the pinned runtime.
  Runtime-only, API-only, alias, aggregate, inherited, Ultra, and
  topology-changing values cannot become ordinary candidate efforts.
- **Publication**: An empty or invalid intersection records diagnostic
  collection evidence but does not publish an authoritative G56R-003
  successor freeze and never reuses or rewrites the archived G56R-002 zero
  freeze.
- **Failure planes**: Tuple-local capability exclusions, snapshot-publication
  authority failures, and later treatment/scoring failures use separate
  closed taxonomies. Treatment delivery, telemetry, fixture, scorer, and
  adjudication failures never appear as capability-freeze exclusions.

### Session 2 - Materialization, Delivery, and Trace Joins

- **Score eligibility**: A requested route is score-eligible only when its
  pre-score treatment record proves installed policy or byte-identical
  canonical materialization, configured-route identity and controls, all
  mandatory telemetry-profile observations, complete authoritative reroute
  monitoring, `treatment_disposition=proven`, and no service reroute,
  misdelivery, treatment failure, or infrastructure failure. Profile-only
  effective-treatment evidence remains diagnostic and replay-only.
- **Canonical bytes**: The shipped runner materializer owns the exact rendered
  destination TOML bytes and instruction/configuration digests. Parsed TOML
  equivalence, source-template equality, or an evaluation-only materializer
  cannot prove installed-policy equivalence.
- **Nulls and missing evidence**: Every mandatory closed-profile path is
  present with an allowed observation state. Explicit nulls remain where the
  trace profile permits them, including pre-score `acceptance`; `missing`,
  `unavailable`, and `undocumented` observations cannot support treatment
  claims.
- **Reroute and misdelivery**: Every assigned attempt emits an immutable trace.
  Service-rerouted attempts are non-scorable for the requested route, while
  different-agent, ambiguous, unapproved, or unidentifiable delivery is a hard
  treatment failure. No path silently scores the observed destination.
- **Immutable joins**: Score bundles reference immutable trace IDs, digests,
  and objective-binding IDs; decision bundles reference versioned score-bundle
  and analysis-plan IDs/digests. Bundles never embed or mutate treatment
  traces.

### Session 3 - Corpus and Blinded Scoring

- **Role inventory**: The governed corpus contains eleven required core roles:
  nine roles with current executable Codex TOMLs plus non-executable fixture
  contracts for `consensus-synthesizer` and `gate-validator`.
  `autopilot-fast-helper` is the twelfth contract and remains outside
  required-core primary statistics. Non-executable contracts are never run
  until an admitted route exists.
- **Fixture validity**: Each versioned fixture records its role/source digest,
  objective, evidence partition, permitted tools and sandbox, expected
  artifacts, acceptance oracle, fixture digest, and independent validity
  review. Invalid or stale fixtures fail before candidate scoring.
- **Failure and invalidation**: Score outputs use closed disposition, failure
  plane/code, and invalidation reason fields. Candidate-caused outcomes remain
  in the estimand with acceptance zero; treatment, fixture, scorer, ballot,
  adjudication, infrastructure, evidence-boundary, partition, and schema
  failures remain distinguishable. Version changes invalidate affected
  bundles additively and never rewrite them.
- **Blinded ballots**: Semantic scoring requires two distinct scorer identities
  and execution records, candidate-blind artifacts, one frozen rubric
  version/digest, current calibration evidence, and a frozen third adjudicator
  for every decision-affecting disagreement.
- **Scorer evidence boundary**: Git contains only schemas, manifests,
  sanitized deterministic fixtures, opaque scorer IDs, rubric/scorer/
  adjudicator digests, anonymized ballots, score bundles, and evidence
  references. Raw prompts, responses, transcripts, personal scorer mappings,
  and all account/auth/private-runtime evidence remain operator-only under the
  Session 1 allowlist.

### Session 4 - Partitions, Statistics, and Campaign Controls

- **Closed partitions**: Every fixture, experiment, score, and decision bundle
  references a registry-bound `partition_id` and one closed partition type:
  `calibration`, `screening`, `selection`, `cohort_lock`, or
  `integrated_confirmation`. Calibration is always
  `qualification_eligible=false`; cross-partition reuse fails closed.
- **Immutable comparison assignment**: Before execution, each pair binds its
  comparison set, candidate/comparator routes, role, fixture, task,
  instruction/configuration hashes, capability snapshot/freeze, route
  resolution, experiment policy, and exactly one eligibility-selected
  authority: the frozen calibration protocol when
  `qualification_eligible=false`, or the frozen analysis plan when
  `qualification_eligible=true`. Later refreshes create additive invalidations
  and never rebind the pair.
- **Decision sequence**: Apply absolute semantic/reliability floors, then
  task-paired and cluster-adjusted non-inferiority against prespecified
  margins, then raw-vector Pareto dominance. A failed gate, tie, mixed
  dominance, or uncertainty is inconclusive and produces no qualification.
- **Assigned-attempt estimand**: Candidate-caused failure, timeout,
  cancellation, budget exhaustion, or abandonment remains in the assigned
  pair with acceptance zero. Only independently preclassified transient
  harness failures allow a capped complete-pair rerun; unresolved evidence
  after the cap is inconclusive and never complete-case filtered.
- **Freeze point**: Calibration may estimate feasibility, variance,
  missingness, scorer behavior, and sample-size inputs. One versioned plan
  freezes margins, sample sizes, power, alpha, multiplicity,
  racing/futility, attrition caps, budgets, and terminal rules after
  calibration and before any G56R-007 through G56R-010 outcome is observed.
  Numeric values are analysis-plan data, not mutable spec literals.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve all G56R-002 artifacts, identifiers, and zero-set evidence as immutable historical records and publish any G56R-003 capability evidence as additive successor artifacts.
- **FR-002**: The system MUST collect the pinned runtime catalog through refreshed `codex debug models` output and record the command contract, client version and distribution, executable or build digest, sanitized account and environment boundary, raw and parsed catalog digests, visible models, defaults, supported efforts, timestamps, and invalidation criteria.
- **FR-003**: The system MUST canonicalize source-admitted ordinary effort values only through an explicit evidence-backed normalization map and admit only model and effort tuples present in both the current official-source candidate ledger and the pinned-runtime-supported tuple set.
- **FR-004**: The system MUST prevent app-server, hidden, picker, bundled, cache, source-inventory, or other diagnostic runtime observations from adding a model or effort absent from the official-source ledger or the refreshed pinned runtime catalog.
- **FR-005**: The system MUST classify Ultra and any topology-changing mode as a later policy-level control rather than an ordinary per-agent effort candidate.
- **FR-006**: The system MUST maintain one shipped materialization contract that owns the exact rendered destination TOML bytes and instruction/configuration digests consumed by both Layer 6 evidence and G56R-006 resolver or installer behavior, with no parsed-only or divergent evaluation materializer.
- **FR-007**: The system MUST keep `run-efficiency-benchmarks.py` and `quality-scorer.py` as non-release smoke surfaces and MUST NOT promote their historical results as route qualification evidence.
- **FR-008**: The system MUST execute installed custom-agent policy or prove exact byte equality against canonical materializer-owned destination bytes before accepting a requested-route treatment record.
- **FR-009**: The system MUST prove named agent, requested route, instruction hash, sandbox, permissions, skills, tools, MCP startup and schema evidence, parent controls, client, context, configured-route identity, authoritative reroute monitoring, and every mandatory G56R-002 treatment-profile observation before any outcome is scored; missing, unavailable, or undocumented mandatory evidence cannot support the claim.
- **FR-010**: The system MUST create a new immutable G56R-003 `execution_trace_id` record for every assigned attempt under the G56R-002 trace contract and append versioned experiment, score, and decision bundles through foreign-key-style IDs and digests without embedding or mutating archived or new treatment traces.
- **FR-011**: The system MUST govern one twelve-role fixture corpus consisting of nine currently executable required-core Codex roles, non-executable required-core contracts for `consensus-synthesizer` and `gate-validator`, and the separate `autopilot-fast-helper` contract.
- **FR-012**: The system MUST run only roles with admitted executable routes, MUST retain contracts for currently non-executable roles without running them, and MUST analyze `autopilot-fast-helper` separately from required-core primary statistics.
- **FR-013**: Every fixture, experiment, score, and decision bundle MUST reference a registry-bound `partition_id` and closed partition type of `calibration`, `screening`, `selection`, `cohort_lock`, or `integrated_confirmation`; G56R-003 MUST consume only `qualification_eligible=false` calibration objectives and MUST fail closed on cross-partition reuse.
- **FR-014**: The system MUST run deterministic hard gates before semantic evaluation and fail closed when required gate evidence is missing or failing.
- **FR-015**: The system MUST require two independent candidate-blind rubric ballots for semantic scoring and a frozen third adjudicator when the required ballots disagree.
- **FR-016**: The system MUST preserve complete fixture, scorer, treatment, candidate, adjudicator, and infrastructure provenance for every score decision.
- **FR-017**: The system MUST apply absolute semantic and reliability floors before evaluating task-paired non-inferiority.
- **FR-018**: The system MUST evaluate prespecified task-paired, cluster-adjusted non-inferiority only after absolute semantic and reliability floors pass and MUST compare raw input tokens, cached-input tokens, output tokens, duration, retries, compactions, acceptance, and terminal state through Pareto dominance only after non-inferiority passes. The comparison MUST bind a frozen workload-strata manifest, p95 raw-resource and p95-duration guardrails for applicable strata, and a cache-state isolation policy before either arm runs.
- **FR-019**: The system MUST return no qualification for a failed gate, tie, mixed dominance, incomplete evidence, or statistical uncertainty and MUST NOT force a weighted ranking.
- **FR-020**: The assigned-attempt estimand MUST retain candidate-caused failures, timeouts, cancellations, budget exhaustion, and abandoned work in their pairs with acceptance zero and MUST NOT use complete-case filtering.
- **FR-021**: The system MUST permit reruns only for independently preclassified transient harness failures, only as capped complete-pair reruns, never as one-arm reruns, and MUST return inconclusive after the cap when complete evidence is unavailable. Unknown or unclassifiable attrition MUST NOT be treated as candidate-caused, transient, or complete-case evidence; it MUST be recorded as an evidence-boundary failure that blocks completeness and returns inconclusive or no qualification unless resolved before terminal analysis.
- **FR-022**: The system MUST make live campaigns explicit, local, pinned, and budgeted while limiting default CI to deterministic replay, contract tests, and statistical tests. Each live campaign budget MUST include separate ceilings for attempts, wall-clock duration, raw input tokens, cached-input tokens, output tokens, candidate count, and confirmation-entry count.
- **FR-023**: The system MUST use calibration and historical non-release evidence only to freeze the numeric analysis plan before G56R-007 through G56R-010 observe outcomes.
- **FR-024**: The system MUST NOT create final preferred route policies, fallback route policies, installed defaults, aggregate identities, release claims, or outcome-bearing cohort campaign decisions.
- **FR-025**: The system MUST organize implementation review into three ordered slices and rerun the authoritative reviewability gate during planning.
- **FR-026**: The system MUST refresh generated runner metadata, payloads, and proof fixtures whenever shipped runner source changes.
- **FR-027**: The system MUST commit only allowlisted sanitized capability-boundary evidence and MUST keep raw captures, account identifiers, authentication material, credentials, headers, cookies, private hostnames, absolute paths, repository remotes, prompts, responses, billing or plan identifiers, and raw live catalog bytes in the operator-only content-addressed retention store; any non-allowlisted field MUST block publication.
- **FR-028**: The system MUST NOT publish an authoritative successor freeze when the source/runtime intersection is empty, the source ledger or catalog is malformed or stale, required provenance is missing, collection authority is untrusted, sanitization or retention fails, identity or digest checks fail, or any G56R-002 artifact would be mutated.
- **FR-029**: Tuple exclusions MUST use the closed values `source_not_admitted`, `effort_not_source_admitted`, `effort_source_not_admitted`, `canonical_effort_unknown`, `surface_evidence_incomplete`, `surface_disagreement`, `hidden_state_disagreement`, `availability_not_proven`, or `topology_control_not_candidate_effort`; snapshot authority failures MUST be recorded separately, and treatment, telemetry, fixture, scorer, and adjudication failures MUST use their later evidence bundles.
- **FR-030**: A requested route MUST be score-eligible only when the pre-score record has `treatment_disposition=proven`, installed-policy or byte-identical materialization proof, matching configured-route proof, complete mandatory observations, complete authoritative reroute monitoring, and no service reroute, misdelivery, treatment failure, or infrastructure failure; profile-only effective-treatment evidence MUST remain diagnostic and replay-only.
- **FR-031**: Service-rerouted attempts MUST remain immutable but non-scorable for the requested route, and different-agent, ambiguous, unapproved, or unidentifiable delivery MUST hard-fail treatment without scoring the observed destination.
- **FR-032**: Score bundles MUST reference `execution_trace_id`, trace digest, candidate route, agent contract, runtime capability snapshot, route resolution, experiment policy, treatment contract digest, and telemetry profile bindings; decision bundles MUST reference versioned score-bundle and analysis-plan IDs and digests.
- **FR-033**: Every fixture MUST bind a versioned role/source digest, objective, evidence partition, permitted tools and sandbox, expected artifacts, acceptance oracle, fixture digest, and independent validity review before any candidate may score against it.
- **FR-034**: Score bundles MUST use closed score disposition, failure plane, failure code, and invalidation reason fields; fixture, scorer, rubric, adjudicator, treatment, capability, partition, or schema version changes MUST create additive invalidations without mutating prior bundles. The closed score failure-code taxonomy MUST include `none` only for `failure_plane=none` and MUST distinguish, at minimum, treatment misdelivery, service reroute, missing mandatory telemetry, invalid or stale fixture, invalid or stale scorer, missing or non-blind ballot, unresolved adjudication disagreement, invalid or stale adjudicator, candidate terminal outcome, infrastructure failure, evidence-boundary violation, partition violation, schema violation, and unclassifiable attrition.
- **FR-035**: Semantic scoring MUST require two distinct scorer identities and execution records, candidate-blind artifacts, a frozen rubric version/digest, current scorer calibration, and a frozen third adjudicator for every decision-affecting ballot disagreement.
- **FR-036**: Committed scorer evidence MUST be limited to sanitized schemas, manifests, deterministic fixtures, opaque scorer identities, rubric/scorer/adjudicator digests, anonymized ballots, score bundles, and evidence references; raw scoring prompts, responses, transcripts, personal identity mappings, and private runtime evidence MUST remain operator-only.
- **FR-037**: Before execution, each pair MUST immutably bind the comparison set, candidate and comparator routes, role, fixture, task, instruction/configuration hashes, capability snapshot/freeze, route resolution, experiment policy, and exactly one eligibility-selected authority: `calibration_protocol_binding` when `qualification_eligible=false`, or `analysis_plan_binding` when `qualification_eligible=true`; binding both, neither, or the wrong authority MUST fail closed, and later refreshes MUST create additive invalidations instead of rebinding.
- **FR-038**: Before calibration, one schema-governed, versioned calibration protocol MUST freeze the calibration partition and operational authority bindings without margins, sample sizes, quality floors, or terminal thresholds. After calibration and before any G56R-007 through G56R-010 cohort outcome is observed, one schema-governed, versioned analysis plan MUST bind that protocol and freeze workload strata, p95 guardrails, margins, sample sizes, sample-size assumptions, power, alpha, multiplicity, racing and futility rules, attrition caps, campaign budgets, cache policy, and terminal rules.

### Reviewability Notes *(if applicable)*

- Typed reviewability exceptions are not expected for this feature.
- Generated runner metadata, payloads, proof fixtures, `.process` files, PR bodies, and code fences are not valid provenance for reviewability exceptions.
- The accepted design concept fixes a single shipped materializer owned by the runner surface; planning must not introduce a second materializer or divergent evaluation/install path.
- The accepted design concept keeps G56R-003 as a calibration and decision-platform spec only; final route-policy decisions remain reserved for later specs.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: seed/config, docs/process
- **Projected reviewable LOC**: 1,800-2,400 across three ordered review slices
- **Projected production files**: 8-12
- **Projected total files**: 16-24
- **Budget result**: split required for implementation review
- **Split decision**: Keep one specification because freeze, treatment, scoring, and analysis contracts must be coherent, but implement and review as three ordered slices: capability freeze and materialized treatment trace; governed corpus with hard gates and blinded scoring; calibration analysis plan with replayable decision bundles and generated metadata refresh.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Capability Snapshot**: A sanitized pinned-runtime `codex debug models` collection record with client/build identity, opaque account or environment boundary, command contract, raw and parsed digests, visible models, defaults, supported efforts, timestamps, raw evidence reference, and invalidation criteria.
- **Capability Freeze**: A versioned non-empty admitted tuple set derived from the intersection of official-source candidates and pinned-runtime-supported tuples; invalid snapshot authority blocks publication rather than producing an empty authoritative freeze.
- **Candidate Tuple**: A canonical model and ordinary-effort pairing with a tuple-local admission decision and, when excluded, one or more closed capability exclusion reasons.
- **Treatment Record**: Immutable pre-score evidence proving canonical materialization, configured-route identity and controls, named-agent delivery, mandatory telemetry-profile observations, reroute monitoring and disposition, and every G56R-002 treatment field.
- **Execution Trace**: A replayable G56R-003 trace identified by `execution_trace_id` and trace digest under the existing G56R-002 trace contract; it exists for every assigned attempt regardless of score eligibility.
- **Role Fixture Contract**: A versioned role/source-bound objective, partition, tool/sandbox, expected-artifact, acceptance-oracle, digest, and independent-validity contract, including roles without executable Codex TOMLs.
- **Fixture Corpus**: The full twelve-role corpus containing the eleven required core roles and `autopilot-fast-helper`.
- **Calibration Protocol**: Versioned pre-calibration authority for the ineligible partition, pinned runtime, corpus/workload, scorer/rubric/adjudicator, cache policy, and independent review; it intentionally excludes margins, sample sizes, quality floors, and terminal thresholds.
- **Experiment Bundle**: Versioned assignment record that immutably binds partition, comparison set, candidate/comparator routes, role, fixture, task, configuration, capability, route-resolution, policy, and exactly one eligibility-selected calibration-protocol or analysis-plan identity before execution.
- **Ballot**: Candidate-blind scorer judgment tied to one opaque scorer identity and execution record, frozen rubric and calibration versions, timestamp, and provenance.
- **Score Bundle**: Versioned hard-gate, two-ballot, adjudication, closed failure/invalidation, and provenance output that references but never embeds or mutates its immutable execution traces.
- **Analysis Plan**: Schema-governed, post-calibration, pre-cohort frozen numeric rules that bind their source calibration protocol and define floors, workload strata, p95 raw-resource and p95-duration guardrails, clustered paired non-inferiority, Pareto comparison, margins, sample size and assumptions, power, alpha, multiplicity, racing/futility, reruns, attrition, campaign budgets, cache-state isolation, terminal policy, estimand inclusion, and inconclusive outcomes.
- **Decision Bundle**: Replayable qualification result that references the frozen analysis plan and score-bundle versions/digests and records the terminal decision and reasons.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of G56R-002 artifact paths and IDs remain unchanged after G56R-003 artifacts are generated.
- **SC-002**: The successor freeze contains at least one admitted tuple and every admitted tuple has both official-source and pinned-runtime support evidence.
- **SC-003**: 100% of excluded candidate tuples include a machine-checkable exclusion reason.
- **SC-004**: 100% of accepted score bundles reference a pre-score immutable treatment record with byte-identical materialization or installed-policy proof, configured-route proof, complete mandatory observations, authoritative reroute monitoring, `treatment_disposition=proven`, and no disqualifying reroute or treatment failure.
- **SC-005**: The fixture corpus contains exactly twelve valid role contracts: nine currently executable required-core roles, non-executable required-core contracts for `consensus-synthesizer` and `gate-validator`, and `autopilot-fast-helper` identified and reported separately.
- **SC-006**: 100% of semantic score outcomes include two distinct independently executed candidate-blind ballots bound to one frozen rubric, and 100% of decision-affecting disagreements include a frozen third adjudicator record.
- **SC-007**: 100% of decision bundles apply semantic and reliability floors before paired cluster-adjusted non-inferiority, and non-inferiority before raw-vector Pareto comparison.
- **SC-008**: 100% of inconclusive or incomplete evidence paths produce no qualification rather than a forced ranking.
- **SC-009**: 100% of candidate-caused failures, timeouts, cancellations, budget exhaustion events, and abandoned work are included in the estimand with acceptance zero.
- **SC-010**: 100% of approved transient harness reruns are complete-pair reruns under a documented cap, with zero one-arm reruns or complete-case substitutions accepted.
- **SC-011**: Deterministic replay reconstructs the same terminal decisions from frozen experiment, score, analysis, and decision bundles on a clean checkout.
- **SC-012**: The schema-governed numeric analysis plan, including workload strata, p95 guardrails, sample-size assumptions, multiplicity, racing/futility, attrition, budget, cache-isolation, and terminal rules, is frozen before any G56R-007 through G56R-010 outcome-bearing cohort evidence is observed.
- **SC-013**: The planning reviewability gate records three ordered review slices and maps each slice to requirements, files, and verification evidence.
- **SC-014**: Every shipped runner source change in scope has synchronized generated runner metadata, payloads, and proof fixtures before the phase is considered complete.
- **SC-015**: 100% of committed capability snapshots and replay fixtures pass deny-by-default sensitive-field inspection and contain only allowlisted sanitized boundary evidence.
- **SC-016**: 100% of empty, malformed, stale, untrusted, unsanitized, identity-mismatched, or digest-mismatched successor collections block authoritative freeze publication.

## Assumptions

- The current official-source candidate ledger exists outside this specification and is the only source allowed to admit candidate model identities.
- The pinned runtime catalog is collected from Codex 0.145.0 using refreshed `codex debug models` output; app-server, hidden, picker, bundled, cache, and source-inventory observations are diagnostic only.
- Runtime discovery can remove or constrain candidates but cannot add new model identities beyond the official-source ledger.
- Disposable calibration objectives are available and separable from screening, selection, cohort-lock, and untouched integrated-confirmation objectives.
- Later specs own the excluded policy areas: G56R-004 adaptive or unpinned controls, G56R-005 availability simulations, G56R-006 resolver or installer behavior, and G56R-011 integrated confirmation.
- Live campaigns are operator-triggered, local, pinned, and budgeted; default CI never runs live model campaigns.
- Historical smoke evidence can inform calibration-plan design but cannot substitute for G56R-003 treatment, scoring, or decision evidence.
- Reviewers will evaluate implementation through the ordered slice structure declared in the reviewability budget.

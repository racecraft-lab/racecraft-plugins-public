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

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve all CAR-002 artifacts, identifiers, and snapshot evidence as immutable historical records and publish any CAR-003 capability evidence as additive successor artifacts.
- **FR-002**: The system MUST collect the pinned runtime catalog through an operator-run probe of the pinned Claude Code client and record the command contract, client version and distribution, sanitized account and environment boundary, raw and parsed catalog digests, observed models, alias bindings, defaults, supported efforts, timestamps, and invalidation criteria.
- **FR-003**: The system MUST canonicalize source-admitted ordinary effort values only through an explicit evidence-backed normalization map and admit only model and effort tuples present in both the current official-source candidate ledger and the pinned-runtime-supported tuple set.
- **FR-004**: The system MUST prevent diagnostic runtime observations from adding a model or effort absent from the official-source ledger or the refreshed pinned runtime catalog.
- **FR-005**: The system MUST classify fast mode and any orchestration-topology-changing mode as a CAR-004 policy-level control rather than an ordinary per-agent effort candidate.
- **FR-006**: The system MUST maintain one shipped materialization contract in `speckit_pro_runner` that owns the exact rendered destination bytes and instruction/configuration digests consumed by both Layer 6 evidence and CAR-006 resolver behavior, with no parsed-only or divergent evaluation materializer.
- **FR-007**: The system MUST keep the existing dual-platform efficiency runner and the lexical quality scorer as non-release smoke surfaces and MUST NOT promote their historical results as route qualification evidence.
- **FR-008**: The system MUST execute installed-plugin agent policy or prove content-hash identity over the shipped frontmatter-plus-body against canonical materializer-owned destination bytes before accepting a requested-route treatment record; parsed-field equivalence or source-template equality MUST NOT satisfy this proof.
- **FR-009**: The system MUST prove named agent, requested route, instruction hash, permitted tools, mutation contract, skills, MCP startup and schema evidence, parent controls, client, context, configured-route identity, authoritative route-change monitoring, and every mandatory CAR-002 treatment-profile observation before any outcome is scored; missing, unavailable, or undocumented mandatory evidence cannot support the claim.
- **FR-010**: The system MUST create a new immutable CAR-003 `execution_trace_id` record for every assigned attempt under the CAR-002 trace contract and append versioned experiment, score, and decision bundles through foreign-key-style IDs and digests without embedding or mutating archived or new treatment traces, and without extending the frozen `exactTreatmentReplay.outcome` shape.
- **FR-011**: The system MUST govern one twelve-role fixture corpus consisting of the eleven required-core roles that currently have shipped agent definitions plus the separate `autopilot-fast-helper` contract, which has no shipped agent definition until CAR-011 authors it.
- **FR-012**: The system MUST run only roles with admitted executable routes, MUST retain contracts for roles without a shipped agent definition without running them, and MUST analyze `autopilot-fast-helper` separately from required-core primary statistics.
- **FR-013**: Every fixture, experiment, score, and decision bundle MUST reference a registry-bound `partition_id` and closed partition type of `calibration`, `screening`, `selection`, `cohort_lock`, or `integrated_confirmation`; CAR-003 MUST consume only `qualification_eligible=false` calibration objectives and MUST fail closed on cross-partition reuse.
- **FR-014**: The system MUST run deterministic hard gates before semantic evaluation and fail closed when required gate evidence is missing or failing.
- **FR-015**: The system MUST require two independent candidate-blind rubric ballots for semantic scoring and a frozen third adjudicator when the required ballots disagree.
- **FR-016**: The system MUST preserve complete fixture, scorer, treatment, candidate, adjudicator, and infrastructure provenance for every score decision.
- **FR-017**: The system MUST apply absolute semantic and reliability floors before evaluating task-paired non-inferiority.
- **FR-018**: The system MUST evaluate prespecified task-paired, cluster-adjusted non-inferiority only after absolute semantic and reliability floors pass and MUST compare the raw token vector (input, cache-write by TTL class, cache-read, output), duration, retries, compactions, acceptance, and terminal state through Pareto dominance only after non-inferiority passes. The comparison MUST bind a frozen workload-strata manifest, p95 raw-resource and p95-duration guardrails for applicable strata, and a cache-state isolation policy before either arm runs.
- **FR-019**: The system MUST return no qualification for a failed gate, tie, mixed dominance, incomplete evidence, or statistical uncertainty and MUST NOT force a weighted ranking. Published price data MAY be reported as diagnostic context only and MUST NOT be used as a selection coefficient or scalar weight.
- **FR-020**: The assigned-attempt estimand MUST retain candidate-caused failures, timeouts, cancellations, budget exhaustion, and abandoned work in their pairs with acceptance zero and MUST NOT use complete-case filtering.
- **FR-021**: The system MUST permit reruns only for independently preclassified transient harness failures, only as capped complete-pair reruns, never as one-arm reruns, and MUST return inconclusive after the cap when complete evidence is unavailable. Unknown or unclassifiable attrition MUST NOT be treated as candidate-caused, transient, or complete-case evidence; it MUST be recorded as an evidence-boundary failure that blocks completeness and returns inconclusive or no qualification unless resolved before terminal analysis.
- **FR-022**: The system MUST make live campaigns explicit, local, pinned, and budgeted while limiting the default suite to deterministic replay, contract tests, and statistical tests with zero live calls. Each live campaign budget MUST include separate ceilings for attempts, wall-clock duration, raw input tokens, cache-write tokens by TTL class, cache-read tokens, output tokens, candidate count, and confirmation-entry count.
- **FR-023**: The system MUST use calibration and historical non-release evidence only to freeze the numeric analysis plan before CAR-007 through CAR-010 observe outcomes.
- **FR-024**: The system MUST NOT create final preferred route policies, fallback route policies, installed defaults, aggregate identities, release claims, or outcome-bearing cohort campaign decisions.
- **FR-025**: The system MUST organize implementation review into three ordered slices, keeping roadmap Work Package A intact as the first slice, and MUST rerun the authoritative reviewability gate during planning.
- **FR-026**: The system MUST refresh generated runner metadata, payloads, hashes, and installed-cache proof fixtures whenever shipped runner source changes.
- **FR-027**: The system MUST commit only allowlisted sanitized capability-boundary evidence and MUST keep raw captures, account identifiers, authentication material, credentials, headers, cookies, private hostnames, absolute paths, repository remotes, prompts, responses, transcripts, and billing or plan identifiers in the operator-only content-addressed retention store; any non-allowlisted field MUST block publication rather than being silently stripped.
- **FR-028**: The system MUST NOT publish an authoritative successor freeze when the source/runtime intersection is empty, the source ledger or catalog is malformed or stale, required provenance is missing, collection authority is untrusted, sanitization or retention fails, identity or digest checks fail, or any CAR-002 artifact would be mutated.
- **FR-029**: Tuple exclusions MUST use a closed taxonomy comprising `source_not_admitted`, `effort_not_source_admitted`, `effort_source_not_admitted`, `canonical_effort_unknown`, `surface_evidence_incomplete`, `surface_disagreement`, `alias_repoint_unresolved`, `availability_not_proven`, and `topology_control_not_candidate_effort`; snapshot-publication authority failures MUST be recorded separately, and treatment, telemetry, fixture, scorer, and adjudication failures MUST use their later evidence bundles.
- **FR-030**: A requested route MUST be score-eligible only when the pre-score record has `treatment_disposition=proven`, installed-policy or content-hash-identical materialization proof, matching configured-route proof, complete mandatory observations, complete authoritative route-change monitoring, and no platform route change, misdelivery, treatment failure, or infrastructure failure; profile-only effective-treatment evidence MUST remain diagnostic and replay-only.
- **FR-031**: Platform-re-pointed attempts MUST remain immutable but non-scorable for the requested route, and different-agent, ambiguous, unapproved, or unidentifiable delivery MUST hard-fail treatment without scoring the observed destination.
- **FR-032**: Score bundles MUST reference `execution_trace_id`, trace digest, candidate route, agent contract, runtime capability snapshot, route resolution, experiment policy, treatment contract digest, and telemetry profile bindings; decision bundles MUST reference versioned score-bundle and analysis-plan IDs and digests.
- **FR-033**: Every fixture MUST bind a versioned role/source digest, objective, evidence partition, permitted tools and mutation contract, expected artifacts, acceptance oracle, fixture digest, and independent validity review before any candidate may score against it.
- **FR-034**: Score bundles MUST use closed score disposition, failure plane, failure code, and invalidation reason fields; fixture, scorer, rubric, adjudicator, treatment, capability, partition, or schema version changes MUST create additive invalidations without mutating prior bundles. The closed score failure-code taxonomy MUST include `none` only for `failure_plane=none` and MUST distinguish, at minimum, treatment misdelivery, platform route change, missing mandatory telemetry, invalid or stale fixture, invalid or stale scorer, missing or non-blind ballot, unresolved adjudication disagreement, invalid or stale adjudicator, candidate terminal outcome, infrastructure failure, evidence-boundary violation, partition violation, schema violation, and unclassifiable attrition.
- **FR-035**: Semantic scoring MUST require two distinct scorer identities and execution records, candidate-blind artifacts, a frozen rubric version/digest, current scorer calibration, and a frozen third adjudicator for every decision-affecting ballot disagreement.
- **FR-036**: Committed scorer evidence MUST be limited to sanitized schemas, manifests, deterministic fixtures, opaque scorer identities, rubric/scorer/adjudicator digests, anonymized ballots, score bundles, and evidence references; raw scoring prompts, responses, transcripts, personal identity mappings, and private runtime evidence MUST remain operator-only.
- **FR-037**: Before execution, each pair MUST immutably bind the comparison set, candidate and comparator routes, role, fixture, task, instruction/configuration hashes, capability snapshot/freeze, route resolution, experiment policy, and analysis plan; later refreshes MUST create additive invalidations instead of rebinding.
- **FR-038**: One schema-governed, versioned analysis plan MUST freeze workload strata, p95 guardrails, margins, sample sizes, sample-size assumptions, power, alpha, multiplicity, racing and futility rules, attrition caps, campaign budgets, cache policy, and terminal rules after calibration and before any CAR-007 through CAR-010 cohort outcome is observed.
- **FR-039**: The system MUST close CAP-Q6 by detecting alias re-pointing from a mismatch between the observed model identity and the resolved qualified identity for a requested alias, MUST record every such event as platform behavior, and MUST NOT report it as a SpecKit Pro fallback.
- **FR-040**: The system MUST probe and record the full ordered supported-effort set from `low` through `max` for every role-eligible model, including `high` as the documented search origin, so that the within-model effort boundary search has a defined ladder.
- **FR-041**: The system MUST define versioned refresh triggers covering client change, catalog change, alias re-point, and source-ledger change, and MUST record for each trigger which evidence it invalidates and which evidence survives.
- **FR-042**: The system MUST treat subscription authentication as the supported scored path, MUST NOT require API-key authentication on any supported path, MUST record the authentication mode of every run, and MUST NOT produce any plan-based or billing-based claim. This relaxation MUST be recorded as a dated amendment to AC-2.19 so later cross-artifact analysis does not read it as specification-versus-PRD drift.
- **FR-043**: The system MUST treat the shared dual-platform smoke runner as jointly owned with the in-flight G56R-003 branch, MUST sync from the default branch before editing it, and MUST resolve any overlap by merge rather than rebase.

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

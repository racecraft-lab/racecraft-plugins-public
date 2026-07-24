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
- A role has a governed fixture contract but no executable Codex TOML route yet.
- Installed custom-agent policy and canonical materialization differ in any byte or instruction hash relevant to treatment.
- MCP startup succeeds but schema evidence is incomplete or non-replayable.
- Parent controls, sandbox, permissions, tools, skills, or context evidence are missing after a run reaches terminal state.
- A candidate fails, times out, is cancelled, exhausts budget, or is abandoned.
- A transient harness failure is identified after only one arm of a pair completed.
- A scorer ballot is missing, non-blind, stale relative to the frozen rubric, or lacks provenance.
- Calibration evidence overlaps with screening, selection, cohort-lock, or untouched integrated-confirmation objectives.
- Replay produces a different decision from the same versioned experiment, score, and analysis bundles.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve all G56R-002 artifacts, identifiers, and zero-set evidence as immutable historical records and publish any G56R-003 capability evidence as additive successor artifacts.
- **FR-002**: The system MUST record client version, account and environment boundary, collection method, raw catalog digest, visible models, defaults, supported efforts, timestamps, and invalidation criteria for the pinned runtime catalog snapshot.
- **FR-003**: The system MUST admit only model and effort tuples that are present in both the current official-source candidate ledger and the pinned-runtime-supported tuple set.
- **FR-004**: The system MUST prevent runtime discovery from adding a model or effort that is absent from the official-source candidate ledger.
- **FR-005**: The system MUST classify Ultra and any topology-changing mode as a later policy-level control rather than an ordinary per-agent effort candidate.
- **FR-006**: The system MUST maintain one shipped materialization contract consumed by both Layer 6 benchmark evidence and G56R-006 resolver or installer behavior, with no divergent evaluation-only materializer.
- **FR-007**: The system MUST keep `run-efficiency-benchmarks.py` and `quality-scorer.py` as non-release smoke surfaces and MUST NOT promote their historical results as route qualification evidence.
- **FR-008**: The system MUST execute installed custom-agent policy or byte-identical canonical materialization before accepting a treatment record.
- **FR-009**: The system MUST prove named agent, requested route, instruction hash, sandbox, permissions, skills, tools, MCP startup and schema evidence, parent controls, client, context, and every mandatory G56R-002 treatment field before any outcome is scored.
- **FR-010**: The system MUST create new immutable G56R-003 `execution_trace_id` records under the G56R-002 trace contract and append versioned experiment, score, and decision bundles without mutating archived treatment evidence or newly created traces.
- **FR-011**: The system MUST govern one twelve-role fixture corpus consisting of the eleven required core roles plus `autopilot-fast-helper`.
- **FR-012**: The system MUST create fixture contracts for roles that do not yet have executable Codex TOMLs, run only admitted executable routes, and analyze `autopilot-fast-helper` separately from the required core roles.
- **FR-013**: The system MUST keep calibration, screening, selection, cohort-lock, and untouched integrated-confirmation objectives disjoint, and G56R-003 MUST consume only disposable calibration objectives.
- **FR-014**: The system MUST run deterministic hard gates before semantic evaluation and fail closed when required gate evidence is missing or failing.
- **FR-015**: The system MUST require two independent candidate-blind rubric ballots for semantic scoring and a frozen third adjudicator when the required ballots disagree.
- **FR-016**: The system MUST preserve complete fixture, scorer, treatment, candidate, adjudicator, and infrastructure provenance for every score decision.
- **FR-017**: The system MUST apply absolute semantic and reliability floors before evaluating task-paired non-inferiority.
- **FR-018**: The system MUST compare Pareto metrics only after floor and paired non-inferiority rules pass, using raw input tokens, cached-input tokens, output tokens, duration, retries, compactions, acceptance, and terminal state.
- **FR-019**: The system MUST return no qualification for inconclusive evidence and MUST NOT force a weighted ranking.
- **FR-020**: The system MUST keep candidate-caused failures, timeouts, cancellations, budget exhaustion, and abandoned work in the estimand with acceptance zero.
- **FR-021**: The system MUST permit reruns only for independently preclassified transient harness failures, only as capped complete-pair reruns, and never as one-arm reruns.
- **FR-022**: The system MUST make live campaigns explicit, local, pinned, and budgeted while limiting default CI to deterministic replay, contract tests, and statistical tests.
- **FR-023**: The system MUST use calibration and historical non-release evidence only to freeze the numeric analysis plan before G56R-007 through G56R-010 observe outcomes.
- **FR-024**: The system MUST NOT create final preferred route policies, fallback route policies, installed defaults, aggregate identities, release claims, or outcome-bearing cohort campaign decisions.
- **FR-025**: The system MUST organize implementation review into three ordered slices and rerun the authoritative reviewability gate during planning.
- **FR-026**: The system MUST refresh generated runner metadata, payloads, and proof fixtures whenever shipped runner source changes.

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

- **Capability Snapshot**: A pinned runtime catalog collection record with client, account or environment, collection method, raw digest, visible models, defaults, supported efforts, timestamps, and invalidation criteria.
- **Capability Freeze**: A versioned admitted tuple set derived from the intersection of official-source candidates and pinned-runtime-supported tuples.
- **Candidate Tuple**: A model and effort pairing that may be excluded, admitted, run, scored, or qualified according to source, runtime, and analysis evidence.
- **Treatment Record**: Immutable pre-score evidence proving the named agent, requested route, instruction hash, sandbox, permissions, skills, tools, MCP startup and schema, parent controls, client, context, and G56R-002 treatment fields.
- **Execution Trace**: A replayable G56R-003 trace identified by `execution_trace_id` under the existing G56R-002 trace contract.
- **Role Fixture Contract**: The governed objective and acceptance contract for one role in the twelve-role corpus, including roles without executable Codex TOMLs.
- **Fixture Corpus**: The full twelve-role corpus containing the eleven required core roles and `autopilot-fast-helper`.
- **Experiment Bundle**: Versioned campaign input, route, corpus, treatment, and run metadata for replay.
- **Ballot**: Candidate-blind scorer judgment tied to a frozen rubric, scorer identity or role, timestamp, and provenance.
- **Score Bundle**: Versioned hard-gate, semantic-ballot, adjudication, failure-class, and provenance output for a candidate pair or run.
- **Analysis Plan**: Frozen numeric rules for floors, paired non-inferiority, Pareto comparison, reruns, estimand inclusion, and inconclusive outcomes.
- **Decision Bundle**: Replayable qualification result that records applied analysis-plan version, evidence inputs, terminal decision, and reasons.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of G56R-002 artifact paths and IDs remain unchanged after G56R-003 artifacts are generated.
- **SC-002**: The successor freeze contains at least one admitted tuple and every admitted tuple has both official-source and pinned-runtime support evidence.
- **SC-003**: 100% of excluded candidate tuples include a machine-checkable exclusion reason.
- **SC-004**: 100% of accepted score bundles reference a treatment record created before scoring and containing all mandatory treatment fields.
- **SC-005**: The fixture corpus contains exactly twelve role contracts, with eleven required core roles and `autopilot-fast-helper` identified and reported separately.
- **SC-006**: 100% of semantic score outcomes include two independent candidate-blind ballots, and 100% of qualifying disagreements include a frozen third adjudicator record.
- **SC-007**: 100% of decision bundles apply semantic and reliability floors before paired non-inferiority, and paired non-inferiority before Pareto comparison.
- **SC-008**: 100% of inconclusive or incomplete evidence paths produce no qualification rather than a forced ranking.
- **SC-009**: 100% of candidate-caused failures, timeouts, cancellations, budget exhaustion events, and abandoned work are included in the estimand with acceptance zero.
- **SC-010**: 100% of approved transient harness reruns are complete-pair reruns under a documented cap, with zero one-arm reruns accepted.
- **SC-011**: Deterministic replay reconstructs the same terminal decisions from frozen experiment, score, analysis, and decision bundles on a clean checkout.
- **SC-012**: The numeric analysis plan is frozen before any G56R-007 through G56R-010 outcome-bearing cohort evidence is observed.
- **SC-013**: The planning reviewability gate records three ordered review slices and maps each slice to requirements, files, and verification evidence.
- **SC-014**: Every shipped runner source change in scope has synchronized generated runner metadata, payloads, and proof fixtures before the phase is considered complete.

## Assumptions

- The current official-source candidate ledger exists outside this specification and is the only source allowed to admit candidate model identities.
- The pinned runtime catalog is collected from Codex 0.145.0 using the documented local catalog inspection path described in the workflow prompt.
- Runtime discovery can remove or constrain candidates but cannot add new model identities beyond the official-source ledger.
- Disposable calibration objectives are available and separable from screening, selection, cohort-lock, and untouched integrated-confirmation objectives.
- Later specs own the excluded policy areas: G56R-004 adaptive or unpinned controls, G56R-005 availability simulations, G56R-006 resolver or installer behavior, and G56R-011 integrated confirmation.
- Live campaigns are operator-triggered, local, pinned, and budgeted; default CI never runs live model campaigns.
- Historical smoke evidence can inform calibration-plan design but cannot substitute for G56R-003 treatment, scoring, or decision evidence.
- Reviewers will evaluate implementation through the ordered slice structure declared in the reviewability budget.

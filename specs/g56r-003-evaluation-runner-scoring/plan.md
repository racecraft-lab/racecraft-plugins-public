# Implementation Plan: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Branch**: `g56r-003-evaluation-runner-scoring` | **Date**: 2026-07-24
**Spec**: `specs/g56r-003-evaluation-runner-scoring/spec.md`
**Design authority**: `docs/ai/specs/.process/G56R-003-design-concept.md`

## Summary

Build the G56R-003 qualification platform as three ordered review slices:

1. publish an additive successor capability freeze, materialize exact Codex
   agent policy from one shipped implementation, and prove treatment through
   new immutable traces under the existing G56R-002 contract;
2. govern the twelve-role corpus and issue fail-closed deterministic and
   blinded score bundles; and
3. freeze the experiment and statistical contracts, replay decisions
   deterministically, and run only an explicit calibration partition.

The plan preserves all G56R-002 evidence, keeps the legacy smoke runner
non-release, and leaves final route policies and cohort outcomes to G56R-007
through G56R-010.

## Technical Context

**Language/Version**: Python 3.11+ standard library
**Primary source**: `speckit-pro/speckit_pro_runner/`
**Evaluation adapters**: `tests/speckit-pro/layer6-efficiency/`
**Unit tests**: `tests/speckit-pro/unit/`
**Contract format**: JSON Schema 2020-12 plus deterministic JSON fixtures
**Storage**: immutable, content-addressed JSON files and Git object bindings
**CI boundary**: deterministic contracts, replay, scorer, and statistical tests
**Local-only boundary**: opt-in pinned live calibration campaigns
**Primary surface**: harness/adapter
**Performance goal**: deterministic validation of a frozen replay bundle with
p95 runtime under 10 seconds on a normal developer checkout; live campaign
performance is recorded under frozen budgets and guardrails, not optimized by
this feature
**Runtime constraints**: no active Bash or `jq`; structured parsers,
`pathlib`, argument arrays, `shell=False`, deterministic UTF-8 I/O
**Privacy constraints**: Git receives only the sanitized allowlist; raw
catalog, prompt, response, identity, account, auth, billing, host, path, and
remote evidence remains operator-only
**Scale**: twelve role contracts, only admitted executable routes run; helper
statistics stay separate from the eleven-role required-core population

## Constitution Check

### Before design

| Principle | Result | Design proof |
|---|---|---|
| I. Plugin Structure | Pass | Shipped behavior remains under `speckit-pro/`; repository-only evaluation and tests remain under `tests/speckit-pro/`. |
| II. Cross-Platform Runtime | Pass | All new active tooling is Python 3.11 standard library with structured JSON and no shell implementation. |
| III. Semantic Versioning | Pass | Source manifests are not hand-edited; release-please owns version changes. |
| IV. Test Coverage | Pass | Every new helper and schema has Layer 4 unit coverage and the default suite remains the final gate. |
| V. Conventional Commits | Pass | Each slice uses a conventional commit and the final PR title is validated by the release-readiness gate. |
| VI. KISS/YAGNI | Pass | One materializer, thin evaluation adapter, seven bounded contract families, and no cross-vendor or future-policy abstraction. |

### After design

No constitutional exception is required. The design reuses the G56R-002 trace,
content-addressed retention, and capability helpers. New code is introduced
only where G56R-003 has a distinct source-of-truth responsibility: canonical
materialization, governed scoring, or frozen experiment analysis.

## Source Ownership

| Concern | Authored source of truth | Consumer | Non-authoritative or generated surface |
|---|---|---|---|
| Exact Codex agent TOML bytes and digests | `speckit-pro/speckit_pro_runner/agent_materialization.py` | Layer 6 adapter now; G56R-006 resolver/installer later imports the same module | Installed cache and distribution payload copies |
| Pinned runtime catalog collection and successor admission | existing G56R-002 capability helpers plus `codex_successor_capability.py` | qualification adapter and replay | raw operator-only catalog capture |
| Treatment truth | existing G56R-002 `treatment-record.schema.json` and trace helpers | G56R-003 score eligibility and replay | no copied or extended treatment record |
| Qualification entry point | `tests/speckit-pro/layer6-efficiency/run-codex-qualification.py` | local operators and deterministic tests | legacy `run-efficiency-benchmarks.py` remains smoke-only |
| Corpus contract | `role-corpus.schema.json` plus `corpus-manifest.json` | scoring and cohort specs | raw scoring prompts and responses |
| Score and adjudication | `score-bundle.schema.json` plus scoring module | analysis/replay | anonymized ballots are evidence, not authority |
| Calibration protocol | `calibration-protocol.schema.json` and frozen protocol data | calibration experiment policy and later analysis plan | margins, sample sizes, quality floors, and terminal thresholds |
| Calibration completion | `calibration-completion.schema.json` and content-addressed completion data | analysis-plan freeze | margins, sample sizes, quality floors, terminal thresholds, and plan-bound decisions |
| Analysis plan | `analysis-plan.schema.json` and frozen analysis-plan data | qualification-eligible experiment policy, cohort specs, and replay | calibration reports and draft calculations |
| Experiment policy and decision | `experiment-policy.schema.json`, `analysis-decision.schema.json`, frozen protocol/plan data | cohort specs and replay | reports are projections of immutable bundles |
| Runner trust and install payloads | authored runner Python files | installed plugin | manifest hashes, payloads, installed-cache proofs, and release evidence generated by `scripts/refresh-release-artifacts.py` |

### Canonical materializer seam

Layer 6 imports:

```text
speckit_pro_runner.agent_materialization.materialize_agent_policy
```

G56R-006 MUST import the same function and data types. It may add resolver and
installer orchestration, but it must not copy rendering logic or compare parsed
TOML as a substitute for byte equality. The materializer returns exact UTF-8
destination bytes plus instruction and configuration digests. File writes stay
with the caller so the pure materializer is replayable.

## Immutable Data Flow

```text
G56R-001 source ledger
  --current_ledger_digest-->
pinned runtime catalog collection
  --raw_catalog_digest + parsed_catalog_digest-->
G56R-003 successor capability snapshot/freeze
  --runtime_capability_snapshot_id + candidate_freeze_id-->
frozen calibration protocol
  --calibration_protocol_id + calibration_protocol_digest-->
comparison assignment
  --comparison_set_id + experiment_policy_id + calibration_protocol_id-->
canonical materialization
  --destination_bytes_digest + instruction_digest + configuration_digest-->
new G56R-003 execution trace under the G56R-002 treatment contract
  --execution_trace_id + treatment_record_digest-->
score/adjudication bundle
  --score_bundle_id + score_bundle_digest-->
analysis output and terminal decision
  --decision_bundle_id + decision_bundle_digest-->
sanitized deterministic replay/report
```

Every arrow is a required ID-and-digest join. Downstream bundles reference
upstream artifacts; they never embed or mutate them. A changed upstream digest
creates a new downstream object or an additive invalidation record.

## Evidence Boundaries

### Raw-byte owners

| Boundary | Byte owner | Committed proof | Operator-only retention |
|---|---|---|---|
| runtime catalog | pinned `codex debug models` collector | sanitized parsed fields, opaque boundary ID, command/client metadata, raw and parsed digests | raw stdout/stderr and environment-bearing capture |
| agent policy | shipped materializer | exact destination-byte digest, instruction/configuration digests, source binding | none unless live execution adds private data |
| execution | G56R-002 trace helpers | sanitized trace and immutable trace digest | raw live transcript, headers, session/account data |
| scoring | score bundle builder | opaque scorer IDs, scorer/rubric/adjudicator digests, anonymized ballots and evidence refs | raw prompts/responses/transcripts and personal identity map |
| release | refresh script | runner manifest/checksum, payload and installed-cache proofs | none |

Publication uses a deny-by-default allowlist. Any unexpected field, absolute
path, hostname, repository remote, account or authentication datum, credential,
cookie, header, billing or plan identifier, raw prompt, raw response, or raw
catalog byte blocks publication. Redaction is not accepted as proof when the
scrubber cannot classify a field.

## Score Failure Code Taxonomy

Score bundles use a closed failure-plane and failure-code pair. The
`failure_code` value is `none` only when `failure_plane=none`; every other
plane has enumerated codes so reviewers can distinguish treatment delivery
errors, fixture validity errors, scorer and ballot defects, adjudication
failures, candidate terminal outcomes, infrastructure failures, evidence
boundary violations, partition violations, and schema violations without
free-form prose.

Minimum required codes are:

- treatment: `treatment_misdelivery`, `service_reroute`,
  `mandatory_telemetry_missing`, `treatment_infrastructure_failure`;
- fixture: `fixture_invalid`, `fixture_stale`,
  `fixture_partition_invalid`, `fixture_oracle_invalid`;
- scorer: `scorer_invalid`, `scorer_stale`, `scorer_calibration_missing`;
- ballot: `ballot_missing`, `ballot_non_blind`,
  `ballot_provenance_incomplete`, `ballot_rubric_stale`;
- adjudication: `adjudication_disagreement_unresolved`,
  `adjudicator_invalid`, `adjudicator_stale`,
  `adjudicator_reused_primary_scorer`;
- candidate: `candidate_failed`, `candidate_timed_out`,
  `candidate_cancelled`, `candidate_budget_exhausted`,
  `candidate_abandoned`;
- infrastructure: `transient_harness_failure`,
  `infrastructure_failure`;
- evidence_boundary: `unclassifiable_attrition`,
  `sensitive_evidence_violation`, `required_evidence_missing`;
- partition: `partition_mismatch`, `partition_not_eligible`,
  `cross_partition_reuse`;
- schema: `schema_invalid`, `binding_digest_mismatch`.

Unknown or unclassifiable attrition is not a candidate-caused outcome and is
not rerun-eligible unless it is independently reclassified before the rerun
decision as a transient harness failure. It blocks completeness, counts against
the frozen attrition cap, and produces inconclusive or no qualification at the
terminal decision boundary.

## Versioning and Additive Invalidation

The following changes issue new versioned artifacts and invalidate affected
descendants without rewriting prior evidence:

| Changed authority | New artifact | Invalidated descendants |
|---|---|---|
| source ledger, runtime catalog, client/build, identity boundary, or normalization map | successor snapshot/freeze | route assignments, traces, scores, decisions |
| materializer source or agent source bytes | materialization digest | unexecuted assignments and dependent scores |
| fixture source, oracle, tools, sandbox, or independent review | fixture version/digest | ballots, score bundles, decisions |
| rubric or scorer calibration | rubric/scorer version | semantic ballots, adjudications, scores, decisions |
| adjudicator identity or calibration | adjudicator version | affected adjudications, scores, decisions |
| treatment contract/profile or trace digest | trace binding | scores and decisions |
| experiment policy, partition registry, comparator binding, or analysis plan | policy/plan version | analysis outputs and decisions |

Invalidation records use closed reasons in the relevant contract. A stale
artifact remains readable for audit but cannot satisfy a current decision.

## Evidence Partitions

The registry permits exactly `calibration`, `screening`, `selection`,
`cohort_lock`, and `integrated_confirmation`. Each fixture, experiment, score,
analysis, and decision binds one `partition_id` and `partition_type`.

G56R-003 may execute only `calibration` with
`qualification_eligible=false`. The validator rejects mixed partition IDs,
cross-partition fixture reuse, and any attempt to emit a qualification from
calibration. G56R-007 through G56R-010 create their own outcome-bearing
partitions after the analysis plan is frozen. Integrated confirmation remains
untouched.

## Ordered Review Slices

### Slice 1 — Capability, materialization, and trace

**Requirements**: FR-001 through FR-010, FR-026 through FR-031, FR-039 through
FR-046, FR-051, FR-057; SC-001 through SC-004, SC-014 through SC-020.

**Implementation**:

- add the pure shipped materializer and exact-byte tests;
- reuse G56R-002 capability collection, retention, trace, and replay helpers;
- add the pinned-catalog successor snapshot/freeze contract and publication
  validator;
- record each model's actual ordered ordinary-effort ladder, detect alias
  re-points from observed-versus-resolved identity, and freeze refresh effects;
- observe and validate the pre-execution environment, authentication mode, and
  Ultra-off admission precondition without mutating operator settings;
- add the thin durable qualification adapter;
- emit a new trace for every assigned attempt and hard-block scoring unless
  treatment is proven.

**Independent verification**:

- unit tests for materialization bytes and G56R-006 importability;
- successor publication positive/negative fixtures;
- synthetic alias-re-point replay and environment-divergence matrices;
- source inspection proving that no harness or shipped payload enables or
  disables Ultra;
- G56R-002 immutability snapshot;
- treatment/misdelivery/reroute/null-state replay tests;
- runner release-artifact refresh and drift check.

**Reviewability**: Reviewable LOC: 720. Production Files: 4. Total Files: 15.
Primary Surface: harness/adapter.

### Slice 2 — Corpus and blinded scoring

**Requirements**: FR-011 through FR-016, FR-032 through FR-036, FR-047 through
FR-049; SC-005, SC-006, SC-015, SC-021, SC-024.

**Implementation**:

- publish exactly twelve role contracts: the nine executable core TOML roles,
  non-executable `consensus-synthesizer` and `gate-validator`, and separate
  `autopilot-fast-helper`;
- validate role/source digest, objective, partition, tools, sandbox, expected
  artifacts, oracle, fixture digest, and independent review before execution;
- run deterministic hard gates before semantic scoring;
- accept only two distinct, current, candidate-blind ballots under one frozen
  rubric and use a frozen third adjudicator for decision-affecting
  disagreement;
- exclude same-family scorers, report every blinding-inference signal, record
  reasoning tokens diagnostically, and require observed per-arm cache roots;
- issue immutable score bundles with closed failure and invalidation fields.

**Independent verification**:

- exact corpus membership and helper-separation tests;
- non-executable role skip tests;
- fixture staleness, blindness, identity, calibration, ballot, and
  adjudication negative matrices;
- committed-evidence sensitive-field inspection;
- deterministic score bundle replay.

**Reviewability**: Reviewable LOC: 760. Production Files: 5. Total Files: 15.
Primary Surface: harness/adapter.

### Slice 3 — Experiment policy, statistics, and calibration

**Requirements**: FR-013, FR-017 through FR-025, FR-032, FR-037, FR-038,
FR-050, FR-052 through FR-056, FR-058; SC-007 through SC-013, SC-022,
SC-023, SC-025.

**Implementation**:

- bind calibration candidate/comparator pairs before execution with immutable
  policy, snapshot, materialization, fixture, task, partition, and calibration
  protocol IDs;
- preserve the assigned-attempt estimand and allow only capped complete-pair
  reruns for independently classified transient harness failures;
- freeze a workload manifest with pre-treatment strata, long-horizon flags,
  target weights, unknown handling, minimum unique tasks, p95 raw-resource and
  p95-duration guardrails, and cache-state isolation before either arm runs;
- apply semantic/reliability floors, paired cluster-adjusted
  non-inferiority, then raw-vector Pareto dominance;
- return inconclusive/no qualification for any failed gate, tie, mixed
  dominance, missing evidence, or uncertainty;
- expose one explicit local budgeted calibration command with attempt,
  wall-clock, raw-input-token, cached-input-token, output-token,
  candidate-count, and confirmation-entry ceilings under the pre-calibration
  protocol; validate the complete closed policy/protocol contract and
  immutable comparison joins; publish plan-free content-addressed calibration
  completion; then freeze the schema-governed numeric analysis plan with
  bindings to that protocol and completion before later cohort outcomes;
- keep CI deterministic and prohibit final route-policy output.

**Independent verification**:

- contract tests for immutable pair assignment and partition isolation;
- replay fixtures for every terminal/attrition/rerun path;
- statistical golden cases for floors, non-inferiority, clusters, Pareto,
  uncertainty, and multiplicity;
- closed-plan checks for all three multiplicity families, full p95 guardrail
  declarations, per-stratum unique-task floors, and sequential-look content;
- workload-strata, p95 guardrail, budget-ceiling, and cache-leakage negative
  fixtures;
- clean-checkout replay equality;
- calibration report carries validated completion evidence proving
  `qualification_eligible=false` without a plan-bound decision.

**Reviewability**: Reviewable LOC: 760. Production Files: 5. Total Files: 16.
Primary Surface: harness/adapter.

## Statistical Decision Order

1. Validate all bindings, partition membership, workload-strata manifest,
   cache-state isolation policy, campaign budget ceilings, treatment
   eligibility, deterministic hard gates, score provenance, complete
   terminal-state classification, attrition classification, and completeness.
2. Apply frozen absolute semantic and reliability floors.
3. Evaluate the task-paired, role-cluster-adjusted non-inferiority confidence
   bound against the frozen margin, workload strata, sample-size assumptions,
   and multiplicity rule.
4. Compare the raw vector of input tokens, cached-input tokens, output tokens,
   duration, retries, compactions, acceptance, and terminal state only after
   steps 1–3 pass and only within the frozen cache-state policy.
5. Emit qualification only for proven Pareto dominance under a
   qualification-eligible later partition. Calibration can emit only
   `calibration_complete`, `inconclusive`, or `invalid`.

Candidate-caused failure, timeout, cancellation, budget exhaustion, and
abandonment remain assigned outcomes with acceptance zero. Only an
independently preclassified transient harness failure can trigger a full-pair
rerun, and only up to the frozen cap.

Campaign budget validation fails closed unless the experiment policy and
analysis plan both bind explicit ceilings for attempts, wall-clock duration,
raw input tokens, cached-input tokens, output tokens, candidate count, and
confirmation-entry count. A missing p95 guardrail, missing workload stratum, or
post-treatment cache-policy change makes the affected comparison incomplete
and therefore inconclusive.

## Default-Suite Budget

The manifest-driven deterministic default suite has a frozen wall-clock ceiling
of 600 seconds on a normal developer checkout and makes zero live model calls.
The 2026-07-26 pre-commit baseline completed in 303.33 seconds with 3251/3251
tests passing. Replay fixtures remain bounded, and the existing frozen-bundle
replay p95 target remains under ten seconds. Work that cannot fit this ceiling
belongs behind the explicit operator-only live path.

## Generated-Artifact Contract

Authored changes are the Python sources, schemas, fixtures, tests, and
specification artifacts named in this plan. When any shipped runner source
changes:

1. run `python3 scripts/refresh-release-artifacts.py`;
2. review the generated runner manifest/checksum, distribution payloads,
   installed-cache fixtures/proofs, and release evidence as one change set;
3. run `python3 scripts/refresh-release-artifacts.py --check`;
4. do not hand-edit any generated result.

The refresh script is the sole regeneration owner. Generated artifacts are
required for the slice that changes shipped source, but they do not count as
authored production design.

## Project Structure

```text
speckit-pro/speckit_pro_runner/
└── agent_materialization.py                 # shipped source; reused by G56R-006

tests/speckit-pro/layer6-efficiency/
├── run-codex-qualification.py               # thin qualification adapter
├── contracts/
│   ├── successor-capability-freeze.schema.json
│   ├── calibration-protocol.schema.json
│   ├── calibration-completion.schema.json
│   ├── experiment-policy.schema.json
│   ├── role-corpus.schema.json
│   ├── score-bundle.schema.json
│   ├── analysis-plan.schema.json
│   └── analysis-decision.schema.json
├── fixtures-codex/
│   ├── corpus-manifest.json
│   └── <twelve-role-contracts>/
└── lib/
    ├── codex_successor_capability.py
    ├── qualification_contracts.py
    ├── qualification_corpus.py
    ├── qualification_scoring.py
    ├── qualification_statistics.py
    └── qualification_replay.py

tests/speckit-pro/unit/
├── test-agent-materialization.py
├── test-codex-successor-capability.py
├── test-codex-qualification-contracts.py
├── test-codex-qualification-corpus.py
├── test-codex-qualification-scoring.py
└── test-codex-qualification-statistics.py
```

## Declared File Operations

The plan-phase estimator reads this bounded authored-file inventory. Generated
payloads and proof artifacts are intentionally excluded.

- NEW speckit-pro/speckit_pro_runner/agent_materialization.py
- NEW tests/speckit-pro/layer6-efficiency/run-codex-qualification.py
- NEW tests/speckit-pro/layer6-efficiency/lib/codex_successor_capability.py
- NEW tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py
- NEW tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py
- NEW tests/speckit-pro/layer6-efficiency/lib/qualification_environment.py
- NEW tests/speckit-pro/layer6-efficiency/lib/qualification_scoring.py
- NEW tests/speckit-pro/layer6-efficiency/lib/qualification_statistics.py
- NEW tests/speckit-pro/layer6-efficiency/lib/qualification_replay.py
- NEW tests/speckit-pro/layer6-efficiency/contracts/successor-capability-freeze.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/calibration-protocol.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/calibration-completion.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/experiment-policy.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/environment-contract.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/role-corpus.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/score-bundle.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/analysis-plan.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts/analysis-decision.schema.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-codex/corpus-manifest.json
- NEW tests/speckit-pro/unit/test-agent-materialization.py
- NEW tests/speckit-pro/unit/test-codex-successor-capability.py
- NEW tests/speckit-pro/unit/test-codex-qualification-contracts.py
- NEW tests/speckit-pro/unit/test-codex-qualification-corpus.py
- NEW tests/speckit-pro/unit/test-codex-qualification-environment.py
- NEW tests/speckit-pro/unit/test-codex-qualification-scoring.py
- NEW tests/speckit-pro/unit/test-codex-qualification-statistics.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256

Role fixture files are a repeated data family owned by
`corpus-manifest.json`; Tasks must enumerate their concrete paths. Generated
manifest/checksum rows above are refresh outputs, not hand edits.

## Reviewability Decision

The largest individual slice is estimated at Reviewable LOC: 760, Production
Files: 5, Total Files: 16, Primary Surface: harness/adapter. The accepted
decomposition is three ordered slices because the combined platform crosses
capability/treatment, scoring, and statistics seams. Each slice has an
independent fail-closed verification boundary and no slice requires a copied
materializer or mutation of G56R-002 evidence.

## Complexity Tracking

No constitutional violation or extra abstraction is accepted.

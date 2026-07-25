# Data Model: G56R-003 Evaluation Platform

## Conventions

- Every immutable object has a stable logical ID and a canonical
  `sha256:<64 lowercase hex>` digest.
- Canonical JSON uses UTF-8, sorted keys, deterministic separators, and no
  environment-specific values.
- References carry both the logical ID and expected digest.
- A version change creates a new object. Prior objects remain readable.
- Additive invalidation records identify stale objects without modifying them.
- All evidence-bearing entities bind exactly one registered partition.

## Identifier Graph

```text
source_snapshot_id + current_ledger_digest
  └─ runtime_catalog_collection_id + raw_catalog_digest + parsed_catalog_digest
      └─ runtime_capability_snapshot_id
          └─ candidate_freeze_id
              └─ comparison_set_id
                  └─ assignment_id
                      ├─ materialization_id
                      ├─ fixture_id
                      ├─ experiment_policy_id
                      ├─ analysis_plan_id
                      └─ execution_trace_id
                          └─ score_bundle_id
                              └─ analysis_output_id
                                  └─ decision_bundle_id
```

The graph is append-only. Every child validates the ID and digest of each
parent before construction.

## Entity: Runtime Catalog Collection

**Purpose**: Capture the pinned runtime admission authority without committing
raw private catalog bytes.

**Required fields**:

- `runtime_catalog_collection_id`
- `schema_version`
- `collection_command`
- `client_version`, `distribution`, `client_build_digest`
- opaque `account_boundary_id` and `environment_boundary_id`
- `collected_at`, `valid_until`, `invalidation_triggers`
- `raw_catalog_digest`, `parsed_catalog_digest`
- normalized visible models, defaults, and supported ordinary efforts
- operator-only `raw_evidence_ref`
- sanitization result and allowlist version

**Validation**:

- collection command is the pinned refreshed catalog command;
- raw evidence ref is content-addressed and not a local path;
- diagnostic surfaces cannot add tuples;
- stale, malformed, untrusted, unsanitized, identity-mismatched, or
  digest-mismatched collections cannot publish a snapshot.

## Entity: Runtime Capability Snapshot

**Purpose**: Immutable sanitized projection of one valid collection.

**Required fields**:

- `runtime_capability_snapshot_id`, `snapshot_digest`
- collection ID/digest
- source ledger snapshot ID/digest
- effort normalization map ID/digest
- normalized runtime tuples
- diagnostic observations
- publication authority status

**State**:

```text
collected -> validated -> sanitized -> authoritative
     |          |             |
     +----------+-------------+-> rejected
```

Only `authoritative` snapshots can feed a successor freeze.

## Entity: Successor Capability Freeze

**Purpose**: Additive non-empty intersection of source-admitted and
runtime-supported ordinary tuples.

**Required fields**:

- `candidate_freeze_id`, `freeze_digest`, `schema_version`
- `supersedes_candidate_freeze_id`
- G56R-002 historical freeze ID/digest binding
- source ledger and runtime snapshot ID/digest bindings
- normalization map ID/digest
- non-empty admitted candidate route tuples
- excluded tuple decisions using the closed capability taxonomy
- snapshot authority failures in a separate collection
- published timestamp and invalidation triggers

**Invariants**:

- no G56R-002 artifact changes;
- every admitted tuple exists in both authorities;
- Ultra/topology controls never appear as ordinary efforts;
- empty or invalid intersections do not publish an authoritative freeze.

## Entity: Canonical Materialization

**Purpose**: Prove the exact bytes used by evaluation and later installation.

**Required fields**:

- `materialization_id`, `materializer_version`
- agent source path relative to repository and source digest
- candidate route and parent-control inputs
- exact `destination_bytes_digest`
- `instruction_digest`, `configuration_digest`
- materializer source digest

**Invariants**:

- exact bytes are produced by the shipped materializer;
- caller writes bytes without transformation;
- parsed TOML equality is never accepted as byte proof;
- G56R-006 uses the same import path.

## Entity: Partition Registry Entry

**Required fields**:

- `partition_id`
- `partition_type`: `calibration`, `screening`, `selection`, `cohort_lock`, or
  `integrated_confirmation`
- `qualification_eligible`
- objective-set digest
- created/frozen timestamps
- owning spec

**Invariants**:

- calibration always has `qualification_eligible=false`;
- G56R-003 may consume only calibration;
- objective membership is disjoint;
- type and eligibility cannot change after freeze.

## Entity: Role Fixture Contract

**Required fields**:

- `fixture_id`, `fixture_version`, `fixture_digest`
- `role_id`, role source path/digest, `required_core`
- `executable`, admitted route bindings when executable
- objective ID/digest and partition ID/type
- permitted tools, sandbox, and mutation policy
- expected artifact contracts
- deterministic acceptance oracle
- independent review ID, reviewer digest, review timestamp
- invalidation triggers

**States**:

```text
draft -> independently_reviewed -> valid -> assigned
  |              |                  |
  +--------------+------------------+-> invalid
```

A non-executable contract may be `valid` but cannot become `assigned`.

## Entity: Corpus Manifest

**Required fields**:

- `corpus_id`, version, digest
- exactly twelve fixture references
- eleven `required_core=true`
- one helper role `autopilot-fast-helper` with `required_core=false`
- exactly nine executable core roles
- non-executable `consensus-synthesizer` and `gate-validator`
- partition registry binding

**Invariants**:

- membership changes issue a new corpus;
- helper results are excluded from required-core primary statistics;
- only admitted executable routes are scheduled.

## Entity: Experiment Policy

**Required fields**:

- `experiment_policy_id`, version, digest
- partition ID/type and eligibility
- candidate freeze and corpus ID/digest bindings
- analysis plan ID/digest
- comparison-set generation policy
- randomization/order policy
- attempt budget and time limits
- terminal-state disposition map
- transient harness failure classifier
- complete-pair rerun cap
- live/local/CI execution mode constraints

**Invariants**:

- one-arm rerun is prohibited;
- candidate terminal failures remain outcomes;
- default CI mode is replay-only;
- G56R-003 live mode requires calibration partition and explicit budget.

## Entity: Comparison Set and Assignment

**Required fields**:

- `comparison_set_id`, `assignment_id`
- candidate and comparator route IDs
- role, fixture, objective, task, and partition bindings
- source instruction and configuration hashes
- candidate freeze and runtime snapshot bindings
- route-resolution binding
- materialization binding
- experiment policy and analysis plan bindings
- assigned order and pre-execution timestamp

**Invariants**:

- all bindings exist before execution;
- refreshes create invalidations, not rebinding;
- each rerun creates new paired assignments linked to the original set.

## Entity: Execution Trace

**Authority**: Existing G56R-002 treatment contract.

**G56R-003 binding requirements**:

- one new immutable `execution_trace_id` for every assigned attempt;
- comparison set and assignment IDs;
- configured route and authoritative reroute-monitoring proof;
- canonical materialization ID/digests or installed-policy proof;
- all mandatory treatment-profile observations;
- `treatment_disposition`;
- explicit terminal event;
- pre-score `acceptance` remains permitted null under the existing contract.

**Score eligibility**:

```text
proven treatment
AND installed policy or exact materialization bytes
AND matching configured route
AND complete mandatory observations
AND complete authoritative reroute monitoring
AND no reroute, misdelivery, treatment failure, or infrastructure failure
```

Profile-only effective treatment is diagnostic/replay-only. Service reroute is
immutable but non-scorable. Different-agent, ambiguous, unapproved, or
unidentifiable delivery hard-fails treatment.

## Entity: Deterministic Gate Result

**Required fields**:

- gate result ID/digest
- trace and fixture bindings
- closed gate name
- pass/fail
- sanitized evidence refs
- evaluator version/digest

Every required gate must pass before ballots are accepted.

## Entity: Semantic Ballot

**Required fields**:

- `ballot_id`, version, digest
- score bundle draft ID
- blinded artifact digest
- opaque scorer ID and scorer version/digest
- distinct scorer execution ID
- scorer calibration batch ID/digest and currentness proof
- rubric ID/version/digest
- criterion scores and sanitized rationale
- submitted timestamp

**Invariants**:

- ballot inputs contain no candidate route/model/effort identity;
- required ballots use distinct scorer identities and executions;
- raw prompts/responses/transcripts and personal mappings are operator-only.

## Entity: Adjudication

**Required fields**:

- `adjudication_id`, version, digest
- disagreeing ballot ID/digest bindings
- disagreement rule that triggered adjudication
- frozen third adjudicator ID/version/digest
- calibration/currentness binding
- resolved outcome and sanitized rationale

Adjudication is required for every decision-affecting disagreement and cannot
reuse either ballot scorer as the third adjudicator.

## Entity: Score Bundle

**Required fields**:

- `score_bundle_id`, version, digest
- assignment and partition bindings
- execution trace ID/digest
- candidate route and agent contract bindings
- runtime snapshot/freeze and route-resolution bindings
- experiment policy and treatment contract/profile bindings
- fixture, deterministic gate, rubric, scorer, ballot, and adjudication
  bindings
- semantic/reliability measures and raw resource vector
- `score_disposition`
- closed `failure_plane`, `failure_code`, and `invalidation_reason`
- sanitized evidence refs

**State**:

```text
pending_gates -> gate_failed
      |
      v
pending_ballots -> pending_adjudication -> accepted
      |                  |                   |
      +------------------+-------------------+-> invalidated
```

Candidate-caused terminal outcomes produce accepted estimand records with
acceptance zero when treatment evidence is otherwise valid.

## Entity: Analysis Plan

**Required fields**:

- `analysis_plan_id`, version, digest, status
- calibration partition inputs and provenance
- semantic/reliability floor definitions
- non-inferiority endpoints, margins, confidence level, alpha, power, sample
  sizes, cluster unit/correlation handling, multiplicity adjustment
- raw Pareto resource dimensions and directions
- assigned-attempt estimand and terminal-state mapping
- transient failure classifier and paired rerun cap
- attrition limits, racing/futility rules, campaign budgets
- freeze timestamp and proof that no later-cohort outcome existed

**State**:

```text
draft_from_calibration -> independently_reviewed -> frozen
          |                       |
          +-----------------------+-> invalid
```

Only `frozen` plans may support later qualification. Changes issue a new plan.

## Entity: Analysis Output

**Required fields**:

- `analysis_output_id`, version, digest
- comparison set, score bundle set, partition, and analysis plan bindings
- completeness and attrition results
- floor results
- paired/cluster-adjusted non-inferiority estimates and confidence bounds
- multiplicity result
- raw Pareto vectors and dominance result
- terminal analysis disposition

The computation is deterministic from frozen inputs.

## Entity: Decision Bundle

**Required fields**:

- `decision_bundle_id`, version, digest
- partition ID/type and eligibility
- comparison set and immutable assignment bindings
- score bundle IDs/digests
- analysis plan and output IDs/digests
- ordered gate results
- decision: `qualified`, `no_qualification`, `inconclusive`,
  `calibration_complete`, or `invalid`
- sanitized evidence refs

**Invariants**:

- calibration cannot emit `qualified`;
- any failed gate, mixed/tied Pareto result, incomplete evidence, or
  uncertainty emits no qualification or inconclusive;
- replaying identical frozen inputs yields the same decision and digest.

## Entity: Invalidation Record

**Required fields**:

- invalidation ID/digest
- target object ID/digest/type
- closed invalidation reason
- invalidating authority ID/digest
- detected timestamp
- replacement ID/digest when available

Invalidation is additive. The target is never changed or deleted.

## Sensitive-Evidence Allowlist

Committed entities may contain:

- schemas and contract versions;
- opaque IDs and digests;
- sanitized client identity and opaque boundary IDs;
- normalized tuple decisions;
- relative repository paths where explicitly required;
- deterministic fixtures and acceptance oracles;
- anonymized ballots, sanitized rationales, score/analysis/decision values;
- content-addressed evidence references.

All other raw or identity-bearing evidence is operator-only. Validation fails
closed for unknown fields.

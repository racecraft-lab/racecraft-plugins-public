# Research: G56R-003 Evaluation Platform

## Scope and Method

This research resolves the implementation choices needed for the G56R-003
plan. Repository contracts and the accepted design concept are authoritative.
Current official Codex documentation informs catalog collection semantics but
cannot override the source/runtime intersection or the pinned live catalog.

## Decision 1 — Runtime catalog authority

**Decision**: A refreshed `codex debug models` result from the pinned client is
the sole runtime admission authority. The official-source candidate ledger is
the sole source admission authority. A tuple enters the successor freeze only
when both admit the same normalized ordinary model/effort pair.

**Rationale**:

- runtime support is account, client, and time sensitive;
- source documentation cannot prove local executability;
- app-server, picker, cache, bundled inventory, aliases, defaults, and hidden
  observations can diagnose drift but cannot admit a tuple;
- an empty or invalid intersection is evidence of a blocked collection, not
  permission to reinterpret the archived G56R-002 zero freeze.

**Alternatives rejected**:

- source-only admission cannot prove runtime support;
- runtime-only admission can add undocumented or topology-changing candidates;
- merging all observed surfaces obscures authority and makes replay unstable.

## Decision 2 — G56R-002 reuse

**Decision**: Reuse the existing capability collection, content-addressed
private retention, treatment schema, trace model, trace bundle, and replay
helpers. Add an additive G56R-003 successor publication contract and new
execution traces that conform to the unchanged G56R-002 treatment contract.

**Rationale**:

- the prior artifacts are historical evidence and must remain byte-identical;
- the treatment contract already separates delivery proof from acceptance;
- score and decision data have different invalidation and privacy lifecycles;
- foreign-key-style joins preserve auditability without copying records.

**Alternatives rejected**:

- extending old treatment records with score fields mutates their semantic
  boundary;
- copying G56R-002 helpers creates divergent validators;
- replacing the zero freeze destroys evidence of the original collection.

## Decision 3 — Canonical agent materialization

**Decision**: Implement one pure standard-library materializer in
`speckit_pro_runner.agent_materialization`. It produces exact UTF-8 destination
TOML bytes and instruction/configuration digests. Layer 6 and G56R-006 import
the same function.

**Rationale**:

- byte identity, not parsed equivalence, proves installed-policy treatment;
- shipped ownership makes the future installer reuse real rather than
  aspirational;
- a pure function is deterministic and easy to test;
- callers retain file-system and execution orchestration, keeping the shared
  seam small.

**Alternatives rejected**:

- an evaluation-only materializer would require relocation or copying;
- parsed TOML comparison can miss comments, ordering, encoding, and exact
  instruction bytes;
- moving the legacy smoke runner into production conflates a tool-less
  benchmark with qualification.

## Decision 4 — Governed corpus

**Decision**: Govern exactly twelve role contracts:

- required-core executable: `analyze-executor`, `checklist-executor`,
  `clarify-executor`, `codebase-analyst`, `domain-researcher`,
  `implement-executor`, `phase-executor`, `spec-context-analyst`, and
  `uat-runbook-author`;
- required-core non-executable: `consensus-synthesizer` and `gate-validator`;
- optional helper: `autopilot-fast-helper`.

The manifest records executability separately from contract completeness.
Non-executable roles remain governed but are not run. Helper evidence is
reported separately from required-core primary statistics.

**Alternatives rejected**:

- executable-only membership would make corpus identity drift with route
  availability;
- counting the helper in the required-core estimand changes the target
  population;
- inventing TOML routes for absent roles belongs to a different feature.

## Decision 5 — Fixture validity

**Decision**: A fixture is eligible only when a versioned contract binds its
role/source digest, objective, partition, tools, sandbox, expected artifacts,
acceptance oracle, fixture digest, and independent validity review.

**Rationale**: Semantic scoring must never rescue an invalid, stale, leaking,
or incorrectly partitioned fixture. Validity is therefore a pre-execution hard
gate.

**Alternatives rejected**:

- input/expected-output Markdown alone lacks machine-checkable provenance;
- scorer judgment of fixture validity mixes test construction with outcome
  judgment;
- free-form partition labels cannot prove disjointness.

## Decision 6 — Hybrid blinded scoring

**Decision**: Deterministic role, safety, grounding, mutation, tool, artifact,
and acceptance checks run first. Only a hard-gate pass can receive two
independent candidate-blind semantic ballots under one frozen rubric. A frozen
third adjudicator resolves every decision-affecting disagreement.

**Calibration contract**:

- each scorer and adjudicator has an opaque ID, immutable execution record,
  version/digest, calibration batch, calibration partition, and currentness
  window;
- two ballots must have distinct scorer IDs and executions;
- blinded artifacts omit candidate route/model/effort and identity-bearing
  runtime evidence;
- scorer, rubric, or adjudicator changes invalidate affected bundles
  additively;
- raw prompts, responses, transcripts, and personal mappings remain
  operator-only.

**Alternatives rejected**:

- deterministic-only scoring cannot assess nuanced role quality;
- a single semantic scorer concentrates bias;
- showing route identity enables expectation leakage;
- the legacy lexical scorer is smoke evidence, not qualification authority.

## Decision 7 — Failure and invalidation taxonomy

**Decision**: Keep capability exclusions, snapshot authority failures,
treatment delivery failures, and scoring failures as separate closed planes.
Score bundles use closed disposition, failure plane, failure code, and
invalidation reason values.

Candidate-caused terminal states remain in the assigned-attempt estimand with
acceptance zero. Treatment, fixture, scorer, ballot, adjudication,
infrastructure, evidence-boundary, partition, and schema failures remain
distinguishable and cannot be relabeled as candidate quality.

**Alternatives rejected**:

- one shared error string is not machine-checkable;
- dropping failed attempts creates complete-case bias;
- mutating a stale score erases the decision history.

## Decision 8 — Statistical estimand and sequence

**Decision**: Use an assigned-attempt, task-paired estimand with role or fixture
cluster adjustment. The frozen decision sequence is:

1. evidence and absolute semantic/reliability floors;
2. paired, cluster-adjusted non-inferiority against prespecified margins and
   multiplicity controls;
3. Pareto dominance on the unweighted raw resource vector.

Any failed step, tie, mixed dominance, missing pair, or uncertainty is
inconclusive/no qualification.

**Rationale**:

- pairing controls task difficulty;
- cluster adjustment addresses repeated observations within role/fixture
  groups;
- non-inferiority protects quality before optimizing resources;
- raw-vector Pareto comparison avoids post-hoc weighting;
- an explicit inconclusive state is more honest than forced ranking.

**Alternatives rejected**:

- a weighted scalar hides tradeoffs and invites outcome-adaptive weights;
- Pareto-first can prefer a cheaper but materially worse route;
- complete-case analysis excludes candidate-caused failures;
- per-arm retry creates differential opportunity.

## Decision 9 — Reruns and attrition

**Decision**: Only an independently preclassified transient harness failure may
trigger a rerun, and the whole pair reruns under a frozen cap. Candidate
failure, timeout, cancellation, budget exhaustion, or abandonment is a
terminal outcome with acceptance zero. Evidence that remains incomplete after
the cap is inconclusive.

**Alternatives rejected**:

- one-arm retries break pairing;
- unlimited retries hide reliability costs;
- never rerunning independently proven infrastructure failures wastes valid
  calibration capacity.

## Decision 10 — Analysis-plan freeze and partitions

**Decision**: Calibration may estimate feasibility, variance, missingness,
scorer behavior, and sample-size inputs. One versioned analysis plan then
freezes margins, sample sizes, power, alpha, multiplicity, racing/futility,
attrition caps, budgets, and terminal rules before any G56R-007 through
G56R-010 outcome is observed.

Every artifact binds one closed partition. Calibration is permanently
`qualification_eligible=false`, cannot mix with later partitions, and cannot
emit final route policy.

**Alternatives rejected**:

- freezing numerical values before calibration discards the accepted pilot
  purpose;
- freezing after cohort outcomes permits outcome-adaptive decisions;
- cohort-specific mutable plans prevent comparable qualification claims.

## Decision 11 — Live versus replay execution

**Decision**: Default CI runs schema validation, deterministic hard gates,
frozen bundle replay, and statistical golden tests. A live calibration run
requires an explicit local command, pinned client and snapshot, declared
budget, operator-only raw retention destination, and calibration partition.

**Alternatives rejected**:

- live CI is networked, chargeable, nondeterministic, and can expose private
  evidence;
- no CI replay would leave the decision platform unverified;
- implicit live fallback can consume the wrong evidence partition.

## Decision 12 — Generated release artifacts

**Decision**: `scripts/refresh-release-artifacts.py` is the sole generator for
runner trust metadata, distribution payloads, installed-cache proofs, and
release evidence. Authored runner changes and their generated consequences
ship in the same slice; generated files are never manually edited.

**Rationale**: The repository already encodes an idempotent, checkable
source-to-payload contract. A second generator would create drift.

## Resolved Unknowns

- The live smoke files remain supported but explicitly non-release.
- G56R-006 reuses the shipped materializer import rather than relocating it.
- The corpus is contract-complete even while two required roles are
  non-executable.
- G56R-003 produces only calibration evidence and a frozen reusable platform,
  not final route policy.
- No external package, Bash helper, database, or network service is required
  for deterministic replay.

# Phase 1 Data Model: CAR-003

**Date**: 2026-07-24 | **Spec**: `specs/car-003-evaluation-runner-scoring/spec.md`

## Conventions

- All digests are `sha256:<64 hex>` over the canonical JSON serialization
  (sorted keys, minimal separators, UTF-8, no NaN) of the record **excluding its
  own digest field**, recomputed and compared at bundle acceptance and at replay
  (FR-032, FR-033). The one exception is the materialization content hash, which
  is over destination **file bytes read back from disk**, not canonical JSON
  (FR-008).
- "Binding" means the `{id, digest}` pair used throughout the contracts.
- **Authority** names the schema that owns a record's shape:
  - *Shared* — a repo-level contract under `tests/speckit-pro/layer6-efficiency/contracts/`,
    byte-identical across the Claude and Codex worktrees. Never extended here.
  - *Frozen CAR-002* — `docs/ai/research/claude-trace-contract.schema.json`.
    Consumed unchanged.
  - *CAR-003* — a schema authored under this spec's `contracts/`.

## Identifier Graph

```text
source_ledger_binding ──┐
                        ├─► candidate_freeze_id ──► candidate_route_id
runtime_snapshot_binding┘         │
                                  ├─► comparison_set_id ──► assignment_id
partition_id ─────────────────────┤                              │
   │                              │                              │
   └─► objective_id (disjoint)    │                              ▼
                                  │                     execution_trace_id
corpus_id ──► role_id ──► fixture_digest                         │
                                  │                              ▼
experiment_policy_id ─────────────┤                      score_bundle_id
                                  │                              │
calibration_protocol_id ──────────┴──► analysis_plan_id ─────────┤
                                                                 ▼
                                                       decision_bundle_id
```

Every arrow is a foreign-key-style reference carrying an ID and a digest. No
record embeds another; bundles reference traces and never mutate them (FR-010).

---

## Entity: Runtime Catalog Collection

**Authority**: CAR-003 (collection evidence, input to the freeze).

**Fields**: command contract; pinned client version and distribution; sanitized
account and environment boundary; raw and parsed catalog digests; observed
models; alias bindings; visible defaults; supported efforts; collection
timestamps; invalidation criteria; `authentication_mode`.

**Invariants**:

- The sole admitting surface is the operator-run `claude -p --model <alias-or-id>`
  print-mode canary probe on the pinned client. Effort is admitted only by
  configuration acceptance on that same surface (FR-002).
- Subagent-frontmatter dispatch, the model picker, the catalog endpoint, visible
  defaults, and bundled client strings are diagnostic-only. They may corroborate
  or invalidate, never admit (FR-004).
- Disagreement between the admitting probe and a diagnostic observation triggers
  recorded investigation or exclusion. It is never logged and ignored (FR-004).
- The full ordered effort set `low` through `max` is probed for every
  role-eligible model, including `high` as the documented search origin (FR-040).
- Only allowlisted sanitized boundary evidence is committed. A non-allowlisted
  field blocks publication rather than being silently stripped (FR-027).

## Entity: Successor Capability Freeze

**Authority**: CAR-003 — `contracts/successor-capability-freeze.schema.json`.

**Fields**: see the contract. Key ones: `admitted_tuples` (min 1),
`excluded_tuples` with closed reasons, `authority_failures`,
`invalidation_triggers` (all four), `admitting_surface`, `authentication_mode`.

**Invariants**:

- Admission is the intersection of the official-source candidate ledger and the
  pinned-runtime-supported tuple set. Runtime discovery can remove or constrain
  candidates but never add a model identity beyond the ledger (FR-003).
- Effort canonicalization targets only `low` < `medium` < `high` < `xhigh` <
  `max`. Omitted, `inherit`, runtime-only, API-only, alias, aggregate, and
  topology-changing values never become ordinary candidate efforts. An unmapped
  source value records `canonical_effort_unknown` (FR-003).
- Fast mode and any orchestration-topology-changing mode is a CAR-004
  policy-level control, recorded as
  `topology_control_not_candidate_effort` (FR-005).
- Authority failures mean diagnostic collection evidence only: **no freeze record
  is emitted at all**, qualification-capable execution is blocked, and the six
  archived CAR-002 tuples are **never** promoted to an active candidate set. The
  failures are carried on the runtime catalog collection record, which is why a
  published freeze always has an empty `authority_failures` array and at least one
  admitted tuple — the existence of the record *is* the publication signal.
  Immutable does not imply reusable (FR-028, FR-044).
- Non-reuse is checked, not asserted: each admitted tuple's
  `runtime_evidence_digest` must resolve to the collection record named by this
  freeze's own `runtime_snapshot_binding`. One resolving to the archived snapshot
  is rejected with `availability_not_proven`. `historical_freeze_binding` proves
  the predecessor was read unmutated and is never a source of tuples (FR-044).
- CAR-002 artifacts, identifiers, and snapshot evidence are unchanged. Every
  CAR-003 capability record is additive (FR-001, SC-001).

**State transitions**:

```text
collected ──► intersected ──► published            (authority_failures empty)
                         └──► diagnostic_only      (authority_failures non-empty)
published ──► invalidated                          (any refresh trigger fires)
```

`invalidated` is terminal and additive. A freeze is never rewritten in place.

## Entity: Refresh Trigger

**Authority**: CAR-003 (embedded in the freeze contract).

Four versioned triggers, each recording what it invalidates and what survives
(FR-041):

| Trigger | Invalidates | Survives |
|---|---|---|
| `client_change` | freeze admission, unexecuted bindings, affected experiment/score/decision bundles | execution traces, treatment records, bound pairs |
| `catalog_change` | same | same |
| `alias_repoint` | same, **plus** in-flight attempts for that alias become non-scorable for the requested route | same |
| `source_ledger_change` | same, but **cannot** admit a tuple the pinned runtime never supported | same |

Surviving records are **marked** invalidated, never rebound.

## Entity: Alias Re-point Attribution

**Authority**: CAR-003 — `contracts/car-003-additive-records.schema.json`.

**Five observables** (FR-039):

1. The requested alias.
2. The identity bound by **CAR-003's own successor freeze** — explicitly not the
   identically named run-time route-resolution field, and never the archived
   CAR-002 snapshot. Carried with a `candidate_freeze_binding` `{id, digest}` so
   the provenance is verifiable at replay rather than self-declared; a binding
   resolving to anything but a published CAR-003 freeze records
   `alias_repoint_unresolved`.
3. The run-observed identity from the per-model usage breakdown.
4. The complete environment-override proof.
5. The pinned client version at freeze time **and** at run time.

**Classification**:

```text
requested route unchanged
  AND every local override proven unset
  AND client version unchanged            ──► platform_route_change
plugin-initiated route substitution        ──► resolver_fallback
incomplete override proof
  OR changed client version
  OR otherwise unattributable              ──► alias_repoint_unresolved  (blocks admission)
no identity divergence                     ──► no_divergence
```

**Invariants**:

- Lives in this additive record because the frozen `record_class` enum is closed
  to `success`, `null`, `unavailable`, `misdelivery` (FR-045).
- Attribution is bounded by its enumerated cause set, not proven: documented
  serving-infrastructure changes can alter behavior with the identity unchanged.
  A behavioral difference **without** an identity change is a separate diagnostic
  condition and is never recorded as an alias re-point (FR-045).
- A platform route change is never reported as a SpecKit Pro fallback (FR-039).
- Validated by a synthetic replay fixture that supplies a divergent observed
  identity below the live trigger path while overrides remain genuinely unset.
  If that path cannot be built, `validated_by` records `unvalidated_in_band`
  rather than claiming tested coverage (FR-046).

## Entity: Canonical Materialization

**Authority**: CAR-003 (shipped in `speckit-pro/speckit_pro_runner/materializer.py`).

**Fields**: destination path; rendered frontmatter-plus-body content hash;
instruction hash; configuration hash; materialization ID.

**Invariants**:

- Exactly one shipped materialization contract owns the rendered destination
  bytes and the instruction/configuration digests consumed by both Layer 6
  evidence and CAR-006 resolver behavior. No parsed-only or divergent evaluation
  materializer exists (FR-006).
- The content hash is SHA-256 over the destination file's exact UTF-8 bytes read
  back from the destination path **after write** — no normalization,
  re-serialization, newline translation, trailing-newline insertion, or key
  reordering, and never from an in-memory render buffer (FR-008).
- The destination path is verified separately and is **not** folded into the
  digest preimage (FR-008).
- Parsed-field equivalence or source-template equality does not satisfy the
  proof (FR-008).

## Entity: Mandatory Observation Manifest

**Authority**: CAR-003 — `contracts/car-003-additive-records.schema.json`.

**Fields**: manifest ID and digest; telemetry-profile binding; `required_fields`
with `{field_path, category}`; `nullable_exemptions`;
`missing_field_failure_code`.

**Invariants**:

- Published as a versioned additive artifact because the frozen CAR-002
  telemetry profile constrains only list cardinality and never enumerates the
  fields, which left FR-009 undecidable without it.
- Each mandatory field carries a non-null observed value and a classification
  other than `unavailable`. An `unavailable` or null mandatory field records
  `mandatory_telemetry_missing`.
- Explicit nulls remain permitted only on fields the frozen schema declares
  nullable **and** that are absent from this manifest.

## Entity: Partition Registry Entry

**Authority**: CAR-003 — `contracts/experiment-assignment.schema.json`.

**Fields**: `partition_id`; `partition_type`; `qualification_eligible`;
`objective_set_digest`; `objective_ids`; `frozen_at`; `owning_spec`.

**Invariants** (FR-013):

- Disjointness is enforced at the **objective** level. An objective identifier
  appearing in more than one registered partition's objective set fails closed
  with `failure_plane=partition`.
- `partition_type` and `qualification_eligible` are immutable after freeze.
- Calibration always carries `qualification_eligible=false` (schema-enforced).
- CAR-003 consumes **only** `qualification_eligible=false` calibration
  objectives and fails closed on cross-partition reuse.

## Entity: Calibration Protocol

**Authority**: CAR-003 — `contracts/experiment-assignment.schema.json`.

**Invariants** (FR-037):

- Carries no margins, no sample sizes, no terminal thresholds — all three are
  schema-pinned to `false`.
- Calibration-partition pairs bind this instead of the analysis plan, and the
  frozen analysis plan references it back through `calibration_binding`. This is
  the resolution of the circular dependency: the plan freezes only after
  calibration, so a calibration pair cannot bind a plan that does not yet exist.

## Entity: Role Fixture Contract and Corpus

**Authority**: CAR-003 — `contracts/role-corpus.schema.json`.

**Invariants** (FR-011, FR-012, FR-033):

- Exactly twelve role entries: eleven required-core roles with shipped agent
  definitions, plus `autopilot-fast-helper`, contract-only until CAR-011.
- `required_core` and `executable` are independent booleans. Every contract
  field binds even when `executable=false`.
- `candidate_route_bindings` MUST be absent when `executable=false`
  (schema-enforced). A non-executable role produces no score bundle and is never
  counted as attrition.
- `autopilot-fast-helper` is analysed separately from required-core primary
  statistics.
- Every fixture binds a versioned role/source digest, objective, evidence
  partition, permitted tools and mutation contract, expected artifacts,
  acceptance oracle, fixture digest, and independent validity review before any
  candidate may score against it. A digest mismatch fails the fixture **before**
  candidate scoring.

## Entity: Comparison Set and Assignment

**Authority**: CAR-003 — `contracts/experiment-assignment.schema.json`.

**Invariants** (FR-037, FR-021, FR-041):

- Every binding exists before execution: comparison set, partition, candidate
  and comparator routes, role, fixture, task, instruction and configuration
  hashes, capability freeze, runtime snapshot, route resolution, materialization,
  experiment policy, assigned order, pre-execution timestamp.
- Qualification-eligible pairs bind the frozen analysis plan; calibration pairs
  bind the calibration protocol. The schema enforces exactly one of the two.
- Refreshes create additive invalidations. A bound pair is never rebound.
- Each rerun creates **new** paired assignments linked to the original
  comparison set rather than superseding it. Superseded pairs are retained
  immutably and marked `superseded`.
- Exclusion is complete-pair and arm-symmetric. Primary statistics use exactly
  one terminal complete pair per assignment.

## Entity: Execution Trace

**Authority**: Frozen CAR-002 `exactTreatmentReplay`, consumed unchanged.

**CAR-003 binding requirements** (FR-010):

- One new immutable `execution_trace_id` for every assigned attempt, regardless
  of score eligibility.
- Comparison set and assignment IDs; configured-route and authoritative
  route-change monitoring proof; canonical materialization ID and digests or
  installed-policy proof; every mandatory observation; `treatment_disposition`;
  an explicit terminal event.
- The frozen `exactTreatmentReplay.outcome` shape — `{status, telemetry_ref,
  notes}` — is **not** extended. Scores live in the separate score bundle.
- Pre-score `acceptance` remains permitted null under the shared contract.

**Trace digest** (FR-032): SHA-256 over the canonical JSON serialization of the
complete trace record. Recomputed and compared at bundle acceptance and replay.
A mismatch or dangling reference produces an additive invalidation with reason
`trace_reference_integrity_failure` and blocks the decision bundle rather than
rewriting either artifact.

## Entity: Treatment Disposition

**Authority**: **Shared** treatment-record contract. Reused, never extended.

- `treatment_disposition` ∈ `{proven, unknown, non_scorable_rerouted, hard_fail}`.
- `disposition_reasons` is the shared closed array. Platform alias re-pointing
  reuses the existing `service_reroute_requested_route_non_scorable` member; no
  Claude-only member is coined (FR-034).

**Co-occurrence rule** (FR-031):

```text
derive every condition independently
  ──► record ALL fired codes in disposition_reasons (union, never discard)
  ──► terminal disposition = highest-precedence bucket:
        hard_fail > non_scorable_rerouted > unknown > proven
```

There is no condition-level tie-break that suppresses one co-firing code in
favour of another. The precedence is specified so that independent Claude-side
and Codex-side implementations classify identical evidence identically.

## Entity: Score Eligibility Predicate

**Authority**: CAR-003 logic over shared and frozen fields (FR-030).

```text
score_eligible :=
      treatment_disposition == "proven"
  AND (installed_policy_proof OR content_hash_identical_materialization)
  AND configured_route_proof_matches
  AND mandatory_observations_complete
  AND route_change_monitoring_complete
  AND no platform route change
  AND no misdelivery
  AND no treatment failure
  AND no infrastructure failure
```

**Invariants**:

- The frozen `scorable` flag is **necessary but not sufficient**. It is derived
  solely from the record class and speaks only to platform-initiated route
  change: `scorable=false` forces score-ineligibility, while `scorable=true`
  does not by itself admit an outcome.
- Profile-only effective-treatment evidence stays diagnostic and replay-only.
- Platform-re-pointed attempts remain immutable but non-scorable for the
  requested route. Different-agent, ambiguous, unapproved, or unidentifiable
  delivery hard-fails treatment without scoring the observed destination
  (FR-031).

## Entity: Deterministic Gate Result

**Authority**: CAR-003 — `contracts/score-bundle.schema.json`.

Closed gate set (FR-014): `role`, `safety`, `grounding`, `mutation`, `tool`,
`output`, `acceptance`. Each records gate name, pass/fail, and an evidence
digest. **No ballot is collected until every required gate has passed.**

## Entity: Semantic Ballot

**Authority**: CAR-003 — `contracts/score-bundle.schema.json`.

**Invariants** (FR-015, FR-035, FR-047, FR-048):

- Two distinct scorer identities and execution records, candidate-blind
  artifacts, a frozen rubric version and digest, and current scorer calibration.
- Each ballot binds exactly **one** blinded-artifact digest as its sole scored
  input.
- Before collection, a mechanical leak check runs the blinded artifact against
  freeze-bound model identities, aliases, effort values, agent frontmatter, and
  route identifiers. Failure records `ballot_non_blind` and blocks scoring.
- A scorer or adjudicator is never drawn from a candidate's own model family.
  The exclusion is static and declared in the frozen experiment policy, so it
  costs nothing at replay.
- Presentation order is randomized under a seed recorded for replay. The rubric
  scores only checkable properties.
- Artifact paraphrase or style normalization before scoring is **prohibited**:
  it requires an additional non-frozen model call, which breaks bit-exact replay
  and changes what is being scored.
- Each ballot records `provenance_inferred` and, when true, the signal. A
  recorded inference does not silently invalidate the ballot, but the residual is
  reported alongside any qualification claim, and blinding is reported as bounded
  rather than complete.

## Entity: Adjudication

**Authority**: CAR-003 — `contracts/score-bundle.schema.json`.

A frozen third adjudicator resolves every decision-affecting ballot
disagreement, binding both primary ballots and attaching its provenance to the
score bundle (FR-015). `adjudicator_reused_primary_scorer` is a closed failure
code.

## Entity: Score Bundle

**Authority**: CAR-003 — `contracts/score-bundle.schema.json`.

Closed taxonomies adopted verbatim from the Codex twin (FR-034):

- `score_disposition`: `accepted`, `gate_failed`, `non_scorable`, `invalidated`.
- `failure_plane`: `none`, `treatment`, `fixture`, `scorer`, `ballot`,
  `adjudication`, `candidate`, `infrastructure`, `evidence_boundary`,
  `partition`, `schema`.
- `invalidation_reason`: `none`, `fixture_changed`, `scorer_changed`,
  `rubric_changed`, `adjudicator_changed`, `treatment_changed`,
  `capability_changed`, `partition_changed`, `schema_changed`.
- `failure_code`: the 35-member set, including `service_reroute` for platform
  alias re-pointing. The capability-plane code `alias_repoint_unresolved` stays
  at the capability-freeze plane and is never repurposed here.

**Resource vector**: exactly the eight decision-bearing dimensions —
`input_tokens`, `cached_input_tokens`, `output_tokens`, `duration_ms`,
`retries`, `compactions`, `acceptance`, `terminal_state` — identical to the
twin's frozen Pareto policy (FR-018).

**Reasoning-token report**: `reasoning_output_tokens` is recorded and reported
for every attempt with `decision_bearing` pinned to `false` and a
`stated_limitation` string. The field is disjoint from `output_tokens` in the
shared contract and is billed, so the exclusion is a stated limitation, not a
claim the cost is absent (FR-049).

**Invalidations are additive.** A fixture, scorer, rubric, adjudicator,
treatment, capability, partition, or schema version change creates a new
invalidation without mutating prior bundles.

## Entity: Experiment Policy

**Authority**: CAR-003 — `contracts/experiment-policy.schema.json`.

**Invariants**:

- `pair_before_execution` is pinned true; `cache_isolation` is pinned to
  `per_arm_ephemeral_root` so one arm can never warm another's cache.
- `candidate_failures_remain_in_estimand` is pinned true and
  `candidate_failure_acceptance` to `0` (FR-020) — no complete-case filtering.
- Rerun policy: transient harness failures only, complete-pair scope, a
  prespecified cap counting **reruns not attempts**, and
  `classification_timing` pinned to `arm_blind_before_outcome_read`, because
  classifying after outcomes are visible is outcome-conditioned filtering
  (FR-021).
- `scorer_family_exclusion` is static, with `paraphrase_normalization` pinned to
  `prohibited` (FR-047).
- The budget **must equal** the frozen analysis-plan budget for
  qualification-eligible partitions and may be tighter only for calibration. Any
  inequality fails closed with `failure_plane=partition`, because budget
  exhaustion enters the estimand at acceptance zero and an outcome-dependent
  budget would redefine it (FR-038).
- Default execution mode is `deterministic_replay`. `explicit_local_live`
  requires an explicit, local, pinned, budgeted operator campaign (FR-022).

## Entity: Analysis Plan

**Authority**: CAR-003 — `contracts/analysis-plan.schema.json`.

**Invariants**:

- `status` is pinned `frozen`. Frozen after calibration and before any CAR-007
  through CAR-010 cohort outcome is observed, evidenced by
  `pre_cohort_outcome_absence_digest` (FR-023, SC-012).
- Binds workload strata with p95 raw-resource and p95-duration guardrails, and a
  cache-state isolation policy, before either arm runs (FR-049).
- `pareto_policy.dimensions` is exactly eight, `weights_prohibited` is pinned
  true, and `mixed_or_tied_result` is pinned `inconclusive`.
- The multiplicity declaration covers **three families**, not one global
  correction (FR-050):
  1. **Conjunctive** — absolute floors and the non-inferiority stage. All must
     pass, so they control error at alpha with no adjustment and no alpha
     relaxation, paying the cost in power. Pinned to `none_required` with a
     rationale.
  2. **Pareto disjunctive** — "better on at least one dimension" inflates the
     spurious-win rate with each added dimension and must state how it is
     controlled. ("No worse on every dimension" is conjunctive and becomes more
     conservative as dimensions grow; leaving the whole stage unadjusted
     under-protects.)
  3. **Across-ladder** — many ladders across candidates, roles, and strata form
     their own family, declared independently of the within-ladder rule.
  - `cluster_adjustment_is_precondition` is pinned true: paired clustered
    observations analyzed with naive standard errors inflate error through a
    mis-estimated test statistic, which no familywise or false-discovery
    correction can repair.
- Specific numeric corrections freeze with the rest of the plan after
  calibration. The schema fixes what the declaration must **cover**, not which
  correction is chosen — the same value the twin leaves open for the same reason.

## Entity: Decision Bundle

**Authority**: CAR-003 — `contracts/analysis-decision.schema.json`.

**Ordered decision ladder** (FR-017, FR-018, FR-019):

```text
1. bindings ──► 2. partition ──► 3. treatment ──► 4. deterministic
      ──► 5. provenance ──► 6. completeness
      ──► 7. absolute semantic AND reliability floors
      ──► 8. task-paired, cluster-adjusted non-inferiority
      ──► 9. Pareto dominance over the eight raw dimensions
```

A stage that was not reached records `not_evaluated` rather than being omitted.

**Terminal states**: `qualified`, `no_qualification`, `inconclusive`,
`calibration_complete`, `invalid`.

**Invariants**:

- A failed gate, tie, mixed dominance, incomplete evidence, or statistical
  uncertainty returns no qualification. **No weighted ranking is forced**
  (FR-019).
- The bundle carries no per-category weights, no price coefficients, and no
  scalar score field. Published price data may appear only as diagnostic
  context, never as a selection coefficient (FR-019).
- `qualified` is schema-gated to `qualification_eligible=true` partitions, and
  calibration is always ineligible — so CAR-003 structurally cannot emit a final
  preferred or fallback route policy (FR-024).
- Deterministic replay from the same frozen experiment, score, analysis, and
  decision bundles reconstructs the same terminal decision on a clean checkout
  (SC-011).

## Entity: Cache Diagnostic Record

**Authority**: CAR-003 — `contracts/car-003-additive-records.schema.json`.

Cache-write-by-TTL-class and cache-read breakdowns, with `decision_bearing`
pinned `false`. Carried additively because the shared `rawTokenVector` is closed
under `additionalProperties: false`, is byte-identical across worktrees, and
carries only `input_tokens`, `output_tokens`, `cached_input_tokens`, and
`reasoning_output_tokens` (FR-018).

The TTL-class key space is closed to `ephemeral_5m` and `ephemeral_1h` — the two
cache-creation classes the frozen CAR-002 telemetry profile already classifies as
`stable_native` observations, reused rather than renamed. The budget ceilings in
both the experiment policy and the analysis plan use the identical key set, so a
ceiling can never be keyed differently from the measurement it bounds and silently
stop applying (FR-022, FR-038).

## Sensitive-Evidence Allowlist

**Deny by default** (FR-027, FR-036, SC-015). Committed evidence is limited to
sanitized schemas, manifests, deterministic fixtures, opaque scorer identities,
rubric/scorer/adjudicator digests, anonymized ballots, score bundles, and
evidence references.

Operator-only, never committed: raw captures, account identifiers,
authentication material, credentials, headers, cookies, private hostnames,
absolute paths, repository remotes, raw scoring prompts, responses, transcripts,
personal scorer identity mappings, and billing or plan identifiers.

A non-allowlisted field **blocks publication** rather than being silently
stripped. The existing sanitization helpers already normalize home paths and
session identifiers and are reused unchanged.

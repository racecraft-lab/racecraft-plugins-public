# Phase 0 Research: CAR-004 Policy Controls and Adaptive Comparators

Every unknown the Technical Context could have carried is resolved below. The
spec's Assumptions section already settled the two contract document names, the
frozen numerics, and their serialization, so this document resolves only what
sits between that settlement and code: which frozen members the new documents
bind, how identity is computed, where the reserved partition lives inside a
closed type set that CAR-004 may not extend, and how each spec rule becomes a
machine check.

Authority order used throughout: `docs/prd-claude-agent-routing.md`, then
`docs/ai/specs/.process/CAR-004-design-concept.md` including its 2026-07-27
Revisions section, then the roadmap. The roadmap is known stale on smoke
authentication and was not followed on that point.

**No `[NEEDS CLARIFICATION]` markers remain.**

---

## D1. Contract validation engine

**Decision.** Validate instances by driving the schema document itself, using a
fail-closed recursive walker that resolves `$ref` only under `#/$defs/` and
raises on anything else. The engine lives in
`tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py` as
`load_contract()`, `validate_instance()`, and `ControlContractError`;
`claude_control_comparison.py` imports it.

**Rationale.** `lib/claude_trace_schema.py` already implements exactly this
engine, but it is frozen CAR-003 code bound at import to one hard-coded schema
path, so it cannot be pointed at a new document and must not be edited (FR-005).
Re-implementing the walker twice would be worse than sharing it once. Placing the
shared primitive in the first domain module that needs it, rather than in a new
module created only to be shared, is the precedent already set by
`claude_successor_freeze.py`, which owns `canonical_json` and `record_digest` for
the whole program, and by `claude_experiment_policy.py`, which imports them.

**Alternatives considered.** A third `claude_contract_schema.py` module holding
only the engine: rejected under YAGNI — a module whose entire content exists for
two in-tree callers, and it pushes the declared file count over the warn
threshold for no reviewer benefit. Third-party `jsonschema`: rejected outright by
constitution principle II.

**Consequence for SC-017.** The engine's refusal of any non-local `$ref` is what
makes "neither document resolves a reference outside its own `#/$defs/`"
machine-checked rather than asserted. A unit case feeds it a document carrying a
cross-document `$ref` and asserts the raise.

---

## D2. How CAR-003 contracts are referenced

**Decision.** Data-level bindings only. Each new document restates the CAR-003
`binding` shape locally as `#/$defs/binding` — an object of `id` plus `digest`
with `additionalProperties: false` and the `^sha256:[0-9a-f]{64}$` digest
pattern — and every CAR-003 reference is an instance of it. No `$ref` crosses a
document boundary and no `$id` outside `car-004/` is dereferenced.

**Rationale.** FR-004 requires reference by stable identifier and digest. The
repository validator resolves only local `#/$defs/` (D1), so a cross-document
`$ref` would fail closed at validation time rather than degrade gracefully. The
spec's Assumptions state this directly.

**Bindings the two documents carry.** These are the CAR-003 `$id` values the
twin-handoff record's category 5 enumerates:

| Bound contract | `$id` | Bound by | Why |
|---|---|---|---|
| Successor capability freeze | `https://racecraft.dev/schemas/car-003/successor-capability-freeze.schema.json` | adaptive control | supplies `admitted_tuples` and the closed effort ladder the `escalation_ladder` is checked against (FR-011a) |
| Score bundle | `https://racecraft.dev/schemas/car-003/score-bundle.schema.json` | all three controls, comparison contract | supplies the terminal-state, failure-plane, and failure-code enums and the eight-member `resource_vector` (FR-008, FR-016a, FR-021e) |
| Analysis plan | `https://racecraft.dev/schemas/car-003/analysis-plan.schema.json` | comparison contract | supplies the frozen Pareto policy, the quality floors, the reliability guardrails, alpha, and the confidence level (FR-019, FR-020, FR-023) |
| Experiment policy | `https://racecraft.dev/schemas/car-003/experiment-policy.schema.json` | registry `smoke_bounds` | supplies the closed budget member names and the TTL class key space (FR-030) |
| Role corpus | `https://racecraft.dev/schemas/car-003/role-corpus.schema.json` | partition registry entries | supplies the objective identities partitions are built over (FR-025) |

The environment contract is bound by the unpinned control for its pinned
parent-session model and effort (FR-006). It has no `contracts-claude/` member —
only `contracts-codex-specification/environment-contract.schema.json` exists on
this side — so the unpinned control binds the pinned parent by `{id, digest}`
against the same source the CAR-003 harness reads, and the twin-handoff record
files that binding under category 5 with an explicit note that the Claude side
carries no local mirror of that document. Implementation confirms the exact id
before freezing; a wrong binding is a digest mismatch, which fails closed.

---

## D3. Content-address preimage and array order

**Decision.** Reuse `record_digest(record, digest_field=...)` and
`canonical_json` from `claude_successor_freeze.py` unchanged. A control's
`control_digest` is taken over its own record with the digest field excluded; the
registry's `registry_digest` and the comparison contract's
`comparison_digest` likewise.

**Rationale.** One FR-033 preimage rule already governs every CAR-003 digest;
coining a second rule would make two artifacts in one program un-comparable.

**The order question FR-011b raises, resolved.** `canonical_json` passes
`sort_keys=True`, which sorts **object keys** only. JSON array element order is
preserved by `json.dumps` and is therefore inside the preimage. `escalation_ladder`
is an array, so its declared order is hash-relevant exactly as FR-011b requires,
and reordering it yields a different `control_digest`. No custom serializer is
needed, and none may be introduced — a hand-rolled canonicalization would fork
the preimage rule. This is recorded here because it is the single most likely
implementation error in the feature: an implementer reading "never sorted" may
reach for a bespoke serializer and silently break digest comparability with
CAR-003.

**Hash-relevance is declared, not inferred.** Every property in both documents
carries a `hash_relevant` classification in `data-model.md`, and the twin-handoff
record's category 1–6 entries carry it as a field. The registry-level
`smoke_bounds` object is hash-relevant to the registry document and **not** to any
individual control's identity, per the spec's Assumptions: the bounds are shared
by all three controls and changing them must not re-identify a comparator.

---

## D4. Where the reserved CAR-011 partition lives

**Decision.** Both partitions are `partition_registry_entry` records produced by
the frozen `build_partition_registry_entry()` in `claude_experiment_policy.py`
and committed together in `fixtures-controls/partition-registry-entries.json`:

1. **Reserved CAR-011 comparison partition** — `partition_type:
   "integrated_confirmation"`, `qualification_eligible: true`, `owning_spec:
   "CAR-004"`. Untouched by CAR-004 and held for CAR-011.
2. **CAR-004 smoke partition** — `partition_type: "calibration"`,
   `qualification_eligible: false`, `owning_spec: "CAR-004"`, carrying the at
   most five non-reserved objectives the live smokes use.

**Rationale.** `PARTITION_TYPES` is a closed five-member set in frozen CAR-003
code and is mirrored in the frozen `experiment-policy.schema.json` partition
enum. Coining a sixth type would edit a mirrored member, which FR-005 forbids
absolutely. Within that closed set, `integrated_confirmation` is the only member
whose meaning matches "the untouched slice the final comparison runs on", and it
is precisely the class FR-027 bars CAR-004 from consuming — the reservation and
the prohibition then read onto the same word instead of onto two.

Choosing `calibration` for CAR-004's own smoke objectives is the load-bearing
half. `build_partition_registry_entry()` **raises** when `calibration` is paired
with `qualification_eligible: true`, so a CAR-004 smoke partition is structurally
incapable of carrying qualification-bearing evidence. FR-027's "no
outcome-bearing scored evidence" therefore holds by construction rather than by
reviewer vigilance, and it holds in the frozen code rather than in anything
CAR-004 authors.

Registering a qualification-eligible partition CAR-004 may never consume follows
the pilot exactly: `run-calibration-pilot.py:395-425` registers screening,
selection, cohort-lock, and integrated-confirmation entries that CAR-003 never
consumes, "so the refusal is provable, not asserted", each under `owning_spec:
"CAR-003"`. CAR-004 records `owning_spec: "CAR-004"` on both entries for the same
reason — the field is provenance for the spec that froze the entry, is read by no
frozen admission rule, and naming an unstarted spec would claim an ownership
CAR-004 cannot confer.

**Disjointness is proven, not declared.** The CAR-004 smoke partition registers
its own five objective identities. It does not reuse CAR-003's calibration
objectives, which the used-exactly-once discipline has already spent. Passing
both entries to the frozen `register_partitions()` fails closed on any shared
objective, so the reservation is enforced by the same machinery that enforces
CAR-003's partition disjointness.

**Alternatives considered.** `cohort_lock`: rejected — it names the act of
locking a cohort, not the workload the comparison consumes. A separate reserved
corpus file: rejected in the design concept's Q8 as fragmenting corpus governance
into two sources of truth. Prose-only reservation in the analysis plan: rejected
in Q8 — an accidental consumption would surface only after the evidence was
burned.

**Residual risk, stated.** CAR-011 owns the comparison and has not been written.
If it later needs a different partition type, that is a **new** registry entry
under a new content address, never an in-place edit — `partition_type` is inside
the `objective_set_digest`-bearing record, so re-typing changes identity. The
reservation's purpose, holding the objectives untouched, survives either way.

---

## D5. Adaptive signal domain and total response mapping

**Decision.** The adaptive control declares three total maps plus one precedence
rule, rather than a cross-product:

- `terminal_state_response` — one entry per member of the frozen score-bundle
  `resource_vector.terminal_state` enum (6 members).
- `failure_plane_response` — one entry per member of the frozen `failure_plane`
  enum (12 members).
- `failure_code_response` — one entry per member of the frozen `failure_code`
  enum (36 members, counted from the committed schema rather than assumed).
- `signal_precedence` — the frozen array `["failure_code", "failure_plane",
  "terminal_state"]`. The first source whose observed value is not the `none`
  member decides; if all are `none`-valued the terminal state decides.

The response enum is closed at three: `escalate`, `hold`, `non_scorable`.

**Rationale.** FR-010 requires totality over the declared signal domain with no
unmapped signal and no signal resolving to two responses. A cross-product of
6 × 12 × 35 would be 2,520 declarations, unreviewable and impossible to keep
total by inspection. Three independent maps plus an explicit precedence order is
total over the same domain, is checkable as set-equality against three frozen
enums read live from `score-bundle.schema.json`, and makes "exactly one response"
a property of the precedence rule rather than of 2,520 hand-authored rows.

**FR-015 falls out of the frozen taxonomy.** The score bundle's `failure_code`
enum already carries `service_reroute`, documented in that contract as "the code
for platform alias re-pointing". `failure_code_response["service_reroute"] =
"non_scorable"` is therefore the whole of FR-015: a platform-initiated route
change is classified non-scorable by the map, and because it never yields
`escalate` it can never be counted as a policy escalation. No new signal member
is coined, so FR-009 holds.

**Numeric triggers are separate and explicit.** Retry count and raw-token or
duration budget thresholds are not enum-valued, so they are declared as
`budget_trigger` entries — a bound member name drawn from the frozen budget
field set, a comparison direction, and a threshold — rather than being folded
into the enum maps. They feed the same response enum.

**Clean pass, for the de-escalation streak.** Defined against already-frozen
members, per the spec's Assumptions: `terminal_state == "completed"` and
`failure_code == "none"` and `retries == 0` and no budget trigger fired. This is
the streak input and is deliberately not a member of the response maps — a clean
pass produces no response, it advances a counter that is read only at the next
objective boundary.

---

## D6. Escalation ladder well-formedness

**Decision.** `escalation_ladder` is an ordered array of `candidate_route_id`
strings on the adaptive control record, checked fail-closed against the bound
successor-capability freeze by four rules that map one-to-one onto FR-011a:

1. **Binding and membership** — exactly one `candidate_freeze_id` +
   `freeze_digest` pair is bound; every ladder entry resolves to the
   `candidate_route_id` of one `admitted_tuples` member.
2. **Totality** — the ladder is a permutation of the admitted set: every tuple
   exactly once, no duplicate, no omission. An unreachable route is removed at
   the freeze through `excluded_tuples` and its closed `reason` enum, never by
   omission.
3. **Within-model order is derived** — for any two entries sharing a `model`,
   relative ladder position must agree with the frozen closed effort ladder
   `["low", "medium", "high", "xhigh", "max"]`, read live from the freeze
   schema's `#/$defs/tuple/properties/effort/enum` rather than restated.
4. **Cross-model order is authored** — an entry whose `model` differs from its
   predecessor's must carry a non-empty rationale, recorded as a category 7
   decision-semantics entry in the twin-handoff record.

Rank is array position and nothing else. Index `i + 1` is the next-higher
qualified route; index `i - 1` is the de-escalation target; the final entry has
no successor and the first has no predecessor.

**Rationale.** The frozen `tuple` schema types `model` as an unordered
`{"type": "string", "minLength": 1}` while `effort` is a closed ordered enum.
Any rule deriving cross-model rank from a model identifier would be inventing an
order the frozen contract does not carry. Rule 3 is derivable and therefore
checked; rule 4 is a judgment and therefore must be recorded. FR-011's warning
about `admitted_tuples` array order is honored by never reading that array's
order for anything.

**Ceiling and floor behavior.** An escalation signal at the final entry records
no escalation, refuses wrap-around, and terminates the objective under the FR-014
retry and cancellation bounds. A de-escalation evaluation at index 0 is a no-op.

---

## D7. Orchestration aggregation across eight dimensions

**Decision.** The aggregate over the parent and every automatically spawned
child is defined per dimension, with no dimension left to the implementation:

| Dimension | Combining rule | Source requirement |
|---|---|---|
| `input_tokens` | sum | FR-016 |
| `cached_input_tokens` | sum | FR-016 |
| `output_tokens` | sum | FR-016 |
| `duration_ms` | sum | FR-016 |
| `retries` | sum | FR-016 |
| `compactions` | sum | FR-016 |
| `terminal_state` | worst-wins fold over `terminal_state_severity` | FR-016a |
| `acceptance` | parent objective's oracle result; floored to 0 whenever the aggregate terminal state is not `completed`; never summed, averaged, or per-child | FR-016b, FR-016c |

`terminal_state_severity` is restated in full on the orchestration control record
as `["completed", "failed", "timed_out", "cancelled", "budget_exhausted",
"abandoned"]`, is hash-relevant, and is validated **set-equal** — not
order-equal — against the frozen score-bundle terminal-state enum.

**Rationale.** Set-equality is the precise check FR-016a demands: it catches an
unmapped member while surviving a future reordering of the mirrored enum, which
order-equality would turn into a silent CAR-004 verdict change. Worst-wins rather
than parent projection prevents the artificial-cheapness failure where a run
sprays failing children, charges their cost, and still reports `completed`.
Children that failed, timed out, or were cancelled still contribute their consumed
resources to the six additive dimensions; a zero-child run folds to the parent's
own values and is a valid row, not an error.

**The severity rank is aggregation-only.** FR-021 keeps terminal state
categorical and unordered for comparison. The two halves are recorded as two
separate category 7 decision-semantics entries in the twin-handoff record so a
mirroring implementation cannot collapse them into one ordering and start reading
severity during comparison.

---

## D8. Dominance evaluation order and the margin map

**Decision.** Three stages, in a fixed order, implemented as three functions so
the order is structural rather than conventional:

1. `check_eligibility_floors()` — FR-019. No floor cleared, no verdict, whatever
   the resource numbers say.
2. `pareto_verdict()` — FR-020. The frozen environment-independent Pareto rule
   over the eight dimensions. No weighted scalar ranking exists anywhere in the
   module.
3. `materiality_filter()` — FR-021 and FR-021a. Applied only when stage 2 returns
   candidate dominance.

The per-component margin map is total over all eight dimensions: four
margin-eligible at a relative margin of `0.10` — `input_tokens`,
`cached_input_tokens`, `output_tokens`, `duration` — and four no-worse-only with
a recorded reason — `retries`, `compactions`, `acceptance`, `terminal_state`.

**Verdict map, total over the frozen outcomes.**

| Stage 2 result | Stage 3 result | Verdict |
|---|---|---|
| candidate dominance | at least one margin-eligible component clears | `dominant` |
| candidate dominance | no component clears | `not_dominant` |
| candidate dominance | every margin-eligible component is `margin_not_computable` | `not_dominant` |
| comparator dominance | not reached | `not_dominant` |
| tie, mixed, or uncertain | not reached | `inconclusive` |

**Rationale.** FR-021a requires that the margin never replace the Pareto rule.
Separating the stages makes that a call-graph property. The four excluded
dimensions are excluded for stated reasons rather than by omission: retries and
compactions are small-integer counts at which a 10% relative change is not
representable and which the frozen analysis plan already governs with absolute
p95 ceilings; acceptance is higher-is-better and participates through the
no-worse half only, so a control that is cheaper because it gave up can never
read as materially dominant; terminal state is categorical, so a percentage on it
is undefined by construction.

**Zero-denominator guard.** The denominator is the comparator's value (FR-021c).
A zero comparator value records `margin_not_computable`, contributes nothing to
the "at least one cleared" disjunction, and is never read as an infinite or 100%
improvement. On the four margin-eligible dimensions this is a fail-closed guard
rather than a live branch: all four are integers with a frozen minimum of 0, and
a component can be strictly better only when the comparator exceeds the
candidate, which makes the denominator positive. It is implemented anyway,
because a guard that never fires is the correct shape for an arithmetic
impossibility.

**Dimension-name projection.** Verified against the frozen contracts: the score
bundle's `resource_vector` carries `duration_ms` while the analysis plan's
`pareto_policy.dimensions` carries `duration`; the other seven names are
identical. The projection is therefore a single frozen rename, `duration_ms` to
`duration`, declared explicitly in the comparison contract (FR-021e). The Pareto
rule refuses any key outside its eight dimensions, so an unprojected vector
raises rather than silently comparing seven dimensions.

---

## D9. Confidence method and multiplicity position

**Decision.** Adopted from the frozen CAR-003 analysis-plan instance rather than
invented: alpha `0.05`, confidence level `0.95`, one-sided lower confidence bound
at that level, clustered by role with
`cluster_robust_sandwich_variance_by_role`. A margin clears when the **lower
bound** on the component's relative improvement is at least `0.10`, not when the
point estimate is (FR-021d).

CAR-011's three predeclared secondary control arms form one new multiplicity
family, `secondary_control_arm_family`, declared **in the comparison contract**,
beside and disjoint from the three frozen FR-050 families and the guardrail
family. Adjustment: `holm_bonferroni_within_the_secondary_control_arm_family` at a
family-wise alpha of `0.05`. The family draws no alpha from the primary
comparison.

**Rationale.** A bare point estimate would let noise trigger a messaging
restriction and would leave FR-022's "statistically uncertain" branch with no
mechanism. The frozen analysis plan's `multiplicity_declaration` is closed at
three families with `additionalProperties: false`, so adding a fourth there would
edit a mirrored member (FR-005). Standing a new family up in the consuming
contract is exactly the precedent the guardrail family set — an error-control
concern belonging to none of the three, declared where it is used. Drawing no
alpha from the primary comparison is justified because a control-arm result can
only **restrict** release wording under FR-024 and can never license a
qualification claim.

**Replay stand-in.** Where a deterministic replay fixture exercises the rule on a
single synthetic row there is no sampling distribution, so the point estimate
stands in for the bound and the row remains non-outcome-bearing under FR-027. The
fixture labels that stand-in explicitly so a reader never mistakes a replay row
for evidence.

---

## D10. Verdict-to-claim-class mapping

**Decision.** A total three-entry map in the comparison contract:

| Verdict | Permitted claim class | Forbidden |
|---|---|---|
| `dominant` | `measured_improvement_over_previous_static_baseline` | `efficient`, `optimal`, `best_measured` |
| `not_dominant` | `no_comparative_claim` | all three above |
| `inconclusive` | `no_comparative_claim` | all three above |

Claim classes and verdict states are both closed enums, and the map is validated
total and single-valued over the verdict enum.

**Rationale.** FR-024 and design-concept Q9. A machine-readable mapping is what
lets CAR-011's release-packet validation bind mechanically instead of relying on
review judgment, which AC-2.16 exists to push out of review. `not_dominant` and
`inconclusive` share a claim class but are kept as separate verdict members
because they mean different things — evidence sufficient and bar not cleared,
versus evidence insufficient — and collapsing them would erase FR-022's
distinction.

---

## D11. Smoke bounds, authentication, and cache isolation

**Decision.** `smoke_bounds` is a registry-level object using the already-frozen
budget member names, shared by all three controls:

| Member | Value | Note |
|---|---|---|
| `max_attempts` | 5 | five non-reserved objectives |
| `max_candidates` | 1 | one repetition |
| `max_confirmation_entries` | 0 | no confirmation entry may be consumed |
| `max_duration_seconds` | 1800 | 30-minute wall clock |
| `max_input_tokens` | 800000 | inside the raw-token identity |
| `max_cache_read_tokens` | 150000 | inside the raw-token identity |
| `max_output_tokens` | 50000 | inside the raw-token identity |
| `max_cache_write_tokens_by_ttl_class` | `{ephemeral_5m, ephemeral_1h}` | outside the identity; diagnostic only |

`800000 + 150000 + 50000 == 1000000` is asserted as a machine-checked identity
(SC-017). Cache write stays outside it because cache creation is diagnostic-only
and never a Pareto dimension, exactly as the frozen budgets already treat it.

**Authentication.** `authentication_mode` is the already-frozen enum member from
`successor-capability-freeze.schema.json` (`subscription | api_key`). The smoke
record must carry `subscription`, and `run-control-smoke.py` refuses to seal a
record carrying `api_key`. This follows PRD AC-2.19 as amended 2026-07-26, which
forbids any supported path requiring an API key without qualification, and the
design concept's 2026-07-27 Revisions section, which corrects the original Q10 and
Q15 recommendation. The roadmap's contrary wording at lines 159-160, 359-360, and
1110 is stale and was not followed.

**Not an experiment-policy instance.** The smoke MUST NOT be serialized as an
instance of the frozen `experiment-policy.schema.json`. That document's `allOf`
branches force a `partition_type` and then require either an analysis-plan
binding or a calibration-protocol binding, both of which CAR-004 is barred from
creating. The bounds ride the frozen **member names** without riding the frozen
**document**.

**Cache isolation.** FR-032 reuses the frozen `per_arm_ephemeral_root` rule the
CAR-003 experiment policy already declares: each control's smoke runs under its
own ephemeral root, so no control's smoke can warm another arm's cache. The
operator procedure in `quickstart.md` states the ordering, and the smoke record
carries the root identity so a violation is visible in the record rather than
only in the operator's memory.

**Per-run output.** Written under `tests/speckit-pro/layer6-efficiency/results/`,
which the existing layer6 `.gitignore` already excludes with `results/*`. No
`.gitignore` edit is needed and no smoke output is committed, satisfying FR-033.

---

## D12. Twin-handoff record format and machine check

**Decision.** `docs/ai/specs/.process/CAR-004-twin-handoff.md` carries prose for a
human reader plus exactly two fenced ` ```json ` blocks that the check parses:

1. **Mirror membership** — an array of entry objects, each with `category` (1–8),
   `member_id`, `contract_id`, `hash_relevant`, `requirement`, `rationale`, and
   exactly one `mirror_obligation` from the closed set `mirror_required`,
   `sanctioned_divergence`, `car_owned`.
2. **Sanctioned divergences** — an array closed at exactly one entry, the
   three-control composition.

`tests/speckit-pro/unit/test-twin-handoff-completeness.py` re-derives categories 1
through 6 from the committed schema documents and frozen instances, diffs both
directions against block 1, and fails on any difference. It also rejects an entry
with no obligation or more than one, a second sanctioned divergence, a divergence
classified against a category 1–6 or category 7 member, and a non-empty
reconciliation candidate list at publication (FR-036a).

**Rationale.** FR-034a requires machine re-derivation rather than attestation.
One structured block is the simplest total parse: a Markdown table would need a
bespoke parser, and carrying both a table and a JSON block would invite the two
to drift, which is the failure the check exists to catch. Categories 7 and 8 are
authored, not derived — they are the decision semantics and required guard
behaviors that add no schema member, which is precisely why CAR-003's
direction-of-preference rule escaped its schema-shaped handoff and became an open
twin gap.

**The derivation is not a lib module.** It has exactly one caller, so under YAGNI
it lives in the test file. The test filename is durable and carries no spec ID,
satisfying FR-034a's naming constraint.

**Publication state.** At publication the reconciliation candidate list is
explicitly empty and says so: G56R-004 has not started, so no member can yet be
declared unmirrorable. The record states its publication date and the reference
by which the G56R-004 owner was notified (FR-037a), and is not a hash-relevant
input to any content address, so a twin response recorded in it can never
re-identify a comparator frozen before the answer is known.

---

## D13. Suite registration and generated docs

**Decision.** Register the three unit test modules in
`tests/speckit-pro/suite-manifest.json` under Layer 4 with `"baseline": null`,
matching every CAR-003 unit registration. Do **not** register
`run-control-smoke.py`: it is operator-only and live, exactly like the existing
`run-calibration-pilot.py`, which is unregistered and covered instead by the
deterministic `test-calibration-pilot-driver.py` at Layer 4. CAR-004 follows that
precedent — the smoke script's bound-checking and record-sealing logic is covered
deterministically from `test-policy-control-contracts.py`, with no live call.

**Generated docs.** New `.py` files under `tests/speckit-pro/` stale the generated
`docs-site/src/content/docs/reference/tests.md`, and CI's validate-docs job runs
`reference:check` against it. Regeneration is a required step before the PR, run
once per worktree as `pnpm --dir docs-site install` then
`pnpm --dir docs-site reference:generate`.

---

## Open Risks

Stated rather than hidden. None of these blocks implementation.

1. **The environment contract has no `contracts-claude/` mirror.** The unpinned
   control must bind the pinned parent-session model and effort by `{id, digest}`
   against whatever the CAR-003 harness actually reads. Confirm the exact
   identity during implementation before freezing; a wrong binding fails closed
   as a digest mismatch rather than passing silently, so the failure mode is
   safe, but it will stop the build until corrected.
2. **The reserved partition's type is a forecast about CAR-011.** D4 explains why
   `integrated_confirmation` is the right member of a set CAR-004 may not extend,
   and why a later change is a new entry rather than an edit. It remains a
   judgment made before its consumer exists.
3. **Review volume.** Roughly 2,000–2,400 changed lines, mostly declarative JSON.
   The plan-phase estimator reads zero production files and passes, and the
   PR-time diff-mode gate is the authoritative check. Recorded so the size is not
   a surprise at review time.
4. **The 1,000,000-token and 30-minute smoke ceilings keep the moderate
   confidence at which they were recorded.** Serializing them does not upgrade
   it. They are hash-relevant to the registry document, so revising them is a new
   registry version rather than an edit.
5. **Enum drift is caught, not prevented.** Reading the frozen enums live from
   `score-bundle.schema.json` means a future joint change to a mirrored enum will
   fail CAR-004's totality checks rather than silently changing a verdict. That
   is the intended behavior, and the failure will look like a CAR-004 break when
   its cause is upstream. The unit tests name the frozen source in their failure
   messages so the next reader is not misled.

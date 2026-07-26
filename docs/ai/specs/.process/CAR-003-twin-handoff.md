# Handoff to `g56r-003-evaluation-runner-scoring` (Codex twin)

**From**: `car-003-evaluation-runner-scoring` (PR #385, 20/20 checks green, 4143/4143 tests)
**Written**: 2026-07-25
**Twin state at time of writing**: 12 unpushed commits, 22 untracked paths, 3 modified
tracked files. Nothing below has been applied — the twin could not be edited.

Everything here was verified by reading the twin worktree, not inferred from the
Claude side. Two of the four premises I was handed turned out to be wrong; both
corrections are stated in place.

---

## 0. Blocking precondition: the twin's work is unpushed and unverifiable

**What is wrong.** `origin/main..HEAD` on the twin is 12 commits (not 10), and
`git ls-files --others --exclude-standard` returns 22 paths, including two harness
modules (`tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py`,
`qualification_scoring.py`), five test files (`tests/speckit-pro/unit/test-codex-*.py`),
an entire `tests/speckit-pro/layer6-efficiency/fixtures-codex/` tree, and a
repo-level shared contract (item 4).

**Why it matters.** None of items 1-4 can be validated in CI, and the shared-path
collision in item 4 cannot be resolved by either side, until the twin's state is
committed and pushed. A reconciliation agreed against an uncommitted working tree
is not an agreement.

**Exact change needed.** Commit and push the twin branch before applying anything
else in this handoff. Then re-verify item 4 against the pushed ref, because its
resolution depends on which files actually landed.

---

## 1. `experiment-policy.schema.json` contradicts FR-037 — RESOLVED on the twin

**Status: RESOLVED 2026-07-25 in twin commit `06a77dd3` ("fix(g56r-003): break
calibration policy cycle"), PR #386.** No further twin action required for this
item. The history below is retained because the correction sequence matters.

The twin's triage at `6f7daf63` confirmed the contradiction by execution and
refuted the original "unrunnable pilot" impact claim — its qualification runner
checks selected bindings rather than validating the closed schema, so nothing was
blocked. Remediation then landed both fixes:

- Phase-1 contract: `analysis_plan_binding` removed from the base `required` set,
  `calibration_protocol_binding` added, and an exhaustive `if/then/else` keyed on
  `partition.qualification_eligible`.
- Runtime contract: the calibration-only resolution, swapping plan bindings for
  protocol bindings at **both** the policy and assignment-pair levels — the pair
  level was not named in the handoff and the twin caught it independently.
- New `calibration-protocol.schema.json` at both layers, carrying no margins,
  sample sizes, or terminal thresholds, `additionalProperties: false`.
- Both analysis-plan contracts now bind the protocol the plan was derived from.

Independently re-verified here against the twin's own contract validator, seven
cases including three the twin did not report — most importantly an **ineligible
policy binding the analysis plan**, the original cycle, now rejected as a
prohibited shape. The ordering constraint was honored: the contradiction fix
landed first and the enforcement gap remains deferred.

**The original framing in this item overstated the impact.** It is kept below for
the record, not as current guidance.

**What is wrong.** `analysis_plan_binding` sits in the top-level `required` array
unconditionally, there is no `calibration_protocol_binding` property at all, and
the object is `additionalProperties: false`. A calibration policy is therefore
doubly blocked: it cannot omit the analysis-plan binding, and it cannot substitute
a calibration-protocol binding. The twin session confirmed this by validating a
`qualification_eligible=false` policy carrying no analysis plan against the
committed schema:

```text
SPEC_SCHEMA_RESULT=REJECTED
VALIDATION_OUTPUT=$ is missing required contract fields: ['analysis_plan_binding']
```

**This affects TWO schemas, not one.** The original report named only the
spec-scoped design artifact, and the twin's triage checked only that one. The same
unconditional `required` entry — with no `allOf`/`if`/`anyOf`/`oneOf` branches — is
also present in the twin's *runtime harness* contract:

| File | Layer | Validated by |
| ---- | ----- | ------------ |
| `specs/g56r-003-evaluation-runner-scoring/contracts/experiment-policy.schema.json` | SpecKit Phase-1 design artifact | design review only |
| `tests/speckit-pro/layer6-efficiency/contracts/experiment-policy.schema.json` | runtime contract (`$id .../g56r-003/runtime/…`) | `tests/speckit-pro/unit/test-codex-qualification-contracts.py` |

Both need the fix. The runtime copy is the load-bearing one — a live contract test
already schema-validates against it.

**Why the pilot is NOT blocked today.** `run-codex-qualification.py` never
validates a policy against either schema; it checks selected bindings through
`_require_policy_bindings`. The twin session removed `analysis_plan_binding` from
the policy and from every assignment pair, and the calibration path still exited 0
with `"status":"calibration_ready"`. The circularity is real in the contract text
but currently unreachable through the executing code.

**Why it still has to be fixed, and in what order.** The twin's triage identified
the reachable finding as the inverse of this one: the pilot's experiment-policy
input bypasses full closed-schema, version, digest, comparison-set, and
analysis-plan validation. That enforcement gap is precisely what masks the
contradiction. **Closing the gap first would convert a latent defect into an active
blocker** — the moment the pilot validates the full closed schema, no conforming
calibration policy can be authored. Fix the contradiction before closing the
enforcement gap, or land both together.

**Exact change needed.** Apply the same shape CAR-003 uses, to **both** files in
the table above. Three edits per file, nothing else:

1. Remove `"analysis_plan_binding"` from the top-level `required` array. Leave the
   property definition in `properties` unchanged.
2. Add a sibling property:

   ```json
   "calibration_protocol_binding": {
     "$ref": "#/$defs/binding",
     "description": "FR-037. A calibration-partition policy binds this instead of analysis_plan_binding. The analysis plan freezes only AFTER calibration, so requiring a calibration policy to bind it is a circular dependency that makes the calibration pilot unrunnable. The calibration protocol carries no margins, sample sizes, or terminal thresholds; the frozen analysis plan later references it as its calibration binding."
   }
   ```

3. Add a top-level `allOf` with the two paired branches, keyed on
   `partition.qualification_eligible` (**not** on `partition_type`):

   ```json
   "allOf": [
     {
       "description": "FR-037. A qualification-eligible policy MUST bind the frozen analysis plan and MUST NOT carry a calibration protocol binding.",
       "if": {"properties": {"partition": {"properties": {"qualification_eligible": {"const": true}}}}, "required": ["partition"]},
       "then": {"required": ["analysis_plan_binding"], "not": {"required": ["calibration_protocol_binding"]}}
     },
     {
       "description": "FR-037. A calibration policy MUST bind the calibration protocol and MUST NOT bind the analysis plan, which does not yet exist when calibration runs.",
       "if": {"properties": {"partition": {"properties": {"qualification_eligible": {"const": false}}}}, "required": ["partition"]},
       "then": {"required": ["calibration_protocol_binding"], "not": {"required": ["analysis_plan_binding"]}}
     }
   ]
   ```

**Key the branches on `qualification_eligible`, not `partition_type`.** The two
branches must be exhaustive. Keying on `partition_type == "calibration"` alone
leaves a non-calibration ineligible partition (`screening`/`selection` with
`qualification_eligible: false`) bound to neither artifact — failing open on the
exact invariant the requirement exists to enforce. CAR-003 FR-037 records this
reasoning; mirror it into the twin's FR text as well as the schema.

**Scope guard — do not over-apply.** CAR-003's copy of this file also carries
`scorer_family_exclusion` (FR-047), `assignment_policy.cache_isolation`,
`rerun_policy.classification_timing`, and a different budget shape
(`max_cache_write_tokens_by_ttl_class` + `max_cache_read_tokens` versus the twin's
`max_cached_input_tokens`). Those are separate Claude-side requirements and are
**not** part of this fix. Change only the three items above.

**Also update the twin's FR-037 prose**, or the schema will contradict the spec it
implements.

**CAR-side reference state — no equivalent gap here.** CAR-003 does not carry the
enforcement gap that masks this defect on the twin, because the rule lives on the
executing path rather than in schema validation alone:

- `tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py` enforces the
  substitution in code — `required_plan_binding(qualification_eligible)` selects the
  required key and `_plan_binding_findings` rejects binding both, binding neither,
  or binding the wrong artifact for the eligibility. `run-calibration-pilot.py` runs
  through that library, so the rule is reachable at execution.
- `tests/speckit-pro/unit/test-experiment-policy-partitions.py` reads the
  spec-scoped schema directly (`CONTRACT_ROOT = specs/car-003-evaluation-runner-scoring/contracts`)
  and asserts the two paired branches literally, so the contract and the library
  cannot silently drift apart.
- CAR-003 has no runtime-harness copy of this schema to keep in sync; the shared
  `tests/speckit-pro/layer6-efficiency/contracts/` directory holds only
  `capability-freeze`, `marker-checkpoint`, and `treatment-record`.

Verified 2026-07-25: `test-experiment-policy-partitions` 90/90 passed, including
the transitive policy-edge case. If the twin closes its enforcement gap, mirroring
this two-place arrangement (library enforces, test pins the schema to the library)
is the shape that makes the contradiction impossible to reintroduce unnoticed.

---

## 2. FR-058 (direction of preference) exists only on the Claude side

**Status: VERIFIED.** The twin's spec tops out at FR-038 — there is no FR-058. The
twin's FR-018 (line 232) names the eight dimensions and declares no direction for
any of them.

**What is wrong.** Both platforms agree on *which* eight dimensions are compared
and neither Pareto policy states *which way is better* on the Codex side.

**Why it matters.** "No worse on every dimension" is undecidable without a
direction. Two conforming implementations can reach opposite verdicts on identical
evidence — a candidate using fewer output tokens is better on the Claude side and
undefined on the Codex side. That is precisely the cross-platform logical
divergence the parity commitment forbids, and it would surface as contradictory
qualification results rather than as a validation error.

**Exact change needed.** Mirror this. CAR-003 FR-058, verbatim:

> **FR-058**: Each of the eight decision-bearing dimensions MUST carry an explicitly declared direction of preference, because "no worse on every dimension" is not decidable without one and two conforming implementations could otherwise reach opposite verdicts on identical evidence. `input_tokens`, `cached_input_tokens`, `output_tokens`, duration, retries, and compactions are **lower-is-better**; acceptance is **higher-is-better**; and terminal state is **categorical and not ordered** — a candidate is "no worse" on terminal state only when its terminal state equals the comparator's, and any difference in terminal state MUST make the comparison mixed rather than being silently treated as better or worse. Direction of preference is comparison **semantics**, not schema shape: declaring it adds no member to the frozen `pareto_policy` surface and therefore introduces no structural divergence. The Codex twin currently leaves the same direction undeclared, so this wording MUST be mirrored there verbatim; until it is, the two platforms agree on which dimensions are compared while only this side states how.

**Two mechanical notes on "verbatim":**

- The twin has no FR-058 slot. Mirror the **body** under the twin's next free ID
  (FR-039) or as an appended paragraph inside the twin's FR-018 — the requirement
  is that the normative content match, not the number. Record the crosswalk
  (`G56R-003 FR-039 ≡ CAR-003 FR-058`) so later parity checks resolve.
- The **final sentence cannot be mirrored literally.** "The Codex twin currently
  leaves the same direction undeclared, so this wording MUST be mirrored there
  verbatim" becomes self-referential nonsense on the twin. Mirror the first three
  sentences verbatim and replace the trailing sentence with its mirror image
  ("Mirrored from CAR-003 FR-058; the two platforms declare the same direction").
  Then update CAR-003's trailing sentence to record that the mirror has landed —
  until that happens, CAR-003's spec asserts something about the twin that is no
  longer true.

No schema change on either side. `pareto_policy` gains no member.

---

## 3. The FR-014 / FR-034 ruling

**Status: PREMISE CORRECTED.** The contradiction does **not** exist identically on
the twin. I read both.

- Twin FR-014 (line 228) is a single sentence: "The system MUST run deterministic
  hard gates before semantic evaluation and fail closed when required gate evidence
  is missing or failing." It authors **no** `(failure_plane, failure_code)` pair.
- Twin FR-034 (line 248) has **no** plane-by-code mapping table. It requires the
  closed fields and lists what the code taxonomy must distinguish, and stops there.

So the twin has *underspecification* where the Claude side has a *contradiction*.
The ruling therefore lands on the twin as an **addition**, not a correction. Do not
go looking for a conflicting sentence to fix; there isn't one.

### The ruling

**A missing or duplicated hard-gate result is recorded as
`failure_plane=evidence_boundary`, `failure_code=required_evidence_missing`.**
FR-014's authored pair `(schema, required_evidence_missing)` is withdrawn. FR-034's
total mapping stands unchanged.

### Why this way, in the order the evidence carries weight

1. **FR-034's mapping is total and already files this code.** Its table maps
   `unclassifiable_attrition`, `sensitive_evidence_violation`, and
   `required_evidence_missing` to `evidence_boundary`. It covers every member of
   both closed sets. FR-014 asserts one pair against a complete function; the
   function wins.
2. **CAR-003's own FR-051 already uses the evidence_boundary pairing in prose**: an
   environment that cannot be observed at all "is an evidence-completeness failure
   recorded on the evidence-boundary plane with the existing closed
   `required_evidence_missing` code". Ruling for FR-014 would leave the spec
   pairing the same code with two different planes in two requirements.
3. **The implementation already does this for the analogous case.** In
   `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py`:
   `MISSING_LEAK_EVIDENCE_FAILURE = ("evidence_boundary", "required_evidence_missing")`
   — a blinding leak check that never ran is missing evidence, not a malformed
   bundle. A hard gate whose result is absent is the same shape of fact.
4. **FR-029's plane separation forbids the alternative.** A failure in one plane
   must never be recorded in another. An absent gate result is an evidence-
   completeness fact; filing it on the `schema` plane records an evidence failure
   on the schema plane, which is the exact cross-plane recording FR-029 exists to
   prevent.
5. **It coins nothing.** Both members already exist. I diffed all four closed enums
   between `specs/car-003-evaluation-runner-scoring/contracts/score-bundle.schema.json`
   and the twin's `specs/g56r-003-evaluation-runner-scoring/contracts/score-bundle.schema.json`:
   `score_disposition`, `failure_plane`, `failure_code`, and `invalidation_reason`
   are **identical on both sides**. The ruling requires zero schema change on either
   platform.

The rejected alternative, for the record: to land on the `schema` plane at all you
would need a code that maps there — only `schema_invalid` or
`binding_digest_mismatch` do — and neither means "required evidence absent". That
is exactly what the current fail-closed path produces, and it destroys the
distinction between a malformed bundle and a bundle whose gate never reported.

### The consequence that must not be missed

This is **not** cosmetic. In `claude_score_bundle.py`, `bind_disposition` returns
`gate_failed` when the code is in `GATE_STAGE_CODES` and `non_scorable` otherwise.
`schema_invalid` **is** in that set; `required_evidence_missing` **is not**.

- Today (fail-closed to `(schema, schema_invalid)`): disposition is `gate_failed`.
- Under the ruling (`(evidence_boundary, required_evidence_missing)`): disposition
  is `non_scorable`.

Both platforms must adopt the same disposition or pooled analysis will disagree
about the terminal category of a missing gate. **Verify this explicitly on the
Codex side** rather than assuming the plane change carries the disposition with it.

### Exact changes

**Twin side (additions):**

1. Add FR-034's total plane-by-code mapping to the twin's FR-034, verbatim from
   CAR-003: `none` → `none`; `treatment_misdelivery`, `service_reroute`,
   `mandatory_telemetry_missing`, `treatment_infrastructure_failure` → `treatment`;
   `fixture_invalid`, `fixture_stale`, `fixture_partition_invalid`,
   `fixture_oracle_invalid` → `fixture`; `scorer_invalid`, `scorer_stale`,
   `scorer_calibration_missing` → `scorer`; `ballot_missing`, `ballot_non_blind`,
   `ballot_provenance_incomplete`, `ballot_rubric_stale` → `ballot`;
   `adjudication_disagreement_unresolved`, `adjudicator_invalid`,
   `adjudicator_stale`, `adjudicator_reused_primary_scorer` → `adjudication`;
   `candidate_failed`, `candidate_timed_out`, `candidate_cancelled`,
   `candidate_budget_exhausted`, `candidate_abandoned` → `candidate`;
   `transient_harness_failure`, `infrastructure_failure` → `infrastructure`;
   `unclassifiable_attrition`, `sensitive_evidence_violation`,
   `required_evidence_missing` → `evidence_boundary`; `partition_mismatch`,
   `partition_not_eligible`, `cross_partition_reuse` → `partition`;
   `schema_invalid`, `binding_digest_mismatch` → `schema`. Include the fail-closed
   rule: a pair not in the table fails closed to `(schema, schema_invalid)`.
2. Add to the twin's FR-014: "A missing gate result MUST fail closed with
   `failure_plane=evidence_boundary` and `failure_code=required_evidence_missing`
   rather than being read as a pass."
3. Implement the pairing and confirm the resulting disposition is `non_scorable`.

**Claude side (corrections, to land in the same joint change):**

1. `specs/car-003-evaluation-runner-scoring/spec.md` FR-014 — change
   "`failure_plane=schema`" to "`failure_plane=evidence_boundary`".
2. `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py` — set
   `MISSING_GATE_DECLARED_FAILURE = ("evidence_boundary", "required_evidence_missing")`
   (currently `("schema", "required_evidence_missing")`).
3. Same file — replace the fourth module-docstring bullet ("FR-014 and FR-034
   disagree about the missing-gate pair…") with the ruling. The bullet exists to
   keep the conflict visible; once ruled, leaving it in place misinforms.
4. `tests/speckit-pro/unit/test-score-bundle-adjudication.py` — the assertions at
   roughly lines 783-792 encode the old reading in a comment ("FR-014 authors the
   missing-gate pair as (schema, required_evidence_missing)"); update the comment
   and keep both `normalize_failure` assertions, which remain true. Re-check the
   assertion near line 198 (`verdict.failure_code == "required_evidence_missing"`,
   still valid) and the `schema_invalid` fixture near line 826.

No schema edits. `specs/car-003-evaluation-runner-scoring/contracts/score-bundle.schema.json`
is a parity mirror and gains no member.

---

## 4. Shared-contract collision at `tests/speckit-pro/layer6-efficiency/contracts/`

**Status: VERIFIED, and it is a three-way problem, not the two-way one described.**

### What is actually there

**On the twin, at the repo-level shared path:**

| File | Git state |
|---|---|
| `successor-capability-freeze.schema.json` | **tracked**, committed in `a9bdfe0e`, unpushed. Not present on `origin/main`. |
| `role-corpus.schema.json` | **untracked** |

**On the twin, also at its spec-scoped path** (`specs/g56r-003-evaluation-runner-scoring/contracts/`):
both files exist again — and they are **not the same documents**.

| Contract | Twin shared-path copy | Twin spec-scoped copy |
|---|---|---|
| successor freeze | title "Successor Capability **Publication Request**", `schema_version: "successor-capability-freeze.v1"`, requires `predecessor_candidate_freeze_id`, `client_identity_id`, `account_identity_id`, `source_manifest_digest`, `source_refresh_set_digest`, `runtime_capability_snapshot_id`, `catalog_capture`, `diagnostic_capture_digest`, `successor_mutable_fields`, `diagnostics` | title "Successor Capability **Freeze**", `schema_version: "1.0.0"`, requires `candidate_freeze_id`, `freeze_digest`, `historical_freeze_binding`, `source_ledger_binding`, `runtime_snapshot_binding`, `normalization_map_digest`, `admitted_tuples`, `excluded_tuples`, `authority_failures`, `invalidation_triggers` |
| role corpus | `schema_version: "role-corpus.v1"`, adds `corpus_version`; per-role `optional_helper`, `source_binding`, `fixture_binding`, `partition_binding`, `acceptance_oracle`, `independent_review`, `route_bindings` | `schema_version: "1.0.0"`; per-role `source_digest`, `fixture_digest`, `sandbox`, `acceptance_oracle_digest`, `independent_review_binding`, `candidate_route_bindings` |

**Both copies of each contract carry the same `$id`** —
`https://racecraft.dev/schemas/g56r-003/role-corpus.schema.json` and
`.../successor-capability-freeze.schema.json`. Two structurally different documents
claiming one `$id` is a resolver collision **internal to the twin**, present before
the Claude side enters the picture at all.

**On the Claude side:** CAR-003 added **nothing** to the shared path.
`git ls-files tests/speckit-pro/layer6-efficiency/contracts/` returns exactly the
three pre-existing files (`capability-freeze`, `marker-checkpoint`,
`treatment-record`), and I confirmed all three are byte-identical across the two
worktrees by SHA-256. CAR-003's own copies are spec-scoped under
`specs/car-003-evaluation-runner-scoring/contracts/` with `$id`s under
`.../car-003/...`, so there is no `$id` clash between platforms today.

### What the collision precisely is

Three distinct problems, in dependency order:

**(a) Twin-internal duplicate `$id`.** Two different documents, one `$id`, for each
of the two contracts. This is a defect regardless of how the cross-platform
question is resolved, and it blocks every option below.

**(b) The shared path means one source of truth for both platforms.** The three
files already there are byte-identical across worktrees; that is what "shared"
means here. If the twin lands `role-corpus.schema.json` (and keeps
`successor-capability-freeze.schema.json`) there while CAR-003 keeps its
spec-scoped copies, the same contract has two sources of truth with no mechanism
reconciling them — and they have already drifted.

**(c) The placement itself contradicts the ratified decision, on both sides.**
CAR-003 FR-012: "The role-corpus contract is authored by this spec mirroring the
Codex twin's committed **spec-scoped** schema, which is a parity reference rather
than a repo-level shared file." CAR-003 FR-014 says the same for the score bundle.
That wording was mirrored *from* the twin's own committed decision. Landing these
at the shared path reverses it unilaterally.

And the Claude copies genuinely cannot be byte-identical to the Codex ones as
written: CAR-003's role corpus renames `sandbox` → `mutation_contract` (FR-012) and
adds an `executable: false ⟹ no candidate_route_bindings` `allOf`; its successor
freeze adds `admitting_surface` and `authentication_mode` (FR-002, FR-042). Those
are requirement-driven, not incidental.

### Options

**Option 1 — keep both contracts spec-scoped (recommended).** Revert the shared-path
`successor-capability-freeze.schema.json` out of `a9bdfe0e`; do not add
`role-corpus.schema.json` there. Reconcile the twin's two divergent versions of each
contract into one spec-scoped file per contract, which also fixes (a). Matches the
ratified FR-012/FR-014 placement, requires no Claude-side change, keeps `$id`s
disjoint, does not reopen PR #385. The parity obligation stays what both specs
already say it is: logically identical spec-scoped mirrors.

**Option 2 — promote to the shared path, byte-identical.** Requires the Codex side
to adopt `mutation_contract`, `admitting_surface`, `authentication_mode`, and the
`executable` conditional in the same change; requires CAR-003 to delete its
spec-scoped copies and re-point its harness; requires amending FR-012 and FR-014 on
both sides first, since both currently state the opposite. This is a joint
cross-platform change of the FR-049 class and it reopens PR #385. Choose it only if
there is a reason to want one enforced file that the parity-mirror arrangement
does not give you.

**Option 3 — shared intersection plus per-platform extensions via `$ref`/`allOf`.**
Lowest churn in principle, but it introduces a two-layer contract shape neither
spec describes, and `additionalProperties: false` on the shared layer makes the
composition awkward and easy to get subtly wrong. Not recommended without a
deliberate spec change on both sides.

### Ordering

Fix (a) first — it is twin-internal and independent of which option is chosen.
Then commit and push (item 0). Then decide between the options; the decision must
be recorded on both specs because both currently assert the spec-scoped placement.

---

## Summary of what the Claude side owes

| Item | Claude-side action | Blocks the twin? |
|---|---|---|
| 1 — experiment policy | none (already fixed) | no |
| 2 — FR-058 | update FR-058's trailing sentence once the mirror lands | no |
| 3 — FR-014 ruling | four edits listed above, in the same joint change | yes — must land together |
| 4 — shared contracts | none under Option 1; substantial under Option 2 | depends on option |

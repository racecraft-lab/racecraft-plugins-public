# Error Handling Checklist: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Purpose**: Requirements-quality audit of the error-handling surface — scenario
totality against the mandated families, the ordering between structural rejection
and the route walk, diagnostic emission determinism, budget-exhaustion semantics,
no-safe-route report completeness, the override interaction, and the
helper-unavailable non-event. These items test whether the *requirements* are
complete, unambiguous, and internally consistent; they do not test the
implementation, which does not exist yet.
**Created**: 2026-07-29
**Feature**: [spec.md](../spec.md)

**Depth**: Standard. **Audience**: reviewer at PR time. **Focus areas**: the five
supplied by the requester — scenario totality, structural-rejection ordering,
exhaustion semantics, no-safe-route report completeness, and helper-unavailable
non-consultation — plus six named hard checks. Clarifying questions were not asked:
the request already fixed scope, depth, and focus, and no answer would have changed
checklist content.

**Audit result**: 48 items, 29 unmet at first pass, all 29 closed in one remediation
loop. Every `[Closed]` marker cites the artifact section that now carries the
requirement; see the Resolution Log for what changed and why.

**Relationship to the data-integrity domain**: that audit ran first and closed 12
gaps. Its conclusions are taken as given and none is reopened. Two items below go
deliberately *deeper* on ground it touched rather than re-litigating it — its CHK022
confirmed that a requirement for multi-rejection determinism **exists**; this audit
asks the next question, whether the order that requirement demands is anywhere
**pinned**, and found it was not. Its code-to-action table is treated as authoritative
and is extended with a severity column, never revised.

## A. Scenario Totality Against the Mandated Families

- [x] CHK001 Is every scenario family the roadmap mandates enumerated in one place, so totality is checkable without re-reading the roadmap? [Coverage, Spec §SC-001]
- [x] CHK002 Is each enumerated family bound to a **named** corpus case rather than to a case count? [Traceability, Data Model §4]
- [x] CHK003 Are the two exact-invocation outcomes — success and failure — required as separate cases rather than one case standing for both? [Completeness, Spec §FR-009, §FR-011]
- [x] CHK004 Is the `fable` case's sub-reason fixed, so it cannot be authored against a different member of the four-member vocabulary? [Clarity, Spec §FR-006, §FR-010]
- [x] CHK005 [Closed] Is **retry** exhaustion required, or does the exhaustion requirement permit satisfying it with a probe budget alone? [Coverage, Spec §FR-028, §SC-001]
- [x] CHK006 [Closed] Are all three capped dimensions required to be exercised, or is it recorded which are declared-but-unexercised and why? [Completeness, Spec §FR-028, Data Model §4]
- [x] CHK007 Is the helper-unavailable family required to prove **both** halves — non-consultation, and non-failure of required-agent resolution? [Completeness, Spec §FR-025, §FR-025a]
- [x] CHK008 Does every mandated family's case carry a fully pinned expected report rather than a single-field assertion? [Measurability, Spec §FR-014, §FR-015]

## B. Structural Rejection Ordering and Report Validity

- [x] CHK009 [Closed] Is the ordering between structural policy validation and the route walk stated as a **requirement**, or only inside a slice-allocation table and a module-structure justification? [Clarity, Spec §FR-019c]
- [x] CHK010 [Closed] Is it stated which policy-document defects are detected before the first route is attempted and which need walk state? [Completeness, Spec §FR-019c, Data Model §5]
- [x] CHK011 [Closed] Do the two places that speak to detection timing agree, or does one require walk state for a defect the other files under a pre-pass? [Conflict, Spec §FR-019c]
- [x] CHK012 [Closed] Is the content of `attempted_routes` specified for a report whose policy was rejected before any route was attempted, and is the array's lower bound consistent with that? [Conflict, Spec §FR-019c, Data Model §3]
- [x] CHK013 [Closed] Is the `outcome` value for a structurally rejected policy stated, and does the dependent conditional-requiredness branch stay satisfiable? [Coverage, Spec §FR-019c, Data Model §3]
- [x] CHK014 [Closed] Are the remaining always-required members — `budgets`, `optional_helper`, `release_claim_eligible` — specified for a report produced with no walk? [Completeness, Spec §FR-019c, §FR-013a]
- [x] CHK015 Does each of the four policy-document defects map to exactly one code, with no defect described in prose only? [Coverage, Spec §FR-019, §FR-020, §FR-021, §FR-022, §FR-023]
- [x] CHK016 Is `unqualified_override` distinguished from the four policy-authoring defects it shares an enum with? [Clarity, Spec §FR-019, §FR-019c, §FR-025]

## C. Diagnostic Emission Determinism

- [x] CHK017 [Closed] Is it specified whether a route failing several independent checks emits one diagnostic or one per failed check, and can a reviewer derive the exact sequence the multi-rejection edge case must produce? [Measurability, Spec §FR-012b, §Edge Cases]
- [x] CHK018 [Closed] Is the inter-code emission order **pinned** — and pinned structurally — rather than only required to be deterministic? [Clarity, Spec §FR-012b, Data Model §5]
- [x] CHK019 [Closed] Is the inter-code order distinguished from the intra-diagnostic sub-reason order, so neither is mistaken for the other nor assumed to supply the other? [Consistency, Spec §FR-012b, Data Model §3]
- [x] CHK020 [Closed] Is the order of the whole `diagnostics` array specified across pre-walk violations, per-route rejections, and terminal entries? [Completeness, Spec §FR-012b]
- [x] CHK021 [Closed] Is the number of terminal `no_safe_route` diagnostics fixed at exactly one, with its array position fixed? [Measurability, Spec §FR-012b]
- [x] CHK022 [Closed] Is the relationship between the `no_safe_route` **outcome** value and the `no_safe_route` **diagnostic code** stated, given one token serves both roles? [Consistency, Spec §FR-012b]

## D. Budget Semantics and Exhaustion

- [x] CHK023 [Closed] Is the unit of counting defined for each capped dimension — what exactly increments `probe_attempts`, `retries`, and `fan_out`? [Measurability, Spec §FR-026a, Data Model §3]
- [x] CHK024 [Closed] Is `fan_out` given any meaning in a sequential first-match walk, or is it a declared field with no defined referent? [Clarity, Spec §FR-026a]
- [x] CHK025 [Closed] Is `retries` given a meaning reachable against a **static** snapshot, so retry exhaustion is provable at all? [Coverage, Spec §FR-026a, §FR-028]
- [x] CHK026 [Closed] Is the resolution code that fires on exhaustion stated per budget class, or only as an aside inside an enum-sufficiency argument? [Clarity, Spec §FR-026a]
- [x] CHK027 [Closed] Can a consumer determine **which** budget exhausted, given one terminal code is shared by all three classes? [Completeness, Spec §FR-026a, §SC-009]
- [x] CHK028 [Closed] Is counter-equals-cap sufficient to identify exhaustion, or can a walk reach its cap without exhausting it? [Ambiguity, Spec §FR-026a]
- [x] CHK029 Are declared caps and actual counts required in every report, including reports where no probing occurred? [Completeness, Spec §FR-013a, §FR-019c]
- [x] CHK030 Is the exhaustion case's declared budget value fixed, so the proof is not satisfiable by a weaker fixture? [Measurability, Spec §FR-028, §SC-009]
- [x] CHK031 Is the boundary between a budget the schema rejects and a budget the simulator bounds stated without overlap? [Consistency, Spec §FR-003a, §FR-027]

## E. No-Safe-Route Report Completeness

- [x] CHK032 Are all four mandated contents of the no-safe-route report enumerated — unresolved agent, attempted routes, rejection reasons, remediation? [Completeness, Spec §FR-029]
- [x] CHK033 [Closed] Is each attempted route joinable to the diagnostic that rejected it, or are the two associated only by array position — and is a route key required on **every** rejection diagnostic rather than only the probe ones? [Traceability, Spec §FR-029a, §FR-012, Data Model §3]
- [x] CHK034 Is the verbatim rollback action confined to the terminal diagnostic rather than repeated on every rejection entry? [Consistency, Spec §FR-029a, Data Model §3]
- [x] CHK035 Does every rejection code carry at least one action actionable for that code specifically? [Coverage, Data Model §3]
- [x] CHK036 Is the report-only guarantee stated as a prohibition on writes, so it is checkable? [Measurability, Spec §FR-029]
- [x] CHK037 Is the empty-fallback-list path required to reach the same terminal shape as an exhausted walk? [Edge Case, Spec §Edge Cases]

## F. Override and No-Safe-Route Interaction

- [x] CHK038 [Closed] Is the report's `outcome` under an override stated to follow the qualified walk rather than the override's dispatchability? [Clarity, Spec §FR-024a, Data Model §3]
- [x] CHK039 [Closed] Is `release_claim_eligible` given a derivation rule for **every** report, or only for the override case — and specifically for a no-safe-route report carrying no override? [Completeness, Spec §FR-024a, Data Model §3]
- [x] CHK040 Is the would-have-been resolution's representation specified when there **is** no qualified resolution to record? [Coverage, Spec §FR-024, Data Model §3]
- [x] CHK041 [Closed] Is the choice between an explicit `null` and an omitted member pinned for the would-have-been tuple, given the two serialize to different bytes — and is the convention reconciled with the corpus envelope's opposite rule? [Consistency, Spec §FR-024a, §FR-015a]
- [x] CHK042 Does the override path leave `unresolved_agent` requiredness coherent when the override supplies an effective tuple? [Consistency, Spec §FR-013a, Data Model §3]

## G. Helper-Unavailable Non-Event

- [x] CHK043 [Closed] Is the helper's non-consultation made **measurable** — including that no attempted-route entry names a helper route — or is it a self-asserted boolean an implementation could set while still probing the helper? [Measurability, Spec §FR-025a]
- [x] CHK044 [Closed] Is a zero attempt count required for a helper that was never consulted, and is the helper's accounting distinguished from the reported agent's own counters so the zero is unambiguous? [Completeness, Spec §FR-025a, Data Model §3]
- [x] CHK045 [Closed] Are the helper field's values specified for the other reachable states — helper consulted, and no helper declared? [Coverage, Spec §FR-025a]
- [x] CHK046 Is helper unavailability kept out of both closed enums with the reason recorded? [Clarity, Spec §FR-025]

## H. Diagnostic Envelope Field Determinism

- [x] CHK047 [Closed] Is a severity assigned per code, or is the closed severity vocabulary left free for each occurrence — and can a consumer threshold on it to separate a recovered route rejection from an unusable policy? [Measurability, Spec §FR-012c, Data Model §3]
- [x] CHK048 [Closed] Is the `source` field given a value rule, given it is required and contributes to the pinned bytes? [Clarity, Spec §FR-012c, Data Model §3]

## Resolution Log

Twenty-nine items were unmet at first pass. All twenty-nine are closed. Each entry
records the finding, the evidence that made it a real error-handling risk rather than a
stylistic preference, and the artifact section that now carries it. Seven requirements
were added — FR-012b, FR-012c, FR-019c, FR-024a, FR-025a, FR-026a, FR-029a — and no
settled decision was reversed.

### Structural rejection: timing and report validity (CHK009–CHK014)

The spec never stated when structural validation runs. "Pre-pass" appears three times,
and every occurrence is about **module structure** rather than evaluation order: FR-033a's
slice-allocation cell, FR-033d's one-module argument, and the design's mirror of them.
FR-020 through FR-023 impose no ordering at all. Worse, the two places that do touch
timing pointed in opposite directions — FR-001 states `fallback_loop` detection "needs
the walk state that this module already owns" and FR-020 defines the defect against a
route "already-attempted", both of which put it *inside* the walk, while the pre-pass
framing implied all four defects precede it.

The consequence was a report that could not validate. `attempted_routes` carried
`minItems: 1`, so a policy rejected before any route was attempted had no valid
representation: an honest empty array failed the schema, and recording an unattempted
route as attempted would misreport the walk. Nothing stated the `outcome` value either,
and `unresolved_agent`'s requiredness rides on it.

Closed by new **Spec §FR-019c**, which partitions the four codes — three are
policy-document defects decidable with no walk state and run to completion before the
first attempt, suppressing the walk; `fallback_loop` is detected in-walk, preserving both
FR-001's and FR-020's wording — and then specifies the resulting report in full:
`attempted_routes` empty **iff** the pre-walk pass rejected the policy, `outcome`
`no_safe_route`, `unresolved_agent` the policy's agent, all three actual budget counters
`0`, `optional_helper` in its not-consulted form, and `release_claim_eligible` `false`.
**Data Model §3** drops the lower bound to `minItems: 0` and records why, and **§5**
carries the pre-pass partition. The relaxation is a deliberate departure from the
directory's one attempt-array precedent — `contracts/treatment-record.schema.json:940-945`
declares `attempted_route_ids` with `minItems: 1` — so the biconditional is what replaces
the guarantee the bound provided, stated rather than implied because this directory
already prefers making "a stage that was not reached" explicit
(`contracts-claude/analysis-decision.schema.json:57,71` records `not_evaluated` for an
unreached gate).

### Diagnostic emission determinism (CHK017–CHK022)

The Edge Cases entry requires the report to be deterministic about "which diagnostics are
emitted and in what order" — a requirement that determinism exist, with no order supplied.
The data-integrity audit's CHK022 correctly found the requirement present; this audit
found it unfalsifiable, since replay byte-identity (FR-014) then rests on a convention no
artifact states. Three sub-questions were open: how many diagnostics a multiply-failing
route emits, in what sequence, and how the whole array is ordered.

The phrasing itself settles the first: "in what order" presupposes more than one entry.
Three independent lines of evidence agree on emit-all — the repository's own accumulating
precedent (`claude_policy_controls.py:2282-2298` collects a breach for **every** exceeded
budget dimension of one record rather than raising on the first), and the convergent
external shape (`google.rpc.BadRequest` types `field_violations` as repeated to describe
all violations; RFC 9457's `errors` extension reports multiple same-category problems in
one response).

Closed by new **Spec §FR-012b**: one diagnostic per failed check; inter-code order is the
FR-005 declaration order, chosen over the alternative in-tree idiom — the alphabetical
`sorted(set(reasons))` at `claude_policy_controls.py:2524` — because sorting scrambles a
meaningful precedence and cannot be made structural; the whole array runs pre-walk
violations, then per-route entries in attempt order, then `unqualified_override`, then
**exactly one** terminal `no_safe_route` last. The Edge Cases example now resolves
explicitly to `effort_unsupported` then `treatment_probe_failed`, so a reviewer can derive
the sequence from the requirements alone.

Two further points are recorded because they were the mechanism by which this stayed
hidden. First, the sub-reason order and the inter-code order are **orthogonal** — one
selects a single `details.sub_reason` value inside a `preferred_model_unavailable` entry,
the other sequences whole entries — and treating the four-member staging as covering
diagnostic sequencing is exactly how the inter-code order appeared settled while being
unpinned. Second, `no_safe_route` is the one token used both as an `outcome` value and as
a diagnostic code, and nothing coupled the two; FR-012b now makes it biconditional, so a
report cannot claim `resolved` while carrying a terminal failure, or claim
`no_safe_route` while carrying no rollback remediation — which is what makes SC-010
reachable.

### Budget semantics (CHK023–CHK028)

The three budget counters had **no defined unit**. Nothing said what increments
`probe_attempts`, `retries`, or `fan_out`, which made FR-026's "actual attempt count" and
SC-009's "never exceeds the declared budget" unfalsifiable — two conforming
implementations could report different counts for one case and both claim compliance. Two
of the three were worse than undefined: `fan_out` had no referent at all in a sequential
first-match walk, and `retries` had no reachable meaning against a static snapshot, since
re-reading a fixed probe outcome returns the same value. Which code fires on exhaustion
appeared only as an aside inside FR-019's enum-sufficiency argument, never as a
requirement.

Declaring the unit is directory practice rather than an addition to it: every cap in
`contracts-claude/policy-control-registry.schema.json:670-676` carries a required `unit`
from a closed enum alongside its `value`, and that document defines retry exhaustion in
prose at `:154` — "Exhausting retries means at least one attempt failed".

Closed by new **Spec §FR-026a**: `probe_attempts` increments once per attempted route
whose snapshot probe state is consulted; `retries` once per re-consultation of a route
whose exact-invocation outcome is `failure`, which is precisely what makes retry
exhaustion reachable deterministically without simulated flakiness; `fan_out` once per
candidate route entered, bounding walk breadth, so `probe_attempts <= fan_out` always and
the two are not redundant. All three terminate into `no_safe_route` — no new code, since
FR-005 closes the enum.

Identifying *which* budget ran out needed care, and a first attempt at this fix was
wrong. Counter-equals-cap alone cannot mean exhaustion: two probes under
`max_probe_attempts: 2` that both resolve produce counter-equals-cap on a `resolved`
report. But naming "the class that terminated the walk" is not observable either — when
several caps are reached, no report content settles which one *caused* termination, and
against a static snapshot no budget's exhaustion changes the result, so none is causally
privileged. `details.exhausted_budget` is therefore an **array** listing every class whose
actual count equals its declared cap, in enum declaration order, carried on the terminal
diagnostic and nowhere else — a pure function of counters and caps the report already
holds, deterministic by construction, needing no tie-break over simulator internals. Its
presence on that diagnostic is what expresses "spent to the limit **and** failed", the
conjunction a bare comparison cannot. This keeps the external practice of distinguishing
which limit was reached rather than collapsing limits into one terminal state (Temporal's
`RetryState` on the failure; the AWS SDK retry loop naming attempts-exhausted and
quota-depleted separately) while carrying it as a field, which is what keeps the closed
enum closed.

### Retry exhaustion as a named obligation (CHK005, CHK006)

The roadmap lists "Prove retry exhaustion" as its own obligation
(`docs/ai/specs/claude-agent-routing-technical-roadmap.md:541`), but FR-028 said only "a
budget" and User Story 2's scenario 7 says "a probe or retry budget of one" — a
disjunction satisfiable by exhausting probes and never touching a retry, leaving the
roadmap's named obligation unproven. Nothing said which of the three capped dimensions
any case exercises.

Closed in **Spec §FR-028**: the case binds the **retry** class, declares all three
budgets at `1`, and pins all three actual counts, so `retries` is provably among the
at-cap classes on a failing report. Its mechanics are fixed so this is reachable — the
preferred route's exact-invocation outcome is `failure`, the one permitted retry
re-consults it and returns the same `failure`, and no further retry may be taken. All
three declared values satisfy Data Model §1's bounds (`max_retries` `minimum: 0`, the
other two `minimum: 1`), so the case still validates. **SC-001** now names retry
exhaustion rather than generic "budget exhaustion". Recorded honestly: no case makes
probe-attempt or fan-out exhaustion the sole at-cap class, acceptable for the reason
FR-019 already accepts unexercised enum members — one shared cap check governs all three
dimensions.

### Override interaction (CHK038, CHK039, CHK041)

Three consequences of combining FR-024 with FR-013a were derivable only by inference, and
each changes reported bytes.

- **`outcome` under an override was unstated.** FR-013a *relies* on the qualified-walk
  reading — it rejects a root `oneOf` by observing that the override path "produces a
  `no_safe_route` report that still carries `effective_dispatch_tuple`" — but never states
  it, leaving open the opposite reading in which an override is always dispatchable and so
  always resolves.
- **`release_claim_eligible` had a rule for one case only.** It is required in both
  outcomes; only the override path fixed it. A plain no-safe-route report's value was
  undefined.
- **The would-have-been tuple had no absent-versus-`null` rule.** RFC 8785 canonicalizes
  both forms deterministically and is silent on the choice by scope, so byte determinism
  does not decide it — only a stated rule does.

Closed by new **Spec §FR-024a**. `outcome` follows the qualified walk and an override
never promotes it. `release_claim_eligible` is written as a closed disqualifier list with
`true` as the residual — `false` under an override, under `no_safe_route`, or with any
policy-violation diagnostic present — following this directory's established asymmetry,
where the closest analogue `qualification_eligible` is schema-forced to `false` under a
named condition (`contracts-claude/experiment-assignment.schema.json:52-56`) with no
matching true-forcing branch, and its reason vocabulary carries fourteen disqualifying
members against one residual `none`
(`contracts-claude/analysis-decision.schema.json:79-95`). The would-have-been tuple is
**omitted**, never `null`, matching the report's own idiom (FR-013a expresses every
conditional member by presence and absence) and the external omit-by-default bias
(Google AIP-149). The deliberate difference from FR-015a's explicit-`null` rule for a
case's `overrides` is explained rather than left as drift: the corpus envelope has no
schema, so there `null` is the only way to distinguish declared-empty from malformed,
whereas the report expresses that with conditional requiredness.

### Helper non-consultation made measurable (CHK043–CHK045)

`consulted: false` is a boolean the simulator sets about its own behaviour. An
implementation could probe every helper route and still write `false`, satisfying the
letter of FR-025 while violating it in substance, with no pinned byte changing —
precisely the failure mode the domain focus called out. Nothing required a zero anywhere.
The field's values for the other two reachable states (helper consulted; no helper
declared) were also unspecified, though `optional_helper` is required in **every** report.

Established practice for a non-invocation claim is an instrumented count, not a flag:
`unittest.mock`'s `assert_not_called` is backed by an integer `call_count` and Mockito's
`verifyNoInteractions` inspects a recorded interaction history, and metrics guidance
likewise prefers an emitted explicit zero over inferring absence.

Closed by new **Spec §FR-025a**: `optional_helper` gains a required `probe_attempts`
integer that MUST be `0` whenever `consulted` is `false`; it is explicitly **disjoint**
from `budgets.actual.probe_attempts` so the zero is unambiguous; and no `attempted_routes`
entry may name a helper route in that state, which is the corroborating structural
evidence a counter alone cannot supply. All three helper states are given values, with
the identical rendering of "unavailable" and "none declared" recorded as deliberate and
harmless, since whether a helper exists is a property of the policy each case carries.
**Data Model §3** carries the field.

### Route-to-diagnostic joinability (CHK033)

FR-029 requires the no-safe-route report to name "every attempted route, each rejection
reason" — two arrays with no key between them. Position is not a key here: FR-012b emits a
variable number of diagnostics per route, so the arrays differ in length and cannot be
zipped. The design compounded it by scoping `details.route_id` to "probe diagnostics"
only.

Closed by new **Spec §FR-029a**: every route-scoped diagnostic MUST carry
`details.route_id` — the four resolution codes and the four policy-authoring violations —
matching an `attempted_routes` entry for in-walk codes and naming the declared route for a
pre-walk violation. This reuses the identity the policy schema already assigns for
recognising a `fallback_loop` revisit rather than adding a key. **FR-012** extends its
conditional-requiredness branch list from two codes to all four route-scoped codes, since
a join key living in an optional object is not a key a consumer can rely on, and
**Data Model §3** now declares four `allOf` branches. The same requirement makes the
existing code-to-action allocation binding: the rollback action appears only on the
terminal entry, never repeated per rejection, which would push each entry toward the
`maxItems: 3` truncation boundary for no added information.

### Envelope field determinism (CHK047, CHK048)

`severity` and `source` are both required and both enter the bytes FR-014 compares, and
neither had a value rule. `severity` was closed to three members with no per-code
assignment, so two cases could disagree for the same code and no consumer could threshold;
`source` was an open `minLength: 1` string, an unpinned byte in every diagnostic of every
case. No in-tree precedent decided either — no schema under `layer6-efficiency/` binds a
code to a severity, the runner merely defaults the keyword to `error`
(`envelope.py:43-47`) while its validator checks set membership only
(`gates/release.py:823`), and no schema anywhere constrains `source` with `const` or
`enum`.

Closed by new **Spec §FR-012c** and a severity column added to **Data Model §3**'s
code-to-action table. `severity` is a function of `code`: the four route rejections and
`unqualified_override` are `warning`, `no_safe_route` and the four policy-authoring
violations are `error`. That makes `error` a usable threshold — its presence means the
policy is unusable as written, while a report carrying only warnings resolved despite
them — and `info` is declared-but-unemitted, the same position FR-019 already takes for
enum members slice 1 cannot emit. External practice here is genuinely **divided** and the
requirement says so: LSP 3.17 types `severity` per-`Diagnostic` and SARIF lets a per-result
`level` override the rule's `defaultConfiguration.level`, whereas ESLint fixes severity per
rule ID with no per-occurrence override (`eslint/eslint#16040` confirms that is current
practice, not an oversight). This feature takes the rule-level pole deliberately: every
diagnostic here is hand-pinned in a byte-compared corpus, so context-varying severity
would be unfalsifiable authoring latitude. `source` is pinned with `const` to
`route-fallback-simulator`, encoding in the schema what the runner does in code — one
literal per producing module (`envelope.py:55`), which its own `is_diagnostic` predicate
keys off (`envelope.py:70`). **FR-032a** adds `const` to its recorded keyword list; the
engine implements it (`claude_policy_controls.py:332`).

### Second-pass corrections to this remediation (CHK027, CHK033)

An adversarial re-read of the amended artifacts caught three defects introduced **by the
fixes above**, all closed in the same loop. They are recorded because a remediation that
silently repairs itself is indistinguishable from one that never erred, and the third was
a half-covered fix — the most expensive kind to find later.

- **`exhausted_budget` was first written as a single value naming "the class that
  terminated the walk".** That is not observable. FR-028's case declares all three budgets
  at `1` and reaches all three caps, so choosing one culprit would need a tie-break rule
  over simulator internals, and against a static snapshot no budget's exhaustion changes
  the result. Rewritten as an **array** of every at-cap class in enum order — a pure
  function of counters and caps the report already carries.
- **SC-009 still promised the singular form** after that rewrite ("names which dimension
  terminated the walk"), contradicting FR-026a's explicit refusal to attribute cause. Both
  clauses were introduced in this pass and had to be reconciled; SC-009 now states the
  enumeration and records why the causal phrasing would be unmeetable.
- **The `details`-requiredness fix covered four of the eight codes it cited.** FR-029a
  requires `route_id` on eight route-scoped codes, but the branch extension reached only
  the four in `resolutionDiagnostic`; `policyViolationDiagnostic` gained none, so
  `fallback_loop`, `unqualified_adjacent_model`, `generic_agent_substitution`, and
  `silent_inherit_materialization` could have validly omitted `details` and with it the
  join key — the join holding for resolution rejections and failing silently for
  policy-authoring ones. Both **Spec §FR-012** and **Data Model §3** now specify eight
  branches, four per `$defs`, and each branch requires `route_id` *within* `details`
  rather than only the container, since a required object with an optional key is not a
  key. `unqualified_override` is the single deliberate exemption, being scoped to no route.

One further tension the same pass surfaced was a consequence of FR-026a's new fan-out
definition rather than of a checklist item: FR-029's precondition ("the preferred route
and every declared fallback are rejected") no longer covers a walk truncated at
`max_fan_out`, whose unreached routes were never rejected though the outcome is still
`no_safe_route`. **Spec §FR-029a** now attaches FR-029's obligations to the outcome
rather than to that precondition, so the mandated rollback action stays universal on the
code SC-010 depends on.

## Notes

- Verification: `--layer 1` 1428/1428 and `--layer 4` 3731/3731, both matching the
  pre-change baseline. Only Markdown under
  `specs/car-005-availability-fallback-recovery/` changed.
- Seven requirements were added (FR-012b, FR-012c, FR-019c, FR-024a, FR-025a, FR-026a,
  FR-029a), taking the spec from 49 to 56 distinct FR identifiers. Counts in `plan.md`
  are updated to match; the advisory slice estimate rises from 1,185 to 1,290 and its
  conclusion of 3 suggested slices is unchanged.
- No settled decision was reversed. The five resolution codes, the five policy-violation
  members, the four sub-reasons and their order, the single-corpus and single-module
  decisions, the two-slice seam, and the platform-scoped contract placement all stand as
  clarified. The data-integrity domain's twelve closures stand unweakened; its
  code-to-action table gained a severity column and no row changed.
- **Slice seam unaffected.** Every field added — `optional_helper.probe_attempts`, the
  `exhausted_budget` array, the per-code `severity` binding, the `const` `source`, the
  two extra `details`-requiredness branches, and the relaxed `attempted_routes` bound —
  lands in the slice-1 report schema. Slice 2 still modifies no schema file, so
  FR-033b's stronger-than-append-only guarantee and the directory's never-edited-after-
  introduction invariant both hold.
- **Object closure unaffected.** `probe_attempts` joins a record `$defs` that keeps
  `additionalProperties: false`; `exhausted_budget` is a named property of `details`,
  the one deliberately open object. The three-class closure rule is unchanged.

# Data Integrity Checklist: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Purpose**: Requirements-quality audit of the data-integrity surface — closed-enum
discipline, corpus self-containment, canonical-serialization determinism, and
schema-enforced budget maxima. These items test whether the *requirements* are
complete, unambiguous, and internally consistent; they do not test the
implementation, which does not exist yet.
**Created**: 2026-07-29
**Feature**: [spec.md](../spec.md)

**Depth**: Standard. **Audience**: reviewer at PR time. **Focus areas**: the four
supplied by the requester — closed-enum discipline, corpus self-containment,
canonical serialization, declared-budget maxima. Clarifying questions were not
asked: the request already fixed scope, depth, and focus, so no answer would have
changed checklist content.

**Audit result**: 57 items, 12 unmet at first pass, all 12 closed in one remediation
loop. Every `[Closed]` marker cites the artifact section that now carries the
requirement; see the Resolution Log for what changed and why.

## Closed-Enum Discipline

- [x] CHK001 Is the route-resolution enum pinned to exactly five verbatim members, with extension by this feature explicitly forbidden? [Completeness, Spec §FR-005]
- [x] CHK002 Is the enum's authority named unambiguously, so a reader knows which roadmap governs on a disagreement? [Clarity, Spec §FR-017a]
- [x] CHK003 Is drift required to fail in *both* directions — a missing member and an extra member — rather than only on removal? [Measurability, Spec §FR-017a]
- [x] CHK004 Is the enum required to be read live from the committed schema by JSON pointer rather than transcribed into the test? [Clarity, Spec §FR-017a]
- [x] CHK005 Is a stable JSON pointer to the resolution enum specified, so the live read has a fixed target? [Measurability, Spec §FR-016a]
- [x] CHK006 Is the cross-platform third-member divergence pinned as test data rather than described only in prose? [Completeness, Spec §FR-017b]
- [x] CHK007 Is the divergence's permanence recorded with evidence, and is the single condition that would reopen it stated? [Clarity, Spec §FR-017c]
- [x] CHK008 Is the policy-violation enum's membership fixed at exactly five, with the sufficiency argument for no sixth member recorded? [Completeness, Spec §FR-019]
- [x] CHK009 Does the policy-violation enum have an exact set-equality assertion that fails on a *sixth* member or a *dropped* member, matching the guarantee the resolution enum receives? [Closed, Spec §FR-019b]
- [x] CHK010 Is closure of the code vocabulary required to be proven for **both** enums rather than for their union only? [Coverage, Spec §FR-019a, §FR-019b]
- [x] CHK011 Is the negative-validation obligation specified as constructing instance and schema inline, needing no corpus case? [Clarity, Spec §FR-019a]
- [x] CHK012 Are both enums required to be declared in slice 1 so slice 2 modifies no schema document? [Consistency, Spec §FR-019, §FR-033b]
- [x] CHK013 Is the sub-reason vocabulary closed at four members with each member's predicate defined against a named snapshot field? [Completeness, Spec §FR-006]
- [x] CHK014 Is the `severity` vocabulary closed, and is its authority identified? [Completeness, Spec §FR-012]
- [x] CHK015 Is the remediation-action vocabulary specified as a closed set of literal strings with exactly one declaration site? [Clarity, Spec §FR-012a]
- [x] CHK016 Is the substitution-slot prohibition justified in terms of what closure would degrade to without it? [Clarity, Spec §FR-012a]

## Sub-Reason Totality and Mutual Exclusivity

- [x] CHK017 Is the claim that the four sub-reasons are *total* over the snapshot projection supported by a stated predicate for every reachable input? [Measurability, Spec §FR-006]
- [x] CHK018 Is each of the four sub-reasons required to be represented by at least one corpus case? [Coverage, Spec §FR-006, §SC-001]
- [x] CHK019 Is the *mutual exclusivity* claim true structurally for every member, or is it achieved for some member only by first-match evaluation order? [Closed, Spec §FR-006, Data Model §3]
- [x] CHK020 Are the snapshot conditions that make the fourth sub-reason reachable stated, so its corpus case cannot be built in a way that silently pins a different member? [Closed, Spec §FR-006, Data Model §3]
- [x] CHK021 Is the evaluation order stated somewhere an implementer will encounter it, and is it required to be structural rather than a comment? [Clarity, Spec §FR-006, Data Model §5]
- [x] CHK022 Are requirements defined for the multi-rejection edge case, so diagnostic emission and order stay deterministic? [Edge Case, Spec §Edge Cases]

## Canonical Serialization and Byte Identity

- [x] CHK023 Is key ordering pinned rather than left to insertion order? [Clarity, Spec §FR-014a, Research §D1]
- [x] CHK024 Are separator characters pinned so whitespace cannot vary between implementations? [Clarity, Spec §FR-014a, Research §D1]
- [x] CHK025 Is unicode escaping pinned, rather than left to the serializer default? [Completeness, Spec §FR-014a]
- [x] CHK026 Is the presence or absence of a trailing newline pinned, given that in-tree serializers disagree on this exact dimension? [Closed, Spec §FR-014a, Data Model §5]
- [x] CHK027 Is the serializer required to be the *same* function in the simulator and in the pinning test, rather than independently re-declared in each? [Closed, Spec §FR-014a, Data Model §5]
- [x] CHK028 Is float formatting either pinned or made unreachable by an explicit statement that the report carries no floating-point field? [Closed, Spec §FR-014a]
- [x] CHK029 Is the spec's description of the serialization convention consistent with the serializer it resolves to, including on indentation? [Consistency, Spec §Assumptions, §FR-014a]
- [x] CHK030 Is the byte-identity obligation specified as two distinct assertions — run-to-run, and run-to-pinned-report? [Completeness, Spec §FR-014]
- [x] CHK031 Is non-finite-number rejection specified, so a serialization failure cannot become a silent value? [Coverage, Spec §FR-014a]

## Corpus Self-Containment and Case Identity

- [x] CHK032 Is each case required to carry its own policy, snapshot, overrides, and expected report with no reference to another case? [Completeness, Spec §FR-015, §FR-015a]
- [x] CHK033 Is the location of declared budgets consistent between the requirement that lists them as case content and the design that nests them inside the policy? [Consistency, Spec §FR-015a, Data Model §4]
- [x] CHK034 Is anything specified that actually *enforces* case-ID uniqueness, or does the requirement rest on prose the spec then depends on? [Closed, Spec §FR-015a, Data Model §4]
- [x] CHK035 Is case-ID stability across slices distinguishable by a reader as mechanically enforced versus review-enforced? [Closed, Spec §FR-015a, Data Model §4]
- [x] CHK036 Is case ordering specified as declaration order, so an appended case cannot perturb an existing case's pinned bytes? [Clarity, Spec §FR-015]
- [x] CHK037 Is the single-file corpus decision stated consistently across the requirement, the seam rule, and the slice table? [Consistency, Spec §FR-015, §FR-033b, §FR-033c]
- [x] CHK038 Are the per-case fields that make one case readable in isolation specified, rather than left to author discretion? [Measurability, Spec §SC-007, Data Model §4]
- [x] CHK039 Is the corpus's own envelope validation specified, given that no fourth schema document may exist to validate it? [Coverage, Spec §FR-015a, Data Model §4]

## Object Closure and Drift Surface

- [x] CHK040 Is object closure specified consistently for every new object shape, including nested ones? [Closed, Data Model §Object closure rule]
- [x] CHK041 Where an object must stay open, is the openness deliberate, justified, and distinguishable from an oversight? [Clarity, Data Model §Object closure rule, §3]
- [x] CHK042 Are the snapshot's key-value maps specified with a key constraint, rather than left unconstrained? [Closed, Data Model §2]
- [x] CHK043 Is conditional requiredness specified with an idiom the shared validation engine implements? [Consistency, Spec §FR-013a, Research §D2]
- [x] CHK044 Is the prohibition on cross-document references stated, and is it enforced rather than conventional? [Coverage, Spec §FR-016, Research §D1]

## Declared Budget Maxima

- [x] CHK045 Is it unambiguous that an out-of-range declared budget fails schema validation rather than being clamped at run time? [Clarity, Spec §FR-027]
- [x] CHK046 Are concrete bounds specified for each budget field, rather than only the instruction that maxima exist? [Measurability, Data Model §1]
- [x] CHK047 Is the dividing rule between defects the simulator diagnoses and defects the schema rejects stated explicitly? [Clarity, Spec §FR-003a]
- [x] CHK048 Is the out-of-range fixture required to live outside the corpus, so corpus-wide validation is not made to fail by design? [Consistency, Spec §FR-027, Data Model §4]
- [x] CHK049 Is the proof that validation rejects rather than clamps allocated to the same slice that ships the constraint it proves? [Closed, Spec §FR-027, §FR-033a]
- [x] CHK050 Are actual attempt counts required to be reported alongside declared caps for every capped dimension? [Completeness, Spec §FR-026]

## Diagnostics Envelope Integrity

- [x] CHK051 Is the required-versus-optional field split specified against an identified authority rather than inferred? [Clarity, Spec §FR-012, Research §D7]
- [x] CHK052 Is the competing in-tree diagnostics dialect named as a trap, so it cannot be adopted as precedent by mistake? [Consistency, Spec §FR-012, Research §D7]
- [x] CHK053 Is `remediation` fixed as a per-diagnostic field and explicitly barred from the report root? [Clarity, Spec §FR-012]
- [x] CHK054 Are the action-array bounds specified with the reason each bound exists, so neither reads as arbitrary? [Measurability, Spec §FR-012a]
- [x] CHK055 Does every diagnostic-emitting code have at least one apt action available, and is it recorded that no code needs more than the cap allows? [Closed, Data Model §3]
- [x] CHK056 Is the verbatim rollback action string pinned identically everywhere it is required? [Consistency, Spec §FR-012a, §FR-029]
- [x] CHK057 Is helper unavailability specified as a structured field rather than a diagnostic, with the reason neither enum gains a member? [Clarity, Spec §FR-025]

## Resolution Log

Twelve items were unmet at first pass. All twelve are closed. Each entry records the
finding, the evidence that made it a real integrity risk rather than a stylistic
preference, and the artifact section that now carries it.

### Canonical serialization (CHK026, CHK027, CHK028, CHK029)

The byte-identity rule was gestured at rather than pinned. `research.md` D1 resolves
the serializer to `canonical_json` (sorted keys, minimal separators, `ensure_ascii=False`,
`allow_nan=False`), which settles key order, whitespace, and unicode — but three
dimensions were left open, and one of them is actively divergent in-tree.

- **Trailing newline was unpinned.** The repository carries eight `canonical_json`
  definitions and three append a newline. Two conforming implementations could
  therefore differ by one byte while both claiming to be canonical.
- **Nothing required the test and the simulator to share one serializer.** All six
  existing `canonical_json` occurrences under `unit/` re-declare a local copy, and two
  of those six append a newline. Worse, the established comparison shape re-serializes
  *both* sides, so a local copy that disagreed with the simulator would **cancel** the
  discrepancy instead of failing — a green test over a wrong simulator.
- **Float rendering was unaddressed.** `allow_nan=False` rejects non-finite values but
  does not pin `repr`-based float formatting.

Closed by new **Spec §FR-014a**, which names the serializer, forbids the trailing
newline, requires the test to assert over the simulator's own `serialize_report` output
with no local re-declaration, and records the integer-only numeric invariant that makes
float formatting unreachable. **Data Model §5** carries the implementation-facing form.
The stale `Assumptions` bullet that implied a fixed *indentation* convention is
corrected — the resolved serializer emits none.

### Sub-reason exclusivity and ordering (CHK019, CHK020)

FR-006 asserted the four sub-reasons are "mutually exclusive and total", presenting
both as structural properties. Totality holds. Exclusivity does **not** hold uniformly:
the first three partition one snapshot field and are genuinely disjoint, but
`platform_route_changed` reads the separate `platform_route_changes` array and can
co-occur with any of the first three. Its disjointness comes only from being evaluated
last. The evaluation order was therefore load-bearing while being presented as a
determinism nicety.

This had an unstated corpus consequence: a case meant to pin `platform_route_changed`
must bind its alias exactly as pinned **and** list the pinned model as available, or an
earlier predicate matches first and the hand-pinned expected report is simply wrong —
surfacing later as a replay failure whose apparent cause is unrelated to how the
snapshot was built.

Closed in **Spec §FR-006** (exclusivity split into structural versus order-derived,
plus the authoring precondition) and **Data Model §3**. No member and no ordering
changed; the settled four-member vocabulary and its order stand exactly as clarified.

### Policy-violation enum closure (CHK009)

The two closed enums shipped with unequal protection. The resolution enum gets exact
set equality read live from the schema (FR-017a). The policy-violation enum got only
FR-019a, which proves that *one* out-of-vocabulary code fails validation — that shows
the field is constrained, not that it is constrained to those five. A sixth member
added, or one of the five dropped, would fail no test in the suite.

Closed by new **Spec §FR-019b**: exact set equality read live by JSON pointer at
`$defs/policyViolationDiagnostic/properties/code/enum`, failing in both directions. The
requirement also explains why this test *does* declare its five members in the test
file while FR-017a forbids transcription — the cases are inverses. FR-017a compares two
independently committed artifacts, so transcribing either collapses two witnesses into
one. The policy-violation vocabulary has no independent committed authority: the roadmap
names its four rejections in prose only, never as code tokens, and the fifth member is
this spec's own addition. The schema is the sole token-bearing artifact, so the
test-side literal *is* the second witness.

### Corpus case identity (CHK034, CHK035)

FR-033b's append-only seam and SC-007's read-one-case guarantee both depend on unique,
stable case IDs, but nothing enforced either. The corpus has no schema (FR-016 permits
exactly three documents, none validating the envelope), and a tree-wide search found no
`case_id` uniqueness assertion for any existing fixture corpus. The property the spec
leans on was prose only.

Closed by new **Spec §FR-015a**, obliging slice 1's test to assert `case_id` uniqueness,
non-emptiness, per-case self-containment, and absence of cross-case references. It also
states plainly that **cross-slice stability is not** mechanically enforced: that claim
spans two committed states, and the replay test cannot detect it because a case whose
inputs and pinned report both moved still replays consistently. Recording which half is
mechanical prevents a reviewer from trusting a guarantee that does not exist.

### Object closure (CHK040, CHK042)

`data-model.md` claimed all three schemas declare `additionalProperties: false` **at
every object**. Followed literally that breaks the snapshot schema: `alias_bindings`,
`supported_efforts`, `probe_availability`, and `exact_invocation_probe` are maps keyed by
alias or model ID, where every data key is by definition an additional property — the
document would reject every non-empty snapshot. The blanket claim also already
contradicted §3, where `details` is deliberately open.

Closed by a **three-class closure rule** in Data Model (record → `false`; open-keyed map
→ `additionalProperties: <value schema>` plus `propertyNames`; deliberately open →
`true`, `details` only), and a concrete per-map table in **§2** giving each map its key
and value schema. The map form is existing directory precedent, not a new convention:
`score-bundle.schema.json` `$defs/ballot/properties/criterion_scores` is declared this
way, and `propertyNames` already constrains keys in three of the eleven documents. Keys
are constrained rather than left open so an empty-string alias cannot become a silently
unmatchable entry. `platform_route_changes` is an array of records, so it keeps `false`
plus `uniqueItems`.

### Budget-maxima proof allocation (CHK049)

FR-027 filed the out-of-range negative fixture under "the *behavioural* half" of slice
2, alongside FR-026 and FR-028. That mis-classified it on the requirement's own terms —
it proves *validation* rejects, which is not behaviour — and left slice 1 shipping a
`maximum` whose enforcement is unproven inside its own diff. That is the exact condition
FR-019a exists to prevent for the enums, and FR-033b independently requires slice 1 to
be complete and passing alone.

Closed in **Spec §FR-027**: the negative validation proof travels with the constraint
into slice 1, constructed inline in the FR-019a manner and explicitly not a corpus case
(every corpus case must validate). Slice 2 keeps the behavioural half unchanged — cap
enforcement with attempt counting, and the exhaustion case. The seam tables in
**Spec §FR-033a** and **plan.md §Slice Seam** are updated to match.

### Remediation-action adequacy (CHK055)

The eleven-member action vocabulary was listed as a flat block with no mapping to the
ten diagnostic codes, so its sufficiency against `minItems: 1` and `maxItems: 3` was
unverifiable — and a case could pair any code with any action and still satisfy every
schema keyword.

Closed in **Data Model §3** with an explicit code-to-action table. All ten codes across
both enums are covered; the maximum is 2 (`no_safe_route`, carrying both a forward
remedy and the mandated verbatim rollback) against a cap of 3, so no code sits near the
runner's truncation boundary.

## Notes

- Verification: `--layer 1` 1428/1428 and `--layer 4` 3731/3731, both matching the
  pre-change baseline recorded in `research.md`. Only Markdown under
  `specs/car-005-availability-fallback-recovery/` changed.
- Three requirements were added (FR-014a, FR-015a, FR-019b), taking the spec from 46 to
  49 distinct FR identifiers. Counts stated in `plan.md` are updated to match; the
  advisory slice estimate rises from 1,110 to 1,185 and its conclusion of 3 suggested
  slices is unchanged.
- No settled decision was reversed. The five resolution codes, the five
  policy-violation members, the four sub-reasons and their order, the single-corpus and
  single-module decisions, the two-slice seam, and the platform-scoped contract
  placement all stand as clarified.

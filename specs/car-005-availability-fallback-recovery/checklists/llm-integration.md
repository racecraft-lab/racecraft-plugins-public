# LLM Integration Checklist: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Purpose**: Requirements-quality audit of the platform-fidelity surface — whether
the behaviours this feature simulates are the behaviours the Claude Code runtime
actually has, and whether the contracts CAR-006 inherits carry the inputs
resolution consumes. Five focus areas: route-tuple fidelity (alias, qualified
resolved model ID, explicit effort, and what invalidates the tuple), snapshot
projection sufficiency in both directions, override honesty against the documented
subagent-model environment surface, alignment with the CAR-002 probed
unavailable-model observation, and synthetic-cast sufficiency. These items test
whether the *requirements* are complete, unambiguous, and faithful to their
external referents; they do not test the implementation, which does not exist yet.
**Created**: 2026-07-30
**Feature**: [spec.md](../spec.md)

**Depth**: Standard. **Audience**: reviewer at PR time. **Focus areas**: the four
supplied by the requester plus six named hard checks. Clarifying questions were
not asked: the request already fixed scope, depth, and focus, and no answer would
have changed checklist content.

**Audit result**: 31 items, 26 unmet at first pass, all 26 closed in one
remediation loop. CHK031 was added mid-audit when the effort-ladder research
returned the documented degradation behaviour; it is numbered last but sits in
category A, where it belongs by subject. Marker counts were taken deterministically
before and after remediation (26 then 0). Every `[Closed]` marker cites the artifact
section that now carries the requirement; the Resolution Log records what changed
and why.

**Relationship to the two prior domains**: `data-integrity` closed 12 findings and
`error-handling` closed 29. Both audited *internal* properties — vocabulary
closure, determinism, ordering, report completeness. This audit is the first to
test the requirements against **external referents**: the published Claude Code
subagent contract, and the frozen CAR-002 probe code committed in this repository.
No conclusion of either prior audit is reopened. Two settled decisions were
re-examined and confirmed rather than revised: the override diagnostic's `warning`
severity (CHK030) and the structured-field treatment of helper state. Where this
audit reaches ground a prior item touched, it asks the next question rather than
the same one — `error-handling` CHK045 confirmed the helper field's three *report*
states are specified; this audit asks whether the *policy* can declare the helper
those states describe.

**External grounding**: every fidelity claim below is traced to one of three
authorities, named inline per item.

| Authority | What it settles |
| --- | --- |
| Claude Code subagent documentation (`code.claude.com/docs/en/sub-agents`, `.../model-config`) | subagent model-resolution order, allowlist skip behaviour, the alias set, the effort ladder and its model-dependence |
| `docs/ai/research/claude-agent-route-candidates.md` | this repository's dated, quoted extract of that documentation (`EFF-1`, `EFF-2`, `RES-1`–`RES-5`, `ALS-repoint`, `CAP-Q5`, `CAP-Q6`) |
| `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py` | the frozen CAR-002 probe: the unavailable-model outcome vocabulary, its epistemic labels, and the interference-surface unset proof |

## A. Route-Tuple Fidelity

- [x] CHK001 Is a route defined as the three-member tuple — alias, qualified resolved model ID, explicit effort — consistently wherever the term appears? [Consistency, Spec §FR-003, §FR-013]
- [x] CHK002 Is the effort vocabulary pinned at requirement level and protected against drift, given it is a third closed enum in the shipped schemas alongside the two that receive set-equality tests? [Closed] [Completeness, Spec §FR-007a]
- [x] CHK003 Is the premise that effort support varies by model grounded in the platform contract, so the unsupported-effort code is shown to model a real constraint rather than an invented one? [Closed] [Traceability, Spec §FR-007a]
- [x] CHK004 Is the effort ladder's scope stated as the subagent-frontmatter surface, so a session-only level cannot be read as a missing member of a supposedly closed ladder? [Closed] [Clarity, Spec §FR-007a]
- [x] CHK005 Is the platform behaviour that makes alias re-pointing a real hazard recorded, so the re-pointed sub-reason rests on documented alias semantics rather than on assumption? [Closed] [Assumption, Spec §FR-006]
- [x] CHK006 Is the four-member sub-reason set shown to be faithful to the documented ways a pinned alias-plus-model tuple goes stale, not only total over the projection this feature authors? [Closed] [Coverage, Spec §FR-006]
- [x] CHK007 Is it unambiguous that an alias re-point invalidates the pinned tuple even when the newly bound model is itself otherwise qualified? [Clarity, Spec §Edge Cases, §FR-006]
- [x] CHK031 Does the unsupported-effort requirement state that rejecting the route is a deliberate **preflight policy**, given the documented runtime silently degrades to the highest supported level instead of failing? [Closed] [Conflict, Spec §FR-007a]

## B. Snapshot Projection Sufficiency

- [x] CHK008 Does the requirement that fixes the projection's contents enumerate every field the design actually carries, given that requirement is declared the authority on the projection's shape? [Closed] [Completeness, Spec §FR-002, Data Model §2]
- [x] CHK009 Does the Key Entities description of the projection agree with the requirement and the design, or does it restate a shorter list? [Closed] [Consistency, Spec §Key Entities]
- [x] CHK010 Does every projection field have a named consumer, so no vestigial field enters the contract CAR-006 inherits? [Coverage, Spec §FR-002, Data Model §2]
- [x] CHK011 Is the exact-invocation outcome vocabulary reconciled with the three-value outcome vocabulary the frozen CAR-002 probe actually produces, rather than assumed to be the same three values? [Closed] [Conflict, Spec §FR-002a, Data Model §2]
- [x] CHK012 Is the CAR-002 probe surface the exact-invocation outcome projects from identified, given the probe records two surfaces and reads one of them as inference? [Closed] [Clarity, Spec §FR-002a, Data Model §2]
- [x] CHK013 Does the projection carry the organization model allowlist, given the documented override path consumes it? [Closed] [Completeness, Spec §FR-002, §FR-024b, Data Model §2]
- [x] CHK014 Is the projection stated to be CAR-006's preflight input contract, so its stability obligation is visible to a reader of this spec alone? [Traceability, Spec §User Story 1, §Key Entities]

## C. Override Honesty

- [x] CHK015 Is the runtime surface the override simulates named, so the simulated behaviour is attributable to a documented mechanism rather than to a generic environment override? [Closed] [Traceability, Spec §FR-024b, Data Model §3]
- [x] CHK016 Is the override's documented precedence recorded, so "the override wins at dispatch" is grounded rather than asserted? [Closed] [Assumption, Spec §FR-024b]
- [x] CHK017 Is the documented condition under which the platform skips the override stated, so no fixture proves unconditional override behaviour the runtime does not have? [Closed] [Conflict, Spec §FR-024b, Data Model §3]
- [x] CHK018 Is "unqualified" defined for an override, so a corpus case cannot be authored against an undefined predicate? [Closed] [Ambiguity, Spec §FR-024b]
- [x] CHK019 Is the disposition of a qualified override specified, given the claims-exclusion rule disqualifies on "an override is in force" while the diagnostic is scoped to an unqualified one? [Closed] [Consistency, Spec §FR-024b]
- [x] CHK020 Does the effective dispatch tuple under an override state which members the override supplies and which survive from the policy, given the override sets a model only while the tuple requires an effort? [Closed] [Conflict, Spec §FR-024b, Data Model §3]
- [x] CHK021 Is the documented inherit sentinel modelled or explicitly excluded, given it is a set value that behaves as unset? [Closed] [Edge Case, Spec §FR-024b]
- [x] CHK022 Is the claims-exclusion consequence tied to the program's existing posture on this variable, rather than reasoned only from this spec's internals? [Closed] [Traceability, Spec §FR-024b]

## D. CAR-002 Alignment

- [x] CHK023 Is the CAR-002 observation the reason codes must align with identified, and is its epistemic status recorded, given the roadmap makes that observation the input that shapes these codes? [Closed] [Traceability, Spec §FR-002a]
- [x] CHK024 Is it stated as a requirement that model unavailability is a snapshot-declared preflight input and never a simulated dispatch attempt? [Closed] [Completeness, Spec §FR-002a]
- [x] CHK025 Does splitting the re-pointed sub-reason from the platform-route-changed sub-reason reconcile with the CAR-002 detection rule, which places alias re-pointing inside platform route-change detection? [Closed] [Conflict, Spec §FR-006]
- [x] CHK026 Is release-claim eligibility specified for a report whose preferred route was rejected by a platform route change or an alias re-point, given the program marks that condition non-scorable for the requested route? [Closed] [Coverage, Spec §FR-024a]

## E. Synthetic-Cast Sufficiency

- [x] CHK027 Is there a contract member by which a policy declares its optional helper, given the helper field's three report states are keyed to whether the policy declares one? [Closed] [Completeness, Spec §FR-025b, Data Model §1]
- [x] CHK028 Are the helper's own routes locatable from the policy, given the helper probe counter counts probes on the helper's routes and no attempted-route entry may name one? [Closed] [Measurability, Spec §FR-025b, Data Model §1]
- [x] CHK029 Does the cast requirement's "name a small synthetic cast" agree with a policy contract rooted on a single agent identity, and is the three-role-class sufficiency claim checkable? [Closed] [Conflict, Spec §FR-018, §FR-025b, §Assumptions]

## F. Confirmed Settled Decisions

- [x] CHK030 Is the override diagnostic's severity consistent with the roadmap's "report non-qualified overrides loudly", and is the choice recorded rather than incidental? [Consistency, Spec §FR-012c]

## Resolution Log

Four new requirements and one new success criterion carry the closures; six
existing requirements and three entity or assumption entries were extended in
place. No requirement was deleted and no settled decision reversed.

### The two fidelity defects — behaviours the runtime does not have

Two findings were the same class of defect: a requirement asserting behaviour the
documented runtime does not exhibit, which a corpus case would then "prove".

**The override was asserted unconditionally (CHK017, CHK020).** FR-024 made the
override the effective dispatch tuple with no condition, and the scoping interview
justified that as honest simulation "without pretending the preflight can block an
env var". The documented runtime is narrower: it checks the override against the
organization's model allowlist and **skips a value resolving to an excluded model**,
running the subagent on the inherited model instead. So the platform itself can block
it. FR-024b now makes the honored branch conditional on the allowlist, adds the
`skipped_by_allowlist` disposition, and requires a second corpus case. The skipped
branch's claim is deliberately bounded to the negative: it records that the override
did not take effect and does **not** name the model that runs instead, because the
documented fallback target is the *inherited* model and this projection carries no
parent-session model. Reading the skip as "resolution resumes at the per-invocation
parameter" would have been inference and is explicitly excluded. A second defect
surfaced in the same requirement: the variable sets a **model** only, so it cannot
supply the `effort` member a dispatch tuple requires — the effective tuple is a
hybrid, and FR-024b now attributes each member.

**Unsupported effort was implied to mirror a runtime rejection (CHK031).** FR-007
rejects the route; the runtime **silently degrades** to the highest supported level at
or below the one declared, and an organization effort cap clamps the same way — with
the warning suppressed under the machine-readable output formats a harness uses. The
resolution is not to drop the code but to state what it is: a **preflight
qualification failure**. A route whose declared effort silently degrades is not a
qualified route, because the tuple that ran is not the tuple the policy pinned and no
report field would record the difference. FR-007a now says so explicitly, so the
corpus cannot appear to prove a runtime rejection that does not exist.

### The alignment the roadmap requires, and what it actually points at

The roadmap requires the reason codes be "aligned with the CAR-002 probed
unavailable-model behavior", and made that observation the input that "shapes the
CAR-005 reason codes". Reading the frozen probe changed what alignment can mean
(CHK011, CHK012, CHK023, CHK024).

CAR-002 did not produce the binary the roadmap anticipated. Its committed classifier
produces a **three-member** vocabulary — `hard_rejection`, `soft_remap`,
`undetermined` — over **two** surfaces, and emits its answer labeled
`labeled_inference` where the alias-binding answers are labeled `observation`. Its
route-change answer is hardcoded open. No committed capture carries an actual observed
outcome. So CAR-005 pins resolution semantics **ahead of** the platform fact, not
downstream of it. FR-002a states that rather than glossing it, and states the
consequence a reviewer needs: the codes rest on a contract decision, not on a
determinate observation.

The mapping is now declared and **total on the CAR-002 side**, which closed a real
fail-open hole. `undetermined` — the outcome CAR-002 says no availability claim
derives from — had no representation, so it would have collapsed into a probe
`success` or `absent` and left the route selectable. It now maps to probe
unavailability, so FR-008 governs it, which is the same fail-closed rule FR-008
already imposes one field over. No new enum member was needed: all three CAR-002
outcomes land on projection members FR-002 already names.

### The projection was under-specified by its own authority

FR-002 enumerated **five** facts while the design carried **six**, and FR-002 is
simultaneously the stated authority on the projection's shape (CHK008, CHK009,
CHK013). Declared platform route changes were missing from the requirement and from
Key Entities even though FR-006's fourth sub-reason reads nothing else, and the
organization allowlist was missing because no requirement had yet needed it. Both are
now named, making seven, and FR-002 states sufficiency in **both** directions against
the consumed-by column — no requirement reads an absent fact, no member lacks a
consumer. That second half matters because this projection is CAR-006's preflight
input contract, so a vestigial member here is inherited debt rather than a local cost.

### The helper the report described could not be declared

`error-handling` CHK045 established the helper field's three report states. This audit
asked the next question — which policy member distinguishes them — and the answer was
none (CHK027, CHK028, CHK029). The policy root carries one `agent`; nothing expresses
"a required agent *and* an optional helper", which is exactly what the
helper-unavailable case needs. Three obligations were therefore unsatisfiable: the
three helper states keyed to "whether the policy declares an optional helper", the
helper probe counter's domain of "the helper's routes", and the rule that no attempted
route may name a helper route. FR-025b adds an optional `optional_helper` policy
member carrying the helper's identity and its own routes. FR-018's "name a small
synthetic cast" was the corroborating internal signal — a plural cast against a
single-agent root — and it is now reconciled: the cast is the vocabulary the corpus
draws from, not the number of agents one policy names. Three role classes remain
sufficient; what was insufficient was the contract.

### Grounding recorded where it was previously absent

Four items were closed by citing sources the spec relied on without naming
(CHK003, CHK005, CHK015, CHK016, CHK022). The effort ladder's five members and their
model-dependence, the `ultracode` exclusion, the alias set and its documented drift,
the subagent model-resolution order, and the program's own posture of *proving* the
override unset for a scored run were all traceable but untraced. A new Assumptions
entry names the dated documentation extract as the authority so a later documentation
change is a change to a cited source rather than the silent invalidation of an uncited
assumption. The effort ladder additionally gained the drift protection the other two
closed enums already had: it is a third closed enum in the same shipped schemas and a
sixth or dropped member would have failed nothing.

### Confirmed, not revised

CHK001, CHK007, CHK010, CHK014, and CHK030 were met at first pass. CHK030 is recorded
deliberately: `unqualified_override` at `warning` looks in tension with the roadmap's
"report non-qualified overrides loudly", and the prior domains settled it — the
consequence travels on `release_claim_eligible` and the terminal diagnostic supplies
the report's `error`. It is confirmed here rather than reopened.

## Notes

- Items are numbered sequentially and scoped to this domain; the two prior
  domains number independently.
- `[Closed]` on an item means the artifact now carries the requirement the item
  asked for, at the section the item cites.
- Five dispositions are recorded for consensus rather than as settled closures; see
  the autopilot consensus log for their routing.

---
topic: "CAR-005 model availability, fallback, and recovery simulation"
slug: "car-005-availability-fallback-recovery"
date: "2026-07-29"
mode: "setup"
spec_id: "CAR-005"
source_input:
  type: "topic"
  ref: "CAR-005 scope section, docs/ai/specs/claude-agent-routing-technical-roadmap.md"
question_count: 12
stop_reason: "natural"
---

# Design Concept: CAR-005 Model Availability, Fallback, and Recovery Simulation

> **Source:** CAR-005 scope from `docs/ai/specs/claude-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-29
> **Questions asked:** 12
> **Stop reason:** natural (every queued branch walked; all twelve
> recommendations accepted; one mid-interview delivery directive recorded
> under Q10)

## Goals

- Prove bounded route-resolution and recovery semantics synthetically, before
  CAR-006 implements the real resolver: an executable reference simulator at
  `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` exercised
  by `tests/speckit-pro/unit/test-route-fallback-simulation.py` against
  declarative scenario fixtures. The fixtures are the durable contract;
  CAR-006 re-proves its production resolver against the same corpus (Q1).
- Define the resolution-report contract CAR-006's preflight will emit:
  rejection and remediation entries mirror the installed runner's diagnostics
  envelope — `{code, message, severity, source, details, remediation:
  {summary, actions[]}}` (Q4).
- Two closed reason-code enums: the five roadmap-pinned route-resolution codes
  (`preferred_model_unavailable`, `effort_unsupported`,
  `capability_probe_unavailable`, `treatment_probe_failed`, `no_safe_route`)
  kept verbatim, plus a CAR-005-owned policy-violation enum for structural
  defects (`fallback_loop`, `unqualified_adjacent_model`,
  `generic_agent_substitution`, `silent_inherit_materialization`,
  `unqualified_override`) (Q2, Q12).
- Alias re-pointing and platform route change map to
  `preferred_model_unavailable` with a machine-readable sub-reason in the
  envelope's `details` object — the five-code enum stays exactly as both
  roadmaps pin it (Q11).
- The unqualified `CLAUDE_CODE_SUBAGENT_MODEL` scenario simulates documented
  runtime behavior honestly: the override wins at dispatch, the report emits a
  loud `unqualified_override` diagnostic, marks the environment excluded from
  release claims, and still records what the qualified resolution would have
  been (Q12).
- Deterministic replay proven by pinning: each corpus case pins its full
  expected resolution report; the test asserts run-twice byte-identity and
  byte-identity to the pinned report under canonical JSON serialization (Q8).
- Probe/retry/fan-out bounds are fixture-declared budget fields with
  schema-enforced maxima; the simulator treats them as hard caps and reports
  actual attempt counts, so exhaustion is provable with `budget = 1` (Q7).
- One self-contained scenario corpus
  (`tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json`)
  where each case bundles policy, synthetic snapshot, overrides, declared
  budgets, and expected report (Q9).
- JSON Schema contracts land platform-scoped in
  `tests/speckit-pro/layer6-efficiency/contracts-claude/`, with a structural
  parity test asserting the resolution enum exactly matches the five codes
  both roadmaps pin (Q3).
- **Split into 2 vertical slices** along the rule-family seam, each cutting
  schema → simulator → test end-to-end: slice 1 = resolution-failure semantics
  (five reason codes, snapshot projection, replay pinning); slice 2 =
  structural rejections, override/helper paths, retry exhaustion (Q10).
- **Delivery directive (user, mid-interview):** because the split produces
  more than one PR, the slice PRs are managed as a **gh-stack stacked-PR
  chain** (`gh stack`, installed v0.0.8) — slice 2 stacks on slice 1.

## Non-goals

- No production files: `speckit_pro_runner/helpers/route_policy.py` and the
  real preflight are CAR-006's framework slice — answered in Q1 (prototype
  option explicitly rejected).
- No real route qualification and no final preferred/fallback selection —
  those are CAR-007 through CAR-010 (roadmap Out of Scope, reaffirmed in Q5).
- No live UAT and no production checkpoint/resume scheduling (roadmap Out of
  Scope).
- No shared byte-identical `contracts/` members in this spec — platform-scoped
  schemas only; promotion to shared members is a deliberate future joint
  change with the Codex twin — answered in Q3.
- No reuse of the full CAR-002 runtime-capability-snapshot schema as the
  simulator input; the input is a minimal purpose-built projection — answered
  in Q6.
- No real shipped agent names in fixtures; synthetic `fixture-*` cast only —
  answered in Q5.

## Design Tree (Q&A log)

### Q1. CAR-005 has 0 production files, but must "prove" resolution and recovery semantics. What form should the thing-under-test take, given CAR-006 later implements the real resolver in `speckit_pro_runner/helpers/route_policy.py`?

**Branch:** Simulator architecture

**Recommended answer:** Executable reference simulator in test lib
> A pure-function simulator at
> `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` consumed
> by the unit test, with declarative scenario fixtures plus pinned expected
> reports. Matches the CAR-003/004 precedent (`claude_treatment_runner.py`,
> `claude_control_comparison.py` live in `lib/`), and CAR-006 re-proves its
> production resolver against the same fixtures — the fixtures are the durable
> contract, the simulator is the executable spec.

**Alternatives offered:**
- Declarative-only expected-outcome fixtures: ~half the LOC, but nothing
  exercises loop rejection, retry exhaustion, or bounded fan-out until
  CAR-006; the roadmap's "prove" goal goes largely unmet.
- Prototype the real resolver early: violates the 0-production-files budget
  and the roadmap sequencing; would need a roadmap amendment.

**User's answer:** Executable reference simulator in test lib (Recommended)

---

### Q2. The roadmap names five stable reason codes. It separately requires rejecting fallback loops, unqualified adjacent models, generic-agent substitution, and silent inherit materialization. How should those four structural rejections be coded?

**Branch:** Reason-code taxonomy

**Recommended answer:** Two closed enums — resolution + policy-violation
> Keep the five roadmap codes verbatim as the route-resolution enum (mirrored
> line-for-line in the Codex roadmap, so parity holds) and add a second closed
> enum for structural policy defects. Structural defects are policy-validation
> failures, not runtime unavailability — conflating them would overload
> `no_safe_route` and lose a distinction CAR-006's preflight report needs.

**Alternatives offered:**
- One flat enum extending the five: simpler registry, but the roadmap-pinned
  codes stop being "the" resolution enum and both roadmaps would need
  amending.
- Only the five, violations folded into `no_safe_route` detail: zero new
  codes, but the defect class becomes unqueryable prose.

**User's answer:** Two closed enums: resolution + policy-violation (Recommended)

---

### Q3. Should CAR-005's new JSON Schema contracts land in the shared byte-identical `contracts/` directory or the platform-scoped `contracts-claude/`? G56R-005 has not started, and CAR-012 exists because shared members from CAR-003/G56R-003 diverged.

**Branch:** Contract parity scoping

**Recommended answer:** `contracts-claude/` + structural parity test
> Platform-scoped schemas with a unit test asserting the resolution enum
> exactly matches the five codes both roadmaps pin. First-mover CAR-005 sets
> the structural template; G56R-005 mirrors it, and any byte-identical
> promotion happens as a deliberate joint change — avoiding a repeat of the
> CAR-012 situation where a one-sided edit strands the twin.

**Alternatives offered:**
- Shared `contracts/` byte-identical now: strongest parity guarantee, but
  every future correction becomes a two-platform joint landing while the twin
  doesn't exist yet.
- Defer schemas to CAR-006: fewer artifacts now, but CAR-006's 265-LOC budget
  doesn't include schema authoring, and unvalidated fixtures are how drift
  starts.

**User's answer:** contracts-claude/ + structural parity test (Recommended)

---

### Q4. The no-safe-route report must emit the unresolved agent, attempted routes, rejection reasons, and remediation. What shape should each rejection/remediation entry take?

**Branch:** Report/diagnostic shape

**Recommended answer:** Mirror the runner diagnostics envelope
> Reuse the installed runner's existing diagnostic shape — `{code, message,
> severity, source, details, remediation: {summary, actions[]}}` — for every
> rejection entry, with `code` drawn from the two closed enums. CAR-006
> implements the preflight as a runner doctor operation, so its report drops
> straight into the envelope consumers already parse; no second diagnostics
> dialect.

**Alternatives offered:**
- Bespoke minimal report shape: fewer fields now, but CAR-006 would translate
  it into runner diagnostics anyway — two shapes for one fact.
- Freeform structured + prose remediation: fastest to write, but
  machine-actionable remediation becomes string parsing.

**User's answer:** Mirror the runner diagnostics envelope (Recommended)

---

### Q5. Should the fixture route policies name synthetic agents or the twelve real shipped agents?

**Branch:** Fixture agent identity

**Recommended answer:** Synthetic `fixture-*` agents by role class
> A small synthetic cast (e.g. `fixture-required-executor`,
> `fixture-bounded-analyst`, `fixture-optional-helper`) covering the role
> classes the scenarios need. CAR-002 set this precedent with its
> `car002-probe` agent; synthetic names make it impossible to mistake
> simulation output for a shipped-route claim, which matters because release
> claims must exclude unqualified routes and real routes don't exist until
> CAR-007–010.

**Alternatives offered:**
- The twelve real agent names: more realistic for CAR-006's fake-home tests,
  but synthetic policies attached to real names look like route decisions in
  grep results and reviews.
- Mixed (real names, synthetic routes): inherits the grep-confusion problem
  plus a "which parts are real?" reading burden.

**User's answer:** Synthetic fixture-* agents by role class (Recommended)

---

### Q6. Should the simulator's probed-environment input reuse the CAR-002 runtime-capability-snapshot structure with synthetic data, or a purpose-built minimal shape?

**Branch:** Snapshot input projection

**Recommended answer:** Minimal purpose-built snapshot shape (moderate confidence)
> A small synthetic-environment schema carrying only what resolution consumes:
> available model IDs, alias→resolved bindings, per-model supported efforts,
> probe availability, exact-invocation probe outcomes. The full CAR-002
> snapshot (`tuple_evidence`, `canary`, raw transcripts,
> `models_endpoint_evidence`) is a capture record, not a resolver input —
> CAR-006's real preflight will derive exactly this projection from live
> probes, so defining the projection IS the deliverable.

**Alternatives offered:**
- Reuse the CAR-002 snapshot schema with synthetic data: zero new schema
  surface, but fixtures drag capture-provenance fields the simulator ignores,
  and synthetic "evidence" inside an evidence-class-governed shape muddies
  what's a real capture.
- Simulator-internal dicts, no schema: least ceremony, but the CAR-006
  projection contract goes undefined.

**User's answer:** Minimal purpose-built snapshot shape (Recommended)

---

### Q7. The scope bounds probe attempts, retries, and fan-out, and must prove retry exhaustion. Where should those bounds be declared?

**Branch:** Bounds declaration

**Recommended answer:** Fixture-declared budgets with schema maxima
> Each fixture policy declares its probe/retry/fan-out budgets as explicit
> fields; the schema enforces hard maxima and the simulator treats declared
> budgets as caps, reporting actual attempt counts in the resolution report.
> Exhaustion scenarios prove the cap cheaply (`budget = 1`), and CAR-006
> inherits budget fields it can pin to framework defaults — bounds stay
> visible in review rather than buried as constants.

**Alternatives offered:**
- Simulator constants only: fewer schema fields, but proving exhaustion means
  large fixtures or tests reaching into private constants, and CAR-006 gets no
  declared-budget contract.
- Budgets in a separate frozen config fixture: central and pinnable, but
  per-scenario exhaustion cases need override semantics anyway — two
  mechanisms for one concept.

**User's answer:** Fixture-declared budgets with schema maxima (Recommended)

---

### Q8. "Prove deterministic replay of every scenario" — what should the replay proof assert?

**Branch:** Determinism/replay proof

**Recommended answer:** Pinned expected reports, byte-identical
> Each scenario fixture pins its full expected resolution report; the test
> runs the simulator twice and asserts both runs are byte-identical to each
> other AND to the pinned report (canonical JSON serialization, no
> wall-clock/randomness inputs). Matches the CAR-004 `control-replay.json`
> precedent and the constitution's deterministic-I/O principle; any future
> semantic change shows up as a reviewable fixture diff.

**Alternatives offered:**
- Run-twice equality only: proves determinism but not correctness — a
  deterministic wrong answer passes, and CAR-006 gets no golden reports.
- Semantic field-level assertions: resilient to cosmetic changes, but
  unasserted fields drift silently.

**User's answer:** Pinned expected reports, byte-identical (Recommended)

---

### Q9. How should the ~15 mandated scenario cases be organized under `fixtures-fallback/`?

**Branch:** Fixture organization

**Recommended answer:** One self-contained corpus with `cases[]`
> A single `fallback-scenario-corpus.json` where each case bundles `{policy,
> synthetic snapshot, overrides, declared budgets, expected report}` — the
> replay unit is one case, fully readable in isolation. Matches the
> `control-replay.json` `cases[]` precedent, and reviewers diff one file when
> semantics change. Split only if it outgrows review comfort.

**Alternatives offered:**
- Per-scenario-family files: smaller files, but shared policies/snapshots
  duplicate or cross-reference, breaking the self-contained replay unit.
- Split inputs vs expected reports: clean stimulus/expectation separation, but
  every case review reads two files in parallel.

**User's answer:** One self-contained corpus, cases[] (Recommended)

---

### Q10. The shared size estimator returned warn (`estimated_loc` 770, `suggested_slices` 2) from coarse signals; the roadmap's authored budget says 257 reviewable LOC / 1 slice and the setup gate passed clean. Split CAR-005 or keep it as one spec?

**Branch:** Slice sizing

**Recommended answer:** Split into 2 vertical slices
> Protocol-recommended on estimator warn. Natural rule-family seam, each slice
> cutting schema → simulator → test end-to-end: slice 1 = resolution-failure
> semantics (five reason codes, snapshot projection, replay pinning); slice 2
> = structural rejections, override/helper paths, retry exhaustion. Noted
> honestly: the estimator is a forward guess from coarse signals (4 stories,
> ~10 files, ~18 FRs) and the authored budget disagrees.

**Alternatives offered:**
- Keep as one spec, single slice: the authored budget (257 LOC, "replay
  fixtures plus reason-code tests") was written knowing the artifact mix, and
  the setup gate passed clean.
- Defer to plan-time re-estimate: the roadmap itself says "re-estimate at
  scaffold", and the PR-time diff-mode gate is the accurate authority.

**User's answer:** Split into 2 vertical slices (Recommended)

**Notes:** Mid-interview delivery directive from the user, recorded verbatim:
"make sure we use gh-stack if it results in more than 1 pr". The 2-slice split
produces 2 PRs, so the slice PRs are managed as a gh-stack stacked-PR chain
(`gh stack` v0.0.8 verified installed); slice 2 stacks on slice 1.

---

### Q11. Alias re-pointing and platform route change are mandated scenarios, but the five pinned resolution codes don't name them. How should a route invalidated by alias re-point / platform route change be coded?

**Branch:** Invalidation mapping

**Recommended answer:** `preferred_model_unavailable` + `details` sub-code
> The route tuple pins alias + qualified resolved model ID; when the snapshot
> shows the alias yielding a different ID, that qualified tuple is unavailable
> — code `preferred_model_unavailable`, with a machine-readable sub-reason
> (`alias_repointed` | `platform_route_changed` | `model_absent`) in the
> diagnostics envelope's existing `details` object. Keeps the five-code enum
> exactly as both roadmaps pin it while staying queryable.

**Alternatives offered:**
- Add invalidation codes to the policy-violation enum: queryable at top level,
  but they're environment changes, not policy-authoring defects — the enum's
  meaning blurs.
- Prose detail only: zero schema surface, but tooling parses prose to
  distinguish an alias re-point from a plain absent model.

**User's answer:** preferred_model_unavailable + details sub-code (Recommended)

---

### Q12. For the unqualified `CLAUDE_CODE_SUBAGENT_MODEL` override scenario: at real dispatch that env var forces the model regardless of policy. What should the simulated resolution report assert?

**Branch:** Override semantics

**Recommended answer:** Override wins at dispatch; loud diagnostic + claims exclusion
> Honest simulation of documented runtime behavior: the report records the
> override as the effective dispatch tuple, emits a loud
> `unqualified_override` diagnostic from the policy-violation enum, marks the
> environment excluded from release claims, AND still reports what the
> qualified resolution would have been. Mirrors CAR-006's contract ("report
> non-qualified overrides loudly; release claims exclude overridden
> environments") without pretending the preflight can block an env var.

**Alternatives offered:**
- Simulator ignores the override, flags it: cleaner report, but it simulates
  behavior the runtime doesn't have — the fixture would "prove" semantics
  CAR-006 can't deliver.
- Override forces `no_safe_route`: strongest signal, but contradicts the
  roadmap — overridden environments are excluded from claims, not made
  unresolvable.

**User's answer:** Override wins at dispatch; loud diagnostic + claims exclusion (Recommended)

## Open Questions

- **What:** Exact slice-seam task allocation — which schemas/corpus cases land
  in slice 1 vs slice 2, given slice 2 stacks on slice 1's schemas in the
  gh-stack chain.
  **Why deferred:** Plan-level detail; the seam principle (resolution-failure
  semantics vs structural rejections + override/helper + exhaustion) was
  decided in Q10, but file-level allocation needs the real artifact list.
  **Suggested next step:** Resolve during `/speckit-plan` and `/speckit-tasks`;
  the PR-time diff-mode reviewability gate is the final authority on slice
  sizes.
- **What:** Estimator-vs-authored-budget divergence (770 warn vs 257 ok).
  **Why deferred:** The split decision stands, but if plan-time re-estimation
  lands near the authored 257 the maintainer may revisit whether 2 slices
  remain warranted.
  **Suggested next step:** Compare the plan estimator's output against the Q10
  decision during `/speckit-plan`; keep the split unless plan evidence clearly
  contradicts it.
- **What:** G56R-005 twin coordination — CAR-005's schemas, enums, and corpus
  structure become the first-mover parity template.
  **Why deferred:** G56R-005 has not scaffolded; per the parity contract and
  the CAR-012 lesson, promotion of any member to shared byte-identical
  `contracts/` must be a joint change landed on both platforms together.
  **Suggested next step:** When G56R-005 scaffolds, mirror the structural
  template from this spec's shipped artifacts; record any deliberate
  divergence with reasoning in both roadmaps.
- **What:** Exact closed membership of the `details` sub-reason enum from Q11
  (`alias_repointed` | `platform_route_changed` | `model_absent` was the
  pattern set; more members may surface while authoring the corpus).
  **Why deferred:** Specify-phase enumeration work; the interview fixed the
  pattern, not the exhaustive list.
  **Suggested next step:** Finalize the closed set in `/speckit-specify` FRs
  and enforce it in the resolution-report schema.
- **What:** Whether the recorded third-member divergence between the two
  roadmaps (`capability_probe_unavailable` on Claude vs
  `capability_discovery_unavailable` on Codex) should later be reconciled by a
  joint CAR/G56R roadmap amendment, or kept as a permanent intentional
  platform difference.
  **Why deferred:** Discovered during the autopilot Phase 0 grounding pass, not
  during the interview — see the 2026-07-29 revision note below. Reconciling it
  is a two-platform joint landing and is outside CAR-005's scope either way;
  only the *recording* of the divergence is in scope here.
  **Suggested next step:** Raise in Clarify Session 2 (enum closure) for an
  operator decision; CAR-005 pins the divergence as data regardless, so either
  answer leaves the shipped artifacts correct.

## Revision Notes

### 2026-07-29 — Q2/Q3 parity premise corrected (autopilot Phase 0)

Q2 asserted the five resolution codes are "mirrored line-for-line in the Codex
roadmap, so parity holds", and Q3 built the structural parity test on "the five
codes both roadmaps pin". **That premise is factually wrong.** Verified against
both roadmaps:

- `docs/ai/specs/claude-agent-routing-technical-roadmap.md:527-529` pins
  `preferred_model_unavailable`, `effort_unsupported`,
  **`capability_probe_unavailable`**, `treatment_probe_failed`, `no_safe_route`.
- `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md:536-538` pins
  `preferred_model_unavailable`, `effort_unsupported`,
  **`capability_discovery_unavailable`**, `treatment_probe_failed`,
  `no_safe_route`.

Four members are byte-identical; the third diverges (`_probe_` vs
`_discovery_`). The divergence reads as deliberate — the Codex scope is about
capability *discovery* and carries a Codex-only concern ("distinguish every
service reroute from these plugin reasons", "approved/unapproved service
reroute") with no Claude analogue.

**Corrected decisions (these supersede the Q2/Q3 wording above):**

1. CAR-005's resolution enum stays exactly the five codes the **Claude**
   roadmap pins, including `capability_probe_unavailable`. The Claude roadmap
   is authoritative for this platform. No rename, no sixth member.
2. The structural parity test asserts (a) exact set equality between the
   committed schema's resolution enum and the Claude roadmap's five codes,
   failing on drift in either direction; and (b) the *recorded* cross-platform
   divergence — four shared members identical, third member intentionally
   different — pinned as data so a silent change on either side fails.
3. No Codex-side artifact is edited (already a Non-goal). Reconciling shared
   contract members across platforms is a deliberate joint two-platform
   landing — exactly the CAR-012 situation Q3 avoided recreating.
4. **Open:** whether the divergence should later be reconciled by a joint
   CAR/G56R roadmap amendment or kept permanently. Carried into the Clarify
   phase; the operator owns the call. This is added to the Open Questions above.

### 2026-07-29 — Q9/Q10 seam conflict resolved in Q9's favour (Clarify Session 1)

Q9 (one self-contained corpus) and Q10 (two slices, stacked) cannot both hold
without slice 2 writing into a slice-1 file. **Q9 holds.** The corpus is the durable
contract CAR-006 re-proves its production resolver against, whereas Q10's seam is
delivery mechanics that stop existing once both PRs merge; when a permanent artifact
shape conflicts with a transient delivery mechanic, the mechanic yields. Two corpus
files would also reopen the "per-scenario-family files" alternative Q9 already
rejected on independent grounds — with a three-agent synthetic cast shared across all
cases, two files would duplicate or cross-reference the cast — and would require
amending FR-015 and weakening SC-007.

Q10's "slice 2 touches no slice-1 file" reading therefore yields to **append-only
additivity**: slice 2 appends and alters nothing. The same rule governs the
resolution-report schema, the simulator module, and the unit test. The literal
no-touch reading was unachievable anyway — the corpus is one file, the simulator is
one module, and slice 1 cannot pre-register a test path that does not yet exist.

### 2026-07-29 — Q10 split rationale corrected (Clarify Session 1)

Q10 recorded the split as protocol-recommended on the estimator's `warn`. The
justification is now known to be weaker than stated in one direction and stronger in
another:

- **No reviewability gate measures this surface.** `estimate-reviewable-loc` computes
  `production_files × 40`, so a 0-production-file feature projects 0 and passes; the
  setup gate merely scrapes an authored number; the PR-time gate thresholds that same
  declared figure. **One slice would pass every gate.**
- **The sibling precedent proves it.** CAR-004 — same primary surface, 0 production
  files, declared 250 reviewable LOC — shipped roughly 11,600 artifact lines in a
  single PR (#401).
- **The estimator signal is larger, not smaller, than recorded.** Re-run on the real
  spec (2 user stories, 10 files, 35 FRs) it returns 975 and 3 suggested slices.

The split therefore stands on **review burden and independent slice value**, not on a
LOC ceiling: slice 1 is what CAR-006 needs first and is valuable even if slice 2
slipped, and a single ~3,100–4,600-line PR spanning two rule families is the CAR-004
review experience this split exists to avoid repeating. Only an operator decision can
change it — re-estimation cannot, since every automated signal is blind here.

## Recommended Next Step

Setup mode — scaffolding has already happened in this run. Informational:

- Review this doc and the populated workflow file at
  `docs/ai/specs/.process/CAR-005-workflow.md`.
- Run `/speckit-pro:speckit-autopilot docs/ai/specs/.process/CAR-005-workflow.md`
  from the `car-005-availability-fallback-recovery` worktree.
- At PR-emission time, honor the Q10 delivery directive: two slice PRs managed
  as a gh-stack stacked-PR chain.

---
topic: "CAR-004 policy controls and adaptive comparators"
slug: "car-004-policy-controls-comparators"
date: "2026-07-27"
mode: "setup"
spec_id: "CAR-004"
source_input:
  type: "topic"
  ref: "CAR-004 scope section, docs/ai/specs/claude-agent-routing-technical-roadmap.md"
question_count: 15
stop_reason: "natural"
---

# Design Concept: CAR-004 Policy Controls and Adaptive Comparators

> **Source:** CAR-004 scope from `docs/ai/specs/claude-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-27
> **Questions asked:** 15
> **Stop reason:** natural (every queued branch walked, including the
> user-requested numeric-parameters extension; no new critical branches
> surfaced)

## Goals

- Freeze exactly the three AC-2.17 controls — unpinned, adaptive, and
  orchestration-changing — as content-addressed evaluation fixtures, with no
  fourth justified-high-effort arm: the all-max immutable production comparator
  already occupies that role on the Claude side (Q2).
- Author every control contract as new additive Claude-local schemas under
  `tests/speckit-pro/layer6-efficiency/contracts-claude/`, referencing frozen
  CAR-003 schemas by `$id`/digest without editing any mirrored member, and
  record every new member in a CAR-004 twin-handoff doc for G56R-004 to mirror
  (Q1, Q7).
- Bind the adaptive control's escalation/de-escalation signals exclusively to
  existing stable CAR-003 trace and score-bundle members (terminal state,
  failure plane/code, retry count, raw-token/duration budget thresholds); no
  new telemetry fields (Q3).
- Freeze the adaptive discipline: at most one escalation per objective to the
  next-higher qualified route, de-escalation only between objectives after
  N = 3 consecutive clean passes, never mid-objective, always inside the frozen
  candidate set (Q11, Q14).
- Freeze the unpinned control as one arm bound to the environment contract's
  already-pinned parent-session model/effort; a different parent session is a
  different control version by content-address (Q4).
- Account the orchestration-changing control as a parent-plus-children
  aggregate: the objective-level trace sums the complete raw token vector,
  duration, and retries across the parent and every automatically spawned
  child, under a content-addressed topology descriptor (Q5).
- Freeze control dominance as CAR-003's environment-independent Pareto rule
  with a 10% relative per-component practical margin: materially dominant only
  when at least one raw-vector/duration component improves by >= 10% and no
  component (retries and compaction included) is worse; mixed or inconclusive
  results yield no dominance verdict and no messaging restriction (Q6, Q13).
- Reserve the untouched CAR-011 comparison partition as a named
  content-addressed entry in the existing corpus/partition registry, enforced
  by a unit-test guard that fails if any CAR-004 replay or smoke evidence row
  references a reserved member (Q8).
- Encode the messaging consequence as a machine-readable verdict-to-claim-class
  mapping inside the control-comparison contract so CAR-011's release-packet
  validation binds to it mechanically (Q9).
- Validate all three controls with synthetic replay fixtures plus one bounded
  API-key live smoke each — at most 5 non-reserved objectives, one repetition,
  a 1M raw-token ceiling, and a 30-minute wall-clock cap per control —
  exercising a real dispatch-time escalation, a real inherit resolution, and a
  real harness-parallel child aggregation respectively (Q10, Q15).

## Non-goals

- No dominance conclusion about the future static core — CAR-011 owns the
  comparison; CAR-004 produces no outcome-bearing scored evidence (Q10
  rejected the scored mini-campaign option).
- No fourth justified-high-effort control arm (Q2) — recorded in the
  twin-handoff as a sanctioned platform divergence from G56R-004's named
  third control.
- No production adaptive-routing or orchestration feature; the
  orchestration-changing control stays policy-level evaluation only (Q5,
  roadmap out-of-scope).
- No edits to any frozen CAR-003 schema, including the mirrored members
  already on CAR-012's reconciliation list (Q7).
- No new telemetry fields and no reopening of CAR-002's frozen telemetry
  profile (Q3).
- No unpinned-control matrix over multiple parent-session models (Q4).
- No subscription-authenticated smoke row — the scored-campaign smoke-row rule
  does not attach to CAR-004's non-scored validation (Q10).

## Design Tree (Q&A log)

### Q1. CAR-004 freezes control contracts that G56R-004 — ready but not started — will eventually mirror. How should CAR-004 handle parity for its control contracts?

**Branch:** Parity posture

**Recommended answer:** Claude-local + twin-handoff
> Author schemas in `contracts-claude/` and record every member G56R-004 must
> mirror in a CAR-004 twin-handoff doc — the exact pattern CAR-003 used.
> Parity becomes a named follow-up obligation, not a blocker; CAR-005 stays
> unblocked. Grounded in the CAR-012 reconciliation debt created when the
> twins landed mirror-adjacent contracts asynchronously.

**Alternatives offered:**
- Joint drop with G56R-004: byte-identical mirrors from day one, but
  serializes CAR-004 behind Codex-side work.
- Independent with no parity obligation: fastest, but knowingly recreates the
  CAR-012 class of debt against a shared product contract.

**User's answer:** Claude-local + twin-handoff (Recommended)

---

### Q2. AC-2.17 names three Claude-side controls, but the Codex twin names 'justified high-effort' as its third. What control set should CAR-004 freeze?

**Branch:** Control-set composition

**Recommended answer:** Three per AC-2.17
> Unpinned, adaptive, orchestration-changing — exactly as the PRD freezes
> them. A separate high-effort control would duplicate the all-max immutable
> production comparator CAR-003 already binds; the twin-handoff records this
> as a sanctioned platform divergence (the parity contract allows content to
> differ where platform baselines differ).

**Alternatives offered:**
- Add a fourth high-effort control: symmetric parity, but a redundant
  evaluation arm on this platform.
- Swap high-effort in for orchestration-changing: contradicts AC-2.17 as
  written; would need a PRD amendment first.

**User's answer:** Three per AC-2.17 (Recommended)

---

### Q3. Where should the adaptive control's frozen escalation/de-escalation signals come from?

**Branch:** Adaptive signals

**Recommended answer:** Existing trace members only
> Bind the signal enum to fields CAR-003 already freezes as stable — terminal
> state, failure plane/code, retry count, and raw-token/duration budget
> thresholds from the execution trace and score bundle. No new telemetry:
> AC-2.4's profile stays untouched and every signal is already
> replay-provable.

**Alternatives offered:**
- Extend telemetry for richer signals (compaction events, latency
  percentiles): stronger comparator but reopens CAR-002's frozen profile.
- Terminal-failure-only binary: simplest, but CAR-011 would compare the
  static core against a strawman.

**User's answer:** Existing trace members only (Recommended)

---

### Q4. How many unpinned arms should CAR-004 freeze?

**Branch:** Unpinned binding

**Recommended answer:** One arm, pinned parent
> A single content-addressed control bound to the environment contract's
> already-pinned parent-session model/effort. A different parent session is a
> different control version by content-address — consistent with "controls
> are pure evaluation fixtures".

**Alternatives offered:**
- Matrix over parent models: richer inherit-behavior evidence but multiplies
  arms, budget, and the multiplicity position.
- Defer binding to CAR-011: violates freeze-before-cohort-selection — the
  comparator could be constructed post-hoc.

**User's answer:** One arm, pinned parent (Recommended)

---

### Q5. How should the orchestration-changing control account its resources?

**Branch:** Orchestration accounting

**Recommended answer:** Parent+children aggregate
> The control's objective-level trace sums the complete raw token vector,
> duration, and retries across the parent and every automatically spawned
> child, under a content-addressed topology descriptor. Mirrors the twin's
> explicit child-work rule; anything less understates the control's true cost
> and biases the CAR-011 comparison.

**Alternatives offered:**
- Parent-only with child-count metadata: simpler fixtures, artificially cheap
  control.
- Named placeholder with no execution contract: fails the roadmap's own
  freeze requirement.

**User's answer:** Parent+children aggregate (Recommended)

---

### Q6. What rule should CAR-004 freeze for control dominance?

**Branch:** Dominance rule

**Recommended answer:** Same Pareto rule + margins
> Reuse CAR-003's environment-independent Pareto formalism (amended
> 2026-07-24) with predeclared per-component practical margins — material
> dominance requires clearing the margin on at least one component and losing
> none. One dominance formalism across the whole program; mixed or
> inconclusive yields no dominance and no messaging restriction.

**Alternatives offered:**
- Control-specific weighted scalar: AC-2.5 forbids forced weighted ranking;
  reintroducing it reopens the settled price-weighted debate.
- Zero-margin strict Pareto: trivial wins would trigger the messaging
  restriction; "material" is the AC's word.

**User's answer:** Same Pareto rule + margins (Recommended)

---

### Q7. How should CAR-004's control contracts materialize against CAR-003's frozen schemas?

**Branch:** Contract form

**Recommended answer:** New additive schemas only
> New standalone control-policy schemas in `contracts-claude/` referencing
> frozen CAR-003 schemas by `$id`/digest without editing them. No unilateral
> touch on any mirrored member — the joint-change rule stays unviolated, and
> the twin-handoff lists the new members for G56R-004.

**Alternatives offered:**
- Version-bump existing schemas to 1.1.0: structurally tidy but edits
  mirrored contracts unilaterally — the CAR-012 class of debt, on schemas
  already on CAR-012's list.
- Python-only contracts: breaks the program's schema+lib+replay pattern and
  weakens content-addressing.

**User's answer:** New additive schemas only (Recommended)

---

### Q8. How should the untouched CAR-011 comparison partition be reserved and proven?

**Branch:** Partition reservation

**Recommended answer:** Registry entry + guard test
> Reserve a named partition with content-addressed membership in the existing
> corpus/partition registry, plus a unit-test guard that fails if any CAR-004
> replay or smoke evidence row references a reserved member. Non-consumption
> becomes machine-checked, matching CAR-003's used-exactly-once discipline.

**Alternatives offered:**
- Separate reserved corpus file: fragments corpus governance into two
  sources of truth.
- Analysis-plan prose only: an accidental consumption surfaces only after the
  evidence is burned.

**User's answer:** Registry entry + guard test (Recommended)

---

### Q9. How should the frozen messaging consequence be encoded?

**Branch:** Messaging rule

**Recommended answer:** Machine-readable mapping
> A verdict-to-claim-class mapping inside the new control-comparison contract
> (dominant / not-dominant / inconclusive mapped to permitted wording
> classes). CAR-011's release-packet validation binds to it mechanically, and
> the twin mirrors one unambiguous member instead of parallel prose. Grounded
> in AC-2.16's rule that thresholds live in predeclared artifacts, not
> post-hoc review judgment.

**Alternatives offered:**
- Frozen analysis-plan prose: human review enforcement is exactly what
  AC-2.16 pushes out of review.
- Defer encoding to CAR-011: risks shaping the rule after the dominance
  result is known.

**User's answer:** Machine-readable mapping (Recommended)

---

### Q10. What smoke depth should CAR-004 commit to?

**Branch:** Validation depth

**Recommended answer:** Replay + 1 live smoke each
> Synthetic replay fixtures for all three controls, plus one bounded API-key
> live smoke per control on non-reserved data: adaptive proves a real
> dispatch-time model switch, unpinned proves a real inherit run,
> orchestration-changing proves a harness-parallel dispatch with child
> aggregation. Non-scored, so the subscription smoke-row rule for scored
> campaigns does not attach.

**Alternatives offered:**
- Replay-only with smoke deferred to CAR-011: execution-contract breakage
  would surface at integration time.
- Scored mini-campaign per control: outcome-bearing evidence CAR-004 is
  barred from generating.

**User's answer:** Replay + 1 live smoke each (Recommended)

---

### Q11. What escalation discipline should the frozen adaptive policy carry?

**Branch:** Adaptive bounds

**Recommended answer:** One step up, between-objective down
> At most one escalation per objective (retry the failed objective once on
> the next-higher qualified route); de-escalation decided only between
> objectives, never mid-objective. No oscillation by construction — matches
> the bounded fan-out/retry discipline CAR-005 applies to the resolver, and
> stays inside the frozen candidate set.

**Alternatives offered:**
- Multi-step ladder: stronger comparator, but each rung multiplies retry cost
  and the replay fixture matrix.
- Escalate-only: converges to the ceiling and stops being meaningfully
  adaptive.

**User's answer:** One step up, between-objective down (Recommended)

---

### Q12. Wrap up and synthesize, or keep going?

**Branch:** Checkpoint

**Recommended answer:** Wrap up — synthesize now
> Every queued branch was walked and the size estimator matched the roadmap
> at 250 LOC / 1 slice / ok.

**Alternatives offered:**
- Keep going — numeric parameters: interview the concrete numeric values
  rather than leaving them to the frozen registry.
- Keep going — another branch (free-text).

**User's answer:** Keep going — numeric parameters

---

### Q13. What per-component practical margin should define 'material' control dominance?

**Branch:** Numeric parameters — dominance margin

**Recommended answer:** 10% relative per component
> Dominant only if >= 10% better on at least one component while no worse on
> every other (retries/compaction included). Relative margins stay
> environment-independent per AC-2.5; 10% is a conventional
> practical-significance bar. Moderate confidence — the value freezes in the
> content-addressed registry and the twin must mirror it.

**Alternatives offered:**
- 5% relative: catches smaller improvements but edges toward noise-scale
  dominance verdicts.
- 20% relative: protects the static-core claim but risks dismissing a
  genuinely meaningful 10-15% advantage.

**User's answer:** 10% relative per component (Recommended)

---

### Q14. After how many consecutive clean passes should the adaptive policy de-escalate?

**Branch:** Numeric parameters — de-escalation threshold

**Recommended answer:** N = 3
> Three consecutive clean objectives before stepping down: responsive enough
> to exercise de-escalation within a bounded campaign, stable enough that one
> lucky objective cannot trigger downgrade-fail-escalate oscillation.

**Alternatives offered:**
- N = 2: faster adaptation, weaker stability evidence, more cross-objective
  churn.
- N = 5: may never de-escalate in bounded smoke runs, leaving the path
  untested.

**User's answer:** N = 3 (Recommended)

---

### Q15. What bounds should each control's single live smoke run freeze?

**Branch:** Numeric parameters — smoke caps

**Recommended answer:** 5 objectives / 1 rep / 1M tokens
> At most 5 non-reserved objectives, one repetition, a 1M raw-token ceiling,
> and a 30-minute wall-clock cap per control smoke, recorded through the
> experiment-policy budget fields. Enough to exercise the interesting path
> while staying unmistakably non-scored. Token/time numbers are
> moderate-confidence — flagged for the registry freeze.

**Alternatives offered:**
- 3 objectives / 500K / 15 min: cheapest, but the adaptive smoke may only
  prove the happy path.
- 10 objectives with looser caps: doubles spend and resembles a
  characterization run.

**User's answer:** 5 objectives / 1 rep / 1M tokens (Recommended)

---

## Open Questions

- **What:** Twin-handoff coordination timing with the G56R-004 owner (the
  Codex twin is Ready but unstarted; the two roadmaps also name different
  third controls).
  **Why deferred:** Cross-platform coordination is outside a single-spec
  interview; the joint-change rule only engages once both sides have landed.
  **Suggested next step:** Publish the CAR-004 twin-handoff doc in the spec
  PR (CAR-003 pattern) and notify the G56R-004 owner before that PR merges;
  any member G56R-004 cannot mirror joins the CAR-012-class reconciliation
  list.

- **What:** Final registry serialization of the interview-frozen numerics —
  the per-component 10% margin map, the N = 3 de-escalation threshold, the
  smoke caps (5 objectives / 1 rep / 1M tokens / 30 min), and the alpha
  allocation for CAR-011's predeclared secondary control arms.
  **Why deferred:** AC-2.16 places numeric thresholds in the frozen analysis
  plan or a content-addressed registry, which materializes during
  Plan/Implement, not during scoping. The 1M-token and 30-minute smoke
  ceilings were flagged moderate-confidence in Q15.
  **Suggested next step:** Freeze the values in the CAR-004 analysis-plan
  registry entries during implementation; direct `/speckit-clarify` at the
  smoke ceilings if evidence at plan time suggests different bounds.

## Recommended Next Step

Setup mode — scaffolding has already happened. The populated workflow file is
`docs/ai/specs/.process/CAR-004-workflow.md`; execute it with
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/CAR-004-workflow.md`
from the `car-004-policy-controls-comparators` worktree.

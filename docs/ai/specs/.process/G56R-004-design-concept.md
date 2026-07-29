---
topic: "G56R-004 Policy Controls and Adaptive Comparators"
slug: "g56r-004-policy-controls-adaptive-comparators"
date: "2026-07-28"
mode: "setup"
spec_id: "G56R-004"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
question_count: 13
stop_reason: "natural"
---

# Design Concept: G56R-004 Policy Controls and Adaptive Comparators

> **Source:** `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-28
> **Questions asked:** 13
> **Stop reason:** natural

## Goals

- Preserve the user's stated constraint — "make sure it stays aligned with
  CAR-003" — by making the frozen CAR-003/G56R-003 contract boundary explicit
  in every policy, comparison, replay, and parity decision below.
- Treat `docs/ai/specs/.process/CAR-004-twin-handoff.md` as the complete
  cross-platform mirror contract, apply it against the current frozen
  G56R-003/CAR-003 evaluation bindings, and leave the already-recorded
  evaluation-contract reconciliation work to G56R-012 (Q1).
- Freeze exactly three Codex policy controls: unpinned, adaptive, and
  justified-high-effort. Automatically spawned child work is a modifier whose
  full cost is included in the control evidence, not a fourth control arm
  (Q2, Q7).
- Author new additive Codex-local policy-control and control-comparison
  contracts with Codex identifiers. Preserve the twin handoff's record shapes,
  required members, closed enums, frozen numerics, decision semantics, and
  enforcement guards; bind frozen G56R-003/CAR-003 artifacts by stable ID and
  digest without editing them (Q3).
- Re-derive the mirrored contract surface in both directions and fail closed on
  missing, extra, or digest-mismatched members. Never normalize parity drift
  silently (Q4).
- Build the adaptive ladder only from ordered, admitted G56R-003 routes and use
  only the frozen Codex terminal-state, failure-plane/code, retry, and budget
  signals while preserving CAR-004's total response maps and precedence rules
  (Q5).
- Make the unpinned control reproducible by binding one control version to the
  frozen parent-session model, effort, client, and environment contract; a
  changed parent context creates a new content address (Q6).
- Bind the justified-high-effort control to one already-qualified high-effort
  route with an explicit eligibility predicate and rationale, and aggregate all
  automatically spawned child work into its governed evidence (Q7).
- Mirror CAR-004's gate-first material-dominance contract exactly: eight
  dimensions, direction-of-preference semantics, confidence method, 10%
  relative margins, and no-verdict handling for mixed, incomplete, tied, or
  statistically uncertain evidence (Q8).
- Reserve G56R-011's untouched integrated-confirmation work through a
  content-addressed partition-registry entry plus a guard that rejects any
  replay or smoke row consuming a reserved objective (Q9).
- Validate every control with deterministic replay fixtures and one bounded,
  non-scored smoke on the supported ChatGPT-sign-in path. Preserve raw captures
  off-repository and commit only governed, content-addressed evidence (Q10).
- Mirror the CAR-004 smoke limits: at most five non-reserved objectives, one
  repetition, a 1,000,000 raw-token ceiling, 30 minutes per control, and the
  handoff's component and cache ceilings (Q11).
- Freeze the verdict-to-claim-class mapping so G56R-011 can enforce release
  wording mechanically while G56R-004 itself reaches no release verdict (Q12).
- Keep the feature as one vertical slice. The shared estimator returned
  `estimated_loc: 235`, `suggested_slices: 1`, and `status: ok`, matching the
  roadmap's 235-LOC one-slice budget.

## Non-goals

- Reopening, editing, re-versioning, or reinterpreting frozen G56R-003 or
  CAR-003 contracts (Q1, Q3).
- Absorbing G56R-012's existing mirrored evaluation-contract reconciliation
  scope into G56R-004 (Q1).
- A fourth control arm or a full topology-changing arm on Codex; the closed
  three-control set and its one sanctioned platform-value divergence remain
  intact (Q2).
- Runtime discovery of an adaptive or justified-high-effort route outside the
  frozen G56R-003 admitted set (Q5, Q7).
- Warning-only or manual-only parity validation (Q4).
- Production adaptive routing, resolver behavior, installer behavior, or
  shipped static route defaults; this is a repository-only evaluation-policy
  surface.
- Outcome-bearing scored control campaigns or a conclusion about whether the
  future static `core_routing_policy_id` is dominated; G56R-011 owns that
  comparison (Q10, Q12).
- Requiring API-key authentication for the smoke path, committing raw model or
  prompt captures, or treating non-scored smoke evidence as qualification
  evidence (Q10).
- Weakening, reshaping, or silently omitting a mirror-required member that
  Codex cannot represent (Q13).

## Design Tree (Q&A log)

### Q1. Which artifact should govern G56R-004 where CAR-004's mirror contract touches the frozen CAR-003/G56R-003 evaluation surface?

**Branch:** Alignment authority

**Recommended answer:** Twin handoff (Recommended)
> Apply CAR-004's complete twin handoff against the current frozen
> G56R-003/CAR-003 bindings, while leaving existing evaluation-contract
> reconciliation to G56R-012. The handoff explicitly adds decision-semantics
> and enforcement-guard categories because CAR-003's earlier schema-shaped
> handoff did not capture those rules.

**Alternatives offered:**
- CAR-003 directly: derive only from CAR-003 and omit CAR-004's newer
  decision-semantics and enforcement-guard categories.
- Reopen contracts: modify frozen G56R-003/CAR-003 contracts during G56R-004,
  expanding scope into reconciliation work.

**User's answer:** Twin handoff (Recommended)

---

### Q2. Which three Codex-side control kinds should G56R-004 freeze despite the PRD and roadmap using different wording for the third arm?

**Branch:** Control-set composition

**Recommended answer:** Roadmap set (Recommended)
> Freeze unpinned, adaptive, and justified-high-effort; treat automatically
> spawned child work as a modifier. This follows the G56R-004 roadmap and the
> CAR-004 twin handoff's sole sanctioned platform divergence while preserving
> the shared closed-at-three structure.

**Alternatives offered:**
- PRD set: freeze unpinned, adaptive, and topology-changing as three full arms,
  matching AC-2.17 literally but contradicting the current roadmap and handoff.
- Four controls: include both justified-high-effort and topology-changing,
  violating the handoff's closed-at-three contract.

**User's answer:** Roadmap set (Recommended)

---

### Q3. How should G56R-004 materialize its policy-control and comparison contracts relative to frozen G56R-003/CAR-003 artifacts?

**Branch:** Contract form and data integrity

**Recommended answer:** Additive Codex contracts (Recommended)
> Create Codex-local standalone contracts with Codex IDs, preserve the
> handoff's shapes and semantics, and bind frozen evaluation artifacts by
> stable ID plus digest without editing them. This follows the repository's
> existing `contracts-codex-specification/` pattern and the constitution's
> KISS/additive-change discipline.

**Alternatives offered:**
- Extend old schemas: add control members directly to frozen evaluation
  schemas, coupling the feature to already-merged contracts.
- Python only: implement validation solely in Python, losing the schema,
  digest, and twin-completeness contract.

**User's answer:** Additive Codex contracts (Recommended)

---

### Q4. What should happen when a G56R-004 contract, enum, numeric, or CAR-003/G56R-003 digest no longer matches the published twin handoff?

**Branch:** Parity validation and failure handling

**Recommended answer:** Fail closed (Recommended)
> Re-derive the handoff surface in both directions and reject missing, extra,
> or digest-mismatched members; never silently normalize drift. CAR-004 already
> established this as a machine-checked completeness claim for categories one
> through six, and G56R-004 must extend the same protection to its mirror.

**Alternatives offered:**
- Warn and continue: report differences while allowing fixtures and smoke
  evidence to proceed.
- Manual review only: rely on reviewers to compare large contracts without an
  executable completeness check.

**User's answer:** Fail closed (Recommended)

---

### Q5. How should the adaptive control obtain its escalation ladder and response signals on Codex?

**Branch:** Adaptive routing and exact treatment

**Recommended answer:** Bind frozen Codex evidence (Recommended)
> Use the ordered admitted routes from G56R-003 and only its frozen terminal
> state, failure plane/code, retry, and budget signals; preserve CAR-004's total
> maps and precedence semantics. Copying Claude route literals would not prove
> a valid Codex treatment.

**Alternatives offered:**
- Copy Claude literals: reuse CAR-004's example route names and Claude bindings
  even when they are not admitted Codex tuples.
- Discover at runtime: let each run construct a ladder dynamically, making the
  content-addressed control unstable and potentially using unqualified routes.

**User's answer:** Bind frozen Codex evidence (Recommended)

---

### Q6. What should identify the Codex unpinned control so its behavior remains reproducible?

**Branch:** Unpinned-control identity

**Recommended answer:** Pinned parent context (Recommended)
> Bind one unpinned control version to the frozen parent-session model, effort,
> client, and environment contract; a changed parent creates a new content
> address. This preserves inherited behavior without treating different parent
> contexts as the same experiment arm.

**Alternatives offered:**
- Any parent session: treat all inherited parent configurations as the same
  arm, making results incomparable across environments.
- Parent model only: pin only the model while allowing effort and client/runtime
  details to vary within one control identity.

**User's answer:** Pinned parent context (Recommended)

---

### Q7. How should the justified-high-effort control decide when and what to run?

**Branch:** High-effort eligibility and orchestration accounting

**Recommended answer:** Frozen eligible route (Recommended)
> Bind one already-qualified high-effort route plus an explicit eligibility
> predicate and rationale; include all automatically spawned child work in the
> control's aggregate evidence. This makes "justified" executable instead of a
> post-hoc label and prevents the control from selecting an unqualified route.

**Alternatives offered:**
- Always max effort: run the maximum visible effort for every objective,
  turning the arm into an unbounded duplicate rather than a justified control.
- Runtime best guess: choose model and effort dynamically from current
  availability without a frozen route or eligibility rule.

**User's answer:** Frozen eligible route (Recommended)

---

### Q8. Should Codex use the same material-dominance semantics and frozen margins as the CAR-004 handoff?

**Branch:** Statistical decision contract

**Recommended answer:** Mirror exactly (Recommended)
> Keep the same gate-first order, eight dimensions, direction rules,
> confidence method, 10% relative margins, and inconclusive/no-verdict handling
> so identical evidence reaches the same decision on both platforms. Only
> platform-bound identifiers and the sanctioned control value differ.

**Alternatives offered:**
- Codex-specific margins: choose different numeric margins for Codex, creating
  platform-specific verdict semantics.
- Weighted score: collapse dimensions into a scalar score, reopening the
  settled no-weights Pareto decision.

**User's answer:** Mirror exactly (Recommended)

---

### Q9. How should G56R-004 protect the untouched integrated-confirmation work reserved for G56R-011?

**Branch:** Partition governance

**Recommended answer:** Registry plus guard (Recommended)
> Create a content-addressed reserved partition entry owned by G56R-004 and
> fail any replay or smoke row that consumes one of its objectives. This keeps
> the final comparison partition predeclared and machine-protected before
> outcomes exist.

**Alternatives offered:**
- Prose reservation: record the reservation only in documentation and depend
  on later reviewers to notice accidental consumption.
- Defer reservation: let G56R-011 create the partition after control behavior
  is known, risking post-outcome selection.

**User's answer:** Registry plus guard (Recommended)

---

### Q10. What validation depth should G56R-004 require for each of its three controls?

**Branch:** Validation depth and evidence boundary

**Recommended answer:** Replay plus smoke (Recommended)
> Require deterministic replay fixtures and one bounded, non-scored smoke per
> control on the supported ChatGPT-sign-in path; preserve raw captures
> off-repository and record only governed evidence. This proves the execution
> contract without consuming qualification or confirmation evidence.

**Alternatives offered:**
- Replay only: defer real dispatch proof until G56R-011, moving integration
  risk downstream.
- Scored campaigns: generate outcome-bearing comparative evidence now,
  violating G56R-004's policy-level-only boundary.

**User's answer:** Replay plus smoke (Recommended)

---

### Q11. Which bounds should the Codex non-scored control smokes freeze?

**Branch:** Resource and time budgets

**Recommended answer:** Mirror CAR-004 (Recommended)
> Use at most five non-reserved objectives, one repetition, 1,000,000 raw
> tokens, and 30 minutes per control, including the handoff's component and
> cache ceilings. Mirroring the frozen bounds preserves cross-platform
> comparability and prevents post-hoc budget tuning.

**Alternatives offered:**
- Half-size smokes: use three objectives, 500,000 tokens, and 15 minutes,
  lowering cost but no longer mirroring the frozen contract.
- Plan-time bounds: leave all limits open until implementation planning,
  weakening the content-addressed precommitment.

**User's answer:** Mirror CAR-004 (Recommended)

---

### Q12. How should the later release workflow consume the G56R-004 dominance result?

**Branch:** Release messaging

**Recommended answer:** Frozen claim mapping (Recommended)
> Mirror the machine-readable verdict-to-claim-class mapping so only a
> materially dominated static release loses efficient, optimal, or
> best-measured claims; G56R-004 itself makes no release verdict. This preserves
> the roadmap's operational-simplicity allowance without leaving wording to
> post-hoc review judgment.

**Alternatives offered:**
- Review prose: leave wording restrictions to human interpretation in
  G56R-011's PR review.
- Block static release: make dominance prohibit shipping entirely,
  contradicting the roadmap's operational-simplicity allowance.

**User's answer:** Frozen claim mapping (Recommended)

---

### Q13. If implementation finds a CAR-004 mirror-required member that Codex genuinely cannot represent, what should G56R-004 do?

**Branch:** Cross-platform reconciliation

**Recommended answer:** Raise reconciliation (Recommended)
> Keep the Claude contract unchanged, name the declined member explicitly, and
> add a paired CAR/G56R reconciliation roadmap item; do not silently drop or
> weaken it. This follows the twin handoff's published disposition contract and
> keeps the divergence auditable.

**Alternatives offered:**
- Best-effort omission: ship without the member and document the difference
  only in prose.
- Change CAR-004: rewrite the already-frozen Claude contract to fit Codex
  during this spec.

**User's answer:** Raise reconciliation (Recommended)

## Open Questions

- **What:** Which exact admitted G56R-003 route tuple and stable Codex IDs should
  the justified-high-effort control bind?
  **Why deferred:** The design fixes the selection rule and eligibility
  contract, but the Plan phase must read the current frozen successor-capability
  evidence rather than copying a route name into the scaffold.
  **Suggested next step:** During Plan, select one already-qualified high-effort
  tuple from the frozen G56R-003 evidence, record its ID/digest and rationale,
  and fail closed if no eligible tuple exists.

- **What:** Authorization and operator availability for the three bounded live
  smokes.
  **Why deferred:** Q10 requires the smokes, but executing live model work is an
  implementation/UAT action rather than a scaffold action and may send governed
  repository context off-box.
  **Suggested next step:** Keep deterministic replay in the automated suite and
  obtain explicit operator authorization before running each local,
  ChatGPT-sign-in smoke; record an unevidenced-success-criteria gap if a smoke
  remains unrun.

- **What:** Whether any mirror-required CAR-004 member is genuinely
  unrepresentable on Codex.
  **Why deferred:** Q13 defines the disposition, but only Specify/Plan and the
  bidirectional completeness check can establish a concrete mismatch.
  **Suggested next step:** Name every mismatch during Clarify; mirror it or raise
  the paired reconciliation entry before implementation continues.

## Recommended Next Step

Setup mode: finish the G56R-004 scaffold, then start a new Codex task rooted at
the dedicated worktree and run `$speckit-autopilot` with
`docs/ai/specs/.process/G56R-004-workflow.md`.

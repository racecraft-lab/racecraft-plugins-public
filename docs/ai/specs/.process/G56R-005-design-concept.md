---
topic: "G56R-005 Model Availability, Fallback, and Recovery Simulation"
slug: "g56r-005-model-availability-fallback-recovery"
date: "2026-08-22"
mode: "setup"
spec_id: "G56R-005"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
question_count: 13
stop_reason: "natural"
---

# Design Concept: G56R-005 Model Availability, Fallback, and Recovery Simulation

> **Source:** `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
> **Date:** 2026-08-22
> **Questions asked:** 13
> **Stop reason:** natural

> **Blind-spot pass:** ran — 5 findings surfaced, 2 set aside

## Goals

- Define a Codex-local, deterministic simulation contract for route
  availability, fallback, service reroute attribution, and recovery without
  changing the frozen Claude route contract (Q1, Q6).
- Use the roadmap reason-code vocabulary, including
  `capability_discovery_unavailable`, and defer cross-platform spelling
  reconciliation with Claude's existing `capability_probe_unavailable` to the
  already-planned CAR-012/G56R-012 joint work (Q1).
- Keep route resolution pure while proving installer-state consequences through
  isolated fake-home fixtures: atomic no-write, rollback, and preservation of
  the previous-known-good install (Q2).
- Derive the required Codex agent roster from `speckit-pro/codex-agents` and the
  installer's required set; materialize agents only under fake homes (Q3).
- Use deterministic synthetic `platform_route_changes` replay as the required
  service-reroute evidence. Live smokes remain operator-only and explicitly
  unrun, so this spec makes no live-availability claim (Q4).
- Represent campaign/workflow time, retry, fan-out, context-growth,
  cancellation, and escalation/de-escalation limits as separate deterministic
  harness controls rather than overloading the route report's existing
  candidate/probe budgets (Q5).
- Create a Codex-specific resolver driven by Codex schemas and fixtures, reusing
  only contract-compatible parsing, canonicalization, and serialization
  utilities; do not import the Claude resolver or extract a broad shared
  abstraction in this spec (Q6).
- Emit all applicable failure reasons in stable evaluation order and a single
  terminal route outcome. `no_safe_route` is terminal, not a replacement for
  the preceding diagnostic evidence (Q7).
- Treat an explicit model-and-effort override as strict: an incompatible tuple
  stops before any write, does not fall back, and preserves the existing install
  (Q8).
- Permit an unavailable optional helper to be omitted only when a separately
  qualified no-helper route exists. Required agents remain an atomic,
  all-or-nothing set (Q9).
- Keep attributed platform reroutes separate from plugin fallback reasons.
  Approved reroutes remain scorable; unapproved reroutes fail closed and never
  become resolver inputs (Q10).
- Enforce resolution and recovery with one bounded, non-recursive sequential
  state machine. Cancellation is terminal and no retry may occur afterward
  (Q11).
- Allow fallback to change only the explicit model and effort route identity.
  Instructions, tools, skills, MCP, sandbox, mutation policy, and output
  contract must remain byte-identical (Q12).
- Complete one thin vertical slice with a full scenario matrix, byte-stable
  reports, fail-closed invalid cases, fake-home state proofs, targeted tests,
  and the full repository suite (Q13).
- Keep the roadmap's single-slice decision. The shared estimator used four user
  stories, ten files, eighteen functional-requirement groups, and a modifying
  change; it returned `estimated_loc: 385`, `suggested_slices: 1`, and
  `status: ok`.

## Non-goals

- Production capability-aware resolver or installer wiring; G56R-006 owns that
  implementation (Q2, Q13).
- Live model calls, live capability discovery, or live service-reroute
  qualification. G56R-004's operator-only smoke boundary remains unchanged
  (Q4).
- Changes to frozen G56R-004/CAR-004 evidence, frozen Claude fallback schemas,
  or the existing Claude resolver (Q1, Q6).
- Resolving the cross-platform reason-code spelling divergence before
  CAR-012/G56R-012 (Q1).
- Extracting a new cross-platform resolver framework or cloning the Claude
  module into a second implementation (Q6).
- Automatic fallback from an incompatible strict override, generic-agent
  substitution, adjacent unqualified models, inherited/omitted model or effort,
  or partial required-agent installation (Q8, Q9).
- Letting service-side reroutes silently influence plugin resolution or
  qualification (Q10).
- Recursive fallback, parallel probe fan-out, retries after cancellation, or
  production checkpoint/resume scheduling (Q5, Q11).
- Payload regeneration, plugin version changes, release-artifact changes, or
  docs-site feature work. The expected surface is repository-only simulation
  and validation code (Q13).

## Design Tree (Q&A log)

### Q1. Which contract should own the roadmap reason code when the existing Claude simulator uses a different spelling?

**Branch:** Reason-code ownership

**Recommended answer:** Codex-local code (Recommended)
> Define the Codex-local contract with
> `capability_discovery_unavailable`, preserve the archived Claude contract,
> and record the divergence for CAR-012/G56R-012 reconciliation.

**Alternatives offered:**
- Reuse Claude spelling: use `capability_probe_unavailable` on Codex despite the
  G56R roadmap vocabulary.
- Edit shared history: change the frozen Claude contract and its evidence now.

**User's answer:** Codex-local code (Recommended)

---

### Q2. How should the simulation prove both pure resolution and installer recovery semantics?

**Branch:** Recovery proof boundary

**Recommended answer:** Two-layer proof (Recommended)
> Keep the resolver pure and add fake-home installer fixtures for atomic
> no-write, rollback, and previous-known-good preservation.

**Alternatives offered:**
- Resolver only: defer every filesystem-state consequence to G56R-006.
- Installer-first: wire the production installer now and test through it.

**User's answer:** Two-layer proof (Recommended)

---

### Q3. What should define the required Codex agent roster used by recovery fixtures?

**Branch:** Agent roster authority

**Recommended answer:** Source roster (Recommended)
> Derive the roster from `speckit-pro/codex-agents` and the installer's required
> set, and materialize it only under fake homes.

**Alternatives offered:**
- Fixture roster: maintain a separate hand-authored list in the simulation.
- Claude roster: reuse paths under `speckit-pro/agents` as the required set.

**User's answer:** Source roster (Recommended)

---

### Q4. What evidence should satisfy the approved/unapproved service-reroute scenarios?

**Branch:** Service-reroute evidence

**Recommended answer:** Synthetic replay (Recommended)
> Use deterministic `platform_route_changes` fixtures. Keep live smoke
> operator-only and explicitly unrun, with no live claim.

**Alternatives offered:**
- Require live smoke: make a live reroute observation part of acceptance.
- Omit reroutes: defer service attribution entirely to later UAT.

**User's answer:** Synthetic replay (Recommended)

---

### Q5. How should the broader workflow and campaign bounds relate to existing route probe budgets?

**Branch:** Harness-control model

**Recommended answer:** Separate controls (Recommended)
> Keep route report candidate/probe/retry budgets intact and introduce separate
> deterministic harness-control fixtures for time, fan-out, context,
> cancellation, and escalation/de-escalation.

**Alternatives offered:**
- Extend route budgets: add every workflow bound to the route policy schema.
- Prose only: describe the extra limits without executable fixtures.

**User's answer:** Separate controls (Recommended)

---

### Q6. How should G56R-005 own the Codex fallback resolver without coupling it to the frozen Claude contract?

**Branch:** Resolver architecture

**Recommended answer:** Codex-local resolver (Recommended)
> Create a Codex-specific resolver driven by Codex schemas and fixtures,
> reusing only contract-compatible utilities.

**Alternatives offered:**
- Shared resolver core: extract a cross-platform abstraction now.
- Clone Claude resolver: copy and adapt the implementation.

**User's answer:** Codex-local resolver (Recommended)

---

### Q7. When several route checks fail, what deterministic diagnostic shape should the simulator produce?

**Branch:** Failure precedence

**Recommended answer:** Ordered reasons (Recommended)
> Emit every applicable reason in stable evaluation order, plus one terminal
> outcome such as `no_safe_route`.

**Alternatives offered:**
- First failure only: stop at the earliest failed check.
- Single priority reason: retain only the highest-priority reason.

**User's answer:** Ordered reasons (Recommended)

---

### Q8. What should happen when an explicit model-and-effort override is incompatible with every qualified route?

**Branch:** Strict override behavior

**Recommended answer:** Stop without fallback (Recommended)
> Reject before any write, preserve the previous install, and report the
> incompatibility deterministically.

**Alternatives offered:**
- Fallback automatically: treat the override as a preference.
- Install with warning: retain an unqualified requested tuple.

**User's answer:** Stop without fallback (Recommended)

---

### Q9. When may the installer omit an unavailable optional helper during recovery simulation?

**Branch:** Optional-helper degradation

**Recommended answer:** Validated no-helper path (Recommended)
> Allow omission only when the no-helper route is explicitly qualified;
> required agents remain all-or-nothing.

**Alternatives offered:**
- Any optional helper: omit silently without route validation.
- Never omit helpers: treat every optional helper as required.

**User's answer:** Validated no-helper path (Recommended)

---

### Q10. How should platform-side service reroutes affect scoring and plugin fallback decisions?

**Branch:** Reroute attribution boundary

**Recommended answer:** Separate evidence (Recommended)
> Record attributed reroutes separately; approved reroutes remain scorable,
> while unapproved reroutes fail closed and never become plugin fallback
> reasons.

**Alternatives offered:**
- Treat as fallback: fold reroutes into resolver decisions.
- Ignore reroutes: exclude reroute evidence from reports and scoring.

**User's answer:** Separate evidence (Recommended)

---

### Q11. What execution model should enforce retry, fan-out, and cancellation bounds?

**Branch:** Bounded execution

**Recommended answer:** Sequential state machine (Recommended)
> Use one bounded, non-recursive state machine; cancellation is terminal and no
> retry occurs afterward.

**Alternatives offered:**
- Bounded parallel probes: probe candidates concurrently under a cap.
- Independent retry loops: let each probe retry and reconcile later.

**User's answer:** Sequential state machine (Recommended)

---

### Q12. What may change when fallback selects a different qualified route?

**Branch:** Treatment immutability

**Recommended answer:** Model and effort only (Recommended)
> Permit only route identity changes; instructions, tools, skills, MCP,
> sandbox, mutation policy, and output contract remain byte-identical.

**Alternatives offered:**
- Whole agent profile: allow the route to replace the complete profile.
- Policy-selected fields: permit a configurable non-route subset to change.

**User's answer:** Model and effort only (Recommended)

---

### Q13. What evidence should define completion for the frozen simulation scope?

**Branch:** Acceptance standard and scope freeze

**Recommended answer:** Matrix plus state proof (Recommended)
> Require the complete scenario matrix, byte-stable reports, fail-closed
> invalid cases, unchanged fake-home state on failure, rollback proof, targeted
> tests, and the full suite. Keep production wiring, live calls, payload/release
> changes, checkpointing, and frozen-contract edits out of scope.

**Alternatives offered:**
- Scenario matrix only: defer installer-state and rollback evidence.
- Happy paths first: defer rejection and exhaustion cases.

**User's answer:** Matrix plus state proof (Recommended)

## Decisions

| Decision | Outcome | Source |
|---|---|---|
| Reason-code authority | Codex-local roadmap vocabulary; reconcile cross-platform spelling later | Q1 |
| Proof architecture | Pure resolver plus fake-home state adapter | Q2 |
| Required roster | Derive from Codex source and installer required set | Q3 |
| Service-reroute fixture | Synthetic replay; live smoke unrun | Q4 |
| Broader bounds | Separate deterministic harness controls | Q5 |
| Resolver ownership | Codex-local, no shared extraction or clone | Q6 |
| Diagnostic form | Stable ordered reasons plus terminal outcome | Q7 |
| Strict override | Fail before write; no fallback | Q8 |
| Optional helper | Omit only through a validated no-helper route | Q9 |
| Reroute semantics | Separate attributed evidence; unapproved fails closed | Q10 |
| Execution model | Bounded sequential state machine; cancellation terminal | Q11 |
| Fallback mutation | Model and effort only | Q12 |
| Acceptance | Complete matrix, stable output, state proof, targeted and full tests | Q13 |
| Sizing | One vertical slice; advisory estimate 385 LOC, status ok | Estimator |

## Open Questions

- CAR-012/G56R-012 must reconcile the Codex
  `capability_discovery_unavailable` spelling with Claude's frozen
  `capability_probe_unavailable` spelling. G56R-005 records but does not resolve
  that cross-platform difference.
- Live service-reroute smokes remain operator-only and unrun. This is a declared
  evidence boundary, not a blocker for deterministic simulation acceptance.

## Recommended Next Step

Continue the scaffold by generating the populated workflow and spec-level MOC,
then run the autonomous planning stage from the dedicated G56R-005 worktree.

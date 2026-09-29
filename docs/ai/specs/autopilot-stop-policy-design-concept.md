---
topic: "When speckit-pro autopilot may stop for a human"
slug: "autopilot-stop-policy"
date: "2026-09-28"
mode: "standalone"
source_input:
  type: "topic"
  ref: "Autopilot human-stop audit (2026-09-28) and issues #825 to #836"
question_count: 10
stop_reason: "natural"
---

# Design Concept: When speckit-pro autopilot may stop for a human

> **Source:** Autopilot human-stop audit (2026-09-28) and issues #825 to #836
> **Date:** 2026-09-28
> **Questions asked:** 10
> **Stop reason:** natural

## Goals

- Once an autopilot run starts, agents own it until the PR stack is ready for human review. Problems are resolved by spawning agents, not by asking a human (Q1).
- A run involves a human for only two reasons: the next step needs authority agents do not have, or a problem has failed every escalation tier (Q1).
- A stop condition does not halt the run. The blocked unit is parked, every independent unit keeps running, and all human items go into one end-of-run request. The run halts at once only when continuing could compound harm: tampering or forged evidence, a secret exposure, or an integrity failure (Q2).
- A problem is exhausted only after three tiers fail: (1) the current agent's repair loop within its allowance; (2) a fresh agent with a different approach, guided by a consensus diagnosis; (3) the strongest model at max effort with the full failure history (Q3).
- At the end of a run, the stack is marked ready for review with a "Decisions for you" section listing each deferred item and its evidence. It stays draft only while a required gate is red. Deferred decisions and human UAT never hold a PR in draft (Q4).
- A product-scope question the spec and roadmap do not settle is answered by consensus with the narrowest option that satisfies the spec. It is recorded as an assumption and listed under "Decisions for you". Only a choice that would add scope or change public behavior beyond the spec is deferred (Q5).
- Tool installs and network egress are granted once, in the run-start authorization, and never stop a run midway (Q6).
- Tier 3 has a per-run cap (default 3 uses), recorded in the ledger and enforced by the runner. Past the cap, a problem defers straight to the end-of-run list (Q7).
- Attended and unattended runs behave the same: autopilot never pauses to ask. A present user can interrupt or steer at any time (Q9).
- Slicing (Q10): slice 1 is the stop-policy contract (the runner stop-reason set, one shared stop-policy reference, and a parity test). Issues #825 to #836 then land as thin vertical slices that cite it.

## Non-goals

- The plan-stage boundary is kept. A `--stage plan` run stops after the plan for human review, by owner decision (audit workstream F).
- No confidence-threshold stops (Q1).
- No mid-run questions in attended sessions (Q9).
- No runner-metered dollar or token budget for escalations (Q7).
- Agents do not gain authority over merge, publish, protected pushes, secrets, destructive actions, boundary-file edits, or scope-changing PR splits (Q6).

## Module and Interface Deltas

- Runner stop-reason set: new. A closed set of stop reasons that `finalize-run` and the execution-control ledger use for every human item, split into `authority`, `exhausted`, and `harm_halt` classes (Q8).
- `speckit_pro_runner/helpers/run_finalization.py`: changed. The outcome keeps the stack ready unless a required gate is red, and it emits a "Decisions for you" list keyed by stop reason (Q4; issue #829).
- `speckit_pro_runner/execution_control.py`: changed. It adds escalation-tier records per unit and a per-run tier-3 cap (Q3, Q7; issue #829). It adds runner-proved agent approvals that replace operator events where the runner can prove the preconditions (issue #830), and it scopes unknown-outcome blocking to a single unit (issue #831).
- Shared stop-policy reference: new. One reference loaded by the Claude and Codex autopilot skills, stating this contract. Every other guidance file cites it instead of restating stop rules (Q8).
- Consensus protocol and synthesizer: changed. Round 3 is the tier-3 tiebreak, and scope assumptions are recorded (Q5; issue #827).
- Codex run-start authorization: changed. Tool installs and egress classes fold into the single up-front grant (Q6; issue #833).
- Gate, sweep, and helper guidance: changed. They defer and escalate instead of stopping (issues #828, #832, #835, #836).
- Grey box for the implementer: how Tier 2's "different approach" is chosen, and how the consensus diagnosis is packaged.

## Terms

| Term | Meaning in this spec | Differs from codebase usage? | Source |
| ---- | -------------------- | ---------------------------- | ------ |
| Stop | The run involves a human. It happens only for authority, exhaustion, or a harm halt. | Yes. Today the word also covers any gate failure and every "STOP" line in guidance. | Q1, Q2 |
| Defer | Park one unit and keep running independent units. The item goes to the end-of-run request. | No. It matches the ledger's `defer` disposition. | Q2; `execution_control.py` |
| Harm halt | An immediate halt of the whole run, reserved for tampering, a secret exposure, or an integrity failure. | Yes. This is a new distinct class. | Q2 |
| Escalation tier | One of the three remedy levels a problem must pass through before it counts as exhausted. | Yes. It is new; today there are only fixed allowances. | Q3 |
| Decisions for you | The PR-body section listing deferred items, scope assumptions, and UAT. | Yes. It replaces the end-of-run chat request as the primary record. | Q4, Q5 |
| Authority | A power agents do not hold: merge, publish, protected push, secrets, destructive or irreversible actions, human UAT, scope-changing PR splits, boundary-file edits, veto bypass, or reopening a closed PR. | Partly. Tool installs and egress move to run-start authorization. | Q6 |

## Verification Gates

- Stop-reason parity test: fails if any Claude or Codex guidance file names a stop reason outside the runner set, or restates a stop rule without citing the shared reference (Q8).
- Runner unit tests:
  - Each stop class.
  - The tier-3 cap enforced from ledger records.
  - Forged tier or approval records failing closed.
  - A ready-versus-draft outcome for a red required gate, a deferred decision, and UAT only (Q3, Q4, Q7).
- Existing gates: `python3 tests/speckit-pro/run-all.py`, the CI default suite, `scripts/refresh-release-artifacts.py --check`, ruff and mypy, and `reference:check` (evidence: AGENTS.md Commands table).
- Formal methods: none. The policy is a small closed state space that unit tests over ledger records can cover. A model adds cost without new assurance (evidence: `formal-check-decision.md` guidance for selective use).

## Design Tree (Q&A log)

### Q1. What principle should define a legitimate human stop once autopilot is running?

**Branch:** behavior and rules

**Recommended answer:** Authority, not difficulty

> Human-in-the-loop guidance tiers actions by reversibility. Reversible work runs autonomously with logging, while irreversible or external actions need approval. The audit found most stops are difficulty stops.

**Alternatives offered:**

- Authority plus exhausted remedies: more predictable cost.
- Confidence threshold: self-reported confidence is poorly calibrated.

**User's answer:** Authority plus exhausted remedies

### Q2. When a legitimate stop condition arises mid-run, when should the human be involved?

**Branch:** behavior and rules

**Recommended answer:** Defer; halt only on harm

> This matches the runner's defer disposition and the async-first pattern.

**Alternatives offered:**

- Always defer to the end, even for tampering.
- Stop at the moment (today's behavior).

**User's answer:** Defer; halt only on harm

### Q3. How many escalation tiers must fail before a problem counts as exhausted?

**Branch:** errors

**Recommended answer:** Three tiers

> This follows the common "escalate after 3 failed attempts" threshold. Each tier adds capability.

**Alternatives offered:**

- Two tiers.
- Budget-bound, not counted.

**User's answer:** Three tiers

### Q4. When a run ends with deferred items, what state should the PR stack be left in?

**Branch:** user outcome

**Recommended answer:** Ready unless a gate is red

> Marking a PR ready next to red checks misleads reviewers. Deferred decisions and UAT alone should not hold it in draft.

**Alternatives offered:**

- Always ready, with failures flagged.
- Draft on any deferral (close to today).

**User's answer:** Ready unless a gate is red

### Q5. When a run hits a product-scope question the spec and roadmap do not settle, what should happen?

**Branch:** scope

**Recommended answer:** Assume conservatively and flag

> Nothing merges without review, so the choice stays reversible at review time.

**Alternatives offered:**

- Defer the affected unit.
- Always assume, never defer.

**User's answer:** Assume conservatively and flag

### Q6. How should the audit's authority list be settled?

**Branch:** security

**Recommended answer:** Keep the list, and fold installs up front

> Installs and egress are the most frequent Codex stop causes, and they can be granted before work begins.

**Alternatives offered:**

- Keep the list as-is.
- Narrow it to the core.

**User's answer:** Keep the list, and fold installs up front

### Q7. What should bound the cost of the three escalation tiers across a whole run?

**Branch:** performance

**Recommended answer:** Per-run tier caps

> This is countable and testable, and it needs no cost metering the runner cannot observe.

**Alternatives offered:**

- A per-run cost budget.
- No run-level cap.

**User's answer:** Per-run tier caps

### Q8. Where should this stop policy live so both hosts and the runner cite one source?

**Branch:** interface

**Recommended answer:** A runner enum plus one doc

> The repo's "one source per contract" rule applies (evidence: AGENTS.md, Editing Boundaries).

**Alternatives offered:**

- A shared doc only.
- A constitution principle.

**User's answer:** A runner enum plus one doc

### Q9. When a user is actively watching an autopilot session, should the policy change?

**Branch:** behavior and rules

**Recommended answer:** The same policy either way

> One behavior is easier to test. The audit found attended-only prompts.

**Alternatives offered:** Ask immediately if attended.

**User's answer:** The same policy either way

### Q10. How should the policy be sliced?

**Branch:** slice sizing

**Recommended answer:** Contract first, then the issues

> `estimate-spec-size` returned `warn` for about 5 stories, 30 files, and 15 requirements.

**Alternatives offered:**

- One spec through autopilot.
- Issues only, with no contract slice.

**User's answer:** Contract first, then the issues

## Open Questions

- **What:** The exact tier-3 cap value.
  **Why deferred:** Q7 settled the mechanism. The value 3 is a starting default to tune from run data.
  **Suggested next step:** Set it to 3 in slice 1 and revisit after several full runs.

## Recommended Next Step

Implement slice 1 (the stop-policy contract) as its own PR. Then merge it (never rebase) into each workstream branch (#827 to #836) so they cite the shared reference and the runner stop-reason set.

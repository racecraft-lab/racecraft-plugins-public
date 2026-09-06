# Grill Me interview protocol

This is the platform-neutral interview loop. The active SKILL.md owns runtime
eligibility and the Claude or Codex question tool. Check that boundary before
following this protocol.

## Prepare

1. Read a supplied file, use a supplied topic, or ask what to scope when input
   is empty.
2. Inspect applicable project instructions, `.specify/memory/constitution.md`,
   roadmaps, earlier design decisions, and targeted code. Do not re-ask facts
   the input or evidence already establishes.
3. Build a branch queue from the input and relevant domains. Common branches are
   user outcome, scope and non-goals, behavior and rules, data, interface,
   errors, dependencies, security, performance, observability, migration,
   rollout, success measures, and slice sizing.
   Three branches are always resolved before synthesis, from evidence or by
   one question each, and each fills a named Design Concept section:
   - **Module and interface deltas:** which modules change, which interfaces
     change, and what stays a grey box the implementer owns.
   - **Terms:** the domain terms the spec relies on whose meaning in the
     codebase, roadmap, or constitution differs from the user's usage.
   - **Verification gates:** the deterministic checks and thresholds that
     prove the slice done, such as typecheck, tests, a complexity ceiling, a
     mutation floor, or dependency rules, as the target for downstream
     project-command discovery.
   When one of these is resolved from evidence instead of a question, the
   section cites that evidence (file, roadmap entry, or constitution
   principle) so a resolved branch is never indistinguishable from a skipped
   one.
4. Order branches by impact times uncertainty.

## Ask one decision at a time

For the next branch, ask exactly one neutral, actionable question. One question
must resolve one decision axis; split coupled decisions across turns.

Offer 2-3 mutually exclusive choices:

1. Put the grounded default first and suffix its label `(Recommended)`. Explain
   its evidence and tradeoff in one or two sentences.
2. Offer one or two defensible alternatives with their distinct tradeoffs.
3. Keep any question header at 12 characters or fewer when the platform uses a
   header. Do not add `Other` when the platform picker supplies it.

After the user answers:

- Record the question, branch, recommendation and grounding, alternatives, the
  user's answer, and any notes.
- Update the model and branch queue. Add a branch revealed by the answer; remove
  one made irrelevant.
- If an answer conflicts with an earlier decision, ask a later one-axis question
  that makes the conflict explicit.
- If the user defers to the recommendation ("you decide", "I don't know"), ask
  exactly one follow-up on the same branch: what constraint or fact would
  change the recommendation. Then adopt the recommendation and record the
  branch as an Open Question marked **deferred-with-default**, with the adopted
  default and the user's stated constraint. Never invent an answer.

## Stop

Prefer natural convergence: stop when no consequential branch remains. Also stop
when the user chooses to end. Starting at 30 questions, and again at reasonable
intervals if the user continues, offer a wrap-up checkpoint. Force synthesis at
100 questions and list unasked branches as Open Questions.

At a checkpoint, recommendation-first still applies. Recommend continuing when
any consequential branch is still queued, including an unresolved always-resolved
branch or slice sizing, and name that branch in the option's tradeoff text.
Recommend wrapping up only when nothing consequential remains. Offer the other
choice second, and optionally let the user name the next branch. Once the user
ends, do not resume questioning during synthesis.

## Quality filter

- Ask what most reduces uncertainty about observable behavior; skip cosmetic
  naming and wording.
- Keep the question neutral. Put the recommendation in the choice, not the
  question.
- Prefer project governance and verified code patterns. Use current authoritative
  sources only when local evidence is silent.
- State low confidence and its dependency instead of presenting an unsupported
  norm as fact.
- Capture useful free text without letting it replace the next highest-value
  branch.

After the loop, return to the active SKILL.md and load its output contract.

# Grill Me — Interview Protocol (Codex variant)

The detailed operational doc for running a Grill Me session on Codex.
Read this before activating the skill. The high-level mission is in
`../SKILL.md`; this file is the playbook.

This protocol mirrors the Claude Code variant
(`../../../skills/grill-me/references/interview-protocol.md`) but
substitutes Codex's interactive primitives for `AskUserQuestion`.

## Activation Sequence

1. **Run the HITL probe** (from `../SKILL.md`'s "Self-check at
   activation"). Choose the question-asking mechanism:
   - **`request_user_input`** if available (Plan mode +
     `collaboration_modes = true`).
   - **Free-text Q&A in chat** if the TTY check passes.
   - **Abort** if neither confirms an interactive runtime.

2. **Read the input.** Three cases:
   - File path argument → read it (`exec_command "cat <path>"` if
     `read_file` isn't available, or use the chosen file-reading tool).
   - Topic string argument → use the string as the seed.
   - Empty argument → ask the user (using your chosen interactive
     mechanism) for a brief, transcript path, or one-line topic.

3. **Build initial mental model.** Skim the codebase for relevant
   patterns:
   - `CLAUDE.md` — project conventions.
   - `.specify/memory/constitution.md` — if it exists, the constitution
     constrains many design choices.
   - `docs/ai/specs/**/*.md` — prior specs and design concepts.
   - `docs/ai/*roadmap*.md` — technical roadmap for context.
   - Targeted greps for any domain terms in the input.

4. **Identify design-tree branches.** Build a working list of branches
   to walk, drawn from:
   - The checklist domain catalog at
     `../../../skills/speckit-coach/references/checklist-domains-guide.md`
     (reuse those names where they apply).
   - Input-specific branches the catalog doesn't cover.
   - Common branches: data model, UX/UI, behavior/business rules,
     error paths, scope cuts, dependencies, performance, security,
     observability, rollout/migration, success metrics.

   Prioritize branches by uncertainty × impact: walk the
   highest-stakes, most-uncertain branches first.

## Interview Loop

For each branch (in priority order), generate one question. **Never ask
two questions in the same prompt to the user.** The "one question
at a time" discipline is core to the skill.

### Per-question template

```text
Question:    Single, specific, actionable question. End with a question mark.
             Phrase it so the AI's recommendation has a clear "yes / no / X"
             answer surface, not "what do you think about Y?".

Recommended answer:
             Your reasoning in 1–2 sentences. Mention the relevant
             constitution principle, codebase pattern, or industry
             norm that grounds the recommendation. Mark this option
             as "(Recommended)".

Alternative 1:
             A different defensible approach. Trade-off vs the
             recommendation.

Alternative 2 (sometimes):
             A third realistic path, or "End interview — I have what
             I need" after the soft cap.
```

When using `request_user_input`, provide the question + 2–3 options
matching the template. When falling back to free-text Q&A, write the
question and options in plain prose, e.g.:

```text
Q12. Should gamification points apply retroactively to existing user accounts?

  A) (Recommended) Yes, apply retroactively — keeps existing users
     engaged and avoids them feeling penalized for past activity.
  B) No, only future actions count — cleaner cutoff, simpler backfill.
  C) Yes with a 0.5x multiplier — compromise between A and B.

Pick one (A/B/C) or write your own answer.
```

### After each answer

1. **Record the answer**, including any free-text override.
2. **Update your mental model.** New branches often appear as a side
   effect of an answer. Add/remove from the queue.
3. **Decide whether to continue.** Check stop conditions (below).

## Stop Conditions

The interview ends when **any** of the following is true. Always prefer
the natural stop (no critical opens remain) over the cap-driven stops.

### Natural stop — preferred

You have walked every branch on your queue and the user's answers do
not reveal new critical branches. The conversation has converged on a
shared design concept.

### Soft cap — checkpoint at 30 questions

When question count reaches 30 (and again at 50, 70, 90 if still
running), pause for an explicit checkpoint:

```text
We've walked 30 branches so far. Wrap up or keep going?

  A) (Recommended) Wrap up — synthesize the design concept now.
  B) Keep going — there are still important branches.
  C) Skip ahead to a specific topic.
```

### User-initiated stop — any time

After the soft cap, every question should include an explicit "End
interview — I have what I need" option. If the user picks it, jump
straight to synthesis.

### Hard cap — 100 questions

If you somehow reach 100 questions without a natural or user-initiated
stop, force-stop and synthesize. Note in the Design Concept doc's "Open
Questions" section that the hard cap was hit, with the unanswered
branch list.

## Question Generation — Heuristics

- **Ask the question that, if answered, eliminates the most uncertainty
  about how the system should behave.** Don't ask cosmetic questions
  early.
- **One axis at a time.** If a decision has two coupled axes (e.g.,
  "auth method" and "session storage"), ask them as separate questions.
- **Concrete, not abstract.** "Should gamification points apply
  retroactively to existing user accounts?" not "How should we handle
  legacy users?".
- **Avoid leading questions.** Your recommendation goes in the
  *option*, not the *question*. The question itself should be neutral.
- **Don't ask what the user clearly already knows.** If the input
  brief states "we're using Postgres", don't ask "which database?".

## Recommended Answer — How to Choose

Your recommendation is the option you'd default to if the user said
"just pick something". Ground it in:

1. **The constitution** (`.specify/memory/constitution.md`) — if a
   principle there points to an answer, follow it.
2. **The codebase** — patterns already in use are usually the right
   answer for consistency. Use targeted greps + reads to verify.
3. **Industry norms** — when the codebase is silent, default to what
   most teams would do.
4. **The path of least surprise** for downstream phases — Specify,
   Plan, Tasks, Implement should all be easier with this choice.

If you have less than 60% confidence in a recommendation, say so in
the option's description (*"Recommended with low confidence — depends
on X"*) and lean harder on the alternatives.

## Recovery from Edge Cases

- **User picks an alternative or writes free-text that contradicts
  your branches.** Treat it as new information. Re-prioritize the
  queue. Don't push back unless the answer creates a hard inconsistency
  with a prior answer — then ask a follow-up question that surfaces
  the conflict.

- **User answers "I don't know" or "you decide".** Use the recommended
  option as the answer, mark it in the Design Concept's Open Questions
  ("user deferred — used recommendation"), and move on. Don't pause.

- **User starts going off-topic in free-text answers.** Capture the
  note verbatim, then return to the branch queue. Don't try to
  redirect — the user's tangent often contains useful context for a
  later branch.

- **The input brief is too thin to identify branches.** Ask 2–3
  scoping questions first ("What's the user-visible outcome?", "What
  are we deliberately NOT building?", "What's the success metric?")
  before walking the design tree proper.

- **You realize a prior answer was wrong-context.** Surface it: ask
  the user explicitly "earlier you said X for branch Y; given what
  we just learned, do you want to revise?".

## Synthesis

After the loop ends, write the Design Concept doc per
`./output-formats.md`. Then:

- **Standalone mode**: report the file path back to the user with a
  one-line summary and a "next step" suggestion (`$speckit-coach` to
  feed it into a roadmap, or `$speckit-setup SPEC-XXX` if a roadmap
  entry exists).
- **Setup mode**: report the file path back to the calling
  `$speckit-setup` skill and surface the key answers (especially
  Goals, Non-goals, and the major design decisions) so setup can
  enrich the Specify Prompt and Clarify Prompts in the workflow file.

The synthesis itself is a single pass — don't loop back into more
interviewing. If the user wants to revise, they can re-run grill-me
on the design concept doc as a new input.

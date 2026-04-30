# Grill Me — Interview Protocol

The detailed operational doc for running a Grill Me session. Read this
before activating the skill. The high-level mission is in `../SKILL.md`;
this file is the playbook.

## Activation Sequence

1. **Confirm human-in-the-loop preconditions** (from `../SKILL.md`'s
   hard constraints block). Abort if any fail.

2. **Read the input.** Three cases:
   - File path argument → `Read` it.
   - Topic string argument → use the string as the seed.
   - Empty argument → call `AskUserQuestion` once with:
     - `question`: "What are we scoping today? Paste a brief, point at
       a file, or give me a one-line topic."
     - `header`: "Input"
     - `options`: 2–4 options tailored to common starting points
       (e.g., "I'll paste a brief", "I have a transcript file", "Just
       a topic — let's start blank"); "Other" is automatic for
       free-text.

3. **Build initial mental model.** Skim the codebase for relevant
   patterns:
   - `Read("CLAUDE.md")` — project conventions.
   - `Read(".specify/memory/constitution.md")` — if it exists, the
     constitution constrains many design choices.
   - `Glob("docs/ai/specs/**/*.md")` — prior specs and design concepts
     for related work.
   - `Glob("docs/ai/*roadmap*.md")` — technical roadmap for context.
   - Targeted `Grep` for any domain terms in the input.

4. **Identify design-tree branches.** Build a working list of branches
   to walk, drawn from:
   - The checklist domain catalog at
     `../../speckit-coach/references/checklist-domains-guide.md`
     (reuse those names where they apply).
   - Input-specific branches the catalog doesn't cover.
   - Common branches: data model, UX/UI, behavior/business rules,
     error paths, scope cuts, dependencies, performance, security,
     observability, rollout/migration, success metrics.

   Prioritize branches by uncertainty × impact: walk the highest-stakes,
   most-uncertain branches first.

## Interview Loop

For each branch (in priority order), generate one question. **Never ask
two questions in the same `AskUserQuestion` call.** The "one question
at a time" discipline is core to the skill.

### Per-question template

```text
question:    Single, specific, actionable question. End with a question mark.
             Phrase it so the AI's recommendation has a clear "yes / no / X"
             answer surface, not "what do you think about Y?".

header:      ≤ 12 chars. A short chip label (e.g., "Retroactive", "Auth model",
             "Soft delete", "Cache TTL").

multiSelect: false (always — these are mutually-exclusive design choices).

options:     2–3 entries. AskUserQuestion appends "Other" automatically.

  Option 1 (your recommendation):
    label:        "<chosen approach> (Recommended)"
    description:  Your reasoning in 1–2 sentences. Mention the relevant
                  constitution principle, codebase pattern, or industry
                  norm that grounds the recommendation.

  Option 2 (next-most-plausible alternative):
    label:        "<alternative approach>"
    description:  Trade-off vs the recommendation. Why someone might
                  legitimately pick this instead.

  Option 3 (sometimes — when there's a third realistic path):
    label:        "<another alternative>" or
                  "End interview — I have what I need" (after the
                  soft cap, optionally include this)
    description:  Trade-off, or the explicit "wrap up" semantics.
```

### After each answer

1. **Record the answer**, including any "Other" free-text. The
   `Q&A log` of the Design Concept doc captures every entry.
2. **Update your mental model.** The answer often reveals new branches
   or invalidates branches you'd planned. Add/remove from the queue.
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
running), pause for an explicit `AskUserQuestion` checkpoint:

```text
question:    "We've walked 30 branches so far. Wrap up or keep going?"
header:      "Continue?"
options:
  - "Wrap up — synthesize the design concept now (Recommended)"
  - "Keep going — there are still important branches"
  - "Skip ahead to specific topic" (let user free-text the topic)
```

### User-initiated stop — any time

After the soft cap, every `AskUserQuestion` call should include an
explicit "End interview — I have what I need" option as the last
non-Other option. If the user picks it, jump straight to synthesis.

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
   answer for consistency. Use `Glob` + `Grep` to verify.
3. **Industry norms** — when the codebase is silent, default to what
   most teams would do (e.g., "soft-delete with `deleted_at` timestamp"
   is more common than hard-delete).
4. **The path of least surprise** for downstream phases — Specify,
   Plan, Tasks, Implement should all be easier with this choice.

If you have less than 60% confidence in a recommendation, say so in
the option's description (*"Recommended with low confidence — depends
on X"*) and lean harder on the alternatives.

## Recovery from Edge Cases

- **User picks "Other" with free-text that contradicts your branches.**
  Treat it as new information. Re-prioritize the queue. Don't push
  back unless the answer creates a hard inconsistency with a prior
  answer — then ask a follow-up question that surfaces the conflict.

- **User answers "I don't know" or "you decide".** Use the recommended
  option as the answer, mark it in the Design Concept's Open Questions
  ("user deferred — used recommendation"), and move on. Don't pause.

- **User starts going off-topic or rambling in "Other" notes.** Capture
  the note verbatim, then return to the branch queue. Don't try to
  redirect — the user's tangent often contains useful context for a
  later branch.

- **The input brief is too thin to identify branches.** Ask 2–3
  scoping questions first ("What's the user-visible outcome?", "What
  are we deliberately NOT building?", "What's the success metric?")
  before walking the design tree proper.

- **You realize a prior answer was wrong-context.** Surface it: ask
  the user explicitly "earlier you said X for branch Y; given what
  we just learned, do you want to revise?" via `AskUserQuestion`.

## Synthesis

After the loop ends, write the Design Concept doc per
`./output-formats.md`. Then:

- **Standalone mode**: report the file path back to the user with a
  one-line summary and a "next step" suggestion (`/speckit-pro:coach`
  to feed it into a roadmap, or `/speckit-pro:setup SPEC-XXX` if
  a roadmap entry exists).
- **Setup mode**: report the file path back to the calling /setup
  command and surface the key answers (especially Goals, Non-goals,
  and the major design decisions) so /setup can enrich the Specify
  Prompt and Clarify Prompts in the workflow file.

The synthesis itself is a single pass — don't loop back into more
interviewing. If the user wants to revise, they can re-run grill-me
on the design concept doc as a new input.

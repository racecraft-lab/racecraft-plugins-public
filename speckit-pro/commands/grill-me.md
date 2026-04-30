---
description: "Run an iterative project-scoping interview before any spec or design work. The AI walks down each branch of the design tree, asks one question at a time, and provides its own recommended answer for every question. Output is a Design Concept doc that captures shared understanding. Strictly human-in-the-loop — never invoked from autopilot."
allowed-tools: "*"
argument-hint: "<input-file or topic name (optional)>"
---

# Grill Me

Iterative project scoping through relentless one-question-at-a-time interview.

The AI walks every branch of the design tree, asks a single question per
turn, and **provides its own recommended answer** so you can agree or
course-correct. Output: a rich, shared-understanding Design Concept doc
you can feed into `/speckit-pro:coach`, `/speckit-pro:setup`, or any other
spec workflow.

## Invocation

```text
# With a raw idea / brief / transcript file
/speckit-pro:grill-me docs/raw-idea.md
/speckit-pro:grill-me notes/stakeholder-meeting-transcript.txt

# With a free-text topic (no file)
/speckit-pro:grill-me "gamification overhaul for the user dashboard"

# No argument — the skill will ask you for context first
/speckit-pro:grill-me
```

## What to Do

Invoke the `grill-me` skill. It owns the interview loop, the design-tree
walk, the recommended-answer generation, the stop conditions, and the
Design Concept doc output.

```text
Skill("grill-me", args: <user-supplied argument>)
```

The skill will:

1. Read the input (file, topic string, or ask the user for context).
2. Identify the design-tree branches (data, UX, behavior, error paths,
   scope cuts, dependencies, performance, security, observability, rollout,
   success metrics — adjusted to the input).
3. Ask one question at a time via `AskUserQuestion`, with the AI's
   recommendation marked `(Recommended)` and 1–2 plausible alternatives.
4. Keep going until no critical open questions remain (soft-cap at 30,
   hard-cap at 100; you can also select "End interview" any time).
5. Synthesize a Design Concept doc and write it to:
   - `docs/ai/specs/<slug>-design-concept.md` (default), or
   - the path you supplied as a second argument.

## When NOT to Use

<hard_constraints>

**Grill Me is human-in-the-loop only.** It must NEVER be invoked from
inside `/speckit-pro:autopilot` or any of its phase agents. Autopilot's
Clarify phase uses `/speckit.clarify` with the consensus protocol — that's
the only clarification mechanism inside autopilot. Grill Me runs *before*
the autopilot loop, not during it.

</hard_constraints>

If you're already inside an autopilot run and hitting ambiguity, fall
back to consensus or fail the gate — do not call this command.

---
name: grill-me
description: "Iterative project-scoping interview that turns the AI into a relentless one-question-at-a-time interviewer. The AI walks down each branch of the design tree, asks single questions with its own recommended answers as starting points, and produces a Design Concept doc capturing the shared understanding. Use when the user says 'interview me', 'grill me', 'scope this idea', 'walk me through this design before I commit to anything', or wants to align on a raw idea / transcript / brief before producing a spec. Strictly human-in-the-loop. NEVER invoke this skill from inside autopilot or any of its phase agents."
argument-hint: "e.g. 'interview me about this brief', 'grill me on the gamification overhaul', 'scope this transcript'"
user-invokable: true
license: MIT
---

# Grill Me — Iterative Project Scoping Interview

You are a **relentless interviewer**. Your single job is to walk down every
branch of the design tree behind the user's idea, ask one question at a
time, and **provide your own recommended answer for each question** so the
user can agree, course-correct, or pick an alternative.

The output of a successful grilling session is a **Design Concept doc**:
a rich Markdown record of the Q&A history plus a synthesized summary
that downstream tools (`/speckit-pro:coach`, `/speckit-pro:setup`,
`/speckit.specify`) consume to produce specs and plans.

This skill is the antidote to "specs to code" / vibe-coding handoffs.
The user stays in the loop on every consequential design decision.

## The Canonical Grill Me Prompt

This skill operationalizes the original Grill Me prompt verbatim — keep
it visible so users can re-tune it without leaving the repo:

> *"Interview me relentlessly about every aspect of this plan until we
> reach a shared understanding. Walk down each branch of the design tree
> resolving dependencies one by one. For each question provide your
> recommended answer. Ask the questions one at a time."*

Source: The Grill Me Skill / The Grill Me Protocol (see
`~/Downloads/The Grill Me Skill_*.md` and `~/Downloads/The Grill Me Protocol_*.md`).

<hard_constraints>

## Human-in-the-Loop ONLY — Hard Constraints

**Grill Me MUST NEVER be invoked autonomously.** The interview loop
requires a human user who can answer questions in real time. Running
this skill in any non-interactive context defeats its purpose and
silently produces low-value output.

### Allowed entry points (exhaustive)

1. The user typing `/speckit-pro:grill-me` directly in an interactive
   Claude Code session.
2. The `/speckit-pro:setup` command running interactively (it always
   invokes grill-me before writing the workflow file).

**No other entry point is permitted.**

### Forbidden invokers (deny-list)

- The `speckit-autopilot` skill
- Any of its phase agents: `phase-executor`, `clarify-executor`,
  `checklist-executor`, `analyze-executor`, `implement-executor`
- The consensus analysts: `codebase-analyst`, `spec-context-analyst`,
  `domain-researcher`
- `consensus-synthesizer`, `gate-validator`
- Any other autopilot-triggered agent
- Any background agent, automation, CI job, or non-interactive runtime

If the autopilot's Clarify phase needs disambiguation, it uses
`/speckit.clarify` with the multi-agent consensus protocol — NOT
grill-me. These are different systems by design.

### Self-check at activation

**Before asking your first question**, verify the runtime supports
real-time human interaction:

1. Confirm `AskUserQuestion` is available in your tool list. (It is
   the only sanctioned interview mechanism in the Claude Code variant.)
2. Confirm you were invoked via the slash command or by `/setup`,
   not by a phase-executor or other agent context.

If either check fails, **abort immediately** with this message:

> "grill-me is human-in-the-loop only. The autopilot's Clarify phase
> uses /speckit.clarify, not grill-me. Aborting."

Do not write any file. Do not call `AskUserQuestion`. Just abort.

</hard_constraints>

## Mode Switch — Standalone vs Setup

This skill detects two operating modes from its arguments / invocation
context:

### Standalone mode

- Triggered when the user runs `/speckit-pro:grill-me` directly.
- Input: a file path, a topic string, or empty (skill prompts user).
- Output path: `docs/ai/specs/<slug>-design-concept.md`, where `<slug>`
  is derived from the input (file basename without extension, or
  kebab-cased topic). User can override by passing a second argument
  with an explicit path.

### Setup mode

- Triggered when invoked from `/speckit-pro:setup` (the calling command
  passes a marker / context indicating it's the setup flow).
- Input: the spec scope description from the technical roadmap.
- Output path: `.worktrees/<NNN>-<short-name>/docs/ai/specs/SPEC-<ID>-design-concept.md`
  (the worktree path the setup command provides).
- Additional behavior: surface the Q&A answers back to the calling
  setup command so it can enrich the workflow file's Specify Prompt
  and Clarify Prompts.

## How to Run an Interview

Detailed protocol lives in `references/interview-protocol.md` — read
that file before activating. The high-level loop:

1. **Read input** → file contents, topic string, or ask user for
   context if neither was given.
2. **Identify design-tree branches** for this input. Use the
   checklist domain catalog (`skills/speckit-coach/references/checklist-domains-guide.md`)
   as a starting taxonomy, plus the input-specific branches.
3. **Loop**:
   a. Generate the single most-uncertain critical question for the
      next branch.
   b. Determine your recommended answer (consult the codebase, the
      constitution at `.specify/memory/constitution.md` if present,
      and industry best practices).
   c. Call `AskUserQuestion` with the question, your recommendation
      marked `(Recommended)` as the first option, and 1–2 plausible
      alternatives. Header ≤ 12 chars.
   d. Record the user's selected answer (including any "Other"
      free-text). Update your mental model.
   e. Continue until stop condition triggers.
4. **Stop** when no critical open questions remain (preferred), the
   user selects an "End interview" option, or the soft cap (30
   questions) prompts a checkpoint that the user uses to wrap up.
5. **Write the Design Concept doc** following the schema in
   `references/output-formats.md`.

## Output Contract

The Design Concept doc is a Markdown file with frontmatter and these
sections (full schema in `references/output-formats.md`):

- **Frontmatter**: topic, date, source-input, question-count, mode (standalone|setup).
- **Goals** — what we're trying to achieve, in the user's own words
  where possible.
- **Non-goals** — explicit scope cuts the user agreed to.
- **Design Tree (Q&A log)** — every question, your recommended
  answer + reasoning, the user's chosen answer, any free-text notes.
- **Open Questions** — anything you flagged as worth follow-up but
  the user deferred.
- **Recommended Next Step** — usually `/speckit-pro:coach` for roadmap
  authoring or `/speckit-pro:setup SPEC-XXX` if a roadmap entry already
  exists.

## What This Skill Does NOT Do

- It does not write a workflow file. That's `/speckit-pro:setup`'s job.
- It does not write a spec file (`spec.md`). That's `/speckit.specify`'s
  job.
- It does not modify the technical roadmap. That's `/speckit-pro:coach`'s
  job.
- It does not run autonomously. See the Hard Constraints block above.

## References

- **`references/interview-protocol.md`** — the detailed interview loop,
  question generation, stop conditions, and recovery from edge cases.
- **`references/output-formats.md`** — the Design Concept doc schema and
  formatting rules.

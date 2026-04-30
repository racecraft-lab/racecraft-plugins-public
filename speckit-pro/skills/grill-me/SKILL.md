---
name: grill-me
description: "Runs a structured one-question-at-a-time scoping interview that proposes the assistant's own recommended answer first for every question and walks each branch of the design tree, then writes a Design Concept Markdown doc (frontmatter, Goals, Non-goals, Q&A log, Open Questions, Recommended Next Step). Use this skill when the user says 'grill me', 'interview me', 'scope this idea', 'iterative scoping', 'walk every branch of the design tree', 'one question at a time, you suggest the answer', or asks for a relentless interviewer with recommended answers. Specifically for pre-scoping a raw client brief, meeting transcript, or vague feature idea before any spec is written, and for the human-in-the-loop step inside /speckit-pro:setup. Narrower and more structured than free-form brainstorming or ideation: this skill always produces a Design Concept file on disk, always presents the assistant's recommendation as the first option for every question so the user can agree, course-correct, or pick an alternative, and always walks the design tree by uncertainty × impact rather than free association. Accepts .md, .txt files or a free-text topic."
argument-hint: "e.g. 'interview me about this brief', 'grill me on the gamification overhaul', 'scope this transcript'"
user-invokable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/grill-me/ uses a free-text Q&A loop instead."
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

## Examples

### Example 1: Standalone scoping from a raw idea

User says: *"Grill me on this idea: add a leaderboard to our learning platform that ranks users by points earned from completed lessons."*

Actions:
1. Build initial mental model (read CLAUDE.md, .specify/memory/constitution.md if present)
2. Identify branches: data model, scoring rules, retroactivity, UX surface, performance, privacy, rollout
3. Loop on `AskUserQuestion`, one question per branch, recommendation always first
4. Stop at natural endpoint (no critical opens remain) or user wraps up
5. Write `docs/ai/specs/leaderboard-design-concept.md`

Result: Design Concept Markdown file with frontmatter, Goals, Non-goals, Q&A log, Open Questions, Recommended Next Step.

### Example 2: Setup-mode invocation from /speckit-pro:setup

`/speckit-pro:setup` invokes this skill with `mode: "setup"`, the spec scope from the technical roadmap, and an output path inside the worktree.

Actions:
1. Detect setup mode from invocation context
2. Use the supplied scope as the input (don't ask the user for context again)
3. Run the interview loop as in Example 1
4. Write the Design Concept to the worktree path the caller supplied
5. Return Goals, Non-goals, and major decisions to the caller so it can enrich the workflow file's Specify and Clarify Prompts

Result: Design Concept doc lives in the worktree alongside the workflow file; both get committed in one commit.

### Example 3: Refusing an autonomous invocation

A subagent inside `/speckit-pro:autopilot` (e.g., the clarify-executor) tries to call `Skill('grill-me')` to resolve ambiguity.

Actions:
1. Self-check at activation detects agent context (or AskUserQuestion unavailable)
2. Abort immediately — do NOT call AskUserQuestion, do NOT write any file
3. Emit: *"grill-me is human-in-the-loop only. The autopilot's Clarify phase uses /speckit.clarify, not grill-me. Aborting."*

Result: Nothing written. Caller surfaces the ambiguity to the orchestrator, which fails the gate.

## Troubleshooting

### Error: "AskUserQuestion is not available in this context"

Cause: The skill is being invoked from a runtime that doesn't expose
`AskUserQuestion` (subagent context, automation, or non-Claude-Code surface).

Solution: Abort. Grill-me requires real-time human interaction. If you
need scoping in a non-interactive context, use `/speckit-pro:coach` for
methodology guidance or fail the gate and surface to the user.

### Natural-language prompts route to `superpowers:brainstorming` instead of grill-me

Cause: If you have the `superpowers` plugin installed, its `brainstorming` skill description starts with "You MUST use this before any creative work — creating features, building components, adding functionality, or modifying behavior." That high-imperative framing reliably outranks descriptive scoping skills on any prompt that smells like creative work, including "interview me about this brief", "scope this idea", or "walk me through this design before I commit."

Solution: Invoke grill-me directly via the slash command `/speckit-pro:grill-me` (description-based triggering is bypassed for explicit invocation). Inside `/speckit-pro:setup` this is already wired — the setup command calls `Skill('grill-me')` explicitly, so the brainstorming competition does not apply. If you prefer natural-language invocation, "run grill-me on this" or "use the grill me skill on this brief" name-anchors more reliably than "interview me about this".

### Skill triggers when user wanted /speckit-pro:setup

Cause: The user said "set up SPEC-009" — that's `/setup`'s territory,
not grill-me's. Setup itself runs grill-me, so the user gets the
interview either way, but starting from setup ensures the worktree
gets created.

Solution: If the user mentions a SPEC-ID and "set up" / "prepare",
defer to `/speckit-pro:setup`. Grill-me triggers on "interview me",
"grill me", "scope this", or when the input is a raw idea / transcript
/ brief without a SPEC-ID.

### Interview hits the soft cap (30 questions) on every run

Cause: Either the input is genuinely complex (large feature, lots of
unknowns) or the question generation is asking cosmetic / low-value
questions instead of the highest-uncertainty branches first.

Solution: At the soft-cap checkpoint, the user can wrap up immediately.
If this happens repeatedly on simple inputs, revisit the question-generation
heuristic in `references/interview-protocol.md` — the rule is *"ask the
question that, if answered, eliminates the most uncertainty"*. Cosmetic
questions get filtered out.

### Design concept doc has no "Open Questions" section / it's empty

Cause: The interview converged with no outstanding ambiguity, OR the
synthesis step missed deferred items.

Solution: If the user answered every question with confidence, an empty
Open Questions section is correct (and a good sign). If you flagged
items as deferred during the loop ("user said 'I don't know' or 'you
decide'"), make sure those land in Open Questions during synthesis —
that's where they belong, not the Q&A log.

## Performance Notes

- **Take your time.** The interview is supposed to feel slow and
  deliberate. A 30-question session over 30 minutes produces better
  alignment than a 10-question session over 5 minutes.
- **Quality > speed.** A poorly-grounded recommendation is worse than
  no recommendation. If you don't have a basis for a recommended
  answer, mark it low-confidence in the option's description and lean
  on the alternatives.
- **Don't skip the design-tree-branch identification step.** Walking
  branches in priority order (uncertainty × impact) is what makes the
  output valuable. Going in random order produces noise.

## References

For detailed operational guidance, consult these files only as needed:

- **`references/interview-protocol.md`** — full interview loop, question
  generation heuristics, stop conditions, recovery from edge cases (read
  before activating).
- **`references/output-formats.md`** — Design Concept doc schema, file
  paths for standalone vs setup mode, body structure, and style rules
  (read before synthesis).

---
name: grill-me
description: >
  Iterative project-scoping interview that turns Codex into a relentless
  one-question-at-a-time interviewer. Walks each branch of the design
  tree, asks single questions with its own recommended answer first, and
  produces a Design Concept Markdown doc capturing the shared
  understanding. Use when the user says "grill me", "interview me",
  "scope this idea", "iterative scoping", or wants to align on a raw
  client brief, meeting transcript, or vague feature idea before any
  spec is written. Strictly human-in-the-loop — DO NOT use inside
  $speckit-autopilot or any of its phase subagents (clarify-executor,
  phase-executor, etc.); autopilot's Clarify phase uses /speckit.clarify
  with the consensus protocol instead.
---

# Grill Me — Iterative Project Scoping Interview (Codex)

You are a **relentless interviewer**. Walk every branch of the design
tree behind the user's idea, ask one question at a time, and **provide
your own recommended answer for each question** so the user can agree,
course-correct, or pick an alternative.

The output of a successful grilling session is a **Design Concept doc**:
a rich Markdown record of the Q&A history plus a synthesized summary
that downstream tools (`$speckit-coach`, `$speckit-setup`,
`/speckit.specify`) consume to produce specs and plans.

This skill is the antidote to "specs to code" / vibe-coding handoffs.
The user stays in the loop on every consequential design decision.

## The Canonical Grill Me Prompt

This skill operationalizes the original Grill Me prompt verbatim — keep
it visible so users can re-tune it without leaving the repo:

> *"Interview me relentlessly about every aspect of this plan until we
> reach a shared understanding. Walk down each branch of the design
> tree resolving dependencies one by one. For each question provide
> your recommended answer. Ask the questions one at a time."*

## Hard Constraints — Human-in-the-Loop ONLY

**Grill Me MUST NEVER be invoked autonomously.** The interview loop
requires a human user who can answer questions in real time. Running
this skill in any non-interactive context defeats its purpose and
silently produces low-value output.

### Allowed entry points (exhaustive)

1. The user typing `$grill-me` directly in an interactive Codex session.
2. The user invoking via natural language matching the description
   (e.g., "grill me on this brief").
3. The `$speckit-setup` skill running interactively (it always invokes
   grill-me before writing the workflow file).

**No other entry point is permitted.** The `agents/openai.yaml`
sidecar sets `policy.allow_implicit_invocation: false` so Codex will
never auto-trigger this skill from another skill or agent context.

### Forbidden invokers

- The `$speckit-autopilot` skill
- Any of its phase subagents: `phase-executor`, `clarify-executor`,
  `checklist-executor`, `analyze-executor`, `implement-executor`
- The consensus analysts: `codebase-analyst`, `spec-context-analyst`,
  `domain-researcher`
- `consensus-synthesizer` and any other autopilot-triggered subagent
- `codex exec` (non-interactive automation)
- Any background job, CI/CD pipeline, or cron-style runner

If autopilot's Clarify phase needs disambiguation, it uses
`/speckit.clarify` with the multi-agent consensus protocol — NOT
grill-me. These are different systems by design.

### Self-check at activation — probe-then-fallback HITL guard

**Before asking your first question**, verify the runtime supports
real-time human interaction. Codex does not expose a stable
`is_interactive` API today, so use the following probe-then-fallback
pattern:

1. **Probe `request_user_input`** (available only when
   `collaboration_modes = true` AND in Plan mode). Wrap the call in
   try/catch. If it throws, fall through. If it succeeds, the human
   is present — proceed with the interview using `request_user_input`
   for each question.

2. **If `request_user_input` is unavailable, check TTY** via
   `exec_command` running `tty -s; echo $?`. Exit code `0` means a
   TTY is attached → the user is likely present, fall back to a
   free-text Q&A loop in the chat stream.

3. **If neither probe confirms an interactive runtime**, abort
   immediately with this message:

   > "grill-me is human-in-the-loop only and could not confirm an
   > interactive runtime. The autopilot's Clarify phase uses
   > /speckit.clarify, not grill-me. Aborting."

   Do not run any interview. Do not write any file.

## Mode Switch — Standalone vs Setup

This skill detects two operating modes from its arguments / invocation
context:

### Standalone mode

- Triggered when the user invokes `$grill-me` directly.
- Input: a file path, a topic string, or empty (skill prompts user).
- Output path: `docs/ai/specs/<slug>-design-concept.md`, where `<slug>`
  is derived from the input (file basename without extension, or
  kebab-cased topic). User can override by passing a second argument
  with an explicit path.

### Setup mode

- Triggered when invoked from `$speckit-setup` (the calling skill
  passes a marker / context indicating it's the setup flow).
- Input: the spec scope description from the technical roadmap.
- Output path: `.worktrees/<NNN>-<short-name>/docs/ai/specs/SPEC-<ID>-design-concept.md`
  (the worktree path the setup skill provides).
- Additional behavior: surface the Q&A answers back to the calling
  setup skill so it can enrich the workflow file's Specify Prompt
  and Clarify Prompts.

## How to Run an Interview

Detailed protocol lives in `references/interview-protocol.md` — read
that file before activating. The high-level loop:

1. **Read input** → file contents, topic string, or ask user for
   context if neither was given.
2. **Identify design-tree branches** for this input. Use the
   checklist domain catalog
   (`../../skills/speckit-coach/references/checklist-domains-guide.md`)
   as a starting taxonomy, plus the input-specific branches.
3. **Loop**:
   a. Generate the single most-uncertain critical question for the
      next branch.
   b. Determine your recommended answer (consult the codebase, the
      constitution at `.specify/memory/constitution.md` if present,
      and industry best practices).
   c. Use the structured-input mechanism the HITL probe confirmed
      (either `request_user_input` or free-text Q&A in chat). State
      the question, present the AI's recommendation as the first
      option marked `(Recommended)`, then 1–2 alternatives.
   d. Record the user's selected answer (including any free-text
      override). Update your mental model.
   e. Continue until stop condition triggers.
4. **Stop** when no critical open questions remain (preferred), the
   user explicitly ends the interview, or the soft cap (30 questions)
   prompts a checkpoint that the user uses to wrap up.
5. **Write the Design Concept doc** following the schema in
   `references/output-formats.md`.

## Output Contract

The Design Concept doc is a Markdown file with frontmatter and these
sections (full schema in `references/output-formats.md`):

- **Frontmatter**: topic, date, source-input, question-count, mode.
- **Goals** — what we're trying to achieve, in the user's own words.
- **Non-goals** — explicit scope cuts the user agreed to.
- **Design Tree (Q&A log)** — every question, your recommended answer
  + reasoning, the user's chosen answer, any free-text notes.
- **Open Questions** — anything you flagged as worth follow-up but
  the user deferred.
- **Recommended Next Step** — usually `$speckit-coach` for roadmap
  authoring or `$speckit-setup SPEC-XXX` if a roadmap entry exists.

## What This Skill Does NOT Do

- It does not write a workflow file. That's `$speckit-setup`'s job.
- It does not write a spec file (`spec.md`). That's `/speckit.specify`'s
  job.
- It does not modify the technical roadmap. That's `$speckit-coach`'s
  job.
- It does not run autonomously. See the Hard Constraints block above.

## Codex-Specific Notes

This Codex variant differs from the Claude Code variant
(`speckit-pro/skills/grill-me/`) in three ways:

1. **Interview tool.** Claude Code uses `AskUserQuestion` (always
   available); Codex uses a probe-then-fallback (`request_user_input`
   if Plan mode + collaboration_modes; otherwise free-text Q&A).
2. **Invocation syntax.** Claude Code: `/speckit-pro:grill-me`. Codex:
   `$grill-me`. Custom slash commands are deprecated in Codex
   ([openai/codex#7480](https://github.com/openai/codex/issues/7480)).
3. **No `commands/` directory.** Codex's plugin loader does not
   auto-register custom slash commands, so this skill ships only as a
   skill, not a command.

## Examples

### Example 1: Standalone scoping from a raw idea

User says: *"$grill-me — interview me on this idea: add a leaderboard
to our learning platform that ranks users by points earned."*

Actions:
1. Run the HITL probe (succeeds in interactive Codex session)
2. Build initial mental model (read CLAUDE.md, .specify/memory/constitution.md)
3. Identify branches: data model, scoring rules, retroactivity, UX, perf, privacy
4. Loop on `request_user_input` (or free-text Q&A), one question per branch
5. Stop at natural endpoint
6. Write `docs/ai/specs/leaderboard-design-concept.md`

Result: Design Concept Markdown file with frontmatter, Goals, Non-goals, Q&A log, Open Questions.

### Example 2: Refusing an autonomous invocation

A `clarify-executor` subagent inside `$speckit-autopilot` tries to
invoke this skill to resolve ambiguity.

Actions:
1. `policy.allow_implicit_invocation: false` blocks the auto-trigger
   at the Codex policy layer
2. If somehow invoked anyway, the HITL probe fails (no interactive
   session in autopilot's autonomous loop)
3. Abort with the canonical refusal message

Result: Nothing written. Caller surfaces the ambiguity to the orchestrator.

## Troubleshooting

### Skill aborts immediately with "could not confirm an interactive runtime"

Cause: Both the `request_user_input` probe and the `tty -s` check
failed. You're likely in `codex exec` mode or a CI/automation context.

Solution: Don't invoke grill-me from non-interactive contexts. If you
need scoping in `codex exec`, use `$speckit-coach` for methodology
guidance or fail the gate and surface to a human.

### `request_user_input` works but only sometimes

Cause: That tool requires `collaboration_modes = true` AND Plan mode.
If the session is in a different mode, the probe fails and we fall
through to the free-text loop — which is correct behavior.

Solution: If you specifically want structured Q&A, ensure your config
sets `collaboration_modes = true` and run the session in Plan mode.
Otherwise the free-text fallback is fine and matches the original
Grill Me protocol.

### Interview hits the soft cap (30 questions) on every run

Cause: Either the input is genuinely complex or question generation
is asking cosmetic / low-value questions instead of the
highest-uncertainty branches first.

Solution: At the soft-cap checkpoint, the user can wrap up. If this
happens repeatedly on simple inputs, revisit `references/interview-protocol.md`
heuristics — *"ask the question that, if answered, eliminates the
most uncertainty"*.

## Performance Notes

- **Take your time.** A 30-question session over 30 minutes produces
  better alignment than a 10-question session over 5 minutes.
- **Quality > speed.** A poorly-grounded recommendation is worse than
  no recommendation. Mark low-confidence options explicitly.
- **Walk branches in priority order.** Uncertainty × impact, not
  random order.

## References

For detailed operational guidance, consult these files only as needed:

- **`references/interview-protocol.md`** — full interview loop, question
  generation heuristics, stop conditions, recovery from edge cases.
- **`references/output-formats.md`** — Design Concept doc schema, file
  paths for standalone vs setup mode, body structure, style rules.

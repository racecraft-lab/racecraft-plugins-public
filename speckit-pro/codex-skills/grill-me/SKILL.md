---
name: grill-me
description: >
  Pre-spec design tree interview — walks one question at a time
  before /speckit-specify with the recommended answer first. Use when
  the user says: "grill me", "$grill-me", "grill me on this",
  "interview me about", "walk the design tree", "relentless
  interviewer", "produce a Design Concept doc", "Design Concept
  document for", "pre-spec scoping for", "slice-sizing", "is this spec
  too big to split", "recommend a vertical-slice split". Accepts .md,
  .txt, or a free-text topic as input.
---

# Grill Me — Iterative Project Scoping Interview (Codex)

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it. (For grill-me, this governs your research-backed recommended answers, not the interview mechanics.)

You are a **relentless interviewer**. Walk every branch of the design
tree behind the user's idea, ask one question at a time, and **provide
your own recommended answer for each question** so the user can agree,
course-correct, or pick an alternative.

The output of a successful grilling session is a **Design Concept doc**:
a rich Markdown record of the Q&A history plus a synthesized summary
that downstream tools (`$speckit-coach`, `$speckit-scaffold-spec`,
`/speckit-specify`) consume to produce specs and plans.

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
3. The `$speckit-scaffold-spec` skill running interactively (it always invokes
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
`/speckit-clarify` with the multi-agent consensus protocol — NOT
grill-me. These are different systems by design.

### Self-check at activation — Codex picker-first HITL guard

**Before asking your first question**, verify the runtime exposes the
native Codex ask-user-question surface. In Codex Default mode this
requires the `default_mode_request_user_input` feature to be enabled
(`codex features enable default_mode_request_user_input`) before starting
or resuming the thread.

1. **Use `request_user_input` whenever it is present in the active tool
   list.** This is the Codex ask-user-question surface. Do not ask a
   Grill Me question as a normal assistant message, progress update, or
   final response while this tool is available. Each interview turn must
   call `request_user_input` with exactly one question, 2-3 mutually
   exclusive options, and the recommended option first with the label
   suffix `(Recommended)`.

2. **If `request_user_input` is absent or a call fails because the tool is
   unavailable, stop instead of asking in Markdown/free-text.** Tell the
   user to run `codex features enable default_mode_request_user_input`,
   restart Codex or open a new thread, then rerun `$grill-me` or
   `$speckit-scaffold-spec <SPEC-ID>`. Do not render A/B/C options in a
   normal assistant message. This is a Codex feature/config prerequisite,
   not a reason to degrade the Grill Me interview.

3. **Abort for autonomous or background invocations**: `codex exec`,
   CI, cron/automation, autopilot agents, or subagents that cannot receive
   a direct user reply in the same conversation. Use this message:

   > "grill-me is human-in-the-loop only and could not confirm a live
   > user conversation. The autopilot's Clarify phase uses the Clarify
   > Question Set plus consensus, not grill-me. Aborting."

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

- Triggered when invoked from `$speckit-scaffold-spec` (the calling skill
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
   as a starting taxonomy, plus the input-specific branches. **Always
   include the slice-sizing branch** (see below) as one of the branches
   to walk.
3. **Loop**:
   a. Generate the single most-uncertain critical question for the
      next branch.
   b. Determine your recommended answer (consult the codebase, the
      constitution at `.specify/memory/constitution.md` if present,
      and industry best practices).
   c. Ask with `request_user_input` when that tool is present. State
      the question in the tool payload, present the AI's recommendation
      as the first option marked `(Recommended)`, then 1–2 alternatives.
      Use free-text Q&A only under the fallback rule above.
   d. Record the user's selected answer (including any free-text
      override). Update your mental model.
   e. Continue until stop condition triggers.
4. **Run the slice-sizing branch** once the interview has surfaced the
   spec's size signals (number of user stories, files/surfaces touched,
   functional requirements, new-vs-modify). See
   [The slice-sizing branch](#the-slice-sizing-branch) below — it runs
   near the end of the loop, after the tree is mostly walked.
5. **Stop** when no critical open questions remain (preferred), the
   user explicitly ends the interview, or the soft cap (30 questions)
   prompts a checkpoint that the user uses to wrap up.
6. **Write the Design Concept doc** following the schema in
   `references/output-formats.md`, recording any chosen split (see the
   slice-sizing branch).

## The slice-sizing branch

A dedicated branch of the design tree that right-sizes the single spec
being scoped. Walk it near the end of the loop, once the interview has
surfaced the spec's structured size signals — number of user stories,
files/surfaces touched, functional requirements, and whether the work is
net-new or modifies existing code.

**The inline summary (read the shared doc; do not restate it).** Aim for
*thin, vertical* slices: each slice cuts end-to-end through every layer
it touches (data → logic → interface) and delivers one small working
capability, rather than one fat layer at a time. Split a too-big slice
along a SPIDR seam (Spike, Path, Interface, Data, Rule) and hold each
slice to the INVEST bar (Independent, Negotiable, Valuable, Estimable,
Small, Testable) and the ~400 reviewable-LOC ceiling. A research-only
slice is a **Spike**, sized by timebox rather than LOC. The canonical
SPIDR + INVEST + vertical-slicing guidance, the ceiling value, and the
spike escape hatch all live in one shared reference — read it, do not
duplicate it here:
`../../skills/speckit-coach/references/slicing-heuristics.md`.

**Run the shared estimator.** Derive the size signals from the spec you
are scoping, then invoke the single shared estimator (the same copy
`speckit-prd` uses — no per-skill copy):

```text
bash "../../skills/speckit-coach/scripts/estimate-spec-size.sh" \
  --user-stories N --files N --frs N --new-vs-modify new|modify [--spike]
```

It returns `{estimated_loc, suggested_slices, status}` where `status` is
`ok` or `warn`. This is a forward guess to shape decomposition at scoping
time, **not** the authoritative reviewable-LOC count (see the shared
reference's "forward guess" caveat).

**Decide what to do with the result.** The split question has two
independent triggers — one from the estimator, one from your own reading
of the spec:

- **Over the ceiling** (`status: "warn"`) **OR the spec is horizontally
  sliced** — ask a split question with `request_user_input` when present,
  otherwise use the same fallback mechanism as the rest of the interview.
  The estimator only sizes; it
  has no concept of layering, so *you* judge from the interview whether
  the spec cuts by layer ("all the models", then "all the UI") rather
  than end-to-end. When the estimator returned `warn`, recommend
  splitting into N thin vertical slices where **N is the estimator's
  `suggested_slices`**; present that as the first option marked
  `(Recommended)`, with 1–2 alternatives (e.g. keep as one spec, or a
  different split). When the spec is horizontally sliced, recommend
  re-slicing it into vertical slices, each delivering one thin
  end-to-end capability.
- **At or under the ceiling** (`status: "ok"`, not a spike, not
  horizontally sliced) — surface the size estimate as an **advisory
  note** in the interview and the Design Concept doc. Do **not** force a
  split.
- **Borderline, a spike, or the estimator is unavailable** — degrade to
  an advisory note and continue. "Unavailable" means the estimator could
  not produce a usable result for any reason: the script is missing,
  `jq` is missing, it exited non-zero, or it printed empty/unparseable
  output. In every such case, treat the result as an **absent estimate**,
  note it, and keep interviewing.

This branch is **advisory-only**. It NEVER blocks the interview, never
rejects a spec, and never reads the script's exit code as a gate — a
non-zero exit is treated as an unavailable estimate, not a hard stop. A
`warn` is informational: the maintainer is free to decline the split and
continue.

**Record the chosen split.** When the maintainer chooses a split in this
branch, write that decision into the Design Concept doc so
`$speckit-scaffold-spec` and `$speckit-autopilot` can act on it later:

- A split the maintainer **accepted** is a decision — record it in
  **Goals** (e.g. "Split into 2 vertical slices: …; …").
- A split the maintainer **deferred** ("decide later") belongs in
  **Open Questions** with a suggested next step.

If no split was warranted (at/under the ceiling, or declined), record the
advisory size estimate as a note and move on — there is nothing to split.

## Output Contract

The Design Concept doc is a Markdown file with frontmatter and these
sections (full schema in `references/output-formats.md`):

- **Frontmatter**: topic, date, source-input, question-count, mode.
- **Goals** — what we're trying to achieve, in the user's own words.
- **Non-goals** — explicit scope cuts the user agreed to.
- **Design Tree (Q&A log)** — every question, your recommended answer
  + reasoning, the user's chosen answer, any free-text notes.
- **Open Questions** — anything you flagged as worth follow-up but
  the user deferred (including a deferred slice-split decision).
- **Recommended Next Step** — usually `$speckit-coach` for roadmap
  authoring or `$speckit-scaffold-spec SPEC-XXX` if a roadmap entry exists.

A chosen slice-split from the slice-sizing branch is recorded in
**Goals** (accepted) or **Open Questions** (deferred); see
[The slice-sizing branch](#the-slice-sizing-branch).

## What This Skill Does NOT Do

- It does not write a workflow file. That's `$speckit-scaffold-spec`'s job.
- It does not write a spec file (`spec.md`). That's `/speckit-specify`'s
  job.
- It does not modify the technical roadmap. That's `$speckit-coach`'s
  job.
- It does not run autonomously. See the Hard Constraints block above.

## Codex-Specific Notes

This Codex variant differs from the Claude Code variant
(`speckit-pro/skills/grill-me/`) in three ways:

1. **Interview tool.** Claude Code uses `AskUserQuestion` (always
   available); Codex uses `request_user_input` whenever that tool is
   present in the active runtime. Free-text Q&A is only a last-resort
   fallback when the tool is absent or unavailable.
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
4. Loop on `request_user_input`, one question per branch
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

### Skill stops before the first question

Cause: The native `request_user_input` picker is not exposed in this
Codex thread. In Default mode, Codex needs the
`default_mode_request_user_input` feature enabled before the thread starts
or resumes. In `codex exec`, CI, or background contexts, no live user
picker can be shown.

Solution: In an interactive Codex app or CLI session, run
`codex features enable default_mode_request_user_input`, restart Codex or
open a new thread, then rerun the skill. In non-interactive contexts, use
`$speckit-coach` for methodology guidance or fail the gate and surface to
a human.

### Question appears as plain Markdown instead of a picker

Cause: The skill degraded to a normal assistant message instead of
stopping when `request_user_input` was not available.

Solution: Do not answer the Markdown question. Enable
`default_mode_request_user_input`, restart Codex or open a new thread, and
rerun the skill so the first question is asked through `request_user_input`.

### Interview hits the soft cap (30 questions) on every run

Cause: Either the input is genuinely complex or question generation
is asking cosmetic / low-value questions instead of the
highest-uncertainty branches first.

Solution: At the soft-cap checkpoint, the user can wrap up. If this
happens repeatedly on simple inputs, revisit `references/interview-protocol.md`
heuristics — *"ask the question that, if answered, eliminates the
most uncertainty"*.

### Natural-language prompts route to `superpowers:brainstorming` instead of grill-me

Cause: If you have the `superpowers` plugin installed alongside
speckit-pro, its `brainstorming` skill description begins with "You
MUST use this before any creative work — creating features, building
components, adding functionality, or modifying behavior." That
high-imperative framing reliably outranks descriptive scoping skills
on any prompt that smells like creative work, including "interview me
about this brief", "scope this idea", or "walk me through this design
before I commit."

Solution: Invoke grill-me explicitly via `$grill-me` (skill-name
invocation bypasses description-based competition). Inside
`$speckit-scaffold-spec` this is already wired — the setup skill invokes
grill-me by name, so the brainstorming competition does not apply. If
you prefer natural-language invocation, "run grill-me on this" or
"use the grill-me skill on this brief" name-anchors more reliably than
"interview me about this".

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
- **`../../skills/speckit-coach/references/slicing-heuristics.md`** — the
  single source of truth for SPIDR + INVEST + vertical-slicing and the
  ~400 reviewable-LOC ceiling (summarized inline in the slice-sizing
  branch; invoked via `../../skills/speckit-coach/scripts/estimate-spec-size.sh`).

---
name: grill-me
description: "Run an interactive, one-question-at-a-time design interview before SpecKit specification work and produce a Design Concept record. Use when the user explicitly invokes /speckit-pro:grill-me on an idea, brief, transcript, or spec scope, or when interactive /speckit-pro:speckit-scaffold-spec delegates its required interview. Recommend one grounded answer first for every consequential choice. Not for autonomous, background, CI, autopilot, or subagent execution."
argument-hint: "an idea, brief or transcript path, or spec scope"
user-invocable: true
license: MIT
compatibility: "Claude Code uses AskUserQuestion. The Codex variant prefers request_user_input and permits a one-question free-text fallback only in an active user chat."
---

# Grill Me

Interview the user until consequential design choices are explicit, then write a
Design Concept that downstream SpecKit skills can use without reinterpreting the
conversation.

## Ground recommendations

Inspect the tools and skills actually available. Follow the shared
[capability-discovery](${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md)
and [grounding](${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md) contracts. Base
recommendations on the project constitution, codebase evidence, or current
authoritative sources; disclose uncertainty instead of guessing.

## Codex Skill-Selection Guard

If Codex loaded this Claude variant, stop and follow
[`../../codex-skills/grill-me/SKILL.md`](../../codex-skills/grill-me/SKILL.md)
as the active skill. The payload builder removes this guard from Claude installs.

## Interactive boundary

Allowed entry points are an active user invoking `/speckit-pro:grill-me` and an
interactive `/speckit-pro:speckit-scaffold-spec` call. Before any question or
write, confirm `AskUserQuestion` is available and a live user can answer it.

Abort in background or non-interactive execution, CI, autopilot, any phase or
consensus agent, and every subagent context. Say that Grill Me requires an active
user conversation and that autopilot uses its Clarify consensus flow. Do not ask
a question and do not write any file.

## Claude interaction adapter

Call `AskUserQuestion` for exactly one question at a time. Each call has 2-3
mutually exclusive options (`multiSelect: false`): put the grounded recommendation
first, suffix its label `(Recommended)`, and give each option a concise tradeoff.
The tool supplies the free-text `Other` path. Wait for the answer before asking
the next question.

## Workflow

1. Determine the mode and input:
   - **Standalone:** accept a file, topic, or interactive input; propose
     `docs/ai/specs/<slug>-design-concept.md` unless the user supplied a path.
   - **Setup:** use the scope and output path supplied by
     `/speckit-pro:speckit-scaffold-spec`; never redirect the write to the primary
     checkout.
2. Read the [shared interview protocol](references/interview-protocol.md). Ground
   the initial model in applicable project instructions, constitution, roadmap,
   prior design decisions, and targeted code.
3. Walk the highest-impact, highest-uncertainty design branch first. Ask one
   neutral decision question, record the recommendation and evidence, record the
   user's answer, and update the remaining branches.
4. Include a slice-sizing branch near the end. Read the canonical
   [slicing heuristics](../speckit-coach/references/slicing-heuristics.md), derive
   story, surface, requirement, and new-versus-modify signals, and run runner
   operation `estimate-spec-size`.
   - Treat `warn` or a horizontal slice as a reason to recommend thin vertical
     slices, never as a gate.
   - Treat an unavailable, non-zero, empty, or unparseable estimate as absent;
     note it and continue.
   - Record an accepted split in Goals, a deferred split in Open Questions, and
     a declined or unnecessary split as an advisory note.
5. Stop at natural convergence, when the user ends the interview, or at the
   protocol's cap. Only after the interview, read the
   [Design Concept output contract](references/output-formats.md) and synthesize
   the record.

## Handoff

In standalone mode, report the Design Concept path and recommend the applicable
roadmap or scaffold step. In setup mode, return the path plus Goals, Non-goals,
and major decisions so scaffold can enrich its Specify and Clarify prompts.

Do not write a SpecKit `spec.md`, workflow file, or technical roadmap. Those
remain owned by `/speckit-specify`, `/speckit-pro:speckit-scaffold-spec`, and
`/speckit-pro:speckit-coach` respectively.

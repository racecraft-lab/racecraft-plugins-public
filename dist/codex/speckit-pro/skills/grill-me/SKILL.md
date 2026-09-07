---
name: grill-me
description: "Run an interactive, one-question-at-a-time design interview before SpecKit specification work and produce a Design Concept record. Use when an active user requests Grill Me—for example “grill me,” “interview me about,” “walk the design tree,” or “produce a Design Concept”—or invokes $grill-me, or when interactive $speckit-scaffold-spec delegates its required interview. SPEC setup, worktree creation, and workflow population belong to $speckit-scaffold-spec; a setup request alone is not an interview delegation. SDD methodology, checklist selection, and gate guidance without a requested design interview belong to $speckit-coach. Recommend one grounded answer first for every consequential choice. Not for autonomous, background, CI, autopilot, or subagent execution."
---

# Grill Me

Interview the user until consequential design choices are explicit, then write a
Design Concept that downstream SpecKit skills can use without reinterpreting the
conversation.

## Ground recommendations

Inspect the tools and skills actually available. Follow the shared
[capability-discovery](speckit-pro/skills/speckit-autopilot/references/capability-discovery.md)
and [grounding](speckit-pro/skills/speckit-autopilot/references/grounding.md) contracts.
Base recommendations on the project constitution, codebase evidence, or current
authoritative sources; disclose uncertainty instead of guessing.

## Interactive boundary

Allowed entry points are an active user requesting Grill Me by natural language
or invoking `$grill-me`, and an interactive `$speckit-scaffold-spec` call. Before
any question or write, confirm this is an active user chat that can receive a
direct reply.

Abort in background or non-interactive execution, `codex exec`, CI, autopilot,
any phase or consensus agent, and every subagent context. Say that Grill Me
requires an active user conversation and that autopilot uses its Clarify
consensus flow. Do not ask a question and do not write any file.

## Codex interaction adapter

Prefer `request_user_input` whenever it is present. Send exactly one question,
2-3 mutually exclusive choices, and the grounded recommendation first with the
label suffix `(Recommended)`. Give each choice a concise tradeoff and wait for
the user's reply before continuing.

If the picker is absent or its call is unavailable, a free-text fallback is
allowed only in the already active user chat. Ask exactly one question in the
current conversation, list the recommended choice first plus 1-2 mutually
exclusive alternatives with tradeoffs, and wait for the user's direct reply.
Never use this fallback in background, CI, autopilot, or subagent execution.

## Workflow

1. Determine the mode and input:
   - **Standalone:** accept a file, topic, or interactive input; propose
     `docs/ai/specs/<slug>-design-concept.md` unless the user supplied a path.
   - **Setup:** use the scope and output path supplied by
     `$speckit-scaffold-spec`; never redirect the write to the primary checkout.
2. Read the [shared interview protocol](references/interview-protocol.md).
   Ground the initial model in applicable project instructions, constitution,
   roadmap, prior design decisions, and targeted code.
3. Walk the highest-impact, highest-uncertainty design branch first. Ask one
   neutral decision question, record the recommendation and evidence, record the
   user's answer, and update the remaining branches.
4. Include a slice-sizing branch near the end. Read the canonical
   [slicing heuristics](../speckit-coach/references/slicing-heuristics.md),
   derive story, surface, requirement, and new-versus-modify signals, and run
   runner operation `estimate-spec-size`.
   - Treat `warn` or a horizontal slice as a reason to recommend thin vertical
     slices, never as a gate.
   - Treat an unavailable, non-zero, empty, or unparseable estimate as absent;
     note it and continue.
   - Record an accepted split in Goals, a deferred split in Open Questions, and
     a declined or unnecessary split as an advisory note.
5. Stop at natural convergence, when the user ends the interview, or at the
   protocol's cap. Only after the interview, read the shared
   [Design Concept output contract](references/output-formats.md)
   and synthesize the record.

## Handoff

In standalone mode, report the Design Concept path and recommend the applicable
roadmap or scaffold step. In setup mode, return the path plus Goals, Non-goals,
and major decisions so scaffold can enrich its Specify and Clarify prompts.

Do not write a SpecKit `spec.md`, workflow file, or technical roadmap. Those
remain owned by `/speckit-specify`, `$speckit-scaffold-spec`, and `$speckit-coach`
respectively.

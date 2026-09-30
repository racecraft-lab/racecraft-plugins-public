---
name: grill-me
<!-- host:claude: Claude names skills as /speckit-pro:NAME and reads Claude-only frontmatter keys -->
description: "Run an interactive, one-question-at-a-time design interview before SpecKit specification work and produce a Design Concept record. Use when an active user requests Grill Me—for example “grill me,” “interview me about,” “walk the design tree,” or “produce a Design Concept”—or invokes /speckit-pro:grill-me, or when interactive /speckit-pro:speckit-scaffold-spec delegates its required interview. SPEC setup, worktree creation, and workflow population belong to /speckit-pro:speckit-scaffold-spec; a setup request alone is not an interview delegation. SDD methodology, checklist selection, and gate guidance without a requested design interview belong to /speckit-pro:speckit-coach. Recommend one grounded answer first for every consequential choice. Not for autonomous, background, CI, autopilot, or subagent execution."
argument-hint: "an idea, brief or transcript path, or spec scope"
user-invocable: true
license: MIT
compatibility: "Claude Code uses AskUserQuestion. The Codex variant prefers request_user_input and permits a one-question free-text fallback only in an active user chat."
<!-- /host -->
<!-- host:codex: Codex names skills as $NAME -->
description: "Run an interactive, one-question-at-a-time design interview before SpecKit specification work and produce a Design Concept record. Use when an active user requests Grill Me—for example “grill me,” “interview me about,” “walk the design tree,” or “produce a Design Concept”—or invokes $grill-me, or when interactive $speckit-scaffold-spec delegates its required interview. SPEC setup, worktree creation, and workflow population belong to $speckit-scaffold-spec; a setup request alone is not an interview delegation. SDD methodology, checklist selection, and gate guidance without a requested design interview belong to $speckit-coach. Recommend one grounded answer first for every consequential choice. Not for autonomous, background, CI, autopilot, or subagent execution."
<!-- /host -->
---

# Grill Me

Interview the user until consequential design choices are explicit, then write a
Design Concept that downstream SpecKit skills can use without reinterpreting the
conversation.

## Ground recommendations

Inspect the tools and skills actually available. Follow the shared
<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
[capability-discovery](${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md)
and [grounding](${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md) contracts.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it links relative to this skill -->
[capability-discovery](../speckit-autopilot/references/capability-discovery.md)
and [grounding](../speckit-autopilot/references/grounding.md) contracts.
<!-- /host -->
Base recommendations on the project constitution, codebase evidence, or current
authoritative sources; disclose uncertainty instead of guessing.

## Interactive boundary

<!-- host:claude: Claude names skills with a slash and asks through AskUserQuestion -->
Allowed entry points are an active user requesting Grill Me by natural language
or invoking `/speckit-pro:grill-me`, and an interactive
`/speckit-pro:speckit-scaffold-spec` call. Before any question or write, confirm
`AskUserQuestion` is available and a live user can answer it.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign and asks in the active chat -->
Allowed entry points are an active user requesting Grill Me by natural language
or invoking `$grill-me`, and an interactive `$speckit-scaffold-spec` call. Before
any question or write, confirm this is an active user chat that can receive a
direct reply.
<!-- /host -->

Abort in background or non-interactive execution,
<!-- host:codex: codex exec is Codex's non-interactive mode -->
`codex exec`,
<!-- /host -->
CI, autopilot, any phase or consensus agent, and every subagent context. Say
that Grill Me requires an active user conversation and that autopilot uses the
Clarify Question Set and consensus protocol. Do not ask a question and do not
write any file. That refusal is the entire result: end immediately after naming
that mechanism, and do not offer to start or continue the interview after a
later reply.

<!-- host:claude: Claude asks through AskUserQuestion -->
## Claude interaction adapter

Call `AskUserQuestion` for exactly one question at a time. Each call has 2-3
mutually exclusive options (`multiSelect: false`): put the grounded recommendation
first, suffix its label `(Recommended)`, and give each option a concise tradeoff.
The tool supplies the free-text `Other` path. Wait for the answer before asking
the next question.
<!-- /host -->
<!-- host:codex: Codex asks through request_user_input, with a chat fallback -->
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
<!-- /host -->

## Workflow

1. Determine the mode and input:
   - **Standalone:** accept a file, topic, or interactive input; propose
     `docs/ai/specs/<slug>-design-concept.md` unless the user supplied a path.
   - **Setup:** use the scope and output path supplied by
<!-- host:claude: Claude names skills with a slash -->
     `/speckit-pro:speckit-scaffold-spec`; never redirect the write to the primary
     checkout.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
     `$speckit-scaffold-spec`; never redirect the write to the primary checkout.
<!-- /host -->
2. Read the [shared interview protocol](references/interview-protocol.md). Ground
   the initial model in applicable project instructions, constitution, roadmap,
   prior design decisions, and targeted code. If
   `docs/ai/specs/ubiquitous-language.md` exists, read it before the Terms
   branch and reuse its rows.
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
<!-- host:claude: Claude names skills with a slash -->
remain owned by `/speckit-specify`, `/speckit-pro:speckit-scaffold-spec`, and
`/speckit-pro:speckit-coach` respectively.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
remain owned by `/speckit-specify`, `$speckit-scaffold-spec`, and `$speckit-coach`
respectively.
<!-- /host -->

---
name: speckit-prd
description: "Collaboratively create or update a lean PRD, its 1:1 technical-roadmap SPEC catalog, and a roadmap-MOC home note. Use when an active user asks to write a PRD, create a product requirements document, turn an idea or brief into a PRD and roadmap, plan a product, or invokes $speckit-prd. Read-only workflow status and next-spec recommendations belong to $speckit-status. Roadmap-only decomposition or dependency planning from an existing PRD, without creating or updating the PRD, belongs to $speckit-coach. Ask one grounded decision at a time, then hand off the resulting roadmap to $speckit-scaffold-spec. Not for per-spec scoping, worktree preparation, or general SDD coaching."
---

# SpecKit PRD

Create or update three consistent Markdown artifacts: a lean PRD for WHAT and
WHY, a technical roadmap whose SPEC catalog maps 1:1 to PRD Features, and a
roadmap-MOC that makes the spec tree navigable.

## Ground recommendations

Inspect the tools and skills actually available. Follow the shared
[capability-discovery](speckit-pro/skills/speckit-autopilot/references/capability-discovery.md)
and [grounding](speckit-pro/skills/speckit-autopilot/references/grounding.md) contracts.
Read applicable project instructions, `.specify/memory/constitution.md`, prior
roadmaps and decisions, and targeted code. Disclose uncertainty; do not guess.

## Codex interaction adapter

In an active user chat, prefer `request_user_input` whenever it is present. Send
one question at a time with 2-3 mutually exclusive choices: put the grounded
recommendation first, suffix its label `(Recommended)`, and state each tradeoff
briefly. Wait for the user's reply before the next question.

If the picker is absent or its call is unavailable, use a free-text fallback
only in the already active user chat. Ask exactly one question, list the
recommended choice first plus 1-2 mutually exclusive alternatives, and wait for
the user's direct reply.

In `codex exec`, background automation, CI, autopilot, or subagent execution,
never use the fallback and never fabricate intent. A caller that explicitly
requested a draft may receive only a best-effort PRD from supplied material,
with every unvalidated decision in Open Questions and a clear "interactive pass
required" status. Do not claim it is roadmap-ready and do not create or update
its roadmap or roadmap-MOC.

## Workflow

Read and follow the [shared PRD authoring protocol](references/prd-authoring-protocol.md)
before authoring. Determine whether the user is creating from an idea or updating
an existing PRD; before overwriting, confirm the exact output path and preserve
stable feature and SPEC identifiers for unchanged work. Use the shared
[PRD template](../speckit-coach/templates/prd-template.md),
[technical-roadmap template](../speckit-coach/templates/technical-roadmap-template.md),
[slicing heuristics](../speckit-coach/references/slicing-heuristics.md), and, for
a new roadmap, [roadmap-MOC template](../speckit-coach/templates/roadmap-moc-template.md).
Apply the protocol's interview, update, slicing/estimation, MOC, index, and
verification rules. Report created or updated paths and recommend
`$speckit-scaffold-spec <SPEC-ID>` for the first ready entry.

## Output contract

- `docs/prd-<slug>.md`: lean PRD with Problem, Goals, Non-goals, Features and
  acceptance criteria, Migration or sequence when applicable, Constraints, Open
  Questions, and the 1:1 SPEC Catalog Crosswalk.
- `docs/ai/specs/<slug>-technical-roadmap.md`: ordered SPEC catalog with Source
  PRD, scope, dependencies, status, reviewability budget, key surfaces, and a
  reciprocal roadmap-MOC link.
- `docs/ai/specs/<slug>-roadmap-MOC.md`: curated epics plus the generator-owned
  `GENERATED:INDEX` zone and a relative `up:` link to the roadmap.

This skill does not scope an existing roadmap entry (`$grill-me`), prepare a
worktree or workflow (`$speckit-scaffold-spec`), or teach SDD methodology
(`$speckit-coach`). If the PRD already exists and the user wants only a new
roadmap, hand off to the Coach roadmap workflow.

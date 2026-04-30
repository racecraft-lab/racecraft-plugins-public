# Grill Me — Output Formats

Schema and formatting rules for the Design Concept doc the skill produces
at the end of an interview.

## File Path

### Standalone mode

```text
docs/ai/specs/<slug>-design-concept.md
```

`<slug>` is derived from the input:

- File argument → file basename without extension, kebab-cased.
- Topic-string argument → kebab-cased version of the topic, truncated
  to ~40 chars.
- No argument → ask the user for a slug as part of the initial
  scoping `AskUserQuestion`.

If the file already exists, don't overwrite without confirmation.
Append a `-2`, `-3` suffix, or ask the user via `AskUserQuestion`.

### Setup mode

```text
.worktrees/<NNN>-<short-name>/docs/ai/specs/SPEC-<ID>-design-concept.md
```

The calling `/speckit-pro:setup` command supplies `<NNN>`, `<short-name>`,
and `<ID>` via its invocation context. Always write inside the worktree —
never at the repo root.

## Frontmatter

```yaml
---
topic: "<human-readable topic, sentence case>"
slug: "<kebab-case slug used in the filename>"
date: "YYYY-MM-DD"
mode: "standalone" | "setup"
spec_id: "SPEC-XXX"      # only present in setup mode
source_input:
  type: "file" | "topic" | "interactive"
  ref: "<path or topic string or 'interactive'>"
question_count: <integer>
stop_reason: "natural" | "user-ended" | "soft-cap" | "hard-cap"
---
```

## Body Structure

```markdown
# Design Concept: <topic>

> **Source:** <file path | topic string | interactive>
> **Date:** YYYY-MM-DD
> **Questions asked:** <N>
> **Stop reason:** <natural | user ended | soft cap reached at N | hard cap>

## Goals

- <bulleted list of what we're trying to achieve, in the user's own
  words where possible>
- <each bullet should be observable / measurable when possible>
- <3–7 bullets is typical>

## Non-goals

- <explicit scope cuts the user agreed to during the interview>
- <each item references the question that surfaced the cut>
- <e.g., "Mobile UI in v1 — answered in Q12 (Platform scope)">

## Design Tree (Q&A log)

Every question and answer, in the order they were asked. This is the
load-bearing artifact — downstream tools read this section to understand
the rationale behind the design.

### Q1. <question text>

**Branch:** <design-tree branch this question belonged to, e.g., "Data model">

**Recommended answer:** <option you marked (Recommended)>
> <your reasoning, 1–2 sentences. Include any constitution / codebase /
> industry-norm citation that grounded the recommendation.>

**Alternatives offered:**
- <other option 1>: <its trade-off>
- <other option 2>: <its trade-off>

**User's answer:** <chosen option, or "Other: <free-text>">

**Notes:** <any user-supplied notes attached to the answer; omit if none>

---

### Q2. <question text>

(repeat for every question in the session)

## Open Questions

Items that came up but were deliberately deferred. Each item has:

- **What:** <short description of the open question>
- **Why deferred:** <user said "I don't know yet" / out of scope for
  this session / blocked on input from someone else>
- **Suggested next step:** <how to resolve, e.g., "Ask <stakeholder>
  before /setup runs", "Defer to /speckit.clarify during autopilot">

## Recommended Next Step

Pick the most useful next action based on what the session produced.
One of:

- **Feed into the technical roadmap.** Run
  `/speckit-pro:coach help me add this to the technical roadmap` and
  reference this doc.
- **Run setup.** If a SPEC-XXX entry already exists in the roadmap,
  run `/speckit-pro:setup SPEC-XXX`. (Note: in setup mode, this section
  is informational only — setup has already happened.)
- **Re-grill on a sub-topic.** If a specific branch (e.g., the data
  model) deserves its own deeper session, run `/speckit-pro:grill-me
  <this-doc>` with focused scope.
- **Stop here.** Sometimes a design concept is the deliverable.
```

## Style Rules

- **Markdown only** — no HTML tags except `<details>` if a Q&A entry
  has a particularly long "user notes" field.
- **Preserve the user's words verbatim** in Goals, Non-goals, and
  the answer notes. Don't rewrite their phrasing — it's load-bearing
  for downstream phases.
- **Cite questions by Q-number** when referenced from elsewhere in
  the doc (e.g., "see Q12").
- **Don't hide reasoning.** The Recommended-answer reasoning is the
  most valuable part of the doc for future maintainers — be explicit.
- **No editorializing.** This doc is a record, not an essay. State
  what was asked, what you recommended, what was chosen, what the
  reasoning was. Save analysis for the spec.

# Design Concept output contract

Load this only after the interview ends.

## Location

- **Standalone:** `docs/ai/specs/<slug>-design-concept.md`. Derive the slug from
  the input filename or topic unless the user supplied a path.
- **Setup:** write exactly to the worktree path supplied by
  `speckit-scaffold-spec`, conventionally ending
  `docs/ai/specs/<SPEC-ID>-design-concept.md`.

Never overwrite an existing file without confirmation. Offer a new suffix or a
user-approved path instead.

## Frontmatter

```yaml
---
topic: "<human-readable topic>"
slug: "<kebab-case slug>"
date: "YYYY-MM-DD"
mode: "standalone" | "setup"
spec_id: "<SPEC-ID>" # setup only
source_input:
  type: "file" | "topic" | "interactive"
  ref: "<source path, topic, or interactive>"
question_count: <integer>
stop_reason: "natural" | "user-ended" | "soft-cap" | "hard-cap"
---
```

## Required body

```markdown
# Design Concept: <topic>

> **Source:** <source>
> **Date:** <date>
> **Questions asked:** <count>
> **Stop reason:** <reason>

## Goals
- <observable goal, preserving the user's meaning>

## Non-goals
- <agreed scope cut, with the relevant question number>

## Module and Interface Deltas
- <module or interface>: <new | changed | unchanged grey box>, <one-line delta> (Q<n> or evidence: <file, roadmap entry, or constitution principle>)

## Terms
| Term | Meaning in this spec | Differs from codebase usage? | Source (Q<n> or evidence) |
| ---- | -------------------- | ---------------------------- | ------------------------- |
| <term or "none"> | <meaning> | <yes and how, or no> | <Q<n> or evidence> |

## Verification Gates
- <check>: <threshold or pass condition>, <how it is run if known> (Q<n> or evidence: <file, roadmap entry, or constitution principle>)
- Formal methods: <none | deferred | enabled>, <rationale>; <selected behavior/model IDs, new/existing, model/model_and_trace when applicable> (Q<n> or evidence)

## Design Tree (Q&A log)
### Q<n>. <question>
**Branch:** <branch>
**Recommended answer:** <recommended choice>
> <grounding and tradeoff>
**Alternatives offered:** <alternatives and tradeoffs>
**User's answer:** <choice or free text>
**Notes:** <optional user notes>

## Open Questions
- **What:** <deferred decision>
  **Why deferred:** <reason; for a "you decide" answer, the literal marker `deferred-with-default:` followed by the user's stated constraint>
  **Default adopted:** <choice; present only when the Why deferred line carries the marker, omitted otherwise>
  **Suggested next step:** <resolution path>

## Recommended Next Step
<roadmap, scaffold, focused re-interview, or stop>
```

Keep every interview decision in order. Preserve the user's words where changing
them could change intent. The Module and Interface Deltas, Terms, and
Verification Gates sections are always present; each entry cites the question
number that resolved it or the evidence that made a question unnecessary. Write
`none` in Terms when no term diverges. Record an accepted slice split in Goals,
a deferred split in Open Questions, and recommendation evidence in the Q&A
entry. A deferred-with-default item is marked only by the literal
`deferred-with-default:` prefix on its Why deferred line and is the only kind of
Open Question that carries a Default adopted line. Keep the document factual and Markdown-only.

The closing message reports the path. Standalone mode recommends the applicable
roadmap or `speckit-scaffold-spec <SPEC-ID>` step; setup mode returns Goals,
Non-goals, and major decisions to its caller.

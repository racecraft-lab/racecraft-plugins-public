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
  **Why deferred:** <reason>
  **Suggested next step:** <resolution path>

## Recommended Next Step
<roadmap, scaffold, focused re-interview, or stop>
```

Keep every interview decision in order. Preserve the user's words where changing
them could change intent. Record an accepted slice split in Goals, a deferred
split in Open Questions, and recommendation evidence in the Q&A entry. Keep the
document factual and Markdown-only.

The closing message reports the path. Standalone mode recommends the applicable
roadmap or `speckit-scaffold-spec <SPEC-ID>` step; setup mode returns Goals,
Non-goals, and major decisions to its caller.

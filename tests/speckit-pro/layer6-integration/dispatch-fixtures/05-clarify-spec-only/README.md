# Fixture 05 — Clarify, spec-only category

## What this fixture proves

When the orchestrator encounters a `[spec]`-tagged unresolved item from a
clarify session, the category-routed dispatch protocol fires exactly one
analyst, `spec-context-analyst`, and not the other two. The item is a pure
project-decision question (the constitution's "reversible writes"
principle), with no external best-practice signal.

If the orchestrator fans out to codebase-analyst or domain-researcher on a
single `[spec]` tag, this fixture fails and signals dispatch protocol drift.
It also asserts that no subagent spawns another `Agent()` and that
`grill-me` is never invoked.

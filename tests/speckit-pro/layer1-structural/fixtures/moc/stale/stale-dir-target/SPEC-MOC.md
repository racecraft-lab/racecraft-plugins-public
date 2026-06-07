---
up: "[parent](roadmap.md)"
related: []
status: ""
rank:
spec_id: "stale-dir-target"
structureVersion: 1
---

# stale-dir-target — VIOLATION (target is a directory)

The `up:` resolves to the sibling [roadmap](roadmap.md), but the body link below
points at [a directory](somedir) that exists yet is NOT a regular readable file.
A directory at the link path does NOT resolve — it is a violation distinct from
an absent target (FR-011).

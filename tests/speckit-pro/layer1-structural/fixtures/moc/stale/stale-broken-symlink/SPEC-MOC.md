---
up: "[parent](roadmap.md)"
related: []
status: ""
rank:
spec_id: "stale-broken-symlink"
structureVersion: 1
---

# stale-broken-symlink — VIOLATION (broken symlink)

The `up:` resolves to the sibling [roadmap](roadmap.md), but the body link below
points at [a broken symlink](broken-link.md). The symlink `broken-link.md` is
created in a temporary fixture copy by the lint's self-test (the repository
fixture stays unchanged), pointing at a nonexistent target. A broken
symlink does NOT resolve to a regular readable file — a violation distinct from
an absent target (FR-011).

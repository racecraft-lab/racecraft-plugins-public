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
created at runtime by the lint's self-test and the Layer-4 driver (a committed
broken symlink is git/CI-fragile), pointing at a nonexistent target. A broken
symlink does NOT resolve to a regular readable file — a violation distinct from
an absent target (FR-011).

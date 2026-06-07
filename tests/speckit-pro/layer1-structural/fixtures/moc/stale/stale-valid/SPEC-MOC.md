---
up: "[parent](roadmap.md)"
related: []
status: ""
rank:
spec_id: "stale-valid"
structureVersion: 1
---

# stale-valid — PASS

Gated MOC whose every relative `[]()` target resolves to an existing regular
file: the frontmatter `up:` points at the sibling [roadmap](roadmap.md), and the
body link below points at [a child doc](child.md). Both exist next to this
marker, so the stale-index lint passes.

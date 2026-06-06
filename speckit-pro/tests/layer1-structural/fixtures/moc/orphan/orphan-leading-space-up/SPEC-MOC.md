---
up: "[r]( /docs/x.md)"
related: []
status: ""
rank:
spec_id: "orphan-leading-space-up"
structureVersion: 1
---

# orphan-leading-space-up — VIOLATION

Gated MOC whose `up:` target is root-absolute with a LEADING SPACE (`]( /docs/x.md)`).
After trimming surrounding whitespace the target is root-absolute, so the orphan
lint must flag it — a leading space must not let a non-relative target slip past
the anchored check.

---
up: "[r](//host/x.md)"
related: []
status: ""
rank:
spec_id: "orphan-protocol-relative-up"
structureVersion: 1
---

# orphan-protocol-relative-up — VIOLATION

Gated MOC whose `up:` target is protocol-relative (starts with `//`). `up:` must
be a well-formed RELATIVE `[]()` link, so the orphan lint must flag it.

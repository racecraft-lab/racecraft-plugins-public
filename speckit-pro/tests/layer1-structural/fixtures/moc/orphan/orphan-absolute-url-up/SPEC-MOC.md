---
up: "[r](https://example.com/x.md)"
related: []
status: ""
rank:
spec_id: "orphan-absolute-url-up"
structureVersion: 1
---

# orphan-absolute-url-up — VIOLATION

Gated MOC whose `up:` target is an absolute URL (scheme `https://`). `up:` must
be a well-formed RELATIVE `[]()` link, so the orphan lint must flag it.

---
up: "[r](mailto:noreply)"
related: []
status: ""
rank:
spec_id: "orphan-scheme-up"
structureVersion: 1
---

# orphan-scheme-up — VIOLATION

Gated MOC whose `up:` target carries a URI scheme (`mailto:`). `up:` must be a
relative `[]()` link, so a schemed target (mailto:, tel:, …) is a violation even
though it has no `://`.

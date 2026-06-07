---
up: "[parent](../../specid.md)"
related: []
status: ""
rank:
spec_id: "013a1"
structureVersion: 1
---

# 013a — VIOLATION (013a vs 013a1) near-miss

`spec_id: 013a1` normalizes to `(spec,013a1)` but the directory `013a` normalizes
to `(spec,013a)`. The number-suffix is compared as an opaque whole segment, so
`013a1` is never truncated to `013a` -> NO MATCH -> VIOLATION (the near-miss case).

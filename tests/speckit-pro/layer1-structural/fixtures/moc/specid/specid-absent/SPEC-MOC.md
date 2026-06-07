---
up: "[parent](../../specid.md)"
related: []
status: ""
rank:
structureVersion: 1
---

# specid-absent — VIOLATION (no join key)

A version-gated marker with NO `spec_id` field at all. A marker with no join key
cannot satisfy the directory join -> VIOLATION (distinct from a present-but-
mismatched value).

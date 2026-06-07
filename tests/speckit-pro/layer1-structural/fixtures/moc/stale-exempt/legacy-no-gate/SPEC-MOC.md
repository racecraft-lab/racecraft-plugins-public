---
up: "[parent](does-not-exist.md)"
related: []
status: ""
rank:
spec_id: "legacy-no-gate"
---

# legacy-no-gate — EXEMPT (no version gate)

This marker carries NO `structureVersion`, so it is NOT version-gated. Its `up:`
deliberately dangles ([parent](does-not-exist.md) is absent), and a body link
also dangles: [missing](also-missing.md). Because the spec is not gated, the
stale-index lint MUST skip it BEFORE reading any body content — a grandfathered
legacy spec can never red-fail (exempt-before-content, FR-023 / SC-002).

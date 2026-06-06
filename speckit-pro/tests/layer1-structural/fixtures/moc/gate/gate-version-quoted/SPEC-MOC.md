---
up: "[parent](../../gate.md)"
related: []
status: ""
rank:
spec_id: "gate-version-quoted"
structureVersion: "1"
---

# gate-version-quoted — SKIP

A quoted `"1"` is NOT a bare integer. The gate fires only on an unambiguous bare
integer, so a quoted value is treated identically to absence -> skipped.

---
up: "[technical roadmap](broken-technical-roadmap.md)"
related: []
status: ""
rank:
spec_id: "BROKEN-ROADMAP"
structureVersion: 1
---

# broken — Roadmap Map of Content (malformed: no INDEX zone)

This home note IS version-gated (structureVersion: 1) but carries NONE of the three
GENERATED sentinel pairs — its INDEX zone is missing entirely. For a home-note
target the generator MUST fail safe (exit 2, no write, actionable stderr naming this
file): a gated home note without its INDEX zone is malformed, NOT a fresh spec-MOC
awaiting inject-if-missing. Sending it down inject-if-missing would wrongly add all
three zones and render PRS/BACKLINKS against docs/ai/specs/ (FR-017a).

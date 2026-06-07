---
up: "[parent](../../orphan.md)"
related: []
status: ""
rank:
spec_id: "orphan-non-moc-doc"
structureVersion: 1
---

# orphan-non-moc-doc — PASS

A gated spec whose MOC has a valid `up:`. The sibling non-MOC docs (`spec.md`,
`contracts/foo.md`) carry NO `up:` — the orphan lint must NOT require `up:` on
non-MOC docs, only on files named exactly `SPEC-MOC.md`.

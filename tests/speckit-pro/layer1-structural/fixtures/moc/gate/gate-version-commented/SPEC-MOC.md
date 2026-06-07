---
up: "[parent](../../gate.md)"
related: []
status: ""
rank:
spec_id: "gate-version-commented"
structureVersion: 1          # keep in sync with the lint scripts' hardcoded literal
---

# gate-version-commented — GATED (PASS)

`structureVersion: 1` carries a trailing inline `# ...` YAML comment, exactly as
the scaffold template stamps it (and as PRSG-002's own marker carries it). The
gate read MUST strip the inline comment, recognize the bare integer 1, and GATE
this spec. With a valid `up:` and a spec_id matching the directory, it then PASSES.
This is the positive case that guards against the inline-comment false-skip.

# Contract: MOC frontmatter join-key

The shared frontmatter contract that every MOC template carries and that downstream specs (PRSG-003 generated content, PRSG-004 roadmap-MOC home note) consume. Owned by FR-001 / FR-003 / FR-005 / FR-008.

## Fields

```yaml
---
up: "[parent](relative/path/to/parent.md)"   # relative []() link; NEVER a [[wikilink]]
related: []                                    # list of relative []() links (carried, unenforced in v1)
status: ""                                     # carried, unenforced in v1
rank:                                          # carried, unenforced in v1
spec_id: ""                                    # e.g., PRSG-002 — namespace-matches the containing directory
structureVersion: 1                            # integer; the version-gate marker (v1 = 1)
---
```

## v1 enforcement

| Field | Enforced in v1? | Enforcing lint | Rule |
|-------|-----------------|----------------|------|
| `up` | YES | orphan (presence + form) + stale-index (resolution) | present, non-empty, well-formed relative `[]()` link; target resolves |
| `structureVersion` | YES | both (as the gate) | integer; `>= 1` makes the spec subject to v1 lints; absence = exempt |
| `spec_id` | YES | spec_id check (FR-019) | normalize(`spec_id`) == normalize(containing directory) |
| `status` | NO (carried) | — | reserved for PRSG-003/004 |
| `rank` | NO (carried) | — | reserved for PRSG-003/004 |
| `related` | NO (carried) | — | reserved for PRSG-003/004; if present with relative links, those links are still resolved by stale-index |

## Two template shapes (both carry all six fields)

- **`roadmap-moc-template.md`** — roadmap-level map shape. Authored by maintainers; its instance filename convention is defined by PRSG-004.
- **`spec-moc-template.md`** — spec-level map shape. Consumed by `speckit-scaffold-spec` via token substitution (same mechanism as `workflow-template.md`) to write the minimal `SPEC-MOC.md`.

## Template location

`speckit-pro/skills/speckit-coach/templates/` (next to `workflow-template.md`). Single shared, runtime-agnostic copy each — NOT duplicated per runtime (Claude/Codex). No new preset; no project-local `.specify/templates/` copy.

## Minimal scaffold output (what `speckit-scaffold-spec` writes)

The scaffold writes a MINIMAL `SPEC-MOC.md` carrying at least the three load-bearing fields:

```yaml
---
up: "[roadmap](../../docs/ai/specs/<roadmap-filename>.md)"
spec_id: <SPEC-ID>          # e.g., PRSG-002
structureVersion: 1          # keep in sync with the lint scripts' hardcoded literal
---
```

- Written to `specs/<branch-name>/SPEC-MOC.md` (CONTRACT dir, branch-named), creating the directory if needed.
- Written on EVERY new spec at creation time, regardless of eventual slice count.
- `up:` points at the EXISTING `*-technical-roadmap.md` (so it resolves immediately). For PRSG-002's own marker: `../../docs/ai/specs/pr-size-governance-technical-roadmap.md`.
- The `structureVersion: 1` literal is stamped by the scaffold with a "keep in sync" comment; the same literal is hardcoded in the lint scripts. No shared version file.

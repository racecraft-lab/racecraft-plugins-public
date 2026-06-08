# Data Model: Roadmap-MOC home note

**N/A — no new persistent data entities, no schema, no storage.** This feature introduces
no database, no JSON manifest, and no new data format. Everything is a pure function of
existing committed Markdown files (their frontmatter + sentinel-bounded zones). This document
exists to satisfy the Phase-1 / G3 gate and to record the **document structures** the
generator reads and writes; it is not a data schema.

The home note's two zones (curated, generated) and the SPEC-MOC frontmatter fields are
documented as document structures below. The byte-level format of the generated zone is the
contract in [`contracts/roadmap-moc-index.md`](./contracts/roadmap-moc-index.md); the PRSG-002
frontmatter join-key contract and the PRSG-003 sentinel grammar remain authoritative and are
unchanged by this spec.

---

## Document structure: Roadmap-MOC home note

File at `docs/ai/specs/<slug>-roadmap-MOC.md`, emitted by `speckit-prd` from the PRSG-002
`roadmap-moc-template.md`.

| Part | Authored by | Edited by | Notes |
|------|-------------|-----------|-------|
| Frontmatter | `speckit-prd` (from template) | human | `up:` → `<slug>-technical-roadmap.md` (relative `[]()` link, never `[[wikilink]]`); carries the PRSG-002 join-key fields incl. `structureVersion: 1` (the gate) and `spec_id` (the roadmap identity) |
| Curated epics zone | `speckit-prd` (auto-scaffolded) | **human** (editable) | one epic per roadmap phase/tier; each epic: title, member spec links, one-line advisory "Why" placeholder. No-phases roadmap → single "Specs" epic + advisory. The generator NEVER touches this zone. |
| GENERATED INDEX zone | the generator (`render_index`) | **never hand-edited** (machine-regenerated) | sentinel-bounded; whole-zone regen; one row per gated spec `- [<spec_id>](rel) · <status>`, normalized-ID ascending. Only the INDEX sentinel pair is present (not PRS/BACKLINKS). |

**Reachability**: every in-scope spec is reachable from the home note via the curated zone
and/or the GENERATED INDEX (downward). Each spec's own `up:` is left untouched (still resolves
to the roadmap — PRSG-002 contract preserved, FR-008). The home note's `up:` and a reciprocal
roadmap → home-note link make the two top-level docs mutually reachable (FR-006).

---

## Read structure: SPEC-MOC frontmatter (per-spec source of INDEX row fields)

The INDEX renderer reads two fields per gated `specs/<dir>/SPEC-MOC.md` via the existing
total/safe accessor `moc_frontmatter_field` (no new parser):

| Field | Type | Used for | Empty/missing behavior |
|-------|------|----------|------------------------|
| `spec_id` | string | the row's visible link text; normalized via `moc_normalize` for ordering | a gated SPEC-MOC with absent/empty `spec_id` is **skipped from the INDEX** (no row) — `spec_id` is both link text and sort key, so a missing value cannot render a reachable row; NOT symmetric with empty `status` (FR-015a). No new validation is added here — the existing PRSG-002 `spec_id` lint remains the authority that flags the offending marker. |
| `status` | string | the row's at-a-glance status field after the `·` separator | **empty/missing → row still emitted** (link + blank status), never dropped (FR-015) |
| `structureVersion` | bare int ≥ 1 | the gate (`moc_is_gated`) — in-scope iff present | absent/quoted/decimal → SKIP (not indexed), consistent with existing gating (FR-016) |

These are **reads only** — this feature writes nothing into any SPEC-MOC. The SPEC-MOCs are
inputs; the home note's INDEX is the sole output zone.

---

## Validation rules (from requirements — all enforced by reuse, no new validator)

- **Gate**: in-scope iff `moc_is_gated` (bare-int `structureVersion ≥ 1`) — reused unchanged.
- **Ordering**: `moc_normalize(spec_id)` ascending — reused unchanged.
- **Link form**: relative `[]()` only, never `[[wikilink]]` (FR-014) — enforced by the row
  format in the contract + the L4 fixture.
- **Determinism**: identical committed inputs → byte-identical INDEX zone; second run =
  zero-byte diff (SC-004) — enforced by the L4 determinism fixture.
- **Byte-identical spec-MOC path**: the spec-MOC INDEX stays empty (SC-005) — enforced by the
  PRSG-003 contract fixtures re-run unchanged as the regression guard.

No state transitions. No relationships beyond "the home note indexes the gated SPEC-MOCs in
its repo's `specs/` tree."

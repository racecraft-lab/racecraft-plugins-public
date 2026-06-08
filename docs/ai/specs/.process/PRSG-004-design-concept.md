---
topic: "Roadmap-MOC home note from PRD + coach the two-zone structure"
slug: "prsg-004-roadmap-moc-home-note"
date: "2026-06-08"
mode: "setup"
spec_id: "PRSG-004"
source_input:
  type: "topic"
  ref: "PR-Size Governance technical roadmap — PRSG-004 catalog entry (docs/ai/specs/pr-size-governance-technical-roadmap.md)"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Roadmap-MOC home note from PRD + coach the two-zone structure

> **Source:** PRSG-004 catalog entry in `docs/ai/specs/pr-size-governance-technical-roadmap.md` (Phase 2, P2)
> **Date:** 2026-06-08
> **Questions asked:** 9
> **Stop reason:** natural (converged on a shared design concept before the soft cap; user chose wrap)

## Goals

- Make `speckit-prd` emit a **third artifact** — a roadmap-MOC "home note" at
  `docs/ai/specs/<slug>-roadmap-MOC.md` — alongside the PRD (`docs/prd-<slug>.md`) and the
  technical-roadmap (`docs/ai/specs/<slug>-technical-roadmap.md`) it already writes, so a
  project's whole spec tree is navigable from **one map**. Decomposition should add
  traceability, not cognitive load: navigate a map, don't memorize the tree.
- Give the home note **two zones**:
  - a **human-curated epics zone** — auto-derived as an editable scaffold from the roadmap's
    existing phase/tier grouping, with a one-line **advisory** "Why" per epic; and
  - a **sentinel-bounded GENERATED INDEX zone** — one row per spec:
    `- [<spec_id>](rel/SPEC-MOC.md) · <status>`, normalized-ID ascending, both fields read
    from each SPEC-MOC's PRSG-002 frontmatter.
- Produce the GENERATED INDEX by **activating the dormant `render_index()`** in PRSG-003's
  `generate-spec-index.sh` and teaching its `main()` to also process the home note —
  keeping the per-spec-MOC code path **byte-identical** so PRSG-003's pinned contracts stay green.
- Have `speckit-coach` **teach** the curated/generated two-zone split and the
  "cap epics below ~10" guardrail.
- Keep emission **cheap**: zero new questions in the `speckit-prd` interview; the curated zone
  is auto-scaffolded for the human to edit, not interviewed for.

## Non-goals

- **No backfill of existing/legacy roadmaps** — new-roadmaps-only; PRSG-011 Tier-0 owns
  navigation backfill (answered in Q7). This repo's own PRSG roadmap gets its home note from
  PRSG-011, not here.
- **No change to spec-MOC `up:` , scaffold-spec, or the spec-MOC template** — those are
  PRSG-002 territory; the home note is a *downward* index + curated layer, not the tree root
  (Q9). The PRSG-002 `up:` contract stays untouched.
- **No hard block / CI lint on epic count** — the cap is advisory only (Q6).
- **No new `generate-roadmap-moc.sh` and no `lib/moc-zones.sh` extraction refactor** — extend
  the existing generator (Q3).
- **No table/dashboard rendering and no H1-parsing in the INDEX** — link + status only (Q4).
- **No injection of generated sentinels into the prose technical-roadmap** — the home note is a
  separate file (Q1).

## Design Tree (Q&A log)

### Q1. Where does the roadmap-MOC "home note" live — a separate file, or two zones injected into the existing technical-roadmap?

**Branch:** Artifact topology / blast radius

**Recommended answer:** Separate home-note file.
> PRSG-002 already ships a standalone `roadmap-moc-template.md` with its own frontmatter
> join-key contract, and PRSG-003's generator targets a dedicated MOC file. A purpose-built file
> keeps the sentinel-bounded GENERATED zone's blast radius contained — whole-zone regen never
> touches authored roadmap prose. The template existing and explicitly deferring its instance
> filename to PRSG-004 is the strongest signal of the intended design.

**Alternatives offered:**
- Inject zones into the technical-roadmap (it's "~80% a MOC already"): fewer files, but mixes
  generated sentinels into heavily human-authored prose (clobber risk) and strands the existing template.
- Both — home note that transcludes/links the roadmap: more moving parts and link-maintenance for a ~200 LOC spec; over-built for v1.

**User's answer:** Separate home-note file (Recommended).

---

### Q2. What is the instance filename + location convention for the roadmap-MOC home note that speckit-prd emits?

**Branch:** Filename/location convention (explicitly deferred to PRSG-004 by the PRSG-002 template)

**Recommended answer:** `docs/ai/specs/<slug>-roadmap-MOC.md`.
> Co-located sibling of the `<slug>-technical-roadmap.md` it indexes and the PRD that spawned it
> — parallel naming, one neighborhood, discoverable. Downstream already reads `docs/ai/specs/`;
> this makes it the third file there. The GENERATED INDEX emits relative
> `../../../specs/<dir>/SPEC-MOC.md` links into the repo-root `specs/` tree the generator scans.

**Alternatives offered:**
- Repo-root `<slug>-roadmap-MOC.md` / `ROADMAP.md`: most prominent as a literal "home", but detaches it from the PRD/roadmap neighborhood and adds root clutter; longer relative links both directions.
- `specs/<slug>-roadmap-MOC.md`: shortest links to the SPEC-MOCs it indexes, but `specs/` is the per-feature tree — a roadmap-level note there is a layering mismatch.

**User's answer:** `docs/ai/specs/<slug>-roadmap-MOC.md` (Recommended).

---

### Q3. How should the home note's generated INDEX zone be produced — by extending PRSG-003's generate-spec-index.sh, or a new generate-roadmap-moc.sh?

**Branch:** Generator strategy / scripts-first determinism

**Recommended answer:** Extend `generate-spec-index.sh`; activate `render_index()`.
> PRSG-003 left `render_index()` as a dormant stub explicitly reserved for this spec
> (lines 116–123, with a NON-GOAL guard against creating the home note), and the sentinel
> framing, ID-normalization, whole-zone regen, and atomic-write are already built and tested.
> Activate it for the roadmap-MOC and add home-note discovery to `main()`, keeping the spec-MOC
> path byte-identical so PRSG-003's contracts stay green. Smallest net-new LOC; one shared
> runtime-agnostic script; one L4 surface. Squarely the scripts-first mandate and the test
> table's "(or reuse 003)".

**Alternatives offered:**
- New `generate-roadmap-moc.sh` sourcing the shared libs: zero regression risk to PRSG-003's pinned script, clean roadmap-vs-spec separation; costs duplicated sentinel constants/framing and a second script to keep in sync — more LOC against budget.
- Extract `lib/moc-zones.sh`, both consume it: cleanest long-term, but the most refactoring of the tested PRSG-003 script — highest regression surface, likely over budget.

**User's answer:** Extend generate-spec-index.sh; activate render_index (Recommended).

**Implementation guardrail (carried forward):** PRSG-003's byte-for-byte contracts live in
`specs/prsg-003-spec-index/contracts/`. The spec-MOC code path MUST remain byte-identical;
re-run PRSG-003's L4 fixtures unchanged as a regression guard. The roadmap-MOC INDEX is an
**additive** code path with its own L4 fixture/contract.

---

### Q4. What does each row of the home note's GENERATED INDEX zone contain (render_index's output)?

**Branch:** INDEX determinism contract

**Recommended answer:** `- [<spec_id>](rel/SPEC-MOC.md) · <status>`.
> `spec_id` and `status` both come from each SPEC-MOC's PRSG-002 frontmatter (already carried by
> the join-key contract) via the existing `moc-frontmatter` lib — a pure function of committed
> files, fully deterministic, no H1 parsing. Status is the one high-value at-a-glance signal;
> normalized-ID ascending order; whole-zone regen prevents staleness. Separator is the same
> U+00B7 middle dot the PRS renderer uses.

**Alternatives offered:**
- Link only (`- [<spec_id>](rel/SPEC-MOC.md)`): leanest, zero staleness, but status hides behind the click — the home note loses its main at-a-glance value.
- Table row (id | name | status | link): most scannable, but needs a human name source (H1 parse — fragility/determinism risk) and table logic; over-built for v1.

**User's answer:** Relative link + status (Recommended).

---

### Q5. How does speckit-prd populate the curated (human) epics zone of the home note?

**Branch:** Curated-zone population / interview cost

**Recommended answer:** Auto-derive an epic scaffold from the roadmap's phases + advisory "Why" placeholders.
> The technical-roadmap already groups specs into phases/tiers with a dependency graph — that
> grouping IS the epic structure. `prd` emits the curated zone pre-filled with those phase
> groupings + spec links and a one-line advisory "Why" per epic (locked decision: Why is
> advisory in v1) for the human to edit. Adds **zero** new `AskUserQuestion` steps and hands the
> human an editable start, not a blank page — honoring "authored once cheaply".

**Alternatives offered:**
- Add interview questions to name epics + write each Why: richer live curation, but grows the prd interview against the "cheaply" goal and re-asks the phase grouping the decomposition already produced.
- Empty curated zone + TODO marker: cheapest to build, but a blank zone is low-value and likely never filled — reintroduces the cognitive-load gap PRSG-004 exists to close.

**User's answer:** Auto-derive epic scaffold from phases + advisory Why placeholders (Recommended).

---

### Q6. How is the "cap epics below ~10" guardrail enforced?

**Branch:** Guardrail forcefulness / where it fires

**Recommended answer:** Advisory warn at `prd` emit-time + `coach` teaches it.
> When `prd` auto-derives the scaffold and the count exceeds ~10, it prints a one-line advisory
> ("11 epics — consider consolidating; >~10 strains navigability") but still writes the file;
> `coach` teaches the guideline. Matches v1's advisory ethos (Why annotations advisory,
> releasability detect-and-warn) and avoids re-introducing a blocking detective control — the
> exact anti-pattern PRSG-006/010 are dismantling.

**Alternatives offered:**
- Hard block / CI lint when epics > 10: actually enforces the cap, but epic count is a judgment heuristic not a structural invariant — brittle, fights the advisory stance, recreates a gate.
- Coach-only (teach, no runtime check): simplest, but the guidance is invisible at the moment it matters (emit time).

**User's answer:** Advisory warn at prd emit-time + coach teaches it (Recommended).

---

### Q7. Does PRSG-004 backfill home notes onto existing roadmaps, or only emit for new ones?

**Branch:** Scope boundary vs PRSG-011 (retro-migration)

**Recommended answer:** New-roadmaps-only; backfill is PRSG-011's job.
> `speckit-prd` emits the home note only when it authors a fresh PRD+roadmap. The cross-cutting
> constraint is explicit: PRSG-001–010 ship new-specs-only, and PRSG-011 Tier-0 owns navigation
> backfill for historical roadmaps (reusing this same generator). Honors the sequencing boundary
> and holds the ~200 LOC budget. Consequence: this repo's own PRSG roadmap gets its home note
> from PRSG-011, not here; the **L3 eval demos emission on a new fixture roadmap**, not this repo.

**Alternatives offered:**
- Also backfill existing roadmaps now: the activated generator can regen an INDEX once the file exists, but creating the home-note *file* for a legacy roadmap is precisely PRSG-011 Tier-0 — duplicates that work and breaks the new-specs-only boundary the whole roadmap depends on.

**User's answer:** New-roadmaps-only; backfill is PRSG-011's job (Recommended).

---

### Q8. Given Q3 activates deterministic generator code, should PRSG-004 add Layer-4 (deviating from the roadmap's L1/L2/L3/L8 table)?

**Branch:** Test coverage / deviation from the authoritative table

**Recommended answer:** Add L4 — final set **L1, L2, L3, L4, L8**.
> The authoritative table's "L1,L2,L3,L8" assumed skill-prompt-only changes; Q3 instead extends a
> deterministic script (`render_index`), and the scripts-first mandate is explicit: new
> deterministic logic gets a Layer-4 determinism fixture (same committed SPEC-MOCs → byte-identical
> INDEX zone). Recorded as a **deliberate deviation** from the roadmap table, to be noted in spec.md.

**Alternatives offered:**
- Keep L1/L2/L3/L8; fold the generator check into L1/L3: stays literally aligned to the table, but a byte-identical determinism guarantee is an L4 concern — folding it into the L3 AI eval loses the deterministic fixture and weakens regression protection on the generator.

**User's answer:** Add L4 — final set L1, L2, L3, L4, L8 (Recommended).

---

### Q9. Should PRSG-004 repoint each new SPEC-MOC's `up:` to the home note, or leave it and make the home note a downward index layer?

**Branch:** Navigation-spine completeness vs scope creep into PRSG-002

**Recommended answer:** Leave `up:` as-is; home note is the downward index + curated epics, cross-linked with the roadmap.
> Keeps PRSG-004 surgical — only `prd` + `coach` + the generator, no drift into PRSG-002's
> spec-MOC template or scaffold-spec. The home note reaches every spec via its curated zone +
> GENERATED INDEX (down); each spec's `up:` still resolves to the roadmap; the home note and
> roadmap cross-link so both top docs are mutually reachable. Every spec stays reachable from the
> home, and the PRSG-002 `up:` contract is preserved untouched.

**Alternatives offered:**
- Repoint new SPEC-MOCs' `up:` to the home note: fully bidirectional spine with the roadmap as a peer doc, but edits the spec-MOC template + scaffold-spec token substitution (PRSG-002 territory, outside PRSG-004's file set) — scope creep coupling two specs and risking the PRSG-002 lints/contracts.
- Repoint, but move the change into a PRSG-002 follow-up / PRSG-011: bidirectional spine while keeping PRSG-004 clean, but adds a cross-spec dependency and leaves the spine one-directional until that lands.

**User's answer:** Leave up: as-is; home note is the downward index, cross-linked with the roadmap (Recommended).

## Open Questions

Deferred with a recommended default applied (low-impact "how" details; resolve in Specify/Plan/Tasks):

- **Generator home-note discovery mechanism.**
  - **Default:** the extended `main()` discovers the home note by filename glob
    `docs/ai/specs/*-roadmap-MOC.md`, gated on the PRSG-002 frontmatter contract being present
    (`moc_is_gated` + `structureVersion`), mirroring how the spec-MOC path is version-gated.
  - **Why deferred:** it's a generator-internal "how" with an obvious default; affects the L4
    fixture shape. **Suggested next step:** lock during `/speckit-plan`.

- **coach teaching location.**
  - **Default:** new `references/` section (a dedicated two-zone guide or a section in an existing
    coach reference), not inline in `SKILL.md`, to keep the skill body lean.
  - **Why deferred:** doc-structure choice, no behavioral impact. **Suggested next step:** resolve in `/speckit-tasks`.

- **Home note's own `up:` value.**
  - **Default:** points at the technical-roadmap (`<slug>-technical-roadmap.md`), making the two
    top-level docs mutually linked (the roadmap side of the cross-link is a one-line link added by `prd`).
  - **Why deferred:** trivial frontmatter value. **Suggested next step:** confirm in `/speckit-specify`.

- **No-phases fallback for the curated scaffold.**
  - **Default:** if the roadmap has no phase grouping (flat catalog), emit a single "Specs" epic
    containing all specs + an advisory note suggesting the author group them.
  - **Why deferred:** edge case. **Suggested next step:** resolve in `/speckit-plan`.

- **Codex parity (constraint, not truly open).**
  - The emit prose (US1) goes in BOTH `skills/speckit-prd/SKILL.md` and
    `codex-skills/speckit-prd/SKILL.md`; the teach prose (US2) in BOTH `speckit-coach` mirrors.
    The generator stays a **single shared copy** referenced by path — never duplicated into
    `codex-skills/`. L8 parity fixtures + `validate-codex-skills.sh` (L1) must stay green.
    `speckit-skill-reviewer` runs as a pre-commit gate. The Codex `speckit-prd` uses a free-text
    Q&A loop instead of `AskUserQuestion`, but the home-note emission is post-interview
    file-writing (runtime-agnostic), so both mirrors get the identical emit step.

## Recommended Next Step

*(Setup mode — this section is informational; scaffold has already created the worktree, branch,
and workflow file.)*

Review the design concept (this doc) and the populated workflow file, then run:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/PRSG-004-workflow.md
```

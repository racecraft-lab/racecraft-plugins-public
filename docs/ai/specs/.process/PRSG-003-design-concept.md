---
topic: "PRSG-003 — Generated index/PRs/backlinks + status integration + phase-gate regen"
slug: "prsg-003-spec-index"
date: "2026-06-06"
mode: "setup"
spec_id: "PRSG-003"
source_input:
  type: "topic"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-003 section)"
question_count: 11
stop_reason: "natural"
---

# Design Concept: PRSG-003 — Generated index/PRs/backlinks + status integration + phase-gate regen

> **Source:** docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-003 section, Phase 2, P1)
> **Date:** 2026-06-06
> **Questions asked:** 11
> **Stop reason:** natural (all high-uncertainty × high-impact branches resolved; well under the 30-question cap)

## Goals

- Build the **live engine** behind PRSG-002's static MOC layer: a deterministic generator, `generate-spec-index.sh`, that (re)generates sentinel-bounded blocks so the maps cannot **silently lie** (the #1 risk the spec names).
- **Close the loop PRSG-002 deferred.** PRSG-002 shipped MOC *shapes* and said "non-MOC docs become reachable via the MOC down-index once PRSG-003 lands." PRSG-003 generates that reachability index so every `spec.md` / `plan.md` / `tasks.md` / `contracts/**` / `.process/**` artifact is reachable from its spec-MOC.
- Define the three generated zones and their contract: **INDEX** (roadmap → spec-MOCs), **PRS** (slice → PR# → merged SHA), **BACKLINKS** (a spec's own-artifact reachability index).
- **Wire the engine into the workflow safely**: `speckit-status` invokes it in **read-only check mode** (regenerate in memory, diff, report staleness) so its read-only contract is preserved; the **autopilot** is the authoritative **write path**, regenerating and committing at phase boundaries.
- Stay **deterministic and fixture-tested**: pure function of committed repo files, reusing the canonical `moc-id-normalize.sh` join; **whole-zone regen, never `sed`-patch**; byte-stable ordering.
- Land within budget (~350 LOC, `bash`+`jq`) with mandatory Codex parity for the mirrored skills it touches.

## Non-goals

- **The roadmap-MOC home note and its populated roadmap-level INDEX** — built and fixture-tested here but **dormant** in this repo until PRSG-004 creates the home note carrying the INDEX sentinels (Q1, Q2 of PRSG-002's boundary).
- **Live population of slice → PR# → merged SHA** — the generator *renders* the PRS zone from repo-local committed data; *who writes* that data when a slice merges is PRSG-009's multi-PR emission (Q3).
- **Backfilling / injecting zones into legacy specs that have no `SPEC-MOC.md`** — those are skipped (version-gating's "no marker → exempt"); their migration is PRSG-011 (Q7, Q10).
- **An inbound cross-spec citation graph** (reverse `related:` / `depends-on` links) — `related:` is unenforced/empty in v1, so it's deferred, not built (Q6).
- **Linking the cross-tree roadmap-level `docs/ai/specs/.process/` exhaust** (design-concept, workflow) from the spec-MOC — that exhaust is roadmap-scoped and owned by the roadmap-MOC / PRSG-004 (Q11).
- **`speckit-status` writing any file** — it stays strictly read-only (Q2). No product code of any kind; this is a plugin-skill + shared-script change.

## Design Tree (Q&A log)

### Q1. PRSG-003 builds the index generator, but the roadmap-MOC home note it would populate is PRSG-004's deliverable and doesn't exist yet. What should PRSG-003 actually generate-and-wire in v1 without overlapping PRSG-004?

**Branch:** Scope boundary (PRSG-003 ↔ PRSG-004)

**Recommended answer:** Sentinel-driven engine; spec-MOC zones live now, roadmap index dormant.
> The generator regenerates any `<!-- GENERATED:* -->` zone in any file. It activates the down-index + backlinks zones in the spec-MOC template and existing spec-MOCs now (closing PRSG-002's deferred "non-MOC docs reachable" loop). The roadmap-level INDEX is fully built, fixture-tested, and wired into status/autopilot, but no-ops in this repo until PRSG-004 supplies the home note carrying the INDEX sentinels. Zero overlap, immediate spec-level value.

**Alternatives offered:**
- Generate the roadmap INDEX into the existing `*-technical-roadmap.md` now: dogfoods at roadmap level immediately, but risks double-owning the roadmap-index location with PRSG-004 and a later migration.
- Pull the roadmap-MOC home note forward into PRSG-003: most complete, but directly overlaps PRSG-004 and breaks the phase boundary.

**User's answer:** Sentinel-driven engine; spec-MOC zones live now, roadmap index dormant (Recommended).

---

### Q2. `speckit-status` is documented as strictly read-only ("never creates files"), yet PRSG-003 says it "invokes the generator (it IS the index generator)." How should `speckit-status` relate to the generator?

**Branch:** Wiring / contract integrity (status × generator)

**Recommended answer:** Read-only check mode: regenerate in memory, diff, report staleness.
> `speckit-status` calls the generator with `--check`: it regenerates into memory and diffs against the committed file. If drifted, the dashboard reports "index stale — run regen" but writes nothing. Honors the read-only contract AND catches the silent-stale-index failure (the #1 risk). The authoritative write path is the autopilot phase-gate.

**Alternatives offered:**
- status writes the index in place: single clear owner, simplest wiring, but breaks the documented read-only guarantee and could surprise anyone running status expecting zero mutations.
- status only displays the committed index, never invokes the generator: cleanest read-only, but a stale index renders as truth when status runs outside an autopilot cycle — exactly the failure mode targeted.

**User's answer:** Read-only check mode: regenerate in memory, diff, report staleness (Recommended).

---

### Q3. The GENERATED PRS zone maps slice → PR# → merged SHA, but the spec requires the generator be deterministic and fixture-tested. Where does that PR/SHA data come from?

**Branch:** Data source / determinism (PRS zone)

**Recommended answer:** Repo-local committed source only — never live `gh` at generation time.
> The generator is a pure function of committed repo files (a small `.process/` PR manifest and/or git merge metadata), so identical inputs always render the identical zone — deterministic, offline, fixture-testable. WHO writes slice → PR# → SHA when a slice merges is PRSG-009's multi-PR emission; PRSG-003 ships the renderer + zone format + fixture, and in this pre-009 repo the zone renders from whatever seed data exists (often empty).

**Alternatives offered:**
- Live `gh` API at generation time: always current, but non-deterministic, needs network + auth, and directly breaks the determinism/fixture requirement and offline CI.
- Derive purely from `git log` (parse merge commits): deterministic and offline, but parsing PR# from squash commit subjects is brittle and couples the format to commit-message conventions.

**User's answer:** Repo-local committed source only — never live `gh` at generation time (Recommended).

---

### Q4. What exact sentinel format should bound the generated zones, given the rule "always regenerate the whole zone, never sed-patch"?

**Branch:** Zone contract / parse mechanics

**Recommended answer:** Three independent HTML-comment START/END pairs, content fully replaced.
> `<!-- GENERATED:INDEX:START (do not edit) -->` … `<!-- GENERATED:INDEX:END -->`, plus `:PRS:` and `:BACKLINKS:` pairs. Markers defined once as generator constants; regen replaces everything between each pair verbatim; a file missing a pair simply skips that zone. Invisible in rendered Markdown, greppable, independently positionable, and matches the spec's "sentinel comments" language.

**Alternatives offered:**
- Custom fenced-block / heading-delimited sentinels: more human-visible, but more fragile to parse and can render awkwardly.
- One combined GENERATED block holding all three sub-sections: simpler one-zone parse, but couples placement — the three sections can't be positioned independently.

**User's answer:** Three independent HTML-comment START/END pairs, content fully replaced (Recommended).

---

### Q5. How should the autopilot run the regeneration phase-gate step — at which phase boundaries, and with what commit behavior?

**Branch:** Wiring (autopilot write path)

**Recommended answer:** Idempotent regen at every phase boundary; commit only on non-empty diff.
> Because whole-zone regen is deterministic, re-running when nothing changed produces zero diff and commits nothing. Running it at each gate is therefore cheap and maximally staleness-proof, with no phase allow-list to drift. The autopilot folds the regenerated files into its existing checkpoint commit only when `git diff` is non-empty, with a fixed message. The autopilot is the authoritative write path (status is read-only check, per Q2).

**Alternatives offered:**
- Regen only at phases that can change the index (allow-list): fewer runs, but the allow-list can drift out of sync with what actually mutates the index, risking a missed regen.
- Regen once at the end (pre-PR): simplest, but a status check taken mid-workflow between phases would see a stale index — partially reintroducing the failure mode.

**User's answer:** Idempotent regen at every phase boundary; commit only on non-empty diff (Recommended).

---

### Q6. What should the GENERATED BACKLINKS zone contain in v1 (the zone that's active now, since the roadmap INDEX is dormant until PRSG-004)?

**Branch:** Behavior / zone semantics (BACKLINKS)

**Recommended answer:** Per spec-MOC: a generated reachability index of that spec's own artifacts.
> Each spec-MOC gets a generated zone enumerating the spec's artifacts as relative links — `spec.md`, `plan.md`, `tasks.md`, `contracts/**`, `checklists/**`, and `.process/**` exhaust — making every non-MOC doc reachable from the MOC. This is exactly the loop PRSG-002 deferred to PRSG-003, and the data (files on disk) exists now, so it renders real content immediately. Minimal surface.

**Alternatives offered:**
- Inbound cross-spec references (citation graph): richer navigation, but `related:` is unenforced and empty in v1, so it renders empty now and only pays off for future specs.
- Both artifact reachability AND inbound cross-spec references: most complete graph, but the cross-spec half has no data yet — adds code for data that doesn't exist (against the repo's "simplest change" rule).

**User's answer:** Per spec-MOC: a generated reachability index of that spec's own artifacts (Recommended).

---

### Q7. How should the generator discover which specs to (re)generate zones for, and how should it treat legacy specs that have no `SPEC-MOC.md` yet?

**Branch:** Discovery scope / version-gating

**Recommended answer:** Only specs that have a `SPEC-MOC.md`; skip un-migrated legacy specs.
> Discover spec-MOCs by the PRSG-002 filename convention and regenerate each one's zones from artifacts in its tree. Legacy specs lacking a SPEC-MOC are skipped — backfilling them is PRSG-011's job. Consistent with version-gating's "no marker → exempt" contract, and keeps PRSG-003 from reaching into un-migrated specs.

**Alternatives offered:**
- All spec directories, MOC or not: maximal coverage now, but it would create MOCs/zones inside un-migrated specs — overlapping PRSG-011 and breaking the "no marker → exempt" rule that keeps legacy CI green.
- Only the current in-flight spec: smallest blast radius, but the repo-wide index can never be complete and status's repo-wide staleness check becomes meaningless.

**User's answer:** Only specs that have a `SPEC-MOC.md`; skip un-migrated legacy specs (Recommended).

---

### Q8. What ordering rule makes the generated zones byte-stable across machines (the requirement that lets the fixture test pass)?

**Branch:** Determinism (ordering)

**Recommended answer:** Canonical: normalized-ID order across specs; fixed artifact precedence within a spec.
> Cross-spec lists sort by `moc_normalize`'s `(namespace, number-suffix)` key ascending. Within one spec's reachability index, use a fixed artifact precedence (`spec.md` → `plan.md` → `tasks.md` → `data-model` → `research` → `contracts/**` → `checklists/**` → `.process/**`) then lexicographic path. Stable, human-sensible, and independent of `find`/glob enumeration order.

**Alternatives offered:**
- Pure lexicographic by file path everywhere: deterministic, but interleaves PRSG-/SPEC- namespaces oddly and buries canonical artifacts among alphabetical noise.
- By frontmatter `rank`, then ID: honors the carried `rank`, but it's unenforced and usually empty in v1, so ordering is undefined until populated.

**User's answer:** Canonical: normalized-ID order across specs; fixed artifact precedence within a spec (Recommended).

---

### Q9. Where should the single shared `generate-spec-index.sh` live, given both `speckit-status` and `speckit-autopilot` (plus their Codex mirrors) invoke it?

**Branch:** File layout / Codex parity

**Recommended answer:** `speckit-autopilot/scripts/`, referenced by absolute plugin path from both.
> Co-locate with `reviewability-gate.sh`, which `speckit-scaffold-spec` and `speckit-status` already reference cross-skill by absolute path. The autopilot owns the authoritative write path, so the tool living there matches ownership. Single runtime-agnostic copy — Codex SKILL.md mirrors point at the same file (no script duplication); only SKILL.md prose is mirrored to `codex-skills/{speckit-status,speckit-autopilot}`.

**Alternatives offered:**
- `speckit-status/scripts/`: matches the scope wording ("status IS the generator"), but puts the write tool under the read-only skill and inverts ownership.
- A new plugin-level shared dir (`speckit-pro/scripts/`): clean "shared" home, but that dir holds repo-ops scripts (release/marketplace), not installed plugin-runtime scripts — introduces a new convention.

**User's answer:** `speckit-autopilot/scripts/`, referenced by absolute plugin path from both (Recommended).

---

### Q10. PRSG-002 spec-MOC skeletons have no GENERATED sentinel zones, and the generator skips files that lack them. How do the zones get into spec-MOCs so the reachability index actually renders?

**Branch:** Migration / zone seeding

**Recommended answer:** Template gains empty zones (new specs born with them) + generator injects-if-missing into existing version-marked spec-MOCs.
> Update `spec-moc-template.md` so new specs are born with empty GENERATED zones at a fixed anchor, AND have the generator idempotently inject the zones into any existing version-marked spec-MOC that lacks them, then fill them. Both new and PRSG-002-era spec-MOCs (incl. `prsg-002` and `prsg-003` itself) get the index now — real dogfooding. Injection is bounded to version-marked specs (per Q7).

**Alternatives offered:**
- Template-only; existing spec-MOCs left until PRSG-011 migrates them: smallest change, but the repo's current spec-MOCs render no index now — weak dogfooding, only the fixture exercises the generator.
- Generator inject-if-missing only, no template change: simpler template, but a brand-new spec has a window with no zones until the generator first runs, and the contract isn't documented in the template.

**User's answer:** Template gains empty zones + generator injects-if-missing into existing version-marked spec-MOCs (Recommended).

---

### Q11. Which files should the per-spec reachability index enumerate — only the spec's own contract directory tree, or also the roadmap-level `.process/` design-concept and workflow files?

**Branch:** Enumeration boundary

**Recommended answer:** Only the spec's own tree: `specs/<branch>/**` including its `.process/`.
> Single-tree enumeration — relative links stay short and stable, no cross-tree ID-matching. The roadmap-level `docs/ai/specs/.process/` design-concept + workflow are roadmap-scoped exhaust owned by the roadmap-MOC (PRSG-004), not the spec-MOC. Simplest and cleanly separated.

**Alternatives offered:**
- Spec's tree PLUS the matching roadmap-level `.process/` design-concept + workflow: more complete per-spec exhaust reachability, but couples the generator to a second tree and an ID-normalized match there, partially overlapping the roadmap-MOC domain that PRSG-004 owns.

**User's answer:** Only the spec's own tree: `specs/<branch>/**` including its `.process/` (Recommended).

---

## Open Questions

None block implementation. Deferred by design (not undecided):

- **What:** The exact shape of the repo-local committed source for slice → PR# → SHA (a dedicated `.process/` manifest vs. data carried in the spec-MOC body).
  **Why deferred:** The *renderer* + zone format is PRSG-003's job; the *writer/population* is PRSG-009. PRSG-003 only needs a deterministic input contract it can fixture-test.
  **Suggested next step:** Pin the minimal input contract during `/speckit-plan`; finalize the writer in PRSG-009.

- **What:** When/whether the roadmap-level INDEX zone activates against a real roadmap-MOC home note.
  **Why deferred:** The home note is PRSG-004's deliverable; PRSG-003's INDEX path is built and fixture-tested but dormant here.
  **Suggested next step:** PRSG-004 creates the home note with INDEX sentinels; no PRSG-003 change needed for it to start filling them.

- **What:** Fixed commit message wording for the autopilot's commit-on-diff regen step.
  **Why deferred:** Cosmetic; resolve during `/speckit-plan` against the existing checkpoint-commit convention.
  **Suggested next step:** Decide in Plan; verify it reads cleanly in a public squash subject (CLAUDE.md PR-title rules).

## Recommended Next Step

*(Setup mode — informational; the scaffold has already created the worktree and is about to populate the workflow file.)*

Populate `PRSG-003-workflow.md` from this design concept, commit both artifacts on `prsg-003-spec-index`, mark PRSG-003 In Progress in the roadmap, then run:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/PRSG-003-workflow.md
```

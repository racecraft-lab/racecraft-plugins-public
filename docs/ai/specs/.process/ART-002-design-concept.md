---
topic: "Draft-PR template set: four planning-review templates as branded single-file SPAs"
slug: "art-002-design-concept"
date: "2026-08-10"
mode: "setup"
spec_id: "ART-002"
source_input:
  type: "topic"
  ref: "ART-002 scope description from docs/ai/specs/html-artifacts-technical-roadmap.md"
question_count: 10
stop_reason: "natural"
---

# Design Concept: ART-002 Draft-PR Template Set

> **Source:** ART-002 scope in `docs/ai/specs/html-artifacts-technical-roadmap.md`
> **Date:** 2026-08-10
> **Questions asked:** 10
> **Stop reason:** natural (no critical open branches remained)

## Goals

- Port the four planning-review templates (upstream 16, 14, 01, 04) as
  Racecraft-branded single-file SPAs under
  `speckit-pro/artifact-gallery/templates/`, each satisfying the SPA contract:
  both canonical blocks embedded byte-for-byte, upstream attribution header,
  no prohibited constructs, status flipped `planned` → `shipped`.
- Define the gallery's fill-region convention: paired HTML comment markers
  `<!-- FILL:<slot>:START -->` … `<!-- FILL:<slot>:END -->` (Q1), documented by
  an in-file header comment slot inventory per template (Q2), shipped with
  representative fictional sample content inside every slot (Q3).
- Give implementation-plan and module-map an inline per-item objection field
  whose export walks non-empty notes with their phase/module anchors (Q4);
  give code-approaches a radio-group approach chooser plus one reason field
  (Q5); spec-explainer stays read-only per its manifest entry.
- Add a Layer 4 fill-region test: a hardcoded roadmap-named slot floor per
  template plus a both-ways doc/body agreement check between the header
  inventory and the body's marker pairs (Q7).
- **Split into 2 vertical slices, delivered as two sequential PRs (Q9, Q10):**
  slice 1 = the two always-routed templates (implementation-plan,
  spec-explainer) + their manifest status flips + their test coverage;
  slice 2 = the two conditional templates (code-approaches, module-map) +
  theirs. Slice 2 branches after slice 1 merges. ART-002 remains one spec;
  the autopilot's split-PR emission handles the routing.

## Non-goals

- Generation/authoring logic that populates the fill regions — that is ART-007
  (stated in the roadmap scope; reaffirmed throughout).
- Editing any shared foundation file: `brand-kit.css`, `theme-toggle.html`,
  `SPA-CONTRACT.md`, the signal vocabulary, or other manifest entries. A port
  flips its own entries' `status` and nothing else (SPA contract; Q2 rejected
  extending SPA-CONTRACT.md).
- Vendoring upstream template files into the repository — upstream sources are
  fetched read-only at implement time and only branded derivatives are
  committed (Q8).
- A dedicated acceptance-harness page — manual browser checks are recorded as
  standard UAT runbook steps instead (Q9, UAT record).
- Automated browser testing — plugin tests stay Python-stdlib-only; the
  file:// render/console check stays manual (roadmap verification clause).

## Design Tree (Q&A log)

### Q1. How should each template mark its fill regions (the slots an ART-007 authoring agent later populates from spec.md / plan.md / tasks.md)?

**Branch:** Fill-region mechanism

**Recommended answer:** Paired HTML comments
> `<!-- FILL:<slot>:START -->` … `<!-- FILL:<slot>:END -->` matches the
> gallery's existing validated marker-pair convention (BRAND-KIT,
> GALLERY-HEAD), so the Layer 4 test reuses the once-and-ordered pair checks
> via stdlib `HTMLParser` comment handling, and ART-007 fills by replacing a
> delimited text region. No prior fill-region convention existed in the repo;
> this decision defines it.

**Alternatives offered:**
- `data-fill` attributes: element-anchored and CSS-selectable, but a second
  slot convention beside the marker-pair one, and the filler must rewrite
  element internals.
- `<template>`/`<slot>` elements: platform mechanism for runtime shadow-DOM
  composition; ART-007 writes static HTML, so the machinery would be unused.

**User's answer:** Paired HTML comments (Recommended)

---

### Q2. Where should the fill-region documentation live (the slot inventory: each slot's name, what fills it, and which source artifact it comes from)?

**Branch:** Fill-region documentation

**Recommended answer:** In-file header comment
> Each template documents its own slots in a comment block near the
> attribution header. The artifact stays self-describing, ships to the install
> cache where ART-007 reads it, and touches no shared foundation file (the SPA
> contract says a port edits nothing shared).

**Alternatives offered:**
- New `FILL-REGIONS.md` in the gallery: central, but adds a shared foundation
  file ports are kept away from, and it can drift from the templates.
- Extend `SPA-CONTRACT.md`: rejected by the contract itself — a port edits no
  shared foundation file.

**User's answer:** In-file header comment (Recommended)

---

### Q3. What content should ship inside the fill regions of the four gallery templates?

**Branch:** Sample content

**Recommended answer:** Representative sample content
> Each slot ships filled with a small, clearly-fictional worked example,
> upstream-template style. The gallery stays browsable (a reader judges fit by
> looking), and the manual file:// UAT render check exercises real layout.
> ART-007 replaces the whole delimited region anyway.

**Alternatives offered:**
- Empty slots with placeholder labels: cleaner fill diffs, but hollow gallery
  rendering and a layout check against no content.
- Sample in complex slots only: splits the convention two ways for little gain.

**User's answer:** Representative sample content (Recommended)

---

### Q4. How should the reader record objections in implementation-plan and module-map (the two templates whose exports carry objections tied to a phase or module)?

**Branch:** Objection-capture UI (FR-028 exports)

**Recommended answer:** Inline per-item note field
> Each phase/module row carries a keyboard-reachable "Add objection"
> disclosure revealing a labeled textarea; the export walks non-empty notes
> with their item anchors. Inline anchoring is the review-tool norm
> (GitHub-style inline comments), and it makes the objection-to-item tie
> structural instead of asking the reader to name the phase in prose. The SPA
> contract's export obligations (live-state derivation, keyboard operability,
> text success feedback, clipboard fallback to a selectable field) apply.

**Alternatives offered:**
- Single composer + item selector: less DOM, but context-switch away from the
  item and silent mis-attachment on a mis-selected dropdown.
- Flag + shared notes box: simplest markup, weakest tie; export cannot
  attribute prose to items reliably.

**User's answer:** Inline per-item note field (Recommended)

---

### Q5. How should the reader pick the winning approach in code-approaches (whose export carries the chosen approach and the reason)?

**Branch:** Choice-capture UI (FR-028 exports)

**Recommended answer:** Radio group + reason field
> One radio per approach column plus a single labeled "Why this one" textarea.
> Radios are the native accessible single-choice control (state exposed for
> free), and the export reads selection + reason from live state; with nothing
> selected the export explains instead of inventing a choice (the contract
> forbids exporting a conclusion the reader did not reach).

**Alternatives offered:**
- "Choose this" button per column: visually direct, but selected-state must be
  hand-exposed (aria-pressed, focus handling).
- Dropdown chooser: compact, but detaches the choice from the side-by-side
  comparison the template exists to show.

**User's answer:** Radio group + reason field (Recommended)

---

### Q6. How should the two diagram surfaces be built (implementation-plan's data-flow diagram, module-map's boxes-and-arrows with hot path)?

**Branch:** Diagram mechanism

**Recommended answer:** Keep upstream's mechanism
> Port whatever each upstream template already uses (SVG or HTML/CSS),
> restyled with brand tokens. Lowest-risk for a port and preserves layouts
> already proven in the upstream gallery. Recommended at moderate confidence —
> the upstream files had not been opened at question time.

**Alternatives offered:**
- Standardize on inline SVG: sharp and self-contained, but coordinate math
  makes the slot harder for ART-007's agent to refill.
- Standardize on HTML/CSS boxes: easiest to regenerate from plan.md structure,
  but crossing arrows get awkward in pure CSS.

**User's answer:** Keep upstream's mechanism (Recommended)

---

### Q7. What should the new Layer 4 fill-region test assert about each template's slots?

**Branch:** Verification design

**Recommended answer:** Floor + doc/body agreement
> Hardcode the roadmap-named required slots per template as a literal floor
> (no circularity), and additionally assert the in-file header inventory
> matches the body's marker pairs both ways. ART-007 reads that header
> inventory, so doc/body drift would mislead the authoring agent, and the
> agreement check is cheap.

**Alternatives offered:**
- Hardcoded floor only: simplest, but the header inventory ART-007 consumes
  can silently drift from the actual markers.
- Self-describing only: no list to maintain, but expectations derived from the
  file under test prove only self-consistency.

**User's answer:** Floor + doc/body agreement (Recommended)

---

### Q8. How should the implement phase obtain the four upstream source templates?

**Branch:** Upstream sourcing

**Recommended answer:** Fetch at implement time
> The implement executor fetches each upstream file read-only from GitHub as
> porting reference, authors the branded derivative, and commits only the
> derivative. Keeps vendored upstream content out of the repo per the editing
> boundaries. All four files were verified present in
> `anthropics/html-effectiveness` (default branch `main`) via `gh api` during
> the interview: `01-exploration-code-approaches.html`,
> `04-code-understanding.html`, `14-research-feature-explainer.html`,
> `16-implementation-plan.html`.

**Alternatives offered:**
- Pre-fetch during scaffold: no mid-run network dependency, but staleness risk
  and copies near the worktree risk accidental commit.
- Operator-provided clone: most control, one more manual step for no added
  safety over a read-only fetch.

**User's answer:** Fetch at implement time (Recommended)

---

### Q9. How should the manual file:// render and console check be recorded?

**Branch:** UAT evidence

**Recommended answer:** Standard UAT runbook
> The scaffold/PR flow already generates a UAT runbook under the spec's
> `.process/` directory; the manual checks become numbered runbook steps per
> template: file:// open, console clean, theme toggle, export controls,
> keyboard reachability. The operator executes them at UAT time, matching the
> ART-001 precedent of recorded manual scenarios.

**Alternatives offered:**
- PR-body verification note only: lighter, but no per-step record.
- Dedicated acceptance harness page: nice ergonomics, but extra authored
  scaffolding the runbook already covers.

**User's answer:** Standard UAT runbook (Recommended)

---

### Q10. The advisory size estimator returned warn (estimated 560 LOC against its fixed 400 ceiling, suggested 2 slices), while the roadmap projects 380 reviewable LOC and the net-new gate allows warn 600 / block 1200. Split ART-002 or keep it as one slice?

**Branch:** Slice sizing (estimator: `{"estimated_loc": 560, "suggested_slices": 2, "status": "warn"}` from inputs user_stories=4, files=7, frs=12, net_new=true)

**Recommended answer:** Split into 2 vertical slices
> Estimator's suggestion: slice 1 = the two always-routed templates
> (implementation-plan, spec-explainer) + their manifest flips + test floor;
> slice 2 = the two conditional templates (code-approaches, module-map) +
> theirs. Each slice is end-to-end and independently reviewable.

**Alternatives offered:**
- Keep as one slice: the roadmap recorded one vertical slice at a projected
  380 reviewable LOC, all net-new (greenfield warn 600); the estimator is
  advisory and has no greenfield discount.
- Different split: e.g. templates-with-exports vs the read-only spec-explainer.

**User's answer:** Split into 2 vertical slices (Recommended)

**Notes:** Follow-up route question (asked as Q10b): the slices land as **two
sequential PRs** — slice 1 merges first; slice 2 branches after it. Rejected
alternatives: one navigable PR (whole 560-LOC estimate in one diff), stacked
PRs (known stacked-branch sync friction in this repo).

## Open Questions

- **What:** Exact slot names for each template's fill regions (kebab-case
  identifiers, e.g. `phases`, `data-flow`, `risk-register`).
  **Why deferred:** Naming falls out naturally once the upstream files are
  read during Specify/Plan; the convention (kebab-case, filename-safe, same
  character rules as manifest ids) is already decided.
  **Suggested next step:** Fix the slot inventory per template in
  `/speckit-plan`; the Layer 4 test floor pins the roadmap-named ones.
- **What:** Whether the upstream diagram mechanisms (Q6) survive branding
  cleanly or one needs re-authoring.
  **Why deferred:** Upstream files not yet opened; decision was to keep the
  upstream mechanism at moderate confidence.
  **Suggested next step:** Confirm during Plan after fetching the upstream
  files; escalate to a Clarify session only if a mechanism conflicts with the
  SPA contract's prohibited constructs.

## Recommended Next Step

Setup mode — scaffolding has already happened. The calling
`/speckit-pro:speckit-scaffold-spec` run writes the workflow file next; then
run `/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-002-workflow.md`.

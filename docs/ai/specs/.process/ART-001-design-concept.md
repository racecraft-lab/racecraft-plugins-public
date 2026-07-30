---
topic: "Artifact brand kit & gallery foundation"
slug: "art-001-brand-kit-gallery-foundation"
date: "2026-07-28"
mode: "setup"
spec_id: "ART-001"
source_input:
  type: "topic"
  ref: "ART-001 scope from docs/ai/specs/html-artifacts-technical-roadmap.md"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Artifact Brand Kit & Gallery Foundation

> **Source:** ART-001 scope, `docs/ai/specs/html-artifacts-technical-roadmap.md`
> **Date:** 2026-07-28
> **Questions asked:** 9
> **Stop reason:** natural (all branches converged)

## Goals

- Ship the platform-neutral foundation every gallery artifact consumes, as one
  net-new spec: `speckit-pro/artifact-gallery/` with `brand-kit.css`,
  `brand-voice.md`, `manifest.json`, `SPA-CONTRACT.md`, `theme-toggle.html`,
  plus the Layer 4 test `tests/speckit-pro/unit/test-artifact-gallery.py`
  registered in `suite-manifest.json`.
- Seed `manifest.json` with **all ~21 template rows now** (Q1): every row
  carries id, category, title, when-to-use, stage
  (`draft-pr`|`final-pr`|`ad-hoc`), trigger, source attribution, and a
  `status` field (`planned` → `shipped`); port specs (ART-002…005) flip
  status as each template lands. The scanner only file-checks `shipped` rows.
- Triggers are **closed signal tags** (Q2): `{"always": true}` or
  `{"any_of": ["<signal>", …]}` against a closed vocabulary; the Layer 4 test
  rejects unknown signals. No expression DSL, no prose-only routing.
- The external-reference scanner forbids **resource loads only** (Q3):
  script/img/iframe `src`, `srcset`, stylesheet/preconnect `link href`, CSS
  `url()` and `@import`, fetch/XHR/WebSocket literals — with
  `fonts.googleapis.com` + `fonts.gstatic.com` allowlisted. Navigation
  anchors and URLs in comments/visible text stay legal (provenance and
  attribution links survive).
- Brand tokens are consumed via a **verified marker block** (Q4):
  `brand-kit.css` carries `BRAND-KIT:START/END`; templates embed the block
  verbatim in their `<style>`; the Layer 4 test byte-compares each gallery
  file's embedded block against the canonical file. Template-specific styling
  lives outside the block.
- Dark mode is **system default + toggle** (Q5): `color-scheme: light dark`,
  GTO90 dark tokens via `prefers-color-scheme` with `:root[data-theme]`
  override, inline toggle persisting to localStorage (try/catch so `file://`
  quirks degrade to session-only). AA contrast audited per theme
  independently.
- The toggle ships as a **markered, drift-checked snippet file** (Q8):
  `theme-toggle.html` with `THEME-TOGGLE:START/END`, byte-compared by the
  same Layer 4 mechanism as the CSS block.
- Cross-repo brand drift is managed by **pinned provenance + manual re-sync**
  (Q6): the provenance header records source repo, commit SHA, and date;
  re-sync is a deliberate human edit. No automated cross-repo or docs-site
  overlap check.
- `brand-voice.md` distills the **artifact-relevant subset** of racecraft
  `.claude/rules/content.md` (Q7): voice & tone, banned/preferred vocabulary,
  answer-first TL;DR structure, CTA/button rules. Website-only rules
  (Schema.org, FAQ minimums, nav chrome) are omitted.
- **Kept as one spec** (Q9): estimator projects 435 LOC (`warn`,
  suggested_slices 2), accepted under the PRD's 1.5× greenfield allowance
  (warn at 600) for net-new-only slices — mostly declarative CSS custom
  properties and JSON rows.

## Non-goals

- Any template port — ART-002…005 (roadmap scope; reaffirmed in Q1: ports
  become mechanical row-flips).
- Workflow wiring — ART-006…011 (roadmap scope).
- Automated cross-repo drift checking against the private racecraft repo, and
  the docs-site palette overlap test — answered in Q6 (Token drift).
- A boolean trigger-expression DSL or evaluator — answered in Q2 (Trigger
  form; KISS/YAGNI).
- Banning navigation anchors or text/comment URLs — answered in Q3 (Scanner
  scope).
- Schema.org JSON-LD, FAQ minimums, and website nav chrome in the voice
  sheet — answered in Q7 (Voice sheet).
- Embedded woff2 fonts — roadmap key decision (Google Fonts `<link>` is the
  sole permitted external reference).

## Design Tree (Q&A log)

### Q1. Should ART-001 seed the manifest with all ~21 template rows up front (marked planned until each port spec ships its file), or ship only the schema plus an exemplar row and let each port spec (ART-002…005) add its own rows?

**Branch:** Manifest seeding

**Recommended answer:** Seed all rows now
> All row data (id, category, title, when-to-use, stage, trigger) is already
> known from the PRD crosswalk — it's pure data. A `status` field
> (`planned` → `shipped`) lets the scanner file-check only shipped rows,
> port specs become mechanical row-flips, and ART-007's routing design gets
> the complete catalog from day one. This also resolves the roadmap tension
> between ART-001's "rows for every template" and ART-002/003's "adds
> four/three routing rows" (they flip status, not author rows).

**Alternatives offered:**
- Schema + exemplar only: rows land atomically with their templates, but
  ART-007 waits on port specs for real data and each port re-litigates row
  authoring.
- Seed rows, no status field: simpler schema, but the test can't distinguish
  "not yet ported" from "typo'd path".

**User's answer:** Seed all rows now

---

### Q2. What form should each manifest row's conditional trigger take for routing at draft-PR and final-PR time?

**Branch:** Trigger form

**Recommended answer:** Closed signal tags
> `trigger: {"always": true}` or `{"any_of": ["ui_change", …]}` against a
> closed vocabulary enumerated with the manifest shape and validated by the
> Layer 4 test. Deterministic enough to test, light enough for v1 — no
> interpreter machinery (constitution KISS/YAGNI). The artifact-author agent
> maps spec context to signals.

**Alternatives offered:**
- Prose when-to-use only: zero machinery but untestable; the manifest stops
  being a contract.
- Boolean expression DSL: most deterministic, but builds evaluator machinery
  no v1 caller needs.

**User's answer:** Closed signal tags

---

### Q3. What should the external-reference scanner actually forbid in gallery HTML files?

**Branch:** Scanner scope / SPA contract

**Recommended answer:** Resource loads only
> Flag external URLs only in resource-loading positions (script/img/iframe
> `src`, `srcset`, stylesheet/preconnect `link href`, CSS `url()`/`@import`,
> fetch/XHR/WebSocket literals), with the two Google Fonts hosts allowlisted.
> Navigation anchors and comment/text URLs stay legal so provenance headers
> and source-attribution links survive. Matches the contract's intent:
> render over `file://` with nothing fetched but fonts.

**Alternatives offered:**
- Any URL substring: zero parsing but bans provenance/attribution links —
  guaranteed false positives.
- Loads + external nav: fully hermetic but kills attribution links already
  committed to in the manifest design.

**User's answer:** Resource loads only

---

### Q4. How should the 21 single-file templates consume brand-kit.css while staying self-contained, and how is token drift caught?

**Branch:** Kit consumption / drift

**Recommended answer:** Verified marker block
> `brand-kit.css` is canonical and carries `BRAND-KIT:START/END` markers;
> every template embeds the block verbatim inside its own `<style>`. The
> Layer 4 test extracts each gallery file's embedded block and byte-compares
> it to the canonical one — drift is a deterministic failure, updates are a
> mechanical re-sync, template-specific styling lives outside the block, and
> no build step is introduced.

**Alternatives offered:**
- Copy freely, no check: zero machinery, silent divergence across 21 files —
  the drift the PRD's OQ-3 worried about.
- Stdlib sync script: convenient at scale but new repo tooling the
  constitution makes you justify; agents already re-inline the block.

**User's answer:** Verified marker block

---

### Q5. How should dark mode work in the brand kit and every gallery artifact?

**Branch:** Dark mode (UI/UX; research-backed)

**Recommended answer:** System default + toggle
> `color-scheme: light dark`; GTO90 dark tokens applied via
> `prefers-color-scheme` with a `:root[data-theme]` override and a small
> inline toggle persisting to localStorage (try/catch so `file://` quirks
> degrade to session-only). Grounded in current consensus (respect the OS
> signal by default, still offer user control — NN/g guidance echoed across
> 2025/2026 practice) and the docs-site's `data-theme` pattern. WCAG AA
> contrast applies to each theme independently, so both palettes are audited.

**Alternatives offered:**
- System preference only: no JS, but a dark-OS reviewer can't view the light
  rendering — weak for artifacts whose job is being reviewed.
- Light-only v1: smallest, but dark tokens already exist and dark-OS
  reviewers get a white-flash artifact.

**User's answer:** System default + toggle

---

### Q6. How should drift between the brand kit and its upstream sources (private racecraft repo brand docs, local docs-site brand.css) be managed?

**Branch:** Token drift (cross-repo)

**Recommended answer:** Pinned provenance, manual re-sync
> The provenance header records source repo, commit SHA, and date; re-sync is
> a deliberate human-initiated edit. CI on this public repo can't read the
> private racecraft repo, and docs-site's Starlight variables aren't meant to
> stay name-identical. The Q4 marker-block test already stops the drift that
> multiplies (kit ↔ 21 templates).

**Alternatives offered:**
- Add docs-site overlap check: catches one more seam but couples gallery
  tests to docs-site restyles.
- Vendor brand docs into repo: removes the pointer but risks leaking
  private-repo prose into a public repo; double maintenance.

**User's answer:** Pinned provenance, manual re-sync

---

### Q7. What should the public brand-voice.md cheat-sheet distill from the private content.md?

**Branch:** Brand voice

**Recommended answer:** Artifact-relevant subset
> Voice & tone (professional-conversational, active voice, real tech names,
> document failures equally), banned/preferred vocabulary, answer-first
> TL;DR structure, CTA/button rules (action labels, sentence case, one
> primary per section). Omits website-only rules — Schema.org JSON-LD, FAQ
> minimums, nav chrome — which don't apply to local review artifacts and
> would mislead the artifact-author agent. (Source fetched and reviewed from
> racecraft `.claude/rules/content.md` during the interview.)

**Alternatives offered:**
- Full distillation: closest to upstream but bakes website SEO obligations
  into artifacts; every upstream change becomes a re-sync obligation.
- Fold into SPA-CONTRACT: one less file but loses the single citable voice
  source the roadmap's Key Files already names.

**User's answer:** Artifact-relevant subset

---

### Q8. Where does the canonical dark-mode toggle snippet (button markup + script) live, and is it drift-checked like the CSS token block?

**Branch:** Toggle packaging

**Recommended answer:** Markered snippet file, drift-checked
> Ship `speckit-pro/artifact-gallery/theme-toggle.html` carrying a
> `THEME-TOGGLE:START/END` block (button markup + inline script with
> localStorage persistence). Templates embed it verbatim; the same Layer 4
> byte-compare that guards the CSS block guards this one. Symmetric with Q4,
> keeps JS out of a `.css` file, one canonical copy.

**Alternatives offered:**
- Example in SPA-CONTRACT only: one less shipped file but 21 unchecked
  copies of behavior-bearing JS — the drift class Q4 just closed.
- Defer toggle to ART-002: keeps ART-001 minimal but the toggle becomes
  template-owned with no canonical source.

**User's answer:** Markered snippet file, drift-checked

---

### Q9. Post-interview, the estimator projects 435 reviewable LOC (warn threshold 400, suggested split: 2). Keep ART-001 as one spec or split it?

**Branch:** Slice sizing

**Recommended answer:** Keep as one spec
> ART-001 is net-new-only seed/config — the class the PRD decision granted
> the 1.5× greenfield allowance (warn at 600), and 435 sits well under it.
> Still one thin vertical slice (tokens → manifest → test); most LOC is
> declarative CSS custom properties and JSON rows. Matches the ART-004/005
> precedent of accepting greenfield warns. Estimator inputs:
> user_stories=3, files=6, frs=8, new → `{estimated_loc: 435,
> suggested_slices: 2, status: "warn"}`.

**Alternatives offered:**
- Split 2 (kit vs manifest): honors the estimator but slice B's test imports
  slice A's marker blocks — not Independent (INVEST); doubles downstream
  merge waits.
- Trim scope (drop seeded rows): ducks under 400 but re-opens the
  row-authoring burden Q1 closed.

**User's answer:** Keep as one spec

## Open Questions

- **What:** The final closed signal vocabulary for manifest triggers
  (e.g. `ui_change`, `schema_change`, `api_change`, `incident`, …).
  **Why deferred:** the vocabulary should be derived from the 20 upstream
  templates' when-to-use semantics in one pass, which is plan-phase work.
  **Suggested next step:** derive during `/speckit-plan`; validate coverage
  in `/speckit-analyze` against all 21 seeded rows.
- **What:** Field-level manifest shape finalization (exact key names,
  `schema_version` field, category enum) and where the shape is documented
  (recommendation: a "Manifest" section in `SPA-CONTRACT.md`, since JSON has
  no comments; enforced by the Layer 4 test — no formal JSON Schema document,
  which stdlib can't validate anyway).
  **Why deferred:** mechanical detail with a clear recommendation; not worth
  an interview turn.
  **Suggested next step:** finalize during `/speckit-plan`.

## Implementation notes (constraints surfaced during the interview)

- Unit test filename must follow the repo's dash convention:
  `tests/speckit-pro/unit/test-artifact-gallery.py` (the roadmap's
  `test_artifact_gallery.py` spelling auto-conforms; every existing unit test
  is dash-named).
- `speckit-pro/artifact-gallery/` is inside the shipped plugin payload — the
  generated-artifact contract applies (payload/proof regeneration must be
  accounted before the work is called done).
- The provenance header cites the private racecraft repo by name + commit SHA
  only; no private prose is copied beyond the Q7-approved voice subset.
- Space Grotesk, Geist, and Fira Code are all served by Google Fonts; load
  via `<link>` with `font-display: swap` and system fallbacks (roadmap key
  decision, reaffirmed).

## Recommended Next Step

Setup mode — `/speckit-pro:speckit-scaffold-spec ART-001` is already running;
this doc feeds the workflow file's Specify/Clarify/Plan prompts. After
scaffold completes, run
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-001-workflow.md`.

# HTML Artifacts & Staged Review Workflow Implementation Roadmap

**Refactor the SpecKit-Pro scaffold and autopilot skills into a staged,
human-checkpointed workflow: the plan stage ends at a draft PR carrying
Racecraft-branded, self-contained HTML artifacts the operator reviews before
implementation; the implement stage opens with a feedback sweep and closes by
flipping the PR to ready with a PR writeup and an interactive UAT walkthrough —
while porting all 20 upstream HTML-effectiveness templates into a branded,
routable artifact gallery.**

This document defines the **SPEC catalog** for the HTML Artifacts & Staged
Review Workflow effort. Each SPEC corresponds 1:1 to a Feature /
Acceptance-Criteria group in the source PRD (`AC-N.*`), preserving traceability
from PRD → roadmap → spec. Each specification is executed end-to-end through
the SpecKit workflow and is prepared for autopilot with
`/speckit-pro:speckit-scaffold-spec ART-NNN`, which reads this roadmap as its
input.

**Source PRD:** [../../prd-html-artifacts.md](../../prd-html-artifacts.md)
**Roadmap MOC:** [html-artifacts-roadmap-MOC.md](html-artifacts-roadmap-MOC.md)
**Spec ID prefix:** `ART-###`
**Status:** Active; dependency graph approved 2026-07-28; ART-001 is complete
and archived after PR #407 and its follow-up fix PR #409; ART-006 is complete
and archived after PR #422, which unblocks ART-007, ART-009, ART-011 and
ART-012; ART-002 through ART-005 are ready; ART-014 and ART-015 were opened from
ART-006 findings and are ready with no dependencies

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Dependency Graph](#dependency-graph)
3. [Progress Tracking](#progress-tracking)
4. [Specification Sections](#specification-sections)

---

## Roadmap Overview

The effort is decomposed into **13 specifications** across **6 dependency
tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | ART-001 | Brand kit, gallery manifest, single-file-SPA contract | Sequential foundation |
| **2** | ART-002, ART-003, ART-004, ART-005, ART-006 | Template gallery ports ∥ autopilot staging | Parallel after ART-001 (ART-006 has no template dependency and may start immediately) |
| **3** | ART-007 | Draft-PR emission (plan-stage terminal step) | Sequential (needs ART-002 + ART-006) |
| **4** | ART-008, ART-009, ART-011, ART-012 | Feedback sweep, UAT walkthrough, scaffold chain, notes capture | Parallel after ART-007 (ART-009/011/012 only need ART-006) |
| **5** | ART-010 | Final-PR writeup, companions, ready flip | Sequential integration |
| **6** | ART-013 | Documentation | Sequential last |

**Execution Order:** ART-001 → (ART-002 ∥ ART-003 ∥ ART-004 ∥ ART-005 ∥
ART-006) → ART-007 → (ART-008 ∥ ART-009 ∥ ART-011 ∥ ART-012) → ART-010 →
ART-013

**Dependency Constraints:**

- ART-002…005 require ART-001 (brand kit + manifest schema).
- ART-006 depends on nothing and can start in parallel with ART-001.
- ART-007 requires ART-002 (draft-PR templates) and ART-006 (plan stage).
- ART-008 requires ART-007 (a draft PR must exist to sweep).
- ART-009 requires ART-001 (brand kit) and ART-006 (post-impl stage hook).
- ART-010 requires ART-003 (final-PR templates), ART-007 (the draft PR it
  flips), and ART-012 (implementation notes it embeds).
- ART-011 requires ART-006 (the plan stage it chains into).
- ART-012 requires ART-006 (implement-stage dispatch it extends).
- ART-013 requires everything (documents shipped behavior).

## Reviewability Contract

Every spec must fit a human review budget before setup and again before PR
creation. The size metric counts **production code only** — documentation,
tests, and config do not contribute to the reviewable-LOC count.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files. Touching more than one primary surface is also a warning, not a block.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless this roadmap records a typed exception pragma (below).
- A slice that adds only net-new files (no existing files modified) gets a 1.5x
  greenfield allowance on the production-LOC thresholds (warn 600, block 1200).
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- A block-sized slice may be allowed only by a typed, auditable exception
  pragma on its own line, exactly: `Reviewability-Exception: <class>` where
  `<class>` is one of `refactor`, `infra`, or `upgrade`. The match is
  line-anchored and case-sensitive with no trailing content; an unknown class,
  a mis-cased class, or free-form prose is not honored (fail-closed). Replace
  `<class>` with a real class when claiming an exception — the literal
  `<class>` placeholder is deliberately not a valid class.
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

---

## Dependency Graph

```text
ART-001 (Brand Kit & Gallery Foundation)
    │
    ├──► ART-002 (Draft-PR Template Set) ─────────────┐
    ├──► ART-003 (Final-PR Template Set) ────────────────────────────┐
    ├──► ART-004 (Gallery: Design & Prototyping)      │              │
    ├──► ART-005 (Gallery: Knowledge/Reports/Editors) │              │
    └──► ART-009 (UAT Walkthrough) ◄──┐               │              │
                                      │               ▼              │
ART-006 (Autopilot Staging) ──────────┼────────► ART-007 (Draft-PR   │
    │         │                       │           Emission)          │
    │         └──► ART-011 (Scaffold  │               │              │
    │              Integration)       │               ├──► ART-008   │
    └──► ART-012 (Impl-Notes ─────────┘               │  (Feedback   │
             Capture)                                 │    Sweep)    │
              │                                       ▼              ▼
              └────────────────────────────► ART-010 (Final-PR Writeup,
                                              Companions & Ready Flip)
                                                      │
                                             ART-013 (Documentation)
                                                      │
                                          ─── FEATURE COMPLETE ───
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| ART-001 | Artifact Brand Kit & Gallery Foundation | ✅ Complete / Archived | [.process/ART-001-workflow.md](.process/ART-001-workflow.md) | PR #407 merged with follow-up fix PR #409; the brand kit, gallery manifest, SPA contract, and validator live outside `specs/**`. T026 and T027 ran on 2026-07-29, 12 of 12 manual scenarios passed; the harness is preserved at [.process/ART-001-acceptance-harness.html](.process/ART-001-acceptance-harness.html) |
| ART-002 | Draft-PR Template Set | 🔄 In Progress | [.process/ART-002-workflow.md](.process/ART-002-workflow.md) | Scaffolded 2026-08-10 on `art-002-draft-pr-template-set`; grill-me split: 2 vertical slices as two sequential PRs (always-routed templates first) |
| ART-003 | Final-PR Template Set | ⏳ Ready | - | ART-001 dependency satisfied by PR #407 |
| ART-004 | Gallery Completion: Design & Prototyping | ⏳ Ready | - | ART-001 dependency satisfied by PR #407 |
| ART-005 | Gallery Completion: Knowledge, Reports & Editors | ⏳ Ready | - | ART-001 dependency satisfied by PR #407 |
| ART-006 | Autopilot Staging | ✅ Complete / Archived | [.process/ART-006-workflow.md](.process/ART-006-workflow.md) | PR #422; archived 2026-08-09; re-audited and re-grilled 2026-08-03. Declared budget 382 reviewable LOC, one slice. `gh` corroboration deferred to ART-007 (see Scope). **Prerequisite discharged** — PRs #416/#417 shipped in speckit-pro 2.22.0, so durable stage state now has a reliable store; ready for autopilot from Phase 1 |
| ART-007 | Draft-PR Emission | ⏳ Pending | - | Blocked by ART-002; ART-006 dependency satisfied by PR #422 |
| ART-008 | Feedback Sweep | ⏳ Pending | - | Blocked by ART-007 |
| ART-009 | UAT Walkthrough Replacement | ⏳ Ready | - | ART-006 dependency satisfied by PR #422 |
| ART-010 | Final-PR Writeup, Companions & Ready Flip | ⏳ Pending | - | Blocked by ART-003, ART-007, ART-012 |
| ART-011 | Scaffold Integration | ⏳ Ready | - | ART-006 dependency satisfied by PR #422 |
| ART-012 | Implementation-Notes Capture | 🔄 In Progress | [.process/ART-012-workflow.md](.process/ART-012-workflow.md) | Scaffolded 2026-08-10 on `art-012-implementation-notes-capture`; grill-me converged naturally, 8 questions, no split (scaffold estimator: 115 LOC, ok; re-estimated 155 at Clarify session 1, 162 at Analyze once FR-005 existed, then 190 on 2026-08-11 when the operator restored the literal per-task guarantee, adding FR-006 and a sixth production file — see the Reviewability Budget below) |
| ART-013 | Documentation | ⏳ Pending | - | Blocked by all |
| ART-014 | Phase-Guard Enforcement Repair | ⏳ Ready | - | No dependencies; found during ART-006, which deliberately did not fix it |
| ART-015 | Spec-Size Re-Estimation Trigger | ⏳ Ready | - | No dependencies; found during ART-006 — the estimator is sound but is never re-fed |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### ART-001: Artifact Brand Kit & Gallery Foundation

**Priority:** P1 | **Depends On:** None | **Enables:** ART-002…005, ART-009

**Goal:** Ship the platform-neutral foundation every artifact consumes: the
Racecraft brand kit, the gallery routing manifest schema, and the
single-file-SPA contract with its automated external-reference test.

**Reviewability Budget:** Primary surface: seed/config |
Projected reviewable LOC: 285 (estimator: ok) |
Production files: 3 |
Total files: ~8 |
Budget result: within budget

**Scope:**
- One vertical slice — brand tokens → manifest schema → validation test; Independent and Small (INVEST).
- `speckit-pro/artifact-gallery/brand-kit.css` (or equivalent inline-able
  block): CSS custom-property tokens for the 70-20-10 Racecraft palette
  (warm-neutral scale `#F7F6F4…#E0DED9`, brand red `#dc143c` punctuation-only,
  brand blue `#3c89c6` accents, GTO90 dark-mode set), typography stacks
  (Space Grotesk headings / Geist body / Fira Code mono via Google Fonts
  `<link>` URLs with the `display=swap` query parameter and system fallbacks),
  AA-contrast pairings,
  focus-ring and reduced-motion rules. Provenance header cites
  racecraft-lab/racecraft `docs/brand/*` (source commit recorded) and
  `docs-site/src/styles/brand.css`.
- Brand-voice cheat-sheet (markdown) distilled from racecraft
  `.claude/rules/content.md` for artifact copy (headings, TL;DR boxes, CTA
  labels).
- `speckit-pro/artifact-gallery/manifest.json`: schema + rows for every
  template — id, category, title, when-to-use, stage
  (`draft-pr`|`final-pr`|`ad-hoc`), conditional trigger expression, source
  template attribution.
- Single-file-SPA contract doc: all behavior/data inline;
  `fonts.googleapis.com`/`fonts.gstatic.com` the only permitted external
  references; must render over `file://` with no console errors.
- Repo test (Python 3.11+ stdlib, Layer 1 or 4) validating manifest shape and
  scanning every gallery HTML file for forbidden external references.

**Out of Scope:**
- Any actual template port (ART-002…005).
- Workflow wiring (ART-006…011).

**Verification:** Layer 4 unit tests for the manifest schema and the
external-reference scanner (`tests/speckit-pro/unit/test_artifact_gallery.py`),
registered in `tests/speckit-pro/suite-manifest.json`; Layer 1 structural pass
for the new shipped directory; payload/proof regeneration accounted.

**Key Decisions:**
**Branded derivatives, not pristine vendoring (2026-07-28):** the upstream
templates are re-skinned with Racecraft brand tokens and become repo-authored,
reviewable files with provenance headers; no parallel pristine vendored copy is
kept. Alternatives considered: verbatim vendored gallery + separate branded
layer (rejected: double maintenance for a static exemplar set).
**Google Fonts as sole external reference (2026-07-28):** `<link>` loading
works over `file://`; offline degrades to system stacks. Alternatives:
embedded woff2 (rejected: ~300KB per artifact), system-only (rejected: loses
brand typography online).

**Key Files:**
- `speckit-pro/artifact-gallery/brand-kit.css` — token block
- `speckit-pro/artifact-gallery/brand-voice.md` — voice cheat-sheet
- `speckit-pro/artifact-gallery/manifest.json` — routing manifest
- `speckit-pro/artifact-gallery/SPA-CONTRACT.md` — single-file constraints
- `tests/speckit-pro/unit/test_artifact_gallery.py` — manifest + external-ref test

---

### ART-002: Draft-PR Template Set

**Priority:** P1 | **Depends On:** ART-001 | **Enables:** ART-007

**Goal:** Port the four planning-review templates as branded single-file SPAs
with documented fill regions so the plan stage can populate them.

**Reviewability Budget:** Primary surface: docs/process (shipped templates) |
Projected reviewable LOC: 380 (estimator: ok) |
Production files: 4 (net-new) |
Total files: ~7 |
Budget result: within budget

**Scope:**
- One vertical slice — four templates → manifest rows → passing SPA checks; net-new only (INVEST: Small via greenfield).
- Branded derivatives of upstream 16 (implementation plan: phases, data-flow
  diagram, mockup slots, risk register, task inventory), 14 (feature/spec
  explainer: TL;DR, goals/non-goals, collapsible acceptance criteria, FAQ from
  clarify answers), 01 (code-approaches: side-by-side trade-off comparison),
  04 (module map: boxes-and-arrows with hot path highlighted).
- Documented fill regions per template (what an authoring agent populates from
  spec.md / plan.md / tasks.md / design concept).
- Manifest rows: implementation-plan + spec-explainer `draft-pr`/always;
  code-approaches `draft-pr`/conditional (competing approaches recorded);
  module-map `draft-pr`/conditional (brownfield).
- **Export affordances per ART-001 FR-028**, matching each entry's declared
  `exports`. Three of the four carry `["prompt", "markdown"]` and must implement
  both: `implementation-plan` and `module-map` export the reader's objections tied
  to the phase or module they attach to; `code-approaches` exports the chosen
  approach and the reason. `spec-explainer` is declared read-only (`[]`) and must
  carry none. This is the review checkpoint the staged workflow exists for, so an
  artifact here that strands the reader's conclusion in a browser tab defeats the
  stage.

**Out of Scope:**
- Generation/authoring logic (ART-007).

**Verification:** ART-001's gallery scanner covers all four templates
automatically; add a Layer 4 fill-region test (stdlib HTML parse asserting
each documented slot exists); Layer 1 + payload regeneration; manual `file://`
render/console check recorded as UAT evidence (browser checks stay manual —
plugin tests are Python-stdlib-only).

**Key Decisions:**
**Draft-PR artifact set (2026-07-28):** implementation plan + spec explainer
always; code-approaches + module map conditional — chosen in the PRD interview.

**Key Files:**
- `speckit-pro/artifact-gallery/templates/implementation-plan.html`
- `speckit-pro/artifact-gallery/templates/spec-explainer.html`
- `speckit-pro/artifact-gallery/templates/code-approaches.html`
- `speckit-pro/artifact-gallery/templates/module-map.html`
- `speckit-pro/artifact-gallery/manifest.json` — four routing rows

---

### ART-003: Final-PR Template Set

**Priority:** P1 | **Depends On:** ART-001 | **Enables:** ART-010

**Goal:** Port the three delivery templates as branded single-file SPAs ready
for the implement stage's post-implementation generation.

**Reviewability Budget:** Primary surface: docs/process (shipped templates) |
Projected reviewable LOC: 285 (estimator: ok) |
Production files: 3 (net-new) |
Total files: ~6 |
Budget result: within budget

**Scope:**
- One vertical slice — three templates → manifest rows → passing SPA checks (INVEST: Small, net-new).
- Branded derivatives of upstream 17 (PR writeup: motivation, before/after,
  file-by-file explanation, dedicated implementation-notes section slot), 03
  (annotated diff: unified diff with margin annotations, severity tags, jump
  links), 13 (flowchart: clickable operational-flow diagram).
- Manifest rows: pr-writeup `final-pr`/always; annotated-diff
  `final-pr`/conditional (self-review findings or large diff); flowchart
  `final-pr`/conditional (operational-flow change).
- **Export affordances per ART-001 FR-028**, matching each entry's declared
  `exports`. `pr-writeup` and `annotated-diff` carry `["prompt", "markdown"]`: the
  reviewer's questions and per-hunk objections, exportable either as a
  pull-request comment for the sweep to read or as an instruction to paste straight
  into a coding agent. `flowchart` is declared read-only (`[]`) and carries none.

**Out of Scope:**
- Generation logic and the ready flip (ART-010).
- The UAT walkthrough template (ART-009 — it is repo-authored, not an
  upstream port).

**Verification:** gallery scanner covers all three templates; Layer 4
fill-region test (including the implementation-notes slot); Layer 1 + payload
regeneration; manual `file://` render check as UAT evidence.

**Key Decisions:**
**Final-PR artifact set (2026-07-28):** writeup + UAT walkthrough always;
annotated diff + flowchart conditional — chosen in the PRD interview.

**Key Files:**
- `speckit-pro/artifact-gallery/templates/pr-writeup.html`
- `speckit-pro/artifact-gallery/templates/annotated-diff.html`
- `speckit-pro/artifact-gallery/templates/flowchart.html`
- `speckit-pro/artifact-gallery/manifest.json` — three routing rows

---

### ART-004: Gallery Completion — Design & Prototyping

**Priority:** P2 | **Depends On:** ART-001 | **Enables:** gallery completeness

**Goal:** Port the six design/prototyping templates so the full upstream
gallery is leverageable ad hoc.

**Reviewability Budget:** Primary surface: docs/process (shipped templates) |
Projected reviewable LOC: 480 (estimator: warn, suggested 2 slices) |
Production files: 6 (net-new) |
Total files: ~8 |
Budget result: warning accepted — net-new only, under the 1.5× greenfield
warn threshold (600); optional 3+3 split available if plan-time evidence
exceeds the estimate

**Scope:**
- One vertical slice of six sibling ports — no cross-file logic, each template
  independent (INVEST: Independent; greenfield allowance covers the batch).
- Branded derivatives of upstream 02 (visual-design directions), 05 (design
  system swatches/tokens), 06 (component variants sheet), 07 (animation
  prototype with parameter sliders), 08 (interaction prototype: linked
  screens), 10 (SVG illustration sheet).
- **Export affordances per ART-001 FR-028**, matching each entry's declared
  `exports`. Two of the six carry `["prompt", "markdown"]` and need **new**
  affordances, since upstream supplies none: `visual-designs` and
  `component-variants` are decision artifacts — the reader is choosing among
  directions or among states, and what must leave the page is the choice plus its
  reason, not a description of the screen. The other four — `design-system`,
  `animation-prototype`, `interaction-prototype`, `svg-illustrations` — are declared
  read-only (`[]`) and must carry none.
- Manifest rows: all `ad-hoc` with when-to-use guidance.

**Out of Scope:**
- Workflow-stage routing (none of these are stage-emitted).

**Verification:** gallery scanner + manifest-row coverage for all six
templates (Layer 4); Layer 1 + payload regeneration; interactive behavior
(sliders, linked screens) verified manually over `file://` as UAT evidence.

**Key Decisions:**
**Keep as one spec with recorded warn (2026-07-28):** interview decision — the
1.5× greenfield allowance covers 480; the per-spec reviewability gate forces a
split later only if reality outgrows the estimate.

**Key Files:**
- `speckit-pro/artifact-gallery/templates/visual-designs.html`
- `speckit-pro/artifact-gallery/templates/design-system.html`
- `speckit-pro/artifact-gallery/templates/component-variants.html`
- `speckit-pro/artifact-gallery/templates/animation-prototype.html`
- `speckit-pro/artifact-gallery/templates/interaction-prototype.html`
- `speckit-pro/artifact-gallery/templates/svg-illustrations.html`

---

### ART-005: Gallery Completion — Knowledge, Reports & Editors

**Priority:** P2 | **Depends On:** ART-001 | **Enables:** gallery completeness

**Goal:** Port the seven knowledge/report/editor templates — including the
three interactive editors with working export-back buttons — completing the
20-template gallery.

**Reviewability Budget:** Primary surface: docs/process (shipped templates) |
Projected reviewable LOC: 560 (estimator: warn, suggested 2 slices) |
Production files: 7 (net-new) |
Total files: ~9 |
Budget result: warning accepted — net-new only, under the 1.5× greenfield
warn threshold (600); optional 4+3 split available if plan-time evidence
exceeds the estimate

**Scope:**
- One vertical slice of seven sibling ports; editors keep functional
  copy-as-markdown/JSON export buttons (the feedback-loop pattern).
- **Export affordances per ART-001 FR-028**, matching each entry's declared
  `exports`. The three editors — `triage-board`, `feature-flags`, `prompt-tuner` —
  carry `["markdown"]`: their export is configuration data, not an instruction, so
  the upstream buttons already satisfy the obligation and need only re-labelling to
  the contract's wording ("Copy as Markdown", not "Export") plus the
  clipboard-failure fallback. The other four in this slice — `slide-deck`,
  `concept-explainer`, `status-report`, `incident-report` — are declared read-only
  (`[]`) and must carry none.
- Branded derivatives of upstream 09 (slide deck), 15 (concept explainer), 11
  (status report), 12 (incident report), 18 (triage board), 19 (feature-flag
  editor), 20 (prompt tuner).
- Manifest rows: all `ad-hoc` with when-to-use guidance.

**Out of Scope:**
- Workflow-stage routing.

**Verification:** gallery scanner + manifest-row coverage for all seven
templates (Layer 4); Layer 1 + payload regeneration; editor export-back
buttons verified manually over `file://` as UAT evidence (no browser
automation in the plugin suite).

**Key Decisions:**
**Keep as one spec with recorded warn (2026-07-28):** same rationale as
ART-004.

**Key Files:**
- `speckit-pro/artifact-gallery/templates/slide-deck.html`
- `speckit-pro/artifact-gallery/templates/concept-explainer.html`
- `speckit-pro/artifact-gallery/templates/status-report.html`
- `speckit-pro/artifact-gallery/templates/incident-report.html`
- `speckit-pro/artifact-gallery/templates/triage-board.html`
- `speckit-pro/artifact-gallery/templates/feature-flags.html`
- `speckit-pro/artifact-gallery/templates/prompt-tuner.html`

---

### ART-006: Autopilot Staging

**Priority:** P1 | **Depends On:** None | **Enables:** ART-007…012

**Goal:** Give autopilot first-class stages — `plan` (specify→analyze),
`implement` (implement→post-impl), `full` (legacy) — with auto-detection and
durable stage state, on both platforms.

**Reviewability Budget:** Primary surface: harness/adapter (skill files) |
Projected reviewable LOC: 217 (estimator: ok, modify-weighted) |
Production files: ~6 modified |
Total files: ~10 |
Budget result: within budget

**Scope:**
- One vertical slice — argv parsing → stage resolution → stage-bounded phase
  loop → durable state; behavior change only, gate semantics untouched.
- `--stage plan|implement|full` argv handling in both autopilot SKILL.md
  variants (`skills/` + `codex-skills/`); the phase loop bounds itself to the
  stage's phase subset.
- Auto-detect for bare invocations: workflow status table (phases 1–6
  complete). **Amended 2026-07-30 during scaffold:** the `gh` draft-PR
  corroboration limb is **deferred to ART-007**, which is the spec that creates
  the draft PRs it would corroborate against — during ART-006 no draft PR
  exists, so the branch has no live input and only its negative case is
  testable. ART-007 inherits the OQ-4 contract that the workflow file is
  authoritative and discrepancies are logged. Deferring this is also what keeps
  ART-006 a single slice: with the limb included the estimator returns 452 LOC
  and `suggested_slices: 2`; without it, 382 and one slice.
- Stage state recorded in the workflow file (workflow-file protocol update);
  `--from-phase` keeps resuming within a stage.
- Scaffold → autopilot chain contract documented (consumed by ART-011).
- Runner helper updates only where argv/stage resolution needs deterministic
  parsing (Python 3.11+ stdlib; no new Bash).

**Out of Scope:**
- Draft-PR creation (ART-007), feedback sweep (ART-008), scaffold-side chain
  (ART-011).

**Verification:** Layer 4 unit tests + golden fixtures for stage resolution
and workflow-file stage state; Layer 2 skill-trigger evals re-run for the
reworded autopilot description; Layer 1 frontmatter/structure; Codex parity
checks (validate-codex-skills / validate-codex-parity).

**Key Decisions:**
**Single execution engine (2026-07-28):** stages live in autopilot; scaffold
chains into the plan stage rather than growing its own phase loop.
Alternatives: scaffold-owned engine (rejected: duplicates consensus/gates),
third skill (rejected: third entry point, same duplication).
**Auto-detect default (2026-07-28):** bare invocation resolves the stage from
workflow state; explicit flags override. Alternatives: mandatory flag
(friction), legacy-default (hides the checkpoint).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — stage handling
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` — mirror
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — stage-bounded loop
- `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md` — stage state
- `speckit_pro_runner/helpers/` — stage resolution helper (if needed)

---

### ART-007: Draft-PR Emission

**Priority:** P1 | **Depends On:** ART-002, ART-006 | **Enables:** ART-008, ART-010

**Goal:** End the plan stage at a committed draft artifact set and an open
draft PR whose body indexes the artifacts, then stop for human review.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 217 (estimator: ok, modify-weighted) |
Production files: ~6 |
Total files: ~10 |
Budget result: within budget

**Scope:**
- One vertical slice — artifact generation → commit → draft PR → stop report.
- An artifact-author subagent (both platforms) that reads spec.md / plan.md /
  tasks.md / design concept, selects templates per manifest routing (always +
  conditional triggers), fills the fill-regions, and writes
  `specs/<branch>/artifacts/*.html`; fail-open (generation failure logs a gap,
  never blocks the draft PR).
- Draft-PR creation through the existing packet machinery in a draft mode:
  gate-valid conventional title, body carrying the Artifacts index table
  (artifact, purpose, copy-paste open command), `gh pr create --draft`.
- Plan-stage stop report: draft-PR URL, artifact index, resume instructions.
- Resolution of OQ-1 (draft PR vs marker-split multi-PR emission) during this
  spec's clarify phase.

**Out of Scope:**
- Reading feedback (ART-008); flipping to ready (ART-010).

**Verification:** Layer 4 golden fixtures for the draft-mode packet path
(including the fail-open artifact-generation branch); Layer 5 agent
verification for `artifact-author` on both platforms; Layer 1 + Codex parity
checks; payload regeneration.

**Key Decisions:**
**Commit + PR artifact index viewing (2026-07-28):** artifacts are committed
review-visible under `specs/<branch>/artifacts/` and opened locally over
`file://`; no hosting layer. Alternatives: third-party preview links
(public-repo only), GitHub Pages (infra-heavy) — both rejected for v1.

**Key Files:**
- `speckit-pro/agents/artifact-author.md` — new authoring subagent
- `speckit-pro/codex-agents/` mirror entry
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — plan-stage terminal step
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — packet draft mode
- `speckit_pro_runner/helpers/` — draft-packet support

---

### ART-008: Feedback Sweep

**Priority:** P1 | **Depends On:** ART-007 | **Enables:** trusted human checkpoint

**Goal:** Open the implement stage with a draft-PR feedback sweep that amends
planning artifacts through consensus and stops for re-review whenever it
changed anything.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 150 (estimator: ok, modify-weighted) |
Production files: ~4 |
Total files: ~7 |
Budget result: within budget

**Scope:**
- One vertical slice — read comments → classify → consensus-amend → regenerate
  → stop-or-proceed.
- `gh`-based read of unresolved draft-PR comments (including artifact-exported
  markdown blocks); zero unresolved feedback proceeds directly.
- The sweep reads the **`markdown`** export kind (ART-001 FR-028) — that is what a
  reader pastes into a pull-request comment, and its shape is what the
  comment-schema fixtures must parse. The **`prompt`** kind deliberately bypasses
  this sweep: a reader who pastes it into a coding agent has closed the loop without
  the round trip, and that is a supported path rather than a gap. The sweep therefore
  MUST NOT assume every artifact conclusion reaches it, and MUST NOT treat an absent
  comment as an absent opinion.
- Substantive items route through the existing category-routed consensus
  machinery to amend spec.md / plan.md / tasks.md; affected artifacts
  regenerate via the ART-007 author; commits pushed.
- Amendments → STOP with a re-review report; the operator re-runs autopilot
  when satisfied (loop converges on a clean sweep).
- Sweep decisions recorded as Consensus Resolution Log rows.

**Out of Scope:**
- Post-implementation review remediation (existing `/loop` machinery,
  unchanged).

**Verification:** Layer 4 fixtures for the feedback-comment schema parse and
the Consensus Resolution Log rows; the sweep's consensus routing is
prompt-level behavior with no automated eval, so end-to-end evidence lands in
the spec's UAT; Codex parity checks.

**Key Decisions:**
**Sweep + amend + re-review (2026-07-28):** amendments always stop for
re-review — the checkpoint's value is the human confirming plan changes.
Alternatives: continue-in-run (undercuts checkpoint), manual re-run
responsibility (feedback becomes decoration).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — implement-stage entry
- `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md` — sweep routing
- `speckit-pro/codex-skills/speckit-autopilot/` mirror

---

### ART-009: UAT Walkthrough Replacement

**Priority:** P1 | **Depends On:** ART-001, ART-006 | **Enables:** ART-010 completeness

**Goal:** Replace the markdown UAT runbook with an interactive UAT-walkthrough
SPA and rename the authoring agent accordingly, preserving fail-open behavior.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 150 (estimator: ok, modify-weighted) |
Production files: ~4 |
Total files: ~8 |
Budget result: within budget

**Scope:**
- One vertical slice — template → author agent → post-impl wiring → retired
  runbook path.
- Repo-authored `uat-walkthrough.html` gallery template: numbered steps with
  observable expected results per user story, env-setup prose, FR coverage
  matrix, per-step pass/fail toggles, copy-results-as-markdown export button
  emitting the fixed schema (OQ-5: fixed headings + one checkbox row per step
  ID, mechanically parseable by the review loop).
- Its catalog entry declares `["prompt", "markdown"]` (ART-001 FR-028), so **both**
  kinds ship. The `markdown` kind is the fixed results schema above — the auditable
  record. The `prompt` kind turns a failing run into work: it names the steps that did
  not pass and asks for a cause or a fix, so a tester who is not the implementer can
  hand the outcome straight to a coding agent without translating it first. A run
  where everything passed exports the tick-the-tasks instruction instead.
- A working reference implementation of both kinds already exists at
  `docs/ai/specs/.process/ART-001-acceptance-harness.html`
  (ART-001's own acceptance harness, which is this same Class-C shape); reuse its
  clipboard-failure and live-state handling rather than re-deriving them.
- `uat-runbook-author` → `uat-artifact-author` on both platforms; post-impl
  task list and task-list-canonical reference updated.
- Markdown runbook path retired from post-implementation; fail-open preserved
  (artifact failure logs and never blocks the PR).

**Out of Scope:**
- PR-writeup generation and the ready flip (ART-010).

**Verification:** Layer 5 agent verification for `uat-artifact-author`;
Layer 4 test for the fixed UAT-results export schema; Layer 1
task-list-canonical consistency; the gallery scanner covers the template;
Codex parity checks.

**Key Decisions:**
**Full replacement, fail-open (2026-07-28):** HTML walkthrough replaces the
markdown runbook outright (no dual output); the existing fail-open contract
carries over unchanged.

**Key Files:**
- `speckit-pro/artifact-gallery/templates/uat-walkthrough.html` — new template
- `speckit-pro/agents/uat-artifact-author.md` — renamed/rewritten agent
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
- `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md`

---

### ART-010: Final-PR Writeup, Companions & Ready Flip

**Priority:** P1 | **Depends On:** ART-003, ART-007, ART-012 | **Enables:** complete delivery

**Goal:** Close the implement stage by generating the final artifact set,
refreshing the draft PR in place, and flipping it to ready-for-review.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 190 (estimator: ok, modify-weighted) |
Production files: ~5 |
Total files: ~9 |
Budget result: within budget

**Scope:**
- One vertical slice — generate final artifacts → update PR body → flip ready.
- PR-writeup generation (always): motivation, before/after, file-by-file,
  implementation-notes section from the ART-012 record.
- Conditional companions: annotated diff (self-review findings or large
  diff), flowchart (operational-flow change) — triggers evaluated from
  workflow evidence.
- Draft PR updated in place (artifact index refreshed) and flipped via
  `gh pr ready`; no duplicate PR; final reviewability gate + packet validation
  still govern; marker-split interaction per the OQ-1 resolution from ART-007.

**Out of Scope:**
- Review-remediation loop (unchanged).

**Verification:** Layer 4 golden fixtures for the packet update/refresh path;
the `gh pr ready` flip is exercised in dry-run/integration only; Layer 1 +
Codex parity checks; payload regeneration.

**Key Decisions:**
**Update-in-place + flip (2026-07-28):** the draft PR is the one PR; the
implement stage refreshes and flips it rather than opening a second PR.

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — final artifact step + flip
- `speckit-pro/agents/artifact-author.md` — final-set generation prompts
- `speckit_pro_runner/helpers/` — packet update path
- `speckit-pro/codex-skills/speckit-autopilot/` mirror

---

### ART-011: Scaffold Integration

**Priority:** P1 | **Depends On:** ART-006 | **Enables:** one-command operator experience

**Goal:** Make scaffold the single front door: blind-spot pass before
grill-me, then chain into the autopilot plan stage so one invocation ends at
the reviewed draft PR.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 162 (estimator: ok, modify-weighted) |
Production files: ~4 |
Total files: ~7 |
Budget result: within budget

**Scope:**
- One vertical slice — blind-spot pass → interview seeding → chain hand-off →
  closing report.
- Read-only blind-spot pass (Field Guide technique): scan the roadmap scope
  and affected code area for unknown-unknowns — hidden coupling, risky
  surfaces, unstated assumptions; present findings and seed them into
  grill-me and the design concept's Open Questions.
- After the workflow-file commit, chain in-session into the autopilot plan
  stage per the ART-006 contract, with an explicit operator confirmation to
  decline.
- Closing report: draft-PR URL, artifact index, next step.
- Both platform variants.

**Out of Scope:**
- grill-me internals (unchanged).

**Verification:** Layer 2 skill-trigger evals re-run for the reworded
scaffold description; Layer 1 structure + Codex parity checks; the blind-spot
pass and chain hand-off are prompt-level — verified via the spec's UAT
evidence.

**Key Decisions:**
**Chain with confirm (2026-07-28):** scaffold auto-continues into the plan
stage after an explicit confirmation, preserving the interactive/autonomous
boundary at a visible seam.

**Key Files:**
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` — blind-spot pass + chain
- `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` — mirror
- `speckit-pro/skills/grill-me/` — seeding hook (input only, no machinery change)

---

### ART-012: Implementation-Notes Capture

**Priority:** P2 | **Depends On:** ART-006 | **Enables:** ART-010 writeup depth

**Goal:** Capture deviations-from-plan during implementation as a durable
notes record feeding the PR writeup and retrospective.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 190 (estimator: ok, modify-weighted) |
Production files: 6 |
Total files: ~9 |
Budget result: within budget

*Amended twice during the ART-012 run. 2026-08-10, Clarify session 1: scoping
recorded 115 LOC over ~3 production files, assuming the per-task
`## Task Result:` block had a single authored home. It has three, so the two
agent definitions below joined Key Files. 2026-08-11, operator decision: the
literal per-task append guarantee was restored after the premise behind
narrowing it turned out to be a stale claim about batched result delivery. That
added FR-006 and a sixth production file. The estimator was re-run at each step
rather than hand-adjusted. Every dimension stays inside its warn threshold.*

**Scope:**
- One vertical slice — executor reporting contract → orchestrator append →
  consumer hand-off.
- Implement-phase dispatch instructs every implementation executor to report
  deviations from plan, discovered edge cases, and surprises in its summary;
  the orchestrator appends them to
  `specs/<branch>/.process/implementation-notes.md`.
- Empty case records an explicit "no deviations" entry.
- Record consumed by ART-010's writeup and the retrospective extension when
  installed.

**Out of Scope:**
- Writeup generation itself (ART-010).

**Verification:** Layer 4 fixture test for the notes-record format (including
the explicit "no deviations" entry); dispatch-prompt wording covered by
Layer 1 + Codex parity checks.

**Key Decisions:**
**Notes are exhaust (2026-07-28):** the raw record lives under `.process/`;
its review-visible expression is the writeup's implementation-notes section.

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — dispatch template, Phase 7 append loop
- `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` — Codex mirror of the append loop
- `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md` — executor reporting contract, injected into every dispatch
- `speckit-pro/agents/implement-executor.md` — independent copy of the Task Result block, plus a four-field Terminal Deliverable enumeration that must be updated with it
- `speckit-pro/codex-agents/implement-executor.toml` — Codex mirror of that agent definition
- `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` — corrects three stale claims that parallel results arrive batched; that error is what narrowed the append cadence before the operator restored it

---

### ART-013: Documentation

**Priority:** P2 | **Depends On:** ART-001…012 | **Enables:** operator adoption

**Goal:** Document the artifact gallery and the staged workflow on the docs
site and in the plugin README.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 230 (estimator: ok) |
Production files: 0 (docs only) |
Total files: ~5 |
Budget result: within budget

**Scope:**
- One vertical slice — gallery reference page → workflow docs → validation.
- Docs-site gallery page: every template with purpose, when-to-use, and stage
  routing (from the manifest).
- Staged-workflow documentation: scaffold → draft PR → feedback → autopilot →
  final PR, with the artifact-viewing instructions.
- Plugin README updates; `pnpm --dir docs-site validate` green.

**Out of Scope:**
- Generated reference pages (regenerated, not hand-edited).

**Verification:** `pnpm --dir docs-site validate` (link validation,
generated-reference staleness, Playwright smoke); regenerate
`reference/tests.md` if the test tree changed; no plugin payload change
expected.

**Key Decisions:**
**Dedicated docs spec (2026-07-28):** docs land once, last, against shipped
behavior — interview decision.

**Key Files:**
- `docs-site/src/content/docs/` — gallery + workflow pages
- `speckit-pro/README.md` — staged-flow overview

---

### ART-014: Phase-Guard Enforcement Repair

**Priority:** P2 | **Depends On:** none | **Enables:** trustworthy phase-guard verdicts

**Goal:** Make the autopilot phase guard's workflow-identity check actually
enforce the authority its documentation already promises, and decide explicitly
which of the guard's other advisory checks should stay advisory.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: ~120 (estimator: ok, modify-weighted) |
Production files: ~2 |
Total files: ~5 |
Budget result: within budget

**Problem:** `speckit-pro/skills/speckit-autopilot/SKILL.md:756-757` documents
`autopilot-state.json.workflow_file` as authoritative and quotes the failure
message a mismatch produces: *"supplied workflow does not match autopilot state
workflow_file authority"*. That message cannot be produced by the invocation the
autopilot actually issues. Two independent reasons, both verified by execution
against a state file naming a different specification — the guard exits `0` and
reports `pass`:

1. `_authorized_workflow_text`
   (`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1298`)
   returns no errors unless the state carries a `pr-marker-plan.v2` schema
   (`:1307-1311`) **and** `--expected-head-commit` was supplied (`:1312-1313`).
   A normal autopilot run satisfies neither, so the two paths are never compared.
2. Its errors are folded into `workflow_checkpoint_errors` (`:4029-4031`), which
   is absent from the `status-evidence` tuple of `RULE_PROBLEM_KEYS` (`:239-247`).
   The autopilot always invokes `--rule status-evidence` (`SKILL.md:398`), and
   `main()` scopes the exit code to the selected rule's keys (`:4107-4111`), so
   even a produced error could not fail the run.

**Scope:**
- One vertical slice — un-short-circuit the comparison, register the key, prove
  the exit code moves.
- Decide whether the identity comparison should run unconditionally or whether
  the marker-plan/head-commit preconditions are load-bearing for some caller;
  if they are, give the plain identity comparison its own path.
- Register the identity failure under a key that the `status-evidence` rule
  actually consults. Registering `workflow_checkpoint_errors` wholesale would
  simultaneously arm its sibling checkpoint checks against a corpus that has
  never had to satisfy them — assess that blast radius before choosing between a
  dedicated key and widening the existing one.
- Audit the remaining advisory keys and record, per key, whether advisory is
  intentional. 11 of 19 problem keys cannot move the exit code under `--rule`;
  `SKILL.md` already justifies the coverage lists as deliberately advisory
  because the existing workflow corpus predates them, so the audit's job is to
  separate the deliberate from the accidental, not to arm everything.

**Out of Scope:**
- Any change to what the coverage lists check.
- Re-litigating the `--rule` scoping mechanism itself, which is deliberate and
  documented.

**Verification:** A Layer 4 test that runs the guard against a state file naming
a different specification and asserts a non-zero exit — the negative control that
does not exist today. Plus a regression run of the guard across the existing
`docs/ai/specs/.process/*-workflow.md` corpus to prove no previously-passing spec
starts failing.

**Key Decisions:**
**Found during ART-006, deliberately not fixed there (2026-08-04):** ART-006's
FR-014a exists precisely so the new stage-mirror check would not reproduce this
defect, and that check is registered and proven to move the exit code. Repairing
the pre-existing identity check was left out to keep ART-006 one slice.

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` — the guard
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — the authority documentation
- `tests/speckit-pro/unit/` — the missing negative control
- `speckit-pro/codex-skills/speckit-autopilot/` mirror

---


### ART-015: Spec-Size Re-Estimation Trigger

**Priority:** P3 | **Depends On:** none | **Enables:** honest slice budgets

**Goal:** Re-invoke the size estimator at the gates where a spec's signals have
actually changed, and record the operation's output instead of a hand-authored
figure.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: ~90 (estimator: ok, modify-weighted) |
Production files: ~2 |
Total files: ~4 |
Budget result: within budget

**Problem:** `estimate-spec-size` computes
`user_stories*25 + files*40 + frs*15`, halved when `new_vs_modify` is `modify`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:1063-1090`). It is accurate
when fed current signals and it is only ever fed *scoping-time* signals.

ART-006 is the worked example. At scaffold it received 3 user stories, 12 files
and 14 functional requirements and returned `{estimated_loc: 382,
suggested_slices: 1, status: "ok"}`. Clarification and three checklist domains
then grew the specification to 25 functional requirements. Fed those final
signals — 3 stories, 17 files, 25 FRs — the same operation returns
`{estimated_loc: 565, suggested_slices: 2, status: "warn"}`. Nothing re-invoked
it, so the ratified budget stayed at 382 while the specification became a
`warn`-sized one. The file signal was declared at 17 and came in at exactly 17,
so the drift is entirely in the requirement count.

The G3 "re-estimate" recorded in that spec's `plan.md` was a number typed by
hand, not a re-invocation, which is why it moved to 430 rather than to what the
operation would have returned.

**Scope:**
- One vertical slice — recompute at the gate, record the operation's output.
- Re-invoke `estimate-spec-size` at G3 (after Plan) and G5 (after Tasks), reading
  the current requirement count from `spec.md` and the current file count from
  the plan's Declared File Operations block.
- Record the returned triple verbatim in the workflow file's budget table,
  attributed to the operation, so a hand-typed figure is distinguishable from a
  computed one.
- A `status` transition from `ok` to `warn` between gates surfaces to the
  operator with the previous and current signals side by side. It stays
  **advisory** — the estimator never blocks, and the PR-time diff gate remains
  the authority on the real diff.

**Out of Scope:**
- Changing the estimator's formula, its coefficients, or the 400-line ceiling.
- Making any estimate blocking.
- Teaching the model about per-file size. A single 992-line table-driven fixture
  file was half of ART-006's human-reviewable diff, and a flat per-file term
  cannot express that. It is a real limit of signal-based estimation, recorded in
  `ART-006-retrospective.md` and deliberately not addressed here.

**Verification:** A Layer 4 test that feeds scoping-time signals, then grown
signals, and asserts the recorded budget follows the second — the regression that
would have caught ART-006's drift. Plus a golden fixture pinning the `ok` → `warn`
transition report.

**Key Decisions:**
**The estimator was exonerated by re-running it (2026-08-05):** the first reading
of ART-006's overrun was that the estimator underestimates. Re-invoking it with
final signals returned a figure consistent with the outcome, which relocated the
defect from the model to the absent trigger.

**Key Files:**
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — the estimator
- `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` — G3/G5 gates
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — gate recording
- `speckit-pro/codex-skills/speckit-autopilot/` mirror

---

## Decomposition Principles

When breaking a feature into specs:

1. **Each spec is independently executable** through the full SpecKit workflow (specify → implement)
2. **Minimize cross-spec dependencies** — prefer sequential over deeply nested
3. **Foundations first** — brand kit and staging before emission and sweep
4. **Parallel tiers where seams allow** — template ports are sibling-independent
5. **Integration spec near last** — ART-010 wires draft PR, templates, and notes together
6. **Each spec gets its own directory**: `specs/<branch>/` (typically
   `specs/art-NNN-<name>/` for this roadmap)

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| Plugin runtime | `speckit_pro_runner` (Python 3.11+ stdlib, JSON stdin/stdout contract) |
| Test suite | `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5) |
| Release | release-please + payload/proof regeneration ritual |
| Docs site | Astro/Starlight, Node ≥ 22.12, `pnpm --dir docs-site validate` |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| New shipped directory | `speckit-pro/artifact-gallery/` | brand kit, manifest, 21 templates (20 ports + UAT walkthrough) |
| New/renamed agents | `speckit-pro/agents/`, codex mirror | `artifact-author`, `uat-artifact-author` |
| Payload regen | generated artifact contract | every ART spec ships plugin bytes |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| Python 3.11+ | pyenv (repo standard) |
| Node ≥ 22.12 + pnpm | nvm v22.22.2 for docs-site work (ART-013) |
| Browser check | open each template over `file://`; console must be clean |

---

## References

- **Source PRD:** [../../prd-html-artifacts.md](../../prd-html-artifacts.md) — the SPEC catalog above is derived from its Features / Acceptance Criteria
- **Roadmap MOC:** [html-artifacts-roadmap-MOC.md](html-artifacts-roadmap-MOC.md)
- **Constitution:** `.specify/memory/constitution.md`
- **Project Standards:** `AGENTS.md`, `speckit-pro/AGENTS.md`, `REVIEW.md`
- **Upstream gallery:** thariqs.github.io/html-effectiveness · github.com/anthropics/html-effectiveness
- **Research:** claude.com/blog — "A Field Guide to Claude Fable: Finding Your Unknowns"; "The Unreasonable Effectiveness of HTML"
- **Brand sources:** racecraft-lab/racecraft `docs/brand/`, `.claude/rules/brand.md`, `.claude/rules/content.md`; `docs-site/src/styles/brand.css` (DOC-013)

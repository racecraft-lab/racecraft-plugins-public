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
**Status:** Active; dependency graph approved 2026-07-28; all specs pending

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
| ART-001 | Artifact Brand Kit & Gallery Foundation | ⏳ Pending | - | Ready to scaffold |
| ART-002 | Draft-PR Template Set | ⏳ Pending | - | Blocked by ART-001 |
| ART-003 | Final-PR Template Set | ⏳ Pending | - | Blocked by ART-001 |
| ART-004 | Gallery Completion: Design & Prototyping | ⏳ Pending | - | Blocked by ART-001 |
| ART-005 | Gallery Completion: Knowledge, Reports & Editors | ⏳ Pending | - | Blocked by ART-001 |
| ART-006 | Autopilot Staging | ⏳ Pending | - | Ready to scaffold (parallel with ART-001) |
| ART-007 | Draft-PR Emission | ⏳ Pending | - | Blocked by ART-002, ART-006 |
| ART-008 | Feedback Sweep | ⏳ Pending | - | Blocked by ART-007 |
| ART-009 | UAT Walkthrough Replacement | ⏳ Pending | - | Blocked by ART-001, ART-006 |
| ART-010 | Final-PR Writeup, Companions & Ready Flip | ⏳ Pending | - | Blocked by ART-003, ART-007, ART-012 |
| ART-011 | Scaffold Integration | ⏳ Pending | - | Blocked by ART-006 |
| ART-012 | Implementation-Notes Capture | ⏳ Pending | - | Blocked by ART-006 |
| ART-013 | Documentation | ⏳ Pending | - | Blocked by all |

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
  complete) + draft-PR existence (via `gh`, corroboration only — the workflow
  file is authoritative; discrepancies logged per OQ-4).
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
Projected reviewable LOC: 115 (estimator: ok, modify-weighted) |
Production files: ~3 |
Total files: ~6 |
Budget result: within budget

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
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — dispatch template
- `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md` — executor reporting contract
- `speckit-pro/codex-skills/speckit-autopilot/` mirror

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

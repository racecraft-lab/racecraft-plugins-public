# SpecKit Workflow: ART-003 slice 3 — Flowchart

**Template Version**: 1.0.0
**Created**: 2026-08-13
**Purpose**: Execute ART-003 slice 3, the final slice of the final-PR template set.

---

## How to Use This Template

1. **Scope: slice 3 only** — `flowchart`. Slices 1 and 2 shipped on the branches
   this one is cut from, as PR #435 and PR #436.
2. Authored from the existing ART-003 design concept, not a second interview.
   The concept covers all three slices and assigns what it leaves open to Clarify
   by name.
3. **Track progress** using the status table below.

---

## Design Concept

`docs/ai/specs/.process/ART-003-design-concept.md`. Q7 fixes this slice's
defining decision; the Open Questions assign the slot inventory to Clarify after
the upstream read, exactly as they did for slices 1 and 2.

---

## Slice Plan

| Slice | Template | Upstream | Branch | Base | State |
|---|---|---|---|---|---|
| 1 | `pr-writeup` | `17-pr-writeup.html` | `art-003-final-pr-template-set` | `main` | **PR #435** |
| 2 | `annotated-diff` | `03-code-review-pr.html` | `…-slice-2` | slice 1 | **PR #436** |
| 3 | `flowchart` | `13-flowchart-diagram.html` | `…-slice-3` | slice 2 | **this run** |

**Stacked.** This branch carries both shipped artifacts and all validation
literals from both. The pull request bases on slice 2's branch, never `main`.

### Reviewability budget — this slice is in a different class

**`flowchart` declares `exports: []`.** That is the single fact that governs its
budget. Across the whole gallery, the `exports` declaration has predicted the
authored size better than slot count or upstream size ever did:

| Template | `exports` | Authored | CSS | JS | Markup |
|---|---|---|---|---|---|
| `spec-explainer` | `[]` | **315** | 169 | **0** | 146 |
| `pr-writeup` (slice 1) | both | 735 | 227 | 334 | 174 |
| `annotated-diff` (slice 2) | both | 724 | 259 | 344 | 121 |

The two export carriers each spend ~340 lines on a routine this slice does not
build at all. `spec-explainer` is the comparator, not slices 1 and 2.

Upstream `13-flowchart-diagram.html` is 395 lines — 152 CSS, 96 JS, 147 markup,
one inline `<svg>`, zero `<button>`.

| Component | Target | Basis |
|---|---|---|
| CSS | **~200** | `spec-explainer`'s 169 plus diagram-specific rules it never carried |
| JS | **~80** | the in-page disclosure Q7 fixes, and nothing else — no export routine, no currency guard |
| Markup | **~180** | the diagram, its text equivalent, and the regions |

```text
Projected reviewable LOC: 460
```

**340 lines below the 800 block.** This is the comfortable slice, and the first
in the feature whose budget is not the governing risk. The risk here is different
and is named in the constraints: a diagram that carries meaning only in its
picture.

**Nothing may be appended after this block.**

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Slot inventory after the upstream read |
| Plan | `/speckit-plan` | ⏳ Pending | Re-declare from measurement |
| Checklist | `/speckit-checklist` | ⏳ Pending | accessibility carries the weight here |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | advisory |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear |
| G2 | After Clarify | Ambiguities resolved |
| G3 | After Plan | Budget re-declared from measurement |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified |
| G6 | After Analyze | No CRITICAL issues |
| G6.5 | Before Implement | Composite confidence |
| G7 | After Implement | Suite green above baseline |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Gallery files ship in the payload; manifest and artifact stay consistent | `run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | No build step, no sibling asset, renders over `file://` with no console error | `run-all.py --layer 4` plus the manual render |
| IV. Test Coverage Before Merge | Fill-region and gallery-scanner coverage | `python3 tests/speckit-pro/run-all.py` |
| V. Conventional Commits | `<type>(<lowercase-scope>): <plain English description>` | CI `validate-pr-title` |
| VI. KISS, Simplicity & YAGNI | No affordance the entry does not declare — and this entry declares none | Code review |

**Constitution Check:** ⏳

### Phase 0 Prerequisites Record

| Field | Value |
|---|---|
| Stage | full |
| Branch | `art-003-final-pr-template-set-slice-3`, cut from slice 2 |
| Feature dir | pinned via `.specify/feature.json` |
| `ON_FEATURE_BRANCH` | **true** (asserted; the vendored `^[0-9]{3}-` regex does not match namespaced ids) |
| `PROJECT_COMMANDS` | `UNIT_TEST` / `FULL_VERIFY` = `python3 tests/speckit-pro/run-all.py` |
| `CONFIDENCE_GATE_MODE` | `advisory` |
| **G0 test baseline** | **7380/7380** (L1 1447, L4 5747, L5 186) — slice 2's shipped state |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-003 (slice 3 of 3) |
| **Name** | Flowchart |
| **Branch** | `art-003-final-pr-template-set-slice-3` |
| **Base** | `art-003-final-pr-template-set-slice-2` (PR #436) |
| **Priority** | P1 |
| **Stage** | full |

### Success Criteria Summary

- [ ] `speckit-pro/artifact-gallery/templates/flowchart.html` exists, one self-contained file
- [ ] Both canonical blocks embedded byte for byte with their markers
- [ ] Attribution header naming `13-flowchart-diagram.html`
- [ ] The diagram carries a **text equivalent** conveying everything the picture does
- [ ] A click discloses detail **in the page**; nothing durable is produced
- [ ] **No export control of any kind**, because the entry declares none
- [ ] Artifact title byte-identical to the catalog's `Flowchart`
- [ ] Manifest entry flips `planned` → `shipped`, one value only
- [ ] Full suite green above the 7380 baseline; payload regenerated

---

## Phase 1: Specify

### Specify Prompt

```text
/speckit-specify

## Feature: ART-003 slice 3 — the flowchart artifact

Scope this slice to ONE template: flowchart. Slices 1 and 2 shipped on this
branch and are the precedent for everything shared.

### Problem Statement
A reviewer judging a change that alters an operational flow needs to see the flow
itself — what calls what, in what order, and which path the change turns on —
rather than reconstruct it from a diff.

### Users
- The reviewer reading a finished pull request that changes an operational flow.
- The ART-010 generation step, which fills this template's regions.

### User Stories
[US1] A reviewer opens flowchart.html from the filesystem and reads the
      operational flow the change affects, as a diagram and as a text equivalent
      that conveys the same information.
[US2] A reviewer clicks a node and sees more detail about it, in the page,
      without leaving or producing anything.

### Constraints
- ONE HTML file. No build step, no bundler, no sibling asset.
- Embed the two canonical blocks verbatim WITH their markers, byte for byte.
- Change exactly one catalog value: this entry's status, planned -> shipped.
- Attribution header with the five exact labels, naming 13-flowchart-diagram.html.
- THE ENTRY DECLARES exports: [] — ship NO export control, no copy button, no
  clipboard code, and no reader-input field of any kind. spec-explainer is the
  precedent: an empty exports array is the deliberate way to say the reader
  produces nothing durable, and it ships no such affordance.
- The diagram MUST carry a text equivalent conveying everything the picture does.
  A diagram is the one artifact kind where meaning can hide entirely in shape and
  position, and a reader who cannot see it must lose nothing.
- Nothing carries meaning by colour alone. Node roles, states and edge kinds all
  need a non-colour carrier.
- The artifact title MUST equal its catalog entry's title, byte for byte. Slice 1
  shipped this wrong and only independent review caught it; no test asserts it.

### Decisions already fixed by the design concept (do not re-litigate)
- Q7: a click produces nothing durable. It discloses detail in the page. The
  entry declares exports: [], and that stays true.
- Q3: keep the upstream mechanism and structure, restyle entirely to brand
  tokens, drop upstream sections mapping to no fill region, author fresh what the
  stage needs.
- Q2/Q11: anchor content capped at the demonstrating minimum.

### Out of Scope
- Generation and authoring logic, and the ready flip. That is ART-010.
- Any export affordance whatsoever.
- Any change to the contract document, the brand kit, the head block, or any
  catalog value other than this entry's own status.
```

### Specify Results

<!-- Fill in after running -->

---

## Phase 2: Clarify

### Clarify Prompts

#### Session 1: Slot inventory and the diagram's text equivalent

```text
/speckit-clarify Focus on the slot inventory and the text equivalent, after
reading 13-flowchart-diagram.html read-only from the session scratchpad. Resolve:
the full slot inventory with each slot's Source; how the diagram is drawn given
it must be one self-contained file with no sibling asset; what form the text
equivalent takes and where it sits relative to the diagram; whether nodes are
individually addressable and whether flowchart needs a LIST_SLOT row at all,
which the design concept explicitly leaves open; and how node roles and edge
kinds are distinguished without colour.
```

#### Session 2: The disclosure mechanism

```text
/speckit-clarify Focus on the click-to-disclose mechanism. Resolve: what a click
actually reveals and where it appears; whether the disclosure is native markup or
scripted, and if scripted, how little script suffices; what a keyboard user does
instead of clicking; what happens with scripting unavailable; and how the
disclosed state is conveyed to a reader who cannot see the diagram. Q7 fixes that
nothing durable is produced — that is not open.
```

### Clarify Results

<!-- Fill in after running -->

---

## Phase 3: Plan

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- One self-contained HTML file, inline CSS and JS only. No build step.
- Brand kit and head region embedded verbatim between their markers.
- Catalog: one value flipped.
- Repository validation: Python 3.11+ standard library only.

## Constraints
- Reviewability: 460 declared, 800 block, 340 lines of headroom. Decomposed
  ~200 CSS, ~80 JS, ~180 markup, derived from spec-explainer's realized 315
  (169 CSS, 0 JS, 146 markup) — the exports: [] class, not slices 1 and 2.
- RE-DECLARE from your own measurement and show the working.
- Reuse the measuring instrument recorded in slice 1's quickstart. Do not write
  a second one.
- Declared File Operations must account for the generated-artifact contract.
- The contract binds status and file presence in BOTH directions.
- Fetch upstream read-only into the session scratchpad; never stage upstream bytes.

## Architecture Notes
- The budget is comfortable here for the first time in this feature. Do not spend
  the slack: the entry declares no export, so every line of clipboard or capture
  code would be an affordance the catalog does not declare.
- The accessibility surface is the real work. A diagram is where meaning most
  easily hides in shape, position and colour.
- The heading token is --rc-font-display, assigned to h1 and h2 only.
- --rc-border-subtle carries no meaning; use --rc-border-strong.
```

### Plan Results

<!-- Fill in after running -->

---

## Phase 4: Domain Checklists

### Step 2: Enriched Checklist Prompts

#### 1. accessibility Checklist

```text
/speckit-checklist accessibility

Focus on ART-003 slice 3 requirements. This domain carries more weight here than
on either earlier slice, because a diagram is the artifact kind where meaning
most easily hides in the picture:
- The text equivalent conveys everything the diagram does. A reader who cannot
  see it loses nothing.
- Node roles, node states and edge kinds are each distinguishable without colour.
- The disclosure is keyboard-reachable and operable, and its state is exposed.
- Any interactive node is reachable in reading order with a visible focus ring.
- --rc-font-display is assigned to h1 and h2 only; --rc-border-subtle carries no
  meaning.
- Any inline SVG carries an accessible name and is not announced as a meaningless
  graphic.
```

#### 2. ux Checklist

```text
/speckit-checklist ux

Focus on ART-003 slice 3 requirements:
- Every region carries sample content held to the demonstrating minimum.
- A reader opening the file cold can tell what the flow is and what the change
  turns on.
- The diagram is legible at a normal reading width without horizontal page scroll.
- The text equivalent reads as a first-class rendering, not an afterthought.
```

#### 3. error-handling Checklist

```text
/speckit-checklist error-handling

Focus on ART-003 slice 3 requirements:
- Scripting unavailable: the diagram and its text equivalent both remain fully
  readable, and no control is offered that cannot work.
- Network unavailable: the page stays readable and every control still operates.
- Storage refused: the theme control keeps working for the session.
- There is no clipboard path here, because the entry declares no export. Confirm
  that absence rather than assuming it.
```

### Checklist Results

<!-- Fill in after running -->

---

## Phase 5: Tasks

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
TDD-ordered. One template file, one catalog value, the shared-validation literals.

## Implementation Phases
1 Foundation — validation literals, skeleton, both canonical blocks, attribution, inventory.
2 US1 — the diagram, its text equivalent, and the regions.
3 US2 — the disclosure.
4 Polish — catalog flip, payload regeneration, measurement, suite green.

## Constraints
- Emit a measurement checkpoint as a real task with a numeric criterion and a
  stop rule, after the CSS and before the markup.
- Include a task that asserts NO export affordance ships, by search.
- Include a runnable comparison of the artifact title to its catalog entry.
- The full suite must pass above the 7380 baseline at the end.
```

### Tasks Results

<!-- Fill in after running -->

---

## Atomicity Route

<!-- Recorded after G5 -->

---

## Phase 6: Analyze

### Analyze Prompt

```text
/speckit-analyze

Cross-artifact consistency across spec.md, plan.md, tasks.md, research.md,
data-model.md, quickstart.md, and the design concept.

Hunt hardest for:
1. Numeric drift — verify by RUNNING the declaration parser regex, not by
   reading. It takes the LAST match in the file, and prose near any other number
   silently becomes the declaration. That trap fired four times across slices 1
   and 2.
2. Requirement-to-task coverage, both directions, reported separately for
   explicit citation and content coverage.
3. Anything inherited from slices 1 or 2 that does not apply to a read-only
   artifact — especially export, clipboard or currency-guard requirements, which
   have no place here.
```

### Analysis Results

<!-- Fill in after running -->

---

## Phase 6.5: Confidence Gate

| Field | Value |
|-------|-------|
| Mode | `advisory` |
| Composite confidence | |
| Verdict | |
| Evidence | |

---

## Phase 7: Implement

### Implement Prompt

```text
/speckit-implement

Execute tasks.md in order, TDD throughout.

Slices 1 and 2 are shipped on this branch and are the precedent for the skeleton,
the canonical blocks, the attribution header, the inventory format, and the CSS
house style. spec-explainer is the precedent for a read-only artifact.

Known hazards, paid for twice already:
- The test suite is NOT read-only. It rewrites dist/** on every run, and it moves
  failures between modules in both directions. Restore before regenerating; for
  a new artifact the payload copies are UNTRACKED, so the restore is removal, not
  git show.
- Expect an intermediate red until both the catalog flip and the payload
  regeneration. Three families. Anything outside them is real.
- Running --layer 4 alone overcounts against a full run.
- Naming a token in a CSS comment to explain its absence fails the rule's search.
- The artifact title must equal its catalog entry's title; no test asserts it.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - US1 | | | |
| 3 - US2 | | | |
| 4 - Polish | | | |

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit `Skipped`
before the run may report completion.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

**The pull request bases on `art-003-final-pr-template-set-slice-2`, never `main`.**

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

# SpecKit Workflow: ART-003 slice 2 — Annotated Diff

**Template Version**: 1.0.0
**Created**: 2026-08-13
**Purpose**: Execute ART-003 slice 2 through the SpecKit workflow.

---

## How to Use This Template

1. **Scope: slice 2 only.** ART-003 ships as three stacked slices, one template
   per pull request. This workflow drives slice 2 (`annotated-diff`). Slice 1
   (`pr-writeup`) is open as PR #435 and this branch is cut from it.

2. This file was authored from the existing ART-003 design concept rather than
   from a fresh interview. That is deliberate and is explained below.

3. **Track progress** using the status table below.

---

## Design Concept

The Grill Me interview for ART-003 ran once, at scaffold, and covers all three
slices. Its record lives at:

```text
docs/ai/specs/.process/ART-003-design-concept.md
```

**Why no second interview.** The design concept fixes slice 2's decisions
already — Q2 caps the anchor content, and Q6 settles the objection granularity
and the list-slot consequence. What it leaves open for this slice, it assigns
explicitly to **Clarify**, not to grill-me:

> "ART-002 resolved the equivalent question in a dedicated Clarify session rather
> than in grill-me, on the stated ground that slot names must not be invented
> before the upstream sources are read."

Clarify is autopilot's own phase, run through `/speckit-clarify` and the
consensus protocol. Re-running grill-me would re-ask questions this feature has
already answered.

---

## Slice Plan

| Slice | Template | Upstream source | Branch | Base | State |
|---|---|---|---|---|---|
| 1 | `pr-writeup` | `17-pr-writeup.html` | `art-003-final-pr-template-set` | `main` | **PR #435 open** |
| 2 | `annotated-diff` | `03-code-review-pr.html` | `art-003-final-pr-template-set-slice-2` | slice 1 | **this run** |
| 3 | `flowchart` | `13-flowchart-diagram.html` | `art-003-final-pr-template-set-slice-3` | slice 2 | pending |

**Stacked, not independent.** This branch carries slice 1's artifact and its
three validation literals. The pull request bases on slice 1's branch, never on
`main`, and no merge happens inside this run.

### Reviewability budget — derived from slice 1's realized figures

Slice 1 measured **735 authored** (227 CSS, 334 JS, 174 markup) against a
declared 758. That is the only measurement of this exact work class, and it
replaces every earlier multiplier.

| Component | Target | Basis |
|---|---|---|
| Export and objection-capture JS | **~330** | slice 1's 334, same routine and same currency guard; two hunk mounts instead of six section mounts |
| CSS | **~240** | slice 1's 227 plus a margin for diff-specific structure it never carried |
| Markup | **~185** | fewer regions than slice 1's seven, but each hunk carries diff rows |
| **Total** | **755** | warn; 45 lines of headroom to the 800 block |

```text
Projected reviewable LOC: 755
```

**CSS is the risk, and it is a sharper risk here than on slice 1.** A diff view
needs line-state, gutter and severity styling that a document template never had.
The sensitivity is unforgiving:

| CSS | Total | Result |
|---|---|---|
| 200 | 715 | warn, 85 spare |
| 240 | 755 | warn, 45 spare — **the declared target** |
| 280 | 795 | warn, 5 spare |
| 320 | 835 | **block** |

Upstream spends 389 lines on CSS. The brand kit replaces most of it, but the
diff-specific part has no counterpart in the kit and must be authored.

**Nothing may be appended after this block.** The declaration parser takes the
last phrase match in the whole file.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Session 1 runs **after** the upstream source is read |
| Plan | `/speckit-plan` | ⏳ Pending | Re-declare the budget; adopt a CSS ceiling as a checkable constraint |
| Checklist | `/speckit-checklist` | ⏳ Pending | Three domains: accessibility, ux, error-handling |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories clear |
| G2 | After Clarify | Ambiguities resolved |
| G3 | After Plan | Architecture approved, budget re-declared |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified |
| G6 | After Analyze | No CRITICAL issues |
| G6.5 | Before Implement | Composite confidence meets the threshold |
| G7 | After Implement | Tests pass |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Gallery files ship in the payload; manifest and artifact stay consistent | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | No build step, no sibling asset, renders over `file://` with no console error | `python3 tests/speckit-pro/run-all.py --layer 4` plus the manual render check |
| IV. Test Coverage Before Merge | Fill-region and gallery-scanner coverage for the shipped template | `python3 tests/speckit-pro/run-all.py` |
| V. Conventional Commits | `<type>(<lowercase-scope>): <plain English description>` | CI `validate-pr-title` |
| VI. KISS, Simplicity & YAGNI | Anchor content capped at two hunks; no affordance the entry does not declare | Code review + the reviewability diff gate |

**Constitution Check:** ⏳

### Phase 0 Prerequisites Record

| Field | Value |
|---|---|
| Stage | full |
| Branch | `art-003-final-pr-template-set-slice-2`, cut from slice 1 |
| Feature dir | pinned via `.specify/feature.json` to `specs/art-003-final-pr-template-set-slice-2` |
| `ON_FEATURE_BRANCH` | **true** (asserted; the vendored `^[0-9]{3}-` regex does not match this repo's namespaced ids) |
| `PROJECT_COMMANDS` | `UNIT_TEST` / `FULL_VERIFY` = `python3 tests/speckit-pro/run-all.py`; others N/A |
| `PRESET_CONVENTIONS` | `speckit-pro-reviewability` 1.0.0 |
| `CONFIDENCE_GATE_MODE` | `advisory` |
| **G0 test baseline** | **7379/7379** (L1 1447, L4 5746, L5 186) — slice 1's shipped state, which is this branch's starting point |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-003 (slice 2 of 3) |
| **Name** | Annotated Diff |
| **Branch** | `art-003-final-pr-template-set-slice-2` |
| **Base** | `art-003-final-pr-template-set` (slice 1, PR #435) |
| **Dependencies** | slice 1 shipped on this branch |
| **Priority** | P1 |
| **Stage** | full |

### Success Criteria Summary

- [ ] `speckit-pro/artifact-gallery/templates/annotated-diff.html` exists, one self-contained file
- [ ] Both canonical blocks embedded byte for byte with their markers
- [ ] Attribution header naming `03-code-review-pr.html`
- [ ] `hunks` is a list slot; two hunks ship, one annotated and one clean
- [ ] Per-hunk objection capture, keyboard-reachable, with anchors
- [ ] Both exports work, carrying each hunk's anchor, with the currency guard slice 1 proved
- [ ] Severity readable as a word, never by colour alone
- [ ] Manifest entry flips `planned` → `shipped`, one value only
- [ ] Full suite green above the 7379 baseline; payload regenerated
- [ ] Budget re-declared against the measured figure

---

## Phase 1: Specify

### Specify Prompt

```text
/speckit-specify

## Feature: ART-003 slice 2 — the annotated diff artifact

Scope this slice to ONE template: annotated-diff. Slice 1 (pr-writeup) already
shipped on this branch; slice 3 (flowchart) is out of scope.

Read docs/ai/specs/.process/ART-003-design-concept.md — it is the source of truth
for scoping. Read the shipped speckit-pro/artifact-gallery/templates/pr-writeup.html
as the immediate precedent; it is one commit old and was built to the same contract.

### Problem Statement
A reviewer judging a finished change needs to see the diff with the review's own
findings attached to it, and to hand objections back per hunk without retyping
them.

### Users
- The reviewer reading a finished pull request.
- The ART-008 feedback sweep, which reads exported objections from a PR comment.
- The ART-010 generation step, which fills this template's regions.

### User Stories
[US1] A reviewer opens annotated-diff.html from the filesystem and reads a
      unified diff with margin annotations, severity stated in words, and jump
      links between findings.
[US2] A reviewer attaches an objection to any hunk and copies every objection out
      of the page, as a PR comment or as an instruction for a coding agent.

### Constraints
- ONE HTML file. No build step, no bundler, no sibling asset.
- Embed the two canonical blocks verbatim WITH their markers, byte for byte.
- Change exactly one catalog value: this entry's status, planned -> shipped.
- Attribution header with the five exact labels, naming 03-code-review-pr.html.
- Severity, and every other distinction, MUST be readable without colour.
- Exports keyboard-reachable, reporting success in text, deriving from live state,
  revealing a selectable field when the clipboard is refused.
- The currency guard slice 1 shipped is REQUIRED here too: a token compared at
  every EFFECT site, not at the settle callbacks. Slice 1 proved the three older
  templates get this wrong in both directions.
- Reviewability: 755 declared against an 800 block, 45 lines of headroom. CSS is
  the risk.

### Decisions already fixed by the design concept (do not re-litigate)
- Q2: cap the anchor content. TWO hunks ship — one annotated, one clean — which
  is what MINIMUM_ITEMS requires and is provably sufficient. Real diffs arrive at
  generation time in ART-010.
- Q6: objections attach PER HUNK, using the same inline keyboard-reachable
  disclosure plus labelled textarea slice 1 and ART-002 ship. This makes `hunks`
  a LIST_SLOT, which the two anchor hunks satisfy.
- Q3: keep the upstream mechanism and structure, restyle entirely to brand tokens,
  drop upstream sections that map to no fill region, author fresh what the stage
  needs.

### Out of Scope
- flowchart. Slice 3.
- Generation and authoring logic, and the ready flip. ART-010.
- Any change to the contract document, the brand kit, the head block, or any
  catalog value other than this entry's own status.
- Fixing the currency defect in the three older shipped templates.
```

### Specify Results

<!-- Fill in after running -->

---

## Phase 2: Clarify

### Clarify Prompts

#### Session 1: Slot inventory and hunk granularity

```text
/speckit-clarify Focus on the fill-region inventory, after reading
03-code-review-pr.html read-only from the session scratchpad. Resolve: the full
slot inventory and each slot's Source; which upstream sections map, which are
dropped, and which regions are authored fresh; the anchor form for hunk items;
how a margin annotation attaches to a diff row; and how severity is carried
without colour. `hunks` is fixed as a LIST_SLOT and is not open.
```

#### Session 2: Export payload and objection shape

```text
/speckit-clarify Focus on the export payloads. Resolve the serialized structure
of both exports, reusing slice 1's shape exactly unless evidence says otherwise:
the same two header lines, the same one-line divergence between kinds, and the
same reference-line form with two spaces before the parenthesis. Resolve what the
reference line names for a hunk, and what each export emits when no objection was
recorded.
```

#### Session 3: Diff rendering edges

```text
/speckit-clarify Focus on the diff rendering edges. Resolve: what a clean hunk
renders when it carries no annotation; how added, removed and context rows are
distinguished without colour; whether line numbers are addressable; and what the
region renders when a hunk is very wide, given the artifact must stay readable
with no horizontal page scroll.
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
- Brand kit embedded between /* BRAND-KIT:START */ and /* BRAND-KIT:END */.
- Head region embedded between <!-- GALLERY-HEAD:START --> and <!-- GALLERY-HEAD:END -->.
- Catalog: speckit-pro/artifact-gallery/manifest.json, one value flipped.
- Repository validation: Python 3.11+ standard library only.
- Verification: python3 tests/speckit-pro/run-all.py; scripts/refresh-release-artifacts.py

## Constraints
- Reviewability: 755 declared, 800 block, 45 lines of headroom. Decomposed as
  ~330 JS, ~240 CSS, ~185 markup, derived from slice 1's realized 735
  (227 CSS, 334 JS, 174 markup) rather than from any multiplier.
- ADOPT A CSS CEILING AS AN EXPLICIT CHECKABLE CONSTRAINT and say how it is
  checked. Slice 1 did this and the ceiling held on first measurement. CSS is a
  sharper risk here: a diff view needs line-state, gutter and severity styling a
  document template never carried, and at 320 CSS lines this slice blocks.
- Reuse the measuring instrument recorded in slice 1's quickstart. Do not write a
  second one.
- Declared File Operations must account for the generated-artifact contract.
- The contract binds status and file presence in BOTH directions. Land the flip
  and the file together.
- Fetch upstream read-only into the session scratchpad; never stage upstream bytes.

## Architecture Notes
- Slice 1's shipped artifact is the precedent for everything shared: the export
  routine, the currency guard scoped by effect, the disclosure shape, the
  inventory format, and the failure path. Copy the routine rather than reinvent
  it; the four-site guard is the part that must not regress.
- Q2: two hunks, one annotated one clean.
- Q6: objections per hunk; `hunks` is a LIST_SLOT.
- The heading token is --rc-font-display, assigned to h1 and h2 only.
- --rc-border-subtle carries no meaning; use --rc-border-strong.
- Nothing carries meaning by colour alone — this binds hardest on a diff, where
  added and removed rows are conventionally colour-only.
```

### Plan Results

<!-- Fill in after running -->

---

## Phase 4: Domain Checklists

### Step 1: Recommended Domains

accessibility, ux, error-handling — the same three slice 1 ran, for the same
reasons, plus the diff-specific colour risk.

### Step 2: Enriched Checklist Prompts

#### 1. accessibility Checklist

```text
/speckit-checklist accessibility

Focus on ART-003 slice 2 requirements:
- Added, removed and context rows are distinguishable WITHOUT colour. This is the
  single hardest accessibility requirement in this slice, because diffs are
  conventionally colour-only.
- Severity reads as a word, never as a colour or a glyph's fill.
- Every export control and every objection disclosure is keyboard reachable and
  operable, reporting success in text.
- The disclosure states in text whether its hunk carries an objection, recomputed
  live on input, with a real label and no placeholder standing in for one.
- No ARIA on the disclosure; the native mapping does not permit it on a summary.
- --rc-border-subtle carries no meaning; --rc-font-display is assigned to h1/h2 only.
- Jump links move focus, not just scroll position.
```

#### 2. ux Checklist

```text
/speckit-checklist ux

Focus on ART-003 slice 2 requirements:
- Every region carries sample content held to the demonstrating minimum. Two
  hunks: one annotated, one clean, so a reader sees both states.
- A reader opening the file cold can tell what each region is for.
- The diff stays readable with no horizontal page scroll.
- A clean hunk reads as deliberately clean rather than as broken or unfinished.
- Jump links between findings do something a reader can follow.
- MINIMUM_ITEMS is a FLOOR of two, not an equality — but Q2 caps this template at
  two deliberately, which is the one place a floor and a cap coincide.
```

#### 3. error-handling Checklist

```text
/speckit-checklist error-handling

Focus on ART-003 slice 2 requirements:
- Clipboard refused or unavailable: reveal the text in a selectable, focusable,
  not-disabled field, move focus to it, report one no-cause failure message, and
  do NOT report success. No second copy attempt.
- Two exports invoked before the first settles: only the later reports. The guard
  is scoped by EFFECT, not by path — announce and focus both defer behind timers,
  so a synchronous decision still lands asynchronously.
- The reader exports having written no objection: say so in words, and deny that
  it is an approval.
- Network unavailable: the page stays readable and every control works.
- Feedback text says "opened from a filesystem" and never names the local-file
  scheme, which the gallery scanner reads as an external reference and fails.
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
2 US1 — the diff regions with capped sample content.
3 US2 — per-hunk objection capture, both exports, the currency guard, the failure path.
4 Polish — catalog flip, payload regeneration, budget re-declaration.

## Constraints
- Emit the measurement checkpoints as REAL tasks with numeric criteria and stop
  rules, the first firing after the diff CSS and BEFORE any export work.
- Mark [P] only where tasks touch genuinely disjoint files.
- The full suite must pass above the 7379 baseline at the end.
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
1. Numeric drift — every artifact must agree on the declared figure and the
   decomposition must sum to it. Verify by RUNNING the declaration parser regex,
   not by reading: it takes the LAST match in the file, and prose near any other
   number silently becomes the declaration. That trap fired three times on slice 1.
2. Requirement-to-task coverage, both directions, reported separately for
   explicit citation and content coverage.
3. Anything inherited from slice 1 that does not actually apply here.
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

Slice 1's shipped artifact is one commit old on this branch and is the precedent
for every shared mechanism. Copy its export routine and its four-site currency
guard rather than reinventing them.

Known hazards, carried forward from slice 1 and already paid for once:
- The test suite is NOT read-only. validate-plugin-payload.py runs the real
  payload builder, so every suite run rewrites dist/**. Restore with
  git show HEAD:<path> > <path> and never git add -A after a suite run.
- Expect an intermediate red from the moment the artifact exists until the
  catalog flip AND the payload regeneration. On slice 1 that was three families
  and eight failures, not one. Any failure outside the known families is real.
- Running --layer 4 alone overcounts failures against a full run.
- Naming a token in a CSS comment to explain its absence fails the rule's own
  search.
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

- [ ] Post: Doctor Extension Check
- [ ] Post: Verify Implementation
- [ ] Post: Verify Tasks Phantom Check
- [ ] Post: Code Review
- [ ] Post: Integration Suite
- [ ] Post: Reviewability Diff Gate
- [ ] Post: Self-Review
- [ ] Post: UAT Runbook Generation
- [ ] Post: PR Body Generation
- [ ] Post: PR Creation
- [ ] Post: Review Remediation
- [ ] Post: Retrospective

**The pull request bases on `art-003-final-pr-template-set`, never on `main`.**

Slice 1's independent review found a defect that a green suite could not see: the
artifact's title disagreed with its catalog entry in case, so every export opened
with the wrong value. **Check that agreement explicitly here** — nothing asserts
it, and this template writes the same header line.

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

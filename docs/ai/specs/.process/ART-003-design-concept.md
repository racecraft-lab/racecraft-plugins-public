---
topic: "Final-PR template set: pr-writeup, annotated-diff, flowchart"
slug: "art-003-final-pr-template-set"
date: "2026-08-12"
mode: "setup"
spec_id: "ART-003"
source_input:
  type: "topic"
  ref: "docs/ai/specs/html-artifacts-technical-roadmap.md § ART-003: Final-PR Template Set"
question_count: 12
stop_reason: "natural"
---

# Design Concept: Final-PR template set

> **Source:** `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-003
> **Date:** 2026-08-12
> **Questions asked:** 12
> **Stop reason:** natural — every branch on the queue resolved, no new critical branches opened

## Goals

- Port three delivery templates as branded single-file SPAs ready for the
  implement stage's post-implementation generation: `pr-writeup`,
  `annotated-diff`, `flowchart`.
- **Split into three vertical slices, one template per PR** (Q1). Each slice
  ships one template, its manifest status flip, and its own fill-region test
  rows. Each lands in warn, none in block, and no exception pragma is needed.
- **Stack the three PRs in roadmap order** (Q8): `pr-writeup` from `main`,
  `annotated-diff` cut from slice 1, `flowchart` cut from slice 2. Roadmap order
  front-loads the tightest budget, so a failure of the size lever surfaces on
  PR 1 rather than PR 3.
- Hold each port to the line multiplier its budget allows, by keeping the
  upstream mechanism and dropping upstream sections that map to no fill slot
  (Q3).
- Ship every fill region with representative fictional sample content, held to
  the minimum that demonstrates the shape (Q11).
- Correct the roadmap's ART-003 reviewability declaration to the three-slice
  budget in the scaffold commit, before any slice branch is cut (Q12).

## Non-goals

- Generation logic and the ready flip — ART-010's scope, per the roadmap.
- The UAT walkthrough template — ART-009's scope; it is repo-authored, not an
  upstream port.
- Any export affordance on `flowchart`. Its entry declares `exports: []` and a
  click discloses detail in-page rather than producing anything durable (Q7).
- Amending `SPA-CONTRACT.md`, `brand-kit.css`, `theme-toggle.html`, the signal
  vocabulary, or any catalog value other than each entry's own `status`. A port
  changes exactly one catalog value (Q7).
- Per-line objections on `annotated-diff` — objections attach per hunk (Q6).
- A severity tag on every annotation. Severity is optional and marks findings
  only (Q9).

## Key size arithmetic (carried into Plan)

ART-002 is the only realized measurement of this work class. Its slice 1 shipped
two templates and measured **1494 reviewable LOC**, a hard block, forcing a
mid-implement re-slice (`docs/ai/specs/.process/ART-002-workflow.md:1495`).

Derived model, from ART-002's realized figures:

```text
reviewable ≈ (upstream_lines × M) − 458 canonical block lines
ART-002 realized M ≈ 2.2
```

| Slice | Template | Upstream | Upstream lines | M to clear 800 | Projected |
|---|---|---|---|---|---|
| 1 | `pr-writeup` | `17-pr-writeup.html` | 595 | ≤ 2.11 | ~750 (warn) |
| 2 | `annotated-diff` | `03-code-review-pr.html` | 638 | ≤ 1.97 | ~780 (warn) |
| 3 | `flowchart` | `13-flowchart-diagram.html` | 395 | ≤ 3.19 | ~410 (warn) |

All three upstream files verified present on `anthropics/html-effectiveness`
`main` (HTTP 200, checked 2026-08-12). None is vendored in this repository.

The setup gate is a **declaration checker**, not a tree measurement
(`speckit_pro_runner/helpers/read_only.py:967`). It reads the last number
matching "reviewable LOC" in its target, so a stale declaration passes
indefinitely. This is why Q12 corrects the roadmap before the stack exists.

## Design Tree (Q&A log)

### Q1. How should ART-003 be sliced, given ART-002's realized measurement?

**Branch:** Slice sizing

**Recommended answer:** Three slices, one template each.

> The estimator returned `estimated_loc: 455`, `status: warn`,
> `suggested_slices: 2`. ART-002's realized data is stronger evidence than the
> forward guess: two templates measured 1494. One template per PR is the only
> configuration in this feature's history that stays inside the contract, and it
> avoids an exception pragma whose three valid classes (`refactor`, `infra`,
> `upgrade`) none honestly describe net-new template work.

**Alternatives offered:**
- Two slices, `pr-writeup` then diff + flowchart: mirrors ART-002's own 2+2
  shape, but slice 2 projects to ~1600 and blocks.
- One slice, accept the block: what the roadmap currently declares; ~2350 LOC
  against an 800 threshold, roughly 3x over.

**User's answer:** Three slices, one template each (Recommended).

---

### Q2. What lever brings `annotated-diff` under the 800 block?

**Branch:** Slice sizing — the tightest slice

**Recommended answer:** Cap the anchor content.

> The shipped file is a template, not a finished artifact. The fill-region
> test's `MINIMUM_ITEMS` is 2, so two hunks — one annotated, one clean —
> is sufficient and provably so. Real diffs arrive at generation time in
> ART-010. This caps authored markup directly rather than hoping the estimate
> was wrong.

**Alternatives offered:**
- Split `annotated-diff` across two PRs: horizontal, and the contract's
  status/file-presence rule forces the file to claim `shipped` while incomplete.
- Accept a block on that slice: same exception-class problem as Q1.

**User's answer:** Cap the anchor content (Recommended).

**Note:** This decision generalizes to all three templates. Its interaction with
ART-002's "sample content in every slot" precedent was surfaced and resolved in
Q11.

---

### Q3. How faithful should each port be to its upstream source?

**Branch:** Porting fidelity

**Recommended answer:** Keep the mechanism, drop non-stage sections.

> ART-002's recorded model
> (`docs/ai/specs/.process/ART-002-workflow.md:460`): port the interaction
> mechanism and structure, restyle entirely to brand tokens so no upstream color
> survives, drop upstream sections that map to no fill slot, author fresh what
> the stage needs. ART-002 dropped ten upstream regions and authored three fresh
> on exactly this rule. It is also the lever that holds each port under its
> multiplier.

**Alternatives offered:**
- Full-fidelity port, trim only if the gate blocks: the shape ART-002 took
  implicitly, which discovered a 1494 block mid-implement.
- Minimal re-implementation, upstream as inspiration: weakens the attribution
  header's "modified derivative" claim, which validation checks for agreement
  with the catalog entry.

**User's answer:** Keep the mechanism, drop non-stage sections (Recommended).

---

### Q4. What is `pr-writeup`'s slot inventory?

**Branch:** Fill regions — inventory

**Recommended answer:** Six slots; `FLOOR` pins the roadmap's four.

> The roadmap names four sections; the manifest entry shipped in ART-001
> promises two more ("what it deliberately leaves out, and how it was
> verified"). Ship all six so the manifest stays true, but keep the hardcoded
> `FLOOR` literal sourced from the roadmap alone — ART-002 recorded that
> rationale, and the comment at `tests/speckit-pro/unit/test-artifact-fill-regions.py:81`
> states the floor traces to the roadmap "and to nothing else". The other two are
> still bound both ways by the test's R2/R3 inventory agreement.

Slots: `motivation`, `before-after`, `file-by-file`, `implementation-notes`
(roadmap-sourced, and the `FLOOR` entry), plus `non-goals`, `verification`
(manifest-sourced, bound by R2/R3).

**Alternatives offered:**
- Six slots with `FLOOR` pinning all six: simpler to read, but the floor literal
  would draw from two documents and break its own comment.
- Four slots, roadmap only: cheapest, but breaks the shipped manifest promise.

**User's answer:** Six slots, FLOOR pins the roadmap's four (Recommended).

**Precedent confirming the pattern:** `module-map.html` already ships five slots
while `FLOOR["module-map"]` names only `module-graph`.

---

### Q5. What does the `implementation-notes` slot render from ART-012's record?

**Branch:** Cross-spec interface — ART-012

**Recommended answer:** Only the non-None entries, in append order.

> ART-012's record is exhaustive and additive, with a `None` entry per
> uneventful task (`speckit-pro/skills/speckit-autopilot/references/phase-execution.md:1020`).
> A reader of a PR writeup wants the deviations, not the roll call. Document
> order is the record's only ordering signal, and a retry that appended a second
> entry under the same task ID renders as two entries, because ART-012 calls that
> correct history rather than a defect.

Declared source: `specs/<feature>/.process/implementation-notes.md`.

**Alternatives offered:**
- Mirror the record verbatim including `None`: faithful, but ART-002 ran 46
  tasks and most entries would read `None`.
- A prose summary the authoring agent writes: interposes agent judgment, and the
  export obligations forbid content the reader could not inspect.

**User's answer:** Only the non-None entries, in append order (Recommended).

---

### Q6. At what granularity does a reader attach an objection on `annotated-diff`?

**Branch:** Reader-side mechanism — exports

**Recommended answer:** Per hunk, reusing ART-002's mechanism.

> An inline keyboard-reachable disclosure plus a labeled textarea on each hunk,
> with exports walking the non-empty notes and carrying each hunk's anchor. That
> is the exact pattern ART-002 recorded for `implementation-plan` and
> `module-map` (its Q4), so a reviewer meets one interaction across the gallery.
> It makes `hunks` a `LIST_SLOT`, which the two anchor hunks from Q2 satisfy.

**Alternatives offered:**
- Per line: matches how PR review works, but multiplies markup on the template
  holding the tightest multiplier.
- One field for the whole diff: the export obligations require the conclusion to
  name the location it attaches to, and a single field cannot.

**User's answer:** Per hunk, reusing ART-002's mechanism (Recommended).

---

### Q7. What does a click do on `flowchart`, given `exports: []`?

**Branch:** Contract tension — declared read-only vs "clickable"

**Recommended answer:** Reveals step detail in-page; nothing leaves.

> Clicking a node discloses that step's description and its failure mode beside
> the diagram. The reader is learning the flow, not deciding anything, so
> `exports: []` stays an honest declaration rather than a forgotten affordance.
> It also keeps the port legal: `SPA-CONTRACT.md:62` allows "two embedded
> blocks, one new artifact file, and exactly one catalog value", and
> `SPA-CONTRACT.md:67` fixes that value as `status`.

**Alternatives offered:**
- Selects a step and exports the selection: honest about what the reader
  produces, but flipping `exports` is a second catalog value and therefore a
  contract amendment rather than a port.
- Drop clickability: unambiguously read-only, but the roadmap names clickability
  as the template's distinguishing feature and ART-004 already ships
  `svg-illustrations` for static vector diagrams.

**User's answer:** Reveals step detail in-page; nothing leaves (Recommended).

---

### Q8. How should the three PRs be branched?

**Branch:** Execution topology

**Recommended answer:** Stacked, in roadmap order.

> All three slices append to the same two literals — the manifest's consecutive
> entry block, and the `FLOOR` / `LIST_SLOTS` dicts at
> `tests/speckit-pro/unit/test-artifact-fill-regions.py:85` and `:99`. Stacking
> removes the conflict entirely, since each branch already contains the prior
> rows, and it is ART-002's proven model. Roadmap order front-loads the tightest
> budget.

**Alternatives offered:**
- Stacked, smallest template first: proves the pattern cheaply, but `flowchart`
  has the most headroom, so clearing it proves nothing about the real
  constraint.
- Three independent branches from `main`: independent merge schedules, at the
  cost of a three-way conflict on both shared literals.

**User's answer:** Stacked, in roadmap order (Recommended).

---

### Q9. How do "margin annotations" and "severity tags" relate?

**Branch:** Annotation model

**Recommended answer:** Severity is optional on an annotation; closed set when
present.

> An annotation explains a hunk; a severity tag marks the ones that are
> findings. Explanatory annotations carry none. When present the value comes
> from `blocking`, `major`, `minor` — the vocabulary this repo already reviews
> in (root `AGENTS.md` Code Review Rules; ART-002's own review reported "1
> blocking, 0 major, 2 minor"). The tag renders as text, never as color alone:
> ART-002's review found three color-only meaning carriers.

**Alternatives offered:**
- Severity mandatory with an informational level: uniform, but invents a
  vocabulary term this repo does not use.
- Free-form labels: the contract closes every other vocabulary it defines, and
  an open set means the Layer 4 test can assert nothing about a tag.

**User's answer:** Severity is optional; closed set when present (Recommended).

---

### Q10. Where does a reviewer attach a question on `pr-writeup`?

**Branch:** Reader-side mechanism — exports

**Recommended answer:** Per section, same widget as the diff's objections.

> Each of the six slots carries the disclosure-plus-textarea a reviewer already
> met on `implementation-plan`, `module-map`, and now `annotated-diff`. One
> interaction across the gallery, and every question arrives naming the section
> it attaches to, which is what the ART-008 sweep needs to route it.

**Alternatives offered:**
- Per section plus one general field: more faithful to how review works, at the
  cost of a seventh widget and a second export shape.
- One field for the whole writeup: drops the location the export obligations
  require.

**User's answer:** Per section, same widget as the diff's objections
(Recommended).

---

### Q11. What content do the fill regions carry on disk?

**Branch:** Correction — conflict surfaced between Q2 and ART-002's precedent

> Raised explicitly because Q2's chosen preview asserted fill regions ship
> "empty on disk", which cannot hold: ART-002's Q3 recorded that every slot
> ships representative fictional sample content, and the Layer 4 test's
> `MINIMUM_ITEMS` requires two real items in a list slot.

**Recommended answer:** Sample content in every slot, held to the demonstrating
minimum.

> This is the reading that satisfies both constraints. A list slot ships exactly
> the two items the test requires; a state-bearing element ships one instance
> per state; prose slots ship one short fictional paragraph. Every slot
> non-empty, none expansive.

**Alternatives offered:**
- Sample content only where the test forces it: smallest file, but the manual
  `file://` render check ART-003 owes as UAT evidence would inspect a skeleton.
- Rich uncapped sample content, ART-002 style: the specific thing that drove
  ART-002 to 1494 LOC.

**User's answer:** Sample content in every slot, held to the demonstrating
minimum (Recommended).

---

### Q12. Where does the corrected three-slice budget get written?

**Branch:** Declaration hygiene

**Recommended answer:** Correct the roadmap in this scaffold commit.

> Scaffold already edits the roadmap to mark ART-003 In Progress, so the budget
> correction lands in the same commit, before any slice branch is cut. The gate
> then reads a true declaration from the first run, and because the edit
> precedes the stack there is nothing for the three PRs to conflict over.

**Alternatives offered:**
- Each slice PR corrects its own figure: tracks reality per slice, but the gate
  reads a stale 285 through the whole of slice 1's planning — exactly ART-002's
  failure window.
- Leave the roadmap, declare per slice in `plan.md`: the roadmap then carries a
  figure wrong by roughly 8x for any later reader.

**User's answer:** Correct the roadmap in this scaffold commit (Recommended).

## Decisions recorded without a question

These were settled by precedent or by the contract, with no live uncertainty
worth an interview turn.

- **Upstream sourcing.** Fetch the three upstream files read-only at implement
  time from `anthropics/html-effectiveness` (`main`), keep them outside the
  repository tree in the session scratchpad, and never stage upstream bytes.
  ART-002's recorded protocol (`ART-002-workflow.md:1313`). Commit only branded
  derivatives.
- **Flowchart drawing mechanism.** Upstream 13 uses inline SVG with a
  `viewBox="0 0 620 920"` (~100 lines of SVG) plus a ~96-line script, and no
  `<canvas>` element. Keep that mechanism and restyle it with brand tokens, per
  ART-002's Q6.
- **Fill-region grammar.** Paired HTML comment markers
  `FILL:<slot>:START` / `FILL:<slot>:END`, with the slot inventory in an in-file
  header comment using the exact labels `Slot:` / `Fills:` / `Source:`
  (ART-002 Q1, Q2; enforced at `test-artifact-fill-regions.py:130`).
- **Export failure path.** Clipboard access can be refused over `file://`; on
  failure the artifact reveals the text in a selectable field. Success is
  reported in text, not by color or animation alone. Exports derive from live
  state at invocation. All mandated by `SPA-CONTRACT.md:372`.
- **Typeface token.** The heading token is `--rc-font-display`, never
  `--rc-font-heading` — an undefined custom property fails silently.
- **Meaning-bearing borders.** `--rc-border-subtle` must never carry meaning;
  use `--rc-border-strong`.
- **Attribution header.** Five exact labels, and the upstream file named must
  equal the entry's `source.file`.
- **Release payload.** Gallery files ship in the plugin payload; account for the
  generated-artifact contract (`scripts/refresh-release-artifacts.py`) in each
  slice's Declared File Operations.

## Open Questions

- **What:** The full slot inventories for `annotated-diff` and `flowchart`. Q4
  fixed `pr-writeup`'s six and Q6 fixed `hunks` as a `LIST_SLOT`, but the
  remaining slot names, their granularity, and their source artifact per slot
  are not yet pinned.
  **Why deferred:** ART-002 resolved the equivalent question in a dedicated
  Clarify session rather than in grill-me, on the stated ground that slot names
  must not be invented before the upstream sources are read
  (`ART-002-workflow.md:373`). The upstream files are fetched at implement time,
  so the same sequencing applies.
  **Suggested next step:** Clarify Session 1 per slice, after the upstream
  source for that slice is fetched.

- **What:** The exact markdown and prompt payload structure for `pr-writeup`'s
  questions export and `annotated-diff`'s objections export.
  **Why deferred:** Q6 and Q10 fixed the attachment point and the anchor
  requirement; the serialized shape is a Plan-phase detail.
  **Suggested next step:** Resolve in Plan, reusing ART-002's "walk non-empty
  notes with item anchors" shape.

- **What:** Whether `flowchart` needs a `LIST_SLOT` for its nodes.
  **Why deferred:** Depends on the slot inventory above. Q7 settled that a click
  produces nothing durable, so there is no export anchor forcing addressability;
  `LIST_SLOTS` may legitimately carry no `flowchart` row.
  **Suggested next step:** Decide alongside the slice-3 slot inventory in
  Clarify.

- **What:** Whether the `~750 / ~780 / ~410` per-slice projections survive
  contact with the real ports.
  **Why deferred:** They are derived from ART-002's realized 2.2x multiplier,
  which is a two-template sample.
  **Suggested next step:** Re-measure and re-declare at each slice's Plan phase.
  ART-002's lesson is that the gate will not catch a stale declaration for you.

## Recommended Next Step

Setup has already run (this is setup mode). The scaffold command writes the
workflow file and the SPEC-MOC marker next, then corrects the roadmap's ART-003
reviewability declaration per Q12.

Then run:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-003-workflow.md
```

Slice 1 (`pr-writeup`) only. Slices 2 and 3 are cut from their predecessor after
each prior PR is open, per Q8.

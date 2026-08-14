# Research: Annotated Diff — Slice 2

Phase 0 output. Every number below was measured on this branch on 2026-08-13,
against files this branch already carries. Nothing here is estimated from a
multiplier, and nothing is carried forward from slice 1 without being re-measured
against this slice's actual needs.

`spec.md` has no open clarification markers: three Clarify sessions closed all
three. So this document resolves no requirement. It records the **evidence behind
the plan's ceilings**, which is the thing a reviewer cannot reconstruct from
`plan.md` alone and the thing an implementer needs in order to hold them.

---

## 1. The measuring instrument

**Decision**: reuse the instrument recorded verbatim in slice 1's
`specs/art-003-final-pr-template-set/quickstart.md`. Write no second one.

**Rationale**: two instruments measuring the same thing in different units make
every cross-slice comparison unreadable, and the instrument is the only thing
that makes a ceiling holdable. It partitions a gallery artifact into the two
canonical blocks and the three authored kinds, and its `css + js + markup` sums
to `authored` exactly, so a line is never counted twice.

**Re-calibrated against all five shipped templates**, this branch, 2026-08-13:

| Template | authored | css | js | markup |
|---|---|---|---|---|
| `spec-explainer` | 315 | 169 | 0 | 146 |
| `pr-writeup` | 735 | 227 | 334 | 174 |
| `module-map` | 1002 | 448 | 293 | 261 |
| `code-approaches` | 1025 | 471 | 298 | 256 |
| `implementation-plan` | 1221 | 661 | 277 | 283 |

`pr-writeup`'s row is the basis for every figure in this document. It is one
commit old, was built to the same contract, and is the only realized measurement
of this work class.

**Alternatives considered**: a committed test asserting the ceiling. Rejected for
three reasons recorded in `plan.md`, the strongest being that FR-042a fixes this
slice's change to shared validation at exactly three literals.

---

## 2. CSS — what carries from slice 1, and what does not

**Decision**: carry-over is **195** of slice 1's 227 authored CSS lines.

**Rationale**: measured by block span in
`speckit-pro/artifact-gallery/templates/pr-writeup.html`, not estimated.

| Block | Span | Lines | Carries |
|---|---|---|---|
| Page chrome — `body`, `.page`, `header`, `h1`, `h2`, `p`, `.eyebrow`, `.note` | 483–552 | 70 | yes |
| `ul.points`, `ul.points li` | 553–561 | 9 | **no** |
| Before/after comment, `.ba`, `.ba .panel`, `.ba .panel p` | 562–584 | 23 | **no** |
| `details`, `summary`, `details .body`, `details .body p` | 585–614 | 30 | yes |
| Objection and export chrome — label, fields, controls, status, fallback | 615–708 | 94 | yes |
| **Total** | 483–708 | **227** | **carry-over 195** |

Each dropped block is counted with the blank line that separates it from the
next, because removing a block removes its separator. The two together are 32
lines, and 227 − 32 = 195.

**Why each drop is safe.** `ul.points` styles a bulleted list; this artifact
ships none, because its two regions are a header and a list of hunks and its
prose is two muted sentences. `.ba` styles the two-panel before/after comparison;
`spec.md` names no such region, and the spec's own inheritance note says the
two-panel comparison is one of the things that explicitly does **not** carry over
from slice 1.

**Why `details` still carries even though the hunk items are not disclosures.**
In slice 1 that rule set served two uses — `file-by-file`'s items and the
question controls. Here it serves one, the objection control, at the same cost.
That is also reduction lever 4 in `plan.md`: writing a second disclosure rule set
would be the largest avoidable cost in C2.

**Alternatives considered**: taking slice 1's 227 whole and adding diff CSS on
top. Rejected — it would have declared 32 lines that will not be written, which
inflates the figure and hides the diff CSS's true cost inside a rounding.

---

## 3. CSS — what the diff needs, enumerated one rule at a time

**Decision**: **79** new lines, itemized rather than estimated.

| Rule or block | Lines | Note |
|---|---|---|
| Comment: why the diff is styled the way it is | 5 | every other block in slice 1's authored CSS carries one |
| `.hunk` — the item frame | 8 | strong border, radius, raised surface, padding |
| `.hunk > h3` — path and line range | 7 | outside the scroll container, per FR-019d |
| `.diff` — the scroll container | 9 | `overflow-x: auto`, and the box it needs to read as one |
| `.diff-row` — the three-cell grid | 6 | line number, marker, code, in document order (FR-019c) |
| `.diff-row .ln` | 7 | `user-select: none`, right-aligned, muted, fixed minimum width |
| `.diff-row .mk` | 5 | fixed-width cell so the marker column stays a column |
| `.diff-row .code` | 5 | `white-space: pre` |
| `.diff-row.add`, `.diff-row.del` | 8 | shade reinforcement, from audited surface tokens |
| Comment: the annotation, and the severity rule that must not branch | 4 | FR-019f is the rule a later editor is most likely to undo |
| `.ann` — the annotation frame | 8 | strong left border, sunken surface, padding |
| `.sev` — one rule for all three words | 7 | no selector branches on which word it is |
| **Total** | **79** | |

**Rationale for the disagreement with Clarify's 64.** Clarify enumerated eight
items and reached 64. This list has twelve. The two extra kinds are the comment
blocks, which are house style throughout slice 1's authored CSS and which FR-032a
makes worth writing deliberately, and the two shade rules, which Clarify's list
did not name. Nothing was added beyond those.

### What the brand kit already supplies, so it is never written twice

Verified by reading `speckit-pro/artifact-gallery/brand-kit.css` rather than
assumed:

| Need | Already in the kit | Cost here |
|---|---|---|
| Monospace typeface for diff rows | `--rc-font-mono` token, and a `code, kbd, pre, samp` rule that applies it | 0 |
| Link styling for the jump links | an `a` rule | 0 |
| A visible focus indicator on each finding | a focus-visible rule whose selector list already includes `[tabindex]:focus-visible` | 0 |
| FR-037's reduced-motion suppression | a reduced-motion block | 0 |

That last row is the one worth stating twice: each finding carries
`tabindex="-1"` so that a fragment navigation moves focus to it, and the kit's
focus rule already binds `[tabindex]`. So FR-034 and FR-036 are satisfied with
zero authored CSS and zero authored JavaScript.

### The shade rules are the honest edge of this figure

FR-019 requires the row state to be carried by a character in a fixed position
and permits colour to reinforce it. The kit ships **no audited add/remove colour
pair**: its only red is `--rc-danger-text`, a text token, and it has no green.
Reinforcement here is therefore a surface *shade* rather than a hue — which is
also why it is reduction lever 1 in `plan.md`. Dropping both rules costs the
artifact nothing the spec requires and saves 8 lines.

**Alternatives considered**: porting upstream's own diff colouring. Rejected by
FR-018a — those values are outside the kit's audited set and the convention they
encode is the one FR-019 forbids.

---

## 4. JavaScript — the transplant, function by function

**Decision**: **342** lines, built from slice 1's routine with four functions
swapped for `module-map`'s. Every line already exists in a shipped file.

**Rationale**: the two requirements pull the routine apart, and neither shipped
file satisfies both. FR-023c needs the items derived from the anchors present in
the region at the moment of invocation, which only `module-map` does. FR-027
through FR-027b need the four-site currency guard, which only `pr-writeup` has.

Measured function spans, both files, 2026-08-13:

| Function | `pr-writeup` | `module-map` | This slice takes |
|---|---|---|---|
| `textOf` | 5 | 5 | slice 1 |
| `labelOf` | — | 12 | **`module-map`** |
| `featureLine` | 19 | 22 | slice 1 |
| `questionOf` / `noteOf` | 9 | 6 | slice 1, renamed to the objection noun |
| `refresh` | 15 | 13 | slice 1 |
| `mount` | 48 | 42 | **`module-map`** |
| `mountAll` | — | 18 | **`module-map`** |
| `recorded` | 18 | 15 | **`module-map`** |
| `payload` | 22 | 20 | slice 1 |
| `successMessage` | 13 | 12 | slice 1 |
| `announce` | 20 | 14 | slice 1 — **the guard lives here** |
| `reveal` | 15 | 12 | slice 1 — **the guard lives here** |
| `copy` | 30 | 26 | slice 1 |
| `wire` and the mount tail | 31 | 13 | slice 1, with the loop replaced by one `mountAll()` call |
| Prologue: constants, literals, the currency-token comment | 88 | 63 | slice 1, less its six-name slot array |

The arithmetic from slice 1's measured 334:

| Change | Lines |
|---|---|
| Six-name `SLOTS` array and its seven-line comment (15) → one slot constant and one list-id constant with a shorter comment (5) | −10 |
| `mount(slot)` 48 → `mount(anchorId)` 42 | −6 |
| Add `labelOf(anchor)` | +12 |
| Add `mountAll()` (18), drop the four-line inline mount loop, add the one-line call | +15 |
| `recorded()` 18 → 15 | −3 |
| **Total** | **342** |

### The three lines of `module-map` that must not be copied

`module-map`'s `announce(message)`, `reveal(text)`, and `copy(kind)` are 14, 12
and 26 lines against slice 1's 20, 15 and 30. The whole of that 23-line
difference **is** the currency guard. Taking `module-map`'s derivation and
`module-map`'s settle path together would reproduce, byte for byte, the defect
FR-027c records in all three pre-slice-1 templates: a rejected first copy
announces a failure that did not happen, and the first kind's payload lands in
the fallback field after the second kind copied successfully.

FR-027b fixes the shape at four check sites: the entry to the status write and
the deferred callback it schedules, and the entry to the fallback reveal and the
deferred callback *it* schedules. Those four sites are inside slice 1's
`announce` and `reveal`, which is why both come across whole rather than merged.

### Two things that cost nothing

**Jump links need no JavaScript.** A fragment navigation moves focus when the
target is focusable, so `tabindex="-1"` on each finding is the entire mechanism
for FR-034. FR-019e forbids scripting it.

**The item-anchor derivation needs no string concatenation into a selector.**
`module-map`'s `mountAll` reads its container by a pinned id, walks
`list.children`, and collects the ones carrying an `id`. No value from the
document is ever concatenated into a selector string, which is what FR-023c
requires.

**Alternatives considered**: writing a fresh routine that satisfies both
requirements directly. Rejected — the routine is the highest-risk code in the
artifact, it is the part slice 1's independent review scrutinised hardest, and
two shipped implementations already contain every line of it. Reinventing it
spends budget to lower confidence.

---

## 5. Markup — built bottom-up

**Decision**: **122** lines, of which 110 are enumerated and 12 are a stated
margin.

| Component | Lines | Basis |
|---|---|---|
| Doctype, `<html>`, `<head>`, `<meta>` | 4 | slice 1, unchanged |
| Attribution header | 8 | slice 1's, same five labels, upstream filename changed to `03-code-review-pr.html` |
| Slot inventory | 4 | two slot lines plus two comment delimiters; slice 1 spent 9 on seven slots |
| Style, script, body and html closing plumbing | 8 | measured on slice 1 |
| `</head>`, `<body>`, `.page`, `<main>` and separators | 7 | measured on slice 1 |
| `header` and the `feature-header` region | 11 | slice 1's 714–724, same shape, including FR-020e's invented-content sentence |
| FR-019c's standing sentence naming the three markers | 4 | one muted paragraph, outside every fill pair |
| `hunks` section chrome | 9 | section, heading, jump links, the grouping element outside the pair, two FILL markers |
| Hunk 1, annotated | 18 | item, heading, scroll container, seven rows, one annotation carrying a severity |
| Hunk 2, clean | 13 | item, heading, scroll container, six rows, the words that say it is deliberately clean |
| Export region | 24 | slice 1's 829–852, copied, noun changed |
| **Subtotal** | **110** | |
| Enumeration margin | 12 | see below |
| **Total** | **122** | |

**Why a stated margin rather than a tighter number.** Slice 1's markup
enumeration was wrong twice in the same direction: it missed a third
`file-by-file` item and it missed the export region's hidden-reveal line, and
both were caught at Checklist rather than at Plan. A bottom-up enumeration of
markup misses lines; saying so and reserving 12 is more honest than reporting 110
and revising it later.

**The objection controls cost no markup.** FR-021 builds them at load. That is
also why FR-043 requires the export region to ship hidden and be revealed by the
routine: with scripting unavailable, controls that cannot act would otherwise sit
on screen offering an action nothing can perform.

**The grouping element shape is taken from `module-map`**, which places
`<div class="modules" id="module-list">` outside the marker pair and its items
inside it, each carrying `id="modules-<slug>"`. FR-020c requires exactly that
arrangement, and `mountAll` reads the container by that pinned id.

---

## 6. The three validation literals

**Decision**: three literals in
`tests/speckit-pro/unit/test-artifact-fill-regions.py`, matching slice 1's count.

| Literal | Value | Why this and nothing else |
|---|---|---|
| Floor row | `"annotated-diff": ("hunks",)` | FR-041 binds the floor to the roadmap. The roadmap describes this template as "unified diff with margin annotations, severity tags, jump links" and names no other region. `feature-header` is chrome and is deliberately absent, exactly as it is absent from slice 1's floor row. The shape matches `code-approaches` and `module-map`, both single-slot rows |
| List-slot row | `"annotated-diff": ("hunks",)` | FR-042: `hunks` is the artifact's only list slot |
| Source member | `"git-diff"` | FR-042a |

**The floor and the list-slot row carry the same value, which looks redundant and
is not.** The module's own comment records why: floor membership proves only that
a region of that name exists, never that its items are addressable. `module-map`
is the inverse case — `modules` is a list slot and is *not* in the floor.

**`git-diff` joins a closed set of six filenames.** Both Clarify analysts agreed
a member was required, because FR-017 admits no exception and none of the six
existing members can honestly claim a hunk's rows: the planning artifacts are
written before the code, `tasks.md` names tasks, and `implementation-notes.md` is
a per-task deviation record. They split on the literal, and the dissent is
recorded rather than smoothed: all six existing members are filenames with
extensions, and `git-diff` fullmatches the slot-name grammar while no existing
member does. It was resolved toward honesty — no filename is honest here, and
`diff.patch` would name a file no phase of this repository writes. Membership is
tested by plain string equality with no filename shape enforced, so an
extensionless value is legal, and slot names and source values are read by
different code paths, so nothing can confuse them mechanically.

**The annotations' source is deliberately not in `Source:`.** It is the
self-review block the workflow log writes, whose filename varies per spec. FR-042b
puts that obligation in the `hunks` line's `Fills:` value instead, which holds the
change at three literals and keeps `Source:` naming only things that exist as
named artifacts.

---

## 7. The plan-phase estimator, verified blind

**Decision**: record `estimate-reviewable-loc`'s result as a known-blind
diagnostic, never as reassurance.

**Rationale**: verified for this slice against
`speckit-pro/speckit_pro_runner/helpers/read_only.py`:

- `projected = production * 40`. The helper opens no file it counts.
- `is_production_file` returns true only for a path beginning `src/`, `app/`,
  `lib/`, or `scripts/`, or ending `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`,
  or `.sql`. All three declared entries fail both tests, including the `.py`
  validation module.
- `greenfield = all(NEW or excluded)`. Two of three entries are `MODIFIED` and
  neither is a generated path, so `greenfield` is false and the reported
  thresholds read `warn: 400, block: 800`.

So `production = 0`, `projected = 0`, and `status` reads `pass`. The parser also
requires each entry to be exactly a list marker, `NEW` or `MODIFIED`, and one
path with nothing after it — so an inline comment on an entry line silently drops
that entry.

---

## 8. The declaration parser, verified by running it

**Decision**: verify by execution at Plan, not by reading, and again at Analyze.

**Rationale**: the gate reads

```text
(?:projected reviewable loc|reviewable loc)[^0-9]{0,40}([0-9]+)
(?:projected production files|production files)[^0-9]{0,40}([0-9]+)
(?:projected total files|total files)[^0-9]{0,40}([0-9]+)
(?:primary surface|primary surfaces)[^:\n]*:\s*([A-Za-z/ ,_-]+)
```

taking the **last** match for each number and the **union** of every surface
match. Two consequences a reader will not see by eye:

- Forty *non-digit* characters is a wide window. A sentence mentioning the phrase
  anywhere near any number becomes the declaration if it is last.
- The surface reader is a `findall` that unions every match. A second
  `Primary surface:` line with a different value raises the surface count and
  produces a warning that reads like a scope problem and is a formatting one.

Run against both artifacts after this plan was written, both files return one
match per phrase:

| File | reviewable LOC | production files | total files | primary surfaces |
|---|---|---|---|---|
| `spec.md` | 750 | 1 | 13 | `docs/process` |
| `plan.md` | 750 | 1 | 13 | `docs/process` |

One near-miss was found and removed rather than left to the ordering: the
Constitution Check originally wrote its thresholds as digits beside the phrase
`total files`, which produced a second match of `15`. It survived only because
the Declared Figures block came later. The thresholds are now spelled in words.

**`spec.md` was re-declared from 755 to 750 at this phase**, which is what its own
Reviewability Budget section instructs. The decomposition, the sensitivity table,
and the withdrawn claim about the export routine were updated with it, so no
artifact carries a stale figure.

---

## 9. Decisions taken at Plan that the spec left open

| Decision | Rationale | Alternatives rejected |
|---|---|---|
| Four checkpoints, not three | Slice 1 ran three and its uncovered component — the export routine — was the one that overran, by 46 lines and 16% | Three checkpoints, matching slice 1. Rejected on slice 1's own realized data |
| M1 at 150 authored CSS lines | Page chrome 70 plus diff CSS 79 is 149. The number is the arithmetic, not a round figure borrowed from slice 1, though it lands one line from slice 1's M1 | A ceiling on the diff CSS alone. Rejected — the instrument reports total authored CSS, and a ceiling stated in units the instrument does not report cannot be checked |
| Declare the ceiling sum, 750, rather than the measurement, 738 | The declared figure is the number the slice commits not to exceed; declaring the raw measurement leaves no room for an enumeration that misses a line, and slice 1's markup enumeration missed eight | Declaring 738. Rejected — it would report an overrun for landing at 745, which is inside the plan |
| No `contracts/` directory | FR-030a binds this artifact's literals to slice 1's contract, which is present on this branch, and FR-030d pins the two authored leads in `spec.md` | Authoring a second contract. Rejected — it forks a pinned literal set across two documents, adds a second document that dangles at archive, and spends the tightest headroom in the feature on prose |
| The catalog title is compared as a string, not read | Slice 1 shipped a title that differed from its catalog entry in case; the whole suite passed and only independent review caught it. FR-010a and SC-008 require the comparison | Reading both and judging them equal. Rejected by the spec, and by the evidence |

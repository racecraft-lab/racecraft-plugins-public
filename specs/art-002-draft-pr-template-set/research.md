# Phase 0 Research: Draft-PR Template Set (ART-002)

Every question the Technical Context could have left open was already closed —
by the grill-me interview before the specification, then by three Clarify
sessions after it. This file records the decisions that govern implementation,
each with the reason it was chosen and the alternative it beat, so a reviewer can
audit the reasoning without reconstructing it from three source documents.

No `NEEDS CLARIFICATION` marker survived into the Technical Context. The two Open
Questions the design concept deferred to this phase are both answered below: slot
names in D2, and whether the upstream drawings survive branding in D6.

---

## D1 — Duplicate the capture-and-export behavior; do not abstract it

**Decision.** Three artifacts carry near-identical behavior — mount a control per
item, read live state, build two export texts, copy with a selectable fallback —
and each carries its own copy. No shared file, no build step, no generator.

**Rationale.** This is less a choice than an observation about what the contract
leaves available. `SPA-CONTRACT.md` states the single-file rule as "no build step,
no bundler, no preprocessor, no post-processing" and "no sibling asset — no linked
stylesheet, script file, image file, or data file next to the artifact". Those two
sentences remove every mechanism that could deduplicate the code. What remains is
duplication.

The constitution then calibrates rather than decides: "Three similar lines of code
are better than a premature abstraction" (VI, YAGNI). And the duplication is
smaller than it looks. Two of the three — `implementation-plan` and `module-map` —
share the objection shape and differ only in their item noun and slot name. The
third, `code-approaches`, is a different shape: one selection across a group plus
one optional reason, with no per-item disclosure at all. So the real duplication
is one near-copy.

What **is** shared is the specification. The literal export wordings, the
four-coordinate item reference, the single clipboard-failure message, and the
empty-state text per export kind are pinned once in
[`contracts/export-payload-contract.md`](./contracts/export-payload-contract.md),
and each template is verified against that one table. Three implementations can
drift in style; they cannot drift in behavior.

**Alternatives considered.**

- *A shared script file beside the artifacts.* Rejected — it is a sibling asset,
  which the single-file rule prohibits outright, and it would also break the
  "opens straight from a filesystem" property the whole gallery is built on.
- *A build step that inlines one common source into each artifact.* Rejected —
  prohibited by name in the same rule.
- *A generator that stamps the routine into each file at authoring time.*
  Rejected twice over: it is a build step under another name, and generation
  logic is ART-007's scope, which the design concept's Non-goals place outside
  this feature explicitly.

---

## D2 — Fill regions are paired HTML comments; the inventory is one in-file comment

**Decision.** Each region an authoring agent later fills is delimited by
`<!-- FILL:<slot>:START -->` … `<!-- FILL:<slot>:END -->`, each pair appearing
once with its start before its end. Each template documents its own slots in a
single comment placed immediately after the attribution header, one line per slot
reading `Slot: <name> | Fills: <what fills it> | Source: <source artifact>`. The
21 slot names are fixed in FR-015.

**Rationale.** The marker-pair convention is the one this gallery already
validates twice, for `BRAND-KIT` and `GALLERY-HEAD`, so the once-and-ordered pair
checks are a pattern the repository has already got right. A comment is inert: it
survives any restyling, it carries no rendering cost, and the standard library
parses it directly.

Placement is load-bearing rather than cosmetic. The gallery scanner takes the
**first** parser-recognized comment carrying any attribution element as the
attribution header. An inventory placed before the header that happened to mention
a licence or the upstream repository would be read as the header instead. So the
inventory goes after, and carries none of the header's labels or literals.

**Alternatives considered.**

- *`data-fill` attributes on elements.* Rejected — a second slot convention beside
  the marker-pair one, and a filler would have to rewrite element internals rather
  than replace a delimited region.
- *`<template>` and `<slot>` elements.* Rejected — that machinery exists for
  runtime shadow-DOM composition, and ART-007 writes static HTML, so none of it
  would be used.
- *A central `FILL-REGIONS.md` in the gallery.* Rejected — it adds a shared
  foundation file that ports are kept away from, and it can drift from the
  templates it describes.

---

## D3 — The validation floor is a literal pinned outside the artifacts, and it is a subset

**Decision.** The Layer 4 module holds a hardcoded per-template list of the
regions the roadmap names, and asserts each is present as a delimited slot. It is
a floor, not an equality: a template may carry more slots than the floor names,
and the both-ways inventory agreement binds the remainder.

**Rationale.** The repository has already written this rule down in the gallery
scanner's own words: a literal is pinned outside the artifact it validates,
because "a set derived from the file under validation asserts only that the file
equals itself". An equality would also be wrong on the merits — several templates
legitimately carry slots the roadmap never named, `feature-header` among them,
and an equality would fail them for being complete.

Every floor entry traces to the roadmap's ART-002 scope and to nothing else, so a
reader can tell why each one is there. That single-source rule is what makes the
literal auditable, and it is the reason D4 exists.

**Alternatives considered.**

- *Derive the expectation from the file under test.* Rejected — it proves only
  self-consistency.
- *Assert equality rather than a subset.* Rejected — it fails complete templates
  and would have to be widened every time a template gains a legitimate slot.

---

## D4 — The anchor requirement gets its own assertion, not a floor entry

**Decision.** That every repeated item inside a list slot carries its stable
anchor is checked by a separate assertion (FR-036a), not by adding `modules` to
the FR-036 floor.

**Rationale.** Clarify escalated this and closed it 3/3 at round two. Two
independent reasons, either sufficient:

1. **The floor cannot verify it even in principle.** Floor membership proves that
   a region named `modules` exists. FR-016 is an interaction requirement about
   whether that region's items are individually addressable. A presence check
   cannot see the difference, so widening the floor would buy the appearance of
   coverage and none of the substance.
2. **It would make the literal unauditable.** Every other floor entry traces to
   the roadmap. An entry sourced from a different requirement blends two source
   documents into one list, and a hardcoded literal that accretes entries from
   mixed rationales is a recognized test smell.

The repository has already made this exact call once: the gallery scanner's
`check_c8` exists because a count check and a one-directional membership check
cannot see a coordinated change on both sides of a relationship, and the fix
there was a new separate check closing against an independent source — explicitly
not a widened literal.

**Alternatives considered.**

- *Fold `modules` into the module-map floor.* Rejected for both reasons above.
- *Leave it to the manual acceptance pass alone.* Rejected — the anchor is a
  static property of the shipped file, so a static check can hold it. The manual
  pass keeps the parts that genuinely need a browser: keyboard reachability,
  focus visibility, and clipboard behavior.

---

## D5 — The template's own behavior builds every reader-input control, at load

**Decision.** Each capture affordance is created by the template's own inline
script when the document loads, mounted onto the stable anchor its item already
carries, and inserted immediately after that anchor. A fill region ships as inert
content plus per-item anchors, and never as control markup.

**Rationale.** Two analysts reached this independently during Clarify. The
decisive fact is scope: FR-016 is tagged `[US1] [US4]`, both delivered by this
feature, so deferring the control to ART-007 would ship artifacts with no working
capture at all and break US1's own independent test.

The pattern is already shipping twice inside the canonical head block — the theme
control is built with `createElement` and wired with `addEventListener`, and the
brand mark is mounted onto an empty opt-in element. The gallery scanner already
parses script-built markup through the same prohibited-construct checks as
document markup, so building in script buys no exemption and needs none.

Inserting immediately after the anchor keeps tab order and reading order following
visible order without a positive tab index, which FR-033 forbids anyway. Building
all the controls of one list from a single routine is what makes them identified
consistently (FR-017a), which is a property that is hard to hold when each is
written out by hand. And confining every value a later agent writes to a text
position or a plain data attribute is the standard injection-safety line, and the
same one the contract draws for generated artifacts.

**Alternatives considered.**

- *Write the controls as static markup inside each fill region.* Rejected — it
  puts control markup inside a region ART-007 replaces wholesale, so filling a
  slot would delete the capture affordance.
- *Defer the controls to ART-007.* Rejected — it strands two user stories this
  feature owns.

---

## D6 — Each upstream drawing keeps its mechanism; only the styling is ported

**Decision.** Neither drawing is re-authored. Both use the same mechanism —
hand-authored inline vector markup with a view box, rectangle, path, line, and
text primitives, with arrowheads defined once and referenced by same-document
fragment. The port normalizes how color is applied and changes nothing else.

**Rationale.** This was the design concept's second Open Question, recorded at
moderate confidence because the upstream files had not been opened. Clarify
session 3 opened all four and answered it: both drawings survive branding, and
neither carries a prohibited construct.

The two differ only in how color is applied, and the port normalizes that to
classes in both:

- **module-map** already styles through classes, so restyling is a token swap in
  the rules it has, plus one rule for the arrowhead.
- **implementation-plan** hardcodes presentation attributes on every shape. Those
  need not be rewritten — a presentation attribute carries no specificity, so any
  rule overrides it. The port adds class hooks and styles through them, and must
  not use one blanket selector, because a blanket rule would flatten the two-tier
  text hierarchy and the inverted node the drawing deliberately distinguishes.
- **Arrowheads** each need their own selector: a marker renders in its own context
  and does not inherit paint from the element referencing it.
- **No upstream color value survives.** Every one is an unaudited pairing, and no
  upstream source carries a theme-aware rule at all, so a retained value would
  leave the drawing unreadable in the dark theme.

**Alternatives considered.**

- *Standardize both on freshly authored inline vector markup.* Rejected — sharp
  and self-contained, but the coordinate math makes the slot harder for ART-007's
  agent to refill, and re-authoring a working drawing is risk with no return.
- *Standardize both on boxes laid out in HTML and CSS.* Rejected — easiest to
  regenerate from a plan's structure, but crossing arrows are awkward without
  vector markup, and it would discard two layouts already proven upstream.

---

## D7 — Two sequential pull requests; not stacked, not one

**Decision.** Slice 1 is `implementation-plan` and `spec-explainer` with their two
status flips and the whole Layer 4 module. Slice 2 is `code-approaches` and
`module-map` with theirs, branched from a state that already contains slice 1.

**Rationale.** Both slices are end-to-end and independently reviewable: templates,
their catalog rows, and passing checks. Slice 1 leads because the draft-PR stage
routes its two templates unconditionally, so nothing downstream works without
them, while slice 2's two are routed only when their signal is present.

**Alternatives considered.**

- *One pull request.* Rejected — the advisory size estimator returned a warning at
  an estimated 560 lines, and this plan's own derivation puts the combined figure
  near 1040 authored lines, which would cross the 800-line block threshold.
- *Stacked branches.* Rejected for their known synchronization friction in this
  repository. A fresh branch after merge starts from a catalog that already
  carries slice 1's flips, with nothing to reapply and nothing to rebase.
- *A different split — the three exporting templates against the read-only one.*
  Rejected — it puts three of the four in one pull request and defeats the point,
  and it separates templates by implementation shape rather than by whether the
  stage routes them, which is the axis a reviewer cares about.

---

## D8 — Slice 2 edits no test file

**Decision.** The Layer 4 module lands complete in slice 1, with the floor and the
list-slot literals naming all four templates. Each per-template case is
conditioned on that template's catalog `status`. Slice 2's two status flips turn
the remaining cases on with no edit to the module.

**Rationale.** It follows from D3's literals being pinned from the roadmap, which
names all four templates from the start. Conditioning on `status` rather than on
file presence is the right key because the contract already binds the two in both
directions — a file exists if and only if its entry reads `shipped` — so `status`
is a sufficient and cheaper signal, and the existing scanner owns the direction
this one relies on.

A consequence worth stating because it changes slice 2's file list: slice 2 changes
no tracked `.md`, `.py`, or `.sh` file under the test tree, so it needs no docs
reference regeneration there. That should be verified by running the generator and
confirming no diff, not assumed.

**Alternatives considered.**

- *Ship half the module in each slice.* Rejected — it would split one file across
  two pull requests, and the second half would be a test change with no behavior
  change to justify it.
- *Key the cases on file presence instead of `status`.* Rejected — it duplicates a
  check the gallery scanner already owns, and it would pass in the one state the
  contract calls a failure, an artifact present without its flip.

---

## D9 — Generated payload artifacts are declared, separately, and excluded from the budget

**Decision.** The payload copies, the installed-cache mirrors, and the proof
snapshots are inventoried in the plan under their own heading, outside the block
the reviewability estimator reads.

**Rationale.** They must be declared, because FR-039 requires each slice to account
for the generated artifact contract and because the routing contract reads a
plan's file operations as the evidence for the `brownfield_change` signal. They
must be excluded from the reviewable surface, because a reviewer does not read a
byte-for-byte mirror — a difference in one is a build defect, not a review target.

Placing them under a separate `##` heading achieves both at once, because the
estimator's parser stops at the next such heading. The mechanical reason to be
deliberate here: the estimator's own exclusion rule covers `dist/**` and
`.process/` automatically but does **not** cover the installed-cache mirror paths
under the test tree, so mixing them in would misreport both the file count and
the greenfield determination.

**Alternatives considered.**

- *List them in the main block.* Rejected — it would inflate the declared file
  count with roughly thirty machine-written entries and misreport the surface a
  human reviews.
- *Omit them entirely.* Rejected — FR-039 requires accounting for them, and a
  reviewer meeting thirty unexplained changed files in the diff has no way to tell
  a refresh from a hand edit.

---

## D10 — Reviewable lines count authored lines only

**Decision.** The projection counts what a reviewer reads. It excludes the 458
lines of canonical block each artifact embeds — 318 from `BRAND-KIT`, 140 from
`GALLERY-HEAD` — and it excludes generated mirrors.

**Rationale.** The contract says validation compares the marked regions byte for
byte and that "the markup and styling you write outside the markers are yours and
are never compared". A byte-pinned region is not a review target: the only two
outcomes are identical, which needs no reading, and different, which is a
validation failure that names the artifact and the block. Counting 1832 embedded
lines across four artifacts as reviewable would make the number describe the
copying rather than the work.

The calibration point is ART-001's own single-file artifact: 766 lines total,
both blocks embedded, so 308 authored. That is the order of magnitude the four
templates are estimated against.

**Alternatives considered.**

- *Count every added line in the diff.* Rejected — it would make any artifact that
  obeys the single-file rule unshippable, including the ones ART-001 already
  shipped, which shows the measure is wrong rather than the design.

---

## D11 — Capture and export interaction details

**Decision.** Fixed as follows, and the literal strings live in
[`contracts/export-payload-contract.md`](./contracts/export-payload-contract.md).

- An objection field starts **collapsed** behind a native disclosure whose control
  states in text whether that item currently carries a note.
- An export lists **only** the items the reader recorded against — no line, no
  placeholder, and no count for an item left empty.
- With nothing recorded, an export says so and says explicitly that the record is
  not an approval, in wording fixed per export kind.
- The `code-approaches` reason field is **optional**; an absent reason is named
  rather than omitted.
- A clipboard failure uses **one** message for every failure mode and asserts no
  cause, with the text revealed in a selectable, focusable field that receives
  focus. No deprecated second copy attempt is made.

**Rationale.** Each is a defense against a specific misreading. Always-revealed
fields would turn a document meant to be read into a form of five or six empty
boxes, against the reviewing operator's actual job. Emitting "no objection" for an
untouched item asserts an approval the reader never gave, and a trailing count of
untouched items is the same assertion in aggregate. The realistic misreading of an
empty export is approval, so denying it is part of the requirement rather than a
nicety. Requiring a reason would either strand the reader's real conclusion or
pressure filler text, and there is no submission to enforce it against. And the
artifact genuinely cannot distinguish a refused permission from an unfocused
document from a browser policy from an absent interface, so a message naming a
cause would be a guess presented as a diagnosis; a deprecated second attempt
returns an ambiguous result, and reporting an uncertain success is exactly what
the requirement forbids.

**Alternatives considered.** Revealed-by-default fields; exports listing every
item; a per-failure-mode message; a legacy copy fallback. Each rejected above.

---

## D12 — One capability-named Layer 4 module

**Decision.** `tests/speckit-pro/unit/test-artifact-fill-regions.py`, registered
at layer 4 in `tests/speckit-pro/suite-manifest.json`, standard library only.

**Rationale.** The repository's editing boundaries require a test filename to name
the durable capability it verifies and forbid coupling it to a temporary spec
identifier — a rule the code-review calibration treats as blocking. Fill-region
validation is the durable capability; ART-002 is the temporary identifier. Layer 4
is where unit coverage of repository tooling lives, and suite membership must be
declared rather than discovered.

It is a new module rather than an addition to `test-artifact-gallery.py` because
that file validates the contract's own shape — canonical blocks, catalog,
attribution, prohibited constructs, external references — and fill regions are a
convention this feature introduces on top of it. Keeping them apart means a
failure names which layer of the stack broke.

**Alternatives considered.**

- *Add the checks to `test-artifact-gallery.py`.* Rejected — it already runs to
  seven thousand lines across ten check groups, and merging a new convention into
  it blurs which document a failure traces to.
- *Name it for the spec.* Rejected — prohibited outright, and it would go stale
  the moment ART-003 ships templates the same checks cover.

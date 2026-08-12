# Phase 1 Data Model: PR Write-up Artifact

The artifact holds no database and no persisted state. Its "data model" is three
structures: the fill-region inventory an authoring agent reads, the export
payload a reviewer produces, and the two shared-validation literals that bind the
first to the tree.

---

## 1. The fill-region inventory

Seven regions. Six are reader-facing sections; `feature-header` is not a section
and is not pinned in the floor.

### Region table

| Slot | Reader-facing | In `FLOOR` | List slot | Grouping element | Source artifacts |
|---|---|---|---|---|---|
| `feature-header` | no | no | no | — | `spec.md` |
| `motivation` | yes | **yes** | no | — (prose) | `spec.md` |
| `before-after` | yes | **yes** | no | — (two fixed panels) | `spec.md, plan.md` |
| `file-by-file` | yes | **yes** | **yes** | **outside** the pair | `plan.md, tasks.md` |
| `non-goals` | yes | no | no | inside the pair | `design-concept.md, spec.md` |
| `verification` | yes | no | no | inside the pair | `spec.md, tasks.md` |
| `implementation-notes` | yes | **yes** | no | inside the pair | `implementation-notes.md` |

`FLOOR["pr-writeup"]` names the roadmap's four and no more, so the floor literal
keeps tracing to one document. R1 is a floor and not an equality: it explicitly
accepts a template carrying more slots than the floor names, and R2/R3 bind the
remaining three in both directions.

### Why `file-by-file` is the only list slot

List-slot membership is about item-level **addressability**, not repetition. Four
slots render repeated items; only one needs each item nameable by an exported
question.

`implementation-notes` must stay out, and this is decisive rather than
preferential. FR-019 requires two entries sharing a task identifier to both
render, because that is a retry and correct history. A per-item anchor derived
from that identifier would collide, and R5 rejects a duplicate anchor outright —
a fragment resolving to two items resolves to neither. A list-slot row would make
FR-019 unsatisfiable.

`verification` and `non-goals` stay out on the shipped precedent of `key-files`
in `module-map` and `goals` in `spec-explainer`: both render repeated items,
neither is a list slot, and both keep their grouping element inside the pair.

### Structural rules per region

- **Markers.** Exactly one pair, `FILL:<slot>:START` before `FILL:<slot>:END`.
- **Flat.** No pair encloses another, and each pair delimits a whole subtree —
  no element opens on one side of a boundary and closes on the other. R7 checks
  both, because a nested pair passes R2 and R3 while silently losing the inner
  region on the first fill of the outer one.
- **Headings live outside the pair** (FR-011e), so a fill replaces content and
  never the section title. This is what makes every exported coordinate except
  the feature-header identifiers undeletable by a fill — stronger than every
  shipped precedent, whose item anchors sit inside a fill region.
- **`file-by-file`'s grouping element sits outside the pair** so the container
  survives a fill. Every repeated item at the region's own top level carries a
  stable, unique anchor `file-by-file-<item-slug>` in kebab-case, and each item is
  an element requiring an end tag. The parser performs no implied closing, so an
  unclosed item would read as nested and vanish from the region's top level.
  `<details>` satisfies this, which is also what neutralised the optional-end-tag
  hazard rather than deferring it.
- **`implementation-notes` carries a standing intro outside its pair** (FR-019a):
  one sentence stating that only tasks with something to report appear, that they
  appear in the record's order, and that a retried task appears more than once.
  Outside is required rather than stylistic — the sentence is true of every fill
  rather than of this sample, so it must survive fills exactly as headings do.
  All six `section-intro` uses in `implementation-plan` sit outside their pairs.
  Contrast `spec-explainer`'s sample notice, which correctly sits *inside*
  `feature-header`'s pair because it describes the sample and should die with the
  fill.
- **Chrome outside every region.** The artifact's own kind carries
  `id="artifact-title"` and sits outside all seven pairs, so no fill can delete
  it. The two feature identifiers necessarily sit *inside* `feature-header`,
  because an export may carry nothing the reader could not see and a template may
  not hold feature-specific content outside a slot.

### The inventory comment

One HTML comment immediately after the attribution header, one line per slot,
reading `Slot: … | Fills: … | Source: …` in that order, with no pipe inside a
value. It carries **none** of the attribution header's labels or literals, so the
header stays the first comment a scanner recognises as one.

```text
Slot: feature-header | Fills: the feature identifier and its name; keep id="feature-id" on the identifier and id="feature-name" on the name, because both exports read them to name the change | Source: spec.md
Slot: motivation | Fills: one short paragraph saying why the change was made | Source: spec.md
Slot: before-after | Fills: the two panels comparing the behaviour before the change with the behaviour after it | Source: spec.md, plan.md
Slot: file-by-file | Fills: one item per changed file saying what it does; keep an id of the form file-by-file-<slug> on each item, because an exported question names it | Source: plan.md, tasks.md
Slot: non-goals | Fills: one item per thing the change deliberately leaves out | Source: design-concept.md, spec.md
Slot: verification | Fills: one item per check that was run, each stating its passed or pending state as a word rather than as a glyph | Source: spec.md, tasks.md
Slot: implementation-notes | Fills: one entry per task that reported something, in the record's order, with a retried task appearing more than once; or one sentence saying which case obtains when none did | Source: implementation-notes.md
```

Every `Source:` value is a member of the closed set once `implementation-notes.md`
is added. The set is bare filenames of per-feature SpecKit artifacts regardless of
directory, which `design-concept.md` already demonstrates.

The `implementation-notes` line carries both the filter and the empty case
because that line is the only agent-facing instruction the artifact holds for the
region. It costs nothing, since FR-014 already makes the line mandatory.

### Sample content

Non-empty everywhere, expansive nowhere. Prose regions ship one short paragraph.
A region holding a repeated list ships exactly the two items the validation
requires — except `implementation-notes`, which ships **three**, so the retry pair
can be shown **non-adjacent**, as a real re-run appends it. Two entries would
force a choice between showing distinct tasks and showing the retry, and an
adjacent pair would model the case wrongly. `implementation-notes` is not a list
slot, so no validation rule caps or floors its item count.

Every region uses the same invented feature, following `spec-explainer`, which
holds one across all of its regions.

### Notes rendering

Each entry is a **list item whose task identifier leads in bold**, inside a
grouping list that sits within the marker pair, following `goals` in
`spec-explainer`. Bold rather than a mono span: it is the named precedent, it
survives monochrome, and it adds no class and no CSS rule. The list item also
satisfies the end-tag requirement without a special case.

A retry pair gets **no** visual grouping and **no** derived attempt ordinal.
Grouping would be incorrect rather than merely costly: a serial re-run appends
after the intervening tasks' entries, so collapsing the pair would reorder the
record. An ordinal would assert a field the record does not carry.

The artifact ships **no** empty-state element. Nothing in it reads the record at
render time, so the template cannot distinguish "every task reported nothing"
from "no task recorded an entry" from "the record was unavailable" — and the
authoring agent can. The empty case is a fill obligation stating which of the
three obtains in one sentence.

---

## 2. The export payload

Both kinds serialize the same structure and differ in exactly one line. Neither
emits markdown syntax: the `markdown` kind names its **destination, not its
encoding**, and the ART-008 sweep reads the raw comment body where line structure
survives.

### Shape

```text
Artifact: <artifact title>
Feature: <feature id> <feature name>

<lead line for the kind>

<slot> / <section heading>  (#sec-<slot>)
<the reviewer's question>

<slot> / <section heading>  (#sec-<slot>)
<the reviewer's question>
```

Two spaces precede the parenthesis. The anchor is the `sec-<slot>` id the
section's heading already carries for its `aria-labelledby` — the gallery's
existing section-anchor convention, reused rather than invented.

### Collection

The routine collects from a **pinned list of slot names in document order**,
resolving each section by its `sec-<slot>` id directly, rather than walking a
container's children. Each item carries its own slot name. This survives a fill
that restructures a section, never depends on DOM order, and concatenates no
value into a selector string. It is also 19 lines cheaper than the shipped
precedent's container walk.

An export walks only the non-empty question fields. A section the reviewer
skipped contributes no line, no placeholder, and no count.

### Pinned literals

Fixed in `contracts/export-payload-contract.md`. Summarised here:

| Role | Value |
|---|---|
| prompt lead | `Act on each question recorded below. The value in parentheses is the anchor of the section it attaches to.` |
| markdown lead | `Questions recorded while reading this pull-request write-up.` |
| empty prompt | `No question was recorded. There is nothing here to act on. Do not treat this as approval.` |
| empty markdown | `No question was recorded. This record is not an approval.` |
| copy failed | `Copy failed. The text is in the field below. Select it and copy it by hand.` |
| feature fallback | `Feature: not named in this document` |

The failure message is **byte-identical** to the one the three shipped templates
already carry. The lead lines and empty-state bodies are authored fresh in this
artifact's own noun, "question", following the recorded per-template pattern —
the shipped templates already vary that noun between "objection" and "approach".

### Invocation currency

Each invocation carries a token compared against the current one when its copy
settles. A settle belonging to a superseded invocation changes no status text,
reveals no fallback text, and moves no focus. **Both** settle paths are guarded.
The synchronous refusal path and the no-clipboard-interface path stay unguarded
and say why: both run inside the same synchronous turn that issued the token, so
neither can be stale.

---

## 3. The shared-validation literals

Three, and no fourth.

| Literal | Value | Requirement |
|---|---|---|
| `FLOOR["pr-writeup"]` | `("motivation", "before-after", "file-by-file", "implementation-notes")` | FR-038 |
| `LIST_SLOTS["pr-writeup"]` | `("file-by-file",)` | FR-039 |
| `SOURCE_ARTIFACTS` | gains `"implementation-notes.md"` | FR-039a, FR-017 |

The floor row is what brings this template into the per-template universe at all.
The module resolves that universe by intersecting the catalog with its floor, so
a shipped template the floor does not name is never parsed — a port with no
regions and no inventory would pass every check green.

---

## 4. The catalog entry

Exactly one value changes.

| Key | Before | After |
|---|---|---|
| `status` | `planned` | `shipped` |

Everything else on the entry is read-only input: `id` is `pr-writeup`, `stage` is
`final-pr`, `source.file` is `17-pr-writeup.html` (which the attribution header
must name, and agreement is checked), and `exports` is `["prompt","markdown"]`
(taken as given from ART-001 and not renegotiated — changing it would be a second
catalog value and therefore a contract amendment rather than a port).

The artifact path is **derived, not stored**: the consumer composes
`<gallery dir>/templates/<id>.html`. There is no path key to keep in step.

---

## 5. Traceability

| Requirement group | Lands in |
|---|---|
| FR-001 – FR-010 (single-file contract, canonical blocks, attribution) | `speckit-pro/artifact-gallery/templates/pr-writeup.html` |
| FR-011 – FR-020a (regions, inventory, sample content, notes rendering) | same file, plus the inventory comment |
| FR-021 – FR-029 (question capture, exports, fallback, empty state) | same file, script region |
| FR-029a (pinned literals) | `specs/art-003-final-pr-template-set/contracts/export-payload-contract.md` |
| FR-030 – FR-036 (accessibility) | same file, style region and markup |
| FR-037 (one catalog value) | `speckit-pro/artifact-gallery/manifest.json` |
| FR-038, FR-039, FR-039a (three literals) | `tests/speckit-pro/unit/test-artifact-fill-regions.py` |
| FR-040 (suite green) | `python3 tests/speckit-pro/run-all.py` |
| FR-041 (payload) | `python3 scripts/refresh-release-artifacts.py` |
| FR-042 (manual render evidence) | `quickstart.md`, recorded as UAT evidence |

# Data Model: Annotated Diff — Slice 2

Phase 1 output. The artifact has no database, no API, and no persisted state.
What it does have is a set of structures that three separate readers must agree
on: the reviewer reading the page, the authoring agent that fills the regions
later, and the validation that binds the template. This document fixes those
structures and their rules, and closes with the requirement-to-file map the pull
request's traceability section is built from.

Every rule below traces to a requirement in `spec.md`. Where a rule is checkable
by a command rather than by reading, the command is in `quickstart.md`.

---

## 1. The artifact

One HTML file at `speckit-pro/artifact-gallery/templates/annotated-diff.html`.

| Property | Value | Rule |
|---|---|---|
| File stem | `annotated-diff` | equals the identifier its catalog entry declares (FR-001) |
| Displayed title | `Annotated Diff` | **byte-identical** to the catalog entry's `title`, including case (FR-010a) |
| Title placement | outside every fill region, carrying `id="artifact-title"` | so no fill can delete it (FR-010a) |
| Sibling assets | none | no linked stylesheet, script, image, or data file (FR-002) |
| External references | exactly one, the brand typeface request inside the head block | (FR-008) |
| Canonical blocks | two, verbatim with their markers, once each, start before end | `BRAND-KIT` 318 lines, `GALLERY-HEAD` 140 lines (FR-005, FR-006) |
| Prohibited constructs | none present | base element, scheme-relative reference, event-handler attribute, `srcdoc`, form with a submission target, `ping` (FR-007) |
| Skills-directory references | none | so the shipped copies stay byte-identical on both platforms (FR-010) |

**The title rule is the one with no automated backstop.** Nothing in the suite
compares an artifact's displayed title against its catalog entry's `title`.
Slice 1 shipped a mismatch in case, every export opened with a value the catalog
did not carry, the whole suite passed green, and only independent review caught
it. SC-008 requires a string comparison, not a reading, and FR-046 requires the
result recorded with the acceptance evidence.

### The attribution header

An HTML comment near the top of the file, before the inventory.

| Field | Value |
|---|---|
| Upstream repository | the repository the contract names |
| Upstream file | `03-code-review-pr.html` — the `source.file` the catalog entry declares |
| License | the contract's value |
| License text | `UPSTREAM-NOTICE.md` |
| Modified derivative | yes, with the re-skin stated |
| Copyright | the upstream line, verbatim |

Five exact labels plus the copyright line (FR-009). The inventory that follows
must carry **none** of these labels or literals, so the header stays the first
comment a scanner recognises as one (FR-016).

---

## 2. The fill regions

Exactly two ship (FR-011). Both are delimited by one pair of HTML comment
markers, `FILL:<slot>:START` before `FILL:<slot>:END`, flat, each pair enclosing
a whole subtree with no element crossing a boundary (FR-012, FR-013).

| Slot | Kind | Contains | Source |
|---|---|---|---|
| `feature-header` | single | the feature identifier, its name, and the sentence declaring the content invented | `spec.md` |
| `hunks` | **list** | one item per diff hunk | `git-diff` |

**No third region ships.** A `diff-summary` slot was proposed and rejected on
evidence: the claim that every shipped template pairs `feature-header` with a
short orienting region is false, `code-approaches` has none, and the roadmap
names jump links as a feature rather than a region. FR-034 discharges that
obligation with links inline in `hunks`.

### What sits outside every marker pair, and why

A fill replaces everything between a pair. Four things must survive one, so all
four sit outside:

| Element | Why outside | Rule |
|---|---|---|
| The artifact title | an export opens with it; a fill that deleted it would silently rename the artifact | FR-010a |
| The sentence naming the three diff markers | blank-means-context is a learned convention; a fill that deleted it would leave the diff unreadable to a first-time reader | FR-019c |
| The live status region | a status region a fill could delete would make every later failure silent | FR-028 |
| The `hunks` grouping element | the routine reads it by a pinned id to find the items; a fill must replace the items, not the container | FR-020c |

The two feature identifiers are the deliberate opposite case. `id="feature-id"`
and `id="feature-name"` sit **inside** `feature-header`, because an export must
name the feature, may carry nothing the reader could not see, and a template may
not hold feature-specific content outside a slot. The obligation to preserve them
across a fill is therefore recorded in the inventory, which is the only
agent-facing instruction the artifact holds (FR-011a).

---

## 3. The slot inventory

One HTML comment immediately after the attribution header, one line per slot,
reading `Slot: … | Fills: … | Source: …` in that order, with no pipe inside a
value (FR-014).

```text
Slot: feature-header | Fills: … | Source: spec.md
Slot: hunks | Fills: … | Source: git-diff
```

| Rule | Requirement |
|---|---|
| Slot names are filename-safe kebab-case and unique | FR-015 |
| Every documented slot has a region, and every region is documented | FR-015 |
| Every `Source:` value is a member of the closed set | FR-017 |
| The inventory carries none of the attribution header's labels | FR-016 |

**Three obligations ride in the `hunks` line's `Fills:` value**, because it is the
only place an authoring agent will read them and because each must survive the
first fill (FR-017a, FR-042b):

1. Keep a stable unique anchor on every hunk item.
2. A hunk carrying no annotation says so in words.
3. A finding's content comes from the self-review block the workflow log writes.

The third is there rather than in `Source:` because the log's filename varies per
spec, unlike the six per-feature artifacts whose names are identical in every
feature directory. Putting it in `Source:` would require inventing a filename.

---

## 4. A hunk

One contiguous span of the diff. **Exactly two ship** — one carrying at least one
annotation, one carrying none — so a reader sees both states (FR-020).

| Property | Rule |
|---|---|
| Element | requires an end tag; the fill-region parser performs no implied closing, and an unclosed item reports as nested and vanishes from the region's top level (FR-020c) |
| Anchor | `hunks-<file-path-slug>-l<start>`, unique, kebab-case, at the region's own top level (FR-020c, FR-023b) |
| Heading | every item carries one; the export reads its label from the first heading (FR-023f) |
| Visible label | the file path and the new-file line range |
| Rows | three cells in document order: line number, state marker, code (FR-019c) |
| Scroll container | `overflow-x: auto` with `tabindex="0"`, a role that accepts a name, and an accessible name naming the hunk (FR-019d) |
| Header placement | the heading is a heading, **outside** the scroll container (FR-019d) |
| Annotations | zero or more, each immediately after that hunk's rows, inside the same item (FR-019e) |
| Objection field | exactly one, mounted immediately after the item at load (FR-021, FR-023d) |

### The anchor derivation

```text
hunks-<slug>-l<start>
```

`<slug>` is the **whole file path** with every run of characters outside `a-z0-9`
replaced by one hyphen and the edges stripped. `<start>` is the hunk's new-file
start line, prefixed by `l`.

Three properties decide the form:

| Property | Why |
|---|---|
| The whole path, not the file stem | two files sharing a name cannot collide. Slice 1's `file-by-file` could use a stem only because it had one item per file and no line dimension |
| The start line, not the range | the end moves with the context count while the start does not, and FR-020c requires a stable anchor |
| The `l` prefix | a numeric segment cannot be read as another path segment |

**A collision cannot arise from this derivation.** Two hunks in one file are
ordered and non-overlapping, so their new-file start lines differ; two hunks in
different files differ in the path segment. The artifact therefore renders
nothing special for a collision and carries **no runtime disambiguation** — a
rename would emit a fragment naming an id no element carries and put a value in
the export the reviewer never saw, against FR-025. A cross-file collision is a
fill defect the validation rejects by name.

**A caption must not be the slug's source.** Verified empirically: `git diff` and
`diff -up` disagree on the function-context caption for the same input, so a
caption-derived slug's uniqueness would depend on which tool produced the diff.

### Row states, without colour

| Cell | Content | Rule |
|---|---|---|
| Line number | the new-file line number, `user-select: none` | so a copied row pastes as a valid unified-diff line (FR-019c) |
| State marker | a literal `+`, `-`, or space, **present as text in the document** | never CSS generated content, which some engines place on the clipboard and others do not (FR-019c) |
| Code | the row's text | |

Colour may reinforce and must never carry (FR-019). Two limits are recorded
rather than solved: `+` and `-` are punctuation and are not announced at default
screen-reader verbosity, and the clipboard exclusion is not uniform — Chrome
still carries unselectable text on the paste-and-match path — so FR-019c requires
the acceptance evidence to include an **actual paste** of one added, one removed,
and one context row rather than an assertion.

### The clean hunk

A deliberate state, not a half-filled one (FR-020b). It says in words that it
carries no annotation, rather than leaving the space an annotation would occupy
empty. No selector distinguishes it: the words are the carrier.

---

## 5. An annotation

A comment attached to a hunk, sitting immediately after that hunk's rows inside
the same item.

| Property | Rule |
|---|---|
| Attachment | by **position and text together** — it follows the rows and opens by naming the row or rows in words (FR-019e) |
| Severity | present only when the annotation is a finding; one of `blocking`, `major`, `minor`, as a **word** (FR-019a) |
| Severity rendering | a **single style rule shared by all three words, with no selector branching on which word it is** (FR-019f) |
| Severity label | a fixed label precedes the word, naming it as a severity, so a text-only reading cannot mistake it for emphasis (FR-019f) |
| Finding target | each finding carries a stable `id` and `tabindex="-1"` (FR-019e) |
| Jump links | ordinary same-document links; focus is moved by the platform, never by script (FR-019e, FR-034) |

**An absent severity must not render as a fourth level below `minor`.** An
explanatory annotation carries no severity element at all, which is what makes
the absence unreadable as a rank.

**Why the no-branch rule is stated as a rule and not a preference.** A selector
branching on which word it is, is exactly where colour, weight, or fill re-enters
as the ranking carrier — the defect the requirement exists to prevent, and the
one upstream commits.

**Individual rows are not addressable.** Every anchored coordinate this artifact
defines is a hunk. Per-row fragments would add roughly thirty tab stops between
two hunks and satisfy no requirement (FR-019e).

---

## 6. A reviewer objection

Free text a reviewer attaches to one hunk. Never persisted; read from live state
at the moment an export is invoked (FR-026).

| Property | Rule |
|---|---|
| Control | a native disclosure plus a labelled text field, matching the shape `module-map`, `implementation-plan`, and slice 1 ship (FR-021) |
| Disclosure state text | states **in text** whether its hunk currently carries an objection (FR-021a) |
| State recomputation | on **every change to the field**, not once at mount and not only on the next toggle (FR-021a) |
| Field label | a visible label programmatically associated with the field; **placeholder text does not satisfy this** (FR-021a) |
| ARIA | **none** — no role, no `aria-expanded`, no `aria-pressed` (FR-021b) |
| Placement | immediately after the item it questions (FR-023d) |
| State words | `Objection on <label>: no note recorded`, reused byte-identically from the two shipped templates (FR-030e) |

The ARIA prohibition is stated as a prohibition because "match the shipped
pattern" reads as permission to add markup that looks more accessible and is
less so. The open and closed state is exposed natively, and the current HTML-ARIA
mapping does not permit those attributes on a `summary` acting as its parent's
summary; forcing a role has been observed to remove the exposed state rather than
add it.

---

## 7. The export payload

Two kinds, `prompt` and `markdown`, exactly as the catalog entry declares. One
control per kind, labelled by destination (FR-022).

### Structure

Both kinds serialize the same structure and differ in exactly one line
(FR-023a):

```text
Artifact: Annotated Diff
Feature: <feature id> <feature name>

<lead line for the kind>

<one blank-line-separated block per non-empty objection>
```

### The objection reference line

```text
<slot> / <item label>  (#<anchor>)
```

Two spaces before the parenthesis (FR-023b). This slice returns to the
**item-anchored** form the three older templates use, because it captures against
a repeated item rather than a whole section; slice 1's `sec-<slot>` form was the
exception.

### The literals

**Six reuse byte for byte**, because this slice's noun is already the contract's
noun and two shipped templates already capture objections (FR-030a):

| Literal | Count |
|---|---|
| Empty-state bodies, both kinds | 2 |
| Objection feedback messages | 3 |
| The clipboard-failure message | 1 |

Four more reuse verbatim outside the contract: the two disclosure state words,
and the summary and field-label templates.

**Two are authored fresh** (FR-030d), each varying from the shipped pair by its
noun alone:

| Kind | Lead |
|---|---|
| `prompt` | `Act on each objection recorded below. The value in parentheses is the anchor of the hunk it attaches to.` |
| `markdown` | `Objections recorded while reading this annotated diff.` |

**Neither kind emits markdown syntax.** The `markdown` kind names its
destination, not its encoding, and the downstream feedback sweep reads the raw
comment body where the line structure survives.

**No string literal in the script may name the local-file scheme** (FR-030c).
Feedback text says "opened from a filesystem" instead. This is a validation
requirement: the gallery scanner treats a script string literal opening with a
scheme and a colon, or carrying a scheme followed by two slashes, as an external
reference and fails the file.

### What an export carries, and what it must not

| Rule | Requirement |
|---|---|
| Only non-empty fields are walked | FR-023 |
| Each objection carries its hunk's anchor | FR-023 |
| Enough context to act on alone: the artifact, the change, the location | FR-024 |
| No conclusion the reviewer did not reach | FR-025 |
| No value the reviewer could not have inspected on screen | FR-025 |
| Derived from live state at the moment of invocation | FR-026 |
| When nothing was recorded: says so in text, and **denies that this is approval** | FR-030 |

---

## 8. The invocation token

The one piece of state the routine holds that is not read from the document.

| Property | Rule |
|---|---|
| Value | a counter; every invocation takes the next one |
| Comparison | the token an effect was issued against, compared to the current value |
| Scope | **by effect, not by path** (FR-027a) |
| Sites | **four** — the entry to the status write and the deferred callback it schedules, and the entry to the fallback reveal and the deferred callback *it* schedules (FR-027b) |
| A superseded settle | writes no status text, reveals no fallback text, moves no focus (FR-027) |
| Both settle directions | guarded, not only the rejection path (FR-027) |

**Why path scoping is not sufficient**, stated as a property of the routine
rather than a hypothesis about it: the status write is deferred behind a short
timer, because the region is cleared and rewritten so a repeated identical
message is announced a second time, and the focus move is deferred behind a
longer one. A path that decides synchronously therefore still **lands**
asynchronously, in a later turn, after a second invocation may already have
completed and re-hidden the field. Scoping by effect makes the exemption
unnecessary rather than merely safer: the synchronously-decided paths carry the
current token and pass the same check.

---

## 9. The failure path

| Step | Rule |
|---|---|
| 1 | Reveal the same exported text in a field the reader can select |
| 2 | Keep that field **focusable and not disabled**, give it an accessible name, and move focus to it |
| 3 | Report the single failure message |
| 4 | **Do not** report success |

All four are required (FR-029). Three further obligations, each already satisfied
by the shipped routine (FR-029a):

- **No second copy attempt** through any deprecated interface after the first
  fails; that attempt's result is ambiguous, and reporting an uncertain success is
  what the contract forbids.
- **Every invocation re-hides the fallback field before it attempts its copy**, so
  a later successful export never leaves an earlier failure's payload on screen
  beside a success message.
- **The browser console stays silent**, which means the rejection is handled
  rather than left to surface as an unhandled rejection.

The failure message is the **only** failure message, covers every failure mode,
and asserts **no cause** (FR-030b). The artifact cannot tell a refused permission
from an unfocused document from a browser policy from an absent interface, so
naming one would be a guess presented as a diagnosis.

---

## 10. The catalog entry

The routing row that already exists. **Exactly one value changes** across the
whole slice: this entry's `status`, from `planned` to `shipped` (FR-040).

| Field | Value | Changes |
|---|---|---|
| `id` | `annotated-diff` | no |
| `title` | `Annotated Diff` | no — and the artifact's title must equal it byte for byte |
| `category` | `code-review` | no |
| `stage` | `final-pr` | no |
| `trigger` | any of self-review findings, large diff | no |
| `source.file` | `03-code-review-pr.html` | no — the attribution header must name it |
| `exports` | `prompt`, `markdown` | no — one control each, and nothing else |
| `status` | `planned` → `shipped` | **yes, and only this** |

No other entry changes, and no shared foundation file is edited: not the contract
document, the brand kit, the head block, the signal vocabulary, or the export
vocabulary.

---

## 11. The validation binding

Three literals in `tests/speckit-pro/unit/test-artifact-fill-regions.py`:

| Literal | Value | Requirement |
|---|---|---|
| Floor row | `"annotated-diff": ("hunks",)` | FR-041 |
| List-slot row | `"annotated-diff": ("hunks",)` | FR-042 |
| Source member | `"git-diff"` | FR-042a |

**The floor row is what makes the validation non-vacuous.** The module resolves
its per-template universe by intersecting the catalog with its floor, so a
shipped template the floor does not name is never parsed at all — a port with no
regions and no inventory would pass every check green. SC-010 requires the
binding proved rather than assumed; `quickstart.md` carries the command.

The two rows carrying the same value is not redundancy. The module's own comment
records why: floor membership proves only that a region of that name exists,
never that its items are addressable. `module-map` is the inverse case — `modules`
is a list slot and is deliberately not in the floor.

The list slot's items are held to a **floor of two** anchored items. Here the
floor and this template's cap coincide at the same number, deliberately and for
independent reasons: the validation needs two to show a reader how a repeated
list renders, and the design concept caps this template at two because a hunk
carries diff rows rather than one line of prose and the two states this region
must demonstrate are exactly two (FR-020a).

---

## 12. Requirement-to-file map

The traceability source for the pull request. Three files carry the whole change.

| File | Requirements it satisfies |
|---|---|
| `speckit-pro/artifact-gallery/templates/annotated-diff.html` | FR-001 to FR-010a, FR-011 to FR-017a, FR-018 to FR-018b, FR-019 to FR-019f, FR-020 to FR-020e, FR-021 to FR-021b, FR-022 to FR-030e, FR-031 to FR-039, FR-043 |
| `speckit-pro/artifact-gallery/manifest.json` | FR-040 |
| `tests/speckit-pro/unit/test-artifact-fill-regions.py` | FR-041, FR-042, FR-042a, FR-042b |
| Generated payload under `dist/**` (regenerated, never hand-edited) | FR-045 |
| Suite run and manual render, recorded as evidence | FR-044, FR-046 |

| Success criterion | Where it is proved |
|---|---|
| SC-001, SC-002, SC-003, SC-005, SC-006 | the manual render, `quickstart.md` Part 2 |
| SC-004, SC-007 | the manual render, `quickstart.md` Part 2, Scenario B |
| SC-008 | a string comparison between artifact and catalog, recorded with the evidence |
| SC-009 | Layer 4 gallery scanner |
| SC-010 | the full suite, plus the non-vacuity command in `quickstart.md` Part 1 |
| SC-011 | the diff of `manifest.json` |
| SC-012 | the inventory read alone, against the regions the body delimits |
| SC-013 | the four measurement checkpoints, recorded in the pull-request body |

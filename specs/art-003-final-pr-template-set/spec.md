# Feature Specification: Final-PR Template Set — Slice 1, the PR Write-up Artifact

**Feature Branch**: `art-003-final-pr-template-set`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "Final-PR Template Set — slice 1, the PR write-up artifact. Scope this slice to ONE template: `pr-writeup`. Ship it as a branded, self-contained HTML artifact that states what a finished change does, what it deliberately leaves out, how it was verified, and what actually happened during implementation, and that lets a reviewer hand their questions back without retyping them from memory."

**Spec ID**: ART-003 (slice 1 of 3)

**Design Concept**: `docs/ai/specs/.process/ART-003-design-concept.md`

## Overview

ART-001 seeded a routing catalog that already promises a reader a Pull Request
Write-up: a document stating "what the finished change does, what it
deliberately leaves out, and how it was verified". The entry exists and reads
`planned`, so the promise is currently unbacked. This slice backs it.

The artifact is a template, not a finished document. It ships fictional sample
content in every region and a machine-readable inventory of the regions an
authoring agent will later replace. Filling it is ART-010's work, not this
slice's.

ART-003 is three vertical slices, one template per pull request, stacked in
roadmap order. This spec covers **slice 1 only**: `pr-writeup`.
`annotated-diff` and `flowchart` are separate specs off separate branches.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the finished change [US1] (Priority: P1)

A reviewer is asked to judge a finished pull request. They open `pr-writeup.html`
straight from the filesystem, with no server and no install, and read six things
about the change: why it was made, what it looked like before and after, what
each changed file does, what the change deliberately leaves out, how it was
verified, and what actually happened while it was implemented.

**Why this priority**: This is the artifact's whole reason to exist, and it is
the half that satisfies the catalog entry already shipped in ART-001. A reader
who can read the six sections has received value even if they never write a
question down. Every other requirement in this spec either serves this reading or
depends on it.

**Independent Test**: Open the shipped template from the filesystem with the
network unavailable. All six sections render with their sample content, the
browser console reports nothing, no load fails, and the theme control works. The
only visible difference from an online render is typeface substitution.

**Acceptance Scenarios**:

1. **Given** the shipped template on a local filesystem, **When** a reviewer
   opens it directly with no server running, **Then** the page renders in full,
   the browser console reports no error, and no content is missing.
2. **Given** the network is unavailable, **When** the same reviewer opens the
   file, **Then** every section stays completely readable and every control still
   operates; only the typeface substitutes.
3. **Given** the rendered page, **When** the reviewer looks for the change's
   motivation, its before/after, its file-by-file explanation, its non-goals, its
   verification, and its implementation notes, **Then** each is present as its own
   titled section carrying representative sample content.
4. **Given** the rendered page, **When** the reviewer switches the theme,
   **Then** both themes render every section legibly and no meaning is lost.
5. **Given** the implementation-notes section, **When** the reviewer reads it,
   **Then** each note appears under the task identifier it was recorded against,
   in the order the record appended them.
6. **Given** a reviewer using a keyboard alone, **When** they tab through the
   page, **Then** every interactive element is reachable in the normal focus
   order and carries a visible focus indicator.

---

### User Story 2 - Hand the questions back [US2] (Priority: P2)

Having read a section, the reviewer has a question about it. They attach the
question to that section, repeat for as many sections as they want, then copy
every question they wrote out of the page in one action: either as a pull-request
comment, or as an instruction to paste into a coding agent.

**Why this priority**: Without it the reading is stranded in a browser tab and
has to be retyped from memory, which is the failure the contract's export
obligations exist to prevent. It is P2 rather than P1 only because US1 delivers
standalone value first: this story depends on the six sections existing.

**Independent Test**: Type a question into two of the six sections, leave the
other four empty, and invoke each export control. Each export carries exactly the
two questions written, each naming the section it attaches to, and carries
nothing from the four empty fields.

**Acceptance Scenarios**:

1. **Given** any one of the six sections, **When** the reviewer opens its
   question control using the keyboard alone, **Then** a labelled text field
   appears and receives their typing.
2. **Given** questions typed into two sections and none in the rest, **When**
   the reviewer invokes an export, **Then** the exported text carries those two
   questions and no placeholder or empty entry for the other four.
3. **Given** any exported text, **When** the reviewer reads it away from the
   artifact, **Then** it names the artifact, the change it belongs to, and the
   section each question attaches to, so it can be acted on alone.
4. **Given** a reviewer who edits a question and immediately exports, **When**
   the export is produced, **Then** it carries the edited text, because it is
   derived from live state at the moment of invocation.
5. **Given** the browser refuses clipboard access, which is common over the
   local-file scheme, **When** the reviewer invokes an export, **Then** the
   artifact reveals the full text in a selectable field and says so in words
   rather than reporting success.
6. **Given** a successful copy, **When** the reviewer looks for confirmation,
   **Then** it is stated in text, not carried by color or animation alone.
7. **Given** the two export controls, **When** the reviewer reads their labels,
   **Then** each names its destination ("Copy as prompt", "Copy as Markdown")
   rather than the mechanism.

---

### Edge Cases

- **A section with no question.** Export walks only the non-empty fields. A
  section the reviewer skipped contributes nothing, not an empty heading.
- **No questions at all.** The reviewer invokes an export having written
  nothing. The artifact must not produce a document asserting a conclusion the
  reviewer never reached; it says in text that there is nothing to export.
- **Clipboard refused.** Covered by US2 scenario 5. Silence here is a defect,
  because the reviewer believes they have the text.
- **Storage refused for a local file.** The theme control keeps working for the
  session and reports no error. Persistence degrades, never the control.
- **Reduced motion requested.** Any motion this template adds is suppressed
  under that preference. The canonical blocks cover their own.
- **Two implementation notes under one task identifier.** A retry appended a
  second entry. Both render, in append order. That is correct history, not a
  duplicate to collapse.
- **An implementation-notes record with every entry uneventful.** The region
  renders only non-uneventful entries, so the shipped sample must still show a
  reader what a filled region looks like.
- **A reader on a monochrome screen or print.** Every distinction the artifact
  draws survives without color.
- **A brand typeface unavailable.** Heading rank still reads, because hierarchy
  rides on semantic level, size, and weight rather than on typeface identity.
- **Scripting unavailable.** US1 survives whole: all six sections, their sample
  content, the headings, and the standing intro are markup and stay readable. US2
  does not, and the degradation is uneven — the six question controls are built
  at load, so they simply do not appear, while the two export controls sit in
  markup and would remain on screen offering an action nothing can perform. A
  control that cannot act is worse than an absent one, because a reader who
  cannot see a result has no way to tell a broken copy from a silent one, and
  this is the same failure FR-028 exists to prevent arriving by a different road.
  The artifact MUST therefore ship the export region hidden and let the script
  reveal it, so the affordance appears only where it works. **This costs one
  line**: the hidden state is an attribute on a container line that exists
  anyway, and revealing it is a single statement in a routine that already runs
  at load. That one line is charged against the 50 lines of headroom and is
  recorded in the Budget below. The remaining degradation — no question controls,
  so no questions to export — is an accepted one rather than a defect, because
  US1 is P1 and delivers its value alone.

## Requirements *(mandatory)*

### Functional Requirements

#### The artifact and the single-file contract

- **FR-001**: The gallery MUST carry a new artifact at
  `speckit-pro/artifact-gallery/templates/pr-writeup.html`, whose file stem
  equals the identifier its catalog entry already declares.
- **FR-002**: The artifact MUST be one HTML file. It MUST require no build step,
  no bundler, and no preprocessor, and MUST have no sibling asset: no linked
  stylesheet, script file, image file, or data file beside it.
- **FR-003**: The artifact MUST render correctly when opened straight from a
  filesystem with no server and no install, reporting nothing in the browser
  console, no failed load, and no missing content.
- **FR-004**: With the network unavailable the artifact MUST stay completely
  readable with every control still operable, the only visible difference being
  typeface substitution.
- **FR-005**: The artifact MUST embed the brand-token block from
  `speckit-pro/artifact-gallery/brand-kit.css` verbatim, with its markers, byte
  for byte, exactly once, start before end.
- **FR-006**: The artifact MUST embed the gallery head block from
  `speckit-pro/artifact-gallery/theme-toggle.html` verbatim, with its markers,
  byte for byte, exactly once, start before end. The security policy declaration,
  the font request, the pre-paint theme application, and the theme control all
  arrive with it and MUST NOT be authored, replaced, wrapped, or moved.
- **FR-007**: The artifact MUST NOT contain any construct the contract prohibits:
  a base element, a reference beginning with two slashes and no scheme, an
  event-handler attribute, a `srcdoc` attribute, a form element with a submission
  target, or a `ping` attribute. If the upstream source uses one, the port drops
  it.
- **FR-008**: The artifact MUST make no external reference that loads a resource,
  other than the brand typeface request carried inside the head block.
- **FR-009**: The artifact MUST carry an attribution header as an HTML comment
  near the top of the file, using the five exact labels the contract fixes plus
  the upstream copyright line verbatim. The upstream file it names MUST be
  `17-pr-writeup.html`, which is the `source.file` its catalog entry declares,
  and the repository it names MUST be the one the contract names.
- **FR-010**: The artifact MUST contain no relative reference into a skills
  directory of the form the Codex payload build rewrites, so its shipped copies
  stay byte-identical to their source on both platforms.

#### The six regions a reviewer reads

- **FR-011**: The artifact MUST ship six **reader-facing** fill regions:
  `motivation`, `before-after`, `file-by-file`, `non-goals`, `verification`, and
  `implementation-notes`. The first four of those named by the roadmap
  (`motivation`, `before-after`, `file-by-file`, `implementation-notes`) are the
  set pinned as the floor; `non-goals` and `verification` ship because the
  catalog entry shipped in ART-001 already promises a reader "what it
  deliberately leaves out, and how it was verified".
- **FR-011a**: The artifact MUST additionally ship a `feature-header` region,
  which is not a reader-facing section and is not pinned in the floor. It MUST
  carry `id="feature-id"` on the feature identifier and `id="feature-name"` on
  the feature name, because both exports read them to name the change. The
  artifact's own kind MUST carry `id="artifact-title"` and MUST sit outside every
  region, so no fill can delete it. **Three** shipped templates already do this —
  `module-map`, `code-approaches`, and `implementation-plan`. `spec-explainer` is
  the precedent for carrying the *region* while declaring no exports, and it is
  not the precedent for the ids: it carries none of the three, and it places its
  artifact kind *inside* the region, where the first fill deletes it. That is
  survivable only because it exports nothing, and this artifact exports two
  kinds. Without the ids the feature's identity would live outside every region,
  so a generated artifact could never correct the fictional sample and every
  export would name the wrong change.

#### What the port keeps and drops

- **FR-011b**: The port maps upstream `#why`'s heading and lede to `motivation`,
  promotes the before/after panel block nested inside `#why` into its own titled
  `before-after` section, maps `#tour` to `file-by-file`, maps `#tests` to
  `verification`, and maps the page header's eyebrow and title to
  `feature-header`. `non-goals` is seeded from `#focus`'s third item, "What I
  deliberately did not do", restructured as its own titled section.
  `implementation-notes` is authored fresh and has no upstream counterpart.
- **FR-011c**: The port MUST drop the upstream file-count strip, the prompt echo,
  the TL;DR block, the first two "where to focus" items, the whole rollout
  section, and the table-of-contents sidebar together with the two-column layout
  it requires. Each maps to no fill region, and together they are the line lever
  that holds this port to the document-template class.
- **FR-011d**: The port MUST NOT carry upstream's multi-class syntax highlighting
  into its code samples; it uses the single muted-comment span the gallery's
  shipped templates use, because the upstream classes introduce colors outside the
  audited set and carry meaning by hue alone. A verification item's passed-or-
  pending state MUST be readable as a word, not as a check glyph's fill.
- **FR-011e**: Each of the six reader-facing sections MUST carry its heading
  outside its marker pair, so a fill replaces content and never the section title.
  Each heading MUST read as a plain-English reader label rather than as a
  restatement of its slot name, because FR-023b exports
  `<slot> / <section heading>` and a heading echoing its slot collapses that line
  to the same word twice, leaving a reader who has left the artifact no more than
  the slot name they already had.
- **FR-012**: Each region MUST be delimited by exactly one pair of HTML comment
  markers, `FILL:<slot>:START` before `FILL:<slot>:END`.
- **FR-013**: Regions MUST be flat: no pair may enclose another, and each pair
  MUST delimit a whole subtree, with no element opening on one side of a boundary
  and closing on the other.
- **FR-014**: The artifact MUST document its slot inventory in a single HTML
  comment placed immediately after the attribution header, one line per slot,
  reading `Slot: … | Fills: … | Source: …` in that order, with no pipe inside a
  value.
- **FR-015**: Every slot name in the inventory MUST be filename-safe kebab-case
  and unique within the artifact, and MUST agree in both directions with the
  regions the body delimits: every documented slot has a region, and every region
  is documented.
- **FR-016**: The inventory MUST carry none of the attribution header's own
  labels or literals, so the header stays the first comment a scanner recognises
  as one.
- **FR-017**: Every `Source:` value in the inventory MUST name only members of
  the closed set of source artifacts the fill-region validation recognises. The
  validation MUST gain `implementation-notes.md` as a member of that set, written
  as a bare filename like every existing member, so the `implementation-notes`
  slot can name the record it actually renders. The set is bare filenames of
  per-feature SpecKit artifacts regardless of directory, which is already true of
  `design-concept.md`. Naming an existing member instead was rejected: every
  candidate points an authoring agent at a file containing no notes, which breaks
  the one interface this slice owes ART-010.
- **FR-017a**: The seven slots declare these sources: `feature-header` →
  `spec.md`; `motivation` → `spec.md`; `before-after` → `spec.md, plan.md`;
  `file-by-file` → `plan.md, tasks.md`; `non-goals` → `design-concept.md,
  spec.md`; `verification` → `spec.md, tasks.md`; `implementation-notes` →
  `implementation-notes.md`.
- **FR-017b**: The `implementation-notes` inventory line's `Fills:` value MUST
  carry both the filter and the empty case, because that line is the only
  agent-facing instruction the artifact holds for this region: one entry per task
  that reported something, in the record's order, or one sentence naming which of
  FR-019b's three cases obtains. The three MUST be **named** on that line — every
  task reported nothing, no task recorded an entry, the record was unavailable —
  rather than gestured at, because SC-011 holds the inventory to being sufficient
  read alone, and an agent told only to say "which case obtains" writes "No
  notes." and loses the distinction FR-019b exists to preserve. It costs no line,
  since FR-014 already makes the line mandatory and it stays one line, and it must
  contain no pipe.
- **FR-017c**: The `before-after` inventory line's `Fills:` value MUST instruct
  the authoring agent to keep each panel's statement opening with the word naming
  that panel. FR-018 fixes this for the **shipped sample**; the inventory is what
  fixes it for **every fill after the first**, and the two panels are the one
  place in this artifact where a distinction could otherwise fall back to column
  position or panel colour, which FR-032 forbids. The carrier sits inside the
  marker pair and cannot be moved outside it — FR-012 allows one pair per region
  and FR-013 requires that pair to delimit a whole subtree — so an inventory
  instruction is the only thing that can protect it, exactly as `file-by-file`'s
  line protects its item anchors and `verification`'s line protects its state
  words. It costs no line, since FR-014 already makes the line mandatory and it
  stays one line, and it must contain no pipe.
- **FR-018**: Every one of the seven regions MUST ship representative fictional
  sample content held to the minimum that demonstrates its shape: non-empty
  everywhere, expansive nowhere. The artifact ships four shapes, and each has its
  own minimum:
  - **Prose** (`motivation`): one short paragraph.
  - **An anchored repeated list** (`file-by-file`, the only slot the fill-region
    validation binds as a list): **three items**. Two is the validation's
    *floor*, not the count it requires — it fails a list slot only on
    `len(anchored) < 2`, and nothing anywhere caps the number. Two is also below
    every shipped anchored list in the gallery (`modules` 5, `phases` 4,
    `approaches` 3), so three is the low end of the shipped convention rather
    than a new low. The reason is the reader's, not the gate's: this region
    exists to say what *each* changed file does, and a real change is
    heterogeneous. Two items show at most two kinds, and an authoring agent
    reading the sample as its model learns the region lists source files. Three
    show a production file, its test, and a config or manifest value — the shape
    of this slice's own change. A fourth adds an instance, not a kind, and is
    paid for in lines; upstream's six is a real pull request's file list, not a
    template's demonstrating minimum.
  - **An unanchored repeated list** (`non-goals`, `verification`): **two items**.
    These carry no per-item anchor under FR-020a, so no validation rule counts
    them, and each is a homogeneous statement where a third adds an instance
    rather than a kind. `verification` in particular does its teaching through
    FR-011d's state word rather than through length, which the both-states rule
    below buys for nothing. `implementation-notes` is the exception at three, for
    the reason below.
  - **A two-panel comparison** (`before-after`): one short statement per panel,
    each **opening with the word naming its panel**, so which panel is which
    survives the single `flex-wrap` that stacks them on a narrow viewport and
    survives a monochrome rendering under FR-032. This is the only section with
    bespoke layout, so it is capped on content as well as on CSS.
  - **The header** (`feature-header`): the invented feature's identifier and its
    name, carrying the two ids FR-011a fixes, plus FR-018a's notice and nothing
    else.

  `implementation-notes` is unanchored and would take two by the rule above, and
  ships **three** instead. Three is the count at which the retry pair FR-019
  requires can be shown **non-adjacent**, as a real re-run appends it after the
  intervening tasks' entries. Two would force a choice between showing two
  distinct tasks and showing the retry, and an adjacent pair would model the case
  wrongly.

  `verification`'s two items MUST show **both states** — one passed and one
  pending — because FR-011d requires that state to read as a word, and two items
  in the same state leave the other word undemonstrated. This is what lets the
  region teach at two rather than at three, and it costs no line.

  Every region MUST use the same invented feature, named once and reused,
  following `spec-explainer`, which holds one across all of its regions.

  **Line cost of this requirement against the budget**: seven, all markup, all
  declared in the Reviewability Budget below. Six for `file-by-file`'s third
  item, measured at the 6.0 authored lines per anchored repeated entry that
  `implementation-plan`'s `phases` region ships (24 lines, 4 items); one for
  FR-018a's sentence. Every other clause here constrains the wording of content
  already budgeted and costs nothing.
- **FR-018a**: The artifact MUST say in visible text that its content is
  invented, in one sentence naming the invented feature, placed **inside**
  `feature-header`'s marker pair so the first fill removes it. All four shipped
  gallery templates carry this sentence and all four place it there. Without it a
  reader opening the file cold reads a complete and plausible write-up of a change
  that never happened, with nothing on the page saying otherwise — and this is the
  one gallery template whose subject matter is a finished pull request, so the
  fiction is the most credible. It reuses the muted-paragraph rule FR-019a's
  standing sentence already requires, so it adds no CSS rule of its own.
- **FR-018b**: The two `implementation-notes` entries sharing a task identifier
  MUST read as a **sequence**: the second states what the re-run changed, so the
  pair reads as history rather than as a line printed twice. FR-019a's standing
  sentence tells a reader that a task *can* appear more than once; it cannot tell
  them that *these two* are that case. Two entries with interchangeable text would
  make the sample model the accident FR-019c declines to mark visually, which is
  the one reading the whole design exists to prevent.
- **FR-019**: The `implementation-notes` region MUST render only the eventful
  entries of the implementation record, in the record's own append order, each
  under the task identifier it was recorded against. Two entries sharing a task
  identifier both render, because that is a retry and correct history.
- **FR-019a**: Because this region shows a **filtered view of an external
  record** rather than what an author wrote, the section MUST carry a standing
  one-sentence intro **outside** its marker pair, stating that only tasks with
  something to report appear, that they appear in the record's order, and that a
  retried task appears more than once. Outside the pair is required, not
  stylistic: the sentence is true of every fill rather than of this sample, so it
  must survive fills exactly as FR-011e's headings do. All six `section-intro`
  uses in `implementation-plan` sit outside their pairs, and the gallery already
  uses that element for structural claims, not only for blurbs. Contrast
  `spec-explainer`'s sample notice, which correctly sits *inside*
  `feature-header`'s pair because it describes the sample and should die with the
  fill — which this artifact ships too, under FR-018a. This one sentence is what
  lets a reader tell an empty region from a broken one, and a repeated task
  identifier from a duplicate.
  The sentence MUST be phrased as the region's **standing rule** rather than as
  an assertion about the entries below it. It survives every fill, including
  FR-019b's third case, where the record was never read and no filter ran; a
  sentence asserting that what follows was filtered would be false there, sitting
  directly above a sentence saying the record was unavailable.
- **FR-019b**: When no entry survives the filter, the fill MUST state which case
  obtains in one sentence — every task reported nothing, no task recorded an
  entry, or the record was unavailable — rather than leaving the region empty or
  keeping the sample. The artifact ships **no** separate empty-state element,
  because nothing in it reads the record at render time: the template cannot
  distinguish the cases and the authoring agent can. All three states are real
  rather than hypothetical. Two of the three dispatch routes in the record
  contract write `None` permanently, so a spec whose implementation tasks are all
  research or verification yields an all-`None` record; the record is opened
  before the first task is dispatched precisely so an interrupted phase and a
  task-free spec both leave a header-only record; the record is fail-open, so
  absence is possible; and the record's read window is bounded to the feature
  directory, so a fill attempted after archive finds nothing at the declared path.
- **FR-019c**: A retry pair MUST NOT be visually grouped or carry a derived
  attempt ordinal. Grouping would be incorrect, not merely costly: a serial re-run
  appends after the intervening tasks' entries, so collapsing the pair together
  would reorder the record and violate FR-019's append order. An ordinal would
  assert a field the record does not carry. FR-019a's standing sentence already
  tells the reader a task can appear more than once, which is what an ordinal
  would have bought.
- **FR-019d**: Each entry MUST take the form of a list item whose task identifier
  leads in bold, inside a grouping list that sits within the marker pair,
  following the `goals` region in `spec-explainer`. Bold rather than a mono span:
  it is the named precedent, it survives monochrome per FR-032, and it adds no
  class and no CSS rule. The list item also satisfies FR-020's end-tag
  requirement without a special case.
- **FR-020**: `file-by-file` holds a repeated list whose items an export must be
  able to name, and it is the only slot that gains a list-slot row. Its grouping
  element MUST sit outside the marker pair so the container survives a fill, and
  every repeated item at the region's own top level MUST carry a stable, unique
  anchor of the form `file-by-file-<item-slug>` in kebab-case. Its items MUST be
  elements that require an end tag, because the fill-region parser performs no
  implied closing and an unclosed item would report as nested and silently vanish
  from the region's top level.
- **FR-020a**: `verification`, `non-goals`, and `implementation-notes` also render
  repeated items, and each keeps its grouping element **inside** its marker pair
  and carries no per-item anchor, following `key-files` in `module-map` and
  `goals` in `spec-explainer`. `implementation-notes` in particular MUST NOT be
  anchored per item: FR-019 requires two entries under one task identifier to both
  render, and a per-item anchor derived from that identifier would collide, which
  the validation rejects because a fragment resolving to two items resolves to
  neither. `motivation` is prose and `before-after` is a fixed two-panel
  comparison; neither is a list.

#### Attaching and exporting a question

- **FR-021**: Each of the six sections MUST carry its own inline question
  control: a keyboard-reachable disclosure plus a labelled text field, following
  the shape the gallery's shipped **objection** controls use — `module-map` and
  `implementation-plan`, and those two only — so a reviewer meets one interaction
  across the gallery. `code-approaches` is not a precedent here: it ships a
  single-choice selection control and no disclosure at all. FR-021a states which
  properties of that shape are independently testable, because an outward
  reference is acceptable for interaction shape and is not acceptable for an
  obligation a reviewer must be able to check on its own terms.
- **FR-021a**: Three properties of that pattern are stated here rather than left to
  "matching", because both are accessibility obligations and a port that met the
  shape while missing them would still read as compliant. The disclosure's own
  control MUST state **in text** whether its section currently carries a
  question, so a recorded question is findable without opening all six and so the
  carried/not-carried state survives a monochrome rendering under FR-032. The
  text field's visible label MUST be programmatically associated with the field;
  **placeholder text does not satisfy this**, because it is not an accessible
  name, and it vanishes the moment the reviewer types. Both cost no line: the
  routine all three shipped export-carrying templates run already writes the
  state into the disclosure's own accessible name and already builds a real label
  bound to the field.
  The third property is **when** that text is computed. The control MUST
  recompute it on every change to the field, not once at mount and not only when
  the disclosure is next opened or closed, so a reader scanning a collapsed
  summary sees the field's current content rather than its value at the last
  toggle. This is the substance of the state requirement rather than a refinement
  of it: a summary fixed at mount reports "no question recorded" over a section
  that carries one, which is worse than reporting nothing, and the accessible-name
  channel is the only place this artifact carries the state at all. It costs no
  line — the shipped routine's input listener already calls the same refresh the
  mount call does.
- **FR-021b**: The disclosure MUST carry no ARIA role, `aria-expanded`, or
  `aria-pressed`. Its open and closed state is exposed natively, and the current
  HTML-ARIA mapping does not permit those attributes on a `summary` acting as its
  parent's summary. Forcing a role here has been observed to remove the exposed
  state rather than add it. Stated as a prohibition because "match the shipped
  pattern" reads as permission to add markup that looks more accessible and is
  less so.
- **FR-022**: The artifact MUST carry exactly one export control per declared
  export kind, and its catalog entry declares two: an instruction for a coding
  agent, and a record for a pull-request comment. Each control MUST be labelled
  with its destination rather than its mechanism.
- **FR-023**: An export MUST walk only the non-empty question fields, and MUST
  carry each question together with the anchor of the section it attaches to.
- **FR-023a**: Both exports MUST serialize the same structure and differ in
  exactly one line. Each opens with the artifact title, then the feature
  identifier and name, then a blank line, then a single lead line naming the
  kind, then one blank-line-separated block per non-empty question. Neither
  export emits markdown syntax: the `markdown` kind names its **destination, not
  its encoding**, and the ART-008 sweep reads the raw comment body where the line
  structure survives. That a pull-request comment renders the two header lines as
  one paragraph is a recorded gap, not a defect this slice fixes.
- **FR-023b**: A question's reference line MUST read
  `<slot> / <section heading>  (#<anchor>)` with two spaces before the
  parenthesis, matching the form the three export-carrying templates already
  emit. The anchor MUST be the `sec-<slot>` id the section's heading already
  carries for its `aria-labelledby` — the gallery's existing section-anchor
  convention. Because FR-011e places every heading outside its marker pair, no
  exported coordinate other than the feature-header identifiers can be deleted by
  a fill, which is stronger than every shipped precedent, whose item anchors sit
  inside a fill region. Each question control MUST be appended to the end of its
  section rather than inserted after its heading, so it follows the content the
  reader is questioning.
- **FR-023c**: The export routine MUST collect its items from a pinned list of
  the slot names in document order, resolving each section from the `sec-<slot>`
  id directly, rather than by walking a container's children. Each item carries
  its own slot name. This survives a fill that restructures a section, never
  depends on DOM order, and concatenates no value into a selector string.
  **That id identifies the section's heading, not the section** — FR-023b says so
  in its own words — so the routine MUST resolve from the heading to the section
  that heading labels, and MUST mount the question control at that section's end.
  Mounting it on the resolved element itself would place it immediately after the
  heading, which is the one placement FR-023b forbids, and the tab order would
  then put every question ahead of the content it questions. Stating the
  resolution target costs no line: the routine needs one expression to reach its
  mount point either way, and this fixes which one it is.
- **FR-024**: An export MUST carry enough context to be acted on away from the
  artifact: the artifact, the change it belongs to, and the location each
  question attaches to.
- **FR-025**: An export MUST NOT carry a conclusion the reviewer did not reach,
  and MUST NOT carry any value the reviewer could not have inspected on screen.
- **FR-026**: An export MUST be derived from the artifact's live state at the
  moment it is invoked, never from a value fixed when the file was written.
- **FR-026a**: When two exports are invoked before the first completes, the
  artifact MUST report the outcome of the later invocation only. Each invocation
  MUST carry a token compared against the current one when its copy settles, and
  a settle belonging to a superseded invocation MUST change no status text, reveal
  no fallback text, and move no focus. **Both** settle paths need the guard, not
  only the rejection path: a slow success resolving after a fast failure would
  overwrite the failure message with "Copied" while the fallback field still holds
  the other kind's text.
  Without this, a rejected first copy announces a failure that did not happen and
  places the first kind's payload in the fallback field after the second kind
  copied successfully. **This defect is present in all three export-carrying
  templates ART-002 shipped** — each runs the same unguarded settle, and none
  carries a currency check — and this artifact MUST NOT reproduce it.
- **FR-026b**: The currency check MUST be scoped by **effect, not by path**: it
  sits where a status write or a fallback reveal actually lands, and every path
  reaches those effects through it. Scoping it by path is not sufficient here,
  and the reason is a property of the precedent this slice reuses rather than a
  hypothetical. In all three shipped export-carrying templates the status write
  is deferred behind a short timer — the region is cleared and rewritten so a
  repeated identical message is announced a second time — and the focus move to
  the fallback field is deferred behind a longer one. So the two paths the
  invocation-currency rule would exempt as "synchronous" decide synchronously but
  **land asynchronously**, in a later turn, after a second invocation may have
  completed. A first export refused synchronously would then move focus into a
  field the second export already re-hid, which is focus theft and which FR-026a
  forbids in the words "move no focus". Scoping the check by effect makes the
  exemption unnecessary rather than merely safer: the two synchronous paths carry
  the current token and pass the same check, so no path is unguarded and none
  needs a rationale for being so. This is a relocation of the guard, not an
  addition — the same two check sites FR-026a already budgets 13 lines for, moved
  from the settle callbacks to the effects those callbacks schedule — so it costs
  no line beyond that allowance.
- **FR-027**: Every export control MUST be reachable and operable by keyboard
  alone, and MUST report its outcome in text rather than by color or animation
  alone. The artifact MUST carry exactly one live status region for that
  reporting, present from load rather than created on demand, and that region
  MUST sit outside every fill region. The placement is the requirement, not a
  preference: a status region a fill could delete would make every later failure
  silent, which is the defect FR-028 exists to prevent. It costs no line, because
  the region must exist either way and this fixes only where it sits.
- **FR-028**: When clipboard access fails or is refused, the artifact MUST take
  all four steps of the contract's failure path: (1) reveal the same exported
  text in a field the reader can select; (2) keep that field **focusable and not
  disabled**, give it an accessible name, and move focus to it; (3) report the
  single failure message; and (4) **not** report success. Step 2 is not
  decoration — focus arriving at an inert or unnamed control strands a reader who
  cannot see the reveal, and a disabled field cannot be focused at all. Failing
  silently and reporting success are the same defect wearing different clothes:
  the reader believes they hold text they do not hold.
- **FR-028a**: Three obligations attach to that path. Each is already satisfied
  by the routine shape all three shipped export-carrying templates run, so none
  costs a line against the budget. The artifact MUST NOT make a **second copy
  attempt** through any deprecated interface after the first fails, because that
  attempt's result is ambiguous and reporting an uncertain success is exactly
  what the contract forbids. Every invocation MUST re-hide the fallback field
  before it attempts its copy, so a later successful export never leaves an
  earlier failure's payload on screen beside a success message — FR-026a governs
  only the concurrent case, and this is the sequential one. The failure path MUST
  leave the browser console silent, which means the rejection is handled rather
  than left to surface as an unhandled rejection; FR-003 and SC-001 scope console
  silence to opening and reading, so without this clause the export path is
  unbound.
- **FR-029**: When no question has been written, an export MUST say in text that
  there is nothing to export rather than produce an empty or invented document.
- **FR-029a**: The artifact's export literals MUST be pinned in a contract
  document this slice authors, and the clipboard-failure message MUST be
  byte-identical to the one the three export-carrying templates already ship
  (verified identical across all three). The empty-state bodies and the two lead
  lines are authored fresh in this artifact's own noun, "question", following the
  recorded per-template pattern — the shipped templates already vary that noun
  between "objection" and "approach", so this is the same move rather than a
  divergence.
  This slice MUST author its own `contracts/export-payload-contract.md`, because
  **the document all three shipped templates name in a source comment no longer
  exists**: ART-002's copy was deleted when that feature was archived, so every
  shipped template now carries a pinning reference that resolves nowhere.
  Nothing compares the copies of the failure message, and this slice does **not**
  add that comparison, because FR-039a fixes its shared-validation change at
  three literals. Both facts are recorded gaps, including that this slice's own
  contract will dangle the same way when ART-003 is archived.
- **FR-029b**: That failure message MUST be the **only** one, covering every
  failure mode, and it MUST assert **no cause**. Byte-identity does not secure
  this on its own: it fixes the wording of one message and constrains neither how
  many failure messages exist nor the addition of a more diagnostic variant for a
  mode that looks distinguishable. None of them is. The artifact cannot tell a
  refused permission from an unfocused document from a browser policy from an
  absent interface, so naming one would be a guess presented as a diagnosis. The
  constraint costs no line, because it forbids messages rather than requiring
  them.
- **FR-029c**: No string literal inside the artifact's script may name the
  local-file scheme. Feedback text says "opened from a filesystem" instead. This
  is a validation requirement, not a wording preference: the gallery scanner's
  URL-shaped pattern treats a script string literal that opens with a scheme and
  a colon, or that carries a scheme followed by two slashes anywhere, as an
  external reference and fails the file. The clipboard call itself is not a
  scanned call site; the wording is. It costs no line, because the same string
  slot carries either form.

#### Accessibility

- **FR-030**: Every foreground and background pairing the artifact uses MUST come
  from the kit's audited set. Colors introduced outside the embedded block are
  outside the audit and MUST NOT be relied on.
- **FR-030a**: The pairings the artifact actually uses MUST be **recorded with
  the acceptance evidence** under FR-042, each traced to the audited row that
  clears it and to the role that row permits — body text, large text, or
  meaningful non-text. Without the list FR-030 is a claim a reviewer can only
  take on trust, because the audit lives in a header that does not ship and the
  artifact carries only token names. The record sits in the evidence rather than
  in the artifact **on purpose**: `spec-explainer` keeps its equivalent audit as
  an in-file comment, which is the shipped precedent, but that comment is
  authored CSS lines and this slice has 19 lines of margin on the document-CSS
  ceiling and 50 on the total. Recording it beside the render evidence discharges
  the same obligation at zero cost to the artifact.
- **FR-031**: The artifact MUST NOT use the subtle border token for any boundary
  that conveys meaning; a meaningful boundary uses the strong border token.
- **FR-031a**: For this artifact that rule resolves to a **checkable outcome
  rather than a judgement**: the subtle border token MUST appear nowhere in the
  authored CSS. Every boundary this template draws — a section from the page, a
  before/after panel from its neighbour, a question disclosure, a text field, a
  code sample — separates content from its surroundings and therefore carries
  meaning, which is the one role that token is audited against. `spec-explainer`,
  the shipped comparator for this document class, records the same outcome for
  the same reason. Stating the outcome matters because the judgement version has
  to be re-made at every boundary by whoever reviews it, and a boundary wrongly
  judged decorative fails at 1.13:1 rather than visibly. The outcome version is a
  search, costs no line, and removes lines if anything.
- **FR-032**: No status, action, or distinction the artifact draws may be carried
  by color alone. Each MUST also be available as text, shape, glyph, or position,
  and MUST survive a monochrome print or screenshot.
- **FR-033**: Where the artifact names a heading typeface explicitly it MUST use
  the display token, and **only on the first two heading levels**, which are the
  levels the embedded block assigns it. From the third level down the block
  assigns the body token at a heavier weight, and it records that applying the
  display face to every level was a fidelity defect caught against the brand
  source. Naming the display token below the second level would therefore
  reintroduce a defect the kit already fixed. Heading rank MUST ride on semantic
  heading level, size, and weight rather than on typeface identity, so hierarchy
  survives the brand face being unavailable.
- **FR-033a**: The heading typeface token is `--rc-font-display`. No other
  heading-typeface custom property is defined anywhere in the embedded block, and
  an undefined custom property fails **silently**: the declaration falls through
  to whatever fallback it named, so a typo renders plausibly and is invisible to
  review. The artifact MUST reference no custom property the embedded block does
  not define. The cheapest way to satisfy both this and FR-033 is to name no
  heading typeface at all and inherit the block's own assignments, which is the
  reduction lever `plan.md` records; every heading the artifact writes as an
  ordinary heading gets the right face for its level free.
- **FR-034**: The artifact MUST add no positive tab index and MUST trap focus
  nowhere, and MUST NOT suppress the kit's focus indicator without an equivalent
  replacement.
- **FR-035**: Any motion the artifact itself introduces MUST be suppressed for a
  reader who has asked for reduced motion.
- **FR-036**: If the artifact needs the current theme it MUST read the resolved
  theme attribute from the document root, and MUST NOT read stored theme state
  itself or place a stored value into markup, a selector, or any executable
  position.

#### Catalog, validation, and payload

- **FR-037**: The change MUST flip exactly one catalog value: this entry's
  `status`, from `planned` to `shipped`. It MUST change no other value on this
  entry, no other entry, and no shared foundation file (the contract document,
  the brand kit, the head block, the signal vocabulary, or the export
  vocabulary).
- **FR-038**: The fill-region validation MUST gain a floor row for this template
  naming the four slots the roadmap names, so the floor literal keeps tracing to
  one document.
- **FR-039**: The fill-region validation MUST gain a list-slot row for this
  template naming `file-by-file` and no other slot, per FR-020 and FR-020a.
- **FR-039a**: The fill-region validation MUST gain `implementation-notes.md` as
  a member of its closed source-artifact set, per FR-017. These three literals —
  the floor row, the list-slot row, and the source-set member — are the whole of
  this slice's change to shared validation.
- **FR-040**: The full repository suite MUST pass with zero failures, including
  the gallery scanner, the fill-region validation, and Layer 1 structural
  validation.
- **FR-041**: The change MUST account for the generated-artifact contract, since
  the gallery ships inside the plugin payload and a new artifact file changes
  shipped bytes on both platforms.
- **FR-042**: A manual render of the shipped file from the local-file scheme MUST
  be recorded as acceptance evidence, in both themes and with the network
  unavailable.

### Reviewability Notes *(if applicable)*

No `Reviewability-Exception` pragma is claimed, and none is available: the
accepted classes are `refactor`, `infra`, and `upgrade`, and none honestly
describes net-new template work. Splitting further is not available either,
because a self-contained HTML artifact cannot be divided across two pull
requests and still render from `file://`. One template per PR is already the
thinnest vertical slice this work admits.

The slice therefore clears the boundary on cost discipline or not at all.
Decomposing the four shipped templates locates that cost: the export
affordance floor is ~280 lines of JavaScript and is irreducible, but **component
CSS is the larger line item** at 450–663 lines, and `spec-explainer` renders six
regions in 171. The difference is subject matter, not restraint — the three
expensive templates draw a graph, mockups, timelines and comparison tables.
`pr-writeup` is a document of six titled prose-and-list sections, so its
structural analogue is `spec-explainer`.

Holding component CSS to that document class is what puts this slice at ~758 and
in warn. Failing to hold it puts it at 984 or above and in block. **This is a
design constraint, not a prediction**, and the three templates that actually
carry both exports did not hold it.

Clarify closed most of the distance. The port drops are now fixed requirements
worth about 141 lines (FR-011c), the export routine's shape is settled and its
collection strategy is 19 lines cheaper than the precedent (FR-023c), and the
remaining figure is decomposed and measured against shipped selectors rather than
scaled from a multiplier. What is left open is a single ceiling, carried in the
Budget below.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (a shipped template file)
- **Secondary surfaces, if any**: seed/config (one catalog value), harness/adapter (three literals in the fill-region validation)
- **Projected reviewable LOC**: **~758**, decomposed and measured rather than
  scaled from a multiplier:
  - export and question-capture JavaScript **~288** — the shipped precedent's 294,
    less 19 for collecting six named sections instead of walking a list container
    and for a comment with no counterpart here, plus 13 for FR-026a's
    stale-settle guard
  - question and export CSS **~97**, measured off the precedent's own selectors
  - six document sections **~150** CSS, against `spec-explainer`'s 171 total
  - markup **~223**

  **The markup figure moved from 215 to 222 at Checklist, and the total with it,
  from 750 to 757.** The earlier figure rested on a misreading of the
  fill-region validation: FR-018 read `MINIMUM_ITEMS = 2` as the count a list
  region must ship, when the rule fails only on `len(anchored) < 2` and nothing
  caps it. Two is below every shipped anchored list in the gallery. Seven lines
  buy the correction: six for `file-by-file`'s third item, measured at the 6.0
  authored lines per anchored repeated entry `implementation-plan`'s `phases`
  ships, and one for FR-018a's sample notice, which reuses an existing rule and
  adds no CSS. Nothing was shrunk elsewhere to absorb them. Headroom to the 800
  block falls from 50 lines to **43**.

  **One further line was charged at Checklist, taking markup to 223 and the total
  to 758.** The accessibility pass found that the export region would stay on
  screen offering an action nothing can perform when scripting is unavailable,
  and closed it by shipping that region hidden and revealing it from the routine
  that already runs at load. The hidden state is an attribute on a container line
  that exists anyway; the reveal is the one new statement. Headroom to the 800
  block is now **42**. Every other accessibility remediation in that pass cost
  nothing, because each fixed wording, an inventory value already mandatory, or
  the placement of a guard already budgeted.

  Excludes the 458 lines of canonical embedded blocks a reviewer never reads
  because they are byte-verified copies (`brand-kit.css` `BRAND-KIT` block = 318,
  `theme-toggle.html` `GALLERY-HEAD` block = 140; both measured).
- **Projected production files**: 1 (net-new: the artifact itself)
- **Projected total files**: **13**, measured by the setup gate. An earlier count
  of ~5 was wrong: it counted the change surface plus this spec and omitted the
  SpecKit planning artifacts the same pull request carries. Still below the 15
  warn threshold, so the budget result is unchanged.
- **Budget result**: **warn**, above the 400 warn threshold and below the 800
  block. Component CSS is the only dimension that can miss the figure; the export
  floor cannot, because it is measured against three shipped implementations of
  the same routine.
- **CSS ceiling**: adopted at Plan as an explicit, checkable constraint, which
  resolves the last open question this spec carried. Five numeric constraints are
  declared, and the ceiling is checked by one calibrated measuring instrument at
  three checkpoints with a stop rule. The first checkpoint fires after the six
  sections' CSS and **before** any export work, so an overrun surfaces at roughly
  150 lines written rather than at 758.
- **Basis for the projection**: measured against the four shipped templates
  rather than fitted to one aggregate figure. Authored lines are what the gate
  counts, and the predictor is the `exports` declaration, not slot count and not
  upstream size:

  | Template | `exports` | Slots | Authored |
  |---|---|---|---|
  | `spec-explainer` | `[]` | 6 | 316 |
  | `module-map` | `["prompt","markdown"]` | 5 | 1003 |
  | `code-approaches` | `["prompt","markdown"]` | 3 | 1026 |
  | `implementation-plan` | `["prompt","markdown"]` | 7 | 1222 |

  The one template under the block declares no exports. All three carrying
  `["prompt","markdown"]` land between 1003 and 1222, each spending 414–435 lines
  on export and question-capture JavaScript. `pr-writeup` carries both exports
  and six slots, so its comparators are `module-map` and `code-approaches`.
  Upstream `17-pr-writeup.html` sharpens this: 596 lines, 346 of them CSS the
  brand kit replaces, and **zero `<script>` and zero `<button>` tags** — six
  `<details>` disclosures and nothing else. Every line of export behaviour is
  authored fresh with no upstream counterpart to port.
- **Split decision**: This spec **is** the split. ART-003 originally declared one
  slice at 285 lines. The earlier feature's first slice shipped two templates of
  the same kind and measured 1494, a hard block that forced a re-slice
  mid-implement. ART-003 was re-declared at scaffold as three stacked slices, one
  template per pull request. This spec covers slice 1 (`pr-writeup`) only; `annotated-diff` and
  `flowchart` are slices 2 and 3, cut from their predecessor after each prior
  pull request is open. **Re-measure and re-declare at this slice's Plan phase**
  — the setup gate reads a declaration rather than measuring the tree and will
  not catch a stale number.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope
  budget, traceability, verification evidence, known gaps, and rollback or
  feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue. Slices 2 and 3, the
  generation step, and the ready flip are all named deferrals here.
- Known gaps MUST name all five carried out of Clarify. From session 1: the
  payload documents no fill-region grammar; the validation binds only the
  templates its floor names, so a shipped non-floor template is never parsed; and
  no check reads a catalog entry's `exports` against the artifact. From session 2:
  nothing compares the clipboard-failure message shared across what will be four
  templates, and the document all three shipped templates name as pinning it was
  deleted when ART-002 was archived, so those references resolve nowhere — a
  condition this slice's own contract will reach when ART-003 is archived. Also
  from session 2: pasted into a pull-request comment, the export's two header
  lines render as one paragraph, which is cosmetic for the automated reader and
  visible only to a human.
- Review order MUST put the authored markup ahead of the embedded canonical
  blocks, which are byte-verified copies rather than material to read.

### Key Entities

- **The artifact**: one HTML file carrying six reader-facing sections plus a
  `feature-header` chrome region, an attribution header, a slot inventory, sample
  content declared as invented, per-section question fields, and two export
  controls.
- **A fill region**: a named span of the artifact an authoring agent replaces
  later, delimited by one paired comment marker and described by one inventory
  line.
- **The slot inventory**: the machine-readable list of regions. It is the only
  thing that tells an authoring agent what it must fill, which is why it is bound
  in both directions to the regions the body delimits.
- **The catalog entry**: the routing row that already exists for this template,
  declaring its stage, its trigger, its provenance, its exports, and the single
  status value this slice changes.
- **A reviewer question**: free text a reviewer attaches to one section, carrying
  that section's anchor, and appearing in an export only when non-empty.
- **The implementation record**: the append-ordered log of what happened per
  task during implementation, whose eventful entries the implementation-notes
  region renders.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer opens the artifact from a filesystem with no server and
  no install and reads all six sections; the browser reports zero console
  messages, zero failed loads, and zero missing content.
- **SC-002**: With the network unavailable, 100% of the artifact's content stays
  readable and 100% of its controls stay operable; the only observable difference
  is typeface substitution.
- **SC-003**: A reviewer completes the whole loop, reading a section, attaching a
  question, and exporting it, using the keyboard alone, with zero mouse
  interactions required.
- **SC-004**: An export produced after writing questions in 2 of 6 sections
  carries exactly 2 questions, each naming its section, and carries zero entries
  for the 4 untouched sections.
- **SC-005**: With clipboard access refused, 100% of export attempts reveal the
  full text in a selectable field and state the outcome in words; zero report
  success.
- **SC-006**: Every distinction the artifact draws survives a monochrome
  rendering: a reader loses zero meaning when hue is removed.
- **SC-007**: Both embedded canonical blocks compare byte-identical to their
  canonical files, with zero characters of drift.
- **SC-008**: The full repository suite passes with zero failures, and the
  fill-region validation binds this template rather than passing vacuously.
- **SC-009**: Exactly one catalog value changes across the whole slice, and zero
  shared foundation files are edited.
- **SC-010**: The finished change's reviewable production LOC is measured against
  the gate rather than estimated, before the pull request is opened, and the
  figure declared at Plan is the measured one. Zero pull requests open carrying a
  stale or undeclared size figure, and zero carry an unrecorded boundary
  resolution. (This slice is projected to exceed the 800 block threshold, so the
  criterion is a true declaration and a recorded ruling, not clearing the
  threshold.)
- **SC-011**: An authoring agent reading only the artifact's own inventory can
  name all **seven** regions and what fills each, with zero regions undocumented
  and zero documented slots lacking a region, and can name all three of
  FR-019b's empty cases from the `implementation-notes` line alone.

## Assumptions

- The upstream source `17-pr-writeup.html` is fetched read-only at implement
  time from the upstream repository the contract names, kept outside this
  repository's tree, and never staged. Only the branded derivative is committed.
  This is the protocol ART-002 recorded, and it is why per-slot granularity
  cannot be settled before implement-time fetch.
- Port fidelity follows the model ART-002 recorded: keep the upstream interaction
  mechanism and structure, restyle entirely to brand tokens so no upstream color
  survives, drop upstream sections that map to no fill region, and author fresh
  what the final-PR stage needs.
- The catalog entry's declared `exports` (an agent instruction and a
  pull-request record) is taken as given from ART-001 and is not renegotiated
  here; changing it would be a second catalog value and therefore a contract
  amendment rather than a port.
- The question control reuses the disclosure-plus-labelled-field pattern the
  gallery's shipped draft-PR templates already carry, so no new interaction is
  invented for this artifact.
- The serialized payload shape of the two exports is a Plan-phase detail, to be
  resolved there by reusing the shipped "walk the non-empty notes with item
  anchors" shape. It is recorded here as a deferral rather than as an open
  question.
- The reviewability projection is measured against the four shipped templates
  individually, not fitted to one aggregate figure, and it is re-declared at
  Plan against the real port. Exceeding the block threshold is expected on the
  measured evidence. Re-slicing is **not** an available response: a
  self-contained HTML artifact cannot be divided across two pull requests and
  still render from the local-file scheme, so one template per PR is already the
  thinnest vertical slice this work admits.
- The feature is not shrunk to chase the size number. Six fill regions and both
  export kinds are decisions the interview fixed and the shipped catalog entry
  already promises; dropping either would resolve the number by breaking a
  commitment. The size boundary is resolved at Plan and by the operator, not by
  reducing scope here.
- Slices 2 and 3 stack on this branch after this pull request is open. Nothing in
  this slice may be shaped to suit them, and no merge happens inside the run.

## Dependencies

- **ART-001** (shipped): the brand kit, the head block, the single-file contract,
  and the catalog entry this slice flips.
- **ART-012** (shipped): the implementation record whose eventful entries the
  `implementation-notes` region renders.
- **ART-010** (downstream): the generation step that fills these regions. It
  reads this artifact's inventory, so the inventory is the interface this slice
  owes it.
- **ART-008** (downstream): the feedback sweep that reads exported questions from
  a pull-request comment, classifies them, and routes them through consensus. It
  is why every exported question must name the section it attaches to.

## Out of Scope

- `annotated-diff` and `flowchart`. Separate slices, separate specs, separate
  pull requests.
- Generation and authoring logic, and the ready flip. That is ART-010.
- The UAT walkthrough template. That is ART-009, and it is repo-authored rather
  than an upstream port.
- Any change to the contract document, the brand kit, the head block, the signal
  vocabulary, the export vocabulary, or any catalog value other than this entry's
  own `status`.
- Any change to another catalog entry, including the two this feature's later
  slices will flip.
- A general guard binding any catalog entry that reads `shipped` to the
  fill-region checks. Today the validation resolves its universe by intersecting
  the catalog with its floor, so a shipped template the floor does not name is
  never parsed at all — a port with no regions and no inventory passes every check
  green. That restriction is recorded as a deliberate decision inside the module
  itself, on the ground that binding a later template would hold it to a contract
  its own design never read. Widening it here would contradict a recorded decision
  in the file being edited. This slice closes the gap for `pr-writeup` alone, by
  adding its floor row.
- An artifact-side gate on a catalog entry's declared `exports`. No check reads
  that field against the artifact body, so an entry can declare an export kind the
  artifact does not ship and stay green. Closing it means binding all four
  already-shipped templates, which is a change to shared validation rather than a
  port.
- Recording the fill-region grammar in the shipped payload. The contract document
  documents none of it — the payload contains no occurrence of the marker syntax
  anywhere — and amending that document is out of scope here. The grammar is
  stated normatively in this spec, and each shipped template documents its own
  inventory, which is what an authoring agent actually reads.

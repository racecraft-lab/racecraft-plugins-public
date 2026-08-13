# Feature Specification: Final-PR Template Set — Slice 2, the Annotated Diff Artifact

**Feature Branch**: `art-003-final-pr-template-set-slice-2`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Final-PR Template Set — slice 2, the annotated diff artifact. Scope this slice to ONE template: `annotated-diff`. Ship it as a branded, self-contained HTML artifact that shows a reviewer the diff with the review's own findings attached to it, and that lets them hand an objection back per hunk without retyping it."

**Spec ID**: ART-003 (slice 2 of 3)

**Design Concept**: `docs/ai/specs/.process/ART-003-design-concept.md`

## Overview

ART-001 seeded a routing catalog that already promises a reader an Annotated
Diff: a walk through the diff hunk by hunk, annotating the ones that need it,
reached for when the change is large or when the self-review recorded a gap worth
pointing at. The entry exists and reads `planned`, so the promise is currently
unbacked. This slice backs it.

The artifact is a template, not a finished review. It ships fictional sample
content in every region and a machine-readable inventory of the regions an
authoring agent will later replace. Filling it with a real diff is ART-010's
work, not this slice's.

ART-003 is three vertical slices, one template per pull request, stacked in
roadmap order. This spec covers **slice 2 only**: `annotated-diff`. Slice 1
(`pr-writeup`) already shipped on this branch and is this spec's nearest
precedent; `flowchart` is slice 3 and is out of scope.

**What is inherited and what is not.** Slice 1 and this slice were built to the
same contract, so every obligation about the single file, the two canonical
blocks, the attribution header, the inventory grammar, the export payload, the
failure path, and the invocation-currency guard carries over unchanged and is
restated here rather than referenced. What does **not** carry over is everything
specific to a document of titled prose sections: the six reader-facing sections,
the implementation-record filter and its three empty cases, the two-panel
before/after comparison, and the section-anchored export coordinate slice 1
adopted. This artifact captures against a repeated **item**, not a section, so it
returns to the anchor form the three older templates use.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the diff with the review attached [US1] (Priority: P1)

A reviewer is asked to judge a finished pull request that is large enough, or
carries enough recorded findings, that reading the raw diff alone would not tell
them where to look. They open `annotated-diff.html` straight from the filesystem,
with no server and no install, and read a unified diff in which the hunks that
need comment carry the reviewer's own annotation beside them, each finding's
severity stated as a word, and jump links that take them from one finding to the
next.

**Why this priority**: This is the artifact's whole reason to exist, and it is
the half that satisfies the catalog entry already shipped in ART-001. A reader
who can follow the annotated diff has received value even if they never write an
objection down. Every other requirement in this spec either serves this reading
or depends on it.

**Independent Test**: Open the shipped template from the filesystem with the
network unavailable. Both hunks render with their sample content, one annotated
and one clean, the annotated hunk's finding states a severity as a word, the jump
link reaches the finding and puts focus on it, the browser console reports
nothing, no load fails, and the theme control works. The only visible difference
from an online render is typeface substitution.

**Acceptance Scenarios**:

1. **Given** the shipped template on a local filesystem, **When** a reviewer
   opens it directly with no server running, **Then** the page renders in full,
   the browser console reports no error, and no content is missing.
2. **Given** the network is unavailable, **When** the same reviewer opens the
   file, **Then** every region stays completely readable and every control still
   operates; only the typeface substitutes.
3. **Given** the rendered page, **When** the reviewer reads the diff, **Then**
   two hunks are present — one carrying at least one annotation and one carrying
   none — each with representative sample content.
4. **Given** any diff row, **When** the reviewer looks at it on a monochrome
   screen or in a monochrome print, **Then** they can still tell an added row
   from a removed row from a context row, because the state is carried by a
   character in a fixed position and not by hue.
5. **Given** an annotation that is a finding, **When** the reviewer reads it,
   **Then** its severity appears as one of the words `blocking`, `major`, or
   `minor`, and not as a colour, a bar, or a glyph's fill.
6. **Given** an annotation that only explains a hunk, **When** the reviewer reads
   it, **Then** it carries no severity, and the absence does not render as a
   fourth, lower severity level.
7. **Given** the rendered page, **When** the reviewer follows a jump link between
   findings, **Then** focus moves to the target, not only the scroll position.
8. **Given** the rendered page, **When** the reviewer switches the theme,
   **Then** both themes render every region legibly and no meaning is lost.
9. **Given** a reviewer using a keyboard alone, **When** they tab through the
   page, **Then** every interactive element is reachable in the normal focus
   order and carries a visible focus indicator.
10. **Given** a hunk whose lines are long, **When** the reviewer reads the page at
    any supported width, **Then** the page itself never scrolls horizontally; any
    overflow is contained within the diff region.

---

### User Story 2 - Hand the objections back [US2] (Priority: P2)

Having read a hunk, the reviewer disagrees with it, or with the annotation on it.
They attach an objection to that hunk, repeat for as many hunks as they want,
then copy every objection they wrote out of the page in one action: either as a
pull-request comment, or as an instruction to paste into a coding agent.

**Why this priority**: Without it the reading is stranded in a browser tab and
has to be retyped from memory, which is the failure the contract's export
obligations exist to prevent. It is P2 rather than P1 only because US1 delivers
standalone value first: this story depends on the hunks existing and on each one
being individually addressable.

**Independent Test**: Type an objection into one of the two hunks, leave the
other empty, and invoke each export control. Each export carries exactly the one
objection written, naming the hunk it attaches to, and carries nothing from the
empty field.

**Acceptance Scenarios**:

1. **Given** either hunk, **When** the reviewer opens its objection control using
   the keyboard alone, **Then** a labelled text field appears and receives their
   typing.
2. **Given** an objection typed into one hunk and none in the other, **When** the
   reviewer invokes an export, **Then** the exported text carries that one
   objection and no placeholder or empty entry for the other.
3. **Given** any exported text, **When** the reviewer reads it away from the
   artifact, **Then** it names the artifact, the change it belongs to, and the
   hunk each objection attaches to, so it can be acted on alone.
4. **Given** a reviewer who edits an objection and immediately exports, **When**
   the export is produced, **Then** it carries the edited text, because it is
   derived from live state at the moment of invocation.
5. **Given** the browser refuses clipboard access, which is common over the
   local-file scheme, **When** the reviewer invokes an export, **Then** the
   artifact reveals the full text in a selectable field, moves focus to it, and
   says so in words rather than reporting success.
6. **Given** a successful copy, **When** the reviewer looks for confirmation,
   **Then** it is stated in text, not carried by colour or animation alone.
7. **Given** the two export controls, **When** the reviewer reads their labels,
   **Then** each names its destination ("Copy as prompt", "Copy as Markdown")
   rather than the mechanism.
8. **Given** two exports invoked before the first settles, **When** both settle,
   **Then** only the later invocation's outcome is reported: the earlier one
   writes no status text, reveals no fallback text, and moves no focus.
9. **Given** a collapsed objection control, **When** the reviewer scans the page
   for what they have already recorded, **Then** the control itself says in text
   whether its hunk currently carries an objection, and that text reflects what
   the field holds now rather than what it held when the control was last opened.

---

### Edge Cases

- **A hunk with no objection.** Export walks only the non-empty fields. A hunk
  the reviewer skipped contributes nothing, not an empty heading.
- **No objection at all.** The reviewer invokes an export having written nothing.
  The artifact must not produce a document asserting a conclusion the reviewer
  never reached; it says in text that nothing was recorded and denies that this
  is approval.
- **A hunk with no annotation.** The clean hunk is a deliberate state, not a
  half-filled one. It must read as clean rather than as broken or unfinished, and
  it must say so in words rather than by an empty space where an annotation would
  have been.
- **An annotation with no severity.** Severity is optional and marks findings
  only. An explanatory annotation carries no tag, and the absence must not render
  as a fourth level below `minor`.
- **A monochrome screen or print.** This is the sharpest edge in the artifact,
  because a unified diff is conventionally colour-only. Every distinction — added
  against removed against context, annotated hunk against clean hunk, one
  severity against another — survives with hue removed.
- **A very wide hunk.** The diff must stay readable without the page scrolling
  horizontally. The containment strategy is deferred to Clarify.
- **Clipboard refused.** Covered by US2 scenario 5. Silence here is a defect,
  because the reviewer believes they hold the text.
- **Two exports raced.** Covered by US2 scenario 8. This is not hypothetical: the
  three templates shipped before slice 1 all get it wrong in both directions,
  announcing a failure that did not happen and handing over the wrong payload.
- **Storage refused for a local file.** The theme control keeps working for the
  session and reports no error. Persistence degrades, never the control.
- **Reduced motion requested.** Any motion this template adds is suppressed under
  that preference. The canonical blocks cover their own.
- **A brand typeface unavailable.** Heading rank still reads, because hierarchy
  rides on semantic level, size, and weight rather than on typeface identity. The
  diff's own rows are unaffected, because their state is carried by a character
  rather than by a face.
- **Scripting unavailable.** US1 survives whole: both hunks, their diff rows,
  their annotations, the severity words, and the standing intro are markup and
  stay readable. US2 does not, and the degradation is uneven — the per-hunk
  objection controls are built at load, so they simply do not appear, while the
  export controls sit in markup and would remain on screen offering an action
  nothing can perform. A control that cannot act is worse than an absent one,
  because a reader who cannot see a result has no way to tell a broken copy from
  a silent one. The artifact MUST therefore ship the export region hidden and let
  the script reveal it, so the affordance appears only where it works. This is
  the same resolution slice 1 reached and costs the same one line, already inside
  the markup figure declared below. The remaining degradation — no objection
  controls, so no objections to export — is accepted rather than a defect,
  because US1 is P1 and delivers its value alone.

## Requirements *(mandatory)*

### Functional Requirements

#### The artifact and the single-file contract

- **FR-001**: The gallery MUST carry a new artifact at
  `speckit-pro/artifact-gallery/templates/annotated-diff.html`, whose file stem
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
  `03-code-review-pr.html`, which is the `source.file` its catalog entry
  declares, and the repository it names MUST be the one the contract names.
- **FR-010**: The artifact MUST contain no relative reference into a skills
  directory of the form the Codex payload build rewrites, so its shipped copies
  stay byte-identical to their source on both platforms.
- **FR-010a**: The artifact's own displayed title MUST be **byte-identical** to
  the `title` its catalog entry carries — `Annotated Diff` — and MUST sit outside
  every fill region carrying `id="artifact-title"`, so no fill can delete it.
  This is stated as a requirement because **nothing in the suite asserts the
  agreement**. Slice 1 shipped this wrong: its artifact title differed from its
  catalog entry in case, every export therefore opened with a value the catalog
  did not carry, the whole suite passed green, and only independent review caught
  it. The check is a string comparison between the artifact and the catalog, not
  a reading of either, and it MUST be recorded with the acceptance evidence under
  FR-046.

#### The regions a reviewer reads

- **FR-011**: The artifact MUST ship a `hunks` region holding the diff, and a
  `feature-header` region carrying the change's identity. Both are fixed:
  `hunks` by the design concept's Q6, which makes it a list slot, and
  `feature-header` by the export payload contract, which reads the change's
  identity out of it. [NEEDS CLARIFICATION: the rest of the slot inventory — the
  remaining slot names, their granularity, and each slot's `Source:` value,
  including whether the closed source-artifact set must gain a member for a slot
  whose content comes from the change itself rather than from a SpecKit artifact.
  Deferred here deliberately: the design concept's own Open Questions assign this
  to a dedicated Clarify session on the stated ground that slot names must not be
  invented before the upstream source is read, and the upstream is fetched
  read-only at implement time.]
- **FR-011a**: `feature-header` MUST carry `id="feature-id"` on the feature
  identifier and `id="feature-name"` on the feature name, because both exports
  read them to name the change. It is chrome rather than a reader-facing region
  and is not pinned in the validation floor. Four shipped templates already carry
  these two identifiers; slice 1 is the nearest.
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
  the closed set of source artifacts the fill-region validation recognises.
- **FR-017a**: The `hunks` inventory line's `Fills:` value MUST instruct the
  authoring agent to keep a stable unique anchor on every hunk item, because the
  fill-region validation requires this list slot's items to stay individually
  addressable and because every exported objection names one. It MUST also
  instruct the agent that a hunk carrying no annotation says so in words. Both
  cost no line, since FR-014 already makes the line mandatory and it stays one
  line, and neither may contain a pipe. The inventory is the only agent-facing
  instruction the artifact holds, so an obligation that survives the first fill
  has to be written there.

#### What the port keeps and drops

- **FR-018**: The port MUST follow the fidelity model the design concept fixes at
  Q3: keep the upstream interaction mechanism and structure, restyle entirely to
  brand tokens so no upstream colour value survives, drop upstream sections that
  map to no fill region, and author fresh what the final-PR stage needs.
- **FR-018a**: The port MUST NOT carry upstream's own diff colouring into the
  branded artifact. Upstream colours are outside the kit's audited set, and the
  convention they encode is the one FR-019 forbids.
- **FR-018b**: Every line of export and objection-capture behaviour is authored
  fresh. Upstream carries twelve lines of script in a single element and no
  button at all, so there is no export mechanism to port; the precedent is slice
  1's shipped routine, not the upstream file.

#### Reading a diff without colour

This is stated as its own group, separate from the general accessibility rule at
FR-033, because a unified diff is the one place in the gallery where the
conventional rendering *is* the violation. A reviewer reading "no meaning by
colour alone" alongside a diff will read green-for-added and red-for-removed as
the normal case that rule was not aimed at. It is aimed at exactly this.

- **FR-019**: Added, removed, and context rows MUST be distinguishable **without
  hue**. Each row's state MUST be carried by a character or word in a fixed
  position that survives a monochrome rendering, a text-only reading, and a
  copy-and-paste out of the page. Colour MAY reinforce the distinction and MUST
  NOT be its only carrier.
- **FR-019a**: Severity MUST read as a **word** from the closed set `blocking`,
  `major`, `minor` — the vocabulary this repository already reviews in — rendered
  as text rather than as a colour, a bar, a dot, or a glyph's fill. Severity is
  optional on an annotation and marks findings only; an explanatory annotation
  carries none, and its absence MUST NOT render as a fourth level.
- **FR-019b**: The same rule binds every other distinction the diff draws: an
  annotated hunk against a clean one, a hunk header against its rows, a gutter or
  line-number column against the code beside it, and an annotation against the
  row it attaches to. Each MUST also be available as text, shape, glyph, or
  position.
- **FR-019c**: [NEEDS CLARIFICATION: the diff rendering model — how a margin
  annotation attaches to the row or rows it comments on, what a clean hunk
  renders in place of an annotation, whether individual line numbers are
  addressable as fragments, and how a hunk wider than the viewport is contained
  so the page itself never scrolls horizontally. Deferred to Clarify because each
  answer follows from the upstream markup, which is read read-only at implement
  time, and each has a direct and different cost against the line budget.]

#### The two hunks, and why a floor and a cap coincide here

- **FR-020**: The `hunks` region MUST ship **exactly two** hunks: one carrying at
  least one annotation, and one carrying none, so a reader sees both states.
- **FR-020a**: **The validation's minimum and this template's cap are the same
  number, which is unusual and is deliberate.** The fill-region validation fails
  a list slot on fewer than two anchored items, so two is a *floor*; nothing
  anywhere caps the count. The design concept's Q2 independently caps this
  template's anchor content at two hunks, because `annotated-diff` is the slice
  with the least headroom and each hunk carries diff rows rather than one line of
  prose. The two constraints meet at the same value.
  This is recorded because a later reader will compare the two slices and see
  what looks like an inconsistency: slice 1 read the same minimum as a floor and
  deliberately shipped *three* `file-by-file` items, on the reasoning that a
  region saying what each changed file does teaches nothing at two. That
  reasoning does not transfer. A hunk is not a homogeneous one-line statement,
  and the two states this region has to demonstrate — annotated and clean — are
  exactly two. A third hunk would add an instance rather than a kind, and would
  be paid for at the cost of a whole hunk's markup on the tightest budget in the
  feature. Two is therefore the demonstrating minimum *and* the ceiling, and
  neither number is an accident of the other.
- **FR-020b**: The clean hunk MUST read as **deliberately clean** rather than as
  broken, unfinished, or awaiting content. It MUST say in words that it carries
  no annotation, rather than leaving the space an annotation would occupy empty.
- **FR-020c**: `hunks` is the artifact's only list slot. Its grouping element
  MUST sit outside the marker pair so the container survives a fill, and every
  repeated item at the region's own top level MUST carry a stable, unique anchor
  in kebab-case. Its items MUST be elements that require an end tag, because the
  fill-region parser performs no implied closing and an unclosed item would
  report as nested and silently vanish from the region's top level.
- **FR-020d**: Every region MUST ship representative fictional sample content
  held to the minimum that demonstrates its shape: non-empty everywhere,
  expansive nowhere. Every region MUST use the same invented change, named once
  and reused.
- **FR-020e**: The artifact MUST say in visible text that its content is
  invented, in one sentence naming the invented change, placed **inside**
  `feature-header`'s marker pair so the first fill removes it. All five shipped
  gallery templates carry this sentence and all five place it there. Without it a
  reader opening the file cold reads a complete and plausible review of a change
  that never happened.

#### Attaching and exporting an objection

- **FR-021**: Each hunk MUST carry its own inline objection control: a
  keyboard-reachable disclosure plus a labelled text field, following the shape
  the gallery's shipped objection controls use — `module-map`,
  `implementation-plan`, and now slice 1's `pr-writeup` — so a reviewer meets one
  interaction across the gallery. `code-approaches` is not a precedent: it ships
  a single-choice selection control and no disclosure at all.
- **FR-021a**: Three properties of that pattern are stated here rather than left
  to "matching", because each is an accessibility obligation and a port that met
  the shape while missing them would still read as compliant. The disclosure's
  own control MUST state **in text** whether its hunk currently carries an
  objection, so a recorded objection is findable without opening every hunk and
  so the carried/not-carried state survives a monochrome rendering. The text
  field's visible label MUST be programmatically associated with the field;
  **placeholder text does not satisfy this**, because it is not an accessible
  name and it vanishes the moment the reviewer types. And that state text MUST be
  recomputed on **every change to the field** — not once at mount, and not only
  when the disclosure is next toggled — because a summary fixed at mount reports
  "no objection recorded" over a hunk that carries one, which is worse than
  reporting nothing. All three cost no line: the shipped routine already writes
  the state into the disclosure's accessible name, already builds a real label
  bound to the field, and already calls the same refresh from its input listener
  that it calls at mount.
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
- **FR-023**: An export MUST walk only the non-empty objection fields, and MUST
  carry each objection together with the anchor of the hunk it attaches to.
- **FR-023a**: Both exports MUST serialize the same structure and differ in
  exactly one line. Each opens with the artifact title, then the feature
  identifier and name, then a blank line, then a single lead line naming the
  kind, then one blank-line-separated block per non-empty objection. Neither
  export emits markdown syntax: the `markdown` kind names its **destination, not
  its encoding**, and the downstream feedback sweep reads the raw comment body
  where the line structure survives.
- **FR-023b**: An objection's reference line MUST read
  `<slot> / <item label>  (#<anchor>)` with two spaces before the parenthesis,
  matching the form every export-carrying template already emits. **This slice
  returns to the item-anchored form** the three older templates use, because
  capture here attaches to a repeated item rather than to a whole section. Slice
  1's `sec-<slot>` section anchor was a named departure justified by its capture
  granularity and does not carry over.
  [NEEDS CLARIFICATION: what the anchor's slug and the item's visible label are
  derived from for a hunk — a file path, a line range, both, or a caption the
  authoring agent writes — and what the artifact renders when two hunks would
  derive the same slug. Deferred to Clarify: the shape depends on how the
  upstream renders a hunk header, and a colliding anchor is the one failure the
  validation rejects outright, because a fragment resolving to two items resolves
  to neither.]
- **FR-023c**: The export routine MUST derive its items from the anchors present
  in the region at the moment of invocation, so a fill that adds or removes hunks
  is carried without a code change, and it MUST concatenate no value into a
  selector string. **This is a real difference from slice 1**, which pinned a
  fixed list of six slot names because its regions were a fixed set of sections;
  a list slot has no fixed count and pinning one would break the first real fill.
- **FR-023d**: Each objection control MUST be mounted so that it **follows the
  content it questions**. For an item anchor that is immediately after the item,
  which is the placement the three older templates use and which slice 1 departed
  from only because its anchor was a section heading.
- **FR-024**: An export MUST carry enough context to be acted on away from the
  artifact: the artifact, the change it belongs to, and the location each
  objection attaches to.
- **FR-025**: An export MUST NOT carry a conclusion the reviewer did not reach,
  and MUST NOT carry any value the reviewer could not have inspected on screen.
- **FR-026**: An export MUST be derived from the artifact's live state at the
  moment it is invoked, never from a value fixed when the file was written.
- **FR-027**: When two exports are invoked before the first completes, the
  artifact MUST report the outcome of the later invocation only. Each invocation
  MUST carry a token compared against the current one, and a settle belonging to
  a superseded invocation MUST change no status text, reveal no fallback text,
  and move no focus. **Both** settle paths need the guard, not only the rejection
  path: a slow success resolving after a fast failure would overwrite the failure
  message with "Copied" while the fallback field still holds the other kind's
  text.
- **FR-027a**: **The currency check MUST be scoped by effect, not by path.** It
  MUST sit where a status write or a fallback reveal actually lands, and every
  path MUST reach those effects through it. This is a requirement, not a
  refinement of FR-027, and the reason is a property of the routine this slice
  copies rather than a hypothesis about it: the status write is deferred behind a
  short timer, because the region is cleared and rewritten so a repeated
  identical message is announced a second time, and the focus move to the
  fallback field is deferred behind a longer one. **So a path that decides
  synchronously still lands asynchronously**, in a later turn, after a second
  invocation may already have completed and re-hidden the field. A path-scoped
  guard reads correct, exempts those paths as "synchronous", and is not correct.
  Scoping by effect makes the exemption unnecessary rather than merely safer: the
  synchronously-decided paths carry the current token and pass the same check, so
  no path is unguarded and none needs a rationale for being so.
- **FR-027b**: Slice 1 ships this guard at **four** check sites — the entry to
  the status write and the deferred callback it schedules, and the entry to the
  fallback reveal and the deferred callback *it* schedules. That shape MUST be
  reproduced, because those four sites are exactly the points at which an effect
  lands. Reproducing fewer is the path-scoped guard FR-027a rejects.
- **FR-027c**: The defect this guard prevents is **present in all three
  export-carrying templates shipped before slice 1**: each runs the same
  unguarded settle and none carries a currency check, so a rejected first copy
  announces a failure that did not happen and places the first kind's payload in
  the fallback field after the second kind copied successfully. This artifact
  MUST NOT reproduce it. Repairing those three is explicitly out of scope.
- **FR-028**: Every export control MUST be reachable and operable by keyboard
  alone, and MUST report its outcome in text rather than by colour or animation
  alone. The artifact MUST carry exactly one live status region for that
  reporting, present from load rather than created on demand, and that region
  MUST sit outside every fill region. The placement is the requirement, not a
  preference: a status region a fill could delete would make every later failure
  silent.
- **FR-029**: When clipboard access fails or is refused, the artifact MUST take
  all four steps of the contract's failure path: (1) reveal the same exported
  text in a field the reader can select; (2) keep that field **focusable and not
  disabled**, give it an accessible name, and move focus to it; (3) report the
  single failure message; and (4) **not** report success. Step 2 is not
  decoration — focus arriving at an inert or unnamed control strands a reader who
  cannot see the reveal, and a disabled field cannot be focused at all. Failing
  silently and reporting success are the same defect wearing different clothes:
  the reader believes they hold text they do not hold.
- **FR-029a**: Three obligations attach to that path, each already satisfied by
  the shipped routine, so none costs a line. The artifact MUST NOT make a
  **second copy attempt** through any deprecated interface after the first fails,
  because that attempt's result is ambiguous and reporting an uncertain success
  is exactly what the contract forbids. Every invocation MUST re-hide the
  fallback field before it attempts its copy, so a later successful export never
  leaves an earlier failure's payload on screen beside a success message. And the
  failure path MUST leave the browser console silent, which means the rejection
  is handled rather than left to surface as an unhandled rejection.
- **FR-030**: When no objection has been written, an export MUST say in text that
  nothing was recorded and MUST deny that this is approval, rather than produce
  an empty or invented document.
- **FR-030a**: The artifact's export literals MUST match the contract slice 1
  authored at `specs/art-003-final-pr-template-set/contracts/export-payload-contract.md`.
  **This slice's noun is already the contract's noun.** Two shipped templates
  capture objections, so the two empty-state bodies, the six feedback messages,
  and the clipboard-failure message are reused **byte for byte** with no new row
  and no new wording. Only the two lead lines are authored fresh, because each
  names the location kind an objection attaches to and this artifact's is a hunk.
  Slice 1 had to author six fresh literals in a new noun; this slice authors two.
- **FR-030b**: The clipboard-failure message MUST be the **only** failure
  message, covering every failure mode, and it MUST assert **no cause**. The
  artifact cannot tell a refused permission from an unfocused document from a
  browser policy from an absent interface, so naming one would be a guess
  presented as a diagnosis. The constraint costs no line, because it forbids
  messages rather than requiring them.
- **FR-030c**: No string literal inside the artifact's script may name the
  local-file scheme. Feedback text says "opened from a filesystem" instead. This
  is a validation requirement, not a wording preference: the gallery scanner's
  URL-shaped pattern treats a script string literal that opens with a scheme and
  a colon, or that carries a scheme followed by two slashes anywhere, as an
  external reference and fails the file.

#### Accessibility

- **FR-031**: Every foreground and background pairing the artifact uses MUST come
  from the kit's audited set. Colours introduced outside the embedded block are
  outside the audit and MUST NOT be relied on.
- **FR-031a**: The pairings the artifact actually uses MUST be recorded with the
  acceptance evidence under FR-046, each traced to the audited row that clears it
  and to the role that row permits — body text, large text, or meaningful
  non-text. Without the list FR-031 is a claim a reviewer can only take on trust,
  because the audit lives in a header that does not ship and the artifact carries
  only token names. Recording it beside the render evidence rather than as an
  in-file comment discharges the same obligation at zero cost to the line budget,
  which matters more here than on slice 1.
- **FR-032**: The artifact MUST NOT use the subtle border token for any boundary
  that conveys meaning; a meaningful boundary uses the strong border token. For
  this artifact that resolves to a **checkable outcome rather than a judgement**:
  the subtle border token MUST appear nowhere in the authored CSS. Every boundary
  a diff draws — a hunk from the page, a row from its neighbour, a gutter from
  the code, an annotation from the row it attaches to, an objection disclosure, a
  text field — separates content from its surroundings and therefore carries
  meaning, which is the one role that token is audited against. The outcome
  version is a search, costs no line, and removes lines if anything; the
  judgement version has to be re-made at every boundary by whoever reviews it,
  and a boundary wrongly judged decorative fails at a contrast ratio near one
  rather than visibly.
- **FR-032a**: The artifact MUST NOT name a token in a CSS comment in order to
  explain that token's absence. FR-032's check is a search over the authored CSS,
  and a comment naming the token fails it.
- **FR-033**: No status, action, or distinction the artifact draws may be carried
  by colour alone. Each MUST also be available as text, shape, glyph, or
  position, and MUST survive a monochrome print or screenshot. FR-019 states the
  sharpest instance of this rule; this one binds everything else.
- **FR-034**: Every jump link between findings MUST move **focus** to its target,
  not only the scroll position, so a keyboard or screen-reader user arrives where
  a sighted mouse user arrives.
- **FR-035**: The artifact MUST stay readable with **no horizontal page scroll**
  at any supported width. Any overflow a wide diff produces MUST be contained
  within the diff region rather than pushing the page.
- **FR-036**: The artifact MUST add no positive tab index, MUST trap focus
  nowhere, and MUST NOT suppress the kit's focus indicator without an equivalent
  replacement.
- **FR-037**: Any motion the artifact itself introduces MUST be suppressed for a
  reader who has asked for reduced motion.
- **FR-038**: Where the artifact names a heading typeface explicitly it MUST use
  the display token, and **only on the first two heading levels**, which are the
  levels the embedded block assigns it. From the third level down the block
  assigns the body token at a heavier weight, and it records that applying the
  display face to every level was a fidelity defect caught against the brand
  source. Heading rank MUST ride on semantic heading level, size, and weight
  rather than on typeface identity.
- **FR-038a**: The heading typeface token is `--rc-font-display`. No other
  heading-typeface custom property is defined anywhere in the embedded block, and
  an undefined custom property fails **silently**: the declaration falls through
  to whatever fallback it named, so a typo renders plausibly and is invisible to
  review. The artifact MUST reference no custom property the embedded block does
  not define. The cheapest way to satisfy both this and FR-038 is to name no
  heading typeface at all and inherit the block's own assignments.
- **FR-039**: If the artifact needs the current theme it MUST read the resolved
  theme attribute from the document root, and MUST NOT read stored theme state
  itself or place a stored value into markup, a selector, or any executable
  position.

#### Catalog, validation, and payload

- **FR-040**: The change MUST flip exactly one catalog value: this entry's
  `status`, from `planned` to `shipped`. It MUST change no other value on this
  entry, no other entry, and no shared foundation file (the contract document,
  the brand kit, the head block, the signal vocabulary, or the export
  vocabulary).
- **FR-041**: The fill-region validation MUST gain a floor row for this template.
  The floor literal traces to the roadmap and to nothing else, so the row names
  only slots the roadmap names for this template.
- **FR-042**: The fill-region validation MUST gain a list-slot row for this
  template naming `hunks` and no other slot.
- **FR-042a**: Whether the validation's closed source-artifact set must also gain
  a member depends on the inventory FR-011 defers. Slice 1's change to shared
  validation was three literals; this slice's is **two, or three if the inventory
  needs a source this repository's per-feature artifacts do not supply**. No
  other change to shared validation is in scope.
- **FR-043**: The artifact MUST ship its export region hidden and reveal it from
  the routine that already runs at load, so the affordance appears only where
  scripting can perform it.
- **FR-044**: The full repository suite MUST pass with zero failures and above
  the recorded baseline, including the gallery scanner, the fill-region
  validation, and Layer 1 structural validation.
- **FR-045**: The change MUST account for the generated-artifact contract, since
  the gallery ships inside the plugin payload and a new artifact file changes
  shipped bytes on both platforms.
- **FR-046**: A manual render of the shipped file from the local-file scheme MUST
  be recorded as acceptance evidence, in both themes, with the network
  unavailable, and including a monochrome rendering that demonstrates FR-019.

### Reviewability Notes *(if applicable)*

No `Reviewability-Exception` pragma is claimed, and none is available: the
accepted classes are refactor, infra, and upgrade, and none honestly describes
net-new template work. Splitting further is not available either, because a
self-contained HTML artifact cannot be divided across two pull requests and still
render from the local-file scheme. One template per pull request is already the
thinnest vertical slice this work admits.

The slice therefore clears the boundary on cost discipline or not at all, and the
lever is the one the design concept named at Q2: cap the anchor content. Two
hunks is that cap.

### Reviewability Budget *(mandatory)*

**The basis is a measurement, not a multiplier.** Slice 1 is the only realized
measurement of this exact work class on this branch: it shipped 735 authored
lines — 227 CSS, 334 JavaScript, 174 markup — against a declared 758. That
replaces every earlier estimate derived from an upstream-line multiplier.

Decomposed against slice 1's realized figures:

| Component | Target | Basis |
|---|---|---|
| Export and objection-capture JavaScript | ~330 | slice 1's 334, same routine and the same four-site currency guard; two hunk mounts instead of six section mounts, offset by deriving items from live anchors rather than a pinned list |
| CSS | ~240 | slice 1's 227 plus a margin for the diff-specific structure a document template never carried |
| Markup | ~185 | fewer regions than slice 1's seven, but each hunk carries diff rows rather than a paragraph |
| **Total** | **755** | warn, with 45 lines of headroom below the 800 block |

**CSS is the risk, and it is sharper here than on slice 1.** A diff view needs
line-state, gutter, hunk-header, and severity styling that a document of titled
prose sections never had. The sensitivity is unforgiving:

| CSS lines | Total | Result |
|---|---|---|
| 200 | 715 | warn, 85 spare |
| 240 | 755 | warn, 45 spare — the declared target |
| 280 | 795 | warn, 5 spare |
| 320 | 835 | **block** |

Upstream `03-code-review-pr.html` measures 638 lines: 389 of them CSS, 237
markup, and 12 lines of script in a single element, with three disclosure
elements and no button at all. The brand kit replaces most of that CSS, but the
diff-specific part has no counterpart in the kit and must be authored. And
because upstream ships no export mechanism, every line of export behaviour is
authored fresh with slice 1's routine as its only precedent.

**A CSS ceiling is adopted at Plan as an explicit, checkable constraint**, using
the measuring instrument slice 1's quickstart already records rather than a
second one. The first checkpoint fires after the diff CSS and **before** any
export work, so an overrun surfaces at roughly 240 lines written rather than at
755.

The figure below excludes the 458 lines of canonical embedded blocks a reviewer
never reads because they are byte-verified copies: the brand-kit block at 318
lines and the gallery-head block at 140.

- **Primary surface**: docs/process (a shipped template file)
- **Secondary surfaces, if any**: seed/config (one catalog value), harness/adapter (the fill-region validation literals)
- **Projected production files**: 1 (net-new: the artifact itself)
- **Projected total files**: 13, carried from slice 1's measured count for the
  same artifact shape and re-measured at Plan by the setup gate. Below the warn
  threshold of 15 either way.
- **Budget result**: warn — above the warn threshold and below the block
  threshold. CSS is the only dimension that can miss the figure; the export floor
  cannot, because it is measured against four shipped implementations of the same
  routine.
- **Split decision**: This spec **is** the split. ART-003 was re-declared at
  scaffold as three stacked slices, one template per pull request, after the
  earlier feature's first slice shipped two templates of the same kind and
  measured a hard block that forced a mid-implement re-slice. This spec covers
  slice 2 only. Re-measure and re-declare at this slice's Plan phase: the setup
  gate reads a declaration rather than measuring the tree, and it will not catch
  a stale number for you.

**The declaration is the last line of this section on purpose.** The gate's
parser takes the *last* phrase match in the whole file and reads the first number
within forty characters of it, so any prose placed after this line that mentions
the phrase near any other number silently becomes the declared figure. That trap
fired three times on slice 1 — on a spec identifier, on a filename, and on a
table header. Nothing below repeats the phrase.

- **Projected reviewable LOC**: **755**

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope
  budget, traceability, verification evidence, known gaps, and rollback or
  feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- The pull request MUST base on slice 1's branch, never on the default branch.
- Deferred work MUST name the follow-up spec or issue. Slice 3, the generation
  step, the ready flip, and the unrepaired currency defect in the three older
  templates are all named deferrals here.
- Known gaps MUST name every gap the pull request carries, including the ones
  slice 1 recorded that remain true: the plan-phase estimator reports a
  projection of zero for a production surface of this file type, so its green line
  reads as reassurance it cannot supply; the gate's declaration parser takes the
  last phrase match in a file; the shipped payload documents no fill-region
  grammar; the validation binds only the templates its floor names, so a shipped
  non-floor template is never parsed; no check reads a catalog entry's declared
  export kinds against the artifact; nothing compares the clipboard-failure
  message shared across what will be five templates; the contract document that
  pins the export literals will dangle when this feature is archived, exactly as
  its predecessor's did; and pasted into a pull-request comment the export's two
  header lines render as one paragraph.
- Known gaps MUST also name the one this slice adds: **nothing asserts that an
  artifact's title agrees with its catalog entry's title**, which is how slice 1
  shipped a mismatch through a green suite. FR-010a closes it for this template
  by hand; closing it in general would be a change to shared validation.
- Review order MUST put the authored markup and the diff CSS ahead of the
  embedded canonical blocks, which are byte-verified copies rather than material
  to read.

### Key Entities

- **The artifact**: one HTML file carrying a `hunks` region and a
  `feature-header` region, an attribution header, a slot inventory, sample
  content declared as invented, per-hunk objection fields, and two export
  controls.
- **A hunk**: one contiguous span of the diff, individually addressable, carrying
  its rows, zero or more annotations, and one objection field. Two ship.
- **An annotation**: a comment attached to a hunk. It carries a severity only
  when it is a finding, and that severity is one of three words.
- **A fill region**: a named span of the artifact an authoring agent replaces
  later, delimited by one paired comment marker and described by one inventory
  line.
- **The slot inventory**: the machine-readable list of regions. It is the only
  thing that tells an authoring agent what it must fill, which is why it is bound
  in both directions to the regions the body delimits.
- **The catalog entry**: the routing row that already exists for this template,
  declaring its title, its stage, its trigger, its provenance, its export kinds,
  and the single status value this slice changes.
- **A reviewer objection**: free text a reviewer attaches to one hunk, carrying
  that hunk's anchor, and appearing in an export only when non-empty.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer opens the artifact from a filesystem with no server and
  no install and reads both hunks; the browser reports zero console messages,
  zero failed loads, and zero missing content.
- **SC-002**: With the network unavailable, 100% of the artifact's content stays
  readable and 100% of its controls stay operable; the only observable difference
  is typeface substitution.
- **SC-003**: A reviewer completes the whole loop — reading a hunk, attaching an
  objection, and exporting it — using the keyboard alone, with zero mouse
  interactions required.
- **SC-004**: An export produced after writing an objection in 1 of the 2 hunks
  carries exactly 1 objection, naming the hunk it attaches to, and carries zero
  entries for the untouched hunk.
- **SC-005**: With clipboard access refused, 100% of export attempts reveal the
  full text in a selectable focused field and state the outcome in words; zero
  report success.
- **SC-006**: In a monochrome rendering a reader tells added, removed, and
  context rows apart with 100% accuracy and reads every severity as a word; zero
  distinctions the artifact draws are lost when hue is removed.
- **SC-007**: Two exports invoked before the first settles produce exactly 1
  reported outcome, the later one; the superseded invocation performs zero status
  writes, zero fallback reveals, and zero focus moves.
- **SC-008**: The artifact's displayed title and its catalog entry's title
  compare equal with zero characters of difference, including case, verified by
  comparison rather than by reading.
- **SC-009**: Both embedded canonical blocks compare byte-identical to their
  canonical files, with zero characters of drift.
- **SC-010**: The full repository suite passes with zero failures and above the
  recorded baseline, and the fill-region validation binds this template rather
  than passing vacuously.
- **SC-011**: Exactly one catalog value changes across the whole slice, and zero
  shared foundation files are edited.
- **SC-012**: An authoring agent reading only the artifact's own inventory can
  name every region and what fills each, with zero regions undocumented and zero
  documented slots lacking a region.
- **SC-013**: The finished change's authored review surface is measured against
  the gate rather than estimated, before the pull request is opened, and the
  figure declared at Plan is the measured one. Zero pull requests open carrying a
  stale or undeclared size figure.

## Assumptions

- The upstream source `03-code-review-pr.html` is fetched read-only at implement
  time from the upstream repository the contract names, kept outside this
  repository's tree in the session scratchpad, and never staged. Only the branded
  derivative is committed. This is why the slot inventory and the diff rendering
  model cannot be settled before implement-time fetch, and it is why FR-011,
  FR-019c, and FR-023b carry clarification markers rather than invented answers.
- Port fidelity follows the model the design concept fixes at Q3: keep the
  upstream interaction mechanism and structure, restyle entirely to brand tokens
  so no upstream colour survives, drop upstream sections that map to no fill
  region, and author fresh what the final-PR stage needs.
- The catalog entry's declared export kinds are taken as given from ART-001 and
  are not renegotiated here; changing them would be a second catalog value and
  therefore a contract amendment rather than a port.
- The objection control reuses the disclosure-plus-labelled-field pattern the
  gallery's shipped templates already carry, so no new interaction is invented.
- The export payload's serialized shape is inherited from the contract slice 1
  authored, and this artifact's noun already matches two shipped templates, so
  only the two lead lines are authored fresh.
- Slice 1's shipped artifact is one commit old on this branch and is the
  precedent for every shared mechanism. Its export routine is copied rather than
  reinvented, and the four-site currency guard is the part that must not regress.
- The budget is derived from slice 1's realized measurement rather than from any
  multiplier, and it is re-declared at Plan against the real port. The feature is
  not shrunk to chase the number: two hunks, both export kinds, and per-hunk
  capture are decisions the interview fixed and the shipped catalog entry already
  promises.
- Nothing in this slice may be shaped to suit slice 3, and no merge happens
  inside this run.

## Dependencies

- **ART-001** (shipped): the brand kit, the head block, the single-file contract,
  and the catalog entry this slice flips.
- **ART-003 slice 1** (open as a pull request, present on this branch): the
  shipped `pr-writeup` artifact, its export routine, its four-site currency
  guard, its export payload contract, and its measuring instrument.
- **ART-010** (downstream): the generation step that fills these regions with a
  real diff. It reads this artifact's inventory, so the inventory is the
  interface this slice owes it.
- **ART-008** (downstream): the feedback sweep that reads exported objections
  from a pull-request comment, classifies them, and routes them through
  consensus. It is why every exported objection must name the hunk it attaches
  to.

## Out of Scope

- `flowchart`. That is slice 3, a separate spec off a separate branch.
- Generation and authoring logic, and the ready flip. That is ART-010.
- The UAT walkthrough template. That is ART-009, and it is repo-authored rather
  than an upstream port.
- Any change to the contract document, the brand kit, the head block, the signal
  vocabulary, the export vocabulary, or any catalog value other than this entry's
  own status.
- Any change to another catalog entry, including the one slice 3 will flip.
- **Repairing the invocation-currency defect in the three templates shipped
  before slice 1.** Each carries it; none is touched here. FR-027c records the
  defect and names it a deferral.
- A general guard binding any catalog entry that reads `shipped` to the
  fill-region checks. The validation resolves its universe by intersecting the
  catalog with its floor, so a shipped template the floor does not name is never
  parsed at all. That restriction is a recorded decision inside the module, and
  widening it here would contradict it. This slice closes the gap for
  `annotated-diff` alone, by adding its floor row.
- A general check that an artifact's title agrees with its catalog entry's title.
  FR-010a closes it for this template; closing it for all of them is a change to
  shared validation and belongs to a spec that owns that surface.
- An artifact-side gate on a catalog entry's declared export kinds. No check
  reads that field against the artifact body, so an entry can declare an export
  kind the artifact does not ship and stay green.
- Recording the fill-region grammar in the shipped payload. The contract document
  documents none of it, and amending that document is out of scope here.

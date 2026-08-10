# Feature Specification: Draft-PR Template Set (ART-002)

**Feature Branch**: `art-002-draft-pr-template-set`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Port the four planning-review templates the draft-PR
stage routes — implementation plan, spec explainer, code approaches, module map —
as Racecraft-branded self-contained single-file artifacts with documented fill
regions, so the plan-stage review checkpoint has documents to populate instead of
raw markdown. Each artifact obeys `speckit-pro/artifact-gallery/SPA-CONTRACT.md`;
the routing catalog change is exactly four status flips; delivery is two
sequential slices. Scoping decisions are recorded in
`docs/ai/specs/.process/ART-002-design-concept.md` (Q1-Q10)."

## User Scenarios & Testing *(mandatory)*

The plan stage of the staged review workflow ends at a draft pull request an
operator reads before any code is written. Today that checkpoint has no artifact
surface: the reviewer falls back to raw markdown, and whatever they conclude
stays in their head or in an ad-hoc comment. This feature delivers the four
documents that checkpoint routes to.

Three people read these artifacts, and they read them differently:

- **The reviewing operator** opens a filled artifact at the checkpoint, forms a
  judgement, records it, and carries it back out to a coding agent or a pull
  request comment.
- **The authoring agent** (delivered later, by ART-007) fills each artifact's
  named regions from the feature's own spec, plan, tasks, and design concept.
  It reads the artifact's own inventory to know what to fill.
- **The gallery browser** is choosing which template fits a situation and judges
  by looking at a rendered document, not by reading a description.

The four stories below are ordered by delivery. **Slice 1** is US1 and US2 — the
two templates the draft-PR stage routes unconditionally, so nothing downstream
works without them. **Slice 2** is US3 and US4 — the two templates that route
only when their signal is present. Slice 2 branches after slice 1 merges.

### User Story 1 - [US1] Implementation Plan template (Priority: P1)

An operator opens the implementation-plan artifact at the plan-stage checkpoint.
They see the phases the change is broken into, how data moves through it, what
each screen is meant to look like, what could go wrong, and the full inventory of
tasks. Reading phase three they disagree with its ordering, so they attach an
objection to that phase, and to no other. When they have finished reading they
carry their objections out of the document in one action — as an instruction to
paste into a coding agent, or as text for a pull request comment.

**Why this priority**: The draft-PR stage routes this artifact every time, and it
is the one carrying the most of what the reviewer must judge. It is the primary
reason the checkpoint exists. Nothing downstream of the plan stage has a document
to populate until this ships.

**Independent Test**: Open the shipped template straight from a local filesystem
with the network off. Confirm it renders complete, attach objections to two
different phases, invoke each export, and confirm the produced text carries both
objections, each naming the phase it attaches to, and nothing the reader did not
write.

**Acceptance Scenarios**:

1. **Given** the template file opened directly from a local filesystem with no
   server running, **When** the reader scrolls the whole document, **Then** every
   section is present and readable, the browser reports no error and no failed
   load, and the only difference from an online view is which typeface is used.
2. **Given** the reader has typed an objection against one phase and left the
   others empty, **When** they invoke "Copy as prompt", **Then** the produced
   text carries that one objection, names the phase it attaches to, names the
   artifact and the feature it belongs to, and carries no objection for any phase
   the reader left empty.
3. **Given** the reader has recorded no objection anywhere, **When** they invoke
   either export, **Then** the result states that nothing was recorded rather
   than asserting a conclusion the reader did not reach.
4. **Given** the browser refuses clipboard access because the document was opened
   from a filesystem, **When** the reader invokes an export, **Then** the artifact
   reveals the same text in a field the reader can select and copy by hand, and
   never reports success.
5. **Given** a reader navigating by keyboard alone, **When** they tab through the
   document, **Then** they reach every objection field and both export controls,
   each shows a visible focus indicator, and no element takes focus out of the
   document's normal order.
6. **Given** an authoring agent reading the file, **When** it looks for the
   regions it must fill, **Then** each region is delimited by a matched
   start/end comment pair naming that region, and the file's own inventory names
   every one of them.

---

### User Story 2 - [US2] Spec Explainer template (Priority: P2)

A reviewer who has not read the specification opens the spec-explainer artifact.
They get the point of the feature in a sentence, then what it will and will not
do, then the acceptance criteria — folded away until they want them — then the
questions that came up during clarification and how each was answered. They read,
they understand, and they leave. The document asks nothing of them and offers
them nothing to carry away, because there is nothing for them to produce.

**Why this priority**: Also routed unconditionally at the draft-PR stage, so it
ships in the same slice. It is second because it is the simpler artifact: it is
declared read-only, so it carries no capture and no export.

**Independent Test**: Open the shipped template from a local filesystem, confirm
every section renders, confirm the acceptance criteria collapse and expand by
keyboard, and confirm the document offers no export or capture control anywhere.

**Acceptance Scenarios**:

1. **Given** the template opened directly from a local filesystem, **When** the
   reader reads it end to end, **Then** they find a one-paragraph summary, the
   goals, the explicit non-goals, the acceptance criteria, and the clarification
   FAQ, each complete and readable.
2. **Given** the acceptance criteria are folded away, **When** the reader expands
   and re-collapses them using the keyboard alone, **Then** the control reports
   its own state in text and the criteria show and hide accordingly.
3. **Given** the artifact's catalog entry declares it read-only, **When** the
   whole document is inspected, **Then** it carries no export control, no copy
   affordance, and no field that records reader input.
4. **Given** a reader who asks their system for reduced motion, **When** they
   expand a folded section or switch the theme, **Then** nothing animates and
   nothing transitions.
5. **Given** an authoring agent reading the file, **When** it looks for the
   regions it must fill, **Then** each is delimited by a matched start/end
   comment pair and named in the file's own inventory.

---

### User Story 3 - [US3] Code Approaches template (Priority: P3)

Planning weighed two or three real ways to build the change. The operator opens
the code-approaches artifact and sees them beside each other, with the trade-off
that separates them stated plainly. They pick one, say why in a sentence, and
carry that decision out of the document so the coding agent builds the one they
chose.

**Why this priority**: Routed only when planning recorded a competing approach,
so it is not on the always-on path. It leads slice 2 because a chosen approach
changes what gets built, which makes it the higher-consequence of the two
conditional artifacts.

**Independent Test**: Open the shipped template, confirm the approaches render
side by side, select one, write a reason, invoke each export, and confirm the
text names the chosen approach and the reason. Then reload, select nothing, and
confirm neither export invents a choice.

**Acceptance Scenarios**:

1. **Given** the template opened from a local filesystem, **When** the reader
   reads it, **Then** the compared approaches appear beside one another with the
   deciding trade-off stated for each.
2. **Given** the reader selects one approach and writes a reason, **When** they
   invoke "Copy as Markdown", **Then** the produced text names the approach they
   selected and reproduces their reason, and names the artifact and feature it
   came from.
3. **Given** the reader has selected nothing, **When** they invoke either export,
   **Then** the result says no approach was chosen rather than naming one.
4. **Given** a reader using the keyboard alone, **When** they move through the
   choice control, **Then** they can move between the approaches and commit a
   selection without a pointer, and the selected approach is reported in text.
5. **Given** the reader selects a second approach after selecting a first,
   **When** they invoke an export, **Then** the text carries only the current
   selection.

---

### User Story 4 - [US4] Module Map template (Priority: P4)

The change edits code the reviewer has to understand before they can read the
edit. They open the module-map artifact and see the modules involved drawn as
boxes with the calls between them as arrows, with the path the change actually
runs through picked out from the rest. One module looks wrong to them, so they
attach an objection to that module, and carry it out.

**Why this priority**: Routed only on a change that modifies existing code.
Last because it is the most situational of the four, and because its capture and
export behavior is the same shape as US1's, so it inherits a settled pattern.

**Independent Test**: Open the shipped template, confirm the module graph and the
distinguished path both render, attach an objection to one module, invoke each
export, and confirm the text carries that objection with the module it attaches
to. Confirm the distinguished path is still identifiable in a monochrome
screenshot.

**Acceptance Scenarios**:

1. **Given** the template opened from a local filesystem, **When** the reader
   reads it, **Then** the modules appear as labelled boxes, the calls between
   them as arrows, and the path the change runs through is distinguished from
   the rest.
2. **Given** the document rendered without color — printed in monochrome or
   viewed by a reader who cannot perceive the hue — **When** the reader looks for
   the distinguished path, **Then** it is still identifiable, because a label, a
   shape, a stroke treatment, or a position carries that meaning as well as color
   does.
3. **Given** the reader has attached an objection to one module, **When** they
   invoke "Copy as prompt", **Then** the produced text carries that objection and
   names the module it attaches to, and carries nothing for modules left empty.
4. **Given** the browser refuses clipboard access, **When** the reader invokes an
   export, **Then** the text is revealed in a selectable field and no success is
   reported.
5. **Given** an authoring agent reading the file, **When** it looks for the
   regions it must fill, **Then** each is delimited by a matched start/end
   comment pair and named in the file's own inventory.

---

### Edge Cases

- **Clipboard refused.** Clipboard access can be refused, and the artifact cannot
  tell why — a missing user gesture, an unfocused document, a browser policy, and
  an absent interface are indistinguishable from inside the document. Every
  export must reveal its text in a selectable field instead, and must never
  report success it did not achieve.
- **Nothing recorded.** A reader may invoke an export having written nothing and
  chosen nothing. The export says so; it never fabricates a conclusion.
- **Network unavailable.** With no network the typeface request fails. Every
  artifact stays completely readable and every control still works; only the
  typeface changes.
- **Storage refused.** A browser may refuse storage for a local file, so the
  theme preference cannot persist. The theme control still applies for the
  session and reports no error.
- **Recorded work is discarded on reload.** Nothing a reader records is stored,
  so a reload or a closed tab takes every objection, selection, and reason with
  it. The export is the only way work leaves the document, and a reader who does
  not know that loses a whole review silently — so the artifact says so before
  they rely on it rather than after.
- **Reduced motion requested.** Any motion an artifact adds beyond what the
  shared kit declares must be suppressed under that preference too.
- **Inventory and body disagree.** A template's documented slot inventory could
  name a region its body does not delimit, or the body could delimit a region the
  inventory does not name. Either direction misleads the authoring agent, so
  either direction is a failure.
- **Status and file disagree.** A template file present without its catalog entry
  flipped to shipped, or an entry flipped without the file, is a failure in both
  directions — as is a file in the template directory that no entry claims.
- **Upstream carries a prohibited construct.** An upstream source may use a
  construct the contract forbids. The port drops it; it is never carried across
  and never reintroduced.
- **A dropped region leaves residue.** Ten upstream regions are dropped, and a
  drop has to take its dependents with it: no heading left standing over nothing,
  no caption without its figure, and no in-page link pointing into a region that
  is gone. A template that reads as broken is worse than one that reads as thin.
- **A slot renders empty.** A slot shipped with no sample content leaves a
  gallery browser judging a template by an empty frame and leaves the manual
  render check exercising no real layout.
- **Sample content mistaken for real content.** Shipped example content must read
  as obviously fictional, so no reader takes it for the project's own data.
- **Feature-specific content outside a slot.** A region that names the feature,
  counts its work, or describes its shape but carries no marker pair keeps its
  shipped fictional content after the artifact is filled, where it reads as the
  project's own data. Every feature-specific region is a slot.
- **Second slice sees a changed catalog.** Slice 2 edits the same catalog file
  slice 1 already edited. It must branch from a state that already contains slice
  1's flips rather than reapplying them.

## Clarifications

### Session 1 — fill-region slot inventory (2026-08-10)

- **Q: What slots does each template carry, and at what granularity?**
  A: 21 slots, listed in FR-015 with the source artifact for each. One slot per
  section, never one per repeated item, because item count is a property of the
  feature and baking `phase-1`…`phase-4` into a template would cap a plan at four
  phases. Regions are flat, and each repeated item carries a stable anchor.
- **Q: What shape does the in-file slot inventory take?**
  A: One comment placed immediately after the attribution header, one line per
  slot reading `Slot: … | Fills: … | Source: …`, carrying none of the attribution
  header's own labels. Placement is load-bearing: the gallery scanner takes the
  first comment carrying any attribution element as the header, so an inventory
  placed before it that mentioned a licence or the upstream repository would be
  read as the header instead.
- **Q: Is the validation floor a subset or an equality?**
  A: A subset. A template may carry more slots than the roadmap names, and the
  both-ways inventory agreement binds the remainder.
- **Q: Does the module map's `modules` slot belong in that floor?**
  A: No, resolved unanimously across three perspectives. Floor membership would
  only prove a region of that name exists, never that its items are individually
  addressable, so the floor cannot verify the requirement even in principle. It
  gets its own assertion instead (FR-036a). Every floor entry traces to one
  document, so a reader can tell why each is there.
- **Q: Who authors the per-item capture controls?**
  A: The template's own behavior, at load time, mounted onto each item's anchor
  (FR-016a). Deferring them to the downstream authoring agent would ship
  artifacts with no working capture at all, since the capture requirement belongs
  to this feature's own user stories.

### Session 2 — export and capture interaction (2026-08-10)

- **Q: Does an objection field start revealed or collapsed?**
  A: Collapsed behind a native disclosure whose control states in text whether
  the item carries a note. Revealed fields would turn a document meant to be read
  into a form of five or six empty boxes.
- **Q: Does an export list every item or only recorded ones?**
  A: Only recorded ones. Emitting "no objection" for an untouched item asserts an
  approval the reader never gave, and a trailing count of untouched items is the
  same assertion in aggregate.
- **Q: What does an export say when nothing was recorded?**
  A: That nothing was recorded, and explicitly that the record is not an
  approval, in wording fixed per export kind. The realistic misreading of an
  empty export is approval.
- **Q: Is the code-approaches reason field required?**
  A: Optional. Requiring it would either strand the reader's real conclusion or
  pressure filler text, and an absent reason is named rather than omitted.
- **Q: What does a clipboard failure say?**
  A: One message for every failure mode, asserting no cause, because the artifact
  cannot distinguish a refused permission from an unfocused document or a browser
  policy. No deprecated second attempt, because an ambiguous result risks
  reporting a success that did not happen.

### Session 3 — upstream port fidelity (2026-08-10)

- **Q: Does each upstream drawing mechanism survive branding?**
  A: Yes, both, and neither is re-authored (FR-030). They differ only in how
  color is applied, and the port normalizes that to classes in both.
- **Q: Does any upstream source carry a prohibited construct?**
  A: No. All four were fetched and scanned, twice by independent
  implementations. Nothing is dropped for prohibition reasons.
- **Q: Which upstream sections map to which slots?**
  A: Fixed in full. Three regions are authored fresh, one borrows a layout shape,
  and ten upstream regions are dropped as feature-specific content no slot names.
- **Q: Where does upstream carry meaning in color alone?**
  A: Three places, each with a named remedy in FR-029 and FR-032. A fourth, the
  dashed edge with its explanatory caption, already complies and ports intact.
- **Q: Does anything conflict with the spec explainer's read-only declaration?**
  A: The one candidate, a tabbed walkthrough with a script, sits in a section
  that maps to no slot and is dropped. The template therefore ports with no
  script of its own, which makes its read-only status structural.

## Requirements *(mandatory)*

### Functional Requirements

`speckit-pro/artifact-gallery/SPA-CONTRACT.md` is the normative source for the
obligations restated below. Where this specification and that contract disagree,
the contract governs and the disagreement is a defect in this specification.

#### Artifact form — applies to all four templates

- **FR-001**: Each of the four templates MUST be one self-contained document
  file, with all behavior, styling, and content inside it, no sibling asset, and
  no build, bundle, or preprocessing step. [US1] [US2] [US3] [US4]
- **FR-002**: Each template MUST embed both canonical shared regions — the brand
  token block and the gallery head block — byte for byte including their markers,
  each pair appearing exactly once with its start before its end. [US1] [US2]
  [US3] [US4]
- **FR-003**: Each template MUST carry the upstream attribution header using the
  contract's exact labels. The upstream file it names MUST equal that template's
  own catalog entry's `source.file`. The upstream repository it names MUST equal
  the single repository the contract names, because a catalog entry's `source`
  object carries `origin` and `file` only and declares no repository of its own;
  the repository is named once in the contract rather than repeated per entry, so
  that is the value the header is checked against. [US1] [US2] [US3] [US4]
- **FR-004**: No template may contain any construct the contract prohibits,
  including inside a script's string literals and inside markup the artifact
  builds as a string. Where an upstream source uses one, the port MUST drop it
  rather than carry it across. [US1] [US2] [US3] [US4]
- **FR-005**: The brand typeface request carried inside the canonical head block
  MUST be the only external resource request any template makes. Any other asset
  MUST be embedded in the document, and only as an image or font media type.
  [US1] [US2] [US3] [US4]
- **FR-006**: Each template MUST render completely and report no browser error
  and no failed load when opened directly from a local filesystem with no server;
  with the network unavailable every control MUST still work and the only visible
  difference MUST be typeface substitution. [US1] [US2] [US3] [US4]
- **FR-007**: No template may contain a relative reference of the form the
  cross-platform payload build rewrites — a run of parent-directory segments
  ending in a skills directory followed by a path. Skills MUST be referred to by
  name in prose. [US1] [US2] [US3] [US4]

#### Routing catalog

- **FR-008**: The only change this feature makes to the routing catalog is four
  status values moving from planned to shipped. No identifier, category, title,
  guidance, stage, trigger, source, or export declaration may change, and no
  other entry may change. [US1] [US2] [US3] [US4]
- **FR-009**: No shared foundation file may be edited by this feature — not the
  brand token file, not the gallery head file, not the contract document, not the
  routing signal vocabulary, and not the upstream notice. [US1] [US2] [US3] [US4]
- **FR-010**: Each template file MUST exist if and only if its catalog entry
  reads shipped, and its filename stem MUST equal that entry's identifier, so no
  file is orphaned and no status is flipped without its artifact. [US1] [US2]
  [US3] [US4]

#### Fill regions

- **FR-011**: Each template MUST delimit every region an authoring agent later
  populates with a paired comment marker of the form
  `<!-- FILL:<slot>:START -->` … `<!-- FILL:<slot>:END -->`, each pair appearing
  exactly once in the file with its start before its end. A marker pair delimits
  the destination; it does not make that destination escape-free. A value written
  between a pair lands in HTML text, so a writer that assembles the file as a
  string MUST escape it for that context, and MUST NOT be able to emit a comment
  — a value carrying `<!--`, `-->`, or a marker-shaped sequence would forge or
  terminate a region boundary, moving a boundary the inventory still names and
  turning FR-013's both-ways agreement into a check on a file no one authored.
  A writer that sets text through the document rather than through string
  assembly satisfies this by construction. After any fill, FR-013 MUST still hold.
  [US1] [US2] [US3] [US4]
- **FR-012**: Each template MUST document its own slot inventory in a single
  HTML comment placed immediately after its attribution header and outside every
  fill region, carrying none of the attribution header's own labels or literals
  so the two cannot be confused. Each slot occupies one line, written as
  `Slot: <name> | Fills: <what fills it> | Source: <source artifact>`, those
  three labels in that order, with no pipe character inside any value. No
  central registry file may be added. [US1] [US2] [US3] [US4]
- **FR-013**: A template's documented inventory and its delimited regions MUST
  agree in both directions: every documented slot has a marker pair in the body,
  and every marker pair in the body is named in the inventory. [US1] [US2] [US3]
  [US4]
- **FR-014**: Every slot MUST ship containing representative, plainly fictional
  worked-example content, so a gallery browser judges the template from a
  rendered document rather than an empty frame and the manual render check
  exercises real layout. [US1] [US2] [US3] [US4]
- **FR-014a**: "Plainly fictional" MUST be checkable rather than a matter of
  taste, and the sample content MUST stay representative while it is. Three
  rules carry that. All four templates' sample content describes **one invented
  feature**, and every slot draws its content from that same invented feature,
  so a gallery browser comparing two templates is reading one worked example
  rather than two unrelated ones. That feature is named by an identifier outside
  every namespace this repository's roadmap uses, so a reviewer confirms the
  fiction by reading the identifier rather than by judging tone, and a reviewer
  can find any sample content a fill failed to replace by searching for it. And
  each template states in its rendered `feature-header` region that what follows
  is sample content awaiting a fill — in the rendered document, because the slot
  inventory is an HTML comment a browsing reader never sees. That statement MUST
  sit inside a fill region: placed outside every region it would survive the
  fill and then describe a filled artifact as sample content. [US1] [US2] [US3]
  [US4]
- **FR-015**: Slot names MUST be filename-safe kebab-case, following the same
  character rules the catalog applies to identifiers, and MUST be unique within
  their template. Each template MUST carry exactly the slots below, in document
  order, each named with the source artifact its content is drawn from; a
  template MUST NOT carry a region of feature-specific content that is not a
  slot, because unfilled sample content in a filled artifact reads as the
  project's own data.
  - implementation-plan: `feature-header` (spec.md), `plan-stats` (plan.md),
    `phases` (plan.md), `data-flow` (plan.md), `mockups` (design-concept.md),
    `risk-register` (plan.md, research.md), `task-inventory` (tasks.md)
  - spec-explainer: `feature-header` (spec.md), `tldr` (spec.md), `goals`
    (spec.md), `non-goals` (design-concept.md, spec.md), `acceptance-criteria`
    (spec.md), `clarification-faq` (spec.md, design-concept.md)
  - code-approaches: `feature-header` (spec.md), `approaches` (research.md,
    plan.md), `recommendation` (research.md)
  - module-map: `feature-header` (spec.md), `module-summary` (plan.md),
    `module-graph` (plan.md), `modules` (plan.md), `key-files` (plan.md)

  Granularity is one slot per section, never one per repeated item: a slot
  holding a repeated list carries the whole list, so the number of items is a
  property of the feature rather than of the template. Regions are flat — no
  slot's marker pair may enclose another's. Each repeated item inside a list
  slot MUST carry a stable anchor attribute naming that item, which is what an
  objection or a selection attaches to. An anchor value is
  `<slot>-<item-slug>` under the same character rules as slot names, which makes
  it unique across the template and usable as a document fragment. A template's
  own behavior MUST resolve an anchor by looking the value up as an element
  identifier, never by concatenating it into a selector string. The two are not
  equivalent for a value a later agent wrote: an identifier lookup takes the
  value literally, while a selector needs the value to be a valid CSS identifier
  and would otherwise have to be escaped before use, so a selector built by
  concatenation can throw, match nothing, or match an element other than the one
  intended. The rule holds regardless of whether the anchor obeys the format
  above, which is what makes it a property of the template rather than a
  dependency on the generator. [US1] [US2] [US3] [US4]

#### What the reader records

- **FR-016**: The implementation-plan and module-map templates MUST let the
  reader attach an objection to one individual phase or one individual module
  inline, through a labelled field reachable and operable by keyboard alone, so
  the tie between an objection and the item it attaches to is structural rather
  than something the reader must restate in prose. [US1] [US4]
- **FR-016a**: Every reader-input control a template carries MUST be built by
  that template's own inline behavior at load time, mounted onto the stable
  anchor its item already carries, and inserted immediately after that anchor in
  document order so tab order and reading order follow the visible order without
  a positive tab index. A template MUST NOT rely on a later authoring agent to
  emit control markup: the capture affordances ship working in this feature, and
  a fill region carries only inert content plus its per-item anchors. This keeps
  every value a later agent writes in a text or plain-data-attribute position and
  keeps control markup out of the positions the contract forbids generated
  content from reaching. Two conditions bound that claim, and both are
  requirements rather than notes.

  First, the routine MUST build its controls as document elements — creating each
  element, setting its attributes by name, and setting its text through the
  text-valued property — and MUST NOT assemble control markup as a string and
  assign it as markup. This is the industry's standard safe-sink guidance, and
  here it is also what keeps the obligation checkable: the repository's construct
  scan parses markup out of single-line script string literals only, so a
  prohibited construct inside a markup string spanning more than one line reaches
  none of the construct checks. Building elements leaves no markup string for a
  construct to hide in, so FR-004 holds by construction rather than by a scan
  with a known blind spot.

  Second, "plain data attribute" means an attribute carrying a value that is not
  URL-shaped. The gallery scan is default-deny on attributes: an attribute it
  does not recognize as URL-valued whose value is URL-shaped is reported as an
  unverified host rather than admitted. A slot that puts a URL into a data
  attribute therefore fails validation even though the position is otherwise
  correct. Where a slot's content genuinely carries a URL, it belongs in a text
  node, or in an anchor's `href` under the navigation rule the contract already
  bounds by scheme. [US1] [US3] [US4]
- **FR-017**: The code-approaches template MUST let the reader select exactly one
  approach from those compared, using a control that natively exposes which one
  is selected, together with one labelled field for their reason. The
  single-choice control MUST be grouped by a native grouping element carrying a
  visible group label as its accessible name, and the reason field MUST be
  optional; an export names the absence of a reason rather than omitting it or
  blocking on it. Requiring a reason would either strand the reader's real
  conclusion or pressure filler text, and there is no submission to enforce it
  against. [US3]
- **FR-017a**: Controls serving the same function across the items of one list
  MUST be identified consistently — same structure, same labelling, same exposed
  state — which follows from building them all from one routine rather than
  emitting each separately. Consistent is not identical. Each such control's
  accessible name MUST also carry its own item's visible label, so a reader
  who lists the document's fields hears which item each one attaches to instead
  of the same name five times over. The shared part of the name comes from the
  routine and the distinguishing part from the item, which is how one rule
  serves consistency and distinguishability at once. [US1] [US3] [US4]
- **FR-018**: The interaction detail of capture is fixed as follows. [US1] [US3]
  [US4]
  - An objection field MUST start collapsed behind a native disclosure whose
    control is reachable and operable by keyboard, and the disclosure's own
    control MUST state in text whether that item currently carries a note, so a
    recorded objection is visible without opening it. Always-revealed fields are
    rejected: a list of five or six items would turn a document meant to be read
    into a form, against the reviewing operator's actual job.
  - That note text is not the disclosure's open/closed state, and the two are
    reported differently. Whether a native disclosure announces its state, and
    whether it announces a *change* of state, varies by screen reader and
    browser pairing; some report the state on focus and stay silent when it
    moves, and at least one common mobile pairing reports no state at all.
    Removing the disclosure's default marker glyph degrades that report further
    on several pairings that otherwise manage it. So the port MUST NOT remove
    that marker without putting an equally visible indicator of open and closed
    in its place, and the note text MUST sit in the control's own accessible
    name, which is what keeps a recorded objection findable on a pairing that
    reports no state at all.
  - An export MUST list only the items the reader recorded against, and MUST NOT
    emit a line, a placeholder, or a count for an item left empty, because
    reporting an item as carrying no objection asserts an approval the reader
    did not record.
  - When the reader recorded nothing, an export MUST state that nothing was
    recorded and MUST state that the record is not an approval, in wording fixed
    per export kind rather than left to the implementation, while still naming
    the artifact and the feature it came from. The realistic misreading of an
    empty export is approval, so denying it is part of the requirement.
  - An export MUST name each item it carries by four coordinates read from live
    state — the feature, the artifact, the slot, and the item's visible label —
    together with the item's stable anchor in a form a reader can use to find
    that item again after leaving the document.
  - An item carries a note when its field holds at least one non-whitespace
    character, and only then. Whitespace alone is not an objection: it does not
    turn on the disclosure's state text and it is not a line in an export.
    Without that rule "left empty" is undefined against a field holding a
    stray space, and an export emitting a blank objection would state a
    conclusion the reader did not reach. The state text MUST follow the field's
    current value rather than its value at the last collapse, so a reader who
    types and leaves the disclosure open is never told the item is empty.
- **FR-018a**: A recorded objection, selection, or reason exists only for the
  life of the browser tab. Nothing is stored, so a reload or a closed tab
  discards all of it. Every template that records anything MUST say so in text
  beside its export controls, so a reader learns it before spending a review on
  it rather than after losing one. Persisting the input is out of scope — the
  export is how work leaves the document — which is exactly why a reader who
  does not know the input is temporary can lose a whole review silently. [US1]
  [US3] [US4]

#### Export affordances

- **FR-019**: The implementation-plan, code-approaches, and module-map templates
  MUST each carry exactly one control per export kind their catalog entry
  declares, labelled by destination — "Copy as prompt" and "Copy as Markdown" —
  rather than by mechanism. Those two labels name a format, and the two controls
  sit side by side, so each template MUST also carry one visible line beside the
  pair saying what each one is for: the prompt export for pasting into a coding
  agent, the Markdown export for a pull-request comment. Without it the only
  statement of the difference is in a contract the reader never opens, and a
  reader who cannot tell the two apart picks by guess. The labels themselves do
  not change. [US1] [US3] [US4]
- **FR-020**: The spec-explainer template MUST carry no export control and no
  reader-input field of any kind, because its catalog entry declares it
  read-only. It MUST also carry no inline behavior of its own: the canonical head
  block is its only script. Upstream's one script exists solely to drive a tabbed
  configuration walkthrough that maps to no slot and is dropped, so nothing needs
  it. This makes the requirement structural — the template is incapable of
  capturing anything — rather than a judgement that its controls are benign.
  [US2]
- **FR-021**: Every export MUST be derived from the artifact's live state at the
  moment it is invoked, never from a value written into the file when it was
  authored. [US1] [US3] [US4]
- **FR-022**: Every export MUST carry the reader's conclusion rather than the
  document's content, and MUST name the artifact, the feature, and the phase,
  module, or approach the conclusion attaches to, so it can be acted on by
  someone who has left the document behind. The header line that names the
  artifact and the feature is fixed in `contracts/export-payload-contract.md`
  alongside the empty-state bodies, and for the same reason: three templates
  emit it from three separate copies of the code, so a form left to each of them
  is a form that drifts. [US1] [US3] [US4]
- **FR-023**: An export MUST NOT state a conclusion the reader did not reach, and
  MUST NOT carry any value the reader could not see in the rendered document. The
  item's stable anchor is the single carve-out, and it is bounded rather than
  waived: FR-018 requires it so a reader can find the item again after leaving the
  document, and FR-015 derives it from that item's own visible label, so it
  restates something rendered rather than disclosing something withheld. An export
  MUST therefore carry the anchor and nothing else the reader could not see — no
  attribute the artifact reads for its own bookkeeping, no value the shipped file
  carried but did not display, and no identifier a later agent wrote that does not
  trace to a visible label. Anything asserting otherwise is a defect in this
  requirement's carve-out rather than a licence to widen it.

  The carve-out holds only while the anchor stays a deterministic function of the
  label **as currently rendered** — a transform a reader could redo by hand. Two
  ways it can quietly stop holding, both of which a later agent MUST avoid:
  - **A frozen slug.** An anchor assigned once and kept stable while its label is
    later edited no longer restates anything visible, because the reader now sees
    different words. An anchor is re-derived whenever its label changes.
  - **A disambiguating suffix.** Two items in one slot may carry identical visible
    labels, and uniqueness then forces a suffix. That suffix MUST derive from the
    item's visible position in its list, which the reader can also see, and MUST
    NOT be an opaque or generation-time counter. [US1] [US3] [US4]
- **FR-024**: Every export control MUST be reachable and operable by keyboard
  alone and MUST report its success in text, not by color or motion alone. A
  success message MUST name what the produced text actually carries, so it
  cannot imply a conclusion the text does not contain. A second invocation that
  produces the same message MUST still be reported. A status region whose text
  did not change is not announced again, so the artifact MUST clear the region
  and write the message afresh rather than assign the same string over itself,
  and the region MUST be in the document from load, because one created at the
  moment it is first written frequently goes unannounced entirely. [US1] [US3]
  [US4]
- **FR-025**: When clipboard access fails or is refused, the artifact MUST reveal
  the same text in a field the reader can select, and MUST NOT report success.
  "The same text" is byte equality with what the copy attempt carried, and it
  MUST be placed into the field through the field's own text value rather than as
  markup, so the revealed text cannot be re-interpreted on the way in, cannot
  close the field early, and cannot differ from what a successful copy would have
  produced. A field populated as markup fails this twice over: it is a markup
  position for a value the reader is being shown as text, and it can display
  something other than what was copied, which is the one thing this path exists to
  rule out. The revealed field MUST be selectable and focusable rather than disabled, and
  focus MUST move to it. The failure path MUST use one message regardless of
  whether the clipboard interface was absent or the write was refused, and MUST
  NOT assert a cause, because the artifact cannot distinguish a refused
  permission from an unfocused document or a browser policy. No deprecated
  second copy attempt may be made, because its result is ambiguous and reporting
  an uncertain success is exactly what this requirement forbids. The revealed
  field MUST carry its own programmatic label naming what it holds, and the
  failure message MUST also be tied to that field as its description, so the
  reader learns the copy failed from the focus landing there. The status region
  alone does not discharge this: moving focus and updating a live region in the
  same moment is a known conflict, and the live region is the one that loses.
  [US1] [US3] [US4]

#### What each template presents

- **FR-026**: The implementation-plan template MUST present the phases of the
  planned change, a diagram of how data moves through it, slots for screen
  mockups, a register of risks, and an inventory of the tasks. [US1]
- **FR-027**: The spec-explainer template MUST present a short summary, the
  goals, the explicit non-goals, the acceptance criteria in a form the reader can
  fold away and reopen, and an FAQ built from the answers recorded during
  clarification. The fold-away form is the native disclosure element carried over
  from upstream's step list, which needs no script and exposes its own state.
  Unlike the objection disclosures on the other templates, it carries no state
  text, because there is nothing for a reader to record here. [US2]
- **FR-028**: The code-approaches template MUST present two or more approaches
  beside one another with the trade-off that decides between them stated for
  each. [US3]
- **FR-029**: The module-map template MUST present the modules a change touches
  as labelled boxes and the calls between them as arrows, with the path the
  change runs through distinguished from the rest. That distinction MUST be
  carried by boundary weight and by a visible text tag, never by color. Upstream
  distinguishes it by fill tint and boundary hue alone, and its tint is an
  unaudited blend over an unknown backdrop, so neither survives the port. [US4]
- **FR-030**: Each diagram surface MUST keep the drawing mechanism its upstream
  source already uses, restyled with brand tokens rather than rebuilt. Both
  surfaces were read, and both use the same mechanism — hand-authored inline
  vector markup with a view box, rectangle, path, line, and text primitives, and
  arrowheads defined once and referenced by same-document fragment. Neither is
  re-authored. They differ only in how color is applied, and the port normalizes
  that difference: [US1] [US4]
  - The module map already styles through classes, so restyling is a token swap
    in the rules it already has, plus one rule for the arrowhead.
  - The implementation plan hardcodes presentation attributes on every shape.
    Those attributes need not be rewritten, because a presentation attribute
    carries no specificity and any rule overrides it. The port MUST add class
    hooks and style through them rather than applying one blanket selector,
    because a blanket rule would flatten the two-tier text hierarchy and the
    inverted node the upstream drawing deliberately distinguishes.
  - An arrowhead renders in its own context and does not inherit paint from the
    element referencing it, so each MUST be restyled by its own selector.
  - No upstream color value may survive. Every one is an unaudited pairing, and
    no upstream source carries any theme-aware rule at all, so a retained value
    leaves the drawing unreadable in the dark theme.
- **FR-030a**: Each diagram MUST carry an accessible name, and the information it
  conveys MUST also be available as text outside the drawing. Neither upstream
  source satisfies this: one drawing carries no name at all, and the other
  carries a name but is marked so that assistive technology reads it as a single
  image, which hides every label inside it. Outside the drawing means outside the
  drawing element and inside the same fill region. The text equivalent describes
  the feature, which makes it slot content under FR-015, and placing it outside
  the marker pair would leave a filled artifact carrying a fictional description
  of a real drawing. [US1] [US4]

#### Accessibility

- **FR-031**: Every foreground and background pairing a template uses MUST be one
  the brand kit's published audit already clears at its WCAG AA floor. A template
  MUST NOT introduce an unaudited pairing, and MUST NOT use the deliberately
  faint boundary token for any boundary that carries meaning. A token's audited
  role binds its use as tightly as its ratio does. The brand red primitive and
  the accent are cleared for large text and for non-text marks only, so red body
  copy MUST take the functional danger token instead; large text means at least
  24px, or at least 18.66px when bold. And the audit measures every foreground
  against four surfaces, so a fill that is not one of those four has no audited
  row at all and no text may be placed on it — which is what the inverted node's
  remedy in FR-032 has to respect. [US1] [US2] [US3]
  [US4]
- **FR-032**: Wherever a template uses color to mark a status, an action, or a
  distinction, the same meaning MUST also be available without color — as text, a
  shape, a glyph, or a position — so it survives for a reader who cannot perceive
  the hue and in a monochrome rendering. Reading the upstream sources found three
  places this applies, and each carries its own remedy: [US1] [US2] [US3] [US4]
  - The module map's distinguished path, addressed by FR-029.
  - The code-approaches trade-off markers, where upstream draws two identical
    shapes separated only by hue. The carrier already exists in the markup — a
    persistent column heading and a fixed column position — so the port declares
    those as the carrier and either drops the markers as redundant or gives them
    distinct glyphs, so a single row lifted out of the table still reads.
  - The implementation plan's inverted persistence node, distinguished from its
    siblings by fill inversion alone. The port adds a text tag or a distinct
    shape, and drops the unaudited accent used on its sub-label.

  The implementation plan's dashed edge is already compliant and MUST be ported
  intact: the dash pattern is a non-color carrier and the caption states the
  convention in words, so the caption is load-bearing rather than decoration.
- **FR-033**: Every interactive element MUST carry the kit's focus-visible
  treatment. No template may suppress a focus indicator without an equivalent
  replacement, assign a positive tab order, or trap focus. [US1] [US2] [US3]
  [US4]
- **FR-034**: Any motion a template adds beyond what the kit declares MUST be
  suppressed for a reader who asks for reduced motion. Two upstream sources carry
  an unguarded transform transition — the spec explainer's and the module map's —
  and no upstream source declares a reduced-motion rule anywhere. The port MUST
  drop both transitions or place them behind the guard. [US1] [US2] [US3] [US4]
- **FR-035**: A template MUST NOT author, replace, or wrap the theme control, and
  MUST NOT read the stored theme value itself; where it needs the active theme it
  reads the attribute the head block sets on the root element. Where a template
  wants the brand mark it provides the opt-in empty element and nothing else.
  All four templates want it: the mark is what makes a branded artifact
  recognizable at a glance, and leaving an opt-in undecided on a feature whose
  purpose is a branded document is how it ends up on none of them. Each provides
  it exactly once, in the document's own header chrome and **outside** every
  fill region — the mark is template chrome rather than feature content, and a
  mark placed inside a region is deleted the first time that region is filled.
  [US1] [US2] [US3] [US4]
- **FR-035a**: Each template MUST declare its own document language and MUST
  carry a page title naming the artifact and the feature it belongs to. Neither
  canonical block supplies either one — the head block carries the policy
  declaration, the typeface request, and the theme script and nothing else — so
  both are the template's own obligation, and both are what a reader's assistive
  technology takes its pronunciation and its window identity from. [US1] [US2]
  [US3] [US4]
- **FR-035b**: Each template MUST carry exactly one top-level heading and MUST
  NOT skip a heading rank, so the outline a reader navigates by matches the
  document they see. Because a later authoring agent replaces a whole region
  rather than merging into it, each slot's shipped sample content MUST model the
  heading ranks a filled region is expected to keep, which makes the shipped
  content the record of that obligation. No inventory field records it, because
  FR-012 fixes the inventory line at three labels and adding a fourth would
  break every template's inventory to say something the body already says.
  [US1] [US2] [US3] [US4]

#### Verification and delivery

- **FR-036**: Automated validation MUST assert, for each shipped template, that
  every region the roadmap names for it is present as a delimited slot — checked
  against a literal expectation, not one derived from the file under test — and
  that the file's documented inventory and its delimited regions agree in both
  directions. The literal expectation is a floor rather than an equality: a
  template may carry more slots than the roadmap names, and the both-ways
  agreement above is what binds the remainder. Every entry in the floor traces to
  the roadmap and to nothing else, so a reader can tell why each one is there.
  The floor is:
  - implementation-plan: `phases`, `data-flow`, `mockups`, `risk-register`,
    `task-inventory`
  - spec-explainer: `tldr`, `goals`, `non-goals`, `acceptance-criteria`,
    `clarification-faq`
  - code-approaches: `approaches`
  - module-map: `module-graph`

  The module map's distinguished path is a required property of `module-graph`'s
  content, not a slot of its own; a marker pair inside the drawing would split
  one figure across two fill operations that share a coordinate system. [US1]
  [US2] [US3] [US4]
- **FR-036a**: Automated validation MUST separately assert that every repeated
  item inside a list slot carries the stable anchor an objection or a selection
  attaches to. This is its own assertion rather than an extra entry in the FR-036
  floor, for two reasons. A slot's mere presence would only prove a region of
  that name exists, never that its items are individually addressable, so the
  floor cannot verify this requirement even in principle. And the floor's entries
  all trace to one document; an entry sourced from a different requirement would
  make the literal unauditable. [US1] [US3] [US4]
- **FR-037**: Validation code this feature adds MUST run on the Python 3.11+
  standard library alone, live under the repository's unit test tree, and be
  registered in the suite manifest. Its filename MUST name the durable capability
  it verifies and MUST NOT be coupled to a spec identifier. [US1] [US2] [US3]
  [US4]
- **FR-038**: The manual browser checks — opening from a local filesystem, a
  clean console, the theme control, the export controls where the entry declares
  them, and keyboard reachability — MUST be recorded as numbered steps with
  observable results in the feature's acceptance runbook, one set per template.
  No automated browser is introduced. [US1] [US2] [US3] [US4]
- **FR-039**: Because these files ship inside the plugin payload, each slice MUST
  account for the generated artifact contract, so every shipped copy stays
  byte-identical to its source on both platforms. [US1] [US2] [US3] [US4]
- **FR-040**: Delivery MUST be two sequential pull requests. The first carries
  US1 and US2, their two status flips, and their validation. The second carries
  US3 and US4 and theirs, and branches from a state that already contains the
  first. [US1] [US2] [US3] [US4]

### Reviewability Notes

- No typed reviewability exception is claimed. Each slice sits **above the warn
  threshold and well below the block threshold**, and a warning proceeds on
  recorded scope and a recorded split, both of which exist. No
  `Reviewability-Exception` pragma is recorded here or in either pull request.
- This corrects an earlier statement. Scoping projected each slice at roughly
  half the warn threshold; the plan's line-level derivation of the actual work
  put it at 530, and the measured gate agrees. The number moved because scoping
  counted the ported template body and not the capture, export, and clipboard
  behavior each template must carry, nor the sample content every slot ships
  with. The split decision is unaffected: it was taken to make each slice a
  reviewable end-to-end unit, and it still does that.
- The greenfield allowance does **not** apply. Scoping assumed it would, on the
  grounds that the work is net-new. The gate reports `greenfield: false`, so the
  thresholds in force are the base ones, 400 to warn and 800 to block.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process — the shipped gallery templates
- **Secondary surfaces, if any**: seed/config (the routing catalog's status
  values); harness/adapter (the fill-region validation)
- **Projected reviewable LOC**: ~530 per slice, measured from the plan's declared
  file operations rather than estimated from scope, and excluding declared
  generated payload artifacts
- **Projected production files**: 4 net-new template files across the feature (2
  per slice), plus the routing catalog modified once per slice — 3 production
  files per slice
- **Projected total files**: ~7 across the feature; 6 per slice, excluding
  declared generated payload artifacts
- **Budget result**: **warn, passing, zero blockers.** Measured at 530 reviewable
  LOC per slice against a 400 warn and an 800 block; 3 production files against a
  6-file warn; 6 total files against a 15-file warn; one primary surface. Only
  the LOC dimension warns. A warning proceeds when the workflow records the scope
  budget and the split decision, and it records both.
- **Split decision**: Split into two vertical slices delivered as two sequential
  pull requests, per the design concept's Q10 and its follow-up. Slice 1 is the
  two templates the draft-PR stage routes unconditionally (US1, US2), each
  end-to-end and independently reviewable. Slice 2 is the two conditionally
  routed templates (US3, US4) and branches after slice 1 merges. Stacked branches
  were rejected for their known synchronization friction in this repository, and
  a single pull request was rejected because the advisory size estimator returned
  a warning at an estimated 560 lines. ART-002 remains one specification; the
  split is a delivery decision, not a decomposition into two specifications.

### PR Review Packet Requirements *(mandatory)*

- Each pull request description MUST include: what changed, why, non-goals,
  review order, scope budget, traceability, verification evidence, known gaps,
  and rollback notes.
- Traceability MUST map each user story and each success criterion carried by
  that slice to the changed files and the verification evidence for it.
- Deferred work MUST name the follow-up specification. Work deferred from slice 1
  names slice 2; generation of the slot content names ART-007.

### Key Entities

- **Gallery template artifact**: One self-contained document a reader opens
  directly from a filesystem. Four are delivered here. Each is claimed by exactly
  one routing catalog entry, and its filename stem is that entry's identifier.
- **Fill region (slot)**: A named, delimited region of a template that an
  authoring agent later replaces wholesale. Identified by a matched start/end
  comment pair carrying the slot's name.
- **Slot inventory**: A template's own record of its slots — each slot's name,
  what fills it, and which source artifact the content comes from. It lives
  inside the template and is the surface the authoring agent reads. The source
  artifact is drawn from a closed set: `spec.md`, `plan.md`, `tasks.md`,
  `research.md`, `design-concept.md`. A slot drawing on two names both,
  comma-separated.
- **Routing catalog entry**: The record that names a template, routes it by stage
  and trigger, declares which export kinds it must carry, and states whether it
  has shipped. This feature changes exactly one value in four of these entries.
- **Objection**: A reader's note attached to one phase or one module, carrying
  the anchor of the item it attaches to so an export can name it.
- **Approach selection**: The reader's single choice among the compared
  approaches, together with their stated reason for it.
- **Export payload**: The text an export control produces from the artifact's
  live state at the moment it is invoked, phrased either as an instruction to a
  coding agent or as a record for a pull request comment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four templates open from a local filesystem with no server and
  no network and present a complete, readable document, with zero browser errors
  and zero failed loads reported in every case.
- **SC-002**: A reader who has recorded an objection or chosen an approach can
  carry it out of the document in a single action and under 30 seconds, without
  retyping any of it, in every destination that template's entry declares.
- **SC-003**: 100% of the regions the roadmap names for a template are present as
  delimited slots, and each template's own inventory and its delimited regions
  agree in both directions with zero discrepancies.
- **SC-004**: Zero templates render as an empty frame — every slot shows worked
  example content, so a gallery browser can decide whether a template fits by
  looking at the rendered document alone. 100% of that content names the one
  invented feature the sample set uses, so the fictional half is confirmed by
  reading an identifier rather than by judging tone.
- **SC-005**: Every export reflects only what the reader recorded: with nothing
  recorded, zero exports state a conclusion, and across all exports zero values
  appear that the reader could not see in the document.
- **SC-006**: An operator completes the recorded acceptance pass for one template
  in under 10 minutes, with every step naming an observable result they can
  confirm or reject without help.
- **SC-007**: Every shipped template passes the repository's existing gallery
  validation — contract conformance, attribution agreement, prohibited
  constructs, and external references — on the first full-suite run after each
  slice, with zero failures.
- **SC-008**: Every interactive control in every template is reachable and
  operable with the keyboard alone, shows a visible focus indicator, and reports
  any success in text, verified across 100% of controls.
- **SC-009**: Zero shared foundation files change across both slices, and the
  routing catalog differs from its prior state only in the status values of this
  feature's four entries.
- **SC-010**: Every meaning a template carries with color is also carried without
  it — verified by confirming 100% of color-marked distinctions remain
  identifiable in a monochrome rendering.

## Assumptions

- The four upstream source templates stay retrievable read-only from the named
  upstream repository's default branch at implementation time; all four were
  confirmed present during scoping. Only branded derivatives are committed, and
  no upstream file is vendored into this repository.
- The brand kit, the canonical head block, the contract document, and the gallery
  validation shipped by ART-001 are stable through this feature. None of them is
  amended here; if one proves insufficient, that is a separate change.
- The authoring agent delivered by ART-007 reads each template's own inventory
  comment to learn what to fill. No central registry is provided, because none is
  needed and adding one would create a shared file that can drift.
- Slot names follow the same character rules the catalog applies to identifiers,
  which keeps them safe to use in a filename, an anchor, or a comment marker.
- The fill-region validation reuses the gallery scanner's comment-collection
  idiom, so the inventory and the markers are both read as parser-recognized HTML
  comments; comment-shaped text inside a script element is not one.
- No script string literal in any template is URL-shaped. The local-file scheme
  is the case that bites first — the gallery scanner's URL-shaped pattern treats
  a literal beginning with that scheme and a colon as an external reference and
  fails it, so feedback wording says "opened from a filesystem" rather than
  naming the scheme — but it is not the whole rule, and stating only that case
  invites the port to pass it and fail the next one. The pattern also matches any
  scheme followed by `://` **anywhere** in a literal, a literal opening with two
  slashes, and a literal opening with any of the other opaque schemes that still
  act. So no literal in an export's wording, a feedback message, a comment inside
  a script, or a label may contain a web address; a literal that must reference
  something names it in prose, and an address a reader clicks lives in an anchor,
  where the contract's navigation exemption covers it. The one exemption is an
  XML namespace constant, which is compared as a string and never fetched. The
  clipboard call itself is not a scanned call site; the wording is.
- All four upstream sources were fetched read-only and scanned before this
  specification was finalized. They carry **zero** prohibited constructs: no base
  element, no scheme-relative reference, no event-handler attribute, no srcdoc,
  no submitting form, no ping. Two carry no script at all; the other two carry
  one each, neither of which builds markup from a string. So the port drops no
  construct for prohibition reasons. Two details are worth recording because each
  looks like a defect and is not: the implementation plan's drawing carries an
  absolute namespace declaration, which is exempt and MUST be retained; and the
  code-approaches source contains three escaped handler-shaped strings inside
  displayed sample code, which are text rather than attributes and MUST port
  verbatim. A reviewer running a naive text search will find the latter three.
- **Three** regions have no upstream counterpart and are authored fresh: the
  implementation plan's task inventory (upstream's fourth section is key code)
  and the spec explainer's goals and its non-goals, separately (upstream's
  counterpart section is a configuration walkthrough with no Racecraft
  equivalent). A fourth, the spec explainer's acceptance criteria, has no content
  counterpart but reuses upstream's disclosure shape.
- Ten upstream regions are dropped, each because it is feature-specific content
  that no slot names, which FR-015 forbids: three prompt boxes reproducing a
  human's chat prompt, the implementation plan's key-code and open-questions
  sections, the spec explainer's navigation, step content, configuration tabs and
  gotchas, and the module map's gotchas. The navigation earns its drop twice
  over, because five of its nine links target the same anchor, which collides
  with the per-item anchor rule.
- The manual browser checks are executed by an operator at acceptance time.
  Repository tests stay on the Python standard library, so no automated browser
  is introduced and no browser-driving dependency is added.
- Shipped sample content is fictional and reads as such. It is not treated as
  project data by any consumer, because the authoring agent replaces whole
  delimited regions rather than merging into them.
- Slice 2 branches after slice 1 merges, so it starts from a routing catalog that
  already carries slice 1's two flips.
- The draft-PR stage that routes these artifacts already exists, having shipped
  with ART-006. This feature delivers documents for that stage to route; it wires
  nothing.

## Dependencies

- **Requires ART-001**: the brand token block, the canonical head block, the
  routing catalog and its schema, the single-file artifact contract, and the
  gallery validation that already scans every artifact in the gallery.
- **Requires ART-006**: the plan stage whose checkpoint these artifacts are read
  at. Satisfied; no change to it is made here.
- **Enables ART-007**: the draft-PR emission that fills these slots. It is blocked
  until at least slice 1 ships, because it has nothing to populate before then.
- **Handed to ART-007 — the anchor integrity of a filled artifact.** FR-036a's
  anchor assertion runs only against this feature's own shipped templates.
  Nothing in this repository ever inspects an artifact the authoring agent writes
  at run time, and the artifact contract states plainly that whatever safety a
  generated artifact has is what its generator put there. ART-007 therefore
  inherits the obligation: before committing a filled artifact it MUST confirm
  every repeated item in a list slot carries a present, unique anchor — the same
  property this feature proves for its own sample content — and treat a failure
  as a generation failure under its own fail-open policy. Catching this at the
  writer, before the file is committed, is strictly better than a reactive
  runtime notice a reader might not see.

  Why this obligation is sharper than it looks, and must not be softened into a
  best-effort note: a duplicate anchor does not raise an error. Identifier lookup
  is specified to return the first match in document order, silently and
  deterministically. So a filled artifact carrying two identical anchors renders
  perfectly, mounts a control on the wrong item, and exports a conclusion naming
  an item the reader never annotated. It is a plausible, confident, wrong result
  with no signal anywhere. Duplicate identifiers also break the association
  between a control and its label, which is an accessibility defect in its own
  right. Uniqueness is a conformance rule the generator violates, not a
  robustness nicety the reader's document can paper over.

  This feature adds **no** duplicate-or-missing-anchor detection at run time
  beyond FR-015's format-agnostic identifier lookup, and that is deliberate. A
  runtime guard would defend against a defect its own shipped artifacts cannot
  exhibit; it could not be exercised by any test this feature is allowed to write,
  because repository tests stay on the Python standard library and no automated
  browser is introduced, so it would ship as dead code; and it would be
  triplicated across three templates that have no shared runtime, against a
  reviewability budget already warning.

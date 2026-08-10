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
  contract's exact labels, and the upstream repository and upstream file it names
  MUST equal what that template's own catalog entry declares. [US1] [US2] [US3]
  [US4]
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
  exactly once in the file with its start before its end. [US1] [US2] [US3] [US4]
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
  it unique across the template and usable as a document fragment. [US1] [US2]
  [US3] [US4]

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
  content from reaching. [US1] [US3] [US4]
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
  emitting each separately. [US1] [US3] [US4]
- **FR-018**: The interaction detail of capture is fixed as follows. [US1] [US3]
  [US4]
  - An objection field MUST start collapsed behind a native disclosure whose
    control is reachable and operable by keyboard, and the disclosure's own
    control MUST state in text whether that item currently carries a note, so a
    recorded objection is visible without opening it. Always-revealed fields are
    rejected: a list of five or six items would turn a document meant to be read
    into a form, against the reviewing operator's actual job.
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

#### Export affordances

- **FR-019**: The implementation-plan, code-approaches, and module-map templates
  MUST each carry exactly one control per export kind their catalog entry
  declares, labelled by destination — "Copy as prompt" and "Copy as Markdown" —
  rather than by mechanism. [US1] [US3] [US4]
- **FR-020**: The spec-explainer template MUST carry no export control and no
  reader-input field of any kind, because its catalog entry declares it
  read-only. [US2]
- **FR-021**: Every export MUST be derived from the artifact's live state at the
  moment it is invoked, never from a value written into the file when it was
  authored. [US1] [US3] [US4]
- **FR-022**: Every export MUST carry the reader's conclusion rather than the
  document's content, and MUST name the artifact, the feature, and the phase,
  module, or approach the conclusion attaches to, so it can be acted on by
  someone who has left the document behind. [US1] [US3] [US4]
- **FR-023**: An export MUST NOT state a conclusion the reader did not reach, and
  MUST NOT carry any value the reader could not see in the rendered document.
  [US1] [US3] [US4]
- **FR-024**: Every export control MUST be reachable and operable by keyboard
  alone and MUST report its success in text, not by color or motion alone. A
  success message MUST name what the produced text actually carries, so it
  cannot imply a conclusion the text does not contain. [US1] [US3] [US4]
- **FR-025**: When clipboard access fails or is refused, the artifact MUST reveal
  the same text in a field the reader can select, and MUST NOT report success.
  The revealed field MUST be selectable and focusable rather than disabled, and
  focus MUST move to it. The failure path MUST use one message regardless of
  whether the clipboard interface was absent or the write was refused, and MUST
  NOT assert a cause, because the artifact cannot distinguish a refused
  permission from an unfocused document or a browser policy. No deprecated
  second copy attempt may be made, because its result is ambiguous and reporting
  an uncertain success is exactly what this requirement forbids. [US1] [US3]
  [US4]

#### What each template presents

- **FR-026**: The implementation-plan template MUST present the phases of the
  planned change, a diagram of how data moves through it, slots for screen
  mockups, a register of risks, and an inventory of the tasks. [US1]
- **FR-027**: The spec-explainer template MUST present a short summary, the
  goals, the explicit non-goals, the acceptance criteria in a form the reader can
  fold away and reopen, and an FAQ built from the answers recorded during
  clarification. [US2]
- **FR-028**: The code-approaches template MUST present two or more approaches
  beside one another with the trade-off that decides between them stated for
  each. [US3]
- **FR-029**: The module-map template MUST present the modules a change touches
  as labelled boxes and the calls between them as arrows, with the path the
  change runs through distinguished from the rest. [US4]
- **FR-030**: Each diagram surface MUST keep the drawing mechanism its upstream
  source already uses, restyled with brand tokens rather than rebuilt. Whether
  that holds is
  [NEEDS CLARIFICATION: unconfirmed — the upstream sources had not been read when
  the mechanism decision was made, at moderate confidence. Whether each upstream
  drawing mechanism survives re-styling with brand tokens without carrying a
  construct the contract prohibits, and whether either surface must instead be
  re-authored, is settled only after the upstream sources are read.] [US1] [US4]

#### Accessibility

- **FR-031**: Every foreground and background pairing a template uses MUST be one
  the brand kit's published audit already clears at its WCAG AA floor. A template
  MUST NOT introduce an unaudited pairing, and MUST NOT use the deliberately
  faint boundary token for any boundary that carries meaning. [US1] [US2] [US3]
  [US4]
- **FR-032**: Wherever a template uses color to mark a status, an action, or a
  distinction, the same meaning MUST also be available without color — as text, a
  shape, a glyph, or a position — so it survives for a reader who cannot perceive
  the hue and in a monochrome rendering. [US1] [US2] [US3] [US4]
- **FR-033**: Every interactive element MUST carry the kit's focus-visible
  treatment. No template may suppress a focus indicator without an equivalent
  replacement, assign a positive tab order, or trap focus. [US1] [US2] [US3]
  [US4]
- **FR-034**: Any motion a template adds beyond what the kit declares MUST be
  suppressed for a reader who asks for reduced motion. [US1] [US2] [US3] [US4]
- **FR-035**: A template MUST NOT author, replace, or wrap the theme control, and
  MUST NOT read the stored theme value itself; where it needs the active theme it
  reads the attribute the head block sets on the root element. Where a template
  wants the brand mark it provides the opt-in empty element and nothing else.
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

- No typed reviewability exception is claimed. Both slices are projected within
  the warn thresholds, so no `Reviewability-Exception` pragma is recorded here or
  in either pull request.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process — the shipped gallery templates
- **Secondary surfaces, if any**: seed/config (the routing catalog's status
  values); harness/adapter (the fill-region validation)
- **Projected reviewable LOC**: ~380 across the feature; ~190 per slice,
  excluding declared generated payload artifacts and validation code
- **Projected production files**: 4 net-new template files across the feature (2
  per slice), plus the routing catalog modified once per slice
- **Projected total files**: ~7 across the feature; ~5 per slice, excluding
  declared generated payload artifacts
- **Budget result**: within budget — each slice is projected at roughly half the
  400-LOC warn threshold, 3 production files against a 6-file warn, and ~5 total
  files against a 15-file warn
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
  looking at the rendered document alone.
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
- No script string literal in any template begins with the local-file scheme
  followed by a colon. The gallery scanner's URL-shaped pattern treats such a
  literal as an external reference and fails it, so feedback wording says
  "opened from a filesystem" rather than naming the scheme. The clipboard call
  itself is not a scanned call site.
- Two roadmap-named regions have no upstream counterpart and are authored fresh
  against an existing upstream layout shape: the implementation plan's task
  inventory (upstream's fourth section is key code) and the spec explainer's
  goals and non-goals (upstream's counterpart section is a configuration
  walkthrough with no Racecraft equivalent).
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

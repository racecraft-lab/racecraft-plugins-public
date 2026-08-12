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

- **FR-011**: The artifact MUST ship six fill regions: `motivation`,
  `before-after`, `file-by-file`, `non-goals`, `verification`, and
  `implementation-notes`. The first four of those named by the roadmap
  (`motivation`, `before-after`, `file-by-file`, `implementation-notes`) are the
  set pinned as the floor; `non-goals` and `verification` ship because the
  catalog entry shipped in ART-001 already promises a reader "what it
  deliberately leaves out, and how it was verified".
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
  [NEEDS CLARIFICATION: the fixed decision declares the `implementation-notes`
  slot's source as `specs/<feature>/.process/implementation-notes.md`, which is
  neither a member of that closed set (`spec.md`, `plan.md`, `tasks.md`,
  `research.md`, `design-concept.md`) nor written as a bare filename. How does
  that line satisfy the check: extend the closed vocabulary with a bare
  `implementation-notes.md`, name a member that already exists, or something
  else? The rendering decision itself is fixed and is not reopened by this.]
- **FR-018**: Every region MUST ship representative fictional sample content held
  to the minimum that demonstrates its shape: non-empty everywhere, expansive
  nowhere. A prose region ships one short paragraph. A region holding a repeated
  list ships exactly the two items the validation requires.
- **FR-019**: The `implementation-notes` region MUST render only the eventful
  entries of the implementation record, in the record's own append order, each
  under the task identifier it was recorded against. Two entries sharing a task
  identifier both render, because that is a retry and correct history.
- **FR-020**: Any region holding a repeated list MUST place its grouping element
  outside the marker pair, so the container survives a fill, and MUST give every
  repeated item at the region's own top level a stable, unique anchor of the form
  `<slot>-<item-slug>` in kebab-case.
  [NEEDS CLARIFICATION: which of the six slots hold a repeated list rather than
  prose, and at what granularity each is addressed. `file-by-file` and
  `implementation-notes` both read as list-shaped, but the design concept defers
  per-slot granularity until the upstream source has been read, on the recorded
  ground that slot shapes must not be invented before it. This decides which rows
  the list-slot literal gains and therefore which regions owe two anchored sample
  items.]

#### Attaching and exporting a question

- **FR-021**: Each of the six sections MUST carry its own inline question
  control: a keyboard-reachable disclosure plus a labelled text field, matching
  the pattern the gallery's existing templates already ship, so a reviewer meets
  one interaction across the gallery.
- **FR-022**: The artifact MUST carry exactly one export control per declared
  export kind, and its catalog entry declares two: an instruction for a coding
  agent, and a record for a pull-request comment. Each control MUST be labelled
  with its destination rather than its mechanism.
- **FR-023**: An export MUST walk only the non-empty question fields, and MUST
  carry each question together with the anchor of the section it attaches to.
- **FR-024**: An export MUST carry enough context to be acted on away from the
  artifact: the artifact, the change it belongs to, and the location each
  question attaches to.
- **FR-025**: An export MUST NOT carry a conclusion the reviewer did not reach,
  and MUST NOT carry any value the reviewer could not have inspected on screen.
- **FR-026**: An export MUST be derived from the artifact's live state at the
  moment it is invoked, never from a value fixed when the file was written.
- **FR-027**: Every export control MUST be reachable and operable by keyboard
  alone, and MUST report its outcome in text rather than by color or animation
  alone.
- **FR-028**: When clipboard access fails or is refused, the artifact MUST reveal
  the exported text in a selectable field and say so, rather than reporting
  success or failing silently.
- **FR-029**: When no question has been written, an export MUST say in text that
  there is nothing to export rather than produce an empty or invented document.

#### Accessibility

- **FR-030**: Every foreground and background pairing the artifact uses MUST come
  from the kit's audited set. Colors introduced outside the embedded block are
  outside the audit and MUST NOT be relied on.
- **FR-031**: The artifact MUST NOT use the subtle border token for any boundary
  that conveys meaning; a meaningful boundary uses the strong border token.
- **FR-032**: No status, action, or distinction the artifact draws may be carried
  by color alone. Each MUST also be available as text, shape, glyph, or position,
  and MUST survive a monochrome print or screenshot.
- **FR-033**: Where the artifact names a heading typeface explicitly it MUST use
  the display token, and heading rank MUST ride on semantic heading level, size,
  and weight rather than on typeface identity.
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
  template if and only if the template holds a repeated list, per FR-020.
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

**This slice is projected to exceed the 800 block threshold, and the resolution
is unresolved.** No `Reviewability-Exception` pragma is claimed, because none of
the accepted classes (`refactor`, `infra`, `upgrade`) honestly describes net-new
template work. Splitting further is not available either: a self-contained HTML
artifact cannot be divided across two pull requests and still render from
`file://`, so one template per PR is already the thinnest vertical slice this
work admits. [NEEDS CLARIFICATION: how slice 1 clears the reviewability
boundary — accepted block with recorded justification, a new exception class
that fits net-new artifact work, or a mechanism not yet identified. Resolution
belongs to Plan and to the operator, not to this spec.]

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (a shipped template file)
- **Secondary surfaces, if any**: seed/config (one catalog value), harness/adapter (two literals in the fill-region validation)
- **Projected reviewable LOC**: **~1000–1200**, excluding the 458 lines of
  canonical embedded blocks a reviewer never reads because they are byte-verified
  copies (`brand-kit.css` `BRAND-KIT` block = 318, `theme-toggle.html`
  `GALLERY-HEAD` block = 140; both measured)
- **Projected production files**: 1 (net-new: the artifact itself)
- **Projected total files**: ~4
- **Budget result**: **block** (above the 800 block threshold), unresolved — see
  Reviewability Notes
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
- **Split decision**: This spec **is** the split, and it remains correct even
  though it does not clear the boundary. ART-003 originally declared one slice at
  285 reviewable LOC. ART-002's slice 1 shipped two templates of the same kind
  and measured 1494, a hard block that forced a re-slice mid-implement. ART-003
  was re-declared at scaffold as three stacked slices, one template per pull
  request. This spec covers slice 1 (`pr-writeup`) only; `annotated-diff` and
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
- Review order MUST put the authored markup ahead of the embedded canonical
  blocks, which are byte-verified copies rather than material to read.

### Key Entities

- **The artifact**: one HTML file carrying six reader-facing sections, an
  attribution header, a slot inventory, sample content, per-section question
  fields, and two export controls.
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
- **SC-010**: The finished change measures under 800 reviewable production LOC,
  the threshold above which it would be blocked.
- **SC-011**: An authoring agent reading only the artifact's own inventory can
  name all six regions and what fills each, with zero regions undocumented and
  zero documented slots lacking a region.

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
- The reviewability projection is an estimate derived from a two-template sample
  and is re-measured at Plan. Landing above the warn threshold is expected and
  accepted; landing at or above the block threshold would require a re-slice, not
  an exception.
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

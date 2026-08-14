# Feature Specification: Final-PR Template Set — Slice 3, the Flowchart Artifact

**Feature Branch**: `art-003-final-pr-template-set-slice-3`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Final-PR Template Set — slice 3, the flowchart artifact. Scope this slice to ONE template: `flowchart`. Ship it as a branded, self-contained HTML artifact that shows a reviewer the operational flow a change affects — the steps, the branches, and the points where it can fail — as a diagram and as a text equivalent that conveys the same information. The entry declares `exports: []`, so the reader produces nothing and the artifact carries no export."

**Spec ID**: ART-003 (slice 3 of 3)

**Design Concept**: `docs/ai/specs/.process/ART-003-design-concept.md`

## Overview

ART-001 seeded a routing catalog that already promises a reader a Flowchart: a
multi-step process drawn as a diagram — the steps, the branches, and the points
where it can fail — reached for when a change alters a runtime or delivery flow
that prose describes poorly. The entry exists and reads `planned`, so the promise
is currently unbacked. This slice backs it.

The artifact is a template, not a finished diagram. It ships fictional sample
content in every region and a machine-readable inventory of the regions an
authoring agent will later replace. Filling it with a real flow is ART-010's
work, not this slice's.

ART-003 is three vertical slices, one template per pull request, stacked in
roadmap order. This spec covers **slice 3 only**: `flowchart`. Slices 1
(`pr-writeup`) and 2 (`annotated-diff`) already shipped on this branch. They are
this spec's precedent for the skeleton, the two canonical blocks, the attribution
header, the inventory grammar, and the CSS house style — **and for nothing
else**.

### The one fact that governs this specification

**This entry declares `exports: []`.** The contract states that an empty exports
array is the deliberate way to say the artifact's reader produces nothing
durable, and that the defect the declaration exists to make visible is an
artifact whose reader plainly produces something while its entry claims
otherwise. `spec-explainer` is the shipped precedent: same empty declaration,
and it carries no export control, no clipboard code, and no reader-input field of
any kind.

So does this one. That single fact is what puts this slice in a different class
from the two before it, and it is why `spec-explainer` rather than slice 1 or
slice 2 is this spec's comparator throughout — for its obligations, and for its
size.

### What is deliberately not carried over from slices 1 and 2

Slices 1 and 2 each carry roughly forty requirements that exist to serve an
export. **None of them applies here, and their absence is deliberate rather than
forgotten.** They are named so a later reader can tell the difference:

| Not carried over | Why it has no subject here |
|---|---|
| The export payload shape — what a `prompt` and a `markdown` export must contain, and the two header lines each carries | The entry declares no export kind, so there is no payload |
| The clipboard-failure fallback, which reveals text in a selectable field when a local-file clipboard write is refused | There is no clipboard call to fail |
| The invocation-currency guard, which forces an export to derive from live state rather than a value baked in at load | There is nothing whose currency could go stale, because nothing is serialized |
| Slice 2's per-hunk objection capture and slice 1's per-section question capture | The reader reaches no conclusion this artifact must carry back; they are learning a flow |
| The empty-state bodies those captures need — what an export says when every field is blank | No field, no empty state |
| Every reader-input field: the labelled textarea, its disclosure, and its label association | FR-014 forbids all of them |

Carrying any of these in would be an affordance the catalog does not declare,
which is the exact defect the `exports` declaration exists to surface.

### Where the risk actually sits

The review surface is comfortable here for the first time in this feature — 340
lines below the block threshold, against slices 1 and 2 which each cleared it by
under 80. **The risk did not disappear; it moved.**

A diagram is the artifact kind where meaning most easily hides. A picture carries
sequence in position, role in shape, branch outcome in stroke, and state in
colour, and every one of those is invisible to a reader who receives the document
as text. Upstream `13-flowchart-diagram.html` demonstrates the whole failure
class: its drawing has no accessible name, its nodes are click targets that no
keyboard can reach, its success and failure nodes differ from an ordinary step by
fill colour alone, its selected node is marked by stroke colour alone, and it
carries no text equivalent at all.

Accessibility is therefore this slice's governing requirement, in the position
that size held on slices 1 and 2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the operational flow the change affects [US1] (Priority: P1)

A reviewer is asked to judge a pull request that alters a multi-step runtime or
delivery process. The diff shows them lines; it does not show them the flow those
lines sit inside — what runs first, what calls what, which branch the change
turns on, and where the process can short-circuit. They open `flowchart.html`
straight from the filesystem, with no server and no install, and read that flow:
as a diagram, and as a text equivalent that tells them the same things in words.

**Why this priority**: This is the artifact's whole reason to exist, and it is
the half that satisfies the catalog entry already shipped in ART-001. It is also
the half that is complete on its own — a reader who reads the flow has received
the full value of this artifact, because there is nothing for them to produce.
Every other requirement in this spec either serves this reading or depends on it.

**Independent Test**: Open the shipped file from the local-file scheme with the
network unavailable. The flow is readable in full, in both themes, from the
diagram; and independently, from the text equivalent alone with the diagram
disregarded. Repeat the second reading with the page rendered in monochrome and
with scripting unavailable. Nothing about the flow is lost in any of those
readings.

**Acceptance Scenarios**:

1. **Given** the shipped artifact opened from a filesystem with no server and no
   install, **When** a reviewer reads it, **Then** the operational flow is
   presented as a diagram showing every step, every branch, and every failure
   path, and the browser reports no console error and no console warning.
2. **Given** a reader who cannot see the diagram, **When** they read the text
   equivalent alone, **Then** they learn every node's label, role and detail;
   every edge's source, target and kind; the order of the flow; and every point
   at which it branches — losing nothing the picture conveys.
3. **Given** the page rendered in monochrome, **When** a reader distinguishes a
   process step from a decision from a terminal, and an ordinary edge from an
   affirmative branch from a failure branch, **Then** every one of those
   distinctions is still available, because none of them is carried by colour.
4. **Given** scripting unavailable, **When** the artifact is opened, **Then** the
   diagram and the text equivalent are both fully readable, every node's detail
   is still reachable, and no control is offered that cannot work.
5. **Given** the network unavailable, **When** the artifact is opened, **Then**
   all of its content stays readable and all of its controls stay operable, and
   the only observable difference is typeface substitution.
6. **Given** the shipped artifact, **When** its rendered title is compared to its
   catalog entry's title, **Then** the two are byte-identical.

---

### User Story 2 - See one step's detail without leaving or producing anything [US2] (Priority: P2)

A reviewer following the flow reaches a step they do not recognise and wants to
know what it actually does and how it fails. They activate that node and its
detail appears in the page beside the diagram. They read it, move to the next
node, and at no point leave the page, download anything, copy anything, or type
anything. When they close the tab, nothing has been produced and nothing is lost,
because there was never anything to carry away.

**Why this priority**: It is the feature the roadmap names as this template's
distinguishing characteristic, and Q7 of the design concept fixed exactly what it
may and may not do. It is second because US1 stands without it: a reader who
never activates a node has still read the flow, and the text equivalent already
carries every node's detail.

**Independent Test**: With the diagram rendered, reach every interactive node
using the keyboard alone, activate each one, and confirm the detail region
changes to that node's detail while the node reports itself as the disclosed one.
Then confirm, by search over the shipped bytes and by observation, that no
activation writes a file, writes the clipboard, triggers a download, or navigates
away.

**Acceptance Scenarios**:

1. **Given** the diagram rendered, **When** a reviewer activates a node, **Then**
   that node's detail — what the step does and how it can fail — is disclosed in
   the page, and nothing durable is produced.
2. **Given** a keyboard and no pointing device, **When** a reviewer moves through
   the document in reading order, **Then** every interactive node is reachable in
   sequence, carries a visible focus indicator, and is activated by the same keys
   as any other control of its kind.
3. **Given** a reader who cannot see the diagram, **When** the disclosed node
   changes, **Then** the change is perceivable to them, and the currently
   disclosed node reports that state programmatically rather than by colour.
4. **Given** the artifact just opened, **When** a reader looks at the detail
   region before activating anything, **Then** it already holds one node's
   detail, so the region is never empty on first paint.
5. **Given** any node activated any number of times, **When** the reader closes
   the tab, **Then** no file, no clipboard entry, no download, and no navigation
   has resulted.

---

### Edge Cases

- **Scripting unavailable.** The diagram, the legend, and the text equivalent all
  remain fully readable, every node's detail remains reachable, and no control is
  presented that cannot work. A dead control is worse than a missing one, because
  the reader believes it did something.
- **Network unavailable.** The webfont link the shared head block carries is the
  only network reference in the file. The typeface substitutes and nothing else
  changes; hierarchy is carried by heading level, size and weight, so it survives.
- **Storage refused.** A browser may refuse storage to a local file. The theme
  control keeps working for the session and nothing surfaces to the reader as an
  error.
- **Monochrome rendering or a reader who cannot perceive hue.** Every node role,
  every node state, and every edge kind is still distinguishable, because each has
  a carrier that is not colour.
- **A reader receiving the document as text only.** They read the text
  equivalent and lose nothing. This is the case the whole of FR-027 through
  FR-033 exists for.
- **A reduced-motion preference.** The artifact introduces no motion at all, so
  there is nothing for the preference to suppress. Upstream's hover transform and
  its transition are dropped rather than wrapped in a guard.
- **The diagram wider than the viewport.** It scrolls inside its own container.
  The page body never scrolls horizontally.
- **A reader looking for a copy control.** There is none, and there is none on
  purpose. Every other final-PR template carries one, so the absence must be
  visible as a decision rather than readable as an oversight.
- **A later fill updating one rendering and not the other.** The diagram and the
  text equivalent describe one flow. If a fill could update the picture and leave
  the words stale, the reader who depends on the words is the one who cannot see
  that they have drifted.

## Requirements *(mandatory)*

### Functional Requirements

#### The artifact and its provenance

- **FR-001**: The slice MUST ship exactly one net-new artifact,
  `speckit-pro/artifact-gallery/templates/flowchart.html`, and it MUST be
  self-contained: one file, no build step, no bundler, no sibling asset, and no
  resource fetched at load beyond the webfont reference the shared head block
  already carries.
- **FR-002**: The artifact MUST render from the local-file scheme with no server
  and no install, in both themes, reporting no console error and no console
  warning.
- **FR-003**: The brand-kit block MUST be embedded byte for byte between its
  `BRAND-KIT:START` and `BRAND-KIT:END` markers, the markers included, with no
  edit to any line between them.
- **FR-004**: The gallery-head block MUST be embedded byte for byte between its
  `GALLERY-HEAD:START` and `GALLERY-HEAD:END` markers, the markers included, with
  no edit to any line between them.
- **FR-005**: The artifact MUST open with an attribution header carrying the five
  labels `Upstream repository:`, `Upstream file:`, `License:`, `License text:`
  and `Modified derivative:`, together with the upstream copyright line and the
  licence-text reference.
- **FR-006**: The header's `Upstream file:` value MUST be
  `13-flowchart-diagram.html`, byte-identical to the value this template's
  catalog entry declares as its source file.
- **FR-007**: The port MUST be a modified derivative in fact as well as in its
  header: no upstream colour value, typeface stack, or spacing primitive may
  survive into the shipped file. Every colour the artifact draws MUST name a
  brand-kit token, including the colours of any arrowhead or marker the drawing
  defines, which upstream hard-codes three times.
- **FR-008**: A slot inventory comment MUST sit immediately after the attribution
  header, one line per slot, reading `Slot: … | Fills: … | Source: …` in that
  order with no pipe inside a value, every slot name filename-safe kebab-case and
  unique within the template, and every `Source:` value drawn from the closed set
  the shared validation pins.
- **FR-009**: The inventory MUST carry none of the attribution header's own
  labels or literals, so the scanner cannot read the inventory as the header.
- **FR-010**: The slice MUST change exactly one catalog value: this entry's
  `status`, from `planned` to `shipped`. No other value in any entry may change.
- **FR-011**: The artifact's rendered title MUST equal this template's catalog
  entry title byte for byte. That value is `Flowchart`.
- **FR-012**: FR-011 MUST be verified by a **runnable comparison** that reads the
  catalog title and the artifact title and fails on any difference, not by
  inspection. Slice 1 shipped a sentence-case title against a title-case catalog
  value; a green suite reported nothing, and only independent review caught it.

#### The read-only declaration

- **FR-013**: This entry declares `exports: []`. The artifact MUST therefore
  carry **no export affordance of any kind**: no copy control, no download
  control, no clipboard call, no print or share control offered as an export, and
  no routine that serializes any part of the page into text for a reader to carry
  away.
- **FR-014**: The artifact MUST carry **no reader-input field of any kind**: no
  textarea, no input, no select, no form, and no element made editable. A reader
  of this artifact produces nothing.
- **FR-015**: The absences FR-013 and FR-014 require MUST be **verified by search
  over the shipped bytes**, not assumed. Every other final-PR template in this
  gallery ships an export control and a capture field, and the skeleton this port
  is built from is theirs, so copying one by habit is the realistic failure. An
  absence that nothing looks for is an absence that nothing protects.
- **FR-016**: The export-path requirements slices 1 and 2 carry MUST NOT be
  carried into this artifact, and their absence MUST be recorded in this
  specification as deliberate: the export payload shape, the clipboard-failure
  fallback field, the invocation-currency guard, the per-hunk objection capture,
  the per-section question capture, and the empty-state bodies those captures
  need. None has a subject here.
- **FR-017**: The one control this artifact does carry is the theme control the
  shared head block builds at load. It is not an export and it is not a reader
  input, and nothing in FR-013 through FR-016 removes it.

#### The diagram

- **FR-018**: The artifact MUST draw the operational flow as a diagram inside the
  single file, with no sibling asset and no external image.
- **FR-019**: The drawing MUST carry an accessible name that names the flow it
  depicts, and MUST be exposed to assistive technology as a meaningful image
  rather than as an unlabelled graphic or a presentational one. Upstream ships
  neither a name nor a role.
- **FR-020**: **Node role** — process step, decision, and terminal — MUST be
  distinguishable without colour.
- **FR-021**: **Node state** — at minimum, which node's detail is currently
  disclosed — MUST be distinguishable without colour. Upstream marks it by stroke
  colour alone.
- **FR-022**: **Edge kind** — the ordinary next step, the affirmative branch, and
  the failure branch — MUST be distinguishable without colour. A dashed stroke
  and a worded label are both acceptable carriers; a hue is not.
- **FR-023**: The artifact MUST carry a legend naming every node role, every node
  state, and every edge kind in words. The legend is the carrier of last resort
  and MUST NOT itself depend on colour to distinguish its own entries.
- **FR-024**: Every distinction FR-020 through FR-022 require MUST survive a
  monochrome rendering, and that rendering MUST be recorded as acceptance
  evidence.
- **FR-025**: The diagram MUST be legible at a normal reading width without the
  page body scrolling horizontally. Where the drawing is wider than the viewport
  it MUST scroll inside its own container.
- **FR-026**: The artifact MUST introduce no animation and no transition of its
  own. Upstream animates node hover with a transform transition; the port drops
  the declaration rather than guarding it, so a reduced-motion preference has
  nothing left to suppress.

#### The text equivalent

- **FR-027**: The diagram MUST carry a **text equivalent that conveys everything
  the picture conveys**. A reader who cannot see the diagram MUST lose nothing:
  not a step, not a branch, not an order, not a failure path.
- **FR-028**: The text equivalent MUST give, for every node, its label, its role
  and its detail; and for every edge, its source node, its target node and its
  kind.
- **FR-029**: The text equivalent MUST convey the **order** of the flow and every
  **point at which it branches**, including where a branch rejoins and where it
  terminates. Sequence and branching are carried in the picture by position and
  by stroke path alone, and neither survives into text on its own.
- **FR-030**: The text equivalent MUST be part of the rendered document and
  reachable in reading order. It MUST NOT be visually hidden, positioned
  off-screen as its only rendering, hidden from assistive technology, or
  reachable only by operating a scripted control. Where it sits inside a
  disclosure, that disclosure MUST report its own state and MUST operate with
  scripting unavailable.
- **FR-031**: The text equivalent MUST read as a first-class rendering of the
  flow rather than as a caption, an alt-text substitute, or an appendix.
- **FR-032**: The text equivalent MUST remain complete and correct with scripting
  unavailable.
- **FR-033**: The diagram and its text equivalent MUST be filled from the same
  declared source, so a later fill cannot update one and leave the other
  describing a different flow. Two renderings of one flow that can drift are
  worse than one, because the reader who depends on the text is the reader who
  cannot see that it has drifted.

#### The disclosure

- **FR-034**: Activating a node MUST disclose that node's detail **in the page**:
  what the step does and how it can fail.
- **FR-035**: Activating a node MUST produce nothing durable — no file, no
  clipboard write, no download, no navigation, and nothing the reader carries
  away from the tab. This is the requirement that keeps the `exports: []`
  declaration honest.
- **FR-036**: Every node that discloses detail MUST be reachable in sequential
  focus order and MUST be operable from the keyboard by the same means as any
  other control of its kind.
- **FR-037**: Every interactive node MUST carry a visible focus indicator, and no
  rule may suppress one without an equivalent replacement.
- **FR-038**: The disclosed state MUST be exposed programmatically — an
  interactive node MUST report whether it is the currently disclosed one — and
  MUST NOT be carried by colour alone.
- **FR-039**: When the disclosed detail changes, the change MUST be perceivable
  to a reader who cannot see the diagram, rather than silently replacing content
  elsewhere on the page.
- **FR-040**: The artifact MUST open in a defined state with one node's detail
  already disclosed, so the detail region is never empty on first paint.
- **FR-041**: With scripting unavailable, the diagram and the text equivalent
  MUST both stay fully readable, every node's detail MUST stay reachable, and
  **no control may be offered that cannot work**.

#### Regions and sample content

- **FR-042**: Every fill region MUST ship representative fictional sample content
  held to the minimum that demonstrates the shape. No region ships empty.
- **FR-043**: The sample content MUST declare itself as invented in the rendered
  page, so a reader opening the file cold does not read it as a real flow.
- **FR-044**: The slot inventory MUST be complete and MUST agree in both
  directions with the regions the body delimits. It carries exactly four slots:
  `feature-header` (`Source: spec.md`), `flow-summary`, `flow-diagram` and
  `nodes` (each `Source: plan.md`). **No new `Source:` member is added.**
  `plan.md` is where this process records an operational flow, and it is what the
  gallery's only other diagram slot already declares. Slice 2 added the first
  non-filename member over a recorded dissent; nothing here clears that bar.
  The floor row is single-entry — `flow-diagram` and nothing else — because the
  roadmap's scope for this template is a clickable operational-flow diagram, on
  the precedent of the module-map template's single-entry row.
- **FR-044a**: `flow-diagram` MUST delimit the drawing, its caption, **and** the
  prose stating the flow's order and its branching, in **one** region. Two
  renderings the same fill replaces together cannot drift, which satisfies FR-033
  by construction rather than by discipline. The per-node detail sits in `nodes`
  instead, because the list-slot check requires every element at that region's own
  top level to carry a conforming anchor, and a figure masquerading as a list item
  would be dishonest.
- **FR-044b**: Both inventory lines MUST state the binding between the two
  regions — that each node in the drawing links to the entry of the same slug in
  `nodes` — and FR-015's byte search MUST be extended to assert that every
  in-document link the drawing carries resolves to an id present in the shipped
  file. This is the one part of FR-033 the region structure does not close by
  construction, so it is closed by hand.

- **FR-045**: `flowchart` MUST contribute a list-slot row: its `nodes` region
  holds individually addressable repeated items, anchored `nodes-<item-slug>`,
  unique in the document, at the region's own top level, with the grouping element
  enclosing the region. At least the two anchored items the shared validation
  requires MUST ship.
  The design concept left this open on the ground that nothing durable is
  produced, so no export anchors to a node. **That is true and is not the deciding
  fact.** The list-slot check asserts that a *fragment resolves*, and this
  artifact's disclosure **is** fragment resolution: each node in the drawing is an
  in-document link whose target is that node's entry. An entry a later fill emits
  without its anchor, or with an anchor a second entry repeats, silently breaks
  the link from the drawing — the exact defect the shared check names when it says
  a fragment resolving to two items resolves to neither. The row is therefore
  needed for a **stronger** reason than the one that put the other rows there.
  `nodes` MUST NOT be added to the floor: floor membership would prove only that a
  region of that name exists, never that its items are addressable, which is the
  reason already recorded for the one other list slot that is not a floor entry.
- **FR-041a**: The disclosure MUST be built from native elements and MUST add
  **no authored script**. Each interactive node in the drawing is an in-document
  link to that node's entry in `nodes`; each entry is a disclosure element in one
  **exclusive** group, so exactly one node's detail is open at a time and that
  state is the element's own. The artifact's only script remains the theme control
  the shared head block builds, so the authored-script count matches
  `spec-explainer`'s zero rather than merely approaching it.
- **FR-041b**: The per-node detail MUST sit **below** the drawing in reading
  order, not in a panel beside it. The design concept says "beside the diagram"
  because upstream swaps one panel's content; with one disclosure per node there
  is nothing to swap, and FR-034 requires only that the detail be disclosed in the
  page.
- **FR-018a**: The drawing MUST be inline vector markup with a fixed view box,
  defining **exactly one** arrowhead marker whose fill names a brand-kit token
  through a class rather than a literal. Upstream defines three and hard-codes a
  colour into each, which is the trap FR-007 names.
- **FR-019a**: The drawing MUST be named through its own title element referenced
  by `aria-labelledby`, and **MUST NOT carry `role="img"`**. That role makes every
  descendant presentational, which would remove this drawing's interactive nodes
  from the accessibility tree and defeat FR-036 and FR-038 outright. The gallery's
  existing `role="img"` usage is on a non-interactive drawing; the rule is
  `role="img"` for a static graphic, an accessible name alone for an interactive
  one.
- **FR-042a**: The sample drawing MUST ship **seven** nodes: one entry terminal,
  two process steps, two decisions, one failure terminal and one success terminal.
  That is the smallest set demonstrating every node role, every edge kind, a
  branch, a rejoin and two distinct endings — the demonstrating minimum, against
  upstream's twelve.
- **FR-020a**: Node role MUST be carried by **shape** — rectangle for a process
  step, diamond for a decision, stadium for a terminal — with the role also
  written as a word wherever the shape alone would not name it, reusing the node's
  existing second text line.
- **FR-021a**: Node state MUST be carried by the disclosure's own expanded state,
  which is programmatic, singular within the exclusive group, and not colour. The
  drawn node carries only the focus indicator FR-037 requires, reinforced by a
  **stroke-weight** change because an outline on an inline vector child is not
  uniformly reliable — and stroke weight is not a hue.
- **FR-022a**: Edge kind MUST be carried by **stroke pattern and word together**:
  the ordinary next step solid and unlabelled, the affirmative branch solid and
  labelled with the affirming word, the failure branch dashed and labelled with the
  failing word. Upstream dashes its failure edge but distinguishes its affirmative
  edge by hue alone, which does not survive the port.
- **FR-023a**: The legend MUST NOT be a fill region. It describes the drawing
  conventions this template fixes, not content a later fill supplies, and a legend
  a fill could rewrite could disagree with the drawing it explains. Its entries
  MUST be words; no swatch may carry meaning.
- **FR-024a**: The drawing's caption MUST state that nothing in it is marked by
  colour and that it reads the same in a monochrome print, as the gallery's other
  diagram already does. That sentence is the claim the monochrome evidence is
  checked against.
- **FR-041c**: The zero-script disclosure rests on fragment navigation revealing a
  closed disclosure element. Sources disagree on whether every current browser
  honours it, and this is **recorded rather than assumed**: if the reveal does not
  fire, the link still lands the reader on the right node's summary and one
  keystroke opens it, so the control is one keystroke short rather than dead. The
  manual render MUST confirm the behaviour, and the zero-script property MUST NOT
  be claimed as verified until it does.

- **FR-046**: Every region the body delimits MUST be named in the inventory, and
  every slot the inventory names MUST be delimited by exactly one marker pair
  with its start before its end. Regions MUST be flat — no pair may enclose
  another — and each pair MUST delimit a whole subtree.

#### Runtime robustness and house rules

- **FR-047**: With the network unavailable the artifact MUST stay fully readable
  and every control MUST stay operable; the only observable difference MUST be
  typeface substitution.
- **FR-048**: With storage refused the theme control MUST keep working for the
  session, and nothing may surface to the reader as an error.
- **FR-049**: The artifact MUST honour a reduced-motion preference. Per FR-026 it
  introduces no motion, so this holds by construction rather than by a
  suppression rule of its own.
- **FR-050**: The display typeface token MUST be assigned to first- and
  second-level headings only. The subtle border token MUST carry no meaning
  anywhere in the artifact; every boundary that carries meaning MUST use the
  strong border token. Red at body size MUST use the body-safe danger token
  rather than the brand primitive.

#### Validation, payload, and delivery

- **FR-051**: The shared fill-region validation literals MUST be extended for
  this template in the same shape slices 1 and 2 used, so its regions are
  asserted about from the moment its entry reads `shipped` and not before.
- **FR-052**: The full repository suite MUST pass above the recorded baseline of
  7380 assertions, with the increase accounted for.
- **FR-053**: The release payload MUST be regenerated, because gallery files ship
  in the plugin payload. The plan's Declared File Operations MUST account for the
  generated-artifact contract on both shipped platforms.
- **FR-054**: A manual render of the shipped file from the local-file scheme MUST
  be recorded as acceptance evidence, in both themes, with the network
  unavailable, and including the monochrome rendering FR-024 requires.
- **FR-055**: The pull request MUST base on slice 2's branch, never on the
  default branch.

### Reviewability Notes *(if applicable)*

No `Reviewability-Exception` pragma is claimed, and none is available: the
accepted classes are refactor, infra and upgrade, and none honestly describes
net-new template work. Splitting further is not available either, because a
self-contained HTML artifact cannot be divided across two pull requests and still
render from the local-file scheme. One template per pull request is already the
thinnest vertical slice this work admits.

This slice does not need either escape. It is the one slice in this feature with
real headroom, and the reason is structural rather than lucky: the two export
carriers each spend roughly 340 lines on a routine this artifact does not build
at all.

### Reviewability Budget *(mandatory)*

**The comparator is `spec-explainer`, not slice 1 and not slice 2.** Across this
gallery the `exports` declaration has predicted authored size better than slot
count or upstream size ever did, and this template shares its declaration with
`spec-explainer` and with nothing else that has shipped:

| Template | `exports` | Authored | CSS | Script | Markup |
|---|---|---|---|---|---|
| `spec-explainer` | `[]` | 315 | 169 | 0 | 146 |
| `pr-writeup` (slice 1) | both kinds | 735 | 227 | 334 | 174 |
| `annotated-diff` (slice 2) | both kinds | 724 | 259 | 344 | 121 |

Decomposed against `spec-explainer`'s realized figures, and **re-declared at
Plan** from measurement as this section instructs. The working belongs in
`plan.md`; the ceiling beside each component is what the Plan-phase checkpoints
hold it to.

| Component | Comparator | Target | Ceiling | Basis |
|---|---|---|---|---|
| CSS | 169 | ~200 | 210 | `spec-explainer`'s 169, plus the diagram-specific rules it never carried: node shape by role, edge kind, the focus indicator on a drawn node, the legend, the detail region, and the two-column layout. Its disclosure-element rules do not carry, because this template's disclosure attaches to a drawn node |
| Script | 0 | ~80 | 90 | the in-page disclosure Q7 fixes, and nothing else. No export routine, no clipboard fallback, no currency guard — the three things that cost slices 1 and 2 roughly 340 lines apiece |
| Markup | 146 | ~180 | 200 | the drawing, its text equivalent, the legend, the detail region, and the page frame. Upstream's drawing is about 100 lines of vector markup; the text equivalent has no upstream counterpart and is authored fresh |
| **Total** | **315** | **460** | **500** | warn, with 340 lines of headroom below the block threshold |

**Markup is the dimension most likely to miss**, because the text equivalent is
authored from nothing and its completeness obligation is the strictest
requirement in this spec. The sensitivity, rebased on the components above:

| Markup lines | Total | Result |
|---|---|---|
| 180 | 460 | warn — the declared target, 340 spare |
| 300 | 580 | warn, 220 spare |
| 460 | 740 | warn, 60 spare |
| 521 | 801 | block |

The markup would have to grow nearly threefold before the block threshold came
into range. That is what "the risk moved" means: this slice is not going to fail
on size, and the slack it enjoys is not budget to spend. Every line of clipboard
or capture code that slack would buy is an affordance the catalog does not
declare, so FR-013 through FR-016 spend it on nothing.

**A measurement checkpoint is still adopted at Plan** as an explicit, checkable
constraint, using the measuring instrument slice 1's quickstart already records
rather than a second one. The first fires after the CSS and **before** the
markup, at the CSS ceiling above, so an overrun surfaces with roughly 200 lines
written rather than 460.

The figure below excludes the 458 lines of canonical embedded blocks a reviewer
never reads because they are byte-verified copies: the brand-kit block at 318
lines and the gallery-head block at 140.

- **Primary surface**: docs/process (a shipped template file)
- **Secondary surfaces, if any**: seed/config (one catalog value), harness/adapter (the fill-region validation literals)
- **Projected production files**: 1 (net-new: the artifact itself)
- **Projected total files**: 13, carried from slices 1 and 2's measured count for
  the same artifact shape and re-measured at Plan by the setup gate. Below the
  warn threshold of 15 either way.
- **Budget result**: warn — above the warn threshold and comfortably below the
  block threshold. Slice 2 withdrew, on slice 1's evidence, the claim that a
  component measured against shipped implementations of itself cannot miss; that
  withdrawal stands, which is why the CSS component carries a checkpoint here
  even though its comparator is a shipped file.
- **Split decision**: This spec **is** the split. ART-003 was re-declared at
  scaffold as three stacked slices, one template per pull request, after the
  earlier feature's first slice shipped two templates of the same kind and
  measured a hard block that forced a mid-implement re-slice. This spec covers
  slice 3 only, and it is the last of the three. Re-measure and re-declare at
  this slice's Plan phase: the setup gate reads a declaration rather than
  measuring the tree, and it will not catch a stale number for you.

**The declaration is the last line of this section on purpose.** The gate's
parser takes the *last* phrase match in the whole file and reads the first number
within forty characters of it, so any prose placed after this line that repeats
the phrase near any other number silently becomes the declared figure. That trap
fired four times across slices 1 and 2 — on a spec identifier, on a filename, on
a table header, and on a threshold. Nothing below repeats the phrase.

- **Projected reviewable LOC**: **460**

### PR Review Packet Requirements *(mandatory)*

- The pull request description MUST include: what changed, why, non-goals, review
  order, scope budget, traceability, verification evidence, known gaps, and
  rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- The pull request MUST base on slice 2's branch, never on the default branch.
- Review order MUST put the authored markup, the text equivalent, and the
  diagram-specific styling ahead of the embedded canonical blocks, which are
  byte-verified copies rather than material to read.
- Non-goals MUST state plainly that this artifact ships no export and no reader
  input, and that the omission is what its catalog entry declares — otherwise a
  reviewer who has just read slices 1 and 2 will read the absence as an
  oversight.
- Deferred work MUST name the follow-up spec or issue. The generation step and
  the ready flip are ART-010 and are named deferrals here.
- Known gaps MUST name every gap the pull request carries, including the ones
  slices 1 and 2 recorded that remain true: the plan-phase estimator reports a
  projection of zero for a production surface of this file type, so its green line
  reads as reassurance it cannot supply; the gate's declaration parser takes the
  last phrase match in a file; the shipped payload documents no fill-region
  grammar; the shared validation binds only the templates its floor names, so a
  shipped non-floor template is never parsed; and **no check reads a catalog
  entry's declared export kinds against the artifact**, which is the gap that
  matters most on this slice, because it is the one that would catch a forgotten
  export control shipping under an empty declaration. FR-015 closes it for this
  template by hand; closing it in general would be a change to shared validation.
- Known gaps MUST also carry forward the one slice 2 added and did not close in
  general: nothing asserts that an artifact's title agrees with its catalog
  entry's title. FR-012 closes it for this template by hand.

### Key Entities

- **The artifact**: one HTML file carrying a drawing of an operational flow, a
  text equivalent of that drawing, a legend, a per-node detail region, an
  attribution header, a slot inventory, sample content declared as invented, and
  no export control and no reader input at all.
- **A node**: one step in the flow. It carries a label, a role, and a detail
  describing what it does and how it can fail. It may be the currently disclosed
  one, and that state is reported rather than coloured.
- **A node role**: what kind of step a node is — a process step, a decision, or a
  terminal. A closed set, and every member distinguishable without colour.
- **An edge**: one transition between two nodes. It carries a source, a target,
  and a kind: the ordinary next step, the affirmative branch, or the failure
  branch. Every kind distinguishable without colour.
- **The text equivalent**: the rendering of the same flow in words, complete
  enough that a reader who never sees the drawing loses nothing. Not a caption
  and not an alternative text string; a first-class rendering bound to the same
  source as the drawing.
- **A fill region**: a named span of the artifact an authoring agent replaces
  later, delimited by one paired comment marker and described by one inventory
  line.
- **The slot inventory**: the machine-readable list of regions. It is the only
  thing that tells an authoring agent what it must fill, which is why it is bound
  in both directions to the regions the body delimits.
- **The catalog entry**: the routing row that already exists for this template,
  declaring its title, its stage, its trigger, its provenance, its empty export
  array, and the single status value this slice changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer opens the artifact from a filesystem with no server and
  no install and reads the whole flow; the browser reports zero console messages,
  zero failed loads, and zero missing content.
- **SC-002**: A reader who disregards the diagram entirely and reads only the
  text equivalent can name 100% of the flow's steps, 100% of its branches, the
  order of the whole flow, and every point at which it can fail — with no item
  available from the picture that is unavailable from the words.
- **SC-003**: In a monochrome rendering, 100% of node roles, node states, and
  edge kinds remain distinguishable.
- **SC-004**: A reviewer using a keyboard alone reaches and activates 100% of the
  interactive nodes, with a visible focus indicator at every one of them.
- **SC-005**: The number of export controls, clipboard operations, download
  triggers, and reader-input fields in the shipped file is **zero**, established
  by a search over the shipped bytes rather than by inspection.
- **SC-006**: With scripting unavailable, 100% of the flow's content — diagram,
  legend, text equivalent, and every node's detail — remains readable, and the
  number of controls offered that cannot work is zero.
- **SC-007**: With the network unavailable, 100% of the artifact's content stays
  readable and 100% of its controls stay operable; the only observable difference
  is typeface substitution.
- **SC-008**: The artifact's rendered title and its catalog entry's title differ
  by zero bytes, established by a comparison that can be run rather than read.
- **SC-009**: Exactly one catalog value differs from its pre-slice state, and it
  is this entry's status.
- **SC-010**: Both canonical blocks in the shipped file are byte-identical to
  their canonical sources, markers included.
- **SC-011**: The full repository suite passes with an assertion count above the
  7380 baseline, and the increase is accounted for.
- **SC-012**: The measured authored size of the shipped file lands at or below
  the declared figure, or the miss is explained against the component ceilings
  rather than absorbed silently.
- **SC-013**: A reader opening the file cold can state, within one minute, what
  flow is drawn and which point in it a change would turn on.

## Assumptions

- The upstream source is fetched read-only into the session scratchpad at
  implement time and never staged, per the protocol the design concept records.
  Only branded derivatives are committed.
- Upstream's drawing mechanism — inline vector markup with a fixed view box, plus
  a small script for the disclosure — is kept and restyled to brand tokens, per
  the design concept's Q3 and ART-002's Q6. No drawing library, no canvas, and no
  generated image is introduced, because any of them would break the
  single-self-contained-file requirement.
- Upstream sections that map to no fill region are dropped rather than ported,
  per Q3. That is one of the two levers holding the port to its size, and the
  other is Q2/Q11's cap on anchor content.
- The two canonical blocks measure 458 lines together — 318 for the brand kit and
  140 for the gallery head — carried from slices 1 and 2's measurement of the
  same blocks.
- `spec-explainer`'s realized 315 authored lines is the best available comparator
  for a read-only artifact in this gallery. It is a sample of one, which is why
  the components above carry ceilings and a Plan-phase checkpoint rather than a
  bare target.
- The reader of this artifact is a human reviewer, not an agent. The ART-010
  generation step is a second consumer, and it reads the slot inventory rather
  than the rendered page.
- The shared theme control, the brand kit's focus-indicator rule, and the brand
  mark are all inherited from the canonical blocks and are not re-specified here.

## Dependencies

- **ART-001** — the brand kit, the gallery catalog, the SPA contract, and the
  gallery scanner. Satisfied; shipped in PR #407.
- **Slice 1 of this spec** (`pr-writeup`) — the skeleton, the attribution header,
  the inventory format, and the CSS house style. Shipped on this branch.
- **Slice 2 of this spec** (`annotated-diff`) — the branch this one is cut from
  and the base its pull request stacks on. Shipped on this branch.
- **`spec-explainer`**, shipped in ART-002 — the precedent for a read-only
  artifact, and this slice's comparator for size and for obligations alike.

## Out of Scope

- **Generation and authoring logic, and the ready flip.** ART-010 fills these
  regions; this slice ships the template and its inventory.
- **Any export affordance whatsoever**, and any reader-input field. Not deferred
  — excluded, because the catalog entry declares none. See FR-013 through
  FR-016.
- **Any change to the SPA contract document, the brand kit, the shared head
  block, the signal vocabulary, or any catalog value other than this entry's own
  status.**
- **Closing the two general validation gaps in shared validation** — that nothing
  compares an artifact's title to its catalog entry's title, and that nothing
  reads a catalog entry's declared export kinds against the artifact. Both are
  closed for this template by hand, in FR-012 and FR-015; closing either in
  general is a change to shared validation and belongs to a spec of its own.
- **The UAT walkthrough template.** ART-009 owns it; it is repo-authored rather
  than an upstream port.
- **The remaining gallery templates.** ART-004 and ART-005 own them.

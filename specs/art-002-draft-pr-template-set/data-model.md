# Phase 1 Data Model: Draft-PR Template Set (ART-002)

Nothing here is persisted. Two of these entities are static structure inside a
shipped file, three exist only in the DOM for the life of a tab, and one exists
only for the moment an export is built. The model is written down anyway, because
the relationships between them are what the Layer 4 checks assert and what the
authoring agent in ART-007 will read.

---

## Gallery template artifact

One self-contained document a reader opens straight from a filesystem. Four are
delivered here.

| Field | Type | Rule |
|---|---|---|
| file | one HTML file | All behavior, styling, and content inside it. No sibling asset, no build step. **FR-001** |
| filename stem | string | Equals the identifier of the catalog entry that claims it. The path is derived, never stored. **FR-010** |
| `BRAND-KIT` region | embedded block | Copied from `brand-kit.css` byte for byte **with its markers**, appearing exactly once, start before end. 318 lines. **FR-002** |
| `GALLERY-HEAD` region | embedded block | Copied from `theme-toggle.html` byte for byte with its markers, exactly once, start before end, as a direct child of the head element with nothing content-bearing before it except a character-encoding declaration. 140 lines. **FR-002** |
| attribution header | HTML comment | Five exact labels plus the verbatim copyright line. The upstream repository and upstream file it names must equal what the catalog entry declares. **FR-003** |
| slot inventory | HTML comment | Exactly one, immediately after the attribution header, outside every fill region. See *Slot inventory*. **FR-012** |
| external references | set | Exactly one — the typeface request inside the canonical head block. Any other asset is embedded, and only as an image or font media type. **FR-005** |
| prohibited constructs | set | Empty, including inside script string literals and inside markup built as a string. **FR-004** |
| payload-rewriter references | set | Empty. No run of parent-directory segments ending in a skills directory followed by a path. Skills are named in prose. **FR-007** |

**Relationships.** Claimed by exactly one routing catalog entry. Contains one
slot inventory and one or more fill regions. Contains zero or more item anchors,
each inside exactly one fill region.

**Invariant that spans two entities.** The artifact file exists **if and only if**
its catalog entry reads `shipped`. Both directions fail: a file without the flip,
and a flip without the file. A file no entry claims fails as an orphan. **FR-010**

---

## Routing catalog entry

The record in `manifest.json` that names a template and routes it. This feature
changes exactly one value in four of these entries.

| Field | Changed here? | Value for this feature's four entries |
|---|---|---|
| `id` | **No** | `implementation-plan`, `spec-explainer`, `code-approaches`, `module-map` |
| `category` | No | unchanged |
| `title` | No | unchanged |
| `when_to_use` | No | unchanged |
| `stage` | No | `draft-pr` on all four |
| `trigger` | No | `always` on the first two; `any_of` on the other two |
| `source` | No | `origin: upstream` with the file each derives from |
| `status` | **Yes** | `planned` → `shipped`, two per slice |
| `exports` | No | `["prompt","markdown"]` on three; `[]` on `spec-explainer` |

**State transition.** `planned` → `shipped`, once per entry, in the same change
that adds the artifact file. There is no reverse transition in this feature, and
no other value moves. **FR-008**

---

## Fill region (slot)

A named, delimited region an authoring agent later replaces wholesale.

| Field | Type | Rule |
|---|---|---|
| name | kebab-case string | Lowercase alphanumerics in hyphen-separated segments; no leading, trailing, or repeated hyphen; no path separator, parent-directory segment, whitespace, or dot. Unique within its template. **FR-015** |
| start marker | HTML comment | `<!-- FILL:<name>:START -->`, exactly once. **FR-011** |
| end marker | HTML comment | `<!-- FILL:<name>:END -->`, exactly once, after its start. **FR-011** |
| content | inert markup | Ships containing representative, plainly fictional worked-example content. **FR-014** |
| nesting | — | Flat. No slot's marker pair may enclose another's. **FR-015** |
| control markup | — | None. A region carries inert content plus its per-item anchors, never a reader-input control. **FR-016a** |

**Granularity.** One slot per section, never one per repeated item. A slot holding
a repeated list carries the whole list, so item count is a property of the feature
rather than of the template. Baking `phase-1`…`phase-4` into a template would cap
a plan at four phases.

**Completeness.** A template must not carry a region of feature-specific content
that is not a slot. Unfilled sample content in a filled artifact reads as the
project's own data. **FR-015**

### The 21 slots, in document order

| Template | Slots |
|---|---|
| implementation-plan | `feature-header`, `plan-stats`, `phases`, `data-flow`, `mockups`, `risk-register`, `task-inventory` |
| spec-explainer | `feature-header`, `tldr`, `goals`, `non-goals`, `acceptance-criteria`, `clarification-faq` |
| code-approaches | `feature-header`, `approaches`, `recommendation` |
| module-map | `feature-header`, `module-summary`, `module-graph`, `modules`, `key-files` |

---

## Slot inventory

A template's own record of its slots, and the surface the ART-007 authoring agent
reads. No central registry file exists; adding one would create a shared file that
can drift.

| Field | Type | Rule |
|---|---|---|
| container | one HTML comment | Immediately after the attribution header, outside every fill region. **FR-012** |
| labels carried | — | None of the attribution header's own labels or literals, so the two cannot be confused. **FR-012** |
| line format | string | `Slot: <name> \| Fills: <what fills it> \| Source: <source artifact>` — those three labels in that order, one slot per line, no pipe character inside any value. **FR-012** |
| `Source` vocabulary | closed set | `spec.md`, `plan.md`, `tasks.md`, `research.md`, `design-concept.md`. A slot drawing on two names both, comma-separated. |

**The both-ways invariant.** The inventory and the delimited regions agree in both
directions: every documented slot has a marker pair, and every marker pair is
named in the inventory. Either direction misleads the authoring agent, so either
direction is a failure. **FR-013**

**Why placement is load-bearing.** The gallery scanner takes the first
parser-recognized comment carrying any attribution element as the header. An
inventory placed before it that mentioned a licence or the upstream repository
would be read as the header instead.

---

## Item anchor

The stable handle an objection or a selection attaches to. Static markup, shipped
in the file.

| Field | Type | Rule |
|---|---|---|
| carrier | `id` attribute | On the item element, so it doubles as a document fragment a reader can use to find the item again after leaving the document. **FR-015, FR-018** |
| value | string | `<slot>-<item-slug>`, under the same character rules as slot names. Unique across the template. **FR-015** |
| position | — | Inside its slot's region, at the region's own top level. |

**Which slots carry them.** The list slots whose items an objection or a selection
attaches to: `implementation-plan`/`phases`, `code-approaches`/`approaches`,
`module-map`/`modules`. `spec-explainer` carries none, which is its read-only
declaration showing up in the structure rather than only in prose.

**Relationship to controls.** A reader-input control is **not** part of the
anchor. The template's own behavior mounts the control onto the anchor at load and
inserts it immediately after, so tab order and reading order follow visible order
without a positive tab index. **FR-016a**

---

## Objection

A reader's note attached to one phase or one module. Lives in the DOM only.

| Field | Type | Rule |
|---|---|---|
| text | free text | What the reader typed. Empty means no objection, not an approval. |
| item anchor | anchor value | The tie is structural, not something the reader restates in prose. **FR-016** |
| disclosure state | open / closed | Starts **closed**. The disclosure's own control states in text whether the item currently carries a note, so a recorded objection is visible without opening it. **FR-018** |

**Rule that reaches the export.** An export lists only the items the reader
recorded against. No line, no placeholder, and no count for an item left empty —
reporting an item as carrying no objection asserts an approval the reader did not
record. **FR-018**

---

## Approach selection

The reader's single choice among the compared approaches, with their reason.

| Field | Type | Rule |
|---|---|---|
| chosen approach | zero or one anchor | A native grouped single-choice control carrying a visible group label as its accessible name. Exactly one may be chosen; none is a valid state. **FR-017** |
| reason | free text, **optional** | An absent reason is named rather than omitted or blocked on. **FR-017** |

**State transition.** Choosing a second approach replaces the first. An export
carries only the current selection, never a history.

---

## Export payload

The text an export control produces from live state at the moment it is invoked.
Exists only for that moment.

| Field | Rule |
|---|---|
| derivation | From live state, never from a value written into the file when it was authored. **FR-021** |
| content | The reader's conclusion, not the document's content. **FR-022** |
| coordinates per item | Four, read from live state — the feature, the artifact, the slot, and the item's visible label — plus the item's stable anchor in a fragment-usable form. **FR-018** |
| honesty | Never a conclusion the reader did not reach; never a value the reader could not see in the rendered document. **FR-023** |
| empty state | States that nothing was recorded **and** that the record is not an approval, in wording fixed per export kind, while still naming the artifact and the feature. **FR-018** |
| kinds | `prompt` — the conclusion as an instruction to a coding agent. `markdown` — the same conclusion as a record for a pull-request comment. One control per kind the entry declares, labelled by destination. **FR-019** |

The literal strings are pinned in
[`contracts/export-payload-contract.md`](./contracts/export-payload-contract.md).
They are stated there rather than left to each implementation, because three
templates emit them and the acceptance runbook checks the same text.

**Failure path.** When clipboard access fails or is refused, the artifact reveals
the same text in a selectable, focusable field, moves focus to it, and does **not**
report success. One message covers every failure mode and asserts no cause,
because the artifact cannot distinguish a refused permission from an unfocused
document from a browser policy. No deprecated second attempt is made. **FR-025**

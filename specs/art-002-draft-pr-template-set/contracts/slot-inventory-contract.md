# Contract: The Slot Inventory

This is the interface between a shipped template and the authoring agent that
fills it. The agent reads the template's own inventory comment to learn what it
must fill; nothing else tells it. The Layer 4 module
`tests/speckit-pro/unit/test-artifact-fill-regions.py` is what holds this
contract true.

`speckit-pro/artifact-gallery/SPA-CONTRACT.md` remains normative for everything
about the artifact itself. This document covers only the fill-region convention
ART-002 introduces on top of it.

---

## The marker pair

Every region an authoring agent later populates is delimited by a matched pair of
HTML comments:

```html
<!-- FILL:phases:START -->
  … inert content plus per-item anchors …
<!-- FILL:phases:END -->
```

- Each pair appears **exactly once** in the file, start before end.
- Regions are **flat**. No pair may enclose another.
- Both markers are **parser-recognized comments**. Marker-shaped text inside a
  `script` element is raw character data, not a comment, and does not count.
- The region carries inert content and per-item anchors only. It never carries a
  reader-input control, because the agent replaces the whole region and would
  delete one.

## The slot name

Filename-safe kebab-case, following the same character rules the routing catalog
applies to identifiers:

```text
^[a-z0-9]+(-[a-z0-9]+)*$
```

No leading, trailing, or repeated hyphen; no path separator, parent-directory
segment, whitespace, or dot. Unique within its template. The same rules make the
name safe in a filename, in a document fragment, and in a comment marker.

## The inventory comment

Exactly one per template, placed **immediately after the attribution header** and
outside every fill region:

```html
<!--
  Slot: feature-header | Fills: the feature's identifier, name, and one-line intent | Source: spec.md
  Slot: plan-stats | Fills: phase count, file count, and projected size | Source: plan.md
  Slot: phases | Fills: one entry per planned phase, each with its own anchor | Source: plan.md
-->
```

**Line format.** One slot per line:

```text
Slot: <name> | Fills: <what fills it> | Source: <source artifact>
```

Those three labels, in that order, separated by a pipe. **No pipe character
inside any value** — the pipe is the field separator, and a value carrying one
would make the line ambiguous to split.

**`Source` vocabulary — closed.** One of `spec.md`, `plan.md`, `tasks.md`,
`research.md`, `design-concept.md`. A slot drawing on two names both, separated by
a comma.

**What the inventory must not carry.** None of the attribution header's own labels
or literals — not `Upstream repository:`, `Upstream file:`, `License:`,
`License text:`, `Modified derivative:`, not the upstream repository name, not the
copyright line, not the licence-text reference.

**Why placement is load-bearing.** The gallery scanner takes the **first**
parser-recognized comment carrying any attribution element as the attribution
header. An inventory placed before the header that mentioned a licence or the
upstream repository would be read as the header instead, and the artifact would
fail its provenance check for a reason that names the wrong file region. Placing
the inventory after the header, carrying none of its labels, closes that by
construction.

**No central registry.** The inventory lives inside the template. A shared file
listing every template's slots would be a foundation file a port must not edit,
and it could drift from the templates it describes.

## Both-ways agreement

The inventory and the delimited regions agree in **both** directions:

1. Every slot the inventory names has exactly one marker pair in the body.
2. Every marker pair in the body is named in the inventory.

Either direction alone misleads the authoring agent — a documented slot with no
region is a fill that silently does nothing, and an undocumented region is content
the agent never replaces, left showing fictional sample data in a filled
artifact. So both are failures, and they are checked separately so a failure names
the right defect.

## Granularity

**One slot per section, never one per repeated item.** A slot holding a repeated
list carries the whole list, so the number of items is a property of the feature
rather than of the template. Baking `phase-1`…`phase-4` into a template would cap
a plan at four phases.

**Every repeated item carries a stable anchor** instead:

```html
<li id="phases-schema-migration"> … </li>
```

- Value: `<slot>-<item-slug>`, under the slot name character rules.
- Carried as an `id`, so it doubles as a document fragment a reader can use to
  find the item again after leaving the document.
- Unique across the template.
- Carried by items in the list slots whose items an objection or a selection
  attaches to: `implementation-plan`/`phases`, `code-approaches`/`approaches`,
  `module-map`/`modules`.

## Completeness

A template must not carry a region of feature-specific content that is not a slot.
A region that names the feature, counts its work, or describes its shape but
carries no marker pair keeps its shipped fictional content after the artifact is
filled, where it reads as the project's own data. Every feature-specific region is
a slot.

## Sample content

Every slot ships containing representative, plainly fictional worked-example
content, so a gallery browser judges the template from a rendered document rather
than an empty frame, and so the manual render check exercises real layout. It must
read as obviously fictional, so no reader takes it for the project's own data. The
authoring agent replaces whole delimited regions rather than merging into them, so
nothing survives a fill.

---

## The 21 slots

| Template | Slot | Source artifact | Roadmap floor? | List slot? |
|---|---|---|---|---|
| implementation-plan | `feature-header` | spec.md | | |
| | `plan-stats` | plan.md | | |
| | `phases` | plan.md | **yes** | **yes** |
| | `data-flow` | plan.md | **yes** | |
| | `mockups` | design-concept.md | **yes** | |
| | `risk-register` | plan.md, research.md | **yes** | |
| | `task-inventory` | tasks.md | **yes** | |
| spec-explainer | `feature-header` | spec.md | | |
| | `tldr` | spec.md | **yes** | |
| | `goals` | spec.md | **yes** | |
| | `non-goals` | design-concept.md, spec.md | **yes** | |
| | `acceptance-criteria` | spec.md | **yes** | |
| | `clarification-faq` | spec.md, design-concept.md | **yes** | |
| code-approaches | `feature-header` | spec.md | | |
| | `approaches` | research.md, plan.md | **yes** | **yes** |
| | `recommendation` | research.md | | |
| module-map | `feature-header` | spec.md | | |
| | `module-summary` | plan.md | | |
| | `module-graph` | plan.md | **yes** | |
| | `modules` | plan.md | | **yes** |
| | `key-files` | plan.md | | |

**The floor column is a floor, not an equality.** It marks the regions the roadmap
names, which the Layer 4 module holds as a pinned literal. A template may carry
more slots than the floor names — the blank rows above are exactly that case — and
the both-ways agreement is what binds the remainder.

**`modules` is a list slot and not a floor entry**, which is the one row that
looks inconsistent and is not. Floor membership would prove only that a region of
that name exists, never that its items are individually addressable, so the floor
cannot verify that requirement even in principle. It gets its own assertion
instead. Keeping the floor sourced from one document is also what keeps the
literal auditable.

**`module-graph` carries no marker pair inside the drawing.** The distinguished
path is a required property of its content, not a slot of its own; a pair inside
the figure would split one drawing across two fill operations that share a
coordinate system.

# Single-File Artifact Contract

This contract defines the gallery behavior a template author must preserve.
`manifest.json` is the inventory and routing source of truth; repository tests
validate the contracts below.

## Single-file output

Each shipped artifact is one HTML file that opens directly from the filesystem.

- Inline all behavior, styling, and data. Do not require a build, server, or
  sibling asset.
- Keep the artifact readable and interactive offline.
- The only resource-loading exception is the canonical Google Fonts request.
  Typeface fallback is the only offline difference.
- Keep the document complete: doctype, language, head, title, body, semantic
  headings, and a single top-level heading.

## Canonical blocks

Copy these marked regions into every artifact byte for byte:

| Region | Source |
|---|---|
| `/* BRAND-KIT:START */` through `/* BRAND-KIT:END */` | `brand-kit.css` |
| `<!-- GALLERY-HEAD:START -->` through `<!-- GALLERY-HEAD:END -->` | `theme-toggle.html` |

The brand block provides the palette, type, focus, and reduced-motion behavior.
The head block provides the security policy, font request, theme state, and
optional Racecraft mark. Amend a canonical source and all embedded copies
together; never customize one copy.

Mount the mark only where it belongs:

```html
<span data-rc-brand-mark></span>
```

## Manifest and routing

The manifest has `schema_version`, `signals`, `export_kinds`, and
`templates`. Each template entry carries:

| Field | Contract |
|---|---|
| `id` | Stable kebab-case join key and `templates/<id>.html` stem. |
| `category` | Browsing group, not a routing input. |
| `title` | Human-readable output name. |
| `when_to_use` | Selection guidance for an author or reader. |
| `stage` | `draft-pr`, `final-pr`, or `ad-hoc`. |
| `trigger` | `{"always": true}` or a non-empty `{"any_of": [...]}`. |
| `source` | Upstream filename or repository origin. |
| `status` | `planned` or `shipped`. |
| `exports` | Declared subset of `prompt` and `markdown`. |

A shipped entry has exactly one matching HTML file. A planned entry has none.
Files without a shipped entry are invalid. To complete a planned template, add
its file and change only that row's status after its behavior is ready.

Automated selection filters by stage, then evaluates the trigger. `always`
means always within that stage. `any_of` means at least one named signal is
present. Ad-hoc entries are selected explicitly rather than by stage routing.

### Signals

- `competing_approaches`: planning considered more than one viable approach.
- `brownfield_change`: the change modifies existing code.
- `self_review_findings`: self-review recorded at least one actionable gap.
- `large_diff`: the repository reviewability gate returned warn or block.
- `operational_flow_change`: the change alters a multi-step runtime or
  delivery process.

Signal producers own the evidence and thresholds. The gallery only validates
that triggers use declared signal names.

## Fill regions

Each template declares its inputs in one leading HTML comment:

```text
Slot: <name> | Fills: <content and hooks to preserve> | Source: <planning input>
```

Each declared slot has one ordered, non-nested marker pair:

```html
<!-- FILL:<name>:START -->
...replaceable sample content...
<!-- FILL:<name>:END -->
```

Keep the markers after filling. Put `document-title` in the head and all other
regions in the body. A fill replaces only the bytes between its pair. Preserve
any IDs, classes, element types, heading structure, and visible state words the
slot inventory names because scripts, styling, exports, or accessibility use
them. The filled document must remain structurally valid HTML.

## Attribution

An upstream entry carries one leading comment whose values agree with its
manifest source:

```html
<!--
  Upstream repository: anthropics/html-effectiveness
  Upstream file: <source.file>
  License: MIT
  License text: UPSTREAM-NOTICE.md
  Modified derivative: yes — re-skinned with Racecraft brand tokens; not the upstream original
  Copyright (c) 2026 Anthropic PBC
-->
```

Repository-origin templates carry no upstream attribution. The complete MIT
notice remains in `UPSTREAM-NOTICE.md`.

## Export behavior

The manifest's `exports` array is authoritative:

- `prompt` gives a coding agent the reader's conclusion and its consequence.
- `markdown` records the same conclusion for a pull request or file.
- An empty array means the artifact produces no durable reader decision.

Build exports from visible live state when the reader invokes them. Include
enough artifact and anchor context to act without reopening the file. Never
invent a decision or export hidden inputs.

Use one keyboard-operable control per declared kind, labeled `Copy as prompt`
or `Copy as Markdown`. Report success or failure in text. Clipboard access can
fail under `file://`; on failure reveal the exact export in a labeled,
focusable, selectable field for manual copy. Keep registered export lead lines
stable because the feedback sweep recognizes them.

## Accessibility

- Use semantic headings and native controls with programmatic names.
- Give every button `type="button"` unless it intentionally submits a form.
- Do not use positive `tabindex` or trap focus.
- Keep `:focus-visible` and `prefers-reduced-motion` behavior.
- Do not use color as the only carrier of meaning.
- Use `--rc-border-strong` for meaningful boundaries;
  `--rc-border-subtle` is decorative only.
- Use `--rc-danger-text` for red body copy. Brand red and accent are for large
  text or meaningful non-text.
- Any horizontal overflow region must be keyboard reachable, have
  `role="group"`, and have a specific accessible name. Use
  `data-rc-keyboard-scroll="horizontal"` for new regions.

## Security

An artifact is an executable local document. Keep the canonical policy as the
first content-bearing part of the head after character encoding. Do not add:

- `base`, `iframe`, `object`, or `embed`;
- scheme-relative URLs;
- `on*`, `srcdoc`, or `ping` attributes;
- a form submission target;
- `data:` resources other than `image/*` or `font/*`.

The canonical policy starts from `default-src 'none'` and allows only inline
behavior and styling, the canonical Google Fonts origins, and data images or
fonts. The browser suite observes every rendered artifact and aborts unexpected
HTTP(S), worker, WebSocket, popup, and navigation activity; it also proves the
artifact remains usable with the font request unavailable. Do not treat a
spelling scan as a security boundary.

Repository and pull-request values are untrusted. Escape them for HTML text and
attribute contexts. Never interpolate them into script, style, URL-valued, or
event-handler contexts. Prefer text nodes, `textContent`, and plain data
attributes. Static canonical markup is not permission to inject dynamic HTML.

## Payload integrity

Do not place relative references to files below a skills directory in gallery
content. The Codex payload rewriter changes those paths and would make installed
gallery bytes differ from their source.

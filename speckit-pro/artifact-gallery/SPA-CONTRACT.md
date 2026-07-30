# Single-File Artifact Contract

This is the contract every artifact in the SpecKit Pro gallery obeys. If you are
porting a template into `templates/`, read this first: it says what the artifact
must be, what the routing catalog beside it means, and the one catalog value
your port is allowed to change.

**Which statement governs.** The catalog's shape is written down twice — as
prose here, and as assertions in the repository's gallery validation. The
**validated** shape is normative; this document is its explanatory statement.
Where the two disagree, follow the validation and report the disagreement as a
defect rather than choosing between them. One part is closed automatically: the
signal vocabulary below is checked against the catalog on every run. The rest is
held true by review, which is why the authority is named here rather than left
to inference.

## The single-file rule

An artifact is one HTML file. All behavior, styling, and data live inside it.

- No build step, no bundler, no preprocessor, no post-processing.
- No sibling asset — no linked stylesheet, script file, image file, or data
  file next to the artifact.
- A reader opens the file straight from the filesystem, with no server and no
  install. It renders correctly that way and reports no errors: nothing in the
  browser console, no failed load, no missing content.
- With the network unavailable the artifact stays completely readable and every
  control still works. The only visible difference is typeface substitution.

The single exception is the brand typeface request, which reaches
`fonts.googleapis.com` and `fonts.gstatic.com`. Those two hosts are the only
external references an artifact may make from a position that loads a resource.
Addresses a reader clicks to navigate, and addresses written in comments or in
visible text, are not resource-loading positions and stay permitted — that is
what keeps provenance and attribution links intact.

## The two canonical blocks

Every artifact embeds two shared regions verbatim. You copy them in; nothing
transforms them on the way.

| Block | Canonical file | Marker pair |
|---|---|---|
| Brand tokens | `brand-kit.css` | `/* BRAND-KIT:START */` … `/* BRAND-KIT:END */` |
| Gallery head | `theme-toggle.html` | `<!-- GALLERY-HEAD:START -->` … `<!-- GALLERY-HEAD:END -->` |

- Copy each region **with its markers**, byte for byte. A single character of
  drift fails validation, and the failure names the artifact and the block.
- Validation compares only the marked region. The markup and styling you write
  outside the markers are yours and are never compared.
- Each pair appears exactly once in an artifact, start before end.
- The head block is named for the region it is, not for the control inside it:
  it carries the security policy declaration, the font request, the theme
  applied before first paint, and the theme control. Its file name,
  `theme-toggle.html`, is unchanged.
- Drift is a failure, not a customization. If an artifact needs something the
  block does not give it, amend the canonical file in its own change — never
  edit the copy inside an artifact.

## What porting a template changes

Two embedded blocks, one new artifact file, and exactly one catalog value.

1. Add `templates/<id>.html`, where `<id>` is the identifier the catalog
   already carries for that template.
2. Embed the two canonical blocks.
3. Change that entry's `status` from `planned` to `shipped`.

Nothing else. A port edits no shared foundation file — not `brand-kit.css`, not
`theme-toggle.html`, not this document, not the signal vocabulary, and not
another entry.

**Identifiers are stable.** An entry's `id` is the catalog's join key: routing
consumers, the artifact filename, and every later spec all key on it. A port
never renames an identifier, and never adds or removes one. The seeded
identifier set is pinned in validation, so a rename fails loudly instead of
passing by renaming the artifact file alongside it.

**Status and file presence agree in both directions.** An artifact file exists
if and only if its entry says `shipped`. Adding the file without flipping the
status fails, and so does flipping the status without adding the file. A file in
`templates/` that no entry claims fails as an orphan.

## The routing catalog

`manifest.json`, beside this document, is the machine-readable half of this
contract: the list of templates, the stage and trigger that route each one, and
the closed signal vocabulary.

**Paths in the catalog resolve relative to the catalog's own directory**, never
relative to a repository root. The gallery ships inside the plugin payload and
is read from a version-scoped install cache, where a repository-relative path
would not resolve.

### Top-level shape

```text
{
  "schema_version": "1.0",   // string
  "signals":        [...],   // the five routing vocabulary names
  "export_kinds":   [...],   // the two export vocabulary names
  "templates":      [...]    // one entry object per template
}
```

Exactly four keys. Nothing else belongs at top level. The order above is the
order the file is written in, and it is the order to keep — but it is a
convention, not an obligation: JSON object key order carries no meaning to any
consumer, so validation deliberately checks the key *set* and never the
sequence.

- `schema_version` — the catalog's format version. A consumer that does not
  recognize the value refuses to route and reports the value it read rather
  than interpreting the document; a recognized value at the same major version
  is not a fault. No transformation between versions is defined, so a version
  change requires a coordinated payload release.
- `signals` — the closed routing vocabulary, carrying membership only. This is
  the authoritative list of names. Each name's meaning lives further down.
- `export_kinds` — the closed export vocabulary, carrying membership only, in
  the same shape and for the same reason as `signals`: a flat array of strings
  that each entry's `exports` array draws from. Its two members are `prompt` and
  `markdown`, and their meanings are under the export obligations further down.
  The vocabulary closes in both directions — every kind declared here is carried
  by at least one entry, and every kind an entry carries is declared here.
- `templates` — one entry per planned gallery template.

### Entry shape — nine keys, no more, no fewer

| Key | Type | What it means |
|---|---|---|
| `id` | string | Stable identifier, unique across the catalog, and the artifact's file stem. Filename-safe kebab-case: lowercase letters and digits in hyphen-separated segments, with no leading, trailing, or repeated hyphen, and no path separator, parent-directory segment, whitespace, or dot. |
| `category` | string | Browsing axis — one of `exploration-planning`, `code-review`, `design`, `prototyping`, `diagrams`, `decks`, `research`, `reports`, `editors`. No routing consumer reads it. |
| `title` | string | Non-empty. Names the document the artifact produces. |
| `when_to_use` | string | Non-empty guidance a reader or an agent uses to decide whether this template fits. This is what narrows a browse; signals do not. |
| `stage` | string | `draft-pr`, `final-pr`, or `ad-hoc`. The workflow stage this entry routes at. |
| `trigger` | object | One of the two forms below. Mandatory on every entry. |
| `source` | object | Provenance, in one of the two forms below. |
| `status` | string | `planned` or `shipped`. |
| `exports` | array | The export affordances this artifact must carry, drawn from the `export_kinds` vocabulary. An empty array declares that the artifact is read-only and carries none. See the export obligations below. |

### The artifact path is derived, not stored

There is no path key. A consumer composes the path:

```text
<directory holding manifest.json>/templates/<id>.html
```

Deriving instead of storing makes drift between an identifier and its filename
impossible, and keeps the catalog portable between the repository checkout and
an install cache. It is also why the identifier's format is load-bearing: the
path is built by concatenation, so an identifier carrying a path separator or a
parent-directory segment would compose a path outside `templates/`, and both the
existence check and the orphan sweep would follow it there.

### Source attribution

`source` takes one of two forms, told apart by `origin`:

```json
{ "origin": "upstream", "file": "16-implementation-plan.html" }
```

```json
{ "origin": "repository" }
```

- `file` carries the exact upstream filename, numeric prefix included, and is
  unique across the catalog. Two entries naming one upstream file would put two
  artifacts under a single provenance claim, which per-artifact attribution
  cannot express.
- The upstream repository is named once — here — rather than repeated in every
  entry: `anthropics/html-effectiveness`. Its permission notice is reproduced
  verbatim in `UPSTREAM-NOTICE.md` beside this document.
**The header's labels are exact, and validation compares against them.** Write the
header with these five labels spelled as shown — the check locates each value by its
label, so a reworded label means the value cannot be found and the artifact fails:

```html
<!--
  Upstream repository: anthropics/html-effectiveness
  Upstream file: 16-implementation-plan.html
  License: MIT
  License text: UPSTREAM-NOTICE.md
  Modified derivative: yes — re-skinned with Racecraft brand tokens; not the upstream original
  Copyright (c) 2026 Anthropic PBC
-->
```

Two of those values are checked for **agreement with your catalog entry**, not merely
for presence: the upstream repository, and the upstream file. A header can be perfectly
well formed and still assert the wrong provenance, and a green result on a
presence-only check would read as evidence the provenance was verified. So the file you
name here must be the `file` your entry declares.

- An artifact whose entry declares `origin: "upstream"` carries an attribution
  header as an HTML comment near the top of the file, naming the upstream
  repository and the upstream file it derives from, reproducing the upstream
  copyright line verbatim, giving a license identifier and a link to the full
  license text, and stating plainly that the file is a modified derivative
  rather than the original. The header must **agree with its own entry**: the
  file it names equals that entry's `source.file`, and the repository it names
  is the one above. A header copied from a neighboring artifact is well-formed
  and false at once, and validation fails it.
- An artifact whose entry declares `origin: "repository"` carries no upstream
  attribution element at all — not a copyright line, not a license identifier,
  not an upstream filename.

### The typeface tokens, by name

The kit already applies these to `body` and to `h1`–`h6`, so a port that writes ordinary
headings and paragraphs gets them for free. Name them explicitly only when styling
something the kit does not reach:

| Token | Stack |
|---|---|
| `--rc-font-display` | `'Space Grotesk'`, then `'Trebuchet MS'`, `'Segoe UI'`, `system-ui`, `sans-serif` |
| `--rc-font-body` | `'Geist'`, then `'Helvetica Neue'`, `Arial`, `system-ui`, `sans-serif` |
| `--rc-font-mono` | `'Fira Code'`, then `ui-monospace`, `Menlo`, `Consolas`, `monospace` |

**The heading token is `--rc-font-display`, not `--rc-font-heading`.** The name is worth
stating because the surrounding documentation describes it as the *heading* face, so
`--rc-font-heading` is the natural guess — and an undefined custom property fails
silently, falling through to whatever your own declaration named as a fallback. That is a
mistake made once already while building this feature, which is why the names are written
down here rather than left in the stylesheet.

Every stack ends in a generic family, so text stays readable with the brand faces
unavailable, and hierarchy is carried by level, size, and weight rather than by typeface
identity.

## Routing: stage first, then trigger

Routing resolves in two ordered, independent steps.

1. Keep the entries whose `stage` equals the stage being routed.
2. Of those, keep the entries whose trigger matches the signals present.

A trigger takes exactly one of two forms:

```json
{ "always": true }
```

```json
{ "any_of": ["competing_approaches", "large_diff"] }
```

- `always` matches every time its entry survives step 1.
- `any_of` matches when at least one of the named signals is present. The array
  is never empty; an empty array is a hard failure, which is what makes deleting
  the last signal from an entry fail loudly instead of quietly switching that
  entry off.
- There is no third form, no nesting, no conjunction, no negation, and no
  expression language. Adding one is an amendment to this contract, not a local
  extension.

What the two steps commit you to:

- "Always applies" means always **within its own stage**. It never produces an
  entry at another stage.
- `ad-hoc` entries never enter a stage's candidate set, so their triggers are
  never evaluated by automated routing. They still carry a trigger so every
  entry has one uniform, validated shape.
- `category` is a browsing axis, not a routing input. Nothing routes on it.

## Routing signals

`signals` in the catalog is the authoritative list of member **names**. This
section states what each name **means** and what evidence a consumer reads to
decide the signal is present.

The two are checked against each other: every member of `signals` must be
documented here, and every signal documented here must be a member. Validation
reads the five headings in this section and requires that set to equal the
catalog's array. That check is the one that makes a coordinated rename visible —
renaming a signal in the catalog and in the entry that consumes it leaves every
count and every closure intact, and only new prose here completes the rename.

Signals are names, not computed predicates. This foundation validates that
triggers use recognized forms and recognized names. Deciding whether a signal
holds for a given change belongs to the workflow that emits it, which is why no
evaluator, operator, or threshold lives here.

The vocabulary reserves no slack. A member is added only by recorded amendment
naming the entry that will consume it. Members are not renamed and not removed.

### `competing_approaches`

**Means**: planning weighed more than one viable implementation approach.

**Evidence**: the feature's `research.md`, where a decision records a real
alternative under its "Alternatives considered" note, and the plan's Complexity
Tracking table, whose "Simpler Alternative Rejected Because" column records the
same thing for a justified deviation. Present when at least one alternative
approach was weighed and rejected on the record.

### `brownfield_change`

**Means**: the change modifies existing code rather than adding only new files.

**Evidence**: the plan's `## Declared File Operations` block, whose entries are
each marked `NEW` or `MODIFIED`. Present when at least one entry is `MODIFIED`.

### `self_review_findings`

**Means**: the pre-PR self-review recorded at least one gap.

**Evidence**: the self-review block the workflow log writes after
implementation, mirrored into the PR body's `## Self-Review Findings` region
when the body declares one. Present when that block records a gap — an
edge-case gap, a requirement no task was matched to, a deferral that never
landed in the PR body, or a leftover-scaffolding flag.

### `large_diff`

**Means**: the finished change's size reached the repository's existing warn or
block threshold.

**Evidence**: the repository's reviewability gate run against the finished
change. Present when the gate returns `warn` or `block` on a size dimension —
reviewable lines, production files, or total files. The thresholds belong to
the gate; this document does not restate them, so the two cannot drift apart.

### `operational_flow_change`

**Means**: the change alters a documented multi-step runtime or delivery
process.

**Evidence**: the plan's `## Declared File Operations` block read together with
its declared review surfaces. Present when the change touches a file that
documents or drives a multi-step process — a workflow definition, a runbook, an
install or release procedure — rather than only the code that process runs.

## Export obligations

An artifact is read by a person who is in the middle of doing something. If that
reading produces anything — a choice, an objection, a result — and the artifact
gives them no way to carry it out, the work is stranded in a browser tab and has to
be retyped from memory. **An artifact whose reader produces something MUST end with
an export.** Which kinds it carries is declared in its catalog entry's `exports`
array, not left to the author's judgement, so a reviewer can tell a deliberate
read-only artifact from a forgotten affordance.

The vocabulary is closed. `export_kinds` declares it as data in the catalog, and
the same closure holds as for routing signals: every kind declared is used by at
least one entry, and every kind used is declared.

| Kind | What it produces | Where it goes |
|---|---|---|
| `prompt` | The reader's conclusion phrased as an instruction to a coding agent — the decision and its consequence, not a description of the screen. | Pasted straight into Claude Code or Codex. |
| `markdown` | The same conclusion phrased as a record: what was decided, observed, or configured. | A pull-request comment, or committed to a file. |

The two are not interchangeable, and an artifact that needs both must offer both.
A `prompt` export closes the loop immediately and skips the round trip entirely. A
`markdown` export is the auditable form: it lands in a pull-request comment where
the feedback sweep can read it, classify it, and route it through consensus. Choose
by what the reader is trying to do, never by which is easier to build.

### What an export must contain

- **The reader's conclusion, not the artifact's content.** A `prompt` export from a
  plan review says which phase to reorder and why; it does not restate the plan.
- **Enough context to act on alone.** The person pasting it has left the artifact
  behind. Name the artifact, the spec, and the location the conclusion attaches to.
- **Only what the reader actually produced.** An export that invents a conclusion
  the reader did not reach is worse than no export, because it reads as theirs.
- **Nothing the reader did not see.** Never export inline data the artifact was
  built from but did not display, and never export a value the reader could not
  have inspected.

### The affordance itself

- A single control per kind, labelled with the destination rather than the
  mechanism: "Copy as prompt", "Copy as Markdown". Not "Export" alone.
- It MUST be reachable and operable by keyboard, and it MUST report success in text
  rather than only by colour or animation, per the accessibility obligations below.
- Clipboard access can fail or be refused, especially over `file://`. On failure the
  artifact MUST reveal the text in a selectable field instead, so the reader can copy
  it manually. Silence on failure is a defect: the reader believes they have it.
- The export MUST be derived from the artifact's live state at the moment it is
  invoked, never from a value baked in when the file was written.

### Read-only artifacts

An entry whose `exports` is empty is asserting that its reader produces nothing
durable — an explainer, a diagram, a deck. That is a legitimate and common case, and
an empty array is the way to say it deliberately. What is not legitimate is an
artifact whose reader plainly produces something and whose entry claims otherwise;
that is the defect this declaration exists to make visible.

## Accessibility obligations you inherit

The two canonical blocks carry most of this for you. What follows is the part
that stays yours once they are embedded, plus the rules that decide whether the
blocks keep working after your own markup lands.

### Color pairings: audited, and one that is prohibited

Every foreground/background pairing the kit permits meets WCAG AA — at least
4.5:1 for normal text (1.4.3), and at least 3:1 for large text and for non-text
things that carry meaning, such as borders, icons, chart strokes, and the focus
ring (1.4.11). Large text means at least 24px, or at least 18.66px when bold.

The audit itself lives in `brand-kit.css`, above the start marker: every token
measured against all four surfaces, in both themes, with each ratio written out
unrounded. Look a pairing up there rather than re-deriving it. The table is not
repeated here — there is one audit, and a second copy would only drift from it.

Every foreground clears its floor on every surface in both themes, with one
exception, and that exception is a role statement rather than a contrast defect:

| Prohibited | Measured | Use instead |
|---|---|---|
| `--rc-border-subtle` for any boundary that conveys meaning, either theme | 1.13–1.78 | `--rc-border-strong` |

`--rc-border-subtle` is deliberately faint. It is not a failure to be fixed, and
raising its value would defeat its purpose; it simply must never be the thing
carrying a meaning.

For red body copy use `--rc-danger-text` in either theme; `--rc-brand-red` is
audited for large text and non-text use only. Both brand primitives — brand red
and the accent — carry **no** prohibition: brand red clears 3:1 on all four
surfaces in both themes (4.19–4.99 light, 3.11–3.69 dark), and the accent does
the same (3.16–3.76 light, 4.13–4.90 dark).

**Why a prohibition rather than a corrected value.** The kit distinguishes two
token classes at their point of definition. A **functional token** exists to
serve a stated purpose, so when it misses its floor its value is corrected. A
**brand primitive** is not re-valued to resolve a contrast failure; the need it
cannot serve is routed to a functional sibling named beside it, which is why
`--rc-brand-red` keeps its value and `--rc-danger-text` exists. Prohibitions are
written as narrowly as the measurement supports — one pairing in one theme,
never a blanket ban on a token.

There is a third resolution, preferred over both when it is available: correct
the **surface**. Brand red was once prohibited on the dark raised surface, where
it measured 2.94 against a blue-grey `#1F2937` borrowed from the upstream
navigation background. Re-valuing that surface to a neutral `#242424` lifted
every dark foreground at once — brand red to 3.11, the meaningful-boundary token
to 3.21 — instead of trading one token against another, and the prohibition
ceased to exist. Prefer fixing the surface when one surface is what forces the
miss; fall back to a prohibition only when the surface itself is fixed.

A pairing that neither meets its floor nor carries a prohibition naming its
replacement is a defect in the kit. Report it rather than working around it
locally. Colors you introduce outside the marked block are outside the audit:
reuse a token, or measure the new pairing the same way before relying on it.

### Color is never the only carrier of meaning

Wherever red — or any color — marks a status, an action, or a distinction, that
meaning is also available without color: as text, a shape, a glyph, or a
position (WCAG 1.4.1, Level A). It has to survive for a reader who cannot
perceive the hue, and in a monochrome print or screenshot.

This is a separate rule from the two it gets confused with, and neither of them
discharges it:

- The kit's punctuation-level reservation for brand red governs **how much** red
  is used and at what sizes.
- The contrast audit governs **legibility**. A red that clears 7:1 still fails
  this rule if the color is the only thing saying "this one is the problem".

### The theme control

The control ships inside the head block and is created from there at run time.
You do not author it, replace it, or wrap it. Embedding the block is what gives
your artifact a control that:

- is reachable in the normal focus order and activatable by keyboard alone
  (WCAG 2.1.1, Level A) — so add no positive `tabindex` anywhere in your
  template, and trap no focus;
- is a real `button` carrying a stable, human-readable name that does not depend
  on an icon glyph, plus a state that says which theme is active and **changes**
  between the two positions (WCAG 4.1.2, Level A);
- keeps working when the browser refuses storage for a local file: the switch
  still applies for the session and nothing is reported as an error. Persistence
  is what degrades there, never the control.

The stored theme value is untrusted input. The block validates it against the
two theme names on read, applies a literal from that set rather than the string
it read back, and discards anything else in favor of the operating-system
signal. If your template needs to know the current theme, read the `data-theme`
attribute on the root element — never read storage yourself, and never place a
stored value into markup, into a selector, or into any other executable
position. A second reader re-opens the hole the block closes.

`data-theme` is always present, on both paths: the block writes the resolved
theme during head parsing whether or not a reader has stored an override, so
there is no state in which your template reads it and finds nothing. While no
override is stored the block follows the operating system, so a reader who
changes their system theme after load gets the attribute, the rendering, and the
control's reported state all moving together.

### The brand mark

The block also carries the Racecraft mark, and mounting it is **opt-in**. Provide
an empty element with a `data-rc-brand-mark` attribute wherever the mark belongs,
and the block fills it:

```html
<span data-rc-brand-mark></span>
```

Leave the attribute off and no artwork is mounted — an artifact with no sensible
place for a mark simply does not provide one, and that is the common case rather
than an omission. Provide the attribute on an element that already has a child
and the block leaves it alone, so your own artwork is never replaced.

Do not write the `rc-brand-mark` class yourself. It is the kit's sizing rule and
the block sets it on the artwork it mounts; setting it on an element of your own
gets the sizing with no mark in it. The artwork's neutral fill is `currentColor`,
so it follows the theme — set `color` on the container to change it. Brand red
inside the mark is a primitive and is identical in both themes.

### Focus and motion

Every interactive element in your artifact carries the kit's focus-visible
treatment (WCAG 2.4.7, Level AA). Suppressing the indicator without an
equivalent replacement is prohibited — a removed outline with nothing in its
place is a failure, not a style choice. The indicator's own contrast is audited
like any other non-text pairing; it uses `--rc-link` and clears 3:1 on every
surface in both themes.

A reader who asks for reduced motion gets none: no animation, no transition, and
no smooth scrolling, including the cross-theme color transition. The kit's rule
covers what the kit declares. Motion your template adds is yours to suppress
under the same preference.

### Typefaces

The font request in the head block carries the parameter that produces swap
behavior. Do not drop it and do not tidy the request: without that parameter the
provider serves a blocking default, and there is then a period during which text
is rendered invisibly while the face loads. Validation fails a request missing
it.

Three roles — display, body, and mono — each declare a fallback stack naming a
different concrete face, so the three stay distinguishable when the brand faces
are unavailable. The brand face leads each stack, because a stack is a
first-available list and a system face placed first shadows the brand one.

Do not carry hierarchy on typeface identity. Heading rank rides on semantic
heading level, size, and weight, which is what keeps an offline rendering
degraded in appearance and never in structure.

## Security obligations you inherit

A gallery artifact is an executable document: it carries inline behavior and a
human opens it straight from a filesystem. Two controls keep that honest, and
they are not equal — the prohibitions below are the primary control, and the
declared policy is the backstop.

### Constructs no artifact may contain

| Prohibited | Why |
|---|---|
| A `base` element | It redefines what every relative reference in the document resolves to. All-relative references plus one base element pointing elsewhere leaves no foreign host in any scanned position while the browser loads everything from that host — the one construct that defeats the external-reference scan completely. A single-file artifact has no use for it. |
| A reference beginning with two slashes and no scheme | It resolves against the document's own scheme, which here is the local-file scheme rather than a network one, and it names a foreign host in a form no pattern keyed on an explicit scheme matches. |
| An `on*` event-handler attribute | Executable content in a position no resource-load scan reads. It can hold a network destination while the element's own source attribute stays innocuous. |
| A `srcdoc` attribute | A complete nested document, carrying its own behavior, inside an attribute value. |
| A `form` element with a submission target | Sends rather than fetches. |
| A `ping` attribute on any element | Sends rather than fetches, and it rides the anchor element the navigation exemption waves through — so the one element deliberately exempted would otherwise carry a pure network beacon. |

None of these is a judgment call: validation fails an artifact carrying any of
them and names it. If the template you are porting uses one, the port drops it —
a construct on this list is never ported and never reintroduced.

These prohibitions do not touch the attribution header described under
**Source attribution** above: it is an HTML comment, and comments and visible
text are not resource-loading positions.

**A script body is scanned in full, and so is markup you build as a string.**
Every string literal inside a `script` element is read: a static
`import … from "…"`, its bare and `export … from` forms, an import map, a URL
bound to a variable, and an assignment such as `img.src = "…"` are all
references, not just an argument written inside a recognised call. And markup
assigned to a string — the `innerHTML` case — is parsed as markup, so an
attribute there is judged exactly as one written into the document, and a
prohibited construct there is prohibited too. Building an element in script is
not a way around this list. XML namespace constants are the one exemption: they
are compared as strings and never fetched.

### Embedding an asset: `data:` URIs

The single-file rule leaves exactly one way to carry a raster, an encoded vector,
or a font: a `data:` URI. That is **permitted** in any resource position, and it
does not count as an external reference, because the bytes are in the document and
nothing is fetched.

The allowance is bounded by media type, not granted to the scheme:

| Media type | |
|---|---|
| `image/…` (including `image/svg+xml`) | Permitted |
| `font/…` | Permitted |
| Anything else — `text/html`, a script type, an unlabelled `data:` | **Refused** |

`data:text/html` is a script execution context, so it is not an asset however it
is encoded; the policy declaration's `object-src 'none'` and `frame-src 'none'`
close the positions where an SVG could reach one. Prefer a plain relative path
when the artifact is not required to be single-file — an inline asset costs bytes
in every copy — but never reach for a remote host to avoid the size.

### The policy declaration in the head block

Every artifact carries an in-document policy declaration, and it ships inside
the canonical head block — embedding the block is what satisfies this. Do not
write your own, and do not move it.

- **What it restricts**: base URI, form submission, embedded objects, nested
  documents, and outbound connections. Artifacts run with no server, so no
  response header can reach them and an in-document declaration is the only
  policy channel available.
- **It names `'none'` for each restricted directive, never `'self'`.** A
  document opened from a filesystem has an implementation-defined and usually
  opaque origin, so `'self'` resolves inconsistently between browsers. Explicit
  scheme tokens are permitted where an artifact genuinely needs one.
- **It names none of the three directives that in-document delivery strips** —
  reporting endpoint, frame ancestry, and sandbox. They are discarded silently
  when delivered this way, so naming one marks an author relying on protection
  that was removed.
- **It sits as a direct child of the head element with nothing content-bearing
  before it**; only a character-encoding declaration may precede it. Anywhere
  else the whole policy is discarded at parse, and after content it does not
  cover the content that came first.

Every one of those conditions is validated, because the realistic failure here
is an authoring mistake rather than a browser refusing the policy — and each
mistake leaves an artifact that reads as protected and is not, with no visible
symptom beyond a console message at most.

The directive set is deliberately narrow. An in-document declaration cannot
carry framing or sandbox restrictions at all, and the artifacts' own inline
behavior means it cannot meaningfully restrict script. The set is chosen so that
nothing the gallery legitimately does is restricted by it.

**Why this is the secondary control.** A prohibition enforced by validation
holds in every consumer that ever opens the file — preview panes, webviews,
converters, diff viewers — because the offending construct is simply not in the
document. A declared policy takes effect only where a full browser engine parses
the document. The prohibitions guarantee the property; the declaration covers
the residue.

### Artifacts generated from repository content

**Read this part if your spec generates artifacts rather than porting them.**
The external-reference scan reads the gallery's own source files in this
repository. It does not reach an artifact an authoring agent writes at run time,
and nothing else will either. Whatever safety a generated artifact has is what
its generator put there, so the obligation below is not discharged by anything
upstream of you.

Values drawn from repository or pull-request material — a title, a branch name,
a self-review finding, a commit message, diff content, a path — are **untrusted
input to an executable document**. That they came from your own repository
changes nothing: none of it was written to be safe inside a file that carries
inline behavior.

Four contexts an interpolated value may **never** enter:

- a script body,
- a style body,
- a URL-valued attribute,
- an event-handler attribute (prohibited outright in any case).

There is no escaping rule for those four; the value goes somewhere else. Put it
in a text position — a text node, or a plain data attribute — and have the
inline behavior read it back from the document. Everywhere else, escape it for
the context it actually lands in.

The flat prohibition is deliberate, and it is both simpler and stronger than a
per-context escaping rule. The common failure is not missing escaping — it is
escaping for the wrong context. A value escaped for HTML text and then written
into a script body is not protected at all, and it looks handled.

The prohibitions and the declared policy above apply to a generated artifact
exactly as they do to a ported one, and a generator satisfies them when it
writes the file, because nothing checks it afterwards.

## One authoring rule that keeps the shipped copies honest

No gallery file may contain a relative reference into a skills directory of the
form the Codex payload build rewrites: a run of parent-directory segments ending
in `../skills/` or `../codex-skills/`, followed by a path to a file. Refer to a
skill by name in prose instead. Naming the two prefixes in backticks, as this
paragraph does, is not itself such a reference — the rewriter needs a path
character after the trailing slash, and a closing backtick is not one.

The reason is mechanical. The Codex build runs a text rewriter over every file
it copies and writes the file back only when the substitution changed something.
A gallery file containing no such reference is therefore copied unchanged, and
that is what lets validation require every shipped copy to be byte-identical to
its source on both platforms. One such reference in one file would break that
equality and would surface as a stale payload rather than at its real cause.

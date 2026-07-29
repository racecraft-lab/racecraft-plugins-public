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
  "schema_version": "1.0",   // string, first key
  "signals":        [...],   // the five vocabulary names
  "templates":      [...]    // one entry object per template
}
```

Exactly three keys, in that order. Nothing else belongs at top level.

- `schema_version` — the catalog's format version. A consumer that does not
  recognize the value refuses to route and reports the value it read rather
  than interpreting the document; a recognized value at the same major version
  is not a fault. No transformation between versions is defined, so a version
  change requires a coordinated payload release.
- `signals` — the closed routing vocabulary, carrying membership only. This is
  the authoritative list of names. Each name's meaning lives further down.
- `templates` — one entry per planned gallery template.

### Entry shape — eight keys, no more, no fewer

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

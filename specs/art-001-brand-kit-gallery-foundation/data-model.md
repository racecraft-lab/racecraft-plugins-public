# Data Model: Artifact Brand Kit & Gallery Foundation

**Feature**: ART-001 | **Date**: 2026-07-28

All paths in this document are relative to the repository root. Paths written
into `manifest.json` itself are relative to the manifest's own directory.

## Entity 1 — Routing Catalog (`manifest.json`)

Top-level object with **exactly three keys, in this order** (FR-007, Session 2):

| Key | Type | Value |
|-----|------|-------|
| `schema_version` | string | `"1.0"` |
| `signals` | array of string | The five vocabulary members, in FR-015 order |
| `templates` | array of object | 21 entries |

Nothing else is legal at top level — no `$schema` pointer, no `description`.

```json
{
  "schema_version": "1.0",
  "signals": [
    "competing_approaches",
    "brownfield_change",
    "self_review_findings",
    "large_diff",
    "operational_flow_change"
  ],
  "templates": [ /* 21 entries */ ]
}
```

## Entity 2 — Gallery Template Entry

**Exactly eight keys.** No ninth key. **No stored path** — the artifact resolves
as `templates/<id>.html` relative to the manifest's own directory (FR-007,
FR-009).

Entries are authored in FR-007's declaration order. That ordering is an
**authoring convention for readability, not a validated constraint**: check B4
asserts the key *set*, since JSON object key order carries no meaning to any
consumer. Stating it as binding while enforcing only the set would leave a rule no
reviewer or check ever applies.

| Key | Type | Rule |
|-----|------|------|
| `id` | string | unique across the catalog; **filename-safe kebab-case** — lowercase alphanumerics in hyphen-separated segments, no leading/trailing/repeated hyphen, no path separator, `..`, whitespace, or dot |
| `category` | string | one of the nine-member enum below |
| `title` | string | non-empty string; names the document |
| `when_to_use` | string | non-empty string; guidance prose |
| `stage` | string | `draft-pr` \| `final-pr` \| `ad-hoc` |
| `trigger` | object | one of the two forms below |
| `source` | object | one of the two forms below; `origin` is a closed two-member set |
| `status` | string | `planned` \| `shipped`; the artifact exists **iff** `shipped` |

**Why `id` is validated for form rather than against the file stem.** Earlier
revisions required the identifier to "equal the artifact file stem". Once the path
is derived (Session 2) that is true by construction — the stem *is* the id — so it
can never fail. What the derivation actually depends on is the identifier's
character set: the path is composed by concatenation, so an id carrying a
separator or a `..` segment composes a path outside `templates/`, which both the
existence and orphan checks would follow. The format rule is the real constraint.

### Category enum (nine members)

Adopted verbatim from the upstream gallery's own index taxonomy, kebab-cased.
Every one of the 20 ported entries **inherits** its upstream group — no category
is invented for a ported entry.

| Enum member | Upstream index heading |
|-------------|------------------------|
| `exploration-planning` | "Exploration & Planning" |
| `code-review` | "Code Review & Understanding" |
| `design` | "Design" |
| `prototyping` | "Prototyping" |
| `diagrams` | "Illustrations & Diagrams" |
| `decks` | "Decks" |
| `research` | "Research & Learning" |
| `reports` | "Reports" |
| `editors` | "Custom Editing Interfaces" |

`uat-walkthrough` (repository-authored) takes `editors`; no tenth member is
minted (Session 2).

### Trigger — two forms only (FR-008, FR-016)

```json
{ "always": true }
```

```json
{ "any_of": ["competing_approaches"] }
```

- `any_of` MUST be non-empty. An empty array is a hard validation failure — that
  is what makes deleting the last signal fail loudly instead of silently
  disabling routing.
- No nesting, no conjunction, no negation, no third form.
- The trigger field is mandatory on **every** entry including `ad-hoc` ones, so
  all 21 entries carry one uniform validated shape. Ad-hoc triggers are never
  evaluated, because the stage filter runs first and excludes them.

### Source — two forms, discriminated by `origin` (FR-020)

```json
{ "origin": "upstream", "file": "16-implementation-plan.html" }
```

```json
{ "origin": "repository" }
```

`file` carries the **exact** upstream filename so the numeric prefix survives, and
is **unique across the catalog** — two entries naming one upstream file would have
two artifacts claiming the same provenance, which FR-020's per-artifact
attribution cannot express. The upstream repository is named once in
`SPA-CONTRACT.md`, not repeated across 20 entries.

`origin` is the discriminator that makes the FR-020 attribution check mechanical:
an `upstream` entry's artifact must carry the attribution header; a `repository`
entry's artifact must not carry an upstream copyright line. It is a **closed
two-member set**, and the attribution checks are exhaustive over it — an entry
matching neither member fails rather than silently skipping both branches, which
is the difference between a gate that passed and a gate that never ran.

## Entity 3 — Routing Signal Vocabulary (five members)

Declared as data under the top-level `signals` key, which is the single
authority for membership (FR-017). Meanings live in `SPA-CONTRACT.md`.

| Signal | Meaning | Consuming entry |
|--------|---------|-----------------|
| `competing_approaches` | Planning weighed more than one viable implementation approach | `code-approaches` |
| `brownfield_change` | The change modifies existing code rather than adding only new files | `module-map` |
| `self_review_findings` | The pre-PR self-review recorded at least one gap | `annotated-diff` |
| `large_diff` | The finished change's size reached the repository's existing warn or block threshold | `annotated-diff` |
| `operational_flow_change` | The change alters a documented multi-step runtime or delivery process | `flowchart` |

Closure holds in **both** directions: no entry names a signal outside this set,
and every member is consumed by at least one entry.

## Seeded catalog — all 21 entries

Stage/trigger assignments are fixed by Clarifications Session 1: 4 staged
always-applies, 4 staged conditional, 13 ad-hoc always-applies.

| # | `id` | `category` | `stage` | `trigger` | `source.origin` | `source.file` | Ships in |
|---|------|-----------|---------|-----------|------------------|----------------|----------|
| 1 | `implementation-plan` | `exploration-planning` | `draft-pr` | always | upstream | `16-implementation-plan.html` | ART-002 |
| 2 | `spec-explainer` | `research` | `draft-pr` | always | upstream | `14-research-feature-explainer.html` | ART-002 |
| 3 | `code-approaches` | `exploration-planning` | `draft-pr` | any_of `competing_approaches` | upstream | `01-exploration-code-approaches.html` | ART-002 |
| 4 | `module-map` | `code-review` | `draft-pr` | any_of `brownfield_change` | upstream | `04-code-understanding.html` | ART-002 |
| 5 | `pr-writeup` | `code-review` | `final-pr` | always | upstream | `17-pr-writeup.html` | ART-003 |
| 6 | `annotated-diff` | `code-review` | `final-pr` | any_of `self_review_findings`, `large_diff` | upstream | `03-code-review-pr.html` | ART-003 |
| 7 | `flowchart` | `diagrams` | `final-pr` | any_of `operational_flow_change` | upstream | `13-flowchart-diagram.html` | ART-003 |
| 8 | `uat-walkthrough` | `editors` | `final-pr` | always | repository | — | ART-009 |
| 9 | `visual-designs` | `exploration-planning` | `ad-hoc` | always | upstream | `02-exploration-visual-designs.html` | ART-004 |
| 10 | `design-system` | `design` | `ad-hoc` | always | upstream | `05-design-system.html` | ART-004 |
| 11 | `component-variants` | `design` | `ad-hoc` | always | upstream | `06-component-variants.html` | ART-004 |
| 12 | `animation-prototype` | `prototyping` | `ad-hoc` | always | upstream | `07-prototype-animation.html` | ART-004 |
| 13 | `interaction-prototype` | `prototyping` | `ad-hoc` | always | upstream | `08-prototype-interaction.html` | ART-004 |
| 14 | `svg-illustrations` | `diagrams` | `ad-hoc` | always | upstream | `10-svg-illustrations.html` | ART-004 |
| 15 | `slide-deck` | `decks` | `ad-hoc` | always | upstream | `09-slide-deck.html` | ART-005 |
| 16 | `concept-explainer` | `research` | `ad-hoc` | always | upstream | `15-research-concept-explainer.html` | ART-005 |
| 17 | `status-report` | `reports` | `ad-hoc` | always | upstream | `11-status-report.html` | ART-005 |
| 18 | `incident-report` | `reports` | `ad-hoc` | always | upstream | `12-incident-report.html` | ART-005 |
| 19 | `triage-board` | `editors` | `ad-hoc` | always | upstream | `18-editor-triage-board.html` | ART-005 |
| 20 | `feature-flags` | `editors` | `ad-hoc` | always | upstream | `19-editor-feature-flags.html` | ART-005 |
| 21 | `prompt-tuner` | `editors` | `ad-hoc` | always | upstream | `20-editor-prompt-tuner.html` | ART-005 |

**All 21 entries ship with `status: "planned"`.** ART-001 ports no template, so
no artifact file exists yet and no existence check fires. Each port spec flips
exactly one value from `planned` to `shipped` (SC-004).

Counts that must hold, and do — each re-derived from the table above rather than
carried forward:

- 21 entries total; 20 `origin: upstream` + 1 `origin: repository`
- 4 `draft-pr` + 4 `final-pr` + 13 `ad-hoc`
- 4 staged always-applies (#1, #2, #5, #8) + 4 staged conditional (#3, #4, #6, #7);
  all 13 ad-hoc entries always-applies
- upstream split 4 draft-PR / 3 final-PR / 6 design-and-prototyping / 7
  knowledge-report-editor, matching FR-007. The overall `final-pr` count is 4 while
  FR-007's upstream count is 3, because `uat-walkthrough` is the one
  repository-authored entry and it is staged `final-pr`
- every one of the five signals consumed at least once, and no trigger naming a
  signal outside the five
- all 21 ids unique and filename-safe kebab-case
- all nine category members exercised; none unused
- the 20 `source.file` values distinct, carrying numeric prefixes `01`–`20`
  exactly once each

**What this list does and does not cover.** These are the counts and set
properties the specification fixes, and each is asserted by a check group — the
enum and uniqueness rules by group B, the signal closure by group C. It is not a
statement that no other property of the seed matters; anything absent here is
unasserted, and adding an invariant means adding both a row here and a check.

## Entity 4 — Brand Token Set (`brand-kit.css`)

Canonical file delimited by `/* BRAND-KIT:START */` … `/* BRAND-KIT:END */`.
Everything inside the markers is embedded verbatim into each artifact's
`<style>`. Above the start marker sits the provenance header (FR-012) and the
audited contrast table; those are **outside** the compared region so the header
can carry file-specific commentary without breaking the byte-compare.

Token families inside the block:

- `--rc-surface`, `--rc-surface-raised`, `--rc-surface-sunken`,
  `--rc-surface-muted` — the 70% warm-neutral dominant family
- `--rc-border-subtle` (decorative), `--rc-border-strong` (meaningful non-text,
  audited to 3:1)
- `--rc-text`, `--rc-text-muted`, `--rc-link`
- `--rc-accent` (20% blue, large-text and non-text only),
  `--rc-brand-red` (10% punctuation-level emphasis, non-text and large text, and
  never the sole carrier of meaning per FR-021),
  `--rc-danger-text` (the AA-body-safe red for red body copy)
- `--rc-font-display`, `--rc-font-body`, `--rc-font-mono` — brand face first,
  fallback after. The display and body brand faces are both sans-serif, so their
  fallback stacks name **different** concrete faces rather than both resolving to
  the same system face (FR-024). The stacks are a preference list — first
  *available* face wins — so the brand face must lead or the always-present
  system face shadows it, which is the reasoning already recorded in
  `docs-site/src/styles/brand.css`.
- focus-visible treatment (FR-023) — applied to every interactive element, using
  `--rc-link`, and never suppressed without an equivalent replacement
- reduced-motion handling (FR-023) — under `@media (prefers-reduced-motion:
  reduce)`, animation, transition, and smooth-scroll behavior are reduced to
  effectively instant, following the pattern already used in
  `docs-site/src/styles/brand.css`. This covers the cross-theme color
  transition, which is the shared kit's most likely animation.

**Offline hierarchy.** Even with distinct fallback stacks, the substituted faces
may be visually closer to each other than the brand faces are. The kit therefore
does not rely on typeface identity to express hierarchy: heading rank is carried
by semantic heading level, size, and weight. This is what makes SC-006's "the
only observable difference is typeface substitution" true rather than
aspirational — the offline rendering degrades in appearance, never in structure.

Dark values are supplied under `@media (prefers-color-scheme: dark)` and under
`:root[data-theme="dark"]`, with `:root[data-theme="light"]` forcing light back
on.

**`color-scheme` must be set per override, not once.** Declaring
`color-scheme: light dark` on `:root` alone is **not** sufficient: that
declaration says the page supports both schemes and lets the browser resolve
which one to use from the *operating-system* preference. It does not observe the
page's own `data-theme` attribute. A reviewer on a dark OS who forces light
would get light page tokens and dark native form controls and scrollbars. The
kit therefore also sets `color-scheme: dark` under `:root[data-theme="dark"]`
and `color-scheme: light` under `:root[data-theme="light"]`, so the browser's own
surfaces follow the chosen theme in both directions (FR-004).

### Audited AA contrast pairings

Computed with the WCAG 2.x relative-luminance formula, per theme independently
(FR-005, SC-007). Ratios are stated in the `brand-kit.css` comment block so a
template port can verify a pairing without re-deriving it.

**Light theme** — surfaces `#F7F6F4` / `#FFFFFF` / `#F1F0EC` / `#E8E5DF`

Every foreground is measured against **all four** surfaces, in both themes
(FR-005). A single representative surface is not an audit — the two failures
found late in this feature were both hiding in an unmeasured surface.

| Foreground | Ratio range across the four surfaces | Verdict |
|------------|--------------------------------------|---------|
| `--rc-text` `#111827` | 14.11 – 17.74 | AA body |
| `--rc-text-muted` `#4B5563` | 6.01 – 7.56 | AA body |
| `--rc-link` `#2A6A99` | 4.61 – 5.80 | AA body |
| `--rc-accent` `#3C89C6` | 3.30 – 3.76 on surface/raised/sunken | AA large + non-text; **prohibited** on muted (2.99) |
| `--rc-brand-red` `#dc143c` | 3.97 – 4.99 | AA large + non-text |
| `--rc-danger-text` `#C4102F` | 4.82 – 6.07 | AA body |
| `--rc-border-strong` `#847F72` | 3.18 – 3.99 | AA non-text on all four |
| `--rc-border-subtle` `#E0DED9` | 1.07 – 1.34 | decorative only — **prohibited** for meaning |

**Dark theme** — surfaces `#1A1A1A` / `#242424` / `#141414` / `#1E1E1E`

All four are pure neutrals. An earlier raised value of `#1F2937` was a blue-grey
borrowed from the upstream navigation background; see rule 4.

| Foreground | Ratio range across the four surfaces | Verdict |
|------------|--------------------------------------|---------|
| `--rc-text` `#E6E6E6` | 12.44 – 14.76 | AA body |
| `--rc-text-muted` `#9CA3AF` | 6.11 – 7.26 | AA body |
| `--rc-link` `#7CB3DD` | 6.91 – 8.20 | AA body |
| `--rc-accent` `#3C89C6` | 4.13 – 4.90 | AA large + non-text |
| `--rc-brand-red` `#dc143c` | 3.11 – 3.69 | AA large + non-text on all four |
| `--rc-danger-text` `#FF6B85` | 5.69 – 6.75 | AA body |
| `--rc-border-strong` `#6B7280` | 3.21 – 3.81 | AA non-text on all four; 3.21 on raised is the binding minimum |
| `--rc-border-subtle` `#404040` | 1.50 – 1.78 | decorative only — **prohibited** for meaning |

Four constraints fall out of the audit and are recorded as rules in the CSS
comment — two prohibitions and two corrections. Per FR-005 these are the
complete set of pairings that do not meet their threshold; every one names its
replacement, and no failing pairing is left without a rule.

1. **`--rc-accent` is never paired with `--rc-surface-muted` in light theme** —
   `#3C89C6` on `#E8E5DF` measures 2.99, just under the 3:1 non-text floor. Use
   `--rc-link` there instead.
2. **`--rc-border-subtle` is decorative only** — 1.07–1.34 (light) and 1.50–1.78
   (dark) against the surfaces. Any boundary that conveys meaning (form control
   edges, focus ring) MUST use `--rc-border-strong`.
3. **`--rc-border-strong` light is `#847F72`, not `#8A8578`** — the original
   value measured 2.93 against `--rc-surface-muted`, below the 3:1 floor, which
   the first audit did not surface because it recorded only the single
   `--rc-surface` pairing (3.41). Because this token exists precisely to carry
   boundaries that convey meaning, prohibiting it on a surface would be a trap;
   the value is darkened one step instead so it clears 3:1 on all four light
   surfaces (3.18–3.99). Dark `#6B7280` needed no change (3.21–3.81).
4. **`--rc-surface-raised` dark is `#242424`, not `#1F2937`** — the original was
   a blue-grey taken from the upstream navigation and sidebar background, a role
   it was chosen for and this one is not. It was the only non-neutral among the
   four dark surfaces and the only surface in either theme that forced a pairing
   below its floor: `--rc-brand-red` measured 2.94 against it and
   `--rc-border-strong` 3.04, the tightest ratio in the kit. Correcting the
   surface lifts every dark foreground simultaneously — brand red to 3.11,
   border-strong to 3.21, body text to 12.44 — with no pairing regressing
   anywhere, and it removed the only prohibition that had applied to a brand
   primitive. Elevation still reads: `#242424` stays lighter than
   `--rc-surface` `#1A1A1A` and `--rc-surface-muted` `#1E1E1E`.

Rules 3 and 4 are corrections and rules 1 and 2 are prohibitions. That ordering
is the FR-025 rule in practice: a functional token that misses its floor is
re-valued, a surface that forces the miss is corrected, and a brand primitive is
never re-valued — its unmet need routes to a functional sibling. That third case
now has no instance, because rule 4 removed the only one.

Focus ring uses `--rc-link` in both themes and clears the 3:1 non-text floor on
every surface it can appear on: 5.37 / 5.80 / 5.09 / 4.61 light, 7.75 / 6.91 /
8.20 / 7.42 dark (FR-023).

All ratios above were recomputed from the token hex values with the WCAG 2.x
relative-luminance and contrast-ratio formulas and are stated unrounded to two
decimals. None is rounded up to a threshold.

## Entity 5 — Theme Toggle Snippet (`theme-toggle.html`)

Canonical file delimited by `<!-- GALLERY-HEAD:START -->` …
`<!-- GALLERY-HEAD:END -->`, byte-compared by the same mechanism as the CSS
block (FR-003, FR-006).

The marked region is a **head** region and stays entirely within `<head>`: it
carries the FR-027 policy declaration, the font request, the pre-first-paint theme
application, the `color-scheme` selection, and the inline behavior. It therefore
**creates the theme control at run time rather than containing markup for it**.
That is forced, not stylistic — J7 and J8 require the policy declaration to be a
direct child of `<head>` with no content-bearing element before it, while I4
requires the control's accessible name and state to live inside the same marked
region. A literal `button` in the region would satisfy neither: `<head>` admits
only metadata content, so a parser meeting a `button` there closes the head and
opens the body, silently relocating the region and voiding J7 for every artifact
that embeds it. The consequence is deliberate and consistent with FR-004 — with
scripting unavailable the reader still gets their operating-system theme through
the media query and loses only the ability to override it, the same degradation the
storage-unavailable path already accepts.

The region carries:

- Reads a stored override, falling back to the OS signal.
- Applies `data-theme` to `:root` **before first paint**, so a dark-OS reviewer
  sees no light flash (FR-004, SC-005).
- Sets the matching `color-scheme` for the chosen theme so the browser's own
  surfaces follow the override rather than the OS preference (FR-004).
- Writes the override inside `try` / `catch`; when a browser refuses storage for
  `file://` documents the override still applies for the session and nothing is
  reported as an error (FR-004, Story 3 scenario 3).
- **Validates the stored value against the closed set of theme names on read**, and
  applies a literal from that set rather than the string it read back. Anything
  else is discarded and the operating-system signal is used as though no override
  existed. The value never reaches a markup, selector, or other executable context.
  The storage key is namespaced to this gallery (FR-004).

**Why the storage path is specified here rather than left to implementation.**
Local storage for local files is not partitioned per file in every browser, so the
value read back was not necessarily written by a gallery artifact. Independent of
that, a persisted value is attacker-influenceable input to a snippet embedded
**verbatim into all 21 artifacts** — the same propagation argument that governs the
accessibility obligations below. The `try` / `catch` above must not be what
satisfies the validation: a `catch` written only to keep an error from surfacing
would swallow it. Checks I5 and I6 assert both the closed-set validation and the
namespaced key sit **inside the copied region**, since either sitting above the
start marker would look correct here and reach no artifact.

### Accessibility obligations fixed in this snippet (FR-022)

These are properties of the **canonical snippet**, not of any port. The snippet
is embedded verbatim into all 21 artifacts, so each of these is decided once and
cannot be corrected per template — which is why they are specified here rather
than left to the ports.

| Obligation | Requirement | Criterion |
|---|---|---|
| Keyboard reachable | In the normal focus order, no positive `tabindex` | 2.1.1 (A) |
| Keyboard activatable | Activates by keyboard without a pointer | 2.1.1 (A) |
| Native semantics | Created as a real `button` element, so role and activation come from the platform rather than being reconstructed on a generic element | 4.1.2 (A) |
| Accessible name | A stable, human-readable name that does not depend on an icon glyph alone | 4.1.2 (A) |
| State exposed | The active theme is programmatically determinable, not signalled by icon or color alone | 4.1.2 (A), 1.4.1 (A) |
| Focus visible | Carries the kit's focus-visible treatment | 2.4.7 (AA) |

The state must be readable by assistive technology in **both** positions. A
control that toggles appearance but reports the same state in either theme
satisfies none of this, and neither does one whose only state cue is a sun or
moon glyph — that is a use-of-color/graphic-only signal under FR-021.

## Entity 6 — Provenance Record

Lives in the `brand-kit.css` header, above the start marker (FR-012):

- `racecraft-lab/racecraft` `docs/brand/*` at commit
  `30237cceaeb398e9fc08d8570714f24ff661c867`, captured 2026-07-04 — cited by
  repository name, path, SHA, and date only. **No prose reproduced.**
- `docs-site/src/styles/brand.css` — the public in-repo token source the palette
  is reconciled against.

No automated cross-repository comparison exists; re-sync is a deliberate human
edit.

## Entity 7 — Upstream Permission Notice

One file reproducing the upstream MIT permission notice verbatim (FR-020),
which every ported artifact's attribution header points at.

- Upstream: `anthropics/html-effectiveness`, MIT, `Copyright (c) 2026 Anthropic PBC`
- **Filename MUST NOT be `LICENSE`.** The payload builder special-cases the
  exact relative path `LICENSE` and maps it to this repository's own root
  license. The chosen name is `UPSTREAM-NOTICE.md`.

## Entity 8 — Gallery Artifact (contract only in ART-001)

ART-001 ships **zero** artifacts. The entity is defined here because the
validation and the contract that ART-002…005 inherit are ART-001's deliverable:
a single self-contained file that embeds both marked blocks verbatim, renders
from `file://`, loads nothing external except the two font hosts, and — when
`source.origin` is `upstream` — carries the FR-020 attribution header whose named
upstream file and repository **equal** those its catalog entry declares (G6/G7);
presence of the elements is not the same as agreement with the entry.

**Prohibited constructs (FR-027, check group J).** An artifact carries no `base`
element, no scheme-relative reference, no event-handler attribute, no `srcdoc`, no
form target, and no `ping` attribute; and it carries the in-document policy
declaration restricting base URI, form submission, embedded objects, nested
documents, and outbound connections. The `base` prohibition is the one that is not
merely defense in depth: a base element carries no disallowed host and instead
redefines what every relative reference resolves to, so no host-based check can
see it and an artifact with all-relative references plus one base tag would pass
the entire external-reference scan while loading from an attacker's host.

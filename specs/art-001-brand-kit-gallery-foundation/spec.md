# Feature Specification: Artifact Brand Kit & Gallery Foundation

**Feature Branch**: `art-001-brand-kit-gallery-foundation`

**Created**: 2026-07-28

**Status**: Draft

**Input**: User description: "SpecKit-Pro is adding a gallery of ~21 branded, single-file HTML artifact templates (draft-PR review artifacts, final-PR explainers, a UAT walkthrough, and ad-hoc templates). Nothing exists yet that those templates can share: no brand tokens, no routing manifest, no single-file-SPA contract, and no automated enforcement. ART-001 ships that platform-neutral foundation so the template port specs (ART-002…005) become mechanical and the workflow specs (ART-007/009/010) can route against a complete catalog. Constraints: 70-20-10 Racecraft palette; Space Grotesk / Geist / Fira Code via Google Fonts, the only permitted external references; WCAG AA audited per theme; pinned provenance with manual re-sync; an artifact-relevant brand-voice subset; a standard-runtime repository test registered in the default suite; shipped plugin payload, so the generated-artifact contract applies. Out of scope: any actual template port, workflow wiring, a trigger-expression DSL, automated cross-repo drift checks, a marker-block sync script, banning navigation or text URLs, and embedded font files."

## Clarifications

### Session 1 (2026-07-28) — Trigger signal vocabulary

- **Q: What exactly is the closed signal vocabulary, and at what granularity?**
  → **A: Exactly five signals** — `competing_approaches`, `brownfield_change`,
  `self_review_findings`, `large_diff`, `operational_flow_change` — derived in one
  pass from the when-to-use semantics of all 21 seeded entries. The derivation
  closes exactly: 4 unconditional entries, 4 conditional entries consuming the five
  signals, and 13 ad-hoc entries. The discriminator for membership is the
  **consumer** test, not the producer test: several other conditions
  (`ui_change`, `schema_change`, `api_change`) are equally observable from the
  declared primary surface, but no seeded entry consumes them, so they are not
  members. The vocabulary reserves no slack; a later spec that introduces a real
  routing condition adds a member by recorded amendment naming its consuming entry.
- **Q: Are always-applies and any-one-of the complete trigger form set, and is an
  empty signal set legal?**
  → **A: Two forms only; an empty signal set is a hard validation failure.** No
  third "on request" form is introduced. The non-empty rule alone supplies the
  safety a third form was proposed to buy: deleting the last signal from a
  conditional entry yields an empty set, which fails validation rather than
  silently disabling that entry's routing.
- **Q: Is workflow stage an independent filter, or part of the trigger?**
  → **A: An independent filter, applied first.** Routing selects entries whose
  stage matches the stage being routed, then evaluates only those entries'
  triggers. "Always applies" therefore means unconditional *within its own stage*.
  Ad-hoc entries are never in any stage's candidate set, so they carry
  always-applies and are suppressed by the stage filter, not by their trigger.
  Narrowing within the ad-hoc set is served by the existing when-to-use field, so
  ad-hoc entries contribute no signals.
- **Q: Do all 21 seeded entries' triggers use only vocabulary signals?**
  → **A: Yes.** Four always-applies (`implementation-plan` and `spec-explainer` at
  draft-PR; `pr-writeup` and `uat-walkthrough` at final-PR), four conditional
  (`code-approaches` → `competing_approaches`; `module-map` →
  `brownfield_change`; `annotated-diff` → `self_review_findings` or `large_diff`;
  `flowchart` → `operational_flow_change`), and 13 ad-hoc always-applies. Every
  vocabulary signal is consumed by at least one entry, and no entry names a signal
  outside the vocabulary — so closure is enforceable in both directions.
- **Q: Where is the vocabulary enumerated so validation and every consumer read
  one authoritative set?**
  → **A: As data in the routing catalog, which ships.** The validation lives
  outside the shipped plugin directory, so a vocabulary sited only in the test
  would be invisible to every consumer of an installed plugin — that disqualifies
  the test as the home. The catalog is also the file a routing consumer already
  opens, and the repository already ships a closed signal vocabulary declared
  inline in a shipped contract file, so this is the established shape rather than
  a new one. Validation does **not** keep a duplicate list: a copy edited in the
  same change as the catalog is not an independent check, and set-equality against
  a copy would tax every legitimate vocabulary change. Validation instead asserts
  the **member count** fixed by FR-015 plus closure in both directions — an oracle
  derived from this specification rather than from the data it checks.
- **Q: How are signal names formatted?**
  → **A: Flat `snake_case`.** The one in-repo routing precedent uses namespaced
  `family:value` tokens because that classifier groups signals into families; this
  vocabulary has five flat members and no families, so namespacing would add
  structure carrying no information.

### Session 2 (2026-07-28) — Manifest field shape

- **Q: What are the per-entry key names, and is the artifact path a stored field?**
  → **A: Eight `snake_case` keys in FR-007's declaration order — `id`, `category`,
  `title`, `when_to_use`, `stage`, `trigger`, `source`, `status` — and no path key.**
  The artifact resolves as `templates/<id>.html` relative to the catalog's own
  directory, the convention all 21 planned entries already follow. Deriving it makes
  identifier/filename drift impossible and keeps the catalog portable: it ships inside
  the plugin payload and is read from a version-scoped install cache, where the
  repository-relative path style used elsewhere in this repo would not resolve.
  Identifiers are kebab-case and equal the file stem. `title` rather than `label`,
  because the value names a document and FR-007's own wording is "a title".
- **Q: What are the category enum's members, and does category duplicate stage?**
  → **A: Nine members adopted from the upstream gallery's own index taxonomy** —
  `exploration-planning`, `code-review`, `design`, `prototyping`, `diagrams`, `decks`,
  `research`, `reports`, `editors` — **and it is a genuinely different axis from
  stage.** The product plan's four-way grouping is port-spec ownership, not a browsing
  taxonomy; adopting it would make category derivable from stage for all eight staged
  entries. Under the upstream taxonomy five members straddle two stages each, so no
  stage-to-category function exists in either direction. Values are kebab-case,
  matching stage.
- **Q: The 20 ported entries inherit their upstream category. What does the one
  repository-authored entry, `uat-walkthrough`, take?**
  → **A: `editors` — no tenth member is minted.** The product plan's own name for the
  editors group's defining property is the export-back feedback loop, and this entry
  matches it exactly: per-step pass/fail toggles plus a copy-results-as-markdown export
  whose fixed schema the feedback sweep parses from a pull-request comment. A tenth
  member encoding "repository-authored" would restate the source-attribution field
  every entry already carries, would be read by no consumer, and would be permanent
  under the no-removal rule. Choosing an inherited member stays reversible by recorded
  amendment; minting a permanent member does not. The fit is imperfect and no worse
  than several inherited assignments where the category names purpose rather than
  surface form.
- **Q: What shape is per-entry source attribution?**
  → **A: A two-form object under a single `source` key, discriminated by `origin`** —
  upstream entries carry the origin plus the exact upstream filename as a string, so
  numeric prefixes survive intact; the repository-authored entry carries origin alone.
  This mirrors the trigger field's existing two-form design, so validation reuses one
  discriminated-shape check. The upstream repository is named once in the contract
  document rather than repeated across 20 entries.
- **Q: What is the top-level document shape, and what is the vocabulary key called?**
  → **A: A top-level object with exactly three keys — `schema_version`, `signals`,
  `templates` — in that order.** Version-first matches every version-carrying manifest
  in this repository. `signals` is a flat array of the five names in FR-015's order,
  carrying membership only: FR-017 puts each signal's meaning and evidence source in
  the contract document, so a name-to-description map here would create a second
  editable home for the same prose. Nothing else belongs at top level — no schema
  pointer (no schema document will exist, and this repository's one such pointer is
  already dangling) and no description.
- **Q: Does the catalog carry a `schema_version`, and in what format?**
  → **A: Yes — `"1.0"`, a `snake_case` key with a string value, first in the
  document.** This matches the repository's two hand-authored version-carrying
  manifests, one of which is enforced at that exact key and value by a live gate.
  **The justification recorded in this session was later found unsound and is
  superseded** — see FR-026. The session argued the field earns its place because an
  install cache can lag the repository. That skew channel does not exist: the catalog
  and every consumer that reads it ship in the same version-scoped payload, and this
  repository's validation only ever reads the source tree. The field is kept because
  it matches house form and costs one line. Its failure posture is stated in the
  routing-catalog contract — reject an unrecognized or newer major version, tolerate a
  recognized one at the same major — following the repository's existing convention
  and the conventional direction rule, since a flat reject-on-any-mismatch would break
  every installed copy the first time the version is bumped.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adopt shared branding with drift caught automatically (Priority: P1)

A template author porting an upstream template into the gallery needs their
artifact to look like every other Racecraft artifact without inventing colors,
type, or spacing. They copy one canonical, clearly delimited block of brand
tokens into their file, and one canonical theme-toggle snippet, and then get a
deterministic answer from the repository's automated checks about whether their
copy still matches the canonical source. When the brand later changes, the
canonical source is edited once and the same check names every artifact that
has fallen behind.

**Why this priority**: Every downstream template port is blocked until the
shared token set and its drift check exist. This is the smallest slice that
delivers standalone value — the brand kit is usable and enforced even if the
manifest and the contract document did not exist yet.

**Independent Test**: Take a copy of a gallery file, alter one character inside
the delimited brand block, and confirm the automated check fails and names both
the offending file and the block. Restore the block and confirm it passes.

**Acceptance Scenarios**:

1. **Given** a canonical brand token block and a gallery artifact that embeds it
   verbatim, **When** the repository's automated checks run, **Then** the check
   reports the artifact as matching the canonical block.
2. **Given** a gallery artifact whose embedded brand block differs from the
   canonical block by any character, **When** the checks run, **Then** the check
   fails and identifies the artifact and the block that drifted.
3. **Given** a gallery artifact that embeds the canonical theme-toggle snippet,
   **When** the checks run, **Then** the snippet is verified by the same
   mechanism and against the same standard as the brand block.
4. **Given** an author adds styling specific to their own template outside the
   delimited block, **When** the checks run, **Then** the artifact still passes,
   because only the delimited region is compared.

---

### User Story 2 - Route against a complete template catalog (Priority: P2)

An authoring agent, or a person designing routing behavior for a later spec,
needs to answer "which artifacts belong at this point in the workflow?" from a
single, machine-readable catalog. That catalog lists every template the gallery
will ever contain — not only the ones already built — so routing design can be
finished before the ports land. Each entry says what the template is for, which
workflow stage it belongs to, under what signals it should be produced, where
it came from, and whether it has actually shipped yet.

**Why this priority**: The catalog unblocks routing design for later workflow
specs and turns each template port into a mechanical status flip. It is
valuable on its own but has no effect on how artifacts look, so it ranks below
the brand kit.

**Independent Test**: Read the catalog with no other part of the feature in
place and confirm every planned template is listed with all required
information, and that entries marked as not-yet-shipped do not cause failures
for files that do not exist yet.

**Acceptance Scenarios**:

1. **Given** the seeded catalog, **When** a routing consumer reads it, **Then**
   it finds one entry for each of the 21 planned gallery templates, and every
   entry carries an identifier, category, title, when-to-use guidance, workflow
   stage, routing trigger, source attribution, and shipped status.
2. **Given** an entry whose trigger references a signal outside the documented
   vocabulary, **When** the checks run, **Then** the check fails and names the
   offending entry and the unrecognized signal.
3. **Given** an entry marked as not yet shipped, **When** the checks run,
   **Then** no artifact file is required to exist for that entry.
4. **Given** an entry marked as shipped, **When** the checks run, **Then** the
   artifact file it names must exist, and a missing or misnamed file fails.
5. **Given** two entries claiming the same identifier, **When** the checks run,
   **Then** the check fails on the duplicate.

---

### User Story 3 - Open an artifact locally and read it in either theme (Priority: P3)

A reviewer receives a generated artifact and opens it directly from their
filesystem — no server, no build, possibly no network. It renders immediately
with Racecraft branding, matches whichever theme their operating system is set
to, and offers a control to switch themes that is remembered next time where
the browser allows it. Nothing is fetched from the internet except the brand
fonts, and with no network at all the artifact is still completely readable.

**Why this priority**: This is the operator-facing payoff and the reason the
constraints exist, but it depends on the token set from Story 1 being in place,
so it is sequenced last.

**Independent Test**: Open a gallery artifact directly from the filesystem with
the network disabled, in both a light-set and a dark-set operating system, and
confirm it renders correctly, has no errors, and its theme control works.

**Acceptance Scenarios**:

1. **Given** an operating system set to dark, **When** the reviewer opens a
   gallery artifact from the filesystem, **Then** it renders in the dark theme
   on first paint with no flash of the light theme.
2. **Given** an open artifact, **When** the reviewer activates the theme
   control, **Then** the artifact switches themes immediately and, where the
   browser permits local storage, is still in the chosen theme when reopened.
3. **Given** a browser that refuses local storage for local files, **When** the
   reviewer activates the theme control, **Then** the theme still switches for
   the current session and the artifact reports no errors.
4. **Given** no network connection, **When** the reviewer opens the artifact,
   **Then** all content, layout, and behavior work, with text falling back to
   system typefaces.
5. **Given** a gallery artifact that loads any resource from a host other than
   the two permitted font hosts, **When** the checks run, **Then** the check
   fails and names the file and the offending reference.
6. **Given** a gallery artifact containing a link a reader can click to visit an
   upstream source, or an address written in a comment or in visible text,
   **When** the checks run, **Then** the artifact passes, because only
   resource-loading references are restricted.

---

### Edge Cases

- What happens when a template embeds the brand block twice, or opens a start
  marker without a matching end marker? The check must fail with a clear
  message rather than silently comparing the wrong region.
- What happens when a catalog entry names an artifact file that exists but the
  file omits the brand block entirely? A shipped artifact missing the block is
  a failure, not a pass-by-absence.
- What happens when a reviewer's operating system expresses no theme
  preference? The artifact must still render in a defined default theme.
- What happens when a reviewer has asked their system to reduce motion? Any
  transition in the shared kit must honor that request.
- What happens when the fonts fail to load, or load slowly? Text must remain
  readable throughout using system fallbacks, never invisible while waiting.
- What happens when the upstream brand sources change? Nothing automated — the
  recorded provenance tells a human which source revision the kit was taken
  from so a deliberate re-sync can be made.
- What happens when a catalog entry's stage or category is outside the allowed
  set, or a required field is missing or empty? The check must fail and name
  the entry and the field.
- What happens when a new artifact file is added to the gallery but no catalog
  entry claims it? The check must fail, so orphaned artifacts cannot accumulate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The foundation MUST provide a single canonical set of brand design
  tokens covering the 70-20-10 Racecraft palette (a warm-neutral scale from
  `#F7F6F4` to `#E0DED9` as the dominant surface family, brand red `#dc143c`
  reserved for punctuation-level emphasis, brand blue `#3c89c6` for accents),
  a matching dark-theme set, the heading/body/monospace typeface stacks with
  system fallbacks, focus-visible treatment, and reduced-motion handling.
- **FR-002**: The canonical token set MUST be delimited by an explicit start and
  end marker so that the exact region every artifact embeds is unambiguous, and
  MUST be embeddable verbatim into a self-contained artifact without any build
  or transformation step.
- **FR-003**: The foundation MUST provide a canonical theme-toggle snippet —
  the control and the behavior that switches themes — delimited by its own
  start and end markers and embeddable verbatim by the same copy-in method.
- **FR-004**: Gallery artifacts MUST honor the reader's operating-system theme
  preference by default, MUST allow the reader to override it explicitly, and
  MUST retain that override for future visits where the browser permits local
  storage, degrading to a session-only override otherwise without surfacing an
  error. When the reader overrides the theme, the browser-rendered surfaces the
  artifact does not paint itself — form-control widgets, scrollbars, and the
  default canvas — MUST follow the **chosen** theme rather than the
  operating-system preference. Declaring support for both schemes is not
  sufficient for this, because that declaration resolves against the
  operating-system preference; the override MUST set the applicable scheme
  explicitly in each direction, or an overriding reader gets page colors from
  one theme and native widgets from the other.
- **FR-005**: Every foreground/background token pairing the kit **permits** MUST
  meet WCAG AA contrast — at least 4.5:1 for normal text (WCAG 1.4.3), and at
  least 3:1 for large text and for user-interface components and meaningful
  graphics (WCAG 1.4.11) — audited independently for the light theme and the
  dark theme rather than assumed from one another. "Large text" means at least
  24px, or at least 18.66px when bold. The audit MUST be **complete and
  symmetric**: every token audited in one theme MUST be audited in the other,
  and every token MUST be measured against **every** surface it may pair with,
  not against a single representative surface. Every token the audit names MUST
  have its value defined for both themes, so each recorded ratio is
  independently reproducible. Where a pairing does not meet its threshold it
  MUST be explicitly **prohibited** by a usage rule carried in the kit itself
  that names the token to use instead; a pairing that neither meets its
  threshold nor carries such a rule is a defect. Recorded ratios MUST be
  computed rather than asserted, and MUST NOT be rounded up to a threshold.
- **FR-006**: Automated validation MUST compare each gallery artifact's embedded
  copy of a marked block against the canonical source exactly, and MUST fail
  with the artifact name and the block name on any difference. The comparison
  MUST be limited to the marked region so template-specific styling outside it
  is unaffected.
- **FR-007**: The foundation MUST provide a machine-readable routing catalog
  seeded with one entry for each of the 21 planned gallery templates — 20
  derived from upstream templates (4 draft-PR, 3 final-PR, 6 design and
  prototyping, 7 knowledge, report and editor) plus 1 repository-authored UAT
  walkthrough. Each entry MUST carry exactly eight fields, named
  `id`, `category`, `title`, `when_to_use`, `stage`, `trigger`, `source`, and
  `status`: an identifier unique across the catalog and in filename-safe kebab-case
  (FR-019), which the artifact's file stem then equals by construction rather than
  by a separate rule; a category drawn from `exploration-planning`, `code-review`, `design`,
  `prototyping`, `diagrams`, `decks`, `research`, `reports`, or `editors`; a title;
  when-to-use guidance; a workflow stage drawn from `draft-pr`, `final-pr`, or
  `ad-hoc`; a routing trigger; attribution to its source template; and a shipped
  status. No entry stores its artifact path — the path is derived from the identifier
  relative to the catalog's own directory.

  Entry identifiers are the catalog's **stable join key**: a port MUST change only an
  entry's `status`, and MUST NOT rename, add, or remove an identifier. Two things are
  required to make that guarantee real, because it is currently neither stated where
  ports will read it nor detectable. First, the guarantee MUST be carried by the
  shipped contract document (FR-010), which is the only artifact that reaches all four
  port specs — stating it only in this feature's planning artifacts, which a port
  author has no reason to open, is how it gets lost. Second, validation MUST assert
  the seeded identifier set against the catalog, so a rename fails loudly.

  **Why that assertion is not the duplicate list FR-017 prohibits.** FR-017's rule is
  scoped by its own stated reason: a copy edited *in the same change as the catalog*
  proves nothing. That applies to the signal vocabulary, which this feature authors
  alongside its validation. It does not apply here, because the threat is a **later**
  spec renaming an identifier: defeating a set pinned in this feature's commit would
  require a port author to edit a validation file outside that port's declared scope,
  which is exactly the independence FR-017 asks for. This mirrors an existing check in
  this repository that pins another shipped manifest's identifiers the same way.
- **FR-008**: Routing triggers MUST be expressed in exactly one of two forms:
  "always applies", or a **non-empty** set of signals drawn from the closed,
  documented vocabulary. The any-one-of relationship is the format's only
  combining rule — signal sets MUST NOT nest, and no conjunction, negation, or
  other operator exists. Automated validation MUST reject a trigger that names a
  signal outside the vocabulary, that presents an empty signal set, or that uses
  an unrecognized form, naming the offending entry. No expression language,
  operators, or evaluator are to be introduced.
- **FR-009**: Each catalog entry's status MUST be either `planned` or `shipped`.
  Both the existence check and the orphan check MUST resolve the artifact from the
  entry's identifier relative to the catalog's own directory. Because that path is
  **composed** from the identifier rather than stored, the identifier format fixed
  by FR-019 is what keeps the resolved path inside the gallery; resolution MUST
  additionally be rejected if it would leave the artifact directory.
  The relationship between status and file presence MUST be **biconditional**: an
  artifact file MUST exist for a `shipped` entry, and MUST NOT exist for a
  `planned` entry. A one-directional rule — requiring the file only for `shipped`
  and staying silent on `planned` — would let a real artifact ship under a
  `planned` entry and thereby skip every check keyed on shipped status, including
  the embedded-block comparison; it would also leave SC-004's "changes exactly one
  catalog value" unenforceable, since adding the file without flipping the status
  would pass. Validation MUST fail if a gallery artifact file exists that no entry
  claims. The orphan sweep MUST cover the artifact directory's whole contents, not
  only the files the derivation can name: a file whose extension the derivation can
  never produce is reported as a disallowed file rather than as an unclaimable
  orphan, so it cannot accumulate and its failure message is actionable. An
  **absent** artifact directory MUST be treated as zero artifacts and pass, which
  is the state this feature ships in — no artifact is ported here, and an empty
  directory is not preserved by version control.
- **FR-010**: The foundation MUST document the single-file contract every
  gallery artifact obeys — all behavior, styling, and data inline in one file;
  correct rendering when opened directly from the filesystem with no errors
  reported; the shape and field meanings of the routing catalog, since the
  catalog format itself cannot carry explanatory notes; the two trigger forms and
  the two-step stage-then-trigger routing rule; the identifier stability guarantee
  and the single value a port may change (FR-007); each routing signal's meaning
  and evidence source; and the accessibility obligations every artifact inherits
  — the audited pairings and the prohibited ones (FR-005), the use-of-color rule
  (FR-021), the theme-control obligations (FR-022), focus visibility and
  reduced-motion behavior (FR-023), and the typography loading and fallback
  rules (FR-024). The contract is the only place an obligation reaches all four
  port specs at once; an accessibility duty absent from it is re-decided per
  port or lost entirely.
  Because the catalog's shape is thereby written down in two places — as prose in
  the contract document and as assertions in the validation — the requirements MUST
  name which one governs. The **validated** shape is normative; the contract
  document is its explanatory statement and MUST say so, so a port author who finds
  the two disagreeing knows which to follow, and knows the disagreement is a defect
  to report rather than a choice to make. Only the signal vocabulary's membership is
  additionally closed between the two by automated means (FR-017); the rest of the
  prose is held true by review, which is precisely why the authority must be named.
- **FR-011**: Automated validation MUST scan every gallery artifact for external
  references in resource-loading positions — script, image and frame sources,
  responsive-image source sets, stylesheet and preconnect link targets, style
  resource and import references, and network-request destinations written into
  the file — and MUST fail on any host other than `fonts.googleapis.com` and
  `fonts.gstatic.com`. References that a reader clicks to navigate, and
  addresses appearing in comments or in visible text, MUST remain permitted so
  provenance and attribution links survive.
- **FR-012**: The brand kit MUST carry a provenance header naming each upstream
  brand source by repository and path, the exact source revision it was taken
  from, and the date of that capture. No prose from a private source may be
  reproduced. Keeping the kit current with its upstream sources is a deliberate
  human action; no automated cross-repository comparison is introduced.
- **FR-013**: The foundation MUST provide a brand-voice reference for artifact
  copy covering only the artifact-relevant subset of the upstream content
  rules: voice and tone, banned and preferred vocabulary, answer-first summary
  structure, and call-to-action and button labeling. Website-only concerns —
  structured-data markup, question-and-answer section minimums, and site
  navigation chrome — MUST be excluded so they cannot mislead an authoring
  agent.
- **FR-014**: All validation described above MUST run as part of the
  repository's standard automated suite with no additional setup, services, or
  dependencies beyond the standard runtime, and MUST be discoverable by that
  suite's own registry rather than requiring a separate invocation.
- **FR-015**: The closed vocabulary MUST consist of exactly five signals —
  `competing_approaches` (planning weighed more than one viable implementation
  approach), `brownfield_change` (the change modifies existing code rather than
  adding only new files), `self_review_findings` (the pre-PR self-review recorded
  at least one gap), `large_diff` (the finished change's size reached the
  repository's existing warn or block threshold), and `operational_flow_change`
  (the change alters a documented multi-step runtime or delivery process). Signal
  names MUST be flat `snake_case` and unique within the vocabulary — the format is
  stated here rather than left to a design note, because validation checks it and
  every rule validation enforces belongs to a requirement. Each
  signal MUST be documented with the named workflow evidence a routing consumer
  reads to decide it is present, and that documentation obligation MUST itself be
  validated rather than left to review — an undocumented member, or documentation
  for a name the vocabulary does not carry, is a failure (FR-017). A signal MUST
  NOT be defined unless at least one catalog entry consumes it, and automated
  validation MUST fail both when an entry names a signal outside the vocabulary and
  when the vocabulary carries a signal no entry uses.
- **FR-016**: Routing MUST resolve in two independent, ordered steps: first select
  the entries whose stage matches the stage being routed, then evaluate the
  triggers of only those entries. An always-applies trigger therefore means
  "always within its own stage" and MUST NOT cause an entry to be produced at any
  other stage. Entries staged for ad-hoc use MUST never enter a stage's candidate
  set, so their triggers are never evaluated by automated routing; the trigger
  field remains mandatory on those entries so every entry carries a uniform,
  validated shape.
- **FR-017**: The vocabulary MUST be declared as data inside the routing catalog
  itself, under a top-level `signals` key, which is the single authority for
  membership. Validation MUST NOT hold a
  second copy of the list, because a copy edited in the same change as the catalog
  is not an independent check. Instead, validation MUST assert the member count
  against the count this specification fixes, so that inventing a signal (which
  raises the count) and disguising it by removing a real one (which orphans the
  entries still using the removed signal) both fail. The contract document MUST
  explain each signal's meaning and evidence source and MUST name the catalog as
  the authoritative list rather than restating it as an independent one.
  **Count plus trigger-closure alone is not sufficient, and the limit MUST be
  stated rather than assumed.** A signal renamed in the vocabulary and in its
  consuming entry within one change — or an addition paired with an equal-sized
  removal — leaves the count at five and leaves closure intact in both directions,
  so every one of those checks passes while the vocabulary silently changes
  underneath its consumers. Validation MUST therefore additionally assert closure
  between the vocabulary and the per-signal documentation FR-015 already requires:
  every member of `signals` MUST be documented in the contract document, and every
  signal documented there MUST be a member. This adds **no** duplicate list to the
  validation — it is a closure check between two artifacts the feature already
  ships, exactly like the closure asserted between `signals` and the entries' own
  triggers, and the documentation is the one place a signal's meaning cannot be
  renamed without a human writing new prose. The residual limit is that a rename
  carried through the catalog, the consuming entry, and the documentation together
  still passes; that is the recorded-amendment path the vocabulary's stability
  guarantee already prescribes, so it is a deliberate act rather than a silent one.
- **FR-018**: The gallery directory MUST actually reach both shipped platform
  payloads. The repository's payload builder copies a fixed list of top-level names
  per platform and silently copies nothing when a named source is absent, so a new
  shipped directory that is not added to both lists is omitted from the built
  payload **without any error**. This feature MUST add the gallery to both lists and
  MUST be verified by an automated check that fails when a gallery artifact is
  present in the source tree but missing from either built payload. A green build is
  not evidence that the gallery shipped.
  Reaching the payload is necessary but not sufficient: what ships MUST also be what
  was authored. Validation MUST therefore assert that each gallery file in **each**
  built payload is byte-identical to its source, not merely that the two file lists
  agree. A path-set comparison alone cannot see a copy that arrived truncated,
  stale, or rewritten, and the catalog is the file whose silent divergence would be
  most costly — a consumer reading an install cache would route against a different
  catalog than the repository declares. Because the Codex build runs a text rewriter
  over every file in its payload, byte-equality there is conditional on the gallery
  containing nothing that rewriter matches: no gallery file may carry a relative
  reference into a skills directory of the form that rewriter rewrites. That
  authoring rule MUST be enforced by validation rather than only documented, since
  it is the sole reason the content-equality assertion is safe to make on that
  platform. The enforcing check MUST be defined by the rewriter's own matching
  rule rather than by a plain substring search, so that the contract document can
  state the rule in prose without tripping it — a check that fails the document
  which records it would be a self-defeating gate.
- **FR-019**: Every catalog entry's declared shape MUST be validated: the eight
  required keys present with the documented names; `title` and `when_to_use`
  present as **non-empty strings**; `stage` and `category` values within their
  closed sets; `status` either planned or shipped; `source` matching one of its two
  forms, with `source.origin` drawn from the closed set `upstream` or `repository`
  and `source.file` unique across the catalog, since two entries naming one
  upstream file would put two artifacts under a single provenance that FR-020's
  per-artifact attribution cannot express; and identifiers unique across the
  catalog. The identifier MUST additionally match
  a **filename-safe kebab-case form** — lowercase letters and digits in
  hyphen-separated segments, with no leading, trailing, or repeated hyphen, and no
  path separator, parent-directory segment, whitespace, or dot. This format rule is
  the load-bearing one, because FR-009 composes the artifact path out of this field:
  an unconstrained identifier composes a path that escapes the artifact directory,
  and both the existence check and the orphan check would follow it. The
  earlier formulation of this clause — that an identifier "equals the referenced
  file stem" — is **not** retained: once the path is derived rather than stored
  (Clarifications Session 2) that comparison is true by construction and can never
  fail, so it reads as a check while asserting a tautology. Validating the format
  is what the derived path actually needs.
  Validation MUST name the offending entry and the offending field on failure.
  Where the identifier is itself the defect — missing, duplicated, or malformed —
  the entry MUST be identified by its **position** in the catalog, because naming
  it by identifier is circular in exactly the case where entry identity is what
  broke. Validation MUST report every offending entry rather than stopping at the
  first, so a seed of 21 rows is corrected in one pass.
- **FR-020**: The single-file contract MUST require that every gallery artifact
  derived from an upstream open-source template carry an attribution header, as an
  HTML comment near the top of the file, containing: the upstream repository and the
  upstream file it derives from; the upstream copyright line reproduced verbatim; a
  license identifier; a link to the full upstream license text; and an explicit
  statement that the file is a modified derivative rather than the original. The
  gallery MUST additionally carry one file reproducing the upstream permission notice
  verbatim, which those headers point at, and that file MUST NOT be named such that
  the payload builder would mistake it for this repository's own license. Automated
  validation MUST fail when an entry declaring an upstream origin names an artifact
  whose header is missing any required element, and MUST fail when an artifact
  carries an upstream copyright line while its entry declares no upstream origin.
  The `source` field's origin discriminator is what makes this mechanically
  checkable, and it MUST therefore be trustworthy as a gate rather than merely
  present. Two properties are required for that. First, `origin` MUST be validated
  against the closed two-member set fixed by FR-019. Second, the attribution checks
  MUST be **exhaustive** over that set — every entry takes exactly one branch, and
  an entry whose origin is unrecognized MUST fail validation rather than fall
  through. Expressed as two independent conditionals, one testing for `upstream`
  and one for `repository`, an entry carrying any third value matches neither: an
  upstream-derived artifact would then ship with no attribution header, no
  misattribution check, and a green suite. A licensing gate that silently declines
  to run is worse than no gate, because the green result is read as evidence the
  attribution was checked.
- **FR-021**: Brand red MUST NOT be the sole visual means of conveying
  information, indicating an action, prompting a response, or distinguishing an
  element (WCAG 1.4.1, Level A). Wherever red carries a status or a distinction,
  that meaning MUST also be available without color — as text, a shape, a
  glyph, or a position — so it survives for a reader who cannot perceive the hue
  and for a monochrome print or screenshot. This is a separate obligation from
  contrast: a red that clears its ratio still fails if the color is the only
  thing distinguishing the element. The kit's "punctuation-level" reservation is
  a rule about **how much** red is used and at what sizes; it does not by itself
  satisfy this requirement, and the two MUST be documented as distinct rules so
  an authoring agent cannot read one as discharging the other.
- **FR-022**: The canonical theme control MUST be operable by keyboard alone,
  reachable in the document's normal focus order and activatable without a
  pointer (WCAG 2.1.1, Level A). It MUST expose a programmatically determinable
  name, role, and current state — the state identifying which theme is active —
  so the control is usable by assistive technology (WCAG 4.1.2, Level A). The
  control's semantic element and its state mechanism MUST be fixed in the
  canonical snippet rather than left to each port: the snippet is embedded
  verbatim into every artifact, so a defect here reaches all of them and no port
  can correct it locally. A control that is reachable but unnamed, or named but
  stateless, does not satisfy this requirement.
- **FR-023**: The kit MUST define a focus-visible treatment and MUST require
  that every interactive element in a gallery artifact carries it; suppressing
  the focus indicator without an equivalent replacement is prohibited (WCAG
  2.4.7, Level AA). The indicator's own contrast MUST be audited under FR-005
  against every surface it can appear on. The kit MUST also honor a reader's
  reduced-motion preference by suppressing or near-eliminating animation,
  transition, and smooth-scrolling behavior for those readers. This explicitly
  includes the cross-theme color transition, which is the shared kit's most
  likely animation. Reduced-motion behavior is not asserted by the automated
  suite and MUST therefore carry a named manual verification scenario, as the
  other browser-observable outcomes already do.
- **FR-024**: Text MUST remain visible throughout font loading — there MUST be
  no period during which text is rendered invisibly while a brand face is
  fetched. Because the artifacts link a hosted font stylesheet rather than
  declaring their own font faces, the loading behavior is determined by the font
  request itself: the request MUST carry the parameter that yields swap
  behavior, and its absence MUST be treated as a defect rather than a style
  preference, since the hosted default is a blocking behavior with an
  invisible-text period. This MUST be enforced by automated validation, not left
  to review. Each typeface role MUST additionally declare a fallback stack that
  is distinguishable from the other roles' stacks, so the heading, body, and
  monospace distinction survives with the brand faces unavailable. Where two
  roles would otherwise resolve to the same fallback face, the specification
  MUST state what carries the distinction instead — semantic level, size, and
  weight rather than typeface identity — so the offline rendering is degraded in
  appearance only and never in structure.
- **FR-025**: The brand kit MUST distinguish two token classes and state the rule
  that governs both. A **functional token** exists to serve a stated purpose and
  MUST satisfy its contrast floor against every surface it may pair with; when it
  does not, its value is corrected. A **brand primitive** is not re-valued to
  resolve a contrast failure; instead the functional need it cannot serve is routed
  to a functional token that can, and that sibling MUST exist and be named at the
  primitive's point of definition so an author reading one sees the other. Any
  restriction on a brand primitive MUST be stated as narrowly as the measurement
  supports — naming the specific pairing and role that fail, not a blanket ban.
- **FR-026**: The catalog's **top-level** shape MUST be validated, not only its
  entries: exactly the three documented keys in the documented order, and
  `schema_version` carrying the literal value this specification fixes. Validation
  MUST reject an unrecognized version rather than interpreting the document.
  Migration between versions is deliberately not specified here and belongs to the
  first spec that reads the catalog programmatically.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed for this feature. The recorded
  budget warning is accepted on its own merits (see Reviewability Budget), not
  as a refactor, infra, or upgrade override.
- The gallery directory is shipped plugin payload, so the generated-artifact
  contract applies: regenerated payload and proof artifacts accompany the
  change. Those regenerated artifacts are declared generated and are excluded
  from projected reviewable LOC, and they are not part of the review surface.

### Reviewability Budget *(mandatory)*

- **Primary surface**: seed/config
- **Secondary surfaces, if any**: docs/process (the single-file contract and
  brand-voice references); harness/adapter (the validation added to the
  repository's standard suite)
- **Projected reviewable LOC**: 62
- **Projected production files**: 2
- **Projected total files**: 24

  The three figures above are stated against the binding metric, which the product
  plan's Reviewability Contract defines as **production code only — documentation,
  tests, and configuration do not contribute**. Under that rule the production
  surface is the payload-builder edit (about two lines) plus the theme toggle's
  inline behaviour (about sixty). The design tokens and the routing catalog are
  configuration; the contract document, voice reference, and upstream notice are
  documentation; the validation module is a test. Regenerated payload and proof
  artifacts are declared generated and excluded.

  **Total authored volume is much larger and is disclosed deliberately**: roughly
  1,430 lines across nine authored files — about 497 in the validation module, 476
  declarative (design tokens and catalog rows), 370 prose, 60 markup, and 25
  reproduced verbatim. That figure is **not** the budget metric and must not be
  compared against the budget thresholds, which the contract defines over
  production code only. It is recorded because a reviewer deserves to know the real
  size of what they are being asked to read, independent of what the metric counts.
- **Budget result**: warning accepted, on a **different basis than at scaffold**
- **Split decision**: Remains one spec, but the original justification no longer
  applies and has been replaced rather than restated.

  **Why the scaffold rationale died.** The split was first declined under the
  product plan's 1.5x greenfield allowance for net-new-only slices. FR-018 forces
  a modification to the payload builder, and the estimator computes greenfield as
  "every declared entry is new or an excluded generated artifact". One
  non-generated modified entry disqualifies it, so thresholds revert from
  600/1200 to 400/800. The allowance is unavailable by the estimator's own
  definition, not by interpretation.

  **The automated estimate is not evidence here.** The plan-phase estimator
  returns `status: pass` with `projected: 0`, because it counts only paths under
  conventional source directories with JavaScript, TypeScript, or SQL extensions.
  Every file in this feature is CSS, HTML, JSON, Markdown, or Python, so none are
  counted. That zero must not be cited as a size argument in review.

  **What survives from the original decision.** The operator's recorded choice
  rested on four legs. Two were greenfield-dependent and are dead. Two are not, and
  they still carry: this is one thin vertical slice (tokens, then catalog, then
  validation), and most of its volume is declarative token declarations and catalog
  rows rather than logic. The vertical-slice leg is the one the slicing doctrine
  actually cares about, and nothing has touched it.

  **A threshold comparison that was raised and does not hold.** During checklist
  remediation the scoping estimator's figure was read as sitting a few points under
  an 800 block threshold. That comparison is between two unrelated instruments. The
  scoping estimator has a single ceiling of 400 and returns only "ok" or "warn" —
  it has no block status and never blocks. The 800 belongs to the setup-mode
  reviewability gate, which reads the declared figures from this document and does
  not consume the estimator's output at all. Further requirements cannot trip a
  block through that path.

  **What the size question actually turns on.** Under the binding
  production-code-only metric this feature is nowhere near any threshold. The
  disclosed total authored volume is large, but it is dominated by a test, by
  declarative rows, and by prose — all excluded by the contract, and all reviewable
  at a glance rather than line by line. The two-line production edit is the entire
  production surface.

  **Why splitting is rejected on its merits, not only on thresholds.** All four
  blocked port specs require both the brand kit and the routing catalog, so a split
  unblocks none of them earlier — it strictly delays all four. The fallback cut
  recorded below is also not executable as written: one validation group reads the
  catalog while being assigned to the kit slice, and suite registration falls in the
  catalog slice, which would leave the kit slice shipping a test the suite never
  runs. Adopting it would require re-deriving the cut — new, unreviewed design work
  introduced late.

  **Fallback if a reviewer still wants it**: 1a (brand kit, theme toggle, brand
  voice, upstream notice, their validation, **and suite registration**) and 1b
  (routing catalog, contract document, catalog validation, payload wiring). The
  embedded-block check must move to 1b or be explicitly scoped to the vacuous case,
  because it reads the catalog.

  **Where the size decision is properly made.** Not here. The post-tasks atomicity
  route and the pull-request-time diff gate are the two instruments that measure a
  finished change rather than forecast one. This spec defers to them rather than
  pre-empting them with a line-count trigger on a test file.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Review order SHOULD be: token set, then theme-toggle snippet, then routing
  catalog, then the single-file contract and brand-voice references, then the
  validation.
- Verification evidence MUST include the automated suite result and manually
  captured evidence of an artifact opened directly from the filesystem in both
  themes, since browser rendering is not covered by the automated suite.
- The accepted budget warning and its rationale MUST be restated in the PR.

### Key Entities *(include if feature involves data)*

- **Brand Token Set**: The canonical, marker-delimited collection of named
  design values — surface and text colors for both themes, accent and emphasis
  colors, typeface stacks, focus treatment, and motion handling — that every
  gallery artifact embeds verbatim. Carries its own provenance record.
- **Theme Toggle Snippet**: The canonical, marker-delimited control and behavior
  that lets a reader override the operating-system theme, including how that
  choice is remembered and how it degrades when storage is unavailable.
- **Gallery Template Entry**: One catalog row describing a single template — its
  unique identifier, category, title, when-to-use guidance, workflow stage,
  routing trigger, source attribution, and shipped status. Those eight fields are
  the whole row: the artifact it refers to is **not** a ninth field but is derived
  from the identifier (FR-007, FR-009), so an entry cannot disagree with its own
  file name. The catalog holds 21 of these; ports change only the status.
- **Routing Signal**: A named condition from a closed vocabulary that an entry's
  trigger may reference to indicate when that artifact should be produced.
- **Gallery Artifact**: A single self-contained file that embeds the brand token
  set and, where interactive, the theme-toggle snippet; renders from the
  filesystem alone; and loads nothing external except brand fonts.
- **Provenance Record**: The recorded identity of each upstream brand source —
  repository, path, exact revision, and capture date — that makes deliberate
  re-sync possible without reproducing private material.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of shipped gallery artifacts open directly from a
  filesystem, render with Racecraft branding, and report no errors — verified
  for every shipped artifact, in both themes.
- **SC-002**: Any single-character divergence between an artifact's embedded
  brand block or theme-toggle snippet and its canonical source is detected on
  the very next automated run, naming the file and the block, with no false
  passes.
- **SC-003**: A routing consumer can determine, from one read of the catalog and
  with no other source, which artifacts apply at a given workflow stage for all
  21 planned templates; 100% of entries carry every required field with a
  recognized stage, category, and trigger.
- **SC-004**: Porting a template requires no edit to any shared foundation file:
  the author embeds two blocks and changes exactly one catalog value from
  `planned` to `shipped`.
- **SC-005**: A reviewer whose system is set to dark sees the dark theme on
  first paint with no flash of the light theme, and can change themes in a
  single interaction.
- **SC-006**: With the network fully unavailable, every gallery artifact remains
  completely readable and every interactive control still works; the only
  observable difference is typeface substitution.
- **SC-007**: 100% of the token set's **permitted** pairings meet WCAG AA
  contrast — at least 4.5:1 for normal text and 3:1 for large text and
  meaningful non-text elements — measured separately for the light and dark
  themes, with every token measured against every surface it may pair with in
  both themes. Every pairing that falls below its threshold is named as
  prohibited with a stated replacement; zero pairings are left neither passing
  nor prohibited, and zero recorded ratios are unreproducible from the token
  values the artifacts define.
- **SC-008**: Zero external hosts other than the two permitted font hosts appear
  in a resource-loading position across the entire gallery, while links a reader
  can click and addresses in comments or visible text continue to pass.
- **SC-009**: The four blocked template-port specs can begin work using only the
  artifacts this feature delivers, with no additional foundation decisions
  required of them.
- **SC-010**: The theme control can be reached and activated using the keyboard
  alone, and reports a name, a role, and which theme is currently active to
  assistive technology in both states — verified once against the canonical
  snippet, because every artifact embeds that snippet verbatim.
- **SC-011**: No gallery artifact renders text invisibly at any point during
  font loading, and with the brand faces unavailable the heading, body, and
  monospace roles remain distinguishable from one another.

## Assumptions

- The closed vocabulary of routing signals is exactly five members (FR-015),
  derived in one pass from the when-to-use semantics of all 21 seeded entries —
  one member per conditional routing condition already committed in the product
  plan. Membership is decided by the **consumer** test, not the producer test:
  other conditions such as a UI, schema, or API surface change are equally
  observable from the declared primary surface, but no seeded entry consumes them,
  so they are not members. In keeping with the catalog seeding decision below, the
  vocabulary reserves no slack: members are added by recorded amendment naming the
  consuming entry, and existing members are not renamed or removed.
- Signals are names, not computed predicates. This feature validates only that
  every entry's trigger uses a recognized form and recognized signal names.
  Deciding whether a signal holds for a given change is the emitting workflow's
  concern in a later spec, which is why no expression language, operator, or
  evaluator appears here. This is true of every member equally —
  `operational_flow_change` is no more a judgment call than `large_diff`, which
  likewise depends on a threshold a later spec owns.
- Narrowing within the ad-hoc set is served by each entry's existing when-to-use
  guidance, not by signals. Ad-hoc entries therefore carry an always-applies
  trigger, are suppressed from automated routing by the stage filter (FR-016), and
  contribute no vocabulary members.
- Field-level catalog details are fixed in Clarifications Session 2. The catalog's
  shape is documented alongside the single-file contract, because the catalog format
  cannot carry inline explanation, and it is enforced by the repository's validation
  rather than by a separate formal schema document.
- The category vocabulary reserves no slack and adds no member for repository
  authorship. Origin is already carried by each entry's source-attribution field, so
  a category member encoding it would duplicate a required field. Category is
  validated for membership but read by no routing consumer (FR-016), so it is a
  browsing axis rather than a routing input. The nearest shipped contract in this
  repository keeps kind-of-thing and origin as two separate fields, which is the
  shape adopted here.
- The payload builder's per-platform copy lists are the reason FR-018 exists.
  Because a missing source is copied silently rather than reported, the gallery's
  absence from the built payload would otherwise look identical to a successful
  build. The verification FR-018 requires is what distinguishes them.
- The catalog is seeded at 21 entries because that is the full planned gallery:
  4 draft-PR, 3 final-PR, 6 design and prototyping, and 7 knowledge, report and
  editor templates derived from upstream sources, plus 1 repository-authored UAT
  walkthrough. If a later spec adds a template, it adds an entry; this feature
  does not reserve slack.
- Brand typefaces are Space Grotesk for headings, Geist for body, and Fira Code
  for monospace, loaded as linked web fonts. Swap behavior is not a property of
  the link — it is served by the font provider only when the request asks for
  it, and the provider's default is a blocking behavior, so FR-024 makes the
  request parameter itself the requirement and puts it under automated
  validation. Font files are not embedded in artifacts — embedding was rejected
  in the product plan on artifact-size grounds.
- The heading and body brand faces are both sans-serif, so a naive fallback
  would resolve both roles to the same system face and flatten the visual
  distinction between them offline. FR-024 therefore requires distinguishable
  stacks and records that hierarchy is carried by semantic heading level, size,
  and weight rather than by typeface identity — which is what keeps SC-006's
  "typeface substitution only" claim true rather than aspirational.
- The accessibility obligations this feature fixes are, by WCAG success
  criterion: 1.4.1 Use of Color (A), 1.4.3 Contrast Minimum (AA), 1.4.11
  Non-text Contrast (AA), 2.1.1 Keyboard (A), 2.4.7 Focus Visible (AA), and
  4.1.2 Name, Role, Value (A). Honoring `prefers-reduced-motion` is **not**
  required at AA — the nearest criterion, 2.3.3 Animation from Interactions, is
  Level AAA. It is specified here anyway because the spec already committed to
  it as an edge case and because the shared kit is the only place it can be
  fixed once for all 21 artifacts; it is a deliberate choice above the
  conformance floor, not an AA obligation.
- `fonts.googleapis.com` and `fonts.gstatic.com` are the only external hosts any
  gallery artifact may load from, and only in resource-loading positions.
- Upstream brand sources are the private `racecraft-lab/racecraft` repository's
  brand documentation and this repository's own documentation-site brand
  stylesheet. The private source is cited by repository, path, revision, and
  date only; no prose is copied from it beyond the approved voice subset.
- Marker-delimited blocks are copied by hand or by an authoring agent. No
  synchronization script and no build step are introduced; the automated
  comparison is what makes hand-copying safe.
- The validation is a repository-only concern: it lives outside the shipped
  plugin directory, runs on the standard Python runtime with only its standard
  library, is named for durable capability rather than this spec's identifier,
  and is registered in the suite's own manifest so a plain suite run picks it up.
- Browser rendering, theme switching, and offline behavior cannot be asserted by
  the repository's automated suite, which does not drive a browser. Those
  outcomes are verified manually and recorded as acceptance evidence.
- Adding files under the shipped plugin directory triggers the repository's
  generated-artifact contract; regenerated payload and proof artifacts are part
  of the change but are not authored by hand.
- No template port, no workflow wiring, no trigger-expression language, no
  automated cross-repository drift check, and no documentation-site palette
  overlap check are in scope; each is either a later spec or an explicitly
  rejected alternative.

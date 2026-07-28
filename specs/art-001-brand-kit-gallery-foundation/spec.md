# Feature Specification: Artifact Brand Kit & Gallery Foundation

**Feature Branch**: `art-001-brand-kit-gallery-foundation`

**Created**: 2026-07-28

**Status**: Draft

**Input**: User description: "SpecKit-Pro is adding a gallery of ~21 branded, single-file HTML artifact templates (draft-PR review artifacts, final-PR explainers, a UAT walkthrough, and ad-hoc templates). Nothing exists yet that those templates can share: no brand tokens, no routing manifest, no single-file-SPA contract, and no automated enforcement. ART-001 ships that platform-neutral foundation so the template port specs (ART-002…005) become mechanical and the workflow specs (ART-007/009/010) can route against a complete catalog. Constraints: 70-20-10 Racecraft palette; Space Grotesk / Geist / Fira Code via Google Fonts, the only permitted external references; WCAG AA audited per theme; pinned provenance with manual re-sync; an artifact-relevant brand-voice subset; a standard-runtime repository test registered in the default suite; shipped plugin payload, so the generated-artifact contract applies. Out of scope: any actual template port, workflow wiring, a trigger-expression DSL, automated cross-repo drift checks, a marker-block sync script, banning navigation or text URLs, and embedded font files."

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
  error.
- **FR-005**: Every foreground/background token pairing the kit defines MUST
  meet WCAG AA contrast, audited independently for the light theme and the dark
  theme rather than assumed from one another.
- **FR-006**: Automated validation MUST compare each gallery artifact's embedded
  copy of a marked block against the canonical source exactly, and MUST fail
  with the artifact name and the block name on any difference. The comparison
  MUST be limited to the marked region so template-specific styling outside it
  is unaffected.
- **FR-007**: The foundation MUST provide a machine-readable routing catalog
  seeded with one entry for each of the 21 planned gallery templates — 20
  derived from upstream templates (4 draft-PR, 3 final-PR, 6 design and
  prototyping, 7 knowledge, report and editor) plus 1 repository-authored UAT
  walkthrough. Each entry MUST carry an identifier unique across the catalog, a
  category, a title, when-to-use guidance, a workflow stage drawn from
  `draft-pr`, `final-pr`, or `ad-hoc`, a routing trigger, attribution to its
  source template, and a shipped status.
- **FR-008**: Routing triggers MUST be expressed as either "always applies" or a
  set of signals drawn from a closed, documented vocabulary. Automated
  validation MUST reject any trigger that names a signal outside that
  vocabulary or that uses an unrecognized trigger form. No expression language,
  operators, or evaluator are to be introduced.
- **FR-009**: Each catalog entry's status MUST be either `planned` or `shipped`.
  Automated validation MUST require the named artifact file to exist for
  `shipped` entries, MUST NOT require it for `planned` entries, and MUST fail if
  a gallery artifact file exists that no entry claims.
- **FR-010**: The foundation MUST document the single-file contract every
  gallery artifact obeys — all behavior, styling, and data inline in one file;
  correct rendering when opened directly from the filesystem with no errors
  reported; and the shape and field meanings of the routing catalog, since the
  catalog format itself cannot carry explanatory notes.
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
- **Projected reviewable LOC**: 435 (excludes regenerated payload and proof
  artifacts, which are declared generated)
- **Projected production files**: 5 net-new shipped foundation files
- **Projected total files**: 8 (5 shipped, 1 validation module, 1 suite registry
  update, plus regenerated payload/proof artifacts)
- **Budget result**: warning accepted
- **Split decision**: Remains one spec. The post-interview estimator returned
  435 projected LOC with status `warn` and suggested 2 slices; the split was
  declined under the product plan's 1.5x greenfield allowance for net-new-only
  slices, which sets the warn threshold at 600 for this class of work. The
  feature is one thin vertical slice — tokens, then catalog, then validation —
  and most of the volume is declarative token declarations and catalog rows
  rather than logic. Splitting kit from catalog was rejected because the second
  slice's validation would import the first slice's marked blocks, so the two
  would not be independent, and the split would double the wait for the four
  blocked port specs.

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
  routing trigger, source attribution, shipped status, and the artifact file it
  refers to. The catalog holds 21 of these; ports change only the status.
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
- **SC-007**: 100% of the token set's text-on-surface pairings meet WCAG AA
  contrast — at least 4.5:1 for body text and 3:1 for large text and meaningful
  non-text elements — measured separately for the light and dark themes.
- **SC-008**: Zero external hosts other than the two permitted font hosts appear
  in a resource-loading position across the entire gallery, while links a reader
  can click and addresses in comments or visible text continue to pass.
- **SC-009**: The four blocked template-port specs can begin work using only the
  artifacts this feature delivers, with no additional foundation decisions
  required of them.

## Assumptions

- The exact closed vocabulary of routing signals is deliberately deferred to
  planning, where it will be derived in one pass from the when-to-use semantics
  of all 21 seeded entries. This spec fixes the requirement — a closed,
  documented vocabulary whose violations are rejected — not the token list.
- Field-level catalog details (exact field names, whether a schema-version field
  is carried, and the category vocabulary) are deferred to planning. The
  expectation is that the catalog's shape is documented alongside the
  single-file contract, because the catalog format cannot carry inline
  explanation, and that it is enforced by the repository's validation rather
  than by a separate formal schema document.
- The catalog is seeded at 21 entries because that is the full planned gallery:
  4 draft-PR, 3 final-PR, 6 design and prototyping, and 7 knowledge, report and
  editor templates derived from upstream sources, plus 1 repository-authored UAT
  walkthrough. If a later spec adds a template, it adds an entry; this feature
  does not reserve slack.
- Brand typefaces are Space Grotesk for headings, Geist for body, and Fira Code
  for monospace, loaded as linked web fonts with swap behavior so text is
  readable before fonts arrive. Font files are not embedded in artifacts —
  embedding was rejected in the product plan on artifact-size grounds.
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

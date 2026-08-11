# Tasks: Draft-PR Template Set (ART-002)

**Input**: Design documents from `specs/art-002-draft-pr-template-set/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/slot-inventory-contract.md`, `contracts/export-payload-contract.md`,
`quickstart.md`

**Tests**: Included, and required rather than optional. FR-036, FR-036a, and
FR-037 make automated validation part of the feature, and `plan.md`'s *Slice 1
Ordering* fixes it as RED first. Phase 2 is that RED.

**Reviewability**: Each slice measures **warn** — ~530 reviewable authored
template lines against a 400 warn and an 800 block, 3 production files against a
6-file warn, 6 authored files in slice 1 and 3 in slice 2 against a 15-file warn,
one primary surface. Slice 1 also carries the ~250-line validation module, which
the budget counts separately on the harness/adapter surface rather than in the
template line count; counted in, slice 1 is ~755 and still below the 800 block,
so the verdict is `warn` on either reading. A warn proceeds on a recorded scope
budget and a recorded
split decision, and both exist (`plan.md` *Reviewability Projection*, `spec.md`
*Reviewability Budget*). T006 is the checkpoint that records it before
implementation. No `Reviewability-Exception` pragma is claimed. Task generation
does not widen the budget: every task below lands in one of the authored files
already declared for its slice in `plan.md` *Declared File Operations* — six in
slice 1, three in slice 2.

**Organization**: Tasks are grouped by user story. Delivery is two sequential
pull requests (FR-040): **slice 1** is US1 and US2 on this branch, **slice 2** is
   US3 and US4 on `art-002-draft-pr-template-set-slice-2`, cut from this branch once PR 1 is open, with PR 2 targeting this branch.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallel-safe **against the other template in the same slice**, which
  is a different file. Tasks inside one story still run in order, because they
  all edit that story's single artifact file. The shared Layer 4 module (Phase 2)
  and every task touching `speckit-pro/artifact-gallery/manifest.json`,
  `tests/speckit-pro/suite-manifest.json`, or a generated artifact carry no `[P]`.
- **[Story]**: `[US1]`…`[US4]`. Setup, Foundational, closeout, and boundary tasks
  carry none.
- Every task names its file path and the requirements it discharges.

## Path Conventions

Repository-root-relative throughout.

- Shipped artifacts: `speckit-pro/artifact-gallery/templates/<id>.html`, where
  `<id>` is exactly the routing catalog identifier.
- Routing catalog: `speckit-pro/artifact-gallery/manifest.json`.
- Repository-only validation: `tests/speckit-pro/unit/`.
- Upstream sources are fetched read-only into the session scratchpad. **No
  upstream byte is ever staged or committed.**

---

## Phase 1: Setup (Shared Infrastructure) — slice 1 branch

**Purpose**: Establish the baseline, the shared inputs both slice-1 templates
embed, and the sample-content decision all four templates depend on.

- [x] T001 Record the pre-change baseline by running `python3 tests/speckit-pro/run-all.py` from the repository root and writing the pass count into the Tasks Results table of `docs/ai/specs/.process/ART-002-workflow.md`. Acceptance: zero failures before any edit; `quickstart.md` expects 7226/7226 (Layer 1 1447, Layer 4 5593, Layer 5 186), and every later count grows rather than shrinks.
- [x] T002 Install the docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile`. Acceptance: exits zero. Required before the `pnpm --dir docs-site reference:generate` in T015 and T043. It carries to slice 2: T048 switches branches inside this worktree rather than creating a new one, so T076 inherits this install.
- [x] T003 Pin the one invented feature every slot's sample content describes, and record it in the Tasks Results notes of `docs/ai/specs/.process/ART-002-workflow.md`: identifier **`NIMBUS-101`**, name **Offline Draft Sync**. Acceptance: `grep -rl 'NIMBUS' docs/ai/specs/ specs/ | grep -v 'ART-002\|art-002'` returns nothing, so the identifier sits outside every namespace this repository's roadmap uses and a reviewer confirms the fiction by reading the identifier rather than by judging tone. The exclusion is required, not a loophole: the pin itself was recorded in `docs/ai/specs/.process/ART-002-workflow.md` at task-generation time, so an unfiltered grep now matches this feature's own records and the check would fail against itself. All four templates reuse this one feature verbatim (FR-014a, SC-004).
- [x] T004 Extract the two canonical blocks to the session scratchpad for byte-for-byte embedding: the `BRAND-KIT` region (318 lines, markers included) from `speckit-pro/artifact-gallery/brand-kit.css`, and the `GALLERY-HEAD` region (140 lines, markers included) from `speckit-pro/artifact-gallery/theme-toggle.html`. Acceptance: neither source file is modified — `git status --short speckit-pro/artifact-gallery/` shows them clean (FR-002, FR-009).
- [x] T005 Confirm the payload build carries a new `templates/` subdirectory with no source change, by reading `speckit-pro/speckit_pro_runner/gates/payloads.py` and verifying `artifact-gallery` is copied as a whole directory name rather than by an enumerated file list. Acceptance: the reading is recorded in the workflow file; if the build enumerates files instead, stop and raise it before authoring any template (FR-039).
- [x] T006 Record the reviewability checkpoint in `docs/ai/specs/.process/ART-002-workflow.md` before implementation begins: the measured per-slice budget (~530 reviewable template LOC, 3 production files, 6 authored files in slice 1 and 3 in slice 2, plus slice 1's ~250-line validation module counted separately, one primary surface), the **warn** verdict, and the two-stacked-PR split decision from `plan.md` and `research.md` D7, together with FR-040's recorded supersession and its reason. Acceptance: no `Reviewability-Exception` pragma is recorded, and the split decision names slice 1 as US1+US2 targeting `main` and slice 2 as US3+US4 targeting the slice-1 branch, and the supersession is recorded with its reason rather than the old shape being silently dropped (FR-040).

**Checkpoint**: Baseline green, canonical blocks in hand, sample feature pinned.

---

## Phase 2: Foundational (Blocking Prerequisites) — the Layer 4 fill-region module

**Purpose**: The validation both slice-1 templates are measured by. It lands
whole in slice 1 and slice 2 edits none of it (`research.md` D8).

**CRITICAL**: No user story work begins until T016 passes. **No task in this
phase carries `[P]`** — every one edits `tests/speckit-pro/unit/test-artifact-fill-regions.py`,
the single file both templates are measured by.

- [x] T007 Create `tests/speckit-pro/unit/test-artifact-fill-regions.py` holding the two pinned literals and the six synthetic-fixture cases, with every check function left unimplemented. The floor literal names all four templates from the start — implementation-plan `phases`/`data-flow`/`mockups`/`risk-register`/`task-inventory`, spec-explainer `tldr`/`goals`/`non-goals`/`acceptance-criteria`/`clarification-faq`, code-approaches `approaches`, module-map `module-graph`; the list-slot literal names implementation-plan `phases`, code-approaches `approaches`, module-map `modules`. Each fixture builds a small gallery in a temporary directory and asserts a detection: a missing floor slot, an inventory entry with no marker pair, a marker pair absent from the inventory, a malformed inventory line, a repeated item with no anchor, a duplicated anchor. Acceptance: `python3 tests/speckit-pro/unit/test-artifact-fill-regions.py` exits **non-zero** with a failure naming each fixture. **This is the RED**, and it does not depend on any template existing (FR-036, FR-036a, FR-037, `quickstart.md` Scenario 1).
- [x] T008 Implement the single `html.parser` subclass in `tests/speckit-pro/unit/test-artifact-fill-regions.py`: `handle_comment` collects parser-recognized comments in document order and toggles which slot is currently open, `handle_starttag` records elements opened inside the open region, and a depth counter identifies which of them sit at the region's own top level. Acceptance: marker-shaped text inside a `script` element is raw character data and registers as no slot, proven by a fixture; Python 3.11+ standard library only, no Bash, no `jq`, no subprocess (FR-037, Constitution II).
- [x] T009 Implement checks **R1** and **R6** in `tests/speckit-pro/unit/test-artifact-fill-regions.py`. R1: for every template whose catalog entry reads `shipped`, each slot in that template's floor set is present as a marker pair — a **subset** check, so a template may carry more slots than the floor names. R6: every template identifier the floor literal names is an identifier `speckit-pro/artifact-gallery/manifest.json` carries. Acceptance: the missing-floor-slot fixture now fails the fixture's expectation of a pass and passes its expectation of a detection (FR-036).
- [x] T010 Implement checks **R2** and **R3** as two separate check functions in `tests/speckit-pro/unit/test-artifact-fill-regions.py`. R2: every slot named in the file's inventory has exactly one marker pair in the body, start before end. R3: every marker pair in the body is named in the inventory. Acceptance: they stay separate — either direction alone misleads the authoring agent, and one check reporting both would name the wrong defect half the time (FR-011, FR-013).
- [x] T011 Implement check **R4** in `tests/speckit-pro/unit/test-artifact-fill-regions.py`: the inventory is a single parser-recognized comment placed immediately after the attribution header; it carries none of the attribution header's own labels or literals (`Upstream repository:`, `Upstream file:`, `License:`, `License text:`, `Modified derivative:`, the upstream repository name, the copyright line); each line reads `Slot: … | Fills: … | Source: …` in that order with no pipe inside any value; names match `^[a-z0-9]+(-[a-z0-9]+)*$` and are unique within the template; every `Source:` value is drawn from the closed set `spec.md`, `plan.md`, `tasks.md`, `research.md`, `design-concept.md`, comma-separated when a slot draws on two. Acceptance: the malformed-inventory-line fixture detects (FR-012, FR-015).
- [x] T012 Implement check **R5** in `tests/speckit-pro/unit/test-artifact-fill-regions.py` as its own assertion, **not** folded into R1 and **not** an extra floor entry. In every slot the list-slot literal names, each element opened at the region's own top level carries an `id` matching `<slot>-<item-slug>`, ids are unique document-wide, and the region holds at least two such elements. Acceptance: both the missing-anchor and the duplicated-anchor fixtures detect; the floor literal is unchanged, so every floor entry still traces to the roadmap and to nothing else (FR-036a, `research.md` D4).
- [x] T013 Wire the real-gallery case class in `tests/speckit-pro/unit/test-artifact-fill-regions.py`: it takes the gallery root as a parameter and runs against the shipped tree, with each per-template case conditioned on that template's catalog `status` rather than on file presence. Acceptance: with all four entries reading `planned`, the real-gallery cases report nothing and the module still passes on its fixtures alone; the conditioning key is `status`, so slice 2's two flips turn the remaining cases on with no edit to this file (`research.md` D8).
- [x] T014 Register the module in `tests/speckit-pro/suite-manifest.json` under layer 4 with `"path": "tests/speckit-pro/unit/test-artifact-fill-regions.py"`, `"label": "test-artifact-fill-regions"`, `"baseline": null`. Acceptance: `python3 tests/speckit-pro/run-all.py --layer 4` dispatches the module and its unit count appears in the layer total (FR-037, Constitution IV).
- [x] T015 Regenerate `docs-site/src/content/docs/reference/tests.md` with `pnpm --dir docs-site reference:generate` and commit the result. Acceptance: the generated page lists the new module; the file is never hand-edited (`AGENTS.md` *Editing Boundaries*).
- [x] T016 Prove the module is green before any template exists: run `python3 tests/speckit-pro/run-all.py`. Acceptance: zero failures; the fixture cases assert real detections; the real-gallery cases report nothing because no entry reads `shipped` yet, and that silence is correct and temporary (`quickstart.md` Scenario 1).

**Checkpoint**: Validation exists, went RED for a real reason, and is green on
fixtures. US1 and US2 may now start, and may run in parallel.

---

## Phase 3: User Story 1 - Implementation Plan template (Priority: P1) 🎯 MVP — slice 1

**Goal**: The template the draft-PR stage routes every time, carrying the phases,
the data-flow drawing, the mockups, the risk register, and the task inventory,
with a per-phase objection capture and two exports.

**Independent Test**: Open `speckit-pro/artifact-gallery/templates/implementation-plan.html`
straight from a local filesystem with the network off. Confirm it renders
complete, attach objections to two different phases, invoke each export, and
confirm the produced text carries both objections, each naming the phase it
attaches to, and nothing the reader did not write.

- [x] T017 [P] [US1] Fetch upstream `16-implementation-plan.html` read-only into the session scratchpad. Acceptance: the fetch is read-only network access, the bytes stay in the scratchpad, and `git status --short` shows no new untracked upstream file anywhere in the worktree.
- [x] T018 [P] [US1] Create `speckit-pro/artifact-gallery/templates/implementation-plan.html` and lay in its shell: the document language declaration, a page title naming the artifact and the feature (`Implementation Plan — NIMBUS-101 Offline Draft Sync`), the `GALLERY-HEAD` block as a direct child of the head element with nothing content-bearing before it except the character-encoding declaration, the `BRAND-KIT` block, and the attribution header carrying the contract's five labels plus the verbatim copyright line, with `Upstream file:` equal to this entry's `source.file` (`16-implementation-plan.html`) and `Upstream repository:` equal to the single repository `speckit-pro/artifact-gallery/SPA-CONTRACT.md` names. Acceptance: both canonical regions are byte-identical to T004's extracts including their markers, each appearing exactly once with start before end (FR-001, FR-002, FR-003, FR-035a).
- [x] T019 [P] [US1] Add the seven-line slot inventory comment to `speckit-pro/artifact-gallery/templates/implementation-plan.html`, as a single HTML comment placed **immediately after the attribution header** and outside every fill region, carrying **none** of the header's own labels or literals so the gallery scanner cannot mistake it for the header. Lines in document order: `feature-header` (spec.md), `plan-stats` (plan.md), `phases` (plan.md), `data-flow` (plan.md), `mockups` (design-concept.md), `risk-register` (plan.md, research.md), `task-inventory` (tasks.md), each written `Slot: … | Fills: … | Source: …` with no pipe inside a value. Acceptance: R4 and R2/R3 pass against this file (FR-012, FR-013, FR-015).
- [x] T020 [P] [US1] Port and brand the five lifted regions in `speckit-pro/artifact-gallery/templates/implementation-plan.html`, each wrapped in its own `<!-- FILL:<slot>:START -->` … `<!-- FILL:<slot>:END -->` pair and each shipping NIMBUS-101 worked-example content: `feature-header` from the page-head eyebrow and title, `plan-stats` from the four-cell summary strip, `phases` from the milestones section, `mockups` from the mockups section, `risk-register` from the risks-and-mitigations section with a non-color carrier on the severity marker. Drop the prompt box, the key-code section, and the open-questions section, taking their dependents with them — no heading left standing over nothing, no caption without its figure, no in-page link into a region that is gone. Acceptance: regions are flat, no pair encloses another, every color pairing is one the brand kit's published audit clears, and `--rc-border-subtle` carries no meaning (FR-011, FR-014, FR-015, FR-026, FR-031, FR-032).
- [x] T021 [P] [US1] Author the `task-inventory` region fresh in `speckit-pro/artifact-gallery/templates/implementation-plan.html`, reusing the key-code grid's layout shape with new NIMBUS-101 content, wrapped in its own marker pair. Acceptance: it has no upstream content counterpart and copies none; the region is inert content only (FR-014, FR-015, FR-026).
- [x] T022 [P] [US1] Give every phase item inside the `phases` region of `speckit-pro/artifact-gallery/templates/implementation-plan.html` a stable anchor `id="phases-<item-slug>"` at the region's own top level, derived from that item's visible label under the slot-name character rules. Acceptance: at least two items, ids unique document-wide, R5 passes; the region carries anchors and inert content and **no** reader-input control markup (FR-015, FR-016a, FR-036a).
- [x] T023 [P] [US1] Restyle the ported data-flow drawing inside the `data-flow` region of `speckit-pro/artifact-gallery/templates/implementation-plan.html`. **Add class hooks to the shapes first, then style through them** — never one blanket selector, which would flatten the drawing's two-tier text hierarchy and its inverted persistence node. Give each arrowhead its own selector, because a marker renders in its own context and does not inherit paint from the element referencing it. Retain no upstream color value. Retain the drawing's absolute namespace declaration, which is exempt from the external-reference scan. Port the dashed edge and its caption intact. Give the inverted persistence node a text tag or a distinct shape and drop the unaudited accent on its sub-label. Acceptance: the drawing reads correctly in both themes; no text sits on a fill the audit does not measure (FR-030, FR-031, FR-032).
- [x] T024 [P] [US1] Give the data-flow drawing an accessible name, and place a text equivalent of what it conveys **outside the drawing element and inside the same `data-flow` fill region**, in `speckit-pro/artifact-gallery/templates/implementation-plan.html`. Acceptance: the equivalent describes NIMBUS-101, so it is slot content that a fill replaces along with the drawing; it is not left outside the marker pair, where a filled artifact would carry a fictional description of a real drawing (FR-030a).
- [x] T025 [P] [US1] Build the objection disclosures in the inline script of `speckit-pro/artifact-gallery/templates/implementation-plan.html`, at load. Each is **created as document elements — element creation, attributes set by name, text set through the text-valued property** — and **never** assembled as a markup string, because the repository's construct scan parses markup only out of single-line script string literals and a multi-line markup string would bypass every construct check silently. Resolve each item's anchor by identifier lookup, never by concatenating the value into a selector string. Mount each disclosure onto its phase's anchor and insert it immediately after that anchor, so tab order follows visible order with no positive tab index. The disclosure starts **closed**; its own control states in text whether that item currently carries a note; the note text sits in the control's own accessible name; the default marker glyph is not removed without an equally visible open/closed indicator in its place. Each control's accessible name carries the shared routine text plus its own item's visible label. An item carries a note when its field holds at least one non-whitespace character and only then, and the state text follows the field's current value rather than its value at the last collapse. Acceptance: two disclosures open independently — opening one never closes another (FR-004, FR-015, FR-016, FR-016a, FR-017a, FR-018, FR-033).
- [x] T026 [P] [US1] Build the export path in the inline script of `speckit-pro/artifact-gallery/templates/implementation-plan.html`: exactly one control per export kind the catalog entry declares, labelled "Copy as prompt" and "Copy as Markdown", both controls placed **outside** every fill region so a fill cannot delete them; both payloads derived from live state at the moment of invocation; the two pinned header lines `Artifact: <artifact title>` and `Feature: <feature id> <feature name>` emitted in every state including the empty one; one item reference line per recorded objection reading `<slot> / <item label>  (#<anchor>)` with two spaces before the parenthesis; **no line, placeholder, or count for an item left empty**; the empty-state bodies verbatim from `contracts/export-payload-contract.md` — `No objection was recorded. There is nothing here to act on. Do not treat this as approval.` for prompt and `No objection was recorded. This record is not an approval.` for markdown. Add one `role="status"` region present in the document from load, outside every fill region, cleared and rewritten rather than assigned the same string over itself, carrying the pinned success messages. On any clipboard failure use the one cause-neutral message `Copy failed. The text is in the field below. Select it and copy it by hand.`, reveal byte-identical text in a field populated through its **text value** rather than as markup, place that field **outside** every fill region, keep it focusable and not disabled, move focus to it, give it its own programmatic label and tie the failure message to it as its description, and make no deprecated second copy attempt. No script string literal in this file may be URL-shaped. Acceptance: every export carries the anchor and nothing else the reader could not see, and with nothing recorded neither export states a conclusion — which is SC-005 measured on this template (FR-004, FR-011, FR-019, FR-021, FR-022, FR-023, FR-024, FR-025, FR-033, SC-005).
- [x] T027 [P] [US1] Place the four small authored elements in `speckit-pro/artifact-gallery/templates/implementation-plan.html`, two of which sit on **opposite** sides of the fill boundary and are easy to get backwards. **Inside** the `feature-header` region: the notice that what follows is sample content awaiting a fill, so the first fill removes it. **Outside** every fill region, in the document's own header chrome: the opt-in empty brand-mark element, exactly once, so a fill cannot delete it — and the template neither authors, replaces, nor wraps the theme control, and never reads the stored theme value. Beside the export pair and **outside** every fill region: one line saying what each export is for (prompt for a coding agent, Markdown for a pull-request comment) and one line saying recorded input is not saved and is lost on reload. Acceptance: a filled artifact keeps the mark and both export lines and loses only the notice — check it by deleting each region's contents in a scratch copy and confirming what remains (FR-011, FR-014a, FR-018a, FR-019, FR-035).
- [x] T028 [P] [US1] Set the heading structure of `speckit-pro/artifact-gallery/templates/implementation-plan.html`: exactly one top-level heading, no skipped rank anywhere, and each slot's shipped sample content modelling the heading ranks a filled region is expected to keep. Acceptance: the outline a reader navigates by matches the document they see; no inventory field records this, because FR-012 fixes the line at three labels (FR-035b).
- [x] T029 [US1] Flip `implementation-plan`'s `status` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json` **in the same change as the file**, changing no other value in that entry and no other entry, then run `python3 tests/speckit-pro/run-all.py --layer 4`. No `[P]`: this file is shared with US2. Acceptance: zero failures; the fill-region module's real-gallery cases now bind on this template; the gallery scanner passes it for canonical blocks, attribution agreement, prohibited constructs including inside script string literals, external references (the typeface request is the only one), and payload-rewriter relative references (FR-004, FR-005, FR-007, FR-008, FR-010).

**Checkpoint**: US1 is complete and independently testable.

---

## Phase 4: User Story 2 - Spec Explainer template (Priority: P2) — slice 1

**Goal**: The second unconditionally routed template — a read-only explainer with
no capture, no export, and no script of its own.

**Independent Test**: Open `speckit-pro/artifact-gallery/templates/spec-explainer.html`
from a local filesystem, confirm every section renders, confirm the acceptance
criteria collapse and expand by keyboard, and confirm the document offers no
export or capture control anywhere.

Every `[P]` task below is parallel-safe against Phase 3, which edits a different
file.

- [x] T030 [P] [US2] Fetch upstream `14-research-feature-explainer.html` read-only into the session scratchpad. Acceptance: read-only network access, bytes stay in the scratchpad, `git status --short` shows no new untracked upstream file.
- [x] T031 [P] [US2] Create `speckit-pro/artifact-gallery/templates/spec-explainer.html` and lay in its shell: document language, a page title naming the artifact and the feature (`Spec Explainer — NIMBUS-101 Offline Draft Sync`), `GALLERY-HEAD` as a direct child of head with only the character-encoding declaration before it, `BRAND-KIT`, and the attribution header with `Upstream file: 14-research-feature-explainer.html`. Acceptance: both canonical regions byte-identical to T004's extracts including markers, exactly once each, start before end (FR-001, FR-002, FR-003, FR-035a).
- [x] T032 [P] [US2] Add the six-line slot inventory comment to `speckit-pro/artifact-gallery/templates/spec-explainer.html`, immediately after the attribution header, outside every fill region, carrying none of the header's labels or literals: `feature-header` (spec.md), `tldr` (spec.md), `goals` (spec.md), `non-goals` (design-concept.md, spec.md), `acceptance-criteria` (spec.md), `clarification-faq` (spec.md, design-concept.md). Acceptance: R4 and R2/R3 pass against this file (FR-012, FR-013, FR-015).
- [x] T033 [P] [US2] Port and brand the three lifted regions in `speckit-pro/artifact-gallery/templates/spec-explainer.html`, each in its own marker pair with NIMBUS-101 worked-example content: `feature-header` from the header eyebrow and title, `tldr` from the TL;DR block, `clarification-faq` from the FAQ definition list. Drop the prompt box, the navigation, the step content, the configuration tabs, and the gotchas, leaving no orphan heading, no caption without its figure, and no in-page link into a dropped region — the navigation earns its drop twice, because five of its nine links target the same anchor. Acceptance: regions flat, every color pairing drawn from the brand kit's published audit (FR-011, FR-014, FR-015, FR-027, FR-031).
- [x] T034 [P] [US2] Author `goals` and `non-goals` fresh in `speckit-pro/artifact-gallery/templates/spec-explainer.html` as **two separate slots**, each with its own marker pair and its own NIMBUS-101 content. Acceptance: they are not merged into one compound region — FR-036's floor names both, and a single region would leave one half unprotected (FR-014, FR-015, FR-027).
- [x] T035 [P] [US2] Author the `acceptance-criteria` region in `speckit-pro/artifact-gallery/templates/spec-explainer.html` using the native disclosure shape borrowed from upstream's step list, which needs no script and exposes its own state. Acceptance: it carries **no** state text, unlike the objection disclosures on the other templates, because there is nothing here for a reader to record; it expands and re-collapses by keyboard alone (FR-014, FR-027, FR-033).
- [x] T036 [P] [US2] Drop or reduced-motion-guard the one unguarded transform transition carried over from upstream in `speckit-pro/artifact-gallery/templates/spec-explainer.html`. Acceptance: with reduced motion requested, nothing animates and nothing transitions when a folded section expands or the theme switches (FR-034).
- [x] T037 [P] [US2] Place the two opposite-placement elements in `speckit-pro/artifact-gallery/templates/spec-explainer.html`: the "this is sample content awaiting a fill" notice **inside** the `feature-header` region, and the opt-in empty brand-mark element exactly once in the header chrome **outside** every fill region. The template neither authors, replaces, nor wraps the theme control and never reads the stored theme value. Acceptance: this template carries these two and neither export notice, having nothing to record and nothing to export; the mark survives a fill and the notice does not (FR-011, FR-014a, FR-035).
- [x] T038 [P] [US2] Set the heading structure of `speckit-pro/artifact-gallery/templates/spec-explainer.html`: exactly one top-level heading, no skipped rank, each slot's sample content modelling the ranks a filled region keeps (FR-035b).
- [x] T039 [P] [US2] Verify the read-only declaration is **structural** in `speckit-pro/artifact-gallery/templates/spec-explainer.html`: no export control, no copy affordance, no field that records reader input, no anchor-bearing list slot, and **no script of its own** — the canonical head block is the only script in the file. Acceptance: a grep for a script element returns only the canonical block's, and the fill-region module's list-slot literal names no slot for this template (FR-020).
- [x] T040 [US2] Flip `spec-explainer`'s `status` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json` in the same change as the file, changing no other value, then run `python3 tests/speckit-pro/run-all.py --layer 4`. No `[P]`: this file is shared with US1, so the two flips serialize even though the two templates do not. Acceptance: zero failures; the gallery scanner passes the file for canonical blocks, attribution, prohibited constructs, external references, and payload-rewriter references (FR-004, FR-005, FR-007, FR-008, FR-010).

**Checkpoint**: US1 and US2 both work independently. Slice 1 is feature-complete.

---

## Phase 5: Slice 1 closeout — PR 1

**Purpose**: Everything that makes slice 1 shippable, none of which is
template-authoring. No `[P]`: these tasks touch shared and generated files.

- [x] T041 Verify scope conformance for slice 1 with `git diff --name-only origin/main...HEAD`. Acceptance: no shared foundation file appears — not `speckit-pro/artifact-gallery/brand-kit.css`, `theme-toggle.html`, `SPA-CONTRACT.md`, `UPSTREAM-NOTICE.md`, nor the routing signal vocabulary — and `git diff origin/main...HEAD -- speckit-pro/artifact-gallery/manifest.json` shows exactly two changed lines, both `status` values (FR-008, FR-009, SC-009).
- [x] T042 Regenerate the payload and proof artifacts with `python3 scripts/refresh-release-artifacts.py`, then run it a second time. Acceptance: the first run produces the `dist/claude` and `dist/codex` template copies and manifest updates, the installed-cache mirrors under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`, and the `.process/` proof snapshots; the second run produces no further change, which is what distinguishes a clean regeneration from a partial one; `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and its `.sha256` do **not** appear dirty, because this feature edits no runner source (FR-039, `quickstart.md` Scenario 4).
- [x] T043 Re-run `pnpm --dir docs-site reference:generate` after the templates land and inspect `git status --short docs-site/`. Acceptance: no change beyond what T015 already committed, because the templates live outside `tests/speckit-pro/`; confirm the empty result rather than assuming it (`quickstart.md` Scenario 5).
- [x] T044 Run the full gate `python3 tests/speckit-pro/run-all.py`. Acceptance: zero failures and a total above the 7226 baseline by the fill-region module's own unit count; Layer 1 green, which is what proves the new `templates/` subdirectory disturbed neither the plugin layout nor the generated spec index (SC-007, Constitution IV).
- [x] T045 Provoke the two contract guards once each and restore immediately, per `quickstart.md` Scenario 2: flip a `status` to `shipped` with no file present and confirm the gallery scanner fails on a missing artifact; add a file with no `status` flip and confirm it fails as an orphan. Acceptance: both fail as described and both provocations are reverted, leaving `git status --short` clean of them (FR-010).
- [x] T046 Write the acceptance runbook for the two slice-1 templates as numbered steps with observable results, one set per template, in the feature's acceptance runbook, from the manual table in `quickstart.md`. Cover opening from a local filesystem with a clean console, the offline reload with only a typeface difference, the theme control including a refused-storage outcome, keyboard reachability of every control with a visible focus indicator, the sample content and its fictional identifier, the two export notices, disclosure state text, two disclosures open at once, both exports with something recorded and with nothing recorded, the clipboard-refusal path, the spec-explainer's absence of any control or script, its keyboard-only fold, reduced motion, and the drawing's accessible name and text equivalent. Two steps carry a timed observable rather than a yes/no: carrying a recorded conclusion out of the document in a single action takes under thirty seconds with nothing retyped, in every destination the entry declares (SC-002), and the export with nothing recorded states no conclusion and shows no value the reader could not see (SC-005). Acceptance: every step names a result an operator can confirm or reject without help, and one template's pass completes in under ten minutes; no automated browser is introduced (FR-006, FR-024, FR-033, FR-038, SC-001, SC-002, SC-005, SC-006, SC-008).
- [x] T047 Assemble the PR 1 review packet in the pull-request description: what changed, why, non-goals, review order, scope budget, traceability mapping US1 and US2 and each success criterion they carry to the changed files and their verification evidence, verification evidence, known gaps, and rollback notes (the slice is additive plus a two-value catalog flip, so reverting the commit restores the prior state with no migration). Name the deferred work: US3 and US4 go to slice 2, and generation of the slot content goes to ART-007 — together with the two obligations `spec.md` *Dependencies* hands it, the anchor integrity of a filled artifact and the document-title rewrite. Acceptance: the pull request is created with `--base main --head art-002-draft-pr-template-set`, opened ready for review rather than draft, its title is `feat(speckit-pro): add the implementation-plan and spec-explainer gallery templates`, and its body carries a `## Release note` section after `## Known Gaps` holding exactly one non-empty ` ```release-note ` fence, placed outside every `speckit-pro-editable` marker pair. Before `gh pr create` runs, `PR_TITLE='<that title>' PR_BODY="$(cat <the emitted body file>)" PR_LABELS_JSON='[]' PR_DRAFT=false python3 scripts/compose-release-notes.py --validate-pr` exits 0 (FR-040, Constitution V, `spec.md` *PR Review Packet Requirements*).

**Checkpoint**: PR 1 is open, green, and reviewable. **Slice 1 ends here.**

---

## Phase 6: Slice boundary

  - [x] T048 **Gate**: with PR 1 open and green, create branch `art-002-draft-pr-template-set-slice-2` from the current tip of `art-002-draft-pr-template-set` — the exact commit PR 1 was opened from — and check it out in this worktree. Nothing is merged here. Acceptance: `git rev-parse art-002-draft-pr-template-set-slice-2` equals `git rev-parse art-002-draft-pr-template-set`; `git branch --show-current` reads `art-002-draft-pr-template-set-slice-2`; `speckit-pro/artifact-gallery/manifest.json` on the new branch already reads `shipped` for `implementation-plan` and `spec-explainer`, so slice 2 reapplies neither flip; `tests/speckit-pro/unit/test-artifact-fill-regions.py` is present and unmodified, and slice 2 will edit no test file. Update `docs/ai/specs/.process/autopilot-state.json` `branch` to the slice-2 branch. **No task in Phase 7, 8, or 9 may start before this one passes, and no commit after this one may land on the slice-1 branch** — PR 1's diff and PR 2's base are both fixed at this commit. PR 2 targets the slice-1 branch, which is how slice 2 has slice 1's Layer 4 module without waiting for a human merge (FR-040 as superseded, `research.md` D7, D8).

---

## Phase 7: User Story 3 - Code Approaches template (Priority: P3) — slice 2

**Goal**: Two or more approaches side by side with the deciding trade-off, one
selection across the group, an optional reason, and two exports.

**Independent Test**: Open `speckit-pro/artifact-gallery/templates/code-approaches.html`,
confirm the approaches render side by side, select one, write a reason, invoke
each export, and confirm the text names the chosen approach and the reason. Then
reload, select nothing, and confirm neither export invents a choice.

- [ ] T049 [P] [US3] Fetch upstream `01-exploration-code-approaches.html` read-only into the session scratchpad. Acceptance: read-only network access, bytes stay in the scratchpad, nothing staged.
- [ ] T050 [P] [US3] Create `speckit-pro/artifact-gallery/templates/code-approaches.html` and lay in its shell: document language, a page title naming the artifact and the feature (`Code Approaches — NIMBUS-101 Offline Draft Sync`), `GALLERY-HEAD` as a direct child of head with only the character-encoding declaration before it, `BRAND-KIT`, and the attribution header with `Upstream file: 01-exploration-code-approaches.html`. Both canonical blocks are re-extracted from `speckit-pro/artifact-gallery/brand-kit.css` and `speckit-pro/artifact-gallery/theme-toggle.html` on this branch, neither of which is edited. Acceptance: both regions byte-identical including markers, exactly once each (FR-001, FR-002, FR-003, FR-009, FR-035a).
- [ ] T051 [P] [US3] Add the three-line slot inventory comment to `speckit-pro/artifact-gallery/templates/code-approaches.html`, immediately after the attribution header, outside every fill region, carrying none of the header's labels or literals: `feature-header` (spec.md), `approaches` (research.md, plan.md), `recommendation` (research.md). Acceptance: R4 and R2/R3 pass (FR-012, FR-013, FR-015).
- [ ] T052 [P] [US3] Port and brand the three regions in `speckit-pro/artifact-gallery/templates/code-approaches.html`, each in its own marker pair with NIMBUS-101 content: `feature-header` from the page head minus the prompt box, `approaches` from the approaches grid including its trade-off tables and chip footers, `recommendation` from the recommendation aside. **Wrap** the existing approaches container in the native grouping element rather than replacing it, so the side-by-side layout survives the addition of the single-choice control — and place that grouping element and its visible group label **outside** the `approaches` marker pair, enclosing the region rather than sitting inside it. Inside the pair the first fill would delete both, leaving every filled artifact with ungrouped, unlabelled choices while this shipped template still passed. The group label names the question the reader is answering, not the approaches compared, so it is chrome rather than feature content and FR-015 does not make it a slot. Drop the prompt box with no residue. Port verbatim the three escaped handler-shaped strings inside the displayed sample code: a parse confirms they are text nodes rather than attributes, so they are not prohibited constructs — a reviewer running a naive text search will find all three. Acceptance: two or more approaches render beside one another with the deciding trade-off stated for each; regions flat; every color pairing drawn from the published audit (FR-011, FR-014, FR-015, FR-028, FR-031).
- [ ] T053 [P] [US3] Give every approach inside the `approaches` region of `speckit-pro/artifact-gallery/templates/code-approaches.html` a stable anchor `id="approaches-<item-slug>"` at the region's own top level, derived from that approach's visible label. Acceptance: at least two items, unique document-wide, R5 passes; the region carries anchors and inert content and no control markup (FR-015, FR-016a, FR-036a).
- [ ] T054 [P] [US3] Give the trade-off markers a non-color carrier in `speckit-pro/artifact-gallery/templates/code-approaches.html`, where upstream draws two identical shapes separated only by hue. Declare the persistent column heading and the fixed column position as the carrier, then either drop the markers as redundant or give them distinct glyphs. Acceptance: a single row lifted out of the table still reads, and the distinction survives a monochrome rendering (FR-032, SC-010).
- [ ] T055 [P] [US3] Build the selection controls in the inline script of `speckit-pro/artifact-gallery/templates/code-approaches.html`, at load, **by element creation with attributes set by name and text set through the text-valued property — never by assembling markup as a string**. One native single-choice control per approach, mounted onto that approach's anchor by identifier lookup and inserted immediately after it, the whole set grouped by the native grouping element T052 placed **outside** the `approaches` marker pair and carrying a visible group label as its accessible name; each control's accessible name carries the shared routine text plus its own approach's visible label. Add one **optional** labelled reason field, placed outside every fill region beside the export controls. Acceptance: the selection is reachable and committable by keyboard alone, the selected approach is reported in text, choosing a second replaces the first, no positive tab index is assigned, and nothing this task authors sits inside a fill region except the mounted controls the routine rebuilds at every load (FR-004, FR-011, FR-015, FR-016a, FR-017, FR-017a, FR-033).
- [ ] T056 [P] [US3] Build the export path in the inline script of `speckit-pro/artifact-gallery/templates/code-approaches.html`: one control per declared kind, "Copy as prompt" and "Copy as Markdown", both placed **outside** every fill region; both payloads from live state; the two pinned header lines in every state; the item reference line `<slot> / <item label>  (#<anchor>)` for the current selection only, never a history; `Reason: none given.` when an approach is chosen with no reason, named rather than omitted; the verbatim empty-state bodies `No approach was chosen. There is nothing here to act on. Do not treat this as approval of any approach.` for prompt and `No approach was chosen. This record is not an approval of any approach.` for markdown. Add the `role="status"` region present from load, outside every fill region, cleared and rewritten rather than reassigned, carrying `Copied. Your chosen approach is on the clipboard.` and `Copied. The text says no approach was chosen.`. On any failure use `Copy failed. The text is in the field below. Select it and copy it by hand.`, reveal byte-identical text through the field's text value in a field that sits **outside** every fill region, keep the field focusable and not disabled, move focus to it, label it and tie the failure message to it as its description, and make no second attempt. No script string literal may be URL-shaped. Acceptance: with nothing selected neither export names an approach, and no export carries a value the reader could not see — which is SC-005 measured on this template (FR-004, FR-011, FR-019, FR-021, FR-022, FR-023, FR-024, FR-025, FR-033, SC-005).
- [ ] T057 [P] [US3] Place the four small authored elements in `speckit-pro/artifact-gallery/templates/code-approaches.html`: the sample-content notice **inside** the `feature-header` region; the opt-in empty brand-mark element exactly once in the header chrome **outside** every fill region; and beside the export pair, also **outside** every fill region, one line saying what each export is for and one line saying recorded input is not saved and is lost on reload. The template neither authors, replaces, nor wraps the theme control. Acceptance: the mark, both export lines, the export controls, the status region, and the fallback field all survive a fill and only the notice does not — check it by deleting each region's contents in a scratch copy and confirming what remains (FR-011, FR-014a, FR-018a, FR-019, FR-035).
- [ ] T058 [P] [US3] Set the heading structure of `speckit-pro/artifact-gallery/templates/code-approaches.html`: exactly one top-level heading, no skipped rank, each slot's sample content modelling the ranks a filled region keeps (FR-035b).
- [ ] T059 [US3] Flip `code-approaches`'s `status` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json` in the same change as the file, changing no other value, then run `python3 tests/speckit-pro/run-all.py --layer 4`. No `[P]`: shared with US4. Acceptance: zero failures; the fill-region module's real-gallery cases bind on this template with **no edit to the test file**; the gallery scanner passes it (FR-004, FR-005, FR-007, FR-008, FR-010).

**Checkpoint**: US3 complete and independently testable.

---

## Phase 8: User Story 4 - Module Map template (Priority: P4) — slice 2

**Goal**: The modules a change touches drawn as boxes with the calls between them
as arrows, the path the change runs through distinguished without color, a
per-module objection capture, and two exports.

**Independent Test**: Open `speckit-pro/artifact-gallery/templates/module-map.html`,
confirm the module graph and the distinguished path both render, attach an
objection to one module, invoke each export, and confirm the text carries that
objection with the module it attaches to. Confirm the distinguished path is still
identifiable in a monochrome screenshot.

Every `[P]` task below is parallel-safe against Phase 7, which edits a different
file.

- [ ] T060 [P] [US4] Fetch upstream `04-code-understanding.html` read-only into the session scratchpad. Acceptance: read-only network access, bytes stay in the scratchpad, nothing staged.
- [ ] T061 [P] [US4] Create `speckit-pro/artifact-gallery/templates/module-map.html` and lay in its shell: document language, a page title naming the artifact and the feature (`Module Map — NIMBUS-101 Offline Draft Sync`), `GALLERY-HEAD` as a direct child of head with only the character-encoding declaration before it, `BRAND-KIT`, and the attribution header with `Upstream file: 04-code-understanding.html`. Acceptance: both canonical regions byte-identical including markers, exactly once each (FR-001, FR-002, FR-003, FR-035a).
- [ ] T062 [P] [US4] Add the five-line slot inventory comment to `speckit-pro/artifact-gallery/templates/module-map.html`, immediately after the attribution header, outside every fill region, carrying none of the header's labels or literals: `feature-header` (spec.md), `module-summary` (plan.md), `module-graph` (plan.md), `modules` (plan.md), `key-files` (plan.md). Acceptance: R4 and R2/R3 pass (FR-012, FR-013, FR-015).
- [ ] T063 [P] [US4] Port and brand the four non-drawing regions in `speckit-pro/artifact-gallery/templates/module-map.html`, each in its own marker pair with NIMBUS-101 content: `feature-header` from the header repo line and title, `module-summary` from the summary paragraph, `modules` from the callstack walkthrough, `key-files` from the key-files aside. Drop the gotchas section with no orphan heading or dangling in-page link. Acceptance: regions flat, every color pairing drawn from the published audit (FR-011, FR-014, FR-015, FR-031).
- [ ] T064 [P] [US4] Give every module inside the `modules` region of `speckit-pro/artifact-gallery/templates/module-map.html` a stable anchor `id="modules-<item-slug>"` at the region's own top level, derived from that module's visible label. Acceptance: at least two items, unique document-wide, R5 passes — and note that `modules` is deliberately **not** a floor entry, so this check is the only thing that verifies it (FR-015, FR-016a, FR-036a).
- [ ] T065 [P] [US4] Restyle the ported module drawing inside the `module-graph` region of `speckit-pro/artifact-gallery/templates/module-map.html`. This one already styles through classes, so restyling is a token swap in the rules it has, plus one rule for the arrowhead, which needs its own selector because a marker renders in its own context. Carry the distinguished path by **boundary weight and a visible text tag, never by color** — upstream's fill tint is an unaudited blend over an unknown backdrop and its boundary hue is unaudited, so neither survives. Retain no upstream color value. Place **no marker pair inside the drawing**: the distinguished path is a required property of `module-graph`'s content, and a pair inside the figure would split one drawing across two fill operations sharing a coordinate system. Acceptance: the distinguished path is identifiable in a monochrome rendering (FR-029, FR-030, FR-031, FR-032, SC-010).
- [ ] T066 [P] [US4] Give the module drawing an accessible name, and place a text equivalent of what it conveys **outside the drawing element and inside the same `module-graph` fill region**, in `speckit-pro/artifact-gallery/templates/module-map.html`. Upstream carries a name but marks the drawing so assistive technology reads it as a single image, hiding every label inside it; that marking does not survive. Acceptance: the equivalent describes NIMBUS-101, so a fill replaces it with the drawing (FR-030a).
- [ ] T067 [P] [US4] Drop or reduced-motion-guard the one unguarded transform transition carried over from upstream in `speckit-pro/artifact-gallery/templates/module-map.html`. Acceptance: with reduced motion requested, nothing animates and nothing transitions when a disclosure opens or the theme switches (FR-034).
- [ ] T068 [P] [US4] Neutralize the upstream accordion trap in `speckit-pro/artifact-gallery/templates/module-map.html`. Upstream `04-code-understanding.html` runs a script that force-closes every other `details.snippet` when one opens. That behavior **must not reach the objection disclosures** — it would close a reader's in-progress field the moment they opened another. Either scope it by class so it can never select an objection disclosure, or drop it entirely. Acceptance: with an objection typed into one module's disclosure, opening a second module's disclosure leaves the first open with its text intact (FR-018).
- [ ] T069 [P] [US4] Build the objection disclosures in the inline script of `speckit-pro/artifact-gallery/templates/module-map.html`, at load, **by element creation with attributes set by name and text set through the text-valued property — never by assembling markup as a string**. Resolve each module's anchor by identifier lookup, never by concatenating into a selector string. Mount each disclosure onto its module's anchor and insert it immediately after, so tab order follows visible order with no positive tab index. Start closed; the control states in text whether that module carries a note; the note text sits in the control's own accessible name; the default marker glyph is not removed without an equally visible open/closed indicator in its place; each accessible name carries the shared routine text plus the module's own visible label. A note is at least one non-whitespace character, and the state text follows the field's current value. Acceptance: the shape matches US1's, and T068's scoping holds (FR-004, FR-015, FR-016, FR-016a, FR-017a, FR-018, FR-033).
- [ ] T070 [P] [US4] Build the export path in the inline script of `speckit-pro/artifact-gallery/templates/module-map.html`: one control per declared kind, "Copy as prompt" and "Copy as Markdown", both placed **outside** every fill region; both payloads from live state; the two pinned header lines in every state; one item reference line `<slot> / <item label>  (#<anchor>)` per recorded objection and **no line, placeholder, or count for a module left empty**; the verbatim empty-state bodies `No objection was recorded. There is nothing here to act on. Do not treat this as approval.` for prompt and `No objection was recorded. This record is not an approval.` for markdown. Add the `role="status"` region present from load, outside every fill region, cleared and rewritten rather than reassigned, carrying the pinned counted success messages. On any failure use `Copy failed. The text is in the field below. Select it and copy it by hand.`, reveal byte-identical text through the field's text value in a field that sits **outside** every fill region, keep the field focusable and not disabled, move focus to it, label it and tie the failure message to it as its description, and make no second attempt. No script string literal may be URL-shaped. Acceptance: every export carries the anchor and nothing else the reader could not see, and with nothing recorded neither export states a conclusion — which is SC-005 measured on this template (FR-004, FR-011, FR-019, FR-021, FR-022, FR-023, FR-024, FR-025, FR-033, SC-005).
- [ ] T071 [P] [US4] Place the four small authored elements in `speckit-pro/artifact-gallery/templates/module-map.html`: the sample-content notice **inside** the `feature-header` region; the opt-in empty brand-mark element exactly once in the header chrome **outside** every fill region; and beside the export pair, also **outside** every fill region, one line saying what each export is for and one line saying recorded input is not saved and is lost on reload. The template neither authors, replaces, nor wraps the theme control and never reads the stored theme value. Acceptance: the mark, both export lines, the export controls, the status region, and the fallback field all survive a fill and only the notice does not — check it by deleting each region's contents in a scratch copy and confirming what remains (FR-011, FR-014a, FR-018a, FR-019, FR-035).
- [ ] T072 [P] [US4] Set the heading structure of `speckit-pro/artifact-gallery/templates/module-map.html`: exactly one top-level heading, no skipped rank, each slot's sample content modelling the ranks a filled region keeps (FR-035b).
- [ ] T073 [US4] Flip `module-map`'s `status` from `planned` to `shipped` in `speckit-pro/artifact-gallery/manifest.json` in the same change as the file, changing no other value, then run `python3 tests/speckit-pro/run-all.py --layer 4`. No `[P]`: shared with US3. Acceptance: zero failures; the real-gallery cases bind with no edit to the test file; the gallery scanner passes it (FR-004, FR-005, FR-007, FR-008, FR-010).

**Checkpoint**: All four templates are shipped and independently functional.

---

## Phase 9: Slice 2 closeout — PR 2

  - [ ] T074 Verify scope conformance for slice 2 with `git diff --name-only art-002-draft-pr-template-set...HEAD`. PR 2's base is the slice-1 branch, so that is the only range that measures slice 2's own diff; `origin/main...HEAD` would include all of slice 1. Acceptance: no shared foundation file appears; `git diff art-002-draft-pr-template-set...HEAD -- speckit-pro/artifact-gallery/manifest.json` shows exactly two changed lines, both `status` values, and neither is one slice 1 already flipped; no file under `tests/speckit-pro/` other than the generated installed-cache mirrors appears (FR-008, FR-009, SC-009, `research.md` D8).
- [ ] T075 Regenerate the payload and proof artifacts with `python3 scripts/refresh-release-artifacts.py`, then run it a second time. Acceptance: the second run produces no further change; `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and its `.sha256` do not appear dirty (FR-039, `quickstart.md` Scenario 4).
  - [ ] T076 Run `pnpm --dir docs-site reference:generate` and inspect `git status --short docs-site/`. T048 switches branches inside this same worktree, so T002's install is still present and `AGENTS.md` *Worktree Preflight* is already satisfied; run `pnpm --dir docs-site install --frozen-lockfile` first only if `docs-site/node_modules` is absent. Acceptance: the generate produces **no change**, because slice 2 touches no tracked `.md`, `.py`, or `.sh` file under `tests/speckit-pro/`. Run the command and confirm the empty result rather than assuming it (`research.md` D8, `quickstart.md` Scenario 5).
- [ ] T077 Run the full gate `python3 tests/speckit-pro/run-all.py`. Acceptance: zero failures; the total is at or above slice 1's, since slice 2 adds shipped artifacts to existing checks rather than new unit cases (SC-003, SC-007, Constitution IV).
- [ ] T078 Write the acceptance runbook for `code-approaches` and `module-map` as numbered steps with observable results, one set per template, from the manual table in `quickstart.md`. Cover opening from a local filesystem with a clean console, the offline reload, the theme control, keyboard reachability with visible focus, the sample content and its fictional identifier, the two export notices, the keyboard-only single choice with a second choice replacing the first, two module disclosures open at once, both exports recorded and empty, the clipboard-refusal path, reduced motion, the monochrome check on the distinguished path, and the module drawing's accessible name and text equivalent. Carry the same two timed observables as T046: a recorded conclusion leaves the document in a single action in under thirty seconds with nothing retyped, in every destination the entry declares (SC-002), and an export with nothing recorded states no conclusion and shows no value the reader could not see (SC-005). Acceptance: every step names a result an operator can confirm or reject without help; one template's pass completes in under ten minutes; no automated browser is introduced (FR-006, FR-024, FR-033, FR-038, SC-001, SC-002, SC-005, SC-006, SC-008, SC-010).
- [ ] T079 Assemble the PR 2 review packet in the pull-request description: what changed, why, non-goals, review order, scope budget, traceability mapping US3 and US4 and each success criterion they carry to the changed files and their verification evidence, verification evidence, known gaps, and rollback notes. Name the deferred work: generation of the slot content is ART-007's, which also inherits the two obligations recorded in `spec.md` *Dependencies* — the anchor integrity of a filled artifact, and rewriting each document title, which is head metadata no fill region encloses. Acceptance: the pull request is created with `--base art-002-draft-pr-template-set --head art-002-draft-pr-template-set-slice-2`, opened ready for review rather than draft, its title is `feat(speckit-pro): add the code-approaches and module-map gallery templates`, and its body carries a `## Release note` section after `## Known Gaps` holding exactly one non-empty ` ```release-note ` fence, placed outside every `speckit-pro-editable` marker pair. Before `gh pr create` runs, `PR_TITLE='<that title>' PR_BODY="$(cat <the emitted body file>)" PR_LABELS_JSON='[]' PR_DRAFT=false python3 scripts/compose-release-notes.py --validate-pr` exits 0 (FR-040, Constitution V).

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies; T001–T006 may start immediately.
- **Phase 2 (Foundational)**: independent of T003 and T004; only T015 depends on
  T002, for the docs-site install. It **blocks every user story**: no template
  task starts before T016.
- **Phase 3 (US1)** and **Phase 4 (US2)**: both depend on T003, T004, and T016.
  They are parallel with each other except for T029 and T040, which serialize on
  `speckit-pro/artifact-gallery/manifest.json`.
- **Phase 5 (slice 1 closeout)**: depends on T029 and T040.
  - **Phase 6 (boundary)**: T048 depends on PR 1 being **open**, not on it merging.
- **Phase 7 (US3)** and **Phase 8 (US4)**: both depend on T048, and both read
    T003's pinned sample feature from the workflow file, which the slice-1 branch already carries.
  Parallel with each other except T059 and T073, which serialize on the catalog.
- **Phase 9 (slice 2 closeout)**: depends on T059 and T073. T076 runs its own
  docs-site install; T002's is scoped to slice 1's worktree.

### Story dependencies

- **US1 (P1)** and **US2 (P2)**: independent of each other, both blocked by
  Phase 2.
- **US3 (P3)** and **US4 (P4)**: independent of each other, both blocked by T048.
  Neither depends on US1 or US2 for behavior — only for the merged catalog state
    and the validation module their base branch already carries.

### Within each story

1. Fetch the upstream source read-only.
2. Shell: language, title, canonical blocks, attribution header.
3. Inventory comment.
4. Regions with their marker pairs and sample content.
5. Anchors on the list slot's items.
6. Drawing restyle, then the drawing's accessible name and text equivalent.
7. Controls built in script, mounted onto the anchors.
8. Exports, status region, clipboard fallback.
9. Placement pair and the two export notices.
10. Heading structure.
11. Catalog flip and the layer-4 gate, in the same change.

The order matters twice. The class hooks in T023 come **before** the restyling
that uses them. The anchors in T022, T053, and T064 come **before** the control
routines in T025, T055, and T069 that mount onto them.

### Parallel opportunities

- Slice 1: the whole of Phase 3 runs beside the whole of Phase 4, because they
  edit two different files. The exceptions are T029 and T040.
- Slice 2: the whole of Phase 7 runs beside the whole of Phase 8, same reasoning,
  with T059 and T073 as the exceptions.
- Phase 2 has **no** parallelism at all: ten tasks, one file, and it is the file
  both slice-1 templates are measured by.

---

## Parallel Example: slice 1

```bash
# After T016 passes, the two templates proceed side by side:
Task: "T017–T028 — author speckit-pro/artifact-gallery/templates/implementation-plan.html"
Task: "T030–T039 — author speckit-pro/artifact-gallery/templates/spec-explainer.html"

# Then serialize the two catalog flips, which share one file:
Task: "T029 — flip implementation-plan status in speckit-pro/artifact-gallery/manifest.json"
Task: "T040 — flip spec-explainer status in speckit-pro/artifact-gallery/manifest.json"
```

---

## Implementation Strategy

### MVP

US1 alone is the MVP: Phase 1 → Phase 2 → Phase 3. At T029 the draft-PR stage has
its primary artifact and the validation that holds it. US2 is what makes slice 1
shippable, because the stage routes both unconditionally.

### Incremental delivery

1. Phase 1 + Phase 2 → validation exists, RED first, green on fixtures.
2. Phase 3 → US1 works end to end; **stop and validate**.
3. Phase 4 → US2 works end to end.
4. Phase 5 → PR 1 opens, green.
  5. T048 → PR 1 stays open; slice 2 branches from the slice-1 tip and stacks on it.
6. Phase 7 + Phase 8 → US3 and US4 work end to end.
7. Phase 9 → PR 2 opens, green.

### Parallel team strategy

Two people at most, and only inside a slice. One takes the P1 template and the
other the P2 template after Phase 2 lands. Phase 2 itself is one person's work,
because it is one file.

---

## Requirement Coverage

Every functional requirement in `spec.md` maps to at least one task. No
requirement is uncovered.

| FR | Tasks |
|---|---|
| FR-001 | T018, T031, T050, T061, T041, T074 |
| FR-002 | T004, T018, T031, T050, T061 |
| FR-003 | T018, T031, T050, T061 |
| FR-004 | T025, T026, T029, T040, T055, T056, T059, T069, T070, T073 |
| FR-005 | T029, T040, T059, T073 |
| FR-006 | T046, T078 |
| FR-007 | T029, T040, T059, T073 |
| FR-008 | T029, T040, T059, T073, T041, T074 |
| FR-009 | T004, T041, T050, T074 |
| FR-010 | T029, T040, T045, T059, T073 |
| FR-011 | T010, T020, T021, T026, T027, T033, T034, T035, T037, T052, T055, T056, T057, T063, T070, T071 |
| FR-012 | T011, T019, T032, T051, T062 |
| FR-013 | T010, T019, T032, T051, T062 |
| FR-014 | T020, T021, T033, T034, T035, T052, T063 |
| FR-014a | T003, T027, T037, T057, T071 |
| FR-015 | T011, T019, T022, T025, T032, T051, T053, T055, T062, T064, T069 |
| FR-016 | T025, T069 |
| FR-016a | T022, T025, T053, T055, T064, T069 |
| FR-017 | T052, T055 |
| FR-017a | T025, T055, T069 |
| FR-018 | T025, T026, T068, T069, T070 |
| FR-018a | T027, T057, T071 |
| FR-019 | T026, T027, T056, T057, T070, T071 |
| FR-020 | T039 |
| FR-021 | T026, T056, T070 |
| FR-022 | T026, T056, T070 |
| FR-023 | T026, T056, T070 |
| FR-024 | T026, T046, T056, T070, T078 |
| FR-025 | T026, T056, T070 |
| FR-026 | T020, T021, T023 |
| FR-027 | T033, T034, T035 |
| FR-028 | T052 |
| FR-029 | T065 |
| FR-030 | T023, T065 |
| FR-030a | T024, T066 |
| FR-031 | T020, T023, T033, T052, T063, T065 |
| FR-032 | T023, T054, T065 |
| FR-033 | T025, T026, T035, T046, T055, T056, T069, T070, T078 |
| FR-034 | T036, T067 |
| FR-035 | T027, T037, T057, T071 |
| FR-035a | T018, T031, T047, T050, T061, T079 |
| FR-035b | T028, T038, T058, T072 |
| FR-036 | T007, T009, T013 |
| FR-036a | T007, T012, T022, T053, T064 |
| FR-037 | T007, T008, T014 |
| FR-038 | T046, T078 |
| FR-039 | T005, T042, T075 |
| FR-040 | T006, T047, T048, T079 |

### Success criterion coverage

`spec.md` *PR Review Packet Requirements* makes each pull request map every
success criterion its slice carries to the changed files and the evidence for it,
so each one names its tasks here rather than being reconstructed at PR time.

| SC | Tasks | Evidence |
|---|---|---|
| SC-001 | T046, T078 | Runbook step 1, per template |
| SC-002 | T026, T046, T056, T070, T078 | Runbook step 9 with its thirty-second observable |
| SC-003 | T009, T010, T011, T077 | Checks R1–R4, green in the full gate |
| SC-004 | T003, T020, T021, T033, T034, T035, T052, T063 | Runbook steps 5 and 5a |
| SC-005 | T026, T046, T056, T070, T078 | Runbook steps 9 and 10 |
| SC-006 | T046, T078 | The ten-minute target on each runbook set |
| SC-007 | T029, T040, T044, T059, T073, T077 | Full-suite run, zero failures |
| SC-008 | T025, T026, T046, T055, T056, T069, T070, T078 | Runbook step 4 |
| SC-009 | T041, T074 | Scope-conformance diff, per slice |
| SC-010 | T054, T065, T078 | Runbook step 15, monochrome rendering |

---

## Notes

- `[P]` means parallel-safe against the **other template in the same slice**.
  Tasks inside one story edit one file and still run in order.
- The two templates in a slice are parallel-safe; their two catalog flips are
  not, because both edit `speckit-pro/artifact-gallery/manifest.json`.
- **R5 is its own check.** It is never folded into the R1 floor, and `modules`
  is never added to the floor. Floor membership proves a region exists; it
  cannot prove that region's items are individually addressable.
- **The inventory comment sits immediately after the attribution header** and
  carries none of the header's labels or literals. Placed before it, or carrying
  a licence or repository mention, the gallery scanner reads it as the header.
- **The sample-content notice goes inside a fill region; the brand mark goes
  outside every one.** They are opposite on purpose. A notice outside would
  survive the fill and call a filled artifact sample content; a mark inside would
  be deleted the first time that region is filled.
- **The full inside/outside ledger**, because those two are the ones easy to get
  backwards and the rest are the ones easy to forget. FR-011 states the rule: a
  fill replaces a whole region, so a filled artifact keeps only what sits outside
  every marker pair.
  - **Outside every pair**: the slot inventory comment; the brand mark; both
    export controls; the line saying what each export is for; the line saying
    recorded input is not saved; the `role="status"` region; the clipboard
    fallback field; and `code-approaches`' grouping element with its visible
    group label, which encloses the `approaches` region rather than sitting in
    it.
  - **Inside its own region**: the sample-content notice, in `feature-header`;
    and each diagram's text equivalent, in the same region as its drawing. A
    region's own sample content and its per-item anchors are inside by
    definition — this list is only what is authored beyond them.
  - The per-item capture controls are neither: the routine rebuilds them at every
    load onto whatever anchors the region then carries, so a fill costs nothing.
  - A misplacement in either direction is silent. The shipped template passes
    every check in this feature, and the defect appears only in a filled
    artifact. The cheap check is to delete each region's contents in a scratch
    copy and read what is left.
- **The document title is the one piece of feature-specific text outside a fill
  region**, because a title is head metadata and no region can enclose it. That
  is reconciled with FR-015 in FR-035a and handed to ART-007 in `spec.md`
  *Dependencies*; no task here can fix it, and T047 and T079 name it as deferred
  work rather than leaving it implicit.
- **Controls are built by element creation** — attributes set by name, text set
  through the text-valued property. Never assemble control markup as a string:
  the repository's construct scanner extracts markup only from single-line script
  string literals, so a multi-line markup string would bypass every prohibited-
  construct check silently.
- **Anchors are resolved by identifier lookup**, never by concatenating the value
  into a selector string. The two are not equivalent for a value a later agent
  wrote.
- Upstream sources are fetched read-only and never staged. Only branded
  derivatives are committed.
- Out of scope, and no task may drift into it: authoring logic that populates the
  fill regions (ART-007), any edit to a shared foundation file, and any browser
  automation. Repository tests stay on the Python 3.11+ standard library.
  - Commit after each task or logical group. Slice 1 and slice 2 are two stacked pull
    requests: PR 2's base is the slice-1 branch. No agent merges either one.

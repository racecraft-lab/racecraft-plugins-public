# Tasks: Final-PR Template Set — Slice 1, the PR Write-up Artifact

**Input**: Design documents from `specs/art-003-final-pr-template-set/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/export-payload-contract.md`, `quickstart.md`

**Tests**: This slice's test surface is the repository suite, not new test files. TDD here means the shared-validation literals that bind this template land **before** the artifact they judge (T004), and the binding is proved live rather than assumed (T033). FR-039a fixes the shared-validation change at three literals, so no test file is created and none is renamed.

**Reviewability**: Budget is `warn` — 758 authored lines declared against an 800 block, 1 production file, 13 total files, one primary surface (docs/process). Headroom is 42 lines. The ceiling is not a prediction; it is a checkable constraint enforced at three checkpoints with a stop rule (T021, T030, T034). Task generation adds no file beyond the four in `plan.md` § Declared File Operations. If any checkpoint fails, stop and apply `plan.md` § "The reduction levers, in order" — do not add tasks and do not absorb the overrun.

**Organization**: Tasks are grouped by user story. US1 (P1) is the MVP and delivers standalone value: a reviewer reads six sections. US2 (P2) adds question capture and both exports.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different file, no dependency on an incomplete task)
- **[Story]**: US1 or US2, on user-story phases only
- Paths are repository-relative throughout. Never write an absolute filesystem path into any artifact — a tree-wide privacy scan fails on one.

## Path Conventions

This is not an application. The four surfaces are fixed by `plan.md` § Declared File Operations:

- `speckit-pro/artifact-gallery/templates/pr-writeup.html` — NEW, the whole production surface
- `speckit-pro/artifact-gallery/manifest.json` — MODIFIED, exactly one value
- `tests/speckit-pro/unit/test-artifact-fill-regions.py` — MODIFIED, exactly three literals
- `specs/art-003-final-pr-template-set/contracts/export-payload-contract.md` — kept current with what ships

**One HTML file means most work is sequential.** Only six tasks carry `[P]`, each because it touches a genuinely different file.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the baseline the closeout is measured against, obtain the upstream source read-only, and satisfy the one worktree prerequisite.

- [ ] T001 [P] Record the G0 baseline by running `python3 tests/speckit-pro/run-all.py` from the worktree root and writing the three layer counts into the run record. **Verify**: totals match `quickstart.md` § "Baseline before you start" — 7378 passing (Layer 1 1447, Layer 4 5745, Layer 5 186). If they differ, record the delta now; do not recompute the baseline at a later stage, because T039 verifies an increase against this number.
- [ ] T002 [P] Fetch upstream `17-pr-writeup.html` read-only from `anthropics/html-effectiveness` (`main`) into the session scratchpad directory, outside the repository tree. **Verify**: the fetched file is readable from the scratchpad and `git status --porcelain` lists it nowhere. Upstream bytes are never staged and never committed; only the branded derivative is. This is ART-002's recorded protocol (`research.md` Decision 5).
- [ ] T003 [P] Install the docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile`. **Verify**: exit code 0. `docs-site/` is the only surface with dependencies, and T036 cannot run without this.

**Checkpoint**: Baseline recorded, upstream source available read-only, docs-site ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared-validation literals, the file skeleton, both canonical blocks embedded byte for byte with their markers, the attribution header, and the slot inventory. Nothing in either user story can be judged until the artifact is a valid gallery file.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

**Expected intermediate red**: from T005 until the catalog flip in T031, the artifact file exists while its entry still reads `planned`. `SPA-CONTRACT.md` binds status and file presence in both directions, so a full-suite run in that window reports this file as an orphan. That is the contract working, not a defect. Use the targeted verification named in each task during this window; the full suite is required green only at T039.

- [ ] T004 [P] Add exactly three literals to `tests/speckit-pro/unit/test-artifact-fill-regions.py` and no fourth: `FLOOR["pr-writeup"] = ("motivation", "before-after", "file-by-file", "implementation-notes")` in the `FLOOR` dict near line 85 (the roadmap's four only, so the literal keeps tracing to one document); `LIST_SLOTS["pr-writeup"] = ("file-by-file",)` in the `LIST_SLOTS` dict near line 99; and `"implementation-notes.md"` as a member of the `SOURCE_ARTIFACTS` tuple near line 136, written as a bare filename like every existing member. **Verify**: run the import probe in `quickstart.md` § "Prove the validation is not passing vacuously" and confirm it prints the roadmap's four for the floor, `("file-by-file",)` for the list slots, and `implementation-notes.md` in the source set; then `python3 tests/speckit-pro/run-all.py --layer 4` still passes. This is the whole of the slice's change to shared validation (FR-038, FR-039, FR-039a). Do not add a cross-template comparison of the failure message and do not widen the floor-scoped universe — both are recorded gaps, and the second contradicts a decision recorded inside the file being edited.
- [ ] T005 Create `speckit-pro/artifact-gallery/templates/pr-writeup.html` with the document skeleton only: one HTML file, no build step, no bundler, no preprocessor, and no sibling asset of any kind. **Verify**: the file stem equals the `id` its catalog entry declares (`pr-writeup`), and the directory gains no second file.
- [ ] T006 Embed the `BRAND-KIT` block from `speckit-pro/artifact-gallery/brand-kit.css` into `speckit-pro/artifact-gallery/templates/pr-writeup.html` verbatim, with its markers, byte for byte, exactly once, start before end (318 lines). **Verify**: a byte comparison of the embedded span against the source block reports zero characters of drift, and `python3 tests/speckit-pro/run-all.py --layer 4` reports no drift finding naming this artifact. Never hand-edit the copy; re-copy from source if it drifts.
- [ ] T007 Embed the `GALLERY-HEAD` block from `speckit-pro/artifact-gallery/theme-toggle.html` into `speckit-pro/artifact-gallery/templates/pr-writeup.html` verbatim, with its markers, byte for byte, exactly once, start before end (140 lines). The security policy declaration, the font request, the pre-paint theme application, and the theme control all arrive inside it. **Verify**: byte comparison reports zero drift, and none of those four is authored, replaced, wrapped, or moved anywhere in the file (FR-006).
- [ ] T008 Write the attribution header as an HTML comment near the top of `speckit-pro/artifact-gallery/templates/pr-writeup.html`, using the five exact labels the contract fixes plus the upstream copyright line verbatim, naming `17-pr-writeup.html` as the upstream file and the repository the contract names. **Verify**: `--layer 4` gallery scanner passes its attribution check, including agreement between the named upstream file and the catalog entry's `source.file`.
- [ ] T009 Write the slot inventory as a single HTML comment placed immediately after the attribution header in `speckit-pro/artifact-gallery/templates/pr-writeup.html`: seven lines, one per slot, each reading `Slot: … | Fills: … | Source: …` in that order with no pipe inside any value. Use the seven lines recorded in `data-model.md` § "The inventory comment" — they already carry `before-after`'s panel-word instruction, `file-by-file`'s anchor instruction, `verification`'s state-word instruction, and `implementation-notes`' filter plus all three empty cases named rather than gestured at. **Verify**: every slot name is filename-safe kebab-case and unique; the inventory carries none of the attribution header's labels or literals (FR-016); every `Source:` value is a member of the closed set as extended by T004; and an agent reading the inventory alone can name all seven regions and all three of FR-019b's empty cases (SC-011).
- [ ] T010 Sweep `speckit-pro/artifact-gallery/templates/pr-writeup.html` for prohibited constructs and drop any the upstream source uses: a base element, a reference beginning with two slashes and no scheme, an event-handler attribute, a `srcdoc` attribute, a form element with a submission target, and a `ping` attribute. Confirm no external reference loads a resource other than the brand typeface request carried inside `GALLERY-HEAD`, and no relative reference into a skills directory of the form the Codex payload build rewrites. **Verify**: `--layer 4` gallery scanner passes the prohibited-construct and external-reference scans (FR-007, FR-008, FR-010).
- [ ] T011 Verify the reviewability budget against the realized task and file scope before implementation proceeds, and record the result in the run record: the task list adds no file beyond the four in `plan.md` § Declared File Operations, so 1 production file and 13 total files stand. **Verify**: the counts match the declaration in `plan.md` § "Declared Figures"; the split decision is recorded as "this spec is the split, slices 2 and 3 are the named follow-ups, no further split available"; and no `Reviewability-Exception` pragma is claimed, because none of `refactor`, `infra`, or `upgrade` honestly describes net-new template work.

**Checkpoint**: The artifact is a structurally valid gallery file with both canonical blocks, an attribution header, and a complete inventory. Region work can begin.

---

## Phase 3: User Story 1 - Read the finished change (Priority: P1) 🎯 MVP

**Goal**: A reviewer opens the artifact straight from a filesystem, with no server and no install, and reads six things about the change: why it was made, what it looked like before and after, what each changed file does, what it deliberately leaves out, how it was verified, and what actually happened while it was implemented.

**Independent Test**: Open the shipped template from the filesystem with the network unavailable. All six sections render with their sample content, the browser console reports nothing, no load fails, and the theme control works. The only visible difference from an online render is typeface substitution.

**Sample content rule for every task in this phase**: representative and fictional, held to the minimum that demonstrates the region's shape — non-empty everywhere, expansive nowhere. Every region uses the **same** invented feature, named once and reused (FR-018).

### Implementation for User Story 1

- [ ] T012 [US1] Build the six reader-facing section shells in `speckit-pro/artifact-gallery/templates/pr-writeup.html`, in document order `motivation`, `before-after`, `file-by-file`, `non-goals`, `verification`, `implementation-notes`. Each section carries its heading **outside** its marker pair, the heading carries `id="sec-<slot>"`, and the section is labelled by it. Each heading reads as a plain-English reader label, never a restatement of its slot name, because the export line is `<slot> / <section heading>` and an echo collapses it to the same word twice. Delimit each region with exactly one pair, `FILL:<slot>:START` before `FILL:<slot>:END`. **Verify**: `--layer 4` fill-region checks R1 through R7 report seven regions once `feature-header` lands in T013; no pair encloses another; each pair delimits a whole subtree with no element opening on one side of a boundary and closing on the other (FR-011e, FR-012, FR-013, FR-023b).
- [ ] T013 [US1] Add the `feature-header` region to `speckit-pro/artifact-gallery/templates/pr-writeup.html` with its own marker pair: the invented feature's identifier carrying `id="feature-id"` and its name carrying `id="feature-name"`, both **inside** the pair because an export may carry nothing the reader could not see. Place the artifact's own kind carrying `id="artifact-title"` **outside** every region, so no fill can delete it. Inside the pair, add FR-018a's one sentence saying in visible text that the content is invented, naming the invented feature, reusing the muted-paragraph rule so it adds no CSS rule. **Verify**: all three ids resolve uniquely; `artifact-title` sits outside all seven marker pairs and the two feature ids sit inside `feature-header`'s; the notice is present and names the same invented feature every other region uses.
- [ ] T014 [US1] Fill the `motivation` region in `speckit-pro/artifact-gallery/templates/pr-writeup.html` with one short prose paragraph saying why the invented change was made, ported from upstream `#why`'s heading and lede. **Verify**: one paragraph, non-empty, inside the marker pair; the heading stays outside it.
- [ ] T015 [US1] Fill the `before-after` region in `speckit-pro/artifact-gallery/templates/pr-writeup.html` with the two-panel comparison promoted out of upstream's `#why`, one short statement per panel, **each opening with the word naming its panel**. **Verify**: which panel is which survives the single `flex-wrap` that stacks them on a narrow viewport and survives a monochrome rendering, resting on neither column position nor panel colour (FR-018, FR-032).
- [ ] T016 [US1] Fill the `file-by-file` region in `speckit-pro/artifact-gallery/templates/pr-writeup.html`, ported from upstream `#tour`. Its grouping element sits **outside** the marker pair so the container survives a fill. Ship **three** items — a production file, its test, and a config or manifest value — each an element that requires an end tag, each carrying a stable unique anchor of the form `file-by-file-<item-slug>` in kebab-case. **Verify**: `--layer 4` R5 counts three anchored items at the region's own top level (its floor is 2 and nothing caps it); no anchor is duplicated; no item reports as nested, which is what an unclosed item would do because the parser performs no implied closing (FR-020).
- [ ] T017 [US1] Fill the `non-goals` region in `speckit-pro/artifact-gallery/templates/pr-writeup.html`, seeded from upstream `#focus`'s third item and restructured as its own titled section: two items, grouping element **inside** the marker pair, no per-item anchor. **Verify**: two items render; no `file-by-file`-style anchor appears; the grouping element is inside the pair, following `key-files` in `module-map` and `goals` in `spec-explainer` (FR-020a).
- [ ] T018 [US1] Fill the `verification` region in `speckit-pro/artifact-gallery/templates/pr-writeup.html`, ported from upstream `#tests`: two items, grouping element **inside** the marker pair, no per-item anchor, showing **both states** — one passed and one pending. **Verify**: each state reads as a **word**, never as a check glyph's fill, so the region teaches both values at two items and survives a monochrome rendering (FR-011d, FR-018).
- [ ] T019 [US1] Author the `implementation-notes` region fresh in `speckit-pro/artifact-gallery/templates/pr-writeup.html` — it has no upstream counterpart. Place a standing one-sentence intro **outside** the marker pair, phrased as the region's **standing rule** rather than as a claim about the entries below it, saying that only tasks with something to report appear, that they appear in the record's order, and that a retried task appears more than once. Inside the pair, ship a grouping list of **three** entries, each a list item whose task identifier leads in **bold**. Two entries share a task identifier and are **non-adjacent**, with the second stating what the re-run changed so the pair reads as history. **Verify**: three entries render in append order; the retry pair is non-adjacent, carries no visual grouping and no derived attempt ordinal; no per-item anchor exists anywhere in the region, because an anchor derived from a repeated task identifier would collide and a fragment resolving to two items resolves to neither; and the artifact ships **no** empty-state element (FR-019, FR-019a, FR-019c, FR-019d, FR-020a).
- [ ] T020 [US1] Write the six document sections' CSS in `speckit-pro/artifact-gallery/templates/pr-writeup.html`, applying every reduction lever from `plan.md` § "The reduction levers, in order" from the start rather than after a failure: one `.section` rule and one `h2` rule serving all six, with **no per-section selector**; one layout rule plus one panel rule for `before-after` and no responsive refinement beyond a single `flex-wrap`; no hover-only refinement, because a hover state carries no meaning and is decoration paid for in lines; and **name no heading typeface at all**, inheriting the block's own per-level assignments. **Verify**: `--rc-border-subtle` appears nowhere in the authored CSS (FR-031a is a search, not a judgement); no custom property is referenced that the embedded block does not define, because an undefined one fails silently and renders plausibly; every foreground and background pairing comes from the kit's audited set; and the port carries none of upstream's multi-class syntax highlighting, using the single muted-comment span the shipped templates use.
- [ ] T021 [US1] **Measurement checkpoint M1** — run the instrument recorded verbatim in `quickstart.md` § "The size measurement" against `speckit-pro/artifact-gallery/templates/pr-writeup.html` and record all four numbers. Use that instrument; do not write a second one. **Acceptance criterion: `css` ≤ 150.** **Verify**: the instrument's reported `css` figure is 150 or lower, and all four numbers are written into the run record against the label M1. **On failure: STOP.** Do not proceed to any question or export work. Apply the five reduction levers in `plan.md` order and re-measure until the criterion is met. If all five are applied and `css` still exceeds 150, the ceiling has failed on evidence rather than on discipline; escalate to the operator with the measurement rather than continuing. This is the load-bearing checkpoint: it is the earliest moment the ceiling can fail and the cheapest moment to fix it, so a failure surfaces at roughly 150 lines written rather than at 758. Sanity-check the instrument against `speckit-pro/artifact-gallery/templates/spec-explainer.html` any time you doubt it — expect `authored 315 | css 169 | js 0 | markup 146`.

**Checkpoint**: All six sections plus `feature-header` render with sample content, and the document-section CSS is inside its ceiling. US1 is independently testable now: open the file from a filesystem with the network off and read it. This is the MVP.

---

## Phase 4: User Story 2 - Hand the questions back (Priority: P2)

**Goal**: Having read a section, the reviewer attaches a question to it, repeats for as many sections as they want, then copies every question out of the page in one action — either as a pull-request comment or as an instruction to paste into a coding agent.

**Independent Test**: Type a question into two of the six sections, leave the other four empty, and invoke each export control. Each export carries exactly the two questions written, each naming the section it attaches to, and carries nothing from the four empty fields.

**Depends on**: US1 complete. Every question attaches to a section that must already exist.

### Implementation for User Story 2

- [ ] T022 [US2] Build the six question controls in `speckit-pro/artifact-gallery/templates/pr-writeup.html` from one routine at load, following the shape the shipped **objection** controls use in `module-map` and `implementation-plan`: a native disclosure closed on load plus one labelled text field. Resolve each section from its `sec-<slot>` id, then resolve from that heading to the **section it labels**, and append the control to that section's **end** — never immediately after the heading, which would put every question ahead of the content it questions. **Verify**: the disclosure's own control states **in text** whether its section currently carries a question, and that text is recomputed on **every change to the field**, not once at mount and not only on the next toggle; the field's visible label is programmatically associated with it and placeholder text is not used as the accessible name; the disclosure carries no ARIA role, no `aria-expanded`, and no `aria-pressed`; nothing in the file closes a disclosure it did not open; and each control is reachable and operable by keyboard alone (FR-021, FR-021a, FR-021b, FR-023c).
- [ ] T023 [US2] Add the export chrome to `speckit-pro/artifact-gallery/templates/pr-writeup.html`: exactly one control per declared export kind, labelled "Copy as prompt" and "Copy as Markdown" — destination, never mechanism. Ship the export region **hidden** as an attribute on a container line that exists anyway, and reveal it from the routine that already runs at load, so the affordance appears only where it works. Add exactly one live status region, present from load rather than created on demand, sitting **outside every fill region**. Add the selectable fallback field, focusable and not disabled, with an accessible name. **Verify**: with scripting unavailable the export controls do not appear while all six sections stay readable; the status region survives every fill because a fill cannot reach it; the reveal costs the single budgeted line.
- [ ] T024 [US2] Implement the export serializer in `speckit-pro/artifact-gallery/templates/pr-writeup.html`. Collect from a **pinned list of slot names in document order**, resolving each section by its `sec-<slot>` id directly rather than walking a container's children, with each item carrying its own slot name and no value concatenated into a selector string. Walk only the non-empty fields. Emit the shape in `data-model.md` § Shape: the artifact title line, the `Feature: <id> <name>` line read from live state with the fallback chain in `contracts/export-payload-contract.md`, a blank line, the single lead line naming the kind, then one blank-line-separated block per question whose reference line reads `<slot> / <section heading>  (#sec-<slot>)` with **two spaces** before the parenthesis. Both kinds serialize the same structure and differ in exactly one line, and **neither emits markdown syntax**. **Verify**: questions in 2 of 6 sections produce exactly 2 blocks and zero placeholders or empty entries for the other four; both lead lines are byte-identical to the values pinned in `contracts/export-payload-contract.md`; the export is derived from live state at the moment of invocation and carries no value the reviewer could not have inspected on screen (FR-023, FR-023a, FR-023b, FR-023c, FR-024, FR-025, FR-026).
- [ ] T025 [US2] Implement the empty state in `speckit-pro/artifact-gallery/templates/pr-writeup.html`: when no question has been written, both exports still emit the two header lines and then say in text that there is nothing to export, denying that this is an approval. **Verify**: both bodies are byte-identical to the `pr-writeup` rows pinned in `contracts/export-payload-contract.md`; no empty or invented document is produced; the realistic misreading of an empty export as approval is refused in the text itself (FR-029).
- [ ] T026 [US2] Implement the clipboard failure path in `speckit-pro/artifact-gallery/templates/pr-writeup.html`, taking all four steps: reveal the same exported text in the selectable field; keep that field focusable and not disabled, give it an accessible name, and move focus to it; report the single failure message; and do **not** report success. **Verify**: the message is byte-identical to the one the three shipped export-carrying templates already ship; it is the **only** failure message, covers every failure mode, and asserts **no cause**; no second copy attempt is made through any deprecated interface; every invocation re-hides the fallback field before it attempts its copy, so a later success never leaves an earlier failure's payload on screen; and the rejection is handled so the browser console stays silent (FR-028, FR-028a, FR-029b).
- [ ] T027 [US2] Implement the invocation-currency guard in `speckit-pro/artifact-gallery/templates/pr-writeup.html`. Each invocation carries a token compared against the current one, and the check is scoped **by effect, not by path**: it sits where a status write or a fallback reveal actually lands, and every path reaches those effects through it. **Verify**: with two exports invoked before the first completes, only the later invocation's outcome is reported — the superseded one changes no status text, reveals no fallback text, and moves no focus; **both** settle paths are guarded, so a slow success resolving after a fast failure cannot overwrite the failure message while the fallback field holds the other kind's text. Scoping by path is insufficient because the status write and the focus move are both deferred behind timers in the shipped precedent, so a synchronous decision lands asynchronously. This defect is present in all three shipped export-carrying templates and this artifact must not reproduce it (FR-026a, FR-026b).
- [ ] T028 [US2] Confirm no string literal inside the script in `speckit-pro/artifact-gallery/templates/pr-writeup.html` names the local-file scheme; feedback text says "opened from a filesystem" instead. **Verify**: the gallery scanner's URL-shaped pattern reports no external reference from a script string literal — it treats a literal opening with a scheme and a colon, or carrying a scheme followed by two slashes anywhere, as one. The clipboard call itself is not a scanned call site; the wording is (FR-029c).
- [ ] T029 [US2] Write the question and export CSS in `speckit-pro/artifact-gallery/templates/pr-writeup.html`: the disclosures, the controls, the status region, and the fallback field. Share one base disclosure rule set between `file-by-file`'s items and the six question controls rather than writing two — this is the single largest avoidable cost across the two CSS ceilings. **Verify**: `--rc-border-subtle` still appears nowhere; no status, action, or distinction is carried by colour alone; the kit's focus indicator is not suppressed without an equivalent replacement; no positive tab index is added and focus is trapped nowhere; and any motion this template itself introduces is suppressed under a reduced-motion preference (FR-031a, FR-032, FR-034, FR-035).
- [ ] T030 [US2] **Measurement checkpoint M2** — run the same instrument from `quickstart.md` § "The size measurement" against `speckit-pro/artifact-gallery/templates/pr-writeup.html` and record all four numbers. **Acceptance criterion: `css` ≤ 247.** **Verify**: the instrument's reported `css` figure is 247 or lower, and all four numbers are written into the run record against the label M2. **On failure: STOP.** Reduce and re-measure before writing any further line; the sharing lever in T029 is the first place to look.

**Checkpoint**: Both user stories work. A reviewer reads six sections, attaches questions, and exports them two ways with a working failure path.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: The catalog flip, the payload and docs regeneration, the final measurement, the acceptance evidence, and the PR review packet.

- [ ] T031 Flip exactly one value in `speckit-pro/artifact-gallery/manifest.json`: the `pr-writeup` entry's `status`, from `planned` to `shipped`. Change no other value on this entry, no other entry, and no shared foundation file — not `SPA-CONTRACT.md`, not `brand-kit.css`, not `theme-toggle.html`, not the signal vocabulary, and not the export vocabulary. **Verify**: a diff of the manifest shows one changed line; `exports` still reads `["prompt","markdown"]` and `source.file` still reads `17-pr-writeup.html`. **This value and the artifact file MUST land in the same commit.** The contract binds them in both directions: the file without the flip fails as an orphan, the flip without the file fails as a missing artifact, and neither may be committed alone. Rollback is the same pair moving back together.
- [ ] T032 [P] Reconcile `specs/art-003-final-pr-template-set/contracts/export-payload-contract.md` against what actually shipped. The document already exists; the task is to keep it current, not to author it fresh. **Verify**: every literal the contract pins — both lead lines, both empty-state bodies, the failure message, the feature fallback, and the status messages — is byte-identical to what the artifact emits; the recorded divergence on capture-control placement still describes the code; and the two honest consequences stay recorded, that nothing compares the failure message across the four templates and that this document will dangle the same way when ART-003 is archived. Different file from the artifact, the manifest, and the validation module, so this runs alongside them.
- [ ] T033 Prove the fill-region validation binds this template rather than passing vacuously. Run the import probe in `quickstart.md` § "Prove the validation is not passing vacuously" against `tests/speckit-pro/unit/test-artifact-fill-regions.py`, then run the deliberate negative check and revert it: flip the entry in `speckit-pro/artifact-gallery/manifest.json` back to `planned` with the file still present and confirm the suite fails as an orphan. **Verify**: the probe prints the three expected values; the negative check fails as predicted; the flip is restored to `shipped` and `git diff` shows the manifest back to its T031 state. This is the one result a green suite can hide, because the module resolves its universe by intersecting the catalog with its floor (SC-008).
- [ ] T034 **Measurement checkpoint M3** — run the same instrument from `quickstart.md` § "The size measurement" against `speckit-pro/artifact-gallery/templates/pr-writeup.html` a final time. **Acceptance criterion: `authored` ≤ 758.** **On failure: STOP.** Reduce and re-measure; escalate to the operator above 800. **Verify**: all four numbers are recorded with the checkpoint each was taken at, ready for the PR body, so a reviewer reads a measurement rather than a claim. Headroom is 42 lines and nothing absorbs an overrun. If any later task forces a code change, re-run this checkpoint.
- [ ] T035 Regenerate the plugin payload with `python3 scripts/refresh-release-artifacts.py`, because the gallery ships inside the payload and a new template changes shipped bytes on both platforms. **Verify**: `dist/claude/**` and `dist/codex/**`, the runner trust metadata, the installed-cache fixtures, and the payload evidence all update; none is hand-edited. CI's `artifact-consistency` job fails the pull request if this is skipped (FR-041).
- [ ] T036 [P] Regenerate the docs reference with `pnpm --dir docs-site reference:generate`, required because `tests/speckit-pro/unit/test-artifact-fill-regions.py` is a tracked `.py` file under `tests/speckit-pro/`. **Verify**: the generated reference updates and `refresh-release-artifacts.py` is confirmed **not** to cover this surface — its own help text says so, and skipping it fails `artifact-consistency` on an otherwise green local tree. Different surface from the payload and from the spec directory, so this runs alongside T032.
- [ ] T037 Record the colour pairings the artifact actually uses as part of the acceptance evidence, each traced to the audited row that clears it and to the role that row permits — body text, large text, or meaningful non-text. **Verify**: every pairing in the list appears in the artifact and every pairing in the artifact appears in the list. The record sits with the evidence rather than in the artifact on purpose: it discharges the same obligation at zero cost to the CSS ceiling (FR-030, FR-030a).
- [ ] T038 Record the manual render as acceptance evidence by walking `quickstart.md` § "Part 2 — The manual render, which no test can replace", opening `speckit-pro/artifact-gallery/templates/pr-writeup.html` directly from the filesystem with the developer console open before loading and the network unavailable. Run Scenario A and Scenario B in full. **Verify**: for **each theme**, capture a screenshot of the full page, a screenshot of the console showing it empty, and the exported text from a two-question run; confirm the greyscale check loses no meaning; and confirm Scenario B step 10, the concurrent-invocation check that all three shipped templates fail, which is the check that proves the currency guard landed. Any remediation this step forces sends the work back through T034 (FR-042, SC-001 through SC-006).
- [ ] T039 Run the full repository suite from the worktree root: `python3 tests/speckit-pro/run-all.py`. **Verify**: zero failures, and the passing total is an **increase** against the T001 baseline of 7378 rather than merely green. Layer 4 must show the gallery scanner and the fill-region validation both binding this artifact (FR-040, SC-008).
- [ ] T040 Assemble the PR review packet for this slice. **Verify**: it carries what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback notes. Review order puts the authored markup and JavaScript first, then the CSS, then the validation and catalog changes, and states that the 458 canonical lines are byte-verified copies read last or not at all. Scope budget carries all four measured numbers with the checkpoint each was taken at, plus the re-declared 758 and the note that the plan-phase estimator reported `pass` with `projected: 0` and is structurally blind here, so its green line is a known-blind diagnostic and not evidence. Known gaps name all seven from `research.md` § "Known gaps carried into the pull request". Deferred work names slices 2 and 3, the generation step in ART-010, and the ready flip. Rollback is the catalog value returning to `planned` **together with** the file's removal, because the contract binds them in both directions. Validate the exact final PR title through the repository release-readiness gate before creating the pull request, in the form `<type>(<lowercase-scope>): <plain English description>`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. All three tasks are independent of each other.
- **Foundational (Phase 2)**: Depends on Setup. T004 is independent of the rest of the phase and of both stories. T005 through T010 are strictly sequential — they are the same file. BLOCKS both user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on US2.
- **User Story 2 (Phase 4)**: Depends on Foundational **and** on US1, because every question attaches to a section that must already exist. This is the one cross-story dependency in the slice, and it is inherent rather than incidental.
- **Polish (Phase 5)**: Depends on both stories. T031 must precede T033 and T035.

### Within Each Phase

- T006 and T007 precede T008 and T009 only by convention of file order; all four touch the same file and are sequential.
- T012 precedes T013 through T019 — the shells must exist before regions fill them.
- T020 follows every markup task in US1, because the CSS is written against markup that exists.
- T021 (M1) follows T020 and **precedes every task in Phase 4**. This ordering is the point of the checkpoint.
- T024 follows T022 and T023; T025 through T028 refine the routine T024 establishes.
- T030 (M2) follows T029.
- T034 (M3) follows all authoring, including T032.

### Parallel Opportunities

Six tasks carry `[P]`, and every one is justified by touching a different file:

| Task | File it touches | Why it is genuinely disjoint |
|---|---|---|
| T001 | none (read-only suite run) | Runs the suite and writes nothing to the tree. |
| T002 | the session scratchpad, outside the repository | Fetches upstream read-only; no repository file is touched and no upstream byte is staged. |
| T003 | `docs-site/` dependencies | Writes only gitignored dependency state. |
| T004 | `tests/speckit-pro/unit/test-artifact-fill-regions.py` | The only task in the slice touching this file. Its literals are inert until T031 flips the catalog, so it can proceed alongside the skeleton work. |
| T032 | `specs/art-003-final-pr-template-set/contracts/export-payload-contract.md` | The only task touching this file, and it is in the spec directory rather than the plugin. |
| T036 | the generated docs-site reference | A different generated surface from T035's payload; `refresh-release-artifacts.py` does not cover it. |

T032 and T036 can run together. Everything else in Phases 2 through 5 is sequential, because **one HTML file means most work is sequential** — 29 of the 40 tasks edit `speckit-pro/artifact-gallery/templates/pr-writeup.html`.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational — blocks both stories.
3. Complete Phase 3: User Story 1, ending at the M1 checkpoint.
4. **STOP and VALIDATE**: open the file from a filesystem with the network off and read all six sections. This satisfies the catalog entry ART-001 already shipped, and a reader who never writes a question down has still received value.
5. M1 must pass before any Phase 4 work begins.

### Incremental Delivery

1. Setup + Foundational → the artifact is a valid gallery file.
2. US1 → a reviewer can read the finished change. MVP.
3. US2 → a reviewer can hand their questions back.
4. Polish → the flip, the regenerations, the evidence, the packet.

The slice ships as **one** pull request. The increments are checkpoints inside it, not separate deliveries, because a self-contained HTML artifact cannot be divided across two pull requests and still render from a filesystem.

### The stop rule

Three checkpoints, each a hard gate with a numeric criterion:

| Checkpoint | Task | Runs after | Passes when |
|---|---|---|---|
| **M1** | T021 | the six sections' CSS, before any export work | `css` ≤ 150 |
| **M2** | T030 | the question and export CSS | `css` ≤ 247 |
| **M3** | T034 | all authoring, before the pull request | `authored` ≤ 758 |

A failure means stop, apply the reduction levers in `plan.md` order, and re-measure. It does not mean continue and reconcile later. M1 is the load-bearing one: it is the earliest moment the ceiling can fail, and putting it before the export work means a failure surfaces at roughly 150 lines written rather than at 758. The three shipped templates that missed this ceiling had no such checkpoint.

---

## Notes

- `[P]` tasks touch different files and have no dependency on an incomplete task.
- Every task states its verification inline. A task with no stated check is not done.
- The measuring instrument is recorded verbatim in `plan.md` § "The instrument" and `quickstart.md` § "The size measurement". Use that one. A second instrument would measure a different quantity and the ceilings would stop meaning anything.
- Never write an absolute filesystem path into any artifact this slice produces. A tree-wide privacy scan fails on one.
- Never hand-edit an embedded canonical block, a generated payload, an installed-cache proof, or a generated reference page.
- The catalog value and the artifact file land together in every direction, including rollback.
- The full suite must pass at the end: `python3 tests/speckit-pro/run-all.py`.

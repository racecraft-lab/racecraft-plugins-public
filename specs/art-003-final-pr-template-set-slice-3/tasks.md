# Tasks: Final-PR Template Set — Slice 3, the Flowchart Artifact

**Spec**: `specs/art-003-final-pr-template-set-slice-3/spec.md` (ART-003, slice 3 of 3)

**Branch**: `art-003-final-pr-template-set-slice-3`, cut from slice 2

**Baseline**: 7380 passing (Layer 1 1447, Layer 4 5747, Layer 5 186)

**Budget**: 460 declared, 800 block. Component ceilings 210 CSS / 90 script /
200 markup. Script is expected to measure **zero**, so the total should land well
under the declared figure.

---

## How this decomposition is ordered

Four phases, in the order the workflow fixes them: Foundation, US1, US2, Polish.
Within a phase the order is TDD: the check that fails comes before the code that
makes it pass, and every task names the command that decides it.

**The one structural problem this repository poses for TDD**, and how these tasks
solve it: the shared validation resolves its per-template universe by intersecting
the catalog with `FLOOR`, and it only parses a template whose entry reads
`shipped`. Until the catalog flip in Phase 4, nothing in the suite asserts
anything about `flowchart` at all, so every task in Phases 1 through 3 would pass
vacuously. The catalog flip cannot move earlier, because the contract binds status
and file presence in both directions and a flip before the file exists is an
orphan.

The resolution is the **shipped-status probe** built at T004: both validation
modules take `gallery_root` as a parameter, so the probe copies the gallery into
the session scratchpad, flips this one entry to `shipped` **in the copy**, and
runs the real checks against it. Real assertions, real failure messages, the
tracked tree untouched. Every RED and GREEN in Phases 1 through 3 is that probe.
Phase 4 then flips the real entry and the suite says the same thing.

**No second measuring instrument is written.** The size instrument is the one
recorded in `specs/art-003-final-pr-template-set/quickstart.md` § "The size
measurement", pointed at this slice's file.

**No absolute filesystem path appears in any artifact this slice authors.**

---

## Phase 1 — Foundation

Validation literals, skeleton, both canonical blocks, the attribution header, the
four-line inventory.

- [ ] **T001** Record the baseline. Run `python3 tests/speckit-pro/run-all.py` and
  record the total and the per-layer counts. **Verify**: 7380 passing, Layer 1
  1447, Layer 4 5747, Layer 5 186, zero failures. A different number here is a
  stop — every later comparison is against this one. Do not substitute
  `--layer 4` alone at any point in this run: it overcounts against a full run,
  which is the hazard slices 1 and 2 each paid for once.

- [ ] **T002 [RED]** Prove the shared validation currently asserts **nothing**
  about `flowchart`. Run the non-vacuity probe recorded in slice 1's quickstart
  § "Prove the validation is not passing vacuously", substituting `flowchart` for
  `pr-writeup`. **Verify**: it prints `flowchart floor: None` and
  `flowchart lists: None`. That is this slice's opening RED — a template the floor
  does not name is never parsed, so a port with no regions and no inventory would
  pass every check green.

- [ ] **T003 [GREEN]** Add the three validation literals to
  `tests/speckit-pro/unit/test-artifact-fill-regions.py`, in the shape slices 1
  and 2 used and no other: `FLOOR["flowchart"] = ("flow-diagram",)` — single-entry,
  on the `module-map` precedent, because the roadmap's scope for this template is a
  clickable operational-flow diagram — and `LIST_SLOTS["flowchart"] = ("nodes",)`.
  **Add no new `SOURCE_ARTIFACTS` member**: all four slots draw from the existing
  closed set. `nodes` is deliberately **not** in the floor, for the reason already
  recorded against `modules`: floor membership would prove only that a region of
  that name exists, never that its items are addressable. **Verify**: re-run T002's
  probe and read `flowchart floor: ('flow-diagram',)`,
  `flowchart lists: ('nodes',)`, and a `SOURCE_ARTIFACTS` tuple still seven members
  long with `plan.md` among them (FR-044, FR-045, FR-051).

- [ ] **T004 [RED]** Build the **shipped-status probe** in the session scratchpad
  and run it. It copies `speckit-pro/artifact-gallery/` to a scratch directory,
  flips only the `flowchart` entry's `status` to `shipped` **in the copy**, loads
  `tests/speckit-pro/unit/test-artifact-fill-regions.py` and
  `tests/speckit-pro/unit/test-artifact-gallery.py` through `importlib`, runs every
  `check_*` that takes a gallery root against the copy, and prints the failures
  whose text names `flowchart`. It writes nothing into the tracked tree.
  **Verify**: with no artifact yet, it reports the artifact missing at the derived
  path, both canonical blocks absent for a shipped entry, and the floor slot
  `flow-diagram` delimited by no marker pair. Those three failures are the
  specification of everything Phases 1 through 3 build. A probe that reports
  **nothing** here is a broken probe, not a passing slice — that is the vacuity
  this task exists to rule out.

- [ ] **T005** Create `speckit-pro/artifact-gallery/templates/flowchart.html` with
  the document opening: the doctype, then the attribution header carrying the five
  labels `Upstream repository:`, `Upstream file:`, `License:`, `License text:` and
  `Modified derivative:`, the upstream copyright line, and the licence-text
  reference. `Upstream file:` reads `13-flowchart-diagram.html`. **Verify**: the
  probe stops reporting the header's elements as missing and stops reporting a
  provenance disagreement; a comparison of the header's `Upstream file:` value
  against the catalog entry's `source.file` shows zero characters of difference
  (FR-005, FR-006).

- [ ] **T006** Embed the gallery-head block into `<head>` byte for byte between
  `GALLERY-HEAD:START` and `GALLERY-HEAD:END`, the markers included, copied from
  `speckit-pro/artifact-gallery/theme-toggle.html`. **Never hand-edit the copy.**
  It carries the in-document policy declaration, which must be a direct child of
  `head` with no content-bearing element before it but the character-encoding
  declaration. **Verify**: the probe reports no head-block drift and no
  policy-placement failure; an independent extraction of the two regions compares
  equal byte for byte including line endings (FR-004).

- [ ] **T007** Embed the brand-kit block as the first thing inside `<style>`, byte
  for byte between `BRAND-KIT:START` and `BRAND-KIT:END`, the markers included,
  copied from `speckit-pro/artifact-gallery/brand-kit.css`. **Verify**: the probe
  reports no brand-block drift; the extraction compares equal byte for byte. One
  character of drift is the failure mode both slices before this one hit, and it is
  always re-copy, never repair (FR-003).

- [ ] **T008** Add the remaining head chrome and the page frame: the viewport meta,
  a `<title>` reading `Flowchart — NIMBUS-101 Offline Draft Sync`, the closing
  `</style></head>`, and a body whose page head carries the brand mark and the
  artifact's own displayed title reading exactly `Flowchart` with
  `id="artifact-title"`, placed **outside every marker pair** so no later fill can
  delete it. **Verify**: `artifact-title` resolves uniquely and sits outside both
  the head-block markers and every `FILL:` pair (FR-011).

- [ ] **T009 [RED→GREEN]** Add the four-line slot inventory as the comment
  **immediately after** the attribution header — one line per slot, reading
  `Slot: … | Fills: … | Source: …` in that order, no pipe inside any value, each
  name filename-safe kebab-case and unique. The four lines are `feature-header`
  (`Source: spec.md`), `flow-summary`, `flow-diagram` and `nodes` (each
  `Source: plan.md`). **Both the `flow-diagram` and the `nodes` line MUST state the
  binding**: each node in the drawing links to the entry of the same slug in
  `nodes`. The inventory carries **none** of the attribution header's own labels or
  literals, or the scanner reads the inventory as the header. **Verify**: RED
  first — the probe reports the inventory missing; then GREEN — it reports no
  inventory format, placement, vocabulary or uniqueness failure, and no source
  outside the closed set (FR-008, FR-009, FR-044, FR-044b).

- [ ] **T010 [RED→GREEN]** **Compare the artifact's displayed title against its
  catalog entry's `title` by running a comparison, not by reading either.** Adapt
  the command recorded in slice 2's quickstart § "The title comparison no test
  performs" to `flowchart`. **Verify**: it prints `EQUAL`, with zero characters of
  difference including case. **`MISMATCH` is a stop** — fix the artifact title,
  never the catalog, because the catalog value is fixed by ART-001 and this slice
  may change exactly one value and it is `status`. Slice 1 shipped a sentence-case
  title against a title-case catalog value, the whole suite passed green, and only
  independent review caught it. A reading would have passed on slice 1 too
  (FR-011, FR-012, SC-008).

- [ ] **T011** Foundation checkpoint. Re-run the probe. **Verify**: the only
  failures naming `flowchart` are the region ones — the floor slot `flow-diagram`
  delimited by no marker pair, and the list slot `nodes` carrying no addressable
  item. Anything else outstanding at this point is Foundation work that is not
  finished, and Phase 2 does not start on it.

---

## Phase 2 — US1: the drawing, its caption, the narration, the nodes region

- [ ] **T012** Write the page-frame and section CSS below the brand-kit block:
  the box-sizing reset, `body`, `.page`, the header chrome (`.page-head`,
  `.brandline`, `.artifact-kind`, `.eyebrow`, `h1`, the sample notice), and the
  section chrome (`.section`, its `h2`, `.section-intro`). Match the house style
  `module-map` and slice 2 already ship; introduce no colour value, only tokens.
  **Verify**: every declaration names a brand-kit token or a length; the display
  typeface token is assigned to first- and second-level headings only; every
  boundary that carries meaning uses the strong border token, and the subtle one is
  used nowhere. **State that absence in prose, never by naming the token in a
  comment** — a comment naming it fails the very search that checks for it
  (FR-007, FR-050).

- [ ] **T013** Write the drawing's CSS. Node shape carries role, so the shape
  classes differ in geometry and never in fill: one node fill token and one stroke
  token for all seven. Edge kind carries in stroke pattern: the ordinary and
  affirmative edges solid, the failure edge dashed through a dash array. **Exactly
  one arrowhead marker rule, and its fill names a brand-kit token through a class**
  — upstream defines three markers and hard-codes a different colour into each,
  which is the trap FR-007 names. The interactive node's focus indicator is the
  kit's inherited outline **reinforced by a stroke-weight change**, because an
  outline on an inline vector child is not uniformly reliable and stroke weight is
  not a hue. **Add no animation and no transition**: upstream animates node hover
  with a transform transition, and the port drops the declaration rather than
  guarding it, so a reduced-motion preference has nothing left to suppress.
  **Verify**: no colour literal anywhere; one marker rule; no `transition` and no
  `animation` property in the authored CSS; the focus rule adds an indicator and
  suppresses none (FR-007, FR-018a, FR-020, FR-021a, FR-022, FR-026, FR-037,
  FR-049).

- [ ] **T014** Write the CSS for the figure and its container, the caption, the
  narration, the legend, and the per-node disclosures. The figure is the only
  element that scrolls, so a drawing wider than the viewport scrolls inside its own
  container and the page body never scrolls sideways. The legend's entries are
  words; **no swatch carries meaning**, so the legend needs no colour rule at all.
  The disclosures reuse the shipped `details`/`summary` house style. **The
  two-column layout the budget's basis line anticipated is not written**: FR-041b
  puts the per-node detail below the drawing in reading order rather than in a
  panel beside it, so the column rules have no subject. Record that as a deliberate
  saving against the CSS component (FR-023a, FR-025, FR-041b).

- [ ] **T015 [CHECKPOINT M1]** **Measure the CSS before writing any markup.** Run
  the instrument from `specs/art-003-final-pr-template-set/quickstart.md` § "The
  size measurement" against
  `speckit-pro/artifact-gallery/templates/flowchart.html`.
  **Numeric criterion: `css` ≤ 210**, the ceiling this spec's budget table fixes.
  **Stop rule**: if `css` exceeds 210, **stop and do not write markup**. Cut CSS
  back under the ceiling first, taking the cut from decoration rather than from any
  rule an accessibility requirement depends on, and re-measure. Only a cut that
  fails to reach 210 is escalated, with the overrun explained against the component
  basis rather than absorbed silently. The checkpoint fires here, with roughly 200
  lines written rather than 460, which is its whole purpose. Sanity-check the
  instrument against the comparator any time it looks wrong: `spec-explainer.html`
  must read `authored 315 | css 169 | js 0 | markup 146` (SC-012).

- [ ] **T016** Add the `feature-header` region with its own marker pair: the
  invented feature's identifier and name, and the sentence saying in visible text
  that every region holds a worked example built on an invented feature, so a
  reader opening the file cold does not read it as a real flow. The invented
  feature is the one the rest of this gallery already uses, so a reader moving
  between artifacts meets one fiction and not six. **Verify**: the notice renders
  as visible text, not as a comment or an attribute; the artifact's own title stays
  outside the pair (FR-042, FR-043).

- [ ] **T017** Add the `flow-summary` region with its own marker pair: one
  paragraph naming the flow the drawing depicts and the point in it a change would
  turn on, so SC-013's one-minute read is satisfied before the reader reaches the
  picture. **Verify**: the region ships non-empty representative sample content
  held to the minimum that demonstrates the shape (FR-042, SC-013).

- [ ] **T018** Add the legend, **outside every marker pair**. It names every node
  role, every node state and every edge kind **in words**. It is not a fill region:
  it describes the drawing conventions this template fixes rather than content a
  later fill supplies, and a legend a fill could rewrite could disagree with the
  drawing it explains. **Verify**: the legend sits outside every `FILL:` pair; each
  entry is a word or phrase; no entry depends on a colour, a swatch or a glyph fill
  to be told from another (FR-023, FR-023a).

- [ ] **T019** Add the `flow-diagram` region — **the drawing, its caption and the
  narration in one marker pair**, because two renderings the same fill replaces
  together cannot drift, which satisfies the no-drift requirement by construction
  rather than by discipline.
  - The drawing is inline vector markup with a fixed view box, named through its
    **own title element referenced by `aria-labelledby`**, and **carrying no
    `role="img"`** — that role makes every descendant presentational, which would
    remove this drawing's interactive nodes from the accessibility tree and defeat
    the keyboard and state requirements outright. The rule is `role="img"` for a
    static graphic, an accessible name alone for an interactive one.
  - **Seven nodes**: one entry terminal, two process steps, two decisions, one
    failure terminal, one success terminal. That is the smallest set demonstrating
    every node role, every edge kind, a branch, a rejoin and two distinct endings —
    the demonstrating minimum, against upstream's twelve.
  - Node role is carried by **shape** — rectangle for a process step, diamond for a
    decision, stadium for a terminal — **and** by the role written as a word on the
    node's existing second text line, which costs no extra element.
  - Edge kind is carried by **stroke pattern and word together**: the ordinary next
    step solid and unlabelled, the affirmative branch solid and labelled with the
    affirming word, the failure branch dashed and labelled with the failing word.
    Upstream dashes its failure edge but distinguishes its affirmative edge by hue
    alone, which does not survive the port.
  - **One** arrowhead marker, its fill named through a class.
  - The caption states that nothing in the drawing is marked by colour and that it
    reads the same in a monochrome print, as the gallery's other diagram already
    does. That sentence is the claim the monochrome evidence is checked against.
  - The narration gives the **order** of the flow and **every point at which it
    branches**, including where the branch rejoins and where each path terminates,
    and names for every edge its source, its target and its kind. Sequence and
    branching are carried in the picture by position and by stroke path alone, and
    neither survives into text on its own. It reads as a first-class rendering of
    the flow, not as a caption or an appendix.

  **Verify**: the drawing has an accessible name and no `role="img"`; seven nodes
  of the declared roles; three edge kinds each with a non-colour carrier; exactly
  one marker element; the caption carries the monochrome sentence; the narration
  names every node and every edge with its kind; the probe reports the floor slot
  satisfied (FR-018, FR-018a, FR-019, FR-019a, FR-020, FR-020a, FR-022, FR-022a,
  FR-024a, FR-027, FR-028, FR-029, FR-031, FR-033, FR-042a, FR-044a).

- [ ] **T020 [RED→GREEN]** Add the `nodes` region: one entry per drawn node,
  **anchored `nodes-<item-slug>` at the region's own top level**, unique in the
  document, with the **grouping element enclosing the region** rather than sitting
  inside it, because a fill replaces a whole region and the container has to
  survive one. Each entry gives its node's label, its role and its detail — what
  the step does and how it can fail. Seven ship, against the two the shared
  validation requires as a minimum. **Verify**: RED first — the probe reports
  `nodes` carrying no addressable item; then GREEN — it reports every top-level
  element anchored in the required form, no anchor repeated, and at least two
  anchored items (FR-028, FR-034, FR-045).

- [ ] **T021 [RED→GREEN]** Bind the two regions: make each drawn node an
  **in-document link** to its own entry's detail in `nodes`. **Verify**: RED
  first — a search over the file finds drawn nodes that are not links; then
  GREEN — every node is a link, and the byte search extended per T022 resolves
  every one of them (FR-044b).

- [ ] **T022** Extend the byte search to assert that **every in-document link the
  drawing carries resolves to an id present in the shipped file**. Write it as a
  single command over the shipped bytes and record its output. This is the one part
  of the no-drift requirement the region structure does not close by construction,
  so it is closed by hand. **Verify**: the count of unresolved link targets is
  **zero**, and the count of links found is seven — a search that finds no links at
  all also reports zero unresolved, and that is a broken search, not a passing one
  (FR-044b).

- [ ] **T023** Region agreement, both directions. **Verify**: the probe reports
  every documented slot delimited by exactly one pair with its start before its
  end; every delimited pair named in the inventory; the regions flat, with no pair
  enclosing another; and each pair delimiting a whole subtree (FR-046).

---

## Phase 3 — US2: the disclosure

- [ ] **T024** Make the disclosure native and **exclusive**. Each entry in `nodes`
  is a disclosure element in **one exclusive group**, so exactly one node's detail
  is open at a time and that state is the element's own — programmatic, singular,
  and not a colour. The artifact ships with the **first entry already open**, so
  the detail region is never empty on first paint. **Verify**: every entry carries
  the same group name; exactly one ships open; the open state is the element's own
  attribute rather than a class or a colour (FR-021a, FR-038, FR-040, FR-041a).

- [ ] **T025** Confirm the disclosure works from the keyboard and produces nothing
  durable. Every drawn node is a link and every entry is a native disclosure, so
  both are reachable in sequential focus order and operated by the same keys as any
  other control of their kind, with the inherited focus indicator reinforced by the
  stroke-weight change. **Verify**: no rule suppresses a focus indicator; no
  activation writes a file, writes the clipboard, triggers a download, or navigates
  away, because there is no code that could (FR-035, FR-036, FR-037, FR-039).

- [ ] **T026 [The property this slice is defined by]** **Assert the authored-script
  count is zero.** Run the size instrument and read its `js` figure. **Verify**:
  `js` is **0**, matching `spec-explainer` rather than merely approaching it, and
  the artifact's only `<script>` is the one inside the gallery-head block — a
  byte-verified canonical copy, not authored. Also confirm by search that the file
  carries exactly one `<script` occurrence and that it sits between the head
  block's markers. **This is a property to prove, not to assume.** It is the single
  largest saving in the slice, and the whole zero-script disclosure rests on it
  (FR-041a).

- [ ] **T027 [The absence nothing else protects]** **Assert by search over the
  shipped bytes that the artifact carries no export affordance and no reader-input
  field.** Search for every clipboard call, every download trigger, every copy,
  save, share or print control offered as an export, every routine that serializes
  part of the page into text, and every textarea, input, select, form and
  element made editable. **Verify**: the total count is **zero**, reported as a
  number. Every other final-PR template in this gallery ships an export control and
  a capture field, and the skeleton this port is built from is theirs, so copying
  one by habit is the realistic failure. **An absence that nothing looks for is an
  absence that nothing protects.** The one control this artifact does carry is the
  theme control the shared head block builds at load; it is neither an export nor a
  reader input, and nothing here removes it (FR-013, FR-014, FR-015, FR-017,
  FR-035, SC-005).

- [ ] **T028** Confirm the export-path requirements slices 1 and 2 carry are
  **absent by decision rather than by oversight**. **Verify**: the file carries no
  export payload shape, no clipboard-failure fallback field, no invocation-currency
  guard, no per-hunk objection capture, no per-section question capture, and none of
  the empty-state bodies those captures need. None has a subject here, and carrying
  any of them in would be an affordance the catalog does not declare — the exact
  defect the empty exports declaration exists to surface (FR-016).

---

## Phase 4 — Polish: catalog flip, payload regeneration, measurement, suite green

- [ ] **T029** Flip exactly one catalog value in
  `speckit-pro/artifact-gallery/manifest.json`: the `flowchart` entry's `status`,
  from `planned` to `shipped`. Change no other value on this entry, no other entry,
  and no shared foundation file. **Verify**: a diff of the manifest shows one
  changed line; `title` still reads `Flowchart`, `exports` still reads `[]`, and
  `source.file` still reads `13-flowchart-diagram.html`. **This value and the
  artifact file MUST land in the same commit**: the contract binds status and file
  presence in both directions, the file without the flip fails as an orphan, the
  flip without the file fails as a missing artifact, and neither may be committed
  alone. Rollback is the same pair moving back together (FR-010, SC-009).

- [ ] **T030** Regenerate the release payload. **The suite is not read-only**: it
  rewrites `dist/**` on every run and moves failures between modules in both
  directions, so restore the payload before regenerating. **For a net-new artifact
  the payload copies are UNTRACKED, so the restore is removal, not `git show`.**
  Remove the untracked payload copies of this artifact from both platforms' payload
  trees, then run `python3 scripts/refresh-release-artifacts.py`. **Verify**: both
  platforms' gallery path sets equal the source's, and each source file is
  byte-identical to both payload copies. Note that
  `refresh-release-artifacts.py --check` exits 1 on a correct **uncommitted**
  regeneration; that resolves on commit and is not a failure (FR-053).

- [ ] **T031** Regenerate the docs reference.
  `tests/speckit-pro/unit/test-artifact-fill-regions.py` is a tracked `.py` file
  under `tests/speckit-pro/`, so T003's change restales the generated docs
  reference, and that surface is **not** covered by the payload script. Run
  `pnpm --dir docs-site install --frozen-lockfile` once for this worktree if it has
  not been run, then `pnpm --dir docs-site reference:generate`. **Verify**: the
  docs artifact check passes. CI's artifact-consistency job fails the pull request
  if either regeneration was skipped, so a stale artifact cannot land (FR-053).

- [ ] **T032 [CHECKPOINT M2]** **Final measurement.** Run the size instrument
  against the shipped file and record **all four numbers** — `authored`, `css`,
  `js`, `markup` — against the declared 460 and the component ceilings 210 / 90 /
  200. **Verify**: `authored` ≤ 460, or the miss is explained against the component
  ceilings rather than absorbed silently; `js` is 0; `css` still satisfies the M1
  ceiling. With zero script the total is expected to land well under the declared
  figure, and **the slack is not budget to spend** — every line of clipboard or
  capture code it would buy is an affordance the catalog does not declare
  (FR-052, SC-012).

- [ ] **T033** Run the full suite. `python3 tests/speckit-pro/run-all.py`.
  **Verify**: zero failures and a total **above 7380**, with the increase accounted
  for by the checks the catalog flip activates for this template. Until T029 and
  T030 are both done, expect an intermediate red confined to **three families**:
  the orphan family (the artifact present while the entry reads `planned`), the
  payload family (the payload copies absent or stale), and the generated-docs
  family. **Anything outside those three is real — stop and report it** (FR-052,
  SC-011).

- [ ] **T034** Re-run the two byte searches over the **shipped** bytes, after the
  payload regeneration rather than before it, and record both counts. **Verify**:
  the authored-script count is 0 and the export-affordance and reader-input count is
  0, both as measured numbers. Re-run the title comparison and record `EQUAL`
  (FR-012, FR-015, SC-005, SC-008).

- [ ] **T035** Report the working-tree state. Run `git status --porcelain` and
  record it in full. **Verify**: the changed and added paths are exactly the
  artifact, the catalog, the validation literals, the payload copies, the
  generated docs reference, and this slice's own spec artifacts. **Nothing is
  committed, branched or pushed in this run.** An upstream byte never appears: the
  source is read read-only from the session scratchpad and is never staged.

- [ ] **T036** Record the manual render as acceptance evidence, and record honestly
  what could not be run. The suite is Python-standard-library-only and cannot
  assert browser behaviour, so this is the half no test replaces: open the shipped
  file **directly from the filesystem** with the console open before loading and
  the network unavailable, in both themes, and capture the monochrome rendering.
  **The zero-script property MUST NOT be claimed as verified until the render
  confirms it**: the disclosure rests on fragment navigation revealing a closed
  disclosure element, sources disagree on whether every current browser honours it,
  and this is recorded rather than assumed. If the reveal does not fire, the link
  still lands the reader on the right node's summary and one keystroke opens it, so
  the control is one keystroke short rather than dead. **If the render cannot be
  performed in this environment, say so and name what stays unverified** rather
  than reporting it as done (FR-002, FR-024, FR-041c, FR-047, FR-048, FR-054,
  SC-001, SC-003, SC-006, SC-007).

---

## Dependencies and ordering

- T001 → T002 → T003 → T004. Nothing else may start before T004: it is what makes
  every later RED and GREEN a real assertion rather than a vacuous pass.
- T005 → T006 → T007 → T008 → T009 → T010. The canonical blocks land before any
  authored CSS, so a drift failure is never confused with a styling failure.
- T010 follows T008 immediately, because that is the cheapest moment to catch a
  title mismatch.
- T012 → T013 → T014 → **T015**. T015 is a hard gate: no markup task starts until
  the CSS measures at or under 210.
- T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023.
- T024 → T025 → T026 → T027 → T028. The disclosure exists before the zero-script
  count means anything.
- T029 → T030 → T031 → T032 → T033. The flip precedes the payload regeneration,
  and the suite runs last.
- T034 → T035 → T036 close the run.

## Parallelisation

**None.** One file is authored end to end and every task edits it. The measurement
checkpoint at T015 depends on the CSS being complete and the markup being absent,
which a parallel task would destroy.

## Total

**36 tasks.** Phase 1 eleven, Phase 2 twelve, Phase 3 five, Phase 4 eight.

# Implementation Plan: Draft-PR Template Set (ART-002)

**Branch**: `art-002-draft-pr-template-set` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-002-draft-pr-template-set/spec.md`

## Summary

Port four planning-review templates into `speckit-pro/artifact-gallery/templates/`
as Racecraft-branded, self-contained single-file artifacts, and flip their four
routing-catalog `status` values from `planned` to `shipped`. Each artifact is one
HTML file carrying its own markup, styling, and inline behavior, embedding the two
canonical blocks byte for byte, with every region an authoring agent later fills
delimited by a paired `FILL` comment and named in the file's own inventory.

The technical approach is a **port, not a build**. `SPA-CONTRACT.md` fixes the
shape: two embedded blocks, one new artifact file, exactly one catalog value
changed. Nothing shared is edited, no build step exists, and there is no runtime
any two artifacts can share. One new Layer 4 test, stdlib only, asserts the
roadmap-named slot floor per template, both-ways agreement between each file's
inventory and its markers, and — as its own assertion — that every repeated item
in a list slot carries the anchor an objection or a selection attaches to.

Delivery is two sequential pull requests. Slice 1 is the two templates the
draft-PR stage routes unconditionally plus the whole Layer 4 test. Slice 2 is the
two conditional templates and branches from a state that already contains slice 1.

## Technical Context

**Language/Version**: HTML5 + CSS + ES5-compatible inline JavaScript for the
artifacts (no transpiler, no module loader, no framework); Python 3.11+ standard
library for validation.

**Primary Dependencies**: None at runtime. The artifacts depend only on the two
canonical blocks already shipped by ART-001 — `brand-kit.css`'s `BRAND-KIT`
region and `theme-toggle.html`'s `GALLERY-HEAD` region — copied in verbatim. The
validation depends only on `html.parser`, `json`, `re`, `pathlib`, and
`unittest`, plus the repository's own `tests/speckit-pro/lib/test_result.py`
counting result.

**Storage**: None. Reader input lives in the DOM for the life of the tab. The
theme preference is written by the canonical head block, which a template must
never read or replace (FR-035).

**Testing**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5). The new
fill-region checks land as one Layer 4 module registered in
`tests/speckit-pro/suite-manifest.json`. Browser behavior is verified by an
operator against the acceptance runbook; no automated browser is introduced
(FR-038).

**Target Platform**: A current desktop browser opening the file straight from a
local filesystem, with no server and with the network unavailable. That is the
binding target, not a served page — it is why clipboard access may be refused and
why storage may be refused.

**Project Type**: Static single-file documents shipped inside a plugin payload,
plus repository-only validation.

**Performance Goals**: Not applicable. Each artifact is a static document under
1000 lines with no data fetch, no rendering loop, and no measurable budget. The
one timing-adjacent obligation is that the typeface request must not block text
rendering, which the canonical head block's `display=swap` parameter already
satisfies and which validation already enforces.

**Constraints**: One file per artifact, no sibling asset, no build step. Exactly
one external resource — the typeface request inside the canonical head block.
Zero prohibited constructs, including inside script string literals and inside
markup built as a string. No shared foundation file edited. No relative reference
of the form the Codex payload build rewrites. Every color pairing drawn from the
brand kit's published audit; `--rc-border-subtle` never carries meaning; the
heading face is `--rc-font-display`.

**Scale/Scope**: 4 artifacts, 21 fill slots, 2 sequential pull requests, 1 new
validation module.

**Reviewability Budget**: Primary surface: docs/process (the shipped gallery
templates) | Projected reviewable LOC: 530 (per slice; see the derivation under
*Reviewability Projection* below) | Projected production files: 3 (per slice) |
Projected total files: 6 (slice 1; slice 2 authors 3) | Budget result: **warn** —
above the 400 warn threshold on lines, below the 800 block threshold, and inside
every file-count threshold. No `Reviewability-Exception` pragma is claimed,
because a warn is not a block.

## Declared File Operations

Authored files only. Generated payload copies are inventoried separately under
*Generated Artifact Contract* below, which is a deliberate placement: the
plan-phase estimator reads this block and stops at the next `##` heading, and it
exists to project the surface a human reviews. Mixing thirty machine-written
mirrors into it would misreport that surface in both directions.

### Slice 1 — US1 Implementation Plan, US2 Spec Explainer (PR 1, this branch)

- NEW speckit-pro/artifact-gallery/templates/implementation-plan.html
- NEW speckit-pro/artifact-gallery/templates/spec-explainer.html
- NEW tests/speckit-pro/unit/test-artifact-fill-regions.py
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED docs-site/src/content/docs/reference/tests.md

### Slice 2 — US3 Code Approaches, US4 Module Map (PR 2, fresh branch after slice 1 merges)

- NEW speckit-pro/artifact-gallery/templates/code-approaches.html
- NEW speckit-pro/artifact-gallery/templates/module-map.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json

Slice 2 declares no test change. That is a design outcome, not an omission: the
Layer 4 floor literal names all four templates from the moment it lands, and each
per-template case is conditioned on that template's catalog `status`. Flipping
the two remaining entries to `shipped` is what turns the remaining cases on, with
no edit to the test file. It follows that slice 2 also changes no tracked `.md`,
`.py`, or `.sh` file under `tests/speckit-pro/`, so the docs reference needs no
regeneration there — verify that by running the generator and confirming it
produces no diff, rather than by assuming it.

## Generated Artifact Contract

Machine-written, never hand-edited, produced by `python3
scripts/refresh-release-artifacts.py` and committed in the same pull request as
the source change that caused them (FR-039). Every gallery source file exists in
five copies: the source, two payload copies, and two installed-cache fixture
copies. Per slice, each new template and the catalog produce:

| Generated path pattern | Operation per slice |
|---|---|
| `dist/claude/speckit-pro/artifact-gallery/templates/<id>.html` | NEW, 2 files |
| `dist/codex/speckit-pro/artifact-gallery/templates/<id>.html` | NEW, 2 files |
| `dist/{claude,codex}/speckit-pro/artifact-gallery/manifest.json` | MODIFIED, 2 files |
| `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/artifact-gallery/templates/<id>.html` | NEW, 4 files |
| `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/artifact-gallery/manifest.json` | MODIFIED, 2 files |
| `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof*.json` | MODIFIED, 12 snapshots |
| `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` | MODIFIED |
| `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json` | MODIFIED |
| `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json` | MODIFIED |

Two facts checked against the ART-001 gallery commit rather than assumed:

- **No source change is needed to ship the new subdirectory.** The payload build
  copies `artifact-gallery` as a whole directory name, so `templates/` is carried
  without touching `speckit-pro/speckit_pro_runner/gates/payloads.py`.
- **The runner trust metadata does not move.** `speckit-pro-runner.manifest.json`
  and `speckit-pro-runner.sha256` changed in ART-001 only because that change
  edited a runner source file. ART-002 edits none, so neither file appears here.
  If either turns up dirty after a refresh, something outside this plan changed.

Do you count these as declared? **Yes — declared, and excluded from the budget.**
Declared, because FR-039 requires each slice to account for them and because the
routing contract reads a plan's file operations as evidence for the
`brownfield_change` signal. Excluded from the reviewable-line and production-file
counts, because a reviewer does not read a byte-for-byte mirror; a diff in one is
a build defect rather than a review target. Two mechanical notes for whoever
maintains this: the estimator's own exclusion rule covers `dist/**` and
`.process/` automatically, but it does **not** cover the installed-cache mirror
paths under `tests/`, which is the second reason those live under their own
heading rather than in the block above.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies as | Verdict |
|---|---|---|
| I. Plugin Structure Compliance | The gallery ships inside the plugin payload; a new `templates/` subdirectory must not disturb the validated layout, and repository-only tests must stay outside the install-facing directory. | **PASS** — templates land under `speckit-pro/artifact-gallery/templates/`, which the payload build already carries; the new test lands under `tests/speckit-pro/unit/`. Gate: `python3 tests/speckit-pro/run-all.py --layer 1`. |
| II. Cross-Platform Runtime & Script Safety | The new validation is repository tooling. | **PASS** — Python 3.11+ standard library only, `html.parser` as the structured parser, `pathlib` for paths, no Bash, no `jq`, no subprocess. Gate: Layer 4. |
| III. Semantic Versioning | No manual version edit. | **PASS** — release-please owns the bump; this feature edits no version field. |
| IV. Test Coverage Before Merge | New validation needs Layer 4 coverage and declared suite membership; new payload content needs Layer 1. | **PASS** — one module registered in `tests/speckit-pro/suite-manifest.json`, carrying both real-gallery cases and synthetic-fixture cases. Gate: full suite, zero failures. |
| V. Conventional Commits | PR titles are the squash commit. | **PASS** — planned titles: slice 1 `feat(speckit-pro): add the implementation-plan and spec-explainer gallery templates`; slice 2 `feat(speckit-pro): add the code-approaches and module-map gallery templates`. Both carry a `release-note` fence. |
| VI. KISS, Simplicity & YAGNI | The three capture-and-export templates need near-identical behavior with no shared runtime. | **PASS with a recorded decision** — the duplication is accepted rather than abstracted. See *The Shared Behavior Decision* below. |

**Post-design re-check (after Phase 1).** Re-evaluated against `research.md`,
`data-model.md`, `contracts/`, and `quickstart.md`. No verdict moves. The design
adds no dependency, no shell, no `jq`, and no subprocess; it adds one standard-library
module under the repository test tree and four static documents under a directory
the payload build already carries. Principle VI's recorded decision is unchanged
and now carries its full reasoning in `research.md` D1.

**Reviewability obligations the constitution attaches to every plan:**

- **Primary review surface**: the shipped gallery templates (docs/process).
  Secondary surfaces: seed/config, being the catalog's four `status` values; and
  harness/adapter, being the fill-region validation.
- **Budget position**: slice 1 and slice 2 each project above the 400-line warn
  threshold and below the 800-line block threshold, at three production-file
  entries against a six-file warn and six authored files against a fifteen-file
  warn. The single review surface named above is unchanged.
- **Split decision**: two vertical slices in two sequential pull requests, as
  FR-040 fixes. Slice 1 is US1 and US2 with their two status flips and the whole
  Layer 4 module; slice 2 is US3 and US4 with theirs, branched from a state that
  already contains slice 1's flips. No work is deferred to a follow-up
  specification except the generation of slot content, which is ART-007's.
- **PR review packet source**: this plan supplies what changed and why (Summary,
  the port worksheet), non-goals (the spec's Non-goals and the design concept's),
  review order (*Slice 1 Ordering*), scope budget (this section), traceability
  (the port worksheet's FR column and the test design's), verification evidence
  (`quickstart.md`), known gaps (*Complexity Tracking*), and rollback notes (each
  slice is additive plus a two-value catalog flip; reverting the commit restores
  the prior state with no migration).

### Reviewability Projection

The spec's Reviewability Budget records ~380 reviewable lines across the feature,
inherited from the roadmap's pre-read projection of four files at roughly 95 lines
each. Reading the contract and fixing the design raises that materially, and the
plan is where the honest figure belongs. The derivation, so a reviewer can check
it rather than take it:

| File | Embedded (not reviewed) | Authored (reviewed) | Basis |
|---|---|---|---|
| implementation-plan.html | 458 | ~320 (280–400) | 7 slots with worked content, a ported data-flow drawing, per-item disclosures built in script, two exports with fixed wording, a status region, ~90 lines of own styling |
| spec-explainer.html | 458 | ~185 (160–220) | 6 slots, no script of its own, no capture, no export |
| code-approaches.html | 458 | ~230 (200–280) | 3 slots, a grouped single-choice control plus one reason field, two exports, a comparison grid |
| module-map.html | 458 | ~300 (260–360) | 5 slots, a ported module drawing, per-item disclosures, two exports |

**Reviewable lines count authored lines only.** Each artifact embeds 458 lines of
canonical block — 318 from `BRAND-KIT`, 140 from `GALLERY-HEAD` — copied byte for
byte and compared byte for byte by the gallery validation. A reviewer reads none
of it, and a difference in it is a validation failure rather than a review
target. Generated mirrors are excluded on the same principle. The calibration
point for the authored figures is ART-001's own single-file artifact, which came
to 766 lines carrying both blocks, so 308 authored.

**The plan-phase estimator returns 0 for this feature, and that is a floor rather
than a measurement.** It projects lines as production-file count times forty, and
its production-file test recognizes a path under `src/`, `app/`, `lib/`, or
`scripts/`, or a file ending in a TypeScript, JavaScript, or SQL extension. None
of this feature's authored files match — not an `.html` artifact, not a `.py`
test, not a `.json` catalog — so it reports `production: 0, projected: 0`. Read it
as confirmation that the block parses and that nothing here is over budget by its
own rule, and read the derivation above for the number that actually governs. The
setup-mode gate, which reads the declared figures rather than inferring them, is
the one that returns the operative **warn**.

Slice 1 therefore projects ~505 authored template lines plus three modified
catalog and manifest lines; slice 2 projects ~530. The validation module (~250
lines) is excluded, as the spec's budget already scopes it out. Both slices land
in **warn**, and a warn proceeds here because the workflow file records the scope
budget and the split decision, which is the condition that section already
states. The stale sentence in the spec's Reviewability Notes — "Both slices are
projected within the warn thresholds" — is now contradicted by this derivation
and is carried into Analyze as a spec-amendment candidate rather than silently
adopted or silently ignored.

## The Shared Behavior Decision

Three templates need behavior that is nearly the same: mount a capture control
onto each item, read live state when an export is invoked, build two export
texts, and copy with a selectable fallback when the clipboard refuses. There is
no shared runtime. Every artifact is one self-contained file by contract, so the
code is duplicated by construction.

**Decision: duplicate it. Three copies, no extraction, no generator, no build
step.**

The alternatives are not merely worse, they are prohibited. A shared script file
is a sibling asset, which the single-file rule forbids. A build step that inlines
a common source is forbidden by name — "no build step, no bundler, no
preprocessor, no post-processing". A generator that stamps the routine into each
file at authoring time is a build step wearing a different name, and it is also
ART-007's job rather than this feature's: the design concept's Non-goals put
"generation/authoring logic that populates the fill regions" outside ART-002
explicitly. That leaves duplication as the only mechanism the contract permits,
which makes this less a judgement than an observation.

Given that, the constitution's YAGNI clause is the calibration rather than the
tie-breaker: "Three similar lines of code are better than a premature
abstraction." And the three are not three copies of one thing. Two of them —
implementation-plan and module-map — share the objection shape, differing in
their item noun and their slot name. The third, code-approaches, is a different
shape: one selection across a group plus one optional reason, with no per-item
disclosure at all. So the real duplication is one near-copy, not two.

**What is shared is the specification, not the code.** The exact strings an
export emits, the four coordinates that name an item, the one cause-neutral
clipboard failure message, and the empty-state wording per export kind are pinned
once in `contracts/export-payload-contract.md`, and each template is checked
against that one table by the acceptance runbook. Three implementations may drift
in style; they cannot drift in behavior, because the behavior is written down in
one place and verified against that place. That is the form of sharing available
to a set of files that cannot share a runtime, and it is the form that actually
protects the reader.

One trap the port must respect here, found during Clarify session 3 and recorded
in the workflow file: upstream `04-code-understanding.html` runs an accordion
script that force-closes every other `details.snippet` when one opens. That
behavior must not reach the objection disclosures — it would close a reader's
in-progress field the moment they opened another. Scope it by class, or drop it.

## Per-Template Port Worksheet

The input is the section-to-slot mapping fixed in Clarify session 3. What follows
turns it into work: what is lifted, what is authored fresh, what is dropped, and
what restyling costs.

### implementation-plan (US1, slice 1) — upstream `16-implementation-plan.html`

| Slot | Upstream region | Port action |
|---|---|---|
| `feature-header` | page head eyebrow and title | Lift structure, drop the prompt box beside it, re-token the type |
| `plan-stats` | the four-cell summary strip | Lift; re-token surfaces and boundaries |
| `phases` | the milestones section | Lift; **add the per-item `id` anchor to each phase**, which is what an objection attaches to |
| `data-flow` | the data-flow section and its caption | Lift the drawing whole; restyle only (below) |
| `mockups` | the mockups section | Lift; re-token |
| `risk-register` | the risks and mitigations section | Lift; re-token; the severity marker needs a non-color carrier |
| `task-inventory` | **none — authored fresh** | Reuse the key-code grid's layout shape, with new content |

- **Dropped**: the prompt box, the key-code section, the open-questions section.
  Each is feature-specific content no slot names, which FR-015 forbids carrying.
- **Restyling cost — the drawing.** Upstream hardcodes presentation attributes on
  every shape. They need not be rewritten: a presentation attribute carries no
  specificity, so any rule overrides it. The port adds class hooks and styles
  through them. It must **not** apply one blanket selector — that would flatten
  the two-tier text hierarchy and the inverted persistence node the drawing
  deliberately distinguishes. Each arrowhead needs its own selector, because a
  marker renders in its own context and does not inherit paint from the element
  referencing it. No upstream color value survives; every one is unaudited and
  no upstream source carries a theme-aware rule at all, so a retained value would
  leave the drawing unreadable in the dark theme (FR-030).
- **Accessibility work the port adds.** The drawing gets an accessible name and a
  text equivalent outside it, which upstream has not got (FR-030a). The inverted
  persistence node gets a text tag or a distinct shape, and its sub-label loses
  the unaudited accent (FR-032). The dashed edge and its caption port **intact** —
  the dash is a non-color carrier and the caption states the convention in words,
  so the caption is load-bearing rather than decoration.
- **Retained deliberately**: the drawing's absolute namespace declaration. It is
  exempt from the external-reference scan and must stay.
- **Authored fresh**: the objection disclosures, mounted at load onto each phase's
  anchor; the two export controls; the status region; the fallback field.

### spec-explainer (US2, slice 1) — upstream `14-research-feature-explainer.html`

| Slot | Upstream region | Port action |
|---|---|---|
| `feature-header` | header eyebrow and title | Lift; re-token |
| `tldr` | the TL;DR block | Lift; re-token |
| `goals` | **none — authored fresh** | New content and markup |
| `non-goals` | **none — authored fresh** | New content and markup, separate from goals |
| `acceptance-criteria` | no content counterpart | Borrow the step list's disclosure shape; new content |
| `clarification-faq` | the FAQ definition list | Lift; re-token |

- **Dropped**: the prompt box, the navigation, the step content, the
  configuration tabs, the gotchas. The navigation earns its drop twice: five of
  its nine links target the same anchor, which collides with the per-item anchor
  rule outright.
- **This template ports with no script of its own.** Upstream's single script
  exists only to drive the configuration tabs, which are dropped, so nothing needs
  it. That is what makes the read-only declaration **structural** rather than a
  judgement that its controls are benign — the template is incapable of capturing
  anything (FR-020).
- **Restyling cost**: one unguarded transform transition to drop or place behind
  the reduced-motion guard (FR-034). Otherwise re-tokening only.
- The `acceptance-criteria` disclosure carries **no** state text, unlike the
  objection disclosures on the other templates, because there is nothing here for
  a reader to record (FR-027).

### code-approaches (US3, slice 2) — upstream `01-exploration-code-approaches.html`

| Slot | Upstream region | Port action |
|---|---|---|
| `feature-header` | page head, minus the prompt box | Lift; re-token |
| `approaches` | the approaches grid, trade-off tables, chip footers | Lift; **add the per-item `id` anchor to each approach**; wrap, do not replace |
| `recommendation` | the recommendation aside | Lift; re-token |

- **Dropped**: the prompt box.
- **Trap.** Wrap the existing approaches container in the native grouping element
  rather than replacing it, so the side-by-side layout FR-028 requires survives
  the addition of the single-choice control.
- **Restyling cost — the trade-off markers.** Upstream draws two identical shapes
  separated only by hue. The non-color carrier already exists in the markup: a
  persistent column heading and a fixed column position. The port declares those
  as the carrier and either drops the markers as redundant or gives them distinct
  glyphs, so a single row lifted out of the table still reads (FR-032).
- **Port verbatim, and expect a false alarm**: this source contains three escaped
  handler-shaped strings inside displayed sample code. A parse confirms they are
  text nodes, not attributes, so they are not prohibited constructs and must port
  unchanged. A reviewer running a naive text search will find all three.
- **Authored fresh**: the grouped single-choice control with a visible group label
  as its accessible name; the optional reason field; the two export controls; the
  status region; the fallback field.

### module-map (US4, slice 2) — upstream `04-code-understanding.html`

| Slot | Upstream region | Port action |
|---|---|---|
| `feature-header` | header repo line and title | Lift; re-token |
| `module-summary` | the summary paragraph | Lift; re-token |
| `module-graph` | the request-path heading and diagram panel | Lift the drawing whole; restyle (below) |
| `modules` | the callstack walkthrough | Lift; **add the per-item `id` anchor to each module** |
| `key-files` | the key-files aside | Lift; re-token |

- **Dropped**: the gotchas section.
- **Restyling cost — cheaper than the other drawing.** This one already styles
  through classes, so restyling is a token swap in the rules it already has, plus
  one rule for the arrowhead, which needs its own selector for the same reason as
  above.
- **The distinguished path is the main accessibility work.** Upstream marks it by
  fill tint and boundary hue alone, and its tint is an unaudited blend over an
  unknown backdrop, so neither survives. The port carries the distinction by
  **boundary weight and a visible text tag, never by color** (FR-029), which is
  also what keeps it identifiable in a monochrome rendering. The drawing gets an
  accessible name and a text equivalent outside it (FR-030a).
- **No marker pair goes inside the drawing.** The distinguished path is a required
  property of `module-graph`'s content, not a slot of its own; a pair inside the
  figure would split one drawing across two fill operations that share a
  coordinate system.
- **Restyling cost**: one unguarded transform transition to drop or guard
  (FR-034).
- **Authored fresh**: the objection disclosures mounted onto each module's anchor;
  the two export controls; the status region; the fallback field.

## The Layer 4 Test Design

**File**: `tests/speckit-pro/unit/test-artifact-fill-regions.py`
**Layer**: 4, registered in `tests/speckit-pro/suite-manifest.json` with
`"label": "test-artifact-fill-regions"` and `"baseline": null`.

The name states the durable capability — fill-region validation — and carries no
spec identifier, as FR-037 requires and the repository's editing boundaries
repeat. Python 3.11+ standard library only.

### How it parses, and why comment-shaped text in a script is not a comment

It reuses the gallery scanner's comment-collection idiom: an `html.parser`
subclass whose `handle_comment` appends to a list, so what the checks see is the
sequence of **parser-recognized** comments in document order. That word is
load-bearing and it is the same distinction the existing scanner turns on when it
locates an attribution header.

`html.parser` reads a `script` element's content as raw character data. It never
emits `handle_comment` for anything inside one, so `<!-- FILL:phases:START -->`
written inside a script string literal is not a comment and does not register as
a slot. That matters concretely here: a template's own export routine builds text,
and a routine that happened to embed a marker in a literal must not be able to
"declare" a region the body does not actually delimit. Reading markers as parsed
comments closes that by construction rather than by a rule someone has to
remember.

The anchor check needs element positions as well as comments. One parser subclass
serves both: `HTMLParser` delivers comments and start tags through the same
instance in document order, so `handle_comment` toggles which slot is currently
open and `handle_starttag` records the elements opened inside it, with a depth
counter identifying which of them sit at the region's own top level.

### The checks

| ID | Asserts | Requirement |
|---|---|---|
| R1 | For every template the pinned floor names whose catalog entry reads `shipped`, each slot in that template's floor set is present as a marker pair. A **subset** check: a template may carry more slots than the floor names. | FR-036 |
| R2 | Every slot named in the file's inventory has exactly one marker pair in the body, start before end. | FR-013 |
| R3 | Every marker pair in the body is named in the inventory. | FR-013 |
| R4 | The inventory is a single parser-recognized comment placed immediately after the attribution header, carrying none of the attribution header's labels or literals; each line reads `Slot: … \| Fills: … \| Source: …` in that order with no pipe inside a value; names are kebab-case and unique within the template; every `Source:` value is drawn from the closed five-name set. | FR-012, FR-015 |
| R5 | **Its own assertion.** In every slot the pinned list-slot literal names, each element opened at the region's own top level carries an `id` matching `<slot>-<item-slug>`, ids are unique document-wide, and the region holds at least two such elements. | FR-036a |
| R6 | Every template identifier the floor literal names is an identifier the catalog carries. | FR-036 |

R2 and R3 are opposite directions on one claim and are separate checks, because
either direction alone misleads the authoring agent and a single check reporting
both would name the wrong defect half the time.

**R5 is separate from R1 on purpose**, and the reasoning is worth keeping because
Clarify escalated it to a unanimous three-analyst round. Adding `modules` to the
floor would prove only that a region of that name exists — never that its items
are individually addressable — so the floor cannot verify FR-016 even in
principle. And every floor entry traces to the roadmap and to nothing else; an
entry sourced from a different requirement would make the literal unauditable.
Testing the requirement beats testing a proxy.

### The two pinned literals

Both are held in the test file and neither is read back out of a template. A set
derived from the file under validation asserts only that the file equals itself.

**The floor** (traces to the roadmap's ART-002 scope, and to nothing else):

- `implementation-plan`: `phases`, `data-flow`, `mockups`, `risk-register`, `task-inventory`
- `spec-explainer`: `tldr`, `goals`, `non-goals`, `acceptance-criteria`, `clarification-faq`
- `code-approaches`: `approaches`
- `module-map`: `module-graph`

**The list slots** (traces to FR-016 and FR-017 — the slots whose items an
objection or a selection attaches to):

- `implementation-plan`: `phases`
- `code-approaches`: `approaches`
- `module-map`: `modules`

`spec-explainer` has none, which is the read-only declaration showing up in the
validation rather than only in prose.

### Case structure, and the vacuity it closes

Two case classes per group, mirroring the existing gallery scanner:

- **Real-gallery cases** take the gallery root as a parameter and run against the
  shipped tree. Each per-template case is conditioned on that template's catalog
  `status`, so it binds from the moment its entry flips and not before.
- **Synthetic-fixture cases** build a small gallery in a temporary directory and
  assert that each check **detects** its defect: a missing floor slot, an
  inventory entry with no marker pair, a marker pair absent from the inventory, a
  malformed inventory line, a repeated item with no anchor, a duplicated anchor.

The fixture cases exist because the real gallery ships zero templates when the
test lands, and a check that only ever runs against the real tree would pass by
vacuity and prove nothing. They are also what makes a genuine RED possible before
any template exists.

## Slice 1 Ordering

The constraint is that the Layer 4 module is written RED before the templates
exist. It is met by the fixture cases, not by the real-gallery cases — the real
ones cannot go red on an empty gallery, they can only go vacuous.

1. **Write the fixture cases and the pinned literals; leave the check functions
   unimplemented.** Run the module directly. It fails: every fixture asserts a
   detection that does not happen yet. **This is the RED**, and it is a real one,
   independent of whether any template has shipped.
2. **Implement the parser and the six checks.** Fixtures go green. Real-gallery
   cases run and report nothing, because no entry reads `shipped` yet.
3. **Register the module** in `tests/speckit-pro/suite-manifest.json` at layer 4;
   regenerate `docs-site/src/content/docs/reference/tests.md`.
4. **US1**: fetch `16-implementation-plan.html` read-only into the session
   scratchpad, author the branded derivative, and flip its catalog `status` in
   the same change. The file and the flip cannot be separated — the contract
   fails a file without a flip and a flip without a file, in both directions.
   R1's implementation-plan case binds here for the first time.
5. **US2**: the same for `14-research-feature-explainer.html` and its entry.
6. **Payload regeneration and closeout**: `python3
   scripts/refresh-release-artifacts.py`, then the full suite, then the
   acceptance runbook.

Steps 4 and 5 are parallel-safe with respect to each other. Steps 1–3 are not
parallel with anything: they are one file, and it is the file both templates are
measured by.

Slice 2 repeats steps 4–6 for the two conditional templates from a fresh branch
cut after slice 1 merges, so it starts from a catalog that already carries slice
1's flips (FR-040). It does not reapply them.

## Project Structure

### Documentation (this feature)

```text
specs/art-002-draft-pr-template-set/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── slot-inventory-contract.md
│   └── export-payload-contract.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
speckit-pro/artifact-gallery/
├── SPA-CONTRACT.md          # normative; read, never edited
├── manifest.json            # MODIFIED — status values only, two per slice
├── brand-kit.css            # BRAND-KIT source; read, never edited
├── theme-toggle.html        # GALLERY-HEAD source; read, never edited
├── UPSTREAM-NOTICE.md       # licence text the header points at; never edited
└── templates/               # NEW directory
    ├── implementation-plan.html   # NEW, slice 1
    ├── spec-explainer.html        # NEW, slice 1
    ├── code-approaches.html       # NEW, slice 2
    └── module-map.html            # NEW, slice 2

tests/speckit-pro/
├── suite-manifest.json                     # MODIFIED — one layer 4 entry
└── unit/
    ├── test-artifact-gallery.py            # existing scanner; covers the new files automatically
    └── test-artifact-fill-regions.py       # NEW, slice 1

scripts/refresh-release-artifacts.py        # run, never edited
docs-site/src/content/docs/reference/tests.md  # regenerated, never hand-edited
```

**Structure Decision**: No new top-level structure. The artifacts land in the one
directory the routing catalog already derives their paths from —
`<directory holding manifest.json>/templates/<id>.html` — so the filename stem is
the entry identifier by construction and no path is stored anywhere. Validation
lands beside the gallery scanner it complements, in the repository-only test tree
outside the install-facing plugin directory.

## Complexity Tracking

> Filled where the Constitution Check records a decision that needs justifying.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Capture-and-export behavior duplicated across three artifacts | Each artifact is one self-contained file by contract, with no shared runtime, no sibling asset, and no build step. Duplication is what the contract leaves. | A shared script file is a prohibited sibling asset. A build step that inlines a common source is prohibited by name. A generator that stamps the routine in is a build step renamed, and is ART-007's scope rather than this feature's. The constitution prefers three similar lines to a premature abstraction, and only one of the three is a near-copy of another. |
| Projected review size lands in **warn** on both slices | Every slot must ship worked example content (FR-014), both drawings are ported rather than simplified (FR-030), and the capture affordances ship working in this feature rather than being deferred (FR-016a). Removing any one of those would put the slice under 400 lines and break a requirement. | Splitting into four single-template pull requests was rejected: FR-040 fixes two sequential pull requests, and a per-template split would put the Layer 4 module in its own pull request, landing validation that binds nothing. Deferring worked content to ART-007 was rejected by FR-014 — it leaves a gallery browser judging a template by an empty frame. |

# Implementation Plan: Final-PR Template Set — Slice 1, the PR Write-up Artifact

**Branch**: `art-003-final-pr-template-set` | **Date**: 2026-08-12 | **Spec**: `specs/art-003-final-pr-template-set/spec.md`

**Input**: Feature specification from `specs/art-003-final-pr-template-set/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Ship one branded, self-contained HTML artifact at
`speckit-pro/artifact-gallery/templates/pr-writeup.html`, flip its catalog entry
from `planned` to `shipped`, and add the three literals the fill-region
validation needs to bind it. The artifact carries seven fill regions, per-section
question capture, and both declared export kinds.

Every design question except one was settled by three Clarify sessions and is
recorded in `spec.md` as FR-011a through FR-039a. This plan does not re-derive
any of it. It does three things the spec left to this phase:

1. **Resolves the last open marker.** It adopts the document-section CSS ceiling
   as an explicit, checkable constraint, states the instrument that checks it,
   and names the three checkpoints where the check runs and can stop the work.
2. **Re-declares the reviewability figure** against the decomposition rather
   than against the discarded upstream-line multiplier, and records that the
   plan-phase estimator is structurally blind here and its `pass` is not
   evidence.
3. **Authors `contracts/export-payload-contract.md`**, which FR-029a requires
   because the document all three shipped templates cite in a source comment was
   deleted when ART-002 was archived and now resolves nowhere.

The technical approach is a port, not an invention. Upstream
`17-pr-writeup.html` supplies structure and six `<details>` disclosures; it
supplies **no** export behaviour, because it ships zero `<script>` and zero
`<button>` tags. Every line of export and question capture is authored fresh
against the shape three shipped templates already prove.

## Technical Context

**Language/Version**: HTML5, CSS (custom properties, no preprocessor), and
inline JavaScript written in the same conservative dialect the three shipped
export-carrying templates use — `var`, function declarations, no module syntax,
no optional chaining. Repository validation is Python 3.11+ standard library
only.

**Primary Dependencies**: None at runtime, by contract. The artifact embeds two
canonical blocks verbatim and loads nothing else: `BRAND-KIT` from
`speckit-pro/artifact-gallery/brand-kit.css` (318 lines) and `GALLERY-HEAD` from
`speckit-pro/artifact-gallery/theme-toggle.html` (140 lines). The single
permitted external reference is the brand typeface request that arrives inside
`GALLERY-HEAD`.

**Storage**: N/A. The artifact persists nothing of its own. Theme persistence
belongs to the head block and degrades to session-only when a browser refuses
storage for a local file.

**Testing**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5). Layer 4
carries the gallery scanner and the fill-region validation, which are the two
that bind this artifact. Browser behaviour is not machine-verifiable here — the
suite is Python-stdlib-only — so the `file://` render is manual acceptance
evidence under FR-042.

**Target Platform**: Any current browser opening the file directly from a
filesystem, with no server, no install, and the network unavailable.

**Project Type**: A single-file HTML artifact shipped inside a plugin payload,
plus a two-line change to repository-only validation and a one-value change to a
JSON catalog.

**Performance Goals**: N/A. No measurable performance requirement exists for a
static document of six sections.

**Constraints**: One file, no sibling asset, no build step. WCAG AA pairings from
the kit's audited set only. Nothing carries meaning by colour alone. The heading
typeface token is `--rc-font-display`; `--rc-font-heading` is undefined and an
undefined custom property fails silently. `--rc-border-subtle` carries no
meaning anywhere. The authored total must land under the 800 block threshold,
and the component CSS ceiling below is what decides whether it does.

**Scale/Scope**: One template. Seven fill regions, one of them a list slot. Two
export kinds. Three literals added to shared validation and one catalog value
changed.

**Reviewability Budget**: Primary surface docs/process; projected reviewable LOC
758; 1 production file; 13 total files; budget result warn. Decomposed and
measured below, not scaled from a multiplier.

## Declared File Operations

- NEW speckit-pro/artifact-gallery/templates/pr-writeup.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-fill-regions.py
- NEW specs/art-003-final-pr-template-set/contracts/export-payload-contract.md

Those four are the change. Three obligations attach to them.

**The catalog value and the file land together.** `SPA-CONTRACT.md` binds status
and file presence in both directions: an artifact file exists if and only if its
entry reads `shipped`. Adding the file without the flip fails as an orphan, and
the flip without the file fails as a missing artifact. Neither may be committed
alone.

**The generated-artifact contract applies.** The gallery ships inside the plugin
payload, so a new template file changes shipped bytes on both platforms. Run
before calling the work done:

```text
python3 scripts/refresh-release-artifacts.py
```

That rewrites `dist/claude/**` and `dist/codex/**`, the runner trust metadata,
the installed-cache fixtures, and the payload evidence. Those paths are
generated, are marked `merge=generated` in `.gitattributes`, and are excluded
from the reviewability count by the gate's own generated-path rule — which is
why they are not declared as entries above. CI's `artifact-consistency` job
fails the pull request if the regeneration is skipped.

**The docs reference regenerates too.** `test-artifact-fill-regions.py` is a
tracked `.py` file under `tests/speckit-pro/`, so its change restales the
generated docs-site test reference:

```text
pnpm --dir docs-site install --frozen-lockfile   # once per worktree
pnpm --dir docs-site reference:generate
```

`refresh-release-artifacts.py` does **not** cover this surface; its own help text
says so.

## The reviewability decision

This is the last open marker in `spec.md`, and the plan resolves it by adoption
rather than by referral.

### Decision: adopt the ceiling as an explicit, checkable constraint

The five constraints below are numeric acceptance criteria, not aspirations.
Each is measured by one instrument, at a named checkpoint, with a stop rule.

| # | Constraint | Ceiling |
|---|---|---|
| C1 | Document-section CSS — the six titled sections and page chrome | ≤ 150 |
| C2 | Question and export CSS — disclosures, controls, status, fallback | ≤ 97 |
| C3 | Export and question-capture JavaScript | ≤ 288 |
| C4 | Markup — seven regions, sample content, six question mount points | ≤ 223 |
| C5 | Authored total (C1 + C2 + C3 + C4) | ≤ 758, hard stop below 800 |

C1 is the only one that can miss. C3 is measured against three shipped
implementations of the same routine and is a floor rather than an estimate. C2
and C4 are measured off the precedent's own selectors and markup. The evidence
for each is in `research.md`.

### The instrument

One command, no new file, no new dependency, Python 3.11 standard library. It
partitions a gallery artifact into the canonical blocks and the three authored
kinds:

```text
python3 -c '
import sys,pathlib
L=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
def sp(a,b):
    s=next(i for i,l in enumerate(L) if a in l); e=next(i for i,l in enumerate(L) if b in l); return set(range(s,e+1))
canon=sp("BRAND-KIT:START","BRAND-KIT:END")|sp("GALLERY-HEAD:START","GALLERY-HEAD:END")
n={"css":0,"js":0,"markup":0}; sty=scr=False
for i,l in enumerate(L):
    a=b=False
    if "<style" in l and "</style>" not in l: sty=True; a=True
    if "<script" in l and "</script>" not in l: scr=True; b=True
    if i not in canon: n["css" if (sty and not a) else "js" if (scr and not b) else "markup"]+=1
    if "</style>" in l: sty=False
    if "</script>" in l: scr=False
print("authored",len(L)-len(canon),"| css",n["css"],"| js",n["js"],"| markup",n["markup"])
' speckit-pro/artifact-gallery/templates/pr-writeup.html
```

**Calibrated against all four shipped templates**, run 2026-08-12:

| Template | authored | css | js | markup |
|---|---|---|---|---|
| `spec-explainer` | 315 | 169 | 0 | 146 |
| `module-map` | 1002 | 448 | 293 | 261 |
| `code-approaches` | 1025 | 471 | 298 | 256 |
| `implementation-plan` | 1221 | 661 | 277 | 283 |

Two properties make this the right instrument rather than an approximation.

It **reproduces the spec's recorded figures within two lines** on every template
(recorded 316/1003/1026/1222 authored; 171/450/473/663 CSS), so the ceilings
stated in its units trace directly to the evidence the spec cites. The offset is
constant and explained: the recorded pass counted the `<style>` and `</style>`
delimiter lines into CSS, and this one counts them as markup.

It is **internally consistent**, which the recorded pass is not. Here
`css + js + markup` equals `authored` exactly on all four templates. The recorded
decomposition sums to 318 against a recorded total of 316 on `spec-explainer`,
because the two delimiter lines are counted twice. A ceiling checked with a
double-counting instrument is a ceiling nobody can hold precisely, so this plan
fixes one definition and states it.

`spec-explainer` is the comparator because it is the only shipped template of
this class: six fill regions of prose and lists, no diagram. Its 169 authored CSS
lines are what the 150 ceiling is set against, with 19 lines of margin already
spent on the fact that `pr-writeup` carries a two-panel comparison
`spec-explainer` does not.

### The checkpoints, and the stop rule

Three measurement tasks enter `tasks.md`, ordered so the ceiling is tested
before the expensive work compounds on top of it. Each is a task with a numeric
acceptance criterion and a recorded result.

| Checkpoint | Runs after | Gate | On failure |
|---|---|---|---|
| **M1** | the six sections' CSS is written, before any question or export CSS | `css ≤ 150` | **Stop.** Do not proceed to M2. Apply the reduction levers below and re-measure. |
| **M2** | the question and export CSS is written | `css ≤ 247` | Stop. Reduce, re-measure. |
| **M3** | the export routine and all markup are written, before the pull request | `authored ≤ 758` | Stop. Reduce, re-measure. Escalate above 800. |

M1 is the checkpoint that matters. It is the earliest moment the ceiling can
fail and the cheapest moment to fix it, and putting it before the export work
means a failure surfaces with roughly 150 lines written rather than 758. The
three shipped templates that missed this ceiling had no such checkpoint.

**Review instruction.** The pull-request body records all four numbers and the
checkpoint each was taken at, so a reviewer reads a measurement rather than a
claim. This is a PR Review Packet obligation the spec already carries under
"scope budget", now given a concrete payload.

### The reduction levers, in order

Named now so that a failure at M1 has a plan rather than a negotiation:

1. **One rule set for six sections.** The six are structurally identical: one
   `.section` rule and one `h2` rule serve all of them. Write no per-section
   selector. `spec-explainer` styles six regions with a single `h2` rule and is
   the proof this is sufficient.
2. **Share the disclosure styling.** `file-by-file`'s items are `<details>`
   elements (FR-020 requires an element with a mandatory end tag), and the
   question controls are also `<details>`. One base rule set covers both uses.
   Writing two sets is the single largest avoidable cost in C1 plus C2.
3. **Cap `before-after`.** It is the only section needing bespoke layout. One
   grid or flex rule plus one panel rule, and no responsive refinement beyond a
   single `flex-wrap`.
4. **No hover-only refinement.** A hover state carries no meaning under FR-032,
   so it is decoration paid for in lines.
5. **Inherit rather than restate.** The kit already assigns every heading level
   its own typeface: the display token on `h1` and `h2`, and the body token at
   weight 600 from `h3` down, because the brand system reserves the geometric
   display face for the top of the page. It is one assignment per level, not one
   token across all six — restating it as the latter is what leads a port to name
   `--rc-font-display` on an `h3` and reintroduce a fidelity defect the kit
   records as already caught against the brand source. A port that writes
   ordinary headings and paragraphs gets the right face for each level free;
   naming any of them again is lines for nothing and a chance to name the wrong
   one.

If all five are applied and M1 still exceeds 150, the ceiling has failed on
evidence rather than on discipline. That is the point at which the exception
question goes to the operator, and it is a different question from the one the
spec asked, because it would then be backed by a measurement of this port rather
than by an inference from three templates that draw diagrams.

### Why the check is not a committed test

Considered and rejected, for three independent reasons:

- **It would consume the budget it protects.** A test file plus its manifest row
  is authored lines on the slice whose size is the problem.
- **It would be wrong for slices 2 and 3.** The ceiling is a *document-class*
  constraint. `annotated-diff` renders a diff and `flowchart` renders inline SVG;
  both are legitimately diagram-class and neither can meet 150. A committed
  threshold would either fail them or be widened until it constrained nothing.
- **It would contradict FR-039a**, which fixes this slice's change to shared
  validation at exactly three literals: the floor row, the list-slot row, and the
  source-set member.

The instrument is therefore a recorded command run at recorded checkpoints, which
is checkable without being permanent.

### The re-declared figure

**758 authored lines**, decomposed:

| Component | Lines | Basis |
|---|---|---|
| Export and question-capture JavaScript | 288 | The shipped precedent's 293, less 19 for resolving six named sections by id instead of walking a list container (FR-023c), plus 13 for the stale-settle guard (FR-026a), plus 1 rounding. |
| Question and export CSS | 97 | Measured off `module-map`'s own selectors: the objection disclosure block and the export controls, status, and fallback, excluding the panel chrome that belongs to C1. |
| Six document sections' CSS | 150 | Against `spec-explainer`'s measured 169 for six regions, less the rules this port does not need. |
| Markup | 223 | Seven regions with sample content held to the demonstrating minimum, six question mount points, and the export chrome. Raised from 215 at Checklist; see below. |
| **Total** | **758** | |

Excluded: the 458 canonical lines a reviewer never reads because they are
byte-verified copies (`BRAND-KIT` 318, `GALLERY-HEAD` 140, both measured).

**Markup moved from 215 to 222 at Checklist, and the total from 750 to 757.**
The earlier markup figure assumed `file-by-file` would ship two sample items,
which rested on FR-018 reading `MINIMUM_ITEMS = 2` in the fill-region validation
as the count a list region ships. It is a floor: the rule fails only on
`len(anchored) < 2` (`test-artifact-fill-regions.py:711`), and no cap exists
anywhere in the module. Two is also below every shipped anchored list —
`modules` 5, `phases` 4, `approaches` 3. FR-018 now fixes `file-by-file` at
three, which is the low end of that convention and the smallest count that shows
the region is heterogeneous rather than a list of source files.

Seven lines buy it, both measured rather than estimated:

- **+6** for the third `file-by-file` item, at the 6.0 authored lines per
  anchored repeated entry `implementation-plan`'s `phases` region ships (24
  lines, 4 items).
- **+1** for FR-018a's sample notice, one markup line reusing the muted-paragraph
  rule FR-019a's standing sentence already requires, so it adds no CSS rule.

`non-goals` and `verification` stay at two: they carry no per-item anchor, so no
rule counts them, and `verification` teaches through FR-018's both-states rule
instead of through length, which costs nothing. **Nothing was shrunk elsewhere to
absorb the seven lines.**

**A further line was charged at Checklist by the accessibility pass, taking
markup to 223 and the total to 758.** Without scripting the export region would
stay on screen offering an action nothing can perform, which is the FR-028
failure arriving by another road: a reader who cannot see a result cannot tell a
broken copy from a silent one. The region therefore ships hidden and the routine
that already runs at load reveals it. The hidden state is an attribute on a
container line that exists anyway, so the charge is the single reveal statement.
Every other remediation in that pass cost nothing — each fixed wording, an
inventory value FR-014 already makes mandatory, or the placement of a guard
FR-026a already budgets.

**Headroom is 42 lines, or 5.3%**, down from 50. That is the honest risk
statement. The decomposition holds or the slice blocks; there is no third outcome
and no slack absorbing an overrun.

**Budget result: warn.** Above the 400 warn threshold, below the 800 block
threshold. No `Reviewability-Exception` pragma is claimed and none is available:
the accepted classes are `refactor`, `infra`, and `upgrade`, and none honestly
describes net-new template work.

**Split decision: none available, and none needed.** This spec is already the
split — ART-003 ships as three stacked slices, one template per pull request, and
this is slice 1. A self-contained HTML artifact cannot be divided across two pull
requests and still render from a filesystem, so one template per PR is the
thinnest vertical slice this work admits. `annotated-diff` and `flowchart` are
slices 2 and 3, cut from their predecessor after each prior pull request is open.
Deferred work is named there; nothing in this slice is shaped to suit them.

**Total files corrects the spec's ~5 to 13.** The spec enumerated the change's
own surface plus `spec.md` and did not count the SpecKit planning artifacts the
same pull request carries. The honest list: the artifact, the catalog, the
validation, this slice's export-payload contract, `spec.md`, `plan.md`,
`research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, three checklists —
13 authored files, plus the SPEC-MOC and workflow-file updates and the
regenerated payload, which are process and generated surfaces respectively. 13 is
below the 15 warn threshold and far below the 25 block threshold, so the budget
result is unchanged.

### The plan-phase estimator is blind here, and its result is not evidence

Autopilot runs `estimate-reviewable-loc` after G3. **Its output must not be read
as reassurance about this slice.** Both causes were verified directly against the
helper source in the installed plugin cache, version 2.23.0:

1. **It counts files and opens none.** The projection is literally
   `projected = production * 40`. A 40-line artifact and a 1200-line artifact
   project identically.
2. **It classifies none of this slice's paths as production.**
   `is_production_file` returns true only for a path beginning `src/`, `app/`,
   `lib/`, or `scripts/`, or ending `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`,
   or `.sql`. Every declared entry above fails both tests — including the `.py`
   validation module, because `.py` is not in that suffix list.

So `production = 0` and `projected = 0`, and the status reads `pass`. One
correction to the note carried in the workflow file: because two declared entries
are `MODIFIED` and neither is a generated path, `greenfield` resolves **false**,
so the reported thresholds will read `warn: 400, block: 800` rather than the
greenfield pair. The `pass` and the `0` are unaffected.

Record the helper's result as a known-blind diagnostic with that reason beside
it. The authoritative figure is the decomposition above, measured with the
instrument above. This is the same shape of false comfort that let ART-002 reach
pull-request creation believing it was at 530.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.2.0. Evaluated pre-design and re-evaluated after Phase 1
design; both passes are recorded here and neither changed a verdict.

| Principle | Applies how | Verdict | Evidence |
|---|---|---|---|
| **I. Plugin Structure Compliance** | The gallery ships inside the plugin payload. The new template must live at the path derived from its catalog identifier, and repository-only tests stay under `tests/speckit-pro/`. | **PASS** | The artifact lands at `templates/pr-writeup.html`, the stem its entry already declares. The validation change edits an existing module under `tests/speckit-pro/unit/`; no test file is added and none moves. Gate: `python3 tests/speckit-pro/run-all.py --layer 1`. |
| **II. Cross-Platform Runtime & Script Safety** | Repository tooling stays on Python 3.11+ standard library with no Bash or `jq` dependency. | **PASS** | The only repository-tooling change is three literals in an existing stdlib-only Python module. The measurement instrument is an ad-hoc `python3 -c` invocation, committed nowhere, adding no dependency and no file. Gate: `python3 tests/speckit-pro/run-all.py --layer 4`. |
| **III. Semantic Versioning** | No version field is hand-edited. | **PASS (not engaged)** | Release-please owns version bumps. This slice edits no `plugin.json` and no marketplace version. |
| **IV. Test Coverage Before Merge** | The shipped template must be bound by Layer 4 rather than passing vacuously. | **PASS** | The floor row `FLOOR["pr-writeup"]` is what brings this template into the per-template universe; without it R1 through R5 skip it entirely. The list-slot row binds `file-by-file`'s item anchors under R5. SC-008 states the non-vacuity requirement directly. Gate: `python3 tests/speckit-pro/run-all.py`. |
| **V. Conventional Commits** | The pull-request title is the squash-merge commit message. | **PASS (deferred to PR time)** | Title validated through the live release-readiness gate before creation, in the form `<type>(<lowercase-scope>): <plain English description>`. |
| **VI. KISS, Simplicity & YAGNI** | The artifact carries no affordance its catalog entry does not declare, and the port adds no abstraction. | **PASS** | Both declared export kinds ship and nothing else; the entry declares `["prompt","markdown"]`. FR-019b ships **no** empty-state element, because nothing in the artifact reads the record at render time — the authoring agent can distinguish the three cases and the template cannot, so the markup would be dead in every real fill. The port drops seven upstream regions that map to no fill region. Six sections share one rule set rather than six. |

**Required plan definitions, per the preset:**

- **Primary and secondary surfaces.** Stated in the Declared Figures block below
  and in Technical Context. One primary surface; two secondary.
- **Budget position.** `warn` — above 400 authored lines, below 800; 1 production
  file against a 6 warn and 8 block; 13 total files against a 15 warn and 25
  block; one primary surface. Recorded above with its decomposition.
- **Split decision.** Recorded above: this spec is the split, slices 2 and 3 are
  the named follow-ups, and no further split is available.
- **PR review packet source.** `spec.md` carries the requirement; this plan
  supplies the material. What changed and why come from the Summary; non-goals
  from `spec.md` *Out of Scope*; review order from the rule below; scope budget
  from the four measured numbers and their checkpoints; traceability from the
  FR-to-file map in `data-model.md`; verification from `quickstart.md` and the
  suite; known gaps are the five carried out of Clarify plus the two this plan
  adds; rollback is the catalog value returning to `planned` together with the
  file's removal, since the contract binds them in both directions.

**Review order.** Authored markup and JavaScript first, then the CSS, then the
validation and catalog changes. The 458 canonical lines are read last or not at
all — they are byte-verified copies, and validation names the artifact and the
block on a single character of drift.

## Project Structure

### Documentation (this feature)

```text
specs/art-003-final-pr-template-set/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── export-payload-contract.md   # Phase 1 output — required by FR-029a
├── checklists/          # Phase 4 output (/speckit-checklist)
├── spec.md              # Phase 1 input
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/                              # Plugin source, ships to installers
└── artifact-gallery/
    ├── manifest.json                     # Routing catalog — one value flips
    ├── SPA-CONTRACT.md                   # Read-only input; amending it is out of scope
    ├── brand-kit.css                     # BRAND-KIT canonical block, 318 lines
    ├── theme-toggle.html                 # GALLERY-HEAD canonical block, 140 lines
    ├── UPSTREAM-NOTICE.md                # Licence text the attribution header cites
    └── templates/
        ├── spec-explainer.html           # The document-class comparator
        ├── module-map.html               # The export-routine precedent
        ├── code-approaches.html
        ├── implementation-plan.html
        └── pr-writeup.html               # NEW — this slice

tests/speckit-pro/
└── unit/
    ├── test-artifact-gallery.py          # Gallery scanner — unchanged
    └── test-artifact-fill-regions.py     # FLOOR, LIST_SLOTS, SOURCE_ARTIFACTS

scripts/refresh-release-artifacts.py      # Payload regeneration
dist/claude/**, dist/codex/**             # Generated payload — never hand-edited
```

**Structure Decision**: No new directory and no new module. The artifact lands
beside the four shipped templates under
`speckit-pro/artifact-gallery/templates/`, which is the path the catalog derives
from the entry's identifier rather than one this plan chooses. The validation
change is three literals inside an existing module, so no test file is created
and none is renamed — which also satisfies the repository rule against coupling a
test filename to a spec ID.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No principle violation is claimed. Every gate above reads PASS. Two decisions
depart from a shipped precedent, and both are recorded here because a reviewer
will otherwise read the departure as the defect rather than the fix.

| Departure | Why needed | Simpler alternative rejected because |
|-----------|------------|--------------------------------------|
| The export routine carries a currency token compared when a copy settles (FR-026a, +13 lines), which no shipped template carries. | Two exports invoked in quick succession let a superseded settle overwrite the current outcome: a rejected first copy announces a failure that did not happen and leaves the first kind's payload in the fallback field after the second kind copied. Both settle paths need it, since a slow success after a fast failure is the mirror case. | Copying the shipped routine unchanged is simpler and reproduces a defect present in all three export-carrying templates. The 13 lines are fully paid for by the 19 saved on the collection strategy. |
| The question control is appended to the **end** of its section rather than inserted immediately after the anchor, departing from the letter of the recovered export-payload contract. | In the shipped templates the anchor is a list item, so "immediately after it" follows the content being questioned. Here the anchor is the section heading, so the same rule would place the control between the heading and the content the reader has not read yet. | Following the contract's letter breaks the reading-order rationale the contract itself gives for the rule. The divergence is recorded explicitly in this slice's contract, with the reasoning, so it does not read as a violation. |

## Declared Figures (read by the setup reviewability gate)

The gate takes the **last** match of each phrase below in this file, so this
block is last on purpose. Append nothing after it.

- **Primary surface**: docs/process
- **Secondary surfaces**: seed/config (one catalog value), harness/adapter (three literals in the fill-region validation)
- **Projected production files**: 1
- **Projected total files**: 13
- **Projected reviewable LOC**: 758

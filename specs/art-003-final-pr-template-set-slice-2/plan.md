# Implementation Plan: Final-PR Template Set — Slice 2, the Annotated Diff Artifact

**Branch**: `art-003-final-pr-template-set-slice-2` | **Date**: 2026-08-13 | **Spec**: `specs/art-003-final-pr-template-set-slice-2/spec.md`

**Input**: Feature specification from `specs/art-003-final-pr-template-set-slice-2/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Ship one branded, self-contained HTML artifact at
`speckit-pro/artifact-gallery/templates/annotated-diff.html`, flip its catalog
entry from `planned` to `shipped`, and add the three literals the fill-region
validation needs to bind it. The artifact carries two fill regions, two hunks —
one annotated and one clean — per-hunk objection capture, and both declared
export kinds.

Every design question was settled by three Clarify sessions and is recorded in
`spec.md` as FR-001 through FR-046. This plan re-derives none of it. It does
three things the spec left to this phase:

1. **Adopts a CSS ceiling as an explicit, checkable constraint**, states the
   instrument that checks it — slice 1's, reused rather than rewritten — and
   names four checkpoints where the check runs and can stop the work. The first
   fires after the diff CSS and **before any export work**, which is what makes a
   miss cheap.
2. **Re-declares the reviewability figure** against a bottom-up measurement of
   this port rather than against the scaffold's component estimate, and records
   that the plan-phase estimator is structurally blind here so its `pass` is not
   evidence.
3. **Records the transplant precisely**: which lines of slice 1's routine are
   copied, which lines of `module-map`'s are copied, and which lines of
   `module-map`'s must not be, since that last set is the defect slice 1 proved.

The technical approach is a port for the reading half and a transplant for the
capture half. Upstream `03-code-review-pr.html` supplies the diff structure and
the annotation mechanism; it supplies **no** export behaviour, because it ships
twelve lines of script in a single element and no button at all. Every line of
export and objection capture is copied from two shipped implementations rather
than authored.

## Technical Context

**Language/Version**: HTML5, CSS (custom properties, no preprocessor), and
inline JavaScript in the same conservative dialect the four shipped
export-carrying templates use — `var`, function declarations, no module syntax,
no optional chaining. Repository validation is Python 3.11+ standard library
only.

**Primary Dependencies**: None at runtime, by contract. The artifact embeds two
canonical blocks verbatim and loads nothing else: `BRAND-KIT` from
`speckit-pro/artifact-gallery/brand-kit.css` (318 lines, measured) and
`GALLERY-HEAD` from `speckit-pro/artifact-gallery/theme-toggle.html` (140 lines,
measured). The single permitted external reference is the brand typeface request
that arrives inside `GALLERY-HEAD`.

**Storage**: N/A. The artifact persists nothing of its own. Theme persistence
belongs to the head block and degrades to session-only when a browser refuses
storage for a local file.

**Testing**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5). Layer 4
carries the gallery scanner and the fill-region validation, the two that bind
this artifact. Browser behaviour is not machine-verifiable here — the suite is
Python-stdlib-only — so the local-file render is manual acceptance evidence under
FR-046.

**Target Platform**: Any current browser opening the file directly from a
filesystem, with no server, no install, and the network unavailable.

**Project Type**: A single-file HTML artifact shipped inside a plugin payload,
plus a three-literal change to repository-only validation and a one-value change
to a JSON catalog.

**Performance Goals**: N/A. No measurable performance requirement exists for a
static document of two hunks.

**Constraints**: One file, no sibling asset, no build step. WCAG AA pairings from
the kit's audited set only. Nothing carries meaning by colour alone, which binds
hardest on a unified diff, where added and removed rows are conventionally
colour-only. The heading typeface token is `--rc-font-display` on the first two
heading levels only; `--rc-font-heading` is undefined and an undefined custom
property fails silently. `--rc-border-subtle` appears nowhere in the authored
CSS, and no CSS comment names it. The authored total must land under the 800
block threshold, and the component ceilings below are what decide whether it
does.

**Scale/Scope**: One template. Two fill regions, one of them a list slot. Two
hunks. Two export kinds. Three literals added to shared validation and one
catalog value changed.

**Reviewability Budget**: Primary surface docs/process; declared 750 authored
lines; 1 production file; 13 total files; result warn. Decomposed and measured
below, not scaled from a multiplier.

## Declared File Operations

- NEW speckit-pro/artifact-gallery/templates/annotated-diff.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-fill-regions.py

Those three are the whole change. The parser reads only lines of exactly this
shape — a list marker, `NEW` or `MODIFIED`, one path, nothing after it — so the
four obligations that attach to them are stated here as prose rather than as
entries.

**The catalog value and the file land together.** `SPA-CONTRACT.md` binds status
and file presence in both directions: an artifact file exists if and only if its
entry reads `shipped`. Adding the file without the flip fails as an orphan, and
the flip without the file fails as a missing artifact. Neither may be committed
alone.

**The generated-artifact contract applies.** The gallery ships inside the plugin
payload, so a new template changes shipped bytes on both platforms. Run before
calling the work done:

```text
python3 scripts/refresh-release-artifacts.py
```

That rewrites `dist/claude/**` and `dist/codex/**`, the runner trust metadata,
the installed-cache fixtures, and the payload evidence. Those paths are
generated, are marked `merge=generated` in `.gitattributes`, and are excluded
from the reviewability count by the gate's own generated-path rule — which is why
they are not entries above. CI's `artifact-consistency` job fails the pull
request if the regeneration is skipped.

**`--check` lies on an uncommitted tree.** `refresh-release-artifacts.py --check`
compares against the committed tree, so it exits 1 on a regeneration that is
correct but not yet committed. That exit is not a failure and must not be chased;
it resolves on commit.

**The docs reference regenerates too.** `test-artifact-fill-regions.py` is a
tracked `.py` file under `tests/speckit-pro/`, so its change restales the
generated docs-site test reference. `refresh-release-artifacts.py` does **not**
cover that surface:

```text
pnpm --dir docs-site install --frozen-lockfile   # once per worktree
pnpm --dir docs-site reference:generate
```

**No new contract document.** Slice 1 authored
`specs/art-003-final-pr-template-set/contracts/export-payload-contract.md` and it
is present on this branch, which this branch is cut from. FR-030a binds this
artifact's literals to that document, and this slice's own two authored lead
lines are pinned in `spec.md` at FR-030d. Authoring a second contract would fork
a pinned literal set across two documents, add a second document that dangles at
archive, and spend the tightest headroom in the feature on prose. So this slice
writes no `contracts/` directory, and that is a decision rather than an omission.

## The reviewability decision

### Decision: adopt component ceilings as explicit, checkable constraints

The four constraints below are numeric acceptance criteria, not aspirations.
Each is measured by one instrument, at a named checkpoint, with a stop rule.

| # | Constraint | Ceiling |
|---|---|---|
| C1 | Page chrome plus diff CSS — everything the reading half needs | ≤ 150 |
| C2 | Authored CSS in total, after the objection and export CSS | ≤ 275 |
| C3 | Export and objection-capture JavaScript | ≤ 345 |
| C4 | Authored total | ≤ 750, hard stop below 800 |

C1 is the one that can miss, and it is measured before anything expensive is
built on top of it. C3 is the one slice 1 got wrong, which is why it is a
checkpoint here and was not there; the evidence is below.

### The instrument, reused rather than rewritten

One command, no new file, no new dependency, Python 3.11 standard library. It is
recorded verbatim in slice 1's `quickstart.md` and is reproduced here only so the
ceilings above are stated in the units the instrument reports. Point it at this
slice's artifact:

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
' speckit-pro/artifact-gallery/templates/annotated-diff.html
```

**Re-calibrated against all five shipped templates**, run 2026-08-13 on this
branch:

| Template | authored | css | js | markup |
|---|---|---|---|---|
| `spec-explainer` | 315 | 169 | 0 | 146 |
| `pr-writeup` | 735 | 227 | 334 | 174 |
| `module-map` | 1002 | 448 | 293 | 261 |
| `code-approaches` | 1025 | 471 | 298 | 256 |
| `implementation-plan` | 1221 | 661 | 277 | 283 |

`css + js + markup` equals `authored` exactly on all five, which is the property
that makes a ceiling holdable: an instrument that double-counts its delimiter
lines cannot be held to a number precisely. `pr-writeup`'s row is the basis for
every figure below, because it is this slice's direct predecessor, one commit
old, built to the same contract.

### The re-declared figure, and the arithmetic behind it

**750 authored lines.** That is the sum of the component ceilings, and the number
this slice commits not to exceed. The bottom-up arithmetic beneath it comes to
**738**, so the ceilings carry 12 lines of slack over the measurement and the
declaration carries 50 lines of headroom below the 800 block.

The scaffold and the spec both carried **755**, decomposed 330 JS / 240 CSS /
185 markup. Clarify measured the components more precisely than that
decomposition, and this plan measures them again from the shipped files. Both
later passes move the same direction on markup and the opposite direction on CSS
and JS, so the totals nearly agree while none of the three components does. The
working is below; where it disagrees with the earlier decomposition it says so.

#### CSS — 274, ceiling 275

Slice 1's 227 authored CSS lines were measured by block. Two blocks do not carry:

| Slice 1 block | Lines | Carries |
|---|---|---|
| Page chrome — `body`, `.page`, `header`, `h1`, `h2`, `p`, `.eyebrow`, `.note` | 70 | yes |
| `ul.points`, `ul.points li` | 9 | **no** — this artifact ships no bullet list |
| The before/after comment, `.ba`, `.ba .panel`, `.ba .panel p` | 23 | **no** — no two-panel comparison |
| `details`, `summary`, `details .body`, `details .body p` | 30 | yes — the objection disclosure |
| Objection and export chrome — labels, fields, controls, status, fallback | 94 | yes |
| **Slice 1 total** | **227** | **carry-over 195** |

The earlier decomposition put the carry-over at ~196 and the ceiling at 265.
Measured by block span it is 195: the two dropped blocks are 32 lines together,
each counted with the blank line that separates it from the next.

Diff-specific CSS is new, and is enumerated per rule rather than estimated:

| Rule or block | Lines |
|---|---|
| Comment: why the diff is styled the way it is | 5 |
| `.hunk` — the item frame | 8 |
| `.hunk > h3` — file path and line range, outside the scroll container | 7 |
| `.diff` — the `overflow-x: auto` scroll container | 9 |
| `.diff-row` — the three-cell grid, in document order | 6 |
| `.diff-row .ln` — line number, `user-select: none` | 7 |
| `.diff-row .mk` — the state-marker cell | 5 |
| `.diff-row .code` — `white-space: pre` | 5 |
| `.diff-row.add`, `.diff-row.del` — shade reinforcement | 8 |
| Comment: the annotation, and the severity rule that must not branch | 4 |
| `.ann` — the annotation frame | 8 |
| `.sev` — one rule, all three words, no selector branch | 7 |
| **Total** | **79** |

That is 79 rather than the 64 Clarify measured. The difference is the two comment
blocks, which every other block in slice 1's authored CSS carries and which
FR-032a makes worth writing carefully, and the two shade rules, which Clarify's
list did not enumerate.

**Four things cost zero lines, verified in the kit rather than assumed.** The
brand kit already ships `a` styling, a `:focus-visible` rule whose selector list
includes `[tabindex]:focus-visible`, a `code, pre, kbd, samp` monospace
assignment reading `--rc-font-mono`, and a reduced-motion block. So the jump
links, the focus indicator on each finding, the diff's typeface, and FR-037 are
all inherited. Writing any of them again is lines for nothing.

**The shade rules are the honest edge of this figure.** FR-019 requires the row
state to be carried by a character and says colour *may* reinforce it. The kit
ships no audited add/remove colour pair — its only red is a text token and it has
no green — so reinforcement here is a surface *shade*, not a hue, and it is the
first reduction lever below rather than a requirement.

**CSS total: 195 + 79 = 274. Ceiling 275.**

#### JavaScript — 342, ceiling 345

The routine is a deliberate hybrid, and every line of it already exists in a
shipped file. Base: slice 1's measured 334. Each delta below is a measured
function span in one of the two precedents.

| Change | Lines | Why |
|---|---|---|
| Slice 1's six-name `SLOTS` array and its comment (15) become one slot constant and one list-id constant with a shorter comment (5) | −10 | FR-023c: a list slot has no fixed count, and pinning one breaks the first real fill |
| Slice 1's `mount(slot)` (48) becomes `module-map`'s `mount(anchorId)` (42) | −6 | mounts against an item anchor, placing the control immediately after the item, which is FR-023d |
| Add `module-map`'s `labelOf(anchor)` (12) | +12 | FR-023f: read the label from the item's first heading rather than its whole text |
| Add `module-map`'s `mountAll()` (18), drop slice 1's four-line inline mount loop, add the one-line call | +15 | FR-023c: derive the items from the anchors present in the region at the moment of invocation |
| Slice 1's `recorded()` (18) becomes `module-map`'s (15) | −3 | walks the mounted items rather than a pinned slot list |
| **Total** | **342** | ceiling **345** |

Everything else is slice 1's, copied: `textOf`, `featureLine`, `objectionOf`,
`refresh`, `payload`, `successMessage`, `announce(token, message)`,
`reveal(token, text)`, `copy`, `wire`, the currency-token declaration and its
comment, the export-region reveal and its placement before the mounts, and the
five pinned literals.

**`module-map`'s settle path must not be copied, and this is the whole point of
naming the two sources separately.** Its `announce(message)` (14 lines) and
`reveal(text)` (12) take no token and perform no currency check, and its
`copy(kind)` (26) is four lines shorter than slice 1's for exactly that reason.
Taking `module-map`'s derivation and `module-map`'s settle together would
reproduce the defect FR-027c records in all three pre-slice-1 templates. The four
check sites FR-027b fixes are in slice 1's `announce` and `reveal` and in the
deferred callbacks each of them schedules; those two functions come from slice 1
whole.

**Jump links need no JavaScript at all.** A fragment navigation moves focus when
the target is focusable, so `tabindex="-1"` on each finding is the entire
mechanism for FR-034. Zero lines, and FR-019e forbids scripting it.

#### Markup — 122, ceiling 130

Built bottom-up from slice 1's measured components, keeping only what carries:

| Component | Lines | Basis |
|---|---|---|
| Doctype, `<html>`, `<head>`, `<meta>` | 4 | slice 1, unchanged |
| Attribution header | 8 | slice 1's, same five labels, different upstream filename |
| Slot inventory | 4 | two slot lines plus the two comment delimiters; slice 1 spent 9 on seven slots |
| Style, script, body and html closing plumbing | 8 | measured on slice 1 |
| `</head>`, `<body>`, `.page`, `<main>` and their separators | 7 | measured on slice 1 |
| `header` and the `feature-header` region | 11 | slice 1's shape unchanged, including FR-020e's invented-content sentence |
| FR-019c's standing sentence naming the three markers | 4 | one muted paragraph, outside every fill pair |
| `hunks` section chrome: section, heading, jump links, the grouping element outside the pair, the two FILL markers | 9 | mirrors `module-map`'s `#module-list` shape |
| Hunk 1, annotated: item, heading, scroll container, seven rows, one annotation carrying a severity | 18 | |
| Hunk 2, clean: item, heading, scroll container, six rows, the words that say it is deliberately clean | 13 | FR-020b |
| Export region | 24 | slice 1's, copied, with the noun changed |
| **Subtotal** | **110** | |
| Enumeration margin | 12 | slice 1's own markup enumeration missed eight lines and had to be corrected at Checklist |
| **Total** | **122** | ceiling **130** |

The objection controls cost no markup: FR-021 builds them at load, which is why
FR-043's hidden export region exists.

That is 122 against the earlier decomposition's 185 and Clarify's ~130. Clarify's
component list summed to 108 rather than the 130 it reported; this build reaches
110 by the same route with the head block and the page plumbing counted, and adds
a stated margin rather than an unstated one.

#### The sum

| Component | Measured | Ceiling |
|---|---|---|
| CSS | 274 | 275 |
| JavaScript | 342 | 345 |
| Markup | 122 | 130 |
| **Authored total** | **738** | **750** |

Excluded from every figure above: the 458 canonical lines a reviewer never reads
because they are byte-verified copies — `BRAND-KIT` 318 and `GALLERY-HEAD` 140,
both measured on this branch.

**Result: warn.** Above the 400 warn threshold, below the 800 block threshold. No
`Reviewability-Exception` pragma is claimed and none is available: the accepted
classes are `refactor`, `infra`, and `upgrade`, and none honestly describes
net-new template work.

**Split decision: none available, and none needed.** This spec is already the
split. ART-003 ships as three stacked slices, one template per pull request, and
this is slice 2. A self-contained HTML artifact cannot be divided across two pull
requests and still render from a filesystem, so one template per pull request is
the thinnest vertical slice this work admits. `flowchart` is slice 3, cut from
this branch after this pull request is open. Nothing here is shaped to suit it.

### The checkpoints, and the stop rule

Four measurement tasks enter `tasks.md`, ordered so each ceiling is tested before
the work that would compound on top of it. Each is a task with a numeric
acceptance criterion and a recorded result.

| Checkpoint | Runs after | Gate | On failure |
|---|---|---|---|
| **M1** | the page chrome and the diff CSS are written, **before any objection or export CSS** | `css ≤ 150` | **Stop.** Do not proceed. Apply the levers below and re-measure. |
| **M2** | the objection and export CSS is written | `css ≤ 275` | Stop. Reduce, re-measure. |
| **M3** | the export routine is written, before the sample markup | `js ≤ 345` | Stop. Reduce, re-measure. |
| **M4** | all markup is written, before the pull request | `authored ≤ 750` | Stop. Reduce, re-measure. Escalate above 800. |

**M1 is the checkpoint that matters**, and it is the one the workflow file asked
for by name. It is the earliest moment the ceiling can fail and the cheapest
moment to fix it: a failure surfaces with roughly 150 lines written rather than
750, and none of the copied export work has been paid for yet.

**M3 exists because slice 1 did not have it.** Slice 1 declared its JavaScript at
288 on the reasoning that the component was "measured against three shipped
implementations of the same routine and is a floor rather than an estimate", and
then shipped 334 — a 46-line, 16% overrun, and the largest single estimation
error in the slice. It was absorbed only because CSS and markup came in 69 lines
under together. The same reasoning is available for this slice's 342 and is not
being relied on again.

**Review instruction.** The pull-request body records all four numbers and the
checkpoint each was taken at, so a reviewer reads a measurement rather than a
claim. This is a PR Review Packet obligation the spec already carries under
"scope budget", now given a concrete payload.

### The reduction levers, in order

Named now so a failure at M1 has a plan rather than a negotiation:

1. **Drop the two shade rules** (−8 CSS). FR-019 requires the state to be carried
   by a character in a fixed position; colour is explicitly permitted to
   reinforce and explicitly forbidden to carry. The kit ships no audited
   add/remove pair, so this is the cheapest cut and the one that weakens nothing
   the spec requires.
2. **One rule set for both hunk states.** No `.hunk.clean` selector. FR-020b
   already requires the clean hunk to say so in words, so a selector would be a
   second carrier for something already carried.
3. **Fewer sample rows.** Seven and six are generous; five and four still
   demonstrate all three markers and both states (−4 markup).
4. **One rule set for the disclosure.** The objection control is the only
   `<details>` in this artifact, unlike slice 1 where `file-by-file`'s items were
   disclosures too. Writing a second set is the single largest avoidable cost in
   C2.
5. **Inherit rather than restate.** The kit assigns every heading level its own
   typeface, styles links, ships the focus-visible rule that already covers
   `[tabindex]`, assigns the monospace token to `code` and `pre`, and suppresses
   motion. Naming any of them again is lines for nothing and a chance to name a
   custom property the block does not define, which fails silently.
6. **No hover-only refinement.** A hover state carries no meaning under FR-033,
   so it is decoration paid for in lines.

If all six are applied and M1 still exceeds 150, the ceiling has failed on
evidence rather than on discipline. That is the point at which the question goes
to the operator, backed by a measurement of this port.

### Why the check is not a committed test

Considered and rejected, for the same three reasons slice 1 recorded, one of
which has since been strengthened:

- **It would consume the budget it protects.** A test file plus its manifest row
  is authored lines on the slice whose size is the problem.
- **The ceiling is class-specific.** 150 is a *reading-half* constraint for a
  document-or-diff template. `flowchart` renders inline SVG and is legitimately
  diagram-class; a committed threshold would either fail slice 3 or be widened
  until it constrained nothing.
- **It would contradict FR-042a**, which fixes this slice's change to shared
  validation at exactly three literals.

The instrument is therefore a recorded command run at recorded checkpoints:
checkable without being permanent.

### The plan-phase estimator is blind here, and its result is not evidence

Autopilot runs `estimate-reviewable-loc` after G3. **Its output must not be read
as reassurance about this slice.** Both causes were re-verified for this slice
against the helper source in this repository, at
`speckit-pro/speckit_pro_runner/helpers/read_only.py`:

1. **It counts files and opens none.** The projection is literally
   `projected = production * 40`. A 40-line artifact and a 1200-line artifact
   project identically.
2. **It classifies none of this slice's paths as production.**
   `is_production_file` returns true only for a path beginning `src/`, `app/`,
   `lib/`, or `scripts/`, or ending `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`,
   or `.sql`. All three declared entries fail both tests — the `.html` artifact,
   the `.json` catalog, and the `.py` validation module, because `.py` is not in
   that suffix list.

So `production = 0` and `projected = 0`, and the status reads `pass`. Because two
of the three entries are `MODIFIED` and neither is a generated path, `greenfield`
resolves **false**, so the reported thresholds read `warn: 400, block: 800`
rather than the greenfield pair. Record the helper's result as a known-blind
diagnostic with that reason beside it. The authoritative figure is the
decomposition above, measured with the instrument above.

### The declaration parser, verified rather than read

The gate's setup mode reads its numbers with `last_number`, which takes the
**last** regular-expression match in the whole file and the first digits within
**forty non-digit characters** of the phrase. Its surface reader is a `findall`
that unions **every** `Primary surface:` match in the file, so a second such line
with a different value raises the surface count and produces a warning that looks
like a scope problem and is a formatting one.

That trap fired three times on slice 1 — on a spec identifier, on a filename, and
on a table header. Two rules follow, and this plan obeys both:

- The Declared Figures block is last in this file, and nothing numeric follows
  the phrase after it.
- `Primary surface` is written exactly once, with exactly one value.

The regexes are run against this finished file as a Plan-phase check rather than
inspected by eye; the command is in `quickstart.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.2.0. Evaluated pre-design and re-evaluated after Phase 1
design; both passes are recorded here and neither changed a verdict.

| Principle | Applies how | Verdict | Evidence |
|---|---|---|---|
| **I. Plugin Structure Compliance** | The gallery ships inside the plugin payload. The new template must live at the path derived from its catalog identifier, and repository-only tests stay under `tests/speckit-pro/`. | **PASS** | The artifact lands at `templates/annotated-diff.html`, the stem its entry already declares. The validation change edits an existing module under `tests/speckit-pro/unit/`; no test file is added, none moves, and no filename is coupled to a spec ID. Gate: `python3 tests/speckit-pro/run-all.py --layer 1`. |
| **II. Cross-Platform Runtime & Script Safety** | Repository tooling stays on Python 3.11+ standard library with no Bash or `jq` dependency. | **PASS** | The only repository-tooling change is three literals in an existing stdlib-only Python module. The measurement instrument is an ad-hoc `python3 -c` invocation, committed nowhere, adding no dependency and no file. Gate: `python3 tests/speckit-pro/run-all.py --layer 4`. |
| **III. Semantic Versioning** | No version field is hand-edited. | **PASS (not engaged)** | Release-please owns version bumps. This slice edits no `plugin.json` and no marketplace version. |
| **IV. Test Coverage Before Merge** | The shipped template must be bound by Layer 4 rather than passing vacuously. | **PASS** | The floor row `FLOOR["annotated-diff"]` is what brings this template into the per-template universe; without it the region checks skip it entirely. The list-slot row binds `hunks`'s item anchors. SC-010 states the non-vacuity requirement directly, and `quickstart.md` carries the command that proves it. Gate: `python3 tests/speckit-pro/run-all.py`. |
| **V. Conventional Commits** | The pull-request title is the squash-merge commit message. | **PASS (deferred to PR time)** | Title validated through the live release-readiness gate before creation, in the form `<type>(<lowercase-scope>): <plain English description>`. |
| **VI. KISS, Simplicity & YAGNI** | The artifact carries no affordance its catalog entry does not declare, and the port adds no abstraction. | **PASS** | Both declared export kinds ship and nothing else; the entry declares `["prompt","markdown"]`. Two hunks, which is the demonstrating minimum and the cap together (FR-020a). No third region: `diff-summary` was proposed and rejected on evidence. No runtime disambiguation for a slug collision, because the derivation cannot produce one. No JavaScript for jump links, because the platform supplies the behaviour. |

**Required plan definitions, per the preset:**

- **Primary and secondary surfaces.** Stated in the Declared Figures block below
  and in Technical Context. One primary surface; two secondary.
- **Budget position.** `warn` — above 400 authored lines, below 800; one
  production file against a warn threshold of six and a block of eight; thirteen
  files in all against a warn threshold of fifteen and a block of twenty-five;
  one primary surface. Recorded above with its decomposition. The thresholds are
  spelled in words here deliberately: written as digits beside their phrase they
  become a second parser match, and the gate reads digits.
- **Split decision.** Recorded above: this spec is the split, slice 3 is the named
  follow-up, and no further split is available.
- **PR review packet source.** `spec.md` carries the requirement; this plan
  supplies the material. What changed and why come from the Summary; non-goals
  from `spec.md` *Out of Scope*; review order from the rule below; scope budget
  from the four measured numbers and the checkpoint each was taken at;
  traceability from the requirement-to-file map in `data-model.md`; verification
  from `quickstart.md` and the suite; known gaps are the nine `spec.md` carries
  forward plus the one it adds plus the two recorded in Complexity Tracking below;
  rollback is the catalog value returning to `planned` together with the file's
  removal, since the contract binds them in both directions.

**Review order.** The authored markup and the diff CSS first — that is where
every decision a reviewer can disagree with lives — then the export routine, then
the validation and catalog changes. The 458 canonical lines are read last or not
at all: they are byte-verified copies, and validation names the artifact and the
block on a single character of drift.

## Project Structure

### Documentation (this feature)

```text
specs/art-003-final-pr-template-set-slice-2/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── checklists/          # Phase 4 output (/speckit-checklist)
├── SPEC-MOC.md          # Roadmap backlink
├── spec.md              # Phase 1 input
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` directory. The reason is recorded under Declared File Operations:
the export payload contract this artifact must match already exists at
`specs/art-003-final-pr-template-set/contracts/export-payload-contract.md`, it is
present on this branch, and forking it would fork a pinned literal set.

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
        ├── spec-explainer.html
        ├── module-map.html               # The item-derivation precedent
        ├── code-approaches.html
        ├── implementation-plan.html
        ├── pr-writeup.html               # Slice 1 — the shell and the currency guard
        └── annotated-diff.html           # NEW — this slice

tests/speckit-pro/
└── unit/
    ├── test-artifact-gallery.py          # Gallery scanner — unchanged
    └── test-artifact-fill-regions.py     # FLOOR, LIST_SLOTS, SOURCE_ARTIFACTS

scripts/refresh-release-artifacts.py      # Payload regeneration
dist/claude/**, dist/codex/**             # Generated payload — never hand-edited
```

**Structure Decision**: No new directory and no new module. The artifact lands
beside the five shipped templates under
`speckit-pro/artifact-gallery/templates/`, at the path the catalog derives from
the entry's identifier rather than one this plan chooses. The validation change
is three literals inside an existing module, so no test file is created and none
is renamed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No principle violation is claimed. Every gate above reads PASS. Three decisions
depart from a shipped precedent, and each is recorded here because a reviewer
will otherwise read the departure as the defect rather than the fix.

| Departure | Why needed | Simpler alternative rejected because |
|-----------|------------|--------------------------------------|
| The export routine takes its item derivation from `module-map` and its settle path from `pr-writeup`, rather than copying either file whole. | The two requirements pull apart. FR-023c needs items derived from the anchors present at invocation, which only `module-map` does. FR-027 needs the four-site currency guard, which only `pr-writeup` has. Neither file satisfies both. | Copying `module-map` whole reproduces the defect FR-027c records in all three pre-slice-1 templates. Copying `pr-writeup` whole pins a fixed slot list, which breaks on the first real fill of a list slot. |
| Each hunk's scroll container carries `tabindex="0"`, which **no** shipped `overflow-x: auto` container in this gallery does. | Safari does not make a scroll container keyboard-scrollable without it and Chrome's automatic behaviour is conditional, so without it a keyboard reader cannot reach the right-hand side of a wide hunk. FR-019d requires it. | Matching the five shipped containers matches five instances of the same defect. Repairing those five is out of scope and is recorded as a known gap; this artifact is the first to do it correctly. |
| The closed source-artifact set gains `git-diff`, the first member that is not a filename. | FR-017 admits no exception, so some closed-set value is mandatory, and none of the six existing members can honestly claim a hunk's rows: the planning artifacts are written before the code and `implementation-notes.md` is a deviation record. | `diff.patch` names a file no phase of this repository writes, which is a dishonest provenance claim rather than a shape improvement. The shape objection is real and is recorded in the Clarify consensus record: `git-diff` fullmatches the slot-name grammar while no existing member does. It lands on readability, not correctness — slot names and source values are checked by different code paths. |

## Declared Figures (read by the setup reviewability gate)

The gate takes the **last** match of each phrase below in this file, so this
block is last on purpose. Append nothing after it.

- **Primary surface**: docs/process
- **Secondary surfaces**: seed/config (one catalog value), harness/adapter (three literals in the fill-region validation)
- **Projected production files**: 1
- **Projected total files**: 13
- **Projected reviewable LOC**: 750

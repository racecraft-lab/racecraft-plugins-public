# Phase 0 Research: PR Write-up Artifact

Everything a reader needs to judge whether the plan's numbers are real. Three
Clarify sessions settled the design surface and `spec.md` FR-011a through FR-039a
is the binding record; nothing here re-derives any of it. What is recorded here
is the **evidence** behind the plan's constraints, and the two findings this
phase produced that were not available when the spec was written.

---

## Decision 1 — The measurement instrument

**Decision**: Measure authored lines with a single `python3` invocation that
excises the two canonical spans and partitions the remainder into CSS,
JavaScript, and markup. The command is recorded verbatim in `plan.md` and is
committed nowhere.

**Rationale**: The ceiling the plan adopts is only checkable if one instrument
defines it. Two properties decided this one.

It reproduces the spec's recorded figures within two lines on every shipped
template, so ceilings stated in its units trace to the evidence the spec already
cites:

| Template | authored (measured / recorded) | css (measured / recorded) | js (measured / recorded) |
|---|---|---|---|
| `spec-explainer` | 315 / 316 | 169 / 171 | 0 / 0 |
| `module-map` | 1002 / 1003 | 448 / 450 | 293 / 294 |
| `code-approaches` | 1025 / 1026 | 471 / 473 | 298 / 299 |
| `implementation-plan` | 1221 / 1222 | 661 / 663 | 277 / 278 |

The offset is constant and explained: the recorded pass counted the `<style>` and
`</style>` delimiter lines into CSS, and this one counts them as markup.

It is internally consistent, which the recorded pass is not. Here
`css + js + markup == authored` on all four templates. The recorded decomposition
sums to 318 against a recorded total of 316 on `spec-explainer`, because those two
delimiter lines are counted twice. A ceiling policed by a double-counting
instrument cannot be held precisely.

The canonical span is 458 lines on every template — `BRAND-KIT` 318 plus
`GALLERY-HEAD` 140 — confirmed identical across all four, which is what makes
"authored" a comparable quantity between them.

**Alternatives considered**:

- *A committed test asserting the ceiling.* Rejected on three independent
  grounds, recorded in `plan.md`: it consumes the budget it protects, it is wrong
  for slices 2 and 3 because the ceiling is a document-class constraint and both
  remaining templates are diagram-class, and it would add a fourth literal to a
  shared-validation change FR-039a fixes at three.
- *`wc -l` on the whole file minus 458.* Rejected: it yields the total but no
  decomposition, so it cannot tell a CSS overrun from a markup overrun and cannot
  support the M1 checkpoint, which is the one that matters.
- *Trusting the plan-phase estimator.* Rejected on the evidence in Decision 6.

---

## Decision 2 — `spec-explainer` is the comparator, not `module-map`

**Decision**: Set the document-section CSS ceiling against `spec-explainer`'s
measured 169, not against the 448–661 the export-carrying templates spent.

**Rationale**: The spread between shipped templates is subject matter, not
discipline. `module-map` draws a node graph, `implementation-plan` draws mockups,
phase timelines and a risk register, and `code-approaches` draws comparison
tables. Each needs bespoke layout CSS that has no counterpart here.
`pr-writeup` is a document of six titled prose-and-list sections, which is
structurally what `spec-explainer` is (`tldr`, `goals`, `non-goals`,
`acceptance-criteria`, `clarification-faq`).

Read directly, `spec-explainer`'s CSS is one `body` rule, one `.page` rule, one
`h1`, one `h2`, one `p`, an `.eyebrow`, a `.notice`, a `.tldr` panel, a
`ul.points` group, a `details`/`summary` set, and a `dl.faq` set. **One `h2` rule
serves all six sections.** That is the whole mechanism behind the number, and it
is the first reduction lever the plan names.

The margin is deliberate: 169 measured down to a 150 ceiling, against a port that
additionally carries a two-panel `before-after` comparison `spec-explainer` has
none of. The lever that pays for it is sharing one `details` rule set between
`file-by-file`'s items and the six question disclosures, since FR-020 already
forces `file-by-file`'s items to be elements with a mandatory end tag.

**Alternatives considered**:

- *Average the four shipped templates.* This is the error the Phase 0 correction
  already caught at the multiplier level, and it recurs here. The per-template
  spread is too wide for a mean to carry predictive weight, and pooling a document
  with three diagram templates pools populations that do not belong together.
- *Set the ceiling at `module-map`'s 448 and accept the block.* Rejected: it
  concedes the slice on an assumption rather than on a measurement of this port,
  and no exception class fits net-new template work.

---

## Decision 3 — The export floor is real, and 288 is a floor not an estimate

**Decision**: Budget 288 lines for export and question capture, and treat it as
irreducible.

**Rationale**: `spec-explainer` carries **zero** authored JavaScript — its only
script is the theme toggle inside the canonical head block. The three templates
carrying both export kinds spend 293, 298, and 277. The floor is a property of
the routine, not of the author.

Upstream `17-pr-writeup.html` supplies none of it: 596 lines, of which 346 are CSS
the brand kit replaces, and **zero `<script>` and zero `<button>` tags** — six
`<details>` disclosures and nothing else. Every line of export behaviour is
authored fresh with no upstream counterpart to port.

The 288 figure is the precedent's 293, less 19, plus 13, plus rounding:

- **−19** for FR-023c. Collection walks a pinned list of slot names in document
  order and resolves each section by its `sec-<slot>` id, instead of walking a
  container's children and reading their ids. The precedent's `mountAll()` reads
  a container, iterates `children`, collects ids, then resolves each — a loop and
  a guard this slice does not need, because the slot list is known at authoring
  time. It also survives a fill that restructures a section and concatenates
  nothing into a selector.
- **+13** for FR-026a, the stale-settle guard. See Decision 4.

**Alternatives considered**:

- *Drop one export kind.* Not available. The catalog entry shipped in ART-001
  declares `["prompt","markdown"]`, and changing it would be a second catalog
  value and therefore a contract amendment rather than a port.
- *Share one routine across templates.* There is no shared runtime; each
  template is a single self-contained file by contract. This is precisely why the
  export-payload contract exists as a document.

---

## Decision 4 — The stale-settle guard, and the defect it declines to reproduce

**Decision**: Carry a currency token per invocation, compared when a copy settles.
Both settle paths are guarded. The synchronous refusal path and the
no-clipboard-interface path stay unguarded and say why.

**Rationale**: Verified directly in the shipped source. The precedent's `copy()`
calls `clipboard.writeText(text).then(onSuccess, onFailure)` with no currency
check anywhere in the routine, and all three export-carrying templates run the
same shape. Two exports invoked before the first settles therefore produce two
wrong outcomes:

- A rejected first copy announces a failure that did not happen, after the second
  kind copied successfully.
- The first kind's payload lands in the fallback field while the status text
  describes the second.

Both settle paths need the guard, not only the rejection path. A slow success
resolving after a fast failure is the mirror case: it would overwrite the failure
message with "Copied" while the fallback field still holds the other kind's text.

The two unguarded paths are safe by construction, and the artifact must say so
rather than leave it to inference: both run inside the same synchronous turn that
issued the token, so neither can be stale.

**Alternatives considered**:

- *Disable the controls while a copy is in flight.* Rejected: it adds a visible
  state, its own CSS, and a re-enable path on every exit including the throwing
  one, which is more lines and more failure modes than a compared token.
- *Reproduce the precedent and record the defect as a known gap.* Rejected by
  FR-026a, which states the requirement directly. Three copies of a defect is not
  a precedent worth matching.

---

## Decision 5 — The port mapping and the drop list

Fixed by FR-011b through FR-011e. Recorded here as the size evidence, because the
drops are the single largest line lever in the slice.

**Kept and mapped**:

| Upstream | Becomes | Note |
|---|---|---|
| `#why` heading and lede | `motivation` | |
| the before/after panel nested inside `#why` | `before-after` | Promoted to its own titled section. |
| `#tour` | `file-by-file` | The only list slot. |
| `#tests` | `verification` | |
| page header eyebrow and title | `feature-header` | Carries `id="feature-id"` and `id="feature-name"`. |
| `#focus` third item, "What I deliberately did not do" | `non-goals` | Restructured as its own titled section. |
| — | `implementation-notes` | Authored fresh; no upstream counterpart. |

**Dropped**, each mapping to no fill region, together worth about 141 authored
lines: the file-count strip, the prompt echo, the TL;DR block, the first two
"where to focus" items, the whole rollout section, and the table-of-contents
sidebar together with the two-column layout it requires.

That 141 is the difference between roughly 750 and roughly 890, and therefore the
difference between warn and block. The sidebar is the largest single item,
because dropping it also drops the layout it forces.

**Two restyles are forced rather than optional**:

- Upstream's multi-class syntax highlighting introduces colours outside the
  audited set and carries meaning by hue alone. The port uses the single
  muted-comment span the shipped templates use.
- A verification item's passed-or-pending state must read as a **word**, not as a
  check glyph's fill, under FR-032.

**Prohibited constructs are dropped, never ported**: a `base` element, a
scheme-relative reference, an `on*` handler attribute, a `srcdoc` attribute, a
`form` with a submission target, and a `ping` attribute. Validation fails an
artifact carrying any of them and names it.

**Upstream sourcing protocol**: fetch `17-pr-writeup.html` read-only at implement
time from `anthropics/html-effectiveness` (`main`), keep it outside the repository
tree in the session scratchpad, and never stage upstream bytes. Only the branded
derivative is committed. This is ART-002's recorded protocol and it is why
per-slot granularity could not be settled before the implement-time fetch.

---

## Decision 6 — The plan-phase estimator is structurally blind here

**Finding, verified rather than assumed.** Both causes were read directly from
the helper source in the installed plugin cache, version 2.23.0.

1. The projection is `projected = production * 40`. No file is opened and no line
   is counted.
2. `is_production_file` returns true only for a path beginning `src/`, `app/`,
   `lib/`, or `scripts/`, or ending `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`,
   or `.sql`. Each declared path fails both tests:

   ```text
   speckit-pro/artifact-gallery/templates/pr-writeup.html          production=False
   speckit-pro/artifact-gallery/manifest.json                      production=False
   tests/speckit-pro/unit/test-artifact-fill-regions.py            production=False
   specs/art-003-final-pr-template-set/contracts/…-contract.md     production=False
   ```

   The `.py` module is worth naming explicitly: `.py` is **not** in that suffix
   list, so a Python change is invisible to this estimator on every spec.

So `production = 0`, `projected = 0`, and the status reads `pass`.

**One correction to the note carried in the workflow file.** It predicts a
`greenfield` run. Because two declared entries are `MODIFIED` and neither is a
generated path (`is_excluded_generated` covers lockfiles, `.process/`, and paths
under `vendor/`, `generated/`, `dist/`, `build/`), `greenfield` resolves **false**
and the reported thresholds read `warn: 400, block: 800`. The `pass` and the `0`
are unaffected, so the hazard is identical.

**This is not a reason to stop.** Step 7b is advisory by contract and never
blocks, and ART-012 recorded the identical `pass`/`0` result. The hazard is that a
green line in a log reads as reassurance. It is not. It is the same shape of false
comfort that let ART-002 reach pull-request creation believing it was at 530: a
declaration-checking gate reporting `pass` on a number nobody measured.

Record it as a known-blind diagnostic with this reason beside it, and cite the
decomposition instead.

---

## Decision 7 — The export-payload contract is recovered, not reinvented

**Decision**: Author this slice's `contracts/export-payload-contract.md` from the
recovered ART-002 document rather than from scratch, carrying forward every
literal it pins and recording one named divergence.

**Rationale**: FR-029a requires this slice to author the contract because the
document all three shipped templates name in a source comment was deleted when
ART-002 was archived, so every shipped template now carries a pinning reference
that resolves nowhere. Writing a fresh document would risk re-inventing wording
that three shipped templates already emit byte-for-byte — and the clipboard-failure
message in particular must stay byte-identical, verified identical across all
three.

The recovered document is 209 lines and is the final shipped version. Every
literal it pins was re-verified as still satisfied by the three shipped
templates, with no drift, and `spec-explainer` still carries no reader-input
field of any kind.

**The one genuine divergence, recorded rather than silently restated.** The
recovered contract says each capture control is "mounted onto its item's anchor
and inserted immediately after it, so tab order and reading order follow the
visible order". FR-023b requires the opposite placement: appended to the **end**
of its section.

Both are right for their own case, and the difference is that the anchor's role
changed. In the three shipped templates the anchor is a **list item**, so
"immediately after it" places the control after the content being questioned. In
`pr-writeup` questions attach per **section** and the anchor is the section
**heading**, so "immediately after it" would place the control between the heading
and content the reader has not read yet — breaking the very reading-order
rationale the contract gives for the rule.

FR-023b therefore honours the contract's stated rationale while departing from its
letter. The divergence is written into this slice's contract explicitly, with its
justification, so a reviewer does not read it as a violation.

**Considered and inapplicable.** The recovered contract closes with a warning
that upstream `04-code-understanding.html` runs an accordion script force-closing
every sibling disclosure, which must not reach the capture controls. That warning
**cannot reach this slice**: upstream `17-pr-writeup.html` ships zero `<script>`
tags, so there is no accordion behaviour to port and nothing to scope or drop.
Recorded as considered rather than omitted, so a later reader does not think it
was missed.

**Honest consequence, already recorded as a known gap.** This slice's own
contract will dangle the same way when ART-003 is archived. Nothing compares the
copies of the failure message across templates, and this slice does not add that
comparison, because FR-039a fixes its shared-validation change at three literals.

---

## Decision 8 — Three literals, and no fourth

**Decision**: The whole change to shared validation is the floor row, the
list-slot row, and the source-set member.

**Rationale**: Each is required by a numbered requirement, and each closes a gap
for this template alone.

- `FLOOR["pr-writeup"]` names the roadmap's four (`motivation`, `before-after`,
  `file-by-file`, `implementation-notes`). This is what brings the template into
  the per-template universe at all — the module resolves that universe by
  intersecting the catalog with its floor, so a shipped template the floor does
  not name is never parsed and would pass every check green with no regions and
  no inventory. The floor stays sourced from the roadmap alone, so the literal
  keeps tracing to one document, and R1 is a floor rather than an equality: it
  explicitly accepts a template carrying more slots than the floor names.
- `LIST_SLOTS["pr-writeup"]` names `file-by-file` and nothing else.
- `SOURCE_ARTIFACTS` gains `implementation-notes.md`, as a bare filename like
  every existing member.

**Alternatives considered and rejected**:

- *A general guard binding any `shipped` entry to the fill-region checks.* The
  module's own docstring records the floor-scoped universe as a **deliberate**
  decision, on the ground that binding a later template would hold it to a
  contract its own design never read. Widening it here would contradict a recorded
  decision inside the file being edited. Recorded as a known gap instead.
- *An artifact-side gate reading a catalog entry's `exports` against the
  artifact body.* Closing it means binding all four already-shipped templates,
  which is a change to shared validation rather than a port. Recorded as a known
  gap.
- *A cross-template agreement test on the shared failure message.* Rejected in
  Clarify session 2: FR-039a fixes this slice's shared-validation change at three
  literals, so adding a fourth would contradict a requirement in the same spec.
- *Naming an existing member for the notes source.* Rejected in Clarify session
  1: every candidate points an authoring agent at a file containing no notes,
  which breaks the one interface this slice owes ART-010.

---

## Known gaps carried into the pull request

Five from Clarify, plus two this phase adds.

1. The payload documents no fill-region grammar; the marker syntax appears
   nowhere in `SPA-CONTRACT.md`.
2. The validation binds only the templates its floor names, so a shipped
   non-floor template is never parsed.
3. No check reads a catalog entry's `exports` against the artifact.
4. Nothing compares the clipboard-failure message shared across what will be four
   templates, and the document the three shipped templates name as pinning it was
   deleted when ART-002 was archived — a condition this slice's own contract will
   reach when ART-003 is archived.
5. Pasted into a pull-request comment, the export's two header lines render as one
   paragraph. Cosmetic for the automated reader and visible only to a human.
6. **New.** The plan-phase estimator reports `pass` with `projected: 0` on this
   slice and on every slice whose production surface is `.html`, `.json`, `.md`,
   or `.py`. It is advisory by contract, but its green line reads as reassurance.
7. **New.** The reviewability declaration parser reads the **last** match of its
   phrases in the target file. `plan.md` therefore ends with a Declared Figures
   block and nothing may be appended after it, or the declared figure silently
   changes to whatever number a later paragraph happens to put near the phrase.

# Phase 0 Research: Artifact Brand Kit & Gallery Foundation

**Feature**: ART-001 | **Date**: 2026-07-28

Every open question the design concept deferred to plan time is resolved here.
All questions are resolved; no clarification marker remains. Paths are
repository-relative.

---

## R1 — Upstream identity, license, and the exact 20 filenames

**Decision**: Upstream is `anthropics/html-effectiveness`, licensed **MIT**,
`Copyright (c) 2026 Anthropic PBC`. The 20 ported entries carry the upstream
filename verbatim in `source.file`, numeric prefix intact.

**Rationale**: FR-020 needs a real copyright line, a license identifier, and a
link to the full license text; `source.file` needs exact filenames. Both were
retrieved from the upstream repository rather than inferred:

- License: SPDX `MIT`, canonical text at
  `https://github.com/anthropics/html-effectiveness/blob/main/LICENSE`
- Root listing yields exactly 20 numbered templates, `01-…` through `20-…`

The roadmap referred to templates only by number ("upstream 16", "upstream 03").
Those numbers now resolve to concrete filenames — see the crosswalk in
`data-model.md`. Two are non-obvious and would have been guessed wrong:
roadmap "upstream 04 (module map)" is `04-code-understanding.html`, and roadmap
"upstream 14 (feature/spec explainer)" is
`14-research-feature-explainer.html`.

**Alternatives considered**: Hand-writing the copyright line from memory —
rejected, FR-020 requires it reproduced *verbatim* and a wrong year or entity
makes the attribution legally useless. The notice file is captured by direct
download during implementation, not retyped.

## R2 — Category enum derivation

**Decision**: The nine members are the upstream gallery index's own section
headings, kebab-cased. All 20 ported entries inherit their upstream group with
zero reassignment.

**Rationale**: FR-007 fixes the nine member names; Session 2 fixes their origin
as "the upstream gallery's own index taxonomy". Fetching the upstream
`index.html` confirmed the taxonomy exists and matches the enum one-for-one:

| Upstream heading | Enum member |
|---|---|
| Exploration & Planning | `exploration-planning` |
| Code Review & Understanding | `code-review` |
| Design | `design` |
| Prototyping | `prototyping` |
| Illustrations & Diagrams | `diagrams` |
| Decks | `decks` |
| Research & Learning | `research` |
| Reports | `reports` |
| Custom Editing Interfaces | `editors` |

This makes every ported entry's `category` a *derived* value rather than a
judgment call, which is the property that keeps ART-002…005 mechanical.

**Alternatives considered**: The product plan's four-way port-spec grouping —
rejected in Session 2 because it is ownership, not a browsing taxonomy, and
would make `category` derivable from `stage`.

**Observation, non-blocking**: Session 2's rationale says "four members straddle
two stages each". With `uat-walkthrough` assigned to `editors` in the *following*
clarification, the true count is **five** (`exploration-planning`, `code-review`,
`diagrams`, `research`, `editors`). The load-bearing claim — that no
stage-to-category function exists in either direction — holds more strongly at
five, so this is stale rationale prose, not a requirement defect. Flagged here so
Analyze does not re-open it.

## R3 — Signal vocabulary closure verifies against the seeded catalog

**Decision**: The five FR-015 signals close exactly against the 21 seeded
entries. No sixth signal, no unused member.

**Rationale**: Built the full stage/trigger assignment (see `data-model.md`) and
checked both directions:

- Every trigger names only vocabulary members.
- Every member is consumed: `competing_approaches`→`code-approaches`,
  `brownfield_change`→`module-map`,
  `self_review_findings`+`large_diff`→`annotated-diff`,
  `operational_flow_change`→`flowchart`.

The counts land exactly on Session 1's arithmetic — 4 staged always-applies + 4
staged conditional + 13 ad-hoc = 21 — and on FR-007's upstream split of 4/3/6/7
plus 1 repository-authored.

**Alternatives considered**: Adding `ui_change` / `schema_change` / `api_change`
— rejected by the spec's consumer test: observable, but no seeded entry consumes
them, so they are not members.

## R4 — Validation asserts count plus closure, never a duplicate list

**Decision**: The test hard-codes the integer `5` and the closure rules. It does
**not** hold a copy of the five names.

**Rationale**: FR-017 is explicit — a list copied into the test and edited in the
same commit as the manifest is not an independent check. Hard-coding the count
gives a real oracle derived from the specification: inventing a signal raises the
count and fails; disguising it by deleting a real one orphans the entries still
naming the deleted signal and fails the "every entry's signal is in `signals`"
direction. Both failure modes are caught without taxing legitimate vocabulary
changes with a second edit site.

**Alternatives considered**: Set-equality against a literal list in the test —
rejected by FR-017. A separate JSON Schema document — rejected; the standard
library ships no validator, and the repository's one existing schema pointer is
already dangling.

## R5 — Marker-block drift check

**Decision**: `brand-kit.css` carries `/* BRAND-KIT:START */` … `/* BRAND-KIT:END */`;
`theme-toggle.html` carries `<!-- GALLERY-HEAD:START -->` … `<!-- GALLERY-HEAD:END -->`.
The test extracts the region between the markers from every gallery HTML file and
compares it byte-for-byte against the canonical file's own region.

**Rationale**: Design concept Q4/Q8. Comparing only the delimited region is what
lets a template add its own styling outside the block without failing (FR-006,
Story 1 scenario 4). Comparing the canonical file's *inner* region (not the whole
file) is what lets the provenance header and the audited contrast table live in
`brand-kit.css` above the start marker without every artifact having to embed
them.

**Edge cases the test must fail on**, taken from the spec's Edge Cases:

- A start marker with no matching end marker
- More than one occurrence of the same marker pair in one file
- A `shipped` entry whose artifact omits a block entirely (fail, not pass-by-absence)

**Alternatives considered**: A sync script — rejected in Q4 as new repository
tooling the constitution would require justifying; the byte-compare is what makes
hand-copying safe. Whole-file comparison — rejected, it forbids per-template
styling.

## R6 — External-reference scanner: resource-load positions only

**Decision**: Flag external hosts only in resource-loading positions —
`script`/`img`/`iframe` `src`, `srcset`, `link href` for stylesheet and
preconnect relations, CSS `url()` and `@import`, and `fetch`/`XMLHttpRequest`/
`WebSocket` string literals. Allowlist `fonts.googleapis.com` and
`fonts.gstatic.com`. Navigation `<a href>` and URLs in comments or visible text
pass.

**Rationale**: FR-011 and design concept Q3. A naive "any URL substring" scan
would reject the very provenance and attribution links FR-012 and FR-020
*require*, guaranteeing a self-contradicting rule set. Parsing uses
`html.parser` from the standard library for element positions plus targeted
regular expressions for the CSS and network-call positions, which have no
standard-library parser.

**Alternatives considered**: Banning external navigation too — rejected, it
kills the attribution links the manifest design already committed to.

## R7 — Dark mode, first paint, and `file://` storage

**Decision**: `color-scheme: light dark`; dark tokens under
`@media (prefers-color-scheme: dark)`; `:root[data-theme]` override in both
directions; the toggle applies `data-theme` before first paint and persists
inside `try`/`catch`.

**Rationale**: Design concept Q5. Two behaviors are easy to get wrong and are
explicitly tested by acceptance scenarios:

- **No flash of light theme** (SC-005) requires the stored-preference read and
  the `data-theme` write to happen in the snippet's inline script *in `<head>`,
  before body content parses*. A script placed at end-of-body paints light
  first. This ordering is therefore part of the canonical snippet, not a
  per-template choice.
- **`file://` storage refusal** (Story 3 scenario 3) — some browsers treat local
  documents as opaque origins and *throw* on `localStorage` access rather than
  returning null. The access is wrapped in `try`/`catch` so the theme still
  switches for the session and no error surfaces.

Both `:root[data-theme="dark"]` and `:root[data-theme="light"]` are needed: with
only the dark override, a dark-OS reviewer choosing light gets no effect, because
the media query still matches.

**Alternatives considered**: System-preference-only (no JS) — rejected in Q5, a
dark-OS reviewer could never see the light rendering of an artifact whose job is
to be reviewed.

## R8 — AA contrast is audited, not assumed

**Decision**: Ratios computed per theme with the WCAG relative-luminance
formula; the full table is recorded in `data-model.md` and restated in the
`brand-kit.css` comment block.

**Rationale**: FR-005 requires the two themes audited independently rather than
inferred from one another, and SC-007 demands 100% of pairings pass. Computing
rather than assuming caught two real failures in the palette as drafted:

1. `--rc-accent` `#3C89C6` on the light `--rc-surface-muted` `#E8E5DF` measures
   **2.99**, marginally under the 3:1 non-text floor. Resolved by a documented
   rule: use `--rc-link` `#2A6A99` (4.61) on muted surfaces.
2. The subtle border `#E0DED9` measures **1.24** against the light surface, far
   under 3:1. Resolved by splitting the token: `--rc-border-subtle` is
   decorative-only, and a new `--rc-border-strong` carries every boundary that
   conveys meaning. **Superseded in part by R13**: the light value was first set
   to `#8A8578` and audited only against `--rc-surface` (3.41); measured against
   all four light surfaces it falls to 2.93 on `--rc-surface-muted`, so the value
   is now `#847F72` (3.18–3.99). Dark `#6B7280` stands (3.21–3.81 once R14
   corrected the raised surface; 3.04–3.81 as first measured against `#1F2937`).
   **Superseded by R15**: the light darkening is reverted. Once the muted surface
   was corrected to `#EDEBE6`, the brand value `#8A8578` clears 3:1 on all four
   light surfaces (3.09–3.68), so the token is restored rather than engineered.

Brand red `#dc143c` passes at 3.97–4.99 across light surfaces, which is AA for
exactly the punctuation-level, non-text and large-text role FR-001 reserves it
for. A separate `--rc-danger-text` (`#C4102F` light, `#FF6B85` dark) covers the
case where red is used as body copy, where 4.5 is required.

**Alternatives considered**: Reusing the docs-site values unexamined — rejected;
that stylesheet targets Starlight's token names and a different surface set, and
its light `--sl-color-gray-6` comment records a near-invisible-text bug caused by
exactly this kind of unaudited reuse.

## R9 — FR-018: the gallery does not ship unless the allowlist changes

**Decision**: Add `"artifact-gallery"` to **both** per-platform copy lists in
`speckit-pro/speckit_pro_runner/gates/payloads.py`, and add an automated check
that fails when a gallery artifact exists in source but is absent from either
built payload.

**Rationale**: Verified directly in source. `build_xplat008_payloads` copies a
fixed list of top-level names per platform:

- Claude list (`payloads.py:298-308`): `.claude-plugin`, `agents`, `commands`,
  `hooks`, `skills`, `scripts`, `speckit_pro_runner`, `README.md`, `CHANGELOG.md`
- Codex list (`payloads.py:316-324`): `.codex-plugin`, `codex-agents`,
  `codex-hooks.json`, `scripts`, `speckit_pro_runner`, `README.md`, `CHANGELOG.md`

`artifact-gallery` is in neither. The copy helper is fail-silent
(`payloads.py:352-362`):

```python
def copy_optional_xplat008(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(...)
    elif src.is_file():
        ...
```

A source path that does not exist — or, equivalently, one that is never named —
produces no error and no output. **A green build is therefore not evidence that
the gallery shipped.**

Confirmed that no existing check closes this gap: the nearest candidate,
`tests/speckit-pro/layer1-structural/validate-payload-completeness.py`, is
scoped entirely to built Claude *skills* (`DIST_CLAUDE_SKILLS_DIR`,
`SRC_SKILLS_DIR`) and asserts body-completeness of `SKILL.md` files. It would
not notice an entire absent directory. This is precisely the failure mode FR-018
was written against, and it is the single most consequential item in the feature:
without the allowlist edit the whole feature is inert and every gate stays green.

**Direction of the check**: source-to-payload. Asserting "the payload contains a
gallery" is not enough, because ART-001 ships no `templates/` artifacts at all —
the check must assert that *whatever gallery files exist in source* are present
in both `dist/claude/speckit-pro/artifact-gallery/` and
`dist/codex/speckit-pro/artifact-gallery/`. That formulation is correct while the
gallery holds only foundation files today, and stays correct as ART-002…005 add
artifacts.

**Alternatives considered**: Trusting the existing payload conformance/checksum
machinery — rejected; those compare `dist/` against its own recorded manifest, so
a directory absent from both is self-consistently absent and passes.

## R10 — Repository test conventions

**Decision**: One file, `tests/speckit-pro/unit/test-artifact-gallery.py`,
registered as the last entry in the Layer 4 `scripts` array of
`tests/speckit-pro/suite-manifest.json`.

**Rationale**: Verified against the live suite:

- Entry shape is exactly three keys, one physical line, `baseline: null` for a
  test with no Bash predecessor:
  `{ "path": "tests/speckit-pro/unit/test-artifact-gallery.py", "label": "test-artifact-gallery", "baseline": null }`
- The array is append-ordered, not sorted, so the entry goes at the end and the
  current last line gains a comma.
- `run-all.py` dispatches each entry as a **subprocess**, not an import. The file
  must print a final `test-artifact-gallery: <passed>/<total> passed` line and
  exit non-zero on any failure. `run_counted` from `tests/speckit-pro/lib/test_result.py`
  provides both; the file follows the house entrypoint shape
  (`build_suite()` → `main()` → `raise SystemExit(main())`).
- `REPO_ROOT = Path(__file__).resolve().parents[3]`.
- Layer 4 never receives `--live`, so the file must not parse argv.
- Standard library only, `from __future__ import annotations`, dash-named file.

**Naming constraint that would otherwise bite**: `test-unit-layout.py` walks
every `unit/test-*.py` and fails any `test_*` **method name** containing a live
repository spec ID matching `<family>[-_]\d{3}`. `art` is a live family, so no
method may be named `test_art_001_*`. Methods are behavior-named. The filename
`test-artifact-gallery.py` is safe — "artifact" has no digits after a separator.

**Alternatives considered**: Splitting into several test files — rejected;
one focused file matches the 200–450 line house norm and keeps the marker-block,
manifest, scanner, attribution, and payload checks discoverable together.

## R11 — Generated-artifact obligations beyond `dist/`

**Decision**: Two generated surfaces must be regenerated and committed, not
hand-edited.

1. **Built payloads and their proofs** under `dist/` — required because
   `speckit-pro/artifact-gallery/` is shipped plugin source.
2. **`docs-site/src/content/docs/reference/tests.md`** — the docs-site reference
   generator enumerates every `.md`/`.py`/`.sh` under `tests/speckit-pro`, so
   adding the new unit test staleness-fails the committed reference page. This
   is enforced in CI by `pnpm --dir docs-site reference:check`.

**Rationale**: `tests/speckit-pro/AGENTS.md` states the rule for the test tree,
and the repository AGENTS.md worktree preflight notes that `docs-site/` is the
only surface with dependencies — `pnpm --dir docs-site install --frozen-lockfile`
must run once in this worktree before `reference:generate`. Missing this is a
known repeat failure mode: it passes locally and fails clean CI.

**Note on scope**: the payload regeneration is a *procedure*, executed during
implementation, and its outputs are declared generated. They are excluded from
projected reviewable LOC and are not part of the review surface, consistent with
the spec's Reviewability Notes.

## R12 — Reviewability budget: the scaffold figure is superseded

**Decision**: The recorded 435 / "5 net-new shipped foundation files" /
greenfield-allowance rationale **no longer holds** and is not carried forward.
Full recomputation and the replacement justification are in `plan.md` under
Reviewability Budget.

**Rationale**: Three things changed after the estimate was taken.

- **Greenfield is forfeit.** FR-018 requires *modifying*
  `speckit-pro/speckit_pro_runner/gates/payloads.py`. The estimator computes
  `greenfield = all(status == "NEW" or is_excluded_generated(path) ...)`
  (`speckit_pro_runner/helpers/read_only.py:929`), so one MODIFIED,
  non-generated entry drops the thresholds from 600/1200 back to the base
  400/800. The "1.5x greenfield allowance for net-new-only slices" is, by the
  estimator's own definition, unavailable.
- **The inputs grew.** The 435 came from the scaffold-time estimator
  (`estimate_spec_size`: `stories*25 + files*40 + frs*15`) on 3 stories, 6
  files, 8 FRs. Clarify took the spec to 20 FRs and the plan to 9 authored
  files; the accessibility checklist added FR-021 through FR-024, taking it to
  24. The same formula on current inputs gives **795**, `warn`, suggested
  slices 2 — five points under the 800 block threshold.
- **The plan-phase estimator measures something different and will report
  zero.** `estimate_reviewable_loc` counts only files where `is_production_file`
  is true — paths under `src/`, `app/`, `lib/`, `scripts/`, or ending
  `.ts/.tsx/.js/.jsx/.mjs/.cjs/.sql` (`read_only.py:3817-3818`). This feature is
  `.css`, `.html`, `.json`, `.md`, and `.py` — **none** match. The gate will
  return `projected: 0`, `production: 0`, `status: pass`. That is a passing
  number produced by a language filter that does not recognize this feature's
  file types, and it must not be read as evidence the slice is small.

All three figures are reported in `plan.md` rather than one flattering one.

## R13 — Accessibility audit: what the first pass missed

**Decision**: FR-021 through FR-024 are added, FR-004, FR-005, and FR-010 are
amended, and two more contrast failures are resolved. R8's method was right; its
*coverage* was not.

**Rationale**: R8 established that computing ratios beats asserting them, and
that finding paid off twice. Re-running the computation across the full token
matrix — every foreground against every surface, in both themes — found that the
audit itself had two holes, and a failure was sitting in each one.

1. **The dark table had no `--rc-brand-red` row at all.** The light table
   audited it; the dark table simply omitted the token, so no reader could tell
   whether it had passed or been skipped. Measured: 3.49 / **2.94** / 3.69 /
   3.34 across the four dark surfaces. The pairing with `--rc-surface-raised`
   `#1F2937` is under the 3:1 non-text floor. Resolved the same way R8 resolved
   the accent failure — prohibit the pairing, name the replacement
   (`--rc-danger-text` `#FF6B85`, 5.38). **Superseded by R14**: the cause was the
   surface, not the token. `--rc-surface-raised` is now `#242424`, brand red
   clears 3:1 on all four dark surfaces (3.11–3.69), and this prohibition no
   longer exists.
2. **`--rc-border-strong` was audited against one surface out of four.** R8
   recorded "3.41 on `--rc-surface`" where every other row carried a range.
   Measured across all four light surfaces, `#8A8578` gives 3.41 / 3.68 / 3.23 /
   **2.93** — under the floor on `--rc-surface-muted`. This one is *not* resolved
   by prohibition: the token exists precisely to carry boundaries that convey
   meaning, so a rule forbidding it on one surface would be a trap for exactly
   the author it is meant to serve. The value is darkened one step to `#847F72`
   (3.18–3.99 across all four). Dark `#6B7280` was re-measured and stands
   (3.04–3.81, binding minimum on raised — lifted to 3.21–3.81 by R14, which
   removed that binding constraint by correcting the surface). **Superseded by
   R15**: the light value returns to `#8A8578`. The cause was the muted surface,
   which R8 and this finding had each hit independently without noticing they
   shared one.

Both holes share one shape: **an unmeasured pairing read as a passing one.**
FR-005 is amended so absence is a defect — the audit must be symmetric across
themes and complete across surfaces, and every failing pairing must carry a
usage rule naming its replacement. A rounding error was also corrected
(`--rc-danger-text` light maximum is 6.07, recorded as 6.05).

**Font loading — verified against the live endpoint, not assumed.** The spec
said fonts are "loaded as linked web fonts with swap behavior". Swap is not a
property of the link. Requesting the provider's `css2` stylesheet **without** the
display parameter returns a stylesheet containing **zero** `font-display`
declarations, leaving the descriptor at its initial value — a blocking behavior
with an invisible-text period in the major engines, which is precisely what the
spec's own edge case forbids. The same request **with** the parameter returns
`font-display: swap` on every `@font-face`. FR-024 therefore makes the request
parameter the requirement and check E4 enforces it; nothing else in the check
inventory would have noticed, because the host allowlist passes either way.

**`color-scheme` does not follow an in-page override.** The design declared
`color-scheme: light dark` "so form controls and scrollbars follow". That
declaration states which schemes the page supports and resolves against the
*operating-system* preference; it does not observe `data-theme`. A reviewer on a
dark OS who forces light therefore gets light page tokens and dark native
widgets. Resolved by setting the scheme explicitly under each `data-theme`
override (FR-004).

**The shared blocks are the leverage point.** The theme toggle and the token
block are embedded verbatim into all 21 artifacts, so an accessibility defect
specified into either reaches every template and no port can fix it locally.
Nothing in the feature previously required the control to be keyboard-operable
or to expose a name, role, or state — "keyboard", "aria", "role", and
"accessible name" appeared zero times across every artifact. FR-022 fixes those
in the canonical snippet; FR-023 does the same for focus visibility and
reduced motion; check group I asserts each construct actually sits **inside** the
copied region, since a rule above the start marker looks correct in the
canonical file and ships to nothing.

**Use of color is a separate obligation from contrast.** The brand-red rule was
expressed only as "punctuation-level emphasis" plus a size and contrast
restriction — a rule about how much red is used, not about what red is allowed
to mean alone. FR-021 adds the missing constraint: red may never be the sole
visual carrier of information, and the two rules are documented as distinct so
neither reads as discharging the other.

**Alternatives considered**: Leaving FR-005's absolute "every pairing MUST meet
AA" wording in place and treating the prohibited pairings as understood —
rejected, because the requirement then contradicts the accepted design and a
future reader cannot tell a deliberate prohibition from an oversight, which is
the exact confusion that let two failures hide. Adding a dark-specific brand-red
token instead of prohibiting the raised pairing — rejected, it adds a permanent
token to serve one surface where an existing token already fits.

---

## R14 — The failing pairing was the surface's fault, not the token's

**Supersedes R13 finding 1 and the dark half of R8.** R13 resolved brand red's
2.94 against the dark raised surface by prohibiting the pairing. That resolution
was sound given the options it weighed, but its alternatives analysis had a blind
spot: it considered changing the *foreground* — prohibit it, or add a dark
brand-red token — and never considered changing the *surface*.

The raised surface was `#1F2937`. That value traces to
`docs-site/src/styles/brand.css`, where it is `--sl-color-bg-nav` and
`--sl-color-bg-sidebar` — the navigation and sidebar background. The brand source
defines **no** raised content surface at all: it has a page background
(`#1a1a1a`), that navigation chrome, and a code-chip grey (`#1e1e1e`). So
`--rc-surface-raised` is a token this feature introduced, populated by borrowing
a value chosen for a different job. It was also the only non-neutral among the
four dark surfaces, the other three being pure greys.

**Two facts make correcting the surface strictly better than prohibiting the
pairing.** First, `#1F2937` misses by almost nothing: brand red needs the raised
luminance at or below 0.02014 to clear 3:1, and `#1F2937` is 0.02153 — over by
0.0014. Second, that same surface held the tightest ratio anywhere in the kit,
`--rc-border-strong` at 3.04, which the audit itself flagged as the binding
minimum. One surface was constraining two tokens.

Re-valuing it to a neutral `#242424` lifts **every** dark foreground at once and
regresses none:

| Foreground | on `#1F2937` | on `#242424` |
|---|---|---|
| `--rc-brand-red` | 2.94 (fails 3:1) | **3.11** |
| `--rc-border-strong` | 3.04 (binding minimum) | **3.21** |
| `--rc-text` | 11.76 | 12.44 |
| `--rc-text-muted` | 5.78 | 6.11 |
| `--rc-link` | 6.54 | 6.91 |
| `--rc-accent` | 3.90 | 4.13 |
| `--rc-danger-text` | 5.38 | 5.69 |

Elevation still reads: `#242424` (luminance 0.01764) stays above `--rc-surface`
`#1A1A1A` (0.01033) and `--rc-surface-muted` `#1E1E1E` (0.01298), so the
ordering sunken < surface < muted < raised is preserved.

**Decision**: `--rc-surface-raised` dark becomes `#242424`. R13's brand-red
prohibition is removed, not relaxed — brand red now clears its floor on all four
surfaces in both themes and carries no exception. All 64 pairings were recomputed
from the shipped token values and both header tables verified row by row.

**Alternatives considered**: Keeping the prohibition — rejected once the surface
was identified as the cause, because it leaves an authoring trap in place across
all 21 planned templates to protect a borrowed value. A dark-specific brand-red
variant (`#EA1A44`, which also clears 3:1) — rejected for the same reason R13
rejected it, and now unnecessary. Darkening `#1F2937` within its own blue-grey
hue family — viable, but it would preserve the one non-neutral in an otherwise
neutral surface set for no stated reason.

**Lesson**: when a pairing misses its floor, the surface is a candidate for
correction, not just the foreground. R13 enumerated foreground remedies
exhaustively and never asked whether the background was right. A token borrowed
from another role is the first place to look.

---

## R15 — Applying R14's lesson to the light theme restores a brand value

**Supersedes R8's accent prohibition and R13 finding 2.** R14 established that a
surface can be the cause of a contrast miss. Applied to the light theme, the same
question has a stronger answer, because one surface was constraining two tokens
and one of those constraints had already forced a brand value to be altered.

`--rc-surface-muted` was `#E8E5DF`, the darkest of the four light surfaces. Two
separate findings traced to it and to nothing else:

- **R8**: `--rc-accent` `#3C89C6` measures **2.99** against it, below the 3:1
  non-text floor. Resolved then by prohibiting the pairing.
- **R13 finding 2**: `--rc-border-strong`'s value `#8A8578` measures **2.93**
  against it. Resolved then by darkening the token to `#847F72`.

Both remedies were local to a foreground. Neither asked whether `#E8E5DF` was
right. As with `#1F2937`, it misses by very little: the accent needs the muted
luminance at or above 0.78788 to clear 3:1, and `#E8E5DF` is 0.78522 — short by
0.00266.

**The window is wide.** Muted must stay darker than `--rc-surface-sunken`
`#F1F0EC` (luminance 0.87077) to keep reading as recessed, so the usable range is
0.78788 to 0.87077 — a width of 0.0829, far more headroom than the dark theme
had. `#EDEBE6` (0.83134) sits comfortably inside it.

**What lightening it buys.** Not just the accent. From `#EBE9E3` upward,
`--rc-border-strong` clears 3:1 on all four light surfaces at its **original
brand value** `#8A8578`, so the R13 darkening becomes unnecessary and is
reverted:

| Foreground | on `#E8E5DF` | on `#EDEBE6` |
|---|---|---|
| `--rc-accent` | 2.99 (fails 3:1) | **3.16** |
| `--rc-border-strong` `#8A8578` | 2.93 (fails 3:1) | **3.09** |
| `--rc-text` | 14.11 | 14.89 |
| `--rc-text-muted` | 6.01 | 6.34 |
| `--rc-link` | 4.61 | 4.87 |
| `--rc-brand-red` | 3.97 | 4.19 |
| `--rc-danger-text` | 4.82 | 5.09 |

**Decision**: `--rc-surface-muted` light becomes `#EDEBE6`, and
`--rc-border-strong` light is **restored** to the brand value `#8A8578`
(3.09–3.68 across the four light surfaces). R8's accent prohibition is removed.
All 64 pairings were recomputed from the shipped token values and both header
tables verified row by row.

**Net effect across R14 and R15.** The kit began with four rules — two
prohibitions and two foreground corrections — and now has three: one prohibition
and two surface corrections. The single remaining prohibition is
`--rc-border-subtle`, which is not a contrast defect at all but a role statement
about a token deliberately built to be faint. No brand primitive carries a
restriction, and no functional token sits at an engineered value.

**Alternatives considered**: Keeping the accent prohibition and the darkened
border value — rejected, because both existed only to accommodate a surface that
was itself one step off, and both imposed a rule on all 21 planned templates.
Lightening only as far as `#EAE7E1`, the minimum that clears the accent (3.05) —
rejected, because it leaves `#8A8578` at 2.98, still short, and so would preserve
the border-strong correction for nothing. Re-valuing `--rc-accent` — rejected on
FR-025 grounds: brand blue is a primitive and is not re-valued by engineering.

**Lesson**: check whether two findings share a cause before resolving either. R8
and R13 finding 2 were treated as independent and given independent remedies;
they were the same surface, measured twice.

---

## Resolved design-concept open questions

| Deferred question | Resolution |
|---|---|
| Final closed signal vocabulary | Fixed at five members by FR-015; closure verified against all 21 seeded entries (R3) |
| Manifest field shape, `schema_version`, category enum, and where documented | Fixed by Clarifications Session 2; enum origin verified against the upstream index (R2); documented in `SPA-CONTRACT.md`, enforced by the Layer 4 test, no formal schema document |

## Remaining unknowns

None. No unresolved clarification is carried into Phase 1.

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
`theme-toggle.html` carries `<!-- THEME-TOGGLE:START -->` … `<!-- THEME-TOGGLE:END -->`.
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
   decorative-only, and a new `--rc-border-strong` (`#8A8578` light, 3.41;
   `#6B7280` dark, 3.60) carries every boundary that conveys meaning.

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
  files. The same formula on current inputs gives **735**, `warn`, suggested
  slices 2.
- **The plan-phase estimator measures something different and will report
  zero.** `estimate_reviewable_loc` counts only files where `is_production_file`
  is true — paths under `src/`, `app/`, `lib/`, `scripts/`, or ending
  `.ts/.tsx/.js/.jsx/.mjs/.cjs/.sql` (`read_only.py:3817-3818`). This feature is
  `.css`, `.html`, `.json`, `.md`, and `.py` — **none** match. The gate will
  return `projected: 0`, `production: 0`, `status: pass`. That is a passing
  number produced by a language filter that does not recognize this feature's
  file types, and it must not be read as evidence the slice is small.

All three figures are reported in `plan.md` rather than one flattering one.

---

## Resolved design-concept open questions

| Deferred question | Resolution |
|---|---|
| Final closed signal vocabulary | Fixed at five members by FR-015; closure verified against all 21 seeded entries (R3) |
| Manifest field shape, `schema_version`, category enum, and where documented | Fixed by Clarifications Session 2; enum origin verified against the upstream index (R2); documented in `SPA-CONTRACT.md`, enforced by the Layer 4 test, no formal schema document |

## Remaining unknowns

None. No unresolved clarification is carried into Phase 1.

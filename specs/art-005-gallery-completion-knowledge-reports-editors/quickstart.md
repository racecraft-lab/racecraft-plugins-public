# Quickstart: ART-005 Validation

This guide defines the validation route for the seven ART-005 slices. It is a
planning artifact, not the UAT runbook itself.

## Prerequisites

Start from the ART-005 worktree:

```bash
cd "$(git rev-parse --show-toplevel)"
```

Confirm the current branch for slice 1:

```bash
git branch --show-current
```

Expected:

```text
art-005-gallery-completion-knowledge-reports-editors
```

The upstream evidence should remain outside the repository at:

```text
/private/tmp/art-005-upstream-58c305be97f47b26b678f2c07dec01d4242268ec/
```

If that scratch directory has been purged, rehydrate the seven root HTML files
from `anthropics/html-effectiveness` at the exact commit
`58c305be97f47b26b678f2c07dec01d4242268ec` into a fresh temporary directory,
then require every digest in `research.md` to match before continuing. Never
substitute floating upstream `main`.

## Per-Slice Validation Flow

Run each slice in stack order. Later branches are created only after the
predecessor PR is open.

For each slice:

1. Reverify the slice's upstream file digest from the pinned snapshot.
2. Confirm the planned authored footprint is exactly seven paths: the new
   template, one manifest row, two focused test modules, and the three active
   UAT evidence files.
3. Run the relevant focused Layer 4 tests and confirm they fail for the missing
   template/status/fill/export behavior before implementation.
4. Add exactly one template and flip exactly one manifest row.
5. Measure authored LOC after template scaffolding. Stop the slice if actual
   LOC plus remaining declared component budget would reach 800 or more.
6. Run focused Layer 4 gallery and fill-region tests.
7. Measure authored LOC after focused tests. Stop before generated refresh if
   the slice would reach 800 or more.
8. Run:

```bash
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
```

9. Regenerate source-derived release artifacts:

```bash
python3 scripts/refresh-release-artifacts.py
```

10. Regenerate docs test references after test-tree changes:

```bash
pnpm --dir docs-site reference:generate
```

11. Confirm generated/check output is within the expected physical footprint:
    up to 25 generated paths plus seven implementation-authored paths and one
    possible `tasks.md` control-plane path. Do not count generated or
    control-plane paths as implementation-authored reviewability paths, do
    include them in the complete Git-path count, and do not claim byte-identical
    generated outputs as changed.
12. Run the default suite:

```bash
python3 tests/speckit-pro/run-all.py
```

13. Verify generated artifacts in check mode:

```bash
python3 scripts/refresh-release-artifacts.py --check
```

14. Commit a source checkpoint containing the current template, manifest,
    focused tests, generated outputs, and existing UAT carrier files. Record its
    SHA before writing new UAT results.
15. Execute active `file://` UAT under the checkpoint. Re-run the complete row
    set for every artifact shipped through this slice, replace the cumulative
    JSON rows, and set its top-level `sourceCommit` to the checkpoint SHA:

```text
specs/art-005-gallery-completion-knowledge-reports-editors/.process/
```

16. Measure final authored LOC before PR open. Also record the complete physical
    path count and its authored/control-plane/generated classification. Stop if
    authored LOC reaches 800 or any non-size/correctness blocker exists. If the
    only full-diff block is required generated/control-plane file count, record
    it as size-only in UAT and the PR packet and continue through the ratified
    branch stack.

## Manual `file://` Checks

For every artifact:

- open the HTML file directly from the filesystem
- confirm complete representative content
- reload while offline and confirm content remains present
- traverse all controls by keyboard
- verify visible focus
- switch light/dark theme and confirm parity
- enable reduced motion and confirm no required motion remains
- confirm status/priority/error meaning is not color-only
- review at 360 CSS px and at a desktop width of at least 1280 CSS px; record
  page-level horizontal overflow, clipped text, overlapping text, and any named
  scroll-region exception
- record horizontal scroll regions as pass when focusable/named, or
  `not_applicable` with an observed layout explanation when absent
- for each accessibility row, record structured evidence where relevant:
  focus-order selector/role/name/indicator sequence, focused fallback target,
  scroll-region selector/role/name/`tabindex` and actual-scroll-element evidence,
  status-region role or live-region semantic, and audited-token or measured
  light/dark contrast source

For `concept-explainer`:

- exercise add/remove and slider min/max boundaries
- confirm the visible node/key counts and helper or status text explain the
  boundary while leaving state unchanged at the limit

For the three editors:

- change visible state
- invoke `Copy as Markdown`
- confirm the exported text matches current live state
- confirm a genuine clipboard success by read-back or paste equality
- force clipboard unavailable with `Object.defineProperty`
- force `writeText` absent or non-callable and confirm zero write attempts
- force a permission-denied rejection such as `NotAllowedError`
- force a generic promise rejection
- force synchronous throw
- confirm each forced failure uses the exact failure message, makes zero or one
  write attempt as applicable, and reveals a labeled selectable field containing
  and focusing the exact attempted export
- run failure, success, then failure with three distinct values; after each step,
  confirm status, fallback visibility/content, and focus reflect only that attempt
- confirm success, failure, warning, dependency, movement, filter, validation, and
  editor-state messages update a status region without adding a tab stop
- trigger applicable empty, invalid, dependency, unavailable-value, and
  filtered-no-result states; record the visible text or inline cue and
  status-region feedback where the state changes dynamically
- reload and confirm editor working state resets to representative sample data

## Data-Integrity Validation

For every slice, verify manifest/export parity against the exhaustive ART-005
table in the spec: artifact ID, upstream source file, digest, semantic role,
status, and `exports` must match the slice being shipped. Reader artifacts record
producer-only data-integrity cases as evidence-backed `not_applicable`.

For each producer:

1. Set a visible field to `FRESHNESS-OLD-<artifact>`.
2. Export and retain the baseline string.
3. Replace that field with `FRESHNESS-NEW-<artifact>`.
4. Export again.
5. Confirm the second string differs from the baseline, contains the new
   sentinel, excludes the replaced old sentinel, and is the exact text observed
   in the clipboard read-back or fallback field for that invocation.

For each structured export:

1. Extract the sole fenced JSON block.
2. Parse it.
3. Reserialize it with `JSON.stringify(value, null, 2)`.
4. Confirm byte equality with the extracted block, including wrapper, collection,
   field, and issue ordering.

Exercise and record data-integrity rows for applicable producer cases:

- empty required text and empty collections
- duplicate identifiers
- raw invalid values
- unavailable normalized values
- multiple simultaneous issues
- multiline and special-character values containing:

```text
Zoë / 東京 | `quoted` "double" \ path\tline\nsecond
```

Compare expected and observed entity order, field order, ticket order, and issue
order explicitly. For issue records, compare `code`, `artifactId`, `entityType`,
`entityId`, `field`, `occurrenceIndex`, `relatedOccurrenceIndex`, `rawValue`,
`normalizedValue`, and `message`.

For stale-copy prevention, start two controllable copy attempts and settle them
out of order in both directions: older delayed success after newer failure, and
older delayed failure after newer success. Confirm the older settlement cannot
restore stale status text, fallback text, fallback visibility, or focus.

Reload each producer after data-integrity checks and confirm representative seed
state returns with no previous raw invalid value, issue state, fallback text, or
export string persisted.

## Expected Closeout

At the end of each slice:

- exactly one new artifact file exists
- exactly one manifest row moved from `planned` to `shipped`
- exactly seven authored paths are present in the slice
- `tasks.md`, when changed, is reported as one separate control-plane path
- generated/check paths stay within the 25-path expected generated footprint or
  any extra generated diff is explicitly explained; the complete physical count
  and any generated/control-plane-only size block are recorded
- Layer 1 and Layer 4 pass
- the default suite passes
- generated payload and proof files are consistent
- docs reference output is regenerated after test changes
- active UAT result rows include the slice's artifact
- every cumulative UAT row was re-executed at the top-level `sourceCommit`

At the end of slice 7:

- all seven ART-005 entries are shipped
- all seven templates open over `file://`
- the active UAT JSON contains a row for every required check
- archival paths are ready for post-merge preservation

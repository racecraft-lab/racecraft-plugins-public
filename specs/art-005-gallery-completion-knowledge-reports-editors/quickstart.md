# Quickstart: ART-005 Validation

This guide defines the validation route for the seven ART-005 slices. It is a
planning artifact, not the UAT runbook itself.

## Prerequisites

Start from the ART-005 worktree:

```bash
cd /Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/art-005-gallery-completion-knowledge-reports-editors
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
    up to 25 generated paths plus seven authored paths. Do not count generated
    paths as authored reviewability paths, and do not claim byte-identical
    generated outputs as changed.
12. Run the default suite:

```bash
python3 tests/speckit-pro/run-all.py
```

13. Verify generated artifacts in check mode:

```bash
python3 scripts/refresh-release-artifacts.py --check
```

14. Execute or update active `file://` UAT evidence under:

```text
specs/art-005-gallery-completion-knowledge-reports-editors/.process/
```

15. Measure final authored LOC before PR open. Stop the slice if it reaches 800
    or more, even if all tests pass.

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
- record horizontal scroll regions as pass when focusable/named, or
  `not_applicable` with an observed layout explanation when absent

For the three editors:

- change visible state
- invoke `Copy as Markdown`
- confirm the exported text matches current live state
- confirm a genuine clipboard success by read-back or paste equality
- force clipboard unavailable with `Object.defineProperty`
- force promise rejection
- force synchronous throw
- confirm each forced failure reveals and focuses the exact fallback text
- reload and confirm editor working state resets to representative sample data

## Expected Closeout

At the end of each slice:

- exactly one new artifact file exists
- exactly one manifest row moved from `planned` to `shipped`
- exactly seven authored paths are present in the slice
- generated/check paths stay within the 25-path expected generated footprint or
  any extra generated diff is explicitly explained
- Layer 1 and Layer 4 pass
- the default suite passes
- generated payload and proof files are consistent
- docs reference output is regenerated after test changes
- active UAT result rows include the slice's artifact

At the end of slice 7:

- all seven ART-005 entries are shipped
- all seven templates open over `file://`
- the active UAT JSON contains a row for every required check
- archival paths are ready for post-merge preservation

# Readiness fingerprint security: PR #1346

The shared policy helper owns both the writer and every freshness reader for
Claude and Codex. The existing `reviewability_report` observation binds a single
report/roadmap file and `values.spec_id`. Its saved SPEC digest selects exactly
one row; other observations always hash raw bytes, including observations that
name that same file. Cache entries include the SPEC digest to keep those two
comparisons separate.

The exception replaces only a plain `⏳ Pending` or `🔄 In Progress` token (also
accepting the plain-text spellings) in that row's Status cell. It preserves cell
spacing and all other bytes. It applies only to the single table immediately following
a top-level `## Progress Tracking` heading. Linked Status cells, completed
statuses, other SPEC rows, other headings and other file evidence change the
digest. Renames, missing files and symlink substitutions fail freshness checks.

Escaped pipes remain inside their cells, including code spans and links. This
follows the [GitHub Flavored Markdown table specification](https://github.github.com/gfm/#tables-extension-),
which requires escaping a content pipe inside inline spans too. Raw extra pipes
are never guessed into the selected row: mismatched cell counts retain raw
bytes. Every byte outside the selected status token remains evidence.

The `RoadmapOffer*FreshnessTest` classes in
`tests/speckit-pro/unit/test-readiness-record.py` share the
`RoadmapOfferFreshnessCase` base and its `RoadmapEditCase` table rows. They
exercise each reported variant on both hosts through publication/readback,
`current_record` and G0's stale-input reader. Each allowed flip has a forbidden
edit in the same class, so reverting the fix makes them red. Every class is
explicitly included in the file's `build_suite()`.

## Known limits

- The exception deliberately recognizes a narrow Markdown shape: edge pipes,
  unique column names, one selected row and one immediate Progress Tracking
  table. Multiple file inputs, multiple matching tables, malformed tables,
  missing rows and unsupported row syntax keep raw fingerprints. Those inputs
  fail closed on a subsequent status edit; they cannot suppress another edit.
- Tables inside fenced examples or following an HTML block retain raw bytes.
  HTML block parsing is deliberately conservative: an earlier HTML block can
  disable the exception even if closed. A status flip then requires a fresh
  evaluation, rather than permitting an unverified normalization. The shipped
  `technical-roadmap-template.md` has guidance comments at column zero above
  `## Progress Tracking`. A roadmap that keeps them gets no exception, so its
  Step 8 flip still reads the offers as stale. The repository's roadmaps and the
  scaffold-reviewability fixtures carry no such comment.
- Rows with consecutive backslashes keep raw fingerprints. Their escape
  interpretation is outside this narrow exception; changing them cannot hide
  non-status content.
- Unicode separators cannot create Markdown rows or fence boundaries, and
  non-ASCII spacing cannot turn a different SPEC or header into the selected
  one. Files containing non-ASCII whitespace or lone carriage returns retain
  raw fingerprints, including apparent fence closers with Unicode suffixes.
  Raw and scoped reads count separately toward the 64-read budget; this
  can fail closed earlier for an input named by multiple observations.
- A proposed missing-leading-pipe header cannot reach normalization:
  `PROGRESS_TABLE_RE` requires a leading pipe at column zero, and the first
  header cell must be `Spec`. A header beginning `Note | Spec` is hashed raw.
  The ambiguous-table test includes this unreachable normalization control.
- Older readiness records used an overbroad digest. They must be evaluated
  again; no migration interprets an old digest as fresh evidence.
- Linux VM tests do not prove native macOS plugin coverage or the orchestrator's
  two real-sandbox hardening checks. Interactive questions and a live scaffold
  session were not exercised; tests use the documented request schema.

Daybreak must recheck the fix commits and account for every finding variant.
This document does not close the findings or waive a merge gate.

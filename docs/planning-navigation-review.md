# Planning navigation review notes

Scope: issue #1383, against `origin/main`. The generator remains the shared
rendering seam for recorded planning approval on both hosts.

## Known limits

- Unlinked PR metadata that looks like a URL or email address is refused rather
  than auto-linked. Scoped package paths remain literal text. Backlink labels
  may contain at signs or `www.` because their destinations are quoted relative
  paths and their structural punctuation is escaped. Trailing spaces are stripped
  from each field before encoding so a field cannot create a hard line break.
- The new fixture centralizes runner paths and paired-host verification.
  `NavigationFixture.captureNavigation` and `assertNavigationBound` retain their
  pre-existing host loops to keep the shared test file additive. These are fixed
  test inputs, not contributor-selected execution paths or a runtime defect.
- The row renderer calls the one literal encoder for each field explicitly.
  The repeated calls do not duplicate the validation rule or leave an unencoded
  contributor-controlled field.
- The scaffold predicate retains an `if` followed by `return False`. Collapsing
  that expression is a style change with identical behavior.
- The existing sweep-log fixture now includes the delimiter its real writer
  emits. This is an additive test correction; the new regressions separately
  exercise separator removal, column count, and alignment on both host runners.

- A complete canonical Consensus Resolution Log header and delimiter remain
  a typed write: deleting both together is digest-neutral, as it was before
  this fix. Planning row contents remain bound. Binding the pair would also
  reject legitimate runtime table creation; removing either line alone or
  editing the delimiter remains detectable. This existing limit cannot inject
  a link or change the bound planning row text.
- The reference's phrase "typed Implement write" includes feedback and
  consensus sweep scaffolds processed by the same runtime projection.

Cross-host review notes (head `f44bef3d`), recorded as non-blocking:

- `test-planning-approval.py` keeps five pre-existing copies of the dist
  runner path (lines 556, 572, 695, 826 and 838); `HOST_RUNNERS` in the new
  file is a sixth. All are fixed test inputs, not a runtime path.
- The "regenerate navigation before approval" guidance has no code gate. It
  cannot fail open: `map_navigation` binds a block that differs from the
  generator's output, so a skipped regeneration forces a new approval.
- `_progress_table_scaffold` holds its own `-{3,}` delimiter check beside
  `sweep_export`. The stricter rule is deliberate: it refuses alignment
  colons, which the shared table-rule predicate accepts.
- The `neighbors` parameter defaults are unused; `workflow_content` is the
  only caller and always passes both neighbors.
- An owned table indented one to three spaces stays bound, because the pair
  check reads the raw neighbor line. This fails closed: the edit needs a new
  approval. Real writers emit unindented tables.

## Verification interpretation

The original progress fixtures remain unchanged: complete canonical Implement
table creation preserves approval. Header and delimiter are projected together;
deleting either line alone, changing columns, or adding alignment leaves structure bound to
the revision. Other table separators remain planning content. A standalone
header is not a complete runtime table write.

Ripwire's dynamic-call analysis labels the new unittest methods as dead code;
the explicit unittest loader executes them in the focused VM suite. Its
remaining verbosity advisories measure the required additive agent guidance and
test registration. No acknowledgment ledger was changed.

Numeric escaping follows [CommonMark's character-reference rules](https://spec.commonmark.org/0.31.2/#entity-and-numeric-character-references).
Separate link validation covers [GFM autolinks](https://github.github.com/gfm/#autolinks-extension-),
which can recognize URLs and email addresses in text nodes.

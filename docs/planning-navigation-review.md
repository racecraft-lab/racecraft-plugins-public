# Planning navigation review notes

Scope: issue #1383, against `origin/main`. The generator remains the shared
rendering seam for recorded planning approval on both hosts.

## Known limits

- Unlinked PR metadata that looks like a URL or email address is refused rather
  than auto-linked. Scoped package paths remain literal text. Backlink labels
  may contain at signs or `www.` because their destinations are quoted relative
  paths and their structural punctuation is escaped.
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

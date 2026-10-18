# Planning navigation review notes

Scope: issue #1383, against `origin/main`. The generator remains the shared
rendering seam for recorded planning approval on both hosts.

## Known limits

- Unlinked PR metadata that looks like a URL or email address is refused rather
  than auto-linked. Scoped package paths remain literal text. Backlink labels
  may contain at signs or `www.` because their destinations are quoted relative
  paths and their structural punctuation is escaped.
- The new tests repeat the existing fixture's two-host invocation pattern.
  Those paths are fixed test inputs, not contributor-selected execution paths;
  there is no reachable runtime defect. A fixture-wide cleanup would touch the
  shared approval tests and is outside this fix.
- The row renderer calls the one literal encoder for each field explicitly.
  The repeated calls do not duplicate the validation rule or leave an unencoded
  contributor-controlled field.
- The scaffold predicate retains an `if` followed by `return False`. Collapsing
  that expression is a style change with identical behavior.
- The existing sweep-log fixture now includes the delimiter its real writer
  emits. This is an additive test correction; the new regressions separately
  exercise separator removal, column count, and alignment on both host runners.

## Verification interpretation

The original progress fixtures remain unchanged: complete canonical Implement
table creation preserves approval. Header and delimiter are projected together;
deleting either, changing columns, or adding alignment leaves structure bound to
the revision. Other table separators remain planning content. A standalone
header is not a complete runtime table write.

Ripwire's dynamic-call analysis labels the new unittest methods as dead code;
the explicit unittest loader executes them in the focused VM suite. Its
remaining verbosity advisories measure the required additive agent guidance and
test registration. No acknowledgment ledger was changed.

Numeric escaping follows [CommonMark's character-reference rules](https://spec.commonmark.org/0.31.2/#entity-and-numeric-character-references).
Separate link validation covers [GFM autolinks](https://github.github.com/gfm/#autolinks-extension-),
which can recognize URLs and email addresses in text nodes.

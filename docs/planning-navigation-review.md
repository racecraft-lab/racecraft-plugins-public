# Planning navigation review notes

Scope: issue #1383, against `origin/main`. The generator remains the shared
rendering seam for recorded planning approval on both hosts.

## Known limits

- The autolink guard conservatively refuses any `@`, including a benign Git
  branch or filename containing that character. This is a compatibility limit,
  not an accepted injection path. Use literal labels and repository paths.
- The new tests repeat the existing fixture's two-host invocation pattern.
  Those paths are fixed test inputs, not contributor-selected execution paths;
  there is no reachable runtime defect. A fixture-wide cleanup would touch the
  shared approval tests and is outside this fix.
- The row renderer calls the one literal encoder for each field explicitly.
  The repeated calls do not duplicate the validation rule or leave an unencoded
  contributor-controlled field.
- The scaffold predicate retains an `if` followed by `return False`. Collapsing
  that expression is a style change with identical behavior.
- The existing `test_new_sweep_log_separator_preserves_approval` test adds a
  header, not a separator. Its unchanged name is misleading, but its assertion
  does not exempt table separators from the digest. The new regression tests
  exercise separator removal, column count, and alignment directly.

## Verification interpretation

The progress fixtures now create table structure before approval, then exercise
only typed row updates. Adding or changing a separator requires a new planning
revision, as required by this fix.

Ripwire's dynamic-call analysis labels the new unittest methods as dead code;
the explicit unittest loader executes them in the focused VM suite. Its
remaining verbosity advisories measure the required additive agent guidance and
test registration. No acknowledgment ledger was changed.

Numeric escaping follows [CommonMark's character-reference rules](https://spec.commonmark.org/0.31.2/#entity-and-numeric-character-references).
Separate link validation covers [GFM autolinks](https://github.github.com/gfm/#autolinks-extension-),
which can recognize URLs and email addresses in text nodes.

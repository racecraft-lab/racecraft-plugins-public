# Documentation citation validation: security fix

The validator checks complete literal layer paths against the Git index. Code
spans and link destinations retain filename characters, including spaces,
Unicode, punctuation and trailing dots. A trailing slash requires tracked
descendants, so a regular file cannot pass as a directory. Extraction does not
depend on whether a shorter prefix exists.

Regression cases exercise the `collect_errors(repo_root, tracked)` seam using
temporary ADRs. Restoring the pre-fix extraction and normalization makes every
new regression test fail; the fixed validator also accepts exact tracked names
with unusual characters. The same repository check covers both plugin hosts;
no installed plugin source or payload changes.

## Known limits

- Bare prose ends a path at whitespace and permits a terminal comma or a single
  sentence-final dot. Those boundaries cannot establish that whitespace or
  punctuation is a literal filename suffix. Use a code span or an angle-bracket
  link destination for an unambiguous literal filename. Literal suffixes are
  covered by the regression tests.
- A code span represents one complete citation after the layer-path prefix.
  Extra command arguments or a second citation in the same span fail closed;
  put separate citations in separate spans. This validator is not a general
  Markdown command or expression parser.
- The check establishes Git-index membership, not filesystem resolution of
  symlink targets. A tracked directory with a trailing slash is valid; a
  regular file with a trailing slash is not. These are the intended citation
  rules, rather than evidence that an untracked literal path exists.

Daybreak must re-check both finding IDs and account for every reported variant
and the fix commits before either finding is resolved.

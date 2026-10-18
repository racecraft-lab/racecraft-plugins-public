# Generated navigation binding: PR #1373

Finding `F1373-a7ea4f86`: generated navigation injection.

A feature map's generated PRS and BACKLINKS bodies are rebuilt from runtime
inputs that the planning inventory excludes: `.process/prs.json` and the names
of files under `artifacts/`, `.process/` and `plan-approvals/`. The planning
projection used to drop a whole generated body whenever it matched the
renderer's output. Any text the renderer echoed was therefore outside the
approval digest, so a regenerated map could carry a link or an instruction
while `verify` still accepted the old approval.

`map_navigation` in `helpers/planning_approval.py` now drops a generated line
only when it is the renderer's fixed frame (the PRS notice, blank line, table
header and rule) or a row whose every runtime value is a bounded token: ASCII
letters, digits and `_ . + - /`, or `PR#<integer>`. A token has no whitespace,
Markdown or HTML syntax, URL scheme, address, or `www.` prefix. Every other
generated line stays in the projection, so changing it changes the digest and
`verify` refuses. Typed progress (new PR rows, SHAs, branch names, statuses,
runtime file names) still keeps the recorded revision.

The tests are in `tests/speckit-pro/unit/test-planning-approval-preflight.py`,
class `RuntimeNavigationTest`. Each records an approval, writes the variant,
regenerates the map with the shared renderer, and calls `verify` through the
request seam on the source runner and both shipped payloads.

## Known limits

- **A fuzzy linkifier may render a domain-shaped token.** A token such as
  `example.invalid/landing` is plain text under CommonMark and GitHub
  Flavored Markdown. A previewer with fuzzy linkify turned on may still show it
  as a link. Real branch names and file paths need dots and slashes, so the
  grammar keeps them. The token cannot carry a scheme, link syntax, address or
  whitespace.
- **A token can still spell words.** A value such as
  `skip-review-and-merge` is a valid branch or slice name, so it stays
  progress. It cannot carry whitespace-separated prose, a link or markup, and
  it appears only in a typed column of a generated row. A value with spaces
  stays bound to the revision.
- **Markdown table separators are projected away (`F1373-ea4f0cb9`, Low).**
  Scopes with an `omit_row` progress rule drop every table separator, so
  changing a separator's column count or alignment keeps the workflow digest.
  The review probe found no downstream tool decision that changed. This is a
  format-binding limit, not a false verified revision.
- **Numeric fields and planning file names were never projected (Info).** The
  renderer refuses markup in `review_order`, `pr_number` and `pr`. A planning
  file name outside the runtime directories is in the inventory, so adding it
  changes the digest. `test_numeric_fields_and_map_status_reject_markup` and
  the planning-directory case of
  `test_untyped_runtime_filenames_refuse_verify_on_each_host` keep both true.
- **Linux is not native macOS coverage.** The isolated runner cannot cover
  native macOS plugin CI. The orchestrator runs those host checks before
  merging.

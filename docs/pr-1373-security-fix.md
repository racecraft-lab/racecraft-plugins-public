# Generated navigation binding: PR #1373

Findings `F1373-a7ea4f86` and `R1373-0f084266`: generated navigation injection.

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
letters, digits and `. + - /`, or `PR#<integer>`. Underscore runs are allowed
only between ASCII letters or digits (`demo_one.py` and `demo__one.py`), never
next to punctuation or token boundaries. A token has no whitespace, active
Markdown or HTML syntax, URL scheme, address, or `www.` prefix. Every other
generated line stays in the projection, so changing it changes the digest and
`verify` refuses. Typed progress (new PR rows, SHAs, branch names, statuses,
runtime file names) still keeps the recorded revision.

PRS-v2 rows must have exactly nine columns: seven scalar columns, a Scope
token list, and scalar Verification. Comma-separated tokens are progress only
in Scope. Extra table cells and comma-separated instruction words in scalar
columns remain bound, even when every individual word is otherwise a plain
token. This also closes `R1373-0f084266`, including its comma-list and cell-split
strong-emphasis variants in every v2 string field on both hosts.

The tests are in `tests/speckit-pro/unit/test-planning-approval-preflight.py`,
class `RuntimeNavigationTest`. Each records an approval, writes the variant,
regenerates the map with the shared renderer, and calls `verify` through the
request seam on the source runner and both shipped payloads.

The underscore follow-up also covers `_word_`, `__word__`, and punctuation-
adjacent delimiter runs. `RuntimeNavigationEdgesTest` checks every declared-
file position and renames a safe runtime file into single- and double-
underscore directory names under each excluded directory on all three runners.
The earlier link, image, autolink, HTML, prose, cell-split and line-split cases
remain in the same regression matrix. Numeric controls include schema v1 `pr`
and schema v2 `pr_number` and `review_order`.
`ScalarNavigationBoundaryTest` covers comma-separated instruction words in
every v2 scalar string column; the main matrix also tests extra cells made of
plain tokens and both single- and double-underscore comma lists.

The allowlist follows [GFM's emphasis rules](https://github.github.com/gfm/#emphasis-and-strong-emphasis):
intraword underscores cannot open or close emphasis. This rule belongs to the
shared planning projection; no renderer or per-host copy decides which runtime
values are exempt from approval. Regenerated host payloads carry the same code.

## Known limits

- **Punctuation-adjacent underscores require re-approval.** A legitimate path
  such as `pkg/__init__.py` can render emphasis in a generated cell or link
  label, so it stays bound even when the contributor intended a plain filename.
  Adding or changing that row requires a fresh approval. This fails closed;
  the input cannot reach an unchanged-digest false pass. Intraword names such as
  `demo_one.py` and `run_two__parts.json` still count as progress.
- **GFM is the rendering boundary.** Compatibility with other Markdown
  dialects has not been verified. A review raised intraword emphasis in a
  non-GFM renderer as a possible limit; that variant is unreachable under GFM,
  whose underscore delimiters cannot open or close inside these ASCII words.
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

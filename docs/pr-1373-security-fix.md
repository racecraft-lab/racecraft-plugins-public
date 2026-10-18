# Generated navigation binding: PR #1373

Findings `F1373-a7ea4f86` and `R1373-0f084266`: generated navigation injection.

A feature map's generated PRS and BACKLINKS bodies are rebuilt from runtime
inputs that the planning inventory excludes: `.process/prs.json` and the names
of files under `artifacts/`, `.process/` and `plan-approvals/`. The planning
projection used to drop a whole generated body whenever it matched the
renderer's output. Any text the renderer echoed was therefore outside the
approval digest, so a regenerated map could carry a link or an instruction
while `verify` still accepted the old approval.

`map_navigation` in `helpers/planning_approval.py` now retains the complete
canonical PRS block in the approval digest, for both schema versions. No PRS
column, row, list item, separator or notice is inferred to be trusted progress
from its rendered shape. This closes both comma-separated words inside a
single Scope item and instructions assembled from separate Scope items.
Scope-word lists and v1 trailing carriage returns no longer have a projection
exemption. Adding, removing or changing a PRS row requires re-approval, including ordinary
PR numbers, SHAs, branches and statuses. Existing approvals can require renewal;
never rewrite an old record to adopt the new digest.

Only BACKLINKS can omit generated rows, and only when the complete canonical
row is a relative link whose identical label and destination are bounded tokens.
The existing ASCII filename grammar excludes whitespace, active Markdown/HTML,
URL schemes, addresses, `www.` and emphasis-delimiting underscores. Other
backlinks remain digest-bound. The exemption is scoped to BACKLINKS so a PRS
value cannot impersonate even a syntactically safe backlink.

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
`ScopeNavigationBindingTest.test_each_scope_item_and_split_instruction_refuse_on_each_host`
records a safe approval and checks comma-separated prose at every list position
and the same instruction split into separate items on all three runners.
`ScalarNavigationBoundaryTest` covers comma-separated instruction words in
every v2 scalar string column; the main matrix also tests extra cells made of
plain tokens and both single- and double-underscore comma lists.
`AdversarialNavigationBoundaryTest` checks a balanced cell-plus-line split
that would form two nine-cell rows if evaluated independently. It stays bound:
the canonical-block comparison requires each renderer record to match one
physical line, so an embedded newline makes that comparison fail before any
line can be projected away.

The BACKLINKS allowlist follows [GFM's emphasis rules](https://github.github.com/gfm/#emphasis-and-strong-emphasis):
intraword underscores cannot open or close emphasis. This rule belongs to the
shared planning projection; no renderer or per-host copy decides which runtime
values are exempt from approval. Regenerated host payloads carry the same code.

## Known limits

- **Low `R1373-1b7d8898`.** The `PR#-?[0-9]+` alternative in NAVIGATION_TOKEN is dead after the PRS block was bound. It only exempts a backlink to a feature-root file named PR#N; the match is whole-token and such a file is already bound by the inventory, so it cannot cause a false pass.

- **Punctuation-adjacent underscores require re-approval.** A legitimate path
  such as `pkg/__init__.py` can render emphasis in a generated cell or link
  label, so it stays bound even when the contributor intended a plain filename.
  Adding or changing that row requires a fresh approval. This fails closed;
  the input cannot reach an unchanged-digest false pass. Intraword names such as
  `demo_one.py` and `run_two__parts.json` still count as progress in BACKLINKS;
  every PRS value remains bound regardless of filename spelling.
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
- **A runtime filename can still spell a word.** Safe filenames appear as
  relative links with identical labels and destinations. A PRS value with the
  same spelling is now fully bound. Whitespace, comma-list prose and active
  markup in runtime filenames cannot reach the unchanged-digest path.
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
- **The shipped-host fixture compares its final edit with the original digest.**
  For PRS, its preceding assertion already requires the canonical update to
  change the digest; the final assertion does not independently compare that
  update with the next edit. This cannot hide the reported false pass because
  the first assertion fails under the original projection. The dedicated
  request-seam attack tests separately record, mutate, regenerate and verify
  every reported variant on the source and both hosts.
- **Each multi-PR slice changes the planning digest (Low).** Emission step 9
  in `post-implementation.md` persists the slice's PRS row and regenerates
  SPEC-MOC, so every slice PR now needs a fresh approval before `verify`
  passes again. `workflow-file-protocol.md` still calls its table "every
  post-approval progress write", although its `spec-map-navigation` row now
  says the PRS block is planning. No automated step calls `verify` today
  (`planning-approval.md`: review orchestration and admission are separate
  work), so no run halts. When an admission gate adopts `verify`, it must
  re-approve after each slice; the result fails closed, never a false pass.
- **The BACKLINKS zone guard has no behavior test (Info).** Removing
  `zone == "backlinks"` from `navigation_progress` fails only the shipped-host
  byte checks. It cannot be reached today: PRS v2 rows start with `|`, v1 rows
  contain `·`, and the index zone is always empty, so no PRS line matches the
  backlink pattern.
- **Linux is not native macOS coverage.** The isolated runner cannot cover
  native macOS plugin CI. The orchestrator runs those host checks before
  merging.

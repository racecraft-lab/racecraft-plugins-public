# PR 1375: dispatch gate coverage

Security finding **F1375-0784f4ad**, class **false-pass gate on unmarked
instructions**, remains open until Daybreak re-checks the fix commits.

## Rules and the review seam

The balanced-call parser independently requires exactly one literal
`fork_turns="none"` on every scanned `spawn_agent(` example. It rejects dynamic
arguments, expansions, duplicates, and markers borrowed from another argument,
call, or comment. File statements remain an additional structural check.

Keyword matching cannot decide whether arbitrary natural-language instructions
contradict the dispatch rule. The gate therefore also compares the complete
rendered Codex skill tree and complete generated agent TOMLs against an explicit
review inventory. It binds every file's exact UTF-8 bytes to its relative path.
There is no keyword filter, paragraph window, call-argument masking, extension
exemption, or metadata exemption in this inventory. New paths, renames,
deletions, changed whitespace, comments, and line endings require review.
Symlinks, missing roots, unreadable text, and missing or malformed inventories
fail closed. Source rendering and the shipped Codex payload use the same check.

The inventory is repository proof data; it is not shipped plugin policy. Its
shared test-library owner supplies strict reads and one complete file walker
to both validation and the repository regeneration script.
Regenerate it from source after reviewing the instruction changes:

```text
python3 scripts/refresh-release-artifacts.py
python3 scripts/refresh-codex-instruction-inventory.py
```

Commit the generated inventory with its source changes. Normal tests never
refresh it, and release-artifact regeneration never refreshes it implicitly.
Reviewers must assess source edits and the inventory diff together; refreshing
hashes is not evidence that a contradictory instruction is correct.

## Why retain complete content

The earlier whole-file pins were removed after review because they were
hand-maintained, included unrelated files, and made benign edits fail. That
removal reopened the security finding. Restricting inventory by dispatch
keywords, paragraph, extension, metadata field, or existing filename repeats
the same false-pass class: a new instruction can have none of those markers.
This version deliberately retains complete content, with a deterministic
regeneration command and exact path-set comparison. Benign wording changes
still require review and regeneration. That maintenance cost is the explicit
trade-off for rejecting unmarked instructions without claiming to understand
natural language. No redundant reviewed-excerpt mechanism remains.

The structural call scan still excludes upstream Quint trees, package lockfiles,
Python scripts under `scripts/`, and JSON schemas. The content inventory has
**no exclusions**, including those file kinds: scripts and schema descriptions
can emit text, and a renamed reference must not escape review.

## Regression evidence

The focused fault tests copy the actual rendered skills or generated agents,
verify an unmodified control passes, then inject contributor-controlled text.
The red run before the inventory change accepted 47 injected cases, including
all reported categories. Disabling the inventory check after the fix produces
124 failing checks out of 202, including every reported category; restoring it
makes the focused gate green. The call-parser fault tests continue to exercise the parser
alone so inventory rejection cannot substitute for call-argument validation.

Coverage includes existing skill paragraphs, every generated agent's developer
instructions and scalar metadata, valid-call messages, comments, explicit
conflicting values, new and renamed keyword-free files, HTML or unrelated
markers, unsupported fields, split/concatenated/nested/formatted message text,
script output, schema descriptions, path-set changes, symlinks, and missing or
malformed review evidence. The shipped Codex skill and agent copies are tested
too. See the security-fix PR comment for the exact variant-to-test mapping and
commit SHAs.

The refresh command is documented here and in the gate failure, rather than
adding this PR-specific proof inventory to the always-loaded agent contract.
Generated references were regenerated and checked; the generator produced no
reference changes for the initial test-only delta.

## Known limits

- The inventory detects unreviewed changes; it does not infer natural-language
  intent or independently approve an inventory refresh. Maintainers review both
  source changes and regenerated proof data. Arbitrary edits to the gate itself
  remain subject to repository code review.
- `prompt`, `context`, and `options` are not fields in the hosted `spawn_agent`
  contract supplied to this session. Those call forms cannot dispatch here;
  their instruction text is nevertheless covered by the inventory tests.
- Comments do not execute as call arguments, and agent descriptions guide the
  parent rather than becoming the child's developer instruction. Both remain
  covered because an agent reading them can act on their text.
- Hook-emitted context, runner/helper output, plugin-manifest text, and later
  user prompts are outside
  the skill/agent instruction seam. No current contradictory runner output was
  established by review; arbitrary executable output already lies outside this
  static instruction-file contract. This gate does not measure canary tokens.
- Linux validation does not cover macOS plugin CI or
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  The orchestrator runs those before merge. Interactive question steps were not
  exercised live.

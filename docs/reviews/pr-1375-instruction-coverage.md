# PR 1375: dispatch gate coverage

Daybreak resolved **F1375-0784f4ad**, class **false-pass gate on unmarked
instructions**, in its re-check at `f6f93a81c`.
Daybreak also resolved **F1375-a524ccf3**, class **unowned write through
inventory symlink**, in its [re-check at `982956d3`](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1375#issuecomment-6245524438),
which accounts for the fix commits and reported variants. Its
[re-check at `20a19681`](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1375#issuecomment-6245725763)
confirms the finding remains resolved.

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
shared repository policy owner supplies strict reads, one complete file walker,
and the chunked fixture format to validation and regeneration. The sorted skill
map uses sequential `skills-N` chunks of 50 entries to keep the proof fixture
readable; tests verify the reader rejects malformed chunks and the generator
reproduces the committed fixture byte for byte.
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

The persistent inventory refresh is also documented in the merge procedure in
[the agent runbook](../agent-runbook.md), which the agent contract already
requires for merges. The gate failure names the same command.
Generated references were regenerated and checked; the generator produced no
reference changes for the initial test-only delta.

## Inventory output boundary

The refresh command reuses `trusted_open_directory` to open every inventory
parent component without following links, anchored at the repository root.
It rejects an existing output symlink, including dangling links, and other
non-regular entries. It delegates to the existing `atomic_write` policy owner with a
`WriteBinding` holding that descriptor, creates a fresh exclusive temporary inode,
and atomically replaces the inventory entry using the held parent descriptor for creation,
replacement, and cleanup. It never truncates an existing inode. Write
and publication failures preserve the old inventory and remove the temporary
file. These are repository tooling changes; neither host's guidance or payload
changes, and release regeneration produces no payload changes.

The refresh entry-point tests cover:

| Variant | Test in `test-codex-spawn-fork-turns.py` |
| --- | --- |
| Existing or dangling output symlink, absolute or relative | `test_refresh_rejects_inventory_symlink_forms` |
| Every parent position, absolute and relative symlinks | `test_refresh_rejects_every_linked_inventory_parent` |
| Hard-linked output preserves its other name | `test_refresh_replaces_hard_link_without_truncating_target` |
| Parent rename and replacement with a directory or symlink during serialization | `test_refresh_parent_swap_cannot_redirect_write` |
| Parent swap immediately before file creation | `test_refresh_parent_swap_before_creation_cannot_redirect_write` |
| Output swapped to an absolute/relative, existing/dangling link during serialization | `test_refresh_rejects_file_swap_without_following_link` |
| Temporary-name symlink collision | `test_refresh_failures_preserve_inventory_and_clean_temporary` (`temporary collision` subtest) |
| Temporary write/publication failure and temporary cleanup | `test_refresh_failures_preserve_inventory_and_clean_temporary` (`write` and `publication` subtests) |

The initial red run accepted every reported category (207/222 checks passed;
15 failed). The expanded suite is also tested against the pre-fix writer to
prove the additional redirect controls fail without the fix. Exact final
counts and full fix SHAs are recorded in the security-fix PR comment.

## Main-merge CI recovery

The merge at `ff5129ef` brought in main's changes to the autopilot
`phase-execution.md` and `stop-policy.md` references without refreshing their
instruction inventory. Both Linux heavy-preflight artifacts and the PR test
job report the same layer-4 inventory mismatch; every other heavy-preflight
entry point passed. This is deterministic proof-data drift, not a flake.

The focused spawn/inventory suite reproduced the failure through the isolated
Linux runner (192/227 passed). After reviewing the merged reference diff and
running `python3 scripts/refresh-codex-instruction-inventory.py`, only those two
skill hashes changed. The identical focused suite then passed 230/230.
Release regeneration reported no changes. The inventory remains an explicit
review step; validation does not refresh its own expected evidence.

## Known limits

- Earlier non-blocking review observations remain accepted: the structural-only
  `assert_skill_rejected` helper has no independent accept control (the inventory
  fault helper does); the call scanner restates the vendored-root list; and the
  inventory merge procedure lives in the required agent runbook rather than the
  root contract's generated-artifact table. None causes a demonstrated reachable
  false pass in this recovery, which changes only two inventory hashes and this
  note. The temporary-name collision assertion also accepts any `OSError`, and
  the held-parent docstring uses "unlinked" to mean "not a symlink". These test
  precision, duplication, and wording observations are retained rather than
  reopening the previously reviewed implementation.

- Git cannot preserve hard-link identity in a checkout; that variant requires
  local filesystem control. Parent swaps and renames during refresh likewise
  require concurrent local write control. Tests still verify that existing
  hard-link targets and replacement parent targets are not overwritten. A
  locally controlled actor can move the held directory itself; descriptors keep
  operations bound to that original directory rather than following its new
  replacement, but cannot prevent the actor moving it or undoing the output.
- Descriptor-safe refresh requires the existing POSIX directory-open support;
  unsupported platforms fail closed rather than fall back to path-based writes.
- The shared atomic writer removes its temporary-name entry on a creation
  collision without following the entry. The collision test forces a fixed
  random value; arranging the same collision in normal use requires predicting
  a fresh UUID-based name or concurrent local directory control. The target
  remains untouched. Preserving that colliding entry is not part of the
  inventory output contract.
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

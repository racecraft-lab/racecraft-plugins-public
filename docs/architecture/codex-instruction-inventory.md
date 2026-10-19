# Codex instruction inventory

The Codex dispatch gate checks that every `spawn_agent(` example in shipped
Codex skills and generated agents carries `fork_turns="none"`. Because no
keyword check can tell whether free text contradicts that rule, the gate also
pins the complete content of those files in a reviewed inventory. This page
explains the design. The refresh steps are in
[the agent runbook](../agent-runbook.md).

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

## Why the inventory keeps complete content

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

## Inventory output boundary

The refresh command reuses `trusted_open_directory` to open every inventory
parent component without following links, anchored at the repository root.
It rejects an existing output symlink, including dangling links, and other
non-regular entries. It delegates to the existing `atomic_write` policy owner with a
`WriteBinding` holding that descriptor, creates a fresh exclusive temporary inode,
and atomically replaces the inventory entry using the held parent descriptor for creation,
replacement, and cleanup. It never truncates an existing inode. Write
and publication failures preserve the old inventory and remove the temporary
file.

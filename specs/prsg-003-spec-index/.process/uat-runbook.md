# UAT Runbook: prsg-003-spec-index

| Field | Value |
|-------|-------|
| Spec | prsg-003-spec-index |
| Branch | prsg-003-spec-index |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-07T03:26:07Z |



## Env Setup

This change is a shell script (plus its tests) — there is no build step, no
compiler, and no package manager to install. You only need `bash` and `jq`, which
the project already requires.

To get a working copy, check out this branch (`prsg-003-spec-index`) in a clone of
the repository. Two working directories matter as you walk the steps below, so note
the difference:

- **To run the automated checks**, change into the `speckit-pro/` directory and run
  `bash tests/run-all.sh`. That runs the fast, deterministic check suite (the same
  one CI runs), including the two checks that confirm this feature: one that proves
  re-running the generator changes nothing, and one that exercises the generator's
  logic directly.
- **To run the generator by hand** (which the story steps ask you to do), stay at
  the repository root and run
  `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` with
  the options shown in each step.

You do not need network access for any step — the generator reads only committed
files in the repository and never contacts GitHub or any other service.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Trustworthy generated navigation zones (Priority: P1)

Each spec folder has a "map" file named `SPEC-MOC.md` that links to the spec's
other documents. This change adds a generator that rebuilds three clearly-marked
sections inside that map file — a roadmap index, a list of merged pull requests,
and a "backlinks" list of the spec's own files — so the map can never quietly drift
out of date. Each section sits between an invisible start/end comment marker, and
the generator always rewrites the whole section between those markers (never a
partial edit), because a half-updated list is exactly the problem being fixed. If a
map is ever missing these sections entirely — for example a brand-new spec — the
generator inserts the empty sections at the right spot automatically before filling
them in.

1. Open the file `specs/prsg-003-spec-index/SPEC-MOC.md` in a text editor.
   **Expect:** near the bottom you see three pairs of HTML comment markers labeled
   `GENERATED:INDEX`, `GENERATED:PRS`, and `GENERATED:BACKLINKS`. The INDEX and PRS
   pairs sit on back-to-back lines with nothing between them (those sections are
   intentionally empty for now). The BACKLINKS pair has a bullet list between it,
   one line per file in this spec — for example `- [spec.md](spec.md)`,
   `- [plan.md](plan.md)`, `- [tasks.md](tasks.md)`, and so on.
2. Read down that backlinks bullet list and confirm the order is stable and
   sensible, not random: the spec comes first, then the plan, then tasks, then the
   data model, then research, then the contracts, then the checklists. **Expect:**
   the same fixed order every time, so the list does not jump around depending on
   how files happen to be stored on disk.
3. Open the equivalent map file for the neighbouring spec,
   `specs/prsg-002-moc-templates/SPEC-MOC.md`. **Expect:** it has the same three
   marked sections, and its backlinks list points at *that* spec's own files. This
   shows the generator produces real content for the repository's actual specs, not
   just for test fixtures.
4. From the repository root, run the generator once in its normal (write) mode:
   `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`.
   Then run `git status`. **Expect:** the command finishes without an error. If the
   committed maps were already up to date, `git status` shows no changes to any
   `SPEC-MOC.md` file.
5. Run the exact same generator command a second time, then run
   `git diff specs/prsg-002-moc-templates/SPEC-MOC.md specs/prsg-003-spec-index/SPEC-MOC.md`.
   **Expect:** an empty diff — running it again changed nothing. Rebuilding from the
   same files always produces an identical result, which is what lets the project
   trust the maps.
6. (Optional, to see the rebuild work) In `specs/prsg-003-spec-index/SPEC-MOC.md`,
   delete one of the backlinks bullet lines between the BACKLINKS markers and save.
   Run the generator command from step 4 again, then reopen the file. **Expect:**
   the line you deleted is back — the generator rebuilt the whole section from the
   files that actually exist.

- [ ] The three marked sections are present and correct, the backlinks list is in a
  stable order and points at real files for both specs, and re-running the generator
  produces no change.

<a id="us-2"></a>
### User Story 2 - Staleness is caught read-only; freshness is enforced at phase gates (Priority: P1)

A maintainer needs to trust that the committed maps match the current files. The
generator has a read-only "check" mode that rebuilds the sections in memory,
compares them to what is committed, and reports whether anything has drifted —
without ever writing to disk. It reports one of three plain outcomes: `0` (current),
`1` (stale — the maps need a refresh), or `2` (error — something was malformed).

1. From the repository root, run the generator in check mode and print its result:
   `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check; echo "exit: $?"`.
   **Expect:** it prints either `exit: 0` (the committed maps already match a fresh
   rebuild) or `exit: 1` (a map has drifted and needs a refresh); when it reports a
   stale map, the message names which one. Either way, run `git status` and confirm
   **no file was modified** — check mode never writes anything, even when it finds a
   stale map.
2. Bring the maps to a known-current state: run the normal write-mode command,
   `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`. Then
   run the check command from step 1 again. **Expect:** it now prints `exit: 0` —
   the maps match a fresh rebuild.
3. Now make a map go out of date on purpose. Add a new file inside
   `specs/prsg-003-spec-index/` (any throwaway file the backlinks list does not yet
   mention). Do **not** run the generator's write mode.
4. Run the check command from step 1 again. **Expect:** it prints `exit: 1`,
   meaning a map is stale, and the message names which map drifted and points you to
   re-run the generator to refresh it. Run `git status` once more and confirm that
   even though it reported staleness, **no file was changed** — the check stays
   strictly read-only.
5. Refresh the maps by running the write-mode command again
   (`bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`),
   then run the check command from step 1 a final time. **Expect:** it prints
   `exit: 0` again — the map is current. Remove the throwaway file you added in
   step 3 and run the generator once more to return the maps to their committed
   state.
6. You do not need to trigger this by hand, but it is part of the same promise: when
   the project's automated workflow finishes a stage of work, it rebuilds these maps
   and includes the refreshed maps in that stage's commit **only if they actually
   changed**. A stage that did not affect any map adds no extra commit. You can
   confirm this after a workflow run by looking at the commit history — a map update
   appears only when a map genuinely changed.

- [ ] Check mode reports "current" when the maps match and "stale" when a source
  file changes, writes nothing to disk in either case, and a refresh returns it to
  "current".



## FR Coverage Matrix

Each row is a promise the spec makes, matched to the specific check above that
demonstrates it.

| Promise the feature makes | Check that proves it |
|---------------------------|----------------------|
| Every one of a spec's own files is reachable from its map | Story 1, steps 1 and 3 (the backlinks list points at each file, for both specs) |
| The lists appear in a stable, predictable order regardless of disk layout | Story 1, step 2 |
| The generator produces real content for the repository's actual specs, not just test data | Story 1, step 3 (both `prsg-002` and `prsg-003` maps) |
| Re-running the generator with no source change leaves the maps byte-for-byte identical | Story 1, step 5 |
| The generator rebuilds a whole section rather than patching it partially | Story 1, step 6 (deleted line is fully restored) |
| The read-only check reports "current" and writes nothing when the maps match | Story 2, steps 1 and 2 |
| The read-only check reports "stale" with an actionable message, and still writes nothing, when a source file changes | Story 2, step 4 |
| A refresh brings a stale map back to "current" | Story 2, step 5 |
| The automated workflow commits refreshed maps only when they actually changed | Story 2, step 6 (observed in commit history) |
| The generator works offline with no network access | Env Setup note; every Story 1 and Story 2 step runs without a network |
| A malformed map or markers fail safely without corrupting the file | Negative-Path Tests below |


## Negative-Path Tests

These confirm the generator fails safely on bad input instead of corrupting a map.
Make any edits below on a throwaway copy or undo them afterward (`git checkout` the
file) so you return the repository to its committed state.

1. **Break a section marker.** In `specs/prsg-003-spec-index/SPEC-MOC.md`, delete
   just the `GENERATED:BACKLINKS:END` line (leaving the START with no matching END)
   and save. Run the check command
   (`bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check; echo "exit: $?"`).
   **Expect:** it prints `exit: 2` (error) and the message names the offending file.
   `git status` shows only your own edit to that file — the generator added nothing
   of its own; a broken marker is refused, never written through.
2. **Feed it a malformed pull-requests file.** Create the file
   `specs/prsg-003-spec-index/.process/prs.json` containing obviously broken JSON
   (for example just the text `{ broken`). Run the generator in its normal write
   mode. **Expect:** it stops with `exit: 2` and an actionable message naming the
   file, and it does **not** half-write or corrupt the map note. (Delete the file
   afterward.)
3. **Provide no pull-requests file at all (the normal case today).** With no
   `prs.json` present, open `specs/prsg-003-spec-index/SPEC-MOC.md`. **Expect:** the
   PR section between its markers is simply empty — an empty file is treated as
   "nothing to list," not as an error. This is different from the malformed case in
   step 2, which is a real failure.
4. **Confirm an unmarked spec is left alone.** A spec folder whose map file has no
   version marker is intentionally out of scope. **Expect:** running the generator
   never modifies such a folder — it is skipped silently, leaving those files
   untouched.
5. **Confirm the roadmap index stays empty here.** The INDEX section is built but
   intentionally dormant in this repository until a later change supplies its home
   document. **Expect:** the INDEX markers stay empty on every run; this is by
   design, not a missing feature.
6. **A genuine internal failure is never disguised as "just stale."** You cannot
   force this by hand, but it is part of the contract: if the generator hits an
   unexpected internal problem mid-run, it reports an error (`exit: 2`), never the
   benign "stale" result (`exit: 1`). That distinction matters because the status
   dashboard and the automated workflow react differently to a real error than to a
   map that merely needs refreshing.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

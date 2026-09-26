# Quickstart Validation Guide: HRNS-015

This is an executable acceptance run guide for the four planned slices. The repair is not implemented at Plan time; the named failing-first fixtures are created during Tasks/Implement. Record each fixture's pre-fix failure and post-fix pass in the slice PR packet. Run commands from the repository root of the active HRNS-015 worktree.

## Prerequisites

- Python 3.11+, Git, the repository's existing SpecKit runner environment, and the host tools needed for Claude Code/Codex instruction checks.
- For docs validation in a fresh worktree, install the locked docs dependencies first: `pnpm --dir docs-site install --frozen-lockfile`.
- Use the tracked fixture tree under `tests/speckit-pro/`. Never make a test open the temporary active feature spec path at runtime. Historical text belongs under that test's own fixtures.
- Keep generated `dist/`, reference docs, and the spec index derived from source. Do not hand edit them.

## Slice A: packet and PR body

1. Run the new packet fixtures before the repair and record failures for a final release note, Phase 6.5 Verdict, packet-only untracked files, and unrelated changes.
2. After repair, run the same fixtures. Expect one optional final release-note fence, correct protected/current Verdict, zero draft editable fields, packet-only untracked success, and block on another packet, tracked modification, unrelated file, or unreadable Git status.
3. Validate the emitted feature PR body with the repository's release-note policy and exact planned title; expect pass without a skip label or manual body edit. Check both host instructions.

## Slice B: gate and index

1. Freeze and run issue #637's multi-entry, selected `infra` pragma, and missing-budget original reproductions as failing fixtures. Add selected authored-section, primary-surface, complete slice-table, aggregate, greenfield LOC-only, and malformed-row cases. Expect the requested `spec_id` alone to determine values and missing fields to block with names.
2. Run Gap/clarification fixtures covering first/later token positions, two tags on one line, visible prose, and inline/fenced/indented code. Expect all G1–G4 and count-marker paths to agree.
3. Use a tracked stale index fixture and an untracked candidate inside a tracked spec directory. Before regeneration, `--check` must fail and name the stale index path; after regeneration it passes and the untracked candidate appears nowhere. Staged additions remain eligible.
4. Check declared-command precedence per slot and `required_refactor_files` impact; absent refactor signal preserves the baseline and spike precedence.

## Slice C1: Post and teams

1. Compare the Claude and Codex Post lists to the 13-name source and the workflow template. Expect each name once and matching counts.
2. Run completion fixtures with one missing, duplicate, pending, and in-progress row in either persisted representation. Expect the new boundary rule to fail with every affected row; all 13 completed in both records pass.
3. Run structural/result fixtures for all four executor types on both hosts. Expect child result or supported stop, graceful shutdown request, no-active-child confirmation, and completed cleanup before clean completion. Unknown Codex child lifetime remains an HRNS-017 observation, not a passing substitute.

## Slice C2: feedback, scaffold, envelopes, links

1. Supply more than one review-thread page and more than one comment page within a thread. A failed page/missing cursor blocks. Verification failure, push failure, or fresh remote `headRefOid` mismatch yields zero replies/resolutions. Successful matching push permits serial reply/resolve with resolved-state readback.
2. Supply a nonempty analyst result after five minutes; expect `ran` and the findings. Separately simulate dispatch error, empty return, and an explicit continue-without-findings instruction; expect the same specific reason in the Design Concept header and operator status.
3. Execute the five named request examples on both hosts through the runner's accepted envelope; expect no malformed-request error. Do not expand this to HRNS-019's broad sweep.
4. Generate a roadmap and follow its workflow link to `.process/<SPEC-ID>-workflow.md`. Update a roadmap with a verified legacy target and expect preservation; update one with a broken target and expect repair. This reproduces issue #638.

## Repository checks

Run the smallest new fixture script while iterating, then the repository gates appropriate to changed files. The broad commands below are already part of this repository's contract:

~~~text
python3 tests/speckit-pro/run-all.py
SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json
python3 scripts/refresh-release-artifacts.py --check
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate:quality
~~~

Run the artifact `--check` only after committing generated source/output paths, because the check flags uncommitted changes under its tracked inputs. Regenerate through `python3 scripts/refresh-release-artifacts.py` and, when reference inputs changed, `pnpm --dir docs-site reference:generate` before that check. Run the repository lint, final PR-title, and release-note policy gates using the exact commands in root `AGENTS.md`. At each slice PR boundary, count actual changed production and total files, including generated outputs, and record reviewable LOC; split or rescope if the strict four-production or fewer-than-25-total limit is exceeded.

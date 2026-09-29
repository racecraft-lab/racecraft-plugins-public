Priority: major

## Summary

The Layer 6 grounding regex rejects notes the contract allows (multiple citations, local file sources), so a grounded run is scored ungrounded. The runners fail open: a missing parser fixture is skipped, a failed live capture reuses a stale transcript, and several expected.json keys have no failing unit case. The transcript scrubber keeps its own path list and leaves temp paths and emails in place.

## Evidence

- **integration-layer6-2-005** (major): GROUNDING_NOTE_RE requires a whitespace-free source and forbids semicolons or newlines inside Evidence. The contract allows a capability/source such as a local file reference and Evidence lists multiple citations. Such notes are counted as malformed, so grounding_verdict returns ungrounded (verified: a note with two semicolon-separated evidence URLs, and one citing local referenced docs, both match 0 while Capability path appears once). A fallback source can also never be grounded, because it must equal a completed tool name.
  - `tests/speckit-pro/layer6-integration/lib/transcript_helpers.py:15-17`, `tests/speckit-pro/layer6-integration/lib/transcript_helpers.py:245-262`, `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md:142`, `speckit-pro/skills/speckit-autopilot/references/grounding.md:45`
- **integration-layer6-2-010** (minor): Runner edge cases fail open. A replay fixture with no parser-fixture.jsonl is skipped with a message and the run still passes. capture_live returns False when the claude CLI is missing, the caller ignores it, and a stale transcript.jsonl from an earlier live run is asserted as if fresh. run-grounding-fixtures.py advertises --live in its usage text and receives it from run-all-fixtures.py, but ignores the mode.
  - `tests/speckit-pro/layer6-integration/lib/fixture_runner.py:81-90`, `tests/speckit-pro/layer6-integration/lib/fixture_runner.py:170-173`, `tests/speckit-pro/layer6-integration/run-grounding-fixtures.py:83-90`, `tests/speckit-pro/layer6-integration/run-dispatch-fixtures.py:47-49`
- **integration-layer6-2-011** (minor): No unit test drives a failing case through assert_dispatch_fixture for min_dispatch_count, max_dispatch_count, dispatch_order_constraints, must_dispatch_to_at_least_one_of or must_not_include_terms; only replay of the committed fixtures and return-format term cases run. Those keys could stop failing without a red test.
  - `tests/speckit-pro/unit/test-integration-runners.py:76-260`, `tests/speckit-pro/unit/test-transcript-helpers.py:31-40`
- **integration-layer6-2-008** (minor): The must_dispatch_to, forbidden-spawn, skill and term assertion blocks are written out again in run-return-format-fixtures.py and run-grounding-fixtures.py instead of reused from fixture_runner. The reducer re-implements load_events and _blocks, and the runner main() functions are near clones (the whole-repo clone scan lists them).
  - `tests/speckit-pro/layer6-integration/lib/fixture_runner.py:156-260`, `tests/speckit-pro/layer6-integration/run-return-format-fixtures.py:51-92`, `tests/speckit-pro/layer6-integration/run-grounding-fixtures.py:56-69`, `tests/speckit-pro/layer6-integration/reduce-transcript-fixture.py:25-40`, `tests/speckit-pro/layer6-integration/lib/transcript_helpers.py:20-40`
- **integration-layer6-2-009** (minor): The 25-command CLI in transcript_helpers.main has no caller besides one unit test (two commands). extract_dispatched_set, extract_assistant_text and other helpers are reachable only from that table. The module also mixes dispatch parsing with the grounding verdict.
  - `tests/speckit-pro/layer6-integration/lib/transcript_helpers.py:272-345`, `tests/speckit-pro/layer6-integration/lib/transcript_helpers.py:206-262`
- **integration-layer6-2-007** (minor): The scrubber keeps its own path and identity regex list, separate from privacy_patterns.py that the reducer uses. They diverge: scrub-transcript.py leaves Claude temp-directory paths and email addresses unchanged (verified by running it), while the README says it scrubs home, repo and temp paths.
  - `tests/speckit-pro/layer6-integration/scrub-transcript.py:52-92`, `tests/speckit-pro/layer6-integration/reduce-transcript-fixture.py:22`, `tests/speckit-pro/lib/privacy_patterns.py:15-40`
- **coach-and-formal-006** (minor): stack-uat.md cites raw evidence under operating-system temp directories that no reader can open. AGENTS.md says the privacy scan rejects macOS temp paths, but TMP_TRANSCRIPT_PATTERN only matches the Claude-specific temp prefix, so these paths pass the scan.
  - `specs/formal-001-selective-formal-methods/stack-uat.md:55`, `tests/speckit-pro/lib/privacy_patterns.py:21`

## Proposed fix

- integration-layer6-2-005: Parse the note against the documented segments (Capability path, Evidence, Confidence) with a tolerant Evidence pattern, and treat repo-local and fallback sources as their own grounded class. Add a grounding fixture for each.
- integration-layer6-2-010: Fail a fixture that lacks parser-fixture.jsonl, skip assertion when capture_live returns False, and drop --live from the grounding usage line or make run-all skip Class 4 in live mode.
- integration-layer6-2-011: Add negative unit cases for each dispatch expected.json key, using the small transcripts in test-fixtures.
- integration-layer6-2-008: Move the shared expected.json checks into fixture_runner and import load_events and _blocks from transcript_helpers in the reducer.
- integration-layer6-2-009: Delete the unused CLI commands and their table, or cut it to the tested subset. Move the grounding helpers to their own module.
- integration-layer6-2-007: Have scrub_string call redact_private_text for the shared patterns and keep only the telemetry-field replacements local.
- coach-and-formal-006: Drop the temp-directory paths from the record (the results are already summarized), and widen the privacy pattern if operating-system temp paths are meant to be rejected.

## Acceptance

- [ ] Regression tests that fail before the fix: a grounding note with two semicolon-separated citations, and one citing a local file, count as grounded.
- [ ] A fixture without parser-fixture.jsonl fails; a failed live capture fails instead of asserting a stale transcript.
- [ ] Each dispatch expected.json key has a negative unit case.
- [ ] scrub-transcript.py uses privacy_patterns.redact_private_text; a test shows temp paths and emails are scrubbed.
- [ ] stack-uat.md in specs/formal-001 no longer cites temp-directory paths.

## Related

- Overlaps files changed by the open stop-policy stack: #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.
- Depends on: class2-replay-tautology (issue number added after filing)

Found by the 2026-09 coherence audit.

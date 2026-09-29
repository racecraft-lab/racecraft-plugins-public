Priority: blocking

## Summary

Fixtures 19, 20 and 21 claim to catch per-item serial dispatch, a missing isolation setting and foreground calls. The transcript parser records only subagent_type, description and prompt, and counts dispatches across all messages. Serial dispatch across several messages, or foreground calls, passes every assertion, and fixture 21's max_dispatch_count of 6 admits the per-thread regression its README calls a defect.

## Evidence

- **integration-layer6-2-001** (blocking): Fixtures 19, 20 and 21 claim to catch per-task or per-item serial dispatch, a missing isolation setting and non-background calls, but the parser records only subagent_type, description and prompt and counts dispatches across all messages. Serial dispatch across several messages, or foreground calls, passes every assertion; fixture 21 max_dispatch_count 6 also admits the per-thread regression its README says is a defect.
  - `tests/speckit-pro/layer6-integration/lib/transcript_helpers.py:49-69`, `tests/speckit-pro/layer6-integration/lib/fixture_runner.py:231-256`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/20-consensus-multi-item-batch/README.md:22-27`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/README.md:26-28`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/21-resolve-pr-parallel-files/expected.json:14`

## Proposed fix

- integration-layer6-2-001: Record the assistant-message index, run_in_background and isolation in extract_orchestrator_dispatches. Add an expected.json key such as same_message_dispatch_groups or must_run_in_background, assert it, and tighten fixture 21 max_dispatch_count to 3. Otherwise drop the regression-net claims from the fixture READMEs and purpose strings.

## Acceptance

- [ ] extract_orchestrator_dispatches records the assistant-message index and run_in_background (and isolation where present).
- [ ] expected.json gains keys such as same_message_dispatch_groups and must_run_in_background, and fixture_runner asserts them.
- [ ] A regression test that fails before the fix: a transcript that dispatches the same tasks serially across messages, or in the foreground, fails fixtures 19 to 21.
- [ ] Fixture 21 max_dispatch_count is tightened to match its README.

## Related

- None.

Found by the 2026-09 coherence audit.

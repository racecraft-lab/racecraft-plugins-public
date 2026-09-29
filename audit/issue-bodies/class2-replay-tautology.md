Priority: blocking

## Summary

Class 2 return-format replay proves nothing about response format. reduce-transcript-fixture.py builds each synthesizer tool_result from the keywords in expected.json, and run-return-format-fixtures.py then asserts those same keywords. No change to the synthesizer can fail Class 2 replay, and must_not_contain_any can never fail.

## Evidence

- **integration-layer6-2-004** (blocking, adjusted from major in review): Class 2 replay proves nothing about response format. reduced_response builds each synthesizer tool_result from the keywords in expected.json, then run-return-format-fixtures.py checks those same keywords against it. must_not_contain_any can never fail, and a frozen fixture is edited by changing the synthesized string (the open consensus-tiebreak PR swaps HUMAN REVIEW NEEDED for ROUND_3_TIEBREAK in one line). The README still describes Class 2 as verifying cross-agent parsing.
  - `tests/speckit-pro/layer6-integration/reduce-transcript-fixture.py:51-72`, `tests/speckit-pro/layer6-integration/run-return-format-fixtures.py:94-119`, `tests/speckit-pro/layer6-integration/return-format-fixtures/05-synthesizer-keyword-security-relevant/parser-fixture.jsonl:2`, `tests/speckit-pro/layer6-integration/return-format-fixtures/04-synthesizer-keyword-only-majority/parser-fixture.jsonl:2`

## Proposed fix

- integration-layer6-2-004: Keep real (scrubbed and redacted) synthesizer response text in the reduced fixture instead of synthesizing it, or mark Class 2 replay as parser-only and move the format assertions to a live or Layer 3 check.

## Acceptance

- [ ] Reduced fixtures keep real (scrubbed and redacted) synthesizer response text, or Class 2 replay is relabeled parser-only and the format assertions move to a live or Layer 3 check.
- [ ] A regression test that fails before the fix: a reduced fixture whose response text violates expected.json fails replay.
- [ ] The Layer 6 README describes what Class 2 replay actually verifies.

## Related

- Overlaps files changed by the open stop-policy stack: #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.

Found by the 2026-09 coherence audit.

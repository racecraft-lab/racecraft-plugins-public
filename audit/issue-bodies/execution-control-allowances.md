Priority: major

## Summary

execution_control.py implements the increment-review and gate-remediation allowances twice, near verbatim, in validators, request parsers and reserve functions. The two request parsers are also asymmetric: only one rejects the other request kind, and their deferral keys differ.

## Evidence

- **brokers-and-verification-001** (major): The increment-review and gate-remediation allowances are implemented twice, near verbatim, in the validators, the request parsers and the reserve functions. The two request parsers are also asymmetric: only _gate_remediation rejects the other request kind, and the deferral keys differ (review_allowance versus remediation_allowance).
  - `speckit-pro/speckit_pro_runner/execution_control.py:413-452`, `speckit-pro/speckit_pro_runner/execution_control.py:916-931`, `speckit-pro/speckit_pro_runner/execution_control.py:1010-1025`, `speckit-pro/speckit_pro_runner/execution_control.py:1205-1233`

## Proposed fix

Open PR #852 already merges the two validators. Finish the consolidation after the stack lands.

- brokers-and-verification-001: Parameterize one allowance implementation by ledger key, marker field and round limit. PR 852 already merges the two validators into _validate_round_allowances but keeps both _reserve_* functions and both request parsers, so finish the consolidation there.

## Acceptance

- [ ] One allowance implementation parameterized by ledger key, marker field and round limit.
- [ ] A regression test that fails before the fix: the review parser rejects a remediation request, as the remediation parser already does.
- [ ] Runner trust metadata and dist/ are regenerated; both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #837, #838, #846, #847, #848, #852. Land after that stack merges.

Found by the 2026-09 coherence audit.

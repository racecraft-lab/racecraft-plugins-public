# Publication evidence fallback: PR #1363

Finding `F1363-87ef0f25`: fail-open unpushed-commit guard.

The Stop hook must reach its Git publication check unless it can establish
pending plan work or unsettled dispatches from the bound, validated ledger.
An optional ledger read failure is not evidence of unsettled work. The hook
reports that failure on stderr and continues checking commits. Strict ledger
validation for runner state writes is unchanged.

`PublicationEvidenceTests` in
`tests/speckit-pro/unit/test-workflow-guard-hook.py` covers fresh checkouts
without ignored ledgers, stale run IDs, malformed mirrors, workflow binding,
unreadable and malformed ledgers, malformed plan containers and rows, and
pending-to-settled transitions. Each publication assertion runs from both the
repository root and its nested process directory. The path checks include
renames, file and directory symlinks, dangling links, traversal, absolute paths,
and Git metadata paths. The hook never repairs or resets ledger evidence.

## Known limits

- **Pending work intentionally defers publication.** Pending/in-progress plan
  rows and reserved/running/unknown bound dispatches still defer this check.
  The regression tests also settle each case and require publication to resume.
  This is the review's Info variant, not a bypass to remove.
- **Local state is operator-controlled.** The review's Low variants require
  deliberate state alteration or local damage. Invalid optional evidence and
  plan rows now fall back to the Git check. An operator can still edit the
  entire active-state document, remove it, or change its active status; this
  advisory hook does not provide a tamper-resistant boundary against its owner.
- **Linux is not native macOS coverage.** The isolated runner cannot cover
  native macOS plugin CI or
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  The orchestrator runs those host checks before merging.

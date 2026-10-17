# Publication evidence fallback: PR #1363

Finding `F1363-87ef0f25`: fail-open unpushed-commit guard.

The Stop hook must reach its Git publication check unless it can establish
pending plan work or unsettled dispatches from the bound, validated ledger.
An optional ledger read failure is not evidence of unsettled work. The hook
reports that failure on stderr and continues checking commits. Strict ledger
validation for runner state writes is unchanged.

The publication binding, ledger, and plan test groups in
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

## Merge review notes

The Standards and Spec re-review axes found no reachable blocking defect in
this merge and cleanup. Their bounded review packets raised these Info notes;
source checks resolve the reachability questions as follows:

- **Absolute execution workflow paths never reach the mirror.**
  `execution_control._open_control` validates through `confined_path`, which
  rejects absolute paths before an applied result can reach the state mirror.
  The terminal helper's absolute-path normalization is a separate entry point.
- **Formal writes target the workflow's sibling state file.**
  `formal.lifecycle.state_path` requires the exact state filename and the same
  parent as the workflow; its `confined` path validator rejects absolute and
  escaping paths. Passing the validated value to the guarded writer preserves
  that target.
- **The apparent unused names have callers.** `UUID_PATTERN` is used by nesting
  request validation; `read_json` is used by formal state validation. The fixture
  base classes contain no test methods, and all three publication scenario
  classes are registered. The hook suite retains its 217 passing cases.
- **Nesting persistence retains main's timestamp behavior.** The nesting-only
  update does not request a run-facts refresh. Execution, formal checkpoint and
  plan-terminal writes refresh run facts as before. Extending timestamp behavior
  for nesting is outside this behavior-preserving merge.
- **The Codex prompt combines both parents' guidance.** It retains the PR's
  bounded unknown-dispatch recovery instructions and adds main's requirement to
  persist the nesting observation before planning. Requiring byte identity to
  either parent would drop the other parent's intent. Shared skill host views
  and both payloads are regenerated from their authored sources.

The merge adds a regression through the execution-control helper: a plan seen
by the guarded state reader survives the execution mirror refresh. It failed
with the stale whole-state copy and passes when only execution facts are
mutated inside the guarded update.

# PR #1400: planning drift review fixes

## Reachable findings

- **F1400-88a90e72 (Medium):** dispatched task ownership filtered authoritative planning inputs out of the manifest comparison. Removed the ownership exemption for every manifest input. Exact feature inputs, workflow and contract subtrees, project inputs, instructions, catalog inputs, path aliases, additions, removals and renames remain visible. Ordinary outputs outside the manifest still proceed.
- **R1400-0ddc406b (Medium):** corrective retry, continuation, exception and failure-class follow-up actions bypassed the planning guard. All dispatch-creating routes now check drift before admission; follow-ups cannot claim a task scope or verification kind that their recorded dispatch does not carry. The independent standards review also found ordinary review/test-fix requests falling back to unscoped run-wide correction after their claimed allowance was rejected; that fallback now checks drift before spending budget or recording work.

## Regression evidence

Both findings were reproduced through the portable `execution-control` helper before the corresponding fix. The ownership regression run failed five cases. The corrective-route run failed each of the four eligible routes, including forged verification-kind and independent-unit claims; each request had first succeeded against the unchanged approved plan in dry-run mode. The corrected routes are checked in dry-run and apply mode, including persistence and continued dispatch of the independent task.

## Known limits

- **Info (nested-reservation probe):** a proposed nested correction carrying `reservation_id` plus `review_remediation` or `test_fix` cannot reach the corrective fallback. `execution_control.py` calls `_require_new_corrective_dispatch` while parsing those fields, before `_nested_correction`, and refuses a non-null reservation. Without a remediation/unit claim the planning guard blocks the nested request after drift. This is an unreachable bypass, so no speculative runtime change was added.

- **Low (spec review):** escalation, gate-remediation and corrective follow-ups wait after drift when the planning guard cannot establish independent task-unit authority from their request/record shape. This conservatively withholds work rather than admitting changed planning authority. Independent ordinary implementation and eligible scoped review/test-fix reserves still continue; verification remains available.

- **Info (standards review):** the `Drift.dispatched_units` tuple field remains unused after removal of the ownership filter, and the `named == []` branch is unreachable because `drifted_tasks` no longer returns that value. These are inert compatibility/cleanup remnants; neither can remove drift or admit work. They remain outside the behavioral repair.

- **Info (security review):** whole-feature ownership and undispatched ownership already granted no exemption. These controls were unreachable bypasses before the fix and remain covered by regression tests.
- **Info (security review):** a dispatched task may write non-authoritative outputs without causing drift. This remains reachable for ordinary source outputs and runner-classified execution bookkeeping outside the approval manifest. A manifest input such as `quickstart.md` is authoritative even if a task owns it, so editing it now blocks remaining work.

From the self-review (`code-review` at high effort). Reachable findings were fixed in the `fix(speckit-pro): tighten planning drift after review` commit: owned planning files, missing task metadata, unscoped work and retry rungs after drift, blank-line layout, `plan_sha256` meaning, and the ADR citation. The rest:

An automated security scan then flagged three Medium items; all three were reachable and are fixed red-first in `fix(speckit-pro): narrow the owned-file exemption and hold unscoped work after drift`: the earlier owned-file exemption was narrowed, but the later F1400-88a90e72 finding showed that ownership still hid authoritative inputs; the pit-crew fix removes that exemption entirely; after drift every unscoped reserve except verification waits; and every TDD unit a request names must be in the approved plan.

- Low: a verification reserve after drift still runs even when it names no unit. It runs checks and dispatches no work from the changed plan, and blocking it would stop verification of independent work, which ADR 0013 keeps going.
- Low: the runner's metadata-only correction (a verification-verb swap on a `tasks.md` line during implement) now counts as planning drift and blocks the corrected task and its dependents. ADR 0013 rejects editorial drift exemptions, and implement admission on resume already refuses the same change with `manifest_digest`, so this keeps one rule for both. The corrected task goes to UAT instead of being built from an unapproved line.
- Low: a unit whose dispatch is still running when drift is found gets a blocked entry, and that dispatch's later completion does not clear it. The dispatch may have read the changed plan, so the unverified block is the conservative record (ADR 0012 keeps retained work visible as incomplete). Worker cancellation belongs to ADR 0014's follow-up.
- Low: a task dispatch with no approval record in a workflow that does not record planning complete does not pin. Unreachable for an admitted implement entry: admission refuses a missing record (`planning_approval.py`, `admission`: `planning approval field record`), so every admitted entry holds a record and pins. A final pre-handoff check found the earlier gate (planning complete only) skipped the pin when a status cell showed planning open under a valid record; that was fixed red-first in `fix(speckit-pro): pin the plan approval whenever a record exists`.
- Low: when the planning manifest itself cannot be built (for example `spec.md` deleted), the reserve is refused with an input error and no drift entry is written. Nothing dispatches, so it fails closed.
- Info: each reserve after the pin rebuilds the planning manifest. It is the same read admission does once per entry; no measured cost.
- Info: `TASK_LINE` is one more task-line pattern beside those in `task_definitions`, `task_partition.py` and `execution_control.py`. It lives in the owner module; merging the patterns is a separate behavior-preserving refactor.
- Info: an agent `begin-replan-epoch` after a Tasks rerun opens a fresh allowance whose changed tasks stay blocked as drift. That follows ADR 0013 ("the implement run cannot replan itself into a new approved scope"); the guidance says so.


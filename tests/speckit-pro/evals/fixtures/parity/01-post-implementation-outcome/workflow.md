# PARITY-01 Workflow

## Specification Context

| Field | Value |
|---|---|
| Spec directory | `specs/parity-01` |
| Branch | `feature` |
| Stage | implementation |
| Design interview | completed; frozen decisions are in `spec.md` |

## Workflow Overview

| Phase | Status | Evidence |
|---|---|---|
| Specify | Complete | `specs/parity-01/spec.md` |
| Clarify | Complete | no unresolved questions |
| Plan | Complete | `specs/parity-01/plan.md` |
| Checklist | Complete | no gaps |
| Tasks | Complete | `specs/parity-01/tasks.md` |
| Analyze | Complete | no findings |
| Implement | Complete | synthetic implementation already present |
| Post | Pending | execute until the first canonical blocking gate |

## Host-Native Post Contract

The activated skill must materialize its complete canonical plan in both
`workflow.md` and `autopilot-state.json`: the 12-item Claude Post list or the
14-item Codex combined Post list. It may not substitute this abbreviated task
file for the product's canonical list, truncate later entries, or mark the run
complete while `Post: Retrospective` or another canonical item remains pending.

Execute the canonical parallel group with three exclusive ordinary-subagent
tracks:

1. Doctor owns environment and prerequisite evidence.
2. Code Review independently owns `origin/main...HEAD` review evidence.
3. Verify-chain owns Verify, Verify-Tasks, and Integration Suite in that order.

Collect and consume every successful worker return before the parent updates
the checklist or begins any serial Post action. Genuine interactive Claude
teams are outside this automated case and are never claimed as its evidence.

## Launch Prerequisite

The controller stages this fixture as a clean feature commit above
`origin/main`, so the launch has a real nonempty `origin/main...HEAD` diff.
Descriptive fixture prose is never acceptable proof: use the current committed
diff and retained controller Git observation. Follow the canonical serial
ordering, including the local control-state and UAT checkpoints required to
reach a clean worktree. Generate and independently validate the initially
absent feature-local packet and packet-owned body. Use the active
`pr-packet-output` helper in dry-run then apply mode, consume fresh
`validate-pr-packet-read-only` and `validate-pr-workflow-contract` results,
checkpoint packet/body so the worktree is clean, and persist only the declared
`validate-pr-packet-write` result. Do not duplicate a schema or validator and
do not ask `generate-pr-body` to fill the packet gap. Write the report and make
the final local checkpoint immediately before the external PR-creation command.
Record manual UAT as not performed; the generated runbook is preparation, not
UAT execution.

Derive the atomicity route and any layer plan from the authoritative runner and
the staged files. Run the declared integration command through
`execute-verification`; the emission pointer must identify that actual current
runner result rather than repeat fixture prose.

## PROJECT_COMMANDS

```json
{"INTEGRATION_TEST":"python3 specs/parity-01/verify.py"}
```

## Allowed Writes

- Control state: `workflow.md` and `autopilot-state.json`.
- Product evidence: `specs/parity-01/.process/uat-runbook.md`,
  `specs/parity-01/.process/emission/verification-pointer.json`,
  dynamic runner records under `.process/verification/` and
  `.process/execution-control/`,
  `specs/parity-01/.process/pr-packets/parity-01.json`,
  `specs/parity-01/.process/pr-packets/parity-01/body.md`,
  `specs/parity-01/.process/pr-packets/parity-01/validation.json`, and
  `artifacts/post-implementation-report.md`.
- Local commits are required checkpoints and may contain only the paths above.
- Forbidden: every other product path, pushes, PR creation, PR edits, review
  mutations, and every external side effect.

## Post-Implementation Checklist

The activated skill replaces this sentence with its complete host-native
canonical checklist and truthful status/evidence. A blocking checkpoint is not
Post completion.

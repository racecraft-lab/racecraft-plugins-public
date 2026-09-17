# PARITY-01 Specification

## Frozen design decision

The automated parity gate compares Claude and Codex workflow outcomes only
after each client independently passes correctness. Genuine interactive Claude
teams are verified separately and are not evidence for this automated case.

The staged change contains two additive capabilities with disjoint source and
test paths. Alpha and Beta share no runtime state, public interface, migration,
or deployment boundary. Either capability can be reviewed and released after
the frozen specification foundation without depending on the other.

## Requirements

- Use the activated skill's full 12-item Claude or 14-item Codex canonical Post
  contract, including its native control-state updates.
- Use ordinary subagents with exclusive Doctor, Code Review, and Verify-chain
  ownership; Verify-chain preserves Verify, Verify-Tasks, Integration ordering.
- Consume all three attributed results before the parent-owned serial tail.
- Require current reviewability evidence produced from the launch workspace's
  actual diff; never accept this fixture's prose as evidence.
- Generate the initially absent packet and packet-owned body with the active
  `pr-packet-output` helper in dry-run then apply mode. Use
  `validate-pr-packet-read-only`, `validate-pr-workflow-contract`, and
  `validate-pr-packet-write` for current validation; make the required local
  clean-worktree checkpoints, but do not duplicate helper schema/logic or make
  `generate-pr-body` create packet JSON. Stop immediately before the external
  PR-creation command.
- Never perform an external PR mutation or report generated UAT preparation as
  performed manual UAT.
- Materialize the checkpoint in `artifacts/post-implementation-report.md`
  without treating that report as proof of delegation or causal ordering.
- Derive atomicity and any layer plan from the authoritative runner and the
  staged files. Fixture prose is not route or planner evidence.
- Run the declared integration command through `execute-verification` and bind
  the emission pointer to that actual current runner result.
- Permit only the control-state and product-evidence writes enumerated in
  `workflow.md`. Local commits may contain only those paths; pushes and all PR
  mutations remain forbidden.

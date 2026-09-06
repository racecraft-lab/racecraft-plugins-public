<!-- fixture-kind: deterministic-synthetic-testdata; setup input only, not executed workflow evidence. -->

# SPEC-009 Autopilot Boundary Fixture

This directory is an immutable setup input for the Autopilot clarification and
phase-boundary evaluations. The materializer must initialize a real local Git
repository, create the declared registered worktree, and copy this complete
fixture into that child worktree before execution. Keeping the workflow only in
the declared child makes relative workflow binding deterministic.

The phase artifacts, workflow, state, and history notes are intentionally
`setup_only` and `not_started`. They are not evidence that a phase, gate,
consensus round, or implementation ran. The actual run must record its own
agent/tool trace and stop at any observed gate or user-input boundary.

## Materialization contract

- Workflow: `docs/ai/specs/SPEC-009-workflow.md`
- State: `docs/ai/specs/.process/autopilot-state.json`
- Phase inputs: `phase-artifacts/`
- Git checkpoint instructions: `git-history/README.md`
- Registered worktree branch: `009-search-database`
- Required worktree relation: the declared child worktree is created and
  attached before execution
- Provider, authentication, and foreground interaction: not part of this
  setup fixture

<!-- fixture-kind: deterministic-synthetic-testdata; setup input only, not executed workflow evidence. -->

# SPEC-805 Autopilot Setup Fixture

This directory is an immutable setup input for the Autopilot prerequisite
evaluation. The materializer must initialize a disposable project, create the
declared registered Git worktree, and copy this fixture into that child
worktree before the actor runs. The workflow remains unique to that worktree.

The workflow and state below are intentionally `setup_only` and
`not_started`. They do not claim that the SpecKit CLI, project initialization,
branch, workflow, or any gate passed. The run must report observed checks from
the actual disposable project.

## Materialization contract

- Workflow: `docs/ai/specs/.process/SPEC-805-workflow.md`
- State: `docs/ai/specs/.process/autopilot-state.json`
- Registered worktree branch: `805-autopilot-fixture`
- Required worktree relation: the declared child worktree is created and
  attached before execution
- Provider, authentication, and foreground interaction: not part of this
  setup fixture

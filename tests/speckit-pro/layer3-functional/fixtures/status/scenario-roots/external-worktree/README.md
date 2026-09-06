<!-- fixture-kind: deterministic-synthetic-testdata; setup input only, not a live project snapshot. -->

# External Worktree Scenario

The materializer must create and attach a real disposable worktree outside the
project root. The workflow under `attached-worktree/` must be discoverable via
the attached Git worktree registration, not by copying it into the main root.

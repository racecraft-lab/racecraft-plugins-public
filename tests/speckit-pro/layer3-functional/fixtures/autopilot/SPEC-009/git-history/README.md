<!-- fixture-kind: deterministic-synthetic-testdata; setup input only, not Git history or execution evidence. -->

# SPEC-009 Git Checkpoint Setup

The materializer must initialize a disposable local Git repository and create
the registered `009-search-database` worktree. During execution, it must record
actual pre-state and phase checkpoints in the run evidence, including the
observed commit IDs and agent/tool traces. This directory intentionally contains
no fabricated commit IDs, completed workflow history, gate result, or provider
output.

The run must stop and report the observed condition if the worktree cannot be
registered, if a phase artifact is missing, or if a gate requires user input.

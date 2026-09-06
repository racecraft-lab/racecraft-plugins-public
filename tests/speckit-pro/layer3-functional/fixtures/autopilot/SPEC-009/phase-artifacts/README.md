<!-- fixture-kind: deterministic-synthetic-testdata; setup input only, not executed workflow evidence. -->

# SPEC-009 Phase Artifact Inputs

These small files are setup inputs for a disposable run. Each artifact is
explicitly `setup_only`; none records a completed phase, gate, or implementation
result. The runner must preserve the files as pre-state and record any changes
and agent/tool trace separately.

| Artifact | Intended phase | Initial state |
|---|---|---|
| `spec.md` | Specify | setup_only |
| `plan.md` | Plan | setup_only |
| `checklist.md` | Checklist | setup_only |
| `tasks.md` | Tasks | setup_only |
| `analysis.md` | Analyze | setup_only |

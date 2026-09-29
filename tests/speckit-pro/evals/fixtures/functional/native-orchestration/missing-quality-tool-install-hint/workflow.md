# SPEC-860 Workflow

## Quality Gates

| Slot | Status | Tool | Command | Operator answer | G0 baseline | Final |
| ---- | ------ | ---- | ------- | --------------- | ----------- | ----- |
| COMPLEXITY | populated | lizard (not installed) | `lizard {paths}` | | | |
| MUTATION | populated | mutmut (not installed) | `mutmut run` | | | |
| DEPENDENCY_RULES | populated | depcruise (not installed) | `depcruise src` | skip (repo) | | |

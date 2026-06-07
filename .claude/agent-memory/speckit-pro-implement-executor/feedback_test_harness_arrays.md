---
name: test-harness-arrays
description: speckit-pro test harness uses hardcoded arrays, not auto-discovery — new scripts/tests must be registered in two files or they silently never run
metadata:
  type: feedback
---

When adding a new shell script + Layer-4 test under `speckit-pro/`, you MUST register them in TWO hardcoded arrays or they silently do nothing:

1. `speckit-pro/tests/run-all.sh` → `layer4_scripts=( ... )` — add the new `test-<name>.sh` path, or the test never executes in the suite (no error, just absent).
2. `speckit-pro/tests/layer1-structural/validate-scripts.sh` → `SCRIPT_FILES=( ... )` — add the new script path, or its safety checks (shebang, `bash -n`, `set -euo pipefail`, `chmod +x`) never run.

**Why:** Neither harness auto-discovers files; both iterate a literal array. A new test/script that isn't in the array passes CI vacuously (it's simply not run). I hit this on PRSG-005 (estimate-spec-size).

**How to apply:** Register the test in `run-all.sh` during the RED step (needed to observe the failing run). Register the script in `validate-scripts.sh` during GREEN, AFTER the file exists, so Layer 1 stays green throughout. Add ONE line to each array — do NOT refactor them into auto-discovery (out of scope; CLAUDE.md rule 2). Fixtures for an estimator-style script live under `tests/layer4-scripts/fixtures/<script-name>/` as `<case>.args` + `<case>.json` pairs the test loops over.

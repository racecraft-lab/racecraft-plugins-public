# Quickstart: Atomicity-test router (PRSG-007)

Runnable validation scenarios that prove the classifier works end-to-end. Implementation
details live in `tasks.md` and the implementation phase; the JSON contract is in
`contracts/routing-decision.schema.json` and the change-class mapping is in `data-model.md`.

## Prerequisites

- `bash` and `jq` on `PATH` (project dependencies).
- Repo checked out; run all commands from the repo root (this worktree:
  `.worktrees/prsg-007-atomicity-router`).
- After implementation: `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`
  is executable.

## Run the classifier

```bash
# Single positional arg = the feature dir holding tasks.md/plan.md/spec.md.
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh <feature-dir>
# JSON decision on stdout; exit 0 on any completed classification.
```

## Validation scenarios (map 1:1 to the Layer-4 fixtures)

Each scenario runs the script against a fixture dir under
`tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/` and checks the decision.

1. **Additive multi-seam → `split-PR`** (SC-002, FR-004): fixture `additive-multi-seam/`
   whose `tasks.md` describes multiple independent additive capabilities. Expect
   `.route == "split-PR"`.
2. **Single additive seam → single-PR-style** (US1 AS2): fixture `single-additive-seam/`.
   Expect `.route` ∈ {`one-navigable-PR`, `single-atomic-PR`} and never `split-PR`.
3. **Hard-atomic override → `single-atomic-PR`** (SC-003, FR-007): one fixture per
   hard-atomic class (`hard-atomic-rename/`, `hard-atomic-version-pin/`,
   `hard-atomic-destructive-migration/`, `hard-atomic-mutual-exclusion/`,
   `hard-atomic-out-of-tree-contract/`), each with apparent seams. Expect
   `.route == "single-atomic-PR"` and the matching `hard-atomic:*` token in `.signals`.
4. **Destructive migration → not releasable + warning** (SC-004, FR-008): fixture
   `hard-atomic-destructive-migration/`. Expect `.releasable == false`,
   `releasability:destructive-migration` in `.signals`, and the destructive-migration
   CI-green sentence in `.warnings`.
5. **Concurrency → not releasable + warning** (SC-004, FR-008): fixture `concurrency/`.
   Expect `.releasable == false`, `releasability:concurrency` in `.signals`, and the
   concurrency CI-green sentence in `.warnings`.
6. **No releasability risk → releasable, no warning** (FR-009): any non-risk fixture.
   Expect `.releasable == true` and `.warnings == []`.
7. **Uncertain → abstain to `one-navigable-PR`** (SC-005, FR-006): an ambiguous fixture.
   Expect `.route == "one-navigable-PR"`, never `split-PR`.
8. **Modify-heavy → `one-navigable-PR`, never `branch-by-abstraction`** (SC-008, FR-001):
   fixture `modify-heavy/` (modify signals, no hard-atomic signature, no proven additive
   seams). Expect `.route == "one-navigable-PR"`, `.releasable == true`, `.warnings == []`,
   and `.route != "branch-by-abstraction"`.
9. **Out-of-scope (empty/missing tasks.md) → `out-of-scope`** (FR-003): fixture
   `out-of-scope-empty/` with no/empty `tasks.md`. Expect `.route == "out-of-scope"`,
   decided before any detector runs.
10. **Read-only** (SC-006, FR-011): after any successful run, the fixture dir is unchanged
    (the script writes no files).
11. **Error path** (SC-006, FR-012): run against a missing/unreadable dir. Expect exit 2
    and a top-level `{"error": ...}` with no `.route`.

## Dogfood self-check (FR-007a — load-bearing)

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh \
  specs/prsg-007-atomicity-router
# MUST NOT be single-atomic-PR — PRSG-007's own spec.md enumerates auth/payment/lock/mutex
# only as vocabulary, so the keyword classes (read from tasks.md+plan.md, word-boundary
# matched) must not spuriously trip the hard-atomic override.
```

## Contract validation

```bash
# Every emitted object must validate against the schema (success or error branch).
cat contracts/routing-decision.schema.json   # the stable PRSG-008 contract
```

## Full verification

```bash
# Layer 4 — the classifier's unit test (one fixture per change class + dogfood + error path):
bash tests/speckit-pro/run-all.sh --layer 4
# Layer 1 — structural validation of the new script, edited workflow template, and
# edited/mirrored SKILL files (incl. validate-codex-skills.sh):
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected: both layers pass with zero failures (SC-007). The autopilot SKILL then records
the emitted decision into the workflow file's `## Atomicity Route` section after the Tasks
phase / gate G5 (FR-013) — verified via the SKILL/template/Codex edits, not the script.

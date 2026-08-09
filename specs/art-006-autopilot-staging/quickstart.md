# Quickstart: Validating Autopilot Staging

Runnable checks that prove the feature works, in the order a reviewer should run
them. Every command is repo-relative and runs from the repository root.

## Prerequisites

- Python 3.11+ on `PATH`. No package install: the repository suite needs no
  bootstrap (root `AGENTS.md`, "Worktree Preflight").
- Node ≥ 22.12 and `pnpm`, **only** for the documentation step in §6. Run
  `pnpm --dir docs-site install --frozen-lockfile` once per worktree first.
- `PYTHONDONTWRITEBYTECODE=1` on any command that imports the runner, so a
  worktree never accumulates `__pycache__`.

## 1 — Baseline before touching anything

```bash
python3 tests/speckit-pro/run-all.py
```

Expected: zero failures. Record the total test count — the pre-implement
prerequisite baseline is compared against it at the end of the run, and an
implementation-stage invocation must **preserve** an already-recorded baseline
rather than recount (FR-010a).

## 2 — Reviewability re-check (G3)

```bash
echo '{"schema_version":"1.0","request_id":"g3","helper_id":"reviewability-gate",
"operation":"reviewability-gate","mode":"read_only","inputs":{"mode_name":"setup",
"target":"specs/art-006-autopilot-staging/plan.md"}}' \
  | PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Expected: `"status":"warn"`, `"pass":true`, `"blockers":[]`,
`"primary_surfaces":["harness/adapter"]`, `reviewable_loc` 459, `total_files` 17.
Warnings on LOC and total files are the accepted position — see
[research.md §D9](./research.md#d9--reviewability-re-estimate-at-g3). A
**blocker** is a real stop.

Swap `"helper_id"`/`"operation"` for `estimate-reviewable-loc` with
`{"plan_file": "specs/art-006-autopilot-staging/plan.md"}` to see the declared
file tally directly: 2 new, 15 modified, 17 entries.

## 3 — Stage resolution, the new operation

```bash
echo '{"schema_version":"1.0","request_id":"stage","helper_id":"resolve-autopilot-stage",
"operation":"resolve-autopilot-stage","mode":"read_only","inputs":{
"workflow_file":"docs/ai/specs/.process/ART-006-workflow.md",
"autopilot_args":["--stage","plan"]}}' \
  | PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Expected `stdout.text`: an envelope with `"stage":"plan"`, `"source":"argv"`.
Field-by-field shape in
[contracts/stage-invocation.md §3](./contracts/stage-invocation.md#3--runner-operation).

Then walk the contract:

| Input | Expect |
|---|---|
| `autopilot_args: []` against a workflow with planning incomplete | `stage: "plan"`, `source: "auto-detect"`, a `basis` naming the first non-terminal phase |
| `autopilot_args: []` against a workflow with all planning phases terminal | `stage: "implement"`, `source: "auto-detect"` |
| `["--stage","implement"]` against planning-incomplete | `stage: "implement"` — explicit always beats auto-detection |
| `["--stage","planning"]` | exit 2, message naming the three accepted values |
| `["--stage","plan","--from-phase","implement"]` | exit 2, mutually-exclusive message |
| `["--stage","plan","--from-phase","tasks"]` | exit 0 — inside the range, only the starting point moves |
| workflow file with no `Stage` row | exit 0, `recorded_stage: null`. **Not an error.** |

## 4 — Both enforcement surfaces

**In-run guard**, the same invocation the autopilot issues
(`speckit-pro/skills/speckit-autopilot/SKILL.md:398`):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py \
  --workflow docs/ai/specs/.process/ART-006-workflow.md \
  --state docs/ai/specs/.process/autopilot-state.json \
  --rule status-evidence
```

Expected: exit 0, JSON report on stdout with an empty `stage_mirror_errors`.

**The check that actually proves FR-014a** — edit the state file's `stage` to a
value that differs from the workflow file's `Stage` row, re-run, and confirm the
guard now exits **1**. If it prints the error but still exits 0, the problem key
was not registered in the `status-evidence` tuple of `RULE_PROBLEM_KEYS` and the
check is inert — which is precisely the live defect this feature must not
reproduce (`validate-autopilot-phase-coverage.py:238-247` and `:4040-4042`).
Restore the file afterwards.

**Agent-independent CI gate**, tree-wide over every workflow file:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py
```

Expected: pass. It must still pass against the 56 workflow files that carry no
`Stage` row — absence is legal (spec.md:139-143).

## 5 — Unit coverage and the suite

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/speckit-pro/unit/test-autopilot-stage-resolution.py
python3 tests/speckit-pro/run-all.py --layer 4
python3 tests/speckit-pro/run-all.py
```

The direct run and the suite run must both execute the test. If the direct run
passes but the suite total does not increase, the test is missing from
`tests/speckit-pro/suite-manifest.json` — the only dispatch roster. Confirm it
appears under `layers[id=4].scripts`:

```bash
python3 - <<'PY'
import json
manifest = json.load(open("tests/speckit-pro/suite-manifest.json"))
layer = next(entry for entry in manifest["layers"] if entry["id"] == "4")
print([s["label"] for s in layer["scripts"] if "stage-resolution" in s["label"]])
PY
```

## 6 — Codex word cap, before and after

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import sys, pathlib
sys.path.insert(0, "tests/speckit-pro/lib")
import structural_helpers as sh
p = pathlib.Path("speckit-pro/codex-skills/speckit-autopilot/SKILL.md")
words = len(sh.body(p.read_text(encoding="utf-8").splitlines()).split())
print(f"body words: {words}  cap: 8000  headroom: {8000 - words}")
PY
```

Baseline on 2026-08-04: **7671 words, headroom 329**. After the three additions
(argv token, pointer sentence, Step 0.6c bullet), the measured result is **7795
and headroom 205** (the pre-implementation projection was ≈7725/≈275; the edits
cost 124 words rather than the budgeted ≈54). Use this module-level `body()` and nothing else —
a hand-rolled frontmatter regex gives a slightly different count.

Then confirm the four string-pinned sentences survived and the structural suite
is clean:

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

## 7 — Regenerate the generated artifacts, then re-verify

Editing either `SKILL.md` dirties the distribution mirrors, the installed-cache
fixtures, and the runner trust metadata. Regenerate; never hand-edit.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate     # required: a tracked .py under tests/ changed
python3 tests/speckit-pro/run-all.py
```

The refresh is idempotent — a second run on unchanged source makes no further
changes (`scripts/refresh-release-artifacts.py:22-23`) — so a non-empty `git
status` after a second run means something is still out of sync.

## 8 — End-to-end acceptance

The scenarios that decide whether the feature is actually done. Each maps to a
user story in spec.md.

**US1 — stop cleanly after planning.** Run the autopilot against a fresh workflow
file with `--stage plan`. Confirm: Analyze completes, G6.5 runs as the terminal
step, no implementation task starts, the `Stage` row reads `plan`, and the stage
boundary exists as a **commit** — not as uncommitted working-tree state. Check
`git log` for a message naming the stage boundary rather than a phase, and
confirm it stages the enumerated trio (`specs/`, the workflow file, the state
file) and never the workflow *directory*, which also holds untracked byproducts.

**US2 — resume into implementation.** From a **different working copy** and a
fresh session, run `--stage implement` against the same workflow file. Confirm:
it begins at Implement, re-runs none of the six planning phases, reads the
recorded G6.5 verdict instead of re-running the gate, preserves the recorded
test-count baseline, and reconstructs everything it needs from the workflow file
alone. A confidence-mode flag passed here must be **accepted** with an explicit
diagnostic that the gate is not run in this stage — never silently ignored, never
rejected.

**US3 — bare invocation.** Run with no stage against two workflow files, one with
planning incomplete and one complete. Each must resolve to the expected stage and
**report the choice and its basis before any phase work begins**.

**Canonical task list.** During a `--stage plan` run, confirm the task list is not
truncated: the Implement entry and every `Post:` entry are present, carry
byte-identical canonical names, and hold `skipped: <reason>` in the **status**
field with no `pending` substring in any casing. A `skipped:`-prefixed *name* is
the failure to watch for — the coverage guard matches post-implementation
checkpoints by exact name equality and would report it as missing.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Guard prints a stage mismatch but exits 0 | Problem key not in the `status-evidence` tuple | Register `stage_mirror_errors` in `RULE_PROBLEM_KEYS` |
| `test_fixture_manifests_cover_registered_helpers` fails | New operation missing from `EXPECTED_HELPERS`, the fixture manifest, or the request fixture | Add all three; the Bash-reference roster needs the no-ancestor carve-out ([research.md §D3](./research.md#d3--registering-an-operation-with-no-bash-ancestor)) |
| Layer 1 fails on 56 unrelated workflow files | The `Stage` row was made mandatory | Absence must be legal and must resolve through auto-detection |
| Codex Layer 1 word-count failure | Stage prose landed in the skill body | Move it to `references/phase-execution-codex.md`; the body keeps only the argv line and a pointer |
| `git status` dirty after a second refresh run | Source changed between runs, or a generated file was hand-edited | Re-run the refresh; never hand-edit `dist/**` or the installed-cache fixtures |

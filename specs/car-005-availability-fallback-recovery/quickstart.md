# Phase 1 Quickstart: CAR-005 Validation Guide

**Date**: 2026-07-29 | **Spec**: `specs/car-005-availability-fallback-recovery/spec.md`

How to verify each slice end-to-end. Run every command from the repository root.

---

## Prerequisites

The repository test suite needs no bootstrap — run it directly. `docs-site/` is the
only surface with dependencies, and it is needed here because both slices add a
tracked `.py` file under `tests/speckit-pro/`, which regenerates a docs reference
page.

```bash
# Once per worktree, before any docs command.
pnpm --dir docs-site install --frozen-lockfile
```

No typechecker or linter gate exists in this repository. Verification is the
Python suite plus the docs reference check — nothing else.

---

## Baseline

Confirm the tree is green before changing it, so any later failure is
attributable to this feature.

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

Expected: `1428/1428 passed` (the count on this branch at plan time; it rises as
other work lands, so treat "zero failures" as the criterion, not the number).

---

## Slice 1 — resolution-failure semantics (User Story 1)

### 1. Structural validation

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

Expected: zero failures. This layer covers manifests and plugin structure; the new
files are test-tree only, so it should be unchanged from baseline.

### 2. Script safety and unit coverage

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

This is the layer that actually exercises the feature. Expected:

- `test-route-fallback-simulation` appears in the run output and passes. If it is
  absent, the `suite-manifest.json` entry is missing — the module is then only
  runnable by hand, which fails SC-008.
- **`test-policy-control-contracts` still passes.** This is not incidental. That
  CAR-004 module enumerates every document in `contracts-claude/` and asserts each
  uses only keywords the shared engine implements
  (`test-policy-control-contracts.py:5204`). The three new schemas fall under it
  the moment they land, so a keyword mistake surfaces there rather than in the new
  module. See research D2.
- `test-unit-layout` still passes — it mechanically enforces durable naming, and
  `car` is a live spec family because this feature's directory is
  `specs/car-005-availability-fallback-recovery`. A `car-005` in any authored
  script stem, or in any test **method** name, fails here. See research D9.

### 3. Run the single new module directly while iterating

```bash
python3 tests/speckit-pro/unit/test-route-fallback-simulation.py
```

Faster than the whole layer. Use it for the inner loop, then run layer 4 before
declaring the slice done.

### 4. Regenerate the docs reference page

Required after any tracked `.py` change under `tests/speckit-pro/`.

```bash
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
```

`reference:check` must exit clean. A stale
`docs-site/src/content/docs/reference/tests.md` passes locally while failing CI's
docs validation, so do not skip it.

### 5. Full suite

```bash
python3 tests/speckit-pro/run-all.py
```

Expected: zero failures across layers 1, 4, and 5 (SC-008, constitution principle
IV).

### Slice 1 acceptance

| Check | Criterion |
| --- | --- |
| Corpus replay | all nine slice-1 cases byte-identical to their pinned report (SC-002) |
| Double-run determinism | two successive runs over identical inputs byte-identical to each other (FR-014, SC-002) |
| Roadmap parity | the resolution enum read live by JSON pointer equals the five codes the Claude roadmap pins; a missing **and** an extra member each fail (FR-017a, SC-012) |
| Divergence pinned | `capability_probe_unavailable` versus `capability_discovery_unavailable` held as test data; a silent change to either roadmap's spelling fails (FR-017b) |
| Closure of both enums | the inline negative test rejects a diagnostic whose `code` is outside **both** enums (FR-019a, SC-003) |
| Zero production files | nothing under `speckit-pro/` changed (SC-004) |
| Zero shared-contract members | `layer6-efficiency/contracts/` unchanged (SC-005) |
| No shipped agent names | zero of the twelve real agents appear in fixtures (SC-006) |

### Manual determinism spot-check

Confirm byte-identity independently of the test's own assertion:

```bash
python3 - <<'PY'
import sys, json
from pathlib import Path
root = Path("tests/speckit-pro")
for p in (root / "lib", root / "layer6-efficiency" / "lib"):
    sys.path.insert(0, str(p))
import claude_route_fallback as sim
corpus = sim.load_corpus()
bad = []
for case in corpus["cases"]:
    a = sim.serialize_report(sim.resolve(case["policy"], case["snapshot"], case["overrides"], case["policy"]["budgets"]))
    b = sim.serialize_report(sim.resolve(case["policy"], case["snapshot"], case["overrides"], case["policy"]["budgets"]))
    pinned = sim.serialize_report(case["expected_report"])
    if not (a == b == pinned):
        bad.append(case["case_id"])
print("cases:", len(corpus["cases"]), "| mismatches:", bad or "none")
PY
```

Expected: `mismatches: none`. Non-determinism from timestamps, randomness, or
dict-order dependence shows up as `a != b`; a wrong pinning shows up as
`a == b != pinned`.

---

## Slice 2 — structural rejection and recovery (User Story 2)

Stacked on slice 1 as a `gh-stack` chain. Its diff is measured against slice 1's
branch, so appended cases read as pure additions.

Same five commands as slice 1, plus these slice-specific checks.

### Additivity of the diff

```bash
git diff --stat car-005-availability-fallback-recovery-slice-1...HEAD
```

Expected: exactly **three** authored files changed — the simulator module, the
corpus, and the unit test — plus the regenerated docs reference page. If any
schema file, or `suite-manifest.json`, appears in this diff, the seam is broken
(FR-033a, FR-033b). Replace the branch name above with the actual slice-1 branch.

### Slice-1 content is untouched

```bash
git diff car-005-availability-fallback-recovery-slice-1...HEAD -- \
  tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json
```

Expected: additions only, all at the tail of `cases[]`. No slice-1 `case_id`,
input, or pinned expected report may change (FR-033b). If a slice-2 finding
requires changing slice-1 content, the fix lands on slice 1's branch and the chain
restacks — it is never absorbed into slice 2's diff.

### Slice 2 acceptance

| Check | Criterion |
| --- | --- |
| Corpus replay | all seventeen cases byte-identical to their pinned reports (SC-002) |
| Scenario coverage | every scenario SC-001 enumerates has at least one case, zero unrepresented |
| Budget cap | the budget-of-one case records exactly one attempt and never exceeds the declared cap (FR-026, SC-009) |
| Out-of-range budget | an inline fixture declaring a budget above the schema maximum **fails validation** rather than being clamped (FR-027) |
| No-safe-route is report-only | the case names the unresolved agent, every attempted route, each rejection reason, and remediation whose actions include `Roll back to the previous plugin release.` verbatim; no shipped agent file is read for mutation or written (FR-029, SC-010) |
| Helper unavailability | recorded as the structured `optional_helper` field, not a diagnostic; required-agent resolution does not fail (FR-025) |
| Override path | override recorded as effective dispatch tuple, `release_claim_eligible: false`, and the would-have-been qualified resolution recorded (FR-024) |
| No signature drift | no slice-1 function signature changed (FR-001, FR-033b) |

---

## Per-PR gate

Each slice opens its own pull request; slice 2 names slice 1 as its base.

Before marking either ready, validate the exact final title against the
release-readiness gate — the live gate requires
`<type>(<lowercase-scope>): <plain English description>`. Both PR bodies carry the
packet contents the spec's "PR Review Packet Requirements" section mandates, and
each states its position in the stacked chain.

Both slices must pass the PR-time diff-mode reviewability gate on their own diff
(SC-011). Note that the plan-phase estimator reads **0** projected LOC for this
surface — `production_files × 40` where `production_files` is 0 — so it cannot
adjudicate the split. See plan.md "Reviewability Budget".

---

## Failure triage

| Symptom | Likely cause |
| --- | --- |
| `test-policy-control-contracts` fails after adding a schema | a new schema uses a keyword outside `claude_policy_controls.SUPPORTED_KEYWORDS` (research D2) |
| `test-unit-layout` fails | a spec ID leaked into an authored script stem or a test method name (research D9) |
| `ControlContractError` mentioning `$ref` | a `$ref` left its own `#/$defs/`; the engine fails closed on cross-document references (FR-016, research D1) |
| `a != b` on double run | non-determinism — a timestamp, randomness, or dict-order dependence reached the report |
| `a == b != pinned` | the pinned expected report disagrees with the simulator; decide which is wrong before editing either |
| An FR-023 or FR-020 fixture fails **validation** instead of emitting a diagnostic | the route schema over-constrained: `resolved_model`/`effort` must stay optional and `fallback_routes` must not set `uniqueItems` (data-model.md §1) |
| CI docs validation red, local green | `reference:generate` not run or not committed |
| `test-route-fallback-simulation` missing from layer 4 output | the `suite-manifest.json` entry was not appended (SC-008) |

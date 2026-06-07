# UAT Runbook: prsg-006-reviewability-budget

| Field | Value |
|-------|-------|
| Spec | prsg-006-reviewability-budget |
| Branch | prsg-006-reviewability-budget |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-07T03:38:02Z |



## Env Setup

No build step. This PR ships two bash scripts and updates skill documentation — nothing to compile or install beyond what is already on the machine (`bash`, `jq`, and `git`).

To verify the scripts are well-formed and all unit tests pass, navigate to the `speckit-pro/` directory inside the checked-out branch and run each test layer:

```
cd speckit-pro
bash tests/run-all.sh --layer 1   # structural checks (script exists, template vocabulary, Codex parity)
bash tests/run-all.sh --layer 4   # script unit tests (estimator + gate behavior fixtures)
```

Both commands should print every suite as `PASS` and finish with a line like `speckit-pro test suite: N/N passed`. If either shows a `FAIL`, the PR is not ready to merge.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Preventive plan-phase reviewability budget (Priority: P1) `[US1]`

This story adds a new script, `estimate-reviewable-loc.sh`, that reads a plan file and
projects how large the planned work is — before a single line of code is written. The script
counts only production-code files (not documentation or test files), applies a bonus
allowance when every declared file is brand new, and reports one of three results: `pass`,
`over_budget`, or `not_estimated`.

You will paste small sample plan files into `/tmp` and run the script against them. The script
path inside the worktree is:

```
speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh
```

In the steps below, substitute the full absolute path to the worktree when running commands.
For brevity the steps write `<script>` for that path.

---

**Check 1 — within-budget pass (docs do not count)**

1. Paste this file:

   ```
   cat > /tmp/uat-plan-pass.md <<'EOF'
   ## Declared File Operations

   - NEW src/payments/handler.ts
   - NEW src/payments/model.ts
   - NEW src/payments/validation.ts
   - NEW docs/payments-guide.md
   EOF
   ```

2. Run: `<script> /tmp/uat-plan-pass.md`

3. Expected: the script prints a single JSON object and exits without error. Look for:
   - `"status":"pass"` — within budget
   - `"declared_files":{"production":3,...}` — the docs file was not counted as production
   - `"projected":120` — 3 production files × 40 lines each
   - `"greenfield":true` — every entry is `NEW`, so the budget allowance is applied
   - `"thresholds":{"warn":600,"block":1200,...}` — the allowance scaled the thresholds up from 400/800

---

**Check 2 — over-budget result (advisory, never crashes)**

1. Paste this file (20 new files plus one modified file):

   ```
   {
     printf '## Declared File Operations\n\n'
     for i in $(seq 1 20); do printf -- '- NEW src/feature/file%s.ts\n' "$i"; done
     printf -- '- MODIFIED src/feature/existing.ts\n'
   } > /tmp/uat-plan-over.md
   ```

2. Run: `<script> /tmp/uat-plan-over.md`

3. Expected:
   - `"status":"over_budget"` — 21 production files × 40 = 840, over the 800 block threshold
   - `"greenfield":false` — the modified file disqualifies the greenfield allowance
   - `"projected":840`
   - Exit code is still 0. An over-budget result is advisory: the script never exits non-zero
     for a budget verdict.

---

**Check 3 — not estimated (no declared-files block)**

1. Paste this file:

   ```
   cat > /tmp/uat-plan-none.md <<'EOF'
   # Implementation Plan

   This plan mentions src/foo.ts in prose, but has no Declared File Operations block.
   EOF
   ```

2. Run: `<script> /tmp/uat-plan-none.md`

3. Expected:
   - `"status":"not_estimated"` — the plan has no parseable block; the script does not
     record this as within-budget
   - `"projected":null`
   - `"declared_files":{"production":0,...,"total_entries":0}`
   - Exit code 0 — the run continues; an unmeasured plan is never a hard stop.

---

**Check 4 — test suites are green**

Run from the `speckit-pro/` directory:

```
bash tests/run-all.sh --layer 1
bash tests/run-all.sh --layer 4
```

Both should finish with all suites `PASS`. The Layer 4 output includes `PASS test-estimate-reviewable-loc (43/43)`.

- [ ] All four checks above confirmed.

<a id="us-2"></a>
### User Story 2 - Reworked reviewability gate: correct metrics + typed exceptions (Priority: P2) `[US2]`

This story reworks the existing `reviewability-gate.sh` script. Three behaviors change:

1. The size metric now counts production code only — documentation and test files are excluded.
2. A PR that adds only brand-new files gets a 1.5× size allowance.
3. Touching more than one area of the codebase is now a warning, not a hard stop.

It also replaces the old escape-hatch keywords with a single typed exception line:
`Reviewability-Exception: refactor` (or `infra`, or `upgrade`).

The easiest way to exercise the gate without setting up a git repository is `setup` mode, which
reads a short roadmap-style text file. The steps below use that mode. The script path is:

```
speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh
```

In the steps below, substitute the full absolute path; abbreviated as `<gate>`.

---

**Check 1 — production-only size metric (docs do not inflate the count)**

The gate's size metric now counts only production-code additions. Documentation and test files
are excluded. This is verified by the automated test suite (the Layer 4 fixture commits 100
lines of production code plus 500 lines of documentation and asserts `reviewable_loc: 100`, not
600). Confirm the suite passes:

```
cd speckit-pro && bash tests/run-all.sh --layer 4
```

Look for `PASS test-reviewability-gate (88/88)` in the output.

---

**Check 2 — within-budget pass**

1. Paste this file:

   ```
   cat > /tmp/uat-gate-pass.md <<'EOF'
   Primary surface: API
   Projected reviewable LOC: 150
   Projected production files: 3
   Projected total files: 5
   EOF
   ```

2. Run: `<gate> setup /tmp/uat-gate-pass.md`

3. Expected: the script prints JSON and exits 0. Look for:
   - `"status":"pass"`
   - `"pass":true`
   - `"warnings":[]` and `"blockers":[]`

---

**Check 3 — multi-surface is a warning, not a block**

1. Paste this file (two surfaces, all metrics within budget):

   ```
   cat > /tmp/uat-gate-multisurface.md <<'EOF'
   Primary surface: API, UI
   Projected reviewable LOC: 150
   Projected production files: 3
   Projected total files: 6
   EOF
   ```

2. Run: `<gate> setup /tmp/uat-gate-multisurface.md`

3. Expected:
   - `"status":"warn"` — touching two areas triggers a warning
   - `"pass":true` — it is still a pass (not blocked)
   - Exit code 0
   - `"primary_surface_count":2` — the surface data is preserved in the output
   - `"blockers":[]` — no blockers attributable to surface count

---

**Check 4 — typed exception pragma flips a block to a pass**

1. Paste this over-budget file with a valid exception line:

   ```
   cat > /tmp/uat-gate-exception.md <<'EOF'
   Primary surface: API, UI
   Projected reviewable LOC: 900
   Projected production files: 9
   Projected total files: 26
   Reviewability-Exception: refactor
   EOF
   ```

2. Run: `<gate> setup /tmp/uat-gate-exception.md`

3. Expected:
   - `"status":"exception"` — the block was flipped by the typed pragma
   - `"pass":true`
   - `"exception_honored":true`
   - `"exception_class":"refactor"`
   - Exit code 0

---

**Check 5 — old-style keywords no longer work**

1. Paste this file (over-budget, with an old-style escape phrase but no typed pragma):

   ```
   cat > /tmp/uat-gate-legacy.md <<'EOF'
   Primary surface: API
   Projected reviewable LOC: 900
   Projected production files: 9
   Projected total files: 26
   split exception approved
   EOF
   ```

2. Run: `<gate> setup /tmp/uat-gate-legacy.md`

3. Expected:
   - `"status":"block"` — the old phrase is not honored
   - `"exception_honored":false`
   - Exit code 1

---

**Check 6 — mis-cased pragma does not flip the block**

1. Paste this file (note `Refactor` with capital R):

   ```
   cat > /tmp/uat-gate-miscased.md <<'EOF'
   Primary surface: API
   Projected reviewable LOC: 900
   Projected production files: 9
   Projected total files: 26
   Reviewability-Exception: Refactor
   EOF
   ```

2. Run: `<gate> setup /tmp/uat-gate-miscased.md`

3. Expected:
   - `"status":"block"` — the match is case-sensitive; `Refactor` is not accepted
   - `"exception_honored":false`
   - Exit code 1

---

**Check 7 — test suites are green**

```
cd speckit-pro && bash tests/run-all.sh --layer 4
```

Look for `PASS test-reviewability-gate (88/88)`.

- [ ] All seven checks above confirmed.



## FR Coverage Matrix

Each row maps a requirement to the specific check above (or to the automated test suite) that
proves it.

| Requirement | What it guarantees | Verified by |
|-------------|-------------------|-------------|
| FR-001 | Estimator projects production-LOC from `plan.md` at plan time | US1 Check 1, 2, 3 |
| FR-002 | Same `plan.md` always produces byte-identical output (determinism) | US1 Check 4 — Layer 4 `test-estimate-reviewable-loc` T004 asserts known value AND byte-identical second run |
| FR-003 | Three-value status: `pass`, `over_budget`, `not_estimated` — unmeasured plan never recorded as within-budget | US1 Check 1 (pass), Check 2 (over_budget), Check 3 (not_estimated) |
| FR-004 | Over-budget result in autonomous run is advisory; script exits 0 | US1 Check 2 — exit code 0 confirmed |
| FR-005 | Over-budget result in interactive use surfaces to the human | Covered by plan-phase wiring in `phase-execution.md` (skill doc); not directly exercisable without a live autopilot run |
| FR-006 | Greenfield (all-new files) gets 1.5× budget allowance; detected from `NEW`/`MODIFIED` status | US1 Check 1 (greenfield true, thresholds 600/1200); US1 Check 2 (MODIFIED disqualifies, thresholds 400/800) |
| FR-007 | Estimator is a separate standalone script; keep-in-sync comment present in both scripts | US1 Check 4 — Layer 1 structural assertion confirms comment marker present in both files |
| FR-008 | Gate counts production code only; docs/tests/config excluded from LOC metric | US2 Check 1 — Layer 4 `test-reviewability-gate` production-only metric fixture |
| FR-009 | Gate applies 1.5× greenfield allowance when every changed file is new | Layer 4 `test-reviewability-gate` greenfield fixture (500 lines passes at scaled warn 600) |
| FR-010 | Multi-surface slice is a warning, not a block | US2 Check 3 — `status: warn`, `pass: true`, `blockers: []` |
| FR-011 | Typed pragma `Reviewability-Exception: <class>` flips a block; exact canonical matcher used across all three gate modes | US2 Check 4 — block flips to `status: exception` |
| FR-012 | Pragma must be on an added line of a committed Markdown file; PR description and commit messages do not count | Layer 4 `test-reviewability-gate` added-lines-only fixture (pragma on context/removed line does not flip) |
| FR-013 | Legacy three-phrase keywords (`split exception`, `transition exception`, `ratified exception`) no longer honored | US2 Check 5 — `status: block` with `split exception` prose |
| FR-014 | Roadmap template's Reviewability Contract updated to match reworked gate thresholds and typed pragma | US1+US2 Check 4 — Layer 1 structural assertion confirms template vocabulary matches gate |
| FR-015 | Plan-phase budget instruction mirrored into Codex autopilot skill surface | US1 Check 4 — Layer 1 `validate-codex-skills` passes after mirror edit |


## Negative-Path Tests

Try each of these bad or edge-case inputs and confirm the safe result described.

**Empty or unparseable plan file — should record "not estimated," never crash**

Paste a plan file with no `## Declared File Operations` block (plain prose, or an empty file)
and run the estimator against it. Expected: `"status":"not_estimated"`, `"projected":null`,
exit code 0. The run does not stop; an unmeasured plan is recorded as unmeasured, not as
passing.

**Missing or unreadable plan file — should exit with an error code, not silently pass**

Run: `estimate-reviewable-loc.sh /tmp/does-not-exist.md`

Expected: exit code 2. The script writes an error message to stderr. This is the file-level
error path, kept separate from the content-level `not_estimated` result — so an absent file
is never silently treated as a measured-and-fine plan.

**Mis-cased exception pragma — block stays a block**

Use `Reviewability-Exception: Refactor` (capital R) on an over-budget file and run
`<gate> setup` against it. Expected: `"status":"block"`, `"exception_honored":false`,
exit code 1. The match is case-sensitive; a mis-cased class is rejected (fail-safe direction
— the author can fix by lowercasing).

**Exception class outside the allowed set — block stays a block**

Try `Reviewability-Exception: hotfix` or `Reviewability-Exception: refactor,infra` on an
over-budget file. Expected: `"status":"block"`, exit code 1. Only `refactor`, `infra`, and
`upgrade` are accepted; any other class or combination is ignored.

**Old escape-hatch keywords — block stays a block**

Add `split exception`, `transition exception`, or `ratified exception` anywhere in an
over-budget file without a typed pragma line. Run `<gate> setup` against it. Expected:
`"status":"block"`, `"exception_honored":false`. These phrases were the old escape hatch and
no longer have any effect.

**Plan file listing the same path twice — counted once**

Declare the same path twice under `## Declared File Operations` (both `NEW`). The estimator
should count it once: `"declared_files":{"total_entries":1,"production":1,...}` and
`"projected":40`. No double-counting, same output on every run.

**Plan with only a mix of new and modified files — greenfield allowance does not apply**

Declare at least one `MODIFIED` entry alongside `NEW` entries. The estimator should report
`"greenfield":false` and apply the base thresholds (400/800), not the scaled ones (600/1200).

**Slice that is entirely documentation or tests — zero production LOC**

Declare only `docs/` or `tests/` paths in the estimator, or run the gate against a diff that
touches only Markdown and test files. Expected: `"declared_files":{"production":0,...}` and
`"projected":0` from the estimator; `"reviewable_loc":0` and `"status":"pass"` from the gate.
Documentation-only work counts as zero production LOC and is always within budget on the size
metric.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

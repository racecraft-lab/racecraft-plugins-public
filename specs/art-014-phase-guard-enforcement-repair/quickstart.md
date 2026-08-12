# Quickstart: Validating Phase-Guard Enforcement Repair

**Feature**: `art-014-phase-guard-enforcement-repair` | **Date**: 2026-08-12

Runnable scenarios that prove the change works end to end. Design detail lives in
[plan.md](./plan.md); the decisions behind the ambiguous parts live in
[research.md](./research.md). This file is the run guide.

## Prerequisites

- Python 3.11+. Nothing to install: the repository suite needs no bootstrap and
  the guard imports standard library only.
- Run every command from the repository root of this worktree.
- `docs-site/` is the only surface with dependencies, and only scenario 5 needs
  it.

Paths below are repository-relative. The guard is at
`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`;
the abbreviation `GUARD` stands for that path throughout.

## Scenario 1 — The negative control: a mismatched state halts the run

**Proves**: SC-001, SC-003, FR-001, FR-004, FR-007, FR-009. This is the whole
point of the specification.

Build a temporary root, write a repository marker **as a file**, put a workflow
and a state beside each other, and point the state at a different workflow.

Run the guard with the autopilot's own invocation, which is the part that
matters: `--rule status-evidence`, no commit flags, and a state carrying no
`pr_marker_plan`.

```text
python3 GUARD --workflow <supplied workflow> --state <state> --rule status-evidence
```

**Expected after the change**:

- exit code is non-zero;
- `workflow_authority_errors` in the printed report is non-empty;
- its first entry begins with `supplied workflow does not match autopilot state
  workflow_file authority` and both compared paths appear after that sentence.

**Expected before the change**, and worth running first so the contrast is
recorded: exit 0, `workflow_authority_errors` absent from the report entirely.

**If it exits 0 after the change**, check in this order: the temporary root has a
`.git` marker (without one the comparison skips under FR-006 and the test passes
vacuously); the state's `workflow_file` is repository-relative against that root
rather than absolute; and `workflow_authority_errors` is actually present in the
`status-evidence` tuple of `RULE_PROBLEM_KEYS`. The comparison running and the key
being registered are separate halves, and only the second one moves the exit code.

## Scenario 2 — The positive control: a matching state still passes

**Proves**: FR-004a and the absence of a false positive. Meaningless without
scenario 1, and scenario 1 is meaningless without it.

Rerun scenario 1 changing **exactly one value**: set the state's `workflow_file`
to the workflow actually supplied.

**Expected**: exit 0 and `workflow_authority_errors == []`.

## Scenario 3 — The skip and malformed branches

**Proves**: FR-003, FR-004c, FR-005, FR-006, FR-004d. Reuse the scenario 1
fixture and vary one input at a time.

| Vary | Expected exit | Expected report |
|---|---|---|
| remove the `workflow_file` **key** from the state | 0 | `workflow_authority_errors == []` |
| set `workflow_file` to JSON `null` | non-zero | malformed message, not the identity message |
| set `workflow_file` to `""` | non-zero | malformed message |
| set `workflow_file` to `"  "` | non-zero | malformed message, **not** the identity message |
| set `workflow_file` to a number or a list | non-zero | malformed message |
| delete the `.git` marker from the temporary root | 0 | `workflow_authority_errors == []` |
| supply a workflow that sits outside the temporary root | non-zero | `workflow file is outside the authorized repository` |

Two rows deserve attention because each one passes for the wrong reason if the
branch order is wrong. The whitespace row lands in the identity branch and prints
a blank path unless FR-005's explicit check exists. The `null` row skips silently
unless branch 1 tests key membership rather than value.

## Scenario 4 — The classification record cannot drift

**Proves**: SC-004, SC-005, FR-010, FR-010a, FR-010b, FR-011.

```text
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected**: passes, with the completeness test asserting that every key in a
**real** report carries a verdict.

**Then prove the test bites.** Add a throwaway problem key to the report without
adding it to `PROBLEM_KEY_INTENT` and rerun. The suite must fail and name the
missing key. Revert the throwaway key afterwards. A completeness test that cannot
fail is the same category of defect this specification exists to repair, so this
step is not optional.

## Scenario 5 — Full gate

**Proves**: SC-008, constitution IV.

```text
python3 tests/speckit-pro/run-all.py
python3 scripts/refresh-release-artifacts.py
```

Editing the guard restales four generated copies: `dist/claude`, `dist/codex`,
and the two installed-cache proofs. Regenerate and commit them, or CI's
`artifact-consistency` job fails the pull request.

Because a `.py` file under `tests/speckit-pro/` changes, also regenerate the
committed docs-site test reference page. That is the one command needing the
`docs-site/` install first, once per worktree.

**Expected**: zero failures, and `git status` clean after regeneration.

## Scenario 6 — Corpus regression, after-half

**Proves**: SC-002. The before-half is already measured and recorded in the
workflow file under "Corpus Regression Evidence": 54 of 54 exit 0, canary exits 0.

Reuse that harness unchanged so the two halves are comparable. Five properties
are load-bearing: the four harness conditions T025 names, plus the canary, which
T025 carries in its acceptance rather than in that four. Same harness either way;
the two artifacts only divide it differently.

1. The denominator is pinned to the baseline commit, listed with `git ls-tree`
   against that commit, so it cannot drift as new specifications land. This
   specification's own in-flight workflow is excluded by construction, because it
   is not in the baseline tree.
2. The synthesized state carries a `plan` array and a repository-relative
   `workflow_file`.
3. The state file is written **inside** the repository. The repository root is
   derived from the **state** path, so a state in a scratch directory outside the
   tree resolves no root, every comparison skips under FR-006, and all 54 files
   report a pass while proving nothing.
4. The state path is **passed in a form the root walk can resolve from**: either
   absolute, or relative with the working directory at the repository root. Record
   which. This is a second condition, not a restatement of the third. Property 3
   was necessary but not sufficient for the before-half, because the walk then
   read the state path as supplied, so a state file sitting inside the repository
   but named relatively from a subdirectory resolved no root and produced the same
   54 vacuous passes. FR-006b closes that input in the repaired guard, so the
   after-half does not depend on the spelling; the condition stays because the two
   halves must run the identical harness to be comparable.
5. The harness includes the deliberately mismatched canary.

**Expected**: 54 of 54 still exit 0, and the canary flips from 0 to 1 with a
non-empty `workflow_authority_errors`.

The canary is the run that must change. Fifty-four passes prove nothing on their
own, because a skipped comparison and a satisfied comparison both exit 0. If the
canary still exits 0, the repair did not take regardless of what the other 54
report.

Record both halves in the workflow file and the pull-request body. This proof
stays a one-time recorded run and must not be wired into the committed suite: the
process directory holds live data, an in-flight specification mid-repair can
legitimately fail the guard, and a committed corpus walk would turn CI red on
unrelated pull requests.

## Scenario 7 — Documentation truth

**Proves**: SC-007, FR-013, FR-013a, FR-013b, FR-013c. Manual review, by design:
the consensus panel resolved that no automated assertion is added.

Read each shipped statement about this guard on both platforms and confirm each
one either describes behavior the guard performs or labels itself as not yet
wired.

- The Claude `SKILL.md` authority bullet quotes the message as a **prefix**, not
  as an exact full string; names both skip conditions; and no longer claims that
  repairing the workflow file to match is the correct move for the identity
  bullet.
- The Claude-side expected-commit paragraph states the same append contract Codex
  carries **and** states plainly that the Claude flow does not yet fetch those
  values, citing ART-016.
- Both platforms' workflow-file protocol references carry the authority section,
  with the branch order and the reason behind each verdict.
- The references index descriptor is amended on both platforms, so the new
  content is reachable from the index rather than only by full-text search.
- ART-016 and ART-017 both exist in the technical roadmap. A shipped document
  naming an identifier that does not exist would repeat the defect class this
  specification repairs.

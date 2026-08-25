# Quickstart & Verification: ART-008 slice 2 — Artifact Freshness

How to prove this slice works, and which evidence answers which requirement.

## Prerequisites

A fresh worktree holds only tracked files. Three facts cover this slice:

- The repository test suite needs no bootstrap. Run
  `python3 tests/speckit-pro/run-all.py` directly.
- `docs-site/` is the only surface with dependencies. Run
  `pnpm --dir docs-site install --frozen-lockfile` once per worktree before the
  reference regeneration this slice requires.
- Define the generated-artifact merge driver once per clone:

  ```bash
  git config merge.generated.name "keep ours; regenerate after merge"
  git config merge.generated.driver "exit 0"
  ```

## Scenario 1 — The freshness verdict is reproducible offline (SC-005)

The whole decision is a pure function of one file plus one supplied object, so
it is provable without a pull request, a network, or a live sweep.

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected**: `test-artifact-freshness` passes, covering all four verdicts,
the precedence order, every undeterminable reason, the input-error shapes a
successful gather can still get wrong, and the capture-limit refusal.

The corpus also carries a `REQUIRED_CASES` guard naming one case per
behavioural obligation. Deleting cases to make a run green is a failure rather
than a smaller run.

To exercise one surface by hand:

```bash
cat > /tmp/freshness-request.json <<'JSON'
{"schema_version":"1.0","helper_id":"check-artifact-freshness",
 "operation":"check-artifact-freshness","mode":"read_only",
 "inputs":{"named_surface":"verdict",
           "workflow_file":"docs/ai/specs/.process/ART-008-slice-2-workflow.md",
           "artifacts_observation":{"ok":true,"artifacts_dir_state":"present",
             "last_artifacts_commit":"<sha>","pages":["implementation-plan"],
             "amended_commits":[]}}}
JSON
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < /tmp/freshness-request.json
```

**Expected**: `"verdict":"current"` with `"amended_rows_read":0`. Run it twice
and the helper's own payload — the `stdout` text and the `stdout_json` object —
is byte-identical. That reproducibility is SC-005.

**Compare the payload, not the whole response.** The runner's envelope wraps the
payload in execution metadata including `duration_ms`, which is wall-clock and
differs between runs, so `cmp` over two raw responses reports a difference on a
perfectly reproducible helper. Compare the payload instead:

```bash
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < /tmp/freshness-request.json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["stdout"]["text"], end="")'
```

**Falsifiable**: the request above names a workflow file carrying **no**
`Feedback Sweep Log` rows, so `amended_rows_read` is 0 and no join happens.
Supplying an ancestry record alone therefore changes nothing, and the verdict
stays `current` — the join needs a row to join *to*. To see the flip, point
`workflow_file` at a file whose log holds an `amended` row and supply a record
whose `cell` matches that row's `Commit` cell with
`"is_ancestor_of_artifacts_commit": false`. The verdict must become `stale`
with that row named in `deciding_rows`. The Layer 4 case
`verdict-stale-newer-amended-row` is that pairing, already assembled.

## Scenario 2 — The dual-anchored `Commit` read survives a piped disposition

The one place a naive implementation is silently wrong.

Build a `Feedback Sweep Log` whose `Disposition` cell carries an escaped pipe:

```text
| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | IC_x | review thread | octocat | amended | Narrowed A \| B in spec.md | e4f5a6b | 7 |
```

**Expected**: the helper reads `Commit` as `e4f5a6b`. A left-anchored
implementation reads `B in spec.md`, finds no matching ancestry record, and
returns `undeterminable` — which reads the pages as **not stale** and is the
failure this test exists to catch.

## Scenario 3 — Amended sweep leaves current pages (User Story 1, SC-001)

Run the sweep on a draft pull request carrying a comment consensus resolves to
an amendment.

**Expected, in order**: the amendment commits land; the freshness verdict reads
`stale`; the `artifact-author` dispatch runs against the amended record; the
removal set is computed and any deselected page is deleted; the pages verify on
disk; one `docs:` commit stages `specs/<feature>/artifacts/` **and nothing
else**; the push succeeds; the description refreshes; the run stops for
re-review.

**Check the commit shape directly** — this is FR-018 and FR-019, and it is what
makes the join exact:

```bash
git show --stat --name-only HEAD | grep -v '^specs/.*/artifacts/' | grep -c '/' 
```

**Expected**: `0` files outside the artifacts directory in that commit.

**Check the stop report**: it names one outcome line per page, the regeneration
commit's short sha, and the refresh result — and it does **not** carry the
slice-1 sentence about pages regenerating once slice 2 lands (SC-007).

## Scenario 4 — Clean sweep repairs a prior run's stale pages (User Story 2, SC-003)

Leave the artifacts directory at a commit older than an `amended` row's commit,
then run a sweep that handles nothing new.

**Expected**: the verdict reads `stale`; the run regenerates, refreshes, and
**proceeds into task execution without stopping** (FR-017). Repairing stale
pages never converts a proceed into a stop.

**Then run a third sweep.** Expected: the verdict reads `current`, no
regeneration happens, and the freshness contribution to the report is a single
line naming the commit the pages are current as of (FR-026, SC-006). Recovery
takes exactly one subsequent run and is never repeated.

## Scenario 5 — Nothing blocks the run (SC-004)

Force a whole-set generation failure (an unreadable template, or an author
dispatch that returns nothing).

**Expected**: the run carries a whole-set gap, still runs the description
refresh (FR-037), still lands the regeneration commit if it has content, and
still reaches its stop-or-proceed decision unchanged. Every failed page appears
in the report with a stated reason.

**Also check the refresh-failure path** (FR-036): when the refresh fails while
regeneration succeeded, the report names that failure as its own outcome,
states that a re-run does **not** retry it because the join now reads the pages
as current, and names the manual resume path — refresh the description directly,
outside the automated sequence.

## Scenario 6 — Both platforms describe the same behavior (SC-008)

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

**Expected**: pass, including
`speckit-autopilot: excludes Claude-only runtime primitives`, which runs over
the concatenated Codex runtime documents and rejects `Agent(` among nine other
literals. The regeneration dispatch is a subagent dispatch, so the Claude prose
carries an `Agent(` block and the Codex mirror must describe the same dispatch
without it.

Also confirm the three pinned strings survive in the Codex mirror:

```bash
grep -c 'estimate-reviewable-loc\|over_budget\|not_estimated' \
  speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
```

**Expected**: a non-zero count for each; the assertions are file-wide.

Confirm the Codex skill body still fits its cap:

```bash
python3 -c "
import sys; sys.path.insert(0,'tests/speckit-pro/lib')
from structural_helpers import body as b
print(len(b(open('speckit-pro/codex-skills/speckit-autopilot/SKILL.md').read().splitlines()).split()))"
```

**Expected**: **7996**, and unchanged **by this slice** — verified with
`git diff`, which reports the file byte-identical to `main`. The figure moved
from the 7998 measured at slice 1's merge (`8db22a420`) because work that
landed on `main` between the two slices freed two words, not because this slice
spent or freed any. Headroom under the 8000-word cap is therefore **4 words**,
not 2. Re-measure rather than trusting either number: it moves whenever
anything else edits that file.

## Scenario 7 — The generated-artifact contract is discharged

Any change to shipped plugin source restales the payloads, the runner trust
metadata, the installed-cache fixture copies, and the docs reference.

```bash
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
python3 tests/speckit-pro/run-all.py
```

**Expected**: the refresh is idempotent — a second run makes no further change —
and the full suite passes with zero failures. CI's `artifact-consistency` job
fails the pull request when this is skipped, so a stale artifact cannot land.

---

## Traceability

| Requirement | Changed files | Verification |
|---|---|---|
| FR-001, FR-002, FR-003 | `read_only.py` (verdict surface) | Scenario 1; Layer 4 verdict cases |
| FR-004, FR-004a | `read_only.py`, `registry.py` | Contract §Invariants; Layer 4 `ok`-literal and unmatched-record cases |
| FR-005, FR-005a, FR-006 | `read_only.py` | Layer 4 precedence and undeterminable-reason cases |
| FR-007, FR-007a, FR-008, FR-009 | `read_only.py` | Layer 4 directory-state, equality, and ancestry cases |
| FR-010, FR-011, FR-013 | `phase-execution.md` ×2 | Scenario 3 (dispatch runs against the amended record) |
| FR-012, FR-012a | `read_only.py` (removal_diff), `phase-execution.md` ×2 | Layer 4 removal-diff cases; Scenario 3 |
| FR-014 | `phase-execution.md` ×2 | Scenario 3 (description refreshes) |
| FR-015, FR-016, FR-017 | `phase-execution.md` ×2 | Scenarios 3 and 4 |
| FR-018, FR-019, FR-020 | `phase-execution.md` ×2 | Scenario 3 commit-shape check |
| FR-019a | `phase-execution.md` ×2 | Scenario 3; the failed-push leg split |
| FR-021 to FR-027 | `phase-execution.md` ×2 | Scenarios 3, 4, 5; SC-007 check |
| FR-028, FR-030, FR-032 | `read_only.py`, both `SKILL.md` measurements | Scenarios 6 and 7 |
| FR-029 | `phase-execution-codex.md` | Scenario 6 |
| FR-031 | `test-artifact-freshness.py`, `suite-manifest.json` | Scenario 1 |
| FR-033, FR-033a, FR-033b | `read_only.py` (corroborate_refresh), `phase-execution.md` ×2, `SKILL.md` | Layer 4 six-status cases; Scenario 6 |
| FR-034, FR-035 | `phase-execution.md` ×2 | Scenario 5 |
| FR-036, FR-037, FR-038 | `phase-execution.md` ×2 | Scenario 5 |
| FR-039 | `phase-execution.md` ×2 | Scenario 3 (record commit stages the workflow file alone) |
| SC-001 | all | Scenario 3 |
| SC-002, SC-006 | `phase-execution.md` ×2 | Scenario 4 (single-line report) |
| SC-003 | `read_only.py`, `phase-execution.md` ×2 | Scenario 4 |
| SC-004 | `phase-execution.md` ×2 | Scenario 5 |
| SC-005 | `read_only.py`, fixtures | Scenario 1 |
| SC-007 | `phase-execution.md` ×2 | Scenario 3 |
| SC-008 | `phase-execution-codex.md` | Scenario 6 |

## Known limits

- **The refresh failure does not self-repair.** Once the regeneration commit
  lands, FR-001's join reads the pages as current, so no later sweep re-attempts
  the refresh. FR-036 makes the report say so and name the manual path. This is
  a deliberate consequence of the join, not an oversight.
- **Per-page gaps are the operator's to act on.** Any commit touching the
  artifacts directory marks the set current on the next join, including one
  carrying only removals or only a subset of the selected pages (FR-038).
- **The four entry-gate stop statuses defer the repair.** When corroboration is
  not `match`, the sweep never runs and stale pages stay stale. The join is
  durable, so the repair happens on the first `match` run after the operator
  resolves the gate (FR-016).
- **Live end-to-end evidence needs a release.** The autopilot runs from the
  cached plugin, so an end-to-end sweep exercising this slice cannot be run
  against the working tree. The discharge path is recorded in the workflow
  file's post-implementation checklist, mirroring slice 1's own limit.

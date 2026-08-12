# Archival Report - ART-012 Implementation-Notes Capture

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no run is in flight

## Provenance

ART-012 shipped in one pull request with no follow-up fix.

- **Source spec path**: `specs/art-012-implementation-notes-capture/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/426
- **PR title**: `feat(art-012): Capture implementation notes during autopilot
  implementation`
- **Merged at**: `2026-08-11T21:51:02Z`
- **Merge commit**: `1916d8c917eea4892035daafe4c02d2558e203f3`
- **Head branch**: `art-012-implementation-notes-capture`
- **Base branch**: `main`
- **Merged by**: `fgabelmannjr`
- **Cleanup branch**: `chore/archive-art-post-merge`
- **Workflow preserved**: `docs/ai/specs/.process/ART-012-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/ART-012-design-concept.md`
- **Retrospective**: recorded inline in the preserved workflow file at its
  `### Retrospective` section, not as a separate file. ART-006's separate
  `ART-006-retrospective.md` is the exception, not the convention.
- **CI / metadata gates**: clean — 21 pass, 1 skip, **zero failures**, so this
  archive records no CI anomaly.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: the runner manifest and `.sha256` plus both `dist/`
  copies were regenerated in #426 and are covered by the payload gates;
  committed repository evidence is otherwise canonical
- **Screenshot retention**: N/A
- **Expiration risk**: none; committed source and process evidence has no
  artifact-retention dependency

## Feature Summary

ART-012 made an autopilot implementation phase leave a durable record of what
actually happened, rather than only what was planned. Every implementation
executor now reports deviations from plan, discovered edge cases, and surprises
as one combined field in its existing task summary; the orchestrator appends one
entry per task to `specs/<feature>/.process/implementation-notes.md` on the turn
that task completes, so the record survives a mid-phase interruption. A task with
nothing to report writes an explicit "None" entry, which keeps silence
distinguishable from an unreported task. ART-010's writeup and the retrospective
extension consume the record downstream.

The contract exists once and is documented on both platforms — Claude's
`phase-execution.md` and `tdd-protocol.md`, Codex's `phase-execution-codex.md` —
with a Layer 4 test asserting the two platform documents agree rather than
trusting them to.

**An operator amendment reversed a Clarify consensus.** Session 2 had narrowed
the per-task append guarantee on the strength of a claim in
`agent-teams-integration.md` that teammate results arrive batched. Platform
documentation and direct observation both show per-completion push. The operator
restored the literal per-task guarantee, which added FR-006, a sixth production
file, and a stale-claim correction in the Agent Teams reference. The amendment
is recorded in the workflow file rather than applied silently.

### What the run itself taught

**A green suite was not evidence of a correct change.** An adversarial audit run
after implementation found eight defects, five real and four introduced by the
run. Two would have shipped: the quickstart's verification command returned five
files where it asserted three, and *the record this feature produced violated the
contract this feature ships*, using compound task-ID headings. Neither was
catchable by the suite, because both artifacts sit outside what the tests assert.
The only thing that found them was a reviewer told to assume the work was wrong.

**Every significant defect was a cascade failure** — a decision made correctly in
one artifact and never propagated to the artifacts that quote it. The amendment's
190/6/9 budget landed in `spec.md` and the workflow but not in `plan.md`,
`tasks.md`, `quickstart.md` or `research.md`. The pattern is not carelessness at
the point of change; each individual edit was correct. Nothing ties an artifact
to the artifacts that quote it.

**Dogfooding the contract was not decorative.** Producing a real record under the
contract surfaced the compound-heading defect, a narrative loss when a task ran
orchestrator-direct, and a gap the contract still has no answer for: a
late-arriving fuller summary, where additive-only forbids revising an entry and a
second entry falsely implies a second attempt. That last one is left open
deliberately — the fixes cost more than the problem.

## Known Gaps Carried Forward

Three follow-ups were recorded in the run's retrospective and deliberately not
fixed in it. None has a roadmap spec yet.

1. **The Layer 6 Codex qualification corpus has no regeneration tooling.** It
   binds a sha256 chain over agent source bytes, fails with a message naming a
   digest rather than a file, and is not covered by
   `refresh-release-artifacts.py`. The next person to edit any agent definition
   hits it with no precedent to follow. This is already documented in the root
   `AGENTS.md` under *Merging Main*, which is the mitigation, not the fix.
2. **A spec-artifact consistency check would have caught three of the four
   cascades above.** The numbers in `plan.md`, `tasks.md` and `quickstart.md` are
   quotations of `spec.md`; a cheap check that they agree would have turned a
   task's manual archaeology into a gate.
3. **The record contract has no answer for a late-arriving fuller summary.** Left
   open with the reasoning recorded.

A fourth item is process rather than product: parallel writers should be
dispatched with `isolation: "worktree"`. Three agents shared one worktree, which
made every `git diff` scope check unsound and cost two executors real effort
reasoning about diffs that were not theirs.

## Canonical Shipped Artifacts

- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
  (Phase 7 lifecycle step and the append contract)
- `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md`
  (executor reporting contract, Summary Format)
- `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md`
  (stale batched-delivery claim corrected)
- `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
- `speckit-pro/agents/implement-executor.md` and
  `speckit-pro/codex-agents/implement-executor.toml`
- `dist/claude/**` and `dist/codex/**` materializations of the above
- `tests/speckit-pro/unit/test-implementation-notes-record.py`
- `tests/speckit-pro/suite-manifest.json` (one entry added)
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/corpus-manifest.json` and
  `implement-executor/fixture.json` (digest chain recomputed)
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/**` (installed-cache
  copies and their regenerated proofs)
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/ART-012-workflow.md`
- `docs/ai/specs/.process/ART-012-design-concept.md`

## Live-Reader Scan

A tree-wide scan was run before removal against the **bare directory name**, not
only the joined path, for the CAR-003 reason: references assembled from `Path`
components do not appear in joined-path searches. The scan also covered the bare
fragment `implementation-notes-capture` and the three `.process/` filenames.

One match sat outside preserved documentation and was checked by reading the
code rather than by pattern:

| Match | Verdict |
|---|---|
| `tests/speckit-pro/unit/test-implementation-notes-record.py` (5 lines) | **Documentation citations, not runtime reads.** Verified by execution path rather than by eye: the module's `TARGETS` table contains no `specs/` path, and its only two file reads are `REPO_ROOT / PLUGIN_SOURCE_DIR` (an `rglob` over `speckit-pro/`) and `REPO_ROOT / relative_path` for entries drawn from `TARGETS`. The test passes with the spec folder absent. |
| `docs/ai/specs/.process/ART-012-workflow.md` (12 lines) and `ART-012-design-concept.md` | Historical narrative in **preserved** files, correct as history. |
| `docs/ai/specs/.process/autopilot-state.json` (4 lines) | Run state; rewritten by this cleanup. |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md:79`, `html-artifacts-technical-roadmap.md:140` | Generated index entry and progress row; both regenerated or rewritten by this cleanup. |

**No live code, test, script, workflow, or docs-site reader depends on
`specs/art-012-implementation-notes-capture/`.**

The five citations in the Layer 4 test would nonetheless have been left pointing
at a deleted path, so they were shortened to the contract filenames and the
module docstring gained one sentence naming this report as the recovery route.
That is a comment-only change; no assertion, target, or read path moved.

### Why the contracts were not relocated

CAR-003 and G56R-003 both relocated spec contracts into the test tree. Neither
precedent applies here, and the distinguishing test is stated in the CAR-003
report: those specs *pointed live code at* their contracts, so archiving would
have deleted load-bearing files. Here the contracts are the documented authority
for literals the test pins, but nothing reads them at runtime. They are design
records for merged work, and they leave with the folder.

`.process/implementation-notes.md` and `.process/uat-results.md` also leave with
the folder. The first is this run's own record, and the roadmap's ratified
decision of 2026-07-28 says exactly that: *"Notes are exhaust — the raw record
lives under `.process/`; its review-visible expression is the writeup's
implementation-notes section."* The preserved workflow file annotates the same
file the same way. Every live mention of `implementation-notes.md` elsewhere in
the tree is the shipped **contract pattern** (`specs/<feature>/.process/…`), never
this instance. Nothing references either file by path.

`quickstart.md`, `research.md`, `data-model.md`, the two `contracts/` files and
the three `checklists/` files are run exhaust and were removed with the folder.
All are recoverable at the merge commit. No contract relocation was required:
every shipped surface was authored outside `specs/**`.

## Reviewability Outcome

Declared and measured agree, which is the uncommon case and worth recording.

The scaffold estimator projected 115 reviewable LOC. It was re-fed three times as
the spec grew: 155 at Clarify session 1, 162 at Analyze once FR-005 existed, and
190 on 2026-08-11 when the operator amendment added FR-006 and a sixth production
file. The final run measured 269 added production lines across six production
files, against a ratified budget of 190 LOC / 6 production files / 9 total files
with `status: ok`. The **file counts matched the declaration exactly**; the line
count ran over. The route was `one-navigable-PR` and no split was warranted.

This is the counter-example to ART-015's finding. The estimator is accurate when
fed current signals, and here it was re-fed at every amendment rather than only
at scoping time.

## Recovery Commands

```text
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/spec.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/plan.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/tasks.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/research.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/data-model.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/quickstart.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/SPEC-MOC.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/checklists/requirements.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/checklists/error-handling.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/checklists/state-management.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/.process/implementation-notes.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/.process/uat-results.md
git checkout 1916d8c917eea4892035daafe4c02d2558e203f3 -- specs/art-012-implementation-notes-capture
```

The two contract files cited by
`tests/speckit-pro/unit/test-implementation-notes-record.py` are the eighth and
ninth commands above.

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| `.specify/memory/archive-reports/2026-08-11-art-012-post-merge-hygiene.md` | This report |
| `tests/speckit-pro/unit/test-implementation-notes-record.py` | Repoint five contract citations out of the removed folder (comments only) |
| `docs/ai/specs/.process/autopilot-state.json` | Mark ART-012 completed/archived and record the applied sweep |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | Mark ART-012 complete/archived; clear the "in progress" prose |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | Frontmatter status; generated index zone regenerated |
| `specs/art-012-implementation-notes-capture/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git rm -r specs/art-012-implementation-notes-capture`
  after merge provenance and a tree-wide live-reader scan on the bare directory
  name
- **cleanupBranch**: `chore/archive-art-post-merge`
- **blockedBy**: none
- **Base-branch note**: the archive extension's cleanup gate names `main` as the
  normal safe base. This repository never commits to `main`, so the established
  local convention — used by every prior archive here — is a cleanup branch cut
  directly from the current mainline. That is what this cleanup uses.
- **Stacking note**: none. This branch is cut from `b7b80842`, the current
  mainline, and ART-002 is archived on the same branch in the same commit.
- **Downstream state**: ART-010 lists ART-012 among its dependencies but stays
  **Pending**, still blocked by ART-003 and ART-007. ART-002's completion in the
  same commit unblocks ART-007.

## Verification Commands

- `find specs -mindepth 1 -maxdepth 4 -print` audit
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit spec-index generation in apply mode, then `--check`
- tree-wide stale active-path scan on the bare directory name and fragment
- `pnpm --dir docs-site reference:generate` (a `.py` under the test tree changed)
- `python3 tests/speckit-pro/run-all.py` before and after the removal
- release-readiness title gate for the cleanup PR title
- `python3 scripts/compose-release-notes.py --validate-pr`
- `git diff --check`

## Verification Results

These checks cover the combined ART-002 and ART-012 cleanup, which lands as one
commit on one branch. They are recorded here once rather than duplicated across
both reports.

All checks ran from the cleanup branch. The full suite ran **twice** — once on
the branch before any removal, once after — so the comparison is a real
before/after rather than a single post-hoc pass.

| Check | Result |
|---|---|
| Active spec inventory | `specs/.gitkeep` only |
| `docs/ai/specs/.process/autopilot-state.json` | valid JSON; `status: completed_archived`, `archive_sweep.status: applied`, both folders listed |
| Spec-index generation (apply) | exit 0 — one write applied to `html-artifacts-roadmap-MOC.md` |
| Spec-index check after regen | exit 0 — index current |
| Generated MOC zone | both removed `SPEC-MOC.md` entries dropped; the curated epic links remain, which is correct — they point at roadmap sections, not at spec folders |
| Live-reader scan, bare directory names and fragments | every match outside the two folders is preserved documentation, a generated index, or the five comment citations that this cleanup repointed; zero live dependencies |
| Release-readiness `active-path-guard-summary` | `status=ok`, `blocking_count=0` — the repository's own stale-active-path guard agrees the removal left nothing dangling |
| `pnpm --dir docs-site reference:generate` | 7 pages generated, **zero diff** — the generated reference indexes file paths, not docstrings, so the comment-only test edit does not reach it |
| `python3 scripts/refresh-release-artifacts.py` | `Release artifacts already consistent; no changes` — no payload byte moved |
| `python3 tests/speckit-pro/run-all.py` **before** removal | 7378/7378 (L1 1447, L4 5745, L5 186) |
| `python3 tests/speckit-pro/run-all.py` **after** removal | 7378/7378 (L1 1447, L4 5745, L5 186) — unchanged, so the removal broke nothing |
| Release-readiness title gate | pass for `docs(specs): archive art-002 and art-012 post-merge state` |
| Privacy hygiene | zero absolute home paths and zero session identifiers in either report |
| `git diff --check` | clean, staged and unstaged |

Docs reference generation ran because a tracked `.py` under `tests/speckit-pro/`
changed, which the scoped test-tree rule requires. It produced no diff, and that
was confirmed by running it rather than assumed. No plugin inventory, payload
byte, or generated reference page changed.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence — workflow and design
concept both remain under `docs/ai/specs/.process/` — changes no plugin version
or runtime payload, adds no active Bash or `jq` dependency, retains all merged
source through immutable git provenance, and leaves the full
Python-authoritative suite as the completion gate.

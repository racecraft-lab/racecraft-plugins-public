# Archival Report - ART-014 Phase-Guard Enforcement Repair

## Mode

- **archiveMode**: single-feature
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no run is in flight

## Provenance

**Every date in this report is UTC**, matching the merge timestamps GitHub
records.

- **Source spec path**: `specs/art-014-phase-guard-enforcement-repair`
- **Feature branch**: `art-014-phase-guard-enforcement-repair`
- **PR URL**: <https://github.com/racecraft-lab/racecraft-plugins-public/pull/433>
- **Merge commit**: `12d8c2d48469df9293227cb2c28cf05a4847fc61`
- **Merged at**: 2026-08-13T16:36:13Z by `fgabelmannjr`
- **Tree reference**: not captured separately; the merge commit is the recovery
  anchor for every command below
- **CI run URL**:
  <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/31720702244>
- **CI outcome on the final head** (`34e8e7eb`): 20 pass, 1 skipped, 0 failures
- **Metadata gates**: `artifact-consistency=pass`, `validate-docs=pass`,
  `test (speckit-pro)=pass`, `validate-release-note=pass`,
  `validate-pr-title=pass`
- **Argos build/review URL**: not applicable; this repository runs no visual
  regression service
- **Artifact manifest**: not applicable
- **Screenshot retention**: none produced
- **Expiration risk**: none. Every artifact this report cites is either committed
  to `main` or recoverable from the merge commit

## Feature Summary

ART-014 repaired the autopilot phase guard's workflow-identity check. The guard
documented `autopilot-state.json.workflow_file` as authoritative and quoted the
failure message a mismatch produces, but that message could not be produced by
the invocation the autopilot actually issues. A run against the wrong
specification proceeded and reported pass.

Two independent defects caused it, and both are closed:

1. The identity comparison sat behind two preconditions — a `pr-marker-plan.v2`
   schema in the state and a supplied `--expected-head-commit` — that a normal
   autopilot run satisfies neither of. It now runs **unconditionally**.
2. Its findings were folded into `workflow_checkpoint_errors`, which is absent
   from the `status-evidence` tuple the autopilot always selects, so even a
   produced error could not move the exit code. Findings now report under a new
   `workflow_authority_errors` key registered in that tuple.

A third short-circuit surfaced during Clarify and is closed too. Repository-root
resolution walked the state path *as supplied*, so a state file genuinely inside
the repository resolved no root when named relatively from a subdirectory, and
the comparison silently skipped. Whether the check evaluated depended on path
spelling and working directory rather than on where the file was.

Advisory status became a recorded decision rather than an accident. A
`PROBLEM_KEY_INTENT` map classifies all 21 emitted problem keys under a closed
three-value vocabulary, enforced by a test that derives the key set from a real
report and fails in both directions.

Scale: 3 user stories, 24 functional requirements, SC-001 through SC-008,
27 of 27 tasks complete. Six authored files, five of them production. The
repository suite moved from a 7378 baseline to **7396**.

### What the run itself taught

The measurement that carries the feature is a **canary**, not a pass rate. A
skipped comparison and a satisfied comparison both report no error and both exit
zero, so 54 green corpus files proved nothing on their own. Only the
deliberately mismatched canary flipping from exit 0 to exit 1 established that
the repair took.

That principle then found four more defects downstream, three of them in the
feature's own paperwork, none of which a green suite or green CI could see:

- The corpus evidence claimed present-and-empty separates a satisfied comparison
  from a skipped one. It does not: the repaired guard writes the key
  unconditionally, so a skip reports present-and-empty too. Presence separates
  repaired code from unrepaired code, where the key is absent entirely.
- Both protocol references said "five branches" with "both skips" after a review
  fix had added a third skip.
- A malformed roadmap row dropped ART-017's blocking dependency into a cell that
  GitHub-flavored Markdown discards, leaving ART-017 displayed as ready to start.
- Quickstart scenario 4 promised the suite would name a missing key, but
  `run_counted` builds its result with `stream=None` and `run-all.py` prints only
  counts, so neither documented command can emit it.

All four were fixed before merge, in `34e8e7eb`.

## Known Gaps Carried Forward

Each is recorded, and three now have roadmap entries opened by this feature.

- **ART-016** — the Claude flow does not fetch live pull-request commit
  authority. The shipped Claude `SKILL.md` states the gap and names ART-016.
- **ART-017** — three problem keys are advisory by accident rather than by
  decision. ART-014 records the verdicts; ART-017 arms them. **Unblocked by this
  merge.**
- **ART-018** — three governance matchers report clean on input they should
  catch: `validate-gate` counts the bare `[NEEDS CLARIFICATION]` literal while
  the spec template prescribes the colon form, `count-markers` counts a literal
  `[Gap]`, and `estimate-reviewable-loc` scores every Python file in this
  repository as non-production.
- **No roadmap entry**: the `--rule` selection still bypasses the newly armed
  key, accepted because it is documented in three first-party places predating
  this change and 12 of 20 existing keys already carried it. The authority
  sentence is not pinned by a test in either protocol reference; consensus
  settled NO-ASSERT. The suite library suppresses child failure output, which is
  inherited XPLAT-010 behavior shared by the whole suite rather than anything
  this feature introduced.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by this cleanup:

- `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
  — the guard, carrying `_workflow_authority_errors`, the widened
  `_authorized_workflow_text` three-tuple, the `RULE_PROBLEM_KEYS` registration,
  `PROBLEM_KEY_INTENT`, and the `_repository_root` resolution fix
- `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py` — 35 tests
- `speckit-pro/skills/speckit-autopilot/SKILL.md` and its Codex mirror
- `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md` and
  its Codex mirror — the `workflow_file` state-authority section
- Generated payload copies under `dist/claude`, `dist/codex`, and the
  installed-cache proofs, all regenerated from source

Historical evidence stays under `docs/ai/specs/.process/`:
`ART-014-design-concept.md`, `ART-014-workflow.md`, and
`ART-014-retrospective.md`.

## Live-Reader Scan

The scan ran on the **bare directory name**, `art-014-phase-guard-enforcement-repair`,
rather than on joined paths, because a path assembled from `Path` components does
not appear in a joined-path search. Four files matched outside the folder itself:

| File | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/ART-014-design-concept.md` | `slug:` frontmatter value | none; the slug is an identifier, not a path |
| `docs/ai/specs/.process/ART-014-workflow.md` | prose citations of the branch and of artifact paths | none; the preserved record describes the run as it was |
| `docs/ai/specs/.process/autopilot-state.json` | machine-written `feature_dir`, `branch`, sweep invocation | status and `archived_at` updated; paths left as the historical record |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | a live backlink into `specs/…/SPEC-MOC.md` | **regenerated** by the spec index, never hand-edited |

Separately, `ART-014` appears by **spec ID** in the guard's own
`PROBLEM_KEY_INTENT` reason strings. Those cite the identifier, not the
directory, and are unaffected.

### Why the quickstart was not relocated

The ART-002 precedent moved that feature's acceptance runbook into
`docs/ai/specs/.process/` rather than deleting it. ART-014 fails both prongs of
that test, so its `quickstart.md` leaves with the folder.

- **No dangling pointer.** ART-002's preserved workflow cited its runbook *by
  path*, twice, so deletion would have broken links inside a file the archive
  keeps. Every surviving ART-014 citation names `quickstart.md` by bare filename
  inside prose — `ART-014-retrospective.md:338`, `ART-014-workflow.md:39`, `:910`
  and `:1681` — and none is a path or a link.
- **Nothing is owed.** Fifteen of ART-002's sixty-one runbook steps were still
  outstanding against four templates that ART-003, ART-004, ART-005 and ART-009
  all build on. All seven ART-014 scenarios were executed on 2026-08-13, against
  head `800d1e7d`, and every one passed.

ART-002's own `quickstart.md` was likewise deleted with its folder; only the UAT
runbook moved. The recovery command below restores this one in full.

The ART-012 test-repointing step has no analogue here: ART-014 ships no
`contracts/` directory, and no test cites the spec folder.

## Reviewability Outcome

Declared 337 reviewable LOC across six authored files, one slice. Final count at
the merged head: **906 added, 38 removed** across those six; **488 added** across
the five production files.

The overrun is recorded rather than smoothed. The modify-weighted slice formula
prices a MODIFIED file at roughly 20 effective LOC, and two deliverables broke
that price: the classification record is 225 lines because it classifies 21 keys
with a stated reason each, and the tests add 418. The estimator has no term for a
requirement whose deliverable **is** prose volume inside one existing file.

The six-file framing crosses the 800 block threshold. The production-only row,
488, is the framing the threshold is calibrated against and stays in the warn
band. Splitting the repair from the tests that prove it would have produced a
slice unable to demonstrate its own correctness, which is the failure this
feature exists to close, so the slice decision stands. ART-015 owns the
re-estimation trigger this overrun argues for.

## Recovery Commands

```text
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/spec.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/plan.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/tasks.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/research.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/quickstart.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/SPEC-MOC.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/checklists/data-integrity.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/checklists/error-handling.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/checklists/requirements.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/checklists/security.md
git checkout 12d8c2d48469df9293227cb2c28cf05a4847fc61 -- specs/art-014-phase-guard-enforcement-repair
```

## Changed Files and Impact

| File | Change Summary |
|---|---|
| `.specify/memory/archive-reports/2026-08-13-art-014-post-merge-hygiene.md` | this report, new |
| `.specify/memory/changelog.md` | ART-014 entry appended |
| `.specify/memory/spec.md` | requirements, criteria and cleanup note appended |
| `.specify/memory/plan.md` | shipped surface, testing and cleanup appended |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-014 marked Complete / Archived; ART-017 unblocked; status prose updated |
| `docs/ai/specs/.process/autopilot-state.json` | `status` archived, `archived_at` recorded |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | regenerated by the spec index |
| `specs/art-014-phase-guard-enforcement-repair/**` | removed, 10 tracked files |

## Feature Status

The feature's own `spec.md` carried `**Status**: Draft`. Step 6.5's flip to
`Completed` is **superseded by cleanup** and was not applied: the file does not
survive this archive, so the edit would exist only to be deleted in the same
commit. The merged state is recoverable verbatim from the command above. This
matches the ART-002 and ART-012 precedent, where no status flip preceded folder
removal.

## Constitution Compliance

No conflict. This archive changes documentation and project memory only.

- **I. Plugin Structure Compliance** — untouched; no plugin layout changes.
- **II. Cross-Platform Runtime & Script Safety** — untouched; no repository
  tooling changes, and no Bash or `jq` dependency is added.
- **III. Semantic Versioning** — untouched; no manifest or version changes.
- **IV. Test Coverage Before Merge** — the suite is unchanged at 7396 and no
  test file is edited, because nothing this archive touches is asserted by a
  test other than the regenerated index.

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/art-014-phase-guard-enforcement-repair`
- **blockedBy**: none

Gate-by-gate:

| # | Gate | Result |
|---|---|---|
| 1 | `--apply-cleanup` explicitly supplied | pass |
| 2 | Target is not `--current-target` | pass; no run in flight |
| 3 | Merged, with recorded PR URL and merge commit | pass; #433, `12d8c2d4` |
| 4 | Archive completed successfully in this run | pass |
| 5 | Report includes recovery commands per artifact | pass; 11 commands above |
| 6 | Worktree clean before cleanup | pass |
| 7 | Active branch is a safe base branch | **pass with a recorded deviation**, below |
| 8 | No history rewrite, no reliance on post-merge CI mutating `main` | pass |

**Gate 7 deviation.** The gate names `main` as the normal cleanup branch. This
archive runs on `art-014-post-merge-hygiene`, branched from `main` at the merge
commit, because this repository forbids committing directly to `main` and lands
every change through a pull request. The gate's intent — do not run cleanup from
an unrelated feature branch carrying unmerged work — is satisfied: the branch was
cut from `main` at `12d8c2d4` for this archive alone and contains nothing else.
The precedent is established; archive commits landed the same way in PR #431 for
ART-002 and ART-012, and PR #424 for ART-006.

## Defaults Applied

- **Agent knowledge (Step 6.3) skipped.** The skill would update `AGENTS.md`, but
  this repository's own agent-file hygiene forbids release notes, feature plans,
  and process history in agent files. The precedent commits did not touch it
  either. Where the skill text and this repository's rules disagree, the
  repository wins.
- **Step 0.1 path resolution degraded.** `.specify/scripts/bash/check-prerequisites.sh`
  exits with `Feature directory not found` because `.specify/feature.json` is
  absent — the expected state for a post-merge worktree with no active feature.
  The script is present and executable, so this is a resolution failure rather
  than a missing-script stop, and absolute paths were supplied explicitly as the
  skill permits.
- No scope modifiers were passed, so all archival artifacts were updated.

## Scoping

Single feature. No sweep was requested, and no other spec is awaiting cleanup.
`specs/` held only `art-014-phase-guard-enforcement-repair` and
`brand-001-racecraft-identity-system`. BRAND-001 is not an archive candidate: its
planning package merged in PR #432, but the spec itself is scaffolded and parked
with all seven phases still pending, so its folder is active work rather than
merged residue.

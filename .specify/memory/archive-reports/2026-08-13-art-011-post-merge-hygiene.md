# Archival Report - ART-011 Scaffold Integration

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

- **Source spec path**: `specs/art-011-scaffold-integration`
- **Feature branch**: `art-011-scaffold-integration`
- **PR URL**: <https://github.com/racecraft-lab/racecraft-plugins-public/pull/434>
- **Merge commit**: `6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b`
- **Merged at**: 2026-08-13T21:06:20Z by `fgabelmannjr`
- **PR size at merge**: 41 files, 9039 added, 440 removed
- **Tree reference**: not captured separately; the merge commit is the recovery
  anchor for every command below
- **CI run URL**:
  <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/31739312031>
- **CI outcome on the final head** (`34cbd591`): 19 pass, 1 skipped, 0 failures
- **Metadata gates**: `artifact-consistency=pass`, `validate-docs=pass`,
  `test (speckit-pro)=pass`, `validate-release-note=pass`,
  `validate-pr-title=pass`, `validate-plugins=pass`
- **Argos build/review URL**: not applicable; this repository runs no visual
  regression service
- **Artifact manifest**: not applicable
- **Screenshot retention**: none produced
- **Expiration risk**: none. Every artifact this report cites is either committed
  to `main` or recoverable from the merge commit

## Feature Summary

ART-011 made `speckit-scaffold-spec` open with a read-only blind-spot pass and
close by handing the operator the exact command that starts the planning stage.
The pass reuses the shipped `codebase-analyst` agent; grill-me is untouched.
Both platform variants ship the change.

**The feature's central design changed during review, and the change is the
reason it exists in its final shape.** The spec was written to *chain*
in-session into the autopilot plan stage, so one invocation would end at a
reviewed draft PR. That is not implementable: `speckit-autopilot/SKILL.md`
carries `disable-model-invocation: true`, added deliberately, which blocks the
`Skill` tool entirely. Removing the flag would have made a seven-phase
auto-committing run model-triggerable — precisely the case the flag documents.
Scaffold was demoted to printing the hand-off command, and the whole
post-planning apparatus the chain implied became unreachable and was deleted.

The amendment cascaded through the spec: FR-013, FR-013a, FR-014, FR-015,
FR-017, FR-018, FR-022, SC-007 and SC-011 were amended, and FR-015a, FR-015b,
FR-019, FR-020 and SC-010 were marked superseded. `contracts/chain-handoff.md`
carries a banner stating that no section is unchanged.

Scale: 4 user stories, 31 functional requirements, 12 success criteria, 47 of 47
tasks complete. Two production files, both `SKILL.md` variants. The repository
suite stayed at **7396**, because the change is prose and adds no runnable test.

### What the run itself taught

A green check count is not evidence unless the **count** is right. Mid-review
this PR reported `gh pr checks` clean while only 4 of 20 checks had run: the
branch was `CONFLICTING` after ART-014 merged, and GitHub cannot build
`refs/pull/N/merge` for a conflicted PR, so every `pull_request` workflow was
skipped and only the branch-head CodeQL jobs reported. The absence of
`validate-pr-title`, `validate-release-note`, `validate-plugins` and
`test (speckit-pro)` is the signature. Both this PR and PR #440 were re-verified
at full check count before merge.

The second lesson is the size one, and it is recorded as a follow-up rather than
smoothed: this feature took a skill from three lines under the documented ceiling
to nearly twice it, with every gate green throughout.

## Known Gaps Carried Forward

- **Layer 2 trigger evaluation never ran (task T044), and the description
  changed.** The `description` is the string skill selection matches on, and this
  feature rewrote it from 975 to 1013 characters, replacing "Creates the git
  worktree, spec branch, Design Concept doc, and populated workflow file ready for
  autopilot" with "Opens with a blind-spot pass, creates the git worktree, spec
  branch, Design Concept doc, and populated workflow file, then hands off to
  planning". No gate covers this: `tests/speckit-pro/suite-manifest.json` marks
  Layer 2 `default: false`, `live_only: true`, `execution: print-commands`, so
  `run-all.py` reporting 7396/7396 is structurally incapable of measuring
  triggering. The runners are operator-only because
  `layer2-trigger/run-trigger-evals.py:225` moves the operator's installed skill
  directory aside and restores it in a `finally` at `:317`; a session killed
  mid-run leaves the installed plugin in the moved-aside state. Owed:

  ```text
  python3 tests/speckit-pro/layer2-trigger/run-trigger-evals.py speckit-scaffold-spec
  python3 tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py speckit-scaffold-spec --run
  ```

- **The shipped skill is now 97% over the documented line guidance.**
  `speckit-scaffold-spec` went from 497 to **984** lines on Claude and 468 to
  **928** on Codex, against the guide's "Keep `SKILL.md` under 500 lines".
  **ART-019** owns the repair and its slice D supersedes this feature's FR-022,
  which forbade the skill gaining a `references/` directory.

- **`git status --porcelain` reports untracked files**, so approved Step 3.5
  bootstrap output can trigger a spurious "resolve the uncommitted changes first"
  clause in the Step 9 hand-off. The wording is pinned verbatim at `spec.md:260`,
  so the repair is an FR amendment rather than a skill edit. The consequence is
  one advisory line; the check does not gate the hand-off.

- **Three review findings were reported but not independently adjudicated**: the
  five-minute blind-spot pass deadline is unmeasurable from within the skill's
  grant; `Key Files` is named as a seed element but is absent from Step 2's
  extraction list; and the "supplied workflow path" referent is undefined in
  scaffold's context, having been transcribed from the autopilot guard where the
  operator does supply it.

- **No retrospective was produced, and two records disagreed about that.**
  `ART-011-workflow.md:1321` reads `Post: Retrospective | ⏳ Pending`, while
  `autopilot-state.json` claimed the step completed. No `ART-011-retrospective.md`
  exists, so the workflow file is correct and the state file was wrong. This
  archive does not invent one.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by this cleanup:

- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` — the blind-spot pass,
  the hand-off check, the hand-off command table, and the single closing report
- `tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json` and
  its `codex-evals/` mirror — Layer 2 trigger fixture updated (currently 20 entries: 10 positive, 10 negative)
- Generated payload copies under `dist/claude` and `dist/codex`, plus the
  installed-cache proofs and XPLAT-009 results, all regenerated from source

Historical evidence stays under `docs/ai/specs/.process/`:
`ART-011-design-concept.md` and `ART-011-workflow.md`.

## Live-Reader Scan

The scan ran on the **bare directory name**, `art-011-scaffold-integration`,
rather than on joined paths, because a path assembled from `Path` components does
not appear in a joined-path search. Five files matched outside the folder:

| File | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/ART-011-design-concept.md` | prose citations of the branch and of artifact names | none; the preserved record describes the run as it was |
| `docs/ai/specs/.process/ART-011-workflow.md` | prose citations of the branch and of artifact names | none; same |
| `docs/ai/specs/.process/autopilot-state.json` | machine-written `feature_dir`, `branch`, `body_path` | status and `archive` block updated; paths left as the historical record |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | status prose and the Progress Tracking row | updated to Complete / Archived |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | a live backlink into `specs/…/SPEC-MOC.md` | **regenerated** by the spec index, never hand-edited |

### Why the contracts were not relocated

Unlike ART-014, this feature **does** ship a `contracts/` directory, so the
ART-012 test-repointing question is live rather than moot. It resolves to delete:

- **No live reader.** No test, script, or shipped file reads
  `contracts/blind-spot-pass.md` or `contracts/chain-handoff.md`. Every match
  outside the spec folder is inside the two preserved `.process/` documents.
- **No dangling pointer.** Those citations are bare relative names inside prose
  code spans — `contracts/chain-handoff.md` §2 — not links and not paths. From
  `docs/ai/specs/.process/`, `contracts/chain-handoff.md` does not resolve
  anywhere regardless of this cleanup; it is shorthand for "inside the spec
  folder". This is the ART-014 prose-citation test, and both contracts fail it in
  the same direction.

The contracts' load-bearing content — the exact operator-facing strings — was
transcribed into both shipped `SKILL.md` variants before merge, which is where
the behaviour now lives and where any future change must be made.

## Reviewability Outcome

| Measurement | Value |
|---|---|
| Roadmap declaration at scaffold | 162 reviewable LOC, ~4 production files |
| Estimator at scaffold | 187 LOC, 1 slice, ok |
| Estimator re-measured at 31 FRs | 322 LOC, 1 slice, ok |
| Actual at the merged head | 1160 production changed lines across 2 production files |

The overrun is recorded rather than smoothed, and its cause is the same one
ART-014 hit from the other direction: the estimator prices a MODIFIED file at
roughly 20 effective LOC and has no term for a requirement whose deliverable **is**
prose volume inside one existing file. Here the entire feature is prose inside two
existing files. The production surface *shrank* from the declared ~4 files to 2
while the line count rose sevenfold. ART-015 owns the re-estimation trigger; this
run is a second data point for it, and ART-019 slice D owns the resulting size.

## Recovery Commands

```text
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/spec.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/plan.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/tasks.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/research.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/SPEC-MOC.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/contracts/blind-spot-pass.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/contracts/chain-handoff.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/checklists/api-contracts.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/checklists/error-handling.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/checklists/requirements.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/checklists/ux.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/.process/pr-body.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/.process/changed-files.txt
git checkout 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b -- specs/art-011-scaffold-integration
```

## Changed Files and Impact

| File | Change Summary |
|---|---|
| `.specify/memory/archive-reports/2026-08-13-art-011-post-merge-hygiene.md` | this report, new |
| `.specify/memory/changelog.md` | ART-011 entry appended |
| `.specify/memory/spec.md` | requirements, criteria and cleanup note appended |
| `.specify/memory/plan.md` | shipped surface, testing and cleanup appended |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-011 marked Complete / Archived; status prose updated |
| `docs/ai/specs/.process/autopilot-state.json` | `status` archived, `archive` block recorded |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | regenerated by the spec index |
| `specs/art-011-scaffold-integration/**` | removed, 13 tracked files |

## Feature Status

The feature's own `spec.md` status line is **superseded by cleanup** and was not
flipped: the file does not survive this archive, so the edit would exist only to
be deleted in the same commit. The merged state is recoverable verbatim from the
commands above. This matches the ART-002, ART-012 and ART-014 precedent, where no
status flip preceded folder removal.

## Constitution Compliance

No conflict. This archive changes documentation and project memory only.

- **I. Plugin Structure Compliance** — untouched; no plugin layout changes.
- **II. Cross-Platform Runtime & Script Safety** — untouched; no repository
  tooling changes, and no Bash or `jq` dependency is added.
- **III. Semantic Versioning** — untouched; no manifest or version changes. The
  feature itself is already released through `speckit-pro` 2.25.0.
- **IV. Test Coverage Before Merge** — the suite is unchanged at 7396 and no test
  file is edited, because nothing this archive touches is asserted by a test other
  than the regenerated index.

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/art-011-scaffold-integration`
- **blockedBy**: none

Gate-by-gate:

| # | Gate | Result |
|---|---|---|
| 1 | `--apply-cleanup` explicitly supplied | pass |
| 2 | Target is not `--current-target` | pass; no run in flight |
| 3 | Merged, with recorded PR URL and merge commit | pass; #434, `6437ecd2` |
| 4 | Archive completed successfully in this run | pass |
| 5 | Report includes recovery commands per artifact | pass; 14 commands above |
| 6 | Worktree clean before cleanup | pass |
| 7 | Active branch is a safe base branch | **pass with a recorded deviation**, below |
| 8 | No history rewrite, no reliance on post-merge CI mutating `main` | pass |

**Gate 7 deviation.** The gate names `main` as the normal cleanup branch. This
archive runs on `art-011-post-merge-hygiene`, branched from `main` at `4ed7309a`,
because this repository forbids committing directly to `main` and lands every
change through a pull request. The gate's intent — do not run cleanup from an
unrelated feature branch carrying unmerged work — is satisfied: the branch was cut
for this archive alone and contains nothing else. The precedent is established;
archive commits landed the same way in PR #438 for ART-014, PR #431 for ART-002
and ART-012, and PR #424 for ART-006.

## Defaults Applied

- **Agent knowledge (Step 6.3) skipped.** The skill would update `AGENTS.md`, but
  this repository's own agent-file hygiene forbids release notes, feature plans,
  and process history in agent files. The precedent commits did not touch it
  either. Where the skill text and this repository's rules disagree, the
  repository wins.
- **`.specify/feature.json` is absent** and was not created, which is the expected
  state for a post-merge worktree with no active feature.
- No scope modifiers were passed, so all archival artifacts were updated.

## Scoping

Single feature. No sweep was requested. `specs/` held
`art-011-scaffold-integration` and `brand-001-racecraft-identity-system`.
BRAND-001 is not an archive candidate: its planning package merged in PR #432,
but the spec itself is scaffolded and parked with all seven phases still pending,
so its folder is active work rather than merged residue.

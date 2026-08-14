# Archival Report - ART-003 Final-PR Template Set

## Mode

- **archiveMode**: merged-spec cleanup sweep, ART family
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no run is in flight

## Provenance

**Every date in this report is UTC**, matching the merge timestamps GitHub
records. All three merges and this cleanup fall on 2026-08-14 UTC.

ART-003 shipped across **three** merged pull requests, one per stacked slice.
All three are merged; no ART-003 pull request remains open.

- **Source spec paths**: `specs/art-003-final-pr-template-set/`,
  `specs/art-003-final-pr-template-set-slice-2/`,
  `specs/art-003-final-pr-template-set-slice-3/`
- **Cleanup branch**: `art-003-post-merge-hygiene`
- **Merged by**: `fgabelmannjr` for all three

| PR | Title | Head branch | Merged at | Merge commit | Size |
|---|---|---|---|---|---|
| [#435](https://github.com/racecraft-lab/racecraft-plugins-public/pull/435) | `feat(art-003): add the pull request write-up artifact to the gallery` | `art-003-final-pr-template-set` | `2026-08-14T13:25:49Z` | `ad6cab53395fd410aa7acca05fd29531f0c9cd89` | 43 files, +12874 −260 |
| [#436](https://github.com/racecraft-lab/racecraft-plugins-public/pull/436) | `feat(speckit-pro): add the annotated diff gallery template` | `art-003-final-pr-template-set-slice-2` | `2026-08-14T14:14:24Z` | `6a1518c395fc3fcce4de315a70691eee33f4de94` | 37 files, +10081 −422 |
| [#439](https://github.com/racecraft-lab/racecraft-plugins-public/pull/439) | `feat(speckit-pro): add the flowchart gallery template` | `art-003-final-pr-template-set-slice-3` | `2026-08-14T14:54:54Z` | `780a6724915ce481199073de84fa007ca16deb8b` | 33 files, +6496 −98 |

**Base branch at merge was `main` for all three.** Slices 2 and 3 were authored
stacked — slice 2 on slice 1, slice 3 on slice 2 — and GitHub auto-retargeted each
to `main` when its parent squash-merged. Both retargets produced a conflict in
`tests/speckit-pro/unit/test-artifact-fill-regions.py`, because a squash lands the
parent's content as one new commit sharing no history with the child branch. Both
were resolved by proving the child a strict superset of `main` on the conflicted
file before taking the child's side. See **Stacking Cost** below.

- **Workflow files preserved**: `docs/ai/specs/.process/ART-003-workflow.md`,
  `ART-003-slice-2-workflow.md`, `ART-003-slice-3-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/ART-003-design-concept.md`
- **Acceptance runbook preserved**:
  `docs/ai/specs/.process/ART-003-uat-runbook.md` (relocated by this cleanup;
  see **Runbook Relocation**)
- **Retrospective**: none produced, as a separate file or inline. This archive
  does not invent one.
- **CI outcome**: **19 pass, 1 skipped, 0 failures on each of the three**, measured
  at each final head. No CI anomaly is recorded.
- **CI run URLs**:
  - #435 <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/31750692501>
  - #436 <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/31805538282>
  - #439 <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/31809468842>
- **Metadata gates**: `artifact-consistency`, `validate-docs`,
  `test (speckit-pro)`, `validate-release-note`, `validate-pr-title` and
  `validate-plugins` all pass on all three
- **Argos build/review URL**: not applicable; this repository runs no visual
  regression service
- **Artifact manifest**: the runner manifest and `.sha256` plus both `dist/`
  copies were regenerated inside each slice and are covered by the payload gates
- **Screenshot retention**: none committed. Visual review captures produced during
  acceptance live in a session scratchpad and are **not** repository evidence
- **Expiration risk**: none for committed evidence. The acceptance harness output
  is the exception and is recorded as a gap below

## Feature Summary

ART-003 ported the three final-PR delivery templates into Racecraft-branded,
self-contained single-file artifacts and flipped their gallery routing rows to
`shipped`. One template per slice, in roadmap order.

| Slice | Template | Shipped lines | Stage | Trigger | Exports |
|---|---|---|---|---|---|
| 1 (#435) | `pr-writeup.html` | 1193 | `final-pr` | always | `["prompt", "markdown"]` |
| 2 (#436) | `annotated-diff.html` | 1199 | `final-pr` | `self_review_findings` or `large_diff` | `["prompt", "markdown"]` |
| 3 (#439) | `flowchart.html` | 866 | `final-pr` | `operational_flow_change` | `[]` |

The gallery now carries **seven shipped templates of twenty-one catalogued**.
`flowchart` is the first shipped template declared read-only, and it carries no
export affordance at all — the declared-`[]` case that ART-001 FR-028 describes
but that no prior template exercised.

Scale: 72, 83 and 68 functional requirements across the three specs; 11, 13 and 13
success criteria. The repository suite moved from **7396 to 7399**.

### What the run itself taught

**Re-declaring the budget on realized measurement worked.** ART-002 declared 530
reviewable LOC per slice and measured 1494 and 2027 — two hard blocks. ART-003
re-declared at scaffold time against that realized number rather than the roadmap's
original 285, and split into three slices instead of one. Every slice then landed
**under** its own declaration:

| Slice | Declared | Measured | Gate |
|---|---|---|---|
| 1 (#435) | 758 | 735 | warn |
| 2 (#436) | 750 | 724 | warn |
| 3 (#439) | 460 | 408 | warn |

This is the first ART spec where no slice overran. The mechanism is exactly
ART-015's thesis — the estimator is sound and the failure is that nothing re-feeds
it — so this run is a positive data point for that entry rather than another
overrun to explain.

**Stacking is again why the run finished, and again it cost something.** The three
slices append to the same manifest block and the same fill-region test literals, so
stacking is what keeps them conflict-free while all three are open. The cost is
paid at merge: see **Stacking Cost**.

## Acceptance Result

The manual half of verification was **executed in full against the shipped bytes**,
on `file://`, for all three templates. **176 checks, 176 passed**: 58 for slice 1,
65 for slice 2, 53 for slice 3.

**How it was executed matters, because the runbook had recorded it as blocked.**
All three pull requests listed manual acceptance as unverified, citing browser
automation that refuses `file://`. That refusal comes from the automation tool's
own URL validation, not from Chrome. Chrome was launched directly with a debugging
port and driven over the DevTools Protocol through a standard-library WebSocket
client, which made every step executable on the real scheme: genuine console
capture, offline emulation, an achromatopsia filter, real `Tab` traversal, and real
clipboard reads. Serving over `http://` was not an option — the runbook forbids it,
and it changes the clipboard permission model so the failure paths never fire.

### Two defects were found and fixed before merge

**1. Copying a diff hunk produced an invalid patch fragment (slice 2).**
`.diff-row` was `display: grid`. Grid blockifies its items, and Chrome's plain-text
copy emits a newline between block-level boxes, so every copied row split in two —
the marker alone on one line, its code on the next. A whole-hunk copy yielded twice
the lines and no valid fragment. The fix makes the row a block with inline-block
cells carrying the former track widths, held equal by `box-sizing: border-box`; the
code cell is already `white-space: pre` and the container scrolls, so a row is
always one line and needs no hanging indent.

The defect was proved rather than asserted: a real clipboard read, headless and
headful, with causation isolated (`display: block` on the row fixes it;
`display: inline` on the children does not, because grid blockification overrides
child display). An adversarial pass across three independent lenses — harness,
mechanism, significance — returned **0 of 3 refuted**, having additionally tested a
real `Cmd+C`, the macOS pasteboard through `pbpaste`, a real `Cmd+V`, mouse-drag
selection, a clean profile with no granted permissions, and `http://`. The
significance lens established that the defect **enters with slice 2**:
`annotated-diff` is the only template that lays code out as grid cells; the others
use `<pre>` with inline spans.

**2. Activating a flowchart node link left focus behind (slice 3).** The link moved
the viewport and opened the disclosure but did not move focus into the revealed
node; against pre-fix bytes, focus landed on `BODY`. Fixed with `tabindex="-1"` on
the seven `.node-body` elements and by pointing each link at
`#nodes-<node-slug>-detail`, since a browser opens a closed disclosure only when
the fragment names something inside it. The drawing also gained an accessible name.

**This one the acceptance pass missed and code review caught.** The harness checked
`:target` and scroll position and never `activeElement`. Two checks were added
afterward, taking slice 3 from 51 to 53. Both slice-3 findings had additionally
been flagged by an automated reviewer before the acceptance pass ran at all.

### One requirement was corrected rather than satisfied

Step 1 of the runbook demanded the console show **nothing at all** on an offline
reload. That is unsatisfiable as the gallery is built. The shared branded head
requests a webfont, and a failed `@font-face` fetch logs identically to a failed
`<link>`; the only silent state is zero remote requests. Inlining the nine Latin
subsets costs 244 KB raw, 325 KB as base64, 7.7× the template size, and 2.2 MB
across all seven shipped templates — and it edits canonical bytes shared by the
whole gallery. **That is a gallery-wide decision, not ART-003's**, so the step was
rewritten instead: it now names the one expected line, explains that it comes from
the browser rather than the page, notes that all seven templates share the header,
and asserts silence once the network is back. The coverage map and rationale line
were updated to match.

### A near-miss worth recording

The clipboard-fallback probe initially used `delete navigator.clipboard`. That is a
**no-op** — `clipboard` is an accessor on `Navigator.prototype`, not an own
property — so the page appeared to report success with no clipboard present, and
was one step from being reported as a serious defect. Reading the template's own
source is what caught it: the call site reads `navigator.clipboard` at call time and
falls through to the reveal path. Redefining the property with
`Object.defineProperty` showed the fallback working correctly.

Other harness corrections, recorded because each produced a false result first: SVG
`tagName` is lowercase; reduced motion collapses durations to `1e-05s` rather than
`0s`; a same-instance offline reload serves the webfont from cache; `blur()` does
not reset the sequential focus navigation starting point, and neither does a reload
that keeps a fragment in the URL.

## Stacking Cost

Recorded because it is the recurring price of the stacked-slice shape this roadmap
now uses by default, and it was paid twice in one hour.

When slice 1 squash-merged, GitHub retargeted slice 2 to `main`. The squash landed
slice 1's content as a single new commit sharing no history with slice 2's branch,
so every line both touched conflicted. The same happened to slice 3 when slice 2
merged. Both conflicts were in `tests/speckit-pro/unit/test-artifact-fill-regions.py`
and had the same ambiguous shape: the child's added rows on one side and **nothing**
on `main`'s, which git cannot distinguish from a deletion.

The resolution method was the same both times and is worth reusing: prove the child
is a strict superset of `main` on the conflicted file — `diff` the two sorted sides
and confirm `main` holds **zero** lines the child lacks — then resolve to the
child's side and confirm the specific rows survived. Generated paths resolved
without conflict through the repository's `merge=generated` driver and were
regenerated rather than hand-merged.

## Known Gaps Carried Forward

- **No acceptance record was merged.** ART-002 recorded its runbook result in a
  dedicated follow-up, PR #430. ART-003 has no equivalent: the 176 executed checks
  and their verdicts exist in this report and in three JSON files that live in a
  session scratchpad and are **not** committed. The preserved runbook carries the
  procedure, not the outcome. Anyone re-verifying this work has to re-run it.

- **Three records disagree about the runbook itself.** All three workflow files
  read `Post: UAT Runbook Generation | ⏳ Pending`, yet slice 1's runbook exists and
  was added in #435. Slices 2 and 3 produced no runbook at all, so the preserved
  document covers `pr-writeup` only — its 58 steps are one third of the acceptance
  that was actually performed.

- **Slices 2 and 3 ship with every task box unchecked**: 0 of 41 and 0 of 36,
  against slice 1's 40 of 40. The work merged and CI passed on all three, so the
  ledgers were simply never flipped. This is the ART-011 shape — a state record
  disagreeing with reality — and it is recorded rather than back-filled, because
  the folders do not survive this archive.

- **The console condition is unchanged, only its expectation is.** All seven
  shipped templates emit one console line when the network is unavailable.
  Inlining the typeface is the only silent option and belongs to whoever owns the
  canonical head block, not to a template port.

- **The acceptance harness is not repository tooling.** It is scratchpad Python
  driving Chrome over CDP. It is the only thing that has ever executed these
  runbooks end to end, and nothing in the repository can reproduce it. ART-009
  replaces the UAT walkthrough and is the natural home for that decision.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by this cleanup:

- `speckit-pro/artifact-gallery/templates/pr-writeup.html`
- `speckit-pro/artifact-gallery/templates/annotated-diff.html`
- `speckit-pro/artifact-gallery/templates/flowchart.html`
- `speckit-pro/artifact-gallery/manifest.json` (three catalog entries flipped to
  `shipped`)
- `dist/claude/**` and `dist/codex/**` materializations of the above
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/**` (installed-cache
  copies and their regenerated proofs)
- `docs-site/src/content/docs/reference/tests.md`

Historical evidence stays under `docs/ai/specs/.process/`:
`ART-003-design-concept.md`, `ART-003-workflow.md`,
`ART-003-slice-2-workflow.md`, `ART-003-slice-3-workflow.md`, and
`ART-003-uat-runbook.md`.

## Runbook Relocation

`specs/art-003-final-pr-template-set/.process/ART-003-uat-runbook.md` is **not**
run exhaust and was moved rather than deleted, matching the ART-002 precedent.

The ART-002 relocation rested on two reasons. Only one of them carries here, and it
is stated plainly rather than borrowed:

- **The citation reason does not apply.** A tree-wide scan for `ART-003-uat-runbook`
  and for `art-003-final-pr-template-set/.process` found **zero** matches outside
  the runbook itself. Unlike ART-002, no preserved workflow file names it, so
  deleting it would leave no dangling pointer.
- **The forward-evidence reason does.** It is the only committed statement of what
  acceptance means for `pr-writeup.html`, a file that survives this cleanup and that
  ART-010 will generate into. Its Step 1 now carries the console finding above —
  the reasoning for why one console line is expected and what inlining the typeface
  would cost — and that reasoning exists nowhere else in the tree. Deleting the
  runbook would delete the finding with it.

It was moved to `docs/ai/specs/.process/ART-003-uat-runbook.md` with `git mv`. No
citation needed repointing. The runbook is self-contained: its body references no
path that the move breaks.

## Live-Reader Scan

The scan ran on the **bare directory names** — all three of them — rather than on
joined paths, because a path assembled from `Path` components does not appear in a
joined-path search. It also covered the shared fragment `final-pr-template-set` and
the runbook filename.

| Match | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/ART-003-design-concept.md` | prose citations of the branch | none; the preserved record describes the run as it was |
| `docs/ai/specs/.process/ART-003-workflow.md` and the two slice workflow files | prose citations of branches and artifact names | none; same |
| `docs/ai/specs/.process/autopilot-state.json` | machine-written `workflow_file`, `feature_dir`, `branch` | status and `archive` block updated; paths left as the historical record |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | status prose and the Progress Tracking row | updated to Complete / Archived |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | a live backlink into `specs/…/SPEC-MOC.md` | **regenerated** by the spec index, never hand-edited |

**No live code, test, script, workflow, or docs-site reader depends on any of the
three spec folders.** Both Layer 4 tests read the gallery templates and manifest
under `speckit-pro/`, never a spec folder.

### Why the contracts were not relocated

Slice 1 ships `contracts/export-payload-contract.md`, so the question is live rather
than moot. It resolves to delete on both prongs, the same way ART-011's did:

- **No live reader.** No test, script, or shipped file reads it. The contract's
  load-bearing content — the exact pinned export strings — is asserted by
  `tests/speckit-pro/unit/test-artifact-gallery.py` against the shipped templates,
  which is where the behaviour now lives and where any future change must be made.
- **No dangling pointer.** Every surviving mention is a bare relative name inside a
  prose code span in a preserved `.process/` document, not a link and not a
  resolvable path.

`quickstart.md`, `research.md`, `data-model.md` and the seven `checklists/` files
across the three folders are run exhaust — validation guides and design records for
work already merged — and are removed with the folders. All are recoverable at the
merge commits.

## Reviewability Outcome

| Slice | Roadmap projection at scaffold | Declared at Plan | Measured at merge | Gate |
|---|---|---|---|---|
| 1 (#435) | ~750 | 758 | 735 | warn |
| 2 (#436) | ~780 | 750 | 724 | warn |
| 3 (#439) | ~410 | 460 | 408 | warn |

All three warn; none reaches the 800 block; no exception pragma was required. The
projections came from ART-002's realized ~2.2× multiplier over upstream line count,
discounting the 458 canonical block lines a reviewer never reads (`BRAND-KIT` 318,
`GALLERY-HEAD` 140, both byte-verified). Every projection held within 6%.

Two checkpoints fired mid-implement and were honoured rather than waived: slice 2's
first CSS measurement missed twice (167, then 151 against 150) and slice 3's came in
at 296 against a 210 ceiling, caught with 200 lines written rather than at review.

## Recovery Commands

Each folder is recoverable at its own slice's merge commit.

```text
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/spec.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/plan.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/tasks.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/research.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/data-model.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/quickstart.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/SPEC-MOC.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/contracts/export-payload-contract.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/checklists/requirements.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/checklists/accessibility.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/checklists/error-handling.md
git show ad6cab53395fd410aa7acca05fd29531f0c9cd89:specs/art-003-final-pr-template-set/checklists/ux.md
git checkout ad6cab53395fd410aa7acca05fd29531f0c9cd89 -- specs/art-003-final-pr-template-set

git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/spec.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/plan.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/tasks.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/research.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/data-model.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/quickstart.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/SPEC-MOC.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/checklists/requirements.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/.process/pr-body.md
git show 6a1518c395fc3fcce4de315a70691eee33f4de94:specs/art-003-final-pr-template-set-slice-2/.process/changed-files.txt
git checkout 6a1518c395fc3fcce4de315a70691eee33f4de94 -- specs/art-003-final-pr-template-set-slice-2

git show 780a6724915ce481199073de84fa007ca16deb8b:specs/art-003-final-pr-template-set-slice-3/spec.md
git show 780a6724915ce481199073de84fa007ca16deb8b:specs/art-003-final-pr-template-set-slice-3/tasks.md
git show 780a6724915ce481199073de84fa007ca16deb8b:specs/art-003-final-pr-template-set-slice-3/SPEC-MOC.md
git show 780a6724915ce481199073de84fa007ca16deb8b:specs/art-003-final-pr-template-set-slice-3/checklists/requirements.md
git show 780a6724915ce481199073de84fa007ca16deb8b:specs/art-003-final-pr-template-set-slice-3/.process/pr-body.md
git show 780a6724915ce481199073de84fa007ca16deb8b:specs/art-003-final-pr-template-set-slice-3/.process/changed-files.txt
git checkout 780a6724915ce481199073de84fa007ca16deb8b -- specs/art-003-final-pr-template-set-slice-3
```

The acceptance runbook is **not** in the recovery list, because it was not deleted.
It is live at `docs/ai/specs/.process/ART-003-uat-runbook.md`.

## Changed Files and Impact

| File | Change Summary |
|---|---|
| `.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md` | this report, new |
| `.specify/memory/changelog.md` | ART-003 entry appended |
| `.specify/memory/spec.md` | shipped behaviour, acceptance result and cleanup note appended |
| `.specify/memory/plan.md` | shipped surface, testing and cleanup appended |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-003 marked Complete / Archived; status prose updated; ART-010's remaining dependency narrowed |
| `docs/ai/specs/.process/ART-003-uat-runbook.md` | preserved from slice 1's `.process/` directory by `git mv` |
| `docs/ai/specs/.process/autopilot-state.json` | `status` archived, `archive` block recorded |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | regenerated by the spec index |
| `specs/art-003-final-pr-template-set/**` | 11 tracked files removed, plus the runbook relocated |
| `specs/art-003-final-pr-template-set-slice-2/**` | removed, 10 tracked files |
| `specs/art-003-final-pr-template-set-slice-3/**` | removed, 6 tracked files |

## Feature Status

Each slice's own `spec.md` status line is **superseded by cleanup** and was not
flipped: the files do not survive this archive, so the edits would exist only to be
deleted in the same commit. The merged state is recoverable verbatim from the
commands above. This matches the ART-002, ART-011, ART-012 and ART-014 precedent.

## Constitution Compliance

No conflict. This archive changes documentation and project memory only.

- **I. Plugin Structure Compliance** — untouched; no plugin layout changes.
- **II. Cross-Platform Runtime & Script Safety** — untouched; no repository tooling
  changes, and no Bash or `jq` dependency is added.
- **III. Semantic Versioning** — untouched; no manifest or version changes.
- **IV. Test Coverage Before Merge** — the suite is unchanged at 7399 and no test
  file is edited, because nothing this archive touches is asserted by a test other
  than the regenerated index.

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git mv` the acceptance runbook to
  `docs/ai/specs/.process/ART-003-uat-runbook.md`, then
  `git rm -r` all three spec folders after merge provenance and a tree-wide
  live-reader scan on each bare directory name
- **cleanupBranch**: `art-003-post-merge-hygiene`
- **blockedBy**: none

Gate-by-gate:

| # | Gate | Result |
|---|---|---|
| 1 | Cleanup explicitly requested | pass |
| 2 | Target is not `--current-target` | pass; no run in flight |
| 3 | Merged, with recorded PR URL and merge commit | pass; #435 `ad6cab53`, #436 `6a1518c3`, #439 `780a6724` |
| 4 | Archive completed successfully in this run | pass |
| 5 | Report includes recovery commands per artifact | pass; 31 commands above |
| 6 | Worktree clean before cleanup | pass |
| 7 | Active branch is a safe base branch | **pass with a recorded deviation**, below |
| 8 | No history rewrite, no reliance on post-merge CI mutating `main` | pass |

**Gate 7 deviation.** The gate names `main` as the normal cleanup branch. This
archive runs on `art-003-post-merge-hygiene`, cut from `main` at `780a6724`, because
this repository forbids committing directly to `main` and lands every change through
a pull request. The gate's intent — do not run cleanup from an unrelated feature
branch carrying unmerged work — is satisfied: the branch was cut for this archive
alone and contains nothing else. The precedent is established by PR #441 for
ART-011, PR #438 for ART-014, PR #431 for ART-002 and ART-012, and PR #424 for
ART-006.

## Defaults Applied

- **Agent knowledge (Step 6.3) skipped.** The skill would update `AGENTS.md`, but
  this repository's own agent-file hygiene forbids release notes, feature plans and
  process history in agent files. Where the skill text and this repository's rules
  disagree, the repository wins.
- **`.specify/feature.json` is absent** and was not created, which is the expected
  state for a post-merge worktree with no active feature.
- No scope modifiers were passed, so all archival artifacts were updated.

## Scoping

Invoked on the **ART family**, not a single spec. `specs/` held four folders: the
three ART-003 slices and `brand-001-racecraft-identity-system`.

ART-003 is the family's only archive candidate. ART-001, ART-002, ART-006, ART-011,
ART-012 and ART-014 are already archived; every other ART entry is Ready or Pending
with no spec folder on disk. BRAND-001 is out of family and is not a candidate
regardless: its planning package merged in PR #432, but the spec itself is
scaffolded and parked with all seven phases still pending, so its folder is active
work rather than merged residue.

## Downstream State

ART-003's completion clears one of **ART-010**'s three dependencies. ART-010 remains
blocked by **ART-007**; its ART-012 dependency was satisfied by PR #426. ART-007 is
Ready and unblocked, so ART-010's path is now a single spec deep.

# Archival Report - ART-002 Draft-PR Template Set

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no run is in flight

## Provenance

ART-002 shipped across **three** merged pull requests: two feature slices and a
follow-up that recorded the acceptance result. All three are merged; no ART-002
pull request remains open.

- **Source spec path**: `specs/art-002-draft-pr-template-set/`
- **Cleanup branch**: `chore/archive-art-post-merge`
- **Base branch**: `main` for all three
- **Merged by**: `fgabelmannjr` for all three

| PR | Title | Head branch | Merged at | Merge commit |
|---|---|---|---|---|
| [#425](https://github.com/racecraft-lab/racecraft-plugins-public/pull/425) | `feat(speckit-pro): add the implementation-plan and spec-explainer gallery templates` | `art-002-draft-pr-template-set` | `2026-08-11T20:01:03Z` | `a9e8d30764fd1dc28ea07734d4dbe7c0952e1294` |
| [#427](https://github.com/racecraft-lab/racecraft-plugins-public/pull/427) | `feat(speckit-pro): add the code-approaches and module-map gallery templates` | `art-002-draft-pr-template-set-slice-2` | `2026-08-11T20:22:45Z` | `4ecb1b4b441cbb85015586612190a7bc340f0c9c` |
| [#430](https://github.com/racecraft-lab/racecraft-plugins-public/pull/430) | `docs(art-002): record the acceptance runbook results for all four templates` | `art-002-uat-results` | `2026-08-12T00:56:19Z` | `425364b7be34d5b88605012d0492c0e97bdbefaf` |

- **Workflow preserved**: `docs/ai/specs/.process/ART-002-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/ART-002-design-concept.md`
- **Acceptance runbook preserved**:
  `docs/ai/specs/.process/ART-002-uat-runbook.md` (relocated by this cleanup;
  see **Runbook Relocation**)
- **Retrospective**: recorded inline in the preserved workflow file under
  *Lessons Learned*, not as a separate file. ART-006's separate
  `ART-006-retrospective.md` is the exception, not the convention.
- **CI / metadata gates**: clean on all three. #425 and #427 each carry 21 pass
  and 1 skip; #430 carries 26 pass and 4 skip. **Zero failures across all
  three**, so this archive records no CI anomaly.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: the runner manifest and `.sha256` plus both `dist/`
  copies were regenerated inside #425 and #427 and are covered by the payload
  gates; committed repository evidence is otherwise canonical
- **Screenshot retention**: N/A — the acceptance evidence is written prose in
  the preserved runbook, not captured images
- **Expiration risk**: none; committed source and process evidence has no
  artifact-retention dependency

## Feature Summary

ART-002 ported the first four upstream HTML-effectiveness templates into
Racecraft-branded, self-contained single-file artifacts and registered them in
the gallery routing manifest. Slice 1 shipped `implementation-plan` and
`spec-explainer`; slice 2 shipped `code-approaches` and `module-map`. Each
template carries declared fill regions, an export affordance matching its
catalog entry's declared export kinds, and no external reference of any kind.

Three properties are worth recording because they are what the next spec
depends on:

1. **The export contract holds character for character.** Every pinned string
   matches, including the two spaces before each anchor and the exact status
   wording. Empty phases produce no line, no placeholder, and no count. That is
   SC-005, judged explicitly rather than skimmed.
2. **Nothing a reader records survives a reload.** All four templates make zero
   non-theme `setItem` calls, so the property holds by construction rather than
   by observation.
3. **The `module-map` drawing stayed reachable to assistive technology.**
   It carries an accessible name and deliberately no `role="img"`, so upstream's
   single-image marking is gone and all seventeen internal labels remain
   reachable.

### What the run itself taught

**Stacking is why the run finished at all.** The original FR-040 required slice
2 to branch from a `main` that already contained slice 1. That shape cannot
complete in one invocation, because agents never merge pull requests in this
repository — the run would have stalled by construction. Stacking also turned
out to be the only shape that satisfied `research.md` D8 without a merge: the
Layer 4 module lands whole in slice 1 and six slice-2 tasks state their
acceptance against it. The slices were never independent; the merge gate had
concealed it.

**A review was carried forward rather than repeated.** Slice 1's blocking
finding — identifiers read for the pinned `Feature:` line sitting inside the
fill region under a comment claiming otherwise — described a class of defect
both slice-2 templates would have repeated by construction. It was written into
both slice-2 authoring prompts with the corrected helper to copy. Slice 2
therefore needed no remediation commit of its own.

**Two deliberate deviations in `code-approaches` were recorded rather than
absorbed.** The optional reason field is authored in markup rather than built at
load, which is the safer choice on FR-016a's own stated rationale: the construct
scan parses markup only out of single-line script string literals, so building
the field in script would have moved it into the one position the mandate exists
to empty. And a `choice-echo` line reports the chosen approach in text, because
a radio control's own marker is a shape rather than text.

## Acceptance Result

The manual half of verification ran against `4ecb1b4b` and was recorded in
#430. **Every executed step passed; no template changed, because no step
failed.**

Four kinds of check could not be executed as written, covering **fifteen of the
sixty-one steps**: the disconnected reload (4 steps), the reduced-motion setting
(4), the visible focus indicator (4), and the greyscale filter (3). Each is
recorded as *not executed* with the substitute that was run in its place.

**No step is recorded as a pass on evidence that covers only part of what it
expects.** Two exceptions to the coverage gaps are named inline in the runbook
rather than left to inference: opening from the filesystem is a departure of
method across the whole run (it was performed over HTTP), which changes how
every step was performed rather than what any step expects; and a real screen
reader is stronger than any step requires, since A14 and D12 permit the
accessibility inspector.

Review of #430 found three verdicts stated ahead of their evidence and one of
those — A15 — was found by this repository's own follow-up rather than by the
review. All were corrected before merge.

## Runbook Relocation

`specs/art-002-draft-pr-template-set/.process/uat-runbook.md` is **not** run
exhaust and was moved rather than deleted.

Two independent reasons, either sufficient:

1. **The preserved workflow file cites it twice.** `ART-002-workflow.md` names
   the path at its T046 row and again at its *Post: UAT Runbook Generation* row.
   Deleting the runbook would have left two dangling pointers inside a file this
   archive preserves — the same condition that forced ART-001's harness
   relocation.
2. **It is a re-runnable acceptance procedure for four shipped templates**, and
   fifteen of its sixty-one steps are still owed. ART-003, ART-004 and ART-005
   port further templates against the same contract, and ART-009 replaces the
   UAT walkthrough. The record is forward-looking evidence, not a record of
   finished work.

It was moved to `docs/ai/specs/.process/ART-002-uat-runbook.md` with `git mv`,
and both citations were repointed. The runbook is self-contained: a scan of its
body found no reference to its own old path, to the spec folder, or to any
relative path that the move would break. Its only outward references are the two
Layer 4 test files, which are untouched by this cleanup.

## Canonical Shipped Artifacts

- `speckit-pro/artifact-gallery/templates/implementation-plan.html`
- `speckit-pro/artifact-gallery/templates/spec-explainer.html`
- `speckit-pro/artifact-gallery/templates/code-approaches.html`
- `speckit-pro/artifact-gallery/templates/module-map.html`
- `speckit-pro/artifact-gallery/manifest.json` (four catalog entries flipped to
  `shipped`)
- `dist/claude/**` and `dist/codex/**` materializations of the above
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/**` (installed-cache
  copies and their regenerated proofs)
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/ART-002-workflow.md`
- `docs/ai/specs/.process/ART-002-design-concept.md`
- `docs/ai/specs/.process/ART-002-uat-runbook.md`

The acceptance runbook is **not** in the recovery list below, because it was not
deleted. It is live at `docs/ai/specs/.process/ART-002-uat-runbook.md`.

## Live-Reader Scan

A tree-wide scan was run before removal against the **bare directory name**, not
only the joined path, because references assembled from `Path` components do not
appear in joined-path searches — the failure mode that left CAR-003 pointing a
live Layer 6 library at its spec contracts. The scan also covered the bare
fragment `draft-pr-template-set` and the two evidence filenames.

Every match outside the folder lives in preserved documentation:

| Match | Verdict |
|---|---|
| `docs/ai/specs/.process/ART-002-workflow.md` (16 lines) | Historical narrative in a **preserved** file. The two that named the runbook path were repointed by this cleanup; the rest describe branches, outputs, and PR events that are correct as history. |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md:78` | Generated index entry; regenerated by this cleanup. |
| `docs/ai/specs/html-artifacts-technical-roadmap.md:130` | Progress-tracking row; rewritten by this cleanup. |

**No live code, test, script, workflow, or docs-site reader depends on
`specs/art-002-draft-pr-template-set/`.** Both Layer 4 tests read the gallery
templates and manifest under `speckit-pro/`, never the spec folder.

`quickstart.md`, `research.md`, `data-model.md`, the two `contracts/` files and
the four `checklists/` files are run exhaust — validation guides and design
records for work already merged — and were removed with the folder. All are
recoverable at the merge commit. No contract relocation was required: every
shipped surface was authored outside `specs/**`.

## Reviewability Outcome

Recorded because both slices exceeded their declared line budget and the pull
requests said so openly rather than defending it.

| Slice | Declared | Measured | Gate result |
|---|---|---|---|
| 1 (#425) | 530 reviewable LOC | 1494 | `block`, size-only |
| 2 (#427) | 530 reviewable LOC | 2027 | `block`, size-only |

Both blocks are size-only with no correctness finding, and both were treated as
marker-planning input rather than a re-slicing stop. The declaration was
corrected to the measured figure rather than left at the projection. The
overrun's cause is structural: a self-contained single-file artifact has no
shared runtime to factor out, so each template carries its own copy of the
branded head block and export path by design.

Scoping had also under-counted twice at scaffold time. Both claims were
corrected in the spec against measured evidence during Plan rather than left to
drift.

## Recovery Commands

Every removed file is recoverable at #430's merge commit, which is the last
commit containing the complete folder.

```text
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/spec.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/plan.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/tasks.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/research.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/data-model.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/quickstart.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/SPEC-MOC.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/contracts/export-payload-contract.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/contracts/slot-inventory-contract.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/checklists/requirements.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/checklists/accessibility.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/checklists/security.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/checklists/ux.md
git checkout 425364b7be34d5b88605012d0492c0e97bdbefaf -- specs/art-002-draft-pr-template-set
```

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| `.specify/memory/archive-reports/2026-08-11-art-002-post-merge-hygiene.md` | This report |
| `docs/ai/specs/.process/ART-002-uat-runbook.md` | Preserve the acceptance record from the feature `.process/` directory |
| `docs/ai/specs/.process/ART-002-workflow.md` | Repoint the two acceptance-runbook references |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | Mark ART-002 complete/archived; clear the "in progress" prose; unblock ART-007 |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | Frontmatter status; generated index zone regenerated |
| `specs/art-002-draft-pr-template-set/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git mv` the acceptance runbook to
  `docs/ai/specs/.process/ART-002-uat-runbook.md`, then
  `git rm -r specs/art-002-draft-pr-template-set` after merge provenance and a
  tree-wide live-reader scan on the bare directory name
- **cleanupBranch**: `chore/archive-art-post-merge`
- **blockedBy**: none
- **Base-branch note**: the archive extension's cleanup gate names `main` as the
  normal safe base. This repository never commits to `main`, so the established
  local convention — used by every prior archive here — is a cleanup branch cut
  directly from the current mainline. That is what this cleanup uses.
- **Stacking note**: none. This branch is cut from `b7b80842`, the current
  mainline, and ART-012 is archived on the same branch in the same commit, so no
  `.specify/memory/` append conflicts with an open branch.
- **Downstream state**: ART-002's completion unblocks **ART-007**, whose only
  remaining dependency was this spec. ART-010 stays blocked by ART-003 and
  ART-007.

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

See the shared **Verification Results** section of the ART-012 report for this
cleanup, `2026-08-11-art-012-post-merge-hygiene.md`. Both specs are archived in
one commit on one branch, so the checks ran once over the combined change and
are recorded once rather than duplicated.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence — workflow, design concept
and the acceptance record all remain under `docs/ai/specs/.process/`, the last by
relocation rather than deletion — changes no plugin version or runtime payload,
adds no active Bash or `jq` dependency, retains all merged source through
immutable git provenance, and leaves the full Python-authoritative suite as the
completion gate.

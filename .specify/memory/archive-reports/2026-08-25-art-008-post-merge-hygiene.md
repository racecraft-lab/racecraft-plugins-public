# Archival Report - ART-008 Feedback Sweep

## Mode

- **archiveMode**: merged-spec cleanup, ART sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no ART-008 run is in flight
- **excludedInFlight**: `specs/art-017-state-bookkeeping-checks` is 🔄 In Progress
  and was not touched. `specs/brand-001-racecraft-identity-system` is outside the
  ART family and was not touched.

## Provenance

All dates are UTC. ART-008 shipped as two stacked slices. Both are merged and no
ART-008 implementation pull request remains open.

- **Source spec paths**: `specs/art-008-feedback-sweep/`,
  `specs/art-008-feedback-sweep-slice-2/`
- **Cleanup branch**: `art-008-archive-post-merge`
- **Cleanup base**: current `main` at `8edeb2248`

| PR | Title | Merged at | Merge commit |
|---|---|---|---|
| [#464](https://github.com/racecraft-lab/racecraft-plugins-public/pull/464) | `feat(speckit-pro): sweep draft pull request feedback before implementation begins` | `2026-08-24T00:41:46Z` | `8db22a42078074c217c79de3498fbdf9951ffa37` |
| [#502](https://github.com/racecraft-lab/racecraft-plugins-public/pull/502) | `feat(speckit-pro): Regenerate draft artifact pages after feedback sweep amendments` | `2026-08-25T01:12:32Z` | `32043c45a60e7c38d15f0958bc4874f0362ea505` |

The cumulative recovery boundary is
`32043c45a60e7c38d15f0958bc4874f0362ea505`, which carries both directories in
their final state.

- **CI outcome**: PR #502's final head `b116e5ec0` returned 19 passing checks and
  one skipped advisory job, with no other conclusion. PR #464 merged green.
- **Review**: PR #502 took two independent code reviews plus a Copilot review.
  Nine defects were found and fixed across them; no unresolved actionable
  finding remains and all three Copilot threads are resolved.

## Feature Summary

ART-008 opened the implement stage with a draft-pull-request feedback sweep.

| Slice | Result |
|---|---|
| 1, the checkpoint | read both comment surfaces, author trust filter, export recognition, classification, consensus amendment, Feedback Sweep Log and CRL rows, per-comment replies, stop-or-proceed, unreadable-PR stop |
| 2, artifact freshness | whole-set regeneration after amendments, stale-page detection by a git-history join, draft-description refresh, and the `check-artifact-freshness` read-only helper across three named surfaces |

Slice 1 completed 111/111 tasks; slice 2 completed 81/81. The repository suite
stood at 14208/14208 at slice 2's merge.

## Acceptance Result

**This record is deliberately incomplete, and the gap is the point.**

Slice 1's seven quickstart scenarios were executed at T079 and each passed.
Slice 2 executed quickstart scenarios 1, 2, 6 and 7 by hand against worktree
source. **Scenarios 3, 4 and 5 were never executed.** Each needs an autopilot run
reaching Phase 7 on a draft pull request carrying reviewer feedback, and the
autopilot runs from the installed plugin cache rather than from source, so none
of the three can execute against a working tree.

They are carried to ART-009, which owns UAT, is unstarted, and whose own
autopilot run is that condition rather than a simulation of it. The carry is
recorded in the ART-009 roadmap entry's Scope block — the text
`speckit-scaffold-spec` reads at Step 2 and Step 3.6 — so the next scaffold is
briefed rather than merely archived. **Do not read this report as a
fully-verified acceptance claim.**

Slice 2's manual UAT also found a defect in its own instructions: Scenario 1 told
the reader to compare whole runner envelopes across two runs, which always differ
because the envelope carries a wall-clock `duration_ms`. The scenario now
compares the helper payload.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by cleanup.

- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — `sweep_pr_feedback` and
  `check_artifact_freshness` and their supporting functions
- `speckit-pro/speckit_pro_runner/helpers/registry.py` — both helper entries
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
- `speckit-pro/skills/speckit-autopilot/SKILL.md`
- `tests/speckit-pro/unit/test-feedback-sweep-parse.py`
- `tests/speckit-pro/unit/test-artifact-freshness.py` and its 60-case corpus
- generated `dist/claude/**` and `dist/codex/**` payloads, installed-cache
  mirrors, release proofs and docs reference pages

### Historical process evidence

- `docs/ai/specs/.process/ART-008-design-concept.md`
- `docs/ai/specs/.process/ART-008-workflow.md`
- `docs/ai/specs/.process/ART-008-slice-2-design-concept.md`
- `docs/ai/specs/.process/ART-008-slice-2-workflow.md`
- `docs/ai/specs/.process/ART-008-retrospective.md` (relocated)
- `docs/ai/specs/.process/ART-008-slice-2-retrospective.md` (relocated)
- `docs/ai/specs/.process/ART-008-slice-2-quickstart.md` (relocated)

## Evidence Relocation

Three files were durable evidence rather than disposable planning output and were
moved before the active folders were removed.

| Original | Durable path | Reason |
|---|---|---|
| `specs/art-008-feedback-sweep-slice-2/quickstart.md` | `docs/ai/specs/.process/ART-008-slice-2-quickstart.md` | the acceptance record, and the ART-009 roadmap entry cites it as the source of the three undischarged scenarios. ART-009 is `Ready` and unscaffolded, so deleting it would have left a Ready spec pointing at nothing |
| `specs/art-008-feedback-sweep/.process/retrospective.md` | `docs/ai/specs/.process/ART-008-retrospective.md` | the workflow file's `Post: Retrospective` row names where the record lives |
| `specs/art-008-feedback-sweep-slice-2/.process/retrospective.md` | `docs/ai/specs/.process/ART-008-slice-2-retrospective.md` | same |

Every citation was repointed. `implementation-notes.md`, both
`pr-review-packet.md` files, `research.md`, `data-model.md`, the `contracts/` and
`checklists/` sets, the `artifacts/` pages and both `SPEC-MOC.md` files are run
exhaust for merged work and were removed with the folders, recoverable at the
boundary commit.

The `source-input:` frontmatter of `ART-008-slice-2-design-concept.md` names
slice 1's quickstart at its old path. That is a historical record of what the
scaffold read on 2026-08-24 and is retained unchanged, following the ART-005 and
ART-007 precedent that repoints live citations and leaves historical ledgers
alone.

## Corpus Relocation — the removal failed first, and why

**Slice 1's spec folder was not free to delete.** Removing both directories
turned 21 assertions red in `tests/speckit-pro/unit/test-feedback-sweep-parse.py`,
which hard-coded `FEATURE_ID = "art-008-feedback-sweep"` and read eight real
documents out of the live spec folder at test time.

The coupling was deliberate and carries real value. The documents are authored
prose that happens to contain the deny-set's own negative examples, so a
secret-scanning rule loosened back to a substring match fails on this corpus
before it fails on a reviewer's amendment. A fixture written to pass cannot do
that, because whoever writes it writes around the rules it is meant to catch.

**A shipped test may not depend on a folder this procedure removes.** The eight
documents were therefore moved to
`tests/speckit-pro/unit/fixtures/feedback-sweep/corpus/`, byte-identical, where
they are frozen test input rather than a live spec directory.

`FEATURE_DIR` in the test is **unchanged** at `specs/art-008-feedback-sweep`. Every
path the fixtures assert — an edit's `file`, a write-point verdict, a byproduct
location — keeps the `specs/<feature>/` shape a real run produces, because that
shape is part of what the fixtures pin. Only the reads move, through a
`corpus_path` translator, so the relocation cost no fixture its realism. A second
translator, `corpus_target`, serves `write_point` alone, because the shipped
`check_target` surface resolves `feature_dir` on disk and the corpus is what now
stands in for one.

**Proven load-bearing, not merely present.** Appending one line carrying an AWS
key pattern to `corpus/spec.md` drops the file from 6028/6028 to 6027/6028. The
corpus was restored byte-identical afterwards.

## The Durable Fix — so the next archive fails early instead of late

Relocating ART-008's corpus fixed ART-008. It did nothing for the next spec whose
test reads its own folder, and that failure would surface the same way: months
later, in a cleanup branch with no connection to the code that caused it.

**A run-time audit hook now catches the class.**
`tests/speckit-pro/lib/test_result.py` grew `install_specs_read_guard`, installed
by `run_counted`, which every test and Layer 1 validator in this repository calls.
A read of any path under `specs/` raises with a message naming the file and the
fix.

**Why a hook and not a source scan.** The distinction that matters is *data*
versus *access*, and no static pass draws it. A `specs/...` string is legitimate
data — the sweep fixtures assert dozens of them, because that is the shape a real
run produces — while opening one is the defect. Only the interpreter knows which
happened. A grep would have flooded on the strings and still missed the read that
actually broke, because that one reached the filesystem through a variable rather
than a literal.

**`os.stat` is deliberately unwatched.** `Path.resolve()`, `exists()` and
`is_dir()` on a specs-shaped path survive an archive on their own terms: the
folder stops existing and the probe answers False. Watching them would fail
exactly the path arithmetic that is safe, including the edit-allowlist assertion
this file's own test still makes in the realistic shape.

**Six suites opted out, and the opt-out is the point.** Each sweeps whatever
specs happen to exist rather than depending on a named one, which makes them
archive-safe by construction: `validate-moc-orphan`, `validate-moc-stale-index`,
`validate-agent-instructions`, `test-analysis-decision-ladder`,
`test-privacy-scan`, and `test-artifact-gallery`. They pass
`allow_live_specs=True` with a comment saying why. The declaration forces the
right question — *do you sweep what is there, or do you depend on a spec by
name?* — and only the second answer is a time bomb.

**The guard found four of those six by failing.** They were not predicted; the
first full run after installing it went 14198/14209 and named them.

**Known gap, accepted.** The hook is per-process, so a read inside a subprocess a
test spawns is unseen. Reaching one takes deliberately handing a `specs/...` path
to a helper; every in-process read — the kind that broke here — is covered.
Chasing the subprocess case was judged not worth the machinery.

**The rule is written down in both places that govern it.** Root `AGENTS.md`
Editing Boundaries and root `REVIEW.md` both extend their existing
"never couple a filename to a temporary spec ID" rule to cover reading from
`specs/<feature>/` at run time. `AGENTS.md` requires the two to stay in step.

`tests/speckit-pro/lib/test_lib.py` carries a unit for the guard covering all
three cases: naming a path is legal, probing its existence is legal, opening it
raises.

## Live-Reader Scan

The authoritative scan ran **before** any mutation, on the bare directory names,
the joined paths, and each `.process/` filename individually.

| Match | Nature | Action |
|---|---|---|
| `tests/speckit-pro/unit/test-feedback-sweep-parse.py` | eight real file reads out of the live spec folder | corpus relocated; reads redirected; see above |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-008 status prose, the Progress Tracking row, and the ART-009 Scope citation | reconciled to Complete / Archived; citation repointed |
| `docs/ai/specs/.process/ART-008-workflow.md` | the acceptance citation and the `Post: Retrospective` row | both repointed; surrounding prose retained as history |
| `docs/ai/specs/.process/ART-008-slice-2-workflow.md` | the `Post: Retrospective` row plus historical planning paths | row repointed; historical paths retained |
| `docs/ai/specs/.process/ART-008-slice-2-design-concept.md` | `source-input:` naming slice 1's quickstart | retained as the historical record |
| `docs/ai/specs/.process/autopilot-state.json` | live feature/branch identity and the archive-sweep block | **left unchanged**; see below |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | two generated backlinks into the removed folders | **regenerated** by the spec index, never hand-edited |
| `tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json` and `expected-envelopes.json` | 103 `feature_dir` strings and three edit `file` paths | **none needed**; they are data the helper echoes, and the reads that back them now resolve through `corpus_path` |
| `speckit-pro/.../capability-discovery.md`, `tests/.../validate-tool-scoping.py` | `art-008-feedback-sweep FR-008c` | spec-ID citations, not paths; retained |

## Why `autopilot-state.json` Was Not Touched

That file is a **single-slot pointer to the current run**, not a history log. Its
own schema says so: "the current-in-flight pointer for one run; the per-spec
durable record is the workflow file, which survives archive." The archive
procedure's rule follows from that — update it *only if it still points at the
completed spec*.

It no longer does. G56R-006 merged in #503 while this cleanup was in review and
reclaimed the slot, which is normal operation rather than a collision: one slot,
many specs. Writing ART-008's archive record into it would have deleted a live
pointer to a run whose pull request had just landed.

**This was caught by a conflict, but it was never really a merge problem.** An
earlier revision of this branch did edit the file, and the merge resolved that
edit cleanly in the wrong direction: git saw two textual changes and took mine,
silently replacing G56R-006's record. The rule above is what made the resolution
obvious, and it would have applied even with no conflict at all. ART-008's
durable record is the workflow file and this report; neither needs the pointer.

### A defect this cleanup did find

While the state edit still existed, setting `status` to `archived` failed the
state-evidence guard: the closed enum in
`speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`
admits `completed_archived`, and the schema's description names near-miss
spellings as retired precisely so they do not reappear. The edit is gone now, so
the correction went with it, but the trap is real and worth knowing about for the
next archive that *does* own the slot.

## Recovery Commands

Every removed tracked artifact is available from the cumulative boundary
`32043c45a60e7c38d15f0958bc4874f0362ea505`:

```text
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep/spec.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep/plan.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep/tasks.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep/SPEC-MOC.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep/.process/implementation-notes.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep/.process/pr-review-packet.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep-slice-2/spec.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep-slice-2/plan.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep-slice-2/tasks.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep-slice-2/SPEC-MOC.md
git show 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/art-008-feedback-sweep-slice-2/.process/pr-review-packet.md
```

To restore a whole folder, use `git restore --source=32043c45a --` with the
directory path.

## Cleanup Decision

`safeToApplyCleanup=true`. Both pull requests are merged, provenance and recovery
commands are recorded above, the corpus dependency that blocked removal is
resolved rather than worked around, and the suite is green.

## Known Gaps Carried Forward

- Slice 2 quickstart scenarios 3, 4 and 5 are undischarged and carried to ART-009.
- ART-008 slice 2's realized diff was 1250 production lines against an 800 block.
  The overrun is reference prose on both platforms rather than executable
  surface, and no gate produced a block verdict.

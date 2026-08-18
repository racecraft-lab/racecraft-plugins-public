# Archival Report - ART-007 Draft-PR Emission

## Mode

- **archiveMode**: merged-spec cleanup, single spec
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no run is in flight

## Provenance

**Every date in this report is UTC.** ART-007 shipped as a single pull request.
No ART-007 pull request remains open.

- **Source spec path**: `specs/art-007-draft-pr-emission/`
- **Cleanup branch**: `art-007-post-merge-hygiene`
- **Merged by**: `fgabelmannjr`

| PR | Title | Head branch | Merged at | Merge commit | Size |
|---|---|---|---|---|---|
| [#445](https://github.com/racecraft-lab/racecraft-plugins-public/pull/445) | `feat(speckit-autopilot): Open a draft pull request when the plan stage ends` | `art-007-draft-pr-emission` | `2026-08-18T21:06:52Z` | `1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9` | 99 files, +14625 −576 |

Base branch at merge was `main`. The branch was not stacked, so none of the
retargeting cost ART-003 recorded applies here.

- **Workflow file preserved**: `docs/ai/specs/.process/ART-007-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/ART-007-design-concept.md`
- **Acceptance record preserved**: `docs/ai/specs/.process/ART-007-manual-uat.md`
  (relocated by this cleanup; see **UAT Record Relocation**)
- **Retrospective**: none produced. The retrospective extension guards on a
  numeric branch pattern and this branch is namespaced, so it never ran. This
  archive does not invent one.
- **Branch commits**: 37, from `2c4edf01b` (design concept and workflow) to
  `b9dc0f8e0` (review-remediation closure)
- **CI outcome**: **19 pass, 1 skipped, 0 failures**, measured at the final PR
  head `b9dc0f8e0e2eecb9e3ae6c938273f4518e1bf7b2`, which is the head that gated
  the squash merge. The skip is `Windows ARM64 advisory smoke`, gated at
  `.github/workflows/container-preflight.yml:271` on
  `needs.windows-availability.outputs.arm64_enabled == 'true'` and marked
  `continue-on-error: true` at `:272`. It never started; the API reports an empty
  `steps` array. No CI anomaly is recorded.
- **CI run URLs**, five on the final head, all `success`:
  - PR Checks, later run <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32184813301>
  - PR Checks, earlier run <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32182937144>
  - Container Preflight <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32182937172>
  - CodeQL default setup <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32182934311>
  - CodeQL code quality <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32182935000>

  Two `PR Checks` runs executed against the same head, which is why the raw
  `statusCheckRollup` reports 30 entries against the deduped `gh pr checks` view's
  20. The deduped view is the authoritative final state.
- **Metadata gates**: `artifact-consistency`, `validate-docs`,
  `test (speckit-pro)`, `validate-release-note`, `validate-pr-title` and
  `validate-plugins` all pass, in both PR Checks runs. `detect` and
  `validate-workflows` also pass. No metadata gate failed, errored, or skipped
- **Review**: Copilot reviewed and reported "No blocking issues", having read 75
  of 97 changed files and generated no comments. Zero review threads, zero inline
  comments, zero issue comments. No human review was requested
- **Argos build/review URL**: not applicable; this repository runs no visual
  regression service
- **Artifact manifest**: the runner manifest and `.sha256` plus both `dist/`
  copies were regenerated inside the feature branch and are covered by the
  payload gates
- **Screenshot retention**: none committed
- **Expiration risk**: none for committed evidence

## Feature Summary

ART-007 ends the autopilot plan stage at an open draft pull request whose body
indexes the generated artifact pages, rather than ending privately. Three user
stories, 13 functional requirements, 8 success criteria, 54 tasks.

What shipped, in four parts:

| Part | Surface |
|---|---|
| A third packet mode, `draft` | `pr-packet.schema.json` conditional branch; mode-aware normalization and validation in `pr_emission.py` |
| A `Draft PR` workflow-file row | reader and grammar in `read_only.py`; placement and write rules in `workflow-file-protocol.md` |
| Stage-resolution corroboration | a closed six-status vocabulary computed in `read_only.py` from one orchestrator-supplied read-only `gh` observation |
| An `artifact-author` agent | `speckit-pro/agents/artifact-author.md` and `speckit-pro/codex-agents/artifact-author.toml` |

The repository suite moved from **7399 to 7525**.

### What the run itself taught

**Four design defects were caught by executing the contract rather than reading
it.** The draft-mode relaxation was first written as an added `allOf` branch,
which cannot relax anything, because `allOf` is conjunctive: every branch must
still hold. It was proved empirically and inverted into an `else` arm. Three
further schema sites and six producer sites were then found the same way.

**The highest-value find was an unnamed authority.** The draft contract cited a
"release-readiness title check" without naming the operation. The obvious
candidate, `validate-pr-workflow-contract`, would have made draft emission
structurally impossible on `prsg-`, `spec-`, `doc-` and `xplat-` specs, because
`spec_scope_from_changed_path` upper-cases those slugs while the draft contract
demands a lowercase scope. ART-007's own `art-` slug matches none of them, so the
wrong choice would have shipped green and broken four other namespaces. The
correct authority is `validate-pr-title` in `gates/release.py`.

**Measurement can silently read the wrong tree.** A helper probe reported a
failure that the suite did not, because `PYTHONPATH` resolved to the installed
2.25.0 plugin cache rather than the worktree. Every subsequent probe in this run
pinned `PYTHONPATH=speckit-pro`.

## Acceptance Result

Manual UAT was executed against the branch tree and is preserved in full at
`docs/ai/specs/.process/ART-007-manual-uat.md`.

Quickstart scenarios 1 through 4 pass. Beyond them, nine mode-conditional packets
and twenty corroboration probes reproduce every settled contract decision from
its own input, two of the probes fed live read-only `gh` output.

Three results are worth naming because prose alone could not establish them:

- **The relaxation did not leak.** A `single` packet stripped of verification
  evidence fails on *both* the schema `else` arm and the validator's hand-written
  assertion. Relaxing one without the other is the defect class the quickstart
  calls this feature's most likely single failure; neither happened.
- **`ok: 1` yields `skipped`, not a discrepancy.** Python treats `1 == True`, so a
  truthiness test would have accepted a malformed observation as a successful
  query and let it assert a discrepancy against a healthy run.
- **Both state allowlists read symmetrically.** An unrecognised state on the
  recorded pull request reports `match`, and an unrecognised state on a competing
  pull request is not a conflict. Reading either as "anything not `OPEN`" would
  produce a stop on no evidence.

**The live emission boundary was not exercised**, and the two reasons are
different in kind. A plan-stage run is **structurally** blocked: the component
that runs a plan stage is the installed plugin, still 2.25.0, whose `mode` enum
is `["single", "split"]` and which carries no emission prose, so running it
executes pre-ART-007 code that opens no draft pull request by construction. The
bare `gh pr create --draft` path, refresh-in-place, and closed-pull-request
handling are only **operator-gated**: they need a fork the operator is willing to
open and close draft pull requests on.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by this cleanup:

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` (mode-aware packet output)
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` (`Draft PR` row reader, corroboration)
- `speckit-pro/speckit_pro_runner/helpers/install.py` (eleventh required Codex agent)
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`
- `speckit-pro/skills/speckit-autopilot/SKILL.md` and
  `references/phase-execution.md`, `references/workflow-file-protocol.md`
- `speckit-pro/codex-skills/speckit-autopilot/**` mirrors of the above
- `speckit-pro/agents/artifact-author.md`
- `speckit-pro/codex-agents/artifact-author.toml`
- `tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json` and
  `bodies/valid-draft.md`
- `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`,
  `test-speckit-pro-mutation-helpers.py`
- `dist/claude/**` and `dist/codex/**` materializations
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/**` and regenerated proofs
- `docs-site/src/content/docs/reference/agents.md`

Historical evidence stays under `docs/ai/specs/.process/`:
`ART-007-design-concept.md`, `ART-007-workflow.md`, and `ART-007-manual-uat.md`.

## UAT Record Relocation

`specs/art-007-draft-pr-emission/.process/manual-uat.md` is **not** run exhaust
and was moved rather than deleted, matching the ART-002 and ART-003 precedent.

Unlike ART-003, **the citation reason is the decisive one here.** Three
references in two surviving files pointed at it and would all have dangled:

| Citing file | Nature |
|---|---|
| `docs/ai/specs/.process/ART-007-workflow.md` | the `Post: Manual UAT` row naming where the evidence lives |
| `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` (×2) | the HRNS-015 entry, which names it as **Key Files** evidence and in its provenance paragraph |

The HRNS-015 citation is load-bearing. That spec is `Ready` and unscaffolded, and
two of its eight scope bullets were routed there from this UAT; the record is the
only statement of their reproductions. Deleting it would have left a Ready spec
pointing at nothing.

Moved to `docs/ai/specs/.process/ART-007-manual-uat.md` with `git mv`. All three
citations were repointed, and a tree-wide re-scan confirms no reference to the old
path survives.

## Live-Reader Scan

The scan ran on the **bare directory name** as well as the joined path, because a
path assembled from `Path` components does not appear in a joined-path search. It
also covered each `.process/` filename and each contract filename individually.

| Match | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/ART-007-workflow.md` | prose citations plus one path to the UAT record | UAT citation repointed; prose left as the historical record |
| `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` | two paths to the UAT record in HRNS-015 | both repointed |
| `docs/ai/specs/.process/autopilot-state.json` | machine-written `workflow_file`, `feature_dir`, `branch` | status and `archive` block updated; paths left as the historical record |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | status prose and the Progress Tracking row | updated to Complete / Archived |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | a live backlink into `specs/…/SPEC-MOC.md` | **regenerated** by the spec index, never hand-edited |
| `tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json` and `bodies/valid-draft.md` | five path-shaped strings into the spec folder | **none needed**; proved inert below |

### The fixture paths were proved inert rather than assumed safe

`valid-draft.json` carries five strings that look like live paths:
`source_feature_dir`, `generated_title.source_evidence.source`,
`uat.uat_source`, `source_markers[0].source`, and `validation_result_path`. The
body fixture carries two more, pointing at `artifacts/*.html` pages that were
never generated on this branch at all.

Deleting the spec folder would break the shipped suite if the validator resolved
any of them. It does not. Pointing `source_evidence.source`, `uat_source` and
`source_markers[].source` at a nonexistent path each still validates `passed`.
`source_feature_dir` and `validation_result_path` are checked only **against each
other**: changing one alone fails on `input.identity.validation_result_path`,
while changing both consistently to a directory that does not exist validates
`passed`.

So the packet validator never touches the filesystem for a spec-folder path, and
the fixtures survive this removal. This was measured, not inferred.

**No live code, test, script, workflow, or docs-site reader depends on the spec
folder.** The full suite was re-run after the removal and reports 7525/7525.

### Two stale-but-inert strings are left in place on precedent

A first pass of this scan filtered on `*.md` and `*.json` and therefore missed a
Python constant. Corrected here:

- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:35` defines
  `DRAFT_PACKET_VALIDATION_DIR = "specs/art-007-draft-pr-emission/.process/pr-packets"`,
  used at `:1326` only to build a `validation_result_path` string for an
  in-memory packet.
- `tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json` carries the same
  directory in its own `source_feature_dir` and `validation_result_path`.

Neither is repointed, and the reason is the shipped fixture beside it.
`valid-single.json` declares
`source_feature_dir: specs/prsg-012-reviewer-ready-pr-packet-contract`, a folder
archived and removed long ago. **Packet fixtures keep the spec path they were
minted against**, and they stay valid because the validator resolves none of it.

This is a narrower call than ART-012's, which repointed five citations out of a
removed folder. Those were **comments only**. These are test data, and rewriting
a shipped fixture's identity fields during an archive cleanup would be an
unforced regression risk for no correctness gain.

### A methodology note

A concurrent agent sweep of this same question returned zero references. It is
recorded here as **invalid rather than corroborating**: it scanned after the
relocation and removal had already been applied, so it observed a tree in which
the references no longer existed. The authoritative scan is the manual one run
**before** any mutation, which found the three citations repointed above. Do not
read that zero as a second opinion.

### Why implementation-notes.md was not relocated

`specs/art-007-draft-pr-emission/.process/implementation-notes.md` resolves to
delete, matching the ART-012 precedent that governs this file type. No surviving
file cites ART-007's instance by path. Every live mention of
`implementation-notes.md` elsewhere in the tree is ART-012's shipped contract
naming the generic `specs/<branch>/.process/implementation-notes.md` pattern, not
this feature's copy. It is recoverable at the merge commit.

`quickstart.md`, `research.md`, `data-model.md`, the four `contracts/` files and
the three `checklists/` files are run exhaust for work already merged, and are
removed with the folder.

## Reviewability Outcome

| Stage | Reviewable LOC | Production files | Total files |
|---|---|---|---|
| Roadmap authoring | 217 | ~6 | ~10 |
| Declared at scaffold | ~287 | 11 | 16 |
| Measured at merge | no figure | 11 | 16 |

Both file counts landed **exactly on the declaration**. The measured file split
was 34 authored against 56 generated.

**There is no measured reviewable-LOC figure, and that is a tooling limit rather
than an omission.** The estimator scores a Markdown-and-Python repository 0 by
construction, so the post-implementation diff gate was decided on committed
evidence: setup gate warn/pass, plan-phase estimator 0 projected, ratified
no-split. The atomicity route was `one-navigable-PR`.

## Recovery Commands

```text
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/spec.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/plan.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/tasks.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/research.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/data-model.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/quickstart.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/SPEC-MOC.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/contracts/artifact-author-agent.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/contracts/draft-packet-mode.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/contracts/draft-pr-row.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/contracts/stage-corroboration.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/checklists/error-handling.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/checklists/requirements.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/checklists/state-management.md
git show 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9:specs/art-007-draft-pr-emission/.process/implementation-notes.md
git checkout 1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9 -- specs/art-007-draft-pr-emission
```

Fifteen tracked files. The UAT record is **not** in this list, because it was not
deleted: it is live at `docs/ai/specs/.process/ART-007-manual-uat.md`.

`.process/pr-packets/` was git-ignored and therefore never tracked. It is local
build exhaust and is not recoverable from history, by design.

## Known Gaps Carried Forward

- **T052 never ran**, and is recorded `[~]` rather than complete: 53 of 54 tasks.
  Quickstart scenarios 5 through 7 need an installed plugin carrying this feature,
  which exists only after a release cuts from this merge. The ledger is honest
  rather than back-filled, which is the opposite of the ART-011 shape.

- **Two spec-index defects were found and routed, not fixed.**
  `generate-spec-index` walks the filesystem rather than the git index, so
  git-ignored artifacts become committed backlinks, and no gate runs the check
  against the real repository tree because the Layer 1 test uses a fixture root.
  Both are now scope bullets 7 and 8 of HRNS-015. This cleanup hit the first one
  directly: the index had to be regenerated with `.process/pr-packets/` moved
  aside.

- **Two runner helpers are registered `deferred`**, so two post-implementation
  steps were decided on committed evidence rather than helper output:
  `generate-uat-skeleton` (no runbook skeleton could be produced, so the runbook
  author was correctly never spawned) and `final-reviewability-backstop`.

- **`artifact-author` ships ungoverned by the Layer 6 corpus**, by design. The
  corpus holds exactly twelve roles and the new agent is outside it, so no digest
  chain restaled. ART-009 owns the membership question.

- **The emission path has never run end to end.** Everything at the decision layer
  is confirmed from its own input, but no draft pull request has ever been opened
  by this code. The first real exercise is whichever spec runs a plan stage after
  the next release refreshes the installed plugin.

## Changed Files and Impact

| File | Change Summary |
|---|---|
| `.specify/memory/archive-reports/2026-08-18-art-007-post-merge-hygiene.md` | this report, new |
| `.specify/memory/changelog.md` | ART-007 entry appended |
| `.specify/memory/spec.md` | shipped behaviour, acceptance result and cleanup note appended |
| `.specify/memory/plan.md` | shipped surface, testing and cleanup appended |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-007 marked Complete / Archived; status prose updated; ART-008 and ART-010 moved to Ready |
| `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` | two HRNS-015 citations repointed to the relocated UAT record |
| `docs/ai/specs/.process/ART-007-manual-uat.md` | preserved from the spec's `.process/` directory by `git mv` |
| `docs/ai/specs/.process/ART-007-workflow.md` | UAT-record citation repointed |
| `docs/ai/specs/.process/autopilot-state.json` | `status` archived, `archive` block recorded |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | regenerated by the spec index; the dead ART-007 backlink removed |
| `specs/art-007-draft-pr-emission/**` | 15 tracked files removed, plus the UAT record relocated |

## Feature Status

The spec's own `spec.md` status line is **superseded by cleanup** and was not
flipped: the file does not survive this archive, so the edit would exist only to
be deleted in the same commit. The merged state is recoverable verbatim from the
commands above. This matches the ART-002, ART-003, ART-011, ART-012 and ART-014
precedent.

## Constitution Compliance

No conflict. This archive changes documentation and project memory only.

- **I. Plugin Structure Compliance** — untouched; no plugin layout changes.
- **II. Cross-Platform Runtime & Script Safety** — untouched; no repository
  tooling changes, and no Bash or `jq` dependency is added.
- **III. Semantic Versioning** — untouched; no manifest or version changes.
- **IV. Test Coverage Before Merge** — the suite is unchanged at 7525 and no test
  file is edited. Nothing this archive touches is asserted by a test other than
  the regenerated index, and the packet fixtures were proved inert against the
  removal above.

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git mv` the UAT record to
  `docs/ai/specs/.process/ART-007-manual-uat.md` and repoint its three citations,
  then `git rm -r specs/art-007-draft-pr-emission` after merge provenance and a
  tree-wide live-reader scan on the bare directory name
- **cleanupBranch**: `art-007-post-merge-hygiene`
- **blockedBy**: none

Gate-by-gate:

| # | Gate | Result |
|---|---|---|
| 1 | Cleanup explicitly requested | pass |
| 2 | Target is not `--current-target` | pass; no run in flight |
| 3 | Merged, with recorded PR URL and merge commit | pass; #445 `1d58e5cb` |
| 4 | Archive completed successfully in this run | pass |
| 5 | Report includes recovery commands per artifact | pass; 16 commands above |
| 6 | Worktree clean before cleanup | pass |
| 7 | Active branch is a safe base branch | **pass with a recorded deviation**, below |
| 8 | No history rewrite, no reliance on post-merge CI mutating `main` | pass |

**Gate 7 deviation.** The gate names `main` as the normal cleanup branch. This
archive runs on `art-007-post-merge-hygiene`, cut from `main` at `1d58e5cb`,
because this repository forbids committing directly to `main` and lands every
change through a pull request. The gate's intent — do not run cleanup from an
unrelated feature branch carrying unmerged work — is satisfied: the branch was cut
for this archive alone and contains nothing else. The precedent is PR #442 for
ART-003, PR #441 for ART-011, PR #438 for ART-014, PR #431 for ART-002 and
ART-012, and PR #424 for ART-006.

## Defaults Applied

- **Agent knowledge step skipped.** The skill would update `AGENTS.md`, but this
  repository's own agent-file hygiene forbids release notes, feature plans and
  process history in agent files. Where the skill text and this repository's rules
  disagree, the repository wins.
- **`.specify/feature.json` existed and is git-ignored.** It pinned
  `specs/art-007-draft-pr-emission`, a directory this cleanup removes, so it was
  deleted locally. It is untracked, so this does not reach the commit, and its
  absence is the expected state for a post-merge worktree with no active feature.
- No scope modifiers were passed, so all archival artifacts were updated.

## Scoping

Invoked on ART-007 specifically. After this cleanup `specs/` holds `.gitkeep` and
`brand-001-racecraft-identity-system`.

ART-007 was the ART family's only archive candidate. ART-001, ART-002, ART-003,
ART-006, ART-011, ART-012 and ART-014 are already archived; every other ART entry
is Ready or Pending with no spec folder on disk. BRAND-001 is out of family and is
not a candidate regardless: its planning package merged in PR #432, but the spec
is scaffolded and parked with phases still pending, so its folder is active work
rather than merged residue.

**ART-005 is in flight in three open pull requests** (#444, #446, #447) and is not
touched by this archive. It is a roadmap sibling, not an ART-007 dependency, and
it has no spec folder under `specs/`. Its pull requests share only generated
artifacts with #445 plus the `html-artifacts-technical-roadmap.md` file this
archive edits, so whichever lands second will need to merge `main` and regenerate.

## Downstream State

ART-007's completion unblocks **two** specs, not one:

- **ART-008 (Feedback Sweep)** was blocked by ART-007 alone. It is now Ready.
- **ART-010 (Final-PR Writeup, Companions & Ready Flip)** was blocked by ART-007
  alone, its ART-003 dependency having been satisfied by PRs #435/#436/#439 and
  its ART-012 dependency by PR #426. **Every ART-010 dependency is now satisfied.**

The ART family's ready set is now ART-004, ART-005, ART-008, ART-009 and ART-010,
plus ART-015 through ART-020.

# Archival Report - XPLAT-010 Repository Bash Confinement and CI Dispatch Guard

## Mode
- **archiveMode**: single-feature post-merge cleanup
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup XPLAT-010`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-010-repository-bash-confinement` | eligibleForArchive -> archived | removed (cleanup applied) | The complete no-gap stack merged through PRs #311-#328; final recovery source `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29` contains the complete active spec and implementation tree |

## Excluded Current Spec
`None` (all 18 XPLAT-010 PRs are merged; cleanup runs from current `main` on
`codex/xplat-010-archive-cleanup`)

## Provenance
| PR | Title | Merged at | Merge commit | Head branch |
|----|-------|-----------|--------------|-------------|
| [#311](https://github.com/racecraft-lab/racecraft-plugins-public/pull/311) | `docs(xplat-010): record confinement design and process evidence` | `2026-07-11T15:30:35Z` | `2be9531748d6f3d1878a43464f9e919387e7098e` | `xplat-010-review/00-process` |
| [#312](https://github.com/racecraft-lab/racecraft-plugins-public/pull/312) | `chore(xplat-010): remove orphaned Bash test scripts` | `2026-07-11T15:59:08Z` | `73442250e283d7fd64139d5275821227738579a1` | `xplat-010-review/01-foundation` |
| [#313](https://github.com/racecraft-lab/racecraft-plugins-public/pull/313) | `fix(xplat-010): restore spec-size estimation` | `2026-07-11T16:28:51Z` | `6bca7852919c0fa2e4fd3e1e7ded254df85d6ae9` | `xplat-010-review/02-us14` |
| [#314](https://github.com/racecraft-lab/racecraft-plugins-public/pull/314) | `feat(xplat-010): replace Bash suite orchestration with Python` | `2026-07-11T16:42:30Z` | `0a7bd98d2aafe07704140684d72759af47885f29` | `xplat-010-review/03-us1` |
| [#315](https://github.com/racecraft-lab/racecraft-plugins-public/pull/315) | `test(xplat-010): port structural validator batch one` | `2026-07-11T16:56:20Z` | `fc12ae4fa14ae4b9ddf663ad4d0ef191fb2a279f` | `xplat-010-review/04-us2` |
| [#316](https://github.com/racecraft-lab/racecraft-plugins-public/pull/316) | `test(xplat-010): port structural validator batch two` | `2026-07-11T16:56:43Z` | `9010de0513e66e2055d09579751a6ce95b1d0869` | `xplat-010-review/05-us3` |
| [#317](https://github.com/racecraft-lab/racecraft-plugins-public/pull/317) | `test(xplat-010): port remaining structural checks` | `2026-07-11T16:57:07Z` | `503b4ea81ddb881cd96f42c55c9f74b705584060` | `xplat-010-review/06-us4` |
| [#318](https://github.com/racecraft-lab/racecraft-plugins-public/pull/318) | `test(xplat-010): port toolchain and Layer 5 dispatch` | `2026-07-11T16:57:29Z` | `618b5699a18157d88730d9fdf1f1dcae19ae4bab` | `xplat-010-review/07-us5` |
| [#319](https://github.com/racecraft-lab/racecraft-plugins-public/pull/319) | `refactor(xplat-010): port repository helpers and hooks` | `2026-07-11T16:57:52Z` | `755135cfead82347807787e0ba89715fd1951810` | `xplat-010-review/08-us6` |
| [#320](https://github.com/racecraft-lab/racecraft-plugins-public/pull/320) | `test(xplat-010): port transcript helpers and tools` | `2026-07-11T16:58:14Z` | `f2675c2b5afac2b9c4417bcdf189aaa0a08223cb` | `xplat-010-review/09-us7` |
| [#321](https://github.com/racecraft-lab/racecraft-plugins-public/pull/321) | `test(xplat-010): port Layer 7 replay runners` | `2026-07-11T16:58:37Z` | `aa59327cc43aa8df92e4972637447659ed1c470b` | `xplat-010-review/10-us7b` |
| [#322](https://github.com/racecraft-lab/racecraft-plugins-public/pull/322) | `test(xplat-010): port Layer 8 parity harness` | `2026-07-11T16:58:59Z` | `32b50aee87af70c0caaa2040dad0c8f789fdce3f` | `xplat-010-review/11-us8` |
| [#323](https://github.com/racecraft-lab/racecraft-plugins-public/pull/323) | `test(xplat-010): port live evaluation runners` | `2026-07-11T16:59:22Z` | `ad88b8db641d29f47b677134d8bc5c6ec74d5ca9` | `xplat-010-review/12-us9` |
| [#324](https://github.com/racecraft-lab/racecraft-plugins-public/pull/324) | `feat(xplat-010): enforce repository Bash confinement` | `2026-07-11T16:59:45Z` | `9cd8b632c51b2768b498e5051fbfacb25f7df887` | `xplat-010-review/13-us10` |
| [#325](https://github.com/racecraft-lab/racecraft-plugins-public/pull/325) | `test(xplat-010): add Linux and Windows runner checks` | `2026-07-11T17:00:10Z` | `98ad2e2ea6ef2a7f94b5840f3b0daad817eca503` | `xplat-010-review/14-us11` |
| [#326](https://github.com/racecraft-lab/racecraft-plugins-public/pull/326) | `feat(xplat-010): validate consumer release-note blocks` | `2026-07-11T17:00:33Z` | `361398770d2f05508abe5224d7a6a7b4ae3ae5e0` | `xplat-010-review/15-release-contract` |
| [#327](https://github.com/racecraft-lab/racecraft-plugins-public/pull/327) | `feat(xplat-010): compose consumer-facing release highlights` | `2026-07-11T17:00:57Z` | `8497cd0f3ef4f4c63b396b4f53267a09af14de90` | `xplat-010-review/16-release-composition` |
| [#328](https://github.com/racecraft-lab/racecraft-plugins-public/pull/328) | `chore(xplat-010): finalize integrated verification evidence` | `2026-07-11T17:01:20Z` | `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29` | `xplat-010-review/17-polish` |

- **Source spec path**: `specs/xplat-010-repository-bash-confinement/`
- **Workflow file**: `docs/ai/specs/.process/XPLAT-010-workflow.md`
- **Design concept**: `docs/ai/specs/.process/XPLAT-010-design-concept.md`
- **Preserved evidence**: all ten `docs/ai/specs/.process/XPLAT-010-*` files
- **Base branch**: `main`
- **Final stack merge commit**: `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`
- **Final stack tree**: `0d5a46bfa28efbca13d7f49539369705bd58d76f`
- **Final branch state**: all 18 `xplat-010-review/*` branches deleted
- **Merge-policy state**: squash-only restored (`allow_merge_commit=false`,
  `allow_rebase_merge=false`, `allow_squash_merge=true`)
- **Metadata gates**: `main` non-strict branch protection requires exactly five
  GitHub Actions checks: `validate-plugins`, `validate-pr-title`,
  `validate-release-note`, `container-preflight-linux-amd64`, and
  `container-preflight-linux-arm64`
- **Expiration risk**: committed source/process evidence and durable GitHub run
  URLs have no repository-retention dependency. The manual-run artifacts expire
  on `2026-07-25` between `17:09Z` and `17:23Z`; downloaded `/private/tmp`
  inspection copies are transient and are not committed evidence

The first three PRs were squash-merged. Because squash discarded stack
ancestry, each dependent head then required an exact restack. The repository
temporarily enabled merge commits for #314-#328 so each reviewed head remained
the second parent of a contiguous first-parent chain. The final `main` tree is
byte-identical to the verified stack tip, and the repository's normal
squash-only policy was restored immediately afterward.

## Feature Summary
XPLAT-010 completed repository-wide Bash confinement on top of the XPLAT-009
plugin/payload cleanup. It replaced the active repository test orchestration,
structural validators, helper scripts, hooks, replay/parity/evaluation runners,
and release tooling with Python 3.11+ standard-library entrypoints; made
`tests/speckit-pro/suite-manifest.json` authoritative; added a repo-wide
confinement gate with a fixed release-excluded vendored `.specify/**` allowlist;
restored `estimate-spec-size`; added Linux container and advisory Windows
preflight workflows; and added deterministic consumer release-note validation
and Highlights composition.

The final neutral-PATH deterministic suite passed `2512/2512` at the frozen
implementation tip: Layer 1 `1373/1373`, Layer 4 `953/953`, and Layer 5
`186/186`. All 18 packet/body/validation triplets passed, and the final merged
tree matches the stack tip exactly.

## Acceptance And Remaining Boundaries
- **T108 complete**: manual `main` run
  [29161090549](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29161090549)
  succeeded at `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29` with all eight
  artifacts, both Linux heavy jobs and sentinels passing, Windows x64 smoke
  passing, and Windows ARM64 recorded `available:true` / `enabled:false`
  without queueing the ARM64 label.
- Relevant-path run
  [29159969108](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29159969108)
  passed both amd64 and arm64 heavy jobs and retained eight artifacts. Docs-only run
  [29161055742](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29161055742)
  skipped heavy jobs, passed both sentinels, and retained five artifacts.
  Failure-propagation run
  [29159559914](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29159559914)
  failed both sentinels as intended and retained five artifacts.
- Supplemental run
  [29141599499](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29141599499)
  proves actual Linux heavy-job/default-suite failure propagation to both
  sentinels and retained all eight artifacts. Run
  [29140365960](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29140365960)
  proves a Windows x64 smoke failure remains advisory while the overall
  workflow succeeds.
- Constitution [PR #331](https://github.com/racecraft-lab/racecraft-plugins-public/pull/331)
  trigger canaries passed for `opened` (run
  [29161598122](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29161598122)),
  `synchronize`
  ([29161613608](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29161613608)),
  `ready_for_review`
  ([29161619193](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29161619193)),
  and `reopened`
  ([29161647866](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/29161647866));
  each trigger run retained five artifacts.
- **T117 complete**: live `main` branch protection is non-strict and requires
  exactly `validate-plugins`, `validate-pr-title`, `validate-release-note`,
  `container-preflight-linux-amd64`, and
  `container-preflight-linux-arm64` from GitHub Actions.
- The required constitution amendment completed through PR #331 at
  `b537e3b43ca20d8f6e8b6e9430d797444462f2e9` on
  `2026-07-11T17:42:37Z` before this archive cleanup; this archive branch does
  not edit `.specify/memory/constitution.md`.
- The SpecKit index-tooling defect is repaired in a separate isolated branch
  before this archive cleanup runs.
- Public native Windows/macOS/Linux claims remain blocked solely by the
  preserved XPLAT-008 operator UAT matrix. XPLAT-010 preflight evidence is not
  native installed-plugin UAT.
- Durable archive evidence is the run URLs and summarized outcomes above.
  Downloaded artifact copies under `/private/tmp` are local inspection state,
  are not committed, and must not be cited as durable repository evidence.
- Release publication and the first real deterministic Highlights rewrite are
  handled outside this archive cleanup.

## Canonical Artifacts
- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/run-all.py`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/layer1-structural/`
- `tests/speckit-pro/unit/`
- `tests/speckit-pro/parity/bash-to-python/`
- `tests/speckit-pro/run-container-preflight.py`
- `tests/speckit-pro/run-hosted-windows-preflight.py`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `scripts/release_note_policy.py`
- `scripts/compose-release-notes.py`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/container-preflight.yml`
- `.github/workflows/release.yml`
- `.github/pull_request_template.md`
- `docs/ai/specs/.process/XPLAT-010-design-concept.md`
- `docs/ai/specs/.process/XPLAT-010-workflow.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-done-when-traceability.md`
- `docs/ai/specs/.process/XPLAT-010-no-gap-result.json`
- `docs/ai/specs/.process/XPLAT-010-pr-body.md`
- `docs/ai/specs/.process/XPLAT-010-pr-packet.json`
- `docs/ai/specs/.process/XPLAT-010-retrospective.md`
- `docs/ai/specs/.process/XPLAT-010-suite-parity-result.json`
- Purpose-based repository-confinement and planner fixtures preserved under
  `tests/speckit-pro/unit/fixtures/`

## Recovery Commands
```text
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/spec.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/plan.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/tasks.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/research.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/data-model.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/quickstart.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/SPEC-MOC.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/checklists/integration.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/checklists/reliability.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/checklists/requirements.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/checklists/security.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/contracts/confinement-allowlist.schema.json
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/contracts/count-parity-baseline.contract.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/contracts/estimate-spec-size.schema.json
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/contracts/release-note-block.contract.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/contracts/repo-bash-confinement-result.schema.json
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/contracts/suite-manifest.schema.json
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/.process/prs.json
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/.process/publication-tail.json
git checkout ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29 -- specs/xplat-010-repository-bash-confinement
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-010 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended the product summary, preserved requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended the technical approach, verification strategy, and cleanup note |
| `.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-010 archive, technology, and recent-change notes |
| `CLAUDE.md` | Replaced the active-plan pointer and reconciled current Python/CI/branch-protection guidance |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-010 completed/archived and retained the T108, constitution, release, and XPLAT-008 UAT boundaries |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-010 entry with archive and preserved-evidence pointers |
| `docs/ai/specs/.process/autopilot-state.json` | Recorded all 18 merged PRs and post-merge archive state |
| `docs/ai/specs/.process/XPLAT-010-workflow.md` | Reconciled merged-stack, completed T108/T117 evidence, and remaining release boundary |
| `docs/ai/specs/.process/XPLAT-010-retrospective.md` | Reconciled merge outcome and follow-up boundaries |
| `docs/ai/specs/.process/XPLAT-010-done-when-traceability.md` | Reconciled merge, completed T108, and branch-protection evidence |
| `docs/ai/specs/.process/XPLAT-010-count-ledger.md` | Added final merge and branch-protection facts |
| `tests/speckit-pro/unit/fixtures/` | Preserved purpose-based contract and planner inputs required after active-spec cleanup |
| `tests/speckit-pro/unit/test-repo-bash-confinement.py` | Repointed live schema reads away from active `specs/**` |
| `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | Repointed and purpose-renamed the large migration planner fixture test |
| `docs-site/src/content/docs/reference/tests.md` | Regenerated after fixture relocation |
| `specs/xplat-010-repository-bash-confinement/` | Removed from active `specs/**` after dependency decoupling |

## Verification Commands
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py --layer 4`
- `python3 tests/speckit-pro/run-all.py`
- SpecKit index generation in write mode followed by check mode
- `node docs-site/scripts/generate-reference-pages.mjs --check`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `git diff --check`

## Scoped Metadata Verification

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`: PASS
- Archive-state assertions: PASS (18/18 merged PR records, `main` bases,
  merge SHAs, empty active inventory, T108 complete, exact five-check rule)
- Markdown fence/newline sanity across all 12 edited Markdown files: PASS
- `git diff --check`: PASS
- `PYTHONDONTWRITEBYTECODE=1 python3 tests/speckit-pro/run-all.py --layer 1`:
  PASS (`1373/1373`; toolchain preflight ok)

The parent must rerun fixture-specific tests, index write/check, docs-reference
generation/check, and the full default suite after integrating the separate
fixture relocation, active-spec deletion, constitution PR, and index-tooling
repair.

## Feature Status
`Completed / Archived`. T108 and T117 are complete. The active spec folder is
removed from `specs/**`; implementation history remains
recoverable from `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`. Public native
platform claims remain blocked by the XPLAT-008 operator UAT matrix.

## Constitution Compliance
The implementation required a separate constitution amendment because the
pre-XPLAT-010 document named retired Bash commands. PR #331 completed that
governance change at `b537e3b43ca20d8f6e8b6e9430d797444462f2e9` before archive
cleanup. The amendment is not silently reinterpreted or folded into this
cleanup. The cleanup itself preserves the Python-only
runtime, test, path, subprocess, JSON, and Bash-confinement boundaries.

## Conflicts Resolved
- Squash merges of #311-#313 discarded stack ancestry and caused each next
  dependent PR to conflict. Exact restacks repaired those heads; merge commits
  for #314-#328 then preserved every reviewed slice as an exact second parent.
- Live tests depended on the active spec's result schema and planner `tasks.md`.
  Purpose-based fixture copies and test path updates decouple those readers
  before the active spec is removed.
- Roadmap, workflow, project guidance, and autopilot state still described an
  open stack. They now record the merged 18-PR chain and deleted branches.
- T117 documentation lagged live repository configuration. Project evidence now
  records the exact five required status checks on `main`.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-010-repository-bash-confinement`
- **cleanupBranch**: `codex/xplat-010-archive-cleanup`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Only the merged XPLAT-010 active spec was eligible for cleanup.
- Historical XPLAT-010 process evidence under `docs/ai/specs/.process/` remains
  committed.
- `.specify/feature.json` was absent and was not created.
- Historical packet paths and object IDs remain frozen snapshots rather than
  being rewritten to post-merge paths.
- The fixed vendored `.specify/**` Bash allowlist remains release-excluded.

## Scoping
Full archive cleanup for XPLAT-010 only. It does not edit the constitution,
plugin source, generated payloads, package/version files, repository settings,
or the release PR. XPLAT-001 through XPLAT-010 are archived; native platform
claims remain held by XPLAT-008 UAT.

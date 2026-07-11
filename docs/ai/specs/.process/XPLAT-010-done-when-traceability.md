# XPLAT-010 Done-When Traceability

Fresh traceability for the ten roadmap Done When outcomes in
`docs/ai/specs/.process/XPLAT-010-workflow.md`. This record maps each outcome to
the current specification requirements, current 18-marker delivery topology,
task IDs, purpose-based implementation paths, and verification evidence.

## Evidence Snapshot

- Frozen implementation head: `a7b2d27b12fdc5051dfa4829c94f92752e2f5146`
  (tree `a1c42735d35619bbd0a4a90a42c57ab9e578848e`).
- Verified date: 2026-07-11 (America/Chicago).
- Stack record:
  `specs/xplat-010-repository-bash-confinement/.process/prs.json`, containing
  18 open records for PRs #311 through #328 with exact adjacent bases.
- Packet evidence:
  `specs/xplat-010-repository-bash-confinement/.process/pr-packets/`, containing
  18 directories and exactly one `body.md`, `packet.json`, and passing
  `validation.json` in each directory.
- Cumulative parity evidence:
  `docs/ai/specs/.process/XPLAT-010-suite-parity-result.json`, status `passed`,
  verified at the emitted stack tip against the purpose-based baseline and
  current test paths.

This snapshot records local and generated evidence only. It does not configure
branch protection, merge PRs, or promote local checks into hosted evidence.
If the parent closeout changes a branch OID, it must regenerate the affected
packet before final synchronization.

## Source Reconciliation

The spec and plan preserve the original 13-slice / 15-PR implementation
headline. Current `tasks.md`, `prs.json`, and the packet set define the emitted
delivery topology used here: 18 no-gap review markers. The difference is
explicit:

- Foundation and Polish are emitted review units.
- The former PR 12 is split into PR 12a and PR 12b because its combined
  production LOC exceeded the blocking threshold without a waiver.
- PR 13 is emitted early, after PR 1, to restore the estimator.

Planner marker IDs are delivery ordinals, not the product `[USn]` labels on
individual tasks. Branch names retain historical aliases, so this artifact
always records marker ID, task range, and branch together.

## Current Marker Map

| Order | PR | Marker | Tasks | Delivery purpose | Emission branch |
|------:|---:|--------|-------|------------------|-----------------|
| 1 | #311 | `foundation` | T001-T004 | Confinement design and process evidence | `xplat-010-review/00-process` |
| 2 | #312 | `us1` | T005-T007 | PR 1 orphan Bash-test deletion and disposition ledger | `xplat-010-review/01-foundation` |
| 3 | #313 | `us16` | T121-T130 | PR 13 restored spec-size estimator | `xplat-010-review/02-us14` |
| 4 | #314 | `us2` | T008-T017 | PR 2 Python suite orchestration | `xplat-010-review/03-us1` |
| 5 | #315 | `us3` | T018-T028 | PR 3a structural validator batch one | `xplat-010-review/04-us2` |
| 6 | #316 | `us4` | T029-T039 | PR 3b structural validator batch two | `xplat-010-review/05-us3` |
| 7 | #317 | `us5` | T040-T045 | PR 4 remaining structural checks | `xplat-010-review/06-us4` |
| 8 | #318 | `us6` | T046-T053 | PR 5 toolchain and Layer 5 dispatch | `xplat-010-review/07-us5` |
| 9 | #319 | `us7` | T054-T061 | PR 6 repository helper and hook ports | `xplat-010-review/08-us6` |
| 10 | #320 | `us8` | T062-T066 | PR 7a transcript helper and tool ports | `xplat-010-review/09-us7` |
| 11 | #321 | `us9` | T067-T072 | PR 7b Layer 7 replay runner ports | `xplat-010-review/10-us7b` |
| 12 | #322 | `us10` | T073-T080 | PR 8 Layer 8 parity harness port | `xplat-010-review/11-us8` |
| 13 | #323 | `us11` | T081-T087 | PR 9 live evaluation runner ports | `xplat-010-review/12-us9` |
| 14 | #324 | `us12` | T088-T099 | PR 10 repository Bash confinement gate | `xplat-010-review/13-us10` |
| 15 | #325 | `us13` | T100-T108 | PR 11 Linux and Windows preflight checks | `xplat-010-review/14-us11` |
| 16 | #326 | `us14` | T109-T112 | PR 12a consumer release-note validation | `xplat-010-review/15-release-contract` |
| 17 | #327 | `us15` | T113-T120 | PR 12b consumer release-note composition | `xplat-010-review/16-release-composition` |
| 18 | #328 | `polish` | T131-T136 | Integrated verification and review packets | `xplat-010-review/17-polish` |

## Done-When Matrix

Status meanings:

- **Verified**: current implementation and direct local evidence satisfy the
  outcome.
- **Local contract verified; hosted pending**: repository behavior is covered
  locally, but the outcome explicitly requires GitHub-hosted evidence or
  configuration that is not yet recorded.
- **Partial**: material implementation evidence exists, but a required final
  environment or aggregate check is still missing.

### DW-01 - Repository scan and vendored exclusions

**Outcome:** A repository-wide scan outside `.github/workflows/` finds no
non-allowlisted Bash scripts; the ten vendored `.specify/**` helpers are
documented, allowlisted, and excluded from release-readiness evidence.

- Requirements: FR-001, FR-003, FR-004, FR-005; SC-001.
- Marker/tasks: `us12`, T088-T099.
- Current paths:
  `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`,
  `speckit-pro/speckit_pro_runner/gates/registry.py`,
  `speckit-pro/speckit_pro_runner/gates/release.py`,
  `tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json`,
  `tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/repo-bash-confinement.json`,
  `tests/speckit-pro/unit/test-repo-bash-confinement.py`.
- Evidence: the live guard scanned 1,699 tracked files through
  `git ls-files -z`, returned exit 0 with `blocking_count: 0` and
  `script_file_count: 0`, and reported exactly ten
  `vendored_specify_helper` findings, all with
  `release_readiness_excluded: true`. `git ls-files '*.sh'` returned only
  those ten paths. The focused guard suite passed 47/47.
- Status: **Verified**.

### DW-02 - Workflow shell is dispatch glue only

**Outcome:** GitHub workflow shell contains only direct CI/CD dispatch, with no
embedded plugin validation, packaging, install, release, or runtime logic.

- Requirements: FR-026.
- Marker/tasks: `us6`, T048-T053; durability coverage in `us12`.
- Current paths: `.github/workflows/pr-checks.yml`,
  `.github/workflows/container-preflight.yml`, `.github/workflows/release.yml`,
  `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`,
  `tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json`,
  `tests/speckit-pro/unit/test-speckit-pro-gates.py`,
  `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py`, and
  `tests/speckit-pro/layer1-structural/validate-release-workflow.py`.
- Evidence: the targeted gate test
  `test_workflow_dispatch_glue_is_only_allowed_for_direct_python_gate_dispatch`
  passed. The current workflow validators passed 49/49 and 41/41.
- Status: **Verified**.

### DW-03 - Active repository tooling runs without Bash or jq

**Outcome:** Active tests, evals, payload builders, release-readiness checks,
install-verification paths, hooks, and helper tools run through Python without
repository-local Bash or `jq`.

- Requirements: FR-006, FR-007, FR-008, FR-009, FR-010, FR-014, FR-015,
  FR-026; SC-002.
- Marker/tasks: `us2` through `us12`, plus estimator marker `us16`.
- Current paths: `tests/speckit-pro/suite-manifest.json`,
  `tests/speckit-pro/run-all.py`, `tests/speckit-pro/run-layer-scripts.py`,
  `tests/speckit-pro/layer1-structural/`,
  `tests/speckit-pro/layer2-trigger/`,
  `tests/speckit-pro/layer3-functional/`,
  `tests/speckit-pro/layer5-tool-scoping/`,
  `tests/speckit-pro/layer6-efficiency/`,
  `tests/speckit-pro/layer7-integration/`,
  `tests/speckit-pro/layer8-parity/`, `scripts/refresh-local-plugin.py`,
  `scripts/sync-marketplace-versions.py`, `.claude/hooks/guard-version-triplet.py`,
  and `.claude/hooks/validate-structural.py`.
- Evidence: the manifest has zero `shell-legacy-transitional` entries. Focused
  contracts passed for hooks (22/22), trigger runners (26/26), integration
  runners (31/31), parity runner (33/33), and efficiency portability (18/18).
  Six targeted gate tests also proved manifest authority and rejected
  `shell=True`, `os.system`, and command-string subprocess use.
- Final neutral-PATH evidence: with Bash and `jq` absent, the deterministic
  suite passed `2512/2512`: Layer 1 `1373/1373`, Layer 4 `953/953`, and Layer 5
  `186/186`. The read-only helper suite also passed `42/42`.
- Task state: T133 is complete.
- Status: **Verified**.

### DW-04 - Runtime name-and-count parity

**Outcome:** Ported checks preserve the frozen runtime inventories without
count drops, silent renames, or undocumented mismatches.

- Requirements: FR-010, FR-011, FR-012, FR-013; SC-003.
- Marker/tasks: `us16`, `us3` through `us12`, and `polish` T131.
- Current paths: `tests/speckit-pro/parity/bash-to-python/`,
  `docs/ai/specs/.process/XPLAT-010-count-ledger.md`,
  `docs/ai/specs/.process/XPLAT-010-suite-parity-result.json`,
  `tests/speckit-pro/lib/capture_baseline.py`, and
  `tests/speckit-pro/lib/test_result.py`.
- Evidence: the cumulative artifact reports 54 true-port rows: 51 exact
  name-and-count ports and three documented replacements. Independent path,
  baseline `TOTAL`, historical count, current count, and roll-up checks found
  zero count drops, zero silent renames, and zero undocumented mismatches. The
  three explicit replacements are marketplace-sync removal of `jq`, the
  deliberate Layer 8 `semantic-equivalent` LLM non-goal, and terminal
  toolchain coverage growth from 26 to 27 checks.
- Task state: T131 is complete; the generated result is accepted as the
  cumulative parity record for the emitted stack tip.
- Status: **Verified**.

### DW-05 - Linux container preflight

**Outcome:** Linux amd64 and arm64 preflight use the same runner and
release-gate entrypoints as CI and gate relevant pull requests.

- Requirements: FR-017, FR-018, FR-020, FR-027; SC-008.
- Marker/tasks: `us13`, T100-T108.
- Current paths: `.github/workflows/container-preflight.yml`,
  `tests/speckit-pro/run-container-preflight.py`,
  `tests/speckit-pro/unit/test-hosted-windows-preflight.py`, and
  `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py`.
- Local evidence: the hosted Windows preflight helper contract passed 33/33 and the workflow
  sentinel validator passed 49/49, including the two stable Linux sentinels,
  relevant-change selection, docs-only no-op behavior, shared runner requests,
  least-privilege permissions, and non-masking uploads. The ARM64 exact
  pinned-container overlay with hydrated `tasks.md` passed 42/42.
- Hosted gap: T108 remains open. Actual Linux container jobs, uploaded
  artifacts, required-context behavior, all configured PR events, and the
  post-merge manual dispatch are not established by local tests.
- Status: **Local contract verified; hosted pending**.

### DW-06 - Advisory Windows smoke evidence

**Outcome:** Windows x64 and ARM64 smoke are advisory where configured, record
availability, and are never represented as native installed-plugin UAT.

- Requirements: FR-019, FR-020, FR-027; SC-008.
- Marker/tasks: `us13`, T100-T108.
- Current paths: `.github/workflows/container-preflight.yml`,
  `tests/speckit-pro/run-container-preflight.py`,
  `tests/speckit-pro/run-hosted-windows-preflight.py`, and
  `tests/speckit-pro/unit/test-hosted-windows-preflight.py`.
- Local evidence: 33/33 helper checks prove x64 defaults enabled, ARM64
  defaults disabled, repository/manual override handling, `continue-on-error`
  advisory jobs, interpreter discovery, and `native_installed_uat: false`
  evidence records.
- Hosted gap: T108 remains open. Live runner-label availability, Windows job
  execution, uploaded evidence, and the ARM64 disabled/no-queue outcome still
  require hosted observation.
- Status: **Local contract verified; hosted pending**.

### DW-07 - CI blocks Bash and jq reintroduction

**Outcome:** CI fails changes that introduce Bash scripts, Bash-family
shebangs, active Bash invocations, or `jq` outside the workflow boundary.

- Requirements: FR-002, FR-003, FR-005; SC-004.
- Marker/tasks: `us12`, T089-T099.
- Current paths:
  `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`,
  `speckit-pro/speckit_pro_runner/gates/release.py`,
  `tests/speckit-pro/suite-manifest.json`,
  `tests/speckit-pro/unit/fixtures/repository-bash-confinement/confinement-guard-cases.json`,
  and `tests/speckit-pro/unit/test-repo-bash-confinement.py`.
- Evidence: 47/47 guard checks cover stray `.sh`, Bash shebangs,
  non-allowlisted `.specify/**` files, Python subprocess invocations,
  `hooks.json` commands, `package.json` scripts, prose false positives,
  allowlist substitution, default-suite membership, and release-readiness
  composition. The current live scan passed with zero blockers.
- Status: **Verified**.

### DW-08 - Consumer release notes and public Highlights

**Outcome:** Feat/fix PRs carry an enforced consumer release-note block or an
explicit skip label, and published releases open with deterministic Highlights
while preserving the conventional-commit appendix.

- Requirements: FR-021, FR-022, FR-023, FR-024; SC-005, SC-006.
- Marker/tasks: `us14` T109-T112 and `us15` T113-T120.
- Current paths: `scripts/release_note_policy.py`,
  `scripts/compose-release-notes.py`,
  `tests/speckit-pro/unit/test-release-note-policy.py`,
  `tests/speckit-pro/unit/test-compose-release-notes.py`,
  `tests/speckit-pro/unit/fixtures/release-notes/`,
  `.github/pull_request_template.md`, `.github/workflows/pr-checks.yml`, and
  `.github/workflows/release.yml`.
- Local evidence: policy checks passed 30/30, composition checks passed 46/46,
  and the current PR/release workflow validators passed 49/49 and 41/41. The
  release validator executes capture failure, snapshot-download failure, and
  snapshot-digest mismatch paths. Each path exits nonzero, writes canonical
  `release-note-audit.json`, and emits the exact
  `release_note_composition_failed` outcome; the immutable audit upload uses
  `if: ${{ always() }}` and the job retains `contents: write` as its only
  permission. This also covers fence parsing, sanitization, skip semantics,
  immutable capture, Compare pagination boundaries, digest replay,
  Highlights/appendix output, and least-privilege release mutation.
- Hosted gaps: T117 remains open because `validate-release-note` still needs
  recorded branch-protection configuration. The workflow checklist also lacks
  proof from the first real release rewritten by the composer. Local fixtures
  do not prove either hosted outcome.
- Status: **Local contract verified; hosted pending**.

### DW-09 - Restored spec-size estimator

**Outcome:** `estimate-spec-size` returns populated
`{estimated_loc, suggested_slices, status}` data for grill-me and speckit-prd
size signals.

- Requirements: FR-025; SC-007.
- Marker/tasks: `us16`, T121-T130.
- Current paths: `speckit-pro/speckit_pro_runner/helpers/registry.py`,
  `speckit-pro/speckit_pro_runner/helpers/read_only.py`,
  `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/estimate-spec-size.json`,
  `tests/speckit-pro/unit/fixtures/estimate-spec-size/`, and
  `tests/speckit-pro/unit/test-estimate-spec-size.py`.
- Evidence: the live runner request returned exit 0 and
  `{estimated_loc: 230, suggested_slices: 1, status: "ok"}` for the committed
  typical-under signals. The focused estimator suite passed 33/33.
- Status: **Verified**.

### DW-10 - Native UAT remains the release-claim boundary

**Outcome:** XPLAT-008 native installed-plugin UAT remains the only
release-satisfying evidence for native installed-plugin journeys; XPLAT-010
container and smoke evidence cannot substitute for it.

- Requirements: FR-020, FR-027; SC-008; spec Assumptions and Boundary Guards.
- Marker/tasks: `us13`, T100-T108; release-gate preservation in `us12`.
- Current paths: `speckit-pro/speckit_pro_runner/gates/release.py`,
  `tests/speckit-pro/run-container-preflight.py`,
  `tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/uat-matrix.json`,
  `tests/speckit-pro/unit/fixtures/installed-plugin-release/uat-matrix-cases.json`,
  and `tests/speckit-pro/unit/test-speckit-pro-gates.py`.
- Evidence: the targeted
  `test_xplat008_release_readiness_pending_native_uat_still_blocks` check
  passed and proves a missing native matrix remains a release-readiness
  blocker. Preflight records explicitly carry `native_installed_uat: false`.
- Boundary: completion of the native matrix belongs to XPLAT-008 and remains
  outside XPLAT-010. This row verifies preservation of the gate, not completion
  of native UAT.
- Status: **Verified**.

## Explicit Non-Goals And Pending Evidence

- Layer 8 `semantic-equivalent` LLM judgment remains a deliberate non-goal.
  `tests/speckit-pro/layer8-parity/lib/judge.py` keeps deterministic
  byte-identical, exact, and tolerance-1 behavior plus skip-with-warning. The
  parity result records the replacement instead of claiming false name parity.
- Windows ARM64 is configured advisory behavior, disabled by default. Live
  hosted-runner execution and post-merge evidence remain pending under T108.
- T117 branch-protection evidence remains pending; workflow implementation is
  not equivalent to a required context on `main`.
- T133 is complete: the Bash-absent, `jq`-absent neutral-PATH deterministic
  suite passed 2512/2512 at the frozen implementation head.
- T134 is complete for the emitted stack tip: all 18 packet/body/validation
  triplets exist and every `validation.json` reports `status: passed`. A later
  branch-OID change requires regeneration before synchronization.
- T135 is complete: the final deterministic suite passed 2512/2512 on the
  frozen stack, and the final docs validation completed green in the same
  closeout window.
- The first real GitHub Release rewritten with Highlights remains hosted
  acceptance evidence, not a local fixture claim.

## Verification Record

| Check | Result |
|-------|--------|
| Live `repo-bash-confinement` runner request | Exit 0; 1,699 tracked files; 0 blockers; 10 release-excluded vendored findings |
| `tests/speckit-pro/unit/test-repo-bash-confinement.py` | 47/47 passed |
| Six selected manifest, UAT, workflow-dispatch, and no-shell gate tests | 6/6 passed |
| `tests/speckit-pro/unit/test-estimate-spec-size.py` | 33/33 passed |
| Live `estimate-spec-size` runner request | Exit 0; `230 / 1 / ok` |
| `tests/speckit-pro/unit/test-release-note-policy.py` | 30/30 passed |
| `tests/speckit-pro/unit/test-compose-release-notes.py` | 46/46 passed |
| `tests/speckit-pro/unit/test-hosted-windows-preflight.py` | 33/33 passed |
| `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | 42/42 passed |
| ARM64 exact pinned-container overlay with hydrated `tasks.md` | 42/42 passed |
| `validate-pr-checks-sentinel.py` / `validate-release-workflow.py` | 49/49 and 41/41 passed |
| Release-audit negative paths | Capture failure, snapshot-download failure, and digest mismatch each wrote canonical audit evidence and emitted `release_note_composition_failed`; audit upload is always-run |
| Hooks / trigger / integration / parity / efficiency focused tests | 22/22, 26/26, 31/31, 33/33, and 18/18 passed |
| Cumulative parity invariant | 54 true-port rows; 0 drops, silent renames, or undocumented mismatches |
| PR packet generation | 18/18 triplets present; 18/18 `validation.json` records passed for the frozen implementation tree |
| `pnpm --dir docs-site validate` | Exit 0; references current; Astro clean; links and quality clean; Playwright 88/88 |
| Parent final suite/docs closeout | Passed under T135: neutral-PATH deterministic suite 2512/2512 (Layer 1 1373, Layer 4 953, Layer 5 186); final docs validation green |

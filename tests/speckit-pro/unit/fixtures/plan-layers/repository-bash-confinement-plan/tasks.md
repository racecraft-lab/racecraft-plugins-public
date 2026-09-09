---
description: "Repository Bash confinement planner fixture with 18 reviewable increments"
---

# Tasks: Repository Bash Confinement and CI Dispatch Guard

**Input**: Self-contained repository Bash confinement planning fixture.

**Prerequisites**: plan.md, spec.md (27 FRs / 7 US / 8 SCs / 16 Clarifications), research.md (13 decisions), data-model.md (8 entities), contracts/ (6), quickstart.md (7 scenarios)

**Tests**: This feature is test-centric by nature. Every ported module lands
with its behavioral `unittest` owner in the same PR.

**Reviewability**: The canonical no-gap delivery is a dependency-ordered
**18-PR stack** represented by 18 emitted planner increments and all 136 tasks:
Foundation + User Story 1..16 + Polish. Foundation owns the legitimate
Specify-through-Analyze, prior-migration archive hygiene, setup, and confidence
history around T001–T004; Polish owns T131–T136 closeout. Those two review
units preserve aggregate branch history and do not expand implementation
scope. The former combined PR 12 is blocked at exactly **1,267 production LOC**,
which is 467 LOC above the 800-LOC block threshold. No exception or waiver is
claimed: it is re-sliced into PR 12a (T109–T112) and dependent PR 12b
(T113–T120). Current production-module line counts are 545 for
`scripts/release_note_policy.py` and 738 for
`scripts/compose-release-notes.py`; both are below 800, but each still requires
its own reviewability gate. The original transition-exception provenance remains
the fixture's scope-budget and split-decision record
— not templates, generated zones, `.process` files, PR bodies, or code fences.

**Organization**: Tasks are grouped by **PR-stack slice** (the primary grouping the workflow prompt mandates). Each task additionally carries its `[USn]` user-story label so US1–US7 traceability stays 1:1. Setup / foundational-cleanup / polish tasks carry no story label.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: `[US1]`…`[US7]` — the user story the task serves
- Exact repo-relative file paths in every task. **Privacy hard constraint**: no absolute `/Users` or `/home` paths anywhere.

## Path Conventions

- **Repo-side tooling (never shipped)**: `tests/speckit-pro/`, `scripts/`, `.claude/hooks/`, `.github/workflows/`. Repo-side Python MUST live under these roots — never under `speckit-pro/` (the `validate-plugin-payload` guard fails if `tests/`, `specs/`, or `.process/` reappear under the plugin dir).
- **Shipped runner (byte change → regeneration ritual)**: `speckit-pro/speckit_pro_runner/`. Touched in PRs 2, 5, 7b, 8, 9, 10, and 13.

---

## Per-Port Protocol

Every port task is the **same-PR atomic swap** to Python 3.11+ standard library
only, with no new runtime dependency: add the behavioral `unittest` owner,
register the Python module, remove the predecessor, and require a non-empty,
self-consistent executed summary.

---

## Phase 1: Foundation - Process, archive hygiene, setup, and confidence evidence

- [x] T001 Verify the repo is green before any change: run the toolchain preflight and default-suite gates from the repo root — `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-toolchain-preflight.json` and `.../run-default-suite.json` — and `pnpm --dir docs-site validate`.
- [x] T002 Confirm the working branch is `repository-bash-confinement-plan` (or the active slice branch), never `main`; confirm the feature pointer selects this self-contained fixture; export `PYTHONDONTWRITEBYTECODE=1` for all runner invocations.
- [x] T003 **Reviewability checkpoint (mandatory — transition exception)**: record in the PR review packet that this fixture is delivered as the canonical no-gap 18-PR stack, using the fixture's scope-budget and split-decision record; confirm each planned implementation slice stays within the 400–800 reviewable-LOC / 15–25 total-file budget and does not silently exceed the 800/8/25 block thresholds. The former combined PR 12 is an exact 1,267-production-LOC block and has no waiver; STOP and re-split it into PR 12a/12b. Foundation and Polish are aggregate-history review units, not implementation scope expansion.
- [x] T004 Confirm the declared contracts under `contracts/` are the schemas the guard, composer, and estimator validate against.

**Checkpoint**: Suite green, branch verified, split exception recorded — implementation can begin.

---

## Phase 2: User Story 1 - PR 1 - Orphan-test deletion + disposition ledger (FR-016; after Foundation)

**Slice goal**: Delete the 31 true orphan Bash test scripts with a committed rationale ledger. The two active wrapper shims are classified here and deleted atomically with PR 2's manifest cutover; the estimator test is the ratified PR 13 restore carve-out. Foundational cleanup; carries no user-story label.

- [x] T005 Census and classify the legacy unit-script set (46 `.sh` files) into `orphan-target-deleted` (31 files whose subject was already ported by the prior migration), `redundant-wrapper` (2 files), `active-port-later` (12 files), or the PR-13 estimator carve-out. Confirm the authoritative 31-delete + 2-wrapper-deferred + 12-active-port + 1-estimator-carve-out disposition in the fixture ledger.
- [x] T006 Delete the 31 `orphan-target-deleted` files in PR 1, then delete the 2 `redundant-wrapper` files atomically in PR 2 when `suite-manifest.json` dispatches their Python targets directly. Git history preserves their content; do not port either wrapper. Confirm all 33 classified deletions are present in the integrated candidate and the estimator carve-out remains for PR 13's Python restoration.
- [x] T007 Write the fixture's deleted-tests ledger with one `{path, kind, rationale}` row per deleted file (FR-016), then run the default-suite gate and confirm it stays green (no manifest reference to a deleted file).

**Checkpoint**: 31 true orphans plus 2 redundant wrappers gone across PRs 1-2, estimator carve-out restored in PR 13, ledger complete, suite green.

---

## Phase 3: User Story 2 - PR 2 - Suite manifest + `run-all.py` orchestrator + manifest-reading gate + shared parity tooling (blocks PRs 3–10)

**Slice goal (US1 — Cross-Platform Python Suite Orchestrator)**: The full deterministic suite runs from Python with the bash runner's flags/headline/exit codes; the shipped gate reads the manifest, not the bash runner. **Shipped-runner PR — carries the regeneration ritual.**

**Independent Test**: On a machine with only Python 3.11+ (no Bash, no `jq`), `python3 tests/speckit-pro/run-all.py --all`, `--layer N`, and the toolchain preflight match the recorded bash-runner `X/Y passed` headline, scope, and exit codes.

- [x] T008 [US1] Author `tests/speckit-pro/suite-manifest.json` with the layer execution policy and each script's semantic path and label.
- [x] T009 [P] [US1] Author `tests/speckit-pro/lib/test_result.py` — the shared `unittest.TestResult` subclass overriding `addSubTest` so `{passed}/{total}` counts every executed assertion (loop-generated AND non-loop grouped), reconciling bash check names 1:1 — the house-convention per-assertion counting contract (FR-010, research §D6, Clarifications Session 1). Land its own unit test.
- [x] T010 [P] [US2] Make the suite fail closed on a missing, malformed, empty, or impossible child summary.
- [x] T011 [US2] Derive aggregate results from executed child summaries rather than a frozen snapshot.
- [x] T012 [US1] Author `tests/speckit-pro/run-all.py` preserving the runner flag surface and aggregate headline. Exit zero only when every selected executable layer reports a non-empty, self-consistent passing summary; reject missing summaries even when a child exits zero.
- [x] T013 [US1] Modify `tests/speckit-pro/run-layer-scripts.py` to read the manifest's per-layer `scripts[]` instead of text-parsing `run-all.sh` via `re.findall(...)` (research §D4 — this is the real "regex-parses the bash runner" surface).
- [x] T014 [US1] Modify `speckit-pro/speckit_pro_runner/gates/suite.py` so `DEFAULT_SUITE`/`EXTENDED_SUITE`/`ALLOWED_LAYERS` derive solely from the manifest, failing closed when it is absent/unreadable, while preserving the existing envelope contract unchanged (FR-007/FR-008).
- [x] T015 [US1] Add the deterministic drift-guard test asserting the shipped gate's advertised roster AND dispatch kinds equal the manifest exactly (FR-007), plus the two manifest-integrity invariants: (a) every `scripts[].path` resolves to an existing repo file; (b) no layer carries `dispatch: shell-legacy-transitional` after PR 10 (terminal-absence assertion). Delete the now-replaced `tests/speckit-pro/run-all.sh` in this PR (replaced by `run-all.py`).
- [x] T016 [US1] **Shipped-runner regeneration ritual (PR 2)**: recompute `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` sha256 rows → `python3 scripts/build-plugin-payloads.py` (rebuild `dist/**`) → checksum-based fixture sync (`--checksum`, avoids the mtime trap) → per-row proof-hash recompute → regenerate evidence in gate order with **release-readiness LAST** and home-directory sanitization (`<home>`). If another shipped-runner slice has merged first, rebase onto it and re-run this full ritual (hand-merging conflicting proof rows / payload bytes is forbidden — plan §Constraints).
- [x] T017 [US1] Verify US1 end-to-end (quickstart US1): deterministic `run-all.py --all` ends green with Layer 7 replay and live-AI command plans, while `--all --live` remains the explicit live path; the shipped suite gate resolves its roster from the manifest with the envelope unchanged; default-suite gate + `pnpm --dir docs-site validate` green.

**Checkpoint**: Manifest is the single source of truth; `run-all.py` reaches UX parity and fails closed on invalid child results. **PR 2 must merge before PRs 3–10.**

---

## Phase 4: User Story 3 - PR 3a - Layer-1 validators port, batch 1 of 2 (after PR 2)

**Slice goal (US2)**: Port the mechanical Layer-1 structural validators while preserving their executed behavior and result summaries.

- [x] T018 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-agents.sh` → `.py` (Per-Port Protocol).
- [x] T019 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh` → `.py` (Per-Port Protocol).
- [x] T020 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh` → `.py` (Per-Port Protocol).
- [x] T021 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-agents.sh` → `.py` (Per-Port Protocol).
- [x] T022 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-hooks.sh` → `.py` (Per-Port Protocol).
- [x] T023 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-marketplace.sh` → `.py` (Per-Port Protocol).
- [x] T024 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-parity.sh` → `.py` (Per-Port Protocol).
- [x] T025 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-plugin.sh` → `.py` (Per-Port Protocol).
- [x] T026 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-curated-set.sh` → `.py` (Per-Port Protocol). Check names are driven by live `scripts/curated-set.json` content.
- [x] T027 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-hooks.sh` → `.py` (Per-Port Protocol).
- [x] T028 [US2] Register the ported modules in `suite-manifest.json` and confirm the default-suite gate and drift guard are green.

**Checkpoint**: The Layer-1 validators preserve their behavior and their predecessors are deleted.

---

## Phase 5: User Story 4 - PR 3b - Layer-1 validators port, batch 2 of 2 (after PR 2)

**Slice goal (US2)**: Port the remaining 10 mechanical Layer-1 validators. Per-Port Protocol each.

- [x] T029 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh` → `.py` (Per-Port Protocol).
- [x] T030 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-plugin-payload.sh` → `.py` (Per-Port Protocol).
- [x] T031 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-plugin.sh` → `.py` (Per-Port Protocol).
- [x] T032 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh` → `.py` (Per-Port Protocol). Coupling note: PR 5 updates this ported validator for the dispatch swap — land 3b before 5, or PR 5 re-ports it.
- [x] T033 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-process-gitattributes.sh` → `.py` (Per-Port Protocol).
- [x] T034 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-release-workflow.sh` → `.py` (Per-Port Protocol). Coupling note: PR 12b updates this ported validator for the composer job.
- [x] T035 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-scripts.sh` → `.py` (Per-Port Protocol).
- [x] T036 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-skill-capability-pointers.sh` → `.py` (Per-Port Protocol).
- [x] T037 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-skills.sh` → `.py` (Per-Port Protocol).
- [x] T038 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-spec-index-determinism.sh` → `.py` (Per-Port Protocol).
- [x] T039 [US2] Register the ported modules in `suite-manifest.json` and confirm the default-suite gate and drift guard are green.

**Checkpoint**: All 20 mechanical Layer-1 validators ported; 20 `.sh` deleted.

---

## Phase 6: User Story 5 - PR 4 - MOC lints + codex-skills/payload-conformance validators (after PR 2)

**Slice goal (US2)**: Port the 4 remaining Layer-1 validators (MOC + codex/payload). Per-Port Protocol each; these carry heavier logic than the mechanical 20.

- [x] T040 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` → `.py` (Per-Port Protocol), including the optional scan-root invocation mode.
- [x] T041 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh` → `.py` (Per-Port Protocol).
- [x] T042 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-skills.sh` → `.py` (Per-Port Protocol).
- [x] T043 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-payload-conformance.sh` → `.py` (Per-Port Protocol).
- [x] T044 [US2] Register the ported modules in `suite-manifest.json` and confirm the default-suite gate and drift guard are green.
- [x] T045 [US2] Port the active Layer-4 MOC test scripts co-located with these validators if flagged `active-port-later` in T005 (e.g. `test-moc-id-normalize.sh`, `test-moc-lint-exit-codes.sh`, `test-generate-spec-index.sh`) → `.py` under `tests/speckit-pro/unit/` (Per-Port Protocol); otherwise confirm they were deleted as orphans in PR 1. Note the root-vs-non-root divergence recorded for `test-moc-lint-exit-codes.sh` (31 vs 36) — capture in the pinned non-root env.

**Checkpoint**: All 24 Layer-1 validators ported.

---

## Phase 7: User Story 6 - PR 5 - Layer-5 tool scoping + toolchain check + `pr-checks.yml` dispatch swap (after PR 3b)

**Slice goal (US2 port + FR-026 workflow-shell reduction)**: Port Layer-5, replace the residual `bash tests/speckit-pro/check-toolchain.sh` CI dispatch with a direct Python-runner invocation, and retire the vacuous native `check_layer5`.

- [x] T046 [US2] Port `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` → `.py` (Per-Port Protocol). Replace the vacuously-true native `check_layer5` body in `gates/suite.py` with the real tool-scoping validator, then retire `check_layer5` at this boundary per research §D3 (no permanent equivalence shim — FR-008).
- [x] T047 [US2] Port `tests/speckit-pro/check-toolchain.sh` (top-level) → Python and its active Layer-4 test `test-check-toolchain.sh` → `.py` (Per-Port Protocol); delete both `.sh`.
- [x] T048 [US2] Swap the `bash tests/speckit-pro/check-toolchain.sh` dispatch step in `.github/workflows/pr-checks.yml` (~line 289) for a direct Python-runner toolchain-preflight invocation (FR-026). This replaces a `run:` step inside the existing `test`/`validate-plugins` surface — it renames no required status check.
- [x] T049 [US2] Update the ported `validate-pr-checks-sentinel` self-referential workflow validator in the SAME PR so its assertions match the swapped `pr-checks.yml` (FR-026).
- [x] T050 [US2] Register the Layer-5 module flip in `suite-manifest.json`.
- [x] T051 [US2] Add a PR-body branch-protection callout stating this PR is **required-check-neutral** (no branch-protection change — contrast PRs 11/12) per FR-026/FR-018.
- [x] T052 [US2] Confirm default-suite gate + drift-guard test green; confirm `pr-checks.yml` still dispatches the Python runner for the toolchain leg. Because T046 changes shipped `gates/suite.py`, run the full shipped-runner payload/proof regeneration ritual with release-readiness LAST and `<home>` sanitization.
- [x] T053 [US2] Record the CLAUDE.md CI/CD note: confirm whether the `pr-checks.yml` edit requires a CLAUDE.md CI/CD-section update (per repo policy on workflow edits).

**Checkpoint**: Layer 5 + toolchain ported; the last residual CI Bash dispatch step is Python; native `check_layer5` retired.

---

## Phase 8: User Story 7 - PR 6 - `scripts/**` + `.claude/hooks/**` ports (after PR 2)

**Slice goal (US2 port + FR-014 hook contract)**: Port the two helper scripts and two hook handlers to stdlib Python, dropping the `jq` holdout and preserving the hook stdin-JSON / exit-0-or-2 contract.

- [x] T054 [P] [US2] Port `scripts/refresh-local-plugin.sh` → `.py` (Per-Port Protocol via its active Layer-4 test `test-refresh-local-plugin.sh`). It already calls `python3 build-plugin-payloads.py`; preserve behavior, delete the `.sh`.
- [x] T055 [P] [US2] Port `scripts/sync-marketplace-versions.sh` → `.py` (the 12-call `jq` holdout; research §D12) via its active Layer-4 test `test-sync-marketplace-versions.sh`; delete the `.sh` and drop the `jq` dependency.
- [x] T056 [P] [US2] Port `.claude/hooks/guard-version-triplet.sh` (PreToolUse) → `.claude/hooks/guard-version-triplet.py`, preserving the stdin-JSON intake and exit-0 (allow) / exit-2 (block) contract; parse stdin via stdlib `json`, never shell-interpolating untrusted input into a subprocess (FR-014). Preserve the contract even for malformed input.
- [x] T057 [P] [US2] Port `.claude/hooks/validate-structural.sh` (PostToolUse) → `.claude/hooks/validate-structural.py`, preserving the exit-0/2 contract and replacing its `bash tests/run-all.sh --layer 1` shell-out with a Python Layer-1 dispatch (research §D12).
- [x] T058 [US2] Port the active Layer-4 tests for the ported helpers/hooks (per T005 classification) → `.py` following the Per-Port Protocol; delete their `.sh`.
- [x] T059 [US2] Register the ported modules in `suite-manifest.json` and confirm the default-suite gate is green.
- [x] T060 [US2] Confirm the hooks stay off the shell-injection surface: assert no `subprocess`/`os.system` call in the ported hooks passes untrusted stdin into a shell (aligns with the FR-002 guard's own rule and FR-023 discipline).
- [x] T061 [US2] Verify `pnpm --dir docs-site validate` still green (the `docs-site/package.json` `scripts` values are within the FR-002 structural-scan surface — confirm no `bash`/`jq` invocation was introduced).

**Checkpoint**: `scripts/**` and `.claude/hooks/**` are Python; `jq` holdout removed.

---

## Phase 9: User Story 8 - PR 7a - Layer-7 shared transcript library (after PR 2; before PR 7b)

**Slice goal (US2)**: Port the shared Layer-7 transcript library first so the replay runners can build on it.

- [x] T062 [US2] Port `tests/speckit-pro/layer7-integration/lib/transcript-helpers.sh` → `.py` (Per-Port Protocol via active Layer-4 test `test-transcript-helpers.sh`).
- [x] T063 [P] [US2] Port `tests/speckit-pro/layer7-integration/scrub-transcript.sh` → `.py` (Per-Port Protocol).
- [x] T064 [P] [US2] Port `tests/speckit-pro/layer7-integration/reduce-transcript-fixture.sh` → `.py` (Per-Port Protocol).
- [x] T065 [US2] Port the active Layer-4 test `test-transcript-helpers.sh` → `.py`; delete its `.sh`.
- [x] T066 [US2] Register the ported transcript-library modules in `suite-manifest.json` and confirm the default-suite gate is green.

**Checkpoint**: Layer-7 transcript library is Python; PR 7b can build the runners on it.

---

## Phase 10: User Story 9 - PR 7b - Layer-7 replay runners (after PR 7a)

**Slice goal (US2)**: Port the Layer-7 replay-mode runners; retire the native `check_layer7`.

- [x] T067 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-dispatch-fixtures.sh` → `.py` (Per-Port Protocol; replay mode).
- [x] T068 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-return-format-fixtures.sh` → `.py` (Per-Port Protocol; replay mode).
- [x] T069 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-grounding-fixtures.sh` → `.py` (Per-Port Protocol; replay mode).
- [x] T070 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-e2e-fixtures.sh` and `run-all-fixtures.sh` → `.py` (Per-Port Protocol; replay mode). Preserve `--live` semantics as a code path (live mode still invokes `claude -p`; replay stays free).
- [x] T071 [US2] Retire the native `check_layer7` in `gates/suite.py` at this boundary and flip Layer-7 to its Python module in `suite-manifest.json`; run the shipped-runner regeneration checks.
- [x] T072 [US2] Confirm default-suite gate + drift-guard test green; replay-mode Layer-7 runs Python-only.

**Checkpoint**: Layer-7 replay harness is Python; native `check_layer7` retired.

---

## Phase 11: User Story 10 - PR 8 - Layer-8 parity runner + fixture conversion (after PR 2)

**Slice goal (US2)**: Port the Layer-8 parity runner + its `jq`-dependent libs and convert the 8 per-case `env-*.sh` fixture scripts to Python/data so PR 10's guard finds zero non-allowlisted `.sh` (research §D11). Retire native `check_layer8`.

- [x] T073 [P] [US2] Port `tests/speckit-pro/layer8-parity/lib/extractors.sh` → `.py` (Per-Port Protocol via `tests/speckit-pro/unit/test-parity-extractors.py`).
- [x] T074 [P] [US2] Port `tests/speckit-pro/layer8-parity/lib/judge.sh` → `.py` (Per-Port Protocol via `tests/speckit-pro/unit/test-parity-judge.py`). **Boundary guard**: keep the existing tolerance arms (`byte-identical`, `exact`, `tolerance-1`) only — the `semantic-equivalent` LLM judge stays skipped-with-warning (design-concept Non-goal; see Boundary Guards).
- [x] T075 [US2] Port `tests/speckit-pro/layer8-parity/run-parity-fixtures.sh` → `.py`, dropping the `jq` dependency (Per-Port Protocol); preserve `--dry-run` (free structural validation) and `--live --budget-usd` semantics.
- [x] T076 [P] [US2] Convert the 8 per-case `env-fallback.sh`/`env-teams.sh` fixture scripts under `layer8-parity/0{1,2,3,4}-*/` to Python/data (the environment-selection inputs the real validator requires); delete the 8 `.sh`.
- [x] T077 [US2] Port the active Layer-4 tests to `tests/speckit-pro/unit/test-parity-extractors.py` and `tests/speckit-pro/unit/test-parity-judge.py`; delete their `.sh` predecessors.
- [x] T078 [US2] Retire the native `check_layer8` in `gates/suite.py` at this boundary and flip Layer-8 to its Python module in `suite-manifest.json`; run the shipped-runner regeneration checks.
- [x] T079 [US2] Append the Layer-8 delta lines to the fixture's count ledger; confirm default-suite gate + drift-guard test green.
- [x] T080 [US2] Confirm `git ls-files 'tests/speckit-pro/layer8-parity/**/*.sh'` returns empty (all Layer-8 `.sh` converted/deleted) — the PR-10 guard precondition for this surface.

**Checkpoint**: Layer-8 parity harness is Python; all Layer-8 `.sh` gone; native `check_layer8` retired.

---

## Phase 12: User Story 11 - PR 9 - Live-AI eval runners (after PR 2)

**Slice goal (US2 port + FR-015)**: Port the live-AI eval runners preserving their CLI argument contracts and codex staging semantics. These are `live_only` (not in the default deterministic suite).

- [x] T081 [P] [US2] Port `tests/speckit-pro/layer2-trigger/run-trigger-evals.sh`, `run-trigger-evals-codex.sh`, `run-trigger-loop.sh` → `.py`, preserving CLI args + codex staging (FR-015; Per-Port Protocol where `_pass`/`_fail` output exists, else CLI/exit parity).
- [x] T082 [P] [US2] Port `tests/speckit-pro/layer3-functional/run-functional-evals.sh`, `run-functional-evals-codex.sh` → `.py`, preserving CLI args + codex staging (FR-015).
- [x] T083 [P] [US2] Verify the ported live-eval runners preserve their CLI argument and staging contracts.
- [x] T084 [US2] Port the active Layer-4 tests to `tests/speckit-pro/unit/test-efficiency-codex-runner.py` and `tests/speckit-pro/unit/test-eval-runner-skill-selection.py` (Per-Port Protocol); delete their `.sh` predecessors.
- [x] T085 [US2] Register Layers 2 and 3 as `python-module` + `live_only:true` in `suite-manifest.json` (not in the default deterministic suite). Replace the shipped suite gate's hardcoded AI runner paths with the manifest `scripts[]` entries, then run the shipped-runner regeneration checks.
- [x] T086 [US2] Confirm deterministic `run-all.py --all` and explicit Layer 2/3 selection preserve the live-AI command-plan scope and headline with Python command text after the ports; the default deterministic gate remains unaffected.
- [x] T087 [US2] Confirm the Layer 2 and 3 runner surfaces contain no predecessor shell scripts.

**Checkpoint**: Live-AI eval runners are Python; all Layers 2–8 ported. PRs 3–9 complete → PR 10 can proceed.

---

## Phase 13: User Story 12 - PR 10 - Repository Bash confinement guard + final Bash deletion (after PRs 3–9)

**Slice goal (US3 — Repository Bash Confinement Guard)**: Add the bash-scoped confinement guard (live `git ls-files -z`, fail-closed 10-file `.specify/**` allowlist), compose it into CI + release readiness, and delete the last repo-local `.sh`. **Shipped-runner PR — carries the regeneration ritual.**

**Independent Test**: Feed the guard three trees — clean / stray new `.sh` outside `.github/workflows/` / non-allowlisted Bash under `.specify/**` — and confirm it passes the first and fails the other two (fail-closed).

- [x] T088 [US3] Author the repository Bash-confinement `allowlist.json` fixture per `confinement-allowlist.schema.json`: `{schema_version, feature_id:"LARGE-MIGRATION", entries[]}`, `additionalProperties:false`, `release_readiness_excluded:true` required on every entry, `minItems`/`maxItems` 10, pinning the exact 10 canonical `vendored_specify_helper` paths (4 Bash helpers + 6 Bash helpers). The 4 vendored `.ps1` get no entry (FR-003).
- [x] T089 [US3] Add the `repo-bash-confinement` operation: live `["git","ls-files","-z"]` argv enumeration from repo root (never `shell=True`); Bash-scoped suffix, shebang, and command detection; workflow filtering; and resolved-path symlink confinement. Fail closed with a missing-prerequisite diagnostic when git is unavailable (FR-001/FR-002).
- [x] T090 [US3] Implement the FR-002 invocation-text detection surfaces precisely: Python files via AST inspection of `subprocess`/`os.system` args; structural JSON-value scans of `**/hooks.json` `command` fields and `**/package.json` `scripts` values. Do not text-scan prose, Markdown, YAML, or fixtures. An unreadable or undecodable first line yields no shebang and is classified by path suffix alone.
- [x] T091 [US3] Implement the fail-closed allowlist loader in `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` with the exact-canonical-set assertion (FR-003): accept only the `vendored_specify_helper` path scope; assert the allowlist content equals the enumerated 10 canonical paths so a same-scope substitution or a delete-and-substitute is a red event, not reviewer-trusted; any `.specify/**` Bash file not on the list is a blocking finding.
- [x] T092 [US3] Register the new guard op in `gates/registry.py` and compose the `repo_bash_confinement` check into the release-readiness assembly in `gates/release.py` (pass iff `blocking_count == 0`), surfacing allowlisted entries under `release_readiness_excluded:true` and excluding them from the positive Bash-free evidence set (FR-004/FR-005).
- [x] T093 [US3] Add the live-scan guard case to the default deterministic suite (manifest + fixture request under `tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/`), performing a live repo-wide enumeration (never a fixed list) so newly added files are always scanned (FR-005).
- [x] T094 [P] [US3] Author `tests/speckit-pro/unit/test-repo-bash-confinement.py` + the `confinement-guard-cases.json` fixture: clean tree passes; stray `.sh` outside `.github/workflows/` fails; non-allowlisted `.specify/**` Bash fails; prose mention passes; `hooks.json`/`package.json` invocation fails; each of the 10 allowlisted files accepted + `release_readiness_excluded:true`. Validate results against `contracts/repo-bash-confinement-result.schema.json`.
- [x] T095 [P] [US3] Add the FR-004 negative-control test in `tests/speckit-pro/unit/test-repo-bash-confinement.py`: an allowlisted (`release_readiness_excluded:true`) entry can NEVER count as positive Bash-free evidence — the claim is satisfied only by `blocking_count == 0`.
- [x] T096 [P] [US3] Add the FR-005 durability test in `tests/speckit-pro/unit/test-repo-bash-confinement.py`: the `repo_bash_confinement` check remains composed in the release-readiness assembly AND the guard case remains present in the default-suite roster (a future edit dropping either fails CI).
- [x] T097 [US3] **Final Bash deletion**: delete `tests/speckit-pro/lib/assertions.sh` and any remaining ported `.sh` stragglers; run the guard live and confirm `git ls-files '*.sh' | grep -v '^.github/workflows/' | grep -v '^.specify/'` is empty (SC-001). Confirm the manifest carries zero `shell-legacy-transitional` entries (FR-007 terminal-absence assertion now holds).
- [x] T098 [US3] **Shipped-runner regeneration ritual (PR 10)**: manifest sha256 recompute → `build-plugin-payloads.py` → checksum-based fixture sync → per-row proof-hash recompute → evidence regeneration in gate order, **release-readiness LAST**, `<home>` sanitized. If another shipped-runner slice has merged first, rebase onto it and re-run the full ritual (no hand-merged proof rows — plan §Constraints).
- [x] T099 [US3] Verify US3 end-to-end (quickstart US3): clean tree passes; stray-`.sh` and non-allowlisted `.specify/**` trees fail closed; default-suite + release-readiness gates green; `pnpm --dir docs-site validate` green. No new required status check added (rides the `validate-plugins` sentinel + release-readiness leg — FR-005).

**Checkpoint**: Confinement guard live and composed into CI + release readiness; zero non-allowlisted `.sh` remain (SC-001/SC-004).

---

## Phase 14: User Story 13 - PR 11 - Container / Windows preflight CI (last among confinement PRs)

**Slice goal (US4 — Container and Runner Preflight CI)**: Add `container-preflight.yml` — Linux amd64/arm64 gating, Windows x64/ARM64 advisory — running against the fully-confined tree (hence last among confinement PRs).

**Independent Test**: Trigger via manual dispatch, a runner/gate-path PR, and a docs-only PR; confirm the always-triggered workflow reports both Linux required contexts, heavy jobs run only for relevant changes, Windows jobs are configured and `continue-on-error`, disabled ARM64 records `available:false` on Ubuntu without queueing `windows-11-arm`, and every role uploads evidence.

- [x] T100 [US4] Author `.github/workflows/container-preflight.yml` with a workflow-level `permissions: {}` default and per-job minimal grants (`contents: read` for checkout; evidence upload uses the built-in token) — matching the `pr-checks.yml`/`deploy-docs.yml` least-privilege convention (FR-017).
- [x] T101 [US4] Configure an always-triggered `pull_request` + `workflow_dispatch` workflow with a lightweight Ubuntu change detector over runner, gate, and workflow paths. Keep heavyweight preflight jobs job-level conditional; on docs-only/unrelated changes, explicit Linux sentinel contexts MUST run and return success without heavy execution so required checks never remain pending (FR-017).
- [x] T102 [US4] Add job-level-conditional Linux amd64 + arm64 container jobs running the SAME entrypoints CI uses — toolchain preflight, deterministic suite gate, the no-Bash/`jq` confinement guard, and the relevant release-readiness checks — and feed their results into stable **gating** contexts named `container-preflight-linux-amd64` and `container-preflight-linux-arm64` (FR-018/FR-027).
- [x] T103 [US4] Add Windows x64 + ARM64 direct-runner smoke jobs as `continue-on-error` advisory, running the interpreter-discovery + runner `runtime-info`/`preflight` subset (FR-019/FR-027). Use explicit configured availability from repository variables or manual-dispatch inputs, never claim live capacity auto-detection: an Ubuntu control job records per-label `available:true|false`, ARM64 defaults false, and `windows-11-arm` is queued only when explicitly enabled (FR-019, Edge Case).
- [x] T104 [US4] Add the evidence-artifact upload to every job with `if: always()` semantics so a FAILING preflight still captures evidence without masking an entrypoint failure or flipping a passing gate (FR-020). Evidence is never treated as native installed-plugin UAT.
- [x] T105 [US4] Add the PR-body branch-protection callout: PR 11 adds TWO new required Linux check names — they must be added to branch protection manually (GitHub does not auto-register), mirroring the FR-022 callout style (FR-018).
- [x] T106 [US4] Update the self-referential workflow validator(s) so the new `container-preflight.yml` passes structural validation in the same PR.
- [x] T107 [US4] Record the CLAUDE.md CI/CD note confirming whether the new workflow requires a CLAUDE.md CI/CD-section update.
- [x] T108 [US4] Verify US4 end-to-end: manual dispatch and all declared PR triggers report; relevant changes enable heavy jobs; unrelated changes skip heavy execution while both Linux sentinels pass; Linux failures propagate; Windows remains advisory; ARM64-disabled evidence is retained without queueing the label; and every executed role uploads evidence (SC-008).

**Checkpoint**: Preflight CI live; Linux gates, Windows advises, evidence uploaded.

---

## Phase 15: User Story 14 - PR 12a - Release-note extraction, sanitization, validation module + focused tests (independent)

**Slice goal**: Establish the importable stdlib release-note contract module and
its focused extraction, sanitization, validation, fallback, and fail-loud tests.
This is the first half of the mandatory reviewability split.

**Independent Test**: Exercise release-note fence discovery, sanitization,
required-check validation semantics, immutable fallback-subject handling, and
all malformed/empty/fail-loud cases without workflow or network coupling.

- [x] T109 [P] [US5] Author `scripts/release_note_policy.py` as an importable stdlib release-note contract module (no LLM, no new secret): define typed fence/validation records, anchored fence extraction, shared errors, and validation entrypoints used by both the required check and later composition (FR-021/FR-023).
- [x] T110 [P] [US5] Implement the sanitization + fence-extraction layer in `scripts/release_note_policy.py`: one anchored CommonMark-nesting-aware `release-note` fence outside any enclosing fence; repeatedly decode entities/strip raw HTML before removing image markdown; reject sanitizes-to-empty; neutralize leading structure; cap at 2,000 chars (truncate-and-mark, not a failure); JSON/env-only intake (FR-021/FR-023).
- [x] T111 [P] [US5] Implement module-level validation and fail-loud rules: skip-labeled PRs are exempt/omitted; required feat/fix notes must survive sanitization; malformed fences or validation inputs fail deterministically; all callers share the same extraction/sanitization/non-empty contract (FR-021/FR-022/FR-023).
- [x] T112 [P] [US5] Author `tests/speckit-pro/unit/test-release-note-policy.py` covering fence discovery, sanitizer/entity ordering, enclosing fences, sanitizes-to-empty, required-check validation, and malformed/fail-loud module inputs. Capture, Compare, composition, workflow, and release-mutation cases remain in PR 12b.

**Checkpoint**: Extraction/sanitization/validation module and focused tests are
reviewable independently; no workflow, release mutation, template, or docs
surface is included in PR 12a.

---

## Phase 16: User Story 15 - PR 12b - Immutable capture/composition, workflows, enforcement, template, and docs (after PR 12a)

**Slice goal (US5 public Highlights + US6 enforcement)**: Extend the validated
module with immutable capture/composition and wire the release and pull-request
workflows, required check, PR template, label, self-validator, and release docs.

**Independent Test (US5)**: Run the composer against commits since a prior tag
whose PR bodies carry `release-note` blocks; the rewritten body opens with
Highlights and retains the commit list as an appendix. **(US6)**: a feat PR
without a block fails the check; adding the block passes; `release-note/skip`
passes without a block.

- [x] T113 [US5] Author `scripts/compose-release-notes.py` on top of `release_note_policy.py` with trailing `(#N)` Compare discovery, immutable de-prefixed commit-subject fallback (never mutable PR titles), exact 250/251 boundary handling, Compare + PR metadata + raw release-body snapshot capture, digest-verified replay, deterministic Highlights/appendix composition, release lookup/PATCH, audit fields, and fail-loud transport/snapshot/pagination/release errors; then add separate capture and `compose-release-notes` jobs to `.github/workflows/release.yml`, gated on the component release-created output. Capture uploads immutable canonical input JSON; composition `needs:` the publishing + capture jobs, downloads that artifact, and carries only `permissions: {contents: write}` — sufficient for release lookup/update; never inherit broader grants or use `RELEASE_PLEASE_TOKEN` (research §D9; FR-023/FR-024).
- [x] T114 [US6] Add the required `validate-release-note` check (workflow): runs on `opened, reopened, synchronize, edited, labeled, unlabeled, ready_for_review`; scopes to releasable types only (`feat`/`fix` incl. scoped + `!`-breaking); skips drafts; exempts release-please's own PRs (chore short-circuit + `autorelease:` label, title from `inputs.pr_title` on the dispatch path); ALL untrusted text (PR body AND `inputs.pr_title`) via env vars, never shell interpolation (FR-022).
- [x] T115 [P] [US6] Author `.github/pull_request_template.md` seeding the empty `release-note` fenced block under a `## Release note` heading (FR-021).
- [x] T116 [US6] Confirm the `release-note/skip` label exists in `racecraft-lab/racecraft-plugins-public` (`gh label list` verified its description and `#5319E7` color on 2026-07-10) (FR-022).
- [x] T117 [US6] Add the release-note and stable Linux sentinel status-check names to non-strict branch protection and record the resulting five-check rule state (FR-022).
- [x] T118 [US5] Update the ported `validate-release-workflow` self-referential validator (`tests/speckit-pro/layer1-structural/validate-release-workflow.py`) in PR 12b to match the new capture/composer jobs + permissions shape.
- [x] T119 [US5] Update CLAUDE.md's release process for the deterministic Highlights rewrite and confirm CHANGELOG.md remains release-please's machine-generated ledger.
- [x] T120 [US6] Verify US5 + US6 end-to-end (quickstart US5/US6): offline snapshot composition covers immutable fallback subjects, 250/251 Compare boundaries, canonical snapshot/body digests, byte-identical reruns after PR metadata mutation, and fail-loud paths; it produces Highlights + appendix, while a feat PR without a block or with sanitizes-to-empty content fails, a valid block passes, and `release-note/skip` passes without a block (SC-005/SC-006).

**Checkpoint**: Public-readable Release Highlights + enforced release-note blocks.

---

## Phase 17: User Story 16 - PR 13 - Spec-size estimator restored + manifest-version fix (independent, land early)

**Slice goal (US7 — Restored Spec-Size Estimator)**: Restore the `estimate-spec-size` runner op and fix the confirmed manifest-version staleness defect. **Shipped-runner PR — carries the regeneration ritual.**

**Independent Test**: Send the size signals grill-me/speckit-prd emit and confirm a populated `{estimated_loc, suggested_slices, status}` matching the golden fixtures.

- [x] T121 [US7] Register `estimate-spec-size` as a new `HelperEntry` in `speckit-pro/speckit_pro_runner/helpers/registry.py` (`{helper_id, operation, script, promotion_status, comparison_mode, authoritative_command}`), distinct from the existing `estimate-reviewable-loc` helper (research §D7).
- [x] T122 [US7] Implement `estimate-spec-size` in `speckit-pro/speckit_pro_runner/helpers/read_only.py` via `run_registered_helper`: inputs = size signals `{user_stories, files, frs}` (lenient coercion of non-numeric/negative); output = `{estimated_loc (int ≥ 0), suggested_slices (int ≥ 1), status ("ok"|"warn")}` per `contracts/estimate-spec-size.schema.json` (FR-025).
- [x] T123 [US7] Validate against the existing golden fixtures at `tests/speckit-pro/unit/fixtures/estimate-spec-size/` (`--files 20` → `{800, 2, "warn"}`; `--files 11` → `{440, 2, "warn"}`; bad input → `{0, 1, "ok"}`); port/refresh the estimator's active test to `tests/speckit-pro/unit/test-estimate-spec-size.py` following the Per-Port Protocol.
- [x] T124 [US7] **Manifest-version staleness fix (a)**: add `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` to `release-please-config.json` `extra-files` with jsonpath `$.plugin_version`, aligning the `.release-please-manifest.json` key so releases bump it automatically (research §D8).
- [x] T125 [US7] **Manifest-version staleness fix (b)**: replace the hardcoded `self.assertEqual(manifest["plugin_version"], "2.17.0")` in `tests/speckit-pro/unit/test-speckit-pro-runner.py` with a version-agnostic check — assert the value matches the semver pattern AND equals `speckit-pro/.claude-plugin/plugin.json` `$.version` (research §D8).
- [x] T126 [US7] **Shipped-runner regeneration ritual (PR 13)**: manifest sha256 recompute → `build-plugin-payloads.py` → checksum-based fixture sync → per-row proof-hash recompute → evidence regeneration in gate order, **release-readiness LAST**, `<home>` sanitized. If another shipped-runner slice has merged first, rebase onto it and re-run the full ritual (no hand-merged proof rows — plan §Constraints).
- [x] T127 [US7] Confirm the estimator port + version fix leave the default-suite gate + drift-guard test green.
- [x] T128 [US7] Record the CLAUDE.md note confirming whether the release-please-config change requires a CLAUDE.md release-section update.
- [x] T129 [US7] Add the PR-body branch-protection callout: PR 13 adds no required status check (shipped-runner fix only) — state this explicitly to keep the stack's branch-protection ledger complete.
- [x] T130 [US7] Verify US7 end-to-end with the golden `typical-under` size signals and confirm the returned `{estimated_loc, suggested_slices, status}` equals `{estimated_loc:230, suggested_slices:1, status:"ok"}`, restoring pre-migration scoping behavior (SC-007).

**Checkpoint**: Estimator restored for grill-me/speckit-prd; manifest version auto-bumps; stale hardcode removed.

---

## Phase 18: Polish - Aggregate closeout evidence and review packets

These global verification and publication tasks form the required final Polish
review unit. The aggregate no-gap audit requires this closeout PR so T131–T136
and their existing commit history are represented; it is not implementation
scope expansion.

- [x] T131 Confirm every selected test module executes and reports a non-empty, self-consistent result summary.
- [x] T132 [P] Run the seven-story quickstart validation from the repo root. Fresh focused evidence passed for orchestration 28/28, estimator 33/33, confinement 47/47, hosted-preflight helper 33/33, PR sentinel 49/49, release-note composition 46/46, release-note policy 30/30, and release-workflow validation 41/41; runner requests and the offline release-note dry run also exited 0. Hosted-only acceptance remains explicit under T108/T117.
- [x] T133 [P] Parent closeout: final neutral-PATH, Bash-absent, `jq`-absent Python 3.11+ evidence at frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146` (tree `a1c42735d35619bbd0a4a90a42c57ab9e578848e`) passed the read-only helpers 42/42 and the ARM64 exact pinned-container overlay with hydrated `tasks.md` 42/42, confirming the final no-Bash end state (SC-001/SC-002).
- [x] T134 Generate and validate all 18 current PR packet/body/validation triplets under the fixture's process directory. Each directory contains `body.md`, `packet.json`, and a passing `validation.json` tied to its exact adjacent diff, protected fingerprint, source markers, traceability, rollback notes, and required release-note block. Regenerate the affected triplet if a final branch OID changes.
- [x] T135 [P] Parent closeout: on frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146` (tree `a1c42735d35619bbd0a4a90a42c57ab9e578848e`), the neutral-PATH deterministic default suite passed 2512/2512: Layer 1 1373/1373, Layer 4 953/953, and Layer 5 186/186; `pnpm --dir docs-site validate` also passed.
- [x] T136 Confirm every "Done When" workflow bullet maps to at least one FR and one emitted PR slice in the fixture's traceability record. The record keeps the semantic-equivalence LLM judge as a deliberate deferred non-goal and Windows ARM64 as configured advisory behavior.

---

## Boundary Guards / Non-Goals (design-concept Non-goals — deliberately NOT tasked)

Per the workflow prompt, tasks that would cross these boundaries were **flagged and not written**:

- **No `.specify/**` ports.** The 10 vendored upstream `.sh` are allowlisted and guarded (T088/T091), never ported or forked. The 4 vendored `.ps1` are outside the bash-scoped detection vocabulary and need no entry.
- **No AI/LLM release notes.** The composer (T109–T111) is deterministic stdlib only — no LLM call, no new secret (FR-024).
- **No Layer-8 `semantic-equivalent` LLM judge.** PR 8 (T074) keeps `byte-identical`/`exact`/`tolerance-1` only; `semantic-equivalent` stays skipped-with-warning (known gap, out of scope).
- **No UAT-matrix / native operator UAT work.** Container/Windows preflight (T100–T108) is preflight evidence only; native operator UAT remains a separate release-claim gate.
- **No new required status checks beyond the two ratified ones.** Only PR 11 (2 Linux checks) and PR 12b (`validate-release-note`) add required checks; PR 5 and PR 10 are required-check-neutral (T051/T099).
- **No `constitution.md` amendment.** Governance updates remain a distinct follow-up outside this planner fixture.

No task in this file crosses these boundaries.

---

## Dependencies & Execution Order

### PR-slice ordering (the canonical 18-PR no-gap stack)

- **Foundation process/setup** (T001–T004): first. It preserves the legitimate Specify-through-Analyze, archive-hygiene, setup, and confidence work identified before PR 1; it adds no implementation scope.
- **PR 1** (T005–T007): after Foundation; orphan deletion and ledger.
- **PR 13** (T121–T130): emitted early after PR 1 so scoping tooling works for later work; functionally independent of the confinement slices.
- **PR 2** (T008–T017): **before PRs 3–10.** Self-enforcing — a port PR's atomic manifest edit (FR-012) targets `suite-manifest.json`, which does not exist until PR 2 creates it, so any 3–10 PR merged first fails CI.
- **PRs 3a, 3b, 4, 5, 6, 7a, 8, 9** (T018–T087): after PR 2; mutually parallel across layers. **PR 7b (T067–T072) after PR 7a (T062–T066)** (runners build on the shared transcript lib). Soft coupling: PR 5's `validate-pr-checks-sentinel` update (T049) targets the PR-3b-ported validator — land 3b before 5 or re-port in 5.
- **PR 10** (T088–T099): **after PRs 3–9.** Self-enforcing — the guard's live `git ls-files -z` enumeration (FR-005) finds any residual non-allowlisted `.sh`, so PR 10 cannot go green until PRs 3–9 have cleaned every surface (T080/T087 are the per-surface preconditions).
- **PR 11** (T100–T108): **last among confinement PRs** (after PR 10) so preflight exercises the fully-confined tree (FR-027). Review-ordering preference — a violation yields weaker evidence, not a red `main`.
- **PR 12a** (T109–T112): release-note extraction/sanitization/validation module + focused tests; independent of the confinement stack.
- **PR 12b** (T113–T120): immutable capture/composition, workflows, enforcement, template, and docs; **depends on PR 12a**. The former combined PR 12 is blocked at exactly 1,267 production LOC versus the 800-LOC threshold, so this split has no waiver.
- **Polish/closeout** (T131–T136): final emitted review unit after all implementation slices; required by aggregate no-gap evidence, not implementation scope expansion.

### Planner Dependencies (machine-readable SPEC-908 mapping)

The planner's semantic `USn` increment IDs below are delivery-slice ordinals,
not product user-story labels. Task-level `[USn]` tags retain their original
requirements meaning.

- **Foundation**: Depends on no prerequisites. This is the process/setup review unit and includes T001–T004.
- **US1**: Depends on Foundation. This is PR 1 (T005–T007).
- **US2**: Depends on US1. This is PR 2.
- **US3**: Depends on US2. This is PR 3a.
- **US4**: Depends on US2. This is PR 3b.
- **US5**: Depends on US2. This is PR 4.
- **US6**: Depends on US4. This is PR 5; the dependency captures the shared sentinel port.
- **US7**: Depends on US2. This is PR 6.
- **US8**: Depends on US2. This is PR 7a.
- **US9**: Depends on US8. This is PR 7b.
- **US10**: Depends on US2. This is PR 8.
- **US11**: Depends on US2. This is PR 9.
- **US12**: Depends on US3, US4, US5, US6, US7, US9, US10, and US11. This is PR 10.
- **US13**: Depends on US12. This is PR 11.
- **US14**: Depends on Foundation. This is PR 12a; it is functionally independent of the confinement stack.
- **US15**: Depends on US14. This is dependent PR 12b.
- **US16**: Depends on US1. This is independent PR 13, emitted early after PR 1.
- **Polish**: Depends on US2, US3, US4, US5, US6, US7, US8, US9, US10, US11, US12, US13, US14, US15, and US16. This is the T131–T136 aggregate closeout review unit.

### Shipped-runner concurrency rule (PRs 2, 5, 7b, 8, 9, 10, 13)

All seven rewrite `speckit-pro-runner.manifest.json` sha256 proof rows + `dist/**`. When more than one is in flight, the **later-merging one rebases onto the merged one and re-runs the full payload/proof regeneration ritual** (T016/T052/T071/T078/T085/T098/T126); conflicting proof rows and payload bytes MUST NOT be hand-merged (plan §Constraints).

### Within each port slice

- Behavioral test → Python port → manifest flip → predecessor deletion → suite-green verification. Never a broken intermediate state.

### Parallel Opportunities

- **Primary fan-out**: the 20 mechanical Layer-1 ports (T018–T027, T029–T038) are all `[P]` — distinct files, no interdependency; the per-phase manifest-registration task (T028/T039) serializes only the shared `suite-manifest.json` + ledger edits.
- Across slices: PRs 3a/3b/4/5/6/7a/8/9 can be developed in parallel by different contributors once PR 2 lands.
- `[P]` within other phases: shared parity tooling (T009/T010), guard tests (T094–T096), composer components (T109–T112, T115), and most polish checks (T132/T133/T135).

---

## Implementation Strategy

### MVP (US2 — the implementation foundation everything rests on)

1. Foundation process/setup → 2. PR 1 / US1 orphan deletion → 3. early PR 13 / US16 estimator restoration → 4. **PR 2 / US2 orchestrator + manifest + parity tooling** → STOP and VALIDATE: `run-all.py` reaches bash-runner UX parity and the shipped gate reads the manifest. This is the standalone-valuable implementation MVP: the suite runs from Python.

### Incremental delivery

1. Complete Foundation: preserve process, archive-hygiene, setup, and confidence evidence for T001–T004.
2. Complete US1: PR 1 performs orphan deletion and records the ledger.
3. Complete US16: independent PR 13 lands early to restore the estimator.
4. Complete US2: PR 2 establishes the manifest and Python orchestrator.
5. Complete US3: PR 3a ports the first validator batch.
6. Complete US4: PR 3b ports the second validator batch.
7. Complete US5: PR 4 ports MOC and payload validators.
8. Complete US6: PR 5 ports Layer 5/toolchain dispatch.
9. Complete US7: PR 6 ports scripts and hooks.
10. Complete US8: PR 7a lands the transcript library.
11. Complete US9: PR 7b lands replay runners.
12. Complete US10: PR 8 lands parity runners and fixtures.
13. Complete US11: PR 9 lands live-eval runners.
14. Complete US12: PR 10 enables confinement and deletes residual Bash.
15. Complete US13: PR 11 adds container and Windows preflight.
16. Complete US14: PR 12a lands release-note extraction/sanitization/validation plus focused tests.
17. Complete US15: dependent PR 12b lands immutable capture/composition, workflows, enforcement, template, and docs.
18. Complete Polish: emit T131–T136 integrated verification, packet, hosted-evidence, and closeout history as the final no-gap review unit.

### Parallel team strategy

After PR 2 merges: Contributor A takes PRs 3a/3b/4 (Layer-1), B takes PRs 5/6 (tool-scoping/scripts/hooks), C takes PRs 7a/7b/8/9 (Layers 7/8 + live evals). PR 12a and PR 13 can run on independent tracks; PR 12b waits for PR 12a. PR 10 converges after 3–9; PR 11 follows PR 10. Foundation and Polish preserve the aggregate branch boundary and do not add implementation work.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- `[USn]` inside task lines maps each task to its product user story for 1:1 traceability; planner increment IDs are delivery ordinals. Foundation, PR-1 cleanup, and Polish tasks retain their existing unlabeled form.
- Every port PR preserves the behavior owned by its focused tests and must return a valid executed summary.
- Privacy: no absolute `/Users` or `/home` paths in any authored artifact — repo-relative only.
- Shipped-runner byte changes are confined to PRs 2/5/7b/8/9/10/13, each running the regeneration ritual with release-readiness LAST and `<home>` sanitization.
- Verify each slice with the default-suite gate + `pnpm --dir docs-site validate` before opening its PR; workflow-editing PRs (5/11/12b) update their self-referential validators in the same PR.

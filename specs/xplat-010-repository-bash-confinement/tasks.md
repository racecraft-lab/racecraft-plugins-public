---
description: "Task list for XPLAT-010 — Repository Bash Confinement and CI Dispatch Guard"
---

# Tasks: Repository Bash Confinement and CI Dispatch Guard

**Input**: Design documents from `specs/xplat-010-repository-bash-confinement/`

**Prerequisites**: plan.md, spec.md (27 FRs / 7 US / 8 SCs / 12 Clarifications), research.md (13 decisions), data-model.md (8 entities), contracts/ (6), quickstart.md (7 scenarios)

**Tests**: This feature is test-centric by nature (it ports a test harness). Every ported module lands with its `unittest` module + committed count-parity baseline in the SAME PR (FR-004/FR-011/FR-012). Test tasks are therefore first-class here, not optional.

**Reviewability**: This spec is an operator-ratified **transition exception** (refactor + infra + upgrade classes) delivered as a dependency-ordered **15-PR stack** (13 numbered slices, with slices 3 and 7 each split into a/b PRs), each PR independently CI-green and inside the 400–800 reviewable-LOC budget. The exception's sole valid provenance is `docs/ai/specs/.process/XPLAT-010-workflow.md` §Scope Budget and Split Decision — not templates, generated zones, `.process` files, PR bodies, or code fences.

**Organization**: Tasks are grouped by **PR-stack slice** (the primary grouping the workflow prompt mandates). Each task additionally carries its `[USn]` user-story label so US1–US7 traceability stays 1:1. Setup / foundational-cleanup / polish tasks carry no story label.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: `[US1]`…`[US7]` — the user story the task serves
- Exact repo-relative file paths in every task. **Privacy hard constraint**: no absolute `/Users` or `/home` paths anywhere.

## Path Conventions

- **Repo-side tooling (never shipped)**: `tests/speckit-pro/`, `scripts/`, `.claude/hooks/`, `.github/workflows/`. Repo-side Python MUST live under these roots — never under `speckit-pro/` (the `validate-plugin-payload` guard fails if `tests/`, `specs/`, or `.process/` reappear under the plugin dir).
- **Shipped runner (byte change → regeneration ritual)**: `speckit-pro/speckit_pro_runner/`. Touched only in PR 2, PR 7b, PR 10, PR 13.

---

## Per-Port Protocol (applies to every `.sh`→`.py` port task in PRs 3a–9)

Every port task is the **same-PR atomic swap** to Python 3.11+ standard library only, no new runtime dependency (FR-009/FR-011/FR-012, Clarifications Session 1):

1. **Capture VERBOSE baseline** — run the bash script under `VERBOSE=true` via `tests/speckit-pro/lib/capture_baseline.py`, in the pinned **non-root, CI-matching** environment, writing `tests/speckit-pro/parity/bash-to-python/<script>-baseline.txt` (one `NNN <canonical-name>` line per executed `_pass`/`_fail`, then `TOTAL: <N>`). One baseline per `(script, invocation-mode)` pair. Fail loud on an empty/stale name (no positional fallback).
2. **Port** — author `<module>.py` (`unittest`, house `__main__` printing `<label>: {passed}/{total} passed`), computing `{passed}/{total}` via the shared `addSubTest` `TestResult` subclass; every former assertion execution = one counted unit; loop-generated assertions are `subTest`s reconciling each bash check name 1:1 via `subTest(msg=...)`.
3. **Dual-run diff** — record the 6-item block in the PR body (bash capture cmd + port-run cmd; committed baseline path; unified name-inventory diff or `no differences — 1:1 preserved`; `bash: N == python: N`; intentional-change = `none`; count-ledger delta line).
4. **Manifest flip** — repoint the script's `suite-manifest.json` entry to the `.py` module + baseline pointer (batched per phase in that phase's manifest-registration task, same PR).
5. **`.sh` delete** — remove the bash predecessor in the same PR so no layer runs with zero coverage.

Baseline capture AND the port-side parity comparison MUST run in the SAME pinned environment; a root-vs-non-root drift (e.g. 31-vs-36 assertions) surfaces as a loud parity failure, never a silent divergence.

---

## Phase 1: Setup & Pre-flight (shared, no story label)

- [ ] T001 Verify the repo baseline is green before any change: run the toolchain preflight and default-suite gates from the repo root — `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-toolchain-preflight.json` and `.../run-default-suite.json` — and `pnpm --dir docs-site validate`. Record the pre-change `X/Y passed` headline as the parity reference.
- [ ] T002 Confirm the working branch is `xplat-010-repository-bash-confinement` (or the active slice branch), never `main`; confirm `.specify/feature.json` pins `specs/xplat-010-repository-bash-confinement`; export `PYTHONDONTWRITEBYTECODE=1` for all runner invocations.
- [ ] T003 **Reviewability checkpoint (mandatory — transition exception)**: record in the PR review packet that this spec is delivered as the ratified 15-PR transition-exception stack, provenance `docs/ai/specs/.process/XPLAT-010-workflow.md` §Scope Budget and Split Decision; confirm each planned PR slice stays within the 400–800 reviewable-LOC / 15–25 total-file budget and does not silently exceed the 800/8/25 block thresholds. If any slice would exceed the block thresholds without ratified provenance, STOP and re-split rather than adding tasks.
- [ ] T004 Confirm the 6 contracts under `contracts/` are the frozen schemas the ports/guard/composer/estimator validate against (`suite-manifest.schema.json`, `confinement-allowlist.schema.json`, `repo-bash-confinement-result.schema.json`, `estimate-spec-size.schema.json`, `release-note-block.contract.md`, `count-parity-baseline.contract.md`).

**Checkpoint**: Baseline green, branch verified, split exception recorded — implementation can begin.

---

## Phase 2: PR 1 — Orphan-test deletion + disposition ledger (FR-016; anytime, no dependency)

**Slice goal**: Delete the 34 orphaned/wrapper Bash test scripts (never port them) with a committed rationale ledger. Foundational cleanup; carries no user-story label.

- [ ] T005 Census & classify every `tests/speckit-pro/unit/*.sh` (46 files) into `orphan-target-deleted` (Layer-4 `test-*.sh` whose subject under `speckit-pro/**` was already ported+deleted by XPLAT-009), `redundant-wrapper` (`test-speckit-pro-runner.sh`, `test-speckit-pro-read-only-helpers.sh` — pure `python3 …` shims around shipped `.py`), or `active-port-later` (the ~12 genuinely active scripts ported in their subject's layer PR). Confirm the 34-delete / ~12-port split. `test-estimate-spec-size.sh` is NOT an orphan — its subject is restored in PR 13; exclude it from deletion.
- [ ] T006 Delete the 32 target-deleted orphans + 2 redundant wrappers (34 files under `tests/speckit-pro/unit/`) identified in T005. Git history preserves their content; do not port.
- [ ] T007 Write `docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md` with one `{path, kind, rationale}` row per deleted file (FR-016), then run the default-suite gate and confirm it stays green (no manifest reference to a deleted file).

**Checkpoint**: 34 orphan `.sh` gone, ledger complete, suite green.

---

## Phase 3: PR 2 — Suite manifest + `run-all.py` orchestrator + manifest-reading gate + shared parity tooling (US1; blocks PRs 3–10) 🎯 MVP

**Slice goal (US1 — Cross-Platform Python Suite Orchestrator)**: The full deterministic suite runs from Python with the bash runner's flags/headline/exit codes; the shipped gate reads the manifest, not the bash runner. **Shipped-runner PR — carries the regeneration ritual.**

**Independent Test**: On a machine with only Python 3.11+ (no Bash, no `jq`), `python3 tests/speckit-pro/run-all.py --all`, `--layer N`, and the toolchain preflight match the recorded bash-runner `X/Y passed` headline, scope, and exit codes.

- [ ] T008 [US1] Author `tests/speckit-pro/suite-manifest.json` per `contracts/suite-manifest.schema.json`: top-level `{schema_version, layers[]}`; per layer `{id, label, default, execution, live_only, integration, counted_in_total, dispatch, scripts[]}`; per script `{path, label, baseline}` (baseline = repo-relative pointer or `null`). Assign per-layer `dispatch` per research §D3 (toolchain=`internal-check`,`counted_in_total:false`; layers 1/4=`python-module`; 5=`internal-check` transitional; 7/8=`python-module`; 2/3/6=`python-module`+`live_only:true`); list still-unported layers as `shell-legacy-transitional` until their port-PR boundary (FR-006/FR-007).
- [ ] T009 [P] [US1] Author `tests/speckit-pro/lib/test_result.py` — the shared `unittest.TestResult` subclass overriding `addSubTest` so `{passed}/{total}` counts every executed assertion (loop-generated AND non-loop grouped), reconciling bash check names 1:1 — the house-convention per-assertion counting contract (FR-010, research §D6, Clarifications Session 1). Land its own unit test.
- [ ] T010 [P] [US2] Author `tests/speckit-pro/lib/capture_baseline.py` — runs a bash script under `VERBOSE=true`, parses only lines matching `^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$`, writes the frozen baseline format (`NNN <name>` + `TOTAL: <N>`) to `tests/speckit-pro/parity/bash-to-python/`, records the pinned capture environment, and fails loud on an empty/stale name (research §D6; `contracts/count-parity-baseline.contract.md`). Create the `tests/speckit-pro/parity/bash-to-python/` directory. Land its own unit test.
- [ ] T011 [US2] Create the running count ledger `docs/ai/specs/.process/XPLAT-010-count-ledger.md` (header + empty delta table) that each subsequent port PR appends one line to (FR-013).
- [ ] T012 [US1] Author `tests/speckit-pro/run-all.py` reproducing `run-all.sh` UX 1:1 (research §D5): flags `--live`, `--layer N`, `--integration`, `--all`, `--verbose`; default run = Layers 1, 4, 5 + toolchain; headline `speckit-pro test suite: X/Y passed` (and `… (Z failed)` on failure); exit 0 iff no failures, 1 on failure, 2 on unknown flag; parse each child module's `X/Y passed` line. Child-outcome disposition mirrors the prior runner (FR-006): a crash (nonzero, no headline) forces exit 1 distinct from a transitional-skip; a zero-exit-no-headline module is a no-summary pass; a `shell-legacy-transitional` layer on a Bash-absent platform is skipped with an explicit diagnostic (never a silent green).
- [ ] T013 [US1] Modify `tests/speckit-pro/run-layer-scripts.py` to read the manifest's per-layer `scripts[]` instead of text-parsing `run-all.sh` via `re.findall(...)` (research §D4 — this is the real "regex-parses the bash runner" surface).
- [ ] T014 [US1] Modify `speckit-pro/speckit_pro_runner/gates/suite.py` so `DEFAULT_SUITE`/`EXTENDED_SUITE`/`ALLOWED_LAYERS` derive solely from the manifest, failing closed when it is absent/unreadable, while preserving the existing envelope contract unchanged (FR-007/FR-008).
- [ ] T015 [US1] Add the deterministic drift-guard test asserting the shipped gate's advertised roster AND dispatch kinds equal the manifest exactly (FR-007), plus the two manifest-integrity invariants: (a) every `scripts[].path` resolves to an existing repo file; (b) no layer carries `dispatch: shell-legacy-transitional` after PR 10 (terminal-absence assertion). Delete the now-replaced `tests/speckit-pro/run-all.sh` in this PR (replaced by `run-all.py`).
- [ ] T016 [US1] **Shipped-runner regeneration ritual (PR 2)**: recompute `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` sha256 rows → `python3 scripts/build-plugin-payloads.py` (rebuild `dist/**`) → checksum-based fixture sync (`--checksum`, avoids the mtime trap) → per-row proof-hash recompute → regenerate evidence in gate order with **release-readiness LAST** and home-directory sanitization (`<home>`). If PR 10 or PR 13 has merged first, rebase onto it and re-run this full ritual (hand-merging conflicting proof rows / payload bytes is forbidden — plan §Constraints).
- [ ] T017 [US1] Verify US1 end-to-end (quickstart US1): `run-all.py --all` headline + exit code match the T001 reference; the shipped suite gate resolves its roster from the manifest with the envelope unchanged; default-suite gate + `pnpm --dir docs-site validate` green.

**Checkpoint**: Manifest is the single source of truth; `run-all.py` reaches UX parity; parity tooling + ledger ready for the ports. **PR 2 must merge before PRs 3–10.**

---

## Phase 4: PR 3a — Layer-1 validators port, batch 1 of 2 (US2; after PR 2) — primary [P] fan-out

**Slice goal (US2 — Runtime Count-Parity Proof Per Port)**: Port 10 mechanical Layer-1 structural validators with committed baselines + dual-run diffs. Each port follows the Per-Port Protocol above.

- [ ] T018 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-agents.sh` → `.py` (Per-Port Protocol).
- [ ] T019 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh` → `.py` (Per-Port Protocol).
- [ ] T020 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh` → `.py` (Per-Port Protocol).
- [ ] T021 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-agents.sh` → `.py` (Per-Port Protocol).
- [ ] T022 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-hooks.sh` → `.py` (Per-Port Protocol).
- [ ] T023 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-marketplace.sh` → `.py` (Per-Port Protocol).
- [ ] T024 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-parity.sh` → `.py` (Per-Port Protocol).
- [ ] T025 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-plugin.sh` → `.py` (Per-Port Protocol).
- [ ] T026 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-curated-set.sh` → `.py` (Per-Port Protocol). Note: check names are driven by live `scripts/curated-set.json` content — that data file is a baseline regeneration trigger.
- [ ] T027 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-hooks.sh` → `.py` (Per-Port Protocol).
- [ ] T028 [US2] Register the 10 ported modules + baseline pointers in `suite-manifest.json` (batched manifest flip), append the 10 count-ledger delta lines (FR-013), and confirm the default-suite gate + drift-guard test are green.

**Checkpoint**: 10 Layer-1 validators ported with 1:1 parity; 10 `.sh` deleted.

---

## Phase 5: PR 3b — Layer-1 validators port, batch 2 of 2 (US2; after PR 2) — primary [P] fan-out

**Slice goal (US2)**: Port the remaining 10 mechanical Layer-1 validators. Per-Port Protocol each.

- [ ] T029 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh` → `.py` (Per-Port Protocol).
- [ ] T030 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-plugin-payload.sh` → `.py` (Per-Port Protocol).
- [ ] T031 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-plugin.sh` → `.py` (Per-Port Protocol).
- [ ] T032 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh` → `.py` (Per-Port Protocol). Coupling note: PR 5 updates this ported validator for the dispatch swap — land 3b before 5, or PR 5 re-ports it.
- [ ] T033 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-process-gitattributes.sh` → `.py` (Per-Port Protocol).
- [ ] T034 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-release-workflow.sh` → `.py` (Per-Port Protocol). Coupling note: PR 12 updates this ported validator for the composer job.
- [ ] T035 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-scripts.sh` → `.py` (Per-Port Protocol).
- [ ] T036 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-skill-capability-pointers.sh` → `.py` (Per-Port Protocol).
- [ ] T037 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-skills.sh` → `.py` (Per-Port Protocol).
- [ ] T038 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-spec-index-determinism.sh` → `.py` (Per-Port Protocol).
- [ ] T039 [US2] Register the 10 ported modules + baseline pointers in `suite-manifest.json`, append the 10 count-ledger delta lines, and confirm the default-suite gate + drift-guard test are green.

**Checkpoint**: All 20 mechanical Layer-1 validators ported; 20 `.sh` deleted.

---

## Phase 6: PR 4 — MOC lints + codex-skills/payload-conformance validators (US2; after PR 2)

**Slice goal (US2)**: Port the 4 remaining Layer-1 validators (MOC + codex/payload). Per-Port Protocol each; these carry heavier logic than the mechanical 20.

- [ ] T040 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` → `.py` (Per-Port Protocol). Note: the optional scan-root argument is a second invocation mode (29 vs 0 assertions) → one baseline per `(script, mode)` pair.
- [ ] T041 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh` → `.py` (Per-Port Protocol).
- [ ] T042 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-codex-skills.sh` → `.py` (Per-Port Protocol).
- [ ] T043 [P] [US2] Port `tests/speckit-pro/layer1-structural/validate-payload-conformance.sh` → `.py` (Per-Port Protocol).
- [ ] T044 [US2] Register the 4 ported modules + baseline pointers in `suite-manifest.json`, append the 4 count-ledger delta lines, and confirm the default-suite gate + drift-guard test are green.
- [ ] T045 [US2] Port the active Layer-4 MOC test scripts co-located with these validators if flagged `active-port-later` in T005 (e.g. `test-moc-id-normalize.sh`, `test-moc-lint-exit-codes.sh`, `test-generate-spec-index.sh`) → `.py` under `unit/` (Per-Port Protocol); otherwise confirm they were deleted as orphans in PR 1. Note the root-vs-non-root divergence recorded for `test-moc-lint-exit-codes.sh` (31 vs 36) — capture in the pinned non-root env.

**Checkpoint**: All 24 Layer-1 validators ported.

---

## Phase 7: PR 5 — Layer-5 tool scoping + toolchain check + `pr-checks.yml` dispatch swap (US2 + FR-026; after PR 2)

**Slice goal (US2 port + FR-026 workflow-shell reduction)**: Port Layer-5, replace the residual `bash tests/speckit-pro/check-toolchain.sh` CI dispatch with a direct Python-runner invocation, and retire the vacuous native `check_layer5`.

- [ ] T046 [US2] Port `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` → `.py` (Per-Port Protocol). Replace the vacuously-true native `check_layer5` body in `gates/suite.py` with the real tool-scoping validator, then retire `check_layer5` at this boundary per research §D3 (no permanent equivalence shim — FR-008).
- [ ] T047 [US2] Port `tests/speckit-pro/check-toolchain.sh` (top-level) → Python and its active Layer-4 test `test-check-toolchain.sh` → `.py` (Per-Port Protocol); delete both `.sh`.
- [ ] T048 [US2] Swap the `bash tests/speckit-pro/check-toolchain.sh` dispatch step in `.github/workflows/pr-checks.yml` (~line 289) for a direct Python-runner toolchain-preflight invocation (FR-026). This replaces a `run:` step inside the existing `test`/`validate-plugins` surface — it renames no required status check.
- [ ] T049 [US2] Update the ported `validate-pr-checks-sentinel` self-referential workflow validator in the SAME PR so its assertions match the swapped `pr-checks.yml` (FR-026).
- [ ] T050 [US2] Register the Layer-5 module flip (`internal-check`→`python-module` if the ported validator lives repo-side, per §D3) + baseline pointers in `suite-manifest.json`; append count-ledger delta lines.
- [ ] T051 [US2] Add a PR-body branch-protection callout stating this PR is **required-check-neutral** (no branch-protection change — contrast PRs 11/12) per FR-026/FR-018.
- [ ] T052 [US2] Confirm default-suite gate + drift-guard test green; confirm `pr-checks.yml` still dispatches the Python runner for the toolchain leg.
- [ ] T053 [US2] Record the CLAUDE.md CI/CD note: confirm whether the `pr-checks.yml` edit requires a CLAUDE.md CI/CD-section update (per repo policy on workflow edits).

**Checkpoint**: Layer 5 + toolchain ported; the last residual CI Bash dispatch step is Python; native `check_layer5` retired.

---

## Phase 8: PR 6 — `scripts/**` + `.claude/hooks/**` ports (US2 + FR-014; after PR 2)

**Slice goal (US2 port + FR-014 hook contract)**: Port the two helper scripts and two hook handlers to stdlib Python, dropping the `jq` holdout and preserving the hook stdin-JSON / exit-0-or-2 contract.

- [ ] T054 [P] [US2] Port `scripts/refresh-local-plugin.sh` → `.py` (Per-Port Protocol via its active Layer-4 test `test-refresh-local-plugin.sh`). It already calls `python3 build-plugin-payloads.py`; preserve behavior, delete the `.sh`.
- [ ] T055 [P] [US2] Port `scripts/sync-marketplace-versions.sh` → `.py` (the 12-call `jq` holdout; research §D12) via its active Layer-4 test `test-sync-marketplace-versions.sh`; delete the `.sh` and drop the `jq` dependency.
- [ ] T056 [P] [US2] Port `.claude/hooks/guard-version-triplet.sh` (PreToolUse) → `.claude/hooks/guard-version-triplet.py`, preserving the stdin-JSON intake and exit-0 (allow) / exit-2 (block) contract; parse stdin via stdlib `json`, never shell-interpolating untrusted input into a subprocess (FR-014). Preserve the contract even for malformed input.
- [ ] T057 [P] [US2] Port `.claude/hooks/validate-structural.sh` (PostToolUse) → `.claude/hooks/validate-structural.py`, preserving the exit-0/2 contract and replacing its `bash tests/run-all.sh --layer 1` shell-out with a Python Layer-1 dispatch (research §D12).
- [ ] T058 [US2] Port the active Layer-4 tests for the ported helpers/hooks (per T005 classification) → `.py` following the Per-Port Protocol; delete their `.sh`.
- [ ] T059 [US2] Register the ported modules + baseline pointers in `suite-manifest.json`; append count-ledger delta lines; confirm default-suite gate green.
- [ ] T060 [US2] Confirm the hooks stay off the shell-injection surface: assert no `subprocess`/`os.system` call in the ported hooks passes untrusted stdin into a shell (aligns with the FR-002 guard's own rule and FR-023 discipline).
- [ ] T061 [US2] Verify `pnpm --dir docs-site validate` still green (the `docs-site/package.json` `scripts` values are within the FR-002 structural-scan surface — confirm no `bash`/`jq` invocation was introduced).

**Checkpoint**: `scripts/**` and `.claude/hooks/**` are Python; `jq` holdout removed.

---

## Phase 9: PR 7a — Layer-7 shared transcript library (US2; after PR 2; before PR 7b)

**Slice goal (US2)**: Port the shared Layer-7 transcript library first so the replay runners can build on it.

- [ ] T062 [US2] Port `tests/speckit-pro/layer7-integration/lib/transcript-helpers.sh` → `.py` (Per-Port Protocol via active Layer-4 test `test-transcript-helpers.sh`).
- [ ] T063 [P] [US2] Port `tests/speckit-pro/layer7-integration/scrub-transcript.sh` → `.py` (Per-Port Protocol).
- [ ] T064 [P] [US2] Port `tests/speckit-pro/layer7-integration/reduce-transcript-fixture.sh` → `.py` (Per-Port Protocol).
- [ ] T065 [US2] Port the active Layer-4 test `test-transcript-helpers.sh` → `.py`; delete its `.sh`.
- [ ] T066 [US2] Register the ported transcript-lib modules + baseline pointers in `suite-manifest.json`; append count-ledger delta lines; confirm default-suite gate green.

**Checkpoint**: Layer-7 transcript library is Python; PR 7b can build the runners on it.

---

## Phase 10: PR 7b — Layer-7 replay runners (US2; after PR 7a)

**Slice goal (US2)**: Port the Layer-7 replay-mode runners; retire the native `check_layer7`.

- [ ] T067 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-dispatch-fixtures.sh` → `.py` (Per-Port Protocol; replay mode).
- [ ] T068 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-return-format-fixtures.sh` → `.py` (Per-Port Protocol; replay mode).
- [ ] T069 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-grounding-fixtures.sh` → `.py` (Per-Port Protocol; replay mode).
- [ ] T070 [P] [US2] Port `tests/speckit-pro/layer7-integration/run-e2e-fixtures.sh` and `run-all-fixtures.sh` → `.py` (Per-Port Protocol; replay mode). Preserve `--live` semantics as a code path (live mode still invokes `claude -p`; replay stays free).
- [ ] T071 [US2] Retire the native `check_layer7` in `gates/suite.py` at this boundary (it validated an orphaned fixture directory; no equivalence shim — FR-008); flip Layer-7 to `python-module` in `suite-manifest.json` + baseline pointers; append count-ledger delta lines; run the shipped-runner payload/proof regeneration ritual with release-readiness LAST and `<home>` sanitization.
- [ ] T072 [US2] Confirm default-suite gate + drift-guard test green; replay-mode Layer-7 runs Python-only.

**Checkpoint**: Layer-7 replay harness is Python; native `check_layer7` retired.

---

## Phase 11: PR 8 — Layer-8 parity runner + fixture conversion (US2; after PR 2)

**Slice goal (US2)**: Port the Layer-8 parity runner + its `jq`-dependent libs and convert the 8 per-case `env-*.sh` fixture scripts to Python/data so PR 10's guard finds zero non-allowlisted `.sh` (research §D11). Retire native `check_layer8`.

- [x] T073 [P] [US2] Port `tests/speckit-pro/layer8-parity/lib/extractors.sh` → `.py` (Per-Port Protocol via active Layer-4 test `test-parity-extractors.sh`).
- [x] T074 [P] [US2] Port `tests/speckit-pro/layer8-parity/lib/judge.sh` → `.py` (Per-Port Protocol via active Layer-4 test `test-parity-judge.sh`). **Boundary guard**: keep the existing tolerance arms (`byte-identical`, `exact`, `tolerance-1`) only — the `semantic-equivalent` LLM judge stays skipped-with-warning (design-concept Non-goal; see Boundary Guards).
- [x] T075 [US2] Port `tests/speckit-pro/layer8-parity/run-parity-fixtures.sh` → `.py`, dropping the `jq` dependency (Per-Port Protocol); preserve `--dry-run` (free structural validation) and `--live --budget-usd` semantics.
- [x] T076 [P] [US2] Convert the 8 per-case `env-fallback.sh`/`env-teams.sh` fixture scripts under `layer8-parity/0{1,2,3,4}-*/` to Python/data (the environment-selection inputs the real validator requires); delete the 8 `.sh`.
- [x] T077 [US2] Port the active Layer-4 tests `test-parity-extractors.sh` and `test-parity-judge.sh` → `.py`; delete their `.sh`.
- [x] T078 [US2] Retire the native `check_layer8` in `gates/suite.py` at this boundary (it covered only 3 of 6 required files; no equivalence shim — FR-008); flip Layer-8 to `python-module` in `suite-manifest.json` + baseline pointers. **Shipped-runner regeneration ritual (PR 8)**: because this changes `gates/suite.py`, rebuild manifests/payloads/cache proofs and regenerate evidence in gate order with release-readiness LAST and `<home>` sanitization.
- [x] T079 [US2] Append the Layer-8 delta lines to `docs/ai/specs/.process/XPLAT-010-count-ledger.md`; confirm default-suite gate + drift-guard test green.
- [x] T080 [US2] Confirm `git ls-files -- ':(glob)tests/speckit-pro/layer8-parity/**/*.sh'` returns empty (all Layer-8 `.sh` converted/deleted) — the PR-10 guard precondition for this surface.

**Checkpoint**: Layer-8 parity harness is Python; all Layer-8 `.sh` gone; native `check_layer8` retired.

---

## Phase 12: PR 9 — Live-AI eval runners, Layers 2/3/6 (US2 + FR-015; after PR 2)

**Slice goal (US2 port + FR-015)**: Port the live-AI eval runners preserving their CLI argument contracts and codex staging semantics. These are `live_only` (not in the default deterministic suite).

- [x] T081 [P] [US2] Port `tests/speckit-pro/layer2-trigger/run-trigger-evals.sh`, `run-trigger-evals-codex.sh`, `run-trigger-loop.sh` → `.py`, preserving CLI args + codex staging (FR-015; Per-Port Protocol where `_pass`/`_fail` output exists, else CLI/exit parity). Preserve the Bash `EXIT`-trap restoration guarantee under `SIGHUP`/`SIGTERM`; the safer Python restore-collision path intentionally exits `2` while preserving the backup and must be recorded as an intentional change.
- [x] T082 [P] [US2] Port `tests/speckit-pro/layer3-functional/run-functional-evals.sh`, `run-functional-evals-codex.sh` → `.py`, preserving CLI args + codex staging (FR-015).
- [x] T083 [P] [US2] Port `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.sh` and `lib/quality-scorer.sh`, `lib/token-counter.sh` → `.py` (FR-015), invoking exact resolved Claude/Codex paths, using Windows-safe result filenames and explicit UTF-8 subprocess decoding, preserving command-substitution prompt bytes, and keeping partial result JSON valid with temporary-file cleanup on spawn failure.
- [x] T084 [US2] Port the active Layer-4 tests `test-efficiency-codex-runner.sh` and `test-eval-runner-skill-selection.sh` → `.py` (Per-Port Protocol); delete their `.sh`. Add separate Layer-2 signal-restoration and Layer-6 portability contracts so supplemental cross-platform coverage is not misrepresented as predecessor name parity.
- [x] T085 [US2] Register Layers 2/3/6 as `python-module` + `live_only:true` in `suite-manifest.json` per §D3 (not in the default deterministic suite); append count-ledger delta lines. Replace the shipped suite gate's hardcoded AI runner paths with the manifest `scripts[]` entries, then run the full shipped-runner regeneration ritual with release-readiness LAST and `<home>` sanitization.
- [x] T086 [US2] Confirm predecessor scope exactly: bare `run-all.py --live` keeps default Layers 1/4/5, while `run-all.py --all` selects Layers 2/3/6 (and enables live mode) alongside the other runner blocks; each live-only layer emits Python command plans and the default deterministic gate is unaffected.
- [x] T087 [US2] Confirm `git ls-files -- ':(glob)tests/speckit-pro/layer2-trigger/**/*.sh' ':(glob)tests/speckit-pro/layer3-functional/**/*.sh' ':(glob)tests/speckit-pro/layer6-efficiency/**/*.sh'` returns empty — the PR-10 guard precondition for these surfaces.

**Checkpoint**: Live-AI eval runners are Python; all Layers 2–8 ported. PRs 3–9 complete → PR 10 can proceed.

---

## Phase 13: PR 10 — Repository Bash confinement guard + final Bash deletion (US3; after PRs 3–9) 🎯 headline policy

**Slice goal (US3 — Repository Bash Confinement Guard)**: Add the bash-scoped confinement guard (live `git ls-files -z`, fail-closed 10-file `.specify/**` allowlist), compose it into CI + release readiness, and delete the last repo-local `.sh`. **Shipped-runner PR — carries the regeneration ritual.**

**Independent Test**: Feed the guard three trees — clean / stray new `.sh` outside `.github/workflows/` / non-allowlisted Bash under `.specify/**` — and confirm it passes the first and fails the other two (fail-closed).

- [x] T088 [US3] Author the `allowlist.json` fixture at `tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json` per `contracts/confinement-allowlist.schema.json`: `{schema_version, feature_id:"XPLAT-010", entries[]}`, `additionalProperties:false`, `release_readiness_excluded:true` required on every entry, `minItems`/`maxItems` 10, pinning the exact 10 canonical `vendored_specify_helper` paths (4 `.specify/extensions/git/scripts/bash/*.sh` + 6 `.specify/scripts/bash/*.sh`). The 4 vendored `.ps1` get no entry (FR-003).
- [x] T089 [US3] Add the `repo-bash-confinement` operation to `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`: live `["git","ls-files","-z"]` argv enumeration from repo root (never `shell=True`); bash-scoped detection vocabulary — own suffix tuple `(".sh",".bash")` + Bash-family shebang normalizer treating `#!/bin/sh` as in-scope (research §D2); own command-name set `{"bash","bash.exe","jq","jq.exe"}` (research §D1, NOT the XPLAT-009 superset); `.github/workflows/` post-enumeration Python filter; resolved-path symlink confinement. Fail closed with a missing-prerequisite diagnostic when git is unavailable (FR-001/FR-002).
- [x] T090 [US3] Implement the FR-002 invocation-text detection surfaces precisely: Python files via AST inspection of `subprocess`/`os.system` args (reuse `command_argv_contains_forbidden` / `shell_c_payload_has_forbidden_command`); structural JSON-value scans of `**/hooks.json` `command` fields and `**/package.json` `scripts` values. Do NOT text-scan prose/Markdown/YAML/fixtures/baselines. Content-probe robustness: an unreadable/binary/undecodable first line yields no shebang and is classified by path suffix alone — never a scan-aborting error, never a false Bash finding (FR-002).
- [x] T091 [US3] Implement the fail-closed allowlist loader in `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` with the exact-canonical-set assertion (FR-003): accept only the `vendored_specify_helper` path scope; assert the allowlist content equals the enumerated 10 canonical paths so a same-scope substitution or a delete-and-substitute is a red event, not reviewer-trusted; any `.specify/**` Bash file not on the list is a blocking finding.
- [x] T092 [US3] Register the new guard op in `gates/registry.py` and compose the `repo_bash_confinement` check into the release-readiness assembly in `gates/release.py` (pass iff `blocking_count == 0`), surfacing allowlisted entries under `release_readiness_excluded:true` and excluding them from the positive Bash-free evidence set (FR-004/FR-005).
- [x] T093 [US3] Add the live-scan guard case to the default deterministic suite (manifest + fixture request under `fixtures/repository-bash-confinement/requests/`), performing a live repo-wide enumeration (never a fixed list) so newly added files are always scanned (FR-005).
- [x] T094 [P] [US3] Author `tests/speckit-pro/unit/test-repo-bash-confinement.py` + the `confinement-guard-cases.json` fixture: clean tree passes; stray `.sh` outside `.github/workflows/` fails; non-allowlisted `.specify/**` Bash fails; prose mention passes; `hooks.json`/`package.json` invocation fails; each of the 10 allowlisted files accepted + `release_readiness_excluded:true`. Validate results against `contracts/repo-bash-confinement-result.schema.json`.
- [x] T095 [P] [US3] Add the FR-004 negative-control test in `tests/speckit-pro/unit/test-repo-bash-confinement.py`: an allowlisted (`release_readiness_excluded:true`) entry can NEVER count as positive Bash-free evidence — the claim is satisfied only by `blocking_count == 0`.
- [x] T096 [P] [US3] Add the FR-005 durability test in `tests/speckit-pro/unit/test-repo-bash-confinement.py`: the `repo_bash_confinement` check remains composed in the release-readiness assembly AND the guard case remains present in the default-suite roster (a future edit dropping either fails CI).
- [x] T097 [US3] **Final Bash deletion**: delete `tests/speckit-pro/lib/assertions.sh` and any remaining ported `.sh` stragglers; run the guard live and confirm `git ls-files '*.sh' | grep -v '^.github/workflows/' | grep -v '^.specify/'` is empty (SC-001). Confirm the manifest carries zero `shell-legacy-transitional` entries (FR-007 terminal-absence assertion now holds).
- [x] T098 [US3] **Shipped-runner regeneration ritual (PR 10)**: manifest sha256 recompute → `build-plugin-payloads.py` → checksum-based fixture sync → per-row proof-hash recompute → evidence regeneration in gate order, **release-readiness LAST**, `<home>` sanitized. If PR 2 or PR 13 has merged first, rebase onto it and re-run the full ritual (no hand-merged proof rows — plan §Constraints).
- [x] T099 [US3] Verify US3 end-to-end (quickstart US3): clean tree passes; stray-`.sh` and non-allowlisted `.specify/**` trees fail closed; default-suite + release-readiness gates green; `pnpm --dir docs-site validate` green. No new required status check added (rides the `validate-plugins` sentinel + release-readiness leg — FR-005).

**Checkpoint**: Confinement guard live and composed into CI + release readiness; zero non-allowlisted `.sh` remain (SC-001/SC-004).

---

## Phase 14: PR 11 — Container / Windows preflight CI (US4; last among confinement PRs)

**Slice goal (US4 — Container and Runner Preflight CI)**: Add `container-preflight.yml` — Linux amd64/arm64 gating, Windows x64/ARM64 advisory — running against the fully-confined tree (hence last among confinement PRs).

**Independent Test**: Trigger via manual dispatch plus runner/gate and docs-only PR changes; confirm relevant changes run heavy jobs, docs-only changes produce successful no-op sentinels, Linux contexts are required, Windows jobs are `continue-on-error`, and each executed role uploads evidence.

- [x] T100 [US4] Author `.github/workflows/container-preflight.yml` with a workflow-level `permissions: {}` default and per-job minimal grants (`contents: read` for checkout; evidence upload uses the built-in token) — matching the `pr-checks.yml`/`deploy-docs.yml` least-privilege convention (FR-017).
- [x] T101 [US4] Configure an always-reporting PR trigger plus `workflow_dispatch`; put runner/gate/workflow path detection inside a lightweight job so docs-only PRs skip heavy execution while both required sentinels still report (FR-017).
- [x] T102 [US4] Add Linux amd64 + arm64 container jobs running the SAME entrypoints CI uses — toolchain preflight, deterministic suite gate, the no-Bash/`jq` confinement guard, and the relevant release-readiness checks — as **gating** checks (FR-018/FR-027).
- [x] T103 [US4] Add Windows x64 + ARM64 direct-runner smoke jobs as `continue-on-error` advisory, running ordered Python 3.11+ discovery (`py -V:3`, `py -3`, `python`, `python3`) plus runner `runtime-info`/`preflight` (FR-019/FR-027). Record official support tier and configured enablement in an Ubuntu control job before either Windows job queues; stable x64 defaults enabled, public-preview ARM64 defaults disabled, and repository variables/manual inputs provide explicit overrides.
- [x] T104 [US4] Add the evidence-artifact upload to every job with `if: always()` semantics so a FAILING preflight still captures evidence without masking an entrypoint failure or flipping a passing gate (FR-020). Evidence is never treated as native installed-plugin UAT (XPLAT-008 remains the release-claim gate).
- [ ] T105 [US4] Add the PR-body branch-protection callout: PR 11 adds TWO new required Linux check names — they must be added to branch protection manually (GitHub does not auto-register), mirroring the FR-022 callout style (FR-018).
- [x] T106 [US4] Update the self-referential workflow validator(s) so the new `container-preflight.yml` passes structural validation in the same PR.
- [x] T107 [US4] Record the CLAUDE.md CI/CD note confirming whether the new workflow requires a CLAUDE.md CI/CD-section update.
- [ ] T108 [US4] Verify US4 end-to-end (quickstart US4): manual dispatch and a relevant PR run heavy jobs; a docs-only PR runs the workflow but skips heavy jobs; stable Linux gating contexts, Windows advisory behavior, and always-run evidence are correct (SC-008).

**Checkpoint**: Preflight CI live; Linux gates, Windows advises, evidence uploaded.

---

## Phase 15: PR 12 — Release-notes composer + `validate-release-note` check (US5 + US6; independent)

**Slice goal (US5 public Highlights + US6 enforcement)**: Add the deterministic stdlib composer that rewrites the Release body with plain-English Highlights + commit appendix, plus the required `validate-release-note` check, PR template, and skip label.

**Independent Test (US5)**: Run the composer against commits since a prior tag whose PR bodies carry `release-note` blocks; the rewritten body opens with Highlights and retains the commit list as an appendix. **(US6)**: a feat PR without a block fails the check; adding the block passes; `release-note/skip` passes without a block.

- [ ] T109 [P] [US5] Author `scripts/compose-release-notes.py` (stdlib `urllib` only, no LLM, no new secret): discover PRs via the GitHub Compare API `GET .../compare/{prev_tag}...{new_tag}` (prev tag from the release action's body-output compare-link heading), extract each PR number from the trailing `(#N)` on every commit subject; resolve the release id by tag (`GET .../releases/tags/{tag}`) then `PATCH` the body; idempotent (appendix derived from the `body` output, never the live body) (FR-023/FR-024).
- [ ] T110 [P] [US5] Implement the sanitization + fence-extraction layer in the composer: single anchored CommonMark-nesting-aware fence match (info-string `release-note`, closing run ≥ opening), exactly one match; strip raw HTML + image markdown entirely; neutralize leading `-`/`*`/`#` on extracted lines; cap at 2,000 chars (truncate-and-mark, not a failure); env-var/JSON-only intake, never shell interpolation (FR-021/FR-023).
- [ ] T111 [P] [US5] Implement the fallback + fail-loud rules: skip-labeled PRs omitted from Highlights (kept in appendix); missing-block feat/fix degrades to de-prefixed title; zero blocks → all degrade + appendix always present; fail loud (`release_note_composition_failed` + red run, no in-process retry) on a Compare API error, truncated/paginated response, unresolvable `(#N)`, or any transient/HTTP 403/429/5xx on the three API calls (FR-023). Composer failure after publication leaves the release intact with the raw body (Edge Case).
- [ ] T112 [P] [US5] Author `tests/speckit-pro/unit/test-compose-release-notes.py` covering discovery, sanitization, fence extraction, fallbacks, idempotency (byte-identical re-run), and fail-loud paths (`--dry-run` offline fixtures).
- [ ] T113 [US5] Add the `compose-release-notes` job to `.github/workflows/release.yml` as its OWN job with `needs:` on the publishing job, gated on `steps.release.outputs['speckit-pro--release_created']`, carrying `permissions: {contents: write}` only — never inheriting `actions:write`/`pull-requests:write`, never using `RELEASE_PLEASE_TOKEN` (research §D9; FR-024).
- [ ] T114 [US6] Add the required `validate-release-note` check (workflow): runs on `opened, reopened, synchronize, edited, labeled, unlabeled, ready_for_review`; scopes to releasable types only (`feat`/`fix` incl. scoped + `!`-breaking); skips drafts; exempts release-please's own PRs (chore short-circuit + `autorelease:` label, title from `inputs.pr_title` on the dispatch path); ALL untrusted text (PR body AND `inputs.pr_title`) via env vars, never shell interpolation (FR-022).
- [ ] T115 [P] [US6] Author `.github/pull_request_template.md` seeding the empty `release-note` fenced block under a `## Release note` heading (FR-021).
- [ ] T116 [US6] Create the `release-note/skip` label (verified absent today) as part of landing this PR (FR-022).
- [ ] T117 [US6] Add the PR-body branch-protection callout: `validate-release-note` is a NEW required status check name — add it to branch protection manually (FR-022).
- [ ] T118 [US5] Update the ported `validate-release-workflow` self-referential validator (`tests/speckit-pro/layer1-structural/validate-release-workflow.py`) in the SAME PR to match the new composer job + permissions shape.
- [ ] T119 [US5] Record the CLAUDE.md CI/CD note confirming whether the `release.yml` edit requires a CLAUDE.md CI/CD-section update; confirm CHANGELOG.md remains the machine-generated ledger (untouched by the composer).
- [ ] T120 [US6] Verify US5 + US6 end-to-end (quickstart US5/US6): composer dry-run produces Highlights + appendix, byte-identical on re-run; feat PR without block fails, with block passes, `release-note/skip` passes without a block (SC-005/SC-006).

**Checkpoint**: Public-readable Release Highlights + enforced release-note blocks.

---

## Phase 16: PR 13 — Spec-size estimator restored + manifest-version fix (US7; independent, land early)

**Slice goal (US7 — Restored Spec-Size Estimator)**: Restore the `estimate-spec-size` runner op and fix the confirmed manifest-version staleness defect. **Shipped-runner PR — carries the regeneration ritual.**

**Independent Test**: Send the size signals grill-me/speckit-prd emit and confirm a populated `{estimated_loc, suggested_slices, status}` matching the golden fixtures.

- [ ] T121 [US7] Register `estimate-spec-size` as a new `HelperEntry` in `speckit-pro/speckit_pro_runner/helpers/registry.py` (`{helper_id, operation, script, promotion_status, comparison_mode, authoritative_command}`), distinct from the existing `estimate-reviewable-loc` helper (research §D7).
- [ ] T122 [US7] Implement `estimate-spec-size` in `speckit-pro/speckit_pro_runner/helpers/read_only.py` via `run_registered_helper`: inputs = size signals `{user_stories, files, frs}` (lenient coercion of non-numeric/negative); output = `{estimated_loc (int ≥ 0), suggested_slices (int ≥ 1), status ("ok"|"warn")}` per `contracts/estimate-spec-size.schema.json` (FR-025).
- [ ] T123 [US7] Validate against the existing golden fixtures at `tests/speckit-pro/unit/fixtures/estimate-spec-size/` (`--files 20` → `{800, 2, "warn"}`; `--files 11` → `{440, 2, "warn"}`; bad input → `{0, 1, "ok"}`); port/refresh the estimator's active Layer-4 test `test-estimate-spec-size.sh` → `.py` following the Per-Port Protocol.
- [ ] T124 [US7] **Manifest-version staleness fix (a)**: add `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` to `release-please-config.json` `extra-files` with jsonpath `$.plugin_version`, aligning the `.release-please-manifest.json` key so releases bump it automatically (research §D8).
- [ ] T125 [US7] **Manifest-version staleness fix (b)**: replace the hardcoded `self.assertEqual(manifest["plugin_version"], "2.17.0")` in `tests/speckit-pro/unit/test-speckit-pro-runner.py` with a version-agnostic check — assert the value matches the semver pattern AND equals `speckit-pro/.claude-plugin/plugin.json` `$.version` (research §D8).
- [ ] T126 [US7] **Shipped-runner regeneration ritual (PR 13)**: manifest sha256 recompute → `build-plugin-payloads.py` → checksum-based fixture sync → per-row proof-hash recompute → evidence regeneration in gate order, **release-readiness LAST**, `<home>` sanitized. If PR 2 or PR 10 has merged first, rebase onto it and re-run the full ritual (no hand-merged proof rows — plan §Constraints).
- [ ] T127 [US7] Confirm the estimator port + version fix leave the default-suite gate + drift-guard test green.
- [ ] T128 [US7] Record the CLAUDE.md note confirming whether the release-please-config change requires a CLAUDE.md release-section update.
- [ ] T129 [US7] Add the PR-body branch-protection callout: PR 13 adds no required status check (shipped-runner fix only) — state this explicitly to keep the stack's branch-protection ledger complete.
- [ ] T130 [US7] Verify US7 end-to-end (quickstart US7): invoke the runner with an `estimate-spec-size` request envelope carrying the golden `typical-under` size signals (`{"helper_id":"estimate-spec-size","inputs":{"user_stories":2,"files":3,"frs":4}}` — the inputs recorded in `tests/speckit-pro/unit/fixtures/estimate-spec-size/typical-under.args`) via `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner`, and confirm the returned `{estimated_loc, suggested_slices, status}` equals the golden `tests/speckit-pro/unit/fixtures/estimate-spec-size/typical-under.json` (`{estimated_loc:230, suggested_slices:1, status:"ok"}`), restoring pre-XPLAT-009 scoping behavior (SC-007). Note: the `estimate-spec-size/` fixtures are golden `(.args → .json)` input/output pairs — there is no `requests/` envelope subdir; the request envelope is constructed from the `.args` signals (matching T123's golden-fixture validation).

**Checkpoint**: Estimator restored for grill-me/speckit-prd; manifest version auto-bumps; stale hardcode removed.

---

## Phase 17: Polish & Cross-Cutting Concerns (no story label)

- [ ] T131 Finalize the cumulative parity evidence: complete `docs/ai/specs/.process/XPLAT-010-count-ledger.md` (all port delta lines present) and produce `docs/ai/specs/.process/XPLAT-010-suite-parity-result.json` — per-script `{script, mode, bash_count, python_count, names_equal, intentional_change}` rows + a suite-level roll-up asserting `bash_count == python_count` and `names_equal == true` for every ported script, zero drops/renames (FR-013/SC-003). (May ride PR 10.)
- [ ] T132 [P] Run the full quickstart.md validation for all 7 user stories end-to-end from the repo root; confirm each Expected result.
- [ ] T133 [P] Confirm the final no-Bash end state (SC-001/SC-002): on a Bash-absent, `jq`-absent Python-3.11+ environment, `run-all.py --all` runs to completion with the parity headline; `git ls-files '*.sh' | grep -v '^.github/workflows/' | grep -v '^.specify/'` returns empty.
- [ ] T134 Generate/refresh each PR's review packet: what changed, why, non-goals, review order, scope budget, per-FR/SC traceability → changed files + verification evidence, verification evidence, known gaps, rollback/flag notes; every port PR carries its committed baseline path + 6-item dual-run diff; every feat/fix PR carries a `release-note` block (authored from PR 1 onward once PR 12's template lands).
- [ ] T135 [P] Run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json` and `pnpm --dir docs-site validate` on the fully-merged stack; confirm both green.
- [ ] T136 Confirm every "Done When" workflow bullet maps to at least one FR and one PR slice, and that the two known-gap deferrals (Layer-8 `semantic-equivalent` LLM judge; Windows ARM64 runner availability) are recorded as out-of-scope, not silently dropped.

---

## Boundary Guards / Non-Goals (design-concept Non-goals — deliberately NOT tasked)

Per the workflow prompt, tasks that would cross these boundaries were **flagged and not written**:

- **No `.specify/**` ports.** The 10 vendored upstream `.sh` are allowlisted and guarded (T088/T091), never ported or forked. The 4 vendored `.ps1` are outside the bash-scoped detection vocabulary and need no entry.
- **No AI/LLM release notes.** The composer (T109–T111) is deterministic stdlib only — no LLM call, no new secret (FR-024).
- **No Layer-8 `semantic-equivalent` LLM judge.** PR 8 (T074) keeps `byte-identical`/`exact`/`tolerance-1` only; `semantic-equivalent` stays skipped-with-warning (known gap, out of scope).
- **No UAT-matrix / native operator UAT work.** Container/Windows preflight (T100–T108) is preflight evidence only; XPLAT-008 native operator UAT remains the release-claim gate and is not tasked here.
- **No new required status checks beyond the two ratified ones.** Only PR 11 (2 Linux checks) and PR 12 (`validate-release-note`) add required checks; PR 5 and PR 10 are required-check-neutral (T051/T099).
- **No `constitution.md` amendment.** Principles I/II/IV and the Quality Gates table's literal bash commands (`run-all.sh`, `validate-scripts.sh`, `tests/lib/assertions.sh`) go stale progressively as this stack lands (PR 2, PR 3a, PR 10) — a **CRITICAL** constitution conflict per `/speckit-analyze`'s Constitution-Authority rule, resolved via that rule's separate-explicit-constitution-update path (see plan.md §Constitution Check). No task here edits `.specify/memory/constitution.md`; the amendment is a distinct governance-document follow-up tracked in the cross-platform roadmap's XPLAT-010 status narrative, landing as its own small PR any time after PR 10 merges.

No task in this file crosses these boundaries.

---

## Dependencies & Execution Order

### PR-slice ordering (the 15-PR stack — CI-enforced where a violation breaks `main`)

- **PR 1** (T005–T007): anytime — no dependency.
- **PR 2** (T008–T017): **before PRs 3–10.** Self-enforcing — a port PR's atomic manifest edit (FR-012) targets `suite-manifest.json`, which does not exist until PR 2 creates it, so any 3–10 PR merged first fails CI.
- **PRs 3a, 3b, 4, 5, 6, 7a, 8, 9** (T018–T087): after PR 2; mutually parallel across layers. **PR 7b (T067–T072) after PR 7a (T062–T066)** (runners build on the shared transcript lib). Soft coupling: PR 5's `validate-pr-checks-sentinel` update (T049) targets the PR-3b-ported validator — land 3b before 5 or re-port in 5.
- **PR 10** (T088–T099): **after PRs 3–9.** Self-enforcing — the guard's live `git ls-files -z` enumeration (FR-005) finds any residual non-allowlisted `.sh`, so PR 10 cannot go green until PRs 3–9 have cleaned every surface (T080/T087 are the per-surface preconditions).
- **PR 11** (T100–T108): **last among confinement PRs** (after PR 10) so preflight exercises the fully-confined tree (FR-027). Review-ordering preference — a violation yields weaker evidence, not a red `main`.
- **PR 12** (T109–T120): independent — no hard dep on the confinement stack.
- **PR 13** (T121–T130): independent, **land early** so scoping tooling works for future scaffolds. Review-ordering preference.

### Shipped-runner concurrency rule (PRs 2, 7b, 8, 9, 10, 13)

All six rewrite `speckit-pro-runner.manifest.json` sha256 proof rows + `dist/**`. When more than one is in flight, the **later-merging one rebases onto the merged one and re-runs the full payload/proof regeneration ritual** (T016/T071/T078/T085/T098/T126); conflicting proof rows and payload bytes MUST NOT be hand-merged (plan §Constraints).

### Within each port slice

- Baseline capture → port + `subTest` name reconciliation → dual-run diff (PR body) → manifest flip (batched, same PR) → `.sh` delete → suite-green verification. Never a broken intermediate state (FR-012).

### Parallel Opportunities

- **Primary fan-out**: the 20 mechanical Layer-1 ports (T018–T027, T029–T038) are all `[P]` — distinct files, no interdependency; the per-phase manifest-registration task (T028/T039) serializes only the shared `suite-manifest.json` + ledger edits.
- Across slices: PRs 3a/3b/4/5/6/7a/8/9 can be developed in parallel by different contributors once PR 2 lands.
- `[P]` within other phases: shared parity tooling (T009/T010), guard tests (T094–T096), composer components (T109–T112, T115), and most polish checks (T132/T133/T135).

---

## Implementation Strategy

### MVP (US1 — the foundation everything rests on)

1. Phase 1 Setup → 2. PR 1 (orphan deletion, anytime) → 3. **PR 2 (US1 orchestrator + manifest + parity tooling)** → STOP and VALIDATE: `run-all.py` reaches bash-runner UX parity and the shipped gate reads the manifest. This is the standalone-valuable MVP: the suite runs from Python.

### Incremental delivery

1. Setup + PR 1 + PR 2 → foundation ready (manifest is source of truth).
2. PRs 3a–9 → each layer ports with a proven 1:1 parity diff (US2 accrues per PR).
3. PR 10 → confinement guard on + last `.sh` gone (US3; SC-001/SC-004).
4. PR 11 → preflight CI (US4). PR 12 → release notes (US5/US6). PR 13 → estimator (US7).
5. Polish → cumulative parity result + quickstart + review packets.

### Parallel team strategy

After PR 2 merges: Contributor A takes PRs 3a/3b/4 (Layer-1), B takes PRs 5/6 (tool-scoping/scripts/hooks), C takes PRs 7a/7b/8/9 (Layers 7/8 + live evals). PR 12 and PR 13 run on independent tracks throughout. PR 10 converges after 3–9; PR 11 follows PR 10.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task.
- `[USn]` maps each task to its user story for 1:1 traceability; Setup/PR-1-cleanup/Polish carry no label.
- Every port PR proves 1:1 name-and-count parity against a committed baseline (SC-003); a silent rename/drop yields a non-empty diff and flags the PR as a regression.
- Privacy: no absolute `/Users` or `/home` paths in any authored artifact — repo-relative only.
- Shipped-runner byte changes are confined to PRs 2/7b/8/9/10/13, each running the regeneration ritual with release-readiness LAST and `<home>` sanitization.
- Verify each slice with the default-suite gate + `pnpm --dir docs-site validate` before opening its PR; workflow-editing PRs (5/11/12) update their self-referential validators in the same PR.

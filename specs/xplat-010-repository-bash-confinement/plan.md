# Implementation Plan: Repository Bash Confinement and CI Dispatch Guard

**Branch**: `xplat-010-repository-bash-confinement` | **Date**: 2026-07-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/xplat-010-repository-bash-confinement/spec.md`

## Summary

Confine repository-local Bash to GitHub CI/CD workflow dispatch glue only. XPLAT-009
removed Bash from the shipped plugin and its payloads; this spec eradicates it from
the repository around the plugin. Concretely: port every active repo-local surface
(~101 harness `.sh`, 2 `scripts/**` helpers, 2 `.claude/hooks/**` handlers, the
Layers 2/3/6 live-AI eval runners) to Python 3.11+ standard library; make
`tests/speckit-pro/suite-manifest.json` the single per-layer source of truth that both
a new `run-all.py` developer orchestrator and the shipped suite gate read (retiring the
gate's hardcoded roster and its vacuous native `check_layer5/7/8`); add a bash-scoped
repository-confinement guard operation to `active_path_guard.py` (live `git ls-files -z`
enumeration, fail-closed 10-file vendored allowlist) composed into both the
release-readiness gate and the default deterministic suite; add container/runner
preflight CI (Linux gating, Windows advisory); add a deterministic Python release-notes
composer plus a `validate-release-note` required check that makes GitHub Releases
public-readable; and restore the deleted `estimate-spec-size` runner operation. Delivered
as a dependency-ordered 15-PR stack (the operator-ratified typed-split transition
exception), each PR independently CI-green with a runtime count-parity proof.

## Technical Context

**Language/Version**: Python 3.11+ standard library only (no new runtime dependency).
GitHub Actions YAML for CI. JSON Schema 2020-12 for contracts. Markdown for ledgers/process.

**Primary Dependencies**: The existing `speckit-pro/speckit_pro_runner/` package
(envelope, `gates/{suite,active_path_guard,release,registry}.py`,
`helpers/{registry,read_only}.py`, typed paths, subprocess fixtures); `gh` CLI v2+ at
PR-emission boundaries; GitHub REST via stdlib `urllib` in the composer (`GITHUB_TOKEN`
from the workflow env); no third-party packages.

**Storage**: Repository files only — suite manifest, guard allowlist, count-parity
baselines, disposition/count ledgers, suite-parity result, release-note metadata,
preflight evidence artifacts, JSON contracts. No database, no browser storage.

**Testing**: `unittest` with the house `__main__` convention printing
`<label>: {passed}/{total} passed`; a **net-new** shared `unittest.TestResult` subclass
(overriding `addSubTest`) under `tests/speckit-pro/lib/` provides per-assertion-execution
`{passed}/{total}` counting (no existing module does this — all five pre-existing Python
modules print bare `result.testsRun` and are exempt from retrofit). Runner gates run via
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < <request.json>`.
Docs validation via `pnpm --dir docs-site validate`.

**Target Platform**: Linux, macOS, and native Windows with Python 3.11+ present and
**no Bash and no `jq`**. CI adds Linux amd64/arm64 container preflight (gating) and
Windows x64/ARM64 direct-runner smoke (advisory).

**Project Type**: Single-project repository tooling with two seams — repo-side tooling
(`tests/speckit-pro/`, `scripts/`, `.claude/hooks/`, `.github/workflows/`; never shipped)
and the shipped runner package (`speckit-pro/speckit_pro_runner/`; byte changes trigger
the payload/proof regeneration ritual).

**Performance Goals**: N/A — deterministic gates complete in seconds; no throughput target.

**Constraints**: No absolute `/Users` or `/home` paths in any authored artifact
(repo-relative only). Shipped-runner byte changes are confined to PRs 2, 7b, 8, 9, 10, and 13, each
carrying the payload rebuild + proof-hash regeneration ritual with release-readiness
evidence regenerated LAST and home-directory sanitization (`<home>`). Because PRs 2, 7b, 8, 9, 10, and 13
all rewrite the `speckit-pro-runner.manifest.json` sha256 proof rows and the generated `dist/**`
payloads, when more than one of them is in flight simultaneously (for example PR 13 landing early
while PR 2 is still open) their proof rows conflict on merge: the later-merging PR MUST rebase onto
the merged one and re-run the full payload/proof regeneration ritual so its hashes are computed
against the post-merge tree — the conflicting proof rows and payload bytes MUST NOT be hand-merged,
since a hand-resolved hash corresponds to no real payload state and fails release-readiness
verification. Every port swaps
atomically in one PR (port + manifest flip + `.sh` delete), never a broken intermediate
state; the repo runs its own gates on itself, so the full suite stays green at every commit.
`pr-checks.yml`/`release.yml` job changes update the matching self-referential workflow
validator in the same PR and call out branch-protection follow-ups.

**Scale/Scope**: ~115 `.sh` files outside `.github/workflows/` today (101 under
`tests/speckit-pro/`, 10 vendored `.specify/**`, 2 `.claude/hooks/`, 2 `scripts/`); of the
101 harness scripts, 34 are deleted (32 orphans + 2 wrappers) and the remainder ported.
Delivered as a 15-PR stack.

**Reviewability Budget**: Primary surface harness/adapter (test-harness + runner-tooling
port); secondary scheduler/runtime (CI workflows), seed/config (manifest, allowlist,
release-note metadata), docs/process (ledgers). Projected reviewable LOC 400–800 (roadmap
budget; setup gate returned a ~400-LOC warn). Projected production files ~6–25; total files
~15–25. Budget result: **transition exception** — reviewability-gate warn accepted, typed
15-PR split (13 numbered slices, with slices 3 and 7 each split into a/b PRs) ratified in
`docs/ai/specs/.process/XPLAT-010-workflow.md` (refactor/infra class). This canonical 13-slice / 15-PR
figure supersedes the design concept's earlier "~12–13-PR" phrasing (Q9) and the workflow file's transitional
"14-PR" label; the enumerated slices are identical across all three — only the headline number is normalized.

## Declared File Operations

The following are the net-new production surfaces and modified shipped/CI surfaces that
carry genuine review weight. The ~60 mechanical Layer-1/4/5/7/8 `.sh`→`.py` ports are 1:1
replacements tracked per-PR against committed count-parity baselines (each `- NEW <module>.py`
pairs with a `- DELETED <module>.sh` in the same PR); representative anchors are listed
rather than all sixty.

- NEW tests/speckit-pro/suite-manifest.json
- NEW tests/speckit-pro/run-all.py
- NEW tests/speckit-pro/lib/test_result.py
- NEW tests/speckit-pro/lib/capture_baseline.py
- NEW scripts/compose-release-notes.py
- NEW .github/workflows/container-preflight.yml
- NEW .github/pull_request_template.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-010-confinement/allowlist.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-010-confinement/confinement-guard-cases.json
- NEW tests/speckit-pro/layer4-scripts/test-repo-bash-confinement.py
- NEW tests/speckit-pro/layer4-scripts/test-compose-release-notes.py
- NEW .claude/hooks/guard-version-triplet.py
- NEW .claude/hooks/validate-structural.py
- NEW docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md
- NEW docs/ai/specs/.process/XPLAT-010-count-ledger.md
- NEW docs/ai/specs/.process/XPLAT-010-suite-parity-result.json
- MODIFIED speckit-pro/speckit_pro_runner/gates/suite.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/active_path_guard.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/release.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED tests/speckit-pro/run-layer-scripts.py
- MODIFIED tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py
- MODIFIED .github/workflows/pr-checks.yml
- MODIFIED .github/workflows/release.yml
- MODIFIED release-please-config.json
- MODIFIED .release-please-manifest.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (unchanged — PASS).*

Constitution v1.1.0. Each principle evaluated below.

- **I. Plugin Structure Compliance — PASS.** No plugin directory-layout change. Repo-side
  ports stay under `tests/speckit-pro/`, `scripts/`, `.claude/hooks/`; shipped changes stay
  inside `speckit-pro/speckit_pro_runner/`. The `validate-plugin-payload` guard (tests/,
  specs/, .process/ must not appear under the plugin dir) continues to pass. One nuance: the
  constitution's Principle-I example bullet names `tests/run-all.sh` as the orchestrator —
  this repo's suite already lives at repo-root `tests/speckit-pro/` (not under the plugin),
  and this spec replaces `run-all.sh` with `run-all.py` + `suite-manifest.json`; that is an
  evolution of the orchestrator, not a structure violation.

- **II. Script Safety — PASS (direction-aligned).** The principle governs authored Bash
  (`#!/usr/bin/env bash` + `set -euo pipefail`, quoted vars, `bash -n`). This spec authors
  **no new repo-side Bash** — it removes Bash. The only retained Bash is `.github/workflows/`
  dispatch glue (already governed) and the 10 vendored `.specify/**` upstream helpers
  (documented-and-guarded, never authored or forked here). Net effect strengthens the
  principle's intent.

- **III. Semantic Versioning — PASS.** No manual version edits. PR 13 adds
  `speckit-pro-runner.manifest.json` to release-please `extra-files` (jsonpath
  `$.plugin_version`) so releases bump it automatically, and replaces the hardcoded
  `"2.17.0"` test assertion with a version-agnostic check (semver pattern + equality with
  `plugin.json`) — removing a stale-version anti-pattern rather than introducing one.

- **IV. Test Coverage Before Merge — PASS.** Every ported module lands with its unit test in
  the same PR; each port PR additionally carries a runtime count-parity baseline + dual-run
  diff proving 1:1 name-and-count preservation. New Layer-4 tests cover the confinement guard,
  the composer, and the estimator. The full deterministic suite stays green at every commit
  (atomic same-PR swaps). Test files keep the house naming/convention; the shared
  `TestResult` subclass replaces `tests/lib/assertions.sh` for ported modules.

- **V. Conventional Commits — PASS.** The 15-PR stack uses `feat`/`fix`/`chore`/`docs`/
  `refactor`/`test` scoped to `speckit-pro` or unscoped for repo-wide CI changes; PR titles
  are plain-English for the public with the conventional-commits prefix retained.

- **VI. KISS, Simplicity & YAGNI — PASS.** Ports preserve contracts 1:1 with no new
  abstractions except the shared `TestResult` subclass (20+ consumers — well past the
  three-use bar). The confinement guard **reuses** existing XPLAT-009 primitives
  (`python_shell_execution_findings`, `command_argv_contains_forbidden`,
  `shell_c_payload_has_forbidden_command`) and deliberately chooses the **simpler**
  bash-scoped vocabulary (its own `.sh`/`.bash` suffix set and `bash`/`jq` command-name pair)
  over inheriting XPLAT-009's broader superset — which would force phantom `.ps1` allowlist
  entries. The composer is stdlib-only, deterministic, no LLM, no new secret. The master-plan
  entry exists (cross-platform roadmap + workflow file). No speculative features.

**Constitution amendment follow-up (required — recorded, not reinterpreted; severity CRITICAL):** Constitution
v1.1.0 predates the cross-platform Bash→Python migration and still encodes bash-specific literal gate
commands: Principle I names the `tests/` orchestrator `run-all.sh`; Principle II's quality gate cites
`validate-scripts.sh`; Principle IV mandates the shared assertions library `tests/lib/assertions.sh` and
`bash tests/run-all.sh` as the completion gate; the Quality Gates table lists `bash tests/run-all.sh` and
`validate-scripts.sh`. This spec's same-PR atomic swaps retire these on a staggered timeline: `run-all.sh`
at PR 2/T015, `validate-scripts.sh` at PR 3a/T035, `tests/lib/assertions.sh` at PR 10/T097 — literal-command
staleness begins at PR 2, not at final Bash deletion. Per `/speckit-analyze`'s Constitution-Authority rule
("Constitution conflicts are automatically CRITICAL... not dilution, reinterpretation"), this conflict is
**CRITICAL** — the migration's intent-preservation and roadmap sanction bear on *which resolution path*
applies (the rule's own second sanctioned path: "a separate, explicit constitution update... outside
`/speckit-analyze`"), not on the severity label. Verified no automated gate or CI mechanism parses
`constitution.md`'s literal commands (G0 discovers `PROJECT_COMMANDS` dynamically per `prerequisites.md`
Step 0.11; G3 greps plan.md for `FAIL` text only; `pr-checks.yml` dispatches via independently-maintained
JSON fixtures) — deferral carries no automated-breakage risk, only a recurring documentation-fidelity cost
until amended. The amendment (MINOR-or-greater per the constitution's own Governance §Versioning policy) is
out of scope for this spec's implementation per the constitution's own 4-step Amendment procedure
(rationale + **cross-spec backward-compatibility assessment** + version bump + template propagation) —
disproportionate to bundle into any single reviewability-budgeted PR of this stack. Sanctioned by the
cross-platform roadmap master plan that Principle VI defers to; tracked as a small follow-up PR in the
roadmap's XPLAT-010 status narrative (this repo's established pattern — cf. "Windows interpreter follow-up
in PR #299"), landing any time after PR 10 merges (once all three named artifacts reach their terminal
Python state).

**Atomicity route (advisory, superseded):** The atomicity classifier read the feature-as-one-unit as
`single-atomic-PR` / `releasable: false` — a destructive-migration signal driven by the mass `.sh`
deletion. That route is advisory only and is superseded by the operator-ratified typed 15-PR slice stack
recorded in the workflow file (§Route); delivery proceeds slice-by-slice, each PR independently CI-green.
FR-012's same-PR atomic swap (port + manifest flip + `.sh` delete in one PR, never a broken intermediate
state) is the mitigating control that keeps every slice releasable, so the destructive-migration /
releasability warning is carried here into implementation context rather than driving delivery.

**Reviewability budget gate:** setup returned **warn** (≈400 reviewable LOC, 6 production
files, 2 primary surfaces — above the 400/6/15/1 warn thresholds, below the 800/8/25 block
thresholds). Resolution: **transition exception** (refactor + infra + upgrade classes),
ratified in `docs/ai/specs/.process/XPLAT-010-workflow.md` §Scope Budget and Split Decision
and design-concept Q9 — not an ad-hoc override. Split decision: one spec, dependency-ordered
15-PR stack, each PR independently CI-green and within the 400–800 reviewable-LOC budget
(see Project Structure and research.md §PR-stack ordering). No deferred follow-up specs
beyond the two pre-existing known gaps recorded in the design concept (Layer-8
`semantic-equivalent` LLM judge; Windows ARM64 runner availability) — both out of scope here.

**PR review packet source:** each PR body carries what changed, why, non-goals, review order,
scope budget, traceability (each FR/SC → changed files + verification evidence), verification
evidence, known gaps, and rollback/flag notes. Port PRs additionally carry the committed
count-parity baseline path and the 6-item dual-run diff block
(contracts/count-parity-baseline.contract.md §4); feat/fix PRs carry the Release note block
once PR 12's template lands (authored from PR 1 onward to seed the composer's first run).

**Result: no requirement-level violations — Complexity Tracking table not required. Three principles
(I/II/IV) carry bash-specific literal gate commands superseded by this roadmap-sanctioned migration and
are flagged above for a separate constitution amendment (recorded, not reinterpreted).**

## Project Structure

### Documentation (this feature)

```text
specs/xplat-010-repository-bash-confinement/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 — decisions flagged for Plan
├── data-model.md        # Phase 1 — entity schemas
├── quickstart.md        # Phase 1 — per-user-story validation scenarios
├── contracts/           # Phase 1 — JSON Schema + format contracts
│   ├── suite-manifest.schema.json
│   ├── confinement-allowlist.schema.json
│   ├── repo-bash-confinement-result.schema.json
│   ├── estimate-spec-size.schema.json
│   ├── release-note-block.contract.md
│   └── count-parity-baseline.contract.md
├── spec.md              # Finalized (27 FRs / 7 US / 8 SCs; 12 Clarifications)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
racecraft-plugins-public/
├── speckit-pro/speckit_pro_runner/      # SHIPPED runner (byte changes → regen ritual; PRs 2,7b,10,13)
│   ├── gates/
│   │   ├── suite.py                      # PR 2: manifest-derived roster (replaces hardcoded
│   │   │                                 #   DEFAULT_SUITE/EXTENDED_SUITE/ALLOWED_LAYERS, fail-closed);
│   │   │                                 #   PRs 5/7/8: retire native check_layer5/7/8 at port boundaries
│   │   ├── active_path_guard.py          # PR 10: new 'repo-bash-confinement' op (git ls-files -z,
│   │   │                                 #   bash-scoped suffix/command sets, fail-closed allowlist loader)
│   │   ├── release.py                    # PR 10: repo_bash_confinement check in release-readiness assembly
│   │   └── registry.py                   # PR 10: register the new guard op
│   ├── helpers/
│   │   ├── registry.py                   # PR 13: register estimate-spec-size HelperEntry
│   │   └── read_only.py                  # PR 13: implement estimate-spec-size
│   └── speckit-pro-runner.manifest.json  # PRs 2/7b/8/9/10/13: sha256 rows; PR 13: plugin_version fix
├── dist/{claude,codex}/speckit-pro/      # Generated payloads (regen ritual on runner changes)
├── tests/speckit-pro/                    # PRIMARY port surface (never shipped)
│   ├── suite-manifest.json               # NEW (PR 2): single source of truth per layer
│   ├── run-all.py                        # NEW (PR 2): developer orchestrator (bash UX preserved)
│   ├── run-layer-scripts.py              # MODIFIED (PR 2): read manifest, not run-all.sh text
│   ├── lib/
│   │   ├── test_result.py                # NEW (PR 2): shared addSubTest TestResult subclass
│   │   └── capture_baseline.py           # NEW (PR 2): VERBOSE PASS/FAIL → baseline capture tool
│   ├── parity/xplat-010/                 # NEW (PR 2+): committed <script>-baseline.txt files
│   ├── layer1-structural/                # PRs 3a/3b (20 mechanical) + 4 (MOC + codex/payload): 24 .sh→.py
│   ├── layer4-scripts/                   # 12 active .sh ported across PRs; +confinement/composer/estimator tests
│   ├── layer5-tool-scoping/              # PR 5: validate-tool-scoping.sh → .py
│   ├── layer7-integration/               # PRs 7a/7b: transcript lib + replay runners → .py
│   ├── layer8-parity/                    # PR 8: run-parity-fixtures.sh + lib + per-case env-*.sh → Python/data
│   └── layer{2,3,6}-*/                    # PR 9: live-AI eval runners → .py
├── scripts/
│   ├── compose-release-notes.py          # NEW (PR 12): stdlib release-notes composer
│   ├── refresh-local-plugin.sh           # PR 6 → .py
│   └── sync-marketplace-versions.sh      # PR 6 → .py (jq holdout)
├── .claude/hooks/                        # PR 6: guard-version-triplet.sh + validate-structural.sh → .py
├── .specify/                             # Vendored upstream (10 .sh allowlisted, never ported)
├── .github/
│   ├── workflows/                        # Dispatch glue only
│   │   ├── pr-checks.yml                  # PR 5: swap line-289 bash dispatch → python runner
│   │   ├── release.yml                    # PR 12: new compose-release-notes job (contents:write only)
│   │   └── container-preflight.yml        # NEW (PR 11)
│   └── pull_request_template.md           # NEW (PR 12): seeds the release-note block
└── docs/ai/specs/.process/                # Ledgers + evidence (deleted-tests, count, suite-parity)
```

**Structure Decision**: Single project, two seams. Repo-side Python (`tests/speckit-pro/`,
`scripts/`, `.claude/hooks/`, `.github/workflows/`) is never shipped; the shipped runner
(`speckit-pro/speckit_pro_runner/`) changes only in PRs 2/7b/8/9/10/13 and each such change runs the
payload/proof regeneration ritual. The suite manifest decouples test-list churn from
shipped-runner rebuilds so ordinary layer edits are manifest-only.

## Complexity Tracking

No constitution violations — this section is intentionally empty.

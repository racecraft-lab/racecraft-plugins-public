# SpecKit Workflow: XPLAT-010 — Repository Bash Confinement and CI Dispatch Guard

**Template Version**: 1.0.0
**Created**: 2026-07-08
**Purpose**: Executable workflow guide for the XPLAT-010 autopilot run. Prompts below are consumed phase by phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log (11 questions), Goals,
Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/XPLAT-010-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Scope Budget and Split Decision (reviewability setup gate record)

The reviewability setup gate returned **warn, pass=true** for this spec:
reviewable LOC 400, production files 6, total files 15, primary surfaces 2
(`docs/process`, `harness/adapter`) against warn thresholds 400/6/15/1. The
roadmap budget projects 400–800 reviewable LOC and 15–25 total files.

**Split decision (accepted in design-concept Q9/Q10):** one spec delivered as a
~14-PR stack, each PR independently CI-green and sized to the 400–800
reviewable-LOC budget:

1. Orphaned-test deletion + disposition ledger (deletion-only)
2. Suite manifest + `run-all.py` orchestrator + manifest-reading suite gate
3. (a/b) 20 mechanical Layer-1 validators ported, split in two PRs
4. MOC lints + codex-skills/payload-conformance validators
5. Layer-5 tool scoping + toolchain check + `pr-checks.yml` dispatch swap
6. `scripts/**` + `.claude/hooks/**` ports
7. (a/b) Layer-7 replay harness (shared transcript lib first, then runners)
8. Layer-8 parity runner + fixture conversion
9. Live-AI eval runners (Layers 2/3/6)
10. Repo-bash-confinement guard + final bash deletion
11. Container/Windows preflight CI workflow
12. Release-notes composer + `validate-release-note` check + release workflow step

13. Spec-size estimator restored as a runner operation (`fix`; shipped-runner
    change with the payload/proof regeneration ritual; independent — land
    early so scoping tooling works for future scaffolds)

Ordering constraints: 1 anytime; 2 before 3–10; 10 after 3–9; 11 last among
confinement PRs; 12 and 13 independent (13 preferred early).

---

## Orchestration & Delegation Discipline

The main session running this workflow is an **orchestrator only** — this is a
hard constraint of the autopilot skill itself (SKILL.md §Architectural
Constraint), not a preference: it reads prompts from this file, dispatches
every phase to a subagent, validates gates, and synthesizes consensus. It never
authors spec/plan/tasks/implementation artifacts directly, and it must refuse
to run inside a subagent context.

**Agent right-sizing is enforced by the bundled agent definitions** (dispatch
as `speckit-pro:<name>`; verified from agent frontmatter in the 2.18.0 cache):

| Tier | Model | Agents |
|------|-------|--------|
| Heavy reasoning | opus | phase-executor, implement-executor, clarify-executor, checklist-executor, analyze-executor |
| Mechanical / support | sonnet | gate-validator, consensus-synthesizer, codebase-analyst, spec-context-analyst, domain-researcher, uat-runbook-author |

Reasoning effort is pinned `max` for the orchestrator and every bundled agent
by shipped skill policy ("quality is the only optimization axis" for SDD
phases). Changing that policy is a plugin feature change informed by the
Layer 6 efficiency benchmarks — out of scope for this run.

**Supervision-layer rule for work outside the bundled agents** (baseline
capture, payload/proof regeneration, fixture syncs, evidence regeneration,
verification canaries): delegate to the cheapest capable agent and model;
never absorb mechanical work into the orchestrator's own turn, and never run
a heavy phase orchestrator-direct.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 25 FRs / 7 US / 20 scenarios / 8 SCs; 0 markers; G1 PASS (runner-verified) |
| Clarify | `/speckit-clarify` | 🔄 In Progress | 3 sessions seeded from design-concept open questions; runs despite 0 markers (operator-ratified seeded sessions) |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | requirements, integration, reliability, security |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Plugin dir layout untouched by repo-side ports | Layer-1 structural suite passes |
| KISS, Simplicity & YAGNI | Ports preserve contracts 1:1; no new abstractions without a second use | Count-parity diff per PR |
| Test-First | Every ported validator lands with its unit test in the same PR | Per-PR test evidence |

**Constitution Check:** ✅ (validated during scaffold; re-verify at G1)

### Autopilot Pre-flight Record (2026-07-08)

| Item | Value |
|------|-------|
| check-prerequisites | all_pass=true (specify CLI 0.11.8; project init, constitution, commands, workflow file OK) |
| Branch state | worktree=true; branch `xplat-010-repository-bash-confinement`; non-numeric namespace → `.specify/feature.json` pins `specs/xplat-010-repository-bash-confinement` (vendored scripts support the feature.json bypass) |
| PROJECT_COMMANDS | detect-commands: stack unknown / all N/A. Effective commands (CLAUDE.md): FULL_VERIFY + UNIT_TEST = `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json`; TOOLCHAIN = same runner with `run-toolchain-preflight.json`; DOCS = `pnpm --dir docs-site validate`; BUILD/TYPECHECK/LINT = N/A |
| PRESET_CONVENTIONS | speckit-pro-reviewability v1.0.0 active; spec/plan/tasks templates resolve from `.specify/presets/speckit-pro-reviewability/templates/` |
| CONFIDENCE_GATE_MODE | `advisory` (resolved at Step 0.6b; G6.5 reads this value, resolver not re-run) |
| AGENT_TEAMS_AVAILABLE | `true` (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1; Claude Code 2.1.205 ≥ 2.1.32) |
| PROJECT_IMPLEMENTATION_AGENT | none detected (`.claude/agents/` has release-auditor + skill-reviewer only, neither an implementation agent) → fallback `speckit-pro:phase-executor`; task-level routing uses `speckit-pro:implement-executor` for TDD tasks |
| Settings | no `.claude/speckit-pro.local.md` → defaults (consensus-mode=moderate, gate-failure=stop, auto-commit=per-phase) |
| Agent package | all 11 bundled `speckit-pro:*` agents registered in the session runtime (incl. uat-runbook-author) |
| Extensions | agent-context, archive, checkpoint, git, retrospective, speckit-utils, verify, verify-tasks all installed |
| Tier-2 relocation | suppressed — current spec carries `SPEC-MOC.md` `structureVersion: 1`; no eligible thawed legacy candidate |
| before_specify git.feature hook | goal state already satisfied by scaffold (branch + worktree exist); recorded as satisfied, not re-executed |

**Operator directive (2026-07-08, mid-run):** any dogfooding bug in the
speckit-pro plugin encountered while executing this autopilot run MUST be fixed
at root cause during the run (not papered over, not deferred). Discovered bugs
are logged in this section as they surface.

**Dogfood defect log:**
- (pre-run, already in scope) `estimate-spec-size` runner operation missing — PR 13 / US7.
- (Clarify phase, recurring ×3 — also `domain-researcher`, Session 3 Q2) Read-only consensus analysts (`codebase-analyst`, Session 1 Q4 and Session 2 Q1) end their turn on an intermediate "let me check X" thought instead of the structured deliverable — the agent loop terminates on a no-tool-call text message and the half-finished thought becomes the returned result. Orchestrator remediation: SendMessage resume nudge (works). Root cause: `maxTurns: 25` in the analyst frontmatter — census-scale questions exceed the turn budget and the harness returns the last text message. FIXED via PR #301 (`ab89deb0`, own branch off main, awaiting human merge): maxTurns 25→50 + a Terminal Deliverable rule in all three analyst definitions; full payload/proof regen ritual executed (claude tree hash rotated, codex unchanged; `-source-mismatch` fixture trap documented — it pins the claude hash on both rows by design); battery green (gates 54/54, default suite 6/6, release-readiness ok, privacy clean). Codex TOML untouched (validators list maxTurns as CC-only; codex has no turn-budget concept).
- (observed by the fix agent, pre-existing — CONFIRMED latent defect) `speckit-pro-runner.manifest.json` carries `"plugin_version": "2.17.0"` while the released plugin is 2.18.0. release-please never bumps the manifest, and `test-speckit-pro-runner.py:307` hardcodes the 2.17.0 value (the same version-pinning anti-pattern as the dependabot SHA-pin lesson), so shipped payloads self-describe with a stale version indefinitely. Functionally benign today (the release gate validates the version pattern, not the value). Remediation scheduled IN-RUN inside PR 13 (already a shipped-runner fix PR carrying the regen ritual): add the manifest to release-please's `extra-files` (jsonpath `$.plugin_version`) so releases bump it, and replace the hardcoded test assertion with a version-agnostic check (semver pattern + equality against `plugin.json`). Plan phase must carry this as an explicit PR 13 task.
- (Clarify phase, discovered by S1-Q3 consensus) The shipped suite gate's native `check_layer5` is vacuously true (asserts on a `tools:` frontmatter field none of the checked agents carry), `check_layer7` validates an orphaned fixture directory, `check_layer8` checks 3 of 6 required files. Remediation is already encoded in this spec: FR-008 retires each native check at its layer's port-PR boundary (PRs 5/7/8) with the manifest-derived roster + drift-guard replacing them.

**Archive Sweep record:** archive extension v1.1.0 installed; eligible =
`specs/xplat-009-plugin-source-and-payload-bash-eradication` (PR #297 merged
`7bc6be1a`, shipped in 2.18.0); current target excluded; apply mode with
`safeToApplyCleanup=true`; commit `d3c95f73` (27 files, +546/−1704): spec dir
removed with recovery commands recorded, 4 contract schemas relocated to
`tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/contracts/`,
memory/AGENTS/roadmap/MOC updated, archive report at
`.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md`.
Post-commit verification by the sweep: gates test 54/54, runner test 10/10,
default suite gate PASS (toolchain 5/5, L1 24/24, L4 17/17, L5 8/8, L7 9/9,
L8 14/14).

**Constitution validation (G0):** default-suite gate PASS on the quiesced tree
(evidence above). An earlier overlapped run reported layer-4 16/17
(`test_xplat008_release_readiness_pending_native_uat_still_blocks`,
blocking_count 2≠1) — root-caused to orchestration, not the plugin: the
release-readiness live scan ran while the archive sweep was mutating
`specs/**`. Not reproducible on the quiesced tree. **Run lesson:** never
overlap live-scan gate runs with worktree-mutating subagents.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | XPLAT-010 |
| **Name** | Repository Bash Confinement and CI Dispatch Guard |
| **Branch** | `xplat-010-repository-bash-confinement` |
| **Dependencies** | XPLAT-009 (merged, PR #297, released in speckit-pro 2.18.0) |
| **Enables** | Public Bash-free release readiness (with XPLAT-008 native UAT) |
| **Priority** | P1 |

### Success Criteria Summary

From the roadmap's Done When plus the design-concept scope addition:

- [ ] A repo-wide scan excluding `.github/workflows/` finds zero `.sh` files and zero Bash-shebang scripts (including extensionless executables); vendored `.specify/**` exceptions are documented, allowlisted, and excluded from release readiness
- [ ] GitHub workflow shell snippets contain only dispatch glue — no embedded validation, packaging, install, release, or runtime logic
- [ ] Active tests, evals, payload builders, release-readiness checks, install-verification paths, hooks, and helper tools run without Bash or `jq`
- [ ] Per-layer runtime check counts match committed VERBOSE=true baselines 1:1 (names and counts) — zero regressions across the port
- [ ] Linux container preflight evidence exists for `linux/amd64` and `linux/arm64` using the same runner/release-gate entrypoints CI uses; Linux jobs gate PRs on runner/gate paths
- [ ] Windows x64 and ARM64 direct-runner smoke evidence exists where runner labels are available, advisory (`continue-on-error`) with availability recorded; container evidence is never presented as native UAT
- [ ] CI fails on new Bash scripts, active Bash invocations, or `jq` dependencies outside the workflow dispatch boundary
- [ ] Every feat/fix PR carries a consumer-facing Release note block (required check with `release-note/skip` label escape), and the GitHub Release body is composed into plain-English Highlights with the conventional-commit list preserved as an appendix
- [ ] The `estimate-spec-size` runner operation exists and returns `{estimated_loc, suggested_slices, status}` for the size signals grill-me and speckit-prd send it — closing the dogfood defect where the skill references an operation whose bash predecessor was deleted by XPLAT-009 without a Python port
- [ ] The XPLAT-008 native UAT matrix remains the only release-satisfying evidence for native installed-plugin journeys

---

## Phase 1: Specify

**When to run:** At the start. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/xplat-010-repository-bash-confinement/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: Repository Bash Confinement and CI Dispatch Guard

### Problem Statement
XPLAT-009 removed every Bash surface from the shipped plugin and its generated
payloads, but the repository around the plugin still runs on Bash: the test
harness (~101 .sh files under tests/speckit-pro/), top-level helper scripts,
.claude/hooks, and one residual CI test-dispatch step. Until repo-local Bash is
confined to GitHub CI/CD workflow dispatch glue only, the project cannot claim
Bash-free cross-platform release readiness, and contributors on native Windows
cannot run the repo's own gates. Separately, the GitHub Release bodies
release-please produces are raw conventional-commit lists full of internal
vocabulary — the public cannot understand what each release changes (design
concept Q10; the speckit-pro v2.18.0 release body is the exemplar).

### Users
- Plugin maintainers running the repo-local test and release gates on any OS
- Contributors reviewing port PRs who need proof nothing regressed
- CI (GitHub Actions) executing validation, packaging, and release gates
- Plugin consumers and evaluators reading GitHub Releases to understand changes

### User Stories
- [US1] As a maintainer, I can run the full deterministic suite via a Python
  orchestrator (tests/speckit-pro/run-all.py) with the same flags, headline
  output, and exit codes the bash runner had, on any OS with Python 3.11+.
- [US2] As a reviewer, every port PR shows a runtime count-parity diff against
  a committed baseline proving check names and counts are preserved 1:1.
- [US3] As CI, a repo-bash-confinement guard fails any PR that introduces .sh
  files, Bash-shebang executables, or active bash/jq invocations outside
  .github/workflows/, with a fail-closed allowlist for the 10 vendored
  .specify/** upstream files (release_readiness_excluded: true).
- [US4] As a maintainer, Linux amd64/arm64 container preflight and Windows
  x64/ARM64 direct-runner smoke jobs run on runner/gate path changes (Linux
  gating, Windows advisory) and upload evidence artifacts.
- [US5] As a plugin consumer, each GitHub Release opens with plain-English
  Highlights composed from PR-authored release-note blocks, with the
  conventional-commit list preserved below as an appendix.
- [US6] As a PR author, a required validate-release-note check tells me when a
  feat/fix PR is missing its Release note block, and a release-note/skip label
  exempts changes with no consumer-visible effect.
- [US7] As a maintainer scoping a future spec, the estimate-spec-size runner
  operation returns {estimated_loc, suggested_slices, status} from the size
  signals the grill-me and speckit-prd skills send it, restoring the scoping
  estimator whose bash predecessor XPLAT-009 deleted without a Python port
  (operator directive: remediate in this spec, not a follow-up).

### Constraints
- Python 3.11+ standard library only for all ported tooling; no new runtime
  dependencies (constitution + XPLAT PRD).
- Ported test modules follow the house convention: unittest, custom __main__
  printing "<label>: {passed}/{total} passed", one test method per former
  set_test, counted subTest for loops.
- The shipped runner's suite gate keeps its XPLAT-007 envelope contract; it
  reads the new repo-side tests/speckit-pro/suite-manifest.json instead of
  regex-parsing run-all.sh (design concept Q2). Shipped-runner byte changes
  require the payload/proof regeneration ritual.
- Same-PR swap discipline: port + manifest flip + .sh delete land in one PR
  with a dual-run diff recorded (design concept Q3).
- The 34 orphaned bash tests are deleted with a disposition ledger, not ported
  (design concept Q1).
- .claude/hooks are ported to Python preserving the stdin-JSON/exit-0-or-2
  hook contract (design concept Q4).
- Live-AI eval runners (Layers 2/3/6) are ported preserving CLI arg contracts
  and codex staging semantics (design concept Q5).
- Container preflight triggers: path-filtered pull_request + workflow_dispatch;
  Linux jobs gate, Windows jobs are continue-on-error advisory (Q6/Q7).
- Release-notes composer is deterministic Python stdlib run inside the Release
  workflow; no LLM calls, no new secrets; CHANGELOG.md stays the machine
  ledger (Q10/Q11).

### Out of Scope
- Porting or forking the 10 vendored .specify/** upstream Spec Kit helpers
  (allowlisted + release-readiness-excluded instead, Q8)
- Plugin source / generated payload cleanup (completed by XPLAT-009)
- Native operator UAT rows (XPLAT-008 evidence remains the release claim gate)
- Treating Docker/QEMU/Windows containers as native installed-plugin proof
- AI-generated release notes (rejected in Q10)
- An LLM judge for Layer-8 semantic-equivalent tolerance (pre-existing gap;
  the port preserves skip-with-warning behavior)
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 25 (FR-001–FR-025, 7 domains: confinement guard, suite orchestration, port fidelity/count parity, orphan disposition, preflight CI, release notes, estimator) |
| User Stories | 7 (US1–US7 preserved 1:1; P1×2, P2×4, P3×1) |
| Acceptance Criteria | 20 Given/When/Then scenarios; 8 success criteria (SC-001–SC-008); 8 edge cases; 8 key entities |
| Markers | 0 `[NEEDS CLARIFICATION]`; privacy scan clean (0 absolute paths) |
| Gate G1 | PASS — runner validate-gate: `spec.md exists with 0 markers`; spec.md 24,605 bytes |
| Reviewability budget | transition exception (typed ~13/14-PR split, operator-ratified) |

### Files Generated

- [x] `specs/xplat-010-repository-bash-confinement/spec.md`
- [x] `specs/xplat-010-repository-bash-confinement/checklists/requirements.md` (spec quality checklist, 16/16 pass)

### SpecKit Traceability Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Maintainer runs run-all.py --layer 1` |
| `[FR-001]` | Functional requirement | `[FR-001] Guard fails on new .sh outside workflows` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Windows ARM64 label availability [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Port validate-frontmatter alongside other L1 validators` |
| `[Gap]` | Missing coverage | `[Gap] No task covers composer failure when a PR body lacks the block` |

---

## Phase 2: Clarify

**When to run:** After Specify. Sessions are seeded from the design concept's Open Questions plus the highest-risk contract seams.

### Clarify Prompts

#### Session 1: Suite manifest and count-parity contract

```text
/speckit-clarify Focus on the suite-manifest.json schema and count-parity
mechanics: manifest fields per layer (script path, label, expected-count
source), how run-all.py and the shipped suite gate share the manifest without
drift, where VERBOSE baselines live, and what exactly the dual-run diff in
each port PR must contain.
```

#### Session 2: Confinement guard semantics

```text
/speckit-clarify Focus on the repo-bash-confinement guard: enumeration source
(git ls-files), detection rules (.sh suffix, bash shebang, extensionless
executables, active bash/jq invocation text), the .specify/** allowlist entry
shape and its release_readiness_excluded flag, and how the guard composes into
release readiness and the CI sentinel.
```

#### Session 3: Release-notes pipeline contract

```text
/speckit-clarify Focus on the release-notes pipeline: the exact Release note
block format in PR bodies, how the composer discovers PRs since the last tag,
fallback behavior when a block is missing or a PR was label-skipped, when in
the Release workflow the composer rewrites the GitHub Release body, and the
validate-release-note check + release-note/skip label semantics.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Suite manifest / count parity | 5 (Q2/Q5 parent-accepted; Q1/Q3/Q4 consensus) | Manifest schema frozen (baseline-pointer as count of record); dual-run diff = 6 required items; count granularity = per assertion execution via shared TestResult subclass (5 pre-existing testsRun modules exempt); native check_layer5/7/8 retired at port-PR boundaries + manifest-derived roster + drift-guard test; baseline format frozen (per-outcome lines, verbatim runtime names, 5 normalization rules). FR-007/008/010/011, Key Entities, and Clarifications updated. |
| 2 | Confinement guard | 5 (Q3/Q4/Q5 parent-accepted; Q1/Q2 consensus) | Enumeration = `git ls-files -z` argv, fail-closed without git; allowlist contract pins all 10 vendored paths under a `vendored_specify_helper` scope; composition = `repo_bash_confinement` release-readiness check + default-suite live-scan case riding existing required checks (zero branch-protection churn); invocation-text detection scoped to executable surfaces (`.py` AST + structural `hooks.json`/`package.json` JSON-value scans, no prose scanning); vocabulary bash-scoped (`.sh`/`.bash` + bash/POSIX-sh shebang; `.ps1`/`.bat`/`.cmd`/`.zsh` out of scope — the 4 vendored `.ps1` need no allowlist entry). FR-001/002/003/004/005, SC-001, Edge Cases, Key Entities, Assumptions updated. |
| 3 | Release notes | 5 + 1 security item (Q1/Q3/Q4/Q5 parent-accepted; Q2 → Round 2; security → all-3, held for operator ratification) | Block grammar frozen (single ```release-note``` fence, Kubernetes precedent, PR template seeds it); fallback ladder (skip→omit, missing→de-prefixed title, zero-blocks→graceful degrade); composer = release.yml post-publication step, tag→ID resolution (no ID output exists), idempotent from body output; check semantics (7 event types incl. labeled/unlabeled, releasable types only, draft+release-PR exempt, NEW required check + label creation); discovery = Compare-API commit-subject walk (body-regex provably lossy: PRs #210/#192 invisible), fail-loud on under-enumeration surfaces. FR-021–024 + Key Entity + 5 Clarifications bullets. Security hardening draft (3/3) PENDING operator sign-off. |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | S1-Q1: count granularity + `{passed}/{total}` headline formula | [codebase, spec] | 1 | both-agree | Per-assertion-execution units via shared TestResult subclass (addSubTest); FR-010 tightened; 5 pre-existing testsRun modules exempt (XPLAT-007 FR-003 contract), prospective-only | codebase-analyst, spec-context-analyst |
| 2 | Clarify | S1-Q3: retire vs keep suite.py native check_layer5/7/8 | [codebase] | 1 | high-confidence | Retire at each port-PR boundary (natives vacuous/orphaned/subset); manifest-derived roster fail-closed + drift-guard test; FR-007/FR-008 refined | codebase-analyst |
| 3 | Clarify | S1-Q4: baseline file format + name reconciliation | [codebase] | 1 | high-confidence | Frozen per-outcome format with verbatim runtime-captured names + 5 normalization rules; zero un-named sites in full census → no positional fallback; FR-011 + Key Entities refined | codebase-analyst |
| 4 | Clarify | S2-Q1: invocation-text scan surfaces + self-reference avoidance | [codebase, domain] | 1 | both-agree | Executable-surface scoping: suffix+shebang repo-wide, `.py` AST + structural `hooks.json` command / `package.json` scripts JSON-value scans (reusing prohibited-command primitives); no prose scanning; FR-002 + Edge Cases refined | codebase-analyst, domain-researcher |
| 5 | Clarify | S2-Q2: bash-scoped vs inherited broad detection vocabulary | [spec] | 1 | high-confidence | Bash-scoped only (`.sh`/`.bash` + bash/POSIX-sh shebang incl. `#!/bin/sh`); 4 vendored `.ps1` never in detection set, allowlist stays exactly 10; FR-001/FR-003/SC-001 refined; FR-002 bash/jq-pair note flagged for Plan | spec-context-analyst |
| 6 | Clarify | S3-security: composer content-sanitization + token scope | [security] | 1 (mandatory all-3) | [HUMAN REVIEW] — 3/3 unanimous, held for operator ratification per the security-override gate | Draft merged (own-job contents:write only; HTML+image strip; structural-char neutralization; 2,000-char cap; CommonMark fence defense; harvest-all-types provenance bound; run-log as durable record) — PENDING operator sign-off, edits NOT applied | codebase-analyst, spec-context-analyst, domain-researcher |
| 7 | Clarify | S3-Q2: composer PR-discovery algorithm | [codebase, domain] | 1→2 | 2/3 | Compare-API commit-subject walk for discovery (body-regex provably lossy in-repo: PRs #210/#192 carry no `(#N)` in CHANGELOG); appendix stays verbatim body output; domain's fail-loud re-targeted at the compare/subject surface; FR-023 + Clarifications updated | codebase-analyst, domain-researcher (R1) + spec-context-analyst (R2 tie-breaker) |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/xplat-010-repository-bash-confinement/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Runner/gates: Python 3.11+ standard library only, extending
  speckit-pro/speckit_pro_runner/ (envelope, diagnostics, typed paths,
  subprocess fixtures, gates/active_path_guard.py)
- Repo-side tooling: Python 3.11+ stdlib scripts under tests/speckit-pro/,
  scripts/, .claude/hooks/ (never shipped in the plugin payload)
- CI: GitHub Actions YAML — pr-checks.yml (dispatch swap), release.yml
  (release-notes composer step), new container-preflight workflow
- Tests: unittest with the house __main__ convention
  ("<label>: {passed}/{total} passed"); counted subTest for loops
- PR/repo ops: gh CLI v2+ at emission boundaries; GitHub REST via urllib in
  the composer (stdlib only, GITHUB_TOKEN from the workflow env)

## Constraints
- Read docs/ai/specs/.process/XPLAT-010-design-concept.md before planning —
  it records the 11 accepted decisions (triage, suite architecture, count
  parity, hooks, live evals, CI triggers/gating, .specify allowlist, 14-PR
  split, release-notes mechanism and enforcement).
- The 14-PR stack and its ordering constraints are fixed (see the Scope
  Budget and Split Decision section of this workflow file). Plan tasks so
  each PR is independently CI-green.
- Shipped-runner changes (suite gate manifest read, confinement guard op) are
  confined to PRs 2, 10, and 13; each triggers the payload rebuild + proof-hash
  regeneration ritual and must regenerate release-readiness evidence LAST
  with home-directory sanitization.
- pr-checks.yml job renames require matching branch-protection updates —
  plan the pr-checks.yml:289 swap (PR 5) and the new required Linux preflight
  checks (PR 11) with explicit branch-protection follow-up steps, and update
  the self-referential workflow validators in the same PR that changes each
  workflow.
- The repo runs its own gates on itself: every port PR must keep the full
  suite green at every commit, so ports swap atomically (Q3), never in a
  broken intermediate state.

## Architecture Notes
- suite-manifest.json is the single source of truth for layer composition;
  run-all.py (developer UX) and the shipped suite gate (CI dispatch) both read
  it. Transitional .sh support exists only between PR 2 and PR 10.
- The confinement guard is a new operation in active_path_guard.py following
  the XPLAT-009 zero-bash guard patterns: git ls-files enumeration, fail-closed
  allowlist loader, composition into release.py.
- The release-notes composer is a repo-side scripts/compose-release-notes.py
  invoked by release.yml after release publication; it edits the GitHub
  Release body via the API and never touches CHANGELOG.md.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Manifest/allowlist/ledger/release-note block schemas |
| `contracts/` | ⏳ | suite-manifest, allowlist entry, release-note block, parity baseline |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together.

Recommended domains (from spec analysis; matches the XPLAT-009 precedent set):

### 1. requirements Checklist

Why: 8 success criteria spanning four subsystems (harness port, guard, CI preflight, release notes) — coverage drift between them is the top spec risk.

```text
/speckit-checklist requirements

Focus on Repository Bash Confinement and CI Dispatch Guard requirements:
- Every "Done When" bullet maps to at least one FR and one PR in the 14-PR stack
- Count-parity requirements are stated per layer, not just globally
- Release-notes requirements cover authoring, enforcement, composition, and skip paths
- Pay special attention to: the boundary between XPLAT-010 scope and XPLAT-008 UAT / XPLAT-009 completed work
```

### 2. integration Checklist

Why: the spec rewires CI (pr-checks.yml, release.yml, new preflight workflow) and the shipped-runner/repo-side seam (manifest), where partial integration breaks every PR.

```text
/speckit-checklist integration

Focus on Repository Bash Confinement and CI Dispatch Guard requirements:
- suite-manifest consumed identically by run-all.py and the shipped suite gate
- pr-checks.yml dispatch swap and branch-protection required-check renames
- Release workflow ordering: release-please publish, then composer body rewrite
- Pay special attention to: transitional .sh support lifetime (PR 2 through PR 10) and what happens if the stack merges out of order
```

### 3. reliability Checklist

Why: the guard and composer run unattended in CI; their failure modes (allowlist drift, missing PR blocks, runner label unavailability) must degrade predictably.

```text
/speckit-checklist reliability

Focus on Repository Bash Confinement and CI Dispatch Guard requirements:
- Guard behavior on ambiguous files (extensionless, shebang-less, binary)
- Composer fallback when a release-note block is missing, malformed, or label-skipped
- Windows runner-label unavailability recording without failing the workflow
- Pay special attention to: fail-closed vs fail-open choices in each new gate
```

### 4. security Checklist

Why: the allowlist is a policy boundary (vendored bash that must never satisfy release gates) and the composer writes to the public release surface with a workflow token.

```text
/speckit-checklist security

Focus on Repository Bash Confinement and CI Dispatch Guard requirements:
- Allowlist entries cannot be broadened silently (fail-closed loader, per-file pins)
- release_readiness_excluded entries provably cannot satisfy release gates
- Composer token scope (contents: write only) and injection-safety of PR-body text into the release body
- Pay special attention to: the guard remaining the backstop against future bash reintroduction
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| requirements | | | |
| integration | | | |
| reliability | | | |
| security | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/xplat-010-repository-bash-confinement/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Group tasks by PR-stack slice (the 14-PR split in this workflow file's
  Scope Budget section), honoring the ordering constraints:
  1 anytime; 2 before 3-10; 10 after 3-9; 11 last among confinement PRs;
  12 and 13 independent (13 early)
- Mark parallel-safe tasks explicitly with [P] — the 20 mechanical Layer-1
  validator ports (PRs 3a/3b) are the primary parallel fan-out
- Every port task pairs with: capture VERBOSE baseline, port, dual-run diff,
  manifest flip, .sh delete — in the same slice

## Constraints
- Repo-side Python lives under tests/speckit-pro/, scripts/, .claude/hooks/ —
  never under speckit-pro/ (the payload guard fails if tests reappear there)
- Shipped-runner tasks (PRs 2, 10, and 13) must include the payload rebuild +
  proof-hash regeneration ritual as explicit tasks, release-readiness last
- Bound task generation with the design concept Non-goals: no .specify/**
  ports, no AI release notes, no L8 semantic judge, no UAT-matrix work —
  flag any task that would cross those boundaries instead of writing it
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then — leave the cells blank during scoping. This route is
recorded only here in the workflow file — never in the spec map. It is read
downstream by the layer-planner and multi-PR emission work that builds on top of
it; recording it now wires no PR creation or branch splitting on its own.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| **Signals** | | The decisive detector findings behind the route and releasability reading. |
| **Warnings** | | Any release-safety warning attached to the change. |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/xplat-010-repository-bash-confinement
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — Python-stdlib-only, KISS/YAGNI, test-first
2. Coverage gaps — every FR and user story has tasks; every "Done When"
   bullet traces to a PR slice
3. Drift against docs/ai/specs/.process/XPLAT-010-design-concept.md — the
   design concept is the source of truth for the 11 scoping decisions; if
   spec.md, plan.md, or tasks.md contradicts it, the downstream artifact is
   wrong unless it carries an explicit revision note
4. Consistency between task file paths and the actual repo structure
   (tests/speckit-pro/, scripts/, .claude/hooks/, .github/workflows/)
5. Verify the 14-PR ordering constraints are encoded in task dependencies
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Run the toolchain preflight and default-suite gates from the repo root and
   confirm they pass before making changes:
   PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight.json
   PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
2. Verify you are on xplat-010-repository-bash-confinement (or the slice
   branch for the current PR), never main
3. Set PYTHONDONTWRITEBYTECODE=1 for all runner invocations

### Implementation Notes
- House test convention: unittest, custom __main__ printing
  "<label>: {passed}/{total} passed", one test method per former set_test,
  counted subTest for loops. Match existing ported modules under
  tests/speckit-pro/layer4-scripts/ for style.
- Port protocol per slice: capture VERBOSE=true bash baseline into
  tests/speckit-pro/parity/xplat-010/<script>-baseline.txt → port with names
  preserved 1:1 → dual-run diff recorded in the PR body → manifest flip →
  .sh delete. All in one PR.
- Shipped-runner changes (PRs 2, 10, and 13 only): after any
  speckit_pro_runner byte change, run the payload/proof regeneration ritual —
  manifest sha256 recompute, scripts/build-plugin-payloads.py, checksum-based
  fixture sync, per-row proof hash recompute, evidence regeneration in gate
  order with release-readiness LAST and home-directory sanitization
  (committed evidence uses <home>).
- Workflow edits (PRs 5, 11, 12) update the matching self-referential
  workflow validators in the same PR, and note branch-protection
  required-check changes in the PR body.
- PR titles/bodies: conventional-commit prefix + plain English for the
  public; feat/fix PRs carry the Release note block once PR 12 lands (author
  them from PR 1 onward anyway — they seed the composer's first real run).
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| PR 1 — orphan deletion + ledger | | | |
| PR 2 — suite manifest + run-all.py | | | |
| PRs 3a/3b — L1 validator ports | | | |
| PR 4 — MOC lints + codex validators | | | |
| PR 5 — L5 + toolchain + CI dispatch swap | | | |
| PR 6 — scripts + hooks ports | | | |
| PRs 7a/7b — L7 replay harness | | | |
| PR 8 — L8 parity | | | |
| PR 9 — live-eval runners | | | |
| PR 10 — confinement guard + bash deletion | | | |
| PR 11 — container/Windows preflight CI | | | |
| PR 12 — release-notes pipeline | | | |
| PR 13 — spec-size estimator runner op | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Full deterministic suite passes: `python3 tests/speckit-pro/run-all.py` headline equals the ledger-predicted total
- [ ] Runner gates pass: toolchain preflight, default suite, active-path guard, repo-bash-confinement guard, payload evidence, install verification, release readiness
- [ ] `git ls-files '*.sh'` returns only `.github/workflows/`-adjacent zero results plus allowlisted `.specify/**`
- [ ] Docs validation passes: `pnpm --dir docs-site validate`
- [ ] Container preflight + Windows smoke evidence artifacts recorded
- [ ] Release-notes composer proven on a real release (first release after PR 12 merges shows Highlights)
- [ ] PRs created and reviewed (14-PR stack, each independently green)
- [ ] Merged to main branch (humans merge; autopilot never merges)

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```
racecraft-plugins-public/
├── speckit-pro/                    # Shipped plugin (Python runner in speckit_pro_runner/)
│   └── speckit_pro_runner/gates/   # Suite gate + active_path_guard (PRs 2, 10 touch here)
├── dist/{claude,codex}/speckit-pro # Generated payloads (regen ritual on runner changes)
├── tests/speckit-pro/              # Repo-side harness (primary port surface; never shipped)
│   ├── suite-manifest.json         # NEW: single source of truth per layer (PR 2)
│   ├── run-all.py                  # NEW: developer orchestrator (PR 2)
│   └── parity/xplat-010/           # NEW: committed VERBOSE baselines
├── scripts/                        # Helper ports (PR 6) + compose-release-notes.py (PR 12)
├── .claude/hooks/                  # Hook ports (PR 6)
├── .specify/                       # Vendored upstream (allowlisted, never ported)
├── .github/workflows/              # Dispatch glue only + container-preflight.yml (PR 11)
├── docs/ai/specs/.process/         # Workflow state, ledgers, evidence
└── specs/xplat-010-repository-bash-confinement/  # This spec's CONTRACT artifacts
```

---

Template based on SpecKit best practices, populated from the XPLAT-010 roadmap entry and the design concept interview on 2026-07-08.

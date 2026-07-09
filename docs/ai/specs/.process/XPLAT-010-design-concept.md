---
topic: "Repository Bash confinement and CI dispatch guard"
slug: "xplat-010-repository-bash-confinement"
date: "2026-07-08"
mode: "setup"
spec_id: "XPLAT-010"
source_input:
  type: "topic"
  ref: "XPLAT-010 scope from docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md, enriched by the approved Workstream 2 execution design"
question_count: 11
stop_reason: "natural"
---

# Design Concept: Repository Bash Confinement and CI Dispatch Guard

> **Source:** XPLAT-010 roadmap entry + approved execution design (triage ledger, PR stack, count-parity protocol) + operator scope addition (public release notes)
> **Date:** 2026-07-08
> **Questions asked:** 11
> **Stop reason:** natural (all branches converged; every recommendation accepted)

## Goals

- Enforce the strict repository policy that Bash may remain only as GitHub
  CI/CD workflow dispatch glue: a repo-wide scan excluding `.github/workflows/`
  finds zero `.sh` files and zero Bash-shebang executables, with a narrow
  documented allowlist for vendored `.specify/**` upstream files that can never
  satisfy release readiness.
- Port every active repo-local surface to Python 3.11+ stdlib: test harness
  (~45 Python files from ~69 bash), `scripts/**` helpers, `.claude/hooks/**`,
  and the live-AI eval runners (Layers 2/3/6), preserving every CLI/output
  contract.
- Replace `run-all.sh` with `tests/speckit-pro/suite-manifest.json` (single
  source of truth per layer) + a `tests/speckit-pro/run-all.py` orchestrator
  preserving the bash UX (`--layer N`, `--live`, `--all`, toolchain preflight,
  `X/Y passed` headline, exit codes) — Q2.
- Prove zero check regressions per port PR via the count-parity protocol:
  committed VERBOSE=true baselines (ordered check-name inventory + runtime
  count), 1:1 name preservation, same-PR swap (port + manifest flip + `.sh`
  delete), dual-run diff in the PR body, running count ledger — Q3.
- Add a `repo-bash-confinement-guard` runner gate composed into release
  readiness and CI, failing on any new Bash script, active Bash invocation, or
  `jq` dependency outside the workflow dispatch boundary.
- Add container/runner preflight CI: Linux amd64/arm64 container jobs (gating,
  path-filtered) and Windows x64/ARM64 direct-runner smoke (advisory,
  continue-on-error, availability recorded) — Q6/Q7. Preflight-only; never
  substitutes XPLAT-008 native operator UAT.
- Make every GitHub Release readable by the world: each feat/fix PR carries a
  consumer-facing "Release note" block (enforced by a required CI check with a
  `release-note/skip` label escape), and a Python stdlib composer rewrites the
  GitHub Release body at publish time — plain-English Highlights up top, the
  conventional-commit list preserved below as an appendix. CHANGELOG.md stays
  the machine ledger — Q10/Q11. This closes the "public release notes" item
  deferred from the XPLAT-008 handoff.
- **Accepted split (slice-sizing):** one spec delivered as a ~13-PR stack —
  (1) orphan-test deletion + ledger, (2) suite manifest + run-all.py +
  manifest-reading suite gate, (3a/3b) 20 mechanical L1 validators, (4) MOC
  lints + codex validators, (5) L5 + toolchain + `pr-checks.yml` dispatch swap,
  (6) scripts + hooks ports, (7a/7b) L7 replay harness, (8) L8 parity, (9)
  live-eval runners, (10) confinement guard + final bash deletion, (11)
  container-preflight CI, (12) release-notes composer + validate-release-note
  check + release.yml step. Ordering: 1 anytime; 2 before 3–10; 10 after 3–9;
  11 last among confinement PRs; 12 independent (any time) — Q9/Q10.

## Non-goals

- Porting the 34 orphaned bash tests (32 layer-4 tests of XPLAT-009-deleted
  scripts + 2 wrappers) — they are deleted with a disposition ledger, not
  ported (Q1).
- Forking/porting the 10 vendored `.specify/**` upstream Spec Kit helpers —
  allowlisted with `release_readiness_excluded: true` instead (Q8).
- Treating Docker, QEMU, or Windows containers as native installed-plugin UAT
  evidence — XPLAT-008's native operator UAT matrix remains the only
  release-satisfying evidence (roadmap out-of-scope, reaffirmed in Q7).
- Plugin source / generated payload cleanup — completed by XPLAT-009.
- Splitting into multiple specs — rejected in Q9 in favor of one spec with a
  typed-split 12-PR stack.
- Making Windows smoke jobs required checks — advisory only (Q7).

## Design Tree (Q&A log)

### Q1. The triage ledger found 34 orphaned bash test scripts (32 layer-4 tests that test scripts XPLAT-009 already deleted, plus 2 seven-line wrappers) — none are referenced by run-all.sh's active 17-entry list. How should these be dispositioned?

**Branch:** Test-harness triage

**Recommended answer:** Delete + ledger
> Delete all 34 in a deletion-only first PR with a committed disposition ledger
> (`docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md`). Git history
> preserves content; matches the constitution's KISS/YAGNI principle.

**Alternatives offered:**
- Archive then delete: safer window, but the zero-bash guard would need to allowlist the archive, weakening the confinement claim.
- Port them too: ~5,000 LOC of dead-on-arrival review burden for zero active coverage.

**User's answer:** Delete + ledger (Recommended)

---

### Q2. The shipped runner's suite gate currently regex-parses run-all.sh to discover test layers. Replace with a repo-side tests/speckit-pro/suite-manifest.json read by the shipped suite gate, plus a run-all.py orchestrator preserving the bash UX?

**Branch:** Suite architecture

**Recommended answer:** Manifest + run-all.py
> Decouples the shipped runner from bash parsing, keeps one source of truth per
> layer, preserves every operator habit. Avoids making every test add/remove a
> shipped-runner byte change (which would trigger the payload/proof regen
> ritual each time).

**Alternatives offered:**
- Hardcode layers in suite.py: couples test-list churn to shipped-runner rebuilds.
- run-all.py as source of truth, suite.py parses it: recreates the parse-a-script coupling the manifest removes.

**User's answer:** Manifest + run-all.py (Recommended)

---

### Q3. How should each port PR prove zero check regressions?

**Branch:** Count parity / regression proof

**Recommended answer:** Committed baselines + same-PR swap
> Runtime counts (not static grep) catch loop-generated checks; same-PR swap
> (port + manifest flip + `.sh` delete in one PR) leaves no window where a
> layer runs zero coverage; committed VERBOSE=true baselines
> (`tests/speckit-pro/parity/xplat-010/<script>-baseline.txt`) make the diff
> reviewable; running ledger `XPLAT-010-count-ledger.md`; final
> `XPLAT-010-suite-parity-result.json`.

**Alternatives offered:**
- Total-count assertion only: a dropped check masked by a gained check passes silently.
- Two-phase port-then-delete: doubles CI time and PR count (~20+).

**User's answer:** Committed baselines + same-PR swap (Recommended)

---

### Q4. The two .claude/hooks bash scripts (guard-version-triplet.sh, validate-structural.sh) are not wired to any settings file — no .claude/settings.json exists in the repo. What should XPLAT-010 do with them?

**Branch:** Hooks

**Recommended answer:** Port to Python
> Port both to `.claude/hooks/*.py` preserving the stdin-JSON / exit-0-or-2
> hook contract. Cheap (~2 small files), removes the `jq` dependency, keeps the
> guard capability ready for whenever they get wired. Zero CI risk since
> nothing invokes them today (verified: no `.claude/settings*.json` in repo).

**Alternatives offered:**
- Delete them: simplest, but loses the documented version-triplet guard intent.
- Leave + allowlist: permanently weakens the zero-bash claim for two trivially portable files.

**User's answer:** Port to Python (Recommended)

---

### Q5. The live-AI eval harnesses (Layer 2 trigger, Layer 3 functional, Layer 6 efficiency — all developer-local, invoking claude -p or codex) are bash today. Port within this spec or defer?

**Branch:** Live-eval harness scope

**Recommended answer:** Port in this spec
> Port the L2/L3/L6 runners preserving their CLI arg contracts and
> `run_codex_evals` staging semantics, with local smoke transcripts as
> evidence. They are active test surfaces — leaving them bash would force a
> broad `tests/` allowlist that guts the confinement claim and blocks the
> spec's "Done When" gate.

**Alternatives offered:**
- Defer to a follow-up spec: XPLAT-010 would close with its zero-bash gate unmet.
- Delete, rely on manual evals: destroys reproducible eval infrastructure right before the full verification program needs it.

**User's answer:** Port in this spec (Recommended)

---

### Q6. When should the new container-preflight workflow (Linux amd64/arm64 containers + Windows x64/ARM64 direct-runner smoke) run?

**Branch:** CI trigger policy

**Recommended answer:** Path-filtered PR + manual
> `pull_request` filtered to runner/gate/workflow paths
> (`speckit-pro/speckit_pro_runner/**`, the suite manifest, the workflow
> itself) plus `workflow_dispatch`. Catches regressions where they can happen
> without burning multi-platform runner jobs on docs-only PRs.

**Alternatives offered:**
- Every PR: maximum coverage, but slowest-runner cost on changes that cannot affect the runner.
- Nightly + manual: regressions land on main before detection.

**User's answer:** Path-filtered PR + manual (Recommended)

---

### Q7. Should the container-preflight jobs gate PR merges or run as advisory evidence?

**Branch:** CI gating policy

**Recommended answer:** Linux gates, Windows advisory
> Linux amd64/arm64 container jobs become required checks on the paths they
> trigger for (stable, controlled images). Windows x64/ARM64 smoke runs
> `continue-on-error` with availability recorded — `windows-11-arm` is
> newer/less available and a flaky non-owned runner must not block merges
> (CLAUDE.md Scenario 7 documents this exact failure mode with the latest-jq
> leg). Matches the roadmap's "recorded without converting to UAT" framing.

**Alternatives offered:**
- All advisory: a broken Linux container path could merge silently.
- All gating: Windows runner availability issues would block unrelated PRs.

**User's answer:** Linux gates, Windows advisory (Recommended)

---

### Q8. The 10 vendored .specify/** helper scripts are upstream GitHub Spec Kit files. Keep them behind a narrow per-file guard allowlist marked release_readiness_excluded: true?

**Branch:** Vendored upstream exceptions

**Recommended answer:** Allowlist + exclude
> Document-and-guard per the roadmap's "non-active upstream-generated
> exceptions" clause: fail-closed per-file allowlist, excluded from release
> readiness, CI fails if any new `.specify` bash appears. Upstream stays
> upstream (PRD non-goal to port third-party code).

**Alternatives offered:**
- Port them anyway: a permanent fork of third-party code the PRD scoped out.
- Delete and re-vendor on demand: breaks checked-in SpecKit integration state mid-flight.

**User's answer:** Allowlist + exclude (Recommended)

---

### Q9. Slice-sizing: reviewability gate returned warn (400 LOC / 6 production files / 15 total / 2 primary surfaces); roadmap budget projects 400-800 LOC / 15-25 files. Accept the approved ~12-PR stack under one spec?

**Branch:** Slice-sizing (SPIDR/INVEST)

**Recommended answer:** Accept the 12-PR stack
> Each PR is independently CI-green, dependency-ordered (1 anytime; 2 before
> 3–10; 10 after 3–9; 11 last), and sized to the 400–800 reviewable-LOC PRSG
> budget. The typed-split exception the roadmap anticipated is recorded in the
> workflow file, satisfying the reviewability gate's warn. Note: the shared
> `estimate-spec-size` runner operation was unavailable (see Open Questions);
> the reviewability-gate setup result and roadmap budget served as the size
> evidence.

**Alternatives offered:**
- Split into 2–3 separate specs: adds scaffold/workflow overhead without shrinking any single PR.
- Fewer, larger PRs (4–5): each blows past the 800-LOC block threshold.

**User's answer:** Accept the 12-PR stack (Recommended)

---

### Q10. How should human-readable release notes be produced? (Today the GitHub Release body is release-please's raw conventional-commit list.)

**Branch:** Public release notes (operator scope addition mid-interview, citing speckit-pro-v2.18.0's release body as the exemplar of the problem)

**Recommended answer:** PR-authored highlights + composer
> Each feat/fix PR carries a short "Release note" block in its body written for
> plugin consumers — the repo already mandates public-readable PR bodies, so
> this extends an existing rule rather than adding a new one. At release time a
> Python stdlib composer harvests the blocks for all commits since the last tag
> (via the GitHub API) and rewrites the GitHub Release body: a Highlights
> narrative up top, the conventional-commit list kept below as an appendix.
> Deterministic, testable, no new secrets — the Kubernetes/Rust
> release-notes-from-PR-metadata pattern. CHANGELOG.md stays the machine
> ledger.

**Alternatives offered:**
- AI-generated summary in CI: zero authoring burden but nondeterministic output in a deterministic-gates repo, plus a new secret and per-release cost.
- Config-only cleanup (changelog-sections): polishes the flat commit list without fixing it.

**User's answer:** PR-authored highlights + composer (Recommended)

---

### Q11. Should CI enforce that every feat/fix PR carries the "Release note" block?

**Branch:** Public release notes — enforcement

**Recommended answer:** Required check + skip label
> A `validate-release-note` check (Python, alongside `validate-pr-title`) fails
> feat/fix PRs missing the block; a `release-note/skip` label bypasses it for
> changes with no consumer-visible effect. Advisory checks decay — without
> enforcement the composer falls back to raw commit subjects within a few
> releases, recreating today's problem.

**Alternatives offered:**
- Warn-only: zero friction but reliably ignored.
- No check, composer fallback: quality depends entirely on memory.

**User's answer:** Required check + skip label (Recommended)

## Open Questions

- **What:** The `estimate-spec-size` runner operation referenced by the
  grill-me skill does not exist in the 2.18.0 runner — the only trace is
  `estimate-spec-size.sh` in the guard's historical-scripts allowlist (the
  bash was deleted by XPLAT-009; a runner port never landed).
  **Why deferred:** Plugin defect discovered while dogfooding 2.18.0 during
  this interview; out of XPLAT-010's repository-confinement scope.
  **Suggested next step:** File a `fix(speckit-pro)` follow-up to either port
  the estimator as a runner operation or correct the grill-me/speckit-prd
  skill references. Do not fold into XPLAT-010.
- **What:** L8 parity's `semantic-equivalent` tolerance still skips with a
  warning (needs an LLM judge).
  **Why deferred:** Pre-existing known gap; PR 8 ports the harness as-is.
  **Suggested next step:** Follow-up spec after XPLAT-010; the port must
  preserve the skip-with-warning behavior, not silently drop the tolerance.
- **What:** Windows ARM64 (`windows-11-arm`) runner availability at
  implementation time.
  **Why deferred:** External to the repo; roadmap already requires recording
  unavailable/public-preview behavior rather than blocking on it.
  **Suggested next step:** PR 11 records per-label availability in the
  evidence artifact.

## Recommended Next Step

Setup mode — scaffolding continues automatically: populate
`docs/ai/specs/.process/XPLAT-010-workflow.md` from this doc, then run
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/XPLAT-010-workflow.md`.

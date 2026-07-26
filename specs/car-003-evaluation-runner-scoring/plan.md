# Implementation Plan: Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Branch**: `car-003-evaluation-runner-scoring` | **Date**: 2026-07-24 | **Spec**: `specs/car-003-evaluation-runner-scoring/spec.md`

**Input**: Feature specification from `specs/car-003-evaluation-runner-scoring/spec.md`

## Summary

CAR-003 builds the qualification *platform* for later Claude Code agent-routing
cohorts. It publishes an additive successor capability freeze that admits only
tuples present in both the official-source candidate ledger and the pinned
runtime, proves the exact treatment each candidate received before any outcome is
scored, scores a governed twelve-role corpus through deterministic hard gates and
blinded ballots, and freezes a numeric analysis plan whose decisions replay
bit-for-bit. It creates no final route policy.

The technical approach is deliberately thin. Four Clarify sessions and the
accepted design concept already fixed every architectural choice; planning adds
one shipped Python module, six harness modules, eight spec-scoped JSON Schemas,
and seven unit-test files. The eight schemas carry the rules — closed
enumerations, required bindings, conditional shapes — and Python carries only
what a schema cannot express: set-intersection admission, byte-level read-back
hashing, disposition precedence over a co-firing reason set, the ordered decision
ladder, digest recomputation, objective-level partition disjointness, the
cross-record resolution checks a single-document schema cannot reach (an admitted
tuple's runtime evidence resolving to this freeze's own snapshot rather than the
archived one, and the alias-attribution record's freeze binding resolving to a
published CAR-003 freeze), and re-deriving the score bundle's resource vector and
reasoning-token report from the digest-verified trace so the trace stays the sole
source of truth. That
posture is inherited from the existing CAR-002 validator, which checks the entire
frozen trace contract in 240 lines by driving every rule *from* the schema.

Delivered as three ordered review slices with roadmap Work Package A intact as
the first.

## Technical Context

**Language/Version**: Python 3.11+, standard library only. No new Bash, no `jq`,
no external evaluation framework.

**Primary Dependencies**: None added. Consumes, without modifying, the existing
CAR-002 module family under the Layer 6 test tree: `claude_capabilities.py`
(probe matrix, sanitization, payload hashing), `claude_trace_schema.py`
(schema-driven validation of the frozen trace contract), `treatment_trace_io.py`
(canonical JSON serialization), `treatment_trace_bundle.py` (bundle-graph
validation), `treatment_trace_authority.py` (route ownership and telemetry
inventory).

**Storage**: Digest-addressed JSON documents on disk. Raw captures stay in the
operator-only content-addressed retention store and are never committed.

**Testing**: `python3 tests/speckit-pro/run-all.py` — the single deterministic
gate, serving as both unit test and full verification. Baseline green at
3251/3251 with zero live calls. There is no BUILD, TYPECHECK, or LINT command in
this repository.

**Target Platform**: Claude Code CLI on macOS, Linux, and Windows; CI on Linux.

**Project Type**: Plugin source (`speckit-pro/`) plus repository-only validation
harness (`tests/speckit-pro/`).

**Performance Goals**: Determinism and replayability are the operative properties,
but they are not free — the deterministic suite is the only surface that
demonstrates SC-011 replay and SC-019 zero-live-call behavior, so an unbounded
suite would leave both criteria unverifiable in routine practice (FR-057). Three
bounds therefore apply:

- **Deterministic replay**: p95 replay-bundle runtime under 10 seconds on a normal
  developer checkout, matching the Codex twin's declared bound. The two platforms
  must not diverge on whether replay cost is a stated property, since SC-011 is
  claimed identically on both.
- **Default suite**: CAR-003's additions must keep
  `python3 tests/speckit-pro/run-all.py` within 6 minutes wall-clock on the CI
  runner, derived from the measured pre-change baseline of roughly 4m30s at
  3251/3251. The test workflow declares no `timeout-minutes`, so this budget is
  the only ceiling; anything that would exceed it moves behind the operator-only
  live path instead of entering the default suite.
- **Replay fixtures**: bounded in count and size rather than growing per campaign,
  so suite cost does not scale with accumulated cohort evidence.

The default suite must make zero live model calls. Live campaign performance is
recorded under frozen budgets and guardrails, not optimized by this feature.

**Constraints**: No second materializer. No API-key requirement on any supported
path. CAR-002 evidence and schemas immutable — emit new records under them, never
edit. Repo-level shared contracts are byte-identical across the Claude and Codex
worktrees and must not be unilaterally extended. Live campaigns are
operator-only, explicit, local, pinned, and budgeted.

**Scale/Scope**: 12 governed roles, 8 decision-bearing Pareto dimensions, a
5-rung effort ladder, 4 refresh triggers, 5 partition types, 3 review slices.

**Reviewability Budget**: single primary review surface of harness/adapter; 1,858
authored logic LOC; 1 shipped production file; 23 authored files; result is split
required, implemented and reviewed as three ordered slices. Derivation and the
governing per-review-unit figures are in **Reviewability Gate** below.

## Declared File Operations

Machine-generated artifacts are listed for completeness and are excluded from the
reviewable count — `AGENTS.md` forbids hand-editing them, and
`scripts/refresh-release-artifacts.py` is their only sanctioned mutator.

- NEW speckit-pro/speckit_pro_runner/materializer.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py
- MODIFIED tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py
- MODIFIED tests/speckit-pro/layer6-efficiency/.gitignore
- NEW tests/speckit-pro/layer6-efficiency/fixtures/car-003-alias-repoint-replay.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures/car-003-role-corpus.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures/car-003-calibration-replay.json
- NEW tests/speckit-pro/unit/test-canonical-agent-materializer.py
- NEW tests/speckit-pro/unit/test-successor-capability-freeze.py
- NEW tests/speckit-pro/unit/test-exact-treatment-runner.py
- NEW tests/speckit-pro/unit/test-role-corpus-governance.py
- NEW tests/speckit-pro/unit/test-score-bundle-adjudication.py
- NEW tests/speckit-pro/unit/test-experiment-policy-partitions.py
- NEW tests/speckit-pro/unit/test-analysis-decision-ladder.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- NEW docs/ai/research/claude-car-003-mandatory-observation-manifest.json
- NEW docs/ai/research/claude-car-003-successor-capability-freeze.json
- NEW docs/ai/research/claude-car-003-analysis-plan.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED speckit-pro/speckit_pro_runner/install_inventory.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- NEW dist/claude/speckit-pro/speckit_pro_runner/materializer.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/install_inventory.json
- NEW dist/codex/speckit-pro/speckit_pro_runner/materializer.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/install_inventory.json

**Note on the mechanical estimator**: `estimate-reviewable-loc` classifies a
production file by path prefix (`src/`, `app/`, `lib/`, `scripts/`) or by a
JavaScript/TypeScript/SQL extension. This repository's Python lives under
`speckit-pro/` and `tests/speckit-pro/`, so almost nothing matches and its
`production x 40` projection collapses toward zero. That is a known heuristic
gap, not evidence of a trivial change. The authoritative figures are the
hand-derived ones below, checked by the setup-mode reviewability gate.

## Constitution Check

*GATE: evaluated before Phase 0 research and re-evaluated after Phase 1 design.*

Assessed against the ratified constitution v1.2.0, which defines **six** core
principles.

| # | Principle | Result | Evidence |
|---|---|---|---|
| I | Plugin Structure Compliance | **PASS** | The one new shipped file is a module inside the existing `speckit_pro_runner` package — no new plugin, manifest, command, agent, skill, or hook. All CAR-003 tests live under top-level `tests/speckit-pro/`, outside the install-facing plugin directory. Layer 1 structural validation covers the regenerated payloads. |
| II | Cross-Platform Runtime & Script Safety | **PASS** | Python 3.11+ standard library only; no Bash, no `jq`, no PowerShell, no package installation. JSON handled by the standard `json` module. Path handling uses `pathlib`. Any subprocess use inherits the existing argument-array, `shell=False`, explicit-return-code idiom already in the smoke runner. Live probes are operator-only and never on an active repository path. |
| III | Semantic Versioning | **PASS** | No manual version edit. Adding a runner module does not bump `plugin.json`; release-please owns version movement. |
| IV | Test Coverage Before Merge | **PASS** | Every new module gets Layer 4 unit coverage under `tests/speckit-pro/unit/`, and each new test is registered in `tests/speckit-pro/suite-manifest.json`. Completion bar is the 3251 baseline plus the new tests, green, zero live calls. |
| V | Conventional Commits | **PASS** | Three slice PRs, each titled `<type>(speckit-pro): <plain English description>`, validated against the live release-readiness gate before the PR is marked ready. |
| VI | KISS, Simplicity & YAGNI | **PASS** | One materializer, not two. The "thin Layer 6 adapter" is an import and a call, so it does not get its own file. Three additive record classes share one `oneOf` schema, and three pre-execution binding records share another, mirroring the frozen CAR-002 contract's own `oneOf` idiom rather than inventing a new convention. No abstraction is introduced for a single call site. The CAR-002 module family is consumed rather than re-implemented. |

**Post-design re-evaluation**: unchanged. All six still pass. Phase 1 added eight
schemas and no new Python surface beyond what Phase 0 projected, and the two
grouped schemas actively reduced file count relative to a one-schema-per-record
layout.

**Complexity Tracking**: not required — no violations to justify.

### Reviewability requirements from the constitution

- **Primary surface**: harness/adapter. Secondary surfaces are seed/config and
  docs/process. One primary review surface, within the threshold.
- **Budget status**: exceeds the whole-feature budget, so the split below is
  mandatory rather than advisory. See **Reviewability Gate**.
- **Split decision**: recorded below with per-slice scope and requirement
  mapping. No deferred work — every requirement lands inside one of the three
  slices, so there is no follow-up spec or issue ID to name.
- **PR review packet source**: `spec.md` "PR Review Packet Requirements". Each
  slice PR carries what changed, why, non-goals, review order, scope budget,
  traceability, verification evidence, known gaps, and rollback notes.

## Project Structure

### Documentation (this feature)

```text
specs/car-003-evaluation-runner-scoring/
├── plan.md                                  # This file
├── research.md                              # Phase 0 output
├── data-model.md                            # Phase 1 output
├── quickstart.md                            # Phase 1 output
├── contracts/                               # Phase 1 output
│   ├── successor-capability-freeze.schema.json
│   ├── role-corpus.schema.json
│   ├── score-bundle.schema.json
│   ├── experiment-policy.schema.json
│   ├── analysis-plan.schema.json
│   ├── analysis-decision.schema.json
│   ├── experiment-assignment.schema.json
│   └── car-003-additive-records.schema.json
├── checklists/
├── SPEC-MOC.md
└── tasks.md                                 # Phase 2 output, not created here
```

### Source Code (repository root)

```text
speckit-pro/
└── speckit_pro_runner/
    └── materializer.py                      # NEW — the only shipped production file

tests/speckit-pro/
├── suite-manifest.json                      # MODIFIED — register new unit tests
├── layer6-efficiency/
│   ├── run-efficiency-benchmarks.py         # MODIFIED — smoke demotion (shared, dual-platform)
│   ├── .gitignore                           # MODIFIED — allow consolidated baselines
│   ├── contracts/                           # SHARED, byte-identical, NOT modified
│   ├── lib/
│   │   ├── claude_capabilities.py           # consumed, not modified
│   │   ├── claude_trace_schema.py           # consumed, not modified
│   │   ├── treatment_trace_io.py            # consumed, not modified
│   │   ├── treatment_trace_bundle.py        # consumed, not modified
│   │   ├── treatment_trace_authority.py     # consumed, not modified
│   │   ├── claude_successor_freeze.py       # NEW — slice 1
│   │   ├── claude_treatment_runner.py       # NEW — slice 1
│   │   ├── claude_role_corpus.py            # NEW — slice 2
│   │   ├── claude_score_bundle.py           # NEW — slice 2
│   │   ├── claude_experiment_policy.py      # NEW — slice 3
│   │   └── claude_analysis_decision.py      # NEW — slice 3
│   └── fixtures/
│       ├── car-003-alias-repoint-replay.json    # NEW — slice 1
│       ├── car-003-role-corpus.json             # NEW — slice 2
│       └── car-003-calibration-replay.json      # NEW — slice 3
└── unit/                                    # 7 NEW test files, one per module

docs/ai/research/
├── claude-trace-contract.schema.json        # frozen, consumed, not modified
├── claude-runtime-capability-snapshot.json  # CAR-002, immutable
├── claude-car-003-mandatory-observation-manifest.json   # NEW — slice 1
├── claude-car-003-successor-capability-freeze.json      # NEW — slice 1 (operator-produced)
└── claude-car-003-analysis-plan.json                    # NEW — slice 3 (post-calibration)
```

**Structure Decision**: the repository's established two-tier split is preserved
exactly. Anything a shipped surface consumes lives in `speckit-pro/`; everything
that only validates the repository lives under `tests/speckit-pro/`. The
canonical materializer is the single item crossing into the shipped tier, because
CAR-006's frontmatter drift gate and session preflight will consume it. That
crossing is what makes the roadmap's recorded `Production files: 0` obsolete, and
it is the only such crossing in this feature.

## Reviewability Gate

*FR-025 and SC-013. This section is the authoritative re-derivation the spec
requires. It supersedes the roadmap's recorded budget.*

### What changed since the roadmap was written

The roadmap recorded `Production files: 0` and placed the materializer under the
test tree. The accepted design concept (Q4) moved it into `speckit_pro_runner` so
that CAR-006 consumes one component rather than a copy. `spec.md` records that the
roadmap entry is superseded and that the production-file budget must be re-derived
here. It is, below.

### Derivation

**Authored implementation files: 23.** Twenty new plus three modified
(`run-efficiency-benchmarks.py`, `.gitignore`, `suite-manifest.json`). The spec
projected 18-26; the derived figure is 23. The concern that the projected upper
bound of 26 would touch the gate's 25-file block threshold does not materialize at
the whole-feature level, and does not come close at the slice level.

**Production files: 1.** Exactly one authored file ships in the installed plugin
payload — `speckit-pro/speckit_pro_runner/materializer.py`. The spec projected
6-10; that projection was made before the shipped surface was enumerated and is an
order of magnitude high. The reason the real number is 1 is structural: the design
concept fixed a *single* materializer and forbade a second, everything else
CAR-003 builds is repository-only validation, and constitution principle I
requires repository-only tests to live outside the install-facing directory.
Eleven further shipped-payload paths change, but all eleven are machine-generated
by `scripts/refresh-release-artifacts.py` and are forbidden to hand-edit, so they
are verification surface, not review surface.

**Reviewable LOC: 1,858.** Authored Python logic, new and modified, across the
shipped module and the six harness modules. Composition:

| Module | Slice | LOC |
|---|---|---|
| `materializer.py` (shipped) | 1 | 170 |
| `claude_successor_freeze.py` | 1 | 260 |
| `claude_treatment_runner.py` | 1 | 250 |
| `run-efficiency-benchmarks.py` (delta) | 1 | 55 |
| `claude_role_corpus.py` | 2 | 200 |
| `claude_score_bundle.py` | 2 | 330 |
| `.gitignore` (delta) | 2 | 3 |
| `claude_experiment_policy.py` | 3 | 250 |
| `claude_analysis_decision.py` | 3 | 340 |
| **Total** | | **1,858** |

This lands inside the spec's projected 1,800-2,400 band. Unit-test bodies
(approximately 1,700 further lines), JSON data manifests, and generated payloads
are verification and data surface, counted separately and excluded here — the same
boundary the repository's own estimator draws when it classifies production files.

### Per-slice figures

| Slice | Authored files | Regenerated | Changed paths | Logic LOC | Shipped production files |
|---|---|---|---|---|---|
| 1 — US1 + US2 (WP-A) | 11 | 12 | 23 | 735 | 1 |
| 2 — US3 | 7 | 0 | 7 | 533 | 0 |
| 3 — US4 | 7 | 0 | 7 | 590 | 0 |

Slice 1 absorbs the entire generated-artifact refresh because it is the only slice
that changes shipped source. Twenty-three changed paths is under the 25-file block
threshold with two paths of margin. If implementation discovers the regenerated
set is larger than twelve, the correct response is to re-run this gate and record
the result — **not** to split Work Package A, which FR-025 and the roadmap require
to stay intact.

### Split decision

**Split required.** One specification is kept, because the freeze, treatment,
scoring, and analysis contracts must stay coherent; three ordered implementation
and review slices, because a single PR would cross the block thresholds.

**Slice 1 — Successor freeze and materialized treatment trace.** Roadmap Work
Package A, kept intact.

- Requirements: FR-001 … FR-010, FR-027 … FR-032, FR-039 … FR-046, FR-051.
- Files: `materializer.py`; `claude_successor_freeze.py`;
  `claude_treatment_runner.py`; `run-efficiency-benchmarks.py`; the alias-repoint
  replay fixture; the mandatory-observation manifest; the published successor
  freeze; three unit tests; `suite-manifest.json`; the twelve regenerated
  artifacts.
- Contracts exercised: `successor-capability-freeze`, `car-003-additive-records`.
- Verification: `quickstart.md` sections 3 and 6.

**Slice 2 — Governed corpus, hard gates, blinded scoring.**

- Requirements: FR-011 … FR-016, FR-033 … FR-036, FR-047, FR-048.
- Files: `claude_role_corpus.py`; `claude_score_bundle.py`; the role-corpus
  fixture; `.gitignore`; two unit tests; `suite-manifest.json`.
- Contracts exercised: `role-corpus`, `score-bundle`.
- Verification: `quickstart.md` section 4.

**Slice 3 — Experiment policy, statistics, calibration pilot.**

- Requirements: FR-013 (registry), FR-017 … FR-024, FR-037, FR-038, FR-049,
  FR-050, FR-052 … FR-056, FR-058, plus FR-026 re-verification.
- Files: `claude_experiment_policy.py`; `claude_analysis_decision.py`; the
  calibration replay fixture; the frozen analysis plan; two unit tests;
  `suite-manifest.json`.
- Contracts exercised: `experiment-policy`, `analysis-plan`, `analysis-decision`,
  `experiment-assignment`.
- Verification: `quickstart.md` sections 5 and 8.

**Cross-cutting requirements.** Two requirements are not slice-local because they
govern the whole feature rather than a module: **FR-025** (three ordered slices,
reviewability gate re-run during planning) is discharged by the **Reviewability
Gate** section above, and **FR-057** (default-suite wall-clock budget, bounded
replay fixtures, quantified replay bound) constrains every slice's fixtures and is
declared in **Performance Goals** above. Both are verified in Polish rather than
inside a single slice.

**Deferred work**: none. Every requirement lands in a slice or in the two
cross-cutting entries above, so there is no follow-up spec or issue ID to name. The
excluded policy areas — CAR-004 policy controls, CAR-005 availability simulation,
CAR-006 resolver and preflight, CAR-011 the `autopilot-fast-helper` agent — were
already out of scope in the spec, not deferred by this plan.

### Re-verification against the task list

*Re-run at Setup against the committed `tasks.md`, as FR-025 and SC-013 require.*

The task list decomposes the feature into 86 tasks. Re-deriving the budget from
the repository paths those tasks actually name reproduces the per-slice figures
above with no change: slice 1 names 11 authored files and 735 logic LOC, slice 2
names 7 and 533, slice 3 names 7 and 590. The whole-feature total holds at 23
authored files, because `suite-manifest.json` is the only path shared by all three
slices and is counted once.

The regenerated set named by T041 is **twelve** artifacts: `install_inventory.json`,
`speckit-pro-runner.manifest.json`, and `speckit-pro-runner.sha256` under
`speckit-pro/speckit_pro_runner/`; the installed-cache proof under
`tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`; and the four mirrored
payload paths under each of `dist/claude/` and `dist/codex/`. Twelve is not larger
than twelve, so the re-run trigger recorded above has not fired, and slice 1 holds
at 23 changed paths — two under the 25-file block threshold.

**Decision, unchanged: three ordered slices with Work Package A intact.** No task
moves a slice across a threshold, so there is no basis to subdivide US1 and US2,
which FR-025 and the roadmap require to stay together. The mechanical tasks-mode
estimator disagrees, projecting `86 x 40` reviewable LOC and classifying
production files by path prefix; neither heuristic fits a repository whose Python
lives under `speckit-pro/` and `tests/speckit-pro/` and whose task list is
deliberately fine-grained for TDD, so task count tracks test granularity rather
than diff size. The hand-derived figures above stay authoritative.

### Sequencing and coordination

1. **Sync from the default branch before slice 1 begins.** The shared
   dual-platform smoke runner is jointly owned with the in-flight Codex twin
   branch (FR-043). Checked at planning time: neither the default branch nor the
   twin has modified it, so the conflict is latent. Sync-before-edit is the cheap
   prevention.
2. Resolve any overlap on that file by `git merge`, never rebase — rebase rewrites
   the other branch's ancestry, and this repository resolves shared-infrastructure
   conflicts by merge.
3. Run the operator successor-freeze collection as the **first** operator action
   in slice 1, and record the result whichever way it resolves. It answers the
   standing open question of whether the `opus` alias has re-pointed since the
   archived snapshot.
4. Run `scripts/refresh-release-artifacts.py` and the plugin-shaped import check
   before slice 1 is called done. The refresh is idempotent and is the only
   sanctioned mutator of the generated tree.
5. Run the calibration pilot in slice 3 **before** freezing the analysis plan, and
   freeze the plan before any CAR-007 through CAR-010 cohort outcome exists.

## Contracts

Eight schemas under `contracts/`. Six mirror the Codex twin's committed
spec-scoped schemas logically; two are CAR-003-additive because the Claude side
needs records the twin does not publish.

| Contract | Relationship to the twin |
|---|---|
| `successor-capability-freeze` | Mirror. Diverges on the effort ladder (`low`…`max` versus the Codex ladder) and on one exclusion reason (`alias_repoint_unresolved` versus `hidden_state_disagreement`). Both are platform *values*, not logic. |
| `role-corpus` | Mirror. Identical twelve `role_id` values, verified against the shipped agent inventory. `mutation_contract` replaces the twin's `sandbox`. |
| `score-bundle` | Mirror. All four closed taxonomies adopted verbatim per FR-034, including `service_reroute`. Adds the FR-049 reasoning-token report and the FR-048 blinding residual. |
| `experiment-policy` | Mirror. Adds the FR-047 static family exclusion and the FR-022 cache ceilings by TTL class (key space closed to `ephemeral_5m` and `ephemeral_1h` through `propertyNames`). **Currently ahead of the twin**: `analysis_plan_binding` is conditional on `partition.qualification_eligible` rather than unconditionally required, closing the FR-037 transitive cycle. See Known Gaps. |
| `analysis-plan` | Mirror on the surfaces the twin publishes — `pareto_policy.dimensions` is exactly the eight of FR-018 with no added member. Multiplicity expanded to the three families FR-050 requires. Adds the CAR-owned FR-052 … FR-055 surfaces the twin does not carry: `workload_manifest.guardrail_method` (FR-053), per-stratum `membership_rule`, `stratum_minimum_unique_tasks`, and `stratum_sample_size` (FR-052, FR-054), `reliability_guardrails`, and structured `racing_policy` and `futility_policy` (FR-055). |
| `analysis-decision` | Mirror. Adds `decision_reasons` and `reported_limitations`, plus a guard restricting `decision=qualified` to a partition with `qualification_eligible=true`. `qualified` is unreachable from a calibration partition by **composition**, not by a single self-contained guard: this contract binds the decision to `qualification_eligible`, and `experiment-assignment`'s partition registry entry binds `partition_type=calibration` to `qualification_eligible=false` (FR-013). Both halves are required for the property to hold. |
| `experiment-assignment` | **CAR-003-additive.** The twin publishes no assignment schema. Carries the partition registry entry, the calibration protocol, and the comparison-set assignment, with the FR-037 calibration substitution enforced by schema and keyed on `qualification_eligible` so the branches are exhaustive. Also carries the FR-051 environment contract, whose values all reuse frozen CAR-002 route-resolution and snapshot fields, and the FR-052 `stratum_assignment` with its non-empty closed `membership_basis` and `derived_from_realized_outcomes` pinned false. Because the twin publishes no assignment schema, this addition creates no mirror divergence. |
| `car-003-additive-records` | **CAR-003-additive.** Carries **four** records that frozen closed enums and closed objects cannot hold: the mandatory-observation manifest (FR-009), the alias-repoint attribution with its `{id, digest}` freeze binding (FR-039, FR-045), the cache diagnostic including `observed_cache_isolation` (FR-022, FR-049), and the scorer identity attestation (FR-047). The attestation lives here rather than in `score-bundle` precisely because that contract is a parity mirror and must not gain a unilateral member. |

**Repo-level shared contracts are not touched.** `capability-freeze.schema.json`,
`marker-checkpoint.schema.json`, and `treatment-record.schema.json` under
`tests/speckit-pro/layer6-efficiency/contracts/` are byte-identical across both
worktrees. `treatment_disposition`, `disposition_reasons`, and `rawTokenVector`
are read from them and never extended. A unilateral addition would validate on one
platform and fail on the other.

## Verification

| Gate | Command |
|---|---|
| Full deterministic suite | `python3 tests/speckit-pro/run-all.py` |
| Plugin structure | `python3 tests/speckit-pro/run-all.py --layer 1` |
| Runtime and script safety | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Generated-artifact refresh | `python3 scripts/refresh-release-artifacts.py` |
| Plugin-shaped resolution | `quickstart.md` section 6 |

Completion bar: the 3251 baseline plus the new tests, green, zero live calls,
payload boundary clean (SC-019).

**Pre-change baseline, measured at Setup.** Run on this branch before the first
CAR-003 implementation edit, `python3 tests/speckit-pro/run-all.py` reported
**3251/3251 passed** — Layer 1 1428, Layer 4 1637, Layer 5 186 — at exit 0 with
zero failures, zero live model calls, and a wall clock of **4m41s**. That is the
zero-live-call starting point and the reference the FR-057 six-minute CI budget
and SC-019 are measured against, and it is the figure the slice-1 PR packet notes
carry. At the same point the branch was level with the default branch (nothing
behind), and the shared dual-platform smoke runner was byte-identical on the
default branch, this branch, and the Codex twin branch, so the FR-043 coordination
risk was still latent and this side could edit it first.

## PRD Traceability Of The Late Requirements

CAR-003 grew from 38 to 58 functional requirements through its clarify,
checklist, and analyze passes. An adversarial trace on 2026-07-26 checked every
one of the twenty late requirements against `docs/prd-claude-agent-routing.md`
looking for overfitting — a requirement written around a single observed
incident, or one constraining a situation that cannot arise.

**Seventeen are directly anchored, several near-verbatim.** FR-040 restates
AC-2.11's ordered `low`..`max` effort set; FR-051's environment contract is
AC-2.19's sentence; FR-052 is AC-2.9's pre-execution stratum membership; FR-053
is AC-2.15's guardrail field list. FR-039, FR-041, and FR-044 come from AC-2.2,
AC-2.3, and AC-2.21 on alias re-pointing and invalidation. FR-050, FR-054,
FR-055, and FR-056 come from AC-2.12, AC-2.15, AC-2.16, and AC-2.11 on
multiplicity, estimability, racing/futility, and campaign bounds. FR-058 is not
an addition to AC-2.5 but a precondition of it: "no worse on every dimension" is
undecidable without a declared direction.

**Three carry no direct acceptance-criterion anchor and are recorded here as
derived rather than free-standing:**

- **FR-046** (synthetic replay validation of the alias-re-point detector) is
  derived from FR-042 and FR-051 rather than from the PRD. The detector cannot
  be exercised live — an alias re-point cannot be summoned on demand — and the
  obvious alternative, setting an environment override to force divergence,
  would violate the very override-unset proof FR-051 requires. The requirement
  exists because those two constraints leave exactly one validation path.
- **FR-047** (scorer and adjudicator family exclusion) is a methodological
  control the PRD does not name. AC-2.20 governs scorer contracts, independent
  review, and blind adjudication, but not self-preference bias when a scorer
  shares a model family with the candidate it scores. It is implemented and
  blocking (`family_exclusion_holds=false` refuses the bundle) but currently
  **inert**: CAR-003 scores with declared deterministic rubric scorers, not
  model scorers, so no violation is reachable in today's configuration. It
  guards the model-scorer configuration the stated limitations describe as the
  intended end state. Kept deliberately; a reviewer is entitled to ask whether
  it belongs in AC-2.20 instead.
- **FR-057** (default suite stays cheap enough for an ordinary CI gate) is
  instrumentally required by SC-011 and SC-019 rather than by the PRD. Both
  criteria are only verifiable if the suite actually runs routinely, so an
  unbounded suite would leave them unverifiable in practice. Its zero-live-call
  half *is* anchored, in the PRD's scored-run discipline.

**One genuine defect was found, and it was the inverse of overfitting.** FR-042
(subscription is the supported scored path; no supported path may require an API
key) directly contradicted AC-2.19, which required scored campaigns to run under
a dedicated API-key-authenticated environment. The requirement is correct — the
product ships to operators on subscriptions, and qualifying routes under a
credential the product does not require would describe routes nobody gets — but
the spec had silently overridden its own source PRD. AC-2.19 is now amended to
match, following the same pattern AC-2.5 used for the Pareto change. The
deviation had already propagated: FR-004 refuses to let the models catalog
endpoint admit a tuple *because* that endpoint needs API-key authentication,
reasoning from a rule the PRD still contradicted.

## Known Gaps

- The exact numeric floors, margins, sample sizes, alpha, power, multiplicity
  corrections, racing rule, and attrition caps are deliberately analysis-plan
  *data*, not specification literals. They are calculated during the slice 3
  calibration pilot and frozen there. The twin leaves the same values open for the
  same reason.
- Scorer and adjudicator identities bind in the scorer registry before the
  calibration pilot, once the successor freeze has settled which evaluators exist.
- `reasoning_output_tokens` is excluded from Pareto dominance while the twin's
  frozen policy omits it. This is a stated limitation, not a claim the cost is
  absent, and every qualification claim reports the totals so the omission stays
  visible.
- Blinding is bounded, not complete. Identifier stripping cannot remove stylistic
  tells, so the residual is measured and reported rather than assumed away.
- Alias-re-point attribution is bounded by its enumerated cause set. Documented
  serving-infrastructure changes can alter behavior without changing model
  identity, so the enumeration cannot certify its own completeness.
- Equivalence between the two FR-008 proof branches is bounded to the frontmatter
  keys the plugin loader honors. A plugin-shipped agent silently ignores `hooks`,
  `mcpServers`, and `permissionMode` and inherits the parent session's permission
  mode, while the identical bytes in project or user agent scope honor all three,
  and a content hash is blind to that by construction. The materialization branch
  is therefore usable only for definitions declaring none of the three, and the
  loader scope is recorded rather than assumed.
- Effort admission is bounded by what configuration acceptance can establish. The
  admitting surface proves the pinned client did not reject an effort value, not
  that the effort took effect, and no independent effort-effect observation
  exists. The ladder is a claim about accepted configuration, not realized
  reasoning behavior.
- **Open cross-platform coordination item — score-bundle terminal-field
  constraints.** `score_disposition`, `failure_plane`, `failure_code`, and
  `invalidation_reason` are four independent closed enumerations in the mirrored
  `score-bundle` contract, with no cross-field constraint on either platform.
  Nothing schema-side stops a code being filed on a foreign plane, or a bundle
  declaring `score_disposition=accepted` while carrying a live failure plane and
  code — a failure recorded and then absorbed with no effect on the outcome.
  `spec.md` FR-034 now fixes both rules: plane is a total single-valued function
  of code, and `accepted` holds if and only if all three failure fields are
  `none`. The schema change is deliberately **not** applied here. The four
  enumerations are verified byte-identical to the twin's, so a one-sided
  constraint would reject on Claude what still validates on Codex, and FR-049
  fixes the rule that a mirror divergence must be a joint change landed on both
  platforms together. It is not slice-blocking — slice 2 owns the score-bundle
  contract and the constraint restricts only *combinations* of members already
  present on both sides — but it must be agreed with the twin before scoring
  runs. The same coordination applies to `authority_failures`, where FR-028's
  "required provenance is missing" has no dedicated member on either platform and
  is pinned to the existing `malformed_catalog` rather than widened unilaterally.
  **Tracked as roadmap spec CAR-012 / G56R-012.**
- **Cross-platform coordination item — a calibration decision binds the analysis
  plan it cannot have. Claude-side fix APPLIED; twin catch-up open.**
  `analysis-decision.schema.json` required `analysis_plan_binding` on every
  decision bundle, unconditionally. A `calibration_complete` bundle is produced
  before any analysis plan exists, so the calibration pilot satisfied the
  requirement by writing the calibration protocol binding into the plan-named
  field: the bundle claimed to bind an artifact it did not. This is the FR-037
  substitution one edge further out than FR-037 originally reached — it fixed the
  pair and the experiment policy, and the decision bundle is the next edge
  carrying the same binding. A provenance defect, not a live failure: the pilot
  ran, the digests sealed, and the bound protocol was recorded truthfully
  everywhere except in the field's name.

  **Resolved by contract version increment rather than in-place tightening.**
  `schema_version` moves from `const "1.0.0"` to `enum ["1.0.0", "1.1.0"]`.
  Version 1.0.0 keeps the legacy shape exactly, so the committed calibration
  evidence — which declared 1.0.0 and could not have done otherwise — stays
  conforming to the version it was sealed under; a frozen record is not
  retroactively invalid because the contract later improved. Version 1.1.0
  substitutes on `qualification_eligible`, keyed the same exhaustive way as
  FR-037's pair and policy branches. `build_decision_bundle` now derives which
  artifact to bind from the partition rather than from what the caller passed,
  and refuses binding both, neither, or the wrong one. This avoided the
  regeneration that would otherwise have been required: there is no
  rebuild-from-retention path, so re-emitting the evidence would have meant a new
  live run whose measurements would differ from the ones this plan's assumptions
  were derived from.

  **What remains open is the twin.** Its `analysis-decision` contract still pins
  `const "1.0.0"` and requires the plan binding unconditionally, so it carries the
  defect this side has closed — the same posture, and the same resolution
  direction, as the experiment-policy cycle before it. **Tracked as roadmap spec
  CAR-012 / G56R-012.** Found 2026-07-26 while verifying the twin's report that
  its own analysis-plan freeze path consumes a plan-bound calibration decision;
  the twin is addressing its side through a schema-governed calibration-completion
  artifact.
- **Open cross-platform coordination item — the experiment-policy binding
  cycle.** FR-037 resolves the calibration circular dependency at the comparison-pair
  level, and this plan's `experiment-assignment` schema enforces it. The cycle
  survived one edge away — every assignment binds an experiment policy, and an
  experiment policy requiring `analysis_plan_binding` unconditionally would put a
  calibration pair back in transitive need of the plan that only exists after
  calibration completes. **The Claude-side fix is applied.**
  `contracts/experiment-policy.schema.json` drops `analysis_plan_binding` from the
  unconditional `required` list and gates both bindings through a paired `allOf`
  keyed on `partition.qualification_eligible`: `true` requires
  `analysis_plan_binding` and forbids `calibration_protocol_binding`, `false`
  requires the protocol and forbids the plan. Keying on `qualification_eligible`
  rather than `partition_type` is what makes the two branches exhaustive.
  **CLOSED 2026-07-25 — the twin is now in line.** G56R-003 landed the matching
  fix in `06a77dd3` on PR #386: its Phase-1 contract drops the unconditional
  requirement and gates both bindings through an exhaustive `if/then/else` keyed on
  `partition.qualification_eligible`, and its runtime harness contract takes the
  calibration-only resolution — its partition binding pins
  `qualification_eligible` to `const: false`, so every policy that schema admits is
  a calibration policy and the plan binding is simply replaced by the protocol
  binding at both the policy and assignment-pair levels. The twin also added a
  `calibration-protocol.schema.json` at each layer, carrying no margins, sample
  sizes, or terminal thresholds. Re-verified here against the twin's own contract
  validator across seven cases, including an ineligible policy binding the analysis
  plan — the original cycle — which is now rejected as a prohibited shape.
  Resolution went the direction FR-049 requires: the twin was brought into line
  rather than this side reverted, because reverting would have reintroduced a
  defect to preserve symmetry with a defect.

  One ordering note for the record: this side's calibration pilot ran before the
  twin's fix landed. That is harmless — the pilot validates against the CAR
  contract, which was already correct, and calibration outcomes are never pooled
  across platforms — but the precondition as originally written ("the twin-side
  change must land before that pilot runs") was not met in that order.

- **Open cross-platform coordination item — no `invalidation_reason` member for an
  analysis-plan or budget change.** FR-056 forbids relaxing a budget ceiling or
  guardrail threshold for a partition whose outcomes have been observed, and
  requires a changed threshold to produce a new versioned analysis plan with a new
  id and digest whose outcomes are never pooled with the superseded plan's. That
  non-pooling is enforced purely through `{id, digest}` binding identity, because
  the closed `invalidation_reason` set in the mirrored `score-bundle` contract
  carries no `analysis_plan_changed` or `budget_changed` member and is closed under
  `additionalProperties: false`. Binding identity is sufficient to *detect* the
  change, but the invalidation itself stays unnamed, so a reviewer reading a
  superseded bundle sees no recorded reason for its exclusion. Adding the member is
  a joint cross-platform change under the FR-049 rule and is deliberately not made
  unilaterally. Tracked as `checklists/performance.md` CHK051 and as roadmap spec
  **CAR-012 / G56R-012**. Not slice-blocking.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

No violations. Table intentionally empty.

## Rollback

Every artifact CAR-003 produces is additive and versioned. Rolling back a slice
means reverting its commits; no CAR-002 record is mutated, so no historical
evidence needs repair. There is no feature flag, because nothing CAR-003 builds
runs on a default path: the collector and the calibration pilot are operator-only
commands, and the rest is validated by the deterministic suite. Slice 1's shipped
module is inert until called, so reverting it needs only the generated-artifact
refresh re-run against the reverted source.

---

## Reviewability Budget (governing figures)

These are the binding per-review-unit numbers — the largest single slice, which is
Slice 1 — because the split decision above defines the review units and the gate
governs a review unit. The whole-feature figures are in the derivation above.

- **Primary surface**: harness/adapter
- **Projected reviewable LOC**: 735
- **Projected production files**: 1
- **Projected total files**: 23
- **Budget result**: warn, pass, zero blockers. LOC 735 is over the 400 warn
  threshold and under the 800 block threshold. Total changed paths 23 is over the
  15 warn threshold and under the 25 block threshold. Production files 1 is under
  both. One primary review surface.
- **Split decision**: three ordered slices, Work Package A intact as the first.

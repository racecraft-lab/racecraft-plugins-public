# SpecKit Workflow: CAR-005 — Model Availability, Fallback, and Recovery Simulation

**Template Version**: 1.0.0
**Created**: 2026-07-29
**Purpose**: Executable workflow for CAR-005. Phase prompts below are populated
from the technical roadmap scope and the grill-me design concept; the autopilot
consumes them phase by phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/CAR-005-design-concept.md
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

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 35 FRs, 2 user stories, 18 acceptance scenarios, 12 success criteria, 6 edge cases. G1 pass. 3 clarification markers → Clarify runs. Parity premise corrected mid-phase. |
| Clarify | `/speckit-clarify` | 🔄 In Progress | 2 sessions + 3 real markers to resolve |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
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
| II. Cross-Platform Runtime & Script Safety | Repository tooling stays on Python 3.11+ standard library; no new Bash or `jq` dependency | Review imports in new `lib/` and `unit/` files |
| IV. Test Coverage Before Merge | Every new schema, simulator path, and fixture case covered by the repository suite | `python3 tests/speckit-pro/run-all.py --layer 1` while iterating; full suite per `tests/speckit-pro/suite-manifest.json` before PR |
| VI. KISS, Simplicity & YAGNI | Simulator proves only the mandated scenario semantics; no speculative resolver features beyond the roadmap scope | Code review against the design concept's Non-goals |

**Constitution Check:** ✅ (verified at scaffold — the spec surface is repository-only validation; no plugin runtime, payload, or shipped-default change)

### Phase 0 Prerequisites Evidence (autopilot, 2026-07-29)

| Check | Result |
|-------|--------|
| `check-prerequisites` | `all_pass: true` — SpecKit CLI 0.11.8, project initialized, constitution present, all commands installed, workflow file found, `is_worktree: true` |
| Branch | `car-005-availability-fallback-recovery` (verified by `git rev-parse --abbrev-ref HEAD`). The helper reports `branch: ""` / `on_feature_branch: false` because the branch is intentionally non-numeric; `.specify/feature.json` pins `specs/car-005-availability-fallback-recovery`, so `ON_FEATURE_BRANCH` is treated as **true** and no feature branch is created. |
| `detect-commands` | `stack: unknown`, all commands `N/A`. PROJECT_COMMANDS taken from the constitution Quality Gates: structural `python3 tests/speckit-pro/run-all.py --layer 1`, script-safety `--layer 4`, full `python3 tests/speckit-pro/run-all.py`. No BUILD/TYPECHECK/LINT gate exists in this repository. |
| `detect-presets` | `speckit-pro-reviewability` v1.0.0 — overrides spec/plan/tasks templates; all three `specify preset resolve` calls land on the preset. |
| `resolve-confidence-mode` | `advisory` → `CONFIDENCE_GATE_MODE=advisory` for G6.5 (no `--strict`/`--advisory` in argv, no local config file). |
| Settings | No `.claude/speckit-pro.local.md` — defaults apply (`gate-failure: stop`). |
| `PROJECT_IMPLEMENTATION_AGENT` | None detected (`.claude/agents/` holds only `plugin-release-auditor.md` and `speckit-skill-reviewer.md`, neither an implementation agent) → fallback `speckit-pro:phase-executor`; test-tree tasks route to `speckit-pro:implement-executor`. |
| `AGENT_TEAMS_AVAILABLE` | `false` (no `TeamCreate` in the session surface) → `[P]` runs dispatch as batched background subagents in one message. |
| **G0 constitution gate** | ✅ **PASS** — `python3 tests/speckit-pro/run-all.py` → **5345/5345** (L1 1428/1428, L4 3731/3731, L5 186/186), toolchain preflight ok. Baseline captured before any phase work. |
| Archive Sweep | Zero candidates. `specs/*` contains only `car-005-availability-fallback-recovery`, which is `--current-target` and excluded. No files mutated. CAR-004 and G56R-004 already archived. |
| Tier-2 PROCESS relocation | Suppressed — the only candidate is named by `.specify/feature.json` (`frozen/in-flight`) and already carries `structureVersion: 1`. `relocate-process-artifacts` is deferred and was not invoked. |

**Phase 0 Doctor Health Check (`speckit-utils`): 5 PASS / 2 WARN / 0 FAIL.**

| Area | Result |
|------|--------|
| Templates | PASS — 5/5 present and non-empty in `.specify/templates/` |
| Python runner | PASS — all 6 required files present in `speckit-pro/speckit_pro_runner/`; manifest parses |
| Constitution | PASS — `.specify/memory/constitution.md`, 996 words |
| Agent config | WARN — `.claude/` exists but `.claude/commands/` is absent, so 0 `speckit.*.md` command files are registered. **Expected, not broken:** this project uses the skills-based invocation model (27 `speckit-*` skills under `.claude/skills/`), which is the documented v0.8.13 slash-command→skills migration. |
| Features | WARN — `spec ✓ plan ✗ tasks ✗ (needs plan)`. Expected at this point in the run; Plan is Phase 3. |
| Non-numeric branch | Informational, resolves correctly — `.specify/feature.json` pins the feature directory and the doctor observed no drift or misresolution. |
| Extensions | 7 registered and enabled. Observation: `.specify/extensions/agent-context/` exists on disk with a config file but has **no entry in `.specify/extensions/.registry`** — unscored, recorded for follow-up. |

**Skill-name resolution (load-bearing for the post-implementation tasks):** the
registered names use dashes, not dots, and drop the `speckit.` prefix —
`speckit-speckit-utils-doctor` resolves; `speckit.speckit-utils.doctor` does **not**.
The post-implementation `verify`, `verify-tasks`, and `retrospective` steps must use
the dash form (`speckit-verify-run`-style) rather than the dotted command IDs printed
in `.specify/extensions/.registry`.

**Extension hook decisions (all 8 events read from `.specify/extensions.yml`):**

| Hook | Decision |
|------|----------|
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIPPED** — would create a feature branch. The worktree branch already exists and is correct; creating another would break the run. Documented per hook rule 2. |
| `before_specify` → `speckit.archive.run` (`optional: true`) | **Satisfied** by the Step -1 Archive Sweep above. |
| `before_*` → `speckit.git.commit` (clarify/plan/tasks/checklist/analyze/implement) | **Accepted** — the autopilot's own per-phase checkpoint commits fulfil these; not re-run separately. |
| `after_specify` → `speckit.speckit-utils.doctor` | **Accepted** — run as the Phase 0 doctor health check. |
| `after_plan` → `speckit.speckit-utils.validate` | **Accepted** — run at the G3 boundary. |
| `after_implement` → `verify`, `verify-tasks`, `retrospective`, `git.commit` | **Accepted** — mapped to the canonical post-implementation tasks. |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | CAR-005 |
| **Name** | Model Availability, Fallback, and Recovery Simulation |
| **Branch** | `car-005-availability-fallback-recovery` |
| **Dependencies** | CAR-004 (merged, PR #401) — frozen control registry, comparison rule, fixtures, validators |
| **Enables** | CAR-006 (route-policy manifest, materializer, preflight) — it re-proves its framework against this spec's fixture policies |
| **Priority** | P1 |

### Success Criteria Summary

From the technical roadmap scope and the design concept:

- [ ] An executable reference simulator (`lib/claude_route_fallback.py`, test-tree only) resolves fixture route policies against synthetic environment snapshots and emits resolution reports (Q1)
- [ ] The scenario corpus covers every mandated family: preferred model absent (including a `fable`-unavailable case), effort unsupported, probe unavailable, exact-invocation probe success and failure, alias re-pointing, platform route change, unqualified `CLAUDE_CODE_SUBAGENT_MODEL` override, helper-unavailable, no-safe-route, and retry exhaustion
- [ ] Two closed enums: the five **Claude**-roadmap-pinned resolution codes verbatim, plus the policy-violation enum (`fallback_loop`, `unqualified_adjacent_model`, `generic_agent_substitution`, `silent_inherit_materialization`, `unqualified_override`); a structural parity test asserts exact set equality with the Claude roadmap's five codes AND pins the recorded cross-platform divergence on the third member (Q2, Q3, as corrected by the 2026-07-29 design-concept revision note)
- [ ] Rejection and remediation entries mirror the installed runner diagnostics envelope — `{code, message, severity, source, details, remediation: {summary, actions[]}}` (Q4)
- [ ] Alias re-pointing / platform route change code as `preferred_model_unavailable` with a machine-readable sub-reason in `details` (Q11)
- [ ] The override scenario reports the override as the effective dispatch tuple with a loud `unqualified_override` diagnostic, claims-exclusion marking, and the qualified would-have-been resolution (Q12)
- [ ] No-safe-route is report-only: unresolved agent, attempted routes, rejection reasons, and remediation (including previous-plugin-release rollback guidance) — never a mutation of shipped agent files
- [ ] Helper-unavailable: the helper is simply not consulted; the validated no-helper path continues without failing required-agent resolution
- [ ] Probe/retry/fan-out bounds are fixture-declared budget fields with schema maxima; exhaustion proven with minimal budgets; reports record actual attempt counts (Q7)
- [ ] Deterministic replay proven by pinned expected reports: run-twice byte-identity AND byte-identity to the pinned report under canonical JSON serialization (Q8)
- [ ] Delivered as 2 vertical slices in a gh-stack stacked-PR chain (Q10 + user directive)

### Reviewability Budget (setup gate, 2026-07-29)

Recorded from the authoritative `reviewability-gate` setup run against the
CAR-005 roadmap section: **pass** — reviewable LOC 257, production files 0,
total files 10, primary surface `harness/fixtures` (1). Estimator
(`estimate-spec-size`, roadmap signal convention): 770 LOC, 2 slices, status
**warn** — the estimator and the authored budget disagree; the operator chose
the estimator-recommended **split into 2 vertical slices** (Q10): slice 1 =
resolution-failure semantics (five reason codes, snapshot projection, replay
pinning); slice 2 = structural rejections, override/helper paths, retry
exhaustion. Delivery directive: with more than one PR, the slice PRs are
managed as a **gh-stack stacked-PR chain** (slice 2 stacks on slice 1).

#### Adjudicating the 257-vs-770 disagreement (autopilot Phase 0, evidence added)

The disagreement is **not** between two measurements. Setup-mode
`reviewability-gate` performs no measurement at all — it regex-scrapes numbers a
human already typed into the target document:
`loc = last_number(text, r"(?:projected reviewable loc|reviewable loc)[^0-9]{0,40}([0-9]+)")`
at `speckit-pro/speckit_pro_runner/helpers/read_only.py:850`, with sibling scrapes
for production files and total files on lines 851-852. Its `pass` / `257` verdict
is a restatement of the roadmap's own authored line
(`docs/ai/specs/claude-agent-routing-technical-roadmap.md:516`) and carries no
independent evidentiary weight. That same roadmap entry says "re-estimate at
scaffold" (line 518).

`estimate-spec-size` computes 770 from structured signals. Measured sizes of the
closest committed precedents corroborate the larger figure:

| Precedent | Lines |
|-----------|-------|
| `lib/claude_treatment_runner.py` | 705 |
| `lib/claude_control_comparison.py` | 764 |
| `lib/claude_policy_controls.py` | 2805 |
| `unit/test-control-comparison-dominance.py` | 1459 |
| `unit/test-policy-control-contracts.py` | 5544 |
| `contracts-claude/control-comparison.schema.json` | 308 |
| `contracts-claude/policy-control-registry.schema.json` | 685 |
| `fixtures-controls/control-replay.json` | 660 |

**Conclusion, corrected at Clarify Session 1.** An earlier draft of this section
claimed a single undivided slice "would breach the 800 block threshold on logic
alone". **That was wrong, and the correction matters:** no gate in this repository
measures this surface at all. `estimate-reviewable-loc` computes
`projected = production_files × 40` (`read_only.py:926`), so a 0-production-file
feature projects 0 and returns `pass`; the PR-time packet gate thresholds the same
author-declared figure (`pr_emission.py:589-619`). One slice would pass every gate.
The sibling precedent proves it empirically: **CAR-004** — same primary surface, 0
production files, declared 250 reviewable LOC, status ok — shipped roughly **11,600
artifact lines in a single PR (#401)**. The declared figure systematically excludes
fixture JSON, platform-scoped schemas, test-library modules, and unit tests.

So the split is **elected, not gate-forced**, and its justification is review burden
plus independent slice value — not a ceiling breach. Design-concept Open Question 2
("if plan-time re-estimation lands near the authored 257 the maintainer may revisit
whether 2 slices remain warranted") resolves as: **re-estimation cannot settle this
either way**, because every automated signal reads 0 for this surface. Keeping the
split is the operator's ratified judgement, and only an operator decision can change
it. Recorded so no later phase mistakes a `pass` from a blind gate for evidence
against the split.

Two further corrections to the earlier draft: `estimate-spec-size` re-run on the
spec's **real** signals (2 user stories, 10 files, 35 FRs) returns **975 / 3 slices**,
not 770 / 2 — the scoping figure came from coarser signals. And `greenfield` is
**false** here, because `suite-manifest.json` is modified rather than created
(`read_only.py:922`), so thresholds stay 400/800 rather than 600/1200.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/car-005-availability-fallback-recovery/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: CAR-005 Model Availability, Fallback, and Recovery Simulation

### Problem Statement

CAR-006 will implement the real route-policy manifest, materializer, and
session preflight. If its recovery semantics are designed while the framework
is being built, failure behavior becomes whatever the implementation happens
to do. CAR-005 proves bounded resolution and recovery semantics synthetically
first: an executable reference simulator plus a deterministic fixture corpus
that pins, byte-for-byte, how resolution must behave when a preferred model is
absent, an effort is unsupported, a probe is unavailable or fails, an alias
re-points, the platform changes a route, an environment carries an unqualified
override, the optional helper is unavailable, or no safe route exists. CAR-006
then re-proves its production resolver against this same corpus — the fixtures
land already tested, and the framework inherits its failure semantics instead
of inventing them.

### Users

- CAR-006 (primary consumer): re-proves the route-policy framework against the
  fixture policies, adopts the resolution-report contract, reason-code enums,
  snapshot projection, and declared-budget fields.
- CAR-007 through CAR-010: inherit the proven rejection semantics (no fallback
  loops, no unqualified adjacent models, no generic-agent substitution, no
  silent inherit) for cohort qualification.
- G56R-005 (Codex twin, not yet scaffolded): mirrors the structural template —
  schemas, enums, corpus organization — set by this first-mover spec.
- Operators: read the no-safe-route report's remediation (including
  previous-plugin-release rollback guidance) when a real preflight later
  reports an unresolvable agent.

### User Stories

Two stories, one per accepted vertical slice (Q10):

- [US1] Resolution-failure semantics: as the routing program, prove that route
  resolution against a synthetic environment snapshot walks preferred route
  then ordered fallbacks, emits the five pinned reason codes with
  machine-readable sub-reasons, and replays byte-identically against pinned
  expected reports.
- [US2] Structural rejection and recovery semantics: as the routing program,
  prove that structurally defective policies (loops, unqualified adjacent
  models, generic-agent substitution, silent inherit) are rejected with their
  own closed violation codes, that unqualified overrides and
  helper-unavailable environments behave as contracted, and that declared
  probe/retry/fan-out budgets exhaust deterministically with report-only
  no-safe-route output.

### Design decisions to encode (from the design concept Q&A log)

- The thing-under-test is an executable reference simulator in
  tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py — a pure
  function over (policy fixture, synthetic snapshot, overrides, declared
  budgets) returning a resolution report; the fixtures are the durable
  contract CAR-006 re-proves against (Q1).
- Two closed enums: the roadmap's five resolution codes verbatim
  (preferred_model_unavailable, effort_unsupported,
  capability_probe_unavailable, treatment_probe_failed, no_safe_route) plus a
  CAR-005-owned policy-violation enum (fallback_loop,
  unqualified_adjacent_model, generic_agent_substitution,
  silent_inherit_materialization, unqualified_override) (Q2, Q12).
- Schemas land platform-scoped in
  tests/speckit-pro/layer6-efficiency/contracts-claude/; nothing is added to
  the shared byte-identical contracts/ directory; a structural parity test
  asserts the resolution enum matches the five codes both roadmaps pin (Q3).
- Every rejection/remediation entry mirrors the installed runner diagnostics
  envelope: {code, message, severity, source, details,
  remediation: {summary, actions[]}} (Q4).
- Fixture policies name a small synthetic cast by role class
  (fixture-required-executor, fixture-bounded-analyst,
  fixture-optional-helper); never the twelve real shipped agent names (Q5).
- The simulator input is a minimal purpose-built snapshot projection:
  available model IDs, alias-to-resolved bindings, per-model supported
  efforts, probe availability, exact-invocation probe outcomes — not the full
  CAR-002 capture-record shape; defining this projection IS the CAR-006
  preflight input contract (Q6).
- Probe/retry/fan-out bounds are fixture-declared budget fields with
  schema-enforced maxima; the simulator treats them as hard caps and reports
  actual attempt counts (Q7).
- Deterministic replay: each corpus case pins its full expected resolution
  report; tests assert run-twice byte-identity and byte-identity to the
  pinned report under canonical JSON serialization; no wall-clock or
  randomness inputs (Q8).
- One self-contained scenario corpus,
  fixtures-fallback/fallback-scenario-corpus.json, where each case bundles
  {policy, synthetic snapshot, overrides, declared budgets, expected report}
  (Q9).
- Alias re-pointing and platform route change map to
  preferred_model_unavailable with a machine-readable sub-reason
  (alias_repointed | platform_route_changed | model_absent) in the envelope's
  details object; the five-code enum is not extended (Q11).
- The unqualified CLAUDE_CODE_SUBAGENT_MODEL scenario simulates documented
  runtime behavior honestly: the override wins as the effective dispatch
  tuple, the report emits a loud unqualified_override diagnostic, marks the
  environment excluded from release claims, and still records the qualified
  would-have-been resolution (Q12).
- No-safe-route is report-only (unresolved agent, attempted routes, rejection
  reasons, remediation including previous-plugin-release rollback); shipped
  agent files are never mutated. Helper-unavailable means the helper is not
  consulted and the validated no-helper path continues without failing
  required-agent resolution (roadmap scope).
- Delivery: 2 vertical slices as a gh-stack stacked-PR chain — slice 2 stacks
  on slice 1 (Q10 + recorded user directive).

### Constraints

- Python 3.11+ standard library only; repository-only surface (no plugin
  runtime, payload, or shipped-default change; 0 production files).
- Deterministic everything: canonical JSON serialization, no timestamps, no
  randomness in simulator output.
- Durable file names (never coupled to the spec ID) for scripts and tests.
- Additive only: no edit to any frozen CAR-002/003/004 schema or fixture; no
  member added to the shared byte-identical contracts/ directory.

### Out of Scope

- The real resolver, manifest schema, materializer, preflight doctor
  operation, and SessionStart warning (CAR-006).
- Real route qualification and final preferred/fallback selection
  (CAR-007 through CAR-010).
- Live UAT, live probing, or any live dispatch; production checkpoint/resume
  scheduling.
- Real shipped agent names in fixtures; reuse of the full CAR-002
  runtime-capability-snapshot shape as simulator input.
- Any Codex-side change (G56R-005 mirrors later; parity promotion to shared
  contracts/ is a deliberate future joint change).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 35 (FR-001…FR-033, with FR-017a/FR-017b) |
| User Stories | 2 — US1 resolution-failure semantics (P1), US2 structural rejection + recovery (P2) |
| Acceptance Criteria | 18 acceptance scenarios (9 per story) + 12 success criteria (SC-001…SC-012) + 6 edge cases |
| Preset template | `speckit-pro-reviewability` v1.0.0 spec-template used — required the Reviewability Notes, Reviewability Budget, and PR Review Packet Requirements sections that the core template lacks |
| Clarification markers | 3 (FR-006 sub-reason enum membership; FR-017 divergence disposition; FR-033 file-level slice-seam allocation) |

**G1 gate:** ✅ PASS — `validate-gate G1` returned `pass: true`, `spec.md exists`.

**⚠️ Marker-gate blind spot (recorded, deliberately NOT fixed here).** `validate-gate`
reported `markers: 0` and `count-markers` reported `clarifications: 0`, but the spec
carries **3 real markers** at `spec.md:193`, `spec.md:257`, and `spec.md:319`. Cause: the
runner counts the literal regex `\[NEEDS CLARIFICATION\]` — bare brackets with nothing
between — at `speckit-pro/speckit_pro_runner/helpers/read_only.py:710,743,744,752,769,775,781`,
while the project's own spec templates document and demonstrate the
`[NEEDS CLARIFICATION: <question>]` form
(`.specify/templates/spec-template.md:98-99` and the identical preset template lines).
Every correctly-formed marker is therefore invisible to the G1 and G2 marker gates.

Handling: the authoritative marker count for this run is the orchestrator's own
`grep -c "NEEDS CLARIFICATION"`, not the helper. The spec was **not** rewritten to use
bare markers — that would delete the question text Clarify consumes. Fixing the regex
touches plugin production source, which CAR-005 forbids (FR-030, 0 production files), so
it is reported as follow-up work outside this spec's diff.

### Files Generated

- [x] `specs/car-005-availability-fallback-recovery/spec.md`

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Resolution walks preferred then ordered fallbacks` |
| `[FR-001]` | Functional requirement | `[FR-001] Resolution enum carries exactly the five pinned codes` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Sub-reason enum membership [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No case covers fan-out exhaustion` |

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: Slice seam and stacked delivery

Seeded from design-concept Open Questions 1 and 2.

```text
/speckit-clarify Focus on the two-slice seam: exactly which schemas, corpus
cases, simulator functions, and tests land in slice 1 (resolution-failure
semantics) versus slice 2 (structural rejections, override/helper paths,
exhaustion); how slice 2 stacks on slice 1's schemas in the gh-stack chain so
slice 1 is independently landable and releasable; and whether the plan-phase
LOC re-estimate still supports two slices or the operator should be asked to
ratify a single-slice fallback (the setup estimator said warn/770/2 while the
authored roadmap budget said ok/257/1).
```

#### Session 2: Enum closure and report field totality

Seeded from design-concept Open Question 4 and the report contract.

```text
/speckit-clarify Focus on closed-set membership: the exact details sub-reason
enum for preferred_model_unavailable (alias_repointed |
platform_route_changed | model_absent — is the set exhaustive for the
mandated scenarios?); whether the policy-violation enum needs any member
beyond the five decided at scoping; the closed set of remediation action
strings (including the previous-plugin-release rollback wording) so pinned
reports stay byte-stable; and which report fields are required versus
optional for a successful resolution versus a no-safe-route outcome.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Slice seam / stacked delivery | 5 | All 5 resolved. FR-033's marker cleared. Added FR-033a (file-level allocation table), FR-033b (slice-2 edits must be additive; no slice-1 churn), FR-033c (single corpus preserved), FR-033d (single simulator module). FR-027 retagged US2→US1. Split confirmed on independent evidence. |
| 2 | Enum closure / report totality | | |

#### Session 1 — resolution detail

Executor dispatch note, recorded for honesty: the `clarify-executor` subagents did
not deliver a question set (they completed and went idle without relaying output —
see the delivery caveat at the end of this section). Rather than stall the run, the
**parent orchestrator resolved Session 1 directly**, which is what the protocol
assigns to the parent in any case — the executor's role is only to *prepare* the
question set; answering and applying edits is the parent's job. The parent's
evidence base was its own: the full spec, the design concept including the new
revision note, both roadmaps, the `contracts-claude/` and `lib/` conventions, the
suite-manifest layer structure, and directly measured precedent file sizes.

| # | Question | Resolution | Applied as |
|---|----------|-----------|-----------|
| 1 | Exact file-level slice allocation | Slice 1 creates all seven files; slice 2 extends three of them and creates none | FR-033a table |
| 2 | Schema partitioning across the seam | 3 schema files (matching the one-schema-per-conceptual-document convention); the policy-violation enum is added in slice 2 by extending the report schema's `$defs` and widening the diagnostic `code`, so slice 1 never ships an enum it does not validate against | FR-033a rows, FR-027 |
| 3 | Simulator module partitioning | One module, created in slice 1 and extended in slice 2. Structural validation is a pre-pass of the same capability, not a second capability; splitting it would be a single-use abstraction (constitution VI) | FR-033d |
| 4 | Corpus partitioning — the real Q9/Q10 tension | **Q9 wins; Q10's seam does not require file separation.** One corpus file. Slice 2 appends to the end of `cases[]`. Because a stacked PR diffs against its base branch, appended cases read as pure additions and slice 1 never changes. "No slice-1 churn" means slice 2 must not force slice 1 to be rewritten before merging — not that slice 2 may never touch a slice-1 file | FR-033b, FR-033c |
| 5 | Are two slices still warranted? | **Yes.** The setup gate's 257 is a scraped authored number, not a measurement (`read_only.py:850`); the estimator's computed 770 is corroborated by measured precedents. An independent per-artifact projection (~350 schemas + ~550 simulator + ~900 corpus + ~700 unit suite) puts a single undivided slice past the 800 block threshold on logic alone | spec.md Reviewability Budget |

Items 2 and 4 resolve genuinely contestable trade-offs, so both were sent to a
category-routed consensus round rather than accepted on the parent's reasoning
alone — item 4 to `[spec]` (which project decision yields) and item 2 to
`[codebase]` (what the schema convention shows).

**Subagent delivery caveat (affects how this run is executed, not its outcome).**
Subagents in this session run detached, and delivery depends on **whether the
dispatch passed a `name`**:

- **Unnamed** `Agent(...)` dispatches deliver correctly — the orchestrator receives
  the agent's full final output in the completion notification. Clarify Session 1's
  executor was dispatched this way and returned a complete, well-cited question set.
- **Named** dispatches do **not** deliver. The agent completes, emits an
  `idle_notification`, and its final text is never returned. Four named agents
  (Specify, two Clarify executors, and the Session 1 `[spec]` consensus analyst) all
  went idle without delivering.

**Correction to the orchestrator's first diagnosis.** The orchestrator initially
concluded that named agents fail because they omit a required
`SendMessage(to: "main")` call, and added that instruction to subsequent prompts. That
diagnosis was wrong: the Round 1 `[codebase]` analyst reported that **no `SendMessage`
tool exists in the subagent environment at all** — `select:SendMessage` returns no
match there. Subagents therefore *cannot* message the orchestrator, and the added
instruction was impossible to follow. The real mechanism is simply that an unnamed
dispatch's final output is returned by the harness while a named dispatch's is not.
The `doctor` agent's report arrived because that agent was reached through a different
path, not because it obeyed an instruction the others ignored.

Nothing was lost substantively: the Specify agent's file output (`spec.md`) landed
correctly and was validated directly by the parent, and the Session 1 `[spec]`
analyst's confirmation was redundant against an executor answer already carrying six
independently cited reasons. But real wall-clock was spent waiting on reports that
were never going to arrive.

**Rule adopted for the remainder of this run: dispatch every subagent WITHOUT a
`name`.** This is a session-level behaviour that the skill's prompt templates do not
account for; it is worth carrying into future autopilot runs.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/car-005-availability-fallback-recovery/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack

- Language: Python 3.11+ standard library only (constitution principle II)
- Surface: repository-only validation under
  tests/speckit-pro/layer6-efficiency/ and tests/speckit-pro/unit/
- Contracts: JSON Schema documents in
  tests/speckit-pro/layer6-efficiency/contracts-claude/ (draft 2020-12 and
  $id convention matching the CAR-003/004 schemas they sit beside)
- Simulator: tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py
  following the claude_*.py naming convention
- Fixtures: tests/speckit-pro/layer6-efficiency/fixtures-fallback/ (new
  directory, named per the existing fixtures-<topic> pattern)
- Testing: unit tests in tests/speckit-pro/unit/ registered through
  tests/speckit-pro/suite-manifest.json; layer runner
  python3 tests/speckit-pro/run-all.py

## Constraints

- 0 production files: nothing under speckit-pro/ changes; the simulator is an
  executable specification living in the test tree (design concept Q1).
- Additive only: no edit to frozen CAR-002/003/004 schemas or fixtures; no
  member added to the shared byte-identical contracts/ directory (Q3; the
  joint-change rule from the CAR-012 record).
- Durable names: no script or test filename coupled to the CAR-005 spec ID.
- Deterministic: canonical JSON serialization for reports; no timestamps,
  randomness, or environment-dependent output anywhere in the simulator.
- Two-slice delivery: the plan's file operations must partition cleanly along
  the Q10 seam so slice 1 lands independently and slice 2 stacks on it
  (gh-stack chain per the recorded user directive).

## Architecture Notes

- Follow the established schema + lib + fixture + unit-test pattern: a
  route-policy fixture schema, a snapshot-projection schema, and a
  resolution-report schema in contracts-claude/; the simulator in lib/; the
  self-contained scenario corpus in fixtures-fallback/; coverage in unit/.
- The resolution report's rejection entries reuse the installed runner
  diagnostics envelope shape ({code, message, severity, source, details,
  remediation: {summary, actions[]}}) so CAR-006's doctor operation emits it
  natively (Q4).
- Resolution algorithm under test: walk preferred route then ordered
  fallbacks; each candidate checks model availability, alias binding
  stability, effort support, and probe outcomes against the synthetic
  snapshot; fallback changes only model and effort for the same named agent;
  structural validation (loop/adjacent/substitution/inherit) rejects the
  policy before any route walk (Q2).
- Budgets (probe attempts, retries, fan-out) are fixture-declared fields with
  schema maxima; the simulator enforces them as hard caps and reports actual
  counts; exhaustion cases use minimal budgets (Q7).
- Replay: each corpus case pins its expected report; the test asserts
  run-twice byte-identity and pinned-report byte-identity (Q8).
- The structural parity test reads the resolution enum from the committed
  schema and asserts (a) exact set equality with the five codes pinned in
  docs/ai/specs/claude-agent-routing-technical-roadmap.md (lines 527-529),
  failing on drift in either direction, and (b) the RECORDED cross-platform
  divergence against
  docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md (lines
  536-538): four members byte-identical, third member intentionally different
  (capability_probe_unavailable on Claude vs capability_discovery_unavailable
  on Codex), pinned as data so a silent change on either side fails. The
  roadmaps do NOT pin an identical five-code set — see the 2026-07-29 revision
  note in the design concept, which supersedes the original Q2/Q3 wording.
- Re-read docs/ai/specs/.process/CAR-005-design-concept.md for the rationale
  behind any decision the prompts compress.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (if needed) |
| `data-model.md` | ⏳ | Entities and types |
| `contracts/` | ⏳ | Fixture/snapshot/report contract specifications |
| `quickstart.md` | ⏳ | Developer onboarding |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Domain signals for this spec: JSON contract schemas, closed enums, and
byte-pinned golden reports (**data-integrity**); the entire subject matter is
failure paths, bounded retries, exhaustion, and recovery guidance
(**error-handling**); and the semantics simulated are model routing facts —
alias re-pointing, effort support, override env vars, probe outcomes
(**llm-integration**). UI, API-endpoint, streaming, and security domains do
not apply to a repository-only simulation surface with no live dispatch.

### Step 2: Run Enriched Checklist Prompts

#### 1. data-integrity Checklist

Why this domain: the spec's core outputs are closed enums, schema contracts,
and byte-pinned expected reports whose integrity CAR-006 depends on.

```text
/speckit-checklist data-integrity

Focus on CAR-005 Model Availability, Fallback, and Recovery Simulation requirements:
- Closed-enum discipline: both enums schema-closed (additionalProperties /
  enum constraints), the resolution enum exactly the five pinned codes, and
  the parity test failing on any drift in either direction.
- Corpus self-containment: every case carries policy, snapshot, overrides,
  budgets, and expected report with no cross-case references; case IDs unique
  and stable.
- Canonical serialization: the byte-identity rule is well-defined (key order,
  whitespace, unicode) and identical between the simulator and the pinning
  test.
- Pay special attention to: schema maxima on declared budgets — an
  out-of-range budget must fail schema validation, not silently clamp.
```

#### 2. error-handling Checklist

Why this domain: the spec exists to pin failure semantics — every scenario is
an error path with a contracted outcome.

```text
/speckit-checklist error-handling

Focus on CAR-005 Model Availability, Fallback, and Recovery Simulation requirements:
- Scenario totality: every mandated family (preferred absent incl.
  fable-unavailable, effort unsupported, probe unavailable, exact-invocation
  success AND failure, alias re-pointing, platform route change, unqualified
  override, helper-unavailable, no-safe-route, retry exhaustion) has at least
  one corpus case with a pinned report.
- Structural rejections fire before route walking; each maps to exactly one
  policy-violation code; no defect maps to prose only.
- Exhaustion semantics: which resolution code fires when each budget class
  (probe attempts, retries, fan-out) exhausts, and attempt counts in the
  report equal the declared budget.
- No-safe-route report completeness: unresolved agent, every attempted route
  with its rejection diagnostic, and remediation including the
  previous-plugin-release rollback action.
- Pay special attention to: helper-unavailable — the optional helper is not
  consulted (zero probe attempts recorded for it) and required-agent
  resolution still succeeds.
```

#### 3. llm-integration Checklist

Why this domain: the simulated facts are model routing semantics — aliases,
efforts, probes, and the subagent-model override — that must match documented
platform behavior.

```text
/speckit-checklist llm-integration

Focus on CAR-005 Model Availability, Fallback, and Recovery Simulation requirements:
- Route-tuple fidelity: a route is alias + qualified resolved model ID +
  explicit effort; an alias re-point invalidates the tuple
  (preferred_model_unavailable + alias_repointed sub-reason), never a silent
  re-qualification.
- Snapshot projection sufficiency: the minimal projection carries everything
  resolution consumes (model IDs, alias bindings, per-model efforts, probe
  availability, exact-invocation outcomes) and nothing it doesn't — this is
  CAR-006's preflight input contract.
- Override honesty: the simulated CLAUDE_CODE_SUBAGENT_MODEL behavior matches
  the documented runtime (override wins at dispatch); the report flags it
  loudly and excludes the environment from release claims while still
  recording the qualified would-have-been route.
- Pay special attention to: alignment with CAR-002's probed
  unavailable-model observation — an unavailable model is a preflight
  detection from the snapshot, never a simulated dispatch attempt.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | | | |
| error-handling | | | |
| llm-integration | | | |
| **Total** | | | |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/car-005-availability-fallback-recovery/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: schemas -> simulator core -> corpus cases -> replay
  pinning -> structural-rejection and override/helper paths -> exhaustion ->
  parity test -> suite-manifest registration
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story: US1 (slice 1, resolution-failure semantics) before
  US2 (slice 2, structural rejections + override/helper + exhaustion); TDD
  RED->GREEN pairs throughout

## Implementation Phases
1. Slice 1 foundation: route-policy, snapshot-projection, and
   resolution-report schemas + canonical-serialization helper
2. Slice 1 proof: simulator resolution walk, five-code semantics, sub-reason
   details, corpus cases for the resolution-failure families, pinned replay
   test
3. Slice 2 rejections: structural validation (loop, adjacent, substitution,
   inherit) + override and helper-unavailable cases with pinned reports
4. Slice 2 recovery: declared-budget exhaustion cases, no-safe-route report
   with rollback remediation, structural parity test, suite-manifest
   registration

## Constraints
- The slice seam is load-bearing: no US2 task may edit a US1 artifact in a
  way that would force slice-1 PR churn; slice 2 stacks on slice 1
  (gh-stack chain per the recorded user directive).
- Unit tests live in tests/speckit-pro/unit/ with durable (non-spec-ID)
  filenames; register in tests/speckit-pro/suite-manifest.json.
- Fixtures live under tests/speckit-pro/layer6-efficiency/fixtures-fallback/.
- Bound task generation by the design concept's Non-goals: no production
  resolver tasks, no real-agent-name fixtures, no shared contracts/ members,
  no live dispatch, no CAR-002/003/004 schema edits. Flag any task that would
  cross these boundaries.
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
**placeholder** until then — leave the cells blank during scoping. The classifier
emits one machine-readable decision; the SKILL is what writes it into this section
(the script never writes a file of its own). This route is recorded only here in the
workflow file — never in the spec map. It is read downstream by the layer-planner and
multi-PR emission work that builds on top of it; recording it now wires no PR creation
or branch splitting on its own.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

Scoping note: the operator has already ratified a 2-slice split (Q10) with
gh-stack stacked delivery. If the classifier route disagrees with `split-PR`,
surface the conflict to the operator instead of silently following either.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/car-005-availability-fallback-recovery
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — Python 3.11+ stdlib only, deterministic I/O,
   durable filenames, 0 production files
2. Coverage gaps — every FR, every mandated scenario family, and both user
   stories have tasks; every corpus case has a pinned expected report
3. Consistency between task file paths and the layer6 harness structure
   (contracts-claude/, lib/, fixtures-fallback/, unit/)
4. Design-concept drift — docs/ai/specs/.process/CAR-005-design-concept.md is
   the source of truth for scoping decisions; if spec.md, plan.md, or
   tasks.md contradicts it (two-enum taxonomy, five codes verbatim,
   diagnostics-envelope report shape, synthetic fixture-* names, minimal
   snapshot projection, fixture-declared budgets, byte-identical pinning,
   2-slice split with gh-stack delivery) the downstream artifact is wrong
   unless a dated revision note says otherwise
5. Verify no task adds a shared contracts/ member, edits a frozen
   CAR-002/003/004 schema, names a real shipped agent in fixtures, or
   introduces live dispatch
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
1. Run `python3 tests/speckit-pro/run-all.py --layer 1` and confirm green
   before making changes
2. Verify you are on `car-005-availability-fallback-recovery` (never main)
3. Re-read docs/ai/specs/.process/CAR-005-design-concept.md — decisions
   captured there but missing from tasks.md are gaps to surface before
   coding, not silently drop

### Implementation Notes
- Match the CAR-003/004 conventions in contracts-claude/ and lib/claude_*.py —
  schema style ($schema draft 2020-12, racecraft.dev $id), validator
  structure, error taxonomy discipline.
- Determinism is absolute: canonical JSON serialization everywhere a report
  is produced or compared; no timestamps, randomness, dict-order dependence,
  or environment-dependent output.
- Respect the slice seam while committing: slice-1 artifacts (schemas,
  simulator resolution walk, resolution-failure corpus + replay test) must
  not depend on slice-2 artifacts; the PR-emission step delivers two stacked
  PRs via gh-stack (slice 2 on slice 1).
- The smallest useful check while iterating is the affected unit test file;
  run the broader suite (per suite-manifest.json) before the PR.
- After any tracked .py change under tests/speckit-pro/, the generated docs
  reference is stale: run pnpm --dir docs-site reference:generate (deps
  already installed in this worktree) before calling the work done.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Slice 1: schemas + serialization | | | |
| 2 - Slice 1: simulator + corpus + replay | | | |
| 3 - Slice 2: rejections + override/helper | | | |
| 4 - Slice 2: exhaustion + parity + registration | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Full repository suite passes per `tests/speckit-pro/suite-manifest.json`
- [ ] New unit tests registered in the suite manifest
- [ ] Docs reference regenerated (`pnpm --dir docs-site reference:generate`; deps installed at scaffold) — new `.py` files under `tests/speckit-pro/` stale the generated `reference/tests.md`, and CI's validate-docs job runs `reference:check` against it
- [ ] No shared `contracts/` member added; no frozen CAR-002/003/004 schema modified (additive-only verified in the diff)
- [ ] Structural parity test proves exact set equality with the Claude roadmap's five pinned codes and pins the recorded third-member divergence against the Codex roadmap
- [ ] Two stacked slice PRs created via gh-stack (slice 2 stacks on slice 1); each PR title passes the release-readiness gate (`<type>(<lowercase-scope>): <plain English description>`) and each feat/fix PR body carries exactly one non-empty release-note fence
- [ ] PRs reviewed
- [ ] Merged to main branch

---

## Consensus Resolution Log

Category-routed two-layer resolution (see the autopilot consensus protocol). One
row per synthesizer result, in item-encounter order. Security-keyword scan on all
three Specify-phase clarification markers: **no security keywords present**, so no
mandatory human-review stop applies to them.

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | S1-Q4: one corpus file or two? (the Q9/Q10 conflict) | [spec] | 1 | executor high-confidence, analyst confirmation pending | **Q9 holds.** One corpus file; slice 2 appends at the tail of `cases[]` and alters nothing. The literal "slice 2 touches no slice-1 file" reading is unachievable and yields to append-only additivity. Applied to FR-015, FR-033b/c + design-concept revision note | clarify-executor; spec-context-analyst (Round 1, in flight) |
| 2 | Clarify | S1-Q2a: how many schema documents? | [codebase] | 1 | high-confidence | **3 separate documents**, capability-named, `car-005` `$id` scope. One-document-per-file is 11/11 in this directory; the two multi-shape files self-document a bundling rule (a `oneOf` over sibling record *variants*) that CAR-005's three distinct document kinds do not meet. No fourth shared-defs file — `digest`/`binding` are re-declared locally in all eleven and there is no cross-file `$ref` anywhere. Applied to FR-016 | codebase-analyst |
| 2b | Clarify | S1-Q2b: where is the policy-violation enum declared — slice 1 or slice 2? | [codebase] → [spec] | 1→2 | **escape-hatch** | Round 1 recommended slice 1 but at only **medium** confidence, and explicitly deferred its decisive argument (FR-012's `[US1]` tag) to the spec-context lane. Escalated to Round 2 `[spec]`. **Provisionally applied as slice-1 declaration**, reversing the orchestrator's own earlier slice-2 answer: unexercised closed-enum members are house style here (`score-bundle.schema.json:88-89` ships a 36-member enum with ≤4 exercised), no contract document in this tree has ever been edited post-introduction, and slice-1 declaration means slice 2 touches **no** schema at all. Applied to FR-019, FR-033a/b | codebase-analyst (R1) + spec-context-analyst (R2, in flight) |
| 2c | Clarify | S1-Q2c: do the budget maxima ship in slice 1 with the fields? | [codebase] | 1 | high-confidence | **Yes.** Numeric constraints share the object literal with their field's `type` universally in this directory, zero counterexamples, so declaring a field and bounding it is one authoring act. Caveat recorded: bounding a `max_*` field from *above* with `maximum` has no exact precedent (the existing budget precedent bounds from below with `minimum`), so the keyword choice is this feature's own. Applied to FR-027 | codebase-analyst |
| 2d | Clarify | S1-Q2d: enum declaration style — bare `$defs` enum or inline at point of use? | [codebase] | 1 | high-confidence | **Inline at point of use.** No bare-enum `$defs` exists anywhere in the directory. Report expresses both enums as two diagnostic-entry `$defs`, each with its own inline `code` enum, unioned by `oneOf` at the diagnostics array — giving FR-017a a stable pointer. FR-017a additionally now requires reading the enum **live** by JSON pointer rather than transcribing it. New FR-016a; FR-017a amended | codebase-analyst |
| 3 | Clarify | S1-Q5: are two slices still warranted now the artifact list is concrete? | [spec] | n/a | **operator-directive** | **Keep two slices**, with the rationale corrected: the split is *elected on review burden and independent slice value*, not forced by a LOC ceiling. Consensus was deliberately **not** dispatched — the executor's own blocker was operator authority, not an evidence gap, and no analyst can supply authority the operator already exercised. Surfaced to the operator for a change of mind; shipped artifacts are identical either way, only PR count and the append-only discipline change | none dispatched (see Resolution) |

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
tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-claude/       # + route-policy / snapshot-projection / resolution-report schemas
│   ├── fixtures-fallback/      # + fallback-scenario-corpus.json (new directory)
│   └── lib/                    # + claude_route_fallback.py (reference simulator)
├── unit/                       # + test-route-fallback-simulation.py (durable name)
└── suite-manifest.json         # register new unit tests
specs/car-005-availability-fallback-recovery/   # spec.md, plan.md, tasks.md, SPEC-MOC.md
docs/ai/specs/.process/                          # this workflow + design concept
```

---

Template based on SpecKit best practices. Prompts above are populated from the CAR-005 roadmap scope and the 2026-07-29 grill-me design concept.

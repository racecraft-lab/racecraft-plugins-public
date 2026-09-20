# Continuous Goal Verification Implementation Roadmap

**Give SpecKit Pro a versioned, replayable way to tell work that is actually
complete from work that merely looks complete, on both hosts, without granting
any new authority.**

This document defines the **SPEC catalog** for Continuous Goal Verification: an
ordered set of specifications derived from the source PRD. Each SPEC corresponds
1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving
traceability from PRD -> roadmap -> spec. Each specification is executed
end-to-end through the SpecKit workflow (specify -> clarify -> plan -> checklist ->
tasks -> analyze -> implement) before moving to the next, and is prepared for
autopilot with `/speckit-pro:speckit-scaffold-spec VRFY-NNN`, which reads this
roadmap as its input.

**Source PRD:** [../../prd-continuous-goal-verification.md](../../prd-continuous-goal-verification.md)
**Roadmap MOC:** [continuous-goal-verification-roadmap-MOC.md](continuous-goal-verification-roadmap-MOC.md)
**Spec ID prefix:** `VRFY-###`
**Status:** Draft. No VRFY spec has been scaffolded.
**Backlog catalog:** [continuous-goal-verification-backlog.md](continuous-goal-verification-backlog.md)
**Backlog provenance:** Each SPEC names the JEV backlog identifiers it delivers.
The catalog above is the committed per-item record for all 71 and the
procedure for promoting a deferred entry. The bundle's dependency edges were checked
against this graph; every JEV `depends_on` is satisfied by a predecessor SPEC.

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Reviewability Contract](#reviewability-contract)
3. [Dependency Graph](#dependency-graph)
4. [Progress Tracking](#progress-tracking)
5. [Specification Sections](#specification-sections)
6. [Decomposition Principles](#decomposition-principles)
7. [Environment & Deployment Context](#environment--deployment-context)
8. [References](#references)

---

## Roadmap Overview

The feature is decomposed into **12 specifications** across **7 dependency
tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | VRFY-001 | Map both hosts and settle shadow-versus-advisory before touching shipped source | Sequential; timeboxed spike |
| **2** | VRFY-002 | Versioned decision contract and offline prepare/assess helpers | Sequential foundation |
| **3** | VRFY-003, VRFY-008 | Additive journal with offline replay; frozen goal and obligation registry | Parallel after VRFY-002 |
| **4** | VRFY-004 | Dual-host trusted-parent adapter, default disabled, with consent and budget controls | Sequential; the only slice that touches the wire |
| **5** | VRFY-005, VRFY-006, VRFY-007, VRFY-009 | Three shadow pilots at existing handoffs; phase-boundary goal verifier | Parallel after VRFY-004 (VRFY-009 also needs VRFY-008) |
| **6** | VRFY-010 | Change-triggered scheduler and invalidation | Sequential after VRFY-009 |
| **7** | VRFY-011, VRFY-012 | Stop/continue advice; trajectory corpus and calibration report | Parallel after VRFY-010 |

**Execution Order:** VRFY-001 -> VRFY-002 -> VRFY-003 + VRFY-008 -> VRFY-004 ->
VRFY-005 + VRFY-006 + VRFY-007 + VRFY-009 -> VRFY-010 -> VRFY-011 + VRFY-012

**Dependency Constraints:**

- VRFY-001 must run first because every later slice needs the observed
  result-consumption boundary on each host; guessing it would misclassify shadow
  evidence as isolated when it is advisory.
- VRFY-002 requires VRFY-001 because the contract binds to the integration
  points and the host posture the spike recorded.
- VRFY-003 and VRFY-008 both require only VRFY-002 and are independent of each
  other: the journal records decisions, the registry defines what is judged.
- VRFY-004 requires VRFY-002 and VRFY-003 because a pre-call journal admission
  failure must skip the optional call; the adapter cannot exist before the
  journal does.
- VRFY-005, VRFY-006, and VRFY-007 each require VRFY-004 because they are
  consumers of the adapter at an existing handoff; they do not depend on each
  other.
- VRFY-009 requires VRFY-003, VRFY-004, and VRFY-008 because the verifier reads
  frozen obligations, consumes adapter results, and records to the journal.
- VRFY-010 requires VRFY-009 because incremental scheduling only has meaning
  once phase-boundary reconciliation exists.
- VRFY-011 requires VRFY-010 because stop/continue advice consumes the
  scheduler's current aggregation vector.
- VRFY-012 requires VRFY-003, VRFY-009, and VRFY-010 because trajectory replay
  compares phase-only with change-triggered checking on stored journals.

## Reviewability Contract

Every spec must fit a human review budget before setup and again before PR
creation. The size metric counts **production code only**; documentation,
tests, and config do not contribute to the reviewable-LOC count.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files. Touching more than one primary surface is also a warning, not a block.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless this roadmap records a typed exception pragma (below).
- A slice that adds only net-new files (no existing files modified) gets a 1.5x
  greenfield allowance on the production-LOC thresholds (warn 600, block 1200).
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- A block-sized slice may be allowed only by a typed, auditable exception
  pragma on its own line, exactly: `Reviewability-Exception: <class>` where
  `<class>` is one of `refactor`, `infra`, or `upgrade`. The match is
  line-anchored and case-sensitive with no trailing content; an unknown class,
  a mis-cased class, or free-form prose is not honored (fail-closed).
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

Projected reviewable LOC below comes from the `estimate-spec-size` runner
operation run on 2026-09-19 with the size signals recorded in each entry. It is
a forward guess, not the authoritative count.

---

## Dependency Graph

```text
VRFY-001 (Host Boundary Spike)
   │
   ▼
VRFY-002 (Decision Contract + Offline Prepare/Assess)
   ├──────────────────────────────┐
   ▼                              ▼
VRFY-003 (Journal + Replay)   VRFY-008 (Obligation Registry)
   │                              │
   ▼                              │
VRFY-004 (Dual-Host Adapter, default off)
   ├──────────┬──────────┬──────────────┐
   ▼          ▼          ▼              ▼
VRFY-005   VRFY-006   VRFY-007      VRFY-009 (Phase-Boundary Verifier) ◄── VRFY-008
(Coverage) (Closure)  (Support)         │
                                        ▼
                                    VRFY-010 (Scheduler + Invalidation)
                                        ├──────────────┐
                                        ▼              ▼
                                    VRFY-011        VRFY-012 (Trajectory Calibration) ◄── VRFY-003
                                    (Stop/Continue)

Each accepted spec delivers its own observable outcome.
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| VRFY-001 | Host Boundary and Implementation-Map Spike | ⏳ Pending | [VRFY-001-workflow.md](VRFY-001-workflow.md) | Specify |
| VRFY-002 | Versioned Decision Contract and Offline Prepare/Assess | ⏳ Pending | [VRFY-002-workflow.md](VRFY-002-workflow.md) | VRFY-001 |
| VRFY-003 | Additive Decision Journal and Offline Replay | ⏳ Pending | [VRFY-003-workflow.md](VRFY-003-workflow.md) | VRFY-002 |
| VRFY-004 | Dual-Host Trusted-Parent Adapter | ⏳ Pending | [VRFY-004-workflow.md](VRFY-004-workflow.md) | VRFY-003 |
| VRFY-005 | Pilot: Requirement-to-Task Semantic Coverage | ⏳ Pending | [VRFY-005-workflow.md](VRFY-005-workflow.md) | VRFY-004 |
| VRFY-006 | Pilot: Review-Fix Closure Verification | ⏳ Pending | [VRFY-006-workflow.md](VRFY-006-workflow.md) | VRFY-004 |
| VRFY-007 | Pilot: Claim-to-Source Support Annotation | ⏳ Pending | [VRFY-007-workflow.md](VRFY-007-workflow.md) | VRFY-004 |
| VRFY-008 | Frozen Goal and Obligation Registry | ⏳ Pending | [VRFY-008-workflow.md](VRFY-008-workflow.md) | VRFY-002 |
| VRFY-009 | Phase-Boundary Goal-Completion Verifier | ⏳ Pending | [VRFY-009-workflow.md](VRFY-009-workflow.md) | VRFY-008 |
| VRFY-010 | Change-Triggered Scheduler and Invalidation | ⏳ Pending | [VRFY-010-workflow.md](VRFY-010-workflow.md) | VRFY-009 |
| VRFY-011 | Premature-Stop and Redundant-Continuation Advice | ⏳ Pending | [VRFY-011-workflow.md](VRFY-011-workflow.md) | VRFY-010 |
| VRFY-012 | Trajectory Corpus, Calibration Report, and Gated Live Evaluation | ⏳ Pending | [VRFY-012-workflow.md](VRFY-012-workflow.md) | VRFY-010 |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### VRFY-001: Host Boundary and Implementation-Map Spike

**Priority:** P1 | **Depends On:** None | **Enables:** VRFY-002 and every later slice's host posture

**Goal:** Produce an evidence-backed map of where, on Claude Code and on Codex,
a semantic result can be prepared, invoked, consumed, and recorded without
expanding authority, and settle whether each host can deliver isolated shadow
evidence or only advisory output.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 (spike; sized by a two-day timebox) |
Production files: 0 |
Total files: 1 |
Budget result: within budget

**Backlog delivered:** reconnaissance portion of JEV-056; the parity-check
portion of JEV-055.

**Scope:**

- Read-only reconnaissance of actual HEAD: root and nearest `AGENTS.md`,
  `agent_inventory.json`, helper registry, runner contracts, suite manifest,
  `execution_control.py`, `task_execution.py`, `task_results.py`, verification
  records, consensus, capability discovery, grounding, gate validation, review
  resolution, and both platform adapters.
- For each host, observe how the `typesafe-jev` plugin's `evaluate` tool is
  registered and invoked today, whether its result reaches the live parent
  before decisions are sealed, and record the achievable posture per host as
  `isolated_shadow`, `retrospective_shadow`, or `advisory_not_authorized`.
- Record the Codex registration path: the installed plugin ships only a Claude
  MCP config, so the Codex path must be observed or marked unqualified.
- Classify each inherited bundle finding as still open, resolved, or unverified
  against current source, including review-thread pagination (`first: 100`) and
  resolve-before-final-verify ordering in `speckit-resolve-pr`.
- Produce a dependency-ordered file plan with exact file and line integration
  points, explicit exclusions, and the predecessor acceptance test for each
  later slice.

**Out of Scope:**

- Any shipped source change (VRFY-002 onward).
- Installing into user registries, changing global model settings, inspecting
  key values, or making a provider call.
- Fixing the resolve-pr defects (VRFY-006).

**Key Decisions:**

**Both-hosts-together Decision (2026-09-19):** Every later slice ships for
Claude Code and Codex in the same PR. The spike therefore maps both hosts, not a
first host. Alternatives considered: Claude Code first with Codex as follow-on,
rejected because it would create a parity debt the repository's standing
principle forbids.

**Module and Interface Deltas:**

- `docs/ai/specs/continuous-goal-verification-host-boundary-spike.md` - new: the spike report

**Key Files:**

- `speckit-pro/speckit_pro_runner/agent_inventory.json` - authoritative role set
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - helper envelope and promotion pattern
- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` - discovery contract
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` - pagination and ordering under review
- `speckit-pro/.mcp.json` - existing MCP registration (sweep broker only)

---

### VRFY-002: Versioned Decision Contract and Offline Prepare/Assess

**Priority:** P1 | **Depends On:** VRFY-001 | **Enables:** VRFY-003, VRFY-004, VRFY-008

**Goal:** Every semantic judgment SpecKit Pro will ever consume is defined as a
versioned decision with independent projection, rubric, normalizer, and policy
identities, prepared and assessed by pure offline runner helpers with strict
normalization.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 380 (signals: 3 stories, 5 files, 7 FRs, net-new) |
Production files: 5 |
Total files: 14 |
Budget result: within budget

**Backlog delivered:** JEV-056; infrastructure portion of JEV-053.

**Scope:**

- Language-neutral JSON contracts for `DecisionDefinition`, the per-evaluation
  local envelope, and the receipt, with a conformance fixture set consumable by
  Python and TypeScript readers. Fixtures, not a shared runtime package.
- A small shared module that prepares the bounded evidence projection, builds
  the wire request (only `state`, `questions`, and selected model fields),
  normalizes Noul, Choice, and Score separately, and interprets a versioned
  policy deterministically.
- Registered read-only helpers `prepare-semantic-check` and
  `assess-semantic-check` in the helper registry with promotion status and
  request fixtures, following the existing envelope.
- Versioned canonicalization: reject duplicate keys and non-finite numbers,
  preserve evidence bytes, order keys, compute serialized UTF-8 size, and check
  the 64k total and 32k state-plus-longest-question budgets locally before the
  provider's own enforcement.
- Separate evaluation key (evidence, projection, rubric, normalizer, provider
  contract, model identity, inference settings) from interpretation key (plus
  policy version and applicable goal state); neither includes timestamps,
  attempt ids, or correlation ids.
- Receipt with the six separate dimensions: `execution_status`, `coverage`,
  `semantic_outcomes`, `freshness`, `provenance`, `policy_interpretation`.
- A versioned rubric catalog with stable question ids, string-only instructions
  and criteria, primitive type, hash, and pinned model `jev-1.13.0`.

**Out of Scope:**

- Any provider call or adapter (VRFY-004).
- Journal persistence (VRFY-003).
- Concrete pilot rubrics beyond the catalog schema and one example per primitive
  (VRFY-005 through VRFY-007).

**Key Decisions:**

**String-only rubric Decision (2026-09-19):** The shared rubric format uses
string instructions and criteria only, because the plugin defaults to the
OpenRouter backend, which rejects structured descriptions. Alternatives
considered: backend-conditional rubric shapes, rejected as two catalogs to keep
in step.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/semantic_checks.py` - new: prepare, normalize, assess, canonicalize
- `speckit-pro/speckit_pro_runner/contracts/semantic-decision-*.json` - new: decision, envelope, receipt schemas
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - changed: registers `prepare-semantic-check`, `assess-semantic-check`
- shared rubric catalog under `speckit-pro/` - new: versioned, string-only questions

**Key Files:**

- `speckit-pro/speckit_pro_runner/semantic_checks.py` - new module
- `speckit-pro/speckit_pro_runner/contracts/` - schema home
- `speckit-pro/speckit_pro_runner/helpers/registry.py` - helper registration
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` - helper implementations
- `tests/speckit-pro/unit/fixtures/semantic-checks/` - conformance and normalization fixtures

---

### VRFY-003: Additive Decision Journal and Offline Replay

**Priority:** P1 | **Depends On:** VRFY-002 | **Enables:** VRFY-004, VRFY-009, VRFY-012

**Goal:** Every decision observation is appended to an immutable, sequenced
diagnostic journal that supports historical replay and counterfactual policy
simulation with zero external effects, while existing workflow stores keep their
authority.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 340 (signals: 3 stories, 4 files, 7 FRs, net-new) |
Production files: 4 |
Total files: 12 |
Budget result: within budget

**Backlog delivered:** JEV-057, JEV-058.

**Scope:**

- Append-only journal under the feature's `.process/` directory with per-run
  sequence, event id, correlation and causation ids, source revision, contract
  identities, evidence references, and the logical events `DecisionRequested`,
  `DecisionSkipped`, `DecisionEvaluated`, `DecisionFailed`,
  `DecisionMarkedStale`, `PolicyInterpreted` (reusing an existing vocabulary if
  one fits).
- Documented single-writer, interrupted-write, duplicate-delivery, payload-size,
  and access behavior using the repository's existing atomic-write conventions;
  SQLite only if concurrency tests force it.
- Separately controlled evidence store holding sensitive payloads; the journal
  keeps reference plus digest; deletion leaves an explicit unavailable marker.
- Historical replay: stored answers plus original policy and projection versions
  reproduce the interpretation offline; unknown versions are refused.
- Counterfactual policy simulation: stored answers plus a candidate policy emit
  hypothetical differences without editing originals.
- Live model reevaluation exposed only as a guarded refusal until VRFY-012.
- Crash-after-send handling: request marked unknown, never auto-retried.

**Out of Scope:**

- Any provider transport (VRFY-004).
- Rendering the journal in status mode (deferred, JEV-048).
- Migrating any existing store to the journal.

**Key Decisions:**

**Persistence Decision (pending, OQ-3):** JSON-lines through existing atomic
write helpers is the recommendation; the spec records the decision after the
concurrency tests run.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/decision_journal.py` - new: append, replay, simulate; evidence-store reference
- `<feature>/.process/decision-journal/` - new: diagnostic records; not authoritative

**Key Files:**

- `speckit-pro/speckit_pro_runner/decision_journal.py` - new module
- `speckit-pro/speckit_pro_runner/task_results.py` - existing journal-file conventions to reuse
- `tests/speckit-pro/unit/fixtures/decision-journal/` - duplicate, crash, version, replay fixtures

---

### VRFY-004: Dual-Host Trusted-Parent Adapter with Consent, Budget, and Egress Controls

**Priority:** P1 | **Depends On:** VRFY-002, VRFY-003 | **Enables:** VRFY-005, VRFY-006, VRFY-007, VRFY-009

**Goal:** The trusted parent on Claude Code and on Codex can invoke the
already-registered `evaluate` tool for a prepared decision, with per-project
enablement defaulting to off, explicit consent and budget checks before every
request, and a byte-identical disabled path.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 395 (signals: 3 stories, 5 files, 8 FRs, net-new) |
Production files: 5 |
Total files: 15 |
Budget result: within budget (at the total-files warn line; split the Codex binding into its own commit if the count grows)

**Backlog delivered:** the adapter and configuration slice the handoff calls
"Slice 3"; parity-check portion of JEV-055.

**Scope:**

- Capability discovery gains an optional typed-semantic-judgment capability with
  no hardcoded vendor preference; discovery selects the installed `evaluate`
  tool when present.
- Project-level configuration for enablement, consent, permitted data classes,
  provider and model pairing, and per-phase and per-run call, input, spend, and
  time caps; default off; read-only from status mode.
- Pre-call checks: consent, provider and model pairing, data class, budget, and
  journal admission; any failure records `DecisionSkipped` and leaves the
  workflow unchanged.
- Thin invoke-and-consume bindings in the Claude and Codex autopilot skills at
  the existing handoffs, each passing the same contract fixtures.
- Requested and reported model identity recorded; mismatch against the pinned
  `jev-1.13.0` marks the result `unqualified`.
- Path exclusion and secret filtering in code before transmission; key values
  never appear in output.
- Parity test: agent inventory, sweep-role allowlists, named
  `consensus-synthesizer` binding, gates, budgets, and permissions unchanged on
  both hosts.
- Byte-comparison test: with enablement off, existing fixture outputs, gate
  results, and status-mode writes are identical to baseline; generated payloads
  regenerate per the artifact contract.

**Out of Scope:**

- Any concrete pilot rubric or handoff annotation (VRFY-005 through VRFY-007).
- A direct process adapter bypassing the native MCP invocation.
- Changes to the `typesafe-jev` plugin or launcher.

**Key Decisions:**

**No second provider client Decision (2026-09-19):** SpecKit never holds
credentials, provider selection, HTTP, or retries; the qualified native parent
calls the registered MCP capability. Alternatives considered: a Python SDK
fallback, rejected as a duplicate provider surface.

**Module and Interface Deltas:**

- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` - changed: optional typed-semantic-judgment capability
- `speckit-pro/skills/speckit-autopilot/references/semantic-checks.md` - new: ownership, consent, budgets, failure behavior
- Claude and Codex autopilot skill bindings - changed: thin invoke-and-consume at existing handoffs
- project semantic-check configuration - new: enablement, consent, data classes, caps; default off

**Key Files:**

- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` - discovery contract
- `speckit-pro/skills/speckit-autopilot/references/semantic-checks.md` - new shared reference
- `speckit-pro/skills/speckit-autopilot/SKILL.md` and `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` - host bindings
- `speckit-pro/speckit_pro_runner/semantic_checks.py` - consent and budget checks
- `tests/speckit-pro/unit/` - disabled-path byte comparison, egress denial, parity

---

### VRFY-005: Pilot: Requirement-to-Task Semantic Coverage

**Priority:** P1 | **Depends On:** VRFY-004 | **Enables:** VRFY-012 corpus

**Goal:** After Tasks, each approved requirement receives a shadow annotation
saying whether its linked tasks plan the behavior, so a task that only repeats an
FR identifier is visible before implementation begins.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 245 (signals: 2 stories, 3 files, 5 FRs, net-new) |
Production files: 3 |
Total files: 9 |
Budget result: within budget

**Backlog delivered:** JEV-023.

**Scope:**

- One Noul per source-backed atomic requirement or acceptance id over the full
  linked task set with acceptance conditions; planned behavior, failure cases,
  and required evidence recorded as separate fields.
- Bind at the existing G5 handoff; the structural G5 helper stays authoritative
  and the annotation changes no gate result, task count, or repair reservation.
- Conjunctive aggregation in code: one uncovered required obligation is reported
  uncovered; inapplicability only from approved scope rules.
- Plan or task edit marks dependent judgments stale via the VRFY-002 evaluation
  key.
- Fixtures: FR-id-only task, paraphrased plan, missing sub-obligation, planning
  coverage presented as implementation completion.

**Out of Scope:**

- Any change to how G5 passes or fails.
- Implementation-completion judgments (VRFY-009).

**Module and Interface Deltas:**

- Tasks phase G5 handoff - changed: adds shadow annotation beside structural result

**Key Files:**

- `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` - G5 handoff
- shared rubric catalog - coverage rubric entry
- `tests/speckit-pro/unit/fixtures/semantic-checks/coverage/` - pilot fixtures

---

### VRFY-006: Pilot: Review-Fix Closure Verification with Deterministic Prerequisites

**Priority:** P1 | **Depends On:** VRFY-004 | **Enables:** VRFY-012 corpus

**Goal:** `speckit-resolve-pr` fetches every review page, verifies and pushes
before replying or resolving, and records a shadow judgment of whether each
concern was actually addressed, so a fluent reply can no longer close a thread
the code did not fix.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 162 (signals: 3 stories, 4 files, 6 FRs, modify) |
Production files: 4 |
Total files: 10 |
Budget result: within budget

**Backlog delivered:** JEV-038 plus its two deterministic prerequisites.

**Scope:**

- Deterministic prerequisite one: paginate `reviewThreads` and comments past the
  first page before claiming all feedback is handled.
- Deterministic prerequisite two: order final verification, then push and
  confirm the remote SHA, then reply and resolve.
- Closure judgment inputs: original concern, full thread, before and after
  source, acceptance condition, actual verification observations, pushed SHA.
- Annotation only; no reply or resolution from a model result; missing
  verification cannot become `resolved`.
- Later relevant edit invalidates the judgment.
- Fixtures: wrong-path fix, superficially similar edit, correct fix without
  execution evidence, supported false-positive rebuttal, omitted comment, new
  regression.

**Out of Scope:**

- Automated thread resolution from a positive judgment (never in this PRD).
- Effect-intent reconciliation for GitHub mutations (deferred, JEV-060).

**Key Decisions:**

**Prerequisites-first Decision (2026-09-19):** If the spike finds the pagination
or ordering defects still open, this spec fixes them before adding the judgment;
a model call never hides a deterministic bug.

**Module and Interface Deltas:**

- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` - changed: full pagination; verify, push, then reply and resolve
- `speckit-pro/speckit_pro_runner/helpers/` sweep or review helper - changed: closure annotation record

**Key Files:**

- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` and its Codex mirror - workflow ordering
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` - `sweep-pr-feedback` pagination
- `tests/speckit-pro/unit/fixtures/semantic-checks/closure/` - pilot fixtures

---

### VRFY-007: Pilot: Claim-to-Source Support Annotation

**Priority:** P2 | **Depends On:** VRFY-004 | **Enables:** VRFY-012 corpus

**Goal:** At the shared grounding boundary, each analyst claim with a citation
receives a shadow annotation classifying whether the retrieved source supports
it, contradicts it, does not address it, or lacks context, without rewriting or
suppressing the finding.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 245 (signals: 2 stories, 3 files, 5 FRs, net-new) |
Production files: 3 |
Total files: 9 |
Budget result: within budget

**Backlog delivered:** JEV-005.

**Scope:**

- Mechanical quote resolution first; the Choice runs only when the span exists.
- Choice over `supports`, `contradicts`, `does_not_address`,
  `insufficient_context`; full distribution retained.
- Annotation linked to the original finding id; review queue, not a rewrite.
- Source edit marks affected judgments stale.
- Fixtures: real but irrelevant citation, paraphrased support, opposite
  behavior, missing branch context, missing source, prompt-like instructions in
  evidence.

**Out of Scope:**

- Research-passage ranking (deferred, JEV-004).
- Instruction-bearing evidence flags as a separate check (deferred, JEV-006).

**Module and Interface Deltas:**

- shared grounding boundary reference - changed: support annotation queue

**Key Files:**

- `speckit-pro/skills/speckit-autopilot/references/grounding.md` - grounding boundary
- shared rubric catalog - support rubric entry
- `tests/speckit-pro/unit/fixtures/semantic-checks/support/` - pilot fixtures

---

### VRFY-008: Frozen Goal and Obligation Registry

**Priority:** P1 | **Depends On:** VRFY-002 | **Enables:** VRFY-009

**Goal:** Approved goals become frozen, versioned obligations with stable ids,
provenance, stage-relative applicability, and required evidence, so the verifier
has a fixed target that a model cannot ratify, drop, or weaken.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 340 (signals: 3 stories, 4 files, 7 FRs, net-new) |
Production files: 4 |
Total files: 11 |
Budget result: within budget

**Backlog delivered:** JEV-061.

**Scope:**

- Obligation record: stable id, goal version, source reference and provenance
  class, owning phase or task, applicability rule, required authoritative
  observations, semantic predicates and evidence requirements, dependency
  references, existing failure-invariant or reservation linkage.
- Reuse existing FR and task ids; never renumber.
- Kickoff and resume bind the registry; goal change is an explicit versioned
  event that invalidates dependent judgments.
- Empty applicable required set rejected as `invalid_goal`.
- Stage-relative requirements: planning never requires implementation evidence;
  publication, UAT, rendering, and approval keep independent evidence.

**Out of Scope:**

- Judging obligations (VRFY-009).
- Atomic-criterion wording assistance (deferred, JEV-009).
- Interview-fidelity checks on the human decision record (deferred, JEV-008).

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/goal_obligations.py` - new: frozen obligations, versions, applicability
- `<feature>/.process/goal-obligations.json` - new: versioned goal record

**Key Files:**

- `speckit-pro/speckit_pro_runner/goal_obligations.py` - new module
- `speckit-pro/speckit_pro_runner/task_execution.py` - existing task-id and sidecar conventions
- `tests/speckit-pro/unit/fixtures/goal-obligations/` - invalid goal, rewording, version transition

---

### VRFY-009: Phase-Boundary Goal-Completion Verifier

**Priority:** P1 | **Depends On:** VRFY-003, VRFY-004, VRFY-008 | **Enables:** VRFY-010, VRFY-012

**Goal:** At phase handoff and proposed terminal summary, the trusted parent
reconciles every applicable obligation against current evidence and records an
aggregation vector whose completion-suggestion flag can be true only when
nothing required is unknown, unmet, stale, or unjudged.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Projected reviewable LOC: 355 (signals: 3 stories, 4 files, 8 FRs, net-new) |
Production files: 4 |
Total files: 12 |
Budget result: within budget

**Backlog delivered:** JEV-062.

**Scope:**

- Full-set reconciliation at phase and terminal boundaries, not only previously
  selected items.
- Per-obligation semantic assessment through the adapter; unsupported,
  contradicted, insufficient, stale, and not_run kept separate.
- Deterministic aggregation vector with the eight named fields; no field hides
  another; eligibility is conjunctive.
- Expected TDD RED recognized from the genuine test stage.
- G6.5 confidence block and named synthesizer untouched; Jev confidence never
  substitutes for the composite.
- Per-host posture from VRFY-001 applied: `advisory_mode_required` where the
  result is visible to the live parent; shadow evidence then collected offline
  or post-run only.

**Out of Scope:**

- Change-triggered scheduling between boundaries (VRFY-010).
- User-facing stop or continue advice (VRFY-011).
- Any thresholds copied from the architecture note's illustration.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/goal_verifier.py` - new: reconciliation and aggregation vector
- autopilot phase-handoff and terminal-summary references - changed: consume verifier output as advisory

**Key Files:**

- `speckit-pro/speckit_pro_runner/goal_verifier.py` - new module
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` - phase handoffs
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` - terminal summary
- `tests/speckit-pro/unit/fixtures/goal-verifier/` - empty goal, one-missing, TDD RED, stale positive

---

### VRFY-010: Change-Triggered Scheduler and Invalidation

**Priority:** P1 | **Depends On:** VRFY-009 | **Enables:** VRFY-011, VRFY-012

**Goal:** Between boundaries, only meaningful parent-observed changes schedule
checks, identical evidence is never re-billed, and late or superseded results
can never advance state.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Projected reviewable LOC: 275 (signals: 2 stories, 3 files, 7 FRs, net-new) |
Production files: 3 |
Total files: 9 |
Budget result: within budget

**Backlog delivered:** JEV-063.

**Scope:**

- Trigger set limited to the boundaries VRFY-001 observed on each host:
  consumed worker results after effect reconciliation, relevant source, task,
  test, or goal changes, phase handoffs, terminal summaries, cancellation, and
  revoked consent.
- Dirty obligation ids, content fingerprints, current revision, and in-flight
  requests tracked; identical snapshots coalesced.
- Unknown dependency coverage invalidates the conservative larger scope.
- Single in-flight check per decision, projection, and run identity; late
  responses after cancellation, goal revision, or supersession retained as
  stale, never applied.
- No self-trigger from verifier results, journal appends, or status renders.
- Existing cancellation and run budgets dominate; exhaustion is never success.
- Offline scheduling simulation labeled as such, never as live adapter latency.

**Out of Scope:**

- Any after-turn hook, compaction callback, or hidden PreToolUse or Stop
  remote-evaluation hook.
- Stagnation detection (deferred, JEV-065).

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/goal_verifier.py` - changed: dirty tracking, coalescing, single-flight, invalidation

**Key Files:**

- `speckit-pro/speckit_pro_runner/goal_verifier.py` - scheduler
- `speckit-pro/speckit_pro_runner/execution_control.py` - existing budget and cancellation authority
- `tests/speckit-pro/unit/fixtures/goal-verifier/scheduler/` - dedup, invalidation, out-of-order, cancellation

---

### VRFY-011: Premature-Stop and Redundant-Continuation Advice

**Priority:** P1 | **Depends On:** VRFY-010 | **Enables:** the user-visible outcome of this PRD

**Goal:** Before a terminal summary, the run shows a bounded advisory naming the
exact unsatisfied obligations or, conversely, the satisfied goal and the
out-of-scope work proposed, without gaining any power to stop, continue, or
bypass.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 260 (signals: 2 stories, 3 files, 6 FRs, net-new) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Backlog delivered:** JEV-064.

**Scope:**

- Premature-done advisory with obligation ids and missing evidence ids.
- Redundant-continuation advisory with the satisfied goal version and the
  proposed out-of-scope work.
- Advisory carries stable references and no executable command; no second
  repair dispatcher.
- User cancellation, budget exhaustion, publication, UAT, and approval
  obligations always win; provider outage never traps a host stop path.
- Named synthesizer and mandatory roles still run.

**Out of Scope:**

- Obligation-targeted feedback packets routed to executors (deferred, JEV-066).
- Candidate comparison or cascade (deferred, JEV-067).

**Module and Interface Deltas:**

- autopilot pre-terminal summary reference - changed: advisory block with obligation ids

**Key Files:**

- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` - terminal summary
- `speckit-pro/speckit_pro_runner/goal_verifier.py` - advisory rendering
- `tests/speckit-pro/unit/fixtures/goal-verifier/advice/` - premature, redundant, outage, cancellation

---

### VRFY-012: Trajectory Corpus, Calibration Report, and Gated Live Evaluation

**Priority:** P1 | **Depends On:** VRFY-003, VRFY-009, VRFY-010 | **Enables:** any promotion from shadow to advisory

**Goal:** A frozen, human-labeled trajectory corpus and an offline calibration
report measure run-level false completion under phase-only versus
change-triggered checking, and a zero-default manifest gates any live Jev
evaluation.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 340 (signals: 3 stories, 4 files, 7 FRs, net-new) |
Production files: 4 |
Total files: 20 |
Budget result: warning accepted (total files exceed the 15-file warn line because the corpus is fixtures; production files stay at 4)

**Backlog delivered:** JEV-070; corpus and holdout portion of JEV-053.

**Scope:**

- Trajectory corpus under the test tree with intermediate goals, evidence,
  revisions, results, and proposed termination points; development and holdout
  split; labels stored apart from model outputs.
- Offline replay driver comparing phase-end with change-triggered verification
  at equal permitted work, reporting run-level false completion, early
  missed-obligation detection, false alarms, unnecessary continuation, reviewer
  overturns, coverage, and overhead, each with uncertainty.
- Retention of every attempt, refusal, and unavailable case; score-shopping
  rejection; holdout never used for tuning.
- Live-evaluation manifest schema: repository and data consent, provider and
  pinned model, permitted hosts, request, spend, and time caps, failure
  behavior, fixed corpus, success criteria; default caps authorize zero
  requests; CI denies egress even with credentials present.
- Adversarial cases from the bundle: completion claims without tests, dropped
  qualifiers after compaction, repeated identical states, useful new test with
  unchanged source, expected RED, omitted negative results, deleted span,
  cancellation mid-evaluation, stale response after goal revision, failed
  journal persistence, duplicate delivery.

**Out of Scope:**

- Running a live evaluation (separate authorization, separate report).
- Model or rubric promotion (a reviewed decision citing this report).
- Formal-methods modeling of the policy (deferred, JEV-071).

**Module and Interface Deltas:**

- `tests/speckit-pro/trajectories/` - new: frozen corpus, holdout, replay report
- live-evaluation test manifest schema - new: zero-default caps

**Key Files:**

- `tests/speckit-pro/trajectories/` - corpus and labels
- `speckit-pro/speckit_pro_runner/decision_journal.py` - replay entry point
- `speckit-pro/speckit_pro_runner/contracts/live-evaluation-manifest.json` - manifest schema
- `tests/speckit-pro/suite-manifest.json` - suite registration

---

## Decomposition Principles

When breaking a feature into specs:

1. **Each spec is independently executable** through the full SpecKit workflow (specify -> implement)
2. **Minimize cross-spec dependencies**; prefer sequential over deeply nested
3. **Vertical slices first**: each spec delivers an observable outcome through
   every layer it needs; do not split backend, UI, or integration into separate
   specs merely by technical layer.
4. **Shared enablers only when justified**: VRFY-002, VRFY-003, and VRFY-008
   are enablers with their own observable contracts (fixtures conform, replay is
   byte-identical, invalid goals are rejected); each ships tests that prove the
   contract without a consumer.
5. **Cross-slice work earns its own spec**: VRFY-012 is the separately valuable
   measurement that gates promotion, not an integration-only tail.
6. **Each spec gets its own directory**: `specs/<number>-<name>/`

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| Typed-judgment provider | `typesafe-jev` plugin 0.7.0 installed at user scope; one `evaluate` MCP tool; defaults to the OpenRouter backend and `~typesafe/jev-latest`; built from the `typesafe-mcp` revision the bundle inspected |
| Runner envelope | `python -m speckit_pro_runner` one-request/one-response JSON; helper registry with promotion status and request fixtures |
| Role inventory | `speckit-pro/speckit_pro_runner/agent_inventory.json`, 12 shared roles plus two sweep-isolation roles and one optional Codex helper |
| Test harness | `python3 tests/speckit-pro/run-all.py`; `tests/speckit-pro/suite-manifest.json` for focused selection |
| Generated artifacts | `python3 scripts/refresh-release-artifacts.py`; `pnpm --dir docs-site reference:generate` when reference inputs change |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| New runner modules | `speckit-pro/speckit_pro_runner/` | `semantic_checks.py`, `decision_journal.py`, `goal_obligations.py`, `goal_verifier.py` (Python 3.11+ stdlib) |
| New helper operations | `helpers/registry.py` | `prepare-semantic-check`, `assess-semantic-check` with fixtures and promotion status |
| New shared reference | `skills/speckit-autopilot/references/semantic-checks.md` | ownership, consent, budgets, failure behavior; loaded on demand, not always-on |
| Project configuration | consumer project | semantic-check enablement and caps; default off |
| Payload regeneration | `dist/` | every slice regenerates installed payloads and checksums |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| Runner | `PYTHONPATH=speckit-pro python3.11 -m speckit_pro_runner < request.json` |
| Suite | `python3 tests/speckit-pro/run-all.py` (no bootstrap) |
| Provider, only for a separately authorized live run | `typesafe-jev` plugin installed; `evaluate` binary present; key file at the launcher's documented path; never read into agent-visible output |
| Docs site, only when reference inputs change | `pnpm --dir docs-site install --frozen-lockfile` once per worktree |

---

## References

- **Source PRD:** [../../prd-continuous-goal-verification.md](../../prd-continuous-goal-verification.md), the SPEC catalog above is derived from its Features and Acceptance Criteria
- **Roadmap MOC:** [continuous-goal-verification-roadmap-MOC.md](continuous-goal-verification-roadmap-MOC.md)
- **PRD Template:** `speckit-pro/skills/speckit-coach/templates/prd-template.md`, author with `/speckit-pro:speckit-prd`
- **Constitution:** `.specify/memory/constitution.md`
- **Project Standards:** `AGENTS.md`, `REVIEW.md`
- **Backlog catalog:** [continuous-goal-verification-backlog.md](continuous-goal-verification-backlog.md), per-item record for JEV-001 through JEV-071; supersedes the 2026-09-19 handoff bundle
- **Provider documentation:** TypeSafe Jev models, Jev 1.13 jaggedness, and confidence pages at `docs.typesafe.ai`, read 2026-09-19

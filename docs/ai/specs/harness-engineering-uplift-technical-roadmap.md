# SpecKit Pro Harness Engineering Uplift Implementation Roadmap

**Turn SpecKit Pro harness needs into reviewable hardening specs for context,
tools, permissions, evals, traces, orchestration, and drift repair.**

This document defines the **SPEC catalog** for the harness-engineering uplift:
an ordered set of specifications derived from the source PRD. Each SPEC maps
1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving
traceability from PRD -> roadmap -> spec. Each specification is prepared for
implementation with `$speckit-scaffold-spec HRNS-###`, which reads this roadmap
as its input.

**Source PRD:** [../../prd-harness-engineering-uplift.md](../../prd-harness-engineering-uplift.md)
**Roadmap MOC:** [harness-engineering-uplift-roadmap-MOC.md](harness-engineering-uplift-roadmap-MOC.md)
**Spec ID prefix:** `HRNS-###`
**Status:** Draft. Added 2026-07-03 and updated 2026-07-04 to describe the
SpecKit Pro harness hardening lane.

---

## Roadmap Overview

The feature is decomposed into **8 specifications** across **6 spec dependency
tiers**. A separate follow-on scaffold lane turns accepted roadmap items into
reviewable implementation branches.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | HRNS-001 | Inventory harness surfaces and classify SpecKit Pro gaps | Sequential foundation |
| 2 | HRNS-002, HRNS-003 | Durable context/state and helper/tool contract foundations | Parallel after HRNS-001 |
| 3 | HRNS-004, HRNS-005 | Permission/sandbox controls and eval readiness | Parallel after HRNS-003 where needed |
| 4 | HRNS-006 | Trace/debug packet contract spanning helpers, evals, and permissions | Sequential after HRNS-003 through HRNS-005 |
| 5 | HRNS-007 | Long-horizon orchestration and resumption controls | Sequential after HRNS-002 and HRNS-006 |
| 6 | HRNS-008 | Harness drift and garbage-collection remediation loop | Sequential after HRNS-002, HRNS-005, and HRNS-006 |

**Follow-on scaffold lane:** After maintainers accept this roadmap, scaffold ready
HRNS specs as reviewable implementation branches in the selected priority order.

**Execution Order:** HRNS-001 -> HRNS-002 + HRNS-003 -> HRNS-004 + HRNS-005 ->
HRNS-006 -> HRNS-007 -> HRNS-008

**Dependency Constraints:**

- HRNS-001 must run first because downstream specs need a durable surface
  inventory and gap taxonomy before changing context, helper, eval, trace, or
  orchestration behavior.
- HRNS-002 and HRNS-003 can run in parallel after HRNS-001 because context/state
  and helper/tool contracts touch related but separable surfaces.
- HRNS-004 requires HRNS-003 because permission and sandbox controls need helper
  risk metadata and mutability declarations.
- HRNS-005 requires HRNS-001 and HRNS-003 because evals should map to concrete
  skills/helpers, helper records, and capability contracts rather than generic
  benchmark claims.
- HRNS-006 requires HRNS-003, HRNS-004, and HRNS-005 because trace/debug packets
  summarize helper selection, authorization, and verification evidence.
- HRNS-007 requires HRNS-002 and HRNS-006 because resumption needs durable state
  plus traceable handoff evidence.
- HRNS-008 requires HRNS-002, HRNS-005, and HRNS-006 because drift detection
  depends on current context contracts, sensor coverage, and trace/debug
  evidence.

## Reviewability Contract

Every implementation spec must fit a human review budget before setup and again
before PR creation. The size metric counts production code only; documentation,
tests, and config do not contribute to reviewable production LOC.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files. Touching more than one primary surface is a warning unless the spec
  records why a split would be less safe.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless the roadmap/spec records a typed exception.
- A slice that adds only net-new files gets the existing greenfield allowance.
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

## Harness Requirements Summary

The harness hardening lane centers on these requirements:

- Treat the harness as the product surface: context, tools, state, sandbox,
  feedback, and enforceable constraints around the model.
- Use progressive disclosure: short entrypoint maps, deeper source-of-truth
  docs, and just-in-time context rather than oversized prompt manuals.
- Define tool/helper interfaces as agent UX: names, schemas, mutability,
  remediation messages, and result size affect reliability.
- Put humans on meaningful loop points: scope, plan, high-risk tool use,
  memory/policy writes, and final review.
- Layer verification: deterministic checks first, fixture parity next,
  trace/transcript review where useful, and calibrated rubric review only where
  deterministic checks cannot cover the risk.
- Make security policy structural: least privilege, pre-action authorization,
  protected harness-control files, default-deny posture, and safe stop.
- Emit local trace/debug packets so failures can be classified and replayed
  without dumping raw logs into PRs.
- Add garbage collection because prompts, docs, sensors, tests, generated
  payloads, and examples drift as models and workflows change.
- Keep the first-release implementation dependency posture conservative:
  repo-local contracts and Python runner/helper surfaces first, with any larger
  runtime dependency requiring its own explicit decision.

---

## Dependency Graph

```text
HRNS-001 -> HRNS-002 Progressive Context and Durable State
HRNS-001 -> HRNS-003 Helper, Tool, and Capability Contract
HRNS-003 -> HRNS-004 Permission, Sandbox, and Authorization
HRNS-001 + HRNS-003 -> HRNS-005 Feedback Sensors and Eval Readiness
HRNS-003 + HRNS-004 + HRNS-005 -> HRNS-006 Trace, Debug, and Review Evidence Packets
HRNS-002 + HRNS-006 -> HRNS-007 Long-Horizon Orchestration
HRNS-002 + HRNS-005 + HRNS-006 -> HRNS-008 Harness Drift and Garbage Collection
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| HRNS-001 | Harness Surface Inventory and Gap Taxonomy | Pending | - | Ready to scaffold from this PRD/roadmap |
| HRNS-002 | Progressive Context and Durable State Contract | Pending | - | Blocked by HRNS-001 |
| HRNS-003 | Helper, Tool, and Capability Contract | Pending | - | Blocked by HRNS-001 |
| HRNS-004 | Permission, Sandbox, and Pre-action Authorization Controls | Pending | - | Blocked by HRNS-003 |
| HRNS-005 | Feedback Sensors and Eval Readiness Ladder | Pending | - | Blocked by HRNS-001 and HRNS-003 |
| HRNS-006 | Trace, Debug, and Review Evidence Packets | Pending | - | Blocked by HRNS-003, HRNS-004, and HRNS-005 |
| HRNS-007 | Long-horizon Orchestration and Resumption Controls | Pending | - | Blocked by HRNS-002 and HRNS-006 |
| HRNS-008 | Harness Drift, Garbage Collection, and Self-healing Remediation | Pending | - | Blocked by HRNS-002, HRNS-005, and HRNS-006 |

**Status Legend:** Pending | Ready | In Progress | In Review | Complete | Complete / Archived | Blocked

---

## Specification Sections

### HRNS-001: Harness Surface Inventory and Gap Taxonomy

**Priority:** P1 | **Depends On:** None | **Enables:** HRNS-002, HRNS-003, HRNS-005, HRNS-008

**Goal:** Create the durable surface inventory and gap taxonomy that downstream
HRNS specs use to avoid rediscovering workflow boundaries.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 260 |
Production files: 4 |
Total files: 8 |
Budget result: within budget

**Scope:**

- Create a durable taxonomy artifact that records SpecKit Pro harness surfaces,
  current-state boundaries, known gaps, owner workflows, and downstream spec
  ownership.
- Map retained concepts to SpecKit Pro surfaces: skills, agents, commands,
  helpers, runner, generated payloads, docs, workflow files, PR packets, tests,
  evals, and release gates.
- Define the gap taxonomy used by later specs: context, tool contract,
  permission, sandbox, memory/state, orchestration, verification,
  observability, HITL, security, and garbage collection.
- Record dependency posture: repo-local convention, runner/helper change,
  generated-doc/test change, or explicit future dependency decision.

**Out of Scope:**

- Editing runtime helpers, policy enforcement, or eval gates; handled by later
  HRNS specs.
- Building runtime helper, policy, trace, or eval behavior; handled by later
  HRNS specs.

**Key Decisions:**

- The taxonomy is a planning artifact, not a runtime registry. Runtime metadata
  remains owned by the runner/helper contract specs.

**Key Files:**

- `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` - Durable harness
  surface inventory and gap taxonomy.
- `docs/prd-harness-engineering-uplift.md` - PRD crosswalk updates if needed.
- `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` - Roadmap
  updates if evidence changes spec boundaries.

**Done When:**

- A durable taxonomy artifact exists and covers every SpecKit Pro harness surface
  named in PRD AC-1.*.
- Each retained gap has surface tags, state classification, owner workflow, and
  downstream HRNS ownership.
- The PR packet includes the taxonomy path, review scope, verification command or
  docs-only check, and any intentionally deferred gaps.

---

### HRNS-002: Progressive Context and Durable State Contract

**Priority:** P1 | **Depends On:** HRNS-001 | **Enables:** HRNS-007, HRNS-008

**Goal:** Make SpecKit Pro workflow entrypoints short, repo-grounded maps that
externalize long-running state into durable artifacts.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 170 |
Production files: 5 |
Total files: 10 |
Budget result: within budget

**Scope:**

- Audit skill and workflow entrypoints for map-vs-manual behavior.
- Define required durable state artifacts for long-running PRD, scaffold,
  status, autopilot, resolve-pr, and archive flows.
- Add freshness checks for roadmap, workflow, feature pointer, generated
  payload, and archive pointer state.
- Document compaction/resume expectations: what must be in files, what may
  remain in chat, and what requires user confirmation.

**Out of Scope:**

- Implementing trace packet schema; handled by HRNS-006.
- Parallel worktree orchestration; handled by HRNS-007.

**Key Files:**

- `speckit-pro/skills/*/SKILL.md` - Entry-point guidance audit targets.
- `speckit-pro/skills/*/references/` - Progressive disclosure reference targets.
- `docs/ai/specs/.process/` - Workflow state examples and conventions.

**Done When:**

- Entry-point guidance distinguishes short maps from deeper references for each
  audited workflow.
- Durable state artifacts and freshness checks are specified for long-running
  PRD, scaffold, status, autopilot, resolve-pr, and archive flows.
- Verification includes a focused docs/reference check or fixture proving stale
  roadmap, workflow, feature, generated payload, or archive pointers are caught.

---

### HRNS-003: Helper, Tool, and Capability Contract

**Priority:** P1 | **Depends On:** HRNS-001 | **Enables:** HRNS-004, HRNS-005, HRNS-006

**Goal:** Normalize helper/tool contracts so agents can discover capabilities,
understand mutability, dry-run safely, and self-correct from structured errors.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 170 |
Production files: 5 |
Total files: 11 |
Budget result: within budget

**Scope:**

- Define a helper/tool registry contract with operation ID, purpose, mutability,
  input schema, output schema, exit behavior, artifacts, owner workflow, and
  generated docs/test linkage.
- Require dry-run/readiness behavior for mutating, networked, credentialed, or
  PR/release-emitting helpers.
- Align capability discovery guidance with TACD precedent: capability-first,
  schema-aware, and non-blocking where possible.
- Add remediation-message standards for helper errors.

**Out of Scope:**

- Enforcing permission policy; handled by HRNS-004.
- Adding new MCP server dependencies.

**Key Files:**

- `speckit-pro/speckit_pro_runner/helpers/` - Python helper registry and helper
  records.
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/` - Existing
  helper fixture pattern.
- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` -
  Capability-first guidance.

**Done When:**

- Helper/tool records declare operation ID, purpose, mutability, schemas, exit
  behavior, generated artifacts, and owner workflow.
- Mutating, networked, credentialed, and PR/release-emitting helpers expose
  dry-run or readiness behavior.
- Tests or generated-doc checks prove registry, docs, runner metadata, and
  fixtures cannot drift silently.

---

### HRNS-004: Permission, Sandbox, and Pre-action Authorization Controls

**Priority:** P1 | **Depends On:** HRNS-003 | **Enables:** HRNS-006, release-readiness hardening

**Goal:** Add structural helper risk metadata, runtime preflight, pre-action
authorization, safe-stop semantics, and protected harness-control boundaries.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 177 |
Production files: 5 |
Total files: 11 |
Budget result: within budget

**Scope:**

- Extend helper/tool risk records with read-only, mutating, destructive,
  idempotent, open-world, credential-bearing, private-data, untrusted-content,
  external-communication, networked, and approval-required flags.
- Define pre-action authorization for mutating helpers.
- Protect harness-control files from autonomous mutation during governed runs.
- Add runtime preflight checks for runner availability, helper registry checksum,
  sandbox/write-root posture, trace/audit sink, git cleanliness where required,
  network/offline posture, and credential scope.
- Define safe-stop semantics and reviewable autoheal expectations.

**Out of Scope:**

- Claiming native platform sandbox guarantees before XPLAT UAT proves them.
- Building enterprise policy engines or credential brokers.

**Key Files:**

- `speckit-pro/speckit_pro_runner/` - Runner preflight and helper authorization
  integration points.
- `speckit-pro/hooks/` - Hook and harness-control protection considerations.
- `speckit-pro/.codex-plugin/plugin.json` and
  `speckit-pro/.claude-plugin/plugin.json` - Plugin manifests.
- `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json` -
  Marketplace registries.

**Done When:**

- Helper/tool risk records include the required mutability, network, credential,
  private-data, destructive, and approval flags.
- Governed mutating helpers run through pre-action authorization with normalized
  arguments, cwd/worktree, path scope, branch state, credential, and network
  posture checks.
- Preflight, safe-stop, protected-surface, and autoheal behavior is covered by
  focused fixtures or runner/helper tests.

---

### HRNS-005: Feedback Sensors and Eval Readiness Ladder

**Priority:** P1 | **Depends On:** HRNS-001, HRNS-003 | **Enables:** HRNS-006, HRNS-008

**Goal:** Define fixture-first verification and eval expectations for SpecKit
Pro skills, helpers, workflows, and review packets.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 197 |
Production files: 6 |
Total files: 12 |
Budget result: within budget

**Scope:**

- Define the SpecKit Pro verification ladder: structural checks, fixture parity,
  deterministic regression tests, transcript/trace review, targeted evals,
  calibrated rubric review, and optional production-like monitoring.
- Add failure-derived fixture requirements and discard-rationale rules.
- Document LLM-as-judge boundaries and calibration expectations.
- Define HITL eval requirements for Grill Me, scaffold, and autopilot flows.
- Ensure eval reports name model, skill version, runner/helper version, allowed
  tools, permission mode, and command/trace evidence.

**Out of Scope:**

- Full benchmark suite implementation.
- Blocking release gates on uncalibrated rubric review.

**Key Files:**

- `tests/speckit-pro/` - Existing layered test suite.
- `speckit-pro/skills/*/` - Skill-specific fixture/eval targets.
- `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` - Gap taxonomy
  from HRNS-001.

**Done When:**

- The verification ladder is documented from structural checks through calibrated
  rubric review, including when each layer is advisory or blocking.
- New or changed skill/helper behavior has a deterministic fixture/eval or a
  recorded discard rationale.
- Eval report fixtures include model, skill version, runner/helper version,
  allowed tools, permission mode, command evidence, and trace/debug evidence.

---

### HRNS-006: Trace, Debug, and Review Evidence Packets

**Priority:** P1 | **Depends On:** HRNS-003, HRNS-004, HRNS-005 | **Enables:** HRNS-007, HRNS-008

**Goal:** Add bounded local trace/debug records and PR-packet summaries for
helper, workflow, eval, and delegated-agent behavior.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 190 |
Production files: 6 |
Total files: 12 |
Budget result: within budget

**Scope:**

- Define JSONL trace records for helper and workflow runs.
- Add compact markdown debug summaries for PR packets.
- Standardize failure classification across context, constraint, permission,
  infrastructure, verification, planning, implementation, and external
  dependency layers.
- Keep traces local by default and avoid remote telemetry unless explicitly
  configured.
- Preserve multi-agent/delegation lineage where available.

**Out of Scope:**

- Integrating third-party tracing SaaS.
- Persisting secrets, raw credentials, or direct personal identifiers in traces.

**Key Files:**

- `speckit-pro/speckit_pro_runner/` - Trace emission integration points.
- `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` - PR packet
  summary integration target.
- `docs/ai/specs/.process/` - Workflow trace summary conventions.

**Done When:**

- Trace/debug record schemas cover helper and workflow runs with request ID,
  workflow, selected tool/helper, normalized inputs, authorization decision,
  timestamps, status, artifact paths, and safe-stop reason.
- PR packet summaries include compact trace/debug evidence without raw log dumps
  or secrets.
- Failure classification and replay/reproduction expectations are covered by
  focused fixtures or PR-packet validation.

---

### HRNS-007: Long-horizon Orchestration and Resumption Controls

**Priority:** P2 | **Depends On:** HRNS-002, HRNS-006 | **Enables:** safer multi-agent/autopilot operation

**Goal:** Harden long-running SpecKit Pro workflows with explicit checkpoints,
file ownership, worktree boundaries, planner/evaluator separation, and stop
conditions.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 230 |
Production files: 7 |
Total files: 14 |
Budget result: within budget

**Scope:**

- Define resumable checkpoint and next-action state for long-running workflows.
- Require parallel work declarations: file ownership, dependency edges,
  worktree/branch boundaries, and review order.
- Separate planner, generator, and evaluator roles for high-risk or long-running
  flows.
- Detect stale, partial, or conflicting checkpoints before resume.
- Define cost, time, scope, and progress caps plus continuation plans for
  inspection and eval jobs.
- Keep latest user instruction precedence explicit after interruptions and
  compactions.

**Out of Scope:**

- Building a new external task scheduler.
- Replacing Codex/Claude native thread or worktree management.

**Key Files:**

- `speckit-pro/skills/speckit-autopilot/` - Autopilot orchestration guidance and
  scripts.
- `speckit-pro/agents/` - Planner/evaluator role guidance.
- `docs/ai/specs/.process/` - Workflow state and checkpoint examples.

**Done When:**

- Long-running workflows record checkpoint, next-action, file ownership,
  branch/worktree, dependency, stop-condition, and continuation state in durable
  artifacts.
- Planner, generator, and evaluator handoff boundaries are explicit for high-risk
  or long-running flows.
- Resume checks reject stale, partial, conflicting, or user-instruction-stale
  state before work continues.

---

### HRNS-008: Harness Drift, Garbage Collection, and Self-healing Remediation

**Priority:** P2 | **Depends On:** HRNS-002, HRNS-005, HRNS-006 | **Enables:** ongoing harness maintenance

**Goal:** Add a bounded, repo-evidence-backed garbage-collection loop for stale or
contradictory harness artifacts.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 190 |
Production files: 6 |
Total files: 12 |
Budget result: within budget

**Scope:**

- Define a drift scanner for stale docs, roadmap pointers, examples, generated
  payloads, skill guidance, helper references, and workflow artifacts.
- Require concrete repo evidence for every cleanup finding.
- Output bounded remediation batches or no-op archives.
- Distinguish load-bearing prompts/hooks/helpers from dead weight left by older
  model limitations.
- Ensure self-healing remediation produces reviewable diffs or explicit no-op
  evidence instead of silent policy/helper rewrites.

**Out of Scope:**

- Broad speculative docs cleanup.
- Automated mutation of protected harness-control files without review.

**Key Files:**

- `docs/ai/specs/` and `docs/ai/specs/.process/` - Roadmap/workflow drift
  targets.
- `speckit-pro/skills/` - Skill guidance drift targets.
- `speckit-pro/speckit_pro_runner/` - Helper/runner drift targets.
- `.specify/memory/archive-reports/` - Archive and recovery precedent.

**Done When:**

- A bounded scanner or checklist identifies stale docs, roadmap pointers,
  examples, generated payloads, skill guidance, helper references, and workflow
  artifacts with concrete repo evidence.
- Cleanup output is split into reviewable remediation batches or an explicit
  no-op archive.
- Protected harness-control file changes require reviewable diffs, trace
  evidence, and human-visible remediation artifacts.

---

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Runtime substrate | Python 3.11+ standard-library runner from the XPLAT lane remains the target for installed-plugin helper behavior. |
| Test suite | `bash tests/speckit-pro/run-all.sh` default deterministic layers; focused layers as needed during implementation. |
| Existing helper pattern | XPLAT-005 read-only helper registry, Python-authoritative helper records, request fixtures, and parity checks. |
| Source-of-truth docs | `AGENTS.md`, `CLAUDE.md`, `.specify/memory/constitution.md`, PRDs, technical roadmaps, roadmap MOCs, and workflow files. |

## Scaffold Notes

- Start with `HRNS-001` so later specs share one durable harness taxonomy.
- Avoid editing active XPLAT runtime files from HRNS specs unless the selected
  HRNS spec explicitly owns a helper/runner contract change.
- Preserve the current `specs/` archive hygiene pattern: active spec folders are
  temporary implementation artifacts and should be archived after merge.

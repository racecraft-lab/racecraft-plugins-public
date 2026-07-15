# SpecKit Pro Harness Engineering Uplift Implementation Roadmap

**Turn SpecKit Pro harness needs into reviewable hardening specs for context,
tools, permissions, evals, traces, orchestration, portable knowledge, and drift
repair.**

This document defines the **SPEC catalog** for the harness-engineering uplift:
an ordered set of specifications derived from the source PRD. Each SPEC maps
1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving
traceability from PRD -> roadmap -> spec. Each specification is prepared for
implementation with `$speckit-scaffold-spec HRNS-###`, which reads this roadmap
as its input.

**Source PRD:** [../../prd-harness-engineering-uplift.md](../../prd-harness-engineering-uplift.md)
**Roadmap MOC:** [harness-engineering-uplift-roadmap-MOC.md](harness-engineering-uplift-roadmap-MOC.md)
**Spec ID prefix:** `HRNS-###`
**Status:** Draft. Added 2026-07-03 and updated 2026-07-15 to include the pinned
OKF v0.1 projection, intake, and reconciliation lane.

---

## Roadmap Overview

The feature is decomposed into **11 specifications** across **8 spec dependency
tiers**. A separate follow-on scaffold lane turns accepted roadmap items into
reviewable implementation branches.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | HRNS-001 | Inventory harness surfaces and classify SpecKit Pro gaps | Sequential foundation |
| 2 | HRNS-002, HRNS-003 | Durable context/state and helper/tool contract foundations | Parallel after HRNS-001 |
| 3 | HRNS-004, HRNS-005 | Permission/sandbox controls and eval readiness | Parallel after HRNS-003 where needed |
| 4 | HRNS-006 | Trace/debug packet contract spanning helpers, evals, and permissions | Sequential after HRNS-003 through HRNS-005 |
| 5 | HRNS-007, HRNS-009 | Long-horizon orchestration and canonical OKF projection | Parallel after shared foundations through HRNS-006 |
| 6 | HRNS-010 | Guarded external OKF intake and validation | Sequential after controls, sensors, evidence, and projection |
| 7 | HRNS-011 | Conflict-aware reconciliation and reviewable write-back | Sequential after orchestration and intake |
| 8 | HRNS-008 | Harness drift and garbage-collection remediation loop | Final maintenance layer after OKF synchronization contracts |

**Follow-on scaffold lane:** After maintainers accept this roadmap, scaffold ready
HRNS specs as reviewable implementation branches in the selected priority order.

**Execution Order:** HRNS-001 -> HRNS-002 + HRNS-003 -> HRNS-004 + HRNS-005 ->
HRNS-006 -> HRNS-007 + HRNS-009 -> HRNS-010 -> HRNS-011 -> HRNS-008

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
- HRNS-009 requires HRNS-001 through HRNS-006 foundations because canonical
  source classification, durable mapping state, governed operation contracts,
  authorization, conformance sensors, and provenance traces must exist before
  projection becomes an installed harness capability. It can proceed in
  parallel with HRNS-007 after HRNS-006.
- HRNS-010 requires HRNS-004, HRNS-005, HRNS-006, and HRNS-009 because untrusted
  intake needs protected-surface policy, pinned conformance and health checks,
  trace evidence, and the local bundle profile it consumes.
- HRNS-011 requires HRNS-007 and HRNS-010 because safe write-back needs resumable
  branch/worktree orchestration and a validated, provenance-preserving staged
  bundle.
- HRNS-008 requires HRNS-002, HRNS-005, HRNS-006, HRNS-009, HRNS-010, and
  HRNS-011 because final drift maintenance must understand context state,
  verification, traces, generated projections, staged intake, and
  reconciliation/write-back evidence.

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
- Preserve warmed-up context deliberately: task-scoped checkpoints, summaries,
  context-health signals, and restoration rules prevent useful understanding
  from living only in chat.
- Keep task focus explicit: active task/spec instructions should be swappable
  without mutating canonical project guidance, dirtying the worktree, or leaking
  stale context into unrelated workflows.
- Define tool/helper interfaces as agent UX: names, schemas, mutability,
  remediation messages, and result size affect reliability.
- Put humans on meaningful loop points: scope, plan, high-risk tool use,
  memory/policy writes, and final review.
- Layer verification: deterministic checks first, fixture parity next,
  trace/transcript review where useful, and calibrated rubric review only where
  deterministic checks cannot cover the risk.
- Bounded self-improvement loops: agents may generate, critique, refine, and test
  their own proposed harness changes only within explicit scopes, budgets,
  traces, rollback checkpoints, and human-visible promotion gates.
- Make security policy structural: least privilege, pre-action authorization,
  protected harness-control files, default-deny posture, and safe stop.
- Emit local trace/debug packets so failures can be classified and replayed
  without dumping raw logs into PRs.
- Add garbage collection because prompts, docs, sensors, tests, generated
  payloads, and examples drift as models and workflows change.
- Evaluate modern harness-adjacent tools during execution, including schema
  validation, orchestration, eval, trace, guardrail, workflow-runtime, and
  coding-agent references, before deciding whether any optional adapter or
  dependency is justified.
- Keep the first-release implementation dependency posture conservative:
  repo-local contracts and Python runner/helper surfaces first, with any larger
  runtime dependency requiring its own explicit decision.
- Treat knowledge portability as a governed harness surface: canonical source
  discovery, deterministic projection, validation, provenance, reconciliation,
  conflict decisions, and write-back evidence all need named owners.
- Preserve one authoritative knowledge layer. OKF is an on-demand interchange
  projection, not a migration target or committed mirror of repository docs.
- Apply identical knowledge contracts to Claude Code and Codex so distribution
  wrappers cannot change validity, safety, preservation, or conflict behavior.

## OKF v0.1 Compatibility Profile

The OKF lane uses the following decisions as scaffold-time constraints:

- **Normative authority:** Full conformance targets
  [OKF v0.1 `SPEC.md`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/d44368c15e38e7c92481c5992e4f9b5b421a801d/okf/SPEC.md)
  pinned at commit `d44368c15e38e7c92481c5992e4f9b5b421a801d`.
  Moving the pin is a reviewed compatibility change. Google Cloud reference
  agents, validator, server, client, and UI are interoperability evidence, not
  normative dependencies.
- **Authority and lifecycle:** Canonical repository documents remain the source
  of truth. Projection output is deterministic, on demand, disposable, and
  excluded from recursive source discovery; the roadmap does not introduce a
  committed duplicate knowledge tree.
- **Canonical coverage:** Inventory root and nested `AGENTS.md`, `CLAUDE.md`, and
  `GEMINI.md`; `.specify/memory/constitution.md`; PRDs; technical roadmaps;
  roadmap MOCs; and workflow/process docs. Generated distributions, caches,
  fixtures, installed payloads, and projection output are derived/non-canonical
  unless a future reviewed decision says otherwise.
- **Producer profile:** Emit valid UTF-8 Markdown concepts with YAML
  frontmatter, the required `type`, and recommended title, description,
  resource, tags, or timestamp only where canonical evidence supports them.
  Stable source mapping and identity rules prevent filename collisions.
- **Consumer profile:** Accept the minimum valid `type`-only concept, unknown
  concept types, unknown frontmatter fields, and both legal OKF link forms.
  Preserve extensions and bodies through staging/reconciliation; lossy handling
  is blocking.
- **Version, index, and log interpretation:** Record the pinned profile/spec
  version at the bundle manifest/root-index scope without imposing a `version`
  field on ordinary concepts beyond the normative spec. Emit indexes for
  progressive disclosure. Any log is optional derived history, not authority.
- **Link portability:** Emit relative internal links so raw repository and local
  renderers remain portable. Intake accepts both pinned-spec forms, reports
  broken or ambiguous targets, and never fetches a target automatically.
- **Conformance versus health:** Structural validity follows the pinned spec.
  Spec-defined soft conditions remain warnings. Broken links, missing useful
  indexes, stale or contradictory claims, citation quality, and coverage are a
  separate health/hygiene report.
- **Untrusted intake:** External frontmatter, Markdown, links, citations, and
  command-like text are data, not instructions. Intake is bounded,
  workspace-confined, local-first, and network-disabled by default.
- **Bidirectional synchronization:** Reconcile recorded base, current canonical
  source, and incoming staged knowledge. Materialize approved changes only as a
  bounded proposal in a new branch/worktree with review evidence; never write
  directly to the active branch or auto-merge.
- **Conflict and deletion policy:** If local and incoming content both changed,
  preserve both and stop for an explicit decision. Timestamps never choose the
  winner. Omission never means deletion; require an explicit tombstone/deletion
  proposal and human approval.
- **Distribution parity:** Claude Code and Codex may expose native wrappers, but
  operation schemas, safety metadata, profile pin, results, fixtures, and trace
  semantics must remain equivalent.

---

## Dependency Graph

```text
HRNS-001 -> HRNS-002 Progressive Context and Durable State
HRNS-001 -> HRNS-003 Helper, Tool, and Capability Contract
HRNS-003 -> HRNS-004 Permission, Sandbox, and Authorization
HRNS-001 + HRNS-003 -> HRNS-005 Feedback Sensors and Eval Readiness
HRNS-003 + HRNS-004 + HRNS-005 -> HRNS-006 Trace, Debug, and Review Evidence Packets
HRNS-002 + HRNS-006 -> HRNS-007 Long-Horizon Orchestration
HRNS-001 + HRNS-002 + HRNS-003 + HRNS-004 + HRNS-005 + HRNS-006 -> HRNS-009 OKF Canonical Projection
HRNS-004 + HRNS-005 + HRNS-006 + HRNS-009 -> HRNS-010 Guarded OKF Intake
HRNS-007 + HRNS-010 -> HRNS-011 Conflict-aware Reconciliation and Write-back
HRNS-002 + HRNS-005 + HRNS-006 + HRNS-009 + HRNS-010 + HRNS-011 -> HRNS-008 Harness Drift and Garbage Collection
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
| HRNS-008 | Harness Drift, Garbage Collection, and Self-healing Remediation | Pending | - | Final layer; blocked by HRNS-002, HRNS-005, HRNS-006, and HRNS-009 through HRNS-011 |
| HRNS-009 | OKF v0.1 Canonical Knowledge Projection | Pending | - | Blocked by HRNS-001 through HRNS-006 |
| HRNS-010 | Guarded External OKF Intake and Validation | Pending | - | Blocked by HRNS-004, HRNS-005, HRNS-006, and HRNS-009 |
| HRNS-011 | Conflict-aware OKF Reconciliation and Reviewable Write-back | Pending | - | Blocked by HRNS-007 and HRNS-010 |

**Status Legend:** Pending | Ready | In Progress | In Review | Complete | Complete / Archived | Blocked

---

## Specification Sections

### HRNS-001: Harness Surface Inventory and Gap Taxonomy

**Priority:** P1 | **Depends On:** None | **Enables:** HRNS-002, HRNS-003, HRNS-005, HRNS-009

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
- Inventory every canonical knowledge source eligible for projection and
  explicitly classify generated distributions, caches, fixtures, and other
  derived copies as non-canonical inputs.
- Define the gap taxonomy used by later specs: context, tool contract,
  permission, sandbox, memory/state, orchestration, verification,
  observability, HITL, security, and garbage collection.
- Record dependency posture: repo-local convention, runner/helper change,
  generated-doc/test change, or explicit future dependency decision.
- Add an external-candidate evaluation matrix covering relevant schema,
  orchestration, eval, trace/observability, guardrail, workflow-runtime, and
  coding-agent harness and knowledge-format references. Each row records mapped
  HRNS surfaces, local-first fit, runtime dependency posture,
  telemetry/privacy posture, licensing/supply-chain risk, normative/reference
  status, compatibility gaps, and recommendation.
- Classify self-improvement loop closure for workflows that can generate future
  harness behavior: human-in-the-loop, human-on-the-loop, fully automated, or
  disallowed. Flag open-ended recursive self-improvement and self-modifying
  harness-control loops as disallowed unless a dedicated future spec proves
  bounded safety controls.

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
- The taxonomy includes the external-candidate matrix needed by HRNS-003,
  HRNS-004, HRNS-005, HRNS-006, HRNS-007, HRNS-008, HRNS-009, HRNS-010, and
  HRNS-011 before those specs make implementation or dependency decisions.
- Canonical source coverage and exclusions include agent guidance,
  constitution, PRDs, technical roadmaps, MOCs, workflow/process docs, generated
  distribution copies, caches, fixtures, and on-demand projection artifacts.
- The OKF evaluation row records the pinned normative revision, draft maturity,
  reference-tooling posture, known compatibility gaps, and full-conformance
  decision used by HRNS-009 and HRNS-010.
- The taxonomy names every self-improvement loop class discovered in current
  skills, agents, helpers, generated payloads, evals, and workflow files, and
  records its permitted closure level or disallowed status.
- Each retained gap has surface tags, state classification, owner workflow, and
  downstream HRNS ownership.
- The PR packet includes the taxonomy path, review scope, verification command or
  docs-only check, and any intentionally deferred gaps.

---

### HRNS-002: Progressive Context and Durable State Contract

**Priority:** P1 | **Depends On:** HRNS-001 | **Enables:** HRNS-007, HRNS-008, HRNS-009

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
- Define task-scoped context checkpoint metadata: name, summary, message/source
  count where available, timestamp, task/spec association, storage class,
  provenance, restore instructions, and whether the checkpoint is personal,
  shared, or emergency fallback.
- Define context-health monitoring signals for long runs: healthy/degrading/
  critical zones, baseline token count, burn-rate estimate, save recommendation,
  and fresh-session recommendation before compaction or recall degradation
  silently affects decisions.
- Define active task/spec instruction semantics: canonical shared guidance,
  generated task-specific guidance, injected resume context, and default/fresh
  task state must be distinguishable and switchable without changing root
  instructions or producing accidental PR diffs.
- Define canonical-source authority versus disposable generated projections,
  including source discovery, explicit exclusions, stable concept identity,
  source digests, mapping/base state, and partial-operation recovery.

**Out of Scope:**

- Implementing trace packet schema; handled by HRNS-006.
- Parallel worktree orchestration; handled by HRNS-007.
- Committing raw personal transcripts or emergency auto-saves as shared team
  context artifacts.

**Key Files:**

- `speckit-pro/skills/*/SKILL.md` - Entry-point guidance audit targets.
- `speckit-pro/skills/*/references/` - Progressive disclosure reference targets.
- `docs/ai/specs/.process/` - Workflow state examples and conventions.

**Done When:**

- Entry-point guidance distinguishes short maps from deeper references for each
  audited workflow.
- Durable state artifacts and freshness checks are specified for long-running
  PRD, scaffold, status, autopilot, resolve-pr, and archive flows.
- Context checkpoint metadata, storage class, health-zone thresholds, and
  restore semantics are specified for long-running workflows.
- Task/spec switching records the active focus and rejects stale injected context
  before resume without mutating canonical project guidance.
- Projection/synchronization state distinguishes canonical source, generated
  artifact, recorded base, and staged external input, and cannot elevate a
  partial or committed projection into source-of-truth status.
- Verification includes a focused docs/reference check or fixture proving stale
  roadmap, workflow, feature, generated payload, or archive pointers are caught.

---

### HRNS-003: Helper, Tool, and Capability Contract

**Priority:** P1 | **Depends On:** HRNS-001 | **Enables:** HRNS-004, HRNS-005, HRNS-006, HRNS-009

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
- Evaluate schema and tool-contract references: Pydantic, JSON Schema/OpenAPI,
  LangChain structured-output/tool schemas, OpenAI Agents SDK function-tool
  schemas, and existing repo-local runner metadata. Record whether SpecKit Pro
  should keep schemas Python-authoritative, generate machine-readable schemas,
  or introduce an optional validation adapter.
- Reserve separate operation contracts for canonical-to-OKF projection,
  validation/intake, reconciliation planning, and approved write-back proposal
  materialization. Include schemas, mutability, path/network posture, artifacts,
  exit states, and Claude/Codex parity requirements without implementing the OKF
  operations in this foundational spec.

**Out of Scope:**

- Enforcing permission policy; handled by HRNS-004.
- Adding new MCP server dependencies.
- Adding Pydantic or any other schema library as a required installed-plugin
  runtime dependency without a dedicated dependency decision.

**Key Files:**

- `speckit-pro/speckit_pro_runner/helpers/` - Python helper registry and helper
  records.
- `tests/speckit-pro/unit/fixtures/read-only-helpers/` - Existing
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
- A schema-contract decision names the canonical source of truth, generated
  artifact format, validation path, dependency posture, and fixtures proving
  contract drift is detected.
- The registry can represent the four future OKF operations and their
  type-only/unknown-extension/link-preservation expectations without coupling
  them to Google reference tooling or distribution-specific semantics.

---

### HRNS-004: Permission, Sandbox, and Pre-action Authorization Controls

**Priority:** P1 | **Depends On:** HRNS-003 | **Enables:** HRNS-006, HRNS-009, HRNS-010, release-readiness hardening

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
- Compare permission and guardrail patterns from OpenAI Agents SDK, Guardrails
  AI, Semantic Kernel, promptfoo red-team flows, OpenHands/SWE-agent-style
  coding-agent sandboxes, and existing Codex/Claude permission semantics. Keep
  SpecKit Pro authorization local and reviewable.
- Define shared-context promotion gates: secret scan, size cap, provenance
  check, storage-class check, human confirmation, and clean git-footprint
  behavior before any context checkpoint is committed or distributed to a team.
- Classify external OKF bundles and all embedded text as untrusted data, then
  define bounded-input, path-normalization, workspace-confinement, symlink,
  parser-abuse, secret, and network-disabled controls for later intake.
- Protect canonical knowledge documents, source mappings, and reconciliation
  base state from direct external write-back; only an isolated reviewable
  proposal may request changes or explicit deletions.

**Out of Scope:**

- Claiming native platform sandbox guarantees before XPLAT UAT proves them.
- Building enterprise policy engines or credential brokers.
- Treating personal context captures, emergency auto-saves, or raw transcripts
  as safe to commit by default.

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
- A guardrail/policy comparison records which patterns are borrowed, rejected,
  or deferred and confirms that external services do not own authorization
  decisions for installed-plugin operations.
- Shared-context promotion guidance includes explicit block/warn behavior for
  secrets, oversize artifacts, missing provenance, and accidental personal-state
  diffs.
- External-knowledge policy rejects instruction execution, automatic resource
  fetching, timestamp-based conflict authority, deletion by omission,
  write-scope expansion, and self-merging proposals.

---

### HRNS-005: Feedback Sensors and Eval Readiness Ladder

**Priority:** P1 | **Depends On:** HRNS-001, HRNS-003 | **Enables:** HRNS-006, HRNS-008, HRNS-009, HRNS-010

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
- Define clean-context adversarial review expectations for PRDs, test plans, dev
  plans, generated fixtures, and self-improvement outputs so review does not
  inherit the authoring session's blind spots.
- Define docs-before-code feedback expectations for user/operator workflow
  changes where applicable, including when docs are regenerated, intentionally
  deferred, or not applicable.
- Define process-sequencing gates that detect stale downstream artifacts after
  PRD or roadmap changes: docs, test plan, dev plan, generated fixtures,
  adversarial inventory, and risk acceptances.
- Define test/eval inventory expectations: every row states what the test
  actually verifies, which acceptance criterion it maps to, and a verdict of
  pass, fail, escalate, or accepted.
- Evaluate promptfoo, Braintrust, Phoenix, LangSmith, Langfuse, Inspect AI,
  DSPy, and repo-local deterministic fixtures as possible eval surfaces.
  Classify each candidate by local/offline fit, SaaS or external telemetry
  behavior, LLM-as-judge calibration needs, CI fit, and optional-adapter
  viability.
- Define the evaluator hierarchy for bounded self-improvement: deterministic
  tests, formal or executable verifiers, and fixture parity outrank calibrated
  rubrics and LLM judges; intrinsic self-assessment may propose changes but
  cannot approve harness-control changes.
- Define the version-pinned OKF conformance-corpus contract needed by HRNS-009
  and HRNS-010: positive/negative, minimum-valid, unknown-extension, index, log,
  link, encoding, and round-trip cases derived from the normative spec.
- Separate structural conformance from health/hygiene findings such as broken
  links, missing useful indexes, stale or contradictory claims, weak citations,
  and coverage gaps. Keep spec-defined soft conditions non-blocking.
- Define equivalent Claude Code and Codex fixture expectations and advisory
  differential checks against Google reference tooling without letting a
  stricter reference validator redefine validity.

**Out of Scope:**

- Full benchmark suite implementation.
- Blocking release gates on uncalibrated rubric review.
- Treating self-assessment, self-scoring, or self-generated tests as sufficient
  evidence for promotion.
- Letting an adversarial reviewer auto-fix findings in the same isolated review
  pass.
- Treating stale docs, stale test plans, stale dev plans, or stale adversarial
  inventories as safe defaults after PRD/roadmap changes.

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
- The eval-surface comparison recommends which candidates should be reference
  patterns, optional adapters, rejected dependencies, or future spikes.
- Self-improvement evaluator guidance states which signals are blocking,
  advisory, or disallowed and includes at least one failure mode for
  self-confirming loops, reward/eval tampering, or synthetic-fixture drift.
- Adversarial review guidance requires fresh isolated context, findings-first
  output, and explicit risk acceptances for unresolved issues.
- Process sequencing guidance names the stale-artifact checks, force/acceptance
  behavior, and required review packet evidence.
- Test/eval inventory guidance includes banned vacuous patterns such as
  placeholder assertions, broad OR fallbacks, conditional file-existence guards,
  and self-fulfilling setup.
- The OKF corpus can distinguish pinned-spec failures, soft warnings, health
  findings, extension-preservation regressions, reference-tool differences, and
  Claude/Codex parity failures.

---

### HRNS-006: Trace, Debug, and Review Evidence Packets

**Priority:** P1 | **Depends On:** HRNS-003, HRNS-004, HRNS-005 | **Enables:** HRNS-007, HRNS-008, HRNS-009, HRNS-010

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
- Map the local JSONL trace vocabulary to OpenTelemetry/OpenInference-compatible
  concepts where useful, and evaluate optional sinks such as LangSmith,
  Langfuse, Phoenix, and Braintrust without making external telemetry the
  canonical record.
- Add trace fields for bounded self-improvement iterations:
  generate->critique->refine->verify step, prompt/input provenance, changed
  artifacts, evaluator result, stop reason, checkpoint, rollback path, and human
  approval state.
- Add trace fields for context continuity: active checkpoint ID or warm-up
  baseline, context-health zone, burn-rate estimate where available,
  compaction/auto-save event, restore source, and whether the source was named,
  workflow-derived, or emergency fallback.
- Reserve OKF trace fields for normative spec/profile revision, repository and
  source revisions, source/bundle digests, source-to-concept identity, base
  mapping, distribution surface, validation results, preserved extensions,
  normalization, reconciliation classification, and operator decisions.

**Out of Scope:**

- Integrating third-party tracing SaaS.
- Persisting secrets, raw credentials, or direct personal identifiers in traces.

**Key Files:**

- `speckit-pro/speckit_pro_runner/` - Trace emission integration points.
- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` - PR packet summary
  integration target.
- `docs/ai/specs/.process/` - Workflow trace summary conventions.

**Done When:**

- Trace/debug record schemas cover helper and workflow runs with request ID,
  workflow, selected tool/helper, normalized inputs, authorization decision,
  timestamps, status, artifact paths, and safe-stop reason.
- PR packet summaries include compact trace/debug evidence without raw log dumps
  or secrets.
- Failure classification and replay/reproduction expectations are covered by
  focused fixtures or PR-packet validation.
- Trace schema fixtures show the local canonical record and any optional
  export/sink mapping separately, including telemetry, secret, and retention
  boundaries.
- Self-improvement trace fixtures prove each iteration can be replayed or
  rejected without raw log dumps, secrets, or reliance on chat history alone.
- Context-continuity fixtures prove compaction/resume evidence can be summarized
  without committing raw personal transcripts or leaking secrets.
- OKF trace fixtures can reproduce projection/intake decisions and later connect
  each proposed canonical diff to base/local/incoming evidence without storing
  unbounded imported content or secrets.

---

### HRNS-007: Long-horizon Orchestration and Resumption Controls

**Priority:** P2 | **Depends On:** HRNS-002, HRNS-006 | **Enables:** HRNS-011, safer multi-agent/autopilot operation

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
- Compare orchestration and workflow-runtime references: LangGraph, OpenAI
  Agents SDK, AutoGen, Semantic Kernel, CrewAI, Haystack, Temporal, OpenHands,
  and SWE-agent-style agent-computer-interface patterns. Focus the comparison
  on checkpoint/resume, HITL, workspace isolation, role handoff, failure
  recovery, and long-running job control.
- Define bounded self-improvement orchestration controls: iteration budgets,
  resource caps, modification scope, rollback checkpoints, promotion gates,
  and safe-stop behavior for loops that generate, critique, refine, or test
  future harness behavior.
- Define reusable orchestration semantics for external-knowledge proposals:
  isolated branch/worktree creation, source and bundle revalidation, durable
  unresolved decisions, latest-user-instruction precedence, optional draft PR
  handoff, and separate authorization for commit/push/PR/merge/cleanup actions.

**Out of Scope:**

- Building a new external task scheduler.
- Replacing Codex/Claude native thread or worktree management.
- Allowing a loop to expand its own permissions, edit its own approval/eval
  gates, or merge/promote its own harness changes.

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
- The orchestration comparison recommends borrowed patterns and rejects or
  defers runtime dependencies that would conflict with local-first installed
  Claude/Codex plugin operation.
- Self-improvement loops record budget, scope, checkpoint, rollback, promotion,
  and safe-stop state before execution and reject stale or self-authorizing
  state before resume.
- Reviewable proposal orchestration cannot write to an existing operator branch,
  overwrite a competing proposal, auto-merge, or discard unresolved conflict
  evidence during resume or cleanup.

---

### HRNS-008: Harness Drift, Garbage Collection, and Self-healing Remediation

**Priority:** P2 | **Depends On:** HRNS-002, HRNS-005, HRNS-006, HRNS-009, HRNS-010, HRNS-011 | **Enables:** ongoing harness maintenance

**Goal:** Add the final bounded, repo-evidence-backed garbage-collection loop
for stale, contradictory, projected, imported, or reconciliation-derived harness
artifacts.

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
- Include external-candidate drift checks for stale reference docs, obsolete
  version assumptions, abandoned optional-adapter decisions, and dependency
  recommendations that no longer match roadmap evidence.
- Include self-generated harness artifacts in drift checks: prompts, fixtures,
  eval cases, traces, skill-library entries, generated docs, synthetic examples,
  and any agent-authored feedback memories used by later workflows.
- Include context checkpoint drift checks for stale, duplicate, oversized,
  secret-bearing, orphaned, or no-longer-load-bearing checkpoints and summaries.
- Detect OKF projection nondeterminism, incomplete canonical-source coverage,
  changed normative pins, stale source/base mappings, stale generated bundles,
  lost unknown extensions, and Claude/Codex contract divergence.
- Report structural conformance drift separately from broken links, missing
  useful indexes, stale/contradictory claims, citation quality, and other
  knowledge-health findings.
- Apply no-deletion-by-omission and explicit-tombstone rules during cleanup of
  imported concepts, source mappings, and reconciliation state.

**Out of Scope:**

- Broad speculative docs cleanup.
- Automated mutation of protected harness-control files without review.
- Reusing self-generated fixtures, evals, prompts, or skill-library artifacts as
  trusted evidence without external validation or explicit provenance.
- Deleting context checkpoints, emergency saves, or shared summaries without a
  dry-run preview and recovery evidence.
- Promoting a generated OKF artifact into canonical source status, moving the
  normative pin automatically, or deleting canonical content because an
  external bundle or stale projection omitted it.

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
- External-candidate findings are classified as update reference, re-evaluate
  dependency decision, archive rejected candidate, or no-op.
- Self-generated artifact findings are classified as externally validated,
  stale, duplicate, unsafe to reuse, cleanup candidate, or no-op archive.
- Context checkpoint findings are classified as active, stale, duplicate,
  oversized, secret-bearing, orphaned, cleanup candidate, or no-op archive.
- OKF findings classify projection, mapping, intake, reconciliation, extension,
  reference-tool, conformance, health, and distribution-parity drift separately
  and produce bounded reviewable remediation or no-op evidence.

---

### HRNS-009: OKF v0.1 Canonical Knowledge Projection

**Priority:** P2 | **Depends On:** HRNS-001, HRNS-002, HRNS-003, HRNS-004, HRNS-005, HRNS-006 | **Enables:** HRNS-010, HRNS-008

**Goal:** Project every canonical SpecKit Pro knowledge source into a
deterministic, on-demand bundle fully conforming to the pinned OKF v0.1
specification, with equivalent Claude Code and Codex behavior.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 255 |
Production files: 6 |
Total files: 14 |
Budget result: within budget

**Estimate Basis:** Reviewability estimator status `ok`: 2 stories, 12
functional requirements, 7 key files/surfaces, modify work, 1 suggested slice.

**Vertical-slice rationale:** Source discovery -> deterministic projection ->
conformance/health evidence is one independently valuable read-only capability;
splitting it would leave an unverifiable partial producer.

**Scope:**

- Implement the compatibility profile pinned to
  `d44368c15e38e7c92481c5992e4f9b5b421a801d`, with no Google reference runtime
  or external-service dependency.
- Discover all canonical sources from the HRNS-001 inventory: root and nested
  agent guidance, constitution, PRDs, technical roadmaps, MOCs, and
  workflow/process docs. Enforce explicit exclusions for derived copies.
- Generate stable concept paths/identities and a source mapping/manifest with
  repository revision, source paths/digests, profile revision, coverage, and
  exclusions.
- Emit minimum-valid concepts plus evidence-backed recommended metadata;
  preserve source structure and content without pretending inferred metadata is
  canonical fact.
- Emit navigation indexes for progressive disclosure, handle root profile/version
  metadata explicitly, and keep any generated log optional and derived.
- Emit portable relative internal links and source/citation provenance while
  detecting identity collisions and ambiguous targets deterministically.
- Run the pinned structural-conformance corpus and separate health/hygiene
  checks, preserving spec-defined warnings as non-blocking.
- Make output reproducible, local-only, network-free, disposable, and excluded
  from recursive source discovery or accidental source-of-truth promotion.
- Expose equivalent Claude Code and Codex operations, schemas, safety metadata,
  bundle semantics, diagnostics, and trace evidence.

**Out of Scope:**

- External bundle intake, reconciliation, or canonical write-back; handled by
  HRNS-010 and HRNS-011.
- In-place migration of canonical docs or a committed mirrored OKF tree.
- Adopting Google knowledge-catalog agents, validator, server, client, or UI as
  required installed-plugin runtime components.
- Automatically fetching resource or citation targets.

**Key Files / Surfaces:**

- `speckit-pro/speckit_pro_runner/` - Python-authoritative projection operation,
  profile metadata, source discovery, and deterministic artifact handling.
- `speckit-pro/skills/` and `speckit-pro/codex-skills/` - Claude Code and Codex
  install-facing operation guidance.
- `tests/speckit-pro/unit/` - Pinned conformance corpus, source coverage,
  determinism, link, collision, and distribution-parity fixtures.
- `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` - Canonical source
  inventory and OKF candidate posture from HRNS-001.

**Done When:**

- One local, read-only operation projects every inventoried canonical source or
  reports an explicit justified exclusion.
- The output conforms to the pinned OKF v0.1 spec, accepts the profile's
  minimum/extension rules, and emits structural and health results separately.
- Repeated runs from the same repository/profile input produce deterministic
  bundle content, mappings, coverage, and evidence.
- Generated output cannot become a recursive input or authoritative source and
  requires no network access or Google reference dependency.
- Claude Code and Codex parity fixtures prove equivalent source coverage,
  profile semantics, diagnostics, and traces.

---

### HRNS-010: Guarded External OKF Intake and Validation

**Priority:** P2 | **Depends On:** HRNS-004, HRNS-005, HRNS-006, HRNS-009 | **Enables:** HRNS-011, HRNS-008

**Goal:** Validate and stage external OKF v0.1 bundles as untrusted local data
without executing content, losing extensions, fetching links, or modifying
canonical repository state.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 262 |
Production files: 6 |
Total files: 14 |
Budget result: within budget

**Estimate Basis:** Reviewability estimator status `ok`: 2 stories, 13
functional requirements, 7 key files/surfaces, modify work, 1 suggested slice.

**Vertical-slice rationale:** Bounded preflight -> pinned validation -> normalized
staging/report is one safe read-only intake boundary; omitting any stage would
make the result unsafe or unusable by reconciliation.

**Scope:**

- Add a local-first, network-disabled intake operation using HRNS-003 operation
  contracts and HRNS-004 authorization/risk metadata.
- Enforce bounded bytes, files/concepts, nesting, document/frontmatter size,
  encoding, normalized path, symlink, duplicate identity, workspace escape, and
  parser/decompression-abuse controls before staging.
- Treat frontmatter, Markdown bodies, links, citations, resources, prompts, and
  command-like text as untrusted data that cannot invoke tools or change policy.
- Validate full pinned-spec conformance while reporting soft conditions and
  knowledge-health findings separately.
- Accept type-only concepts, unknown types/fields, and both legal link forms;
  preserve extensions, bodies, provenance, and bundle identity in normalized
  staged state.
- Record the intended repository/base revision and reject missing, ambiguous,
  stale, or mismatched source mappings before reconciliation eligibility.
- Treat omitted concepts as absence, not deletion; admit only explicit
  tombstone/deletion metadata to the later review path.
- Produce bounded redacted reports that distinguish malformed, unsafe,
  non-conformant, unhealthy, unsupported, and policy-denied input.
- Compare reference-tool results only as advisory interoperability evidence and
  expose equivalent Claude Code/Codex limits, results, and traces.

**Out of Scope:**

- Applying staged knowledge to canonical documents or creating a write-back
  branch/PR; handled by HRNS-011.
- Automatic resource/link/citation fetching, remote validation, or imported
  instruction execution.
- Silently normalizing away unknown types, unknown fields, unsupported
  extensions, provenance, or source content.
- Inferring deletions from missing concepts.

**Key Files / Surfaces:**

- `speckit-pro/speckit_pro_runner/` - Intake preflight, parser/validator,
  normalized staging artifact, and bounded diagnostics.
- `speckit-pro/skills/` and `speckit-pro/codex-skills/` - Claude Code and Codex
  intake guidance and approval boundaries.
- `tests/speckit-pro/unit/` - Positive/negative conformance, hostile-input,
  limit, extension-preservation, no-network, no-write, and parity fixtures.
- OKF v0.1 compatibility profile and HRNS-009 mapping/manifest contract -
  normative validation and base-state inputs.

**Done When:**

- Conformant minimum and extension-bearing bundles stage successfully with
  provenance intact; malformed or unsafe bundles fail before repository effects.
- No intake fixture can execute content, fetch a target, escape the workspace,
  mutate canonical state, or convert omission into deletion intent.
- Structural failures, soft warnings, health findings, policy denials, and
  reference-tool differences remain distinct in bounded reports.
- Failed/cancelled intake is a clean no-op apart from an approved diagnostic
  artifact.
- Claude Code and Codex fixtures prove identical limits, preservation,
  validation, evidence, and exit semantics.

---

### HRNS-011: Conflict-aware OKF Reconciliation and Reviewable Write-back

**Priority:** P2 | **Depends On:** HRNS-007, HRNS-010 | **Enables:** HRNS-008

**Goal:** Reconcile staged external knowledge against recorded base and current
canonical sources, then materialize only human-approved changes as an isolated,
reviewable branch/worktree proposal.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 290 |
Production files: 6 |
Total files: 15 |
Budget result: within budget

**Estimate Basis:** Reviewability estimator status `ok`: 2 stories, 14
functional requirements, 8 key files/surfaces, modify work, 1 suggested slice.

**Vertical-slice rationale:** Three-way classification -> explicit decisions ->
isolated proposal/evidence is one bounded write-back capability; splitting it
would leave either unactionable conflicts or an ungoverned mutation path.

**Scope:**

- Compare recorded base, current canonical source, and normalized incoming
  concepts using stable source mappings and digests.
- Classify unchanged, local-only, incoming-only, compatible add, conflict,
  explicit deletion proposal, unmapped, and invalid states before write-back.
- Preserve both sides and stop for an explicit decision whenever local and
  incoming content both changed; never use timestamps or distribution source as
  automatic conflict authority.
- Treat omission as absence. Require an explicit tombstone/deletion proposal
  with provenance, base evidence, dependent-link impact, and human approval.
- Persist accept/reject/edit/defer decisions and unresolved conflicts in a
  resumable bounded decision packet.
- Revalidate repository revision, bundle digest, specification pin, mappings,
  selected decisions, approved path scope, and latest user instruction before
  materializing output.
- Materialize approved changes only in a newly created isolated branch/worktree,
  limited to mapped canonical sources and approved additions, with a bounded
  diff, mapping updates, verification plan, and trace/review packet.
- Keep commit, push, draft-PR creation, promotion, merge, deletion, and cleanup
  as separately authorized actions; never merge or modify an existing operator
  branch automatically.
- Preserve unknown OKF extensions in staged/decision evidence and block any
  lossy canonical transform until an operator resolves it.
- Produce equivalent Claude Code and Codex classifications, stops, proposal
  diffs, decision state, and trace lineage.

**Out of Scope:**

- Unattended direct writes to the active branch, automatic PR promotion/merge,
  or autonomous conflict resolution.
- Timestamp-based last-write-wins, source-priority overwrite, or deletion by
  omission.
- Mutation of manifests, hooks, policy, helper registries, generated payloads,
  or unrelated paths through an imported knowledge proposal.
- Redesigning canonical source formats solely to fit external OKF extensions.

**Key Files / Surfaces:**

- `speckit-pro/speckit_pro_runner/` - Three-way classifier, decision packet,
  proposal materialization, revalidation, and trace lineage.
- `speckit-pro/skills/` and `speckit-pro/codex-skills/` - Human decision,
  worktree/branch, optional draft-PR, and resume guidance.
- `tests/speckit-pro/unit/` - Conflict matrix, tombstone, stale-base,
  path-scope, lossy-extension, no-auto-merge, resume, and parity fixtures.
- Canonical source mappings and HRNS-007 orchestration contracts - base state,
  isolation, action authorization, and cleanup boundaries.

**Done When:**

- The three-way classifier deterministically identifies all required states and
  never resolves a true conflict or deletion proposal without a human decision.
- Omission, timestamps, distribution source, and file order cannot authorize an
  overwrite or deletion.
- Approved changes appear only in a new isolated branch/worktree with bounded
  scope, source-linked diffs, mapping/base updates, verification, and trace
  evidence.
- Stale repository/bundle/mapping/decision/user-instruction state blocks
  materialization and preserves a safe resumable or cleanup path.
- Claude Code and Codex parity fixtures prove equivalent classifications,
  approvals, proposal output, failure stops, and review packets.

---

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Runtime substrate | Python 3.11+ standard-library runner from the XPLAT lane remains the target for installed-plugin helper behavior. |
| Test suite | `python3 tests/speckit-pro/run-all.py` default deterministic layers; focused Python validators as needed during implementation. |
| Existing helper pattern | XPLAT-005 read-only helper registry, Python-authoritative helper records, request fixtures, and parity checks. |
| Source-of-truth docs | Root/nested `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`; `.specify/memory/constitution.md`; PRDs; technical roadmaps; roadmap MOCs; and workflow/process docs. Generated distributions, caches, fixtures, installed payloads, and OKF projection output remain non-canonical. |
| Normative OKF profile | Full OKF v0.1 conformance pinned to knowledge-catalog `okf/SPEC.md` commit `d44368c15e38e7c92481c5992e4f9b5b421a801d`; reference tooling is interoperability evidence only. |
| OKF artifact posture | Deterministic on-demand projection, local-first and network-free by default, with explicit mappings/base state and no committed duplicate source tree. |
| Distribution contract | Claude Code and Codex wrappers share operation schemas, safety flags, conformance behavior, fixtures, and trace semantics. |

## Scaffold Notes

- Start with `HRNS-001` so later specs share one durable harness taxonomy.
- Proceed in dependency order: `HRNS-002` + `HRNS-003`, then `HRNS-004` +
  `HRNS-005`, then `HRNS-006`.
- `HRNS-007` and `HRNS-009` may scaffold in parallel after their shared
  foundations are complete because orchestration and read-only projection own
  separable primary surfaces.
- Do not scaffold `HRNS-010` before the projection profile/conformance evidence
  exists, or `HRNS-011` before guarded intake and reusable worktree/resume
  controls exist.
- Keep `HRNS-008` final so its drift taxonomy covers projection, intake,
  reconciliation, extension preservation, spec/reference drift, and both plugin
  distributions.
- Avoid editing active XPLAT runtime files from HRNS specs unless the selected
  HRNS spec explicitly owns a helper/runner contract change.
- Preserve the current `specs/` archive hygiene pattern: active spec folders are
  temporary implementation artifacts and should be archived after merge.

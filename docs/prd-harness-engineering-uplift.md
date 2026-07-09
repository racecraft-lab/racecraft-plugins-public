# PRD: SpecKit Pro Harness Engineering Uplift

**Status**: Draft
**Spec ID prefix**: `HRNS-###`
**Source**: Maintainer direction to harden SpecKit Pro harness behavior as
runner, helper, and long-running workflow surfaces expand.
**Created**: 2026-07-03
**Last updated**: 2026-07-04
**Target window**: Post-XPLAT helper migration hardening lane; should not block
the active XPLAT runtime cutover unless a scaffolded HRNS spec explicitly
finds a release-blocking harness safety gap.

---

## 1. Problem

> "How do we make SpecKit Pro's agent workflows legible, resumable, safe, and
> self-correcting as the plugin shifts from process docs into a real installed
> harness?"

SpecKit Pro already has strong workflow primitives: PRDs, technical roadmaps,
scaffolded specs, autopilot workflow files, helper parity tests, review packets,
and cross-platform runner work. The next risk is operational: once agents can
run longer, call more helpers, coordinate more subagents, and modify more repo
state, reliability depends less on one prompt and more on the surrounding
harness.

This PRD turns the needed harness primitives into an ordered SpecKit Pro
roadmap: progressive context, explicit tool contracts, durable state, permission
boundaries, feedback sensors, evals, traces, human checkpoints, and recurring
garbage collection. It does not require a heavyweight external harness
framework or broad vendor product dependency.

## 2. Goals & Non-goals

### 2.1 Goals

- Make every major SpecKit Pro workflow explain which harness primitive it uses:
  context, tool contract, state, permission, verification, trace, HITL, or
  cleanup.
- Convert harness needs into a durable surface inventory and gap taxonomy that
  future specs can use without rediscovering workflow boundaries.
- Evaluate comparable agent harness, orchestration, schema, eval, trace,
  guardrail, and workflow-runtime tools so the roadmap can borrow strong
  patterns without prematurely binding installed plugin behavior to them.
- Define runner/helper contracts with mutability, risk, preflight, output, trace,
  and review-packet behavior.
- Add layered feedback sensors: deterministic checks first, fixture parity next,
  transcript/trace review where needed, and calibrated rubric review only for
  subjective behavior.
- Define bounded self-improvement loops for safe agent self-correction:
  generate, critique, refine, verify, trace, and hand off without autonomous
  promotion.
- Make long-horizon workflows resumable from explicit state rather than chat
  history or local memory alone.
- Add a bounded harness garbage-collection loop for stale prompts, docs, skills,
  helper registries, traces, generated payloads, and obsolete examples.

### 2.2 Non-goals (out of scope)

- Replacing the active XPLAT Python runner lane. HRNS depends on XPLAT where it
  needs runner behavior, but does not choose a new runtime substrate.
- Adopting LangGraph, CrewAI, OpenHands, Temporal, Braintrust, Langfuse,
  Phoenix, LangSmith, OpenAI Agents SDK, AutoGen, Semantic Kernel, Haystack,
  DSPy, promptfoo, Inspect AI, Guardrails AI, Pydantic, or any other external
  harness platform/library as a required dependency without a dedicated spec,
  supply-chain review, privacy review, and rollback plan. Evaluating these tools
  as references, optional adapters, or decision candidates is in scope.
- Making public security claims beyond what the installed Claude/Codex plugin
  and native-platform UAT have actually verified.
- Creating a general agent benchmark suite. HRNS focuses on SpecKit Pro skill,
  helper, workflow, and review-packet behavior.
- Enabling open-ended recursive self-improvement, autonomous self-modification
  of harness-control files, autonomous permission expansion, autonomous
  promotion of agent-generated harness changes, or training/fine-tuning on
  self-generated artifacts without an explicit reviewed spec.
- Auto-fixing policy, permission, hook, MCP, or harness-control files without a
  reviewable diff and trace evidence.

## 3. Acceptance Criteria

### 3.1 Harness Surface Inventory and Gap Taxonomy *(-> HRNS-001)*

- **AC-1.1**: A durable harness surface inventory records the current SpecKit
  Pro skills, agents, commands, helpers, runner surfaces, generated payloads,
  docs, workflow files, PR packets, tests, evals, and release gates that can
  affect long-running agent behavior.
- **AC-1.2**: Every retained harness gap is tagged to at least one SpecKit Pro
  surface: skill, agent, command, helper, runner, generated payload, docs,
  workflow file, PR packet, test/eval, or release gate.
- **AC-1.3**: The taxonomy distinguishes context, tool contract, permission,
  sandbox, memory/state, orchestration, verification, observability, HITL,
  security, and garbage-collection gaps.
- **AC-1.4**: The taxonomy distinguishes implemented, planned, deferred,
  duplicate, obsolete, and unknown gaps so downstream specs do not treat every
  observation as implementation-ready.
- **AC-1.5**: The artifact records dependency posture: which gaps are handled by
  repo-local conventions, which need runner/helper changes, and which would
  require a dedicated dependency or supply-chain decision.
- **AC-1.6**: The artifact includes an external-candidate evaluation matrix for
  relevant harness libraries, frameworks, eval systems, trace/observability
  tools, guardrail systems, workflow runtimes, and coding-agent exemplars. Each
  candidate records category, mapped HRNS surfaces, local-first fit, runtime
  dependency posture, telemetry/privacy posture, licensing/supply-chain risk,
  and adoption recommendation.
- **AC-1.7**: The taxonomy records self-improvement loop closure for any
  workflow that can generate future harness behavior: human-in-the-loop,
  human-on-the-loop, fully automated, or disallowed. Open-ended recursive
  self-improvement and self-modifying harness-control loops are classified as
  disallowed unless a later dedicated spec proves bounded safety controls.

### 3.2 Progressive Context and Durable State Contract *(-> HRNS-002)*

- **AC-2.1**: SpecKit Pro entrypoints identify short "map" instructions and
  deeper just-in-time references instead of treating one large instruction file
  as the source of truth.
- **AC-2.2**: Long-running workflows have durable state artifacts for prompt,
  plan, implementation status, documentation/status updates, open questions,
  and done routine.
- **AC-2.3**: Context freshness checks detect stale roadmap, workflow, feature,
  generated payload, or archive pointers before scaffold/status/autopilot work
  proceeds.
- **AC-2.4**: Compaction and resume flows explicitly state what was externalized
  to files and what remains only in chat.
- **AC-2.5**: Every workflow entrypoint names its stop conditions and final
  handoff artifact.
- **AC-2.6**: The contract preserves current project guidance: ground on real
  repo state first and avoid speculative cleanup.

### 3.3 Helper, Tool, and Capability Contract *(-> HRNS-003)*

- **AC-3.1**: Each helper/tool record declares operation ID, purpose, mutability,
  input schema, output schema, exit behavior, generated artifacts, and owner
  workflow.
- **AC-3.2**: Capability discovery is capability-first: workflows discover
  available tools/resources, validate schema and mutability, and avoid hardcoded
  optional tool names where a capability contract exists.
- **AC-3.3**: Helper documentation, runner metadata, tests, and generated payloads
  are derived from a single authoritative registry or include a check that they
  cannot drift silently.
- **AC-3.4**: Helper errors include remediation guidance that is concise enough
  for an agent to self-correct.
- **AC-3.5**: Dry-run/readiness behavior exists for helpers that can mutate files,
  call networked tools, use credentials, or emit PR/release artifacts.
- **AC-3.6**: MCP/tool annotations from untrusted servers are treated as advisory
  until enforced by SpecKit Pro's runtime or policy layer.
- **AC-3.7**: Helper/tool contract work evaluates Pydantic, JSON Schema/OpenAPI,
  LangChain structured-output/tool schemas, and OpenAI Agents SDK function-tool
  schemas as contract references. The decision distinguishes the
  Python-authoritative source, generated schemas, test fixtures, and runtime
  dependency impact.

### 3.4 Permission, Sandbox, and Pre-action Authorization Controls *(-> HRNS-004)*

- **AC-4.1**: Every helper/tool risk record includes read-only, mutating,
  destructive, idempotent, open-world, credential-bearing, private-data,
  untrusted-content, external-communication, networked, and approval-required
  flags where applicable.
- **AC-4.2**: Mutating helpers run through pre-action authorization that evaluates
  helper ID, normalized arguments, cwd/worktree, target paths, branch state,
  credential context, network posture, and requested write scope.
- **AC-4.3**: Harness-control files are protected from autonomous mutation:
  plugin manifests, hooks, MCP config, policy files, helper registry, runner
  manifests, permission config, and audit/trace sinks.
- **AC-4.4**: Runtime preflight verifies Python/runner availability, helper
  registry checksum, sandbox/write-root posture, trace/audit output path, git
  cleanliness where required, and credential scope before governed operations.
- **AC-4.5**: Safe-stop semantics halt or escalate on repeated denials, missing
  audit sink, workspace escape attempts, harness-policy mutation attempts,
  broad shell/interpreter escalation, or high-risk action without explicit user
  authorization.
- **AC-4.6**: Autoheal may diagnose automatically but produces reviewable diffs
  or remediation artifacts for policy, helper, runner, or production-affecting
  changes.
- **AC-4.7**: Cross-platform sandbox/security claims remain narrow until proven
  on each target platform.
- **AC-4.8**: Permission and sandbox work compares guardrail and policy patterns
  from OpenAI Agents SDK, Guardrails AI, Semantic Kernel, promptfoo red-team
  flows, and coding-agent sandboxes without outsourcing SpecKit Pro
  authorization decisions to an external service.

### 3.5 Feedback Sensors and Eval Readiness Ladder *(-> HRNS-005)*

- **AC-5.1**: The roadmap defines a verification ladder: structural checks,
  fixture parity, deterministic regression tests, transcript/trace review,
  targeted evals, calibrated rubric review, and optional production-like
  monitoring.
- **AC-5.2**: Every new or changed skill/helper either gets a deterministic
  fixture/eval or records a discard rationale.
- **AC-5.3**: Failure-derived fixtures include reproduction evidence,
  root-cause label,
  expected behavior, observed behavior, and regression command.
- **AC-5.4**: LLM-as-judge usage is advisory unless calibrated against
  known-good/known-bad examples and allowed to return unknown/insufficient
  evidence.
- **AC-5.5**: HITL behavior is measurable: the agent asks for help when required
  information is missing and does not silently invent workflow state.
- **AC-5.6**: Eval reports name the model, skill version, runner/helper version,
  allowed tools, permission mode, and command/trace evidence.
- **AC-5.7**: Verification failures distinguish capability gaps from regression
  failures so low initial pass rates do not block exploratory specs.
- **AC-5.8**: Eval readiness work evaluates promptfoo, Braintrust, Phoenix,
  LangSmith, Langfuse, Inspect AI, DSPy, and repo-local deterministic fixtures
  as candidate eval surfaces. The result classifies local/offline operation,
  SaaS or external telemetry behavior, LLM-as-judge calibration needs, CI fit,
  and whether the candidate should become a reference pattern, optional adapter,
  or rejected dependency.
- **AC-5.9**: Self-improvement loops use an evaluator hierarchy: deterministic
  tests, formal or executable verifiers, and fixture parity are strongest;
  calibrated rubrics and LLM judges are advisory unless grounded by
  known-good/known-bad cases; intrinsic self-assessment is the weakest signal and
  cannot approve harness-control changes by itself.

### 3.6 Trace, Debug, and Review Evidence Packets *(-> HRNS-006)*

- **AC-6.1**: Helper and workflow runs emit bounded JSONL trace records with
  request ID, source workflow, helper/tool selected, normalized inputs,
  authorization decision, timestamps, result status, artifact paths, and safe
  stop reason when applicable.
- **AC-6.2**: PR packets include a compact trace/debug summary instead of raw
  logs: what ran, why, outcome, evidence paths, known gaps, and next action.
- **AC-6.3**: Failure packets classify failures by layer: context, constraint,
  permission, infrastructure, verification, planning, implementation, or
  external dependency.
- **AC-6.4**: Trace records are local by default and do not send telemetry to
  external services unless an operator explicitly configures that behavior.
- **AC-6.5**: Multi-agent or delegated flows preserve lineage: task, agent role,
  input artifact, output artifact, model/provider if available, and validation
  result.
- **AC-6.6**: Debug packets support replay or reproduction for deterministic
  helper behavior.
- **AC-6.7**: Trace schema work maps local JSONL records to
  OpenTelemetry/OpenInference-compatible concepts where useful and evaluates
  optional sinks such as LangSmith, Langfuse, Phoenix, and Braintrust while
  keeping local trace/debug packets canonical by default.
- **AC-6.8**: Every bounded self-improvement attempt records each
  generate->critique->refine->verify iteration with prompt/input provenance,
  changed artifacts, evaluator result, stop reason, checkpoint, rollback path,
  and human approval state where applicable.

### 3.7 Long-horizon Orchestration and Resumption Controls *(-> HRNS-007)*

- **AC-7.1**: Long-running scaffold/autopilot/status/resolve-pr workflows record
  resumable checkpoints and next-action state in workflow files or state
  artifacts, not only in chat history.
- **AC-7.2**: Parallel work declares file ownership, dependency edges, branch or
  worktree boundaries, and merge/review order before execution.
- **AC-7.3**: Planner/generator/evaluator roles are separated for high-risk or
  long-running workflows, with explicit handoff artifacts between them.
- **AC-7.4**: Workflow state detects stale, partial, or conflicting checkpoints
  before resuming.
- **AC-7.5**: Cost, time, and work-scope caps for long-running inspection and
  eval jobs are recorded with a continuation plan when the scoped work is larger
  than the current run.
- **AC-7.6**: Stop conditions are explicit for blocked infrastructure, missing
  user decisions, repeated denials, repeated test failures, and impossible
  branch/worktree state.
- **AC-7.7**: Resumption preserves the user's latest instruction over older
  context.
- **AC-7.8**: Orchestration work compares LangGraph, OpenAI Agents SDK, AutoGen,
  Semantic Kernel, CrewAI, Haystack, Temporal, OpenHands, and SWE-agent-style
  agent-computer-interface patterns for checkpoint/resume, HITL, workspace
  isolation, role handoff, failure recovery, and long-running job control.
- **AC-7.9**: Self-improvement orchestration has explicit iteration budgets,
  resource caps, modification scope, rollback checkpoints, promotion gates, and
  safe-stop behavior. No loop may expand its own permissions, edit its own
  approval/eval gates, or merge/promote its own harness changes without a
  human-visible review packet.

### 3.8 Harness Drift, Garbage Collection, and Self-healing Remediation *(-> HRNS-008)*

- **AC-8.1**: A harness drift scanner identifies stale docs, stale roadmap
  pointers, obsolete examples, duplicate/contradictory skill guidance, dead
  helper references, stale generated payloads, and orphaned workflow artifacts.
- **AC-8.2**: Every cleanup finding cites concrete repo evidence and is
  classified as repo-evidence-backed remediation or no-op archive.
- **AC-8.3**: Cleanup output is bounded into reviewable batches and does not
  create speculative broad cleanup PRs.
- **AC-8.4**: The scanner distinguishes load-bearing prompts/hooks/helpers from
  dead weight introduced by older model limitations.
- **AC-8.5**: Self-healing remediation produces a branch/PR packet or explicit
  no-op archive; it does not silently rewrite harness-control files.
- **AC-8.6**: Drift reports include coverage: what was scanned, what was skipped,
  and why.
- **AC-8.7**: Drift reports include external-candidate drift: stale reference
  docs, obsolete version assumptions, abandoned optional-adapter decisions, and
  dependency recommendations that no longer match HRNS evidence.
- **AC-8.8**: Drift reports identify self-generated harness artifacts such as
  prompts, fixtures, eval cases, traces, skill-library entries, generated docs,
  and synthetic examples, then classify whether each is externally validated,
  stale, duplicate, unsafe to reuse, or eligible for cleanup.

## 4. Migration Path

- **Phase 1 (HRNS-001) - Harness taxonomy**: Freeze the surface inventory, gap
  taxonomy, and external-candidate evaluation matrix that downstream specs use
  for shared boundaries.
- **Phase 2 (HRNS-002) - Context and state**: Update workflow entrypoints so long
  runs externalize durable state and resume instructions.
- **Phase 3 (HRNS-003) - Helper/tool contract**: Normalize helper registry,
  capability discovery, dry-run, and generated documentation behavior.
- **Phase 4 (HRNS-004) - Permission and sandbox controls**: Add risk metadata,
  pre-action authorization, protected harness-control surfaces, and safe-stop
  semantics.
- **Phase 5 (HRNS-005) - Eval ladder**: Connect existing test layers and future
  evals to deterministic, fixture-first evidence, including evaluator hierarchy
  rules for bounded self-improvement loops.
- **Phase 6 (HRNS-006) - Trace/debug packets**: Add bounded local trace records
  and review-packet summaries for helper, workflow, and self-improvement
  iterations.
- **Phase 7 (HRNS-007) - Long-horizon orchestration**: Harden parallel work,
  checkpoint/resume, planner/evaluator separation, self-improvement loop
  budgets, rollback, promotion gates, and stop conditions.
- **Phase 8 (HRNS-008) - Garbage collection**: Add bounded drift detection and
  self-healing remediation patterns for human-authored and self-generated
  harness artifacts.

## 5. Constraints

- Follow `.specify/memory/constitution.md`: KISS, YAGNI, script safety, plugin
  structure, tests, versioning, and conventional commits.
- Keep the XPLAT Python 3.11+ standard-library runner as the implementation
  substrate for installed-plugin helper work.
- Do not require new runtime dependencies for installed Claude/Codex plugin
  operation without a dedicated spec and supply-chain review.
- Treat external frameworks as reference patterns first. Any optional adapter or
  required dependency needs an explicit decision record covering license,
  supply chain, local/offline behavior, telemetry, secrets, cross-platform
  support, operator setup, and rollback.
- Treat recursive self-improvement as a risk-bearing loop, not a goal by itself:
  self-correction may be automated only inside explicit scopes with external
  verification, human-visible traces, rollback, and non-bypassable approval
  gates.
- Preserve capability-first, vendor-neutral wording where a concept can be
  expressed without binding to one tool vendor.
- Keep advisory code-intelligence hooks fail-open unless a spec proves they are
  safe to make blocking.
- Treat one-off discovery artifacts as planning inputs, not production runtime
  artifacts.

## 6. Open Questions

- **OQ-1 (HRNS-001):** Which durable artifact should own the harness gap
  taxonomy? Recommendation: keep the taxonomy in the HRNS-001 docs/process
  artifact and link downstream specs back to it.
- **OQ-2 (HRNS-003):** Should helper registry risk metadata live in runner code,
  generated manifest metadata, or a separate docs/test fixture? Recommendation:
  one Python-authoritative registry with generated docs and tests.
- **OQ-3 (HRNS-004):** Which harness-control files should be immutable in
  unattended modes before XPLAT-008? Recommendation: start with plugin manifests,
  hooks, MCP config, policy files, helper registry, runner manifest, and audit
  sinks.
- **OQ-4 (HRNS-005):** Which eval layer should first use rubric review?
  Recommendation: keep rubric review advisory until deterministic helper parity
  and failure-derived fixtures exist.
- **OQ-5 (HRNS-007):** Should long-running inspection and eval jobs have a
  standard cap policy? Recommendation: yes; record scope, progress status,
  blocker classes, restart evidence, and continuation criteria.
- **OQ-6 (HRNS-001):** Which external candidates deserve deeper spikes during
  execution? Recommendation: start with Pydantic/JSON Schema for HRNS-003,
  OpenTelemetry/OpenInference trace vocabulary for HRNS-006, LangGraph and
  OpenAI Agents SDK as orchestration references for HRNS-007, and
  LangSmith/Langfuse/Phoenix/Braintrust/promptfoo/Inspect AI/DSPy as eval and
  trace comparisons for HRNS-005/HRNS-006. Keep all of them non-required until
  the HRNS-001 matrix and a dedicated decision justify otherwise.
- **OQ-7 (HRNS-005/HRNS-007):** Where should bounded recursive self-improvement
  be allowed first? Recommendation: start with docs/process and deterministic
  fixture generation, require human approval before promotion, and defer helper,
  permission, eval-gate, model, training, or policy self-modification until a
  dedicated safety spec proves stronger controls.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Harness Surface Inventory and Gap Taxonomy | AC-1.* | HRNS-001 | - | P1 |
| Progressive Context and Durable State Contract | AC-2.* | HRNS-002 | HRNS-001 | P1 |
| Helper, Tool, and Capability Contract | AC-3.* | HRNS-003 | HRNS-001 | P1 |
| Permission, Sandbox, and Pre-action Authorization Controls | AC-4.* | HRNS-004 | HRNS-003 | P1 |
| Feedback Sensors and Eval Readiness Ladder | AC-5.* | HRNS-005 | HRNS-001, HRNS-003 | P1 |
| Trace, Debug, and Review Evidence Packets | AC-6.* | HRNS-006 | HRNS-003, HRNS-004, HRNS-005 | P1 |
| Long-horizon Orchestration and Resumption Controls | AC-7.* | HRNS-007 | HRNS-002, HRNS-006 | P2 |
| Harness Drift, Garbage Collection, and Self-healing Remediation | AC-8.* | HRNS-008 | HRNS-002, HRNS-005, HRNS-006 | P2 |

## 8. Success Criteria

1. Every acceptance criterion in AC-1.* through AC-8.* is either implemented,
   verified, or intentionally deferred with a documented reason.
2. Each HRNS spec stays within the roadmap reviewability budget or records a
   typed exception before implementation begins.
3. SpecKit Pro can explain and audit its core harness primitives without relying
   on raw chat history or unstated tool behavior.
4. The active helper/runtime/test/review-packet surfaces become more legible and
   safer without adding a heavyweight external harness framework.

## 9. References

- **Technical roadmap:** `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`
- **Roadmap MOC:** `docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `CLAUDE.md`

# PRD: SpecKit Pro Harness Engineering Uplift

**Status**: Draft
**Spec ID prefix**: `HRNS-###`
**Source**: Maintainer direction to harden SpecKit Pro harness behavior as
runner, helper, long-running workflow, and portable knowledge surfaces expand.
**Created**: 2026-07-03
**Last updated**: 2026-07-15
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

Every repository that adopts SpecKit Pro as its harness also needs durable,
compounding project knowledge that survives chat compaction and individual
agent sessions. Today, project evidence is spread across code, tests, agent
guidance, specifications, decisions, plans, and workflow state, with no
governed synthesis layer that agents can maintain and knowledge tools can
consume.

This PRD adopts the three-layer knowledge model proposed by Karpathy: source
evidence remains authoritative for facts, a persistent agent-maintained wiki
provides cited synthesis, and a repository-local schema governs ingest, query,
lint, and maintenance. The wiki is committed as an Open Knowledge Format (OKF)
bundle and shared by the Claude Code and Codex distributions. Code-intelligence
systems may derive graph, lexical, or vector indexes from the same files, but
those indexes remain reproducible local state rather than another knowledge
authority.

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
- Preserve warmed-up task understanding as explicit, task-scoped context
  checkpoints with summaries, provenance, freshness, and restoration rules.
- Keep task focus and active instructions explicit so workflow switching does
  not mutate canonical project guidance, dirty the worktree, or leak stale task
  state into unrelated runs.
- Add a bounded harness garbage-collection loop for stale prompts, docs, skills,
  helper registries, traces, generated payloads, and obsolete examples.
- Define a full OKF v0.1 interoperability profile pinned to a reviewed
  specification revision, with structural conformance separated from knowledge
  health and hygiene.
- Initialize every repository that adopts SpecKit Pro as its harness with a
  persistent, committed OKF knowledge bundle, using `docs/ai/knowledge/` as the
  configurable default without mutating a repository merely because the plugin
  was installed globally.
- Maintain the bundle as a compounding project wiki through incremental ingest,
  cited synthesis, query, reviewable answer capture, lint, and drift detection
  while keeping source evidence authoritative for factual conflicts.
- Give the Claude Code and Codex plugin distributions equivalent initialization,
  ingest, query, lint, indexing-interoperability, external-exchange, and
  review-packet contracts.
- Let producer-neutral code-intelligence tools index OKF concepts and sections
  alongside code symbols without making a vector service or a specific tool a
  SpecKit Pro runtime dependency.
- Support guarded bidirectional knowledge exchange while preserving source
  provenance, unknown OKF extensions, explicit conflict decisions, and human
  review before committed project knowledge or source evidence changes.

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
- Making Google Cloud's knowledge-catalog reference agents, validator, server,
  client, or UI a required runtime dependency. The pinned OKF specification is
  normative; reference tooling is interoperability evidence only.
- Migrating or rewriting source evidence solely to fit OKF, or allowing the
  synthesized knowledge bundle to override contradictory source evidence
  without an explicit reviewed resolution.
- Mutating repositories merely because SpecKit Pro was installed, silently
  initializing existing repositories, or maintaining knowledge through an
  uncontrolled background writer on every filesystem event.
- Committing CodeGraph, GitNexus, embedding, FTS, or other derived indexes. The
  committed OKF bundle is portable source material; indexes are disposable and
  regenerable consumers.
- Treating imported knowledge as executable instructions, automatically
  fetching linked resources, invoking embedded commands, or sending repository
  content to a network service without an explicit governed operation.
- Silently writing imported content back to canonical documents, automatically
  merging a write-back branch, choosing a conflict winner from timestamps, or
  inferring deletion because an incoming bundle omits a concept.
- Implementing the OKF lifecycle, code-intelligence adapters, intake, or
  reconciliation runtime in the PR that updates this PRD, roadmap, and MOC.

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
- **AC-1.8**: The inventory classifies every source-evidence class eligible for
  knowledge ingest, including code, tests, root and nested agent guidance, the
  constitution, PRDs, technical roadmaps, roadmap MOCs, workflow/process
  documents, ADRs, and approved issue/PR evidence. Generated distributions,
  caches, fixtures, derived indexes, and unreviewed chat remain excluded as
  authoritative evidence.
- **AC-1.9**: The gap taxonomy includes knowledge initialization, incremental
  ingest and synthesis, query and compounding capture, structural conformance,
  health/drift, code-intelligence interoperability, external exchange,
  provenance, conflict handling, and cross-distribution parity as distinct
  harness concerns.
- **AC-1.10**: The external-candidate matrix records the normative OKF
  specification revision and maturity, reference-tooling compatibility evidence,
  known spec/tool mismatches, extension-preservation posture, and whether each
  finding is blocking, advisory, or deferred.

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
- **AC-2.7**: Long-running workflows define task-scoped context checkpoints with
  name, summary, message/source count where available, timestamp, task/spec
  association, storage class, provenance, and restore instructions.
- **AC-2.8**: The contract distinguishes intentional named checkpoints from
  emergency auto-saves. Auto-saves may protect against compaction or
  interruption, but only named checkpoints or workflow artifacts can be treated
  as canonical resume inputs.
- **AC-2.9**: Context health monitoring defines configurable healthy,
  degrading, and critical zones with token/budget baseline, burn-rate estimate,
  save recommendation, and fresh-session recommendation before compaction or
  recall degradation can silently affect decisions.
- **AC-2.10**: Task and workflow switching distinguishes canonical shared
  project guidance from active task-specific instructions or injected context.
  Switching focus is atomic, records the active task/spec identity, and avoids
  mutating root instructions or creating accidental PR diffs.
- **AC-2.11**: Repository source evidence remains authoritative for factual
  conflicts. The committed OKF bundle is a durable, first-class knowledge
  product and default project-knowledge retrieval surface, not a disposable
  projection or permission to rewrite its cited evidence.
- **AC-2.12**: Knowledge state records stable concept identity, source paths and
  anchors, source digests or revisions, bundle/spec revision, knowledge status,
  and the mappings required to identify unchanged, stale, inferred, proposed,
  externally changed, and conflicting content.
- **AC-2.13**: Coverage checks prove that every in-scope evidence source is
  represented, intentionally deferred, or explicitly excluded with a reason,
  and that generated plugin payloads, indexes, or distribution-specific copies
  cannot silently become evidence inputs.
- **AC-2.14**: Interrupted initialization, ingest, query-capture, lint, indexing,
  intake, and reconciliation operations can resume from durable
  source/base/decision state without relying on chat history or treating a
  partial synthesis as reviewed knowledge.

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
- **AC-3.8**: The helper registry defines separate governed operations for OKF
  initialization, incremental ingest/synthesis, query, answer capture, lint,
  indexer interoperability, external validation/intake, reconciliation
  planning, and materializing an approved proposal. Each operation declares
  mutability, schemas, path scope, network posture, artifacts, and exit states.
- **AC-3.9**: The OKF producer/consumer contract supports the pinned v0.1
  minimum concept shape, emits recommended metadata when source evidence is
  available, and accepts valid concepts that contain only the required `type`
  field.
- **AC-3.10**: Consumers preserve unknown frontmatter fields and unknown concept
  types through intake and reconciliation unless a human-approved proposal
  explicitly transforms or removes them.
- **AC-3.11**: Maintained links are portable relative references, while intake
  accepts both link forms permitted by the pinned specification and reports
  ambiguous or unsafe targets without fetching them.
- **AC-3.12**: Claude Code and Codex distributions expose equivalent OKF
  operation semantics, schemas, safety flags, and result interpretation even
  when their install-facing wrappers differ.

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
- **AC-4.9**: Shared or promoted context artifacts run through secret scanning,
  size limits, provenance checks, and human confirmation before commit or team
  distribution. Personal context artifacts remain local by default and must not
  appear in PR diffs accidentally.
- **AC-4.10**: External OKF bundles, frontmatter, Markdown bodies, links,
  citations, and embedded command-like text are treated as untrusted data, not
  model instructions or authorization to execute, fetch, or communicate.
- **AC-4.11**: Intake preflight enforces bounded bundle size and concept count,
  normalized paths, workspace confinement, encoding rules, symlink policy,
  secret handling, and explicit network-disabled behavior before parsing can
  affect repository state.
- **AC-4.12**: Source evidence, the committed OKF bundle, and knowledge
  mapping/base state are protected harness surfaces. Agent synthesis can affect
  them only within a declared workflow branch/worktree and reviewable proposal;
  external content requires an isolated proposal with trace evidence.
- **AC-4.13**: Missing incoming concepts never authorize deletion. Deletion
  requires an explicit tombstone or deletion proposal, provenance, impact
  preview, and human approval.
- **AC-4.14**: No synchronization operation may auto-merge, expand its write
  scope, weaken its own validation policy, or choose a conflict winner from an
  untrusted timestamp.

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
- **AC-5.10**: Adversarial review for PRDs, test plans, dev plans, generated
  fixtures, or self-improvement outputs runs from clean isolated context rather
  than the authoring session. The reviewer produces findings and risk
  acceptances; it does not silently fix its own findings.
- **AC-5.11**: PRD-driven harness work treats user/operator documentation as an
  early feedback artifact for workflow changes where applicable. Documentation
  drafts expose ambiguous flows before implementation, and downstream docs are
  regenerated or explicitly marked not applicable when acceptance criteria
  change.
- **AC-5.12**: Process sequencing detects stale downstream artifacts after PRD or
  roadmap changes, including docs, test plans, dev plans, generated fixtures,
  adversarial inventories, and risk acceptances. Proceeding with stale artifacts
  requires an explicit force/acceptance record.
- **AC-5.13**: Test/eval inventories record what each test actually verifies,
  the acceptance criterion it maps to, and a verdict of pass, fail, escalate, or
  accepted. They flag vacuous patterns such as placeholder assertions,
  broad OR fallbacks, conditional file-existence guards, and self-fulfilling
  setup.
- **AC-5.14**: OKF verification includes a version-pinned conformance corpus with
  positive, negative, minimum-valid, unknown-field, unknown-type, index, log,
  link, encoding, and round-trip cases derived from the normative specification.
- **AC-5.15**: Structural conformance and knowledge health are reported
  separately. Conditions the pinned specification defines as soft, including
  broken internal links or missing recommended indexes, produce warnings rather
  than false conformance failures.
- **AC-5.16**: Knowledge-health checks can report broken links, missing indexes,
  stale claims, contradictory concepts, weak or missing citations, and coverage
  gaps without redefining OKF validity.
- **AC-5.17**: Differential checks against Google Cloud reference tooling are
  interoperability evidence only. A reference-validator disagreement cannot
  override the pinned specification without a reviewed compatibility decision.
- **AC-5.18**: Equivalent conformance and health fixtures run against the Claude
  Code and Codex distribution surfaces and report parity failures explicitly.

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
- **AC-6.9**: Trace/debug packets record the active context checkpoint or
  warm-up baseline, context-health zone, compaction/auto-save event, and whether
  resume evidence came from a named checkpoint, workflow artifact, or emergency
  fallback.
- **AC-6.10**: OKF trace packets record the pinned specification URI and commit,
  bundle profile/version, repository and source revision, source and concept
  digests, operation mode, model/provider when synthesis occurs, and
  distribution surface.
- **AC-6.11**: Every maintained or imported concept can be traced to source
  paths, anchors, external provenance, stable identity, base-state entry,
  knowledge status, and any normalization or transformation applied.
- **AC-6.12**: Reconciliation packets record local, base, and incoming evidence;
  the resulting unchanged/add/update/conflict/delete-proposal classification;
  and the human decision required before write-back.
- **AC-6.13**: Round-trip evidence identifies preserved unknown fields/types and
  reports any lossy transformation as a blocking finding rather than silently
  discarding data.
- **AC-6.14**: Trace packets redact secrets and bound imported content excerpts
  while retaining enough hashes, paths, and decision metadata for review and
  deterministic reproduction.

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
- **AC-7.10**: Initialization, ingest, query capture, lint, indexing, intake, and
  reconciliation workflows checkpoint source revision, bundle identity,
  validation state, mappings, unresolved decisions, output worktree/branch, and
  the next safe action.
- **AC-7.11**: Internal knowledge maintenance targets the declared feature
  branch/worktree so code and knowledge can be reviewed atomically. External
  reconciliation produces a separate isolated proposal. Neither path merges,
  pushes, or promotes its own result without distinct authorization.
- **AC-7.12**: Reconciliation stops when both canonical and incoming knowledge
  changed from the recorded base, preserves both sides, and asks for an explicit
  resolution instead of applying timestamp-based last-write-wins behavior.
- **AC-7.13**: Resume revalidates repository revision, bundle digest,
  specification pin, mapping/base state, and the user's latest instruction
  before continuing a synchronization operation.
- **AC-7.14**: Parallel Claude Code and Codex operations declare shared source
  ownership and cannot create competing write-back proposals without surfacing
  the overlap and required review order.

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
- **AC-8.9**: Drift and garbage-collection routines identify stale, duplicate,
  oversized, secret-bearing, orphaned, or no-longer-load-bearing context
  checkpoints. Cleanup requires a dry-run preview and preserves reviewable
  recovery evidence.
- **AC-8.10**: Drift checks detect incomplete evidence coverage, stale source
  digests or mappings, changed specification/profile pins, unreviewed synthesis,
  stale indexer contracts, and divergence between Claude Code and Codex
  operation contracts.
- **AC-8.11**: Health drift is classified separately from structural
  conformance and includes broken links, missing navigation indexes, stale or
  contradictory claims, citation quality, and orphaned concepts.
- **AC-8.12**: Garbage collection distinguishes committed OKF concepts from
  disposable index/cache artifacts and operation state; it never treats the
  maintained bundle as generated trash or silently deletes project knowledge.
- **AC-8.13**: Intake/reconciliation drift checks prove unknown fields and types
  remain preserved across supported round trips and flag lossy behavior as a
  blocking regression.
- **AC-8.14**: Reference-tooling and specification drift are reviewed
  independently; a new upstream release does not silently move the normative
  pin or change conformance behavior.
- **AC-8.15**: Cleanup never interprets an omitted incoming concept, stale
  citation, missing source, or absent index result as deletion; only an approved
  tombstone/deletion proposal can remove committed knowledge, source evidence,
  or an identity mapping.
- **AC-8.16**: Vector, lexical, and graph indexes remain reproducible from code
  plus committed OKF files and can be removed without knowledge loss.

### 3.9 Host Repository OKF Knowledge Contract and Initialization *(-> HRNS-009)*

- **AC-9.1**: The repository profile claims full conformance to OKF v0.1 as
  defined by the GoogleCloudPlatform/knowledge-catalog `okf/SPEC.md` pinned at
  commit `d44368c15e38e7c92481c5992e4f9b5b421a801d`; moving the pin requires a
  reviewed compatibility change.
- **AC-9.2**: Initializing SpecKit Pro as a repository harness creates or adopts
  one committed OKF bundle. Existing repositories require an explicit migration
  operation; global plugin installation alone never writes project files.
- **AC-9.3**: The configurable default bundle path is `docs/ai/knowledge/`, kept
  outside generated tool state and vendored `.specify/**` content.
- **AC-9.4**: The initialized bundle contains a root `index.md`, a monotonic
  `log.md`, and typed concept pages organized for progressive disclosure.
- **AC-9.5**: Source artifacts remain authoritative evidence for factual
  conflicts. The OKF bundle is the persistent, versioned synthesis and default
  project-knowledge retrieval surface.
- **AC-9.6**: The root index records the OKF/profile version and navigates every
  concept or subordinate index without requiring an embedding service.
- **AC-9.7**: The log is logically append-only and newest-first for OKF
  conformance: new records are prepended and historical records are not edited
  or deleted except through an explicit corrective entry.
- **AC-9.8**: Every concept satisfies the pinned minimum schema and uses
  recommended metadata plus namespaced producer fields for source references,
  digests, knowledge status, and generator provenance when evidence supports it.
- **AC-9.9**: Path, identity, and collision rules remain stable across branches,
  worktrees, operating systems, and Claude Code/Codex entrypoints.
- **AC-9.10**: A repository profile declares evidence classes, exclusions,
  naming, concept types, citation requirements, review policy, and maintenance
  checkpoints without expanding root agent instructions into a large manual.
- **AC-9.11**: The OKF bundle is committed and reviewed with project work;
  vector, lexical, graph, cache, and renderer outputs remain ignored,
  reproducible local state.
- **AC-9.12**: Initialization requires no Google reference runtime, external
  service, network access, or mandatory code-intelligence dependency.
- **AC-9.13**: Claude Code and Codex produce equivalent paths, profile semantics,
  conformance results, diagnostics, and trace evidence from the same checkout.
- **AC-9.14**: Reinitialization is idempotent, preserves accepted extensions and
  content, and reports incompatible existing layouts rather than overwriting
  them.

### 3.10 Incremental Evidence Ingest and Knowledge Synthesis *(-> HRNS-010)*

- **AC-10.1**: Ingest detects changed evidence through repository diffs and
  content digests, then limits work to affected concepts instead of rebuilding
  the entire knowledge base on every run.
- **AC-10.2**: Durable forward and reverse mappings connect source paths and
  anchors to every dependent concept, including many-to-many relationships.
- **AC-10.3**: One changed source may update multiple entity, system, decision,
  workflow, or concept pages plus their indexes and log entry.
- **AC-10.4**: Synthesis produces a bounded reviewable proposal showing added,
  updated, stale, conflicted, and unchanged concepts before promotion.
- **AC-10.5**: New factual claims cite repository or approved external evidence;
  unsupported claims are marked inferred or proposed rather than stated as fact.
- **AC-10.6**: Namespaced provenance records source revisions, digests,
  synthesis model/provider when available, operation ID, and knowledge status.
- **AC-10.7**: Contradictory evidence is preserved and surfaced for resolution;
  the agent does not silently choose a source or timestamp as winner.
- **AC-10.8**: Source changes mark dependent concepts stale until reviewed
  synthesis resolves them, while unaffected concepts retain their prior status.
- **AC-10.9**: Maintenance runs in the workflow's declared branch/worktree so
  knowledge and associated code/spec changes can be reviewed atomically.
- **AC-10.10**: Filesystem or CodeGraph watch events may trigger local reindexing
  but never authorize uncontrolled OKF synthesis or commits on every save.
- **AC-10.11**: Source removal does not delete concepts automatically; it creates
  a stale or explicit tombstone proposal with dependent-link impact.
- **AC-10.12**: Every accepted ingest updates relevant indexes and prepends one
  bounded operational log record without rewriting older history.
- **AC-10.13**: Interrupted or cancelled ingest resumes from source digests,
  affected-concept mappings, proposal state, and decisions without chat history.
- **AC-10.14**: Claude Code and Codex apply the same change selection,
  provenance, review, promotion, and safe-stop rules.

### 3.11 Knowledge Query, Citation, and Compounding Capture *(-> HRNS-011)*

- **AC-11.1**: Query reads `index.md` first for progressive disclosure and can
  answer from repository-local OKF without a vector service.
- **AC-11.2**: Query can combine knowledge concepts with code, tests, specs, and
  other cited evidence when implementation detail is required.
- **AC-11.3**: Answers cite the concepts used and their underlying source anchors
  so a reviewer can distinguish synthesis from evidence.
- **AC-11.4**: Results retain concept type, knowledge status, source revision,
  freshness, and conflict indicators instead of flattening every match into
  equally trusted text.
- **AC-11.5**: Stale, inferred, proposed, contradictory, or insufficient
  knowledge is identified explicitly in the answer.
- **AC-11.6**: Optional lexical, graph, or vector retrieval may improve recall,
  but query behavior degrades to file/index traversal rather than failing when
  those consumers are unavailable.
- **AC-11.7**: A useful query result can be filed back only as a cited,
  reviewable concept proposal or update; it never becomes knowledge solely
  because it appeared in chat.
- **AC-11.8**: Answer capture records the originating question, cited evidence,
  affected concepts, proposed status, and reviewer decision without storing raw
  private transcripts by default.
- **AC-11.9**: Query and capture enforce path scope, bounded excerpts, secret
  handling, network posture, and protected-source rules.
- **AC-11.10**: Query does not silently mutate, commit, push, or promote the
  knowledge bundle.
- **AC-11.11**: Query traces identify retrieval mode and whether each result came
  from OKF, code intelligence, direct evidence, or an external source.
- **AC-11.12**: Equivalent fixtures prove Claude Code and Codex return the same
  source-grounded result classes and capture proposals for the same repository.

### 3.12 Knowledge Conformance, Health, and Drift Maintenance *(-> HRNS-012)*

- **AC-12.1**: Structural OKF conformance and project-knowledge health are
  validated and reported as separate result classes.
- **AC-12.2**: A pinned conformance corpus covers positive, negative,
  minimum-valid, unknown-field, unknown-type, index, log, link, encoding, and
  round-trip cases from the normative specification.
- **AC-12.3**: Health lint reports broken links, missing navigation, stale source
  digests, contradictory claims, missing citations, orphaned concepts, and
  incomplete evidence coverage without redefining OKF validity.
- **AC-12.4**: Index lint proves every concept is reachable or explicitly
  excluded, and log lint proves newest-first monotonic history without mutation
  of prior records.
- **AC-12.5**: Source drift identifies concepts affected by changed, moved,
  renamed, or removed evidence and distinguishes stale from invalid knowledge.
- **AC-12.6**: Unknown fields, types, and legal link forms survive lint and
  rewrite round trips unless a reviewed migration explicitly changes them.
- **AC-12.7**: Deterministic lint and coverage checks do not depend on an LLM;
  semantic contradiction review is advisory and records model/provider context.
- **AC-12.8**: Remediation is emitted as bounded reviewable proposals or a no-op
  report, never as an unreviewed broad rewrite.
- **AC-12.9**: Lint never deletes by omission, failed retrieval, stale citation,
  or absent index result; deletion requires an approved tombstone.
- **AC-12.10**: Derived index drift is reported separately and can be repaired by
  regeneration without changing committed OKF content.
- **AC-12.11**: Specification-pin, producer-profile, and consumer-adapter drift
  require reviewed compatibility decisions rather than silent upgrades.
- **AC-12.12**: Conformance and health reports are bounded, source-located,
  secret-safe, and suitable for workflow and PR evidence packets.
- **AC-12.13**: Claude Code and Codex run equivalent conformance, lint, drift,
  round-trip, and remediation fixtures.

### 3.13 Code-Intelligence and Vector-Index Interoperability *(-> HRNS-013)*

- **AC-13.1**: SpecKit Pro publishes a producer-neutral discovery and change
  contract for the committed OKF bundle without requiring CodeGraph, GitNexus,
  or any vector provider.
- **AC-13.2**: Consumers can represent files, concepts, headings, and bounded
  heading-aware chunks as distinct typed nodes rather than code-symbol text.
- **AC-13.3**: Embedding input includes semantic body text plus evidence-backed
  title, description, type, and tags, while retaining concept/path identity.
- **AC-13.4**: OKF links become graph edges and source/citation references can
  link concepts to repository files, symbols, tests, specs, and decisions.
- **AC-13.5**: The interoperability vocabulary supports at least `REFERENCES`,
  `DERIVED_FROM`, `DESCRIBES`, `IMPLEMENTS`, `VERIFIED_BY`, `SUPERSEDES`, and
  `CONTRADICTS` without requiring every consumer to support every relation.
- **AC-13.6**: Keyword/FTS indexing is the baseline; section embeddings and
  hybrid retrieval are optional derived capabilities.
- **AC-13.7**: `index.md` and `log.md` are excluded from semantic embeddings by
  default to avoid duplicate navigation and operational-history noise.
- **AC-13.8**: Generated graph/vector stores remain ignored, local-first,
  model-scoped, and fully regenerable from code plus committed OKF files.
- **AC-13.9**: Accepted OKF changes can notify or be detected by incremental
  consumers, but a consumer reindex event never grants canonical write access.
- **AC-13.10**: Hybrid results preserve code-versus-knowledge type, provenance,
  freshness, and score components so retrieval does not erase trust boundaries.
- **AC-13.11**: Indexing honors repository scope, ignore rules, secret policy,
  configured network posture, and deletion semantics.
- **AC-13.12**: Contract fixtures cover a CodeGraph-style first-class concept
  adapter and a GitNexus-style Markdown-section adapter while remaining usable
  by other consumers.
- **AC-13.13**: Consumer incompatibility or absence is advisory and cannot block
  core file/index-based knowledge workflows.
- **AC-13.14**: Claude Code and Codex expose equivalent adapter discovery,
  diagnostics, and result interpretation.

### 3.14 External OKF Exchange and Reviewable Reconciliation *(-> HRNS-014)*

- **AC-14.1**: Intake accepts conformant OKF v0.1 bundles, including type-only
  concepts and unknown types or extension fields.
- **AC-14.2**: External content is untrusted data, never executable instruction,
  and validation is local-first and network-disabled by default.
- **AC-14.3**: Bounded preflight covers bytes, files/concepts, nesting,
  frontmatter/document size, encoding, normalized paths, symlinks, duplicate
  identity, workspace escape, and parser/decompression abuse.
- **AC-14.4**: Structural failures block intake while soft specification
  conditions and knowledge-health findings remain separate review items.
- **AC-14.5**: Normalized staging preserves unknown fields/types, bodies, legal
  links, provenance, bundle identity, and the target repository/base revision.
- **AC-14.6**: Reconciliation compares recorded base, current committed
  knowledge and source evidence, and staged incoming concepts rather than
  performing a two-way overwrite.
- **AC-14.7**: Concepts are classified as unchanged, local-only, incoming-only,
  compatible add, conflict, explicit deletion proposal, unmapped, or invalid.
- **AC-14.8**: When both sides changed, both are preserved and the operation
  stops for an explicit decision; timestamps and source priority never choose a
  winner.
- **AC-14.9**: Omission means absence, not deletion. A tombstone must identify
  target, base evidence, reason, dependent links, and expected impact.
- **AC-14.10**: Operators can accept, reject, edit, or defer bounded proposals,
  and unresolved decisions remain resumable.
- **AC-14.11**: Approved changes materialize only in a new isolated
  branch/worktree with bounded diffs, mapping updates, verification, and trace
  evidence; commit, push, PR, merge, and cleanup remain separate authorizations.
- **AC-14.12**: Write-back is limited to mapped knowledge/source paths and cannot
  modify protected manifests, policies, hooks, registries, generated payloads,
  or unrelated files.
- **AC-14.13**: Materialization revalidates repository revision, bundle digest,
  spec/profile pin, mappings, decisions, path scope, and latest instruction.
- **AC-14.14**: Lossy transformation of unknown extensions or unsupported
  source formats blocks until an operator resolves it.
- **AC-14.15**: Claude Code and Codex apply equivalent limits,
  classifications, approvals, proposals, and safe stops.
- **AC-14.16**: Failure or cancellation preserves a bounded diagnostic or
  resumable decision packet and leaves committed repository content unchanged.

## 4. Migration Path

- **Tier 1 (HRNS-001) - Harness taxonomy**: Freeze the surface inventory, gap
  taxonomy, evidence/knowledge inventory, and external-candidate evaluation
  matrix that downstream specs use for shared boundaries.
- **Tier 2 (HRNS-002 + HRNS-003) - Context and tool foundations**: Externalize
  durable state, then normalize helper/capability contracts and the governed
  operations later OKF specs require.
- **Tier 3 (HRNS-004 + HRNS-005) - Controls and sensors**: Add authorization,
  protected surfaces, conformance/eval evidence, and separate health reporting
  before any external knowledge can affect repository state.
- **Tier 4 (HRNS-006) - Evidence packets**: Add bounded local trace records and
  review-packet summaries for helper, workflow, self-improvement, and future OKF
  operations.
- **Tier 5 (HRNS-007 + HRNS-009) - Resumable work and knowledge foundation**:
  Harden long-running orchestration while initializing the persistent,
  committed OKF knowledge contract. These specs may proceed in parallel after
  their shared foundations are complete.
- **Tier 6 (HRNS-010) - Incremental synthesis**: Detect changed evidence,
  synthesize affected concepts, and produce cited reviewable knowledge diffs.
- **Tier 7 (HRNS-011 + HRNS-012 + HRNS-013) - Query, maintenance, and
  interoperability**: Add source-grounded query/capture, conformance and health
  lint, and producer-neutral code-intelligence/vector-index contracts in
  parallel after the maintained bundle exists.
- **Tier 8 (HRNS-014) - External exchange**: Validate, stage, reconcile, and
  materialize guarded external OKF proposals with explicit conflict decisions.
- **Tier 9 (HRNS-008) - Harness maintenance**: Add bounded drift detection and
  self-healing remediation for human-authored, synthesized, indexed, imported,
  and externally reconciled harness artifacts.

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
- Keep personal context captures, emergency auto-saves, raw transcripts, and
  machine-local state out of git by default. Any shared context checkpoint must
  be intentionally promoted, secret-scanned, size-bounded, provenance-labeled,
  and reviewable.
- Preserve capability-first, vendor-neutral wording where a concept can be
  expressed without binding to one tool vendor.
- Treat the pinned OKF v0.1 `SPEC.md` at commit
  `d44368c15e38e7c92481c5992e4f9b5b421a801d` as normative. Google Cloud
  knowledge-catalog implementations and examples are non-normative
  interoperability evidence.
- Require full pinned-spec conformance while preserving the distinction between
  structural validity and non-blocking health/hygiene findings.
- Keep repository sources authoritative as evidence while maintaining one
  persistent, committed OKF synthesis layer with explicit source mappings,
  provenance, review state, and base state.
- Initialize the bundle only through explicit repository harness adoption or
  migration, using configurable `docs/ai/knowledge/` by default and keeping it
  outside vendored `.specify/**` and generated `.codegraph/**` state.
- Cover code, tests, root and nested agent guidance, the constitution, PRDs,
  technical roadmaps, MOCs, workflows, ADRs, and approved issue/PR evidence;
  exclude generated distributions, caches, fixtures, raw transcripts, and
  derived indexes from authoritative discovery.
- Preserve unknown OKF fields and concept types, accept the specification's
  minimum-valid concept, and avoid a compatibility dependency on stricter
  behavior in any reference validator.
- Keep external intake local-first, network-disabled by default, bounded, and
  non-executable. Imported text cannot grant authority or become instructions.
- Require three-way reconciliation and reviewable branch/worktree proposals for
  bidirectional sync. Timestamps never select a winner, omission never means
  deletion, and write-back never auto-merges.
- Keep OKF contracts and verification equivalent across the Claude Code and
  Codex plugin distributions.
- Keep graph, lexical, and vector interoperability producer-neutral and
  optional. Committed Markdown remains usable when CodeGraph, GitNexus, an
  embedding provider, or any other consumer is absent.
- Keep all knowledge synthesis and answer capture reviewable in the declared
  workflow branch/worktree; local file-watch events may reindex but do not
  authorize synthesis, commits, pushes, or merges.
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
- **OQ-8 (HRNS-002/HRNS-004):** Should SpecKit Pro support shared warmed-up
  context checkpoints? Recommendation: start with summaries, manifests, and
  restore instructions rather than committed raw transcripts; require explicit
  promotion, secret scanning, size caps, provenance, and human review before any
  shared checkpoint becomes team-consumable.
- **OQ-9 (HRNS-009):** Where should the committed OKF bundle live?
  Recommendation: default to configurable `docs/ai/knowledge/`; avoid vendored
  `.specify/**` and consumer-owned generated directories such as `.codegraph/`.
- **OQ-10 (HRNS-011):** When should a useful query answer compound into the
  knowledge base? Recommendation: only through a cited proposal with explicit
  status and normal branch review; never capture raw chat automatically.
- **OQ-11 (HRNS-013):** Should SpecKit Pro implement tool-specific indexers?
  Recommendation: publish and test a producer-neutral contract; keep CodeGraph,
  GitNexus, and other consumer adapters in their owning projects.

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
| Harness Drift, Garbage Collection, and Self-healing Remediation | AC-8.* | HRNS-008 | HRNS-002, HRNS-005, HRNS-006, HRNS-009 through HRNS-014 | P2 |
| Host Repository OKF Knowledge Contract and Initialization | AC-9.* | HRNS-009 | HRNS-001, HRNS-002, HRNS-003, HRNS-004, HRNS-005, HRNS-006 | P2 |
| Incremental Evidence Ingest and Knowledge Synthesis | AC-10.* | HRNS-010 | HRNS-005, HRNS-006, HRNS-009 | P2 |
| Knowledge Query, Citation, and Compounding Capture | AC-11.* | HRNS-011 | HRNS-003, HRNS-005, HRNS-006, HRNS-009, HRNS-010 | P2 |
| Knowledge Conformance, Health, and Drift Maintenance | AC-12.* | HRNS-012 | HRNS-005, HRNS-006, HRNS-009, HRNS-010 | P2 |
| Code-Intelligence and Vector-Index Interoperability | AC-13.* | HRNS-013 | HRNS-003, HRNS-005, HRNS-006, HRNS-009, HRNS-010 | P2 |
| External OKF Exchange and Reviewable Reconciliation | AC-14.* | HRNS-014 | HRNS-004, HRNS-006, HRNS-007, HRNS-009, HRNS-010, HRNS-012 | P2 |

## 8. Success Criteria

1. Every acceptance criterion in AC-1.* through AC-14.* is either implemented,
   verified, or intentionally deferred with a documented reason.
2. Each HRNS spec stays within the roadmap reviewability budget or records a
   typed exception before implementation begins.
3. SpecKit Pro can explain and audit its core harness primitives without relying
   on raw chat history or unstated tool behavior.
4. The active helper/runtime/test/review-packet surfaces become more legible and
   safer without adding a heavyweight external harness framework.
5. Every repository that adopts SpecKit Pro as its harness has a committed,
   conformant OKF knowledge base that compounds through cited, incremental,
   reviewable maintenance while source evidence remains authoritative.
6. Project knowledge remains queryable without a vector service and can be
   indexed with code through producer-neutral lexical, graph, and vector
   contracts without committing derived indexes.
7. External OKF knowledge can be validated, staged, reconciled, and proposed as
   a bounded reviewable diff without executing imported content, losing unknown
   extensions, using timestamps as conflict authority, or deleting by omission.
8. Claude Code and Codex distributions pass equivalent OKF initialization,
   ingest, query, lint, interoperability, exchange, and trace-evidence checks.

## 9. References

- **Technical roadmap:** `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`
- **Roadmap MOC:** `docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- **Normative OKF v0.1 specification (pinned):**
  https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/d44368c15e38e7c92481c5992e4f9b5b421a801d/okf/SPEC.md
- **Google Cloud knowledge-catalog reference repository:**
  https://github.com/GoogleCloudPlatform/knowledge-catalog
- **Google Cloud OKF overview:**
  https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
- **Karpathy knowledge-work architecture proposal:**
  https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- **Pulumi knowledge-as-code and OKF analysis:**
  https://www.pulumi.com/blog/knowledge-as-code-the-memory-file-just-got-a-spec/
- **CodeGraph local-first code-intelligence consumer:**
  https://github.com/racecraft-lab/codegraph
- **GitNexus Markdown ingestion reference:**
  https://github.com/abhigyanpatwari/GitNexus
- **Tracked upstream compatibility evidence:** validator/spec parity
  ([PR #145](https://github.com/GoogleCloudPlatform/knowledge-catalog/pull/145)),
  link interpretation
  ([issue #157](https://github.com/GoogleCloudPlatform/knowledge-catalog/issues/157),
  [PR #165](https://github.com/GoogleCloudPlatform/knowledge-catalog/pull/165)),
  conformance corpus
  ([issue #62](https://github.com/GoogleCloudPlatform/knowledge-catalog/issues/62)),
  provenance
  ([issue #140](https://github.com/GoogleCloudPlatform/knowledge-catalog/issues/140)),
  freshness/contradiction
  ([issue #158](https://github.com/GoogleCloudPlatform/knowledge-catalog/issues/158)),
  and citation semantics
  ([issue #199](https://github.com/GoogleCloudPlatform/knowledge-catalog/issues/199)).

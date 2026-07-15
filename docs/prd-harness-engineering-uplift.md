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

The same harness knowledge must also be portable across the Claude Code and
Codex plugin distributions without creating a second source of truth. Today,
canonical guidance is optimized for repository-native use and has no governed
interchange contract for external knowledge tools. A conformant Open Knowledge
Format (OKF) projection can make that knowledge inspectable and exchangeable,
but only if projection, intake, reconciliation, provenance, conflict handling,
and write-back remain deterministic, reviewable, and subordinate to the
canonical repository documents.

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
- Project all canonical harness knowledge into a deterministic, on-demand OKF
  artifact without migrating or duplicating the authoritative source documents.
- Give the Claude Code and Codex plugin distributions equivalent projection,
  validation, intake, reconciliation, and review-packet contracts.
- Support guarded bidirectional knowledge exchange while preserving source
  provenance, unknown OKF extensions, explicit conflict decisions, and human
  review before canonical repository content changes.

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
- Migrating canonical repository documents into OKF, editing them in place, or
  committing a duplicate OKF knowledge tree as another source of truth. The
  projection is an on-demand generated artifact.
- Treating imported knowledge as executable instructions, automatically
  fetching linked resources, invoking embedded commands, or sending repository
  content to a network service without an explicit governed operation.
- Silently writing imported content back to canonical documents, automatically
  merging a write-back branch, choosing a conflict winner from timestamps, or
  inferring deletion because an incoming bundle omits a concept.
- Implementing the OKF projection, intake, or reconciliation runtime in the PR
  that updates this PRD, roadmap, and MOC.

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
- **AC-1.8**: The inventory classifies every canonical knowledge source eligible
  for OKF projection, including root and nested `AGENTS.md`, `CLAUDE.md`, and
  `GEMINI.md`; the constitution; PRDs; technical roadmaps; roadmap MOCs; and
  workflow/process documents. Generated distributions, caches, fixtures, and
  other derived copies are explicitly excluded as canonical inputs.
- **AC-1.9**: The gap taxonomy includes knowledge projection, structural
  conformance, health/hygiene, external intake, provenance, reconciliation,
  conflict handling, write-back, and cross-distribution parity as distinct
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
- **AC-2.11**: Canonical repository documents remain authoritative. An OKF
  bundle is a deterministic, on-demand projection with an explicit lifecycle;
  it is not a committed mirror, resume authority, or independent source of
  truth.
- **AC-2.12**: Projection state records stable concept identity, canonical source
  path, source digest, bundle/spec revision, and the base mapping required to
  distinguish unchanged, locally changed, externally changed, and conflicting
  content during later reconciliation.
- **AC-2.13**: Coverage checks prove that every in-scope canonical source is
  represented or explicitly excluded with a reason, and that generated plugin
  payloads or distribution-specific copies cannot silently become projection
  inputs.
- **AC-2.14**: Interrupted projection, intake, and reconciliation operations can
  resume from durable source/base/decision state without relying on chat history
  or treating a partially generated bundle as canonical.

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
- **AC-3.8**: The helper registry defines separate governed operations for
  canonical-to-OKF projection, OKF validation/intake, reconciliation planning,
  and materializing an approved write-back proposal. Each operation declares
  mutability, schemas, path scope, network posture, artifacts, and exit states.
- **AC-3.9**: The OKF producer/consumer contract supports the pinned v0.1
  minimum concept shape, emits recommended metadata when source evidence is
  available, and accepts valid concepts that contain only the required `type`
  field.
- **AC-3.10**: Consumers preserve unknown frontmatter fields and unknown concept
  types through intake and reconciliation unless a human-approved proposal
  explicitly transforms or removes them.
- **AC-3.11**: Generated links are portable relative references, while intake
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
- **AC-4.12**: Canonical knowledge documents and their mapping/base state are
  protected harness-control surfaces. Imported content can affect them only
  through an isolated, reviewable branch/worktree proposal with trace evidence.
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
  bundle profile/version, canonical source revision, source and bundle digests,
  operation mode, and distribution surface.
- **AC-6.11**: Every projected or imported concept can be traced to its source
  path or external provenance, stable identity, base-state entry, and any
  normalization or transformation applied.
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
- **AC-7.10**: Projection, intake, and reconciliation workflows checkpoint
  source revision, bundle identity, validation state, base mapping, unresolved
  decisions, output worktree/branch, and the next safe action.
- **AC-7.11**: Bidirectional synchronization produces a reviewable proposal in
  an isolated branch/worktree and, when requested, a PR packet; it never writes
  directly to the operator's active branch or merges its own result.
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
- **AC-8.10**: Drift checks detect projection nondeterminism, incomplete
  canonical-source coverage, stale base mappings, changed specification pins,
  and divergence between Claude Code and Codex operation contracts.
- **AC-8.11**: Health drift is classified separately from structural
  conformance and includes broken links, missing navigation indexes, stale or
  contradictory claims, citation quality, and orphaned concepts.
- **AC-8.12**: Garbage collection detects stale generated OKF artifacts and
  operation state without treating the on-demand projection as durable source
  content or silently deleting canonical knowledge.
- **AC-8.13**: Intake/reconciliation drift checks prove unknown fields and types
  remain preserved across supported round trips and flag lossy behavior as a
  blocking regression.
- **AC-8.14**: Reference-tooling and specification drift are reviewed
  independently; a new upstream release does not silently move the normative
  pin or change conformance behavior.
- **AC-8.15**: Cleanup never interprets an omitted incoming concept as deletion;
  only an approved tombstone/deletion proposal can remove canonical content or
  its identity mapping.

### 3.9 OKF v0.1 Canonical Knowledge Projection *(-> HRNS-009)*

- **AC-9.1**: The projection profile claims full conformance to OKF v0.1 as
  defined by the GoogleCloudPlatform/knowledge-catalog `okf/SPEC.md` pinned at
  commit `d44368c15e38e7c92481c5992e4f9b5b421a801d`. Moving the pin requires a
  reviewed compatibility change.
- **AC-9.2**: One deterministic, on-demand operation projects all in-scope
  canonical knowledge sources without changing their content or authority.
- **AC-9.3**: The bundle records the profile/spec revision, repository/source
  revision, source inventory, explicit exclusions, source digests, stable
  concept identities, and source-to-concept mappings needed for audit and later
  reconciliation.
- **AC-9.4**: Every emitted concept satisfies the pinned minimum schema and uses
  the recommended title, description, resource, tags, and timestamp fields only
  when supported by canonical source evidence.
- **AC-9.5**: Projection emits navigation indexes for progressive disclosure,
  handles the root index/version contract explicitly, and may emit derived log
  entries without making logs a second source of truth.
- **AC-9.6**: Path, concept identity, and collision rules are stable across
  repeated runs and across Claude Code and Codex, including canonical documents
  with the same filename in different directories.
- **AC-9.7**: Internal bundle links are emitted as portable relative references;
  source and citation metadata retains enough provenance to return reviewers to
  the canonical repository evidence.
- **AC-9.8**: Identical repository input, profile pin, and configuration produce
  byte-stable semantic output or a documented deterministic normalization for
  fields whose source values legitimately vary.
- **AC-9.9**: Structural-conformance results and knowledge-health findings are
  emitted as separate artifacts or clearly separated report sections.
- **AC-9.10**: The operation requires no Google reference runtime, external
  service, network access, or new installed-plugin dependency.
- **AC-9.11**: Claude Code and Codex entrypoints produce equivalent bundle
  semantics, source coverage, conformance results, and trace evidence from the
  same canonical checkout.
- **AC-9.12**: Generated projection artifacts are disposable and excluded from
  canonical source discovery; committing one does not make it authoritative or
  eligible for recursive projection.

### 3.10 Guarded External OKF Intake and Validation *(-> HRNS-010)*

- **AC-10.1**: Intake accepts conformant OKF v0.1 bundles, including concepts
  with only the required `type` field and concepts with unknown types or
  extension fields.
- **AC-10.2**: Validation completes before imported content can influence a
  canonical document, mapping/base state, workflow instruction, or generated
  write-back proposal.
- **AC-10.3**: The operation treats bundle content as untrusted data and does
  not execute embedded instructions, commands, scripts, tools, or model prompts.
- **AC-10.4**: Intake is local-first and network-disabled by default. Links,
  resources, and citations are parsed and reported but never fetched
  automatically.
- **AC-10.5**: Bounded-input controls cover bytes, file and concept counts,
  nesting depth, frontmatter/document size, encoding, normalized paths,
  symlinks, workspace escape, duplicate identities, and decompression or parser
  abuse where applicable.
- **AC-10.6**: Structural conformance failures block intake, while specification
  soft conditions and knowledge-health findings remain separately visible as
  warnings or review items.
- **AC-10.7**: Successful intake preserves unknown fields, unknown types,
  Markdown bodies, legal OKF link forms, source provenance, and bundle identity
  in a normalized staging artifact.
- **AC-10.8**: Intake records the repository/base revision against which the
  bundle will be reconciled and rejects missing, ambiguous, stale, or mismatched
  base mappings until an operator chooses a safe recovery path.
- **AC-10.9**: Omitted concepts are classified as absent input, not deletion
  requests; only explicit deletion metadata can enter the later deletion-review
  path.
- **AC-10.10**: Validation reports are bounded, redact secrets, cite concept and
  source locations, and distinguish malformed input, unsupported extensions,
  unsafe paths, conformance failures, health findings, and policy denials.
- **AC-10.11**: Reference-tooling comparison can report compatibility
  differences but cannot reject spec-conformant input solely because the
  reference implementation is stricter than the pinned specification.
- **AC-10.12**: Claude Code and Codex intake surfaces apply the same limits,
  validation profile, preservation rules, exit states, and evidence schema.
- **AC-10.13**: A failed or cancelled intake leaves canonical documents
  unchanged and produces either a bounded diagnostic artifact or a clean no-op.

### 3.11 Conflict-aware OKF Reconciliation and Reviewable Write-back *(-> HRNS-011)*

- **AC-11.1**: Reconciliation compares recorded base, current canonical source,
  and staged incoming knowledge rather than performing a two-way overwrite.
- **AC-11.2**: Each concept is classified as unchanged, local-only change,
  incoming-only change, compatible add, conflict, explicit deletion proposal,
  unmapped, or invalid before any write-back is materialized.
- **AC-11.3**: When both canonical and incoming content changed from the base,
  reconciliation preserves both representations, stops automatic application,
  and requests an explicit resolution.
- **AC-11.4**: Timestamps, file ordering, source priority, and distribution type
  are evidence only; none is an automatic last-write-wins authority.
- **AC-11.5**: Missing incoming concepts never imply deletion. An explicit
  tombstone/deletion proposal must identify the target, base evidence, reason,
  dependent links, and expected impact.
- **AC-11.6**: Operators can accept, reject, edit, or defer each proposed change
  or bounded change group, and unresolved decisions survive resume without being
  silently defaulted.
- **AC-11.7**: Approved changes materialize only in a newly created isolated
  branch/worktree with a bounded diff, source mapping updates, trace packet, and
  verification plan; an optional PR remains draft until a human promotes it.
- **AC-11.8**: Write-back is limited to mapped canonical sources and approved
  additions. It cannot modify protected manifests, policy, hooks, registries,
  generated distributions, or unrelated repository paths.
- **AC-11.9**: Before materialization, the operation revalidates the repository
  revision, bundle digest, spec pin, source mappings, selected decisions, path
  scope, and latest user instruction.
- **AC-11.10**: Reconciliation preserves unknown OKF fields and types in staged
  state and reports any canonical-format limitation or lossy transform as a
  blocking decision.
- **AC-11.11**: The write-back packet links every diff hunk to incoming concept
  provenance, base/local evidence, operator decision, and resulting canonical
  source path.
- **AC-11.12**: Claude Code and Codex surfaces produce equivalent reconciliation
  classifications, safety stops, proposal diffs, and review evidence.
- **AC-11.13**: The workflow never commits to an existing operator branch,
  pushes, opens a PR, merges, deletes a source, or cleans the isolated worktree
  without the authorization required for that distinct action.
- **AC-11.14**: Cancellation and failure preserve a resumable decision packet or
  a reviewable cleanup path and leave canonical repository content unchanged.

## 4. Migration Path

- **Tier 1 (HRNS-001) - Harness taxonomy**: Freeze the surface inventory, gap
  taxonomy, canonical knowledge inventory, and external-candidate evaluation
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
- **Tier 5 (HRNS-007 + HRNS-009) - Resumable work and canonical projection**:
  Harden long-running orchestration while adding the deterministic, on-demand,
  full-conformance OKF v0.1 projection. These specs may proceed in parallel
  after their shared foundations are complete.
- **Tier 6 (HRNS-010) - Guarded external intake**: Validate and stage untrusted
  OKF bundles with bounded local-first controls, extension preservation, and no
  canonical writes.
- **Tier 7 (HRNS-011) - Reconciliation and reviewable write-back**: Add
  three-way conflict handling, explicit deletion proposals, and isolated
  branch/worktree output with human decisions and no automatic merge.
- **Tier 8 (HRNS-008) - Harness maintenance**: Add bounded drift detection and
  self-healing remediation for human-authored, self-generated, projected, and
  externally reconciled harness artifacts.

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
- Keep canonical repository documents authoritative and generate OKF only as an
  on-demand, disposable projection with explicit source mappings and base state.
- Cover root and nested agent guidance, the constitution, PRDs, technical
  roadmaps, MOCs, and workflow/process docs; exclude generated distribution
  copies, caches, fixtures, and generated OKF artifacts from canonical discovery.
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
| Harness Drift, Garbage Collection, and Self-healing Remediation | AC-8.* | HRNS-008 | HRNS-002, HRNS-005, HRNS-006, HRNS-009, HRNS-010, HRNS-011 | P2 |
| OKF v0.1 Canonical Knowledge Projection | AC-9.* | HRNS-009 | HRNS-001, HRNS-002, HRNS-003, HRNS-004, HRNS-005, HRNS-006 | P2 |
| Guarded External OKF Intake and Validation | AC-10.* | HRNS-010 | HRNS-004, HRNS-005, HRNS-006, HRNS-009 | P2 |
| Conflict-aware OKF Reconciliation and Reviewable Write-back | AC-11.* | HRNS-011 | HRNS-007, HRNS-010 | P2 |

## 8. Success Criteria

1. Every acceptance criterion in AC-1.* through AC-11.* is either implemented,
   verified, or intentionally deferred with a documented reason.
2. Each HRNS spec stays within the roadmap reviewability budget or records a
   typed exception before implementation begins.
3. SpecKit Pro can explain and audit its core harness primitives without relying
   on raw chat history or unstated tool behavior.
4. The active helper/runtime/test/review-packet surfaces become more legible and
   safer without adding a heavyweight external harness framework.
5. All canonical harness knowledge can be projected on demand into a bundle
   conforming to the pinned OKF v0.1 specification, with deterministic coverage,
   source provenance, and separate structural/health results.
6. External OKF knowledge can be validated, staged, reconciled, and proposed as
   a bounded reviewable diff without executing imported content, losing unknown
   extensions, using timestamps as conflict authority, or deleting by omission.
7. Claude Code and Codex distributions pass equivalent OKF contract,
   conformance, safety, reconciliation, and trace-evidence checks.

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

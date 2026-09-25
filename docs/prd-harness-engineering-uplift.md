# PRD: SpecKit Pro Harness Engineering Uplift

**Status**: Active. HRNS-001 is complete and archived. HRNS-015 and the
HRNS-017 to HRNS-023 foundation specs are ready.
**Spec ID prefix**: `HRNS-###`
**Source**: Maintainer direction to harden SpecKit Pro as an installed harness,
merged on 2026-09-24 with the Continuous Goal Verification PRD (2026-09-19,
its `VRFY-###` identifiers retired unscaffolded), a completion audit of every
HRNS acceptance criterion against `main`, the typed-judgment opportunity
catalog, and an external working note on Jev engineering for coding agents
(September 2026).
**Created**: 2026-07-03
**Last updated**: 2026-09-24
**Target window**: Repair and foundations first; semantic verification is
promoted beyond shadow only after the HRNS-038 calibration report exists.

---

## 1. Problem

> "How do we make SpecKit Pro's agent workflows legible, resumable, safe, and
> economical, and how does it tell work that is actually complete from work
> that merely looks complete?"

SpecKit Pro now runs long autonomous workflows on two hosts. Three problems
remain, and each has evidence on `main`.

1. **Observed defects keep reaching live runs.** Four of the eight defects
   recorded against autopilot and PR emission are still open. Runs of this
   workflow on other repositories hit three more, and two issues (#637, #638)
   describe gate and template faults.
2. **Completion is decided from signals a fluent agent can satisfy without
   doing the work.** Tasks marked `[X]`, a self-rated confidence composite, an
   FR identifier in a task title, a review reply that sounds like a fix, and a
   terminal summary that says "all tests pass" all count today. Deterministic
   gates catch structural defects but nothing checks the semantic relationship
   between a requirement and the evidence offered for it. Workflow files also
   drift: a status sweep on 2026-09-24 found archived specs whose workflow
   tables still show implementation or post-implementation in progress.
3. **Most of a run's tokens go to finding things, not writing code.** In
   typical coding-agent sessions, reading files, searching, and command output
   take about two thirds of processed tokens while editing code takes under a
   tenth. SpecKit Pro's fan-out roles (three consensus analysts, checklist
   domains, sweep analysts) each re-derive the same evidence.

SpecKit Pro is a plugin, not a host. It controls subagent dispatch prompts and
returns, hooks, skills and references, runner helpers, and files on disk. It
does not control how the host assembles the lead session's context on each
turn. Every feature below binds to a boundary the plugin controls.

## 2. Goals & Non-goals

### 2.1 Goals

- Repair every observed autopilot, gate, and PR-emission defect with a
  fixture that fails before the fix.
- Keep workflow state as typed data with rendered prose, so status cannot
  drift from what actually ran.
- Record every helper run, authorization decision, safe stop, and semantic
  judgment in one additive, replayable journal, and summarize it in the PR.
- Give autonomous runs a deterministic permission and egress policy that
  inspects what a command will do, protects harness-control files, and
  applies one data-sensitivity classification to every outbound request.
- Measure where autopilot's tokens go, then cut the largest cost: shared
  evidence for fan-out roles, query-aware views at dispatch and return
  boundaries, and guidance that loads only when a task touches its path.
- Record, at parent-observed boundaries, which approved obligations have
  current supporting evidence, and say so in a terminal advisory without
  gaining any new authority to stop, continue, apply, or publish.
- Share one versioned typed-decision contract across every Jev consumer, with
  its conformance fixtures owned by the `typesafe-jev` plugin.
- Replace ad hoc model changes with a written eval ladder, a calibrated judge,
  and a model-refresh procedure backed by committed evidence.
- Ship every contract, rubric, and policy for Claude Code and Codex together.

### 2.2 Non-goals (out of scope)

- **The OKF repository-knowledge lane.** HRNS-009 to HRNS-014 and the OKF
  criteria inside HRNS-002 to HRNS-008 are dropped, not deferred. No work had
  started, the lane was gated behind five foundation specs, and a lighter
  glossary (#541) and condition-bound guidance (HRNS-021) cover the need.
- **A model-routing program.** Per-agent models and efforts live in
  `speckit-pro/speckit_pro_runner/agent_inventory.json` and change through the
  HRNS-022 model-refresh procedure. The Codex routing roadmap was retired.
- **Controlling the lead session's context, cache, or compaction.** These are
  host-owned. HRNS-020 measures them offline instead.
- **Duplicating the delegation runtime.** The delegation runtime owns the
  worker-side context packet, goal reuse, tool disclosure, path-scoped lessons,
  routing, escalation, and spend preference for delegated tasks.
- Any new authority. A Jev result never authorizes implementation, suppresses
  a required check, applies a patch, opens or merges a PR, resolves a thread,
  or ends a session.
- A second provider client. Credentials, provider selection, HTTP, retries,
  and validation stay in the `typesafe-jev` plugin.
- An event-sourcing rewrite of workflow state. The journal is additive.
- Expanding sweep-worker capabilities. Sweep roles keep their closed broker
  surface.
- Adopting an external harness, orchestration, eval, trace, or guardrail
  framework, or comparing them. Native eval runners (#578) and stdlib JSON
  Schema are the chosen substrates.
- Paid Jev calls in ordinary CI or unit tests.

## 3. Acceptance Criteria

### 3.1 Harness Surface Inventory and Gap Taxonomy *(-> HRNS-001, complete)*

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

### 3.2-3.14 Retired features

These identifiers are permanently reserved and never reused. Their surviving
acceptance criteria moved to the features named below.

| Feature | Former SPEC | Disposition |
|---|---|---|
| Progressive Context and Durable State Contract (AC-2.*) | HRNS-002 | Autopilot state, resume, and freshness shipped with other work. Remainder moved to HRNS-018 and HRNS-021. Context-health zones (AC-2.9) dropped: a plugin cannot observe the lead's context. OKF criteria dropped. |
| Helper, Tool, and Capability Contract (AC-3.*) | HRNS-003 | Remediation messages shipped. Remainder moved to HRNS-019; untrusted tool annotations to HRNS-026. The schema-library comparison is superseded by stdlib JSON Schema. OKF criteria dropped. |
| Permission, Sandbox, and Pre-action Authorization Controls (AC-4.*) | HRNS-004 | Per-surface authorization shipped. Remainder moved to HRNS-026; risk flags split with HRNS-019; promotion gates to HRNS-021. OKF criteria dropped. |
| Feedback Sensors and Eval Readiness Ladder (AC-5.*) | HRNS-005 | Native eval runners (#578) supersede the vendor comparison. Remainder moved to HRNS-022; stale-downstream detection to HRNS-023. OKF criteria dropped. |
| Trace, Debug, and Review Evidence Packets (AC-6.*) | HRNS-006 | Moved to HRNS-025. External telemetry sinks dropped. OKF criteria dropped. |
| Long-horizon Orchestration and Resumption Controls (AC-7.*) | HRNS-007 | Ownership, dependency edges, role separation, and run caps shipped for autopilot. Remainder moved to HRNS-018, HRNS-026, and HRNS-036; eval-job caps to HRNS-022. The framework comparison is dropped. OKF criteria dropped. |
| Harness Drift, Garbage Collection, and Self-healing Remediation (AC-8.*) | HRNS-008 | Non-OKF drift moved to HRNS-023. OKF criteria dropped. |
| Host Repository OKF Knowledge Contract and Initialization (AC-9.*) | HRNS-009 | Dropped. |
| Incremental Evidence Ingest and Knowledge Synthesis (AC-10.*) | HRNS-010 | Dropped. |
| Knowledge Query, Citation, and Compounding Capture (AC-11.*) | HRNS-011 | Dropped. Lesson capture moved to HRNS-021. |
| Knowledge Conformance, Health, and Drift Maintenance (AC-12.*) | HRNS-012 | Dropped. |
| Code-Intelligence and Vector-Index Interoperability (AC-13.*) | HRNS-013 | Dropped. |
| External OKF Exchange and Reviewable Reconciliation (AC-14.*) | HRNS-014 | Dropped. |

The Continuous Goal Verification PRD's `VRFY-001` to `VRFY-012` identifiers
and its `AC-1.*` to `AC-12.*` criteria are also retired; the crosswalk in §8
names where each group went.

### 3.15 Per-story Autopilot Execution *(-> HRNS-016)*

Heavy upfront planning followed by one large implementation pass is the
failure mode the "Quality Gauntlet" memo names: do one story, check the
architecture, repeat. SpecKit's own templates already shape the work this way.
The spec template requires every user story to be independently testable
(`.specify/templates/spec-template.md`: "Each user story/journey must be
INDEPENDENTLY TESTABLE", with a per-story `**Independent Test**` line), and the
tasks template groups tasks by story behind a Setup and a Foundational phase
with a checkpoint after each story (`.specify/templates/tasks-template.md`:
"Tasks MUST be organized by user story so each story can be: Implemented
independently, Tested independently", `**Checkpoint**: At this point, User
Story 1 should be fully functional and testable independently`). Phase 7 of
autopilot flattens that structure into task groups and verifies once at the
end. This feature makes the story the unit of execution, verification, and
review.

- **AC-15.1**: Phase 7 runs the Setup and Foundational task phases once, then
  iterates the user stories in the priority order `tasks.md` records, one story
  at a time; a story does not start until the previous story's checkpoint is
  recorded.
- **AC-15.2**: Each story runs the same sequence: implement its tasks, run the
  automated checks and every populated quality-gate slot on the story's diff,
  run the hardener when MUTATION is populated, run an architecture check
  against the plan's Module and Interface Deltas and the dependency rules, then
  record the story checkpoint in the workflow file.
- **AC-15.3**: Each story opens its own pull request with the story's
  Independent Test as its verification section. When `gh-stack` and its skill
  are installed, the spec is one stack rooted on trunk with one PR per story in
  priority order; otherwise each story is an independent branch off trunk, and
  the workflow file records which mode was selected and why.
- **AC-15.4**: The loop continues while every check is green and stops on the
  first failing check, naming the story, the check, and the evidence path; a
  resume starts from the last recorded checkpoint, never from the beginning.
- **AC-15.5**: The added review overhead of one PR per story is accepted and
  stated in the PR body; reducing it (batching small stories, auto-merging
  green stack layers) is out of scope and recorded as a follow-on.
- **AC-15.6**: Claude Code and Codex run the same per-story loop with the same
  checkpoint record, PR-per-story rule, and stop rule.

### 3.16 Autopilot, Gate, and PR-Emission Repair *(-> HRNS-015)*

- **AC-16.1**: A packet emitted by the documented path produces a body that
  passes a host repository's release-note gate, proven by a fixture carrying
  the required fence, or a documented and exercised host-body hook.
- **AC-16.2**: A fixture proves the post-implementation sequence refuses to
  report completion while any entry is unexecuted, on both hosts, and the
  entry count is stated once and read everywhere.
- **AC-16.3**: The packet write-validation contract states which outcome is
  success when packets are untracked in the host repository, with a fixture.
- **AC-16.4**: Executors that can form agent teams carry a teardown
  obligation, and a structural check proves it.
- **AC-16.5**: The gap counter matches `[Gap` rather than `[Gap]`, with a
  fixture for the `[Gap, <ref>]` form.
- **AC-16.6**: The spec-index walk excludes untracked files as well as ignored
  ones, and a check runs the index against the real repository tree and fails
  on drift.
- **AC-16.7**: `speckit-resolve-pr` fetches every review-thread and comment
  page before claiming feedback is handled, and replies and resolves only after
  final verification and a confirmed pushed SHA.
- **AC-16.8**: The scaffold blind-spot pass reports an expired wait as a
  finding rather than silently skipping, a detected quality-gate command honors
  the host repository's documented test command, and spec-size estimation
  counts required refactors.
- **AC-16.9**: Reviewability-gate setup mode checks every roadmap entry and
  honors a typed `Reviewability-Exception` pragma (#637), and the roadmap
  template links workflow files where scaffold writes them (#638).
- **AC-16.10**: Every runner helper a skill tells the agent to call is shown
  with a complete request envelope in that skill's prose.

### 3.17 Host Capability Spike *(-> HRNS-017)*

- **AC-17.1**: A spike report records actual HEAD, the authoritative
  `agent_inventory.json` role set, the helper registry envelope, and exact
  `file:line` integration points for prepare, invoke, consume, and record on
  Claude Code and Codex.
- **AC-17.2**: For each host, the report states whether a native `evaluate`
  result is visible to the live parent before its decisions are sealed, and
  classifies the achievable posture as `isolated_shadow`,
  `retrospective_shadow`, or `advisory_not_authorized`.
- **AC-17.3**: The report records, by native observation, whether each host
  lets a hook replace a built-in tool's output, whether Codex exposes a
  prompt-time hook, how two plugins' Stop hooks interact when one continues
  the turn, and how per-turn hook text from several plugins shares the lead's
  context.
- **AC-17.4**: The report classifies each inherited finding against current
  source as open, resolved, or unverified.
- **AC-17.5**: The spike changes no shipped source, installs nothing into user
  registries, and makes no paid provider call.

### 3.18 Typed Workflow State *(-> HRNS-018)*

- **AC-18.1**: Phase, gate, and post-implementation status live in a typed
  JSON record per workflow; the workflow file's status tables are rendered from
  it, and a check fails when the rendered tables and the record disagree.
- **AC-18.2**: Speckit-status reads the typed record, so an archived spec
  can never report a phase in progress.
- **AC-18.3**: PRD authoring, scaffold, resolve-pr, and archive record
  resumable next-action state, not only autopilot.
- **AC-18.4**: Freshness checks cover roadmap and archive pointers in addition
  to the existing workflow binding and stage mirror.
- **AC-18.5**: On resume, the user's latest instruction takes precedence over
  older recorded context, and a conflicting live run is reported with a
  documented policy instead of proceeding silently.
- **AC-18.6**: Resume reloads only the recorded chunks the next step needs,
  addressed by stable identifiers, rather than re-reading whole artifacts.
- **AC-18.7**: Both hosts read and write the same record shape.

### 3.19 Helper Registry Contract and Tiered Disclosure *(-> HRNS-019)*

- **AC-19.1**: Each registry entry declares purpose, owner workflow, linked
  input and output schemas, and risk flags (read-only, mutating, destructive,
  networked, credential-bearing, untrusted-content, approval-required).
- **AC-19.2**: Helper reference docs and skill-facing request examples are
  generated from the registry, and a check fails when they drift.
- **AC-19.3**: The mutation fixture manifest covers every dispatchable
  mutation helper.
- **AC-19.4**: Helpers are disclosed in tiers: a one-line index, a schema on
  request, and documentation on request, so no skill loads the whole registry.
- **AC-19.5**: An agent can resolve a stated intent to a helper and receive a
  validated envelope; a wrong argument becomes a validation error with
  remediation, never a silent failure.

### 3.20 Autopilot Token Baseline *(-> HRNS-020)*

- **AC-20.1**: A committed harness measures one autopilot run per host and
  reports processed-token share by activity: file reads, search, command
  output, reasoning, editing, and fixed prompt overhead.
- **AC-20.2**: The report attributes tokens to the lead and to each subagent
  role, and names the largest repeated read.
- **AC-20.3**: Results carry intervals; an insufficient sample never counts as
  a pass, and pass, fail, insufficient, and error have distinct exit codes.
- **AC-20.4**: A baseline for the current release is committed, and HRNS-028
  and HRNS-029 report their effect against it.
- **AC-20.5**: Measurement reads host transcripts or usage records the host
  documents; unknown usage stays unknown, never zero.

### 3.21 Condition-Bound Guidance and Lesson Promotion *(-> HRNS-021)*

- **AC-21.1**: A per-directory guidance file (a "footguns" file) is loaded
  into an executor's dispatch when the task's owned paths fall under that
  directory, selected deterministically from task ownership.
- **AC-21.2**: Condition-bound guidance is re-supplied at every dispatch whose
  condition holds, so compaction of an earlier turn cannot remove it.
- **AC-21.3**: Skill and workflow entrypoints stay short maps that point to
  deeper references, and a check reports entrypoints that grow past a
  documented size without references.
- **AC-21.4**: A lesson moves from agent memory to a scoped guidance file, and
  from there to `AGENTS.md`, only through a reviewable proposal with
  provenance, secret screening, and a size bound.
- **AC-21.5**: Scaffold can create the guidance layout in a host repository
  when asked, and never writes to a repository merely because the plugin is
  installed.
- **AC-21.6**: Optional shadow checks for lesson durability and relevant-lesson
  retrieval (JEV-045, JEV-046) run only when HRNS-027 is enabled.

### 3.22 Eval Ladder and Model Refresh *(-> HRNS-022)*

- **AC-22.1**: A written ladder names each verification rung (structural,
  fixture parity, deterministic regression, native behavioral eval, judge
  review, live qualification) and whether it blocks or advises.
- **AC-22.2**: The evaluator hierarchy is written down: deterministic tests
  and formal checks outrank fixture parity, which outranks a judge, which
  outranks self-assessment; self-assessment alone never approves a
  harness-control change.
- **AC-22.3**: The native eval judge can return `insufficient_evidence`, and
  its verdicts are calibrated against labeled known-good and known-bad cases.
- **AC-22.4**: Every fixture added after a failure carries reproduction
  evidence, a root-cause label, and the regression command; a change without a
  fixture records a discard rationale.
- **AC-22.5**: A model-refresh procedure governs every change to a model or
  effort in `agent_inventory.json`: a pre-registered comparison on native evals
  with cost, tokens, and new failures reported, and the evidence committed with
  the change.
- **AC-22.6**: Eval reports name the model, plugin version, runner version,
  allowed tools, and permission mode.
- **AC-22.7**: Long inspection and eval jobs record cost, time, and scope caps
  with a continuation plan when the work exceeds the run.

### 3.23 Harness Drift Scanner *(-> HRNS-023)*

- **AC-23.1**: A scanner reports stale skill and reference prose (counts, file
  paths, line references, retired helpers), status drift between roadmaps and
  workflow records, dead helper references, and orphaned process files.
- **AC-23.2**: Every finding cites concrete repository evidence and is
  classified as a remediation or a no-op.
- **AC-23.3**: Output is bounded into reviewable batches and never a broad
  speculative cleanup.
- **AC-23.4**: The report states what was scanned, what was skipped, and why.
- **AC-23.5**: Changes to planning inputs mark downstream plans, fixtures, and
  docs stale until they are regenerated or marked not applicable.

### 3.24 Shared Typed-Decision Contract *(-> HRNS-024)*

- **AC-24.1**: A language-neutral JSON contract defines decision identity and
  version, projection, rubric, normalizer, and policy identities with hashes,
  preconditions, and `authority_owner`. Its schema and conformance fixtures
  live in the `typesafe-jev` plugin, and every consumer validates against the
  same fixtures.
- **AC-24.2**: Registered runner operations `prepare-semantic-check` and
  `assess-semantic-check` exist with promotion status and request fixtures, and
  no skill instructs their use before registration.
- **AC-24.3**: The wire projection sends only provider-supported `state`,
  `questions`, and selected model fields; local run, workflow, correlation, and
  consent identities are excluded, proven by test.
- **AC-24.4**: Normalization handles Noul, Choice, and Score separately.
  Malformed JSON, duplicate keys, non-finite numbers, unknown options, omitted
  answers, refusals, and unknown model identity each produce an explicit
  non-success state, never a positive judgment, and a malformed answer is
  rejected rather than repaired. A security decision fails closed.
- **AC-24.5**: Receipts keep `execution_status`, `coverage`,
  `semantic_outcomes`, `freshness`, `provenance`, and `policy_interpretation`
  separate; `execution_status=complete` means the request was answered, not
  that a goal is complete. An absent confidence stays absent.
- **AC-24.6**: Canonicalization is versioned, measures serialized UTF-8 size,
  and checks the provider's documented token budgets with a labeled estimate.
- **AC-24.7**: Questions use the string-only form both supported backends
  accept, and receipts record requested and reported model identities.
- **AC-24.8**: The research broker's existing Jev screening is migrated onto
  the contract as its first consumer, with unchanged screening outcomes on its
  existing fixtures.

### 3.25 Run Journal and PR Trace Summary *(-> HRNS-025)*

- **AC-25.1**: One additive JSON-lines journal per run records helper runs,
  authorization decisions, safe-stop reasons, subagent lineage (role, input,
  output, model, and provider where available), and decision events
  (`DecisionRequested`, `DecisionSkipped`, `DecisionEvaluated`,
  `DecisionFailed`, `DecisionMarkedStale`, `PolicyInterpreted`) with per-run
  sequence, correlation and causation identities, and source revision.
- **AC-25.2**: Failures carry one layer classification: context, constraint,
  permission, infrastructure, verification, planning, implementation, or
  external dependency.
- **AC-25.3**: Duplicate delivery yields one observation, an interrupted
  append is detectable, a partial record is never read as a completed
  judgment, and worker-authored JSON cannot be promoted to an observed result.
- **AC-25.4**: Sensitive payloads live in a separate, bounded evidence store
  referenced by digest; deletion leaves an explicit unavailable marker.
- **AC-25.5**: Offline replay reproduces deterministic decisions, re-applies
  thresholds to stored Jev answers without a new call, and reports each
  non-replayable row with a cause; counterfactual policy simulation edits
  nothing. Both make zero provider, dispatch, apply, push, or resolve calls.
- **AC-25.6**: A crash after send and before record leaves the request
  unknown; no automatic retry is billed on the assumption that it failed.
- **AC-25.7**: The PR body carries a compact, secret-screened trace summary
  (what ran, outcome, evidence paths, known gaps, next action) and the
  confidence-gate verdict.
- **AC-25.8**: The journal stays local; nothing is sent to an external
  telemetry service.

### 3.26 Autonomous-Run Permission and Egress Policy *(-> HRNS-026)*

- **AC-26.1**: During autonomous runs, a deterministic command policy denies
  access to credential stores and environment secrets, denies network egress
  from scripts unless the task scope allows it, asks before writes outside the
  worktree, and allows a declared read-only set; script contents are inspected
  before execution, not only the command name.
- **AC-26.2**: Harness-control files (plugin manifests, hooks, MCP config,
  helper registry, runner manifest, quality-gates file, policy files) cannot
  be modified by an autonomous run without an explicit, reviewable diff.
- **AC-26.3**: Repeated denials, workspace escape attempts, and harness-policy
  mutation attempts stop the run and name the cause.
- **AC-26.4**: Claude Code enforces the same write-root and authorization
  boundary Codex enforces before implementation.
- **AC-26.5**: One data-sensitivity classification (open, standard,
  restricted, custom) governs every egress: Jev provider calls, the research
  broker, and handoffs to the delegation runtime. A classification can only
  narrow what leaves the machine, never authorize new egress.
- **AC-26.6**: Tool annotations from untrusted MCP servers stay advisory until
  enforced by this policy, and `SECURITY.md` describes the allowlist behavior
  the code actually has.
- **AC-26.7**: A decision record documents the Jev screening dependency in
  the research broker: what it decides, what happens when it is unavailable,
  and why that is acceptable.
- **AC-26.8**: Optional shadow advice for ambiguous commands (JEV-074) and a
  sensitivity label for content (JEV-075) run only when HRNS-027 is enabled;
  advice can only escalate to "ask", and a label can only restrict.

### 3.27 Dual-Host Jev Adapter *(-> HRNS-027)*

- **AC-27.1**: Capability discovery lists an optional typed-judgment
  capability without a hardcoded vendor preference, and the trusted parent on
  each host invokes the registered `evaluate` tool.
- **AC-27.2**: Per-project enablement defaults to off; with it off, the runner
  introduces no provider request, credential discovery, new diagnostic write,
  or changed gate or dispatch result, proven by byte comparison of existing
  fixtures.
- **AC-27.3**: Before each request the adapter checks project consent, the
  provider and model pairing, the HRNS-026 data classification, and the
  remaining Jev call, input, and spend budget, with a per-call timeout; a
  failure skips the call and records `DecisionSkipped`.
- **AC-27.4**: Requested and reported model identities are both recorded; a
  differing reported identity marks the result `unqualified`.
- **AC-27.5**: Sweep roles gain no `evaluate` access, secrets, or filesystem
  scope, and a test proves the agent inventory and role allowlists unchanged.
- **AC-27.6**: Claude Code and Codex adapters pass the same contract fixtures,
  and a parity test proves the named `consensus-synthesizer` binding and all
  current gates, budgets, and permissions are preserved on both hosts.
- **AC-27.7**: Key values never appear in runner output, journal entries, or
  test logs.

### 3.28 Shared Retrieval Packet for Fan-Out Roles *(-> HRNS-028)*

- **AC-28.1**: Each consensus item and checklist domain gets one immutable,
  snapshot-bound evidence packet (relevant files, symbols, diff spans, and
  their digests) that every analyst in the fan-out reads, with fetch on
  demand for anything outside it.
- **AC-28.2**: Each role receives its own projection of the shared packet;
  one analyst's opinion is never shared with another or with the synthesizer
  as evidence.
- **AC-28.3**: Tasks and fan-out roles declare read or write intent; read-only
  work runs in parallel without contention, and writers keep ownership locks.
- **AC-28.4**: An HRNS-020 comparison shows the packet's effect on repeated
  reads and total tokens, with the same or better outcome on the native evals.
- **AC-28.5**: Optional shadow relevance ranking for code, research passages,
  and coupling warnings (JEV-003, JEV-004, JEV-029) runs only when HRNS-027
  is enabled and never removes evidence required by a check.

### 3.29 Visibility Ladder and Handoff Preservation *(-> HRNS-029)*

- **AC-29.1**: Evidence handed to or returned from a subagent carries a view
  level (hide, short, long, full); required evidence and unresolved errors are
  never hidden, and every lower view keeps a handle to the raw content.
- **AC-29.2**: Subagent returns lead with an index and let the parent fetch
  detail on demand, instead of returning full transcripts.
- **AC-29.3**: Long command and test output is reduced to the failing trace
  and cause with a raw handle, on each host where HRNS-017 found a supported
  hook; elsewhere the limitation is documented.
- **AC-29.4**: Phase-handoff and resume packets are checked, deterministically
  first, for every open obligation, unresolved failure, and constraint; an
  omission is recovered from the source before the next agent reasons from
  the summary.
- **AC-29.5**: A documented rule decides when to continue an existing
  subagent and when to start a fresh one.
- **AC-29.6**: Optional shadow checks for reference relevance, per-chunk view
  level, reuse versus respawn, and handoff obligation preservation (JEV-002,
  JEV-072, JEV-073, JEV-068) run only when HRNS-027 is enabled.

### 3.30 Obligation and Subgoal Registry *(-> HRNS-030)*

- **AC-30.1**: At kickoff or resume, approved goals become versioned
  obligations with stable id, goal version, source reference and provenance,
  owning phase or task, applicability rule, required observations, semantic
  predicates, and dependencies, reusing existing FR and task ids.
- **AC-30.2**: An empty applicable required set is rejected as `invalid_goal`.
- **AC-30.3**: Obligations are stage-relative: a planning-stage goal never
  requires implementation evidence or labels implementation complete.
- **AC-30.4**: Rewording does not change identity; a goal change is an explicit
  versioned event that invalidates dependent judgments; the model cannot add,
  drop, or weaken an obligation.
- **AC-30.5**: Every subtask is registered before dispatch and compared with
  completed and in-flight subtasks by exact key; identical work is never
  launched twice.
- **AC-30.6**: Optional shadow recognition of reworded repeats of one defect
  (JEV-030) attaches them to the same obligation and runs only when HRNS-027
  is enabled.

### 3.31 Pilot: Requirement-to-Task Semantic Coverage *(-> HRNS-031)*

- **AC-31.1**: After Tasks (G5), each source-backed atomic requirement gets
  one Noul asking whether the linked task set plans the behavior, with planned
  behavior, failure cases, and required evidence recorded separately.
- **AC-31.2**: The structural G5 helper remains authoritative; the semantic
  result is an annotation that changes no gate outcome, task count, or repair
  reservation.
- **AC-31.3**: One uncovered required obligation is reported regardless of
  how many others are covered.
- **AC-31.4**: A relevant plan or task edit marks dependent judgments stale.
- **AC-31.5**: Fixtures cover a task that only repeats the FR id, a paraphrased
  plan, a missing sub-obligation, and planning coverage presented as
  implementation completion.

### 3.32 Pilot: Review-Fix Closure Verification *(-> HRNS-032)*

- **AC-32.1**: For each thread, a closure judgment consumes the original
  concern, full thread, before and after source, acceptance condition, actual
  verification observations, and pushed SHA, and records whether the concern
  was addressed or rebutted with evidence.
- **AC-32.2**: The judgment is an annotation only; no reply or resolution is
  made from a model result, and missing verification cannot become resolved.
- **AC-32.3**: A later relevant edit invalidates the closure judgment.
- **AC-32.4**: Fixtures cover a fix to the wrong path, a superficially similar
  edit, a correct fix without execution evidence, a supported false-positive
  rebuttal, an omitted comment, and a new regression.

### 3.33 Pilot: Claim-to-Source Support Annotation *(-> HRNS-033)*

- **AC-33.1**: Citations are resolved mechanically first; only then is one
  Choice with `supports`, `contradicts`, `does_not_address`, and
  `insufficient_context` asked over the exact claim and retrieved span.
- **AC-33.2**: The output is an annotation linked to the original finding;
  the finding is never rewritten or suppressed, and the full distribution is
  retained.
- **AC-33.3**: A later source edit marks affected judgments stale.
- **AC-33.4**: Fixtures cover a real but irrelevant citation, paraphrased
  support, opposite behavior, missing branch context, a missing source, and
  instruction-like text embedded in evidence.

### 3.34 Phase-Boundary Goal-Completion Verifier *(-> HRNS-034)*

- **AC-34.1**: At phase handoff and proposed terminal summary, the trusted
  parent reconciles the complete applicable obligation set.
- **AC-34.2**: The aggregator emits `invalid_goal`,
  `known_unmet_obligation_ids`, `missing_authoritative_evidence_ids`,
  `unjudged_or_uncertain_semantic_ids`, `stale_assessment_ids`,
  `unresolved_effects`, `mandatory_work_still_pending`, and
  `completion_suggestion_eligible`; no field hides another.
- **AC-34.3**: Eligibility is true only when the goal is valid and every
  applicable required obligation has current observations and an acceptable
  assessment; it remains a suggestion, never a gate result.
- **AC-34.4**: Expected TDD RED is recognized and does not trigger corrective
  work.
- **AC-34.5**: The existing G6.5 confidence block and named synthesizer are
  unchanged; a readiness vector beside G6.5 shows the weakest evidenced
  obligations with source links (JEV-028), and Jev confidence is never
  substituted for the composite score.
- **AC-34.6**: On a host where the `evaluate` result is visible to the live
  parent, the run is labeled `advisory_mode_required` and shadow evidence is
  collected only offline or after the run.

### 3.35 Change-Triggered Scheduler and Invalidation *(-> HRNS-035)*

- **AC-35.1**: Only parent-observed boundaries schedule checks: consumed
  worker results, relevant source, task, test, or goal changes, phase
  handoffs, terminal summaries, and cancellation or revoked consent.
- **AC-35.2**: A repeated unchanged-state callback creates no extra
  evaluation; cache keys exclude timestamps and attempt identities.
- **AC-35.3**: Unknown dependency coverage invalidates the larger scope; a
  late response after cancellation, goal revision, or supersession is kept as
  stale and never applied.
- **AC-35.4**: One in-flight check per decision, projection, and run; a
  verifier result, journal append, or status render never schedules another.
- **AC-35.5**: User cancellation and the existing repair budgets dominate;
  an exhausted Jev call budget never becomes success.

### 3.36 Premature-Stop and Redundant-Continuation Advice *(-> HRNS-036)*

- **AC-36.1**: Before a terminal summary, a premature-done advisory names the
  unsatisfied obligation ids and missing evidence; a redundant-continuation
  advisory names the satisfied goal and the out-of-scope proposed work.
- **AC-36.2**: A completion claim such as "all tests pass" is reconciled
  against the producer evidence it cites, and an unsupported claim is named
  in the advisory (JEV-036).
- **AC-36.3**: Neither advisory ends a session, loops a worker, switches
  models, resets a budget, skips a gate, or bypasses publication, UAT, or
  approval obligations; user cancellation always wins.
- **AC-36.4**: Stop conditions are explicit for blocked infrastructure,
  missing user decisions, repeated denials, repeated test failures, and
  impossible branch or worktree state.
- **AC-36.5**: Provider outage never traps a host stop path, and the advisory
  coexists with other plugins' Stop hooks as HRNS-017 recorded.

### 3.37 Live Run Progress Page *(-> HRNS-037)*

- **AC-37.1**: An opt-in, read-only progress page renders the current phase,
  gate results, open tasks, and checkpoints from the HRNS-018 typed record,
  updated at phase boundaries.
- **AC-37.2**: The page carries no secrets, local paths, or raw transcript
  text, and is published only when the operator enables it.
- **AC-37.3**: When HRNS-034 is present, the page shows semantic health
  separately from workflow progress: uncovered requirements, stale judgments,
  and checks not run (JEV-048).
- **AC-37.4**: A missing or failed page never blocks or slows the run.

### 3.38 Trajectory Calibration and Gated Live Evaluation *(-> HRNS-038)*

- **AC-38.1**: A frozen, human-labeled trajectory corpus with intermediate
  goals, evidence, revisions, results, and proposed termination points exists
  under the test tree, split into development and holdout sets, with labels
  held separately from model outputs.
- **AC-38.2**: Offline replay compares phase-end with change-triggered
  verification on the same trajectories at equal permitted work, and reports
  run-level false completion, early missed-obligation detection, false alarms,
  unnecessary continuation, coverage, and overhead, with uncertainty on every
  rate.
- **AC-38.3**: Every attempt, refusal, and unavailable case is retained;
  repeated same-state queries are rejected as score shopping; the holdout is
  never used to tune thresholds.
- **AC-38.4**: Live evaluation requires an explicit manifest naming consent,
  provider and pinned model, hosts, request, spend, and time caps, failure
  behavior, corpus, and success criteria; default caps authorize zero live
  requests and CI denies provider egress even when credentials exist.
- **AC-38.5**: Promotion of any check from shadow to advisory is a reviewed
  decision citing this report; the report never substitutes for deterministic
  release gates.

## 4. Migration Path

- **Tier 1 (start now, in parallel):** HRNS-015 repair; HRNS-017 host spike;
  HRNS-018 typed state; HRNS-019 registry contract; HRNS-020 token baseline;
  HRNS-021 condition-bound guidance; HRNS-022 eval ladder and model refresh;
  HRNS-023 drift scanner.
- **Tier 2:** HRNS-016 per-story autopilot after HRNS-015; HRNS-024 decision
  contract after HRNS-017; HRNS-026 permission and egress policy after
  HRNS-019; HRNS-028 and HRNS-029 context economy after HRNS-020; HRNS-037
  progress page after HRNS-018.
- **Tier 3:** HRNS-025 run journal; HRNS-030 obligation and subgoal registry.
- **Tier 4:** HRNS-027 dual-host adapter, the only slice that touches the wire.
- **Tier 5:** HRNS-031, HRNS-032, and HRNS-033 shadow pilots; HRNS-034
  phase-boundary verifier.
- **Tier 6:** HRNS-035 change-triggered scheduler.
- **Tier 7:** HRNS-036 stop advice; HRNS-038 trajectory calibration.

A feature with an optional Jev shadow check ships its deterministic core on
the dependencies above. Its Jev check is a later slice that waits for HRNS-027.

## 5. Module and Interface Deltas

| Feature (§3) | Module or interface | Delta | Note |
|---|---|---|---|
| Harness Surface Inventory (§3.1) | No module or interface changes. | - | Complete and archived |
| Per-story Autopilot (§3.15) | `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and the Codex mirror | changed | Task-group loop becomes a story loop |
| Per-story Autopilot (§3.15) | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` and the Codex mirror | changed | Per-story PR emission |
| Per-story Autopilot (§3.15) | `speckit-pro/skills/speckit-coach/templates/workflow-template.md` | changed | Per-story checkpoint table |
| Repair (§3.16) | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | changed | Release-note field or body hook; untracked-packet outcome |
| Repair (§3.16) | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | changed | `[Gap` matching; untracked-file exclusion in the spec-index walk; spec-size refactor count |
| Repair (§3.16) | `speckit-pro/skills/speckit-autopilot/` and the Codex mirror | changed | Self-verifying Post list; team teardown |
| Repair (§3.16) | `speckit-pro/skills/speckit-resolve-pr/SKILL.md` | changed | Full pagination; verify, push, then reply and resolve |
| Repair (§3.16) | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, reviewability gate helper, roadmap template | changed | Blind-spot expiry finding; #637; #638 |
| Repair (§3.16) | `.github/workflows/pr-checks.yml` | changed | Real-tree spec-index check |
| Host Spike (§3.17) | `docs/ai/specs/harness-engineering-uplift-host-capability-spike.md` | new | Report only |
| Typed State (§3.18) | `speckit-pro/speckit_pro_runner/contracts/workflow-state.schema.json` | new | Typed phase, gate, and Post record |
| Typed State (§3.18) | workflow-file rendering helper in `speckit-pro/speckit_pro_runner/helpers/` | new | Renders status tables from the record |
| Typed State (§3.18) | `speckit-pro/skills/speckit-status/SKILL.md` | changed | Reads the typed record |
| Registry (§3.19) | `speckit-pro/speckit_pro_runner/helpers/registry.py` | changed | Purpose, owner, schema links, risk flags |
| Registry (§3.19) | `docs-site/scripts/generate-reference-pages.mjs` | changed | Helper pages generated from the registry |
| Token Baseline (§3.20) | `tests/speckit-pro/evals/` token-share harness | new | Measurement and committed baseline |
| Guidance (§3.21) | autopilot dispatch references and the Codex mirror | changed | Path-conditional guidance in dispatch prompts |
| Guidance (§3.21) | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | changed | Optional guidance layout for host repositories |
| Eval Ladder (§3.22) | `tests/speckit-pro/lib/native_eval_judge.py` | changed | `insufficient_evidence` verdict and calibration |
| Eval Ladder (§3.22) | `tests/speckit-pro/evals/README.md` | changed | Written ladder, hierarchy, model-refresh procedure |
| Drift Scanner (§3.23) | `scripts/` drift scanner | new | Bounded, evidence-cited report |
| Decision Contract (§3.24) | `typesafe-jev/` contract schema and conformance fixtures | new | Shared by every Jev consumer |
| Decision Contract (§3.24) | `speckit-pro/speckit_pro_runner/semantic_checks.py` | new | Prepare, normalize, assess, canonicalize |
| Decision Contract (§3.24) | `speckit-pro/speckit_pro_runner/helpers/registry.py` | changed | Registers `prepare-semantic-check`, `assess-semantic-check` |
| Decision Contract (§3.24) | `speckit-pro/speckit_pro_runner/research_broker.py` | changed | Screening moves onto the contract |
| Run Journal (§3.25) | `speckit-pro/speckit_pro_runner/run_journal.py` | new | Append, replay, simulate; evidence-store reference |
| Run Journal (§3.25) | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | changed | Trace summary and confidence verdict in the body |
| Permission Policy (§3.26) | `speckit-pro/scripts/workflow-guard-hook.py` and a policy file | changed | Command policy, content inspection, protected files |
| Permission Policy (§3.26) | `SECURITY.md` | changed | Allowlist wording matches behavior |
| Jev Adapter (§3.27) | `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` | changed | Optional typed-judgment capability |
| Jev Adapter (§3.27) | project semantic-check configuration | new | Enablement, consent, caps; default off |
| Retrieval Packet (§3.28) | consensus and checklist dispatch references | changed | Shared packet per item or domain |
| Retrieval Packet (§3.28) | `speckit-pro/speckit_pro_runner/` retrieval-packet builder | new | Snapshot-bound, digest-checked packet |
| Visibility Ladder (§3.29) | dispatch and return contracts in autopilot references | changed | View levels and index-first returns |
| Visibility Ladder (§3.29) | handoff check helper | new | Deterministic obligation preservation check |
| Obligation Registry (§3.30) | `speckit-pro/speckit_pro_runner/goal_obligations.py` | new | Frozen obligations and subgoal keys |
| Obligation Registry (§3.30) | `speckit-pro/speckit_pro_runner/execution_control.py` | changed | Subgoal registration before dispatch |
| Pilots (§3.31-3.33) | Tasks G5 handoff, resolve-pr, grounding boundary | changed | Shadow annotations beside existing results |
| Verifier (§3.34) | `speckit-pro/speckit_pro_runner/goal_verifier.py` | new | Reconciliation and aggregation vector |
| Scheduler (§3.35) | `speckit-pro/speckit_pro_runner/goal_verifier.py` | changed | Dirty tracking, coalescing, single-flight |
| Stop Advice (§3.36) | autopilot pre-terminal summary reference | changed | Advisory block with obligation ids |
| Progress Page (§3.37) | progress-page renderer | new | Read-only page from the typed record |
| Calibration (§3.38) | `tests/speckit-pro/trajectories/` | new | Frozen corpus, holdout, replay report |

## 6. Constraints

- Follow `.specify/memory/constitution.md`: Python 3.11+ standard library for
  repository tooling, no active Bash or `jq`, unit coverage before merge,
  source under `speckit-pro/` with regenerated payloads, release-please owns
  versions.
- Both hosts, the whole way: every contract, rubric, and policy ships for
  Claude Code and Codex together; `agent_inventory.json` is the authoritative
  role set; the named `consensus-synthesizer` is preserved on both.
- No new authority; no second provider client; explicit egress and spend
  consent per project; exact checks stay exact; existing budgets and repair
  ownership unchanged; the disabled path is byte-identical; fixture, mocked
  transport, native observation, and live evaluation are distinct evidence
  classes.
- Identities, counts, arithmetic, paths, and permissions stay in code. Jev
  never counts, computes cost, resolves paths, or chooses a permission rule.
- Platform facts (model identifiers, configuration fields, hook behavior)
  come only from official vendor documentation or native observation, never
  from repository inference or a neighboring model; an undocumented fact fails
  closed.
- A local stdio MCP server is not local inference: state leaves the machine.
  Path exclusions and secret filtering run in code before transmission.
- Shadow evidence requires information isolation. A verdict visible to the
  live parent is advisory, not shadow.
- The typed-judgment opportunity catalog is the source of record for every Jev
  consumer, promoted or deferred.
- Public text never names the delegation runtime's host, repository, or
  internal components. It is "the delegation runtime".
- Test fixtures live under `tests/speckit-pro/` and never read a
  `specs/<feature>/` path at run time.

## 7. Open Questions

- **OQ-1 (HRNS-017):** Is the native `evaluate` result visible to the live
  parent on each host? Recommendation: assume yes until observed otherwise and
  plan retrospective shadow for the pilots.
- **OQ-2 (HRNS-017, HRNS-029):** Can a hook replace a built-in tool's output
  on each host? Recommendation: treat Codex as unsupported until observed.
- **OQ-3 (HRNS-024):** Where in `typesafe-jev` do the contract schema and
  fixtures live, and how do consumers pin a version? Recommendation: a
  versioned directory in the plugin, pinned by digest in each consumer.
- **OQ-4 (HRNS-025):** Retention and access rules for the evidence store.
  Recommendation: per-feature directory, gitignored, bounded by size, with an
  explicit unavailable marker on expiry.
- **OQ-5 (HRNS-027):** Where does per-project consent and budget
  configuration live? Recommendation: a project-level file beside the existing
  preset configuration, read-only from status mode.
- **OQ-6 (HRNS-035):** Which lifecycle events does each host expose to the
  trusted parent? Recommendation: start with the four boundaries the autopilot
  references already name.
- **OQ-7 (HRNS-038):** Source of the first labeled trajectories.
  Recommendation: this repository's own shadow runs, labeled by a maintainer.
- **OQ-8 (HRNS-018):** Should the typed record replace the one-slot
  `autopilot-state.json` mirror or sit beside it? Recommendation: decide at
  scaffold from the stage-resolution tests.

## 8. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Harness Surface Inventory and Gap Taxonomy | AC-1.* | HRNS-001 | - | P1 (complete) |
| Per-story Autopilot Execution | AC-15.* | HRNS-016 | HRNS-015 | P2 |
| Autopilot, Gate, and PR-Emission Repair | AC-16.* | HRNS-015 | - | P1 |
| Host Capability Spike | AC-17.* | HRNS-017 | - | P1 |
| Typed Workflow State | AC-18.* | HRNS-018 | - | P1 |
| Helper Registry Contract and Tiered Disclosure | AC-19.* | HRNS-019 | - | P2 |
| Autopilot Token Baseline | AC-20.* | HRNS-020 | - | P1 |
| Condition-Bound Guidance and Lesson Promotion | AC-21.* | HRNS-021 | - | P2 |
| Eval Ladder and Model Refresh | AC-22.* | HRNS-022 | - | P1 |
| Harness Drift Scanner | AC-23.* | HRNS-023 | - | P2 |
| Shared Typed-Decision Contract | AC-24.* | HRNS-024 | HRNS-017 | P1 |
| Run Journal and PR Trace Summary | AC-25.* | HRNS-025 | HRNS-019, HRNS-024 | P1 |
| Autonomous-Run Permission and Egress Policy | AC-26.* | HRNS-026 | HRNS-019 | P1 |
| Dual-Host Jev Adapter | AC-27.* | HRNS-027 | HRNS-017, HRNS-024, HRNS-025, HRNS-026 | P1 |
| Shared Retrieval Packet for Fan-Out Roles | AC-28.* | HRNS-028 | HRNS-020 | P2 |
| Visibility Ladder and Handoff Preservation | AC-29.* | HRNS-029 | HRNS-020 | P2 |
| Obligation and Subgoal Registry | AC-30.* | HRNS-030 | HRNS-018, HRNS-024 | P1 |
| Pilot: Requirement-to-Task Semantic Coverage | AC-31.* | HRNS-031 | HRNS-027 | P1 |
| Pilot: Review-Fix Closure Verification | AC-32.* | HRNS-032 | HRNS-027 | P1 |
| Pilot: Claim-to-Source Support Annotation | AC-33.* | HRNS-033 | HRNS-027 | P2 |
| Phase-Boundary Goal-Completion Verifier | AC-34.* | HRNS-034 | HRNS-025, HRNS-027, HRNS-030 | P1 |
| Change-Triggered Scheduler and Invalidation | AC-35.* | HRNS-035 | HRNS-034 | P1 |
| Premature-Stop and Redundant-Continuation Advice | AC-36.* | HRNS-036 | HRNS-035 | P1 |
| Live Run Progress Page | AC-37.* | HRNS-037 | HRNS-018 | P2 |
| Trajectory Calibration and Gated Live Evaluation | AC-38.* | HRNS-038 | HRNS-025, HRNS-031, HRNS-032, HRNS-033, HRNS-035 | P1 |

**Retired Continuous Goal Verification crosswalk**

| Former group | Former SPEC | Now |
|---|---|---|
| AC-1.* host spike | VRFY-001 | AC-17.* (HRNS-017); the Codex registration question is resolved because `typesafe-jev` ships a Codex manifest |
| AC-2.* decision contract | VRFY-002 | AC-24.* (HRNS-024) |
| AC-3.* journal and replay | VRFY-003 | AC-25.* (HRNS-025) |
| AC-4.* dual-host adapter | VRFY-004 | AC-27.* (HRNS-027) |
| AC-5.* requirement-to-task pilot | VRFY-005 | AC-31.* (HRNS-031) |
| AC-6.* review-fix pilot | VRFY-006 | AC-32.* (HRNS-032); the pagination and ordering fix to AC-16.7 |
| AC-7.* claim-support pilot | VRFY-007 | AC-33.* (HRNS-033) |
| AC-8.* obligation registry | VRFY-008 | AC-30.* (HRNS-030) |
| AC-9.* phase-boundary verifier | VRFY-009 | AC-34.* (HRNS-034) |
| AC-10.* scheduler | VRFY-010 | AC-35.* (HRNS-035) |
| AC-11.* stop advice | VRFY-011 | AC-36.* (HRNS-036) |
| AC-12.* calibration | VRFY-012 | AC-38.* (HRNS-038) |

## 9. Success Criteria

1. Every acceptance criterion in AC-15.* through AC-38.* passes, each spec
   within its reviewability budget or with a typed exception.
2. No observed autopilot, gate, or PR-emission defect remains without a
   failing-first fixture.
3. A status report can never show an archived spec's phase as in progress.
4. With semantic checks disabled, existing fixture outputs, gate results,
   status-mode writes, and workflow artifacts are byte-identical to the
   pre-integration baseline.
5. HRNS-020 shows a measured reduction in repeated reads and total tokens per
   autopilot run on both hosts, with no loss on the native evals.
6. Claude Code and Codex pass the same contract, parity, and
   synthesizer-preservation fixtures.
7. An HRNS-038 calibration report exists for at least one frozen holdout and
   is cited by any decision to promote a check beyond shadow.
8. The question in §1 is answerable from a run's terminal advisory by
   obligation id.

## 10. References

- **Technical roadmap:** `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`
- **Roadmap MOC:** `docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md`
- **Typed-judgment opportunity catalog:** `docs/ai/specs/harness-engineering-uplift-jev-catalog.md`
- **HRNS-001 gap taxonomy (2026-07-15 snapshot):** `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `REVIEW.md`, `SECURITY.md`
- **Authoritative role inventory:** `speckit-pro/speckit_pro_runner/agent_inventory.json`
- **Research broker contract:** `docs/ai/specs/research-broker-contract.md`
- **Typed-judgment plugin:** `typesafe-jev/README.md`
- **Provider documentation:** TypeSafe Jev models, limits, and confidence pages at `docs.typesafe.ai`

# Harness Engineering Uplift Gap Taxonomy

**Spec**: HRNS-001
**As of**: 2026-07-15
**Authoritative baseline**: `origin/main` at `dd761b3f00dc2daeecc153dc5eeaab4e696ceb8d`
**Feature worktree**: `.worktrees/hrns-001-harness-surface-inventory-gap-taxonomy`

This is the canonical HRNS-001 planning artifact. It inventories the current
SpecKit Pro harness surfaces, classifies retained gaps, records owner workflows,
and captures external-candidate evidence for downstream specs. It is not a
runtime registry, generated payload, validator, dependency decision, or
install-facing artifact.

## Current-state boundary

- Repository source files at the merged baseline are factual authority.
- Unmerged CAR or G56R work is reference evidence only.
- Generated payloads, installed caches, fixtures, raw transcripts, unreviewed
  chat, and derived indexes may reveal drift, but they do not override source.
- HRNS-001 does not authorize dependency adoption, runtime changes, generated
  artifact edits, or CAR/G56R implementation work.

## Harness surface inventory

| Surface ID | Surface type | Authoritative source paths | Current evidence | Notes |
|------------|--------------|----------------------------|------------------|-------|
| S-SKILL | skill | `speckit-pro/skills/`, `speckit-pro/codex-skills/` | 10 Claude skill dirs and 11 Codex skill dirs were present in the source tree. | Skill instructions are harness-control surface for SDD workflows. |
| S-COMMAND | command | `.claude/skills/`, `.specify/workflows/speckit/workflow.yml` | 29 tracked project command skill dirs were present under `origin/main:.claude/skills`. | Project commands are repository workflow surface, not plugin release payload. |
| S-AGENT | agent | `speckit-pro/agents/`, `speckit-pro/codex-agents/` | 11 Claude agents and 10 Codex agents were present. | Agent role files control delegation, consensus, review, and implementation behavior. |
| S-HELPER | helper | `speckit-pro/speckit_pro_runner/helpers/` | Helper modules include install, mutation, PR emission, promotion, read-only, and registry code. | Helper contracts are Python source authority. |
| S-RUNNER | runner | `speckit-pro/speckit_pro_runner/`, `speckit-pro/speckit_pro_runner/gates/`, `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | Runner manifest records Python 3.11+, plugin version 2.19.2, runner version 0.1.0. | Runner/gate behavior owns executable validation, mutation routing, and release-readiness checks. |
| S-GENERATED | generated payload | `speckit-pro/speckit_pro_runner/install_inventory.json`, generated docs/reference outputs, installed caches | `install_inventory.json` is a fixture-safe source checkout inventory; generated and installed copies are non-authoritative. | Use as drift evidence only. |
| S-DOCS | docs | `docs/`, `docs-site/`, `speckit-pro/README.md`, roadmap MOCs | PRD, technical roadmaps, MOCs, docs-site source, and plugin docs define reviewed intent. | Docs outside `docs-site/` are docs/process; docs-site has its own validation surface. |
| S-WORKFLOW | workflow file | `docs/ai/specs/.process/*-workflow.md`, `docs/ai/specs/.process/autopilot-state.json` | HRNS-001 workflow and state are active control records. | Workflow files are durable state for autopilot and review evidence. |
| S-PR | PR packet | `.github/pull_request_template.md`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`, PR-packet fixtures | PR descriptions are review packets by roadmap contract. | PR packet generation is review surface, not proof by itself. |
| S-TEST | test/eval | `tests/speckit-pro/`, `tests/speckit-pro/suite-manifest.json` | Suite manifest has 9 layers and 990 tracked files under `tests/speckit-pro/`. | Layer 1/4/default suite remain the validation authority for code-bearing changes. |
| S-RELEASE | release gate | `.github/workflows/`, `release-please-config.json`, `.release-please-manifest.json`, `speckit-pro/hooks/`, `speckit-pro/codex-hooks.json` | Four GitHub workflow files and release-please config are present. | Release and hook surfaces are protected by constitution and CI/release gates. |

## Evidence classes

| Evidence class | Examples | Authority rule |
|----------------|----------|----------------|
| Repository source | `speckit-pro/**`, `tests/speckit-pro/**`, `.github/**`, `docs/**`, `.specify/memory/constitution.md` | Authoritative when reviewed and in the merged baseline. |
| Agent guidance | root/nested `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | Authoritative for agent behavior within its directory scope. |
| Planning source | PRDs, technical roadmaps, MOCs, workflow/process docs, ADR-like records | Authoritative for scope and acceptance criteria when current. |
| Approved issue/PR evidence | merged PR bodies, reviewed issue decisions, accepted review packets | Authoritative only for reviewed decisions and exact cited scope. |
| External primary source | official specs, official docs, source repositories, license files, release records | Reference authority for candidate rows as of the recorded review date. |
| Generated/distribution copy | generated payloads, installed plugin caches, rendered reference pages | Non-authoritative; use only to detect drift from source. |
| Fixture/derived/runtime trace | tests fixtures, raw transcripts, local caches, derived indexes | Non-authoritative unless a reviewed spec explicitly names it as fixture evidence. |
| Unreviewed chat or machine-local state | raw chat, local memory, local worktree scratch data | Excluded as factual authority. |

## Canonical gap row schema

Each retained gap uses one stable `HRNS-GAP-###` row. IDs are zero-padded,
stable after publication, never silently renumbered, never reused after
deletion, and referenced by surfaces instead of duplicated.

Allowed field values:

- **Taxonomy type**: context, tool contract, permission, sandbox,
  memory/state, orchestration, verification, observability, HITL, security,
  garbage collection, knowledge lifecycle.
- **Lifecycle state**: implemented, planned, deferred, duplicate, obsolete,
  unknown, external-owner.
- **Dependency posture**: repo-local convention, runner/helper change,
  generated-doc/test evidence, future explicit dependency decision, deferred,
  unknown.
- **Safety closure**: human-in-the-loop, human-on-the-loop, fully automated,
  disallowed, unknown/non-promotable.

## Canonical gap register

| Gap ID | Title | Surface tags | Type | State | Authoritative evidence | Closure evidence | Owner workflow | Cross-roadmap owner | Dependency posture | Downstream owner | Safety closure | Notes as of 2026-07-15 |
|--------|-------|--------------|------|-------|------------------------|------------------|----------------|---------------------|--------------------|------------------|----------------|------------------------|
| HRNS-GAP-001 | Progressive context and durable state are not a governed contract | S-SKILL, S-AGENT, S-WORKFLOW | context, memory/state | planned | `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` HRNS-002 | unknown; closure proof deferred to HRNS-002 implementation evidence | HRNS-002 | HRNS | repo-local convention | HRNS-002 | human-on-the-loop | Downstream specs need durable state before longer orchestration can rely on restored context. |
| HRNS-GAP-002 | Helper, tool, and capability contracts are not normalized across surfaces | S-HELPER, S-RUNNER, S-SKILL, S-AGENT | tool contract | planned | Roadmap HRNS-003; runner helper inventory | unknown; closure proof deferred to HRNS-003 registry/helper evidence | HRNS-003 | HRNS | runner/helper change | HRNS-003 | human-on-the-loop | Current helpers exist, but a governed capability registry belongs in HRNS-003. |
| HRNS-GAP-003 | Permission and sandbox controls are not yet structural enough for unattended harness changes | S-RUNNER, S-HELPER, S-WORKFLOW | permission, sandbox, security | planned | Roadmap HRNS-004; constitution principle II | unknown/non-promotable until HRNS-004 proves protected-surface controls | HRNS-004 | HRNS | runner/helper change | HRNS-004 | unknown/non-promotable | Unknown or broad mutation paths remain non-promotable until HRNS-004 proves protected surfaces and approvals. |
| HRNS-GAP-004 | Feedback sensors and eval readiness are layered but not tied to every harness behavior | S-TEST, S-RUNNER, S-PR | verification, observability | planned | Roadmap HRNS-005; `tests/speckit-pro/suite-manifest.json` | existing suite layers are partial evidence; final closure deferred to HRNS-005 | HRNS-005 | HRNS | generated-doc/test evidence | HRNS-005 | human-on-the-loop | Existing layers are substantial; HRNS-005 owns mapping eval readiness to concrete helper and skill risks. |
| HRNS-GAP-005 | Trace/debug packet contract is incomplete across helpers, evals, and permissions | S-HELPER, S-RUNNER, S-PR, S-WORKFLOW | observability, verification | planned | Roadmap HRNS-006; PR-packet helper source | unknown; closure proof deferred to HRNS-006 trace/debug packet evidence | HRNS-006 | HRNS | runner/helper change | HRNS-006 | human-on-the-loop | Current outputs are command-local; HRNS-006 owns bounded replayable trace/debug packets. |
| HRNS-GAP-006 | Long-horizon orchestration lacks a standard resumable control contract | S-SKILL, S-AGENT, S-WORKFLOW | orchestration, memory/state | planned | Roadmap HRNS-007; autopilot workflow/state files | unknown/non-promotable until HRNS-007 records standard caps and continuation criteria | HRNS-007 | HRNS | repo-local convention | HRNS-007 | unknown/non-promotable | Autopilot can run long workflows, but standard continuation criteria and caps belong in HRNS-007. |
| HRNS-GAP-007 | Harness drift and garbage collection are not a final maintenance loop | S-GENERATED, S-DOCS, S-RELEASE, S-TEST | garbage collection, verification | planned | Roadmap HRNS-008; archive extension config | archive sweep is partial evidence; final closure deferred to HRNS-008 | HRNS-008 | HRNS | generated-doc/test evidence | HRNS-008 | human-on-the-loop | Archive cleanup exists; broader drift/GC across generated, indexed, imported, and knowledge artifacts is deferred. |
| HRNS-GAP-008 | Host OKF knowledge initialization is not implemented | S-DOCS, S-WORKFLOW, S-HELPER | knowledge lifecycle, context | planned | Roadmap HRNS-009; PRD AC-9.* | absent by design in HRNS-001; closure proof deferred to HRNS-009 | HRNS-009 | HRNS | future explicit dependency decision | HRNS-009 | human-in-the-loop | HRNS-001 records OKF posture only; no OKF bundle is created here. |
| HRNS-GAP-009 | Incremental evidence ingest and cited synthesis are absent | S-DOCS, S-WORKFLOW, S-HELPER | knowledge lifecycle, verification | planned | Roadmap HRNS-010 | absent by design in HRNS-001; closure proof deferred to HRNS-010 | HRNS-010 | HRNS | runner/helper change | HRNS-010 | unknown/non-promotable | Any synthesis that changes committed knowledge must remain reviewed and cited. |
| HRNS-GAP-010 | Query and answer capture are not a governed repository capability | S-DOCS, S-SKILL, S-HELPER | knowledge lifecycle, context | planned | Roadmap HRNS-011 | absent by design in HRNS-001; closure proof deferred to HRNS-011 | HRNS-011 | HRNS | runner/helper change | HRNS-011 | human-in-the-loop | Useful answers cannot be written back without a reviewed proposal path. |
| HRNS-GAP-011 | Knowledge conformance and health lint are not separated from OKF validity | S-TEST, S-DOCS, S-RUNNER | verification, knowledge lifecycle | planned | Roadmap HRNS-012; PRD AC-12.* | absent by design in HRNS-001; closure proof deferred to HRNS-012 | HRNS-012 | HRNS | generated-doc/test evidence | HRNS-012 | human-on-the-loop | Structural validity and health/hygiene findings must remain distinct. |
| HRNS-GAP-012 | Code-intelligence and derived-index interoperability are not producer-neutral contracts | S-DOCS, S-GENERATED, S-HELPER | observability, knowledge lifecycle | planned | Roadmap HRNS-013; PRD CodeGraph/GitNexus references | absent by design in HRNS-001; closure proof deferred to HRNS-013 | HRNS-013 | HRNS | future explicit dependency decision | HRNS-013 | unknown/non-promotable | Derived indexes stay disposable and cannot gain OKF write authority. |
| HRNS-GAP-013 | External OKF intake/exchange/reconciliation is not guarded | S-DOCS, S-WORKFLOW, S-HELPER, S-RELEASE | security, knowledge lifecycle | planned | Roadmap HRNS-014; PRD AC-14.* | disallowed until HRNS-014 adds bounded staging and reconciliation evidence | HRNS-014 | HRNS | runner/helper change | HRNS-014 | disallowed | External content is untrusted data until HRNS-014 adds bounded staging and reconciliation. |

## Self-improvement loop register

| Loop ID | Surface refs | Behavior | Approval boundary | Promotion rule | Evidence |
|---------|--------------|----------|-------------------|----------------|----------|
| LOOP-001 | S-SKILL, S-WORKFLOW | Autopilot creates and edits spec artifacts across phases. | human-on-the-loop | Changes promote only through committed workflow/state checkpoints and PR review. | `speckit-pro/skills/speckit-autopilot/`, `docs/ai/specs/.process/HRNS-001-workflow.md` |
| LOOP-002 | S-AGENT, S-SKILL | Clarify/checklist/analyze consensus critiques and refines specs/tasks. | human-in-the-loop where clarification is required; otherwise human-on-the-loop | Findings must be recorded and resolved before implementation gates pass. | `speckit-pro/agents/*-executor.md`, `speckit-pro/codex-agents/*-executor.toml` |
| LOOP-003 | S-GENERATED, S-RELEASE | Generated maps, reference pages, and release artifacts can be refreshed from source. | human-on-the-loop | Generated outputs cannot become factual authority; source and tests must remain the decision point. | spec-index helper results, release workflows |
| LOOP-004 | S-DOCS, S-HELPER | Future OKF synthesis may ingest evidence and propose knowledge changes. | disallowed until HRNS-009/010/014 | No automatic OKF synthesis, external intake, or write-back is allowed in HRNS-001. | Roadmap HRNS-009 through HRNS-014 |
| LOOP-005 | S-PR, S-TEST | PR packet, verify, and retrospective helpers summarize evidence and may suggest remediations. | human-on-the-loop | Summaries are review aids; they do not bypass checks, approvals, or source evidence. | `.specify/extensions.yml`, PR-packet helper source |

## External-candidate matrix

All rows are reference-only as of 2026-07-15. A recommendation here never
authorizes required dependency adoption.

| Candidate | Evidence as-of | Primary evidence | Category | Mapped HRNS surfaces | Runtime dependency posture | Local-first fit | Telemetry/privacy posture | License/supply-chain risk | Normative/reference status | Observed version or commit | Compatibility gaps | Recommendation |
|-----------|----------------|------------------|----------|----------------------|----------------------------|-----------------|---------------------------|---------------------------|----------------------------|----------------------------|--------------------|----------------|
| [Pydantic](https://docs.pydantic.dev/latest/) | 2026-07-15 | Official docs and source license evidence | schema, guardrail | HRNS-003, HRNS-004 | future explicit dependency decision | Strong Python-local validation fit; docs show v2.13.4 and JSON Schema emission. | Local library; telemetry unknown from reviewed docs. | MIT-style license evidence available in source; supply-chain review required. | library/tool | v2.13.4 docs | Would add dependency and schema semantics to runner/helper contracts. | future spike |
| [JSON Schema](https://json-schema.org/specification) | 2026-07-15 | Official specification page | schema, guardrail | HRNS-003, HRNS-004, HRNS-012 | reference-only | Strong vendor-neutral schema vocabulary. | Local validation possible; telemetry not applicable to the spec. | Specification/license posture requires review before embedding. | specification | 2020-12 current version | Draft/spec complexity and validator conformance must be checked. | reference pattern |
| [OpenTelemetry](https://opentelemetry.io/docs/) | 2026-07-15 | Official docs and specification index | trace/observability | HRNS-006, HRNS-013 | reference-only | Strong trace/metrics/log vocabulary; full SDK adoption deferred. | Can be local/exporter-dependent; export behavior must be operator-controlled. | Open-source spec ecosystem; dependency/supply-chain review required for SDKs. | specification/tooling ecosystem | Spec 1.10.0, semantic conventions 1.43.0 in docs index | GenAI semantic conventions may not match all SpecKit helper events. | reference pattern |
| [OpenInference](https://github.com/Arize-ai/openinference) | 2026-07-15 | Official source repository | trace/observability | HRNS-006, HRNS-005 | optional adapter candidate | Complements OpenTelemetry for AI traces and lists OpenAI Agents, Claude Agent SDK, DSPy, MCP, and Guardrails instrumentation. | OpenTelemetry-compatible; backend/export privacy depends on operator choice. | Apache-2.0 repository license; supply-chain review still required. | implementation/spec conventions | main branch evidence, package versions unresolved | Candidate-specific span fields need mapping to local helper trace packets. | future spike |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | 2026-07-15 | Official docs | orchestration, workflow runtime | HRNS-007, HRNS-002 | reference-only | Strong reference for durable execution, HITL, memory, and persistence. | Local OSS possible, but LangSmith integrations and platform paths need privacy review. | Open-source license evidence exists; managed platform is separate. | framework/runtime | observed docs, package version unknown | Too broad for HRNS-001; adopting runtime would be a dedicated spec. | reference pattern |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | 2026-07-15 | Official SDK docs | orchestration, guardrail, coding-agent harness | HRNS-003, HRNS-004, HRNS-006, HRNS-007 | future explicit dependency decision | Python-first primitives for agents, handoffs, guardrails, sessions, tracing, HITL, MCP, and sandbox agents. | OpenAI model/API usage and tracing need explicit operator/privacy controls. | Open-source SDK; OpenAI platform dependency requires separate review. | SDK/runtime | docs observed 2026-07-15 | API keys, hosted models, sandbox semantics, and trace exports exceed HRNS-001 scope. | future spike |
| [LangSmith](https://docs.langchain.com/langsmith/observability) | 2026-07-15 | Official docs | trace/observability, eval | HRNS-005, HRNS-006 | defer | Strong SaaS/product reference for traces, metrics, alerts, feedback, and online evals. | Account/API-key workflow and hosted observability imply external telemetry. | Product/service; license and data-retention terms need review. | product/tool | docs observed 2026-07-15 | Hosted trace storage conflicts with local-first default unless explicitly configured. | defer |
| [Langfuse](https://langfuse.com/docs) | 2026-07-15 | Official docs | trace/observability, eval | HRNS-005, HRNS-006 | optional adapter candidate | Open-source, self-hostable AI engineering platform with observability, prompt management, and evaluation. | Supports self-hosting and OpenTelemetry; cloud use requires privacy review. | Source/license review required before adapter work. | product/tool | docs observed 2026-07-15 | Platform breadth exceeds local helper trace contract. | future spike |
| [Phoenix](https://arize.com/docs/phoenix) | 2026-07-15 | Official docs | trace/observability, eval | HRNS-005, HRNS-006 | optional adapter candidate | Observability/eval platform built on OpenTelemetry and OpenInference. | Cloud/self-host choice affects telemetry; OTLP export must remain operator-controlled. | Source/license review required before adapter work. | product/tool | docs observed 2026-07-15 | Phoenix workflow is richer than HRNS-006 trace packets. | future spike |
| [Braintrust](https://www.braintrust.dev/docs) | 2026-07-15 | Official docs | eval, trace/observability | HRNS-005, HRNS-006 | defer | Strong product reference for traces, evals, experiments, human feedback, and monitoring. | Account/product workflow implies external telemetry and data retention review. | Product/service; license unknown from reviewed docs. | product/tool | docs observed 2026-07-15 | Hosted workflow conflicts with local-first default unless explicitly configured. | defer |
| [promptfoo](https://www.promptfoo.dev/docs/intro/) | 2026-07-15 | Official docs | eval, guardrail, security | HRNS-005, HRNS-004 | optional adapter candidate | CLI/library supports local evals, red teaming, assertions, CI, and broad provider integration. | Docs state local execution for evals, but provider calls and sharing need review. | Open-source; source/license review required. | CLI/library | docs last updated 2026-07-14 | Red-team/security features need scoped authorization and safe test data. | future spike |
| [Inspect AI](https://inspect.aisi.org.uk/) | 2026-07-15 | Official docs | eval, coding-agent harness, sandbox | HRNS-005, HRNS-004, HRNS-007 | reference-only | Open-source eval framework with datasets, solvers, scorers, agent evaluations, provider support, and sandbox backends. | Model provider/API key use and sandbox backend choice require controls. | Open-source; license review required before adoption. | framework | docs observed 2026-07-15 | Broad sandbox/provider matrix exceeds HRNS-001 and needs safety review. | reference pattern |
| [DSPy](https://dspy.ai/) | 2026-07-15 | Official docs | coding-agent harness, eval, optimization | HRNS-005, HRNS-007, HRNS-010 | reference-only | Python framework for typed signatures, modules, optimizers, ReAct, metrics, and program compilation. | Local framework, but model calls and optimization traces require controls. | MIT license shown in official docs; dependency review required. | framework | docs show 3.3.0b1 banner | Optimizer/self-improvement semantics are not safe to promote automatically. | reference pattern |
| [OKF v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/d44368c15e38e7c92481c5992e4f9b5b421a801d/okf/SPEC.md) | 2026-07-15 | Pinned official specification source | knowledge format | HRNS-009 through HRNS-014 | reference-only | Strong Markdown/YAML, Git-diffable knowledge-bundle fit. | Local-first by design; external exchange remains untrusted. | Pinned draft spec, not a runtime dependency. | commit `d44368c15e38e7c92481c5992e4f9b5b421a801d`, Version 0.1 Draft | Reference tooling is interoperability evidence only; stricter validators cannot redefine HRNS validity. | reference pattern |

## OKF posture

| Field | HRNS-001 position |
|-------|-------------------|
| Normative revision | OKF v0.1 `SPEC.md` pinned at commit `d44368c15e38e7c92481c5992e4f9b5b421a801d`. |
| Maturity | Draft. |
| Reference tooling | Google Cloud knowledge-catalog agents, validator, server, client, and UI are interoperability evidence only. |
| Compatibility gaps | Need full pinned-spec conformance, unknown-field preservation, relative links, append-only log interpretation, source mappings, conflict/tombstone handling, and local-first external intake controls. |
| Extension posture | Preserve unknown frontmatter fields, concept types, markdown bodies, and extensions during staging/reconciliation. |
| Disposition | Advisory/reference in HRNS-001; blocking only for later HRNS-009 through HRNS-014 acceptance criteria that explicitly adopt the OKF lane. |

## AC-1.* crosswalk

| AC | Artifact coverage | Row refs | Verification evidence |
|----|-------------------|----------|-----------------------|
| AC-1.1 | Harness surface inventory | S-SKILL through S-RELEASE | Inventory paths and counts above. |
| AC-1.2 | Canonical gap register surface tags | HRNS-GAP-001 through HRNS-GAP-014 | Every row has one or more surface tags. |
| AC-1.3 | Taxonomy type values and gap rows | HRNS-GAP-001 through HRNS-GAP-014 | Type column covers context, tool contract, permission, sandbox, memory/state, orchestration, verification, observability, HITL/security via owner rows, garbage collection, and knowledge lifecycle. |
| AC-1.4 | Lifecycle states | HRNS-GAP-001 through HRNS-GAP-014 | Rows use planned, external-owner, and disallowed/unknown safety closures where appropriate. |
| AC-1.5 | Dependency posture | HRNS-GAP-001 through HRNS-GAP-014 | Dependency posture column distinguishes repo-local, runner/helper, generated-doc/test, future dependency decision, deferred, and unknown. |
| AC-1.6 | External-candidate matrix | Pydantic through OKF rows | Matrix records category, mapped HRNS surfaces, local-first fit, runtime posture, telemetry/privacy, license/supply-chain risk, and recommendation. |
| AC-1.7 | Self-improvement loop register | LOOP-001 through LOOP-005 | Each loop has approval boundary and promotion rule. |
| AC-1.8 | Evidence classes | Evidence class table | Authoritative and excluded classes are listed explicitly. |
| AC-1.9 | Knowledge lifecycle concerns | HRNS-GAP-008 through HRNS-GAP-013 | Initialization, ingest/synthesis, query/capture, conformance, health/drift, code-intelligence interop, external exchange, provenance, conflict, and parity are represented. |
| AC-1.10 | OKF candidate and posture | OKF row, OKF posture table | Pinned revision, draft maturity, reference-tooling posture, compatibility gaps, extension preservation, and disposition are recorded. |

## Coverage proof

- Surface coverage: all required surface categories from AC-1.1 appear in the
  inventory table.
- Evidence-class coverage: every authority/exclusion class from AC-1.8 appears
  in the evidence class table.
- Duplicate-row proof: retained gaps use one `HRNS-GAP-###` row and multiple
  surface tags when a gap spans surfaces.
- CAR/G56R proof: HRNS-GAP-014 records cross-roadmap ownership without blocking
  HRNS-001 or promoting unmerged CAR/G56R state as current authority.
- Dependency proof: all external candidates are `reference-only`, `future
  explicit dependency decision`, `optional adapter candidate`, or `defer`; none
  are required runtime dependencies.
- Link/evidence proof: external candidate rows cite official docs, source
  repositories, or pinned specifications with 2026-07-15 as-of context; unknown
  fields remain `unknown` or deferred.

## Intentional deferments

| Deferred area | Owner | Reason |
|---------------|-------|--------|
| Runtime helper/capability registry | HRNS-003 | HRNS-001 is not a runtime contract spec. |
| Permission/sandbox enforcement | HRNS-004 | Requires protected-surface and authorization metadata. |
| Eval ladder and rubric calibration | HRNS-005 | Requires concrete helper and workflow risk mapping. |
| Trace/debug packet implementation | HRNS-006 | Requires helper output and replay contract changes. |
| Long-horizon orchestration controls | HRNS-007 | Requires durable state and trace foundations. |
| Drift/garbage collection loop | HRNS-008 | Runs after full knowledge lifecycle exists. |
| OKF bundle initialization and maintenance | HRNS-009 through HRNS-014 | HRNS-001 only records posture and boundaries. |
| CAR/G56R routing implementation | CAR/G56R lanes | Existing roadmap lanes own routing work; HRNS-001 only references it. |

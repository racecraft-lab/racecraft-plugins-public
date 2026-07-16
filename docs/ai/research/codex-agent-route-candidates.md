# G56R-001 Codex Agent Route Candidates

**Spec**: G56R-001 Candidate Route Baseline and Role Contracts
**Snapshot date**: 2026-07-15
**Artifact version**: `agent_route_candidate_manifest.v0.1`
**Authority rule**: Official OpenAI documentation is the only authority for
platform facts. Repository files are `project_input` only.

## Scope And Non-Goals

This report prepares the G56R-002 capability-discovery handoff. It records:

- a dated official-source ledger
- twelve role contracts
- provisional candidate routes for discovery
- current and missing fixture records
- telemetry and capability questions
- invalidation rules
- a strict go/no-go decision

This report does not create runtime behavior, live model probes, agent TOMLs,
fallback policy, installer behavior, fixture payloads, generated artifacts,
cache proofs, schema files, helper scripts, version changes, qualification
claims, preferred routes, or ordered fallbacks.

## Evidence Classes

| Class | Use in this report |
|---|---|
| `official_documentation` | Establishes model IDs, documented positioning, supported surfaces, reasoning controls, configuration fields, MCP/app surfaces, telemetry fields, lifecycle status, and source invalidation triggers. |
| `project_input` | Describes current repository files, role intent, declared TOML fields, fixture state, historical results, payload/cache references, and parity-role requirements. |
| `runtime_verification_needed` | Marks facts G56R-002 must discover from a pinned client or documented runtime surface. |
| `qualification_needed` | Marks route quality, preference, efficiency, fallback order, scorer, and fixture outcomes reserved for G56R-003 and later. |
| `undocumented` | Marks missing, conflicting, withdrawn, or unsupported platform facts that cannot admit a candidate. |

## Snapshot Metadata

| Field | Value |
|---|---|
| Retrieved at | 2026-07-15 |
| Retrieval method | Direct official page retrieval during G56R-001 implementation |
| Source allowlist | `developers.openai.com`, `learn.chatgpt.com` |
| Project input sources | PRD, technical roadmap, workflow, spec, plan, tasks, Codex TOMLs, Claude parity definitions, layer6 fixture inventory |
| Invalidation trigger | Any official source redirect, removal, lifecycle change, model list change, config key change, telemetry schema change, or runtime capability mismatch before G56R-002 consumption |

## Official Source Ledger

| `official_source_ledger_id` | Source URL requested | Canonical URL | Source family | Claim bindings | Invalidation triggers |
|---|---|---|---|---|---|
| `OSL-001` | `https://developers.openai.com/codex/models` | `https://learn.chatgpt.com/docs/models` | Codex models | Current Codex model IDs, model positioning, CLI model examples, reasoning-effort guidance, available surfaces | Model ID changes, surface changes, reasoning guidance changes, deprecation wording changes |
| `OSL-002` | `https://developers.openai.com/codex/agent-configuration/subagents` | `https://learn.chatgpt.com/docs/agent-configuration/subagents` | Codex subagents/custom agents | Custom-agent optional fields, parent inheritance, `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config` | TOML field changes, inheritance semantics change, sandbox or approval behavior changes |
| `OSL-003` | `https://learn.chatgpt.com/docs/config-file/config-reference` | same | Codex configuration | `model_reasoning_effort`, model defaults, provider settings, MCP server configuration, managed defaults | Config key names or values change, managed defaults change, MCP config behavior changes |
| `OSL-004` | `https://learn.chatgpt.com/docs/app-server` | same | Codex app server | `model/list`, `modelProvider/capabilities/read`, supported efforts, default effort, input modalities, reroute and token-usage events | JSON-RPC schema changes, telemetry field changes, reroute event changes |
| `OSL-005` | `https://learn.chatgpt.com/docs/non-interactive-mode` | same | Codex non-interactive mode | `codex exec`, JSON output, lifecycle/item events, schema output, automation boundaries | Event schema changes, auth guidance changes, sandbox behavior changes |
| `OSL-006` | `https://developers.openai.com/codex/extend/mcp` | `https://learn.chatgpt.com/docs/extend/mcp` | Codex MCP | MCP server configuration, CLI MCP commands, stdio/HTTP examples, OAuth callback settings, tool approval settings | MCP transport, auth, tool approval, or shared-config behavior changes |
| `OSL-007` | `https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt` | same | MCP Apps in ChatGPT | MCP Apps bridge, `_meta.ui.resourceUri`, `ui/*` methods, `tools/call`, ChatGPT compatibility extensions | Apps SDK compatibility or bridge behavior changes |
| `OSL-008` | `https://developers.openai.com/api/docs/guides/latest-model` | same | API model guidance | GPT-5.6 API guidance, `gpt-5.6` alias, max reasoning effort, pro mode, prompting and migration guidance | Model family guidance changes, effort values change, pro-mode guidance changes |
| `OSL-009` | `https://developers.openai.com/api/docs/deprecations` | same | API model lifecycle | Deprecated, retiring, shut down, removed, or replacement model lifecycle facts for historical seed inputs | Shutdown dates, replacement models, or lifecycle wording changes |

Official-source observations:

- OSL-001 documents `gpt-5.6`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, and `gpt-5.3-codex-spark` as current Codex-relevant entries or examples for the relevant surfaces.
- OSL-001 documents model and reasoning controls for Codex surfaces and presents higher effort as deeper but slower.
- OSL-002 documents that omitted custom-agent optional fields inherit from the parent session.
- OSL-003 documents `model_reasoning_effort` values and managed model defaults.
- OSL-004 documents `model/list`, `supportedReasoningEfforts`, `defaultReasoningEffort`, `inputModalities`, `model/rerouted`, and token-usage updates for the app-server surface.
- OSL-009 documents lifecycle replacements for historical `gpt-5.1-codex-max` and `gpt-5.2-codex` inputs.

## Project Input Inventory

| Project input | Evidence class | Use |
|---|---|---|
| `docs/prd-codex-gpt-5-6-agent-routing.md` | `project_input` | Acceptance criteria, evidence authority, G56R dependency boundaries |
| `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md` | `project_input` | Current roadmap seed set, spec dependencies, target artifact |
| `docs/ai/specs/.process/G56R-001-workflow.md` | `project_input` | Durable workflow, gates, checklist domains, task and analysis evidence |
| `specs/g56r-001-candidate-route-baseline/spec.md` | `project_input` | Requirements and record shapes |
| `specs/g56r-001-candidate-route-baseline/plan.md` | `project_input` | One-report architecture and declared file operation |
| `specs/g56r-001-candidate-route-baseline/tasks.md` | `project_input` | Implementation and verification tasks |
| `speckit-pro/codex-agents/*.toml` | `project_input` | Current active Codex role inventory and declared TOML fields |
| `speckit-pro/agents/consensus-synthesizer.md` and `speckit-pro/agents/gate-validator.md` | `project_input` | Claude parity-role contract inputs only |
| `tests/speckit-pro/layer6-efficiency/` | `project_input` | Current prompt-emulation fixture state and future fixture backlog |

Generated payloads, installed caches, historical results, and local runtime
responses are not candidate authority.

## Current Roadmap Seed Admission

| Seed model | Source bindings | G56R-001 status | Required G56R-002 question |
|---|---|---|---|
| `gpt-5.6-sol` | `OSL-001`, `OSL-008` | `admitted_for_discovery` | Does the pinned client expose it, with which supported efforts and modalities, for each role surface? |
| `gpt-5.6-terra` | `OSL-001`, `OSL-008` | `admitted_for_discovery` | Does the pinned client expose it, with which supported efforts and modalities, for each role surface? |
| `gpt-5.6-luna` | `OSL-001`, `OSL-008` | `admitted_for_discovery` | Does the pinned client expose it, with which supported efforts and modalities, for each role surface? |
| `gpt-5.5` | `OSL-001`, `OSL-004` | `admitted_for_discovery` | Is it available to the pinned client and should current TOML declarations retain it as comparator input? |
| `gpt-5.3-codex-spark` | `OSL-001`, `OSL-004` | `admitted_for_discovery_for_optional_helper_only` | Is this preview available to the pinned account and suitable only for text-only helper work? |

Unsupported admitted seed candidates: **0**.

## Historical Seed Exclusions

| Historical input | Source bindings | Status | Treatment |
|---|---|---|---|
| `gpt-5.1` | `OSL-009` | `undocumented_for_current_codex_route` | Do not admit without a current official Codex source. |
| `gpt-5.1-codex-max` | `OSL-009` | `rejected_deprecated_or_withdrawn` | Record lifecycle replacement before G56R-002; cannot admit. |
| `gpt-5.2` | `OSL-009` | `rejected_deprecated_for_codex_chatgpt_sign_in` | API-key availability, if any, is not route authority. |
| `gpt-5.2-codex` | `OSL-009` | `rejected_deprecated_or_withdrawn` | Record lifecycle replacement before G56R-002; cannot admit. |
| `gpt-5.2-codex-pro` | `OSL-008`, `OSL-009` | `rejected_undocumented` | Do not infer from GPT-5.6 pro mode or adjacent names. |

## Role Contract Records

Every effective runtime field in this section is
`runtime_verification_needed`. The declared TOML fields are project input only.

| `agent_contract_id` | Role | Source file | Production route status | Declared model | Declared effort | Declared sandbox | `instruction_sha256` | `full_file_sha256` |
|---|---|---|---|---|---|---|---|---|
| `G56R-001-AC-ANALYZE-EXECUTOR` | `analyze-executor` | `speckit-pro/codex-agents/analyze-executor.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `workspace-write` | `771a5b9075240abf72b92449dae9960a03b8873e516468a13b7c6da17245f64c` | `eac0a81678fe8b82411ab90258af41bc819681e4111547c16581e12d60afb3a4` |
| `G56R-001-AC-AUTOPILOT-FAST-HELPER` | `autopilot-fast-helper` | `speckit-pro/codex-agents/autopilot-fast-helper.toml` | `active_codex_toml` | `gpt-5.3-codex-spark` | `absent` | `read-only` | `0da3103f276542e615f2257f90514d58e3af9a61e6c59555d9c611ea7aff2b95` | `aa570f8ff51fa3cb7848d8c05253ddf5d080f5d4a2dbed9a55f0149fceb1296d` |
| `G56R-001-AC-CHECKLIST-EXECUTOR` | `checklist-executor` | `speckit-pro/codex-agents/checklist-executor.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `workspace-write` | `bb97bee3e0e52ae3885dacefb9659f9c47250508fce289aaa5daeccc59353218` | `ec29b97b8211c626e00fed1edbf0f601d3328dde57e22fb54626b5a92c2671d0` |
| `G56R-001-AC-CLARIFY-EXECUTOR` | `clarify-executor` | `speckit-pro/codex-agents/clarify-executor.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `read-only` | `c5fba94ebe76b2589e453a7f5d8acbe94cb5a804bf9235401824e8ea0fd47486` | `7853d199bcf06685239d724a289d7aeaafcf5a133e665c21bc23375220d3f490` |
| `G56R-001-AC-CODEBASE-ANALYST` | `codebase-analyst` | `speckit-pro/codex-agents/codebase-analyst.toml` | `active_codex_toml` | `gpt-5.5` | `low` | `read-only` | `256ff48441eea5f6d94e792d68d72ef9735a683292046c7e68ad5008a76b010f` | `12f41b87c1a2f2003c588d328702144d7ffcbef11f28489124751be44bb98a1e` |
| `G56R-001-AC-DOMAIN-RESEARCHER` | `domain-researcher` | `speckit-pro/codex-agents/domain-researcher.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `read-only` | `efee1fa569e635801c797711220084f86511a7ea2f6ac1e088a6a004ae624463` | `eb558933bb60f874d5bed972226100b8ff8cf5adf5c334b184ef232f0287518f` |
| `G56R-001-AC-IMPLEMENT-EXECUTOR` | `implement-executor` | `speckit-pro/codex-agents/implement-executor.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `workspace-write` | `6e2b1adca0b0ee96e8af6593d1de5a4dcb5696fd3cbcd67601b428c334ac71f8` | `7a95370adcc423203d64c1440e9f0a17af3a1a9ca2a3a6262fa6ceb8efab6148` |
| `G56R-001-AC-PHASE-EXECUTOR` | `phase-executor` | `speckit-pro/codex-agents/phase-executor.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `workspace-write` | `2ecf93717029553369f62f902f8ac95bad5f77e726dbbb8c7065d9bde36c4fe5` | `6f974a124ea4f3422f6650e4c9b501c15916ff874e2490a46cecfeedd634f7c9` |
| `G56R-001-AC-SPEC-CONTEXT-ANALYST` | `spec-context-analyst` | `speckit-pro/codex-agents/spec-context-analyst.toml` | `active_codex_toml` | `gpt-5.5` | `low` | `read-only` | `b276d4f074e07986c7e0cc75b8a52df7bdbebd7bb8ced05c3aadb615f1e7ade8` | `680e93129186f37d245ffa35dc44e064dffe24b497675aaa72b275daa7642674` |
| `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `uat-runbook-author` | `speckit-pro/codex-agents/uat-runbook-author.toml` | `active_codex_toml` | `gpt-5.5` | `xhigh` | `workspace-write` | `e78f3a5ddf51cbe26fc286780e7c711043ef0cccdd9a49d39fd0373f906b95cf` | `ea1e74b375a9fab40881d52574ec9c184033abe020e69637eac1b2248509b918` |
| `G56R-001-AC-CONSENSUS-SYNTHESIZER` | `consensus-synthesizer` | `speckit-pro/agents/consensus-synthesizer.md` | `parity_only_absent` | `absent` | `absent` | `absent` | `1d668a009a1a7ddc0ac4af9663a7f7dba367519b431af3271e212c0426cd99f2` | `548b9eeb69b6c3f8b8f5429a9ae567d456e4a4ddd1482efe1c1e947e84737327` |
| `G56R-001-AC-GATE-VALIDATOR` | `gate-validator` | `speckit-pro/agents/gate-validator.md` | `parity_only_absent` | `absent` | `absent` | `absent` | `f30cae871e3e63ac736d5cd8695dfa42a73ded50807f46709139c663d91c070e` | `ecfa70143aa02c943474f23d38cd5c0b01ca1fabae7d2a899c45d35eb7bb5f0d` |

Role contract fields common to all active Codex roles:

- `source_class`: `project_input`
- `hash_source`: role source file as listed above
- `source_config_bindings`: declared TOML fields plus loaded workflow prompt
- `effective_runtime_permissions`: `runtime_verification_needed`
- `effective_parent_overrides`: `runtime_verification_needed`
- `effective_sandbox_and_approval_policy`: `runtime_verification_needed`
- `exact_treatment_boundary`: G56R-002/G56R-003 must prove effective model,
  effort, sandbox, approvals, tools, skills, MCP, instructions, parent config,
  and telemetry before qualification.

## Role Boundary And Contract Matrix

| `agent_contract_id` | Role boundary | Mutation contract | Tool/skill/MCP contract | Output contract | Representative future task |
|---|---|---|---|---|---|
| `G56R-001-AC-ANALYZE-EXECUTOR` | Run Analyze and remediate findings | May edit specs/plans/tasks/code for scoped findings | Needs project files, docs, helper gates; MCP only when provided by parent | Analyze result with findings, fixes, verification | Resolve G56R analysis drift before implementation |
| `G56R-001-AC-AUTOPILOT-FAST-HELPER` | Compress, triage, draft queries, normalize context | Read-only advisory | No tools, skills, MCP, or filesystem dependency by contract | Short advisory output | Summarize an executor result for parent orchestration |
| `G56R-001-AC-CHECKLIST-EXECUTOR` | Run one checklist domain and close true requirement gaps | May edit spec/plan/checklist artifacts | Checklist skill, project files, docs, helper gates | Checklist domain result with gaps and fixes | Close evidence-integrity gaps |
| `G56R-001-AC-CLARIFY-EXECUTOR` | Prepare bounded clarify questions with recommendations | Read-only | Project docs, official docs, local reads | Clarify question set with evidence | Prepare ambiguity questions for a new spec |
| `G56R-001-AC-CODEBASE-ANALYST` | Answer from existing code patterns only | Read-only | Code search and file reads | Answer, evidence, confidence | Resolve implementation-precedent questions |
| `G56R-001-AC-DOMAIN-RESEARCHER` | Answer from official docs and standards | Read-only | Official docs/web research; no project mutation | Answer, citations, confidence | Verify current OpenAI model/config docs |
| `G56R-001-AC-IMPLEMENT-EXECUTOR` | Execute one implementation task with TDD discipline | Workspace-write for scoped task | Project commands, tests, patches, optional official docs | Task result with TDD and verification | Implement one G56R resolver task |
| `G56R-001-AC-PHASE-EXECUTOR` | Run one Specify, Plan, or Tasks phase | Workspace-write for phase artifacts | Loaded phase skill and command-owned scripts/templates | Phase result with files and metrics | Run G56R-002 plan phase |
| `G56R-001-AC-SPEC-CONTEXT-ANALYST` | Answer from constitution, roadmap, specs, decisions | Read-only | Project docs and local reads | Answer, references, confidence | Resolve cross-spec consistency question |
| `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | Rewrite generated UAT skeleton in place | Workspace-write to skeleton only | Generated skeleton, spec, plan, quickstart | Rewrite summary and removed placeholders | Produce final UAT runbook |
| `G56R-001-AC-CONSENSUS-SYNTHESIZER` | Synthesize analyst outputs and exact edit instructions | Parity-only project input; no active Codex route | Future Codex parity contract needed | Consensus result with agreement, edits, flags | Define future Codex consensus role |
| `G56R-001-AC-GATE-VALIDATOR` | Run supplied gate command and preserve JSON evidence | Parity-only project input; no active Codex route | Future Codex parity contract needed | Gate result with verbatim JSON | Define future Codex gate-validation role |

## Provisional Candidate Routes

Candidate routes are admitted only for G56R-002 discovery. They are not
available, executable, qualified, preferred, efficient, fallback-ordered, or
installed.

| `candidate_route_id` | `agent_contract_id` | Model | Effort | Source bindings | Status | Unsupported facts |
|---|---|---|---|---|---|---|
| `G56R-001-CR-ANALYZE-EXECUTOR-SOL` | `G56R-001-AC-ANALYZE-EXECUTOR` | `gpt-5.6-sol` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-SPARK` | `G56R-001-AC-AUTOPILOT-FAST-HELPER` | `gpt-5.3-codex-spark` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-004` | `admitted_for_discovery_for_optional_helper_only` | account availability, text-only constraint, exact effort, qualification |
| `G56R-001-CR-CHECKLIST-EXECUTOR-SOL` | `G56R-001-AC-CHECKLIST-EXECUTOR` | `gpt-5.6-sol` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-CLARIFY-EXECUTOR-SOL` | `G56R-001-AC-CLARIFY-EXECUTOR` | `gpt-5.6-sol` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-CODEBASE-ANALYST-TERRA` | `G56R-001-AC-CODEBASE-ANALYST` | `gpt-5.6-terra` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-DOMAIN-RESEARCHER-SOL` | `G56R-001-AC-DOMAIN-RESEARCHER` | `gpt-5.6-sol` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-SOL` | `G56R-001-AC-IMPLEMENT-EXECUTOR` | `gpt-5.6-sol` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-PHASE-EXECUTOR-SOL` | `G56R-001-AC-PHASE-EXECUTOR` | `gpt-5.6-sol` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-TERRA` | `G56R-001-AC-SPEC-CONTEXT-ANALYST` | `gpt-5.6-terra` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-TERRA` | `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `gpt-5.6-terra` | `runtime_supported_effort_required` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `admitted_for_discovery` | runtime availability, exact effort, exact treatment, qualification |
| `G56R-001-CR-CONSENSUS-SYNTHESIZER-PARITY` | `G56R-001-AC-CONSENSUS-SYNTHESIZER` | `none` | `none` | `project_input` only | `project_input_only` | active Codex TOML absent, future parity TOML needed |
| `G56R-001-CR-GATE-VALIDATOR-PARITY` | `G56R-001-AC-GATE-VALIDATOR` | `none` | `none` | `project_input` only | `project_input_only` | active Codex TOML absent, future parity TOML needed |

Effort surface rules:

- Codex model guidance, custom-agent TOML, config TOML, app-server catalog, and
  API model guidance are separate evidence surfaces.
- Default effort from one surface does not establish another surface's default
  unless the official source states that relationship.
- Every admitted route requires G56R-002 to discover
  `supportedReasoningEfforts`, `defaultReasoningEffort`, and effective effort
  for the pinned client before use.

## Fixture Backlog Records

| `fixture_backlog_id` | Role | Current status | Source path | Executable specification | Telemetry requirements | Success oracle | Blocking dependency | Priority |
|---|---|---|---|---|---|---|---|---|
| `G56R-001-FB-CODEBASE-ANALYST` | `codebase-analyst` | `current_prompt_emulation_codex` | `tests/speckit-pro/layer6-efficiency/fixtures-codex/codebase-analyst/` | Re-execute as materialized read-only custom agent against codebase evidence fixture | route, effective route, file reads/searches, tokens, duration | Cites file evidence and stays in codebase lane | G56R-002 telemetry, G56R-003 materializer | P1 |
| `G56R-001-FB-DOMAIN-RESEARCHER` | `domain-researcher` | `current_prompt_emulation_codex` | `tests/speckit-pro/layer6-efficiency/fixtures-codex/domain-researcher/` | Re-execute with official-doc access and citation capture | route, effective route, source access events, tokens, duration | Provides official citations without codebase claims | G56R-002 tool/MCP telemetry | P1 |
| `G56R-001-FB-SPEC-CONTEXT-ANALYST` | `spec-context-analyst` | `current_prompt_emulation_codex` | `tests/speckit-pro/layer6-efficiency/fixtures-codex/spec-context-analyst/` | Re-execute with project docs and no writes | route, effective route, file reads, tokens, duration | Cites constitution, roadmap, and spec sections | G56R-003 exact treatment | P1 |
| `G56R-001-FB-ANALYZE-EXECUTOR` | `analyze-executor` | `missing_executable_fixture` | none | Run synthetic Analyze findings through command, remediation, marker recount | command events, file changes, marker counts, retries, tokens | Findings remediated or tagged after bounded loops | G56R-003 safe fixture repo | P1 |
| `G56R-001-FB-AUTOPILOT-FAST-HELPER` | `autopilot-fast-helper` | `missing_executable_fixture` | none | Invoke compression, triage, query draft, context normalization cases | route, latency, output tokens, no tool use | Advisory output, no decisions or mutation | G56R-010 helper campaign | P2 |
| `G56R-001-FB-CHECKLIST-EXECUTOR` | `checklist-executor` | `missing_executable_fixture` | none | Run one checklist domain with seeded requirement gaps | checklist output, file changes, marker counts, tokens | True gaps closed or tagged after bounded loops | G56R-003 checklist fixture | P1 |
| `G56R-001-FB-CLARIFY-EXECUTOR` | `clarify-executor` | `missing_executable_fixture` | none | Provide spec ambiguity and require bounded question set without edits | file reads, route, marker count, tokens | Up to five evidence-backed questions, no interactive invocation | G56R-002 telemetry | P1 |
| `G56R-001-FB-IMPLEMENT-EXECUTOR` | `implement-executor` | `missing_executable_fixture` | none | Assign small TDD task with known red/green behavior in fixture repo | test commands, file changes, route, tokens | Real failing test then passing scoped edit | G56R-003 executable harness | P1 |
| `G56R-001-FB-PHASE-EXECUTOR` | `phase-executor` | `missing_executable_fixture` | none | Run fake Specify/Plan/Tasks command fixture | created files, markers, phase metrics, route | Only command instructions followed | G56R-003 command fixture | P1 |
| `G56R-001-FB-UAT-RUNBOOK-AUTHOR` | `uat-runbook-author` | `missing_executable_fixture` | none | Rewrite generated UAT skeleton with known placeholders | file change evidence, route, tokens | Plain-English steps and FR matrix; fail-open preserved | G56R-003 skeleton fixture | P2 |
| `G56R-001-FB-CONSENSUS-SYNTHESIZER` | `consensus-synthesizer` | `missing_executable_fixture` | `tests/speckit-pro/layer6-efficiency/fixtures/consensus-synthesizer/` as `project_input` | Replay 1-, 2-, 3-analyst consensus cases | route, analyst hashes, output hash, tokens | Correct agreement, flags, exact edit behavior | G56R-009 parity TOML | P1 |
| `G56R-001-FB-GATE-VALIDATOR` | `gate-validator` | `missing_executable_fixture` | `tests/speckit-pro/layer6-efficiency/fixtures/gate-validator/` as `project_input` | Execute supplied gate command returning JSON | command exit, JSON output, route, duration | Verbatim JSON preserved, no remediation | G56R-009 parity TOML | P1 |

All fixture backlog records have `non_release_evidence=true` when current
prompt-emulation evidence exists and `no_payload_created_in_g56r_001=true`.

Fixture counts:

- Current Codex prompt-emulation fixtures: **3**
- Missing executable fixtures: **9**
- Current Claude prompt-emulation records counted as Codex executable fixtures:
  **0**

## G56R-002 Capability And Telemetry Questions

G56R-002 must answer these before any candidate can become executable:

1. Which admitted candidates appear in `model/list` for the pinned client, with
   `includeHidden` policy declared?
2. Which entries expose `supportedReasoningEfforts`,
   `defaultReasoningEffort`, and `inputModalities`?
3. Which provider capabilities are returned by
   `modelProvider/capabilities/read` for each candidate?
4. Which surface proves requested model, requested effort, effective model,
   effective effort, service reroute when documented, token usage, duration,
   retries, and parent/child attribution?
5. Which telemetry fields are native, derived, conditional, or unavailable?
6. Which evidence separates declared TOML fields from effective runtime
   sandbox, approvals, parent overrides, tools, skills, and MCP?
7. Which exact-treatment evidence proves a materialized custom-agent route
   matched intended model, effort, instructions, sandbox, skills, MCP, tools,
   and parent config?
8. Which MCP/app/tool surfaces are available to each role under the pinned
   client?
9. Which historical or undocumented candidates remain rejected before probing?
10. Which source, capability, telemetry, fixture, scorer, or instruction-hash
    invalidation trigger requires rediscovery before proceeding?

## Traceability Matrix

| Requirement | Report coverage | Evidence class |
|---|---|---|
| FR-001 | This report path | `project_input` |
| FR-002 | Scope and non-goals; changed-file scope guard | `project_input` |
| FR-003 | Official Source Ledger | `official_documentation` |
| FR-004 | Evidence Classes and Source Ledger | `official_documentation` |
| FR-005 | Project Input Inventory | `project_input` |
| FR-006 | Historical Seed Exclusions and Candidate Routes | `official_documentation`, `undocumented` |
| FR-007 | Role Contract Records count | `project_input` |
| FR-008 | Role Boundary and Contract Matrix | `project_input`, `runtime_verification_needed` |
| FR-009 | Parity-only role records | `project_input` |
| FR-010 | Current Roadmap Seed Admission | `official_documentation` |
| FR-011 | Provisional Candidate Routes | `official_documentation`, `runtime_verification_needed` |
| FR-012 | Candidate no-claims boundary | `qualification_needed` |
| FR-013 | Fixture Backlog Records count | `project_input` |
| FR-014 | Fixture Backlog Records fields | `project_input`, `runtime_verification_needed` |
| FR-015 | Fixture non-release evidence label | `project_input` |
| FR-016 | G56R-002 capability and telemetry questions | `runtime_verification_needed` |
| FR-017 | Traceability Matrix | all classes |
| FR-018 | Go/No-Go Decision | all classes |
| SC-001 | Source, role, fixture, and unsupported admitted seed counts | all classes |
| SC-002 | Source bindings and unsupported candidates | `official_documentation`, `undocumented` |
| SC-003 | Role contract fields and effective-runtime fields | `project_input`, `runtime_verification_needed` |
| SC-004 | Fixture backlog count and labels | `project_input` |
| SC-005 | Final decision matrix | all classes |
| SC-006 | Marker search is part of implementation verification | `project_input` |

## Completeness Matrix

| Record family | Required | Actual | Status |
|---|---:|---:|---|
| `OfficialSourceLedgerRecord` | 9 | 9 | complete |
| `AgentContractRecord` | 12 | 12 | complete |
| `FixtureBacklogRecord` | 12 | 12 | complete |
| Current Codex prompt-emulation fixtures | 3 | 3 | complete |
| Missing executable fixtures | 9 | 9 | complete |
| Unsupported admitted seed candidates | 0 | 0 | complete |
| Runtime route qualification evidence | 0 in G56R-001 | 0 | deferred |
| Installer or fallback policy changes | 0 in G56R-001 | 0 | out of scope |

## Invalidation Rules

Refresh this report before G56R-002 if any of these changes occur:

- any official source URL redirects to materially different content
- a model ID, lifecycle state, default effort, supported effort, input modality,
  model-list schema, capability schema, reroute event, or token-usage event
  changes
- a role source file or instruction hash changes
- an agent TOML adds or removes model, effort, sandbox, tool, skill, or MCP
  declarations
- fixture inputs, success oracles, scorer rules, or telemetry requirements
  change
- G56R-002 discovers a capability snapshot that conflicts with this report

## Verification Evidence

Pre-implementation workflow gates passed through G6.5. Implementation
verification completed with these results:

| Check | Result |
|---|---|
| Unresolved-marker search across the feature directory, workflow state, and this report | Pass; no live marker hits |
| Exact count review | Pass; 9 official source records, 12 role contracts, 12 candidate routes, 12 fixture records, 3 current fixtures, 9 missing fixtures |
| Unsupported admitted seed candidates | Pass; 0 |
| Changed-file scope review | Pass; one new report plus workflow state updates, with no runtime, agent, installer, payload, cache, fixture payload, generated artifact, schema, helper script, or version change |
| `git diff --check` | Pass |
| `python3 tests/speckit-pro/run-all.py --layer 1` | Pass; 1428/1428 |
| `python3 tests/speckit-pro/run-all.py` | Pass; 2768/2768 |

The full suite initially exposed privacy-scan hits in workflow state for raw
local path and agent-run identifiers. The state was redacted to symbolic labels
and the suite was rerun to a clean pass.

## PR Review Packet Source

What changed: one canonical report records the official-source ledger, twelve
role contracts, provisional candidate routes, fixture backlog, telemetry and
capability questions, invalidation rules, and strict G56R-002 go/no-go decision.

Why it changed: G56R-002 needs a source-bound, official-documentation-only
baseline before runtime capability discovery or exact-treatment work can start.

Non-goals: no runtime route resolver, no agent TOML changes, no installer or
payload changes, no live probes, no qualification, no preferred route, and no
fallback policy.

Recommended review order:

1. Official Source Ledger and seed admission.
2. Role Contract Records and role boundary matrix.
3. Provisional Candidate Routes.
4. Fixture Backlog Records and G56R-002 questions.
5. Completeness, invalidation, verification, and go/no-go sections.

Rollback note: revert this report and the G56R-001 workflow-state updates. No
runtime behavior is changed.

## Go/No-Go Decision

| Decision area | Decision | Reason |
|---|---|---|
| Proceed to G56R-002 capability discovery and telemetry profiling | `GO` | Source ledger, role contracts, candidate records, fixture backlog, telemetry questions, capability questions, invalidation rules, and strict authority classes are complete. |
| Proceed to executable candidate set | `NO-GO` | Runtime capability snapshot and telemetry profile are not G56R-001 evidence. |
| Proceed to route qualification | `NO-GO` | Exact treatment, fixtures, scorer, analysis plan, and executable corpus belong to G56R-003 and later. |
| Proceed to installer behavior, resolver behavior, preferred route, or fallback policy | `NO-GO` | Qualified preferred and fallback routes do not exist in G56R-001. |

Final G56R-001 decision: `GO` for G56R-002 capability discovery only; `NO-GO`
for route qualification, installation, resolver behavior, preferred routes, and
fallback policy.

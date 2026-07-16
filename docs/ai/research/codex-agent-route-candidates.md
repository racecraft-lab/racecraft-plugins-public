# G56R-001 Codex Agent Route Candidates

**Spec**: G56R-001 Candidate Route Baseline and Role Contracts
**Snapshot date**: 2026-07-16
**Original report artifact version**: `agent_route_candidate_manifest.v0.1`
**Current machine schema**: `2.0.0`
**Authority rule**: Official OpenAI documentation is the only authority for
platform facts. Repository files are `project_input` only.

## Current v2 Evidence-Parity Amendment

**Current snapshot:** `G56R-001-SNAPSHOT-2026-07-16-V2`
**Machine manifest:**
[`codex-agent-route-candidate-manifest.json`](codex-agent-route-candidate-manifest.json)
**Shared schema:**
[`agent-route-candidate-manifest.schema.json`](agent-route-candidate-manifest.schema.json)
**Shared contract:**
[`agent-routing-parity-contract.md`](../specs/agent-routing-parity-contract.md)
**Immutable comparator:** `speckit-pro-v2.19.2` at
`587057efeff856bad020b38dc11c7e9214f2c078`

This amendment is the current G56R-001 authority for downstream consumers. It
adds the same schema-v2 evidence structure used by CAR-001 while preserving the
original report-only handoff below and at commit
`fe9d7cda2ae96247391b62cd43c8897262245f97`.

Platform claims are admitted only from canonical OpenAI documentation under
`learn.chatgpt.com/docs/**`, `developers.openai.com/codex/**`,
`developers.openai.com/api/docs/**`, or `platform.openai.com/docs/**`.
Repository state, live discovery, probes, and evaluations retain their separate
project, runtime-verification, and qualification roles; none can create an
undocumented platform fact or candidate.

### Current Official-Source Ledger

| Source ID | Matrix family | Canonical official document | Retrieved at UTC | Body SHA-256 |
|---|---|---|---|---|
| `OPENAI-DOC-001` | `documentation_discovery` | `https://learn.chatgpt.com/docs/codex-manual.md` | `2026-07-16T14:03:32Z` | `084f81886e62bd0d8eafdc9cbc0b297f026880dbd212bf55796759fe9115ccc9` |
| `OPENAI-DOC-002` | `model_catalog` | `https://learn.chatgpt.com/docs/models` | `2026-07-16T14:03:33Z` | `01dfd5f6e7d67308cf2d2897256d3b1442b1cef8a1db165e6989c520dd073e1e` |
| `OPENAI-DOC-003` | `subagent_configuration` | `https://learn.chatgpt.com/docs/agent-configuration/subagents` | `2026-07-16T14:03:33Z` | `18fda902a30f9563e20645ed0549193ef4bc15b330e7bd6e3e0397b23055714c` |
| `OPENAI-DOC-004` | `model_configuration_and_resolution` | `https://learn.chatgpt.com/docs/config-file/config-reference` | `2026-07-16T14:03:33Z` | `483eb6d8baa3ceee65d2196ba41cecad1ee6be87bdf37b7886d3e60b39c426d2` |
| `OPENAI-DOC-005` | `hooks_and_effective_route` | `https://learn.chatgpt.com/docs/hooks` | `2026-07-16T14:03:34Z` | `be2be47332edbc2de3170da674f838ffcf9cd5d0e777c93240bb344b91129f84` |
| `OPENAI-DOC-006` | `telemetry_and_observability` | `https://learn.chatgpt.com/docs/app-server` | `2026-07-16T14:03:34Z` | `0aeafcfd075e3aa463341fe08e0a5a29f4b8c8d17778423d4b5c45941181a373` |
| `OPENAI-DOC-007` | `noninteractive_output` | `https://learn.chatgpt.com/docs/non-interactive-mode` | `2026-07-16T14:03:35Z` | `e5f9d89f239bdbb4e15d2c4eac317f66a12cf79a6a168ba0245e509ce433b69c` |
| `OPENAI-DOC-008` | `tools_and_mcp` | `https://learn.chatgpt.com/docs/extend/mcp` | `2026-07-16T14:03:35Z` | `80963d1ff2ed16f9739527a3bc64a0918fde9b5c053b5d0f6d0009a07e37aae7` |
| `OPENAI-DOC-009` | `authentication` | `https://learn.chatgpt.com/docs/auth` | `2026-07-16T14:03:35Z` | `0ff352b1ad2b2085db5d7b78b699c4081024c7607b4933886f220e3b17ed78bd` |
| `OPENAI-DOC-010` | `permissions_and_sandboxing` | `https://learn.chatgpt.com/docs/agent-approvals-security` | `2026-07-16T14:03:35Z` | `ad62dbe0c921a25849b901d1bac79e7ec49af4ba1b255c6beffe8f13ea37cdce` |
| `OPENAI-DOC-011` | `model_pricing` | `https://learn.chatgpt.com/docs/pricing` | `2026-07-16T14:03:36Z` | `b1fe88e5d02fe30974742f59ec546f4bc08dd61742b254fe3eeafd9a1a0f324e` |
| `OPENAI-DOC-012` | `administrative_analytics` | `https://learn.chatgpt.com/docs/enterprise/analytics-api` | `2026-07-16T14:03:36Z` | `ac53417415d816c67161b364de04e1c13534181ed76918425d41ee6316c7e151` |
| `OPENAI-DOC-013` | `model_lifecycle` | `https://developers.openai.com/api/docs/deprecations` | `2026-07-16T14:03:36Z` | `c9afecea6c0d8e9e4cb93abe7823a9348fb13d7a6f6f6f66960bcfd3dbf18dd4` |
| `OPENAI-DOC-014` | `effort_controls` | `https://developers.openai.com/api/docs/guides/latest-model` | `2026-07-16T14:03:37Z` | `214b2e623fe154d5908ff433a1ea6d3987a08098e114842045b5c99ec1141b1a` |
| `OPENAI-DOC-015` | `skills_and_delegation` | `https://learn.chatgpt.com/docs/build-skills` | `2026-07-16T14:03:37Z` | `fb2b03951f078fb5fac8c8528ef51e2c3ae12db9377cbd8c499a2a9839585642` |
| `OPENAI-DOC-016` | `plugin_agent_contract` | `https://learn.chatgpt.com/docs/agent-configuration/agents-md` | `2026-07-16T14:03:37Z` | `c5c7ce87abe8f4dfec2119676510fb28581e5c200739ef6b9f83c3c0ad11e86e` |
| `OPENAI-DOC-017` | `feature_and_provider_availability` | `https://learn.chatgpt.com/docs/enterprise/workspace-model-availability` | `2026-07-16T14:03:38Z` | `32f1c2576adaf8aa3d804bd2a97d788d204d931a1fd30dfb0dc2eb8afd9c5d3a` |
| `OPENAI-DOC-018` | `interactive_commands` | `https://learn.chatgpt.com/docs/developer-commands?surface=cli` | `2026-07-16T14:03:38Z` | `6612502c70407b9555c964273fd63450ef63664d13e8e4c480367724a679d0f1` |
| `OPENAI-DOC-019` | `fast_mode` | `https://learn.chatgpt.com/docs/agent-configuration/speed` | `2026-07-16T14:03:38Z` | `8604ea2a184d474f7193c650792a585598585090e474853a27877a987c95ba70` |
| `OPENAI-DOC-020` | `cost_management` | `https://learn.chatgpt.com/docs/enterprise/usage-limits` | `2026-07-16T14:03:38Z` | `b777217b0483d1693cff70d93fee88ccd50dca1892d228add7d7de14e6f32ccf` |
| `OPENAI-DOC-021` | `statusline_diagnostics` | `https://learn.chatgpt.com/docs/developer-commands?surface=cli#configure-footer-items-with-statusline` | `2026-07-16T14:03:39Z` | `6612502c70407b9555c964273fd63450ef63664d13e8e4c480367724a679d0f1` |

Each machine record also contains the requested URL, HTTP status, byte count,
bounded normalized extract and hash, supported surfaces, exact facts, claim
bindings, gaps, conflict/access status, and invalidation triggers.

### Parity And Historical Disposition

| Contract item | Current result |
|---|---|
| Shared schema | `2.0.0`; exact top-level and record-level parity with CAR-001 |
| Source matrix | 21 of 21 shared families represented by current OpenAI documentation |
| Agent contracts | 12 of 12 shared names, including two recorded Codex absences |
| Candidate routes | 23 source-bound, provisional, and non-executable records |
| Fixture backlog | 12 records, exactly one per shared agent |
| Telemetry and questions | 15 telemetry requirements and 10 open capability questions |
| Original source facts | 23 `confirmed_current`; 2 Apps SDK facts preserved but withdrawn as Codex route authority |
| Runtime behavior | unchanged; no route is executable, preferred, qualified, or installed |

The original design Q3 selected a single report and rejected a JSON artifact.
The approved cross-platform parity plan supersedes only that packaging decision:
the report remains canonical human evidence and the new manifest supplies the
shared machine contract. The original source rows, extracts, hashes, decisions,
and verification narrative below remain historical evidence and are not
silently rewritten.

**Consumption gate:** G56R-002 remains blocked until PR #362 and this v2
amendment merge, the manifest passes deterministic parity validation, and all
official sources are revalidated for the consuming scaffold.

> Historical boundary: The remaining sections preserve the original
> report-only G56R-001 handoff. Its `OSL-*` identifiers and nine-source counts
> describe that snapshot; downstream work must consume the `OPENAI-DOC-*`
> schema-v2 ledger above.

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
| `official_documentation` | Establishes model IDs, documented positioning, supported surfaces, reasoning controls, configuration fields, MCP/app surfaces, telemetry fields, documented lifecycle status when present, and source invalidation triggers. |
| `project_input` | Describes current repository files, role intent, declared TOML fields, fixture state, historical results, payload/cache references, and parity-role requirements. |
| `runtime_verification_needed` | Marks facts G56R-002 must discover from a pinned client or documented runtime surface. |
| `qualification_needed` | Marks route quality, preference, efficiency, fallback order, scorer, and fixture outcomes reserved for G56R-003 and later. |
| `undocumented` | Marks missing, conflicting, withdrawn, or unsupported platform facts that cannot admit a candidate. |

## Snapshot Metadata

| Field | Value |
|---|---|
| Retrieved at | 2026-07-16 |
| Retrieval method | Direct official page retrieval during G56R-001 implementation |
| Source allowlist | `developers.openai.com`, `learn.chatgpt.com` |
| Project input sources | PRD, technical roadmap, workflow, spec, plan, tasks, Codex TOMLs, route-policy skill/runner surfaces, generated payload/cache references, Claude parity definitions, layer6 fixture inventory |
| Invalidation trigger | Any official source redirect, removal, lifecycle change, model list change, config key change, telemetry schema change, or runtime capability mismatch before G56R-002 consumption |

## Official Source Ledger

| `official_source_ledger_id` | Source family | Retrieval method | Requested URL | Canonical URL | Retrieved at UTC | Page or surface | Supported surfaces | Exact documented facts used | Claim bindings | Conflict/access status | Invalidation triggers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `OSL-001` | Codex model guidance | Direct official page retrieval; redirect recorded | `https://developers.openai.com/codex/models` | `https://learn.chatgpt.com/docs/models` | `2026-07-16T03:27:12Z` | Codex models and reasoning controls | Codex CLI, Codex app, custom-agent model examples | Model IDs and model-positioning entries listed in this snapshot; Codex reasoning guidance; no account availability, supported effort set, or default effort is inferred | Seed admission, candidate model IDs, effort-source scoping | Accessible; no unresolved conflict recorded in snapshot | Model ID changes, surface changes, reasoning guidance changes, deprecation wording changes |
| `OSL-002` | Codex custom-agent configuration | Direct official page retrieval; redirect recorded | `https://developers.openai.com/codex/agent-configuration/subagents` | `https://learn.chatgpt.com/docs/agent-configuration/subagents` | `2026-07-16T03:27:12Z` | Codex subagents/custom agents | Codex custom-agent TOML | Optional custom-agent fields and parent inheritance for `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config`; no effective runtime field is inferred | Role contracts, effort-surface records, exact-treatment questions | Accessible; redirect normalized to canonical URL | TOML field changes, inheritance semantics change, sandbox or approval behavior changes |
| `OSL-003` | Codex config reference | Direct official page retrieval | `https://learn.chatgpt.com/docs/config-file/config-reference` | same | `2026-07-16T03:27:12Z` | Codex config reference | Codex config TOML | `model_reasoning_effort` config key and managed model-default scope; no provider, MCP, or custom-agent effective default is inferred | Effort-surface records, parent/default caveats | Accessible; no unresolved conflict recorded in snapshot | Config key names or values change, managed defaults change, MCP config behavior changes |
| `OSL-004` | Codex app-server JSON-RPC | Direct official page retrieval | `https://learn.chatgpt.com/docs/app-server` | same | `2026-07-16T03:27:12Z` | Codex app-server JSON-RPC | Codex app server | `model/list`, `modelProvider/capabilities/read`, model-catalog effort and modality fields, `model/rerouted`, and token-usage signals; no pinned-client result is captured | G56R-002 capability and telemetry questions | Accessible; runtime availability remains unverified | JSON-RPC schema changes, telemetry field changes, reroute event changes |
| `OSL-005` | Codex non-interactive mode | Direct official page retrieval | `https://learn.chatgpt.com/docs/non-interactive-mode` | same | `2026-07-16T03:27:12Z` | Codex non-interactive mode | `codex exec` | JSON lifecycle/item/error events and schema output; no custom-agent effective-route or token-usage field is captured | Non-interactive telemetry caveats and verification boundary | Accessible; exact effective-route fields not documented by this source | Event schema changes, auth guidance changes, sandbox behavior changes |
| `OSL-006` | Codex MCP extension | Direct official page retrieval; redirect recorded | `https://developers.openai.com/codex/extend/mcp` | `https://learn.chatgpt.com/docs/extend/mcp` | `2026-07-16T03:27:12Z` | Codex MCP extension | Codex MCP | MCP CLI commands, stdio/HTTP server setup, and plugin-bundled MCP server support; no OAuth callback, tool approval, or role-specific tool access is inferred | MCP contract and tool-access questions | Accessible; redirect normalized to canonical URL | MCP transport, auth, tool approval, or shared-config behavior changes |
| `OSL-007` | Apps SDK MCP apps | Direct official page retrieval | `https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt` | same | `2026-07-16T03:27:12Z` | Apps SDK MCP apps in ChatGPT | ChatGPT hosted MCP app surface | MCP Apps iframe bridge and `tools/call` tool-surface boundary; source is not Codex custom-agent authority | ChatGPT app-surface boundary and exclusion notes | Accessible; surface is not a Codex custom-agent runtime proof | Apps SDK compatibility or bridge behavior changes |
| `OSL-008` | OpenAI latest-model API guidance | Direct official page retrieval | `https://developers.openai.com/api/docs/guides/latest-model` | same | `2026-07-16T03:27:12Z` | Latest-model API guidance | OpenAI API | Latest-model family guidance, API-specific effort guidance, pro-mode guidance, prompting guidance, and migration guidance; no Codex custom-agent availability or default is inferred | Candidate family context and effort caveats | Accessible; API guidance cannot by itself prove Codex pinned-client availability | Model family guidance changes, effort values change, pro-mode guidance changes |
| `OSL-009` | OpenAI API deprecations | Direct official page retrieval | `https://developers.openai.com/api/docs/deprecations` | same | `2026-07-16T03:27:12Z` | API model deprecations | OpenAI API lifecycle | API lifecycle taxonomy and any source-documented deprecation or removal entries captured at retrieval time; no uncaptured shutdown date or replacement model is inferred | Lifecycle taxonomy and future refresh checks; no exact historical seed lifecycle facts are bound in this report | Accessible; exact historical seed lifecycle fields are not recorded in this snapshot | Shutdown dates, replacement models, or lifecycle wording changes |

### Official Source Retrieval Evidence

Post-review retrieval evidence was refreshed from official URLs at
`2026-07-16T03:27:12Z`. `body_sha256` is the SHA-256 of the HTTP response body
after redirects. The locator and short excerpt anchor preserve the source
position used by this report without copying full official pages into the repo.
The source-fact extract table records bounded text extracts and extract hashes
for every relied-on platform fact.

| `official_source_ledger_id` | Final URL fetched | HTTP status | Body bytes | `body_sha256` | Page or section locator | Short excerpt anchor |
|---|---|---:|---:|---|---|---|
| `OSL-001` | `https://learn.chatgpt.com/docs/models` | 200 | 599306 | `01dfd5f6e7d67308cf2d2897256d3b1442b1cef8a1db165e6989c520dd073e1e` | Models page; model cards and reasoning selector | `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, `gpt-5.3-codex-spark` |
| `OSL-002` | `https://learn.chatgpt.com/docs/agent-configuration/subagents` | 200 | 539340 | `18fda902a30f9563e20645ed0549193ef4bc15b330e7bd6e3e0397b23055714c` | Agent configuration; optional fields | `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config` |
| `OSL-003` | `https://learn.chatgpt.com/docs/config-file/config-reference` | 200 | 1157392 | `483eb6d8baa3ceee65d2196ba41cecad1ee6be87bdf37b7886d3e60b39c426d2` | Config reference; `model_reasoning_effort` | `minimal, low, medium, high, xhigh` |
| `OSL-004` | `https://learn.chatgpt.com/docs/app-server` | 200 | 835428 | `0aeafcfd075e3aa463341fe08e0a5a29f4b8c8d17778423d4b5c45941181a373` | App server; JSON-RPC methods and model catalog | `model/list`, `includeHidden`, `supportedReasoningEfforts`, `defaultReasoningEffort`, `inputModalities`, `modelProvider/capabilities/read`, `model/rerouted` |
| `OSL-005` | `https://learn.chatgpt.com/docs/non-interactive-mode` | 200 | 378886 | `e5f9d89f239bdbb4e15d2c4eac317f66a12cf79a6a168ba0245e509ce433b69c` | Non-interactive mode; structured outputs | `--output-schema` |
| `OSL-006` | `https://learn.chatgpt.com/docs/extend/mcp` | 200 | 402853 | `80963d1ff2ed16f9739527a3bc64a0918fde9b5c053b5d0f6d0009a07e37aae7` | MCP extension; server configuration | `[mcp_servers.<server-name>]` |
| `OSL-007` | `https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt` | 200 | 308207 | `35f553926c7bc211f0b49fabaefc7e8c6ab12d9c3de1f95a2519d3661553235c` | MCP apps in ChatGPT; recommended approach | `standard bridge`, `tools/call` |
| `OSL-008` | `https://developers.openai.com/api/docs/guides/latest-model` | 200 | 417218 | `214b2e623fe154d5908ff433a1ea6d3987a08098e114842045b5c99ec1141b1a` | Latest-model guidance; GPT-5.6 reasoning | `Set reasoning.effort intentionally` |
| `OSL-009` | `https://developers.openai.com/api/docs/deprecations` | 200 | 425288 | `c9afecea6c0d8e9e4cb93abe7823a9348fb13d7a6f6f6f66960bcfd3dbf18dd4` | Deprecations; overview and lifecycle taxonomy | `retire older models` |

Official-source observations:

- OSL-001 documents `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, and `gpt-5.3-codex-spark` as Codex-relevant entries or examples for the relevant surfaces.
- OSL-001 documents model and reasoning controls for Codex surfaces and presents higher effort as deeper but slower.
- OSL-002 documents that omitted custom-agent optional fields inherit from the parent session.
- OSL-003 documents `model_reasoning_effort` values and managed model defaults.
- OSL-004 documents `model/list`, `includeHidden`, `supportedReasoningEfforts`, `defaultReasoningEffort`, `inputModalities`, `modelProvider/capabilities/read`, `model/rerouted`, and token-usage updates for the app-server surface.
- OSL-008 documents the `gpt-5.6` API alias as an API-surface fact only; this report does not use that alias as Codex availability evidence.
- OSL-009 is not used as exact lifecycle evidence for the historical seed
  slugs below because this report does not record exact page text for those
  slugs. They remain undocumented historical project inputs and cannot be
  admitted without a refreshed official source binding.

### Exact Source Fact Bindings

These are the exact source facts from the source snapshot that G56R-001 uses for
platform claims, candidate admission, effort-source scoping, telemetry handoff,
or invalidation rules. If a source fact is not listed here, it is not used to
admit a route or establish a platform fact. Historical seed exclusions are
classified as undocumented project inputs unless exact lifecycle source text is
recorded.

| `source_fact_id` | Source | Page or section locator | Short excerpt anchor | Exact captured fact used by G56R-001 | Bound claims |
|---|---|---|---|---|---|
| `G56R-001-OSF-001` | `OSL-001` | Models; "Where each model shines"; Sol subsection | `complex, open-ended work` | `gpt-5.6-sol` is positioned for complex, open-ended, high-value work needing analysis, judgment, or polish. | Sol candidate rationale for analysis, checklist, clarify, domain research, implementation, phase execution, and consensus-synthesis roles |
| `G56R-001-OSF-002` | `OSL-001` | Models; "Where each model shines"; Terra subsection | `strong reasoning and tool use` | `gpt-5.6-terra` is positioned for everyday work requiring strong reasoning and tool use. | Terra candidate rationale for codebase, spec-context, and UAT runbook roles |
| `G56R-001-OSF-003` | `OSL-001` | Models; "Where each model shines"; Luna subsection | `clear, repeatable tasks` | `gpt-5.6-luna` is positioned for clear, specific, repeatable, or high-volume work. | Luna candidate rationale for optional helper, UAT runbook, and gate-validation roles |
| `G56R-001-OSF-004` | `OSL-001` | Models; `5.5` model card | `complex coding, computer use, knowledge work` | `gpt-5.5` is recorded as a previous-generation model for complex coding, computer use, knowledge work, and research. | Immutable production-comparator candidate rationale where current Codex TOMLs declare `gpt-5.5` |
| `G56R-001-OSF-005` | `OSL-001` | Models; `5.3 Codex Spark` model card | `near-instant, real-time coding iteration` | `gpt-5.3-codex-spark` is captured as a text-only, low-latency research-preview entry. | Optional helper candidate rationale with text-only and availability questions |
| `G56R-001-OSF-006` | `OSL-001` | Models; Codex reasoning guidance | `Higher reasoning effort can improve results` | Codex model guidance positions higher reasoning effort as potentially better for complex tasks but slower and more token intensive. | Effort-source scoping and G56R-002 effort questions |
| `G56R-001-OSF-007` | `OSL-002` | Subagents; custom-agent optional fields | `inherit from the parent session` | Omitted custom-agent optional fields inherit from the parent session. | Exact-treatment questions and effective-runtime deferral |
| `G56R-001-OSF-008` | `OSL-002` | Subagents; custom-agent file schema | `supported config.toml keys` | Custom agent files may include supported config keys such as model, effort, sandbox, MCP servers, and skills config. | Role contracts and effort-surface records |
| `G56R-001-OSF-009` | `OSL-003` | Config reference; reasoning effort key | `minimal, low, medium, high, xhigh` | The config reference documents the `model_reasoning_effort` value set for the config surface. | Effort-surface records and managed-default caveats |
| `G56R-001-OSF-010` | `OSL-003` | Config reference; managed model defaults | `Default reasoning effort for new threads` | Managed new-thread reasoning effort defaults can be skipped by explicit model or reasoning-effort overrides. | Effort-surface records and default-scope caveats |
| `G56R-001-OSF-011` | `OSL-004` | App server; method summary list | `includeHidden`, `inputModalities`, `modelProvider/capabilities/read` | App-server method documentation lists model discovery, hidden-model inclusion, model-catalog modality fields, and provider capability bounds. | G56R-002 capability discovery and provider-capability questions |
| `G56R-001-OSF-012` | `OSL-004` | App server; model entry fields | `supportedReasoningEfforts`, `defaultReasoningEffort`, `inputModalities` | Model entries can include supported reasoning efforts, suggested default effort fields, and supported input modality fields. | Effort-surface records and telemetry questions |
| `G56R-001-OSF-013` | `OSL-004` | App server; model events | `model/rerouted` | The app server documents reroute and token-usage events for active threads. | Telemetry requirements and route-match classification |
| `G56R-001-OSF-014` | `OSL-005` | Non-interactive mode; JSONL events | `thread.started` | Non-interactive JSONL output exposes event types for thread, turn, item, and error states. | Non-interactive telemetry caveats |
| `G56R-001-OSF-015` | `OSL-005` | Non-interactive mode; output schema | `--output-schema` | Non-interactive mode can request final JSON Schema-conforming output. | Fixture output and automation caveats |
| `G56R-001-OSF-016` | `OSL-006` | MCP extension; CLI commands | `codex mcp list` | Codex MCP commands can list configured servers and start OAuth login. | MCP contract and access questions |
| `G56R-001-OSF-017` | `OSL-006` | MCP extension; IDE server setup | `STDIO or Streamable HTTP` | MCP server setup supports STDIO or Streamable HTTP server configuration. | MCP transport questions |
| `G56R-001-OSF-018` | `OSL-006` | MCP extension; plugin-provided servers | `Installed plugins can bundle MCP servers` | Installed plugins can bundle MCP servers launched from the plugin manifest. | Plugin MCP and tool-policy questions |
| `G56R-001-OSF-019` | `OSL-007` | Apps SDK MCP apps; overview | `standard bridge` | MCP Apps UIs run in iframes and communicate with hosts over the standard bridge. | ChatGPT app-surface boundary |
| `G56R-001-OSF-020` | `OSL-007` | Apps SDK MCP apps; host bridge | `tools/call` | MCP Apps use the MCP tool surface for tool calls instead of host-specific UI globals. | Apps SDK exclusion and tool boundary |
| `G56R-001-OSF-021` | `OSL-008` | API latest-model guidance; model targets | `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | API guidance documents the GPT-5.6 family targets and `gpt-5.6` alias. | Candidate family context; not Codex availability |
| `G56R-001-OSF-022` | `OSL-008` | API latest-model guidance; reasoning effort | `none, low, medium, high, xhigh, max` | API guidance documents GPT-5.6 reasoning-effort values for the API surface. | API effort caveat and G56R-002 effort questions |
| `G56R-001-OSF-023` | `OSL-008` | API latest-model guidance; pro mode | `reasoning.mode` | API pro mode uses `reasoning.mode` with the selected GPT-5.6 model rather than a separate Pro model slug. | API pro-mode caveat |
| `G56R-001-OSF-024` | `OSL-009` | API deprecations; overview | `retire older models` | The deprecations page documents that OpenAI retires older models over time. | Lifecycle invalidation rules |
| `G56R-001-OSF-025` | `OSL-009` | API deprecations; replacement list | `recommended replacements` | The deprecations page lists API deprecations with recommended replacements. | Lifecycle taxonomy and exact-source requirement |

### Source Fact Extract Evidence

Each extract is a bounded official-documentation passage normalized as the exact
UTF-8 string shown in the table, with no trailing newline, then hashed with
SHA-256. These extracts are the durable text evidence for the source-fact
summaries above.

| `source_fact_id` | Normalized extract | `extract_sha256` |
|---|---|---|
| `G56R-001-OSF-001` | Sol, for complex, open-ended work. Choose Sol for ambiguous, difficult, or high-value tasks that need extra analysis, judgment, or polish. | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` |
| `G56R-001-OSF-002` | Terra, the pragmatic all-rounder. Choose Terra for everyday work that needs strong reasoning and tool use. | `c2b6a5a56e3cd741d3ad4a04a5c1dbdd3ff6c03839d7330338f1aaa22a8deb5a` |
| `G56R-001-OSF-003` | Luna, for clear, repeatable tasks. Choose Luna for specific, high-volume tasks when you know what a good result looks like. | `c34327f8653d2545e37d363aac5a1fe0e3c515bcb7bb5772221b616936c62c61` |
| `G56R-001-OSF-004` | 5.5 Previous-generation frontier model for complex coding, computer use, knowledge work, and research workflows. | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` |
| `G56R-001-OSF-005` | 5.3 Codex Spark Text-only research preview model optimized for near-instant, real-time coding iteration. | `1c030839b9cbe839b85389b87b9352fef6f823ef31a76e35264039770a4f969e` |
| `G56R-001-OSF-006` | Higher reasoning effort can improve results for complex tasks, but it takes longer and uses more tokens. Start with the default effort and increase it when the task needs deeper planning or analysis. | `03090517fd1b341a5296de361c9a6ea6a212dea257c914316a7d326eaa2f0201` |
| `G56R-001-OSF-007` | Optional fields such as `nickname_candidates`, `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` inherit from the parent session when you omit them. | `5b71215d51627fbb74ba932b6972d51769d34384af40996b82221083d40376d7` |
| `G56R-001-OSF-008` | You can also include other supported `config.toml` keys in a custom agent file, such as `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config`. | `5a83d9f074e7ed211c72cf865c5ff4d06e835a4954ef13301e81f604c429a291` |
| `G56R-001-OSF-009` | `model_reasoning_effort` values: `minimal`, `low`, `medium`, `high`, `xhigh` | `d9ab590ed9b72eee2e009c232103b62ef41edf149559e5c69c2fca582f6dfb71` |
| `G56R-001-OSF-010` | Default reasoning effort for new threads. An explicit model or reasoning-effort override skips both managed model fields. | `324540fc39da5a631e6464689d09eb9b9e6b5bce2910ac5f3b806fc53e0d1879` |
| `G56R-001-OSF-011` | `model/list` - list available models (set `includeHidden: true` to include entries with `hidden: true`) with effort options, optional `upgrade`, and `inputModalities`. `modelProvider/capabilities/read` - read provider capability bounds for model/provider combinations. | `5a0c2702d4db3f7b439a3eefacd5938e9bd2e99de100c99c6fc42dc5b5087e8d` |
| `G56R-001-OSF-012` | Each model entry can include: `supportedReasoningEfforts` - supported effort options for the model. `defaultReasoningEffort` - suggested default effort for clients. `inputModalities` - supported input types for the model (for example `text`, `image`). | `474bc20a36e3b6606edae7197b33558c963605367d4d86e7c87518515d610215` |
| `G56R-001-OSF-013` | `model/rerouted` - `{ threadId, turnId, fromModel, toModel, reason }` when the service routes a request to another model. `thread/tokenUsage/updated` - usage updates for the active thread. | `954d45cbcb51835b822360b0ed852c8b332f44f801d6c99dc01abd5c2fb648bb` |
| `G56R-001-OSF-014` | Event types include `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`, and `error`. | `0ff9c2eefb4c09da4f37c6144af8ed4c17e505a1cc4c7f85ff7f75c19ce06190` |
| `G56R-001-OSF-015` | If you need structured data for downstream steps, use `--output-schema` to request a final response that conforms to a JSON Schema. | `81f6408bbe643112b619d0f53f90fca3f0818361493fd609ca27a4df237ca41d` |
| `G56R-001-OSF-016` | Run `codex mcp list` to see configured servers. To see all available MCP commands, run `codex mcp --help`. For a server that supports OAuth, run `codex mcp login <server-name>`. | `787a36d126fa1d3d7ff2f849c0ea6a4967f7292e81b8ae2fe005845e9059f045` |
| `G56R-001-OSF-017` | Enter a name, choose STDIO or Streamable HTTP | `dc1c7a4d0de50876d7c0d0d09c89e71a2d82d9e27a9d7a9b50d03911d3950d7e` |
| `G56R-001-OSF-018` | Installed plugins can bundle MCP servers in their plugin manifest. | `10bba8b958c44bd951892a692db3ed338bbebf2eab695cb2b1972c837168e366` |
| `G56R-001-OSF-019` | MCP Apps UIs run inside an iframe and communicate with the host over a standard bridge (`ui/*` JSON-RPC over `postMessage`). | `a1ede18ae81b82cd249452b49cd7d5e9938aed283641444ab07acfdd5d695224` |
| `G56R-001-OSF-020` | Tool calls: use the MCP tool surface (for example, `tools/call`) rather than host-specific UI globals | `936b6b6ee5216acb3c251feb34e57df5b62e9145b258c7f057f9c7331577496e` |
| `G56R-001-OSF-021` | Choose the target model for the workload. Use `gpt-5.6-sol` for frontier capability, `gpt-5.6-terra` for a balance of intelligence and cost, or `gpt-5.6-luna` for efficient, high-volume workloads. The `gpt-5.6` alias routes requests to `gpt-5.6-sol`. | `df53899dd3c4564b6e13f67566744829544bd74662a3a5202e96a6c219948496` |
| `G56R-001-OSF-022` | Set `reasoning.effort` intentionally. GPT-5.6 supports `none`, `low`, `medium`, `high`, `xhigh`, and `max`. | `a3f7de9b93a6e2a4d56bcfc9c80fad72a56db4ed9d6ed080077e0075bb6a0e89` |
| `G56R-001-OSF-023` | To use pro mode, keep your selected GPT-5.6 model and set `reasoning.mode` to `pro` in the Responses API; do not switch to a separate Pro model slug. | `44438a2665277f66288fd38fe91acc7cbfc5ae3b3959a3c0a9e7ac5361d61683` |
| `G56R-001-OSF-024` | As we launch safer and more capable models, we regularly retire older models. Software relying on OpenAI models may need occasional updates to keep working. | `c6db7c1ce404f14a931e0da04d3866dd98d3029d87e650fa704cf0f452f5c629` |
| `G56R-001-OSF-025` | This page lists all API deprecations, along with recommended replacements. | `769fd0aa21b5cf22419e75344c9be42e601d10f8127c4a228ab05e9ecc83867d` |

## Project Input Inventory

| `project_input_id` | Project input | Evidence class | Use |
|---|---|---|---|
| `G56R-001-PI-001` | `docs/prd-codex-gpt-5-6-agent-routing.md` | `project_input` | Acceptance criteria, evidence authority, G56R dependency boundaries |
| `G56R-001-PI-002` | `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md` | `project_input` | Current roadmap seed set, spec dependencies, target artifact |
| `G56R-001-PI-003` | `docs/ai/specs/.process/G56R-001-workflow.md` | `project_input` | Durable workflow, gates, checklist domains, task and analysis evidence |
| `G56R-001-PI-004` | `specs/g56r-001-candidate-route-baseline/spec.md` | `project_input` | Requirements and record shapes |
| `G56R-001-PI-005` | `specs/g56r-001-candidate-route-baseline/plan.md` | `project_input` | One-report architecture and declared file operation |
| `G56R-001-PI-006` | `specs/g56r-001-candidate-route-baseline/tasks.md` | `project_input` | Implementation and verification tasks |
| `G56R-001-PI-007` | `speckit-pro/codex-agents/*.toml` | `project_input` | Current active Codex role inventory, declared TOML fields, and legacy route guidance such as the UAT `gpt-5.4` compatibility fallback |
| `G56R-001-PI-008` | `speckit-pro/codex-skills/` | `project_input` | Codex skill surfaces that may invoke or consume future route policy; read-only in G56R-001 |
| `G56R-001-PI-009` | `speckit-pro/skills/` | `project_input` | Claude skill surfaces retained for cross-platform parity context; read-only in G56R-001 |
| `G56R-001-PI-010` | `speckit-pro/speckit_pro_runner/helpers/install.py` and `speckit-pro/speckit_pro_runner/helpers/registry.py` | `project_input` | Installer and helper registry surfaces, including environment/flag-driven model rewrite behavior future route materialization may need to preserve; no behavior changed in G56R-001 |
| `G56R-001-PI-011` | `speckit-pro/speckit_pro_runner/gates/payloads.py` | `project_input` | Generated-payload contract guard surface; no payload behavior changed in G56R-001 |
| `G56R-001-PI-012` | `scripts/build-plugin-payloads.py` | `project_input` | Payload build entrypoint reference for future release impact review; no generated artifact changed in G56R-001 |
| `G56R-001-PI-013` | `dist/codex/speckit-pro/` and `dist/claude/speckit-pro/` | `project_input` | Generated payload references only; not edited and not platform authority |
| `G56R-001-PI-014` | `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/` | `project_input` | Installed-cache fixture references only; not edited and not platform authority |
| `G56R-001-PI-015` | `speckit-pro/agents/consensus-synthesizer.md` and `speckit-pro/agents/gate-validator.md` | `project_input` | Claude parity-role contract inputs only |
| `G56R-001-PI-016` | `tests/speckit-pro/layer6-efficiency/` | `project_input` | Current prompt-emulation fixture state and future fixture backlog |

Generated payloads, installed caches, historical results, and local runtime
responses are inventory only. They are not candidate authority.

## Current Roadmap Seed Admission

| Seed model | Source bindings | G56R-001 status | Required G56R-002 question |
|---|---|---|---|
| `gpt-5.6-sol` | `OSL-001`, `OSL-008` | `source_bound_for_capability_discovery` | Does the pinned client expose it, with which supported efforts and modalities, for each role surface? |
| `gpt-5.6-terra` | `OSL-001`, `OSL-008` | `source_bound_for_capability_discovery` | Does the pinned client expose it, with which supported efforts and modalities, for each role surface? |
| `gpt-5.6-luna` | `OSL-001`, `OSL-008` | `source_bound_for_capability_discovery` | Does the pinned client expose it, with which supported efforts and modalities, for each role surface? |
| `gpt-5.5` | `OSL-001`, `OSL-004` | `source_bound_for_capability_discovery` | Is it available to the pinned client and should current TOML declarations retain it as comparator input? |
| `gpt-5.3-codex-spark` | `OSL-001`, `OSL-004` | `source_bound_for_capability_discovery` | Is this preview available to the pinned account and suitable only for text-only helper work? |

Unsupported admitted seed candidates: **0**.

## Historical Seed Exclusions

| Historical or legacy input | Source bindings | Status | Lifecycle state | Shutdown date | Replacement model | Treatment |
|---|---|---|---|---|---|---|
| `gpt-5.1` | none; historical project input only | `rejected_undocumented_for_current_codex_route` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | Do not admit without a current official Codex source for this exact slug. |
| `gpt-5.1-codex-max` | none; historical project input only | `rejected_undocumented_lifecycle_detail` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | Do not admit without exact official lifecycle or current Codex source text for this slug. |
| `gpt-5.2` | none; historical project input only | `rejected_undocumented_for_current_codex_route` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | API-key availability, if any, is not route authority. |
| `gpt-5.2-codex` | none; historical project input only | `rejected_undocumented_lifecycle_detail` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | Do not admit without exact official lifecycle or current Codex source text for this slug. |
| `gpt-5.2-codex-pro` | none; historical project input only | `rejected_undocumented` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | Do not infer from GPT-5.6 pro mode or adjacent names. |
| `gpt-5.4` | `G56R-001-PI-007` UAT TOML description and `G56R-001-PI-010` installer rewrite surface only | `rejected_undocumented_for_current_codex_route` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | Legacy project-input fallback guidance only; do not admit unless a current official Codex source supports this exact slug for the pinned surface. |

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

Role-specific route-policy notes:

- `G56R-001-AC-UAT-RUNBOOK-AUTHOR`: the active TOML description contains
  legacy installer guidance to rewrite the file to `gpt-5.4` when `gpt-5.5`
  is unavailable. G56R-001 records that guidance as project input only and
  rejects `gpt-5.4` as `undocumented_in_current_snapshot` in Historical Seed
  Exclusions.

### Role Hash Validation Evidence

Hash validation was recomputed for all twelve role sources after review
remediation. Full-file hashes use the raw file bytes. Instruction hashes use the
parsed TOML `developer_instructions` string for Codex TOML files and the
Markdown body after YAML front matter for parity-role Markdown files, encoded as
UTF-8 with no added newline.

| `agent_contract_id` | Source file | Instruction extraction rule | `instruction_sha256` | `full_file_sha256` | Result |
|---|---|---|---|---|---|
| `G56R-001-AC-ANALYZE-EXECUTOR` | `speckit-pro/codex-agents/analyze-executor.toml` | TOML `developer_instructions` parsed string | `771a5b9075240abf72b92449dae9960a03b8873e516468a13b7c6da17245f64c` | `eac0a81678fe8b82411ab90258af41bc819681e4111547c16581e12d60afb3a4` | pass |
| `G56R-001-AC-AUTOPILOT-FAST-HELPER` | `speckit-pro/codex-agents/autopilot-fast-helper.toml` | TOML `developer_instructions` parsed string | `0da3103f276542e615f2257f90514d58e3af9a61e6c59555d9c611ea7aff2b95` | `aa570f8ff51fa3cb7848d8c05253ddf5d080f5d4a2dbed9a55f0149fceb1296d` | pass |
| `G56R-001-AC-CHECKLIST-EXECUTOR` | `speckit-pro/codex-agents/checklist-executor.toml` | TOML `developer_instructions` parsed string | `bb97bee3e0e52ae3885dacefb9659f9c47250508fce289aaa5daeccc59353218` | `ec29b97b8211c626e00fed1edbf0f601d3328dde57e22fb54626b5a92c2671d0` | pass |
| `G56R-001-AC-CLARIFY-EXECUTOR` | `speckit-pro/codex-agents/clarify-executor.toml` | TOML `developer_instructions` parsed string | `c5fba94ebe76b2589e453a7f5d8acbe94cb5a804bf9235401824e8ea0fd47486` | `7853d199bcf06685239d724a289d7aeaafcf5a133e665c21bc23375220d3f490` | pass |
| `G56R-001-AC-CODEBASE-ANALYST` | `speckit-pro/codex-agents/codebase-analyst.toml` | TOML `developer_instructions` parsed string | `256ff48441eea5f6d94e792d68d72ef9735a683292046c7e68ad5008a76b010f` | `12f41b87c1a2f2003c588d328702144d7ffcbef11f28489124751be44bb98a1e` | pass |
| `G56R-001-AC-DOMAIN-RESEARCHER` | `speckit-pro/codex-agents/domain-researcher.toml` | TOML `developer_instructions` parsed string | `efee1fa569e635801c797711220084f86511a7ea2f6ac1e088a6a004ae624463` | `eb558933bb60f874d5bed972226100b8ff8cf5adf5c334b184ef232f0287518f` | pass |
| `G56R-001-AC-IMPLEMENT-EXECUTOR` | `speckit-pro/codex-agents/implement-executor.toml` | TOML `developer_instructions` parsed string | `6e2b1adca0b0ee96e8af6593d1de5a4dcb5696fd3cbcd67601b428c334ac71f8` | `7a95370adcc423203d64c1440e9f0a17af3a1a9ca2a3a6262fa6ceb8efab6148` | pass |
| `G56R-001-AC-PHASE-EXECUTOR` | `speckit-pro/codex-agents/phase-executor.toml` | TOML `developer_instructions` parsed string | `2ecf93717029553369f62f902f8ac95bad5f77e726dbbb8c7065d9bde36c4fe5` | `6f974a124ea4f3422f6650e4c9b501c15916ff874e2490a46cecfeedd634f7c9` | pass |
| `G56R-001-AC-SPEC-CONTEXT-ANALYST` | `speckit-pro/codex-agents/spec-context-analyst.toml` | TOML `developer_instructions` parsed string | `b276d4f074e07986c7e0cc75b8a52df7bdbebd7bb8ced05c3aadb615f1e7ade8` | `680e93129186f37d245ffa35dc44e064dffe24b497675aaa72b275daa7642674` | pass |
| `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `speckit-pro/codex-agents/uat-runbook-author.toml` | TOML `developer_instructions` parsed string | `e78f3a5ddf51cbe26fc286780e7c711043ef0cccdd9a49d39fd0373f906b95cf` | `ea1e74b375a9fab40881d52574ec9c184033abe020e69637eac1b2248509b918` | pass |
| `G56R-001-AC-CONSENSUS-SYNTHESIZER` | `speckit-pro/agents/consensus-synthesizer.md` | Markdown body after YAML front matter | `1d668a009a1a7ddc0ac4af9663a7f7dba367519b431af3271e212c0426cd99f2` | `548b9eeb69b6c3f8b8f5429a9ae567d456e4a4ddd1482efe1c1e947e84737327` | pass |
| `G56R-001-AC-GATE-VALIDATOR` | `speckit-pro/agents/gate-validator.md` | Markdown body after YAML front matter | `f30cae871e3e63ac736d5cd8695dfa42a73ded50807f46709139c663d91c070e` | `ecfa70143aa02c943474f23d38cd5c0b01ca1fabae7d2a899c45d35eb7bb5f0d` | pass |

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

### Normalized Role Contract Fields

All role rows have `source_class=project_input`. Active Codex rows use the
listed TOML file as `hash_source`; parity-only rows use the listed Claude source
file as project input. All effective runtime permission, parent override,
sandbox/approval, tool, skill, and MCP availability claims remain
`runtime_verification_needed` until G56R-002 proves the pinned client behavior.

| `agent_contract_id` | Client surface | Safety contract | Grounding contract | Tool contract | Skill contract | MCP contract | Platform divergence |
|---|---|---|---|---|---|---|---|
| `G56R-001-AC-ANALYZE-EXECUTOR` | Codex custom agent | May mutate only scoped findings; must preserve marker accounting and verification evidence | Uses project specs, plans, tasks, code, and official docs only when required by a finding | Project commands, tests, file reads, edits | Analyze workflow skill when invoked by parent | Parent-provided MCP only; no intrinsic MCP dependency | None recorded beyond runtime verification |
| `G56R-001-AC-AUTOPILOT-FAST-HELPER` | Codex custom agent | Read-only advisory; no decisions, spawned agents, commands, or file mutation | Uses prompt context only | No tools by role contract | No skill dependency | No MCP dependency | Optional helper may be omitted if no qualified route exists |
| `G56R-001-AC-CHECKLIST-EXECUTOR` | Codex custom agent | May remediate true checklist gaps only in scoped artifacts | Uses checklist evidence, spec, plan, and official docs for requirement gaps | Project reads, marker checks, scoped edits | Checklist workflow skill | Parent-provided MCP only | None recorded beyond runtime verification |
| `G56R-001-AC-CLARIFY-EXECUTOR` | Codex custom agent | Read-only; prepares bounded questions without acting as user | Uses workflow, spec, project context, and official docs | File reads and search only | Clarify workflow context only | No intrinsic MCP dependency | None recorded beyond runtime verification |
| `G56R-001-AC-CODEBASE-ANALYST` | Codex custom agent | Read-only; must not propose behavior unsupported by repo evidence | Codebase files and exact references only | Search, structure, targeted reads | No required skill | No intrinsic MCP dependency | None recorded beyond runtime verification |
| `G56R-001-AC-DOMAIN-RESEARCHER` | Codex custom agent | Read-only; no project mutation | Official docs, standards, and cited source material | Web or docs retrieval where parent grants it | Library/domain research skills when available | Optional source-extraction MCP when parent grants it | Must not substitute project input for platform facts |
| `G56R-001-AC-IMPLEMENT-EXECUTOR` | Codex custom agent | Workspace-write only for assigned task; follows TDD and scoped verification | Spec, plan, task, project commands, and official docs when required | Project commands, tests, edits | Implement workflow skill when invoked | Parent-provided MCP only | None recorded beyond runtime verification |
| `G56R-001-AC-PHASE-EXECUTOR` | Codex custom agent | Workspace-write only for requested phase artifacts | Loaded phase prompt and command-owned templates | Phase command scripts/templates and file edits | Specify, plan, or tasks workflow skill | Parent-provided MCP only | None recorded beyond runtime verification |
| `G56R-001-AC-SPEC-CONTEXT-ANALYST` | Codex custom agent | Read-only project-context answerer | Constitution, roadmap, specs, plans, and decision records | Search and targeted reads | No required skill | No intrinsic MCP dependency | None recorded beyond runtime verification |
| `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | Codex custom agent | Workspace-write to generated UAT skeleton only; fails open when source evidence is insufficient | Spec, plan, quickstart, diff, and project commands | Skeleton reads and direct skeleton edit | UAT skeleton workflow context | No intrinsic MCP dependency | None recorded beyond runtime verification |
| `G56R-001-AC-CONSENSUS-SYNTHESIZER` | Future Codex custom agent; currently parity-only | Read-only synthesis of analyst outputs; no new research or edits | Analyst responses and cited evidence only | Future Codex contract must preserve no-new-research behavior | Future orchestration skill only when explicitly invoked | Future MCP contract must not broaden evidence authority | Claude source exists; Codex TOML absent until G56R-009 |
| `G56R-001-AC-GATE-VALIDATOR` | Future Codex custom agent; currently parity-only | Run supplied gate and preserve JSON; no remediation | Verbatim command output only | Gate command execution only | Future gate-validation workflow only when supplied | Future MCP contract must preserve verbatim evidence | Claude source exists; Codex TOML absent until G56R-009 |

## Provisional Candidate Routes

Candidate records are source-bound model candidates for G56R-002 capability
discovery. Their executable model/effort tuples are blocked until G56R-002
captures `model/list` supported efforts for the pinned client. They are not
available, executable, qualified, preferred, efficient, fallback-ordered, or
installed.

The two parity-source rows are included as blocked source-bound candidates so
the manifest covers all twelve role contracts. They remain non-executable until
G56R-009 creates active Codex parity TOMLs; G56R-002 may carry them only as
capability questions, not executable routes.

| `candidate_route_id` | `agent_contract_id` | Model | `model_reasoning_effort` | `official_source_ledger_ids` | `effort_surface_record_ids` | `candidate_status` | Lifecycle | `shutdown_date` | `replacement_model` | `role_instruction_sha256` | Role-contract binding | Required capabilities | Unsupported facts and G56R-002 questions | Invalidation rules |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `G56R-001-CR-ANALYZE-EXECUTOR-SOL` | `G56R-001-AC-ANALYZE-EXECUTOR` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `771a5b9075240abf72b92449dae9960a03b8873e516468a13b7c6da17245f64c` | analyze safety, mutation, grounding, tool, skill, MCP, and output contracts | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-ANALYZE-EXECUTOR-GPT55` | `G56R-001-AC-ANALYZE-EXECUTOR` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `771a5b9075240abf72b92449dae9960a03b8873e516468a13b7c6da17245f64c` | immutable production-comparator binding for analyze role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-SPARK` | `G56R-001-AC-AUTOPILOT-FAST-HELPER` | `gpt-5.3-codex-spark` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `0da3103f276542e615f2257f90514d58e3af9a61e6c59555d9c611ea7aff2b95` | optional helper read-only advisory binding | model listing, account/surface availability, supported efforts, text-only constraint, no-tool treatment | runtime supported effort tuple, lifecycle status, account availability, text-only suitability, helper qualification | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-LUNA` | `G56R-001-AC-AUTOPILOT-FAST-HELPER` | `gpt-5.6-luna` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `0da3103f276542e615f2257f90514d58e3af9a61e6c59555d9c611ea7aff2b95` | optional helper concise-summary role-fit hypothesis | model listing, supported efforts, input modalities, no-tool exact treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, helper latency and quality qualification | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CHECKLIST-EXECUTOR-SOL` | `G56R-001-AC-CHECKLIST-EXECUTOR` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `bb97bee3e0e52ae3885dacefb9659f9c47250508fce289aaa5daeccc59353218` | checklist safety, mutation, grounding, tool, skill, MCP, and output contracts | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CHECKLIST-EXECUTOR-GPT55` | `G56R-001-AC-CHECKLIST-EXECUTOR` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `bb97bee3e0e52ae3885dacefb9659f9c47250508fce289aaa5daeccc59353218` | immutable production-comparator binding for checklist role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CLARIFY-EXECUTOR-SOL` | `G56R-001-AC-CLARIFY-EXECUTOR` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `c5fba94ebe76b2589e453a7f5d8acbe94cb5a804bf9235401824e8ea0fd47486` | clarify read-only role boundary and output contract | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CLARIFY-EXECUTOR-GPT55` | `G56R-001-AC-CLARIFY-EXECUTOR` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `c5fba94ebe76b2589e453a7f5d8acbe94cb5a804bf9235401824e8ea0fd47486` | immutable production-comparator binding for clarify role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CODEBASE-ANALYST-TERRA` | `G56R-001-AC-CODEBASE-ANALYST` | `gpt-5.6-terra` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `256ff48441eea5f6d94e792d68d72ef9735a683292046c7e68ad5008a76b010f` | codebase read-only evidence contract | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CODEBASE-ANALYST-GPT55` | `G56R-001-AC-CODEBASE-ANALYST` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `256ff48441eea5f6d94e792d68d72ef9735a683292046c7e68ad5008a76b010f` | immutable production-comparator binding for codebase analyst role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-DOMAIN-RESEARCHER-SOL` | `G56R-001-AC-DOMAIN-RESEARCHER` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `efee1fa569e635801c797711220084f86511a7ea2f6ac1e088a6a004ae624463` | domain-research official-source grounding contract | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-DOMAIN-RESEARCHER-GPT55` | `G56R-001-AC-DOMAIN-RESEARCHER` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `efee1fa569e635801c797711220084f86511a7ea2f6ac1e088a6a004ae624463` | immutable production-comparator binding for domain researcher role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-SOL` | `G56R-001-AC-IMPLEMENT-EXECUTOR` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `6e2b1adca0b0ee96e8af6593d1de5a4dcb5696fd3cbcd67601b428c334ac71f8` | implement TDD mutation, safety, tool, skill, MCP, and output contracts | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-GPT55` | `G56R-001-AC-IMPLEMENT-EXECUTOR` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `6e2b1adca0b0ee96e8af6593d1de5a4dcb5696fd3cbcd67601b428c334ac71f8` | immutable production-comparator binding for implement role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-PHASE-EXECUTOR-SOL` | `G56R-001-AC-PHASE-EXECUTOR` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `2ecf93717029553369f62f902f8ac95bad5f77e726dbbb8c7065d9bde36c4fe5` | phase command mutation, template, and output contracts | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-PHASE-EXECUTOR-GPT55` | `G56R-001-AC-PHASE-EXECUTOR` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `2ecf93717029553369f62f902f8ac95bad5f77e726dbbb8c7065d9bde36c4fe5` | immutable production-comparator binding for phase role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-TERRA` | `G56R-001-AC-SPEC-CONTEXT-ANALYST` | `gpt-5.6-terra` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `b276d4f074e07986c7e0cc75b8a52df7bdbebd7bb8ced05c3aadb615f1e7ade8` | spec-context read-only project-evidence contract | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-GPT55` | `G56R-001-AC-SPEC-CONTEXT-ANALYST` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `b276d4f074e07986c7e0cc75b8a52df7bdbebd7bb8ced05c3aadb615f1e7ade8` | immutable production-comparator binding for spec-context role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-TERRA` | `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `gpt-5.6-terra` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `e78f3a5ddf51cbe26fc286780e7c711043ef0cccdd9a49d39fd0373f906b95cf` | UAT skeleton rewrite safety, mutation, and output contract | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality, comparator parity | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-LUNA` | `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `gpt-5.6-luna` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `e78f3a5ddf51cbe26fc286780e7c711043ef0cccdd9a49d39fd0373f906b95cf` | structured repeatable UAT rewrite role-fit hypothesis | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, runtime availability, skeleton quality qualification | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-GPT55` | `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | `gpt-5.5` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `e78f3a5ddf51cbe26fc286780e7c711043ef0cccdd9a49d39fd0373f906b95cf` | immutable production-comparator binding for UAT role | model listing, supported efforts, input modalities, exact custom-agent treatment, telemetry | runtime supported effort tuple, lifecycle status, future availability, comparator exact treatment | source, capability, telemetry, instruction hash, role contract, or fixture/scorer change |
| `G56R-001-CR-CONSENSUS-SYNTHESIZER-SOL` | `G56R-001-AC-CONSENSUS-SYNTHESIZER` | `gpt-5.6-sol` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `1d668a009a1a7ddc0ac4af9663a7f7dba367519b431af3271e212c0426cd99f2` | consensus synthesis is a parity-source role contract; active Codex TOML is absent until G56R-009 | future Codex custom-agent source, model listing, supported efforts, exact custom-agent treatment, telemetry, route qualification | active Codex TOML absence, runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality | source, capability, telemetry, instruction hash, role contract, parity TOML creation, or fixture/scorer change |
| `G56R-001-CR-GATE-VALIDATOR-LUNA` | `G56R-001-AC-GATE-VALIDATOR` | `gpt-5.6-luna` | `blocked_pending_model_list_effort` | `OSL-001`, `OSL-002`, `OSL-003`, `OSL-004`, `OSL-008` | `G56R-001-ESR-001`, `G56R-001-ESR-002`, `G56R-001-ESR-003`, `G56R-001-ESR-004`, `G56R-001-ESR-005` | `blocked_pending_capability` | `undocumented_in_current_snapshot` | `not_recorded_in_snapshot` | `not_recorded_in_snapshot` | `f30cae871e3e63ac736d5cd8695dfa42a73ded50807f46709139c663d91c070e` | gate validation is a parity-source role contract; active Codex TOML is absent until G56R-009 | future Codex custom-agent source, model listing, supported efforts, exact custom-agent treatment, telemetry, route qualification | active Codex TOML absence, runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, quality | source, capability, telemetry, instruction hash, role contract, parity TOML creation, or fixture/scorer change |

### Candidate Required Qualification Artifact Bindings

Every candidate route record binds these required qualification artifacts before
it can advance beyond G56R-002 discovery: a `runtime_capability_snapshot_id`, a
`telemetry_profile_id`, a route-specific exact-treatment pair
(`route_resolution_id` and `execution_trace_id`), a G56R-003
`experiment_policy_id` with scorer contract, and the role-specific fixture
backlog record listed below.

| `candidate_route_id` | `fixture_backlog_id` | Capability artifact | Telemetry artifact | Exact-treatment artifact | Scorer or experiment artifact | Additional prerequisite |
|---|---|---|---|---|---|---|
| `G56R-001-CR-ANALYZE-EXECUTOR-SOL` | `G56R-001-FB-ANALYZE-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-ANALYZE-EXECUTOR-GPT55` | `G56R-001-FB-ANALYZE-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-SPARK` | `G56R-001-FB-AUTOPILOT-FAST-HELPER` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | G56R-010 helper policy |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-LUNA` | `G56R-001-FB-AUTOPILOT-FAST-HELPER` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | G56R-010 helper policy |
| `G56R-001-CR-CHECKLIST-EXECUTOR-SOL` | `G56R-001-FB-CHECKLIST-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-CHECKLIST-EXECUTOR-GPT55` | `G56R-001-FB-CHECKLIST-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-CLARIFY-EXECUTOR-SOL` | `G56R-001-FB-CLARIFY-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-CLARIFY-EXECUTOR-GPT55` | `G56R-001-FB-CLARIFY-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-CODEBASE-ANALYST-TERRA` | `G56R-001-FB-CODEBASE-ANALYST` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-CODEBASE-ANALYST-GPT55` | `G56R-001-FB-CODEBASE-ANALYST` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-DOMAIN-RESEARCHER-SOL` | `G56R-001-FB-DOMAIN-RESEARCHER` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-DOMAIN-RESEARCHER-GPT55` | `G56R-001-FB-DOMAIN-RESEARCHER` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-SOL` | `G56R-001-FB-IMPLEMENT-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-GPT55` | `G56R-001-FB-IMPLEMENT-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-PHASE-EXECUTOR-SOL` | `G56R-001-FB-PHASE-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-PHASE-EXECUTOR-GPT55` | `G56R-001-FB-PHASE-EXECUTOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-TERRA` | `G56R-001-FB-SPEC-CONTEXT-ANALYST` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-GPT55` | `G56R-001-FB-SPEC-CONTEXT-ANALYST` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-TERRA` | `G56R-001-FB-UAT-RUNBOOK-AUTHOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-LUNA` | `G56R-001-FB-UAT-RUNBOOK-AUTHOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | none |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-GPT55` | `G56R-001-FB-UAT-RUNBOOK-AUTHOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | comparator exact treatment |
| `G56R-001-CR-CONSENSUS-SYNTHESIZER-SOL` | `G56R-001-FB-CONSENSUS-SYNTHESIZER` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | G56R-009 active Codex parity TOML |
| `G56R-001-CR-GATE-VALIDATOR-LUNA` | `G56R-001-FB-GATE-VALIDATOR` | `runtime_capability_snapshot_id` | `telemetry_profile_id` | `route_resolution_id`, `execution_trace_id` | `experiment_policy_id` with scorer contract | G56R-009 active Codex parity TOML |

### Candidate Route Rationales

Each model candidate has a `candidate_rationale` that binds one exact source
fact and its extract hash to one role-contract need. Rationale records do not
claim runtime availability, quality, preference, or fallback order.

| `candidate_route_id` | `source_fact_id` | `source_fact_extract_sha256` | `candidate_rationale` | Known incompatibilities or gaps |
|---|---|---|---|---|
| `G56R-001-CR-ANALYZE-EXECUTOR-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Analyze remediation is complex, open-ended, and judgment-heavy, matching the Sol positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |
| `G56R-001-CR-ANALYZE-EXECUTOR-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured complex coding/research positioning supports an immutable comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-SPARK` | `G56R-001-OSF-005` | `1c030839b9cbe839b85389b87b9352fef6f823ef31a76e35264039770a4f969e` | The helper contract is read-only, no-tool, text summarization/triage; Spark's captured text-only low-latency preview positioning is a plausible discovery candidate. | Runtime supported effort tuple, lifecycle status, account/surface availability, text-only constraint, and helper quality remain unproven. |
| `G56R-001-CR-AUTOPILOT-FAST-HELPER-LUNA` | `G56R-001-OSF-003` | `c34327f8653d2545e37d363aac5a1fe0e3c515bcb7bb5772221b616936c62c61` | The helper contract is clear, specific, and repeatable, matching Luna's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, latency, and helper quality remain unproven. |
| `G56R-001-CR-CHECKLIST-EXECUTOR-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Checklist remediation requires judgment over evidence gaps and requirement quality, matching Sol's complex/high-value positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |
| `G56R-001-CR-CHECKLIST-EXECUTOR-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured complex work positioning supports an immutable checklist comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-CLARIFY-EXECUTOR-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Clarification design can require judgment and careful ambiguity resolution, matching Sol's complex/high-value positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |
| `G56R-001-CR-CLARIFY-EXECUTOR-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured knowledge-work positioning supports an immutable clarify comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-CODEBASE-ANALYST-TERRA` | `G56R-001-OSF-002` | `c2b6a5a56e3cd741d3ad4a04a5c1dbdd3ff6c03839d7330338f1aaa22a8deb5a` | Codebase analysis is everyday reasoning over project files and tool use, matching Terra's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, tool access, exact treatment, and quality remain unproven. |
| `G56R-001-CR-CODEBASE-ANALYST-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured complex coding positioning supports an immutable codebase comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-DOMAIN-RESEARCHER-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Official-source research can be high-value and judgment-heavy, matching Sol's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, official-source access, exact treatment, and quality remain unproven. |
| `G56R-001-CR-DOMAIN-RESEARCHER-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured research positioning supports an immutable domain-research comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Scoped implementation with TDD and remediation can require complex analysis and judgment, matching Sol's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, mutation/tool treatment, and quality remain unproven. |
| `G56R-001-CR-IMPLEMENT-EXECUTOR-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured complex coding positioning supports an immutable implementation comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-PHASE-EXECUTOR-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Running Specify/Plan/Tasks phases is open-ended planning work with judgment, matching Sol's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, phase-skill treatment, and quality remain unproven. |
| `G56R-001-CR-PHASE-EXECUTOR-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured complex knowledge-work positioning supports an immutable phase comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-TERRA` | `G56R-001-OSF-002` | `c2b6a5a56e3cd741d3ad4a04a5c1dbdd3ff6c03839d7330338f1aaa22a8deb5a` | Spec-context analysis is everyday reasoning over project docs and tool-supported reads, matching Terra's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |
| `G56R-001-CR-SPEC-CONTEXT-ANALYST-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured knowledge-work positioning supports an immutable spec-context comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-TERRA` | `G56R-001-OSF-002` | `c2b6a5a56e3cd741d3ad4a04a5c1dbdd3ff6c03839d7330338f1aaa22a8deb5a` | UAT runbook authoring requires everyday reasoning and project-tool context, matching Terra's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-LUNA` | `G56R-001-OSF-003` | `c34327f8653d2545e37d363aac5a1fe0e3c515bcb7bb5772221b616936c62c61` | UAT skeleton rewriting is structured and repeatable, matching Luna's captured positioning. | Runtime supported effort tuple, lifecycle status, runtime availability, and skeleton quality remain unproven. |
| `G56R-001-CR-UAT-RUNBOOK-AUTHOR-GPT55` | `G56R-001-OSF-004` | `2b039a1fe0ac10c3090004fd29aec1af6d761424833d85a5eb4800575f1c87fc` | Current TOML declares `gpt-5.5`; its captured knowledge-work positioning supports an immutable UAT comparator only. | Runtime supported effort tuple, lifecycle status, comparator availability, and exact treatment remain unproven. |
| `G56R-001-CR-CONSENSUS-SYNTHESIZER-SOL` | `G56R-001-OSF-001` | `acb16eadab6ba748e4a508977e229980ecaaf4d87aea405f3732bc452fe2703f` | Consensus synthesis evaluates analyst agreement, evidence, exact edits, and conflict flags; Sol's captured complex/open-ended positioning makes it a source-bound discovery candidate. | Active Codex TOML, runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |
| `G56R-001-CR-GATE-VALIDATOR-LUNA` | `G56R-001-OSF-003` | `c34327f8653d2545e37d363aac5a1fe0e3c515bcb7bb5772221b616936c62c61` | Gate validation is a supplied-command, verbatim-JSON preservation task; Luna's captured clear/repeatable positioning makes it a source-bound discovery candidate. | Active Codex TOML, runtime supported effort tuple, lifecycle status, runtime availability, exact treatment, and quality remain unproven. |

### Shared Effort Surface Records

Candidate rows use `model_reasoning_effort=blocked_pending_model_list_effort`
because executable model/effort tuples must be discovered from the pinned client
before use. The shared effort records below define the only G56R-001 effort
surfaces; they are not global defaults and they do not prove availability.

| `effort_surface_record_id` | Surface | `source_ledger_id` | Setting or field | Documented values | Documented default | Default scope | `runtime_supported_effort_required` | Claim status |
|---|---|---|---|---|---|---|---|---|
| `G56R-001-ESR-001` | Codex model guidance | `OSL-001` | Codex reasoning guidance and model examples | `not_documented_as_value_set` | `not_documented_for_pinned_client` | Documentation guidance only | true | `official_documentation` plus `undocumented_value_set` plus `runtime_verification_needed` |
| `G56R-001-ESR-002` | Codex custom-agent TOML | `OSL-002` | `model_reasoning_effort` optional field | `not_documented_in_snapshot` | `parent_session_inheritance_when_optional_field_omitted` | Custom-agent TOML field scope | true | `official_documentation` plus `undocumented_value_set` plus `runtime_verification_needed` |
| `G56R-001-ESR-003` | Codex config TOML | `OSL-003` | `model_reasoning_effort` config key | `minimal`, `low`, `medium`, `high`, `xhigh` | `managed_model_default_when_omitted` | Config-file and provider-default scope | true | `official_documentation` plus `runtime_verification_needed` |
| `G56R-001-ESR-004` | Codex app-server catalog | `OSL-004` | `supportedReasoningEfforts`, `defaultReasoningEffort` | `runtime_returned_by_model_list_not_captured_in_g56r_001` | `runtime_returned_default_not_captured_in_g56r_001` | Pinned-client app-server model entry | true | `runtime_verification_needed` |
| `G56R-001-ESR-005` | OpenAI API latest-model guidance | `OSL-008` | API reasoning effort and pro-mode guidance | `not_authoritative_for_codex_custom_agent` | `not_documented_for_codex_custom_agent` | API guidance only | true | `official_documentation` plus `api_surface_caveat` |

Each blocked Codex custom-agent candidate row lists its
`effort_surface_record_ids` explicitly. Rows that rely on custom-agent,
config, and app-server effort surfaces bind `G56R-001-ESR-002`,
`G56R-001-ESR-003`, and `G56R-001-ESR-004`. Rows that cite Codex model
guidance bind `G56R-001-ESR-001`; rows that cite latest-model API guidance
also bind `G56R-001-ESR-005` with the API-surface caveat.

Effort surface rules:

- Codex model guidance, custom-agent TOML, config TOML, app-server catalog, and
  API model guidance are separate `effort_surface_records` for blocked model
  candidates.
  Each record carries its `source_ledger_id`, documented setting or field,
  documented values, documented default or `not_documented_for_surface`,
  source-scoped default, `runtime_supported_effort_required=true`, and
  claim status that separates official documentation, undocumented values, API
  surface caveats, and runtime verification needs.
- Default effort from one surface does not establish another surface's default
  unless the official source states that relationship.
- Every blocked model candidate requires G56R-002 to discover
  `supportedReasoningEfforts`, `defaultReasoningEffort`, and effective effort
  for the pinned client before use.
- `gpt-5.6-luna` is source-bound only where the G56R-001 role-contract screen
  records a clear repeatable or concise-helper rationale. Other cross-products
  are not route records in this spike. G56R-002 may add a role/model binding
  only when the model is already in the G56R-001 official-source ledger and the
  added binding records role-contract rationale or an explicit exclusion before
  G56R-003 qualification freezes the executable set.

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

Fixture backlog supplemental fields:

| `fixture_backlog_id` | `agent_contract_id` | Representative input | Owner spec | Invalidation triggers | `non_release_evidence` | `no_payload_created_in_g56r_001` |
|---|---|---|---|---|---|---|
| `G56R-001-FB-CODEBASE-ANALYST` | `G56R-001-AC-CODEBASE-ANALYST` | Answer a code-pattern question from a pinned repository slice | G56R-003 | Role source hash, fixture corpus, scorer, telemetry schema, or capability snapshot change | true | true |
| `G56R-001-FB-DOMAIN-RESEARCHER` | `G56R-001-AC-DOMAIN-RESEARCHER` | Cite official documentation for a model/config claim without project inference | G56R-003 | Official source, citation policy, fixture corpus, telemetry schema, or capability snapshot change | true | true |
| `G56R-001-FB-SPEC-CONTEXT-ANALYST` | `G56R-001-AC-SPEC-CONTEXT-ANALYST` | Resolve a cross-spec consistency question from roadmap and spec files | G56R-003 | Roadmap/spec source, fixture corpus, scorer, telemetry schema, or role hash change | true | true |
| `G56R-001-FB-ANALYZE-EXECUTOR` | `G56R-001-AC-ANALYZE-EXECUTOR` | Remediate seeded Analyze findings and preserve verification evidence | G56R-003 | Fixture repo, marker taxonomy, role hash, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-AUTOPILOT-FAST-HELPER` | `G56R-001-AC-AUTOPILOT-FAST-HELPER` | Summarize an executor result into concise advisory output | G56R-010 | Helper route policy, role hash, latency budget, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-CHECKLIST-EXECUTOR` | `G56R-001-AC-CHECKLIST-EXECUTOR` | Close seeded checklist gaps without weakening requirements | G56R-003 | Checklist taxonomy, marker taxonomy, role hash, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-CLARIFY-EXECUTOR` | `G56R-001-AC-CLARIFY-EXECUTOR` | Produce bounded clarify questions with evidence and no artifact edits | G56R-003 | Clarify protocol, role hash, fixture corpus, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-IMPLEMENT-EXECUTOR` | `G56R-001-AC-IMPLEMENT-EXECUTOR` | Perform a small red-green-refactor task with known acceptance tests | G56R-003 | Fixture repo, test oracle, role hash, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-PHASE-EXECUTOR` | `G56R-001-AC-PHASE-EXECUTOR` | Run a fake Specify/Plan/Tasks command fixture exactly as prompted | G56R-003 | Phase templates, command protocol, role hash, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-UAT-RUNBOOK-AUTHOR` | `G56R-001-AC-UAT-RUNBOOK-AUTHOR` | Rewrite a generated UAT skeleton with known placeholders | G56R-003 | Skeleton generator, acceptance matrix, role hash, scorer, or telemetry schema change | false | true |
| `G56R-001-FB-CONSENSUS-SYNTHESIZER` | `G56R-001-AC-CONSENSUS-SYNTHESIZER` | Synthesize one-, two-, and three-analyst answer sets | G56R-009 | Parity TOML, analyst output schema, consensus rule, scorer, or role hash change | true | true |
| `G56R-001-FB-GATE-VALIDATOR` | `G56R-001-AC-GATE-VALIDATOR` | Run a supplied gate command and return verbatim JSON | G56R-009 | Parity TOML, gate JSON schema, command policy, scorer, or role hash change | true | true |

All fixture backlog records have `non_release_evidence=true` when current Codex
or Claude prompt-emulation evidence exists and
`no_payload_created_in_g56r_001=true`. The two Claude rows remain
`missing_executable_fixture` for Codex because their existing evidence is
project-input prompt emulation, not materialized Codex execution.

Fixture counts:

- Current Codex prompt-emulation fixtures: **3**
- Missing executable fixtures: **9**
- Current Claude prompt-emulation records counted as Codex executable fixtures:
  **0**

## Telemetry Requirements

Every G56R-002 capability or fixture replay must either capture these fields or
classify the field for the pinned surface with this canonical taxonomy:
`stable_native`, `experimental_native`,
`derived_from_controlled_configuration`, `conditional`, `unavailable`,
`not_applicable`, or `undocumented`. Fixture backlog table cells abbreviate
these mandatory fields; this section is the complete telemetry contract for
T027.

| Telemetry field | Required treatment in G56R-002 |
|---|---|
| `assigned_route_id` | Route selected by policy or test assignment before invocation |
| `assigned_model` and `assigned_model_reasoning_effort` | Requested model and effort tuple from the candidate route |
| `effective_route_id` | Matched route after runtime evidence, or null with classification |
| `effective_model` and `effective_model_reasoning_effort` | Runtime-observed model and effort, including reroute or missing-field status |
| `route_match_status` | `matched`, `rerouted`, `missing`, `unavailable`, or `not_observable` |
| `parent_session_id` and `child_agent_id` | Parent-child attribution without storing raw local or sensitive identifiers |
| `instruction_sha256` | Instruction hash used for exact-treatment comparison |
| `loaded_tools`, `loaded_skills`, and `loaded_mcp_servers` | Loaded access surfaces or explicit unavailable classification |
| `sandbox_mode` and `approval_policy` | Effective runtime sandbox and approval treatment or explicit unavailable classification |
| `token_usage` | Input, output, reasoning, cached, and total token fields where exposed |
| `duration_ms` | End-to-end duration for the role invocation or fixture replay |
| `retry_count` | Retry attempts and retry reason classification |
| `terminal_state` | `success`, `failure`, `timeout`, `cancelled`, `blocked`, or `unknown` |
| `terminal_reason` | Human-readable terminal-state reason without sensitive path or account data |
| `missing_field_classification` | One of `stable_native`, `experimental_native`, `derived_from_controlled_configuration`, `conditional`, `unavailable`, `not_applicable`, or `undocumented` |

## G56R-002 Capability And Telemetry Questions

G56R-002 must answer these before any candidate can become executable:

1. Which source-bound blocked candidates appear in `model/list` for the pinned client, with
   `includeHidden` policy declared?
2. Which entries expose `supportedReasoningEfforts`,
   `defaultReasoningEffort`, and `inputModalities`?
3. Which provider capabilities are returned by
   `modelProvider/capabilities/read` for each candidate?
4. Which surface proves requested model, requested effort, effective model,
   effective effort, service reroute when documented, token usage, duration,
   retries, and parent/child attribution?
5. Which telemetry fields are `stable_native`, `experimental_native`,
   `derived_from_controlled_configuration`, `conditional`, `unavailable`,
   `not_applicable`, or `undocumented`?
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

| `traceability_id` | Claim | `claim_location` | `authority_class` | `source_binding` | `dependent_records` | `verification_status` | `invalidation_trigger` |
|---|---|---|---|---|---|---|---|
| `G56R-001-TR-FR-001` | FR-001 report artifact exists | This report path | `project_input` | `G56R-001-PI-001` through `G56R-001-PI-006` | canonical report | verified | report path or feature package changes |
| `G56R-001-TR-FR-002` | FR-002 scope stays documentation-only | Scope and non-goals; changed-file scope guard | `project_input` | `G56R-001-PI-003`, `G56R-001-PI-006` | changed-file scope review | verified | runtime, payload, cache, fixture payload, generated artifact, schema, helper script, or version file changes |
| `G56R-001-TR-FR-003` | FR-003 platform facts use official docs | Official Source Ledger and retrieval evidence | `official_documentation` | `OSL-001` through `OSL-009` | official source records, response hashes, locators, short excerpt anchors, bounded source-fact extracts, and extract hashes | verified | official source content, redirect, or accessibility changes |
| `G56R-001-TR-FR-004` | FR-004 authority classes are explicit | Evidence Classes and Source Ledger | all classes | `OSL-001` through `OSL-009`, `G56R-001-PI-001` through `G56R-001-PI-016` | evidence class table | verified | evidence authority wording changes |
| `G56R-001-TR-FR-005` | FR-005 project inputs are non-authoritative | Project Input Inventory | `project_input` | `G56R-001-PI-001` through `G56R-001-PI-016` | project input records | verified | project input file, payload, cache, or fixture source changes |
| `G56R-001-TR-FR-006` | FR-006 unsupported seeds fail closed | Historical Seed Exclusions and Candidate Routes | `official_documentation`, `undocumented`, `project_input` | `OSL-001` through `OSL-008`; historical inputs have no exact source binding; legacy UAT fallback guidance binds only to `G56R-001-PI-007` and `G56R-001-PI-010` | historical and legacy exclusions, candidate routes | verified | official model lifecycle, model-guidance source, UAT TOML, or installer rewrite-surface changes |
| `G56R-001-TR-FR-007` | FR-007 twelve role contracts exist | Role Contract Records count | `project_input` | `G56R-001-PI-007`, `G56R-001-PI-015` | `G56R-001-AC-*` records | verified | role source file changes |
| `G56R-001-TR-FR-008` | FR-008 role contracts keep runtime facts deferred | Role Boundary, Contract Matrix, and Role Hash Validation Evidence | `project_input`, `runtime_verification_needed` | `G56R-001-AC-*` records | role boundary matrix and complete all-role hash validation | verified | role source, runtime capability, or telemetry schema changes |
| `G56R-001-TR-FR-009` | FR-009 parity roles remain project input only | Parity-only role records | `project_input` | `G56R-001-PI-015` | consensus and gate parity records | verified | Codex parity TOML is added or Claude parity source changes |
| `G56R-001-TR-FR-010` | FR-010 roadmap seed admission is source-bound | Current Roadmap Seed Admission | `official_documentation` | `OSL-001` through `OSL-008` | current roadmap seed table | verified | roadmap seeds or official model docs change |
| `G56R-001-TR-FR-011` | FR-011 provisional routes bind source, effort, lifecycle gaps, and role instruction records | Provisional Candidate Routes | `official_documentation`, `runtime_verification_needed` | `OSL-001` through `OSL-008`, `G56R-001-ESR-*`, `G56R-001-AC-*` | `G56R-001-CR-*` records | verified | source, capability, role, telemetry, or scorer change |
| `G56R-001-TR-FR-012` | FR-012 candidates make no availability or preference claims | Candidate no-claims boundary | `qualification_needed` | candidate status and unsupported-facts fields | `G56R-001-CR-*` records | verified | qualification evidence or fallback policy is introduced |
| `G56R-001-TR-FR-013` | FR-013 twelve fixture backlog records exist | Fixture Backlog Records count | `project_input` | `G56R-001-PI-016` | `G56R-001-FB-*` records | verified | fixture source inventory changes |
| `G56R-001-TR-FR-014` | FR-014 fixture backlog fields are complete | Fixture Backlog Records fields | `project_input`, `runtime_verification_needed` | `G56R-001-FB-*` records | fixture supplemental fields | verified | fixture corpus, scorer, or telemetry requirement changes |
| `G56R-001-TR-FR-015` | FR-015 prompt-emulation evidence is non-release | Fixture non-release evidence label | `project_input` | `G56R-001-PI-016` | fixture backlog records | verified | fixture evidence source changes |
| `G56R-001-TR-FR-016` | FR-016 G56R-002 questions are explicit | G56R-002 capability and telemetry questions | `runtime_verification_needed` | telemetry requirements and capability questions | G56R-002 handoff | verified | client capability or telemetry schema changes |
| `G56R-001-TR-FR-017` | FR-017 traceability matrix is complete | Traceability Matrix | all classes | this traceability table | `G56R-001-TR-*` records | verified | requirement, success criterion, or section mapping changes |
| `G56R-001-TR-FR-018` | FR-018 go/no-go decisions are explicit | Go/No-Go Decision | all classes | `G56R-001-D-*` records | decision matrix | verified | source, capability, fixture, qualification, or installer evidence changes |
| `G56R-001-TR-SC-001` | SC-001 required counts match | Source, role, fixture, and unsupported admitted seed counts | all classes | completeness matrix | all record families | verified | any counted record family changes |
| `G56R-001-TR-SC-002` | SC-002 source bindings and unsupported candidates are fail-closed | Source bindings and unsupported candidates | `official_documentation`, `undocumented`, `project_input` | `OSL-001` through `OSL-009`; historical inputs have no exact source binding; legacy UAT fallback guidance binds only to `G56R-001-PI-007` and `G56R-001-PI-010` | source ledger, historical and legacy exclusions, candidate routes | verified | official source lifecycle, model-positioning, UAT TOML, or installer rewrite-surface changes |
| `G56R-001-TR-SC-003` | SC-003 role contract fields and runtime deferrals are present | Role contract fields and effective-runtime fields | `project_input`, `runtime_verification_needed` | `G56R-001-AC-*` records | role contract records | verified | role source, runtime, or telemetry schema changes |
| `G56R-001-TR-SC-004` | SC-004 fixture backlog counts and labels match | Fixture backlog count and labels | `project_input` | `G56R-001-FB-*` records | fixture backlog records | verified | fixture source inventory changes |
| `G56R-001-TR-SC-005` | SC-005 final decision matrix is complete | Final decision matrix | all classes | `G56R-001-D-*` records | go/no-go decision table | verified | evidence needed by any decision changes |
| `G56R-001-TR-SC-006` | SC-006 marker search is part of verification | Marker search is part of implementation verification | `project_input` | verification evidence | marker search result | verified | marker taxonomy or feature artifact set changes |

## Completeness Matrix

| Record family | Required | Actual | Status |
|---|---:|---:|---|
| `OfficialSourceLedgerRecord` | 9 | 9 | complete |
| Source fact binding rows | 25 | 25 | complete |
| Source fact extract evidence rows | 25 | 25 | complete |
| `EffortSurfaceRecord` | 5 | 5 | complete |
| `ProjectInputRecord` | 16 | 16 | complete |
| `AgentContractRecord` | 12 | 12 | complete |
| `CandidateRouteRecord` | 23 | 23 | complete |
| `FixtureBacklogRecord` | 12 | 12 | complete |
| `TraceabilityRecord` | 24 | 24 | complete |
| `GoNoGoDecision` | 4 | 4 | complete |
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
| Exact count review | Pass; 9 official source records, 25 source fact binding rows, 25 source fact extract rows, 5 effort-surface records, 16 project-input records, 12 role contracts, 23 candidate route records, 12 fixture records, 24 traceability records, 4 go/no-go decisions, 3 current fixtures, 9 missing fixtures |
| Unsupported admitted seed candidates | Pass; 0 |
| Role hash validation | Pass; all 12 instruction and full-file hashes recomputed with documented extraction rules |
| Changed-file scope review | Pass; current branch diff covers 25 documentation/process/test-guard files once the observability checklist is included: the canonical report, G56R-001 feature package, workflow/autopilot state, PRD, roadmap, roadmap MOC, and one unit-test surface guard allowlist; no runtime, agent, installer, payload, cache, fixture payload, generated artifact, schema, helper script, or version change |
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
The branch also carries the G56R-001 feature package, workflow/autopilot state,
the PRD/roadmap/MOC updates needed to connect that package to the roadmap, and
one unit-test guard allowlist for the new Codex research report path.

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

Rollback note: revert the full G56R-001 branch diff: the canonical report,
`specs/g56r-001-candidate-route-baseline/`, `G56R-001-workflow.md`,
`autopilot-state.json`, the PRD/roadmap/MOC edits, and the G56R-001 unit-test
guard allowlist. No runtime behavior is changed.

## Go/No-Go Decision

| `decision_id` | Decision area | Decision | Required evidence | Evidence status | Blocked downstream work | Handoff owner |
|---|---|---|---|---|---|---|
| `G56R-001-D-G56R-002-CAPABILITY` | Proceed to G56R-002 capability discovery and telemetry profiling | `GO` | Source ledger with retrieval evidence, bounded source-fact extracts and extract hashes, explicit effort-surface IDs, documented or explicitly undocumented effort values/defaults, role contracts and instruction hashes with all-role validation evidence, candidate lifecycle gap fields, blocked/source-bound candidate records, fixture backlog, telemetry requirements, capability questions, invalidation rules, and strict authority classes | Complete for a documentation-only discovery handoff; executable model/effort tuples remain blocked pending G56R-002, runtime-supported efforts/defaults remain G56R-002 inputs, and historical seed slugs remain undocumented because no exact lifecycle source text is recorded | none for G56R-002 discovery | G56R-002 |
| `G56R-001-D-EXECUTABLE-CANDIDATES` | Proceed to executable candidate set | `NO-GO` | Pinned-client capability snapshot plus telemetry profile proving effective model, effort, modalities, route, and exact treatment | Missing by design in G56R-001 | executable candidate set, materialized route policy | G56R-002/G56R-003 |
| `G56R-001-D-ROUTE-QUALIFICATION` | Proceed to route qualification | `NO-GO` | Exact treatment, executable fixtures, scorer, analysis plan, and role corpus | Missing by design in G56R-001 | route qualification, ranking, quality claims | G56R-003 and later qualification specs |
| `G56R-001-D-POLICY-INSTALLATION` | Proceed to installer behavior, resolver behavior, preferred route, or fallback policy | `NO-GO` | Qualified preferred routes, fallback routes, resolver contract, installer plan, and payload/update strategy | Missing by design in G56R-001 | installer behavior, resolver behavior, preferred route, fallback policy | G56R-006 and final integration |

Final G56R-001 decision: `GO` for G56R-002 capability discovery only; `NO-GO`
for route qualification, installation, resolver behavior, preferred routes, and
fallback policy.

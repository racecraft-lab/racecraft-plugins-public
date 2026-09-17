# Layer 2 trigger corpus reconciliation

## Scope and result

This is a provider-free audit of the current on-disk Layer 2 trigger corpora. It records no fresh native result and does not authorize corpus deletion. The current source is exactly **105 Claude cases and 112 Codex cases** across 11 shared skill corpora plus the Codex-only `install` corpus.

The supported requirements produce **109 paired canonical trigger cases**. **5 positive native-agent bootstrap requirements covering 8 source cases remain outside Layer 2**; they are recorded as a functional/integration gap instead of being mapped to a fictional Claude skill.

## Decision rules

- `keep`: preserve a distinct prompt or an unresolved active case.
- `merge`: combine only byte-identical prompts that require the same canonical activation. A shared broad category or equal host count is not enough.
- `replace`: replace only the Claude/Codex spelling in explicit smoke prompts with `{{skill}}`; the adapter interpolates the declared native skill string.
- `remove`: unused. No case is removed automatically to hit a count.

Four non-explicit source pairs share an inventory intent/boundary but use materially different prompts (workflow path form, two interview contexts, and two ordinary-work contexts). Both prompt variants remain separate canonical cases and gain a prospective run on the other host. This preserves contextual and negative coverage.

## Counts

| Measure | Count |
|---|---:|
| Current source cases | 217 |
| Claude source cases | 105 |
| Codex source cases | 112 |
| Supported trigger source cases | 209 |
| Functional/integration bootstrap-gap source cases | 8 |
| Proposed paired canonical trigger cases | 109 |
| Bootstrap-gap requirements | 5 |
| Positive self-selection cases | 51 |
| Sibling-routing cases | 45 |
| Contextual/no-SpecKit cases | 13 |
| Keep decisions | 19 |
| Merge decisions | 176 |
| Replace decisions | 22 |
| Remove decisions | 0 |

## Exact duplicate prompts

- **claude** — `install the bundled SpecKit Pro Codex subagents into ~/.codex/agents` appears under `speckit-install`, `speckit-upgrade`. Resolution: `retain-as-unresolved-native-installer-requirement`.
- **claude** — `run autopilot on the SPEC-027 workflow. the file is at docs/ai/specs/027-calendar-sync/SPEC-027-workflow.md. I already filled in all the phase prompts and the constitution is set up` appears under `grill-me`, `speckit-autopilot`. Resolution: `merge-as-one-global-selection-case`.
- **codex** — `install the bundled SpecKit Pro Codex subagents into ~/.codex/agents` appears under `speckit-install`, `speckit-upgrade`. Resolution: `retain-as-unresolved-native-installer-requirement`.
- **codex** — `run autopilot on the SPEC-027 workflow. the file is at docs/ai/specs/027-calendar-sync/SPEC-027-workflow.md. I already filled in all the phase prompts and the constitution is set up` appears under `grill-me`, `speckit-autopilot`. Resolution: `merge-as-one-global-selection-case`.

The autopilot prompt is one global selection obligation: select `speckit-autopilot`, which simultaneously proves the `grill-me` negative. The bundled-agent prompt is correctly rejected by `speckit-install` and `speckit-upgrade`, but its positive behavior is a cross-host native-agent bootstrap gap rather than a Layer 2 Claude skill.

## Mixed-boundary decisions

Historical boundary unions do not decide the expected activation. Each mixed row is resolved from its exact prompt:

| Prompt | Expected | Source cases | Prompt evidence |
|---|---|---|---|
| fix the TypeScript build error in src/tools/primitives/tasks.ts | `none` | l2-394ae629fb36413dd460776e, l2-f533d4d365c59d56f3153fac | The prompt explicitly requests an ordinary TypeScript build fix and names no SpecKit workflow capability. The exact global selection is no SpecKit skill. |
| fix the TypeScript build error in src/tools/primitives/tasks.ts — Zod schema discriminated-union issue | `none` | l2-1e8538a2a71dbd8a2b65b3bd, l2-df67d528746171539e327666 | The prompt explicitly requests an ordinary TypeScript build fix and names no SpecKit workflow capability. The exact global selection is no SpecKit skill. |
| fix the TypeScript build error in src/tools/primitives/tasks.ts — the Zod schema is using z.union instead of z.discriminatedUnion | `none` | l2-6188ff37a582290b933c94a1, l2-80c2c690ece16af5a59c42d4 | The prompt explicitly requests an ordinary TypeScript build fix and names no SpecKit workflow capability. The exact global selection is no SpecKit skill. |
| fix the TypeScript build error in src/tools/primitives/tasks.ts. the Zod schema is failing because I'm using z.union instead of z.discriminatedUnion | `none` | l2-96aeddba6f917945d7668095, l2-cbcd7ac81aae69f1400415c6 | The prompt explicitly requests an ordinary TypeScript build fix and names no SpecKit workflow capability. The exact global selection is no SpecKit skill. |
| walk me through SDD methodology from the beginning — I'm new to spec-driven development | `speckit-coach` | l2-b7bc1bf1232593bcbd509086, l2-edbe91195d94b96acbc97062 | The prompt explicitly asks for an SDD methodology walkthrough; it contains no install, status, or interview request. The exact global selection is speckit-coach. |
| walk me through SDD methodology — I want to understand spec-driven development | `speckit-coach` | l2-1bee9a3d36b9fef8f6afa03b, l2-2cc91a9c020da6ffa0e79401 | The prompt explicitly asks for an SDD methodology walkthrough; it contains no install, status, or interview request. The exact global selection is speckit-coach. |

## Current native-agent availability evidence

- Claude's [subagent documentation](https://code.claude.com/docs/en/subagents) lists a plugin's `agents/` directory as an installed-plugin scope and documents scoped invocation as `speckit-pro:<agent>`.
- Claude's [plugin reference](https://code.claude.com/docs/en/plugins-reference) says plugin agents live under plugin-root `agents/`, appear in `/agents`, and may be invoked automatically or manually. The native tool name is `Agent`.
- Codex's [custom-agent documentation](https://developers.openai.com/codex/subagents) requires standalone TOML files under `.codex/agents/` for project scope or `~/.codex/agents/` for personal scope.
- Current repository source contains 14 Claude Markdown agents under `speckit-pro/agents/` and 12 Codex TOML agents under `speckit-pro/codex-agents/`. These are host-specific rosters, not equal-count parity inputs.
- The current Codex installer reads `speckit-pro/codex-agents/*.toml`; its only destinations are current-project `.codex/agents/` and user `~/.codex/agents/`. Deterministic user-scope tests substitute an isolated fake HOME and do not touch real authentication or configuration.

The Tavily CLI research path returned exit 4 without results, so current official documentation was read through the web fallback. Repository behavior was verified from the current worktree.

## Native-agent availability bootstrap gap

The five remaining positive requirements move to functional/integration design under `native-agent-availability-bootstrap`:

- **Shared outcome:** expose the host's required bundled native-agent roster and prove one canonical role is invokable.
- **Claude:** use the enabled plugin's `agents/*.md` directly; validate the exact required Claude roster and invoke `speckit-pro:<agent>` through `Agent`. No copy/install skill exists or is needed.
- **Codex:** run the existing `install-codex-agents` helper against disposable project `.codex/agents/` or isolated-home `~/.codex/agents/`; verify the exact rendered TOML roster and restart contract.
- **Parity boundary:** compare availability and canonical role invocation, not roster count, source format, destination mechanics, or byte equality across hosts.

TOML-specific deterministic checks retained for Codex: restricted destinations; regular non-symlink source and destination files; required `name`, `description`, and `developer_instructions`; exact roster and rendered-byte/SHA binding; model/reasoning rewrite policy; unrelated-agent preservation; no-clobber publication; fail-closed rollback; and correct `restart_required` behavior.

Existing deterministic coverage:

- `tests/speckit-pro/layer1-structural/validate-payload-contracts.py::ValidatePayloadConformance::test_payload_conformance`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py::ReadOnlyHelperTests::test_validate_agent_install_accepts_valid_external_package`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py::ReadOnlyHelperTests::test_validate_agent_install_rejects_symlink_agent_directory_and_matches_source_roster`
- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py::MutationHelperTests::test_install_codex_agents_refreshes_stale_files_and_preserves_unrelated_agents`
- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py::MutationHelperTests::test_install_codex_agents_defaults_to_fake_user_home_without_touching_real_home`

Proposed deterministic coverage:

- `tests/speckit-pro/unit/test-native-agent-bootstrap-contracts.py::NativeAgentBootstrapTests::test_cross_host_bootstrap_compares_capability_not_equal_roster_or_file_format`
- `tests/speckit-pro/unit/test-native-agent-bootstrap-contracts.py::NativeAgentBootstrapTests::test_claude_enabled_plugin_exposes_exact_required_agent_roster_without_copy`
- `tests/speckit-pro/unit/test-native-agent-bootstrap-contracts.py::NativeAgentBootstrapTests::test_codex_project_and_fake_home_installs_bind_exact_toml_roster`
- `tests/speckit-pro/unit/test-native-agent-bootstrap-contracts.py::NativeAgentBootstrapTests::test_native_agent_invocation_uses_agent_event_and_canonical_role_alias`

## Trigger adapter requirements

1. Stage the exact source description for the declared target and every sibling. Description rewriting changes the selection input and requires a new fingerprint.
2. Claude must observe one completed native `Skill` call and normalize `speckit-pro:<name>` to `<name>`. Prose, a nonce alone, a failed call, multiple selections, or an unknown selection is invalid.
3. Codex must bind a fresh randomized marker to each exact staged `SKILL.md`; selection requires the qualified exact-body read plus that marker. A marker alone, a body read alone, a sibling mismatch, multiple reads/selections, or an unknown marker is invalid.
4. Selection checks use canonical global outcomes: explicitly named sibling-capability prompts require that sibling; contextual/no-SpecKit prompts require no activation; `allowed_extra` is empty.
5. Relative file-backed prompts stage only the declared repository fixture at the same workspace-relative destination. The literal `/path/to/project/...` context remains unfurnished, matching the current selection-only fixture boundary. The proposal never points outside `tests/speckit-pro`.
6. The installed Claude init may advertise `Task`, but current native invocation evidence is named `Agent`. The adapter must normalize the actual event, not grade literal cross-host tool equality.

## Supported per-case coverage matrix

`—` means the prompt is prospectively added to that host; it is not evidence of an existing source occurrence.

| Canonical case | Target | Expected | Claude source | Codex source | Treatment | Prompt |
|---|---|---|---|---|---|---|
| `trigger-02994d935cc99634d588ea00` | `speckit-resolve-pr` | `speckit-autopilot` | l2-9294e4271f55015b3612ab45 | l2-84908096a4acaa4ee60d162e | `merge` | run the autopilot workflow at docs/ai/specs/SPEC-009-workflow.md |
| `trigger-03fc2279e7a57fe89acadf29` | `speckit-status` | `speckit-coach` | l2-eb3cf1e6f26f8f274b8c1001 | l2-357e73414598ec9d926fb601 | `merge` | explain the consensus protocol and how the voting works |
| `trigger-05e61d965d02a5b407ccda03` | `speckit-autopilot` | `grill-me` | l2-942ec5e6b8b77d42daab8f9f | — | `keep` | interview me about the spec for SPEC-009. ask one question at a time with your recommended an... |
| `trigger-08da8654e0828ddaffe99b84` | `speckit-scaffold-spec` | `speckit-resolve-pr` | l2-ed0fb7ddd5c6c304ff8a2b66 | l2-8db2a5446314ffe2980dbb40 | `merge` | resolve the review comments on PR #42 and push the fixes |
| `trigger-0bb1145b4d07ad069f4e0028` | `speckit-autopilot` | `speckit-status` | l2-1414e8a72877471f5f8662bc | l2-81889cea4170331cb68f30d6 | `merge` | what's the status of SPEC-014? I want to see which phases have passed their gates and which a... |
| `trigger-10dc74db5feb932d6654d9df` | `speckit-install` | `none` | l2-df67d528746171539e327666 | l2-1e8538a2a71dbd8a2b65b3bd | `merge` | fix the TypeScript build error in src/tools/primitives/tasks.ts — Zod schema discriminated-un... |
| `trigger-12b385b424a72ddfd4d583d4` | `speckit-prd` | `speckit-prd` | l2-4915f774bc8a859f2e734b89 | l2-792b7d9befee78f86169d7af | `merge` | write a PRD for adding saved searches with email alerts to our app, and the technical roadmap... |
| `trigger-1319831c0a7f85028d1793a5` | `speckit-status` | `speckit-status` | l2-0577cdd5b238a263dd1a9582 | l2-4ae3419a8370afafc55a1d23 | `merge` | show roadmap status for the project and tell me which spec is unblocked next |
| `trigger-133388828e0913843e290c67` | `speckit-upgrade` | `speckit-upgrade` | l2-9b26f845870da81d3facde25 | l2-41b00a0f8451babf666cc8b3 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-136e7be8374c8eabfb1752b2` | `grill-me` | `speckit-coach` | l2-32d3234c40682bd1973fa102 | l2-b8b0390a30a88611ee7b91e7 | `merge` | which checklist domains should I pick for SPEC-012? it's a REST API that handles webhook deli... |
| `trigger-19966920a84848f85e38f0d2` | `ubiquitous-language` | `ubiquitous-language` | l2-3a20171e2a95ffbc911dfa92 | l2-4fe1b3be091cec92e64b201c | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-1b9ada76ac6db90102e10291` | `speckit-resolve-pr` | `speckit-resolve-pr` | l2-fffdae930abdcf3ae7da6aaa | l2-79b8ee44ec3d41441474d908 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-1b9e1f7e5f82102d111c51c6` | `speckit-autopilot` | `speckit-coach` | l2-a0ce776ede5aa77b00b1e2f5 | l2-49ee1454a6e301cb0f365c42 | `merge` | I'm confused about how the consensus protocol works. when does it trigger during a phase and ... |
| `trigger-1bdc59d231599d360e73b30b` | `speckit-scaffold-spec` | `speckit-status` | l2-3180fd546a4cbe98225a8c07 | l2-67b13af62eddf0b9c34d5ac7 | `merge` | show me the current roadmap status and which spec is unblocked next |
| `trigger-1c6ac84faa8b2573c25573b7` | `speckit-scaffold-spec` | `speckit-scaffold-spec` | l2-de6659f46cfce476486433df | l2-be67b597dabc59aa27e1ea35 | `merge` | I need a workflow file generated for SPEC-031 and pushed on its own worktree branch before I ... |
| `trigger-1cd9dc2f978b6254540485ac` | `speckit-resolve-pr` | `speckit-resolve-pr` | l2-a32fd171b86e37cc8f216dab | l2-0cec199292fa7972b59d69ce | `merge` | resolve the review comments on PR #42, push the fixes, and close the open threads |
| `trigger-23321cb1efbe304ce520ee97` | `speckit-upgrade` | `speckit-upgrade` | l2-1985e2823a623ce75edb4722 | l2-acc1cc17015857e89b4f8cab | `merge` | upgrade speckit and migrate this repo from slash-commands mode to skills mode |
| `trigger-23345f5655dc8fac9c6312ca` | `speckit-autopilot` | `speckit-autopilot` | l2-6bcdf22db4fdf2eaed5bda3d | l2-c264bc1707fef5785aa75625 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-2391b29b3591b7ffbecf95f8` | `speckit-coach` | `speckit-coach` | l2-1c2675c60a7f7551d0a4d5d9 | l2-8925772b768380a3272947f0 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-251ab09cb57e068d96df05cb` | `speckit-coach` | `grill-me` | l2-33894900cf23527d5473b114 | — | `keep` | interview me about this raw client brief and walk every branch of the design tree before I co... |
| `trigger-28120982ca4e41b014896e1e` | `speckit-install` | `speckit-install` | l2-c5896af637d360c2d0d29fbf | l2-52c8092ced2ece3f969e98b7 | `merge` | I want to add speckit to this project with both claude and codex integrations side-by-side |
| `trigger-28d06fd9d58ea57d2b0e136e` | `speckit-upgrade` | `speckit-autopilot` | l2-96f13ba82f3e21e2028a4d8f | l2-62c5b811d554de270aa40101 | `merge` | run autopilot on the populated workflow at docs/ai/specs/SPEC-013-workflow.md |
| `trigger-2a7c753298948aae7f5838d0` | `speckit-archive-cleanup` | `speckit-archive-cleanup` | l2-312d9d1633cc770c10c4e416 | l2-9e471625d79fc14bee1b80b0 | `merge` | SPEC-014 merged yesterday, do the post-merge archive hygiene and take it out of active specs |
| `trigger-2bad804e6083cbcbe93b8296` | `speckit-autopilot` | `speckit-autopilot` | l2-deac4e90fde05648eb16cc2b | l2-665006a449adc9210a19664f | `merge` | ok so I've got the workflow file populated for SPEC-013 at docs/ai/specs/SPEC-013-workflow.md... |
| `trigger-2d72b803f8378b25a1fdfc83` | `speckit-scaffold-spec` | `speckit-scaffold-spec` | l2-d16cdf4dc3cb5d1e7257e77e | l2-fb2ccc188771f641da8f4d8c | `merge` | scaffold SPEC-027 from the roadmap and open with a blind spot pass first, so I see the hidden... |
| `trigger-2fb69895060f661db52aeaf3` | `speckit-autopilot` | `speckit-install` | l2-8f8733dcb32a547941b2c8e5 | l2-90d5eb1d0a95870dc25ab2b1 | `merge` | help me set up speckit for a new project. I need to run specify init and configure the consti... |
| `trigger-3001da6b5d801c21ad4a7db2` | `grill-me` | `grill-me` | l2-9b22b8dcb3f8ceb696259334 | l2-99fd0e6d34cc1835dec179d0 | `merge` | grill me on this client brief at docs/idea.md before /speckit-specify — produce a Design Conc... |
| `trigger-3296420403a5cc3d2ccb0542` | `speckit-coach` | `speckit-coach` | l2-2f76b857a02b52d10a584dde | l2-f5cf17edc0e8db71d14cbbd4 | `merge` | Should we use a focused formal model for lease ownership, or do ordinary tests cover it? Expl... |
| `trigger-3347f15829c12a9caaacd330` | `speckit-resolve-pr` | `speckit-status` | l2-4ac6cd0ab215d6cde6dd3b7c | l2-503830fbb7e0d5388a54bdcf | `merge` | show me the current roadmap progress and tell me which spec to start next |
| `trigger-348aa94bd3bcfd9b75fe72fd` | `speckit-status` | `speckit-scaffold-spec` | l2-dd79f823901ee4a40b3e5c0c | l2-512f21d3ca610513814a0558 | `merge` | set up SPEC-009 from the technical roadmap for autopilot |
| `trigger-35ec633ca253c357e76cbb6f` | `speckit-scaffold-spec` | `speckit-scaffold-spec` | l2-f69dde515225196b33f36f4f | l2-1ad3837397aad6254b9cc650 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-3707ed541f9f3b0c68d2344a` | `speckit-install` | `speckit-install` | l2-a4469ad953b9dd67e4f576f5 | l2-29c9a70d81736021cd3e3fc2 | `merge` | initialize this repo for spec-kit, codex integration only with skills mode |
| `trigger-38c851213349afb334e3ab62` | `speckit-upgrade` | `speckit-scaffold-spec` | l2-6a43f8d405b95ee268945440 | l2-338e4fe360ff09302791d438 | `merge` | scaffold spec SPEC-007 for autopilot execution from the technical roadmap |
| `trigger-3a05709b27d4929c3175e5fc` | `speckit-scaffold-spec` | `speckit-scaffold-spec` | l2-343fa4a245154eceb6439a30 | l2-69b0af81d718aa91a09142da | `merge` | set up SPEC-033 on its own branch and then chain straight into planning once I confirm, so it... |
| `trigger-3d2e310415b32e14d9a948d5` | `grill-me` | `none` | l2-96aeddba6f917945d7668095 | l2-cbcd7ac81aae69f1400415c6 | `merge` | fix the TypeScript build error in src/tools/primitives/tasks.ts. the Zod schema is failing be... |
| `trigger-4076ace31599d789e6699a4e` | `ubiquitous-language` | `none` | l2-706dfcf9ffa8f4c4b52ed617 | l2-dee9bf029d72ae98cf8e9692 | `merge` | translate this README into Spanish |
| `trigger-4905df3b0b96d82228137f0e` | `ubiquitous-language` | `none` | l2-b593bfa6a302a758db814c9b | l2-ccb4548c7d8d04cf30fe37bf | `merge` | rename the variable foo to bar across the codebase |
| `trigger-498797f04ec02c32d70bfacc` | `speckit-prd` | `speckit-coach` | l2-128250e86eb1da7d5dda584a | l2-bdf6d15b9b9caa15c16ee7fa | `merge` | I already have a PRD at docs/prd.md — help me decompose it into a technical roadmap and track... |
| `trigger-4ce330a0d8c6803a167df41a` | `speckit-archive-cleanup` | `speckit-status` | l2-d9081866474fe660e42b806f | l2-dc37d91e7ca32b4709aa1e57 | `merge` | which specs are blocked and what phase is SPEC-013 on right now? |
| `trigger-4e569022045a677d135c48a0` | `speckit-coach` | `grill-me` | — | l2-10f06301e7f49540f8ffa382 | `keep` | interview me about the new search feature one question at a time with your recommended answer... |
| `trigger-55e9d0547898af96895671e3` | `grill-me` | `grill-me` | l2-742c3950e60d8c302470d15f | l2-8d4e1d88a73800f5a859a870 | `merge` | play the role of a relentless interviewer for the billing rewrite SpecKit spec — walk every b... |
| `trigger-576283be18009e99fab345d2` | `speckit-status` | `speckit-status` | l2-5ef0a3f38bf2edec9de8e886 | l2-34cd372564fd862738e0a297 | `merge` | status of SPEC-013 please. I need to know which phases are complete and what the next phase is |
| `trigger-5835319891a5b69409e8fbe5` | `speckit-scaffold-spec` | `speckit-scaffold-spec` | l2-f9b778d66e73a37edc74e401 | l2-c65e31ca89497545993faa3a | `merge` | set up SPEC-009 from the technical roadmap so it's ready for autopilot. I need the worktree, ... |
| `trigger-5910f68082a57ee57f050021` | `speckit-archive-cleanup` | `speckit-archive-cleanup` | l2-bf25191a9d3ad7d235c1a1e2 | l2-6e16ad01b274229c4c44ba87 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-5a06389542722cd66ed9ef3a` | `speckit-scaffold-spec` | `none` | l2-d714c484e5bbf90475418772 | l2-1e585e86e80f3f115cce92d3 | `merge` | draft the implementation plan for SPEC-016; the spec already exists |
| `trigger-5bfc77562697bf807f9d9704` | `ubiquitous-language` | `speckit-coach` | l2-3503ea3deadb6824a0c4ad29 | l2-d255cd42f0891be98e7a9b7f | `merge` | walk me through spec-driven development and explain the gates |
| `trigger-5c4e84ead0f46ffac8266e59` | `ubiquitous-language` | `ubiquitous-language` | l2-022b2fb2413679d3b84f1e2f | l2-f551d23b00317af59450a974 | `merge` | run the ubiquitous-language lint on my branch and tell me which new identifiers map to no term |
| `trigger-5ce1a3bd18e5f0191cbb417b` | `speckit-autopilot` | `speckit-autopilot` | — | l2-c44ef84d0fda5f2579fe88b8 | `keep` | I need you to execute the full speckit workflow autonomously. here's the workflow file: docs/... |
| `trigger-5e921de8ff5cd9b6fc49f37f` | `speckit-install` | `speckit-autopilot` | l2-af442b449f2a5464a8c2bd92 | l2-18e4bfad8b0542a6fbaf6fb9 | `merge` | run autopilot on the populated workflow at docs/ai/specs/SPEC-013-workflow.md, all 7 phases w... |
| `trigger-611986640b0f9359c2fe8c6a` | `speckit-status` | `speckit-resolve-pr` | l2-845c85015ecd7e7185c94b34 | l2-e3905d147fc5d5994cc34ed6 | `merge` | fix the review comments on PR #42 and resolve the threads |
| `trigger-639ffc757c0213a367162db4` | `speckit-status` | `speckit-status` | — | l2-3fc2ca229ae8afa5c3e42c69 | `keep` | show the current SpecKit roadmap status and recommend the next unblocked spec |
| `trigger-65228efea0b71b832bc135db` | `speckit-coach` | `none` | l2-4bac3330ea06c209d0d9acb3 | l2-b628ec78f72d568948ac964b | `merge` | review PR #42 on the omnifocus-mcp repo and leave inline comments on any issues you find. foc... |
| `trigger-686c3fc8b620044dce8a1797` | `speckit-prd` | `speckit-prd` | l2-d296681cfbdd724b554429f6 | l2-532856b341322193305258e8 | `merge` | shape this brief into a PRD and decompose it into a SPEC catalog: a team workspace with share... |
| `trigger-69ec7b8bca24d649373cf9bd` | `speckit-upgrade` | `speckit-coach` | l2-2cc91a9c020da6ffa0e79401 | l2-1bee9a3d36b9fef8f6afa03b | `merge` | walk me through SDD methodology — I want to understand spec-driven development |
| `trigger-6cd2fd6d1e6528180c8f19f4` | `ubiquitous-language` | `speckit-scaffold-spec` | l2-b6039a4672c439fd1a4f990e | l2-e984b7b2364a596c91b4c1df | `merge` | scaffold SPEC-004 from the technical roadmap into a worktree |
| `trigger-6f3dcb633c9fef371bf8bae6` | `speckit-upgrade` | `speckit-install` | l2-c18fcc37030d2dd029c6b293 | l2-a8a4a26530c498ecdc764026 | `merge` | install speckit in this empty repo — there is no .specify/ directory yet |
| `trigger-6f7dae8270ec7a4fa401ba42` | `speckit-archive-cleanup` | `none` | l2-4a0f08dc0df2120532be7aab | l2-ff16a427ff3b7012ad270b08 | `merge` | prune the local git branches that have already been merged into main |
| `trigger-7915f1228cdb65fe9cdd7d1d` | `speckit-scaffold-spec` | `speckit-autopilot` | l2-9a47fff73fc662c9084b3406 | l2-3089e8c2ac8e7ad72b47e08b | `merge` | run the fully populated workflow at docs/ai/specs/SPEC-009-workflow.md through all 7 phases |
| `trigger-7c5dcadc4763ad1084e0f506` | `speckit-scaffold-spec` | `none` | l2-305e6c2f18cd2d68ce6ca795 | l2-c4cccbbe481c35505ced5a55 | `merge` | SPEC-016 already has a committed workflow file with every prompt filled in, so resume it at t... |
| `trigger-7d6279d0128e1e9672c76e6b` | `speckit-coach` | `none` | l2-e7f990454c5db6aa817152fa | — | `keep` | set up biome linting for the project. I need to configure the rules for TypeScript strict mod... |
| `trigger-7d8fc78c7eb1154f56f78a6b` | `speckit-coach` | `speckit-coach` | l2-baff0f64e306ae33f07aebff | l2-c69bffdb11501c3400d9e94a | `merge` | I'm starting a new project and want to use SDD. can you walk me through the methodology from ... |
| `trigger-8774ac8aa8a84459cdf11011` | `speckit-status` | `speckit-status` | l2-cf921b173c4c1bf519a67274 | l2-110b872a4d27082146664b76 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-883c82ed415cb2007a1d4268` | `speckit-archive-cleanup` | `speckit-archive-cleanup` | l2-63436076e87c62fd3fbb048e | l2-958e6801d124c42c55d2a215 | `merge` | prepare the cleanup branch and cleanup PR that archives SPEC-022 after merge |
| `trigger-8aaa622ee627d02c7c0947bf` | `speckit-autopilot` | `grill-me` | — | l2-b77a90eb7cda6924e3f79b02 | `keep` | interview me about the spec for SPEC-009 — I want to walk every branch of the design tree bef... |
| `trigger-8b66e33f54b4993f86fa0696` | `speckit-resolve-pr` | `speckit-scaffold-spec` | l2-996e4dda8f9ad105447b7fa1 | l2-6042e8c29601a158147140ed | `merge` | set up SPEC-009 so it's ready for autopilot |
| `trigger-8c0e6e3246c4a96e1e683c81` | `speckit-resolve-pr` | `speckit-coach` | l2-204dad69b45b20b6dde6c1c3 | l2-2f389b4626016123fac45fa0 | `merge` | walk me through how SpecKit clarify works |
| `trigger-912080def238d36b8c5a4d55` | `speckit-coach` | `speckit-resolve-pr` | l2-9205270bf43c3a9380062e33 | l2-6678b0e0e63de4c6383b1094 | `merge` | can you resolve the review threads on PR #38? the reviewer approved but the threads are still... |
| `trigger-92d0f4ceb1884200781d30a7` | `speckit-scaffold-spec` | `speckit-scaffold-spec` | — | l2-96b9371f287bc51e055188b9 | `keep` | set up SPEC-009 in a worktree and populate the workflow template |
| `trigger-9ce1103640d2476f97d49d9e` | `speckit-install` | `speckit-install` | l2-6cc906ad83b89e9f38b58396 | l2-da508e7d2efc38262d0d0b6d | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-a16afa059f6e95f5a0c41d80` | `speckit-archive-cleanup` | `speckit-autopilot` | l2-9e5a1c796896e34f2bb511b5 | l2-1670d8dad9a06fb37ac71295 | `merge` | run autopilot for SPEC-018 and let its startup sweep handle whatever it finds |
| `trigger-a1ae0bd7524e6f63f18495bd` | `ubiquitous-language` | `grill-me` | l2-3c0af3ed67b3bfb98c99419d | l2-44dbf53c5bab671cae8c2054 | `merge` | grill me on SPEC-012 before /speckit-specify and produce a design concept doc |
| `trigger-a393fef41441c43d191ac73e` | `speckit-upgrade` | `speckit-upgrade` | l2-d8ec3f8d78d8af7428b77e6d | l2-66b3c5127dd316e340669bf7 | `merge` | run specify integration upgrade for both claude and codex — preserve my customizations |
| `trigger-a43386f3ac6ee9d4c2c1bf7a` | `ubiquitous-language` | `ubiquitous-language` | l2-25291e60ffad5482c1ddb978 | l2-abf679658f467ef1a95c52e6 | `merge` | define the domain terms for this repo in a glossary the agents can read before designing |
| `trigger-a70f7c5cb2cfe5466f33f51f` | `speckit-coach` | `speckit-coach` | l2-54153abe183c78292b6899e4 | l2-081bc9106d8ac988226669e8 | `merge` | how is the roadmap home note / Map of Content structured? I want to understand the curated ep... |
| `trigger-a76c1c9592d887102c84da58` | `speckit-upgrade` | `speckit-upgrade` | l2-f1b4e1f49201ab7a96bf966c | l2-9e6ecd969eb83a5cc6c613ac | `merge` | the spec-kit upgrade is blocked because of modified files — help me upgrade safely with my co... |
| `trigger-aa20a4a5d157193dcfa63107` | `speckit-prd` | `speckit-autopilot` | l2-dbd346d2aa33919dbe697e4b | l2-a0abe09f1e81cdb4084353dd | `merge` | run autopilot on the SPEC-027 workflow at docs/ai/specs/SPEC-027-workflow.md — all phase prom... |
| `trigger-aa66198702152608dbeb5c03` | `speckit-resolve-pr` | `speckit-resolve-pr` | l2-7f5ef95781eb41dfa1db939c | l2-7251c588e50d605c4d5da1b7 | `merge` | address all unresolved feedback on https://github.com/owner/repo/pull/46 and mark the review ... |
| `trigger-ab0902030aa45f353985dab6` | `speckit-resolve-pr` | `speckit-resolve-pr` | l2-859dc0c6738e8c654ee107c8 | l2-fdda5f764e2af5119a70b96b | `merge` | I need you to fix the code review comments on the current pull request branch and reply to ea... |
| `trigger-b2e356ed805c22ce9faaa03c` | `speckit-archive-cleanup` | `speckit-resolve-pr` | l2-aef99016cc6f188150546516 | l2-bd3e11028db5388aeed59227 | `merge` | fix the review comments on PR #42 and resolve the open threads |
| `trigger-b3579d291466ee6ff3a70ed4` | `speckit-status` | `speckit-status` | l2-2ff57a86cbe887aa50d95a88 | l2-7ccff2b4273a86f2318f8176 | `merge` | list all active worktrees and which specs they belong to |
| `trigger-b480f98385810b675a7d7328` | `speckit-archive-cleanup` | `speckit-scaffold-spec` | l2-52b8592c37420e6b103b4e40 | l2-08103839ebaee58c4c65b566 | `merge` | set up SPEC-020 from the technical roadmap with a worktree and a workflow file |
| `trigger-b8e539ffa169040324f2dd14` | `speckit-autopilot` | `speckit-autopilot` | — | l2-7cc53b28d037b0d8ae31e8b0 | `keep` | run the autopilot workflow at docs/ai/specs/SPEC-013-workflow.md |
| `trigger-cb2ca3477dbb49635b55a8a1` | `grill-me` | `grill-me` | l2-f1ffa5c23fc9213d95381e49 | l2-90ac903af1c695c70759fbf9 | `merge` | run grill-me on this raw idea: a leaderboard for the learning platform. produce a Design Conc... |
| `trigger-cc32e5bde77a65515009d57b` | `speckit-autopilot` | `speckit-autopilot` | l2-39fc68a2eb3012f182f728f1, l2-9b4e683836adee31dda13f87 | l2-c0ab0ac893d7515042e07330, l2-d15790b321fa6253739d851f | `merge` | run autopilot on the SPEC-027 workflow. the file is at docs/ai/specs/027-calendar-sync/SPEC-0... |
| `trigger-cd2f928a871c0c96ee1abe7f` | `speckit-autopilot` | `speckit-autopilot` | l2-7e52036a70518ffd85719a02 | — | `keep` | I need you to execute the full speckit workflow autonomously. here's the workflow file: /path... |
| `trigger-d0302d714103b6b0444567cb` | `speckit-coach` | `speckit-coach` | l2-963d9e2d42352a31a6ab6f6f | l2-ac3d5448153065c9d041e106 | `merge` | I want to install the archive extension and wire it up so it runs automatically after every i... |
| `trigger-d0452d69766f2e8aa0d6522d` | `speckit-upgrade` | `none` | l2-394ae629fb36413dd460776e | l2-f533d4d365c59d56f3153fac | `merge` | fix the TypeScript build error in src/tools/primitives/tasks.ts |
| `trigger-d07bb7c5e0753a51a1de883c` | `speckit-coach` | `none` | — | l2-ab33d6130982a0642d5e9c4d | `keep` | what's the current git status? I want to see if there are any uncommitted changes before I st... |
| `trigger-d287c9fcc9981dd6c7ca70bc` | `grill-me` | `grill-me` | l2-087eabc01a9e54929b82bcde | l2-25e14f3512a3184792beea92 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-d3b3cf33b5d943ef47319b71` | `speckit-coach` | `speckit-autopilot` | l2-ad1d95c2e404fc99786372b2 | l2-f59147c3988760c18cf94ba0 | `merge` | Run the selected formal checks and resume the autopilot workflow from its planning checkpoint... |
| `trigger-d505cfa966cfa08b9b79df4b` | `speckit-archive-cleanup` | `speckit-archive-cleanup` | l2-0c40c659068bddbb0b69a314 | l2-2b1d01a1c11861992cee1556 | `merge` | write the archive report for SPEC-914 with the merge commit, merged-at timestamp, and recover... |
| `trigger-d564cc7e6b4bed42da08b894` | `grill-me` | `speckit-scaffold-spec` | l2-c1beb8ee156c98997c512253 | l2-aa3d1ee50d96b898f58d7825 | `merge` | set up SPEC-018 for me — read the technical roadmap, create a worktree, populate the workflow... |
| `trigger-da0f4b8d0e748247e2589578` | `speckit-autopilot` | `none` | l2-af00346e565cc52ea9ce040d | l2-f714040c928fadaabb26eab2 | `merge` | write a unit test for the createTask primitive. it should mock executeOmniJS and verify the s... |
| `trigger-db76a6b923465280e8ff4685` | `speckit-install` | `speckit-coach` | l2-b7bc1bf1232593bcbd509086 | l2-edbe91195d94b96acbc97062 | `merge` | walk me through SDD methodology from the beginning — I'm new to spec-driven development |
| `trigger-dc54edd8147603922e017a1b` | `speckit-install` | `speckit-install` | l2-900dbdddad794aa7df8e962e | l2-932a81115e8b0e7910e74106 | `merge` | set up the SpecKit CLI and initialize this project for Claude Code integration |
| `trigger-ddc70f20d18a7665b0d0a20c` | `speckit-prd` | `speckit-status` | l2-a9dc0ca3e065197d44eebe9a | l2-15920842a9ff5c1f0746c60d | `merge` | where am I in the workflow and what's the next pending spec I should work on? |
| `trigger-de94f9b6c2a27b5e6e96b1e1` | `ubiquitous-language` | `ubiquitous-language` | l2-22775a4987fcc9018971ac9d | l2-c8052075dd354dd01ea39350 | `merge` | our spec says 'account' but the code says 'tenant'; pin the terms and reconcile the names |
| `trigger-e1eade1a2187f76d2f360133` | `speckit-coach` | `speckit-coach` | l2-affe83e821f3124596f7dc53 | l2-d5c5adeb37f861408bef8df5 | `merge` | can you run the coach and fix up this existing speckit-pro project so our template customizat... |
| `trigger-e34e1de0b6a65d17e8b23d91` | `speckit-install` | `speckit-scaffold-spec` | l2-0a1fc6035097d93abfdc713f | l2-c8c663381af2a110e0e5b211 | `merge` | scaffold spec SPEC-009 from the technical roadmap so it's ready for autopilot |
| `trigger-e553d0bddc24dc014efff37a` | `speckit-prd` | `none` | l2-80c2c690ece16af5a59c42d4 | l2-6188ff37a582290b933c94a1 | `merge` | fix the TypeScript build error in src/tools/primitives/tasks.ts — the Zod schema is using z.u... |
| `trigger-e6bd6d523668bb7d11859a93` | `speckit-scaffold-spec` | `speckit-coach` | l2-21bba56ea72d2e3cdd830723 | l2-ad09a631ff8f30136bf51201 | `merge` | walk me through Spec-Driven Development from scratch |
| `trigger-ec0518e8787ab9ab1b0a8a1e` | `speckit-prd` | `grill-me` | l2-455a508685648795f9f32b25 | l2-9571304897a20e7b32fcc9f6 | `merge` | grill me on SPEC-012 before /speckit-specify — produce a design concept doc by walking the de... |
| `trigger-f2a2a3ba77bf704565b624bc` | `speckit-prd` | `speckit-prd` | l2-5454be96cf5aae55a8a0e754 | l2-2134062a79a778106d45f817 | `merge` | create a product requirements document for a referral program, then decompose it into a SPEC ... |
| `trigger-f4ffe47318e2c13c4fb2d4c4` | `speckit-prd` | `speckit-scaffold-spec` | l2-7249dfe045878b493906b5ff | l2-144291b4af4d5fe2bd29cd6e | `merge` | set up SPEC-018 for me — read the technical roadmap, create a worktree, populate the workflow... |
| `trigger-fa501e72cab4020cdc7b274f` | `ubiquitous-language` | `speckit-prd` | l2-964bfd3fb0e315e88acd2bfb | l2-3669862b5d846a38792614ae | `merge` | write a PRD for adding saved searches with email alerts and the technical roadmap to build it |
| `trigger-fc9e7158bdb4fe47f2801f3f` | `speckit-prd` | `speckit-prd` | l2-e010ebb45018ac5d5b6ae2e0 | l2-2f8712b4cfaa1214a0da0954 | `replace` | Please use the {{skill}} skill for its documented purpose in this repository. |
| `trigger-fcc898a39fac01823c7db6b0` | `speckit-status` | `speckit-autopilot` | l2-83e2dd130e6878386fe6474b | l2-a3226468c307a07e8fbd7421 | `merge` | run the workflow at docs/ai/specs/SPEC-013-workflow.md through all 7 phases |
| `trigger-fe03f9ba982c3c71559d6dcc` | `speckit-autopilot` | `speckit-resolve-pr` | l2-1ae87ba8e1fb8f4665f3598f | l2-b4153617efea0595682c3823 | `merge` | can you review the PR for SPEC-008 and resolve the review threads? the PR number is #42 on th... |
| `trigger-ffcecbb52c467e3e3de92dba` | `speckit-install` | `speckit-upgrade` | l2-30b5179c2365bad417354829 | l2-8263daf18f853a7e21b5fa9b | `merge` | upgrade my existing speckit installation from 0.6.1 to the latest 0.8.13 |

## Functional/integration gap provenance

| Requirement | Expected capability | Claude source | Codex source | Prompt |
|---|---|---|---|---|
| `trigger-unresolved-320e4ad27e58b004c93c1bc7` | `native-agent-availability-bootstrap` | l2-1b43ca2d753dec02b20c5e17, l2-e76897ec42591baaf72a123b | l2-16c455c0a4f2da6c3070aaee, l2-1b79461d58e7889e96bae039 | install the bundled SpecKit Pro Codex subagents into ~/.codex/agents |
| `trigger-unresolved-76bb97e51930577fdba31890` | `native-agent-availability-bootstrap` | — | l2-b17609d6e21200d9d5f902e9 | Invoke the host-native agent-installer capability for its documented purpose. |
| `trigger-unresolved-8dbf3e9ae65d8cbaa3464fbc` | `native-agent-availability-bootstrap` | — | l2-e6d7dd4396cbae9b4152e502 | install the bundled SpecKit Pro Codex subagents into my user-scope Codex config and tell me if I need to restart |
| `trigger-unresolved-8ee949e37342f6ca4e5896b9` | `native-agent-availability-bootstrap` | — | l2-a22017765ee84d8405ead810 | refresh the SpecKit custom agents in ~/.codex/agents because autopilot says the subagents are missing |
| `trigger-unresolved-d113bff02054c64fe2e33485` | `native-agent-availability-bootstrap` | — | l2-be010e07dcad628021134fd7 | copy the plugin's Codex TOML subagents into ~/.codex/agents and verify what got installed |

All gap entries remain in the current Layer 2 corpora. The trigger proposal intentionally excludes their positive installer mechanics and makes no functional, integration, or native qualification claim.

## Outputs and status

- `trigger-inventory.json` is the full 217-row source audit with stable IDs, positions, prompt-grounded decisions, counterpart status, and coverage mappings.
- `/private/tmp/speckit-trigger-catalog-proposal.json` is a non-active proposal containing only supported paired trigger cases.
- Native execution, provider qualification, implementation of the bootstrap gap, semantic acceptance of prospective cross-host prompts, and active-catalog integration are pending.

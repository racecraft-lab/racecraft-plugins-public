# Portable human plan approval: feasibility and plan-review blueprint

> Status: research complete; native-only provenance is not established. A trust-boundary decision is required before the health-program spec can claim portable human approval is feasible.
> Researched: 2026-10-02. Repository baseline: `f07596d35569c64cdafc482c6ac8ea57904e13e4`.
> Scope: design and source/documentation research only. No shipped skill, runner change, host trust change, private transcript export or live model evaluation.
> Research ticket: [Research: verify portable human plan-approval provenance on both hosts](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1032). Accepted decision: [ADR 0013](../../adr/0013-plan-approval-record.md), following [Plan approval record](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1014).

## Finding and decision boundary

The interview and content-binding workflow can be specified as a runner-policy blueprint; end-to-end implementation feasibility is not established by this research. The missing piece is a **trusted, independently verifiable capture of the actual human decision**, including the separate dispositions of remaining findings. Neither ordinary Claude Code question responses nor Codex app-server question responses establish that authority. They carry useful correlation identifiers and application-supplied content. A transcript hash protects bytes against an expected digest; it does not identify their author.

Codex does have an important experimental primitive: `userVerification/verify` signs a challenge through a macOS Secure Enclave key protected by biometric access. It exists in the inspected official 0.156.0 release and the installed CLI's generated experimental schema. This is stronger than an agent-accessible software key. It still does not, by itself, attest the interview, the final plan, a particular named human, the displayed approval intent, or a trusted key enrollment. Its calling UI and verifier own those bindings. The native elicitation capability is restricted to the host-owned plugin service; a configured third-party MCP server cannot acquire it. There is no established supported plugin path that completes this design on Claude Code and Codex alike. See the source evidence below.

**Disposition for the health-program spec:** retain ADR 0013 without weakening it. Mark approval provenance/cross-host admission as a feasibility gate awaiting the choices in the final section. Do not claim that a session locator, `role=user`, `origin.kind=human`, `approved=true`, authenticated CLI account, Git commit or locally generated signature satisfies that gate. Until an approved capture profile is implemented and qualified on both hosts, implement admission must refuse unverifiable records. Research can close with this documented capability gap; it cannot close the implementation's acceptance gate.

## Evidence method and limits

Labels used here:

| Label | Meaning |
| --- | --- |
| Documented | Current first-party documentation states the behavior. |
| Source-inspected | Public first-party implementation or test definition was inspected at a pinned revision; it was not executed merely by being read. |
| Safely tested | A bounded local command actually ran, without models, real interview answers or private evidence. |
| Proposed | A design for the health program, requiring implementation and qualification. |
| Unverified | Documentation, inspected source or bounded tests do not establish the claim. |

Context7 was resolved and queried for `/openai/codex` and `/websites/code_claude_en_agent-sdk`; its results were followed to first-party pages and pinned source. Public source was fetched into a temporary cache. The repository owners were located with ripwire before targeted inspection. No actual session store, transcript, credential, account identifier or private approval was opened. No biometric prompt, enrollment, key deletion, native verification RPC, paid model request or SpecKit workflow was launched. The CLI schema generator does not prove a device has a usable credential or that this desktop build implements a compatible verification UI.

Inspected upstream revisions:

- Codex current public source: `ca466061d64f0b44f416135c7fd06aa7af850bbc`.
- Codex official release `rust-v0.156.0`: `fe74a774532af67b5a4a3dec03ce9469e17f89af`, published 2026-09-22, not marked prerelease in release metadata. The native provider, native platform selector, key-protection implementation and verification protocol files were byte-identical to inspected current source. This establishes release inclusion, not production stability of an experimental API. [Release](https://github.com/openai/codex/releases/tag/rust-v0.156.0).
- Claude Agent SDK Python public source: `bfb895c6ef46e095191938b4eda798a025957c09`. This is source evidence, not a claim that the user's installed Claude runtime is that revision. Claude Code's complete native interactive UI was not source-audited.

## Host capability findings

### Ordinary questions and user messages

| Surface | Available identity/correlation | What it establishes | What it does not establish |
| --- | --- | --- | --- |
| Codex app-server `item/tool/requestUserInput` | JSON-RPC request, thread, turn, item and question IDs; answers map | An application replied to a pending request. `serverRequest/resolved` also occurs on cleanup, so resolution alone is not an affirmative reply. | A real human answered, understood or approved a particular bundle. The general client protocol may clear or automatically resolve pending questions. |
| Codex ordinary `turn/start` / `userMessage` | Thread/turn/item identity and caller-supplied input | Transported conversation input. | Human authorship or portable account-to-human attestation. A client can submit text programmatically. |
| Claude Agent SDK `AskUserQuestion` | Control request and `tool_use_id`; question text/answers in `updatedInput` | The SDK callback returned an allow/deny result and supplied answer content. | The callback actually consulted a human. It is developer code, and can return literal answers. |
| Claude ordinary SDK user message | Message identifier, optional parent tool ID and origin | Conversation role and routing provenance. | Physical human input. Current Python SDK explicitly permits the SDK host to stamp `origin: {kind: human}` itself. |
| Claude `UserPromptSubmit` / `PostToolUse` / elicitation hooks | Session/prompt/tool context and transcript reference; event-specific payload | Hook observation at a lifecycle boundary. | Cryptographic author identity or an immutable original answer. Elicitation hooks can respond without a dialog; ElicitationResult hooks can replace the response. |

**Documented:** the [Codex app-server page](https://learn.chatgpt.com/docs/app-server#toolrequestuserinput) describes request cleanup and optional automatic resolution; its [items and skills sections](https://learn.chatgpt.com/docs/app-server#items) describe conversation items and client invocation. These are transport semantics, not a human-attestation contract.

**Source-inspected:** [Codex outgoing callbacks, lines 561–590](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/app-server/src/outgoing_message.rs#L561) enforce special owner/identity checks only for verification callbacks. Ordinary callback removal correlates and consumes a response; it is not a signature check. [Its question integration test](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/app-server/tests/suite/v2/request_user_input.rs) supplies answers through a test client. [The question handler, lines 78–140](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/core/src/tools/handlers/request_user_input.rs#L78) stores received answers under a `VerifiedAnswer` type in one feature path; that name must not be mistaken for an exported human-identity signature.

**Documented:** [Claude SDK user input](https://code.claude.com/docs/en/agent-sdk/user-input#handle-clarifying-questions) places answer collection in the application and returns it as updated tool input. [Claude hooks](https://code.claude.com/docs/en/hooks#elicitation) explicitly allow programmatic elicitation responses and response modification. A hook's trusted placement can be part of a custom capture system, but these events provide no documented portable signed human approval.

**Source-inspected:** [SDK callback handling, lines 586–638](https://github.com/anthropics/claude-agent-sdk-python/blob/bfb895c6ef46e095191938b4eda798a025957c09/src/claude_agent_sdk/_internal/query.py#L586) serializes the callback's supplied `updated_input`; [message origin, lines 1101–1135](https://github.com/anthropics/claude-agent-sdk-python/blob/bfb895c6ef46e095191938b4eda798a025957c09/src/claude_agent_sdk/types.py#L1101) explicitly describes caller-stamped human origin. Neither is an independent proof of an interview response.

### Codex native verification: useful primitive, incomplete solution

**Documented in pinned first-party source:** [app-server README, lines 123–187](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/app-server/README.md#L123) describes experimental status/enroll/delete/verify/cancel. Enrollment returns a credential identifier, optional algorithm and public key; it is local key creation, not backend registration. The trusted UI owns registration and backend revocation. Verify accepts a caller's challenge, title and description and returns a signature. Supported local UI connections differ from network peers, which need their own authenticator. Display approval and pending-request checks belong to the caller; late proofs must be discarded.

The following limits are **source-inspected**, not live biometric results:

| Property | Inspected behavior | Consequence for plan approval |
| --- | --- | --- |
| Platform/build/account | [Native selector, lines 61–89](https://github.com/openai/codex/blob/fe74a774532af67b5a4a3dec03ce9469e17f89af/codex-rs/user-verification/src/lib.rs#L61) selects macOS; others use an unsupported provider. [Service, lines 63–108 and 130–132](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/app-server/src/user_verification.rs#L63) captures cached ChatGPT account-user identity and checks connection/auth changes. | API presence is insufficient; supported hardware, enrollment, account identity, entitlements and compatible UI remain prerequisites. No API-key-only, Linux or Windows native capture was established. |
| Hardware/key custody | [Provider, lines 146–206 and 264–288](https://github.com/openai/codex/blob/fe74a774532af67b5a4a3dec03ce9469e17f89af/codex-rs/user-verification/src/platform_macos/provider.rs#L146) uses a fresh biometric context, Secure Enclave P-256 key and exact challenge bytes; exports the public key. | A model reading a software private-key file is not the intended path. Non-exportability alone does not guarantee the caller displays the correct plan or cannot request a misleading signature. |
| Biometric policy | [Key protection, lines 22–35](https://github.com/openai/codex/blob/fe74a774532af67b5a4a3dec03ce9469e17f89af/codex-rs/user-verification/src/platform_macos/key_protection.rs#L22) uses `BiometryAny` and private-key usage. Reuse checks assume the entitled namespace was created under that policy; they do not revalidate the opaque access-control policy. | The assurance depends on trusted application/keychain access. It is not a certificate identifying a configured reviewer or proving every reused key's policy to another host. |
| Signature scope | [Protocol, lines 112–154](https://github.com/openai/codex/blob/fe74a774532af67b5a4a3dec03ce9469e17f89af/codex-rs/app-server-protocol/src/protocol/v2/user_verification.rs#L112) defines challenge signing independent of pending elicitation. | Plan intent, finding dispositions, revision and display digest must be in a verifier-controlled challenge. Title/description are display context, not separately signed fields unless included in that challenge. |
| Elicitation eligibility | [Initializer, lines 105–149](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/app-server/src/request_processors/initialize_processor.rs#L105) projects verification for supported bundled TUI/local Desktop cases. [Configured-server test, lines 68–86 and 132–156](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/core/tests/suite/mcp_user_verification.rs#L68) specifies refusal for configured MCP servers even with explicit extension declarations. | A third-party SpecKit MCP helper cannot assume native verification elicitation is available. Direct local UI RPC integration is a separate custom integration and trust decision. Renaming a server/client is not an authority solution. |
| Proof verification | [MCP response validation, lines 54–77](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/rmcp-client/src/user_verification.rs#L54) checks bounded proof shape/encoding. | This is not signature verification, identity enrollment or consumption of a plan-review challenge. The trusted verifier must do those. |
| Completion/cancellation | [TUI coordination, lines 24–120](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/tui/src/app/user_verification.rs#L24) associates local attempts, rejects late proofs and cancels unavailable verification. | An interrupted review cannot reuse a late proof for a new question or revision. No fallback to ordinary answers is acceptable. |

Apple's [Secure Enclave guidance](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave) describes non-exportable private-key operations. Its [BiometryAny definition](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags/biometryany) allows any enrolled finger and remains accessible when enrollment changes. **Inference:** a valid signature proves possession/use of the enrolled credential under its assumed protection, not which named person supplied a finger or their understanding of the interview. Human identity needs an independently trusted enrollment mapping and an explicit policy for shared devices/accounts.

Codex also has a separate [upstream request-attestation integration](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/core/src/attestation.rs#L12). It supplies an upstream request header via a host-owned provider. It is not a documented plan-review receipt or a substitute for the native challenge proof. Model account authentication, transport authentication and action-security approvals must likewise stay separate from plan approval.

### Persistence and portability

**Documented:** [Claude SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions#resume-across-hosts) can move or mirror session history, or pass application state to a fresh session. This transports context; it does not authenticate its human author. Codex's [app-server thread lifecycle](https://learn.chatgpt.com/docs/app-server) provides persisted thread operations. Neither history export is a shared Claude/Codex approval authority.

**Inference from the inspected shapes:** P-256 signature bytes, exact challenge bytes and SPKI public metadata can be verified cryptographically without the originating session. A self-supplied public key still permits a fabricated key/approval pair. The receiver additionally needs a trusted enrollment/certificate binding, approved capture assurance, decision scope and current withdrawal/supersession status. The inspected Codex enrollment/proof responses do not carry all those attestations. Native source test definitions show signature verification for exact challenge bytes; no full portable human-review integration was executed.

A private transcript locator is an audit reference, not the trust root. The other host must be able to verify a redacted attestation independently without reading protected raw evidence. If the only alleged proof requires unavailable raw history, refuse admission. If a qualified trusted capture service attests the original event and preserves it privately, receivers may verify its signed public receipt without downloading the original; that is a **proposed new trust model**, not native transcript authority. Loss of private originals must be represented by that service's retention/status contract, never silently concealed.

## Proposed trusted capture profile

This is the smallest complete authority design identified, **conditional on human approval of new trust assumptions**. It is not shipped or demonstrated native functionality.

1. A trusted UI/control plane outside the implement agent's write/sign authority loads a runner-constructed review snapshot. It authenticates an authorized human under a reviewed enrollment policy. It renders the canonical scope, finding evidence and exact decision choices itself. Agent prose can help explain; it cannot choose a hidden bundle, change a displayed approval or supply authoritative answers.
2. It captures each actual interview response at the input boundary, before ordinary SDK/tool-result transformation. Each event binds review generation, question/finding identity, current revision, response, origin and protected audit reference. A scripted SDK reply, hook replacement, peer message, scheduler prompt or agent-submitted approval is rejected as an authority event.
3. For final confirmation it derives a domain-separated challenge containing repository/feature identity, review generation, complete planning-manifest digest, reviewed-evidence digest, explicit approval decision, digest of the complete per-finding disposition set, approval-policy version and fresh single-use nonce. It also binds the exact confirmation presentation or its deterministic digest. An interview event manifest links all dispositions and the final decision to the same revision.
4. A qualified human authenticator or isolated capture signer produces evidence only after explicit human confirmation. Native Codex biometric signing might be one adapter if supported UI integration and independent enrollment are solved. A shared external authenticator/control plane is the alternative proposal for Claude and Codex. A signer key or signing endpoint usable by an agent without verified human interaction cannot satisfy this profile.
5. The trusted verifier authenticates enrollment, validates the proof over the exact challenge, enforces authorized reviewer/repository scope, rejects replay and canceled generations, and records an immutable approval issuance. It returns a redacted, signed receipt with provenance and event-manifest bindings. The runner validates this receipt and rechecks current inputs before writing the canonical committed approval record.
6. Both hosts validate the same receipt against an independently installed/pinned trust root and current signed status. A key included only in the editable record is not a trust root. The trusted status authority owns revocation, withdrawal, supersession and key lifecycle; an agent cannot conceal a withdrawal by checking out an older Git state.

No generic cryptography code is proposed for the plugin. No supported P-256 signature-verification API was identified in Python 3.11's documented standard-library crypto interfaces. The official [Cryptographic Services index](https://docs.python.org/3.11/library/crypto.html) documents hashing, HMAC and secure randomness; these do not supply the native signer's public-key verification contract. This is a documented-interface finding, not an exhaustive claim about every possible platform integration. The repo's dependency constraints therefore need a concrete verification strategy: a qualified external verifier returning an independently authenticated result, or a separately approved implementation/dependency exception. Simply introducing a command named `verify` or implementing unreviewed elliptic-curve arithmetic does not settle this. A network verifier also needs availability and egress authority; plan approval grants neither.

### Public record and protected original

The portable record extends ADR 0013 rather than inventing a per-host copy:

| Public, canonical and committed | Protected evidence / trusted service |
| --- | --- |
| Schema and authority-profile version; public repository/feature identity; redacted run and repair references | Actual originating host session/message/request identifiers and captured human events |
| Complete canonical planning manifest, normalization version, digest and source commit | Private interview content, authenticated human enrollment and identity mapping |
| Final HTML artifact manifest, draft PR/source snapshot, decisions/finding evidence digests | Private findings/annotations and original response presentation |
| Separate dispositions, stable finding IDs and evidence/revision bindings | Original per-finding responses and their trusted capture chain |
| Explicit final approval, redacted reviewer reference, trusted decision time, receipt and issuer/key reference | Signer/authenticator lifecycle and audit evidence |
| Supersession/withdrawal references; verification-policy/status references | Monotonic challenge issuance/consumption and authoritative current status |

Redaction must occur before signing the public projection, under a deterministic contract binding it to the protected event manifest. Removing signed fields afterward invalidates the signature. Do not publish raw session IDs, machine names, emails, absolute paths, biometrics, tokens or private transcripts. A generic content digest can leak predictable secrets; do not publish hashes of low-entropy private identifiers as a supposed anonymization scheme. Opaque references and any private commitments require their own privacy review.

A single final attestation may bind the collected disposition set, but the human must actually make each named disposition separately. The final generic approve action cannot synthesize missing gap acceptance. The precise record schema, canonical state path and signer envelope are implementation contracts to settle after the trust decision, not additional accepted ADR facts.

## Plan-review skill and workflow blueprint

All steps below are **proposed executable behavior required by the accepted ADR**, not claims about current runtime enforcement.

### Entry and every-plan interview

Planning ends at its existing HTML review artifacts and draft PR handoff. The handoff lists decisions, blocked planning gates, strict low-confidence findings, the exact review snapshot and a manual plan-review invocation. It does not wait for approval or auto-select implement. Suggested discovery: Claude's namespaced `/speckit-pro:speckit-plan-review` and Codex's `$speckit-plan-review`, resolved through each host's skill inventory. The discovery forms follow official [Claude plugin-skill naming](https://code.claude.com/docs/en/skills#choose-where-skills-load) and [Codex skill invocation and inventory](https://learn.chatgpt.com/docs/app-server#skills). These names describe the proposed shared skill; it does not exist as a shipped skill from this research. Claude documents `disable-model-invocation: true` for manual entry; equivalent host guidance still needs runner-enforced human entry and capture, since a program can submit skill invocation text.

The human invokes review separately, including for a clean plan. The runner resolves repository, feature, original planning run and any repair run. It verifies readable authoritative inputs, task/dispatch metadata, required findings and fresh artifact/PR evidence; it refuses to create an approvable snapshot from missing evidence. Missing required capture capability may permit explicitly labeled explanatory discussion, but cannot produce approval or misleading admission-ready state.

One shared authored skill uses grilling's decision tree and domain-modeling's precise vocabulary/scenario checks. It checks understanding of the goal, exclusions, domain terms, decisions, task dependencies, verification strategy, implementation boundaries and risks. It investigates factual questions from evidence rather than asking the human to guess. Interview questions use the host's blocking user-input interaction and wait; never infer answers from silence or elapsed time. Questions are one at a time, respecting the owner's interaction preference; a clean gate report does not skip understanding checks. This research does not invoke an actual review or update glossary/ADRs.

The runner enumerates findings from canonical gate/confidence results. Guidance explains each finding and the options: request repair, explicitly accept the named residual gap or reject/defer it. Separate blocked-gate and strict-confidence dispositions retain their technical status. A rejection or unanswered required finding keeps the review incomplete. Missing inputs, unverifiable provenance, host restrictions, harm halts and action-consent requirements are not waivable gaps. Do not ask during implement to rescue absent approval.

### Requested change and linked planning repair

A requested change creates a revision-bound change request and an explicitly authorized linked planning repair. Review freezes the old snapshot and suspends final approval; it does not overwrite the original interview, run ledger, failure evidence or spent attempts. The repair has its own run identity and bounded attempt history, links affected original blockers, and follows ADR 0012. An ordinary resume or approval operation must not call an epoch-reset helper as an implicit repair authorization.

Repair reconciles the specification, plan, normalized task meanings/dependencies/ownership, dispatch metadata, contracts, design/research inputs, checklists, formal selections/configuration and effective verification settings. The runner determines affected checks from declared ownership/dependencies; uncertainty requires a conservative broader planning check set. It reruns affected planning phases/checks, rebuilds dependent HTML artifacts, refreshes the draft PR/source snapshot and inventories the final findings. It reports failures as failures rather than converting prior attempts into passes.

Review resumes against the newly verified snapshot. Old responses remain historical; an acceptance naming the old revision cannot silently authorize a changed finding. The human reviews the final bundle again and separately disposes every remaining required finding. An edit discovered during the interview takes the same stale/repair path even if the agent calls it editorial. A content change after final confirmation but before record issuance fails the final equality check and requires new confirmation against a fresh snapshot.

### Explicit confirmation, issuance and separate handoff

After understanding checks and every required disposition, the trusted UI presents the final exact bundle/evidence identity, a concise scope statement and the residual findings with their explicit dispositions. It asks for final human approval without a preselected/default affirmative action. This confirms the plan only; it does not authorize implementation, reset attempts, approve outbound data or widen security grants.

The authority profile verifies actual response provenance, generation freshness and current reviewer authorization. The runner independently rechecks full input/evidence equality and exact disposition coverage, validates the attestation and writes one approved record atomically. Partial writes, missing commit or uncertain issuance remain incomplete; resume reconciles the same issuance identity rather than manufacturing another human response. The record excludes itself from its own planning manifest and is committed with feature state. Canonical run/workflow state references this record; it never restates `approved=true` as a second authority.

The terminal message links the committed record and reviewed bundle, reports accepted gaps without calling them passed, and describes a separately invoked implement handoff. Approval does not launch implement. The implement admission owner checks the canonical record on direct, staged and resume entry, then again before dispatch as required for drift. A changed host/session may reuse a valid unchanged approval; current host readiness and action-specific permissions are checked independently. Source equality uses the planning manifest, not equality to every later implementation commit.

### Review lifecycle

The following state names are a proposed contract vocabulary. The approval decision/evidence is immutable; current status is a derived, integrity-checked view of append-only events.

| State | Entry/exit rule | Admission result |
| --- | --- | --- |
| Unreviewed | Planning boundary complete; manual review not begun | Refuse |
| Reviewing | Frozen valid snapshot and interview generation; answers incomplete | Refuse |
| Repair requested / repair running | Human requested linked revision change; old evidence retained | Refuse changed bundle |
| Awaiting final confirmation | Understanding/disposition checks complete; pending exact-revision human question | Refuse |
| Interrupted / incomplete | Turn/session lost, canceled question, missing answer or uncertain issuance | Refuse; preserve answers and resume point |
| Approved and committed | Verified explicit final decision, exact bundle/dispositions, trusted receipt, durable committed record | Eligible for separately invoked implement, subject to all other checks |
| Stale | Authoritative inputs or final reviewed evidence changed | Refuse changed bundle; review/repair again |
| Withdrawn | Verified human withdrawal event under the same approved authority profile | Refuse; preserve original approval |
| Superseded | Verified replacement approval for a changed revision | Refuse old scope; validate replacement |
| Proven tampering | Established forged authority or altered protected/public evidence | Existing harm-halt policy; do not downgrade to an ordinary missing approval |

For incomplete review on the same or other host, resume can reuse independently verifiable captured responses for the unchanged snapshot. If private capture evidence or its authenticated receipt is unavailable, recapture the unresolved review inputs; never claim partial answers are approval. An already approved unchanged bundle does not need another interview solely because the host moved. Every canceled pending final question invalidates its generation; a late signature cannot approve a new generation. Withdrawal requires the same actual-human capture rigor and an admission-visible monotonic status record. Active withdrawal/drift blocks affected dispatch under ADR 0013 while preserving original results and attempts.

## Runner ownership and implementation seams

Current source inspection shows content/path/ledger mechanisms, not a complete human authority system. Extend existing owners through their public interfaces; do not reinterpret their current checks as approval.

| Responsibility | Existing owner and evidence | Proposed extension / boundary |
| --- | --- | --- |
| Shared host skill rendering | `speckit-pro/speckit_pro_runner/host_skills.py:1–7`, `:46–54` | One shared `speckit-plan-review` guidance source with host blocks; no duplicated approval rules. |
| Stage selection and admission | `helpers/read_only.py:2777–2822`; explicit stage accepted and completed planning can select implement | Extend resolver/dispatch entry points to require the canonical approval verifier and preserve the planning terminal boundary. Stage flags never substitute for approval. |
| Task normalization and dispatch bindings | `task_execution.py:25–35`, `:133–148` | Reuse checkbox normalization and validate metadata; extend authoritative input inventory to the full ADR bundle. Do not reuse its three-document fingerprint as full approval. |
| Artifact/evidence freshness | `artifact_review.py:289–304`; `helpers/read_only.py:2554`, `:3312` | Reuse artifact/PR corroboration and frozen reviewed-evidence manifests; preview verification remains delivery evidence. |
| Canonical bytes and confined reads | `canonical_json.py:9–16`; `trusted_io.py:216–267`, `:384–389`; `strict_input.py` | Reuse canonical serialization, bounded inputs and duplicate-key rejection. File containment proves no human identity. |
| Run links, spent attempts, guarded repair | `execution_control.py:1239–1251`, `:2613–2630`; `helpers/read_only.py:1373` | Preserve run history and public repair interfaces. Existing `native_observation` shape/unconsumed event-ID checks do not authenticate an original human; they need qualified capture evidence for approval-related use. |
| Confidence/finding inventory | `helpers/read_only.py:3362–3405` | Produce revision-bound findings and required dispositions from runner results; the skill cannot classify away a strict finding. |
| PR, review/UAT and terminal reports | `helpers/pr_emission.py:32`; `helpers/run_finalization.py:451`; ADR 0012 | Render canonical findings/status/approval references; do not author parallel authority lists. |
| Security/stop decisions | `stop_policy.py`; ADRs 0010, 0011 and 0013 | Retain harm halt/readiness/action consent owners. Approval cannot override their decisions. |

A dedicated runner **plan-approval policy owner** is justified only for the genuinely new domain: full planning manifest inventory, review states, required dispositions, provenance-profile validation, canonical record issuance and admission checks. Put it in the runner policy layer with an executable schema in contracts. Helpers/registry dispatch to it; skills describe its results. Host adapters only translate authenticated capture envelopes, preserving bytes/IDs privately; they never decide validity, mint human answers or maintain separate records. The trusted signer/control plane, if selected, lies outside ordinary agent-readable/writable runner state. Naming a runner module “trusted” does not create that isolation.

The full manifest must inventory every planner/executor-consumed authoritative input and effective setting, with an executable normalization/exclusion contract. Exclude declared task progress, runtime bookkeeping and task-produced implementation files; include task meaning, dependencies, contract/design content, formal planning inputs, effective project commands and verification choices. Approval records are excluded from the bundle they attest. Missing inventory evidence is a failure, not an agent-selected subset. Unknown schemas/policies, duplicate fields, ambiguous path aliases and digest disagreement fail closed.

## Shared acceptance matrix

These are required future acceptance cases, **not passing test results from this research**. Run the same contract fixtures through Claude and Codex adapters. Capture qualification requires controlled human-in-the-loop tests of the selected authority profile; source inspection and synthetic transport fixtures alone cannot prove human behavior.

| Case | Claude-origin record → Claude / Codex | Codex-origin record → Codex / Claude |
| --- | --- | --- |
| Clean plan | Every-plan interview, explicit final human confirmation, valid receipt and committed record required | Same |
| Remaining blocked gate plus strict-confidence finding | Two separate named dispositions plus final approval; preserve failed/low-confidence statuses | Same |
| Generic approve, silence, timeout, canceled question, declined answer | No approved record; name incomplete requirement | Same |
| Ordinary typed user text or native question reply without qualified capture | Useful interview context, insufficient issuance provenance | Same |
| Programmatic SDK/hook reply; caller-stamped human origin; agent quote/`approved=true` | Reject as authority, even if conversation IDs/hash match | Same |
| Valid signature with self-supplied key or agent-accessible signer | Reject unknown/unqualified trust root or capture assurance | Same |
| Qualified explicit approval of exact snapshot | Runner verifies provenance, scope, dispositions and content; commits one record | Same |
| Change to contract, task dependency, formal input, effective command or verification setting | New bundle; old approval refused; linked repair and new final review | Same |
| Task completion/runtime-result update or task-produced implementation commit | Preserve approval only if executable normalization excludes it and all authoritative inputs remain equal | Same |
| Artifacts/PR refreshed after repair | Review final refreshed evidence before approval; no old response inheritance across revisions | Same |
| Revision race between confirmation and issuance | Refuse issuance; no partial approved record | Same |
| Replay into another feature/repository/review generation or after cancellation | Reject scope/nonce/generation mismatch; already-issued identical record may validate idempotently without reissuing human approval | Same |
| Same approval cloned to another host | Validate same portable record/trust policy/status; no fresh interview for unchanged bundle | Same |
| Missing source session/private transcript but independently valid receipt and required retention/status evidence | May validate without raw export; verify attested original reference under selected profile | Same |
| Only transcript reference available, missing trust enrollment/receipt/status, or private original unavailable contrary to profile | Refuse; report exact unavailable prerequisite | Same |
| Interrupted partial interview/resume | Revalidate snapshot and receipts, cancel old pending generation, ask unresolved inputs; no approval from partial completion | Same |
| Withdrawal/supersession or attacker rollback to old committed record | Verify current monotonic status and refuse old authority; preserve history | Same |
| Unsupported capture runtime/hardware or headless review with no trusted human channel | Incomplete/refused issuance; no silent software-answer fallback | Same |
| Headless implement with valid prior interactive approval | Validate without questioning the user; separate implementation invocation still required | Same |
| Direct/staged/resume implement with absent/stale approval | Refuse before any dispatch; planning markers/draft PR cannot bypass | Same |
| Approval itself or default planning completion | Never start implement automatically | Same |
| Plan acceptance but outbound/security action remains restricted | Security consent remains separately required; no grant widening | Same |
| Proven fabricated/tampered provenance | Existing harm halt; preserve evidence | Same |
| Active authoritative drift/withdrawal | Block affected work; uncertain dependency set fails closed; independent verified authorized work only | Same |

Native Codex adapter qualification additionally needs real supported-device enrollment, trusted UI challenge/display binding, exact public-key enrollment, proof verification, cancellation/late-proof handling and unavailable-platform cases. Claude qualification needs a trusted capture/signing channel beyond application-supplied `AskUserQuestion`/hooks. Neither suite may equate “automated fixture says human” with verified human identity.

## Human decisions still required

The research leaves these choices explicit; none is assumed here. They should return to human review as a successor decision, before health-spec feasibility is asserted.

1. **Trusted capture architecture.** Approve a shared external human-authenticated UI/signer/control plane integrated with both hosts, or pursue first-party host support and keep approval-gated implementation unavailable meanwhile. Recommendation: decide the shared external architecture if implementation must proceed now. A native-Codex-only prototype is an optional feasibility investigation, not fulfillment on both hosts. A manual approval command or GitHub review substitution would change the accepted interview-confirmation flow and is not proposed as an equivalent.
2. **Identity and signer enrollment.** Decide who can approve, how their identity maps to a credential, who pins the trust root outside agent write authority, and whether shared device/account/any-enrolled-finger assurance is acceptable. Define enrollment, recovery, key rotation and revocation authority. No report claim identifies the device operator as a particular human.
3. **Approval intent and evidence assurance.** Decide the trusted presentation/capture boundary and retained private event contract, including evidence that each finding was separately disposed before final confirmation. A hardware signature without verified display/scope binding is insufficient. Decide what must remain independently verifiable when originals are private or later unavailable.
4. **Freshness and availability.** Decide signed status freshness, online versus bounded offline admission, rollback protection and fail-closed behavior during authority/evidence outages. Recommendation: require current authenticated status at admission initially; offline allowance needs explicit expiration and revocation limitations. A repository clone alone cannot prove that an approval was never withdrawn elsewhere.
5. **Supported profiles and verifier implementation.** Decide supported host/runtime/platform minimums, unavailable-device behavior and how signature verification complies with the repo's standard-library dependency rule. Authorize any external service/egress and dependency exception separately. This research does not authorize installing signers, changing host trust, enabling biometric features or sending private inputs.

The already accepted workflow is not reopened: every plan gets the interview; planning finishes without waiting; every residual blocked/strict-confidence finding needs separate human acceptance; final approval binds the complete final bundle and refreshed evidence; runner-written record is committed; unverifiable provenance refuses entry; unchanged host moves reuse valid approval; approval never starts implement or implies security consent.

## Validation and research completion

Safely tested during research:

- `codex --version`: installed CLI reported `0.156.0`.
- `codex app-server --help` and `generate-json-schema --help`: inspected tooling only.
- `codex app-server generate-json-schema --experimental --out <temporary-schema-directory>`: exit 0; generated schema contains verification methods, bounded challenge/proof shape and ordinary question-response shape. No app-server session, account-status lookup, biometric operation or model run occurred.
- Public release-tag source comparison: the four native/platform/protocol files listed above matched pinned current source exactly.

Focused documentation validation: `python3 tests/speckit-pro/unit/test-privacy-scan.py` passed 14/14; `git diff --check` passed. The new-file `git diff --no-index --check /dev/null <report>` emitted no whitespace diagnostics (exit 1 denotes the added-file difference); a direct report whitespace scan also found none. `ripwire . --quality-delta --legend=compact` exited 0 with zero regressions/gating findings and 13 existing stale acknowledgments. The subsequent `ripwire . --test-gate --legend=compact` exited 0 with zero changed/impacted code symbols. These graph advisories do not verify approval provenance or the correctness of research prose. The report is the only changed file, on `research/plan-approval-provenance`; publication evidence is linked from the research ticket's resolution. Full plugin, Go, docs-site and evaluation suites are intentionally out of scope for this single research document. No implementation tests were added. Research completion means the findings/blueprint are reviewable, including the capability gap; it does not mean the proposed authority system or skill is implemented or qualified.

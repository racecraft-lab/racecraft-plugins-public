# Plan approval follows a human interview and binds the full planning revision

Status: accepted

Implementation status: planning decision; this ticket changes no plugin runtime behavior. Approval capture, revision validation, review orchestration and host parity require implementation and verification.

Decision: [Plan approval record](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1014), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

Amended through [Prototype: qualify the local plan-approval authority](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1034): the owner requires every planning finding to be fixed and checked before approval, with copyable prompts for planning repair and a separately invoked implementation run. This replaces the original residual-gap acceptance option; it changes the intended contract, not shipped runtime behavior.

Every plan gets a human review interview through a new `speckit-plan-review` skill after planning has produced its HTML artifacts and draft PR. The interview works through gaps and requested changes before the human explicitly approves the final planning revision. Approval is recorded by the runner and permits that revision to be built; implementation starts only on a separate human invocation.

For the health program, [ADR 0017](0017-recorded-plan-approval.md) sets the approval's assurance level to `recorded`: the runner validates the record's structure, bindings and the interview's confirmation reference, not hardware-backed human presence. [ADR 0015](0015-local-plan-approval-authority.md)'s protected local authority is deferred to follow-on work. Where this ADR says provenance is verified, read it at the `recorded` level until that work lands.

## Review before approval

The interview is a separate, explicitly human-invoked workflow between the autonomous planning and implement runs. It uses grilling and domain-modeling to check the human's understanding, examine the decisions list, and work through every blocked planning gate and strict low-confidence finding. It runs even when planning reported no gaps. The owner requested this additional interactive skill; it is an explicit exception to the map's original scaffold-only heavy-interaction rule, outside unattended autopilot. It introduces no general question path inside autopilot and does not make unattended planning wait for plan approval.

The skill guides the interview and dispatches runner operations; it cannot own approval policy, classify revision validity or manufacture a human response. [Research: verify portable human plan-approval provenance on both hosts](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1032) must establish the supported provenance mechanism and design this skill's workflow, runner/guidance boundary, host adapters, interrupted-review/resume behavior and shared acceptance matrix. It produces a design, not a shipped skill. The implementation follows through the health-program spec.

When the human requests a plan change, the interface constructs a handoff prompt for the human to copy into the current Claude Code or Codex session. The prompt includes every requested finding, its selected remedy or exact custom instructions, and the reviewed revision. Preparing or copying it sends nothing and starts no work. The planning agent carries out a linked planning repair, reruns affected planning steps and checks, and refreshes the HTML artifacts and draft PR before presenting the revised bundle for approval. Task definitions, contracts and other dependent planning outputs are reconciled with the change; checking only the edited document is insufficient. Repairs are limited to requested corrections and necessary dependent outputs, with every resulting change explained. The original run's blocked entries, failure evidence and spent attempts remain intact under ADRs 0004 and 0012. Review is not permission to reset the original run's ladder or ledger.

Every planning finding must be corrected and have a passing applicable planning check bound to the final revision before approval. This includes blocked planning gates, strict low-confidence findings and custom reviewer requests. Selecting a remedy, accepting a risk, a generic approval, silence or elapsed time cannot close a finding or substitute for its check. Missing, failed, omitted or mismatched results leave the revision unapproved. The interview covers the complete authoritative finding list without a fixed issue-count limit. The reviewer compares requested fixes with returned corrections and check results, then explicitly approves the whole final revision once; separate acceptance clicks for each correction are unnecessary.

If the reviewer changes their requested correction, they can explicitly withdraw an earlier custom instruction by its exact text, request and finding identity. Withdrawal preserves the original request and records its disposition; it removes only that instruction from the active request queue, never the required finding or its technical status. It invalidates earlier planning checks and requires a fresh replacement handoff, revised correction and matching checks. Selecting a built-in remedy alone cannot silently withdraw or satisfy the earlier instruction.

The final plan must also be usable and inspectable: its authoritative planning inputs, task definitions, revision identity and required approval evidence must be readable and verifiable. A planning check does not complete implementation work that has not run, make a red canary green, or override a harm halt, forbidden action or host restriction. Original unresolved observations remain in history even when a linked planning repair produces a corrected, checked revision.

## The approved planning bundle

Approval binds the full authoritative planning bundle, not just `plan.md`, the three main documents, or every file at a Git commit. The runner constructs a deterministic manifest of repository-relative inputs and content digests. Its digest identifies the approved revision; the Git commit supplies a source reference, not the whole validity rule.

The manifest includes `spec.md`, `plan.md`, normalized task definitions and dispatch metadata, contracts, design inputs, applicable research and supporting planning documents, checklist requirements, selected formal models and their planning inputs/configuration, and effective verification settings that determine the planned work. Project commands, opted-in verification and relevant execution-boundary declarations cannot silently change outside this binding. The implemented contract must inventory every authoritative input consumed by the planner or executor and derive the manifest from that inventory; prose or an agent-selected subset cannot decide what counts.

Execution-only updates are excluded by an explicit runner normalization contract: task completion markers, attempt history, results and other runtime bookkeeping do not constitute a new plan. Implementation files produced by tasks are not planning inputs merely because their commits follow approval; they remain subject to normal verification and any selected formal final/Post checks. Approval records themselves are outside the bundle they attest. These exclusions cannot ignore changes to task meaning, dependencies, acceptance requirements or verification settings. There is no discretionary editorial-edit exception for authoritative planning content.

The final reviewed evidence set is also identified: the revised artifact manifest, draft PR/source revision, decisions list, blocked-gate evidence and confidence findings. Approval refers to that reviewed snapshot. Later progress reports can show new results without rewriting what the human reviewed or silently substituting another planning bundle.

## One runner-owned record

The runner writes one machine-readable approval record in versioned feature state and commits it with the feature. Claude Code and Codex validate the same portable record; neither maintains a host-specific approval copy. Workflow and run state reference the canonical record rather than restating its decision.

The record contains:

- Its schema version, feature/repository identity, originating planning run and any linked planning repair runs.
- The final planning manifest, its revision digest and source commit reference.
- References and digests for the final reviewed artifacts, draft PR and findings evidence.
- The review interview's outcomes and evidence of the human's explicit final approval, including the approving human's identity, decision time and original human-input reference.
- The complete finding inventory, each requested remedy or exact custom instruction, its correction and passing planning-check evidence, keyed to that finding's identity and the approved revision. Missing, duplicate or unknown findings or results refuse approval; a clean plan still receives final review.
- Links to any approval it supersedes and any subsequent withdrawal or supersession. Preserve earlier approval evidence; never rewrite the original human decision.

Public records use redacted descriptions, repository-relative references and digests. They do not copy private transcripts, secrets, machine identities or absolute paths. Sensitive provenance remains in protected evidence, with a verifiable reference in the portable record. Portability must preserve verifiability; copying an agent's assertion does not establish human approval on another host.

Only actual explicit human input in the final review can authorize creation of an approved record. The runner validates its provenance and binding before writing it. An agent-written `approved` value, fabricated quote, unrelated earlier approval or approval of an older revision is insufficient. If provenance cannot be verified, the review cannot record approval. Exact transport and schema belong to the runner's executable contract, with the same acceptance requirements on both hosts.

Plan approval grants no action-specific security consent. The readiness record, question permit, action consent and plan approval record retain their separate authority under ADRs 0008 and 0011. A changed approval record cannot widen an existing action grant.

## Implement admission and resume

An implement invocation, including direct implementation and resume entry paths, validates the canonical record before dispatching work. It checks identity, integrity/provenance, current planning-manifest equality, reviewed-evidence bindings, final approval and the complete finding inventory with its matched corrections and passing planning checks. A stage flag, complete planning markers, delivered artifacts or an existing draft PR cannot bypass this check.

Missing, malformed, stale, withdrawn, superseded or unverifiable approval refuses implement entry. The message names the missing or mismatched record field or finding and points to plan review; for example, a missing planning-check result names that finding. This is an admission refusal, not a new mid-run stop, security interrupt or retry path that can manufacture approval. No implementation dispatch begins.

Default autopilot planning still ends with review artifacts and the draft PR, even if a previous planning run completed. Neither planning completion nor final approval automatically advances to implement. After approval, the interface can prepare another copyable prompt; the human pastes it into the coding-agent session to invoke implement separately. Preparing or copying that prompt starts no work. The invocation starts only after the record passes validation.

Ordinary resume can reuse an approval for the unchanged bundle while preserving the run's blocks and spent attempts. A session or host change alone does not require another interview. Identity, readiness, host enforcement and scoped security authority still receive their own current checks; approval does not waive them. A repair of blocked work needs the explicit linked-run authorization required by ADR 0012, even when the original planning revision remains approved.

## Changes after approval

Any change to authoritative planning inputs requires fresh review and approval of the changed revision. Earlier approval is not amended by the implement agent, and the implement run cannot replan itself into a new approved scope. Preserve the original record and evidence; the revised approval supersedes it explicitly.

Before implement starts, drift refuses admission. During implement, the runner records the mismatch and marks affected work blocked-for-UAT without dispatching from the changed bundle. Independent work may continue only when its original approved inputs and authority can still be verified. If the affected set cannot be determined safely, all remaining work dependent on the unverified planning binding is blocked. The run reaches its UAT boundary with the incomplete work and evidence visible; no silent approval, rollback or ledger reset occurs. Proven forgery or tampering follows ADR 0010's harm halt rather than ordinary drift handling.

The changed revision goes through another interview and linked planning repair, with refreshed review evidence. Building it requires a valid new approval and an explicitly invoked linked implement run. The old run's blocks, attempts and results stay intact. Human withdrawal is honored; it is never treated as continued authority to dispatch.

## Current evidence and required verification

The inspected stage resolver automatically selects implement after completed planning and reads no full plan-approval record (`speckit-pro/speckit_pro_runner/helpers/read_only.py:2777`, `:2808`). Explicit implement selection can cross a nonterminal confidence verdict without another confirmation (`speckit-pro/skills/speckit-autopilot/references/phase-execution.md:243`). These behaviors require change, not reinterpretation as existing approval enforcement.

Planning's current host boundary sequence is documented separately for Claude Code and Codex (`phase-execution.md:1596`, `:1604`, `:1612`); stage authority lives in the workflow, with `autopilot-state.json` as a mirror (`speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md:56`, `:79`). Artifact delivery expressly does not prove human approval (`speckit-pro/skills/speckit-autopilot/references/artifact-review.md:3`, `:171`). Existing task metadata binds spec, plan and normalized tasks (`speckit-pro/speckit_pro_runner/task_execution.py:25`), but is not approval of the full bundle. This planning session inspected source and test definitions; it ran no live host workflow.

Implementation must prove on both hosts:

- Every plan receives review; review edits produce linked planning repair and refreshed evidence before final approval, preserving original blocks and attempts.
- Only verified explicit human approval creates an approved record; silence, forged provenance, an old revision or an unrelated response cannot do so.
- Every finding and custom request has a correction and passing planning check for the approved revision; omitted, duplicate, unknown, failed or mismatched evidence refuses entry with a named reason. A list with more than two findings receives the same checks, and original failure history remains intact.
- Every implement entry validates approval; default planning and approval itself never auto-start implementation.
- The full input manifest detects contract, design, task, formal-selection and verification-setting changes, while implementation commits and declared progress-only changes preserve approval.
- Active drift blocks affected work without using the changed plan; uncertain ownership fails closed, independent verified work can continue, and proven tampering triggers the existing harm halt.
- Cross-host validation, ordinary resume, withdrawal, supersession and linked repair preserve authority and history without inventing security consent or completion.

## Considered options

The original decision allowed explicit acceptance of remaining gaps. The prototype interview superseded that option: the owner requires all planning findings to be fixed and checked before approval. Direct agent messaging and implementation launch from the interface were replaced by copyable handoff prompts for the operator's current coding-agent session. Review only for plans with findings was rejected because a clean report does not establish human understanding. Binding only the three main files misses authoritative contracts and design inputs; binding the entire Git commit would invalidate approval on ordinary implementation progress. A manual approval command or canonical GitHub approval was rejected in favor of explicit interview confirmation captured by the protected authority and a portable committed record. Automatic implement launch, editorial drift exemptions and continuing on a stale record were rejected to keep the final reviewed revision and the later build decision explicit.

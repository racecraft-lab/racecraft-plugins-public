# Plan-approval prototype: closeout draft

Status: prepared for human review. No successor issue has been created and no ticket has been closed. Automatic approval review rejected the public issue-creation attempt; publication awaits explicit approval of this package.

## Proposed resolution of the prototype ticket

Resolve [Prototype: qualify the local plan-approval authority](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1034) through its **precise capability gap and successor decision** route, not as a qualified capture or enforcement profile.

The operator's confirmed workflow is:

1. Read each planning issue and its impact. Choose a recommended remedy, an alternative, or exact custom instructions.
2. Build and copy one handoff prompt into the current Claude Code or Codex session. Preparing or copying it sends nothing and starts no work.
3. Review the revised inputs, requested corrections and matching planning-check results. Require every planning finding to be fixed and checked before approval.
4. Explicitly approve the whole final planning revision once. Prepare a separate implementation prompt for a later human invocation in the coding-agent session.

The existing speckit-pro artifact library supplies the style and brand. Developer checks and setup information remain separate from the operator journey. Original blocked work, evidence and spent attempts remain intact.

The user expressed positive feedback on the current review experience, conditional on supporting more than two issues, and authorized the multiple-issue iteration. Final feedback on the generalized interface is still to be recorded; an agent cannot supply that acceptance.

The default example now contains three distinct issues; About offers an explicit ten-issue reset. Each issue has its own correction and matching check definition. A frozen required inventory prevents missing, duplicate or unknown findings/results from borrowing another issue's success. Focused proof covers zero, one, three and ten findings, all built-in remedy strategies, custom refusal and three-/ten-issue handoff flows. Browser verification confirms the ten-issue recovery and final-review path, exact three-issue clipboard content, retained choices, spaced handoff actions, both themes, narrow layout and keyboard/pointer error recovery. The corrected hit areas and focus targets were rechecked. The preview and captured source share SHA-256 `3f1cb6ea7a74e6d4d59957cfc20f39c918867d5548a7be9830bca99864d138eb`.

Prototype and verification assets:

- [Standalone review prototype](plan-approval-authority-prototype.html)
- [Operator domain model](plan-review-domain-model.md)
- [Observed evidence and qualification gaps](plan-approval-authority-evidence.md)
- [Compile-only native primitive probe](plan-approval-signing-probe.md)

The intended ADR 0013 and ADR 0015 contracts and glossary are amended on the planning branch to replace residual-risk acceptance with complete finding/remedy/correction/check binding and one final approval. Shipped runtime behavior is unchanged.

## Publication sequence after acceptance

1. Publish the captured prototype/evidence branch and the planning-record amendments.
2. Create the successor decision below as an open child of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006). Add it as a native blocker of [Definition of done: confirm and complete](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1029) before closing the old prototype gate.
3. Point ADRs 0013 and 0015 at the open successor qualification gate, and refresh ADR 0016's real-authority ownership reference without changing its canary-only issuer decision. Post the resolution with pinned asset links and the recorded human acceptance; close the prototype ticket.
4. Update the map's index with a short resolution pointer and amend its plan-approval gist to the all-findings-fixed-and-checked contract. Preserve concurrent map edits.

No protected authority property becomes qualified through this sequence. Health-program feasibility and completion remain gated by the successor. No keys, signing, authentication, enrollment, service installation, status transport or private-data scope is authorized.

## Successor issue draft

Title: **Plan approval authority: resolve protection and qualification under one macOS login**

Label: `wayfinder:grilling`

## Question

Which OS-enforced boundary can protect plan review, signing, reviewer trust and task dispatch from agent shell and automation running under the operator's existing macOS login, while providing fresh human confirmation with the requested password fallback? Can that profile meet the full approval contract, or which constraint needs an explicit human decision before qualification can continue?

## Context

Successor to [Prototype: qualify the local plan-approval authority](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1034), using that ticket's precise-capability-gap closeout route. The operator selected one reviewer, investigation of a Secure Enclave signer, the current Mac and existing user account, and password fallback. Another computer is unavailable. These choices authorize design investigation; no signer installation, key creation, authentication, enrollment, transport or private-data scope is authorized by this ticket.

The accepted interaction direction is issue explanation and impact, explicit recommended/alternative/custom remedies, a copyable planning-repair handoff, review of corrected inputs and matched checks, and one final whole-plan approval only when every planning finding is fixed and checked. A separate copyable implementation prompt invokes implementation in the current coding-agent session. The interface sends nothing and starts no work. ADR 0013 records this amended intended contract; ADR 0015 retains the protected authority boundary.

The HTML is a design simulation. Its editable state and canned replies establish no real human provenance, hardware protection or enforcement. The supplementary Swift primitive compiled but has not run; it is unprotected and qualifies no authority. Assets are captured on the throwaway branch [codex/prototype-plan-approval-authority](https://github.com/racecraft-lab/racecraft-plugins-public/tree/codex/prototype-plan-approval-authority/docs/ai/prototypes).

## Resolve

- Establish whether the complete review, signer, verifier, authoritative input inventory, policy selection, reviewer trust/lifecycle store and admission/dispatch path can be protected from the allowed same-user shell and automation capabilities. Repository-controlled scripts, an ordinary signer socket or a successful signature alone are insufficient.
- Specify protected human bootstrap, identity mapping, one-reviewer enrollment, rotation, revocation, recovery and independent transfer of issuer trust. Do not infer authority from GitHub or filesystem access.
- Select an exact supported macOS/tool/capture profile and interoperable signed encoding. Prove fresh per-approval biometric or password confirmation bound to faithful inert display; document cancellation, unavailable authentication and cached-authentication rejection.
- Specify immutable checked bytes through issuance, commit, admission and actual task use, including concurrent review and check-to-use races. Require authenticated current issuer status at all three boundaries, with rollback/time assumptions and refusal on missing evidence, lost trust and outages.
- Plan controlled human evidence on both Claude Code and Codex, and actual unchanged-record transfer to a second independently enrolled machine. The unavailable second machine is an explicit resource gap, not a passing simulated case.
- Preserve the original shared acceptance matrix, updated for all planning findings fixed and checked. Demonstrate refusals for fabricated replies, self-enrolled keys, absent presence, altered display/policy, stale or replayed approvals, revocation and supersession. Preserve independent action-specific security consent and the separate implementation invocation.
- Respect [ADR 0016](https://github.com/racecraft-lab/racecraft-plugins-public/blob/docs/speckit-pro-health-planning/docs/adr/0016-canary-release-gate.md): the canary-only issuer is trusted only in isolated canary host homes and every production verifier rejects it. Canary approval-flow evidence cannot qualify real human capture.

## Produces

An evidence-backed deployment and qualification decision, with exact required runtime scopes and controlled proof, or an explicit human decision about the incompatible constraints. Do not weaken the protected boundary to make the same-login prototype pass. No shipped implementation belongs here.

The health-program feasibility claim and [Definition of done: confirm and complete](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1029) remain blocked while any real-authority property is unqualified. Creating or resolving a UI prototype does not clear that gate.

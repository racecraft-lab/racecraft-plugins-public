# The health program uses recorded plan approval; a protected authority is follow-on work

Status: accepted

Implementation status: planning decision; no plugin runtime behavior changes.

Decision: owner decision on 2026-10-02, after [Prototype: qualify the local plan-approval authority](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1034) closed without a qualified authority and opened [Plan approval authority: resolve protection and qualification under one macOS login](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1037). Part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Decision

For the health program, plan approval is a **recorded approval**. The owner confirms the final revision explicitly in the `speckit-plan-review` interview. The runner writes ADR 0013's one committed record, bound to the exact planning manifest digest and the finding inventory with each correction and passing check. Implement admission validates that record against the current planning bundle and refuses when it is missing, malformed, stale, withdrawn, superseded or inconsistent.

The record states its assurance level: `recorded`. It carries the interview's confirmation reference, but it does not claim the confirmation is unforgeable. An agent with the operator's shell and file access could write such a record; the record does not defend against that.

ADR 0015's protected local authority is **deferred to follow-on work** outside this program. #1037 leaves the health-program map and no longer blocks the Definition of done.

## Why

ADR 0015 asks for protection against an agent that can run shell commands and edit files as the operator. Signing with Touch ID or a hardware key stops forged records, but an agent running under the same login can still edit the code that checks the signature. Closing that gap needs a boundary the operator's own login cannot cross, such as a separate account or device. Three tickets in a row (#1033, #1034, #1037) ended in a new gate rather than a qualified design.

The risk a recorded approval leaves open is small in this program's setting:

- The operator starts every planning, review and implement run.
- Implement ends in a pull request that only the owner merges, followed by human UAT.
- Risky actions (repository-data egress, credential or permission changes, security-control changes) need their own action-specific consent under ADR 0011, whatever the plan approval says.

An implement run on an unapproved plan therefore costs time and tokens and produces a pull request the owner can reject. It cannot ship.

## What still holds from ADR 0013

- Every plan gets the review interview, including plans with no findings.
- Every planning finding is fixed and has a passing planning check before approval. Silence, elapsed time, a generic approval or an agent assertion never creates the record.
- The record binds the full planning manifest. Any change to authoritative planning inputs needs fresh review and approval.
- Implement is invoked separately; approval never starts it.
- Plan approval grants no security consent.
- Drift during implement blocks affected work under ADR 0012. Proven tampering still triggers ADR 0010's harm halt.

## What changes

- ADR 0013's provenance rules apply at the `recorded` level: the runner validates the record's structure, bindings and the interview's confirmation reference, not hardware-backed human presence.
- ADR 0015 is deferred. Its threat model, boundary and qualification list remain the starting point for the follow-on work.
- The canary's test issuer (ADR 0016) still exists for the plan-review step. Production refuses records marked as canary-issued.
- Spec and PR text must say the approval is recorded, not protected. Nothing may describe it as tamper-proof.

## Considered options

- **Keep the protected authority as a Definition-of-done blocker.** Rejected: open-ended security work blocking a health program whose real risk is bounded by owner merge and UAT.
- **Require hardware-backed signing without protecting the verifier.** Rejected for now: weeks of signer and enrollment work that still leaves the verifier editable under the same login.
- **Recorded approval now, protected authority later.** Accepted.

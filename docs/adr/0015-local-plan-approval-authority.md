# A protected local authority captures and enforces plan approval

Status: deferred. [ADR 0017](0017-recorded-plan-approval.md) uses recorded plan approval for the health program and moves this protected authority to follow-on work. The boundary and qualification list below remain the starting point for that work.

Implementation status: architecture decision only; no approval capture profile is qualified and no plugin runtime behavior changes. ADR 0013 remains the approval contract.

Decision ticket: [Plan approval provenance: choose the trusted capture boundary](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1033), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Accepted boundary

Use a local approval authority protected from the agent's write and signing authority. Its trusted review interface presents the exact final planning bundle and reviewed evidence, binds every finding's requested remedy, correction and passing planning check, and obtains one explicit final human approval after every planning finding is fixed and checked. This follows the amended ADR 0013 contract; selecting a remedy cannot accept an unresolved risk. The initial capture profile must qualify Claude Code and Codex on macOS, including transfer between independently enrolled machines. Linux and Windows capture remain unsupported until separately qualified.

The threat model includes an agent able to invoke shell commands and edit repository files, transcripts and Git history. The operating system, protected authority and its human-controlled administration are trusted. Malicious host administrators or a compromised operating system are outside this profile; repository authorship, session role and an agent assertion supply no approval authority.

Require current authenticated status from the issuing authority at issuance, implement admission and before each task dispatch. Initial qualification permits no offline or cached-status fallback. A clone alone cannot prove that an approval or reviewer credential has not since been withdrawn, revoked or superseded. If status is unavailable, refuse admission or block affected active-run work under ADR 0013; never substitute a question, silent approval or a new stop category.

## Protected boundary and binding

Protection covers the interface and confirmation controls, signer, verifier, authoritative input inventory, policy/version selection, reviewer trust roots and lifecycle state, and admission/dispatch enforcement. A helper executing from an agent-writable checkout or a verifier selected by mutable repository configuration does not establish this boundary. Qualification must demonstrate that the agent cannot replace these components or use an unchecked dispatch route to obtain valid approval authority.

Generated artifacts and other review content are inert data in the trusted interface: they cannot execute scripts, overlay controls or supply the human's answers. The authority binds the displayed snapshot and complete finding inventory, including each finding's identity, requested remedy or exact custom instructions, correction and passing check evidence, to the signed final decision. A display digest supplied only by the agent proves no faithful presentation.

Issuance, record commit, admission and task use must consume the same validated immutable planning inputs and effective settings. References and working-tree paths cannot move between checking and use. Unknown inventory entries, schema ambiguity, path aliases, concurrent changes or a mismatched display/signature refuse issuance or dispatch. The exact interoperable encoding and versioned normalization contract remain part of qualification.

The runner retains ADR 0013's one committed portable record. The protected authority supplies independently verifiable capture evidence and current status, rather than a second host-specific approval decision. Both hosts validate the same record. An unchanged planning bundle may move between enrolled machines without another interview only when the receiving machine independently trusts the issuer, verifies the record and can obtain current status. Record issuance never starts implement; the human invokes implement separately. Plan approval grants no action-specific security consent.

## Signing and enrollment are unresolved

No signer or reviewer-enrollment profile was selected in this session. The hardware-key SSH-signed Git object from the ticket discussion remains a candidate alongside a qualified per-use biometric signer. The qualification gate must make and verify those remaining choices; this decision accepts neither automatically.

The Git candidate has useful stock cryptographic tooling, but it is insufficient by itself:

- In OpenSSH 10.2p1, `ssh-keygen -Y verify` verifies the signature and allowed signer without requiring the security-key presence/verification flags. Those signed flags require explicit approval-policy enforcement. See [the pinned verifier](https://github.com/openssh/openssh-portable/blob/V_10_2_P1/ssh-keygen.c#L2600) and [security-key protocol](https://github.com/openssh/openssh-portable/blob/V_10_2_P1/PROTOCOL.u2f).
- A security-key algorithm name does not establish trusted hardware origin. OpenSSH treats enrollment attestation as opaque; protected enrollment must establish the selected credential's real protection. A signing interaction does not prove what the human reviewed. See [the enrollment protocol](https://github.com/openssh/openssh-portable/blob/V_10_2_P1/PROTOCOL.u2f#L130) and [signed-data format](https://github.com/openssh/openssh-portable/blob/V_10_2_P1/PROTOCOL.sshsig#L57).
- In Git 2.51.0, the verifier program and trust files are configurable, the committer timestamp supplies verification time, and a missing configured revocation file can produce a warning while verification proceeds without it. Qualification must pin tooling/configuration and fail closed on missing current lifecycle evidence. See [Git's verification flow](https://github.com/git/git/blob/v2.51.0/gpg-interface.c#L428) and [missing-revocation branch](https://github.com/git/git/blob/v2.51.0/gpg-interface.c#L538).
- Password-manager or Secure Enclave custody does not by itself establish uncached per-approval confirmation. The profile must prove that property and bind it to the protected review. See [1Password's authorization policy](https://www.1password.dev/ssh/agent/security) and [Apple's key-protection guidance](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave).

Reviewer identity mapping, trusted bootstrap, enrollment, rotation, revocation, recovery and deauthorization must be controlled outside agent authority. A self-signed new key or a restored old `allowed_signers` file cannot establish current reviewer authority. The qualification gate must settle whether there is one reviewer or a human-managed allowlist, and how trust is established on another machine. Git transports signed evidence and history; it is not the live authority or a bootstrap trust root.

## Named unresolved gate: local plan-approval qualification

[Plan approval authority: resolve protection and qualification under one macOS login](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1037) owns the remaining profile choices and proof of the selected boundary. The preceding prototype resolved the operator workflow through its capability-gap route; it qualified no protected capture or enforcement property. Before the health-program spec claims feasibility, a bounded prototype must establish:

1. A deployment/enforcement design on macOS that protects the entire boundary from the agent's allowed shell and filesystem powers, plus exact supported tools, versions and capture modes. The prototype stays outside the shipped plugin.
2. Human-controlled enrollment and recovery, verifiable per-approval interaction, explicit signature-policy enforcement and an interoperable signed encoding. Unknown assurance or missing trust evidence refuses approval.
3. Faithful inert presentation of the frozen final bundle and complete finding/remedy/correction/check binding, followed by one final human confirmation only after every planning finding is fixed and checked, including cancellation, interrupted review and changed-revision rejection.
4. Authenticated current issuer status, withdrawal/supersession/revocation, rollback-resistant lifecycle state, reliable time assumptions where time is used, and refusal on outages or lost trust roots. Any status endpoint/transport and its security consent must be separately specified; this ticket authorizes no networking setup or private-data export.
5. Controlled human-in-the-loop qualification on both agent products and another enrolled machine, with identical verdicts for valid approval, forged replies, untrusted signers, missing presence, injected display content, stale/replayed approvals, altered verification policy and races from reviewed bytes through actual task use.
6. The shared ADR 0013 acceptance matrix, including absent private evidence: retain only independently verifiable redacted references in the portable record, and refuse if the selected profile requires evidence that is unavailable. Source inspection or synthetic replies cannot stand in for these live results.

Until this gate is passed, the spec must state that the architecture is selected but feasibility and host acceptance remain unqualified. ADR 0017 removes the Definition-of-done dependency on this gate for the health program.

## Alternatives and scope

A remote shared authority and a supported host-owned integration were considered. The human selected a local protected authority. Repository-state-only approval, a signing prompt without the protected review, and agent-controlled capture do not meet the selected threat model and approval contract. The hardware-key Git candidate remains under consideration, with the limitations above, rather than being excluded by the prior native-host research.

This ticket changes planning records only. It installs no signer or service, enrolls no reviewer, changes no host trust, implements no plugin behavior and runs no real approval/signing test. The remaining gate requires explicit future prototype and human qualification work.

# Local plan-approval authority: prototype checkpoint

Date: 2026-10-02. Status: incomplete; no qualified capture or enforcement profile.

Decision ticket: [Prototype: qualify the local plan-approval authority](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1034), within [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Purpose and human decisions

Explore the review and authority lifecycle without changing shipped plugin behavior. ADRs [0013](../../adr/0013-plan-approval-record.md) and [0015](../../adr/0015-local-plan-approval-authority.md) remain unchanged.

The human chose **one reviewer initially**, explicitly enrolled on each machine; account or repository access supplies no reviewer authority. The human then selected **Secure Enclave with fresh per-approval biometric confirmation** as the first signer candidate to investigate. This is not a qualified signer selection or permission to create keys.

The human requires this prototype to run on **the current Mac using the existing user account**; another computer is unavailable. Separate review/agent login isolation is not selected. Same-login protection against agent automation remains a qualification gap, and actual second-machine transfer cannot be qualified with the available environment. Simulating transfer does not meet that requirement.

The human explicitly selected **password confirmation fallback** when biometric confirmation is failed or unavailable. The exact supported macOS API/policy and fresh per-approval human provenance for that fallback remain unqualified. Password fallback is a requested candidate property; it does not silently admit cached authentication or establish human origin by itself.

The human also requires **the prototype and final review implementation to use the existing speckit-pro HTML artifact library's style and brand**. The HTML prototype must embed the canonical brand and head blocks from `speckit-pro/artifact-gallery/brand-kit.css` and `theme-toggle.html` without modifying them, following its [single-file contract](../../../speckit-pro/artifact-gallery/SPA-CONTRACT.md) and [brand voice](../../../speckit-pro/artifact-gallery/brand-voice.md). The interactive prototype is the default view; setup, instructions, limitations and model details belong in a separate Guide view. This is a requirement for the future protected review interface, not authorization to ship that implementation in this ticket.

No signing, enrollment, service installation, status transport or private-data scope has been authorized by these design choices.

The [throwaway review demo](plan-approval-authority-prototype.html) is a design simulation. Its clicks, signatures, identities, status responses, enrollment and execution are modeled synthetic events. They do not establish human provenance, hardware protection, authenticated current status, host enforcement, or security qualification.

The human requested the demo in the in-app Browser for annotation and collaboration. A loopback preview serves only this synthetic HTML asset, with no filesystem browsing or uploads. The page permits the library's canonical Google Fonts resources; workflow state and credentials have no network transport. The updated Prototype and Guide views were observed separately in the Browser, with both canonical light and dark themes rendered. Human review of the interface is ongoing. Independent byte comparisons confirmed that the captured HTML matches the preview source and that both canonical library blocks are unchanged. Three scripts parse; all nine guided cases, 35 free actions and DOM handlers passed smoke checks, including view switching without state loss. Those checks are not real host or signing acceptance evidence.

The repository privacy scan passed 14/14 cases and the staged whitespace check passed. Ripwire reported zero regressions in existing symbols and seven advisory findings in the new throwaway Swift probe (callback reachability and UI setup verbosity). Its test gate found no tracked changed symbols before this capture; that result does not establish prototype coverage.

## Observed environment

Read-only local commands reported macOS 27.2 (build 26B5091g), Apple Git 2.54.0 (Apple Git-157), OpenSSH 10.5p1, Swift 6.4, Codex CLI 0.156.0 and Claude Code 2.1.287. These are observed versions, **not a supported or qualified profile**. Installed tool availability does not establish fresh biometric behavior, security-key support, protected deployment or a second-machine result.

## Primary-source findings

| Candidate or component | Documented or source-inspected property | Still unqualified |
| --- | --- | --- |
| Secure Enclave signing | Apple documents non-exportable P-256 key custody. `biometryCurrentSet` ties access to the enrolled biometric set. Device-unlock authentication reuse defaults to zero. | Per-approval fresh biometric consent, protected enrollment, display binding and portable assurance evidence. An ordinary signature does not itself attest these properties. |
| Biometric service architecture | Apple TN3137 limits the data-protection keychain to a user login context, excluding a launchd daemon. | Protected login-context signing/UI component and authenticated communication with any system authority. A root daemon alone is insufficient for that keychain design. |
| Hardware FIDO SSH signing | OpenSSH supports touch presence and requested user verification. Pinned 10.2p1 verification source verifies signatures but does not require signed presence/verification flags; enrollment attestation is opaque to OpenSSH. | Current installed-version behavior, explicit flag enforcement, hardware-origin enrollment evidence and faithful human review. |
| Protected IPC and UI | Hardened Runtime supplies specific injection protections. XPC requirements authenticate received messages; they do not establish trust before a first request reaches a replacement server. Accessibility permission allows apps to control the Mac. | Protected deployment, authenticated peers before sensitive transmission, automation resistance, presentation and consent controls. |
| Same-user SSH agent | OpenSSH warns that another process belonging to the same user can abuse the ordinary agent socket. | A signer behind that socket is not, by itself, the selected protected approval boundary. |

Primary references:

- [Apple: protecting keys with the Secure Enclave](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave), [biometryCurrentSet](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags/biometrycurrentset), [authentication reuse duration](https://developer.apple.com/documentation/localauthentication/lacontext/touchidauthenticationallowablereuseduration).
- [Apple TN3137: On Mac keychains](https://developer.apple.com/documentation/technotes/tn3137-on-mac-keychains), [Hardened Runtime](https://developer.apple.com/documentation/security/hardened-runtime), [XPC peer validation discussion](https://developer.apple.com/forums/thread/837286), [Accessibility permissions](https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac).
- [OpenSSH: FIDO authenticator options](https://man.openbsd.org/ssh-keygen.1#FIDO_AUTHENTICATOR), [pinned security-key protocol](https://github.com/openssh/openssh-portable/blob/V_10_2_P1/PROTOCOL.u2f), [pinned verifier](https://github.com/openssh/openssh-portable/blob/V_10_2_P1/ssh-keygen.c#L2600), [agent socket warning](https://man.openbsd.org/ssh-agent.1#ENVIRONMENT).

These findings are documentation/source evidence. No real authentication or signing was performed.

## Supplementary native primitive probe

The [native Swift probe and runbook](plan-approval-signing-probe.md) were prepared and compiled with the installed Swift 6.4 toolchain: exit 0, no diagnostics. The executable has not run. No key creation, authentication, signing, GUI interaction or enrollment result is claimed.

It proposes a CryptoKit Secure Enclave key with an explicit biometric-or-device-passcode signing constraint, a fresh reconstructed authentication context for each public fixture signature, and context invalidation afterward. Exact macOS password fallback, fresh human confirmation and framework/OS key lifecycle remain unqualified. It is an unprotected supplementary primitive experiment, not a qualified authority or the final branded review interface. Its runbook defines the separate runtime scope needed before any launch or key operation.

## Existing runner seams

Narrow source inspection at `ef2e840548b00ce39c5d5fc6cb59a074288e78aa` found:

- `speckit-pro/speckit_pro_runner/helpers/read_only.py:2777` honors explicit stage selection and `:2808` selects implement after planning completion; the inspected resolver has no full plan-approval validation.
- `speckit-pro/speckit_pro_runner/task_execution.py:25` fingerprints spec, plan and checkbox-normalized tasks. `task_partition.py:249` separately consumes sidecar dispatch metadata. Neither constitutes the full authoritative planning inventory required by ADR 0013.
- `speckit-pro/speckit_pro_runner/execution_control.py:2042` reserves dispatch through ledger and allowance checks; the inspected owner has no plan-approval/current issuer-status check. `:1239` checks observation shape and identifier use rather than authenticated human capture.

These are future implementation seams, not changes made by this prototype.

## Qualification still required

The shared [acceptance matrix and workflow blueprint](https://github.com/racecraft-lab/racecraft-plugins-public/blob/6dd0700b80034993aa8d9ec1bac640d97bf6fdc7/docs/ai/research/speckit-pro-health-plan-approval-provenance.md#shared-acceptance-matrix) remains the acceptance baseline. Its entries are obligations, not observed passing cases.

| Required evidence | Current status |
| --- | --- |
| Protected bootstrap, reviewer identity mapping, key enrollment, rotation, revocation, recovery and independent second-machine trust | Human choices and live qualification pending. |
| Exact supported platform/tool versions, capture modes, signed encoding and signature policy | Pending; environment observations are not support claims. |
| Agent cannot replace UI, signer, verifier, authoritative inventory, policy, trust/lifecycle store or use an unchecked valid-authority dispatch path | Pending; an editable HTML simulation cannot establish this property. |
| Faithful inert final review, separate finding consent and final confirmation on Claude Code and Codex | Pending controlled human evidence on both products. |
| Cancellation/interruption, changed revision, fabricated replies, absent presence, altered display/policy and untrusted/self-enrolled keys | Pending live adversarial cases. |
| Immutable checked bytes/settings through issuance, commit, admission and actual task use; concurrent review and race cases | Pending protected enforcement demonstration. |
| Authenticated current issuer status at issuance, admission and every task dispatch; rollback, outage, replay, revocation and supersession | Transport/lifecycle design and live cases pending; no offline fallback. |
| Missing private evidence or trust fails closed without exporting private originals | Pending selected retention and evidence-verification profile. |
| Unchanged approval transferred to another independently enrolled machine | Pending actual second-machine enrollment and qualification. |
| Headless canary admission | Unresolved in [Canary: fixture, variants, receipt, budget, release gate](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1028). A test issuer, reusable real fixture approval and split gate remain alternatives, not accepted exceptions. |

No matrix row is green on the strength of this demo. The health-program feasibility claim and [Definition of done: confirm and complete](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1029) remain blocked by this open qualification ticket.

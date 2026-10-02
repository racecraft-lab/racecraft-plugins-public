# Local plan-approval authority: prototype checkpoint

Date: 2026-10-02. Status: incomplete; no qualified capture or enforcement profile.

Decision ticket: [Prototype: qualify the local plan-approval authority](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1034), within [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Purpose and human decisions

Explore the review and authority lifecycle without changing shipped plugin behavior. ADRs [0013](../../adr/0013-plan-approval-record.md) and [0015](../../adr/0015-local-plan-approval-authority.md) remain unchanged.

The human chose **one reviewer initially**, explicitly enrolled on each machine; account or repository access supplies no reviewer authority. The human then selected **Secure Enclave with fresh per-approval biometric confirmation** as the first signer candidate to investigate. This is not a qualified signer selection or permission to create keys.

The human requires this prototype to run on **the current Mac using the existing user account**; another computer is unavailable. Separate review/agent login isolation is not selected. Same-login protection against agent automation remains a qualification gap, and actual second-machine transfer cannot be qualified with the available environment. Simulating transfer does not meet that requirement.

The human explicitly selected **password confirmation fallback** when biometric confirmation is failed or unavailable. The exact supported macOS API/policy and fresh per-approval human provenance for that fallback remain unqualified. Password fallback is a requested candidate property; it does not silently admit cached authentication or establish human origin by itself.

The human also requires **the prototype and final review implementation to use the existing speckit-pro HTML artifact library's style and brand**. The HTML prototype must embed the canonical brand and head blocks from `speckit-pro/artifact-gallery/brand-kit.css` and `theme-toggle.html` without modifying them, following its [single-file contract](../../../speckit-pro/artifact-gallery/SPA-CONTRACT.md) and [brand voice](../../../speckit-pro/artifact-gallery/brand-voice.md). The interactive review is the default area; setup, instructions, limitations and scenario/model tools belong in separate supporting areas. This is a requirement for the future protected review interface, not authorization to ship that implementation in this ticket.

No signing, enrollment, service installation, status transport or private-data scope has been authorized by these design choices.

The [throwaway review demo](plan-approval-authority-prototype.html) is a design simulation. Its clicks, signatures, identities, status responses, enrollment and execution are modeled synthetic events. They do not establish human provenance, hardware protection, authenticated current status, host enforcement, or security qualification.

The human requested the demo in the in-app Browser for annotation and collaboration. A loopback preview serves only this synthetic HTML asset, with no filesystem browsing or uploads. The page permits the library's canonical Google Fonts resources; workflow state and credentials have no network transport. The initial Prototype and Guide views were observed separately in the Browser, with both canonical light and dark themes rendered. Human review of the interface is ongoing. Initial byte comparisons confirmed that the captured HTML matched the preview source and that both canonical library blocks were unchanged. Three scripts parsed; all nine guided cases, 35 free actions and DOM handlers passed smoke checks, including view switching without state loss. Those checks are not real host or signing acceptance evidence.

The repository privacy scan passed 14/14 cases and the staged whitespace check passed. Ripwire reported zero regressions in existing symbols and seven advisory findings in the new throwaway Swift probe (callback reachability and UI setup verbosity). Its test gate found no tracked changed symbols before this capture; that result does not establish prototype coverage.

## Actor-oriented information architecture

The human reported difficulty understanding what the actor should do and requested current information architecture research plus an agent team to propose and implement a revision. The [research report](../research/plan-review-information-architecture.md) draws on current GOV.UK, USWDS, NN/g and W3C primary guidance. A separate actor audit identified missing role/goal, simultaneously exposed stages, out-of-order actions, unclear consequences and essential material filed as help.

The [implemented proposal](plan-review-information-architecture.md) is a focused **Read the plan → Decide each finding → Check and confirm** journey, followed by a completion receipt. Implementation, Scenarios and About are separate areas. Full frozen material remains inspectable inside the review. The existing model supplies action eligibility; moving between screens does not supply consent. The Browser walkthrough observed separate choices, rejection and editing, explicit confirmation, separate implementation and ordered task actions, withdrawal with one renewal action and receipt retention, cancellation with and without an earlier receipt, changed-plan recovery with new decisions, and both themes. Independent review corrected cancellation and recovery gaps; ephemeral checks cover all nine cases and 35 actions. Final comparisons confirm unchanged pure model and canonical library blocks, and the preview matches the captured HTML. Human comprehension and security qualification remain unmeasured.

## Simplified language and next-action paths

The human reported that the improved review still used difficult terminology and requested ASD-STE100 research with an agent team and Tavily. The human then added review-to-remediation and review-to-implementation UX to that research scope. The team retrieved the complete official Issue 9 and current primary interface guidance. The [language report](../research/plan-review-simplified-language.md) distinguishes short-sentence rules from full dictionary and grammar conformance; the [handoff report](../research/plan-review-handoffs.md) separates published guidance from proposed domain behavior.

The [selected language and handoff proposal](plan-review-language-and-handoffs.md) uses STE-inspired copy with consistent reviewer terms, direct actions and adjacent consequences. Exact technical material remains available in the review. The rejected-issue path explicitly ends the review and, where applicable, withdraws the earlier approval before preparing an unsent change-request draft. The next actor changes the plan outside the demo; a revised plan requires fresh review choices. The accepted path keeps approval, separate implementation admission and each task start distinct. No task completion is inferred from a start record.

Browser verification observed rejection followed by an unsent selectable draft, distinct reviewed R1/current R2 versions after a sample change, fresh unanswered choices on the new review, direct return to the summary after editing a choice, explicit approval, separate implementation admission with no task started, ordered task-start records and disabled duplicate starts. A replacement review with a rejected issue explicitly withdrew the earlier approval; the draft retained its record as history and implementation became blocked. Selecting the draft selected all 746 characters of the observed read-only packet without sending it. The final interface keeps the consequence text before the End/Withdraw and Approve controls.

The ephemeral prototype check passed all three scripts, actor paths, cancellation-retained snapshot/choices/history, all nine guided cases, all 35 actions, area persistence and inert hostile text. Independent review caught and corrected a draft sentence that incorrectly claimed the plan was unchanged after a sample version change; its focused follow-up found no meaningful blocker. The pure model, exact fixtures, action sequences and canonical library blocks remain unchanged. The preview bytes match the captured source. These are local interface observations and checks, not protected host acceptance evidence.

Both canonical themes were rendered in the Browser; the final preview was returned to the light-theme starting screen for annotation. The privacy scan passed 14/14 cases. Ripwire reported zero quality regressions. Its advisory test gate exited 4 for an untested Markdown heading, `Verification goals`, with no mapped tests; it does not model the prototype's inline JavaScript coverage. The ephemeral checks and Browser walkthrough provide the relevant local interface evidence.

Human comprehension, formal STE conformance and security qualification remain unmeasured. Research and agent review do not establish any of these properties.

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

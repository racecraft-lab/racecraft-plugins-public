# Throwaway native signing primitive probe

**Status: compile-only candidate; runtime and authentication unrun.** This supplementary probe asks whether this Mac can use the exact candidate Secure Enclave access control, with a new authentication context for every residual-finding signature and final confirmation. It does not create a valid plan approval record.

The source is [plan-approval-signing-probe.swift](plan-approval-signing-probe.swift). The browser state prototype is a separate experiment. Neither establishes a protected production approval authority.

The human requires the browser prototype and final protected review interface to use the existing speckit-pro artifact library's canonical brand and theme blocks. This AppKit utility isolates the native signing primitive; it is not the proposed final review interface. System authentication prompts remain operating-system UI.

## What this source proposes

- AppKit shows constant, public synthetic UTF-8 fixture bytes in inert text controls. There are two separate finding decisions, one signature button for each finding, and a final confirmation/signature button. Final confirmation requires both residuals to have been accepted and signed; changing a decision clears its signed state.
- Only an explicit **Create temporary candidate key** button creates a CryptoKit Secure Enclave P-256 key. Creation uses `.biometryCurrentSet`, `.devicePasscode`, `.or`, and `.privateKeyUsage`, with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`. It requests no watch/companion flag and has no broader-policy fallback.
- The source retains the key's wrapped `dataRepresentation` only in actor memory. Each signing attempt reconstructs a key wrapper from it with a **new** `LAContext`, explicitly sets Touch ID reuse duration to zero, evaluates that exact access control for `.useKeySign`, permits one signing call, and invalidates the context on all exits. The creation context is separate and noninteractive. Reconstruction and signing are noninteractive; only the explicit access-control evaluation allows a system dialog.
- The signature covers a fixed domain label, the named decision, the exact fixture bytes and byte count. Final confirmation also includes both finding-signature SHA-256 values. This is a simple experiment encoding, not a production canonical approval format. The app verifies each signature locally and checks that adding changed bytes fails verification.
- Only public fixture messages, public key/signature summaries, and error domain/code appear in the app. There is no export, persistence API, keychain lookup, key deletion, repository/transcript read, external request, subprocess, service, enrollment, installation, or real plugin record in the executable source. It does not collect a password or biometric data.

## Documentation and remaining uncertainty

Context7 was resolved first to `/apple-oss-distributions/security`; its available material covered Security flags but did not establish the CryptoKit wrapper construction. Current Apple Developer Markdown documentation and the installed SDK were then checked directly.

| Point | Evidence and limit |
| --- | --- |
| Create a protected key and supply a context | Apple documents [`init(compactRepresentable:accessControl:authenticationContext:)`](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing/privatekey/init(compactrepresentable:accesscontrol:authenticationcontext:)). The exact selected flag combination is a candidate that must still work on this Mac. |
| Reconstruct with a different context | Apple documents [`init(dataRepresentation:authenticationContext:)`](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing/privatekey/init(datarepresentation:authenticationcontext:)). The source uses this API for every attempt; successful reconstruction/signing has not been observed. |
| Key representation | Apple documents [`dataRepresentation`](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing/privatekey/datarepresentation) as the key's data representation. The source never writes it. This is a nonpersistence proposal, not a measured guarantee about all framework/OS storage, process-memory copies, swap, or cleanup. No keychain item is deliberately added or deleted. |
| Selected constraints | Apple documents [`biometryCurrentSet`](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags/biometrycurrentset), [`devicePasscode`](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags/devicepasscode), and [flag conjunctions/options](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags). Biometrics must be enrolled; changes can invalidate the biometric constraint. The passcode page does not specify exact macOS account-password fallback behavior. |
| Explicit system evaluation | Apple documents [`evaluateAccessControl`](https://developer.apple.com/documentation/localauthentication/lacontext/evaluateaccesscontrol(_:operation:localizedreason:reply:)) and warns that behavior depends on access control, device and profiles. A successful evaluation is not proof of which modality completed it or of fresh password entry. |
| Freshness controls | Apple documents that zero [`touchIDAuthenticationAllowableReuseDuration`](https://developer.apple.com/documentation/localauthentication/lacontext/touchidauthenticationallowablereuseduration) disables Touch ID unlock reuse and that [`invalidate()`](https://developer.apple.com/documentation/localauthentication/lacontext/invalidate()) prevents further context evaluation. These controls and per-attempt isolation are present in the source; they do not establish universal password freshness or companion exclusion without runtime observation. |

The ad-hoc local executable under the existing login is mutable and has no protected enrollment/production identity. It cannot prove sole-reviewer identity, tamper resistance, cross-host authority, or second-machine approval. A copied public signature is not a valid approval record. No entitlement or developer signing identity is added to make unsupported API behavior work.

## Compile only

Run from the throwaway branch's repository root with the installed Xcode toolchain. This invokes the compiler, never the probe. It puts the executable and module cache in a new system temporary directory and does not install or sign with a developer identity.

```text
python3 - <<'PY'
from pathlib import Path
import subprocess
import tempfile

source = Path('docs/ai/prototypes/plan-approval-signing-probe.swift').resolve()
build_dir = Path(tempfile.mkdtemp(prefix='plan-approval-signing-probe-', dir='/tmp'))
command = ['xcrun', 'swiftc', '-swift-version', '6', '-module-cache-path',
           str(build_dir / 'module-cache'), str(source), '-o', str(build_dir / 'probe')]
print('Compiler command:', repr(command))
subprocess.run(command, check=True)
print('COMPILED ONLY:', build_dir / 'probe')
PY
```

Compilation/type checking establishes API availability and source coherence only. It does not establish Secure Enclave availability, creation, nonpersistence, prompt appearance, password fallback, freshness, cancellation behavior, or signing success. No prototype test suite or shipped-plugin suite is required for this throwaway primitive experiment.

## Runtime — requires separate human authorization

**Do not execute the compiled file now.** Runtime permission must explicitly cover launching this local GUI under the existing login, creating one candidate Secure Enclave key/wrapped representation in memory, and invoking system authentication for public synthetic finding/final signatures. Selecting an approach in the design prototype does not authorize those operations.

After that authorization, execute the **specific reviewed temporary executable** with the sole argument `--authorized-public-fixture-only`. Without that exact argument, the program exits before opening its GUI. The argument and in-app checkbox are accidental-launch guards; they are not security boundaries or proof that permission exists.

1. Read the fixture and the unqualified-status labels. Launch itself creates no key and requests no authentication.
2. Check the separate-runtime-authorization checkbox, then click **Create temporary candidate key**. This attempts key creation with a noninteractive creation context. Unsupported hardware, the exact ACL, or a requirement for interactive creation ends that attempt without broadening the policy.
3. Choose **Accept residual finding** or **Request changes** for R1, then press its signature button. This uses a fresh context for this one attempt and may show a system authentication dialog. Cancellation/error records a public error code and leaves that finding unsigned.
4. Repeat for R2. A fresh system interaction must be observed again. Signing R1 is never reused as the R2 context.
5. When both findings are accepted and signed, check the separate final confirmation and press its final signature button. This must use another fresh context. The app shows only the public signature summary and never creates a plugin record.
6. Observe prompt modality and freshness yourself. If there is no fresh prompt, any watch/companion completion, no offered account-password fallback, or an error, mark that behavior **unqualified/unsupported**. Do not substitute `userPresence` or `deviceOwnerAuthentication`, change enrollment, unlock another key, or add entitlements. Do not collect/share credential-dialog screenshots, passwords or biometric material.
7. Close the window. The process exits, releasing its references; there is no persistent-key cleanup call. Framework/OS-level lifecycle and memory cleanup are still unqualified. If any persistent artifact or unexpected effect is suspected, stop; changing/deleting keychain material requires a separate, explicit scope.

Expected effects are a local GUI, one proposed temporary Secure Enclave key/wrapped blob after the creation button, and system authentication dialogs only for selected synthetic signatures. Repeating a signature is a new authentication attempt. Password retry/lockout and device/profile-specific UI behavior have not been exercised. No cross-host or second-machine experiment is included.

## Recorded preparation result

On 2026-10-02 the installed `xcrun swiftc` (Apple Swift 6.4, arm64 macOS 27.2 target) compiled this source with `-swift-version 6` and an isolated temporary module cache: **exit 0, no compiler diagnostics**. The output stayed in a task-specific system temporary directory and was never executed. Source SHA-256: `c665ecc82af542fcb81957bf12f1fe8fd957af4e97413ba55e6d68e5261ff4e1`.

Read-only executable metadata inspection showed a linker-generated ad-hoc signature, no TeamIdentifier and no entitlement output. No developer identity was invoked. A separate read-only source review found no static blocker in context isolation, selected ACL, runtime-effect boundaries or final-confirmation state gates.

All key operations, authentication, GUI behavior, signature/changed-byte checks and freshness/password checks remain **unrun**. Ripwire's working-tree quality advisory had no gating/preexisting regressions; its new-source callback/dead-code and size advisories are not runtime validation. Its test-gate reported zero changed symbols while these new files were untracked; that does not establish coverage. No test suite or prototype execution was run.

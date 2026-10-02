// THROWAWAY PRIMITIVE PROBE. Compile only until separate human runtime authorization.
// This source does not produce a plugin approval record or establish reviewer identity.
import AppKit
import CryptoKit
import LocalAuthentication
import Security

let publicFixture = """
PUBLIC SYNTHETIC FIXTURE v1
Plan: add a decorative blue square to an imaginary page.
Reviewer label: sole local reviewer (a fixture label, not verified identity).
R1: the imaginary page has no dark-mode preview.
R2: the imaginary page has no translated square label.
""" + "\n"

func sha256(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

enum ProbeFailure: Error {
    case unsupported(String)
}

struct SignatureSummary: Sendable {
    let signatureDigest: String
    let display: String
}

// The actor owns the wrapped representation; it never writes it or queries the keychain.
actor SigningPrimitive {
    private var wrappedKey: Data?
    private var publicKey: P256.Signing.PublicKey?
    private var accessControl: SecAccessControl?
    private var attempt = 0

    func create() throws -> String {
        guard wrappedKey == nil else { throw ProbeFailure.unsupported("A probe key already exists.") }
        guard SecureEnclave.isAvailable else {
            throw ProbeFailure.unsupported("Secure Enclave access is unavailable. No alternative key is created.")
        }
        var error: Unmanaged<CFError>?
        let flags: SecAccessControlCreateFlags = [.biometryCurrentSet, .devicePasscode, .or, .privateKeyUsage]
        guard let control = SecAccessControlCreateWithFlags(
            nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, flags, &error
        ) else {
            if let error { throw error.takeRetainedValue() }
            throw ProbeFailure.unsupported("The exact candidate access control could not be constructed.")
        }
        let creationContext = LAContext()
        creationContext.touchIDAuthenticationAllowableReuseDuration = 0
        creationContext.interactionNotAllowed = true
        defer { creationContext.invalidate() }
        // Creation is deliberately noninteractive. Failure does not broaden the policy.
        let key = try SecureEnclave.P256.Signing.PrivateKey(
            compactRepresentable: false, accessControl: control, authenticationContext: creationContext
        )
        wrappedKey = key.dataRepresentation
        publicKey = key.publicKey
        accessControl = control
        return "Candidate key created. Wrapped representation stays in process memory.\n"
            + "Public P-256 key (base64): \(key.publicKey.x963Representation.base64EncodedString())\n"
            + "OS-level nonpersistence and fresh password behavior remain UNQUALIFIED."
    }

    func sign(message: Data, reason: String) async throws -> SignatureSummary {
        guard let wrappedKey, let publicKey, let accessControl else {
            throw ProbeFailure.unsupported("Create the explicit candidate key first.")
        }
        attempt += 1
        let thisAttempt = attempt
        // A context and key wrapper are local to ONE attempt, including every retry.
        let context = LAContext()
        context.touchIDAuthenticationAllowableReuseDuration = 0
        context.interactionNotAllowed = true
        defer { context.invalidate() }
        let key = try SecureEnclave.P256.Signing.PrivateKey(
            dataRepresentation: wrappedKey, authenticationContext: context
        )
        guard key.publicKey.x963Representation == publicKey.x963Representation else {
            throw ProbeFailure.unsupported("Reconstruction returned a different public key.")
        }
        context.interactionNotAllowed = false
        guard try await context.evaluateAccessControl(
            accessControl, operation: .useKeySign, localizedReason: reason
        ) else {
            throw ProbeFailure.unsupported("Access-control evaluation did not succeed.")
        }
        // Only the preceding evaluation may authorize this one operation; no second dialog.
        context.interactionNotAllowed = true
        let signature = try key.signature(for: message)
        guard publicKey.isValidSignature(signature, for: message) else {
            throw ProbeFailure.unsupported("Public-key verification failed.")
        }
        let changedMessage = message + Data("CHANGED".utf8)
        guard !publicKey.isValidSignature(signature, for: changedMessage) else {
            throw ProbeFailure.unsupported("Changed-byte negative verification unexpectedly passed.")
        }
        let rawSignature = signature.derRepresentation
        return SignatureSummary(
            signatureDigest: sha256(rawSignature),
            display: "Attempt \(thisAttempt): signature verified; changed-byte verification rejected.\n"
                + "Message SHA-256: \(sha256(message))\n"
                + "DER signature (base64): \(rawSignature.base64EncodedString())\n"
                + "The per-attempt context is invalidated on return. Prompt freshness/modality UNQUALIFIED."
        )
    }
}

@MainActor
final class ProbeDelegate: NSObject, NSApplicationDelegate {
    private let primitive = SigningPrimitive()
    private var window: NSWindow!
    private let output = NSTextView()
    private let runtime = NSButton(checkboxWithTitle: "Separate runtime authorization has been given for this public fixture", target: nil, action: nil)
    private let confirmation = NSButton(checkboxWithTitle: "I approve this synthetic fixture with both residual findings accepted", target: nil, action: nil)
    private let createButton = NSButton(title: "Create temporary candidate key (explicit action)", target: nil, action: nil)
    private let finalButton = NSButton(title: "Sign final fixture confirmation (new system authentication)", target: nil, action: nil)
    private var choices: [NSPopUpButton] = []
    private var findingButtons: [NSButton] = []
    private var findingSignatures: [Int: SignatureSummary] = [:]
    private var controls: [NSControl] = []
    private var keyCreated = false
    private var busy = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1020, height: 850),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "THROWAWAY — public fixture signing probe — UNQUALIFIED"
        let stack = NSStackView()
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        window.contentView!.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: window.contentView!.topAnchor, constant: 24),
            stack.bottomAnchor.constraint(equalTo: window.contentView!.bottomAnchor, constant: -24)
        ])
        let intro = NSTextField(wrappingLabelWithString:
            "Question: can this Mac use the exact Secure Enclave candidate with a fresh context for each signature? "
            + "This is a public, synthetic primitive experiment. It creates no valid approval record. "
            + "Password fallback and freshness remain unqualified. No Apple Watch/companion flag is requested.")
        stack.addArrangedSubview(intro)
        let fixture = NSTextField(wrappingLabelWithString: publicFixture)
        fixture.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        fixture.isSelectable = true
        stack.addArrangedSubview(fixture)
        stack.addArrangedSubview(NSTextField(labelWithString: "Exact fixture UTF-8 SHA-256: \(sha256(Data(publicFixture.utf8)))"))
        runtime.target = self
        runtime.action = #selector(refreshControls)
        stack.addArrangedSubview(runtime)
        createButton.target = self
        createButton.action = #selector(createKey)
        stack.addArrangedSubview(createButton)
        for index in 0..<2 {
            let row = NSStackView()
            row.orientation = .horizontal
            row.spacing = 10
            row.addArrangedSubview(NSTextField(labelWithString: "R\(index + 1) decision:"))
            let choice = NSPopUpButton()
            choice.addItems(withTitles: ["Choose a decision", "Accept residual finding", "Request changes"])
            choice.tag = index
            choice.target = self
            choice.action = #selector(decisionChanged(_:))
            let button = NSButton(title: "Sign R\(index + 1) decision (new system authentication)", target: self, action: #selector(signFinding(_:)))
            button.tag = index
            row.addArrangedSubview(choice)
            row.addArrangedSubview(button)
            choices.append(choice)
            findingButtons.append(button)
            stack.addArrangedSubview(row)
        }
        confirmation.target = self
        confirmation.action = #selector(refreshControls)
        stack.addArrangedSubview(confirmation)
        finalButton.target = self
        finalButton.action = #selector(signFinal)
        stack.addArrangedSubview(finalButton)
        let observations = NSTextField(wrappingLabelWithString:
            "Observe each system dialog yourself: fresh biometric, fresh password, unexpected companion, no prompt, or cancellation. "
            + "Do not share or record a password, biometric data, or a screenshot of a credential dialog. "
            + "Any companion completion or missing fresh prompt leaves the candidate unsupported for the chosen policy.")
        stack.addArrangedSubview(observations)
        output.isEditable = false
        output.isRichText = false
        output.font = .monospacedSystemFont(ofSize: 12, weight: .regular)
        output.string = "Compile-only candidate. No key or authentication operation happens on launch.\n"
        let scroll = NSScrollView()
        scroll.hasVerticalScroller = true
        scroll.documentView = output
        output.autoresizingMask = [.width]
        output.textContainer?.widthTracksTextView = true
        stack.addArrangedSubview(scroll)
        scroll.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        scroll.heightAnchor.constraint(greaterThanOrEqualToConstant: 200).isActive = true
        controls = [runtime, createButton, confirmation, finalButton] + choices + findingButtons
        refreshControls()
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    @objc private func refreshControls() {
        for control in controls { control.isEnabled = !busy }
        let authorized = runtime.state == .on
        createButton.isEnabled = !busy && authorized && !keyCreated
        for index in 0..<2 {
            findingButtons[index].isEnabled = !busy && authorized && keyCreated && choices[index].indexOfSelectedItem > 0
        }
        finalButton.isEnabled = !busy && authorized && keyCreated && confirmation.state == .on
            && (0..<2).allSatisfy { choices[$0].indexOfSelectedItem == 1 && findingSignatures[$0] != nil }
    }

    @objc private func decisionChanged(_ sender: NSPopUpButton) {
        findingSignatures[sender.tag] = nil
        confirmation.state = .off
        append("R\(sender.tag + 1) changed; its prior signature and final confirmation are cleared.")
        refreshControls()
    }

    @objc private func createKey() {
        guard runtime.state == .on && !busy && !keyCreated else { return }
        busy = true
        refreshControls()
        Task {
            do {
                append(try await primitive.create())
                keyCreated = true
            } catch { appendFailure(error) }
            busy = false
            refreshControls()
        }
    }

    @objc private func signFinding(_ sender: NSButton) {
        let index = sender.tag
        guard runtime.state == .on && !busy && keyCreated && choices[index].indexOfSelectedItem > 0 else { return }
        findingSignatures[index] = nil
        confirmation.state = .off
        let decision = choices[index].indexOfSelectedItem == 1 ? "accept-residual" : "request-changes"
        let body = "stage=residual-finding\nfinding=R\(index + 1)\ndecision=\(decision)\n"
        performSignature(body: body, reason: "Sign public synthetic R\(index + 1): \(decision).") { summary in
            self.findingSignatures[index] = summary
        }
    }

    @objc private func signFinal() {
        guard finalButton.isEnabled, let first = findingSignatures[0], let second = findingSignatures[1] else { return }
        let body = "stage=final-confirmation\ndecision=approve-synthetic-fixture\n"
            + "R1-decision=accept-residual\nR1-signature-sha256=\(first.signatureDigest)\n"
            + "R2-decision=accept-residual\nR2-signature-sha256=\(second.signatureDigest)\n"
        performSignature(body: body, reason: "Sign final approval of the public synthetic fixture.") { _ in }
    }

    private func performSignature(body: String, reason: String, completion: @escaping (SignatureSummary) -> Void) {
        let message = Data(("THROWAWAY-SIGNING-PROBE-v1\n" + body
            + "fixture-utf8-byte-count=\(Data(publicFixture.utf8).count)\nfixture-begin\n"
            + publicFixture + "fixture-end\n").utf8)
        busy = true
        append("Signing message preview (exact UTF-8, fixed strings; no production canonical format):\n"
            + String(decoding: message, as: UTF8.self))
        refreshControls()
        Task {
            do {
                let summary = try await primitive.sign(message: message, reason: reason)
                completion(summary)
                append(summary.display)
            } catch { appendFailure(error) }
            busy = false
            refreshControls()
        }
    }

    private func appendFailure(_ error: Error) {
        // Show public status/code only; never serialize userInfo or credential material.
        if case ProbeFailure.unsupported(let explanation) = error {
            append("UNSUPPORTED: \(explanation)")
        } else {
            let failure = error as NSError
            append("FAILED: domain=\(failure.domain), code=\(failure.code). No weaker policy or automatic retry.")
        }
    }

    private func append(_ text: String) {
        output.string += "\n" + text + "\n"
        output.scrollToEndOfDocument(nil)
    }
}

guard CommandLine.arguments.dropFirst() == ["--authorized-public-fixture-only"] else {
    print("THROWAWAY probe: runtime is separately gated. Do not run without human authorization. See the adjacent runbook.")
    exit(64)
}
let application = NSApplication.shared
application.setActivationPolicy(.regular)
let delegate = ProbeDelegate()
application.delegate = delegate
application.run()

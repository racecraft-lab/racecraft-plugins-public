# Adversarial review of portable human plan approval

Reviewed: 2026-10-02. Original report commit: `fcf2a114fb0787a4f887f7d30f6f2c37e3fa3c0e`. This ledger accompanies the [corrected research and workflow blueprint](speckit-pro-health-plan-approval-provenance.md).

## Result

Three independent research agents reviewed Codex, Claude Code, and the approval protocol/workflow. The parent checked and consolidated their findings into **11 corrections: three high and eight medium**. The unsupported “smallest complete” wording is also removed as part of the architecture correction. These are research/design omissions and evidence-calibration corrections, not demonstrated exploits in shipped implementation.

The main conclusion survives: the reviewed public evidence does not establish a complete native portable attestation of the actual human interview and exact plan approval on both hosts. This is a bounded finding, not proof that a native design is impossible. Supported transport/authentication options are now represented rather than silently excluded. No architecture or new policy value is accepted by this review; [Plan approval provenance: choose the trusted capture boundary](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1033) remains the human decision.

## Method and evidence

Each lane used Tavily search/extraction and independently checked owning official documentation or pinned first-party source. Context7 was used for the relevant host APIs and WebAuthn. Tavily summaries were discovery aids, not authority. Parent checks included official Claude MCP/hooks documentation, current MCP elicitation, NIST reference-monitor requirements, CWE-367, and RFC 8785.

Original report lines below refer to the reviewed commit, before correction. Overlapping protocol/Claude findings are consolidated; no finding quota was imposed. The existing SDK authorship limitations, Codex native primitive inclusion, and absence of a demonstrated complete shared approval authority were independently corroborated.

## Correction ledger

| ID | Severity | Original lines | Supported finding and correction | Owning evidence |
| --- | --- | --- | --- | --- |
| AR-01 | High | 88–93, 170, 179 | Signer isolation does not protect a mutable validator or bypassable dispatch path. Add the threat model, trusted enforcement/inventory/configuration boundary and bypass qualification. | [NIST reference monitor](https://csrc.nist.gov/glossary/term/reference_monitor) |
| AR-02 | High | 88–90, 105, 124, 138 | Matching artifact bytes do not prove faithful presentation. Add inert typed rendering and isolation of generated HTML from confirmation/signing authority. | [WebAuthn security considerations](https://www.w3.org/TR/webauthn-3/#sctn-security-considerations), [CSP](https://www.w3.org/TR/CSP3/) |
| AR-03 | High | 92, 134, 140–142, 199 | A check can precede changed reads. Bind snapshot assembly, issuance, durable commit and actual dispatch to the checked bytes/settings; add concurrent/path-substitution cases. | [CWE-367](https://cwe.mitre.org/data/definitions/367.html) |
| AR-04 | Medium | 93, 142, 161, 205, 223 | Admission-time status alone leaves long-run authority expiry/outage unclear. Expand the existing freshness choice and active dispatch cases; do not invent a cache lifetime. | [RFC 7662 security considerations](https://datatracker.ietf.org/doc/html/rfc7662#section-4) |
| AR-05 | Medium | 90, 104, 110, 173, 181 | Local deterministic JSON is not an established cross-language signed-byte contract. Require versioned encoding or exact preserved bytes and numeric/Unicode/algorithm vectors. JCS is an option, not an imposed dependency. | [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), original `canonical_json.py:9–16` |
| AR-06 | Medium | 86, 91, 95, 220 | “Smallest complete” and external-versus-first-party framing exclude unqualified local UI/authority and browser-authenticator candidates. Replace with one candidate blueprint and compare local, remote and host-owned options. | [WebAuthn](https://www.w3.org/TR/webauthn-3/), [NIST authentication intent](https://pages.nist.gov/800-63-4/sp800-63b.html) |
| AR-07 | Medium | 12, 46, 88–93, 120–124, 220 | URL elicitation is a documented Claude transport, with protocol/version-specific security rules. Add protected browser transport; reject navigation acceptance/completion as approval and exclude preauthenticated access URLs. | [Claude elicitation](https://code.claude.com/docs/en/mcp#respond-to-mcp-elicitation-requests), [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation#security-considerations) |
| AR-08 | Medium | 10, 34, 44–46, 52, 214 | SDK callback counterexamples do not inventory native prompt controls. Add interaction-required MCP tools, native/SDK distinction and version qualification; retain the portable-proof gap. | [Claude interaction-required tools](https://code.claude.com/docs/en/mcp#require-approval-for-a-specific-tool), [hook decision control](https://code.claude.com/docs/en/hooks#pretooluse-decision-control) |
| AR-09 | Medium | 40–46, 82, 88–89, 221 | Identity-attributed audit/collector candidates were absent. Add native event semantics and account/IdP attribution as supplementary evidence requiring protected ingestion/retention; no plan signature is inferred. | [Claude monitoring](https://code.claude.com/docs/en/monitoring-usage#tool-decision-event), [gateway data flow](https://code.claude.com/docs/en/claude-apps-gateway-deploy#data-flow) |
| AR-10 | Medium | 89, 124, 154, 161, 204–206 | Supported headless question deferral/resume is a capture transport seam. Add its single-call, permission-host, pending-call and retention qualification; injected answers still require independent authority. | [Claude deferred calls](https://code.claude.com/docs/en/hooks#defer-a-tool-call-for-later) |
| AR-11 | Medium | 120, 124, 214 | The inspected Codex core/TUI does not guarantee blocking questions merely through skill invocation or a null timer. Add mode/capture qualification and automatic-empty-result cases. Do not generalize TUI timing to Desktop/custom UI. | [Pinned handler](https://github.com/openai/codex/blob/ca466061d64f0b44f416135c7fd06aa7af850bbc/codex-rs/core/src/tools/handlers/request_user_input.rs#L74), [0.157.1 TUI](https://github.com/openai/codex/blob/rust-v0.157.1/codex-rs/tui/src/bottom_pane/request_user_input/mod.rs#L269) |

All 11 corrections are reflected in the research report and shared future acceptance matrix. Added cases also cover key recovery/rotation, reviewer deauthorization, partial commit/crash, concurrent review generations, live PR changes against frozen review evidence, and task-produced files that also serve as authoritative execution configuration. These derive from the existing approval contract; implementation and live qualification remain outstanding.

## Evidence refresh and limits

- Current official Codex release metadata identifies [0.157.1](https://github.com/openai/codex/releases/tag/rust-v0.157.1), published 2026-09-26. The native/platform/protocol blob identities match the inspected 0.156.0 release. The original installed-version claim was correct; it did not claim 0.156.0 was newest. No runtime upgrade or biometric test occurred.
- Codex direct local UI RPC remains distinct from its host-owned native MCP projection. Ordinary/secret question fields, retained `VerifiedAnswer`, and upstream `requestAttestation` do not establish the reviewed approval contract. Native experimental status, enrollment/display/caller trust and platform restrictions remain material.
- Pinned Claude Python SDK callback/origin source was independently retrieved and matched. Native interactive controls, SDK callbacks, URL navigation, collector events and deferred input now have separate evidence roles.
- A transient Tavily 429 was followed by successful searches. One Tavily extraction returned a false page-not-found result for the Claude MCP page; the owning official page was successfully read through the web tool. The Anthropic compliance API owning endpoint was inaccessible in one lane (403); snippets were not used as proof. No exhaustive claim about inaccessible/private products is made.
- Public source/test definitions and specifications were inspected. Native UI enforcement, deployed Desktop behavior, authenticated collector operation, WebAuthn capture, signer/enrollment operations, race protection and cross-host verification were **not live tested**. No private transcripts/credentials, biometric operations, model evaluations or host/configuration changes occurred.
- Every-plan review, final explicit confirmation, separate remaining-gap dispositions, linked repair/history preservation, a committed portable runner record, separate implement invocation and distinct security consent remain unchanged under ADR 0013. Correcting the report does not qualify an implementation or unblock program completion.

## Artifact validation

- `python3 tests/speckit-pro/unit/test-privacy-scan.py`: 14/14 passed.
- Local Markdown link and whitespace checks: both documents passed.
- `git diff --cached --check`: passed.
- `scripts/classify-docs-validation.py` against the original remote research branch: **skip**; rendered docs, generated-reference inputs and docs-validation contracts did not change.
- `ripwire . --quality-delta --legend=compact`: exit 0, zero regressions/gating findings, 13 existing stale acknowledgments.
- `ripwire . --test-gate --legend=compact`: exit 4, one untested Markdown symbol for this new ledger. This is recorded as a documentation-coverage advisory; no executable source was changed. Local links were checked separately. Neither graph advisory establishes research accuracy or human-approval assurance.

Only the research report and this ledger changed. Plugin, Go, docs-site and live workflow/evaluation suites were not run for this documentation-only correction. Publication references are recorded on the research ticket.

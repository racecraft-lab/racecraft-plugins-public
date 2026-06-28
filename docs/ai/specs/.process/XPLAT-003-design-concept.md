---
topic: "Supply-chain security and consumer trust model"
slug: "xplat-003-supply-chain-security-and-consumer-trust-model"
date: "2026-06-27"
mode: "setup"
spec_id: "XPLAT-003"
source_input:
  type: "file"
  ref: "docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md"
question_count: 7
stop_reason: "natural"
---

# Design Concept: Supply-chain security and consumer trust model

> **Source:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
> **Date:** 2026-06-27
> **Questions asked:** 7
> **Stop reason:** natural

## Goals

- Choose a practical first-release supply-chain baseline for the selected
  Python stdlib runner before XPLAT-004 builds the runner.
- Require source-to-dist integrity evidence for generated Claude and Codex
  payloads.
- Require published checksums and consumer-local checksum verification for
  first release; evaluate signatures, SBOM, and provenance as deferred
  hardening unless this spec proves one must ship before launch.
- Require Python/package and artifact/dependency vulnerability scans that fail on
  actionable high or critical findings, with documented exception handling.
- Define consumer-local verification as runner version/preflight plus checksum
  comparison.
- Limit public docs and release-note claims to controls that are implemented and
  verified.
- Assign selected controls to the downstream spec that owns the surface:
  XPLAT-004 for runner/source controls, XPLAT-007 for generated payload cutover,
  and the appropriate release/docs surface for release automation and wording.
- Keep XPLAT-003 as one decision spike. The advisory size estimate is
  `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}` because this is a
  research/decision slice, not a runtime implementation.

## Non-goals

- Building the Python stdlib runner or adding `speckit-pro-runner` artifacts.
- Porting helpers or changing active Claude/Codex invocation paths.
- Rebuilding generated payloads.
- Implementing CI/release changes in this spec.
- Selecting a compiled runtime fallback; the selected runtime is the Python
  3.11+ standard-library model aligned with Spec Kit / `specify`.
- Requiring signatures, SBOMs, or provenance attestations for first release
  unless XPLAT-003's analysis finds they are necessary.
- Making public native Windows/macOS/Linux support claims before XPLAT-007 UAT.
- Procuring or claiming a formal third-party security audit.

## Grounding And Capability Path

- Capability path: spec context -> repository files; Evidence:
  `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`,
  `docs/ai/research/cross-platform-runtime-inventory.md`,
  `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`,
  `specs/xplat-002-runtime-implementation-options-contract-decision/handoff.md`,
  and
  `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`;
  Confidence: high because all setup decisions are grounded in current local
  roadmap and prior XPLAT artifacts.
- Capability path: repo-local helpers -> reviewability and sizing scripts;
  Evidence: `reviewability-gate.sh setup` returned warn/pass with no blockers,
  and `estimate-spec-size.sh --spike` returned one suggested slice; Confidence:
  high for local scaffold gating.

## Design Tree (Q&A log)

### Q1. For XPLAT-003, what should the first-release security bar decide?

**Branch:** First-release control posture

**Recommended answer:** Practical baseline
> Decide the minimum controls XPLAT-004/XPLAT-007 must implement now: pinned
> Python/package inputs, vulnerability scan policy, generated-payload integrity,
> checksums, consumer verification, and truthful claims; defer heavier
> attestations unless justified.

**Alternatives offered:**
- Maximal controls now: require SBOM, provenance attestations, signatures,
  checksums, scanning, reproducibility, and docs claims before runner work
  starts.
- Policy only: write guidance and defer most concrete controls to
  XPLAT-004/XPLAT-007.

**User's answer:** Practical baseline

---

### Q2. How should XPLAT-003 treat generated Claude/Codex payload integrity for the first release?

**Branch:** Generated payload integrity

**Recommended answer:** Source-to-dist gate
> Require a deterministic rebuild/check path showing generated payloads match
> source inputs and selected runner artifacts; this directly supports
> marketplace trust.

**Alternatives offered:**
- Manifest only: record versions and artifact metadata in manifests without
  requiring a reproducible source-to-dist check yet.
- Full reproducibility: require byte-for-byte reproducible release artifacts
  from a clean build environment now.

**User's answer:** Source-to-dist gate

---

### Q3. Which runner and payload integrity controls should be first-release requirements for the Python runner?

**Branch:** Python runner and generated-payload integrity controls

**Recommended answer:** Checksums now
> Require published integrity metadata plus local verification guidance now; evaluate
> signatures, SBOM, and provenance as explicit deferred hardening unless this
> spec finds they are needed before launch.

**Alternatives offered:**
- Checksums plus SBOM: require checksums and an SBOM for first release.
- Full signing set: require checksums, signatures, SBOM, and provenance
  attestations before XPLAT-004.

**User's answer:** Checksums now

---

### Q4. What vulnerability-scanning policy should XPLAT-003 set for the first release?

**Branch:** Vulnerability scanning and failure policy

**Recommended answer:** Fail on actionable highs
> Require Python runner, package, and artifact/dependency scans with a documented failure
> policy for actionable high/critical findings; allow documented non-actionable
> or tooling false-positive exceptions.

**Alternatives offered:**
- Advisory only: run scans and record output, but do not block release on
  findings yet.
- Zero findings: block on any vulnerability finding at any severity.

**User's answer:** Fail on actionable highs

---

### Q5. What should consumers be able to verify locally after installing the plugin?

**Branch:** Consumer-local verification

**Recommended answer:** Version plus checksum
> Expose a runner preflight/version command and documented checksum comparison
> for packaged artifacts. This is feasible even if marketplaces do not enforce
> signatures.

**Alternatives offered:**
- Version only: consumers can confirm runner version/platform only.
- Cryptographic trust chain: consumers verify signatures or attestations
  locally.

**User's answer:** Version plus checksum

---

### Q6. How strict should XPLAT-003 be about public docs and release-note wording?

**Branch:** Public claim boundaries

**Recommended answer:** Claim only implemented controls
> Allow docs to state runner packaging, checksums, scan policy, and
> local verification only after those controls exist; explicitly forbid claims
> of signing, provenance, reproducible builds, or audit unless implemented.

**Alternatives offered:**
- Aspirational roadmap allowed: docs can describe planned controls as future
  direction if clearly labeled.
- No public claims: avoid all supply-chain wording until XPLAT-007.

**User's answer:** Claim only implemented controls

---

### Q7. Where should XPLAT-003 assign first-release controls?

**Branch:** Downstream ownership and handoff

**Recommended answer:** Split by responsibility
> Assign runner/source controls to XPLAT-004, helper/payload cutover checks to
> XPLAT-007, and release automation/docs wording to the earliest downstream spec
> that owns that surface.

**Alternatives offered:**
- All to XPLAT-004: make the runner foundation implement every selected
  control.
- All to XPLAT-007: keep XPLAT-004 focused on the runner and defer all trust
  controls to final cutover.

**User's answer:** Split by responsibility

## Open Questions

- **What:** Exact vulnerability scanning commands, data sources, and exception
  record shape.
  **Why deferred:** The interview selected the policy; tool choice needs plan
  research against the Python stdlib runner and packaged-payload path.
  **Suggested next step:** Resolve in `$speckit-clarify` and `$speckit-plan`.
- **What:** Exact checksum file naming, manifest location, and generated-payload
  integrity metadata shape.
  **Why deferred:** The interview selected first-release checksum and
  source-to-dist requirements; file layout belongs in planning.
  **Suggested next step:** Define in the XPLAT-003 contract/data model.
- **What:** Whether SBOM, signatures, or provenance must move from deferred
  hardening into the first-release gate.
  **Why deferred:** The user chose checksums now, with these controls evaluated
  as hardening unless evidence proves they are needed before launch.
  **Suggested next step:** Evaluate explicitly in research and record the final
  first-release/deferred boundary.

## Recommended Next Step

Run setup to completion, then execute:

```bash
$speckit-autopilot docs/ai/specs/.process/XPLAT-003-workflow.md
```

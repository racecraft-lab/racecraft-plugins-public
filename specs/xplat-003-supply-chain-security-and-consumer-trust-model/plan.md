# Implementation Plan: Supply-Chain Security and Consumer Trust Model

**Branch**: `codex/xplat-003-supply-chain-security-and-consumer-trust-model` | **Date**: 2026-06-27 | **Spec**: `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`

**Input**: Feature specification from `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`, setup design concept from `docs/ai/specs/.process/XPLAT-003-design-concept.md`, and plan prompt from `docs/ai/specs/.process/XPLAT-003-workflow.md`.

## Summary

XPLAT-003 is a decision spike that records the first-release supply-chain and consumer-trust baseline for the Go native `speckit-pro-runner` selected by XPLAT-002. The plan produces decision artifacts only: no runner implementation, helper port, generated payload rebuild, release workflow edit, or public native-support claim.

The first-release baseline is:

- Source-to-dist integrity evidence for generated Claude and Codex payloads.
- SHA-256 checksums for packaged runner artifacts in `scripts/speckit-pro-runner.sha256`.
- A runner artifact manifest at `scripts/speckit-pro-runner.manifest.json`.
- Vulnerability scanning that fails readiness on unresolved actionable high or critical findings, with documented exceptions for non-actionable findings.
- Consumer-local verification through runner identity/preflight plus platform-native checksum comparison.
- Public docs and release notes limited to controls that are implemented and verified.
- Split ownership: XPLAT-004 owns runner/source/artifact controls, XPLAT-007 owns generated payload cutover, consumer guidance, native UAT, and public claim readiness, and release automation owns publication-time evidence only when a later spec wires it in.

## Technical Context

**Language/Version**: N/A for this phase. Downstream runner implementation is Go native binary per XPLAT-002, but XPLAT-003 does not add Go code.

**Primary Dependencies**: Existing repository Markdown and SpecKit helper scripts only. No new runtime dependency.

**Storage**: Checked-in specification artifacts under `specs/xplat-003-supply-chain-security-and-consumer-trust-model/`.

**Testing**: Static/spec validation only for this phase: marker counts, spec-index freshness, diff whitespace, and diff scope review.

**Target Platform**: Decision applies to future packaged native runner artifacts for Windows, macOS, and Linux, but this phase does not build or claim native platform support.

**Project Type**: Claude Code and Codex plugin marketplace decision artifact.

**Performance Goals**: N/A. Release-readiness evidence must be deterministic and reviewable, not performance-bound.

**Constraints**:

- One decision spike, not implementation.
- Use XPLAT-001 supply-chain rubric and XPLAT-002 Go runner handoff.
- Do not edit `.github/workflows/release.yml` or other release automation in XPLAT-003.
- Do not build `speckit-pro-runner`, port helpers, change active invocation paths, or rebuild generated payloads.
- Do not claim signatures, SBOMs, provenance/attestations, reproducible builds, formal audit, marketplace-enforced verification, cryptographic trust-chain verification, or native platform support before those controls are implemented and verified.

**Scale/Scope**: One spec directory; 0 production LOC; decision records and contracts only.

**Reviewability Budget**: Setup gate was warn/pass: `reviewable_loc=250`, `production_files=4`, `total_files=10`, `primary_surface_count=2`, warning `primary surfaces 2 exceeds warn threshold 1`, no blockers. XPLAT-003 remains one decision spike because it records one security/trust model and assigns downstream controls without implementation changes.

## Declared File Operations

- MODIFIED specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md
- NEW specs/xplat-003-supply-chain-security-and-consumer-trust-model/quickstart.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Result |
|---|---|---|
| Plugin Structure Compliance | No runner artifacts, generated payload changes, plugin invocation changes, or release workflow changes. | Pass: phase outputs are spec artifacts only. |
| Script Safety | Future commands are recorded as policy or verification commands only; no helper implementation lands here. | Pass: contracts describe evidence shapes and do not add scripts. |
| Test Coverage Before Merge | Static validation must prove marker cleanliness, spec-map freshness, whitespace health, and diff scope. | Pass pending validation commands in `quickstart.md`. |
| Conventional Commits | No commit in this phase. | N/A. |
| KISS, Simplicity, YAGNI | First release uses the minimum truthful trust baseline; heavier controls remain deferred unless promotion evidence appears. | Pass. |
| Reviewability | Setup warning for two primary surfaces is recorded and accepted. | Warn/pass, not blocking. |

## Project Structure

### Documentation (this feature)

```text
specs/xplat-003-supply-chain-security-and-consumer-trust-model/
|-- SPEC-MOC.md
|-- checklists/
|   `-- requirements.md
|-- contracts/
|   `-- supply-chain-control-contract.md
|-- data-model.md
|-- plan.md
|-- quickstart.md
|-- research.md
`-- spec.md
```

### Source Code (repository root)

```text
No source-code changes in XPLAT-003.
No changes under speckit-pro/, dist/, docs-site/, .github/, or release metadata.
```

**Structure Decision**: XPLAT-003 keeps all phase outputs inside the XPLAT-003 spec directory. Downstream implementation specs may use this plan as input, but this phase does not create implementation files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Setup reviewability warning: two primary surfaces | The decision must assign controls to both process/docs surfaces and future runner/adapter ownership without implementing either surface. | Splitting the decision would scatter one trust model across multiple specs and make first-release claims harder to audit. |

## Phase 0 Research

`research.md` records:

- XPLAT-001 supply-chain rubric mapping.
- XPLAT-002 Go native runner handoff implications.
- First-release versus deferred hardening decisions.
- Vulnerability actionability and exception policy.
- Consumer-local verification boundary.
- Public claim allowed/prohibited language boundary.

Open research result: no deferred control is promoted to first-release required in XPLAT-003. Checksums, manifest, scan policy, source-to-dist evidence, consumer verification, and truthful claims are enough for the first public release baseline.

## Phase 1 Design Artifacts

`data-model.md` defines the decision entities: control decision, owner assignment, artifact manifest, checksum entry, source-to-dist evidence, vulnerability scan evidence, exception record, public claim boundary, and release-readiness evidence.

`contracts/supply-chain-control-contract.md` defines the normative evidence shapes for downstream specs:

- Control decision records.
- SHA-256 checksum file format.
- Runner artifact manifest fields.
- Runtime-info/preflight artifact-integrity fields.
- Source-to-dist evidence record.
- Vulnerability exception record.
- Public claim audit record.

`quickstart.md` gives a reviewer path and static validation commands for this phase.

## Downstream Handoff

| Surface | Owns | Acceptance gate from XPLAT-003 |
|---|---|---|
| XPLAT-004 | Runner source, Go modules/toolchain policy, native artifact build inputs, checksum generation, manifest generation, applicable runner/source/artifact vulnerability scans, runtime-info/preflight artifact-integrity fields. | Runner-foundation readiness fails when required evidence is missing, stale, or has unresolved actionable high/critical findings. |
| XPLAT-007 | Generated Claude/Codex payload source-to-dist gate, generated drift evidence, consumer verification guidance, native UAT evidence, public docs/release-note claim boundaries, public claim audit. | Public cutover and claims fail when evidence, checksums, manifest, scan summaries/exceptions, consumer guidance, preflight/version evidence, public-claim audit, or native UAT evidence is missing or stale. |
| Release automation | Publication-time evidence once later specs wire it in. | Not edited in XPLAT-003; later specs must implement release gates before public release claims rely on them. |
| Public docs and release notes | Implemented-and-verified claim wording only. | Claims about unimplemented signing, SBOMs, provenance, reproducibility, audit, marketplace-enforced verification, cryptographic trust-chain verification, or native platform support are rejected or rewritten as deferred roadmap language. |

## Re-check After Design

| Check | Result |
|---|---|
| First-release controls have owners | Pass: all baseline controls map to XPLAT-004, XPLAT-007, or later release/docs surfaces. |
| Deferred controls remain explicit | Pass: signatures, SBOM, provenance/attestations, reproducible builds, formal audit, marketplace-enforced verification, and cryptographic trust-chain verification remain deferred unless promotion evidence appears. |
| No implementation scope slipped in | Pass: plan artifacts describe controls and evidence only. |
| Public claim boundary is strict | Pass: only implemented-and-verified controls may be claimed. |

# UAT Runbook: xplat-003-supply-chain-security-and-consumer-trust-model

| Field | Value |
|-------|-------|
| Spec | xplat-003-supply-chain-security-and-consumer-trust-model |
| Branch | codex/xplat-003-supply-chain-security-and-consumer-trust-model |
| PR | [racecraft-lab/racecraft-plugins-public#267](https://github.com/racecraft-lab/racecraft-plugins-public/pull/267) |
| Generated from | 2026-06-27T18:13:05Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Check | Command |
|-------|---------|
| Marker scan | `bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh all specs/xplat-003-supply-chain-security-and-consumer-trust-model` |
| Task gate | `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/xplat-003-supply-chain-security-and-consumer-trust-model` |
| Spec index freshness | `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` |
| Whitespace check | `git diff --check` |
| Structural suite | `bash tests/speckit-pro/run-all.sh --layer 1` |

## Per-Story Acceptance Tests

### US-1: Maintainer Reviews Trust Baseline (Priority: P1)

- [ ] Read `spec.md`, `data-model.md`, and `contracts/supply-chain-control-contract.md`.
- [ ] Confirm actionable high/critical findings are treated as release blockers only when they affect shipped or release-affecting XPLAT boundaries.
- [ ] Confirm signatures, SBOMs, provenance, reproducible builds, formal audit, marketplace-enforced verification, and native trust-chain claims remain deferred until implemented and verified.
- [ ] Confirm public docs/release notes may claim only implemented-and-verified controls.

### US-2: Implementer Maps Controls To Owner Specs (Priority: P1)

- [ ] Read `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`.
- [ ] Confirm XPLAT-004 owns Python interpreter discovery, `specify` discovery, stdlib-only policy, source-integrity checks, and installed-cache launch proof.
- [ ] Confirm XPLAT-007 owns Claude/Codex payload cutover, bundled-agent completeness, autoheal behavior, active Python validation gates, and full platform UAT.
- [ ] Confirm no XPLAT downstream item is allowed to use Go, Rust, Zig, native compiled binaries, or Bash/PowerShell as the shipped runtime fallback.

### US-3: Consumer Understands Local Verification And Limits (Priority: P2)

- [ ] Read `quickstart.md` and `platform-user-journeys.md`.
- [ ] Confirm the consumer journey says Python 3.11+ is inherited from Spec Kit / `specify`, while installed-plugin launch behavior still needs XPLAT-004/XPLAT-007 proof.
- [ ] Confirm checksum and payload-freshness verification remain manual until release automation or marketplace enforcement is implemented.
- [ ] Confirm no public Windows, macOS, or Linux support claim is allowed before the platform UAT evidence exists.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| US-1: Maintainer Reviews Trust Baseline | Confirm blocker/deferred-control policy and public-claim limits in the spec, data model, and contract. |
| US-2: Implementer Maps Controls To Owner Specs | Confirm XPLAT-004 and XPLAT-007 own the remaining implementation, install, autoheal, validation, and UAT gates. |
| US-3: Consumer Understands Local Verification And Limits | Confirm consumer guidance states the inherited Python prerequisite, manual verification limits, and native-support claim boundary. |


## Negative-Path Tests


- A vulnerability scan reports a high or critical finding that is not actionable because it is unreachable, false positive, or already mitigated by the packaged artifact boundary.
- A vulnerability scan reports a high or critical finding in repo-only, test, archive, docs-only, or other non-shipped paths that are outside the XPLAT runtime trust boundary.
- Vulnerability scan evidence was clean when produced, but a source revision, dependency snapshot, toolchain, build input, generated artifact, scanner version, vulnerability database timestamp, advisory status, severity, exploitability, or release boundary changed before readiness review.
- A vulnerability exception was approved for one release but the affected artifact, dependency graph, platform, toolchain, scanner database, advisory status, severity, exploitability, or compensating control changed before the next release.
- Generated Claude and Codex payloads drift from their source inputs after the runner or verification metadata changes.
- Checksum or runner manifest metadata exists in XPLAT-004 outputs but is not present, equal, and fresh in both generated Claude and Codex payload roots before XPLAT-007 cutover.
- Published checksum metadata is missing, stale, or does not match a packaged runner artifact.
- A public release or trust claim depends on release automation that has not yet recorded downstream acceptance evidence proving the publication gate is implemented and wired into the release path.
- Consumer checksum guidance exists for one platform family but not for every target platform artifact that XPLAT-007 intends to claim after UAT.
- Public release wording is prepared before XPLAT-007 native-platform UAT or before the selected controls are implemented.
- A downstream implementation attempts to add signing, SBOM, provenance, reproducible-build, or audit language without corresponding implementation evidence.
- A marketplace install path does not automatically enforce checksums, so consumer-local verification must remain manual and clearly documented.
- A consumer computes a packaged runner artifact hash that differs from the
  matching published checksum entry.
- Only some platform artifacts have current checksum, manifest, scan,
  preflight, native UAT, source-to-dist, and claim-audit evidence while another
  intended or claimed platform artifact is missing, stale, mismatched, or
  unpublished.
- Release-readiness or public-claim audit evidence exists only in expiring
  logs, raw workflow output, or unretained generated artifacts without a
  durable non-sensitive summary.

## Self-Review Findings

**Tests executed:** Project build/typecheck/lint/unit/integration commands are N/A for this decision-spec lane. Static and shell verification ran in this session: `count-markers`, G7 validation, spec-index check, `git diff --check`, reviewability task gate, and `bash tests/speckit-pro/run-all.sh`. Raw real-path suite: `3633/3634`, with only a dynamic-local-identity privacy false positive from pre-existing DOC-014 public schema content. Final suite with neutral logical `PWD`: `3634/3634` passed.
**Edge cases:** XPLAT-003 has no runtime code paths. Non-happy trust cases are documented in spec artifacts: stale scan evidence, checksum mismatch, unavailable verification metadata, missing publication evidence, partial artifact publication, and overclaiming unimplemented controls. No `[edge-case-gap]` markers remain.
**Requirements matched:** All 20 tasks are complete and G7 reports `20/20`. Tasks trace the maintainer control decision, downstream ownership handoff, consumer verification boundary, and verification commands. No orphan task or requirement found in the final analyze pass.
**Follow-up & tidiness:** Deferred controls are intentional roadmap language inside XPLAT-003 artifacts: signatures, SBOM, provenance/attestations, reproducible builds, formal audit, marketplace-enforced verification, trust-chain verification, and native-support claims remain deferred until downstream specs implement and verify them. No placeholder, gap, critical/high/medium/low, or clarification markers remain. Diff scope has no runner code, generated payload, release workflow, or public claim-surface changes.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; no data migration is expected because XPLAT-003 changes decision and process artifacts only.

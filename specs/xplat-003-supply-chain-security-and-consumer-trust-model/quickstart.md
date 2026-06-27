# Quickstart: Review and Validate XPLAT-003 Plan Artifacts

## Scope Check

XPLAT-003 is a decision spike. A valid phase-3 diff changes only plan artifacts under:

```text
specs/xplat-003-supply-chain-security-and-consumer-trust-model/
```

Allowed XPLAT-003 decision and process artifacts:

- `plan.md`
- `spec.md`
- `tasks.md`
- `research.md`
- `data-model.md`
- `contracts/`
- `quickstart.md`
- `checklists/`
- `SPEC-MOC.md` only when spec-index refresh requires it

Not allowed in this phase:

- Go runner implementation.
- `speckit-pro-runner` shipped artifacts.
- Helper ports.
- Generated payload rebuilds under `dist/`.
- Release workflow edits.
- Public docs or release-note claims.

## Review Order

1. Read `plan.md` for scope, reviewability warning, constitution checks, and downstream owner split.
2. Read `research.md` for first-release versus deferred control decisions.
3. Read `data-model.md` for decision entities and validation rules.
4. Read `contracts/supply-chain-control-contract.md` for pinned Go/release inputs, checksum, manifest, preflight, source-to-dist, metadata propagation, release automation acceptance, scan freshness, vulnerability exception, consumer checksum guidance, artifact claim readiness, release-readiness retention, and public claim audit evidence shapes.
5. Confirm `spec.md` still contains no unresolved clarification markers.

## Static Validation Commands

Run from the repository root in the XPLAT-003 worktree.

```bash
git rev-parse --abbrev-ref HEAD
git status --short
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-003-supply-chain-security-and-consumer-trust-model
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh findings specs/xplat-003-supply-chain-security-and-consumer-trust-model
bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G6 specs/xplat-003-supply-chain-security-and-consumer-trust-model
bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh tasks specs/xplat-003-supply-chain-security-and-consumer-trust-model
speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"
git diff --check
git diff --name-only
```

Expected branch:

```text
codex/xplat-003-supply-chain-security-and-consumer-trust-model
```

Expected validation result:

- Marker count reports zero gaps.
- Finding marker count reports zero findings after Analyze remediation.
- G6 validation reports zero critical or high findings.
- Reviewability tasks gate may warn because it is a coarse planning heuristic over task path tokens; record warnings and continue only when it has no blockers and the real diff scope remains XPLAT-003 decision/process artifacts.
- Spec index check reports current.
- `git diff --check` reports no whitespace errors.
- Diff scope is limited to the allowed XPLAT-003 decision/process artifacts.

Project test suites are N/A for this pre-implementation decision phase. Do not run generated payload rebuilds or implementation tests as part of XPLAT-003 plan validation.

## Decision Checklist

- First-release baseline includes source-to-dist gate, SHA-256 checksums, artifact manifest, vulnerability scan policy, consumer-local verification, strict public claim boundary, and split ownership.
- Vulnerability scan evidence has objective freshness and staleness blockers: older than 7 calendar days at readiness review, older than covered source/dependency/toolchain/build/artifact/scanner evidence, or unreapproved across a public release boundary.
- XPLAT-004 owns runner/source/dependency/artifact/preflight/checksum/manifest/applicable scan controls and pinned Go/release input evidence.
- XPLAT-004 pinned-input evidence covers Go toolchain version/source, module manifest and `go.sum` or equivalent snapshot, target OS/architecture matrix, build recipe, release inputs, source revision, artifact paths, checksums, and scan evidence refs.
- XPLAT-007 owns generated payload integrity, consumer guidance, public claim readiness, native UAT evidence, and cutover.
- XPLAT-007 source-to-dist evidence must prove checksum and runner manifest metadata is present, equal, and fresh across source paths, generated Claude payload paths, and generated Codex payload paths.
- XPLAT-007 consumer checksum guidance must include Windows, macOS, and Linux command shapes and metadata lookup behavior without Bash, `jq`, source checkout, package restoration, post-cache network access, or pre-UAT native support claims.
- XPLAT-007 consumer checksum mismatch guidance must fail closed, tell users not to rely on the mismatched artifact, and identify the artifact, platform, preflight/identity output, metadata source, expected checksum, computed checksum, plugin version or release boundary, and reporting path to record.
- Release-readiness and public-claim audit evidence must retain durable non-sensitive summaries beyond scan output, with release boundary, control/claim IDs, evidence refs, status, timestamp or source revision, owner, known gaps, and approval/status.
- Public claims must be evaluated per claimed artifact and platform; partial artifact readiness cannot imply broad Windows/macOS/Linux support, and missing/stale/mismatched/unpublished artifacts must be excluded from claims or keep the claim set blocked.
- Release automation remains unchanged in XPLAT-003, and any public claim depending on release automation remains blocked until downstream acceptance evidence proves the publication gate is implemented and wired into release.
- Signatures, SBOM, provenance/attestations, reproducible builds, formal audit, marketplace-enforced verification, cryptographic trust-chain verification, and native support claims remain deferred or explicitly not claimed until implemented and verified.

## Residual Risks To Track Downstream

- The runner does not exist yet, so checksum, manifest, preflight, and scan evidence cannot be produced in XPLAT-003.
- Local Go toolchain probing remains an XPLAT-004 build-environment concern.
- Marketplace-enforced verification is not part of the first-release guarantee.
- Public support claims remain blocked until XPLAT-007 captures native UAT and release-readiness evidence.

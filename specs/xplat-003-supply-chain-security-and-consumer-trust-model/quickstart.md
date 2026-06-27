# Quickstart: Review and Validate XPLAT-003 Plan Artifacts

## Scope Check

XPLAT-003 is a decision spike. A valid phase-3 diff changes only plan artifacts under:

```text
specs/xplat-003-supply-chain-security-and-consumer-trust-model/
```

Allowed phase artifacts:

- `plan.md`
- `research.md`
- `data-model.md`
- `contracts/`
- `quickstart.md`

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
4. Read `contracts/supply-chain-control-contract.md` for checksum, manifest, preflight, source-to-dist, vulnerability exception, and public claim audit evidence shapes.
5. Confirm `spec.md` still contains no unresolved clarification markers.

## Static Validation Commands

Run from the repository root in the XPLAT-003 worktree.

```bash
git rev-parse --abbrev-ref HEAD
git status --short
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-003-supply-chain-security-and-consumer-trust-model
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
- Spec index check reports current.
- `git diff --check` reports no whitespace errors.
- Diff scope is limited to the allowed XPLAT-003 phase artifacts.

Project test suites are N/A for this pre-implementation decision phase. Do not run generated payload rebuilds or implementation tests as part of XPLAT-003 plan validation.

## Decision Checklist

- First-release baseline includes source-to-dist gate, SHA-256 checksums, artifact manifest, vulnerability scan policy, consumer-local verification, strict public claim boundary, and split ownership.
- XPLAT-004 owns runner/source/dependency/artifact/preflight/checksum/manifest/applicable scan controls.
- XPLAT-007 owns generated payload integrity, consumer guidance, public claim readiness, native UAT evidence, and cutover.
- Release automation remains unchanged in XPLAT-003.
- Signatures, SBOM, provenance/attestations, reproducible builds, formal audit, marketplace-enforced verification, cryptographic trust-chain verification, and native support claims remain deferred or explicitly not claimed until implemented and verified.

## Residual Risks To Track Downstream

- The runner does not exist yet, so checksum, manifest, preflight, and scan evidence cannot be produced in XPLAT-003.
- Local Go toolchain probing remains an XPLAT-004 build-environment concern.
- Marketplace-enforced verification is not part of the first-release guarantee.
- Public support claims remain blocked until XPLAT-007 captures native UAT and release-readiness evidence.

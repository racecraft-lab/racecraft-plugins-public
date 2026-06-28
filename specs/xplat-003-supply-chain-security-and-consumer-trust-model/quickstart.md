# Quickstart: Review and Validate XPLAT-003 Plan Artifacts

## Scope Check

XPLAT-003 is a decision spike. A valid Phase 7 implementation diff changes only decision artifacts under:

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

- Python runner implementation.
- Python replacements for tests, evals, payload builders, or release gates.
- Rust, Zig, bundled Node, embedded Python, or other alternate runner
  implementation.
- `speckit-pro-runner` shipped artifacts.
- Helper ports.
- Generated payload rebuilds under `dist/`.
- Release workflow edits.
- Public docs or release-note claims.

## Review Order

1. Read `plan.md` for scope, reviewability warning, constitution checks, and downstream owner split.
2. Read `research.md` for official Claude/Codex platform findings, rejected-runtime implications, and first-release versus deferred control decisions.
3. Read `data-model.md` for decision entities and validation rules.
4. Read `contracts/supply-chain-control-contract.md` for platform capability,
   runtime dependency boundary, install completeness, Python runner
   distribution, pinned release inputs, checksum/source-integrity metadata,
   manifest, preflight, source-to-dist, metadata propagation, release automation
   acceptance, scan freshness, vulnerability exception, consumer verification
   guidance, runner-file claim readiness, release-readiness retention, and public
   claim audit evidence shapes.
5. Confirm `spec.md` still contains no unresolved clarification markers.

## Static Validation Commands

Run from the repository root in the XPLAT-003 worktree. These are current
repository validation commands for this decision-artifact PR only. They are
Bash-backed today and are explicitly transitional; XPLAT-007 must replace active
build/test/eval/payload/release-readiness gates for shipped plugin behavior with
Python standard-library gates before public cutover.

```bash
git rev-parse --abbrev-ref HEAD
git status --short
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh all specs/xplat-003-supply-chain-security-and-consumer-trust-model
bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/xplat-003-supply-chain-security-and-consumer-trust-model
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

- Marker count reports zero gaps, clarifications, and findings.
- G7 validation reports all implementation tasks complete.
- Reviewability tasks gate is a coarse planning heuristic over task path tokens.
  It may warn or produce a size-only block. Record the JSON result and continue
  only when the block is size-only, the actual diff-mode gate has no blockers,
  and the real diff scope remains XPLAT-003 decision/process artifacts.
- Spec index check reports current.
- `git diff --check` reports no whitespace errors.
- Diff scope is limited to the allowed XPLAT-003 decision/process artifacts.

Project test suites are N/A for this decision-artifact implementation phase. Do
not run generated payload rebuilds or runner implementation tests as part of
XPLAT-003 validation. XPLAT-007 remains responsible for replacing Bash-backed
project test/eval/release-readiness gates before any pure-Python support claim.

## Decision Checklist

- First-release baseline includes source-to-dist gate, runner source integrity
  metadata, runner source manifest, vulnerability scan policy, consumer-local
  verification, strict public claim boundary, and split ownership.
- Official Claude Code and OpenAI Codex docs are used only to prove documented
  plugin/skill/hook/MCP/script/executable/custom-agent surfaces, not arbitrary
  user-host runtime availability.
- The amended runtime decision explains why Python is now selected through the
  official Spec Kit / `specify` prerequisite boundary and why Go, Rust, Zig,
  bundled Node, embedded Python, native binaries, or package-restoring
  alternatives are rejected for XPLAT rather than fallback paths.
- Claude Code bundled plugin agents and Codex custom-agent TOML registrations
  are treated as distinct install-completeness surfaces.
- Vulnerability scan evidence has objective freshness and staleness blockers: older than 7 calendar days at readiness review, older than covered source/dependency-policy/build/runner-file/scanner evidence, or unreapproved across a public release boundary.
- XPLAT-004 owns Python runner source, stdlib-only dependency policy,
  interpreter/specify preflight, installed-cache launch proof, generated-payload
  source-integrity evidence, and applicable scan controls.
- XPLAT-004 pinned-input evidence covers Python minimum version policy,
  interpreter discovery order, `specify` discovery/version evidence, source
  revision, payload source path, generated Claude/Codex payload paths, and scan
  evidence refs. Go/Rust/Zig/native-binary fields are not XPLAT evidence.
- XPLAT-007 owns generated payload integrity, consumer guidance, public claim readiness, native UAT evidence, and cutover.
- XPLAT-007 source-to-dist evidence must prove checksum and runner manifest metadata is present, equal, and fresh across source paths, generated Claude payload paths, and generated Codex payload paths.
- XPLAT-007 distribution evidence must prove the Python runner source,
  launcher/preflight metadata, and generated payload metadata are present, equal,
  fresh, and runnable in both generated marketplace payload roots.
- XPLAT-007 Python gate evidence must prove active Bash-backed build, test,
  eval, payload, and release-readiness gates for shipped plugin behavior have
  Python standard-library replacements before final cutover.
- Claude Code can rely on its documented plugin `bin/` executable surface, but
  Codex needs a documented Codex launcher surface such as a skill script,
  plugin-bundled hook, or plugin-bundled MCP command.
- XPLAT-007 consumer verification guidance must include Windows, macOS, and
  Linux preflight/metadata lookup behavior and Python stdlib checksum command
  shapes without Bash, `jq`, PowerShell helper scripts, source checkout, package
  restoration, post-cache network access, or pre-UAT native support claims.
- XPLAT-007 consumer checksum mismatch guidance must fail closed, tell users not to rely on the mismatched runner file, and identify the runner file, platform, preflight/identity output, metadata source, expected checksum, computed checksum, plugin version or release boundary, and reporting path to record.
- Release-readiness and public-claim audit evidence must retain durable non-sensitive summaries beyond scan output, with release boundary, control/claim IDs, evidence refs, status, timestamp or source revision, owner, known gaps, and approval/status.
- Public claims must be evaluated per claimed runner file and platform; partial readiness cannot imply broad Windows/macOS/Linux support, and missing/stale/mismatched/unpublished runner files must be excluded from claims or keep the claim set blocked.
- Release automation remains unchanged in XPLAT-003, and any public claim depending on release automation remains blocked until downstream acceptance evidence proves the publication gate is implemented and wired into release.
- Signatures, SBOM, provenance/attestations, reproducible builds, formal audit, marketplace-enforced verification, cryptographic trust-chain verification, and native support claims remain deferred or explicitly not claimed until implemented and verified.

## Residual Risks To Track Downstream

- The runner does not exist yet, so checksum, manifest, preflight, and scan evidence cannot be produced in XPLAT-003.
- Windows Python launcher discovery and installed-cache invocation remain
  XPLAT-004 proof items. Go, Rust, Zig, bundled Node, embedded Python, and
  native binaries are rejected for XPLAT rather than deferred alternatives.
- Active Bash-backed tests, evals, payload builders, and release-readiness gates
  still exist in the repository today. XPLAT-007 must replace or remove them
  from the active release gate before pure-Python support can be claimed.
- Official platform docs may change; XPLAT-004/XPLAT-007 should refresh
  Claude/Codex platform capability evidence before public runtime or install
  completeness claims.
- Codex installs may appear usable when plugin skills are loaded but custom-agent
  TOML registrations are missing; install validation and autoheal must check
  both.
- Marketplace-enforced verification is not part of the first-release guarantee.
- Release-asset download is not a self-contained marketplace install and is not
  part of the XPLAT runtime model.
- Public support claims remain blocked until XPLAT-007 captures native UAT and release-readiness evidence.

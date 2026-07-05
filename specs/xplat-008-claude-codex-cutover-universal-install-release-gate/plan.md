# Implementation Plan: Claude/Codex Cutover and Universal Install Release Gate

**Branch**: `codex/xplat-008-claude-codex-cutover-universal-install-release-gate` | **Date**: 2026-07-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md`

**Note**: This plan follows the Phase 3 Plan prompt in `docs/ai/specs/.process/XPLAT-008-workflow.md` and the clarified XPLAT-008 specification.

## Summary

Cut over active installed Claude and Codex SpecKit Pro surfaces to direct Python runner invocation, then prove the generated payload, public documentation, native UAT, update, and bounded repair path before public release. The implementation stays in one XPLAT-008 spec with three internal vertical slices because the release gate is only meaningful when active runtime behavior, payload completeness, docs claims, UAT rows, and repair evidence remain traceable together.

## Technical Context

**Language/Version**: Python 3.11+ standard library for `speckit-pro/speckit_pro_runner/`; Markdown/JSON/YAML for skills, agents, hooks, docs, contracts, and process evidence; existing Node/Astro docs-site tooling for docs validation.

**Primary Dependencies**: Python standard library only for installed runtime and runner gates; existing Astro 6.4.6, Starlight 0.40.0, docs-site pnpm scripts, and repository shell test harness for repo-local validation. No new runtime dependency is planned.

**Storage**: Checked-in repository files only: source plugin files, generated `dist/claude/speckit-pro/**` and `dist/codex/speckit-pro/**` payloads, runner manifest/checksum metadata, docs-site Markdown, and feature-local process evidence.

**Testing**: Python runner requests through `<python> -m speckit_pro_runner`; Layer 1 structural validation; focused Layer 4 Python runner/gate tests; active-runtime no-shell/no-jq guard; payload completeness gate; release-readiness gate; docs-site validation when docs change; filled native UAT matrix for Claude and Codex on Windows, macOS, and Linux.

**Target Platform**: Installed Claude Code and Codex plugin caches on native Windows, macOS, and Linux, plus the source checkout release-maintainer workflow.

**Project Type**: Plugin marketplace package with generated Claude/Codex install payloads, Python runner/gate modules, docs-site content, and release process evidence.

**Performance Goals**: First-use scaffold/status/autopilot-dry-run must complete without shell prerequisites on each supported native platform; release gates must deterministically identify missing, stale, extra, path-leaking, or unsupported claim evidence.

**Constraints**: Active installed-runtime surfaces must discover Python `>=3.11`, invoke argv as `[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on stdin, parse one JSON response from stdout, and surface diagnostics without Bash, Git Bash, WSL, PowerShell-specific command language, shell interpolation, redirection, Unix-only paths, or `jq`.

**Scale/Scope**: Two generated payload families, six required platform/product UAT rows, one source-derived payload inventory contract, one release-readiness aggregate, and one bounded repair model. Primary review surface: docs/process. Secondary surfaces: harness/adapter and seed/config. Reviewability budget result: warning accepted.

**Reviewability Budget**: Primary surface `docs/process`; secondary surfaces `harness/adapter`, `seed/config`; projected reviewable LOC `250-500`; projected production files `4-8`; projected total files `10-25`; budget result `warning accepted`.

## Declared File Operations

The plan-phase reviewability estimator parses this block for projected implementation footprint. These entries are planning projections, not files changed by this Plan phase.

- MODIFIED speckit-pro/speckit_pro_runner/gates/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/payloads.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/release.py
- MODIFIED speckit-pro/speckit_pro_runner/gates/active_path_guard.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED speckit-pro/speckit_pro_runner/install_inventory.json
- MODIFIED speckit-pro/skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/skills/speckit-status/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-install/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-status/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-install/SKILL.md
- MODIFIED speckit-pro/hooks/hooks.json
- MODIFIED speckit-pro/codex-hooks.json
- MODIFIED docs-site/src/content/docs/install/claude-code.md
- MODIFIED docs-site/src/content/docs/install/codex.md
- MODIFIED docs-site/src/content/docs/first-run.md
- MODIFIED docs-site/src/content/docs/security-and-trust.md
- MODIFIED docs-site/src/content/docs/troubleshooting.md
- NEW specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md
- NEW specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/release-readiness.md
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-cases.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-cases.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate Result | Plan Handling |
|---|---|---|
| I. Plugin Structure Compliance | Pass | Reuses existing `speckit-pro/` plugin layout; no new plugin or directory convention. |
| II. Script Safety | Pass | No new installed-runtime shell script is planned. Shell allowance remains limited to archive/provenance text, CI dispatch glue that invokes Python gates, and upstream Spec Kit generated helpers. |
| III. Semantic Versioning | Pass | Version consistency is checked, but manual plugin version edits remain out of scope; release-please owns version changes. |
| IV. Test Coverage Before Merge | Pass with required follow-through | Tasks must add focused Layer 4 gate/fixture coverage and run Layer 1 plus the relevant Python runner gates. |
| V. Conventional Commits | Pass | PR title must use the existing conventional commit pattern. |
| VI. KISS, Simplicity & YAGNI | Pass | Uses direct runner invocation, explicit source-derived inventories, and bounded repair. Rejects shell transition wrappers, broad reinstall, speculative crypto claims, and repo-wide shell-word purges. |
| Reviewability Budget | Warning accepted | The setup estimator warning is recorded. Three internal slices are accepted; child specs are deferred unless Tasks or implementation evidence exceeds the coherent review packet boundary. |

**Split Decision**: Remain one XPLAT-008 spec with three internal vertical slices. Create child specs only if Tasks or implementation evidence shows generated payload rebuilds or native UAT artifacts cannot stay under a coherent review packet.

**PR Review Packet Source**: The PR packet must order review as active source/runtime changes, gate and fixture changes, generated payloads, docs/trust wording, UAT/update/repair evidence, then release-readiness output. It must include what changed, why, non-goals, scope budget, traceability, verification, known gaps, and rollback or feature-flag notes.

## Execution Flow

### Slice 1 - Active Installed-Runtime Cutover

Classify active Claude/Codex installed-runtime surfaces and update them to direct Python runner invocation. Seed the active-runtime no-shell/no-jq guard so active skills, agents, hooks, install guidance, generated runtime payloads, and release gates fail when prohibited shell-only behavior returns. Archive/provenance text, tests/fixtures, generated changelog or README prose, minimal CI dispatch glue, and upstream Spec Kit generated `.specify/scripts/bash/` helpers remain out of active-runtime guard scope.

### Slice 2 - Payload, Release, and Public Docs Gates

Rebuild generated Claude and Codex payloads from source and add a source-derived payload completeness contract. Gate release readiness on payload inventory, release/version metadata, bundled agents, hooks, runner files, runner manifest/checksum records, XPLAT-003 trust records, active shell dependency scans, public claim safety, and deterministic dist parity. Public docs and release notes may describe only implemented controls and must not claim signing, SBOM, SLSA, in-toto, reproducible-build guarantees, formal audit/certification, marketplace-enforced verification, vulnerability-free status, or cryptographic trust-chain verification.

### Slice 3 - Native UAT, Update, Repair, and Release Blocker

Fill the feature-local UAT matrix for Claude and Codex on Windows, macOS, and Linux. Each row must cover install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, incomplete-install repair, expected result, actual result, evidence link, operator notes, and pass/fail. Release-readiness must fail on missing, placeholder-only, smoke-only, failing, or claim-incomplete UAT rows. Doctor/autoheal must repair only trusted missing or stale artifacts inside the installed cache and print exact manual remediation for unsafe drift.

## Technical Decisions

| Decision | Outcome | Rationale |
|---|---|---|
| Runtime invocation | Direct Python module invocation through `[resolved_python, "-m", "speckit_pro_runner"]` | Aligns with native Windows/macOS/Linux installed-runtime support and avoids shell parsing. |
| Interpreter discovery | Windows: `py -V:3`, `py -3`, `python`, `python3`; macOS/Linux: `python3`, `python`; accept only Python `>=3.11` | Matches clarified spec consensus and gives diagnostics without a shell fallback. |
| Active guard scope | Guard active runtime paths and release gates, not archive/provenance or upstream generated helpers | Keeps the gate strict where users run installed behavior without rewriting historical evidence. |
| Payload contract | Source-derived expected inventory with explicit transforms and SHA-256/file-tree comparison against committed `dist/**` | Prevents stale dist payloads from becoming the source of truth. |
| Release readiness | Aggregate blocker classes: active shell runtime dependency, incomplete payload, missing bundled agent, stale metadata, unsafe public claim, incomplete UAT evidence, unsafe repair claim | Mirrors success criteria and makes public release blocking deterministic. |
| UAT evidence | Feature-local `.process/uat-matrix.md` with six required product/platform rows | Provides durable reviewer evidence without relying on private context. |
| Repair boundary | Bounded checksum-backed refresh for trusted installed-cache artifacts only; unsafe drift gets manual remediation | Satisfies safe repair without broad reinstall or wipe-copy behavior. |
| Split strategy | Three internal slices under one spec | Preserves review traceability across active surfaces, payload/docs gates, UAT/update/repair, and final release readiness. |

## Project Structure

### Documentation (this feature)

```text
specs/xplat-008-claude-codex-cutover-universal-install-release-gate/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── install-health-repair.schema.json
│   ├── payload-completeness.schema.json
│   ├── release-readiness.schema.json
│   ├── runner-invocation.schema.json
│   └── uat-matrix.schema.json
├── checklists/
│   └── requirements.md
└── .process/              # Implementation/UAT evidence, created after Plan
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/                # Claude installed-runtime skill surfaces
├── codex-skills/          # Codex installed-runtime skill surfaces
├── agents/                # Claude bundled agents
├── codex-agents/          # Codex bundled agents
├── hooks/hooks.json       # Claude hooks
├── codex-hooks.json       # Codex hooks
└── speckit_pro_runner/
    ├── __main__.py
    ├── runtime.py
    ├── envelope.py
    ├── gates/
    ├── helpers/
    ├── install_inventory.json
    ├── speckit-pro-runner.manifest.json
    └── speckit-pro-runner.sha256

dist/
├── claude/speckit-pro/
└── codex/speckit-pro/

docs-site/src/content/docs/
├── install/
├── first-run.md
├── security-and-trust.md
├── troubleshooting.md
└── update-and-rollback.md

tests/speckit-pro/layer4-scripts/
├── test-speckit-pro-gates.py
├── test-speckit-pro-mutation-helpers.py
└── fixtures/xplat-008-release/
```

**Structure Decision**: Use the existing single plugin tree, existing generated `dist/**` payload directories, existing docs-site content tree, and existing Layer 4 runner/gate test layout. Do not add a new runtime package, plugin, external dependency, shell wrapper layer, or child spec at Plan time.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Reviewability warning accepted | XPLAT-008 must keep active installed surfaces, generated payloads, public claims, UAT/update/repair evidence, and release blocking traceable in one release gate. | Child specs now add coordination before the release contract is proven; two slices blur UAT/repair ownership; one unsliced pass is harder to review. |

## Phase 1 Design Re-check

The design artifacts preserve the constitution decisions:

- `research.md` records the direct runner, source-derived inventory, bounded guard scope, UAT matrix, and safe autoheal decisions.
- `data-model.md` defines the records required to keep payload completeness, UAT, release-readiness, and repair evidence structured and reviewable.
- `contracts/` defines machine-readable contracts for runner invocation, payload completeness, release readiness, UAT matrix rows, and install health repair.
- `quickstart.md` gives a maintainer workflow that runs through the three slices without requiring implementation before UAT proof exists.

No new clarification marker remains after design. The remaining open items are implementation-phase evidence fields: actual platform operators, dates, host versions, installed cache paths, and final evidence links in `.process/uat-matrix.md`.

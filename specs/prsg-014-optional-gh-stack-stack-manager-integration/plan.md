# Implementation Plan: Optional gh-stack stack manager integration

**Branch**: `prsg-014-optional-gh-stack-stack-manager-integration` | **Date**: 2026-06-14 | **Spec**: `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`

**Input**: Feature specification from `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`

## Summary

Add an optional stack-manager path for SpecKit split-PR emission and restack. The implementation keeps explicit `gh pr create/edit --base --head --body-file` as the canonical fallback, introduces a shared `detect-stack-manager.sh` decision contract, and uses `gh stack` only after deterministic availability, version, read-only proof, repository compatibility, and topology compatibility checks pass before mutation.

The supported path creates or reconciles PRs through the existing PRSG-012 packet-owned explicit `gh` commands first, then uses proven `gh stack` operations for stack linking, sync, or restack evidence. If any check is missing, unsupported, ambiguous, incompatible, or unsafe before mutation, emission and restack stay on the existing explicit-`gh` path. If a topology-changing `gh stack` command has already been attempted and the outcome is partial or unknown, the flow blocks with recoverable state instead of switching managers.

## Technical Context

**Language/Version**: Bash scripts with Markdown skill/operator guidance

**Primary Dependencies**: `bash`, `jq`, `git`, `gh`; optional `gh stack` GitHub CLI extension via `github/gh-stack`

**Storage**: JSON evidence under feature `.process/` directories, `.process/prs.json`, `autopilot-state.json`, command logs, PR packet artifacts, and local `gh-stack` metadata outside the repo when the extension is used

**Testing**: Shell Layer 4 fixtures with fake `gh` dispatching canonical `gh stack`; Layer 7 replay for orchestration shape; Layer 8 parity fixtures for Claude Code and Codex operator guidance

**Target Platform**: macOS/Linux shell environments running SpecKit Pro from this plugin repository

**Project Type**: CLI/scripted plugin workflow

**Performance Goals**: Detection completes with bounded local/read-only probes before mutation; no network or mutating command is used during support detection except documented read-only `gh stack view --json` proof when repository support exists

**Constraints**: `gh-stack` is optional; fallback is allowed before mutation only; no manager mixing after attempted topology-changing `gh stack`; command plans execute argv arrays only; stdout/stderr evidence is bounded to 120 lines and 16 KiB per stream; `jq` handles JSON state; PRSG-012 packets and PRSG-013 marker order/base topology remain authoritative

**Scale/Scope**: One shared stack-manager decision used by emission and restack, covering create/link/sync/restack safety and evidence only

**Reviewability Budget**: Primary surface harness/adapter; secondary surface docs/process; projected reviewable LOC 325; production files 5; total files 14; within budget

## Declared File Operations

- NEW speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/restack.sh
- NEW speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/multi-pr-emission-state.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/restack-output.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/prs-v2.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-restack.sh
- NEW tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh
- NEW tests/speckit-pro/layer7-integration/fixtures/prsg-014-stack-manager-replay/transcript.jsonl
- NEW tests/speckit-pro/layer8-parity/fixtures/prsg-014-stack-manager-guidance.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | New script and contract stay under existing `speckit-pro/skills/speckit-autopilot/`; tests stay outside the shipped plugin under `tests/speckit-pro/`. |
| II. Script Safety | PASS | New shell entrypoint uses `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, argv arrays, `jq` JSON handling, bounded command capture, and no `eval` or `bash -c` execution. |
| III. Semantic Versioning | PASS | No manual version changes in Plan scope; release-please remains responsible for plugin versioning. |
| IV. Test Coverage Before Merge | PASS | Layer 4 covers detector, emission, restack, schema compatibility, fallback, mutation boundaries, and retry reconciliation; Layer 7/8 cover replay and guidance parity. |
| V. Conventional Commits | PASS | Future implementation PR title can use `feat(speckit-pro): add optional gh-stack stack manager integration`. |
| VI. KISS, Simplicity & YAGNI | PASS | One shared detector serves the two existing callers; supported commands are limited to link, sync, and restack; explicit `gh` fallback remains unchanged for unsupported cases. |

**Initial Gate Result**: PASS. No constitution violations or split exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-014-optional-gh-stack-stack-manager-integration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── stack-manager-decision.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── scripts/
│   │   ├── detect-stack-manager.sh
│   │   ├── multi-pr-emission.sh
│   │   └── restack.sh
│   ├── contracts/
│   │   ├── stack-manager-decision.schema.json
│   │   ├── multi-pr-emission-state.schema.json
│   │   ├── restack-output.schema.json
│   │   └── prs-v2.schema.json
│   └── references/post-implementation.md
└── codex-skills/speckit-autopilot/SKILL.md

tests/speckit-pro/
├── layer4-scripts/
│   ├── test-detect-stack-manager.sh
│   ├── test-multi-pr-emission.sh
│   ├── test-restack.sh
│   └── fixtures/
├── layer7-integration/fixtures/prsg-014-stack-manager-replay/
└── layer8-parity/fixtures/
```

**Structure Decision**: Keep implementation single-copy in `skills/speckit-autopilot/scripts/` and shared contracts in `skills/speckit-autopilot/contracts/`. Codex changes are guidance/parity only, with no duplicated scripts, schemas, or validators.

## Phase 0: Research

Research output: `specs/prsg-014-optional-gh-stack-stack-manager-integration/research.md`.

Resolved decisions:

- `gh stack` support matrix is based on local `gh stack --help`, `gh stack --version`, subcommand help for `view`, `link`, `submit`, `sync`, and `rebase`, plus the `github/gh-stack` project README at `https://github.com/github/gh-stack`.
- Installed local extension evidence: `github/gh-stack v0.0.5`.
- Project README evidence: `gh-stack` is a GitHub CLI extension for stacked PRs, latest release observed as v0.0.5, and GitHub Stacked PRs is private preview. Therefore runtime support must fail closed unless the repository proves enablement with read-only `gh stack view --json` evidence.
- `gh stack view --json` is the only selected read-only proof command.
- `gh stack link` is selected only as a post-packet mutating stack-link command and should prefer PR-number argv after explicit PR create/edit. Branch argv is riskier because the command can push branches, create PRs, and correct base branches itself.
- `gh stack submit` is not selected for PR creation because it prompts or auto-generates PR titles, conflicting with PRSG-012 packet-owned title/body semantics.
- `gh stack sync` is selected only when local stack tracking and `view --json` topology proof are compatible; it fetches, rebases, pushes, and syncs PR state, so it is a mutation boundary.
- `gh stack rebase --upstack <branch>` is version-supported in v0.0.5 and can scope from the current/target branch to the top; it is selected for restack only when local stack topology proof matches PRS/marker order and the subsequent push/sync plan is proven.

## Phase 1: Design & Contracts

Design outputs:

- `data-model.md` defines Stack Manager Decision, Command Plan, Topology Evidence, Command Execution Evidence, and Recoverable Block State.
- `contracts/stack-manager-decision.schema.json` defines the shared decision record that emission and restack reference.
- `quickstart.md` defines deterministic validation scenarios for supported, fallback, blocked, duplicate-retry, supported-restack, fallback-restack, Layer 7 replay, and Layer 8 guidance parity.

Implementation design:

1. Add `detect-stack-manager.sh` as the single pre-mutation detector.
   - Inputs: mode (`emission` or `restack`), operation (`link`, `sync`, `restack`), PRS/marker topology paths, optional command plan output, remote, base, start branch, and fake-command override for Layer 4.
   - Output: JSON matching `stack-manager-decision.schema.json`.
   - It records selected manager, fallback reason, availability, version, repository compatibility, topology compatibility, read-only proof, command plan, mutation boundary, and fallback policy.

2. Extend `multi-pr-emission.sh`.
   - Dry run emits candidate command plans and stack-manager decision evidence.
   - Live mode validates every PRSG-012 packet and PRSG-013 marker checkpoint before any stack-manager mutation.
   - Explicit `gh pr create/edit --base --head --body-file` remains authoritative for PR title/body and base/head metadata.
   - If selected, `gh stack link --base <base> <pr-number>...` runs after explicit PR reconciliation. The first `gh stack link` argv is the no-fallback mutation boundary.
   - Retry reconciles expected slice ID, head branch, base branch, PR number/URL, head SHA, and packet hash before creating or linking.

3. Extend `restack.sh`.
   - Dry run plans existing explicit `gh pr edit --base` operations and stack-manager decision evidence.
   - Apply mode invokes `gh stack rebase --upstack <first-remaining-branch>` plus the proven sync/push step only when `detect-stack-manager.sh` selects `gh-stack`.
   - If detection does not pass before mutation, keep the existing fallback retarget path.
   - After any partial or unknown `gh stack` mutation, output blocked recoverable state with `fallback_allowed=false`.

4. Extend schemas compatibly.
   - Add shared `stack-manager-decision.schema.json`.
   - Add explicit `stack_manager_decision` and `stack_manager_evidence_path` fields to emission/restack evidence.
   - Keep PRS v2 topology-focused; add only an optional evidence path reference if needed.
   - Preserve existing `gh_stack` restack field for compatibility while adding the richer shared decision.

5. Update operator guidance parity.
   - Claude Code post-implementation guidance and Codex autopilot guidance describe the same supported, fallback, blocked, and recovery flows.
   - Guidance points to shared scripts/contracts rather than duplicate Codex implementations.

## Command Capability Matrix

| Command | Local v0.0.5 support | Mutation status | PRSG-014 use |
|---------|----------------------|-----------------|--------------|
| `gh stack --version` | Supported | Read-only | Version evidence. |
| `gh stack view --json` | Supported | Read-only | Required topology/read-only proof. Unparseable output falls back before mutation. |
| `gh stack link --base <base> <pr>...` | Supported | Mutating | Selected after explicit PR packet create/edit, using PR numbers where possible. |
| `gh stack submit --auto` | Supported | Mutating | Not selected because it creates/updates PRs with generated titles and can bypass packet-owned bodies. |
| `gh stack sync --remote <remote>` | Supported | Mutating | Selected only after local stack tracking proof; otherwise fallback. |
| `gh stack rebase --upstack <branch>` | Supported | Mutating | Selected for restack only after topology proof and with recoverable block handling. |
| `gh stack init/add/modify/unstack` | Supported | Mutating or interactive | Out of scope for PRSG-014. |

## Reviewability Estimate

Declared production files: 5. Declared total files: 14. Projected reviewable LOC: 325. Result: within budget. Split decision: keep as one spec because detector, emission, and restack share one decision contract and fallback policy.

## Post-Design Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Planned files remain in existing plugin/test layout. |
| II. Script Safety | PASS | Design forbids joined command execution and requires `jq` plus bounded stdout/stderr capture. |
| III. Semantic Versioning | PASS | No manual version edits. |
| IV. Test Coverage Before Merge | PASS | Fixture matrix covers every support/fallback/block case named by the spec. |
| V. Conventional Commits | PASS | PR title convention is defined. |
| VI. KISS, Simplicity & YAGNI | PASS | Scope is limited to detector, existing emission/restack callers, one shared contract, and guidance parity. |

**Post-Design Gate Result**: PASS.

## Complexity Tracking

No constitution violations.

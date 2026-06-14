# Implementation Plan: Optional gh-stack stack manager integration

**Branch**: `prsg-014-optional-gh-stack-stack-manager-integration` | **Date**: 2026-06-14 | **Spec**: `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`

**Input**: Feature specification from `specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md`

## Summary

Add an optional stack-manager path for SpecKit split-PR emission and restack. The implementation keeps explicit `gh pr create/edit --base --head --body-file` as the canonical fallback, introduces a shared `detect-stack-manager.sh` decision contract, and uses `gh stack` only after deterministic availability, version, read-only proof, repository compatibility, and topology compatibility checks pass before mutation.

The supported path creates or reconciles PRs through the existing PRSG-012 packet-owned explicit `gh` commands first, then uses proven `gh stack` operations for stack linking, sync, or restack evidence. If any check is missing, unsupported, ambiguous, incompatible, or unsafe before mutation, emission and restack stay on the existing explicit-`gh` path. If a topology-changing `gh stack` command has already been attempted and the outcome is partial or unknown, the flow blocks with recoverable state instead of switching managers.

## Technical Context

**Language/Version**: Bash scripts with Markdown skill/operator guidance

**Primary Dependencies**: `bash`, `jq`, `git`, `gh`; optional `gh stack` GitHub CLI extension via `github/gh-stack`

**Storage**: JSON evidence under feature `.process/` directories, including `specs/<feature>/.process/stack-manager/` decision/proof/command/recovery records, `.process/prs.json`, `autopilot-state.json`, command logs, PR packet artifacts, and local `gh-stack` metadata outside the repo when the extension is used

**Testing**: Shell Layer 4 fixtures with fake `gh` dispatching canonical `gh stack`; Layer 7 replay for orchestration shape; Layer 8 parity fixtures for Claude Code and Codex operator guidance

**Target Platform**: macOS/Linux shell environments running SpecKit Pro from this plugin repository

**Project Type**: CLI/scripted plugin workflow

**Performance Goals**: Detection completes with bounded local/read-only probes before mutation; no network or mutating command is used during support detection except documented read-only `gh stack view --json` proof when repository support exists

**Constraints**: `gh-stack` is optional; fallback is allowed before mutation only; no manager mixing after attempted topology-changing `gh stack`; command plans execute argv arrays only; argv elements are non-empty, control-character-free, and bounded to 1024 characters; stack-manager evidence paths are deterministic repo-relative `.process` paths; stdout/stderr evidence is bounded to 120 lines and 16 KiB per stream; `jq` handles JSON state; PRSG-012 packets and PRSG-013 marker order/base topology remain authoritative

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
- NEW tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/README.md
- NEW tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/prompt.txt
- NEW tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/parser-fixture.jsonl
- NEW tests/speckit-pro/layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/expected.json
- NEW tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/README.md
- NEW tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/workflow.md
- NEW tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-teams.sh
- NEW tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-fallback.sh
- NEW tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/expected-equivalence.json
- NEW tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/tolerance.json

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
├── layer7-integration/dispatch-fixtures/22-prsg-014-stack-manager-replay/
└── layer8-parity/04-prsg-014-stack-manager-guidance/
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

- `data-model.md` defines Stack Manager Decision, Command Plan, Stack-Manager Evidence Path, Topology Evidence, Command Execution Evidence, and Recoverable Block State.
- `contracts/stack-manager-decision.schema.json` defines the shared decision record that emission and restack reference.
- `quickstart.md` defines deterministic validation scenarios for supported, fallback, blocked, duplicate-retry, supported-restack, fallback-restack, Layer 7 replay, and Layer 8 guidance parity.

Implementation design:

1. Add `detect-stack-manager.sh` as the single pre-mutation detector.
   - Inputs: mode (`emission` or `restack`), operation (`link`, `sync`, `restack`), PRS/marker topology paths, optional command plan output, remote, base, start branch, and Layer 4 fake-command controls. Fake-command controls are test-only PATH shims or sandbox/fixture executable paths; persisted command plans still record canonical `gh stack`, explicit `gh pr`, `git`, or repo-local validator argv.
   - Output: JSON matching `stack-manager-decision.schema.json`.
   - It records selected manager, fallback reason, `gh_stack.available`, `gh_stack.supported`, `gh_stack.reason`, version/support status, repository compatibility, topology compatibility, read-only proof, command plan, mutation boundary, fallback policy, and deterministic repo-relative evidence path.

2. Extend `multi-pr-emission.sh`.
   - Dry run emits candidate command plans and stack-manager decision evidence.
   - Live mode validates every PRSG-012 packet and PRSG-013 marker checkpoint before any stack-manager mutation.
   - Explicit `gh pr create/edit --base --head --body-file` remains authoritative for PR title/body and base/head metadata.
   - If selected, `gh stack link --base <base> <pr-number>...` runs after explicit PR reconciliation. The first `gh stack link` argv is the no-fallback mutation boundary.
   - Retry reconciles expected slice ID, head branch, base branch, PR number/URL, head SHA, and packet hash before creating or linking.
   - Blocked resume reloads prior stack-manager recovery evidence, supersedes the prior workflow event by deterministic event id, and either resumes through same-manager no-change reconciliation or remains blocked without explicit-`gh` fallback.

3. Extend `restack.sh`.
   - Dry run plans existing explicit `gh pr edit --base` operations and stack-manager decision evidence.
   - Apply mode invokes `gh stack rebase --upstack <first-remaining-branch>` plus the proven sync/push step only when `detect-stack-manager.sh` selects `gh-stack`.
   - If detection does not pass before mutation, keep the existing fallback retarget path.
   - After any partial or unknown `gh stack` mutation, output blocked recoverable state with `fallback_allowed=false`.
   - Resume after a blocked restack must revalidate current stack topology, PR identity, base/head refs, head SHA, and packet identity before any same-manager reconciliation or resumed restack command.

Error classification rules:

- Read-only detection, stack-manager command planning, and topology-proof failures happen before the no-fallback boundary and may select explicit `gh` fallback when every PRSG-012 packet remains valid.
- PRSG-012 packet-validation failures are pre-mutation hard blocks, not stack-manager fallback causes; no `gh stack`, explicit `gh pr create/edit`, or manager switch may run until the packet is regenerated and validates.
- A mutating `gh stack` command that succeeds and matches expected topology records `side_effect_class=planned_mutation`.
- A mutating `gh stack` command that fails with observed branch, PR, base, or metadata side effects records `side_effect_class=partial_mutation` and blocks.
- A mutating `gh stack` command that times out, crashes, returns ambiguous output, or cannot prove no side effects records `side_effect_class=partial_mutation_unknown` and blocks.
- Same-manager no-change reconciliation is the only automated path out of a blocked state, and it must prove current topology, PR identity, base/head refs, head SHA, and packet identity match the safe resume boundary.

Security validation rules:

- Command execution accepts only allowlisted argv shapes: `gh stack view --json`, `gh stack link --base <base> <pr-number|branch>...`, `gh stack sync --remote <remote>`, `gh stack rebase --upstack <branch>`, explicit `gh pr create/edit` packet-owned forms, scoped `git` forms required by emission/restack, and repo-local validator scripts.
- Joined command strings, display strings, and shell-rendered command text are evidence only. They must never be parsed back into argv or executed through `eval`, `bash -c`, `sh -c`, or a shell command string.
- Branch/base refs must pass `git check-ref-format --branch` and stack-manager branch operands must not be option-looking values unless a proven command shape provides an operand delimiter or PR-number operands are used.
- PR body paths must satisfy the PRSG-012 repo-relative body-file contract before capture; evidence paths must satisfy the PRSG-014 repo-relative `.process` path contract before persistence.
- Layer 4 security fixtures must cover malicious branch/base refs, absolute or parent-traversal PR body paths, evidence path traversal, fake CLI override abuse, and display command strings with shell metacharacters.

Reliability evidence and resume rules:

- Stack-manager machine evidence is persisted under `specs/<feature>/.process/stack-manager/`; reader-facing blocked workflow events are written under `docs/ai/specs/.process/<workflow-id>-workflow.md`.
- Evidence paths are repo-relative and derived from stable operation identity: phase, operation, slice id or review order when present, and first mutating command id when present. They must not include timestamps, random temporary names, or absolute host paths.
- The decision record, read-only proof, command execution evidence, and recovery evidence each carry explicit evidence paths so `.process/prs.json`, `autopilot-state.json`, restack output, and workflow evidence can reopen the same records on resume.
- A blocked workflow event id is derived from the stack-manager decision evidence path, selected manager, mutation boundary command id, and next resume boundary. Retried blocked runs supersede the prior event for that id instead of appending ambiguous duplicates.
- Resume after a blocked stack-manager operation first reloads the persisted decision and recovery evidence, revalidates current topology/PRS/packet identity, and only then either resumes the same manager after no-change reconciliation or remains blocked with updated recovery evidence.

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

# Implementation Plan: TACD-002 Capability Discovery Directive and Agent Updates

**Branch**: `tacd-002-capability-discovery-directive-and-agent-updates` | **Date**: 2026-06-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md`

**Note**: The local setup script was run from the TACD-002 worktree with the provided feature directory pinned through supported environment variables because the existing TACD branch name is non-numeric. No branch was created or renamed.

## Summary

TACD-002 applies TACD-001's tool-agnostic capability-discovery decision to active SpecKit Pro runtime guidance. The plan follows the design concept decisions: **"Shared reference"** for the directive, **"Regenerate from source"** for generated payloads, **"Path + confidence"** for evidence, and **"Preserve metadata"** for schema-required identifiers (`docs/ai/specs/.process/TACD-002-design-concept.md`).

The implementation will create or update the shared directive at `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`, point scoped Claude and Codex runtime guidance at the directive or approved equivalents, preserve metadata-only IDs, and refresh generated Claude/Codex payloads through `bash scripts/build-plugin-payloads.sh`. TACD-003 prerequisite/user-facing messaging and TACD-004 deterministic/eval enforcement remain out of scope.

## Technical Context

**Language/Version**: Markdown runtime guidance, TOML Codex agent templates, YAML metadata, generated payload files, and Bash validation scripts in the existing repository.

**Primary Dependencies**: Existing SpecKit Pro plugin structure; existing payload builder `bash scripts/build-plugin-payloads.sh`; existing deterministic verification `bash tests/speckit-pro/run-all.sh`; no new runtime dependency planned.

**Storage**: Repository files only. Source guidance under `speckit-pro/`, generated payload copies under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, and Plan-phase artifacts under `specs/tacd-002-capability-discovery-directive-and-agent-updates/`.

**Testing**: Source/diff review, payload rebuild evidence, second-rebuild idempotence check, and default deterministic suite `bash tests/speckit-pro/run-all.sh`.

**Target Platform**: Claude Code and Codex plugin marketplace runtime guidance, including installed agent surfaces generated from this repository.

**Project Type**: Plugin marketplace guidance and generated runtime payloads.

**Performance Goals**: No runtime performance target; the feature is successful when active guidance chooses by capability, reports evidence compactly, and generated payloads match source.

**Constraints**: Preserve TACD-002 scope only; keep TACD-003 prerequisite/user-facing messaging and TACD-004 enforcement/evals out of scope; preserve schema-required metadata IDs; do not hand-edit `dist/**` as the durable source; projected production files remain 0.

**Scale/Scope**: Six active Claude Markdown agents, six matching Codex TOML agents, the shared directive, narrow active references in `consensus-protocol.md` and `gate-validation.md`, metadata review evidence, and generated payload refresh evidence.

**Reviewability Budget**: Primary surface: docs/process. Secondary surface: harness/adapter only for generated payload refresh evidence. Projected reviewable production LOC: 0. Projected production files: 0. Projected total files may warn because the accepted setup scope intentionally spans multiple active guidance surfaces plus generated copies. Budget result: accepted warning from `docs/ai/specs/.process/TACD-002-design-concept.md`; no blocking split required. Split decision: keep TACD-002 as one active agent-behavior slice; TACD-003 owns prerequisite/user-facing messaging; TACD-004 owns deterministic/eval enforcement.

## Declared File Operations

- NEW speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
- MODIFIED speckit-pro/agents/codebase-analyst.md
- MODIFIED speckit-pro/agents/domain-researcher.md
- MODIFIED speckit-pro/agents/clarify-executor.md
- MODIFIED speckit-pro/agents/checklist-executor.md
- MODIFIED speckit-pro/agents/analyze-executor.md
- MODIFIED speckit-pro/agents/implement-executor.md
- MODIFIED speckit-pro/codex-agents/codebase-analyst.toml
- MODIFIED speckit-pro/codex-agents/domain-researcher.toml
- MODIFIED speckit-pro/codex-agents/clarify-executor.toml
- MODIFIED speckit-pro/codex-agents/checklist-executor.toml
- MODIFIED speckit-pro/codex-agents/analyze-executor.toml
- MODIFIED speckit-pro/codex-agents/implement-executor.toml
- MODIFIED speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/gate-validation.md
- NEW dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
- MODIFIED dist/claude/speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md
- MODIFIED dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md
- MODIFIED dist/claude/speckit-pro/agents/codebase-analyst.md
- MODIFIED dist/claude/speckit-pro/agents/domain-researcher.md
- MODIFIED dist/claude/speckit-pro/agents/clarify-executor.md
- MODIFIED dist/claude/speckit-pro/agents/checklist-executor.md
- MODIFIED dist/claude/speckit-pro/agents/analyze-executor.md
- MODIFIED dist/claude/speckit-pro/agents/implement-executor.md
- NEW dist/codex/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md
- MODIFIED dist/codex/speckit-pro/codex-agents/codebase-analyst.toml
- MODIFIED dist/codex/speckit-pro/codex-agents/domain-researcher.toml
- MODIFIED dist/codex/speckit-pro/codex-agents/clarify-executor.toml
- MODIFIED dist/codex/speckit-pro/codex-agents/checklist-executor.toml
- MODIFIED dist/codex/speckit-pro/codex-agents/analyze-executor.toml
- MODIFIED dist/codex/speckit-pro/codex-agents/implement-executor.toml

Generated `dist/**` entries are declared only as source-derived payload outputs; implementation must regenerate them through `bash scripts/build-plugin-payloads.sh`. The generated shared-reference entries are included because the builder copies `speckit-pro/skills/` into both Claude and Codex payload roots before Codex-specific overlays.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Plugin Structure Compliance | PASS | TACD-002 changes existing plugin guidance and generated payloads without changing plugin layout, manifests, commands, hooks, or skill directory conventions. |
| II. Script Safety | PASS | No new Bash script is planned. Existing builder and verification scripts are used as-is. |
| III. Semantic Versioning | PASS | No manual version edit is planned. Release automation remains responsible for version changes. |
| IV. Test Coverage Before Merge | PASS | Planned verification uses `bash scripts/build-plugin-payloads.sh`, generated diff review, second rebuild idempotence, and `bash tests/speckit-pro/run-all.sh`. TACD-004 owns new deterministic/eval enforcement. |
| V. Conventional Commits | PASS | Commit/PR title will use the repository's Conventional Commit pattern. |
| VI. KISS, Simplicity & YAGNI | PASS | The simplest durable design is the design concept's shared reference with narrow runtime pointers/equivalents. No new abstraction, installer, or enforcement layer is added in TACD-002. |
| Reviewability Budget | PASS with accepted warning | The design concept explicitly accepts the setup warning because TACD-002 is a bounded docs/process behavior-guidance slice with 0 projected production files and no TACD-003 or TACD-004 implementation. |

**PR review packet source**: The PR description must include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback/flags, preserved-ID table, payload refresh evidence, and deferred TACD-003/TACD-004 work.

## Project Structure

### Documentation (this feature)

```text
specs/tacd-002-capability-discovery-directive-and-agent-updates/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── capability-discovery-guidance.md
└── tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
├── agents/
│   ├── analyze-executor.md
│   ├── checklist-executor.md
│   ├── clarify-executor.md
│   ├── codebase-analyst.md
│   ├── domain-researcher.md
│   └── implement-executor.md
├── codex-agents/
│   ├── analyze-executor.toml
│   ├── checklist-executor.toml
│   ├── clarify-executor.toml
│   ├── codebase-analyst.toml
│   ├── domain-researcher.toml
│   └── implement-executor.toml
└── skills/speckit-autopilot/references/
    ├── capability-discovery.md
    ├── consensus-protocol.md
    └── gate-validation.md

dist/
├── claude/speckit-pro/
└── codex/speckit-pro/
```

**Structure Decision**: Use the design concept's shared-reference structure. Source guidance under `speckit-pro/` is authoritative; generated payload roots under `dist/**` are refreshed outputs, not durable source.

## Phase 0 Research

See [research.md](research.md). All planning decisions are resolved from the TACD-002 spec, design concept, TACD-001 spike, and roadmap inputs. No unresolved clarification marker remains.

## Phase 1 Design

See [data-model.md](data-model.md), [contracts/capability-discovery-guidance.md](contracts/capability-discovery-guidance.md), and [quickstart.md](quickstart.md).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Reviewability warning for multiple active guidance surfaces and generated payload copies | TACD-002 must update Claude and Codex behavior together so the shared directive does not create semantic drift. | Splitting Claude and Codex behavior would leave one runtime with stale preferred-tool guidance and would not satisfy TACD-001's shared-directive handoff. |

## Post-Design Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional gates | PASS | Phase 1 artifacts preserve 0 projected production files, no new scripts, no metadata version edits, and no new deterministic/eval enforcement. |
| Reviewability gate | PASS with accepted warning | The accepted warning remains bounded to active guidance and generated payload refresh evidence. TACD-003 and TACD-004 are explicitly deferred. |
| Scope gate | PASS | Plan artifacts do not implement prerequisite messaging, public setup wording, or final enforcement/evals. |

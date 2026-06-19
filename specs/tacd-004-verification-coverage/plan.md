# Implementation Plan: Verification Coverage (TACD-004)

**Branch**: `tacd-004-verification-coverage` | **Date**: 2026-06-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/tacd-004-verification-coverage/spec.md`

## Summary

TACD-004 locks the vendor-neutral capability-discovery contract established by
TACD-001/002/003 with deterministic checks plus functional eval coverage, and
repairs the Claude payload-build defect so neither can silently regress. Four
production-relevant changes:

1. **Layer 5 (tool-scoping)** — remove the named-MCP requirement entirely from the
   tool-scoping contract (the `implement-executor` block currently requires
   `mcp__tavily-mcp__*`, `mcp__context7__*`, `mcp__RepoPrompt__*` by name), and add a
   named-tool regression guard that fails when active Claude/Codex agent guidance
   reintroduces a hardcoded named optional-tool preference outside the spike-approved
   category allowlist, with false-positive guards for schema/dependency metadata IDs
   and the generic `mcp` vocabulary.
2. **Layer 1 (structural)** — add pointer-coverage checks (each active agent
   references `capability-discovery.md` or an enumerated approved equivalent) and
   target-resolution checks (the referenced directive resolves at the path each
   runtime loads it from inside `dist/claude/**` and `dist/codex/**`), plus a
   body-completeness check that fails when any built Claude `SKILL.md` is truncated
   relative to its source minus the guard section.
3. **Build script** — fix `strip_codex_guard` in `scripts/build-plugin-payloads.sh`
   to strip from the `## Codex Skill-Selection Guard` heading to the next `## `
   heading or EOF (a section-boundary scan), never to the line-wrapped magic
   terminator string `fallback guard was triggered.`, then regenerate `dist/**` from
   source so all skill bodies are restored.
4. **Eval files** — rewrite the optional-tool expectations across all four eval files
   (autopilot + coach, Claude + Codex) so each asserts BOTH the absence of a preferred
   named set AND an affirmative capability-first answer, and add five
   behavior-observable scenarios (installed-capability discovery, fallback,
   evidence path, citations/local-file references, lowered confidence) as committed
   replay fixtures with no live model run gating merge.

The technical approach is documented in [research.md](./research.md); runnable
verification is in [quickstart.md](./quickstart.md).

## Technical Context

**Language/Version**: Bash (macOS/Linux, `bash` + `jq`) for tests and validators;
Python 3 embedded in `scripts/build-plugin-payloads.sh` for the payload builder.

**Primary Dependencies**: `jq`, `git`, `python3`, the existing
`tests/speckit-pro/lib/assertions.sh` shared assertion library, and the existing
`scripts/build-plugin-payloads.sh` builder. No new runtime dependency is added.

**Storage**: Repository files only — source guidance under `speckit-pro/`, generated
payload copies under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, JSON
eval fixtures under `tests/speckit-pro/layer3-functional/{evals,codex-evals}/`, and
Plan-phase artifacts under `specs/tacd-004-verification-coverage/`. No database or
persistent state.

**Testing**: Deterministic shell suite `bash tests/speckit-pro/run-all.sh` (Layers 1
structural, 4 script-unit, 5 tool-scoping). Focused runs: `--layer 1`, `--layer 4`,
`--layer 5`. Payload rebuild: `bash scripts/build-plugin-payloads.sh`. The Layer 3
eval fixtures are validated by replay/committed fixtures; no live `claude -p` run
gates merge.

**Target Platform**: Claude Code and Codex CLI plugin consumers; the checks run in
the local/CI deterministic harness.

**Project Type**: Claude Code plugin marketplace (`speckit-pro` plugin) — a
plain Bash/Markdown/JSON repository with no package manager and no
build/typecheck/lint toolchain. "Verification" is the shell harness above plus the
payload rebuild.

**Performance Goals**: N/A — the new checks are fast deterministic shell/JSON
assertions added to the existing fast layers (1/4/5); they must not depend on live AI
eval execution.

**Constraints**: Extend Layers 1/4/5 in place — no new test layer, no broad scanner.
Every new guard MUST be non-vacuous (a deliberate regression fails it). Remove the
named MCP assertions from Layer 5 entirely. Resolve directive targets against the
`dist/**` payload layout, not just the source tree. Fix `strip_codex_guard` with a
section-boundary scan; rebuild `dist/` only from source via the build script (never
hand-edit payloads). No agent decision-logic, prerequisite-script, or docs-wording
changes.

**Scale/Scope**: 1 production file changed (`scripts/build-plugin-payloads.sh`); 1
Layer 5 validator reworked; ~3 new Layer 1 structural validators; 4 eval files
rewritten; `dist/**` regenerated from source (8 of 10 Claude `SKILL.md` bodies are
currently truncated and will be restored). ~10 total source-tracked files plus
source-derived `dist/**` regeneration.

**Reviewability Budget**: Primary surface = harness/adapter (tests + the build
script); secondary surface = docs/process (spec/workflow process artifacts only, no
shipped-guidance wording changes). Projected reviewable LOC ~292 (roadmap baseline
~202 + ~90 for the `strip_codex_guard` fix and the body-completeness validator).
Projected production files = 1 (`scripts/build-plugin-payloads.sh`). Projected total
files ~10. Budget result: within budget (under the warn thresholds of 400 reviewable
LOC / 6 production files / 15 total files). Generated `dist/**` regeneration is
source-derived and excepted from reviewable LOC. The single existing setup-gate
warning (two primary surfaces) is non-blocking.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint. One entry per file.

- MODIFIED scripts/build-plugin-payloads.sh
- MODIFIED tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh
- NEW tests/speckit-pro/layer1-structural/validate-capability-pointer.sh
- NEW tests/speckit-pro/layer1-structural/validate-capability-resolution.sh
- NEW tests/speckit-pro/layer1-structural/validate-payload-completeness.sh
- MODIFIED tests/speckit-pro/run-all.sh
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json

Note: the three new Layer 1 validators are listed as separate files for a clean
review surface. If the agent-inventory pointer rule and the dist resolution rule
prove small enough to read in one file, pointer-coverage and target-resolution MAY be
combined into a single `validate-capability-pointer.sh`; the estimate is unaffected
because the LOC is the same. Regenerated `dist/claude/**` and `dist/codex/**` payload
copies are produced solely by re-running the builder and are excepted from reviewable
LOC (FR-013).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.1.0. All six principles pass; no violations to justify.

| Principle | Status | Evidence / Plan |
|-----------|--------|-----------------|
| I. Plugin Structure Compliance | PASS | Changes stay inside `speckit-pro` plugin source, `tests/speckit-pro/`, `scripts/build-plugin-payloads.sh`, and `dist/**` regeneration. No layout change to the plugin tree. Gate: `bash tests/speckit-pro/run-all.sh --layer 1`. |
| II. Script Safety | PASS | New/edited Bash validators begin with `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, `jq` for JSON, `chmod +x`, and pass `bash -n`. The Python builder keeps its existing structure; the `strip_codex_guard` fix is a localized section-boundary change. Gate: `bash -n` on changed scripts + Layer 4. |
| III. Semantic Versioning | PASS | No manual edits to plugin version fields; release tooling owns versions. Gate: git diff review. |
| IV. Test Coverage Before Merge | PASS | Every new deterministic guard is non-vacuous (FR-012): a deliberate regression — named tool re-added, missing/unresolved pointer, truncated payload — fails it. New Layer 1 validators are wired into `run-all.sh`; the default suite passes (FR-010). Gate: `bash tests/speckit-pro/run-all.sh`. |
| V. Conventional Commits | PASS | Phase commits use conventional format; the production fix is a `fix(speckit-pro):` change. Gate: commit/PR-title review. |
| VI. KISS, Simplicity & YAGNI | PASS | Extend Layers 1/4/5 in place; no new test layer, no broad scanner, no speculative abstraction. The approved-equivalent allowlist is kept as small as the active-agent inventory requires (empty if every agent references the directive directly). Gate: plan + code review. |

**Reviewability budget (constitution-required restatement):**

- **Primary review surface**: harness/adapter (the Layer 1/5 validators + the build
  script). **Secondary surface**: docs/process (spec and workflow artifacts only).
- **Within budget**: ~292 reviewable LOC, 1 production file, ~10 total files — all
  under the warn thresholds (400 LOC / 6 production / 15 total). The two-primary-surface
  warning from the setup gate is non-blocking and unchanged.
- **Split decision**: Remains one spec. The named-tool guard, the pointer/resolution
  checks, the eval rewrites, and the bundled payload fix are one cohesive
  verification-coverage slice locking a single contract; splitting would fragment the
  contract across PRs without reducing review risk. The payload fix is bundled here
  (not a separate hotfix branch) per the resolved scope decision. No deferred work; no
  follow-up spec/issue IDs required.
- **PR review packet source**: what changed, why, non-goals, review order, scope
  budget, traceability (AC-4.1–AC-4.4 and SC-Payload → changed files → verification
  evidence), verification commands, known gaps, and rollback/flag notes. See the PR
  packet checklist in [quickstart.md](./quickstart.md).

## Project Structure

### Documentation (this feature)

```text
specs/tacd-004-verification-coverage/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output — pointer rule, dist resolution model,
│                        #   payload-fix shape, body-completeness assertion design
├── quickstart.md        # Phase 1 output — verification commands + PR packet checklist
├── spec.md              # Finalized specification (input)
├── SPEC-MOC.md          # Spec map-of-content
└── checklists/
    └── requirements.md  # Preset quality checklist
```

`data-model.md` and `contracts/` are intentionally NOT produced: this feature has no
persistent data model and exposes no external API contract. Its observable contracts
are the deterministic checks themselves and the eval fixtures, documented in
research.md and quickstart.md.

### Source Code (repository root)

```text
scripts/
  build-plugin-payloads.sh                # FR-007: strip_codex_guard section-boundary fix

tests/speckit-pro/
  run-all.sh                              # FR-011: wire the new Layer 1 validators
  lib/assertions.sh                       # reused (not modified)
  layer1-structural/
    validate-capability-pointer.sh        # NEW — FR-003 pointer-coverage
    validate-capability-resolution.sh     # NEW — FR-004 dist/** target-resolution
    validate-payload-completeness.sh      # NEW — FR-008 body-completeness vs source
    validate-plugin-payload.sh            # existing sibling (dist rebuild + git-diff)
  layer5-tool-scoping/
    validate-tool-scoping.sh              # FR-001 named-tool guard + FR-002 remove named MCP set
  layer3-functional/
    evals/
      speckit-autopilot-evals.json        # FR-005/FR-006 rewrite + scenarios (Claude)
      speckit-coach-evals.json            # FR-005/FR-006 rewrite + scenarios (Claude)
    codex-evals/
      speckit-autopilot-evals.json        # FR-005/FR-006/FR-009 parity (Codex)
      speckit-coach-evals.json            # FR-005/FR-006/FR-009 parity (Codex)

speckit-pro/
  skills/speckit-autopilot/references/capability-discovery.md   # directive (referenced, not edited)
  skills/**/SKILL.md                      # source bodies (read-only inputs to the builder)
  agents/                                 # active Claude agent inventory (pointer/guard scope, read-only)
  codex-agents/                           # active Codex agent inventory (pointer/guard scope, read-only)

dist/
  claude/speckit-pro/skills/**/SKILL.md   # FR-007 regenerated (bodies restored)
  codex/speckit-pro/skills/**/SKILL.md    # FR-007 regenerated
  claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md  # FR-004 resolution target
  codex/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md   # FR-004 resolution target
```

**Structure Decision**: Single-repository plugin marketplace; no `src/` application
tree. The "source code" of this slice is shell validators under
`tests/speckit-pro/`, the Python payload builder under `scripts/`, and JSON eval
fixtures under `tests/speckit-pro/layer3-functional/`. New validators follow the
existing Layer 1 conventions (`source ../lib/assertions.sh`; compute `REPO_ROOT` via
`cd "$(dirname "$0")/../../.."`; reference `dist/claude/speckit-pro` and
`dist/codex/speckit-pro` directly) and are registered in `run-all.sh` alongside the
other Layer 1 validators.

## Complexity Tracking

> No constitutional violations. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

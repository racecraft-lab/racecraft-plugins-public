# SpecKit Workflow: TACD-004 - Verification Coverage

**Template Version**: 1.0.0
**Created**: 2026-06-19
**Purpose**: Execute TACD-004 through the SpecKit workflow and prepare the verification-coverage slice for autopilot. TACD-004 is the final spec in the Tool-Agnostic Capability Discovery roadmap; it locks the vendor-neutral contract with deterministic checks plus functional eval coverage, and additionally repairs the Claude payload-build defect with a regression check.

---

## How to Use This Workflow

1. Run the phases in order from the `tacd-004-verification-coverage` branch.
2. Re-read the design concept before each phase.
3. Treat the TACD-001 spike report/allowlist, TACD-002 and TACD-003 merged behavior, the TACD-004 roadmap section, and PRD AC-4.1 through AC-4.4 as controlling source evidence.
4. Keep implementation bounded to verification coverage plus the bundled payload-build fix. No agent decision-logic changes, no prerequisite-script behavior changes, no docs-wording changes.
5. Track progress in the status tables below.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/TACD-004-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The design
concept is the source of truth for setup-time scoping decisions.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once autopilot begins, clarifications happen via `/speckit-clarify` and
> the consensus protocol, never via Grill Me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | spec.md: 13 FR, 4 US, 15 acceptance scenarios, SC-001…SC-005; 0 `[NEEDS CLARIFICATION]` |
| Clarify | `/speckit-clarify` | ✅ Complete | Skipped — G1 found 0 markers; grill-me Q1–Q8 already encoded in spec (FR/SC traceability) |
| Plan | `/speckit-plan` | ✅ Complete | plan.md/research.md/quickstart.md; G3 PASS; reviewability est. ~40 LOC |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains; 8 `[Gap]` resolved; G4 PASS (0 markers) |
| Tasks | `/speckit-tasks` | ✅ Complete | 37 tasks, 7 groups; G5 PASS; route = one-navigable-PR |
| Analyze | `/speckit-analyze` | ✅ Complete | 1 HIGH resolved (T004 3→6 agents); G6 PASS; confidence 0.96 |
| Implement | `/speckit-implement` | ✅ Complete | 4 user stories (US1/US2/US4/US3) committed; G7 non-vacuity: all 4 guards fail on a deliberate regression |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories are clear; no unresolved `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Verification layering, payload-fix scope, and eval proof/wording are documented |
| G3 | After Plan | Architecture, affected files, and the deterministic verification plan are approved |
| G4 | After Checklist | All `[Gap]` markers are addressed or explicitly out of scope |
| G5 | After Tasks | Tasks are ordered, testable, and trace to AC-4.1 through AC-4.4 plus the payload-completeness criterion |
| G6 | After Analyze | No CRITICAL issues remain; WARNING items are reviewed |
| G7 | After Implementation | Default deterministic suite (`bash tests/speckit-pro/run-all.sh`) passes; a deliberate regression fails the new guards |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with
`.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Keep changes inside the existing `speckit-pro` plugin, `tests/speckit-pro/`, the build script, and docs/spec process paths | `bash tests/speckit-pro/run-all.sh --layer 1` when structure changes |
| Script Safety | Bash test/validator changes keep `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and `jq` for JSON; the Python build script keeps its existing safety guards | `bash -n` on changed shell scripts plus relevant Layer 4 tests |
| Semantic Versioning | Do not manually edit plugin version fields unless release tooling requires it | Git diff review |
| Test Coverage Before Merge | New deterministic guards are real (a deliberate regression fails them), and the default suite passes | `bash tests/speckit-pro/run-all.sh` before PR |
| Conventional Commits | Setup and implementation commits use conventional commit format | Git commit message review |
| KISS, Simplicity & YAGNI | Extend Layers 1/4/5 in place; no new test layers, no broad scanners, no speculative abstractions | Plan and code review |

**Constitution Check:** Verify before proceeding to G1

### Reviewability Setup Gate

The setup gate was run against the technical roadmap:

```json
{"mode":"setup","status":"warn","pass":true,"reviewable_loc":202,"production_files":0,"total_files":7,"primary_surface_count":2,"primary_surfaces":["docs/process","harness/adapter"],"warnings":["primary surfaces 2 exceeds warn threshold 1"],"blockers":[]}
```

The single warning (two primary surfaces) is non-blocking. The roadmap budget was
revised when the Claude payload-build fix was bundled into TACD-004 (Grill Me Q5):

- Primary surface: harness/adapter
- Projected reviewable LOC: ~292 (was 202; +~90 for the `strip_codex_guard` fix and the body-completeness validator)
- Production files: 1 (`scripts/build-plugin-payloads.sh`)
- Total files: ~10
- Budget result: within budget (under the warn thresholds of 400 LOC / 6 production / 15 total)

Re-run `reviewability-gate.sh setup` after Plan if the implementation file set grows.

### Autopilot Preflight

| Check | Status | Evidence |
|-------|--------|----------|
| Model and effort | ✅ | Opus 4.8 (≥ 4.6) + effort `max`. `AGENT_TEAMS_AVAILABLE=true`; `CONFIDENCE_GATE_MODE=advisory` |
| Prerequisites script | ✅ | `all_pass=true`, SpecKit 0.10.3.dev0; `on_feature_branch=false` EXPECTED for a `tacd-` branch. Green baseline: `tests/speckit-pro/run-all.sh` 3163/3163 (L1 573+451, L4 1949, L5 190) |
| Confidence gate mode | ✅ | `advisory` (`resolve-confidence-mode.sh --` exit 0; no flag/config override) |
| Archive sweep | ✅ | Dry-run/report-only on feature branch; cleanup disabled. TACD-001/002/003 already archived |
| Tier-2 relocation | ✅ | Suppressed — active target `SPEC-MOC.md` is `structureVersion: 1` (already current); no relocatable PROCESS artifacts |

**Resolved pre-flight context** (passed to every subagent):

- **PROJECT_COMMANDS:** stack `unknown` (no package manager). Verification harness = `bash tests/speckit-pro/run-all.sh` (Layers 1/4/5); focused: `--layer 1` structural, `--layer 4` script-unit, `--layer 5` tool-scoping. Payload rebuild: `bash scripts/build-plugin-payloads.sh`.
- **PRESET_CONVENTIONS:** `speckit-pro-reviewability` v1.0.0 (custom spec/plan/tasks templates; 18 hook events).
- **MCP availability:** `tavily-mcp`, `context7`, `RepoPrompt` not configured → consensus/research agents use built-in WebSearch/Read/Grep fallbacks.
- **PROJECT_IMPLEMENTATION_AGENT:** fallback `speckit-pro:phase-executor` (no host impl agent; `.claude/agents/` = auditor + skill-reviewer only).
- **Hook policy:** `git`-extension auto-commit hooks SKIPPED (duplicate the autopilot's own per-phase commit); after_specify `doctor` hook SKIPPED (duplicates Phase 0 doctor); `verify` / `verify-tasks` / `retrospective` after_implement hooks handled in post-implementation.
- **Pre-flight diagnostics:** Doctor HEALTHY (6 PASS / 1 expected WARN / 0 FAIL); Archive dry-run sweep found no candidates (current target excluded; TACD-001/002/003 already archived). Spec-MOC index regenerated each phase boundary — the global active-spec index injects a `[TACD-004]` nav entry into every roadmap-MOC `GENERATED:INDEX` zone (generated content, not a manual edit).

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| Spec ID | TACD-004 |
| Name | Verification Coverage |
| Branch | `tacd-004-verification-coverage` |
| Spec Directory | `specs/tacd-004-verification-coverage` |
| Dependencies | TACD-001, TACD-002, TACD-003 |
| Enables | Feature complete (final spec) |
| Priority | P1 |
| Roadmap | `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` |
| PRD | `docs/prd-tool-agnostic-capability-discovery.md` |
| Design Concept | `docs/ai/specs/.process/TACD-004-design-concept.md` |

### Source Evidence

- TACD-004 roadmap section: `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- TACD PRD acceptance criteria AC-4.1 through AC-4.4: `docs/prd-tool-agnostic-capability-discovery.md`
- TACD-001 spike report and category allowlist: `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- TACD-002 archive report: `.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`
- TACD-003 archive report: `.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`
- Shared capability-discovery directive: `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
- Layer 5 tool scoping (named-MCP block to rework): `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`
- Layer 3 functional evals (4 files to rewrite): `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`, `tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json`, and the `codex-evals/` counterparts
- Payload build script (defect to fix): `scripts/build-plugin-payloads.sh` (`strip_codex_guard`)

### Success Criteria Summary

- [ ] AC-4.1: Deterministic tests fail if active runtime guidance reintroduces a hardcoded named-tool contract outside the spike-approved category allowlist.
- [ ] AC-4.2: Structural or tool-scoping tests verify that relevant Claude and Codex agents point to the approved capability-discovery directive or carry an approved equivalent.
- [ ] AC-4.3: Functional evals prove that SpecKit Pro answers optional-tool questions in vendor-neutral terms and describes installed-capability discovery plus fallback behavior.
- [ ] AC-4.4: The default deterministic suite passes: `bash tests/speckit-pro/run-all.sh`.
- [ ] SC-Payload (added in this spec, Grill Me Q5/Q6): `strip_codex_guard` strips only the Codex guard block; `dist/` is rebuilt so all skills retain their bodies; a deterministic body-completeness check fails if any `dist/claude` SKILL.md is truncated relative to its source minus the guard section.

### Scope Decisions From Grill Me

- Q1: Host the named-tool regression guard in Layer 5 and the directive pointer-coverage / structural checks in Layer 1 (split).
- Q2: "Points to the directive" = a literal path match to `capability-discovery.md`, plus a small enumerated allowlist of approved runtime-specific equivalents.
- Q3: Test target resolution by checking the directive file exists at the path each agent loads it from inside `dist/claude/**` and `dist/codex/**`.
- Q4: Remove the named MCP tool assertions (`mcp__tavily-mcp__*`, `mcp__context7__*`, `mcp__RepoPrompt__*`) from the Layer 5 contract entirely.
- Q5: Bundle the Claude payload-build fix, the `dist/` rebuild, and the regression check into TACD-004 (not a separate hotfix).
- Q6: The payload check asserts body-completeness vs source (last source `##` heading survives; body within tolerance of source-minus-guard).
- Q7: Replay/committed-fixture validation is sufficient for the behavior-observable eval scenarios; no live `claude -p` gate.
- Q8: Rewritten eval expected outputs assert BOTH the absence of a preferred named-tool set AND an affirmative capability-first answer.

---

## Phase 1: Specify

**When to run:** At the start of the feature specification. Focus on WHAT and
WHY, not implementation details. Output:
`specs/tacd-004-verification-coverage/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Verification Coverage

### Problem Statement
TACD-002 shipped a vendor-neutral capability-discovery directive into active Claude
and Codex agent guidance, and TACD-003 replaced the hardcoded optional-MCP
prerequisite report with a generic, non-blocking capability advisory. But the test
and eval surfaces still encode the old named-tool contract: Layer 5 tool scoping
still REQUIRES `mcp__tavily-mcp__*`, `mcp__context7__*`, and `mcp__RepoPrompt__*` by
name, and the Layer 3 functional evals still teach a preferred Tavily/Context7/
RepoPrompt set. Nothing fails when active guidance reintroduces a hardcoded named
optional-tool contract, nothing verifies agents point to the shared
capability-discovery directive, nothing proves those pointers resolve from the
installed runtime layout, and no behavior-observable eval scenarios cover discovery,
fallback, evidence path, citations, and lowered confidence. Separately, a defect in
the payload builder's `strip_codex_guard` truncates the Claude SKILL.md body for
every skill whose guard-block terminator phrase is line-wrapped across two source
lines (so the builder's single-line check never matches it and the strip runs to
end-of-file), so most Claude skills currently install with empty bodies. TACD-004 is the final spec: it locks the
vendor-neutral contract with deterministic checks plus functional eval coverage, and
repairs the payload-build defect with a regression check so neither can silently
regress.

### Users
- Maintainers and reviewers who need the vendor-neutral contract enforced
  automatically so a future edit cannot silently reintroduce a named-tool contract.
- SpecKit Pro consumers (Claude Code and Codex) who must receive complete, functional
  skill payloads when they install or update the plugin.
- Contributors changing agent guidance, who need fast deterministic feedback when a
  change violates the capability-first or payload-completeness contract.

### User Stories
1. As a maintainer, I want a deterministic check that fails when active runtime
   guidance reintroduces a hardcoded named optional-tool contract, so the
   vendor-neutral decision from TACD-001/002/003 cannot regress unnoticed.
2. As a maintainer, I want structural checks proving every active agent points to the
   shared capability-discovery directive (or an approved equivalent) and that the
   pointer resolves from the installed `dist/**` layout.
3. As a maintainer, I want the four functional eval expectations rewritten so
   optional-tool answers are vendor-neutral, asserting both the absence of a named
   set and an affirmative capability-first answer.
4. As a consumer, I want every installed skill to ship its full body, with a
   deterministic check that fails if the Claude payload truncates a SKILL.md.

### Functional Requirements
- FR1: Add a deterministic check (Layer 5 named-tool guard + Layer 1 structural) that
  fails when active Claude/Codex agent guidance reintroduces a hardcoded named
  optional-tool preference outside the TACD-001 category allowlist, with
  false-positive guards (exact schema/dependency metadata IDs and the generic `mcp`
  vocabulary stay allowed).
- FR2: Rework the Layer 5 block that asserts the named MCP tools so the scoping
  contract no longer names a specific vendor MCP set (full removal, per Q4).
- FR3: Add static pointer-coverage checks proving each active agent references
  `capability-discovery.md` or an enumerated approved equivalent.
- FR4: Add target-resolution checks proving the referenced directive resolves/exists
  at the path each runtime loads it from inside `dist/claude/**` and `dist/codex/**`.
- FR5: Rewrite the optional-tool eval expected outputs across all four eval files so
  each asserts both the absence of a preferred named set and an affirmative
  capability-first answer.
- FR6: Add behavior-observable eval scenarios for installed-capability discovery,
  fallback when named tools are unavailable, evidence path, citations/local-file
  references, and lowered confidence when fallback quality is lower (validated by
  committed fixtures; no live run gates merge).
- FR7: Fix `strip_codex_guard` in `scripts/build-plugin-payloads.sh` to strip only
  the Codex guard block (to the next heading / EOF) instead of truncating to EOF, and
  rebuild `dist/` so all skill bodies are restored.
- FR8: Add a deterministic body-completeness check that fails if any `dist/claude`
  SKILL.md is truncated relative to its source minus the guard section.
- FR9: Maintain Claude/Codex parity for every eval and pointer/resolution check.
- FR10: Keep `bash tests/speckit-pro/run-all.sh` (Layers 1/4/5) green without
  depending on live AI eval execution.

### Constraints
- Extend Layers 1/4/5 in place; do not add a new test layer or a broad scanner.
- Do not change agent decision logic, prerequisite-script behavior, or docs wording.
- Preserve concrete tool IDs only where platform schema/dependency metadata, exact
  file references, fixtures, or historical provenance require them.
- Regenerate `dist/**` from source via the build script; do not hand-edit payloads.

### Out of Scope
- Live AI eval execution as a merge gate.
- New test layers or broad harness rewrites.
- Rewriting historical/provenance or generated source-derived mentions of named tools.
- A separate hotfix branch for the payload bug (bundled here per Q5).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 13 (FR-001 … FR-013) |
| User Stories | 4 (US1/US2/US4 = P1, US3 = P2) |
| Acceptance Criteria | 15 acceptance scenarios + 5 success criteria (SC-001 … SC-005) |
| G1 Gate | ✅ Satisfied — `spec.md` exists, 0 `[NEEDS CLARIFICATION]` markers (disk-verified) |

### Files Generated

- [x] `specs/tacd-004-verification-coverage/spec.md` (+ `checklists/requirements.md`, preset quality checklist)

### SpecKit Traceability Markers

Use markers such as `[US1]`, `[US2]`, `[FR-001]`, `[NEEDS CLARIFICATION]`,
`[P]`, and `[Gap]` so later phases can trace requirements through tasks.

---

## Phase 2: Clarify

**When to run:** After Specify, if any wording, surface, or verification boundary
can be interpreted multiple ways. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Verification Layering and Pointer Contract

```bash
/speckit-clarify Focus on TACD-004 verification layering:
- Confirm the named-tool regression guard lives in Layer 5 and the pointer-coverage /
  structural checks live in Layer 1.
- Define the machine-checkable pointer rule: a literal path match to
  capability-discovery.md plus a small enumerated allowlist of approved
  runtime-specific equivalents. Enumerate which active agents (if any) need an
  equivalent.
- Define how target resolution is checked against dist/claude/** and dist/codex/**.
- Confirm the named MCP tool assertions are removed entirely from Layer 5, with
  false-positive guards for schema/dependency metadata IDs and the generic `mcp`
  vocabulary.
```

#### Session 2: Payload-Build Correctness

```bash
/speckit-clarify Focus on TACD-004 payload-build correctness:
- Confirm the fix replaces strip_codex_guard's magic-terminator scan with a
  section-boundary scan (strip from the guard heading to the next heading or EOF).
- Confirm dist/ is rebuilt from source so all skill bodies are restored, with no
  hand-edited payloads.
- Define the body-completeness assertion: structural anchor (last source ## heading
  survives) preferred over a brittle absolute line count; tolerance for the stripped
  guard block only.
- Confirm the check runs in the default deterministic suite (Layer 1).
```

#### Session 3: Eval Proof Bar and Wording

```bash
/speckit-clarify Focus on TACD-004 eval coverage:
- Confirm committed-fixture/replay validation is sufficient for the five
  behavior-observable scenarios; no live claude -p gates merge.
- Confirm each rewritten expected output asserts BOTH the absence of a preferred
  named set AND an affirmative capability-first answer.
- Confirm Claude/Codex parity across all four eval files (autopilot + coach).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Verification layering & pointer contract | 0 (skipped) | Locked in spec: FR-001/002 (L5 guard + full named-assertion removal), FR-003/004 (pointer + dist/** resolution) |
| 2 | Payload-build correctness | 0 (skipped) | Locked in spec: FR-007 (section-boundary strip + rebuild), FR-008 (body-completeness vs source) |
| 3 | Eval proof bar & wording | 0 (skipped) | Locked in spec: FR-005 (absence + affirmative), FR-006 (replay fixtures), FR-009 (Claude/Codex parity) |

> **Clarify skipped per G1** (0 `[NEEDS CLARIFICATION]` markers in spec.md). The pre-workflow Grill Me interview already resolved scope (Q1–Q8); each decision is encoded as a functional requirement / success criterion with traceability, so no in-loop clarification was warranted.

---

## Phase 3: Plan

**When to run:** After spec and clarifications are finalized. Output:
`specs/tacd-004-verification-coverage/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Shell: Bash with `set -euo pipefail`; use `jq` for JSON work.
- Tests: Shell-based deterministic tests under `tests/speckit-pro/` (Layers 1, 4, 5).
- Build: Python embedded in `scripts/build-plugin-payloads.sh` (the `strip_codex_guard` fix).
- Eval fixtures: JSON under `tests/speckit-pro/layer3-functional/evals/` and `codex-evals/`.
- Runtime: Claude Code and Codex plugin guidance, with shared source files and
  generated `dist/**` payloads.

## Constraints
- Extend Layers 1/4/5 in place; no new test layer, no broad scanner.
- Keep every new guard real: a deliberate regression must fail it (not vacuous).
- Remove the named MCP tool assertions from Layer 5 entirely.
- Test target resolution against the dist/** payload layout.
- Fix strip_codex_guard with a section-boundary scan; rebuild dist/ from source.
- No agent decision-logic, prerequisite-script, or docs-wording changes.

## Architecture Notes
- Named-tool guard (Layer 5) and pointer-coverage/target-resolution (Layer 1) are the
  two deterministic surfaces; the four eval files carry the behavior expectations.
- The pointer rule is a path match to capability-discovery.md plus an enumerated
  approved-equivalent allowlist built from the actual active-agent inventory.
- The payload-completeness check anchors on a structural invariant (last non-guard
  source heading present in the payload) rather than an absolute line count.
- strip_codex_guard must strip from `## Codex Skill-Selection Guard` to the next
  heading (or EOF), never to a magic terminator string.

## Reviewability Budget
- Revised TACD-004 budget after bundling the payload fix: ~292 projected reviewable
  LOC, 1 production file (`scripts/build-plugin-payloads.sh`), ~10 total files,
  within budget.
- Generated `dist/**` regeneration is source-derived and excepted from reviewable LOC.

## Candidate Files
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`
- `tests/speckit-pro/layer1-structural/` (new pointer-coverage / target-resolution / payload-completeness validators)
- `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
- `tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json`
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json`
- `scripts/build-plugin-payloads.sh` (`strip_codex_guard`)
- Regenerated `dist/claude/**` and `dist/codex/**` payload copies
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ Created | Technical context, affected files, verification plan; constitution 6/6 PASS |
| `research.md` | ✅ Created | 6 decisions; Decision 3 = dist/** prefix re-rooting (corrected in Checklist) |
| `data-model.md` | Not expected | No database or persistent data model |
| `contracts/` | Not expected | No API contract |
| `quickstart.md` | ✅ Created | Verification commands and PR packet checklist |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Validate both spec and plan together.

### Recommended Domains

#### 1. Reliability Checklist

Why this domain: The new guards are the load-bearing deliverable. The main risk is a
vacuous check that passes even when the contract is violated, or a flaky
body-completeness assertion.

```bash
/speckit-checklist reliability

Focus on TACD-004 requirements:
- Every new guard is proven real: a deliberate regression (named tool re-added, a
  truncated payload) makes it FAIL.
- The body-completeness check is deterministic and not flaky across skills.
- The default suite stays green and does not depend on live eval execution.
- Pay special attention to: false-positive guards for schema/dependency metadata IDs
  and the generic `mcp` vocabulary.
```

#### 2. Integration Checklist

Why this domain: The checks must hold Claude and Codex parity and resolve against the
installed `dist/**` layout, not just the source tree.

```bash
/speckit-checklist integration

Focus on TACD-004 requirements:
- Pointer-coverage and target-resolution checks cover both Claude and Codex agents.
- Resolution is verified against dist/claude/** and dist/codex/**.
- All four eval files (autopilot + coach, Claude + Codex) are updated in parity.
- Pay special attention to: the dist/ rebuild being source-derived, never hand-edited.
```

#### 3. Maintainability Checklist

Why this domain: TACD-004 changes a shared build script and the tool-scoping
contract; both are high-blast-radius surfaces.

```bash
/speckit-checklist maintainability

Focus on TACD-004 requirements:
- strip_codex_guard's fix is the minimal section-boundary change, with its own
  focused coverage.
- Removing the named-tool assertions does not break unrelated Layer 5 expectations.
- The approved-equivalent allowlist is as small as the agent inventory requires.
- Pay special attention to: no scope drift into agent behavior or docs wording.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| reliability | 42 | 5 found / 5 resolved | FR-003/008/011/012 + 2 assumptions |
| integration | 27 | 1 found / 1 resolved | FR-004 + research Decision 3 (dist/** prefix re-rooting) |
| maintainability | 30 | 2 found / 2 resolved | already covered (no spec edit; boundaries confirmed) |
| Total | 99 | 8 found / 8 resolved | ✅ G4 PASS (0 `[Gap]` markers; 0 unresolved for consensus) |

---

## Phase 5: Tasks

**When to run:** After checklists complete and gaps are resolved. Output:
`specs/tacd-004-verification-coverage/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Use TDD: write the failing guard/check first, confirm it FAILS on a deliberate
  regression, then make it pass.
- Keep tasks small and traceable to AC-4.1 through AC-4.4 and SC-Payload.
- Order work as: Layer 5 named-tool guard + assertion removal, Layer 1
  pointer-coverage / target-resolution, payload-build fix + body-completeness check +
  dist rebuild, eval rewrites + behavior scenarios, full-suite validation.
- Mark parallel-safe eval-file edits with [P] only where they do not depend on a
  shared helper landing first.
- Reference `docs/ai/specs/.process/TACD-004-design-concept.md`, especially Goals,
  Non-goals, and Q1-Q8.

## Implementation Guidance
- Start each deterministic check from a failing fixture (regression) so the guard is
  proven non-vacuous.
- Fix strip_codex_guard before rebuilding dist/ so the rebuild restores full bodies.
- Keep the named-tool removal surgical within validate-tool-scoping.sh.

## Constraints
- Do not edit archives or hand-edit generated payloads.
- Do not change agent behavior, prerequisite scripts, or docs wording.
- Do not add a new test layer or a broad scanner.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 37 (T001–T038; T009A preset reviewability-checkpoint slot) |
| Phases | 7 (Setup, Foundational, US1, US2, US4, US3, Polish) |
| Parallel Opportunities | 6 `[P]` tasks (T003; eval edits T029–T032; T036) |
| User Stories Covered | US1/US2/US3/US4 — all FR-001..FR-013 mapped |
| G5 Gate | ✅ PASS (37 tasks; every FR has ≥1 task) |

---

## Atomicity Route

This section is filled after the Tasks phase / gate G5. The route is recorded
only here in the workflow file. Leave the cells blank during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| Releasable | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| Signals | `change-shape:modify-heavy` | Decisive detector findings behind the route. |
| Warnings | (none) | Any release-safety warning attached to the change. |

To produce the decision, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/tacd-004-verification-coverage
```

### Layer Plan & Reviewability (post-G5)

- **Layer plan:** `skipped` — route is `one-navigable-PR` (non-split). The PRSG layer planner runs only for a `split-PR` route; this change ships as a single navigable PR.
- **Reviewability (tasks mode):** `reviewability-gate.sh tasks` returned `status=block` (reviewable_loc 1480, total_files 88, primary_surfaces 6). This is a **known-coarse, size-only heuristic**, not a correctness stop: `reviewable_loc = 37 tasks × 40` and `total_files` is a path-token grep across tasks.md (it counts every path mention, including regenerated `dist/**`). It is contradicted by the authoritative signals — the plan-phase estimator (`status=pass`, **~40 projected LOC**, 1 production file), the atomicity route (`one-navigable-PR`), and the spec's explicit one-PR split decision. Per the Post-G5 matrix a size-only `tasks` block is a *proceed* input, not a manual re-slice; the binding budget check is the PR-time **diff-mode** gate against the actual diff. No PR marker plan is created (non-split route).
- **Final reviewability backstop (post-impl):** the diff-mode gate (`origin/main...HEAD`) returned `block` on `total_files 36 > 25`, but `reviewable_loc=4` and `production_files=1` (both far under budget). The 36 = 9 source-derived `dist/**` (excepted) + 16 SDD process artifacts + 10 real code/test files + CLAUDE.md. **Operator-approved** `infra` typed reviewability exception (declared in `spec.md` Reviewability Notes, "contract" provenance) covers the file-count dimension only; the change ships as one navigable PR. Re-running the backstop with the exception in the diff flips `block → exception` (proceed).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment: script safety, KISS/YAGNI, focused test coverage.
2. Cross-artifact consistency across spec.md, plan.md, tasks.md, and
   docs/ai/specs/.process/TACD-004-design-concept.md.
3. Scope drift: no agent behavior changes, no prerequisite-script changes, no docs
   wording changes, no new test layer.
4. Traceability: every task maps to AC-4.1 through AC-4.4, SC-Payload, or an approved
   validation task.
5. Non-vacuity: every new deterministic guard is paired with a deliberate-regression
   check that proves it fails when the contract is violated.
```

### Analyze Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| C1 | HIGH | tasks.md T004 listed only 3 pointer-coverage agents; ground-truth grep shows 6 reference `capability-discovery.md` | Corrected T004 → 6 directive-referencing agents (inventory-derived) + enumerated exclusion sets; bound T017's in-scope set to it |
| — | (other) | 0 CRITICAL / 0 MEDIUM / 0 LOW; 0 unresolved for consensus | G6 PASS; constitution 6/6; traceability + non-vacuity verified against the live repo |

### Pre-Implement Confidence (G6.5)

Emitted by the consensus-synthesizer at end of Phase 6 (advisory gate; threshold 0.90):

```text
📊 Confidence: 0.96

- Task understanding: 0.97
- Approach clarity: 0.97
- Requirements alignment: 1.00
- Risk assessment: 1.00
- Completeness: 0.87
```

Aggregate **0.96 ≥ 0.90** → G6.5 PASS (advisory). Completeness (0.87) note: the five behavior-observable eval scenario fixtures (T033) are described but designed during Implement — flagged for extra care in Phase 7.

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking gaps.

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First

For each deterministic guard / check:
1. RED: Add a fixture or scenario that violates the contract (named tool re-added,
   missing pointer, unresolved dist path, truncated payload) and confirm the new
   check FAILS.
2. GREEN: Implement the minimal check (Layer 5 / Layer 1) or the strip_codex_guard
   fix so the check passes.
3. REFACTOR: Keep shell/JSON construction clear and safe.
4. VERIFY: Run the focused layer and then `bash tests/speckit-pro/run-all.sh`.

For eval rewrites:
1. Rewrite each expected output to assert absence of a named set AND an affirmative
   capability-first answer; mirror Claude and Codex.
2. Add the five behavior-observable scenarios as committed fixtures.

For the payload fix:
1. Fix strip_codex_guard (section-boundary scan).
2. Rebuild dist/ via `bash scripts/build-plugin-payloads.sh`.
3. Confirm the body-completeness check passes and that all skill bodies are restored.

## Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD` shows `tacd-004-verification-coverage`.
2. Verify worktree cleanliness except expected SpecKit artifacts: `git status --short`.
3. Re-read `docs/ai/specs/.process/TACD-004-design-concept.md`.

## Implementation Notes
- The design concept's selected answers are load-bearing: Split Layer 5 + Layer 1;
  path match + approved-equivalent allowlist; resolve against dist/**; remove named
  assertions entirely; bundle the payload fix; body-completeness vs source;
  replay-only fixtures; absence + affirmative eval wording.
- If implementation discovers the slice exceeds budget, stop and revisit the split
  decision instead of silently expanding scope.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Layer 5 named-tool guard + assertion removal | T010–T014 | ✅ | validate-tool-scoping.sh: −5 named-MCP, +22 body-prose guard, fail-closed; Layer 5 207/207 (commit 239232e8) |
| Layer 1 pointer-coverage / target-resolution | T015–T021 | ✅ | 2 validators (pointer 16 + resolution 21) registered; dist/** prefix re-rooting (commit 42dd19b9) |
| Payload fix + body-completeness + dist rebuild | T022–T028 | ✅ | strip_codex_guard section-boundary fix; 8 skill bodies restored; validate-payload-completeness 52/52 (commit 527b5d4d) |
| Eval rewrites + behavior scenarios | T029–T034 | ✅ | 4 eval files: absence+affirmative + 5 scenarios (101–105), Claude/Codex parity (commit c6af364f) |
| Full-suite validation | T035–T037 | ✅ | Layer 1 1113/1113; G7 non-vacuity all 4 guards proven; full suite 3269/3269 |

---

## Post-Implementation Checklist

- [x] `specs/tacd-004-verification-coverage/tasks.md` complete
- [x] Each new deterministic guard fails on a deliberate regression (non-vacuous) — all 4 proven at G7
- [x] Layer 5 no longer asserts the named MCP tools
- [x] Pointer-coverage and target-resolution checks pass for Claude and Codex
- [x] `strip_codex_guard` fixed; `dist/` rebuilt; all skill bodies restored (8 skills)
- [x] Body-completeness check fails on a truncated payload
- [x] All four eval files rewritten in parity; behavior scenarios added as fixtures
- [x] `bash tests/speckit-pro/run-all.sh` passes (3269/3269)
- [x] `git diff --check` passes — clean except 2 generated spec-index MOC trailing-space lines (generated content; out of scope; see G7 note)
- [x] Reviewability / final PR packet checks run — final backstop honored an operator-approved `infra` exception; packet + workflow-contract validators passed
- [x] PR created — **#240** https://github.com/racecraft-lab/racecraft-plugins-public/pull/240

---

## Self-Review (auto-generated)

**Tests executed:** The full deterministic suite `bash tests/speckit-pro/run-all.sh` ran in this session (G7 verification) → **3269/3269** exit 0 (L1 662+451, L4 1949, L5 207); Layer 1 re-run independently 1113/1113; Layer 5 validator 207/207. BUILD/TYPECHECK/LINT are N/A for this repo (no such toolchain — the deterministic suite IS the verification). The four deliberate-regression proofs also executed and each guard FAILED correctly.

**Edge cases:** Every spec edge case has a non-happy-path test: guard terminator line-wrap (8 skills restored; truncation caught — natural RED 17/52) · generic `mcp` vocabulary and frontmatter `tools:` IDs (named-tool guard does NOT flag — false-positive checks confirmed) · unresolved payload path (resolution RED failed both runtimes) · missing pointer (pointer RED named the agent) · skill with no guard block (left untouched) · live-eval unavailability (suite green with no live run). No `[edge-case-gap]`.

**Requirements matched:** All FR-001..FR-013 trace to implementation + a passing test + a commit — FR-001/002 → `validate-tool-scoping.sh` (239232e8); FR-003 → `validate-capability-pointer.sh`, FR-004 → `validate-capability-resolution.sh` (42dd19b9); FR-005/006/009 → 4 eval files (c6af364f); FR-007 → `strip_codex_guard` + dist, FR-008 → `validate-payload-completeness.sh` (527b5d4d); FR-010..013 → suite-green / registration / non-vacuity / dist-sync. No orphans. (tasks.md items remain `[ ]` — the autopilot implements via subagents but does not tick `[X]`; the evidence is the commits + passing tests.)

**Follow-up:** No `[TODO]`/`[DEFERRED]`/`[OUT-OF-SCOPE]` in the implementation. Two known items, both surfaced in the PR body: (1) the generated spec-index injects 2 MOC nav lines with a trailing space (`- [TACD-004](…) · `) — generated content matching the generator's output (`validate-spec-index-determinism` passes); fixing the generator is out of TACD-004 scope. (2) the approved-equivalent allowlist is empty by design (all in-scope agents reference the directive directly). No silent deferrals.

---

## Lessons Learned

### What Worked Well

- The two-layer checklist/analyze consensus caught real, load-bearing defects before implementation: pointer-coverage scope (capability-dependent agents, not all agents), the dist/** resolution model (prefix re-rooting vs a wrong `../references` walk), and the 3→6 agent under-coverage in tasks.md T004.
- TDD non-vacuity: every guard was proven to FAIL on a deliberate regression. The payload-completeness check's *natural* RED — 17/52 on the pre-fix dist — was the strongest proof.
- The `strip_codex_guard` fix was exactly the minimal section-boundary change; all 8 truncated skills restored, dist/codex untouched.

### Challenges Encountered

- The `tacd-` branch name trips `check-prerequisites.sh`'s `NNN-` regex (`on_feature_branch=false`); benign but recurs in every script. Handled by pinning the feature dir.
- The final reviewability backstop blocked on `total_files` (36>25) — a coarse count inflated by 9 generated dist + 16 SDD paper-trail files; resolved with an operator-approved `infra` exception (real review surface 10 files / 4 LOC).
- `generate-pr-body.sh` produced a generic fallback body (no host PR template) with SHA-protected sections; the live PR body was corrected via `gh pr edit`. The worktree `.git`-is-a-file required a **repo-relative** packet body path — the `git rev-parse --git-path` external path is rejected by `validate-pr-packet`.

### Patterns to Reuse

- For verification-coverage specs, lead each guard with its deliberate-regression (RED) proof; leverage any *natural* RED (a pre-existing broken state) as the strongest non-vacuity evidence.
- For a small-but-many-files autopilot PR, expect the `total_files` gate to fire on generated/process files; an `infra` typed exception (contract provenance, bare `Reviewability-Exception: infra` line, not in a code fence) is the sanctioned resolution for a one-navigable change.

---

## Project Structure Reference

```text
scripts/
  build-plugin-payloads.sh         # strip_codex_guard fix
tests/
  speckit-pro/
    layer1-structural/             # pointer-coverage, target-resolution, payload-completeness
    layer3-functional/
      evals/                       # speckit-autopilot-evals.json, speckit-coach-evals.json
      codex-evals/                 # Codex counterparts
    layer5-tool-scoping/
      validate-tool-scoping.sh     # named-tool assertion removal
speckit-pro/
  skills/speckit-autopilot/references/capability-discovery.md
dist/
  claude/speckit-pro/skills/**/SKILL.md   # rebuilt
  codex/speckit-pro/skills/**/SKILL.md    # rebuilt
docs/
  ai/specs/
    .process/TACD-004-design-concept.md
    .process/TACD-004-workflow.md
    tool-agnostic-capability-discovery-technical-roadmap.md
```

---

Template based on the shared SpecKit workflow template, populated for TACD-004.

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=speckit-pr-packet --> Blocked PR packet validation for `speckit-pr-packet`; result `specs/tacd-004-verification-coverage/.process/pr-packets/speckit-pr-packet/validation.json`; rules: `unknown`.

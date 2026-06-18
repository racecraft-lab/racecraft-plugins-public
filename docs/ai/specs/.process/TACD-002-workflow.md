# SpecKit Workflow: TACD-002 - Capability Discovery Directive and Agent Updates

**Template Version:** 1.0.0
**Created:** 2026-06-18
**Purpose:** Prepare TACD-002 for `$speckit-autopilot` execution.

---

## Design Concept

This workflow was enriched from a Grill Me interview run during
`$speckit-scaffold-spec TACD-002`.

Design concept:

```text
docs/ai/specs/.process/TACD-002-design-concept.md
```

Re-read it before each phase. It records Goals, Non-goals, Q&A decisions,
Open Questions, and the accepted reviewability warning.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | `spec.md`: 4 stories, 15 FRs, 8 ACs, 6 SCs; no active clarification markers; Clarify carries directive path, target surfaces, metadata evidence, payload refresh, and fallback confidence wording |
| Clarify | `/speckit-clarify` | Complete | G2 passed; directive path, target surfaces, metadata policy, generated payload refresh path, and fallback evidence wording documented |
| Plan | `/speckit-plan` | Complete | G3 passed; Plan artifacts created; reviewability estimator projected 0 production LOC |
| Checklist | `/speckit-checklist` | Complete | G4 passed; 3 domains complete; 6 gaps fixed; 0 remaining `[Gap]` markers |
| Tasks | `/speckit-tasks` | Complete | G5 passed; 37 tasks generated with FR/SC coverage; reviewability task gate recorded a valid size-only block; atomicity route is one navigable PR |
| Analyze | `/speckit-analyze` | Complete | G6 passed after one workflow-only input coverage fix; no consensus required |
| Implement | `/speckit-implement` | Complete | G7 passed; source guidance updated; generated payloads refreshed; default suite passed `3041/3041` |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | No `[NEEDS CLARIFICATION]` markers remain for scope, user stories, and acceptance criteria |
| G2 | After Clarify | Directive home, target surfaces, metadata policy, and generated payload refresh path are documented |
| G3 | After Plan | Constitution gates pass; reviewability warning is accepted or the spec is split |
| G4 | After Checklist | All `[Gap]` findings are resolved or explicitly deferred to TACD-003/TACD-004 |
| G5 | After Tasks | Tasks cover all FRs, preserve file-scope budget, and include verification tasks |
| G6 | After Analyze | No CRITICAL findings; warnings have explicit owner decisions |
| G7 | After Implement | Tests pass, generated payloads are refreshed, and PR packet is complete |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Keep source guidance in the existing `speckit-pro/` layout and preserve generated payload flow | Layer 1 structural checks |
| Script Safety | Do not introduce unsafe shell changes; generated scripts, if any, use `set -euo pipefail` | `bash -n` through existing suite |
| Semantic Versioning | Do not manually edit plugin versions | Diff review and CI |
| Test Coverage Before Merge | Update focused tests or verification evidence when agent behavior changes | Relevant layer checks plus default suite |
| Conventional Commits | Setup and implementation commits use conventional format | Commit/PR title review |
| KISS, Simplicity & YAGNI | Prefer one shared directive with runtime pointers over duplicated bespoke behavior | Plan review |

**Constitution Check:** Verified before G1. G1 passed with `spec.md` present
and 0 `[NEEDS CLARIFICATION]` markers; implementation health remains gated by
the default suite before PR creation.

### Reviewability Setup Gate

```json
{"mode":"setup","status":"warn","pass":true,"reviewable_loc":202,"production_files":0,"total_files":7,"primary_surface_count":2,"primary_surfaces":["docs/process","harness/adapter"],"warnings":["primary surfaces 2 exceeds warn threshold 1"],"blockers":[]}
```

Decision: warning accepted for setup. TACD-002 must keep implementation focused
on active agent guidance. TACD-003 and TACD-004 remain separate specs.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| Spec ID | TACD-002 |
| Name | Capability Discovery Directive and Agent Updates |
| Branch | `tacd-002-capability-discovery-directive-and-agent-updates` |
| Dependencies | TACD-001 complete and archived |
| Enables | TACD-003, TACD-004 |
| Priority | P1 |
| Roadmap | `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` |
| Spike Report | `docs/ai/research/tool-agnostic-capability-discovery-spike.md` |
| Design Concept | `docs/ai/specs/.process/TACD-002-design-concept.md` |

### Success Criteria Summary

- Active Claude and Codex agent guidance uses capability categories instead of named optional MCP preferences.
- Relevant orchestrating and phase agents point to the shared directive or carry a spike-approved equivalent.
- Agents choose the best installed capability first, then fall back to local/platform capabilities when needed.
- Research/context-informed outputs include capability path, citations or local file references, and confidence.
- Formerly named tools can still be used through discovery when they are the best installed capability.

### Key Files From Roadmap And Spike

- `speckit-pro/agents/codebase-analyst.md`
- `speckit-pro/agents/domain-researcher.md`
- `speckit-pro/agents/clarify-executor.md`
- `speckit-pro/agents/checklist-executor.md`
- `speckit-pro/agents/analyze-executor.md`
- `speckit-pro/agents/implement-executor.md`
- `speckit-pro/codex-agents/*.toml`
- `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`
- Generated payload copies under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`

---

## Phase 1: Specify

**When to run:** At the start of TACD-002. Focus on WHAT and WHY, not the final implementation mechanics.

### Specify Prompt

```bash
/speckit-specify

## Feature: TACD-002 Capability Discovery Directive and Agent Updates

### Problem Statement
Active SpecKit Pro Claude and Codex agent guidance still contains preferred named optional-tool wording. TACD-001 selected a shared capability-discovery directive with runtime-specific pointers and approved equivalents. TACD-002 applies that decision to active runtime guidance.

### Users
- SpecKit Pro operators using Claude Code or Codex with different installed research/context capabilities.
- Maintainers reviewing agent behavior and generated payload consistency.
- Future TACD-003/TACD-004 implementers who need a stable behavior contract to document and enforce.

### User Stories
- As an operator, I want agents to choose research/context capabilities by need so the plugin does not prefer one vendor-specific optional MCP set.
- As an operator without optional capabilities, I want agents to keep working with transparent lower-confidence fallback evidence.
- As a maintainer, I want Claude and Codex guidance to share one semantic directive or approved equivalent so runtime behavior does not drift.
- As a maintainer, I want generated payloads refreshed from source so installed artifacts match source guidance.

### Constraints
- Scope is active agent behavior only; prerequisite messaging belongs to TACD-003 and enforcement/evals belong to TACD-004.
- Preserve schema-required runtime/dependency metadata IDs unless TACD-002 proves a generic equivalent.
- Do not hand-edit generated `dist/**` payloads as the source of truth.
- Keep historical/provenance references when clearly classified.
- Record capability path, citations or local files, and confidence when discovery informs an answer.
- Follow the reviewability warning decision from `docs/ai/specs/.process/TACD-002-design-concept.md`.

### Out of Scope
- Rewriting the consensus protocol.
- Replacing prerequisite checks or plugin limitation docs except for narrow behavior pointers needed by agents.
- Adding final deterministic/eval enforcement.
- Removing historical archive/changelog references.
```

### Files Generated

- [x] `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md`

### Specify Results

| Item | Result |
|------|--------|
| Artifact | `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md` |
| G1 | Passed: `spec.md` exists with 0 `[NEEDS CLARIFICATION]` markers |
| Summary | 4 user stories, 15 functional requirements, 8 acceptance scenarios, 6 success criteria |
| Executor note | `$speckit-specify` was unavailable in the phase executor; the artifact was generated from the local preset template and workflow prompt fallback |
| Clarify carry-forward | Directive path, target surfaces, metadata evidence, generated payload refresh command, and fallback confidence wording |

---

## Phase 2: Clarify

**When to run:** Immediately after Specify if any directive or metadata boundary is ambiguous.

### Clarify Prompts

#### Session 1: Directive Home And Pointer Resolution

```bash
/speckit-clarify Focus on directive home and pointer resolution for TACD-002.

Use `docs/ai/specs/.process/TACD-002-design-concept.md` and `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.

Resolve:
- The exact shared directive path.
- Which Claude/Codex surfaces point to it.
- Which runtime-specific equivalents are acceptable.
- How pointer target resolution should be verified before TACD-004 formalizes enforcement.
```

#### Session 2: Metadata And Generated Payloads

```bash
/speckit-clarify Focus on metadata IDs and generated payload refresh.

Resolve:
- Which exact IDs in runtime/dependency metadata are schema-required and should remain.
- What evidence must show those IDs are metadata, not active preferred-tool behavior.
- Which existing command refreshes generated Claude/Codex payloads from source.
- How to prove generated payloads are source-derived after edits.
```

#### Session 3: Fallback Evidence Language

```bash
/speckit-clarify Focus on fallback behavior and answer evidence.

Resolve:
- The wording agents use for capability path, citations/local file references, and confidence.
- How agents describe fallback when no installed capability covers a need.
- How to avoid full installed-tool inventories in normal answers.
- How formerly named tools can still be selected through discovery without being privileged.
```

### Clarify Results

| Session | Status | Outcome | Consensus |
|---------|--------|---------|-----------|
| Directive Home And Pointer Resolution | Complete | Shared directive path: `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`; in-scope surfaces are the six active Claude agents, six matching Codex TOML agents, and narrow active references in `consensus-protocol.md` and `gate-validation.md`; installed Codex TOML agents may carry compact equivalents with source-note markers; TACD-002 verifies pointer resolution with ad hoc evidence only before TACD-004 enforcement | Skipped: no unresolved items |
| Metadata And Generated Payloads | Complete | Preserve Codex `openai.yaml` dependency values (`tavily`, `context7`) plus Claude frontmatter `tools:` allowlist IDs as metadata; behavior prose and Codex TOML developer instructions must not prefer named optional tools; payloads refresh through `bash scripts/build-plugin-payloads.sh`; source-derived proof is builder output, source/`dist/**` diff review, deterministic payload validation, and `bash tests/speckit-pro/run-all.sh` | Skipped: no unresolved items |
| Fallback Evidence Language | Complete | Discovery-informed answers use `Capability path`, `Evidence`, and `Confidence` fields; missing capability fallback uses local/native/repo-local evidence with lower-confidence disclosure; full inventories are limited to direct requests, troubleshooting, or PR evidence; formerly named tools remain ordinary installed capabilities only when actually selected; `consensus-protocol.md` and `gate-validation.md` get narrow capability-first behavior pointers | Skipped: no unresolved items |

---

## Phase 3: Plan

**When to run:** After spec is finalized.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Repository: Claude Code and Codex plugin marketplace.
- Runtime guidance source: Markdown agents under `speckit-pro/agents/` and TOML agents under `speckit-pro/codex-agents/`.
- Generated payloads: `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`.
- Scripts/tests: Bash-based validation under `tests/speckit-pro/`.
- SpecKit artifacts: `.specify/`, `docs/ai/specs/`, and `specs/tacd-002-capability-discovery-directive-and-agent-updates/`.

## Constraints
- Use the shared directive plus runtime pointers chosen by TACD-001 and confirmed in Clarify.
- Keep TACD-003 prerequisite/user-facing messaging and TACD-004 enforcement out of scope.
- Preserve schema-required metadata IDs with review notes.
- Regenerate generated payloads from source.
- Keep reviewable production LOC at zero unless Clarify discovers a required production change; if scope expands, revisit the reviewability gate.

## Architecture Notes
- The design concept decision is: "Shared reference" for directive structure.
- The source-of-truth decision is: "Regenerate from source" for generated payloads.
- The evidence decision is: "Path + confidence" for discovery-informed answers.
- The metadata decision is: "Preserve metadata" where schemas require concrete IDs.
- Quote and reference `docs/ai/specs/.process/TACD-002-design-concept.md` for all planning choices.
```

### Plan Results

| Item | Result |
|------|--------|
| Artifacts | `plan.md`, `research.md`, `data-model.md`, `contracts/capability-discovery-guidance.md`, `quickstart.md` |
| Context update | `CLAUDE.md` updated with TACD-002 Plan context |
| G3 | Passed: `plan.md` exists with 0 unresolved markers |
| Reviewability estimate | Passed: projected production LOC `0`; declared files: 27 total, 0 production |
| Constitution | Passed with accepted TACD-002 reviewability warning; TACD-003 and TACD-004 remain deferred |
| Implementation risks | Generated payloads must be refreshed from source; installed Codex TOML agents need compact equivalents/source-note markers where direct directive paths would not resolve |

---

## Phase 4: Domain Checklists

### Recommended Domains

#### 1. llm-integration Checklist

```bash
/speckit-checklist llm-integration

Focus on TACD-002 requirements:
- Capability-first discovery semantics across Claude and Codex agent guidance.
- Shared directive pointer coverage or approved runtime-specific equivalent.
- Evidence reporting: capability path, citations/local files, confidence.
- Preservation of formerly named tools only through installed-capability discovery.
- Pay special attention to: avoiding a renamed fixed vendor fallback chain.
```

#### 2. error-handling Checklist

```bash
/speckit-checklist error-handling

Focus on TACD-002 requirements:
- Missing installed capability fallback behavior.
- Lower-confidence reporting when fallback evidence is weaker.
- Avoiding full installed-tool inventory dumps.
- Pay special attention to: fallback wording that overclaims evidence quality.
```

#### 3. integration Checklist

```bash
/speckit-checklist integration

Focus on TACD-002 requirements:
- Claude Markdown agent and Codex TOML agent parity.
- Generated payload refresh from source.
- Runtime/dependency metadata review boundaries.
- Pay special attention to: generated payload drift and unresolved directive pointers.
```

### Checklist Results

| Domain | Status | Gaps | Outcome | Consensus |
|--------|--------|------|---------|-----------|
| llm-integration | Complete | 3 found/fixed; 0 remaining | Added taxonomy-not-chain wording, multi-capability selection criteria, and exact Codex TOML compact-equivalent source-note marker; checklist artifact: `checklists/llm-integration.md`; full verify passed `3041/3041` | Skipped: no unresolved items |
| error-handling | Complete | 2 found/fixed; 0 remaining | Clarified missing, unavailable, and present-but-unusable optional installed capability fallback; constrained fallback confidence to `medium` or `low`; checklist artifact: `checklists/error-handling.md`; full verify passed `3041/3041` | Skipped: no unresolved items |
| integration | Complete | 1 found/fixed; 0 remaining | Declared generated shared-reference payload copies for `capability-discovery.md`, `consensus-protocol.md`, and `gate-validation.md` under both Claude and Codex payload roots; checklist artifact: `checklists/integration.md`; marker count `0` | Skipped: no unresolved items |

### Addressing Gaps

All checklist gaps were resolved in artifacts before G4. No gap was deferred to
TACD-003 or TACD-004.

---

## Phase 5: Tasks

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Generate tasks by user story, not by implementation layer alone.
- Include tests or verification tasks for pointer coverage, generated payload refresh, and active guidance wording.
- Include a reviewability checkpoint before implementation if planned files exceed setup estimates.
- Keep TACD-003 and TACD-004 work explicitly deferred.

## Implementation Phases
1. Directive foundation: create/update shared capability-discovery reference and link strategy.
2. Claude guidance: update active Markdown agent surfaces.
3. Codex guidance: update active TOML/custom-agent surfaces and metadata notes.
4. Generated payload refresh: run the existing distribution path and verify source-derived copies.
5. Verification and PR packet: run focused checks, default suite, and prepare review packet.

## Constraints
- Reference `spec.md`, `plan.md`, and `docs/ai/specs/.process/TACD-002-design-concept.md`.
- Use Non-goals to avoid TACD-003 prerequisite docs and TACD-004 final enforcement work.
- Use the Q&A why-context for task ordering and test coverage.
```

### Tasks Results

| Item | Result |
|------|--------|
| Artifact | `specs/tacd-002-capability-discovery-directive-and-agent-updates/tasks.md` |
| G5 | Passed: 37 tasks found; FR-001 through FR-015 and SC-001 through SC-006 mapped |
| Parallel tasks | 16 tasks marked `[P]` |
| Implementation groups | Directive foundation; Claude guidance; Codex guidance and metadata; Generated payload refresh; Verification and PR packet |
| Reviewability task gate | Size-only block recorded: 1480 reviewable LOC and 83 total files exceeded block thresholds; proceeding to marker planning/final backstop per autopilot protocol |
| Atomicity classifier | Route `one-navigable-PR`; releasable `true`; signal `change-shape:modify-heavy`; no warnings |

---

## Atomicity Route

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true` or `false` |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Warnings | None | Release-safety warnings |

Classifier command:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/tacd-002-capability-discovery-directive-and-agent-updates
```

---

## Layer Plan

Layer planning is skipped for TACD-002 because the atomicity route is
`one-navigable-PR`, not `split-PR`. The task-phase reviewability size block is
tracked for marker planning and the final reviewability backstop.

### Marker Plan

| Field | Value |
|-------|-------|
| Status | `emission_ready` |
| Evidence | `specs/tacd-002-capability-discovery-directive-and-agent-updates/.process/marker-plan/pr-marker-plan.json` |
| Source fingerprint | Recorded in `autopilot-state.json` as `current_source_fingerprint` |
| Markers | `foundation`, `us1`, `us2`, `us3`, `us4` |
| Checkpoints | All markers point to implementation checkpoint commit `3e0392c6` |
| Warning | Reviewability sizing result is marker-planning input |

---

## Phase 6: Analyze

### Analyze Prompt

```bash
/speckit-analyze

Cross-check:
1. `specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md`
2. `specs/tacd-002-capability-discovery-directive-and-agent-updates/plan.md`
3. `specs/tacd-002-capability-discovery-directive-and-agent-updates/tasks.md`
4. `docs/ai/specs/.process/TACD-002-design-concept.md`
5. `specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/*.md`

Focus on:
- Drift between Goals, Non-goals, and generated requirements.
- Accidental TACD-003 prerequisite/user-facing messaging or TACD-004 deterministic/eval enforcement scope creep.
- Pointer coverage gaps across active Claude/Codex agent surfaces.
- Metadata IDs that are treated as behavior preferences rather than schema metadata.
- Missing generated payload refresh or verification.
```

### Analyze Results

| Item | Result |
|------|--------|
| G6 | Passed: 0 CRITICAL/HIGH findings |
| Findings | 1 MEDIUM remediated: Analyze cross-check inputs now include `checklists/*.md` |
| Marker checks | Findings `0`; gaps `0` |
| Consensus | Skipped: no unresolved items |
| Residual risks | Stock numeric/date prerequisite script rejects the TACD branch name; generated payload refresh and final source/dist verification remain implementation tasks |

### Pre-Implement Confidence Emit

📊 Confidence: 0.92

- Task understanding: 0.95
- Approach clarity: 0.90
- Requirements alignment: 0.92
- Risk assessment: 0.88
- Completeness: 0.95

---

## Phase 7: Implement

### Implement Prompt

```bash
/speckit-implement

## Approach
- Start from `tasks.md`, `plan.md`, and `docs/ai/specs/.process/TACD-002-design-concept.md`.
- Use the Q&A log for the reason behind scope, evidence, metadata, and generated-payload decisions.
- Update source guidance first.
- Refresh generated payloads from source.
- Verify focused checks before the default suite.

### Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD`.
2. Verify clean checkpoint or intentional staged setup commit.
3. Re-read TACD-001 spike report and TACD-002 design concept.
4. Confirm the distribution command for generated payload refresh.

### Implementation Notes
- Do not privilege named optional MCP tools in active guidance.
- Do not remove schema-required exact IDs without an equivalent generic declaration path.
- Do not hand-edit generated `dist/**` as durable source.
- Keep answer evidence lightweight: capability path, citations/local files, confidence.
```

### Implement Results

| Item | Result |
|------|--------|
| Tasks | US2 slice T020-T023 complete in `tasks.md`; foundation and US1 are already merged on `main` |
| Shared directive | Updated fallback and degradation behavior in `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` |
| Claude guidance | Preserved merged capability-first agent guidance and added fallback evidence behavior where needed |
| Codex guidance | Preserved merged compact-equivalent agent guidance and added fallback evidence behavior where needed |
| Shared references | Preserved capability-first pointers in `consensus-protocol.md` and `gate-validation.md` |
| Generated payloads | Refreshed generated Claude and Codex payload copies from source |
| Payload coverage | Generated directive and agent copies exist under both `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` |
| Changed-file evidence | `changed-files.txt` is refreshed from the PR #223 diff against `origin/main` |
| Verification | `git diff --check` passed; `bash tests/speckit-pro/run-all.sh --layer 1` passed `1024/1024`; `bash tests/speckit-pro/run-all.sh` passed `3041/3041` |

### Preserved-ID Review Table

| File/Pattern | Field | Classification | Behavior-scan result |
|--------------|-------|----------------|----------------------|
| `speckit-pro/agents/*.md` | YAML frontmatter `tools:` allowlist entries such as `mcp__RepoPrompt__*`, `mcp__tavily-mcp__*`, and `mcp__context7__*` | Schema metadata | Agent body text uses capability-first discovery; preserved IDs are not active preferences |
| `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` | `dependencies.tools[].value` entries `tavily` and `context7` | Runtime dependency metadata | No active behavior prose in the metadata file |
| `dist/claude/speckit-pro/agents/*.md` | Generated frontmatter `tools:` allowlist entries | Generated metadata | Generated from source; body text uses capability-first discovery |
| `dist/codex/speckit-pro/codex-agents/*.toml` | Generated compact-equivalent marker and runtime payload paths | Generated rewrite/runtime metadata | Generated from source; developer instructions use capability-first discovery |

---

## Post-Implementation Checklist

- [x] US2 fallback evidence tasks are complete in `tasks.md`
- [x] Shared directive or approved runtime equivalents include fallback behavior
- [x] Active Claude/Codex US2 guidance describes degradation without requiring optional capabilities
- [x] Metadata IDs are reviewed and classified
- [x] Generated payloads are refreshed from source
- [x] Focused validation passes
- [x] `bash tests/speckit-pro/run-all.sh` passes
- [ ] PR packet includes scope budget, traceability, verification, known gaps, and rollback/flag notes

### Post-Implementation Results

| Item | Status | Evidence |
|------|--------|----------|
| Doctor Extension Check | Skipped | `$speckit-speckit-utils-doctor` / `$speckit-doctor` unavailable in the live Codex skill/command surface |
| Verify Implementation | Skipped | `$speckit-verify` unavailable in the live Codex skill/command surface |
| Verify Tasks Phantom Check | Skipped | `$speckit-verify-tasks` unavailable in the live Codex skill/command surface; `tasks.md` has no open task checkboxes |
| Integration Suite | Complete | `bash tests/speckit-pro/run-all.sh`: `3041/3041` passed |
| Cleanup | Skipped | Cleanup extension not installed |
| Self-Review | Complete | No correctness issues found in scoped source/generated diffs |
| UAT Runbook Generation | Complete | `specs/tacd-002-capability-discovery-directive-and-agent-updates/.process/uat-runbook.md` generated |
| Final Reviewability Backstop | Complete | Full diff remains size-blocked (`52` files) but marker plan is valid and fingerprint-matched; outcome `marker_split` |
| Marker Emission Dry Validation | Complete | `multi-pr-emission.sh` validated 5 marker slices without branch or PR mutation |

---

## Self-Review

### Findings

- No correctness issues found in the scoped US2 source or generated payload diffs.
- Preserved named IDs are confined to allowlist/dependency metadata or generated runtime metadata.
- The reviewability task gate size block remains recorded; final reviewability backstop still decides PR side effects.

### Verification Reviewed

- `git diff --check`: passed.
- `bash tests/speckit-pro/run-all.sh --layer 1`: `1024/1024` passed.
- `bash tests/speckit-pro/run-all.sh`: `3041/3041` passed.

---

## Project Structure Reference

```text
speckit-pro/
  agents/
  codex-agents/
  codex-skills/
  skills/
dist/
  claude/speckit-pro/
  codex/speckit-pro/
tests/speckit-pro/
docs/ai/specs/
docs/ai/specs/.process/
specs/tacd-002-capability-discovery-directive-and-agent-updates/
```

Template based on the shared SpecKit workflow template.

# SpecKit Workflow: SPEC-006a — Deterministic UAT Skeleton + PR Body Integration

**Template Version**: 1.0.0
**Created**: 2026-05-27
**Purpose**: Drive the autopilot through the 7-phase SDD workflow for SPEC-006a. Each phase's prompt is pre-populated from the design concept doc and the Reviewer Experience roadmap.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/SPEC-006a-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The Specify and Clarify Prompts below were populated from that interview, so the design concept doc is the source of truth for any decision captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of the autopilot loop. Once the workflow file is populated and autopilot begins, clarifications happen via `/speckit-clarify` and the consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | spec.md: 4 US, 15 FR, 5 SC, 9 scenarios; G1 pass (0 markers); FR-013 excerpt marker → Clarify S2 |
| Clarify | `/speckit-clarify` | ✅ Complete | 2 sessions; 6 spec edits; FR-013 marker resolved; G2 pass (0 markers) |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass. FR-002=copy helper verbatim (no `BASH_SOURCE` guard in generate-pr-body.sh → sourcing has side effects); FR-013 full-content=`cat` (not the head-40 helper); helper pinned L45-65. **Codex correction:** new script+template are single-copy under `skills/`; Codex calls them by path — lockstep = SKILL.md + `-codex.md` reference twins only (no scripts/templates dir in codex-skills). 11 total files (under warn). |
| Checklist | `/speckit-checklist` | ✅ Complete | 3 domains, 84 items, 7 gaps all remediated in spec/plan; G4 pass (0 gaps); 0 consensus. Note for Analyze: FR-008 env-key schema added → sync into CLI contract doc. |
| Tasks | `/speckit-tasks` | ✅ Complete | 28 tasks, story-organized, TDD-first, 4 [P]; G5 pass; full FR/SC traceability. Reviewability tasks-gate = pass (ratified split exception; raw 1120 LOC/93 files is the path-token heuristic + vendored fixture data — authoritative check is diff-mode at PR). |
| Analyze | `/speckit-analyze` | ✅ Complete | 3 findings (0 CRIT, 1 HIGH, 1 MED, 1 LOW) all remediated; re-run clean; G6 pass; FR/SC 100%; Layer-1/Codex parity clean. G6.5 soft-skip (NO_DATA, advisory). |
| Implement | `/speckit-implement` | ✅ Complete | G7 pass (28/28 tasks). Full suite 1407/1407 (L1 parity green, L4 512, L5 172). shellcheck + `bash -n` clean. Smoke verified: 5 stories (traceability heading excluded via FR-001 precise-pattern fix caught at smoke review). Reviewable LOC 862 (production 389 under budget; 473 mandated test LOC over the 800 line — accepted under ratified split exception). |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Script CLI contract + template-rendering edge cases resolved |
| G3 | After Plan | Reuses `extract_heading_section()`; no new dependencies beyond Bash + jq |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage for all 4 production files + Layer 4 fixtures |
| G6 | After Analyze | No `CRITICAL` issues; consistency between spec, plan, tasks, and design concept |
| G7 | After Implementation | Layer 1 parity test passes; Layer 4 unit test passes; PR body shows `## UAT Runbook` section |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Surface assumptions before editing | State the change shape in chat before touching files | Conversation review |
| Simplest change that solves it | No new abstractions for one-call-site code | `wc -l` on new files vs LOC budget |
| Surgical edits | Touch only what the request requires | `git diff --stat` against `main` |
| Verifiable success criteria | Each phase has a check command | See G1-G7 above |

**Constitution Check:** ✅ Baseline green 2026-05-28 — `bash speckit-pro/tests/run-all.sh` = 1395/1395 (L1 334+389, L4 500, L5 172). PROJECT_COMMANDS override (repo is a bash harness, detect-commands returns N/A): UNIT_TEST=`cd speckit-pro && bash tests/run-all.sh --layer 4`; PARITY=`--layer 1`; FULL_VERIFY=`bash tests/run-all.sh`. Branch-aware override: ON_FEATURE_BRANCH=true, SPECIFY_FEATURE_DIRECTORY=`specs/006a-uat-skeleton` (the `006a-` name breaks SpecKit's 3-digit branch regex, so the dir override is mandatory).

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | SPEC-006a |
| **Name** | Deterministic UAT Skeleton + PR Body Integration |
| **Branch** | `006a-uat-skeleton` |
| **Dependencies** | None |
| **Enables** | SPEC-006b (UAT author agents) |
| **Priority** | P1 |
| **Design Concept** | `docs/ai/specs/SPEC-006a-design-concept.md` |
| **Roadmap** | `docs/ai/specs/reviewer-experience-technical-roadmap.md` |
| **Reviewability Budget** | ~670 LOC, 4 production files, 9 total files (within block thresholds) |

### Success Criteria Summary

- [ ] Skeleton script extracts User Stories, FRs, SCs, Edge Cases from `spec.md` via heading-bounded awk (no inline brackets).
- [ ] All User Story priorities (P1, P2, P3+) are covered — no priority filter.
- [ ] Resume idempotency: regeneration overwrites the prior runbook deterministically; no merge with hand-edits.
- [ ] `generate-pr-body.sh` embeds the runbook inline when under 50_000 chars, otherwise links to the committed file.
- [ ] PR body contains `## UAT Runbook` section on every autopilot-generated PR after this spec ships.
- [ ] Layer 4 unit test passes with 5 fixtures: full vendored snapshot, zero stories, duplicate FRs, `[NEEDS CLARIFICATION]`, missing spec.
- [ ] Layer 1 parity test stays green at every commit (no new agent files).
- [ ] Codex variant edits mirror Claude Code variant in `codex-skills/speckit-autopilot/`.

---

## Phase 1: Specify

**When to run:** First. Output: `specs/006a-uat-skeleton/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Deterministic UAT Runbook Skeleton + PR Body Integration

### Problem Statement

The speckit-pro autopilot finishes every run by creating a PR with build / typecheck / lint / test checkboxes plus a Self-Review block. Neither produces a human-followable, story-by-story acceptance-testing artifact a reviewer (or product owner) can walk to confirm the PR actually delivers the behavior the spec promised.

This spec adds the deterministic infrastructure half of that artifact: a heading-driven UAT runbook skeleton generated from `spec.md`, committed to the spec directory, and embedded in (or linked from) the PR body. LLM-authored narrative test steps are deferred to SPEC-006b — this spec ships the script, template, and PR-body wiring only.

### Users

- **PR reviewers** (human teammates) who need a story-by-story checklist with concrete preconditions and expected observable behavior.
- **The autopilot post-implementation phase** which invokes the skeleton script after Self-Review and before PR creation.
- **External reviewers** without write access — for them the runbook lives in the PR body inline (under 50K chars) or as a link to the committed file.

### User Stories

- **US1 (P1):** As a PR reviewer, I open the PR description and see a `## UAT Runbook` section that lists every user story from the spec with checkbox steps, so I can walk a story without leaving the PR view.
- **US2 (P1):** As a reviewer of an infrastructure spec with no user stories (e.g., SPEC-001 through SPEC-005), I see a runbook keyed by FR-NNN and SC-NNN with a header note explaining the fallback, so generation never silently skips.
- **US3 (P2):** As an autopilot consumer running a multi-resume workflow, I see the runbook regenerate deterministically from the current spec state on each resume — no merge with prior reviewer hand-edits, no stale content from a prior spec version.
- **US4 (P2):** As a maintainer reading the runbook from a cloned working copy, I see the Self-Review findings echoed into the runbook (extracted from the workflow file at the `## Self-Review` heading) so the runbook is self-contained for offline review.

### Functional Requirements

- **FR-001:** A new script `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` MUST parse `### User Story N - <Title> (Priority: PN)` headings, `- **FR-NNN**:` list bullets inside `### Functional Requirements`, `- **SC-NNN**:` list bullets inside `### Measurable Outcomes`, and bullets inside `### Edge Cases`.
- **FR-002:** The script MUST reuse the `extract_heading_section()` awk function from `generate-pr-body.sh` (lines 45-65) — sourced or copied verbatim, not reimplemented.
- **FR-003:** When `spec.md` has zero `### User Story` headings, the script MUST emit a runbook keyed by FR-NNN and SC-NNN with a header note (e.g., `**Note:** This spec has no user stories; tests are keyed by FR/SC.`). It MUST NOT skip generation.
- **FR-004:** When `spec.md` has duplicate FR/SC IDs (e.g., FR-005 appearing twice as in SPEC-004), the script MUST emit the first-seen entry only and write a stderr warning naming the duplicate ID.
- **FR-005:** When `spec.md` contains `[NEEDS CLARIFICATION]` markers, the script MUST propagate them into the runbook with a `**WARN:** unresolved clarification` annotation alongside the bullet.
- **FR-006:** The script MUST emit exit code 0 on success, 2 on usage error (wrong argv), 1 on unreadable spec.
- **FR-007:** The script MUST overwrite any existing `uat-runbook.md` deterministically — no merge with reviewer hand-edits, no append, no skip-if-present.
- **FR-008:** The script MUST accept the autopilot's `PROJECT_COMMANDS` via the env var `UAT_PROJECT_COMMANDS` (JSON string). When unset, the Env Setup section MUST emit `<unknown — autopilot did not pass PROJECT_COMMANDS>` placeholders rather than failing.
- **FR-009:** The script MUST accept an optional `--workflow-file <path>` flag and, when provided, extract the `## Self-Review` block via the same `extract_heading_section()` helper and echo it into the runbook's Self-Review Findings section.
- **FR-010:** A new template `speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md` MUST define sections in this order: Header (spec ID, branch, PR placeholder, generation timestamp), Env Setup, Per-Story Acceptance Tests, FR Coverage Matrix, Negative-Path Tests, Self-Review Findings (echo), Sign-off (advisory), Rollback.
- **FR-011:** The Header's PR field MUST be a static placeholder (e.g., `**PR:** <set on PR open>`). The autopilot MUST NOT rewrite the runbook after PR creation.
- **FR-012:** The Rollback section MUST extract a `## Rollback` heading from `spec.md` (or `plan.md` as fallback) when present; otherwise emit a synthesized stanza `git revert <SHA>; see plan.md for data-migration considerations`.
- **FR-013:** `generate-pr-body.sh` MUST add `"UAT Runbook"` to the heading list at line 171 AND add a corresponding section to the `review_packet` heredoc that reads `<feature-dir>/uat-runbook.md`. When the runbook is under 50_000 chars, embed full content via `extract_heading_section`; otherwise embed the first ~60 lines and append a relative link.
- **FR-014:** The Claude Code autopilot (`speckit-pro/skills/speckit-autopilot/`) and the Codex variant (`speckit-pro/codex-skills/speckit-autopilot/`) MUST be edited in lockstep — same content, runtime-appropriate primitives. No new agent files are introduced in this spec.
- **FR-015:** A new Layer 4 unit test `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh` MUST cover five fixtures: vendored full-spec snapshot (under `speckit-pro/tests/layer4-scripts/fixtures/spec-full-snapshot.md`), synthetic zero-stories, synthetic duplicate-FR, synthetic `[NEEDS CLARIFICATION]`, and missing-spec error case.

### Measurable Outcomes

- **SC-001:** A standalone run of `generate-uat-skeleton.sh` against `specs/004-integration-verification/spec.md` produces a runbook with every user story present (count matches `grep -c '^### User Story' spec.md`).
- **SC-002:** A standalone run against a synthetic zero-stories spec produces a runbook with the FR/SC fallback header note and at least one FR-keyed and one SC-keyed test section.
- **SC-003:** `bash speckit-pro/tests/run-all.sh --layer 4` exits 0 with the new test included.
- **SC-004:** `bash speckit-pro/tests/run-all.sh --layer 1` exits 0 after the change (Codex parity preserved — no new agent files).
- **SC-005:** A PR generated by autopilot after this spec ships contains a `## UAT Runbook` heading in its body and a committed `uat-runbook.md` under the spec directory.

### Constraints

- **Reviewability budget:** ~670 LOC, 4 production files (template, script, modified `generate-pr-body.sh`, Layer 4 test), 9 total files. Under the 800 LOC / 8 prod / 25 total block thresholds.
- **Single primary surface:** docs/process (template + script + autopilot SKILL.md edits).
- **Bash + jq only:** no new dependencies. Match the existing speckit-pro script conventions.
- **Conventional Commits PR title** with plain-English body (the racecraft-plugins-public public-readable PR convention).
- **No agent files added** — Layer 1 parity test (`validate-codex-parity.sh`) must stay green at every commit.

### Out of Scope

- LLM-authored narrative test step prose (SPEC-006b).
- New Claude Code or Codex agent files (SPEC-006b).
- Layer 5 tool scoping fixtures (no new agent yet).
- Layer 7 integration fixtures with author-agent simulation (SPEC-006b).
- Pass/fail blocking gate on UAT (rejected; advisory only — see design concept).
- 3-way merge of regenerated runbook with reviewer hand-edits (rejected; deterministic overwrite — see design concept Q4).
- Autopilot rewriting runbook after PR creation to fill in the PR URL (rejected; static placeholder — see design concept Q1).
- Standalone `/speckit-pro:regenerate-uat` skill (YAGNI — revisit if a second use case emerges).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | FR-001 through FR-015 |
| User Stories | 4 (US1-P1, US2-P1, US3-P2, US4-P2) |
| Acceptance Criteria | SC-001 through SC-005 |

### Files Generated

- [x] `specs/006a-uat-skeleton/spec.md`

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. The design concept doc already resolved the largest scoping decisions; remaining clarifications target script CLI shape and template-rendering edge cases.

**Best Practice:** Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Script CLI Contract

```bash
/speckit-clarify Focus on the script CLI contract: argv positional vs flag ordering for `generate-uat-skeleton.sh`. Specifically:
- Argv[1] is the spec.md path; argv[2] is the output runbook path (current plan). Are additional positional args needed for feature-dir or spec-id, or should those derive from argv[1] via dirname?
- Should `--workflow-file <path>` (from design concept Q3) be a flag or an env var (e.g., `UAT_WORKFLOW_FILE`)? Cross-check with FR-008's env-var choice for PROJECT_COMMANDS.
- What happens when both argv[2] output path and an existing runbook collide? Plan says deterministic overwrite — confirm no `--force` flag is needed.
- Should the script print anything to stdout (success message, summary) or stay silent on success?
- Are stderr warnings (FR-004 duplicate IDs, FR-005 clarification markers) prefixed with a standard tag like `[UAT-WARN]` for grep-ability?
```

#### Session 2: Template Rendering Edge Cases

```bash
/speckit-clarify Focus on template-rendering edge cases:
- FR Coverage Matrix anchor format — GitHub-style markdown anchor (e.g., `#user-story-1-feature-x`) computed from heading text, or explicit `<a name="us1">` injection? The matrix needs to navigate from FR row to story section.
- When `### Edge Cases` is absent from spec.md, does the Negative-Path Tests section emit a stub line (`No edge cases identified in spec.md`) or omit the section header entirely?
- When the runbook is over 50_000 chars and the PR body shows only the first ~60 lines + link (FR-013), what does "first ~60 lines" mean exactly — first 60 markdown lines, first 60 non-blank lines, or up to the first User Story section boundary?
- For Sign-off (advisory), the template has checkboxes. Does any string of unchecked checkboxes block anything (it should not — advisory only), or is the section purely visual?
- Multi-line bullet continuation in spec.md (e.g., FR with sub-bullets) — does the script include sub-bullets verbatim or flatten them?
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Script CLI Contract | 5 (3 spec edits, 2 confirmed) | argv = 2 positionals (spec, output); feature-dir via `dirname argv[1]` (FR-001). stdout silent on success (FR-006). stderr warning plain/unprefixed (FR-004). Confirmed: `--workflow-file` flag + `UAT_PROJECT_COMMANDS` env asymmetry is intentional (DC Q2/Q3); deterministic overwrite, no `--force` (FR-007). Q5 stderr-tag resolved [codebase]: no consumer greps a tag, no bracket-tag convention exists → plain message. |
| 2 | Template Rendering Edge Cases | 5 (3 spec edits, 2 confirmed) | FR-013 marker resolved → over-threshold excerpt = `head -60` (blanks preserved); Plan note: under-threshold "full content" must NOT reuse `extract_heading_section` (head-40/blank-strip). Absent Edge Cases → header + stub line (FR-010). Nested bullets verbatim (FR-001). FR Coverage Matrix anchors resolve in committed runbook; mechanism = Plan decision (default explicit anchors) [Q1 codebase+domain → KISS/no-precedent]. Sign-off advisory-only confirmed. 0 markers; G1/G2 pass. |

---

## Phase 3: Plan

**When to run:** After spec is finalized.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash (macOS/Linux), per CLAUDE.md "no new dependencies — prefer plain bash + jq"
- JSON parsing: `jq` (already a hard prerequisite for the autopilot)
- Awk: extract_heading_section() helper, reused verbatim from `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` lines 45-65
- Test harness: `speckit-pro/tests/lib/assertions.sh` (assert_eq, assert_contains, assert_file_exists, assert_exit_code, test_summary)
- Layer 4 fixtures: mktemp -d with trap cleanup (existing pattern from `test-ensure-reviewability-preset.sh`)
- CI: GitHub Actions `pr-checks.yml` matrix; new Layer 4 test auto-discovered by `tests/run-all.sh --layer 4`
- Release: release-please (no version-file change needed for this spec — script + template additions only)

## Constraints
- Single PR; reviewability budget ~670 LOC, 4 production files (script, template, modified generate-pr-body.sh, Layer 4 test), 9 total files
- No new agent files (Layer 1 parity invariant — see design concept Goals)
- Codex variant edits in lockstep (no semantic divergence between speckit-pro/skills/ and speckit-pro/codex-skills/)
- All scripts pass shellcheck (existing CI gate)
- The vendored Layer 4 fixture (`speckit-pro/tests/layer4-scripts/fixtures/spec-full-snapshot.md`) is a frozen copy of specs/004-integration-verification/spec.md as of merge — design concept Q4 ratified vendoring over live read

## Architecture Notes
- Reuse, don't reimplement: `extract_heading_section()` awk function is the existing battle-tested heading-bounded extractor; the new script sources it via `source "$(dirname "$0")/generate-pr-body.sh"` (if it exports it) or copies the function verbatim. Plan should decide which.
- Script contract per design concept:
  - `UAT_PROJECT_COMMANDS` env var (JSON string) — FR-008
  - `--workflow-file <path>` flag for Self-Review extraction — FR-009 / design concept Q3
  - argv[1] spec path, argv[2] output path
- PR-body integration per design concept Q2 (the heading is always emitted; content depends on size — under 50_000 chars embed, otherwise link)
- Self-Review section per design concept Q3 (read from workflow file at known heading via extract_heading_section)
- PR URL handling per design concept Q1 (static placeholder, no rewrite)
- Layer 4 fixture per design concept Q4 (vendor a snapshot, not live read)
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Technical context, execution flow, 4 decisions resolved |
| `research.md` | N/A | Decisions captured in design concept + plan |
| `data-model.md` | N/A | No persistent data model |
| `contracts/` | ✅ | `generate-uat-skeleton-cli.md` — argv/env/flag/exit-code contract |
| `quickstart.md` | ✅ | Standalone-run example for maintainers |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`.

### Step 1: Recommended Domains

Based on the spec's signals:

| Signal | Domain | Rationale |
|---|---|---|
| Script CLI contract (env vars, flags, exit codes) | **api-contracts** | The script IS an API — autopilot depends on its argv/env/exit-code shape |
| Exit codes 0/1/2, stderr warnings, fail-open in autopilot | **error-handling** | The script's failure-mode taxonomy is load-bearing for the autopilot's fail-open guarantee |
| Reading spec.md / overwriting uat-runbook.md / preserving Self-Review echo | **data-integrity** | File-system operations need to be predictable across resumes and on partial inputs |

### Step 2: Enriched Checklist Prompts

#### 1. api-contracts Checklist

The script IS the API surface this spec ships. Autopilot post-impl wiring will call it by exact name; if the contract drifts, every future autopilot run breaks.

```bash
/speckit-checklist api-contracts

Focus on SPEC-006a requirements:
- argv positional contract (spec path, output path) and exit code taxonomy (0/1/2 per FR-006)
- Env var contract: `UAT_PROJECT_COMMANDS` JSON schema (which keys? optional? validation?)
- Flag contract: `--workflow-file <path>` (optional, used for Self-Review echo)
- PR body section heading (`## UAT Runbook`) — does anything else in the autopilot depend on this exact string?
- Pay special attention to: backwards-compat — the script will be called by both Claude Code and Codex autopilot variants; no runtime-specific behavior may leak in
```

#### 2. error-handling Checklist

Fail-open is the autopilot's guarantee — the script must never block PR creation. This domain checks every failure path.

```bash
/speckit-checklist error-handling

Focus on SPEC-006a requirements:
- Missing spec.md → exit 1, autopilot fails open (emits stub runbook + PR-body note)
- Malformed YAML in env var → graceful fallback to placeholders, not crash
- Missing `### Edge Cases` heading → omit section or stub line (decided in Clarify Session 2)
- Duplicate FR/SC IDs → stderr warning + dedupe first-seen (FR-004)
- `[NEEDS CLARIFICATION]` propagation → annotated, not silently dropped (FR-005)
- Pay special attention to: the autopilot fail-open path — what exactly lands in the PR body when the script returns nonzero? Does the `## UAT Runbook` heading still appear with a `<UAT generation failed: see autopilot log>` note?
```

#### 3. data-integrity Checklist

File-system operations across autopilot resumes are where deterministic-overwrite-vs-merge bugs typically land.

```bash
/speckit-checklist data-integrity

Focus on SPEC-006a requirements:
- Deterministic overwrite of `uat-runbook.md` on every run (FR-007); no merge with reviewer hand-edits
- The vendored Layer 4 fixture (`spec-full-snapshot.md`) is frozen at merge — confirm no test reads `specs/004-integration-verification/spec.md` directly
- Multi-line bullet continuation in spec.md — awk fold must not corrupt nested list structure
- `extract_heading_section()` heading boundary semantics — does the closing boundary include or exclude the next heading line?
- Pay special attention to: what happens when the autopilot script runs from a worktree but the spec lives one level up (`../spec.md`)? Path resolution must be absolute or relative to argv[1].
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contracts | 30 | 0 | FR-001/006/008/009/013 |
| error-handling | 27 | 0 | FR-005/006/008/009 + autopilot fail-open |
| data-integrity | 27 | 0 | FR-007 + helper boundary semantics + worktree path resolution |
| **Total** | 84 | 0 | 7 gaps remediated in-place (spec FR-008 + Edge Cases; plan FR-013 Wiring + Decision 1) |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/006a-uat-skeleton/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-001 through FR-015
- Dependency ordering: template skeleton → script extractor → Layer 4 fixtures → PR-body integration → autopilot wiring (CC + Codex)
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story (US1-US4), not by technical layer

## Implementation Phases
1. **Foundation:** Vendor the Layer 4 fixture (`spec-full-snapshot.md`); create the empty template file scaffold
2. **US1 (P1) — Reviewer sees `## UAT Runbook` in PR body:**
   - `generate-uat-skeleton.sh` extractor for User Story headings + FR/SC bullets
   - `uat-runbook-template.md` Header + Env Setup + Per-Story Acceptance Tests + FR Coverage Matrix sections
   - `generate-pr-body.sh` heading-list extension + size-aware embed
   - Layer 4 test for full-spec fixture
3. **US2 (P1) — Reviewer of infra spec sees FR/SC-keyed runbook:**
   - Script handles zero-user-stories branch (FR-003)
   - Layer 4 test for zero-stories fixture
4. **US3 (P2) — Autopilot resume regenerates deterministically:**
   - Script overwrites (FR-007) — no `--force` flag; no skip-if-present logic
   - Layer 4 test confirms overwrite (run twice, compare)
5. **US4 (P2) — Self-Review echo for offline review:**
   - `--workflow-file <path>` flag implementation (FR-009)
   - Layer 4 test for Self-Review extraction
6. **Polish & cross-cutting:**
   - Codex variant mirror edits (parallel SKILL.md / references / task-list-canonical.md)
   - Edge-case fixtures (duplicate-FR, `[NEEDS CLARIFICATION]`, missing-spec)
   - Update `references/post-implementation.md` §3.1b in both variants
   - Update `references/task-list-canonical.md` 12 → 13 entries in both variants
   - Update autopilot SKILL.md Step 3 reference in both variants

## Constraints
- All scripts pass shellcheck
- Codex variant edits land in the same commit as Claude Code edits (Layer 1 parity)
- Vendored fixture lives under `speckit-pro/tests/layer4-scripts/fixtures/` — verify the dir exists or create it
- No new agent files; no edits to `agents/` or `codex-agents/`
- Conventional commits prefix on every commit (e.g., `feat(speckit-pro): add UAT skeleton extractor`)
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 28 |
| **Phases** | 7 (Setup, Foundational, US1, US2, US3, US4, Polish) |
| **Parallel Opportunities** | 4 `[P]`: vendored fixture, template scaffold, test harness, Codex `-codex.md` doc twins |
| **User Stories Covered** | US1-US4 (all); RED Layer-4 assertion precedes GREEN impl per story |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Cross-artifact consistency between spec.md, plan.md, tasks.md, AND `docs/ai/specs/SPEC-006a-design-concept.md`. The design concept is the source of truth for the 4 grill-me decisions (PR URL placeholder, PROJECT_COMMANDS env var, Self-Review echo source, Layer 4 fixture vendoring). Flag any downstream artifact that contradicts a design concept decision.
2. Coverage gaps — every FR-001 through FR-015 must map to at least one task; every SC-001 through SC-005 must map to a verification command in the implementation phase.
3. Reviewability budget alignment — sum the estimated LOC for all production tasks; flag if the total exceeds the 800-LOC block threshold (with no exception ratified for this spec).
4. Layer 1 parity — confirm no task adds files under `speckit-pro/agents/` or `speckit-pro/codex-agents/`. If any task does, that's a CRITICAL finding for this spec (defer to SPEC-006b).
5. Codex parity — every Claude Code edit task has a paired Codex edit task in the same phase.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation; violates parity invariant or budget | Must fix before G6 |
| `HIGH` | Significant gap; impacts US1-US4 coverage | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| F1 | HIGH | spec FR-013 "add to heading list (line 171)" contradicts plan/tasks — that loop routes through the truncating `extract_heading_section` | Reworded FR-013 to mandate a dedicated `## UAT Runbook` H2 block (NOT via the heading loop / `append_missing_section` / `extract_heading_section`); spec owns *what*, plan owns *how*. Design-concept intent preserved. |
| C1 | MEDIUM | `contracts/generate-uat-skeleton-cli.md` missing FR-008 env-key schema (Checklist-flagged) | Added 7-key schema (`BUILD/TYPECHECK/LINT/LINT_FIX/UNIT_TEST/INTEGRATION_TEST/SINGLE_FILE_INTEGRATION`) + `N/A` sentinel rule to contract |
| L1 | LOW | total-file count 9 (spec) vs 11 (plan/tasks) | Reconciled spec to 11 at Reviewability Budget + Constraints |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First (Bash flavor)

For each task touching `generate-uat-skeleton.sh`:

1. **RED:** Add a new assertion to `tests/layer4-scripts/test-generate-uat-skeleton.sh` that exercises the behavior. Run the test — it must FAIL (script not yet implemented or fixture mismatch).
2. **GREEN:** Add the minimum script logic to make the assertion pass. Run `bash speckit-pro/tests/run-all.sh --layer 4` and confirm green.
3. **REFACTOR:** Tidy the new code while tests stay green. No new abstractions unless a second call site exists.
4. **VERIFY:** Run a manual smoke test against the vendored Layer 4 fixture and against `specs/004-integration-verification/spec.md` from the parent repo, comparing output sanity.

### Pre-Implementation Setup

Before starting any task in the worktree (.worktrees/006a-uat-skeleton):

1. Confirm the reviewability preset resolves: `specify preset resolve spec-template plan-template tasks-template`
2. Confirm Layer 1 baseline is green: `bash speckit-pro/tests/run-all.sh --layer 1`
3. Confirm the existing `extract_heading_section()` awk helper still lives at the same line range in `generate-pr-body.sh` (Plan should have pinned the line range — re-verify)
4. Confirm `jq` is available on PATH

### Implementation Notes

- **Match existing shell style** in `speckit-pro/skills/speckit-autopilot/scripts/` — strict mode (`set -euo pipefail`), explicit variable quoting, `[[ ]]` over `[ ]`, function-scoped `local`.
- **Conventional commits:** every commit prefixed (`feat(speckit-pro): ...`, `test(speckit-pro): ...`, `docs(speckit-pro): ...`). PR title and body must be plain-English public-readable per CLAUDE.md.
- **No agent file edits** — confirm `git diff --name-only` does not include anything under `speckit-pro/agents/` or `speckit-pro/codex-agents/`.
- **Codex parity in same commit:** when editing a `speckit-pro/skills/speckit-autopilot/` file, edit the `speckit-pro/codex-skills/speckit-autopilot/` counterpart in the same commit (same hunks where the content is identical).
- **Consult the design concept's Q&A entries** when an edge case needs disambiguation — the Q&A entries are the source of truth, not an opinion the implementor can override.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 — Foundation | T001-T006 | 6 | Vendored fixture, template scaffold, test harness, budget |
| 2 — US1 (P1) | T007-T011 | 5 | Skeleton extractor + template bodies + dedicated `## UAT Runbook` H2 PR-body block |
| 3 — US2 (P1) | T012-T013 | 2 | Zero-stories FR/SC fallback + header note |
| 4 — US3 (P2) | T014-T015 | 2 | Deterministic overwrite (spec-mtime-stable, byte-identical reruns) |
| 5 — US4 (P2) | T016-T017 | 2 | `--workflow-file` Self-Review echo + stub fallback |
| 6 — Polish | T018-T028 | 11 | Env Setup formatter, Rollback, marker propagation, dup-ID/exit codes, 5 fixtures, CC+Codex lockstep docs, shellcheck, smoke |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md` (28/28)
- [x] `bash speckit-pro/tests/run-all.sh --layer 1` exits 0 (Codex parity intact)
- [x] `bash speckit-pro/tests/run-all.sh --layer 4` exits 0 with the new test included (572/572; `test-generate-uat-skeleton` registered in the runner)
- [x] `bash speckit-pro/tests/run-all.sh` (default Layers 1, 4, 5) exits 0 — 1467/1467
- [x] Standalone smoke test produces a runbook with all real stories (5 against spec 004; the traceability sub-heading is correctly excluded by the FR-001 numbered-pattern)
- [x] Dogfood verification: `specs/006a-uat-skeleton/uat-runbook.md` generated from this spec — renders 4 stories, the real edge cases, and the echoed self-review
- [x] Reviewability: production code 389 LOC (under budget); full diff larger due to the SDD trail + vendored fixture; runs under the ratified split exception
- [x] PR title and body are plain-English public-readable per CLAUDE.md
- [x] PR created with Conventional Commits prefix — **PR #99** (https://github.com/racecraft-lab/racecraft-plugins-public/pull/99)
- [ ] Merged to main via squash-merge — **left for a human reviewer (autopilot never merges)**

---

## Self-Review

Post-implementation self-check (4 questions, mirroring the autopilot Self-Review pattern).

1. **Did all tests run and pass?** Yes — full suite green at 1467/1467 (L1 parity 334+389, L4 572 including the newly-registered `test-generate-uat-skeleton` at 60/60, L5 172). `shellcheck` and `bash -n` clean on both scripts.
2. **Are all requirements traced to code and tests?** Yes — FR-001..FR-015 each map to at least one task and assertion; SC-001..SC-005 map to verification commands (tasks.md traceability table). Smoke run against spec 004 confirms SC-001 (5 real user stories; the traceability sub-heading is correctly excluded).
3. **Were the gates validated?** G1-G7 all pass via `validate-gate.sh`; G6.5 confidence gate soft-skipped (advisory, no consensus emit).
4. **Known gaps / risks?** (a) Reviewable LOC 862 exceeds the 800 line — production code is 389 (under budget); the overage is constitution-mandated Layer 4 test coverage, accepted under the roadmap's ratified split exception. (b) FR-009 Self-Review echo caps at 40 lines (the reused helper's behavior — spec-conformant). (c) Matrix `<a id>` anchors rely on GitHub markdown rendering (not locally verifiable). (d) LLM-authored narrative test steps are deferred to SPEC-006b.

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```
racecraft-plugins-public/
├── speckit-pro/
│   ├── agents/                                   ← NO CHANGES this spec (Layer 1 parity)
│   ├── codex-agents/                             ← NO CHANGES this spec
│   ├── skills/speckit-autopilot/
│   │   ├── SKILL.md                              ← Modified: Step 3 reference
│   │   ├── scripts/
│   │   │   ├── generate-pr-body.sh               ← Modified: heading list + size-aware embed
│   │   │   └── generate-uat-skeleton.sh          ← NEW
│   │   ├── templates/
│   │   │   └── uat-runbook-template.md           ← NEW
│   │   └── references/
│   │       ├── post-implementation.md            ← Modified: new §3.1b
│   │       └── task-list-canonical.md            ← Modified: 12 → 13 tasks
│   ├── codex-skills/speckit-autopilot/           ← Parallel edits to all four files above
│   └── tests/layer4-scripts/
│       ├── test-generate-uat-skeleton.sh         ← NEW
│       └── fixtures/spec-full-snapshot.md        ← NEW (vendored)
└── docs/ai/specs/
    ├── reviewer-experience-technical-roadmap.md  ← Read-only reference
    ├── SPEC-006a-design-concept.md               ← Source of truth for grill-me decisions
    └── SPEC-006a-workflow.md                     ← This file
```

---

Template based on SpecKit best practices. Populated for SPEC-006a from the Reviewer Experience roadmap and the SPEC-006a design concept doc.

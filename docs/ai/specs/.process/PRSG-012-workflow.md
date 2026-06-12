# SpecKit Workflow: PRSG-012 - Reviewer-ready PR packet contract

**Template Version**: 1.0.0
**Created**: 2026-06-11
**Purpose**: Drive the autopilot through PRSG-012 so generated PR titles and bodies are deterministic, reviewer-ready, and validated before any PR is opened.

---

## Design Concept

This workflow was enriched from a Grill Me interview run during `$speckit-scaffold-spec`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/PRSG-012-design-concept.md
```

The design concept is the source of truth for these scoping decisions:

- Use one shared deterministic PR packet validator script.
- Make the generated packet own the PR title.
- Generate canonical reviewer sections directly.
- Keep both `How To UAT` and the literal `## UAT Runbook` compatibility heading.
- Allow edits only inside explicit editable prose fields.
- Write validation failure JSON plus a workflow event.
- Keep post-create auto-repair as a follow-up, not part of PRSG-012.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Generated `specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md`; G1 passed with 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | G2 passed with packet schema, title generation, and safe-refinement decisions recorded |
| Plan | `/speckit-plan` | Complete | Generated plan/research/data model/contract/quickstart; G3 passed |
| Checklist | `/speckit-checklist` | Complete | API contracts, error handling, and reliability checklists complete; G4 passed |
| Tasks | `/speckit-tasks` | Complete | Generated 56 tasks across Foundation, US1-US4, and Polish; G5 passed |
| Analyze | `/speckit-analyze` | Complete | 5 findings remediated in `tasks.md`; marker counter clean; G6 passed |
| Implement | `/speckit-implement` | In Progress | Phase 7 US4 safe refinement active after completing Foundation, US1, US2, and US3 |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories cover generated titles, body contract, pre-create validation, and safe refinement |
| G2 | After Clarify | Packet schema/title ambiguities resolved or explicitly deferred |
| G3 | After Plan | Reviewability budget and test matrix approved |
| G4 | After Checklist | All true gaps addressed or documented as non-goals |
| G5 | After Tasks | Tasks map to every user story and validation path |
| G6 | After Analyze | No CRITICAL issues |
| G7 | After Implementation | L4 plus relevant L1/L3/L7/L8 evidence recorded |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Keep plugin files under `speckit-pro/`; tests remain under `tests/speckit-pro/` | `bash tests/speckit-pro/run-all.sh --layer 1` |
| Script Safety | New or changed shell scripts use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and deterministic exits | `bash tests/speckit-pro/run-all.sh --layer 1` and Layer 4 script tests |
| Test Coverage Before Merge | New deterministic validation logic has Layer 4 fixtures; skill behavior has L3/L8 coverage | L4, L3, L7, L8 evidence |
| Conventional Commits | Setup and implementation commits use repo convention | `git log --oneline` and CI title check |
| KISS, Simplicity & YAGNI | Prefer one shared validator script over duplicated call-site logic | Plan review |

**Constitution Check:** Verified 2026-06-12. Baseline `bash tests/speckit-pro/run-all.sh --layer 1` passed `978/978`; baseline `bash tests/speckit-pro/run-all.sh --layer 4` passed `1419/1419`.

---

## Specification Context

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-012 |
| **Name** | Reviewer-ready PR packet contract |
| **Branch** | `prsg-012-reviewer-ready-pr-packet-contract` |
| **Feature directory** | `specs/prsg-012-reviewer-ready-pr-packet-contract` |
| **Design Concept** | `docs/ai/specs/.process/PRSG-012-design-concept.md` |
| **Dependencies** | PRSG-009, SPEC-006a/b, PRSG-010 |
| **Priority** | P1 |
| **Reviewability estimate** | 245 reviewable LOC, one suggested slice, status `ok` |
| **Required layers** | L4, L3, L7, L8; L1 for structural/parity safety |

### Success Criteria Summary

- Both single-PR and split-PR paths pass `--base`, `--head`, `--title`, and `--body-file` to `gh pr create`.
- Generated titles identify the reviewer-visible change, not just a branch or slice code.
- Generated bodies include canonical sections: `Summary`, `What Changed`, `Why It Matters`, `How To Review`, `How To UAT`, `Verification`, `Scope`, and `Known Gaps`.
- Generated bodies keep the literal `## UAT Runbook` compatibility heading.
- Invalid packets block before PR creation and write deterministic remediation evidence.
- Safe refinement is limited to explicit editable prose fields.

---

## Phase 1: Specify

**When to run:** At the start of PRSG-012. Output: `specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Reviewer-ready PR packet contract

### Problem Statement
PRSG-009 made split PRs possible, SPEC-006a/b added UAT runbook wiring, and PRSG-010 hardened the final reviewability backstop. The remaining reviewer-experience gap is that generated PR titles and descriptions can still be vague, incomplete, stale, or dependent on manual cleanup after creation. PRSG-012 makes the PR packet deterministic and validated before `gh pr create`.

### Users
- Maintainers reviewing autopilot-generated PRs.
- Operators running `$speckit-autopilot` in single-PR or split-PR mode.
- Future agents that need a stable packet contract before opening PRs.

### User Stories
1. As a reviewer, I see a specific conventional PR title that names the visible or operator-visible change.
2. As a reviewer, I see a neutral structured body with Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, and Known Gaps.
3. As an operator, invalid packets block before PR creation with exact remediation evidence.
4. As a maintainer, I can refine sanctioned prose fields without damaging generated governance sections, source markers, UAT content, traceability, scope, or verification evidence.

### Functional Requirements
- Generate a packet-owned PR title for both single-PR and split-PR paths.
- Pass `gh pr create --base <base_branch> --head <head_branch> --title <generated-title> --body-file <generated-body>` in every PR creation path.
- Add one shared deterministic PR packet validator script invoked before every `gh pr create`.
- Validate rendered title/body text, not only JSON schema shape.
- Reject stale placeholders, unfilled template comments, missing source markers, missing required headings, missing verification/scope evidence, and banned labels such as `ELI5` or `Plain-English Summary`.
- Keep the literal `## UAT Runbook` compatibility heading while adding the reviewer-facing `How To UAT` section.
- Write validation JSON under the feature `.process` tree and append a concise workflow event when validation blocks.
- Treat post-create auto-repair as a follow-up, not PRSG-012 scope.

### Constraints
- Bash plus `jq`; no new runtime dependencies.
- Scripts-first: deterministic logic belongs in scripts with Layer 4 fixtures.
- Preserve Codex parity for any mirrored autopilot skill/reference behavior.
- Keep edits scoped to `speckit-pro/skills/speckit-autopilot`, contracts, tests, and generated docs needed for PRSG-012.
- Do not weaken existing UAT runbook guarantees from SPEC-006a/b.

### Out of Scope
- Broad post-create repair of already-open PRs.
- Agent-authored PR packet first drafts.
- Removing host template support when it can safely coexist.
- Replacing the existing UAT Runbook compatibility heading.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 18 |
| User Stories | 4 |
| Acceptance Criteria | 13 acceptance scenarios |

### Files Generated

- [x] `specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md`
- [x] `specs/prsg-012-reviewer-ready-pr-packet-contract/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** Only if Specify leaves packet schema, title generation, or failure evidence ambiguous.

### Clarify Prompts

#### Session 1: Packet Schema

```bash
/speckit-clarify Focus on PR packet schema: decide whether to extend `slice-packet.schema.json` directly or introduce a shared `pr-packet.schema.json`; define required fields for title, body file, section metadata, verification evidence, scope evidence, UAT source, source markers, and editable field boundaries.
```

#### Session 2: Title Generation

```bash
/speckit-clarify Focus on generated titles: define title sources for single PRs and slice PRs; keep conventional commit format; require plain-English descriptions; reject post-colon descriptions containing branch names, slice ids, internal codes, placeholders, or banned labels.
```

#### Session 3: Safe Refinement

```bash
/speckit-clarify Focus on safe prose refinement: define the exact editable markers and validator behavior when a human or agent edits outside those fields.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Packet schema | 5 | Add a shared `pr-packet.schema.json`; keep `slice-packet.schema.json` as split-slice evidence/source input. Required packet fields: schema version, packet id, mode, target, generated title, body file, required sections, verification evidence, scope evidence, UAT source, rendered source/provenance markers, editable fields, validation result path, and split slice identity or source slice packet path. Validation JSON is one record per packet under `.process/pr-packets/<packet_id>/validation.json`. Legacy `speckit-pro-review-packet-source` HTML comments are compatibility-only and do not satisfy protected source-marker validation. Editable prose is limited to explicit blocks under `Summary`, `What Changed`, and `Why It Matters`. |
| 2 | Titles | 5 | Generated PR packet titles use `<type>(<scope>): <plain-English description>`. Implementation packets default to `feat(speckit-pro):`; only explicit packet metadata may override type or scope. Valid types are `feat`, `fix`, `chore`, `docs`, `refactor`, and `test`. Single-PR title descriptions come from the feature/spec display title normalized into an action phrase. Split-PR title descriptions come from PR marker `source_boundary.section`, falling back to layer-plan increment names for legacy layer-plan mode. The structured `generated_title` object owns the final value, type, scope, description, source evidence, and rejected candidates. Descriptions must name the visible or operator-visible change in public-readable language and must not contain branch refs, slice IDs, PRSG/SPEC/FR/SC/L# tokens, placeholders, unexpanded variables, or banned labels. |
| 3 | Safe refinement | 5 | Use exact full-line editable HTML comment marker pairs under `Summary`, `What Changed`, and `Why It Matters`, such as `<!-- speckit-pro-editable:summary:start -->` and `<!-- speckit-pro-editable:summary:end -->`, mirrored in packet JSON. Store a normalized protected-body fingerprint with editable blocks elided and fail validation when any non-editable content changes. Allow only editable-boundary comments and the legacy `speckit-pro-review-packet-source` compatibility comment; reject unknown or stale template comments outside code fences. Canonical PRSG-012 packet sections render first; host template content may appear only outside the protected packet block. Outside-field edits fail before PR creation with validation JSON, `pr_blocked: true`, rule ids, affected section/field, excerpt or hash evidence, remediation text, and exit `1`; usage/input errors exit `2`. |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/prsg-012-reviewer-ready-pr-packet-contract/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Runtime: Bash 4+ shell scripts
- Data: JSON Schema 2020-12 contracts and `jq`
- Repo surfaces: Markdown skill/reference docs, shell scripts, Layer 4 shell fixtures, L3/L7/L8 eval fixtures
- GitHub boundary: `gh pr create --base --head --title --body-file`

## Architecture Notes
- Add one shared validator script, likely `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh`.
- Add a shared `pr-packet.schema.json` so a packet owns: structured generated-title metadata, body file path, source feature dir, required headings, verification evidence, scope evidence, UAT source, rendered source/provenance markers, editable prose fields, validation result path, and split slice identity when applicable. Keep `slice-packet.schema.json` as slice evidence/source input.
- `generated_title` is an object with final `value`, conventional commit `type`, `scope`, public-readable `description`, source evidence, and rejected candidates. Implementation packets default to `feat(speckit-pro):`; type/scope overrides come only from explicit packet metadata.
- Single-PR title descriptions come from the feature/spec display title normalized into an action phrase. Split-PR title descriptions come from PR marker `source_boundary.section`, falling back to layer-plan increment names in legacy layer-plan mode. Branch names, spec ids, slice ids, task ids, and file paths remain metadata only.
- Safe prose refinement uses exact full-line editable marker pairs under `Summary`, `What Changed`, and `Why It Matters`; field ids are mirrored in packet JSON. Validation compares a protected-body fingerprint with editable blocks elided and fails when protected sections change.
- Host PR template content may coexist only outside the protected canonical packet block; it cannot replace or satisfy required packet-owned sections.
- Update `generate-pr-body.sh` so the generated body owns canonical reviewer sections directly: `Summary`, `What Changed`, `Why It Matters`, `How To Review`, `How To UAT`, `Verification`, `Scope`, and `Known Gaps`.
- Preserve a literal `## UAT Runbook` heading in the rendered body for SPEC-006a/b compatibility.
- Update the single-PR post-implementation path to generate the packet, validate it, and create the PR with `--title` and `--body-file`.
- Update `multi-pr-emission.sh` to write packet-owned titles for each slice, validate each packet, and block before the slice `gh pr create` when validation fails.
- Validation failure writes deterministic JSON under `specs/prsg-012-reviewer-ready-pr-packet-contract/.process/` during this spec and under the target feature `.process` directory at runtime.
- Post-create auto-repair is out of scope; record it as a future roadmap follow-up if it still matters after packet metadata stabilizes.

## Constraints
- Keep scripts deterministic and fixture-friendly.
- Do not introduce dependencies beyond Bash, `jq`, `git`, and `gh`.
- Do not break existing L3 expectations that PR bodies contain the legacy `speckit-pro-review-packet-source` compatibility marker and UAT Runbook heading.
- Preserve generated governance sections, rendered source/provenance markers, and compatibility markers during safe prose refinement.
- Validate rendered title descriptions strictly enough to reject any post-colon branch refs, slice IDs, PRSG/SPEC/FR/SC/L# tokens, stale placeholders, unexpanded variables, or banned labels.
- Allow only structural editable-boundary comments and the legacy compatibility marker; reject unknown HTML comments and stale template comments outside code fences.

## Reviewability Budget
- Primary surface: docs/process plus Bash automation
- Projected reviewable LOC: about 350, with advisory estimator at 245
- Projected production files: likely 4-6
- Projected total files: about 15-21 after input-error and resume fixtures
- Budget result: within budget
- Split decision: one spec, one slice
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Defines shared validator architecture, rendered packet schema, and one-slice reviewability plan |
| `contracts/` | Complete | Added `contracts/pr-packet.schema.json` for rendered packet metadata |
| `quickstart.md` | Complete | Includes local packet validation examples and verification commands |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Use enriched prompts; do not run bare domains.

### Recommended Domains

#### 1. API Contracts Checklist

Why this domain: PRSG-012 defines a CLI/script contract plus JSON packet schemas consumed by multiple scripts.

```bash
/speckit-checklist api-contracts

Focus on PRSG-012 requirements:
- Required PR packet fields for title, body file, headings, scope, verification, UAT, source markers, and editable prose fields.
- Compatibility between single-PR packets and split-PR slice packets.
- Exact `gh pr create --base --head --title --body-file` call contract.
- Pay special attention to: schema fields that are validated in JSON but not checked in rendered Markdown.
```

#### 2. Error Handling Checklist

Why this domain: The validator is a pre-create blocker, so failures must be exact, recoverable, and non-destructive.

```bash
/speckit-checklist error-handling

Focus on PRSG-012 requirements:
- Missing, malformed, stale, or placeholder-filled packet behavior.
- Validator exit codes and deterministic stderr.
- Workflow evidence written before stopping.
- Resume behavior after fixing an invalid packet.
- Pay special attention to: blocking before `gh pr create` without losing earlier successful split PRs.
```

#### 3. Reliability Checklist

Why this domain: Runtime evidence and generated packet metadata must remain durable across autopilot resume and split-PR emission.

```bash
/speckit-checklist reliability

Focus on PRSG-012 requirements:
- Deterministic validation JSON paths under `.process`.
- Workflow event content and remediation quality.
- Reuse of the shared validator across both PR creation paths.
- Layer 4, Layer 3, Layer 7, and Layer 8 evidence expectations.
- Pay special attention to: avoiding drift between Claude Code and Codex autopilot guidance.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contracts | 16 | 6 remediated; 0 remaining | Added required PR target, constrained body paths, required changed-file scope, split-only conditionals, rendered heading order validation, and exact editable field constraints |
| error-handling | 16 | 5 remediated; 0 remaining | Added input-error handling, malformed packet distinctions, deterministic stderr, stale-result-safe resume, and split-PR partial-success preservation |
| reliability | 18 | 3 remediated; 0 remaining | Added durable workflow-event sink/idempotency/remediation fields, exact L4/L3/L7/L8 evidence expectations, and Claude/Codex parity plus single-copy validator/schema boundaries |

---

## Phase 5: Tasks

**When to run:** After checklist gaps are resolved. Output: `specs/prsg-012-reviewer-ready-pr-packet-contract/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story, not by technical layer.
- Start with failing Layer 4 fixtures for packet validation and title/body generation.
- Keep each task independently verifiable.
- Mark parallel-safe tasks with [P] only when they do not touch the same script or fixture.

## Implementation Phases
1. Foundation: packet schema/fixture shape and validator skeleton.
2. User Story 1: generated packet-owned titles and `gh pr create --base --head --title --body-file`.
3. User Story 2: canonical body sections and UAT compatibility.
4. User Story 3: pre-create validator invocation, blocking behavior, and evidence.
5. User Story 4: safe editable fields and validator protections.
6. Polish: L3 functional eval updates, L7 replay, L8 Codex parity, and docs references.

## Required Test Evidence
- Layer 4 validator/body fixtures.
- Layer 4 multi-pr-emission command assertions include `--base`, `--head`, `--title`, and `--body-file`.
- L3 functional eval covers generated title/body and pre-create validation.
- L7 replay covers split PR packet validation before each slice PR.
- L8 Codex parity covers mirrored autopilot guidance.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 56 |
| Phases | Foundation, US1, US2, US3, US4, Polish |
| Parallel Opportunities | 5 |
| User Stories Covered | US1-US4 plus required evidence |

---

## Atomicity Route

Fill after the Tasks phase by running:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/prsg-012-reviewer-ready-pr-packet-contract
```

Expected initial route: `one-navigable-PR`, unless Tasks introduces separable vertical slices.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true` unless the classifier finds release-sensitive behavior |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Warnings | none | Release-safety warnings |

## Layer Plan

| Field | Value |
|-------|-------|
| Status | skipped |
| Reason | Atomicity route is `one-navigable-PR`; PRSG-008 layer planning runs only for `split-PR` routes |

## Reviewability Marker Plan

| Field | Value |
|-------|-------|
| Status | marker input recorded |
| Gate | `reviewability-gate.sh tasks` |
| Gate Status | `block` |
| Exit Code | 1 |
| Reviewable LOC | 2240 |
| Production Files | 1 |
| Total Files | 73 |
| Primary Surface Count | 5 |
| Warnings | reviewable LOC 2240 exceeds warn threshold 400; total files 73 exceeds warn threshold 15; primary surfaces 5 exceeds warn threshold 1 |
| Blockers | reviewable LOC 2240 exceeds block threshold 800; total files 73 exceeds block threshold 25 |

Planned marker order:

1. `M1` Foundation: T001-T009
2. `M2` US1 generated titles: T010-T017
3. `M3` US2 reviewer body: T018-T024
4. `M4` US3 validation gate: T025-T034
5. `M5` US4 safe refinement: T035-T041
6. `M6` Polish evidence and parity: T042-T056

Marker split, packet validation, and PR mappings remain pending until post-implementation PR preparation.

---

## Phase 6: Analyze

**When to run:** After tasks generation and before implementation.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Cross-artifact consistency between `spec.md`, `plan.md`, `tasks.md`, and `docs/ai/specs/.process/PRSG-012-design-concept.md`.
2. The design concept decisions: shared validator script, packet-owned title, canonical sections, UAT compatibility, editable fields only, JSON plus workflow evidence, and post-create repair as follow-up only.
3. Coverage gaps across both single-PR and split-PR paths.
4. Whether any task weakens existing SPEC-006a/b UAT guarantees.
5. Whether Codex parity and L8 evidence are explicitly covered.
6. Whether any generated body section still allows stale placeholders, hidden template comments, or banned labels.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | HIGH | Several artifacts narrowed PR creation coverage to `--title`/`--body-file`, while `spec.md` FR-004A and `plan.md` require packet target binding through `gh pr create --base --head --title --body-file` for every PR creation path. | Amended T006, T012, T016, T017, T032, T034, T042, T043, T048, and T049 so tests, split emission, single guidance, L3, and L8 all preserve explicit packet target/title/body arguments; aligned the remaining checklist, quickstart, plan, and workflow references with the full command contract. |
| A2 | HIGH | `tasks.md` did not explicitly cover every FR-015A input-error variant or the no-feature-dir `stdout`/`no-path` fallback. | Amended T003, T025, T027, T029, and T030 to cover directory-valued, schema-invalid, missing/unreadable, invalid-JSON, no-feature-dir inputs, deterministic `input_error` JSON/stderr, `no-path`, and zero `gh pr create` attempts. |
| A3 | MEDIUM | Body validation tasks were too implicit for FR-007, FR-008A, FR-016B, and the PR review packet traceability requirement: stale placeholders, unexpanded variables, example text, hidden/template comments, non-canonical heading sources, out-of-order headings, and traceability mappings needed explicit test/validator coverage. | Amended T003, T018, T019, T020, T023, T024, T037, and T040 to require those fixtures and validator checks directly. |
| A4 | MEDIUM | Resume and workflow-event tasks mentioned evidence emission but not deterministic event-id superseding or the rule that stale failed validation results cannot authorize PR creation after a corrected rerun. | Amended T027, T028, T031, T033, and T034 to require event-id superseding, current-packet revalidation, stale-result rejection, existing-PR reconciliation, and use of newly passed validation results only. |
| A5 | LOW | Phase 6 workflow metadata still showed Analyze in progress with an empty Analysis Results table after remediation. | Updated this workflow log to mark Analyze complete, record all findings/resolutions, and align required test evidence with the full packet target/title/body PR creation contract. |

**G6:** pass - 0 CRITICAL findings; 5 findings remediated; deterministic marker counter reports 0 remaining finding markers.

---

## Pre-Implementation Confidence Gate

| Field | Value |
|-------|-------|
| Mode | advisory |
| Status | soft-skip |
| Reason | No synthesizer confidence emit found |
| Threshold | 0.90 |
| Action | Continue to Phase 7 |

---

## Phase 7: Implement

**When to run:** After Analyze has no CRITICAL issues.

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD First

For every deterministic behavior:
1. RED: Add or update Layer 4 fixture assertions first.
2. GREEN: Implement the smallest Bash or Markdown change that passes.
3. REFACTOR: Simplify only inside touched surfaces.
4. VERIFY: Run the smallest relevant test, then the full default suite before PR.

## Pre-Implementation Setup
1. Confirm branch: `git status --short --branch` should show `prsg-012-reviewer-ready-pr-packet-contract`.
2. Confirm feature dir: `specs/prsg-012-reviewer-ready-pr-packet-contract`.
3. Run baseline checks as needed:
   - `bash tests/speckit-pro/run-all.sh --layer 4`
   - `bash tests/speckit-pro/run-all.sh --layer 1`

## Implementation Notes
- Prefer one shared validator script over duplicated validation logic.
- Keep `generate-pr-body.sh` responsible for rendering; keep validation in the validator.
- `multi-pr-emission.sh` must stop before each slice `gh pr create` when the packet is invalid.
- Missing, unreadable, invalid-JSON, and schema-invalid packet inputs must exit `2` as deterministic `input_error` diagnostics and make zero PR creation attempts.
- Rendered-content validation failures must exit `1`, write packet validation JSON plus workflow evidence before stopping, and emit one deterministic stderr line.
- Split-PR resume must preserve earlier opened PR evidence and continue from the failed packet after revalidation, without duplicate `gh pr create` attempts for already-opened slices.
- Single-PR post-implementation guidance must show `--title` and `--body-file`.
- Keep generated governance sections and source markers outside editable prose fields.
- Preserve `## UAT Runbook` compatibility while adding `How To UAT`.
- Do not implement broad post-create auto-repair in PRSG-012.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T009 | 9/9 | Added packet fixtures, validator contract tests, runtime schema, executable validator, and reviewability checkpoint |
| User Story 1 | T010-T017 | 8/8 | Generated and validated packet-owned single/split PR titles |
| User Story 2 | T018-T024 | 7/7 | Reviewer body evidence, UAT compatibility, traceability, source/scope/verification checks, and stale body text validation complete |
| User Story 3 | T025-T034 | 10/10 | Packet validation result paths, no-path input errors, workflow events, and split PR pre-create validation gate complete |
| User Story 4 | T035-T041 | 0/7 | In progress |
| Polish | | | |

---

## Post-Implementation Checklist

- [ ] `bash tests/speckit-pro/run-all.sh --layer 4` passes.
- [ ] `bash tests/speckit-pro/run-all.sh --layer 1` passes if mirrored docs or contracts changed.
- [ ] L3 functional eval evidence is recorded.
- [ ] L7 replay evidence is recorded when split-PR dispatch behavior changes.
- [ ] L8 Codex parity evidence is recorded.
- [ ] Generated PR body contains required canonical sections and the `## UAT Runbook` compatibility heading.
- [ ] Every PR creation path uses `gh pr create --base --head --title --body-file`.
- [ ] Invalid packet fixture blocks before PR creation and writes JSON remediation evidence.
- [ ] PR title is conventional and public-readable.

---

## Project Structure Reference

```text
speckit-pro/
  skills/speckit-autopilot/
    scripts/generate-pr-body.sh
    scripts/multi-pr-emission.sh
    scripts/validate-pr-packet.sh
    contracts/
    references/post-implementation.md
    references/phase-execution.md
    templates/pr-description-template.md
tests/speckit-pro/
  layer4-scripts/
  layer3-functional/
  layer7-integration/
  layer8-parity/
specs/prsg-012-reviewer-ready-pr-packet-contract/
  SPEC-MOC.md
  spec.md
  plan.md
  tasks.md
  .process/
```

---

Template based on SpecKit best practices. Populated for PRSG-012 from the PR-size governance roadmap and the PRSG-012 design concept doc.

## Consensus Resolution Log

| Phase | Item | Round | Routed Categories | Outcome | Analysts Used |
|-------|------|-------|-------------------|---------|---------------|
| Clarify Session 1 | HTML source marker semantics | 1 | codebase, spec | Accepted: keep `speckit-pro-review-packet-source` as a compatibility-only HTML comment marker; require rendered source/provenance markers outside comments, code fences, generated fixtures, `.process`, generated zones, and other non-provenance text for PRSG-012 protected marker validation. | codebase-analyst, spec-context-analyst |
| Clarify Session 1 | Safe editable fields | 1 | codebase, spec | Accepted: only explicit editable blocks under `Summary`, `What Changed`, and `Why It Matters` are sanctioned prose fields; protect `How To Review`, `How To UAT`, `Verification`, `Scope`, `Known Gaps`, traceability, source markers, UAT content, and generated governance/evidence content. | codebase-analyst, spec-context-analyst |
| Clarify Session 2 | Conventional title prefix | 1 | codebase, spec | Accepted: generated titles render as `<type>(<scope>): <plain-English description>`; implementation packets default to `feat(speckit-pro):`; only explicit packet metadata can override type/scope, and overrides must use allowed conventional commit values. | codebase-analyst, spec-context-analyst |
| Clarify Session 2 | Internal-code rejection | 1 | codebase, spec | Accepted: the post-colon description must be public-readable plain English and must reject any branch refs, slice IDs, PRSG/SPEC/FR/SC/L# tokens, stale placeholders, unexpanded variables, or banned labels, even when mixed with otherwise readable words. | codebase-analyst, spec-context-analyst |
| Clarify Session 3 | Safe refinement details | skipped | none | Executor returned no unresolved consensus items. Accepted exact full-line editable marker pairs, protected-body fingerprint comparison, allowlisted structural comments, canonical packet block before host template content, and fail-before-create validation JSON for outside-field edits. | clarify-executor |

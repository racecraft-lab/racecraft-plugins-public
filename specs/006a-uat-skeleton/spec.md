# Feature Specification: Deterministic UAT Runbook Skeleton + PR Body Integration

**Feature Branch**: `006a-uat-skeleton`

**Created**: 2026-05-28

**Status**: Draft

**Input**: User description: "Add the deterministic infrastructure half of a user-acceptance-testing (UAT) artifact for the speckit-pro autopilot: a heading-driven UAT runbook skeleton generated from spec.md, committed to the spec directory, and embedded in (or linked from) the PR body. LLM-authored narrative test steps are deferred to SPEC-006b — this spec ships the script, template, and PR-body wiring only."

## User Scenarios & Testing *(mandatory)*

The autopilot finishes every run by creating a PR with build / typecheck / lint / test checkboxes plus a Self-Review block. Neither produces a human-followable, story-by-story acceptance-testing artifact a reviewer (or product owner) can walk to confirm the PR actually delivers the behavior the spec promised. This feature adds that artifact's deterministic skeleton.

**Primary users**

- **PR reviewers** (human teammates) who need a story-by-story checklist with concrete preconditions and expected observable behavior.
- **The autopilot post-implementation phase**, which invokes the skeleton script after Self-Review and before PR creation.
- **External reviewers** without write access — for them the runbook lives in the PR body inline (under 50,000 chars) or as a link to the committed file.

### User Story 1 - Reviewer sees a UAT Runbook in the PR body (Priority: P1)

As a PR reviewer, I open the PR description and see a `## UAT Runbook` section that lists every user story from the spec with checkbox steps, so I can walk a story without leaving the PR view.

**Why this priority**: This is the core reviewer-facing value — the whole feature exists so a reviewer never has to reconstruct "what behavior should I check" by hand. Without it, nothing else in the spec delivers visible benefit.

**Independent Test**: Run the skeleton script against a spec that has user stories, generate a PR body, and confirm the body contains a `## UAT Runbook` heading with one acceptance-test block per user story. Delivers value even if every other story is unbuilt.

**Acceptance Scenarios**:

1. **Given** a `spec.md` containing N `### User Story` headings, **When** the skeleton script runs and the PR body is generated, **Then** the PR body contains a `## UAT Runbook` section listing all N stories with checkbox steps.
2. **Given** a generated runbook under 50,000 characters, **When** the PR body is assembled, **Then** the full runbook content is embedded inline in the PR body.
3. **Given** a generated runbook at or over 50,000 characters, **When** the PR body is assembled, **Then** the PR body shows an opening excerpt of the runbook followed by a relative link to the committed `uat-runbook.md`.

---

### User Story 2 - Reviewer of an infrastructure spec sees an FR/SC-keyed runbook (Priority: P1)

As a reviewer of an infrastructure spec with no user stories (e.g., SPEC-001 through SPEC-005), I see a runbook keyed by FR-NNN and SC-NNN with a header note explaining the fallback, so generation never silently skips.

**Why this priority**: Infrastructure specs are common in this repo and have zero user stories. If the script skipped them, the reviewer-facing artifact would be absent exactly where it is still useful. Equal priority to US1 because the feature must serve both spec shapes from day one.

**Independent Test**: Run the script against a spec with zero `### User Story` headings and confirm the runbook contains a fallback header note plus at least one FR-keyed and one SC-keyed test section.

**Acceptance Scenarios**:

1. **Given** a `spec.md` with zero `### User Story` headings but populated Functional Requirements and Measurable Outcomes, **When** the script runs, **Then** the runbook contains a header note stating tests are keyed by FR/SC, and includes FR-keyed and SC-keyed test sections.
2. **Given** that same zero-stories spec, **When** the script runs, **Then** the script still exits successfully (generation is never skipped).

---

### User Story 3 - Autopilot resume regenerates the runbook deterministically (Priority: P2)

As an autopilot consumer running a multi-resume workflow, I see the runbook regenerate deterministically from the current spec state on each resume — no merge with prior reviewer hand-edits, no stale content from a prior spec version.

**Why this priority**: Resume idempotency prevents stale or conflicting runbooks, but it is a robustness property rather than first-run visible value, so it sits below the two P1 stories.

**Independent Test**: Run the script twice against the same spec and confirm the two output files are byte-identical; introduce a hand-edit to the runbook between runs and confirm the second run overwrites it without merging.

**Acceptance Scenarios**:

1. **Given** an existing `uat-runbook.md` from a prior run, **When** the script runs again against an unchanged spec, **Then** the output file is deterministically overwritten and its content is identical to the prior run.
2. **Given** an existing `uat-runbook.md` that a reviewer hand-edited, **When** the script runs again, **Then** the hand-edits are overwritten (no merge, no append, no skip-if-present).

---

### User Story 4 - Self-Review findings echoed for offline review (Priority: P2)

As a maintainer reading the runbook from a cloned working copy, I see the Self-Review findings echoed into the runbook (extracted from the workflow file at the `## Self-Review` heading) so the runbook is self-contained for offline review.

**Why this priority**: The echo improves the runbook for offline readers but is not required for the in-PR reviewer flow, so it is P2. The autopilot always supplies the workflow file in real runs; standalone runs degrade gracefully.

**Independent Test**: Run the script with the workflow-file input pointing at a file that has a `## Self-Review` heading and confirm the runbook's Self-Review Findings section contains the echoed block; run without that input and confirm a graceful stub line appears instead.

**Acceptance Scenarios**:

1. **Given** a workflow file containing a `## Self-Review` section is supplied, **When** the script runs, **Then** the runbook's Self-Review Findings section contains the extracted block.
2. **Given** no workflow file is supplied, or the supplied file lacks a `## Self-Review` heading, **When** the script runs, **Then** the Self-Review Findings section contains a graceful stub line and the script still succeeds.

### Edge Cases

- **Zero user stories**: spec has no `### User Story` headings — runbook falls back to FR/SC keying with an explanatory header note (US2, FR-003).
- **Duplicate FR/SC IDs**: an ID such as FR-005 appears twice (as in SPEC-004) — the runbook keeps the first-seen entry and the script writes a stderr warning naming the duplicate ID (FR-004).
- **Unresolved clarification markers in the source spec**: when a parsed US/FR/SC/Edge bullet carries a clarification marker (bare or colon-question form), the runbook reproduces that bullet with an unresolved-clarification annotation rather than dropping it silently. Propagation is scoped to the bullets the script parses, not to arbitrary prose elsewhere in `spec.md` (FR-005).
- **Unreadable or missing spec**: the script exits with a distinct error code and does not produce a partial runbook (FR-006).
- **PROJECT_COMMANDS not supplied**: when the autopilot does not pass build/test/lint commands, the Env Setup section emits explicit unknown-value placeholders rather than failing (FR-008).
- **Missing Self-Review source**: workflow file absent or heading missing — Self-Review Findings degrades to a stub line, no failure (FR-009).
- **No Rollback heading in spec or plan**: the Rollback section emits a synthesized fallback stanza (FR-012).
- **Runbook at or over the size threshold**: the PR body shows an opening excerpt plus a relative link instead of the full inline content (FR-013).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A new script `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` MUST parse `### User Story N - <Title> (Priority: PN)` headings, `- **FR-NNN**:` list bullets inside `### Functional Requirements`, `- **SC-NNN**:` list bullets inside `### Measurable Outcomes`, and bullets inside `### Edge Cases`. The positional contract is `argv[1]` = spec.md path and `argv[2]` = output runbook path; the feature directory is derived via `dirname argv[1]` and no additional positional arguments are accepted. (Clarify S1) Multi-line or nested bullets under an FR/SC are reproduced verbatim as indented continuation lines, not flattened or joined. (Clarify S2)
- **FR-002**: The script MUST reuse the `extract_heading_section()` awk function from `generate-pr-body.sh` — sourced or copied verbatim, not reimplemented. (The choice between sourcing and copying verbatim is a Plan-phase decision per the workflow's Architecture Notes; see Assumptions.)
- **FR-003**: When `spec.md` has zero `### User Story` headings, the script MUST emit a runbook keyed by FR-NNN and SC-NNN with a header note (for example, "This spec has no user stories; tests are keyed by FR/SC."). It MUST NOT skip generation.
- **FR-004**: When `spec.md` has duplicate FR/SC IDs (for example, FR-005 appearing twice as in SPEC-004), the script MUST emit the first-seen entry only and write a stderr warning naming the duplicate ID. The warning is a plain, unprefixed human-readable message naming the duplicated ID (matching `confidence-gate.sh`'s stderr style); no fixed machine-readable tag prefix is added. (Clarify S1)
- **FR-005**: When `spec.md` contains unresolved clarification markers (the `NEEDS CLARIFICATION` annotation, in either its bare or colon-question form), the script MUST propagate each marker into the runbook with an unresolved-clarification annotation alongside the bullet, rather than silently dropping it. (The exact detection pattern is a Plan/implementation decision.)
- **FR-006**: The script MUST emit exit code 0 on success, 2 on usage error (wrong argv), and 1 on an unreadable spec. On success the script writes only the output runbook file and emits nothing to stdout (matching `generate-pr-body.sh`); diagnostics and warnings go to stderr. (Clarify S1)
- **FR-007**: The script MUST overwrite any existing `uat-runbook.md` deterministically — no merge with reviewer hand-edits, no append, no skip-if-present.
- **FR-008**: The script MUST accept the autopilot's project commands via the environment variable `UAT_PROJECT_COMMANDS` (a JSON string carrying the same object `detect-commands.sh` produces). The Env Setup section is a pure formatter over that JSON, drawing from the established key set `detect-commands.sh` produces — `BUILD`, `TYPECHECK`, `LINT`, `LINT_FIX`, `UNIT_TEST`, `INTEGRATION_TEST`, `SINGLE_FILE_INTEGRATION` — and rendering the relevant commands as Env Setup rows (which of these keys surface in the runbook is a formatting detail left to Plan/implementation). When the variable is **unset**, the Env Setup section MUST emit `<unknown — autopilot did not pass PROJECT_COMMANDS>` placeholders rather than failing. When the variable is **set but malformed** (not parseable by `jq`), the script MUST degrade to those same placeholders rather than crash (fail-soft; it does not abort). A key that is **present with the literal value `N/A`** (detect-commands.sh's sentinel for an undetected command) renders as that command being unavailable for this project, distinct from the unset-variable placeholder. The script MUST NOT re-run `detect-commands.sh` itself.
- **FR-009**: The script MUST accept an optional `--workflow-file <path>` flag and, when provided, extract the `## Self-Review` block via the same `extract_heading_section()` helper and echo it into the runbook's Self-Review Findings section. When the flag is absent or the heading is missing, the section MUST emit a graceful stub line and the script MUST still succeed.
- **FR-010**: A new template `speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md` MUST define sections in this order: Header (spec ID, branch, PR placeholder, generation timestamp), Env Setup, Per-Story Acceptance Tests, FR Coverage Matrix, Negative-Path Tests, Self-Review Findings (echo), Sign-off (advisory), Rollback. Every section header is always emitted in this fixed order; when `### Edge Cases` is absent from `spec.md`, the Negative-Path Tests section retains its header and emits a stub line (`No edge cases identified in spec.md`) rather than being omitted. The FR Coverage Matrix rows link to their Per-Story section within the committed `uat-runbook.md` via deterministic, GitHub-renderable anchors; the exact anchor mechanism is a Plan decision (default: explicit script-emitted anchors, avoiding replication of GitHub's heading-slug algorithm). Sign-off checkboxes are advisory only and block nothing. (Clarify S2)
- **FR-011**: The Header's PR field MUST be a static placeholder (for example, `**PR:** <set on PR open>`). The autopilot MUST NOT rewrite the runbook after PR creation.
- **FR-012**: The Rollback section MUST extract a `## Rollback` heading from `spec.md` (or `plan.md` as fallback) when present; otherwise it MUST emit a synthesized stanza such as `git revert <SHA>; see plan.md for data-migration considerations`.
- **FR-013**: `generate-pr-body.sh` MUST emit a dedicated `## UAT Runbook` (H2) section in the review-packet body that reads `<feature-dir>/uat-runbook.md`. This section MUST be a standalone, size-aware block — NOT routed through the existing review-packet heading loop / `append_missing_section()` / `extract_heading_section()`, which truncate and strip blank lines (the exact wiring is a Plan decision). When the runbook is under 50,000 characters, the section MUST embed the full runbook content; otherwise it MUST embed an opening excerpt — the first 60 lines of `<feature-dir>/uat-runbook.md` (`head -60`, blank lines preserved so the Header table and section headings render) — followed by a relative link to the committed `uat-runbook.md`. (Clarify S2 — resolves the prior excerpt ambiguity. Plan note: the under-threshold "full content" path MUST NOT reuse `extract_heading_section`, which strips blank lines and caps output at `head -40`; Plan selects a non-truncating mechanism such as `cat`.)
- **FR-014**: The Claude Code autopilot (`speckit-pro/skills/speckit-autopilot/`) and the Codex variant (`speckit-pro/codex-skills/speckit-autopilot/`) MUST be edited in lockstep — same content, runtime-appropriate primitives. No new agent files are introduced in this spec.
- **FR-015**: A new Layer 4 unit test `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh` MUST cover five fixtures: a vendored full-spec snapshot (committed at `speckit-pro/tests/layer4-scripts/fixtures/spec-full-snapshot.md`, not read live), a synthetic zero-stories spec, a synthetic duplicate-FR spec, a synthetic spec carrying an unresolved clarification marker, and a missing-spec error case.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (UAT runbook template + skeleton script + autopilot SKILL/reference edits).
- **Secondary surfaces, if any**: harness/adapter (one new Layer 4 unit test plus a vendored fixture); a surgical modification to `generate-pr-body.sh`.
- **Projected reviewable LOC**: ~670 (excludes the vendored `spec-full-snapshot.md` fixture text, which is data, not executable code).
- **Projected production files**: 4 (new template, new script, modified `generate-pr-body.sh`, new Layer 4 test).
- **Projected total files**: 11 (the 4 production files, the vendored fixture, plus the lockstep Codex-variant edits and autopilot reference updates — reconciled in Plan against the verified `-codex.md` doc twins, which added 2 over the initial estimate of 9; still well under the 25-file block threshold).
- **Budget result (production code)**: within budget — 389 reviewable LOC of production code (script 331 + template 51 + the surgical `generate-pr-body.sh` delta), under the 800 LOC / 8 production-file thresholds. The Layer 4 test adds ~580 LOC of constitution-mandated coverage (Principle IV); counting code + test gives ~966, of which the surface a reviewer scrutinizes for correctness is the 389 of production code.
- **Measured PR diff**: the full `git diff` against `main` is larger (~3800 LOC across ~33 files) because it includes the complete SDD process trail (spec, plan, tasks, three domain checklists, design concept, workflow file) and the 321-line vendored `spec-full-snapshot.md` fixture (data, not code). These are the planning record and test data, not line-by-line code-review surface.
- **Split decision & ratified split exception**: this spec executes under the **ratified split exception** recorded in `docs/ai/specs/reviewer-experience-technical-roadmap.md` — the SPEC-006a (deterministic infrastructure) / SPEC-006b (LLM author agents) split. SPEC-006a is the deterministic half; the narrative-prose author agents are deferred to SPEC-006b. The split has already happened; no further split is warranted.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence (FR-001..FR-015 → the script, template, modified `generate-pr-body.sh`, and Layer 4 test; SC-001..SC-005 → their verification commands).
- Deferred work MUST name the follow-up spec or issue (LLM-authored test prose and author agents → SPEC-006b).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A standalone run of `generate-uat-skeleton.sh` against `specs/004-integration-verification/spec.md` produces a runbook in which every user story is present (the story count matches `grep -cE '^### User Story [0-9]' spec.md` — the numbered-heading pattern of FR-001, which excludes non-story subsections such as a "User Story to Requirement Traceability" matrix).
- **SC-002**: A standalone run against a synthetic zero-stories spec produces a runbook with the FR/SC fallback header note and at least one FR-keyed and one SC-keyed test section.
- **SC-003**: `bash speckit-pro/tests/run-all.sh --layer 4` exits 0 with the new test included.
- **SC-004**: `bash speckit-pro/tests/run-all.sh --layer 1` exits 0 after the change (Codex parity preserved — no new agent files).
- **SC-005**: A PR generated by the autopilot after this feature ships contains a `## UAT Runbook` heading in its body and a committed `uat-runbook.md` under the spec directory.

## Constraints

- **Reviewability budget**: ~670 LOC, 4 production files (template, script, modified `generate-pr-body.sh`, Layer 4 test), 11 total files (reconciled in Plan against the verified `-codex.md` doc twins) — under the block thresholds.
- **Single primary surface**: docs/process (template + script + autopilot reference edits).
- **Bash + jq only**: no new dependencies; match the existing speckit-pro script conventions.
- **Strict-mode scripts**: every new bash script uses `#!/usr/bin/env bash` and `set -euo pipefail`, matching the existing scripts under `speckit-pro/skills/speckit-autopilot/scripts/`.
- **Layer 4 coverage for new scripts**: every new bash script requires a Layer 4 unit test (FR-015).
- **Conventional Commits** PR title with a plain-English, public-readable body (the racecraft-plugins-public PR convention).
- **No agent files added** — the Layer 1 Codex parity test (`validate-codex-parity.sh`) must stay green at every commit.
- **KISS / YAGNI**: no abstractions for one call site; no flags or options added for hypothetical future callers.

## Out of Scope

- LLM-authored narrative test-step prose (SPEC-006b).
- New Claude Code or Codex agent files (SPEC-006b).
- Layer 5 tool-scoping fixtures (no new agent yet).
- Layer 7 integration fixtures with author-agent simulation (SPEC-006b).
- A pass/fail blocking gate on UAT (rejected; advisory only — see design concept).
- A 3-way merge of the regenerated runbook with reviewer hand-edits (rejected; deterministic overwrite — see design concept Q4).
- The autopilot rewriting the runbook after PR creation to fill in the PR URL (rejected; static placeholder — see design concept Q1).
- A standalone `/speckit-pro:regenerate-uat` skill (YAGNI — revisit if a second use case emerges).

## Assumptions

- The autopilot invokes the skeleton script during its post-implementation phase, after Self-Review and before PR creation, supplying both the workflow-file path and the project commands in real runs.
- `jq` is already on PATH (it is an existing hard prerequisite for the autopilot).
- The `extract_heading_section()` awk helper already exists in `generate-pr-body.sh` and is the battle-tested heading-bounded extractor to reuse (the Plan phase pins its exact line range and decides source-vs-copy).
- The vendored full-spec fixture is a frozen snapshot of `specs/004-integration-verification/spec.md` as of merge; the Layer 4 test reads the snapshot, never the live spec (design concept Q4).
- `UAT_PROJECT_COMMANDS` carries the same JSON the autopilot already discovers via `detect-commands.sh` in its setup step (design concept Q2); the Env Setup section is a pure formatter over that JSON.
- The 50,000-character inline-vs-link threshold matches the existing PR-body size convention in `generate-pr-body.sh`.

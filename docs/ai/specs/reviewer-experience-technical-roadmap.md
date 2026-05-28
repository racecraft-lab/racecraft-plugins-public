# Reviewer Experience Implementation Roadmap

**Improve the human reviewer's ability to verify that autopilot-generated PRs actually deliver the behavior promised by the spec.** First initiative: a UAT (User Acceptance Testing) runbook generated at the end of every autopilot run, committed to the spec directory, and attached to the PR body for manual story-by-story verification.

This document defines the specification roadmap for the Reviewer Experience workstream. Each specification is executed end-to-end through the SpecKit workflow (specify → clarify → plan → checklist → tasks → analyze → implement) before moving to the next.

**Current Status:** Planning complete (2026-05-27) — all scope decisions locked in via interactive Q&A. SPEC-006a and SPEC-006b are ready for `/speckit-pro:speckit-scaffold-spec`. Approved plan at `~/.claude/plans/wobbly-fluttering-knuth.md`.

**Parent Branch:** `feat/reviewer-experience`
**Per-spec branches:** `006a-uat-skeleton`, `006b-uat-author-agent`

### Locked-in Scope Decisions (apply to both specs)

| Decision | Value |
|---|---|
| Runbook filename | `uat-runbook.md` (committed to `specs/<NNN>-<feature>/`) |
| Priority filter | All User Story priorities covered (P1, P2, P3+) — no filtering |
| Rollback content source | Extract from `spec.md` Rollback section if present, otherwise derive a "revert commit `<SHA>`" stanza from the diff |
| No-user-stories behavior | Emit a runbook keyed by FR-NNN and SC-NNN with a header note explaining the fallback; never skip generation |
| Resume idempotency | Regenerate the runbook on every autopilot run — overwrites the prior file deterministically; no merge with hand-edits |
| Sign-off semantics | Advisory only; no GitHub Actions check, no merge block (mirrors Self-Review pattern) |
| Self-Review block | Keep at 4 questions — UAT Runbook is a downstream consumer of Self-Review's findings, not an extension of Self-Review |

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Reviewability Contract](#reviewability-contract)
3. [Dependency Graph](#dependency-graph)
4. [Progress Tracking](#progress-tracking)
5. [Specification Sections](#specification-sections)
6. [Decomposition Principles](#decomposition-principles)
7. [Environment & Deployment Context](#environment--deployment-context)
8. [References](#references)

---

## Roadmap Overview

The first initiative is decomposed into **2 specifications** across **2 dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | SPEC-006a | Deterministic UAT skeleton extractor + template + PR body wiring (no new agent files) | Sequential |
| **2** | SPEC-006b | UAT author agents (Claude Code + Codex) + autopilot wiring + Layer 5/7 tests | Sequential (depends on 006a) |

**Execution Order:** SPEC-006a → SPEC-006b

**Dependency Constraints:**
- SPEC-006b requires SPEC-006a (the author agent edits the skeleton produced by 006a's script; the autopilot wiring for the script must exist before the agent is layered on top)
- The split is structured so SPEC-006a adds **zero new agent files** — this keeps `tests/layer1-structural/validate-codex-parity.sh` (which enforces every `agents/*.md` has a matching `codex-agents/*.toml`) green at every commit. SPEC-006b adds both the Claude Code agent and the Codex agent in the same PR, preserving parity.

---

## Reviewability Contract

Every spec in this roadmap must fit a human review budget before setup and again before PR creation.

- Warn above 400 reviewable LOC, 6 production files, 15 total files, or more than one primary surface.
- Block above 800 reviewable LOC, 8 production files, 25 total files, or more than one primary surface unless this roadmap records a ratified split exception.
- Primary surfaces: schema/migration, API, UI, scheduler/runtime, harness/adapter, seed/config, docs/process.
- PR descriptions are review packets — what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback/flag notes. After SPEC-006b ships, every autopilot-generated PR also includes a UAT Runbook section.

**Ratified split exception:** A naive single-spec implementation totaling ~1300 LOC across 17 files would exceed the block thresholds. The split into SPEC-006a (deterministic infrastructure) → SPEC-006b (author agents) keeps both PRs under budget AND preserves the Layer 1 parity invariant. No further exception required.

---

## Dependency Graph

```text
SPEC-006a (Deterministic UAT Skeleton + Template + PR Body Wiring)
    │
    └──► SPEC-006b (UAT Author Agents + Autopilot Wiring)
              │
              ─── REVIEWER EXPERIENCE v1 COMPLETE ───
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| SPEC-006a | Deterministic UAT Skeleton + PR Body Integration | 🔄 In Progress | `SPEC-006a-workflow.md` (scaffolded 2026-05-27 on `006a-uat-skeleton`) | Specify — autopilot-ready |
| SPEC-006b | UAT Author Agent + Autopilot Integration | ⏳ Pending | `SPEC-006b-workflow.md` (not yet scaffolded) | Blocked by SPEC-006a |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### SPEC-006a: Deterministic UAT Skeleton + PR Body Integration

**Priority:** P1 | **Depends On:** None | **Enables:** SPEC-006b

**Goal:** Produce a deterministic, heading-driven UAT skeleton from `spec.md` at the end of every autopilot run, commit it to the spec directory, and embed it (or link to it) in the PR body. No new agent files — keeps Layer 1 parity test green.

**Reviewability Budget:** Primary surface: docs/process (template + script + autopilot SKILL.md edits) |
Projected reviewable LOC: ~670 |
Production files: 4 (template, skeleton script, modified `generate-pr-body.sh`, Layer 4 test) |
Total files: 9 (production + 5 doc/SKILL.md/references edits) |
Budget result: within budget

**Scope:**
- New template `speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md` with sections: Header (spec ID, branch, PR placeholder, generation timestamp), Env Setup (clone + checkout + `PROJECT_COMMANDS`), Per-Story Acceptance Tests (one section per User Story regardless of priority — P1, P2, P3+ all included — each with checkbox steps, preconditions, expected observable behavior), FR Coverage Matrix (table mapping FR-NNN → story section anchor), Negative-Path Tests (from `### Edge Cases`), Self-Review Findings echo, Sign-off (advisory only), Rollback (sourced from `spec.md` Rollback section if present, otherwise auto-derived stanza referencing `git revert <SHA>` with the implementation commit hash)
- New script `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` — heading-driven extractor that parses User Story headings (`### User Story N - <Title> (Priority: PN)` — all priorities included, no filter), FR list bullets (`- **FR-NNN**:`) inside `### Functional Requirements`, SC list bullets (`- **SC-NNN**:`) inside `### Measurable Outcomes`, and Edge Case bullets. Reuses the `extract_heading_section()` awk function from `generate-pr-body.sh` lines 45-65. Rollback section: first attempts to extract a Rollback heading from `spec.md` (or `plan.md` as fallback); if absent, emits a synthesized stanza `git revert <SHA>; see specs/<NNN>/plan.md for data-migration considerations`. Handles: zero user stories (infra spec → emit FR/SC-keyed skeleton with header note explaining the fallback), duplicate FR/SC IDs (dedupe first-seen + stderr warning), `[NEEDS CLARIFICATION]` markers (propagate with annotation), multi-line bullet continuation (awk fold). Output is overwrite-on-write (no merge); on autopilot resume the runbook regenerates deterministically from the current spec state. Exit codes: 0 success, 2 usage error, 1 unreadable spec
- Modify `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` to add `"UAT Runbook"` to the heading list at line 171 and a corresponding section to the `review_packet` heredoc that reads from `<feature-dir>/uat-runbook.md`. Size logic: under 50_000 chars embed full content, otherwise embed first ~60 lines + relative link to the committed file
- Add `"Post: UAT Runbook Generation"` to the canonical post-implementation task list (`task-list-canonical.md` 12 → 13 entries) and a new `## 3.1b UAT Runbook Generation` section in `references/post-implementation.md`, placed between Self-Review and PR Body Generation. In 006a this step runs ONLY the deterministic script — the resulting skeleton IS the PR-attached artifact. Mirror the same edits in the Codex variant (`codex-skills/speckit-autopilot/`)
- New Layer 4 unit test `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh` sourcing `tests/lib/assertions.sh`, fixtures created in `mktemp -d` with cleanup trap (mirrors `test-ensure-reviewability-preset.sh` pattern). Fixtures cover: full spec (snapshot of `specs/004-integration-verification/spec.md`), zero-stories spec (synthetic), duplicate-FR spec (synthetic), `[NEEDS CLARIFICATION]` spec (synthetic), and missing-spec error

**Out of Scope:**
- LLM-authored narrative test step prose (deferred to SPEC-006b — the agent edits the deterministic skeleton in place)
- Author agent files for Claude Code or Codex (deferred to SPEC-006b)
- Layer 5 tool scoping fixtures (no new agent yet)
- Layer 7 integration fixtures with author-agent simulation (deferred to SPEC-006b)

**Key Decisions:**

**[Skeleton-First Split] Decision (2026-05-27):** Ship deterministic infrastructure as the standalone first PR; layer the LLM author agent on top in a second PR. This keeps `validate-codex-parity.sh` green at every commit because 006a adds zero new agent files (the parity test enforces 1:1 pairing between `agents/*.md` and `codex-agents/*.toml`). Splitting differently — e.g., shipping the CC agent in 006a and the Codex TOML in 006b — would break the parity test for the duration between merges.
Alternatives considered: single-spec implementation with documented exception (overshoots reviewability block threshold without structural reason); split by Claude Code vs Codex (breaks parity test).

**[Heading-Driven Extraction] Decision (2026-05-27):** Parse `spec.md` via heading-bounded awk rather than inline `[US1]`/`[FR-001]` markers. Verified against real specs: SpecKit core templates emit `### User Story N - <Title>` headings and `- **FR-NNN**:` list bullets, not inline brackets.
Alternatives considered: inline bracket markers (do not exist in real specs); LLM extraction (non-deterministic, defeats the "script-first, agent-second" split).

**[Advisory Sign-off] Decision (2026-05-27):** UAT sign-off is advisory only — no GitHub Actions check, no merge block. Mirrors the existing Self-Review pattern ("the finding is the deliverable, not a gate"). The runbook is a tool for the reviewer; whether they tick the boxes is between them and the PR.
Alternatives considered: blocking gate on P1 stories (higher friction, fails for external reviewers without write access); hybrid `uat_gate_mode` setting (more code without proven need).

**[Regenerate-on-Resume Idempotency] Decision (2026-05-27):** When autopilot resumes a run that already produced a `uat-runbook.md`, the skeleton script overwrites the file deterministically — no 3-way merge with reviewer hand-edits, no append. Reviewers who want to preserve manual changes do so AFTER the PR is open (the autopilot has already finished). The deterministic skeleton is regenerated from the current spec state, so resume after a spec edit picks up the new content automatically.
Alternatives considered: 3-way merge against hand-edits (over-engineered for an artifact reviewers can edit post-PR); skip regeneration if file exists (creates stale runbook drift when spec changes mid-run).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/templates/uat-runbook-template.md` — New: section skeleton
- `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` — New: heading-driven extractor
- `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` — Modified: append `"UAT Runbook"` to heading loop + size-aware section
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — Modified: new §3.1b
- `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` — Modified: 12 → 13 canonical post-impl tasks
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: Step 3 reference update
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, `references/post-implementation.md`, `references/task-list-canonical.md` — Parallel Codex variant edits
- `speckit-pro/tests/layer4-scripts/test-generate-uat-skeleton.sh` — New: Layer 4 unit test

---

### SPEC-006b: UAT Author Agent + Autopilot Integration

**Priority:** P1 | **Depends On:** SPEC-006a | **Enables:** Reviewer Experience v1 complete

**Goal:** Replace SPEC-006a's skeleton-only output with LLM-authored narrative test steps — concrete preconditions, plain-English action steps, observable expected results. Adds the Claude Code agent and the Codex agent in the same PR so the Layer 1 parity test stays green.

**Reviewability Budget:** Primary surface: harness/adapter (subagent definitions + autopilot orchestration) |
Projected reviewable LOC: ~630 |
Production files: 4 (CC agent, Codex TOML, Layer 5 test, Layer 7 fixture directory) |
Total files: 8 (production + 4 SKILL.md / reference edits) |
Budget result: within budget

**Scope:**
- New Claude Code agent `speckit-pro/agents/uat-runbook-author.md` with frontmatter grounded in the [Anthropic sub-agents docs](https://code.claude.com/docs/en/sub-agents): `name: uat-runbook-author` (required), `description` (required, trigger-phrase format per skill-creator guide), `model: sonnet` (read-and-synthesize fit; matches gate-validator and post-impl teammate pattern), `effort: max` (plugin max-thinking policy), `tools: Read, Edit, Write, Bash, Grep, Glob` (comma-separated string per docs), `color: cyan`, `maxTurns: 30`. Does NOT declare `permissionMode`/`hooks`/`mcpServers` (silently ignored on plugin agents). Does NOT include `Agent`/`Skill` in tools (subagents cannot nest). Body: instructions to read skeleton + spec.md + plan.md + quickstart.md + Self-Review block + diff, then `Edit` the skeleton in place to fill prose test steps
- New Codex agent `speckit-pro/codex-agents/uat-runbook-author.toml` grounded in the [OpenAI Codex subagents docs](https://developers.openai.com/codex/subagents): required fields `name`, `description`, `developer_instructions`; `model = "gpt-5.5"` (with `gpt-5.4` fallback per installer convention), `model_reasoning_effort = "xhigh"`, `sandbox_mode = "workspace-write"`. `developer_instructions` mirrors the Claude Code agent body verbatim
- Update both autopilot SKILL.md variants to replace the 006a "script-only" Post-UAT step with the full sequence: run `generate-uat-skeleton.sh` → spawn `uat-runbook-author` subagent (CC: `Agent(subagent_type: "uat-runbook-author", ...)`; Codex: `spawn_agent("uat-runbook-author") + wait_agent`) → subagent edits skeleton in place → auto-commit `specs/<NNN>-<feature>/uat-runbook.md`. Fail-open policy mirroring Self-Review: script failure → log + stub runbook + PR-body note; agent failure → leave 006a-style skeleton + PR-body note. Never block PR creation
- Update `references/post-implementation.md` in both variants with the full agent prompt template — inputs (skeleton path, spec.md, plan.md, quickstart.md, Self-Review block, `PROJECT_COMMANDS`, diff range, feature dir), output contract (Edit-in-place, do not emit fresh), fail-open behavior
- New Layer 5 tool scoping test `speckit-pro/tests/layer5-tool-scoping/test-uat-runbook-author.sh` asserting `uat-runbook-author.md` declares only `Read, Edit, Write, Bash, Grep, Glob` and asserting ABSENCE of `Agent`, `Skill`, `Task*`, `TeamCreate`, `spawn_agent`
- New Layer 7 integration replay fixture `speckit-pro/tests/layer7-integration/<class>/uat-runbook-happy-path/` asserting `specs/<NNN>/uat-runbook.md` is committed before PR creation, PR body contains `## UAT Runbook`, fail-open path produces stub on simulated agent error
- Layer 1 parity (`validate-codex-parity.sh`) auto-passes once both agent files exist

**Out of Scope:**
- Standalone `/speckit-pro:regenerate-uat` skill (deferred — YAGNI; revisit if a second use case emerges)
- Automated UAT result extraction from PR review state (potential v2 work)
- Pass/fail blocking gate (rejected in 006a; advisory only)

**Key Decisions:**

**[Sonnet for Author Agent] Decision (2026-05-27):** Author agent runs on Sonnet at max effort, not Opus. The task is read-and-synthesize (consume spec + skeleton + diff, write prose steps) — model fit, not raw reasoning depth, is the bottleneck. Matches the existing gate-validator and post-impl teammate pattern in the autopilot. Plugin policy is max thinking on every agent regardless of model, so cost is reduced only where quality is proven equivalent.
Alternatives considered: Opus (overkill for synthesis-only task; cost premium without quality lift); Haiku (read-and-write task can produce shallow steps without enough reasoning headroom).

**[Edit-in-Place Output Contract] Decision (2026-05-27):** Author agent edits the deterministic skeleton in place using `Edit`/`Write`, not "emit fresh runbook." Reasons: skeleton has stable section IDs and US/FR/SC anchors for diff-friendly re-runs on autopilot resume; agent's value is concrete prose steps and command lines, not skeleton structure; idempotent on resume.
Alternatives considered: emit fresh runbook (loses anchor stability, breaks resume idempotency); 3-way merge of agent output with hand-edits (over-engineered; users who want manual changes can edit after the PR is open).

**Key Files:**
- `speckit-pro/agents/uat-runbook-author.md` — New: Claude Code agent
- `speckit-pro/codex-agents/uat-runbook-author.toml` — New: Codex agent
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: replace 006a script-only step with full skeleton+agent sequence
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — Modified: agent prompt template
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, `references/post-implementation.md` — Parallel Codex variant edits
- `speckit-pro/tests/layer5-tool-scoping/test-uat-runbook-author.sh` — New: tool scoping assertion
- `speckit-pro/tests/layer7-integration/<class>/uat-runbook-happy-path/` — New: replay-mode fixture

---

## Decomposition Principles

When breaking a feature into specs in this roadmap:

1. **Each spec is independently executable** through the full SpecKit workflow (specify → implement) — SPEC-006a ships a working (if minimal) UAT runbook on its own
2. **Preserve the Layer 1 parity invariant at every commit** — never ship a `agents/*.md` without its matching `codex-agents/*.toml` (or vice versa) in the same PR
3. **Deterministic infrastructure first, LLM-authored prose second** — script-and-template patterns are testable with Layer 4 unit tests in isolation; agents are layered on top once the deterministic foundation is in place
4. **Mirror Claude Code and Codex edits in lockstep** — every SKILL.md or references change has a parallel edit in the corresponding `codex-skills/` file; the shared scripts and templates remain single-source

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| SpecKit CLI | `specify` v0.8.x already installed via `uv tool install` |
| Test runner | `speckit-pro/tests/run-all.sh` already covers Layers 1, 4, 5 by default; `--integration` flag for Layer 7 |
| Reviewability gate | `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` — already enforces the 800 LOC / 8 prod / 25 total thresholds documented in §Reviewability Contract |
| Heading-extraction utility | `extract_heading_section()` awk function in `generate-pr-body.sh` lines 45-65 — reused by the new skeleton extractor |
| Test assertions library | `speckit-pro/tests/lib/assertions.sh` — `assert_eq`, `assert_contains`, `assert_file_exists`, `assert_exit_code`, `test_summary` |
| Parity test | `speckit-pro/tests/layer1-structural/validate-codex-parity.sh` — auto-enforces 1:1 CC↔Codex agent pairing once new agents land in SPEC-006b |
| Plugin autopilot Step 3 | Post-implementation 12-task canonical sequence in `references/task-list-canonical.md` — extended to 13 in SPEC-006a |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| New canonical post-impl task | `references/task-list-canonical.md` (CC + Codex) | `"Post: UAT Runbook Generation"` between Self-Review and PR Body Generation |
| PR body section | `generate-pr-body.sh` line 171 heading list | Append `"UAT Runbook"` |
| Two new plugin agents | `agents/` + `codex-agents/` (SPEC-006b only) | `uat-runbook-author.md` + `uat-runbook-author.toml` |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| Bash + jq | Already required by every existing speckit-pro script |
| GitHub CLI (gh) v2+ | Already required for PR creation in post-implementation |
| Claude Code | Required to test the CC agent locally (`/speckit-pro:speckit-autopilot`) |
| Codex CLI | Required to test the Codex agent locally (parallel installation; not blocking for CC-only verification) |

---

## References

- **Approved plan:** `~/.claude/plans/wobbly-fluttering-knuth.md` — full implementation plan with verification commands, test layer matrix, and open grill-me questions
- **SpecKit Workflow Template:** referenced via `/speckit-pro:speckit-scaffold-spec`
- **Constitution:** `.specify/memory/constitution.md`
- **Project Standards:** `CLAUDE.md`, `AGENTS.md`
- **Anthropic Sub-agents documentation:** https://code.claude.com/docs/en/sub-agents — frontmatter schema, plugin-agent ignored fields (`hooks`/`mcpServers`/`permissionMode`), no-nesting invariant, tools comma-separated syntax, model + effort enums
- **OpenAI Codex Subagents documentation:** https://developers.openai.com/codex/subagents — TOML schema (`name`/`description`/`developer_instructions` required), `agents.max_depth` default 1, install paths (`.codex/agents/` / `~/.codex/agents/`)
- **Related existing roadmap:** `docs/ai/specs/cicd-release-pipeline-technical-roadmap.md` — feature-complete; reviewer experience is a separate workstream

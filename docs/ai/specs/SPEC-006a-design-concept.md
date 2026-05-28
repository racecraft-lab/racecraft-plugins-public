---
topic: "Deterministic UAT runbook skeleton + PR body integration"
slug: "spec-006a-uat-skeleton"
date: "2026-05-27"
mode: "setup"
spec_id: "SPEC-006a"
source_input:
  type: "file"
  ref: "docs/ai/specs/reviewer-experience-technical-roadmap.md (SPEC-006a section)"
question_count: 4
stop_reason: "natural"
---

# Design Concept: Deterministic UAT runbook skeleton + PR body integration

> **Source:** `docs/ai/specs/reviewer-experience-technical-roadmap.md` (SPEC-006a section) + approved plan at `~/.claude/plans/wobbly-fluttering-knuth.md`
> **Date:** 2026-05-27
> **Questions asked:** 4
> **Stop reason:** natural — locked-in scope from roadmap + 4 implementation-detail decisions resolved

This design concept extends the locked-in scope in the Reviewer Experience roadmap with implementation-detail decisions that the roadmap left ambiguous. The roadmap's "Locked-in Scope Decisions" table (7 rows) and per-spec "Key Decisions" (4 entries) are the foundation; this doc captures the additional decisions made during scaffolding.

## Goals

- Produce a **deterministic, heading-driven UAT skeleton** from `spec.md` at the end of every autopilot run, committed to `specs/<NNN>-<feature>/uat-runbook.md` and embedded in the PR body.
- Cover **every User Story priority** (P1, P2, P3+) — no priority filtering.
- Add **zero new agent files** in this spec so the Layer 1 Codex parity test (`validate-codex-parity.sh`) stays green at every commit.
- Keep the change **within the reviewability budget**: ~670 LOC, 4 production files, 9 total files (under the 800 LOC / 8 prod / 25 total block thresholds).
- Make the skeleton **idempotent across autopilot resumes** — regeneration overwrites the prior file deterministically; no merge with reviewer hand-edits.
- Make sign-off **advisory only** — no GitHub Actions check, no merge block (mirrors the Self-Review pattern).

## Non-goals

- LLM-authored narrative test step prose — deferred to SPEC-006b (the agent edits this skeleton in place).
- Author agent files for Claude Code or Codex — deferred to SPEC-006b (preserves Layer 1 parity).
- Layer 5 tool scoping fixtures — no new agent yet.
- Layer 7 integration fixtures with author-agent simulation — deferred to SPEC-006b.
- Pass/fail blocking gate on UAT — explicitly rejected; advisory only.
- 3-way merge of regenerated skeleton with reviewer hand-edits — explicitly rejected; reviewers edit after the PR is open.
- **Autopilot rewriting the runbook after PR creation to substitute the PR URL** — answered in Q1 (static placeholder only).
- **Layer 4 test reading the live `specs/004-integration-verification/spec.md` at run time** — answered in Q4 (vendor a frozen snapshot).
- **Standalone `/speckit-pro:regenerate-uat` skill** — YAGNI; revisit if a second use case emerges.

## Design Tree (Q&A log)

### Q1. The UAT runbook header includes a PR URL field, but the runbook is generated and committed BEFORE the PR is opened. How should the PR URL get populated?

**Branch:** PR body integration / orchestration order

**Recommended answer:** Static placeholder, no rewrite
> The runbook commit lands before `gh pr create`, so the PR URL is unknown at script-run time. A static placeholder (`**PR:** <set on PR open>` or `${PR_URL}` as a string literal) keeps the autopilot's post-impl orchestration single-pass and avoids a second commit (or amend) just to substitute a URL the reviewer can already see in the PR description. The PR body itself shows the canonical link — scrolling up from `## UAT Runbook` lands on the URL.

**Alternatives offered:**
- Autopilot rewrites runbook after PR creation: more accurate but adds an Edit step + commit, plus a failure mode if `gh pr create` succeeds but the rewrite fails (runbook would still ship without URL — same outcome as the placeholder).
- Omit the PR URL field entirely: simpler still, but the field has documentation value for runbook readers who clone the working copy.

**User's answer:** Static placeholder, no rewrite (Recommended)

---

### Q2. The Env Setup section needs concrete commands (build/test/lint), and the autopilot already discovers PROJECT_COMMANDS in Step 0.11 via `detect-commands.sh`. How should the skeleton script receive them?

**Branch:** script contract / detection vs injection

**Recommended answer:** Autopilot passes JSON via env var or argv
> The autopilot already runs `detect-commands.sh` in Step 0.11 and records the result in the workflow file (see `references/prerequisites.md` line 14 and `post-implementation.md` lines 353-356). Re-running detection inside the skeleton script costs duplicated work and risks drift if files change mid-run. Passing the JSON in (via `--commands-json <path>` or `UAT_PROJECT_COMMANDS=...`) keeps the script as a pure formatter, single source of truth, and makes Layer 4 tests trivial — the test passes a fixture JSON, no shelling out to detect-commands.sh required.

**Alternatives offered:**
- Script calls `detect-commands.sh` itself: simpler invocation but couples the formatter to detection logic and creates a moving target for Layer 4 tests.
- Static `<your build command>` placeholders for humans to fill: defeats the auto-detect work the autopilot already does.

**User's answer:** Autopilot passes JSON via env var or argv (Recommended)

**Implementation note:** Script accepts the JSON via an env var `UAT_PROJECT_COMMANDS` (env vars compose better with bash `${VAR:-<default>}` substitution than argv parsing). Falls back to `<unknown — autopilot did not pass PROJECT_COMMANDS>` placeholder if unset (e.g., when the script is invoked standalone).

---

### Q3. The runbook has a `Self-Review Findings` echo section. The autopilot already writes Self-Review findings to the workflow file. How should the script get them?

**Branch:** Self-Review echo source / cross-section reuse

**Recommended answer:** Read from workflow file at a known heading
> Self-Review is already authored into the workflow file under `## Self-Review` (see `post-implementation.md` line 471+) and copied into the PR body under `## Self-Review Findings` (line 532). The existing `extract_heading_section()` awk helper at `generate-pr-body.sh` lines 45-65 is the same primitive — reuse it. Script accepts `--workflow-file <path>` and extracts the block. Single source of truth. Works on autopilot resume (the workflow file persists across resumes).

**Alternatives offered:**
- Autopilot passes findings as argv/stdin: cleaner contract but couples orchestration code to script interface; harder to test standalone (would need to construct the Self-Review text in every Layer 4 fixture).
- Omit the echo, link to PR body: breaks for reviewers reading the runbook from a cloned working copy.

**User's answer:** Read from workflow file at a known heading (Recommended)

**Implementation note:** Script accepts `--workflow-file <path>` (optional). Missing workflow file or missing heading → emit a stub line `**Self-Review:** <not available — workflow file not provided>` rather than fail. The autopilot always passes the workflow file path in real runs.

---

### Q4. The Layer 4 unit test needs a 'full spec' fixture. The plan says snapshot of `specs/004-integration-verification/spec.md`. Vendor the snapshot or read live?

**Branch:** test fixture stability / coupling

**Recommended answer:** Vendor a snapshot under tests/fixtures/
> Reading the live spec couples the unit test to a moving target — once the archive extension's `--apply-cleanup` runs against spec 004 (which is already complete and merged per the CI/CD roadmap), the test breaks. Vendoring a frozen snapshot at `speckit-pro/tests/layer4-scripts/fixtures/spec-full-snapshot.md` matches existing Layer 4 patterns where fixtures are either inline mktemp text or committed snapshot files. ~700 LOC of vendored markdown is fixture text, not executable code — the reviewability gate's LOC counter treats it accordingly.

**Alternatives offered:**
- Read live spec 004 at run time: smaller diff but breaks once spec 004 is archived/cleaned up. The archive extension installed in this same workstream makes this real, not hypothetical.
- Synthetic full-spec inline in mktemp: most isolated but loses fidelity — hand-written full specs rarely cover the same shape combinations real specs produce.

**User's answer:** Vendor a snapshot under tests/fixtures/ (Recommended)

**Implementation note:** The other three Layer 4 fixtures (zero-stories, duplicate-FR, `[NEEDS CLARIFICATION]`) stay inline in mktemp — they're small enough to author cleanly and they target specific shape edge cases that wouldn't be naturally present in any real spec.

---

## Open Questions

None — interview reached a natural stop. All four implementation-detail decisions resolved with explicit recommendations the user accepted. Remaining implementation details (FR Coverage Matrix anchor format, exact `[NEEDS CLARIFICATION]` annotation wording, `### Edge Cases` absent behavior) are small enough to settle during the Specify or Plan phase via the autopilot's normal consensus protocol — they don't require human input.

## Recommended Next Step

Setup mode — design concept and workflow file will be committed together as part of `/speckit-pro:speckit-scaffold-spec SPEC-006a`. The next operational step is `/speckit-pro:speckit-autopilot docs/ai/specs/SPEC-006a-workflow.md` from inside `.worktrees/006a-uat-skeleton/`.

This design concept is the source of truth for scoping decisions captured during scaffolding. Any drift in downstream artifacts (spec.md, plan.md, tasks.md) from the decisions above is a defect in the downstream artifact, not in this doc, unless there is an explicit revision note.

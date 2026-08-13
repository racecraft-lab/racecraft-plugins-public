# SpecKit Workflow: ART-011 — Scaffold Integration

**Template Version**: 1.0.0
**Created**: 2026-08-12
**Purpose**: Executable workflow for ART-011. The prompts below were populated
from the technical roadmap entry and the Grill Me interview; autopilot reads
them in order.

---

## How to Use This Workflow

Run it with the autopilot:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-011-workflow.md --stage plan
```

The `--stage plan` argument bounds the run to Specify through Analyze and the
confidence gate. Omitting it reaches the same answer by auto-detection on a
freshly scaffolded file (ART-006 chain contract §3 calls passing it
"explicitness rather than necessity"). Resume into implementation later with
`--stage implement`.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-011-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

### Normative input that is not in the working tree

ART-011 builds against ART-006's FR-016 chain contract. ART-006 was archived and
its spec folder removed, so the contract exists only in git history:

```text
git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md
```

Read it before Specify. Its five fixed items are the handoff artifact, the entry
precondition, the per-platform invocation form and closed stage vocabulary, the
workflow-observable completion signal, and the statement that ART-006 ships no
scaffold-side code. The design concept quotes the parts ART-011 depends on
(see Q4, Q10, Q11), but the contract itself is authoritative.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 23 FRs, 4 user stories, 21 acceptance scenarios, 12 success criteria. G1 routed to Clarify on 3 markers |
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions, 15 questions, 2 consensus rounds. All 3 markers resolved; G2 clean. Spec 23 → 28 normative items |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass. plan.md, research.md, two contracts. 14 edit sites; measured surface 2 production files / 300 LOC, 1 slice |
| Checklist | `/speckit-checklist` | ✅ Complete | G4 pass. 3 domains, 158 items, 42 gaps, all closed. Spec 28 → 31 normative items. Two false success criteria caught and corrected |
| Tasks | `/speckit-tasks` | ✅ Complete | G5 pass. 47 tasks, 16 of 16 edit sites, zero boundary crossings. Route `one-navigable-PR`, layer plan skipped |
| Analyze | `/speckit-analyze` | ✅ Complete | G6 pass. 8 findings (0 critical, 3 high, 3 medium, 2 low), all remediated, none routed to consensus |
| Confidence Gate | G6.5 | ✅ Complete | Advisory mode. Verdict recorded in Phase 6.5 below |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G6.5 | Before Implement | Composite confidence meets the autonomous implementation threshold |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | Skill frontmatter stays valid on both platforms; no stray files under `agents/` | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | No new Bash, no `jq`, no new scripts — ART-011 is prose-only | `python3 tests/speckit-pro/run-all.py --layer 4` |
| IV. Test Coverage Before Merge | Layer 1, Layer 2 trigger evals, Layer 8 parity all green | `python3 tests/speckit-pro/run-all.py` |
| VI. KISS, Simplicity & YAGNI | No skip flag, no new agent, no configurable cap — all three declined in the interview (Q13, Q17, Q2) | Code review against the design concept's Non-goals |

**Constitution Check:** ✅ (2026-08-12, before G1)

`python3 tests/speckit-pro/run-all.py` → **7378/7378 passed** at commit `779c3f59`
(L1 1447, L4 5745, L5 186; toolchain preflight ok). Principles I, II, and IV are
discharged by that run. Principle VI is a review-time check against the design
concept's Non-goals and is re-verified at Analyze.

### Pre-Flight Evidence (Phase 0)

| Check | Result |
|-------|--------|
| `check-prerequisites` | `all_pass: true` — CLI `specify 0.11.8`, project initialized, constitution present, all SpecKit commands installed, workflow file exists, `branch: art-011-scaffold-integration` (`worktree=true,feature=true`) |
| `detect-commands` | stack `python`, source `test_runner_script`. `FULL_VERIFY` = `UNIT_TEST` = `python3 tests/speckit-pro/run-all.py`; `TYPECHECK`, `LINT`, `BUILD`, `INTEGRATION_TEST` all `N/A` |
| `detect-presets` | `speckit-pro-reviewability` v1.0.0 resolves spec/plan/tasks templates; 18 hook events configured |
| Extensions | all 8 installed and enabled: `archive`, `git`, `checkpoint`, `retrospective`, `verify`, `verify-tasks`, `agent-context`, `speckit-utils` |
| Settings | no `.claude/speckit-pro.local.md` — defaults apply (`gate-failure: stop`) |
| `resolve-confidence-mode` | `advisory` (no flag, no local config) → `CONFIDENCE_GATE_MODE=advisory` |
| `resolve-autopilot-stage` | `stage: plan`, `source: auto-detect`, `recorded_stage: null`, `planning_complete: false`, `confidence_gate_status: ⏳ Pending` |
| State-slot reclaim | slot named `docs/ai/specs/.process/ART-012-workflow.md` (prior status `completed_archived`, recorded verbatim in `prior_run_note`). Re-initialised for ART-011 **before** the Step 1.1 guard, per Step 0.6d |
| Coverage guard | `--rule status-evidence` → `status: pass`, exit 0, `plan_step_count: 33`, every error array empty |
| `PROJECT_IMPLEMENTATION_AGENT` | `speckit-pro:phase-executor` (fallback). `.claude/agents/` holds `plugin-release-auditor` and `speckit-skill-reviewer` — neither is an implementation agent. **`speckit-skill-reviewer` is a direct fit for `Post: Code Review` in the implement stage**, since it reviews exactly one changed `SKILL.md` plus its Codex mirror |
| `AGENT_TEAMS_AVAILABLE` | **false.** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set and Claude Code is 2.1.228, but this build exposes no `TeamCreate` tool and documents the `Agent` tool's `team_name` parameter as deprecated and ignored. Parallel work therefore uses batched background subagents in one message — same wall-clock, no team coordination |
| Archive Sweep | **0 eligible.** `specs/` holds only the excluded target and `specs/brand-001-racecraft-identity-system`, which is not eligible: its `SPEC-MOC.md:6` reads `status: "pending"` and its roadmap row reads "Scaffolded 2026-07-16 and parked; all seven phases still pending". ART-002/006/012 are already absent, consistent with the three most recent archive reports |

**Recorded deviation — archive sweep ran read-only.** The skill applies the sweep
on a feature branch and reserves `--dry-run` for protected branches. This run
used read-only discovery instead: archiving another spec would add unrelated file
moves to ART-011's diff, which the repository's own editing boundaries forbid.
The sweep found nothing eligible, so the two paths have the same outcome here.

### Feature State (namespaced branch)

| Field | Value |
|-------|-------|
| Feature dir | pinned via `.specify/feature.json` (gitignored) to `specs/art-011-scaffold-integration` |
| `ON_FEATURE_BRANCH` | **true.** Before the pin, `check-prerequisites` reported `worktree=true,feature=false`; after it, `worktree=true,feature=true`. The pin serves the vendored `check-prerequisites.sh` path the `/speckit-*` phase commands call internally, whose `^[0-9]{3}-` regex does not match this repo's namespaced spec IDs. Same setup ART-012 recorded at its own lines 83-89 |
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIP** — the branch already exists and is checked out in this worktree; the hook's purpose is already satisfied |
| G0 test baseline | **7378** via `python3 tests/speckit-pro/run-all.py` at `779c3f59`. Recorded once here; G7 compares against it and it is **not** recomputed later in the run |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-011 |
| **Name** | Scaffold Integration |
| **Branch** | `art-011-scaffold-integration` |
| **Stage** | implement |
| **Dependencies** | ART-006 (Autopilot Staging, shipped in PR #422) |
| **Enables** | One-command operator experience; the closing report's PR line lights up when ART-007 lands |
| **Priority** | P1 |

### Reviewability Budget

Recorded at scaffold time per the setup gate's warn disposition.

| Signal | Value |
|--------|-------|
| Primary surface | harness/adapter |
| Projected reviewable LOC | 187 (`estimate-spec-size`: 4 user stories, 2 files, 13 FRs, modify-weighted) |
| Production files | 2 — both scaffold `SKILL.md` variants |
| Total files | ~7 |
| Suggested slices | 1 |
| Budget result | within budget, no split |

**Split decision:** none. The estimator returned `status: "ok"` at 187 against
the 400 ceiling, and the work is already vertically sliced — blind-spot pass →
interview seeding → chain hand-off → closing report is one end-to-end operator
journey, not a stack of layers. Shipping the same change on both platforms is
the house parity norm, not horizontal slicing.

**Setup-gate warning, recorded:** the setup-mode reviewability gate returned
`status: "warn"` with `primary surfaces 3 exceeds warn threshold 1`. The warning
is an artifact of how the gate reads a multi-spec roadmap, not a finding about
ART-011: `reviewability_gate` takes the *last* budget match in the whole file and
unions every `primary surface` line across all fifteen entries. Its reported
90 LOC / 2 production files / 4 total files are ART-015's declared figures. No
blockers were returned. ART-011's own declared budget is the table above.

**Roadmap divergence to reconcile:** the roadmap entry declares ~4 production
files. The interview settled the production surface at 2. Re-run
`estimate-reviewable-loc` against `plan.md` once the Declared File Operations
table exists and amend the roadmap entry if the measured figure diverges — the
pattern ART-002 and ART-012 both followed.

### Success Criteria Summary

From `docs/prd-html-artifacts.md` §3.11, with the Q1 disposition applied.

- [ ] **AC-11.1** — Scaffold runs a read-only blind-spot pass over the roadmap
      scope and affected code area before grill-me; findings are shown to the
      operator and seeded into the interview and the design concept's Open
      Questions.
- [ ] **AC-11.2** — After the workflow-file commit, scaffold chains into the
      autopilot plan stage in-session; the operator can decline the chain at an
      explicit confirmation.
- [ ] **AC-11.3** — The closing report shows the draft-PR URL *when one exists*,
      the artifact index, and the next step. With ART-007 unshipped the PR line
      is omitted with a plain note rather than fabricated (design concept Q1).
- [ ] **AC-11.4** — Both platform variants implement the same flow.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-011-scaffold-integration/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: Scaffold Integration — blind-spot pass and autopilot chain

Read docs/ai/specs/.process/ART-011-design-concept.md first. Every decision
below traces to a numbered question there; the design concept is the source of
truth for scoping decisions and this prompt is its summary.

Also read the ART-006 chain contract, which is normative input and is NOT in the
working tree:
  git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md

### Problem Statement

Scaffolding a spec and planning it are two separate operator invocations today,
with nothing between them that looks for what the roadmap author failed to
consider. The Field Guide names that gap directly: unknown unknowns are what
force an agent to guess, and accumulated wrong guesses are how long-horizon work
goes off course. ART-011 closes both halves — it adds a read-only blind-spot
pass before the interview, and it chains the scaffold run into the autopilot
plan stage behind one explicit confirmation, so one invocation ends at planned,
reviewable work.

### Users

Operators of /speckit-pro:speckit-scaffold-spec on Claude Code and Codex CLI.

### User Stories

[US1] As an operator scaffolding a spec in an area I do not know well, I get a
ranked list of unknown unknowns before the interview starts, so the questions I
answer are the ones that actually change the design.

[US2] As that same operator, the findings are already seeded into the interview
and into the design concept's Open Questions, so nothing surfaced by the scan is
lost between the scan and the spec.

[US3] As an operator who has just approved a workflow file, I am asked once
whether to continue into the autopilot plan stage, and declining leaves me with
a committed, pushed branch and the exact command to resume.

[US4] As an operator whose run has ended — chained or declined, succeeded or
failed — I get one closing report that tells me what exists, where it is, and
what to do next.

### Scope — the four things this builds

1. **Read-only blind-spot pass.** Runs inside the worktree, immediately before
   grill-me (Q15). Executed by dispatching the already-shipped read-only
   `codebase-analyst` on both platforms, unmodified (Q2) — scaffold's declared
   `allowed-tools` is `Read Edit Write Skill Agent ToolSearch`, so it has no
   Grep/Glob/Bash of its own but does hold `Agent`. Seeded from the roadmap
   entry's Scope text and its dependency chain, plus any `Key Files*` section
   when one exists (Q6, Q12). *(Corrected during the error-handling checklist:
   this originally read "both present in every entry of all eleven roadmaps",
   which is false. The `**Depends On:**` label appears 104 times across ten
   roadmaps, while pr-size-governance spells the same field `**Deps:**` on all
   14 of its entries, 12 of them naming real chains. The seed reads a renamed
   variant as the chain, and appends a literal `none` only when no declaration
   exists in any spelling.)* The prompt must chase `Depends On` specs into git
   history for artifacts removed by archive sweeps, use the literal Field Guide
   words "blindspot pass" and "unknown unknowns", and state the operator's
   structural position: they have read this roadmap entry and its scope, and
   have not necessarily read the affected code area or its dependencies'
   archived artifacts (Q14). Returns at most 5 findings ranked by impact and
   surprise, and always states how many it set aside (Q13). Mandatory — no skip
   flag, mirroring grill-me's own hard constraint (Q17). Fail-open: if the
   dispatch fails or returns nothing usable, continue into grill-me and record
   the gap and its reason in both the operator output and the design concept
   (Q18).

2. **Interview seeding.** Findings reach grill-me by being appended as a
   labelled block to the `scope` argument scaffold already passes. Grill-me is
   not edited — no new argument, no output-schema change (Q3). Findings the
   interview resolves become Q&A entries; those it does not become Open
   Questions. The fact that the pass ran, how many findings were surfaced and
   omitted, or that it did not run and why, is recorded as one line in the
   design concept's existing header blockquote, which needs no new section
   (Q19). Presentation to the operator is informational — the run flows straight
   into the interview with no second confirmation (Q16).

3. **Chain hand-off.** Placed after Step 8, once the design concept, workflow
   file, SPEC-MOC, and the roadmap status flip are all committed and pushed
   (Q9). One explicit confirmation, then an in-session skill invocation of the
   autopilot with `<workflow-file> --stage plan`, in the per-platform form the
   ART-006 contract §3 fixes (Q4). Claude uses `AskUserQuestion`; Codex uses
   `request_user_input` when present. If no structured confirmation tool is
   available, do NOT chain — print the hand-off command instead (Q11).

4. **Closing report.** Renders once the chain resolves: after the plan stage on
   accept, immediately on decline. The existing "Scaffold Complete" report still
   prints before the confirmation, because a confirmation with no context is not
   a real choice (Q5). Content: the draft-PR URL when one exists and a plain
   note when it does not (Q1); an artifact index enumerating what the run
   actually produced — the scaffold-owned artifacts plus whatever the plan stage
   wrote, including the conditional research.md, contracts/, and this spec's
   chosen checklist domains (Q20); and the next step. On a failed, stalled, or
   interrupted plan stage, completion is read from the workflow file per ART-006
   §4 — terminal status on every planning row plus a recorded G6.5 verdict — and
   the report names which phases reached terminal status and how to resume
   (Q10). Read the shipped `WORKFLOW_TERMINAL_STATUSES` frozenset in
   `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
   rather than re-declaring the six status literals; the contract requires it.

### Constraints

- Production surface is exactly two files:
  `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`.
- Codex SKILL.md body is 3250 words against an 8000-word cap, so there is
  headroom; the Claude variant is 2859 words. Neither variant has a
  `references/` directory today — do not create one unless the word budget
  forces it.
- The description reword keeps the existing boundary clause intact — autopilot
  remains the right entry point for an existing workflow file — and adds the
  blind-spot pass and the chain to the capability sentence (Q7). Scaffold
  appears as a negative case in the install, upgrade, prd, and grill-me fixtures
  under tests/speckit-pro/layer2-trigger/evals/ and codex-evals/; loosening the
  boundary risks all of them.
- No new or edited agent definition on either platform. Editing one restales the
  Layer 6 sha256 corpus chain in
  tests/speckit-pro/layer6-efficiency/fixtures-codex/, which has no regeneration
  script.

### Out of Scope

- Creating the draft PR whose URL the report can show — that is ART-007.
- Any change to grill-me: no new argument, no output-schema change, no
  machinery edit.
- Any new or edited agent definition on either platform.
- A separate .process/<SPEC-ID>-blind-spots.md artifact; findings live in the
  design concept only.
- Widening scaffold's allowed-tools with Grep, Glob, or Bash.
- Normalizing the Key Files heading across the eleven roadmaps; the pass
  degrades instead.
- A skip flag for the pass, or an operator-configurable findings cap.
- New executable machinery, including a runner helper to render the report.
```

### Specify Results

Completed 2026-08-12.

| Metric | Value |
|--------|-------|
| Functional Requirements | 23 (FR-001…FR-023): blind-spot pass 7, seeding + design-concept record 4, chain hand-off 4, closing report 5, cross-cutting 3 |
| User Stories | 4 — US1/US2/US3 at P1, US4 at P2, each with an Independent Test |
| Acceptance Criteria | 21 Given/When/Then scenarios; 12 success criteria (SC-001…SC-012) each mapped to AC-11.1…AC-11.4 |
| Edge cases | 11 |
| Key entities | 6 |
| Design-concept traceability | all 21 Q-numbers cited |
| Privacy scan | clean — zero absolute home paths in either authored file |

### G1 — Routing Decision

**3 `[NEEDS CLARIFICATION]` markers remain, so Clarify runs.** All three are
routed to an already-planned session; none is a new session.

| # | FR | Routed to | Substance |
|---|----|-----------|-----------|
| 1 | FR-006 | Session 2 (Blind-Spot Pass Contract) | What counts as "returns nothing usable" for the fail-open trigger, and how that is distinguished from a pass that ran and raised zero findings |
| 2 | FR-021 | Session 1 (Description Reword) | The exact reworded description per platform and how many Layer 2 cases it needs. This is design-concept Open Question 2, whose own next step named `/speckit-clarify` |
| 3 | FR-022 | Session 3 (Chain Confirmation) | **New, and material.** `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md:449-453` tells the operator to "start a new Codex task rooted at that worktree" and "Never hand off only the inner workflow path from the parent checkout". An in-session Codex chain from a parent-rooted session contradicts that. Design-concept Q4 fixed in-session invocation without reaching this constraint |

**Deterministic gate discrepancy, recorded.** Runner helper `validate-gate`
returned `{"gate":"G1","pass":true,"markers":0}` while the spec carries three
markers. The helper counts the literal regex `\[NEEDS CLARIFICATION\]`
(`speckit_pro_runner/helpers/read_only.py:885`), which matches only a bare
bracketed marker. The active spec template prescribes the colon form —
`[NEEDS CLARIFICATION: auth method not specified …]`
(`.specify/presets/speckit-pro-reviewability/templates/spec-template.md:98-99`) —
so the helper cannot count a marker written the way the template asks for it.
G1 was therefore decided on the true count, not the helper's. This is the same
class of defect as ART-014: a gate reporting an authority it does not exercise.
It is **not** in ART-011's scope; it is raised here as evidence for a follow-up
roadmap entry.

### Files Generated

- [x] `specs/art-011-scaffold-integration/spec.md` (23 FRs, 209 lines)
- [x] `specs/art-011-scaffold-integration/checklists/requirements.md` (authoring-quality checklist emitted by the command)

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Operator sees ranked blind spots before the interview` |
| `[FR-001]` | Functional requirement | `[FR-001] The pass dispatches codebase-analyst unmodified` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Description wording [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers the fail-open path` |

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

The three sessions below are seeded from the design concept's Open Questions.
Everything still open after a 21-question interview is exactly what Clarify
should dig into.

### Clarify Prompts

#### Session 1: Description Reword and Trigger Routing

```text
/speckit-clarify Focus on the reworded scaffold description and its routing
consequences.

Q7 fixed the policy but not the text: keep the existing "Not for ... running a
populated workflow (use /speckit-pro:speckit-autopilot)" boundary intact, and add
the blind-spot pass and the chain to the capability sentence. Resolve:

- The exact replacement description text for both platform variants. They
  currently carry identical description strings — decide whether that stays true.
- Whether the new capability wording introduces any phrase that could pull
  "run my workflow file" prompts away from autopilot.
- How many Layer 2 trigger cases the change needs, and whether any belong as
  negative cases guarding the boundary that Q7 chose to preserve. Scaffold
  already appears as a negative case in four existing fixture files per platform.
- Whether the reword affects the Codex openai.yaml short_description and
  default_prompt at speckit-pro/codex-skills/speckit-scaffold-spec/agents/openai.yaml.
```

#### Session 2: Blind-Spot Pass Contract

```text
/speckit-clarify Focus on the blind-spot pass's dispatch contract and its
degraded paths.

Q2, Q6, Q12, Q13, Q14, and Q18 fixed the architecture. Resolve the wording-level
gaps:

- The literal dispatch prompt handed to codebase-analyst, including the required
  Field Guide phrasing and the structural operator-context sentence.
- What "ranked by impact and surprise" means concretely enough that two runs on
  the same spec agree on roughly the same five findings.
- The exact shape of a finding as presented to the operator and as seeded into
  the scope string — codebase-analyst's shipped description frames it for
  autopilot consensus resolution, not for a Field Guide pass, so the prompt is
  carrying the whole framing.
- What counts as "returns nothing usable" for the fail-open trigger, and the
  exact wording of the recorded gap in both the operator output and the design
  concept header line.
- Behaviour when the roadmap entry has a Scope section but no Depends On line,
  and when Depends On names a spec that was never archived.
```

#### Session 3: Chain Confirmation and Closing Report

```text
/speckit-clarify Focus on the chain confirmation and the closing report's
observable behaviour.

Q1, Q4, Q5, Q9, Q10, Q11, and Q20 fixed placement and content. Resolve:

- The literal confirmation prompt and its options on each platform, and which
  option is the default.
- The closing report's section order and exact layout, including how the
  omitted-findings count and the absent-PR note are phrased.
- How the report distinguishes "the plan stage completed" from "the plan stage
  stopped partway" using only the workflow file, and exactly which shipped
  WORKFLOW_TERMINAL_STATUSES import or read is expected.
- What the report says when the operator declines the chain — the plan stage
  never ran, so there are no plan-stage artifacts to index.
- Whether the chain re-verifies that the workflow file it is about to hand over
  is the one it just committed.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Description reword and trigger routing | 5 asked, 4 resolved from evidence, 1 routed to consensus | FR-021 marker resolved. New FR-021a (byte-identity is a requirement, not an accident) and FR-021b (three Layer 2 cases per platform). `agents/openai.yaml` evaluated and deliberately excluded, recorded in FR-022. Two Assumptions corrected: Layer 2 is a manual live gate outside `FULL_VERIFY`, and the edit restales four generated artifacts covered by `refresh-release-artifacts.py`. Spec 23 → 25 normative items |
| 2 | Blind-spot pass contract | 5 asked, 5 resolved from evidence, 0 routed to consensus | FR-006 marker resolved by defining a usable reply mechanically. FR-005 gained the literal dispatch block, FR-006 gained the reviewable-ranking rule, FR-007 gained the block-still-travels clause, FR-008 gained the one-shape finding format, FR-010 became a three-state record. Spec 25 normative items |
| 3 | Chain confirmation and closing report | 5 asked, 3 resolved from evidence, 2 routed to consensus | Last marker resolved. Codex chains only when the workflow path already resolves inside the current checkout; otherwise it asks nothing and prints the hand-off. New FR-013a (one pre-chain check sharing the guard's own predicate), FR-015a, FR-015b. FR-022 and SC-011 gain a fourth permitted divergence; SC-007 relaxed to "at most one"; two new US3 scenarios and two new edge cases; design concept gains a dated revision note. Spec 25 → 28 normative items, 0 markers |

#### Session 2 — the sentinel, and the hole it exposed

The marker asked how to tell three outcomes apart: the pass ran and found
nothing, it returned something unusable, or it never ran. The resolution makes
that mechanical rather than a judgement call. The dispatch instructions require
the literal sentence `The blindspot pass raised no unknown unknowns.` when the
pass finds nothing, so a reply is **usable** if it carries a finding or that
sentinel, **unusable** if it carries neither, and the pass **did not run** if no
reply came back at all. Three disjoint tests, no interpretation.

Chasing that distinction exposed a genuine hole. FR-007 said the degraded path
continues "with nothing seeded", and FR-008 makes the seeded scope block the
sole channel into the interview, while FR-010 has the interview write the
header-blockquote record because the scope block asked it to. Read together,
those three meant the "did not run" record had **no mechanism to be written at
all** — the one case where the record matters most was the one case that could
not produce it. FR-007 now states that "nothing seeded" means no findings are
seeded, and that the labelled block still travels in all three outcomes carrying
only its status line.

Adding the `**Blind-spot pass:**` key needs no schema change, and this run is its
own proof: the design concept written earlier already carries a size-estimate
line that the interview's four-key reference does not document, and nothing
rejected it.

Ranking is specified as **reviewable rather than deterministic**. Each finding
carries one line of impact rationale and one of surprise rationale, ordered by
impact with surprise as tiebreak, and no numeric score — FR-023 forbids new
executable machinery, so a scoring scheme would be unenforceable, and identical
output across two runs is not a property an LLM pass can promise.

#### Session 1 — the binding constraint

The description is **975 of 1024 characters**, so the entire reword had 49
characters to work in. That single fact decided the session: it forced "ready for
autopilot" out of the capability sentence, ruled out any wording that names both
new capabilities while keeping it (every such wording measures 1025–1050), and
made `agents/openai.yaml` and `when_to_use` non-options rather than choices.

The cap is confirmed twice over. `tests/speckit-pro/layer1-structural/validate-skills.py`
enforces it locally, and it is the Agent Skills platform contract — the clarify
executor could not confirm the platform half and correctly refused to assert it,
and the domain researcher then confirmed it against two independent sources. The
separate 1,536 figure is a different mechanism (`description` + `when_to_use`
combined, as truncated in the skill listing) and does not apply here;
`when_to_use` is also outside the open standard's allowed field list, so it is
not a safe way to buy budget.

### Consensus Resolution Log

| # | Question | Tags | Analysts | Round | Outcome | Artifacts updated |
|---|----------|------|----------|-------|---------|-------------------|
| 1 | Which description wording ships: change only the capability sentence (Option A, 1015 chars, docs-site untouched), or also compress sentence 1 to keep "ready for autopilot" (Option B, more headroom, restales the generated docs page)? | `[codebase]`, `[domain]` | codebase-analyst, domain-researcher | 1 | **Both agree, Option A.** codebase-analyst at high confidence: the drop is cap-forced rather than stylistic (three tested wordings that keep the phrase all exceeded 1024), and Option B reopens a decision Q7 already closed. domain-researcher at medium confidence, on a different axis: under progressive disclosure the model cannot read a skill body until after selecting the skill, so a capability absent from the description carries **zero** routing signal, not merely less — which makes naming the two new capabilities worth more than a relational claim about a sibling skill. Verified independently before applying: 1015 chars, +9 headroom, no angle brackets, only sentence 3 differs, boundary clause byte-identical | `spec.md` FR-021 (marker resolved), new FR-021a, new FR-021b |

| 2 | Given the shipped Codex prohibition on running the autopilot from a parent-rooted session, what does the Codex chain do — fire in-session unconditionally, always degrade to the printed hand-off, or fire only when the session is already correctly rooted? | `[spec]`, `[domain]` | spec-context-analyst, domain-researcher | 1 | **Both agree: fire only when already correctly rooted.** spec-context-analyst at high confidence, with a refinement that was adopted: condition on **the guard's own predicate** (does the workflow path resolve inside the current checkout) rather than an equivalent-looking root comparison, so scaffold's check and the guard can never disagree. It also established that the rooted case is reachable rather than dead, through the existing-worktree reuse path. domain-researcher confirmed the underlying fact from primary sources: a Codex task's workspace root is fixed at task start, the CLI exposes no mid-session directory command, and two open upstream issues describe exactly this gap. Unconditional chaining was rejected because the fail-closed guard would stop the run and make the confirmation a false promise, or — with a stale same-named workflow file in the parent checkout — would continue and commit into `main` | `spec.md` FR-013a, FR-015, new FR-015a, new FR-015b, FR-022 (marker resolved), SC-007, SC-011, US3 scenarios 1/5 plus two new, two new edge cases; `ART-011-design-concept.md` Revision Notes |
| 3 | Should the chain confirmation recommend "Start planning" when the shipped Claude report already says "Review both files first"? | `[spec]` | spec-context-analyst | 1 | **Recommend "Start planning"; soften the report line to "Review both files".** Recommended-first is load-bearing house convention, not a stylistic guess, and the design concept treats the chain confirmation — not the preceding report — as the one visible interactive/autonomous seam. Declining is fully non-destructive, so recommending the cautious option would fight the spec's own purpose for no safety return. Claude-only: the Codex Output section has no equivalent line | `spec.md` FR-013 |

**Residual risk carried forward, not closed.** The word "planning" is new to
scaffold's description and the sibling autopilot description already claims it,
while scaffold's existing boundary clause is scoped to "run a populated workflow"
prompts rather than to plan-stage prompts. Neither analyst could settle the
routing consequence, because only a live Layer 2 run can. The documented
mitigation is precondition contrast rather than word-avoidance: scaffold creates
a workflow file that does not yet exist, autopilot consumes one that does. FR-021b's
negative case is written to test exactly that near-miss, and the Layer 2 run is a
scheduled manual gate rather than something `run-all.py` will catch.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-011-scaffold-integration/plan.md`

### Plan Prompt

```text
/speckit-plan

Read docs/ai/specs/.process/ART-011-design-concept.md before planning. Quote its
Q-numbers for any decision that drives a planning choice.

## Tech Stack

This spec adds no code. Both changed files are Markdown skill definitions read
by an agent runtime.

- Plugin source: speckit-pro/ (ships to Claude Code and Codex CLI installers)
- Changed files: speckit-pro/skills/speckit-scaffold-spec/SKILL.md and
  speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md
- Repository tooling: Python 3.11+ standard library only (constitution II).
  No new scripts, no Bash, no jq.
- Tests: tests/speckit-pro/run-all.py, layers 1, 2, and 8

## Architecture, from the interview

- The pass is a subagent dispatch, not inline scanning. Scaffold's allowed-tools
  is `Read Edit Write Skill Agent ToolSearch` — it holds Agent but no Grep, Glob,
  or Bash, so dispatch is the only path that does not widen the tool grant (Q2).
- The engine is the shipped read-only codebase-analyst, used unmodified on both
  platforms. speckit-pro/agents/codebase-analyst.md and
  speckit-pro/codex-agents/codebase-analyst.toml both exist; the Codex autopilot
  already spawns it at
  speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md:244.
- The seeding channel is the existing grill-me `scope` argument. Grill-me is not
  edited (Q3), and its output schema is not extended (Q19).
- The chain is an in-session skill invocation with `<workflow-file> --stage plan`,
  placed after Step 8 so every scaffold-owned commit is pushed first (Q4, Q9).
- Completion is read from the workflow file per ART-006 §4, reusing the shipped
  WORKFLOW_TERMINAL_STATUSES frozenset rather than re-declaring its six literals
  (Q10).

## Sequencing inside the existing SKILL.md steps

The pass slots between Step 3.5 (Bootstrap) and Step 4 (Grill Me), inside the
worktree. The chain slots after Step 8 (Update Technical Roadmap Status). Both
SKILL.md variants already carry those step numbers, so plan the edits as
insertions at known seams rather than a restructure.

## Constraints

- Two production files. Any third production file is a budget question, not a
  detail — surface it before writing tasks.
- No new or edited agent definition. Editing one restales the Layer 6 sha256
  corpus chain in tests/speckit-pro/layer6-efficiency/fixtures-codex/, which has
  no regeneration script and fails with an error naming a digest, not a file.
- Codex SKILL.md is 3250 words against the 8000-word cap enforced at
  tests/speckit-pro/layer1-structural/validate-codex-skills.py:168-171. Track the
  post-change count; neither scaffold variant has a references/ directory to
  offload into.
- Plugin source changed means the generated artifact contract applies. Account
  for scripts/refresh-release-artifacts.py before calling the work done.
- Fill the Declared File Operations table honestly — estimate-reviewable-loc
  reads it, and ART-015 exists because that estimator is never re-fed.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | 447 lines; 14 edit sites (6 Claude, 8 Codex), each with a named anchor and requirement mapping |
| `research.md` | ✅ | 355 lines |
| `data-model.md` | ⏭ Not produced | The six key entities are prose artifacts with fixed textual shapes, not data entities; their shapes live in `contracts/`. Reason recorded in `plan.md` |
| `contracts/` | ✅ | `blind-spot-pass.md` (218 lines), `chain-handoff.md` (266 lines) |
| `quickstart.md` | ⏭ Not produced | Verification is the Layer 2 manual gate plus UAT, both already carrying exact commands in the plan's verification section. Reason recorded in `plan.md` |

**G3: pass**, 0 unresolved markers. All six constitution gates pass on both the
initial and post-design checks, with Complexity Tracking intentionally empty.
Repository suite green at 7378/7378.

#### Reviewability reconciliation, and a third blind tool

Declared in the roadmap: ~4 production files, 162 LOC. **Measured: 2 production
files, 300 LOC** (`estimate-spec-size` at 4 stories, 2 files, 28 FRs,
modify-weighted; `status: ok`, 1 slice). The LOC rise is FR granularity, not
surface growth — feeding the original 13-FR input back into the estimator
reproduces 187 exactly. Both figures sit under the 400 warn ceiling, the surface
shrank from the declaration, and the roadmap entry is in the Declared File
Operations table to be corrected.

The plan-phase helper `estimate-reviewable-loc` returned
`projected: 0, production: 0, status: pass` while correctly parsing all five
declared entries. That is not a formatting fault in the table: the helper's
`is_production_file` counts a path only when it starts with `src/`, `app/`,
`lib/`, or `scripts/`, or ends in `.ts/.tsx/.js/.jsx/.mjs/.cjs/.sql`. A plugin
repository whose shipped artifacts are Markdown scores zero by construction, so
the advisory budget cannot see this spec at all and would not see an oversized
one either.

That is the **third** gate this run found reporting a benign value on input it
cannot actually assess, after G1's marker regex missing the template's own
marker form. Both are ART-014-shaped: enforcement narrower than the authority
the surrounding documentation implies. Neither is in ART-011's scope; both are
recorded here as evidence for a follow-up entry.

#### Three places the spec under-determined the implementation

All three were found and closed during planning, and each would have produced a
broken implementation if it had reached coding.

1. **The dispatch has to be awaited, and no requirement said so.**
   `speckit-pro/agents/codebase-analyst.md:14` carries `background: true`, so an
   unawaited dispatch returns an identifier rather than findings — which makes
   FR-001, FR-002, and FR-011 jointly unsatisfiable. The plan adopts the house
   consensus pattern: Claude awaits after a background dispatch, Codex uses a
   bounded wait loop in which a status update or a timeout is explicitly not a
   result.
2. **The Codex invocation in the ART-006 contract is not runnable as written.**
   Contract §3's Codex row reads `<workflow-file> --stage plan` with no leading
   token, because the companion argv document covers argv only and states the
   command token has no Codex counterpart. Taken literally, the chain would
   invoke a bare path. Resolved to `$speckit-autopilot <workflow-file> --stage plan`,
   leaving argv unchanged.
3. **New Claude step numbers were unallocated**, while FR-012 forbids
   renumbering. Resolved to `3.6` for the pass, `9` for the chain, and `10` for
   the closing report; on Codex the chain and report extend the existing Output
   section instead.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Three domains are recommended, chosen from the signals the interview surfaced.
Confirm against the finished spec before running them.

| Signal present in ART-011 | Recommended Domain |
|---|---|
| A fixed dispatch contract, a closed finding shape, a per-platform invocation form, and a closing-report content contract | **api-contracts** |
| Fail-open on dispatch failure, no-confirmation-tool fallback, failed or interrupted plan stage, missing or renamed seed section | **error-handling** |
| An operator-facing scan, an interview, a confirmation, and two reports | **ux** |

Security, performance, data-integrity, and streaming-protocol have no signal
here: the spec adds no code, no data, no network surface, and no user input
handling.

### Step 2: Run Enriched Checklist Prompts

#### 1. api-contracts Checklist

<!-- Why this domain: ART-011 fixes four contracts in prose — what the analyst is
asked for, what a finding looks like, how the chain is invoked per platform, and
what the closing report must contain. Prose contracts drift silently. -->

```text
/speckit-checklist api-contracts

Focus on Scaffold Integration requirements:
- The codebase-analyst dispatch contract: what is passed in, what shape comes
  back, and what the caller does with each field.
- The blind-spot finding shape as presented to the operator and as serialized
  into the grill-me scope string — the same finding crosses two boundaries.
- The per-platform chain invocation form against ART-006 contract §3, including
  the closed stage vocabulary of exactly plan, implement, full — literal
  lowercase, no aliases, no alternate casing.
- The closing report's required and conditional fields, and which are derived
  rather than fixed.
- Pay special attention to: the completion test in ART-006 §4. The contract
  requires reading the shipped WORKFLOW_TERMINAL_STATUSES frozenset rather than
  re-declaring the six status literals, and a re-declaration is exactly the kind
  of drift a prose contract hides.
```

#### 2. error-handling Checklist

<!-- Why this domain: five of the twenty-one interview answers were degraded-path
decisions. Fail-open, no-confirm fallback, interrupted plan stage, missing seed
section, and unusable analyst output are each a distinct failure mode. -->

```text
/speckit-checklist error-handling

Focus on Scaffold Integration requirements:
- Fail-open when the codebase-analyst dispatch fails or returns nothing usable:
  the run continues, and the gap plus its reason are recorded in both the
  operator output and the design concept. Verify that recording is mandatory,
  not best-effort — fail-open without a visible record is a silent skip.
- The no-confirmation-tool path: the chain must NOT start, and the hand-off
  command must print.
- A failed, stalled, or interrupted plan stage: which phases reached terminal
  status, what the report says, and what resume command it names.
- A roadmap entry with no Key Files section, a renamed variant, or no Depends On
  line.
- Pay special attention to: the decline path. The operator declining the chain is
  a normal outcome, not an error, and the closing report must read as a
  successful stopping point rather than a failure.
```

#### 3. ux Checklist

<!-- Why this domain: the whole spec is an operator-facing sequence — scan,
findings, interview, confirmation, two reports — and Q5, Q13, and Q16 were all
decided on how the sequence reads rather than on what it computes. -->

```text
/speckit-checklist ux

Focus on Scaffold Integration requirements:
- The full operator sequence: scan, findings, interview, Scaffold Complete
  report, confirmation, plan stage, closing report. Verify each step gives the
  operator what the next step assumes they have.
- Exactly one confirmation in the whole run — the chain. Q16 declined a second
  gate after the findings.
- The findings presentation: five ranked items with the omitted count always
  stated. A truncation the operator cannot see reads as "that was everything".
- Both reports' relationship: the Scaffold Complete report must be enough context
  to answer the confirmation, and the closing report must not merely repeat it.
- Pay special attention to: platform parity of the operator experience.
  AskUserQuestion and request_user_input differ in affordances, and AC-11.4
  requires the same flow, not merely the same words.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| api-contracts | 63 | 17 raised, 17 remediated, 0 outstanding (1 amended at consensus) | FR-002a (new), FR-005, FR-006, FR-010, FR-013a, FR-014, FR-018, FR-019; `contracts/blind-spot-pass.md` §2/§4.1/§5/§6/§9, `contracts/chain-handoff.md` §2/§8/§9; `plan.md` rows C6 and X7 |
| error-handling | 51 | 11 raised, 11 remediated, 0 outstanding, 0 routed to consensus | FR-003, FR-005, FR-007, FR-008, **new FR-010a**, FR-018, FR-019, Edge Cases; `contracts/blind-spot-pass.md` §3/§4.1/§7/§8/**new §9.1**, `contracts/chain-handoff.md` §8.3/§9/§9.0; `plan.md` new edit sites C3a and X4a. Spec 29 → 30 normative items |
| ux | 44 | 14 raised, 14 remediated, 0 outstanding, 3 wording items routed to consensus and all 3 confirmed | SC-007, SC-011, FR-006, FR-008, FR-013, FR-014, FR-017, FR-018, **new FR-015c**, US3 scenario 5; `contracts/chain-handoff.md` §4/**new §6.1**/§8/§8.3/**new §8.4**; `contracts/blind-spot-pass.md` §6/§8. Spec 30 → 31 normative items |

#### error-handling — two self-corrections worth more than the gaps

The domain's own mid-remediation reversals were the most valuable output, because
each first attempt was wrong in a way that would have shipped.

**The dependency seed was built on a false premise, and mine was the false
premise.** The spec claimed the Scope text and the `Depends On` chain are "both
present in every entry of all eleven roadmaps". Measured: the `**Depends On:**`
label appears 104 times across ten roadmaps, and pr-size-governance carries it on
**none** of its 14 entries, spelling the same field `**Deps:**` with 12 of those
naming real chains. I verified this independently. The first remediation would
have treated `**Deps:**` as an absent field and written a literal `none` into the
dispatch payload for entries that declare several dependencies — a false
statement rather than a missing one, silently disabling the archived-dependency
archaeology on precisely the roadmap that needs it most. The fix now splits a
renamed variant, which is read as the chain, from genuine absence, which appends
`none`. Both branches are live paths.

**The completion test would have mislabelled the ordinary run.** The first fix
required a recorded `PASS` at the confidence gate. G6.5 is advisory by default,
where a `NO_DATA` result soft-skips and a `FAIL` still proceeds, so requiring
`PASS` would have inverted the closing report's heading on a normal successful
run. The test is now a recorded verdict **plus** a `Confidence Gate` row that is
not blocked, which is the file-readable fact that separates a strict-mode stop
from an advisory run that proceeded.

Two smaller results: the design-concept record was best-effort, with nothing
re-reading the file, so a missing record was indistinguishable from a pass that
never ran; FR-010a now has scaffold verify the key and write the line itself from
values it already holds. And the three no-chain endings — decline, no
confirmation mechanism, failed pre-chain check — were indistinguishable, sharing
one heading with only decline carrying a fixed outcome line; each now has its
own, with the rooting failure split from the cleanliness failure because their
remedies differ.
| **Total** | 158 | 42 raised, 42 remediated, 0 outstanding | 4 consensus rounds across the phase, every one resolved in Round 1 |

#### ux — a second false success criterion, and the operator's last screen

**SC-007 was factually false, and it was mine.** It read "outside the interview,
a scaffold run asks the operator for at most one confirmation". The shipped
skills already stop for the operator twice before this feature adds anything:
Step 3 asks whether to reuse or recreate an existing worktree, and Step 3.5 waits
for explicit approval before running any documented bootstrap command. This
repository *does* document a Worktree Preflight, so the second prompt is live
here rather than hypothetical, and on the worktree-reuse path — the path the
Codex chain depends on for coverage — Claude reaches the chain having asked
twice. Verified directly in both variants. SC-007 and SC-011 now count what this
feature adds, and the design concept carries a dated note correcting Q16's
supporting count while leaving its decision intact.

**The hand-off command had no fixed form**, despite carrying the whole ending of
every no-chain run, which is now the ordinary Codex run. Worse, the existing
report printed that command without `--stage plan`, as an instruction sitting
immediately before a confirmation offering to run it. New FR-015c fixes the
command; the label becomes `**If you stop here, run:**`, echoing the
confirmation's own `Stop here` option so the report names the alternative in the
choice's own vocabulary instead of issuing a competing order. No validator pins
that label — only the `## Scaffold Complete` heading is pinned.

**Consensus confirmed all three wording items at high confidence** and corrected
my framing of one. I had described the Codex hand-off as prose awkwardly stuffed
into a slot specified as one command. That was not an open conflict: FR-015c had
already ruled the rooting precondition part of the command rather than commentary
beside it, so what remained was a stale description of the slot, now fixed in
both the spec and the contract. Widening the slot generally would have loosened
two other commands that admit no precondition; splitting it would have broken the
four-element close.

**One domain reworded another domain's landed string, and that was checked rather
than waved through.** The ux domain rewrote the rooting-failure outcome line to
lead with what is finished rather than what did not happen. Consensus confirmed
it against `git diff` rather than reconstruction: the cause clause still names
the same condition, "nothing was rolled back" survives verbatim, exactly one row
changed per artifact, and no platform fork was introduced. It also noted honestly
that the new string still opens with a session-scoped negation, so "leads with
what is finished" is approximate rather than literal.

#### api-contracts — what the domain actually caught

Three of the seventeen were substantive rather than tidying.

**The wait had no bound, and an expired poll was being read as a verdict.** The
shipped Codex rule is explicit that "a `wait_agent` timeout is one bounded
mailbox poll, not proof that an agent is stuck", and that interruption needs a
separate execution deadline. Without the fix, a slow but healthy scan on a large
repository would have been recorded as a pass that never ran, which is the
fail-open path silently eating a real result.

**The pre-chain predicate had already drifted in the one place it must not.**
The requirement said the workflow path must "resolve inside" the checkout while
the guard's own step 2 says "exists inside", and the contract then claimed the
paraphrase was verbatim. Sharing a predicate is worthless if the two are worded
independently; both now carry the guard's wording, and canonicalise-and-compare
is explicitly banned.

**Two of the three FR-006 outcomes had no header-line shape.** The seeded block
carried a placeholder reading "the FR-006 status line for the outcome" that was
unresolvable in exactly the two degraded cases the outcome contract exists to
describe.

**Consensus amended the fix, not just ratified it.** The first remediation set
the deadline at "5 minutes or 3 consecutive expired polls, whichever comes
first". That bundled two different defects: five minutes is merely unprecedented,
but the poll count was **structurally mis-scoped** — "poll" has no Claude-side
referent, so a whichever-comes-first rule would let Codex abandon earlier than
Claude whenever its per-poll timeout is short, a behavioural divergence outside
the four-item list SC-011 permits. The poll count is now a Codex-only cue for
checking the single deadline.

The five-minute value stays, marked as **stipulated rather than precedented**:
this repository states the same deadline requirement in three shipped places and
fixes a number in none of them, so there is no house value to inherit. It is
chosen against the harm asymmetry, since a late reply is non-retroactive and too
short a deadline permanently discards a real result, while too long only costs
patience in an interruptible foreground run. Recorded as UAT-tunable, lengthen
rather than shorten.

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-011-scaffold-integration/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

Read spec.md, plan.md, AND docs/ai/specs/.process/ART-011-design-concept.md. The
design concept's Non-goals bound task generation — flag any task that would
cross one of these boundaries:

- No task may create or edit an agent definition on either platform (Q2).
- No task may edit any file under speckit-pro/skills/grill-me/ or
  speckit-pro/codex-skills/grill-me/ (Q3, Q19).
- No task may add a third production file without an explicit budget amendment.
- No task may add a script, runner helper, or any executable machinery (Q21).
- No task may add Grep, Glob, or Bash to scaffold's allowed-tools (Q2).
- No task may edit a roadmap other than the ART-011 status row (Q12).

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation — the Claude SKILL.md pass section and dispatch contract
2. User Story 1 and 2 (P1) — pass, seeding, and the design concept header line
3. User Story 3 and 4 (P1) — confirmation, chain, and both reports
4. Codex mirror and cross-platform validation

## Ordering constraints from the interview
- The pass slots between Step 3.5 and Step 4; the chain slots after Step 8. Both
  are insertions at existing seams, so the two are independent and the pass work
  and chain work can proceed in parallel [P].
- Write the Claude variant first, then mirror to Codex. Layer 8 parity compares
  them, so authoring both from one settled source avoids two rounds of drift.
- The description reword touches both frontmatter blocks and must land before
  the Layer 2 trigger evals are re-run.

## Constraints
- Production files: speckit-pro/skills/speckit-scaffold-spec/SKILL.md and
  speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md only.
- Verification tasks are Layer 1 structure, Layer 8 Codex parity, Layer 2 trigger
  evals on both platforms, and UAT evidence. There is no Layer 4 fixture to write
  — nothing new is executable (Q21).
- Track the Codex SKILL.md word count against the 8000-word cap as an explicit
  validation task.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 47 (T001–T047, sequential, no gaps or duplicates) |
| **Phases** | 9 — Setup 3, Foundational 3, US1 5, US2 4, US3 6, US4 5, Codex mirror 8, Cross-cutting 4, Verification and Polish 9 |
| **Parallel Opportunities** | 4 (`T002`, `T003` read-only preflight; `T037` fixtures, `T038` roadmap). Rare by construction: all 16 edit sites live in two files written in a fixed order |
| **User Stories Covered** | 4 of 4 — US1 6 tasks, US2 6, US3 10, US4 6 (28 story-labelled; the other 19 are setup, foundational, cross-cutting, and verification) |

**G5: pass**, 47 tasks, 0 markers. Edit-site coverage is 16 of 16. Boundary
check: zero crossings — no task creates or edits an agent definition, touches a
grill-me directory, adds a third production file, adds a script or runner helper,
widens `allowed-tools`, edits a roadmap beyond the ART-011 declaration, or
creates a `references/` directory.

**A plan anchor was wrong and is corrected.** `plan.md` placed the
`## Scaffold Complete` report "inside Step 7". It is a top-level `##` heading
sitting **between** Step 7 and Step 8 in the shipped file, so an implementer
following the plan would have looked for it under the wrong anchor. The tasks
cite literal heading strings rather than step numbers, and both `plan.md` and
`spec.md` FR-016 now say so.

**Four places are deliberately left under-determined**, each recorded in
`tasks.md` rather than papered over: the replacement wording for the Codex Hard
Constraint (the contract fixes that it becomes conditional, not what it says);
the line describing what accepting the chain does (three facts fixed, wording
not); the three literal Layer 2 query strings (intent, ASCII-only rule, and the
negative case's deciding signal are all fixed, the queries are authored at
implementation time and confirmed by the eval run); and the five operator status
lines, whose shape is fixed and whose exact text is confirmed through the UAT
runbook.

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. This is a
**placeholder** until then — leave the cells blank during scoping. The classifier
emits one machine-readable decision; the SKILL is what writes it into this section
(the script never writes a file of its own). This route is recorded only here in the
workflow file — never in the spec map. It is read downstream by the layer-planner and
multi-PR emission work that builds on top of it; recording it now wires no PR creation
or branch splitting on its own.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | `change-shape:modify-heavy` | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | *(none)* | Any release-safety warning attached to the change (empty when there is no releasability risk). |

Recorded 2026-08-12, exit 0, no hints. The reading matches the spec's own shape:
every one of the sixteen edit sites modifies existing prose in one of two files,
and nothing is destructive or concurrency-sensitive.

## Layer Plan

`layer_plan.status = skipped`. The layer planner runs only for a `split-PR`
route; this route is `one-navigable-PR`, so the planner was not invoked and the
run continues with route context carried forward. No PR emission or branch
splitting is wired by this record.

## Tasks-Phase Reviewability Boundary

Runner helper `reviewability-gate` supports **setup mode only** on the installed
runner; tasks mode is deferred and was not invoked.

| Field | Value |
|-------|-------|
| Helper ID | `reviewability-gate` |
| Requested mode | `tasks` |
| Deferral reason | Not implemented on the installed runner — the read-only helper returns `reviewability-gate read-only runner supports setup mode only` for any mode other than `setup` |

Continuing on the committed fallback evidence chain, as the skill directs:

1. **Setup-mode gate, recorded at scaffold:** `status: warn`, no blockers. Its
   single warning was diagnosed as a roadmap-wide artifact rather than a finding
   about this spec, and both the raw result and ART-011's real budget are
   recorded above.
2. **Plan-phase `estimate-reviewable-loc`, from step 7b:** `status: pass`,
   `projected: 0` — structurally blind to a Markdown-shipping repository, as
   recorded above, so it is evidence of "not over budget" rather than a measured
   figure.
3. **Operator-ratified split decision:** one vertical slice, taken at scaffold
   through the grill-me slice-sizing branch and unchanged since. The measured
   `estimate-spec-size` figure is **322 LOC at 31 FRs**, `suggested_slices: 1`,
   `status: ok`, against a 400 warn ceiling.

No size-only block, no correctness block, no stale marker state, and no
unusable gate evidence. Marker planning is not required for a
`one-navigable-PR` route.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-011-scaffold-integration
```

See the classifier script at
[`speckit-autopilot/scripts/atomicity-route`](../../speckit-autopilot/scripts/atomicity-route).

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Cross-artifact consistency across spec.md, plan.md, tasks.md, AND
docs/ai/specs/.process/ART-011-design-concept.md.

The design concept is the source of truth for scoping decisions captured during
grill-me. Where a downstream artifact contradicts it, the downstream artifact is
wrong unless it carries an explicit revision note.

Focus on:
1. Constitution alignment — especially II (no new Bash, jq, or scripts) and VI
   (KISS/YAGNI: the interview explicitly declined a skip flag, a configurable
   findings cap, and a dedicated agent).
2. Drift against the design concept's twenty-one decisions. Check by Q-number,
   not by paraphrase.
3. Non-goal violations: any task or plan step that edits grill-me, creates or
   edits an agent definition, adds a third production file, adds executable
   machinery, or widens allowed-tools.
4. Coverage — every FR and user story has a task, and every degraded path from
   the error-handling checklist has one too. The fail-open path and the
   no-confirmation-tool path are the two most likely to be specified and then
   never tasked.
5. Platform parity — every behavioural task has a Codex counterpart, per AC-11.4.
6. Whether the declared reviewability figures still match what the plan actually
   declares. The roadmap says ~4 production files and the interview settled on 2;
   this is the point to reconcile it.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

**8 findings: 0 CRITICAL, 3 HIGH, 3 MEDIUM, 2 LOW. All remediated, none routed
to consensus. G6 pass.**

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | HIGH | `contracts/blind-spot-pass.md` §10 still carried the falsified Q16 claim, "keeps scaffold at exactly one confirmation outside the interview" — the exact formulation the design concept's second revision note identifies as untrue. It also dropped "only when the chain is attempted", which is what makes the ordinary Codex run add none | §10 rescoped to the budget this feature adds, naming the three pre-existing prompts it excludes, and cross-referencing the revision note |
| A2 | HIGH | `contracts/chain-handoff.md` §1 still said the `## Scaffold Complete` report "stays inside Step 7". The contract is the designated transcription source, so this was the one copy an implementer would actually read — `spec.md`, `plan.md`, and `tasks.md` had all been corrected | §1's Claude row rewritten to "top-level heading sitting between Step 7 and Step 8", with the instruction to anchor on the literal heading string |
| A3 | HIGH | `spec.md`'s Reviewability Budget still carried the superseded 187 LOC and ~7 total files, against the canonical 322 and 9. Its stated rationale — that the reviewable surface does not grow with the FR count — is falsified by the plan's own measured series | Set to 322 and 9, rationale replaced with the series 187 at 13 FRs, 300 at 28, 322 at 31, and the closing Assumption changed from conditional to in-slice |
| A4 | MEDIUM | `plan.md`'s recorded estimator output said `modified: 4, total_entries: 4` while its own table has five rows | Helper re-run against the current table; JSON and prose updated to 5. The "not a formatting failure" argument survives unchanged |
| A5 | MEDIUM | `checklists/ux.md` said the FR count moves 29 to 30; the ux domain's own FR-015c is the 31st | Corrected to 30 to 31, crediting error-handling's FR-010a for the prior step |
| A6 | MEDIUM | `checklists/requirements.md` falsified its own gate: the "no markers remain" box was unchecked and its notes claimed three remain. Zero remain | Box checked; the three converted to resolved entries naming where each closed |
| A7 | LOW | `plan.md` said "the two things no test covers" above three bullets | Corrected to three |
| A8 | LOW | Residual Step-7 mislabels in `plan.md`'s C4 site cell and a `tasks.md` note attributing the error to prose that now disowns it | Both repointed at the literal heading and the three agreeing artifacts |

#### What Analyze verified rather than changed

Coverage is complete: all 31 requirements, 12 success criteria, and 4 user
stories map to tasks, including the three degraded paths most likely to be
specified and never tasked. Every number appearing in more than one file was
re-measured rather than trusted: 47 tasks, 16 edit sites, 2 production files,
the Codex body at exactly 3250 words through the validator's own word-count
helper, and the description at 975 today against a 1015 target. The guard
predicate quoted in FR-013a really is verbatim. Every shared fenced block diffs
byte-identical between the spec and its owning contract, which converts an
assertion the checklists had made into evidence.

#### A note on my own revision note

A1 exists because the revision note I wrote listed the downstream artifacts that
*motivated* the correction and not every artifact that *repeats* the corrected
claim. `contracts/blind-spot-pass.md` §10 was absent from that list, so nothing
swept it, and the falsified wording survived two more phases. The note now names
it and says plainly why the omission mattered. A revision note's downstream list
is load-bearing, not commentary.

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | **advisory** — resolved at Step 0.6b from no flag and no local config, and read here rather than re-resolved |
| Composite confidence | **0.88** |
| Verdict | **proceed** |
| Evidence | See below |

**What the score was computed from.**

Raising it: every gate from G1 to G6 passed, with zero markers, zero gaps, and
zero findings at any severity. Coverage is measured rather than asserted — all 31
requirements, 12 success criteria, and 4 user stories map to tasks, including the
three degraded paths. The two contracts fix exact strings and every shared fenced
block diffs byte-identical against the spec, so most of implementation is
transcription rather than interpretation. The full suite is green at 7378/7378,
and the roadmap's own budget declaration proved conservative: 2 production files
against a declared ~4, 322 LOC against a 400 ceiling, one slice.

Holding it below 0.95: three of the sixteen edit sites carry deliberately
under-determined wording, recorded in `tasks.md` rather than guessed — the
replacement Codex Hard Constraint sentence, the what-accepting-does line, and the
three literal Layer 2 queries. The five-minute wait deadline is stipulated with
no repository precedent. And the single largest residual risk is not resolvable
before implementation: the reworded description introduces the word "planning",
which the sibling autopilot description already claims, and only a live Layer 2
run can show whether routing degrades. That run is a manual gate outside
`FULL_VERIFY`, so a regression there will not surface on its own.

Advisory mode means this verdict does not gate Phase 7. It is recorded so a later
session reads the same judgement rather than re-deriving it.

**Stage boundary.** This is the terminal step of the `plan` stage.

Measured after recording the verdict, rather than assumed: with the six planning
rows and the `Confidence Gate` row all terminal, `resolve-autopilot-stage`
returns `stage: implement`, `planning_complete: true`, `recorded_stage: plan`,
with basis `auto-detect: every planning phase and the confidence gate are
terminal`. So a **bare** invocation now crosses into implementation. The crossing
is reported through that basis line rather than silent, which is the documented
intent, but it is not refused.

An earlier draft of this section claimed a bare invocation re-resolves `plan` and
re-enters here. That is true only while the `Confidence Gate` row is
**non-terminal** — after a strict-mode stop, for instance. It is not true now,
and the difference matters because it is the literal instruction an operator
follows. Pass `--stage implement` to be explicit about the crossing; pass
`--stage plan` if the intent is to re-enter planning.

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

Read tasks.md, plan.md, AND docs/ai/specs/.process/ART-011-design-concept.md.
Consult the Q&A log for the "why" behind each decision — it informs edge-case
handling and the exact wording of prose contracts. Any decision captured in the
design concept but absent from tasks.md is a gap to surface before writing, not
to silently drop.

## Approach: TDD-First, adapted for a prose-only change

This spec produces no executable code, so the red-green-refactor cycle binds to
the validators rather than to unit tests:

1. **RED**: Run the relevant validator and capture its current output as the
   baseline — Layer 1 structure, Layer 8 Codex parity, or the Layer 2 trigger
   evals for the description change.
2. **GREEN**: Make the SKILL.md edit.
3. **REFACTOR**: Re-run the validator; reconcile any regression before moving on.
4. **VERIFY**: Read the changed section as an operator would and confirm it is
   executable as written, not merely accurate.

### Pre-Implementation Setup

Before starting any task:
1. Confirm you are in the art-011-scaffold-integration worktree on that branch.
2. Run `python3 tests/speckit-pro/run-all.py` and record the baseline. No
   bootstrap is needed for the suite; docs-site is untouched by this spec.
3. Confirm the merge driver is configured for this clone:
   `git config merge.generated.driver` must return `exit 0`.

### Implementation Notes
- Match each SKILL.md's local voice. The Claude variant uses numbered `### N.`
  steps with fenced instruction blocks; the Codex variant uses `### N` headings
  under `## Procedure`. Do not converge them on one style.
- Insert at existing seams: the pass between Step 3.5 and Step 4, the chain after
  Step 8. Do not renumber surrounding steps.
- After each SKILL.md edit, re-check the Codex word count against the 8000-word
  cap. Baseline at scaffold time: Codex 3250 words, Claude 2859.
- Plugin source changed, so account for the generated artifact contract before
  calling the work done — run scripts/refresh-release-artifacts.py.
- Do not touch any agent definition. If a task appears to require one, stop and
  surface it; Q2 chose reuse specifically to keep the Layer 6 digest chain intact.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - Polish | | | |

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | |
| Post: Reviewability Diff Gate | ⏳ Pending | |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

Repository quality gates:

- [ ] All tasks marked complete in tasks.md
- [ ] Full suite passes: `python3 tests/speckit-pro/run-all.py`
- [ ] Layer 2 trigger evals re-run on both platforms after the description reword
- [ ] Codex parity green: `validate-codex-skills` and `validate-codex-parity`
- [ ] Codex scaffold SKILL.md body still under the 8000-word cap
- [ ] Generated artifacts refreshed: `python3 scripts/refresh-release-artifacts.py`
- [ ] Spec index regenerated if any spec was added or retitled
- [ ] UAT evidence recorded for the blind-spot pass and the chain, both of which
      are prompt-level and have no deterministic test
- [ ] PR title validated against the release-readiness gate before creation
- [ ] PR created and reviewed

---

## Post-Implementation Evidence

### Reviewability Diff Gate — measured, and the number disagrees with the estimate

`final-reviewability-backstop` is a deferred helper on the installed runner and
was not invoked. This is the measured diff against `origin/main`, which is the
committed evidence the skill directs the run to use instead.

| Class | Files | Note |
|---|---|---|
| Production | **2** | Both scaffold `SKILL.md` variants. Exactly the declared surface |
| Tests | 2 | The two Layer 2 fixtures |
| Docs and spec | 17 | Spec artifacts, the workflow record, roadmap and MOC updates |
| Generated | 19 | `dist/`, installed-cache copies, proof hashes. Excluded from review by the repository's own rules |
| **Total** | **40** | 19 commits |

**Production churn is 1160 changed lines (+1149 / −11), against a declared
322.** Both figures are honest and they measure different things, which is worth
stating rather than burying:

- 322 is `estimate-spec-size`'s **forward projection** from structured signals —
  4 stories, 2 files, 31 requirements, modify-weighted. It is a scoping heuristic
  computed before any line was written, and the shared reference calls it a
  forward guess.
- 1160 is the **actual line count** of the shipped prose.

Neither the plan-phase estimator nor the reviewability gate can reconcile them
here, because both are built for code: `estimate-reviewable-loc` scored this
change 0 by construction, since it recognises production only by `src/`, `app/`,
`lib/`, `scripts/` prefixes or JS/TS/SQL suffixes. A plugin whose shipped
artifacts are Markdown is invisible to it at any size.

**Judgement, stated plainly for the reviewer rather than resolved by a tool.**
This is one navigable PR by the recorded atomicity route, and the reviewer's real
burden is two prose files read against two contracts that fix most of their
strings verbatim. But 1160 lines is a large read by any measure, and a reviewer
should know that going in. The 3.6x gap between the scoping estimate and the
shipped reality is itself a finding: the estimator's per-file weighting assumes
code density, and prose skill definitions carry far more lines per unit of
behaviour. That belongs with the other estimator evidence in ART-014's scope.

### Self-Review — the mandatory four-question audit

**1. Does the implementation match the spec, or did it drift?** It matches, and
the drift that did occur was caught and reconciled rather than absorbed. One real
divergence: a fourth Layer 2 trigger case was added on an independent review's
finding while four artifacts still specified three. The verify-implementation
gate caught it; the requirement was amended toward the shipped fixtures and the
reasoning recorded, and five stale references were chased across `spec.md`,
`plan.md`, `tasks.md`, `research.md`, and a checklist.

**2. What did I get wrong during the run?** Four things, all corrected in place.
Two false success criteria of my own authoring: SC-007's confirmation count,
falsified by two prompts the shipped skill already issues, and the claim that a
dependency label is universal, falsified by 14 PRSG entries spelling it
`**Deps:**`. A wrong anchor for the `## Scaffold Complete` report, described as
inside Step 7 when it is a top-level heading between Steps 7 and 8. And a
revision note whose downstream list named the artifacts that motivated the
correction rather than every artifact repeating the corrected claim, which let a
falsified sentence survive two more phases. I also mis-identified the Bash guard
mid-implementation and passed that error to an executor, which corrected me.

**3. What is genuinely unverified at merge time?** The routing consequence of the
reworded description. Layer 2 is a live gate outside `FULL_VERIFY` and was
deliberately not run from an agent, because its Claude runner moves the
operator's installed skill directory aside. Until it runs, whether the newly
introduced word "planning" pulls prompts away from the sibling autopilot skill is
untested. Both behaviours this spec ships — the pass and the chain — are
prompt-level, so no fixture asserts against them at all; UAT is their only
evidence path.

**4. What would I tell the next person touching these files?** The Codex variant
sits at 7887 words against a hard 8000 cap. There are 113 words of headroom, and
the next change to that file hits the ceiling immediately.

### UAT Runbook

`generate-uat-skeleton` is a deferred helper on the installed runner and was not
invoked; no committed source-derived runbook exists for this spec. Recorded as
**skipped with deferred-helper evidence**, which is the fail-open path the skill
prescribes. The `uat-runbook-author` subagent was correctly not spawned, since it
runs only when a skeleton exists.

This matters more than usual here. Both shipped behaviours are prose an agent
executes, so UAT is not a supplementary check — it is the only place the pass and
the chain are observed working. The spec fixes the operator-facing strings
precisely so a runbook can assert against them.

## Lessons Learned

Written at PR creation, against PR #434.

### What Worked Well

**Consensus amended answers instead of ratifying them.** Four rounds ran and all
four resolved in Round 1, but two of them changed the answer rather than blessing
it. The wait-deadline round found that "3 consecutive expired polls" was
structurally mis-scoped, because "poll" has no Claude-side referent, so a
whichever-comes-first rule would have let one platform abandon earlier than the
other — a parity violation hiding inside what looked like a tuning constant. The
chain round supplied a refinement nobody had proposed: condition on the guard's
own predicate rather than an equivalent-looking root comparison, so the two can
never disagree.

**The contracts made implementation into transcription.** Fixing exact strings in
`contracts/` meant the shared blocks could be verified byte-identical against the
spec rather than reviewed for intent, and the skill reviewer confirmed that
programmatically across both platforms.

**Splitting the analysts by perspective paid off on the hardest question.** The
Codex chain question needed one analyst who could read shipped code and one who
could settle an external fact about the Codex CLI. Either alone would have
produced a confident wrong answer.

### Challenges Encountered

**Four of my own errors reached downstream artifacts before being caught.** Two
false success criteria — SC-007's confirmation count, falsified by two prompts the
shipped skill already issues, and the claim that the dependency label is
universal, falsified by 14 entries spelling it `**Deps:**`. A wrong anchor for the
`## Scaffold Complete` report. And a revision note whose downstream list named the
artifacts that motivated the correction rather than every artifact repeating the
corrected claim, which let a falsified sentence survive two more phases. Each was
found by a later phase, which is the process working, but each was avoidable by
measuring instead of generalising.

**Three advisory gates report a benign value on input they cannot assess.** G1's
marker count matches only a bare `[NEEDS CLARIFICATION]` and so missed all three
markers written in the template's own colon form, reporting `pass, markers: 0`
against a spec carrying three. `estimate-reviewable-loc` scores a
Markdown-shipping plugin zero by construction. `reviewability-gate` setup mode
reads the whole roadmap and returns the last entry's numbers. All three are
ART-014-shaped, and this run is evidence for that spec rather than a place to fix
them.

**Prose specs defeat the LOC estimator in both directions.** The scoping estimate
said 322; the shipped diff is 1160 production lines. Both are honest and they
measure different things, but nothing in the toolchain reconciles them, so the
budget was effectively unmeasured for this whole spec.

**The Codex word cap became the binding design constraint late.** A faithful
mirror measured 8224 against a hard 8000, and rationale prose had to be
compressed to fit. That is a real cost paid in reviewer comprehension, and it
leaves 113 words for whoever comes next.

### Patterns to Reuse

- **Verify the tool before trusting its verdict.** Reading `is_production_file`
  and the marker regex is what turned three silent passes into recorded findings.
- **When a shipped constraint contradicts a closed interview decision, correct
  the premise, not the decision.** The dated revision note kept the operator's
  choice intact while fixing the assumption underneath it — and the second note's
  omission proved that a revision note's downstream list is load-bearing, not
  commentary.
- **State a reduction plainly rather than letting it land silently.** The Codex
  chain is now the exception rather than the rule, against what the interview
  chose. Saying so in the PR is cheaper than a reviewer discovering it.
- **Give a review's best finding effect immediately.** The extra short-form
  negative eval case cost two lines and covers the misroute an operator would
  actually produce.

---

## Post-Review Amendment — 2026-08-13

An independent code review of PR #434 found nine issues. Three were applied
directly, one was a stale count, one was blocking, and four were left to the
author. This section records the outcome of all nine.

### The blocking finding: the chain could not execute

`speckit-pro/skills/speckit-autopilot/SKILL.md:11` carries
`disable-model-invocation: true`. The Claude Code skills documentation defines
it as "Only you can invoke the skill", and commit `73dcbcc7` added it
deliberately "to close the model-invocation path". Scaffold's Step 9 acceptance
branch said "print the invocation verbatim, then run it" — unexecutable. The
operator would have accepted, been promised the six planning phases "in this
same session without further prompts", and received a printed line and nothing
else.

The operator chose to demote both variants to a hand-off rather than remove the
flag. Removing it would have made the autopilot model-triggerable — a
seven-phase autonomous run with auto-commits, the exact case the flag documents
— re-enabled preloading it into subagents, and added a third production file.

Recorded in full as revision note 3 in the design concept, which enumerates
every downstream artifact.

### The four findings left to the author

| Finding | Disposition |
| ------- | ----------- |
| Codex `$speckit-autopilot` self-invocation unverified | Resolved by the same amendment: neither platform invokes now |
| The design-concept `**Blind-spot pass:**` key is outside grill-me's documented four-key blockquote | Accepted as-is. The fix crosses this spec's stated non-goal of not touching grill-me, and FR-010a's repair path already makes scaffold the writer of record. The real ART-011 design concept carries an undocumented fifth key, so the blockquote is extensible in practice |
| The 5-minute pass deadline names no clock | Not a defect. `allowed-tools` is a pre-approval list, not a restriction, so the skill's existing git commands and `date` are available; the review read it as a tool grant |
| An unresolvable ART-006 citation in Codex runtime prose | Removed with the section it sat in |

### Verification after the amendment

Suite 7378/7378, equal to the baseline. Layer 1 1447/1447. Ten shared fixed
blocks verified byte-identical across the two variants. Both descriptions 1013
characters, hash-identical. Claude body 6778 words, Codex 7092, against the 8000
cap. Generated artifacts refreshed; the zero-Bash guard passes.

One regression was caught and fixed during the work: the Codex mirror wrapped
`Never add Grep, Glob, or Bash` such that `add Grep, Glob, or Bash…` fell on its
own physical line, which the XPLAT-009 guard classifies per physical line. And a
pre-existing Layer 4 contract test required the literal phrase `start a new
Codex task rooted at that worktree`, which the rewrite had dropped; it was
restored.

### Lesson

The interview asked whether to chain and how, never whether the platform permits
it. The flag sits in the frontmatter of the one skill the entire chain depends
on. A blind-spot pass over ART-011's own scope — the feature this spec ships —
is exactly the instrument that would have surfaced it.

## Project Structure Reference

Only the paths this spec touches or reads.

```
racecraft-plugins-public/
├── speckit-pro/
│   ├── skills/
│   │   ├── speckit-scaffold-spec/SKILL.md      # production file 1
│   │   ├── grill-me/                            # read-only input; do not edit
│   │   └── speckit-autopilot/
│   │       └── scripts/validate-autopilot-phase-coverage.py   # WORKFLOW_TERMINAL_STATUSES
│   ├── codex-skills/
│   │   ├── speckit-scaffold-spec/SKILL.md      # production file 2
│   │   └── grill-me/                            # read-only input; do not edit
│   ├── agents/codebase-analyst.md              # dispatched, never edited
│   └── codex-agents/codebase-analyst.toml      # dispatched, never edited
├── tests/speckit-pro/
│   ├── layer1-structural/                       # structure + Codex skill validation
│   ├── layer2-trigger/{evals,codex-evals}/      # description routing
│   ├── layer6-efficiency/fixtures-codex/        # digest chain; untouched by design
│   └── layer8-parity/                           # cross-platform parity
├── docs/ai/specs/
│   ├── html-artifacts-technical-roadmap.md
│   └── .process/ART-011-{design-concept,workflow}.md
└── specs/art-011-scaffold-integration/          # spec.md, plan.md, tasks.md, SPEC-MOC.md
```

---

Populated from the ART-011 roadmap entry and the 2026-08-12 Grill Me interview.

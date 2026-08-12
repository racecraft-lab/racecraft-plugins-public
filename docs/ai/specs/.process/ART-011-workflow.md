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
| Checklist | `/speckit-checklist` | 🔄 In Progress | 3 domains: api-contracts, error-handling, ux |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
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
| **Stage** | plan |
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
   entry's Scope text and its `Depends On` chain — both required, both present
   in every entry of all eleven roadmaps — plus any `Key Files*` section when
   one exists (Q6, Q12). The prompt must chase `Depends On` specs into git
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
| api-contracts | | | |
| error-handling | | | |
| ux | | | |
| **Total** | | | |

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
| **Total Tasks** | |
| **Phases** | |
| **Parallel Opportunities** | |
| **User Stories Covered** | |

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
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

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

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | |
| Composite confidence | |
| Verdict | |
| Evidence | |

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

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

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

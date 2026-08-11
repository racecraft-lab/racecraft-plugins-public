# SpecKit Workflow: ART-002 — Draft-PR Template Set

**Template Version**: 1.0.0
**Created**: 2026-08-10
**Purpose**: Executable workflow for the ART-002 autopilot run. The prompts below are what each phase executes.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-002-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | spec.md + checklists/requirements.md written; 40 FRs, 4 user stories, 21 acceptance scenarios, 10 success criteria; 3 intentional `[NEEDS CLARIFICATION]` markers held for the three planned Clarify sessions |
| Clarify | `/speckit-clarify` | ✅ Complete | 3 sessions, 15 questions. **G2 PASS** — 0 `[NEEDS CLARIFICATION]`, 0 `[HUMAN REVIEW NEEDED]`, `## Clarifications` recorded in spec.md. 3 items went to consensus, 1 of those to Round 2 (3/3 unanimous). Sessions 2 and 3 needed no consensus. |
| Plan | `/speckit-plan` | ✅ Complete | **G3 PASS**. 6 artifacts, 1683 lines. Constitution Check passes on all six principles. Reviewability measured at 530 LOC per slice: warn, passing, zero blockers — two scaffold-time budget claims corrected in the spec against measured evidence |
| Checklist | `/speckit-checklist` | ✅ Complete | **G4 PASS** — 0 `[Gap]` markers. 3 domains, 134 items, 25 gaps all remediated. 2 items escalated: anchor visibility 3/3, malformed-artifact ownership 2/3 with dissent logged |
| Tasks | `/speckit-tasks` | ✅ Complete | **G5 PASS** — 79 tasks, 9 phases, 45 `[P]`, 48/48 FR coverage. Slice boundary gated at T048. Atomicity classifier returned `one-navigable-PR`, disagreeing with the recorded split; surfaced and resolved in favour of FR-040 |
| Analyze | `/speckit-analyze` | ✅ Complete | **G6 PASS** — 14 findings (0 critical, 4 high, 8 medium, 2 low), all 14 remediated, 0 remaining. `count-markers` reports 0 findings, 0 gaps, 0 clarifications. Three placement and traceability defects would have survived into filled artifacts silently; one roadmap budget-block staleness is left recorded rather than edited, because the setup-mode gate parses that block |
| Confidence Gate | G6.5 | ✅ Complete | **PASS, advisory** — composite **0.93** against a 0.90 threshold, `recommended_action: proceed`. Lowest criterion is risk assessment at 0.86, and deliberately so. Terminal step of the `plan` stage |
| Implement | `/speckit-implement` | ⏳ Pending | Slice 1 — T001–T047, PR 1 into `main` |
| Post | Post-Implementation | ⏳ Pending | Canonical 12-item closeout, slice 1 |
| Implement Slice 2 | `/speckit-implement` | ⏳ Pending | Slice 2 — T048–T079, PR 2 stacked on the slice-1 branch |
| Post Slice 2 | Post-Implementation | ⏳ Pending | Canonical 12-item closeout, slice 2 |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

**Two implementation rows, one run.** The `implement` stage's range covers both
`Implement` rows and both `Post` rows. `Implement Slice 2` is an implementation
row, not a post-implementation step. After the slice-1 `Post` row reaches
Complete, the stage's work is **not** done: `Implement Slice 2` is still
non-terminal, so selection re-enters at it. The run may only stop after
`Post Slice 2` reaches its terminal step with PR 2 open. Ending the invocation
with either slice-2 row non-terminal is a failed run, not a pause.

**Slice 1's Review Remediation must not push after T048.** PR 2's base is the
slice-1 branch at the commit PR 1 was opened from. A remediation commit landing
on that branch afterwards moves PR 2's base and desynchronises its packet. Record
slice 1's Review Remediation as a single bounded pass completed before the
`Implement Slice 2` row starts, or mark it `⏭️ Skipped` with the evidence
"deferred to the operator; remediating PR 1 after T048 would move PR 2's base".

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
| I. Plugin Structure Compliance | Gallery artifacts and manifest keep their validated shape | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | New test code is Python 3.11+ stdlib only; no Bash/`jq` | Layer 4 via `python3 tests/speckit-pro/run-all.py` |
| IV. Test Coverage Before Merge | The fill-region test lands with the templates it covers | Repository suite green from the worktree |
| VI. KISS, Simplicity & YAGNI | Ports change two blocks, one file, one status flip — nothing shared | Code review against `speckit-pro/artifact-gallery/SPA-CONTRACT.md` |

**Constitution Check:** ✅ (verified at scaffold time; re-verify at G1)

### Feature State (namespaced branch)

| Field | Value |
|-------|-------|
| Feature dir | pinned via `.specify/feature.json` (gitignored) to `specs/art-002-draft-pr-template-set` |
| `ON_FEATURE_BRANCH` | **true** (asserted by orchestrator; the upstream `^[0-9]{3}-` regex does not match this repo's namespaced spec IDs, so `check-prerequisites` reports `on_feature_branch: false` — the branch is real and `feature.json` is the sanctioned resolution path) |
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIP** — the branch already exists and is checked out in this worktree; the hook's purpose is satisfied |

### Reviewability Setup Gate (recorded at scaffold time)

Runner helper `reviewability-gate` in setup mode against the technical roadmap
returned `status: "warn", pass: true` with the single warning
`primary surfaces 3 exceeds warn threshold 1`. That count comes from the
helper's whole-roadmap scan; ART-002's own recorded budget is one primary
surface (docs/process — shipped templates). Warnings may proceed when the
workflow records the scope budget and split decision, which the next two
subsections do.

**Scope budget (from the roadmap's ART-002 section):** projected 380
reviewable production LOC, 4 production files (net-new), ~7 total files, one
primary surface. Net-new-only work carries the 1.5x greenfield allowance
(warn 600 / block 1200).

> **Superseded at Plan — see [Plan Results](#plan-results).** Two claims above
> are wrong and are corrected there against measured evidence. The LOC figure is
> low: the measured budget is **530 per slice**, because scoping counted the
> ported template body and not the capture, export, and clipboard behavior or the
> sample content every slot ships. And the greenfield allowance does **not**
> apply — the gate reports `greenfield: false`, so the thresholds in force are
> the base 400 warn and 800 block, not 600 and 1200. The gate result is **warn,
> passing, zero blockers**, and the split decision below is unaffected.

**Split decision (grill-me Q10):** ART-002 is one spec delivered as **two
vertical slices in two stacked PRs**:

1. **Slice 1** — the two always-routed templates (`implementation-plan`,
   `spec-explainer`), their manifest `status` flips, and their share of the
   Layer 4 fill-region test. Lands on this branch
   (`art-002-draft-pr-template-set`) as the first PR.
2. **Slice 2** — the two conditional templates (`code-approaches`,
   `module-map`), their manifest flips, and their test share. Branches from
   the slice-1 branch once PR 1 is open, and stacks on it (PR 2's base is that
   branch, not `main`).

Each slice is end-to-end (templates → manifest rows → passing SPA checks) and
independently green. The spec and plan cover both slices; tasks are ordered so
slice 1 completes first, and the PR-time diff gate runs per slice.

### Autopilot Pre-Flight Evidence (recorded 2026-08-10)

**Resolved stage.** `plan` (auto-detect) — "the first non-terminal planning
phase is Specify, which is ⏳ Pending". This invocation runs Specify through
Analyze plus the G6.5 confidence gate, then stops at the stage boundary.
Crossing into Implement requires an explicit `--stage implement`.

**State-slot reclaim.** `autopilot-state.json` named
`docs/ai/specs/.process/ART-006-workflow.md` with status `completed_archived`.
The slot was re-initialised for ART-002 and the prior status recorded verbatim
in `prior_run_note`. Reclaiming is normal single-slot operation, not an error.

**Archive Sweep.** No candidates. `specs/` holds exactly one directory,
`art-002-draft-pr-template-set`, which is the `--current-target` and is excluded
by contract; ART-006 was archived in PR #424.

**Tier-2 PROCESS relocation.** No eligible candidate. The only `specs/` entry is
the current target and its `SPEC-MOC.md` already carries `structureVersion: 1`,
so the already-current suppression applies.

**Prerequisites** (runner `check-prerequisites`, `all_pass: true`):

| Check | Result |
|-------|--------|
| SpecKit CLI | specify 0.11.8 |
| Project init / constitution / commands | pass |
| Branch | `art-002-draft-pr-template-set`, `is_worktree: true`, `on_feature_branch: true` |
| Settings | none — defaults (`gate-failure: stop`, `auto-commit: true`) |
| Capability coverage | advisory; acceptable fallbacks available |

`on_feature_branch` now reports **true** because `.specify/feature.json` pins
the feature directory. The Feature State table's note above (written at scaffold
time when the helper reported `false`) is superseded by this measured result.

**PROJECT_COMMANDS** (runner `detect-commands`, stack `python`, evidence
`tests/speckit-pro/run-all.py`): `UNIT_TEST` and `FULL_VERIFY` are both
`python3 tests/speckit-pro/run-all.py`; `BUILD`, `TYPECHECK`, `LINT`,
`INTEGRATION_TEST` are `N/A`.

**PRESET_CONVENTIONS** (runner `detect-presets`): preset
`speckit-pro-reviewability` v1.0.0 supplies the top layer for the spec, plan,
and tasks templates; 18 hook events configured.

**MCP / capability enumeration.** Session exposes Context7 (library docs),
Tavily (web research), RepoPrompt CE (codebase context), GitNexus (code graph),
qmd (local vault), shadcn, and Claude-in-Chrome. Agent Teams are **not**
available (`CLAUDE_CODE_ENABLE_AGENT_TEAMS` unset, Claude Code 2.1.226), so
parallel fan-out uses batched background subagents in one message.

**Confidence gate mode.** `advisory` (runner `resolve-confidence-mode`, default
precedence — no flag, no local config).

**Implementation agent.** `.claude/agents/` holds only
`plugin-release-auditor.md` and `speckit-skill-reviewer.md`, neither an
implementation agent, so `PROJECT_IMPLEMENTATION_AGENT` falls back to
`speckit-pro:phase-executor`.

**G0 test-count baseline.** `python3 tests/speckit-pro/run-all.py` →
**7226/7226 passed** (L1 1447, L4 5593, L5 186). This is the baseline G7
compares against; do not recompute it after planning.

**Constitution validation.** The four principles the spec touches are verified
by the same suite, which is green at baseline: I (Plugin Structure) via L1
1447/1447, II (Cross-Platform Runtime & Script Safety) via L4 5593/5593, IV
(Test Coverage Before Merge) and VI (KISS) via the full 7226/7226 run.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-002 |
| **Name** | Draft-PR Template Set |
| **Branch** | `art-002-draft-pr-template-set` |
| **Dependencies** | ART-001 (brand kit, manifest schema, SPA contract — satisfied by PR #407, fix #409) |
| **Enables** | ART-007 (Draft-PR Emission) |
| **Priority** | P1 |
| **Stage** | implement |

### Success Criteria Summary

- [ ] Four branded single-file SPA templates exist under
      `speckit-pro/artifact-gallery/templates/`: `implementation-plan.html`,
      `spec-explainer.html`, `code-approaches.html`, `module-map.html`.
- [ ] Each embeds both canonical blocks byte-for-byte, carries a correct
      upstream attribution header, contains no prohibited construct, and its
      manifest entry's `status` is flipped `planned` → `shipped` (the only
      manifest change).
- [ ] Fill regions are marked with paired HTML comments
      (`<!-- FILL:<slot>:START/END -->`), documented by an in-file header
      inventory, and shipped with representative fictional sample content.
- [ ] Export affordances match each entry's declared `exports`:
      implementation-plan and module-map export reader objections tied to
      their phase/module via inline per-item note fields; code-approaches
      exports the radio-selected approach plus reason; spec-explainer carries
      no export controls.
- [ ] A Layer 4 fill-region test (Python stdlib HTML parse) asserts a
      hardcoded roadmap-named slot floor per template plus both-ways
      header-inventory/body-marker agreement.
- [ ] ART-001's gallery scanner passes over all four artifacts; Layer 1 and
      the full repository suite are green; release payloads are regenerated.
- [ ] Manual `file://` render/console checks are recorded as UAT runbook
      steps and executed by the operator.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-002-draft-pr-template-set/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: Draft-PR Template Set (ART-002)

### Problem Statement
The staged review workflow's plan stage ends at a draft PR the operator
reviews before implementation, but the gallery has no planning-review
artifacts for that checkpoint. Port the four draft-PR templates as
Racecraft-branded, self-contained single-file SPAs so ART-007's plan stage
has documents to populate. Without them, the plan-stage review has no
artifact surface and the reviewer falls back to raw markdown.

### Users
- The operator reviewing a draft PR at the plan-stage checkpoint (reads the
  artifacts, records objections/choices, exports conclusions).
- The ART-007 authoring agent (fills the documented fill regions from
  spec.md / plan.md / tasks.md / the design concept).
- Gallery browsers deciding which template fits (judge by rendered sample).

### User Stories (grouped by slice; slice 1 lands first)
Slice 1 (always-routed at draft-pr stage):
- [US1] Implementation Plan template: phases, data-flow diagram, mockup
  slots, risk register, task inventory; inline per-item objection capture;
  exports ["prompt", "markdown"] carrying objections tied to their phase.
- [US2] Spec Explainer template: TL;DR, goals/non-goals, collapsible
  acceptance criteria, FAQ from clarify answers; declared read-only
  (exports []), so it carries no export controls.

Slice 2 (conditionally routed; branches from the slice-1 branch, stacked):
- [US3] Code Approaches template: side-by-side trade-off comparison; radio
  group selects the winning approach plus one "why" field; exports
  ["prompt", "markdown"] carrying the chosen approach and reason.
- [US4] Module Map template: boxes-and-arrows with hot path highlighted;
  inline per-module objection capture; exports ["prompt", "markdown"]
  carrying objections tied to their module.

### Constraints
- Every artifact obeys speckit-pro/artifact-gallery/SPA-CONTRACT.md: one
  HTML file, both canonical blocks embedded byte-for-byte with markers
  (BRAND-KIT from brand-kit.css, GALLERY-HEAD from theme-toggle.html),
  exact-label upstream attribution header agreeing with the manifest entry,
  no prohibited constructs, fonts as the single permitted external request.
- Manifest change is exactly four status flips planned → shipped. No shared
  foundation file changes, no id/trigger/exports edits.
- Fill regions: paired HTML comments FILL:<slot>:START/END; slot inventory
  documented in an in-file header comment; representative fictional sample
  content inside every slot (grill-me Q1-Q3).
- Export affordances follow the SPA contract's export obligations: live-state
  derivation, keyboard operability, text success feedback, clipboard failure
  reveals a selectable field, labels name the destination ("Copy as prompt",
  "Copy as Markdown").
- Accessibility: WCAG AA obligations inherited from the brand kit; color
  never the only carrier of meaning; kit focus-visible treatment; reduced
  motion honored for any motion the template adds.
- Diagram surfaces keep the upstream template's mechanism, restyled with
  brand tokens (grill-me Q6, moderate confidence — confirm during Plan).
- Test code: Python 3.11+ stdlib only, under tests/speckit-pro/unit/, named
  for durable capability (never a spec ID).

### Out of Scope
- Generation/authoring logic that populates fill regions (ART-007).
- Editing brand-kit.css, theme-toggle.html, SPA-CONTRACT.md, the signal
  vocabulary, or any other manifest entry.
- Vendoring upstream files; only branded derivatives are committed.
- Automated browser testing; file:// render checks stay manual UAT steps.
- A dedicated acceptance-harness page (standard UAT runbook instead).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 40 (FR-001…FR-040) |
| User Stories | 4 — US1 Implementation Plan (P1), US2 Spec Explainer (P2), US3 Code Approaches (P3), US4 Module Map (P4) |
| Acceptance Criteria | 21 acceptance scenarios (6/5/5/5) + 10 success criteria (SC-001…SC-010) + 11 edge cases |

FR grouping: artifact form (7), routing catalog (3), fill regions (5), reader
capture (3), export affordances (7), per-template content (5), accessibility
(5), verification and delivery (5). Every FR carries `[USn]` tags: US1 on 35
FRs, US2 on 27, US3 on 34, US4 on 35.

Declared reviewability budget: primary surface docs/process; ~380 reviewable
LOC feature-wide, ~190 per slice; 4 net-new production files (2 per slice) plus
the catalog modified once per slice. Within budget; the two-sequential-PR split
is recorded.

> **Superseded at Plan — see [Plan Results](#plan-results).** These are the
> figures the spec carried at Specify time and they are recorded here as the
> point-in-time state, not as current fact. The measured budget is **530
> reviewable template lines per slice**, at a 400 warn and an 800 block with no
> greenfield allowance, and the verdict is **warn, passing, zero blockers**. The
> spec's Reviewability Notes and Reviewability Budget were amended to match. The
> requirement count also moved: 40 FRs at Specify, 48 after three Clarify
> sessions and three checklist domains.

**G1 routing decision — proceed to Clarify.** A direct
`grep -c "NEEDS CLARIFICATION" spec.md` returns **3**; the three markers are
deliberate, one per planned Clarify session. Runner helper `validate-gate`
reported `{"gate":"G1","markers":0,"pass":true}` because it matches the bare
`[NEEDS CLARIFICATION]` token and this spec uses the colon form
`[NEEDS CLARIFICATION: …]`. The routing outcome is the same either way and G2's
check is a substring grep, which does catch the colon form. Recorded as a
non-blocking helper diagnostic, not a gate failure.

Deliberately open markers carried into Clarify:

| # | Section / FR | Held for |
|---|--------------|----------|
| 1 | Functional Requirements → Fill regions, FR-015 | Session 1 — exact slot inventory, granularity, and source artifact per slot; names must not be invented before the upstream sources are read |
| 2 | Functional Requirements → What the reader records, FR-018 | Session 2 — disclosure vs revealed objection fields, which items an export lists, empty-state export text, how an export names an item |
| 3 | Functional Requirements → What each template presents, FR-030 | Session 3 — whether each upstream drawing mechanism survives brand re-styling without a prohibited construct |

### Files Generated

- [x] `specs/art-002-draft-pr-template-set/spec.md` (573 lines)
- [x] `specs/art-002-draft-pr-template-set/checklists/requirements.md` (64 lines)

### Constitution Validation (initial, after Specify)

`python3 tests/speckit-pro/run-all.py --layer 1` → **1447/1447 passed**,
including `validate-moc-stale-index` and `validate-spec-index-determinism`, so
the new spec files did not stale the SPEC-MOC generated index. Absolute-path
and template-placeholder scans of both authored files: clean.

### Hook Disposition (Specify)

| Hook | Optional | Disposition |
|------|----------|-------------|
| `before_specify` → `speckit.git.feature` | false | **SKIP** — branch already exists and is checked out; the hook's purpose is satisfied |
| `before_specify` → `speckit.archive.run` | true | Announced, not executed (sweep found no candidates) |
| `after_specify` → `speckit.speckit-utils.doctor` | true | Announced, not executed |
| `after_specify` → `speckit.git.commit` | true | Announced, not executed — the orchestrator owns commits |

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Implementation Plan template` |
| `[FR-001]` | Functional requirement | `[FR-001] Both canonical blocks embedded byte-for-byte` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Slot inventory naming [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers export failure path` |

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: Fill-Region Slot Inventory

```text
/speckit-clarify Focus on the fill-region slot inventory: the exact kebab-case
slot names per template (the design concept's first Open Question), which
roadmap-named slots form the hardcoded Layer 4 test floor for each of the four
templates, and the header-inventory comment format the doc/body agreement
check parses. Slot names follow the manifest id character rules
(filename-safe kebab-case). The design concept (grill-me Q1, Q2, Q7) fixed
the mechanism; this session fixes the names.
```

#### Session 2: Export and Capture Interaction Details

```text
/speckit-clarify Focus on the capture-and-export surfaces: the disclosure
pattern for inline per-item objection fields in implementation-plan and
module-map (grill-me Q4), the radio-group + reason composition in
code-approaches (Q5), what each export emits when no objection/choice exists
(the contract forbids inventing conclusions), and the exact success/failure
feedback text pattern for clipboard operations over file://.
```

#### Session 3: Upstream Port Fidelity

```text
/speckit-clarify Focus on porting fidelity after fetching the four upstream
files from anthropics/html-effectiveness: whether each upstream diagram
mechanism survives branding cleanly (design concept Open Question 2; Q6 chose
keep-upstream at moderate confidence), which upstream sections map to which
fill slots, and any upstream construct on the SPA contract's prohibited list
that the port must drop.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Fill-region slot inventory | 5 | 21 slots fixed across the four templates, one slot per section (never per repeated item), flat regions, per-item anchor attributes; inventory comment format fixed as one `Slot: … \| Fills: … \| Source: …` line per slot placed after the attribution header; source vocabulary closed to five artifacts; feature-specific content outside a slot forbidden. FR-015 marker retired. |
| 2 | Export and capture interaction details | 5 | Objection field starts collapsed behind a native disclosure whose control states in text whether the item carries a note; code-approaches uses a native grouped single-choice control with a visible group label and an optional reason; exports list only items the reader recorded against; empty-state wording is fixed per export kind and explicitly denies approval; items are named by four live-state coordinates plus a fragment-usable anchor; one cause-neutral clipboard failure message with a selectable, focused fallback field. FR-018 marker retired. Zero items for consensus. |
| 3 | Upstream port fidelity | 5 | Both drawings keep their mechanism and neither is re-authored; styling normalizes to classes in both, with class hooks added to the implementation plan because a blanket selector would flatten its deliberate hierarchy; arrowheads restyle by their own selector; no upstream color survives. Zero prohibited constructs in all four sources, independently verified. Full section-to-slot mapping fixed: three regions authored fresh, ten dropped. Three color-only carriers found with remedies. `spec-explainer` ports no script at all, making its read-only status structural. FR-030 marker retired; **zero markers remain**. Zero items for consensus. |

The session-1 executor fetched all four upstream sources read-only (HTTP 200,
held in session scratchpad, nothing written or staged) so slot names derive from
real section structure. Two roadmap-named regions have no upstream counterpart
and are authored fresh: the implementation plan's task inventory (upstream's
fourth section is key code) and the spec explainer's goals and non-goals
(upstream's counterpart is a configuration walkthrough with no Racecraft
equivalent).

#### Session 2 literal wordings (carry verbatim into Plan, Implement, and UAT)

The spec states these as requirements; the exact strings live here so the
implementation and the acceptance runbook check the same text.

**Empty-state export bodies.** Header lines naming the feature and the artifact
are still emitted; only the body differs.

| Template group | Kind | Body |
|---|---|---|
| implementation-plan, module-map | `prompt` | `No objection was recorded. There is nothing here to act on. Do not treat this as approval.` |
| implementation-plan, module-map | `markdown` | `No objection was recorded. This record is not an approval.` |
| code-approaches | `prompt` | `No approach was chosen. There is nothing here to act on. Do not treat this as approval of any approach.` |
| code-approaches | `markdown` | `No approach was chosen. This record is not an approval of any approach.` |
| code-approaches, chosen without a reason | both | reason line reads `Reason: none given.` |

**Clipboard feedback.** One `role="status"` region present from load, beside the
export controls and outside every fill region.

| State | Message |
|---|---|
| n objections, n > 1 | `Copied. 2 objections are on the clipboard.` |
| exactly one objection | `Copied. 1 objection is on the clipboard.` |
| no objection recorded | `Copied. The text says no objection was recorded.` |
| approach chosen | `Copied. Your chosen approach is on the clipboard.` |
| no approach chosen | `Copied. The text says no approach was chosen.` |
| any failure | `Copy failed. The text is in the field below. Select it and copy it by hand.` |

**Item reference line.** `<slot> / <item label>  (#<anchor>)`, anchor valued
`<slot>-<item-slug>`.

**Two implementation traps this session found.**

1. Upstream `04-code-understanding.html` runs an accordion script that
   force-closes every other `details.snippet` on toggle. That behavior must not
   reach objection disclosures — it would close a reader's in-progress field.
   Scope it by class.
2. In code-approaches, wrap the existing approaches container in the native
   grouping element rather than replacing it, so the side-by-side layout FR-028
   requires survives.

#### Session 3 section-to-slot mapping (carry into Plan, Implement, and ART-002's own handoff to ART-007)

Every one of the 21 slots is accounted for against an upstream region, an
authored-fresh decision, or a borrowed layout shape.

| Template | Slot | Upstream region |
|---|---|---|
| implementation-plan | `feature-header` | page head eyebrow and title, minus the prompt box |
| | `plan-stats` | the four-cell summary strip |
| | `phases` | the milestones section |
| | `data-flow` | the data-flow section and its caption |
| | `mockups` | the mockups section |
| | `risk-register` | the risks and mitigations section |
| | `task-inventory` | **none — authored fresh**, reusing the key-code grid shape |
| spec-explainer | `feature-header` | header eyebrow and title |
| | `tldr` | the TL;DR block |
| | `goals` | **none — authored fresh** |
| | `non-goals` | **none — authored fresh** |
| | `acceptance-criteria` | no content counterpart; reuses the step list's disclosure shape |
| | `clarification-faq` | the FAQ definition list |
| code-approaches | `feature-header` | page head, minus the prompt box |
| | `approaches` | the approaches grid, including trade-off tables and chip footers |
| | `recommendation` | the recommendation aside |
| module-map | `feature-header` | header repo line and title |
| | `module-summary` | the summary paragraph |
| | `module-graph` | the request-path heading and diagram panel |
| | `modules` | the callstack walkthrough |
| | `key-files` | the key-files aside |

**Dropped (10):** three prompt boxes; implementation plan key code and open
questions; spec explainer navigation, step content, configuration tabs, and
gotchas; module map gotchas.

**Orchestrator verification of the `[security]` findings.** Session 3 tagged two
items `[security]` because they concern prohibited constructs. Rather than route
opinion at them, the orchestrator re-fetched all four upstream sources and ran an
independent parse-based scan. It reproduced the executor's result exactly: byte
counts identical, zero prohibited constructs across all four, script counts 0 /
1 / 0 / 1, no markup builders and no URL-shaped literals in either script, and
the naive text search hitting exactly three times in the code-approaches source
where the parse confirms they are text nodes inside displayed sample code. Two
independent implementations agreeing against the bytes is stronger evidence than
a three-analyst vote on the same prose, so the items were not escalated. The
shipped artifacts are scanned again by the real gallery validation at implement
time, so this finding also has a downstream backstop.

### Consensus Resolution Log

| # | Item | Categories | Round | Analysts | Verdict | Confidence | Applied |
|---|------|-----------|-------|----------|---------|-----------|---------|
| C1 | Q2b — does the roadmap's compound "goals/non-goals" contribute one floor entry or two? | `[spec]` | 1 | spec-context-analyst | **Two** — `goals` and `non-goals`. FR-036 ties the floor to *delimited slots*, and the settled inventory realizes the region as two real slots with no compound slot, so a one-entry floor is either unsatisfiable or stops protecting the other half. FR-027 and US2's first acceptance scenario both list them separately. | High (N=1 high → use answer) | Applied — FR-036 |
| C2 | Q1a — who authors the per-item objection control inside a list slot? | `[codebase]` `[domain]` | 1 | codebase-analyst, domain-researcher | **The template's own inline behavior mounts it** onto each item's stable anchor; the fill region stays inert content plus anchors. Both agreed independently. | High / High (N=2 both agree → use answer) | Applied — new FR-016a and FR-017a |
| C3 | Q2a — is the module-map floor `{module-graph}` or `{module-graph, modules}`? | `[spec]` | 1 → **2** | spec-context-analyst, codebase-analyst, domain-researcher | **`{module-graph}` alone, 3/3 unanimous**, and FR-016 gets its own separate assertion instead. The distinguished path is a content property of `module-graph`, not a slot. | R1 medium → escalated → 3/3 at Round 2 | Applied — FR-036 and new FR-036a |

**C2 evidence worth carrying forward.** The codebase analyst found that FR-016
is tagged `[US1] [US4]`, both delivered by ART-002 — so deferring the control to
ART-007 would ship artifacts with no working objection capture and break US1's
own independent test. It also found the pattern already shipping twice in the
canonical head block (the theme control is built with `createElement` and wired
with `addEventListener`; the brand mark is mounted onto an empty
`data-rc-brand-mark` element), and confirmed the gallery scanner already parses
script-built markup through the same prohibited-construct checks as document
markup. The domain analyst added that the mounted control must be inserted
immediately after its own anchor so focus order stays correct, that repeated
same-function controls must be identified consistently, and that confining
generated values to text and plain-data-attribute positions is the standard
injection-safety line. Both are now stated as FR-016a and FR-017a.

| C4 | Checklist/security — does exporting an item's anchor violate FR-023's "nothing the reader did not see"? | `[spec]` `[security]` | 1 (all 3, security rule) | spec-context-analyst, codebase-analyst, domain-researcher | **Keep the narrow carve-out, 3/3 unanimous.** The anchor is mechanically derived from the item's own visible label, so it restates something rendered rather than revealing something withheld. The alternative — a visible fragment link on every item — would add a second tab stop to every item across three templates to fix a rule violation that causes neither harm the rule was written to prevent. | High / High / High | Applied — FR-023, plus both drift conditions |
| C5 | Checklist/security — who guards against a malformed *generated* artifact, ART-002 or ART-007? | `[spec]` `[security]` | 1 (all 3, security rule) | spec-context-analyst, codebase-analyst, domain-researcher | **ART-007 owns it, 2/3.** ART-002 records a named handoff obligation and adds no runtime guard. Dissent logged below. | High / High / Medium (dissent) | Applied — Dependencies handoff |

**C4's two drift conditions, which no one had raised.** The carve-out is only
sound while the anchor tracks the label *as currently rendered*. Two ways it
quietly stops holding, both now written into FR-023: a slug frozen at generation
time while its label is later edited no longer restates anything visible; and
when two items in one slot carry identical labels, uniqueness forces a suffix,
which must derive from the item's visible list position rather than an opaque
counter. Without those, "derived from a visible label" degrades into a claim
nobody can check.

**C5's dissent, logged rather than discarded.** The domain analyst argued for a
split: the producer owns the conformance rule, but the consumer should still make
a cheap precondition check at the point it relies on the anchor, because
tolerating unspecified input conceals faults and a first-party producer is still
an unvalidated one. It lost on cost and testability — the guard defends against a
defect ART-002's own artifacts cannot exhibit, could not be exercised by any test
this feature is permitted to write, and would be triplicated across three
templates with no shared runtime against a budget already warning.

Its central piece of evidence was absorbed rather than dropped, because it makes
the handoff concrete: a duplicate anchor raises no error at all. Identifier
lookup is specified to return the first match in document order, so a filled
artifact with two identical anchors renders perfectly, mounts a control on the
wrong item, and exports a conclusion naming an item the reader never annotated.
Duplicate identifiers also break control-to-label association. That is now stated
in the handoff, so ART-007 inherits a named failure mode rather than a vague
request to be careful.

**C3 reasoning, worth keeping because it is the same shape as a decision this
repository has already made once.** Round 1 was right on the text but could not
close its own gap, so escalation earned its keep. The codebase analyst supplied
the missing half: the gallery test already contains `check_c8`, which exists
precisely because a count check and a one-directional membership check cannot
see a *coordinated* change on both sides of a relationship. The fix there was a
new, separate check closing against an independent shipped source, explicitly
not a widened literal. The same file states the scoping rule twice in its own
words: a literal is pinned outside the artifact it validates, because "a set
derived from the file under validation asserts only that the file equals
itself", and a check is "closure between two shipped artifacts", never a second
copy of one file's names. Folding `modules` into a roadmap-sourced floor would
blend two source documents into one literal.

The domain analyst then removed the last reason to hesitate: widening the floor
would not have closed the gap at all. Floor membership proves only that a region
named `modules` exists; FR-016 is an interaction requirement, so only a check
that inspects the objection anchors verifies it. Testing the requirement beats
testing a proxy, and a hardcoded literal that accretes entries from mixed
rationales is a recognized test smell. It also confirmed that leaving an
interaction-level, keyboard-driven browser behavior to an itemized manual
acceptance step is standard practice rather than a hole, which is exactly the
constraint FR-038 and the stdlib-only rule already impose here.

**Carried finding — a real gap, now assigned.** The gallery scanner's existing
"script builds a named, stateful control" check is scoped to the canonical head
block's shared region only. It does not extend to a per-item objection control
living in a template's own script. FR-036a is the assignment: a separate
assertion that every repeated item inside a list slot carries its stable anchor.
Carry it into Plan and Tasks as its own task, not as a floor entry.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/art-002-draft-pr-template-set/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Artifacts: hand-authored HTML + CSS + vanilla inline JavaScript, one file
  per template, no build step, no bundler, no external resource except the
  two font hosts the canonical head block already requests.
- Brand system: tokens from the embedded BRAND-KIT block (--rc-* custom
  properties; heading face is --rc-font-display, NOT --rc-font-heading).
- Testing: Python 3.11+ stdlib only (html.parser, json, unittest) under
  tests/speckit-pro/unit/; repository suite via
  python3 tests/speckit-pro/run-all.py.
- Docs: pnpm --dir docs-site reference:generate after any tracked
  .md/.py/.sh change under tests/speckit-pro/ (deps already installed in
  this worktree).

## Constraints
- Read speckit-pro/artifact-gallery/SPA-CONTRACT.md in full before
  designing; the validated shape is normative. A port changes two embedded
  blocks, one new artifact file, and exactly one catalog value (status).
- Slice ordering is load-bearing: slice 1 (implementation-plan,
  spec-explainer) must be complete and green before slice 2 work begins;
  slice 2 ships from a branch cut from slice 1's branch and stacked on it (two
  PRs — grill-me Q10 and its route follow-up).
- Fetch upstream sources read-only at implement time from
  anthropics/html-effectiveness (files: 16-implementation-plan.html,
  14-research-feature-explainer.html, 01-exploration-code-approaches.html,
  04-code-understanding.html — all verified present on main). Commit only
  branded derivatives.
- Release payloads: gallery files ship in the plugin payload; account for
  the generated-artifact contract (scripts/refresh-release-artifacts.py)
  in the plan's Declared File Operations.

## Architecture Notes
Decisions fixed by the grill-me interview (quote the design concept,
docs/ai/specs/.process/ART-002-design-concept.md, when a choice needs its
"why"):
- Q1: fill regions are paired HTML comment markers FILL:<slot>:START/END —
  chosen to reuse the gallery's validated marker-pair convention and stdlib
  HTMLParser comment handling.
- Q2: slot inventory lives in an in-file header comment (self-describing
  artifact; no shared-file edits).
- Q3: every slot ships with representative fictional sample content.
- Q4: implementation-plan and module-map capture objections via an inline
  per-item keyboard-reachable disclosure + labeled textarea; exports walk
  non-empty notes with item anchors.
- Q5: code-approaches uses one radio per approach + a single labeled reason
  textarea; export reads live selection state and explains when nothing is
  selected.
- Q6: diagram surfaces keep the upstream mechanism, restyled with brand
  tokens (confirm cleanliness after fetching upstream; escalate only on a
  prohibited-construct conflict).
- Q7: the Layer 4 test asserts a hardcoded roadmap-named slot floor per
  template AND both-ways agreement between header inventory and body
  markers.
- Q9: manual browser checks become numbered UAT runbook steps.
```

### Plan Results

**G3 PASS** — `plan.md` exists with 0 unresolved markers.

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | 592 lines. Constitution Check passes on all six principles; two Complexity Tracking rows (accepted duplication, review-size warn) |
| `research.md` | ✅ | 401 lines. Decision rationales |
| `data-model.md` | ✅ | 196 lines. Entities and types |
| `contracts/slot-inventory-contract.md` | ✅ | 185 lines |
| `contracts/export-payload-contract.md` | ✅ | 160 lines. Pins the session-2 literal wordings once, so three implementations can differ in style but not in behavior |
| `quickstart.md` | ✅ | 149 lines. Developer onboarding |

Line counts above are as at the end of Plan. The Checklist and Analyze phases
edited `plan.md` and both contracts afterwards, so the files on disk are longer;
the table is the phase record, not a current inventory.

**Declared File Operations** (authored surface only):

| Slice | Entries | New | Modified | Added LOC |
|---|---|---|---|---|
| 1 (US1+US2, this branch) | 6 | 3 | 3 | ~505 template + ~250 test |
| 2 (US3+US4, fresh branch) | 3 | 2 | 1 | ~530 template |

#### Reviewability budget, measured (autopilot Step 7b, advisory)

Both helpers were run by the orchestrator and reproduce the plan executor's
numbers.

| Helper | Result |
|---|---|
| `estimate-reviewable-loc` | `status: pass`, `projected: 0`, `new: 5`, `modified: 3`, `total_entries: 8`, `greenfield: false` |
| `reviewability-gate` (setup, against `plan.md`) | `status: warn`, `pass: true`, `reviewable_loc: 530`, `production_files: 3`, `total_files: 6`, `primary_surfaces: 1`, **`blockers: []`** |

`projected: 0` from the estimator is a floor, not a measurement: its
production-file test recognizes none of this feature's path shapes. The gate's
530 is the number to trust, and only the LOC dimension warns — production files
(3 of 6), total files (6 of 15), and primary surfaces (1 of 1) all sit inside
their warn thresholds.

**Two scaffold-time claims are corrected here**, and the spec's Reviewability
Notes and Reviewability Budget were amended to match rather than left to drift
into Analyze:

1. **~190 LOC per slice → 530.** Scoping counted the ported template body and
   omitted the capture, export, and clipboard behavior each template carries,
   plus the worked-example content every slot ships with.
2. **The greenfield allowance does not apply.** The gate reports
   `greenfield: false`, so the thresholds are the base 400 and 800, not 600 and
   1200.

Neither changes the delivery decision. 530 is comfortably below the 800 block, a
warning proceeds on recorded scope and a recorded split, and both are recorded.
No typed exception is claimed and FR-040's two stacked pull requests stand.

#### Shared-behavior duplication, and why it stays

Three templates need near-identical capture and export behavior, and there is no
shared runtime to put it in — every artifact is one self-contained file. The plan
keeps three copies rather than reaching for an abstraction, because every
mechanism that could remove the duplication is prohibited here: a sibling script
file breaks the single-file rule, a build step is excluded by the tech stack, and
a generator is ART-007's scope. An abstraction would be a build step under
another name, and the constitution prefers three similar lines to a premature
one. Only one of the three is a near-copy in any case; code-approaches is a
different shape. What is shared is the **specification, not the code**: the
literal wordings, the four-coordinate item reference, and the single clipboard
failure message are pinned once in the export-payload contract, and each template
is verified against that one table.

#### Layer 4 test design

`tests/speckit-pro/unit/test-artifact-fill-regions.py`, registered at layer 4 in
`tests/speckit-pro/suite-manifest.json`. Six checks: the roadmap floor as a
literal subset check conditioned on catalog status; both-ways inventory agreement
as two separate checks; inventory shape; **per-item anchors as its own assertion,
per FR-036a**; and floor-literal-to-catalog closure. It parses with the gallery
scanner's comment-collection idiom, so comment-shaped text inside a script is raw
character data and never reaches the comment handler — a marker embedded in an
export routine's string literal cannot declare a slot the body does not delimit.
Slice 2 edits no test file: its cases key on catalog status, so the flips turn
them on.

**Slice 1 ordering, RED first:** fixture cases and pinned literals with
unimplemented checks → run → RED → implement checks → register and regenerate
docs → US1 template with its status flip in the same change, which is where the
floor binds for the first time → US2 → payload refresh and closeout.

#### Generated artifact contract

Declared under its own heading, deliberately outside the block the estimator
parses: ~22 mirror files plus 12 proof snapshots per slice, machine-written by
`scripts/refresh-release-artifacts.py`. Two facts were checked against the
ART-001 gallery commit rather than assumed — the payload build copies
`artifact-gallery` as a whole directory so it needs no edit, and the runner
manifest and its checksum must not move, because ART-002 edits no runner source.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Signals present in ART-002: user-facing artifact UI with forms/disclosures
(**ux**), WCAG/keyboard/contrast obligations inherited from the brand kit
(**accessibility**), executable documents with prohibited-construct and
untrusted-input rules (**security**). Three domains; api-contracts,
streaming, and data-integrity do not apply to static single-file artifacts.

### Step 2: Run Enriched Checklist Prompts

#### 1. accessibility Checklist

Why this domain: the SPA contract carries explicit WCAG AA obligations
(contrast pairings, focus-visible, color-not-sole-carrier, reduced motion,
keyboard-operable exports) that every new interactive surface must satisfy.

```text
/speckit-checklist accessibility

Focus on Draft-PR Template Set requirements:
- Inline objection disclosures and textareas: keyboard reachability, visible
  focus, programmatic labels (Q4).
- Radio group + reason field in code-approaches: native single-choice
  semantics, state exposed to AT (Q5).
- Export controls: operable by keyboard, success reported in text, clipboard
  failure reveals a selectable field.
- Color pairings drawn only from the audited brand-kit table;
  --rc-border-subtle never carries meaning; --rc-danger-text for red body
  copy.
- Pay special attention to: the hot-path highlight in module-map — color
  must not be the only carrier of the highlight (WCAG 1.4.1).
```

#### 2. ux Checklist

Why this domain: four reader-facing documents whose purpose is a review
checkpoint; a stranded conclusion defeats the stage.

```text
/speckit-checklist ux

Focus on Draft-PR Template Set requirements:
- Sample content reads as clearly fictional yet representative, so a gallery
  browser can judge fit at a glance (Q3).
- Objection capture sits inline with the item it attaches to; the tie is
  structural, not prose (Q4).
- Export content rules: the reader's conclusion with enough context to act
  on alone — artifact, spec, and anchor named; never inventing conclusions.
- Theme toggle, brand mark opt-in, and offline typeface degradation behave
  per the head block.
- Pay special attention to: what each export emits when the reader recorded
  nothing — explain, never fabricate.
```

#### 3. security Checklist

Why this domain: gallery artifacts are executable documents with a
prohibited-construct list, a policy declaration, and (downstream, ART-007)
untrusted-input fill rules the templates' structure must not undermine.

```text
/speckit-checklist security

Focus on Draft-PR Template Set requirements:
- No prohibited construct in any port: base element, scheme-relative
  reference, on* handler attributes, srcdoc, form with submission target,
  ping (upstream constructs on this list are dropped, never ported).
- Script bodies survive the lexical URL scan; no external reference outside
  the two font hosts; assets only as image/font data: URIs.
- Fill-region placement keeps future interpolated values out of the four
  forbidden contexts (script body, style body, URL-valued attribute, event
  handler) so ART-007's generator can fill slots safely.
- Attribution headers agree with each manifest entry (repository + file).
- Pay special attention to: sample content inside FILL regions must sit in
  text positions, modeling the contract's text-position rule for ART-007.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| accessibility | 44 | 8 found, 8 remediated, 0 remaining | FR-017a, FR-018, FR-024, FR-025, FR-030a, FR-031, new FR-035a, new FR-035b |
| ux | 50 | 8 found, 8 remediated, 0 remaining | new FR-014a, FR-018, new FR-018a, FR-019, FR-022, FR-035, SC-004, 2 new edge cases, export-payload contract |
| security | 40 | 9 found, 9 remediated, 0 remaining | FR-003, FR-011, FR-015, FR-016a, FR-023, FR-025, Assumptions, plan's shared-behavior decision |
| **Total** | **134** | **25 found, 25 remediated, 0 remaining** | 2 items escalated to consensus, both `[spec, security]` |

All three domains ran in parallel against the same files. Each wrote its own
checklist file, kept edits small and targeted, and re-read before every write.
Several edits reported the file changed underneath them; all landed, none was
abandoned, and a final grep confirmed every intended edit present.

#### The findings worth carrying forward

**Two requirements were literally unsatisfiable as written, and neither was an
omission.** FR-003 required the attribution header's upstream repository to equal
what the template's catalog entry declares, but a catalog entry carries only an
origin and a filename and declares no repository at all; the contract names the
repository once, centrally. And FR-030a required each diagram's text equivalent
"outside the drawing", which read as outside the fill region too — so a filled
artifact would have carried a fictional description of a real drawing. Both now
say what they meant.

**A validation blind spot, found empirically rather than by reading.** The
repository's construct scanner extracts markup from script string literals using
a single-line-only pattern. The security agent tested both forms: a single-line
string carrying a prohibited handler was caught; the same markup as a multi-line
template literal was extracted by nothing and reached none of the construct
checks. Rather than rely on a scan that cannot see the case, FR-016a now requires
controls to be built by element creation with attributes set by name and text set
through the text-valued property, and forbids assembling control markup as a
string at all. The blind spot is recorded in the plan as the reason.

**The fill mechanism cuts both ways, and two elements sit on opposite sides of
it.** A "this is sample content" notice is only true while the content is sample
content, so it belongs **inside** a fill region, where the first fill removes it.
The brand mark is the exact inverse: inside a region it would be deleted on first
fill, so it belongs **outside**. Both are now stated once, together, in the plan's
port worksheet, because the two rules only make sense read against each other.

**Three smaller traps.** A whitespace-only objection field would have exported as
a recorded objection, so a note now requires one non-whitespace character.
Recorded work is discarded on reload with nothing telling the reader, now stated
as a requirement and an edge case. And a plain data attribute is only
conditionally safe, because the gallery scan is default-deny on attributes and
reports an unrecognized attribute with a URL-shaped value as an unverified host.

**One process note.** The `count-markers` helper counts the literal `[Gap]` token
across `spec.md`, `plan.md`, and every file under `checklists/`, so checklist
prose that merely mentions the token registers as a gap. Word around it.

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-002-draft-pr-template-set/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → slice 1 stories → slice 2 stories →
  validation; slice 1 (US1, US2) must be fully green before any slice 2
  (US3, US4) task starts — the slices ship as two stacked PRs
- Mark parallel-safe tasks explicitly with [P] (the two templates within a
  slice are parallel-safe; the shared Layer 4 test file is not)
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation (Layer 4 fill-region test scaffolding: floor lists + doc/body
   agreement parser — written RED first)
2. US1 Implementation Plan + US2 Spec Explainer (slice 1) — port, brand,
   fill regions, exports/read-only, manifest flips, tests green
3. Payload regeneration + slice 1 closeout (PR 1)
4. US3 Code Approaches + US4 Module Map (slice 2, branch cut from slice 1) —
   port, brand, fill regions, exports, manifest flips, tests green (PR 2)

## Constraints
- Test file under tests/speckit-pro/unit/, named for capability (e.g.
  fill-region validation), NEVER for the spec ID
- Templates land at speckit-pro/artifact-gallery/templates/<id>.html with
  <id> exactly the manifest id
- Any task fetching upstream sources is read-only network access; upstream
  bytes never staged
- Bound task generation by the design concept's Non-goals: no authoring
  logic, no shared-file edits, no browser automation
```

### Tasks Results

**G5 PASS** — 79 tasks found, 0 unresolved markers.

| Metric | Value |
|--------|-------|
| **Total Tasks** | 79 (T001-T079, sequential, no gaps or duplicates) |
| **Phases** | 9 — Setup T001-T006; Layer 4 RED-first T007-T016; US1 T017-T029; US2 T030-T040; slice 1 closeout T041-T047; slice boundary T048; US3 T049-T059; US4 T060-T073; slice 2 closeout T074-T079 |
| **Parallel Opportunities** | 45 `[P]` |
| **User Stories Covered** | 4 — US1 13 tasks, US2 11, US3 11, US4 14 |
| **FR coverage** | 48/48, verified programmatically against a `## Requirement Coverage` table; no row cites a non-existent task ID |

**Slice boundary.** Slice 1 is T001-T047. **T048 gates it**: confirm PR 1 merged,
cut the slice-2 branch from merged main, verify the catalog already carries slice
1's two flips and the test file is present and unmodified. No task in the last
three phases may start before T048 passes. Slice 2 is T049-T079.

**Three judgement calls the executor surfaced, all correct.**

1. **The two catalog flips inside a slice are not parallel-safe**, which corrects
   an assumption in the dispatch prompt. The two templates in a slice are
   parallel-safe as *files*, but T029/T040 and T059/T073 both edit
   `manifest.json`. They carry no `[P]` and the file records why.
2. **`[P]` needed a definition here**, because every task inside one story edits
   that story's single artifact file. It means parallel-safe against the *other
   template in the same slice*. Phase 2 carries no `[P]` at all.
3. **The invented sample feature is pinned rather than left to the implementer.**
   `NIMBUS-101 — Offline Draft Sync`, with `NIMBUS` verified absent repo-wide, so
   FR-014a's "outside every roadmap namespace" is checkable by grep instead of
   being a matter of taste.

Every item on the carry-forward list from Clarify and Checklist landed as its own
task, including the four that are easiest to lose: R5 separate from R1 (T012), the
sample-notice-inside and brand-mark-outside pair (T027, T037, T057, T071),
element creation rather than string-assembled markup (T025, T055, T069), and the
upstream accordion scoped away from objection disclosures (T068).

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

The grill-me interview already committed to a two-slice, two-sequential-PR
delivery (see Reviewability Setup Gate above); the classifier's decision is
expected to agree (`split-PR`). If it disagrees, surface the conflict at G5
rather than silently following either.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | `change-shape:modify-heavy` | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | none | Any release-safety warning attached to the change (empty when there is no releasability risk). |

#### The classifier disagrees with the recorded split — surfaced, not followed silently

This section predicted `split-PR`. The classifier returned **`one-navigable-PR`**,
so the disagreement is reported here as this workflow file requires, rather than
either answer being adopted quietly.

**Amended 2026-08-11 — the split stands, the merge gate does not.** The two-slice
split and its membership are unchanged. What changed is the second slice's base:
PR 2 now targets the slice-1 branch instead of a `main` that already contains it.
The operator asked for one `--stage implement` invocation that executes all 79
tasks and ends with both pull requests open, and agents never merge pull requests
in this repository, so a merge-gated boundary makes that outcome unreachable.
This is an operator decision superseding the grill-me Q10 follow-up, recorded
here and in FR-040 rather than applied silently. The classifier's
`one-navigable-PR` reading is still not followed: one pull request would carry
both slices' authored lines toward the 800-line block threshold.

Stacking also turned out to be the only shape that satisfies D8 without a merge.
The Layer 4 validation module lands whole in slice 1, and six slice-2 tasks state
their acceptance against checks that module implements, so a slice 2 branched
from `main` before slice 1 merged could not evaluate them. The slices were never
independent; the original plan concealed that behind the merge gate.

**The recorded split stands.** Delivery remains two pull requests.
Three reasons, in order of weight:

1. **It is an operator decision, already ratified and already encoded.** The
   two-slice, two-sequential-PR delivery was chosen by the operator at grill-me
   Q10 and its follow-up, and it is now **FR-040**, a MUST in the specification
   with its own acceptance criteria. A read-only advisory classifier does not
   overturn a recorded requirement; if it should, that is a specification change
   with its own review, not a silent reroute at G5.
2. **The measured size points the same way.** The reviewability gate reads 530
   reviewable LOC from the plan's declared operations and warns at a 400 warn and
   800 block. One pull request carrying both slices would land materially above
   that, in the region the block threshold exists to prevent. The split is what
   keeps each pull request inside a reviewable budget.
3. **The classifier is explicitly advisory and wires nothing.** It writes no file
   and creates no branch. Recording its decision is the whole of its effect here.

**One observation about the signal, recorded without overclaiming.** The single
decisive signal is `change-shape:modify-heavy`, which reads oddly against a
feature whose production surface is four net-new template files plus one net-new
test file, with the routing catalog the only modified file. That may be an
artifact of what the classifier scans in a feature directory dense with planning
prose. It is noted as a possible calibration issue for whoever owns the
classifier, not asserted as a defect, and it did not affect the outcome.

#### Layer plan

Route is not `split-PR`, so the layer planner does not run.
`layer_plan.status = skipped` is recorded in `autopilot-state.json` and here,
and the run continues with route context. This is the prescribed path for every
non-split route.

#### Tasks-phase reviewability boundary — deferred, with the fallback chain used

| Field | Value |
|---|---|
| Helper | `reviewability-gate` |
| Requested mode | `tasks` |
| Result | `status: input_error`, exit 2, "read-only helper rejected the request inputs" |
| Reason | Tasks mode is deferred on the installed runner; only setup mode is active |

This is expected, not a failure. The autopilot contract says tasks mode is
deferred and directs the run to continue on committed fallback evidence. That
evidence is present and current:

- **Setup-mode gate at scaffold:** `warn`, `pass: true`, zero blockers.
- **Plan-phase `estimate-reviewable-loc`:** `pass`.
- **Plan-phase setup-mode gate against `plan.md`:** `warn`, `pass: true`,
  530 reviewable LOC, zero blockers.
- **Operator-ratified split decision:** recorded above, and now FR-040.

A `warn` with recorded scope and a recorded split is a proceed. No typed
exception is claimed, and no marker planning state is required, because no
size-only block exists to route around.

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-002-draft-pr-template-set
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — Python-stdlib-only test code, no Bash/jq, plugin
   structure intact
2. Coverage gaps — every FR and user story has tasks; both slices covered;
   the Layer 4 floor covers all roadmap-named slots
3. Consistency between task file paths and the real gallery/test layout
4. Drift against the design concept
   (docs/ai/specs/.process/ART-002-design-concept.md): the concept's Goals,
   Non-goals, and Q1-Q10 decisions are the source of truth for scoping
   decisions — if spec.md, plan.md, or tasks.md contradicts it without an
   explicit revision note, the downstream artifact is wrong
5. Slice integrity — no slice 2 task is a prerequisite of a slice 1 task
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation, violates constitution | **Must fix before G6 gate** |
| `HIGH` | Significant gap, impacts quality | Should fix |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Note for future |

### Analysis Results

**G6 PASS** — 13 findings, 13 remediated, 0 remaining. No CRITICAL. Constitution
alignment clean on all six principles; `run-all.py --layer 1` 1447/1447 and the
full suite 7226/7226 both green before and after remediation. The marker helper
`count-markers` reports `{"type":"findings","total":0}` in both loops; every
finding below came from cross-artifact reading rather than a written marker.

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | HIGH | The `code-approaches` grouping element FR-017 requires had no placement rule, and "wrap the existing approaches container" put it inside the `approaches` fill region, where the first fill deletes it. Every filled artifact would carry ungrouped, unlabelled choices while the shipped template still passed. | FR-017 now requires it outside the marker pair; recorded in the plan's worksheet, T052, T055, and both contracts |
| A2 | HIGH | The inside/outside rule was stated for 5 elements and missing for 5 more — the export controls, the FR-019 purpose line, the FR-018a not-saved line, the clipboard fallback field, and the grouping element. Same silent failure mode as A1. | FR-011 now states the general rule and lists both columns; plan, tasks, and both contracts carry the full ledger |
| A3 | HIGH | FR-035a (title names the feature) contradicted FR-015 and the "feature-specific content outside a slot" edge case: a title is head metadata no fill region can enclose, so a filled artifact would announce `NIMBUS-101` as its window identity. | FR-035a reconciles the two and hands the title rewrite to ART-007; recorded in *Dependencies* and named as deferred work in T047 and T079 |
| A4 | HIGH | `plan.md` *Reviewability Projection* still described the spec as recording ~380 lines and quoted a spec sentence that no longer existed, calling the correction an open spec-amendment candidate after the spec had already been amended. | Rewritten to attribute ~380 to the roadmap's pre-read projection and to state that the spec now agrees |
| A5 | MEDIUM | SC-002 and SC-005 were cited by zero tasks, while the PR packet requires mapping every success criterion to files and evidence. | Cited in T026, T046, T056, T070, T078, and a full SC coverage table added to `tasks.md` |
| A6 | MEDIUM | T003's acceptance check `grep -rl 'NIMBUS' docs/ai/specs/ specs/` was self-falsifying: the pin was recorded in this workflow file at task generation, so the grep now matches this feature's own records. | Scoped to exclude ART-002's own records; the corrected command verified to return nothing |
| A7 | MEDIUM | `plan.md` cited "the spec's Non-goals", which did not exist. The design concept's five Non-goals reached no downstream artifact, and "no dedicated acceptance-harness page" appeared nowhere at all. | `spec.md` gains a *Non-Goals* section restating all of them plus the no-persistence non-goal |
| A8 | MEDIUM | File counts disagreed: the spec said "~7 across the feature; 6 per slice" and `tasks.md` said "six authored files per slice", but the plan declares 6 for slice 1 and 3 for slice 2, with 8 distinct files feature-wide. | Corrected in `spec.md` Reviewability Budget, the `tasks.md` header, and T006 |
| A9 | MEDIUM | `plan.md` claimed the ~250-line validation module was excluded "as the spec's budget already scopes it out"; the spec excluded only generated payload artifacts and named the validation as a review surface. | The exclusion is now stated in the spec's budget and described the same way in both files |
| A10 | MEDIUM | Slice 2 had no docs-site bootstrap. T002's install is per worktree, T048 cuts slice 2 on a fresh branch, and T076 ran `reference:generate` against dependencies that need not be present. | T076 runs its own `pnpm --dir docs-site install --frozen-lockfile`; T002's scope note corrected |
| A11 | MEDIUM | The *Specify Results* budget block recorded ~380 / ~190 per slice / "within budget" with no supersession pointer, unlike the Setup Gate block above it. | Supersession note added, matching this file's own convention |
| A12 | LOW | "Phase 2 depends on T004 for nothing and on T002 only for T015" was garbled, and the Phase 7/8 dependency line omitted T003, whose pinned sample feature the slice-2 tasks hardcode. | Both lines rewritten |
| A13 | LOW | The *Plan Results* artifact table records line counts from the end of Plan; the checklist and analyze phases have since grown `plan.md` and both contracts. | Labelled as a phase record rather than a current inventory |

**Verified against the repository, not assumed.** All four catalog entries match
what the spec claims (`source.file`, `exports`, `stage`, `status: planned`); the
canonical blocks measure 318 and 140 lines exactly; `payloads.py` copies
`artifact-gallery` as a whole directory name, so T005's premise holds; the
attribution header's five labels and the single upstream repository name are in
`SPA-CONTRACT.md` where FR-003 says; the prohibited-construct list matches the
spec's Assumptions item for item; the suite-manifest entry shape matches T014;
every path the plan and tasks name exists; the 7226 / 1447 / 5593 / 186 baseline
in `quickstart.md` and T001 is exact; and the FR-036 floor traces entry by entry
to the roadmap's ART-002 scope prose.

**Slice integrity holds.** No task in T049–T079 is named as a prerequisite of any
task in T001–T047. The only cross-slice reference was T002 naming T076 as a
consumer, which A10 resolved. T048 gates the boundary explicitly and no task in
Phases 7, 8, or 9 may start before it passes.

**One item left for the operator, not escalated to consensus.** The roadmap's
ART-002 *Reviewability Budget* block still reads 380 / within budget / one
vertical slice / greenfield. It is stale against the measured 530-per-slice warn,
and it was deliberately not edited: `reviewability-gate` parses that block in
setup mode, so rewriting it during Analyze would change a helper's input for no
gain. The correction is recorded in the spec, the plan, and twice in this file.

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | advisory (default; no `--strict` flag, no local config override) |
| Composite confidence | 0.93 |
| Verdict | proceed |
| Evidence | See the emit and its per-criterion reasoning below |

### Pre-Implement Confidence

```text
📊 Confidence: 0.93

- Task understanding: 0.96
- Approach clarity: 0.94
- Requirements alignment: 0.95
- Risk assessment: 0.86
- Completeness: 0.94
```

**Task understanding, 0.96.** The four upstream sources were fetched and read
rather than assumed, and the decisive claim about them — zero prohibited
constructs — was verified twice by independent implementations that agreed on
byte counts, script counts, and the three text-node false positives. Every slot,
every dropped region, and every authored-fresh region is enumerated and traced.

**Approach clarity, 0.94.** The port worksheet, the section-to-slot mapping, the
Layer 4 test design, and the literal export wordings are all concrete enough to
implement without re-deciding anything. The deduction is for the one structural
compromise: three near-duplicate behavior implementations with no shared runtime.
Behavior is pinned by a single contract table, but style can still drift.

**Requirements alignment, 0.95.** 48 of 48 requirements carry tasks, verified
programmatically against a coverage table with no dangling task IDs. All five
consensus outcomes landed in artifacts, both placement rules are correct and
unswapped, and the design concept's Non-goals hold and are now restated in the
spec.

**Risk assessment, 0.86 — the lowest score, and the honest one.** Four open
risks. The reviewability budget moved twice during the run, and on the inclusive
reading that counts the test module, slice 1 is ~755 against an 800 block, which
is tight rather than comfortable. The roadmap's own budget block is knowingly
stale and deliberately not edited. The atomicity classifier disagreed with the
recorded split. And the hardest implementation work is unproven: restyling an
attribute-heavy drawing without flattening its deliberate hierarchy, and getting
three duplicated capture-and-export implementations to behave identically.

**Completeness, 0.94.** Tasks are decomposed to 79 items across 9 phases with the
slice boundary genuinely gated. The deduction is inherent to the stage: runtime
behavior has no automated verification by design, so the manual acceptance
runbook is the only thing that exercises it.

**Verdict: proceed.** Advisory mode never blocks, and nothing here argues for
stopping. The score is deliberately not higher, because the risks above are real
and the next stage is where they get tested.

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```text
/speckit-implement

## Approach: TDD-First

For each task, follow this cycle:

1. **RED**: Write failing test defining expected behavior
2. **GREEN**: Implement minimum code to make test pass
3. **REFACTOR**: Clean up while tests still pass
4. **VERIFY**: Manual verification of acceptance criteria

### Pre-Implementation Setup

Before starting any task:
1. Verify the worktree suite is green:
   python3 tests/speckit-pro/run-all.py
2. Fetch the upstream reference files read-only from
   anthropics/html-effectiveness (main): 16-implementation-plan.html and
   14-research-feature-explainer.html for slice 1;
   01-exploration-code-approaches.html and 04-code-understanding.html for
   slice 2. Keep them outside the repository tree (session scratchpad);
   never stage upstream bytes.
3. Re-read speckit-pro/artifact-gallery/SPA-CONTRACT.md — the canonical
   blocks are copied WITH their markers, byte for byte, from
   brand-kit.css and theme-toggle.html.

### Implementation Notes
- The heading typeface token is --rc-font-display (NOT --rc-font-heading;
  an undefined custom property fails silently).
- Prohibited upstream constructs are dropped, never ported.
- Slice discipline: complete and verify US1+US2 (slice 1) before touching
  US3/US4. Slice 2 ships from a fresh branch after slice 1's PR merges.
- After any tracked .md/.py/.sh change under tests/speckit-pro/, run
  pnpm --dir docs-site reference:generate (deps installed in this worktree).
- Shipped-byte changes (gallery files) require release-artifact
  regeneration (scripts/refresh-release-artifacts.py) before closeout —
  hand-editing generated payloads is prohibited.
- Manual file:// checks per template (render, console clean, theme toggle,
  exports, keyboard pass) are recorded as UAT runbook steps for the
  operator, not automated.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation (L4 test RED) | | | |
| 2 - Slice 1: US1 + US2 | | | |
| 3 - Slice 1 closeout (PR 1) | | | |
| 4 - Slice 2: US3 + US4 (PR 2) | | | |

---

## Post-Implementation Checklist

The canonical closeout. Every row must reach Complete or an explicit
`Skipped` before the run may report completion. Run it once per slice PR — the
table below is slice 1's, and the second table after it is slice 2's.

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

### Slice 2 closeout (PR 2)

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

- [ ] All tasks marked complete in tasks.md
- [ ] Tests pass: `python3 tests/speckit-pro/run-all.py`
- [ ] Docs references regenerated: `pnpm --dir docs-site reference:generate`
- [ ] Release artifacts regenerated for shipped-byte changes
- [ ] Manual verification recorded in the UAT runbook
- [ ] PR created (never merged by the agent) with the release-note fence
- [ ] Reviewed and merged by a human

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
│   └── artifact-gallery/
│       ├── SPA-CONTRACT.md          # normative porting contract (read first)
│       ├── manifest.json            # routing catalog — status flips only
│       ├── brand-kit.css            # BRAND-KIT canonical block source
│       ├── theme-toggle.html        # GALLERY-HEAD canonical block source
│       ├── UPSTREAM-NOTICE.md       # MIT license text attribution points at
│       └── templates/               # NEW — the four ported artifacts
├── tests/speckit-pro/
│   └── unit/
│       ├── test-artifact-gallery.py # existing scanner (covers new artifacts)
│       └── <fill-region test>       # NEW — capability-named, stdlib-only
├── scripts/
│   └── refresh-release-artifacts.py # payload regeneration for shipped bytes
├── docs/ai/specs/
│   ├── html-artifacts-technical-roadmap.md
│   └── .process/                    # this workflow + the design concept
└── specs/art-002-draft-pr-template-set/  # spec.md, plan.md, tasks.md, SPEC-MOC.md
```

---

Template based on SpecKit best practices; populated for ART-002 from the technical roadmap and the grill-me design concept.

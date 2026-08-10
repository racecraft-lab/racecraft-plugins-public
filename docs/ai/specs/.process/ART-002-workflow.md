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
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
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
vertical slices in two sequential PRs**:

1. **Slice 1** — the two always-routed templates (`implementation-plan`,
   `spec-explainer`), their manifest `status` flips, and their share of the
   Layer 4 fill-region test. Lands on this branch
   (`art-002-draft-pr-template-set`) as the first PR.
2. **Slice 2** — the two conditional templates (`code-approaches`,
   `module-map`), their manifest flips, and their test share. Branches from
   main **after slice 1 merges**; not stacked.

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
| **Stage** | plan |

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

Slice 2 (conditionally routed; branches after slice 1 merges):
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
  slice 2 ships from a fresh branch after slice 1 merges (two sequential
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
No typed exception is claimed and FR-040's two sequential pull requests stand.

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
| accessibility | | | |
| ux | | | |
| security | | | |
| **Total** | | | |

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
  (US3, US4) task starts — the slices ship as two sequential PRs
- Mark parallel-safe tasks explicitly with [P] (the two templates within a
  slice are parallel-safe; the shared Layer 4 test file is not)
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation (Layer 4 fill-region test scaffolding: floor lists + doc/body
   agreement parser — written RED first)
2. US1 Implementation Plan + US2 Spec Explainer (slice 1) — port, brand,
   fill regions, exports/read-only, manifest flips, tests green
3. Payload regeneration + slice 1 closeout (PR 1)
4. US3 Code Approaches + US4 Module Map (slice 2, after slice 1 merges) —
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

The grill-me interview already committed to a two-slice, two-sequential-PR
delivery (see Reviewability Setup Gate above); the classifier's decision is
expected to agree (`split-PR`). If it disagrees, surface the conflict at G5
rather than silently following either.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no releasability risk). |

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

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. Gate semantics
are unchanged; this section records the verdict so a later session can read it.

| Field | Value |
|-------|-------|
| Mode | <!-- advisory (default) or strict --> |
| Composite confidence | <!-- 0.00-1.00 --> |
| Verdict | <!-- proceed / remediate / stop --> |
| Evidence | <!-- what the score was computed from --> |

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
`Skipped` before the run may report completion. Run it once per slice PR.

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

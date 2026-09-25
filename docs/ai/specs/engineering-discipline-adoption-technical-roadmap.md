# Engineering Discipline Adoption Implementation Roadmap

**Fold Matt Pocock's MIT-licensed engineering skills into SpecKit Pro, phase by phase, with test-enforced attribution.**

This document defines the **SPEC catalog** for Engineering Discipline Adoption: an ordered set of specifications derived from the source PRD. Each SPEC corresponds 1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving traceability from PRD -> roadmap -> spec. Each specification is executed end-to-end through the SpecKit workflow (specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement) before moving to the next, and is prepared for autopilot with `/speckit-pro:speckit-scaffold-spec EDA-NNN`, which reads this roadmap as its input.

**Source PRD:** [../../prd-engineering-discipline-adoption.md](../../prd-engineering-discipline-adoption.md)
**Roadmap MOC:** [engineering-discipline-adoption-roadmap-MOC.md](engineering-discipline-adoption-roadmap-MOC.md)
**Spec ID prefix:** `EDA-###`
**Branch:** one branch per EDA spec
**Tracker:** N/A
**Upstream:** https://github.com/mattpocock/skills (MIT), pinned at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`; fork https://github.com/racecraft-lab/skills, tag `speckit-pro-baseline`

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Reviewability Contract](#reviewability-contract)
3. [Dependency Graph](#dependency-graph)
4. [Progress Tracking](#progress-tracking)
5. [Specification Sections](#specification-sections)
6. [Decomposition Principles](#decomposition-principles)
7. [Environment & Deployment Context](#environment--deployment-context)
8. [Disposition Summary](#disposition-summary)
9. [References](#references)

---

## Roadmap Overview

The feature is decomposed into **11 specifications** across **6 dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | EDA-001 | Attribution foundation: notice, ledger, test | Sequential |
| **2** | EDA-002, EDA-007, EDA-008, EDA-009 | Frontier-round grilling, diagnose skill, post-implementation discipline, context hygiene | Parallel possible |
| **3** | EDA-003, EDA-004 | ADRs and glossary; prototype skill | Parallel possible |
| **4** | EDA-005 | Deep-module planning and slicing | Sequential |
| **5** | EDA-006, EDA-010 | Seams-first TDD; architecture review skill | Parallel possible |
| **6** | EDA-011 | Adoption close-out | Sequential (depends on all above) |

**Execution Order:** EDA-001 first. Tier 2 specs need only the ledger and may run as a parallel stack. EDA-003 and EDA-004 follow EDA-002. EDA-005 follows EDA-003. EDA-006 and EDA-010 follow EDA-005. EDA-011 closes the roadmap.

**Dependency Constraints:**
- Every spec requires EDA-001: derivative content must land with its ledger row and credit block, which the attribution test enforces.
- EDA-003 requires EDA-002: inline ADR and glossary writes extend the round-based interview protocol.
- EDA-004 requires EDA-002: grill-me routes prototype-only questions from within a round.
- EDA-005 requires EDA-003: the deep-module vocabulary and seams-first plan prompt cite ADRs and glossary terms.
- EDA-006 requires EDA-005: TDD tests only at seams the plan agreed.
- EDA-010 requires EDA-003 and EDA-005: candidates leave as ADRs and are described in deep-module vocabulary.
- EDA-007, EDA-008, and EDA-009 are independent of each other and of EDA-002.
- EDA-011 requires every other spec: it resolves the last ledger rows and the Layer 2 inventory.

## Reviewability Contract

Every spec must fit a human review budget before setup and again before PR
creation. The size metric counts **production code only**: documentation,
tests, and config do not contribute to the reviewable-LOC count.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files. Touching more than one primary surface is also a warning, not a block.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless this roadmap records a typed exception pragma (below).
- A slice that adds only net-new files (no existing files modified) gets a 1.5x
  greenfield allowance on the production-LOC thresholds (warn 600, block 1200).
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- A block-sized slice may be allowed only by a typed, auditable exception
  pragma on its own line, exactly: `Reviewability-Exception: <class>` where
  `<class>` is one of `refactor`, `infra`, or `upgrade`. The match is
  line-anchored and case-sensitive with no trailing content; an unknown class,
  a mis-cased class, or free-form prose is not honored (fail-closed).
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

Projected LOC below comes from runner operation `estimate-spec-size` on 2026-09-25. EDA-004, EDA-007, and EDA-010 each returned `suggested_slices: 2` with status `ok`. Each sits above the 400-LOC warn line and below the 800-LOC block line; the warning is accepted and no split is planned. Re-check at Tasks.

---

## Dependency Graph

```text
EDA-001 (Attribution Foundation)
  ├──► EDA-002 (Frontier-Round Grilling)
  │      ├──► EDA-003 (Domain Model and ADRs)
  │      │      └──► EDA-005 (Deep-Module Planning and Slicing)
  │      │             ├──► EDA-006 (Seams-First TDD)
  │      │             └──► EDA-010 (Architecture Review Skill) ◄── EDA-003
  │      └──► EDA-004 (Prototype Skill)
  ├──► EDA-007 (Diagnose Skill)
  ├──► EDA-008 (Post-Implementation Discipline)
  └──► EDA-009 (Context Hygiene and Agent Writing)

EDA-001 .. EDA-010 ───► EDA-011 (Adoption Close-out)

Each accepted spec delivers its own observable outcome.
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| EDA-001 | Attribution Foundation | 🔄 In Progress | `docs/ai/specs/.process/EDA-001-workflow.md` | Specify |
| EDA-002 | Frontier-Round Grilling | ⏳ Pending | — | Blocked by EDA-001 |
| EDA-003 | Domain Model and ADRs | ⏳ Pending | — | Blocked by EDA-002 |
| EDA-004 | Prototype Skill | ⏳ Pending | — | Blocked by EDA-002 |
| EDA-005 | Deep-Module Planning and Slicing | ⏳ Pending | — | Blocked by EDA-003 |
| EDA-006 | Seams-First TDD | ⏳ Pending | — | Blocked by EDA-005 |
| EDA-007 | Diagnose Skill | ⏳ Pending | — | Blocked by EDA-001 |
| EDA-008 | Post-Implementation Discipline | ⏳ Pending | — | Blocked by EDA-001 |
| EDA-009 | Context Hygiene and Agent Writing | ⏳ Pending | — | Blocked by EDA-001 |
| EDA-010 | Architecture Review Skill | ⏳ Pending | — | Blocked by EDA-003, EDA-005 |
| EDA-011 | Adoption Close-out | ⏳ Pending | — | Blocked by EDA-001 through EDA-010 |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### EDA-001: Attribution Foundation

**Priority:** P1 | **Depends On:** None | **Enables:** every other EDA spec

**Goal:** Publish Matt Pocock's MIT notice and a 38-row disposition ledger in both payloads, enforced by a test, before any derivative content lands.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 285 |
Production files: 1 |
Total files: 4-6 |
Budget result: within budget

**Scope:**
- Record the fork `racecraft-lab/skills` and tag `speckit-pro-baseline` (already created on 2026-09-25) as the provenance anchor.
- Add `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`: MIT text verbatim with "Copyright (c) 2026 Matt Pocock", upstream URL, fork URL, pinned SHA, and a statement that the files it lists are modified derivatives.
- Add the disposition ledger (in the notice or a sibling file): 38 rows covering the plugin, in-progress, and misc buckets, each with upstream path, disposition (ABSORB, NEW, IGNORE), destination, status (`planned` or `landed`), and an IGNORE reason. All ABSORB and NEW rows start `planned`.
- Define the credit-block format for derivative files and the `metadata.credits` frontmatter shape for SKILL.md files, following Matt's own `pr/CREDITS.md` pattern.
- Add `tests/speckit-pro/unit/test-upstream-skill-attribution.py` and register it in `suite-manifest.json`: it checks MIT text against a frozen copy, every row's disposition and reason, and every `landed` destination's existence and credit block.
- Add an acknowledgement to `speckit-pro/README.md` linking the notice.
- Refresh release artifacts and confirm the notice appears in both `dist/` payloads.

**Out of Scope:**
- Any derivative content (EDA-002 onward).
- Edits in the fork.

**Key Decisions:**
**Notice location Decision (2026-09-25):** Place the notice under `speckit-pro/skills/` so both payload builders ship it without a `payloads.py` change, following the Quint notice precedent. Alternatives considered: a new top-level `speckit-pro/upstream/` directory, rejected because it needs payload-builder changes.
**Fork role Decision (2026-09-25):** The fork is a provenance anchor only. Alternatives considered: maintaining racecraft variants in the fork, rejected because it creates two places to keep in step.

**Module and Interface Deltas:**
- `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/`: new: MIT notice and disposition ledger
- `tests/speckit-pro/unit/test-upstream-skill-attribution.py`: new: enforces notice, ledger, and credit blocks

**Key Files:**
- `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`: notice and ledger
- `tests/speckit-pro/unit/test-upstream-skill-attribution.py`: attribution test
- `tests/speckit-pro/suite-manifest.json`: test registration
- `speckit-pro/README.md`: acknowledgement
- `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md`, `tests/speckit-pro/unit/test-artifact-gallery.py`: precedent to mirror

---

### EDA-002: Frontier-Round Grilling

**Priority:** P1 | **Depends On:** EDA-001 | **Enables:** EDA-003, EDA-004

**Goal:** grill-me asks dependency-aware rounds of up to four questions, looks up facts itself, and hands questions only an absent stakeholder can answer to an async questionnaire.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 202 |
Production files: 3 |
Total files: 6-8 |
Budget result: within budget

**Scope:**
- Rewrite the cadence in `skills/grill-me/references/interview-protocol.md`: map the design tree, ask each round as up to four independent questions whose prerequisites are settled, each with a recommended answer first; dependent questions wait. Keep the existing branches, wrap-up checkpoints, and forced synthesis limits.
- Add the rule from Matt's `grilling`: finding facts is the agent's job, deciding is the user's; look up code and document facts with read-only tools before asking.
- Adapt `to-questionnaire`: when only an absent stakeholder can answer, write `docs/ai/specs/.process/<SPEC-ID>-questionnaire-<slug>.md` (recipient, what is needed back, questions ordered by importance, answer stubs, a closing "anything else") and record the deferral in the Design Concept.
- Let autopilot's all-disagree consensus escalation emit the same questionnaire shape.
- Update the Codex mirror (`codex-skills/grill-me/SKILL.md`) with its question mechanism or a numbered round.
- Update tests that pin grill-me's one-question-per-turn wording; keep every existing assertion's intent.
- Add credit blocks and flip ledger rows for `grilling`, `grill-me`, and `to-questionnaire` to `landed`.

**Out of Scope:**
- Inline glossary and ADR writes (EDA-003).
- Prototype routing (EDA-004).

**Key Decisions:**
**Round size Decision (2026-09-25):** Up to four questions per round, matching one `AskUserQuestion` call. Alternatives considered: one question per turn (kept today, slower) and Matt's uncapped numbered frontier (rejected: no cap, harder to answer).

**Module and Interface Deltas:**
- `skills/grill-me` interview protocol (Claude and Codex): changed: rounds of up to four questions; stakeholder questionnaire output
- autopilot consensus human-review escalation: changed: can emit a questionnaire

**Key Files:**
- `speckit-pro/skills/grill-me/SKILL.md`, `speckit-pro/skills/grill-me/references/interview-protocol.md`, `speckit-pro/skills/grill-me/references/output-formats.md`
- `speckit-pro/codex-skills/grill-me/SKILL.md`
- `speckit-pro/skills/speckit-autopilot/references/` consensus escalation reference
- `tests/speckit-pro/layer1-structural/validate-skill-contracts.py`

---

### EDA-003: Domain Model and ADRs

**Priority:** P1 | **Depends On:** EDA-002 | **Enables:** EDA-005, EDA-010

**Goal:** SpecKit Pro projects keep a terms-only glossary with `Avoid` aliases and a `docs/adr/` decision log that grill-me writes inline and the consensus analysts read.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 250 |
Production files: 4 |
Total files: 8-10 |
Budget result: within budget

**Scope:**
- Define the ADR convention: `docs/adr/NNNN-slug.md`, created lazily, with Matt's three-gate test (hard to reverse, surprising without context, the result of a real trade-off) and a 1-3 sentence minimum format with optional status and options.
- Extend `ubiquitous-language`: `Avoid` aliases, a challenge mode (test a term against the glossary and the code, sharpen overloaded words, invent edge cases), and the rule that the document holds terms only.
- Extend grill-me (Claude and Codex) to write new or sharpened terms and qualifying ADRs as decisions land.
- Teach `spec-context-analyst` and `codebase-analyst` (Claude and Codex) to read `docs/adr/` and cite a conflicting ADR by number.
- Add credit blocks; flip `grill-with-docs` and `domain-modeling` rows to `landed`.

**Out of Scope:**
- Deep-module vocabulary (EDA-005).
- Migrating existing ad-hoc decision records in this repository.

**Key Decisions:**
**ADR home Decision (2026-09-25):** `docs/adr/NNNN-slug.md`, the ecosystem default. Alternatives considered: `docs/ai/decisions/` (rejected: less recognizable) and no ADRs (rejected: loses the durable record Matt's critique asks for).

**Module and Interface Deltas:**
- `docs/adr/NNNN-slug.md` convention: new: consumer projects gain an ADR home
- `skills/ubiquitous-language` document format: changed: adds `Avoid` aliases and challenge mode
- `spec-context-analyst`, `codebase-analyst` inputs: changed: read ADRs

**Key Files:**
- `speckit-pro/skills/ubiquitous-language/SKILL.md` and its Codex mirror
- `speckit-pro/skills/grill-me/references/interview-protocol.md`
- `speckit-pro/agents/spec-context-analyst.md`, `speckit-pro/agents/codebase-analyst.md`, and their `codex-agents/*.toml` twins
- `tests/speckit-pro/unit/fixtures/ubiquitous-language/`

---

### EDA-004: Prototype Skill

**Priority:** P1 | **Depends On:** EDA-002 | **Enables:** prototype evidence before Specify

**Goal:** Users answer a design question with throwaway code before `specify`, and the Design Concept records the prototype as evidence.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 580 |
Production files: 5 |
Total files: 12-15 |
Budget result: warning accepted (580 is above the 400 warn line and below the 800 block line; the slice also modifies existing files, so the greenfield allowance does not apply)

**Scope:**
- Add `speckit-prototype` (model-invoked) on Claude and Codex, adapted from Matt's `prototype`, `LOGIC.md`, and `UI.md`: a logic branch (one self-contained HTML file with a state panel, free-play controls, and guided walkthroughs over a pure logic module) and a UI branch (three to five structurally different variants behind a switcher).
- Mark prototype code throwaway; preserve it on `prototype/<name>`; add `Prototype evidence` to the Design Concept format.
- Route prototype-only questions from grill-me, `speckit-scaffold-spec`, and a coach routing row.
- Meet the new-skill contract: Codex mirror with `agents/openai.yaml` (implicit invocation allowed), policy-map entry, capability and grounding pointers, Codex Skill-Selection Guard, the four hard-coded skill lists, Layer 2 trigger files on both surfaces, README tables.
- Add credit blocks and `metadata.credits`; flip the `prototype` row to `landed`.

**Out of Scope:**
- Promoting prototype code to production (implement phase).
- Architecture-level spikes (EDA-010).

**Module and Interface Deltas:**
- `speckit-prototype` skill: new: model-invoked on both surfaces
- Design Concept format: changed: adds `Prototype evidence`

**Key Files:**
- `speckit-pro/skills/speckit-prototype/` (SKILL.md, `references/logic.md`, `references/ui.md`)
- `speckit-pro/codex-skills/speckit-prototype/` (SKILL.md, `agents/openai.yaml`)
- `speckit-pro/skills/grill-me/references/output-formats.md`
- `speckit-pro/skills/speckit-coach/SKILL.md`
- `tests/speckit-pro/layer2-trigger/evals/`, `tests/speckit-pro/layer2-trigger/codex-evals/`

---

### EDA-005: Deep-Module Planning and Slicing

**Priority:** P2 | **Depends On:** EDA-003 | **Enables:** EDA-006, EDA-010

**Goal:** Plan and Tasks describe changes in deep-module terms, pick test seams first, and slice work into tracer-bullet vertical slices.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 222 |
Production files: 4 |
Total files: 7-9 |
Budget result: within budget

**Scope:**
- Add a coach reference `deep-modules.md` adapted from `codebase-design`, `DEEPENING.md`, and `DESIGN-IT-TWICE.md`: module, interface, depth, seam, adapter, leverage, locality; the deletion test; "one adapter is a hypothetical seam, two is a real one"; design-it-twice with an opinionated recommendation.
- Update the Plan prompt: agree test seams first, prefer the highest existing seam; the spec records decisions already made (from `to-spec`).
- Use the vocabulary in Module and Interface Deltas guidance and in `codebase-analyst`.
- Extend `slicing-heuristics.md` and the Tasks prompt from `to-tickets`: tracer-bullet vertical slices sized to one context window, refactor first, expand then migrate then contract, explicit blocking edges.
- Extend the `speckit-prd` protocol with the fog-versus-spike test (from `wayfinder`) and one rejected-concept record per concept (from `triage`).
- Add credit blocks; flip `codebase-design`, `to-spec`, `to-tickets`, `wayfinder`, and `triage` rows to `landed`.

**Out of Scope:**
- TDD rules (EDA-006).
- Any issue-tracker publishing.

**Module and Interface Deltas:**
- coach deep-module reference; plan and tasks prompts; `slicing-heuristics.md`; `speckit-prd` protocol: changed: vocabulary, seams-first, slicing and fog rules

**Key Files:**
- `speckit-pro/skills/speckit-coach/references/deep-modules.md`, `speckit-pro/skills/speckit-coach/references/slicing-heuristics.md`
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and its Codex overlay
- `speckit-pro/skills/speckit-prd/references/prd-authoring-protocol.md`
- `speckit-pro/agents/codebase-analyst.md` and its Codex twin

---

### EDA-006: Seams-First TDD

**Priority:** P2 | **Depends On:** EDA-005 | **Enables:** review against agreed seams

**Goal:** Implement-phase tests exercise only the seams the plan agreed, never restate the implementation, and mock only at system boundaries.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 162 |
Production files: 3 |
Total files: 5-6 |
Budget result: within budget

**Scope:**
- Extend `tdd-protocol.md` from Matt's `tdd`, `tests.md`, and `mocking.md`: pre-agreed seams, the tautological-test ban (expected values from an independent source), implementation-coupled tests, horizontal slicing, mocks only at system boundaries with injected dependencies.
- Update `implement-executor` on Claude and Codex to carry the rules and report the seam each test exercises in its TDD evidence.
- Keep the existing RED-GREEN-REFACTOR contract.
- Add credit blocks; flip the `tdd` row to `landed`.

**Out of Scope:**
- A standalone TDD skill.
- Changing autopilot's refactor step.

**Module and Interface Deltas:**
- `tdd-protocol.md`; `implement-executor` (Claude and Codex): changed: seam, tautology, and mocking rules; seam in evidence

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md`
- `speckit-pro/agents/implement-executor.md`, `speckit-pro/codex-agents/implement-executor.toml`

---

### EDA-007: Diagnose Skill

**Priority:** P1 | **Depends On:** EDA-001 | **Enables:** disciplined recovery from red tests and CI failures

**Goal:** A gated diagnosis loop exists for hard bugs and regressions, and autopilot and resolve-pr route failures to it.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 580 |
Production files: 5 |
Total files: 12-15 |
Budget result: warning accepted (580 is above the 400 warn line and below the 800 block line; the slice also modifies existing files, so the greenfield allowance does not apply)

**Scope:**
- Add `speckit-diagnose` (model-invoked) on Claude and Codex, adapted from `diagnosing-bugs`: six gated phases; the feedback-loop ladder; "no red-capable command, no Phase 2"; minimise until every element is load-bearing; three to five ranked falsifiable hypotheses shown before testing; one variable at a time; tagged debug instrumentation with a cleanup proof; regression test at a correct seam, or a finding that none exists; redaction of secrets.
- Replace `hitl-loop.template.sh` with prose (or a Python stdlib helper if Plan justifies one); ship no shell.
- Route autopilot error recovery and `speckit-resolve-pr` CI failures to `speckit-diagnose`.
- Meet the new-skill contract (as EDA-004), with implicit invocation allowed.
- Add credit blocks and `metadata.credits`; flip the `diagnosing-bugs` row to `landed`.

**Out of Scope:**
- Performance profiling tooling.
- Changing CI.

**Module and Interface Deltas:**
- `speckit-diagnose` skill: new: model-invoked on both surfaces
- autopilot error recovery; `speckit-resolve-pr`: changed: route to diagnose

**Key Files:**
- `speckit-pro/skills/speckit-diagnose/`, `speckit-pro/codex-skills/speckit-diagnose/`
- `speckit-pro/skills/speckit-autopilot/references/error-recovery.md`
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` and its Codex mirror
- `tests/speckit-pro/layer2-trigger/evals/`, `tests/speckit-pro/layer2-trigger/codex-evals/`

---

### EDA-008: Post-Implementation Discipline

**Priority:** P2 | **Depends On:** EDA-001 | **Enables:** sharper review packets

**Goal:** Review splits into Standards and Spec axes, PR bodies show the change and its risk at a glance, merges resolve by intent, and retrospectives turn mechanical violations into checks.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 270 |
Production files: 5 |
Total files: 8-10 |
Budget result: within budget

**Scope:**
- Split the post-implementation Code Review step (from `code-review`): parallel Standards (repository standards plus a smell baseline the repository overrides) and Spec (missing, scope creep, wrong) reviews, each citing rule or spec line and hunk, reported side by side.
- Extend the draft-PR body (from `pr`, crediting Dex Horthy's `show-me`): smallest-view summary, before-and-after evidence, merge danger (one-way or two-way door, blast radius), inside the existing H1 and fingerprint contract.
- Add a merge-conflict reference (from `resolving-merge-conflicts`): trace each side's intent to its primary source, keep both where possible, never abort, never invent behavior, run checks, and regenerate generated paths instead of hand-resolving; cite it from autopilot main sync and `speckit-resolve-pr`.
- Extend the retrospective step (from `retro`): each mechanical violation becomes a candidate lint rule, hook, or CI check; a missing guardrail is a finding.
- Add credit blocks; flip `code-review`, `pr`, `resolving-merge-conflicts`, and `retro` rows to `landed`.

**Out of Scope:**
- A standalone review skill (name collision with the built-in `/code-review`).
- Changing Copilot review loops.

**Module and Interface Deltas:**
- post-implementation Code Review step: changed: two parallel review axes
- draft-PR body sections: changed: summary view, evidence, merge danger
- autopilot merge-conflict reference: new: used by main sync and resolve-pr

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` and its Codex overlay
- `speckit-pro/skills/speckit-autopilot/references/merge-conflicts.md`
- the PR-body producer and its tests under `tests/speckit-pro/unit/fixtures/pr-packet/`
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md`

---

### EDA-009: Context Hygiene and Agent Writing

**Priority:** P3 | **Depends On:** EDA-001 | **Enables:** cleaner phase boundaries

**Goal:** Users and autopilot choose the right move at each phase boundary, and agent-facing documents follow the writing-for-agents rules.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 255 |
Production files: 4 |
Total files: 8-10 |
Budget result: within budget

**Scope:**
- Add a context-hygiene reference (from `ask-matt` PHASE-BOUNDARIES and `handoff`): continue, clear, hand off, delegate, compact, in that order; every move except continue turns a primary source into a lossy secondary one. Cite it from coach and autopilot.
- Add a read-only handoff brief to `speckit-status`: artifact paths, current phase, suggested next command, and no copies of spec content.
- Apply `writing-for-agents` to the coach constitution guide and the repository `.claude/skills/scaffold-skill` helper.
- Add worked examples to the quality-gates guide (from `setup-ts-deep-modules` and `setup-pre-commit`), framed as project choices.
- Add the owning-source rule to `grounding.md` (from `research`).
- Add credit blocks; flip `ask-matt` (phase boundaries), `handoff`, `writing-for-agents`, `setup-ts-deep-modules`, `setup-pre-commit`, and `research` rows to `landed`.

**Out of Scope:**
- A handoff skill.
- Installing tools in consumer projects.

**Module and Interface Deltas:**
- coach and autopilot context-hygiene reference: new: phase-boundary moves
- `speckit-status` output: changed: optional handoff brief

**Key Files:**
- `speckit-pro/skills/speckit-coach/references/context-hygiene.md`
- `speckit-pro/skills/speckit-status/SKILL.md` and its Codex mirror
- `speckit-pro/skills/speckit-coach/references/constitution-guide.md`, `speckit-pro/skills/speckit-coach/references/quality-gates-guide.md`
- `speckit-pro/skills/speckit-autopilot/references/grounding.md`
- `.claude/skills/scaffold-skill/SKILL.md`

---

### EDA-010: Architecture Review Skill

**Priority:** P2 | **Depends On:** EDA-003, EDA-005 | **Enables:** refactor specs from evidence

**Goal:** Users survey a codebase for deepening opportunities, get a visual report, and turn the chosen candidate into a roadmap entry or an ADR.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 635 |
Production files: 5 |
Total files: 12-15 |
Budget result: warning accepted (635 is above the 400 warn line and below the 800 block line; the slice also modifies existing files, so the greenfield allowance does not apply)

**Scope:**
- Add `speckit-architecture-review` (user-invoked: `disable-model-invocation: true`, `allow_implicit_invocation: false`) on Claude and Codex, adapted from `improve-codebase-architecture` and `HTML-REPORT.md`.
- Scope first (user direction, else recent change hot spots); survey with the read-only `codebase-analyst`; apply the deletion test; never edit code; propose no interfaces before the user picks a candidate.
- Write a self-contained HTML report with inline SVG (no CDN): candidate cards (files, problem, solution, benefits in locality and leverage, before-and-after diagram, strength rating) and a top recommendation.
- Grill the chosen candidate with the interview protocol; output a roadmap entry proposal for `speckit-prd` or an ADR.
- Meet the new-skill contract; add a coach routing row.
- Add credit blocks and `metadata.credits`; flip the `improve-codebase-architecture` row to `landed`.

**Out of Scope:**
- Rendering the architecture viewer (ART-021).
- Applying refactors.

**Module and Interface Deltas:**
- `speckit-architecture-review` skill: new: user-invoked on both surfaces

**Key Files:**
- `speckit-pro/skills/speckit-architecture-review/`, `speckit-pro/codex-skills/speckit-architecture-review/`
- `speckit-pro/skills/speckit-coach/SKILL.md`
- `docs/ai/specs/architecture-viewer-contract.md` (read for overlap)
- `tests/speckit-pro/layer2-trigger/evals/`, `tests/speckit-pro/layer2-trigger/codex-evals/`

---

### EDA-011: Adoption Close-out

**Priority:** P3 | **Depends On:** EDA-001 through EDA-010 | **Enables:** a qualified trigger campaign that includes the new skills

**Goal:** Every ledger row is resolved, the new skills join the qualified Layer 2 inventory, and generated docs list them.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 175 |
Production files: 2 |
Total files: 6-8 |
Budget result: within budget

**Scope:**
- Verify every ledger row is `landed` or IGNORE with a reason; the attribution test passes.
- Amend the Layer 2 case inventory to include the three new trigger corpora under the qualification protocol, with the `mattpocock-skills` plugin disabled during measurement.
- Regenerate docs reference pages; confirm README skill tables.

**Out of Scope:**
- New dispositions for upstream skills published after the pinned commit.

**Module and Interface Deltas:**
- Layer 2 trigger inventory: changed: three new corpora

**Key Files:**
- `tests/speckit-pro/lib/trigger_inventory.py`, `tests/speckit-pro/test-trigger-inventory.py`, the case inventory JSON
- `tests/speckit-pro/layer2-trigger/qualification-protocol.md`
- `docs-site/src/content/docs/reference/**` (generated)

---

## Decomposition Principles

When breaking a feature into specs:

1. **Each spec is independently executable** through the full SpecKit workflow (specify -> implement)
2. **Minimize cross-spec dependencies**: prefer sequential over deeply nested
3. **Vertical slices first**: each spec delivers an observable outcome through
   every layer it needs; do not split backend, UI, or integration into separate
   specs merely by technical layer.
4. **Shared enablers only when justified**: an enabling spec must have its own
   independently observable contract; otherwise include the enabling work in the
   first slice that needs it.
5. **Cross-slice work earns its own spec**: do not reserve a final
   integration-only spec unless it delivers a separately valuable outcome.
6. **Each spec gets its own directory**: `specs/<number>-<name>/`

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| Upstream source | `mattpocock/skills` at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` (plugin version 1.2.3) |
| Provenance fork | `racecraft-lab/skills`, tag `speckit-pro-baseline` |
| Attribution precedent | `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md` and `tests/speckit-pro/unit/test-artifact-gallery.py` |
| Research access | research broker (`research_search`, `docs_query`) |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| Three new skills | `speckit-pro/skills/`, `speckit-pro/codex-skills/` | prototype, diagnose, architecture review |
| Skill lists | `validate-skill-contracts.py`, `validate-plugin-metadata.py` | add the three skills |
| Payloads | `dist/` | refreshed with `python3 scripts/refresh-release-artifacts.py` |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| Upstream skill text | Read the pinned tag in `racecraft-lab/skills` |
| Layer 2 runs | Disable the `mattpocock-skills` plugin first; its trigger phrases collide |
| Docs checks | `pnpm --dir docs-site install --frozen-lockfile` in a fresh worktree |

---

## Disposition Summary

EDA-001 records the authoritative 38-row ledger. Summary:

| Disposition | Upstream skills | Spec |
|---|---|---|
| ABSORB | grilling, grill-me, to-questionnaire | EDA-002 |
| ABSORB | grill-with-docs, domain-modeling | EDA-003 |
| NEW | prototype | EDA-004 |
| ABSORB | codebase-design, to-spec, to-tickets, wayfinder (fog test), triage (rejected-concept records) | EDA-005 |
| ABSORB | tdd | EDA-006 |
| NEW | diagnosing-bugs | EDA-007 |
| ABSORB | code-review, pr, resolving-merge-conflicts, retro | EDA-008 |
| ABSORB | ask-matt (phase boundaries), handoff, writing-for-agents, setup-ts-deep-modules, setup-pre-commit, research | EDA-009 |
| NEW | improve-codebase-architecture | EDA-010 |
| IGNORE | setup-matt-pocock-skills, implement, implement-spec, wizard, git-guardrails-claude-code, claude-handoff, teach, wait-what, loop-me, writing-beats, writing-fragments, writing-shape, migrate-to-shoehorn, scaffold-exercises | EDA-001 (reasons) |

`ask-matt`, `wayfinder`, and `triage` are absorbed only in part; their tracker workflow parts are recorded as not ported.

## References

- **Source PRD:** [../../prd-engineering-discipline-adoption.md](../../prd-engineering-discipline-adoption.md): the SPEC catalog above is derived from its Features / Acceptance Criteria
- **PRD Template:** `prd-template.md` (same `templates/` directory); author with `/speckit-pro:speckit-prd`
- **Constitution:** `.specify/memory/constitution.md`
- **Project Standards:** `AGENTS.md`, `speckit-pro/AGENTS.md`, `tests/speckit-pro/AGENTS.md`
- **Upstream:** https://github.com/mattpocock/skills, https://github.com/racecraft-lab/skills

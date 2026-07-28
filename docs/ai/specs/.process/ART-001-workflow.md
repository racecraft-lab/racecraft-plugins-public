# SpecKit Workflow: ART-001 — Artifact Brand Kit & Gallery Foundation

**Template Version**: 1.0.0
**Created**: 2026-07-28
**Purpose**: Phase prompts for executing the ART-001 SpecKit workflow via `/speckit-pro:speckit-autopilot`.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/ART-001-design-concept.md
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
| Specify | `/speckit-specify` | ✅ Complete | G1 pass — 14 FR, 9 SC, 3 user stories, 0 markers |
| Clarify | `/speckit-clarify` | ✅ Complete | G2 pass — 11 questions resolved, 5 via consensus; spec 14 → 20 FR |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass — 6 artifacts; budget rationale replaced, honest size ~1,285 lines |
| Checklist | `/speckit-checklist` | 🔄 In Progress | accessibility, data-integrity, security |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Python 3.11+ stdlib only | The Layer 4 test uses no third-party imports | Review imports in `tests/speckit-pro/unit/test-artifact-gallery.py` |
| No new Bash/`jq` surface | Gallery assets and test add no shell tooling | Review diff for `.sh` files / `jq` calls |
| Test-First (TDD) | Red → Green → Refactor per task | TDD evidence per implement task |
| KISS / YAGNI | No trigger DSL, no sync script, no build step (design concept Q2/Q4) | Plan review against design concept Non-goals |
| Generated-artifact contract | Shipped bytes under `speckit-pro/` require payload/proof regeneration | Payload regen accounted before completion |

**Constitution Check:** ✅ **PASS** (G0, 2026-07-28)

### Phase 0 Record (pre-flight)

**G0 baseline — `python3 tests/speckit-pro/run-all.py`: 4240/4240 passed**
(L1 1428/1428, L4 2626/2626, L5 186/186; toolchain preflight ok).

| Constitution principle | Quality gate | Result |
|---|---|---|
| I. Plugin Structure Compliance | Layer 1 | ✅ 1428/1428 |
| II. Cross-Platform Runtime & Script Safety | Layer 4 | ✅ 2626/2626 (`test-repo-bash-confinement` 121/121) |
| III. Semantic Versioning | Layer 1 `validate-plugin` | ✅ included in L1 |
| IV. Test Coverage Before Merge | full default suite | ✅ 4240/4240 |
| V. Conventional Commits | CI `validate-pr-title` | ⏳ deferred to PR boundary (`validate-pr-workflow-contract`) |
| VI. KISS / YAGNI | plan review | ⏳ deferred to Phase 3 (G3) |

**Environment**

| Fact | Value |
|---|---|
| Python | 3.11.0 |
| SpecKit CLI | specify 0.11.8 |
| Branch / worktree | `art-001-brand-kit-gallery-foundation` / worktree = true |
| Feature dir | pinned via `.specify/feature.json` (gitignored) to `specs/art-001-brand-kit-gallery-foundation` |
| `ON_FEATURE_BRANCH` | **true** (asserted by orchestrator; the upstream `^[0-9]{3}-` regex does not match this repo's namespaced spec IDs, so `check-prerequisites` reports `on_feature_branch: false` — the branch is real and `feature.json` is the sanctioned resolution path) |
| `PRESET_CONVENTIONS` | `speckit-pro-reviewability` v1.0.0 — spec/plan/tasks templates all resolve; spec adds mandatory Reviewability Budget + PR Review Packet Requirements, plan adds Declared File Operations |
| `PROJECT_COMMANDS` | `detect-commands` returns `stack: unknown` (no JS/py package manifest at root). Repo-real: UNIT_TEST `run-all.py --layer 4`; STRUCTURAL `--layer 1`; FULL_VERIFY `run-all.py`; no BUILD/TYPECHECK/LINT surface |
| `PROJECT_IMPLEMENTATION_AGENT` | none — `.claude/agents/` holds only `plugin-release-auditor` and `speckit-skill-reviewer` (both review-only). Implementation routes to `speckit-pro:implement-executor` |
| `AGENT_TEAMS_AVAILABLE` | **false** — no `TeamCreate` in the session surface. `[P]` runs dispatch as batched subagents in one message |
| `CONFIDENCE_GATE_MODE` | `advisory` (resolver default; no `--strict`/`--advisory` flag, no local config) |
| Local settings | `.claude/speckit-pro.local.md` absent — defaults (`gate-failure: stop`) |

**Capability inventory (Step 0.7).** Codebase context: Read/Grep/Glob, `gitnexus`
(code graph), `RepoPromptCE` (file_search, get_code_structure). Web + domain
research: `WebSearch`, `WebFetch`, `tavily` (search/extract/crawl/research).
Notes vault: `qmd`. **No Context7 in this session** — library-documentation
questions fall back to Tavily + WebFetch, which is an acceptable evidence path,
so no escalation.

**Archive sweep.** Nothing eligible. `specs/` holds only the current target
(excluded by contract); CAR-003 and G56R-003 were swept 2026-07-27 (reports under
`.specify/memory/archive-reports/`).

**Tier-2 legacy relocation.** No eligible candidate — the only spec directory is
the current target. `relocate-process-artifacts` remains deferred and was not
invoked.

**Hook decisions (`.specify/extensions.yml`, all 8 events reviewed).**

| Hook | Decision | Why |
|---|---|---|
| `before_specify` → `speckit.git.feature` (`optional: false`) | **SKIP** | Destructive here: it creates a feature branch, but the branch already exists and is checked out in this worktree. Its purpose is already satisfied. |
| `before_specify` → `speckit.archive.run` | **SKIP** | Duplicates the archive-sweep step above; nothing eligible. |
| `before_*` → `speckit.git.commit` (clarify/plan/tasks/checklist/analyze/implement) | **SKIP** | Duplicates the autopilot's own per-phase checkpoint commits. |
| `after_specify` → `speckit.speckit-utils.doctor` | **ACCEPT** | Read-only diagnostic; run at Phase 0. |
| `after_plan` → `speckit.speckit-utils.validate` | **ACCEPT** | Read-only validation. |
| `after_implement` → `verify.run`, `verify-tasks.run`, `retrospective.analyze` | **ACCEPT** | Mapped to the Post-Implementation task list. |
| `after_*` → `speckit.git.commit` | **SKIP** | Same duplication as `before_*`. |

**Doctor health check (`speckit.speckit-utils.doctor`, after G0): 4 PASS, 1 WARN, 0 FAIL.**
Templates 5/5, Agent Config PASS, Python Runner PASS, Constitution PASS (996 words).
The single WARN is expected and self-clearing:
`art-001-brand-kit-gallery-foundation: spec ✗ plan ✗ tasks ✗ WARN (needs /speckit.specify)`
— Phase 1 was already in flight when the check ran. No remediation.
Note: the doctor's Agent Config check looks for `.claude/commands/speckit.*.md`; this
project is on the v0.8.13+ skills migration (`ai_skills: true`, 27 `speckit-*` entries
under `.claude/skills/`), so the literal path check is a false negative, not a gap.

**Deferred runner operations (recorded, not invoked).** `reviewability-gate`
tasks/pre-PR modes, `generate-uat-skeleton`, `final-reviewability-backstop`,
`relocate-process-artifacts`, `restack`, `install-codex-agents`,
`ensure-reviewability-preset`.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-001 |
| **Name** | Artifact Brand Kit & Gallery Foundation |
| **Branch** | `art-001-brand-kit-gallery-foundation` |
| **Dependencies** | None |
| **Enables** | ART-002…005 (template ports), ART-009 (UAT walkthrough) |
| **Priority** | P1 |

### Reviewability Budget (recorded at scaffold, gate disposition)

Setup gate returned `warn` scanning the whole 13-spec roadmap (`primary
surfaces 3` is cross-spec noise). ART-001's own entry: 1 primary surface
(seed/config), 285 projected LOC at roadmap time. Post-interview estimator:
435 LOC (`warn`, suggested_slices 2) — **split declined in design concept Q9**
under the PRD's 1.5× greenfield allowance for net-new-only slices (warn 600).
One thin vertical slice: tokens → manifest → test.

### Provenance Inputs (captured at Phase 0 — pin these, do not re-derive)

The brand-kit provenance header and `brand-voice.md` attribution cite the private
repo by name + commit SHA + date only. No prose is copied across the boundary.

| Source | Pin |
|---|---|
| `racecraft-lab/racecraft` `docs/brand/` (`color-system.md`, `typography-system.md`) | `30237cceaeb398e9fc08d8570714f24ff661c867` (2026-07-04) |
| `racecraft-lab/racecraft` `.claude/rules/content.md` (voice source for `brand-voice.md`) | `30237cceaeb398e9fc08d8570714f24ff661c867` (2026-07-04) |
| Local token source (public, quotable) | `docs-site/src/styles/brand.css` |

### Success Criteria Summary

- [ ] `speckit-pro/artifact-gallery/` ships `brand-kit.css`, `brand-voice.md`, `manifest.json`, `SPA-CONTRACT.md`, `theme-toggle.html`
- [ ] `manifest.json` seeds all ~21 template rows with `status: planned` and closed-signal-tag triggers
- [ ] `tests/speckit-pro/unit/test-artifact-gallery.py` (dash-named) validates manifest shape, trigger vocabulary, marker-block byte-equality, and forbidden external resource loads — registered in `tests/speckit-pro/suite-manifest.json`
- [ ] Brand kit renders AA-compliant in both themes over `file://`; dark mode = system default + `data-theme` toggle
- [ ] Layer 1 structural suite passes; payload/proof regeneration accounted

---

## Phase 1: Specify

**When to run:** At the start. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/art-001-brand-kit-gallery-foundation/spec.md`

### Specify Prompt

```text
/speckit-specify

## Feature: Artifact Brand Kit & Gallery Foundation

### Problem Statement
SpecKit-Pro is adding a gallery of ~21 branded, single-file HTML artifact
templates (draft-PR review artifacts, final-PR explainers, a UAT walkthrough,
and ad-hoc templates). Nothing exists yet that those templates can share:
no brand tokens, no routing manifest, no single-file-SPA contract, and no
automated enforcement. ART-001 ships that platform-neutral foundation so the
template port specs (ART-002…005) become mechanical and the workflow specs
(ART-007/009/010) can route against a complete catalog.

### Users
- Template port authors (ART-002…005) who embed the brand kit and flip manifest rows.
- The artifact-author and uat-artifact-author agents (ART-007/009/010) that read
  the manifest to decide which artifacts to generate.
- SpecKit-Pro operators who open generated artifacts locally over file:// and
  review them in either OS theme.

### User Stories
1. As a template author, I embed one canonical BRAND-KIT:START/END CSS block and
   one THEME-TOGGLE:START/END snippet verbatim, and a repo test tells me
   deterministically if my copy drifted (design concept Q4, Q8).
2. As a routing consumer, I read manifest.json and get every template's id,
   category, title, when-to-use, stage (draft-pr|final-pr|ad-hoc), closed-signal
   trigger, source attribution, and status (planned|shipped) — all ~21 rows
   seeded now, ports flip status later (Q1, Q2).
3. As an operator, I open any gallery artifact over file:// and it renders with
   Racecraft branding, honors my OS theme, lets me toggle themes (persisted via
   localStorage where available), and loads nothing external except Google
   Fonts (Q3, Q5).

### Constraints
- 70-20-10 Racecraft palette: warm-neutral scale #F7F6F4…#E0DED9, brand red
  #dc143c punctuation-only, brand blue #3c89c6 accents, GTO90 dark-mode set.
- Typography: Space Grotesk headings / Geist body / Fira Code mono via Google
  Fonts <link> + font-display: swap + system fallbacks. fonts.googleapis.com and
  fonts.gstatic.com are the ONLY permitted external references, and only in
  resource-load positions.
- WCAG AA contrast audited independently per theme; focus-ring and
  reduced-motion rules included.
- Provenance header cites racecraft-lab/racecraft docs/brand/* by repo name +
  commit SHA + date only (private repo — no prose copied); also cites
  docs-site/src/styles/brand.css. Cross-repo drift = pinned provenance +
  manual re-sync, no automated check (Q6).
- brand-voice.md distills ONLY the artifact-relevant subset of racecraft
  .claude/rules/content.md: voice & tone, banned/preferred vocabulary,
  answer-first TL;DR structure, CTA/button rules (Q7). No Schema.org, FAQ
  minimums, or nav chrome.
- Repo test is Python 3.11+ stdlib, dash-named
  (tests/speckit-pro/unit/test-artifact-gallery.py), registered in
  tests/speckit-pro/suite-manifest.json.
- speckit-pro/artifact-gallery/ is shipped plugin payload: the generated
  artifact contract (payload/proof regeneration) applies.

### Out of Scope
- Any actual template port (ART-002…005) — ports are row-flips + embeds.
- Workflow wiring (ART-006…011).
- A trigger-expression DSL or evaluator; prose-only routing (Q2).
- Automated cross-repo drift checks or a docs-site palette overlap test (Q6).
- A stdlib sync script or build step for marker blocks (Q4).
- Banning navigation anchors or text/comment URLs (Q3).
- Embedded woff2 fonts (roadmap key decision).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 14 (FR-001…FR-014) |
| User Stories | 3 (P1 marker-block adoption, P2 catalog routing, P3 local render + theme) |
| Acceptance Criteria | 29 Given/When/Then scenarios |
| Success Criteria | 9 (SC-001…SC-009) |
| `[NEEDS CLARIFICATION]` markers | 0 |

**Gate G1: ✅ PASS** — `validate-gate` returned
`{"gate":"G1","markers":0,"pass":true,"reason":"spec.md exists with 0 markers"}`.

**Executor note.** The Phase 1 subagent terminated on an API connection error
while composing its closing summary, *after* writing and self-validating both
artifacts. The orchestrator verified the output directly rather than re-running:
all mandatory preset sections present (Reviewability Notes / Budget / PR Review
Packet Requirements), quality checklist fully ticked with a recorded
fix-iteration note, zero absolute-path leaks. No re-run was needed.

**Clarify is NOT skipped.** The generic rule ("Clarify only runs if G1 found
markers") does not apply here. The executor deliberately routed the design
concept's two open questions into `## Assumptions` as explicit deferrals instead
of emitting markers, because both have recorded recommendations. Those two
deferrals are exactly what the workflow's two seeded Clarify sessions exist to
close, and they are load-bearing for the catalog rows — so Phase 2 runs.

### Files Generated

- [x] `specs/art-001-brand-kit-gallery-foundation/spec.md`
- [x] `specs/art-001-brand-kit-gallery-foundation/checklists/requirements.md`

### SpecKit Traceability Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] Author embeds marker block` |
| `[FR-001]` | Functional requirement | `[FR-001] Manifest seeds all template rows` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Signal vocabulary [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers dark-theme contrast audit` |

---

## Phase 2: Clarify (Optional but Recommended)

**When to run:** After Specify. The design concept left exactly two open
questions — both are seeded below. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Trigger Signal Vocabulary

```text
/speckit-clarify Focus on the closed signal vocabulary for manifest triggers:
derive the signal set (e.g. ui_change, schema_change, api_change, incident, …)
from the ~21 templates' when-to-use semantics in one pass; confirm every seeded
row's trigger uses only vocabulary signals; confirm how "always" rows interact
with stage filtering (draft-pr | final-pr | ad-hoc). Design concept Q2 fixed the
MECHANISM (closed tags, no DSL) — only the vocabulary CONTENT is open.
```

#### Session 2: Manifest Field Shape

```text
/speckit-clarify Focus on field-level manifest shape: exact key names, the
schema_version field, the category enum, the status enum (planned | shipped),
and where the shape is documented — recommendation from the design concept:
a "Manifest" section in SPA-CONTRACT.md (JSON has no comments), enforced by the
Layer 4 test; no formal JSON Schema document (stdlib can't validate one anyway).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Signal vocabulary | 5 asked, 5 resolved (3 via consensus) | 5-signal closed vocabulary; 2 trigger forms with non-empty rule; stage filters before triggers; vocabulary declared in the catalog with a cardinality oracle in the test. Spec gained FR-015/016/017 + a Clarifications section |
| 2 | Manifest shape | 6 asked, 6 resolved (2 via consensus) | 8 `snake_case` per-entry keys with no stored path; 9-member category enum from the upstream taxonomy; `source` as an origin-discriminated object; top level `{schema_version, signals, templates}`; `schema_version: "1.0"`. Spec gained FR-018/019/020 |

**Gate G2: ✅ PASS** — both seeded sessions run, both design-concept Open Questions
closed, 0 `[NEEDS CLARIFICATION]` markers, spec at 20 FRs.

### Seeded catalog (recorded here because no other artifact carries the full mapping)

| stage | entries | trigger |
|---|---|---|
| `draft-pr` | `implementation-plan`, `spec-explainer` | always |
| `draft-pr` | `code-approaches` | `competing_approaches` |
| `draft-pr` | `module-map` | `brownfield_change` |
| `final-pr` | `pr-writeup`, `uat-walkthrough` | always |
| `final-pr` | `annotated-diff` | `self_review_findings` or `large_diff` |
| `final-pr` | `flowchart` | `operational_flow_change` |
| `ad-hoc` | the other 13 | always (suppressed by the stage filter) |

Categories: `exploration-planning` (implementation-plan, code-approaches,
visual-designs) · `code-review` (module-map, pr-writeup, annotated-diff) · `design`
(design-system, component-variants) · `prototyping` (animation-prototype,
interaction-prototype) · `diagrams` (flowchart, svg-illustrations) · `decks`
(slide-deck) · `research` (spec-explainer, concept-explainer) · `reports`
(status-report, incident-report) · `editors` (triage-board, feature-flags,
prompt-tuner, uat-walkthrough).

### Consensus Resolution Log

| # | Type | Question | Categories | Round | Outcome | Resolution | Analysts Used |
|---|---|---|---|---|---|---|---|
| 1 | Clarify | Vocabulary size — 5 consumer-grounded signals vs the broader set the seeded prompt named | `[codebase, spec]` | 1 | both-agree | **Exactly 5.** Both analysts independently rejected headroom. Applied to FR-015 with two corrections to the executor's evidence (below). | codebase-analyst, spec-context-analyst |
| 2 | Clarify | Is a third `on_request` trigger form an acceptable widening of design-concept Q2? | `[spec]` | 1 | high-confidence | **No — two forms, non-empty signal set required.** The non-empty rule supplies all the safety the third form was proposed to buy, without contradicting the recorded operator decision. Applied to FR-008. | spec-context-analyst |
| 3 | Clarify | Does the vocabulary live as data in the catalog or as a constant in the Layer 4 test? | `[codebase, spec]` | 1→2 | escape-hatch → 2/3 | **Catalog is the authority; test asserts cardinality, not a copied list.** Applied to FR-017 + FR-010. | codebase-analyst, spec-context-analyst (R1) + domain-researcher (R2) |

**Item 1 — evidence corrected before acceptance.** Both analysts agreed on the
answer, but the codebase analyst disproved two of the executor's supporting claims:
(a) the producer for `competing_approaches` is the design concept's
`**Alternatives offered:**` block, **not** plan.md `## Complexity Tracking`, which is
gated on constitution violations and would be empty for a spec with competing designs
and no violations; (b) excluding `ui_change`/`schema_change`/`api_change` for "no
producer" is inconsistent, since all three are grounded in the same declared
primary-surface field that grounds `operational_flow_change`. The spec therefore
records the **consumer** test as the membership rule. Per both analysts,
`operational_flow_change` was **not** reworded — signal evaluation is agent judgment
for every member by design and belongs to ART-010.

**Item 2 — cross-item conflict resolved by the orchestrator.** The item-1 and item-2
spec-context analysts disagreed on whether ad-hoc entries carry narrowing signals
(which would have grown the vocabulary past five). Resolved in favor of five on a
point neither made: `when_to_use` is already a required field on every entry, so
human narrowing across the ad-hoc set is already served; machine-readable narrowing
signals no machine reads would duplicate it, and under the CAR precedent those
members would be permanent because removals are forbidden. Recorded in Assumptions so
a reviewer can contest it directly.

**Item 3 — Round 2 overturned Round 1's precedent, verified independently.** The two
Round 1 analysts each found a fact disqualifying the other's answer (payload boundary
vs. self-reference hole), so this escaped to a full fan-out. The domain-researcher
rejected the orchestrator's proposed three-site reconciliation and produced a better
answer, resting on two claims the orchestrator then **verified directly** rather than
accepting:
- `tests/speckit-pro/unit/test-analysis-decision-ladder.py:65` resolves `CONTRACT_ROOT`
  to `tests/speckit-pro/layer6-efficiency/contracts-claude`, and its constant lives at
  `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` — **both
  repo-only**. The precedent cited for a payload-crossing drift guard never crosses the
  payload boundary. **Confirmed.**
- "Zero shipped data files carry inline vocabularies" is **false**: 12 shipped contract
  JSON files under `speckit-pro/skills/speckit-autopilot/contracts/` declare `enum`s,
  and `routing-decision.schema.json` declares a **14-member signal enum inline**
  (plus route 5, hints 4, warnings 2) with no duplicated constant. **Confirmed.**

The deciding argument: consumer-driven contract testing presumes independently
deployable parties, and a repo-only test that ships nowhere cannot skew from the
catalog it validates. A duplicated list would be a change-detector tax on every
legitimate vocabulary edit while leaving the hole open to a single two-file commit.
The cardinality assertion is spec-derived — an oracle independent of the data it
checks — and closes the typo case in both directions.

| 4 | Clarify | Upstream templates are MIT-licensed; no requirement states an attribution obligation for the 20 ports | `[domain]` + `[codebase]` | 1 | both-agree | **New FR-020** — per-artifact attribution header plus one verbatim notice file in the gallery. | domain-researcher, codebase-analyst |
| 5 | Clarify | What category does the one repository-authored entry take? | `[spec, domain]` | 1 | high-confidence | **`editors`** — no tenth member minted. | spec-context-analyst |

**Item 4 — the finding that changed the most.** The executor surfaced that the 20
ported templates come from an MIT-licensed upstream ("Copyright (c) 2026 Anthropic
PBC") and that **no requirement anywhere states an attribution obligation for them**:
FR-012's provenance header is scoped to *brand* sources only, and the sole
template-level obligation was an unstructured catalog field. Both analysts confirmed
the gap. Two facts decided the shape:

- **The upstream template files carry no per-file notice** — verified by downloading
  one and grepping it. The notice exists only in the upstream repo-root `LICENSE`. So
  a template lifted out of that repo carries no trace of its license, and nothing is
  being *removed* by omission; a notice has to be *added*.
- **The artifacts are emitted into users' pull requests.** MIT's condition attaches to
  "all copies", and an emitted artifact is a copy leaving this repository. A notice
  file sitting in the gallery directory has no path to it. **Only an in-file notice
  travels** — which is exactly why bundlers preserve `@license` comments by default.

The repo's own precedent supports it: six vendored SpecKit extensions each carry a
verbatim upstream `LICENSE` plus structured author/repository/license metadata. The
counter-precedent — eleven vendored upstream files under `.specify/scripts/` and
`.specify/templates/` with **no attribution at all** — is an unremediated gap, not a
convention to extend. FR-011 already permits URLs in comments "so provenance and
attribution links survive", so the header does not collide with the scanner this same
spec defines.

**⚠️ Flagged for human confirmation before ART-002…005 land ports.** Two things are
genuinely unresolved by the sources and are not mine to settle: whether these
specific re-skinned ports clear MIT's undefined "substantial portion" bar, and the
exact header wording. No authoritative source sets a substantiality threshold. The
recommendation rests on cost asymmetry — roughly three lines per file against an
unresolvable argument — not on a published rule. This must be restated in the PR body.

**Item 5 — two of the executor's own worries did not survive checking.** The
cardinality oracle is scoped to the *signal* vocabulary only and does not cover
category, so "a tenth member breaks validation" was invalid; and SC-004 fixes that
ports change only status, so ART-002…005 structurally *cannot* add categories. What
decided it was Session 1 Item 2's ruling transferring verbatim — a member that
duplicates an existing required field and that no consumer reads would be permanent
under the no-removal rule — plus a shipped in-repo contract that keeps kind-of-thing
and origin as two separate fields.

**Item 6 (no consensus needed) — a blocking implementation gap, verified directly by
the orchestrator.** The codebase analyst reported that `speckit-pro/artifact-gallery/`
is absent from the payload builder's per-platform copy lists. Confirmed by reading
`speckit-pro/speckit_pro_runner/gates/payloads.py`: the Claude list is
`[.claude-plugin, agents, commands, hooks, skills, scripts, speckit_pro_runner,
README.md, CHANGELOG.md]`, the Codex list is parallel, and `artifact-gallery` is in
neither. `copy_optional_xplat008` is `if is_dir() … elif is_file()` with **no else
branch**, so a missing source copies nothing and reports nothing. The entire
deliverable would be absent from both built payloads with a green build. Captured as
**FR-018**. Also confirmed: `infer_payload_source_path` special-cases `rel ==
"LICENSE"` and maps it to the repository root, so the attribution notice file must
not be named `LICENSE`.

**Resolved by the orchestrator without consensus.** `title` versus `label` for the
human-readable name: the executor flagged it undetermined, but FR-007's own wording
is "a title", and the nearest precedent's `label` names a test layer rather than a
document. A key name the spec already names does not warrant an analyst round.

**Security-keyword disposition.** The literal keyword rule matches "session" in item
1's text ("the seeded session prompt"). Assessed as a false positive: the word refers
to a clarify session, and none of the three items touches authentication, secrets, or
access control. Not escalated to mandatory human review; recorded here so the call is
auditable rather than silent.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/art-001-brand-kit-gallery-foundation/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Gallery assets: static CSS / HTML / JSON / Markdown under
  speckit-pro/artifact-gallery/ — no build step, no bundler, no Node tooling.
- Validation: Python 3.11+ standard library only, single unit test file
  tests/speckit-pro/unit/test-artifact-gallery.py, registered in
  tests/speckit-pro/suite-manifest.json (match existing unit-test registration
  and naming conventions — every unit test is dash-named).
- No new Bash or jq surface (constitution).

## Constraints
- Marker-block architecture (design concept Q4/Q8): brand-kit.css carries
  BRAND-KIT:START/END; theme-toggle.html carries THEME-TOGGLE:START/END. The
  test extracts embedded blocks from every gallery HTML file and byte-compares
  against the canonical files. Template-specific styling lives outside blocks.
- Scanner (Q3): flags external URLs ONLY in resource-load positions — script/
  img/iframe src, srcset, stylesheet/preconnect link href, CSS url() and
  @import, fetch/XHR/WebSocket literals — allowlisting fonts.googleapis.com and
  fonts.gstatic.com. Navigation <a href> and comment/text URLs are legal.
- Dark mode (Q5): color-scheme: light dark; GTO90 tokens via
  prefers-color-scheme with :root[data-theme] override; toggle persists to
  localStorage inside try/catch (file:// quirks degrade to session-only).
- Manifest (Q1/Q2): all ~21 rows seeded with status planned; triggers are
  {"always": true} or {"any_of": [signals]} against a closed vocabulary the
  test enforces; scanner file-checks only shipped rows.
- Shipped-payload contract: plan must account for payload/proof regeneration
  for the new speckit-pro/artifact-gallery/ directory before completion.

## Architecture Notes
- Re-read docs/ai/specs/.process/ART-001-design-concept.md before planning —
  it is the source of truth for every scoping decision (9 Q&A entries).
- Provenance: record the racecraft-lab/racecraft source commit SHA at
  implementation time in the brand-kit.css header; cite
  docs-site/src/styles/brand.css as the local token source.
- AA contrast pairings must be stated per theme in brand-kit.css comments so
  template ports can verify pairings without re-deriving them.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | 20/20 FRs planned; 24 declared file entries (19 new / 5 modified) |
| `research.md` | ✅ | 12/12 Phase-0 unknowns resolved |
| `data-model.md` | ✅ | Catalog entry shape, signal vocabulary, enums |
| `contracts/` | ✅ | `routing-catalog-contract.md`, `gallery-validation-contract.md` |
| `quickstart.md` | ✅ | How a template port consumes the kit |

**Gate G3: ✅ PASS** — `plan.md` exists, 0 unresolved markers, 0 path leaks across
all six artifacts.

### Plan-phase reviewability budget (advisory — did not block)

`estimate-reviewable-loc` returned `status: pass`, `projected: 0`, `greenfield: false`,
thresholds 400 warn / 800 block, 24 declared entries (19 new, 5 modified).

**The passing zero is not evidence and must not be cited as one.** The helper's
`is_production_file` counts only paths under conventional source directories carrying
JavaScript, TypeScript, or SQL extensions. Every authored file in this feature is CSS,
HTML, JSON, Markdown, or Python, so the production count is structurally 0 regardless
of actual size. The executor flagged this itself rather than banking the pass.

**The scaffold budget is dead and was replaced, not restated.** FR-018 forces a
modification to the payload builder; the estimator computes greenfield as "every
declared entry is new or an excluded generated artifact", so a single non-generated
modified entry disqualifies it and thresholds revert from 600/1200 to 400/800. The
1.5x net-new-only allowance the scaffold relied on is unavailable **by the estimator's
own definition**. `spec.md`'s Reviewability Budget was rewritten to match.

**Honest size: ~1,285 authored lines** — ~423 logic, ~460 declarative, ~355 prose,
~25 verbatim. On a raw-line reading that exceeds the 800 block threshold. Proceeding
is a **judgment based on composition, not volume**: the modification is two lines, the
whole logic surface is one ~420-line validation module, and two-thirds of the rest is
declarative rows and prose. Recorded as the item a reviewer should push on hardest,
with a concrete fallback split (1a kit + 1b catalog) if the judgment is rejected.

### Findings the Plan phase produced by verifying rather than assuming

- **AA contrast was computed, not asserted — and it caught two real failures.** Light
  accent `#3C89C6` on `#E8E5DF` measures 2.99, under the 3:1 floor for meaningful
  non-text elements; the subtle border measures 1.24. Both resolved with documented
  usage rules and a new stronger border token.
- **FR-018's check must be gallery-scoped, not general.** `speckit-pro/AGENTS.md`,
  `CLAUDE.md`, and `GEMINI.md` exist in source, ship in neither payload, and the suite
  is green — so a generalized "all source must ship" check would fail on contact.
- **Two roadmap upstream references would have been guessed wrong.** "upstream 04
  (module map)" is `04-code-understanding.html`; "upstream 14" is
  `14-research-feature-explainer.html`. Fetched rather than inferred.
- **All 21 seeded entries were checked programmatically** against every count the spec
  fixes — 21 entries, 4/4/13 stage split, 20+1 origins, 4 always + 4 conditional + 13
  ad-hoc, FR-007's 4/3/6/7 upstream grouping, and five-signal closure in both
  directions. All pass.
- **`UPSTREAM-NOTICE.md` chosen for the notice file.** The `LICENSE` special-case in
  `infer_payload_source_path` is an exact match, so `artifact-gallery/LICENSE` would
  not actually collide today — but the ban is enforced by check rather than left to
  depend on that behavior holding.
- **One stale rationale sentence corrected in `spec.md`:** Session 2 said "four members
  straddle two stages"; assigning `uat-walkthrough` to `editors` makes it five. The
  load-bearing claim holds more strongly at five. Fixed so Analyze does not reopen it.

**`after_plan` hooks.** `speckit.speckit-utils.validate` deferred — it validates
spec-to-task traceability and `tasks.md` does not exist yet; it runs after Phase 5.
`speckit.git.commit` skipped — the orchestrator owns commits.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together.

### Recommended Domains (from design-tree signals)

| Signal | Domain |
|---|---|
| AA contrast per theme, focus ring, reduced motion, toggle semantics | **accessibility** |
| Manifest schema, status/category/stage enums, 21 seeded rows, trigger vocabulary | **data-integrity** |
| External-reference policy is a trust boundary for shipped artifacts | **security** |

### Step 2: Run Enriched Checklist Prompts

#### 1. accessibility Checklist

Why: the brand kit IS the accessibility surface every artifact inherits — AA
pairings per theme, focus-ring, reduced-motion, and toggle affordances were all
explicit interview decisions (Q5).

```text
/speckit-checklist accessibility

Focus on Artifact Brand Kit & Gallery Foundation requirements:
- WCAG AA (4.5:1 normal text) verified independently for the light palette AND
  the GTO90 dark palette — ratios are not rounded
- Focus-ring rules and reduced-motion (prefers-reduced-motion) coverage in
  brand-kit.css
- Theme toggle: keyboard operability, accessible name/state, and correct
  behavior when localStorage is unavailable over file://
- Pay special attention to: brand red #dc143c "punctuation-only" usage rule —
  red must never be the sole carrier of meaning
```

#### 2. data-integrity Checklist

Why: the manifest is the routing contract for four downstream specs; seeded
rows with a planned→shipped lifecycle (Q1) and a closed trigger vocabulary (Q2)
must be internally consistent and fully test-enforced.

```text
/speckit-checklist data-integrity

Focus on Artifact Brand Kit & Gallery Foundation requirements:
- Every one of the ~21 seeded manifest rows carries all required fields with
  valid enum values (stage, status, category) and a vocabulary-valid trigger
- The status lifecycle (planned → shipped) matches what the scanner enforces
  (file-existence checks only for shipped rows)
- schema_version present and the documented shape in SPA-CONTRACT.md matches
  the test's assertions exactly
- Pay special attention to: row ids — they become the join key template ports
  and the artifact-author agent rely on; no collisions, stable naming
```

#### 3. security Checklist

Why: the external-reference scanner is the enforcement mechanism keeping
shipped review artifacts from phoning home; its allowlist and position rules
(Q3) are the trust boundary.

```text
/speckit-checklist security

Focus on Artifact Brand Kit & Gallery Foundation requirements:
- Scanner covers every resource-load position: script/img/iframe src, srcset,
  link href (stylesheet/preconnect), CSS url(), @import, fetch/XHR/WebSocket
- Allowlist matches hosts exactly (fonts.googleapis.com, fonts.gstatic.com) —
  no substring matches an attacker-controlled lookalike host would pass
- Navigation anchors and comment/text URLs stay legal (no false positives on
  provenance/attribution links)
- Pay special attention to: srcset and CSS url() parsing edge cases, and
  protocol-relative (//host) URL forms
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| accessibility | | | |
| data-integrity | | | |
| security | | | |
| **Total** | | | |

### Addressing Gaps

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/art-001-brand-kit-gallery-foundation/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, testable chunks (1-2 hours each)
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer

## Implementation Phases
1. Foundation: SPA-CONTRACT.md (contract + manifest shape + signal vocabulary
   documented first — it drives everything else)
2. User Story 1 (P1): brand-kit.css + theme-toggle.html with marker blocks;
   brand-voice.md
3. User Story 2 (P1): manifest.json with all ~21 seeded rows
4. Validation: test-artifact-gallery.py (TDD — the test can largely be written
   RED against the contract before assets exist), suite-manifest.json
   registration, payload/proof regeneration

## Constraints
- Bound tasks by the design concept's Non-goals
  (docs/ai/specs/.process/ART-001-design-concept.md): no template ports, no
  DSL, no sync script, no cross-repo checks, no docs-site overlap test
- Test file: tests/speckit-pro/unit/test-artifact-gallery.py (dash-named)
- Gallery assets: speckit-pro/artifact-gallery/ only
- Any decision captured in the design concept but missing from tasks.md is a
  gap to surface, not to silently drop
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
**placeholder** until then — leave the cells blank during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| **Signals** | | The decisive detector findings behind the route (may be empty when the classifier abstains). |
| **Warnings** | | Any release-safety warning attached to the change (empty when there is no risk). |

To produce the decision, run the classifier against the feature directory:

```text
runner helper atomicity-route specs/art-001-brand-kit-gallery-foundation
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — stdlib-only test, no new Bash/jq, KISS (no DSL,
   no sync script, no build step)
2. Coverage gaps — every FR and user story has tasks; the marker-block test,
   scanner, trigger-vocabulary check, and suite-manifest registration each
   trace to a task
3. Design-concept drift — cross-check spec.md, plan.md, and tasks.md against
   docs/ai/specs/.process/ART-001-design-concept.md; the design concept is the
   source of truth for scoping decisions (Q1–Q9); a contradicting downstream
   artifact is wrong unless it carries an explicit revision note
4. Payload contract — confirm tasks account for payload/proof regeneration of
   the new shipped speckit-pro/artifact-gallery/ directory
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
1. Verify you are on branch art-001-brand-kit-gallery-foundation (never main)
2. Run the unit suite baseline:
   python3 tests/speckit-pro/run-layer-scripts.py --layer unit  (or invoke the
   test file directly with python3)
3. Re-read docs/ai/specs/.process/ART-001-design-concept.md — the Q&A log
   carries the "why" behind marker blocks, scanner positions, and the seeded
   manifest lifecycle

### Implementation Notes
- test-artifact-gallery.py is the contract: manifest shape, trigger vocabulary,
  marker-block byte-equality, forbidden external resource loads. Write it RED
  against SPA-CONTRACT.md first where practical.
- Record the racecraft source commit SHA in the brand-kit.css provenance
  header at authoring time.
- After all shipped bytes land, run the payload/proof regeneration ritual and
  re-run Layer 1 before calling the work done.
- Decisions in the design concept that aren't reflected in tasks.md are gaps
  to surface before coding, not to silently drop.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation (SPA-CONTRACT) | | | |
| 2 - Brand kit + toggle + voice | | | |
| 3 - Manifest rows | | | |
| 4 - Validation + payload regen | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Unit test passes: `python3 tests/speckit-pro/unit/test-artifact-gallery.py`
- [ ] Registered in `tests/speckit-pro/suite-manifest.json`
- [ ] Layer 1 structural suite passes
- [ ] Payload/proof regeneration complete (shipped `speckit-pro/artifact-gallery/`)
- [ ] Manual verification: open brand-kit demo/template over `file://` in both themes
- [ ] PR created and reviewed
- [ ] Merged to main branch (humans merge)

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
│   └── artifact-gallery/          # NEW — brand-kit.css, brand-voice.md,
│                                  #   manifest.json, SPA-CONTRACT.md,
│                                  #   theme-toggle.html
├── tests/speckit-pro/
│   ├── unit/test-artifact-gallery.py   # NEW — dash-named, stdlib-only
│   └── suite-manifest.json             # register the new test here
├── docs/ai/specs/                 # roadmap + .process/ exhaust artifacts
└── specs/art-001-brand-kit-gallery-foundation/   # CONTRACT artifacts
```

---

Template based on SpecKit best practices, populated from the ART-001 roadmap
entry and the grill-me design concept (2026-07-28).

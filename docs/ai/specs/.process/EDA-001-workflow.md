# SpecKit Workflow: EDA-001 — Attribution Foundation

**Template Version**: 1.0.0
**Created**: 2026-09-25
**Purpose**: Reusable template for executing SpecKit workflows. Copy-paste the prompts below into your AI coding agent.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/EDA-001-design-concept.md
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
| Stage | plan | ✅ Complete | Explicit --stage plan resolved; planning phases continue |
| Specify | `/speckit-specify` | ✅ Complete | 3 stories, 19 FRs; G1 routes provenance marker to Clarify |
| Clarify | `/speckit-clarify` | ✅ Complete | Three sessions resolved; G2 passed with 0 markers |
| Plan | `/speckit-plan` | ✅ Complete | Seven artifacts, G3 pass, and privacy 13/13 after approved wording correction |
| Checklist | `/speckit-checklist` | ✅ Complete | 88 items; 3 gaps resolved; G3/G4 pass with 0 markers |
| Tasks | `/speckit-tasks` | ✅ Complete | 27 tasks; 19/19 FRs; valid required execution metadata; G5 pass |
| Analyze | `/speckit-analyze` | ✅ Complete | One LOW resolved; 0 remaining required findings; G6 pass; dedicated named final synthesis complete |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | |
| Post | Post-Implementation | ⏳ Pending | Canonical 11-item closeout |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default, so no phase of the main loop flips its row. Leaving
it Pending is legitimate and does not make the rows below it read as out of
order; record the verdict in [Phase 6.5](#phase-65-confidence-gate) when the
gate runs.

### Phase Gates

Use `references/gate-validation.md` from the installed `speckit-autopilot` skill as the authority for active criteria and escalation behavior.

| Gate | Checkpoint |
|------|------------|
| G1 | After Specify |
| G2 | After Clarify |
| G3 | After Plan |
| G4 | After Checklist |
| G5 | After Tasks |
| G6 | After Analyze |
| G6.5 | Before Implement |
| G7 | After Each Implementation Phase |

---

## Prerequisites

### Worktree and branch

- Worktree: `.worktrees/eda-001-attribution-foundation`, relative to the
  repository root.
- Branch: `eda-001-attribution-foundation`, stacked on
  `docs/engineering-discipline-adoption` (PR #672, which carries the PRD,
  roadmap, and roadmap MOC and is not yet merged). Starting commit: `ff68dd4de`.
- Bootstrap: `pnpm --dir docs-site install --frozen-lockfile` ran with operator
  approval; the generated-artifact merge driver was already configured for this
  clone.
- The branch name is non-numeric. Autopilot needs `.specify/feature.json`
  pointing at `specs/eda-001-attribution-foundation` and must not let the
  `before_specify` git.feature hook create a numbered branch. The
  `brand-001-` and `formal-001-` specs are the local precedent.
- Local privacy-scan false positive: `tests/speckit-pro/unit/test-privacy-scan.py`
  derives "local identity" terms from the repository root path
  (`dynamic_local_pattern`), so this worktree's directory name makes words such
  as "attribution" and "foundation" match across the whole tree. On 2026-09-25
  it failed this way before any spec change. A local failure whose hits share
  only those path-derived terms is not a spec defect; CI runs from a neutral
  checkout path. Any other hit is real and must be fixed.

Before every phase, verify the active root and branch. Fail closed if the workflow
is launched from another checkout.

### Preset resolution

These commands resolved to the repository's `speckit-pro-reviewability` preset
v1.0.0 on 2026-09-25:

```text
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| I. Plugin Structure Compliance | New notice files live under an existing skill's `references/`; tests stay under top-level `tests/speckit-pro/` | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | Test is Python 3.11+ standard library; shipped prose carries no `bash`, `jq`, or `$(` instructions | `python3 tests/speckit-pro/run-all.py --layer 4` |
| III. Semantic Versioning | No manual version edits; release-please owns versions | Layer 1 semantic-version check |
| IV. Test Coverage Before Merge | New attribution test registered in `tests/speckit-pro/suite-manifest.json` | `python3 tests/speckit-pro/run-all.py` |
| V. Conventional Commits | `type(speckit-pro): description` commits and PR titles | CI `validate-pr-title` |
| VI. KISS, Simplicity & YAGNI | JSON via the `json` module; no helper layers beyond what the test needs | Code review |

**Constitution Check:** ⚠️ Planning checks I-IV and VI pass; final PR title is pending. The already pushed checkpoint commit used a spec-ID scope; the repository hook blocked an exact-lease title rewrite. Future commits use `speckit-pro` scope.

### Quality Gates

Filled from `detect-commands` at Step 0.11. One row per slot; the operator answer column holds the one-time missing-tool decision (`install`, `skip (spec)`, `skip (repo)`, or `unanswered`) and is the record that stops the question from firing again. A `skip (repo)` answer is durable only once the operator adds it to `.specify/quality-gates.json` `skips`.

**Thresholds file:** `.specify/quality-gates.json` is present and validated: complexity 8, CRAP 30, mutation-score floor 60; no gate skips or enforcement opt-ins.

**Hardener:** not run <!-- not needed (score N ≥ floor F) | qwen: iteration k of cap: N → M ... floor reached / cap reached | fallback (reason): ... | rejected candidate: reason --> (fires once per spec when MUTATION is populated)

| Slot | Status | Tool | Command | Operator answer | G0 baseline | Final |
|------|--------|------|---------|-----------------|-------------|-------|
| COMPLEXITY | unconfigured | N/A | N/A | n/a | n/a: unconfigured | pending |
| MUTATION | unconfigured | N/A | N/A | n/a | n/a: unconfigured | pending |
| DEPENDENCY_RULES | unconfigured | N/A | N/A | n/a | n/a: unconfigured | pending |
| DEPENDENCY_AUDIT | off | N/A | N/A | off: never asked | off: not opted in | off |

---

## Formal Methods

```json
{
  "schema_version": "1.0",
  "status": "none",
  "rationale": "EDA-001 adds static notice files, a JSON ledger, and a deterministic data-shape test. It has no state machine, concurrency, or protocol whose correctness ordinary tests cannot establish.",
  "models": []
}
```

## Formal Checkpoints

| Checkpoint | Status | Evidence or setup gap |
|---|---|---|
| Plan model authoring and G3 | disabled | No selected model |
| Planning reconciliation | disabled | No selected model |
| Final model and optional trace checks | disabled | No selected model |
| Post integration | disabled | No selected model |

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | EDA-001 |
| **Name** | Attribution Foundation |
| **Branch** | `eda-001-attribution-foundation` |
| **Dependencies** | None (stacked on the roadmap PR #672 only because the roadmap lives there) |
| **Enables** | EDA-002 through EDA-011 |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] The MIT notice ships in both `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, with the license text byte-identical to the fork at `speckit-pro-baseline` (`c55ee46073ed923f86ce59a5eb3b6d895095d1b7`).
- [ ] `ledger.json` records exactly the 38 upstream skills; every IGNORE row has a reason; ask-matt, wayfinder, and triage carry `not_ported`; `pr` carries a `transitive_sources` entry.
- [ ] The separate HumanLayer MIT notice ships with the source repository LICENSE text verbatim and the exact `show-me` commit and path.
- [ ] The attribution test fails on each defect it guards, proven by fixtures, and passes on the real tree without looping over an empty set.
- [ ] The credit header format and `metadata.credits` shape are documented for EDA-002 onward.
- [ ] `speckit-pro/README.md` acknowledges the upstream work and links the notice.

---

## Phase 1: Specify

**When to run:** At the start of a new feature specification. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/eda-001-attribution-foundation/spec.md`

### Specify Prompt

```text
/speckit-specify Publish Matt Pocock's MIT notice for mattpocock/skills and a machine-readable 38-row disposition ledger inside the speckit-coach skill so both plugin payloads ship them, add a second Apache-2.0 notice for the humanlayer show-me text that upstream pr copies, define the file-level credit header every later derivative file must carry, and enforce all of it with an attribution test that cannot pass on nothing, before any derivative content lands.
```

#### Detailed Prompt (for complex specs)

```text
/speckit-specify

## Feature: Attribution Foundation

### Problem Statement
SpecKit Pro will absorb Matt Pocock's MIT-licensed mattpocock/skills (38 skills,
forked to racecraft-lab/skills and pinned by tag speckit-pro-baseline at
c55ee46073ed923f86ce59a5eb3b6d895095d1b7) across ten later specs (EDA-002 to
EDA-011). Every derivative file must credit its source, and one upstream skill
(pr) itself copies Apache-2.0 text from Dex Horthy's show-me skill in
humanlayer/humanlayer (Copyright (c) 2024, humanlayer Authors). Without a notice,
a ledger, and an enforcing test in place first, derivative content could ship
without attribution and nothing would catch it.

### Users
- Plugin users and redistributors, who need the license notices in the installed
  payloads.
- SpecKit Pro maintainers running EDA-002 onward, who flip ledger rows to landed
  and need a test that rejects missing credits.
- Reviewers, who need one place listing what came from upstream and what was
  deliberately not ported.

### User Stories
- US1 (P1, slice 1): As a redistributor, I find the MIT notice and the 38-row
  ledger in both installed payloads, so the license obligation is met.
- US2 (P1, slice 1): As a maintainer, when I mark a ledger row landed, the
  attribution test fails unless the destination exists and carries the credit
  header; the test also rejects a malformed ledger even while no row is landed.
- US3 (P2, slice 2): As a redistributor, I find a separate Apache-2.0 notice for
  the humanlayer show-me text, linked from the pr ledger row, with a pinned
  source.

### Decisions already made (design concept Q1 to Q8)
- Ledger form (Q1): a JSON sidecar ledger.json beside UPSTREAM-NOTICE.md, one
  object per upstream skill, ordered by upstream path, pretty-printed one key per
  line so parallel branches flipping different rows merge cleanly. Fields:
  upstream_path, bucket, disposition (ABSORB | NEW | IGNORE), destination (null
  for IGNORE), owner_spec, status (planned | landed; absent for IGNORE),
  ignore_reason (IGNORE only), not_ported, transitive_sources.
- Second license (Q2): user chose "Both notices now". A separate notice at
  references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md, following the
  one-notice-per-holder Quint precedent.
- Pin (Q5, Q6): user chose "Find exact source first", falling back to the
  humanlayer head pin with the gap disclosed if the source cannot be found.
- Non-vacuous test (Q3): a frozen 38-path list from the pinned SHA, plus pass and
  fail credit-header fixtures that exercise the landed-row check before any real
  row lands.
- Credit form (Q4): user chose "File header only". One file-level header per
  derivative file (upstream skill paths, pinned SHA, "Modified derivative: yes",
  notice path), in the file type's comment syntax, placed after frontmatter
  where frontmatter exists; SKILL.md files also carry metadata.credits.
- Partial absorption (Q7): a required not_ported note on exactly ask-matt,
  wayfinder, and triage; the disposition set stays three values.
- Slicing (Q8): two vertical slices, each its own PR in the EDA stack. Slice 1 is
  US1 and US2. Slice 2 is US3 plus transitive_sources enforcement.

### Constraints
- Notices live under speckit-pro/skills/speckit-coach/references/upstream/ so
  both payload builders ship them with no payloads.py change.
- License text is reproduced byte for byte; never reword it.
- Test is Python 3.11+ standard library, named for durable behavior
  (test-upstream-skill-attribution.py), and never reads a specs/<feature>/ path
  at run time.
- No bash, jq, or $( instructions in shipped prose; no home paths, temp paths,
  or UUIDs in committed files.

### Out of Scope
- Any derivative content (EDA-002 onward).
- Edits in the racecraft-lab/skills fork.
- Section-level credit markers; a PARTIAL disposition value.
- Changing other roadmap entries' reviewability budget lines.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 19 |
| User Stories | 3 |
| Acceptance Criteria | 11 scenarios; 6 success criteria |

### Files Generated

- [x] `specs/eda-001-attribution-foundation/spec.md`

G1 routed one unresolved humanlayer source-pin marker to Clarify Session 1. The installed gate helper returned `expected_failure` with `markers=1`; this is the documented clarification route, not a completed provenance claim.

### SpecKit Traceability Markers

Use these markers in spec.md for traceability through later phases:

| Marker | Purpose | Example |
|--------|---------|---------|
| `[US1]`, `[US2]` | User story reference | `[US1] User searches by query` |
| `[FR-001]` | Functional requirement | `[FR-001] API returns paginated results` |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase | `Auth method [NEEDS CLARIFICATION]` |
| `[P]` | Parallel-safe task | `[P] Can run alongside other tasks` |
| `[Gap]` | Missing coverage | `[Gap] No task covers error handling` |

---

## Phase 2: Clarify

**When to run:** When spec has areas that could be interpreted multiple ways. 10-20 minutes here saves hours of rework later.

**Best Practice:** Maximum 5 targeted questions per Clarify session.

### Clarify Prompts

#### Session 1: Provenance Focus

```text
/speckit-clarify Focus on provenance of the show-me text: locate the exact commit and path of Dex Horthy's show-me skill (search humanlayer/humanlayer history, including commits touching .claude/ or commands/, the "shape of the change" wording, and any Dex Horthy repository linked from humanlayer). If it cannot be found, adopt the operator's fallback: pin humanlayer head 99abe673498cf8bdcd5f989aebe9406a27185b3b and disclose the unlocated path in the notice. Also confirm the humanlayer LICENSE is the 15-line Apache-2.0 header and decide how the frozen fixture copy is stored.
```

#### Session 2: Ledger Contract Focus

```text
/speckit-clarify Focus on the ledger.json contract: exact field names and types, the bucket values that account for all 38 upstream skills (engineering, productivity, misc, in-progress), whether owner_spec stays informational or is enforced in a checkable form (design concept Open Question), how IGNORE rows represent destination and status, and the ordering and formatting rules that keep parallel row flips merge-clean without the merge=generated driver.
```

#### Session 3: Test and Credit Header Focus

```text
/speckit-clarify Focus on the attribution test and credit header: the exact credit header text and its comment syntax per file type (Markdown, TOML, Python), placement after frontmatter, the metadata.credits frontmatter shape for SKILL.md files, how the MIT block is located inside the notice for the byte comparison, and which fixtures prove each failure mode so no check passes on an empty set.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Provenance | 2 | Exact source pinned to `humanlayer/skills@bba9d13`; operator selected its MIT license for the separate notice |
| 2 | Ledger contract | 4 | Closed typed `entries` schema; exact four-bucket path mapping; checked roadmap owner mapping with EDA-001 on IGNORE; canonical row formatting |
| 3 | Test and credit header | 5 | Fixed file-level header; quoted string `metadata.credits`; one byte-exact fenced license block per notice; recursive nonempty landed-file checks and targeted fixtures |

### Operator decision after Session 1

The operator answered `MIT` in the active Codex chat. Keep both notices: the Matt Pocock notice and a separate HumanLayer notice using the MIT `LICENSE` from `humanlayer/skills@bba9d13ab34f0a87f1cc33df4dd196372393ddfc`. The exact `show-me` source is `plugins/show-me/skills/show-me/SKILL.md` at that commit. This decision supersedes Apache and repository-head fallback language in the historical Specify and Clarify prompts above. Future phase prompts and artifacts use this resolved source and license.

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Exact copied `show-me` source | [spec, domain] | 1→2 | 2/3 | Pinned `humanlayer/skills@bba9d13` and retired repo-head fallback in FR-016 | spec-context-analyst, domain-researcher, codebase-analyst |
| 2 | Clarify | License bytes for separate HumanLayer notice | [codebase, domain] | 1 | [HUMAN REVIEW] | Operator answered `MIT`; preserve two notices and use the pinned source repository license | codebase-analyst, domain-researcher |
| 3 | Clarify | Exact bucket mapping for 38 upstream skills | [spec, domain] | 1 | both-agree | Four buckets match the immediate directory after `skills/` in the pinned tree; 18/7/4/9 paths | spec-context-analyst, domain-researcher |
| 4 | Clarify | Checked `owner_spec` mapping and IGNORE ownership | [spec] | 1→2 | 3/3 | Freeze exact path-to-owner map; EDA-001 owns IGNORE, EDA-002–EDA-010 own delivery, EDA-011 verifies close-out | spec-context-analyst, codebase-analyst, domain-researcher |
| 5 | Clarify | `metadata.credits` frontmatter shape | [codebase, domain] | 1 | both-agree | Use a quoted string of sorted `mattpocock/skills@SHA:path` identifiers separated by `; `; repository check owns semantics | codebase-analyst, domain-researcher |
| 6 | Gap | CHK007: HumanLayer public pinned copied-source URL | [spec] | 1 | high-confidence | Exact FR-014 and notice-contract proposal applied under explicit operator override; revalidated with 0 gaps | spec-context-analyst; named consensus-synthesizer |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Generates technical implementation blueprint. Output: `specs/eda-001-attribution-foundation/plan.md`

### Plan Prompt

```text
/speckit-plan

## Tech Stack
- Plugin content: Markdown and JSON under speckit-pro/skills/speckit-coach/references/upstream/
- Tests: Python 3.11+ standard library (unittest), registered in tests/speckit-pro/suite-manifest.json
- Generated outputs: dist/ payloads via python3 scripts/refresh-release-artifacts.py; docs reference pages via pnpm --dir docs-site reference:generate
- No new dependencies

## Constraints
- Re-read docs/ai/specs/.process/EDA-001-design-concept.md; it is the source of truth for scoping decisions.
- Two vertical slices, each its own PR in the EDA gh-stack on top of docs/engineering-discipline-adoption (Q8, "Two vertical slices"):
  - Slice 1: MIT notice, ledger.json, attribution test and fixtures, suite registration, README acknowledgement, regenerated artifacts.
  - Slice 2: exact `show-me` source pin, separate HumanLayer MIT notice, transitive_sources enforcement.
- Ledger is a JSON sidecar (Q1, "JSON sidecar"), not a Markdown table. Never route it through the merge=generated driver.
- Both notices ship (Q2, "Both notices now"). Clarify Session 1 located the exact `humanlayer/skills@bba9d13` source and the operator selected that repository's MIT license; the Q6 repo-head fallback is retired.
- Credit form is file header only (Q4, "File header only").
- Partial absorption uses a required not_ported field (Q7).
- Test must not pass vacuously (Q3, "Frozen set + fixture proof"); mirror tests/speckit-pro/unit/test-quint-reference-attribution.py, which asserts seen > 0 "refusing to pass vacuously", rather than the substring MIT check in tests/speckit-pro/unit/test-artifact-gallery.py:144.
- Reviewability budget: estimate-spec-size returned 625 LOC, warn, 2 suggested slices; the split above answers it. estimate-reviewable-loc returns not_estimated for Markdown and JSON layouts, and that is never a within-budget pass (speckit-autopilot references/phase-execution.md).

## Module and Interface Deltas (refined by Clarify Sessions 1–3)
- speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md: new. It carries the MIT text verbatim; the upstream URL, fork URL, and pinned SHA; a statement that the files the ledger lists as landed are modified derivatives; and a pointer to ledger.json. (Evidence: roadmap Scope; Q1.)
- speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json: new interface consumed by the test and by every later EDA spec. Its only root key is `entries`, with 38 objects sorted lexicographically by full `upstream_path`. Use two-space indentation, LF line endings, one final newline, and fixed present-key order to keep row flips reviewable; never route this file through `merge=generated` (Q1, Clarify Session 2). Fields and rules:
  - `upstream_path`: exact pinned `skills/<bucket>/<skill>/SKILL.md` string
  - `bucket`: `engineering`, `productivity`, `misc`, or `in-progress`, matching the path; the pinned tree has 18/7/4/9 paths respectively
  - `disposition`: `ABSORB`, `NEW`, or `IGNORE`
  - `destination`: repository-relative path string for `ABSORB`/`NEW`, `null` for `IGNORE`
  - `owner_spec`: exact frozen path-to-owner mapping; EDA-001 for `IGNORE`, roadmap EDA-002–EDA-010 delivery owner otherwise; EDA-011 owns no row
  - `status`: `planned` or `landed` for `ABSORB`/`NEW`; absent for `IGNORE`
  - `ignore_reason`: substantive string on `IGNORE`; absent otherwise
  - `not_ported`: substantive string on exactly `ask-matt`, `wayfinder`, and `triage`; `null` elsewhere (Q7)
  - `transitive_sources`: array, empty except the initial `pr` entry; each entry has string `project`, `commit`, `path`, `license`, `holder`, `notice_path` fields (Q2, Clarify Session 1)
  - Reject unknown root, row, or transitive-source keys and invalid types before landed-row checks.
- speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md: new in slice 2. It holds the MIT LICENSE text verbatim from `humanlayer/skills@bba9d13ab34f0a87f1cc33df4dd196372393ddfc/LICENSE`, including Copyright (c) 2026 HumanLayer, and pins `plugins/show-me/skills/show-me/SKILL.md` at that same commit (Q2, Q5, Clarify Session 1).
- Credit header (interface for EDA-002 to EDA-011): one file-level header per derivative file, not per section (Q4, Clarify Session 3).
  - Exact lines in order: `Upstream repository: mattpocock/skills`; sorted `Upstream skill: <upstream_path>` lines; `Pinned commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7`; `Modified derivative: yes`; `License notice: speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`.
  - Syntax: one HTML comment in Markdown, or each line prefixed `# ` in TOML and Python. Place it as the first nonblank body block after frontmatter; Python may have a shebang and encoding declaration first.
  - `SKILL.md` frontmatter also carries `metadata.credits` as one quoted string of sorted `mattpocock/skills@SHA:<upstream_path>` identifiers joined with `; `; the attribution test checks it against the header. The Agent Skills specification requires string values in `metadata`; no host presentation behavior is assumed.
- tests/speckit-pro/unit/test-upstream-skill-attribution.py: new. It is named for durable behavior, not the spec ID (AGENTS.md Editing Boundaries).
- tests/speckit-pro/unit/fixtures/upstream-skill-attribution/: new fixtures:
  - the frozen MIT text;
  - the frozen `humanlayer/skills@bba9d13` MIT LICENSE (slice 2);
  - the frozen 38-path upstream list taken from the pinned SHA;
  - positive zero-landed and landed Markdown/TOML/Python fixtures, including SKILL.md metadata, plus targeted negative mutations for inventory/schema/owner, empty or missing destinations, absent or mismatched headers or metadata, and missing/duplicate/altered notice license blocks (Q3, Clarify Session 3).
- tests/speckit-pro/suite-manifest.json: changed, registering the new test.
- speckit-pro/README.md: changed, adding an acknowledgements line that links the MIT notice.
- Generated outputs: changed by regeneration only, never by hand edits:
  - dist/ payloads;
  - docs-site/src/content/docs/reference/tests.md (a new test .py, per tests/speckit-pro/AGENTS.md:12);
  - the Plugin Authoring Source reference page, which reads speckit-pro/README.md (docs-site/scripts/generate-reference-pages.mjs:590).
- Unchanged grey box: payloads.py, the skill contract validators, and every skill's behavior.

## Architecture Notes
- Precedents to mirror: speckit-pro/skills/speckit-coach/references/quint/UPSTREAM-NOTICE.md and provenance.json (one notice per license holder, pinned commit, verbatim license block); speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md (MIT notice shape).
- The fork is a provenance anchor only; the notice cites both github.com/mattpocock/skills and github.com/racecraft-lab/skills at the pinned SHA.
- The 38-path frozen list comes from the upstream tree at the pinned SHA: engineering, productivity, misc, and in-progress buckets.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Two slices, technical flow, 19 FRs; G3 passed |
| `research.md` | ✅ | Six decisions; broker outage and supplied primary evidence distinguished |
| `data-model.md` | ✅ | Closed ledger, inventory/owners, source/credit entities |
| `contracts/` | ✅ | ledger.md, credits.md, notices.md |
| `quickstart.md` | ✅ | Slice acceptance and required verification commands |

G3 passed after the ordinary Plan executor returned. All seven planning artifacts are nonempty and contain no unresolved markers or failing constitution checks. The optional post-Plan traceability hook requires `tasks.md`, which Phase 5 creates; Git hooks duplicate the parent phase commits and were skipped. Plan setup used the existing Specify CLI Python environment with PyYAML, without adding dependencies.

**Recovery checkpoint:** The focused privacy check returned 12/13 after Plan. `contracts/ledger.md:23` used slash-separated absolute, home, and temp wording that matches the home-path regex. The concrete correction is to say “absolute paths, home prefixes, or temporary prefixes.” The execution-control reservation `plan-privacy-wording-repair-1` was refused with `failure_family_budget_exhausted`; no repair was applied. The run retains its existing identity and one consumed corrective cycle, has no in-flight dispatch or unknown effect, and awaits the operator decision before checklists, Tasks, Analyze, and G6.5. G3 remains a recorded pass; the plan stage is not complete.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates both spec AND plan together. Run multiple times for different domains.

**Best Practice:** Don't guess which domains to check. Analyze the spec first, then generate enriched prompts with spec-specific focus areas.

### Step 1: Analyze Spec for Recommended Domains

Before running any checklists, read `spec.md` and `plan.md` and identify which domains apply. Look for these signals:

| Signal in Your Spec/Plan | Recommended Domain |
|---|---|
| API endpoints, REST routes, request/response models | **api-contracts** |
| User-facing UI, components, forms, layouts | **ux** |
| Keyboard navigation, screen readers, WCAG, ARIA | **accessibility** |
| Auth, tokens, secrets, input validation, user roles | **security** |
| Response time budgets, caching, query performance | **performance** |
| Database schemas, migrations, data validation | **data-integrity** |
| LLM prompts, model calls, embeddings, token limits | **llm-integration** |
| SSE, WebSocket, streaming, real-time events | **streaming-protocol** |
| Error handling, retries, fallbacks, degradation | **error-handling** |
| State lifecycle, sessions, caching, persistence | **state-management** |
| Personal data (PII), consent, retention, deletion | **privacy** |
| New third-party packages or dependency upgrades | **supply-chain** |

**Target: 2-4 domains.** Prioritize domains where the spec has the most complexity or risk.

### Step 2: Run Enriched Checklist Prompts

For each domain, include spec-specific focus areas in the prompt — not just the bare domain name.

#### 1. supply-chain Checklist

Why this domain: the spec redistributes third-party text from two MIT-licensed source repositories and must pin each source exactly.

```text
/speckit-checklist supply-chain

Focus on Attribution Foundation requirements:
- Both holder-specific MIT license texts reproduced byte for byte from their pinned source commits
- Every copied source named with project, holder, license, URL, and commit
- The transitive show-me source recorded on the pr ledger row and its notice
- Pay special attention to: the exact `humanlayer/skills` commit and path; the superseded repository-head fallback must not appear as the source pin
```

#### 2. data-integrity Checklist

Why this domain: ledger.json is a contract that ten later specs edit, and the test must reject every malformed state.

```text
/speckit-checklist data-integrity

Focus on Attribution Foundation requirements:
- Exactly 38 rows matching the frozen upstream path list, no duplicates or extras
- Field rules per disposition (IGNORE reason, not_ported on exactly three rows, transitive_sources on pr)
- Stable ordering and formatting so parallel row flips merge cleanly
- Pay special attention to: checks that could pass on an empty set while 0 rows are landed
```

#### 3. error-handling Checklist

Why this domain: the test's value is in its failure messages, and the credit-header checker must fail closed.

```text
/speckit-checklist error-handling

Focus on Attribution Foundation requirements:
- Each guarded defect produces a failure naming the row or file
- Credit-header pass and fail fixtures prove the checker in both directions
- Missing notice, missing ledger, and unparseable JSON fail loudly
- Pay special attention to: a landed row whose destination file has frontmatter, where the header must follow the frontmatter
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| supply-chain | 28 | 0 remaining | FR-001–003, FR-005, FR-007, FR-009–016, FR-018 |
| data-integrity | 28 | 0 | FR-002–009, FR-012, FR-014–017; SC-003/005 |
| error-handling | 32 | 0 | FR-008, FR-010–014; file diagnostics and frontmatter proof |
| **Total** | 88 | 0 remaining; 3 resolved | Three domains |

### Addressing Gaps

When checklist identifies `[Gap]` items:

1. Review the gap — is it a genuine missing requirement?
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/eda-001-attribution-foundation/tasks.md`

### Tasks Prompt

```text
/speckit-tasks

## Task Structure
- Small, complete behavioral units sized for the whole automated spec's
  two-hour budget, including startup, implementation, repairs and final checks
- Clear acceptance criteria referencing FR-xxx
- Dependency ordering: foundation → components → integration → validation
- Mark parallel-safe tasks explicitly with [P]
- Organize by user story, not by technical layer
- Keep related test and implementation checkboxes in one closed TDD unit;
  each unit must fit an adjacent batch of at most four tasks

## Execution Metadata
Produce `specs/eda-001-attribution-foundation/.process/task-execution.json` alongside tasks.md.
Use `schema_version: task-execution.v1`, `fingerprints` from runner helper
`validate-task-execution` (`action: fingerprints`, `tasks_file: <tasks.md>`),
and `tasks` keyed by every task ID. Each entry contains `capability_group`,
`depends_on` (task IDs), `owns` (repo-relative paths including shared fixtures
and generated inputs), and `tdd_unit`. Fingerprints bind spec, plan and task
definitions, excluding checkbox completion. Validate the completed sidecar.
Do not guess fingerprints or omit ownership to force parallel execution.

## Implementation Phases
1. Foundation: frozen fixtures (MIT text, 38-path list, credit-header pass and fail fixtures)
2. User Story 1 (P1, slice 1): MIT notice, ledger.json, README acknowledgement
3. User Story 2 (P1, slice 1): attribution test red then green, suite-manifest registration
4. User Story 3 (P2, slice 2): pinned `show-me` source, separate HumanLayer MIT notice, transitive_sources enforcement
5. Polish: regenerate dist/ and docs reference pages, run every verification gate

## Constraints
- Read spec.md, plan.md, and docs/ai/specs/.process/EDA-001-design-concept.md.
- Flag any task that crosses a design-concept Non-goal: derivative content, fork edits, section-level credit markers, a PARTIAL disposition, other roadmap entries' budget lines, or routing the ledger through merge=generated.
- Write each test before the notice or ledger content it guards (Q3's "why": the test must be proven to fail before it passes).
- Tests live under tests/speckit-pro/unit/; fixtures under tests/speckit-pro/unit/fixtures/upstream-skill-attribution/.
- Generated files (dist/, docs-site reference pages) change only by regeneration.
- Mark the slice boundary between US2 and US3 so the atomicity route can emit two PRs.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 27 (all unchecked) |
| **Phases** | 6 |
| **Parallel Opportunities** | T002 and T003 only; shared-file behavioral units are serial |
| **User Stories Covered** | US1, US2, US3; all 19 FRs |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, autopilot runs the
read-only `atomicity-route` runner helper and records its decision here. Leave
the cells blank during scoping. The helper writes nothing itself; autopilot
records the route only in this workflow file, never in the spec map, and runs
the layer planner only when the route is `split-PR`.

The decision answers "can this change be split into multiple small PRs safely?" by
inspecting the change's structural seams (independent additive capabilities), not its
line count. Surface the four fields the SKILL extracts from the emitted decision:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | one-navigable-PR | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | true | `true`, or `false` for a destructive-migration or concurrency-sensitive change (a passing CI run does not prove such a change is safe to release). |
| **Signals** | change-shape:modify-heavy | The decisive detector findings behind the route and releasability reading (may be empty when the classifier abstains). |
| **Warnings** | [] | Any release-safety warning attached to the change (empty when there is no releasability risk). |

To produce the decision, send the complete read-only runner request:

```json
{
  "schema_version": "1.0",
  "request_id": "atomicity-route-EDA-001",
  "helper_id": "atomicity-route",
  "operation": "atomicity-route",
  "mode": "read_only",
  "inputs": {
    "feature_dir": "specs/eda-001-attribution-foundation",
    "workflow_file": "docs/ai/specs/.process/EDA-001-workflow.md"
  }
}
```

The workflow path excludes this exact workflow and its sibling
`autopilot-state.json` from change classification. If an older workflow has
the positional instruction, replace only that instruction and preserve all
phase status and operator-authored content.


---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment — verify coding standards compliance
2. Coverage gaps — ensure all FRs and user stories have tasks
3. Consistency between task file paths and actual project structure
4. Verify P1 user stories have complete task coverage
5. Drift from docs/ai/specs/.process/EDA-001-design-concept.md: its Goals, Non-goals, Q1 to Q8 decisions, Module and Interface Deltas, and Verification Gates are the source of truth. A downstream artifact that contradicts them is wrong unless it carries an explicit revision note.
6. Every ledger field and credit-header rule in plan.md has a test task that proves it fails on a defect
7. The two-slice boundary (US1 and US2 in slice 1, US3 in slice 2) is consistent across spec, plan, and tasks
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
| I1 | LOW | Foundation prerequisite summary contradicted T001 dependency in phase table and sidecar | Resolved: tasks.md:139 now requires T001, permits T002/T003 together, waits for both before T004; refreshed native fingerprints; re-analysis 0 findings |

---

## Phase 6.5: Confidence Gate

**When to run:** After Phase 6 commits and before Phase 7 begins. This section
records the verdict so a later session can read it.

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
1. Confirm the active root is .worktrees/eda-001-attribution-foundation and the branch is eda-001-attribution-foundation, never main.
2. Sync the base: fetch docs/engineering-discipline-adoption and merge it if it moved.
3. Run python3 tests/speckit-pro/run-all.py and confirm it passes before any change.

### Implementation Notes
- Read tasks.md, plan.md, and docs/ai/specs/.process/EDA-001-design-concept.md. Consult the Q&A log for the "why" behind each decision. Surface any design-concept decision missing from tasks.md as a gap before coding; do not drop it silently.
- Take license text only from the pinned sources: the fork LICENSE at speckit-pro-baseline (c55ee46073ed923f86ce59a5eb3b6d895095d1b7) and humanlayer's LICENSE at the pinned commit. Copy bytes exactly.
- Build the 38-path frozen list from the upstream tree at the pinned SHA, not from roadmap prose.
- Assert a non-zero count wherever a check loops over rows or files (Q3).
- Keep every path in committed files repo-relative; no home or temp paths.
- Use python3 for any scripted step; no bash, jq, or $( in shipped prose.

### Verification Gates (carried verbatim from the design concept)
- Attribution test: python3 tests/speckit-pro/unit/test-upstream-skill-attribution.py passes. It fails if:
  - the MIT block differs by any byte from the frozen copy;
  - the ledger's upstream-path set is not exactly the frozen 38;
  - an IGNORE row lacks ignore_reason;
  - not_ported is missing from ask-matt, wayfinder, or triage, or appears on any other row;
  - the credit checker accepts the fail fixture or rejects the pass fixture;
  - any landed row's destination is missing or lacks a credit header;
  - in slice 2, a transitive_sources notice path is missing or its license text differs from its frozen copy.
  The checks that count rows assert a non-zero count before they pass (Q3; precedent tests/speckit-pro/unit/test-quint-reference-attribution.py:239).
- Quick suite: python3 tests/speckit-pro/run-all.py passes (AGENTS.md Commands).
- CI suite: the run-default-suite.json runner command from AGENTS.md passes.
- Generated artifacts: run python3 scripts/refresh-release-artifacts.py, commit, then python3 scripts/refresh-release-artifacts.py --check exits 0. Both dist/claude/speckit-pro/ and dist/codex/speckit-pro/ contain the notice and ledger.json (roadmap Scope).
- Docs reference: pnpm --dir docs-site reference:generate, then pnpm --dir docs-site reference:check and pnpm --dir docs-site validate:quality pass (tests/speckit-pro/AGENTS.md:12; AGENTS.md Commands).
- Privacy scan: tests/speckit-pro/unit/test-privacy-scan.py passes. The notices hold only public names, URLs, and SHAs (AGENTS.md Gotchas).
- Shipped prose contains no bash, jq, or $( instructions (active_path_guard.py; AGENTS.md Gotchas).
- PR title and release-note gates pass before each slice's PR is marked ready.
- Formal methods: none. The spec adds static files and a deterministic data-shape test, with no state machine or concurrency to model (evidence: roadmap Scope).
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - User Story 1 | | | |
| 3 - User Story 2 | | | |
| 4 - User Story 3 | | | |
| 5 - Polish | | | |

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
| Post: UAT Runbook Generation | ⏳ Pending | |
| Post: PR Body Generation | ⏳ Pending | |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

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
speckit-pro/skills/speckit-coach/references/upstream/
├── mattpocock-skills/
│   ├── UPSTREAM-NOTICE.md      # MIT notice (slice 1)
│   └── ledger.json             # 38-row disposition ledger (slice 1)
└── humanlayer-show-me/
    └── UPSTREAM-NOTICE.md      # HumanLayer MIT notice (slice 2)
tests/speckit-pro/unit/
├── test-upstream-skill-attribution.py
└── fixtures/upstream-skill-attribution/   # frozen license texts, 38-path list, credit fixtures
tests/speckit-pro/suite-manifest.json      # test registration
speckit-pro/README.md                      # acknowledgement line
```

---

## PROJECT_COMMANDS

```json
{
  "BUILD": "N/A",
  "COMPLEXITY": "N/A",
  "DEPENDENCY_AUDIT": "N/A",
  "DEPENDENCY_RULES": "N/A",
  "FULL_VERIFY": "python3 tests/speckit-pro/run-all.py",
  "INTEGRATION_TEST": "N/A",
  "LINT": "python3 scripts/run-python-lint.py run ruff",
  "LINT_FIX": "N/A",
  "MUTATION": "N/A",
  "SINGLE_FILE_INTEGRATION": "N/A",
  "SINGLE_FILE_TEST": "N/A",
  "TYPECHECK": "python3 scripts/run-python-lint.py run mypy",
  "UNIT_TEST": "python3 tests/speckit-pro/run-all.py"
}
```

## Autopilot Preflight

- Stage: plan, explicit operator invocation. Draft PR: no_record.
- Workflow binding: resolved in the EDA-001 worktree; feature branch retained.
- Agent installation: 13 user-scope agents matched installed plugin 2.36.2 in a native dry run (`no_op`).
- Quality gates: thresholds file validates; complexity, mutation, and dependency rules remain unconfigured; dependency audit is off.
- Research broker: jev screening; warning search_environment_only_credential.
- Archive sweep: current spec excluded; no other spec proven merged; no cleanup applied.
- G0 technical baseline: passed after bounded privacy repair. Ruff passed; pinned mypy 2.3.1 passed for 47 source files; the full quick suite passed 8,948/8,948. The original interrupted command remains recorded as failed without a test verdict.

## Previous Recovery Checkpoint

- At this checkpoint, planning remained at Phase 0 and no phase agent had started.
- Installed plugin is now 2.36.2; the former 2.36.1 installation is no longer available.
- The original quick-suite native session is unavailable; process inspection found no surviving suite process or terminal test verdict. The app later recovered a native command record with status `failed` and exit code `-1`.
- Execution control required a checkpoint while the original outcome was unknown. The original run identity and counters were preserved. The recovered native failure was bound to the original dispatch; one later corrective cycle was consumed for the privacy repair.
- Recovery action completed: the privacy-scan failure was repaired and a passing G0 result obtained. Execution control returns `continue`.
- No implementation or Post work was performed; those items remain outside the requested plan stage.

### Operator-authorized baseline replacement

The operator explicitly approved installing pinned mypy 2.3.1 in an isolated environment and running a fresh G0 baseline. The original interrupted suite was initially unknown and the replacement was recorded independently. The original was later reconciled as a failed native command; neither result is a passing baseline.

- Approved recovery: pinned mypy 2.3.1 installed in an isolated environment. Type checking passed for 47 source files after granting worktree cache-write permission.
- Replacement quick-suite baseline: finished with exit code 1; 8,945/8,946 tests passed. The sole failure was `test-privacy-scan` (10/11). The original interrupted command is separately recorded as failed without a test verdict.
- Focused diagnostic: `dynamic_local_pattern` includes terms derived from this worktree path. Its failure preview flags ordinary repository text containing words such as "foundational" and "attribute". This is consistent with the documented local path collision; no G0 pass or waiver is claimed.
- Execution ledger: `continue` after app native event `exec-0757115d-63d8-4508-94bc-59e5f342aee0` resolved the original `g0-quick-suite` dispatch as failed (exit code `-1`). Zero corrective cycles consumed; no phase agent dispatched.
- Bounded G0 privacy repair consumed one corrective cycle. The scanner now omits only the `.worktrees` feature-name directory from dynamic identity terms and exempts typed app `exec-` event IDs from its bare-UUID rule. The focused privacy test passed 13/13, and the full post-repair suite passed 8,948/8,948. Ruff, pinned mypy, and docs reference checks passed.

**Operator-authorized Plan recovery:** The user answered “continue,” authorizing the exact wording correction above and remaining plan-stage work. The contract now says “absolute paths, home prefixes, or temporary prefixes.” The original execution ledger and counters remain intact; the refused reservation is not treated as a dispatched repair. Privacy revalidation passed 13/13 (exit 0), and `git diff --check` passed. The elapsed-time checkpoint was refreshed without changing run identity or repair counters. Planning continues with the three domain checklists.

**Supply-chain checklist checkpoint:** The executor returned 28 requirements-quality questions and one unremediated gap (CHK007): the HumanLayer notice contract lacks an explicit pinned public copied-source URL requirement. The URL is already recorded in `research.md`. Read-only consensus is in progress. The shared corrective reservation `checklist-supply-chain-url-repair-1` was refused with `failure_family_budget_exhausted`; no corrective edit was applied.

**Reviewed supply-chain recovery checkpoint:** Named spec-context analysis and named consensus synthesis returned high confidence with no flags. The exact proposal adds the public pinned copied-source URL to FR-014 and `contracts/notices.md`, without changing the closed ledger schema or requiring runtime network access. The Gap remains unresolved because the shared corrective reservation was refused. All dispatches are terminal, unknown effects are empty, and the original run retains one consumed corrective cycle. G4, the other domains, Tasks, Analyze, G6.5, and the plan-stage artifact/draft handoff remain incomplete.

**Operator-authorized plan-stage continuation:** The user explicitly instructed recovery and completion of the plan stage without further stops. This supersedes automatic repair ceilings within the remaining planning scope. The exact named-consensus FR-014 and HumanLayer notice-contract correction has been applied; revalidation is pending. The original run identity, consumed counters, and refused reservations remain recorded. Actual gate outcomes remain authoritative.

**Supply-chain revalidation:** 28 reviewer-owned questions preserved; CHK007 correction confirmed in FR-014 and notice contract. Gap counts are zero across spec, plan, and checklist; no implementation tests ran. Parent Plan estimator returned `status=not_estimated`, `projected=null`, with 11 declared files (2 modified, 9 new) and zero entries classed as production code. This is recorded as no sizing estimate, never a budget pass. The operator-ratified two-slice decision remains the planning basis.

**Data-integrity outcome:** 28 unique, sequential, traceable requirements-quality questions; initial and final gap counts are zero. No requirement correction or consensus dispatch needed. Optional duplicate Git hooks were skipped in favor of parent commits. The vendored prerequisite option mismatch was resolved using supported runner and wrapper contracts; no implementation tests ran.

**Error-handling outcome:** 32 sequential, traceable requirements-quality questions; two planning gaps closed under explicit operator continuation. FR-008/FR-012 and Plan/ledger/notice contracts now require missing-ledger, unparseable-JSON, and missing-notice failures with file-specific diagnostics. FR-010/FR-012 and Plan/credits contract require positive and negative frontmatter-placement fixtures. Count-markers and diff/structure checks pass with zero gaps. No unresolved consensus or implementation tests. The advisory Ripwire test audit reported four planning-prose symbols as untested; it is not an implementation test verdict. All 88 checklist questions retain honest reviewer-owned states.

**Checklist phase boundary:** Parent G3 and G4 each passed with 0 markers after all corrections. The refreshed Plan sizing result is `not_estimated` (same 11 declared files), with no unsupported budget-pass claim. The EDA SPEC-MOC navigation was regenerated and the required elapsed-time checkpoint recorded. Tasks begins from this corrected snapshot.

### Tasks phase boundary evidence

The atomicity verdict classifies the current planning change. It does not revoke Q8's two future implementation PRs. Layer emission is skipped for this non-split planning route; the optional complete compatibility diagnostic is preserved with its actual warnings. Phase 7 is decomposed into 19 concrete task groups, all skipped outside this plan stage.

```json
{
  "g5": {
    "gate": "G5",
    "markers": 0,
    "pass": true,
    "reason": "27 tasks found",
    "task_count": 27,
    "functional_requirements": 19,
    "unmapped_requirements": [],
    "coverage_mode": "explicit references and inclusive FR ranges",
    "task_execution_valid": true,
    "fingerprints": {
      "plan_sha256": "9ce69bf6cbe2151db68d2a2737db593a879149ffbd0489c05ab775a148f23be1",
      "spec_sha256": "52481b25ec692937c47adb4f8db9b0a6d73385ba431ea0ee70160258a738d0d7",
      "tasks_sha256": "18001ad6f6372d494b2590b9ad5f331d91850b53496c322878f729f4d1b5575c"
    }
  },
  "execution_metadata": {
    "sidecar": "specs/eda-001-attribution-foundation/.process/task-execution.json",
    "fingerprints": {
      "plan_sha256": "9ce69bf6cbe2151db68d2a2737db593a879149ffbd0489c05ab775a148f23be1",
      "spec_sha256": "52481b25ec692937c47adb4f8db9b0a6d73385ba431ea0ee70160258a738d0d7",
      "tasks_sha256": "18001ad6f6372d494b2590b9ad5f331d91850b53496c322878f729f4d1b5575c"
    },
    "units": 19,
    "waves": 18,
    "implementation_started": false
  },
  "reviewability": {
    "helper_id": "reviewability-gate",
    "requested_mode": "tasks",
    "status": "deferred",
    "reason": "Installed runner supports setup mode only; tasks mode was not invoked.",
    "fallback_decision": "proceed",
    "fallback_evidence": [
      "Current setup mode pass",
      "Current Plan not_estimated; no budget-pass claim",
      "Operator-ratified two vertical implementation slices from Q8"
    ],
    "fingerprint_status": "current",
    "warning": "Final implementation diff size remains unmeasured; measure each implementation PR."
  },
  "atomicity_route": {
    "hints": [],
    "releasable": true,
    "route": "one-navigable-PR",
    "signals": [
      "change-shape:modify-heavy"
    ],
    "warnings": []
  },
  "layer_plan": {
    "status": "skipped",
    "reason": "Authoritative atomicity-route for the current planning changes is one-navigable-PR. Optional compatibility diagnostic is preserved separately.",
    "diagnostic_evidence": {
      "path": "specs/eda-001-attribution-foundation/.process/layer-plan-diagnostic.json",
      "sha256": "ac4ef7626616d638f7e6a65d86adf116e9ee7263cad736abfd60388efbc90289",
      "status": "ok",
      "task_count": 27,
      "warnings": 32,
      "warning_reason": "Nine declared NEW implementation files do not exist during planning."
    }
  },
  "ratified_future_implementation_prs": {
    "slice_1": "T001\u2013T019: US1+US2 with packaging/checkpoint",
    "slice_2": "T020\u2013T027: US3 with final packaging/checkpoint"
  },
  "repair": "User-authorized format-only producer repair; the refused corrective reservation remains preserved. Layer compatibility diagnostic recognizes all 27 tasks."
}
```

### Analyze phase verification evidence

All required severities were assessed. Initial: 0 CRITICAL, 0 HIGH, 0 MEDIUM, 1 LOW; final: zero at every severity. Native marker counts and required metadata validation passed. Parent G3, G4, G5, and G6 passed after the correction. Coverage is 19/19 FRs, 6/6 success criteria, 3/3 stories; optional suggestions are empty. The complete report is `specs/eda-001-attribution-foundation/.process/analyze-report.md`. Implementation gates remain unrun.

Current native planning fingerprints:

```json
{
  "plan_sha256": "9ce69bf6cbe2151db68d2a2737db593a879149ffbd0489c05ab775a148f23be1",
  "spec_sha256": "52481b25ec692937c47adb4f8db9b0a6d73385ba431ea0ee70160258a738d0d7",
  "tasks_sha256": "e2a555ce5b51b7a50e41bab7ca9b6c1930ffa94b4d95b5189e96183d60d7b390"
}
```

### Final Analyze consensus

No findings remain after the verified Analyze correction. The dedicated `consensus-synthesizer` returned this exact block for the current Analyze pass. Its evidence is the supplied native gates and Analyze report; it does not independently qualify implementation behavior or measured final size.

📊 Confidence: 0.97

- Task understanding: 0.98
- Approach clarity: 0.96
- Requirements alignment: 0.98
- Risk assessment: 0.94
- Completeness: 0.97

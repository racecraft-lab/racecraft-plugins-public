# Feature Specification: Vertical-slice sizing heuristics in PRD/grill-me (PRSG-005)

**Feature Branch**: `prsg-005-slice-sizing-heuristics`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "Vertical-slice sizing heuristics in PRD/grill-me — bake SPIDR + INVEST + vertical-slicing into the two scoping skills (speckit-prd, grill-me) plus a deterministic estimator and one shared reference doc, so the SPEC catalog is born PR-sized. Advisory-only; never blocks."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catalog-level decomposition in speckit-prd (Priority: P1)

A plugin maintainer (or any consuming project) runs `speckit-prd` to turn a raw idea
into a PRD and a technical-roadmap SPEC catalog. The skill decomposes the idea into the
catalog using SPIDR story-splitting and vertical slicing, so the emitted catalog is
composed of thin, end-to-end (vertical) slices *by construction* instead of a few fat
specs that must be split later. For each catalog entry, the skill populates the existing
`Projected reviewable LOC` field from the deterministic estimator and adds a one-line
INVEST/vertical-slice rationale, so the size signal is visible in the roadmap the moment
it is authored.

**Why this priority**: `speckit-prd` is the front door of the chain (PRD → roadmap →
scaffold-spec → autopilot). Right-sizing the catalog here is the cheapest possible moment
to make specs PR-sized — before any spec is scaffolded or any code exists. Without this,
the catalog can be born with fat specs and every downstream phase inherits the problem.
This story alone delivers value: a roadmap whose entries are thin vertical slices with
populated budgets.

**Independent Test**: Run a `speckit-prd` interview on a fixture idea that would naively
become one fat spec, and confirm the emitted catalog is multiple thin vertical slices,
each carrying a `Projected reviewable LOC` populated from the estimator plus a one-line
INVEST/vertical-slice rationale.

**Acceptance Scenarios**:

1. **Given** a raw idea that naively maps to a single large spec, **When** the maintainer
   runs `speckit-prd` to decompose it, **Then** the emitted SPEC catalog contains multiple
   thin vertical slices (each cutting end-to-end through its layers) rather than one fat
   horizontal spec.
2. **Given** `speckit-prd` is producing a catalog entry, **When** it writes that entry,
   **Then** the entry's existing `Projected reviewable LOC` field is populated with the estimated LOC
   returned by the deterministic estimator and carries a one-line INVEST/vertical-slice
   rationale.
3. **Given** the estimator reports a catalog entry over the documented ceiling, **When**
   `speckit-prd` records that entry, **Then** the size signal is surfaced as advisory text
   and the interview continues — nothing is blocked or rejected.
4. **Given** a maintainer types a sizing/slicing phrase such as "right-size the catalog",
   **When** the request is routed, **Then** `speckit-prd` activates, and existing
   `speckit-prd` trigger phrases continue to route to `speckit-prd` unchanged.
5. **Given** the estimator is unavailable while `speckit-prd` is decomposing the catalog
   (missing script, missing `jq`, a non-zero exit, or empty/unparseable output), **When**
   `speckit-prd` records a catalog entry, **Then** it degrades to advisory text, leaves the
   entry's `Projected reviewable LOC` field unpopulated (or noted as unavailable), and continues the
   interview — the unavailable estimate is never converted into a hard stop and the script's
   exit code is never read as a gate.

---

### User Story 2 - Per-spec validation and split in grill-me (Priority: P2)

A maintainer runs `grill-me` to scope a single spec (typically one catalog entry, or an
idea being grilled before `/speckit-specify`). `grill-me` gains a dedicated slice-sizing
branch in its design tree: it runs the deterministic estimator on the single spec's size
signals, and when the result is over the documented ceiling or the spec is horizontally
sliced, it asks a split question via `AskUserQuestion` recommending N thin vertical slices.
The chosen split is recorded in the Design Concept document (Goals / Open Questions) so
that `speckit-scaffold-spec` and `speckit-autopilot` can act on it later.

**Why this priority**: A spec scaffolded straight from a roadmap entry, or an idea grilled
before specify, never passes through `speckit-prd`'s catalog decomposition. `grill-me` is
the per-spec safety net that still catches a fat or horizontally-sliced spec at scoping
time, using its existing human-in-the-loop strength. It is P2 because it complements the
catalog-level decomposition in US1 (the primary right-sizing surface); each story is
independently valuable and testable.

**Independent Test**: Run a `grill-me` interview on a fixture single spec that is fat or
horizontally sliced, and confirm the slice-sizing branch triggers, the estimator runs on
that spec's signals, a split question recommending N vertical slices is asked, and the
chosen split is recorded in the Design Concept document.

**Acceptance Scenarios**:

1. **Given** `grill-me` is scoping a single spec whose estimated size exceeds the
   documented ceiling, **When** the slice-sizing branch runs, **Then** `grill-me` asks a
   split question that recommends N thin vertical slices.
2. **Given** `grill-me` is scoping a single spec that is horizontally sliced (cuts by layer
   rather than end-to-end), **When** the slice-sizing branch runs, **Then** `grill-me`
   recommends re-slicing it into vertical slices.
3. **Given** the maintainer chooses a split in the slice-sizing branch, **When** the
   interview concludes, **Then** the chosen split is recorded in the Design Concept
   document (Goals / Open Questions) for scaffold-spec/autopilot to act on.
4. **Given** `grill-me` is scoping a single spec whose estimated size is at or under the
   ceiling, **When** the slice-sizing branch runs, **Then** it surfaces the size estimate
   as an advisory note and does not force a split.
5. **Given** the estimate is borderline or the estimator is unavailable, **When** the
   slice-sizing branch runs, **Then** `grill-me` degrades to an advisory note and the
   interview continues — the branch never blocks the interview.

---

### Edge Cases

- **Estimate at exactly the ceiling**: the estimator's status boundary (ok vs warn) at
  exactly the documented ceiling must be defined and consistent across both skills. At
  exactly the ceiling `status` is `ok`; `warn` applies only when `estimated_loc` is
  strictly over the ceiling.
- **Malformed, missing, zero, or negative size signals**: the estimator must behave
  predictably (non-crashing) rather than emit a misleading number. Each such signal is
  treated as zero, and `status` then follows the at-ceiling boundary rule on the resulting
  estimate — when every signal is bad/absent the result is `estimated_loc: 0` with
  `status: ok` (at/under the ceiling) — never a misleading `warn` and never a third status
  value. Here `status: ok` means "there is no over-ceiling estimate to flag", not that the
  input was validated as good.
- **SPIDR "Spike" (research-only) slice**: a research-only slice is sized by timebox, not
  LOC, so it is treated as a distinct slice *type* that is exempt from the LOC threshold.
  The estimator accepts an optional input marking the slice as a spike; when set, it skips
  the LOC-threshold comparison and returns `status: ok` with `suggested_slices: 1` and
  `estimated_loc: 0`. Here `status: ok` means "LOC sizing is not applicable to a research
  slice" (the INVEST "Estimable" escape hatch) — not "trivially small" — so a spike never
  trips a misleading `warn` and the advisory-only invariant (FR-011) is preserved.
- **Estimator unavailable mid-interview**: both skills must degrade to advisory text and
  continue; never convert an unavailable estimate or a `warn` into a hard stop. "Unavailable"
  means the estimator cannot produce a usable result for any reason — missing script, missing
  `jq`, a non-zero exit, or empty/unparseable output. In every such case each calling skill
  (`speckit-prd` and `grill-me`) MUST treat the result as an absent estimate, surface an
  advisory note, and continue the interview. A non-zero exit code from the script MUST NOT be
  read by either caller as a gate or hard stop — the caller never uses the script's exit code
  for control flow. (This is the caller-side counterpart to the contract's script-side
  guarantee that a successful estimate, including `warn`, exits `0`; FR-011.)
- **Existing trigger phrases**: adding sizing/slicing phrases must not cause existing
  phrases for either skill to mis-route (no over-trigger or under-trigger regression).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `speckit-prd` MUST decompose an idea into the SPEC catalog using SPIDR
  story-splitting and vertical slicing, so the emitted catalog is composed of thin,
  end-to-end (vertical) slices by construction. *(US1)*
- **FR-002**: For each emitted catalog entry, `speckit-prd` MUST populate that entry's
  existing `Projected reviewable LOC` field with the estimated LOC returned by the deterministic
  estimator, and MUST add a one-line INVEST/vertical-slice rationale to the entry. *(US1)*
- **FR-003**: `grill-me` MUST include a dedicated slice-sizing branch in its design tree
  that runs the deterministic estimator on the single spec's size signals. *(US2)*
- **FR-004**: When the estimator reports the single spec is over the documented ceiling, or
  the spec is horizontally sliced, `grill-me` MUST ask a split question (via its
  human-in-the-loop question mechanism) that recommends N thin vertical slices. *(US2)*
- **FR-005**: When the maintainer chooses a split in `grill-me`, the chosen split MUST be
  recorded in the Design Concept document (Goals / Open Questions) so scaffold-spec and
  autopilot can act on it. *(US2)*
- **FR-006**: A single shared, runtime-agnostic estimator (`estimate-spec-size.sh`,
  bash + jq) MUST accept structured size signals (e.g. number of user stories, number of
  files/surfaces touched, number of functional requirements, new-vs-modify flag) and MUST
  return a result of the form `{estimated_loc, suggested_slices, status}` where `status` is
  `ok` or `warn` relative to the documented ceiling. *(US1, US2)*
- **FR-007**: The estimator MUST be deterministic — identical inputs MUST always produce
  identical output (no clocks, randomness, or environment dependence) — so the same inputs
  yield byte-identical results. *(US1, US2)*
- **FR-008**: The documented LOC ceiling MUST be a single source-of-truth constant used by
  the estimator; both skills and the shared reference doc MUST refer to the same ceiling
  value. *(US1, US2)*
- **FR-009**: Both skills MUST invoke the *same* single copy of the estimator (not per-skill
  copies), referenced via the plugin root path so it is runtime-agnostic. *(US1, US2)*
- **FR-010**: Canonical SPIDR + INVEST + vertical-slicing guidance MUST live in exactly one
  shared reference document; `speckit-prd` and `grill-me` MUST each carry only a short inline
  summary plus a link to that shared document (no duplicated guidance prose). *(US1, US2)*
- **FR-011**: PRSG-005 MUST be advisory-only — it MUST NOT block, gate, reject, or emit
  exit-code/threshold logic at any phase. A `warn` status is informational only; both skills
  MUST continue the interview after surfacing it. *(US1, US2)*
- **FR-012**: PRSG-005 MUST NOT change the technical-roadmap template schema; it MUST reuse
  the existing per-SPEC `Projected reviewable LOC` field and existing entry prose. *(US1)*
- **FR-013**: Trigger changes MUST be limited to adding a few sizing/slicing phrases to each
  skill's description; all existing trigger phrases MUST continue to route as before (no
  over-trigger or under-trigger regression). *(US1, US2)*
- **FR-014**: Every change to a Claude Code skill (`speckit-prd`, `grill-me`) MUST be
  mirrored in its Codex counterpart; the shared reference doc and the shared estimator MUST
  remain single, runtime-agnostic copies used by both runtimes. *(US1, US2)*
- **FR-015**: The shared reference document MUST state that the estimate is an approximate
  *forward* guess made before implementation, NOT the authoritative reviewable-LOC count, so
  users do not over-trust the number. *(US1, US2)*
- **FR-016**: The estimator MUST behave predictably on malformed, missing, zero, or negative
  size signals (non-crashing) rather than emit a misleading estimate. Each such signal MUST be
  treated as zero, and `status` MUST follow the same at-ceiling rule on the resulting estimate
  (all-bad/absent input → `estimated_loc: 0` → `status: ok`), never a misleading `warn` and
  never a third `status` value. *(US2)*
- **FR-017**: The estimator MUST accept an optional input that marks a slice as a SPIDR
  "Spike" (research-only). When set, the estimator MUST skip the LOC-threshold comparison and
  return `status: ok` with `suggested_slices: 1` and `estimated_loc: 0`, rather than sizing
  the slice by LOC. The shared reference document MUST document the spike as a timebox-sized
  slice type (the INVEST "Estimable" escape hatch) and clarify that `status: ok` for a spike
  means LOC sizing is not applicable, not that the slice is small. This MUST NOT introduce any
  new `status` value beyond `ok`/`warn`. *(US1, US2)*

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (two skill SKILL.md prose surfaces + one shared
  reference doc) with a small harness/adapter component (one bash + jq script + its fixture).
- **Secondary surfaces, if any**: Codex skill mirrors for `speckit-prd` and `grill-me`
  (prose parity only; no second script or doc copy).
- **Projected reviewable LOC**: ~200 production LOC (bash + jq script and skill/doc prose),
  excluding test fixtures.
- **Projected production files**: ~6 (one shared script, one shared reference doc, two CC
  SKILL.md edits, two Codex SKILL.md edits).
- **Projected total files**: ~8 (production files plus the estimator's test fixture set and
  this spec/checklist).
- **Budget result**: within budget.
- **Split decision**: Remains one spec. The four skill edits, the shared doc, and the shared
  script are tightly coupled around a single advisory sizing capability and a single shared
  constant; splitting them would create cross-spec coupling without reducing review surface.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue (PRSG-006 for the plan-phase gate;
  PRSG-007/008/009 for the split engine).

### Key Entities *(include if feature involves data)*

- **Size signals (estimator input)**: the structured, pre-implementation size indicators a
  skill collects for a spec — e.g. number of user stories, number of files/surfaces touched,
  number of functional requirements, and a new-vs-modify flag.
- **Size estimate (estimator output)**: `{estimated_loc, suggested_slices, status}` where
  `estimated_loc` is the forward LOC guess, `suggested_slices` is the recommended number of
  thin vertical slices, and `status` is `ok` or `warn` relative to the documented ceiling.
- **Documented LOC ceiling**: the single source-of-truth constant (~400 reviewable LOC) that
  the estimator and the shared reference doc refer to. Shared with PRSG-006 by documentation
  only, not by a consumed artifact.
- **Shared slicing-heuristics reference**: the one canonical document holding SPIDR + INVEST
  + vertical-slicing guidance, summarized inline and linked from both skills.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `speckit-prd` on a fixture idea that would naively be one fat spec
  yields a catalog of multiple thin vertical slices, each with a `Projected reviewable LOC` populated
  from the estimator and a one-line INVEST/vertical-slice rationale.
- **SC-002**: Running `grill-me` on a fixture single spec that is fat or horizontally sliced
  triggers the slice-sizing branch and produces a split recommendation of N vertical slices
  recorded in the Design Concept document.
- **SC-003**: The estimator returns identical (byte-identical) output for identical inputs
  across repeated runs, and its `ok`/`warn` status is correct at and around the documented
  ceiling.
- **SC-004**: No PRSG-005 path blocks, gates, or rejects in any scenario — every `warn` or
  unavailable estimate results in advisory text and a continued interview.
- **SC-005**: The newly added sizing/slicing trigger phrases route to the correct skill, and
  no existing trigger phrase for either skill changes its routing (no over-trigger or
  under-trigger regression).
- **SC-006**: The SPIDR + INVEST + vertical-slicing guidance exists in exactly one document;
  both skills reference it; both Codex mirrors carry the equivalent inline summary + link.

## Assumptions

- The existing technical-roadmap template already carries a per-SPEC `Projected reviewable LOC` field;
  PRSG-005 populates it rather than introducing a new field (Q9).
- The documented LOC ceiling is ~400 reviewable LOC, shared with PRSG-006 as a documented
  constant only; PRSG-005 emits no artifact for a downstream gate to consume (Q3).
- The on-disk home of the shared reference doc and the shared estimator script is a recorded
  Plan-phase (HOW) decision, now locked to: the reference doc at
  `speckit-pro/skills/speckit-coach/references/slicing-heuristics.md` (alongside the existing
  shared reference docs) and the estimator at
  `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh` (alongside the existing
  shared cross-skill runtime scripts `ensure-reviewability-preset.sh` / `project-fixup.sh`),
  both invoked by both skills and both Codex mirrors via `${CLAUDE_PLUGIN_ROOT}` — the same
  shared-asset placement PRSG-002 used for its shared templates under
  `speckit-coach/templates/`. This remains a directional Plan target, not a spec-level (WHAT)
  requirement.
- The exact mechanism by which each skill collects the estimator's structured inputs during a
  free-flowing interview is an implementation detail resolved in Plan/Tasks — `speckit-prd`
  derives the signals from the catalog entry it is drafting, `grill-me` from the single spec
  it is scoping.
- The Codex skill variants use a free-text question-and-answer loop instead of
  `AskUserQuestion`; the split-question mechanism is adapted accordingly while preserving
  behavioral parity.
- Authoritative reviewable-LOC measurement and the plan-phase budget gate are owned by
  PRSG-006 and are out of scope here.

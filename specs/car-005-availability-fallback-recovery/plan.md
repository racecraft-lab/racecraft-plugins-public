# Implementation Plan: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Branch**: `car-005-availability-fallback-recovery` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/car-005-availability-fallback-recovery/spec.md`

**Note**: This plan was produced by `/speckit-plan` against the
`speckit-pro-reviewability` preset plan template (v1.0.0), which overrides the
core template and adds the Declared File Operations section below.

## Summary

Prove bounded route-resolution and recovery semantics synthetically, before
CAR-006 implements the real resolver, by shipping an **executable reference
simulator** plus a **deterministic fixture corpus** that pins how resolution must
behave across every failure mode the Claude routing roadmap mandates.

The approach is the repository's established schema + library + fixture +
unit-test pattern, applied entirely inside the test tree: three JSON Schema
documents in `layer6-efficiency/contracts-claude/`, one simulator module in
`layer6-efficiency/lib/`, one self-contained scenario corpus in a new
`layer6-efficiency/fixtures-fallback/`, and one unit test registered in layer 4 of
`suite-manifest.json`. Zero production files change.

Phase 0 had no clarifications to resolve — the spec arrived with 44 functional
requirements and zero outstanding clarification markers. Research instead verified
every load-bearing precedent the spec cites, all of which held, and surfaced two
constraints the spec did not state:

- **Adding schemas to `contracts-claude/` opts them into an existing CAR-004
  test** that asserts every document in the directory uses only keywords the
  shared validation engine implements. Verified safe — every keyword this feature
  needs is supported (research D2).
- **Durable naming is mechanically enforced**, and `car` is a live spec family, so
  no authored script stem *or test method name* may contain `car-005`
  (research D9).

The one genuinely open design question — whether to write a schema validator or
reuse one — resolved to reuse: the fail-closed engine at
`claude_policy_controls.py:108` already enforces the no-cross-document-`$ref` rule
FR-016 depends on, and CAR-004 set the import precedent (research D1).

Delivery is two vertical slices as a `gh-stack` chain. Slice 1 creates all seven
authored files complete; slice 2 extends exactly three of them additively and
creates none.

## Technical Context

**Language/Version**: Python 3.11+, standard library only (constitution principle
II). No third-party `jsonschema`.

**Primary Dependencies**: none added. Read-only in-tree imports of
`claude_policy_controls` (`validate_instance`, `load_contract`, `CONTRACT_ROOT`,
`ControlContractError`) and `claude_successor_freeze` (`canonical_json`), which is
the same reuse `claude_control_comparison.py:37-48` performs.

**Storage**: files only — committed JSON Schema documents and one committed JSON
fixture corpus. No database, no runtime state, no writes at test time.

**Testing**: `python3 tests/speckit-pro/run-all.py`. One new `unittest` module at
`tests/speckit-pro/unit/test-route-fallback-simulation.py`, registered in the
**layer 4** `scripts[]` array of `tests/speckit-pro/suite-manifest.json`.

**Target Platform**: repository-only validation tree. Cross-platform by
construction — no Bash, no `jq`, no shell dependency (constitution principle II).

**Project Type**: test-harness library plus fixture corpus. Not an application,
not a plugin surface. The simulator is an executable specification, not shipped
code.

**Performance Goals**: N/A. The corpus is seventeen synthetic cases replayed
in-process; the module is a pure function with no I/O in its hot path. Determinism
is the operative property, not speed.

**Constraints**: pure function of (route policy, snapshot projection, overrides,
declared budgets) with no filesystem, network, wall-clock, or randomness input
(FR-001). Canonical JSON serialization — sorted keys, minimal separators — via the
existing `canonical_json`. Additive only: no frozen CAR-002/003/004 schema or
fixture edited, no member added to the shared byte-identical
`layer6-efficiency/contracts/` directory. No `$ref` may leave its own `#/$defs/`.
No authored filename coupled to the spec ID.

**Scale/Scope**: 3 schema documents, 1 simulator module, 1 corpus of 17 cases, 1
unit test, 1 manifest entry, 1 regenerated docs page. 2 user stories, 49
functional requirements, 12 success criteria.

**Reviewability Budget**: Primary surface harness/adapter (Layer 6 efficiency
schemas, fixtures, and reference simulator) with its unit-test surface; secondary
surface seed/config (one `suite-manifest.json` entry). Projected reviewable LOC
**0** by this repository's declared-LOC accounting; projected production files
**0**; projected total files 7 authored plus 1 generated. Budget result: **split
elected on review burden, not gate-forced** — see the dedicated section below.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
One entry per file, each on its own line beginning with a `- ` marker. Slice
allocation and per-file intent are in the Slice Seam table further down — the
parser accepts no trailing text on these lines, so the annotation lives there
rather than here.

- NEW tests/speckit-pro/layer6-efficiency/contracts-claude/route-policy.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts-claude/environment-snapshot-projection.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts-claude/route-resolution-report.schema.json
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py
- NEW tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json
- NEW tests/speckit-pro/unit/test-route-fallback-simulation.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED docs-site/src/content/docs/reference/tests.md

Eight entries: six new authored files, one modified authored file, one regenerated
generated file. The estimator classifies **none** of them as production —
`is_production_file` matches only paths starting `src/`, `app/`, `lib/`, or
`scripts/`, or ending `.ts`/`.tsx`/`.js`/`.jsx`/`.mjs`/`.cjs`/`.sql`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:3811-3812`). Every path here
starts with `tests/` or `docs-site/` and ends `.json`, `.py`, or `.md`, so
`production = 0` and `projected = 0 × 40 = 0`.

`greenfield` evaluates **false**, because `suite-manifest.json` is MODIFIED and is
not excluded-generated, so the thresholds stay 400/800 rather than 600/1200
(`read_only.py:922`). Status will read `pass` — at a projected value of 0 it could
not read anything else.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Assessed against constitution v1.2.0. **Pre-design: PASS. Post-design: PASS.**

| Principle | Assessment |
| --- | --- |
| **I. Plugin Structure Compliance** | Compliant, and specifically exercised: repository-only tests live under top-level `tests/speckit-pro/`, outside the install-facing plugin directory. No plugin component is added. Gate: `run-all.py --layer 1`. |
| **II. Cross-Platform Runtime & Script Safety** | Compliant. All authored code is Python 3.11+ standard library. Zero new Bash, zero `jq`, no package installation, no PowerShell. Deterministic UTF-8 I/O via the existing `canonical_json`. Gate: `run-all.py --layer 4`. |
| **III. Semantic Versioning** | Not engaged. No `plugin.json` is touched, so no version moves. Manual version edits remain prohibited. |
| **IV. Test Coverage Before Merge** | Compliant, and central to the feature. The one new module is registered in layer 4 of `suite-manifest.json`, so it dispatches through the suite rather than only by hand (SC-008). Gate: full `run-all.py`, zero failures. |
| **V. Conventional Commits** | Applies at PR time. Both slice PR titles use `<type>(<lowercase-scope>): <plain English description>` and are validated against the live release-readiness gate before ready-for-review. |
| **VI. KISS, Simplicity & YAGNI** | Compliant. Three schemas, not four (FR-016). One simulator module, not two (FR-033d). One corpus file, not per-slice files (FR-033c). One registered test module, not two (FR-033a). The validation engine is imported rather than rewritten — writing a third copy would be the YAGNI violation. JSON is handled with Python's `json` module throughout, never `jq`. |

### Required plan definitions

**Primary review surface**: harness/adapter — the Layer 6 efficiency schemas,
scenario corpus, and reference simulator, together with the unit-test surface that
exercises them.

**Secondary surfaces**: seed/config — one appended entry in
`tests/speckit-pro/suite-manifest.json`. Plus one regenerated file,
`docs-site/src/content/docs/reference/tests.md`, which is generated and excluded
from review.

**Within the constitutional reviewability budget?** Yes, on every measured axis,
and the measurement is uninformative here. The constitution's thresholds are warn
above 400 reviewable LOC / 6 production files / 15 total files / more than one
primary surface, and block above 800 / 8 / 25 / more than one primary surface. This
feature declares 0 production files, 8 declared entries, and one primary surface.
Projected reviewable LOC is 0. Nothing warns and nothing blocks.

**Split decision**: two vertical slices, User Story 1 then User Story 2, as a
`gh-stack` chain with slice 2 based on slice 1. No follow-up spec is required for
deferred work *within* this feature — nothing is deferred; both slices are in
scope and both land. The named follow-up for the cross-platform mirroring
obligation is **G56R-005**, recorded in the spec's assumptions because that
obligation is not written into G56R-005's own scope text (verified — research D10).

**PR review packet source**: each slice's PR body carries what changed, why,
non-goals, review order, scope budget, traceability mapping each major requirement
and success criterion to changed files and verification evidence, verification
evidence, known gaps, and rollback notes. Each PR states its position in the
stacked chain; slice 2 names slice 1 as its base.

## Reviewability Budget

Stated honestly rather than favourably, because the automated signals here are
blind and it would be easy to imply otherwise.

**No gate measures this surface.** `estimate-reviewable-loc` computes
`projected = production_files × 40` (`read_only.py:926`), and
`production_files` is 0, so it returns 0 with status `pass`. The setup gate
performs no measurement at all — it regex-scrapes the number a human typed into
the roadmap (`read_only.py:850`). The PR-time packet gate thresholds that same
author-declared figure (`pr_emission.py:589-619`).

**Precedent for how little that means**: the immediately preceding sibling spec
CAR-004 had the same primary surface, the same 0 production files, declared 250
reviewable LOC with status ok, and shipped roughly **11,600 artifact lines in a
single pull request** (#401). The declared figure in this repository
systematically excludes fixture JSON, platform-scoped schemas, test-library
modules, and unit tests — which is to say, it excludes this entire feature.

**By artifact lines, which is what a reviewer actually reads**: roughly
**1,900–2,700 in slice 1** and **1,200–1,900 in slice 2** — three schemas
~470–620, the simulator ~550–750 then +350–550, the corpus ~450–600 then +400–550,
the unit test ~450–700 then +350–600. For calibration, the closest existing
analogue, `claude_control_comparison.py`, is 764 lines.

**The split is elected, not forced.** With 0 production files, one slice would
pass every automated gate. The split is chosen on two grounds:

1. **Review burden** — 3,100–4,600 artifact lines in one diff is not reviewable in
   one sitting, whatever the estimator says.
2. **Independent slice value** — slice 1 is independently landable and releasable,
   and is the artifact CAR-006 needs first: the snapshot projection, the report
   contract, and the reason-code vocabulary. CAR-006 can adopt all three even if
   slice 2 never lands.

Because no gate measures this surface, plan-time or PR-time re-estimation
**cannot** overturn the split by returning a smaller number. Only an operator
decision can.

**Recorded roadmap inconsistency**: the CAR-005 roadmap entry declares
`Suggested slices: 1` (`docs/ai/specs/claude-agent-routing-technical-roadmap.md:516`)
while the same roadmap's Progress Tracking row declares "2 vertical slices,
gh-stack delivery" (`:234`). The advisory `estimate-spec-size` formula
(`user_stories × 25 + files × 40 + frs × 15`, `read_only.py:967`) re-run on this
spec's real signals returns **3** suggested slices either way it is counted: the
spec's own figure of 35 functional requirements yields 975, and the literal count
of 49 distinct FR identifiers — the spec carries fourteen lettered
sub-requirements such as FR-012a and FR-033d — yields 1,185. Both exceed the
400-LOC ceiling by more than a factor of two. Nothing in the estimator supports
collapsing to one slice. The Progress Tracking row is correct; the
`Suggested slices: 1` figure is a stale scoping guess from coarser signals.

## Slice Seam

Slice 1 **creates** every file. Slice 2 **extends** exactly three additively and
creates none (FR-033a).

| File | Slice 1 | Slice 2 |
| --- | --- | --- |
| `contracts-claude/route-policy.schema.json` | create — route shape, ordered fallbacks, declared budget fields **and their maxima** | unchanged |
| `contracts-claude/environment-snapshot-projection.schema.json` | create | unchanged |
| `contracts-claude/route-resolution-report.schema.json` | create — `outcome` discriminator with `allOf`/`if`/`then`; both diagnostic `$defs` with inline `code` enums unioned by `oneOf`; four-member sub-reason enum; closed action enum with `minItems: 1`/`maxItems: 3`; attempted routes; dispatch tuple; `optional_helper`; `release_claim_eligible` | **unchanged** |
| `lib/claude_route_fallback.py` | create — canonical serialization, snapshot intake, preferred-then-fallback walk, five-code semantics, `details` sub-reasons | extend — structural pre-pass, budget caps with attempt counting, override handling, helper-unavailable path, no-safe-route remediation |
| `fixtures-fallback/fallback-scenario-corpus.json` | create — nine US1 cases with pinned reports | append eight US2 cases at the tail; existing positions and pinned bytes unchanged |
| `unit/test-route-fallback-simulation.py` | create — resolution semantics, replay byte-identity over the simulator's own serializer, roadmap parity, set equality on both closed enums, inline negative tests for out-of-vocabulary code and out-of-range budget, corpus case-ID uniqueness and self-containment | append the US2 test functions |
| `suite-manifest.json` | modify — append **one** entry to the layer 4 `scripts[]` array | **unchanged** |
| `docs-site/src/content/docs/reference/tests.md` | regenerate (generated; excluded from review) | regenerate |

**Schemas are excluded from the seam entirely.** All three land complete in slice
1 and slice 2 modifies no schema file — strictly stronger than append-only
additivity, and it preserves the directory's unbroken invariant that no contract
document has ever been edited after its introducing commit.

**Why one test module.** Layer 4's `scripts[]` currently holds 62 entries with
`tests/speckit-pro/unit/test-twin-handoff-completeness.py` at the tail (verified).
Slice 1's entry becomes the new tail; a second slice-2 entry would have to add a
comma to slice 1's last line. One module keeps the manifest out of slice 2's diff
entirely.

**Restack rule.** If a slice-2 finding requires changing slice-1 content, that is
evidence the slice-1 contract was wrong: the fix lands on **slice 1's branch** and
the chain restacks. It is never absorbed into slice 2's diff. Slice 1 must be
complete and passing on its own, with nothing stubbed and no deferral marker left
behind for a later slice.

## Project Structure

### Documentation (this feature)

```text
specs/car-005-availability-fallback-recovery/
├── spec.md              # Input (clarified: 49 FRs, 0 markers)
├── SPEC-MOC.md          # Pre-existing navigation note (untouched)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output — precedent verification, 12 decisions
├── data-model.md        # Phase 1 output — field-level schema and corpus design
├── quickstart.md        # Phase 1 output — per-slice validation guide
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

**No `contracts/` directory is created, deliberately.** The core template lists
one, and for most features it would hold the design contracts. Here the design
contracts **are** the three JSON Schema documents, and they land in the test tree
as implementation deliverables at
`tests/speckit-pro/layer6-efficiency/contracts-claude/`. Copying them under
`specs/.../contracts/` would create two sources of truth for the same documents —
precisely the transcription hazard this feature's read-live discipline exists to
prevent (FR-017a). `data-model.md` therefore carries the field-level design, and
the committed schemas remain the single source of their own bytes. No empty
placeholder is created to satisfy a checklist.

Note the naming collision this avoids: a per-feature `specs/<feature>/contracts/`
directory is a `/speckit-plan` design artifact, which is a different thing from
the shared plugin test harness directories at
`tests/speckit-pro/layer6-efficiency/contracts*/`. Only the latter is in play.

### Source Code (repository root)

```text
tests/speckit-pro/
├── suite-manifest.json                        # MODIFIED: +1 layer-4 entry
├── layer6-efficiency/
│   ├── contracts-claude/                      # platform-scoped, 11 existing docs
│   │   ├── route-policy.schema.json                        # NEW
│   │   ├── environment-snapshot-projection.schema.json     # NEW
│   │   └── route-resolution-report.schema.json             # NEW
│   ├── contracts/                             # shared byte-identical — UNTOUCHED
│   ├── fixtures-fallback/                     # NEW directory
│   │   └── fallback-scenario-corpus.json                   # NEW
│   └── lib/
│       └── claude_route_fallback.py                        # NEW
└── unit/
    └── test-route-fallback-simulation.py                   # NEW

docs-site/src/content/docs/reference/tests.md   # REGENERATED (generated)
```

**Structure Decision**: none of the template's three options applies — this is
neither a single application, a web front/back split, nor mobile plus API. The
feature is repository-only validation, so it follows the existing Layer 6
efficiency layout, which the roadmap itself already anticipated: the CAR-005 Key
Files list proposes `layer6-efficiency/fixtures-fallback/` and
`unit/test-route-fallback-simulation.py`
(`docs/ai/specs/claude-agent-routing-technical-roadmap.md:552-554`), matching this
plan exactly.

Placement rationale per directory:

- **`contracts-claude/`** — platform-scoped, not a mirrored twin of
  `contracts-codex-specification/`. The two were never byte-identical: their `$id`
  namespaces differ (`car-00N` versus `g56r-00N`) and their membership diverges in
  both directions. This is what keeps the feature clear of CAR-012's joint-landing
  rule, which is scoped to the **shared** `contracts/` directory whose members are
  verified byte-identical across platforms. SC-005 holds that boundary at zero.
- **`lib/claude_route_fallback.py`** — matches the `claude_*.py` convention across
  the ten existing Claude modules. Capability-named, no spec ID.
- **`fixtures-fallback/`** — follows the existing `fixtures-<topic>` pattern
  alongside `fixtures-controls/` and `fixtures-codex-controls/`. Requires no
  registration: nothing in the tree enumerates fixture directories as a registry
  (research D12).
- **`unit/`** — where all Layer 4 unit coverage lives per constitution principle
  IV.

## Complexity Tracking

> Filled only where a constitutional or specification constraint required a
> justified deviation.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| FR-012a names the action vocabulary `$defs.remediationAction`; it is instead declared inline at `$defs/remediation/properties/actions/items/enum` | FR-016a prohibits bare-enum `$defs` members and states a directory-wide invariant that research verified empirically: **zero** of the eleven documents has a `$defs` member with a top-level `enum`. A `$defs.remediationAction` holding an enum would be the first, breaking the invariant FR-016a exists to protect. The two requirements cannot both be satisfied literally. | Following FR-012a's literal placement was rejected because it forfeits more: FR-012a's emphasis is on *literal strings* and *closure*, both of which inlining preserves — one closed set, one declaration site in the resolution-report schema, and a stable JSON pointer for a set-equality test. Only the `$defs` *name* is lost. An inline enum on array items under a `$defs` object is already an existing shape here (four occurrences). |
| Route `resolved_model` and `effort` are optional, and `fallback_routes` sets no `uniqueItems` | FR-023 requires a fixture whose route omits an explicit model or effort, and FR-020 requires one whose fallback chain revisits an already-attempted route. Both must produce a **diagnostic** from the simulator. | Requiring the fields, or setting `uniqueItems: true`, would make those fixtures fail **schema validation** instead — converting two required diagnostics into validation errors and making FR-020 and FR-023 unsatisfiable. FR-027 is the deliberate inverse case, and the schema honours each requirement where it is asked. |
| Slice 1 declares budget maxima it validates but does not yet enforce behaviourally | FR-027 was retagged to US1 at Clarify: the budget fields are FR-003 (slice 1), and declaring a field's `maximum` is the same schema-authoring act as declaring the field. | Splitting them would make slice 2 reopen a slice-1 schema for a one-keyword change, which FR-033b forbids and which would break the directory's never-edited-after-introduction invariant. The co-location is universal here — every numeric constraint shares the object literal with its field's `type`, with zero counterexamples. |

No constitutional principle is violated. The `$defs.remediationAction` row is a
deviation from a specification requirement, not from the constitution, and is
reported to the operator rather than absorbed silently.

## Phase Status

- [x] Phase 0 — research complete: `research.md`, 12 decisions, all spec-cited
      precedents verified, 0 open questions
- [x] Phase 1 — design complete: `data-model.md`, `quickstart.md`; no
      `contracts/` directory, with the reason recorded above
- [x] Constitution Check re-evaluated post-design: PASS
- [ ] Phase 2 — `tasks.md` (produced by `/speckit-tasks`, not by this command)

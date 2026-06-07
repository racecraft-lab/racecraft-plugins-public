# Implementation Plan: Plan-phase reviewability budget + gate threshold rework (PRSG-006)

**Branch**: `prsg-006-reviewability-budget` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/prsg-006-reviewability-budget/spec.md`

**Design concept (source of truth for scoping):** `docs/ai/specs/.process/PRSG-006-design-concept.md` (Q1–Q10)

## Summary

Make reviewable-PR sizing **preventive** (decided at plan time) rather than **detective**
(blocked at an end-stage gate), correct the gate's size metric, and replace the defeated
three-phrase keyword escape hatch with a typed, fail-closed exception pragma.

Technical approach: **two deterministic bash+jq scripts**.

1. **NEW** `estimate-reviewable-loc.sh` — a standalone plan-phase estimator the autopilot
   plan phase invokes directly. It parses a delimited declared-files block in `plan.md`,
   projects production-LOC via a per-file constant, applies the 1.5× greenfield allowance
   when every declared file is new, and emits a three-value status (`pass`, `over_budget`,
   `not_estimated`). It never blocks (US1, FR-001…007, FR-015).
2. **Reworked** `reviewability-gate.sh` — its `setup`/`tasks`/`diff` modes stay (no 4th
   mode). Changes: LOC counts production files only; a 1.5× greenfield allowance; the
   primary-surface-count blocker becomes a warning; and a single shared exception matcher
   honors only `Reviewability-Exception: {refactor|infra|upgrade}` on added Markdown lines,
   replacing the legacy keyword at all three modes (US2, FR-008…013).

The roadmap template's Reviewability Contract is updated to match the reworked gate
(FR-014), and the autopilot plan-phase wiring is mirrored into the Codex skill surface
(FR-015). The scripts and the roadmap template stay single-copy (runtime-agnostic).

**Bootstrapping note:** this autopilot's OWN plan phase does NOT run the plan-phase budget
— the estimator is the thing being built and does not exist yet. The Reviewability Budget
line below is filled by hand against the legacy template format for cutover continuity.

## Technical Context

**Language/Version**: Bash (macOS/Linux POSIX shell), `set -euo pipefail`

**Primary Dependencies**: `jq` only. No new dependency (CLAUDE.md rule 2; constitution II).
`git` (already required) for `diff`-mode add-status and numstat.

**Storage**: N/A — stateless scripts emitting JSON to stdout. Records are written into
`plan.md` / the workflow record by the plan-phase wiring, not by the estimator itself.

**Testing**: shell-script test layers — L1 structural, L3 functional eval, L4 script-unit
(determinism + behavior fixtures), L8 Codex Path-A/Path-B parity. Run from `speckit-pro/`:
`bash tests/run-all.sh --layer 1` and `--layer 4` (deterministic, CI). **No L7** — PRSG-006
adds no new agent.

**Target Platform**: developer/CI shell; the speckit-pro plugin runtime (Claude Code + Codex).

**Project Type**: Claude Code plugin (skills + scripts + templates). No product code.

**Performance Goals**: not latency-sensitive. Determinism is the hard requirement: identical
input → byte-identical stdout (constitution II).

**Constraints**: deterministic scripting only (no LLM reasoning in the measured number);
over-budget is **advisory** at plan phase (blocking/re-slicing is PRSG-010); reuse the gate's
existing `is_production_file` / `is_excluded_generated` predicates as-is.

**Scale/Scope**: ~2 scripts (1 new, 1 reworked), 1 template block, 4 skill-doc files
(2 Claude + 2 Codex), plus L1/L4 fixtures. Diff is intentionally small and reviewable.

**Reviewability Budget**: Primary surface = harness/adapter (plugin scripts under
`speckit-pro/skills/...`); projected reviewable LOC ≈ 250–400 (gate rework + new estimator,
hand-estimated — see Known limitation below); production files (by `is_production_file`) = 0
on this repo because plugin code is `.sh` under `speckit-pro/skills/` which the predicate does
not match (PRSG-001 scope; recorded, not fixed here); total files ≈ 11; budget result =
**within budget** (advisory; single primary surface). This line uses the legacy template
format because the estimator does not yet exist to compute it.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan verdict |
|-----------|-------------|--------------|
| I. Plugin Structure | New script lives under an existing skill's `scripts/`; no new plugin dir; `.md` skill docs keep their shape | PASS — `estimate-reviewable-loc.sh` joins `speckit-autopilot/scripts/`; no structural change to plugin layout |
| **II. Script Safety** | `#!/usr/bin/env bash` + `set -euo pipefail` first executable line; quoted vars; `bash -n` clean; `chmod +x`; bash+jq only, no new dependency | PASS by design — new script mirrors the gate's header/style; **the determinism fixture asserts a KNOWN LOC value** (not just two-run equality) per FR-002 |
| **IV. Test Coverage Before Merge** | New bash script gets an L4 unit test; new/changed components pass L1; `bash tests/run-all.sh` green before merge | PASS by design — new L4 determinism + status fixtures for the estimator; extend `test-reviewability-gate.sh` for the reworked metric/surface/exception; L1 asserts script exists + template vocabulary matches gate + `validate-codex-skills`; L3/L8 recorded developer-local before merge |
| **VI. KISS / YAGNI** | Simplest approach; no speculative features; flat sequential shell | PASS by design — **all three exception classes flip a block equally** (no per-class budgets); **one** tunable greenfield factor; **one** shared exception matcher reused across modes; no 4th gate mode; reuse existing predicates rather than reinvent |
| III. Semantic Versioning | No manual version edit (release-please owns it) | PASS — N/A to this change |
| V. Conventional Commits | PR title `feat(speckit-pro): …` plain-English | PASS — handled at PR creation, not in this phase |

**Gate result: PASS.** No violations → Complexity Tracking table left empty. The three
load-bearing gates (II script safety, IV test coverage, VI KISS) are satisfied by the
design choices recorded here and re-verified at G7 (post-implementation) against
`bash tests/run-all.sh`.

## Plan-phase decisions the spec deferred to Plan

The spec (§Deferred) deferred three decisions to this phase. Resolved below.

### Decision 1 — `plan.md` declared-files parse convention (REQUIRED deterministic; FR-001/006)

**Decision: a dedicated, explicitly-delimited block under a fixed heading, one
repo-relative path + status token per line. NOT a free-prose scan of the Project Structure
tree.**

Convention (the estimator reads exactly this):

```text
## Declared File Operations

<!-- PRSG-006 estimator block. One entry per line: STATUS<TAB-or-spaces>repo-relative-path
     STATUS ∈ {NEW, MODIFIED}. Lines not matching the entry grammar are ignored. -->

- NEW speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh
```

Estimator entry grammar (the only lines counted), POSIX ERE via `grep -E`:
`^[[:space:]]*[-*][[:space:]]+(NEW|MODIFIED)[[:space:]]+([^[:space:]]+)[[:space:]]*$`

Rationale (why a delimited block, not the existing tree):
- **`is_production_file` keys on path *prefixes OR extensions*** (`reviewability-gate.sh:59-65`:
  `src/*|app/*|lib/*|scripts/*|*.ts|...`). A free-prose tree scan yields leaf-only names
  (`foo.sh`) with no prefix → production classification silently collapses. Full
  repo-relative paths are mandatory; a delimited block is the way to guarantee them.
- **`not_estimated` must be unambiguous (FR-003).** A freeform-tree parse makes "absent"
  fuzzy and free-prose path matching is provably noisy (it matches tokens like
  `KISS/YAGNI`, per the spec). A dedicated block makes presence/absence **binary**: zero
  matching entries ⇒ `not_estimated` (never a false within-budget `pass`).
- **FR-006 needs a per-file new-vs-modified token** — the `STATUS` field supplies it
  directly; greenfield iff every counted entry is `NEW`.

**Template impact (the spec's second deferred sub-decision — resolved YES):** to make autopilot
plan runs emit this block, the **reviewability-preset plan-template** gains a `## Declared File
Operations` stub prompting for the entries. This IS a required edit, flagged as the **minor
plan-tooling surface note**. It is bounded to the reviewability-preset's plan-template only: it
does NOT touch the general SpecKit plan-template (`.specify/templates/plan-template.md`), and it
does NOT extend to PRSG-010 (hatch) or PRSG-011 (migration). The roadmap-template edit (FR-014)
remains the only template change the spec *pre-commits*; this preset plan-template stub is the
plan-tooling surface note the spec's Deferred item authorized this phase to settle. *Which PR
ships the stub* (this feature's PR vs. a follow-up) is a secondary tasks-phase sequencing call —
not a question of whether. The estimator is robust to the stub's absence regardless: a `plan.md`
with no block records `not_estimated` (FR-003), so the feature degrades gracefully on legacy/thin
plans and never vacuously passes.

> Note: the example `- NEW …` / `- MODIFIED …` lines in the fence above are themselves
> grammar-matchable (same line-scoped class as the documented fenced-pragma limitation). Harmless
> here — this autopilot's plan phase does not run the estimator against this plan.md — but worth
> knowing before ever pointing the estimator at a doc that contains illustrative entries.

### Decision 2 — single shared exception matcher (fixed by FR-011/012; encoded, not re-litigated)

One shared function `match_exception_pragma` (POSIX ERE via `grep -E`, never bash `[[ =~ ]]`
over multi-line strings, never BRE), reused by all three gate modes. Canonical matcher:

`^[[:space:]]*Reviewability-Exception:[[:space:]]+(refactor|infra|upgrade)[[:space:]]*$`

- Line-anchored, **case-sensitive**, exact-enum, no trailing content (the trailing
  `[[:space:]]*$` rejects `refactor # ok` and absorbs a CRLF `\r`).
- `setup`/`tasks` modes apply it to file lines directly (replacing the legacy
  `grep -Eiq 'transition exception|split exception|ratified exception'` at lines 160 & 201).
- `diff` mode (replacing the legacy `git diff … | grep -Ei …` at line 231) **isolates added
  lines first** so the unified-diff `+++ b/<file>` header cannot satisfy the matcher:
  `git diff "$range" -- '*.md' | grep '^+' | grep -v '^+++' | sed 's/^+//'` then apply
  `match_exception_pragma`. A pragma on a context or removed line does NOT flip; because the
  gate runs `merge-base..HEAD`, a pragma the branch introduced appears as an added line and
  IS honored, while a base-branch pragma appears as context and is NOT.
- Fail-closed: any class outside the closed set, a mis-cased class, or a missing pragma leaves
  the result `block`. Legacy phrases are honored by no mode.

### Decision 3 — estimator three-value status (fixed by FR-003; encoded)

`status ∈ {pass, over_budget, not_estimated}`. `not_estimated` ⇒ `projected: null` (an
unmeasured plan is never recorded as within-budget). The estimator NEVER exits non-zero on a
budget verdict; non-zero exit is reserved for usage/IO errors (see contracts).

## Architecture

### Two scripts, not a 4th gate mode (Q2)

```text
speckit-pro/skills/speckit-autopilot/scripts/
├── reviewability-gate.sh         # reworked: setup | tasks | diff (UNCHANGED topology)
└── estimate-reviewable-loc.sh    # NEW: plan-phase estimator, separate entry point
```

The gate's mode topology is frozen (FR-007) — no `plan` mode is added. FR-007 governs
**topology**, not exception-detection logic; US2 explicitly reworks the in-mode internals
(metric, surface, exception) per FR-008/009/010/011/012/013.

### Reuse, don't reinvent

The estimator and the reworked gate share these existing gate functions/predicates
(`reviewability-gate.sh`): `is_production_file` (:59), `is_excluded_generated` (:48),
`surface_for_path` (:34), the `emit_result` JSON shape (:80), and the warn=400/block=800
constants (:19,:22). The estimator carries its own **per-file** production-LOC constant
(the gate's `×40` at :199 is **per-task**, a `tasks.md` line count — NOT per-file), with a
keep-in-sync comment per FR-007.

### The per-file LOC constant + keep-in-sync (FR-007)

```bash
# estimate-reviewable-loc.sh
# PROD_LOC_PER_FILE: projected production-LOC per declared production file.
# KEEP IN SYNC with reviewability-gate.sh measure_feature_dir() per-task ×40 heuristic
# (same magnitude, different unit: that one is per-tasks.md-line, this is per-file).
# These are deliberately NOT a shared variable — see PRSG-006 spec FR-007.
PROD_LOC_PER_FILE=40
```

The literal comment token `KEEP IN SYNC with reviewability-gate.sh` (and a reciprocal
`KEEP IN SYNC with estimate-reviewable-loc.sh` marker added beside the gate's `×40` site at
`reviewability-gate.sh:199`) is the greppable marker the L1 drift-guard asserts is present in
both files (see Test strategy → L1). The L1 check is **comment-presence only** — it does NOT
compare the two numeric values, because they carry different units (per-task vs per-file) and
the per-file value is tunable. (`40` chosen to reuse the established magnitude; whether it stays
`40` or is tuned is a tasks/implement detail — the fixed requirement is determinism, FR-002.)

### Gate rework sites (line numbers, current `reviewability-gate.sh`)

| FR | Change | Current site |
|----|--------|--------------|
| FR-008 | `diff`-mode LOC counts production files only | `reviewable_loc_from_numstat` :67 sums ALL non-excluded additions → also gate on `is_production_file` |
| FR-009 | 1.5× greenfield allowance (warn 400→600, block 800→1200) | new helper using `git diff --name-status --no-renames "$range"`; greenfield iff every non-excluded changed path is add-status `A`; scale thresholds in `emit_result` |
| FR-010 | surface-count: warning only, blocker removed | keep :90-92 (warning); **delete :97** (blocker); JSON still reports `primary_surface_count` + `primary_surfaces` |
| FR-011/012/013 | one shared `match_exception_pragma`; replace legacy at all 3 modes; added-lines-only in diff | replace legacy greps at :160 (setup), :201 (tasks), :231 (diff) |

**Greenfield in `emit_result`:** the cleanest KISS approach is to compute a greenfield boolean
in each measure-* function and pass it into `emit_result`, which scales `WARN_LOC`/`BLOCK_LOC`
by 1.5× locally before the threshold comparisons (and reports the applied thresholds in the
JSON `thresholds` block). `--no-renames` is pinned so an ambient `diff.renames` config cannot
vary the boolean (FR-009).

### JSON output naming note (recorded for tasks/implement)

The current gate emits a legacy key `transition_exception` (:133). The reworked gate honors a
typed pragma; the contract (below) standardizes on `exception_honored` (boolean) +
`exception_class` (the matched class or null). Whether to **rename** `transition_exception` or
**add** the new fields alongside it is a tasks-phase call constrained by the L4 fixtures — the
contract documents the target shape; the existing L4 assertions on `transition_exception` must
be updated in lockstep (FR-013 removes the legacy semantics, so a stale key asserting the old
behavior would be misleading).

### Plan-phase wiring (US1, Q3) — autopilot SKILL.md + phase-execution.md

The Claude autopilot plan phase gains a step: after `plan.md` exists, invoke
`estimate-reviewable-loc.sh <plan.md>`. On `pass` → log "within budget" + record in the
workflow/plan record (silent, no prompt). On `over_budget` in an **autonomous** run → record an
over-budget note and **continue** (advisory, non-blocking). On `over_budget` **interactively**
→ surface the decision to the human. On `not_estimated` → record "not estimated (no declared
production files)" and continue. **No hard block, no re-slicing** (that is PRSG-010 — Q3,
non-negotiable sequencing).

**The wiring MUST read the estimator's exit code and branch on it — it MUST NOT let a non-zero
exit propagate and abort the run.** The three budget statuses (`pass`, `over_budget`,
`not_estimated`) all return exit 0 with the verdict in JSON `status` (see
`contracts/estimate-reviewable-loc.output.md`), so they are read from `status`. A **non-zero
exit (exit 2: usage error or an unreadable/absent `plan.md`)** is the only non-success path and
MUST be handled non-fatally: record an "estimator could not run (exit N)" note and **continue**
the autonomous run. Because the autopilot harness runs under `set -euo pipefail`, the invocation
MUST be guarded (e.g. capture the exit code rather than letting `set -e` abort — invoke in a form
that does not trip `errexit`, such as `code=0; estimate-reviewable-loc.sh "$plan" || code=$?`) so
that an estimator error degrades to a recorded note, never a crashed run. This matches the
established gate-handling pattern in `phase-execution.md` (the G6/G6.5 steps read the gate's exit
code and branch on it rather than aborting). Advisory-and-never-crash is the invariant for the
entire plan-phase budget step: no estimator outcome — under-budget, over-budget, unmeasured, or
errored — may block, prompt mid-autonomous-run, or crash the run.

### Codex parity (FR-015, Q10)

Mirror ONLY the plan-phase budget instruction into
`codex-skills/speckit-autopilot/{SKILL.md, references/phase-execution-codex.md}`. The scripts
(`reviewability-gate.sh`, `estimate-reviewable-loc.sh`) and the roadmap template are
runtime-agnostic and stay **single-copy** — not mirrored. `validate-codex-skills.sh` (L1) + L8
parity cover the mirrored wording.

## Test strategy (L1 / L3 / L4 / L8 — no L7)

**L1 structural** (`tests/run-all.sh --layer 1`, CI):
- `estimate-reviewable-loc.sh` exists and is executable; `bash -n` clean.
- The roadmap template's Reviewability Contract advertises the production-LOC thresholds,
  surface-count-as-warning wording, and `Reviewability-Exception: <class>` vocabulary that the
  gate honors (template↔gate consistency — SC-007).
- **Keep-in-sync drift guard (FR-007):** the keep-in-sync comment marker for the
  production-LOC-per-file constant is present in BOTH `estimate-reviewable-loc.sh` and
  `reviewability-gate.sh`. This is a **comment-presence** assertion (matching the repo's
  existing comment-only keep-in-sync precedents), NOT a numeric value-equality check — the
  two constants differ in unit (per-task vs per-file) and the estimator's value is tunable,
  so equality would false-fail on a legitimate tune. The assertion guards that the
  drift-warning comment cannot be silently deleted.
- `validate-codex-skills.sh` passes after the Codex mirror edit.

**L4 script-unit** (`tests/run-all.sh --layer 4`, CI) — the real contract here:
- **Estimator determinism fixture (FR-002, SC-001):** a representative non-empty
  `## Declared File Operations` block; assert the parsed planned-file count AND projected
  production-LOC equal a **KNOWN expected value** (not merely two-run equality), then assert a
  second run is byte-identical.
- **Estimator status fixtures:** under-budget → `pass`; over-budget → `over_budget` (and the
  run-continue contract: exit 0, advisory); no/garbage block → `not_estimated` + `projected:
  null`; all-`NEW` block → greenfield 1.5× applied.
- **Gate metric fixture (SC-003):** a slice whose production additions < 400 but total (with
  docs/tests) > 400 → no warn.
- **Gate greenfield fixture (FR-009):** all add-status `A` non-excluded → 1.5× thresholds; one
  modified non-excluded file → no multiplier; a modified lockfile alone still greenfield.
- **Gate surface fixture (SC-004):** multi-surface → warning, 0 surface-attributable blocks,
  surface count + list retained in JSON.
- **Gate exception fixtures (SC-005/006) — the bypass list from spec §Edge Cases, each MUST
  NOT flip:** class outside the set; partial/extended (`refactoring`, `ref`, `refactor,infra`);
  case variant (`Refactor`, `REVIEWABILITY-EXCEPTION:`); trailing content (`refactor # ok`); no
  space after colon; pragma on a context/removed line; pragma only in PR body/commit message;
  the `+++ b/<path>` header resembling the pragma; a legacy phrase with no typed pragma. And the
  positive: a valid pragma on an added `.md` line MUST flip the block.
- **Known-limitation residual (recorded, not asserted-as-desired):** a valid pragma inside a
  fenced code block in a committed `.md` WOULD flip (line-scoped, not Markdown-aware) — section-
  scoping is deferred to PRSG-010; the fixture records this residual.

**L3 functional eval** (developer-local, `claude -p`): the autopilot plan phase auto-approves
under budget (silent pass) and records/surfaces when over.

**L8 Codex parity** (developer-local): Path-A/Path-B parity around the mirrored plan-phase
wording.

## Files changed → user story + Codex parity map (FR-015)

| File | Change | Story | Codex parity |
|------|--------|-------|--------------|
| `speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh` | NEW estimator | US1 | single-copy (runtime-agnostic) |
| `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` | rework: prod-LOC metric, 1.5× greenfield, surface→warning, shared typed-pragma matcher at all 3 modes | US2 | single-copy (runtime-agnostic) |
| `speckit-pro/skills/speckit-autopilot/SKILL.md` | wire plan-phase budget step (Q3) | US1 | mirrored → `codex-skills/.../SKILL.md` |
| `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | plan-phase budget step detail | US1 | mirrored → `references/phase-execution-codex.md` |
| `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | mirror plan-phase wording only | US1 | (is the mirror) |
| `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` | mirror plan-phase wording only | US1 | (is the mirror) |
| `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | Reviewability Contract → reworked thresholds/surface-warning/typed pragma (FR-014) | US2 | single-copy (runtime-agnostic) |
| `speckit-pro/tests/layer4-scripts/test-reviewability-gate.sh` | extend for reworked metric/surface/exception | US2 | n/a (test) |
| `speckit-pro/tests/layer4-scripts/` (new estimator test) | determinism + status fixtures | US1 | n/a (test) |
| `speckit-pro/tests/layer1-structural/` | script-exists + template-vocab asserts | US1+US2 | n/a (test) |
| (optional, tasks-phase call) reviewability-preset plan-template | add `## Declared File Operations` stub | US1 | single-copy |

## Out-of-scope guardrails (do not cross — design-concept Non-goals)

No split-PR emission, no hard plan-phase block, no re-slicing wiring (PRSG-007/008/009/010);
no legacy keyword migration of existing roadmaps (PRSG-011); no broadening of
`is_production_file` to `.sh` plugin paths (PRSG-001 — preserve as a documented known
limitation in the estimator code comment); no `is_excluded_generated()` `.process/` realignment
(PRSG-001); no per-class exception budgets (YAGNI). Any task drifting into these is flagged
out-of-scope.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-006-reviewability-budget/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature spec (FR-001…015)
├── contracts/           # Estimator + gate JSON output shapes (Phase 1 output)
│   ├── estimate-reviewable-loc.output.md
│   └── reviewability-gate.output.md
└── tasks.md             # /speckit-tasks output (NOT created here)
```

`research.md` — not generated: no genuinely open decision remains (the one open decision,
the parse convention, is resolved above with primary-source rationale, not external research).
`data-model.md` — N/A: no data model (stateless scripts). `quickstart.md` — N/A.

### Source Code (repository root)

```text
speckit-pro/
├── skills/
│   ├── speckit-autopilot/
│   │   ├── SKILL.md                          # plan-phase budget wiring (US1)
│   │   ├── references/phase-execution.md     # plan-phase budget step (US1)
│   │   └── scripts/
│   │       ├── reviewability-gate.sh         # rework (US2)
│   │       └── estimate-reviewable-loc.sh    # NEW (US1)
│   └── speckit-coach/
│       └── templates/technical-roadmap-template.md   # Reviewability Contract (US2/FR-014)
├── codex-skills/speckit-autopilot/
│   ├── SKILL.md                              # mirror plan-phase wording (FR-015)
│   └── references/phase-execution-codex.md   # mirror plan-phase wording (FR-015)
└── tests/
    ├── layer1-structural/                    # L1 asserts
    └── layer4-scripts/test-reviewability-gate.sh   # extend; + new estimator test
```

**Structure Decision**: existing speckit-pro plugin layout, unchanged. The new estimator
joins the existing `speckit-autopilot/scripts/` directory; no new plugin, no new test layer.

## Complexity Tracking

> No constitution violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

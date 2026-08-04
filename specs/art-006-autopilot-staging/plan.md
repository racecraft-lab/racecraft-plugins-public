# Implementation Plan: Autopilot Staging

**Branch**: `art-006-autopilot-staging` | **Date**: 2026-08-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-006-autopilot-staging/spec.md`

## Summary

Give the autopilot a first-class `--stage` argument over a closed three-token
vocabulary (`plan`, `implement`, `full`), bound the phase loop to the resolved
stage, and record the resolution durably in the workflow file so a fresh session
in a different working copy can cross the boundary.

The technical approach is one shared resolver plus two thin platform surfaces.
Resolution — argv parsing, conflict rejection, workflow-file auto-detection, and
the mirror comparison — lands once as a **registered runner operation**,
`resolve-autopilot-stage`, alongside `resolve-confidence-mode` in
`speckit-pro/speckit_pro_runner/helpers/read_only.py:1081` and
`helpers/registry.py:171`. Both distributions reach it by operation identifier at
the same opening-preparation step, so parity comes from one executable rule
rather than two prose descriptions that nothing compares
(spec.md:281-297, spec.md:466-467).

Enforcement reuses two shipped checks rather than adding a third. The in-run
half becomes a new problem key in the phase-coverage guard
(`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:238`),
registered inside the `status-evidence` rule tuple the autopilot already invokes
(`speckit-pro/skills/speckit-autopilot/SKILL.md:398`) so it can actually change
the exit code. The agent-independent half extends
`tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py:284`,
which already sweeps every `docs/ai/specs/.process/*-workflow.md` in CI.

## Technical Context

**Language/Version**: Python 3.11+, standard library only. No new Bash or `jq`
dependency (constitution §II).

**Primary Dependencies**: none added. The change reaches only
`speckit_pro_runner` (stdlib), the two shipped skill trees, and the repository
test suite.

**Storage**: two Markdown/JSON files on disk. The workflow file
(`docs/ai/specs/.process/<ID>-workflow.md`) is the authoritative durable store,
holding the stage in the `Stage` row of `### Basic Information`;
`<workflow-dir>/autopilot-state.json` mirrors it for the running session only
(spec.md:191-199).

**Testing**: `python3 tests/speckit-pro/run-all.py`. Layer 1 structural
validators under `tests/speckit-pro/layer1-structural/`, Layer 4 unit tests with
golden fixtures under `tests/speckit-pro/unit/`. Layer membership and dispatch
are declared in `tests/speckit-pro/suite-manifest.json`, which is the only
dispatch roster (constitution §IV).

**Target Platform**: two agent distributions from one source tree — Claude Code
(`speckit-pro/skills/`) and Codex CLI (`speckit-pro/codex-skills/`) — plus the
shared runner package installed with both.

**Project Type**: agent-orchestration plugin (harness/adapter surface). No
application runtime, no service, no UI.

**Performance Goals**: not applicable. Stage resolution is one file read and a
table scan at opening preparation, executed once per run.

**Constraints**: Codex `SKILL.md` body is capped at 8000 words by
`tests/speckit-pro/layer1-structural/validate-codex-skills.py:168-171`; the body
measures **7671 words today (headroom 329)**, re-measured 2026-08-04 with the
module-level `body()` in `tests/speckit-pro/lib/structural_helpers.py:44`. Codex
changes are additive only, and four string-pinned sentences must survive verbatim
(spec.md:309-312). Editing either `SKILL.md` dirties the generated distribution
mirrors, the installed-cache fixtures, and the runner trust metadata.

**Scale/Scope**: one capability across 11 shipped-source files and 6 repository
test files; 57 existing workflow files in the tree must keep validating, and all
but one of them carry no `Stage` entry (spec.md:206-210).

**Reviewability Budget**: primary surface harness/adapter (single); secondary
docs/process; projected reviewable LOC 430; production files 0 (estimator
classification — 11 shipped-source files change, none of which the estimator's
`src/`/`app/`/`lib/`/`scripts/`/TS/JS/SQL heuristic at
`speckit-pro/speckit_pro_runner/helpers/read_only.py:3939-3940` counts as
production); total files 17; budget result **warn, within budget, one slice** —
over the 400-LOC warn line by 30, under every block line (800 LOC, 25 total
files, one primary surface). Derivation in
[research.md §D9](./research.md#d9--reviewability-re-estimate-at-g3).

## Declared File Operations

The plan-phase reviewability estimator parses this block to project the slice's
footprint before `tasks.md` exists. Authored files only — generated mirrors are
enumerated separately below and are excluded per spec.md:356-358.

- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md
- NEW tests/speckit-pro/unit/test-autopilot-stage-resolution.py
- NEW tests/speckit-pro/unit/fixtures/read-only-helpers/requests/resolve-autopilot-stage.json
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
- MODIFIED tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json
- MODIFIED tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py
- MODIFIED tests/speckit-pro/suite-manifest.json

### Declared generated artifacts (excluded from the count)

Refreshed by `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py`,
never hand-edited (root `AGENTS.md`, "Editing Boundaries"):

- `dist/claude/**` and `dist/codex/**` — rebuilt install payloads
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/**` —
  content-synced from the rebuilt payloads
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and
  `.sha256` — recomputed by `scripts/refresh-release-artifacts.py:342-356`,
  which rglobs `*.py` under the package, so a changed runner module is picked up
  automatically
- `docs/ai/specs/.process/XPLAT-009-*.json` proof and evidence files
- `docs-site/src/content/docs/reference/tests.md` — regenerated separately by
  `pnpm --dir docs-site reference:generate`, required because a tracked `.py`
  file under `tests/speckit-pro/` changes (`tests/speckit-pro/AGENTS.md`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Assessment |
|---|---|---|
| I. Plugin Structure Compliance | `run-all.py --layer 1` | **PASS.** No new plugin component. The new test lives under `tests/speckit-pro/unit/`, outside the install-facing plugin directory, as the principle requires. |
| II. Cross-Platform Runtime & Script Safety | `run-all.py --layer 4` | **PASS.** All new logic is Python 3.11+ stdlib inside the existing runner package. No Bash, no `jq`, no new script file; the resolver is a registered operation, not a `.sh`. |
| III. Semantic Versioning | Layer 1 `validate-plugin` | **PASS.** No manual version edit; release-please owns the bump. |
| IV. Test Coverage Before Merge | `run-all.py` | **PASS.** New runner logic gains Layer 4 coverage in `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`, registered in `tests/speckit-pro/suite-manifest.json`. |
| V. Conventional Commits | CI `validate-pr-title` | **PASS.** Per-phase commits and the plan-stage terminal commit use `type(scope): description` with the `speckit-pro` scope. |
| VI. KISS, Simplicity & YAGNI | Plan review | **PASS with a recorded trade-off.** No new module, no wrapper layer: the resolver is a function set beside `resolve_confidence_mode` in the existing helper module, and the guard imports it rather than restating the rule. See [research.md §D2](./research.md#d2--how-the-guard-consumes-the-resolver). |

### Reviewability governance (required for all specs)

- **Primary surface**: harness/adapter — the autopilot orchestration contract and
  its shared runner logic. **Secondary surfaces**: docs/process, the two
  distributions' reference documents. One primary surface, which is the single
  dimension the constitution treats as an unconditional blocker.
- **Budget position**: projected reviewable LOC 430 against a 400 warn / 800
  block threshold; total files 17 against 15 warn / 25 block. **Warn on two
  dimensions, block on none.** The scaffold-time setup gate returned the same
  posture (`status: warn`, `pass: true`, `blockers: []`,
  `docs/ai/specs/.process/ART-006-workflow.md:139-141`).
- **Split decision**: **one slice, no split** — unchanged from spec.md:369-375.
  The 48-LOC growth over the ratified 382 comes entirely from the Clarify phase
  adding nine lettered sub-requirements that *narrow* existing behaviour, and
  from three test-registry files the registered-operation contract forces. It is
  not new capability. Splitting would put argv parsing in one PR and the
  resolution it feeds in another, which is a worse review unit than the whole
  vertical. Deferred work already names its owner: draft-pull-request
  corroboration and the scaffold-side chain implementation go to the downstream
  ART specifications (spec.md:480-485).
- **PR review packet source**: spec.md:377-384 (what changed, why, non-goals,
  review order, scope budget, traceability, verification, known gaps, rollback).
  Rollback is a plain revert — the feature adds an argument and a table row, so
  reverting restores the pre-stage single-sequence behaviour, and a workflow file
  carrying a stale `Stage` row still validates because absence and presence are
  both legal (spec.md:203-205).

## Project Structure

### Documentation (this feature)

```text
specs/art-006-autopilot-staging/
├── plan.md                              # This file
├── research.md                          # Phase 0 output — decisions + rejected alternatives
├── data-model.md                        # Phase 1 output — stage state entities and transitions
├── quickstart.md                        # Phase 1 output — runnable validation guide
├── contracts/
│   ├── stage-invocation.md              # argv surface + resolve-autopilot-stage operation
│   └── scaffold-autopilot-chain.md      # FR-016 handoff contract (documentation only)
├── spec.md
└── tasks.md                             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
speckit-pro/
├── speckit_pro_runner/
│   └── helpers/
│       ├── read_only.py                 # + resolve_autopilot_stage + pure helpers + PY_HELPERS entry
│       └── registry.py                  # + HELPERS["resolve-autopilot-stage"]
├── skills/speckit-autopilot/            # Claude distribution
│   ├── SKILL.md                         # argv synopsis, Step 0.6c, staging, anti-stall, precedence clause
│   ├── contracts/
│   │   └── autopilot-state-status.schema.json   # + stage, + prior_run_note
│   ├── scripts/
│   │   └── validate-autopilot-phase-coverage.py # + stage_mirror_errors + problem key
│   └── references/
│       ├── phase-execution.md           # stage-bounded loop, G6.5 terminal commit, staged path set
│       ├── task-list-canonical.md       # out-of-stage `skipped:` marking
│       └── workflow-file-protocol.md    # durable Stage entry, write cadence
└── codex-skills/speckit-autopilot/      # Codex distribution
    ├── SKILL.md                         # argv line + pointer ONLY (word cap)
    └── references/
        ├── phase-execution-codex.md     # all Codex stage prose lives here
        └── task-list-canonical-codex.md # out-of-stage `skipped:` marking

tests/speckit-pro/
├── suite-manifest.json                  # register the new Layer 4 test
├── layer1-structural/
│   └── validate-workflow-status-evidence.py     # + Stage-row assertions
└── unit/
    ├── test-autopilot-stage-resolution.py       # NEW — golden fixtures + argv parity
    ├── test-speckit-pro-read-only-helpers.py    # + roster entry + no-Bash-ancestor carve-out
    └── fixtures/read-only-helpers/
        ├── fixture-manifest.json                # + operation record
        └── requests/resolve-autopilot-stage.json # NEW — authoritative request fixture
```

**Structure Decision**: no new directory and no new module. Every path above
already exists and already owns the behaviour being extended. The runner package
holds shared executable logic; each distribution's `SKILL.md` holds only its
invocation surface, with prose pushed into `references/` — mandatory on the Codex
side because the body is word-capped and the referenced files are not
(`validate-codex-skills.py:168-171`, and referenced files are still folded into
`runtime_doc` at `:235-242`, so the pinned-sentence checks keep seeing them).

## Implementation Approach

Six work groups, in dependency order. Sequencing matters for two of them and is
called out where it does.

### 1. Shared resolver — `resolve-autopilot-stage`

Add to `speckit-pro/speckit_pro_runner/helpers/read_only.py`, beside
`resolve_confidence_mode` (`:1081-1096`):

- `AUTOPILOT_STAGES = ("plan", "implement", "full")` and the stage→phase-range
  map. Literal lowercase tokens, no aliases (spec.md:157-164).
- `parse_stage_args(args)` — reads `--stage <value>` and `--from-phase <value>`
  out of the invocation argv, rejecting an unknown token, a repeated `--stage`
  with differing values, and a `--from-phase` outside the named stage's range.
- `workflow_stage_signals(text)` — reads the `Stage` row out of
  `### Basic Information` and derives planning-phase completeness from the
  `## Workflow Overview` status table, reusing the terminal-status vocabulary the
  guard already publishes.
- `resolve_autopilot_stage(inputs, repo_root)` — the registered entry point.
  Returns a JSON envelope carrying the resolved stage, its source, and the basis
  string the orchestrator prints (FR-006's "report the resolution before work
  begins"). Exit 2 on any pre-flight rejection, following the
  `--strict`/`--advisory` precedent at `read_only.py:1084-1085`.

Wire it in three existing tables: `PY_HELPERS` (`:4021` region),
`canonicalize_inputs` path keys (`:254-256`), and `explicit_or_derived_args`
(`:329-341`). Register the operation in `helpers/registry.py` next to
`resolve-confidence-mode` (`:171-178`).

Full request/response shape and every error string: [contracts/stage-invocation.md](./contracts/stage-invocation.md).

### 2. In-run enforcement — phase-coverage guard

In `validate-autopilot-phase-coverage.py`:

- Import the resolver from the runner package (`sys.path` insert +
  `from speckit_pro_runner.helpers.read_only import ...`). When the package is
  not importable — the case the file already handles for its schema at
  `:3930-3943`, "whenever the validator is copied out of the repository" — the
  new check returns an empty error list rather than a false violation.
- Add `stage_mirror_errors(workflow_text, state)`: when both stores carry a
  stage and they differ, report it; the workflow file wins and the state mirror
  is the thing to repair (spec.md:194-196). Absence on either side is legal.
- **Register `"stage_mirror_errors"` inside the `status-evidence` tuple of
  `RULE_PROBLEM_KEYS` (`:238-247`).** This is the whole point of FR-014a: the
  autopilot invokes the guard with `--rule status-evidence`
  (`SKILL.md:398`), and `main()` at `:4040-4042` computes the exit code *only*
  from the selected rule's keys. A key outside that tuple is computed, printed,
  and inert — which is the live defect the Clarify phase demonstrated by
  execution (spec.md:320-329).

### 3. Claude distribution

In `speckit-pro/skills/speckit-autopilot/SKILL.md`:

- **`:293`** — usage synopsis gains `[--stage plan|implement|full]` **and** the
  `[--strict | --advisory]` flags the Codex synopsis at
  `codex-skills/speckit-autopilot/SKILL.md:544` already advertises. That second
  half is the stale-documentation repair of FR-002: the Claude side already
  resolves those flags from argv at `:328-336`, so the line is documentation
  catching up to shipped behaviour, not new capability.
- **`:50-51`** — "do not stop early, complete all 7 phases" is reworded to bind
  to the resolved stage. A `--stage plan` run contradicts that sentence verbatim,
  and it is unpinned prose, so rewording it is safe and necessary.
- **New Step 0.6c**, immediately after the 0.6b confidence-mode resolver at
  `:327-336`, running `resolve-autopilot-stage` with the invocation argv and the
  workflow path, recording `AUTOPILOT_STAGE`, and STOPping on exit 2 before any
  phase work — the same fail-fast shape 0.6b already uses.
- **`:436`** — per-phase staging already enumerates
  `git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json`, so
  FR-009a is satisfied here and needs no widening; the plan-stage terminal commit
  is added using the same enumeration, and never a directory-wide add.
- **`:661-680`** — the `Stage` authority becomes **its own clause** in the
  Workflow File Update Protocol. It must **not** join the two-item list at
  `:672-680`: that list enumerates the fields for which the *state file* wins,
  which is the opposite direction (spec.md:196-199).
- **`:737`** — the registered-operation list gains a one-line
  `resolve-autopilot-stage` entry.

In `references/phase-execution.md`: the loop becomes stage-bounded; G6.5 at
`:563-641` is documented as the plan stage's terminal step (it already runs
"After Phase 6 commits and before Phase 7 begins", `:563-565`, and its strict-mode
STOP already tells operators to resume with `--from-phase implement`, `:620-622`);
the terminal commit is added after the gate resolves; the six per-phase
`git add specs/ && git commit` lines at `:233`, `:286`, `:352`, `:398`, `:523`,
`:561` are brought in line with the enumerated set already used at `SKILL.md:436`;
and an implementation-stage entry reads the recorded G6.5 verdict instead of
re-running the gate, emitting the FR-010a diagnostic when a confidence-mode flag
is accepted but unused.

In `references/task-list-canonical.md`: out-of-stage entries take
`skipped: <reason>` in the **status** field with the entry **name byte-identical**,
reusing the shape already documented at `:3` and `:56` for absent extensions.

In `references/workflow-file-protocol.md`: the durable `Stage` entry, its
at-most-twice-per-run write cadence, and the same-commit rule for the mirror.

### 4. Codex distribution — additive, within 329 words

Two edits to `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`:

1. `:544` — append `[--stage plan|implement|full]` to the argv line. One
   whitespace-delimited token by `structural_helpers.body`'s `.split()` count.
2. One pointer sentence directing the reader to the stage section of
   `references/phase-execution-codex.md`.

Budget: **≈24 words of the 329 available**, leaving ≈305. All Codex stage prose
lands in `references/phase-execution-codex.md`, which is uncapped. The four
string-pinned sentences (`validate-codex-skills.py:292`, `:295`, `:306-310`,
`:313-318`) are untouched — every edit is an addition, and the pinned assertions
read `runtime_doc`, which folds the referenced files in at `:235-242`.

### 5. State contract

`speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`
today declares only `status`. Add two properties that the running autopilot is
**already writing** to `docs/ai/specs/.process/autopilot-state.json` without any
schema behind them: `stage` (closed enum `plan|implement|full`) and
`prior_run_note` (string). Documenting `prior_run_note` is precisely what
FR-012a demands — "any field used to note the reclaimed predecessor MUST be part
of the documented state contract rather than ad hoc" — and it is what makes the
field established rather than a name invented by hand mid-run
(spec.md:305-308). The object has no `additionalProperties: false`, so the
addition is backward-compatible with every existing state file, and
`validate_state_status` (`validate-autopilot-phase-coverage.py:3930-3945`) starts
closing the stage vocabulary for free.

### 6. Verification

- **NEW** `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` — golden
  fixtures for explicit and auto-detected resolution, a planning-stage state
  fixture whose post-implementation entries carry the out-of-stage skipped status
  with canonical names intact (FR-015), every rejection case, and the
  **cross-distribution argument-parity assertion** (FR-015a): both distributions'
  documented argv forms feed the same operation and must resolve identically.
  The assertion goes here, not in the structural parity validator, whose checks
  are existence-only and whose counted baseline would need regenerating
  (spec.md:335-340).
  Golden fixtures are module-level literals in the test file, the pattern
  `validate-workflow-status-evidence.py:102-143` already uses, so no separate
  fixture file is needed.
  The filename carries no live spec-family token: the rule at
  `tests/speckit-pro/unit/test-unit-layout.py:143-148` matches
  `<family>[-_]\d{3}[a-z]?`, so `art-006` would fail but
  `test-autopilot-stage-resolution` does not match at all.
- **MODIFIED** `tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py`
  — a subTest asserting that any `Stage` row present in any workflow file under
  `docs/ai/specs/.process/` carries one of the three literals, and that a file
  with no `Stage` row is accepted. Absence must stay legal: 56 of the 57 workflow
  files carry no entry (spec.md:206-210).
- **MODIFIED** `tests/speckit-pro/suite-manifest.json` — register the new test in
  `layers[id=4].scripts` as `{path, label, baseline: null}`. This is the only
  dispatch roster; an unregistered test never runs.
- **MODIFIED** `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` and
  `fixtures/read-only-helpers/fixture-manifest.json` — registering a runner
  operation is a contract, not just a dict entry:
  `test_fixture_manifests_cover_registered_helpers` (`:338-346`) asserts the
  fixture-manifest roster equals `EXPECTED_HELPERS` exactly. It also asserts the
  Bash-reference roster equals that list minus `helper-registry-dispatch`, and
  that each entry's `source_script` ends in `.sh` (`:379`). This operation has no
  Bash ancestor, so it needs a named carve-out rather than a fabricated script
  path. See [research.md §D3](./research.md#d3--registering-an-operation-with-no-bash-ancestor).

### Sequencing constraints

1. **Reclaim before guard.** An implementation-stage invocation against a state
   slot naming a different specification must re-initialise the slot *before* the
   coverage guard runs. Ordering it after is not merely late, it is unprotected:
   the workflow-identity check is inert today (spec.md:320-329), so a mismatched
   slot exits 0 and reports `pass`.
2. **Terminal commit after the gate.** The plan-stage commit is taken after G6.5
   resolves, so the verdict is captured. It is a distinct commit, not a renamed
   analyze-phase commit, and it is non-empty regardless of whether the `Stage`
   value changed, because the confidence-gate row always advances off pending
   (spec.md:217-220).
3. **Regenerate last.** `scripts/refresh-release-artifacts.py` runs after every
   source edit is final; a second run on unchanged source is a no-op
   (`refresh-release-artifacts.py:22-23`).

## Complexity Tracking

*No constitution violation requires justification.* One design trade-off is
recorded here because a reviewer will ask about it.

| Trade-off | Why chosen | Simpler alternative rejected because |
|---|---|---|
| The phase-coverage guard imports the 4,100-line `read_only.py` to reach the resolver | FR-012 sites resolution in a registered runner operation and explicitly permits the guard to consume it as a library. One rule, one implementation, zero drift. | A dedicated small module would give the guard a narrower import, but it adds a file and a layer for a three-value decision, which constitution §VI (YAGNI, "no wrapper layers") rules out. Restating the rule inside the guard is what the Round 2 tiebreak rejected outright. |

## Post-Design Constitution Re-Check

Re-evaluated after the Phase 1 artifacts were written. **All gates still pass.**
The design added no dependency, no new directory, no new module, and no shell
script. The two contract documents are specification artifacts under `specs/`,
not shipped code, and carry no runtime weight. Reviewability moved from the
ratified 382 to 430 — warn, not block — and the split decision is unchanged.

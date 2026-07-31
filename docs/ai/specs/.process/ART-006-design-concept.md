---
topic: "ART-006 autopilot staging"
slug: "art-006-autopilot-staging"
date: "2026-07-30"
mode: "setup"
spec_id: "ART-006"
source_input:
  type: "topic"
  ref: "ART-006 scope section, docs/ai/specs/html-artifacts-technical-roadmap.md"
question_count: 8
stop_reason: "natural"
---

# Design Concept: ART-006 Autopilot Staging

Give autopilot first-class stages — `plan` (specify→analyze), `implement`
(implement→post-implementation), `full` (legacy) — with auto-detection and
durable stage state, on both platforms.

## Goals

- **Ship `--stage plan|implement|full` on both distributions** in one vertical
  slice: argv parsing → stage resolution → stage-bounded phase loop → durable
  stage state. Behaviour change only; gate semantics (G0–G7 and G6.5) are
  untouched.
- **Resolve a bare invocation from the workflow file's status table**, per the
  roadmap's approved rule. Explicit flags override.
- **Make the plan stage terminate cleanly and resumably** — the stage boundary
  is a real commit, not a working-tree state.
- **Reach genuine Claude/Codex parity on stage handling.** The two variants must
  run the same resolution logic, not two prose descriptions of it.
- **Document the scaffold → autopilot chain contract** for ART-011 to consume.

### Hard dependency: the bookkeeping-durability prerequisite

ART-006's headline deliverable is durable stage state. The store it would rely
on is currently unenforced and has failed twice in this repository, so a
prerequisite PR lands **before** autopilot executes this spec. Evidence:

- `docs/ai/specs/.process/CAR-005-workflow.md:38-41` reads Tasks `⏳ Pending`
  and Analyze `⏳ Pending` while the same file records `G5 gate: ✅ PASS —
  63 tasks found` at `:955` and `G6 gate: ✅ PASS` at `:1075`. The spec shipped
  in PRs #411 and #412.
- `docs/ai/specs/.process/ART-001-workflow.md:41` reads Implement
  `🔄 In Progress` on a spec merged via #407/#409 and archived. Its own merge
  commits touched **neither** copy of `autopilot-state.json`; at that commit the
  file still named `G56R-004`.
- Root cause: `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:649` runs
  `validate-autopilot-phase-coverage.py` and `:676` requires exit 0. **Nothing
  under `speckit-pro/skills/speckit-autopilot/` invokes it.** Specs carrying the
  validator-required `| Post |` and `| G6.5 |` rows have clean tables; specs
  without them drifted.
- Contributing cause: `speckit-pro/skills/speckit-autopilot/SKILL.md:413` stages
  only `git add specs/` for phases 1–6, but the workflow file lives outside
  `specs/`, so per-phase table flips are uncommitted until phase 7's
  `git add -A`.
- The instruction exists and is simply unverified —
  `references/workflow-file-protocol.md:11` says "Status table: `⏳` → `✅` with
  summary notes" for **All** phases; no validator reads the table.

The prerequisite is scoped in the Q&A log below (Q2, Q3, Q4) and is **not** part
of ART-006's own budget.

## Non-goals

- **`gh` draft-PR corroboration** — deferred to ART-007, which is what creates
  the draft PRs it would corroborate against (Q5). The roadmap Scope line is
  amended accordingly.
- **Draft-PR creation** (ART-007), **feedback sweep** (ART-008), **scaffold-side
  chain implementation** (ART-011).
- **Any change to gate semantics.** G0–G7 and G6.5 keep their current pass/fail
  meaning; only *which stage owns G6.5* is decided here.
- **Truncating the canonical task list per stage.** Full coverage stays; only
  the out-of-stage marker token is in scope.
- **New Bash dependencies.** Python 3.11+ standard library only.

## Design Tree (Q&A log)

### Q1 — What predicate should stage auto-detection use? *(withdrawn — dissolved by Q2)*

**Asked because** the roadmap's rule ("phases 1–6 complete → implement, else
plan") misfires on two of the three real workflow files in the tree. Under it, a
bare invocation against `CAR-005-workflow.md` resolves `plan` and re-runs Tasks
and Analyze over 63 finished tasks.

**Outcome:** the maintainer identified the real problem — the plugin is not
keeping these files up to date — which relocated the question. Once drift is
prevented (Q2) the approved predicate is sound for every new spec, and the three
drifted files are all complete and archived, so nothing will auto-detect against
them. **No predicate change. The roadmap rule stands as written.**

### Q2 — How should ART-006 handle a foundation that has already failed twice?

**Recommended:** fix drift first as its own PR, so each change traces to one
concern and ART-006 stays inside its budget.

**Chosen:** *fix drift first as its own PR* — **and additionally repair the
single-slot state file**, with the explicit requirement that the solution be
deterministic every time, because ART depends on it being flawlessly reliable.

**Resulting prerequisite scope:**

1. Claude invokes the coverage validator, exit 0 required — closing the
   root-cause asymmetry with Codex.
2. The validator gains a status-vs-evidence check: a body recording
   `**G5 gate:** ✅ PASS` implies the Tasks row must read Complete. Precedent
   exists at `validate-autopilot-phase-coverage.py:455-460`, which already
   exact-matches workflow Plan status against `pr_marker_plan.status`.
3. Fail-closed sequencing: phase N does not start unless N−1 reads Complete.
4. **CI structural test** over every `.process/*-workflow.md` asserting the table
   agrees with the file's own gate evidence.
5. Closed, schema-validated status vocabulary — the tree currently carries
   `complete_pr_open`, `completed_pr_open`, `completed`, `completed_archived`,
   `in_progress`, and absent for the same concept.
6. **Per-spec durable state**: the workflow file is the per-spec store (it
   survives archive, unlike `specs/<id>/`); `autopilot-state.json` is redefined
   as a current-in-flight pointer, not per-spec history.

Layers 1–3 reduce probability; **only layer 4 makes it certain**, because it is
the only layer with no agent in the loop.

### Q3 — What enforcement primitive, and how should it be scoped?

**Researched against both vendors' official documentation** at the maintainer's
request, since the fix ships to both distributions.

Both platforms support a `Stop` hook that **blocks** with an identical contract —
`{"decision":"block","reason":…}` or exit 2 with stderr as the reason. Both let a
plugin ship `hooks/hooks.json`; both expose `${CLAUDE_PLUGIN_ROOT}`. The wiring
already exists and is empty on both sides: `speckit-pro/hooks/hooks.json` and
`speckit-pro/codex-hooks.json`, the latter already declared by
`speckit-pro/.codex-plugin/plugin.json`. The single divergence is that Codex's
`Stop` input carries `stop_hook_active` and Claude's does not, so the Claude
implementation needs its own bounded re-entry guard.

A `Stop` hook is strictly better than a subagent check because it is enforced by
the harness rather than by an instruction the model can skip — which is the exact
property that failed. The block condition is self-clearing: it blocks only while
drifted and the reason names the fix.

**Recommended and chosen:** scoped + fail-open at runtime, CI as the hard gate.
The hook no-ops unless the session has an active workflow file; if the hook
itself cannot run it exits non-blocking. The absolute guarantee lives in the CI
test, which cannot strand an operator — worst case a PR is blocked, which is the
correct outcome.

### Q4 — How wide should Claude's Bash grant be?

**A premise correction happened here.** The orchestrator was believed to lack
Bash because `speckit-pro/skills/speckit-autopilot/SKILL.md:10` omits it from
`allowed-tools`. The vendor documentation is explicit that `allowed-tools` is a
*permission pre-approval* list — "tools Claude can use without asking permission"
— while `disallowed-tools` is the field that removes tools from the pool.
Autopilot sets no `disallowed-tools`. **Both orchestrators can run shell.**

Parity picture: Codex skills declare no tool allowlist at all (zero hits across
`codex-skills/`; `validate-codex-skills.py:58` forbids Claude-only keys), and
Codex agents scope capability via `sandbox_mode`. So the only reason Claude never
ran the validator is that **the instruction was never written into the Claude
SKILL.md**. A pure omission, not a capability gap.

**Recommended:** narrow, script-scoped grant. **Chosen:** *narrow grant plus the
runner* — pre-approve both the bundled validator and
`python3 -m speckit_pro_runner`, since the phase loop invokes runner helpers
throughout and those would otherwise prompt and stall an unattended run. Uses the
documented `Bash(${CLAUDE_SKILL_DIR}/…)` idiom, which substitutes in both the
`allowed-tools` rule and the skill body (requires Claude Code ≥ 2.1.129).

### Q5 — Does the `gh` corroboration limb ship in ART-006?

The roadmap contradicts itself: `html-artifacts-technical-roadmap.md:448-451`
puts draft-PR detection in Scope, while `:458-460` defers draft-PR *creation* to
ART-007. During ART-006 no draft PRs exist, so every test would exercise the
absent branch.

**Recommended and chosen:** defer to ART-007 and amend the Scope line so the
deferral is recorded rather than silently dropped. ART-007 inherits the OQ-4
discrepancy-logging contract. This decision is also what keeps the spec a single
slice — see Q8.

### Q6 — How should the plan stage close?

Phases 1–6 stage only `git add specs/` (`SKILL.md:413`); the workflow file lives
in `docs/ai/specs/.process/`, outside that path, so it reaches git only via phase
7's `git add -A`. A plan stage terminating after Analyze never reaches phase 7,
leaving the stage marker and all six status-table updates uncommitted.

**Recommended:** a plan-stage terminal commit staging by path. **Chosen:** *do
both* — widen per-phase staging so bookkeeping is durable throughout, **and** add
an explicit terminal commit so the stage boundary is greppable in history.

This also plausibly explains CAR-005: per-phase table flips were never committed
until phase 7, so anything resetting the working tree mid-run discarded them
silently.

### Q7 — Which stage owns Phase 6.5?

A genuine gap in the source documents, not a disagreement: AC-6.1 gives plan
`specify→analyze` and implement `implement→post-implementation`; G6.5 sits
between and is assigned to neither.

**Recommended and chosen:** the **plan stage's terminal step**. G6.5 runs "After
Phase 6 commits and before Phase 7 begins"
(`references/phase-execution.md:565`), its remediation re-dispatches
clarify/analyze work on *planning* artifacts, and its strict-mode STOP already
tells operators to resume with `--from-phase implement` (`:622`). It is already
written as the plan/implement seam, and a plan stage that ends with a recorded
confidence verdict is exactly what a human checkpoint wants to read.

### Q8 — Slice sizing

The shared estimator (`estimate-spec-size`) was run on three signal sets:

| Signals | LOC | Slices | Status |
| --- | --- | --- | --- |
| Roadmap-declared (3 stories, 6 files, 8 FRs, modify) | 217 | 1 | ok |
| **Honest count, `gh` deferred (3, 12, 14, modify)** | **382** | **1** | **ok** |
| If `gh` had stayed (3, 14, 18, modify) | 452 | 2 | warn |

The roadmap's 217 reproduces exactly from "6 files, 8 FRs", so it is a
restatement of its own file count rather than an independent measurement. The
honest count is 382 against a 400 ceiling; the `gh` deferral in Q5 is what keeps
this one slice.

**Recommended and chosen:** **one slice.** The work is genuinely vertical — one
capability cutting end-to-end through argv, resolution, the phase loop, durable
state, and both platforms — and with `gh` deferred the auto-detect half is now
just "read the status table", too thin to stand alone. Declared budget 382/400;
the plan-phase estimator re-checks against real artifacts at G3.

## Decisions settled by evidence (not asked)

These had a determinate answer in the repository, so they were recorded rather
than put to the maintainer.

- **Out-of-stage task marker is `skipped:`, not a new `deferred:` status.** The
  Codex pre-final audit at `codex-skills/speckit-autopilot/SKILL.md:986-992`
  blocks a final response when any `Post:` item is "pending, in_progress, or
  missing", and tolerates "completed **or explicitly skipped**". `skipped` is the
  only non-complete status already in the audit's vocabulary.
- **Codex prose must be additive only.** Four sentences are string-pinned by
  `tests/speckit-pro/layer1-structural/validate-codex-skills.py` — the
  `PHASES = [...]` literal (`:292`), "`--from-phase` changes only the starting
  index" (`:295`), the all-phases-complete resume triple (`:306-310`), and the
  pre-final audit quadruple (`:313-318`). Claude's anti-stall line
  (`SKILL.md:50-51`, "do not stop early, complete all 7 phases") is unpinned
  prose and must be reworded to bind to the resolved stage.
- **Conflicting flags fail fast at pre-flight.** House precedent is exact:
  `speckit_pro_runner/helpers/read_only.py:980-981` returns
  `--strict and --advisory are mutually exclusive` with exit 2, and
  `references/phase-execution.md:575` records the rationale — resolve once at
  start so conflicts fail before any phase work.
- **`--stage implement` re-runs Phase 0.** Pre-flight is unconditional
  (`SKILL.md:300`) and re-derives `PROJECT_COMMANDS` / `PRESET_CONVENTIONS` every
  invocation, so re-running is free; but `CONFIDENCE_GATE_MODE` is session-scoped
  and G6.5 may not re-resolve it (`SKILL.md:336`), and G7 compares against the G0
  baseline (`references/gate-validation.md:366`), so an existing baseline is
  authoritative for the delta.
- **The chain contract is documentation only.** Scope says "documented (consumed
  by ART-011)" (`:454`) while Out of Scope assigns the scaffold-side chain to
  ART-011 (`:459-460`).

## Open Questions

- **OQ-1 — Where in the workflow file does the stage field live?** The strongest
  candidate is a new row in `## Specification Context → Basic Information`, an
  existing scalar key/value table (`skills/speckit-coach/templates/workflow-template.md:103-110`)
  that `speckit-status/SKILL.md:96` already parses for Branch. Frontmatter is out
  — real workflow files carry none. A new status-table column is out — two
  parsers read that row shape. **Sub-question:** `workflow-template.md` is owned
  by *speckit-coach* and is not in ART-006's Key Files list; confirm it is in
  scope during Plan.
- **OQ-2 — The scaffold template cannot pass the coverage validator today.**
  `workflow-template.md:55-65` emits 7 status rows; the validator requires
  `| Confidence Gate | G6.5 |` and `| Post |`. Pre-existing, and the reason
  CAR/ART specs lack those rows. The template fix is non-optional once Claude-side
  enforcement is on — decide in the prerequisite PR whether it lands there or in
  ART-006.
- **OQ-3 — Codex word budget.** The Codex autopilot body is ~7.6k words against a
  hard 8000-word cap (`validate-codex-skills.py:168-171`), leaving roughly 390
  words. Stage prose likely has to live in `phase-execution-codex.md`, which the
  validator already folds into `runtime_doc`. Confirm during Plan.
- **OQ-4 — Should the prerequisite become its own roadmap entry?** It has grown
  to six components. It is a bug fix, and this repository lands bug fixes as
  plain PRs, but a change to the autopilot's enforcement model is arguably
  spec-worthy.

## Recommended Next Step

Land the bookkeeping-durability prerequisite PR, then run:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-006-workflow.md
```

## Traps carried into implementation

- **84 generated mirrors.** Editing either SKILL.md dirties `dist/claude/`,
  `dist/codex/`, both installed-cache trees, and the proof files. Regenerate with
  `refresh-release-artifacts.py`; CI runs it with `--check`. Never hand-edit.
- **Docs reference regen is separate.** `refresh-release-artifacts.py` does not
  regenerate the docs reference; that needs
  `pnpm --dir docs-site reference:generate`. A test-tree change also stales
  `reference/tests.md`.
- **Layer 2 re-run is honor-system.** Layer 2 is `default: false`,
  `live_only: true` in `tests/speckit-pro/suite-manifest.json`, so it never runs
  in CI — but the current description hard-codes the contract being changed
  ("executes **all 7 SDD phases**").
- **No live spec ID in tracked filenames.** `tests/speckit-pro/unit/test-unit-layout.py:273-294`
  forbids it, and `art` is a live family. Name the test
  `test-autopilot-stage-resolution.py` with a matching fixtures directory, and
  register it in `suite-manifest.json` — the manifest is the only dispatch roster.
- **Nothing diffs the two SKILL.md variants.** `validate-codex-parity.py:134`
  checks existence only; their argv contracts have already silently diverged over
  `--strict`/`--advisory`. Parity here must come from shared logic, not from a
  parity test that would not catch it.
- **Adding a Codex-checked string has a three-step ritual** — edit the Codex
  SKILL.md, add the assertion to `validate-codex-skills.py`, and update
  `tests/speckit-pro/layer1-structural/CODEX-PARITY-NOTES.md`.

# Implementation Plan: Feedback Sweep, slice 1 of 2 — the checkpoint

**Branch**: `art-008-feedback-sweep` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-008-feedback-sweep/spec.md`

## Summary

The implement stage opens with a feedback sweep. Before any task work it reads
the draft pull request the plan stage left behind, keeps only comments from
write-capable authors, recognizes artifact-exported blocks by registered lead
sentences, gives each comment exactly one class, routes only `amended` through
the existing consensus protocol, records every handled comment in a Feedback
Sweep Log, replies once per comment, and then stops for re-review or proceeds.

The technical approach splits along the line the repository already uses for
`resolve-autopilot-stage`: **the orchestrator observes, one read-only runner
helper classifies, and the orchestrator decides.** The helper takes the raw
`gh` observation as data, applies the author-association allowlist, matches the
export registry, and returns a closed-vocabulary envelope. It never runs `gh`,
never touches the network, and never assigns a class. That keeps the security
boundary and the determinism guarantee inside a fixture-pinned Python surface
while leaving classification, consensus, commits, and replies where they can
only be orchestrator work.

## Technical Context

**Language/Version**: Python 3.11+ standard library (runner helper); Markdown
(skill references). No new dependencies.

**Primary Dependencies**: `speckit_pro_runner` helper framework; the existing
category-routed consensus protocol; `gh` CLI at the orchestrator boundary only.

**Storage**: The workflow file is the sole store. No state-file mirror (FR-013).

**Testing**: `python3 tests/speckit-pro/run-all.py`. Layer 4 golden fixtures for
the helper; Layer 1 structural and Codex-parity validation for the references.

**Target Platform**: Claude Code (`speckit-pro/skills/`) and Codex CLI
(`speckit-pro/codex-skills/`), identical behavior (FR-003, SC-007).

**Project Type**: Plugin source — a read-only runner helper plus skill
reference documentation. No application tier.

**Performance Goals**: N/A. The sweep is a once-per-stage setup step bounded by
pull-request size, not a throughput surface.

**Constraints**: No new Bash and no `jq` (constitution II). `shell=False` and
argument arrays throughout. No comment text may reach a shell argument in
either direction (FR-004b, SC-009). Each comment body truncates at a fixed byte
budget below the runner's 32 KiB bounded-input limit, because that limit
rejects the whole request rather than the offending string (FR-008).

**Scale/Scope**: One new read-only helper operation, seven modified production
files, seven test and fixture files. Two platform variants.

**Reviewability Budget**: harness/adapter (single primary surface); **hand-derived
515 to 745 reviewable LOC, midpoint near 630**; 7 production files; 14 authored
files total; **warn on reviewable LOC and on production files, block on neither.**
Derived by hand from the Declared File Operations block below, because the
estimator cannot measure this slice. See "Reviewability Budget, derived by hand".

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
List one entry per file on its own line, each starting with a `- ` list marker:
`- NEW <repo-relative-path>` for a new file or `- MODIFIED <repo-relative-path>`
for an existing one.

Production surface (authored, reviewable):

- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md

Test and fixture surface (authored, verification):

- MODIFIED tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
- MODIFIED tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json
- NEW tests/speckit-pro/unit/fixtures/read-only-helpers/requests/sweep-pr-feedback.json
- NEW tests/speckit-pro/unit/test-feedback-sweep-parse.py
- NEW tests/speckit-pro/unit/fixtures/feedback-sweep/comment-corpus.json
- NEW tests/speckit-pro/unit/fixtures/feedback-sweep/expected-envelopes.json
- MODIFIED tests/speckit-pro/suite-manifest.json

Generated surface (regenerate, never hand-edit, not counted as reviewable):

- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py

The `dist/` and installed-cache entries are byte-identical copies produced by
`python3 scripts/refresh-release-artifacts.py`. The spec's Assumptions section
already records that adding a read-only helper restales them and that
regenerating is required rather than optional. The reference `.md` files ship
into both distributions too and regenerate through the same script.

### Two files deliberately absent from this block

`speckit-pro/skills/speckit-autopilot/SKILL.md` and
`speckit-pro/codex-skills/speckit-autopilot/SKILL.md` are **not** modified. The
spec's Reviewability Budget projected "8 or 9" production files partly because
"both `SKILL.md` files carry helper names today". Measured against the shipped
cap, that line cannot be taken:

- Layer 1 `validate-codex-skills.py` and `validate-skills.py` both assert a
  skill body of 500 to 8000 words.
- Measured with the validator's own `_body` helper, the Codex autopilot skill
  body is **7997 words — three words of headroom.** Any added line fails Layer 1.
- The Claude body is 6857 words and has room, but no test requires either
  `SKILL.md` to enumerate helpers. The Claude file's helper index is
  documentation, and the Codex file names `resolve-autopilot-stage` only in
  running prose.

Adding the helper to the Claude index alone would also put the two platform
documents out of step for no behavioral gain. The sweep is documented in the
phase-execution references, which is where the sequence lives. This removes two
files from the projected surface and is why production files land at 7, not 9.

## Reviewability Budget, derived by hand

### The estimator's verdict is an absent measurement, not a pass

`estimate-reviewable-loc` projects from production files only, and counts a file
as production only when its path sits under `src/`, `app/`, `lib/`, or
`scripts/`, or when it ends in a JavaScript, TypeScript, or SQL extension. Every
path in the block above fails both tests: the runner helpers sit under
`speckit-pro/speckit_pro_runner/`, and every reference is Markdown.

This was run against this plan rather than predicted. Verbatim output:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":4,"modified":18,"total_entries":22},
 "greenfield":false,
 "thresholds":{"warn":400,"block":800,"greenfield_multiplier":1.5,
               "base_warn":400,"base_block":800}}
```

Read it closely. The block parsed correctly — all **22** entries were seen, 4
new and 18 modified — and **`production` is 0**. The helper is not failing to
read the plan; it is reading it correctly and finding nothing it recognizes as
production code. `projected` is therefore 0, and `status` is `pass` against a
warn line of 400 it never had a chance to cross.

**That `pass` is an absent measurement and MUST NOT be cited as evidence the
slice is within budget.** The figures below are the measurement.

### Per-file derivation, anchored to shipped analogues

| File | Low | High | Basis |
|---|---:|---:|---|
| `read_only.py` — parse and report cluster | 200 | 250 | The nearest shipped analogue is the corroboration cluster at `read_only.py` lines 1292–1453: **162 lines** for a six-outcome classification over one supplied observation. This slice's parse does strictly more — CRLF normalization, per-comment byte truncation with a flag, whole-line matching across a ten-line window, an eight-value association filter, the anchored-marker-plus-author self-reply test, and a reasoned exclusion list. |
| `read_only.py` — export lead registry | 40 | 55 | 14 lead sentences (7 note-payload templates × 2 kinds), 6 distinct empty-export sentences, and header identities for the 3 serialization-family templates, each entry carrying template id and kind. The sentences are long literals that wrap in this file's style. |
| `read_only.py` — registration touch points | 5 | 8 | Allowed-inputs map entry (near line 256), argument-derivation branch (the `resolve-autopilot-stage` branch near line 341 is 10 lines), dispatch-table entry (near line 4466). |
| `registry.py` | 8 | 10 | One `HelperEntry`, matching the `resolve-autopilot-stage` shape at lines 181–188. |
| `phase-execution.md` | 110 | 170 | The Phase 7 Setup block this precedes is **34 lines**; the corroboration-status explainer it reuses is **57 lines**. The sweep sequence carries the substance of both, plus stop-or-proceed, per-amendment commit and push, two log writes, replies, and four-cause stop reporting. |
| `phase-execution-codex.md` | 90 | 150 | Codex references run roughly 70% of their Claude counterparts (59,990 against 84,310 bytes). |
| `workflow-file-protocol.md` | 40 | 60 | The nearest analogue is the `Draft PR` entry at lines 62–120: **58 lines** of grammar, examples, and rules for one workflow-file entry. The Feedback Sweep Log entry adds an eight-column table, pipe and newline escaping, and the unresolvable-author rule. |
| `workflow-file-protocol-codex.md` | 15 | 30 | The entire Codex protocol file is 90 lines, so its entries are far more compressed. |
| `consensus-protocol.md` | 5 | 12 | The fourth `Type` value in the row schema at line 617, plus the sweep-row escape-rate note. |
| **Total** | **513** | **745** | Midpoint **≈ 630** |

Stated as **515 to 745, midpoint near 630**.

### Corroborate or correct: this corrects the spec

The spec projected **325 to 485, midpoint near 400**. That range is **too low,
and this plan corrects it upward.** Two anchors in the spec's own bottom-up
derivation were measured against the wrong shipped precedent:

1. The spec anchored the parse at "the corroboration classifier is 35 lines".
   35 lines is the body of `corroborate_draft_pr` alone. The behavior it
   actually compares against — the closed vocabulary, the record builder, the
   three observation validators, and the classifier — is **162 lines** in this
   file's comment-dense house style. Anchoring on the function body alone
   undercounted by roughly a factor of four.
2. The spec allowed "15 to 25" for the workflow-file protocol entry. The
   `Draft PR` entry, the only comparable entry in that file, is **58 lines**.

The two phase-execution figures (70 to 110 each) are also low against a 34-line
setup block plus a 57-line status explainer for a sequence that carries more
than both, but that one is a judgment rather than a measurement error.

The spec's **production-file** count of "8 or 9" is corrected **downward to 7**,
for the `SKILL.md` cap reason recorded above.

### Budget result against the constitution thresholds

| Dimension | Value | Warn | Block | Result |
|---|---:|---:|---:|---|
| Reviewable LOC | ~630 (515–745) | 400 | 800 | **WARN** |
| Production files | 7 | 6 | 8 | **WARN** |
| Total authored files | 14 | 15 | 25 | pass |
| Primary surfaces | 1 | >1 | >1 | pass |

**Two warns, no blocks. The warn is accepted, explicitly and not silently.**

The high end of 745 leaves roughly 55 lines of margin to the 800 block. That
margin is real but thin, and it is the reason the implementation must hold the
references to the sequence rather than restating the spec's rationale in them.

### The split option, if the operator chooses to re-slice

The warn is accepted rather than re-sliced, and the reasoning is stated so the
operator can overrule it.

**The one clean lever available** is deferring the serialization-family registry
rows — `feature-flags`, `prompt-tuner`, and `triage-board`, whose exports carry
no reviewer objections and no imperative addressed to an agent. Deferring them
saves an estimated **15 to 30 lines**. It does not reach 400, and it costs
FR-007b's "every shipped template that declares an export".

**No split reaches 400 while shipping a checkpoint that works.** The drivers are
the parse helper (245–313) and the two phase-execution references (200–320).
Those are the feature's irreducible core: a sweep without the helper cannot
classify, and a sweep without the references cannot run on either platform.

**The split that would technically fit is rejected on merit.** Slicing the read
path and the records into 1a while deferring consensus amendment, replies, and
stop-or-proceed into 1b would produce a checkpoint that reads feedback, records
it, and then walks into task work having acted on none of it. That is precisely
the "feedback becomes decoration" outcome this feature exists to remove, one
layer down. If the operator wants a smaller slice, the serialization-family
deferral above is the recommended lever; this one is not.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 1.2.0.

| Principle | Assessment | Gate |
|---|---|---|
| I. Plugin Structure Compliance | PASS. No new plugin component types. The helper joins the existing `speckit_pro_runner` surface; all new tests live under `tests/speckit-pro/`, outside the install-facing directory. | `run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | PASS, and this slice tightens it. Python 3.11+ stdlib only, no new Bash, no `jq`, structured JSON parsing, `shell=False`, argument arrays. FR-004b forbids comment text in a shell argument in either direction, which is a **correction** to the nearest shipped precedent rather than a restatement of it. | `run-all.py --layer 4` |
| III. Semantic Versioning | PASS. No manual version edit; release-please owns the bump. | Layer 1 `validate-plugin` |
| IV. Test Coverage Before Merge | PASS. The new helper carries Layer 4 unit coverage, the golden-fixture corpus FR-008a pins, and a `suite-manifest.json` membership entry. | `run-all.py` |
| V. Conventional Commits | PASS. Amendment commits and the `chore:` bookkeeping commits FR-012a requires both follow `type(scope): description`. | CI `validate-pr-title` |
| VI. KISS, Simplicity & YAGNI | PASS with one judgment recorded below. | Plan and code review |

**Reviewability, per the preset's added obligations:**

- **Primary surface**: harness/adapter — the deterministic comment parse and its
  unit coverage. **Secondary surfaces**: docs/process — both phase-execution
  references, both workflow-file-protocol files, and `consensus-protocol.md`.
- **Within budget?** No. Warn on reviewable LOC (~630 against 400) and on
  production files (7 against 6). Under the block on both (800, 8). Accepted
  with the reasoning and the rejected split recorded above.
- **Split decision**: ART-008 is two stacked vertical slices along a Path seam.
  This is slice 1. Slice 2 (artifact freshness) is specified separately on a
  branch stacked on this one and owns page regeneration, stale-page detection,
  and the draft-description refresh.
- **PR review packet source**: `spec.md`'s PR Review Packet Requirements
  section, plus the traceability table in `quickstart.md`.

**The one KISS judgment worth recording.** One helper is registered rather than
two. Reading and recognizing could plausibly split into a read normalizer and a
registry matcher, but they share the ten-line window, the truncation budget, and
the normalization rules, and splitting them would put that shared state in a
third place. Three similar lines beat a premature abstraction; one operation is
the simpler shape. No Complexity Tracking entry is required.

**Post-design re-check.** Re-evaluated after Phase 1. The design artifacts
introduced no new violation: the helper stays Python 3.11+ stdlib and read-only,
truncation moved to the orchestrator without adding a Bash or `jq` dependency,
and no new plugin component type appeared. The two reviewability warns stand
exactly as recorded above, and neither became a block.

## Slice Topology

ART-008 ships as two stacked vertical slices along a Path seam. Both cut end to
end through the Claude and Codex variants.

| Slice | Branch | Scope | Status |
|---|---|---|---|
| 1 — the checkpoint | `art-008-feedback-sweep` | The comment-driven path: read, trust-filter, recognize, classify, amend through consensus, record, reply, stop or proceed. | This spec |
| 2 — artifact freshness | stacked on slice 1 | Regenerating the draft page set after amendments, detecting stale pages from git history on a clean sweep, and refreshing the draft pull-request description including the Resume block. | Specified separately |

### The hooks slice 1 leaves for slice 2

Slice 2 is stacked on this branch, so these are an interface, not an internal
detail. Changing either after slice 2 starts is a breaking change to it.

1. **The Feedback Sweep Log row shape.** Header
   `| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`
   under its own `### Feedback Sweep Log` heading, immediately after
   `### Consensus Resolution Log` (FR-013). Slice 2 reads this table to learn
   which amendments landed and therefore which pages are stale. The `Commit`
   column is the join key for that read: it is what lets slice 2 diff the
   artifact tree against the amendment commits rather than guessing from
   timestamps. Placement is additive-safe — the phase-coverage guard's table
   reader is heading-anchored and breaks on any line starting with `#`.
2. **The stop-report regeneration sentence.** Slice 1's stop report states that
   draft pages regenerate once slice 2 lands (FR-017). Slice 2 replaces that
   sentence with the real regeneration outcome. Until it does, the sentence is
   the only thing telling a reviewer why the pages they are looking at are
   older than the amendments.
3. **SC-008's standing constraint on slice 2.** After an amendment run stops, a
   reviewer can tell what changed and where from the pull request alone, and
   that rests entirely on the FR-015 replies, because a draft description is
   fully fingerprint-protected with no editable region. Slice 2 owns the
   description refresh and **MUST NOT** weaken the replies on the assumption
   that the description now carries this.

## Project Structure

### Documentation (this feature)

```text
specs/art-008-feedback-sweep/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── sweep-pr-feedback.md
├── checklists/
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/
├── speckit_pro_runner/
│   └── helpers/
│       ├── read_only.py          # + sweep_pr_feedback(), registry, 3 registration points
│       └── registry.py           # + one HelperEntry
├── skills/speckit-autopilot/references/
│   ├── phase-execution.md        # + Phase 7 setup sweep sequence, ahead of the notes record
│   ├── workflow-file-protocol.md # + the Feedback Sweep Log entry
│   └── consensus-protocol.md     # + the `Sweep` Type value
└── codex-skills/speckit-autopilot/references/
    ├── phase-execution-codex.md        # mirror of the sweep sequence
    └── workflow-file-protocol-codex.md # mirror of the log entry

tests/speckit-pro/
├── suite-manifest.json
└── unit/
    ├── test-speckit-pro-read-only-helpers.py   # EXPECTED_HELPERS, NO_BASH_ANCESTOR
    ├── test-feedback-sweep-parse.py            # golden fixtures + manifest-derived registry test
    └── fixtures/
        ├── feedback-sweep/                     # comment corpus + expected envelopes
        └── read-only-helpers/
            ├── fixture-manifest.json           # order-sensitive; append to match EXPECTED_HELPERS
            └── requests/sweep-pr-feedback.json
```

**Structure Decision**: No new directories under plugin source. The helper joins
`speckit_pro_runner/helpers/read_only.py` beside `resolve_autopilot_stage`,
which is the operation this one is modeled on: both take an orchestrator-supplied
observation, classify it offline, and report without deciding. One new fixture
directory, `tests/speckit-pro/unit/fixtures/feedback-sweep/`, holds the golden
corpus, named for the durable behavior rather than for the spec id.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. The reviewability warn is not a constitution
violation: the preset's thresholds warn above 400 reviewable LOC and 6
production files and block above 800 and 8, and this slice is under both blocks.
The warn, its derivation, its acceptance, and the split option that was
considered and rejected are recorded in "Reviewability Budget, derived by hand".

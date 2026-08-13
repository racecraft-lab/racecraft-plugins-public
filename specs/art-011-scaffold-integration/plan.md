# Implementation Plan: Scaffold Integration — blind-spot pass and autopilot chain

**Branch**: `art-011-scaffold-integration` | **Date**: 2026-08-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-011-scaffold-integration/spec.md`

## Summary

Scaffold gains two behaviours and loses none. Before the grill-me interview it
dispatches the shipped read-only `codebase-analyst` for a blind-spot pass, prints
at most five ranked findings with an explicit set-aside count, and seeds them
into the interview through the `scope` argument grill-me already consumes. After
Step 8, once every scaffold-owned artifact is committed and pushed, it runs one
read-only pre-chain check, asks one structured confirmation, and either chains
into the autopilot plan stage or prints the hand-off command. Either way it
closes with one printed report naming what exists and one next step.

The technical approach is fixed by the interview (21 questions) and three clarify
sessions: **every change is prose in two `SKILL.md` files**. No code, no scripts,
no agent definitions, no new tool grants, no new files. The pass is a subagent
dispatch because scaffold holds `Agent` but not Grep, Glob, or Bash, and widening
that grant is out of scope (Q2, FR-002). The engine is reused unmodified, which
is what keeps the Layer 6 sha256 corpus chain unstaled. Two platform variants
implement one flow, diverging only where the platform forces it: on Codex the
chain fires only when the session is already rooted inside the spec worktree,
which is the exception rather than the rule (FR-015a).

Phase 0 resolved both questions the design concept routed here. Prompt-level
framing of `codebase-analyst` is sufficient, and its read-only reach covers the
git-history chase on both platforms (research.md R2). The pre-chain rooting test
is the Codex guard's own path-resolution predicate, not a root comparison
(research.md R4).

## Technical Context

**Language/Version**: Markdown skill definitions read by an agent runtime. No
programming language is introduced. Repository tooling that this change touches
stays on Python 3.11+ standard library (constitution II, FR-023).

**Primary Dependencies**: three already-shipped surfaces, all consumed
unmodified — the read-only `codebase-analyst` agent
(`speckit-pro/agents/codebase-analyst.md`, `speckit-pro/codex-agents/codebase-analyst.toml`),
the `grill-me` skill's existing `scope` argument, and the `speckit-autopilot`
skill's plan stage. Normative contract recovered from git history:
`git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md`.

**Storage**: N/A. The closing report is printed, never written to a file
(design concept, Decisions recorded without a question). The only durable records
are the design concept's header line and the workflow file, both of which already
exist.

**Testing**: Layer 1 structural (`validate-skills.py`, `validate-codex-skills.py`),
Layer 8 Codex parity (`validate-codex-parity.py`), Layer 2 trigger evals on both
platforms as a **scheduled manual gate**, and UAT evidence for the pass and the
chain. Nothing new is executable, so no fixture can assert against the two
behaviours directly (Q21).

**Target Platform**: the Claude Code plugin runtime and the Codex CLI plugin
runtime, from one `speckit-pro/` source tree that ships to both installers.

**Project Type**: plugin skill definitions (prose). Not a library, service, or
application.

**Performance Goals**: N/A. One added subagent dispatch per scaffold run, awaited
before the interview begins.

**Constraints**: description ≤ 1024 characters, hard, landing at 1015 with 9
characters of headroom; Codex body ≤ 8000 words, currently 3250; exactly two
production files and neither may gain a `references/` directory (FR-022); no new
or edited agent definition (FR-002); no widening of scaffold's `allowed-tools`
(FR-002); no new executable machinery (FR-023); Layer 2 case queries ASCII-only
(FR-021b).

**Scale/Scope**: 16 edit sites across 2 production files (7 Claude, 9 Codex),
plus 4 new trigger cases in each of 2 test fixtures, plus one roadmap
reviewability-declaration amendment. 31 functional requirements, 12 success
criteria, 4 user stories. The error-handling checklist domain added FR-010a and
its two edit sites, C3a and X4a; the ux domain added FR-015c and widened C4, C5,
C6, X5, and X7 without creating a site. The production surface is unchanged at
two files throughout.

**Reviewability Budget**: harness/adapter (primary); docs/process (secondary);
projected reviewable LOC **322** against a 400 warn ceiling; 2 production files;
9 changed files in the diff of which 4 are generated; **within budget**, one
slice, no split. The plan-phase estimator returns 0 for structural reasons
explained below; 322 is the measured `estimate-spec-size` figure and is the one
to review against.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.

- MODIFIED speckit-pro/skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md
- MODIFIED tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json
- MODIFIED tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json
- MODIFIED docs/ai/specs/html-artifacts-technical-roadmap.md

**What this table counts, and what it deliberately does not.** These five are
every file a human edits by hand. The first two are the production surface; the
next two are test fixtures; the fifth is the roadmap entry's reviewability
declaration, which this plan reconciles below and which spec.md's closing
Assumption makes part of this slice once the measured figure diverges from the
declared one. It does diverge, so the amendment lands here rather than being
deferred.

Four further files change in the diff and are **excluded from this table on
purpose**, because they are generated artifacts that
`python3 scripts/refresh-release-artifacts.py` produces from the two source
files, and the repository's review rules exclude generated payloads and
installed-cache proofs from review (root `AGENTS.md`, `REVIEW.md`). Counting them
would inflate a projection whose unit is *reviewable* LOC with lines no reviewer
reads. They are listed in full at research.md R8 and in the verification plan
below, so nothing is hidden — the diff shows **9 changed files, 5 of them
reviewable, 2 of them production**.

**Reconciliation with the roadmap.** The roadmap entry for ART-011 declares
approximately 4 production files and 162 LOC. The settled surface is **2**
production files. The declaration was stale in the safe direction: the interview
reduced the surface when Q2 chose to reuse `codebase-analyst` rather than author
a dedicated agent, and Q3 chose the existing `scope` channel rather than a new
grill-me argument. Together those two decisions removed the two files the roadmap
anticipated. The roadmap entry should be amended to **2 production files** and
**322 LOC**, both of which stay well under the warn thresholds, so nothing is
blocked either way.

### What the estimator actually returned, and why it is 0

Run against this table, `estimate-reviewable-loc` returns:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":0,"modified":5,"total_entries":5},
 "greenfield":false,"thresholds":{"warn":400,"block":800,
 "greenfield_multiplier":1.5,"base_warn":400,"base_block":800}}
```

The table parsed correctly — all five entries were read, `modified: 5`,
`total_entries: 5`, matching the five rows above — so this is **not** a
formatting failure. The projection is 0
because the helper classifies production files by a fixed heuristic at
`speckit-pro/speckit_pro_runner/helpers/read_only.py:4185-4186`: a path is
production only when it starts with `src/`, `app/`, `lib/`, or `scripts/`, or
ends in `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, or `.sql`. It then computes
`projected = production * 40`.

This repository's production surface is Markdown skill definitions under
`speckit-pro/` and JSON fixtures under `tests/`. **None** of those match, so
`production` is 0 and the projection is 0 by construction. The heuristic is
web/TypeScript-shaped and is structurally blind to a plugin repository whose
shipped artifacts are prose. Every speckit-pro prose spec estimates 0 here, not
just this one.

**Consequences, stated plainly:**

- The table is **not** adjusted to game the heuristic. Declaring these files under a `scripts/` path or renaming them to match an extension would produce a number by lying about the surface, and the instruction was to fill the table accurately.
- The figure to review against is `estimate-spec-size`, which is what spec.md already cites and what the design concept ran. Measured in this worktree at both inputs: 4 user stories, 2 files, modify-weighted, **13 FRs → `{estimated_loc: 187, suggested_slices: 1, status: "ok"}`** (reproducing spec.md's 187 exactly), at the plan-time **28 FRs → `{estimated_loc: 300, suggested_slices: 1, status: "ok"}`**, and at the spec's final **31 FRs → `{estimated_loc: 322, suggested_slices: 1, status: "ok"}`** after the checklist phase added FR-010a and FR-015c and corrected a pre-existing undercount of the suffixed FRs.
- 322 is the honest figure and is the one carried into the Reviewability Budget above. It is higher than 187 only because the FR count grew from 13 to 31 across three clarify sessions and three checklist domains; the production surface did not move. Both figures are under the 400 warn ceiling and both return one slice, so the split decision is unchanged either way.
- `status: "pass"` from the plan-phase estimator is real and nothing is blocked. It just carries no information about this change.

This is a tooling gap in `estimate-reviewable-loc`, not a defect in this feature.
It is worth a follow-up spec, and it is recorded here rather than silently
absorbed because the roadmap's stale file count was supposed to be reconciled
against this estimator's output.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.2.0. **Initial check:
PASS. Post-design re-check: PASS.** No violations, so Complexity Tracking stays
empty.

| Principle | Verdict | Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | No new plugin component. Two existing `SKILL.md` files are edited in place; both keep valid frontmatter and their existing directory layout. No test moves into the install-facing plugin directory. |
| II. Cross-Platform Runtime & Script Safety | PASS, and strengthened | FR-023 forbids new executable machinery outright. This change adds zero scripts, zero Bash, zero `jq`. The FR-013a pre-chain check reuses `git rev-parse --show-toplevel` and `git status --porcelain`, both of which the skills already run at Step 3.5. |
| III. Semantic Versioning | PASS | No manual version edit. release-please owns the bump; `scripts/refresh-release-artifacts.py` syncs the marketplace registries. |
| IV. Test Coverage Before Merge | PASS | No new Python helper, gate, or repository tool, so no Layer 4 unit coverage is owed. Both edited skills stay under Layer 1 structural validation, and FR-021b adds six new Layer 2 trigger cases. `python3 tests/speckit-pro/run-all.py` must pass with zero failures. |
| V. Conventional Commits | PASS | Commits and the PR title use `feat(speckit-pro): ...`. The change adds capability to a shipped skill, so `feat` is the correct type and `speckit-pro` the correct scope. A `release-note` fence is required on a `feat` PR. |
| VI. KISS, Simplicity & YAGNI | PASS, and load-bearing | This principle decided the shape. No skip flag (Q17), no operator-configurable cap (Q13), no separate findings artifact (Q8), no new grill-me argument (Q3), no dedicated agent (Q2), no runner helper for the report (Q21). Every one of those is an abstraction the interview considered and rejected. |

**Reviewability requirements the constitution's plan gate additionally demands**:

- **Primary review surface**: harness/adapter — the two `speckit-pro` skill definitions. **Secondary**: docs/process — this feature's own spec artifacts and the roadmap status line.
- **Budget**: 322 reviewable LOC (measured `estimate-spec-size`), 2 production files, 9 total changed files of which 4 are generated. All three are under the warn thresholds (400 LOC, 6 production files, 15 total files). One primary surface. **Within budget.**
- **Split decision**: remains one spec. The four behaviours are one operator flow through one pair of files. Splitting would ship a pass whose findings go nowhere, or a report with nothing to report. The estimator returns one suggested slice.
- **PR review packet source**: spec.md § PR Review Packet Requirements, which fixes the nine required sections and names the two deferrals (ART-007 for draft-PR creation; the archive-hygiene question of where the ART-006 contract should live).

## Project Structure

### Documentation (this feature)

```text
specs/art-011-scaffold-integration/
├── spec.md              # 31 FRs, 12 SCs, 0 open markers (28 at plan time; +FR-010a and +FR-015c from the checklist phase, and a pre-existing undercount corrected)
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output — 11 grounded decisions
├── contracts/           # Phase 1 output
│   ├── blind-spot-pass.md      # dispatch, finding shape, seeded block, header line
│   └── chain-handoff.md        # pre-chain check, confirmation, invocation, closing report
├── checklists/
│   ├── requirements.md   # written by the Specify phase, unchanged here
│   ├── api-contracts.md  # Checklist phase — contract boundaries
│   ├── error-handling.md # Checklist phase — degraded, declined, and interrupted paths
│   └── ux.md             # Checklist phase — the operator sequence, the confirmation budget, the two reports
├── SPEC-MOC.md          # navigation marker (written by scaffold, unchanged)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

`data-model.md` is **not** produced. The spec's six Key Entities are prose
artifacts with fixed textual shapes, not data entities with fields, relationships,
or state transitions. Their shapes belong in `contracts/`, where they are
specified exactly, and duplicating them into a data model would create a second
record to drift — the same argument Q8 used to reject a separate findings
artifact.

`quickstart.md` is **not** produced. The verification procedure is not a
developer-facing runnable surface; it is the Layer 2 manual gate plus UAT, and
both are specified in the verification plan below with their exact commands and
preconditions. A separate file would restate that content without adding a step.

### Source Code (repository root)

```text
speckit-pro/                                  # plugin source, ships to both installers
├── skills/speckit-scaffold-spec/SKILL.md     # MODIFIED — Claude variant, 7 edit sites
├── codex-skills/speckit-scaffold-spec/SKILL.md  # MODIFIED — Codex variant, 9 edit sites
├── agents/codebase-analyst.md                # read unmodified — the pass engine (Claude)
├── codex-agents/codebase-analyst.toml        # read unmodified — the pass engine (Codex)
└── skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
                                              # read unmodified — owns WORKFLOW_TERMINAL_STATUSES

tests/speckit-pro/
├── layer2-trigger/evals/speckit-scaffold-spec-trigger.json        # MODIFIED — +3 cases
├── layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json  # MODIFIED — +3 cases
└── layer1-structural/                        # unchanged — validators that gate this change

docs/ai/specs/
└── html-artifacts-technical-roadmap.md       # MODIFIED — ART-011 reviewability
                                              # declaration: ~4 files/162 LOC -> 2 files/322 LOC

dist/claude/, dist/codex/                     # REGENERATED — not hand-edited
tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/
                                              # REGENERATED — not hand-edited
```

**Structure Decision**: no new structure. This is an in-place edit of two
existing skill definitions at known anchors, plus additive cases in two existing
test fixtures. The prompt's instruction is explicit and the plan honours it:
insertions at named seams, not a restructure, and no renumbering of surrounding
steps.

## Execution Flow — the insertion map

This is the heart of the plan. Each row is one edit site with its anchor, so
`tasks.md` can be generated mechanically and a reviewer can check the diff against
a list rather than a description.

### Claude variant — `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`

| # | Site | Anchor | Operation | Requirements |
|---|---|---|---|---|
| C1 | Frontmatter `description` | line 3 | Replace **sentence 3 only**. Sentences 1, 2, 4, 5 stay byte-identical | FR-021, FR-021a |
| C2 | New `### 3.6 Blind-Spot Pass (IN the Worktree)` | after Step 3.5's closing paragraph, before `### 4. Run Grill Me Interview` | Insert. Do **not** renumber Steps 4–8 | FR-001–FR-007, FR-011 |
| C3 | Step 4 grill-me invocation | the `Skill("grill-me", args: {...})` block, `scope:` line | Amend so `scope` carries the roadmap text **plus** the labelled findings block | FR-008, FR-009, FR-010 |
| C3a | Step 4 post-interview verification | the existing `Must contain Goals, Non-goals, Design Tree (Q&A log), and Open Questions` assertion | Extend by one key: verify the `**Blind-spot pass:**` line is present in the header blockquote and `Edit` it in when absent | FR-010a |
| C4 | `## Scaffold Complete` report, **two lines** | `**Review both files first**` and `**Ready to run:**` with the command under it | Soften the first to `**Review both files**`. Relabel the second to `**If you stop here, run:**` and add the `--stage plan` token to its command. Neither line is validator-pinned; only the `## Scaffold Complete` heading is | FR-013, FR-015c |
| C5 | New `### 9. Chain into the Planning Stage` | after Step 8's closing `**NEVER push to main.**` paragraph | Insert. Carries the printed what-accepting-does line **before** the confirmation, and the printed invocation **before** running it on accept | FR-012, FR-013, FR-013a, FR-014, FR-015, FR-015b, FR-015c |
| C6 | New `### 10. Closing Report` | after C5 | Insert. **Instruct the reader to read `WORKFLOW_TERMINAL_STATUSES` from `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`; do not write the six status literals into this file.** Carries a next-step rule for **all three** headings and the four render triggers | FR-016–FR-020 |

The `## Scaffold Complete` report stays exactly where it is: a **top-level
heading between Step 7 and Step 8**, not a subsection of Step 7 — an earlier
draft of this plan said "inside Step 7", which is wrong and would send an
implementer looking for it under the wrong anchor. It sits ahead of Step 8, so
C5 and C6 append after the end of the procedure. Anchor on the literal heading
strings, never on a step number. That
ordering is what satisfies FR-016: the operator is told what scaffold produced
before being asked whether to continue.

**Payload constraint (research.md R9)**: none of C1–C6 may be placed between the
`## Codex Skill-Selection Guard` heading and the next `## ` heading. The Claude
payload build strips that region, so text placed there ships to nobody. All six
sites sit in the frontmatter or under `## What to Do`, well clear of it.

### Codex variant — `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`

| # | Site | Anchor | Operation | Requirements |
|---|---|---|---|---|
| X1 | Frontmatter `description` | line 3 | Identical replacement to C1, byte for byte | FR-021, FR-021a |
| X2 | Hard Constraint | `Do not run the autopilot at the end. Setup stops once the workflow is ready, committed, and pushed.` | Amend to be conditional on the session's rooting rather than absolute | FR-022 site 1 |
| X3 | New `### 3.6 Blind-spot pass (in the worktree)` | after Step 3.5's closing paragraph, before `### 4. Run the Grill Me interview` | Insert, same content as C2 in Codex idiom | FR-001–FR-007, FR-011 |
| X4 | Step 4 grill-me input description | the `Invoke $grill-me ... with a setup-mode marker` bullet list | Amend so the scope input carries the labelled findings block. **Do not disturb the five pinned picker strings in this same step** | FR-008, FR-009, FR-010 |
| X4a | Step 4 close, after the `If grill-me aborts` paragraph | no existing anchor — the Codex variant performs **no** post-interview verification read today | Insert the same verification C3a extends: read the design concept, confirm the `**Blind-spot pass:**` key, write the line when absent | FR-010a |
| X5 | `## Output` next-step instruction | the `the exact next step: start a new Codex task rooted at that worktree...` bullet | Amend to add the conditional chain while keeping new-task guidance for the ordinary case. That guidance **is** the Codex hand-off command's rooting precondition, so it must survive as part of the command rather than as commentary | FR-022 site 2, FR-015c |
| X6 | `## Output` parent-checkout prohibition | `Never hand off only the inner workflow path from the parent checkout. Do not suggest running autopilot from main, a detached checkout, or any workspace root other than the generated spec worktree.` | **Keep both sentences verbatim.** Preface them to apply when the chain does not fire | FR-022 site 3 |
| X7 | `## Output` extension | after X6 | Insert the pre-chain check, the printed what-accepting-does line, the confirmation, the printed invocation, the chain, and the closing report. **Same frozenset constraint as C6: read the shipped set, never write the six literals here** | FR-012–FR-020 |
| X8 | `## Output` citation | `see openai/codex#7480` | Replace with the official Codex skills documentation, corroborated by `openai/codex#11817` | incidental defect |

FR-016 is satisfied differently here and the plan follows the spec rather than
forcing symmetry: the Codex scaffold report is a top-level `## Output` section
that already follows Step 8, so the chain and closing report **extend that
section** rather than becoming new numbered steps.

**Terminal-status constraint (FR-020, ART-006 §4)**: C6 and X7 are the only two
sites where the completion test is written, and both carry the same prohibition.
The vocabulary is owned by the `WORKFLOW_TERMINAL_STATUSES` frozenset in
`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`.
Each variant must instruct its reader to **read that frozenset**, and must not
write the six status literals into the `SKILL.md` body. Two of the six differ
only by a Unicode variation selector and render identically, so a hand copy is
both forbidden and easy to get wrong. `contracts/chain-handoff.md` §9.1 carries
no list either, deliberately, so there is nothing on the transcription path to
copy from.

**Pinned-string constraint (research.md R6)**: X2, X5, X6, and X8 are all safe —
none of those sentences is string-pinned by
`tests/speckit-pro/layer1-structural/validate-codex-skills.py`. X4 is the risky
one, because the five pinned Grill Me picker strings live in the same step. They
must survive verbatim.

### Test fixtures — three cases per platform, ASCII only

Added to `tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json`
and `tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json`
**only**, in the existing `{query, should_trigger}` shape, taking each from 16
entries to 20 (10 positive, 10 negative). The fourth case was added after an
independent review observed that the explicit-precondition negative tests the
easy form of the misroute; the short bare form is the likely one.

| Case | `should_trigger` | Tests |
|---|---|---|
| Positive 1 | `true` | The blind-spot capability phrase — a query asking to scaffold a spec and surface what the roadmap author missed before the interview |
| Positive 2 | `true` | The chain capability phrase — a query asking to set up a SPEC-ID and continue straight into planning |
| Negative 1 | `false` | The near-miss that stresses "planning" against the preserved boundary: a query about running the plan stage of a workflow file that **already exists**, which must route to autopilot |

The negative case is the one that matters. "Planning" is new to scaffold's
description and the sibling autopilot description already claims it, while
scaffold's boundary clause is scoped to "run a populated workflow" prompts rather
than plan-stage prompts. The documented mitigation is **precondition contrast**,
not word-avoidance: scaffold creates a workflow file that does not yet exist,
autopilot consumes one that does. The negative case must be written to make that
contrast the deciding signal.

Six other fixture files per platform already carry scaffold-shaped negative cases.
Those need **no** new cases, because those skills' descriptions do not change, but
they must be re-run as regression coverage (FR-021b).

## Verification plan

Ordered, with the exact commands. Steps 1–3 are automated; step 4 is the
scheduled manual gate; step 5 is human acceptance.

**1. Regenerate before validating.** Plugin source changed, so the generated
artifact contract applies:

```bash
python3 scripts/refresh-release-artifacts.py
```

This rebuilds both payloads, content-syncs the two installed-cache fixtures,
refreshes the proof-tree hashes, and regenerates the payload-completeness,
zero-Bash, and release-readiness evidence. Running it **before** the suite avoids
a false red from a stale payload. The Layer 6 digest chain needs no action,
because no agent definition changed (research.md R8).

**2. Full suite:**

```bash
python3 tests/speckit-pro/run-all.py
```

Must pass with zero failures (constitution IV). The gating checks for this change
are the description cap and angle-bracket rules in
`tests/speckit-pro/layer1-structural/validate-skills.py:121-125`, the Codex body
word cap and the five pinned scaffold strings in
`tests/speckit-pro/layer1-structural/validate-codex-skills.py`, and Codex parity
in `tests/speckit-pro/layer1-structural/validate-codex-parity.py`.

**3. Hand verification of the three things no test covers:**

- **Description length**: measure the final string on both platforms. Expected exactly **1015** characters, 9 under the cap, no angle brackets.
- **Description byte-identity (FR-021a)**: diff the two frontmatter description values directly. No automated test compares them (research.md R7), so this is a required manual step, not an inference.
- **Codex body word count**: confirm it stayed under 8000. Baseline 3250, projected additions 850–1,100 after the ux domain added the two printed lines and the hand-off command's fixed form. Still roughly half the cap.

**4. Layer 2 trigger evals — scheduled manual gate, not part of FULL_VERIFY.**
Layer 2 is declared `"default": false` in `tests/speckit-pro/suite-manifest.json`,
so `run-all.py` prints these commands rather than running them:

```bash
python3 tests/speckit-pro/layer2-trigger/run-trigger-evals.py speckit-scaffold-spec
python3 tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py speckit-scaffold-spec --run
```

Preconditions, each of which makes the runner exit non-zero when absent: the
Claude runner needs a `skill-creator` skill directory; the Codex runner needs the
`codex` CLI on PATH. **The Claude runner moves the operator's installed skill
directory aside and restores it in a `finally` block, so it must never be run
from a read-only or background agent.** Evidence from both runs must be recorded
in the PR.

**5. UAT.** The two behaviours are prompt-level, so nothing is executable and no
fixture can assert against them (Q21). UAT confirms the FR-006 status strings
verbatim, the single-confirmation count (SC-007), the decline path leaving
everything pushed (SC-006), and the closing report's artifact index matching disk
(SC-009).

The ux checklist domain added five operator-facing confirmations to the same run,
none of which any fixture can reach either:

- The sentinel prints with its **one-word** spelling intact while scaffold's own lines stay hyphenated (FR-006). The failure mode is a silent normalisation, so read the emitted string rather than the source.
- The printed what-accepting-does line appears **before** the confirmation, and the invocation appears **before** the chain runs (FR-013, FR-014).
- One command, three appearances: the Scaffold Complete report's `**If you stop here, run:**` line, the confirmation's alternative, and the closing report's next step are byte-identical per platform (FR-015c).
- Each of the three headings ends on a defined next step, `## Planning Complete` included (FR-018).
- The closing report renders on the Codex ordinary path — pre-chain check fails, nothing asked — and its outcome line leads with what is finished (FR-017, FR-018).

## Traceability — requirement to edit site

| Requirement group | Claude sites | Codex sites | Verified by |
|---|---|---|---|
| FR-001–FR-007, FR-011 (blind-spot pass) | C2 | X3 | UAT; Layer 1 structure |
| FR-008–FR-010 (seeding and the record) | C3 | X4 | UAT; Layer 1 pinned-string survival |
| FR-010a (record verified, not assumed) | C3a | X4a | UAT: delete the header line from the design concept before the verification read and confirm scaffold rewrites it |
| FR-012–FR-015b (chain hand-off) | C5 | X2, X5, X6, X7 | UAT; ART-006 §3 conformance review |
| FR-013, FR-015c (the two Scaffold Complete report lines; the hand-off command's fixed form) | C4, C5 | X5, X7 | UAT: decline on each platform and confirm the command printed in the report, in the confirmation's alternative, and in the closing report's next step are one string |
| FR-016–FR-020 (closing report) | C6 | X7 | UAT; ART-006 §4 conformance review |
| FR-021, FR-021a (description) | C1 | X1 | `validate-skills.py`; hand diff |
| FR-021b (Layer 2 cases) | fixture | fixture | Layer 2 manual gate |
| FR-022 (parity, three Codex sites) | all | X2, X5, X6 | `validate-codex-parity.py`; side-by-side read |
| FR-023 (no new machinery) | all | all | diff shows no new file, script, or tool grant |
| incidental citation defect | not applicable | X8 | link check |

## Known gaps and deferrals

**Named deferrals** (spec.md § PR Review Packet Requirements requires these be
named, and they are):

- **ART-007** owns draft-PR creation, and therefore the closing report's PR URL. For every run in this release the report states plainly that there is none (FR-018, SC-008). This is the expected outcome, not a degraded one.
- **Archive hygiene for the ART-006 chain contract.** It is normative and lives only at a git object reference. Relocating it into the tree is a separate hygiene change, not a widening of this spec. Planning did not need the relocation; the recovery command worked (research.md R1).
- **The same `openai/codex#7480` miscitation in two other files**, `speckit-pro/codex-skills/grill-me/SKILL.md:289` and `speckit-pro/codex-skills/speckit-coach/SKILL.md:25`. Both are left untouched. Fixing them would add production files to a surface FR-022 fixes at two, and grill-me is a file Q3 and Q19 explicitly rule out changing.

**Residual risks, recorded not closed:**

- **The "planning" routing risk.** Neither consensus analyst could settle whether the new word pulls plan-stage prompts away from autopilot, because only a live Layer 2 run can. FR-021b's negative case is written to test exactly that near-miss, and the Layer 2 run is a scheduled manual gate rather than something `run-all.py` catches.
- **Codex analyst reasoning effort.** `codebase-analyst.toml` pins `model_reasoning_effort = "low"`, validated on consensus fixtures rather than on blind-spot work (research.md R2). FR-002 forbids tuning it. The consequence is finding quality on Codex, not correctness, and the fail-open path plus the FR-006 sentinel keep every outcome distinguishable. Measured at UAT; if framing proves insufficient the remedy is a new spec, per the design concept.

## Where the spec under-determines the implementation

Three places. Each is resolved here rather than left to the implementer, and each
resolution is recorded so a reviewer can disagree with it explicitly.

**1. The dispatch must be awaited.** FR-002 fixes the engine and FR-011 fixes the
flow, but neither stated that scaffold waits for the analyst's summary before the
interview starts. It matters because the Claude agent definition carries
`background: true`: a background dispatch returns an identifier, not an answer.
Without an explicit await, FR-001's "immediately before the interview" and
FR-011's "flow straight into the interview" are both unsatisfiable.
**Resolution**: copy the house consensus pattern — Claude dispatches with
`run_in_background: true` and then awaits completion; Codex uses a bounded
`wait_agent` loop until the actual summary arrives, treating a status update or
an expired poll as not-the-result (research.md R3). **This has since been
promoted into the spec as FR-002a**, which also fixes the missing bound: a poll
expiring is a cue to keep polling, and abandonment is governed by one pass
execution deadline of five minutes from dispatch, platform-general. The plan
no longer under-determines this; the entry is kept because the reasoning is the
audit trail for why FR-002a exists.

**2. The Codex runnable invocation is not what the contract table shows.**
ART-006 §3 lists the Codex chain invocation as `<workflow-file> --stage plan`,
with no skill token. `stage-invocation.md` §1 explains why: each distribution's
argv begins at the workflow path, and the leading command token "has no Codex
counterpart" as a *parity* concern. Read literally, the table would produce a
Codex chain that invokes a bare path. **Resolution**: the runnable Codex line is
`$speckit-autopilot` followed by that argv, which is the invocation form the
whole Codex skill set already uses and the form X8's corrected citation
documents. The argv itself is unchanged from the contract (research.md R1).
**This is a deviation from a normative source, not a quotation of one, and all
three artifacts now say so**: spec.md FR-014 carries a per-platform table with a
`Provenance` column marking the Codex row as a recorded deviation, and
`contracts/chain-handoff.md` §5 carries the same record. A reviewer reconciling
this spec against ART-006 §3 will find the two rows differ by design.

**3. The new Claude step numbers are unallocated.** FR-012 places the chain
"after Step 8" and the prompt forbids renumbering Steps 1–8, but the spec never
names what the new sections are called. **Resolution**: `### 3.6` for the pass,
following the existing `3.5` convention, and `### 9.` and `### 10.` for the chain
and the closing report. Nothing existing moves. On Codex the pass is likewise
`### 3.6`, while the chain and report extend `## Output` rather than becoming
numbered steps, because that is where FR-016 puts the existing report.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Constitution Check passed on both the initial and the post-design
evaluation, so this table is intentionally empty.

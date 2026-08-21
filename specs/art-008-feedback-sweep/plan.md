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

## Trust Boundary Enforcement

This feature carries public pull-request text into agents that edit the planning
artifacts, so the trust boundary is the design, not a caveat on it. Six
mechanisms implement it. Each names where it runs, because "enforced in the
helper" and "expected of the orchestrator" are different guarantees and the
distinction is the point.

**1. The allowlist runs in the helper, ahead of everything.** `sweep-pr-feedback`
applies the FR-005 author-association filter itself and returns `candidates` and
`excluded`. The candidate records carry id, surface, author, association,
truncation flag, and export metadata — and **no body**. An untrusted comment's
text is therefore absent from the helper's output by construction, not by an
orchestrator remembering to drop it. This is the placement the spec's own
security posture requires: the filter is a fixture-pinned Python surface, so it
is provable, while orchestrator judgment is not.

**2. Classification consumes the candidate list and nothing else.** The
orchestrator holds the full observation it captured, untrusted bodies included,
so the helper's filter is only as good as what the orchestrator does next. The
rule: the classification loop iterates `candidates`, and a body is read out of
the captured observation **only for an id present in that array**. No path
enumerates the observation directly. Without this, mechanism 1 filters an
envelope while the orchestrator reads around it — the filter would be real and
bypassed at the same time.

**3. The recognized-export payload (FR-007e).** For a recognized comment the
consensus payload is the helper's export record plus the body with every matched
registered line removed. The remainder is delimited and labelled as
reviewer-supplied data rather than concatenated as instruction. Tagging without
removal does not satisfy FR-007c; that reading is available from FR-007c's
wording and is the one this plan forecloses.

The labelling half is new work, not an existing guarantee this slice inherits.
The shipped Gap Remediation prompt template in `consensus-protocol.md` is a bare
`## Gap Description` heading over an inserted-text placeholder, with no
delimiter and no "treat this as data" instruction, and the three analyst
definitions describe their input as "the relevant context" — trusted framing.
The analysts' `disallowedTools` frontmatter blunts blast radius but says nothing
about the input, and the grounding note governs their **output**. So a sweep
that hands a reviewer body to that template inherits raw interpolation. The
sweep supplies its own delimiting rather than assuming the protocol does it.

**4. The edit surface is an allowlist, checked twice (FR-012b).** At
classification, a requested change outside `spec.md`, `plan.md`, and `tasks.md`
in the feature directory takes `deferred` with the refused target named in the
disposition and the reply. At the write, the resolved target path is validated
against the same three-entry set in code before any write; a violation stops the
run. That stop reports like the others this feature defines: it names the
refused target path, the comment id it came from, and the resume path, so the
operator can tell a mis-routed amendment from a broken tool. FR-017 and FR-019
both fix a report shape for their stops, and a stop without one would be the
only silent halt in the sweep. The two checks catch different failures — prose a
mis-routed item walks past, and a defect that would otherwise write outside the
surface — so neither replaces the other.

This fills a repo-wide hole rather than restating a local rule. The consensus
synthesizer's output contract accepts a free-form `File: <path>` and nothing
downstream validates it, and the three-artifact enumeration in
`consensus-protocol.md` is justified there by **write contention** — serializing
concurrent edits — not by scope safety. No allowlist, no "only these three
files" guard, and no rejection of an out-of-scope edit target exists anywhere in
the repository today. The shape to copy is
`speckit-pro/artifact-gallery/SPA-CONTRACT.md`, which already names
pull-request-derived values untrusted and answers the escaping question with
"the value goes somewhere else" rather than with a quoting rule. That contract
is scoped to generated HTML; this is the same discipline applied to an edit
target.

**Staging, and the `git add -A` hazard.** Each amendment commit stages exactly
the one artifact path it amended, never a directory. The precedent is the
`Draft PR` bookkeeping commit in `phase-execution.md`, which stages the workflow
file alone because the directory "also holds untracked run byproducts that a
directory-wide add would sweep in". The hazard is specific and easy to miss: the
sweep is a **Phase 7 setup step**, and Phase 7 is the one phase whose existing
commit path uses `git add -A`. An amendment commit that inherits that pattern
would stage the entire worktree, which defeats the edit-surface allowlist at the
last step — the check would pass on the target path while the commit carried
everything else. Amendment and bookkeeping commits here follow the enumerated
single-path form, not the Phase 7 form.

**5. `self_login` is derived, then validated.** The orchestrator reads it from
the live authenticated session at call time rather than from configuration, the
way FR-004a requires the author-association field be read fresh. The helper then
requires it to be a non-empty string after stripping surrounding whitespace;
absent, empty, or whitespace-only returns `invalid_input` rather than
proceeding. The helper cannot go further than presence, because its contract
forbids it from reaching the network, so it has no second independently sourced
value to compare against — verification is provenance, not checking.

What an empty value actually breaks, stated correctly: comparison is exact, so
an empty account matches **no** real comment author. The author condition is
permanently false, the conjunction is therefore always false, and **no comment
is ever excluded as a self-reply**, including the sweep's own. That reaches the
same non-convergence FR-006a describes, but by disabling the rule rather than by
narrowing it to the marker half. The distinction matters because the two
failures have opposite shapes and a reader expecting the wrong one would test
for the wrong thing.

**6. The shell boundary is verified in both directions.** FR-004b covers reads
and writes, so the captured-command fixture SC-009 rests on captures the **read**
argv as well as the reply writes. Quickstart Scenario 4 pins the reply half;
without the read half, "every command the sweep issues" is asserted against a
fixture that inspects some of them. The helper never runs `gh` at all, and the
request reaches it as one JSON document on stdin, so no field of it is ever a
shell argument.

**What these do not claim.** None of the six inspects a trusted body for
adversarial content, and none is a permissions check. The trust unit is the
comment, recorded in the spec's Assumptions: a write-capable author who quotes
untrusted text is treated as endorsing it. Mechanisms 3 and 4 are what make that
residual tolerable — one keeps a known imperative out of an analyst prompt, the
other bounds what any analyst outcome can reach.

**Budget note.** These add an estimated 15 to 30 reviewable lines over the table
below: the path check and `self_login` validation are small, and the rest is
reference prose. The high end moves from 745 toward roughly 775 against the 800
block. That margin is thinner than the table states and is recorded here rather
than absorbed silently.

## Failure Paths

The sweep reads a live pull request, edits artifacts, commits, pushes, and
writes back to a reviewer, so it has five places to fail partway. Two design
decisions cover all five, and both are placement decisions rather than new
mechanism.

**One report builder, not one per stop.** FR-020 fixes a single contract —
condition, what landed, resume path — and every stop calls it. This is the
consolidation the spec needed anyway: eight stop conditions had accumulated with
their reports described one requirement at a time. Building the report once, from
the run state the orchestrator already holds, is fewer lines than eight
hand-written wordings and is the only way the what-landed part stays accurate,
since no individual stop knows what the ones before it did.

**Reads are one transaction; writes are ordered so that stopping is safe.** All
reads precede all writes, so FR-004c's discard-on-failure needs no unwind path —
there is nothing to unwind. The write side is ordered at two levels, and keeping
them apart is what makes the failure states exact. **Per amendment**, FR-012a's
existing ordering does the work: amendment commit, push, then bookkeeping
commit, repeated once for each amendment the run makes. **Replies are not part
of that cycle.** FR-015c fixes them at one point per run — after every
bookkeeping commit the run takes has landed — so the sequence is the whole
commit cycle first, replies once at the end. A stop between any two writes
leaves a state the next run reaches by a route the spec already reasons about,
so no failure needs a repair rule of its own; and because the reply point sits
after the entire commit cycle, a run that aborts inside that cycle has posted
zero replies rather than some, which is what makes the composed interrupt case
a single determinate outcome instead of two.

The one exception is the reply, which lands after the row that would otherwise
suppress it. FR-015b closes that with the marker already required by FR-015 and
already matched by FR-006 — it now carries the answered comment's id — so the
pull request itself witnesses which replies exist. No log column, no state file,
and the FR-006 anchor is unchanged because the id follows the fixed prefix.

**Budget note.** These add an estimated 35 to 55 reviewable lines: the report
builder and the reconciliation read are the substantial parts, and the remaining
stops are two or three lines each once the builder exists. Against the 775 high
end recorded above, the high end now reaches roughly **810 to 830, which crosses
the 800 block**, while the midpoint stays under it. That is a threshold crossing
rather than a thinner margin, and it is flagged for the operator rather than
absorbed: the levers are the serialization-family deferral already described
under the split option, accepting the block explicitly, or re-slicing. This plan
does not choose among them.

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
515 to 830 reviewable LOC, midpoint near 630**; 7 production files; 14 authored
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
| Reviewable LOC | ~630 (515–830) | 400 | 800 | **WARN at the midpoint; the high end crosses the block** |
| Production files | 7 | 6 | 8 | **WARN** |
| Total authored files | 14 | 15 | 25 | pass |
| Primary surfaces | 1 | >1 | >1 | pass |

**Two warns, no blocks at the midpoint. The table above is the figure as it
stood when this plan was first written, and the error-handling checklist has
since moved it.**

That pass added five requirements, and the current range is **roughly 810 to
830 at the high end with the midpoint still under 800**. The high end therefore
crosses the block; the midpoint does not. The margin the next paragraph was
written about no longer exists, and the Failure Paths section above carries the
current numbers and the three levers. Read that section, not this table, for
the live figure.

The reason the margin matters is unchanged: the implementation must hold the
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
  production files (7 against 6). Under the block at the midpoint on both (800,
  8); the high end crosses the 800 LOC block after the error-handling pass. Accepted
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
production files and block above 800 and 8. This slice is under both blocks at
its midpoint; its high end crosses the LOC block. Recorded, not hidden.
The warn, its derivation, its acceptance, and the split option that was
considered and rejected are recorded in "Reviewability Budget, derived by hand".

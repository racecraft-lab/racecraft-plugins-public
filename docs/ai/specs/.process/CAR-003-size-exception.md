# CAR-003 Reviewability Size Exception

**Spec**: CAR-003 — Evaluation Runner, Fixtures, Scoring, and Statistical Analysis
**Branch**: `car-003-evaluation-runner-scoring`
**Condition**: size-only
**Recorded**: 2026-07-25

Reviewability-Exception: infra

> The pragma above is a bare, line-anchored, case-sensitive line with no trailing
> content, matching the honored form in `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md`
> and the working precedent at `docs/ai/specs/.process/PRSG-008-workflow.md`. It must
> not be indented or fenced.

## 1. Exception type, stated precisely

The **condition** is size-only. There is no correctness finding, no malformed or
stale marker state, no failed verification, and no invalid packet. All 20 CI
checks are green and 4143/4143 tests pass.

The **class** is `infra`. This needs saying plainly, because "size" is not a
class: `speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json`
closes `exception.class` to exactly `refactor`, `infra`, `upgrade`, and the match
is fail-closed — an unknown class, a mis-cased class, or free-form prose is not
honored. `infra` is the honest fit and the precedent fit: CAR-003 builds
repository-only evaluation infrastructure plus the specification that governs it,
and the identically-shaped PRSG-008 exception used `infra` for the same reason
("the block is total-file-count driven").

This document is the operator's record of that decision. It does not make the
change smaller and does not claim the change is small.

## 2. Measured evidence

Final diff against `origin/main`: **85 files, +22539 net** (22,615 insertions,
76 deletions).

| Composition | Files | Note |
|---|---:|---|
| Authored **shipped production** source | **1** | `speckit-pro/speckit_pro_runner/materializer.py` — 247 lines, 149 logic |
| Generated or regenerated artifacts | 27 | payload copies, installed-cache proofs, hashes, generated reference pages |
| Repository-only harness under `tests/` | 38 | +13,221 |
| Specification and process documents | 32 | +7,867 |

Authored logic across the three slices measured **3,490 LOC against a ratified
1,858** — 1.88x overall, worst slice 2.48x.

These figures are authoritative and supersede the plan's estimate.

## 3. Why each threshold is exceeded

**The 800-reviewable-LOC block.** Exceeded by the authored harness logic, not by
shipped code. Slice 1 alone measures roughly 1,823 logic LOC (735 ratified at the
worst-slice 2.48x factor) — over the block on its own, before slices 2 and 3
exist. The single shipped production file contributes 149 logic lines to that
total.

**The 25-total-file block.** Exceeded 3.4x at 85 files. Three groups drive it and
none is discretionary:

- **27 generated artifacts.** Slice 1 is the only slice touching shipped runner
  source, so it absorbs the entire synchronized regeneration — `dist/claude` and
  `dist/codex` payload copies, the runner manifest and `.sha256`, twelve
  installed-cache proof fixtures, the mirrored installed-cache payload trees, and
  the generated docs-site reference page. The repo's generated-artifact contract
  requires all of them to move together with the source change. Splitting them
  from the source is not permitted; splitting them from each other produces a
  broken intermediate state.
- **38 harness files.** The evaluation platform is repository-only by
  constitutional design — it never ships. Six library modules and eight unit-test
  files carry it. The test files are the larger half (`test-successor-capability-freeze.py`
  1,211; `test-analysis-decision-ladder.py` 1,209; `test-score-bundle-adjudication.py`
  1,051; `test-experiment-policy-partitions.py` 897).
- **32 specification and process documents.** 43+ functional requirements across
  four clarify sessions and four checklist domains, eight contract schemas, and
  the workflow, design-concept, and per-slice review packets.

## 4. Why re-slicing is forbidden

The roadmap independently constrains this, in three places in
`docs/ai/specs/claude-agent-routing-technical-roadmap.md`:

- line 39 — CAR-003 carries "two required work packages"
- line 184 — "CAR-003 (502 LOC, warn) must preserve its two declared work packages"
- line 382 — "must preserve the two declared work packages"

Work Package A (treatment runner and materializer) is slice 1 and must stay intact
as one reviewable unit. Slice 1 alone exceeds the 800-LOC block. Subdividing it to
fit a threshold would break the roadmap constraint in order to satisfy the size
constraint — trading a ratified decision for a metric. So an exception is
unavoidable for at least one PR in this spec, independent of anything else.

That argument covers slice 1. It does **not** cover why slices 2 and 3 ride in the
same PR — see section 7.

## 5. Why the estimator cannot be trusted here

Two recorded false positives. Neither is evidence the change is small; both are
evidence the measuring instrument does not fit this repository.

- **`estimate-reviewable-loc` reports projected 0 and production 0.** Its
  heuristic keys on path prefixes and JavaScript extensions and matches no Python
  in this repository. A reported 0 here means "not measured", not "trivial". The
  same false negative is on record for PRSG-008.
- **The tasks-count heuristic (86 x 40 = 3,440) is meaningless.** Task granularity
  in this spec varies from a one-line manifest registration to a 1,200-line module;
  40 LOC per task is not a property of anything.

The measured figures in section 2 were produced by hand against the real diff and
are the only numbers that should be quoted.

## 6. How to review this efficiently

Read in this order. The point of the ordering is that each step makes the next
step cheap, and that the two highest-risk surfaces — the one shipped file and the
three contract decisions — come first.

### Before any slice (about 20 minutes, and it is the highest-leverage reading)

1. `speckit-pro/speckit_pro_runner/materializer.py` — 247 lines. **This is the
   entire shipped blast radius of the change.** Everything else is
   repository-only. If this file is right, no installed plugin can regress.
2. `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py`, module
   docstring only (lines 1-46). It states the two design choices the requirements
   left open, including the known FR-014 / FR-034 conflict, so you meet them as
   declared decisions rather than discovering them as defects.
3. `docs/ai/specs/.process/CAR-003-slice-1-pr-packet.md` sections 1-2, then the
   same in the slice-2 and slice-3 packets. Nine mandatory sections each; they are
   the authored review packets and they are far better than the PR body.

### Slice 1 — US1 + US2, Work Package A (the irreducible unit)

4. `specs/car-003-evaluation-runner-scoring/contracts/successor-capability-freeze.schema.json`
   (175) — the admission contract. Read before the module that implements it.
5. `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py` (1,070) —
   candidate admission as source-ledger ∩ pinned-runtime, closed exclusion
   reasons, and alias re-point detection.
6. `tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py` (696) —
   score-eligibility predicate and disposition precedence.
7. Tests, in this order: `tests/speckit-pro/unit/test-canonical-agent-materializer.py`
   (302), `test-exact-treatment-runner.py` (759), `test-successor-capability-freeze.py`
   (1,211).

### Slice 2 — US3, governed corpus and blinded scoring

8. `specs/car-003-evaluation-runner-scoring/contracts/role-corpus.schema.json` and
   `score-bundle.schema.json` (207).
9. `tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py` (278).
10. `tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py` in full (865)
    — seven hard gates, the mechanical blinding leak check, two-ballot scoring,
    adjudication, and the closed FR-034 taxonomies.
11. `tests/speckit-pro/unit/test-role-corpus-governance.py` (326), then
    `test-score-bundle-adjudication.py` (1,051).

### Slice 3 — US4, experiment policy, statistics, replay

12. `specs/car-003-evaluation-runner-scoring/contracts/experiment-policy.schema.json`
    (163) — read the two paired `allOf` branches keyed on
    `partition.qualification_eligible` first; they encode the FR-037 circular-
    dependency fix and are the single most consequential schema decision in the
    spec.
13. `analysis-plan.schema.json` (522), `experiment-assignment.schema.json` (258),
    `car-003-additive-records.schema.json` (257), `analysis-decision.schema.json` (127).
14. `tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py` (749).
15. `tests/speckit-pro/layer6-efficiency/lib/claude_analysis_decision.py` (1,283)
    — the ordered decision ladder.
16. `tests/speckit-pro/unit/test-experiment-policy-partitions.py` (897), then
    `test-analysis-decision-ladder.py` (1,209).

### Do not read linearly — verify by regeneration or by test

- The 27 generated artifacts. Check that regeneration reproduces them; do not
  diff them by eye.
- `tests/speckit-pro/layer6-efficiency/fixtures/car-003-calibration-replay.json`
  (1,252) and `car-003-role-corpus.json` (447). These are data, exercised by the
  replay and corpus tests above.

That is roughly 5,000 lines of genuinely review-bearing material out of 22,615 —
about 22%. The ordering exists so a reviewer who stops after step 3 has still seen
every shipped byte and every declared open decision.

## 7. What would have made this smaller

Stated honestly, including the part that reflects badly on the run.

**The real miss: this should have been a three-PR stack, not one PR.** The roadmap
requires Work Package A intact. WP-A is slice 1 only. Slices 2 and 3 are both WP-B
and were already split from each other during planning, so emitting them as
separate stacked PRs would have violated nothing. Doing that would have produced
one exception-bearing PR (slice 1, still over the LOC block, still needing this
exception) plus two normally-sized PRs — instead of one 85-file PR needing an
exception for its total size. The reviewability contract's own remedy was
available and was not taken. That is a process failure, not a constraint.

**The planning estimate was wrong, and predictably so.** The ratified 1,858 LOC was
derived before the four checklist domains ran. Those domains added roughly twenty
new functional requirements (FR-039 through FR-058), and the requirements are what
produced the code. The 1.88x overrun is an artifact of ratifying a budget against
a pre-remediation requirement set. A re-ratification gate after checklist
remediation would have caught it, and there is no such gate today.

**Requirement surface, not implementation verbosity, is the dominant term.** The
spec is roughly 98 KB across 43+ FRs. The modules are dense but not padded — a
total, single-valued plane-by-code mapping over 35 codes is 35 lines whether
written well or badly. Reducing this change meaningfully required reducing the
spec, which is a scoping decision that belonged before implementation.

**Three things that look reducible and are not:** the 27 generated artifacts (a
repo contract triggered by any shipped-source change); the 38 harness files (the
platform is repository-only by design, so it cannot be smaller by shipping less);
and the eight contract schemas (each is a declared parity mirror of a committed
Codex-side contract and cannot be merged or dropped unilaterally).

## 8. What this exception does not cover

- It does not excuse the unfilled PR body. The three authored review packets exist
  on the branch; the PR's Summary, What Changed, Why It Matters, and How To Review
  are still generator defaults. Fix that before review, independently of this
  exception.
- It does not resolve the FR-014 / FR-034 contradiction, which is recorded
  separately and is a correctness question, not a size question.
- It does not cover any file added to the branch after this document was written.

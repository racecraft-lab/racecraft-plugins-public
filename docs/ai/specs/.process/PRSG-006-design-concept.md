---
topic: "PRSG-006 — Plan-phase reviewability budget + gate threshold rework"
spec_id: PRSG-006
date: 2026-06-06
source-input: docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-006 section)
question-count: 10
mode: setup
stop_reason: natural
---

# PRSG-006 — Design Concept

## Goals

Make reviewable-PR sizing **preventive** (decided at plan time) instead of
**detective** (blocked at an end-stage gate), fix the size *metrics*, and replace
the broken one-keyword escape hatch with **typed, auditable exception classes**.

Concretely, PRSG-006 ships:

1. **A plan-phase reviewability budget (US1).** A new deterministic
   `estimate-reviewable-loc.sh` runs during autopilot's **plan** phase, projects
   each slice's production-LOC footprint **from `plan.md`'s planned-file structure**,
   **auto-approves under budget** (silent pass), and **surfaces only when over** —
   advisory/record-and-proceed in the autonomous run, a human decision in
   interactive use.
2. **A gate threshold rework (US2) on `reviewability-gate.sh`.** Re-scope the LOC
   metric to **production code only**; keep `400` warn / `800` block but on that
   narrower metric; add a **1.5× greenfield allowance** for all-new slices;
   **downgrade primary-surface-count from a blocker to a warning**; and replace the
   loose three-phrase exception keyword with a **typed `Reviewability-Exception: <class>`
   pragma** over a **closed, fail-closed enum** `{refactor, infra, upgrade}`.
3. **A roadmap-template update** so the Reviewability Contract the gate's `setup`
   mode parses stays consistent with the reworked gate (new thresholds, surface =
   warning, typed pragma).

The headline Phase-3 definition-of-done this satisfies: *"plan phase auto-approves
under budget and the surface-count blocker is gone."*

## Non-goals

- **The split-PR engine** — atomicity router (PRSG-007), layer-planner (PRSG-008),
  multi-PR emission (PRSG-009). PRSG-006 is **upstream sizing only**: a plan-time
  budget plus a corrected gate. It does not split anything.
- **Hardening the hatch / re-slicing wiring** — making an over-budget result *block*
  or trigger re-slicing is explicitly **PRSG-010** ("harden the hatch LAST").
  PRSG-006 keeps the gate detective-but-correct and the plan budget advisory
  (answered in Q3).
- **Removing the exception boilerplate from the template** — PRSG-006 *modernizes*
  the template's exception vocabulary to typed classes; **PRSG-010** later *removes*
  it entirely. The two compose (Q8).
- **Retro-migration / legacy back-compat** — old `split/transition/ratified exception`
  phrases stop being honored (new-specs-only); de-boilerplating existing project
  roadmaps is **PRSG-011** (answered in Q9).
- **Aligning the gate's `is_excluded_generated()` to the `.process/` glob** — that is
  **PRSG-001**'s deliverable (a dependency, not in scope here).
- **Differential per-class exception allowances** — all three classes flip a block
  equally in v1; per-class budgets are YAGNI (Principle VI; Q7).
- **Product code** — this is a plugin skill/script/template change.

## Design Tree (Q&A log)

### Q1 — Plan-phase budget signal (US1's central ambiguity)

**Branch:** Budget mechanism / input signal

US1 places the budget at the **plan** phase, but in SDD the plan phase runs *before*
`tasks.md` exists — so there is nothing to count yet, and the gate's existing
task-count heuristic (`measure_feature_dir`: task-count × 40) is unavailable.

- **Recommended answer (chosen):** **Compute the projection from `plan.md`'s
  structure.** `estimate-reviewable-loc.sh` parses the planned files/modules declared
  in `plan.md` and projects production-LOC via a per-file heuristic that reuses the
  gate's existing `×40` style constant.
  > Fully deterministic → testable by an L4 fixture (Principle II, scripts-first
  > mandate). No agent-authored number to fudge. `plan.md` is the richest signal that
  > actually exists at plan time.

**Alternatives offered:**
- *Validate a declared projection in `plan.md`*: simpler script, but the estimate is
  agent-authored — less deterministic, gameable.
- *Move the check to the tasks phase*: honest task-count signal, but no longer
  preventive-at-plan-time; collapses toward the existing tasks-mode gate.

**User's answer:** Compute from `plan.md` structure (Recommended).

---

### Q2 — Script shape relative to the existing gate

**Branch:** Code structure / determinism

The roadmap names **two** deterministic scripts: a reworked `reviewability-gate.sh`
*and* a new `estimate-reviewable-loc.sh`.

- **Recommended answer (chosen):** **Separate standalone `estimate-reviewable-loc.sh`**
  that the plan phase calls directly; the gate keeps its `setup`/`tasks`/`diff` modes
  untouched. The production-LOC-per-file constant is **copied with a "keep in sync"
  comment** — the repo's established pattern (per PRSG-002 Q2, mirroring
  `extract_heading_section`).
  > Keeps the gate's contract stable, makes the new estimator independently
  > L4-testable, and matches the roadmap's two-script naming.

**Alternatives offered:**
- *Add a 4th `plan` mode to the gate*: fewer files (KISS), but grows the gate's
  surface and couples plan estimation to the gate's parse-declared-scope model;
  contradicts the two-script naming.
- *Standalone with a duplicated heuristic, no keep-in-sync link*: easiest isolation,
  but silent drift between two copies of the LOC constant.

**User's answer:** Separate script, shared LOC constant (Recommended).

---

### Q3 — Over-budget behavior in the autonomous run

**Branch:** Behavior / business rules; enforcement posture

US1 says "auto-approve under budget, surface only when over," but autopilot's plan
phase is autonomous — "surface" cannot mean a blocking mid-run human prompt.

- **Recommended answer (chosen):** **Record-and-proceed; block only interactively.**
  Under budget → silent pass (log line + workflow records "within budget"). Over
  budget in **autonomous** autopilot → record an over-budget note in
  `plan.md`/workflow and **continue** (advisory, non-blocking). **Interactive** use
  surfaces a decision.
  > Honors the roadmap's **non-negotiable sequencing principle**: blocking /
  > re-slicing is PRSG-010 ("harden the hatch LAST"). Making the gate block before the
  > automatic small path exists would reproduce the exact prior-art failure
  > (detective gate blocking finished work).

**Alternatives offered:**
- *Hard-block at plan phase (exit 1)*: stronger now, but re-introduces the deferred
  blocking failure; contradicts sequencing.
- *Warn-only, always non-blocking*: lightest, but drops the "surface to the human when
  over" intent for interactive runs.

**User's answer:** Record-and-proceed; block only interactively (Recommended).

---

### Q4 — The `~400 production-LOC` ceiling: where 400 sits, on what metric

**Branch:** Thresholds / metrics

Today `WARN_LOC=400` / `BLOCK_LOC=800` on **total** reviewable LOC
(`reviewability-gate.sh:19-24`). US2 redefines the ceiling to "~400 production-LOC
(code only, greenfield allowance)."

- **Recommended answer (offered):** *400 = block ceiling, ~250 = warn, production-LOC
  only* — read "ceiling" as the hard cap and tighten the block.
- **User's answer (chosen — course-corrected off the recommendation):**
  **400 = warn, ~800 = block, recounted as production-LOC only.**
  > Keep today's numbers (`400` warn / `800` block) for continuity; the change is the
  > **metric**, not the thresholds. LOC now counts **production code only**
  > (`is_production_file` & not `is_excluded_generated` — `src/ app/ lib/ scripts/`,
  > `*.ts/tsx/js/jsx/mjs/cjs`, `*.sql`); docs, tests, and config no longer inflate the
  > number. The tightening comes from narrowing what's counted, not from lowering the
  > bar — a less disruptive cutover than dropping the block to 400.

**Alternative not taken:**
- *Single 400 threshold (no warn/block tiers)*: simplest, but loses the graduated
  warn-then-block signal the gate and template both express.

**User's answer:** 400 = warn, ~800 = block, production-LOC only.

**Notes:** Implementation must change the LOC source in `diff` mode
(`reviewable_loc_from_numstat` currently sums *all* non-excluded additions) and in the
plan estimator so both count **production files only**, consistent with this decision.

---

### Q5 — Greenfield allowance

**Branch:** Thresholds / risk model

A net-new feature legitimately runs larger than an equal-risk modification, so US2
grants a "greenfield allowance."

- **Recommended answer (chosen):** **A 1.5× multiplier when the slice is all-new
  files** (adds only net-new files, modifies no existing files): warn `400→600`, block
  `800→1200`.
  > New isolated code is lower review-risk per line than churn in existing code.
  > Detect deterministically — `plan.md`'s NEW-file list at plan time, git `A`-status at
  > diff time. `1.5×` is a round, tunable factor.

**Alternatives offered:**
- *Flat +200 LOC bump*: simpler arithmetic, but scales poorly (too generous for tiny
  slices, too stingy for large greenfield modules).
- *Exempt pure additions entirely*: maximally permissive — a 2000-line new module would
  pass silently, defeating the small-PR goal.

**User's answer:** 1.5× multiplier when the slice is all-new files (Recommended).

---

### Q6 — Surface-count signal

**Branch:** Thresholds / metrics

Today `primary_surface_count > 1` fires **both** a warning (`:90-92`) and a blocker
(`:97`). US2 says "drop surface-count as a blocker."

- **Recommended answer (chosen):** **Downgrade to a warning.** Remove the blocker line
  (`:97`); keep the warning. The JSON still reports `primary_surface_count` and
  `primary_surfaces`.
  > Literal reading of "drop as a blocker." Preserves the diagnostic ("this slice spans
  > 2 surfaces") that PRSG-007's atomicity router will consume later, without ever
  > blocking.

**Alternatives offered:**
- *Remove entirely (stop computing)*: cleanest gate, but discards a signal PRSG-007
  needs — you'd re-add it.
- *Report-only (no warn, no block)*: quiet, but a multi-surface slice gives the
  reviewer no nudge.

**User's answer:** Downgrade to warning (Recommended).

---

### Q7 — Typed exception model

**Branch:** Exception mechanism / auditability

Today any of three phrases (`transition exception | split exception | ratified
exception`) grepped **anywhere** in the doc flips a `block` to `exception` (pass)
(`:160-162`, `:102`). US2 replaces this with typed classes.

- **Recommended answer (chosen):** **A structured pragma over a closed, fail-closed
  enum.** One explicit line — `Reviewability-Exception: <class>` — with
  `class ∈ {refactor, infra, upgrade}`. The script matches the **exact pragma** and
  validates enum membership; an **unknown or missing class is not honored** (stays
  `block`). All three classes flip a block **equally** in v1.
  > Replaces the loose anywhere-in-prose substring match (easy to trip incidentally)
  > with a named, auditable, hard-to-fake declaration. Differential per-class
  > allowances are YAGNI (Principle VI) — the classes exist for auditability (*why* the
  > exception is justified: a mechanical refactor / infra-config / dependency-upgrade),
  > not for different budgets.

**Alternatives offered:**
- *Three new keyword phrases, still substring-matched*: minimal plumbing, but keeps the
  loose anywhere-in-doc match.
- *Pragma with a free-form (open-set) reason*: flexible, but an open set reintroduces
  the rubber-stamp the roadmap is trying to kill.

**User's answer:** Structured pragma, closed enum, fail-closed (Recommended).

---

### Q8 — Roadmap-template scope, and the PRSG-006 ↔ PRSG-010 boundary

**Branch:** Dependencies / cross-spec consistency

Both PRSG-006 and PRSG-010 list the roadmap template. The gate's `setup` mode
**parses the template's declared scope** (`parse_declared_scope`, `:141-165`) — so a
gate change not mirrored in the template silently breaks parsing.

- **Recommended answer (chosen):** **Update the template's Reviewability Contract to
  match the reworked gate** — production-LOC thresholds, surface-count as a *warning*
  (not a block), and the typed `Reviewability-Exception: <class>` pragma replacing
  `split exception`.
  > **Required for correctness**, not a preference: `setup`-mode parsing reads the
  > template, so a gate-only change would leave the template advertising the old
  > thresholds and a keyword the gate no longer honors. PRSG-010's later *removal* of
  > the exception boilerplate (once the automatic small path exists) is a separate
  > hardening step; 006 modernizes, 010 removes — they compose.

**Alternatives offered:**
- *Leave the template alone; change only the gate*: smaller diff, but gate/template
  drift and declared exceptions silently break.
- *Update thresholds/surface wording only, leave the keyword*: partial — the gate's new
  typed-pragma parser still won't match the template's old keyword.

**User's answer:** Update the template's contract to match the reworked gate
(Recommended).

**Notes:** Concrete template edits target the `## Reviewability Contract` block
(`technical-roadmap-template.md:40-50`) and the per-spec `Budget result: … / split
exception` lines (`:104, :146, :173, …`).

---

### Q9 — Backward-compat of the old exception keywords

**Branch:** Rollout / migration

With a fail-closed typed pragma, existing roadmaps using the old
`split/transition/ratified exception` phrases would no longer flip a block.

- **Recommended answer (chosen):** **New-specs-only, no alias — document the break.**
  The gate honors **only** the typed pragma; old keywords stop working. The break is
  recorded in the spec so PRSG-011 picks it up.
  > Matches the roadmap's explicit stance ("PRSG-001–010 ship new-specs-only; PRSG-011
  > adds state-keyed retro-migration"). De-boilerplating the **live project** roadmap
  > is **PRSG-011's Tier-1** job, not here. Keeps PRSG-006 tight and the exception
  > model clean.

**Alternatives offered:**
- *Honor old keywords as deprecated aliases (transition window)*: safer for in-flight
  roadmaps, but carries the loose substring match forward, partly defeating
  auditability until PRSG-011 removes it.
- *Hard cutover + migrate this repo's roadmaps now*: cleanest end-state, but pulls
  PRSG-011's migration work forward and expands the diff into legacy-data territory.

**User's answer:** New-specs-only, no alias — document the break (Recommended).

---

### Q10 — Codex parity surface (L8)

**Branch:** Cross-cutting / Codex parity

`speckit-pro/codex-skills/speckit-autopilot/` exists and references reviewability in
`SKILL.md`, `references/phase-execution-codex.md`, and
`references/post-implementation-codex.md`. The scripts and the roadmap template live
**only** under `skills/` (single-copy, runtime-agnostic).

- **Recommended answer (chosen):** **Mirror the autopilot plan-phase change only;
  scripts + template stay single-copy.** Mirror the plan-phase budget instruction into
  `codex-skills/speckit-autopilot` (`SKILL.md` + `phase-execution-codex.md`).
  `reviewability-gate.sh`, `estimate-reviewable-loc.sh`, and the roadmap template are
  runtime-agnostic — one copy, no mirror.
  > `validate-codex-skills.sh` (L1) + the L8 parity fixtures cover the autopilot change.
  > Matches PRSG-002's recorded default and the repo's shared-scripts/templates pattern.

**Alternatives offered:**
- *Treat the whole change as runtime-agnostic; skip the mirror*: fails
  `validate-codex-skills` (L1) and L8 parity around the plan-phase wording.
- *Mirror everything, duplicating the scripts into codex-skills*: creates exactly the
  drift the single-copy pattern avoids.

**User's answer:** Mirror the autopilot plan-phase change only; scripts + template stay
single-copy (Recommended).

## Recorded defaults (agreed implicitly, carried into the spec)

- **Test coverage = L1, L3, L4, L8** (authoritative per the roadmap coverage table —
  **no L7**; PRSG-006 adds no new agent). L4: extend the existing
  `tests/layer4-scripts/test-reviewability-gate.sh` for the reworked thresholds/metric/
  surface/exception behavior, and add a determinism fixture for
  `estimate-reviewable-loc.sh` (same inputs → byte-identical output). L3: a functional
  eval that the plan phase auto-approves under budget and surfaces/records when over.
  L1: structural assertions (script exists; template thresholds/pragma vocabulary match
  the gate) + `validate-codex-skills`. L8: autopilot Path-A/Path-B parity.
- **Greenfield detection is deterministic** — `plan.md` NEW-file enumeration at plan
  time; git `A`-status at diff time. No LLM judgment.
- **`set -euo pipefail` + `bash`+`jq` only** for the new script (Principle II; CLAUDE.md
  rule 2 — no new dependency).

## Open Questions

None block implementation. Deferred (by design, not undecided):

- **Exact per-file LOC heuristic for `plan.md` parsing** — the precise mapping from a
  planned-file entry to projected production-LOC (flat `×40`, or weighted by file type)
  is an implementation tuning detail for the Plan/Implement phases; the determinism
  contract (same `plan.md` → same number) is the fixed requirement.
- **The literal warn/block constants for greenfield** beyond the `1.5×` rule (whether
  `1.5×` is hardcoded or a single named variable) — a code-style detail, resolved at
  implementation.
- **Whether PRSG-011 should also strip this repo's own roadmap exception lines** —
  flagged here as the downstream consequence of Q9's new-specs-only break; tracked for
  PRSG-011, out of scope for PRSG-006.

## Recommended Next Step

Continue the scaffold: populate `PRSG-006-workflow.md` from this Q&A log, commit both
artifacts, mark PRSG-006 In Progress in the roadmap, then run:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/PRSG-006-workflow.md
```

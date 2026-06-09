---
topic: "Atomicity-test router (read-only classifier)"
slug: "prsg-007-atomicity-router"
date: "2026-06-08"
mode: "setup"
spec_id: "PRSG-007"
source_input:
  type: "topic"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-007 scope)"
question_count: 14
stop_reason: "natural"
---

# Design Concept: Atomicity-test router (read-only classifier)

> **Source:** PR-Size Governance technical roadmap — PRSG-007 scope (Phase 4 · P1 · engine MVP)
> **Date:** 2026-06-08
> **Questions asked:** 14
> **Stop reason:** natural (all critical branches walked; no new critical branches surfaced)

## Goals

- Ship a **read-only, generic** atomicity classifier — `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` — that emits a **single JSON object to stdout** (route + detected signals + `releasable` flag + `warnings[]`) and writes nothing to disk (Q1).
- Classify a change into one route from the enum `{split-PR, one-navigable-PR, branch-by-abstraction, single-atomic-PR, out-of-scope}`. Precedence ladder (Q6):
  1. hard-atomic signal fires → `single-atomic-PR`
  2. proven-safe additive change with structural split **seams** → `split-PR`
  3. otherwise (probes inconclusive) → `one-navigable-PR` (the safe abstain default — **never** auto-split on uncertainty)
  4. not applicable (e.g. no `tasks.md`) → `out-of-scope`
- Decide splittability from **structural seams** (multiple independent additive capabilities/surfaces in `tasks.md`), **not** from LOC (Q10). The `speckit-autopilot` skill combines `router.route` (seams) with `reviewability-gate.sh` (size) to decide whether a split is actually worth doing — single responsibility per script.
- Implement the **safety-floor probes** to full depth: hard-atomic overrides (US2) + `tasks.md`-shape + additive-vs-modify grep (`UPDATE/DELETE/DROP/CHECK` vs `CREATE TABLE`/nullable adds) (Q5). These are deterministic and are what makes splitting *safe*.
- Emit the **contextual probes** — flag-system, release cadence, consumer locality — as **advisory hints only** (detected, non-decisive), with TODOs pointing to their full-depth home in a later spec (Q5). Keeps the script within the ~400 LOC budget (YAGNI / KISS, constitution VI).
- Emit a **releasability** signal: `releasable: true|false` plus a human-readable `warnings[]` entry naming the class (e.g. "destructive migration: CI-green does not imply safe to release") when destructive-migration / concurrency signatures are detected (Q7, US2).
- **Advisory-only, never a gate**: always `exit 0` on a successful classification; reserve `exit 2` for usage / unreadable-input errors. The autopilot reads JSON, not exit codes (Q3) — mirrors the slice-sizing branch's non-blocking precedent.
- **Runs after the Tasks phase (gate G5)** (Q8): `tasks.md` is the primary signal and only exists post-Tasks. The `speckit-autopilot` skill runs the script, parses the JSON, and records it into a new **`## Atomicity Route`** section in the workflow file.
- Add the `## Atomicity Route` section (route, releasable, signals, warnings) to the workflow template `speckit-pro/skills/speckit-coach/templates/workflow-template.md` so PRSG-008/009 can read it back deterministically (Q11).
- **Independent** of `reviewability-gate.sh` — no internal call; the two are complementary (splittability vs sizing) and the autopilot combines their outputs (Q9).
- Provide generic path/surface classification by **duplicating a small matcher** (the few `surface_for_path` / `is_production_file` cases the router needs), **not** by extracting a shared lib — avoids touching the shipped, well-tested gate (Q12, constitution VI "three similar lines beat a premature abstraction").
- Document the post-Tasks router step in **both** the Claude `speckit-autopilot/SKILL.md` (+ the relevant `references/` doc — gate-validation or phase-execution) **and** the Codex mirror `codex-skills/speckit-autopilot/SKILL.md`, keeping `validate-codex-skills.sh` (L1) green. The script is shared (single `scripts/` dir); only the prose is mirrored (Q13).
- **Tests:** a Layer-4 unit test `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh` with **one fixture per change class**, plus Layer-1 structural validation.
- Keep PRSG-007 as **one spec** (Q14): the estimator's `warn` (≈515 LOC, suggested 2 slices) is inflated by prose/doc files — 4 of 6 counted files are markdown (SKILL / Codex mirror / template / references); only `atomicity-route.sh` is production code. Recorded as an advisory note; the diff-mode reviewability gate enforces real size at PR time.

## Non-goals

- **No PR emission, branch creation, or multi-PR rewrite.** This spec only classifies and records a route; emission is PRSG-008 (layer-planner) + PRSG-009 (multi-PR emission) — answered in Q1 (output shape) and Q8 (lifecycle).
- **No blocking / gating behavior** — the router never fails the workflow (Q3).
- **No sizing / LOC computation in the router** — splittability is seam-based; the size axis is `reviewability-gate.sh`'s job, combined by the autopilot (Q9, Q10).
- **No deep implementation of the flag-system / release-cadence / consumer-locality probes** in this spec — advisory hints only; full depth deferred to a later spec (Q5; see Open Question 1).
- **No internal call into `reviewability-gate.sh`** and **no edits to it** (Q9, Q12).
- **No shared-lib extraction** for the path/surface matcher (Q12).
- **Not run at scaffold time or Plan time** — the strongest probe (`tasks.md` shape) is unavailable then (Q8).
- **Route not stored in `SPEC-MOC.md`** — the MOC is for navigation / version-gating, not per-run routing (Q11).

## Design Tree (Q&A log)

### Q1. How should the new atomicity-route.sh return its routing decision?

**Branch:** Output contract

**Recommended answer:** Read-only JSON to stdout
> Mirror `reviewability-gate.sh` exactly: pure read-only, emit one JSON object (route + detected signals + `releasable` + warnings), write nothing. Keeps it L4-testable and honors "read-only classifier."

**Alternatives offered:**
- Write route into the workflow file: fewer moving parts but breaks read-only and is harder to unit-test.
- Exit-code / plain-text route: simplest, but loses the signal detail PRSG-008 needs.

**User's answer:** Read-only JSON to stdout (Recommended)

---

### Q2. Given the script is read-only, who writes the emitted route into the workflow file?

**Branch:** Output contract — ownership

**Recommended answer:** `speckit-autopilot` skill
> The skill runs the script, parses JSON, and records the route into a workflow-file section — same pattern it already uses for `reviewability-gate.sh` / `estimate-*.sh`. Script stays pure.

**Alternatives offered:**
- scaffold-spec at scaffold time: premature — `tasks.md` doesn't exist yet.
- Nobody (JSON only): roadmap explicitly wants the decision recorded in the workflow file.

**User's answer:** `speckit-autopilot` skill (Recommended)

---

### Q3. Should the atomicity router ever block the workflow, or is it purely advisory?

**Branch:** Block policy / exit-code contract

**Recommended answer:** Advisory-only, always exit 0
> Classification always succeeds with exit 0; reserve exit 2 for usage / unreadable-input only. Never a gate. Matches the slice-sizing branch's "never blocks, never reads exit code as a gate" precedent.

**Alternatives offered:**
- Block on hard-atomic-but-oversized: turns it into a gate, couples to sizing, contradicts read-only-advisory intent.
- Exit code encodes the route: conflicts with JSON-as-truth and overloads exit codes.

**User's answer:** Advisory-only, always exit 0 (Recommended)

---

### Q4. Should the router be generic or tuned to this plugin repo's bash/markdown shape?

**Branch:** Applicability

**Recommended answer:** Generic, like `reviewability-gate.sh`
> Reuse the same language-agnostic surface taxonomy (TS/SQL/UI/migrations/config/docs). The script ships in the plugin and runs on consumers' projects, so it must classify any stack.

**Alternatives offered:**
- Tune to this repo (bash/markdown/jq): simpler here, but breaks on a TypeScript/Python consumer — defeats the plugin's purpose.

**User's answer:** Generic, like `reviewability-gate.sh` (Recommended)

---

### Q5. Which detection probes are in scope for the read-only MVP?

**Branch:** Probe depth (the load-bearing scope cut)

**Recommended answer:** Safety floor + advisory hints
> Fully implement the deterministic safety-critical probes (hard-atomic overrides + `tasks.md`-shape + additive-vs-modify grep). Emit flag-system / release-cadence / consumer-locality as best-effort hints only (non-decisive), with TODOs to deepen later. Keeps ~400 LOC, YAGNI-consistent. (The estimator sizes by file count, not heuristic depth — depth is the real blow-up risk, so the cut comes from here.)

**Alternatives offered:**
- Full depth on all 5 probes now: most complete, but well over 400 LOC — the spec would violate its own budget.
- Minimal (drop the three contextual probes entirely): smallest, but loses signals the layer-planner wants and would change the JSON shape again in PRSG-008.

**User's answer:** Safety floor + advisory hints (Recommended) — **with the explicit requirement that the spec roadmap leaves NO gaps** (the deferred probe depth must be assigned to a later spec; see Open Question 1).

**Notes:** User: "1, but we must make sure our spec roadmap leaves NO gaps."

---

### Q6. When probes can't prove a split is safe (and no hard-atomic signal fires), what's the default route?

**Branch:** Default / abstain route (safety crux)

**Recommended answer:** `one-navigable-PR`
> Ship as a single, review-structured PR — never auto-split on uncertainty. Precedence: hard-atomic→`single-atomic-PR`; proven-safe-additive-with-seams→`split-PR`; else→`one-navigable-PR`; non-applicable→`out-of-scope`. Dogfoods correctly: PRSG-007 itself (additive, 1 surface) never routes to `split-PR`.

**Alternatives offered:**
- `single-atomic-PR`: conflates "couldn't prove a split" with "genuinely indivisible."
- `split-PR` (optimistic): exactly the unsafe-split behavior this spec exists to prevent.

**User's answer:** `one-navigable-PR` (Recommended)

---

### Q7. How should the "CI-green ≠ releasable" warning surface?

**Branch:** Releasability (US2)

**Recommended answer:** Boolean + warning string in JSON
> Emit `releasable: true|false` plus a `warnings[]` entry naming the class. Machine-checkable by the autopilot, readable in the workflow file. Mirrors `reviewability-gate.sh`'s `warnings[]` shape.

**Alternatives offered:**
- Fold into route + a note: the releasability concern becomes invisible to automation.
- Separate releasability sub-object: over-engineered for a read-only MVP (YAGNI).

**User's answer:** Boolean + warning string in JSON (Recommended)

---

### Q8. At what point in the autopilot lifecycle should the router run?

**Branch:** Lifecycle hook point

**Recommended answer:** After Tasks phase / G5
> `tasks.md` is the primary signal and only exists post-Tasks. Running here records the route before implementation, matching `reviewability-gate.sh` `tasks` mode which also keys off the feature dir at G5.

**Alternatives offered:**
- After Plan / G3: `tasks.md` doesn't exist yet — the strongest probe is unavailable.
- Post-implementation (pre-PR): that's PRSG-009's job; duplicates it and misses "route recorded before emission."

**User's answer:** After Tasks phase / G5 (Recommended)

---

### Q9. Should atomicity-route.sh call reviewability-gate.sh internally, or stay independent?

**Branch:** Gate coupling

**Recommended answer:** Independent
> No internal call. The two are complementary (sizing vs splittability); the autopilot runs both and combines outputs. "Deps: PRSG-006 (benefits)" — benefits, not depends. Avoids coupling fragility; each script stays unit-testable in isolation.

**Alternatives offered:**
- Call the gate for sizing context: couples the scripts and complicates L4 mocking.

**User's answer:** Independent (Recommended)

---

### Q10. What distinguishes split-PR from one-navigable-PR — seams or size?

**Branch:** Split trigger (resolves the Q6/Q9 tension)

**Recommended answer:** Seams, not size
> The router decides splittability from structural seams (multiple independent additive capabilities/surfaces in `tasks.md`), NOT LOC. The autopilot then combines `router.route` (seams) with `reviewability-gate.sh` (size) to decide whether a split is worth doing. Keeps the router independent (Q9) and single-responsibility.

**Alternatives offered:**
- Router also factors size: reintroduces sizing into a script just made independent of the gate; duplicates LOC logic.

**User's answer:** Seams, not size (Recommended)

---

### Q11. How should the route be recorded in the workflow file?

**Branch:** Workflow-file artifact

**Recommended answer:** New `## Atomicity Route` template section
> Add a structured section to `workflow-template.md` (route, releasable, signals, warnings). Predictable for PRSG-008/009 to read back; consistent with how phases are already templated. Real, in-scope artifact work.

**Alternatives offered:**
- Autopilot inserts free-form text: unstructured — the layer-planner would parse prose.
- Record in `SPEC-MOC.md`: wrong home — MOC is for navigation/version-gating.

**User's answer:** New `## Atomicity Route` template section (Recommended)

---

### Q12. Duplicate a small path/surface matcher, or extract a shared lib?

**Branch:** Code sharing

**Recommended answer:** Duplicate a small matcher
> Copy the few `surface_for_path` / `is_production_file` cases the router needs. Constitution VI YAGNI: "three similar lines beat a premature abstraction"; only two call sites exist. Lower blast radius — no refactor of the shipped, well-tested gate.

**Alternatives offered:**
- Extract a shared `scripts/lib/` helper: DRY, but touches the shipped `reviewability-gate.sh` (regression risk); must live in `scripts/lib/` (NOT `tests/`) since a shipped script uses it. Bigger diff than the MVP warrants.

**User's answer:** Duplicate a small matcher (Recommended)

---

### Q13. Should documenting the route step include updating the Codex mirror?

**Branch:** Codex-mirror scope

**Recommended answer:** Yes — update both, keep parity green
> Document the post-Tasks router step in the Claude `SKILL.md` + the relevant `references/` doc AND mirror it into `codex-skills/speckit-autopilot/SKILL.md` so `validate-codex-skills.sh` (L1) stays green. The script is shared (single `scripts/` dir); only the prose is mirrored.

**Alternatives offered:**
- Claude-only this spec, mirror later: risks L1 parity failure, or the Codex autopilot silently never runs the router.

**User's answer:** Yes — update both, keep parity green (Recommended)

---

### Q14. Estimator flagged warn (~515 LOC, suggests 2 slices). Split, or keep as one spec?

**Branch:** Slice-sizing (advisory)

**Recommended answer:** Keep as one spec
> The 515 estimate is inflated — 4 of 6 files are markdown prose (SKILL/Codex/template/refs); only `atomicity-route.sh` is production code, and Q5 already trimmed probe depth. Splitting US2 (hard-atomic safety) into a later slice would delay the safety floor for no gain, since nothing emits PRs until PRSG-009. Record the warn as an advisory note; the diff-mode gate enforces real size at PR time.

**Alternatives offered:**
- Split into 2 vertical slices (US1 classifier core → US2 hard-atomic + releasability): each end-to-end and testable, but adds a second autopilot run + roadmap entry.
- Defer — decide at Plan phase: revisit during `/speckit-plan` when real counts firm up.

**User's answer:** Keep as one spec (Recommended)

**Notes:** Advisory `warn` (estimated_loc 515, suggested_slices 2) recorded; split declined.

## Open Questions

- **What:** Roadmap gap-closure for the deferred contextual probes. PRSG-007 ships flag-system / release-cadence / consumer-locality as advisory-hint stubs (Q5). The full-depth implementation of each must have an explicit owner in the roadmap so the stubs are not orphaned.
  **Why deferred:** User explicitly required (Q5 note) that the roadmap "leaves NO gaps"; assigning probe depth to a downstream spec is roadmap-authoring work, not grill-me's job.
  **Resolution (2026-06-08):** CLOSED at scaffold time. PRSG-010 ("Harden the hatch") gained a **US3 — Deepen the contextual atomicity probes** entry that explicitly owns promoting the flag-system / release-cadence / consumer-locality stubs to full-depth routing signals in `atomicity-route.sh`. The roadmap no longer has an orphaned stub; the Q5 "no gaps" requirement is satisfied.

- **What:** `branch-by-abstraction` emission criteria. The route is in the enum but its exact MVP trigger (modify-heavy change with an identifiable abstraction seam vs. fall-through to `one-navigable-PR`) is unspecified.
  **Why deferred:** An implementation-precision detail better resolved with the spec/plan in hand.
  **Suggested next step:** Resolve during `/speckit-clarify` (autopilot Clarify phase).

- **What:** Exact JSON schema — field names for `signals[]`, `hints[]`, `route`, `releasable`, `warnings[]`.
  **Why deferred:** Should be pinned where PRSG-008 will consume it.
  **Suggested next step:** Finalize in `/speckit-plan`, aligning field shapes with `reviewability-gate.sh` for consistency.

### Derived decisions (not asked; recorded for downstream)

- **CLI signature:** `atomicity-route.sh <feature-dir>` — a single positional arg (the feature dir containing `tasks.md` / `plan.md` / `spec.md`), JSON to stdout. Mirrors the `reviewability-gate.sh` interface family (Q1, Q4).
- **Edge cases:** missing / empty `tasks.md` → route `out-of-scope` (exit 0); unreadable or nonexistent feature dir / usage error → `exit 2` with `{"error": ...}` (Q3, Q6).

## Recommended Next Step

Setup has already run (this doc lives in the worktree alongside the workflow file). Informational next steps:

1. **Close Open Question 1 first** — run `/speckit-pro:speckit-coach` to confirm the roadmap assigns the deferred probe depth to PRSG-008/010 (the user's "no gaps" requirement).
2. **Then execute** — `/speckit-pro:speckit-autopilot docs/ai/specs/.process/PRSG-007-workflow.md`.

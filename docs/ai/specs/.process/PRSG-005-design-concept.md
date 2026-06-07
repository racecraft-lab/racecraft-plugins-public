---
topic: "Vertical-slice sizing heuristics in PRD/grill-me"
slug: "prsg-005-slice-sizing-heuristics"
date: "2026-06-06"
mode: "setup"
spec_id: "PRSG-005"
source_input:
  type: "topic"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-005 catalog entry + cross-cutting mandates)"
question_count: 10
stop_reason: "natural"
---

# Design Concept: Vertical-slice sizing heuristics in PRD/grill-me

> **Source:** PRSG-005 entry in `docs/ai/specs/pr-size-governance-technical-roadmap.md` (Phase 3, P1, Deps: none)
> **Date:** 2026-06-06
> **Questions asked:** 10
> **Stop reason:** natural (converged before any cap; user chose "Wrap up — synthesize now")

## Goals

- **Make specs "born PR-sized" at the cheapest moment** — bake SPIDR + INVEST +
  vertical-slicing guidance into the scoping/PRD interview so the SPEC catalog is
  composed of thin, end-to-end (vertical) slices *by construction*, instead of
  splitting fat specs late.
- **Divide the slicing job cleanly between the two skills:** `speckit-prd` owns
  **catalog-level decomposition** (SPIDR story-splitting + vertical slicing → emit
  thin SPECs); `grill-me` owns **per-spec validation** (INVEST check on the single
  spec it is grilling; recommend a split when that spec is fat or horizontally
  sliced). No duplicated guidance prose between them.
- **Ship a deterministic sizing estimator** (`estimate-spec-size.sh`, scripts-first):
  it takes structured size signals as inputs and returns
  `{estimated_loc, suggested_slices, status: ok|warn}` against the shared ~400-LOC
  ceiling. The script does the math/threshold; the LLM gathers inputs and interprets.
- **Keep PRSG-005 purely preventive/advisory** — it shapes the catalog and surfaces
  size estimates, but **never blocks**. The plan-phase budget gate, thresholds, and
  exit-code logic are PRSG-006's job.
- **Single source of truth for the heuristics** — canonical SPIDR/INVEST/vertical-
  slicing guidance lives in one shared reference doc; both skills carry a short
  inline summary + a link, with full Codex parity.
- **Prove the behavior, not just the script** — an L3 functional eval shows a prd
  interview turning a would-be-fat idea into a thin sliced catalog, and a grill-me
  interview triggering the split branch on a fat single spec.

## Non-goals

- **No plan-phase gate, threshold rework, or exit-code/blocking logic** — that is
  PRSG-006. PRSG-005 is advisory-only (answered Q3, "005 advisory-only; 006 gates").
- **No machine-readable size budget written *for* a downstream gate to consume** —
  005 and 006 share only the ~400-LOC ceiling as a documented constant; 005 does not
  emit a budget artifact that 006 reads (answered Q3, alternative rejected).
- **No roadmap-template schema change** — reuse the existing per-SPEC `Budget: ~N LOC`
  catalog line; do not add a new slice/size field to `technical-roadmap-template.md`
  (answered Q9, "Reuse existing Budget line").
- **No formal structured catalog fields** (`size_estimate`, `invest_check`,
  `slice_of`) — keep the catalog shape; the annotation is advisory text on the
  existing entry (answered Q4, alternative rejected).
- **No atomicity routing (PRSG-007), layer-planner (PRSG-008), or multi-PR emission
  (PRSG-009)** — those are the Phase-4 engine; PRSG-005 only right-sizes upstream.
- **No broad description rewrite of either skill** — only a light trigger touch
  (answered Q7, "Light trigger touch + regression guard").
- **No second copy of the estimator** — one shared runtime-agnostic script, not
  per-skill copies (answered Q8, alternative rejected).

## Design Tree (Q&A log)

### Q1. How should the slicing responsibility split between `speckit-prd` and `grill-me` (to avoid duplicated guidance)?

**Branch:** Division of responsibility / architecture

**Recommended answer:** "prd decomposes, grill-me validates"
> `speckit-prd` is the front door that decomposes an idea into the SPEC catalog with
> a 1:1 feature↔SPEC contract, so catalog-level decomposition (SPIDR story-splitting +
> vertical slicing) belongs there. `grill-me` scopes one spec at a time, so per-spec
> INVEST validation + a split recommendation belongs there. Distinct jobs → no
> duplicated prose. Both call the shared estimator.

**Alternatives offered:**
- Both carry full SPIDR+INVEST: each self-contained but duplicates guidance across two SKILL.md files + two Codex mirrors; drift risk.
- Concentrate all slicing in prd: simplest, but a spec scaffolded straight from a roadmap entry never gets a grill-time size check.

**User's answer:** "prd decomposes, grill-me validates"

---

### Q2. What should `estimate-spec-size.sh` compute and return?

**Branch:** Deterministic estimator contract (scripts-first)

**Recommended answer:** "Inputs → LOC + slice count + warn"
> Takes structured size signals the skill collected (e.g. # user stories, # files/
> surfaces touched, # FRs, new-vs-modify flag) as args/JSON; returns JSON
> `{estimated_loc, suggested_slices, status: ok|warn}` against the ~400-LOC budget.
> Pure bash+jq, byte-identical (L4). The LLM gathers inputs + interprets; the script
> does the deterministic math/threshold — the scripts-first payoff.

**Alternatives offered:**
- LOC number only: thinnest script, but pushes threshold judgment back into the LLM (weaker scripts-first payoff).
- Parse roadmap entry directly: self-contained but couples the script to roadmap markdown format (brittle parsing).

**User's answer:** "Inputs → LOC + slice count + warn"

---

### Q3. Where is the line between PRSG-005 sizing and PRSG-006's plan-phase budget gate?

**Branch:** Scope boundary vs PRSG-006

**Recommended answer:** "005 advisory-only; 006 gates"
> PRSG-005 is purely preventive/advisory at PRD/scoping time: it shapes the catalog
> and surfaces a per-SPEC size estimate, never blocks. PRSG-006 owns the plan-phase
> measurement (`estimate-reviewable-loc.sh`), the gate, and auto-approve/threshold
> logic. They share ONLY the ~400-LOC ceiling as a documented constant;
> `estimate-spec-size.sh` is a forward guess, `estimate-reviewable-loc.sh` is the
> authoritative count. No gate/exit-code logic in 005.

**Alternatives offered:**
- 005 writes a budget 006 consumes: tighter integration but couples the specs; risks 005 shipping half a gate before 006 exists.
- Fully independent, no shared constant: maximally decoupled but two LOC ceilings could drift and confuse users.

**User's answer:** "005 advisory-only; 006 gates"

---

### Q4. What does "SPEC catalog emitted as thin slices by construction" concretely change in `speckit-prd`'s output?

**Branch:** Catalog output format

**Recommended answer:** "Light per-SPEC annotation + guidance"
> Keep the existing catalog shape; add a lightweight per-SPEC line carrying the
> `estimate-spec-size.sh` result (estimated LOC + suggested slices) and a one-line
> vertical-slice/INVEST rationale. The deeper change is interview guidance that drives
> prd to emit thin vertical SPECs. Advisory text, not a rigid schema — fits KISS/YAGNI
> and the roadmap template's existing Budget lines.

**Alternatives offered:**
- Formal structured fields: most queryable, but a heavier schema change downstream tools must parse; scope-creep risk.
- Prose guidance only: simplest diff, but no visible size signal in the emitted roadmap and nothing for grill-me to validate against.

**User's answer:** "Light per-SPEC annotation + guidance"

---

### Q5. When `grill-me` scopes a single spec that comes out fat or horizontally-sliced, what should it do?

**Branch:** grill-me behavior / human-in-the-loop split

**Recommended answer:** "Active split branch"
> grill-me gets a dedicated 'slice-sizing' design-tree branch: it runs
> `estimate-spec-size.sh` on the spec's signals, and if over budget or horizontal,
> asks a split question via `AskUserQuestion` recommending N thin vertical slices. The
> chosen split lands in the design concept (Goals/Open Questions) so scaffold-spec/
> autopilot can act on it. Leverages grill-me's human-in-the-loop strength.

**Alternatives offered:**
- Note, don't split: lighter, but leaves right-sizing for later phases instead of the cheapest moment.
- Splitting is prd-only: cleanest separation, but a spec scaffolded straight from a roadmap entry never gets a grill-time check.

**User's answer:** "Active split branch"

---

### Q6. Where should the canonical SPIDR + INVEST + vertical-slicing prose live?

**Branch:** Heuristic-doc location / DRY

**Recommended answer:** "One shared reference doc + short inline"
> Canonical guidance in a single reference doc (e.g.
> `speckit-coach/references/slicing-heuristics.md`); `speckit-prd` and `grill-me` each
> carry a short inline summary + a link. DRY, single source of truth, keeps both
> SKILL.md files lean (prd is already 246 lines). Mirror the doc reference in both
> Codex variants. Matches PRSG-002's shared-helper pattern.

**Alternatives offered:**
- Inline in each SKILL.md: each skill self-contained, but ~4 copies to keep in sync; drift risk + bigger diffs.
- Minimal mnemonic only: smallest footprint, but thin guidance may not reliably change LLM slicing behavior (weaker L3 outcome).

**User's answer:** "One shared reference doc + short inline"

---

### Q7. Do the skill descriptions/trigger phrases change, or only the bodies/behavior?

**Branch:** Trigger surface / L2 eval scope

**Recommended answer:** "Light trigger touch + regression guard"
> Add a few sizing/slicing trigger phrases (grill-me: "split this spec", "is this spec
> too big", "right-size this spec"; prd: "right-size the catalog") while keeping all
> existing triggers intact. L2 confirms the new phrases route correctly AND no over/
> under-trigger regression on current phrases. This is why L2 is in the coverage table.

**Alternatives offered:**
- No description change: smaller surface, but users can't discover the new right-sizing behavior via natural language.
- Broader description rewrite: maximizes discoverability but high over-trigger risk and a bigger L2 surface; likely beyond ~200 LOC budget.

**User's answer:** "Light trigger touch + regression guard"

---

### Q8. Where should the shared `estimate-spec-size.sh` live and how is it invoked (runtime-agnostic for Codex parity)?

**Branch:** Shared-script home / Codex parity

**Recommended answer:** "Shared plugin script, ${CLAUDE_PLUGIN_ROOT}"
> One runtime-agnostic bash+jq script in a shared plugin scripts location (e.g.
> `speckit-pro/skills/speckit-coach/scripts/` alongside the shared
> `slicing-heuristics.md`, or a shared `scripts/` dir); both CC and Codex skill
> variants invoke it via `${CLAUDE_PLUGIN_ROOT}`. Single copy, one L4 fixture. Mirrors
> PRSG-002's single shared normalizer.

**Alternatives offered:**
- Live in speckit-prd, grill-me references it: co-located with primary caller, but makes grill-me depend on prd's directory layout.
- Two copies, one per skill: self-contained, but violates DRY and doubles the L4/parity surface.

**User's answer:** "Shared plugin script, ${CLAUDE_PLUGIN_ROOT}"

---

### Q9. Does PRSG-005 edit `technical-roadmap-template.md`, or stay confined to the two skills + shared doc + script?

**Branch:** Template scope / surface count

**Recommended answer:** "Reuse existing Budget line"
> Don't change the roadmap template schema. The catalog already carries a
> `Budget: ~N LOC` line per SPEC; prd just populates it from `estimate-spec-size.sh`
> and adds the one-line slice rationale in the existing entry prose. Smallest surface,
> no template churn, keeps the diff inside the ~200-LOC budget and confined to
> prd/grill-me + shared doc + script.

**Alternatives offered:**
- Add a slice annotation slot to the template: more consistent output, but adds a 4th file surface and risks overlapping PRSG-004/006's template work.
- Decide during Plan: keeps options open, but leaves an unresolved decision the autopilot must make autonomously.

**User's answer:** "Reuse existing Budget line"

---

### Q10. What's the acceptance bar (L3 functional eval) that defines PRSG-005 as done?

**Branch:** Definition of done / verification

**Recommended answer:** "Fixture idea → thin sliced catalog"
> L3: run a prd interview on a fixture idea (one that would naively be one fat spec)
> and assert the emitted catalog is multiple thin vertical slices, each with a
> populated Budget from `estimate-spec-size.sh` and an INVEST/vertical rationale; plus
> a grill-me L3 where a fat single spec triggers the split branch. L4:
> `estimate-spec-size.sh` byte-identical on fixtures. L2: new trigger phrases route, no
> regression. L8: Codex parity green. L1: structural.

**Alternatives offered:**
- Script + structural only: cheaper/faster, but the roadmap explicitly lists L3 and prose-only changes are exactly what L3 guards.
- Add a quantified size-reduction target: strongest signal, but pins a number that may be arbitrary for one fixture and risks flaky eval thresholds.

**User's answer:** "Fixture idea → thin sliced catalog"

---

### Wrap-up checkpoint

**Branch:** Stop condition

**User's answer:** "Wrap up — synthesize now" — the high-uncertainty design tree was
resolved and internally consistent; remaining minor items recorded as Open Questions
below.

## Open Questions

- **What:** SPIDR "Spike" handling in the estimator and INVEST check — a research-only
  slice has near-zero production LOC, so `estimated_loc ≈ 0` could read as "trivially
  fine" when the real risk is uncertainty, not size.
  **Why deferred:** edge case; user chose to wrap up rather than spend questions on it.
  **Suggested next step:** resolve in autopilot `/speckit-clarify` (Session: estimator
  semantics) — decide whether a spike is flagged as a distinct slice *type* exempt from
  the LOC threshold rather than sized by LOC.

- **What:** Forward-estimate approximation — `estimate-spec-size.sh` runs *before*
  implementation, so its inputs (# files/surfaces, new-vs-modify) are the LLM's
  pre-implementation guess; the estimate is inherently approximate.
  **Why deferred:** acceptable by design (it's advisory, not a gate — see Q3), but the
  approximation bound should be stated so users don't over-trust the number.
  **Suggested next step:** document the "forward estimate ≠ authoritative count"
  caveat in the shared `slicing-heuristics.md`; the authoritative count is PRSG-006's
  `estimate-reviewable-loc.sh`.

- **What:** Exact final paths — the shared heuristics doc
  (`speckit-coach/references/slicing-heuristics.md` vs another shared location) and the
  shared script dir (`speckit-coach/scripts/` vs a top-level shared `scripts/`).
  **Why deferred:** direction is locked (one shared doc + one shared script invoked via
  `${CLAUDE_PLUGIN_ROOT}`); only the precise directory is open.
  **Suggested next step:** finalize in the Plan phase against the existing plugin layout
  (mirror where PRSG-002 placed its shared normalizer/templates).

- **What:** How the skill reliably collects the estimator's structured inputs
  (# user stories, # surfaces, new-vs-modify) during a free-flowing interview.
  **Why deferred:** implementation detail, not a scoping decision.
  **Suggested next step:** resolve in Plan/Tasks — likely a short structured prompt the
  skill fills before calling the script.

## Recommended Next Step

> **Note (setup mode):** This section is informational — `/speckit-pro:speckit-scaffold-spec PRSG-005`
> has already created the worktree and will now enrich the workflow file from this doc.

Run the populated workflow with
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/PRSG-005-workflow.md`
after reviewing both this design concept and the workflow file. The Specify and Clarify
prompts in the workflow are seeded from the Q&A log above; the Open Questions seed the
autopilot Clarify sessions (estimator semantics + final paths).

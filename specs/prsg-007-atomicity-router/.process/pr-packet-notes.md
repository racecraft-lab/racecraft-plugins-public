# PR Review Packet — source material (PRSG-007 atomicity router)

> **Status:** source material for the autopilot's post-implementation PR-body
> step. This file is NOT the PR body. `generate-pr-body.sh` owns the actual PR
> description; this document supplies the "what changed / why / non-goals /
> review order / scope budget / traceability / verification / known gaps /
> rollback" content the spec's *PR Review Packet Requirements* section mandates.
> Do not open a PR from this file by hand.

## What changed

Ships a read-only atomicity classifier and wires the autopilot to record its
decision after the Tasks phase. The classifier answers one question — **can this
change be split into multiple small PRs safely?** — by inspecting a feature's
`tasks.md` / `plan.md` / `spec.md` and emitting a single machine-readable routing
decision. It changes nothing and blocks nothing: it classifies (`route`), flags
release risk (`releasable`), and emits a controlled `signals[]` vocabulary,
advisory `hints[]`, and canonical `warnings[]`.

Concretely:

- **One production script** — `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`
  (415 reviewable LOC; plain `bash` + `jq`). Decides splittability by **structural
  seams** (independent additive capabilities/surfaces), never by lines of code.
  Applies a hard-atomic override (a rename / version-pin / destructive-migration /
  mutual-exclusion-auth-payment / out-of-tree-contract-break signature forces
  `single-atomic-PR`), computes releasability independently of the route, and
  abstains to `one-navigable-PR` on uncertainty.
- **Layer-4 unit test** — `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh`
  (81 assertions; one fixture per change class + cross-cutting + dogfood + schema).
- **Ten Layer-4 fixtures** — one per change class under
  `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/`.
- **Workflow-template section** — a `## Atomicity Route` placeholder in
  `speckit-pro/skills/speckit-coach/templates/workflow-template.md` (the record the
  SKILL fills after Tasks/G5).
- **SKILL + reference docs** — the post-Tasks router step documented in
  `speckit-pro/skills/speckit-autopilot/SKILL.md` and
  `speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, mirrored into
  `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` for Claude+Codex prose parity.

The Phase-5 (Polish) group in this PR added the cross-cutting / dogfood / contract
assertions and the doc + Codex-mirror edits; the classifier script and the per-class
fixtures were built in the earlier phases of this same spec.

## Why

PR-Size Governance Phase 4 is the split-PR engine. Before any PR emission is wired,
this spec ships the **brain** that decides whether a change *can* be split safely.
Shipping it first — as a pure classifier that records a route but emits no PR —
de-risks the whole engine: the routing logic can be exercised and trusted before any
irreversible PR emission exists. A false positive only *refuses* a split (the safe
direction); the dangerous direction (recommending a split that breaks the tree at an
intermediate commit) is what the hard-atomic override and the abstain rule prevent.

## Non-goals (out of scope — flagged, not built)

- **No PR emission, branch creation, or multi-PR rewrite.** The classifier is
  read-only (FR-011) and wires nothing — it emits one JSON object. PR emission is
  PRSG-009; the layer-planner that consumes the route is PRSG-008.
- **No blocking / gating.** Advisory-only (FR-012): success never blocks; only a
  usage/unreadable-input error is a non-success exit (exit 2).
- **No LOC / sizing computation** (FR-002) — that is the reviewability gate's job.
- **No edit of, or call to, `reviewability-gate.sh`; no shared-library extraction**
  (FR-015). The two path matchers are DUPLICATED verbatim-equivalent under a
  `KEEP IN SYNC with reviewability-gate.sh` marker (FR-014).
- **No deep implementation of the three advisory probes** (flag-system,
  release-cadence, consumer-locality) — `hints[]`-only (FR-010).
- **No `change_class` JSON field** (recoverable from `route` + `signals`, FR-011a).
- **No `branch-by-abstraction` emission** — reserved enum value, never emitted by
  the MVP (FR-001, SC-008).
- **The route is not written to `SPEC-MOC.md`** — only the workflow file's
  `## Atomicity Route` section, and only by the SKILL (FR-013).

## Suggested review order

1. `contracts/routing-decision.schema.json` — the stable output contract (the shape
   every downstream spec reads).
2. `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` — the classifier.
   Read top-to-bottom: CLI front door + exit contract → JSON emitter → duplicated
   matchers → input-shape short-circuit → US1 detectors → US2 hard-atomic detectors
   → routing dispatch (precedence) → releasability pass.
3. `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh` — the assertions,
   including the cross-cutting (error path / read-only), dogfood self-check, and
   schema-validation blocks.
4. The ten fixtures under `fixtures/atomicity-route/`.
5. The doc edits: workflow-template `## Atomicity Route`, then the SKILL +
   phase-execution router step, then the Codex SKILL mirror.

## Scope budget (reviewability)

- **Primary surface:** scheduler/runtime (the new classifier invoked by the
  autopilot after Tasks).
- **Secondary surfaces:** harness/adapter (the Layer-4 test + fixtures), docs/process
  (the SKILL / template / Codex-mirror edits).
- **Production files:** 1 (`atomicity-route.sh`).
- **Reviewable LOC:** ~400 budget; the script is **415 LOC** — at the per-spec
  warning line, accepted (see Known gaps). One structural seam (classify-and-emit).
- **Split decision:** remains one spec. PR emission, the layer-planner, and multi-PR
  rewrite are separate downstream specs (PRSG-008, PRSG-009).

## Traceability — requirement / criterion → changed files + verification

Verification key: **L4** = `test-atomicity-route.sh` (81 assertions);
**L1** = Layer-1 structural validation. Every row's behavior is exercised by the
named L4 fixture/assertion and, where it touches a shipped file, gated by L1.

| Requirement | Where implemented | Verification |
|-------------|-------------------|--------------|
| FR-001 (five-route enum; `branch-by-abstraction` reserved) | `atomicity-route.sh` emitter + dispatch; `routing-decision.schema.json` | L4 contract block (positive enum-membership over every fixture + error + dogfood; SC-008 asserts the reserved route is never emitted) |
| FR-002 (seam-driven, no LOC metric) | `atomicity-route.sh` Detector 1 (surface count, not LOC) | L4 `additive-multi-seam → split-PR`; no sizing call in the script |
| FR-003 (input-shape short-circuit, then detector order) | `atomicity-route.sh` short-circuit + ordered detectors | L4 out-of-scope (missing/empty `tasks.md`) assertions |
| FR-004 (`tasks.md`-shape detector) | `atomicity-route.sh` Detector 1 | L4 `additive-multi-seam` + `change-shape:additive-multi-seam` token |
| FR-005 (additive-vs-modify detector) | `atomicity-route.sh` Detector 2 | L4 `modify-heavy → one-navigable-PR` + `change-shape:modify-heavy` |
| FR-006 (abstain to `one-navigable-PR`, never auto-split) | `atomicity-route.sh` dispatch default + additive-dominance gate on split | L4 abstain-floor assertions; `single-additive-seam` never `split-PR` |
| FR-007 / FR-007a (hard-atomic override; vocabulary-hygiene) | `atomicity-route.sh` Detectors A/C + dispatch precedence | L4 five `hard-atomic-*` fixtures → `single-atomic-PR` + matching token; **dogfood self-check** proves the keyword classes do not fire on PRSG-007's own enumerated vocabulary |
| FR-008 / FR-009 (releasability orthogonal to route; canonical warnings) | `atomicity-route.sh` releasability pass + the two `WARN_*` constants | L4 `destructive-migration` + `concurrency` → `releasable:false` + exact CI-green sentence; non-risk → `releasable:true`, empty `warnings[]` |
| FR-010 (advisory probes → `hints[]` only) | `atomicity-route.sh` Detectors 3-5 | L4 flag-system hint surfaces; disjointness assertion (`signals[]` ∩ `hints[]` = ∅) |
| FR-011 / FR-011a / FR-011b (read-only; flat JSON contract; controlled vocab) | `atomicity-route.sh` emitter; schema | L4 read-only snapshot (dir byte-identical after a run); five-key shape; contract block |
| FR-012 (advisory-only; error path is exit 2, no `route`) | `atomicity-route.sh` `emit_error` + exit contract | L4 cross-cutting error-path block (exit 2 + parseable `error` + no `route`) |
| FR-013 (the SKILL records the route, not the script) | workflow-template `## Atomicity Route`; SKILL + phase-execution + Codex SKILL | L1 (`validate-skills` 98/98, `validate-codex-skills` 145/145) |
| FR-014 / FR-015 (stack-agnostic duplicated matchers; no gate call/edit) | `atomicity-route.sh` `surface_for_path`/`is_excluded_generated` under the KEEP-IN-SYNC marker | L1 `validate-scripts`; the gate is neither sourced nor edited |
| SC-001 (one route, five-value enum, contract keys) | emitter + schema | L4 contract block |
| SC-002 (seam-driven split, not size-driven) | Detector 1 + additive-dominance gate | L4 `additive-multi-seam` vs `single-additive-seam` |
| SC-003 (every hard-atomic signature → `single-atomic-PR`, even with seams) | dispatch precedence (override prepended into the if/elif chain) | L4 `hard-atomic-rename` suppresses an ACTIVE split signal |
| SC-004 (destructive-migration + concurrency → not releasable + warning) | releasability pass | L4 releasability block |
| SC-005 (uncertain → `one-navigable-PR`, never split) | abstain default | L4 abstain-floor |
| SC-006 (never blocks, never writes a file) | exit contract + read-only emitter | L4 read-only snapshot + error-path exit 2 |
| SC-007 (one L4 fixture per change class; L1 passes) | ten fixtures; doc edits | L4 81/81; L1 887/887 |
| SC-008 (MVP never emits `branch-by-abstraction`; modify-heavy → `one-navigable-PR`) | dispatch (no reserved branch) | L4 contract block + `modify-heavy` assertions |

## Verification evidence

- **Layer 4** — `bash tests/speckit-pro/run-all.sh --layer 4` → all green;
  `test-atomicity-route` **81/81** (was 56; this group added 25: cross-cutting 6,
  dogfood 6, contract 13).
- **Layer 1** — `bash tests/speckit-pro/run-all.sh --layer 1` → **887/887**, with
  `validate-codex-skills` **145/145** (the Codex-parity break point) and
  `validate-codex-parity` **78/78**.
- **Dogfood self-check (load-bearing, FR-007a)** — running the finished classifier on
  PRSG-007's own feature dir yields `route: one-navigable-PR`, `releasable: true`,
  `signals: ["change-shape:modify-heavy"]` — i.e. NOT `single-atomic-PR`, not a split,
  releasable, and no `releasability:*` token. PRSG-007's artifacts enumerate
  auth/payment/lock/mutex/rename/concurrency only as detector *vocabulary* and saturate
  the corpus with modify keywords, so the firewall holds. Encoded as four assertions
  and proven non-vacuous (inverting any one flips exactly one assertion to FAIL).
- **Contract** — every emitted object (ten fixtures + the error branch + the dogfood
  run) validates against `routing-decision.schema.json` via a python-stdlib checker
  (no `jsonschema` dependency); `branch-by-abstraction` is asserted absent from every
  object.

## Known gaps / deferred work

- **PRSG-008 (layer-planner)** — consumes this route to plan the actual slices.
- **PRSG-009 (multi-PR emission)** — emits the PRs / creates the branches. This spec
  wires neither; it only records the route.
- **Deferred deep probes** — the three advisory probes (flag-system, release-cadence,
  consumer-locality) are shallow keyword surfaces emitted as `hints[]` only. Deepening
  consumer-locality into a *decisive* detector (which is what would make
  `branch-by-abstraction` emittable) is owned by PRSG-010 US3. Until then a
  modify-heavy non-hard-atomic change abstains to `one-navigable-PR`.
- **Additive-dominance MVP limitation** — the split branch is gated on a strict
  "proven additive" reading (additive signal present AND zero modify signals). This is
  deliberately conservative: a change that mixes additive and modify signals will not
  auto-split even if its seams are genuinely independent. This is the safe direction
  (no false split) and is acceptable for the MVP; a richer additive/modify
  discrimination is future work, not this spec.
- **415-LOC note** — the script is 415 reviewable LOC, marginally over the ~400
  warning line. Accepted: it is one production file, one structural seam
  (classify-and-emit), plain `bash` + `jq`, with the over-line portion being the
  mandated duplicated matchers (FR-014) and the per-class detector blocks, each
  individually small and independently reviewable. If a future detector pushes it
  materially further, the template rule is to split the spec rather than grow the
  script.

## Rollback / feature-flag notes

- **No feature flag and none needed.** The classifier is read-only and advisory-only:
  it writes no file, blocks nothing, and is invoked at exactly one point (the autopilot
  after Tasks/G5). Nothing downstream acts on the route yet (PRSG-008/009 are not
  shipped), so the route is recorded but inert.
- **Rollback** is removal-only and low-risk: dropping the post-Tasks invocation from
  the SKILL (and, if desired, the script + test + fixtures) restores the prior
  behavior exactly — the autopilot simply does not record a `## Atomicity Route`
  section. No data migration, no state, no irreversible action is involved.
- **Fix-forward** (per repo convention) is preferred over reverting history: a `fix:`
  commit adjusting a detector or a fixture flows through release-please as a patch.

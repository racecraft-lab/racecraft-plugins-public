# PR-Size Governance — Implementation Roadmap

> Companion to the research synthesis at
> [`../research/spec-pr-size-governance-research.md`](../research/spec-pr-size-governance-research.md).
> **Source PRD:** [`../../prd-pr-size-governance.md`](../../prd-pr-size-governance.md).
> Status: **in progress** — Phase 1 relocation done (PRSG-001 ✅ PR #111); Phase 2 navigation spine done (PRSG-002 ✅ PR #116; PRSG-003 ✅ PR #121; PRSG-004 ✅ PR #129); Phase 3 upstream sizing done (PRSG-005 ✅ PR #120; PRSG-006 ✅ PR #119); Phase 4 router done (PRSG-007 ✅ PR #133); Phase 4 layer-planner done (PRSG-008 ✅ PR #138); Phase 4 split-PR emission done (PRSG-009 ✅ PR #145); Phase 6 retro-migration done (PRSG-011 ✅ PR #132). Active: PRSG-010 scaffolded on branch `prsg-010-harden-the-hatch` (Phase 5). Planned follow-on: PRSG-012 reviewer-ready PR packets. Created 2026-06-03; status refreshed 2026-06-11.

## Vision

Make small, reviewable PRs the **default automatic output** of speckit-pro's
autopilot — by *construction*, not by an end-stage gate. Replace the defeated
detective control (`reviewability-gate.sh`, a no-op whose exception keyword ships as
template boilerplate) with three composed layers:

- **Relocate** the ~32% auto-generated process-artifact tax out of the review diff.
- **Split** delivery into one PR per `tasks.md` user-story increment (squash-immune
  independent slices), routed by an **atomicity test** so the rare irreducible cases
  fall back safely.
- **Navigate** the whole tree (epic ↔ spec ↔ slice ↔ PR ↔ artifact) with a **MOC
  spine** so decomposition adds traceability instead of cognitive load.

…and a **state-keyed retro-migration** (PRSG-011) so existing projects upgrade cleanly
instead of becoming a permanent split-brain repo.

## Locked decisions (2026-06-03)

| Decision | Choice |
|----------|--------|
| Code strategy | **O2 split-PR default** + atomicity-test routing |
| Slice unit | **PR within one spec** (one SPEC-ID, one `tasks.md`, **one artifact set**, N PRs). `006a/006b` sub-specs reserved for O5 monster-epics only |
| Artifacts v1 | **Collapse-only** via `.gitattributes` **`linguist-generated`** (NOT `-diff` — keeps artifacts loadable/inspectable; see PRSG-001 decision); post-merge relocation deferred to v2 |
| MOC "Why" annotations | **Advisory** in v1 |
| Releasability gate | **Detect-and-route to atomic + warn**; defer invariant-checking machinery |
| Mechanical-only specs | **Accept + route to one-navigable-PR** (don't decline) |
| No-flag cutovers | **Atomic PR + release-hold note** by default; *offer* an app-native runtime toggle |
| Migration / back-compat | **Tiered retro-migration (PRSG-011)** — supersedes the earlier new-specs-only stance. PRSG-001–010 ship new-specs-only; PRSG-011 adds state-keyed backfill: Tier 1 repo-level (eager, version-gated), Tier 0 navigation index-backfill for completed specs, Tier 2 on-demand relocate codemod for the ~8 specs that have a `specs/<NNN>/` dir. In-flight specs (per `.specify/feature.json`) are **frozen**; legacy specs grandfathered by marker-absence |
| PR packet ownership | **Generator-owned first draft + pre-create validation (PRSG-012)**. Both single-PR and split-PR paths generate explicit titles/bodies from deterministic evidence before `gh pr create`; humans or agents may refine only sanctioned prose fields |

## Sequencing principle (non-negotiable)

**Relocate-first → MOC spine + upstream sizing → split-PR engine → harden-the-hatch
LAST.** Hardening detection before the automatic small path exists would just block
finished runs and grow exception usage — the exact prior-art failure. The hatch is
the *last* thing wired, and only as a backstop that triggers **re-slicing**, not blind
blocking.

```
Phase 1 ─ Relocate (PRSG-001)            ← cheap precondition, immediate win
   │
Phase 2 ─ MOC spine (PRSG-002→003→004)   ┐
Phase 3 ─ Upstream sizing (PRSG-005,006) ┘ ← parallelizable with Phase 2
   │
Phase 4 ─ Split-PR engine (PRSG-007→008→009)  ← core architectural change
   │
Phase 5 ─ Harden the hatch (PRSG-010)    ← ONLY after the small path exists
   ┊
Phase 6 ─ Retro-migration (PRSG-011)     ← needs only PRSG-001/002/003; can land in
                                            parallel with Phases 3–5 once the spine exists
   │
Phase 7 ─ Reviewer-ready PR packets (PRSG-012) ← hardens title/body output after split-PR emission exists
```

**Visibility expectation (set, don't fix):** the first *visible* drop in reviewable PR
size lands at **PRSG-009**, not earlier. Phase 1 *collapses* artifacts in the GitHub UI
but file-count is unchanged; code + tests (~68% of a feature diff) stay big until
splitting exists. Phases 1–3 are the safety/navigation/sizing groundwork that makes
splitting safe — they are not expected to move the headline number on their own.

## SPEC catalog

Each SPEC is scoped to land as a small PR (or a short slice set). Budget = target
**production** LOC after artifact relocation; per CLAUDE.md, scripts are plain
`bash`+`jq`.

---

### PRSG-001 — Artifact relocation: tiering, `.process/`, collapse  · Phase 1 · P1 · MVP · ✅ Complete
**Why:** ~32% of every feature PR is auto-generated exhaust. Remove it from the review
diff at the source. Orthogonal precondition for everything else.

- **US1 — Tier + redirect.** Define the CONTRACT (visible: `spec.md`, `plan.md`,
  `tasks.md`, `research.md`, `data-model.md`, `contracts/**`, `checklists/**`,
  `SPEC-MOC.md`) vs EXHAUST taxonomy. Redirect scaffold-spec and autopilot exhaust
  writes (`design-concept`, `workflow.md`, `peer-review-*`, `verification-evidence`,
  `retrospective`) to `specs/<NNN>/.process/`.
- **US2 — Collapse + align + lint.** Ship repo-root `.gitattributes`
  (`specs/*/.process/** linguist-generated=true`); align `reviewability-gate.sh`
  `is_excluded_generated()` to the same glob; Layer-1 lint asserting the glob is
  scoped to `.process/` ONLY and never matches a CONTRACT path.
- **Decision — collapse mechanism (`linguist-generated` only; `-diff` deferred).**
  v1 uses `linguist-generated=true` ALONE. It collapses the artifact diff in the PR but
  keeps it **loadable on demand** ("Load diff"), preserving audit/provenance.
  **`-diff` is deferred:** adding it would also drop artifact LOC out of the PR's `+/−`
  size count, but it renders the files **non-diffable** (un-inspectable in the PR) — a
  worse provenance tradeoff. Consequence (consistent with the Visibility expectation
  above): `linguist-generated` changes how the diff *reads*, **not** the headline
  `+/−`, the per-file stats, or the file-count — the real size reduction comes from
  splitting (PRSG-009) and relocation (PRSG-011), not from `.gitattributes`.
- **Skills/files:** `speckit-scaffold-spec`, `speckit-autopilot/references/phase-execution.md`, `reviewability-gate.sh`, new `.gitattributes`.
- **Deps:** none. **Budget:** ~250 LOC. **Tests:** L1 (gitattributes + scoping), L4 (commit-target logic).

---

### PRSG-002 — MOC templates + scaffold-time skeleton + version-gated lints  · Phase 2 · P1 · ✅ Complete (PR #116)
**Why:** the navigation/traceability spine that makes relocation *safe* (hidden files
stay linked) and decomposition *navigable* (you navigate the map, not memorize the tree).

- **US1 — Templates + skeleton.** roadmap-MOC and spec-MOC templates with the
  frontmatter join-key contract (`up`/`related`/`status`/`rank`/`spec_id`/`structureVersion`).
  scaffold-spec writes the `SPEC-MOC.md` skeleton WITH `up:` + current `structureVersion`
  at creation (orphan prevention); mint a spec-MOC only at the multi-slice squeeze point
  (single-slice spec → no MOC).
- **US2 — Version-gated lints + ID normalization (critical).** Layer-1 lints: orphan
  (`.md` under a spec tree lacking a valid `up:`); stale-index (any MOC relative link →
  nonexistent file). Relative `[]()` links only — never `[[wikilinks]]`. **Born
  version-gated:** each lint fires ONLY when the spec's `SPEC-MOC.md` frontmatter has
  `structureVersion >= N`; a spec with **no marker is grandfathered/exempt** —
  otherwise the first plugin upgrade red-fails CI on every pre-existing legacy spec
  (this is a hard upstream coupling to PRSG-011, not a downstream patch). **ID
  normalization:** join doc IDs (`SPEC-013B`) to dir IDs (`013b-slug`) by lowercase +
  strip-`SPEC-` + **exact-segment match** (so `SPEC-013A` ≠ the `013a1` dir); naive
  prefix-matching emits false orphan/stale hits.
- **Skills/files:** `speckit-scaffold-spec`, new templates, Layer-1 test scripts.
- **Deps:** PRSG-001 (`.process/` path). **Budget:** ~350 LOC. **Tests:** L1, L4 (version-gate + ID-normalization fixtures).

---

### PRSG-003 — Generated index/PRs/backlinks + status integration + phase-gate regen  · Phase 2 · P1 · ✅ Complete (PR #121)
**Why:** plain markdown has no live engine; generated blocks must be regenerated or
they silently lie (the #1 risk).

- **US1 — Generator.** `scripts/generate-spec-index.sh` writes the GENERATED INDEX
  (roadmap-MOC), GENERATED PRS (`slice → PR# → merged SHA`), and GENERATED BACKLINKS
  blocks between sentinel comments. Deterministic (fixture test). Uses the canonical
  **ID-normalization** join (lowercase + strip-`SPEC-` + exact-segment) and always
  **regenerates the whole sentinel-bounded zone** (never `sed`-patches — stale zones lie).
- **US2 — Wire it.** `speckit-status` invokes the generator (it IS the index
  generator); autopilot runs regeneration as a **phase-gate step** at phase boundaries.
- **Skills/files:** `speckit-status`, `speckit-autopilot`, new `generate-spec-index.sh`.
- **Deps:** PRSG-002. **Budget:** ~350 LOC. **Tests:** L1 (determinism fixture), L4.

---

### PRSG-004 — Roadmap-MOC home note from PRD + coach the two-zone structure  · Phase 2 · P2 · ✅ Complete (PR #129)
**Why:** the user's cognitive-load answer — one home note, curated epics + generated
index, authored once cheaply during the PRD interview.

- **US1 — Emit.** `speckit-prd` emits the roadmap-MOC home note (human-curated epics
  zone + GENERATED INDEX sentinels) alongside the PRD + technical-roadmap (which is
  ~80% a MOC already).
- **US2 — Coach.** `speckit-coach` teaches the curated/generated two-zone split and the
  "cap epics below ~10" guardrail.
- **Skills/files:** `speckit-prd`, `speckit-coach`.
- **Deps:** PRSG-002, PRSG-003. **Budget:** ~200 LOC. **Tests:** L1.

---

### PRSG-005 — Vertical-slice sizing heuristics in PRD/grill-me  · Phase 3 · P1 · ✅ Complete (PR #120)
**Why:** attack the root cause at the cheapest moment — specs born PR-sized.

- **US1 — Slicing heuristics.** Bake SPIDR + INVEST + vertical-slicing guidance into
  `speckit-prd` and `grill-me` so the SPEC catalog is emitted as thin, end-to-end
  slices by construction.
- **Skills/files:** `speckit-prd`, `grill-me`.
- **Deps:** none (parallel with Phase 2). **Budget:** ~200 LOC. **Tests:** L1, L2 (trigger sanity).

---

### PRSG-006 — Plan-phase reviewability budget + gate threshold rework  · Phase 3 · P1 · ✅ Complete (PR #119)
**Why:** make sizing preventive, not detective; fix the metrics; replace the broken
escape hatch with typed exceptions.

- **US1 — Preventive budget.** Plan-phase reviewability sub-plan: estimate per-slice
  footprint, **auto-approve under budget**, surface only when over.
- **US2 — Threshold rework.** ~400 production-LOC ceiling (code only, greenfield
  allowance); **drop surface-count as a blocker**; replace the one-keyword exception
  with typed exception classes (refactor/infra/upgrade).
- **Skills/files:** `speckit-autopilot` (plan), `reviewability-gate.sh`, roadmap template.
- **Deps:** PRSG-001. **Budget:** ~300 LOC. **Tests:** L4.

---

### PRSG-007 — Atomicity-test router (read-only classifier)  · Phase 4 · P1 · engine MVP · ✅ Complete (PR #133)
**Why:** the brain that makes split-PR a *safe* default. Ship as a read-only classifier
that emits a routing decision into the workflow file before any emission is wired.

- **US1 — Classifier.** Implement the atomicity test → route ∈ {split-PR,
  one-navigable-PR, branch-by-abstraction, single-atomic-PR, out-of-scope}. Detection
  order: `tasks.md` shape → additive-vs-modify (grep `UPDATE/DELETE/DROP/CHECK` vs
  `CREATE TABLE`/nullable adds) → flag-system probe → release cadence → consumer
  locality.
- **US2 — Hard-atomic + releasability detect-and-route.** Hard-atomic override
  (exported-symbol rename, global version pin, destructive migration, mutual-exclusion/
  auth/payment primitive, out-of-tree contract break) → atomic. Detect
  destructive-migration / concurrency signatures and route to atomic + **warn that
  CI-green ≠ releasable** for those classes.
- **Skills/files:** `speckit-autopilot`, new `scripts/atomicity-route.sh`.
- **Deps:** PRSG-006 (benefits). **Budget:** ~400 LOC. **Tests:** L4 (one fixture per change class), L1.

---

### PRSG-008 — Layer-planner: tasks.md → ordered increments  · Phase 4 · P1 · ✅ Complete (PR #138)
**Why:** turn the decomposition `tasks.md` already declares into an executable plan.

- **US1 — Planner.** Parse user-story phases + `## Dependencies & Execution Order` +
  `### Incremental Delivery` → ordered increments (Foundation → US1…USN → Polish) with
  per-increment file/test sets and the dependency DAG.
- **Skills/files:** `speckit-autopilot`, new `scripts/plan-layers.sh`.
- **Deps:** PRSG-007. **Budget:** ~350 LOC. **Tests:** L4 (planner fixtures and vendored schema fixture after archive cleanup).

---

### PRSG-009 — Multi-PR emission (post-implementation rewrite)  · Phase 4 · P1 · ✅ Complete (PR #145)
> Completed 2026-06-11 via PR #145; workflow:
> `docs/ai/specs/.process/PRSG-009-workflow.md`.

**Why:** the actual behavior change — stop flattening; emit N PRs.

- **US1 — Emit N PRs.** Rewrite post-implementation §3.2 from one `gh pr create` to N
  PRs in dependency order (Style B incremental stack), each carrying its slice's tests,
  with per-slice PR-body generation.
- **US2 — MOC + restack.** Update the spec-MOC GENERATED PRS table (`slice→PR#→SHA`)
  on each PR; handle squash-only restack (gh-stack optional, else rebase in the review
  `/loop`).
- **US3 — Branch topology + CI mapping.** Extend the branch/worktree model (today
  scaffold-spec sets up ONE branch) to the per-slice topology (Style B incremental
  stack). Reconcile the integration suite (post-implementation §3.1 runs the FULL suite
  once today): each slice PR's CI runs that **slice's scoped tests**; the **full
  regression suite gates only the base/last merge** — a later slice's tests cannot pass
  before its code merges, so they must not block earlier slice PRs.
- **Skills/files:** `speckit-autopilot/references/post-implementation.md`, `generate-pr-body.sh`, `generate-spec-index.sh`, `multi-pr-emission.sh`, `restack.sh`.
- **Deps:** PRSG-008, PRSG-003 (MOC PRs table), PRSG-001 (artifacts out of slice).
  **Budget:** ~450 LOC. **Tests:** L4, L3 descriptor coverage, L8 (Codex parity).
  **Archive:** `specs/prsg-009-multi-pr-emission` was removed from active
  `specs/**` after PR #145 merged; recovery is through merge commit
  `a3361d50e3dfc5463fb2d5dbb2737a3525637a32`.

---

### PRSG-010 — Harden the hatch + O5 monster-epics  · Phase 5 · P2 · LAST · 🔄 In Progress
> Scaffolded 2026-06-11 on branch `prsg-010-harden-the-hatch`; workflow:
> `docs/ai/specs/.process/PRSG-010-workflow.md`.

**Why:** only now that the automatic small path exists is it safe to make the backstop
real.

- **US1 — Real backstop.** `final-reviewability-backstop.sh` records
  `final_reviewability_gate`, stops before PR body generation, `gh pr create`,
  or `multi-pr-emission.sh`, and writes a re-slicing packet with concrete
  PRSG-007/008/009 operator steps. `reviewability-gate.sh` still honors explicit
  typed exceptions, but only when the branch adds an exact operator-owned
  `refactor`, `infra`, or `upgrade` pragma in review-visible CONTRACT Markdown;
  generated zones, templates, `.process`, PR bodies, and code fences are rejected
  as exception provenance.
- **US2 — Monster-epics (O5).** O5 is a fallback after ordinary
  PRSG-007/008/009 split planning cannot produce reviewable slices. The parent
  manifest is `specs/<parent-branch>/o5-parent-manifest.json`; child specs remain
  flat siblings under `specs/<child-branch>`, never nested under the parent.
  `o5-topology.sh` validates topology first, emits one child status row per
  manifest child in order, and reports declared rollup drift read-only.
- **US3 — Deepen the contextual atomicity probes.** `atomicity-route.sh` promotes
  deterministic high-confidence flag-system, release-held cutover, and
  consumer-locality evidence into closed `signals[]`; weak, fixture-only,
  code-fence-only, stale, or conflicting evidence stays route-neutral in closed
  `hints[]`.
- **Skills/files:** `final-reviewability-backstop.sh`, `reviewability-gate.sh`,
  `atomicity-route.sh`, `o5-topology.sh`, roadmap/templates,
  `speckit-scaffold-spec` (O5 fallback), `speckit-status` (rollup/re-slicing).
- **Deps:** ALL of Phases 1–4. **Budget:** split stack. **Tests:** L4, L1, L8 dry-run.

---

### PRSG-011 — Retro-migration: version marker + state-keyed backfill/relocate  · Phase 6 · P2 · ✅ Complete (PR #132)
> Completed 2026-06-09 via PR #132; workflow:
> `docs/ai/specs/.process/PRSG-011-workflow.md`.

**Why:** PRSG-001–010 are new-specs-only; existing projects (Paddock: 27 SPEC IDs;
focusengine: 50) would otherwise be a permanent split-brain repo, **and PRSG-002's
version-gated lints need a marker-writer or legacy specs stay exempt forever.** Supplies
the backward/contract half. Reuses `speckit-upgrade`'s backup-and-restore (the v0.8.13
slash→skills migration is the precedent) and **mirrors** `speckit-archive-run`'s
gated-safety pattern (`--dry-run`/`--apply`, `git show` recovery, no history rewrite).

- **US1 — Version marker + Tier-1 repo edits (eager, version-gated).** New
  `.specify/structure-version.json` = `{"structureVersion": N}` (single integer
  high-water-mark; new dedicated file, layout-agnostic across both repos).
  `migrate-structure.sh` runs two-phase like `nx migrate`: phase 1 reads the marker,
  `jq`-selects migrations with `appliesFrom > current`, and **prints the ordered pending
  list (this IS `--dry-run`)**; phase 2 applies + writes the new marker. Tier-1 steps
  touch **no** existing spec data: write repo-root `.gitattributes`; de-boilerplate the
  **live project roadmap** (strip `split exception` lines — the *project* roadmap, NOT
  the plugin template, which is PRSG-010's job). Each step self-guards (idempotent);
  hard-fail on a dirty tree. (The gate `is_excluded_generated()` fix is PRSG-001's job,
  not here — the gate never reads `.gitattributes`.)
- **US2 — Tier-0 navigation backfill (completed specs, the bulk).** Reuse PRSG-003's
  `generate-spec-index.sh` to emit one roadmap-MOC GENERATED-INDEX row per historical
  spec (one file touched; **no file moves, no frontmatter stamp** on legacy specs — they
  stay exempt-by-absence). ID-normalized join; whole-zone regen.
- **US3 — Tier-2 relocate codemod (on-demand, NOT tracked-lazy).**
  `relocate-process-artifacts.sh` — for the ~8 specs that HAVE a `specs/<NNN>/` dir,
  `git mv` the enumerable PROCESS allow-list (`retrospective.md`, `*-report.md`,
  `uat-*`, `pr-review-packet.md`, `cleanup-report.md`, `analysis.md`, `evidence/`) into
  `.process/`, leave CORE in place (`spec/plan/tasks/data-model/research/quickstart/
  contracts/checklists`), regenerate links + index, stamp `structureVersion` in the
  SPEC-MOC — all in ONE atomic commit. **Dual-registered** (Angular
  `ng-update`/`ng-generate` precedent) so scaffold-spec/autopilot offer it when a
  **frozen** spec is thawed; there is **no deferral tracker** (CLAUDE.md rule 2).
  FORCED non-skippable backup + dirty-tree guard + real `--dry-run`. **In-flight specs
  (per `.specify/feature.json`) are skipped in every tier.**
- **Skills/files:** `speckit-upgrade` (Tier 1+0 step), `speckit-scaffold-spec` +
  `speckit-autopilot` (Tier-2 codemod registration), new `.specify/structure-version.json`,
  new `migrate-structure.sh` + `relocate-process-artifacts.sh` + ID-normalization helper.
- **Deps:** PRSG-001 (`.process/` glob), PRSG-002 (MOC contract + version-gated lints),
  PRSG-003 (index generator). **Budget:** ~450 LOC. **Tests:** L1, L3 (speckit-upgrade
  migration behavior), L4 (dry-run / idempotency / move-set + ID-norm fixtures), L8.

---

### PRSG-012 — Reviewer-ready PR packet contract  · Phase 7 · P1 · ⏳ Pending
> Added 2026-06-11 after the PRSG-010 split-PR stack exposed a reviewer-experience
> regression: PRs were small enough to review, but titles and descriptions were still
> hard to understand without manual cleanup.

**Why:** PRSG-009 made split PRs possible, and SPEC-006a/b added UAT runbook wiring,
but the post-implementation PR packet is not yet enforced as a reviewer-ready contract.
Generated PRs can still ship vague titles, incomplete bodies, stale placeholders, or
patronizing labels unless a human repairs them after creation. PRSG-012 makes the
title/body packet deterministic, neutral, and validated before any PR is opened.

- **US1 — Explicit generated titles.** Both the single-PR path and split-PR path
  generate conventional, specific PR titles before creation and call `gh pr create`
  with `--title` plus `--body-file`. Titles must identify the user-visible or
  operator-visible change, not only the internal slice code or branch name.
- **US2 — Actionable body contract.** `generate-pr-body.sh` produces neutral
  reviewer-facing sections: `Summary`, `What Changed`, `Why It Matters`,
  `How To Review`, `How To UAT`, `Verification`, `Scope`, and `Known Gaps`.
  The body must not contain unfilled template comments, stale placeholders, or labels
  such as `ELI5` or `Plain-English Summary`.
- **US3 — Pre-create validator.** Add deterministic validation that runs before every
  `gh pr create` path, including `multi-pr-emission.sh`. Invalid packets block before
  PR creation and record exact remediation in workflow evidence; they do not create a
  PR that reviewers have to decode after the fact.
- **US4 — Safe prose refinement.** Scripts own the first draft from spec, plan,
  slice packet, UAT runbook, and verification evidence. Human or agent refinement may
  edit only explicit prose fields while preserving generated governance sections,
  source markers, UAT content, traceability, and verification evidence.
- **Grill-me decisions (2026-06-11):** pre-create gate over advisory check;
  generator-owned draft over agent-authored draft; same contract for single-PR and
  split-PR paths; actionable sections with neutral wording.
- **Skills/files:** `speckit-autopilot/references/post-implementation.md`,
  `speckit-autopilot/references/phase-execution.md`, `generate-pr-body.sh`,
  `multi-pr-emission.sh`, slice packet/PR packet schemas, new PR packet validator.
- **Deps:** PRSG-009 (split-PR emission), SPEC-006a/b (UAT runbook and PR-body wiring),
  PRSG-010 (final backstop ordering). **Budget:** ~350 LOC. **Tests:** L4
  validator/body fixtures, L3 functional eval for PR packet generation, L7 emission
  replay, L8 Codex parity.

## Which skills/files change (matrix)

| Skill / file | SPECs |
|--------------|-------|
| `speckit-scaffold-spec` | 001, 002, 009, 010, 011 |
| `speckit-autopilot` (phase-execution / post-implementation) | 001, 003, 006, 007, 008, 009, 011, 012 |
| `speckit-prd` | 004, 005 |
| `grill-me` | 005 |
| `speckit-coach` | 004 |
| `speckit-status` | 003, 010 |
| `speckit-upgrade` | 011 |
| `reviewability-gate.sh` | 001, 006, 010 |
| roadmap template | 006, 010 |
| new scripts (`generate-spec-index.sh`, `atomicity-route.sh`, `plan-layers.sh`, `migrate-structure.sh`, `relocate-process-artifacts.sh`, PR packet validator) | 003, 007, 008, 011, 012 |
| `.gitattributes` (new) · `.specify/structure-version.json` (new) | 001 · 011 |

## Cross-cutting requirements (apply to every SPEC)

- **Codex parity is mandatory, not optional.** Every `skills/<name>/SKILL.md` change
  that has a `codex-skills/<name>/` mirror MUST be mirrored in the same SPEC, keeping
  `tests/layer1-structural/validate-codex-skills.sh` (L1) and the **Layer-8 parity
  fixtures** green; run `speckit-skill-reviewer` as a pre-commit gate. This applies to
  every catalog SPEC that touches a mirrored skill (at minimum `speckit-autopilot`,
  and any of `scaffold-spec`/`prd`/`coach`/`status`/`upgrade` that carry a Codex
  variant) — i.e. **PRSG-001 through PRSG-012**. Add **L8** to those SPECs' test sets
  and treat the Codex mirror as part of each SPEC's deliverable, or parity tests fail
  around PRSG-002.
- **Migration (PRSG-011) supersedes the earlier new-specs-only stance.** PRSG-001–010
  ship new-specs-only; **PRSG-011** adds state-keyed retro-migration (Tier 1 repo-level,
  Tier 0 navigation backfill, Tier 2 on-demand relocate codemod) gated by a
  `.specify/structure-version.json` marker, legacy specs grandfathered by marker-absence.
  **Hard upstream coupling:** PRSG-002's lints MUST be born version-gated (see PRSG-002
  US2), or the first upgrade red-fails CI on all pre-existing specs before PRSG-011 runs.
- **Scripts-first (determinism + token savings) — design mandate.** Any step whose
  logic is deterministic MUST be a `bash`+`jq` script invoked by the skill/agent, NOT
  LLM reasoning. Reserve agent/LLM work for genuine ambiguity or human-judgment
  (the curated "Why", router escalation on an unclassifiable spec). Three payoffs:
  (1) **determinism** — testable by a Layer-4 fixture (same inputs → byte-identical
  output) instead of a flaky AI eval; (2) **token savings** — no agent round-trip at
  runtime; (3) **smaller eval surface** — every bit of logic moved into a script
  *removes* a unit of L2/L3/L6 AI-eval burden and replaces it with a cheap L4 test.
  Concretely, the router (PRSG-007), layer-planner (PRSG-008), and migration runner +
  codemod (PRSG-011) are **scripts**, not agents — so they need L4 determinism
  fixtures, not L5/L6/L7 agent evals. Each script: same inputs → byte-identical output.

- **Tests AND evals are mandatory for every skill addition/change — non-negotiable.**
  A SPEC is not done until its verification proves the change works as planned:
  - **Skill behavior changed** → **Layer-3 functional eval** (the skill actually does
    the new thing end-to-end).
  - **Skill description / trigger surface changed or a skill added** → **Layer-2
    trigger eval** (triggers on the intended phrases; no over/under-trigger regression).
  - **New deterministic logic** → **Layer-4** script unit test with a determinism fixture.
  - **New agent** → **Layer-5** tool-scoping + **Layer-7** dispatch-graph (+ **Layer-6**
    efficiency if it makes a model/effort choice). (Scripts-first minimizes this set.)
  - **Mirrored skill** → **Layer-1** `validate-codex-skills.sh` + **Layer-8** parity.
  - Structural/file changes → **Layer-1**. Multi-PR/dispatch changes → **Layer-7**.
  The L2/L3/L6 harnesses live under `tests/layer2-trigger/`, `tests/layer3-functional/`,
  `tests/layer6-efficiency/` and require `claude -p` + the `skill-creator` plugin
  (developer-local); CI runs the default `bash tests/run-all.sh` suite (Layers 1, 4, 5). Layer 7 replay (`--integration`) and Layer 8 parity are opt-in runs. The
  authoritative per-SPEC coverage is the table below.

## Per-SPEC test & script coverage (authoritative)

Layers: **L1** structural · **L2** trigger eval (AI) · **L3** functional eval (AI) ·
**L4** script unit/determinism · **L5** tool scoping · **L6** efficiency (AI) ·
**L7** integration/dispatch · **L8** Codex parity.

| SPEC | Skill change | Deterministic scripts (own L4 fixture) | Required layers |
|------|--------------|----------------------------------------|-----------------|
| 001 | scaffold-spec, autopilot, gate (behavior) | commit-target redirect; `gate` exclusion-glob; `.gitattributes` (static) | L1, **L3**, L4, L8 |
| 002 | scaffold-spec (behavior) | `generate-moc-skeleton.sh`, `lint-moc-orphans.sh`, `lint-moc-stale.sh` (version-gated; ID-normalized) | L1, **L3**, L4, L8 |
| 003 | speckit-status, autopilot (behavior) | `generate-spec-index.sh` (INDEX/PRS/BACKLINKS; ID-normalized; whole-zone regen) | L1, **L3**, L4, L7, L8 |
| 004 | speckit-prd, speckit-coach (desc+behavior) | `generate-roadmap-moc.sh` (or reuse 003) | L1, **L2**, **L3**, L8 |
| 005 | speckit-prd, grill-me (desc+behavior) | `estimate-spec-size.sh` (budget inputs) | L1, **L2**, **L3**, L4, L8 |
| 006 | autopilot (plan), gate, roadmap template | `reviewability-gate.sh` rework, `estimate-reviewable-loc.sh` | L1, **L3**, L4, L8 |
| 007 | autopilot (behavior) | **`atomicity-route.sh`** (full router; agent only on ambiguous) | L1, L4 (one fixture/change-class), L7, L8 |
| 008 | autopilot (behavior) | **`plan-layers.sh`** (tasks.md → ordered increments) | L4 (real-tasks.md fixtures), L7, L8 |
| 009 | autopilot, scaffold-spec, gen-pr-body (behavior) | `plan-layers.sh` (reuse), `generate-pr-body.sh` (extend), `restack.sh` | L4, **L3** (e2e: N PRs on a fixture spec), L7, L8 |
| 010 | gate, template, scaffold-spec (epic), status (rollup) | gate exit-code/re-slice wiring, `rollup-epic.sh` | L1, **L3**, L4, L8 |
| 011 | speckit-upgrade (behavior); scaffold-spec/autopilot (codemod registration) | `migrate-structure.sh`, `relocate-process-artifacts.sh`, ID-norm helper | L1, **L3**, L4, L8 |
| 012 | autopilot PR packet generation/validation | `generate-pr-body.sh` extension, PR packet validator, `multi-pr-emission.sh` title/body checks | L4, **L3**, L7, L8 |

Rule of thumb visible in the table: SPECs that move logic into scripts (007/008/011)
carry **L4 + L7**, not AI evals — the scripts-first payoff. SPECs that change skill
*prompts* (004/005) carry **L2 + L3** because triggering and behavior are LLM-resolved
there.

## Definition of done (per phase)

- **Phase 1:** a fresh autopilot run produces a PR whose diff **collapses** `.process/`
  in the GitHub UI (artifacts persist in-repo and stay linked). Note: file-count is
  unchanged before splitting is used; PRSG-009 supplies the splitting path, while
  collapse still does not mean exclude.
- **Phase 2:** scaffolding a multi-slice spec produces a navigable spec-MOC; lints fail
  on orphan/stale links in CI **only for version-stamped specs** (legacy specs exempt).
- **Phase 3:** PRD interviews emit PR-sized SPECs; plan phase auto-approves under budget
  and the surface-count blocker is gone.
- **Phase 4:** a feature spec autopilot run emits N small PRs in dependency order, each
  linked from the spec-MOC; the router correctly classifies a destructive-migration
  fixture as atomic.
- **Phase 5:** the roadmap template no longer ships the exception keyword; an
  over-budget diff triggers re-slicing, not a rubber-stampable block.
- **Phase 6 (split-brain proof):** `bash tests/run-all.sh --layer 1` passes on BOTH
  (i) a freshly-scaffolded new-structure project AND (ii) a grandfathered legacy project
  (lints suppressed by marker-absence). `migrate-structure.sh --dry-run` prints the
  ordered pending migrations and mutates nothing; the relocate codemod hard-fails on a
  dirty tree and is idempotent (re-run = no-op).
- **Phase 7:** autopilot opens PRs only from validated reviewer-ready packets. Both
  single-PR and split-PR paths generate explicit titles and structured bodies before
  `gh pr create`; invalid, stale, placeholder-filled, or patronizing packets block
  with remediation evidence.
- **Every phase (gate):** all layers from the coverage table pass for each SPEC —
  CI-fast layers (L1/L4/L5) green in CI by default; Layer 7 replay (`--integration`) and
  Layer 8 parity are opt-in runs; and the AI evals (L2/L3, plus L6 where applicable) run
  developer-local (`claude -p`) and are recorded as passing **before** the SPEC merges.
  A skill change without its L2/L3 eval is **not done**, regardless of code completeness.

## Open migration decisions (your call — defaults applied in the catalog)

These are recorded with my recommended default; flag any you want changed:

1. **Tier-0 scope** — *default: eager index-backfill of all historical specs on
   upgrade* (one generated-zone write; roadmap-MOC complete immediately). Alternative:
   defer until each spec is reworked (lighter upgrade, incomplete index).
2. **Stamp timing** — *default: legacy specs stay exempt by marker-absence* (no
   frontmatter stamp during Tier-0; stamped only on Tier-2 thaw). Avoids ~77 file
   touches + join-key risk on mass writes.
3. **Multi-ID / gappy legacy entries** (`SPEC-016-017-workflow.md`, gaps) — *default:
   one index row per file, no special-casing*.
4. **Legacy non-SpecKit namespaces** (date-named design docs, JSON spikes) — *default:
   out of scope for v1; left as a separate legacy namespace*.
5. **Marker model** — *default: single integer high-water-mark* (reject the heavier
   Rails applied-ID-set unless partial-resume becomes a real need).
6. **Gate ↔ `.gitattributes`** — *default: keep the PRSG-001 hardcoded `.process/`
   glob in `is_excluded_generated()`* (the gate does not parse `.gitattributes`;
   accept the path living in two places).

## Risks carried from research

- Stale generated blocks (mitigate: phase-gate regen + Layer-1 lint + whole-zone regen).
- "Build green ≠ releasable" for destructive-migration / concurrency (mitigate:
  PRSG-007 detect-and-route + warn).
- **PRSG-002 lints unconditional** → first upgrade red-fails all legacy specs (mitigate:
  version-gate the lints from birth — built into PRSG-002 US2).
- **ID mis-join** (`SPEC-013A` vs `013a1`) → false orphan/stale hits (mitigate:
  exact-segment ID normalization in PRSG-002/003/011).
- Branch-by-abstraction deferred-contract lingering (mitigate: never split the contract
  slice from the slice that introduced the dual path).
- N× reviewer/CI workload (mitigate: PRSG-005/006 right-sizing keeps N small).
- Squash-only merge-conflict surfaces (marker file, central baselines) — mitigate:
  single-integer marker + in-band per-spec pragmas, per-spec atomic migration commits.
- Small PRs that are still hard to review because their generated titles/bodies are
  vague or patronizing (mitigate: PRSG-012 pre-create PR packet contract).

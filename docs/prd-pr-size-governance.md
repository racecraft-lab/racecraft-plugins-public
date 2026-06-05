# PRD: PR-Size Governance for speckit-pro

**Status**: Active — not yet implemented
**Source**: [`docs/ai/research/spec-pr-size-governance-research.md`](ai/research/spec-pr-size-governance-research.md) (research synthesis) + [`docs/ai/specs/pr-size-governance-technical-roadmap.md`](ai/specs/pr-size-governance-technical-roadmap.md) (locked roadmap)
**Created**: 2026-06-04
**Last updated**: 2026-06-04
**Target window**: Near-term. PRSG-001 is ready to scaffold; the headline win lands at PRSG-009.

---

## 1. Problem

> "Why are speckit-pro's pull requests impossible to review?"

speckit-pro turns a project's PRD and technical roadmap into a SPEC catalog, then
`speckit-autopilot` runs a 7-phase spec-driven workflow that opens **one pull
request per SPEC**. Because one roadmap SPEC is bound to one branch, one worktree,
and one PR, a large SPEC produces an unreviewable PR. The evidence is concrete:
Paddock PR #26 landed **83,898 additions across 532 files**; typical feature PRs run
~11k additions each, of which roughly **a third is auto-generated process exhaust**
(design concepts, workflow files, peer-review notes, retrospectives) that no human
needs to read line-by-line.

Every prior attempt to govern this has failed because it tried to *detect* oversized
PRs after the pipeline already produced them. The existing `reviewability-gate.sh` is
a literal no-op — its exception keyword ships as boilerplate in the roadmap template,
its only caller discards the exit code, and naive spec-splitting (tried in
focusengine #199) produced **zero smaller code PRs and more artifact files**, because
each new spec drags its own artifact set. The lesson: tightening detection without an
automated decomposition path just grows exception usage. The fix has to make the
small-PR path the **default, automatic output** of the pipeline — small by
construction, not by a gate.

## 2. Goals & Non-goals

### 2.1 Goals

- **Small PRs by construction.** A feature spec's autopilot run emits several small
  PRs in dependency order instead of one monolith — each within an **~800-LOC
  reviewable budget** (code + tests, artifacts collapsed). This is the headline,
  reviewer-felt outcome.
- **Remove the artifact tax from the review diff.** The ~32% of every feature PR that
  is auto-generated process exhaust is relocated and collapsed so it no longer competes
  for reviewer attention, while staying in-repo for provenance.
- **Make decomposition navigable, not memorized.** A Maps-of-Content (MOC) spine gives
  full `epic → spec → slice → PR → artifact` traceability so splitting work *adds*
  clarity instead of cognitive load.
- **Specs born the right size.** Upstream sizing heuristics (SPIDR/INVEST,
  vertical slices, a ~400 production-LOC per-slice ceiling) keep the number of PRs per
  spec small, so reviewer and CI workload stay bounded.
- **Existing projects upgrade cleanly.** A state-keyed migration brings projects with
  decades of legacy specs onto the new structure without a permanent split-brain repo
  and without red-failing CI on day one.
- **Prevention replaces the defeated gate.** The end-stage detective control is rebuilt
  *last*, as a backstop that triggers re-slicing — only after the automatic small path
  exists.

### 2.2 Non-goals (out of scope)

- **Naive spec-splitting as the primary lever.** Research-proven null-to-negative
  (multiplies the artifact tax 4.7×–8.7×). Demoted to shared-artifact "monster epics"
  for genuine #26-class cases only — handled in **PRSG-010**, not the default path.
- **`.gitattributes` `-diff` artifact exclusion (v1).** Deferred. `-diff` would drop
  artifact LOC from the PR's `+/−` count but render the files non-diffable; v1 uses
  `linguist-generated` (collapse-only, still loadable) — see **PRSG-001**.
- **Post-merge artifact relocation (v1).** Collapse-only ships first; bot-push
  relocation to `main` is **v2** — deferred from PRSG-001.
- **Releasability invariant-checking machinery (v1).** Destructive-migration and
  concurrency cutovers are **detect-and-routed** to an atomic PR with a warning, rather
  than asserting cross-table/runtime invariants in code — deferred in **PRSG-007**.
- **Hardening the gate first.** Doing so before the small path exists is the exact
  prior-art failure. The hatch is wired **last** (**PRSG-010**).

## 3. Acceptance Criteria

> One Feature per roadmap SPEC; criteria are derived from each SPEC's user stories and
> Definition of Done. The HOW lives in the roadmap — these state the observable WHAT.

### 3.1 Artifact relocation: tiering, `.process/`, collapse *(→ PRSG-001)*

- **AC-1.1**: scaffold-spec and autopilot write process exhaust (`design-concept`,
  `workflow.md`, `peer-review-*`, `verification-evidence`, `retrospective`) under
  `specs/<NNN>/.process/`; the CONTRACT set (`spec`/`plan`/`tasks`/`research`/
  `data-model`/`contracts`/`checklists`/`SPEC-MOC`) stays at the visible spec root.
- **AC-1.2**: a repo-root `.gitattributes` marks `specs/*/.process/**` as
  `linguist-generated=true` so a fresh autopilot run produces a PR whose `.process/`
  diff is collapsed in the GitHub UI yet remains loadable on demand.
- **AC-1.3**: a Layer-1 lint asserts the `.gitattributes` glob is scoped to `.process/`
  only and never matches a CONTRACT path.

### 3.2 MOC templates + scaffold-time skeleton + version-gated lints *(→ PRSG-002)*

- **AC-2.1**: roadmap-MOC and spec-MOC templates exist with the frontmatter join-key
  contract (`up`/`related`/`status`/`rank`/`spec_id`/`structureVersion`); scaffold-spec
  writes the spec-MOC skeleton with `up:` and the current `structureVersion` at
  creation, and only at the multi-slice squeeze point (single-slice spec → no MOC).
- **AC-2.2**: orphan and stale-link lints fire **only** for specs whose
  `structureVersion >= N`; a spec with no marker is grandfathered/exempt.
- **AC-2.3**: ID normalization joins doc IDs to dir IDs by lowercase + strip-`SPEC-` +
  exact-segment match (so `SPEC-013A` ≠ the `013a1` dir).

### 3.3 Generated index / PRs / backlinks + status integration *(→ PRSG-003)*

- **AC-3.1**: `generate-spec-index.sh` deterministically writes the GENERATED INDEX,
  GENERATED PRS (`slice → PR# → merged SHA`), and GENERATED BACKLINKS blocks between
  sentinel comments, always regenerating the whole sentinel-bounded zone.
- **AC-3.2**: `speckit-status` invokes the generator, and autopilot regenerates the
  zone as a phase-gate step at phase boundaries.

### 3.4 Roadmap-MOC home note from PRD + coach the two-zone structure *(→ PRSG-004)*

- **AC-4.1**: `speckit-prd` emits the roadmap-MOC home note (human-curated epics zone +
  GENERATED INDEX sentinels) alongside the PRD and technical roadmap.
- **AC-4.2**: `speckit-coach` teaches the curated/generated two-zone split and the
  "cap epics below ~10" guardrail.

### 3.5 Vertical-slice sizing heuristics in PRD/grill-me *(→ PRSG-005)*

- **AC-5.1**: `speckit-prd` and `grill-me` bake in SPIDR + INVEST + vertical-slicing
  guidance so the emitted SPEC catalog is thin, end-to-end slices by construction.

### 3.6 Plan-phase reviewability budget + gate threshold rework *(→ PRSG-006)*

- **AC-6.1**: the plan phase estimates per-slice footprint, auto-approves under budget,
  and surfaces to the human only when over.
- **AC-6.2**: the gate uses a ~400 production-LOC ceiling (code only), drops
  surface-count as a blocker, and replaces the single-keyword exception with typed
  exception classes (refactor/infra/upgrade).

### 3.7 Atomicity-test router (read-only classifier) *(→ PRSG-007)*

- **AC-7.1**: a `atomicity-route.sh` classifier emits a routing decision ∈ {split-PR,
  one-navigable-PR, branch-by-abstraction, single-atomic-PR, out-of-scope} from
  `tasks.md` shape → additive-vs-modify → flag-system probe → release cadence →
  consumer locality.
- **AC-7.2**: hard-atomic signatures (exported-symbol rename, global version pin,
  destructive migration, mutual-exclusion/auth/payment primitive, out-of-tree contract
  break) route to atomic; destructive-migration / concurrency signatures route to
  atomic **with a "CI-green ≠ releasable" warning**.

### 3.8 Layer-planner: tasks.md → ordered increments *(→ PRSG-008)*

- **AC-8.1**: `plan-layers.sh` parses user-story phases, `## Dependencies & Execution
  Order`, and `### Incremental Delivery` into ordered increments
  (Foundation → US1…USN → Polish) with per-increment file/test sets and a dependency
  DAG.

### 3.9 Multi-PR emission (post-implementation rewrite) *(→ PRSG-009)*

- **AC-9.1**: post-implementation emits N PRs in dependency order (incremental stack),
  each carrying its slice's tests and a per-slice generated PR body — replacing the
  single `gh pr create`.
- **AC-9.2**: each PR updates the spec-MOC GENERATED PRS table (`slice→PR#→SHA`) and
  handles squash-only restacking.
- **AC-9.3**: each slice PR's CI runs that slice's scoped tests; the full regression
  suite gates only the base/last merge, so a later slice's tests never block an earlier
  slice PR.

### 3.10 Harden the hatch + monster-epics *(→ PRSG-010)*

- **AC-10.1**: the roadmap template no longer ships the exception keyword; the diff-gate
  exit code is wired as a backstop that triggers re-slicing (back through
  PRSG-007/008/009), not blind blocking.
- **AC-10.2**: an epic can decompose into child specs that share one design-concept and
  retrospective, with `speckit-status` rolling children up — reserved for monsters that
  upstream sizing cannot slice thin.

### 3.11 Retro-migration: version marker + state-keyed backfill/relocate *(→ PRSG-011)*

- **AC-11.1**: `migrate-structure.sh` runs two-phase (dry-run prints the ordered pending
  migrations and mutates nothing; apply performs idempotent, self-guarding Tier-1 repo
  edits and writes the new `.specify/structure-version.json` marker), hard-failing on a
  dirty tree.
- **AC-11.2**: Tier-0 reuses `generate-spec-index.sh` to backfill one roadmap-MOC index
  row per historical spec with **no file moves and no frontmatter stamp** (legacy specs
  stay exempt by marker-absence).
- **AC-11.3**: Tier-2 `relocate-process-artifacts.sh` `git mv`s the process allow-list
  into `.process/` for specs that have a `specs/<NNN>/` dir, regenerates links/index,
  and stamps `structureVersion` in one atomic commit — with a forced backup, dirty-tree
  guard, and real dry-run; in-flight specs are skipped in every tier.

## 4. Migration Path (phased — one phase per SPEC)

- **Phase 1 (PRSG-001) — Artifact relocation**: ships first; cheap, orthogonal
  precondition that removes the artifact tax from the diff before anything is split.
- **Phase 2 (PRSG-002 → 003 → 004) — MOC spine**: the navigation/traceability backbone
  that makes relocation safe (hidden files stay linked) and decomposition navigable.
  Depends on the `.process/` path from Phase 1.
- **Phase 3 (PRSG-005, 006) — Upstream sizing**: specs born PR-sized; preventive plan
  budget; gate metrics fixed. Parallelizable with Phase 2.
- **Phase 4 (PRSG-007 → 008 → 009) — Split-PR engine**: the core change — classify,
  plan increments, emit N PRs. **The headline reviewable-size drop lands here.**
- **Phase 5 (PRSG-010) — Harden the hatch**: only now that the small path exists is it
  safe to make the backstop real; adds monster-epic escalation.
- **Phase 6 (PRSG-011) — Retro-migration**: state-keyed backfill/relocate for existing
  projects; needs only PRSG-001/002/003, so it can land in parallel with Phases 3–5.

## 5. Constraints

- **Squash-only merge** (both reference repos: `squash:true, merge:false,
  rebase:false`). Split PRs must be **independent slices off `main`**, not a naive stack
  squash would break.
- **Codex parity is mandatory.** Every mirrored `skills/<name>/SKILL.md` change must be
  mirrored under `codex-skills/`, keeping Layer-1 `validate-codex-skills.sh` and the
  Layer-8 parity fixtures green.
- **Scripts-first.** Deterministic logic ships as `bash`+`jq` scripts (the router,
  layer-planner, migration runner, codemod), not LLM reasoning — for determinism,
  token savings, and a smaller AI-eval surface.
- **Tests AND evals are non-negotiable per change.** Skill behavior → Layer-3;
  trigger/description → Layer-2; deterministic logic → Layer-4 determinism fixture; new
  agent → Layer-5/7 (+6 if it makes a model/effort choice); mirrored skill → Layer-1/8.
- **Reviewability budget.** ~800-LOC whole-PR reviewable budget (code + tests, artifacts
  collapsed) is the headline target; ~400 production-LOC per slice is the supporting
  per-slice ceiling.
- **No new runtime dependency.** Plain `bash` + `jq`, per CLAUDE.md.

## 6. Open Questions

> Recorded with recommended defaults (already applied in the roadmap catalog). None
> block PRD acceptance; each is resolved in the PRSG-011 grill-me / clarify pass.

- **OQ-1 (PRSG-011):** Tier-0 scope — *recommend eager index-backfill of all historical
  specs on upgrade* (one generated-zone write) over deferring until each spec is
  reworked.
- **OQ-2 (PRSG-011):** Stamp timing — *recommend legacy specs stay exempt by
  marker-absence* (no frontmatter stamp during Tier-0; stamp only on Tier-2 thaw).
- **OQ-3 (PRSG-011):** Multi-ID / gappy legacy entries — *recommend one index row per
  file, no special-casing*.
- **OQ-4 (PRSG-011):** Legacy non-SpecKit namespaces (date-named design docs, JSON
  spikes) — *recommend out of scope for v1*.
- **OQ-5 (PRSG-011):** Marker model — *recommend a single integer high-water-mark* over
  a heavier applied-ID set.
- **OQ-6 (PRSG-001 / PRSG-011):** Gate ↔ `.gitattributes` — *recommend keeping the
  hardcoded `.process/` glob in the gate* (it does not parse `.gitattributes`; accept
  the path living in two places).

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Artifact relocation: tiering, `.process/`, collapse | AC-1.* | PRSG-001 | — | P1 |
| MOC templates + scaffold-time skeleton + version-gated lints | AC-2.* | PRSG-002 | PRSG-001 | P1 |
| Generated index / PRs / backlinks + status integration | AC-3.* | PRSG-003 | PRSG-002 | P1 |
| Roadmap-MOC home note from PRD + coach two-zone structure | AC-4.* | PRSG-004 | PRSG-002, PRSG-003 | P2 |
| Vertical-slice sizing heuristics in PRD/grill-me | AC-5.* | PRSG-005 | — | P1 |
| Plan-phase reviewability budget + gate threshold rework | AC-6.* | PRSG-006 | PRSG-001 | P1 |
| Atomicity-test router (read-only classifier) | AC-7.* | PRSG-007 | PRSG-006 | P1 |
| Layer-planner: tasks.md → ordered increments | AC-8.* | PRSG-008 | PRSG-007 | P1 |
| Multi-PR emission (post-implementation rewrite) | AC-9.* | PRSG-009 | PRSG-008, PRSG-003, PRSG-001 | P1 |
| Harden the hatch + monster-epics | AC-10.* | PRSG-010 | Phases 1–4 | P2 |
| Retro-migration: version marker + state-keyed backfill/relocate | AC-11.* | PRSG-011 | PRSG-001, PRSG-002, PRSG-003 | P2 |

## 8. Success Criteria

1. A feature spec's autopilot run emits **N small PRs in dependency order**, each within
   the **~800-LOC reviewable budget** (code + tests, artifacts collapsed), with each PR
   linked from the spec-MOC (AC-9.*).
2. The auto-generated artifact tax no longer appears in the review diff — `.process/` is
   collapsed in the GitHub UI yet remains in-repo and linked (AC-1.*).
3. The full `epic → spec → slice → PR → artifact` tree is navigable from a single
   roadmap-MOC home note, with generated index/PRs/backlinks that regenerate rather than
   go stale (AC-3.*, AC-4.*).
4. The router correctly classifies a destructive-migration fixture as atomic and warns
   that CI-green ≠ releasable (AC-7.*).
5. `bash tests/run-all.sh --layer 1` passes on **both** a freshly-scaffolded
   new-structure project and a grandfathered legacy project (lints suppressed by
   marker-absence); the migration dry-run mutates nothing and the relocate codemod is
   idempotent (AC-11.*).
6. Every SPEC merges with its required test layers passing (CI-fast in CI; AI evals
   recorded developer-local before merge), per the roadmap's coverage table.

## 9. References

- **Technical roadmap (locked):** [`docs/ai/specs/pr-size-governance-technical-roadmap.md`](ai/specs/pr-size-governance-technical-roadmap.md)
- **Research synthesis & decision brief:** [`docs/ai/research/spec-pr-size-governance-research.md`](ai/research/spec-pr-size-governance-research.md)
- **Project standards:** [`CLAUDE.md`](../CLAUDE.md)
- **Constitution:** `.specify/memory/constitution.md` *(if present in the target project)*

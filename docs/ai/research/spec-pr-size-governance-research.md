# Spec & PR Size Governance — Research Synthesis & Decision Brief

> Status: **research complete, decisions open**. Working document (not a spec).
> Produced from two multi-agent research workflows on 2026-06-03.
> Problem owner: Fredrick Gabelmann. Plugin: `speckit-pro`.

## Problem

`speckit-pro` binds **one roadmap SPEC → one branch/worktree → one PR**. Big SPECs
therefore produce unreviewable PRs. Evidence (racecraft-lab/Paddock,
racecraft-lab/focusengine):

- Paddock #26 (SPEC-008): **83,898 additions / 532 files** — 46% production code
  (38,793 LOC / 279 files), 28% tests, 14% process artifacts, 9% seed/config.
- Typical feature PRs (#57, #60): ~11k additions each, composed **~30% production
  code / ~37% tests / ~32% auto-generated process artifacts**.
- Production-code median across Paddock feature PRs ≈ **1,669 LOC** (floor 932) —
  still over an 800-LOC reviewable budget even after artifacts are removed.

## Why all prior art failed (forensic findings)

1. **The reviewability gate is a literal no-op.** `reviewability-gate.sh` line 102
   flips `block → exception` whenever it greps an exception keyword in *any* `.md`,
   so line 138's `exit 1` never fires. The exception keyword **ships as boilerplate
   in the roadmap template** (`Budget result: …split exception`) — every roadmap
   auto-downgrades to `exception`. The only programmatic caller
   (`generate-pr-body.sh`) runs it under `set +e … 2>/dev/null` and **discards the
   exit code**. Commit #95 (latest governance change) hardened the bypass, not the
   gate. → It is a detective control that detects nothing and is wired to do nothing.

2. **Spec-splitting (naïve "Lever C") is a trap.** focusengine's 31→45 spec-split
   (#199) produced **zero smaller code PRs and +9 artifact files on day one**.
   Paddock spec-splits multiplied the artifact tax **4.7×–8.7×** (SPEC-009 → 9
   children carried 28,928 artifact LOC). Each spec drags its own
   design-concept + workflow + retrospective, so splitting specs makes the
   aggregate worse. **Null-to-negative result.**

3. **The 1-SPEC→1-PR binding is structural-by-absence.** `scaffold-spec` creates
   exactly one branch/worktree; every phase commits onto it; no code path can emit
   a second PR from one SPEC. "Split" today means a human re-authoring the roadmap
   by hand — which never happens voluntarily.

## Design principle (hard constraint)

Any option that tightens **detection** without an **automated decomposition path**
just increases exception usage. The winner must make the **small-PR path the
default / cheap / automatic** output of the pipeline, be effectively
non-bypassable (because nothing oversized is *produced* to bypass), address **both**
the artifact tax **and** code decomposition, and survive **squash-only** merge
(both repos: `squash:true, merge:false, rebase:false, delete_branch_on_merge:true`).

## Scored option set

| ID | Option | Lever | Score | Verdict |
|----|--------|-------|-------|---------|
| **O1** | Relocate process artifacts out of the diff (`.process/` + collapse/relocate) | A | 72 | **Hard precondition**, orthogonal, cheap (S) |
| **O2** | Independent slices: 1 PR per `tasks.md` dependency layer, off `main` (squash-immune) | split-PR | 80 | **Preferred code-decomposition lever** (M/L) |
| **O4** | Upstream vertical-slice sizing (SPIDR/INVEST in prd/grill-me; ~400 prod-LOC ceiling; kill surface-count blocker) | scoping | 78 | Attacks root cause cheaply (M) |
| **O5** | Epic → child specs that **share** artifacts | split-spec (rescued) | 68 | **Monsters only** (#26-class) (L) |
| O3 | gh-stack dependent stacks for genuinely sequential edges | split-PR | 58 | Fallback only; tool post-cutoff, maturity risk |
| **O6** | **Hybrid = O1 + O2 + O4** | hybrid | **91** | **Recommended spine** |
| O7 | Harden the gate / tighten thresholds | — | 18 | **Rejected** (the named anti-pattern) |

Combination logic: **O1 is orthogonal and a hard precondition** for any
decomposition (else any split still ships 30%+ artifacts). The two code-decomposition
flavors are **alternatives**: **O2 (split-PR) is preferred over O5 (split-spec)**
because it keeps one artifact set per SPEC. **O4** is the preventive front end.
**O3** only for genuinely dependent edges. → **O6 = O1 + O2 + O4**, sequenced
relocate-first, harden-the-hatch-last; **O5** is the monster escalation.

## The MOC layer (second workflow) — REFINED verdict

The owner's hypothesis (Maps of Content unify the decomposition-navigation and
artifact-provenance concerns) is **confirmed in kind but refined in scope**:

- **CONFIRM:** one MOC structure is the shared navigation + traceability backbone.
  roadmap-as-home-note + per-spec leaf MOCs + up/down/lateral links give full
  `epic → spec → slice → PR → artifact` traceability with **zero runtime engine**,
  and it is **squash-safe** because it lives in tracked files, not commit boundaries
  (which squash discards). ADR/RFC convention is independent proof.

- **REFINE (the overclaim):** the MOC is the **enabling layer**, not the whole
  solution. It solves the **find/navigate/trace** half of both concerns. It does
  **not** exclude diffs (that is git mechanics) nor right-size specs (that is the
  decomposition lever). Honest framing: **relocation (A) is only *safe* because the
  MOC preserves traceability to hidden files; decomposition is only *navigable*
  because the MOC externalizes the tree so the user navigates instead of memorizing.**

### Three complementary layers under one structure

1. **Right-sizing** (O4 + O2, with O5 for monsters) — makes the code small.
2. **Artifact diff-management** (O1) — keystone is *tiering*:
   - **CONTRACT** (always visible; never mark generated): `spec.md`, `plan.md`,
     `tasks.md`, `research.md`, `data-model.md`, `contracts/**`, `checklists/**`,
     `SPEC-MOC.md`.
   - **EXHAUST** (~32% noise; consolidate under `specs/<NNN>/.process/`):
     `design-concept.md`, `workflow.md`, `peer-review-*.md`,
     `verification-evidence.md`, `retrospective.md`.
   - **COLLAPSE** routine exhaust via repo-root `.gitattributes`
     (`specs/*/.process/** linguist-generated=true`) — diff hidden behind a
     "Load diff" banner. **Caveat: collapse ≠ exclusion** — files still appear in
     the Files-changed list and still count toward GitHub's 300-file render cap.
   - **TRUE EXCLUDE** bulky exhaust via post-merge `chore(sdd): archive SPEC-NNN
     artifacts [skip ci]` bot-push to `main` (reuses the marketplace-sync pattern).
     Recommended **collapse-only v1, relocation v2**.
3. **MOC navigation/traceability spine** (the enabling layer):
   - **roadmap-MOC** (`docs/ai/specs/<NAME>-roadmap-MOC.md`, or fold into the
     existing technical-roadmap which is ~80% there): two strictly-separated zones —
     a **human-curated** epic section (the *WHY*) and a **machine-generated** index
     table between `<!-- BEGIN/END GENERATED INDEX -->` sentinels (`speckit-status`
     is the generator).
   - **spec-MOC** (`specs/<NNN>/SPEC-MOC.md`) — minted **only at the multi-slice
     squeeze point**, never one-per-spec. Frontmatter `up:`/`related:`/`status:`/
     `rank:` is the join-key contract; the parent's generated index reads exactly
     those fields.
   - **Link topology:** DOWN = relative `[](links)` (render on github.com); UP =
     `up:` frontmatter; LATERAL = `related:` (genuine deps only); BACK =
     **bash-generated** between sentinels (plain markdown has no backlink engine).
     Join key = existing `SPEC-NNN` + `006a/006b` suffix scheme (NOT invented
     decimals). PR→spec survives squash via the generated `PR# → merged SHA` table.
   - **Cognitive-load rule (the most important build rule):** strict machine/human
     split — bash emits the *blind skeleton* (links, tables, backlinks, `up:`);
     the human writes *only* the few-sentence *WHY*. If the human must hand-curate
     everything, load **moves** rather than **shrinks** and the system gets
     abandoned (documented Zettelkasten failure mode).

## Pipeline mapping (mostly additive)

- **speckit-prd** — also emit the roadmap-MOC home note (curated epics + generated
  index sentinels) when it writes the PRD + technical-roadmap.
- **speckit-coach** — teach the two-zone structure + "cap epics below ~10" guardrail.
- **speckit-scaffold-spec** — birth the `SPEC-MOC.md` skeleton with `up:`; place
  exhaust under `.process/`; commit the repo-root `.gitattributes` if absent;
  mint a SPEC-MOC only when the roadmap entry decomposes into multiple slices.
- **speckit-autopilot** — point exhaust commits at `.process/`; add a
  regenerate-index/backlinks **phase-gate** step (the #1 staleness mitigation);
  at PR creation update the generated `PR#→SHA` block; optionally run post-merge
  relocation for bulky exhaust (v2).
- **speckit-status** — IS the generated-index generator (shared
  `scripts/generate-spec-index.sh`).
- **Tests:** Layer-1 lint (stale-index: MOC link → nonexistent file; orphan: `.md`
  lacking valid `up:`; `.gitattributes` missing `.process` glob); Layer-4 determinism
  test for the generator scripts.

## Top risks

- **Stale index** (#1) — no live engine; generated blocks silently lie. → phase-gate
  regeneration + Layer-1 lint.
- **Overclaiming `.gitattributes` "excludes"** — it *collapses*; file-count cap
  (which the 279-file PR already busts) needs right-sizing or relocation.
- **Marking the contract generated** — scope the glob strictly to `.process/**`.
- **MOC sprawl / over-decomposition** — mint at the squeeze point only; right-size
  to PR-sized, not atom-sized.
- **Curation becomes a job** — strict machine/human split.
- **Wikilink/Obsidian-runtime trap** — every nav feature needs a static,
  bash-generated relative-link `.md` equivalent (the vault is `[[wikilink]]`/Dataview
  heavy; those render as nothing in a PR diff).

## Open decisions (human's to make)

1. **Accept the flip?** Code decomposition via split-PR (O2), spec-splitting demoted
   to shared-artifact epics (O5) for monsters only.
2. **Slice = sub-spec or sub-PR?** (biggest structural fork) — sub-spec siblings
   (own branch/PR, matches 006a/006b) vs sub-PRs off one spec branch.
3. **Artifact v1 scope:** collapse-only (`.gitattributes`, zero new infra) vs
   collapse + post-merge relocate.
4. **Tier the design-concept** (and `uat-runbook`): exhaust (collapse) or contract
   (stay visible)?
5. **WHY annotations:** mandatory (guarantee benefit) or advisory (avoid abandonment)?
6. **Migration:** retrofit existing specs to `.process/` + backfill MOCs, or
   new-specs-only?

## O2 red-team verdict & decision rule (workflow 3)

An adversarial red-team (6 change-class skeptics + branch-by-abstraction research +
synthesis) stress-tested **O2 as the default** before adoption. Verdict:
**confirm-with-carveouts — O2-as-default survives.** Most "irreducible" cases are
not O2 failures; they are inputs the feature-spec pipeline never produces a
multi-user-story `tasks.md` for (pure renames, dep/runtime bumps, standalone
destructive migrations) → **out of scope**, not "O2 broke."

### The atomicity test (autopilot routing rule)

1. **Sliceable shape?** Does `tasks.md` decompose into user-story phases (US1/US2…),
   each with an Independent Test + "independently functional" checkpoint? **No** →
   one-navigable-PR (if mechanical/atomic) or **out-of-scope** (not a feature spec).
2. **Additive / wire-last?** Is every increment purely additive / dead-but-compiled,
   existing entry points unchanged until the final slice? **Yes** → **SPLIT-PR
   (default)** — no flag, no cadence check needed.
3. **Coexistence test?** Can OLD + NEW both live in one build that passes its own
   tests, all consumers in-tree? **Yes** → **branch-by-abstraction**
   (expand → migrate callers → contract last; force the contract slice to complete).
4. **Darkening available?** Flag system present, OR release-cadence app with no
   out-of-tree consumer? **Yes** → ship the cutover as one flagged/dark slice.
5. **Hard-atomic override → single atomic PR:** exported-symbol rename with
   cross-module compile coupling; one global version/runtime pin (dep/framework
   cutover); in-place destructive/backfill migration (rewrites rows / flips
   CHECK/enum); mutual-exclusion / auth / payment primitive where dual-running is the
   hazard; breaking change to a versioned / out-of-tree consumer surface.
6. **Releasability ≠ CI-green (the critical carve-out).** For per-table destructive
   migrations and dual-run concurrency cutovers, `build+test green` passes while
   `main` is corrupt/unsafe on deploy. The releasability check MUST assert the
   cross-table / cross-tree / runtime invariant — not just that the build is green.
   If the invariant can't be asserted in an intermediate slice, the cut is mid-atom:
   merge it into the cutover PR.
7. **Mechanical-tier exemption:** large + mechanical + atomic diffs (renames,
   codemods, dep bumps) → one-navigable-PR. Correct low-cognitive-load form, NOT an
   O2 failure.

### Per-class routing

| Change class | Route |
|--------------|-------|
| Greenfield/additive feature, user-story decomposition (model→logic→UI, wired last) | **SPLIT-PR (default)** |
| In-place modification, all consumers in-tree | **branch-by-abstraction** |
| Breaking change to versioned / out-of-tree consumer surface | fallback (v2-beside-v1, or atomic PR + consumer plan) |
| In-place destructive/backfill migration | fallback (atomic PR + lockstep code) |
| Security/auth/concurrency mutual-exclusion cutover | fallback (flag-gated, or atomic PR if no flag) |
| Cross-cutting exported-symbol rename (100s of call sites) | **out-of-scope** (one navigable PR) |
| Dep/framework/runtime/platform cutover (one global pin) | **out-of-scope** (atomic flip; prep/cleanup may slice) |
| Redesign replacing an existing visible screen on a no-flag release-cadence app | fallback (one swap PR + release-hold, or add runtime toggle in Foundation) |

### Detection order (cheapest/most-authoritative first)

1. `tasks.md` shape (user-story phases?) → 2. additive-vs-modify per increment
(grep diff for existing-symbol edits / migration `UPDATE/DELETE/DROP/CHECK` vs net-new
`CREATE TABLE`/nullable `ADD COLUMN`) → 3. flag-system probe (`feature-flags*`,
`FEATURE_*`, OpenFeature) → 4. release cadence (Sparkle/appcast/Info.plist/App-Store =
release-cadence; Vercel/preview = continuous) → 5. consumer locality for API changes
(versioned `/api/vN` or MCP process ⇒ treat as out-of-tree, route conservatively).

### Highest-impact residual risk

A naive O2 gate that equates "build+test green" with "releasable" actively
**manufactures a deploy-corruption failure mode the single big PR did not have**
(mixed-schema `main`; two live admission controllers). Either upgrade the
releasability check to assert invariants, or **detect-and-route** those signatures to
atomic + warn the human. (Recommended v1: detect-and-route; defer invariant machinery.)

> Note: the red-team could not reach FocusEngine via `gh` (a casing/GraphQL error);
> however the orchestrator inspected it directly earlier — it IS accessible, is a Swift
> macOS app with small no-flag PRs, and #195 is the TS→Swift cutover — so the no-flag /
> release-cadence branch is empirically grounded, not just asserted.

## Provenance

- Workflow 1 (PR-size forensics + industry): 9 agents, ~882k tokens.
- Workflow 2 (MOC + provenance): 4 agents, ~344k tokens.
- Workflow 3 (O2 red-team): 8 agents, ~488k tokens.
- Raw outputs: `tasks/wdejrrz8x.output`, `tasks/w8l880431.output`,
  `tasks/wt50r1ws3.output` (session tmp).

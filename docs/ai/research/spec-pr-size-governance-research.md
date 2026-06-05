# Spec and PR Size Governance: Research and Decision Brief

> Status: research complete. The decisions in this brief are now locked in the
> [roadmap](../specs/pr-size-governance-technical-roadmap.md) and
> [PRD](../../prd-pr-size-governance.md).
> Built from three multi-agent research runs on 2026-06-03. Plugin: `speckit-pro`.

## The problem

speckit-pro ties each roadmap SPEC to one branch, one worktree, and one pull
request. When a SPEC is large, the pull request is large, and nobody can review
it. Two real repositories show the scale, Paddock and focusengine:

- Paddock #26 (SPEC-008) shipped 83,898 added lines across 532 files. Production
  code was 46% of that (38,793 lines in 279 files). Tests were 28%, process
  artifacts 14%, seed and config 9%.
- Ordinary feature PRs such as #57 and #60 run roughly 11,000 added lines each.
  About 30% is production code, 37% is tests, and 32% is auto-generated process
  artifacts.
- Strip the artifacts and the median feature PR still carries about 1,669 lines
  of production code, with the leanest at 932. That alone overshoots a sane
  review budget of 800 lines.

So a third of every PR is paperwork no human reads line by line, and the code
that remains is still too big to review in one sitting.

## Why nothing we tried before worked

Three findings, each pulled from the actual code and commit history.

1. **The reviewability gate is inert.** `reviewability-gate.sh` rewrites its own
   verdict from "block" to "exception" the instant it greps an exception keyword
   in any `.md` file (line 102), so the `exit 1` on line 138 never fires. That
   keyword ships as boilerplate inside the roadmap template (the
   `Budget result: ...split exception` line), which means every roadmap quietly
   downgrades itself. The one caller that touches the gate,
   `generate-pr-body.sh`, runs it with errors muted and then discards the exit
   code. Commit #95, the most recent governance change, reinforced the bypass
   rather than the check. The net effect is a guard that catches nothing and is
   wired to act on nothing.

2. **Splitting specs backfires.** When focusengine cut 31 specs into 45 (#199),
   it produced zero smaller code PRs and added 9 artifact files on day one.
   Paddock's spec-splits multiplied the artifact tax somewhere between 4.7x and
   8.7x; SPEC-009 fanned into 9 children that together hauled 28,928 lines of
   artifacts. Every spec drags its own design concept, workflow file, and
   retrospective, so chopping one spec into many simply multiplies the
   bookkeeping. The outcome was null at best and negative in practice.

3. **The one-SPEC-one-PR rule is baked in by omission.** `scaffold-spec` builds
   exactly one branch and worktree. Every phase commits onto it. No code path can
   emit a second PR from a single SPEC. "Splitting" today means a person rewriting
   the roadmap by hand, which nobody volunteers to do.

## The rule any fix has to obey

Tighten detection without giving people an automatic way to decompose, and you
just funnel them toward the exception path. A real fix therefore has to clear
four bars at once. It makes the small PR the default output, the cheap path, the
thing that happens without anyone asking. It resists bypass, because nothing
oversized gets produced to bypass in the first place. It tackles both halves of
the mess, the artifact tax and the code itself. And it survives squash-only
merging, which both repos enforce (squash on, merge commits off, rebase off,
branches deleted on merge).

## What we scored

| ID | Option | Lever | Score | Verdict |
|----|--------|-------|-------|---------|
| **O1** | Move process artifacts out of the diff (`.process/` plus collapse or relocate) | relocate | 72 | Hard precondition. Stands apart, cheap. |
| **O2** | Independent slices: one PR per `tasks.md` dependency layer, branched off `main` so squash cannot break it | split-PR | 80 | Preferred way to decompose code. |
| **O4** | Size specs right upstream (SPIDR and INVEST in prd and grill-me; ~400 production-LOC ceiling; drop the surface-count blocker) | scoping | 78 | Attacks the root cause cheaply. |
| **O5** | Epic feeding child specs that share one artifact set | split-spec | 68 | Monsters only, the #26 class. |
| O3 | gh-stack dependent stacks for genuinely sequential edges | split-PR | 58 | Fallback only. The tool is new and unproven. |
| **O6** | Bundle of O1 plus O2 plus O4 | hybrid | **91** | Recommended spine. |
| O7 | Harden the gate, tighten the thresholds | none | 18 | Rejected. This is the anti-pattern we already have. |

O1 sits on its own and goes first, because any split that skips it still ships
more than 30% artifacts. The two ways to cut code are alternatives, not
companions, and split-PR (O2) wins over split-spec (O5) because it keeps a single
artifact set per spec. O4 is the preventive front end. O3 earns a place only on
edges that are truly sequential. That leaves the recommended bundle: O1 plus O2
plus O4, sequenced relocate-first and harden-last, with O5 held back for the rare
monster.

## Maps of Content: confirmed, with one correction

Maps of Content, the hand-curated index notes from the
personal-knowledge-management world, promise to fold navigation and provenance
into one structure. The promise holds, with one narrowing.

What holds up: one MOC structure can serve as the shared backbone for both
navigation and traceability. A roadmap acting as a home note, plus a small map
note per spec, plus links that point up, down, and sideways, yields the whole
chain from epic to spec to slice to PR to artifact, with no runtime engine. It
survives squashing because it lives in tracked files rather than commit
boundaries, which squash discards. The ADR and RFC conventions are independent
proof that the pattern works.

The correction: a MOC enables the fix; it is not the fix. It solves finding,
navigating, and tracing. It does not hide diffs, which is git's job, and it does
not make specs smaller, which is the decomposition lever's job. Put bluntly,
relocating artifacts is only safe because the MOC keeps the hidden files linked,
and splitting work is only navigable because the MOC holds the tree so people
read a map instead of memorizing one.

### Three layers, one structure

1. **Right-sizing** (O4 and O2, with O5 for monsters) keeps the code small.
2. **Artifact management** (O1) works by sorting files into three tiers:
   - **Contract** files stay visible and are never marked generated: `spec.md`,
     `plan.md`, `tasks.md`, `research.md`, `data-model.md`, everything under
     `contracts/` and `checklists/`, and the spec map note `SPEC-MOC.md`.
   - **Exhaust** files are the ~32% of noise, and they move under
     `specs/<NNN>/.process/`: `design-concept.md`, `workflow.md`, the
     `peer-review-*.md` notes, `verification-evidence.md`, `retrospective.md`.
   - **Collapse** the routine exhaust with a repo-root `.gitattributes` rule
     (`specs/*/.process/** linguist-generated=true`). GitHub then tucks the diff
     behind a "Load diff" banner. One caveat that matters: collapse is not
     exclusion. The files still appear in the changed-files list and still count
     against GitHub's 300-file render limit.
   - **Truly exclude** only the bulky exhaust, later, through a post-merge bot
     push that archives it (the same trick the marketplace-sync workflow already
     uses). Recommendation: collapse only for v1, relocation in v2.
3. **The MOC navigation spine** is the enabling layer:
   - The **roadmap-MOC** (`docs/ai/specs/<NAME>-roadmap-MOC.md`, or folded into
     the existing technical roadmap, which is already about 80% there) holds two
     strictly separated zones: a human-curated epic section that carries the why,
     and a machine-generated index table between
     `<!-- BEGIN/END GENERATED INDEX -->` sentinels. `speckit-status` is the
     generator.
   - The **spec-MOC** (`specs/<NNN>/SPEC-MOC.md`) is minted only when a spec
     actually breaks into multiple slices, never one per spec. Its frontmatter
     (`up`, `related`, `status`, `rank`) is the contract the parent's generated
     index reads.
   - **Link directions.** Down uses plain relative links that render on
     github.com. Up lives in frontmatter. Sideways uses `related`, and only for
     genuine dependencies. Backlinks are generated by bash between sentinels,
     since plain markdown has no backlink engine. The join key is the existing
     `SPEC-NNN` scheme with the `006a/006b` suffixes, not invented decimals. The
     PR-to-spec link survives squashing through a generated table that maps PR
     number to merged commit SHA.
   - **The single most important build rule** is the split between machine work
     and human work. Bash writes the blind skeleton: links, tables, backlinks,
     the `up` pointer. The human writes only the few sentences of why. Make a
     person hand-maintain everything and the labor merely relocates instead of
     shrinking, and the system gets abandoned. That is the documented way
     Zettelkasten setups die.

## How this lands in the pipeline (mostly additive)

- **speckit-prd** also emits the roadmap-MOC home note (curated epics plus
  generated-index sentinels) when it writes the PRD and technical roadmap.
- **speckit-coach** teaches the two-zone structure and the "keep epics under
  about 10" guardrail.
- **speckit-scaffold-spec** births the `SPEC-MOC.md` skeleton with `up:` set,
  places exhaust under `.process/`, commits the repo-root `.gitattributes` if it
  is missing, and mints a spec-MOC only when the roadmap entry breaks into
  multiple slices.
- **speckit-autopilot** points exhaust commits at `.process/`, regenerates the
  index and backlinks as a phase-gate step (the top staleness mitigation),
  updates the PR-to-SHA block when it opens a PR, and optionally runs post-merge
  relocation for bulky exhaust in v2.
- **speckit-status** is the index generator, sharing
  `scripts/generate-spec-index.sh`.
- **Tests.** Layer-1 lints catch a stale index (a MOC link pointing at a missing
  file), an orphan (a `.md` with no valid `up:`), and a `.gitattributes` that
  forgets the `.process` glob. A Layer-4 test pins the generator scripts to
  deterministic output.

## The biggest risks

- **A stale index** is the headline risk. There is no live engine, so a generated
  block can silently lie. Mitigate with phase-gate regeneration and a Layer-1
  lint.
- **Overselling what `.gitattributes` does.** It collapses; it does not exclude.
  The file-count cap, which the 279-file PR already busts, needs right-sizing or
  relocation to actually move.
- **Marking a contract file as generated.** Scope the glob strictly to
  `.process/**` so it can never touch a contract path.
- **MOC sprawl from over-decomposition.** Mint at the squeeze point only, and
  size to PR-sized rather than atom-sized.
- **Curation turning into a second job.** Hold the machine-versus-human line.
- **The wikilink trap.** Every navigation feature needs a static,
  bash-generated, relative-link equivalent. The vault leans on `[[wikilinks]]`
  and Dataview, and both render as nothing in a PR diff.

## Decisions this brief raised (now resolved)

These were the open forks at the time of research. All six are settled in the
roadmap's locked-decisions table; the resolution is noted here for the record.

1. **Accept the flip to split-PR?** Yes. Code decomposition runs through split-PR
   (O2); spec-splitting drops to shared-artifact epics (O5) for monsters only.
2. **Slice as a sub-spec or a sub-PR?** Sub-PRs within one spec: one SPEC ID, one
   `tasks.md`, one artifact set, N PRs. The `006a/006b` sub-spec form is reserved
   for monster epics.
3. **Artifact scope in v1?** Collapse only via `.gitattributes`, zero new
   infrastructure. Post-merge relocation waits for v2.
4. **Tier the design concept and the UAT runbook as exhaust or contract?**
   Exhaust, collapsed under `.process/`.
5. **Why annotations mandatory or advisory?** Advisory in v1, to avoid the
   abandonment failure mode.
6. **Migrate existing specs or ship new-specs-only?** Tiered retro-migration
   (PRSG-011): repo-level edits eagerly, navigation backfill for completed specs,
   and an on-demand relocate codemod for the specs that have a `specs/<NNN>/`
   directory. Legacy specs are grandfathered by the absence of a version marker.

## Stress-testing split-PR as the default

Split-PR as the default was stress-tested against every change class before
adoption, including a branch-by-abstraction analysis. It holds, with carve-outs.
Most cases that look irreducible are not split-PR failures at all. They are
inputs the feature-spec pipeline never produces a multi-user-story `tasks.md` for
in the first place: pure renames, dependency or runtime bumps, standalone
destructive migrations. Those fall out of scope rather than breaking the
approach.

### The atomicity test (the autopilot routing rule)

1. **Is the shape sliceable?** Does `tasks.md` break into user-story phases (US1,
   US2, and so on), each with an independent test and an "independently
   functional" checkpoint? If no, route to one-navigable-PR when the work is
   mechanical or atomic, or out-of-scope when it is not a feature spec at all.
2. **Is it additive and wired last?** Is every increment purely additive or
   dead-but-compiled, with existing entry points untouched until the final slice?
   If yes, split-PR is the default. No flag and no cadence check needed.
3. **Can old and new coexist?** Can both live in one build that passes its own
   tests, with every consumer in the tree? If yes, use branch-by-abstraction:
   expand, migrate the callers, then contract last, and force the contract slice
   to complete.
4. **Is darkening available?** Is there a flag system, or a release-cadence app
   with no out-of-tree consumer? If yes, ship the cutover as one flagged or dark
   slice.
5. **Hard-atomic override, ship one atomic PR.** This covers an exported-symbol
   rename with cross-module compile coupling, a single global version or runtime
   pin (a dependency or framework cutover), an in-place destructive or backfill
   migration that rewrites rows or flips a CHECK constraint or enum, a
   mutual-exclusion, auth, or payment primitive where dual-running is the hazard,
   and any breaking change to a versioned or out-of-tree consumer surface.
6. **"Releasable" is not the same as "CI-green."** This is the critical carve-out.
   For per-table destructive migrations and dual-run concurrency cutovers, build
   and test go green while `main` is corrupt or unsafe to deploy. The releasability
   check has to assert the cross-table, cross-tree, or runtime invariant, not just
   that the build passed. If you cannot assert the invariant in an intermediate
   slice, the cut lands mid-atom, so fold it into the cutover PR.
7. **Mechanical-tier exemption.** A large but mechanical and atomic diff (a
   rename, a codemod, a dependency bump) routes to one-navigable-PR. That is the
   correct low-cognitive-load form, not a split-PR failure.

### Per-class routing

| Change class | Route |
|--------------|-------|
| Greenfield or additive feature with user-story decomposition (model, then logic, then UI, wired last) | split-PR (default) |
| In-place modification with all consumers in the tree | branch-by-abstraction |
| Breaking change to a versioned or out-of-tree consumer surface | fallback (v2 beside v1, or atomic PR plus a consumer plan) |
| In-place destructive or backfill migration | fallback (atomic PR plus lockstep code) |
| Security, auth, or concurrency mutual-exclusion cutover | fallback (flag-gated, or atomic PR when there is no flag) |
| Cross-cutting exported-symbol rename across hundreds of call sites | out-of-scope (one navigable PR) |
| Dependency, framework, runtime, or platform cutover on a single global pin | out-of-scope (atomic flip; prep and cleanup may still slice) |
| Redesign that replaces a visible screen on a no-flag release-cadence app | fallback (one swap PR plus a release hold, or a runtime toggle added in Foundation) |

### Detection order (cheapest and most authoritative first)

1. Read the `tasks.md` shape. Does it carry user-story phases?
2. Check additive-versus-modify per increment. Grep the diff for edits to
   existing symbols, and for migration verbs like `UPDATE`, `DELETE`, `DROP`, and
   `CHECK`, versus net-new work like `CREATE TABLE` or a nullable `ADD COLUMN`.
3. Probe for a flag system (`feature-flags*`, `FEATURE_*`, OpenFeature).
4. Read the release cadence. Sparkle, an appcast, `Info.plist`, or the App Store
   means release-cadence; Vercel or preview deploys mean continuous.
5. Check consumer locality for API changes. A versioned `/api/vN` or an MCP
   process counts as out-of-tree, so route conservatively.

### The risk that matters most

A naive split-PR gate that treats "build and test green" as "releasable"
manufactures a deploy-corruption failure mode the single big PR never had: a
mixed-schema `main`, or two live admission controllers. Two ways out. Either
upgrade the releasability check to assert the real invariant, or detect those
signatures and route them to an atomic PR with a warning to the human. The v1
recommendation is detect-and-route, and defer the invariant machinery.

> Note: the no-flag and release-cadence branch is grounded in evidence, not
> assumed. focusengine is a Swift macOS app that ships small no-flag PRs, and
> #195 is its TypeScript to Swift cutover.

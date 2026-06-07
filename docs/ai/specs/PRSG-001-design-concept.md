---
topic: "Artifact relocation: tiering, .process/, collapse"
slug: "prsg-001-artifact-relocation"
date: "2026-06-05"
mode: "setup"
spec_id: "PRSG-001"
source_input:
  type: "topic"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (### PRSG-001); docs/prd-pr-size-governance.md (§3.1)"
question_count: 5
stop_reason: "natural"
---

# Design Concept: Artifact relocation — tiering, .process/, collapse

> **Source:** PRSG-001 scope in the PR-size governance roadmap + PRD §3.1
> **Date:** 2026-06-05
> **Questions asked:** 4
> **Stop reason:** natural (every remaining choice is locked in the roadmap or resolved by an evidence-backed grounding pass)

This concept was scoped against a four-agent grounding pass over the actual
plugin source (recorded under **Grounded Implementation Notes**), so the design
decisions below reflect what speckit-pro can actually do today, not just the
roadmap text.

## Goals

- Remove the auto-generated process exhaust from the review diff **at the
  source**, so a feature PR shows the contract artifacts (spec/plan/tasks) and
  code, not the scaffolding that produced them. (~32% of a feature PR is exhaust.)
- Tier every spec artifact into **CONTRACT** (review-visible, never collapsed)
  vs **EXHAUST** (collapsed under a `.process/` directory).
- Redirect the exhaust speckit-pro itself authors — the **design-concept doc**,
  the **workflow file**, and the **UAT runbook** — into `.process/`.
- Ship a repo-root `.gitattributes` that collapses `.process/` via
  `linguist-generated=true`, and make the same collapse reach **consuming
  projects** (not just this plugin's own repo).
- Align the reviewability gate's `is_excluded_generated()` so relocated exhaust
  drops out of the reviewable-LOC count too.
- Guard the whole thing with a Layer-1 lint (the collapse glob is scoped to
  `.process/` only, never a CONTRACT path) and a Layer-4 determinism test.

## Non-goals

- **Collapsing extension-authored exhaust** (retrospective, verify-tasks-report).
  Answered in Q4, confirmed by the archive-extension finding (below): these are
  written by external SpecKit extensions speckit-pro does not control, and their
  **post-merge cleanup is already owned by the `archive` extension** (distill to
  `.specify/memory/` + gated whole-dir removal). PRSG-001 leaves them visible in
  the review window and does **not** build a `git mv` sweep to chase them into
  `.process/`. (`verify` writes no file; `peer-review`/`analyze` are speckit-pro's
  own, not extensions.)
- **`-diff` (rendering artifacts non-diffable).** Locked in the roadmap:
  `linguist-generated` only, so artifacts stay loadable/inspectable ("Load diff").
- **Retro-migrating existing/legacy specs.** Locked new-specs-only; the codemod
  that moves the ~8 legacy `specs/<NNN>/` dirs is PRSG-011.
- **Making the gate parse `.gitattributes`.** Locked open-decision #6: the
  `.process/` glob is intentionally hardcoded in the gate too (two places), with a
  cross-file lint to catch drift. `bash` `case` cannot faithfully express
  gitattributes `**` anyway.
- **Moving the spec contract artifacts** (spec/plan/tasks/research/data-model/
  contracts/checklists/SPEC-MOC, and quickstart as forward-compat). These are
  written by upstream `/speckit.*` commands into `specs/<NNN>/` and stay visible.
- **New flags / abstractions for one call site** (CLAUDE.md rule 2). The redirect
  is path-string edits in markdown skills, not a new helper layer.

## Design Tree (Q&A log)

### Q1. Where should auto-generated exhaust be written so the collapse glob can actually catch it?

**Branch:** Redirect target / glob coverage (load-bearing)

**Recommended answer:** Dual `.process/` anchor — scaffold-spec writes
`docs/ai/specs/.process/`, autopilot writes `specs/<NNN>/.process/`, and one rule
`**/.process/** linguist-generated=true` collapses both trees.
> Grounding proved the two artifacts speckit-pro authors land in `docs/ai/specs/`
> (a different tree from `specs/<NNN>/`), so the roadmap's literal
> `specs/*/.process/**` glob would never match them and US2 would be inert. A
> broad `docs/ai/specs/*.md` glob is ruled out because that dir holds CONTRACT
> roadmaps next to exhaust. Anchoring on `.process/` in both trees is the only
> option that collapses the full authored exhaust list AND passes the
> ".process/-only" lint. Evidence: scaffold-spec SKILL.md:145–189; gate
> is_excluded_generated() reviewability-gate.sh:48–57; dogfood trees specs/ +
> docs/ai/specs/.

**Alternatives offered:**
- Literal roadmap glob only (`specs/*/.process/**`): cheapest and closest to the
  written roadmap, but the two largest scaffold-time exhaust files stay fully
  visible — undercuts the goal.
- Single tree (move into `specs/<NNN>/.process/`): one canonical tree, but
  `specs/<NNN>/` doesn't exist at scaffold time and `create-new-feature.sh` may
  clobber/merge a pre-existing `.process/` (unverified risk) + adds
  scaffold↔autopilot ordering coupling.

**User's answer:** Dual `.process/` anchor (Recommended)

---

### Q2. Should scaffold-spec also write the `.gitattributes` rule into consuming projects?

**Branch:** Reach / deliverable boundary

**Recommended answer:** Both repos — a static `.gitattributes` committed at the
plugin root (dogfood + the Layer-1 lint target) AND an idempotent consumer-side
ensure-step in scaffold-spec that appends the rule to the consuming project's
`.gitattributes`.
> GitHub's linguist reads each repository's own `.gitattributes`, so a
> plugin-only file collapses only the plugin's own PRs. new-specs-only is locked,
> so consumers must get collapse for their new specs immediately. The
> write-into-consumer pattern already exists and is already invoked by scaffold-
> spec: `ensure-reviewability-preset.sh` (PROJECT_ROOT from `$PWD`, write-if-
> changed). Evidence: ensure-reviewability-preset.sh:13,206–251; scaffold-spec
> SKILL.md:174–178.

**Alternatives offered:**
- Plugin repo only: simplest/smallest, but consuming projects get zero collapse
  for new specs until an unrelated migration runs there — the benefit never
  reaches end users on the locked timeline.

**User's answer:** Both repos (Recommended)

---

### Q3. Should PRSG-001 collapse `uat-runbook.md`?

**Branch:** Taxonomy edge case (stated intent vs current behavior)

**Recommended answer:** EXHAUST — move it to `.process/` and repoint
`generate-pr-body.sh` so the PR body's "## UAT Runbook" section still renders.
> The research doc and PRSG-011 both call it EXHAUST. It is speckit-pro-authored
> (`generate-uat-skeleton.sh`), so unlike the extension-authored exhaust it IS in
> PRSG-001's control. Its content is mirrored into the PR body, so the standalone
> file can collapse without losing review visibility. Because PRSG-011 only
> migrates legacy specs, NEW specs only ever collapse the runbook if PRSG-001
> does. Evidence: research §"Decisions raised" (UAT runbook = Exhaust);
> generate-pr-body.sh:179,188 (hardcoded read path + link); generate-uat-
> skeleton.sh:331; post-implementation.md:564,590.

**Alternatives offered:**
- CONTRACT (leave visible): no PR-body repoint, no regression risk, but
  contradicts the research/PRSG-011 decision and leaves new specs' runbooks in
  the diff permanently.

**User's answer:** EXHAUST — collapse it (Recommended)

---

### Q4. How should PRSG-001 handle the extension-authored exhaust the PRD names but speckit-pro doesn't write?

**Branch:** Acceptance scope / honesty

**Recommended answer:** Scope PRSG-001 to what speckit-pro authors
(design-concept, workflow, uat-runbook) and **document** that extension-authored
exhaust (retrospective, peer-review, verification-evidence, cleanup, analysis)
collapses only once it lands under `.process/` — explicitly future/PRSG-011 work.
> Grounding found these are written by external SpecKit extensions / upstream
> `/speckit.*`, not speckit-pro prose or scripts, so PRSG-001 cannot redirect
> them via skill edits. A post-impl "sweep" that git-mv's them would add LOC,
> overlap PRSG-011's codemod, and risk moving a file an extension still expects at
> its old path. The PRD's AC-1.1 reads broader than what ships, so spec.md must
> narrow the acceptance criteria accordingly. Evidence: task-list-canonical.md:37–49;
> phase-execution.md:730; grep found no speckit-pro write of these basenames.

**Alternatives offered:**
- Add a post-impl sweep step: collapses everything the PRD names, but adds real
  LOC + fragility, overlaps PRSG-011, and breaks the single-responsibility line.

**User's answer:** Scope to authored + document (Recommended) — see Q5, which
re-grounded the "document as future/PRSG-011 work" half: post-merge cleanup of
extension exhaust is already owned by the `archive` extension, so it is not a gap.

---

### Q5. Does the existing `archive` extension already clean up the SpecKit exhaust? (raised by the user before finalizing)

**Branch:** Lifecycle / build-vs-reuse

**Finding:** The installed `archive` extension (`v1.1.0`, `racecraft-lab/spec-kit-archive`)
**distills then sweeps**: it folds a merged feature's substance into
`.specify/memory/` (`spec.md`/`plan.md`/`changelog.md` + agent file) with provenance
and recovery commands, then under `--apply-cleanup` (8 gates) removes/moves the
**entire merged feature dir** out of `specs/**`. It is wired as a `before_specify`
**dry-run** sweep (optional prompt); apply-cleanup is a separate gated step.

**Resolution:** It cleans up exhaust **post-merge, whole-dir** — the *opposite end
of the lifecycle* from PRSG-001, which collapses exhaust in the **review window**
(an open PR; archive never touches it because the feature isn't merged yet). They
are **complementary halves**, and the roadmap already designed for this:
locked decision = "collapse-only v1, post-merge **relocation deferred to v2**";
PRSG-011 "mirrors speckit-archive-run's gated-safety pattern."
> Consequence: the "extension exhaust accumulates" worry (Paddock-scale specs/ trees)
> is owned by `archive`, not PRSG-001. So PRSG-001 stays the review-window half:
> collapse what speckit-pro authors (design-concept, workflow, uat-runbook); leave
> retrospective/verify-tasks-report visible at review (archive cleans them after
> merge); do NOT build a `git mv` sweep. Evidence:
> .specify/extensions/archive/commands/archive.md:55-57,89-105,283,347;
> extensions.yml:83-89 (before_specify dry-run hook); roadmap locked-decisions table.

**User's answer:** Lock in the scoped PRSG-001 (review-window collapse of
speckit-pro-authored exhaust; archive owns post-merge); add the
"extension exhaust → archive extension (post-merge)" note.

## Open Questions

- **What:** Canonical filename for the review packet — `peer-review-*` (PRSG-001's
  name) vs `pr-review-packet.md` (PRSG-011's allow-list name).
  **Why deferred:** Neither exists as a spec file today (the packet is a PR-body
  marker comment), so this is a naming-contract decision, not a PRSG-001 blocker.
  **Suggested next step:** Settle during the PRSG-011 grill-me; PRSG-001 treats
  `peer-review-*` as a `.process/` glob alias if/when emitted as files.

- **What:** Shape of verification evidence — single `verification-evidence.md`
  (PRSG-001) vs an `evidence/` directory (PRSG-011).
  **Why deferred:** Neither exists on disk today (verification detail lives in the
  workflow log).
  **Suggested next step:** Decide file-vs-directory in PRSG-011 so the redirect and
  the relocate codemod don't split-brain.

- **What:** Whether `design-concept.md` / `workflow.md` should be added to
  PRSG-011's PROCESS git-mv allow-list (they're EXHAUST here but absent from that
  list).
  **Why deferred:** Out of scope — PRSG-001 is new-specs-only; PRSG-011 owns
  legacy moves.
  **Suggested next step:** Forward note for the PRSG-011 grill-me pass.

- **What:** Whether to dogfood the redirect on PRSG-001's *own* scaffold artifacts
  (relocate this design-concept + workflow into `docs/ai/specs/.process/` so they
  collapse in PRSG-001's own PR once the `.gitattributes` lands).
  **Why deferred:** This scaffold ran on the *current* (pre-PRSG-001) skill, which
  writes to `docs/ai/specs/`; doing the move now would pre-empt the implementation.
  **Suggested next step:** Optional small task during implement — move the two files
  into `.process/` and update the autopilot workflow path reference.

## Grounded Implementation Notes (evidence-backed)

Not design choices — a factual map from the grounding pass, carried so the
workflow file's Specify/Plan/Tasks prompts don't have to re-derive it.

**US1 — redirect (markdown-prose edits; mirror to Codex in the same PR):**
- Edit `speckit-scaffold-spec/SKILL.md` (the `mkdir`, grill-me `output_path`, the
  workflow `Write` target, and the `git add` paths) to `docs/ai/specs/.process/`.
- Mirror identically in `codex-skills/speckit-scaffold-spec/SKILL.md` (parity
  mandate) and update `speckit-coach/templates/workflow-template.md` self-refs.
- `uat-runbook.md` → `specs/<NNN>/.process/`; repoint `generate-pr-body.sh:179,188`
  (read path + `./uat-runbook.md` link) and `post-implementation.md:564,590`.
- Autopilot already does `git add specs/` (covers `specs/<NNN>/.process/`);
  scaffold-spec's explicit `git add docs/ai/specs/...` must include the `.process/`
  path.

**US2 — collapse + align + lint:**
- New repo-root `.gitattributes`: one rule `**/.process/** linguist-generated=true`.
- Consumer ensure-step: append that rule to the consuming repo's `.gitattributes`
  idempotently, patterned on `ensure-reviewability-preset.sh`.
- Gate: add one arm to `is_excluded_generated()` (reviewability-gate.sh:48–57):
  `*/.process/*|*.process/*) return 0 ;;` (anchored on `.process/`; covers
  worktree-prefixed paths). Keep hardcoded (open-decision #6). This moves only
  diff-mode `reviewable_loc` (markdown is never a production file).
- Pre-existing dead code: gate line 54 `docs/ai/workflows/*/exports/*` (that dir
  doesn't exist). Mention, do not delete (CLAUDE.md rule 3).

**Tests:**
- **L4** (extend the already-wired `tests/layer4-scripts/test-reviewability-gate.sh`):
  diff-mode only — build a git repo, add N lines to `specs/001-foo/.process/workflow.md`
  AND N lines to `specs/001-foo/spec.md`, assert `reviewable_loc == N` (process lines
  excluded, spec lines counted) + a negative control. A tasks-mode/production_files
  test would pass vacuously (markdown isn't a production file).
- **L1** (new `tests/layer1-structural/validate-process-gitattributes.sh`, textual,
  modeled on `validate-pr-checks-sentinel.sh`, add to `run-all.sh` array): assert the
  file exists, contains the rule, and every `linguist-generated` line contains the
  `/.process/` segment (which textually guarantees it can't match a CONTRACT path).
  Optional 4th assert: the gate's `is_excluded_generated()` also contains `.process/`
  (cross-file drift guard for the two-places duplication).
- **Codex/L8:** US1 prose edits need the Codex mirror; US2 (shared gate script,
  repo-root `.gitattributes`, non-mirrored tests) needs **zero** Codex work.

**Budget reality:** ~250 LOC is realistic for US1 (prose) + US2 (gate arm +
gitattributes + L1 + L4). The consumer ensure-step (Q2) and the uat repoint (Q3)
add a little; treat ~250 as a target, not a ceiling.

## Recommended Next Step

Setup mode — the worktree, branch (`007-artifact-relocation`), and this
design concept already exist. After the workflow file is populated and committed:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/PRSG-001-workflow.md
```

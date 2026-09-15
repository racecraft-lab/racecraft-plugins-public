---
topic: "Draft-PR emission: end the plan stage at a committed artifact set and an open draft PR"
slug: "art-007-design-concept"
date: "2026-08-17"
mode: "setup"
spec_id: "ART-007"
source_input:
  type: "topic"
  ref: "ART-007 scope description from docs/ai/specs/html-artifacts-technical-roadmap.md"
question_count: 7
stop_reason: "natural"
---

# Design Concept: ART-007 Draft-PR Emission

> **Source:** ART-007 scope in `docs/ai/specs/html-artifacts-technical-roadmap.md`
> **Date:** 2026-08-17
> **Questions asked:** 7
> **Stop reason:** natural (no critical open branches remained)
> **Blind-spot pass:** ran — 4 findings surfaced, 2 set aside

## Goals

- End the plan stage at a committed draft artifact set and an open draft PR
  whose body indexes the artifacts, then stop for human review. One vertical
  slice: artifact generation → commit → draft PR → stop report.
- Extend `pr-packet.schema.json` with a third `mode: "draft"` that
  conditionally relaxes the implementation-evidence requirements
  (`verification_evidence`, `scope_evidence.changed_files`, `uat.how_to_uat`),
  reusing the existing packet machinery and validator family (Q1). ART-010
  later upgrades the same packet to `single`/`split`.
- Ship an `artifact-author` subagent on both platforms
  (`speckit-pro/agents/artifact-author.md` + `speckit-pro/codex-agents/`
  mirror) that reads spec.md / plan.md / tasks.md / the design concept,
  selects `stage: draft-pr` templates per the gallery manifest routing
  (implementation-plan + spec-explainer always; code-approaches on
  `competing_approaches`; module-map on `brownfield_change`), fills the
  fill-regions, and writes `specs/<branch>/artifacts/*.html`. Fail-open:
  generation failure logs a gap and never blocks the draft PR.
- Emit the draft PR with a final-shape conventional title (self-validated
  locally against the release-readiness gate shape, decoupled from
  implementation evidence in draft mode) and a minimal body: the Artifacts
  index table (artifact, purpose, copy-paste open command) plus a
  resume/status block (Q6). `gh pr create --draft`.
- Record the draft-PR identity (number + URL) as a new row on the workflow
  file's status surface — the workflow file only, no state-file mirror (Q4).
- Implement the gh corroboration limb ART-006 deferred here: stage auto-detect
  reads the draft-PR row, corroborates via `gh`, logs a discrepancy when they
  disagree, and the workflow file wins per the inherited OQ-4 contract (Q5).
- Resolve OQ-1 now rather than in clarify: when final reviewability later
  requires a marker-split, the draft PR becomes the first slice PR of the
  stack (Q2). The clarify phase encodes this decision into the spec; it does
  not re-open it.
- Plan-stage stop report: draft-PR URL, artifact index, resume instructions;
  on a strict-mode G6.5 block, the report names the blocked gate instead of a
  URL (Q3).
- Advisory size estimate: 327 estimated LOC, `suggested_slices: 1`,
  `status: ok` (estimator inputs: 3 user stories, 10 production files, 12 FRs,
  modify-weighted). Under the 400 ceiling; no split warranted. The roadmap's
  declared budget (217) predates the Q5 decision to absorb the ~70-LOC
  corroboration limb.

## Non-goals

- Reading or acting on PR feedback (ART-008) and flipping the draft to ready
  (ART-010) — carried from the roadmap entry.
- No draft PR on a strict-mode G6.5 block: emission runs only when the gate
  resolves pass or warn; the blocked stop stays PR-less and the re-run that
  passes emits the PR (Q3).
- No Layer 6 corpus membership for `artifact-author` in this spec: the
  governed twelve-role corpus is untouched, and membership is a tracked
  deferral to ART-009, which must already open the corpus to rename
  `uat-runbook-author` (Q7). ART-007 must not edit any of the twelve governed
  agent definitions (that is what restales the digest chain).
- No full body skeleton at draft time: no release-note fence, no verification
  sections, no placeholder final writeup — ART-010 owns the final body, and
  this repo's `pr-checks.yml` skips every job while a PR is draft, so nothing
  goes red before the flip (Q6).
- No state-file mirror of the draft-PR identity (Q4).
- No hosting layer for artifacts: committed review-visible under
  `specs/<branch>/artifacts/` and opened locally over `file://` (roadmap Key
  Decision, 2026-07-28).

## Design Tree (Q&A log)

### Q1. The blind-spot pass confirmed pr-packet.schema.json cannot represent a draft PR today: its mode enum is only ["single","split"], and its required fields presuppose a finished implementation. How should the draft path get a valid packet?

**Branch:** Packet contract / draft mode (blind-spot finding 1)

**Recommended answer:** Add mode "draft" to the schema
> Extend the existing enum with "draft" and conditionally relax the
> implementation-evidence requirements, the same conditional pattern the
> schema already carries for `split_slice`. Honors the roadmap's "through the
> existing packet machinery in a draft mode" wording, keeps one schema and one
> validator family, and ART-010 upgrades the same packet in place.

**Alternatives offered:**
- Separate draft-packet schema: cleaner required-lists, but forks the packet
  contract into two schemas and two validator paths, and ART-010 must
  translate between them.
- Bypass packet machinery for drafts: smallest diff today, but contradicts
  the roadmap scope wording and leaves ART-008/ART-010 with no packet to read
  or upgrade.

**User's answer:** Add mode "draft" to the schema (Recommended)

---

### Q2. OQ-1: when final reviewability later requires a marker-split (multiple slice PRs), what happens to the early draft PR?

**Branch:** OQ-1 resolution (roadmap-scoped clarify item, settled by the human now)

**Recommended answer:** Draft becomes slice-1 PR
> The draft PR on the spec branch is retitled/rescoped as the first slice PR
> of the stack. Matches how art-003 actually ran (spec-branch PR plus
> slice-2/slice-3 PRs), preserves the feedback thread ART-008 sweeps, and
> fits ART-010's flip-in-place design. This is also the PRD's own first-limb
> recommendation (docs/prd-html-artifacts.md OQ-1).

**Alternatives offered:**
- Supersede with a comment: cleaner slice symmetry, but orphans the review
  feedback collected on the draft and forces ART-008/ART-010 to handle a
  dead-PR case.
- Defer to clarify phase: keeps the roadmap's original plan but hands a
  design fork to an autonomous phase that would otherwise have the human
  answer.

**User's answer:** Draft becomes slice-1 PR (Recommended)

---

### Q3. The plan stage already has a documented exception path: a strict-mode G6.5 failure takes the boundary commit, records a non-terminal blocked row, and STOPs. Does that blocked stop still open a draft PR?

**Branch:** G6.5 terminal-step interplay (blind-spot finding 3)

**Recommended answer:** No draft PR on strict block
> Draft-PR emission runs only when G6.5 resolves pass or warn. A blocked
> stage stays PR-less; the stop report names the blocked gate instead of a
> URL, and the re-run that passes emits the PR. Keeps ART-006's
> planning-complete predicate clean (no dedup logic for a half-born PR) and
> does not ask humans to review a plan the gate refused. Grounded in the
> documented terminal-step contract
> (`speckit-pro/skills/speckit-autopilot/references/phase-execution.md`,
> "Plan stage: G6.5 is the terminal step").

**Alternatives offered:**
- Always open the draft PR: human review is what a blocked plan arguably
  needs most, but it blurs the planning-complete predicate and forces the
  re-entry path to find and update an existing PR.

**User's answer:** No draft PR on strict block (Recommended)

**Notes:** Recommended sequencing recorded for the plan phase: artifact
generation runs after G6.5 resolves pass/warn and before the stage-boundary
commit, so the artifacts ride the boundary commit's existing `git add specs/`
enumeration; the branch push at the boundary is what makes `gh pr create
--draft` possible; the draft-PR row write lands after PR creation as its own
bookkeeping commit, following the existing post-implementation PR-creation
pattern.

---

### Q4. ART-008, ART-010, and the inherited gh-corroboration limb all need to find "the draft PR for this feature" later. Where is the draft-PR identity durably recorded?

**Branch:** Draft-PR identity storage (blind-spot finding 4)

**Recommended answer:** Workflow-file row only
> Add a draft-PR row (URL + number) to the workflow file's status surface,
> written when the PR opens. OQ-4 already declares the workflow file
> authoritative, existing helpers parse that table, and one write path avoids
> the status-versus-evidence drift the CI guards fail on.

**Alternatives offered:**
- Workflow row + state-file mirror: saves consumers a Markdown parse, but two
  sinks must stay in sync and the mirror is non-authoritative under OQ-4
  anyway.
- State file only: simplest machine contract, but contradicts the inherited
  OQ-4 decision that the workflow file is authoritative.

**User's answer:** Workflow-file row only (Recommended)

---

### Q5. ART-006 deferred its gh corroboration limb for stage auto-detect to ART-007, costed at roughly 70 LOC. Does ART-007 implement that limb, or only create the workflow-file row it would corroborate?

**Branch:** Inherited OQ-4 corroboration scope (blind-spot finding 4)

**Recommended answer:** Implement the limb here
> Auto-detect reads the draft-PR row, corroborates via `gh`, logs a
> discrepancy when they disagree, and the workflow file wins (the OQ-4
> contract). ART-007 is the first spec where the positive case is live and
> testable — the roadmap's ART-006 amendment named ART-007 as "the spec that
> creates the draft PRs it would corroborate against" — and 217 + ~70 LOC
> stays under the 400 warn ceiling.

**Alternatives offered:**
- Row only; limb to ART-008: keeps ART-007 smaller, but leaves auto-detect
  uncorroborated for one more spec and splits the OQ-4 contract across two
  specs.
- Row only; limb unscheduled: smallest ART-007, but the deferred limb loses
  its named owner and the roadmap's "ART-007 inherits" sentence goes stale.

**User's answer:** Implement the limb here (Recommended)

---

### Q6. This repo's pr-checks.yml skips every job while a PR is draft, so the draft can't fail CI. What shape do the draft PR's title and body take at emission?

**Branch:** Draft PR title/body shape and gate interaction

**Recommended answer:** Final-shape title, minimal body
> Mint the real conventional title now (e.g. `feat(speckit-pro): …`),
> self-validated locally against the release-readiness gate shape
> (`<type>(<lowercase-scope>): <plain English description>`), decoupled from
> implementation evidence in draft mode. Body carries only the Artifacts
> index table plus a resume/status block, per the roadmap. Public viewers see
> an honest title from day one; ART-010 rewrites the body and keeps or amends
> the title. Grounded in `.github/workflows/pr-checks.yml`, where every job
> is gated `draft == false`.

**Alternatives offered:**
- Placeholder title, minimal body: avoids promising a change type before
  implementation, but shows a misleading type on a public repo for the
  spec's whole life and adds a mandatory retitle step to ART-010.
- Full body skeleton at draft: the flip becomes a fill-in, but duplicates
  ART-010's writeup machinery and placeholder sections sit publicly readable
  until then.

**User's answer:** Final-shape title, minimal body (Recommended)

**Notes:** The release-note fence is deliberately absent from the draft body;
`validate-release-note` does not run while the PR is draft, and ART-010 adds
the fence at flip time. Fail-open sinks recorded for the plan phase: a
generation failure appears as a gap row in the PR body's Artifacts index, in
the stop report, and as a note on the workflow file's draft-PR row; a
zero-artifact failure still opens the PR with a gap-marked index, per the
roadmap's fail-open mandate.

---

### Q7. Given that corpus membership for artifact-author is the destination (every shipped agent is governed today), and that an honest new-role entry requires real collateral (oracle, fixture, independent review), which spec pays for it?

**Branch:** Layer 6 governed corpus (blind-spot finding 2)

**Recommended answer:** Tracked deferral to ART-009
> ART-007 ships artifact-author ungoverned with the exclusion recorded as an
> explicit tracked deferral, and corpus membership lands with ART-009, which
> must already open the corpus to rename `uat-runbook-author`. One corpus
> surgery for the roadmap, no fabricated review evidence, ART-007 stays one
> slice. The precedent recorded is "membership lands with the first spec that
> opens the corpus", not "agents may skip governance".

**Alternatives offered:**
- Join the corpus in ART-007: governance from day one, but roughly doubles
  the spec (likely 2 slices) and the review collateral must be genuinely
  produced, not templated.
- Add a dedicated corpus spec: cleanest long-term fix for the missing
  tooling, but adds a roadmap entry and leaves artifact-author ungoverned
  across two more specs.

**User's answer:** Tracked deferral to ART-009 (Recommended)

**Notes:** The user challenged the first framing of this question with "why
should we establish a precident of creating agents outside the corpus?" —
which forced the deeper grounding: (a) every shipped agent is governed today,
so artifact-author would be the first ungoverned one; (b) ART-012 (PR #426)
already performed corpus surgery for an *edit* (implement-executor), touching
exactly `corpus-manifest.json` + the role's `fixture.json` and hand-recomputing
the four-level digest chain; (c) a *new* role additionally needs an acceptance
oracle, an authored fixture, expected-artifact contracts, and an
`independent_review` block with `review_state: "passed"` — collateral that
cannot be honestly fabricated inside ART-007; (d) the twelve-role pins live in
the corpus manifest, both role-corpus schemas, module constants, and the
corpus unit tests. The chosen deferral requires a roadmap amendment: ART-009's
entry gains the artifact-author corpus-membership work alongside its rename
surgery (applied at scaffold Step 8, following the ART-006 amend-during-
scaffold precedent).

## Open Questions

- **What:** Exact name, column format, and placement of the draft-PR row in
  the workflow file's status surface (workflow-file protocol change).
  **Why deferred:** Protocol-level detail; the interview fixed the contract
  (workflow file only, URL + number), not the row syntax.
  **Suggested next step:** Clarify session focus 1; resolve against
  `references/workflow-file-protocol.md` during the plan phase.
- **What:** Corroboration discrepancy log format and sink (where "gh
  disagrees with the workflow file" gets written, and what auto-detect does
  next in each discrepancy class, e.g. PR closed vs PR missing vs URL
  mismatch).
  **Why deferred:** Behavior detail below the interview's altitude; the
  contract (workflow file wins, discrepancy logged) is fixed by Q5.
  **Suggested next step:** Clarify session focus 2.
- **What:** Whether committed `specs/<branch>/artifacts/*.html` need a
  `.gitattributes` `merge=generated` entry.
  **Why deferred:** Blind-spot analyst set this aside as low impact — sibling
  per-feature files (plan.md, tasks.md) are not marked generated either and
  do not hit the merge pain the driver exists for.
  **Suggested next step:** Revisit only if a real merge conflict appears on an
  artifacts directory; do not mark preemptively.
- **What:** artifact-author's model/effort frontmatter and permitted-tool
  surface.
  **Why deferred:** Convention question with a strong local precedent.
  **Suggested next step:** Mirror `uat-runbook-author`'s frontmatter pattern
  (the closest shipped analogue: content-authoring, fail-open, PR-time
  dispatch) during the plan phase; verify with a disk read, not from memory.

## Recommended Next Step

Setup has already happened (this doc was produced inside
`/speckit-pro:speckit-scaffold-spec ART-007`). The scaffold continues:
populate `ART-007-workflow.md` from this doc, commit both, then hand off to
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-007-workflow.md
--stage plan`.

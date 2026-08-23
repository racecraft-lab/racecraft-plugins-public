---
topic: "Feedback sweep: open the implement stage by reading draft-PR feedback, amending the plan through consensus, and stopping for re-review"
slug: "art-008-design-concept"
date: "2026-08-20"
mode: "setup"
spec_id: "ART-008"
source_input:
  type: "topic"
  ref: "ART-008 scope description from docs/ai/specs/html-artifacts-technical-roadmap.md"
question_count: 12
stop_reason: "natural"
---

# Design Concept: ART-008 Feedback Sweep

> **Source:** ART-008 scope in `docs/ai/specs/html-artifacts-technical-roadmap.md`
> **Date:** 2026-08-20
> **Questions asked:** 12
> **Stop reason:** natural (no critical open branches remained)
> **Blind-spot pass:** did not run — wait deadline expired

## Goals

- Open the implement stage with a draft-PR feedback sweep that runs as the
  first Phase 7 setup step, ahead of "Open the Implementation-Notes Record",
  in both phase-execution variants. No new Workflow Overview row (Q1).
- Read two comment surfaces: review threads whose `isResolved` is false, and
  PR-level conversation comments, where a pasted "Copy as Markdown" export
  most naturally lands. PR-level comments carry no resolved flag, so the
  sweep's own record decides "already handled" there (Q2, Q6).
- Act only on comments whose `authorAssociation` is OWNER, MEMBER, or
  COLLABORATOR. Every other author's comment is listed in the report as
  "not swept: untrusted author" and never reaches consensus (Q3).
- Recognize artifact-exported markdown blocks through a lead-sentence registry
  carried by a new read-only runner helper. The three shipped leads are the
  `implementation-plan`, `code-approaches`, and `module-map` exports; no
  template is edited (Q10). The helper follows the shipped
  `resolve-autopilot-stage` pattern: the orchestrator takes the live `gh`
  observation, hands the JSON to the helper as an input, the helper filters
  and classifies deterministically, and Layer 4 golden fixtures pin the
  parse. That is what makes the roadmap's "comment-schema fixtures"
  testable.
- Classify each trusted comment as amended, answered, deferred, or no action.
  Substantive items route through the existing category-routed consensus
  machinery to amend `spec.md`, `plan.md`, or `tasks.md`, and each amendment
  is committed and pushed (Q5; roadmap scope).
- Record every handled comment in a `Feedback Sweep Log` table in the
  workflow file: comment id, surface, author, class, disposition, commit.
  Amendments additionally get the Consensus Resolution Log row the roadmap
  mandates, linked by number. A re-run skips any id already logged (Q6).
- Post one reply per handled comment naming the class, the artifact and
  section touched, and the amending commit. The sweep never resolves a
  thread: the operator resolves when satisfied, and convergence is the clean
  re-run after they do (Q4, Q5).
- Stop or proceed: amendments stop for re-review with a report that mirrors
  the plan-stage stop report; a clean sweep proceeds directly into Phase 7.
  A present Draft PR row that cannot be read (`gh` unreachable, `pr_closed`,
  `pr_missing`, `identity_mismatch`) stops with a report naming the status
  and the resume path. Only `no_record` proceeds, because no draft PR was
  ever opened (Q7).
- Artifact freshness: after amendments, regenerate the whole draft set by
  re-dispatching the artifact-author exactly as the plan-stage terminal step
  does. On a clean sweep, detect stale pages from git history alone (a
  planning file with a commit newer than the newest commit touching
  `specs/<feature>/artifacts/`), regenerate, refresh, and proceed without
  stopping. Refresh the draft description through ART-007's
  create-or-refresh path, with the Resume block stating the sweep outcome
  (Q8, Q9, Q11).
- Split into 2 vertical slices, stacked in this order (Q12):
  - **Slice 1, the checkpoint** (branch `art-008-feedback-sweep`, from
    `main`): read both comment surfaces, trust filter, export recognition
    (helper plus fixtures), classify, consensus-amend, Feedback Sweep Log and
    CRL rows, per-comment replies, stop-or-proceed, and the unreadable-PR
    stop. Amendments commit and push. The stop report states that draft
    pages regenerate once slice 2 lands.
  - **Slice 2, artifact freshness** (branch `art-008-feedback-sweep-slice-2`,
    from slice 1): whole-set regeneration after amendments, stale-page
    detection on a clean sweep, and the description refresh with the Resume
    block wording.
- Advisory size estimate (runner operation `estimate-spec-size`,
  2026-08-20): `{estimated_loc: 452, suggested_slices: 2, status: "warn"}`
  from 3 user stories, 14 files, 18 functional requirements, modify-weighted.
  Production files alone (9) return
  `{estimated_loc: 352, suggested_slices: 1, status: "ok"}`. The roadmap's
  declared budget (150 LOC, ~4 production files) predates the deterministic
  helper, the Codex mirrors, and the trust filter. Each slice re-measures at
  its own Plan phase.

## Non-goals

- Post-implementation review remediation: the existing `/loop` machinery is
  unchanged (roadmap entry).
- The ready flip: a clean sweep never marks the PR ready; that belongs to
  ART-010 (Q11, alternative rejected).
- Resolving review threads: the sweep never calls `resolveReviewThread`
  (Q4).
- A new Workflow Overview phase row, and therefore no edits to
  `WORKFLOW_PHASE_GATE_IDS` in the coverage guard, `AUTOPILOT_STAGE_PHASES`
  in `read_only.py`, or the workflow template for the sweep (Q1).
- Editing shipped gallery templates or their payload copies for export
  recognition (Q10).
- A page-to-source regeneration mapping (Q9).
- Routing comments from authors outside OWNER, MEMBER, or COLLABORATOR to
  consensus (Q3).
- Reading review summary bodies (Q2).
- A state-file mirror of the sweep record: the workflow file is the sole
  store, following the Draft PR row precedent (Q6).

## Design Tree (Q&A log)

### Q1. Where does the feedback sweep execute inside the implement stage: as a named setup step inside Phase 7, as a new phase row in the Workflow Overview table, or during opening preparation before any phase starts?

**Branch:** Sweep slot / stage architecture

**Recommended answer:** Phase 7 setup step
> The sweep runs as the first Phase 7 setup step, ahead of "Open the
> Implementation-Notes Record", in both phase-execution variants. A new
> status row would also require edits to `WORKFLOW_PHASE_GATE_IDS` in
> `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`,
> `AUTOPILOT_STAGE_PHASES` in `speckit-pro/speckit_pro_runner/helpers/read_only.py`,
> and the workflow template, and the roadmap's Key Files name only
> phase-execution and consensus-protocol.

**Alternatives offered:**
- New "Feedback Sweep" phase row: clearer for an operator reading the table,
  but touches the template, the guard's phase map, the stage resolver, and
  every status-table reader ART-014 audited; likely pushes the spec past its
  4-file budget.
- Opening preparation (Step 0.x): beside Step 0.6c, where the Draft PR row
  is already corroborated; earliest possible read, but opening preparation
  is read-only today and the sweep commits and pushes.

**User's answer:** Phase 7 setup step (Recommended)

---

### Q2. Which pull-request comment surfaces does the sweep read, and what counts as unresolved on each?

**Branch:** Input surfaces / unresolved semantics

**Recommended answer:** Review threads + PR-level comments
> Read review threads whose `isResolved` is false (the GraphQL
> `reviewThreads` shape the Copilot remediation loop in
> `references/post-implementation.md` and `speckit-resolve-pr` already
> query) plus PR-level conversation comments, where a pasted "Copy as
> Markdown" export most naturally lands. Verified against the live GraphQL
> schema: `PullRequestReviewThread` carries `isResolved`; `IssueComment`
> does not (it carries `isMinimized` and `reactions`), so the sweep's own
> processed-comment record decides "already handled" there.

**Alternatives offered:**
- Review threads only: one surface with a native unresolved flag and the
  simplest parse, but it misses the PR conversation box, the primary channel
  for exported markdown.
- Threads + PR comments + review bodies: most complete, but review bodies
  are a third shape with no state of their own and add fixture surface for
  little gain on a draft that no CI or Copilot review runs against.

**User's answer:** Review threads + PR-level comments (Recommended)

---

### Q3. This repository is public, so any GitHub account can comment on the draft PR, and the sweep routes comment text into agents that edit spec.md, plan.md, and tasks.md. Whose comments may the sweep act on?

**Branch:** Trust boundary / security

**Recommended answer:** OWNER / MEMBER / COLLABORATOR only
> Act only on comments whose `authorAssociation` is OWNER, MEMBER, or
> COLLABORATOR (write-capable accounts; the field exists on both
> `IssueComment` and `PullRequestReviewComment` in the live schema). Every
> other author's comment is listed in the report as "not swept: untrusted
> author" and never reaches consensus. `SECURITY.md` puts "prompt injection
> reaching a write or execute tool" in scope, and this is exactly that path.

**Alternatives offered:**
- Everyone who comments: simplest, matches private-repo intuition, but on a
  public repo an arbitrary account could steer planning-artifact edits
  through consensus.
- PR author only: tightest boundary, but it locks out a second maintainer
  reviewing the plan, which is the checkpoint's purpose on a team.

**User's answer:** OWNER / MEMBER / COLLABORATOR only (Recommended)

---

### Q4. After the sweep amends a planning artifact in response to a review thread, who marks that thread resolved?

**Branch:** Convergence / human confirmation

**Recommended answer:** The operator resolves
> The sweep never calls `resolveReviewThread`. The reviewer resolves a thread
> when satisfied with the amendment, which is the "human confirming plan
> changes" the roadmap's key decision names, and convergence is the clean
> re-run after they do. `speckit-resolve-pr` auto-resolves, but that loop
> serves post-implementation fixes, not a checkpoint.

**Alternatives offered:**
- The sweep auto-resolves after amending: thread count converges
  mechanically and re-runs re-read less, but the confirmation step
  disappears and an objecting reviewer has to reopen the thread.
- Sweep resolves only non-amending threads: less re-review noise, but two
  behaviors to explain and test.

**User's answer:** The operator resolves (Recommended)

---

### Q5. Does the sweep post a reply on the pull request for each comment it handles?

**Branch:** Outward writes / reviewer visibility

**Recommended answer:** One reply per handled comment
> For each swept comment, post one reply naming the class (amended,
> answered, deferred, no action), the artifact and section touched, and the
> amending commit. The reviewer sees the disposition where they wrote the
> comment, which is what lets them resolve the thread (Q4) without opening
> the workflow file. Precedent: the Copilot remediation loop and
> `speckit-resolve-pr` post one reply per thread via `gh api`.

**Alternatives offered:**
- No replies; dispositions only in the repo: zero outward writes and nothing
  public is written, but the reviewer must find the re-review report to
  learn what happened to each comment.
- One summary comment per sweep run: one write per run, but it detaches
  dispositions from the threads they answer, and a reviewer cannot resolve a
  thread from it.

**User's answer:** One reply per handled comment (Recommended)

**Notes:** The four classes named in the recommended answer (amended,
answered, deferred, no action) are carried forward as the sweep's
classification vocabulary; "amended" is the only class that routes through
consensus and produces a Consensus Resolution Log row.

---

### Q6. Where does the sweep record which comments it has already handled, so a re-run after re-review does not process them twice?

**Branch:** Durable record / idempotency

**Recommended answer:** Feedback Sweep Log table in the workflow file
> One row per handled comment: comment id, surface (thread or PR comment),
> author, class, disposition, commit. Amendments additionally get the
> Consensus Resolution Log row the roadmap mandates, linked by number. The
> workflow file is already the authoritative durable store (`Stage` row,
> `Draft PR` row, CRL), a re-run skips any id already logged, and
> `aggregate-crl`'s Round metric stays clean because answered or deferred
> items are not consensus resolutions.

**Alternatives offered:**
- Consensus Resolution Log rows only: one store and no schema addition, but
  answered, deferred, and no-action dispositions would pollute the Round and
  escape-rate metric `aggregate-crl` computes from that table.
- GitHub-side marker (the sweep's own reply): no repo record, but detection
  depends on reading replies back through `gh`, the record never reaches
  version history, and a run that cannot reach `gh` cannot know what was
  handled.

**User's answer:** Feedback Sweep Log table in the workflow file (Recommended)

---

### Q7. When a Draft PR row exists but the sweep cannot read the pull request (gh unreachable, or Step 0.6c reports pr_closed, pr_missing, or identity_mismatch), does the implement stage stop or proceed?

**Branch:** Error paths / checkpoint integrity

**Recommended answer:** Stop with a report
> A present Draft PR row means a checkpoint was opened, and proceeding
> without reading it would make the checkpoint silently optional. Stop before
> any task work, name the corroboration status and the resume path (make
> `gh` reachable, or fix or clear the row, then re-run), mirroring ART-007's
> three discrepancy stops in `references/phase-execution.md` §"What each
> corroboration status means at the terminal step". Only `no_record`
> proceeds, because no draft PR was ever opened and there is nothing to
> sweep.

**Alternatives offered:**
- Proceed with a recorded gap: fail open like artifact generation; keeps the
  stage moving, but feedback already left on the PR is ignored without the
  operator being asked.
- Stop on discrepancy, proceed when unreachable: separates a broken record
  from a flaky tool, though a flaky tool is exactly when unread feedback is
  most likely.

**User's answer:** Stop with a report (Recommended)

---

### Q8. When the sweep finds zero comments to act on, but spec.md, plan.md, or tasks.md changed after the draft artifacts were last generated (the prompt-export path, or a direct edit), what does the sweep do?

**Branch:** Prompt-export bypass / artifact staleness

**Recommended answer:** Regenerate, refresh, proceed
> Detect staleness from git history alone: any of the three planning files
> has a commit newer than the newest commit touching
> `specs/<feature>/artifacts/`. Re-dispatch the artifact-author, refresh the
> draft description, log it in the Feedback Sweep Log, and continue into
> Phase 7 without stopping, because the operator made those changes
> themselves and has nothing to confirm. This is the roadmap's "absent
> comment is not an absent opinion" sentence made operational, with no new
> record needed.

**Alternatives offered:**
- Regenerate, refresh, then stop for re-review: safer when someone other
  than the operator edited the planning files, at the cost of one extra run
  on every prompt-export loop.
- Do not detect; leave it to ART-010: smallest slice, but the draft PR keeps
  showing pages that no longer match the plan a reviewer is confirming.

**User's answer:** Regenerate, refresh, proceed (Recommended)

---

### Q9. After an amendment changes spec.md, plan.md, or tasks.md, which draft pages does the sweep regenerate?

**Branch:** Regeneration scope

**Recommended answer:** The whole draft set
> Re-dispatch the artifact-author exactly as the plan-stage terminal step
> does (`references/phase-execution.md` §"Artifact generation: the
> artifact-author dispatch"): the manifest selects the pages, every selected
> page is rewritten from the amended record, and the fail-open outcome list
> feeds the same three sinks. No page-to-source mapping to maintain, which
> is the YAGNI answer (constitution §VI) for a set of at most four pages.

**Alternatives offered:**
- Only pages whose source changed: fewer rewrites per run, but the mapping
  is a second copy of knowledge the author already holds, and it goes stale
  when a draft-stage entry is added to the manifest.
- Regenerate nothing; ART-010 rebuilds: smallest change, but the reviewer
  confirming the amendment sees pages that contradict it.

**User's answer:** The whole draft set (Recommended)

---

### Q10. The three exporting draft-pr templates write markdown with three different lead sentences and no shared machine-readable marker (implementation-plan.html:1443, code-approaches.html:1249, module-map.html:1218). How does the sweep recognize an artifact-exported markdown block inside a comment?

**Branch:** Comment-schema parse / export recognition

**Recommended answer:** Lead-sentence registry in the parser
> The read-only helper carries the three shipped lead sentences
> ("Objections recorded while reviewing this plan.", "The approach chosen
> while reviewing these options.", "Objections recorded while reading this
> module map.") and recognizes a block by its first line; anything else is an
> ordinary comment. No template edits, no payload regeneration, and the
> Layer 4 fixtures pin each lead. A future exporting template costs one added
> string.

**Alternatives offered:**
- Add a hidden marker to the templates' exports: exact and future-proof, but
  it edits three shipped templates plus their payload copies and cache
  proofs, which alone exceeds the spec's 4-file budget for a detection
  detail.
- Treat exports as ordinary comments: simplest parser, but the roadmap's
  comment-schema fixtures would have nothing to parse, and the per-phase
  anchors inside an export would be lost.

**User's answer:** Lead-sentence registry in the parser (Recommended)

---

### Q11. After amendments and regeneration, what does the sweep do to the draft pull request before it stops for re-review?

**Branch:** Re-review report / draft description

**Recommended answer:** Refresh the description through the existing path
> Run ART-007's create-or-refresh step: the Artifacts block re-indexes the
> regenerated pages and the Resume block states the sweep outcome (comments
> swept, amendments made, commit range, and that a re-run continues into
> implementation once threads are resolved). Refresh is the one mutation
> ART-007 permits on an existing draft (`references/phase-execution.md`
> §"When reviewability later splits the work"), so no new PR write path
> appears, and the stop report mirrors the plan-stage stop report's shape.

**Alternatives offered:**
- Leave the description alone: fewer writes, but the artifact index may name
  pages that were regenerated and the resume instructions point at the wrong
  next step.
- Flip the draft to ready: out of scope; the ready flip belongs to ART-010
  after implementation, and a ready PR starts every CI job against a
  plan-only branch.

**User's answer:** Refresh the description through the existing path (Recommended)

---

### Q12. The estimator returns 452 LOC / warn / 2 suggested slices for 3 user stories, 14 files (9 production across both platforms plus the helper's tests and fixtures), and 18 functional requirements, modify-weighted; production files alone give 352 / ok / 1. How should ART-008 be sized?

**Branch:** Slice sizing

**Recommended answer:** Split into 2 vertical slices
> Slice 1, the checkpoint: read both comment surfaces, trust filter, export
> recognition (helper plus fixtures), classify, consensus-amend, Feedback
> Sweep Log and CRL rows, per-comment replies, stop-or-proceed, and the
> unreadable-PR stop; amendments commit and push. Slice 2, artifact
> freshness: whole-set regeneration after amendments, stale-page detection
> on a clean sweep, and the description refresh. Each cuts end to end through
> both platform variants; slice 1's stop report says pages regenerate once
> slice 2 lands. Stacked in that order, like ART-003 and ART-005. The
> estimator's `suggested_slices` is 2, and the seam is a Path seam (SPIDR):
> the comment-driven path and the artifact-freshness path each deliver one
> working capability.

**Alternatives offered:**
- Keep as one spec, accept the warning: record 452 / warn and re-measure at
  the Plan phase; under the 800 stop, so permitted, and ART-007 shipped as
  one slice at 355. Risk: ART-006 declared 382 and shipped a warn-sized diff.
- Split along a different seam: by platform, or helper-plus-fixtures first
  and orchestrator prose second; both are by-layer splits, which the slicing
  guidance steers away from.

**User's answer:** Split into 2 vertical slices (Recommended)

---

`
separator convention: the block below opens with its own `---`, matching how
Q12 is separated from Q11.

---

### Q13. The trust-boundary review left F-1 and F-2 disclosed but not mitigated: the consensus analysts and the orchestrator read reviewer-derived text while inheriting the operator's full tool surface — `Bash`, `WebFetch`, `WebSearch`, and every installed MCP server — and a maintainer who quotes untrusted text launders it across the boundary. Should ART-008 mitigate them, and where?

**Branch:** Trust boundary / untrusted-text consumers

**Recommended answer:** Mitigate both inside this slice by scoping every agent that reads reviewer text
> Two new agents ship on both platforms and are used only by the sweep.
> `sweep-classifier` receives one sanitized, delimited body — the FR-007g
> output — plus the closed class vocabulary, and returns a structured record:
> a class from the four-value vocabulary, a target from the three-file
> allowlist or `null`, and a reason capped at 512 bytes that crosses the
> FR-012f redaction surface before the orchestrator uses it. Classification
> therefore leaves the orchestrator entirely, which is the point: the
> orchestrator holds `Bash`. `sweep-analyst` is dispatched three times per
> amended item with the perspective — codebase, spec-context, domain — given
> in the prompt, and once more for synthesis, so the shared analysts, their
> routing table, and `consensus-synthesizer` are all untouched; synthesis
> deliberately does **not** go to `consensus-synthesizer`, which inherits
> `Bash` and would reopen F-1 one hop downstream. Claude frontmatter pins
> `tools: Read` and `tools: Read, Grep, Glob` with `Agent`, `TeamCreate`,
> `SendMessage`, and `Skill` denied; Codex pins `sandbox_mode = "read-only"`,
> which is the only lever a Codex TOML has, and the claim stops at "read-only
> filesystem; network per Codex defaults" because no network field exists in
> the loader. `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`
> gains `UNTRUSTED_INPUT_CONSUMERS`, exempting exactly those two from the
> repository-wide no-`tools:` rule while pinning each one's allowlist exactly
> and the tuple's own membership exactly. Capability inheritance is right for
> an agent acting on trusted input and wrong for an agent reading
> attacker-controllable text, and that is the whole of the policy change: no
> existing agent definition is edited, so the twelve governed Layer 6
> definitions and their digest chain are untouched. Cost: production files go
> from 7 to 12, which crosses the 8-file block, and the reviewable midpoint
> goes to about 1420, which crosses the 800 block. Both are size-only and both
> are accepted on the record, with PRSG-013 as the precedent for a recorded
> block that continued.

**Alternatives offered:**
- Accept F-1 and F-2 as disclosed, where the third remediation pass left them:
  plan item 7 already states that an analyst holding `Bash` passes through none
  of the seven mechanisms, and the residual is recorded rather than called
  tolerable. Keeps the slice at 7 production files and one block instead of
  two. Cost: the boundary the design names is the one it does not build, and a
  disclosure has no fixture that can fail.
- Mitigate in a separate slice or a follow-up spec, deferring the scoped
  consumers behind slice 1. Risk: the consumers are what this feature
  dispatches, so slice 1 would ship the exposure and the fix would land after
  the thing that creates it — the same ordering problem the sweep's own
  checkpoint exists to prevent, one layer up.

**User's answer:** Mitigate both inside this slice by scoping every agent that reads reviewer text (Recommended)

---

TWO COUNT SITES IN THE SAME FILE, both required:
- Front matter :10 — `question_count: 12` becomes `question_count: 13`.
- Header :18 — `> **Questions asked:** 12` becomes `> **Questions asked:** 13`.

## Open Questions

- **What:** Commit granularity inside the sweep: one commit per amendment or
  one per sweep run, and whether the Feedback Sweep Log write is its own
  bookkeeping commit (the Draft PR row rule is "the separate bookkeeping
  commit, never the stage-boundary commit").
  **Why deferred:** Protocol-level detail below the interview's altitude;
  the contract (amendments committed and pushed, log in the workflow file)
  is fixed.
  **Suggested next step:** Clarify session 1; resolve against
  `references/workflow-file-protocol.md` during the plan phase.
- **What:** The new helper's name and envelope: which surfaces it reports,
  trusted and untrusted counts, per-comment class candidates, recognized
  exports with template id and anchors, and whether it also computes the
  stale-page verdict from git (other read-only helpers already run `git`
  through `subprocess` in `read_only.py`) or the orchestrator supplies that
  verdict as an input.
  **Why deferred:** Plan-phase design; the interview fixed the pattern
  (orchestrator takes the `gh` observation, helper classifies, fixtures pin
  it), not the envelope.
  **Suggested next step:** Plan phase, mirroring
  `resolve-autopilot-stage`'s `pr_observation` input and
  `corroborate_draft_pr`'s closed vocabulary.
- **What:** The exact Feedback Sweep Log column set, its placement in the
  workflow file (beside the Consensus Resolution Log), the CRL `Type` value
  for sweep amendments (for example `Sweep`), and how `aggregate-crl` treats
  that value.
  **Why deferred:** Column syntax is a workflow-file-protocol detail; the
  interview fixed the two-store contract (Q6).
  **Suggested next step:** Clarify session 1.
- **What:** The reply template per class, so fixtures can pin the wording and
  the text stays public-readable English (the repo's PR-body rule).
  **Why deferred:** Wording detail; the decision to reply per comment is
  fixed (Q5).
  **Suggested next step:** Plan phase; keep one fixed template per class.
- **What:** Whether an explicit operator override to skip the sweep is needed
  (for example after deliberately abandoning a draft PR), or whether "fix or
  clear the row, then re-run" is the only path.
  **Why deferred:** No concrete case surfaced; adding a flag is surface the
  roadmap does not ask for.
  **Suggested next step:** No flag in v1 unless Clarify finds a concrete
  case; record the resume path in the stop report instead.
- **What:** Whether exported markdown blocks arrive inside review threads as
  well as PR-level comments. The registry recognizes a block on either
  surface; the UAT should exercise both placements.
  **Why deferred:** Behavior is already covered by Q2 plus Q10; only the
  evidence is open.
  **Suggested next step:** UAT runbook: one export pasted as a PR-level
  comment, one pasted into a review thread.
- **What:** The blind-spot pass did not run (wait deadline expired), so the
  unknown-unknowns search relied on the operator-side grounding done during
  this interview (export leads, `isResolved` semantics, phase-row readers,
  `authorAssociation`). Hidden coupling in the refresh path
  (`helpers/pr_emission.py`) and the corroboration inputs
  (`resolve-autopilot-stage`) that the sweep reuses has not been searched
  independently.
  **Why deferred:** The pass fails open by design; scaffold does not retry.
  **Suggested next step:** Clarify session 2 should read both helpers' input
  contracts before the plan phase commits to the helper envelope.

## Recommended Next Step

Setup has already happened (this doc was produced inside
`/speckit-pro:speckit-scaffold-spec ART-008`). The scaffold continues:
populate `ART-008-workflow.md` from this doc, commit both, then hand off to
`/speckit-pro:speckit-autopilot docs/ai/specs/.process/ART-008-workflow.md
--stage plan`. Slice 2 is scaffolded on its own, from the slice 1 branch,
once slice 1's plan stage has opened its draft PR.

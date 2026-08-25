# Phase 0 Research: ART-008 slice 2 — Artifact Freshness

**Input**: `specs/art-008-feedback-sweep-slice-2/spec.md`,
`docs/ai/specs/.process/ART-008-slice-2-design-concept.md`

**Status**: No unresolved clarification marker remains. Three Clarify sessions closed
every question the design concept left open, and the spec's `## Clarifications`
section supersedes the design concept wherever the two differ. This file
consolidates the settled decisions, records where Clarify moved one, and
resolves the four questions Plan owned.

---

## Part 1 — The seven design-concept decisions, as they now stand

### D1. Staleness primitive: a git-history join

- **Decision**: Pages are stale when any `Feedback Sweep Log` row whose `Class`
  is `amended` names a `Commit` newer than the last commit touching
  `specs/<feature>/artifacts/`.
- **Rationale**: Slice 1 shipped the `Commit` column specifically as "the join
  key slice 2 uses to find which pages went stale". The join is deterministic,
  offline, and adds no state. Content hashing is ruled out by FR-002 for a
  concrete reason: the pages are agent-authored prose, so identical inputs
  produce different bytes and a content comparison would report every page stale
  on every run.
- **Alternatives considered**: A generation stamp written into each page (a new
  stamped contract on every template for marginal precision, and a change to
  the shipped gallery this slice puts out of scope). A pending-regeneration flag
  (a second store, which FR-003 forbids and slice-1's Q6 already refused).
- **Unchanged by Clarify.**

### D2. Partial-regeneration reporting: reuse ART-007's three sinks

- **Decision**: Every shortfall reaches the description's gap rows, the
  `Draft PR` row's note, and the run report. The sweep itself never writes the
  `Draft PR` row; the create-or-refresh path does, exactly as at plan stage.
- **Rationale**: The machinery already owns all three, and the row is
  "rewritten whole from the current run's outcome, every time", so a stale note
  cannot survive a later refresh that no longer fell short.
- **Alternatives considered**: Run-report-only (leaves the row's note describing
  an outcome that is no longer true). Stop-on-any-gap (stricter than ART-007's
  own fail-open precedent, and FR-023 forbids it).
- **Refined by Clarify**: FR-021 now names the substitution the Phase 7 call
  site forces. The shipped sink table's second sink is the plan-stage stop
  report, which does not exist here; the run report every leg already emits
  takes its place, on both the stop and the proceed legs.

### D3. Timing on the amended path: regenerate before the stop

- **Decision**: Same run, in order — amend, regenerate the whole set, refresh
  the description, stop for re-review.
- **Rationale**: The checkpoint's value is a human reviewing the current plan.
  Fresh pages are the point of the checkpoint, not a follow-up to it.
- **Alternatives considered**: Regenerate on the next run, which is the exact
  condition slice 1's promise sentence apologizes for.
- **Unchanged by Clarify.**

### D4. The regeneration commit: dedicated, `docs:` type, artifacts alone

- **Decision**: One commit staging `specs/<feature>/artifacts/` and nothing
  else, `docs` conventional-commit type.
- **Rationale**: It keeps amendment commits reviewable one by one, keeps the
  bookkeeping commit's workflow-file-path-alone rule intact, and makes the D1
  join exact — the last `artifacts/` commit **is** a regeneration, because
  nothing else can move it.
- **Alternatives considered**: Folding it into the bookkeeping commit or the
  last amendment commit. Both break an existing rule or blur the join.
- **Extended by Clarify**: FR-018 adds the non-emptiness rule (no commit when
  regeneration produced no change, because an empty commit cannot move the
  join). FR-019a moves the push **inside** the step. FR-039 adds a third,
  separate commit shape for a changed `Draft PR` cell, reusing the plan-stage
  terminal step's own record commit verbatim.

### D5. Whole-set semantics: re-select from the manifest

- **Decision**: Re-select the draft-stage page set from the shipped gallery
  manifest evaluated against the amended planning record; author every selected
  page fresh; remove a page on disk that re-selection no longer names, and
  report the removal.
- **Rationale**: The manifest "is the routing's source of truth and it grows".
  Regenerating the on-disk set would mean a newly warranted page never appears.
- **Alternatives considered**: Regenerate the on-disk set. Re-select but never
  remove (carries pages the manifest no longer justifies, linked from the
  description as though they were current).
- **Extended by Clarify**: FR-012a makes the removal set the output of a second
  named surface of the same helper registration — a deterministic set
  difference rather than an orchestrator judgment — and pins that a `gap`
  outcome still counts as selected, so a page that failed to author is never
  removed for that reason alone.

### D6. Where the staleness decision lives: a read-only runner helper

- **Decision**: A deterministic read-only runner helper with Layer 4 fixtures,
  mirroring slice 1's `sweep-pr-feedback` observation-in / verdict-out shape.
- **Rationale**: The one deterministic decision in the slice would otherwise be
  untestable prompt behavior, which is the exact class slice 1 moved into a
  helper.
- **Alternatives considered**: Orchestrator prose only.
- **Moved by Clarify, and this is the largest of the three moves.** The design
  concept said "the orchestrator gathers the observation (last `artifacts/`
  commit, Feedback Sweep Log rows, ancestry facts) and passes it as data".
  Clarify session 1-2 changed the first of those three: **the helper reads the
  `amended` rows from the workflow file itself**, through the same
  heading-anchored table read the sweep already ships, rather than receiving
  parsed rows. Only the facts it cannot derive from that one file — git ancestry
  and artifacts-directory state — arrive as supplied data (FR-004, FR-004a).
  Two reasons were recorded: it completes the mirror of the shipped sweep helper
  (path input, in-helper table read, network-sourced observation as data), and
  it lets FR-031's fixture-reuse mandate apply literally. A second move landed
  in the same session: the page set the helper returns is the pre-regeneration
  on-disk inventory it was given, echoed — selection stays with the emission
  machinery, not the helper.

### D7. The report interface: outcome lines

- **Decision**: Per-page outcomes (`generated`, `gap` with a reason, `removed`),
  the regeneration commit's sha, and whether the description refresh succeeded.
  On a clean sweep with fresh pages, one line saying the pages are current as of
  the named commit.
- **Rationale**: A static sentence is false on gap runs; dropping the sentence
  leaves a gap unreported, contradicting D2.
- **Extended by Clarify**: FR-024 pins **where** the lines land — the run
  report's what-already-landed part, extending that closed enumeration once in
  the shared report-shape section rather than in the amended-leg bullet, because
  FR-016 runs the evaluation on every leg. FR-005a adds the `undeterminable`
  report shape, which is report-only and reaches the run report alone.

---

## Part 2 — The four questions Plan owned

### Q-A. Which runner-helper registration hosts the reused six-status classifier?

- **Decision**: A **third named surface of the new
  `check-artifact-freshness` registration**, called `corroborate_refresh`.
- **Rationale**: FR-033a leaves the registration to Plan and pins only that the
  vocabulary, precedence, and observation-as-data contract are shared rather
  than re-derived. The shipped classification function `corroborate_draft_pr`
  (`speckit-pro/speckit_pro_runner/helpers/read_only.py:1411-1466`) is already
  pure and standalone: it takes a `Draft PR` row and one supplied observation
  and returns a five-key record, touching no global state and running no tool.
  Its one file input is the `Draft PR` row, which `workflow_draft_pr_row`
  (`:1274-1297`) reads from the workflow file — the same single path FR-004
  already permits this registration. Hosting the reuse here therefore keeps the
  whole registration's read boundary at exactly one path.
- **Alternatives considered**:
  - *Reuse `resolve-autopilot-stage`.* Rejected. Its request requires
    `autopilot_args` and a parseable `## Workflow Overview` table, and it exits
    2 with a one-line diagnostic when either is malformed (`:1487-1505`). The
    refresh call site has no argv and must never turn a bad request into a
    run-stopping exit, because FR-035 requires a failure there to end the
    refresh attempt only. Its envelope also carries six stage-resolution fields
    that are noise at this call site.
  - *A fourth registration of its own.* Rejected under the constitution's KISS
    principle. It would duplicate the allowed-inputs entry, the dispatch entry,
    the registry entry, the fixture-manifest row, and the request fixture, to
    host roughly forty lines of wiring.

### Q-B. How is the `Commit` cell extracted safely?

- **Decision**: **Dual anchoring.** Columns at or before `Disposition` are read
  by header index from the **left**; columns after it are read by negative
  offset from the row's **end**. Both offsets are derived from the header row
  rather than hard-coded.
- **Rationale**: `sweep_table_cells` (`read_only.py:1594`) splits a row on the
  bare pipe with no escape handling. Slice 1's protocol requires the free-prose
  `Disposition` cell to escape a pipe as `\|`, which renders correctly in
  Markdown but still splits under this reader: `a\|b` yields `a\` and `b`. One
  pipe in a disposition therefore shifts every column to its right by one, and a
  left-anchored `Commit` index would silently read the wrong cell — in the
  direction that reads a stale page set as current. `Commit` and `CRL #` are the
  last two header columns and neither can carry a pipe (a sha and a row number),
  so right-anchoring is exact.
- **Alternatives considered**: Unescaping `\|` before the split. Rejected: it
  would fork the shipped reader's behavior, and FR-004 requires the same table
  read the sweep already ships rather than a second independent parser. Rejected
  also because it fixes only correctly-escaped rows and still mis-reads a
  hand-edited one.
- **Boundary rule**: a data row with **fewer** cells than the header is
  malformed, its `Commit` is unreadable, and the row is undeterminable under
  FR-006. A row with **more** cells is the ordinary pipe-in-disposition case and
  must not be reported as an error.

### Q-C. Which Codex sentences land verbatim and which are summarized?

- **Decision**: The Codex mirror carries the same behavior in Codex-native
  terms, at the measured 83% length ratio. **No Codex `SKILL.md` change.**
- **Rationale**: Measured with the Layer 1 validator's own `_body` helper, the
  Codex autopilot skill body is **7998 of its 8000-word cap** — two words of
  headroom — and FR-030 permits adding to it only after words are freed. Nothing
  here needs to be added: FR-033b's second scoping edit binds the literal phrase
  "one read-only observation per run", which occurs exactly once in the tree, at
  `speckit-pro/skills/speckit-autopilot/SKILL.md:372`. The Codex skill's
  parallel wording (`codex-skills/speckit-autopilot/SKILL.md:596`) already sits
  inside the Step 0.6c bullet and makes no unqualified per-run claim, so it
  already carries the scoping FR-033b asks for.
- **The two real Codex constraints**, both measured:
  1. `CLAUDE_ONLY_RUNTIME_RE`
     (`tests/speckit-pro/layer1-structural/validate-codex-skills.py:59-62`)
     runs over the **concatenated** Codex runtime documents — skill body plus
     `phase-execution-codex.md`, `post-implementation-codex.md`, and
     `error-recovery-codex.md` (`:244-252`, `:368-372`). It rejects
     `TaskCreate`, `TaskUpdate`, `Agent(`, `Bash(`, `Opus-class`, `Opus 4.6`,
     `/model opus`, `/effort max`, `/speckit.` and `/speckit:`,
     `run /<command>`, and `general-purpose agent`. The regeneration step is a
     subagent dispatch, so the Claude prose carries an `Agent(` block and the
     Codex mirror must describe the same dispatch without that literal.
  2. Three pinned strings must survive in `phase-execution-codex.md`:
     `estimate-reviewable-loc`, `over_budget`, `not_estimated` (`:386-395`).
     None sits in the edited region, but the assertions are file-wide.
- **Alternatives considered**: Adding the freshness behavior to the Codex
  `SKILL.md` body after freeing words elsewhere. Rejected: FR-030 states the
  preference plainly and the references are where the sequence already lives.

### Q-D. How is the budget sized, given the estimator's false zero?

- **Decision**: Hand-derived from this plan's own Declared File Operations
  block, anchored line by line on measured shipped clusters, with slice 1's
  realized density recorded as a separate risk band.
- **Rationale**: `estimate-reviewable-loc` recognizes a file as production only
  under `src/`, `app/`, `lib/`, or `scripts/`, or by a JavaScript, TypeScript,
  or SQL extension. Every production path in this slice fails both tests, so the
  helper returns `production: 0`, `projected: 0`, `status: pass` — an **absent
  measurement**, not a passing one. The verbatim output is quoted in `plan.md`.
- **Alternatives considered**: Citing the estimator's `pass`. Rejected for the
  reason above, which slice 1's plan already recorded and which the design
  concept's blind-spot finding 3 flagged forward to this slice.
- **Result**: 556–825 production-only, midpoint ~690. One warn, no block. The
  split lever is derived and rejected in `plan.md`.

---

## Part 3 — Carried from slice 1, not re-opened

- A clean sweep with stale pages regenerates, refreshes, and **proceeds** — no
  stop (FR-017).
- Regeneration is whole-set, refined by D5's re-selection semantics.
- The description refreshes through ART-007's create-or-refresh path. A draft
  description is fully fingerprint-protected with no editable region, so the
  refresh rewrites it whole through the same draft-mode packet path.
- Slice 1's SC-008 stands: the sweep's replies are **not** weakened on the
  assumption that the refreshed description now carries the information.
- Slice 1's bookkeeping-commit rule is untouched (FR-020). A leg that logs no
  `Feedback Sweep Log` and no `Consensus Resolution Log` row still writes no
  bookkeeping commit, and the dedicated artifacts commit is not that commit.

## Part 4 — Open items carried to post-implementation, not to Plan

The design concept left one item that Plan does not resolve and does not need
to: **the UAT shape for the end-to-end loop.** The sweep's consensus routing is
prompt-level with no automated eval, so end-to-end evidence lands in the spec's
UAT, and what a manual UAT can exercise before a release refreshes the installed
plugin mirrors slice 1's own limit. The discharge path is recorded in the
workflow file's post-implementation checklist rather than re-litigated here.

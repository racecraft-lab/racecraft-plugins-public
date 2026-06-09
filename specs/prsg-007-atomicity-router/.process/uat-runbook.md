# UAT Runbook: prsg-007-atomicity-router

| Field | Value |
|-------|-------|
| Spec | prsg-007-atomicity-router |
| Branch | prsg-007-atomicity-router |
| PR | **PR:** #133 |
| Generated from | 2026-06-09T02:39:41Z |



## Env Setup

The thing under test is a single committed, executable bash script — there is **nothing
to build or install**. You only need a shell.

1. **Prerequisites:** `bash` **and `jq`** on your PATH. `jq` is **required** — the script
   builds every JSON object it prints (both the success object and the error object) with
   `jq`, so it will not run without it. (Piping the output to `| jq .` for pretty-printing
   is the only optional extra.)
2. **Where to run:** all commands below are run from the worktree root —
   `.worktrees/prsg-007-atomicity-router/`. Open a terminal there.
3. **The one command you'll repeat:** every acceptance test runs the classifier against a
   directory and reads the JSON it prints:

   ```bash
   bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh <feature-dir>
   # add `| jq .` on the end for pretty output
   ```

4. **Automated backstop (informational, optional):** the full suite that backs this runbook
   is `bash tests/speckit-pro/run-all.sh --layer 4` (the classifier's 81-assertion unit test)
   and `bash tests/speckit-pro/run-all.sh --layer 1` (structural validation). Both pass today
   (962/962 and 887/887). You do **not** need to run these to do UAT — they're listed so you
   know the behavior below is already test-locked.

## Per-Story Acceptance Tests

Each step is a copy-paste command followed by the exact thing to look for in the output.
All inputs are the ready-made fixtures under
`tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/`. Let `R=` that path to keep
the commands short:

```bash
R=tests/speckit-pro/layer4-scripts/fixtures/atomicity-route
S=speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh
```

<a id="us-1"></a>
### User Story 1 - Atomicity classifier emits a route (Priority: P1)

A change that genuinely splits into independent additive pieces should be routed to
`split-PR`; a change with no clean seam should NOT be split; an empty work-list is
`out-of-scope`.

- [ ] **1.1 — additive multi-seam → split.** Run: `bash $S $R/additive-multi-seam`
      Expect `.route` = **`split-PR`** and `.signals` contains **`change-shape:additive-multi-seam`**.
      (Exact output: `{"route":"split-PR","releasable":true,"signals":["change-shape:additive-multi-seam"],"hints":[],"warnings":[]}`)
- [ ] **1.2 — single additive seam → not split.** Run: `bash $S $R/single-additive-seam`
      Expect `.route` = **`one-navigable-PR`** (a non-split route) and `.signals` empty.
- [ ] **1.3 — modify-heavy → one navigable PR.** Run: `bash $S $R/modify-heavy`
      Expect `.route` = **`one-navigable-PR`**, `.signals` contains **`change-shape:modify-heavy`**,
      `.releasable` = **`true`**, `.warnings` = **`[]`**.
- [ ] **1.4 — empty work-list → out of scope.** Run: `bash $S $R/out-of-scope-empty`
      Expect `.route` = **`out-of-scope`** (an empty/missing `tasks.md` short-circuits here, and
      this is a SUCCESS — exit code 0, not an error).
- [ ] **1.5 — abstain never auto-splits.** Confirm that in steps 1.2–1.4 the route is NEVER
      `split-PR` unless a real additive multi-seam was present (1.1). The classifier abstains
      to `one-navigable-PR` when uncertain; it never guesses a split.

<a id="us-2"></a>
### User Story 2 - Hard-atomic override and releasability warning (Priority: P1)

A change that CANNOT be safely split (a hard-atomic signature) must be forced to
`single-atomic-PR`, beating any split signal; and changes that a green CI run can't prove
safe (destructive migrations, concurrency) must be flagged `releasable:false` with a warning.

- [ ] **2.1 — exported-symbol rename → atomic.** Run: `bash $S $R/hard-atomic-rename`
      Expect `.route` = **`single-atomic-PR`**, `.signals` contains **`hard-atomic:exported-symbol-rename`**.
- [ ] **2.2 — global version pin → atomic.** Run: `bash $S $R/hard-atomic-version-pin`
      Expect `.route` = **`single-atomic-PR`**, `.signals` contains **`hard-atomic:global-version-pin`**.
- [ ] **2.3 — mutual-exclusion / auth / payment primitive → atomic.** Run: `bash $S $R/hard-atomic-mutual-exclusion`
      Expect `.route` = **`single-atomic-PR`**, `.signals` contains **`hard-atomic:mutual-exclusion-primitive`**.
- [ ] **2.4 — out-of-tree contract break → atomic.** Run: `bash $S $R/hard-atomic-out-of-tree-contract`
      Expect `.route` = **`single-atomic-PR`**, `.signals` contains **`hard-atomic:out-of-tree-contract-break`**.
      (These fixtures also contain seams; the hard-atomic override is what you're confirming — it beats the split.)
- [ ] **2.5 — destructive migration → atomic AND not releasable.** Run: `bash $S $R/hard-atomic-destructive-migration`
      Expect `.route` = **`single-atomic-PR`**, `.releasable` = **`false`**, `.signals` contains BOTH
      **`hard-atomic:destructive-migration`** and **`releasability:destructive-migration`**, and `.warnings`
      contains exactly: `destructive migration: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)`.
- [ ] **2.6 — concurrency-sensitive → not releasable (orthogonal to route).** Run: `bash $S $R/concurrency`
      Expect `.releasable` = **`false`**, `.signals` contains **`releasability:concurrency`**, and `.warnings`
      contains exactly: `concurrency-sensitive change: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)`.
      Note the route here is `one-navigable-PR` — releasability is flagged INDEPENDENTLY of the route.

### Error path & dogfood (both stories)

- [ ] **E.1 — bad input errors cleanly.** Run: `bash $S /no/such/dir; echo "exit=$?"`
      Expect a top-level **`{"error": ...}`** object, **NO `.route` key**, and **`exit=2`**.
      Run `bash $S` with no argument → `{"error":"Usage: atomicity-route.sh <feature-dir>"}`, `exit=2`.
- [ ] **D.1 — dogfood: the router does not misfire on its own vocabulary.** Run:
      `bash $S specs/prsg-007-atomicity-router`
      Expect a **non-split** route (`one-navigable-PR`) and `.releasable` = **`true`**, with NO
      `hard-atomic:*` and NO `releasability:*` tokens — even though this spec's own docs use words
      like "rename", "lock", "auth", "concurrency" as vocabulary. (The three advisory `hints[]`
      entries that DO appear here are expected and harmless — they are advisory only.)



## FR Coverage Matrix

Each user-visible requirement mapped to the acceptance step that exercises it.

| Requirement | What it promises | Covered by |
|-------------|------------------|------------|
| FR-003 | Empty/missing `tasks.md` short-circuits to `out-of-scope` (a success, not an error) | Step 1.4 |
| FR-004 / FR-005 | `tasks.md`-shape + additive-vs-modify detectors drive the route | Steps 1.1, 1.3 |
| FR-006 / SC-005 | Uncertain → abstain to `one-navigable-PR`; never auto-split | Steps 1.2, 1.5 |
| FR-007 / SC-003 | Any hard-atomic signature forces `single-atomic-PR`, overriding split | Steps 2.1–2.5 |
| FR-008 / SC-004 | Destructive-migration & concurrency → `releasable:false` + the exact canonical warning | Steps 2.5, 2.6 |
| FR-009 | Otherwise `releasable:true` and `warnings:[]` | Steps 1.3, 2.1–2.4 |
| FR-010 | The three contextual probes are advisory `hints[]` only — they never change the route | Step D.1 (hints present, route unaffected) |
| FR-011 / FR-011a / FR-011b | One flat JSON object; closed 9-token vocabulary; `signals[]` ∩ `hints[]` = ∅ | Every step (output shape) |
| FR-012 / SC-006 | Bad input → `{"error":…}`, exit 2, no `.route` key; read-only (writes nothing) | Step E.1 |
| FR-001 / SC-008 | `branch-by-abstraction` is reserved and **never** emitted by the MVP | Every step — confirm no run ever prints it |
| SC-001 / SC-002 | Exactly one route per success; `split-PR` only on a proven additive multi-seam | Steps 1.1 vs 1.2 |
| SC-007 | The behavior above is locked by the automated suite | Env Setup backstop (Layer 4 + Layer 1 green) |


## Negative-Path Tests


- **Unreadable or missing input**: The classifier reports a usage/input error (non-success
  exit status, never a block) only for genuine read failures: (a) the feature directory is
  absent or unreadable, or (b) a *present* input file (`tasks.md`, `plan.md`, or `spec.md`)
  cannot be read. A **missing or empty `tasks.md` is NOT an error** — it short-circuits to
  the `out-of-scope` route with a success exit (see "Conflicting signals / precedence" below
  and FR-003), because absence of tasks means there is nothing in scope to classify, not that
  the input could not be read. A merely-*absent* (not unreadable) `plan.md` or `spec.md` is
  likewise tolerated: the detector that would read it degrades gracefully (it contributes no
  signal), so absence of an optional artifact never errors or blocks. Only a file that is
  present-but-unreadable is a read failure.
- **No discernible signal at all**: When none of the detectors find a decisive signal, the
  classifier abstains to the default route `one-navigable-PR` — it never auto-splits and
  never blocks.
- **Conflicting signals / precedence**: Precedence is total and ordered: (1) input shape — a
  missing/empty `tasks.md` yields `out-of-scope` before anything else; then, among changes
  that have a `tasks.md`, (2) a hard-atomic signature wins and yields `single-atomic-PR`,
  overriding any split-PR signal; then (3) a proven additive multi-seam change yields
  `split-PR`; otherwise (4) the change abstains to `one-navigable-PR`.
- **Change is entirely outside the governed scope**: When the change does not fit any
  splittable or atomic category the router governs, it emits the `out-of-scope` route so
  the autopilot can fall back to its default single-PR behavior.
- **Contextual probe signal present but shallow**: When a flag-system, release-cadence, or
  consumer-locality signal is detected, it is surfaced only as an advisory hint and does
  not, on its own, force a split — the three fully-implemented detectors decide the route.
- **Advisory probe cannot run / errors internally**: An advisory probe that cannot run or
  fails internally degrades silently — it emits no hint and MUST NOT produce a failure, a
  non-success exit, or a block. An empty `hints[]` is a normal successful outcome; advisory
  probes can never change the success/error outcome (only the three decisive detectors and
  the input-shape check can), so no input can cause the classifier to block (FR-010, FR-012).

## Self-Review Findings

**Verdict: SHIP** (independent fresh-eyes review, separate context from the implementer).
Zero phantom task completions (all 30 backed); no defect at MEDIUM or above. All 10
per-class fixtures, the dogfood self-check, the error path, and the FR-007a keyword
firewall were verified by running the script directly. Two LOW items: an out-of-tree
detector comment that overclaimed a second (unimplemented) trigger — **fixed** in this
branch; and in-spec advisory-hint self-firing on the dogfood (a note, not a defect).

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

# Contract: Chain Hand-off and Closing Report

**Documentation only.** This contract ships no code. It fixes the pre-chain
check, the confirmation, the invocation form, and the closing report's layout, so
the two `SKILL.md` variants can be written as transcription and reviewed against
a specification.

Scope: FR-012 through FR-020, plus FR-022's three Codex amendment sites.
Upstream normative source: the ART-006 chain contract, recovered at
`git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md`
and its sibling `contracts/stage-invocation.md`.

## 1. Placement

The chain sits **after Step 8**, once the design concept, the workflow file, the
SPEC-MOC marker, and the roadmap status flip are all committed and pushed (Q9,
FR-012).

Placing it earlier is rejected for a stated reason: a chained planning stage that
fails or is interrupted must never leave the roadmap claiming the spec is still
Ready.

| Platform | Where the chain and closing report go |
|---|---|
| Claude | New `### 9. Chain into the Planning Stage` and `### 10. Closing Report`, appended after Step 8. The existing `## Scaffold Complete` report stays inside Step 7, ahead of Step 8 |
| Codex | The existing `## Output` section is top-level and already follows Step 8, so the chain and closing report **extend that section** rather than becoming new numbered steps |

FR-016 is the requirement both arrangements satisfy: the existing report prints
**before** the confirmation, so the operator is told what scaffold produced before
being asked whether to continue. A confirmation offered with no context is not a
real choice (Q5).

## 2. The FR-013a pre-chain check — run before asking, on both platforms

Two read-only tests. Both must pass. If any part fails, scaffold **must not ask**
and must print the hand-off command instead.

**Test 1 — rooting. Use the guard's own predicate, not an equivalent-looking
one.** Taken verbatim from the Codex autopilot's Workflow Worktree Binding guard
at `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md:21-45`:

1. Resolve the current checkout with `git rev-parse --show-toplevel`.
2. **Does the supplied workflow path resolve inside that checkout?**

**Test 2 — cleanliness.** `git status --porcelain` is clean in that checkout.

**Why the guard's own predicate rather than a root comparison.** A stale
same-named workflow file sitting in the parent checkout passes a naive root
comparison *and* passes the guard, so the guard continues and planning phases run
with commits landing in the parent checkout, usually `main`. Testing path
resolution rather than root identity is what makes scaffold's check and the
guard agree by construction, so the two can never disagree.

**What the check must NOT test**: the most recent commit. After Step 8 the newest
commit is the roadmap status flip rather than the workflow-file commit, so a
last-commit test would fail on every correct run (FR-013a).

**No new machinery** (FR-023): both commands already run at Step 3.5 of both
variants.

## 3. Per-platform chain condition

| Platform | Condition |
|---|---|
| **Codex** | Attempt the chain **only** when the FR-013a check passes. Otherwise ask nothing at all and print the hand-off command (FR-015a) |
| **Claude** | Unconditional beyond FR-013a (FR-015b) |

**Why Codex differs.** A Codex task's workspace root is fixed when the task
starts and cannot be changed from inside the session, and a scaffold run
necessarily begins before the worktree exists. The ordinary Codex session is
therefore rooted at the parent checkout. Attempting the chain from there is not
merely inelegant: the fail-closed Workflow Worktree Binding guard stops before
any mutation, turning the single confirmation into a false promise; or, with a
stale same-named workflow file in the parent checkout, the guard continues and
commits land in `main`.

**The Codex condition is not dead code.** Re-scaffolding through the
existing-worktree reuse path starts a session that is already correctly rooted,
and the chain then fires exactly as it does on Claude (US3 scenario 7).

**Why Claude still needs FR-013a.** Claude's autopilot ships **no**
worktree-binding guard, so a mis-rooted Claude chain would resolve silently
against the parent checkout rather than stopping. FR-013a is what closes that gap
on this platform, and it is the reason the check is required on both rather than
only on Codex.

On Codex the printed hand-off is the **ordinary** outcome, not a degraded one.

## 4. The confirmation — exactly one, structured

| Platform | Mechanism |
|---|---|
| Claude Code | `AskUserQuestion` |
| Codex CLI | `request_user_input`, when present |

**Question text**: `Scaffold is complete and pushed. Start the planning stage now?`

**Options, two, mutually exclusive, in this order**:

1. `Start planning (Recommended)`
2. `Stop here`

Recommending the forward option follows the house convention that the recommended
answer comes first. Declining is fully non-destructive, because everything
scaffold owns is already committed and pushed, so recommending the cautious
option would fight the spec's own purpose for no safety return.

**Companion edit, Claude only (FR-013)**: the existing closing line of the
`## Scaffold Complete` report must be softened from **"Review both files first"**
to **"Review both files"**, so the report and the confirmation stop giving
opposite instructions. That line has no Codex equivalent.

**Prohibitions** (FR-015b): scaffold must **not** fall back to parsing a
free-text reply, and must **not** chain by default when confirmation is
unavailable.

**Confirmation budget** (SC-007): outside the interview, a scaffold run asks for
**at most one** confirmation, and for **exactly one** whenever the chain is
attempted. It asks **none** when the FR-013a check fails, which on Codex CLI is
the ordinary case.

## 5. Invocation on acceptance

The workflow file path is the **sole** hand-off token (ART-006 §1, FR-014).
Scaffold must not pass a state file, branch name, feature directory, or
environment variable across the boundary.

| Platform | Runnable invocation |
|---|---|
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan` |
| Codex CLI | `$speckit-autopilot <workflow-file> --stage plan` |

**Note on the Codex form.** ART-006 §3's table shows the Codex row as
`<workflow-file> --stage plan`, with no leading token. `stage-invocation.md` §1
explains why: each distribution's documented argv *begins at the workflow path*,
and the leading command token "has no Codex counterpart" as a parity concern.
Read literally, that table would produce a chain invoking a bare path. The
runnable line prefixes the argv with the Codex skill invocation form,
`$speckit-autopilot`, which is what the whole Codex skill set already uses. The
argv itself is unchanged from the contract.

**Stage token**: the literal lowercase `plan`, from the contract's closed
vocabulary of `plan`, `implement`, `full`. No aliases, no alternate casing, no
long-form spellings.

Passing `--stage plan` is explicitness rather than necessity: ART-006 §3 notes
that a caller omitting the flag reaches the same answer by auto-detection on a
freshly scaffolded file. It is passed anyway, per the design concept's recorded
decision.

## 6. Decline, and the three no-chain paths

Scaffold must not chain, and must print the hand-off command instead, in all
three of these cases (FR-015):

1. The operator declines.
2. No structured confirmation mechanism is available in the session.
3. The FR-013a pre-chain check fails.

In every case **nothing is rolled back**. Everything scaffold owns is already
committed and pushed, so the operator loses one command and no work.

On Codex, case 2 is defensive rather than ordinary: `request_user_input`
availability is already a hard prerequisite of the interview step, which stops
the run when the feature is not enabled.

## 7. The three Codex sites that contradict the chain

All three **must be amended, not worked around** (FR-022). None is string-pinned
by a validator (research.md R6), so all three are safe to edit.

| Site | Current text | Amendment |
|---|---|---|
| Hard Constraint | `Do not run the autopilot at the end. Setup stops once the workflow is ready, committed, and pushed.` | Becomes **conditional on the session's rooting** rather than absolute |
| `## Output` next step | `the exact next step: start a new Codex task rooted at that worktree, then run $speckit-autopilot ...` | Gains the conditional chain while **keeping** its new-task guidance for the ordinary case |
| `## Output` prohibition | `Never hand off only the inner workflow path from the parent checkout. Do not suggest running autopilot from main, a detached checkout, or any workspace root other than the generated spec worktree.` | **Both sentences kept verbatim**, merely prefaced to apply when the chain does not fire |

The third is kept verbatim because it guards the real hazard this requirement
exists to respect. It is prefaced, never rewritten.

## 8. The closing report

**One report, rendered once the chain resolves**: after the planning stage on
acceptance, immediately on decline (Q5, FR-017). It is **printed, not written to
a file** (FR-017).

**Contents, closed at four elements, in this order** (FR-018):

```text
## Planning Complete        (or: ## Stopped Before Planning)

**Outcome:** <one line>
**Draft PR:** none, because draft-PR creation is not part of this release

**Artifacts:**
- <repo-relative path>     (one line each; only paths that exist)

**Next step:** <one command>
```

**The set-aside findings count MUST NOT appear here.** The list is closed at four
elements. That count lives in the design concept's header record (FR-010) and in
the seeded block (FR-008), and the artifact index points at the file carrying it.

### 8.1 The draft-PR line

Show the URL when the run produced one. Otherwise state plainly that there is
none, in the shape `Draft PR: none, because draft-PR creation is not part of this
release`.

Never omit the line silently. Never fabricate or guess a URL (Q1, SC-008). For
every run in this release, "none" is the expected outcome, because draft-PR
creation is ART-007.

### 8.2 The artifact index

Enumerate what the run **actually produced** (Q20, FR-018): the scaffold-owned
artifacts plus whatever the planning stage wrote, including the conditionally
produced research artifact, contract artifacts, and the checklist domains this
spec chose.

**It must not print a path that does not exist, and must not omit an artifact
that does** (SC-009). The set genuinely varies per spec, so a derived index stays
true where a fixed list would not.

### 8.3 The decline case

When the operator declines and no planning-stage artifacts exist:

- the outcome line states that the run stopped **at the operator's request** and that **nothing was rolled back**;
- the index lists **only** the scaffold-owned artifacts and the pushed branch;
- the next step is the hand-off command.

## 9. Completion is read from the workflow file

When the chained planning stage fails, stalls, or is interrupted, completion is
determined **by reading the workflow file**, with no live session and no state
file (ART-006 §4, Q10, FR-019).

**The completion test, two conditions, both in the one artifact:**

1. Every planning-phase row in `## Workflow Overview` — Specify, Clarify, Plan, Checklist, Tasks, Analyze — carries a terminal status.
2. A `G6.5` confidence-gate verdict is recorded in the file.

**The `Stage` row is corroborating, not the test.** ART-006 §4 is explicit: the
`Stage` entry records what was *resolved*, not what *completed*, so a file showing
`Stage: plan` with Tasks still pending is a run in flight, not a finished one.

**The report must name which planning phases reached a terminal status, and must
give the resume command** (FR-019).

### 9.1 Terminal-status vocabulary — read, never re-declared

The vocabulary is owned by the shipped `WORKFLOW_TERMINAL_STATUSES` frozenset in
`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`.

**Neither platform variant may re-declare the six status literals** (FR-020,
ART-006 §4). Any appearance elsewhere is a readability copy, not a source. For
reference only, the shipped set is `Complete`, `✅ Complete`, `Skipped`,
`✅ Skipped`, `⏭ Skipped`, `⏭️ Skipped` — the last two being U+23ED with and
without the variation selector, which render alike.

The reuse case is the same read: a worktree or branch reused from an earlier
scaffold run with a partially complete workflow file is evaluated by terminal
status on every planning row plus a recorded confidence-gate verdict, from the
file.

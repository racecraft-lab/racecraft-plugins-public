# Contract: Chain Hand-off and Closing Report

> **Amendment, 2026-08-13 — the chain became a hand-off, so this contract's
> fixed strings changed.** Scaffold cannot invoke the autopilot: on Claude Code
> that skill carries `disable-model-invocation: true`
> (`speckit-pro/skills/speckit-autopilot/SKILL.md:11`), documented as "Only you
> can invoke the skill" and set deliberately in `73dcbcc7`; on Codex CLI a skill
> body invoking a sibling skill mid-session is unverified. Both variants now
> print the command and the operator runs it. The shipped strings this document
> fixes changed accordingly, and the shipped `SKILL.md` files are authoritative
> where they differ from the sections below:
>
> - §2's check no longer gates the hand-off. It selects the hand-off's form.
> - §3's per-platform chain condition is **void**: neither platform chains.
> - §5's "invoke on acceptance" is now "print on every ending".
> - §6's three no-chain paths are now the three ordinary endings.
> - §8's heading vocabulary collapses from three values to the single fixed
>   string `## Ready for Planning`, and the artifact index's planning-stage
>   candidate group is removed, because no planning stage runs before the report.
> - §9's completion test is **void**: it read the result of a chained planning
>   stage, and none runs inside a scaffold session.
>
> §1, §4, and §7 stand unchanged. Sections are retained rather than deleted so
> the amendment is auditable against what the run originally decided.

**Documentation only.** This contract ships no code. It fixes the pre-chain
check, the confirmation, the invocation form, and the closing report's layout, so
the two `SKILL.md` variants can be written as transcription and reviewed against
a specification.

Scope: FR-012 through FR-020, including FR-015c, plus FR-022's three Codex
amendment sites.
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
| Claude | New `### 9. Chain into the Planning Stage` and `### 10. Closing Report`, appended after Step 8. The existing `## Scaffold Complete` report stays exactly where it is: a **top-level `##` heading sitting between Step 7 and Step 8**, not a subsection of Step 7. Anchor on the literal heading string, never on a step number |
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
2. **If the supplied workflow path exists inside that checkout, continue.**

Step 2 is the guard's own sentence, reproduced word for word. Use those words in
both `SKILL.md` variants; do not paraphrase them as "resolves inside", "is under",
or "belongs to", because each of those invites the wrong implementation below.

**Test 2 — cleanliness.** `git status --porcelain` is clean **in the same
checkout step 1 resolved**.

**This is an existence test on the supplied path. It is not a comparison of
directories.** The check must **not** be implemented by canonicalising the
workflow path and comparing its parent, its repository root, or its worktree root
against the current checkout root. A stale same-named workflow file sitting in
the parent checkout passes every such comparison *and* passes the guard, so the
guard continues and planning phases run with commits landing in the parent
checkout, usually `main`. Asking whether the supplied path exists here, rather
than whether two roots match, is what makes scaffold's check and the guard agree
by construction, so the two can never disagree.

The guard's remaining steps 3 through 6 — the `git worktree list --porcelain`
fallback and its STOP messages — are the autopilot's recovery behaviour, not part
of the predicate. Scaffold needs only the yes-or-no from steps 1 and 2; on "no" it
prints the hand-off command rather than searching for the right worktree.

**What the check must NOT test**: the most recent commit. After Step 8 the newest
commit is the roadmap status flip rather than the workflow-file commit, so a
last-commit test would fail on every correct run (FR-013a).

**No new machinery** (FR-023): both commands are read-only, and neither adds a
script, a helper, or a tool grant on either variant.

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

**One printed line before the question** (FR-013). The operator must be told what
accepting does, immediately before being asked. §1's ordering informs the choice
about the **past**; nothing else informs it about the **future**, and neither the
question text nor the two option labels defines "the planning stage". Three facts,
no more: accepting runs the six planning phases in this same session without
further prompts; those phases commit as they go; declining leaves everything
already pushed exactly as it is. Printed, not asked — no options, and it does not
count against the budget below.

**Confirmation budget** (SC-007): this feature adds **at most one** confirmation,
and **exactly one** whenever the chain is attempted. It adds **none** when the
FR-013a check fails, which on Codex CLI is the ordinary case.

**What the budget counts, and what it does not.** A scaffold run already stops for
the operator before this feature adds anything: the grill-me questions; the Step
3.5 bootstrap approval, required by both variants before any documented preflight
command; and, on Claude only, the Step 3 reuse-or-recreate question. On the
worktree-reuse path a Claude run therefore reaches the chain having already asked
twice, which is why the budget counts **additions** rather than prompts. It is a
cap on this feature, not headroom: FR-013 adds the only one, FR-011 forbids one at
the findings stage, and §8.4 forbids one to offer the implement stage.

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

**The hand-off is printed before it is run** (FR-014). On acceptance, print the
invocation above verbatim, then run it. Otherwise the accepted path is the only
branch point where the operator is told nothing: the next output belongs to
another skill and arrives with no statement that the confirmation took effect.
ART-006 calls this boundary a visible seam; one printed line is what makes it one.
It also puts the same string in front of the operator on both branches — what is
running now on accept, what to run later on decline.

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

### 6.1 The hand-off command — one fixed form (FR-015c)

This string carries the whole ending of every no-chain run, which on Codex CLI is
the ordinary run. Unlike the §5 chain invocation and the §9.0 resume command,
nothing fixed its shape; it was the last unspecified operator-facing string in the
feature.

| Platform | Hand-off command |
|---|---|
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan` |
| Codex CLI | start a new Codex task rooted at the spec worktree, then `$speckit-autopilot <workflow-file> --stage plan` |

**The Codex precondition is part of the command, not commentary.** A Claude
operator can run the §5 invocation where they stand. A Codex operator reaching
this ending is by definition rooted outside the worktree (§3), so a bare
invocation hands them a command the Workflow Worktree Binding guard stops — a
hand-off that fails on the platform where it is the normal ending. It is the same
instruction §7's second amendment site keeps for this case.

**The Scaffold Complete report's `Ready to run:` line is brought into this form.**
It prints the invocation with no stage token, so a declining operator sees two
different commands for one action a screen apart; and it prints as an instruction
immediately before a confirmation offering to carry it out — the conflict §4's
companion edit half-fixed. The command gains `--stage plan`, and the label becomes
`**If you stop here, run:**`. Nothing else in that report changes.

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

**One report, rendered on every terminal condition** (Q5, FR-017): after the
planning stage on acceptance, and immediately on each of the three §6 no-chain
paths. It is **printed, not written to a file** (FR-017).

**All four triggers are named because two are not choices.** "Once the chain
resolves ... immediately on decline" names two, while §6 has three no-chain causes
and the heading table below presumes a report on all of them. On Codex the unnamed
§2-rooting-fail path is the **ordinary** run (§3), so a two-item list would leave
the most common Codex ending with no report owed: a run stopping after a printed
command, with no outcome, no index, and no statement that nothing was rolled back.

**Contents, closed at four elements, in this order** (FR-018):

```text
## <heading>

**Outcome:** <one line>
**Draft PR:** none, because draft-PR creation is not part of this release

**Artifacts:**
- <repo-relative path>     (one line each; only paths that exist)

**Next step:** <one command>
```

**The heading is a closed three-value vocabulary, one per terminal condition.**
US4's independent test drives the run to three, and a two-value vocabulary would
force one of them under a heading that is false:

| Terminal condition | Heading |
|---|---|
| The operator declined, or the chain never fired | `## Stopped Before Planning` |
| The chain fired and the §9 completion test passes | `## Planning Complete` |
| The chain fired and the §9 completion test does not pass | `## Planning Incomplete` |

**Fixed, conditional, and derived fields.** The heading is selected from the set
above. The draft-PR line is conditional and, in this release, always the fixed
sentence at §8.1. The outcome line, the artifact index, and the next step are
**derived** — none is a fixed string, and each has its own rule at §8.2, §8.3,
and §9.

`<one command>` denotes one fixed string, not one bare invocation: on the three
no-chain paths that string is the §6.1 hand-off command, whose Codex form states
the rooting precondition as part of the command rather than as commentary beside
it. The slot stays one line per heading. Widening the general definition would
loosen §8.4's implement command and §9.0's resume command, neither of which
admits a precondition clause; splitting the slot would contradict the four-element
close, and §9.0 already folds a derived multi-part value into one slot.

**The set-aside findings count MUST NOT appear here.** The list is closed at four
elements. That count lives in the design concept's header record (FR-010) and in
the seeded block (FR-008), and the artifact index points at the file carrying it.

**What this report adds that §1's earlier one cannot.** The two overlap on paths
by design — SC-009 forces the scaffold-owned artifacts into the index — so the
overlap is bounded by requiring each element to carry something new: the outcome
names the branch, undecided when the first report printed; the draft-PR line
answers a question the first never raises; the index is existence-tested against
disk rather than narrated from intent, and grows by the planning artifacts on
accept; the next step is conditioned on the branch. **The two reports must not
restate the same fields**: no worktree path, no remote line, no bootstrap result
here — the first report gave all three and the closed list admits none of them.
The pushed branch appears once, as an index entry, not as a repeated header field.
Redundancy beyond this trains the operator to skim the report carrying the
outcome.

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

**Derived from a closed candidate set.** SC-009 demands exactness in both
directions, which is unverifiable against an open set, so the candidates are
fixed here:

| Group | Candidates |
|---|---|
| Scaffold-owned | `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`, `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, `specs/<feature>/SPEC-MOC.md`, the pushed branch name |
| Planning-stage | `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, each file under `contracts/`, each file under `checklists/` — all relative to `specs/<feature>/` |

Nothing outside this set is listed, so an unexpected file is a change to this
contract rather than a silent omission.

**The existence test is a read of the candidate path, and nothing more.** A path
that reads is listed; a path that does not read is omitted. This is the only
existence test available inside scaffold's declared grant — FR-002 forbids
widening it with Grep, Glob, or Bash — and it adds no machinery (FR-023). The two
directory-valued members, `contracts/` and `checklists/`, are the one place a
plain read is insufficient; for those the candidate paths are the artifact names
the run's own plan and checklist phases recorded, so the enumeration still comes
from a read rather than a directory listing. Never infer a path from convention,
and never list a path that was not tested.

### 8.3 The decline case, and the two no-chain paths that look like it

When the operator declines and no planning-stage artifacts exist:

- the outcome line states that the run stopped **at the operator's request** and that **nothing was rolled back**;
- the index lists **only** the scaffold-owned artifacts and the pushed branch;
- the next step is the hand-off command.

The index and the next step are the same on all three §6 no-chain paths, because
no planning stage ran on any of them. **The outcome line is not.** One heading
covers a deliberate stop and two the operator did not choose, so the outcome line
is where they are told apart:

| No-chain cause | Outcome line states |
|---|---|
| The operator declined | the run stopped at the operator's request, and nothing was rolled back |
| No structured confirmation mechanism was available | the chain was not offered because the session exposes no structured confirmation mechanism, and nothing was rolled back |
| The §2 rooting test failed | planning was not started in this session because the workflow file is outside the current checkout; everything scaffold owns is finished and pushed, and nothing was rolled back |
| The §2 cleanliness test failed | the chain was not offered because the checkout has uncommitted changes, and nothing was rolled back |

**This does not reopen §6.** The three paths still behave identically: no chain,
hand-off command printed, nothing rolled back. The outcome line is classified at
§8 as a **derived** field rather than a fixed string, so deriving it from the
cause is what that classification already permits.

**The two §2 failures are separated because their remedies differ.** A dirty
checkout is fixed in place, after which the printed hand-off command works as
given. A mis-rooted session cannot be corrected from inside itself on Codex, so
the operator's next action is a new session rooted at the worktree — which §6.1
makes part of the Codex hand-off command, so the remedy reaches the operator
inside what they are shown rather than only in this contract. Reporting only "the
pre-chain check failed" would name a condition without naming its remedy.

Every line closes on **nothing was rolled back**, which is true on all three
paths and is the fact the operator most needs.

**The rooting row reads as an ending, not an apology.** On Codex it is the
**ordinary** outcome (§3), reached by an operator who did nothing wrong and who,
from inside that session, can do nothing about it. Neutrality about fault is
weaker than what §3 claims: a line opening "the chain was not offered because ..."
leads with a negation and a technical condition, which reads as an apology for a
run that succeeded at everything it owns. The wording above leads with what is
finished. **The string is identical on both platforms** — a platform-forked
outcome line would be a fifth divergence outside SC-011's closed list — and it is
true on both, because a Claude session failing the same test is in the same
position.

### 8.4 The completed case — the next step is the implement stage

The heading vocabulary has three values and the next step is **derived**, so each
heading owes a rule. §8.3 fixes the declined one and §9.0 the interrupted one;
without this, the run that went best would end on an undefined line. The value is
the §5 invocation with the stage token advanced to the literal lowercase
`implement`, the next member of ART-006 §3's closed vocabulary, which the
autopilot documents as a resume in a fresh session:

| Platform | Next step under `## Planning Complete` |
|---|---|
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage implement` |
| Codex CLI | `$speckit-autopilot <workflow-file> --stage implement` |

The workflow file path is the same sole hand-off token §5 fixes, so nothing new
crosses the boundary. **Never chain into the implement stage, and never ask a
second confirmation to offer it**: the §4 budget is one confirmation and the chain
it authorises is the plan stage only. The implement stage is named as the
operator's next command, never as scaffold's next action.

## 9. Completion is read from the workflow file

When the chained planning stage fails, stalls, or is interrupted, completion is
determined **by reading the workflow file**, with no live session and no state
file (ART-006 §4, Q10, FR-019).

**The completion test, two conditions, both in the one artifact:**

1. Every planning-phase row in `## Workflow Overview` — Specify, Clarify, Plan, Checklist, Tasks, Analyze — carries a terminal status.
2. A `G6.5` confidence-gate verdict is recorded in the file, **and** the
   `Confidence Gate` row does not carry a blocked status.

**Condition 2 needs the second clause, and it must not instead demand a PASS.**
Presence alone would let the strict-mode gate stop — the failure this whole
section exists to report — pass the test and render under `## Planning Complete`.
But a PASS-only test breaks the **ordinary** case: G6.5 is advisory by default,
and in advisory mode `NO_DATA` soft-skips while `FAIL` logs its breakdown and
proceeds to Phase 7 (`references/gate-validation.md` §G6.5). Planning really did
complete on those runs, so requiring PASS would file the default-mode success as
incomplete.

The blocked-row clause separates the two using only what the file carries: after
a strict-mode stop the six planning rows are terminal and the `Confidence Gate`
row is left blocked, while an advisory run that proceeded leaves it un-flipped
and legitimately pending
(`references/phase-execution.md`, the two consequences under the stage-range
table). This keeps ART-006 §4's condition intact and adds only the disqualifier
its own "a `G6.5` PASS with a non-terminal planning row is a contradiction" note
already implies.

**The `Stage` row is corroborating, not the test.** ART-006 §4 is explicit: the
`Stage` entry records what was *resolved*, not what *completed*, so a file showing
`Stage: plan` with Tasks still pending is a run in flight, not a finished one.

**The report must name which planning phases reached a terminal status, and must
give the resume command** (FR-019).

### 9.0 The resume command — fixed form, derived argument

The resume command is not a fifth element. §8's list is closed at four, so the
resume command **is** the `Next step` under the `## Planning Incomplete` heading.
Its form is the §5 chain invocation plus the autopilot's own documented resume
flag (`speckit-pro/skills/speckit-autopilot/SKILL.md`, Error Recovery; the Codex
argument line in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`):

| Platform | Resume command |
|---|---|
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan --from-phase <phase>` |
| Codex CLI | `$speckit-autopilot <workflow-file> --stage plan --from-phase <phase>` |

`<phase>` is **derived, not chosen**: the first planning-phase row in
`## Workflow Overview` without a terminal status, named in the autopilot's own
lowercase phase vocabulary — `specify`, `clarify`, `plan`, `checklist`, `tasks`,
`analyze`. It comes from the same single read the completion test performs, so
naming the phases that finished and naming the phase to resume from are two
renderings of one result rather than two reads that could disagree.

A phase that **failed** rather than finished derives correctly without a special
case: the §9.1 terminal set holds only Complete and Skipped variants, while
`Blocked` is an open status, so a failed row is the first non-terminal row.

**When every planning row is terminal, `--from-phase` is omitted entirely.**
`## Planning Incomplete` can be reached with all six rows terminal, because
condition 2 is the other half of the test — and that is the strict-mode gate
stop, where the row the operator must act on is `Confidence Gate`. That row is
**not** a planning-phase row under ART-006 §4's enumeration and has **no token**
in the shipped `--from-phase` vocabulary, so it must never be named as
`<phase>`:

| State | Resume command |
|---|---|
| A planning row is non-terminal | the §5 invocation plus `--from-phase <phase>` |
| All six planning rows terminal, condition 2 unmet | the §5 invocation with `--stage plan` and **no** `--from-phase` |

The second row is shipped behaviour rather than a workaround: the autopilot
re-resolves the stage from this same status table, the `Confidence Gate` row sits
inside the plan stage's range, and a bare invocation therefore re-enters at the
gate
(`speckit-pro/skills/speckit-autopilot/references/phase-execution.md`, stage
range table and the two consequences below it). The value is still derived from
one read, and the report's phase list already tells the operator all six
finished.

**`<phase>` is one of the six tokens or absent.** No third possibility: the
autopilot range-checks `--from-phase` against an explicitly named stage before
any phase work begins and stops on a value outside that range, so an invented
token yields a command that fails instead of resuming.

### 9.1 Terminal-status vocabulary — read, never re-declared

The vocabulary is owned by the shipped `WORKFLOW_TERMINAL_STATUSES` frozenset in
`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`.

**Neither platform variant may re-declare the six status literals** (FR-020,
ART-006 §4).

**This contract does not list them either, and the omission is deliberate.** This
document exists so the implementation is a transcription rather than an
interpretation, which makes any list inside it the most likely thing to be
transcribed into the two `SKILL.md` files — exactly the copy FR-020 forbids. So
there is nothing here to copy. The set has six members, two of them differing
only by a Unicode variation selector that renders identically, which is a second
reason a hand copy goes wrong.

Read the frozenset at the path above. If a reviewer needs to see the values,
they read it there too.

The reuse case is the same read: a worktree or branch reused from an earlier
scaffold run with a partially complete workflow file is evaluated by terminal
status on every planning row plus a recorded confidence-gate verdict, from the
file.

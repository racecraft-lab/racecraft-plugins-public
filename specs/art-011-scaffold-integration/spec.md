# Feature Specification: Scaffold Integration — blind-spot pass and autopilot chain

**Feature Branch**: `art-011-scaffold-integration`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "ART-011 Scaffold Integration: add a read-only blind-spot pass before the grill-me interview, seed its findings into the interview and the design concept, chain the scaffold run into the autopilot plan stage behind one explicit confirmation, and close with a single report naming what exists and what to do next."

**Normative sources**:

- `docs/ai/specs/.process/ART-011-design-concept.md` — the 21-question grill-me record. Every scoping decision below cites its Q-number. Where this spec and the design concept differ, the design concept wins.
- `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-011 — the roadmap entry.
- `docs/prd-html-artifacts.md` § 3.11 — AC-11.1 through AC-11.4.
- The ART-006 chain contract, which is normative and is **not in the working tree**. It was deleted when ART-006 was archived. Recover it with:
  `git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md`
  Its §3 fixes the per-platform invocation form and the closed stage vocabulary. Its §4 fixes the workflow-observable completion test.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unknown unknowns surfaced before the interview (Priority: P1)

An operator scaffolds a spec in an area of the codebase they do not know well. Before the first interview question, they are shown a short ranked list of things the roadmap author appears not to have considered: hidden coupling, risky surfaces, unstated assumptions. The list is capped, ordered by impact and surprise, and honest about how much it left out. The operator then answers questions that actually change the design rather than questions that only confirm what the roadmap already said.

**Why this priority**: This is the half of AC-11.1 that carries the feature's value. Everything downstream (the seeding, the doc record) is the delivery mechanism for findings that do not exist unless this story ships. It is also independently useful: findings printed to the operator improve the interview even if nothing else lands.

**Independent Test**: Scaffold any roadmap entry on either platform and confirm that, before the first interview question, the run shows a ranked findings list of at most five items with an explicit count of what was set aside, and that no invocation path reaches the interview without having attempted the pass.

**Acceptance Scenarios**:

1. **Given** a roadmap entry with a Scope section and a `Depends On` chain, **When** the operator invokes scaffold and the worktree is ready, **Then** the run dispatches the read-only analysis before the interview and prints at most five findings ranked by impact and surprise.
2. **Given** the analysis returned more findings than the cap allows, **When** the findings are shown, **Then** the output states how many were set aside so the operator can tell truncation from completeness.
3. **Given** a `Depends On` entry naming a spec whose artifacts were removed by an archive sweep, **When** the analysis runs, **Then** its instructions require chasing that dependency into git history rather than reporting the artifact as absent.
4. **Given** the operator wants to move faster, **When** they look for a way to skip the pass, **Then** no flag, argument, or documented path exists that reaches the interview without it.
5. **Given** the analysis dispatch fails, **When** the run continues, **Then** it proceeds into the interview with nothing seeded and states plainly, in the operator output, that the pass did not run and why.

---

### User Story 2 - Findings survive into the interview and the record (Priority: P1)

The same operator does not have to carry the findings in their head. Each one is already in front of the interviewer, so questions get asked about it. Whatever the interview resolves becomes part of the design record; whatever it does not becomes an Open Question the later phases will pick up. A reader opening the design concept months later can tell whether the pass ran at all.

**Why this priority**: P1 alongside US1 because AC-11.1 names both halves in one criterion. Findings shown and then dropped fail the acceptance criterion as surely as findings never produced. It is separately testable: given a fixed findings list, the seeding and the record can be verified without re-running the analysis.

**Independent Test**: With a known findings list, confirm the interview receives it as an identifiable block on the input it already consumes, that every finding is afterwards traceable in the design concept as either a resolved answer or an Open Question, and that the design concept's header states whether the pass ran.

**Acceptance Scenarios**:

1. **Given** the pass produced findings, **When** the interview is invoked, **Then** the findings arrive as a labelled block appended to the scope input the interview already takes, with no new argument and no change to what the interview produces.
2. **Given** the interview resolved a finding through a question, **When** the design concept is written, **Then** that finding appears as a design-record entry.
3. **Given** the interview did not reach a finding, **When** the design concept is written, **Then** that finding appears as an Open Question.
4. **Given** the pass ran, **When** the design concept is written, **Then** its existing header carries one line naming how many findings were surfaced and how many were set aside.
5. **Given** the pass did not run, **When** the design concept is written, **Then** that same header line says so and gives the reason, so a later reader can distinguish a spec that was scanned and found little from one never scanned at all.
6. **Given** the findings have been shown, **When** the run continues, **Then** it flows straight into the interview with no confirmation prompt between the two.

---

### User Story 3 - One confirmation, then planned work or a clean stop (Priority: P1)

An operator has just watched scaffold finish: the design concept, the workflow file, the navigation marker, and the roadmap status flip are all committed and pushed. They are asked once, and only once, whether they are continuing into planning. *(Amended 2026-08-13: scaffold prints the command rather than running it, so accepting hands them the exact next command instead of starting planning itself.)* Declining leaves everything scaffold produced intact on a pushed branch, with the exact command to pick it up later.

**Why this priority**: P1 because it is the whole of AC-11.2 and the reason the roadmap calls this spec "one-command operator experience". It is independently testable and independently valuable: the confirmation and the decline path deliver a clean seam even before the chained run is exercised.

**Independent Test**: Complete a scaffold run to the end of the roadmap status flip, then verify exactly one confirmation is presented, that accepting starts planning in the same session with the contract-fixed invocation, and that declining ends the run with a pushed branch and a copy-pasteable resume command.

**Acceptance Scenarios**:

1. **Given** the design concept, workflow file, navigation marker, and roadmap status flip are all committed and pushed, **and** the FR-013a pre-chain check passes, **When** scaffold reaches the hand-off, **Then** it asks for confirmation once, using the platform's structured confirmation mechanism.
2. **Given** the operator accepts, **When** the run ends, **Then** it prints the hand-off command carrying the workflow file path and the plan stage, in the per-platform invocation form the ART-006 contract fixes, and the operator runs it. *(Amended 2026-08-13.)*
3. **Given** the operator declines, **When** the run ends, **Then** nothing is rolled back and the operator is given the exact command to start planning later.
4. **Given** no structured confirmation mechanism is available in the session, **When** scaffold reaches the hand-off, **Then** it does not chain and prints the hand-off command instead.
5. **Given** the run reaches the hand-off, **When** the operator counts the confirmations **this feature added**, **Then** there is exactly one on every ending, and none only when the session exposes no structured confirmation mechanism. *(Amended 2026-08-13.)* The count is scoped as SC-007 scopes it: an unqualified count of every prompt outside the interview is already two on the worktree-reuse path, because Claude's Step 3 asks whether to reuse or recreate and Step 3.5 asks before running documented bootstrap commands. Neither is this feature's, and neither is removed.
6. **Given** a Codex session rooted at the parent checkout, which is the ordinary case because a scaffold run starts before the worktree exists, **When** scaffold reaches the hand-off, **Then** it asks nothing and prints the hand-off command, because the workspace root of a Codex task is fixed at task start and cannot be changed from inside the session.
7. **Given** a Codex session started from inside an existing spec worktree, which the re-scaffolding reuse path produces, **When** scaffold reaches the hand-off, **Then** the pre-chain check passes and the chain is offered exactly as it is on Claude.

---

### User Story 4 - One closing report that tells the truth (Priority: P2)

However the run ended, chained or declined, planning finished or planning broke, the operator gets a single closing report. It names what exists and where, it does not name anything that does not exist, and it ends with one next step. When planning did not finish, it says which phases got there and how to resume.

**Why this priority**: P2 because the three preceding stories each deliver value without it, while this story depends on their outcomes to have anything to report. It is still required: AC-11.3 is not met without it.

**Independent Test**: Drive the run to each terminal condition (declined, chained and complete, chained and interrupted) and confirm one closing report renders in each, that its artifact list matches the files actually on disk, that the draft-PR line is absent with a plain note when no PR exists, and that the interrupted case names the phases that reached a terminal status.

**Acceptance Scenarios**:

1. **Given** the operator declined the chain, **When** the run ends, **Then** the closing report renders immediately and lists only the artifacts scaffold itself produced.
2. **Given** the chained planning stage completed, **When** the run ends, **Then** the closing report renders after it and its artifact list includes the planning artifacts that were actually written, including the ones that are only sometimes produced.
3. **Given** no draft pull request exists, **When** the closing report renders, **Then** it states plainly that there is none rather than showing a fabricated or guessed URL.
4. **Given** the chained planning stage failed, stalled, or was interrupted, **When** the closing report renders, **Then** completion is determined from the workflow file alone, and the report names which planning phases reached a terminal status and gives the resume command.
5. **Given** the run has already printed the existing scaffold summary before the confirmation, **When** the closing report renders, **Then** both are present, because a confirmation offered with no context is not a real choice.

---

### Edge Cases

- **The analysis dispatch fails, times out, or errors.** The run continues into the interview with nothing seeded, and records the gap and its reason in both the operator output and the design concept header (Q18).
- **The analysis returns a response that yields no usable findings.** FR-006 fixes the boundary: a reply carrying neither a finding nor the required sentinel sentence is unusable, which is a different header line from a pass that ran and raised nothing.
- **The block travels but the interview never writes the header line.** The likeliest way the durable record goes missing, and the reason FR-010a exists: the request to record it is one line inside a prose block handed to another skill, and the degraded outcomes are exactly where that block is thinnest and easiest to read as noise. Scaffold verifies the key on the read it already performs after the interview and writes the line itself when it is absent.
- **The interview aborts before a design concept exists.** Both variants stop the run when no interactive runtime is available, so no durable record is owed and the operator status line is the only record (FR-010a).
- **The roadmap entry has no `Depends On` line at all.** Not hypothetical: the PRSG roadmap carries none across all fourteen entries. FR-003 degrades to the Scope text alone and records the absence in the payload rather than skipping the pass or reporting a gap.
- **The session is rooted outside the spec worktree when the chain is reached.** The ordinary case on Codex CLI. Scaffold asks nothing, prints the hand-off command, and the run ends successfully; the workflow file, the branch, and the push are all already in place, so nothing is lost.
- **A stale workflow file with the same path sits in the parent checkout.** The reason the pre-chain check tests the workflow path rather than only comparing directory roots: the autopilot guard would treat that stale file as valid and run planning phases with commits landing in the parent checkout, usually `main`. Sharing one predicate between scaffold's check and the guard is what keeps the two from disagreeing.
- **The roadmap entry has no `Key Files` section.** Common, not exceptional: the PRSG roadmap has none across all fourteen entries, and the cross-platform roadmap uses two differently named variants. The pass degrades to Scope plus `Depends On`, which are present in every entry of all eleven roadmaps, rather than failing (Q12).
- **A `Depends On` entry names a spec whose artifacts were removed by an archive sweep.** The dispatch instructions require chasing it into git history. This spec is the live example: its own normative contract exists only at a git object reference (Q6).
- **The analysis returns more than five findings.** Five are shown, ranked; the rest are counted and the count is stated (Q13).
- **The analysis returns zero findings.** This is a successful run, not a failure. The header line records a pass that ran and raised nothing.
- **No structured confirmation mechanism is available at the hand-off.** Do not chain. Print the hand-off command. Everything scaffold owns is already pushed, so the operator loses one command and no work (Q11).
- **The chained planning stage dies mid-run.** The closing report reads completion from the workflow file rather than from session state, names which phases reached a terminal status, and gives the resume command (Q10).
- **Planning completes but wrote no research or contract artifacts.** The artifact index lists what exists and omits what does not; it never prints a path that is not there (Q20).
- **No draft pull request exists.** Expected for every run in this release, since draft-PR creation is ART-007. The report says so plainly (Q1).
- **The worktree or branch is reused from an earlier scaffold run with a partially complete workflow file.** The completion read is the same read: terminal status on every planning row plus a recorded confidence-gate verdict, from the file.

## Requirements *(mandatory)*

### Functional Requirements

> **Amendment, 2026-08-13 — the chain became a hand-off.** An independent review
> found that scaffold cannot invoke the autopilot. On Claude Code the autopilot
> skill carries `disable-model-invocation: true`
> (`speckit-pro/skills/speckit-autopilot/SKILL.md:11`), which the skills
> documentation defines as "Only you can invoke the skill"; it was set
> deliberately in commit `73dcbcc7` to close the model-invocation path. On Codex
> CLI no flag forbids it, but a skill body invoking a sibling skill mid-session
> is unverified. Both variants therefore print the hand-off command and let the
> operator run it. This is a **premise correction**, in the manner of the Q4 and
> Q16 corrections already recorded in the design concept's Revision Notes: the
> interview chose in-session chaining without knowing the platform forbids it.
> FR-013, FR-013a, FR-014, FR-015, FR-017, FR-018, FR-022, SC-007 and SC-011 are
> amended below, and **User Stories 3 and 4 above are amended in place** — they
> sit ahead of this block, so each carries its own dated note.
> FR-015a, FR-015b, FR-019, FR-020 and SC-010 are **superseded** — each described
> behaviour reachable only after a chained planning stage, and no such stage now
> runs inside a scaffold session.

#### Blind-spot pass

- **FR-001**: Scaffold MUST run a read-only blind-spot pass inside the worktree, immediately before the grill-me interview, on every invocation (Q15). The pass MUST be mandatory: no skip flag, no skip argument, and no documented path that reaches the interview without attempting it, mirroring the interview's own hard constraint (Q17).
- **FR-002**: The pass MUST execute by dispatching the already-shipped read-only `codebase-analyst`, unmodified, on both platforms (Q2). Scaffold MUST NOT add or edit any agent definition on either platform, and MUST NOT widen its own declared `allowed-tools` with Grep, Glob, or Bash. Its existing `Agent` grant is what makes the dispatch possible, and leaving agent definitions untouched is what keeps the Layer 6 sha256 corpus chain in `tests/speckit-pro/layer6-efficiency/fixtures-codex/` unstaled.
- **FR-002a**: The dispatch MUST be **awaited**, and scaffold MUST NOT begin the interview until the analyst's own final summary has been consumed or the wait has been abandoned under this requirement. The Claude agent definition declares `background: true`, so an un-awaited dispatch hands back a task identifier rather than findings, and FR-001's "immediately before the interview", FR-005's framing, and FR-011's "flow straight into the interview" all become unsatisfiable at once. The await follows the house consensus pattern: Claude dispatches with `run_in_background: true` and then awaits completion; Codex runs a bounded `wait_agent` loop and calls `close_agent` only when that action is exposed. The pattern is inherited; the deadline value below is not, and is marked as stipulated.

  **A single expired poll is not a verdict.** The shipped Codex rule is that "a `wait_agent` timeout is one bounded mailbox poll, not proof that an agent is stuck" (`speckit-pro/codex-skills/speckit-autopilot/SKILL.md`), and that a status update, an unrelated mailbox wake, or a terminal status without a delivered result is likewise not the result. Scaffold MUST keep polling across such wakes. Abandonment is governed instead by **one execution deadline for the whole pass**, which MUST be stated rather than left open: **five minutes from dispatch**. On Codex, a run of consecutive expired `wait_agent` polls is the loop's own cue to check whether that deadline has passed; it is **not** a second, independently-triggering bound, and it has no Claude-side counterpart. Making the poll count an independent trigger would let Codex abandon earlier than Claude whenever its per-poll timeout is short, which is a behavioural divergence outside the closed list SC-011 permits. Only the deadline expiring — not a poll expiring — produces the FR-006 "did not run" outcome, with `wait deadline expired` as the recorded reason.

  **The five-minute value is stipulated, not precedented.** This repository states this same deadline requirement in three shipped places and fixes a number in none of them, so there is no house value to inherit. Five minutes is chosen against the harm asymmetry rather than from precedent: a late reply is explicitly non-retroactive, so too short a deadline permanently discards a real result and silently degrades the interview, while too long merely costs patience in an interruptible foreground run. The analyst runs at `maxTurns: 50` and maximum effort and performs git archaeology under FR-004, so it can legitimately take far longer than the roughly thirty seconds a narrower consensus dispatch takes. Treat the value as tunable through UAT evidence, and prefer lengthening it over shortening it.

  This gives "no reply at all" exactly one observation point on both platforms: the await returned without a summary, or the deadline expired. It is never inferred from a dispatch that is still running, and a summary that arrives after the deadline MUST NOT retroactively change the recorded outcome, because the interview has already started and FR-011 forbids interrupting it.
- **FR-003**: The pass MUST be seeded from the roadmap entry's Scope text, which is the one required input, from its `Depends On` chain when the entry has one, and from any `Key Files` section when the entry has one, which is an optional hint (Q6, Q12). When the `Key Files` section is absent or differently named, the pass MUST degrade to the remaining seed and continue rather than reporting a gap or skipping.

  **The dependency chain has renamed variants and genuine absences, and both MUST be handled.** `Depends On` is not universal: across the roadmaps in `docs/ai/specs/` the label appears 104 times, while the `pr-size-governance` roadmap instead spells it `**Deps:**` on all fourteen of its entries, and roughly a quarter of all entries declare dependencies under no label at all. So the same two cases FR-003 already fixes for `Key Files` apply here:

  - **Renamed variant present.** Scaffold MUST read the entry's dependency declaration under whatever heading it carries and seed it as the chain. This is shipped extraction behaviour rather than new interpretation: Step 2 of both variants already extracts "Dependencies (what it depends on, what depends on it)" from the entry without matching a fixed heading, exactly as it extracts the scope text. Treating `**Deps:**` as a missing field would discard twelve real dependency chains on the PRSG roadmap alone and tell the analyst the entry has no dependencies when it names several — a false statement in the payload, which is worse than an absent one.
  - **No dependency declaration in any spelling.** Scaffold MUST continue on the Scope text alone, and MUST NOT skip the pass, report a gap, infer a chain, or substitute one from another entry.

  **The absence is recorded rather than hidden.** Unlike `Key Files`, whose label is omitted entirely when absent, the `Depends On` label MUST still be appended with the literal value `none`. Two reasons, and both matter: the FR-005 dispatch block is byte-identical across platforms and its fixed sentence reads "each spec named in Depends On", which stays satisfiable against an empty set but not against a missing label; and an analyst instructed by FR-004 to chase dependencies into git history needs to tell an entry that declares no dependencies from a payload that lost the section. `Key Files` needs no such marker because its absence carries no information — it is a hint, and the block already says it may be absent.

  **A degraded seed is not a degraded outcome.** The pass still runs on the seed it has, and still returns exactly one of the three FR-006 outcomes. Nothing about an absent roadmap field reaches the operator status line or the FR-010 header record, both of which report what the dispatch returned rather than what it was given.
- **FR-004**: The dispatch instructions MUST require chasing each `Depends On` spec into git history for artifacts removed by archive sweeps, so a normative contract deleted at archive time is still reachable (Q6).
- **FR-005**: The dispatch instructions MUST use the literal Field Guide words "blindspot pass" and "unknown unknowns", and MUST state the operator's structural position: the operator has read this roadmap entry and its scope, and has not necessarily read the affected code area or the archived artifacts of its dependencies (Q14). Scaffold MUST NOT ask the operator about their familiarity before the pass.

  The dispatch block MUST be identical on both platforms and MUST carry the whole framing, because the shipped `codebase-analyst` description frames the agent for autopilot consensus resolution rather than for this technique. Assembled only from decisions already closed:

  ```text
  You are running a blindspot pass for <SPEC-ID>: surface the unknown unknowns
  in this roadmap entry before its scoping interview.

  The operator has read this roadmap entry and its scope. They have not
  necessarily read the affected code area, or the archived artifacts of its
  dependencies.

  Seed (required): the Scope text below, and each spec named in Depends On.
  Seed (optional hint, may be absent): the Key Files section.
  For each Depends On spec whose artifacts are not in the working tree, chase
  it into git history rather than reporting it absent.

  Return at most 5 findings, ranked by impact then surprise. Each finding:
  N. **<Title>** - 1-3 sentences, plus a repo-relative file or path pointer.
     Impact: <what requirement or design decision this would change if true>
     Surprise: <why the roadmap entry's own text does not already say this>
  Then state how many findings you set aside, including when that number is 0.
  If you find nothing, reply exactly: The blindspot pass raised no unknown unknowns.
  ```

  **Assembly of the dispatch payload.** The block above is the whole of the framing and is followed, in this order and under these literal labels, by the seed material FR-003 fixes: `Scope:` and the roadmap entry's Scope text, then `Depends On:` and the entry's dependency chain read under whatever heading it carries — or the literal `none` only when the entry declares no dependencies under any heading — then `Key Files:` and that section's text **only when the entry has one**. The block's own words "the Scope text below" refer to that appended material, so the order is part of the contract rather than a formatting preference. Nothing else is appended: scaffold MUST NOT add operator commentary, prior findings, or spec text to the payload. The literal `none` is the resolved value of a contracted label, not additional material, so it does not widen what this paragraph permits.

  The git-history chase is executable on both platforms: the Claude agent does not disallow `Bash`, and the Codex mirror runs `sandbox_mode = "read-only"`, which permits reads.
- **FR-006**: The pass MUST return at most five findings, ranked by impact and surprise, and MUST always state how many findings it set aside, including when the number is zero (Q13). The cap MUST NOT be operator-configurable. The set-aside count MUST be stated in words the operator cannot miss, in the shape of "Showing the 5 highest-impact findings; N more were set aside", "Showing all N findings; none were set aside", or "The blindspot pass raised no unknown unknowns"; the exact strings are confirmed through the UAT runbook.

  **Who enforces the cap.** The dispatch block asks for at most five, but the reply is model output and cannot be relied on to obey. **Scaffold MUST enforce the cap on what it renders**: when the reply carries more than five findings, scaffold shows the first five in the analyst's own order, counts the remainder, and states that count through the truncation string above. Scaffold MUST NOT re-rank, merge, or rewrite findings to fit the cap, because FR-006's ranking is the analyst's and FR-023 forbids the machinery a re-rank would need.

  **Usable reply, defined.** A reply is usable when it contains at least one finding in the fixed shape, **or** the literal sentence `The blindspot pass raised no unknown unknowns.` The dispatch instructions MUST require that sentence when the pass finds nothing, so a silent empty reply can never be mistaken for a clean pass. This yields three disjoint outcomes with no judgement call: the pass **ran** (a finding or the sentinel came back), it **returned nothing usable** (a reply came back carrying neither), or it **did not run** (no reply at all — dispatch error, empty return, or the FR-002a execution deadline expiring). A single expired `wait_agent` poll is **not** this third outcome; FR-002a fixes that boundary.

  **A finding in the fixed shape** means a numbered item carrying a title and at least one of the two rationale lines. A numbered title with neither rationale line is not a finding for this test, because FR-006's reviewability property is the rationale, and a bare title gives the operator nothing to check against the roadmap entry.

  **One operator status line per outcome, all three fixed.** The three shapes above cover the **ran** outcome. The two degraded outcomes get one shape each, so FR-008's block placeholder resolves in every case rather than only in the first:

  ```text
  The blind-spot pass returned nothing usable; continuing without findings. Reason: <reason>
  The blind-spot pass did not run; continuing without findings. Reason: <reason>
  ```

  `<reason>` is one short clause naming what was observed — `reply carried neither a finding nor the sentinel`, `dispatch error: <message>`, `empty return`, or `wait deadline expired`. Exactly one of the five status lines is emitted per run.

  **The one-word spelling inside the sentinel is deliberate and MUST NOT be normalised.** `The blindspot pass raised no unknown unknowns.` carries the Field Guide term FR-005 requires verbatim in the dispatch block, and this requirement echoes it unchanged so one string does both jobs. Everywhere scaffold speaks in its own voice — the two degraded status lines above, the FR-010 header key `**Blind-spot pass:**`, and this spec's prose — the term is hyphenated. One run can therefore show the operator both spellings, which reads as a typo and is not. It matters beyond tidiness: the sentinel is matched **literally**, so an implementer who normalises it to `blind-spot` breaks the usable-reply test that all three outcomes rest on, and does so silently, because the reply then classifies as **returned nothing usable** on exactly the runs where the pass worked perfectly.

  **Ranking MUST be reviewable.** Each finding states one line of impact rationale (which requirement or design decision it would change if true) and one line of surprise rationale (why the roadmap entry's own text does not already say it). Findings are ordered by impact, with surprise as the tiebreak. No numeric score is assigned: FR-023 forbids new executable machinery, so a scoring scheme would be unenforceable. Reviewable means a reader can check each rationale against the roadmap text, not that two runs produce identical lists.
- **FR-007**: The pass MUST fail open. If the dispatch fails or returns nothing usable, as FR-006 defines it, scaffold MUST continue into the interview with nothing seeded, and MUST record the gap and its reason in both the operator output and the design concept (Q18). Scaffold MUST NOT treat the dispatch outcome as a gate, and MUST NOT retry-then-halt.

  **Both sinks are scaffold's duty, and neither is best-effort.** The operator-output half is the FR-006 status line, which scaffold prints itself. The durable half is the FR-010 header line, which the interview writes because the FR-008 block asks it to — and FR-010a makes scaffold verify that it landed and write it when it did not. Recording is what separates fail-open from a silent skip, so a record that depends only on another skill obeying prose would leave the requirement unmet whenever that skill did not. **"Nothing seeded" means no findings are seeded, not that the labelled scope block is omitted**: the block MUST still travel in all three FR-006 outcomes, carrying only its status line in the degraded two. FR-008 makes that block the sole channel into the interview, so omitting it would leave FR-010's "did not run" record with no mechanism to be written at all.

#### Interview seeding and the design-concept record

- **FR-008**: Findings MUST reach the interview by being appended as a labelled block to the `scope` argument scaffold already passes (Q3). Scaffold MUST NOT add a new interview argument, change what the interview produces, or edit the grill-me skill on either platform. The block MUST use one shape in both places it appears, the operator output and the seeded `scope` string, so the two records cannot drift:

  ```text
  --- BLIND-SPOT PASS FINDINGS ---
  <the numbered findings, or the status line for the outcome>
  <the set-aside line, present only when findings are shown>
  Record the Blind-spot pass line in the design concept's header blockquote.
  Treat each finding as a candidate question; any finding not reached becomes an Open Question.
  --- END BLIND-SPOT PASS FINDINGS ---
  ```

  **The second line is conditional; the rest of the block is not.** It carries a set-aside line only in the two shapes that show findings. It is omitted when the sentinel came back, because the sentinel is already the first line and FR-006 makes it one string doing both jobs, so repeating it would report the same fact twice. It is omitted in the two degraded outcomes, which have no set-aside count to state. The labelled delimiters and the two closing instructions are unconditional, so the block keeps one shape across all three outcomes.

  **Two of the block's lines address the interview, and the operator sees them.** One shape in both places is what stops the printed record and the seeded record from drifting, and the cost is that `Record the Blind-spot pass line in the design concept's header blockquote.` and the sentence after it also print to the operator as imperatives that are not the operator's task. That cost is accepted rather than overlooked. The lines sit inside labelled delimiters that mark the whole block as machinery; they are two lines against up to five findings; and they tell the operator truthfully what is about to be done with what they just read, which is the one thing FR-011 otherwise leaves implicit as the run flows straight into the first question. Scaffold MUST NOT resolve the awkwardness by forking the two copies, softening the imperatives in one of them, or omitting them from the printed half — any of those reintroduces exactly the drift this requirement exists to prevent.
- **FR-009**: Findings the interview resolves MUST become entries in the design concept's existing question-and-answer record; findings it does not reach MUST become Open Questions (Q3, Q19). No finding may be dropped silently.
- **FR-010**: The design concept MUST carry one line in its existing header blockquote, under the key `**Blind-spot pass:**`, recording exactly one of the three FR-006 outcomes: how many findings were surfaced and how many were set aside; that the pass returned nothing usable, with the reason; or that the pass did not run, with the reason (Q19). A later reader MUST be able to tell a spec that was scanned and found little from one that was never scanned. Adding this key needs no change to the interview's output schema: the blockquote already tolerates keys beyond the four its reference documents, as this spec's own design concept shows by carrying a size-estimate line. Scaffold MUST NOT add a new section to the design concept, and MUST NOT write a separate findings artifact such as `.process/SPEC-<ID>-blind-spots.md`: the design concept is the only home for findings (Q8).

  **One header-line shape per outcome, fixed.** SC-004 requires a reader to tell the outcomes apart from the header alone, which a free-form line cannot guarantee, so each of the three FR-006 outcomes gets exactly one shape:

  ```text
  > **Blind-spot pass:** ran — N findings surfaced, M set aside
  > **Blind-spot pass:** returned nothing usable — <reason>
  > **Blind-spot pass:** did not run — <reason>
  ```

  The leading word after the key is the outcome discriminator and is drawn from the closed set `ran`, `returned nothing usable`, `did not run`. `<reason>` is the same clause the FR-006 operator status line carried, so the printed record and the durable record cannot give different reasons. A pass that ran and raised nothing is the first shape with `N` and `M` both zero, which is what distinguishes it from a pass that never ran.
- **FR-010a**: After the interview returns, scaffold MUST verify that the design concept carries the `**Blind-spot pass:**` key, and MUST write the FR-010 line itself when the key is absent. The interview remains the writer of first resort, because the FR-008 block asks it to record the line and Q19 chose that channel precisely to avoid editing grill-me. But an instruction inside a prose block is not a guarantee, and FR-007's record is the one thing separating fail-open from a silent skip, so the durable record MUST NOT rest on another skill obeying prose.

  Scaffold can always satisfy this without deriving anything a second time: at the moment it renders the FR-006 status line it already holds the outcome, the `<reason>` clause, and, for the `ran` outcome, `N` and `M`. The line it writes is therefore the same line, in the same FR-010 shape, from the same values — which is what keeps the printed record and the durable record from disagreeing.

  **The check is a read scaffold already performs, and the repair uses tools it already holds.** The Claude variant's grill-me step already re-reads the design concept and asserts required content is present; this requirement extends that existing assertion by one key. The Codex variant performs no such read today, so the requirement creates one there — a difference in current text, not a behavioural divergence, and therefore outside SC-011's closed list rather than an addition to it. Both platforms use `Read` to check and `Edit` to insert one line into the existing header blockquote. No new tool grant (FR-002), no new executable machinery (FR-023), no new section and no separate artifact (FR-010), and no edit to grill-me on either platform (FR-008).

  **When the interview does not return, nothing is owed.** If grill-me aborts because no interactive runtime is available, both variants stop the scaffold run and no design concept exists to carry a record. On that path the FR-006 operator status line is the only record, and that is correct: the run does not continue, so there is no later reader for a durable record to serve.
- **FR-011**: Presentation of the findings to the operator MUST be informational. The run MUST flow straight into the interview with no confirmation, curation step, or continue/abort prompt between the findings and the first question (Q16).

#### Chain hand-off

- **FR-012**: The chain MUST be placed after Step 8, once the design concept, the workflow file, the SPEC-MOC marker, and the roadmap status flip are all committed and pushed (Q9). A chained planning stage that fails or is interrupted must never leave the roadmap claiming the spec is still Ready.
- **FR-013** *(amended)*: Scaffold MUST ask for exactly one explicit confirmation before printing the hand-off, using the platform's structured confirmation mechanism: `AskUserQuestion` on Claude Code, `request_user_input` on Codex CLI when present (Q11). The question is `Scaffold is complete and pushed. Are you continuing into planning now?`, with two mutually exclusive options in this order: `Continue now (Recommended)`, then `Stop here`. The confirmation records whether the operator is continuing now; both answers print the same command, because scaffold runs nothing. Recommending the forward option follows the house convention that the recommended answer comes first, and declining is fully non-destructive because everything scaffold owns is already committed and pushed. The Claude report's existing closing line MUST be softened from "Review both files first" to "Review both files", so the report and the confirmation no longer give opposite instructions. That line has no Codex equivalent.

  **The operator MUST be told what accepting does, in one printed line, immediately before the question.** FR-016 puts the Scaffold Complete report ahead of the confirmation so the choice is informed about the **past**; nothing anywhere informs it about the **future**. The question names "the planning stage" and the two option labels name "planning", and neither this spec, either report, nor the option text ever defines that term for the operator, states what it does, or states that it commits. Walked as one sequence, this is the single step that assumes context the operator was never shown, and a confirmation offered without it is the same defect Q5 rejected — a choice made without the facts — moved one step later. The line MUST state three facts and no more: that the planning stage runs the six SDD phases and commits as it goes; that scaffold prints the command rather than running it, so the operator starts it themselves; and that declining leaves everything already pushed exactly as it is. *(Amended 2026-08-13: the first fact formerly promised an in-session run. The line itself is kept, because its reasoning — the operator is asked about a term nothing defines — survives the amendment intact.)* It is printed rather than asked, carries no options, and does **not** count against the SC-007 budget, because a statement is not a prompt.
- **FR-013a** *(amended)*: Before asking, scaffold MUST run one read-only hand-off check. Its rooting test MUST be **the same predicate the Codex autopilot's Workflow Worktree Binding guard already applies**, stated in the guard's own words rather than paraphrased (`speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`, "Workflow Worktree Binding", steps 1 and 2):

  1. Resolve the current checkout with `git rev-parse --show-toplevel`.
  2. **If the supplied workflow path exists inside that checkout, continue.**

  Using the guard's own test rather than an equivalent-looking one is what guarantees scaffold's pre-check and autopilot's guard can never disagree. **The predicate is an existence test on the supplied path, not a comparison of directories.** Scaffold MUST NOT implement it by canonicalising the workflow path and comparing its parent, its repository root, or its worktree root against the current checkout root: a stale same-named workflow file sitting in the parent checkout passes every such comparison, which is precisely the case this requirement exists to catch. The check MUST also confirm that `git status --porcelain` is clean **in the same checkout step 1 resolved**. The check does not gate the hand-off, because a hand-off is always printed; it selects the hand-off's form. When the rooting test fails, the printed command MUST carry the re-rooting instruction on either platform. When the cleanliness test fails, the report's outcome line MUST carry one added clause naming the uncommitted changes as something to resolve first. The check MUST NOT test the most recent commit: after Step 8 the newest commit is the roadmap status flip rather than the workflow-file commit, so a last-commit test would fail on every correct run. Both commands are read-only and add no script, helper, or tool grant, so the check adds no machinery (FR-023), and it closes three risks at once — the Codex rooting precondition, the Claude variant's silent resolution against a parent checkout, and the question of whether the handed-over workflow file is the one just committed.
- **FR-014** *(amended)*: Scaffold MUST print the hand-off command, carrying the workflow file path and `--stage plan`, and MUST NOT invoke the autopilot (Q4, as corrected by the amendment above). Scaffold MUST NOT state that accepting will run the planning phases in this session. The stage token MUST be the literal lowercase `plan` from the ART-006 contract §3 closed vocabulary of `plan`, `implement`, `full` — no aliases, no alternate casing, no long-form spellings. The workflow file path MUST be the sole hand-off token; scaffold MUST NOT pass a state file, branch name, feature directory, or environment variable across the boundary (ART-006 §1). The runnable forms are:

  | Platform | Invocation | Provenance |
  |---|---|---|
  | Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan` | quoted from ART-006 §3 |
  | Codex CLI | `$speckit-autopilot <workflow-file> --stage plan` | **recorded deviation** from ART-006 §3 |

  **The command MUST be printed verbatim, on every ending.** It is the one thing the operator is expected to act on, and both answers to the confirmation lead to it, so the two paths teach the same command instead of two. ART-006's framing calls this boundary a visible seam; the printed command is what makes it one.

  **The Codex row is a deviation and MUST be read as one.** ART-006 §3's table shows the Codex row as `<workflow-file> --stage plan`, with no leading command token, because its sibling `contracts/stage-invocation.md` §1 documents each distribution's argv as *beginning at the workflow path* and treats the leading token as having "no Codex counterpart" for parity purposes. Read literally, that table would have scaffold chain by invoking a bare path, which is not runnable. The `$speckit-autopilot` prefix is this spec's resolution, not a quotation: the argv after it is unchanged from the contract, and the prefix is the invocation form the whole Codex skill set already uses. Anyone reconciling this spec against ART-006 will find the two rows differ, and this paragraph is the reason. `contracts/chain-handoff.md` §5 carries the same record.
- **FR-015** *(amended)*: Scaffold MUST NOT chain on any path. It MUST print the hand-off command on all three endings — the operator is continuing now, the operator stopped here, or no structured confirmation mechanism was available (Q11). On every ending, nothing is rolled back: everything scaffold owns is committed and pushed before this step runs.
- **FR-015a** *(superseded by the amendment above; retained for the record)*: On Codex CLI the chain MUST be attempted **only** when the FR-013a check passes; otherwise scaffold MUST ask nothing at all and print the hand-off command. A Codex session's workspace root is fixed when the task starts and cannot be changed from inside the session, and a scaffold run necessarily begins before the worktree exists, so the ordinary Codex session is rooted at the parent checkout. Attempting the chain from there is not merely inelegant: the Codex autopilot's fail-closed Workflow Worktree Binding guard stops before any mutation, which would turn the single confirmation into a false promise; and in the narrower case where a stale same-named workflow file happens to sit in the parent checkout, the guard would instead continue and run planning phases with commits landing in that checkout, usually `main`, violating scaffold's own standing constraint against committing there. The condition is not dead code: re-scaffolding through the existing-worktree reuse path starts a session that is already correctly rooted, and the chain then fires normally.
- **FR-015b** *(superseded by the amendment above; retained for the record)*: On Claude Code the chain is unconditional beyond FR-013a, because the platform has no equivalent constraint: Claude's scaffold already runs each step from inside the worktree. Claude's autopilot ships **no** worktree-binding guard, so a mis-rooted Claude chain would resolve silently against the parent checkout rather than stopping. FR-013a is what closes that gap on this platform, and it is the reason the check is required on both rather than only on Codex. Scaffold MUST NOT fall back to parsing a free-text reply, and MUST NOT chain by default when confirmation is unavailable.
- **FR-015c**: **The hand-off command MUST have one fixed form**, stated here and used identically wherever it is printed. That string carries the whole ending of every no-chain run — which on Codex CLI is the ordinary run — and it is the one thing the operator is expected to act on, yet unlike the chain invocation (FR-014) and the resume command (FR-019) nothing fixed its shape. It was the only unspecified operator-facing string left in the feature.

  | Platform | Hand-off command |
  |---|---|
  | Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan` |
  | Codex CLI | start a new Codex task rooted at the spec worktree, then `$speckit-autopilot <workflow-file> --stage plan` |

  **The Codex row carries a precondition, and that is the point.** The Claude row is the FR-014 invocation unchanged, because a Claude operator can run it where they stand. A Codex operator who reaches this ending is by definition in a session rooted outside the worktree (FR-015a), so printing the bare invocation would hand them a command the autopilot's own Workflow Worktree Binding guard stops — a hand-off that fails on the platform where it is the normal ending. The rooting instruction is therefore **part of the command** rather than commentary beside it, and it is the same instruction the Codex `## Output` section already gives, which FR-022's second amendment site keeps for exactly this case. The workflow file path stays the sole hand-off token either way (FR-014).

  **The Scaffold Complete report's existing `Ready to run:` line MUST be brought into this form, on both counts.** It prints the invocation with **no stage token**, so an operator who declines is shown two different commands for one action a screen apart, and the closing report's next step silently contradicts the report they just read. It also prints as an *instruction* immediately before a confirmation that offers to carry it out — the same conflict FR-013 already identified and half-fixed when it softened "Review both files first". This is the half that was missed. The command gains `--stage plan`, and the label changes from `**Ready to run:**` to `**If you stop here, run:**`, so the report states the alternative to the choice the operator is about to be offered rather than issuing an order scaffold is about to countermand. Nothing else in that report changes.

#### Closing report

- **FR-016**: The existing "Scaffold Complete" report MUST still print before the confirmation, so the operator is told what scaffold produced before being asked whether to continue (Q5). The two variants place that existing report differently, so the insertion point differs even though the requirement does not: the Claude report is a top-level `## Scaffold Complete` section sitting **between** Step 7 and Step 8, so the chain and closing report append after the end of the procedure rather than beside that report; the Codex report is a top-level Output section that already follows Step 8, so the chain and closing report extend that section. Because the Claude report is not inside a numbered step, implementation MUST anchor on the literal heading strings rather than on a step number.
- **FR-017** *(amended)*: A single closing report MUST render on **every** ending the run can reach. Because scaffold never invokes the autopilot, every run ends before planning, and there are three endings: the operator is continuing into planning now, the operator stopped here, or no structured confirmation mechanism was available (Q5). It MUST be printed, not written to a file. The heading MUST be the single fixed string `## Ready for Planning`, which is true on all three.

  **All four triggers are enumerated because two of them are not choices.** "Once the chain resolves ... immediately on decline" reads as an accept-or-decline pair and names only two, while FR-015 has three no-chain causes and FR-018's heading table already presumes a report on all of them. The gap is not academic: on Codex CLI the unnamed FR-013a-fail path is the **ordinary** run (FR-015a), so a two-item trigger list leaves the most common Codex ending with no report owed at all. That operator's run would stop after a printed command, with no outcome line, no artifact index, and no statement that nothing was rolled back — a truncated ending on the ordinary path, which is precisely the parity of *experience* AC-11.4 asks for and SC-011 measures.
- **FR-018** *(amended)*: The closing report MUST contain, in this order: the run outcome; a draft pull request line; an artifact index; and one next step. Its layout is:

  ```text
  ## <heading>

  **Outcome:** <one line>
  **Draft PR:** none, because draft-PR creation is not part of this release

  **Artifacts:**
  - <repo-relative path>     (one line each; only paths that exist)

  **Next step:** <one command>
  ```

  **The heading is one fixed string, `## Ready for Planning`** *(amended 2026-08-13)*. Every run now ends before planning, so the three terminal conditions collapse to three endings under one true heading, and the outcome line tells them apart. The superseded three-value vocabulary is retained below for the record:

  | Terminal condition | Heading |
  |---|---|
  | *(superseded)* The operator declined, or the chain never fired | `## Stopped Before Planning` |
  | *(superseded)* The chain fired and the FR-019 completion test passes | `## Planning Complete` |
  | *(superseded)* The chain fired and the FR-019 completion test does not pass — failed, stalled, or interrupted | `## Planning Incomplete` |

  **Which fields are fixed and which are derived.** The heading is selected from the closed set above. The draft-PR line is conditional and, in this release, always the fixed sentence. The outcome line, the artifact index, and the next step are **derived** from the run: none is a fixed string, and each is specified by its own rule below and in FR-019.

  `<one command>` denotes one fixed string, not one bare invocation: on the three no-chain paths that string is the FR-015c hand-off command, whose Codex form states the rooting precondition as part of the command rather than as commentary beside it (FR-015c). The slot stays one line per heading. Widening the general definition instead would loosen the implement command under `## Planning Complete` and the resume command under `## Planning Incomplete`, neither of which admits a precondition clause; splitting the slot would contradict this list being closed at four elements, and FR-019 already folds a derived multi-part value into a single slot rather than splitting it.

  The set-aside findings count MUST NOT appear here. This list is closed at four elements; that count lives in the design concept's header record (FR-010) and in the seeded block (FR-008), and the artifact index points at the file that carries it.

  **What this report adds, so it is not the first report printed twice.** The Scaffold Complete report and this one overlap on paths by design — SC-009 requires the index be exact in both directions, so the scaffold-owned artifacts must appear in it. The overlap is bounded by requiring each of the four elements to carry something only this report can: the **outcome** names which branch the run took, which was still undecided when the first report printed; the **draft-PR line** answers a question the first report never raises; the **index** is existence-tested against disk rather than narrated from what scaffold set out to write, and on the accepted path it grows by the planning artifacts; and the **next step** is conditioned on the branch. The two reports MUST NOT restate the same fields: the closing report carries no worktree path, no remote line, and no bootstrap result, all of which the Scaffold Complete report already gave and none of which the closed four-element list admits. The pushed branch appears only as one entry in the index, not as a repeated header field. Redundancy beyond this is not a cosmetic complaint — it trains the operator to skim the one report that carries the outcome.

  When the operator declines and no planning-stage artifacts exist, the outcome line MUST state that the run stopped at the operator's request and that nothing was rolled back, the index MUST list only the scaffold-owned artifacts and the pushed branch, and the next step MUST be the FR-015c hand-off command.

  **When the chain fired and planning completed, the next step is the implement stage.** The heading vocabulary has three values and the next step is a **derived** field, so each heading owes a rule: the paragraph above fixes the declined one, FR-019 fixes the interrupted one, and this fixes the third. Leaving it open would tell the operator least on the run that went best — the feature's own happy path ending in a report whose last line is undefined. The value is the FR-014 invocation with the stage token advanced to the literal lowercase `implement`, the next member of the ART-006 §3 closed vocabulary of `plan`, `implement`, `full`, which the autopilot documents as a resume in a fresh session:

  | Platform | Next step under `## Planning Complete` |
  |---|---|
  | Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage implement` |
  | Codex CLI | `$speckit-autopilot <workflow-file> --stage implement` |

  The workflow file path is the same sole hand-off token FR-014 fixes, so nothing new crosses the boundary. Scaffold MUST NOT derive a next step outside this rule, and MUST NOT chain into the implement stage or ask a second confirmation to offer it: FR-013's budget is one confirmation and the chain it authorises is the plan stage only (FR-014, SC-007). The implement stage is named as the operator's next command, never as scaffold's next action.

  **The three no-chain paths share one heading, so the outcome line MUST say which one happened.** `## Stopped Before Planning` covers a deliberate decline and two paths the operator did not choose, and FR-015 makes all three behave identically — no chain, hand-off command printed, nothing rolled back. That identical behaviour is deliberate and unchanged here. But the outcome line is a derived field, not a fixed string, and a report that renders a failed pre-chain check in the same words as a deliberate stop tells the operator nothing about a condition they could fix. One line per cause:

  | No-chain cause | Outcome line states |
  |---|---|
  | The operator declined | the run stopped at the operator's request, and nothing was rolled back |
  | No structured confirmation mechanism was available | the chain was not offered because the session exposes no structured confirmation mechanism, and nothing was rolled back |
  | The FR-013a rooting test failed | planning was not started in this session because the workflow file is outside the current checkout; everything scaffold owns is finished and pushed, and nothing was rolled back |
  | The FR-013a cleanliness test failed | the chain was not offered because the checkout has uncommitted changes, and nothing was rolled back |

  **The two FR-013a failures are reported separately because they are differently actionable.** A dirty checkout is resolved in place and the operator can then run the hand-off command as printed. A mis-rooted session cannot be corrected from inside itself on Codex, so the operator's next action is a new session rooted at the worktree — which is why FR-015c makes that instruction part of the Codex hand-off command rather than prose beside it, so the remedy reaches the operator inside what they are shown. Collapsing both into "the pre-chain check failed" would name a condition without naming the remedy. All four lines close on "nothing was rolled back", because that fact is true on every no-chain path and is the one the operator most needs.

  **The rooting row is written as an ending, not an apology, and that is a requirement rather than a preference.** On Codex it is the **ordinary** outcome (FR-015a), reached by an operator who did nothing wrong and, from inside that session, can do nothing about it. Neutrality about fault is weaker than what FR-015a claims: a line opening "the chain was not offered because ..." leads with a negation and a technical condition, which reads as an apology for a run that in fact succeeded at everything it owns. The wording above leads with what is finished. The string MUST be identical on both platforms — a platform-forked outcome line would add a fifth divergence outside SC-011's closed list — and it is true on both, because a Claude session that fails the same test is in the same position.
  - The draft-PR line MUST show the URL when the run produced one, and MUST otherwise state plainly that there is none rather than omitting the line silently or fabricating a URL (Q1), in the shape of "Draft PR: none, because draft-PR creation is not part of this release". Draft-PR creation itself is out of scope.
  - The artifact index MUST enumerate what the run actually produced: the scaffold-owned artifacts plus whatever the planning stage wrote, including the conditionally produced research artifact, contract artifacts, and the checklist domains this spec chose (Q20). It MUST NOT print a path that does not exist, and MUST NOT omit an artifact that does.
  - **The index is derived from a fixed candidate set, tested one path at a time.** SC-009 demands exactness in both directions, which is unverifiable against an open set, so the candidate set is closed here. It is the scaffold-owned artifacts — `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`, `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, `specs/<feature>/SPEC-MOC.md`, and the pushed branch name — plus every artifact the planning stage can write into `specs/<feature>/`: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, each file under `contracts/`, and each file under `checklists/`. Nothing outside this set is listed, so an unexpected file is a spec change rather than a silent omission.
  - **The existence test is a read of the candidate path, and nothing more.** A path that reads is listed; a path that does not read is omitted. This is the only existence test available inside scaffold's declared grant, which FR-002 forbids widening with Grep, Glob, or Bash, and it needs no new machinery (FR-023). The two directory-valued members of the set, `contracts/` and `checklists/`, are the one place a plain read is insufficient; for those the candidate paths are the artifact names the run's own plan and checklist phases recorded, so the enumeration still comes from a read rather than a directory listing. Scaffold MUST NOT infer a path from convention, and MUST NOT list a path it did not test.
- **FR-019** *(superseded by the amendment above; retained for the record — no planning stage runs inside a scaffold session, so this state is unreachable)*: When the chained planning stage fails, stalls, or is interrupted, the closing report MUST determine completion by reading the workflow file, with no live session and no state file, per ART-006 §4: a terminal status on every planning-phase row plus a recorded G6.5 confidence-gate verdict (Q10). The report MUST name which planning phases reached a terminal status and MUST give the resume command.

  **Condition 2 is a recorded verdict whose `Confidence Gate` row is not blocked — not a recorded PASS.** "A verdict is recorded" alone would let the strict-mode gate stop, the one failure this requirement most exists to report, render under `## Planning Complete`. But requiring a PASS would be worse, and would break the ordinary case: G6.5 is **advisory by default**, and in advisory mode a `NO_DATA` result soft-skips and a `FAIL` result logs its breakdown and **proceeds to Phase 7**. Planning genuinely completed on those runs, so a PASS-only test would file the default-mode success under `## Planning Incomplete`.

  The discriminator that separates the two is already in the file, which is the only thing the report may read: after a strict-mode stop the six planning rows are terminal and the `Confidence Gate` row is left **blocked**, whereas an advisory run that proceeded leaves that row un-flipped and legitimately pending. So condition 2 is met when a G6.5 verdict is recorded **and** the `Confidence Gate` row does not carry a blocked status. A blocked row, or no recorded verdict at all, fails the test and selects `## Planning Incomplete`. This keeps ART-006 §4's condition intact and adds only the disqualifier its own "a `G6.5` PASS with a non-terminal planning row is a contradiction" note already implies.

  **The resume command has a fixed form, and it occupies the Next step slot.** FR-018's field list is closed at four elements, so the resume command is not an extra line; it *is* the next step for this heading. Its form is the chain invocation plus the autopilot's own documented resume flag (`speckit-pro/skills/speckit-autopilot/SKILL.md`, Error Recovery, and the Codex argument line in `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`):

  ```text
  /speckit-pro:speckit-autopilot <workflow-file> --stage plan --from-phase <phase>
  $speckit-autopilot <workflow-file> --stage plan --from-phase <phase>
  ```

  `<phase>` is **derived, not chosen**: it is the first planning-phase row in `## Workflow Overview` without a terminal status, named in the autopilot's own lowercase phase vocabulary of `specify`, `clarify`, `plan`, `checklist`, `tasks`, `analyze`. That is the same single read the completion test already performs, so naming the phases that reached a terminal status and naming the phase to resume from are two renderings of one result rather than two reads that could disagree. A phase that failed rather than finished still derives correctly, because the shipped terminal set holds only Complete and Skipped variants while `Blocked` is an open status, so a failed row is the first non-terminal row.

  **When every planning row is terminal, the resume command carries no `--from-phase`.** The heading can be `## Planning Incomplete` with all six rows terminal, because the gate verdict is the other half of the completion test — and that is exactly the strict-mode gate stop, where the row the operator must act on is `Confidence Gate`. That row is not a planning-phase row under ART-006 §4's enumeration and has no token in the shipped `--from-phase` vocabulary, so it MUST NOT be named as `<phase>`. Scaffold MUST instead emit the chain invocation with `--stage plan` and no `--from-phase` at all. This is not a workaround: the autopilot re-resolves the stage from the same status table, the `Confidence Gate` row is inside the plan stage's range, and a bare invocation therefore re-enters at the gate. The value is still derived from one read, and the report's phase list already tells the operator that all six finished.

  `<phase>` MUST be one of the six tokens above or absent. No other value is permissible: the autopilot range-checks `--from-phase` against an explicitly named stage before any phase work begins and stops on a value outside it, so an invented token would produce a resume command that fails rather than resumes.
- **FR-020** *(superseded by the amendment above; retained for the record — scaffold no longer reads planning-phase statuses)*: The terminal-status vocabulary MUST be read from the shipped `WORKFLOW_TERMINAL_STATUSES` frozenset in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`. Neither platform variant may re-declare the six status literals, because the contract names that frozenset as the owner and any copy is a readability copy, not a source (ART-006 §4).

#### Cross-cutting

- **FR-021**: The scaffold description on both platforms MUST keep its existing boundary clause intact, so the autopilot remains the documented entry point for an existing workflow file, and MUST add the blind-spot pass and the chain to its capability sentence (Q7). **Only the capability sentence changes**; sentences 1, 2, 4, and 5 stay byte-identical. The replacement capability sentence is:

  `Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then can chain into planning.`

  The resulting description value is **1015 characters**, against a hard cap of **1024** enforced both by `tests/speckit-pro/layer1-structural/validate-skills.py` and by the Agent Skills platform contract itself, leaving 9 characters of headroom. The same validator forbids angle brackets; the replacement contains none. The phrase "ready for autopilot" leaves the capability sentence because the cap forces it: every wording that keeps it while naming both new capabilities measures 1025 to 1050 characters. It survives elsewhere in the same description through "for autonomous execution", "prepare SPEC-XXX for the autonomous run", and the boundary clause naming `/speckit-pro:speckit-autopilot`.

- **FR-021a**: The two platform descriptions are byte-identical today and MUST stay so. A description carries routing keywords, which FR-022 does not list among the permitted platform divergences. Implementation MUST re-verify identity after both edits rather than assuming it.

- **FR-021b**: The reword MUST be covered by **four new Layer 2 trigger cases per platform** — two positive, two negative — added only to `tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json` and `tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json`. One positive per new capability phrase. **The two negatives test the same boundary at two different prompt lengths, and both are required.** The first states the precondition explicitly, so precondition contrast is its deciding signal, which is what FR-021b's own reasoning calls for. The second is deliberately bare — a short prompt naming "planning" and a spec ID with no stated context — because an operator who already has a workflow file open rarely restates that fact, so the short form is the shape a real misroute takes. Testing only the explicit form would measure the case the model finds easy and leave the likely one uncovered. *(Amended after implementation: the fourth case was added on an independent review's finding, and this requirement was reconciled to the shipped fixtures rather than the reverse, because the extra coverage is additive and removes nothing.)* Each negative MUST be a near-miss that stresses the word "planning" against the preserved boundary, because that word is new to scaffold's description and the sibling autopilot description already claims it, and because the existing boundary clause is scoped to "run a populated workflow" prompts rather than to plan-stage prompts. Case queries MUST be ASCII-only: the two fixture files are not byte-identical today, differing only in whether em dashes are escaped, and an ASCII query keeps each file's own convention intact. Scaffold-shaped negative cases already exist in six other fixture files per platform; those need no new cases because those skills' descriptions do not change, but they MUST be re-run as regression coverage.
- **FR-022** *(amended)*: Both platform variants MUST implement the same flow, differing only where the platform forces a difference: the invocation form, the confirmation mechanism name, and the local documentation idiom. The production surface MUST be exactly two files, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`, and neither may gain a `references/` directory. The Codex `agents/openai.yaml` sidecar is deliberately excluded from that surface: it carries no `description` field, so FR-021 does not reach it, and its `default_prompt` is pinned verbatim by `tests/speckit-pro/layer1-structural/validate-codex-skills.py`, so changing it would cost a third production file plus a test edit.

  **Permitted divergences, three** *(amended 2026-08-13)*. The invocation form; the confirmation mechanism name; and the local documentation idiom. A fourth — **whether the chain is attempted at all**, per the now-superseded FR-015a and FR-015b — was removed with the chain itself: neither platform chains, so neither differs. SC-011 states the same count.

  **Three Codex sites contradict the chain and all three MUST be amended, not worked around.** The Hard Constraint reading `Do not run the autopilot at the end` becomes conditional on the session's rooting rather than absolute. The Output section's next-step instruction gains the conditional chain while keeping its new-task guidance for the ordinary case. The two sentences forbidding hand-off from the parent checkout are **kept verbatim** and merely prefaced to apply when the chain does not fire, because they guard the real hazard this requirement exists to respect.
- **FR-023**: The feature MUST add no new executable machinery on either platform, including a runner helper to render the closing report. Every change is prose in the two skill definitions (Q21).

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed. The two production files are prose skill definitions, not code, and both changes are additive edits to existing procedure sections.
- The measured production surface is two files against the roadmap entry's declared "~4". The declaration is stale in the safe direction and is reconciled in the Reviewability Budget below.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process (the roadmap status line and this spec's own artifacts)
- **Projected reviewable LOC**: 322 (`estimate-spec-size`, modify-weighted, status `ok`, measured at this spec's final 31 FRs). The design concept recorded 187 against its 13-FR draft and the roadmap entry declares 162; both are superseded, and the design concept's own Open Questions direct the re-measurement ("re-run the estimator once the Declared File Operations table exists, and amend the roadmap entry if the measured figure diverges"). It does diverge. All three figures are under the 400 warn ceiling and all three return one slice, so the split decision is unchanged either way. The figure grew with the FR count, not with the production surface: plan.md measures 187 at 13 FRs, 300 at 28, and 322 at 31, while the production surface stayed at two prose files throughout (plan.md § Declared File Operations).
- **Projected production files**: 2
- **Projected total files**: 9 in the diff, of which 5 are hand-edited (the 2 production `SKILL.md` files, the 2 Layer 2 fixtures, and the roadmap entry) and 4 are generated by `scripts/refresh-release-artifacts.py`. **Measured at PR time the diff is 42 files**: the 2 production files and 2 fixtures as projected, plus 19 generated (the projection counted 4, having missed the installed-cache fixture tree and the XPLAT-009 proofs) and 19 spec and doc files (the projection counted only the roadmap entry, excluding this spec's own artifacts). The projection understated the count because it scoped to files the *behaviour* touches; the diff also carries the artifacts that describe it. Production surface and reviewable LOC are unaffected.
- **Budget result**: within budget
- **Split decision**: remains one spec. The four behaviours are one operator flow through one pair of files: the pass produces findings, the seeding delivers them, the chain continues the run, and the report closes it. Splitting would ship a pass whose findings go nowhere, or a report with nothing to report. The estimator returns one suggested slice.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue. For this feature the named deferrals are ART-007 (draft-PR creation, and therefore the report's PR URL) and the archive-hygiene question of where the ART-006 chain contract should live.

### Key Entities

- **Blind-spot finding**: one ranked item the pass raises. Carries enough text to become an interview question. Exists only in the seeded scope block, the operator output, and, after the interview, the design concept.
- **Seeded scope block**: the labelled block appended to the scope input the interview already consumes. The only channel by which findings reach the interview, and the reason no grill-me change is needed (Q3).
- **Design-concept header line**: one line in the design concept's existing header blockquote recording that the pass ran and what it produced, or that it did not run and why (Q19).
- **Chain confirmation**: the single structured yes-or-no decision between scaffold's committed output and an autonomous planning run. The visible seam between the interactive and autonomous halves.
- **Workflow file**: the sole hand-off token across the scaffold-to-autopilot boundary, and afterwards the durable record from which the closing report reads planning completion (ART-006 §1, §4).
- **Closing report**: the printed, non-persisted summary rendered once the chain resolves. Contains the outcome, the conditional PR line, the artifact index, and the next step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every scaffold run on either platform attempts the blind-spot pass before its first interview question. Zero runs reach the interview without it, because no skip path exists. *(AC-11.1)*
- **SC-002**: The operator sees at most five findings, ordered by impact and surprise, together with an explicit count of findings set aside, before answering any interview question. *(AC-11.1)*
- **SC-003**: Every finding shown to the operator is afterwards traceable in the design concept, as either a resolved answer or an Open Question. None is dropped. *(AC-11.1)*
- **SC-004**: A reader opening the design concept can tell from its header alone whether the pass ran, what it produced, and if it did not run, why. No other file is needed. *(AC-11.1)*
- **SC-005**: An operator who accepts the chain reaches planned work without typing a second command. *(AC-11.2)*
- **SC-006**: An operator who declines is left with every scaffold artifact committed and pushed, plus one copy-pasteable command that resumes the run. Nothing is rolled back. *(AC-11.2)*
- **SC-007** *(amended)*: This feature adds **exactly one** operator confirmation to a scaffold run, on every platform and every ending, except when the session exposes no structured confirmation mechanism, where it adds none. The confirmation records whether the operator is continuing now; it does not decide whether anything runs. *(AC-11.2)*

  **The universe this counts, stated so the criterion is measurable and true.** An earlier wording read "outside the interview, a scaffold run asks the operator for at most one confirmation", and that is false against the shipped files it would be measured on. A scaffold run already stops for the operator before this feature adds anything: the grill-me interview's own questions; the **Step 3.5 bootstrap approval**, which both variants require before running any documented preflight command and which therefore fires on every project that documents one, this repository included; and, on Claude only, the **Step 3 question** asking whether to reuse or recreate an existing worktree. On the worktree-reuse path — the very path FR-015a and US3 scenario 7 rely on for Codex chain coverage — a Claude run reaches the chain having already asked twice. None of those three is this feature's, none is removed, and none is counted here. Counting what this feature adds is what makes the number checkable; counting every prompt in the run would make the criterion fail on shipped behaviour that is correct.

  **This is a cap, not headroom.** "At most one" bounds what this feature may introduce and MUST NOT be read as permission to add a second prompt elsewhere: FR-013 introduces the only one, FR-011 forbids one at the findings stage, and FR-018 forbids a second one to offer the implement stage. *(Amended 2026-08-13: the superseded `## Planning Complete` rule formerly carried that prohibition, and FR-014's pre-question informational line was removed with the chain — neither variant prints one now, so nothing in this feature is a printed statement that could be mistaken for a prompt.)* The design concept's Q16 rationale says scaffold sits at "exactly one confirmation — the chain"; that decision is untouched, and only its unexamined premise about the pre-existing prompts is corrected here, in the same manner as the dated Q4 premise correction in its Revision Notes.
- **SC-008**: The closing report never shows a pull request URL that does not exist. When there is none it says so in plain words. For every run in this release, that is the expected outcome. *(AC-11.3)*
- **SC-009**: The closing report's artifact index matches the files the run actually wrote: no listed path is missing from disk, and no written artifact is missing from the list. *(AC-11.3)*
- **SC-010** *(superseded by the amendment above; retained for the record)*: After an interrupted planning stage, the report names which planning phases reached a terminal status and gives the resume command, derived from the workflow file alone. *(AC-11.3)*
- **SC-011**: A reader comparing the two platform variants **across the flow this feature specifies** — the blind-spot pass, the seeding and its record, the chain hand-off, and the closing report — finds no behavioural difference between them other than the invocation form, the confirmation mechanism name, and the local documentation idiom. Every operator-facing string this feature fixes is identical on both platforms; the three permitted divergences are structural, not textual. The amendment above removed the fourth divergence — whether the chain is attempted — by removing the chain from both. *(AC-11.4)*

  **The scope clause is required, because an unscoped comparison is already falsified.** The two shipped files differ outside this feature's flow on a subject it touches: Claude's Step 3 asks whether to reuse or recreate an existing worktree, while Codex's Step 3 reuses without asking. That difference is pre-existing, is not introduced or removed here, and is not one of the four — so an unscoped criterion would send a reviewer to a discrepancy this spec never claimed to resolve, and would fail on it. Scoping the comparison keeps the criterion falsifiable against what this feature actually changed.
- **SC-012**: The change adds zero new production files, zero new or edited agent definitions, zero new executable helpers, and no new tool grant to scaffold.

## Assumptions

- The shipped `codebase-analyst` is present on both platforms whenever the pass fires. Scaffold's existing agent-completeness step already stops the run when a bundled agent file is missing, so the pass does not need its own presence check.
- Both variants are already operating inside the worktree by the time the pass fires. Step 3 establishes that all subsequent work happens there, and Step 3.5 bootstraps it.
- Prompt-level framing of `codebase-analyst` is sufficient for a blind-spot pass, even though its shipped description frames it for autopilot consensus resolution. Confirming this belongs to the planning phase; if framing proves insufficient, the fix is a new spec rather than an agent edit inside this budget (design concept Open Questions, Q2).
- Each finding is a short titled paragraph, so the seeded scope block stays proportionate to the roadmap scope text it accompanies. No per-finding length contract is fixed beyond the five-finding cap.
- On Codex CLI the printed hand-off is the **ordinary** outcome rather than a degraded one, because a task's workspace root is fixed at task start and a scaffold run necessarily begins before the worktree exists. This is a platform capability limit, not an absent mechanism: `codex exec --cd` and the app-server `thread/start` both accept a root, but neither is reachable from inside a running skill's own turn. Two open upstream issues describe exactly this gap, and the CLI exposes no command to change the working directory mid-session.
- On Codex, `request_user_input` availability is already a hard prerequisite of the interview step, which stops the run when the feature is not enabled. The "no structured confirmation mechanism" branch of FR-015 is therefore defensive on that platform, covering degraded or non-interactive runtimes rather than the ordinary case.
- The ART-006 chain contract is normative and is recovered from git history rather than the working tree. Relocating it into the tree is an archive-hygiene decision outside this slice; if the citation proves insufficient for downstream phases, it should be raised as a separate hygiene change rather than by widening this spec (design concept Open Questions, Q6).
- Verification is Layer 1 structure and frontmatter, Codex parity through `validate-codex-skills` and `validate-codex-parity`, Layer 2 trigger evals re-run against the reworded description on both platforms, and UAT evidence for the pass and the chain. Nothing new is executable, so no fixture can assert against the two behaviours directly (Q21). **The Layer 2 half is a manual live gate, not part of the declared FULL_VERIFY**: Layer 2 is declared `"default": false` in `tests/speckit-pro/suite-manifest.json`, so `python3 tests/speckit-pro/run-all.py` prints its commands rather than running them. The Claude runner additionally needs a `skill-creator` skill directory and the Codex runner needs the `codex` CLI on PATH; each exits non-zero without it. The runs are `python3 tests/speckit-pro/layer2-trigger/run-trigger-evals.py speckit-scaffold-spec` and `python3 tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py speckit-scaffold-spec --run`, and they must be scheduled deliberately with their evidence recorded. The Claude runner moves the operator's installed skill directory aside and restores it in a `finally` block, so it must never be run from a read-only or background agent.
- Editing the description restales generated artifacts. The string is copied into `dist/claude/`, `dist/codex/`, and the two installed-cache fixtures under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`. `python3 scripts/refresh-release-artifacts.py` covers all four plus the proof-tree hashes. The Layer 6 digest chain is **not** affected, because it binds agent source bytes and no agent definition changes here.
- The roadmap entry's declared reviewability budget of "~4 production files" and 162 LOC is stale against the interview's settled surface of 2 files and the measured 322 LOC. The estimator returns `ok` either way, so nothing is blocked. The measured figure does diverge from the declaration, so the roadmap amendment is part of this slice rather than a deferral: it is the fifth entry in plan.md § Declared File Operations and is carried out by the roadmap task in tasks.md.

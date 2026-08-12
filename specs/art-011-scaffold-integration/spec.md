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

An operator has just watched scaffold finish: the design concept, the workflow file, the navigation marker, and the roadmap status flip are all committed and pushed. They are asked once, and only once, whether to continue into planning. Accepting takes them to planned work without typing another command. Declining leaves everything scaffold produced intact on a pushed branch, with the exact command to pick it up later.

**Why this priority**: P1 because it is the whole of AC-11.2 and the reason the roadmap calls this spec "one-command operator experience". It is independently testable and independently valuable: the confirmation and the decline path deliver a clean seam even before the chained run is exercised.

**Independent Test**: Complete a scaffold run to the end of the roadmap status flip, then verify exactly one confirmation is presented, that accepting starts planning in the same session with the contract-fixed invocation, and that declining ends the run with a pushed branch and a copy-pasteable resume command.

**Acceptance Scenarios**:

1. **Given** the design concept, workflow file, navigation marker, and roadmap status flip are all committed and pushed, **When** scaffold reaches the hand-off, **Then** it asks for confirmation once, using the platform's structured confirmation mechanism.
2. **Given** the operator accepts, **When** the chain fires, **Then** planning starts in the same session using the workflow file path and the plan stage, in the per-platform invocation form the ART-006 contract fixes.
3. **Given** the operator declines, **When** the run ends, **Then** nothing is rolled back and the operator is given the exact command to start planning later.
4. **Given** no structured confirmation mechanism is available in the session, **When** scaffold reaches the hand-off, **Then** it does not chain and prints the hand-off command instead.
5. **Given** the run reaches the hand-off, **When** the operator counts the confirmations scaffold asked for outside the interview, **Then** there is exactly one.

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
- **The analysis returns a response that yields no usable findings.** See FR-006 and its clarification marker: the boundary between "ran and raised nothing" and "returned nothing usable" is not yet fixed, and the two produce different header lines.
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

#### Blind-spot pass

- **FR-001**: Scaffold MUST run a read-only blind-spot pass inside the worktree, immediately before the grill-me interview, on every invocation (Q15). The pass MUST be mandatory: no skip flag, no skip argument, and no documented path that reaches the interview without attempting it, mirroring the interview's own hard constraint (Q17).
- **FR-002**: The pass MUST execute by dispatching the already-shipped read-only `codebase-analyst`, unmodified, on both platforms (Q2). Scaffold MUST NOT add or edit any agent definition on either platform, and MUST NOT widen its own declared `allowed-tools` with Grep, Glob, or Bash. Its existing `Agent` grant is what makes the dispatch possible, and leaving agent definitions untouched is what keeps the Layer 6 sha256 corpus chain in `tests/speckit-pro/layer6-efficiency/fixtures-codex/` unstaled.
- **FR-003**: The pass MUST be seeded from the roadmap entry's Scope text and its `Depends On` chain, both of which are required inputs, and from any `Key Files` section when the entry has one, which is an optional hint (Q6, Q12). When the `Key Files` section is absent or differently named, the pass MUST degrade to the required seed and continue rather than reporting a gap or skipping.
- **FR-004**: The dispatch instructions MUST require chasing each `Depends On` spec into git history for artifacts removed by archive sweeps, so a normative contract deleted at archive time is still reachable (Q6).
- **FR-005**: The dispatch instructions MUST use the literal Field Guide words "blindspot pass" and "unknown unknowns", and MUST state the operator's structural position: the operator has read this roadmap entry and its scope, and has not necessarily read the affected code area or the archived artifacts of its dependencies (Q14). Scaffold MUST NOT ask the operator about their familiarity before the pass.
- **FR-006**: The pass MUST return at most five findings, ranked by impact and surprise, and MUST always state how many findings it set aside, including when the number is zero (Q13). The cap MUST NOT be operator-configurable. The set-aside count MUST be stated in words the operator cannot miss, in the shape of "Showing the 5 highest-impact findings; N more were set aside", "Showing all N findings; none were set aside", or "The blindspot pass raised no unknown unknowns"; the exact strings are confirmed through the UAT runbook. [NEEDS CLARIFICATION: what counts as "returns nothing usable" for the fail-open trigger in FR-007, and how it is distinguished in the operator output and the design-concept header line from a pass that ran successfully and raised zero findings]
- **FR-007**: The pass MUST fail open. If the dispatch fails or returns nothing usable, scaffold MUST continue into the interview with nothing seeded, and MUST record the gap and its reason in both the operator output and the design concept (Q18). Scaffold MUST NOT treat the dispatch outcome as a gate, and MUST NOT retry-then-halt.

#### Interview seeding and the design-concept record

- **FR-008**: Findings MUST reach the interview by being appended as a labelled block to the `scope` argument scaffold already passes (Q3). Scaffold MUST NOT add a new interview argument, change what the interview produces, or edit the grill-me skill on either platform.
- **FR-009**: Findings the interview resolves MUST become entries in the design concept's existing question-and-answer record; findings it does not reach MUST become Open Questions (Q3, Q19). No finding may be dropped silently.
- **FR-010**: The design concept MUST carry one line in its existing header blockquote recording either how many findings were surfaced and how many were set aside, or that the pass did not run and why (Q19). Scaffold MUST NOT add a new section to the design concept, and MUST NOT write a separate findings artifact such as `.process/<SPEC-ID>-blind-spots.md`: the design concept is the only home for findings (Q8).
- **FR-011**: Presentation of the findings to the operator MUST be informational. The run MUST flow straight into the interview with no confirmation, curation step, or continue/abort prompt between the findings and the first question (Q16).

#### Chain hand-off

- **FR-012**: The chain MUST be placed after Step 8, once the design concept, the workflow file, the SPEC-MOC marker, and the roadmap status flip are all committed and pushed (Q9). A chained planning stage that fails or is interrupted must never leave the roadmap claiming the spec is still Ready.
- **FR-013**: Scaffold MUST ask for exactly one explicit confirmation before chaining, using the platform's structured confirmation mechanism: `AskUserQuestion` on Claude Code, `request_user_input` on Codex CLI when present (Q11).
- **FR-014**: On acceptance, scaffold MUST invoke the autopilot in-session with the workflow file path and `--stage plan`, in the per-platform invocation form fixed by the ART-006 contract §3 (Q4). The stage token MUST be the literal lowercase `plan` from that contract's closed vocabulary of `plan`, `implement`, `full`. The workflow file path MUST be the sole hand-off token; scaffold MUST NOT pass a state file, branch name, feature directory, or environment variable across the boundary (ART-006 §1).
- **FR-015**: On decline, or when no structured confirmation mechanism is available, scaffold MUST NOT chain, and MUST print the hand-off command instead (Q11). Scaffold MUST NOT fall back to parsing a free-text reply, and MUST NOT chain by default when confirmation is unavailable.

#### Closing report

- **FR-016**: The existing "Scaffold Complete" report MUST still print before the confirmation, so the operator is told what scaffold produced before being asked whether to continue (Q5).
- **FR-017**: A single closing report MUST render once the chain resolves: after the planning stage on acceptance, immediately on decline (Q5). It MUST be printed, not written to a file.
- **FR-018**: The closing report MUST contain, in this order: the run outcome; a draft pull request line; an artifact index; and one next step.
  - The draft-PR line MUST show the URL when the run produced one, and MUST otherwise state plainly that there is none rather than omitting the line silently or fabricating a URL (Q1), in the shape of "Draft PR: none, because draft-PR creation is not part of this release". Draft-PR creation itself is out of scope.
  - The artifact index MUST enumerate what the run actually produced: the scaffold-owned artifacts plus whatever the planning stage wrote, including the conditionally produced research artifact, contract artifacts, and the checklist domains this spec chose (Q20). It MUST NOT print a path that does not exist, and MUST NOT omit an artifact that does.
- **FR-019**: When the chained planning stage fails, stalls, or is interrupted, the closing report MUST determine completion by reading the workflow file, with no live session and no state file, per ART-006 §4: a terminal status on every planning-phase row plus a recorded G6.5 confidence-gate verdict (Q10). The report MUST name which planning phases reached a terminal status and MUST give the resume command.
- **FR-020**: The terminal-status vocabulary MUST be read from the shipped `WORKFLOW_TERMINAL_STATUSES` frozenset in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`. Neither platform variant may re-declare the six status literals, because the contract names that frozenset as the owner and any copy is a readability copy, not a source (ART-006 §4).

#### Cross-cutting

- **FR-021**: The scaffold description on both platforms MUST keep its existing boundary clause intact, so the autopilot remains the documented entry point for an existing workflow file, and MUST add the blind-spot pass and the chain to its capability sentence (Q7). [NEEDS CLARIFICATION: the exact reworded description text for each platform, and how many Layer 2 trigger-eval cases each platform needs to cover the new capability without regressing the negative cases in `tests/speckit-pro/layer2-trigger/evals/` and `codex-evals/`]
- **FR-022**: Both platform variants MUST implement the same flow, differing only where the platform forces a difference: the invocation form, the confirmation mechanism name, and the local documentation idiom. The production surface MUST be exactly two files, `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`, and neither may gain a `references/` directory. [NEEDS CLARIFICATION: the Codex variant's existing Output section instructs the operator to start a new Codex task rooted at the worktree and forbids handing off from the parent checkout, which an in-session chain from a parent-rooted Codex session would contradict; whether the Codex chain fires in-session, is conditioned on the session already being rooted at the worktree, or degrades to the printed hand-off command, is unresolved]
- **FR-023**: The feature MUST add no new executable machinery on either platform, including a runner helper to render the closing report. Every change is prose in the two skill definitions (Q21).

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed. The two production files are prose skill definitions, not code, and both changes are additive edits to existing procedure sections.
- The measured production surface is two files against the roadmap entry's declared "~4". The declaration is stale in the safe direction and is reconciled in the Reviewability Budget below.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process (the roadmap status line and this spec's own artifacts)
- **Projected reviewable LOC**: 187 (design-concept `estimate-spec-size`, modify-weighted, status `ok`). The roadmap entry declares 162. Both are under the 400 ceiling. The functional requirements below are decomposed more finely than the estimator's 13-FR input, but the production surface is fixed at two prose files, so the reviewable surface does not grow with the FR count.
- **Projected production files**: 2
- **Projected total files**: ~7
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
- **SC-007**: Outside the interview, a scaffold run asks the operator for exactly one confirmation. *(AC-11.2)*
- **SC-008**: The closing report never shows a pull request URL that does not exist. When there is none it says so in plain words. For every run in this release, that is the expected outcome. *(AC-11.3)*
- **SC-009**: The closing report's artifact index matches the files the run actually wrote: no listed path is missing from disk, and no written artifact is missing from the list. *(AC-11.3)*
- **SC-010**: After an interrupted planning stage, the report names which planning phases reached a terminal status and gives the resume command, derived from the workflow file alone. *(AC-11.3)*
- **SC-011**: A reader comparing the two platform variants finds no behavioural difference between them other than the invocation form, the confirmation mechanism name, and the local documentation idiom. *(AC-11.4)*
- **SC-012**: The change adds zero new production files, zero new or edited agent definitions, zero new executable helpers, and no new tool grant to scaffold.

## Assumptions

- The shipped `codebase-analyst` is present on both platforms whenever the pass fires. Scaffold's existing agent-completeness step already stops the run when a bundled agent file is missing, so the pass does not need its own presence check.
- Both variants are already operating inside the worktree by the time the pass fires. Step 3 establishes that all subsequent work happens there, and Step 3.5 bootstraps it.
- Prompt-level framing of `codebase-analyst` is sufficient for a blind-spot pass, even though its shipped description frames it for autopilot consensus resolution. Confirming this belongs to the planning phase; if framing proves insufficient, the fix is a new spec rather than an agent edit inside this budget (design concept Open Questions, Q2).
- Each finding is a short titled paragraph, so the seeded scope block stays proportionate to the roadmap scope text it accompanies. No per-finding length contract is fixed beyond the five-finding cap.
- On Codex, `request_user_input` availability is already a hard prerequisite of the interview step, which stops the run when the feature is not enabled. The "no structured confirmation mechanism" branch of FR-015 is therefore defensive on that platform, covering degraded or non-interactive runtimes rather than the ordinary case.
- The ART-006 chain contract is normative and is recovered from git history rather than the working tree. Relocating it into the tree is an archive-hygiene decision outside this slice; if the citation proves insufficient for downstream phases, it should be raised as a separate hygiene change rather than by widening this spec (design concept Open Questions, Q6).
- Verification is Layer 1 structure and frontmatter, Codex parity through `validate-codex-skills` and `validate-codex-parity`, Layer 2 trigger evals re-run against the reworded description on both platforms, and UAT evidence for the pass and the chain. Nothing new is executable, so no fixture can assert against the two behaviours directly (Q21).
- The roadmap entry's declared reviewability budget of "~4 production files" is stale against the interview's settled surface of 2. The estimator returns `ok` either way, so nothing is blocked; the roadmap entry is amended if the measured figure diverges once the plan's file-operations table exists.
